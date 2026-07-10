import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

from config import KNOWLEDGE_ROOT, PROJECT_EXPORT_DIR


PROJECTS_DIR = KNOWLEDGE_ROOT / "01_Projects"


SKIP_DIR_NAMES = {
    ".venv",
    "__pycache__",
    "backups",
    "qdrant_storage",
    "qdrant_local",
    "_imported",
}


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
        metadata[key.strip()] = value.strip().strip('"').strip("'")

    return metadata, body, True


def should_skip(path: Path) -> bool:
    parts = set(path.parts)
    return bool(parts.intersection(SKIP_DIR_NAMES))


def is_project_related_markdown(path: Path, project: str) -> bool:
    """
    判断一个 Markdown 是否属于指定项目。

    判断规则：
    1. 01_Projects/project 目录下的文件属于该项目。
    2. Frontmatter 中 project 等于目标 project 的文件属于该项目。
    """
    if should_skip(path):
        return False

    try:
        rel_parts = path.relative_to(KNOWLEDGE_ROOT).parts
    except ValueError:
        return False

    if len(rel_parts) >= 2 and rel_parts[0] == "01_Projects" and rel_parts[1] == project:
        return True

    if path.suffix.lower() != ".md":
        return False

    try:
        text = read_text(path)
    except Exception:
        return False

    metadata, _, _ = parse_frontmatter(text)
    return metadata.get("project", "") == project


def collect_project_files(project: str, include_summaries: bool = True) -> list[Path]:
    files = []

    for path in KNOWLEDGE_ROOT.rglob("*"):
        if not path.is_file():
            continue

        if should_skip(path):
            continue

        if path.suffix.lower() != ".md":
            continue

        # 默认导出项目本体、问题、决策、总结等所有 Frontmatter project 匹配的 Markdown
        if is_project_related_markdown(path, project):
            if not include_summaries:
                rel_parts = path.relative_to(KNOWLEDGE_ROOT).parts
                if rel_parts and rel_parts[0] == "05_Summaries":
                    continue
            files.append(path)

    return sorted(set(files))


def run_list_docs_snapshot(project: str, output_path: Path) -> None:
    """
    保存当前 list_docs.py 输出，作为导出包快照。
    """
    base_dir = Path(__file__).parent.resolve()
    python_exe = sys.executable

    result = subprocess.run(
        [python_exe, "list_docs.py"],
        cwd=base_dir,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
    )

    now = datetime.now().isoformat(timespec="seconds")

    lines = [
        "---",
        f"title: {project} 导出时入库文档快照",
        f"created: {now}",
        "category: summary",
        f"project: {project}",
        "doc_type: export_snapshot",
        "tags: [项目导出, list_docs, 自动生成]",
        "---",
        "",
        f"# {project} 导出时入库文档快照",
        "",
        f"生成时间：{now}",
        "",
        "```text",
        result.stdout,
    ]

    if result.stderr:
        lines.extend(
            [
                "",
                "[stderr]",
                result.stderr,
            ]
        )

    lines.extend(
        [
            "```",
            "",
        ]
    )

    output_path.write_text("\n".join(lines), encoding="utf-8")


def create_manifest(project: str, files: list[Path], output_path: Path) -> None:
    now = datetime.now().isoformat(timespec="seconds")

    lines = [
        "---",
        f"title: {project} 项目导出清单",
        f"created: {now}",
        "category: summary",
        f"project: {project}",
        "doc_type: export_manifest",
        "tags: [项目导出, manifest, 自动生成]",
        "---",
        "",
        f"# {project} 项目导出清单",
        "",
        f"导出时间：{now}",
        f"文件数量：{len(files)}",
        "",
        "## 文件列表",
        "",
    ]

    for path in files:
        rel_path = path.relative_to(KNOWLEDGE_ROOT)
        lines.append(f"- {rel_path}")

    lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")


def create_zip(project: str, files: list[Path], export_zip_path: Path, extra_files: list[Path]) -> None:
    with ZipFile(export_zip_path, "w", ZIP_DEFLATED) as zipf:
        for file_path in files:
            arcname = file_path.relative_to(KNOWLEDGE_ROOT)
            zipf.write(file_path, arcname)

        for file_path in extra_files:
            arcname = Path("_export_metadata") / file_path.name
            zipf.write(file_path, arcname)


def export_project(project: str, include_summaries: bool = True) -> None:
    project_dir = PROJECTS_DIR / project

    if not project_dir.exists():
        print(f"[警告] 项目主目录不存在：{project_dir}")
        print("仍会尝试根据 Frontmatter project 字段导出相关文件。")

    files = collect_project_files(
        project=project,
        include_summaries=include_summaries,
    )

    print("个人项目秘书 + 数据知识库：项目导出工具")
    print("")
    print(f"项目名称：{project}")
    print(f"项目主目录：{project_dir}")
    print(f"导出文件数量：{len(files)}")

    if not files:
        print("")
        print("未找到可导出的项目文件。")
        return

    PROJECT_EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    export_base_name = f"{timestamp}_{project}_export"
    temp_dir = PROJECT_EXPORT_DIR / export_base_name
    temp_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = temp_dir / "export_manifest.md"
    snapshot_path = temp_dir / "list_docs_snapshot.md"

    create_manifest(project, files, manifest_path)
    run_list_docs_snapshot(project, snapshot_path)

    export_zip_path = PROJECT_EXPORT_DIR / f"{export_base_name}.zip"

    create_zip(
        project=project,
        files=files,
        export_zip_path=export_zip_path,
        extra_files=[manifest_path, snapshot_path],
    )

    print("")
    print("项目导出完成：")
    print(export_zip_path)
    print("")
    print("导出包中包含：")
    print("1. 项目相关 Markdown 文件")
    print("2. _export_metadata/export_manifest.md")
    print("3. _export_metadata/list_docs_snapshot.md")
    print("")
    print("建议下一步：")
    print("1. 打开 zip 检查内容。")
    print("2. 如果确认无误，可以执行 python backup_kb.py 做全库备份。")


def main():
    parser = argparse.ArgumentParser(
        description="个人项目秘书 + 数据知识库：按项目导出资料包"
    )

    parser.add_argument(
        "--project",
        required=True,
        help="要导出的项目名，例如 Personal_Project_Assistant",
    )

    parser.add_argument(
        "--no-summaries",
        action="store_true",
        help="不导出 05_Summaries 下的项目报告、问答记录、日报周报等总结文件。",
    )

    args = parser.parse_args()

    export_project(
        project=args.project,
        include_summaries=not args.no_summaries,
    )


if __name__ == "__main__":
    main()