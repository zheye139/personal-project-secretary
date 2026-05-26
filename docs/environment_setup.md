---
title: Environment Setup / 环境安装说明
created: 2026-05-26
category: summary
project: personal-project-secretary
doc_type: environment_setup
tags: [environment, Python, Ollama, Qdrant, Docker, RAG, M1, M2]
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
docker run -d --name pkb-qdrant -p 6333:6333 -v D:/Personal_Knowledge_Base/99_System/qdrant_storage:/qdrant/storage qdrant/qdrant
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
KNOWLEDGE_ROOT = Path(r"D:\Personal_Knowledge_Base")
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
MILESTONE_CLOSEOUT_DIR = KNOWLEDGE_ROOT / "05_Summaries" / "milestone_closeouts"
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

## 10. Common Problems / 常见问题

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
