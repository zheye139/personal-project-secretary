---
title: Command Reference / 命令速查表
created: 2026-05-26
category: summary
project: personal-project-secretary
doc_type: command_reference
tags: [commands, PowerShell, RAG, Qdrant, Ollama, Python, M1, M2, M3, personal-secretary, retrieval]
---

# Command Reference / 命令速查表

This document lists common commands for the local knowledge base manager, M2 personal secretary layer, and M3 index/retrieval optimization layer.

本文档集中记录本地知识库管理员工具箱、M2 个人秘书层和 M3 索引检索优化层的常用命令。

---

## 1. Enter Project Directory / 进入代码目录

```powershell
cd <your-repo-path>\personal-project-secretary\rag_mvp
.\.venv\Scripts\activate
```

Note: this is the code repository path, not the private knowledge base path.

注意：这是代码仓库路径，不是私人知识库路径。

---

## 2. Daily Startup / 每次开始使用前

```powershell
cd <your-repo-path>\personal-project-secretary\rag_mvp
.\.venv\Scripts\activate
docker start pkb-qdrant
python status.py
```

Purpose / 作用：

1. Enter the script directory / 进入脚本目录。
2. Activate Python virtual environment / 激活 Python 虚拟环境。
3. Start Qdrant / 启动 Qdrant。
4. Check system status / 查看系统状态。

---

## 3. Ollama Commands / Ollama 命令

Check version / 查看版本：

```powershell
ollama --version
```

List models / 查看模型：

```powershell
ollama list
```

Install models / 安装模型：

```powershell
ollama pull qwen3:8b
ollama pull bge-m3
```

Run chat model / 运行主模型：

```powershell
ollama run qwen3:8b
```

Check Ollama API / 检查 Ollama API：

```powershell
curl.exe http://127.0.0.1:11434/api/tags
```

---

## 4. Qdrant and Docker / Qdrant 与 Docker

Start Qdrant / 启动 Qdrant：

```powershell
docker start pkb-qdrant
```

Restart Qdrant / 重启 Qdrant：

```powershell
docker restart pkb-qdrant
```

Check containers / 查看容器：

```powershell
docker ps
docker ps -a
```

Check Qdrant API / 检查 Qdrant API：

```powershell
curl.exe http://127.0.0.1:6333/
curl.exe http://127.0.0.1:6333/collections
```

Create Qdrant container / 创建 Qdrant 容器：

```powershell
docker run -d --name pkb-qdrant -p 6333:6333 -v <your-knowledge-root>/99_System/qdrant_storage:/qdrant/storage qdrant/qdrant
```

Use your own knowledge-base path if different.

如果你的知识库路径不同，请修改 volume 路径。

---

## 5. Python Environment / Python 环境

Create virtual environment / 创建虚拟环境：

```powershell
py -3.11 -m venv .venv
```

Activate virtual environment / 激活虚拟环境：

```powershell
.\.venv\Scripts\activate
```

Install dependencies / 安装依赖：

```powershell
pip install -r ..\requirements.txt
```

Check dependency conflicts / 检查依赖冲突：

```powershell
pip check
```

---

## 6. Environment and Index / 环境与索引

Check environment / 检查环境：

```powershell
python check_env.py
```

Index Markdown files / 入库 Markdown 文档：

```powershell
python ingest.py
```

Daily update / 日常更新索引：

```powershell
python update_index.py
```

List indexed documents / 查看已入库文档：

```powershell
python list_docs.py
```

Inspect Qdrant collection / 查看 Qdrant 集合样本：

```powershell
python inspect_collection.py
```

System status / 系统状态总览：

```powershell
python status.py
```

Full health check / 全链路健康检查：

```powershell
python health_check_full.py
```

---

## 7. RAG Q&A / RAG 问答

Basic question / 普通问答：

```powershell
python ask.py "What is the current project status?"
```

Project-filtered question / 按项目查询：

```powershell
python ask.py --project Demo_Project "What is the project status?"
```

Document type filter / 按文档类型查询：

```powershell
python ask.py --doc-type progress_log "What progress has been recorded?"
```

Category filter / 按资料大类查询：

```powershell
python ask.py --category problem "What issues were recorded?"
```

Tag filter / 按标签查询：

```powershell
python ask.py --tag demo "What demo records are available?"
```

---

## 8. Search Without Chat Model / 不调用模型的片段搜索

```powershell
python search_docs.py "project status" --show-text
```

With project filter / 按项目过滤：

```powershell
python search_docs.py --project Demo_Project "next steps" --show-text
```

With document type filter / 按文档类型过滤：

```powershell
python search_docs.py --doc-type next_steps "next task" --show-text
```

---

## 9. Add and Import Notes / 新增与导入记录

Add a progress note / 新增项目进度：

```powershell
python add_note.py --category project --project Demo_Project --doc-type progress_log --title "Progress title" --tags "demo,progress" --content "Progress content."
```

Add an issue / 新增问题记录：

```powershell
python add_note.py --category problem --project Demo_Project --title "Issue title" --tags "demo,issue" --content "Issue content."
```

Import Inbox Markdown files / 导入 Inbox 文件：

```powershell
python inbox_import.py
python inbox_import.py --execute
```

Update index after changes / 修改后重新入库：

```powershell
python update_index.py
```

---

## 10. M1 Reports / M1 报告能力

Project report / 项目状态报告：

```powershell
python project_report.py --project Demo_Project
```

Daily report / 日报：

```powershell
python time_report.py --project Demo_Project --mode daily
```

Weekly report / 周报：

```powershell
python time_report.py --project Demo_Project --mode weekly
```

Index generated reports / 报告生成后入库：

```powershell
python update_index.py
```

---

## 11. M2 Personal Secretary Commands / M2 个人秘书命令

Extract next actions / 提取下一步行动：

```powershell
python next_action.py --project Demo_Project
```

Generate project brief / 生成项目简报：

```powershell
python project_brief.py --project Demo_Project
```

Summarize multiple projects / 汇总多个项目状态：

```powershell
python multi_project_status.py
```

Generate priority advice / 生成优先级建议：

```powershell
python priority_advisor.py
```

Review project records / 复盘项目记录：

```powershell
python review_assistant.py --project Demo_Project
```

Generate personal secretary report / 生成个人秘书汇报：

```powershell
python secretary_report.py
```

Milestone closeout / 阶段封版检查：

```powershell
python milestone_closeout.py --milestone M2
```

If command options differ, check help / 如果参数不同，请查看帮助：

```powershell
python next_action.py --help
python project_brief.py --help
python multi_project_status.py --help
python priority_advisor.py --help
python review_assistant.py --help
python secretary_report.py --help
python milestone_closeout.py --help
```


---

## 12. M3 Index and Retrieval Optimization / M3 索引与检索优化

### 12.1 Incremental index / 增量索引

Daily update / 日常更新：

```powershell
python update_index.py
```

Dry run only / 只预览变化：

```powershell
python update_index.py --dry-run
```

Force all Markdown files to rebuild / 强制全部 Markdown 重新入库：

```powershell
python update_index.py --force-all
```

### 12.2 Single-file update / 单文件更新

```powershell
python update_index.py --file "01_Projects/Demo_Project/progress_log.md"
```

Force rebuild one file / 强制重建单个文件：

```powershell
python update_index.py --file "01_Projects/Demo_Project/progress_log.md" --force-file
```

### 12.3 Project-level update / 项目级更新

```powershell
python update_index.py --project Demo_Project
```

Force rebuild one project / 强制重建指定项目：

```powershell
python update_index.py --project Demo_Project --force-project
```

### 12.4 Full rebuild / 全量重建

Preview / 预览：

```powershell
python rebuild_index.py
```

Execute / 执行：

```powershell
python rebuild_index.py --execute
```

If Qdrant collection is damaged / 如果 Qdrant collection 已损坏：

```powershell
python rebuild_index.py --execute --skip-check --skip-snapshot
```

### 12.5 Search modes / 检索模式

Vector semantic search / 向量语义检索：

```powershell
python search_docs.py --mode vector "project status" --show-text
```

Keyword search / 关键词检索：

```powershell
python search_docs.py --mode keyword "update_index.py" --show-text
```

Hybrid search / 混合检索：

```powershell
python search_docs.py --mode hybrid "M3 incremental indexing" --show-text
```

Adjust hybrid weights / 调整混合检索权重：

```powershell
python search_docs.py --mode hybrid "update_index.py" --vector-weight 0.3 --keyword-weight 0.7 --show-text
```

### 12.6 Ask with retrieval modes / 使用不同检索模式问答

```powershell
python ask.py --search-mode vector "What is the current project status?"
python ask.py --search-mode keyword "What does update_index.py do?"
python ask.py --search-mode hybrid "What did M3 improve?"
```

With filters / 配合过滤条件：

```powershell
python ask.py --project Demo_Project --search-mode hybrid "What should I do next?"
python ask.py --doc-type progress_log --search-mode keyword "M3.7"
python ask.py --category problem --search-mode hybrid "OffsetOutOfBounds"
```

### 12.7 Retrieval evaluation / 检索评估

Run all modes / 评估全部模式：

```powershell
python retrieval_eval.py --mode all
```

Run one mode / 评估单一模式：

```powershell
python retrieval_eval.py --mode vector
python retrieval_eval.py --mode keyword
python retrieval_eval.py --mode hybrid
```

Custom TopK / 自定义 TopK：

```powershell
python retrieval_eval.py --mode all --top-k 1,3,5,10 --limit 10
```

Index generated evaluation reports / 将评估报告重新入库：

```powershell
python update_index.py --project Personal_Project_Assistant
```

### 12.8 M3 closeout / M3 阶段封版

```powershell
python milestone_closeout.py --milestone M3
```


---

## 13. Backup, Export, and Maintenance / 备份、导出与维护

Backup knowledge base / 备份知识库：

```powershell
python backup_kb.py
```

Export project package / 导出项目资料包：

```powershell
python export_project.py --project Demo_Project
```

Validate Markdown files / 检查 Markdown 规范：

```powershell
python validate_kb.py
```

Repair Frontmatter / 修复 Frontmatter：

```powershell
python repair_frontmatter.py
python repair_frontmatter.py --execute
```

Rebuild Qdrant index / 重建 Qdrant 索引：

```powershell
python rebuild_index.py
python rebuild_index.py --execute
```

Archive a project / 归档项目：

```powershell
python archive_project.py --project Demo_Project
python archive_project.py --project Demo_Project --execute
```

---

## 14. M4 Local Console, Discovery, API, and Web Commands / M4 本地控制台、发现、API 和 Web 命令

M4 adds a local console menu, command registry, discovery helpers, and a local FastAPI/Web interface. These features keep the local-first design: the API binds to `127.0.0.1` by default and is not intended for public network exposure.

M4 新增了本地控制台菜单、命令注册表、发现辅助工具，以及本地 FastAPI/Web 界面。这些功能保持本地优先设计：API 默认绑定到 `127.0.0.1`，并且不用于公网暴露。

### 14.1 Command registry / 命令注册表

```powershell
python command_registry.py
```

`command_registry.py` is the command registry. It describes available project commands and their metadata. It does not directly execute business workflows by itself.

`command_registry.py` 是命令注册表。它用于描述可用的项目命令及其元数据。它本身不会直接执行业务工作流。

### 14.2 Local terminal launcher / 本地终端启动器

```powershell
python launcher.py
```

`launcher.py` is the local terminal menu entry point. It helps run existing scripts from a guided menu, including status checks, ask, search, reports, backup, advanced maintenance, and starting the local API server.

`launcher.py` 是本地终端菜单入口。它可以通过引导式菜单帮助运行已有脚本，包括状态检查、ask、search、报告、备份、高级维护，以及启动本地 API 服务器。

### 14.3 Project discovery / 项目发现

```powershell
python project_discovery.py --summary
python project_discovery.py --projects
python project_discovery.py --categories
python project_discovery.py --doc-types
python project_discovery.py --tags
```

`project_discovery.py` reads the local manifest and discovers projects, categories, doc types, tags, files, and summary metadata. It is used by the local API and Web pages for filter lists and overview data.

`project_discovery.py` 会读取本地 manifest，并发现项目、分类、文档类型、标签、文件和摘要元数据。它会被本地 API 和 Web 页面用于筛选列表和概览数据。

### 14.4 Start local API and Web service / 启动本地 API 和 Web 服务

```powershell
.\run_api.ps1
```

`run_api.ps1` starts the local FastAPI/Web service on `127.0.0.1:8000` by default. It does not start as a background service and can be stopped with `Ctrl+C`.

`run_api.ps1` 默认会在 `127.0.0.1:8000` 上启动本地 FastAPI/Web 服务。它不会作为后台服务启动，可以通过 `Ctrl+C` 停止。

Equivalent command / 等效命令:

```powershell
.\.venv\Scripts\python.exe -m uvicorn api_app:app --host 127.0.0.1 --port 8000 --no-use-colors
```

### 14.5 Local FastAPI app / 本地 FastAPI 应用

```powershell
python -m uvicorn api_app:app --host 127.0.0.1 --port 8000 --no-use-colors
```

`api_app.py` provides the local API and Web page routes, including homepage, Search, Ask, Diagnostics, Troubleshooting, API overview, and FastAPI docs. The Web/API layer does not execute `update_index`, `rebuild`, `backup`, or `add_note` from the browser.

`api_app.py` 提供本地 API 和 Web 页面路由，包括首页、Search、Ask、Diagnostics、Troubleshooting、API overview，以及 FastAPI docs。Web/API 层不会从浏览器执行 `update_index`、`rebuild`、`backup` 或 `add_note`。