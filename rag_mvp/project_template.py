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
        title=f"{project} 项目 README",
        project=project,
        doc_type="readme",
        tags=["项目说明", "README"],
        body_lines=[
            f"# {project}",
            "",
            "## 1. 项目简介",
            "",
            "请在这里填写项目的基本介绍。",
            "",
            "## 2. 项目目标",
            "",
            "1. ",
            "2. ",
            "3. ",
            "",
            "## 3. 当前阶段",
            "",
            "当前阶段：待填写。",
            "",
            "## 4. 主要目录",
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
            "## 5. 使用说明",
            "",
            "本项目资料会被个人项目秘书 + 数据知识库系统读取，并通过 RAG 检索问答。",
            "",
        ],
    )


def build_project_overview(project: str) -> str:
    return build_markdown(
        title=f"{project} 项目概述",
        project=project,
        doc_type="project_overview",
        tags=["项目概述"],
        body_lines=[
            f"# {project} 项目概述",
            "",
            "## 1. 项目定位",
            "",
            "请说明这个项目是什么，用来解决什么问题。",
            "",
            "## 2. 项目背景",
            "",
            "请记录项目产生的原因、使用场景、需求来源。",
            "",
            "## 3. 核心目标",
            "",
            "1. ",
            "2. ",
            "3. ",
            "",
            "## 4. 技术路线",
            "",
            "请记录当前采用的技术路线。",
            "",
            "## 5. 当前范围",
            "",
            "本阶段计划完成：",
            "",
            "1. ",
            "2. ",
            "3. ",
            "",
            "## 6. 暂不包含",
            "",
            "本阶段暂不处理：",
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
        title=f"{project} 项目进度记录",
        project=project,
        doc_type="progress_log",
        tags=["项目进度", "进度记录"],
        body_lines=[
            f"# {project} 项目进度记录",
            "",
            f"## {today}",
            "",
            "### 已完成",
            "",
            "1. 创建项目知识库模板。",
            "2. 初始化项目基础文档。",
            "",
            "### 当前阶段",
            "",
            "待填写。",
            "",
            "### 下一步",
            "",
            "1. 补充项目概述。",
            "2. 补充技术路线。",
            "3. 记录第一个问题或决策。",
            "",
        ],
    )


def build_issues(project: str) -> str:
    return build_markdown(
        title=f"{project} 问题记录",
        project=project,
        doc_type="issues",
        tags=["问题记录", "Bug", "故障排查"],
        body_lines=[
            f"# {project} 问题记录",
            "",
            "## 问题模板",
            "",
            "### 问题标题",
            "",
            "待填写。",
            "",
            "### 问题现象",
            "",
            "待填写。",
            "",
            "### 原因分析",
            "",
            "待填写。",
            "",
            "### 解决方案",
            "",
            "待填写。",
            "",
            "### 当前状态",
            "",
            "待填写。",
            "",
        ],
    )


def build_decisions(project: str) -> str:
    return build_markdown(
        title=f"{project} 决策记录",
        project=project,
        doc_type="decisions",
        tags=["决策记录", "技术决策"],
        body_lines=[
            f"# {project} 决策记录",
            "",
            "## 决策模板",
            "",
            "### 决策标题",
            "",
            "待填写。",
            "",
            "### 决策背景",
            "",
            "待填写。",
            "",
            "### 可选方案",
            "",
            "1. 方案 A：",
            "2. 方案 B：",
            "3. 方案 C：",
            "",
            "### 最终选择",
            "",
            "待填写。",
            "",
            "### 选择原因",
            "",
            "待填写。",
            "",
            "### 后续影响",
            "",
            "待填写。",
            "",
        ],
    )


def build_technical_notes(project: str) -> str:
    return build_markdown(
        title=f"{project} 技术笔记",
        project=project,
        doc_type="technical_notes",
        tags=["技术笔记", "知识记录"],
        body_lines=[
            f"# {project} 技术笔记",
            "",
            "## 技术主题",
            "",
            "待填写。",
            "",
            "## 核心概念",
            "",
            "待填写。",
            "",
            "## 关键命令 / 代码",
            "",
            "```text",
            "待填写",
            "```",
            "",
            "## 注意事项",
            "",
            "待填写。",
            "",
            "## 参考资料",
            "",
            "待填写。",
            "",
        ],
    )


def build_next_steps(project: str) -> str:
    return build_markdown(
        title=f"{project} 下一步计划",
        project=project,
        doc_type="next_steps",
        tags=["下一步", "任务计划"],
        body_lines=[
            f"# {project} 下一步计划",
            "",
            "## 短期任务",
            "",
            "1. ",
            "2. ",
            "3. ",
            "",
            "## 中期任务",
            "",
            "1. ",
            "2. ",
            "3. ",
            "",
            "## 长期方向",
            "",
            "1. ",
            "2. ",
            "3. ",
            "",
            "## 当前优先级",
            "",
            "1. 高优先级：",
            "2. 中优先级：",
            "3. 低优先级：",
            "",
        ],
    )


def create_project(project: str, overwrite: bool = False) -> None:
    safe_project = sanitize_name(project)

    if not safe_project:
        raise ValueError("项目名不能为空。")

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

    print(f"项目目录：{project_dir}")
    print(f"notes 目录：{notes_dir}")

    created_count = 0
    skipped_count = 0

    for file_name, content in files.items():
        file_path = project_dir / file_name
        created = write_file(file_path, content, overwrite=overwrite)

        if created:
            created_count += 1
            print(f"[创建] {file_path}")
        else:
            skipped_count += 1
            print(f"[跳过] 已存在：{file_path}")

    print("")
    print("项目模板生成完成。")
    print(f"创建文件数：{created_count}")
    print(f"跳过文件数：{skipped_count}")
    print("")
    print("建议下一步执行：")
    print("python update_index.py")


def main():
    parser = argparse.ArgumentParser(
        description="个人项目秘书 + 数据知识库：新项目模板生成工具"
    )

    parser.add_argument(
        "--project",
        required=True,
        help="项目名称，例如 Electronics_Project",
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="如果文件已存在，则覆盖。默认不覆盖。",
    )

    args = parser.parse_args()

    create_project(
        project=args.project,
        overwrite=args.overwrite,
    )


if __name__ == "__main__":
    main()