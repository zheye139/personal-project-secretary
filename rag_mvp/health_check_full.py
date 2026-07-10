import os
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

import requests
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

import vector_store_config
from config import (
    OLLAMA_URL,
    CHAT_MODEL,
    EMBED_MODEL,
)

QDRANT_URL = vector_store_config.get_qdrant_url()
COLLECTION_NAME = vector_store_config.get_collection_name()


BASE_DIR = Path(__file__).parent.resolve()


# 避免访问本机服务时走系统代理
vector_store_config.configure_qdrant_environment()


def print_step(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def model_exists(target: str, models: list[str]) -> bool:
    if target in models:
        return True

    if ":" not in target and f"{target}:latest" in models:
        return True

    return False


def check_ollama_tags() -> bool:
    print_step("1. 检查 Ollama API 与模型列表")

    try:
        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"[失败] Ollama API 不可访问：{e}")
        return False

    models = [m.get("name", "") for m in data.get("models", [])]

    print(f"[成功] Ollama API 可访问：{OLLAMA_URL}")
    print(f"已安装模型：{models}")

    ok = True

    if model_exists(CHAT_MODEL, models):
        print(f"[成功] 主对话模型存在：{CHAT_MODEL}")
    else:
        print(f"[失败] 主对话模型不存在：{CHAT_MODEL}")
        ok = False

    if model_exists(EMBED_MODEL, models):
        print(f"[成功] 向量模型存在：{EMBED_MODEL}")
    else:
        print(f"[失败] 向量模型不存在：{EMBED_MODEL}")
        ok = False

    return ok


def embed_text(text: str) -> list[float]:
    text = text.strip()

    try:
        resp = requests.post(
            f"{OLLAMA_URL}/api/embed",
            json={
                "model": EMBED_MODEL,
                "input": text,
            },
            timeout=120,
        )

        if resp.status_code == 200:
            data = resp.json()
            if "embeddings" in data and data["embeddings"]:
                return data["embeddings"][0]
    except Exception:
        pass

    resp = requests.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={
            "model": EMBED_MODEL,
            "prompt": text,
        },
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["embedding"]


def check_embedding() -> tuple[bool, list[float]]:
    print_step("2. 检查 bge-m3 向量生成")

    try:
        vector = embed_text("这是一次个人项目秘书知识库向量健康检查。")
    except Exception as e:
        print(f"[失败] 向量生成失败：{e}")
        return False, []

    if not vector:
        print("[失败] 返回向量为空。")
        return False, []

    print("[成功] 向量生成正常。")
    print(f"向量维度：{len(vector)}")

    return True, vector


def clean_response(text: str) -> str:
    return text.replace("<think>", "").replace("</think>", "").strip()


def check_chat_generation() -> bool:
    print_step("3. 检查 qwen3:8b 文本生成")

    prompt = "请用一句中文回答：个人项目秘书知识库健康检查是否正在运行？不要输出思考过程。"

    try:
        resp = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": CHAT_MODEL,
                "prompt": prompt,
                "stream": False,
            },
            timeout=300,
        )
        resp.raise_for_status()
        data = resp.json()
        answer = clean_response(data.get("response", ""))
    except Exception as e:
        print(f"[失败] 文本生成失败：{e}")
        return False

    if not answer:
        print("[失败] 文本生成返回为空。")
        return False

    print("[成功] 文本生成正常。")
    print("模型回答：")
    print(answer[:300])

    return True


def get_qdrant_client() -> QdrantClient:
    return vector_store_config.get_qdrant_client(timeout=60)


def check_qdrant_collection() -> bool:
    print_step("4. 检查 Qdrant 与主集合")

    try:
        client = get_qdrant_client()
        collections = client.get_collections().collections
        names = [c.name for c in collections]
    except Exception as e:
        print(f"[失败] Qdrant 不可访问：{e}")
        return False

    print(f"[成功] Qdrant 可访问：{QDRANT_URL}")
    print(f"已有集合：{names}")

    if COLLECTION_NAME not in names:
        print(f"[失败] 主集合不存在：{COLLECTION_NAME}")
        return False

    try:
        info = client.get_collection(COLLECTION_NAME)
        print(f"[成功] 主集合存在：{COLLECTION_NAME}")
        print(f"向量片段数量：{info.points_count}")
    except Exception as e:
        print(f"[失败] 读取主集合信息失败：{e}")
        return False
    finally:
        try:
            client.close()
        except Exception:
            pass

    return True


def check_qdrant_temp_write_search(vector: list[float]) -> bool:
    print_step("5. 检查 Qdrant 临时写入 / 检索 / 删除")

    if not vector:
        print("[失败] 没有可用向量，无法进行临时写入测试。")
        return False

    temp_collection = f"health_check_tmp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    vector_size = len(vector)

    client = get_qdrant_client()

    try:
        client.create_collection(
            collection_name=temp_collection,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE,
            ),
        )

        point_id = str(uuid.uuid4())

        client.upsert(
            collection_name=temp_collection,
            points=[
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "text": "health check temp point",
                        "created_at": datetime.now().isoformat(timespec="seconds"),
                    },
                )
            ],
        )

        if hasattr(client, "query_points"):
            response = client.query_points(
                collection_name=temp_collection,
                query=vector,
                limit=1,
                with_payload=True,
            )
            points = response.points
        else:
            points = client.search(
                collection_name=temp_collection,
                query_vector=vector,
                limit=1,
            )

        if not points:
            print("[失败] 临时集合检索无结果。")
            return False

        print("[成功] 临时集合写入和检索正常。")
        print(f"临时集合：{temp_collection}")
        print(f"检索分数：{points[0].score:.4f}")

        return True

    except Exception as e:
        print(f"[失败] Qdrant 临时写入 / 检索失败：{e}")
        return False

    finally:
        try:
            client.delete_collection(temp_collection)
            print(f"[完成] 已删除临时集合：{temp_collection}")
        except Exception:
            pass

        try:
            client.close()
        except Exception:
            pass


def run_subprocess_check(title: str, command: list[str]) -> bool:
    print_step(title)
    print("执行命令：", " ".join(command))
    print("")

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    try:
        result = subprocess.run(
            command,
            cwd=BASE_DIR,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=600,
            env=env,
        )
    except Exception as e:
        print(f"[失败] 子进程执行异常：{e}")
        return False

    if result.stdout:
        print(result.stdout)

    if result.stderr:
        print("[stderr]")
        print(result.stderr)

    if result.returncode != 0:
        print(f"[失败] 返回码：{result.returncode}")
        return False

    print("[成功] 命令执行正常。")
    return True


def check_search_docs() -> bool:
    return run_subprocess_check(
        title="6. 检查 search_docs.py 搜索功能",
        command=[
            sys.executable,
            "search_docs.py",
            "--project",
            "Personal_Project_Assistant",
            "--limit",
            "1",
            "当前项目的第一阶段模型方案是什么？",
        ],
    )


def check_ask_core() -> bool:
    print_step("7. 检查 ask.py 核心检索 + 生成函数")

    try:
        import ask

        question = "当前项目的第一阶段模型方案是什么？"

        contexts = ask.search_context(
            question=question,
            limit=2,
            project="Personal_Project_Assistant",
        )

        if not contexts:
            print("[失败] ask.search_context 未检索到资料。")
            return False

        print(f"[成功] ask.search_context 检索到资料数量：{len(contexts)}")

        answer = ask.generate_answer(question, contexts)

        if not answer:
            print("[失败] ask.generate_answer 返回为空。")
            return False

        print("[成功] ask.generate_answer 正常。")
        print("回答预览：")
        print(answer[:500])

        return True

    except Exception as e:
        print(f"[失败] ask.py 核心函数检查失败：{e}")
        return False


def main():
    print("个人项目秘书 + 数据知识库：全链路健康检查")
    print(f"检查时间：{datetime.now().isoformat(timespec='seconds')}")
    print(f"工作目录：{BASE_DIR}")
    print(f"Python：{sys.executable}")

    results = []

    ok = check_ollama_tags()
    results.append(("Ollama API 与模型列表", ok))

    ok, vector = check_embedding()
    results.append(("bge-m3 向量生成", ok))

    ok = check_chat_generation()
    results.append(("qwen3:8b 文本生成", ok))

    ok = check_qdrant_collection()
    results.append(("Qdrant 与主集合", ok))

    ok = check_qdrant_temp_write_search(vector)
    results.append(("Qdrant 临时写入/检索/删除", ok))

    ok = check_search_docs()
    results.append(("search_docs.py 搜索功能", ok))

    ok = check_ask_core()
    results.append(("ask.py 核心检索+生成", ok))

    print("\n" + "=" * 80)
    print("全链路健康检查总结")
    print("=" * 80)

    passed = 0

    for name, ok in results:
        if ok:
            passed += 1
            print(f"[通过] {name}")
        else:
            print(f"[失败] {name}")

    print("")
    print(f"通过数量：{passed}/{len(results)}")

    if passed == len(results):
        print("结论：系统全链路健康，可以正常使用。")
    else:
        print("结论：存在失败项，请根据上方日志修复。")


if __name__ == "__main__":
    main()
