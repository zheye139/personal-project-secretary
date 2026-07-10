from collections import defaultdict

import vector_store_config

QDRANT_URL = vector_store_config.get_qdrant_url()
COLLECTION_NAME = vector_store_config.get_collection_name()


# 避免访问本机服务时走系统代理
vector_store_config.configure_qdrant_environment()


def main():
    client = vector_store_config.get_qdrant_client(timeout=60)

    if not client.collection_exists(COLLECTION_NAME):
        print(f"集合不存在：{COLLECTION_NAME}")
        print("请先运行：python ingest.py")
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

    print("=== 已入库文档列表 ===")
    print(f"集合名称：{COLLECTION_NAME}")
    print(f"片段总数：{total}")
    print(f"文档数量：{len(docs)}")

    by_project = defaultdict(list)

    for source, info in docs.items():
        by_project[info["project"]].append(info)

    for project, items in sorted(by_project.items()):
        print(f"\n## 项目：{project}")

        for info in sorted(items, key=lambda x: x["source"]):
            print(
                f"- {info['doc_type']} | "
                f"{info['file_name']} | "
                f"片段数：{info['chunks']} | "
                f"更新时间：{info['updated_at']}"
            )
            print(f"  来源：{info['source']}")

    try:
        client.close()
    except Exception:
        pass


if __name__ == "__main__":
    main()
