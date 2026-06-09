import argparse
import os
import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).parent.resolve()


# ============================================================
# Windows / PowerShell 中文输出处理
# ============================================================

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def run_command(title: str, command: list[str]) -> int:
    """
    执行子命令，并实时显示输出。
    """
    print("")
    print("=" * 80)
    print(f"开始：{title}")
    print("=" * 80)
    print("执行命令：", " ".join(command))
    print("")

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    result = subprocess.run(
        command,
        cwd=BASE_DIR,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )

    if result.returncode != 0:
        print("")
        print(f"[失败] {title}")
        print(f"返回码：{result.returncode}")
    else:
        print("")
        print(f"[完成] {title}")

    return result.returncode


def main():
    parser = argparse.ArgumentParser(
        description="个人项目秘书 + 数据知识库：默认增量更新索引"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只分析增量变化，不修改 Qdrant，也不写入 manifest。",
    )

    parser.add_argument(
        "--force-all",
        action="store_true",
        help="强制所有 Markdown 重新入库，用于首次补齐 point_ids。",
    )

    parser.add_argument(
        "--file",
        default=None,
        help=(
            "只更新指定 Markdown 文件。"
            "支持绝对路径，或相对于 KNOWLEDGE_ROOT 的路径。"
        ),
    )

    parser.add_argument(
        "--force-file",
        action="store_true",
        help="与 --file 一起使用，强制重建该文件，即使文件未变化。",
    )

    parser.add_argument(
        "--project",
        default=None,
        help="只更新指定项目相关 Markdown 文件。",
    )

    parser.add_argument(
        "--force-project",
        action="store_true",
        help="与 --project 一起使用，强制重建该项目全部现存 Markdown 文件。",
    )

    parser.add_argument(
        "--skip-check",
        action="store_true",
        help="跳过 check_env.py。",
    )

    parser.add_argument(
        "--skip-list-docs",
        action="store_true",
        help="跳过 list_docs.py。",
    )

    args = parser.parse_args()

    selected_modes = [
        bool(args.file),
        bool(args.project),
    ]

    if sum(selected_modes) > 1:
        print("[失败] --file 和 --project 不能同时使用。")
        raise SystemExit(1)

    print("个人项目秘书 + 数据知识库：索引更新")
    print("模式：默认增量更新")
    print(f"工作目录：{BASE_DIR}")

    if args.file:
        print(f"单文件更新：{args.file}")

    if args.project:
        print(f"项目级更新：{args.project}")

    if not args.skip_check:
        code = run_command(
            title="环境自检",
            command=[sys.executable, "check_env.py"],
        )

        if code != 0:
            print("")
            print("索引更新中断。请先修复环境自检错误。")
            raise SystemExit(code)

    incremental_command = [sys.executable, "incremental_index.py"]

    if args.dry_run:
        incremental_command.append("--dry-run")

    if args.force_all:
        incremental_command.append("--force-all")

    if args.file:
        incremental_command.extend(["--file", args.file])

    if args.force_file:
        incremental_command.append("--force-file")

    if args.project:
        incremental_command.extend(["--project", args.project])

    if args.force_project:
        incremental_command.append("--force-project")

    code = run_command(
        title="执行增量索引",
        command=incremental_command,
    )

    if code != 0:
        print("")
        print("索引更新中断。请先修复增量索引错误。")
        raise SystemExit(code)

    if not args.skip_list_docs and not args.dry_run:
        code = run_command(
            title="列出已入库文档",
            command=[sys.executable, "list_docs.py"],
        )

        if code != 0:
            print("")
            print("索引更新中断。请先修复上面的错误。")
            raise SystemExit(code)

    print("")
    print("=" * 80)
    print("索引更新完成")
    print("=" * 80)
    print("")

    if args.file:
        print("单文件更新已完成。")
    elif args.project:
        print("项目级更新已完成。")
    else:
        print("增量索引更新已完成。")

    print("")
    print("建议下一步执行：")
    print('python ask.py "当前项目进行到哪里了？"')
    print('python search_docs.py "当前项目" --show-text')


if __name__ == "__main__":
    main()

