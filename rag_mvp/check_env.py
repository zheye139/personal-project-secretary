import requests

import vector_store_config
from config import (
    KNOWLEDGE_ROOT,
    OLLAMA_URL,
    EMBED_MODEL,
    CHAT_MODEL,
)

QDRANT_URL = vector_store_config.get_qdrant_url()
QDRANT_TIMEOUT = vector_store_config.get_qdrant_timeout()
COLLECTION_NAME = vector_store_config.get_collection_name()


# 避免访问本机服务时走系统代理
vector_store_config.configure_qdrant_environment()


def print_config_summary() -> None:
    print("=== Vector Store Configuration ===")
    print(f"KNOWLEDGE_ROOT: {KNOWLEDGE_ROOT}")
    print(f"OLLAMA_URL: {OLLAMA_URL}")
    print(f"CHAT_MODEL: {CHAT_MODEL}")
    print(f"EMBED_MODEL: {EMBED_MODEL}")
    print(f"QDRANT_URL: {QDRANT_URL}")
    print(f"QDRANT_TIMEOUT: {QDRANT_TIMEOUT}")
    print(f"QDRANT_COLLECTION: {COLLECTION_NAME}")
    print("")


def check_ollama():
    print("=== 检查 Ollama ===")

    try:
        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"[失败] 无法连接 Ollama：{e}")
        return False

    data = resp.json()
    models = [m.get("name") for m in data.get("models", [])]

    print(f"[成功] Ollama 可访问：{OLLAMA_URL}")
    print(f"已安装模型：{models}")

    ok = True

    if CHAT_MODEL not in models:
        print(f"[警告] 未发现主对话模型：{CHAT_MODEL}")
        ok = False
    else:
        print(f"[成功] 主对话模型存在：{CHAT_MODEL}")

    if EMBED_MODEL not in models:
        print(f"[警告] 未发现向量模型：{EMBED_MODEL}")
        ok = False
    else:
        print(f"[成功] 向量模型存在：{EMBED_MODEL}")

    return ok


def check_qdrant():
    print("\n=== 检查 Qdrant ===")

    try:
        client = vector_store_config.get_qdrant_client(timeout=60)

        collections = client.get_collections().collections
        names = [c.name for c in collections]

        print(f"[成功] Qdrant 可访问：{QDRANT_URL}")
        print(f"已有集合：{names}")

        if COLLECTION_NAME in names:
            print(f"[成功] 知识库集合存在：{COLLECTION_NAME}")
        else:
            print(f"[提示] 知识库集合暂不存在：{COLLECTION_NAME}")
            print("      运行 python ingest.py 后会自动创建。")

        try:
            client.close()
        except Exception:
            pass

        return True

    except Exception as e:
        print(f"[失败] 无法连接 Qdrant：{e}")
        return False


def main():
    print("个人项目秘书 + 数据知识库：环境自检\n")

    print_config_summary()

    ollama_ok = check_ollama()
    qdrant_ok = check_qdrant()

    print("\n=== 总结 ===")

    if ollama_ok and qdrant_ok:
        print("[通过] 当前环境可以运行 RAG 最小系统。")
    else:
        print("[未完全通过] 请根据上面的失败项进行修复。")


if __name__ == "__main__":
    main()
