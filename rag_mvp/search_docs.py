import argparse
import os
import re
import sys
from pathlib import Path

import requests
from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue

import config


# ============================================================
# 基础配置
# ============================================================

OLLAMA_URL = config.OLLAMA_URL
EMBED_MODEL = config.EMBED_MODEL
QDRANT_URL = config.QDRANT_URL
COLLECTION_NAME = config.COLLECTION_NAME


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

def get_qdrant_client() -> QdrantClient:
    """
    创建 Qdrant 客户端。
    """
    return QdrantClient(
        url=QDRANT_URL,
        check_compatibility=False,
        timeout=120,
    )


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


def build_filter(
    project: str | None = None,
    doc_type: str | None = None,
    category: str | None = None,
    tag: str | None = None,
) -> Filter | None:
    """
    构建 Qdrant payload 过滤器。

    支持：
    1. project
    2. doc_type
    3. category
    4. tag

    tag 字段通常是 list[str]，Qdrant MatchValue 可匹配数组中的元素。
    """
    must_conditions = []

    if project:
        must_conditions.append(
            FieldCondition(
                key="project",
                match=MatchValue(value=project),
            )
        )

    if doc_type:
        must_conditions.append(
            FieldCondition(
                key="doc_type",
                match=MatchValue(value=doc_type),
            )
        )

    if category:
        must_conditions.append(
            FieldCondition(
                key="category",
                match=MatchValue(value=category),
            )
        )

    if tag:
        must_conditions.append(
            FieldCondition(
                key="tags",
                match=MatchValue(value=tag),
            )
        )

    if not must_conditions:
        return None

    return Filter(must=must_conditions)


def normalize_text(text) -> str:
    """
    将任意值转换为小写字符串，方便关键词匹配。
    """
    if text is None:
        return ""

    if isinstance(text, list):
        text = " ".join(str(item) for item in text)

    return str(text).lower()


def tokenize_query(query: str) -> list[str]:
    """
    将查询拆成关键词。

    兼容：
    1. 英文单词
    2. 数字和版本号，例如 M3.3
    3. 下划线脚本名，例如 update_index.py
    4. 中文连续短语
    """
    query = query.strip().lower()

    if not query:
        return []

    tokens = []

    # 保留原始查询作为短语匹配。
    tokens.append(query)

    # 提取英文/数字/下划线/点/短横线片段。
    ascii_tokens = re.findall(r"[a-zA-Z0-9_\.\-]+", query)
    tokens.extend(ascii_tokens)

    # 提取中文片段。
    chinese_tokens = re.findall(r"[\u4e00-\u9fff]+", query)
    tokens.extend(chinese_tokens)

    # 如果中文片段较长，额外按常见长度切一下，提升召回。
    for item in chinese_tokens:
        if len(item) >= 4:
            for i in range(0, len(item) - 1):
                tokens.append(item[i : i + 2])
            for i in range(0, len(item) - 2):
                tokens.append(item[i : i + 3])

    # 去重但保持顺序。
    result = []
    seen = set()

    for token in tokens:
        token = token.strip()

        if not token:
            continue

        if token in seen:
            continue

        seen.add(token)
        result.append(token)

    return result


def build_keyword_search_text(payload: dict) -> str:
    """
    把 payload 中适合关键词检索的字段合并成一个字符串。

    权重在 score_keyword_payload() 中单独处理。
    """
    fields = [
        payload.get("title", ""),
        payload.get("file_name", ""),
        payload.get("source", ""),
        payload.get("doc_type", ""),
        payload.get("category", ""),
        payload.get("project", ""),
        payload.get("tags", []),
        payload.get("text", ""),
    ]

    return normalize_text(" ".join(normalize_text(field) for field in fields))


def score_keyword_payload(query: str, payload: dict) -> float:
    """
    对单条 payload 做关键词评分。

    分数规则偏实用，不追求复杂：
    1. 完整短语命中 text/title/source 时加高分。
    2. title / file_name / source 命中权重大。
    3. text 命中权重较小。
    4. tokens 命中越多分越高。
    """
    query_norm = query.strip().lower()
    tokens = tokenize_query(query_norm)

    if not tokens:
        return 0.0

    title = normalize_text(payload.get("title", ""))
    file_name = normalize_text(payload.get("file_name", ""))
    source = normalize_text(payload.get("source", ""))
    tags = normalize_text(payload.get("tags", []))
    text = normalize_text(payload.get("text", ""))
    doc_type = normalize_text(payload.get("doc_type", ""))
    category = normalize_text(payload.get("category", ""))
    project = normalize_text(payload.get("project", ""))

    score = 0.0

    # 完整短语命中。
    if query_norm and query_norm in title:
        score += 40

    if query_norm and query_norm in file_name:
        score += 35

    if query_norm and query_norm in source:
        score += 35

    if query_norm and query_norm in tags:
        score += 20

    if query_norm and query_norm in text:
        score += 25

    # token 命中。
    for token in tokens:
        if token in title:
            score += 10

        if token in file_name:
            score += 8

        if token in source:
            score += 8

        if token in tags:
            score += 6

        if token in doc_type:
            score += 4

        if token in category:
            score += 3

        if token in project:
            score += 3

        if token in text:
            score += 2

    # 轻微惩罚完全没有正文的记录。
    if not text.strip():
        score -= 1

    return score


def vector_search(
    client: QdrantClient,
    query: str,
    query_filter: Filter | None,
    limit: int,
) -> list[dict]:
    """
    执行向量语义检索。
    """
    query_vector = embed_text(query)

    if hasattr(client, "query_points"):
        response = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            query_filter=query_filter,
            limit=limit,
            with_payload=True,
        )
        points = response.points
    else:
        points = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            query_filter=query_filter,
            limit=limit,
            with_payload=True,
        )

    results = []

    for point in points:
        payload = point.payload or {}

        results.append(
            {
                "score": float(point.score),
                "payload": payload,
                "point_id": str(point.id),
                "mode": "vector",
            }
        )

    return results


def keyword_search(
    client: QdrantClient,
    query: str,
    query_filter: Filter | None,
    limit: int,
    max_scan_points: int = 5000,
) -> list[dict]:
    """
    执行关键词检索。

    实现方式：
    1. 使用 Qdrant scroll 拉取 payload。
    2. 在 Python 中对 title/file_name/source/tags/text 做关键词匹配。
    3. 按关键词分数排序。

    说明：
    这是 M3.6 的基础关键词检索。
    M3.7 会再做 hybrid 检索。
    """
    results = []
    offset = None
    scanned = 0

    while True:
        points, offset = client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=query_filter,
            limit=200,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )

        if not points:
            break

        for point in points:
            payload = point.payload or {}
            score = score_keyword_payload(query, payload)

            scanned += 1

            if score > 0:
                results.append(
                    {
                        "score": float(score),
                        "payload": payload,
                        "point_id": str(point.id),
                        "mode": "keyword",
                    }
                )

            if scanned >= max_scan_points:
                break

        if offset is None:
            break

        if scanned >= max_scan_points:
            break

    results.sort(
        key=lambda item: (
            item["score"],
            payload_sort_time(item.get("payload", {})),
        ),
        reverse=True,
    )

    return results[:limit]


def hybrid_search(
    client: QdrantClient,
    query: str,
    query_filter: Filter | None,
    limit: int,
    max_scan_points: int = 5000,
    vector_weight: float = 0.6,
    keyword_weight: float = 0.4,
) -> list[dict]:
    """
    执行混合检索。

    逻辑：
    1. 先执行 vector_search，获得语义相近结果。
    2. 再执行 keyword_search，获得关键词命中结果。
    3. 对两组结果分别归一化。
    4. 按去重 key 合并。
    5. 使用 hybrid_score = vector_score * 权重 + keyword_score * 权重。
    """
    vector_limit = max(limit * 3, 10)
    keyword_limit = max(limit * 3, 10)

    vector_results = vector_search(
        client=client,
        query=query,
        query_filter=query_filter,
        limit=vector_limit,
    )

    keyword_results = keyword_search(
        client=client,
        query=query,
        query_filter=query_filter,
        limit=keyword_limit,
        max_scan_points=max_scan_points,
    )

    vector_scores = normalize_result_scores(vector_results)
    keyword_scores = normalize_result_scores(keyword_results)

    merged = {}

    for item in vector_results:
        key = result_dedupe_key(item)
        merged[key] = {
            "score": 0.0,
            "vector_score": float(item.get("score", 0.0)),
            "keyword_score": 0.0,
            "vector_norm": vector_scores.get(key, 0.0),
            "keyword_norm": 0.0,
            "payload": item.get("payload", {}),
            "point_id": item.get("point_id", ""),
            "mode": "hybrid",
            "hit_modes": ["vector"],
        }

    for item in keyword_results:
        key = result_dedupe_key(item)

        if key not in merged:
            merged[key] = {
                "score": 0.0,
                "vector_score": 0.0,
                "keyword_score": float(item.get("score", 0.0)),
                "vector_norm": 0.0,
                "keyword_norm": keyword_scores.get(key, 0.0),
                "payload": item.get("payload", {}),
                "point_id": item.get("point_id", ""),
                "mode": "hybrid",
                "hit_modes": ["keyword"],
            }
        else:
            merged[key]["keyword_score"] = float(item.get("score", 0.0))
            merged[key]["keyword_norm"] = keyword_scores.get(key, 0.0)

            if "keyword" not in merged[key]["hit_modes"]:
                merged[key]["hit_modes"].append("keyword")

    results = []

    for item in merged.values():
        hybrid_score = (
            item["vector_norm"] * vector_weight
            + item["keyword_norm"] * keyword_weight
        )

        # 同时命中 vector 和 keyword 时，给一点加成。
        if "vector" in item["hit_modes"] and "keyword" in item["hit_modes"]:
            hybrid_score += 0.15

        item["score"] = hybrid_score
        results.append(item)

    results.sort(
        key=lambda item: (
            item.get("score", 0.0),
            payload_sort_time(item.get("payload", {})),
        ),
        reverse=True,
    )

    return results[:limit]


def payload_sort_time(payload: dict) -> str:
    """
    用于同分时排序。
    """
    return str(payload.get("updated_at", ""))


def result_dedupe_key(item: dict) -> str:
    """
    生成检索结果去重 key。

    优先使用 point_id。
    如果 point_id 不存在，则使用 source + chunk_index。
    """
    point_id = str(item.get("point_id", "")).strip()

    if point_id:
        return f"point:{point_id}"

    payload = item.get("payload", {})
    source = payload.get("source", "")
    chunk_index = payload.get("chunk_index", "")

    return f"source:{source}#chunk:{chunk_index}"


def normalize_score(value: float, min_value: float, max_value: float) -> float:
    """
    将分数归一化到 0 到 1。

    用于把 vector 分数和 keyword 分数合并。
    """
    if max_value <= min_value:
        return 1.0 if value > 0 else 0.0

    return (value - min_value) / (max_value - min_value)


def normalize_result_scores(results: list[dict]) -> dict[str, float]:
    """
    对一组结果按自身分数范围归一化。

    返回：
    dedupe_key -> normalized_score
    """
    if not results:
        return {}

    scores = [float(item.get("score", 0.0)) for item in results]
    min_score = min(scores)
    max_score = max(scores)

    normalized = {}

    for item in results:
        key = result_dedupe_key(item)
        score = float(item.get("score", 0.0))
        normalized[key] = normalize_score(score, min_score, max_score)

    return normalized


def print_result(
    index: int,
    item: dict,
    show_text: bool = False,
) -> None:
    """
    打印单条检索结果。
    """
    payload = item.get("payload", {})
    score = item.get("score", 0.0)
    mode = item.get("mode", "")

    print("")
    print("=" * 80)
    print(f"结果 {index}")
    print("=" * 80)

    if mode == "keyword":
        print(f"关键词分数：{score:.4f}")
    elif mode == "hybrid":
        print(f"混合分数：{score:.4f}")
        print(f"向量原始分数：{item.get('vector_score', 0.0):.4f}")
        print(f"关键词原始分数：{item.get('keyword_score', 0.0):.4f}")
        print(f"命中来源：{item.get('hit_modes', [])}")
    else:
        print(f"相关度：{score:.4f}")

    print(f"检索模式：{mode}")
    print(f"资料大类：{payload.get('category', '')}")
    print(f"项目：{payload.get('project', '')}")
    print(f"文档类型：{payload.get('doc_type', '')}")
    print(f"标题：{payload.get('title', '')}")
    print(f"标签：{payload.get('tags', [])}")
    print(f"文件名：{payload.get('file_name', '')}")
    print(f"来源：{payload.get('source', '')}")
    print(f"片段：{payload.get('chunk_index', '')}")
    print(f"更新时间：{payload.get('updated_at', '')}")

    if show_text:
        print("")
        print("内容预览：")
        text = payload.get("text", "")

        if len(text) > 600:
            print(text[:600] + "\n...")
        else:
            print(text)

def print_summary(
    query: str,
    mode: str,
    results: list[dict],
    project: str | None,
    doc_type: str | None,
    category: str | None,
    tag: str | None,
) -> None:
    """
    打印检索摘要。
    """
    print(f"搜索内容：{query}")
    print(f"检索模式：{mode}")

    if project:
        print(f"限定项目：{project}")

    if doc_type:
        print(f"限定文档类型：{doc_type}")

    if category:
        print(f"限定资料大类：{category}")

    if tag:
        print(f"限定标签：{tag}")

    print(f"检索结果数量：{len(results)}")


def main():
    parser = argparse.ArgumentParser(
        description="个人项目秘书 + 数据知识库：知识库片段搜索"
    )

    parser.add_argument(
        "query",
        help="搜索内容。",
    )

    parser.add_argument(
        "--mode",
        choices=["vector", "keyword", "hybrid"],
        default="vector",
        help=(
            "搜索模式："
            "vector=向量语义检索，"
            "keyword=关键词检索，"
            "hybrid=混合检索。默认 vector。"
        ),
    )

    parser.add_argument(
        "--project",
        default=None,
        help="限定项目。",
    )

    parser.add_argument(
        "--doc-type",
        default=None,
        help="限定文档类型。",
    )

    parser.add_argument(
        "--category",
        default=None,
        help="限定资料大类。",
    )

    parser.add_argument(
        "--tag",
        default=None,
        help="限定标签。",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="返回结果数量。",
    )

    parser.add_argument(
        "--max-scan-points",
        type=int,
        default=5000,
        help="keyword 模式最多扫描多少个 Qdrant points。",
    )

    parser.add_argument(
        "--vector-weight",
        type=float,
        default=0.6,
        help="hybrid 模式下向量检索权重，默认 0.6。",
    )

    parser.add_argument(
        "--keyword-weight",
        type=float,
        default=0.4,
        help="hybrid 模式下关键词检索权重，默认 0.4。",
    )

    parser.add_argument(
        "--show-text",
        action="store_true",
        help="显示片段正文预览。",
    )

    args = parser.parse_args()

    query_filter = build_filter(
        project=args.project,
        doc_type=args.doc_type,
        category=args.category,
        tag=args.tag,
    )

    client = get_qdrant_client()

    try:
        if args.mode == "vector":
            results = vector_search(
                client=client,
                query=args.query,
                query_filter=query_filter,
                limit=args.limit,
            )
        elif args.mode == "keyword":
            results = keyword_search(
                client=client,
                query=args.query,
                query_filter=query_filter,
                limit=args.limit,
                max_scan_points=args.max_scan_points,
            )
        else:
            results = hybrid_search(
                client=client,
                query=args.query,
                query_filter=query_filter,
                limit=args.limit,
                max_scan_points=args.max_scan_points,
                vector_weight=args.vector_weight,
                keyword_weight=args.keyword_weight,
            )

    finally:
        try:
            client.close()
        except Exception:
            pass

    print_summary(
        query=args.query,
        mode=args.mode,
        results=results,
        project=args.project,
        doc_type=args.doc_type,
        category=args.category,
        tag=args.tag,
    )

    for index, item in enumerate(results, start=1):
        print_result(
            index=index,
            item=item,
            show_text=args.show_text,
        )


if __name__ == "__main__":
    main()

