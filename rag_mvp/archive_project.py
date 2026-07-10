import argparse
import shutil
from datetime import datetime
from pathlib import Path

from config import KNOWLEDGE_ROOT


PROJECT_ROOT = KNOWLEDGE_ROOT / "01_Projects"
ARCHIVE_ROOT = KNOWLEDGE_ROOT / "01_Projects_Archived"


def project_path(project: str) -> Path:
    """
    获取项目当前路径。
    """
    return PROJECT_ROOT / project


def archive_path(project: str) -> Path:
    """
    生成带时间戳的归档路径，避免覆盖历史归档。
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return ARCHIVE_ROOT / f"{timestamp}_{project}"


def count_files(path: Path) -> int:
    """
    统计目录中的文件数量。
    """
    if not path.exists():
        return 0

    return sum(1 for p in path.rglob("*") if p.is_file())


def write_archive_note(target_dir: Path, project: str, source_dir: Path) -> None:
    """
    在归档目录中写入 ARCHIVED.md，记录归档信息。
    """
    note_path = target_dir / "ARCHIVED.md"
    now = datetime.now().isoformat(timespec="seconds")

    content = f"""---
title: {project} 项目归档记录
created: {now}
category: project
project: {project}
doc_type: archived_project
tags: [项目归档, archive, M1.24]
---

# {project} 项目归档记录

## 归档时间

{now}

## 归档原因

请在这里补充归档原因。

## 归档说明

该项目已从：

```text
{source_dir}
```

移动到：

```text
{target_dir}
```

## 后续处理

如需恢复，可将该目录重新移动回：

```text
{source_dir}
```

恢复后建议执行：

```powershell
python update_index.py
python status.py
```
"""

    note_path.write_text(content, encoding="utf-8")


def archive_project(project: str, execute: bool = False) -> None:
    """
    归档指定项目目录。

    默认只预览，不移动文件。
    使用 --execute 后才会真正移动目录。
    """
    src = project_path(project)

    if not src.exists():
        print(f"[错误] 项目不存在：{src}")
        return

    if not src.is_dir():
        print(f"[错误] 目标不是目录：{src}")
        return

    dst = archive_path(project)
    file_count = count_files(src)

    print("个人项目秘书 + 数据知识库：项目归档工具")
    print("")
    print(f"项目名称：{project}")
    print(f"源目录：{src}")
    print(f"目标归档目录：{dst}")
    print(f"文件数量：{file_count}")
    print(f"执行归档：{execute}")

    if not execute:
        print("")
        print("当前为预览模式，未移动任何文件。")
        print("确认无误后执行：")
        print(f"python archive_project.py --project {project} --execute")
        return

    ARCHIVE_ROOT.mkdir(parents=True, exist_ok=True)

    if dst.exists():
        print(f"[错误] 目标归档目录已存在：{dst}")
        print("请稍后重试，或手动检查归档目录。")
        return

    shutil.move(str(src), str(dst))
    write_archive_note(
        target_dir=dst,
        project=project,
        source_dir=src,
    )

    print("")
    print("项目已归档：")
    print(dst)
    print("")
    print("建议下一步执行：")
    print("python update_index.py")
    print("")
    print("说明：")
    print("如果该项目是测试项目，并且不希望归档内容入库，可以保持 01_Projects_Archived 不被 ingest.py 收集。")


def main():
    parser = argparse.ArgumentParser(
        description="个人项目秘书 + 数据知识库：安全归档项目目录"
    )

    parser.add_argument(
        "--project",
        required=True,
        help="要归档的项目目录名，例如 Test_Project",
    )

    parser.add_argument(
        "--execute",
        action="store_true",
        help="真正执行归档。默认只预览，不移动文件。",
    )

    args = parser.parse_args()

    archive_project(
        project=args.project,
        execute=args.execute,
    )


if __name__ == "__main__":
    main()