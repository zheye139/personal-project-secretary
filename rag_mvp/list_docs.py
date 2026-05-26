import os
from collections import defaultdict

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

    docs = defaultdict(
        lambda: {
            "chunks": 0,
            "project": "",
            "doc_type": "",
            "file_name": "",
            "source": "",
            "updated_at": "",
        }
    )

    offset = None
    total = 0

    while True:
        points, offset = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=100,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )

        if not points:
            break

        for point in points:
            payload = point.payload or {}

            source = payload.get("source", "unknown")
            docs[source]["chunks"] += 1
            docs[source]["project"] = payload.get("project", "")
            docs[source]["doc_type"] = payload.get("doc_type", "")
            docs[source]["file_name"] = payload.get("file_name", "")
            docs[source]["source"] = source
            docs[source]["updated_at"] = payload.get("updated_at", "")

            total += 1

        if offset is None:
            break

    print("=== already document list ===")
    print(f"collection name:{COLLECTION_NAME}")
    print(f"total chunk count:{total}")
    print(f"document count:{len(docs)}")

    by_project = defaultdict(list)

    for source, info in docs.items():
        by_project[info["project"]].append(info)

    for project, items in sorted(by_project.items()):
        print(f"\n##  :{project}")

        for info in sorted(items, key=lambda x: x["source"]):
            print(
                f"- {info['doc_type']} | "
                f"{info['file_name']} | "
                f"chunk :{info['chunks']} | "
                f"updated at:{info['updated_at']}"
            )
            print(f"  source:{info['source']}")

    try:
        client.close()
    except Exception:
        pass


if __name__ == "__main__":
    main()