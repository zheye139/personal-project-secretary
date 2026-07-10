# Knowledge Operating System

**A Local-First Personal Project Secretary and Knowledge Base Manager**

English | [中文说明](#中文说明)

A local-first knowledge operating system built with **Markdown**, **Ollama**, **Qdrant**, **Python**, **FastAPI**, and a configurable **Vector Store** connection layer.

The current release focuses on project knowledge capture, retrieval, reporting, personal secretary workflows, local Web/API access, and configurable Qdrant deployment. Markdown remains the primary source of truth, while Qdrant remains a rebuildable vector index.

This is not a model-training project, and it is not a public cloud service.

---

## Current Release

```text
v0.5.0-vector-store-config
```

This release includes:

- M1: local RAG knowledge-base infrastructure
- M2: personal secretary analysis layer
- M3: index and retrieval optimization layer
- M4: local console, FastAPI API, and local Web interface
- M5: Vector Store configuration and cross-PC deployment validation

M5 adds a unified Qdrant configuration layer, environment-variable overrides, local/LAN/remote Qdrant access, cross-PC validation, and updated deployment documentation.

The current Vector Store backend is still Qdrant. M5 decouples the application from a fixed `localhost` deployment, but does not yet provide Milvus, pgvector, Weaviate, or other Vector Store implementations.

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
- local terminal launcher
- local FastAPI API
- local Web interface
- Search and Ask browser pages
- local diagnostics and troubleshooting pages
- configurable Vector Store connection
- local Docker Qdrant
- LAN or remote Qdrant
- virtual-machine-to-host Qdrant access
- environment-variable configuration
- cross-PC deployment validation

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

## Core Architecture

```text
Private Markdown Knowledge Base
            ↓
      Indexing Layer
            ↓
Vector Store Configuration
            ↓
 Local / LAN / Remote Qdrant
            ↓
 Search / Ask / Reports / Secretary
            ↓
 Local Console / FastAPI / Web
```

Core principles:

1. Markdown is the primary source of truth.
2. Qdrant is a rebuildable vector index.
3. Ollama provides local model services.
4. Python scripts provide indexing, retrieval, reporting, and secretary workflows.
5. Environment variables can override deployment-specific configuration.
6. `config.py` remains a local configuration fallback.
7. `vector_store_config.py` is the shared Qdrant connection layer.
8. The Web/API layer remains local-first and is not intended for public-network exposure.

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
- FastAPI
- Uvicorn
- HTTPX
- local HTML/CSS/JavaScript Web interface
- Vector Store configuration layer

---

## Repository vs. Private Knowledge Base

Keep the code repository and your private knowledge base separate.

Example:

```text
Code repository:
<your-repo-path>\Knowledge_Operating_System

Private knowledge base:
<your-knowledge-root>
```

The knowledge-base root can be configured through `PKB_KNOWLEDGE_ROOT` or the local `rag_mvp/config.py`.

Configuration priority:

```text
environment variables
    ↓
config.py
    ↓
built-in defaults
```

The configured knowledge-base root must point to your private Markdown knowledge base, not to this GitHub repository.

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

Do not publish your real private knowledge base, Qdrant storage, backups, personal QA logs, real local paths, or private network addresses to GitHub.

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

Check the installed models:

```powershell
ollama list
```

Make sure the model names shown by `ollama list` match the values configured in `config.py` or the corresponding environment variables.

### 2. Configure Qdrant

#### Option A: Start Qdrant with Docker

Use a Qdrant storage path under your private knowledge base:

```powershell
docker run -d --name pkb-qdrant -p 6333:6333 -v <your-knowledge-root>/99_System/qdrant_storage:/qdrant/storage qdrant/qdrant
```

If the container already exists:

```powershell
docker start pkb-qdrant
```

Check Qdrant:

```powershell
curl.exe http://127.0.0.1:6333/
curl.exe http://127.0.0.1:6333/collections
```

#### Option B: Use an Existing LAN or Remote Qdrant Service

Check the network connection:

```powershell
Test-NetConnection <qdrant-host> -Port 6333
curl.exe http://<qdrant-host>:6333/
```

Then configure:

```powershell
$env:PKB_QDRANT_URL = "http://<qdrant-host>:6333"
$env:PKB_QDRANT_COLLECTION = "personal_knowledge_base"
```

Important:

- `127.0.0.1` always refers to the machine on which the current process is running.
- A virtual machine must use a reachable host or LAN address to access Qdrant running on another machine.
- The configured collection name must match the intended target collection.
- LAN or remote Qdrant access is intended for trusted private networks.
- M5 does not provide a public-Internet exposure or authentication design for Qdrant.
- Do not expose port `6333` directly to the public Internet without a dedicated security architecture.

### 3. Create the Python Environment

Python 3.11 is the recommended public deployment baseline. Newer Python versions may work, but should be validated against the project's third-party dependencies before being documented as supported.

```powershell
cd <your-repo-path>\Knowledge_Operating_System\rag_mvp

py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -r ..\requirements.txt
```

Each PC and each Python virtual environment must install its own dependencies.

Installing `qdrant-client` on the development PC does not automatically install it inside another PC or virtual machine.

### 4. Configure the Local Environment

The project supports both environment variables and a local `config.py`.

Configuration priority:

```text
environment variables
    ↓
config.py
    ↓
built-in defaults
```

To create a local configuration file:

```powershell
Copy-Item .\config.example.py .\config.py
```

Then edit `rag_mvp/config.py` as needed:

```python
from pathlib import Path

KNOWLEDGE_ROOT = Path(r"<your-knowledge-root>")
```

You can also override deployment-specific values with environment variables:

```powershell
$env:PKB_KNOWLEDGE_ROOT = "<your-knowledge-root>"

$env:PKB_OLLAMA_URL = "http://127.0.0.1:11434"
$env:PKB_CHAT_MODEL = "qwen3:8b"
$env:PKB_EMBED_MODEL = "bge-m3:latest"

$env:PKB_QDRANT_URL = "http://127.0.0.1:6333"
$env:PKB_QDRANT_TIMEOUT = "120"
$env:PKB_QDRANT_COLLECTION = "personal_knowledge_base"
```

Make sure `EMBED_MODEL` matches the model name shown by `ollama list`:

```python
EMBED_MODEL = "bge-m3"
# or
EMBED_MODEL = "bge-m3:latest"
```

### 5. Run Non-Destructive Environment Checks

```powershell
python check_env.py
python status.py
python inspect_collection.py
python list_docs.py
```

These commands are intended for normal, non-destructive environment validation.

`health_check_full.py` is a full write-path test. It may create, write, search, and delete a temporary Qdrant collection, so run it only after confirming that the target test environment allows those operations.

### 6. Index Markdown Documents

Before indexing, confirm that:

- `PKB_KNOWLEDGE_ROOT` or `config.py` points to the intended private knowledge base.
- `PKB_QDRANT_URL` points to the intended Qdrant service.
- `PKB_QDRANT_COLLECTION` points to the intended collection.

Then run:

```powershell
python update_index.py
```

### 7. Search and Ask

Search without calling the chat model:

```powershell
python search_docs.py "current project status"
```

Ask a question:

```powershell
python ask.py "What is the current project status?"
```

You can also ask in Chinese:

```powershell
python ask.py "当前项目进行到哪里了？"
```

---

## M4 Local Console, API, and Web Interface

M4 adds a local interaction layer on top of the M1-M3 command-line workflow.

### Local Console

```powershell
cd rag_mvp
.\.venv\Scripts\python.exe launcher.py
```

The launcher provides a guided terminal menu for status checks, Ask, Search, adding notes, updating the index, reports, retrieval evaluation, backup, advanced maintenance, and starting the local API server.

### Local Web/API

```powershell
cd rag_mvp
.\run_api.ps1
```

If PowerShell blocks the script:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\run_api.ps1
```

`-Scope Process` affects only the current PowerShell process and is reset when the PowerShell window is closed.

Open in a browser:

```text
http://127.0.0.1:8000/
http://127.0.0.1:8000/search
http://127.0.0.1:8000/ask
http://127.0.0.1:8000/diagnostics
http://127.0.0.1:8000/troubleshooting
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/api
```

Main M4 pages:

- `/` - local homepage
- `/search` - local knowledge-base search
- `/ask` - local RAG question answering
- `/diagnostics` - local API, Qdrant, Ollama, Discovery, and Commands diagnostics
- `/troubleshooting` - local troubleshooting guide
- `/docs` - FastAPI documentation
- `/api` - API overview

Main M4 API endpoints:

- `GET /api`
- `GET /api/v1/health`
- `GET /api/v1/commands`
- `GET /api/v1/discovery/summary`
- `GET /api/v1/discovery/projects`
- `GET /api/v1/discovery/doc-types`
- `GET /api/v1/discovery/categories`
- `GET /api/v1/discovery/tags`
- `GET /api/v1/search`
- `POST /api/v1/ask`
- `GET /api/v1/diagnostics`

M4 safety boundaries:

- The local API binds to `127.0.0.1` by default.
- The Web/API layer is not intended for public-network exposure.
- Web pages do not use external CDN assets.
- Web pages do not execute `update_index`, `rebuild`, `backup`, or `add_note`.
- Search does not write to the knowledge base.
- Ask does not save QA logs by default.
- `save_log=true` is currently rejected.
- API/Web responses should not expose local absolute paths, configuration URLs, raw context, prompts, raw payloads, full Markdown text, source paths, stack traces, or raw exception text.

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
| `search_docs.py` | Search indexed knowledge chunks without calling the chat model |
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
| `rebuild_index.py` | Rebuild the target Qdrant collection after confirming the configured URL, collection name, and knowledge-base root |
| `health_check_full.py` | Run a full write-path system health check |
| `status.py` | Show system status |
| `update_index.py` | Run environment checks, indexing, and document listing |

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
python milestone_closeout.py --milestone M2
python update_index.py
```

For a full write-path health test, run the following separately after confirming that temporary collection creation and deletion are allowed:

```powershell
python health_check_full.py
```


---

## M3 Index and Retrieval Optimization Scripts

| Script / File | Purpose | Notes |
|---|---|---|
| `manifest_utils.py` | Manage `index_manifest.json` | Tracks Markdown fingerprints, chunk count, and Qdrant point IDs |
| `incremental_index.py` | Core incremental indexing engine | Handles added, changed, deleted, and unchanged files |
| `update_index.py` | Daily index update entry | Defaults to incremental indexing |
| `rebuild_index.py` | Full Qdrant rebuild entry | Deletes the target collection, resets the manifest, and rebuilds from Markdown |
| `search_docs.py` | Search chunks with vector, keyword, or hybrid modes | Supports `--mode vector`, `--mode keyword`, and `--mode hybrid` |
| `ask.py` | RAG Q&A with selectable retrieval mode | Supports `--search-mode vector`, `--search-mode keyword`, and `--search-mode hybrid` |
| `retrieval_eval.py` | Retrieval quality evaluation | Reports Top1, Top3, and Top5 hit rates |
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
```

`--execute` changes the target collection. Confirm the configured Qdrant URL, collection name, and knowledge-base root before running it.

```powershell
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

## M4 Local Console / API / Web Files

| File | Purpose |
|---|---|
| `command_registry.py` | Command registry and metadata |
| `launcher.py` | Local terminal menu |
| `project_discovery.py` | Discover projects, categories, document types, tags, files, and summary data |
| `run_api.ps1` | Start the local API/Web service |
| `api_app.py` | FastAPI app, API routes, and Web page routes |
| `tests/test_api_app.py` | API and Web safety tests |
| `web/index.html` | Local homepage |
| `web/search.html` | Search page |
| `web/ask.html` | Ask page |
| `web/diagnostics.html` | Diagnostics page |
| `web/troubleshooting.html` | Troubleshooting guide |


---

## M5 Vector Store Configuration

M5 introduces:

```text
rag_mvp/vector_store_config.py
```

The application now reads Qdrant configuration through a shared Vector Store configuration layer.

Configuration priority:

```text
environment variables
    ↓
config.py
    ↓
built-in defaults
```

Supported environment variables:

| Variable | Purpose |
|---|---|
| `PKB_KNOWLEDGE_ROOT` | private Markdown knowledge-base root |
| `PKB_OLLAMA_URL` | Ollama service URL |
| `PKB_CHAT_MODEL` | chat model name |
| `PKB_EMBED_MODEL` | embedding model name |
| `PKB_QDRANT_URL` | Qdrant service URL |
| `PKB_QDRANT_TIMEOUT` | Qdrant timeout in seconds |
| `PKB_QDRANT_COLLECTION` | Qdrant collection name |

Local Qdrant example:

```powershell
$env:PKB_QDRANT_URL = "http://127.0.0.1:6333"
$env:PKB_QDRANT_COLLECTION = "personal_knowledge_base"
```

LAN or remote Qdrant example:

```powershell
$env:PKB_QDRANT_URL = "http://<qdrant-host>:6333"
$env:PKB_QDRANT_COLLECTION = "personal_knowledge_base"
```

Important:

- `127.0.0.1` always means the machine on which the current process is running.
- A virtual machine must use a reachable host or LAN address to access Qdrant on another PC.
- The configured collection name must match the intended target collection.
- The Web/API server still binds to `127.0.0.1:8000` by default and is not intended for public-network exposure.
- LAN or remote Qdrant access is intended for trusted private networks.
- M5 does not provide a public-Internet exposure or authentication design for Qdrant.
- Do not expose port `6333` directly to the public Internet without a dedicated security architecture.

---

## M5 Non-destructive Validation

```powershell
python check_env.py
python status.py
python inspect_collection.py
python list_docs.py

python search_docs.py "M5 Vector Store"
python ask.py "Please briefly explain the current knowledge base."
```

`health_check_full.py` is a full write-path test. It may create, write, search, and delete a temporary Qdrant collection, so run it only after explicit confirmation.

---

## Documentation

Recommended documentation files:

- `docs/quickstart.md` - bilingual quick start
- `docs/environment_setup.md` - environment setup
- `docs/command_reference.md` - command reference
- `docs/restore_guide.md` - recovery guide
- `docs/rag_mvp_readme.md` - engineering notes
- `docs/roadmap.md` - roadmap
- `docs/local_console.md` - local terminal launcher guide
- `docs/local_web_api.md` - local Web/API guide
- `docs/m4_release_notes.md` - M4 release notes
- `docs/m5_release_notes.md` - M5 release notes
- `docs/vector_store_configuration.md` - Vector Store and Qdrant deployment guide
- `docs/environment_variables.md` - temporary and persistent environment-variable operations

---

## Roadmap

Completed:

```text
M1: Local RAG knowledge-base infrastructure
M2: Personal secretary analysis layer
M3: Index and retrieval optimization layer
M4: Local console, API, and Web interface
M5: Vector Store configuration and cross-PC deployment validation
```

See `docs/roadmap.md` for details.

---
# 中文说明

## Knowledge Operating System

**个人项目秘书 + 知识库管理员**

Knowledge Operating System 是一个本地优先的知识操作系统，基于 **Markdown**、**Ollama**、**Qdrant**、**Python**、**FastAPI** 以及可配置的 **Vector Store（向量存储）连接层**构建。

当前版本重点面向长期项目知识的记录、检索、汇报、个人秘书工作流、本地 Web/API 使用，以及可配置的 Qdrant 部署。Markdown 仍然是系统的主要数据源，Qdrant 则作为可随时重建的向量索引。

本项目不是大模型训练项目，也不是面向公网的云服务。

---

## 当前发布版本

```text
v0.5.0-vector-store-config
```

当前版本包含：

- M1：本地 RAG 知识库基础设施
- M2：个人秘书分析层
- M3：索引与检索优化层
- M4：本地控制台、FastAPI API 与本地 Web 界面
- M5：Vector Store 配置层与跨 PC 部署验证

M5 新增统一的 Qdrant 配置层、环境变量覆盖、本机/局域网/远程 Qdrant 访问、跨 PC 部署验证，以及对应的部署文档。

当前实际实现的 Vector Store 后端仍然是 Qdrant。M5 完成的是应用程序与固定 `localhost` 部署方式的解耦，尚未实现 Milvus、pgvector、Weaviate 或其他 Vector Store 后端。

---

## 项目可以做什么

本项目用于构建本地知识工作流，可管理和处理：

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
- 日常个人秘书汇报
- 增量索引
- 单文件索引更新
- 项目级索引更新
- 关键词检索
- 混合检索
- 检索质量评估
- 本地终端启动器
- 本地 FastAPI API
- 本地 Web 首页
- Search 与 Ask 浏览器页面
- 本地诊断与故障排查页面
- 可配置的 Vector Store 连接
- 本机 Docker Qdrant
- 局域网或远程 Qdrant
- 虚拟机访问宿主机 Qdrant
- 环境变量配置
- 跨 PC 部署验证

系统围绕两个主要角色设计。

### 知识库管理员

主要负责：

- 整理 Markdown 文档
- 维护 Frontmatter 元数据
- 导入 Inbox 临时记录
- 将 Markdown 文档索引到 Qdrant
- 检查知识库结构
- 修复缺失或不完整的 Frontmatter
- 备份和恢复知识库
- 导出项目资料包
- 维护增量索引状态
- 在需要时根据 Markdown 重新构建 Qdrant 索引

### 个人项目秘书

主要负责：

- 回答项目问题
- 调取项目知识
- 生成项目报告
- 生成日报和周报
- 提取下一步行动
- 生成项目简报
- 汇总多个项目的状态
- 给出优先级建议
- 复盘项目记录中的缺失信息和风险
- 生成日常个人秘书汇报

---

## 技术栈

- Python
- Markdown
- Ollama
- qwen3:8b
- bge-m3
- Qdrant
- Docker
- PowerShell
- FastAPI
- Uvicorn
- HTTPX
- 本地 Web 浏览器
- Vector Store 配置层

---

## 代码仓库与私人知识库应分开

请将代码仓库与私人知识库目录分开管理。

示例：

```text
代码仓库：
<your-repo-path>\Knowledge_Operating_System

私人知识库：
<your-knowledge-root>
```

知识库根目录可以通过环境变量 `PKB_KNOWLEDGE_ROOT` 配置，也可以在本地 `rag_mvp/config.py` 中配置。

配置的知识库根目录应指向私人 Markdown 知识库，而不是 GitHub 代码仓库。

推荐的私人知识库目录结构：

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

不要将真实私人知识库、Qdrant 存储目录、备份文件或个人问答日志发布到 GitHub。

---

## 示例知识库

建议在以下目录提供最小示例知识库：

```text
examples/Personal_Knowledge_Base_Template
```

公开演示时请使用示例数据，不要使用真实的个人项目记录。

---

## 快速开始

### 1. 安装 Ollama 模型

```powershell
ollama pull qwen3:8b
ollama pull bge-m3
```

查看已安装模型：

```powershell
ollama list
```

---

### 2. 使用 Docker 启动 Qdrant

建议将 Qdrant 存储目录放在私人知识库目录下：

```powershell
docker run -d --name pkb-qdrant -p 6333:6333 -v <your-knowledge-root>/99_System/qdrant_storage:/qdrant/storage qdrant/qdrant
```

如果容器已经存在：

```powershell
docker start pkb-qdrant
```

检查 Qdrant：

```powershell
curl.exe http://127.0.0.1:6333/
curl.exe http://127.0.0.1:6333/collections
```

---

### 3. 创建 Python 环境

推荐使用 Python 3.11 作为公开部署基线。其他较新版本需要自行确认第三方依赖兼容性。

```powershell
cd <your-repo-path>\Knowledge_Operating_System\rag_mvp

py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -r ..\requirements.txt
```

每台 PC、每个 Python 虚拟环境都需要独立安装项目依赖。

开发机已经安装的 `qdrant-client`，不会自动出现在另一台 PC 或虚拟机的 Python 环境中。

---

### 4. 创建本地配置

复制公开配置示例：

```powershell
Copy-Item .\config.example.py .\config.py
```

然后根据需要编辑 `rag_mvp/config.py`：

```python
from pathlib import Path

KNOWLEDGE_ROOT = Path(r"<your-knowledge-root>")
```

也可以使用环境变量覆盖部署相关配置：

```powershell
$env:PKB_KNOWLEDGE_ROOT = "<your-knowledge-root>"
$env:PKB_QDRANT_URL = "http://127.0.0.1:6333"
$env:PKB_QDRANT_COLLECTION = "personal_knowledge_base"
```

请确保 `EMBED_MODEL` 与 `ollama list` 显示的模型名称一致：

```python
EMBED_MODEL = "bge-m3"
# 或
EMBED_MODEL = "bge-m3:latest"
```

---

### 5. 执行非破坏性环境检查

```powershell
python check_env.py
python status.py
python inspect_collection.py
python list_docs.py
```

这些命令主要用于检查当前配置、Ollama、Qdrant、Collection 和已索引文档状态。

`health_check_full.py` 属于完整写入链路测试，可能创建、写入、检索并删除临时 Qdrant Collection，不应作为普通只读环境检查默认执行。

---

### 6. 索引 Markdown 文档

执行前，请先确认：

- `PKB_KNOWLEDGE_ROOT` 或 `config.py` 指向正确的私人知识库
- `PKB_QDRANT_URL` 指向正确的 Qdrant
- `PKB_QDRANT_COLLECTION` 指向预期的 Collection

然后执行：

```powershell
python update_index.py
```

---

### 7. 提问测试

```powershell
python ask.py "当前项目状态是什么？"
```

也可以先只测试检索：

```powershell
python search_docs.py "当前项目状态"
```

---

## M4 本地控制台、API 与 Web 界面

M4 在 M1～M3 命令行工作流的基础上，增加了本地交互层。

### 本地控制台

```powershell
cd rag_mvp
.\.venv\Scripts\python.exe launcher.py
```

本地终端启动器提供引导式菜单，可执行状态检查、Ask、Search、添加笔记、更新索引、生成报告、检索评估、备份、高级维护以及启动本地 API 服务等操作。

### 本地 Web/API

```powershell
cd rag_mvp
.\run_api.ps1
```

如果 PowerShell 阻止执行 `.ps1` 文件，可仅对当前 PowerShell 进程临时放行：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\run_api.ps1
```

`-Scope Process` 只影响当前 PowerShell 进程，关闭窗口后失效。

在浏览器中打开：

```text
http://127.0.0.1:8000/
http://127.0.0.1:8000/search
http://127.0.0.1:8000/ask
http://127.0.0.1:8000/diagnostics
http://127.0.0.1:8000/troubleshooting
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/api
```

M4 主要页面：

- `/`：本地首页
- `/search`：本地知识库搜索
- `/ask`：本地 RAG 问答
- `/diagnostics`：本地 API、Qdrant、Ollama、Discovery 和 Commands 诊断
- `/troubleshooting`：本地故障排查指南
- `/docs`：FastAPI 自动文档
- `/api`：API 总览

M4 主要 API：

- `GET /api`
- `GET /api/v1/health`
- `GET /api/v1/commands`
- `GET /api/v1/discovery/summary`
- `GET /api/v1/discovery/projects`
- `GET /api/v1/discovery/doc-types`
- `GET /api/v1/discovery/categories`
- `GET /api/v1/discovery/tags`
- `GET /api/v1/search`
- `POST /api/v1/ask`
- `GET /api/v1/diagnostics`

M4 安全边界：

- 本地 API 默认绑定到 `127.0.0.1`
- Web/API 不用于公网暴露
- Web 页面不使用外部 CDN 资源
- Web 页面不执行 `update_index`、`rebuild`、`backup` 或 `add_note`
- Search 不写入知识库
- Ask 默认不保存 QA 日志
- 当前会拒绝 `save_log=true`
- API/Web 响应不应暴露本地绝对路径、配置 URL、原始上下文、Prompt、原始 Payload、完整 Markdown 正文、源文件路径、堆栈跟踪或原始异常文本

---

## 常用命令

```powershell
python status.py
python list_docs.py
python search_docs.py "Python 环境恢复" --show-text
python ask.py --project Demo_Project "当前项目状态是什么？"
python project_report.py --project Demo_Project
python time_report.py --project Demo_Project --mode weekly
python backup_kb.py
```

---

## M1 核心脚本

| 脚本 | 作用 |
|---|---|
| `check_env.py` | 检查 Ollama、模型、Qdrant 和 Collection 状态 |
| `ingest.py` | 解析 Markdown 文件并索引到 Qdrant |
| `ask.py` | 执行 RAG 问答 |
| `search_docs.py` | 搜索已检索到的知识片段，不调用聊天模型 |
| `add_note.py` | 新增带 Frontmatter 的 Markdown 笔记 |
| `inbox_import.py` | 从 `00_Inbox` 导入 Markdown 文件 |
| `project_template.py` | 创建标准项目目录和 Markdown 模板 |
| `archive_project.py` | 安全归档暂停或测试项目 |
| `project_report.py` | 生成项目状态报告 |
| `time_report.py` | 生成日报或周报 |
| `backup_kb.py` | 创建知识库备份 |
| `export_project.py` | 导出项目资料包 |
| `validate_kb.py` | 检查 Markdown 和 Frontmatter 规范 |
| `repair_frontmatter.py` | 修复缺失或不完整的 Frontmatter |
| `rebuild_index.py` | 重建 Qdrant 索引；执行前应确认目标 Collection |
| `health_check_full.py` | 执行包含临时写入的完整系统健康检查 |
| `status.py` | 显示系统状态 |
| `update_index.py` | 执行环境检查、索引更新和文档列表检查 |

---

## M2 个人秘书脚本

| 脚本 | 作用 | 输出 `doc_type` |
|---|---|---|
| `next_action.py` | 从项目日志、计划、报告和周报中提取下一步行动 | `next_action_report` |
| `project_brief.py` | 生成简明的单项目简报 | `project_brief` |
| `multi_project_status.py` | 汇总多个项目的状态 | `multi_project_status` |
| `priority_advisor.py` | 提供项目和任务优先级建议 | `priority_advice` |
| `review_assistant.py` | 复盘项目记录并识别缺失信息和风险 | `review_report` |
| `secretary_report.py` | 生成日常个人秘书汇报 | `secretary_report` |
| `milestone_closeout.py` | 为 M1、M2 及后续阶段生成里程碑封版报告 | `milestone_report` |

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

里程碑封版：

```powershell
python milestone_closeout.py --milestone M2
python update_index.py
```

如需执行完整健康检查，请先确认允许创建和删除临时测试 Collection，再单独执行：

```powershell
python health_check_full.py
```

---

## M3 索引与检索优化脚本

| 脚本 / 文件 | 作用 | 说明 |
|---|---|---|
| `manifest_utils.py` | 管理 `index_manifest.json` | 记录 Markdown 文件指纹、片段数量和 Qdrant Point ID |
| `incremental_index.py` | 增量索引核心引擎 | 处理新增、修改、删除和未变化文件 |
| `update_index.py` | 日常索引更新入口 | 默认执行增量索引 |
| `rebuild_index.py` | 全量重建 Qdrant 的入口 | 删除目标 Collection、重置 Manifest 并根据 Markdown 重建 |
| `search_docs.py` | 支持向量、关键词和混合模式的检索工具 | 支持 `--mode vector`、`--mode keyword`、`--mode hybrid` |
| `ask.py` | 支持选择检索模式的 RAG 问答入口 | 支持 `--search-mode vector`、`--search-mode keyword`、`--search-mode hybrid` |
| `retrieval_eval.py` | 检索质量评估脚本 | 输出 Top1、Top3 和 Top5 命中率 |
| `retrieval_eval.json` | 检索评估测试集 | 存放在 `99_System/eval` |

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

执行 `--execute` 前，请确认目标 Qdrant URL、Collection 名称和私人知识库路径均正确。

检索模式：

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

## M4 本地控制台 / API / Web 文件

| 文件 | 作用 |
|---|---|
| `command_registry.py` | 命令注册表和命令元数据 |
| `launcher.py` | 本地终端菜单 |
| `project_discovery.py` | 发现项目、分类、文档类型、标签、文件和汇总信息 |
| `run_api.ps1` | 启动本地 API/Web 服务 |
| `api_app.py` | FastAPI 应用、API 路由和 Web 页面路由 |
| `tests/test_api_app.py` | API 和 Web 安全测试 |
| `web/index.html` | 本地首页 |
| `web/search.html` | Search 页面 |
| `web/ask.html` | Ask 页面 |
| `web/diagnostics.html` | Diagnostics 页面 |
| `web/troubleshooting.html` | 故障排查页面 |

---

## M5 Vector Store 配置

M5 新增：

```text
rag_mvp/vector_store_config.py
```

应用程序现在通过统一的 Vector Store 配置层读取 Qdrant 配置。

配置优先级：

```text
环境变量
    ↓
config.py
    ↓
程序内置默认值
```

支持的环境变量：

| 环境变量 | 作用 |
|---|---|
| `PKB_KNOWLEDGE_ROOT` | 私人 Markdown 知识库根目录 |
| `PKB_OLLAMA_URL` | Ollama 服务地址 |
| `PKB_CHAT_MODEL` | 对话模型名称 |
| `PKB_EMBED_MODEL` | Embedding 模型名称 |
| `PKB_QDRANT_URL` | Qdrant 服务地址 |
| `PKB_QDRANT_TIMEOUT` | Qdrant 超时时间，单位为秒 |
| `PKB_QDRANT_COLLECTION` | Qdrant Collection 名称 |

本机 Qdrant 示例：

```powershell
$env:PKB_QDRANT_URL = "http://127.0.0.1:6333"
$env:PKB_QDRANT_COLLECTION = "personal_knowledge_base"
```

局域网或远程 Qdrant 示例：

```powershell
$env:PKB_QDRANT_URL = "http://<qdrant-host>:6333"
$env:PKB_QDRANT_COLLECTION = "personal_knowledge_base"
```

重要说明：

- `127.0.0.1` 始终表示当前运行程序的机器
- 虚拟机访问另一台 PC 或宿主机上的 Qdrant 时，必须使用可访问的宿主机 IP 或局域网 IP
- 配置的 Collection 名称必须与目标 Qdrant 中已经存在的 Collection 一致
- Web/API 服务仍默认绑定到 `127.0.0.1:8000`，不用于公网暴露

---

### PowerShell 脚本执行策略

如果 `run_api.ps1` 被 PowerShell 执行策略阻止：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\run_api.ps1
```

`-Scope Process` 只影响当前 PowerShell 进程，关闭窗口后恢复原有策略。

---

## M5 非破坏性验证

```powershell
python check_env.py
python status.py
python inspect_collection.py
python list_docs.py

python search_docs.py "M5 Vector Store"
python ask.py "请简单说明当前知识库是什么。"
```

`health_check_full.py` 属于完整写入链路测试，可能创建、写入、检索并删除临时 Qdrant Collection。只有在明确确认测试环境允许这些操作后再执行。

---

## 文档

推荐文档：

- `docs/quickstart.md`：双语快速开始
- `docs/environment_setup.md`：环境安装与配置
- `docs/command_reference.md`：命令参考
- `docs/restore_guide.md`：恢复指南
- `docs/rag_mvp_readme.md`：工程说明
- `docs/roadmap.md`：路线图
- `docs/local_console.md`：本地终端启动器说明
- `docs/local_web_api.md`：本地 Web/API 说明
- `docs/m5_release_notes.md`：M5 发布说明
- `docs/vector_store_configuration.md`：Vector Store 与 Qdrant 部署指南
- `docs/environment_variables.md`：临时和永久环境变量操作说明

---

## 路线图

已完成：

```text
M1：本地 RAG 知识库基础设施
M2：个人秘书分析层
M3：索引与检索优化层
M4：本地控制台、API 与 Web 界面
M5：Vector Store 配置层与跨 PC 部署验证
```

后续规划请参阅：

```text
docs/roadmap.md
```

---
