import argparse
import os
import requests
from datetime import datetime, timedelta

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

from config import (
    OLLAMA_URL,
    CHAT_MODEL,
    QDRANT_URL,
    COLLECTION_NAME,
    TIME_REPORT_DIR,
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


def get_time_range(mode: str) -> tuple[datetime, datetime]:
    now = datetime.now()

    if mode == "daily":
        start = datetime(now.year, now.month, now.day)
        end = now
        return start, end

    if mode == "weekly":
        start = now - timedelta(days=7)
        end = now
        return start, end

    raise ValueError("mode only  daily or weekly")


def build_filter(project: str):
    """
    Qdrant thisinonly  project filter. 
    time rangein Python in  updated_at thendetermine,   Range onlycan issue. 
    """
    return Filter(
        must=[
            FieldCondition(
                key="project",
                match=MatchValue(value=project),
            )
        ]
    )

def parse_datetime(value: str) -> datetime | None:
    """
    parse ISO time . 
    for example:2026-05-17T20:34:04
    """
    if not value:
        return None

    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def is_in_time_range(updated_at: str, start: datetime, end: datetime) -> bool:
    """
    determine updated_at whetherindaily report/weekly reporttime range . 
    """
    dt = parse_datetime(updated_at)

    if dt is None:
        return False

    return start <= dt <= end


def load_context(project: str, mode: str, max_points: int = 100, max_chars: int = 22000) -> list[dict]:
    start, end = get_time_range(mode)

    client = QdrantClient(
        url=QDRANT_URL,
        check_compatibility=False,
        timeout=60,
    )

    if not client.collection_exists(COLLECTION_NAME):
        raise RuntimeError(f"collection does not exist:{COLLECTION_NAME}, please first  python update_index.py")

    scroll_filter = build_filter(project=project)

    contexts = []
    offset = None
    total_chars = 0

    while True:
        points, offset = client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=scroll_filter,
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
			
            updated_at = payload.get("updated_at", "")

            if not is_in_time_range(updated_at, start, end):
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
                "updated_at": updated_at,
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
            x.get("updated_at", ""),
            x.get("category", ""),
            x.get("doc_type", ""),
            x.get("source", ""),
            x.get("chunk_index", 0),
        )
    )

    return contexts


def build_context_text(contexts: list[dict]) -> str:
    lines = []

    for i, ctx in enumerate(contexts, start=1):
        lines.append(f"## records {i}")
        lines.append(f"- record category:{ctx.get('category', '')}")
        lines.append(f"-  :{ctx.get('project', '')}")
        lines.append(f"- document type:{ctx.get('doc_type', '')}")
        lines.append(f"- title:{ctx.get('title', '')}")
        lines.append(f"- tags:{ctx.get('tags', [])}")
        lines.append(f"- file:{ctx.get('file_name', '')}")
        lines.append(f"- source:{ctx.get('source', '')}")
        lines.append(f"- updated at:{ctx.get('updated_at', '')}")
        lines.append("")
        lines.append(ctx.get("text", ""))
        lines.append("")

    return "\n".join(lines)


def generate_time_report(project: str, mode: str, contexts: list[dict]) -> str:
    now = datetime.now()
    start, end = get_time_range(mode)

    if mode == "daily":
        title = f"{project} daily report"
        report_sections = """
## 1. today 
## 2. todaycompletedcontent
## 3. todayaddrecords
## 4. today toissue
## 5. todayimportant decisions
## 6. tomorrowrecommendations
"""
    else:
        title = f"{project} weekly report"
        report_sections = """
## 1. this week 
## 2. this weekcompletedcontent
## 3. this weekaddrecords
## 4. this week toissues and resolution status
## 5. this weekimportant decisions
## 6. current risks
## 7.  recommendations
"""

    context_text = build_context_text(contexts)

    if not contexts:
        context_text = "No relevant records were found in the current time range."

    prompt = f"""
 is Personal Project SecretaryandKnowledge Base . 

please knowledge base records timereport. 

[project name]
{project}

[report type]
{mode}

[time range]
{start.isoformat(timespec="seconds")} to {end.isoformat(timespec="seconds")}

[knowledge base records]
{context_text}

[ ]
pleaseUse English Markdown output. 

# {title}

{report_sections}

 :
1. only answer based on records, do not fabricate information. 
2. if insufficient records, please 'insufficient records, no '. 
3.  save to knowledge base. 
4. do not output reasoning process, not  <think> tags. 
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
    return data.get("response", "").replace("<think>", "").replace("</think>", "").strip()


def save_time_report(project: str, mode: str, report: str, contexts: list[dict]) -> str:
    TIME_REPORT_DIR.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")

    if mode == "daily":
        doc_type = "daily_report"
        tag_name = "daily report"
    else:
        doc_type = "weekly_report"
        tag_name = "weekly report"

    file_path = TIME_REPORT_DIR / f"{timestamp}_{project}_{doc_type}.md"

    sources = sorted({ctx.get("source", "") for ctx in contexts if ctx.get("source", "")})

    lines = []
    lines.append("---")
    lines.append(f"title: {project} {tag_name} {timestamp}")
    lines.append(f"created: {now.isoformat(timespec='seconds')}")
    lines.append("category: summary")
    lines.append(f"project: {project}")
    lines.append(f"doc_type: {doc_type}")
    lines.append(f"tags: [{tag_name}, project report, RAG, auto generated]")
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
        description="Personal Project Secretary + Knowledge Base: daily report / weekly report"
    )

    parser.add_argument(
        "--project",
        required=True,
        help="project name, for example Demo_Project",
    )

    parser.add_argument(
        "--mode",
        required=True,
        choices=["daily", "weekly"],
        help="report type:daily or weekly",
    )

    parser.add_argument(
        "--max-points",
        type=int,
        default=100,
        help=" read chunk",
    )

    parser.add_argument(
        "--max-chars",
        type=int,
        default=22000,
        help=" model",
    )

    args = parser.parse_args()

    print(f"running  {args.mode} report")
    print(f" :{args.project}")

    contexts = load_context(
        project=args.project,
        mode=args.mode,
        max_points=args.max_points,
        max_chars=args.max_chars,
    )

    print(f"loaded chunk count:{len(contexts)}")

    report = generate_time_report(
        project=args.project,
        mode=args.mode,
        contexts=contexts,
    )

    file_path = save_time_report(
        project=args.project,
        mode=args.mode,
        report=report,
        contexts=contexts,
    )

    print("")
    print("timereportalready :")
    print(file_path)
    print("")
    print("recommended next command:")
    print("python update_index.py")


if __name__ == "__main__":
    main()