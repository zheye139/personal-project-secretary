import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import requests

from config import (
    QDRANT_URL,
    COLLECTION_NAME,
    KNOWLEDGE_ROOT,
    BACKUP_DIR,
)


BASE_DIR = Path(__file__).parent.resolve()


def run_command(title: str, command: list[str], capture: bool = False) -> subprocess.CompletedProcess:
    print("\n" + "=" * 80)
    print(f"start:{title}")
    print("=" * 80)
    print("command:", " ".join(command))
    print("")

    result = subprocess.run(
        command,
        cwd=BASE_DIR,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=capture,
    )

    if capture:
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("[stderr]")
            print(result.stderr)

    if result.returncode != 0:
        print(f"[failed] {title}")
        print(f"return code:{result.returncode}")
    else:
        print(f"[completed] {title}")

    return result


def save_snapshot() -> Path:
    """
    inrebuild save  list_docs.py  . 
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    snapshot_dir = BACKUP_DIR / "index_rebuild_snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    snapshot_path = snapshot_dir / f"{timestamp}_before_rebuild_list_docs.md"

    result = subprocess.run(
        [sys.executable, "list_docs.py"],
        cwd=BASE_DIR,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
    )

    lines = [
        "---",
        f"title: rebuild document  {timestamp}",
        f"created: {datetime.now().isoformat(timespec='seconds')}",
        "category: summary",
        "project: Demo_Project",
        "doc_type: index_rebuild_snapshot",
        "tags: [ rebuild, list_docs, auto generated, M1.28]",
        "---",
        "",
        "# rebuild document ",
        "",
        f"generated at:{datetime.now().isoformat(timespec='seconds')}",
        "",
        "```text",
        result.stdout,
    ]

    if result.stderr:
        lines.extend(
            [
                "",
                "[stderr]",
                result.stderr,
            ]
        )

    lines.extend(
        [
            "```",
            "",
        ]
    )

    snapshot_path.write_text("\n".join(lines), encoding="utf-8")
    return snapshot_path


def collection_exists() -> bool:
    url = f"{QDRANT_URL}/collections/{COLLECTION_NAME}/exists"

    try:
        resp = requests.get(url, timeout=20)
        if resp.status_code == 200:
            data = resp.json()
            return bool(data.get("result", {}).get("exists", False))
    except Exception:
        pass

    #  :read collections  
    resp = requests.get(f"{QDRANT_URL}/collections", timeout=20)
    resp.raise_for_status()
    data = resp.json()

    collections = data.get("result", {}).get("collections", [])
    names = [item.get("name") for item in collections]
    return COLLECTION_NAME in names


def delete_collection() -> None:
    url = f"{QDRANT_URL}/collections/{COLLECTION_NAME}"
    resp = requests.delete(url, timeout=120)

    if resp.status_code in {200, 202}:
        print(f"[completed] alreadydeletecollection:{COLLECTION_NAME}")
        return

    if resp.status_code == 404:
        print(f"[ ] collection does not exist, no delete:{COLLECTION_NAME}")
        return

    print(f"[failed] deletecollectionfailed,  :{resp.status_code}")
    print(resp.text)
    resp.raise_for_status()


def main():
    parser = argparse.ArgumentParser(
        description="Personal Project Secretary + Knowledge Base:safe rebuild Qdrant  "
    )

    parser.add_argument(
        "--execute",
        action="store_true",
        help="actuallyexecutedeletecollectionandrebuild . defaultonlypreview. ",
    )

    parser.add_argument(
        "--skip-snapshot",
        action="store_true",
        help="skiprebuild  list_docs  . ",
    )

    args = parser.parse_args()

    print("Personal Project Secretary + Knowledge Base: rebuildtool")
    print(f"knowledge base root:{KNOWLEDGE_ROOT}")
    print(f"Qdrant  :{QDRANT_URL}")
    print(f"collection name:{COLLECTION_NAME}")
    print(f"executerebuild:{args.execute}")

    print("\nexecute :")
    print("1.   python check_env.py")
    print("2. saverebuild  list_docs  ")
    print(f"3. delete Qdrant collection:{COLLECTION_NAME}")
    print("4.   python ingest.py re- ")
    print("5.   python list_docs.py  ")

    if not args.execute:
        print("\n aspreview mode,  deletecollection,  rebuild . ")
        print("After confirmation, run:")
        print("python rebuild_index.py --execute")
        return

    result = run_command(
        title="environment check",
        command=[sys.executable, "check_env.py"],
    )

    if result.returncode != 0:
        print("\nenvironment checkfailed, alreadyin . ")
        return

    if not args.skip_snapshot:
        print("\nrunningsaverebuild document ...")
        snapshot_path = save_snapshot()
        print(f" alreadysave:{snapshot_path}")

    print("\nrunningcheckcollectionwhetherexists...")

    try:
        exists = collection_exists()
    except Exception as e:
        print(f"[failed] no checkcollection :{e}")
        return

    if exists:
        print(f"collectionexists,  delete:{COLLECTION_NAME}")
        delete_collection()
    else:
        print(f"collection does not exist, no delete:{COLLECTION_NAME}")

    result = run_command(
        title="re-  Markdown document",
        command=[sys.executable, "ingest.py"],
    )

    if result.returncode != 0:
        print("\nre- failed, please repair. ")
        return

    result = run_command(
        title="listalready document",
        command=[sys.executable, "list_docs.py"],
    )

    if result.returncode != 0:
        print("\nlist_docs.py executefailed, pleasecheck. ")
        return

    print("\n" + "=" * 80)
    print(" rebuildcompleted")
    print("=" * 80)
    print("")
    print("recommended next command:")
    print("python status.py")
    print('python ask.py " purpose stagemodel is ？"')


if __name__ == "__main__":
    main()