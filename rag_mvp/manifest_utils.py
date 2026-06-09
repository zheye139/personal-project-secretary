import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

import config


# ============================================================
# 基础配置
# ============================================================

KNOWLEDGE_ROOT = config.KNOWLEDGE_ROOT

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


# ============================================================
# Manifest 版本
# ============================================================

MANIFEST_VERSION = 1


# ============================================================
# 默认跳过目录
# ============================================================

SKIP_DIR_NAMES = {
    ".venv",
    "__pycache__",
    "backups",
    "qdrant_storage",
    "qdrant_local",
    "_imported",
    "01_Projects_Archived",
    ".git",
}


def now_iso() -> str:
    """
    返回当前 ISO 时间字符串。
    """
    return datetime.now().isoformat(timespec="seconds")


def normalize_rel_path(path: Path) -> str:
    """
    将文件路径转换为相对于 KNOWLEDGE_ROOT 的统一格式。

    统一使用 /，避免 Windows 反斜杠影响 GitHub 和 JSON 可读性。
    """
    rel_path = path.resolve().relative_to(KNOWLEDGE_ROOT.resolve())
    return rel_path.as_posix()


def resolve_source_path(source: str) -> Path:
    """
    将 manifest 中保存的 source 字段转换回实际文件路径。
    """
    return KNOWLEDGE_ROOT / Path(source)


def should_skip(path: Path) -> bool:
    """
    判断文件或目录是否需要跳过。

    原则：
    1. 不扫描虚拟环境。
    2. 不扫描 Qdrant 数据目录。
    3. 不扫描备份目录。
    4. 不扫描归档项目目录。
    5. 不扫描 Git 目录。
    """
    parts = set(path.parts)
    return bool(parts.intersection(SKIP_DIR_NAMES))


def is_allowed_system_doc(path: Path) -> bool:
    """
    允许 99_System/docs 下的 Markdown 文档进入知识库索引。

    但 99_System/rag_mvp、99_System/backups、99_System/qdrant_storage 等不进入索引。
    """
    try:
        rel_parts = path.relative_to(KNOWLEDGE_ROOT).parts
    except ValueError:
        return False

    return (
        len(rel_parts) >= 2
        and rel_parts[0] == "99_System"
        and rel_parts[1] == "docs"
    )


def should_collect_markdown(path: Path) -> bool:
    """
    判断一个 Markdown 文件是否应该被纳入知识库扫描。

    这个规则需要和 ingest.py 的收集规则保持一致：
    1. 普通知识库目录下的 Markdown 可以扫描。
    2. 99_System/docs 下的 Markdown 可以扫描。
    3. 99_System 其他目录跳过。
    4. 跳过 backups、qdrant_storage、.venv 等目录。
    """
    if path.suffix.lower() != ".md":
        return False

    if should_skip(path):
        return False

    try:
        rel_parts = path.relative_to(KNOWLEDGE_ROOT).parts
    except ValueError:
        return False

    if is_allowed_system_doc(path):
        return True

    if rel_parts and rel_parts[0] == "99_System":
        return False

    return True


def file_sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """
    计算文件 sha256。

    用途：
    1. 判断文件内容是否变化。
    2. 避免只依赖 mtime 导致误判。
    """
    digest = hashlib.sha256()

    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)

            if not chunk:
                break

            digest.update(chunk)

    return digest.hexdigest()


def build_file_fingerprint(path: Path) -> dict:
    """
    构建文件基础指纹。

    只记录文件状态，不记录 Qdrant point 信息。
    """
    stat = path.stat()

    return {
        "source": normalize_rel_path(path),
        "mtime_ns": stat.st_mtime_ns,
        "size": stat.st_size,
        "sha256": file_sha256(path),
    }


def build_manifest_record(
    path: Path,
    chunk_count: int = 0,
    point_ids: list[str] | None = None,
) -> dict:
    """
    构建一个完整 manifest 文件记录。

    M3.1 阶段 chunk_count 和 point_ids 可以先为空。
    M3.2 增量入库时会真正写入这些字段。
    """
    fingerprint = build_file_fingerprint(path)

    record = {
        "source": fingerprint["source"],
        "mtime_ns": fingerprint["mtime_ns"],
        "size": fingerprint["size"],
        "sha256": fingerprint["sha256"],
        "chunk_count": chunk_count,
        "point_ids": point_ids or [],
        "updated_at": now_iso(),
    }

    return record


def is_same_fingerprint(record: dict, fingerprint: dict) -> bool:
    """
    判断 manifest 中的记录是否和当前文件指纹一致。
    """
    return (
        record.get("mtime_ns") == fingerprint.get("mtime_ns")
        and record.get("size") == fingerprint.get("size")
        and record.get("sha256") == fingerprint.get("sha256")
    )


def empty_manifest() -> dict:
    """
    创建空 manifest 结构。
    """
    return {
        "version": MANIFEST_VERSION,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "knowledge_root": str(KNOWLEDGE_ROOT),
        "files": {},
    }


def normalize_manifest(raw: dict | None) -> dict:
    """
    修正 manifest 结构，避免字段缺失。
    """
    if not isinstance(raw, dict):
        return empty_manifest()

    manifest = dict(raw)

    manifest.setdefault("version", MANIFEST_VERSION)
    manifest.setdefault("created_at", now_iso())
    manifest.setdefault("updated_at", now_iso())
    manifest.setdefault("knowledge_root", str(KNOWLEDGE_ROOT))
    manifest.setdefault("files", {})

    if not isinstance(manifest["files"], dict):
        manifest["files"] = {}

    return manifest


def load_manifest(path: Path | None = None) -> dict:
    """
    读取 index_manifest.json。

    如果文件不存在，返回空 manifest。
    """
    manifest_path = path or INDEX_MANIFEST_PATH

    if not manifest_path.exists():
        return empty_manifest()

    try:
        text = manifest_path.read_text(encoding="utf-8")
        raw = json.loads(text)
        return normalize_manifest(raw)
    except json.JSONDecodeError:
        print(f"[警告] manifest JSON 格式异常：{manifest_path}")
        print("将返回空 manifest。")
        return empty_manifest()


def save_manifest(manifest: dict, path: Path | None = None) -> Path:
    """
    保存 index_manifest.json。
    """
    manifest_path = path or INDEX_MANIFEST_PATH
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    manifest = normalize_manifest(manifest)
    manifest["updated_at"] = now_iso()

    text = json.dumps(
        manifest,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )

    manifest_path.write_text(text + "\n", encoding="utf-8")
    return manifest_path


def init_manifest(overwrite: bool = False) -> Path:
    """
    初始化 index_manifest.json。

    默认不覆盖已有文件。
    """
    if INDEX_MANIFEST_PATH.exists() and not overwrite:
        return INDEX_MANIFEST_PATH

    manifest = empty_manifest()
    return save_manifest(manifest)


def get_record(manifest: dict, source: str) -> dict | None:
    """
    从 manifest 中读取指定 source 的记录。
    """
    files = manifest.get("files", {})
    return files.get(source)


def set_record(manifest: dict, source: str, record: dict) -> dict:
    """
    写入或更新指定 source 的记录。
    """
    manifest = normalize_manifest(manifest)
    manifest["files"][source] = record
    manifest["updated_at"] = now_iso()
    return manifest


def remove_record(manifest: dict, source: str) -> dict:
    """
    从 manifest 中移除指定 source 的记录。
    """
    manifest = normalize_manifest(manifest)

    if source in manifest["files"]:
        del manifest["files"][source]

    manifest["updated_at"] = now_iso()
    return manifest


def record_point_ids(manifest: dict, source: str, point_ids: list[str]) -> dict:
    """
    更新某个文件对应的 Qdrant point_ids。

    M3.2 中删除旧 points 时会用到。
    """
    manifest = normalize_manifest(manifest)
    record = manifest["files"].get(source)

    if not record:
        return manifest

    record["point_ids"] = point_ids
    record["chunk_count"] = len(point_ids)
    record["updated_at"] = now_iso()

    manifest["files"][source] = record
    manifest["updated_at"] = now_iso()

    return manifest


def collect_markdown_files() -> list[Path]:
    """
    扫描知识库中应该参与索引的 Markdown 文件。
    """
    files = []

    for path in KNOWLEDGE_ROOT.rglob("*.md"):
        if should_collect_markdown(path):
            files.append(path)

    return sorted(files)


def scan_files() -> dict[str, dict]:
    """
    扫描当前知识库 Markdown 文件，返回 source -> fingerprint。
    """
    result = {}

    for path in collect_markdown_files():
        fingerprint = build_file_fingerprint(path)
        result[fingerprint["source"]] = fingerprint

    return result


def analyze_changes(manifest: dict, scanned_files: dict[str, dict]) -> dict:
    """
    分析当前文件系统与 manifest 的差异。

    返回：
    - added: 新增文件
    - changed: 修改文件
    - deleted: 删除文件
    - unchanged: 未变化文件
    """
    manifest = normalize_manifest(manifest)
    manifest_files = manifest.get("files", {})

    added = []
    changed = []
    deleted = []
    unchanged = []

    scanned_sources = set(scanned_files.keys())
    manifest_sources = set(manifest_files.keys())

    for source in sorted(scanned_sources - manifest_sources):
        added.append(source)

    for source in sorted(manifest_sources - scanned_sources):
        deleted.append(source)

    for source in sorted(scanned_sources & manifest_sources):
        record = manifest_files[source]
        fingerprint = scanned_files[source]

        if is_same_fingerprint(record, fingerprint):
            unchanged.append(source)
        else:
            changed.append(source)

    return {
        "added": added,
        "changed": changed,
        "deleted": deleted,
        "unchanged": unchanged,
    }


def update_manifest_from_scan(manifest: dict, scanned_files: dict[str, dict]) -> dict:
    """
    根据当前扫描结果更新 manifest。

    注意：
    M3.1 阶段这个函数只写入基础文件记录。
    后续 M3.2 中，入库成功后会补充 point_ids 和 chunk_count。
    """
    manifest = normalize_manifest(manifest)

    new_files = {}

    for source, fingerprint in scanned_files.items():
        old_record = manifest["files"].get(source, {})

        record = {
            "source": source,
            "mtime_ns": fingerprint["mtime_ns"],
            "size": fingerprint["size"],
            "sha256": fingerprint["sha256"],
            "chunk_count": old_record.get("chunk_count", 0),
            "point_ids": old_record.get("point_ids", []),
            "updated_at": now_iso(),
        }

        new_files[source] = record

    manifest["files"] = new_files
    manifest["updated_at"] = now_iso()

    return manifest


def print_change_summary(changes: dict) -> None:
    """
    打印变化分析摘要。
    """
    print("")
    print("=== Manifest 变化分析 ===")
    print(f"新增文件 added：{len(changes['added'])}")
    print(f"修改文件 changed：{len(changes['changed'])}")
    print(f"删除文件 deleted：{len(changes['deleted'])}")
    print(f"未变化文件 unchanged：{len(changes['unchanged'])}")


def print_change_details(changes: dict, show_unchanged: bool = False) -> None:
    """
    打印变化详情。
    """
    sections = [
        ("新增文件", "added"),
        ("修改文件", "changed"),
        ("删除文件", "deleted"),
    ]

    if show_unchanged:
        sections.append(("未变化文件", "unchanged"))

    for title, key in sections:
        items = changes.get(key, [])

        print("")
        print(f"## {title}：{len(items)}")

        if not items:
            continue

        for source in items:
            print(f"- {source}")


def print_manifest_info(manifest: dict) -> None:
    """
    打印 manifest 基本信息。
    """
    manifest = normalize_manifest(manifest)

    print("")
    print("=== Manifest 信息 ===")
    print(f"路径：{INDEX_MANIFEST_PATH}")
    print(f"version：{manifest.get('version')}")
    print(f"created_at：{manifest.get('created_at')}")
    print(f"updated_at：{manifest.get('updated_at')}")
    print(f"knowledge_root：{manifest.get('knowledge_root')}")
    print(f"记录文件数量：{len(manifest.get('files', {}))}")


def main():
    parser = argparse.ArgumentParser(
        description="Personal Project Secretary: index_manifest.json 工具"
    )

    parser.add_argument(
        "--init",
        action="store_true",
        help="初始化 index_manifest.json。默认不覆盖已有文件。",
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="与 --init 一起使用，覆盖已有 manifest。",
    )

    parser.add_argument(
        "--scan",
        action="store_true",
        help="扫描 Markdown 文件并分析与 manifest 的差异。",
    )

    parser.add_argument(
        "--write-scan",
        action="store_true",
        help="扫描 Markdown 文件，并将当前扫描结果写入 manifest。",
    )

    parser.add_argument(
        "--show-unchanged",
        action="store_true",
        help="显示未变化文件列表。",
    )

    args = parser.parse_args()

    print("个人项目秘书 + 数据知识库：Manifest 工具")
    print(f"知识库根目录：{KNOWLEDGE_ROOT}")
    print(f"Manifest 路径：{INDEX_MANIFEST_PATH}")

    if args.init:
        path = init_manifest(overwrite=args.overwrite)
        print("")
        print("Manifest 已初始化：")
        print(path)

    manifest = load_manifest()
    print_manifest_info(manifest)

    if args.scan or args.write_scan:
        scanned_files = scan_files()
        changes = analyze_changes(manifest, scanned_files)

        print("")
        print(f"当前扫描到 Markdown 文件数量：{len(scanned_files)}")

        print_change_summary(changes)
        print_change_details(
            changes=changes,
            show_unchanged=args.show_unchanged,
        )

        if args.write_scan:
            updated_manifest = update_manifest_from_scan(
                manifest=manifest,
                scanned_files=scanned_files,
            )
            path = save_manifest(updated_manifest)

            print("")
            print("Manifest 已根据当前扫描结果更新：")
            print(path)


if __name__ == "__main__":
    main()
