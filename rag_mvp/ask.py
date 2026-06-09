import argparse
import os
import re
import requests
import sys
from datetime import datetime
from pathlib import Path

# 避免 Python/qdrant-client 访问本机服务时走系统代理
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

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

from config import (
    OLLAMA_URL,
    EMBED_MODEL,
    CHAT_MODEL,
    QDRANT_URL,
    COLLECTION_NAME,
    SEARCH_LIMIT,
    QA_LOG_DIR,
)


def embed_text(text: str) -> list[float]:
    """
    调用 Ollama 生成向量。

    优先使用 /api/embed。
    如果当前 Ollama 版本不支持，则回退到 /api/embeddings。
    """
    text = text.strip()

    if not text:
        raise ValueError("不能向量化空文本")

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

            if "embeddings" in data and data["embeddings"]:
                return data["embeddings"][0]

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


def clean_model_response(text: str) -> str:
    """
    清理 qwen3 可能输出的 <think>...</think> 思考内容。
    """
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    return text.strip()


def collection_exists(client: QdrantClient, collection_name: str) -> bool:
    """
    检查 Qdrant collection 是否存在。
    """
    try:
        return client.collection_exists(collection_name)
    except Exception:
        existing = [c.name for c in client.get_collections().collections]
        return collection_name in existing


def build_query_filter(
    project: str | None = None,
    doc_type: str | None = None,
    category: str | None = None,
    tag: str | None = None,
):
    """
    根据项目名、文档类型、资料大类、标签构建 Qdrant 过滤条件。
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


# ============================================================
# M3.7 / M3.7-b：关键词检索与混合检索辅助函数
# ============================================================

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

    支持：
    1. 英文单词
    2. 数字和版本号，例如 M3.3
    3. 脚本名，例如 update_index.py
    4. 中文连续短语
    """
    query = query.strip().lower()

    if not query:
        return []

    tokens = []

    # 完整查询用于短语命中。
    tokens.append(query)

    # 英文、数字、版本号、脚本名。
    ascii_tokens = re.findall(r"[a-zA-Z0-9_\.\-]+", query)
    tokens.extend(ascii_tokens)

    # 中文片段。
    chinese_tokens = re.findall(r"[\u4e00-\u9fff]+", query)
    tokens.extend(chinese_tokens)

    # 中文长词额外切成 2 字和 3 字片段，提升召回。
    for item in chinese_tokens:
        if len(item) >= 4:
            for i in range(0, len(item) - 1):
                tokens.append(item[i : i + 2])

            for i in range(0, len(item) - 2):
                tokens.append(item[i : i + 3])

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


def score_keyword_payload(query: str, payload: dict) -> float:
    """
    对单条 payload 做关键词评分。

    分数越高，表示关键词命中越明确。
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

    return score


def payload_sort_time(payload: dict) -> str:
    """
    同分时按更新时间排序。
    """
    return str(payload.get("updated_at", ""))


def result_dedupe_key(item: dict) -> str:
    """
    生成检索结果去重 key。
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


def payload_to_context_item(
    payload: dict,
    score: float = 0.0,
    mode: str = "vector",
) -> dict:
    """
    将 Qdrant payload 转换为 ask.py 使用的上下文结构。
    """
    return {
        "score": score,
        "mode": mode,
        "category": payload.get("category", ""),
        "project": payload.get("project", ""),
        "doc_type": payload.get("doc_type", ""),
        "title": payload.get("title", ""),
        "tags": payload.get("tags", []),
        "file_name": payload.get("file_name", ""),
        "source": payload.get("source", ""),
        "chunk_index": payload.get("chunk_index", ""),
        "updated_at": payload.get("updated_at", ""),
        "text": payload.get("text", ""),
    }


def vector_search_contexts(
    client: QdrantClient,
    question: str,
    query_filter,
    limit: int,
) -> list[dict]:
    """
    向量语义检索。
    """
    query_vector = embed_text(question)

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


def keyword_search_contexts(
    client: QdrantClient,
    question: str,
    query_filter,
    limit: int,
    max_scan_points: int = 5000,
) -> list[dict]:
    """
    关键词检索。

    通过 Qdrant scroll 读取 payload，再在 Python 中做关键词评分。
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
            score = score_keyword_payload(question, payload)

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


def hybrid_search_contexts(
    client: QdrantClient,
    question: str,
    query_filter,
    limit: int,
    max_scan_points: int = 5000,
    vector_weight: float = 0.6,
    keyword_weight: float = 0.4,
) -> list[dict]:
    """
    混合检索：
    vector + keyword 去重、归一化、加权合并。
    """
    vector_limit = max(limit * 3, 10)
    keyword_limit = max(limit * 3, 10)

    vector_results = vector_search_contexts(
        client=client,
        question=question,
        query_filter=query_filter,
        limit=vector_limit,
    )

    keyword_results = keyword_search_contexts(
        client=client,
        question=question,
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


def search_context(
    question: str,
    limit: int = 5,
    project: str | None = None,
    doc_type: str | None = None,
    category: str | None = None,
    tag: str | None = None,
    search_mode: str = "vector",
    max_scan_points: int = 5000,
    vector_weight: float = 0.6,
    keyword_weight: float = 0.4,
) -> list[dict]:
    """
    检索问答上下文。

    search_mode:
    - vector：向量语义检索
    - keyword：关键词检索
    - hybrid：混合检索

    兼容旧调用：
    health_check_full.py 中原来的 search_context(question=..., limit=..., project=...)
    不需要修改。
    """
    client = QdrantClient(
        url=QDRANT_URL,
        check_compatibility=False,
        timeout=120,
    )

    query_filter = build_query_filter(
        project=project,
        doc_type=doc_type,
        category=category,
        tag=tag,
    )

    try:
        if search_mode == "vector":
            raw_results = vector_search_contexts(
                client=client,
                question=question,
                query_filter=query_filter,
                limit=limit,
            )

        elif search_mode == "keyword":
            raw_results = keyword_search_contexts(
                client=client,
                question=question,
                query_filter=query_filter,
                limit=limit,
                max_scan_points=max_scan_points,
            )

        elif search_mode == "hybrid":
            raw_results = hybrid_search_contexts(
                client=client,
                question=question,
                query_filter=query_filter,
                limit=limit,
                max_scan_points=max_scan_points,
                vector_weight=vector_weight,
                keyword_weight=keyword_weight,
            )

        else:
            raise ValueError(f"不支持的 search_mode：{search_mode}")

    finally:
        try:
            client.close()
        except Exception:
            pass

    contexts = []

    for item in raw_results:
        payload = item.get("payload", {})

        ctx = payload_to_context_item(
            payload=payload,
            score=float(item.get("score", 0.0)),
            mode=item.get("mode", search_mode),
        )

        if item.get("mode") == "hybrid":
            ctx["vector_score"] = item.get("vector_score", 0.0)
            ctx["keyword_score"] = item.get("keyword_score", 0.0)
            ctx["hit_modes"] = item.get("hit_modes", [])

        contexts.append(ctx)

    return contexts


def generate_answer(question: str, contexts: list[dict]) -> str:
    """
    根据检索上下文调用 qwen3:8b 生成回答。
    """
    if not contexts:
        return "当前知识库没有检索到相关资料，无法确认。"

    context_text = ""

    for i, ctx in enumerate(contexts, start=1):
        mode = ctx.get("mode", "vector")

        context_text += f"\n[资料 {i}]\n"
        context_text += (
            f"资料大类：{ctx.get('category', '')}，"
            f"项目：{ctx.get('project', '')}，"
            f"文档类型：{ctx.get('doc_type', '')}，"
            f"标题：{ctx.get('title', '')}，"
            f"标签：{ctx.get('tags', [])}，"
            f"文件：{ctx.get('file_name', '')}，"
            f"来源：{ctx.get('source', '')}，"
            f"片段：{ctx.get('chunk_index', '')}，"
            f"更新时间：{ctx.get('updated_at', '')}，"
            f"检索模式：{mode}，"
            f"检索分数：{ctx.get('score', 0.0):.4f}\n"
        )

        if mode == "hybrid":
            context_text += (
                f"向量原始分数：{ctx.get('vector_score', 0.0):.4f}，"
                f"关键词原始分数：{ctx.get('keyword_score', 0.0):.4f}，"
                f"命中来源：{ctx.get('hit_modes', [])}\n"
            )

        context_text += ctx.get("text", "")
        context_text += "\n"

    prompt = f"""
你是我的个人项目秘书和数据知识库助手。

请严格根据下面提供的知识库资料回答问题。
如果资料中没有明确答案，请说明“当前知识库资料不足，无法确认”，不要编造。

【知识库资料】
{context_text}

【用户问题】
{question}

【回答要求】
1. 使用中文回答。
2. 先给出直接结论。
3. 再列出依据。
4. 最后给出下一步建议。
5. 不要输出思考过程。
"""

    resp = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": CHAT_MODEL,
            "prompt": prompt,
            "stream": False,
        },
        timeout=300,
    )
    resp.raise_for_status()

    data = resp.json()
    return clean_model_response(data.get("response", ""))


def save_qa_log(question: str, answer: str, contexts: list[dict]) -> None:
    """
    保存本次问答记录到 Markdown 文件。

    这个函数会自动生成带 Frontmatter 的 Markdown 文件，
    方便后续重新入库，并通过 category / project / doc_type / tag 检索。
    """
    QA_LOG_DIR.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
    file_path = QA_LOG_DIR / f"{timestamp}_qa.md"

    lines = []

    # =========================
    # Markdown Frontmatter
    # =========================
    lines.append("---")
    lines.append(f"title: 问答记录 {timestamp}")
    lines.append(f"created: {now.isoformat(timespec='seconds')}")
    lines.append("category: summary")
    lines.append("project: Personal_Project_Assistant")
    lines.append("doc_type: qa_log")
    lines.append("tags: [问答记录, RAG, 自动生成]")
    lines.append("---")
    lines.append("")

    # =========================
    # 正文内容
    # =========================
    lines.append("# 问答记录")
    lines.append("")

    lines.append("## 用户问题")
    lines.append("")
    lines.append(question)
    lines.append("")

    lines.append("## 检索来源")
    lines.append("")

    if not contexts:
        lines.append("未检索到相关资料。")
        lines.append("")
    else:
        for i, ctx in enumerate(contexts, start=1):
            mode = ctx.get("mode", "vector")

            lines.append(f"### 资料 {i}")
            lines.append("")
            lines.append(f"- 资料大类：{ctx.get('category', '')}")
            lines.append(f"- 项目：{ctx.get('project', '')}")
            lines.append(f"- 文档类型：{ctx.get('doc_type', '')}")
            lines.append(f"- 标题：{ctx.get('title', '')}")
            lines.append(f"- 标签：{ctx.get('tags', [])}")
            lines.append(f"- 文件名：{ctx.get('file_name', '')}")
            lines.append(f"- 来源：{ctx.get('source', '')}")
            lines.append(f"- 片段：{ctx.get('chunk_index', '')}")
            lines.append(f"- 检索模式：{mode}")
            lines.append(f"- 检索分数：{ctx.get('score', 0):.4f}")

            if mode == "hybrid":
                lines.append(f"- 向量原始分数：{ctx.get('vector_score', 0.0):.4f}")
                lines.append(f"- 关键词原始分数：{ctx.get('keyword_score', 0.0):.4f}")
                lines.append(f"- 命中来源：{ctx.get('hit_modes', [])}")

            lines.append(f"- 更新时间：{ctx.get('updated_at', '')}")
            lines.append("")

    lines.append("## 模型回答")
    lines.append("")
    lines.append(answer)
    lines.append("")

    file_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"\n问答记录已保存：{file_path}")


def print_contexts(contexts: list[dict]) -> None:
    """
    打印检索到的资料列表。
    """
    print("\n=== 检索到的资料 ===")

    if not contexts:
        print("未检索到相关资料。")
        return

    for i, ctx in enumerate(contexts, start=1):
        mode = ctx.get("mode", "vector")
        score = ctx.get("score", 0.0)

        print(
            f"{i}. [{ctx.get('category', '')}] "
            f"[{ctx.get('project', '')}] "
            f"{ctx.get('doc_type', '')} / {ctx.get('file_name', '')} "
            f"tags={ctx.get('tags', [])} "
            f"| mode={mode} "
            f"| score={score:.4f}"
        )

        print(f"   来源：{ctx.get('source', '')}")

        if mode == "hybrid":
            print(
                "   "
                f"vector={ctx.get('vector_score', 0.0):.4f} | "
                f"keyword={ctx.get('keyword_score', 0.0):.4f} | "
                f"hit={ctx.get('hit_modes', [])}"
            )


def main():
    parser = argparse.ArgumentParser(
        description="个人项目秘书 + 数据知识库：RAG 问答脚本"
    )

    parser.add_argument(
        "question",
        nargs="*",
        help="要提问的问题",
    )

    parser.add_argument(
        "--project",
        default=None,
        help="限定检索的项目名，例如 Personal_Project_Assistant",
    )

    parser.add_argument(
        "--doc-type",
        default=None,
        help="限定检索的文档类型，例如 progress_log、model_decisions、issues、next_steps",
    )

    parser.add_argument(
        "--category",
        default=None,
        help="限定资料大类，例如 project、knowledge、decision、problem、summary、attachment",
    )

    parser.add_argument(
        "--tag",
        default=None,
        help="限定标签，例如 RAG、问答记录、自动生成",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=SEARCH_LIMIT,
        help="检索返回片段数量",
    )

    parser.add_argument(
        "--search-mode",
        choices=["vector", "keyword", "hybrid"],
        default="vector",
        help="检索模式：vector=向量检索，keyword=关键词检索，hybrid=混合检索。默认 vector。",
    )

    parser.add_argument(
        "--max-scan-points",
        type=int,
        default=5000,
        help="keyword / hybrid 模式最多扫描多少个 Qdrant points。",
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

    args = parser.parse_args()

    if args.question:
        question = " ".join(args.question).strip()
    else:
        question = input("请输入问题：").strip()

    if not question:
        print("问题不能为空。")
        return

    if args.project:
        print(f"限定项目：{args.project}")

    if args.doc_type:
        print(f"限定文档类型：{args.doc_type}")

    if args.category:
        print(f"限定资料大类：{args.category}")

    if args.tag:
        print(f"限定标签：{args.tag}")

    print(f"检索模式：{args.search_mode}")

    if args.search_mode == "hybrid":
        print(f"向量权重：{args.vector_weight}")
        print(f"关键词权重：{args.keyword_weight}")

    contexts = search_context(
        question=question,
        limit=args.limit,
        project=args.project,
        doc_type=args.doc_type,
        category=args.category,
        tag=args.tag,
        search_mode=args.search_mode,
        max_scan_points=args.max_scan_points,
        vector_weight=args.vector_weight,
        keyword_weight=args.keyword_weight,
    )

    print_contexts(contexts)

    print("\n=== qwen3:8b 回答 ===")
    answer = generate_answer(question, contexts)
    print(answer)

    save_qa_log(question, answer, contexts)


if __name__ == "__main__":
    main()
