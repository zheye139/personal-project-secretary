import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import config


# ============================================================
# 基础配置
# ============================================================

KNOWLEDGE_ROOT = config.KNOWLEDGE_ROOT

MILESTONE_REPORT_DIR = getattr(
    config,
    "MILESTONE_REPORT_DIR",
    KNOWLEDGE_ROOT / "05_Summaries" / "milestone_reports",
)

BASE_DIR = Path(__file__).parent.resolve()


# ============================================================
# Windows / PowerShell 中文输出处理
# ============================================================

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

def run_command(title: str, command: list[str], timeout: int = 900) -> tuple[bool, str]:
    """
    执行一个外部命令，并返回：
    1. 是否成功
    2. 输出内容

    用途：
    - 执行 health_check_full.py
    - 执行 status.py
    - 执行 list_docs.py
    - 执行 search_docs.py
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
            timeout=timeout,
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

def get_milestone_config(milestone: str) -> dict:
    """
    根据里程碑名称返回封版配置。

    当前重点支持：
    - M1：本地 RAG 最小系统增强阶段
    - M2：个人秘书能力增强阶段

    后续 M3/M4 可以继续在这里追加。
    """
    milestone_upper = milestone.upper()

    if milestone_upper == "M1":
        return {
            "title": "M1 阶段封版报告",
            "doc_type": "milestone_report",
            "tags": "[M1, 阶段封版, RAG, 自动生成]",
            "focus": "本地 RAG 最小系统增强阶段",
            "summary_lines": build_m1_summary_lines(),
            "extra_checks": [
                (
                    "检查 M1 相关文档",
                    [
                        sys.executable,
                        "search_docs.py",
                        "--tag",
                        "M1",
                        "M1 阶段完成了什么？",
                    ],
                ),
            ],
        }

    if milestone_upper == "M2":
        return {
            "title": "M2 阶段封版报告",
            "doc_type": "milestone_report",
            "tags": "[M2, 阶段封版, 个人秘书, 秘书能力, 自动生成]",
            "focus": "个人秘书能力增强阶段",
            "summary_lines": build_m2_summary_lines(),
            "extra_checks": [
                (
                    "检查 next_action_report",
                    [
                        sys.executable,
                        "search_docs.py",
                        "--doc-type",
                        "next_action_report",
                        "下一步行动清单",
                    ],
                ),
                (
                    "检查 project_brief",
                    [
                        sys.executable,
                        "search_docs.py",
                        "--doc-type",
                        "project_brief",
                        "项目简报",
                    ],
                ),
                (
                    "检查 multi_project_status",
                    [
                        sys.executable,
                        "search_docs.py",
                        "--doc-type",
                        "multi_project_status",
                        "多项目状态汇总",
                    ],
                ),
                (
                    "检查 priority_advice",
                    [
                        sys.executable,
                        "search_docs.py",
                        "--doc-type",
                        "priority_advice",
                        "优先级建议",
                    ],
                ),
                (
                    "检查 review_report",
                    [
                        sys.executable,
                        "search_docs.py",
                        "--doc-type",
                        "review_report",
                        "项目记录复盘",
                    ],
                ),
                (
                    "检查 secretary_report",
                    [
                        sys.executable,
                        "search_docs.py",
                        "--doc-type",
                        "secretary_report",
                        "个人秘书汇报",
                    ],
                ),
            ],
        }
    
    if milestone_upper == "M3":
        return {
            "title": "M3 阶段封版报告",
            "doc_type": "milestone_report",
            "tags": "[M3, 阶段封版, 增量索引, 混合检索, 检索评估, 自动生成]",
            "focus": "索引与检索能力优化阶段",
            "summary_lines": build_m3_summary_lines(),
            "extra_checks": [
                (
                    "检查 manifest 工具",
                    [
                        sys.executable,
                        "manifest_utils.py",
                        "--scan",
                    ],
                ),
                (
                    "检查默认增量索引 dry-run",
                    [
                        sys.executable,
                        "update_index.py",
                        "--dry-run",
                        "--skip-check",
                        "--skip-list-docs",
                    ],
                ),
                (
                    "检查项目级增量索引 dry-run",
                    [
                        sys.executable,
                        "update_index.py",
                        "--project",
                        "Personal_Project_Assistant",
                        "--dry-run",
                        "--skip-check",
                        "--skip-list-docs",
                    ],
                ),
                (
                    "检查 search_docs keyword 模式",
                    [
                        sys.executable,
                        "search_docs.py",
                        "--mode",
                        "keyword",
                        "--limit",
                        "3",
                        "update_index.py",
                    ],
                ),
                (
                    "检查 search_docs hybrid 模式",
                    [
                        sys.executable,
                        "search_docs.py",
                        "--mode",
                        "hybrid",
                        "--limit",
                        "3",
                        "M3 阶段增量索引做了什么？",
                    ],
                ),
                (
                    "检查 ask.py hybrid 模式",
                    [
                        sys.executable,
                        "ask.py",
                        "--search-mode",
                        "hybrid",
                        "--limit",
                        "3",
                        "M3 阶段增量索引做了什么？",
                    ],
                ),
                (
                    "检查 retrieval_eval keyword 模式",
                    [
                        sys.executable,
                        "retrieval_eval.py",
                        "--mode",
                        "keyword",
                        "--no-save",
                    ],
                ),
            ],
        }

    return {
        "title": f"{milestone_upper} 阶段封版报告",
        "doc_type": "milestone_report",
        "tags": f"[{milestone_upper}, 阶段封版, 自动生成]",
        "focus": f"{milestone_upper} 阶段",
        "summary_lines": build_generic_summary_lines(milestone_upper),
        "extra_checks": [],
    }

def build_m1_summary_lines() -> list[str]:
    """
    M1 阶段总结内容。
    """
    return [
        "## 1. M1 阶段定位",
        "",
        "M1 阶段目标是完成“个人项目秘书 + 数据知识库”的本地 RAG 最小系统，",
        "并增强为可长期维护的个人项目知识库工具。",
        "",
        "M1 阶段核心原则：",
        "",
        "1. Markdown 是主数据源。",
        "2. Qdrant 是可重建向量索引。",
        "3. Ollama 是本地模型服务。",
        "4. Python 脚本是自动化工具层。",
        "5. config.py 是统一配置中心。",
        "",
        "## 2. M1 已完成能力",
        "",
        "1. Ollama 本地模型服务接入。",
        "2. qwen3:8b 主对话模型部署。",
        "3. bge-m3 向量模型部署。",
        "4. Docker Qdrant 向量数据库接入。",
        "5. Markdown 文档入库。",
        "6. Frontmatter 元数据解析。",
        "7. project / doc_type / category / tag 过滤检索。",
        "8. ask.py RAG 问答。",
        "9. search_docs.py 片段搜索。",
        "10. add_note.py 快速新增记录。",
        "11. project_report.py 项目报告。",
        "12. time_report.py 日报 / 周报。",
        "13. status.py 系统状态总览。",
        "14. backup_kb.py 知识库备份。",
        "15. validate_kb.py 和 repair_frontmatter.py 规范检查与修复。",
        "16. rebuild_index.py 安全重建索引。",
        "17. health_check_full.py 全链路健康检查。",
        "",
        "## 3. M1 封版判断",
        "",
        "如果 health_check_full.py、status.py、list_docs.py 均通过，并且关键文档可检索，",
        "则 M1 可作为本地 RAG 知识库 MVP 增强版封版。",
        "",
    ]

def build_m2_summary_lines() -> list[str]:
    """
    M2 阶段总结内容。

    M2 的定位不是服务化，而是“个人秘书能力增强”。
    """
    return [
        "## 1. M2 阶段定位",
        "",
        "M2 阶段目标是将 M1 的“能存、能搜、能问答”的知识库基础能力，",
        "升级为“能提炼、能汇总、能复盘、能给建议”的个人秘书分析能力。",
        "",
        "M2 阶段不优先做 FastAPI 服务化，也不优先做 Web UI，",
        "而是优先增强本地脚本层的秘书能力。",
        "",
        "## 2. M2 已完成能力",
        "",
        "### M2.1 next_action.py",
        "",
        "从 progress_log、next_steps、project_report、weekly_report 中提取下一步行动项，",
        "生成 next_action_report，并保存到 05_Summaries/next_actions。",
        "",
        "### M2.2 project_brief.py",
        "",
        "生成单项目简报，包括当前状态、最近进展、当前问题、下一步行动、风险提醒和建议补充记录，",
        "并保存到 05_Summaries/project_briefs。",
        "",
        "### M2.3 multi_project_status.py",
        "",
        "汇总多个项目状态，支持默认汇总所有项目，也支持 --project 指定项目、--exclude-project 排除项目，",
        "并保存到 05_Summaries/multi_project_status。",
        "",
        "### M2.4 priority_advisor.py",
        "",
        "根据项目状态、问题、计划、行动项和多项目汇总资料给出优先级建议，",
        "并保存到 05_Summaries/priority_advice。",
        "",
        "### M2.5 review_assistant.py",
        "",
        "对项目记录进行复盘，检查项目资料是否完整，指出遗漏内容、风险与隐患、",
        "建议补充的记录和需要立即修正的问题，并保存到 05_Summaries/review_reports。",
        "",
        "### M2.6 secretary_report.py",
        "",
        "综合 multi_project_status、priority_advice、review_report、project_brief、next_action_report、",
        "weekly_report、daily_report、project_report、progress_log、next_steps、issues 等资料，",
        "生成个人秘书汇报，并保存到 05_Summaries/secretary_reports。",
        "",
        "## 3. M2 当前形成的秘书工作流",
        "",
        "```powershell",
        "python next_action.py --project Personal_Project_Assistant",
        "python project_brief.py --project Personal_Project_Assistant",
        "python multi_project_status.py",
        "python priority_advisor.py",
        "python review_assistant.py --project Personal_Project_Assistant",
        "python secretary_report.py",
        "python update_index.py",
        "```",
        "",
        "## 4. M2 封版判断",
        "",
        "M2 可以小封版的条件：",
        "",
        "1. next_action_report 可生成并入库。",
        "2. project_brief 可生成并入库。",
        "3. multi_project_status 可生成并入库。",
        "4. priority_advice 可生成并入库。",
        "5. review_report 可生成并入库。",
        "6. secretary_report 可生成并入库。",
        "7. health_check_full.py 全链路检查通过。",
        "8. status.py 能正常显示系统状态。",
        "9. list_docs.py 能正常列出文档。",
        "",
        "如果上述条件满足，则 M2 可作为“个人秘书能力增强阶段”小封版。",
        "",
        "## 5. M2 后续维护建议",
        "",
        "1. 每次新增项目记录后执行 `python update_index.py`。",
        "2. 每个项目阶段结束时执行 `python project_brief.py --project 项目名`。",
        "3. 每周执行 `python multi_project_status.py` 和 `python priority_advisor.py`。",
        "4. 每周执行一次 `python secretary_report.py` 生成个人秘书汇报。",
        "5. 定期执行 `python review_assistant.py --project 项目名` 检查项目记录质量。",
        "6. 修改核心脚本前执行 `python backup_kb.py`。",
        "",
        "## 6. M3 推荐方向",
        "",
        "M2 完成后，下一阶段可以有两个方向：",
        "",
        "1. 继续增强秘书能力，例如自动计划、任务状态追踪、过期事项提醒。",
        "2. 开始服务化，例如 FastAPI、本地 Web UI、局域网访问和自动化执行层。",
        "",
        "考虑当前项目定位，建议 M3 优先方向为：",
        "",
        "```text",
        "M3：任务追踪与自动化调度能力",
        "```",
        "",
        "而不是立刻进入复杂 Web UI。",
        "",
    ]


def build_m3_summary_lines() -> list[str]:
    """
    M3 阶段总结内容。

    M3 的定位是索引与检索能力优化阶段，
    不做 Web UI，不做 OpenClaw 自动化。
    """
    return [
        "## 1. M3 阶段定位",
        "",
        "M3 阶段目标是将系统从“能用的本地 RAG 系统”，",
        "升级为“可长期扩展、可快速更新、可评估检索质量的知识库系统”。",
        "",
        "M3 不优先做 Web UI，也不优先做 OpenClaw 自动化，",
        "而是专注索引与检索能力优化。",
        "",
        "M3 重点方向：",
        "",
        "1. 增量索引。",
        "2. 单文件更新。",
        "3. 项目级更新。",
        "4. 删除文件同步清理 Qdrant。",
        "5. 关键词检索。",
        "6. 混合检索。",
        "7. 检索评估。",
        "8. 全量重建与长期维护能力。",
        "",
        "## 2. M3 已完成能力",
        "",
        "### M3.1 index_manifest.json 与 manifest_utils.py",
        "",
        "新增 index_manifest.json 和 manifest_utils.py，",
        "用于记录每个 Markdown 文件的 mtime_ns、size、sha256、chunk_count、point_ids、updated_at 等信息。",
        "",
        "这为后续增量索引、单文件更新、项目级更新和删除文件同步清理 Qdrant 提供基础。",
        "",
        "### M3.2 默认增量索引",
        "",
        "新增 incremental_index.py，并将 update_index.py 改为默认增量更新入口。",
        "",
        "增量索引支持：",
        "",
        "1. added 新增文件入库。",
        "2. changed 修改文件删除旧 points 后重新入库。",
        "3. deleted 删除文件同步清理 Qdrant。",
        "4. unchanged 未变化文件跳过。",
        "",
        "rebuild_index.py 继续保留为全量重建入口。",
        "",
        "### M3.3 单文件更新",
        "",
        "update_index.py 和 incremental_index.py 支持 --file 参数，",
        "可以只更新指定 Markdown 文件。",
        "",
        "支持新增、修改、未变化跳过、--force-file 强制重建，以及文件删除后的 Qdrant points 清理。",
        "",
        "### M3.4 项目级更新",
        "",
        "update_index.py 和 incremental_index.py 支持 --project 参数，",
        "可以只更新指定项目相关 Markdown 文件。",
        "",
        "支持 --force-project 强制重建指定项目内全部现存 Markdown 文件。",
        "",
        "### M3.5 全量重建入口适配",
        "",
        "更新 rebuild_index.py，使其成为专用全量重建入口。",
        "",
        "新版 rebuild_index.py 默认预览，执行 --execute 后会：",
        "",
        "1. 备份旧 index_manifest.json。",
        "2. 尝试保存 list_docs.py 快照。",
        "3. 删除 Qdrant collection。",
        "4. 重置 manifest。",
        "5. 调用 update_index.py --force-all --skip-check 重新入库。",
        "",
        "### M3.6 关键词检索",
        "",
        "增强 search_docs.py，支持 --mode keyword。",
        "",
        "keyword 模式基于 title、file_name、source、tags、doc_type、category、project、text 等字段评分，",
        "适合搜索脚本名、函数名、错误码、精确关键词和路径。",
        "",
        "### M3.7 混合检索",
        "",
        "增强 search_docs.py，支持 --mode hybrid。",
        "",
        "hybrid 模式会同时执行 vector 向量检索和 keyword 关键词检索，",
        "并对结果进行去重、归一化、加权合并。",
        "",
        "支持 --vector-weight 和 --keyword-weight 调整权重。",
        "",
        "### M3.7-b ask.py 接入混合检索",
        "",
        "增强 ask.py，支持 --search-mode vector / keyword / hybrid。",
        "",
        "ask.py 保持原有问答能力，同时可通过 hybrid 模式提高实际问答检索质量。",
        "",
        "### M3.8 retrieval_eval.json 检索评估测试集",
        "",
        "新增 99_System/eval/retrieval_eval.json，包含 15 条检索评估用例，",
        "覆盖 vector、keyword、hybrid 三类典型检索场景。",
        "",
        "### M3.9 retrieval_eval.py 检索评估脚本",
        "",
        "新增 retrieval_eval.py，可自动评估 vector、keyword、hybrid 三种检索模式。",
        "",
        "评估内容包括：",
        "",
        "1. Top1 / Top3 / Top5 命中情况。",
        "2. 每条 case 的首次命中排名。",
        "3. Top 检索结果明细。",
        "4. 未命中详情。",
        "5. Markdown 检索评估报告。",
        "",
        "## 3. M3 当前形成的索引与检索工作流",
        "",
        "### 日常增量更新",
        "",
        "```powershell",
        "python update_index.py",
        "```",
        "",
        "### 单文件更新",
        "",
        "```powershell",
        "python update_index.py --file \"01_Projects/Personal_Project_Assistant/progress_log.md\"",
        "python update_index.py --file \"01_Projects/Personal_Project_Assistant/progress_log.md\" --force-file",
        "```",
        "",
        "### 项目级更新",
        "",
        "```powershell",
        "python update_index.py --project Personal_Project_Assistant",
        "python update_index.py --project Personal_Project_Assistant --force-project",
        "```",
        "",
        "### 全量重建",
        "",
        "```powershell",
        "python rebuild_index.py",
        "python rebuild_index.py --execute",
        "```",
        "",
        "### 三种检索模式",
        "",
        "```powershell",
        "python search_docs.py --mode vector \"当前项目进行到哪里了？\" --show-text",
        "python search_docs.py --mode keyword \"update_index.py\" --show-text",
        "python search_docs.py --mode hybrid \"M3 阶段增量索引做了什么？\" --show-text",
        "```",
        "",
        "### ask.py 三种问答检索模式",
        "",
        "```powershell",
        "python ask.py --search-mode vector \"当前项目进行到哪里了？\"",
        "python ask.py --search-mode keyword \"update_index.py 的作用是什么？\"",
        "python ask.py --search-mode hybrid \"M3 阶段增量索引做了什么？\"",
        "```",
        "",
        "### 检索评估",
        "",
        "```powershell",
        "python retrieval_eval.py --mode vector",
        "python retrieval_eval.py --mode keyword",
        "python retrieval_eval.py --mode hybrid",
        "python retrieval_eval.py --mode all",
        "```",
        "",
        "## 4. M3 封版判断",
        "",
        "M3 可以封版的条件：",
        "",
        "1. index_manifest.json 存在且能记录 Markdown 文件状态。",
        "2. update_index.py 默认增量更新正常。",
        "3. update_index.py --file 单文件更新正常。",
        "4. update_index.py --project 项目级更新正常。",
        "5. rebuild_index.py --execute 全量重建正常。",
        "6. search_docs.py 支持 vector / keyword / hybrid。",
        "7. ask.py 支持 vector / keyword / hybrid。",
        "8. retrieval_eval.json 存在且格式正确。",
        "9. retrieval_eval.py 能生成检索评估报告。",
        "10. health_check_full.py 全链路检查通过。",
        "",
        "如果上述条件满足，则 M3 可作为“索引与检索能力优化阶段”封版。",
        "",
        "## 5. M3 后续维护建议",
        "",
        "1. 日常新增或修改 Markdown 后执行 `python update_index.py`。",
        "2. 只修改一个文件时优先使用 `python update_index.py --file 文件路径`。",
        "3. 只处理一个项目时优先使用 `python update_index.py --project 项目名`。",
        "4. Qdrant 状态异常或索引严重不一致时使用 `python rebuild_index.py --execute`。",
        "5. 查询脚本名、错误码、路径时优先使用 keyword 或 hybrid。",
        "6. 实际问答建议优先尝试 `python ask.py --search-mode hybrid`。",
        "7. 每次大改检索逻辑后执行 `python retrieval_eval.py --mode all`。",
        "",
        "## 6. M4 推荐方向",
        "",
        "M3 完成后，后续可以选择两个方向：",
        "",
        "1. 继续做任务追踪与自动化调度能力。",
        "2. 进入服务化，例如 FastAPI、本地 Web UI、局域网访问、OpenClaw 接入。",
        "",
        "考虑当前项目演进，建议 M4 可优先考虑：",
        "",
        "```text",
        "M4：任务追踪与自动化调度能力",
        "```",
        "",
        "也可以将 FastAPI / Web UI 放到后续阶段，避免过早增加系统复杂度。",
        "",
    ]


def build_generic_summary_lines(milestone: str) -> list[str]:
    """
    未专门配置的里程碑使用这个通用模板。
    """
    return [
        f"## 1. {milestone} 阶段定位",
        "",
        f"{milestone} 阶段尚未配置专门总结模板。",
        "",
        f"## 2. {milestone} 阶段检查说明",
        "",
        "本报告会执行通用检查：",
        "",
        "1. health_check_full.py",
        "2. status.py",
        "3. list_docs.py",
        "",
        "如果需要更完整的封版内容，请在 get_milestone_config() 中增加专门配置。",
        "",
    ]

def save_closeout_report(
    milestone: str,
    milestone_config: dict,
    outputs: dict[str, str],
    results: dict[str, bool],
) -> Path:
    """
    保存阶段封版报告。
    """
    MILESTONE_REPORT_DIR.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
    milestone_upper = milestone.upper()

    report_path = MILESTONE_REPORT_DIR / f"{timestamp}_{milestone_upper}_closeout_report.md"

    lines = []

    lines.append("---")
    lines.append(f"title: {milestone_config['title']} {timestamp}")
    lines.append(f"created: {now.isoformat(timespec='seconds')}")
    lines.append("category: summary")
    lines.append("project: Personal_Project_Assistant")
    lines.append(f"doc_type: {milestone_config['doc_type']}")
    lines.append(f"tags: {milestone_config['tags']}")
    lines.append(f"milestone: {milestone_upper}")
    lines.append("---")
    lines.append("")

    lines.append(f"# {milestone_config['title']}")
    lines.append("")
    lines.append(f"生成时间：{now.isoformat(timespec='seconds')}")
    lines.append(f"知识库根目录：{KNOWLEDGE_ROOT}")
    lines.append(f"阶段定位：{milestone_config['focus']}")
    lines.append("")

    lines.extend(milestone_config["summary_lines"])
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## 自动检查结果摘要")
    lines.append("")

    for name, ok in results.items():
        status = "通过" if ok else "失败"
        lines.append(f"- {name}：{status}")

    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## 自动检查详细输出")
    lines.append("")

    for name, output in outputs.items():
        lines.append(f"### {name}")
        lines.append("")
        lines.append("```text")
        lines.append(output)
        lines.append("```")
        lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path

def main():
    parser = argparse.ArgumentParser(
        description="个人项目秘书 + 数据知识库：通用阶段封版检查"
    )

    parser.add_argument(
        "--milestone",
        required=True,
        help="阶段名称，例如 M1、M2、M3。",
    )

    parser.add_argument(
        "--skip-health",
        action="store_true",
        help="跳过 health_check_full.py，适合快速生成封版报告。",
    )

    parser.add_argument(
        "--skip-extra-checks",
        action="store_true",
        help="跳过该里程碑的额外检索检查。",
    )

    args = parser.parse_args()

    milestone = args.milestone.upper()
    milestone_config = get_milestone_config(milestone)

    print("个人项目秘书 + 数据知识库：通用阶段封版检查")
    print(f"阶段：{milestone}")
    print(f"阶段定位：{milestone_config['focus']}")
    print(f"工作目录：{BASE_DIR}")
    print(f"Python：{sys.executable}")

    checks = []

    if not args.skip_health:
        checks.append(
            ("health_check_full.py", [sys.executable, "health_check_full.py"])
        )

    checks.extend(
        [
            ("status.py", [sys.executable, "status.py"]),
            ("list_docs.py", [sys.executable, "list_docs.py"]),
        ]
    )

    if not args.skip_extra_checks:
        checks.extend(milestone_config.get("extra_checks", []))

    outputs = {}
    results = {}

    for name, command in checks:
        ok, output = run_command(name, command)
        outputs[name] = output
        results[name] = ok

    report_path = save_closeout_report(
        milestone=milestone,
        milestone_config=milestone_config,
        outputs=outputs,
        results=results,
    )

    print("\n" + "=" * 80)
    print("阶段封版检查完成")
    print("=" * 80)
    print("")
    print("封版报告已生成：")
    print(report_path)
    print("")

    if all(results.values()):
        print(f"结论：{milestone} 阶段可以封版。")
    else:
        print(f"结论：{milestone} 阶段仍有检查项失败，请先修复。")

    print("")
    print("建议下一步执行：")
    print("python update_index.py")
    print(
        f'python ask.py --doc-type milestone_report "{milestone} 阶段完成了什么？"'
    )


if __name__ == "__main__":
    main()

