import argparse
import os
import re
import sys
import uuid
from datetime import datetime
from pathlib import Path

import requests
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    FilterSelector,
    MatchValue,
    PointStruct,
    VectorParams,
)

import config
import manifest_utils


# ============================================================
# 基础配置
# ============================================================

KNOWLEDGE_ROOT = config.KNOWLEDGE_ROOT

OLLAMA_URL = config.OLLAMA_URL
EMBED_MODEL = config.EMBED_MODEL

QDRANT_URL = config.QDRANT_URL
COLLECTION_NAME = config.COLLECTION_NAME

CHUNK_MAX_CHARS = getattr(config, "CHUNK_MAX_CHARS", 800)


# ============================================================
# Windows / PowerShell 中文输出处理
# ============================================================

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


# ============================================================
# 避免访问本机服务时走系统代理
# ============================================================

for key in [
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
]:
    os.environ.pop(key, None)

os.environ["NO_PROXY"] = "localhost,127.0.0.1,::1"
os.environ["no_proxy"] = "localhost,127.0.0.1,::1"


def now_iso() -> str:
    """
    返回当前 ISO 时间字符串。
    """
    return datetime.now().isoformat(timespec="seconds")


def read_text(path: Path) -> str:
    """
    读取 Markdown 文件。
    """
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8-sig")


def get_qdrant_client() -> QdrantClient:
    """
    创建 Qdrant 客户端。
    """
    return QdrantClient(
        url=QDRANT_URL,
        check_compatibility=False,
        timeout=120,
    )


def collection_exists(client: QdrantClient) -> bool:
    """
    检查 Qdrant collection 是否存在。
    """
    try:
        return client.collection_exists(COLLECTION_NAME)
    except Exception:
        collections = client.get_collections().collections
        names = [item.name for item in collections]
        return COLLECTION_NAME in names


def parse_frontmatter(text: str) -> tuple[dict, str, bool]:
    """
    解析 Markdown Frontmatter。

    返回：
    metadata, body, has_frontmatter
    """
    raw_text = text.lstrip()

    if not raw_text.startswith("---"):
        return {}, text.strip(), False

    parts = raw_text.split("---", 2)

    if len(parts) < 3:
        return {}, text.strip(), False

    raw_meta = parts[1].strip()
    body = parts[2].strip()

    metadata = {}

    for line in raw_meta.splitlines():
        line = line.strip()

        if not line or ":" not in line:
            continue

        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()

        metadata[key] = value.strip('"').strip("'")

    return metadata, body, True


def parse_tags(raw_value) -> list[str]:
    """
    将 tags 字段统一转换为 list[str]。
    """
    if not raw_value:
        return []

    value = str(raw_value).strip()

    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1]
        return [
            item.strip().strip('"').strip("'")
            for item in inner.split(",")
            if item.strip()
        ]

    return [
        item.strip().strip('"').strip("'")
        for item in value.split(",")
        if item.strip()
    ]


def infer_category(path: Path, metadata: dict) -> str:
    """
    推断 category。
    """
    if metadata.get("category"):
        return metadata["category"].strip()

    rel_parts = path.relative_to(KNOWLEDGE_ROOT).parts

    mapping = {
        "01_Projects": "project",
        "02_Knowledge": "knowledge",
        "03_Decisions": "decision",
        "04_Problems": "problem",
        "05_Summaries": "summary",
        "06_Attachments": "attachment",
        "99_System": "system",
    }

    if not rel_parts:
        return "unknown"

    return mapping.get(rel_parts[0], "unknown")


def infer_project(path: Path, metadata: dict, category: str) -> str:
    """
    推断 project。
    """
    if metadata.get("project"):
        return metadata["project"].strip()

    rel_parts = path.relative_to(KNOWLEDGE_ROOT).parts

    if len(rel_parts) >= 2 and rel_parts[0] == "01_Projects":
        return rel_parts[1]

    if len(rel_parts) >= 2 and rel_parts[0] in {
        "02_Knowledge",
        "03_Decisions",
        "04_Problems",
        "05_Summaries",
        "06_Attachments",
    }:
        return rel_parts[1]

    if category == "system":
        return "Personal_Project_Assistant"

    return "unknown"


def infer_doc_type(path: Path, metadata: dict) -> str:
    """
    推断 doc_type。
    """
    if metadata.get("doc_type"):
        return metadata["doc_type"].strip()

    if metadata.get("type"):
        return metadata["type"].strip()

    stem = path.stem.lower()

    mapping = {
        "readme": "readme",
        "project_overview": "project_overview",
        "progress_log": "progress_log",
        "issues": "issues",
        "next_steps": "next_steps",
        "decisions": "decisions",
        "technical_notes": "technical_notes",
        "commands": "command_reference",
        "environment_setup": "environment_setup",
        "restore_guide": "restore_guide",
        "rag_mvp_readme": "rag_mvp_readme",
    }

    if stem in mapping:
        return mapping[stem]

    if stem.endswith("_qa"):
        return "qa_log"

    if "project_report" in stem:
        return "project_report"

    if "daily_report" in stem:
        return "daily_report"

    if "weekly_report" in stem:
        return "weekly_report"

    if "next_actions" in stem or "next_action" in stem:
        return "next_action_report"

    if "project_brief" in stem:
        return "project_brief"

    if "multi_project_status" in stem:
        return "multi_project_status"

    if "priority_advice" in stem:
        return "priority_advice"

    if "review_report" in stem:
        return "review_report"

    if "secretary_report" in stem:
        return "secretary_report"

    if "closeout_report" in stem or "milestone" in stem:
        return "milestone_report"

    return "note"


def build_payload_metadata(path: Path, text: str) -> tuple[dict, str]:
    """
    解析并补齐 payload metadata。
    """
    metadata, body, _ = parse_frontmatter(text)

    category = infer_category(path, metadata)
    project = infer_project(path, metadata, category)
    doc_type = infer_doc_type(path, metadata)

    title = metadata.get("title", "").strip() or path.stem
    tags = parse_tags(metadata.get("tags", ""))

    updated_at = datetime.fromtimestamp(
        path.stat().st_mtime
    ).isoformat(timespec="seconds")

    source = manifest_utils.normalize_rel_path(path)

    payload_base = {
        "category": category,
        "project": project,
        "doc_type": doc_type,
        "title": title,
        "tags": tags,
        "file_name": path.name,
        "source": source,
        "updated_at": updated_at,
    }

    return payload_base, body


def split_text(text: str, max_chars: int = CHUNK_MAX_CHARS) -> list[str]:
    """
    将 Markdown 正文切分为多个片段。

    简单规则：
    1. 按空行分段。
    2. 尽量不截断段落。
    3. 单段过长时强制切分。
    """
    text = text.strip()

    if not text:
        return []

    paragraphs = re.split(r"\n\s*\n", text)
    chunks = []
    current = ""

    for paragraph in paragraphs:
        paragraph = paragraph.strip()

        if not paragraph:
            continue

        if len(paragraph) > max_chars:
            if current.strip():
                chunks.append(current.strip())
                current = ""

            for i in range(0, len(paragraph), max_chars):
                part = paragraph[i : i + max_chars].strip()
                if part:
                    chunks.append(part)

            continue

        candidate = paragraph if not current else current + "\n\n" + paragraph

        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current.strip():
                chunks.append(current.strip())
            current = paragraph

    if current.strip():
        chunks.append(current.strip())

    return chunks


def embed_text(text: str) -> list[float]:
    """
    调用 Ollama 生成向量。

    优先使用 /api/embed。
    如果当前 Ollama 版本不支持，则回退到 /api/embeddings。
    """
    text = text.strip()

    try:
        resp = requests.post(
            f"{OLLAMA_URL}/api/embed",
            json={
                "model": EMBED_MODEL,
                "input": text,
            },
            timeout=120,
        )

        if resp.status_code == 200:
            data = resp.json()
            embeddings = data.get("embeddings", [])

            if embeddings:
                return embeddings[0]
    except Exception:
        pass

    resp = requests.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={
            "model": EMBED_MODEL,
            "prompt": text,
        },
        timeout=120,
    )
    resp.raise_for_status()

    data = resp.json()
    return data["embedding"]


def ensure_collection(client: QdrantClient, vector_size: int) -> None:
    """
    确保 Qdrant collection 存在。
    """
    if collection_exists(client):
        return

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=vector_size,
            distance=Distance.COSINE,
        ),
    )

    print(f"[创建集合] {COLLECTION_NAME}，向量维度：{vector_size}")


def delete_by_point_ids(client: QdrantClient, point_ids: list[str]) -> None:
    """
    根据 point_ids 删除旧 points。
    """
    if not point_ids:
        return

    try:
        client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=point_ids,
            wait=True,
        )
        print(f"  已按 point_ids 删除旧 points：{len(point_ids)}")
    except Exception as e:
        print(f"  [警告] 按 point_ids 删除失败，将继续尝试按 source 删除：{e}")


def delete_by_source_value(client: QdrantClient, source_value: str) -> None:
    """
    根据 payload.source 删除旧 points。
    """
    if not source_value:
        return

    selector = FilterSelector(
        filter=Filter(
            must=[
                FieldCondition(
                    key="source",
                    match=MatchValue(value=source_value),
                )
            ]
        )
    )

    try:
        client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=selector,
            wait=True,
        )
        print(f"  已按 source 删除旧 points：{source_value}")
    except Exception as e:
        print(f"  [警告] 按 source 删除失败：{source_value} | {e}")


def delete_old_points_for_source(
    client: QdrantClient,
    manifest: dict,
    source: str,
) -> None:
    """
    删除某个 Markdown 文件对应的旧 Qdrant points。

    为兼容历史版本，执行三种删除：
    1. manifest 中记录的 point_ids
    2. payload.source 使用 / 的路径
    3. payload.source 使用 \\ 的路径
    """
    if not collection_exists(client):
        return

    record = manifest.get("files", {}).get(source, {})
    point_ids = record.get("point_ids", [])

    delete_by_point_ids(client, point_ids)

    delete_by_source_value(client, source)

    backslash_source = source.replace("/", "\\")
    if backslash_source != source:
        delete_by_source_value(client, backslash_source)


def make_point_id(source: str, sha256: str, chunk_index: int) -> str:
    """
    生成稳定的 point id。

    同一个 source + sha256 + chunk_index 会生成同一个 UUID。
    """
    raw = f"{source}:{sha256}:{chunk_index}"
    return str(uuid.uuid5(uuid.NAMESPACE_URL, raw))


def resolve_user_file_path(raw_file: str) -> tuple[Path, str]:
    """
    将用户输入的 --file 参数转换为：
    1. 实际 Path
    2. manifest / Qdrant payload 中使用的 source

    支持：
    1. 绝对路径：
       D:\\Personal_Knowledge_Base\\01_Projects\\Demo\\progress_log.md

    2. 相对 KNOWLEDGE_ROOT 的路径：
       01_Projects/Demo/progress_log.md

    3. 当前 rag_mvp 目录下的相对路径不推荐，但会尝试解析。
    """
    raw_file = raw_file.strip().strip('"').strip("'")

    input_path = Path(raw_file)

    # 情况 1：用户传入绝对路径
    if input_path.is_absolute():
        path = input_path
    else:
        # 情况 2：优先按 KNOWLEDGE_ROOT 相对路径解析
        kb_path = KNOWLEDGE_ROOT / input_path

        if kb_path.exists():
            path = kb_path
        else:
            # 情况 3：文件可能已经被删除，仍按 KNOWLEDGE_ROOT 相对路径生成 source
            path = kb_path

    try:
        source = path.resolve().relative_to(KNOWLEDGE_ROOT.resolve()).as_posix()
    except ValueError:
        raise ValueError(
            "指定文件不在 KNOWLEDGE_ROOT 目录下，不能作为知识库文件更新："
            f"{path}"
        )

    return path, source


def is_valid_markdown_file_for_index(path: Path) -> bool:
    """
    判断文件是否是允许入库的 Markdown 文件。
    """
    if path.suffix.lower() != ".md":
        return False

    return manifest_utils.should_collect_markdown(path)


def index_markdown_file(client: QdrantClient, path: Path) -> dict:
    """
    将单个 Markdown 文件写入 Qdrant，并返回 manifest record。
    """
    text = read_text(path)
    source = manifest_utils.normalize_rel_path(path)

    if not text.strip():
        print(f"  [跳过空文件] {source}")
        return manifest_utils.build_manifest_record(
            path=path,
            chunk_count=0,
            point_ids=[],
        )

    payload_base, body = build_payload_metadata(path, text)

    content_for_index = body.strip() if body.strip() else text.strip()
    chunks = split_text(content_for_index)

    if not chunks:
        print(f"  [跳过无有效内容文件] {source}")
        return manifest_utils.build_manifest_record(
            path=path,
            chunk_count=0,
            point_ids=[],
        )

    fingerprint = manifest_utils.build_file_fingerprint(path)
    point_ids = []
    points = []

    first_vector = None

    for chunk_index, chunk_text in enumerate(chunks):
        vector = embed_text(chunk_text)

        if first_vector is None:
            first_vector = vector
            ensure_collection(client, vector_size=len(first_vector))

        point_id = make_point_id(
            source=source,
            sha256=fingerprint["sha256"],
            chunk_index=chunk_index,
        )

        payload = dict(payload_base)
        payload["chunk_index"] = chunk_index
        payload["text"] = chunk_text

        points.append(
            PointStruct(
                id=point_id,
                vector=vector,
                payload=payload,
            )
        )
        point_ids.append(point_id)

    if points:
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points,
            wait=True,
        )

    print(f"  已入库：{source} | chunks={len(points)}")

    return manifest_utils.build_manifest_record(
        path=path,
        chunk_count=len(point_ids),
        point_ids=point_ids,
    )


def apply_force_all(changes: dict, scanned_files: dict, manifest: dict) -> dict:
    """
    将所有当前存在的 Markdown 文件强制视为需要重新入库。

    用途：
    1. M3.2 刚接入后，可以执行一次 --force-all。
    2. 让 manifest 中补齐 point_ids。
    """
    manifest_files = manifest.get("files", {})
    scanned_sources = sorted(scanned_files.keys())

    added = []
    changed = []

    for source in scanned_sources:
        if source in manifest_files:
            changed.append(source)
        else:
            added.append(source)

    return {
        "added": added,
        "changed": changed,
        "deleted": changes.get("deleted", []),
        "unchanged": [],
    }


def print_summary(changes: dict) -> None:
    """
    打印变化摘要。
    """
    print("")
    print("=== 增量索引变化摘要 ===")
    print(f"新增文件 added：{len(changes['added'])}")
    print(f"修改文件 changed：{len(changes['changed'])}")
    print(f"删除文件 deleted：{len(changes['deleted'])}")
    print(f"跳过文件 skipped：{len(changes['unchanged'])}")


def print_items(title: str, items: list[str]) -> None:
    """
    打印文件列表。
    """
    print("")
    print(f"## {title}：{len(items)}")

    for item in items:
        print(f"- {item}")


def infer_project_from_existing_file(path: Path) -> str:
    """
    从仍然存在的 Markdown 文件中推断 project。
    """
    try:
        text = read_text(path)
        metadata, _, _ = parse_frontmatter(text)
        category = infer_category(path, metadata)
        return infer_project(path, metadata, category)
    except Exception:
        return ""


def get_manifest_record_project(record: dict) -> str:
    """
    从 manifest record 中读取 project。
    """
    if not record:
        return ""

    return str(record.get("project", "")).strip()


def source_belongs_to_project(
    source: str,
    project: str,
    scanned_files: dict,
    manifest: dict,
) -> bool:
    """
    判断某个 source 是否属于指定 project。

    判断顺序：
    1. 如果当前文件还存在，从文件 Frontmatter / 路径推断 project。
    2. 如果文件已删除，从 manifest 旧记录读取 project。
    3. 如果都没有，则用路径兜底判断 01_Projects/<project>/...
    """
    project = project.strip()

    if not project:
        return False

    if source in scanned_files:
        path = manifest_utils.resolve_source_path(source)
        current_project = infer_project_from_existing_file(path)

        if current_project == project:
            return True

    record = manifest.get("files", {}).get(source, {})
    record_project = get_manifest_record_project(record)

    if record_project == project:
        return True

    # 路径兜底：项目主目录下的文件
    prefix = f"01_Projects/{project}/"

    if source.startswith(prefix):
        return True

    return False


def filter_scanned_files_by_project(
    scanned_files: dict[str, dict],
    project: str,
) -> dict[str, dict]:
    """
    只保留属于指定项目的当前 Markdown 文件。
    """
    result = {}

    for source, fingerprint in scanned_files.items():
        path = manifest_utils.resolve_source_path(source)
        current_project = infer_project_from_existing_file(path)

        if current_project == project:
            result[source] = fingerprint
            continue

        if source.startswith(f"01_Projects/{project}/"):
            result[source] = fingerprint

    return result


def filter_manifest_files_by_project(
    manifest: dict,
    project: str,
) -> dict[str, dict]:
    """
    从 manifest 中筛选属于指定项目的旧记录。

    这一步对于“项目级删除同步”很重要：
    文件删除后无法读取 Frontmatter，只能依赖 manifest 中保存的 project。
    """
    result = {}

    for source, record in manifest.get("files", {}).items():
        record_project = get_manifest_record_project(record)

        if record_project == project:
            result[source] = record
            continue

        if source.startswith(f"01_Projects/{project}/"):
            result[source] = record

    return result


def build_project_limited_manifest(manifest: dict, project: str) -> dict:
    """
    构建只包含指定项目记录的临时 manifest。

    注意：
    这里只用于变化分析，不直接覆盖原始 manifest。
    """
    limited = manifest_utils.normalize_manifest(manifest)
    limited["files"] = filter_manifest_files_by_project(
        manifest=manifest,
        project=project,
    )

    return limited


def run_single_file_update(
    raw_file: str,
    dry_run: bool = False,
    force: bool = False,
) -> int:
    """
    执行单文件更新。

    处理逻辑：
    1. 文件存在，且 manifest 中没有记录：
       -> 作为新增文件入库。

    2. 文件存在，且内容发生变化：
       -> 删除旧 points 后重新入库。

    3. 文件存在，但内容没有变化：
       -> 默认跳过。
       -> 如果 force=True，则强制删除旧 points 后重新入库。

    4. 文件不存在，但 manifest 中有记录：
       -> 视为删除文件，从 Qdrant 删除旧 points，并移除 manifest 记录。

    5. 文件不存在，且 manifest 中没有记录：
       -> 无操作。
    """
    manifest = manifest_utils.load_manifest()

    try:
        path, source = resolve_user_file_path(raw_file)
    except Exception as e:
        print(f"[失败] 文件路径解析失败：{e}")
        return 1

    print("个人项目秘书 + 数据知识库：单文件索引更新")
    print(f"输入文件：{raw_file}")
    print(f"解析路径：{path}")
    print(f"source：{source}")
    print(f"dry_run：{dry_run}")
    print(f"force：{force}")

    record = manifest.get("files", {}).get(source)

    client = None

    # ------------------------------------------------------------
    # 情况 A：文件不存在
    # ------------------------------------------------------------
    if not path.exists():
        print("")
        print("[检测结果] 文件不存在。")

        if not record:
            print("Manifest 中也没有该文件记录，无需处理。")
            return 0

        print("Manifest 中存在该文件记录，将作为 deleted 文件处理。")

        if dry_run:
            print("dry-run 模式：不会删除 Qdrant points，也不会修改 manifest。")
            return 0

        client = get_qdrant_client()

        try:
            delete_old_points_for_source(
                client=client,
                manifest=manifest,
                source=source,
            )
            manifest = manifest_utils.remove_record(manifest, source)
            manifest_utils.save_manifest(manifest)
        except Exception as e:
            print(f"[失败] 删除文件同步清理失败：{e}")
            return 1
        finally:
            try:
                client.close()
            except Exception:
                pass

        print("单文件删除同步完成。")
        return 0

    # ------------------------------------------------------------
    # 情况 B：文件存在，但不是可入库 Markdown
    # ------------------------------------------------------------
    if not is_valid_markdown_file_for_index(path):
        print("")
        print("[跳过] 该文件不是允许入库的 Markdown 文件。")
        print("可能原因：")
        print("1. 文件不是 .md。")
        print("2. 文件位于 99_System 非 docs 目录。")
        print("3. 文件位于 backups、qdrant_storage、.venv、归档目录等跳过目录。")
        return 0

    # ------------------------------------------------------------
    # 情况 C：文件存在，判断新增 / 修改 / 未变化
    # ------------------------------------------------------------
    fingerprint = manifest_utils.build_file_fingerprint(path)

    if not record:
        action = "added"
    elif force:
        action = "changed-force"
    elif manifest_utils.is_same_fingerprint(record, fingerprint):
        action = "unchanged"
    else:
        action = "changed"

    print("")
    print(f"[检测结果] {action}")

    if action == "unchanged":
        print("文件未变化，跳过入库。")
        print("如果需要强制重建该文件，请使用：")
        print(f'python update_index.py --file "{raw_file}" --force-file')
        return 0

    if dry_run:
        print("dry-run 模式：不会修改 Qdrant，也不会写入 manifest。")
        return 0

    client = get_qdrant_client()

    try:
        if action in {"changed", "changed-force"}:
            print("")
            print("[清理旧 points]")
            delete_old_points_for_source(
                client=client,
                manifest=manifest,
                source=source,
            )

        print("")
        print("[写入新 points]")
        new_record = index_markdown_file(client, path)
        manifest = manifest_utils.set_record(manifest, source, new_record)
        manifest_utils.save_manifest(manifest)

    except Exception as e:
        print(f"[失败] 单文件入库失败：{e}")
        return 1

    finally:
        try:
            client.close()
        except Exception:
            pass

    print("")
    print("单文件索引更新完成。")
    print("Manifest 已更新：")
    print(manifest_utils.INDEX_MANIFEST_PATH)

    return 0


def run_incremental_index(
    dry_run: bool = False,
    force_all: bool = False,
) -> int:
    """
    执行增量索引。

    返回：
    0 = 成功
    1 = 失败
    """
    manifest = manifest_utils.load_manifest()
    scanned_files = manifest_utils.scan_files()
    changes = manifest_utils.analyze_changes(manifest, scanned_files)

    if force_all:
        changes = apply_force_all(
            changes=changes,
            scanned_files=scanned_files,
            manifest=manifest,
        )

    print("个人项目秘书 + 数据知识库：增量索引")
    print(f"知识库根目录：{KNOWLEDGE_ROOT}")
    print(f"集合名称：{COLLECTION_NAME}")
    print(f"扫描 Markdown 文件数量：{len(scanned_files)}")
    print(f"dry_run：{dry_run}")
    print(f"force_all：{force_all}")

    print_summary(changes)

    print_items("新增文件", changes["added"])
    print_items("修改文件", changes["changed"])
    print_items("删除文件", changes["deleted"])

    if dry_run:
        print("")
        print("当前为 dry-run 模式，未修改 Qdrant，也未写入 manifest。")
        return 0

    client = get_qdrant_client()

    try:
        # 删除已经不存在的文件对应的旧 points
        for source in changes["deleted"]:
            print("")
            print(f"[删除文件同步清理] {source}")
            delete_old_points_for_source(
                client=client,
                manifest=manifest,
                source=source,
            )
            manifest = manifest_utils.remove_record(manifest, source)

        # 修改文件：先删旧 points，再重新入库
        for source in changes["changed"]:
            print("")
            print(f"[修改文件重新入库] {source}")

            path = manifest_utils.resolve_source_path(source)

            delete_old_points_for_source(
                client=client,
                manifest=manifest,
                source=source,
            )

            record = index_markdown_file(client, path)
            manifest = manifest_utils.set_record(manifest, source, record)

        # 新增文件：直接入库
        for source in changes["added"]:
            print("")
            print(f"[新增文件入库] {source}")

            path = manifest_utils.resolve_source_path(source)
            record = index_markdown_file(client, path)
            manifest = manifest_utils.set_record(manifest, source, record)

        manifest_utils.save_manifest(manifest)

    except Exception as e:
        print("")
        print(f"[失败] 增量索引执行异常：{e}")
        return 1

    finally:
        try:
            client.close()
        except Exception:
            pass

    print("")
    print("增量索引完成。")
    print("Manifest 已更新：")
    print(manifest_utils.INDEX_MANIFEST_PATH)

    return 0


def run_project_update(
    project: str,
    dry_run: bool = False,
    force_project: bool = False,
) -> int:
    """
    执行项目级索引更新。

    处理逻辑：
    1. 只扫描当前属于该 project 的 Markdown 文件。
    2. 只比较 manifest 中属于该 project 的旧记录。
    3. added：新增入库。
    4. changed：删除旧 points 后重新入库。
    5. deleted：清理 Qdrant points，并从 manifest 删除记录。
    6. unchanged：跳过。
    7. force_project=True 时，当前项目所有现存文件都强制重建。
    """
    project = project.strip()

    if not project:
        print("[失败] project 不能为空。")
        return 1

    manifest = manifest_utils.load_manifest()
    scanned_all = manifest_utils.scan_files()

    scanned_project_files = filter_scanned_files_by_project(
        scanned_files=scanned_all,
        project=project,
    )

    project_manifest = build_project_limited_manifest(
        manifest=manifest,
        project=project,
    )

    changes = manifest_utils.analyze_changes(
        manifest=project_manifest,
        scanned_files=scanned_project_files,
    )

    if force_project:
        changes = apply_force_all(
            changes=changes,
            scanned_files=scanned_project_files,
            manifest=project_manifest,
        )

    print("个人项目秘书 + 数据知识库：项目级索引更新")
    print(f"项目：{project}")
    print(f"知识库根目录：{KNOWLEDGE_ROOT}")
    print(f"集合名称：{COLLECTION_NAME}")
    print(f"项目 Markdown 文件数量：{len(scanned_project_files)}")
    print(f"dry_run：{dry_run}")
    print(f"force_project：{force_project}")

    print_summary(changes)

    print_items("新增文件", changes["added"])
    print_items("修改文件", changes["changed"])
    print_items("删除文件", changes["deleted"])

    if dry_run:
        print("")
        print("当前为 dry-run 模式，未修改 Qdrant，也未写入 manifest。")
        return 0

    client = get_qdrant_client()

    try:
        for source in changes["deleted"]:
            print("")
            print(f"[项目级删除同步清理] {source}")

            delete_old_points_for_source(
                client=client,
                manifest=manifest,
                source=source,
            )

            manifest = manifest_utils.remove_record(manifest, source)

        for source in changes["changed"]:
            print("")
            print(f"[项目级修改文件重新入库] {source}")

            path = manifest_utils.resolve_source_path(source)

            delete_old_points_for_source(
                client=client,
                manifest=manifest,
                source=source,
            )

            record = index_markdown_file(client, path)
            manifest = manifest_utils.set_record(manifest, source, record)

        for source in changes["added"]:
            print("")
            print(f"[项目级新增文件入库] {source}")

            path = manifest_utils.resolve_source_path(source)
            record = index_markdown_file(client, path)
            manifest = manifest_utils.set_record(manifest, source, record)

        manifest_utils.save_manifest(manifest)

    except Exception as e:
        print("")
        print(f"[失败] 项目级索引更新异常：{e}")
        return 1

    finally:
        try:
            client.close()
        except Exception:
            pass

    print("")
    print("项目级索引更新完成。")
    print("Manifest 已更新：")
    print(manifest_utils.INDEX_MANIFEST_PATH)

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="个人项目秘书 + 数据知识库：增量索引工具"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只分析变化，不修改 Qdrant，也不写入 manifest。",
    )

    parser.add_argument(
        "--force-all",
        action="store_true",
        help="强制将所有当前 Markdown 文件重新入库，用于补齐 point_ids。",
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

    args = parser.parse_args()

    selected_modes = [
        bool(args.file),
        bool(args.project),
    ]

    if sum(selected_modes) > 1:
        print("[失败] --file 和 --project 不能同时使用。")
        raise SystemExit(1)

    if args.file:
        code = run_single_file_update(
            raw_file=args.file,
            dry_run=args.dry_run,
            force=args.force_file,
        )

    elif args.project:
        code = run_project_update(
            project=args.project,
            dry_run=args.dry_run,
            force_project=args.force_project,
        )

    else:
        code = run_incremental_index(
            dry_run=args.dry_run,
            force_all=args.force_all,
        )

    raise SystemExit(code)


if __name__ == "__main__":
    main()
