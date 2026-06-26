---
title: rag_mvp Engineering Notes / rag_mvp 工程说明
created: 2026-05-26
category: summary
project: personal-project-secretary
doc_type: rag_mvp_readme
tags: [RAG, engineering, M1, M2, M3, personal-secretary, indexing, retrieval, Ollama, Qdrant]
---

# rag_mvp Engineering Notes / rag_mvp 工程说明

`rag_mvp` is the command-line engine of **Personal Project Secretary + Knowledge Base Manager**.

`rag_mvp` 是“个人项目秘书 + 知识库管理员系统”的命令行核心工程。

---

## 1. System Positioning / 系统定位

M1 provides the local knowledge base manager toolbox.

M1 提供本地知识库管理员工具箱。

```text
Markdown records → embedding → Qdrant index → retrieval → qwen3:8b answer/report
```

M2 adds the personal secretary analysis layer.

M2 增加个人项目秘书分析层。

```text
next actions → project brief → multi-project status → priority advice → review → secretary report
```

M3 adds the index and retrieval optimization layer.

M3 增加索引与检索能力优化层。

```text
index manifest → incremental index → single-file/project update → keyword search → hybrid search → retrieval evaluation
```

The project is not a model training project. It is a local knowledge workflow.

本项目不是模型训练项目，而是本地知识工作流。

M4 adds the local console, API, and Web interface layer.

```text
command registry -> launcher -> project discovery -> local FastAPI API -> local Web pages
```

Current positioning:

```text
Local-first personal project secretary and knowledge base assistant.
```

The project remains a local tool. It is not a public network service and is not designed for cloud deployment by default.

---

## 2. Core Principles / 核心原则

1. Markdown is the primary data source.
2. Qdrant is a rebuildable vector index.
3. Ollama provides local model services.
4. Python scripts are the automation layer.
5. `config.py` is the configuration center.
6. Generated outputs should be saved as Markdown and re-indexed.

中文：

1. Markdown 是主数据源。
2. Qdrant 是可重建向量索引。
3. Ollama 提供本地模型服务。
4. Python 脚本是自动化工具层。
5. `config.py` 是统一配置中心。
6. 自动生成的报告应保存为 Markdown 并重新入库。

---

## 3. M1 Scripts / M1 脚本

| Script | Purpose |
|---|---|
| `check_env.py` | Check local environment |
| `ingest.py` | Index Markdown files |
| `ask.py` | RAG question answering |
| `search_docs.py` | Search chunks without chat model |
| `list_docs.py` | List indexed documents |
| `inspect_collection.py` | Inspect Qdrant collection |
| `update_index.py` | Check environment, index documents, list documents |
| `status.py` | Show system status |
| `add_note.py` | Add Markdown notes |
| `inbox_import.py` | Import Inbox Markdown files |
| `project_report.py` | Generate project report |
| `time_report.py` | Generate daily/weekly reports |
| `backup_kb.py` | Backup knowledge base |
| `rebuild_index.py` | Rebuild Qdrant index |
| `validate_kb.py` | Validate Markdown metadata |
| `repair_frontmatter.py` | Repair missing Frontmatter |
| `export_project.py` | Export project package |
| `health_check_full.py` | Full-chain health check |

---

## 4. M2 Scripts / M2 脚本

| Script | Purpose | Typical output doc_type |
|---|---|---|
| `next_action.py` | Extract next actions | `next_action_report` |
| `project_brief.py` | Generate a project brief | `project_brief` |
| `multi_project_status.py` | Summarize multiple projects | `multi_project_status` |
| `priority_advisor.py` | Suggest priorities | `priority_advice` |
| `review_assistant.py` | Review project records | `review_report` |
| `secretary_report.py` | Generate personal secretary report | `secretary_report` |
| `milestone_closeout.py` | Run milestone closeout checks | `milestone_closeout` |

---

## 5. Recommended M2 Workflow / 推荐 M2 工作流

```powershell
python update_index.py
python next_action.py --project Demo_Project
python project_brief.py --project Demo_Project
python multi_project_status.py
python priority_advisor.py
python review_assistant.py --project Demo_Project
python secretary_report.py
python milestone_closeout.py --milestone M2
python update_index.py
python backup_kb.py
```


---

## 6. M3 Scripts / M3 脚本

| Script / File | Purpose | Typical output |
|---|---|---|
| `manifest_utils.py` | Manage `index_manifest.json` and detect file changes | Runtime state file |
| `incremental_index.py` | Core incremental indexing engine | Qdrant points + manifest updates |
| `update_index.py` | Daily incremental update entry | Updated Qdrant collection |
| `rebuild_index.py` | Full index rebuild entry | Rebuilt Qdrant collection |
| `search_docs.py` | Search in vector, keyword, or hybrid mode | Terminal results |
| `ask.py` | RAG Q&A with configurable retrieval mode | `qa_log` |
| `retrieval_eval.py` | Evaluate retrieval quality | `retrieval_eval_report` |
| `retrieval_eval.json` | Evaluation test cases | JSON test set |

---

## 7. Recommended M3 Workflow / 推荐 M3 工作流

Daily update / 日常更新：

```powershell
python update_index.py
```

Single-file update / 单文件更新：

```powershell
python update_index.py --file "01_Projects/Demo_Project/progress_log.md"
```

Project-level update / 项目级更新：

```powershell
python update_index.py --project Demo_Project
```

Search / 检索：

```powershell
python search_docs.py --mode vector "project status" --show-text
python search_docs.py --mode keyword "update_index.py" --show-text
python search_docs.py --mode hybrid "incremental indexing" --show-text
```

Question answering / 问答：

```powershell
python ask.py --search-mode hybrid "What did M3 improve?"
```

Evaluation / 评估：

```powershell
python retrieval_eval.py --mode all
```

Closeout / 阶段封版：

```powershell
python milestone_closeout.py --milestone M3
```

---

## 8. M3 Design Notes / M3 设计说明

M3 keeps Markdown as the source of truth and treats Qdrant as a rebuildable index.

M3 继续坚持 Markdown 是主数据源，Qdrant 是可重建索引。

`index_manifest.json` is a local runtime file. It should not be committed to GitHub because it may contain local file state and Qdrant point ids.

`index_manifest.json` 是本地运行状态文件，不建议提交到 GitHub，因为其中可能包含本地文件状态和 Qdrant point ids。

Use `update_index.py` for daily work and `rebuild_index.py --execute` when the collection must be rebuilt.

---

## 9. M4 Local Console, API, and Web Interface / M4 本地控制台、API 和 Web 界面

M4 adds a local interaction layer for the existing M1-M3 capabilities.

M4 为已有的 M1-M3 能力新增了一个本地交互层。

| Component                  | Purpose                                                                                               |
| -------------------------- | ----------------------------------------------------------------------------------------------------- |
| `command_registry.py`      | Registry of available commands and metadata / 可用命令及其元数据的注册表                                           |
| `launcher.py`              | Local terminal menu / 本地终端菜单                                                                          |
| `project_discovery.py`     | Discovery of projects, categories, doc types, tags, files, and summary data / 发现项目、分类、文档类型、标签、文件和摘要数据 |
| `api_app.py`               | Local FastAPI API and HTML route server / 本地 FastAPI API 和 HTML 路由服务器                                 |
| `run_api.ps1`              | PowerShell startup script for the local API/Web server / 本地 API/Web 服务器的 PowerShell 启动脚本              |
| `web/index.html`           | Local homepage / 本地首页                                                                                 |
| `web/search.html`          | Search page / Search页面                                                                                |
| `web/ask.html`             | Ask page / Ask页面                                                                                      |
| `web/diagnostics.html`     | Local diagnostics page / 本地诊断页面                                                                       |
| `web/troubleshooting.html` | Local troubleshooting guide / 本地故障排查指南                                                                |

M4 Web/API capabilities / M4 Web/API 能力:

- Local Web homepage. / 本地 Web 首页。
- Search API and Search page. / Search API 和 Search 页面。
- Ask API and Ask page. / Ask API 和 Ask 页面。
- Diagnostics page for API, Qdrant, Ollama, Discovery, and Commands. / 用于 API、Qdrant、Ollama、Discovery 和 Commands 的 Diagnostics 页面。
- Troubleshooting page for local service checks. / 用于本地服务检查的 Troubleshooting 页面。
- FastAPI automatic docs at `/docs`. / FastAPI 自动文档位于 `/docs`。
- API overview at `/api`. / API 概览位于 `/api`。

Safety boundary / 安全边界:

- The local API binds to `127.0.0.1` by default. / 本地 API 默认绑定到 `127.0.0.1`。
- The Web/API layer is not intended for public-network exposure. / Web/API 层不用于公网暴露。
- Web pages do not execute `update_index`, `rebuild`, `backup`, or `add_note`. / Web 页面不会执行 `update_index`、`rebuild`、`backup` 或 `add_note`。
- Search does not write to the knowledge base. / Search 不会写入知识库。
- Ask does not save QA logs by default. / Ask 默认不会保存 QA 日志。

日常使用 `update_index.py`，需要彻底重建索引时使用 `rebuild_index.py --execute`。
