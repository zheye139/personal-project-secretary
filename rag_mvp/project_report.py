import argparse
import os
import requests
from datetime import datetime
from collections import defaultdict

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

from config import (
    OLLAMA_URL,
    CHAT_MODEL,
    QDRANT_URL,
    COLLECTION_NAME,
    PROJECT_REPORT_DIR,
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


def build_project_filter(project: str):
    return Filter(
        must=[
            FieldCondition(
                key="project",
                match=MatchValue(value=project),
            )
        ]
    )


def load_project_context(project: str, max_points: int = 80, max_chars: int = 18000) -> list[dict]:
    """
    from Qdrant inreadspecified purposerecords. 
      scroll, not retrieval,  report. 
    """
    client = QdrantClient(
        url=QDRANT_URL,
        check_compatibility=False,
        timeout=60,
    )

    if not client.collection_exists(COLLECTION_NAME):
        raise RuntimeError(f"collection does not exist:{COLLECTION_NAME}, please first  python update_index.py")

    query_filter = build_project_filter(project)

    offset = None
    contexts = []
    total_chars = 0

    while True:
        points, offset = client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=query_filter,
            limit=50,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )

        if not points:
            break

        for point in points:
            payload = point.payload or {}
            text = payload.get("text", "")

            if not text:
                continue

            item = {
                "category": payload.get("category", ""),
                "project": payload.get("project", ""),
                "doc_type": payload.get("doc_type", ""),
                "title": payload.get("title", ""),
                "tags": payload.get("tags", []),
                "file_name": payload.get("file_name", ""),
                "source": payload.get("source", ""),
                "chunk_index": payload.get("chunk_index", ""),
                "updated_at": payload.get("updated_at", ""),
                "text": text,
            }

            contexts.append(item)
            total_chars += len(text)

            if len(contexts) >= max_points or total_chars >= max_chars:
                break

        if offset is None:
            break

        if len(contexts) >= max_points or total_chars >= max_chars:
            break

    try:
        client.close()
    except Exception:
        pass

    contexts.sort(
        key=lambda x: (
            x.get("category", ""),
            x.get("doc_type", ""),
            x.get("updated_at", ""),
            x.get("source", ""),
            x.get("chunk_index", 0),
        )
    )

    return contexts


def build_context_text(contexts: list[dict]) -> str:
    grouped = defaultdict(list)

    for ctx in contexts:
        key = f"{ctx.get('category', '')} / {ctx.get('doc_type', '')}"
        grouped[key].append(ctx)

    lines = []

    for group_name, items in grouped.items():
        lines.append(f"\n## {group_name}\n")

        for i, ctx in enumerate(items, start=1):
            lines.append(f"### records {i}")
            lines.append(f"- title:{ctx.get('title', '')}")
            lines.append(f"- file:{ctx.get('file_name', '')}")
            lines.append(f"- source:{ctx.get('source', '')}")
            lines.append(f"- updated at:{ctx.get('updated_at', '')}")
            lines.append(f"- tags:{ctx.get('tags', [])}")
            lines.append("")
            lines.append(ctx.get("text", ""))
            lines.append("")

    return "\n".join(lines)


def generate_report(project: str, contexts: list[dict]) -> str:
    if not contexts:
        return f"# {project} project status report\n\n knowledge basein hasretrievedthis purposerecords. "

    context_text = build_context_text(contexts)

    prompt = f"""
 is Personal Project SecretaryandKnowledge Base . 

please knowledge base records, as , canexecute project status report. 

[project name]
{project}

[knowledge base records]
{context_text}

[report requirements]
pleaseUse English Markdown output,  below :

# {project} project status report

## 1. current overall status
description stage. 

## 2. alreadycompletedcontent
 listalready completedcontent. 

## 3.  
description model,  , script, knowledge base etc. . 

## 4. already toissues and resolution status
listalready recordissue, reasonandsolution. 

## 5. important decisions
list inalready decision. 

## 6. current risksand items
identifylatercancan issue. 

## 7. next-step recommendations
provide , actionable next stepstasks. 

 :
1. only answer based on records, do not fabricate information. 
2. if insufficient records, please 'insufficient records, no '. 
3. content saveas stagereport. 
"""

    resp = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": CHAT_MODEL,
            "prompt": prompt,
            "stream": False,
        },
        timeout=600,
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("response", "")


def save_report(project: str, report: str, contexts: list[dict]) -> str:
    PROJECT_REPORT_DIR.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
    file_path = PROJECT_REPORT_DIR / f"{timestamp}_{project}_project_report.md"

    sources = sorted({ctx.get("source", "") for ctx in contexts if ctx.get("source", "")})

    lines = []
    lines.append("---")
    lines.append(f"title: {project} project status report {timestamp}")
    lines.append(f"created: {now.isoformat(timespec='seconds')}")
    lines.append("category: summary")
    lines.append(f"project: {project}")
    lines.append("doc_type: project_report")
    lines.append("tags: [project report, RAG, auto generated]")
    lines.append("---")
    lines.append("")
    lines.append(report)
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("##  report knowledge basesource")
    lines.append("")

    if not sources:
        lines.append("No source recorded. ")
    else:
        for source in sources:
            lines.append(f"- {source}")

    lines.append("")

    file_path.write_text("\n".join(lines), encoding="utf-8")
    return str(file_path)


def main():
    parser = argparse.ArgumentParser(
        description="Personal Project Secretary + Knowledge Base: project status report"
    )

    parser.add_argument(
        "--project",
        required=True,
        help="project name, for example Demo_Project",
    )

    parser.add_argument(
        "--max-points",
        type=int,
        default=80,
        help=" read chunk",
    )

    parser.add_argument(
        "--max-chars",
        type=int,
        default=18000,
        help=" model",
    )

    args = parser.parse_args()

    print(f"runningreadproject records:{args.project}")

    contexts = load_project_context(
        project=args.project,
        max_points=args.max_points,
        max_chars=args.max_chars,
    )

    print(f"loaded chunk count:{len(contexts)}")

    if not contexts:
        print("No project records were loaded, so the report content may be insufficient. ")

    print("running project status report...")
    report = generate_report(args.project, contexts)

    file_path = save_report(args.project, report, contexts)

    print("")
    print("project reportalready :")
    print(file_path)
    print("")
    print("recommended next command:")
    print("python update_index.py")


if __name__ == "__main__":
    main()