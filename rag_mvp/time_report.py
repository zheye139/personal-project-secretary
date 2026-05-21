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

    raise ValueError("mode 只支持 daily 或 weekly")


def build_filter(project: str):
    """
    Qdrant 这里只按 project 过滤。
    时间范围在 Python 中根据 updated_at 再判断，避免 Range 只能处理数字的问题。
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
    解析 ISO 时间字符串。
    例如：2026-05-17T20:34:04
    """
    if not value:
        return None

    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def is_in_time_range(updated_at: str, start: datetime, end: datetime) -> bool:
    """
    判断 updated_at 是否在日报/周报时间范围内。
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
        raise RuntimeError(f"集合不存在：{COLLECTION_NAME}，请先运行 python update_index.py")

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
        lines.append(f"## 资料 {i}")
        lines.append(f"- 资料大类：{ctx.get('category', '')}")
        lines.append(f"- 项目：{ctx.get('project', '')}")
        lines.append(f"- 文档类型：{ctx.get('doc_type', '')}")
        lines.append(f"- 标题：{ctx.get('title', '')}")
        lines.append(f"- 标签：{ctx.get('tags', [])}")
        lines.append(f"- 文件：{ctx.get('file_name', '')}")
        lines.append(f"- 来源：{ctx.get('source', '')}")
        lines.append(f"- 更新时间：{ctx.get('updated_at', '')}")
        lines.append("")
        lines.append(ctx.get("text", ""))
        lines.append("")

    return "\n".join(lines)


def generate_time_report(project: str, mode: str, contexts: list[dict]) -> str:
    now = datetime.now()
    start, end = get_time_range(mode)

    if mode == "daily":
        title = f"{project} 日报"
        report_sections = """
## 1. 今日总体状态
## 2. 今日完成内容
## 3. 今日新增资料
## 4. 今日遇到的问题
## 5. 今日重要决策
## 6. 明日建议
"""
    else:
        title = f"{project} 周报"
        report_sections = """
## 1. 本周总体状态
## 2. 本周完成内容
## 3. 本周新增资料
## 4. 本周遇到的问题与解决情况
## 5. 本周重要决策
## 6. 当前风险
## 7. 下周建议
"""

    context_text = build_context_text(contexts)

    if not contexts:
        context_text = "当前时间范围内没有检索到相关资料。"

    prompt = f"""
你是我的个人项目秘书和数据知识库助手。

请根据下面的知识库资料生成一份项目时间报告。

【项目名称】
{project}

【报告类型】
{mode}

【时间范围】
{start.isoformat(timespec="seconds")} 到 {end.isoformat(timespec="seconds")}

【知识库资料】
{context_text}

【输出要求】
请使用中文 Markdown 格式输出。

# {title}

{report_sections}

要求：
1. 只根据资料回答，不要编造。
2. 如果某一部分资料不足，请写“资料不足，无法确认”。
3. 输出要适合直接保存到项目知识库。
4. 不要输出思考过程，不要输出 <think> 标签。
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
        tag_name = "日报"
    else:
        doc_type = "weekly_report"
        tag_name = "周报"

    file_path = TIME_REPORT_DIR / f"{timestamp}_{project}_{doc_type}.md"

    sources = sorted({ctx.get("source", "") for ctx in contexts if ctx.get("source", "")})

    lines = []
    lines.append("---")
    lines.append(f"title: {project} {tag_name} {timestamp}")
    lines.append(f"created: {now.isoformat(timespec='seconds')}")
    lines.append("category: summary")
    lines.append(f"project: {project}")
    lines.append(f"doc_type: {doc_type}")
    lines.append(f"tags: [{tag_name}, 项目报告, RAG, 自动生成]")
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
        description="个人项目秘书 + 数据知识库：生成日报 / 周报"
    )

    parser.add_argument(
        "--project",
        required=True,
        help="项目名称，例如 Demo_Project",
    )

    parser.add_argument(
        "--mode",
        required=True,
        choices=["daily", "weekly"],
        help="报告类型：daily 或 weekly",
    )

    parser.add_argument(
        "--max-points",
        type=int,
        default=100,
        help="最多读取多少个向量片段",
    )

    parser.add_argument(
        "--max-chars",
        type=int,
        default=22000,
        help="最多提供多少字符给模型",
    )

    args = parser.parse_args()

    print(f"正在生成 {args.mode} 报告")
    print(f"项目：{args.project}")

    contexts = load_context(
        project=args.project,
        mode=args.mode,
        max_points=args.max_points,
        max_chars=args.max_chars,
    )

    print(f"读取到片段数量：{len(contexts)}")

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
    print("时间报告已生成：")
    print(file_path)
    print("")
    print("建议下一步执行：")
    print("python update_index.py")


if __name__ == "__main__":
    main()