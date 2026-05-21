import argparse
import os
import re
from datetime import datetime
from pathlib import Path

from config import KNOWLEDGE_ROOT


CATEGORY_DIR_MAP = {
    "project": "01_Projects",
    "knowledge": "02_Knowledge",
    "decision": "03_Decisions",
    "problem": "04_Problems",
    "summary": "05_Summaries",
}


DEFAULT_DOC_TYPE_MAP = {
    "project": "project_note",
    "knowledge": "knowledge_note",
    "decision": "decision",
    "problem": "issue",
    "summary": "summary",
}


def sanitize_filename(text: str) -> str:
    """
    将标题转换成适合 Windows 文件名的字符串。
    """
    text = text.strip()
    text = re.sub(r'[\\/:*?"<>|]', "_", text)
    text = re.sub(r"\s+", "_", text)
    return text[:80] if text else "untitled"


def parse_tags(raw_tags: str | None) -> list[str]:
    """
    将逗号分隔的标签字符串转成列表。
    示例：
    "RAG, Qdrant, 问题记录"
    """
    if not raw_tags:
        return []

    return [tag.strip() for tag in raw_tags.split(",") if tag.strip()]


def read_content(args) -> str:
    """
    优先使用 --content。
    如果没有 --content，但提供了 --from-file，则从文件读取。
    如果都没有，则进入交互输入。
    """
    if args.content:
        return args.content.strip()

    if args.from_file:
        path = Path(args.from_file)
        if not path.exists():
            raise FileNotFoundError(f"Content file does not exist: {path}")
        return path.read_text(encoding="utf-8").strip()

    print("Please enter the note content. Press Ctrl+Z and then Enter to finish:")
    import sys
    return sys.stdin.read().strip()


def build_target_dir(category: str, project: str | None) -> Path:
    """
    根据 category 和 project 生成保存目录。
    """
    if category not in CATEGORY_DIR_MAP:
        raise ValueError(
            f"Not supported category：{category}。"
            f"Optional value：{', '.join(CATEGORY_DIR_MAP.keys())}"
        )

    root_dir = KNOWLEDGE_ROOT / CATEGORY_DIR_MAP[category]

    if category == "project":
        if not project:
            raise ValueError("category=project must be provided --project")
        return root_dir / project / "notes"

    if category in ["problem", "decision", "summary"]:
        if project:
            return root_dir / project
        return root_dir

    if category == "knowledge":
        if project:
            return root_dir / project
        return root_dir / "General"

    return root_dir


def build_markdown(
    title: str,
    category: str,
    project: str,
    doc_type: str,
    tags: list[str],
    content: str,
) -> str:
    """
    生成带 Frontmatter 的 Markdown 内容。
    """
    now = datetime.now().isoformat(timespec="seconds")
    tag_text = "[" + ", ".join(tags) + "]" if tags else "[]"

    lines = [
        "---",
        f"title: {title}",
        f"created: {now}",
        f"category: {category}",
        f"project: {project}",
        f"doc_type: {doc_type}",
        f"tags: {tag_text}",
        "---",
        "",
        f"# {title}",
        "",
        content,
        "",
    ]

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Personal Project Secretary + Knowledge Base: add a Markdown note."
    )

    parser.add_argument(
        "--category",
        required=True,
        choices=["project", "knowledge", "decision", "problem", "summary"],
        help="Note category: project / knowledge / decision / problem / summary",
    )

    parser.add_argument(
        "--project",
        default="Demo_Project",
        help="Project name, for example: Demo_Project.",
    )

    parser.add_argument(
        "--doc-type",
        default=None,
        help="Document type, for example: progress_log, issue, decision, summary, knowledge_note.",
    )

    parser.add_argument(
        "--title",
        required=True,
        help="Note title.",
    )

    parser.add_argument(
        "--tags",
        default=None,
        help="Tags separated by commas, for example: RAG,Qdrant,issue.",
    )

    parser.add_argument(
        "--content",
        default=None,
        help="Note content.",
    )

    parser.add_argument(
        "--from-file",
        default=None,
        help="Read note content from a text file.",
    )

    args = parser.parse_args()

    category = args.category
    project = args.project
    doc_type = args.doc_type or DEFAULT_DOC_TYPE_MAP[category]
    tags = parse_tags(args.tags)
    content = read_content(args)

    if not content:
        raise ValueError("Note content cannot be empty. Please use --content or --from-file.")

    target_dir = build_target_dir(category=category, project=project)
    target_dir.mkdir(parents=True, exist_ok=True)

    date_prefix = datetime.now().strftime("%Y-%m-%d")
    file_name = f"{date_prefix}_{sanitize_filename(args.title)}.md"
    file_path = target_dir / file_name

    markdown = build_markdown(
        title=args.title,
        category=category,
        project=project,
        doc_type=doc_type,
        tags=tags,
        content=content,
    )

    file_path.write_text(markdown, encoding="utf-8")

    print("Record created：")
    print(file_path)
    print("")
    print("Next step:")
    print("python ingest.py")


if __name__ == "__main__":
    main()