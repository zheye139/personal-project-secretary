import argparse
import os
import re
import requests
import sys
from collections import defaultdict
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

REVIEW_REPORT_DIR = getattr(
    config,
    "REVIEW_REPORT_DIR",
    KNOWLEDGE_ROOT / "05_Summaries" / "review_reports",
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
    "technical_notes",
    "project_report",
    "weekly_report",
    "project_brief",
    "next_action_report",
    "priority_advice",
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
    """
    return Filter(
        must=[
            FieldCondition(
                key="project",
                match=MatchValue(value=project),
            )
        ]
    )


def parse_csv_values(raw_values: list[str] | None) -> list[str]:
    """
    parsecanduplicate, can command . 
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
    parse and  doc_type. 
    """
    parsed = parse_csv_values(raw_doc_types)

    if not parsed:
        return DEFAULT_DOC_TYPES

    return parsed


def safe_text_preview(text: str, max_chars: int = 180) -> str:
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
    max_points: int = 180,
    max_chars: int = 30000,
) -> list[dict]:
    """
    from Qdrant inreadspecifiedproject records. 

    review_assistant.py  'recordscomplete and risks', 
    so read project records. 
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
            limit=100,
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


def summarize_doc_type_counts(contexts: list[dict]) -> dict[str, int]:
    """
    statistics  doc_type. 
    """
    counts = defaultdict(int)

    for ctx in contexts:
        counts[ctx.get("doc_type", "")] += 1

    return dict(counts)


def get_latest_updated_at(contexts: list[dict]) -> str:
    """
     recordsinrecentupdated at. 
    """
    latest = ""

    for ctx in contexts:
        updated_at = ctx.get("updated_at", "")
        if updated_at > latest:
            latest = updated_at

    return latest


def local_rule_review(project: str, contexts: list[dict]) -> list[str]:
    """
    not modelbasicrulescheck. 

     :
    1. checkwhethermissing document type. 
    2. checkwhetherlong-term has next_steps. 
    3. checkwhether has issue recordordecision record. 
    """
    issues = []
    counts = summarize_doc_type_counts(contexts)

    required_doc_types = [
        "project_overview",
        "progress_log",
        "next_steps",
        "issues",
        "decisions",
    ]

    for doc_type in required_doc_types:
        if counts.get(doc_type, 0) == 0:
            issues.append(f"cancanmissing document type:{doc_type}")

    if counts.get("project_brief", 0) == 0:
        issues.append(" not found project_brief, recommendationsfirst project brief. ")

    if counts.get("next_action_report", 0) == 0:
        issues.append(" not found next_action_report, recommendationsfirst next action list. ")

    if counts.get("weekly_report", 0) == 0:
        issues.append(" not found weekly_report, recommendationsregularly weekly report. ")

    if counts.get("issues", 0) == 0 and counts.get("issue", 0) == 0:
        issues.append("not found issue record, cancannot later . ")

    if counts.get("decisions", 0) == 0 and counts.get("decision", 0) == 0:
        issues.append("not found decision record, recommendationsrecord reason. ")

    if not contexts:
        issues.append(f"  {project} Loaded records are available. ")

    return issues


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

        sources.append(f"{doc_type} | {source} | {updated_at}")

    return sorted(set(sources))


def build_local_review_text(project: str, contexts: list[dict]) -> str:
    """
     rulescheck results as Markdown. 
    """
    counts = summarize_doc_type_counts(contexts)
    local_issues = local_rule_review(project, contexts)
    latest = get_latest_updated_at(contexts)

    lines = []
    lines.append("##  rulescheck ")
    lines.append("")
    lines.append(f"-  :{project}")
    lines.append(f"- candidate chunk count:{len(contexts)}")
    lines.append(f"- recentupdated at:{latest if latest else ' '}")
    lines.append(f"- document type statistics:{counts}")
    lines.append("")

    if local_issues:
        lines.append("### rulesfoundissue")
        lines.append("")
        for issue in local_issues:
            lines.append(f"- {issue}")
    else:
        lines.append("not found rulesissue. ")

    lines.append("")

    return "\n".join(lines)


def generate_review_report(
    project: str,
    contexts: list[dict],
    local_review: str,
) -> str:
    """
    call qwen3:8b  project records report. 
    """
    if not contexts:
        lines = [
            f"# {project} project records report",
            "",
            "Loaded project records are available for analysis. ",
            "",
            local_review,
            "",
            "recommendations:",
            "",
            "1.   project_overview.md. ",
            "2.   progress_log.md. ",
            "3.   issues.md. ",
            "4.   decisions.md. ",
            "5.   next_steps.md. ",
            "6. execute python update_index.py  re- script. ",
            "",
        ]
        return "\n".join(lines)

    context_text = build_context_text(contexts)

    prompt_lines = [
        " is Personal Project Secretaryand . ",
        "",
        "please project recordsand rulescheck results, forproject records . ",
        "",
        " notisre-summary , insteadcheck:",
        "1. recordwhether complete. ",
        "2. whetherexists . ",
        "3. whetherexistsrisks. ",
        "4. whetherhas issue record missingresolve . ",
        "5. whetherhas record missingnext steps. ",
        "6. whetherhas decision missing . ",
        "7. whether document. ",
        "",
        "[project name]",
        project,
        "",
        "[ rulescheck results]",
        local_review,
        "",
        "[project records]",
        context_text,
        "",
        "[ ]",
        "Use English Markdown output. ",
        "",
        f"# {project} project records report",
        "",
        "## 1.  ",
        "  3 to 6  describe project records whether complete,  issueis . ",
        "",
        "## 2. recordcomplete check",
        "check project overview,  , issue, decision, next steps, report,  whether . ",
        "",
        "## 3. found ",
        "list project recordsin or content. ",
        "",
        "## 4. risks and hidden issues",
        "identifycancan , maintenance,  ,  risks. ",
        "",
        "## 5. recommended records to add",
        "please ,  :",
        "",
        "|   | recommended additionscontent | reason | recommendationssave /document type | priority |",
        "| --- | --- | --- | --- | --- |",
        "",
        "## 6. recommendationsimmediate issue",
        "list this recordissue. ",
        "",
        "## 7. later recommendations",
        "description this maintenancethis project records. ",
        "",
        " :",
        "1. only answer based on records, do not fabricate information. ",
        "2. if insufficient records, please 'insufficient records, no '. ",
        "3. do not output reasoning process. ",
        "4. not  <think> tags. ",
        "5. recommendations , not empty . ",
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


def save_review_report(
    project: str,
    report: str,
    contexts: list[dict],
    doc_types: list[str],
    local_review: str,
) -> Path:
    """
    save reportas Markdown. 
    """
    REVIEW_REPORT_DIR.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")

    file_path = REVIEW_REPORT_DIR / f"{timestamp}_{project}_review_report.md"

    sources = build_source_summary(contexts)
    doc_type_text = "[" + ", ".join(doc_types) + "]"

    lines = []

    lines.append("---")
    lines.append(f"title: {project} project records report {timestamp}")
    lines.append(f"created: {now.isoformat(timespec='seconds')}")
    lines.append("category: summary")
    lines.append(f"project: {project}")
    lines.append("doc_type: review_report")
    lines.append("tags: [ , M2.5, auto generated, personal secretary]")
    lines.append(f"source_doc_types: {doc_type_text}")
    lines.append("---")
    lines.append("")
    lines.append(report)
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(local_review)
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
    return file_path

def main():
    parser = argparse.ArgumentParser(
        description="Personal Project Secretary + Knowledge Base:project records "
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
        ),
    )

    parser.add_argument(
        "--max-points",
        type=int,
        default=180,
        help=" read chunk. ",
    )

    parser.add_argument(
        "--max-chars",
        type=int,
        default=30000,
        help=" model. ",
    )

    parser.add_argument(
        "--no-save",
        action="store_true",
        help="onlyin , notsave Markdown file. ",
    )

    args = parser.parse_args()

    doc_types = parse_doc_types(args.doc_type)

    print("Personal Project Secretary + Knowledge Base:project records ")
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

    local_review = build_local_review_text(
        project=args.project,
        contexts=contexts,
    )

    print("")
    print("=" * 80)
    print(" rulescheck ")
    print("=" * 80)
    print(local_review)

    print("")
    print("running project records report...")

    report = generate_review_report(
        project=args.project,
        contexts=contexts,
        local_review=local_review,
    )

    print("")
    print("=" * 80)
    print("project records report")
    print("=" * 80)
    print(report)

    if args.no_save:
        print("")
        print("already  --no-save,  save Markdown file. ")
        return

    file_path = save_review_report(
        project=args.project,
        report=report,
        contexts=contexts,
        doc_types=doc_types,
        local_review=local_review,
    )

    print("")
    print("project records reportalreadysave:")
    print(file_path)
    print("")
    print("recommended next command:")
    print("python update_index.py")
    print(
        'python ask.py --doc-type review_report '
        '" project recordshas and risks？"'
    )


if __name__ == "__main__":
    main()

