import os
from collections import Counter

from qdrant_client import QdrantClient

from config import QDRANT_URL, COLLECTION_NAME


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


def main():
    client = QdrantClient(
        url=QDRANT_URL,
        check_compatibility=False,
        timeout=60,
    )

    if not client.collection_exists(COLLECTION_NAME):
        print(f"collection does not exist:{COLLECTION_NAME}")
        print("please first :python ingest.py")
        return

    info = client.get_collection(COLLECTION_NAME)

    print("=== Qdrant collection  ===")
    print(f"collection name:{COLLECTION_NAME}")
    print(f"vector count:{info.points_count}")
    print(f"vector configuration:{info.config.params.vectors}")

    print("\n===   ===")

    points, _ = client.scroll(
        collection_name=COLLECTION_NAME,
        limit=10,
        with_payload=True,
        with_vectors=False,
    )

    if not points:
        print("collection contains no data. ")
        return

    project_counter = Counter()
    doc_type_counter = Counter()

    for i, point in enumerate(points, start=1):
        payload = point.payload or {}

        project = payload.get("project", "")
        doc_type = payload.get("doc_type", "")
        file_name = payload.get("file_name", "")
        source = payload.get("source", "")
        chunk_index = payload.get("chunk_index", "")
        updated_at = payload.get("updated_at", "")

        project_counter[project] += 1
        doc_type_counter[doc_type] += 1

        print(f"\n--- chunk {i} ---")
        print(f" :{project}")
        print(f"document type:{doc_type}")
        print(f"file name:{file_name}")
        print(f"source:{source}")
        print(f"chunk index:{chunk_index}")
        print(f"updated at:{updated_at}")

        text = payload.get("text", "")
        preview = text.replace("\n", " ")[:120]
        print(f"content preview:{preview}...")

    print("\n===   10  statistics ===")
    print(" statistics:")
    for project, count in project_counter.items():
        print(f"- {project}: {count}")

    print("document type statistics:")
    for doc_type, count in doc_type_counter.items():
        print(f"- {doc_type}: {count}")

    try:
        client.close()
    except Exception:
        pass


if __name__ == "__main__":
    main()