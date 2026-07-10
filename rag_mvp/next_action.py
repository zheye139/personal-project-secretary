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

NEXT_ACTION_DIR = getattr(
    config,
    "NEXT_ACTION_DIR",
    KNOWLEDGE_ROOT / "05_Summaries" / "next_actions",
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
    "progress_log",
    "next_steps",
    "project_report",
    "weekly_report",
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
    Qdrant 层只按 project 过滤。
    doc_type 在 Python 中再过滤，避免多条件 OR 兼容性问题。
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
    如果没有传入，则使用默认目标文档类型。
    """
    if not raw_doc_types:
        return DEFAULT_DOC_TYPES

    result = []

    for item in raw_doc_types:
        parts = [part.strip() for part in item.split(",") if part.strip()]
        result.extend(parts)

    return sorted(set(result))


def safe_text_preview(text: str, max_chars: int = 300) -> str:
    """
    生成短预览文本。
    """
    text = text.replace("\n", " ").strip()

    if len(text) <= max_chars:
        return text

    return text[:max_chars] + "..."


def load_project_contexts(
    project: str,
    doc_types: list[str],
    max_points: int = 120,
    max_chars: int = 24000,
) -> list[dict]:
    """
    从 Qdrant 中读取指定项目的候选资料。

    读取逻辑：
    1. 先按 project 从 Qdrant scroll。
    2. 再在 Python 中筛选 doc_type。
    3. 按 updated_at 倒序排序。
    4. 限制最大片段数量和最大字符数，避免 prompt 过长。
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
    将检索到的资料整理成给模型使用的上下文文本。
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
    生成来源列表，写入最终 Markdown 报告。
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


def generate_next_actions(project: str, contexts: list[dict]) -> str:
    """
    调用 qwen3:8b，从项目资料中提取下一步行动项。
    """
    if not contexts:
        lines = [
            f"# {project} 下一步行动清单",
            "",
            "当前没有读取到可用于提取行动项的项目资料。",
            "",
            "建议：",
            "",
            "1. 补充 progress_log.md。",
            "2. 补充 next_steps.md。",
            "3. 生成 project_report 或 weekly_report 后重新运行本脚本。",
            "",
        ]
        return "\n".join(lines)

    context_text = build_context_text(contexts)

    prompt_lines = [
        "你是我的个人项目秘书和项目管理助手。",
        "",
        "请根据下面提供的项目资料，提取可执行的下一步行动项。",
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
        f"# {project} 下一步行动清单",
        "",
        "## 1. 直接结论",
        "用 3 到 6 条概括当前最应该推进的事项。",
        "",
        "## 2. 待办事项清单",
        "请用表格输出，列包含：",
        "",
        "| 编号 | 待办事项 | 建议优先级 | 来源依据 | 备注 |",
        "| --- | --- | --- | --- | --- |",
        "",
        "要求：",
        "1. 待办事项必须是可执行动作，不要写空泛表述。",
        "2. 建议优先级只能使用：高 / 中 / 低。",
        "3. 来源依据要尽量写明来自 progress_log、next_steps、project_report 或 weekly_report。",
        "4. 如果资料不足，请写“资料不足，无法确认”。",
        "",
        "## 3. 今日建议",
        "列出今天最适合处理的 1 到 3 个事项。",
        "",
        "## 4. 本周建议",
        "列出本周建议处理的事项。",
        "",
        "## 5. 需要补充的资料",
        "指出为了更准确提取待办事项，还需要补充哪些记录。",
        "",
        "额外要求：",
        "1. 不要编造资料中不存在的事实。",
        "2. 不要输出思考过程。",
        "3. 不要输出 <think> 标签。",
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


def save_next_actions(
    project: str,
    report: str,
    contexts: list[dict],
    doc_types: list[str],
) -> Path:
    """
    将行动清单保存为 Markdown 文件，方便后续重新入库。
    """
    NEXT_ACTION_DIR.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")

    file_path = NEXT_ACTION_DIR / f"{timestamp}_{project}_next_actions.md"

    sources = build_source_summary(contexts)
    doc_type_text = "[" + ", ".join(doc_types) + "]"

    lines = []

    lines.append("---")
    lines.append(f"title: {project} 下一步行动清单 {timestamp}")
    lines.append(f"created: {now.isoformat(timespec='seconds')}")
    lines.append("category: summary")
    lines.append(f"project: {project}")
    lines.append("doc_type: next_action_report")
    lines.append("tags: [下一步行动, 待办事项, M2.1, 自动生成]")
    lines.append(f"source_doc_types: {doc_type_text}")
    lines.append("---")
    lines.append("")
    lines.append(report)
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 本行动清单使用的知识库来源")
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
        description="个人项目秘书 + 数据知识库：提取项目下一步行动项"
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
            "默认：progress_log,next_steps,project_report,weekly_report"
        ),
    )

    parser.add_argument(
        "--max-points",
        type=int,
        default=120,
        help="最多读取多少个向量片段。",
    )

    parser.add_argument(
        "--max-chars",
        type=int,
        default=24000,
        help="最多提供多少字符给模型。",
    )

    parser.add_argument(
        "--no-save",
        action="store_true",
        help="只在终端输出，不保存 Markdown 文件。",
    )

    args = parser.parse_args()

    doc_types = parse_doc_types(args.doc_type)

    print("个人项目秘书 + 数据知识库：下一步行动项提取")
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
    print("正在生成下一步行动清单...")

    report = generate_next_actions(
        project=args.project,
        contexts=contexts,
    )

    print("")
    print("=" * 80)
    print("下一步行动清单")
    print("=" * 80)
    print(report)

    if args.no_save:
        print("")
        print("已选择 --no-save，未保存 Markdown 文件。")
        return

    file_path = save_next_actions(
        project=args.project,
        report=report,
        contexts=contexts,
        doc_types=doc_types,
    )

    print("")
    print("行动清单已保存：")
    print(file_path)
    print("")
    print("建议下一步执行：")
    print("python update_index.py")
    print(
        'python ask.py --doc-type next_action_report '
        '"当前项目下一步最应该做什么？"'
    )


if __name__ == "__main__":
    main()

