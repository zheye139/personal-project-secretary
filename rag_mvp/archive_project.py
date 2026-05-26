import argparse
import shutil
from datetime import datetime
from pathlib import Path

from config import KNOWLEDGE_ROOT


PROJECT_ROOT = KNOWLEDGE_ROOT / "01_Projects"
ARCHIVE_ROOT = KNOWLEDGE_ROOT / "01_Projects_Archived"


def project_path(project: str) -> Path:
    """
    Get the current project path.
    """
    return PROJECT_ROOT / project


def archive_path(project: str) -> Path:
    """
    Build a timestamped archive path to avoid overwriting existing archives.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return ARCHIVE_ROOT / f"{timestamp}_{project}"


def count_files(path: Path) -> int:
    """
    Count files in a directory.
    """
    if not path.exists():
        return 0

    return sum(1 for p in path.rglob("*") if p.is_file())


def write_archive_note(target_dir: Path, project: str, source_dir: Path) -> None:
    """
    Write ARCHIVED.md in the archived project directory.
    """
    note_path = target_dir / "ARCHIVED.md"
    now = datetime.now().isoformat(timespec="seconds")

    content = f"""---
title: {project} Project Archive Records
created: {now}
category: project
project: {project}
doc_type: archived_project
tags: [Project Archive, archive, M1.24]
---

# {project} Project Archive Records

## Archive time

{now}

## Reason for archiving

Please add the reason for archiving here.

## Archiving Instructions

The project has been completed from:

```text
{source_dir}
```

Move to:

```text
{target_dir}
```

## Follow-up processing

To restore, the directory can be moved back:

```text
{source_dir}
```

Recommended actions after recovery:

```powershell
python update_index.py
python status.py
```
"""

    note_path.write_text(content, encoding="utf-8")


def archive_project(project: str, execute: bool = False) -> None:
    """
    Archive the specified project directory.

    Preview by default and do not move files.
    Move the directory only when --execute is provided.
    """
    src = project_path(project)

    if not src.exists():
        print(f"[error] Project does not exist:{src}")
        return

    if not src.is_dir():
        print(f"[error] The target is not a directory:{src}")
        return

    dst = archive_path(project)
    file_count = count_files(src)

    print("Personal Project Secretary + Data Knowledge Base: Project Archiving Tool")
    print("")
    print(f"Project Name:{project}")
    print(f"Source directory:{src}")
    print(f"Target Archive Directory:{dst}")
    print(f"Number of files:{file_count}")
    print(f"Perform archiving:{execute}")

    if not execute:
        print("")
        print("Currently in preview mode, no files have been moved.")
        print("Execute after confirming that everything is correct:")
        print(f"python archive_project.py --project {project} --execute")
        return

    ARCHIVE_ROOT.mkdir(parents=True, exist_ok=True)

    if dst.exists():
        print(f"[error] The target archive directory already exists: {dst}")
        print("Please try again later, or check the archive directory manually.")
        return

    shutil.move(str(src), str(dst))
    write_archive_note(
        target_dir=dst,
        project=project,
        source_dir=src,
    )

    print("")
    print("The project has been archived:")
    print(dst)
    print("")
    print("Recommended next steps:")
    print("python update_index.py")
    print("")
    print("illustrate:")
    print("If the project is a test project and you do not want the archived content to be stored in the repository, you can prevent 01_Projects_Archived from being collected by ingest.py.")


def main():
    parser = argparse.ArgumentParser(
        description="Personal Project Secretary + Data Knowledge Base: Securely Archived Project Catalog"
    )

    parser.add_argument(
        "--project",
        required=True,
        help="The name of the project directory to be archived, for example Test_Project",
    )

    parser.add_argument(
        "--execute",
        action="store_true",
        help="Performs actual archiving. By default, it only previews and does not move files.",
    )

    args = parser.parse_args()

    archive_project(
        project=args.project,
        execute=args.execute,
    )


if __name__ == "__main__":
    main()