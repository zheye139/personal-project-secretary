import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

from config import KNOWLEDGE_ROOT, PROJECT_EXPORT_DIR


PROJECTS_DIR = KNOWLEDGE_ROOT / "01_Projects"


SKIP_DIR_NAMES = {
    ".venv",
    "__pycache__",
    "backups",
    "qdrant_storage",
    "qdrant_local",
    "_imported",
}


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8-sig")


def parse_frontmatter(text: str) -> tuple[dict, str, bool]:
    text = text.lstrip()

    if not text.startswith("---"):
        return {}, text, False

    parts = text.split("---", 2)

    if len(parts) < 3:
        return {}, text, False

    raw_meta = parts[1].strip()
    body = parts[2].strip()

    metadata = {}

    for line in raw_meta.splitlines():
        line = line.strip()

        if not line or ":" not in line:
            continue

        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"').strip("'")

    return metadata, body, True


def should_skip(path: Path) -> bool:
    parts = set(path.parts)
    return bool(parts.intersection(SKIP_DIR_NAMES))


def is_project_related_markdown(path: Path, project: str) -> bool:
    """
    determinea Markdown whether specified . 

    determinerules:
    1. 01_Projects/project directory file this . 
    2. Frontmatter in project etc. goal project file this . 
    """
    if should_skip(path):
        return False

    try:
        rel_parts = path.relative_to(KNOWLEDGE_ROOT).parts
    except ValueError:
        return False

    if len(rel_parts) >= 2 and rel_parts[0] == "01_Projects" and rel_parts[1] == project:
        return True

    if path.suffix.lower() != ".md":
        return False

    try:
        text = read_text(path)
    except Exception:
        return False

    metadata, _, _ = parse_frontmatter(text)
    return metadata.get("project", "") == project


def collect_project_files(project: str, include_summaries: bool = True) -> list[Path]:
    files = []

    for path in KNOWLEDGE_ROOT.rglob("*"):
        if not path.is_file():
            continue

        if should_skip(path):
            continue

        if path.suffix.lower() != ".md":
            continue

        # defaultexport , issue, decision, summaryetc.all Frontmatter project   Markdown
        if is_project_related_markdown(path, project):
            if not include_summaries:
                rel_parts = path.relative_to(KNOWLEDGE_ROOT).parts
                if rel_parts and rel_parts[0] == "05_Summaries":
                    continue
            files.append(path)

    return sorted(set(files))


def run_list_docs_snapshot(project: str, output_path: Path) -> None:
    """
    save  list_docs.py  , asexport package . 
    """
    base_dir = Path(__file__).parent.resolve()
    python_exe = sys.executable

    result = subprocess.run(
        [python_exe, "list_docs.py"],
        cwd=base_dir,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
    )

    now = datetime.now().isoformat(timespec="seconds")

    lines = [
        "---",
        f"title: {project} Exporting a snapshot of the imported document",
        f"created: {now}",
        "category: summary",
        f"project: {project}",
        "doc_type: export_snapshot",
        "tags: [Project Export, list_docs, Automatically generated]",
        "---",
        "",
        f"# {project} Exporting a snapshot of the imported document",
        "",
        f"Generation time:{now}",
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

    output_path.write_text("\n".join(lines), encoding="utf-8")


def create_manifest(project: str, files: list[Path], output_path: Path) -> None:
    now = datetime.now().isoformat(timespec="seconds")

    lines = [
        "---",
        f"title: {project} Project Export List",
        f"created: {now}",
        "category: summary",
        f"project: {project}",
        "doc_type: export_manifest",
        "tags: [Project Export, manifest, Automatically generated]",
        "---",
        "",
        f"# {project} Project Export List",
        "",
        f"Export time:{now}",
        f"Number of files:{len(files)}",
        "",
        "## File List",
        "",
    ]

    for path in files:
        rel_path = path.relative_to(KNOWLEDGE_ROOT)
        lines.append(f"- {rel_path}")

    lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")


def create_zip(project: str, files: list[Path], export_zip_path: Path, extra_files: list[Path]) -> None:
    with ZipFile(export_zip_path, "w", ZIP_DEFLATED) as zipf:
        for file_path in files:
            arcname = file_path.relative_to(KNOWLEDGE_ROOT)
            zipf.write(file_path, arcname)

        for file_path in extra_files:
            arcname = Path("_export_metadata") / file_path.name
            zipf.write(file_path, arcname)


def export_project(project: str, include_summaries: bool = True) -> None:
    project_dir = PROJECTS_DIR / project

    if not project_dir.exists():
        print(f"[WARNING] The project's main directory does not exist:{project_dir}")
        print("We will still attempt to export the relevant files based on the Frontmatter project field.")

    files = collect_project_files(
        project=project,
        include_summaries=include_summaries,
    )

    print("Personal Project Secretary + Data Knowledge Base: Project Export Tool")
    print("")
    print(f"Project Name:{project}")
    print(f"Project main directory:{project_dir}")
    print(f"Number of exported files:{len(files)}")

    if not files:
        print("")
        print("No exportable project file found.")
        return

    PROJECT_EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    export_base_name = f"{timestamp}_{project}_export"
    temp_dir = PROJECT_EXPORT_DIR / export_base_name
    temp_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = temp_dir / "export_manifest.md"
    snapshot_path = temp_dir / "list_docs_snapshot.md"

    create_manifest(project, files, manifest_path)
    run_list_docs_snapshot(project, snapshot_path)

    export_zip_path = PROJECT_EXPORT_DIR / f"{export_base_name}.zip"

    create_zip(
        project=project,
        files=files,
        export_zip_path=export_zip_path,
        extra_files=[manifest_path, snapshot_path],
    )

    print("")
    print("Project export complete:")
    print(export_zip_path)
    print("")
    print("The exported package includes:")
    print("1. Project-related Markdown files")
    print("2. _export_metadata/export_manifest.md")
    print("3. _export_metadata/list_docs_snapshot.md")
    print("")
    print("Recommended next steps:")
    print("1. Open the zip file and check its contents.")
    print("2. If everything is correct, you can run `python backup_kb.py` to perform a full database backup.")


def main():
    parser = argparse.ArgumentParser(
        description="Personal Project Secretary + Data Knowledge Base: Export data packages by project"
    )

    parser.add_argument(
        "--project",
        required=True,
        help="The project name to be exported, for example, Demo_Project",
    )

    parser.add_argument(
        "--no-summaries",
        action="store_true",
        help="Do not export project reports, Q&A records, daily and weekly reports, and other summary files under 05_Summaries.",
    )

    args = parser.parse_args()

    export_project(
        project=args.project,
        include_summaries=not args.no_summaries,
    )


if __name__ == "__main__":
    main()