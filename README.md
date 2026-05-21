# Personal Project Secretary + Knowledge Base Manager

English | [中文说明](#中文说明)

A local-first personal project secretary and knowledge base manager built with **Markdown**, **Ollama**, **Qdrant**, and **Python**.

This project is a local RAG-based workflow for people who want to record, organize, retrieve, summarize, and report long-running project information. It is **not** a model training project. Your Markdown files remain the primary data source, and the vector database can be rebuilt at any time.

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

The system is designed around two roles:

### Knowledge Base Manager

Responsible for:

- organizing Markdown documents
- maintaining Frontmatter metadata
- importing inbox notes
- indexing Markdown files into Qdrant
- validating knowledge-base structure
- backing up and restoring the knowledge base

### Personal Project Secretary

Responsible for:

- answering project questions
- retrieving project knowledge
- generating project reports
- generating daily and weekly reports
- summarizing progress
- helping plan next actions

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

## Current Status

Current release target:

```text
v0.1.0-local-rag-mvp
```

This version is a local command-line MVP. It focuses on the local knowledge-base workflow, not on a Web UI or cloud service.

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

Recommended knowledge-base structure:

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

---

## Example Knowledge Base

A minimal example knowledge base is available in:

```text
examples/Personal_Knowledge_Base_Template
```

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

## Main Scripts

| Script | Purpose |
|---|---|
| `check_env.py` | Check Ollama, models, Qdrant, and collection status |
| `ingest.py` | Parse Markdown files and index them into Qdrant |
| `ask.py` | Run RAG question answering |
| `search_docs.py` | Search retrieved chunks without calling the chat model |
| `add_note.py` | Add a Markdown note with Frontmatter |
| `inbox_import.py` | Import Markdown files from `00_Inbox` |
| `project_report.py` | Generate a project status report |
| `time_report.py` | Generate daily or weekly reports |
| `backup_kb.py` | Create a knowledge-base backup |
| `status.py` | Show system status |
| `update_index.py` | Run environment check, indexing, and document listing |

---

## Documentation

- `docs/quickstart.md` - bilingual quick start
- `docs/environment_setup.md` - environment setup
- `docs/command_reference.md` - command reference
- `docs/restore_guide.md` - recovery guide
- `docs/rag_mvp_readme.md` - engineering notes
- `docs/roadmap.md` - roadmap

---

## Roadmap

Short term:

- complete the local command-line toolbox
- improve documentation and examples
- make script outputs more friendly for public users

---

## License

MIT License

---

# 中文说明

这是一个本地优先的“个人项目秘书 + 知识库管理员”系统，使用 **Markdown** 作为主数据源，**Qdrant** 作为可重建向量索引，**Ollama** 本地模型用于问答、总结和项目报告生成。

本项目不是模型训练项目，而是一个面向个人长期项目管理的本地 RAG 知识工作流。

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
- 备份与恢复知识库

### 个人项目秘书

负责：

- 回答项目问题
- 调取项目知识
- 生成项目状态报告
- 生成日报和周报
- 总结项目进度
- 辅助规划下一步行动

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
python update_index.py
python ask.py "当前项目进行到哪里了？"
```

## 当前阶段

当前版本是 `v0.1.0-local-rag-mvp`，属于本地命令行 MVP。
