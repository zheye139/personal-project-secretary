---
title: Environment Setup / 环境安装说明
created: 2026-05-26
category: summary
project: personal-project-secretary
doc_type: environment_setup
tags: [environment, Python, Ollama, Qdrant, Docker, RAG, M1, M2, M3, retrieval]
---

# Environment Setup / 环境安装说明

This document explains how to install, configure, validate, and restore the local environment for the project.

本文档说明如何安装、配置、验证和恢复本项目的本地运行环境。

---

## 1. Recommended Software / 推荐基础软件

- Windows 10 / Windows 11
- Python 3.11
- Docker Desktop
- Ollama
- Git
- PowerShell
- VS Code, optional / 可选

Check Python / 检查 Python：

```powershell
py --version
python --version
```

Python 3.11 is recommended.

推荐使用 Python 3.11。

---

## 2. Install Ollama Models / 安装 Ollama 模型

```powershell
ollama pull qwen3:8b
ollama pull bge-m3
```

Check installed models / 查看已安装模型：

```powershell
ollama list
```

Check Ollama API / 检查 Ollama API：

```powershell
curl.exe http://127.0.0.1:11434/api/tags
```

If `ollama list` shows `bge-m3:latest`, set `EMBED_MODEL` in `config.py` to:

如果 `ollama list` 显示 `bge-m3:latest`，则 `config.py` 中应配置为：

```python
EMBED_MODEL = "bge-m3:latest"
```

---

## 3. Start Qdrant / 启动 Qdrant

Create container / 创建容器：

```powershell
docker run -d --name pkb-qdrant -p 6333:6333 -v <your-knowledge-root>/99_System/qdrant_storage:/qdrant/storage qdrant/qdrant
```

Start existing container / 启动已有容器：

```powershell
docker start pkb-qdrant
```

Check Qdrant / 检查 Qdrant：

```powershell
curl.exe http://127.0.0.1:6333/
curl.exe http://127.0.0.1:6333/collections
```

---

## 4. Create Python Environment / 创建 Python 环境

```powershell
cd <your-repo-path>\personal-project-secretary\rag_mvp
py -3.11 -m venv .venv
.\.venv\Scripts\activate
pip install -r ..\requirements.txt
```

Check dependencies / 检查依赖：

```powershell
pip check
```

---

## 5. Create Local Config / 创建本地配置

```powershell
Copy-Item .\config.example.py .\config.py
```

Edit `config.py` / 编辑 `config.py`：

```python
KNOWLEDGE_ROOT = Path(r"<your-knowledge-root>")
OLLAMA_URL = "http://127.0.0.1:11434"
CHAT_MODEL = "qwen3:8b"
EMBED_MODEL = "bge-m3:latest"
QDRANT_URL = "http://127.0.0.1:6333"
COLLECTION_NAME = "personal_knowledge_base"
```

Important / 注意：

- `KNOWLEDGE_ROOT` points to the private Markdown knowledge base.
- It should not point to the GitHub repository.
- `COLLECTION_NAME` is recommended to use `personal_knowledge_base`.

---

## 6. M1 Output Directories / M1 输出目录

These paths are usually derived from `KNOWLEDGE_ROOT` in `config.py`.

这些路径通常由 `config.py` 中的 `KNOWLEDGE_ROOT` 推导得到。

```python
QA_LOG_DIR = KNOWLEDGE_ROOT / "05_Summaries" / "qa_logs"
QA_LOG_ARCHIVE_DIR = KNOWLEDGE_ROOT / "05_Summaries" / "qa_logs_archived"
PROJECT_REPORT_DIR = KNOWLEDGE_ROOT / "05_Summaries" / "project_reports"
TIME_REPORT_DIR = KNOWLEDGE_ROOT / "05_Summaries" / "time_reports"
BACKUP_DIR = KNOWLEDGE_ROOT / "99_System" / "backups"
```

---

## 7. M2 Output Directories / M2 输出目录

M2 scripts may use these output directories:

M2 脚本可能使用以下输出目录：

```python
NEXT_ACTION_DIR = KNOWLEDGE_ROOT / "05_Summaries" / "next_actions"
PROJECT_BRIEF_DIR = KNOWLEDGE_ROOT / "05_Summaries" / "project_briefs"
MULTI_PROJECT_STATUS_DIR = KNOWLEDGE_ROOT / "05_Summaries" / "multi_project_status"
PRIORITY_ADVICE_DIR = KNOWLEDGE_ROOT / "05_Summaries" / "priority_advice"
REVIEW_REPORT_DIR = KNOWLEDGE_ROOT / "05_Summaries" / "review_reports"
SECRETARY_REPORT_DIR = KNOWLEDGE_ROOT / "05_Summaries" / "secretary_reports"
MILESTONE_REPORT_DIR = KNOWLEDGE_ROOT / "05_Summaries" / "milestone_reports"
```

If your local script uses different directory variable names, keep them consistent with `config.py`.

如果你的本地脚本使用不同变量名，请以 `config.py` 为准并保持一致。

---

## 8. Validate Environment / 验证环境

```powershell
python check_env.py
python status.py
```

Then index documents / 然后执行入库：

```powershell
python update_index.py
```

---

## 9. Validate M2 Scripts / 验证 M2 脚本

Syntax check / 语法检查：

```powershell
python -m py_compile next_action.py project_brief.py multi_project_status.py priority_advisor.py review_assistant.py secretary_report.py milestone_closeout.py
```

Help check / 查看帮助：

```powershell
python next_action.py --help
python project_brief.py --help
python multi_project_status.py --help
python priority_advisor.py --help
python review_assistant.py --help
python secretary_report.py --help
python milestone_closeout.py --help
```

Run M2 demo commands / 运行 M2 示例命令：

```powershell
python next_action.py --project Demo_Project
python project_brief.py --project Demo_Project
python multi_project_status.py
python priority_advisor.py
python review_assistant.py --project Demo_Project
python secretary_report.py
python milestone_closeout.py --milestone M2
```

After report generation / 生成报告后：

```powershell
python update_index.py
```


---

## 10. M3 Configuration and Validation / M3 配置与验证

M3 adds incremental indexing, search modes, and retrieval evaluation.

M3 增加增量索引、检索模式和检索评估能力。

Add these paths to `config.py` if they are not already present / 如果本地 `config.py` 尚未包含，请增加：

```python
INDEX_MANIFEST_PATH = KNOWLEDGE_ROOT / "99_System" / "index_manifest.json"

EVAL_DIR = KNOWLEDGE_ROOT / "99_System" / "eval"
RETRIEVAL_EVAL_PATH = EVAL_DIR / "retrieval_eval.json"

RETRIEVAL_EVAL_REPORT_DIR = KNOWLEDGE_ROOT / "05_Summaries" / "retrieval_eval_reports"
```

Create eval directory / 创建评估目录：

```powershell
New-Item -ItemType Directory -Force "<your-knowledge-root>\99_System\eval"
```

Validate M3 scripts / 验证 M3 脚本：

```powershell
python -m py_compile manifest_utils.py incremental_index.py update_index.py rebuild_index.py search_docs.py ask.py retrieval_eval.py milestone_closeout.py
python -m tabnanny manifest_utils.py incremental_index.py update_index.py rebuild_index.py search_docs.py ask.py retrieval_eval.py milestone_closeout.py
```

Initialize and scan manifest / 初始化和扫描 manifest：

```powershell
python manifest_utils.py --init
python manifest_utils.py --scan
```

Run incremental indexing / 执行增量索引：

```powershell
python update_index.py --dry-run
python update_index.py
```

Run M3 retrieval checks / 执行 M3 检索检查：

```powershell
python search_docs.py --mode keyword "update_index.py" --show-text
python search_docs.py --mode hybrid "M3 incremental indexing" --show-text
python ask.py --search-mode hybrid "What did M3 improve?"
```

Run retrieval evaluation / 执行检索评估：

```powershell
python retrieval_eval.py --mode all
python update_index.py --project Personal_Project_Assistant
```

Run M3 closeout / 执行 M3 阶段封版：

```powershell
python milestone_closeout.py --milestone M3
```

### Qdrant shard error recovery / Qdrant shard 错误恢复

If Qdrant reports `OffsetOutOfBounds` or cannot load a local shard, treat Qdrant as a rebuildable index.

如果 Qdrant 报 `OffsetOutOfBounds` 或无法加载 local shard，应将 Qdrant 视为可重建索引处理。

Recommended recovery / 推荐恢复方式：

```powershell
python rebuild_index.py --execute --skip-check --skip-snapshot
```

If collection deletion also fails, rebuild the storage directory after backing it up.

如果 collection 删除也失败，请先备份并重建 storage 目录。


---

## 11. Common Problems / 常见问题

### Ollama cannot connect / Ollama 无法连接

```powershell
ollama list
curl.exe http://127.0.0.1:11434/api/tags
```

### Qdrant cannot connect / Qdrant 无法连接

```powershell
docker ps -a
docker start pkb-qdrant
curl.exe http://127.0.0.1:6333/collections
```

### Document not found / 文档检索不到

```powershell
python list_docs.py
python search_docs.py "keyword" --show-text
python update_index.py
```

### Wrong working directory / 当前目录错误

If you are inside `rag_mvp`, run:

如果你已经在 `rag_mvp` 目录内，执行：

```powershell
python add_note.py --help
```

If you are at repository root, run:

如果你在仓库根目录，执行：

```powershell
python rag_mvp\add_note.py --help
```

---

## 12. M4 Local API and Web Environment / M4 本地 API 和 Web 环境

M4 adds a local FastAPI API and browser Web interface.

M4 新增了一个本地 FastAPI API 和浏览器 Web 界面。

Additional Python dependencies / 额外的 Python 依赖:

- FastAPI
- Uvicorn
- HTTPX

Install dependencies from the project requirements file / 从项目的 requirements 文件安装依赖:

```powershell
cd rag_mvp
.\.venv\Scripts\activate
pip install -r requirements.txt
```

Start the local API/Web service / 启动本地 API/Web 服务:

```powershell
cd rag_mvp
.\run_api.ps1
```

Equivalent command / 等效命令:

```powershell
.\.venv\Scripts\python.exe -m uvicorn api_app:app --host 127.0.0.1 --port 8000 --no-use-colors
```

Open the browser at / 在浏览器中打开:

```text
http://127.0.0.1:8000/
http://127.0.0.1:8000/docs
```

Security notes / 安全说明:

- The local API binds to `127.0.0.1` by default.
- The Web/API service is not intended for public-network exposure.
- The Web pages do not load external CDN assets.
- Search and Ask still depend on the local Qdrant index and local Ollama services.

## M5 Vector Store Configuration / M5 Vector Store 配置

M5 adds a shared Vector Store configuration layer.

Configuration priority:

```text
environment variables
    ↓
config.py
    ↓
built-in defaults
```

Supported environment variables:

```text
PKB_KNOWLEDGE_ROOT
PKB_OLLAMA_URL
PKB_CHAT_MODEL
PKB_EMBED_MODEL
PKB_QDRANT_URL
PKB_QDRANT_TIMEOUT
PKB_QDRANT_COLLECTION
```

---

## Local Qdrant / 本机 Qdrant

```powershell
$env:PKB_QDRANT_URL = "http://127.0.0.1:6333"
$env:PKB_QDRANT_COLLECTION = "personal_knowledge_base"
```

---

## Remote Qdrant / 远程 Qdrant

```powershell
$env:PKB_QDRANT_URL = "http://<qdrant-host>:6333"
$env:PKB_QDRANT_COLLECTION = "personal_knowledge_base"
```

Network checks:

```powershell
ping <qdrant-host>
Test-NetConnection <qdrant-host> -Port 6333
curl.exe http://<qdrant-host>:6333/
```

---

## VMware NAT / VMware NAT 模式

Recommended M5 VM setup:

```text
VMware Network Adapter:
NAT
```

On the host:

```powershell
ipconfig
```

Find:

```text
VMware Network Adapter VMnet8
IPv4: <host-ip>
```

In the VM:

```powershell
Test-NetConnection <host-ip> -Port 6333
curl.exe http://<host-ip>:6333/
```

Then:

```powershell
$env:PKB_QDRANT_URL = "http://<host-ip>:6333"
```

---

## Docker Port Mapping / Docker 端口映射

```powershell
docker ps
```

Cross-PC access normally requires a reachable mapping such as:

```text
0.0.0.0:6333->6333/tcp
```

---

## Firewall / 防火墙

If TCP 6333 fails:

- check Qdrant service
- check Docker mapping
- check Windows Firewall
- check VMware network mode
- check the active Windows network profile

Do not expose Qdrant directly to the public Internet without a dedicated security design.

---

## Python Dependencies on a New PC / 新 PC Python 依赖

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -r ..\requirements.txt
```

Package name:

```text
qdrant-client
```

Import name:

```text
qdrant_client
```

Each PC and each virtual environment must install dependencies independently.

---

## PowerShell Script Policy / PowerShell 脚本策略

If `run_api.ps1` is blocked:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\run_api.ps1
```

This setting only applies to the current PowerShell process.

---

## Non-destructive Validation / 非破坏性验证

```powershell
python check_env.py
python status.py
python inspect_collection.py
python list_docs.py
python search_docs.py "M5 Vector Store"
python ask.py "请简单说明当前知识库是什么"
```

`health_check_full.py` is a write-path test and may create/delete a temporary collection.
