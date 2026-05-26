from pathlib import Path
from datetime import datetime
import uuid
import os

# Prevent Python/qdrant-client from using system proxies for local services.
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

import requests
from tqdm import tqdm

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from config import (
    OLLAMA_URL,
    EMBED_MODEL,
    QDRANT_URL,
    COLLECTION_NAME,
    KNOWLEDGE_ROOT,
    CHUNK_MAX_CHARS,
)

def embed_text(text: str) -> list[float]:
    text = text.strip()
    if not text:
        raise ValueError("Cannot embed empty text")

    #   Ollama embedding  
    try:
        resp = requests.post(
            f"{OLLAMA_URL}/api/embed",
            json={"model": EMBED_MODEL, "input": text},
            timeout=120,
        )
        if resp.status_code == 200:
            data = resp.json()
            if "embeddings" in data and data["embeddings"]:
                return data["embeddings"][0]
    except Exception:
        pass

    #   Ollama embedding  
    resp = requests.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={"model": EMBED_MODEL, "prompt": text},
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["embedding"]


def split_markdown(text: str, max_chars: int = CHUNK_MAX_CHARS) -> list[str]:
    text = text.strip()
    if not text:
        return []

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks = []
    current = ""

    for paragraph in paragraphs:
        if len(current) + len(paragraph) + 2 <= max_chars:
            current = current + "\n\n" + paragraph if current else paragraph
        else:
            if current.strip():
                chunks.append(current.strip())
            current = paragraph

    if current.strip():
        chunks.append(current.strip())

    return chunks


def collect_markdown_files() -> list[Path]:
    """
    collectknowledge basein Markdown file. 

    rules:
    1. defaultcollectknowledge basein .md file. 
    2. skip .venv, backups, qdrant_storage, qdrant_local etc. directory. 
    3.   99_System/docs indescriptiondocument . 
    4. skip 99_System/rag_mvp in description scriptdirectorycontent. 
    """
    files = []

    skip_dir_names = {
        ".venv",
        "__pycache__",
        "backups",
        "qdrant_storage",
        "qdrant_local",
    }

    for path in KNOWLEDGE_ROOT.rglob("*.md"):
        parts = set(path.parts)

        if parts.intersection(skip_dir_names):
            continue

        rel_parts = path.relative_to(KNOWLEDGE_ROOT).parts

        #   99_System/docs indescriptiondocument 
        if len(rel_parts) >= 2 and rel_parts[0] == "99_System" and rel_parts[1] == "docs":
            files.append(path)
            continue

        # skip 99_System  directory,  script , backupdescriptionetc. 
        if rel_parts and rel_parts[0] == "99_System":
            continue

        files.append(path)

    return files


def infer_project_name(file_path: Path) -> str:
    """
    frompathinferproject name. 
    for example:
    <your-knowledge-root>\\01_Projects\\Demo_Project\\progress_log.md
    => Demo_Project
    """
    try:
        rel_parts = file_path.relative_to(KNOWLEDGE_ROOT).parts

        if len(rel_parts) >= 3 and rel_parts[0] == "01_Projects":
            return rel_parts[1]

        if len(rel_parts) >= 2:
            return rel_parts[0]

    except Exception:
        pass

    return "unknown"


def infer_doc_type(file_path: Path) -> str:
    """
    fromfile nameinferdocument type. 
    """
    stem = file_path.stem.lower()

    mapping = {
        "readme": "readme",
        "project_overview": "project_overview",
        "environment": "environment",
        "model_decisions": "model_decisions",
        "progress_log": "progress_log",
        "issues": "issues",
        "next_steps": "next_steps",
        "decisions": "decisions",
        "technical_notes": "technical_notes",
    }

    return mapping.get(stem, "note")


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """
    parse Markdown   YAML Frontmatter. 
     only lightweightparse, not  pyyaml. 
     :
    ---
    key: value
    tags: [a, b, c]
    ---
    """
    text = text.lstrip()

    if not text.startswith("---"):
        return {}, text

    parts = text.split("---", 2)

    if len(parts) < 3:
        return {}, text

    raw_meta = parts[1].strip()
    body = parts[2].strip()

    metadata = {}

    for line in raw_meta.splitlines():
        line = line.strip()

        if not line or ":" not in line:
            continue

        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()

        if value.startswith("[") and value.endswith("]"):
            items = value[1:-1].split(",")
            metadata[key] = [item.strip().strip('"').strip("'") for item in items if item.strip()]
        else:
            metadata[key] = value.strip('"').strip("'")

    return metadata, body


def infer_category(file_path: Path) -> str:
    """
    from directoryinferrecord category. 
    """
    try:
        rel_parts = file_path.relative_to(KNOWLEDGE_ROOT).parts

        if not rel_parts:
            return "unknown"

        root_dir = rel_parts[0]

        mapping = {
            "01_Projects": "project",
            "02_Knowledge": "knowledge",
            "03_Decisions": "decision",
            "04_Problems": "problem",
            "05_Summaries": "summary",
            "06_Attachments": "attachment",
            "99_System": "system",
        }
        return mapping.get(root_dir, "unknown")

    except Exception:
        return "unknown"


def collection_exists(client: QdrantClient, collection_name: str) -> bool:
    try:
        return client.collection_exists(collection_name)
    except Exception:
        existing = [c.name for c in client.get_collections().collections]
        return collection_name in existing


def ensure_collection(client: QdrantClient, vector_size: int):
    if not collection_exists(client, COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE,
            ),
        )
        print(f"collection created:{COLLECTION_NAME}")
    else:
        print(f"collection already exists:{COLLECTION_NAME}")


def make_point_id(source: str, chunk_index: int, chunk: str) -> str:
    raw = f"{source}:{chunk_index}:{chunk}"
    return str(uuid.uuid5(uuid.NAMESPACE_URL, raw))


def main():
    client = QdrantClient(
        url=QDRANT_URL,
        check_compatibility=False,
        timeout=60,
    )

    md_files = collect_markdown_files()
    print(f"found Markdown file count:{len(md_files)}")

    if not md_files:
        print("No indexable Markdown files were found. ")
        return

    all_items = []

    for file_path in md_files:
        try:
            text = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = file_path.read_text(encoding="utf-8-sig")

        frontmatter, body_text = parse_frontmatter(text)
		
        chunks = split_markdown(text)
        rel_path = str(file_path.relative_to(KNOWLEDGE_ROOT))

        if not chunks:
            print(f"skipempty fileornovalidcontentfile:{rel_path}")
            continue

        category = frontmatter.get("category") or infer_category(file_path)
        project_name = frontmatter.get("project") or infer_project_name(file_path)
        doc_type = frontmatter.get("doc_type") or frontmatter.get("type") or infer_doc_type(file_path)
        file_name = file_path.name
        title = frontmatter.get("title", "")
        tags = frontmatter.get("tags", [])

        updated_at = datetime.fromtimestamp(
            file_path.stat().st_mtime
        ).isoformat(timespec="seconds")

        for index, chunk in enumerate(chunks):
            all_items.append(
                {
                     "category": category,
                     "project": project_name,
                     "doc_type": doc_type,
                     "file_name": file_name,
                     "title": title,
                     "tags": tags,
                     "relative_path": rel_path,
                     "source": rel_path,
                     "chunk_index": index,
                     "text": chunk,
                     "updated_at": updated_at,
                }
            )

    if not all_items:
        print("All Markdown files are empty and cannot be indexed. Please add at least one valid Markdown file first. ")
        return

    first_vector = embed_text(all_items[0]["text"])
    vector_size = len(first_vector)
    print(f"vector dimension:{vector_size}")

    ensure_collection(client, vector_size)

    points = []

    for item in tqdm(all_items, desc=" and "):
        vector = embed_text(item["text"])

        point_id = make_point_id(
            source=item["source"],
            chunk_index=item["chunk_index"],
            chunk=item["text"],
        )

        points.append(
            PointStruct(
                id=point_id,
                vector=vector,
                payload={
                    "category": item["category"],
                    "project": item["project"],
                    "doc_type": item["doc_type"],
                    "file_name": item["file_name"],
                    "title": item["title"],
                    "tags": item["tags"],
                    "relative_path": item["relative_path"],
                    "source": item["source"],
                    "chunk_index": item["chunk_index"],
                    "text": item["text"],
                    "updated_at": item["updated_at"],
                },
            )
        )

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points,
    )

    print("Indexing completed. ")
    print(f"valid chunk count:{len(points)}")

    try:
        client.close()
    except Exception:
        pass


if __name__ == "__main__":
    main()