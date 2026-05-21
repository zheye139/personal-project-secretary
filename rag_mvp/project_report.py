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


# 避免访问本机服务时走系统代理
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
    从 Qdrant 中读取指定项目的资料。
    使用 scroll，不依赖语义检索，适合做项目整体报告。
    """
    client = QdrantClient(
        url=QDRANT_URL,
        check_compatibility=False,
        timeout=60,
    )

    if not client.collection_exists(COLLECTION_NAME):
        raise RuntimeError(f"集合不存在：{COLLECTION_NAME}，请先运行 python update_index.py")

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
            lines.append(f"### 资料 {i}")
            lines.append(f"- 标题：{ctx.get('title', '')}")
            lines.append(f"- 文件：{ctx.get('file_name', '')}")
            lines.append(f"- 来源：{ctx.get('source', '')}")
            lines.append(f"- 更新时间：{ctx.get('updated_at', '')}")
            lines.append(f"- 标签：{ctx.get('tags', [])}")
            lines.append("")
            lines.append(ctx.get("text", ""))
            lines.append("")

    return "\n".join(lines)


def generate_report(project: str, contexts: list[dict]) -> str:
    if not contexts:
        return f"# {project} 项目状态报告\n\n当前知识库中没有检索到该项目的资料。"

    context_text = build_context_text(contexts)

    prompt = f"""
你是我的个人项目秘书和数据知识库助手。

请根据下面的知识库资料，为项目生成一份清晰、可执行的项目状态报告。

【项目名称】
{project}

【知识库资料】
{context_text}

【报告要求】
请使用中文 Markdown 格式输出，包含以下章节：

# {project} 项目状态报告

## 1. 当前总体状态
说明项目当前处于什么阶段。

## 2. 已完成内容
按条目列出已经完成的内容。

## 3. 当前技术方案
说明当前模型、数据库、脚本、知识库结构等关键方案。

## 4. 已遇到的问题与解决情况
列出已经记录的问题、原因和解决方式。

## 5. 重要决策
列出项目中已经做出的关键技术决策。

## 6. 当前风险与注意事项
指出后续可能出现的问题。

## 7. 下一步建议
给出具体、可执行的下一步任务。

要求：
1. 只根据资料回答，不要编造。
2. 如果资料不足，请明确写“资料不足，无法确认”。
3. 内容要适合保存为项目阶段报告。
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
    lines.append(f"title: {project} 项目状态报告 {timestamp}")
    lines.append(f"created: {now.isoformat(timespec='seconds')}")
    lines.append("category: summary")
    lines.append(f"project: {project}")
    lines.append("doc_type: project_report")
    lines.append("tags: [项目报告, RAG, 自动生成]")
    lines.append("---")
    lines.append("")
    lines.append(report)
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 本报告使用的知识库来源")
    lines.append("")

    if not sources:
        lines.append("未记录来源。")
    else:
        for source in sources:
            lines.append(f"- {source}")

    lines.append("")

    file_path.write_text("\n".join(lines), encoding="utf-8")
    return str(file_path)


def main():
    parser = argparse.ArgumentParser(
        description="个人项目秘书 + 数据知识库：生成项目状态报告"
    )

    parser.add_argument(
        "--project",
        required=True,
        help="项目名称，例如 Demo_Project",
    )

    parser.add_argument(
        "--max-points",
        type=int,
        default=80,
        help="最多读取多少个向量片段",
    )

    parser.add_argument(
        "--max-chars",
        type=int,
        default=18000,
        help="最多提供多少字符给模型",
    )

    args = parser.parse_args()

    print(f"正在读取项目资料：{args.project}")

    contexts = load_project_context(
        project=args.project,
        max_points=args.max_points,
        max_chars=args.max_chars,
    )

    print(f"读取到片段数量：{len(contexts)}")

    if not contexts:
        print("没有读取到项目资料，报告仍会生成，但内容会提示资料不足。")

    print("正在生成项目状态报告...")
    report = generate_report(args.project, contexts)

    file_path = save_report(args.project, report, contexts)

    print("")
    print("项目报告已生成：")
    print(file_path)
    print("")
    print("建议下一步执行：")
    print("python update_index.py")


if __name__ == "__main__":
    main()