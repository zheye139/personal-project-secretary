import argparse
import re
import requests
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from qdrant_client import QdrantClient

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

SECRETARY_REPORT_DIR = getattr(
    config,
    "SECRETARY_REPORT_DIR",
    KNOWLEDGE_ROOT / "05_Summaries" / "secretary_reports",
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


# ============================================================
# 默认参与秘书汇报的文档类型
# ============================================================

DEFAULT_DOC_TYPES = [
    "multi_project_status",
    "priority_advice",
    "review_report",
    "project_brief",
    "next_action_report",
    "weekly_report",
    "daily_report",
    "project_report",
    "progress_log",
    "next_steps",
    "issues",
    "issue",
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


def parse_csv_values(raw_values: list[str] | None) -> list[str]:
    """
    解析可重复、可逗号分隔的命令行参数。

    示例：
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
    解析参与秘书汇报的 doc_type。
    """
    parsed = parse_csv_values(raw_doc_types)

    if not parsed:
        return DEFAULT_DOC_TYPES

    return parsed


def safe_text_preview(text: str, max_chars: int = 160) -> str:
    """
    生成终端预览文本。
    """
    text = text.replace("\n", " ").strip()

    if len(text) <= max_chars:
        return text

    return text[:max_chars] + "..."


def get_project_latest_time(items: list[dict]) -> str:
    """
    获取某个项目资料中的最近更新时间。
    """
    latest = ""

    for item in items:
        updated_at = item.get("updated_at", "")
        if updated_at > latest:
            latest = updated_at

    return latest


def load_secretary_contexts(
    include_projects: list[str],
    exclude_projects: list[str],
    doc_types: list[str],
    max_points: int = 1200,
) -> dict[str, list[dict]]:
    """
    从 Qdrant 中读取用于生成个人秘书汇报的资料，并按 project 分组。

    读取规则：
    1. 不指定 --project 时，读取所有项目。
    2. 指定 --project 时，只读取指定项目。
    3. 指定 --exclude-project 时，排除指定项目。
    4. 只读取指定 doc_type。
    """
    client = get_qdrant_client()

    if not client.collection_exists(COLLECTION_NAME):
        raise RuntimeError(
            f"集合不存在：{COLLECTION_NAME}，请先运行 python update_index.py"
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


def trim_contexts(
    grouped_contexts: dict[str, list[dict]],
    max_projects: int,
    max_items_per_project: int,
    max_chars_per_project: int,
) -> dict[str, list[dict]]:
    """
    控制传给模型的资料量。

    逻辑：
    1. 优先保留最近更新的项目。
    2. 每个项目保留最近的若干片段。
    3. 每个项目限制最大字符数。
    """
    project_latest = []

    for project, items in grouped_contexts.items():
        project_latest.append((project, get_project_latest_time(items)))

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
    构建给 qwen3 使用的多项目上下文。
    """
    lines = []

    for project, items in grouped_contexts.items():
        lines.append(f"# 项目：{project}")
        lines.append("")

        for index, ctx in enumerate(items, start=1):
            lines.append(f"## 资料 {index}")
            lines.append("")
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

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def build_source_summary(grouped_contexts: dict[str, list[dict]]) -> list[str]:
    """
    生成来源清单。
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


def print_terminal_overview(grouped_contexts: dict[str, list[dict]]) -> None:
    """
    在终端打印参与秘书汇报的资料概览。
    """
    print("")
    print("候选项目资料概览：")

    for project, items in grouped_contexts.items():
        latest = get_project_latest_time(items)
        doc_type_count = defaultdict(int)

        for item in items:
            doc_type_count[item.get("doc_type", "")] += 1

        print("")
        print(f"- 项目：{project}")
        print(f"  片段数量：{len(items)}")
        print(f"  最近更新时间：{latest}")
        print(f"  文档类型统计：{dict(doc_type_count)}")

        for index, item in enumerate(items[:3], start=1):
            print(
                f"  {index}. {item.get('doc_type', '')} | "
                f"{item.get('file_name', '')} | "
                f"{item.get('updated_at', '')}"
            )
            print(f"     {safe_text_preview(item.get('text', ''), 120)}")


def generate_secretary_report(grouped_contexts: dict[str, list[dict]]) -> str:
    """
    调用 qwen3:8b 生成个人秘书汇报。
    """
    today = datetime.now().strftime("%Y-%m-%d")

    if not grouped_contexts:
        lines = [
            "# 个人秘书汇报",
            "",
            f"生成日期：{today}",
            "",
            "当前没有读取到可用于生成个人秘书汇报的项目资料。",
            "",
            "建议：",
            "",
            "1. 先生成 project_brief。",
            "2. 先生成 next_action_report。",
            "3. 先生成 multi_project_status。",
            "4. 先生成 priority_advice。",
            "5. 先生成 review_report。",
            "6. 执行 python update_index.py 后重新运行本脚本。",
            "",
        ]
        return "\n".join(lines)

    context_text = build_context_text(grouped_contexts)

    prompt_lines = [
        "你是我的个人项目秘书。",
        "",
        "请根据下面的知识库资料，生成一份适合日常查看的“个人秘书汇报”。",
        "",
        "这份汇报不是单个项目报告，而是帮助我快速了解：",
        "1. 当前多个项目整体情况。",
        "2. 今天最应该做什么。",
        "3. 本周应该关注什么。",
        "4. 有哪些风险。",
        "5. 哪些记录需要补充。",
        "",
        "【当前日期】",
        today,
        "",
        "【知识库资料】",
        context_text,
        "",
        "【输出要求】",
        "请使用中文 Markdown 输出。",
        "",
        "# 个人秘书汇报",
        "",
        "## 1. 今日直接结论",
        "用 3 到 6 条说明今天最重要的判断。",
        "",
        "## 2. 当前项目总览",
        "用表格输出，列包含：",
        "",
        "| 项目 | 当前状态 | 最近进展 | 当前风险 | 下一步建议 |",
        "| --- | --- | --- | --- | --- |",
        "",
        "## 3. 今日建议处理事项",
        "列出今天最建议处理的 1 到 5 个事项。",
        "每一项都要尽量具体可执行。",
        "",
        "## 4. 本周重点建议",
        "列出本周建议重点关注的项目和事项。",
        "",
        "## 5. 风险提醒",
        "列出当前最需要注意的风险。",
        "",
        "## 6. 需要补充的项目记录",
        "列出为了让知识库更完整，建议补充的记录。",
        "",
        "## 7. 建议执行的命令",
        "列出接下来建议执行的命令，例如 update_index、project_brief、next_action、backup 等。",
        "",
        "额外要求：",
        "1. 只根据资料回答，不要编造。",
        "2. 如果资料不足，请写“资料不足，无法确认”。",
        "3. 不要输出思考过程。",
        "4. 不要输出 <think> 标签。",
        "5. 建议要具体，不要空泛。",
        "6. 这份报告要适合我每天打开查看。",
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


def save_secretary_report(
    report: str,
    grouped_contexts: dict[str, list[dict]],
    doc_types: list[str],
) -> Path:
    """
    保存个人秘书汇报为 Markdown。
    """
    SECRETARY_REPORT_DIR.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")

    file_path = SECRETARY_REPORT_DIR / f"{timestamp}_secretary_report.md"

    project_names = sorted(grouped_contexts.keys())
    project_text = "[" + ", ".join(project_names) + "]"
    doc_type_text = "[" + ", ".join(doc_types) + "]"
    sources = build_source_summary(grouped_contexts)

    lines = []

    lines.append("---")
    lines.append(f"title: 个人秘书汇报 {timestamp}")
    lines.append(f"created: {now.isoformat(timespec='seconds')}")
    lines.append("category: summary")
    lines.append("project: Personal_Project_Assistant")
    lines.append("doc_type: secretary_report")
    lines.append("tags: [个人秘书汇报, M2.6, 自动生成, 个人秘书]")
    lines.append(f"projects: {project_text}")
    lines.append(f"source_doc_types: {doc_type_text}")
    lines.append("---")
    lines.append("")
    lines.append(report)
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 本个人秘书汇报使用的知识库来源")
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
        description="个人项目秘书 + 数据知识库：生成个人秘书汇报"
    )

    parser.add_argument(
        "--project",
        action="append",
        default=None,
        help="指定参与汇报的项目。可重复使用，也可逗号分隔。不指定则分析所有项目。",
    )

    parser.add_argument(
        "--exclude-project",
        action="append",
        default=None,
        help="排除指定项目。可重复使用，也可逗号分隔。",
    )

    parser.add_argument(
        "--doc-type",
        action="append",
        default=None,
        help="指定参与分析的文档类型。可重复使用，也可逗号分隔。",
    )

    parser.add_argument(
        "--max-projects",
        type=int,
        default=12,
        help="最多分析多少个项目。",
    )

    parser.add_argument(
        "--max-items-per-project",
        type=int,
        default=24,
        help="每个项目最多读取多少个片段。",
    )

    parser.add_argument(
        "--max-chars-per-project",
        type=int,
        default=14000,
        help="每个项目最多提供多少字符给模型。",
    )

    parser.add_argument(
        "--max-points",
        type=int,
        default=1200,
        help="从 Qdrant 最多扫描多少个候选片段。",
    )

    parser.add_argument(
        "--no-save",
        action="store_true",
        help="只在终端输出，不保存 Markdown 文件。",
    )

    args = parser.parse_args()

    include_projects = parse_csv_values(args.project)
    exclude_projects = parse_csv_values(args.exclude_project)
    doc_types = parse_doc_types(args.doc_type)

    print("个人项目秘书 + 数据知识库：个人秘书汇报")
    print(f"指定项目：{include_projects if include_projects else '全部'}")
    print(f"排除项目：{exclude_projects if exclude_projects else '无'}")
    print(f"目标文档类型：{doc_types}")
    print(f"最多项目数：{args.max_projects}")
    print(f"每项目最大片段数：{args.max_items_per_project}")
    print(f"每项目最大字符数：{args.max_chars_per_project}")

    grouped = load_secretary_contexts(
        include_projects=include_projects,
        exclude_projects=exclude_projects,
        doc_types=doc_types,
        max_points=args.max_points,
    )

    trimmed = trim_contexts(
        grouped_contexts=grouped,
        max_projects=args.max_projects,
        max_items_per_project=args.max_items_per_project,
        max_chars_per_project=args.max_chars_per_project,
    )

    print("")
    print(f"读取到项目数量：{len(trimmed)}")

    print_terminal_overview(trimmed)

    print("")
    print("正在生成个人秘书汇报...")

    report = generate_secretary_report(trimmed)

    print("")
    print("=" * 80)
    print("个人秘书汇报")
    print("=" * 80)
    print(report)

    if args.no_save:
        print("")
        print("已选择 --no-save，未保存 Markdown 文件。")
        return

    file_path = save_secretary_report(
        report=report,
        grouped_contexts=trimmed,
        doc_types=doc_types,
    )

    print("")
    print("个人秘书汇报已保存：")
    print(file_path)
    print("")
    print("建议下一步执行：")
    print("python update_index.py")
    print(
        'python ask.py --doc-type secretary_report '
        '"今天最应该优先处理什么？"'
    )


if __name__ == "__main__":
    main()

