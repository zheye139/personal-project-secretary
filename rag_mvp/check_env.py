import os
import requests

from qdrant_client import QdrantClient

from config import (
    OLLAMA_URL,
    EMBED_MODEL,
    CHAT_MODEL,
    QDRANT_URL,
    COLLECTION_NAME,
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


def check_ollama():
    print("=== 检查 Ollama ===")

    try:
        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"[Failure] Unable to connect Ollama：{e}")
        return False

    data = resp.json()
    models = [m.get("name") for m in data.get("models", [])]

    print(f"[Successfully] Ollama is accessible:{OLLAMA_URL}")
    print(f"Installed models:{models}")

    ok = True

    if CHAT_MODEL not in models:
        print(f"[WARNING] No main dialogue model found:{CHAT_MODEL}")
        ok = False
    else:
        print(f"[Success] Main dialogue model exists:{CHAT_MODEL}")

    if EMBED_MODEL not in models:
        print(f"[Warning] No vector model found:{EMBED_MODEL}")
        ok = False
    else:
        print(f"[Success] Vector model exists:{EMBED_MODEL}")

    return ok


def check_qdrant():
    print("\n=== examine Qdrant ===")

    try:
        client = QdrantClient(
            url=QDRANT_URL,
            check_compatibility=False,
            timeout=60,
        )

        collections = client.get_collections().collections
        names = [c.name for c in collections]

        print(f"[Success] Qdrant is accessible:{QDRANT_URL}")
        print(f"Existing collection:{names}")

        if COLLECTION_NAME in names:
            print(f"[Successfully] The knowledge base collection exists:{COLLECTION_NAME}")
        else:
            print(f"[Note] The knowledge base collection does not currently exist.{COLLECTION_NAME}")
            print("      It will be created automatically after running python ingest.py.")

        try:
            client.close()
        except Exception:
            pass

        return True

    except Exception as e:
        print(f"[Failure] Unable to connect Qdrant：{e}")
        return False


def main():
    print("Personal Project Secretary + Data Knowledge Base: Environment Self-Check\n")

    ollama_ok = check_ollama()
    qdrant_ok = check_qdrant()

    print("\n=== Summarize ===")

    if ollama_ok and qdrant_ok:
        print("[Pass] The current environment can run the RAG minimal system.")
    else:
        print("[Not fully passed] Please fix the issues listed above.")


if __name__ == "__main__":
    main()