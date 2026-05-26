import argparse
import os
import re
import requests
import sys
from datetime import datetime
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

import config


# ============================================================
# base configuration
# ============================================================

OLLAMA_URL = config.OLLAMA_URL
CHAT_MODEL = config.CHAT_MODEL
QDRANT_URL = config.QDRANT_URL
COLLECTION_NAME = config.COLLECTION_NAME
KNOWLEDGE_ROOT = config.KNOWLEDGE_ROOT

PROJECT_BRIEF_DIR = getattr(
    config,
    "PROJECT_BRIEF_DIR",
    KNOWLEDGE_ROOT / "05_Summaries" / "project_briefs",
)


# ============================================================
# Windows / PowerShell English output 
# ============================================================

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


# ============================================================
# Prevent local service requests from going through system proxies.
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


DEFAULT_DOC_TYPES = [
    "readme",
    "project_overview",
    "progress_log",
    "next_steps",
    "issues",
    "issue",
    "decisions",
    "decision",
    "project_report",
    "weekly_report",
    "next_action_report",
]

def clean_model_response(text: str) -> str:
    """
    cleanup qwen3 cancan  <think>...</think> content. 
    """
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    return text.strip()


def get_qdrant_client() -> QdrantClient:
    """
    create Qdrant  . 
    """
    return QdrantClient(
        url=QDRANT_URL,
        check_compatibility=False,
        timeout=60,
    )


def build_project_filter(project: str):
    """
    Qdrant   project filter. 
    doc_type laterin Python infilter,   qdrant-client  . 
    """
    return Filter(
        must=[
            FieldCondition(
                key="project",
                match=MatchValue(value=project),
            )
        ]
    )


def parse_doc_types(raw_doc_types: list[str] | None) -> list[str]:
    """
    parsecommand  doc_type. 
     :
    --doc-type progress_log
    --doc-type progress_log,next_steps
    --doc-type progress_log --doc-type weekly_report
    """
    if not raw_doc_types:
        return DEFAULT_DOC_TYPES

    result = []

    for item in raw_doc_types:
        parts = [part.strip() for part in item.split(",") if part.strip()]
        result.extend(parts)

    return sorted(set(result))


def safe_text_preview(text: str, max_chars: int = 240) -> str:
    """
     preview . 
    """
    text = text.replace("\n", " ").strip()

    if len(text) <= max_chars:
        return text

    return text[:max_chars] + "..."


def load_project_contexts(
    project: str,
    doc_types: list[str],
    max_points: int = 140,
    max_chars: int = 26000,
) -> list[dict]:
    """
    from Qdrant inreadspecifiedproject records. 

    project_brief.py notis question answeringretrieval, insteadproject status , 
    sothisin  scroll read records, then  doc_type  . 
    """
    client = get_qdrant_client()

    if not client.collection_exists(COLLECTION_NAME):
        raise RuntimeError(
            f"collection does not exist:{COLLECTION_NAME}, please first  python update_index.py"
        )

    scroll_filter = build_project_filter(project)

    contexts = []
    offset = None
    total_chars = 0

    while True:
        points, offset = client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=scroll_filter,
            limit=80,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )

        if not points:
            break

        for point in points:
            payload = point.payload or {}

            doc_type = payload.get("doc_type", "")
            text = payload.get("text", "")

            if doc_type not in doc_types:
                continue

            if not text:
                continue

            item = {
                "category": payload.get("category", ""),
                "project": payload.get("project", ""),
                "doc_type": doc_type,
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
            x.get("updated_at", ""),
            x.get("doc_type", ""),
            x.get("source", ""),
            str(x.get("chunk_index", "")),
        ),
        reverse=True,
    )

    return contexts


def build_context_text(contexts: list[dict]) -> str:
    """
    project records modelcan . 
    """
    lines = []

    for index, ctx in enumerate(contexts, start=1):
        lines.append(f"## records {index}")
        lines.append("")
        lines.append(f"- record category:{ctx.get('category', '')}")
        lines.append(f"-  :{ctx.get('project', '')}")
        lines.append(f"- document type:{ctx.get('doc_type', '')}")
        lines.append(f"- title:{ctx.get('title', '')}")
        lines.append(f"- tags:{ctx.get('tags', [])}")
        lines.append(f"- file:{ctx.get('file_name', '')}")
        lines.append(f"- source:{ctx.get('source', '')}")
        lines.append(f"- chunk:{ctx.get('chunk_index', '')}")
        lines.append(f"- updated at:{ctx.get('updated_at', '')}")
        lines.append("")
        lines.append(ctx.get("text", ""))
        lines.append("")

    return "\n".join(lines)


def build_source_summary(contexts: list[dict]) -> list[str]:
    """
     source list. 
    """
    sources = []

    for ctx in contexts:
        source = ctx.get("source", "")
        doc_type = ctx.get("doc_type", "")
        updated_at = ctx.get("updated_at", "")

        if not source:
            continue

        item = f"{doc_type} | {source} | {updated_at}"
        sources.append(item)

    return sorted(set(sources))


def generate_project_brief(project: str, contexts: list[dict]) -> str:
    """
    call qwen3:8b  project brief. 
    """
    if not contexts:
        lines = [
            f"# {project} project brief",
            "",
            "Loaded project records are incomplete. ",
            "",
            "recommended additions:",
            "",
            "1. project_overview.md",
            "2. progress_log.md",
            "3. issues.md",
            "4. next_steps.md",
            "5. project_report or weekly_report",
            "",
        ]
        return "\n".join(lines)

    context_text = build_context_text(contexts)

    prompt_lines = [
        " is Personal Project Secretaryand . ",
        "",
        "please project records,  ,  ,  viewproject brief. ",
        "",
        "[project name]",
        project,
        "",
        "[project records]",
        context_text,
        "",
        "[ ]",
        "Use English Markdown output. ",
        "",
        f"# {project} project brief",
        "",
        "## 1.  ",
        " description . ",
        "",
        "## 2. current status",
        "  3 to 6  stage, already capabilityand . ",
        "",
        "## 3. recent ",
        "listrecentalready completedor items. ",
        "",
        "## 4. current issues",
        "list existsissue, risksor items. ",
        "ifrecordsin has issue, please 'recordsinnot found issue'. ",
        "",
        "## 5. next actions",
        "list recommendations  3 to 8  next actions. ",
        " canexecute. ",
        "",
        "## 6. risk reminders",
        "listlatercancan risks. ",
        "",
        "## 7. recommended records to add",
        "identifyas knowledge base complete,  this record. ",
        "",
        " :",
        "1. only answer based on records, do not fabricate information. ",
        "2. if insufficient records, please 'insufficient records, no '. ",
        "3. do not output reasoning process. ",
        "4. not  <think> tags. ",
        "5.  project report,  quicklyview. ",
    ]

    prompt = "\n".join(prompt_lines)

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
    return clean_model_response(data.get("response", ""))


def save_project_brief(
    project: str,
    brief: str,
    contexts: list[dict],
    doc_types: list[str],
) -> Path:
    """
    saveproject briefas Markdown,  laterre- . 
    """
    PROJECT_BRIEF_DIR.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")

    file_path = PROJECT_BRIEF_DIR / f"{timestamp}_{project}_project_brief.md"

    sources = build_source_summary(contexts)
    doc_type_text = "[" + ", ".join(doc_types) + "]"

    lines = []

    lines.append("---")
    lines.append(f"title: {project} project brief {timestamp}")
    lines.append(f"created: {now.isoformat(timespec='seconds')}")
    lines.append("category: summary")
    lines.append(f"project: {project}")
    lines.append("doc_type: project_brief")
    lines.append("tags: [project brief, M2.2, auto generated, personal secretary]")
    lines.append(f"source_doc_types: {doc_type_text}")
    lines.append("---")
    lines.append("")
    lines.append(brief)
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("##  project brief knowledge basesource")
    lines.append("")

    if not sources:
        lines.append("No source recorded. ")
    else:
        for source in sources:
            lines.append(f"- {source}")

    lines.append("")

    file_path.write_text("\n".join(lines), encoding="utf-8")
    return file_path


def main():
    parser = argparse.ArgumentParser(
        description="Personal Project Secretary + Knowledge Base: project brief"
    )

    parser.add_argument(
        "--project",
        required=True,
        help="project name, for example Personal_Project_Assistant",
    )

    parser.add_argument(
        "--doc-type",
        action="append",
        default=None,
        help=(
            "specified and document type. "
            "canduplicate ,  can . "
            "default project overview,  , issue, next steps, project report, weekly report,  etc.. "
        ),
    )

    parser.add_argument(
        "--max-points",
        type=int,
        default=140,
        help=" read chunk. ",
    )

    parser.add_argument(
        "--max-chars",
        type=int,
        default=26000,
        help=" model. ",
    )

    parser.add_argument(
        "--no-save",
        action="store_true",
        help="onlyin , notsave Markdown file. ",
    )

    args = parser.parse_args()

    doc_types = parse_doc_types(args.doc_type)

    print("Personal Project Secretary + Knowledge Base:project brief ")
    print(f" :{args.project}")
    print(f"goaldocument type:{doc_types}")
    print(f" chunk :{args.max_points}")
    print(f" :{args.max_chars}")

    contexts = load_project_contexts(
        project=args.project,
        doc_types=doc_types,
        max_points=args.max_points,
        max_chars=args.max_chars,
    )

    print(f"candidate record chunk count:{len(contexts)}")

    if contexts:
        print("")
        print("candidaterecordspreview:")

        for index, ctx in enumerate(contexts[:8], start=1):
            print(
                f"{index}. "
                f"{ctx.get('doc_type', '')} | "
                f"{ctx.get('file_name', '')} | "
                f"{ctx.get('updated_at', '')}"
            )
            print(f"   source:{ctx.get('source', '')}")
            print(f"   content:{safe_text_preview(ctx.get('text', ''), 120)}")

    print("")
    print("running project brief...")

    brief = generate_project_brief(
        project=args.project,
        contexts=contexts,
    )

    print("")
    print("=" * 80)
    print("project brief")
    print("=" * 80)
    print(brief)

    if args.no_save:
        print("")
        print("already  --no-save,  save Markdown file. ")
        return

    file_path = save_project_brief(
        project=args.project,
        brief=brief,
        contexts=contexts,
        doc_types=doc_types,
    )

    print("")
    print("project briefalreadysave:")
    print(file_path)
    print("")
    print("recommended next command:")
    print("python update_index.py")
    print(
        'python ask.py --doc-type project_brief '
        '" project briefsummary ？"'
    )


if __name__ == "__main__":
    main()
