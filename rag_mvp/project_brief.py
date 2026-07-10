import argparse
import re
import requests
import sys
from datetime import datetime
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

import config
import vector_store_config


# ============================================================
# 基础配置
# ============================================================

OLLAMA_URL = config.OLLAMA_URL
CHAT_MODEL = config.CHAT_MODEL
QDRANT_URL = vector_store_config.get_qdrant_url()
COLLECTION_NAME = vector_store_config.get_collection_name()
KNOWLEDGE_ROOT = config.KNOWLEDGE_ROOT

PROJECT_BRIEF_DIR = getattr(
    config,
    "PROJECT_BRIEF_DIR",
    KNOWLEDGE_ROOT / "05_Summaries" / "project_briefs",
)


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

vector_store_config.configure_qdrant_environment()


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
    清理 qwen3 可能输出的 <think>...</think> 内容。
    """
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    return text.strip()


def get_qdrant_client() -> QdrantClient:
    """
    创建 Qdrant 客户端。
    """
    return vector_store_config.get_qdrant_client(timeout=60)


def build_project_filter(project: str):
    """
    Qdrant 层按 project 过滤。
    doc_type 后续在 Python 中过滤，方便兼容更多 qdrant-client 版本。
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
    解析命令行传入的 doc_type。
    支持：
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
    生成终端预览文本。
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
    从 Qdrant 中读取指定项目资料。

    project_brief.py 不是单纯问答检索，而是项目状态汇总，
    所以这里使用 scroll 读取项目相关资料，再按 doc_type 筛选。
    """
    client = get_qdrant_client()

    if not client.collection_exists(COLLECTION_NAME):
        raise RuntimeError(
            f"集合不存在：{COLLECTION_NAME}，请先运行 python update_index.py"
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
    将项目资料整理成模型可读上下文。
    """
    lines = []

    for index, ctx in enumerate(contexts, start=1):
        lines.append(f"## 资料 {index}")
        lines.append("")
        lines.append(f"- 资料大类：{ctx.get('category', '')}")
        lines.append(f"- 项目：{ctx.get('project', '')}")
        lines.append(f"- 文档类型：{ctx.get('doc_type', '')}")
        lines.append(f"- 标题：{ctx.get('title', '')}")
        lines.append(f"- 标签：{ctx.get('tags', [])}")
        lines.append(f"- 文件：{ctx.get('file_name', '')}")
        lines.append(f"- 来源：{ctx.get('source', '')}")
        lines.append(f"- 片段：{ctx.get('chunk_index', '')}")
        lines.append(f"- 更新时间：{ctx.get('updated_at', '')}")
        lines.append("")
        lines.append(ctx.get("text", ""))
        lines.append("")

    return "\n".join(lines)


def build_source_summary(contexts: list[dict]) -> list[str]:
    """
    生成来源清单。
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
    调用 qwen3:8b 生成项目简报。
    """
    if not contexts:
        lines = [
            f"# {project} 项目简报",
            "",
            "当前没有读取到足够的项目资料，无法生成完整简报。",
            "",
            "建议补充：",
            "",
            "1. project_overview.md",
            "2. progress_log.md",
            "3. issues.md",
            "4. next_steps.md",
            "5. project_report 或 weekly_report",
            "",
        ]
        return "\n".join(lines)

    context_text = build_context_text(contexts)

    prompt_lines = [
        "你是我的个人项目秘书和项目管理助手。",
        "",
        "请根据下面的项目资料，生成一份简短、清晰、适合日常查看的项目简报。",
        "",
        "【项目名称】",
        project,
        "",
        "【项目资料】",
        context_text,
        "",
        "【输出要求】",
        "请使用中文 Markdown 输出。",
        "",
        f"# {project} 项目简报",
        "",
        "## 1. 一句话状态",
        "用一句话说明项目当前处于什么状态。",
        "",
        "## 2. 当前状态",
        "用 3 到 6 条概括项目当前阶段、已具备能力和整体进展。",
        "",
        "## 3. 最近进展",
        "列出最近已经完成或推进的事项。",
        "",
        "## 4. 当前问题",
        "列出当前明确存在的问题、风险或待确认事项。",
        "如果资料中没有明确问题，请写“资料中未发现明确问题”。",
        "",
        "## 5. 下一步行动",
        "列出最建议推进的 3 到 8 个下一步行动。",
        "要求每一项都尽量可执行。",
        "",
        "## 6. 风险提醒",
        "列出后续可能影响项目推进的风险。",
        "",
        "## 7. 建议补充的记录",
        "指出为了让知识库更完整，还应该补充哪些记录。",
        "",
        "额外要求：",
        "1. 只根据资料回答，不要编造。",
        "2. 如果资料不足，请明确写“资料不足，无法确认”。",
        "3. 不要输出思考过程。",
        "4. 不要输出 <think> 标签。",
        "5. 简报要短于项目报告，适合日常快速查看。",
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
    保存项目简报为 Markdown，方便后续重新入库。
    """
    PROJECT_BRIEF_DIR.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")

    file_path = PROJECT_BRIEF_DIR / f"{timestamp}_{project}_project_brief.md"

    sources = build_source_summary(contexts)
    doc_type_text = "[" + ", ".join(doc_types) + "]"

    lines = []

    lines.append("---")
    lines.append(f"title: {project} 项目简报 {timestamp}")
    lines.append(f"created: {now.isoformat(timespec='seconds')}")
    lines.append("category: summary")
    lines.append(f"project: {project}")
    lines.append("doc_type: project_brief")
    lines.append("tags: [项目简报, M2.2, 自动生成, 个人秘书]")
    lines.append(f"source_doc_types: {doc_type_text}")
    lines.append("---")
    lines.append("")
    lines.append(brief)
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 本项目简报使用的知识库来源")
    lines.append("")

    if not sources:
        lines.append("未记录来源。")
    else:
        for source in sources:
            lines.append(f"- {source}")

    lines.append("")

    file_path.write_text("\n".join(lines), encoding="utf-8")
    return file_path


def main():
    parser = argparse.ArgumentParser(
        description="个人项目秘书 + 数据知识库：生成项目简报"
    )

    parser.add_argument(
        "--project",
        required=True,
        help="项目名称，例如 Personal_Project_Assistant",
    )

    parser.add_argument(
        "--doc-type",
        action="append",
        default=None,
        help=(
            "指定参与分析的文档类型。"
            "可重复使用，也可用逗号分隔。"
            "默认包含项目概述、进度、问题、下一步、项目报告、周报、行动清单等。"
        ),
    )

    parser.add_argument(
        "--max-points",
        type=int,
        default=140,
        help="最多读取多少个向量片段。",
    )

    parser.add_argument(
        "--max-chars",
        type=int,
        default=26000,
        help="最多提供多少字符给模型。",
    )

    parser.add_argument(
        "--no-save",
        action="store_true",
        help="只在终端输出，不保存 Markdown 文件。",
    )

    args = parser.parse_args()

    doc_types = parse_doc_types(args.doc_type)

    print("个人项目秘书 + 数据知识库：项目简报生成")
    print(f"项目：{args.project}")
    print(f"目标文档类型：{doc_types}")
    print(f"最大片段数：{args.max_points}")
    print(f"最大字符数：{args.max_chars}")

    contexts = load_project_contexts(
        project=args.project,
        doc_types=doc_types,
        max_points=args.max_points,
        max_chars=args.max_chars,
    )

    print(f"读取到候选资料片段数量：{len(contexts)}")

    if contexts:
        print("")
        print("候选资料预览：")

        for index, ctx in enumerate(contexts[:8], start=1):
            print(
                f"{index}. "
                f"{ctx.get('doc_type', '')} | "
                f"{ctx.get('file_name', '')} | "
                f"{ctx.get('updated_at', '')}"
            )
            print(f"   来源：{ctx.get('source', '')}")
            print(f"   内容：{safe_text_preview(ctx.get('text', ''), 120)}")

    print("")
    print("正在生成项目简报...")

    brief = generate_project_brief(
        project=args.project,
        contexts=contexts,
    )

    print("")
    print("=" * 80)
    print("项目简报")
    print("=" * 80)
    print(brief)

    if args.no_save:
        print("")
        print("已选择 --no-save，未保存 Markdown 文件。")
        return

    file_path = save_project_brief(
        project=args.project,
        brief=brief,
        contexts=contexts,
        doc_types=doc_types,
    )

    print("")
    print("项目简报已保存：")
    print(file_path)
    print("")
    print("建议下一步执行：")
    print("python update_index.py")
    print(
        'python ask.py --doc-type project_brief '
        '"当前项目简报总结了什么？"'
    )


if __name__ == "__main__":
    main()
