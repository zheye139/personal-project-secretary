import argparse
import re
import os
import requests
from datetime import datetime

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
    text = text.strip()
    if not text:
        raise ValueError("Empty text cannot be vectorized")

    try:
        resp = requests.post(
            f"{OLLAMA_URL}/api/embed",
            json={"model": EMBED_MODEL, "input": text},
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
        json={"model": EMBED_MODEL, "prompt": text},
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


def search_context(
    question: str,
    limit: int = SEARCH_LIMIT,
    project: str | None = None,
    doc_type: str | None = None,
    category: str | None = None,
    tag: str | None = None,
) -> list[dict]:
    client = QdrantClient(
        url=QDRANT_URL,
        check_compatibility=False,
        timeout=60,
    )

    if not collection_exists(client, COLLECTION_NAME):
        raise RuntimeError(
            f"未找到集合 {COLLECTION_NAME}，请先运行 python ingest.py 完成入库。"
        )

    query_vector = embed_text(question)
    query_filter = build_query_filter(
        project=project,
        doc_type=doc_type,
        category=category,
        tag=tag,
    )

    if hasattr(client, "query_points"):
        response = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            query_filter=query_filter,
            limit=limit,
            with_payload=True,
        )
        results = response.points
    else:
        results = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            query_filter=query_filter,
            limit=limit,
        )

    contexts = []

    for item in results:
        payload = item.payload or {}
        contexts.append(
            {
                "score": item.score,
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
        )

    try:
        client.close()
    except Exception:
        pass

    return contexts


def generate_answer(question: str, contexts: list[dict]) -> str:
    if not contexts:
        return "No relevant information was found in the current knowledge base, so confirmation is not possible."

    context_text = ""

    for i, ctx in enumerate(contexts, start=1):
        context_text += f"\n[data {i}]\n"
        context_text += (
            f"Category: {ctx['category']}, "
            f"Project: {ctx['project']}, "
            f"Document type: {ctx['doc_type']}, "
            f"Title: {ctx['title']}, "
            f"Tags: {ctx['tags']}, "
            f"File name: {ctx['file_name']}, "
            f"Source path: {ctx['source']}, "
            f"Chunk index: {ctx['chunk_index']}, "
            f"Updated at: {ctx['updated_at']}, "
            f"Score: {ctx['score']:.4f}\n"
        )
        context_text += ctx["text"]
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
    方便后续 ingest.py 重新入库，并通过 category / project / doc_type / tag 检索。
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
    lines.append(f"title: Question and Answer Record {timestamp}")
    lines.append(f"created: {now.isoformat(timespec='seconds')}")
    lines.append("category: summary")
    lines.append("project: Demo_Project")
    lines.append("doc_type: qa_log")
    lines.append("tags: [Question and Answer Record, RAG, Automatically generated]")
    lines.append("---")
    lines.append("")

    # =========================
    # 正文内容
    # =========================
    lines.append("# Question and Answer Record")
    lines.append("")

    lines.append("## User Issues")
    lines.append("")
    lines.append(question)
    lines.append("")

    lines.append("## Search source")
    lines.append("")

    if not contexts:
        lines.append("No relevant information was found.。")
        lines.append("")
    else:
        for i, ctx in enumerate(contexts, start=1):
            lines.append(f"### data {i}")
            lines.append("")
            lines.append(f"- Category：{ctx.get('category', '')}")
            lines.append(f"- Project：{ctx.get('project', '')}")
            lines.append(f"- Document type: {ctx.get('doc_type', '')}")
            lines.append(f"- Title：{ctx.get('title', '')}")
            lines.append(f"- Tags：{ctx.get('tags', [])}")
            lines.append(f"- File name：{ctx.get('file_name', '')}")
            lines.append(f"- Source path: {ctx.get('source', '')}")
            lines.append(f"- Chunk index：{ctx.get('chunk_index', '')}")
            lines.append(f"- Score：{ctx.get('score', 0):.4f}")
            lines.append(f"- Updated at：{ctx.get('updated_at', '')}")
            lines.append("")

    lines.append("## Model Response")
    lines.append("")
    lines.append(answer)
    lines.append("")

    file_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"\n问答记录已保存：{file_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Personal Project Secretary + Data Knowledge Base: RAG Question Answering Script"
    )

    parser.add_argument(
        "question",
        nargs="*",
        help="Questions to ask",
    )

    parser.add_argument(
        "--project",
        default=None,
        help="Limit the search to the project name, for example, Demo_Project",
    )

    parser.add_argument(
        "--doc-type",
        default=None,
        help="Limit the document type to be searched, for example progress_log、model_decisions、issues、next_steps",
    )
    
    parser.add_argument(
        "--category",
        default=None,
        help="Limited data categories, for example project、knowledge、decision、problem、summary、attachment",
    )
    
    parser.add_argument(
        "--tag",
        default=None,
        help="Limited tags, such as RAG, Q&A history, and automatically generated tags.",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=SEARCH_LIMIT,
        help="Number of fragments retrieved",
    )

    args = parser.parse_args()

    if args.question:
        question = " ".join(args.question).strip()
    else:
        question = input("Please enter your question.：").strip()

    if not question:
        print("The question cannot be empty.。")
        return

    if args.project:
        print(f"Limited items：{args.project}")

    if args.doc_type:
        print(f"Document type restrictions：{args.doc_type}")
        
    if args.category:
        print(f"Limited data categories：{args.category}")
    
    if args.tag:
        print(f"Limited Label：{args.tag}")

    contexts = search_context(
        question=question,
        limit=args.limit,
        project=args.project,
        doc_type=args.doc_type,
        category=args.category,
        tag=args.tag,
    )

    print("\n=== Found data ===")

    if not contexts:
        print("No relevant information was found.。")
    else:
        for i, ctx in enumerate(contexts, start=1):
            print(
                f"{i}. [{ctx['category']}] "
                f"[{ctx['project']}] "
                f"{ctx['doc_type']} / {ctx['file_name']} "
                f"tags={ctx['tags']} "
                f"| score={ctx['score']:.4f}"
            )

    print("\n=== qwen3:8b answer ===")
    answer = generate_answer(question, contexts)
    print(answer)
    
    save_qa_log(question, answer, contexts)


if __name__ == "__main__":
    main()