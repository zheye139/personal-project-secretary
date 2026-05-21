import argparse
import re
import shutil
from datetime import datetime
from pathlib import Path

from config import KNOWLEDGE_ROOT


INBOX_DIR = KNOWLEDGE_ROOT / "00_Inbox"
IMPORTED_DIR = INBOX_DIR / "_imported"


CATEGORY_DIR_MAP = {
    "project": "01_Projects",
    "knowledge": "02_Knowledge",
    "decision": "03_Decisions",
    "problem": "04_Problems",
    "summary": "05_Summaries",
    "attachment": "06_Attachments",
}


def sanitize_filename(text: str) -> str:
    text = text.strip()
    text = re.sub(r'[\\/:*?"<>|]', "_", text)
    text = re.sub(r"\s+", "_", text)
    return text[:80] if text else "untitled"


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """
    解析 Markdown 顶部 Frontmatter。
    支持：
    ---
    title: xxx
    category: project
    project: Demo_Project
    doc_type: progress_log
    tags: [RAG, 进度记录]
    ---
    """
    text = text.lstrip()

    if not text.startswith("---"):
        return {}, text

    parts = text.split("---", 2)

    if len(parts) < 3:
        return {}, text

    raw_meta = parts[1].strip()
    body = parts[2].strip()

    metadata = {}

    for line in raw_meta.splitlines():
        line = line.strip()

        if not line or ":" not in line:
            continue

        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()

        if value.startswith("[") and value.endswith("]"):
            items = value[1:-1].split(",")
            metadata[key] = [
                item.strip().strip('"').strip("'")
                for item in items
                if item.strip()
            ]
        else:
            metadata[key] = value.strip('"').strip("'")

    return metadata, body


def build_frontmatter(
    title: str,
    category: str,
    project: str,
    doc_type: str,
    tags: list[str],
    created: str,
) -> str:
    tag_text = "[" + ", ".join(tags) + "]" if tags else "[]"

    return "\n".join(
        [
            "---",
            f"title: {title}",
            f"created: {created}",
            f"category: {category}",
            f"project: {project}",
            f"doc_type: {doc_type}",
            f"tags: {tag_text}",
            "---",
            "",
        ]
    )


def infer_defaults(path: Path, metadata: dict) -> dict:
    """
    对缺失的 Frontmatter 字段做默认补全。
    """
    now = datetime.now().isoformat(timespec="seconds")

    title = metadata.get("title") or path.stem
    category = metadata.get("category") or "project"
    project = metadata.get("project") or "Demo_Project"
    doc_type = metadata.get("doc_type") or metadata.get("type") or "note"
    tags = metadata.get("tags") or []
    created = metadata.get("created") or now

    if isinstance(tags, str):
        tags = [tag.strip() for tag in tags.split(",") if tag.strip()]

    return {
        "title": title,
        "category": category,
        "project": project,
        "doc_type": doc_type,
        "tags": tags,
        "created": created,
    }


def build_target_dir(metadata: dict) -> Path:
    category = metadata["category"]
    project = metadata["project"]

    if category not in CATEGORY_DIR_MAP:
        raise ValueError(
            f"不支持的 category：{category}。"
            f"可选值：{', '.join(CATEGORY_DIR_MAP.keys())}"
        )

    root = KNOWLEDGE_ROOT / CATEGORY_DIR_MAP[category]

    if category == "project":
        return root / project / "notes"

    if category in ["problem", "decision", "summary"]:
        return root / project

    if category == "knowledge":
        return root / project

    if category == "attachment":
        return root / project

    return root


def build_target_file_path(source_path: Path, metadata: dict) -> Path:
    target_dir = build_target_dir(metadata)
    date_prefix = datetime.now().strftime("%Y-%m-%d")
    safe_title = sanitize_filename(metadata["title"])

    file_name = f"{date_prefix}_{safe_title}.md"
    target_path = target_dir / file_name

    if not target_path.exists():
        return target_path

    index = 1
    while True:
        candidate = target_dir / f"{date_prefix}_{safe_title}_{index}.md"
        if not candidate.exists():
            return candidate
        index += 1


def normalize_markdown(source_path: Path, metadata: dict, body: str) -> str:
    frontmatter = build_frontmatter(
        title=metadata["title"],
        category=metadata["category"],
        project=metadata["project"],
        doc_type=metadata["doc_type"],
        tags=metadata["tags"],
        created=metadata["created"],
    )

    body = body.strip()

    if not body.startswith("#"):
        body = f"# {metadata['title']}\n\n{body}"

    return frontmatter + body + "\n"


def collect_inbox_files() -> list[Path]:
    if not INBOX_DIR.exists():
        return []

    files = []

    for path in INBOX_DIR.glob("*.md"):
        if path.is_file():
            files.append(path)

    return sorted(files)


def import_file(source_path: Path, dry_run: bool = True) -> tuple[Path, Path]:
    text = source_path.read_text(encoding="utf-8")
    raw_metadata, body = parse_frontmatter(text)
    metadata = infer_defaults(source_path, raw_metadata)

    target_path = build_target_file_path(source_path, metadata)
    normalized_text = normalize_markdown(source_path, metadata, body)

    archive_path = IMPORTED_DIR / source_path.name

    if dry_run:
        return target_path, archive_path

    target_path.parent.mkdir(parents=True, exist_ok=True)
    IMPORTED_DIR.mkdir(parents=True, exist_ok=True)

    target_path.write_text(normalized_text, encoding="utf-8")

    if archive_path.exists():
        stem = archive_path.stem
        suffix = archive_path.suffix
        index = 1

        while True:
            candidate = IMPORTED_DIR / f"{stem}_{index}{suffix}"
            if not candidate.exists():
                archive_path = candidate
                break
            index += 1

    shutil.move(str(source_path), str(archive_path))

    return target_path, archive_path


def main():
    parser = argparse.ArgumentParser(
        description="个人项目秘书 + 数据知识库：导入 00_Inbox 中的 Markdown 文件"
    )

    parser.add_argument(
        "--execute",
        action="store_true",
        help="真正执行导入。默认只预览，不移动文件。",
    )

    args = parser.parse_args()
    dry_run = not args.execute

    print("个人项目秘书 + 数据知识库：Inbox 导入工具")
    print(f"Inbox 目录：{INBOX_DIR}")
    print(f"执行导入：{args.execute}")

    files = collect_inbox_files()

    print(f"\n发现 Inbox Markdown 文件数量：{len(files)}")

    if not files:
        print("没有发现可导入的 Markdown 文件。")
        return

    for source_path in files:
        try:
            target_path, archive_path = import_file(
                source_path=source_path,
                dry_run=dry_run,
            )

            print("\n---")
            print(f"源文件：{source_path}")
            print(f"目标文件：{target_path}")
            print(f"归档位置：{archive_path}")

        except Exception as e:
            print("\n---")
            print(f"处理失败：{source_path}")
            print(f"原因：{e}")

    if dry_run:
        print("\n当前为预览模式，未移动任何文件。")
        print("确认无误后执行：")
        print("python inbox_import.py --execute")
    else:
        print("\n导入完成。")
        print("建议下一步执行：")
        print("python update_index.py")


if __name__ == "__main__":
    main()