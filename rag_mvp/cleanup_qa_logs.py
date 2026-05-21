import argparse
import hashlib
import shutil
from pathlib import Path

from config import QA_LOG_DIR, QA_LOG_ARCHIVE_DIR


FAILED_PATTERNS = [
    "No relevant information was found in the current knowledge base.",
    "No relevant information was found.",
    "The current knowledge base lacks sufficient information to confirm.",
]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8-sig")


def extract_section(text: str, heading: str) -> str:
    """
    从 Markdown 中提取指定二级标题内容。
    例如 heading="用户问题" 或 heading="模型回答"。
    """
    marker = f"## {heading}"

    if marker not in text:
        return ""

    after = text.split(marker, 1)[1]

    next_heading_index = after.find("\n## ")
    if next_heading_index >= 0:
        after = after[:next_heading_index]

    return after.strip()


def is_failed_log(text: str) -> bool:
    """
    判断是否是失败/无效问答记录。
    """
    return any(pattern in text for pattern in FAILED_PATTERNS)


def make_duplicate_key(text: str) -> str:
    """
    根据用户问题 + 模型回答生成重复判断 key。
    """
    question = extract_section(text, "User Issues")
    answer = extract_section(text, "Model Response")

    raw = f"{question}\n---\n{answer}".strip()

    if not raw:
        raw = text.strip()

    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def collect_qa_logs() -> list[Path]:
    if not QA_LOG_DIR.exists():
        return []

    return sorted(QA_LOG_DIR.glob("*_qa.md"))


def analyze_logs(files: list[Path]) -> dict:
    """
    分析失败记录和重复记录。
    """
    failed_files = []
    duplicate_files = []

    seen = {}

    for file_path in files:
        text = read_text(file_path)

        if is_failed_log(text):
            failed_files.append(file_path)

        key = make_duplicate_key(text)

        if key in seen:
            # 保留第一份，后续重复的归档
            duplicate_files.append(file_path)
        else:
            seen[key] = file_path

    return {
        "failed": failed_files,
        "duplicate": duplicate_files,
    }


def move_files(files: list[Path], reason: str) -> None:
    """
    将文件移动到归档目录，不直接删除。
    """
    target_dir = QA_LOG_ARCHIVE_DIR / reason
    target_dir.mkdir(parents=True, exist_ok=True)

    for file_path in files:
        target_path = target_dir / file_path.name

        # 如果目标已存在，避免覆盖
        if target_path.exists():
            stem = file_path.stem
            suffix = file_path.suffix
            index = 1

            while True:
                candidate = target_dir / f"{stem}_{index}{suffix}"
                if not candidate.exists():
                    target_path = candidate
                    break
                index += 1

        shutil.move(str(file_path), str(target_path))
        print(f"Archived：{file_path.name} -> {target_path}")


def print_files(title: str, files: list[Path]) -> None:
    print(f"\n=== {title} ===")
    print(f"quantity：{len(files)}")

    if not files:
        return

    for file_path in files:
        print(f"- {file_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Clean up failed and duplicate question and answer records in qa_logs."
    )

    parser.add_argument(
        "--mode",
        choices=["failed", "duplicate", "all"],
        default="all",
        help="Cleanup modes: failed = failed records, duplicate = duplicate records, all = both are processed.",
    )

    parser.add_argument(
        "--execute",
        action="store_true",
        help="Performs actual archiving. By default, it only previews and does not move files.",
    )

    args = parser.parse_args()

    print("Personal project secretary + data knowledge base: qa_logs cleanup tool")
    print(f"Question and Answer History Directory:{QA_LOG_DIR}")
    print(f"Archive directory:{QA_LOG_ARCHIVE_DIR}")
    print(f"model:{args.mode}")
    print(f"Execute archive:{args.execute}")

    files = collect_qa_logs()

    print(f"\n The number of qa_log files was found:{len(files)}")

    if not files:
        print("No qa_log file was found.")
        return

    result = analyze_logs(files)

    failed_files = result["failed"]
    duplicate_files = result["duplicate"]

    if args.mode in ["failed", "all"]:
        print_files("Suspected failure / invalid Q&A record", failed_files)

    if args.mode in ["duplicate", "all"]:
        print_files("Suspected duplicate question and answer records", duplicate_files)

    if not args.execute:
        print("\n Currently in preview mode, no files have been moved.")
        print("Once everything is confirmed to be correct, the following steps can be taken:")
        print(f"python cleanup_qa_logs.py --mode {args.mode} --execute")
        return

    if args.mode in ["failed", "all"] and failed_files:
        move_files(failed_files, "failed")

    if args.mode in ["duplicate", "all"] and duplicate_files:
        # 避免同一个文件既是 failed 又是 duplicate 时重复移动
        remaining_duplicate_files = [p for p in duplicate_files if p.exists()]
        move_files(remaining_duplicate_files, "duplicate")

    print("\n Cleaning complete.")
    print("Recommended next steps:")
    print("python update_index.py")


if __name__ == "__main__":
    main()