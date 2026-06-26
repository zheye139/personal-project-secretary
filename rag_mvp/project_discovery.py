import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

import config
import manifest_utils


# ============================================================
# Windows / PowerShell 中文输入输出处理
# ============================================================

def setup_console_encoding() -> None:
    """
    尽量修正 Windows 控制台中文输入输出编码。
    """
    if os.name == "nt":
        try:
            import ctypes

            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleCP(65001)
            kernel32.SetConsoleOutputCP(65001)
        except Exception:
            pass

    try:
        sys.stdin.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


setup_console_encoding()


# ============================================================
# 基础配置
# ============================================================

KNOWLEDGE_ROOT = config.KNOWLEDGE_ROOT
INDEX_MANIFEST_PATH = getattr(
    config,
    "INDEX_MANIFEST_PATH",
    KNOWLEDGE_ROOT / "99_System" / "index_manifest.json",
)


# ============================================================
# 通用工具
# ============================================================

def normalize_text(value) -> str:
    """
    转成去除首尾空格的字符串。
    """
    if value is None:
        return ""

    return str(value).strip()


def normalize_tags(value) -> list[str]:
    """
    将 tags 统一成 list[str]。
    """
    if hasattr(manifest_utils, "normalize_tags_value"):
        return manifest_utils.normalize_tags_value(value)

    if not value:
        return []

    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]

    return [
        item.strip()
        for item in str(value).split(",")
        if item.strip()
    ]


def safe_int(value, default: int = 0) -> int:
    """
    安全转 int。
    """
    try:
        return int(value)
    except Exception:
        return default


def load_manifest() -> dict:
    """
    加载 manifest。

    通过 manifest_utils.load_manifest() 读取，可自动兼容旧 manifest。
    """
    if not INDEX_MANIFEST_PATH.exists():
        raise FileNotFoundError(f"index_manifest.json not found: {INDEX_MANIFEST_PATH}")

    return manifest_utils.load_manifest()


def iter_records(manifest: dict):
    """
    遍历 manifest files 记录。
    """
    files = manifest.get("files", {})

    if not isinstance(files, dict):
        return

    for source, record in files.items():
        if not isinstance(record, dict):
            continue

        yield source, record


# ============================================================
# 数据发现函数
# ============================================================

def discover_projects(manifest: dict) -> list[dict]:
    """
    发现项目列表。

    返回：
    [
      {
        "name": "Personal_Project_Assistant",
        "file_count": 10,
        "chunk_count": 30,
        "doc_types": ["progress_log", ...],
        "categories": ["project", ...]
      }
    ]
    """
    project_map = {}

    for source, record in iter_records(manifest):
        project = normalize_text(record.get("project", ""))

        if not project:
            continue

        if project not in project_map:
            project_map[project] = {
                "name": project,
                "file_count": 0,
                "chunk_count": 0,
                "doc_types": set(),
                "categories": set(),
                "tags": set(),
            }

        item = project_map[project]
        item["file_count"] += 1
        item["chunk_count"] += safe_int(record.get("chunk_count", 0))

        doc_type = normalize_text(record.get("doc_type", ""))
        category = normalize_text(record.get("category", ""))

        if doc_type:
            item["doc_types"].add(doc_type)

        if category:
            item["categories"].add(category)

        for tag in normalize_tags(record.get("tags", [])):
            item["tags"].add(tag)

    results = []

    for item in project_map.values():
        item["doc_types"] = sorted(item["doc_types"])
        item["categories"] = sorted(item["categories"])
        item["tags"] = sorted(item["tags"])
        results.append(item)

    return sorted(results, key=lambda x: x["name"].lower())


def discover_categories(manifest: dict) -> list[dict]:
    """
    发现 category 列表。
    """
    counter = Counter()

    for source, record in iter_records(manifest):
        category = normalize_text(record.get("category", ""))

        if category:
            counter[category] += 1

    return [
        {
            "name": name,
            "file_count": count,
        }
        for name, count in sorted(counter.items(), key=lambda x: x[0].lower())
    ]


def discover_doc_types(manifest: dict, project: str | None = None) -> list[dict]:
    """
    发现 doc_type 列表。

    可选按 project 过滤。
    """
    counter = Counter()

    for source, record in iter_records(manifest):
        if project:
            record_project = normalize_text(record.get("project", ""))
            if record_project != project:
                continue

        doc_type = normalize_text(record.get("doc_type", ""))

        if doc_type:
            counter[doc_type] += 1

    return [
        {
            "name": name,
            "file_count": count,
        }
        for name, count in sorted(counter.items(), key=lambda x: x[0].lower())
    ]


def discover_tags(manifest: dict, project: str | None = None) -> list[dict]:
    """
    发现 tags 列表。

    可选按 project 过滤。
    """
    counter = Counter()

    for source, record in iter_records(manifest):
        if project:
            record_project = normalize_text(record.get("project", ""))
            if record_project != project:
                continue

        for tag in normalize_tags(record.get("tags", [])):
            counter[tag] += 1

    return [
        {
            "name": name,
            "file_count": count,
        }
        for name, count in sorted(counter.items(), key=lambda x: x[0].lower())
    ]


def discover_files(
    manifest: dict,
    project: str | None = None,
    doc_type: str | None = None,
    category: str | None = None,
    tag: str | None = None,
) -> list[dict]:
    """
    发现文件列表。

    支持按 project / doc_type / category / tag 过滤。
    """
    results = []

    for source, record in iter_records(manifest):
        record_project = normalize_text(record.get("project", ""))
        record_doc_type = normalize_text(record.get("doc_type", ""))
        record_category = normalize_text(record.get("category", ""))
        record_tags = normalize_tags(record.get("tags", []))

        if project and record_project != project:
            continue

        if doc_type and record_doc_type != doc_type:
            continue

        if category and record_category != category:
            continue

        if tag and tag not in record_tags:
            continue

        results.append(
            {
                "source": source,
                "file_name": normalize_text(record.get("file_name", Path(source).name)),
                "title": normalize_text(record.get("title", Path(source).stem)),
                "project": record_project,
                "category": record_category,
                "doc_type": record_doc_type,
                "tags": record_tags,
                "chunk_count": safe_int(record.get("chunk_count", 0)),
                "updated_at": normalize_text(record.get("updated_at", "")),
            }
        )

    return sorted(
        results,
        key=lambda x: (
            x.get("project", "").lower(),
            x.get("doc_type", "").lower(),
            x.get("source", "").lower(),
        ),
    )


def build_summary(manifest: dict) -> dict:
    """
    构建 discovery 摘要。
    """
    projects = discover_projects(manifest)
    categories = discover_categories(manifest)
    doc_types = discover_doc_types(manifest)
    tags = discover_tags(manifest)
    files = discover_files(manifest)

    total_chunks = sum(item.get("chunk_count", 0) for item in files)

    return {
        "manifest_path": str(INDEX_MANIFEST_PATH),
        "total_files": len(files),
        "total_chunks": total_chunks,
        "project_count": len(projects),
        "category_count": len(categories),
        "doc_type_count": len(doc_types),
        "tag_count": len(tags),
        "projects": projects,
        "categories": categories,
        "doc_types": doc_types,
        "tags": tags,
    }


def build_discovery_data(
    manifest: dict,
    project: str | None = None,
    doc_type: str | None = None,
    category: str | None = None,
    tag: str | None = None,
) -> dict:
    """
    构建完整 discovery 数据。

    后续 Web API 可以直接复用这个函数。
    """
    return {
        "summary": build_summary(manifest),
        "projects": discover_projects(manifest),
        "categories": discover_categories(manifest),
        "doc_types": discover_doc_types(manifest, project=project),
        "tags": discover_tags(manifest, project=project),
        "files": discover_files(
            manifest=manifest,
            project=project,
            doc_type=doc_type,
            category=category,
            tag=tag,
        ),
    }


# ============================================================
# 终端输出函数
# ============================================================

def print_table_header(title: str) -> None:
    """
    打印标题。
    """
    print("")
    print("=" * 80)
    print(title)
    print("=" * 80)


def print_projects(projects: list[dict]) -> None:
    """
    打印项目列表。
    """
    print_table_header("Projects")

    if not projects:
        print("No projects found.")
        return

    print(f"{'Project':<36} {'Files':>8} {'Chunks':>8} Doc types")
    print("-" * 80)

    for item in projects:
        doc_types = ", ".join(item.get("doc_types", [])[:5])

        if len(item.get("doc_types", [])) > 5:
            doc_types += ", ..."

        print(
            f"{item['name']:<36} "
            f"{item['file_count']:>8} "
            f"{item['chunk_count']:>8} "
            f"{doc_types}"
        )


def print_simple_counter(title: str, items: list[dict]) -> None:
    """
    打印简单计数列表。
    """
    print_table_header(title)

    if not items:
        print("No items found.")
        return

    print(f"{'Name':<50} {'Files':>8}")
    print("-" * 64)

    for item in items:
        print(f"{item['name']:<50} {item['file_count']:>8}")


def print_files(files: list[dict], limit: int | None = None) -> None:
    """
    打印文件列表。
    """
    print_table_header("Files")

    if not files:
        print("No files found.")
        return

    shown = files

    if limit and limit > 0:
        shown = files[:limit]

    print(f"{'Project':<28} {'Doc type':<22} {'Chunks':>6} Source")
    print("-" * 100)

    for item in shown:
        print(
            f"{item.get('project', ''):<28} "
            f"{item.get('doc_type', ''):<22} "
            f"{item.get('chunk_count', 0):>6} "
            f"{item.get('source', '')}"
        )

    if limit and len(files) > limit:
        print("")
        print(f"Showing {limit} of {len(files)} files.")


def print_summary(summary: dict) -> None:
    """
    打印摘要。
    """
    print_table_header("Discovery summary")

    print(f"Manifest path: {summary.get('manifest_path', '')}")
    print(f"Total files:   {summary.get('total_files', 0)}")
    print(f"Total chunks:  {summary.get('total_chunks', 0)}")
    print(f"Projects:      {summary.get('project_count', 0)}")
    print(f"Categories:    {summary.get('category_count', 0)}")
    print(f"Doc types:     {summary.get('doc_type_count', 0)}")
    print(f"Tags:          {summary.get('tag_count', 0)}")


def print_json(data: dict) -> None:
    """
    输出 JSON。
    """
    print(json.dumps(data, ensure_ascii=False, indent=2))


# ============================================================
# 命令行入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Personal Project Secretary project and metadata discovery tool"
    )

    parser.add_argument(
        "--projects",
        action="store_true",
        help="显示项目列表。",
    )

    parser.add_argument(
        "--categories",
        action="store_true",
        help="显示 category 列表。",
    )

    parser.add_argument(
        "--doc-types",
        action="store_true",
        help="显示 doc_type 列表。",
    )

    parser.add_argument(
        "--tags",
        action="store_true",
        help="显示 tag 列表。",
    )

    parser.add_argument(
        "--files",
        action="store_true",
        help="显示文件列表。",
    )

    parser.add_argument(
        "--summary",
        action="store_true",
        help="显示摘要。",
    )

    parser.add_argument(
        "--project",
        default=None,
        help="按项目过滤。",
    )

    parser.add_argument(
        "--doc-type",
        default=None,
        help="按文档类型过滤。",
    )

    parser.add_argument(
        "--category",
        default=None,
        help="按资料大类过滤。",
    )

    parser.add_argument(
        "--tag",
        default=None,
        help="按标签过滤。",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="文件列表显示数量。",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="输出 JSON。",
    )

    args = parser.parse_args()

    manifest = load_manifest()

    data = build_discovery_data(
        manifest=manifest,
        project=args.project,
        doc_type=args.doc_type,
        category=args.category,
        tag=args.tag,
    )

    # JSON 模式：输出完整结构，方便 launcher.py / Web UI 复用。
    if args.json:
        print_json(data)
        return

    # 如果没有指定任何显示项，默认显示 summary + projects。
    no_specific_action = not any(
        [
            args.projects,
            args.categories,
            args.doc_types,
            args.tags,
            args.files,
            args.summary,
        ]
    )

    if args.summary or no_specific_action:
        print_summary(data["summary"])

    if args.projects or no_specific_action:
        print_projects(data["projects"])

    if args.categories:
        print_simple_counter("Categories", data["categories"])

    if args.doc_types:
        print_simple_counter("Doc types", data["doc_types"])

    if args.tags:
        print_simple_counter("Tags", data["tags"])

    if args.files:
        print_files(data["files"], limit=args.limit)


if __name__ == "__main__":
    main()
