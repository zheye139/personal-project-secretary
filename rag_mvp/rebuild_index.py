import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import requests

from config import (
    QDRANT_URL,
    COLLECTION_NAME,
    KNOWLEDGE_ROOT,
    BACKUP_DIR,
)


BASE_DIR = Path(__file__).parent.resolve()


def run_command(title: str, command: list[str], capture: bool = False) -> subprocess.CompletedProcess:
    print("\n" + "=" * 80)
    print(f"开始：{title}")
    print("=" * 80)
    print("执行命令：", " ".join(command))
    print("")

    result = subprocess.run(
        command,
        cwd=BASE_DIR,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=capture,
    )

    if capture:
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("[stderr]")
            print(result.stderr)

    if result.returncode != 0:
        print(f"[失败] {title}")
        print(f"返回码：{result.returncode}")
    else:
        print(f"[完成] {title}")

    return result


def save_snapshot() -> Path:
    """
    在重建索引前保存当前 list_docs.py 输出。
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    snapshot_dir = BACKUP_DIR / "index_rebuild_snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    snapshot_path = snapshot_dir / f"{timestamp}_before_rebuild_list_docs.md"

    result = subprocess.run(
        [sys.executable, "list_docs.py"],
        cwd=BASE_DIR,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
    )

    lines = [
        "---",
        f"title: 重建索引前文档快照 {timestamp}",
        f"created: {datetime.now().isoformat(timespec='seconds')}",
        "category: summary",
        "project: Demo_Project",
        "doc_type: index_rebuild_snapshot",
        "tags: [索引重建, list_docs, 自动生成, M1.28]",
        "---",
        "",
        "# 重建索引前文档快照",
        "",
        f"生成时间：{datetime.now().isoformat(timespec='seconds')}",
        "",
        "```text",
        result.stdout,
    ]

    if result.stderr:
        lines.extend(
            [
                "",
                "[stderr]",
                result.stderr,
            ]
        )

    lines.extend(
        [
            "```",
            "",
        ]
    )

    snapshot_path.write_text("\n".join(lines), encoding="utf-8")
    return snapshot_path


def collection_exists() -> bool:
    url = f"{QDRANT_URL}/collections/{COLLECTION_NAME}/exists"

    try:
        resp = requests.get(url, timeout=20)
        if resp.status_code == 200:
            data = resp.json()
            return bool(data.get("result", {}).get("exists", False))
    except Exception:
        pass

    # 兼容方式：读取 collections 列表
    resp = requests.get(f"{QDRANT_URL}/collections", timeout=20)
    resp.raise_for_status()
    data = resp.json()

    collections = data.get("result", {}).get("collections", [])
    names = [item.get("name") for item in collections]
    return COLLECTION_NAME in names


def delete_collection() -> None:
    url = f"{QDRANT_URL}/collections/{COLLECTION_NAME}"
    resp = requests.delete(url, timeout=120)

    if resp.status_code in {200, 202}:
        print(f"[完成] 已删除集合：{COLLECTION_NAME}")
        return

    if resp.status_code == 404:
        print(f"[提示] 集合不存在，无需删除：{COLLECTION_NAME}")
        return

    print(f"[失败] 删除集合失败，状态码：{resp.status_code}")
    print(resp.text)
    resp.raise_for_status()


def main():
    parser = argparse.ArgumentParser(
        description="个人项目秘书 + 数据知识库：安全重建 Qdrant 索引"
    )

    parser.add_argument(
        "--execute",
        action="store_true",
        help="真正执行删除集合并重建索引。默认只预览。",
    )

    parser.add_argument(
        "--skip-snapshot",
        action="store_true",
        help="跳过重建前 list_docs 快照。",
    )

    args = parser.parse_args()

    print("个人项目秘书 + 数据知识库：索引重建工具")
    print(f"知识库根目录：{KNOWLEDGE_ROOT}")
    print(f"Qdrant 地址：{QDRANT_URL}")
    print(f"集合名称：{COLLECTION_NAME}")
    print(f"执行重建：{args.execute}")

    print("\n将执行的操作：")
    print("1. 运行 python check_env.py")
    print("2. 保存重建前 list_docs 快照")
    print(f"3. 删除 Qdrant 集合：{COLLECTION_NAME}")
    print("4. 运行 python ingest.py 重新入库")
    print("5. 运行 python list_docs.py 验证结果")

    if not args.execute:
        print("\n当前为预览模式，未删除集合，未重建索引。")
        print("确认无误后执行：")
        print("python rebuild_index.py --execute")
        return

    result = run_command(
        title="环境自检",
        command=[sys.executable, "check_env.py"],
    )

    if result.returncode != 0:
        print("\n环境自检失败，已中止。")
        return

    if not args.skip_snapshot:
        print("\n正在保存重建前文档快照...")
        snapshot_path = save_snapshot()
        print(f"快照已保存：{snapshot_path}")

    print("\n正在检查集合是否存在...")

    try:
        exists = collection_exists()
    except Exception as e:
        print(f"[失败] 无法检查集合状态：{e}")
        return

    if exists:
        print(f"集合存在，准备删除：{COLLECTION_NAME}")
        delete_collection()
    else:
        print(f"集合不存在，无需删除：{COLLECTION_NAME}")

    result = run_command(
        title="重新入库 Markdown 文档",
        command=[sys.executable, "ingest.py"],
    )

    if result.returncode != 0:
        print("\n重新入库失败，请根据上方错误修复。")
        return

    result = run_command(
        title="列出已入库文档",
        command=[sys.executable, "list_docs.py"],
    )

    if result.returncode != 0:
        print("\nlist_docs.py 执行失败，请检查。")
        return

    print("\n" + "=" * 80)
    print("索引重建完成")
    print("=" * 80)
    print("")
    print("建议下一步执行：")
    print("python status.py")
    print('python ask.py "当前项目的第一阶段模型方案是什么？"')


if __name__ == "__main__":
    main()