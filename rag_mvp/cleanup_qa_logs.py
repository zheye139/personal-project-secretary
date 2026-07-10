import argparse
import hashlib
import shutil
from pathlib import Path

from config import QA_LOG_DIR, QA_LOG_ARCHIVE_DIR


FAILED_PATTERNS = [
    "当前知识库没有检索到相关资料",
    "未检索到相关资料",
    "当前知识库资料不足，无法确认",
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
    question = extract_section(text, "用户问题")
    answer = extract_section(text, "模型回答")

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
        print(f"已归档：{file_path.name} -> {target_path}")


def print_files(title: str, files: list[Path]) -> None:
    print(f"\n=== {title} ===")
    print(f"数量：{len(files)}")

    if not files:
        return

    for file_path in files:
        print(f"- {file_path}")


def main():
    parser = argparse.ArgumentParser(
        description="清理 qa_logs 中的失败问答记录和重复问答记录"
    )

    parser.add_argument(
        "--mode",
        choices=["failed", "duplicate", "all"],
        default="all",
        help="清理模式：failed=失败记录，duplicate=重复记录，all=两者都处理",
    )

    parser.add_argument(
        "--execute",
        action="store_true",
        help="真正执行归档。默认只预览，不移动文件。",
    )

    args = parser.parse_args()

    print("个人项目秘书 + 数据知识库：qa_logs 清理工具")
    print(f"问答记录目录：{QA_LOG_DIR}")
    print(f"归档目录：{QA_LOG_ARCHIVE_DIR}")
    print(f"模式：{args.mode}")
    print(f"执行归档：{args.execute}")

    files = collect_qa_logs()

    print(f"\n发现 qa_log 文件数量：{len(files)}")

    if not files:
        print("没有发现 qa_log 文件。")
        return

    result = analyze_logs(files)

    failed_files = result["failed"]
    duplicate_files = result["duplicate"]

    if args.mode in ["failed", "all"]:
        print_files("疑似失败 / 无效问答记录", failed_files)

    if args.mode in ["duplicate", "all"]:
        print_files("疑似重复问答记录", duplicate_files)

    if not args.execute:
        print("\n当前为预览模式，未移动任何文件。")
        print("确认无误后可执行：")
        print(f"python cleanup_qa_logs.py --mode {args.mode} --execute")
        return

    if args.mode in ["failed", "all"] and failed_files:
        move_files(failed_files, "failed")

    if args.mode in ["duplicate", "all"] and duplicate_files:
        # 避免同一个文件既是 failed 又是 duplicate 时重复移动
        remaining_duplicate_files = [p for p in duplicate_files if p.exists()]
        move_files(remaining_duplicate_files, "duplicate")

    print("\n清理完成。")
    print("建议下一步执行：")
    print("python update_index.py")


if __name__ == "__main__":
    main()