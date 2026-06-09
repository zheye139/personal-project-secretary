# Personal Project Secretary + Knowledge Base Manager

English | [中文说明](#中文说明)

A local-first personal project secretary and knowledge base manager built with **Markdown**, **Ollama**, **Qdrant**, and **Python**.

This project is a local RAG-based workflow for people who want to record, organize, retrieve, summarize, review, and report long-running project information. It is **not** a model training project. Your Markdown files remain the primary data source, and the vector database can be rebuilt at any time.

---

## Current Release Target

```text
v0.3.0-local-index-retrieval
```

This version includes:

- M1: local RAG knowledge-base infrastructure
- M2: personal secretary analysis layer
- M3: index and retrieval optimization layer

It is still a local command-line toolbox. It does not require a Web UI or cloud service.

---

## What This Project Does

This project helps you build a local knowledge workflow for:

- project records
- progress logs
- technical notes
- issue and solution tracking
- decision records
- daily and weekly reports
- project summaries
- personal knowledge notes
- next-action extraction
- project briefs
- multi-project status summaries
- priority advice
- project record reviews
- daily personal secretary reports
- incremental indexing
- single-file and project-level index updates
- keyword and hybrid retrieval
- retrieval quality evaluation

The system is designed around two roles.

### Knowledge Base Manager

Responsible for:

- organizing Markdown documents
- maintaining Frontmatter metadata
- importing inbox notes
- indexing Markdown files into Qdrant
- validating knowledge-base structure
- repairing missing Frontmatter
- backing up and restoring the knowledge base
- exporting project packages
- maintaining incremental index state
- rebuilding Qdrant from Markdown when needed

### Personal Project Secretary

Responsible for:

- answering project questions
- retrieving project knowledge
- generating project reports
- generating daily and weekly reports
- extracting next actions
- generating project briefs
- summarizing multiple projects
- giving priority advice
- reviewing project records for missing information and risks
- generating daily personal secretary reports

---

## Tech Stack

- Python
- Markdown
- Ollama
- qwen3:8b
- bge-m3
- Qdrant
- Docker
- PowerShell

---

## Repository vs. Private Knowledge Base

Keep the code repository and your private knowledge base separate.

Example:

```text
Code repository:
D:\Projects\personal-project-secretary

Private knowledge base:
D:\Personal_Knowledge_Base
```

`KNOWLEDGE_ROOT` in `rag_mvp/config.py` should point to your private Markdown knowledge base, not to this GitHub repository.

Recommended private knowledge-base structure:

```text
Personal_Knowledge_Base/
├─ 00_Inbox/
├─ 01_Projects/
├─ 02_Knowledge/
├─ 03_Decisions/
├─ 04_Problems/
├─ 05_Summaries/
├─ 06_Attachments/
└─ 99_System/
   ├─ backups/
   ├─ docs/
   └─ qdrant_storage/
```

Do not publish your real private knowledge base, Qdrant storage, backups, or personal QA logs to GitHub.

---

## Example Knowledge Base

A minimal example knowledge base is recommended under:

```text
examples/Personal_Knowledge_Base_Template
```

Use sample data for public demos instead of real personal project records.

---

## Quick Start

### 1. Install Ollama Models

```powershell
ollama pull qwen3:8b
ollama pull bge-m3
```

### 2. Start Qdrant with Docker

Use a Qdrant storage path under your private knowledge base:

```powershell
docker run -d --name pkb-qdrant -p 6333:6333 -v D:/Personal_Knowledge_Base/99_System/qdrant_storage:/qdrant/storage qdrant/qdrant
```

If the container already exists:

```powershell
docker start pkb-qdrant
```

### 3. Create Python Environment

```powershell
cd <your-repo-path>\personal-project-secretary\rag_mvp
py -3.11 -m venv .venv
.\.venv\Scripts\activate
pip install -r ..\requirements.txt
```

### 4. Create Local Config

```powershell
Copy-Item .\config.example.py .\config.py
```

Then edit `rag_mvp/config.py`:

```python
from pathlib import Path

KNOWLEDGE_ROOT = Path(r"D:\Personal_Knowledge_Base")
```

Make sure `EMBED_MODEL` matches the model name shown by `ollama list`:

```python
EMBED_MODEL = "bge-m3"
# or
EMBED_MODEL = "bge-m3:latest"
```

### 5. Check Environment

```powershell
python check_env.py
python health_check_full.py
```

### 6. Index Markdown Documents

```powershell
python update_index.py
```

### 7. Ask a Question

```powershell
python ask.py "What is the current project status?"
```

You can also ask in Chinese:

```powershell
python ask.py "当前项目进行到哪里了？"
```

---

## Common Commands

```powershell
python status.py
python list_docs.py
python search_docs.py "Python environment recovery" --show-text
python ask.py --project Demo_Project "What is the project status?"
python project_report.py --project Demo_Project
python time_report.py --project Demo_Project --mode weekly
python backup_kb.py
```

---

## M1 Core Scripts

| Script | Purpose |
|---|---|
| `check_env.py` | Check Ollama, models, Qdrant, and collection status |
| `ingest.py` | Parse Markdown files and index them into Qdrant |
| `ask.py` | Run RAG question answering |
| `search_docs.py` | Search retrieved chunks without calling the chat model |
| `add_note.py` | Add a Markdown note with Frontmatter |
| `inbox_import.py` | Import Markdown files from `00_Inbox` |
| `project_template.py` | Create a standard project folder and Markdown templates |
| `archive_project.py` | Archive inactive or test projects safely |
| `project_report.py` | Generate a project status report |
| `time_report.py` | Generate daily or weekly reports |
| `backup_kb.py` | Create a knowledge-base backup |
| `export_project.py` | Export a project package |
| `validate_kb.py` | Validate Markdown and Frontmatter quality |
| `repair_frontmatter.py` | Repair missing or incomplete Frontmatter |
| `rebuild_index.py` | Rebuild the Qdrant index safely |
| `health_check_full.py` | Run a full system health check |
| `status.py` | Show system status |
| `update_index.py` | Run environment check, indexing, and document listing |

---

## M2 Personal Secretary Scripts

| Script | Purpose | Output doc_type |
|---|---|---|
| `next_action.py` | Extract next actions from project logs, plans, reports, and weekly reports | `next_action_report` |
| `project_brief.py` | Generate a concise single-project brief | `project_brief` |
| `multi_project_status.py` | Summarize multiple project statuses | `multi_project_status` |
| `priority_advisor.py` | Provide project and task priority advice | `priority_advice` |
| `review_assistant.py` | Review project records and identify missing information and risks | `review_report` |
| `secretary_report.py` | Generate a daily personal secretary report | `secretary_report` |
| `milestone_closeout.py` | Generate milestone closeout reports for M1/M2 and later phases | `milestone_report` |

---

## M2 Recommended Workflow

Single project workflow:

```powershell
python next_action.py --project Demo_Project
python project_brief.py --project Demo_Project
python review_assistant.py --project Demo_Project
python update_index.py
```

Multi-project workflow:

```powershell
python multi_project_status.py
python priority_advisor.py
python secretary_report.py
python update_index.py
```

Milestone closeout:

```powershell
python health_check_full.py
python milestone_closeout.py --milestone M2
python update_index.py
```


---

## M3 Index and Retrieval Optimization Scripts

| Script / File | Purpose | Notes |
|---|---|---|
| `manifest_utils.py` | Manage `index_manifest.json` | Tracks Markdown fingerprints, chunk count, and Qdrant point ids |
| `incremental_index.py` | Core incremental indexing engine | Handles added, changed, deleted, and unchanged files |
| `update_index.py` | Daily index update entry | Defaults to incremental indexing |
| `rebuild_index.py` | Full Qdrant rebuild entry | Deletes collection, resets manifest, and rebuilds from Markdown |
| `search_docs.py` | Search chunks with vector / keyword / hybrid modes | Supports `--mode vector`, `--mode keyword`, `--mode hybrid` |
| `ask.py` | RAG Q&A with selectable retrieval mode | Supports `--search-mode vector`, `--search-mode keyword`, `--search-mode hybrid` |
| `retrieval_eval.py` | Retrieval quality evaluation | Reports Top1 / Top3 / Top5 hit rates |
| `retrieval_eval.json` | Retrieval evaluation test set | Stored under `99_System/eval` |

---

## M3 Recommended Workflow

Daily incremental update:

```powershell
python update_index.py
```

Single-file update:

```powershell
python update_index.py --file "01_Projects/Demo_Project/progress_log.md"
python update_index.py --file "01_Projects/Demo_Project/progress_log.md" --force-file
```

Project-level update:

```powershell
python update_index.py --project Demo_Project
python update_index.py --project Demo_Project --force-project
```

Full rebuild:

```powershell
python rebuild_index.py
python rebuild_index.py --execute
```

Search modes:

```powershell
python search_docs.py --mode vector "current project status" --show-text
python search_docs.py --mode keyword "update_index.py" --show-text
python search_docs.py --mode hybrid "M3 incremental indexing" --show-text
```

RAG Q&A retrieval modes:

```powershell
python ask.py --search-mode vector "What is the project status?"
python ask.py --search-mode keyword "What does update_index.py do?"
python ask.py --search-mode hybrid "What did M3 improve?"
```

Retrieval evaluation:

```powershell
python retrieval_eval.py --mode all
```


---

## Documentation

Recommended documentation files:

- `docs/quickstart.md` - bilingual quick start
- `docs/environment_setup.md` - environment setup
- `docs/command_reference.md` - command reference
- `docs/restore_guide.md` - recovery guide
- `docs/rag_mvp_readme.md` - engineering notes
- `docs/roadmap.md` - roadmap

---

## Roadmap

Completed:

```text
M1: Local RAG knowledge-base infrastructure
M2: Personal secretary analysis layer
M3: Index and retrieval optimization layer
```

---

# 中文说明

这是一个本地优先的“个人项目秘书 + 知识库管理员”系统，使用 **Markdown** 作为主数据源，**Qdrant** 作为可重建向量索引，**Ollama** 本地模型用于问答、总结、项目报告和个人秘书汇报生成。

本项目不是模型训练项目，而是一个面向个人长期项目管理的本地 RAG 知识工作流。

---

## 当前发布目标

```text
v0.3.0-local-index-retrieval
```

当前版本包含：

- M1：本地 RAG 知识库基础设施
- M2：个人秘书分析层
- M3：索引与检索能力优化层

该版本仍然是本地命令行工具箱，不依赖 Web UI 或云服务。

---

## 项目用途

本项目用于帮助个人管理：

- 项目记录
- 进度日志
- 技术笔记
- 问题与解决方案
- 决策记录
- 日报与周报
- 项目总结
- 个人知识笔记
- 下一步行动提取
- 项目简报
- 多项目状态汇总
- 优先级建议
- 项目记录复盘
- 个人秘书汇报
- 增量索引
- 单文件和项目级索引更新
- 关键词检索与混合检索
- 检索质量评估

---

## 核心定位

系统包含两个角色。

### 知识库管理员

负责：

- 整理 Markdown 文档
- 维护 Frontmatter 元数据
- 导入 Inbox 临时记录
- 将 Markdown 文档入库到 Qdrant
- 检查知识库结构
- 修复缺失或不完整 Frontmatter
- 备份与恢复知识库
- 导出项目资料包

### 个人项目秘书

负责：

- 回答项目问题
- 调取项目知识
- 生成项目状态报告
- 生成日报和周报
- 提取下一步行动
- 生成项目简报
- 汇总多个项目状态
- 给出优先级建议
- 复盘项目记录中的遗漏和风险
- 生成日常个人秘书汇报

---

## 代码仓库与知识库目录需要分开

示例：

```text
代码仓库：
D:\Projects\personal-project-secretary

私人知识库：
D:\Personal_Knowledge_Base
```

`rag_mvp/config.py` 中的 `KNOWLEDGE_ROOT` 应指向私人 Markdown 知识库目录，而不是 GitHub 代码仓库目录。

不要把真实个人知识库、Qdrant 数据、备份文件和问答日志上传到 GitHub。

---

## 快速开始

```powershell
ollama pull qwen3:8b
ollama pull bge-m3

docker run -d --name pkb-qdrant -p 6333:6333 -v D:/Personal_Knowledge_Base/99_System/qdrant_storage:/qdrant/storage qdrant/qdrant

cd <your-repo-path>\personal-project-secretary\rag_mvp
py -3.11 -m venv .venv
.\.venv\Scripts\activate
pip install -r ..\requirements.txt

Copy-Item .\config.example.py .\config.py
python check_env.py
python health_check_full.py
python update_index.py
python ask.py "当前项目进行到哪里了？"
```

---

## M1 核心脚本

| 脚本 | 作用 |
|---|---|
| `check_env.py` | 检查 Ollama、模型、Qdrant 和集合状态 |
| `ingest.py` | 解析 Markdown 并入库到 Qdrant |
| `ask.py` | 执行 RAG 问答 |
| `search_docs.py` | 搜索知识库片段，不调用聊天模型 |
| `add_note.py` | 新增带 Frontmatter 的 Markdown 记录 |
| `inbox_import.py` | 从 `00_Inbox` 导入 Markdown |
| `project_template.py` | 创建标准项目目录和 Markdown 模板 |
| `archive_project.py` | 安全归档暂停或测试项目 |
| `project_report.py` | 生成项目状态报告 |
| `time_report.py` | 生成日报或周报 |
| `backup_kb.py` | 备份知识库 |
| `export_project.py` | 导出项目资料包 |
| `validate_kb.py` | 检查 Markdown 和 Frontmatter 规范 |
| `repair_frontmatter.py` | 修复缺失或不完整 Frontmatter |
| `rebuild_index.py` | 安全重建 Qdrant 索引 |
| `health_check_full.py` | 全链路健康检查 |
| `status.py` | 查看系统状态 |
| `update_index.py` | 执行环境检查、入库和文档列表检查 |

---

## M2 个人秘书脚本

| 脚本 | 作用 | 输出 doc_type |
|---|---|---|
| `next_action.py` | 提取项目下一步行动项 | `next_action_report` |
| `project_brief.py` | 生成单项目简报 | `project_brief` |
| `multi_project_status.py` | 汇总多个项目状态 | `multi_project_status` |
| `priority_advisor.py` | 给出项目和任务优先级建议 | `priority_advice` |
| `review_assistant.py` | 复盘项目记录，指出遗漏和风险 | `review_report` |
| `secretary_report.py` | 生成日常个人秘书汇报 | `secretary_report` |
| `milestone_closeout.py` | 为 M1/M2 和后续阶段生成阶段封版报告 | `milestone_report` |

---

## M3 索引与检索优化脚本

| 脚本 / 文件 | 作用 | 说明 |
|---|---|---|
| `manifest_utils.py` | 管理 `index_manifest.json` | 记录 Markdown 文件指纹、片段数量和 Qdrant point ids |
| `incremental_index.py` | 增量索引核心引擎 | 处理 added、changed、deleted、unchanged 文件 |
| `update_index.py` | 日常索引更新入口 | 默认执行增量更新 |
| `rebuild_index.py` | 全量重建入口 | 删除 collection、重置 manifest、从 Markdown 重新入库 |
| `search_docs.py` | 支持 vector / keyword / hybrid 的检索工具 | 支持 `--mode vector`、`--mode keyword`、`--mode hybrid` |
| `ask.py` | 支持检索模式选择的 RAG 问答入口 | 支持 `--search-mode vector`、`--search-mode keyword`、`--search-mode hybrid` |
| `retrieval_eval.py` | 检索质量评估脚本 | 输出 Top1 / Top3 / Top5 命中率 |
| `retrieval_eval.json` | 检索评估测试集 | 位于 `99_System/eval` |

---

## M3 推荐工作流

日常增量更新：

```powershell
python update_index.py
```

单文件更新：

```powershell
python update_index.py --file "01_Projects/Demo_Project/progress_log.md"
python update_index.py --file "01_Projects/Demo_Project/progress_log.md" --force-file
```

项目级更新：

```powershell
python update_index.py --project Demo_Project
python update_index.py --project Demo_Project --force-project
```

全量重建：

```powershell
python rebuild_index.py
python rebuild_index.py --execute
```

三种检索模式：

```powershell
python search_docs.py --mode vector "当前项目状态" --show-text
python search_docs.py --mode keyword "update_index.py" --show-text
python search_docs.py --mode hybrid "M3 增量索引" --show-text
```

RAG 问答检索模式：

```powershell
python ask.py --search-mode vector "当前项目状态是什么？"
python ask.py --search-mode keyword "update_index.py 的作用是什么？"
python ask.py --search-mode hybrid "M3 阶段改进了什么？"
```

检索评估：

```powershell
python retrieval_eval.py --mode all
```

---

## M2 推荐工作流

单项目工作流：

```powershell
python next_action.py --project Demo_Project
python project_brief.py --project Demo_Project
python review_assistant.py --project Demo_Project
python update_index.py
```

多项目工作流：

```powershell
python multi_project_status.py
python priority_advisor.py
python secretary_report.py
python update_index.py
```

阶段封版：

```powershell
python health_check_full.py
python milestone_closeout.py --milestone M2
python update_index.py
```

---

## 文档

推荐文档文件：

- `docs/quickstart.md`：双语快速开始
- `docs/environment_setup.md`：环境安装说明
- `docs/command_reference.md`：命令速查表
- `docs/restore_guide.md`：恢复流程
- `docs/rag_mvp_readme.md`：工程说明
- `docs/roadmap.md`：路线图

---

## 路线图

已完成：

```text
M1：本地 RAG 知识库基础设施
M2：个人秘书分析层
M3：索引与检索能力优化层
```

---
