import argparse
import re
import requests
import sys
from collections import defaultdict
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

REVIEW_REPORT_DIR = getattr(
    config,
    "REVIEW_REPORT_DIR",
    KNOWLEDGE_ROOT / "05_Summaries" / "review_reports",
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
    "technical_notes",
    "project_report",
    "weekly_report",
    "project_brief",
    "next_action_report",
    "priority_advice",
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
    解析可重复、可逗号分隔的命令行参数。
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
    解析参与复盘的 doc_type。
    """
    parsed = parse_csv_values(raw_doc_types)

    if not parsed:
        return DEFAULT_DOC_TYPES

    return parsed


def safe_text_preview(text: str, max_chars: int = 180) -> str:
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
    max_points: int = 180,
    max_chars: int = 30000,
) -> list[dict]:
    """
    从 Qdrant 中读取指定项目资料。

    review_assistant.py 关注“资料完整性和风险”，
    所以会读取较多类型的项目资料。
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
    统计当前项目包含哪些 doc_type。
    """
    counts = defaultdict(int)

    for ctx in contexts:
        counts[ctx.get("doc_type", "")] += 1

    return dict(counts)


def get_latest_updated_at(contexts: list[dict]) -> str:
    """
    获取资料中的最近更新时间。
    """
    latest = ""

    for ctx in contexts:
        updated_at = ctx.get("updated_at", "")
        if updated_at > latest:
            latest = updated_at

    return latest


def local_rule_review(project: str, contexts: list[dict]) -> list[str]:
    """
    不依赖模型的基础规则检查。

    作用：
    1. 检查是否缺少关键文档类型。
    2. 检查是否长期没有 next_steps。
    3. 检查是否没有问题记录或决策记录。
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
            issues.append(f"可能缺少关键文档类型：{doc_type}")

    if counts.get("project_brief", 0) == 0:
        issues.append("尚未发现 project_brief，建议先生成项目简报。")

    if counts.get("next_action_report", 0) == 0:
        issues.append("尚未发现 next_action_report，建议先生成下一步行动清单。")

    if counts.get("weekly_report", 0) == 0:
        issues.append("尚未发现 weekly_report，建议定期生成周报。")

    if counts.get("issues", 0) == 0 and counts.get("issue", 0) == 0:
        issues.append("未发现明确问题记录，可能不利于后续复盘。")

    if counts.get("decisions", 0) == 0 and counts.get("decision", 0) == 0:
        issues.append("未发现明确决策记录，建议记录关键技术选择原因。")

    if not contexts:
        issues.append(f"项目 {project} 没有读取到可复盘资料。")

    return issues


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

        sources.append(f"{doc_type} | {source} | {updated_at}")

    return sorted(set(sources))


def build_local_review_text(project: str, contexts: list[dict]) -> str:
    """
    将本地规则检查结果整理为 Markdown。
    """
    counts = summarize_doc_type_counts(contexts)
    local_issues = local_rule_review(project, contexts)
    latest = get_latest_updated_at(contexts)

    lines = []
    lines.append("## 本地规则检查摘要")
    lines.append("")
    lines.append(f"- 项目：{project}")
    lines.append(f"- 候选片段数量：{len(contexts)}")
    lines.append(f"- 最近更新时间：{latest if latest else '未知'}")
    lines.append(f"- 文档类型统计：{counts}")
    lines.append("")

    if local_issues:
        lines.append("### 规则发现的问题")
        lines.append("")
        for issue in local_issues:
            lines.append(f"- {issue}")
    else:
        lines.append("未发现明显规则问题。")

    lines.append("")

    return "\n".join(lines)


def generate_review_report(
    project: str,
    contexts: list[dict],
    local_review: str,
) -> str:
    """
    调用 qwen3:8b 生成项目记录复盘报告。
    """
    if not contexts:
        lines = [
            f"# {project} 项目记录复盘报告",
            "",
            "当前没有读取到可用于复盘的项目资料。",
            "",
            local_review,
            "",
            "建议：",
            "",
            "1. 补充 project_overview.md。",
            "2. 补充 progress_log.md。",
            "3. 补充 issues.md。",
            "4. 补充 decisions.md。",
            "5. 补充 next_steps.md。",
            "6. 执行 python update_index.py 后重新运行本脚本。",
            "",
        ]
        return "\n".join(lines)

    context_text = build_context_text(contexts)

    prompt_lines = [
        "你是我的个人项目秘书和项目复盘助手。",
        "",
        "请根据下面的项目资料和本地规则检查结果，对项目记录进行复盘。",
        "",
        "复盘重点不是重新总结项目，而是检查：",
        "1. 记录是否完整。",
        "2. 是否存在遗漏。",
        "3. 是否存在风险。",
        "4. 是否有问题记录但缺少解决方案。",
        "5. 是否有进度记录但缺少下一步。",
        "6. 是否有技术决策但缺少理由。",
        "7. 是否需要补充文档。",
        "",
        "【项目名称】",
        project,
        "",
        "【本地规则检查结果】",
        local_review,
        "",
        "【项目资料】",
        context_text,
        "",
        "【输出要求】",
        "请使用中文 Markdown 输出。",
        "",
        f"# {project} 项目记录复盘报告",
        "",
        "## 1. 复盘结论",
        "用 3 到 6 条说明项目记录当前是否完整、主要问题是什么。",
        "",
        "## 2. 记录完整性检查",
        "检查项目概述、进度、问题、决策、下一步、报告、行动清单是否齐全。",
        "",
        "## 3. 发现的遗漏",
        "列出当前项目资料中明显缺失或需要补充的内容。",
        "",
        "## 4. 风险与隐患",
        "指出可能影响项目推进、维护、迁移、复盘的风险。",
        "",
        "## 5. 建议补充的记录",
        "请用表格输出，列包含：",
        "",
        "| 编号 | 建议补充内容 | 原因 | 建议保存位置/文档类型 | 优先级 |",
        "| --- | --- | --- | --- | --- |",
        "",
        "## 6. 建议立即修正的问题",
        "列出最应该马上处理的记录问题。",
        "",
        "## 7. 后续复盘建议",
        "说明以后应该如何持续维护这个项目记录。",
        "",
        "额外要求：",
        "1. 只根据资料回答，不要编造。",
        "2. 如果资料不足，请明确写“资料不足，无法确认”。",
        "3. 不要输出思考过程。",
        "4. 不要输出 <think> 标签。",
        "5. 建议要具体，不要空泛。",
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
    保存项目复盘报告为 Markdown。
    """
    REVIEW_REPORT_DIR.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")

    file_path = REVIEW_REPORT_DIR / f"{timestamp}_{project}_review_report.md"

    sources = build_source_summary(contexts)
    doc_type_text = "[" + ", ".join(doc_types) + "]"

    lines = []

    lines.append("---")
    lines.append(f"title: {project} 项目记录复盘报告 {timestamp}")
    lines.append(f"created: {now.isoformat(timespec='seconds')}")
    lines.append("category: summary")
    lines.append(f"project: {project}")
    lines.append("doc_type: review_report")
    lines.append("tags: [项目复盘, M2.5, 自动生成, 个人秘书]")
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
    lines.append("## 本复盘报告使用的知识库来源")
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
        description="个人项目秘书 + 数据知识库：项目记录复盘助手"
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
            "指定参与复盘的文档类型。"
            "可重复使用，也可逗号分隔。"
        ),
    )

    parser.add_argument(
        "--max-points",
        type=int,
        default=180,
        help="最多读取多少个向量片段。",
    )

    parser.add_argument(
        "--max-chars",
        type=int,
        default=30000,
        help="最多提供多少字符给模型。",
    )

    parser.add_argument(
        "--no-save",
        action="store_true",
        help="只在终端输出，不保存 Markdown 文件。",
    )

    args = parser.parse_args()

    doc_types = parse_doc_types(args.doc_type)

    print("个人项目秘书 + 数据知识库：项目记录复盘助手")
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

    local_review = build_local_review_text(
        project=args.project,
        contexts=contexts,
    )

    print("")
    print("=" * 80)
    print("本地规则检查摘要")
    print("=" * 80)
    print(local_review)

    print("")
    print("正在生成项目记录复盘报告...")

    report = generate_review_report(
        project=args.project,
        contexts=contexts,
        local_review=local_review,
    )

    print("")
    print("=" * 80)
    print("项目记录复盘报告")
    print("=" * 80)
    print(report)

    if args.no_save:
        print("")
        print("已选择 --no-save，未保存 Markdown 文件。")
        return

    file_path = save_review_report(
        project=args.project,
        report=report,
        contexts=contexts,
        doc_types=doc_types,
        local_review=local_review,
    )

    print("")
    print("项目记录复盘报告已保存：")
    print(file_path)
    print("")
    print("建议下一步执行：")
    print("python update_index.py")
    print(
        'python ask.py --doc-type review_report '
        '"当前项目记录有哪些遗漏和风险？"'
    )


if __name__ == "__main__":
    main()

