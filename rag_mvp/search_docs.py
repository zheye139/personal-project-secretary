import argparse
import os
import requests

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

from config import (
    OLLAMA_URL,
    EMBED_MODEL,
    QDRANT_URL,
    COLLECTION_NAME,
    SEARCH_LIMIT,
)


# Prevent local service requests from going through system proxies.
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


def embed_text(text: str) -> list[float]:
    text = text.strip()
    if not text:
        raise ValueError("Cannot embed empty text")

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


def build_query_filter(
    project: str | None = None,
    doc_type: str | None = None,
    category: str | None = None,
    tag: str | None = None,
):
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


def search_docs(
    query: str,
    limit: int,
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

    if not client.collection_exists(COLLECTION_NAME):
        raise RuntimeError(f"collection does not exist:{COLLECTION_NAME}, please first  python update_index.py")

    query_vector = embed_text(query)
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

    docs = []

    for item in results:
        payload = item.payload or {}
        docs.append(
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

    return docs


def print_results(results: list[dict], show_text: bool, max_text_chars: int):
    if not results:
        print("not retrieved records. ")
        return

    print(f"retrieval resultscount:{len(results)}")

    for i, item in enumerate(results, start=1):
        print("\n" + "=" * 80)
        print(f"  {i}")
        print("=" * 80)
        print(f"relevance score:{item['score']:.4f}")
        print(f"record category:{item['category']}")
        print(f" :{item['project']}")
        print(f"document type:{item['doc_type']}")
        print(f"title:{item['title']}")
        print(f"tags:{item['tags']}")
        print(f"file name:{item['file_name']}")
        print(f"source:{item['source']}")
        print(f"chunk:{item['chunk_index']}")
        print(f"updated at:{item['updated_at']}")

        if show_text:
            text = item["text"] or ""
            preview = text[:max_text_chars]
            print("\ncontent preview:")
            print(preview)

            if len(text) > max_text_chars:
                print("...")


def main():
    parser = argparse.ArgumentParser(
        description="Personal Project Secretary + Knowledge Base:searchknowledge basechunk, notcall qwen3:8b"
    )

    parser.add_argument(
        "query",
        nargs="*",
        help="searchissueor ",
    )

    parser.add_argument(
        "--project",
        default=None,
        help=" , for example Demo_Project",
    )

    parser.add_argument(
        "--doc-type",
        default=None,
        help=" document type, for example progress_log, qa_log, project_report",
    )

    parser.add_argument(
        "--category",
        default=None,
        help=" record category, for example project, knowledge, decision, problem, summary",
    )

    parser.add_argument(
        "--tag",
        default=None,
        help=" tags, for example RAG, auto generated, project report",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=SEARCH_LIMIT,
        help=" count",
    )

    parser.add_argument(
        "--show-text",
        action="store_true",
        help="displaychunk textpreview",
    )

    parser.add_argument(
        "--max-text-chars",
        type=int,
        default=500,
        help="bodypreview ",
    )

    args = parser.parse_args()

    if args.query:
        query = " ".join(args.query).strip()
    else:
        query = input("Enter search query:").strip()

    if not query:
        print("Search query cannot be empty. ")
        return

    if args.project:
        print(f" :{args.project}")
    if args.doc_type:
        print(f" document type:{args.doc_type}")
    if args.category:
        print(f" record category:{args.category}")
    if args.tag:
        print(f" tags:{args.tag}")

    print(f"search query:{query}")

    results = search_docs(
        query=query,
        limit=args.limit,
        project=args.project,
        doc_type=args.doc_type,
        category=args.category,
        tag=args.tag,
    )

    print_results(
        results=results,
        show_text=args.show_text,
        max_text_chars=args.max_text_chars,
    )


if __name__ == "__main__":
    main()