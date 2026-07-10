import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import config


# ============================================================
# 基础配置
# ============================================================
# 使用 config.py 中的 KNOWLEDGE_ROOT。
# 如果 config.py 中还没有 MILESTONE_REPORT_DIR，则自动使用默认目录。
KNOWLEDGE_ROOT = config.KNOWLEDGE_ROOT
MILESTONE_REPORT_DIR = getattr(
    config,
    "MILESTONE_REPORT_DIR",
    KNOWLEDGE_ROOT / "05_Summaries" / "milestone_reports",
)

BASE_DIR = Path(__file__).parent.resolve()


# ============================================================
# Windows 控制台 UTF-8 输出修复
# ============================================================
# 作用：
# 1. 避免 PowerShell 中中文输出乱码。
# 2. 避免 subprocess 捕获其他脚本输出时乱码。
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def run_command(title: str, command: list[str]) -> tuple[bool, str]:
    """
    执行一个外部 Python 脚本，并返回：
    1. 是否成功
    2. 脚本输出内容

    这里统一设置 PYTHONUTF8 和 PYTHONIOENCODING，
    用于减少 Windows PowerShell 中文乱码问题。
    """
    print("\n" + "=" * 80)
    print(f"开始：{title}")
    print("=" * 80)
    print("执行命令：", " ".join(command))
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
            timeout=900,
            env=env,
        )
    except Exception as e:
        output = f"[异常] {e}"
        print(output)
        return False, output

    output_parts = []

    if result.stdout:
        output_parts.append(result.stdout)

    if result.stderr:
        output_parts.append("[stderr]\n" + result.stderr)

    output = "\n".join(output_parts)

    if output:
        print(output)

    if result.returncode != 0:
        print(f"[失败] {title}，返回码：{result.returncode}")
        return False, output

    print(f"[完成] {title}")
    return True, output


def build_m1_summary() -> str:
    """
    生成 M1 阶段封版报告中的固定总结内容。

    这里不用三引号 f-string，
    避免复制代码时出现字符串断层问题。
    """
    lines = [
        "## 1. M1 阶段定位",
        "",
        "M1 阶段目标是完成“个人项目秘书 + 数据知识库”的本地 RAG 最小系统，",
        "并逐步增强为可长期维护的个人项目知识库工具。",
        "",
        "M1 阶段的核心原则：",
        "",
        "1. Markdown 是主数据源。",
        "2. Qdrant 是可重建向量索引。",
        "3. Ollama 是本地模型服务。",
        "4. Python 脚本是自动化工具层。",
        "5. config.py 是统一配置中心。",
        "6. 备份和恢复文档是系统长期可维护的保障。",
        "",
        "---",
        "",
        "## 2. M1 已完成能力",
        "",
        "M1 阶段已完成以下能力：",
        "",
        "1. 本地 Ollama 模型服务接入。",
        "2. qwen3:8b 主对话模型部署。",
        "3. bge-m3 向量模型部署。",
        "4. Docker Qdrant 向量数据库接入。",
        "5. Markdown 文档读取、切块和向量化。",
        "6. Qdrant 入库和语义检索。",
        "7. ask.py RAG 问答脚本。",
        "8. search_docs.py 片段搜索脚本。",
        "9. Frontmatter 元数据解析。",
        "10. project / doc_type / category / tag 过滤检索。",
        "11. qa_logs 自动保存问答记录。",
        "12. add_note.py 快速新增知识库记录。",
        "13. project_report.py 项目报告生成。",
        "14. time_report.py 日报 / 周报生成。",
        "15. status.py 系统状态总览。",
        "16. list_docs.py 文档列表检查。",
        "17. inspect_collection.py 集合样本检查。",
        "18. backup_kb.py 知识库备份。",
        "19. restore_guide.md 恢复流程文档。",
        "20. environment_setup.md 环境安装说明。",
        "21. commands.md 命令速查表。",
        "22. cleanup_qa_logs.py 问答记录清理。",
        "23. inbox_import.py Inbox 自动归档。",
        "24. project_template.py 新项目模板生成。",
        "25. archive_project.py 项目归档。",
        "26. validate_kb.py Markdown 规范检查。",
        "27. repair_frontmatter.py Frontmatter 批量修复。",
        "28. export_project.py 项目资料导出。",
        "29. rebuild_index.py 安全重建 Qdrant 索引。",
        "30. health_check_full.py 全链路健康检查。",
        "",
        "---",
        "",
        "## 3. M1 当前可用日常流程",
        "",
        "### 3.1 启动系统",
        "",
        "```powershell",
        r"cd D:\Personal_Knowledge_Base\99_System\rag_mvp",
        r".\.venv\Scripts\activate",
        "docker start pkb-qdrant",
        "python status.py",
        "```",
        "",
        "### 3.2 新增记录",
        "",
        "```powershell",
        'python add_note.py --category project --project Personal_Project_Assistant --doc-type progress_log --title "进度标题" --tags "RAG,进度记录" --content "进度内容"',
        "python update_index.py",
        "```",
        "",
        "### 3.3 问答",
        "",
        "```powershell",
        'python ask.py --project Personal_Project_Assistant "当前项目进行到哪里了？"',
        "```",
        "",
        "### 3.4 搜索片段",
        "",
        "```powershell",
        'python search_docs.py "关键词" --show-text',
        "```",
        "",
        "### 3.5 生成报告",
        "",
        "```powershell",
        "python project_report.py --project Personal_Project_Assistant",
        "python time_report.py --project Personal_Project_Assistant --mode weekly",
        "python update_index.py",
        "```",
        "",
        "### 3.6 备份",
        "",
        "```powershell",
        "python backup_kb.py",
        "```",
        "",
        "---",
        "",
        "## 4. M1 封版判断",
        "",
        "M1 可以封版的条件：",
        "",
        "1. health_check_full.py 全链路检查通过。",
        "2. status.py 能正常显示系统状态。",
        "3. list_docs.py 能正常列出文档。",
        "4. ask.py 能正常回答基于知识库的问题。",
        "5. search_docs.py 能正常搜索片段。",
        "6. backup_kb.py 能正常生成备份。",
        "7. rebuild_index.py 能安全重建索引。",
        "8. 关键文档已经入库，包括环境说明、恢复说明、命令速查表、README。",
        "",
        "如果上述条件满足，则 M1 可以作为“本地 RAG 知识库 MVP 增强版”封版。",
        "",
        "---",
        "",
        "## 5. M2 推荐方向",
        "",
        "M2 不建议继续堆很多小脚本，而应进入“服务化和自动化执行层”。",
        "",
        "推荐 M2 方向：",
        "",
        "1. M2.1：增加本地 API 服务，例如 FastAPI。",
        "2. M2.2：增加局域网访问限制和安全配置。",
        "3. M2.3：接入 OpenClaw 或类似自动化执行层。",
        "4. M2.4：增加简单 Web UI 或本地控制台界面。",
        "5. M2.5：增加多项目仪表盘。",
        "6. M2.6：增加任务队列，例如自动入库、自动日报、定时备份。",
        "7. M2.7：增加插件式脚本管理。",
        "8. M2.8：优化检索质量，例如混合检索、关键词过滤、重排序。",
        "9. M2.9：迁移到更强台式主机后替换更强模型。",
        "10. M2.10：为其他项目接入统一知识库流程。",
        "",
        "---",
        "",
        "## 6. M2 优先建议",
        "",
        "建议 M2 第一优先级不是 Web UI，而是：",
        "",
        "```text",
        "M2.1：本地 API 服务化",
        "```",
        "",
        "原因：",
        "",
        "1. API 是后续 Web UI、OpenClaw、局域网助手、自动化任务的基础。",
        "2. 当前脚本已经稳定，可以封装为服务接口。",
        "3. 服务化后，后续可以从浏览器、自动化工具或其他程序调用知识库能力。",
        "",
        "M2.1 可以优先实现这些接口：",
        "",
        "```text",
        "GET  /status",
        "POST /ask",
        "POST /search",
        "POST /add_note",
        "POST /update_index",
        "POST /project_report",
        "POST /time_report",
        "```",
        "",
        "---",
        "",
        "## 7. M1 后续维护建议",
        "",
        "M1 封版后仍需保持以下维护习惯：",
        "",
        "1. 新增 Markdown 后执行 `python update_index.py`。",
        "2. 每完成阶段执行 `python project_report.py`。",
        "3. 每周执行 `python time_report.py --mode weekly`。",
        "4. 修改核心脚本前执行 `python backup_kb.py`。",
        "5. 定期执行 `python health_check_full.py`。",
        "6. 定期执行 `python validate_kb.py --write-report`。",
        "7. 迁移前执行 `python export_project.py` 和 `python backup_kb.py`。",
        "",
    ]

    return "\n".join(lines)


def save_closeout_report(outputs: dict[str, str], results: dict[str, bool]) -> Path:
    """
    保存 M1 阶段封版报告。

    报告内容包括：
    1. M1 阶段总结
    2. M2 规划建议
    3. 自动检查结果
    4. health_check_full.py 输出
    5. status.py 输出
    6. list_docs.py 输出
    """
    MILESTONE_REPORT_DIR.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
    report_path = MILESTONE_REPORT_DIR / f"{timestamp}_M1_closeout_report.md"

    lines = []

    # Markdown Frontmatter
    lines.append("---")
    lines.append(f"title: M1 阶段封版报告 {timestamp}")
    lines.append(f"created: {now.isoformat(timespec='seconds')}")
    lines.append("category: summary")
    lines.append("project: Personal_Project_Assistant")
    lines.append("doc_type: milestone_report")
    lines.append("tags: [M1, 阶段封版, M2规划, RAG, 自动生成]")
    lines.append("---")
    lines.append("")

    # 报告正文
    lines.append("# M1 阶段封版报告")
    lines.append("")
    lines.append(f"生成时间：{now.isoformat(timespec='seconds')}")
    lines.append(f"知识库根目录：{KNOWLEDGE_ROOT}")
    lines.append("")
    lines.append(build_m1_summary())
    lines.append("")
    lines.append("---")
    lines.append("")

    # 自动检查摘要
    lines.append("## 8. 自动检查结果摘要")
    lines.append("")

    for name, ok in results.items():
        status = "通过" if ok else "失败"
        lines.append(f"- {name}：{status}")

    lines.append("")
    lines.append("---")
    lines.append("")

    # health_check_full.py 输出
    lines.append("## 9. health_check_full.py 输出")
    lines.append("")
    lines.append("```text")
    lines.append(outputs.get("health_check_full.py", ""))
    lines.append("```")
    lines.append("")

    # status.py 输出
    lines.append("## 10. status.py 输出")
    lines.append("")
    lines.append("```text")
    lines.append(outputs.get("status.py", ""))
    lines.append("```")
    lines.append("")

    # list_docs.py 输出
    lines.append("## 11. list_docs.py 输出")
    lines.append("")
    lines.append("```text")
    lines.append(outputs.get("list_docs.py", ""))
    lines.append("```")
    lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def main():
    """
    主流程：

    1. 运行 health_check_full.py
    2. 运行 status.py
    3. 运行 list_docs.py
    4. 汇总输出并生成 M1 封版报告
    """
    print("个人项目秘书 + 数据知识库：M1 阶段封版检查")
    print(f"工作目录：{BASE_DIR}")
    print(f"Python：{sys.executable}")

    checks = [
        ("health_check_full.py", [sys.executable, "health_check_full.py"]),
        ("status.py", [sys.executable, "status.py"]),
        ("list_docs.py", [sys.executable, "list_docs.py"]),
    ]

    outputs = {}
    results = {}

    for name, command in checks:
        ok, output = run_command(name, command)
        outputs[name] = output
        results[name] = ok

    report_path = save_closeout_report(
        outputs=outputs,
        results=results,
    )

    print("\n" + "=" * 80)
    print("M1 阶段封版检查完成")
    print("=" * 80)
    print("")
    print("封版报告已生成：")
    print(report_path)
    print("")

    if all(results.values()):
        print("结论：M1 阶段可以封版。")
    else:
        print("结论：M1 阶段仍有检查项失败，请先修复。")

    print("")
    print("建议下一步执行：")
    print("python update_index.py")
    print('python ask.py --doc-type milestone_report "M1 阶段完成了什么？"')


if __name__ == "__main__":
    main()