import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).parent.resolve()


def run_step(title: str, command: list[str]) -> bool:
    """
    执行一个步骤，并打印清晰的阶段信息。
    """
    print("\n" + "=" * 80)
    print(f"开始：{title}")
    print("=" * 80)
    print("执行命令：", " ".join(command))
    print("")

    try:
        result = subprocess.run(
            command,
            cwd=BASE_DIR,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        if result.returncode != 0:
            print("")
            print(f"[失败] {title}")
            print(f"返回码：{result.returncode}")
            return False

        print("")
        print(f"[完成] {title}")
        return True

    except Exception as e:
        print("")
        print(f"[异常] {title}")
        print(e)
        return False


def main():
    python_exe = sys.executable

    print("个人项目秘书 + 数据知识库：一键更新索引")
    print(f"工作目录：{BASE_DIR}")
    print(f"Python：{python_exe}")

    steps = [
        (
            "环境自检",
            [python_exe, "check_env.py"],
        ),
        (
            "重新入库 Markdown 文档",
            [python_exe, "ingest.py"],
        ),
        (
            "列出已入库文档",
            [python_exe, "list_docs.py"],
        ),
    ]

    for title, command in steps:
        ok = run_step(title, command)
        if not ok:
            print("\n索引更新中断。请先修复上面的错误。")
            return

    print("\n" + "=" * 80)
    print("索引更新完成")
    print("=" * 80)
    print("")
    print("你现在可以继续执行：")
    print('python ask.py "当前项目最近新增了什么记录？"')


if __name__ == "__main__":
    main()