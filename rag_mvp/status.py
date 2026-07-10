from collections import defaultdict
from datetime import datetime

import requests

import vector_store_config
from config import (
    OLLAMA_URL,
    CHAT_MODEL,
    EMBED_MODEL,
    KNOWLEDGE_ROOT,
)

QDRANT_URL = vector_store_config.get_qdrant_url()
QDRANT_TIMEOUT = vector_store_config.get_qdrant_timeout()
COLLECTION_NAME = vector_store_config.get_collection_name()


# 避免访问本机服务时走系统代理
vector_store_config.configure_qdrant_environment()


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
        client = vector_store_config.get_qdrant_client(timeout=60)

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
    """
    打印当前系统可用命令。

    M1：基础 RAG 知识库能力。
    M2：个人秘书能力增强脚本。
    """
    print("\n=== 当前可用命令 ===")

    command_groups = {
        "基础环境与状态": [
            ("python check_env.py", "检查 Ollama / Qdrant / 模型环境"),
            ("python health_check_full.py", "执行全链路健康检查"),
            ("python status.py", "查看系统状态总览"),
            ("python list_docs.py", "列出已入库文档"),
            ("python inspect_collection.py", "查看 Qdrant 集合和样本 payload"),
        ],
        "入库与索引": [
            ("python ingest.py", "重新入库 Markdown 文档"),
            ("python update_index.py", "一键检查环境 + 重新入库 + 列出文档"),
            ("python rebuild_index.py", "预览安全重建 Qdrant 索引"),
            ("python rebuild_index.py --execute", "执行安全重建 Qdrant 索引"),
        ],
        "问答与搜索": [
            ('python ask.py "问题"', "普通 RAG 问答"),
            (
                'python ask.py --project Personal_Project_Assistant "问题"',
                "按项目检索问答",
            ),
            (
                'python ask.py --category problem "问题"',
                "按资料大类检索问答",
            ),
            (
                'python ask.py --tag RAG "问题"',
                "按标签检索问答",
            ),
            (
                'python search_docs.py "关键词" --show-text',
                "搜索知识库片段，不调用 qwen3:8b",
            ),
        ],
        "记录新增与整理": [
            (
                'python add_note.py --category problem --title "标题" --content "内容"',
                "快速新增记录",
            ),
            ("python inbox_import.py", "预览导入 00_Inbox 中的 Markdown"),
            ("python inbox_import.py --execute", "执行 Inbox Markdown 自动归档"),
            (
                "python project_template.py --project New_Project",
                "生成新项目知识库模板",
            ),
            (
                "python archive_project.py --project Test_Project",
                "预览归档项目",
            ),
            (
                "python archive_project.py --project Test_Project --execute",
                "执行项目归档",
            ),
        ],
        "报告生成": [
            (
                "python project_report.py --project Personal_Project_Assistant",
                "生成项目状态报告",
            ),
            (
                "python time_report.py --project Personal_Project_Assistant --mode daily",
                "生成日报",
            ),
            (
                "python time_report.py --project Personal_Project_Assistant --mode weekly",
                "生成周报",
            ),
        ],
        "M2 个人秘书能力": [
            (
                "python next_action.py --project Personal_Project_Assistant",
                "提取项目下一步行动项",
            ),
            (
                "python project_brief.py --project Personal_Project_Assistant",
                "生成项目简报",
            ),
            (
                "python multi_project_status.py",
                "汇总多个项目状态",
            ),
            (
                "python priority_advisor.py",
                "生成项目优先级建议",
            ),
            (
                "python review_assistant.py --project Personal_Project_Assistant",
                "复盘项目记录，指出遗漏和风险",
            ),
            (
                "python secretary_report.py",
                "生成个人秘书汇报",
            ),
            (
                "python milestone_closeout.py --milestone M2",
                "生成 M2 阶段封版报告",
            ),
        ],
        "规范检查与维护": [
            ("python validate_kb.py", "检查知识库 Markdown 规范"),
            (
                "python validate_kb.py --write-report",
                "生成知识库规范检查报告",
            ),
            (
                "python repair_frontmatter.py",
                "预览 Frontmatter 修复",
            ),
            (
                "python repair_frontmatter.py --execute",
                "执行 Frontmatter 批量修复",
            ),
            (
                "python cleanup_qa_logs.py",
                "预览清理失败/重复问答记录",
            ),
            (
                "python cleanup_qa_logs.py --mode all --execute",
                "归档失败/重复问答记录",
            ),
        ],
        "备份与导出": [
            ("python backup_kb.py", "备份完整知识库"),
            (
                "python export_project.py --project Personal_Project_Assistant",
                "导出指定项目资料包",
            ),
            (
                "python export_project.py --project Personal_Project_Assistant --no-summaries",
                "导出项目资料包，不包含总结类文件",
            ),
        ],
    }

    for group_name, commands in command_groups.items():
        print(f"\n## {group_name}")

        for cmd, desc in commands:
            print(f"- {cmd}")
            print(f"  {desc}")


def print_next_steps(qdrant_info: dict):
    """
    根据当前系统状态给出下一步建议。

    这里已经加入 M2 个人秘书能力工作流。
    """
    print("\n=== 下一步建议 ===")

    if not qdrant_info["ok"]:
        print("1. Qdrant 当前不可访问，请先启动 Docker 容器：")
        print("   docker start pkb-qdrant")
        print("2. 然后执行：")
        print("   python check_env.py")
        return

    if not qdrant_info["collection_exists"]:
        print("1. 当前集合不存在，请先执行：")
        print("   python ingest.py")
        print("2. 然后执行：")
        print("   python list_docs.py")
        return

    print("## 日常基础流程")
    print("1. 新增项目记录时，优先使用 add_note.py 或 inbox_import.py。")
    print("2. 新增或修改 Markdown 后，执行：")
    print("   python update_index.py")
    print("3. 查询前如果不确定检索效果，先执行：")
    print('   python search_docs.py "关键词" --show-text')

    print("\n## M2 个人秘书推荐流程")
    print("如果你想查看当前整体工作情况，建议按顺序执行：")
    print("1. python next_action.py --project Personal_Project_Assistant")
    print("2. python project_brief.py --project Personal_Project_Assistant")
    print("3. python multi_project_status.py")
    print("4. python priority_advisor.py")
    print("5. python review_assistant.py --project Personal_Project_Assistant")
    print("6. python secretary_report.py")
    print("7. python update_index.py")

    print("\n## 阶段维护建议")
    print("1. 每完成一个小阶段，执行：")
    print("   python project_report.py --project Personal_Project_Assistant")
    print("2. 每周执行：")
    print("   python time_report.py --project Personal_Project_Assistant --mode weekly")
    print("3. 每周或重要修改前执行：")
    print("   python backup_kb.py")
    print("4. 每个阶段结束时执行：")
    print("   python milestone_closeout.py --milestone M2")

    print("\n## 下一阶段建议")
    print("M2.8 当前任务是增强 status.py、commands.md、README 等入口文档。")
    print("完成后可以考虑进入 M3：任务追踪与自动化调度能力。")


def main():
    print("个人项目秘书 + 数据知识库：系统状态总览")
    print(f"检查时间：{datetime.now().isoformat(timespec='seconds')}")
    print(f"知识库根目录：{KNOWLEDGE_ROOT}")

    print("\n=== 模型与服务配置 ===")
    print(f"Ollama 地址：{OLLAMA_URL}")
    print(f"主对话模型：{CHAT_MODEL}")
    print(f"向量模型：{EMBED_MODEL}")
    print(f"Qdrant 地址：{QDRANT_URL}")
    print(f"Qdrant timeout：{QDRANT_TIMEOUT}")
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
