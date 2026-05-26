import argparse
import os
import re
import requests
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from qdrant_client import QdrantClient

import config


# ============================================================
# base configuration
# ============================================================

OLLAMA_URL = config.OLLAMA_URL
CHAT_MODEL = config.CHAT_MODEL
QDRANT_URL = config.QDRANT_URL
COLLECTION_NAME = config.COLLECTION_NAME
KNOWLEDGE_ROOT = config.KNOWLEDGE_ROOT

MULTI_PROJECT_STATUS_DIR = getattr(
    config,
    "MULTI_PROJECT_STATUS_DIR",
    KNOWLEDGE_ROOT / "05_Summaries" / "multi_project_status",
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
    "project_brief",
    "next_action_report",
    "project_report",
    "weekly_report",
    "progress_log",
    "next_steps",
    "issues",
    "issue",
    "decisions",
    "decision",
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


def parse_csv_values(raw_values: list[str] | None) -> list[str]:
    """
    parsecommand incanduplicate, can . 
    for example:
    --project A --project B
    --project A,B
    """
    if not raw_values:
        return []

    result = []

    for item in raw_values:
        parts = [part.strip() for part in item.split(",") if part.strip()]
        result.extend(parts)

    return sorted(set(result))


def parse_doc_types(raw_doc_types: list[str] | None) -> list[str]:
    """
    parse andmulti-project  doc_type. 
    """
    parsed = parse_csv_values(raw_doc_types)

    if not parsed:
        return DEFAULT_DOC_TYPES

    return parsed


def safe_text_preview(text: str, max_chars: int = 160) -> str:
    """
     preview . 
    """
    text = text.replace("\n", " ").strip()

    if len(text) <= max_chars:
        return text

    return text[:max_chars] + "..."


def load_all_project_contexts(
    include_projects: list[str],
    exclude_projects: list[str],
    doc_types: list[str],
    max_points: int = 500,
) -> dict[str, list[dict]]:
    """
    from Qdrant inreadproject records, and  project  . 

    rules:
    1. if include_projects notis empty, only this . 
    2. exclude_projects in . 
    3. onlyreadspecified doc_type chunk. 
    """
    client = get_qdrant_client()

    if not client.collection_exists(COLLECTION_NAME):
        raise RuntimeError(
            f"collection does not exist:{COLLECTION_NAME}, please first  python update_index.py"
        )

    grouped = defaultdict(list)
    offset = None
    total_seen = 0

    while True:
        points, offset = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=200,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )

        if not points:
            break

        for point in points:
            payload = point.payload or {}

            project = payload.get("project", "")
            doc_type = payload.get("doc_type", "")
            text = payload.get("text", "")

            if not project:
                continue

            if include_projects and project not in include_projects:
                continue

            if exclude_projects and project in exclude_projects:
                continue

            if doc_type not in doc_types:
                continue

            if not text:
                continue

            item = {
                "category": payload.get("category", ""),
                "project": project,
                "doc_type": doc_type,
                "title": payload.get("title", ""),
                "tags": payload.get("tags", []),
                "file_name": payload.get("file_name", ""),
                "source": payload.get("source", ""),
                "chunk_index": payload.get("chunk_index", ""),
                "updated_at": payload.get("updated_at", ""),
                "text": text,
            }

            grouped[project].append(item)
            total_seen += 1

            if total_seen >= max_points:
                break

        if offset is None:
            break

        if total_seen >= max_points:
            break

    try:
        client.close()
    except Exception:
        pass

    for project, items in grouped.items():
        items.sort(
            key=lambda x: (
                x.get("updated_at", ""),
                x.get("doc_type", ""),
                x.get("source", ""),
                str(x.get("chunk_index", "")),
            ),
            reverse=True,
        )

    return dict(grouped)


def trim_project_contexts(
    grouped_contexts: dict[str, list[dict]],
    max_projects: int,
    max_items_per_project: int,
    max_chars_per_project: int,
) -> dict[str, list[dict]]:
    """
     model ,   prompt  . 

    sortrules:
    1.  each recentupdated at . 
    2. each  max_items_per_project  . 
    3. each  max_chars_per_project  . 
    """
    project_latest = []

    for project, items in grouped_contexts.items():
        latest = ""
        for item in items:
            updated_at = item.get("updated_at", "")
            if updated_at > latest:
                latest = updated_at
        project_latest.append((project, latest))

    project_latest.sort(key=lambda x: x[1], reverse=True)

    selected_projects = [project for project, _ in project_latest[:max_projects]]

    trimmed = {}

    for project in selected_projects:
        items = grouped_contexts.get(project, [])
        selected_items = []
        total_chars = 0

        for item in items[:max_items_per_project]:
            text = item.get("text", "")
            selected_items.append(item)
            total_chars += len(text)

            if total_chars >= max_chars_per_project:
                break

        trimmed[project] = selected_items

    return trimmed


def build_context_text(grouped_contexts: dict[str, list[dict]]) -> str:
    """
    buildmulti-project . 
    """
    lines = []

    for project, items in grouped_contexts.items():
        lines.append(f"#  :{project}")
        lines.append("")

        for index, ctx in enumerate(items, start=1):
            lines.append(f"## records {index}")
            lines.append("")
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

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def build_source_summary(grouped_contexts: dict[str, list[dict]]) -> list[str]:
    """
     source list. 
    """
    sources = []

    for project, items in grouped_contexts.items():
        for ctx in items:
            source = ctx.get("source", "")
            doc_type = ctx.get("doc_type", "")
            updated_at = ctx.get("updated_at", "")

            if not source:
                continue

            sources.append(f"{project} | {doc_type} | {source} | {updated_at}")

    return sorted(set(sources))


def build_project_overview_for_terminal(grouped_contexts: dict[str, list[dict]]) -> None:
    """
    in in candidate andrecords . 
    """
    print("")
    print("candidate project records :")

    for project, items in grouped_contexts.items():
        latest = ""
        doc_type_count = defaultdict(int)

        for item in items:
            doc_type_count[item.get("doc_type", "")] += 1
            updated_at = item.get("updated_at", "")
            if updated_at > latest:
                latest = updated_at

        print("")
        print(f"-  :{project}")
        print(f"  chunk count:{len(items)}")
        print(f"  recentupdated at:{latest}")
        print(f"  document type statistics:{dict(doc_type_count)}")

        for index, item in enumerate(items[:3], start=1):
            print(
                f"  {index}. {item.get('doc_type', '')} | "
                f"{item.get('file_name', '')} | "
                f"{item.get('updated_at', '')}"
            )
            print(f"     {safe_text_preview(item.get('text', ''), 120)}")


def generate_multi_project_status(grouped_contexts: dict[str, list[dict]]) -> str:
    """
    call qwen3:8b  project status . 
    """
    if not grouped_contexts:
        lines = [
            "# multi-project status summary",
            "",
            "Loaded project records are available for analysis. ",
            "",
            "recommendations:",
            "",
            "1. firstas  progress_log, next_steps, project_brief or weekly_report. ",
            "2. execute python update_index.py  re- script. ",
            "",
        ]
        return "\n".join(lines)

    context_text = build_context_text(grouped_contexts)

    prompt_lines = [
        " is Personal Project Secretaryandmulti-project . ",
        "",
        "please knowledge base records,  multi-project status summary. ",
        "",
        "[knowledge base records]",
        context_text,
        "",
        "[ ]",
        "Use English Markdown output. ",
        "",
        "# multi-project status summary",
        "",
        "## 1.  ",
        "  3 to 6  multiple projects . ",
        "",
        "## 2. project status ",
        "please ,  :",
        "",
        "|   | current status | recent  | current issues/risks | next-step recommendations |",
        "| --- | --- | --- | --- | --- |",
        "",
        " :",
        "1. each . ",
        "2. current status . ",
        "3. current issues/risksif insufficient records, please 'insufficient records, no '. ",
        "4. next-step recommendations canexecute. ",
        "",
        "## 3. recent ",
        "listrecentrecords or . ",
        "",
        "## 4. cancan ",
        "listrecords , long-term has next stepsormissingrecent . ",
        "",
        "## 5.  issue",
        "summarymultiple projectsinduplicate issue, risksormaintenance . ",
        "",
        "## 6. this weekrecommendations items",
        "providethis weekrecommended to prioritize anditems. ",
        "",
        " :",
        "1. only answer based on records, do not fabricate information. ",
        "2. do not output reasoning process. ",
        "3. not  <think> tags. ",
        "4. if insufficient records, please state insufficient records. ",
    ]

    prompt = "\n".join(prompt_lines)

    resp = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": CHAT_MODEL,
            "prompt": prompt,
            "stream": False,
        },
        timeout=900,
    )
    resp.raise_for_status()

    data = resp.json()
    return clean_model_response(data.get("response", ""))


def save_multi_project_status(
    report: str,
    grouped_contexts: dict[str, list[dict]],
    doc_types: list[str],
) -> Path:
    """
    savemulti-project status summaryas Markdown. 
    """
    MULTI_PROJECT_STATUS_DIR.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")

    file_path = MULTI_PROJECT_STATUS_DIR / f"{timestamp}_multi_project_status.md"

    project_names = sorted(grouped_contexts.keys())
    project_text = "[" + ", ".join(project_names) + "]"
    doc_type_text = "[" + ", ".join(doc_types) + "]"
    sources = build_source_summary(grouped_contexts)

    lines = []

    lines.append("---")
    lines.append(f"title: multi-project status summary {timestamp}")
    lines.append(f"created: {now.isoformat(timespec='seconds')}")
    lines.append("category: summary")
    lines.append("project: Personal_Project_Assistant")
    lines.append("doc_type: multi_project_status")
    lines.append("tags: [multi-project , M2.3, auto generated, personal secretary]")
    lines.append(f"projects: {project_text}")
    lines.append(f"source_doc_types: {doc_type_text}")
    lines.append("---")
    lines.append("")
    lines.append(report)
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("##  multi-project knowledge basesource")
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
        description="Personal Project Secretary + Knowledge Base:multi-project status summary"
    )

    parser.add_argument(
        "--project",
        action="append",
        default=None,
        help="specified . canduplicate ,  can . notspecified all . ",
    )

    parser.add_argument(
        "--exclude-project",
        action="append",
        default=None,
        help=" specified . canduplicate ,  can . ",
    )

    parser.add_argument(
        "--doc-type",
        action="append",
        default=None,
        help="specified and document type. canduplicate ,  can . ",
    )

    parser.add_argument(
        "--max-projects",
        type=int,
        default=12,
        help=" . ",
    )

    parser.add_argument(
        "--max-items-per-project",
        type=int,
        default=18,
        help="each read chunk. ",
    )

    parser.add_argument(
        "--max-chars-per-project",
        type=int,
        default=10000,
        help="each model. ",
    )

    parser.add_argument(
        "--max-points",
        type=int,
        default=800,
        help="from Qdrant  candidate chunk. ",
    )

    parser.add_argument(
        "--no-save",
        action="store_true",
        help="onlyin , notsave Markdown file. ",
    )

    args = parser.parse_args()

    include_projects = parse_csv_values(args.project)
    exclude_projects = parse_csv_values(args.exclude_project)
    doc_types = parse_doc_types(args.doc_type)

    print("Personal Project Secretary + Knowledge Base:multi-project status summary")
    print(f"specified :{include_projects if include_projects else ' '}")
    print(f" :{exclude_projects if exclude_projects else 'no'}")
    print(f"goaldocument type:{doc_types}")
    print(f" multi-project :{args.max_projects}")
    print(f" chunk :{args.max_items_per_project}")
    print(f" :{args.max_chars_per_project}")

    grouped = load_all_project_contexts(
        include_projects=include_projects,
        exclude_projects=exclude_projects,
        doc_types=doc_types,
        max_points=args.max_points,
    )

    trimmed = trim_project_contexts(
        grouped_contexts=grouped,
        max_projects=args.max_projects,
        max_items_per_project=args.max_items_per_project,
        max_chars_per_project=args.max_chars_per_project,
    )

    print("")
    print(f"loaded record count:{len(trimmed)}")

    build_project_overview_for_terminal(trimmed)

    print("")
    print("running multi-project status summary...")

    report = generate_multi_project_status(trimmed)

    print("")
    print("=" * 80)
    print("multi-project status summary")
    print("=" * 80)
    print(report)

    if args.no_save:
        print("")
        print("already  --no-save,  save Markdown file. ")
        return

    file_path = save_multi_project_status(
        report=report,
        grouped_contexts=trimmed,
        doc_types=doc_types,
    )

    print("")
    print("multi-project status summaryalreadysave:")
    print(file_path)
    print("")
    print("recommended next command:")
    print("python update_index.py")
    print(
        'python ask.py --doc-type multi_project_status '
        '" project status ？"'
    )


if __name__ == "__main__":
    main()
