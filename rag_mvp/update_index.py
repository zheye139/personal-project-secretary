import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).parent.resolve()


def run_step(title: str, command: list[str]) -> bool:
    """
    execute a , and stage . 
    """
    print("\n" + "=" * 80)
    print(f"start:{title}")
    print("=" * 80)
    print("command:", " ".join(command))
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
            print(f"[failed] {title}")
            print(f"return code:{result.returncode}")
            return False

        print("")
        print(f"[completed] {title}")
        return True

    except Exception as e:
        print("")
        print(f"[exception] {title}")
        print(e)
        return False


def main():
    python_exe = sys.executable

    print("Personal Project Secretary + Knowledge Base:one-click ")
    print(f"working directory:{BASE_DIR}")
    print(f"Python:{python_exe}")

    steps = [
        (
            "environment check",
            [python_exe, "check_env.py"],
        ),
        (
            "re-  Markdown document",
            [python_exe, "ingest.py"],
        ),
        (
            "listalready document",
            [python_exe, "list_docs.py"],
        ),
    ]

    for title, command in steps:
        ok = run_step(title, command)
        if not ok:
            print("\n in . please firstrepair . ")
            return

    print("\n" + "=" * 80)
    print(" completed")
    print("=" * 80)
    print("")
    print(" incan execute:")
    print('python ask.py " recentadd record？"')


if __name__ == "__main__":
    main()