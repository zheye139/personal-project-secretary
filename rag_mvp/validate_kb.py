import argparse
from pathlib import Path

from config import KNOWLEDGE_ROOT


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


def should_skip(path: Path) -> bool:
    parts = set(path.parts)
    return bool(parts.intersection(SKIP_DIR_NAMES))


def parse_frontmatter(text: str) -> tuple[dict, str, bool]:
    """
     :
    metadata: Frontmatter field
    body: body
    has_frontmatter: whetherexists Frontmatter
    """
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
        key = key.strip()
        value = value.strip()

        metadata[key] = value

    return metadata, body, True


def collect_markdown_files() -> list[Path]:
    files = []

    for path in KNOWLEDGE_ROOT.rglob("*.md"):
        if should_skip(path):
            continue

        #   99_System/docs  andcheck;skip 99_System  directory
        rel_parts = path.relative_to(KNOWLEDGE_ROOT).parts

        if len(rel_parts) >= 2 and rel_parts[0] == "99_System" and rel_parts[1] == "docs":
            files.append(path)
            continue

        if rel_parts and rel_parts[0] == "99_System":
            continue

        files.append(path)

    return sorted(files)


def validate_file(path: Path) -> list[str]:
    issues = []

    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8-sig")

    rel_path = path.relative_to(KNOWLEDGE_ROOT)

    if not text.strip():
        issues.append("empty file")
        return issues

    metadata, body, has_frontmatter = parse_frontmatter(text)

    if not has_frontmatter:
        issues.append("missing Frontmatter")
        return issues

    for field in REQUIRED_FIELDS:
        value = metadata.get(field, "").strip()
        if not value:
            issues.append(f"missingfield:{field}")

    category = metadata.get("category", "").strip()
    if category and category not in {
        "project",
        "knowledge",
        "decision",
        "problem",
        "summary",
        "attachment",
        "system",
    }:
        issues.append(f"category invalid:{category}")

    if metadata.get("tags", "").strip() in {"[]", ""}:
        issues.append("tags is empty")

    if not body.strip():
        issues.append("body is empty")

    if len(str(rel_path)) > 180:
        issues.append("path is too long, laternot maintenance")

    return issues


def write_report(results: dict[Path, list[str]]) -> Path:
    report_dir = KNOWLEDGE_ROOT / "05_Summaries" / "validation_reports"
    report_dir.mkdir(parents=True, exist_ok=True)

    from datetime import datetime

    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
    report_path = report_dir / f"{timestamp}_kb_validation_report.md"

    lines = []
    lines.append("---")
    lines.append(f"title: knowledge basestandardcheck report {timestamp}")
    lines.append(f"created: {now.isoformat(timespec='seconds')}")
    lines.append("category: summary")
    lines.append("project: Demo_Project")
    lines.append("doc_type: validation_report")
    lines.append("tags: [knowledge basecheck, validation, auto generated, M1.25]")
    lines.append("---")
    lines.append("")
    lines.append("# knowledge basestandardcheck report")
    lines.append("")
    lines.append(f"check time:{now.isoformat(timespec='seconds')}")
    lines.append("")
    lines.append(f"files with issuescount:{len(results)}")
    lines.append("")

    if not results:
        lines.append("not found standardissue. ")
    else:
        for path, issues in results.items():
            rel_path = path.relative_to(KNOWLEDGE_ROOT)
            lines.append(f"## {rel_path}")
            lines.append("")
            for issue in issues:
                lines.append(f"- {issue}")
            lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def main():
    parser = argparse.ArgumentParser(
        description="Personal Project Secretary + Knowledge Base:Markdown standardcheck tool"
    )

    parser.add_argument(
        "--write-report",
        action="store_true",
        help="check resultssaveas Markdown report. ",
    )

    parser.add_argument(
        "--show-ok",
        action="store_true",
        help="displaypassedcheckfile. ",
    )

    args = parser.parse_args()

    files = collect_markdown_files()

    print("Personal Project Secretary + Knowledge Base:Markdown validation check")
    print(f"knowledge base root:{KNOWLEDGE_ROOT}")
    print(f"check Markdown file count:{len(files)}")

    problem_results = {}
    ok_count = 0

    for path in files:
        issues = validate_file(path)

        rel_path = path.relative_to(KNOWLEDGE_ROOT)

        if issues:
            problem_results[path] = issues
            print("")
            print(f"[issue] {rel_path}")
            for issue in issues:
                print(f"  - {issue}")
        else:
            ok_count += 1
            if args.show_ok:
                print(f"[passed] {rel_path}")

    print("")
    print("=== check summary ===")
    print(f"passedfile count:{ok_count}")
    print(f"files with issuescount:{len(problem_results)}")

    if args.write_report:
        report_path = write_report(problem_results)
        print("")
        print("check reportalready :")
        print(report_path)
        print("")
        print("recommended next command:")
        print("python update_index.py")


if __name__ == "__main__":
    main()