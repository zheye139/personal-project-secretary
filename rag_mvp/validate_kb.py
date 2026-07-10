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
    返回：
    metadata: Frontmatter 字段
    body: 正文
    has_frontmatter: 是否存在 Frontmatter
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

        # 允许 99_System/docs 入库和检查；跳过 99_System 其他目录
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
        issues.append("空文件")
        return issues

    metadata, body, has_frontmatter = parse_frontmatter(text)

    if not has_frontmatter:
        issues.append("缺少 Frontmatter")
        return issues

    for field in REQUIRED_FIELDS:
        value = metadata.get(field, "").strip()
        if not value:
            issues.append(f"缺少字段：{field}")

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
        issues.append(f"category 不规范：{category}")

    if metadata.get("tags", "").strip() in {"[]", ""}:
        issues.append("tags 为空")

    if not body.strip():
        issues.append("正文为空")

    if len(str(rel_path)) > 180:
        issues.append("路径过长，后续不方便维护")

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
    lines.append(f"title: 知识库规范检查报告 {timestamp}")
    lines.append(f"created: {now.isoformat(timespec='seconds')}")
    lines.append("category: summary")
    lines.append("project: Personal_Project_Assistant")
    lines.append("doc_type: validation_report")
    lines.append("tags: [知识库检查, validation, 自动生成, M1.25]")
    lines.append("---")
    lines.append("")
    lines.append("# 知识库规范检查报告")
    lines.append("")
    lines.append(f"检查时间：{now.isoformat(timespec='seconds')}")
    lines.append("")
    lines.append(f"问题文件数量：{len(results)}")
    lines.append("")

    if not results:
        lines.append("未发现明显规范问题。")
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
        description="个人项目秘书 + 数据知识库：Markdown 规范检查工具"
    )

    parser.add_argument(
        "--write-report",
        action="store_true",
        help="将检查结果保存为 Markdown 报告。",
    )

    parser.add_argument(
        "--show-ok",
        action="store_true",
        help="显示通过检查的文件。",
    )

    args = parser.parse_args()

    files = collect_markdown_files()

    print("个人项目秘书 + 数据知识库：Markdown 规范检查")
    print(f"知识库根目录：{KNOWLEDGE_ROOT}")
    print(f"检查 Markdown 文件数量：{len(files)}")

    problem_results = {}
    ok_count = 0

    for path in files:
        issues = validate_file(path)

        rel_path = path.relative_to(KNOWLEDGE_ROOT)

        if issues:
            problem_results[path] = issues
            print("")
            print(f"[问题] {rel_path}")
            for issue in issues:
                print(f"  - {issue}")
        else:
            ok_count += 1
            if args.show_ok:
                print(f"[通过] {rel_path}")

    print("")
    print("=== 检查总结 ===")
    print(f"通过文件数量：{ok_count}")
    print(f"问题文件数量：{len(problem_results)}")

    if args.write_report:
        report_path = write_report(problem_results)
        print("")
        print("检查报告已生成：")
        print(report_path)
        print("")
        print("建议下一步执行：")
        print("python update_index.py")


if __name__ == "__main__":
    main()