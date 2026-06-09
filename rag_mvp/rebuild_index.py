import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import requests

import config
import manifest_utils


# ============================================================
# 基础配置
# ============================================================

BASE_DIR = Path(__file__).parent.resolve()

KNOWLEDGE_ROOT = config.KNOWLEDGE_ROOT
QDRANT_URL = config.QDRANT_URL
COLLECTION_NAME = config.COLLECTION_NAME

BACKUP_DIR = getattr(
    config,
    "BACKUP_DIR",
    KNOWLEDGE_ROOT / "99_System" / "backups",
)

INDEX_MANIFEST_PATH = getattr(
    config,
    "INDEX_MANIFEST_PATH",
    KNOWLEDGE_ROOT / "99_System" / "index_manifest.json",
)


# ============================================================
# Windows / PowerShell 中文输出处理
# ============================================================

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def now_timestamp() -> str:
    """
    返回适合文件名使用的时间戳。
    """
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def now_iso() -> str:
    """
    返回 ISO 时间。
    """
    return datetime.now().isoformat(timespec="seconds")


def run_command(
    title: str,
    command: list[str],
    capture: bool = False,
    timeout: int = 1200,
) -> subprocess.CompletedProcess:
    """
    执行外部命令。

    capture=True 时捕获输出，适合写入快照。
    capture=False 时直接在终端显示输出。
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
        capture_output=capture,
        timeout=timeout,
        env=env,
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


def collection_exists_by_rest() -> bool:
    """
    通过 Qdrant REST API 判断 collection 是否存在。

    这里不用 qdrant_client，避免某些 shard 损坏时 client 调用触发异常。
    """
    url = f"{QDRANT_URL}/collections"

    resp = requests.get(url, timeout=30)
    resp.raise_for_status()

    data = resp.json()
    collections = data.get("result", {}).get("collections", [])
    names = [item.get("name") for item in collections]

    return COLLECTION_NAME in names


def delete_collection_by_rest() -> bool:
    """
    通过 REST API 删除 Qdrant collection。

    返回 True 表示已删除或原本不存在。
    """
    try:
        exists = collection_exists_by_rest()
    except Exception as e:
        print(f"[警告] 无法读取 collection 列表：{e}")
        exists = True

    if not exists:
        print(f"[提示] collection 不存在，无需删除：{COLLECTION_NAME}")
        return True

    url = f"{QDRANT_URL}/collections/{COLLECTION_NAME}"

    try:
        resp = requests.delete(url, timeout=120)
    except Exception as e:
        print(f"[失败] 删除 collection 请求异常：{e}")
        return False

    if resp.status_code in {200, 202}:
        print(f"[完成] 已删除 collection：{COLLECTION_NAME}")
        return True

    if resp.status_code == 404:
        print(f"[提示] collection 不存在：{COLLECTION_NAME}")
        return True

    print(f"[失败] 删除 collection 失败，状态码：{resp.status_code}")
    print(resp.text)
    return False


def save_list_docs_snapshot() -> Path | None:
    """
    尝试保存重建前 list_docs.py 输出。

    如果 Qdrant collection 已损坏，list_docs.py 可能失败。
    失败时不阻塞 rebuild。
    """
    timestamp = now_timestamp()
    snapshot_dir = BACKUP_DIR / "index_rebuild_snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    snapshot_path = snapshot_dir / f"{timestamp}_before_rebuild_list_docs.md"

    result = run_command(
        title="保存重建前 list_docs 快照",
        command=[sys.executable, "list_docs.py"],
        capture=True,
        timeout=600,
    )

    lines = []
    lines.append("---")
    lines.append(f"title: 重建索引前文档快照 {timestamp}")
    lines.append(f"created: {now_iso()}")
    lines.append("category: summary")
    lines.append("project: Personal_Project_Assistant")
    lines.append("doc_type: index_rebuild_snapshot")
    lines.append("tags: [索引重建, list_docs, 自动生成, M3.5]")
    lines.append("---")
    lines.append("")
    lines.append("# 重建索引前文档快照")
    lines.append("")
    lines.append(f"生成时间：{now_iso()}")
    lines.append(f"命令返回码：{result.returncode}")
    lines.append("")
    lines.append("```text")
    lines.append(result.stdout or "")

    if result.stderr:
        lines.append("")
        lines.append("[stderr]")
        lines.append(result.stderr)

    lines.append("```")
    lines.append("")

    snapshot_path.write_text("\n".join(lines), encoding="utf-8")

    if result.returncode != 0:
        print("[提示] list_docs.py 快照命令失败，但快照文件仍已保存错误输出。")

    print(f"快照已保存：{snapshot_path}")
    return snapshot_path


def backup_manifest() -> Path | None:
    """
    备份旧 index_manifest.json。
    """
    if not INDEX_MANIFEST_PATH.exists():
        print("[提示] index_manifest.json 不存在，无需备份。")
        return None

    timestamp = now_timestamp()
    manifest_backup_dir = BACKUP_DIR / "index_manifest_backups"
    manifest_backup_dir.mkdir(parents=True, exist_ok=True)

    backup_path = manifest_backup_dir / f"{timestamp}_index_manifest.json"
    shutil.copy2(INDEX_MANIFEST_PATH, backup_path)

    print(f"Manifest 已备份：{backup_path}")
    return backup_path


def reset_manifest() -> Path:
    """
    重置 index_manifest.json。

    重建 Qdrant collection 后，旧 point_ids 不再有效，
    所以必须重置 manifest，然后通过 update_index.py --force-all 重新写入。
    """
    path = manifest_utils.init_manifest(overwrite=True)
    print(f"Manifest 已重置：{path}")
    return path


def print_plan(skip_snapshot: bool, skip_check: bool) -> None:
    """
    打印 rebuild 将执行的操作计划。
    """
    print("个人项目秘书 + 数据知识库：全量重建索引")
    print("")
    print(f"知识库根目录：{KNOWLEDGE_ROOT}")
    print(f"Qdrant 地址：{QDRANT_URL}")
    print(f"Collection：{COLLECTION_NAME}")
    print(f"Manifest：{INDEX_MANIFEST_PATH}")
    print("")
    print("将执行以下操作：")

    step = 1

    if not skip_check:
        print(f"{step}. 运行 check_env.py")
        step += 1

    if not skip_snapshot:
        print(f"{step}. 尝试保存重建前 list_docs.py 快照")
        step += 1

    print(f"{step}. 备份旧 index_manifest.json")
    step += 1

    print(f"{step}. 删除 Qdrant collection：{COLLECTION_NAME}")
    step += 1

    print(f"{step}. 重置 index_manifest.json")
    step += 1

    print(f"{step}. 执行 update_index.py --force-all --skip-check")
    step += 1

    print(f"{step}. 执行 list_docs.py 验证结果")


def run_rebuild(
    skip_snapshot: bool = False,
    skip_check: bool = False,
) -> int:
    """
    真正执行全量重建。
    """
    if not skip_check:
        result = run_command(
            title="环境自检",
            command=[sys.executable, "check_env.py"],
            capture=False,
            timeout=600,
        )

        if result.returncode != 0:
            print("")
            print("[中止] 环境自检失败。")
            print("如 collection 已损坏导致 check_env.py 失败，可改用：")
            print("python rebuild_index.py --execute --skip-check")
            return result.returncode

    if not skip_snapshot:
        save_list_docs_snapshot()

    backup_manifest()

    ok = delete_collection_by_rest()

    if not ok:
        print("")
        print("[中止] 删除 Qdrant collection 失败。")
        print("如果 Qdrant 本地 shard 已损坏，请先重建 qdrant_storage。")
        return 1

    reset_manifest()

    result = run_command(
        title="执行全量重新入库",
        command=[
            sys.executable,
            "update_index.py",
            "--force-all",
            "--skip-check",
        ],
        capture=False,
        timeout=3600,
    )

    if result.returncode != 0:
        print("")
        print("[失败] 全量重新入库失败。")
        return result.returncode

    result = run_command(
        title="验证已入库文档",
        command=[sys.executable, "list_docs.py"],
        capture=False,
        timeout=900,
    )

    if result.returncode != 0:
        print("")
        print("[失败] list_docs.py 验证失败。")
        return result.returncode

    print("")
    print("=" * 80)
    print("全量重建索引完成")
    print("=" * 80)
    print("")
    print("建议下一步执行：")
    print("python status.py")
    print("python health_check_full.py")
    print('python ask.py "当前项目进行到哪里了？"')

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="个人项目秘书 + 数据知识库：全量重建 Qdrant 索引"
    )

    parser.add_argument(
        "--execute",
        action="store_true",
        help="真正执行重建。默认只预览，不删除 collection。",
    )

    parser.add_argument(
        "--skip-snapshot",
        action="store_true",
        help="跳过重建前 list_docs.py 快照。",
    )

    parser.add_argument(
        "--skip-check",
        action="store_true",
        help="跳过 check_env.py。适合 collection 已损坏时使用。",
    )

    args = parser.parse_args()

    print_plan(
        skip_snapshot=args.skip_snapshot,
        skip_check=args.skip_check,
    )

    if not args.execute:
        print("")
        print("当前为预览模式，未删除 collection，未重置 manifest，未重建索引。")
        print("")
        print("确认无误后执行：")
        print("python rebuild_index.py --execute")
        print("")
        print("如果 collection 已损坏导致 check_env.py 或 list_docs.py 报错，可执行：")
        print("python rebuild_index.py --execute --skip-check --skip-snapshot")
        return

    code = run_rebuild(
        skip_snapshot=args.skip_snapshot,
        skip_check=args.skip_check,
    )

    raise SystemExit(code)


if __name__ == "__main__":
    main()
