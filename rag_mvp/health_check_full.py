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

from config import (
    OLLAMA_URL,
    CHAT_MODEL,
    EMBED_MODEL,
    QDRANT_URL,
    COLLECTION_NAME,
)


BASE_DIR = Path(__file__).parent.resolve()


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
    print_step("1. Check the Ollama API and model list")

    try:
        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"[Failure] Ollama API inaccessible:{e}")
        return False

    models = [m.get("name", "") for m in data.get("models", [])]

    print(f"[Success] Ollama API is accessible:{OLLAMA_URL}")
    print(f"Installed models:{models}")

    ok = True

    if model_exists(CHAT_MODEL, models):
        print(f"[Success] Main dialogue model exists:{CHAT_MODEL}")
    else:
        print(f"[Failure] The main dialogue model does not exist:{CHAT_MODEL}")
        ok = False

    if model_exists(EMBED_MODEL, models):
        print(f"[Success] Vector model exists:{EMBED_MODEL}")
    else:
        print(f"[Failure] Vector model does not exist:{EMBED_MODEL}")
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
    print_step("2. Check bge-m3 vector generation")

    try:
        vector = embed_text("This is a personal project secretary knowledge base vector health check.")
    except Exception as e:
        print(f"[Failure] Vector generation failed:{e}")
        return False, []

    if not vector:
        print("[Failure] The return vector is empty.")
        return False, []

    print("[Success] Vector generation is normal.")
    print(f"Vector dimension:{len(vector)}")

    return True, vector


def clean_response(text: str) -> str:
    return text.replace("<think>", "").replace("</think>", "").strip()


def check_chat_generation() -> bool:
    print_step("3. Check qwen3:8b text generation")

    prompt = "Please answer in English: Is the Personal Project Secretary Knowledge Base Health Check running? Do not provide your thought process."

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
        print(f"[Failure] Text generation failed:{e}")
        return False

    if not answer:
        print("[Failure] Text generation returned an empty string.")
        return False

    print("[Success] Text generation was successful.")
    print("Model's answer:")
    print(answer[:300])

    return True


def get_qdrant_client() -> QdrantClient:
    return QdrantClient(
        url=QDRANT_URL,
        check_compatibility=False,
        timeout=60,
    )


def check_qdrant_collection() -> bool:
    print_step("4. Check Qdrant and the main set")

    try:
        client = get_qdrant_client()
        collections = client.get_collections().collections
        names = [c.name for c in collections]
    except Exception as e:
        print(f"[Failure] Qdrant is inaccessible:{e}")
        return False

    print(f"[Success] Qdrant is accessible:{QDRANT_URL}")
    print(f"Existing collection:{names}")

    if COLLECTION_NAME not in names:
        print(f"[Failure] The main set does not exist:{COLLECTION_NAME}")
        return False

    try:
        info = client.get_collection(COLLECTION_NAME)
        print(f"[Success] The main set exists:{COLLECTION_NAME}")
        print(f"Number of vector fragments:{info.points_count}")
    except Exception as e:
        print(f"[Failure] Failed to read main collection information:{e}")
        return False
    finally:
        try:
            client.close()
        except Exception:
            pass

    return True


def check_qdrant_temp_write_search(vector: list[float]) -> bool:
    print_step("5. Check Qdrant temporary writes/retrievals/deletions")

    if not vector:
        print("[Failure] No vector available, temporary write test cannot be performed.")
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
            print("[failed] temporary collectionno retrieval results. ")
            return False

        print("[OK] temporary collection andretrieval . ")
        print(f"temporary collection:{temp_collection}")
        print(f"retrieval score:{points[0].score:.4f}")

        return True

    except Exception as e:
        print(f"[failed] Qdrant temporary  / retrievalfailed:{e}")
        return False

    finally:
        try:
            client.delete_collection(temp_collection)
            print(f"[completed] alreadydeletetemporary collection:{temp_collection}")
        except Exception:
            pass

        try:
            client.close()
        except Exception:
            pass


def run_subprocess_check(title: str, command: list[str]) -> bool:
    print_step(title)
    print("command:", " ".join(command))
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
        print(f"[failed] subprocess execution exception:{e}")
        return False

    if result.stdout:
        print(result.stdout)

    if result.stderr:
        print("[stderr]")
        print(result.stderr)

    if result.returncode != 0:
        print(f"[failed] return code:{result.returncode}")
        return False

    print("[OK] commandexecute . ")
    return True


def check_search_docs() -> bool:
    return run_subprocess_check(
        title="6. check search_docs.py search function",
        command=[
            sys.executable,
            "search_docs.py",
            "--project",
            "Demo_Project",
            "--limit",
            "1",
            " purpose stagemodel is ？",
        ],
    )


def check_ask_core() -> bool:
    print_step("7. check ask.py coreretrieval +  ")

    try:
        import ask

        question = " purpose stagemodel is ？"

        contexts = ask.search_context(
            question=question,
            limit=2,
            project="Demo_Project",
        )

        if not contexts:
            print("[failed] ask.search_context not retrieved records. ")
            return False

        print(f"[OK] ask.search_context retrieved recordscount:{len(contexts)}")

        answer = ask.generate_answer(question, contexts)

        if not answer:
            print("[failed] ask.generate_answer  is empty. ")
            return False

        print("[OK] ask.generate_answer  . ")
        print("answer preview:")
        print(answer[:500])

        return True

    except Exception as e:
        print(f"[failed] ask.py core checkfailed:{e}")
        return False


def main():
    print("Personal Project Secretary + Knowledge Base:full-chain health check")
    print(f"check time:{datetime.now().isoformat(timespec='seconds')}")
    print(f"working directory:{BASE_DIR}")
    print(f"Python:{sys.executable}")

    results = []

    ok = check_ollama_tags()
    results.append(("Ollama API andmodel list", ok))

    ok, vector = check_embedding()
    results.append(("bge-m3 embedding generation", ok))

    ok = check_chat_generation()
    results.append(("qwen3:8b  ", ok))

    ok = check_qdrant_collection()
    results.append(("Qdrant andmain collection", ok))

    ok = check_qdrant_temp_write_search(vector)
    results.append(("Qdrant temporary /retrieval/delete", ok))

    ok = check_search_docs()
    results.append(("search_docs.py search function", ok))

    ok = check_ask_core()
    results.append(("ask.py coreretrieval+ ", ok))

    print("\n" + "=" * 80)
    print("full-chain health checksummary")
    print("=" * 80)

    passed = 0

    for name, ok in results:
        if ok:
            passed += 1
            print(f"[passed] {name}")
        else:
            print(f"[failed] {name}")

    print("")
    print(f"passed count:{passed}/{len(results)}")

    if passed == len(results):
        print(" : , can . ")
    else:
        print(" :existsfailed items, please logs aboverepair. ")


if __name__ == "__main__":
    main()