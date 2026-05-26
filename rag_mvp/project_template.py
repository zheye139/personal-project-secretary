import argparse
import re
from datetime import datetime
from pathlib import Path

from config import KNOWLEDGE_ROOT


PROJECT_ROOT = KNOWLEDGE_ROOT / "01_Projects"


def sanitize_name(name: str) -> str:
    name = name.strip()
    name = re.sub(r'[\\/:*?"<>|]', "_", name)
    name = re.sub(r"\s+", "_", name)
    return name


def build_frontmatter(
    title: str,
    project: str,
    doc_type: str,
    tags: list[str],
) -> str:
    now = datetime.now().isoformat(timespec="seconds")
    tag_text = "[" + ", ".join(tags) + "]" if tags else "[]"

    lines = [
        "---",
        f"title: {title}",
        f"created: {now}",
        "category: project",
        f"project: {project}",
        f"doc_type: {doc_type}",
        f"tags: {tag_text}",
        "---",
        "",
    ]

    return "\n".join(lines)


def build_markdown(
    title: str,
    project: str,
    doc_type: str,
    tags: list[str],
    body_lines: list[str],
) -> str:
    return build_frontmatter(
        title=title,
        project=project,
        doc_type=doc_type,
        tags=tags,
    ) + "\n".join(body_lines) + "\n"


def write_file(path: Path, content: str, overwrite: bool = False) -> bool:
    if path.exists() and not overwrite:
        return False

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def build_readme(project: str) -> str:
    return build_markdown(
        title=f"{project}   README",
        project=project,
        doc_type="readme",
        tags=[" description", "README"],
        body_lines=[
            f"# {project}",
            "",
            "## 1.  ",
            "",
            "pleaseinthisin purpose . ",
            "",
            "## 2.  goal",
            "",
            "1. ",
            "2. ",
            "3. ",
            "",
            "## 3.  stage",
            "",
            " stage: . ",
            "",
            "## 4.  directory",
            "",
            "```text",
            project,
            "├─ README.md",
            "├─ project_overview.md",
            "├─ progress_log.md",
            "├─ issues.md",
            "├─ decisions.md",
            "├─ technical_notes.md",
            "├─ next_steps.md",
            "└─ notes",
            "```",
            "",
            "## 5.  description",
            "",
            " project records Personal Project Secretary + Knowledge Base read, andpassed RAG retrievalquestion answering. ",
            "",
        ],
    )


def build_project_overview(project: str) -> str:
    return build_markdown(
        title=f"{project} project overview",
        project=project,
        doc_type="project_overview",
        tags=["project overview"],
        body_lines=[
            f"# {project} project overview",
            "",
            "## 1.  ",
            "",
            "pleasedescriptionthis is ,  resolve issue. ",
            "",
            "## 2.  ",
            "",
            "pleaserecord reason,  ,  source. ",
            "",
            "## 3. coregoal",
            "",
            "1. ",
            "2. ",
            "3. ",
            "",
            "## 4.  ",
            "",
            "pleaserecord . ",
            "",
            "## 5.  range",
            "",
            " stageplancompleted:",
            "",
            "1. ",
            "2. ",
            "3. ",
            "",
            "## 6.  not ",
            "",
            " stage not :",
            "",
            "1. ",
            "2. ",
            "3. ",
            "",
        ],
    )


def build_progress_log(project: str) -> str:
    today = datetime.now().strftime("%Y-%m-%d")

    return build_markdown(
        title=f"{project} project progressrecord",
        project=project,
        doc_type="progress_log",
        tags=["project progress", " record"],
        body_lines=[
            f"# {project} project progressrecord",
            "",
            f"## {today}",
            "",
            "### alreadycompleted",
            "",
            "1. create knowledge base . ",
            "2.  basicdocument. ",
            "",
            "###  stage",
            "",
            " . ",
            "",
            "### next steps",
            "",
            "1.  project overview. ",
            "2.  . ",
            "3. record aissue or decision. ",
            "",
        ],
    )


def build_issues(project: str) -> str:
    return build_markdown(
        title=f"{project} issue record",
        project=project,
        doc_type="issues",
        tags=["issue record", "Bug", " "],
        body_lines=[
            f"# {project} issue record",
            "",
            "## issue ",
            "",
            "### issuetitle",
            "",
            " . ",
            "",
            "### issue ",
            "",
            " . ",
            "",
            "### reason ",
            "",
            " . ",
            "",
            "### resolve ",
            "",
            " . ",
            "",
            "### current status",
            "",
            " . ",
            "",
        ],
    )


def build_decisions(project: str) -> str:
    return build_markdown(
        title=f"{project} decision record",
        project=project,
        doc_type="decisions",
        tags=["decision record", " decision"],
        body_lines=[
            f"# {project} decision record",
            "",
            "## decision ",
            "",
            "### decisiontitle",
            "",
            " . ",
            "",
            "### decision ",
            "",
            " . ",
            "",
            "### can ",
            "",
            "1.   A:",
            "2.   B:",
            "3.   C:",
            "",
            "###  ",
            "",
            " . ",
            "",
            "###  reason",
            "",
            " . ",
            "",
            "### later ",
            "",
            " . ",
            "",
        ],
    )


def build_technical_notes(project: str) -> str:
    return build_markdown(
        title=f"{project}  ",
        project=project,
        doc_type="technical_notes",
        tags=[" ", "knowledgerecord"],
        body_lines=[
            f"# {project}  ",
            "",
            "##  ",
            "",
            " . ",
            "",
            "## core ",
            "",
            " . ",
            "",
            "##  command /  ",
            "",
            "```text",
            " ",
            "```",
            "",
            "##  items",
            "",
            " . ",
            "",
            "##  records",
            "",
            " . ",
            "",
        ],
    )


def build_next_steps(project: str) -> str:
    return build_markdown(
        title=f"{project} next stepsplan",
        project=project,
        doc_type="next_steps",
        tags=["next steps", "tasksplan"],
        body_lines=[
            f"# {project} next stepsplan",
            "",
            "##  tasks",
            "",
            "1. ",
            "2. ",
            "3. ",
            "",
            "## in tasks",
            "",
            "1. ",
            "2. ",
            "3. ",
            "",
            "## long-term ",
            "",
            "1. ",
            "2. ",
            "3. ",
            "",
            "##  priority",
            "",
            "1.  priority:",
            "2. inpriority:",
            "3.  priority:",
            "",
        ],
    )


def create_project(project: str, overwrite: bool = False) -> None:
    safe_project = sanitize_name(project)

    if not safe_project:
        raise ValueError(" notcanis empty. ")

    project_dir = PROJECT_ROOT / safe_project
    notes_dir = project_dir / "notes"

    files = {
        "README.md": build_readme(safe_project),
        "project_overview.md": build_project_overview(safe_project),
        "progress_log.md": build_progress_log(safe_project),
        "issues.md": build_issues(safe_project),
        "decisions.md": build_decisions(safe_project),
        "technical_notes.md": build_technical_notes(safe_project),
        "next_steps.md": build_next_steps(safe_project),
    }

    project_dir.mkdir(parents=True, exist_ok=True)
    notes_dir.mkdir(parents=True, exist_ok=True)

    print(f"project directory:{project_dir}")
    print(f"notes directory:{notes_dir}")

    created_count = 0
    skipped_count = 0

    for file_name, content in files.items():
        file_path = project_dir / file_name
        created = write_file(file_path, content, overwrite=overwrite)

        if created:
            created_count += 1
            print(f"[create] {file_path}")
        else:
            skipped_count += 1
            print(f"[skip] alreadyexists:{file_path}")

    print("")
    print("project template completed. ")
    print(f"createfile :{created_count}")
    print(f"skipfile :{skipped_count}")
    print("")
    print("recommended next command:")
    print("python update_index.py")


def main():
    parser = argparse.ArgumentParser(
        description="Personal Project Secretary + Knowledge Base: project template tool"
    )

    parser.add_argument(
        "--project",
        required=True,
        help="project name, for example Electronics_Project",
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="iffilealreadyexists,  . defaultnot . ",
    )

    args = parser.parse_args()

    create_project(
        project=args.project,
        overwrite=args.overwrite,
    )


if __name__ == "__main__":
    main()