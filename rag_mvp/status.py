import os
from collections import defaultdict
from datetime import datetime

import requests
from qdrant_client import QdrantClient

from config import (
    OLLAMA_URL,
    CHAT_MODEL,
    EMBED_MODEL,
    QDRANT_URL,
    COLLECTION_NAME,
    KNOWLEDGE_ROOT,
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


def check_ollama() -> tuple[bool, list[str]]:
    try:
        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        models = [m.get("name", "") for m in data.get("models", [])]
        return True, models
    except Exception:
        return False, []


def model_exists(target: str, models: list[str]) -> bool:
    if target in models:
        return True

    if ":" not in target and f"{target}:latest" in models:
        return True

    return False


def check_qdrant():
    try:
        client = QdrantClient(
            url=QDRANT_URL,
            check_compatibility=False,
            timeout=60,
        )

        ok = client.collection_exists(COLLECTION_NAME)

        if not ok:
            try:
                client.close()
            except Exception:
                pass

            return {
                "ok": True,
                "collection_exists": False,
                "points_count": 0,
                "docs_count": 0,
                "recent_docs": [],
                "projects": {},
            }

        info = client.get_collection(COLLECTION_NAME)
        points_count = info.points_count or 0

        docs = {}
        projects = defaultdict(int)

        offset = None

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

                source = payload.get("source", "unknown")
                project = payload.get("project", "unknown")
                doc_type = payload.get("doc_type", "unknown")
                file_name = payload.get("file_name", "")
                updated_at = payload.get("updated_at", "")

                projects[project] += 1

                if source not in docs:
                    docs[source] = {
                        "source": source,
                        "project": project,
                        "doc_type": doc_type,
                        "file_name": file_name,
                        "updated_at": updated_at,
                        "chunks": 0,
                    }

                docs[source]["chunks"] += 1

                if updated_at > docs[source].get("updated_at", ""):
                    docs[source]["updated_at"] = updated_at

            if offset is None:
                break

        recent_docs = sorted(
            docs.values(),
            key=lambda x: x.get("updated_at", ""),
            reverse=True,
        )[:8]

        try:
            client.close()
        except Exception:
            pass

        return {
            "ok": True,
            "collection_exists": True,
            "points_count": points_count,
            "docs_count": len(docs),
            "recent_docs": recent_docs,
            "projects": dict(projects),
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "collection_exists": False,
            "points_count": 0,
            "docs_count": 0,
            "recent_docs": [],
            "projects": {},
        }


def print_available_commands():
    print("\n=== 当前可用命令 ===")

    commands = [
        ('python check_env.py', "检查 Ollama / Qdrant 环境"),
        ('python ingest.py', "重新入库 Markdown 文档"),
        ('python update_index.py', "一键检查环境 + 重新入库 + 列出文档"),
        ('python list_docs.py', "列出已入库文档"),
        ('python inspect_collection.py', "查看 Qdrant 集合和样本 payload"),
        ('python ask.py "问题"', "普通 RAG 问答"),
        ('python ask.py --project Demo_Project "问题"', "按项目检索问答"),
        ('python ask.py --category problem "问题"', "按资料大类检索问答"),
        ('python ask.py --tag RAG "问题"', "按标签检索问答"),
        ('python add_note.py --category problem --title "标题" --content "内容"', "快速新增记录"),
        ('python project_report.py --project Demo_Project', "生成项目状态报告"),
        ('python time_report.py --project Demo_Project --mode daily', "生成日报"),
        ('python time_report.py --project Demo_Project --mode weekly', "生成周报"),
    ]

    for cmd, desc in commands:
        print(f"- {cmd}")
        print(f"  {desc}")


def print_next_steps(qdrant_info: dict):
    print("\n=== 下一步建议 ===")

    if not qdrant_info["ok"]:
        print("1. Qdrant 当前不可访问，请先启动 Docker 容器：")
        print("   docker start pkb-qdrant")
        print("2. 然后执行：python check_env.py")
        return

    if not qdrant_info["collection_exists"]:
        print("1. 当前集合不存在，请先执行：python ingest.py")
        print("2. 然后执行：python list_docs.py")
        return

    print("1. 新增项目记录时，优先使用 add_note.py。")
    print("2. 新增记录后，执行 python update_index.py 重新入库。")
    print("3. 每完成一个小阶段，可以执行 project_report.py 生成项目状态报告。")
    print("4. 每天或每周可以执行 time_report.py 生成日报/周报。")
    print("5. 后续可以进入 M1.15：增加 search_docs.py，专门搜索文档和片段。")


def main():
    print("个人项目秘书 + 数据知识库：系统状态总览")
    print(f"检查时间：{datetime.now().isoformat(timespec='seconds')}")
    print(f"知识库根目录：{KNOWLEDGE_ROOT}")

    print("\n=== 模型与服务配置 ===")
    print(f"Ollama 地址：{OLLAMA_URL}")
    print(f"主对话模型：{CHAT_MODEL}")
    print(f"向量模型：{EMBED_MODEL}")
    print(f"Qdrant 地址：{QDRANT_URL}")
    print(f"Qdrant 集合：{COLLECTION_NAME}")

    print("\n=== Ollama 状态 ===")
    ollama_ok, models = check_ollama()

    if not ollama_ok:
        print("[失败] Ollama 不可访问。")
    else:
        print("[成功] Ollama 可访问。")
        print(f"已安装模型：{models}")

        if model_exists(CHAT_MODEL, models):
            print(f"[成功] 主对话模型存在：{CHAT_MODEL}")
        else:
            print(f"[警告] 未发现主对话模型：{CHAT_MODEL}")

        if model_exists(EMBED_MODEL, models):
            print(f"[成功] 向量模型存在：{EMBED_MODEL}")
        else:
            print(f"[警告] 未发现向量模型：{EMBED_MODEL}")

    print("\n=== Qdrant / 知识库状态 ===")
    qdrant_info = check_qdrant()

    if not qdrant_info["ok"]:
        print("[失败] Qdrant 不可访问。")
        print(qdrant_info.get("error", ""))
    else:
        print("[成功] Qdrant 可访问。")

        if not qdrant_info["collection_exists"]:
            print(f"[提示] 集合不存在：{COLLECTION_NAME}")
        else:
            print(f"[成功] 集合存在：{COLLECTION_NAME}")
            print(f"向量片段数量：{qdrant_info['points_count']}")
            print(f"文档数量：{qdrant_info['docs_count']}")

            print("\n项目片段统计：")
            for project, count in sorted(qdrant_info["projects"].items()):
                print(f"- {project}: {count}")

            print("\n最近新增 / 修改文档：")
            for doc in qdrant_info["recent_docs"]:
                print(
                    f"- [{doc['project']}] {doc['doc_type']} | "
                    f"{doc['file_name']} | "
                    f"片段数：{doc['chunks']} | "
                    f"更新时间：{doc['updated_at']}"
                )
                print(f"  来源：{doc['source']}")

    print_available_commands()
    print_next_steps(qdrant_info)


if __name__ == "__main__":
    main()