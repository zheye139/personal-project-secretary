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


# Prevent local service requests from going through system proxies.
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
    """
     available commands. 

    M1:basic RAG knowledge basecapability. 
    M2:personal secretary capabilities script. 
    """
    print("\n===  available commands ===")

    command_groups = {
        "basic and ": [
            ("python check_env.py", "check Ollama / Qdrant / model "),
            ("python health_check_full.py", "executefull-chain health check"),
            ("python status.py", "viewsystem status overview"),
            ("python list_docs.py", "listalready document"),
            ("python inspect_collection.py", "view Qdrant collectionand  payload"),
        ],
        " and ": [
            ("python ingest.py", "re-  Markdown document"),
            ("python update_index.py", "one-clickcheck  + re-  + listdocument"),
            ("python rebuild_index.py", "previewsafe rebuild Qdrant  "),
            ("python rebuild_index.py --execute", "executesafe rebuild Qdrant  "),
        ],
        "question answeringandsearch": [
            ('python ask.py "issue"', "  RAG question answering"),
            (
                'python ask.py --project Personal_Project_Assistant "issue"',
                " retrievalquestion answering",
            ),
            (
                'python ask.py --category problem "issue"',
                " record categoryretrievalquestion answering",
            ),
            (
                'python ask.py --tag RAG "issue"',
                " tagsretrievalquestion answering",
            ),
            (
                'python search_docs.py " " --show-text',
                "searchknowledge basechunk, notcall qwen3:8b",
            ),
        ],
        "recordadd and ": [
            (
                'python add_note.py --category problem --title "title" --content "content"',
                "quicklyaddrecord",
            ),
            ("python inbox_import.py", "previewimport 00_Inbox in Markdown"),
            ("python inbox_import.py --execute", "execute Inbox Markdown automaticarchive"),
            (
                "python project_template.py --project New_Project",
                " knowledge base ",
            ),
            (
                "python archive_project.py --project Test_Project",
                "previewarchive ",
            ),
            (
                "python archive_project.py --project Test_Project --execute",
                "execute project archive",
            ),
        ],
        "report ": [
            (
                "python project_report.py --project Personal_Project_Assistant",
                " project status report",
            ),
            (
                "python time_report.py --project Personal_Project_Assistant --mode daily",
                " daily report",
            ),
            (
                "python time_report.py --project Personal_Project_Assistant --mode weekly",
                " weekly report",
            ),
        ],
        "M2 personal secretary capabilities": [
            (
                "python next_action.py --project Personal_Project_Assistant",
                " next action items",
            ),
            (
                "python project_brief.py --project Personal_Project_Assistant",
                " project brief",
            ),
            (
                "python multi_project_status.py",
                " project status",
            ),
            (
                "python priority_advisor.py",
                " project priority advice",
            ),
            (
                "python review_assistant.py --project Personal_Project_Assistant",
                " project records, identify and risks",
            ),
            (
                "python secretary_report.py",
                " personal secretary report",
            ),
            (
                "python milestone_closeout.py --milestone M2",
                "  M2 milestone closeout report",
            ),
        ],
        "validation check andmaintenance": [
            ("python validate_kb.py", "check knowledge base Markdown standard"),
            (
                "python validate_kb.py --write-report",
                " knowledge basestandardcheck report",
            ),
            (
                "python repair_frontmatter.py",
                "preview Frontmatter repair",
            ),
            (
                "python repair_frontmatter.py --execute",
                "execute Frontmatter batchrepair",
            ),
            (
                "python cleanup_qa_logs.py",
                "previewcleanupfailed/duplicateQA log",
            ),
            (
                "python cleanup_qa_logs.py --mode all --execute",
                "archivefailed/duplicateQA log",
            ),
        ],
        "backupandexport": [
            ("python backup_kb.py", "backupcompleteknowledge base"),
            (
                "python export_project.py --project Personal_Project_Assistant",
                "export specified project records ",
            ),
            (
                "python export_project.py --project Personal_Project_Assistant --no-summaries",
                "export project records , not summary file",
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
     system statusprovidenext-step recommendations. 

    thisinalready  M2 personal secretary capabilities . 
    """
    print("\n=== next-step recommendations ===")

    if not qdrant_info["ok"]:
        print("1. Qdrant  not accessible, please first  Docker  :")
        print("   docker start pkb-qdrant")
        print("2.  execute:")
        print("   python check_env.py")
        return

    if not qdrant_info["collection_exists"]:
        print("1.  collection does not exist, please firstexecute:")
        print("   python ingest.py")
        print("2.  execute:")
        print("   python list_docs.py")
        return

    print("##  basic ")
    print("1. add project records , prioritize  add_note.py or inbox_import.py. ")
    print("2. add or  Markdown  , execute:")
    print("   python update_index.py")
    print("3.  ifnot retrieval quality, firstexecute:")
    print('   python search_docs.py " " --show-text')

    print("\n## M2 personal secretary ")
    print("if view , recommendations execute:")
    print("1. python next_action.py --project Personal_Project_Assistant")
    print("2. python project_brief.py --project Personal_Project_Assistant")
    print("3. python multi_project_status.py")
    print("4. python priority_advisor.py")
    print("5. python review_assistant.py --project Personal_Project_Assistant")
    print("6. python secretary_report.py")
    print("7. python update_index.py")

    print("\n## stagemaintenancerecommendations")
    print("1.  completeda stage, execute:")
    print("   python project_report.py --project Personal_Project_Assistant")
    print("2. weeklyexecute:")
    print("   python time_report.py --project Personal_Project_Assistant --mode weekly")
    print("3. weeklyor execute:")
    print("   python backup_kb.py")
    print("4. eachstageend execute:")
    print("   python milestone_closeout.py --milestone M2")

    print("\n## next stagerecommendations")
    print("M2.8  tasksis  status.py, commands.md, README etc. document. ")
    print("completed can enter M3:tasks andautomatic capability. ")


def main():
    print("Personal Project Secretary + Knowledge Base:system status overview")
    print(f"check time:{datetime.now().isoformat(timespec='seconds')}")
    print(f"knowledge base root:{KNOWLEDGE_ROOT}")

    print("\n=== modeland configuration ===")
    print(f"Ollama  :{OLLAMA_URL}")
    print(f"chat model:{CHAT_MODEL}")
    print(f"embedding model:{EMBED_MODEL}")
    print(f"Qdrant  :{QDRANT_URL}")
    print(f"Qdrant collection:{COLLECTION_NAME}")

    print("\n=== Ollama   ===")
    ollama_ok, models = check_ollama()

    if not ollama_ok:
        print("[failed] Ollama not accessible. ")
    else:
        print("[OK] Ollama accessible. ")
        print(f"installedmodel:{models}")

        if model_exists(CHAT_MODEL, models):
            print(f"[OK] chat modelexists:{CHAT_MODEL}")
        else:
            print(f"[ ] not foundchat model:{CHAT_MODEL}")

        if model_exists(EMBED_MODEL, models):
            print(f"[OK] embedding modelexists:{EMBED_MODEL}")
        else:
            print(f"[ ] not foundembedding model:{EMBED_MODEL}")

    print("\n=== Qdrant / knowledge base  ===")
    qdrant_info = check_qdrant()

    if not qdrant_info["ok"]:
        print("[failed] Qdrant not accessible. ")
        print(qdrant_info.get("error", ""))
    else:
        print("[OK] Qdrant accessible. ")

        if not qdrant_info["collection_exists"]:
            print(f"[ ] collection does not exist:{COLLECTION_NAME}")
        else:
            print(f"[OK] collectionexists:{COLLECTION_NAME}")
            print(f" chunk count:{qdrant_info['points_count']}")
            print(f"document count:{qdrant_info['docs_count']}")

            print("\n chunkstatistics:")
            for project, count in sorted(qdrant_info["projects"].items()):
                print(f"- {project}: {count}")

            print("\nrecentadd /  document:")
            for doc in qdrant_info["recent_docs"]:
                print(
                    f"- [{doc['project']}] {doc['doc_type']} | "
                    f"{doc['file_name']} | "
                    f"chunk :{doc['chunks']} | "
                    f"updated at:{doc['updated_at']}"
                )
                print(f"  source:{doc['source']}")

    print_available_commands()
    print_next_steps(qdrant_info)


if __name__ == "__main__":
    main()