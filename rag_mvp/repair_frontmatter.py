import argparse
import shutil
from datetime import datetime
from pathlib import Path

from config import KNOWLEDGE_ROOT, BACKUP_DIR


REQUIRED_FIELDS = ["title", "category", "project", "doc_type", "tags"]

SKIP_DIR_NAMES = {
    ".venv",
    "__pycache__",
    "backups",
    "qdrant_storage",
    "qdrant_local",
    "_imported",
    "01_Projects_Archived",
}


CATEGORY_MAP = {
    "01_Projects": "project",
    "02_Knowledge": "knowledge",
    "03_Decisions": "decision",
    "04_Problems": "problem",
    "05_Summaries": "summary",
    "06_Attachments": "attachment",
    "99_System": "system",
}


DOC_TYPE_BY_NAME = {
    "readme": "readme",
    "project_overview": "project_overview",
    "environment": "environment",
    "model_decisions": "model_decisions",
    "progress_log": "progress_log",
    "issues": "issues",
    "next_steps": "next_steps",
    "decisions": "decisions",
    "technical_notes": "technical_notes",
    "commands": "command_reference",
    "environment_setup": "environment_setup",
    "restore_guide": "restore_guide",
    "rag_mvp_readme": "rag_mvp_readme",
}


def should_skip(path: Path) -> bool:
    parts = set(path.parts)
    return bool(parts.intersection(SKIP_DIR_NAMES))


def collect_markdown_files() -> list[Path]:
    files = []

    for path in KNOWLEDGE_ROOT.rglob("*.md"):
        if should_skip(path):
            continue

        rel_parts = path.relative_to(KNOWLEDGE_ROOT).parts

        # 允许 99_System/docs 入库和修复
        if len(rel_parts) >= 2 and rel_parts[0] == "99_System" and rel_parts[1] == "docs":
            files.append(path)
            continue

        # 跳过 99_System 其他目录
        if rel_parts and rel_parts[0] == "99_System":
            continue

        files.append(path)

    return sorted(files)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8-sig")


def parse_frontmatter(text: str) -> tuple[dict, str, bool]:
    text = text.lstrip()

    if not text.startswith("---"):
        return {}, text, False

    parts = text.split("---", 2)

    if len(parts) < 3:
        return {}, text, False

    raw_meta = parts[1].strip()
    body = parts[2].strip()

    metadata = {}

    for line in raw_meta.splitlines():
        line = line.strip()

        if not line or ":" not in line:
            continue

        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip()

    return metadata, body, True


def infer_category(path: Path) -> str:
    rel_parts = path.relative_to(KNOWLEDGE_ROOT).parts

    if not rel_parts:
        return "unknown"

    return CATEGORY_MAP.get(rel_parts[0], "unknown")


def infer_project(path: Path, category: str) -> str:
    rel_parts = path.relative_to(KNOWLEDGE_ROOT).parts

    if len(rel_parts) >= 3 and rel_parts[0] == "01_Projects":
        return rel_parts[1]

    if len(rel_parts) >= 3 and rel_parts[0] in {"04_Problems", "05_Summaries", "03_Decisions"}:
        return rel_parts[1]

    if len(rel_parts) >= 3 and rel_parts[0] == "02_Knowledge":
        return rel_parts[1]

    if len(rel_parts) >= 2 and rel_parts[0] == "99_System":
        return "Personal_Project_Assistant"

    if category in {"knowledge", "decision", "problem", "summary", "system"}:
        return "Personal_Project_Assistant"

    return "unknown"


def infer_doc_type(path: Path) -> str:
    stem = path.stem.lower()

    if stem in DOC_TYPE_BY_NAME:
        return DOC_TYPE_BY_NAME[stem]

    if stem.endswith("_qa"):
        return "qa_log"

    if stem.endswith("_project_report"):
        return "project_report"

    if stem.endswith("_daily_report"):
        return "daily_report"

    if stem.endswith("_weekly_report"):
        return "weekly_report"

    if "validation_report" in stem:
        return "validation_report"

    return "note"


def infer_title(path: Path) -> str:
    return path.stem.replace("_", " ").strip() or "Untitled"


def infer_tags(category: str, doc_type: str) -> list[str]:
    tags = []

    if category:
        tags.append(category)

    if doc_type:
        tags.append(doc_type)

    tags.append("自动补全Frontmatter")

    return tags


def normalize_tags(raw_value, category: str, doc_type: str) -> str:
    if not raw_value:
        tags = infer_tags(category, doc_type)
        return "[" + ", ".join(tags) + "]"

    value = str(raw_value).strip()

    if value in {"[]", ""}:
        tags = infer_tags(category, doc_type)
        return "[" + ", ".join(tags) + "]"

    if value.startswith("[") and value.endswith("]"):
        return value

    # 如果原来是普通字符串，转为列表格式
    items = [item.strip() for item in value.split(",") if item.strip()]
    if not items:
        items = infer_tags(category, doc_type)

    return "[" + ", ".join(items) + "]"


def build_fixed_metadata(path: Path, metadata: dict) -> dict:
    category = metadata.get("category", "").strip() or infer_category(path)
    doc_type = metadata.get("doc_type", "").strip() or metadata.get("type", "").strip() or infer_doc_type(path)
    project = metadata.get("project", "").strip() or infer_project(path, category)
    title = metadata.get("title", "").strip() or infer_title(path)
    created = metadata.get("created", "").strip()

    if not created:
        created = datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")

    tags = normalize_tags(
        raw_value=metadata.get("tags", ""),
        category=category,
        doc_type=doc_type,
    )

    fixed = dict(metadata)

    fixed["title"] = title
    fixed["created"] = created
    fixed["category"] = category
    fixed["project"] = project
    fixed["doc_type"] = doc_type
    fixed["tags"] = tags

    # 如果旧文档只有 type，没有 doc_type，则保留 type 不强删
    return fixed


def build_frontmatter(metadata: dict) -> str:
    preferred_order = [
        "title",
        "created",
        "category",
        "project",
        "doc_type",
        "tags",
    ]

    lines = ["---"]

    used_keys = set()

    for key in preferred_order:
        value = metadata.get(key, "")
        lines.append(f"{key}: {value}")
        used_keys.add(key)

    # 保留其他已有字段
    for key, value in metadata.items():
        if key in used_keys:
            continue
        lines.append(f"{key}: {value}")

    lines.append("---")
    lines.append("")

    return "\n".join(lines)


def repair_content(path: Path, text: str) -> tuple[str, list[str]]:
    metadata, body, has_frontmatter = parse_frontmatter(text)
    issues = []

    if not text.strip():
        issues.append("空文件，跳过修复")
        return text, issues

    if not has_frontmatter:
        issues.append("补充 Frontmatter")

    fixed_metadata = build_fixed_metadata(path, metadata)

    for field in REQUIRED_FIELDS:
        old_value = metadata.get(field, "").strip()
        new_value = fixed_metadata.get(field, "").strip()

        if not old_value:
            issues.append(f"补充字段：{field} = {new_value}")

    if metadata.get("tags", "").strip() in {"", "[]"}:
        issues.append(f"补充 tags：{fixed_metadata.get('tags', '')}")

    fixed_frontmatter = build_frontmatter(fixed_metadata)

    fixed_body = body.strip()

    if not fixed_body:
        fixed_body = f"# {fixed_metadata['title']}\n\n待补充内容。"
        issues.append("正文为空，添加占位正文")

    fixed_text = fixed_frontmatter + fixed_body + "\n"

    return fixed_text, issues


def backup_original(path: Path, backup_root: Path) -> None:
    rel_path = path.relative_to(KNOWLEDGE_ROOT)
    target_path = backup_root / rel_path
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target_path)


def main():
    parser = argparse.ArgumentParser(
        description="个人项目秘书 + 数据知识库：批量修复 Markdown Frontmatter"
    )

    parser.add_argument(
        "--execute",
        action="store_true",
        help="真正写入修复结果。默认只预览，不修改文件。",
    )

    parser.add_argument(
        "--only-missing",
        action="store_true",
        help="只修复缺少 Frontmatter 的文件；默认也修复缺少字段的文件。",
    )

    args = parser.parse_args()

    files = collect_markdown_files()

    print("个人项目秘书 + 数据知识库：Frontmatter 修复工具")
    print(f"知识库根目录：{KNOWLEDGE_ROOT}")
    print(f"检查 Markdown 文件数量：{len(files)}")
    print(f"执行修复：{args.execute}")

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_root = BACKUP_DIR / "frontmatter_repair" / timestamp

    changed_count = 0
    skipped_count = 0

    for path in files:
        text = read_text(path)
        metadata, _, has_frontmatter = parse_frontmatter(text)

        if args.only_missing and has_frontmatter:
            skipped_count += 1
            continue

        fixed_text, issues = repair_content(path, text)

        # 没有问题，或者空文件跳过
        actionable_issues = [issue for issue in issues if issue != "空文件，跳过修复"]

        if not actionable_issues:
            skipped_count += 1
            continue

        rel_path = path.relative_to(KNOWLEDGE_ROOT)

        print("")
        print(f"[待修复] {rel_path}")
        for issue in issues:
            print(f"  - {issue}")

        changed_count += 1

        if args.execute:
            backup_original(path, backup_root)
            path.write_text(fixed_text, encoding="utf-8")
            print("  已修复并备份原文件。")

    print("")
    print("=== 修复总结 ===")
    print(f"需要修复文件数量：{changed_count}")
    print(f"跳过文件数量：{skipped_count}")

    if args.execute:
        print("")
        print("修复已执行。")
        print(f"原文件备份目录：{backup_root}")
        print("")
        print("建议下一步执行：")
        print("python validate_kb.py")
        print("python update_index.py")
    else:
        print("")
        print("当前为预览模式，未修改任何文件。")
        print("确认无误后执行：")
        print("python repair_frontmatter.py --execute")


if __name__ == "__main__":
    main()