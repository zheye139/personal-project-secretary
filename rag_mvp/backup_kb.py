import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

from config import KNOWLEDGE_ROOT, BACKUP_DIR


EXCLUDE_DIR_NAMES = {
    ".venv",
    "__pycache__",
    "qdrant_storage",
    "qdrant_local",
    "backups",
}

EXCLUDE_FILE_SUFFIXES = {
    ".pyc",
    ".log",
    ".tmp",
}


def should_skip(path: Path) -> bool:
    """
    判断文件或目录是否需要跳过。
    """
    parts = set(path.parts)

    if parts.intersection(EXCLUDE_DIR_NAMES):
        return True

    if path.is_file() and path.suffix.lower() in EXCLUDE_FILE_SUFFIXES:
        return True

    return False


def collect_files() -> list[Path]:
    """
    收集需要备份的文件。
    默认备份整个知识库根目录，但排除虚拟环境、缓存、Qdrant 数据目录和历史备份。
    """
    files = []

    for path in KNOWLEDGE_ROOT.rglob("*"):
        if should_skip(path):
            continue

        if path.is_file():
            files.append(path)

    return files


def run_list_docs(output_path: Path) -> None:
    """
    执行 list_docs.py，把当前入库文档状态保存到备份目录。
    """
    base_dir = Path(__file__).parent.resolve()
    python_exe = sys.executable

    result = subprocess.run(
        [python_exe, "list_docs.py"],
        cwd=base_dir,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
    )

    content = []
    content.append("# Current list of documents added to the database")
    content.append("")
    content.append(f"Generation time：{datetime.now().isoformat(timespec='seconds')}")
    content.append("")
    content.append("```text")
    content.append(result.stdout)

    if result.stderr:
        content.append("")
        content.append("[stderr]")
        content.append(result.stderr)

    content.append("```")
    content.append("")

    output_path.write_text("\n".join(content), encoding="utf-8")


def create_zip_backup(files: list[Path], backup_zip_path: Path) -> None:
    """
    创建 zip 备份包。
    """
    with ZipFile(backup_zip_path, "w", ZIP_DEFLATED) as zipf:
        for file_path in files:
            arcname = file_path.relative_to(KNOWLEDGE_ROOT)
            zipf.write(file_path, arcname)


def main():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_name = f"{timestamp}_Personal_Knowledge_Base_backup"
    temp_dir = BACKUP_DIR / backup_name
    temp_dir.mkdir(parents=True, exist_ok=True)

    print("Personal Project Secretary + Data Knowledge Base: Backup Tool")
    print(f"Knowledge Base Root Directory：{KNOWLEDGE_ROOT}")
    print(f"Backup output directory：{BACKUP_DIR}")

    print("\n Generating a list of currently added documents...")
    list_docs_path = temp_dir / "list_docs_snapshot.md"
    run_list_docs(list_docs_path)

    print("Collecting files that need to be backed up...")
    files = collect_files()

    # 把 list_docs_snapshot.md 也加入备份
    files.append(list_docs_path)

    print(f"Number of files to be backed up：{len(files)}")

    backup_zip_path = BACKUP_DIR / f"{backup_name}.zip"

    print("Creating a zip backup package...")
    create_zip_backup(files, backup_zip_path)

    # 清理临时目录
    try:
        shutil.rmtree(temp_dir)
    except Exception:
        pass

    print("\n Backup complete:")
    print(backup_zip_path)
    print("")
    print("suggestion:")
    print("1. Regularly copy the backups directory to an external hard drive or cloud storage.")
    print("2. Run `python backup_kb.py` once after each stage is completed.")
    print("3. If the Qdrant data becomes important later, add a dedicated backup for the Docker volume.")


if __name__ == "__main__":
    main()