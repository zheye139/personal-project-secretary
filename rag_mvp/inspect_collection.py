import os
from collections import Counter

from qdrant_client import QdrantClient

from config import QDRANT_URL, COLLECTION_NAME


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


def main():
    client = QdrantClient(
        url=QDRANT_URL,
        check_compatibility=False,
        timeout=60,
    )

    if not client.collection_exists(COLLECTION_NAME):
        print(f"集合不存在：{COLLECTION_NAME}")
        print("请先运行：python ingest.py")
        return

    info = client.get_collection(COLLECTION_NAME)

    print("=== Qdrant 集合信息 ===")
    print(f"集合名称：{COLLECTION_NAME}")
    print(f"向量数量：{info.points_count}")
    print(f"向量配置：{info.config.params.vectors}")

    print("\n=== 示例数据 ===")

    points, _ = client.scroll(
        collection_name=COLLECTION_NAME,
        limit=10,
        with_payload=True,
        with_vectors=False,
    )

    if not points:
        print("集合中没有数据。")
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

        print(f"\n--- 片段 {i} ---")
        print(f"项目：{project}")
        print(f"文档类型：{doc_type}")
        print(f"文件名：{file_name}")
        print(f"来源：{source}")
        print(f"片段序号：{chunk_index}")
        print(f"更新时间：{updated_at}")

        text = payload.get("text", "")
        preview = text.replace("\n", " ")[:120]
        print(f"内容预览：{preview}...")

    print("\n=== 前 10 条样本统计 ===")
    print("项目统计：")
    for project, count in project_counter.items():
        print(f"- {project}: {count}")

    print("文档类型统计：")
    for doc_type, count in doc_type_counter.items():
        print(f"- {doc_type}: {count}")

    try:
        client.close()
    except Exception:
        pass


if __name__ == "__main__":
    main()