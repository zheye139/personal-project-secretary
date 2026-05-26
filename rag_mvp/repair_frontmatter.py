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

        #   99_System/docs  andrepair
        if len(rel_parts) >= 2 and rel_parts[0] == "99_System" and rel_parts[1] == "docs":
            files.append(path)
            continue

        # skip 99_System  directory
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
        return "Demo_Project"

    if category in {"knowledge", "decision", "problem", "summary", "system"}:
        return "Demo_Project"

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

    tags.append("automatic Frontmatter")

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

    # if is ,  as 
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

    # if documentonlyhas type,  has doc_type,   type not 
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

    #  alreadyhasfield
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
        issues.append("empty file, skiprepair")
        return text, issues

    if not has_frontmatter:
        issues.append("  Frontmatter")

    fixed_metadata = build_fixed_metadata(path, metadata)

    for field in REQUIRED_FIELDS:
        old_value = metadata.get(field, "").strip()
        new_value = fixed_metadata.get(field, "").strip()

        if not old_value:
            issues.append(f" field:{field} = {new_value}")

    if metadata.get("tags", "").strip() in {"", "[]"}:
        issues.append(f"  tags:{fixed_metadata.get('tags', '')}")

    fixed_frontmatter = build_frontmatter(fixed_metadata)

    fixed_body = body.strip()

    if not fixed_body:
        fixed_body = f"# {fixed_metadata['title']}\n\n content. "
        issues.append("body is empty,  body")

    fixed_text = fixed_frontmatter + fixed_body + "\n"

    return fixed_text, issues


def backup_original(path: Path, backup_root: Path) -> None:
    rel_path = path.relative_to(KNOWLEDGE_ROOT)
    target_path = backup_root / rel_path
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target_path)


def main():
    parser = argparse.ArgumentParser(
        description="Personal Project Secretary + Knowledge Base:batchrepair Markdown Frontmatter"
    )

    parser.add_argument(
        "--execute",
        action="store_true",
        help="actually repair . defaultonlypreview, not file. ",
    )

    parser.add_argument(
        "--only-missing",
        action="store_true",
        help="onlyrepairmissing Frontmatter file;default repairmissingfieldfile. ",
    )

    args = parser.parse_args()

    files = collect_markdown_files()

    print("Personal Project Secretary + Knowledge Base:Frontmatter repairtool")
    print(f"knowledge base root:{KNOWLEDGE_ROOT}")
    print(f"check Markdown file count:{len(files)}")
    print(f"executerepair:{args.execute}")

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

        #  has issue, or empty fileskip
        actionable_issues = [issue for issue in issues if issue != "empty file, skiprepair"]

        if not actionable_issues:
            skipped_count += 1
            continue

        rel_path = path.relative_to(KNOWLEDGE_ROOT)

        print("")
        print(f"[ repair] {rel_path}")
        for issue in issues:
            print(f"  - {issue}")

        changed_count += 1

        if args.execute:
            backup_original(path, backup_root)
            path.write_text(fixed_text, encoding="utf-8")
            print("  alreadyrepairandbackup file. ")

    print("")
    print("=== repairsummary ===")
    print(f" repairfile count:{changed_count}")
    print(f"skipfile count:{skipped_count}")

    if args.execute:
        print("")
        print("repairalreadyexecute. ")
        print(f" filebackup directory:{backup_root}")
        print("")
        print("recommended next command:")
        print("python validate_kb.py")
        print("python update_index.py")
    else:
        print("")
        print(" aspreview mode,  file. ")
        print("After confirmation, run:")
        print("python repair_frontmatter.py --execute")


if __name__ == "__main__":
    main()