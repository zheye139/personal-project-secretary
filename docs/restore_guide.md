---
title: Restore Guide / 恢复流程
created: 2026-05-26
category: summary
project: personal-project-secretary
doc_type: restore_guide
tags: [restore, migration, backup, RAG, Qdrant, Ollama, M1, M2]
---

# Restore Guide / 恢复流程

This guide explains how to restore the system on a new machine or after reinstalling the operating system.

本文档说明如何在新电脑或重装系统后恢复本项目。

---

## 1. Restore Scope / 恢复范围

You need to restore or recreate:

需要恢复或重新创建：

1. Code repository / 代码仓库
2. Private Markdown knowledge base / 私人 Markdown 知识库
3. Ollama models / Ollama 模型
4. Qdrant Docker container / Qdrant Docker 容器
5. Python virtual environment / Python 虚拟环境
6. Qdrant vector index / Qdrant 向量索引
7. M1 and M2 output directories / M1 与 M2 输出目录

---

## 2. Clone Repository / 克隆代码仓库

```powershell
git clone https://github.com/zheye139/personal-project-secretary.git
cd personal-project-secretary\rag_mvp
```

Or use your own fork/repository path.

也可以使用你自己的 fork 或本地仓库路径。

---

## 3. Restore Knowledge Base Files / 恢复知识库文件

Restore your private knowledge base to a local directory, for example:

将私人知识库恢复到本地目录，例如：

```text
D:\Personal_Knowledge_Base
```

Recommended structure / 推荐结构：

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
```

---

## 4. Install Ollama Models / 安装 Ollama 模型

```powershell
ollama pull qwen3:8b
ollama pull bge-m3
ollama list
```

---

## 5. Restore Qdrant / 恢复 Qdrant

Create or start Qdrant container:

创建或启动 Qdrant 容器：

```powershell
docker run -d --name pkb-qdrant -p 6333:6333 -v D:/Personal_Knowledge_Base/99_System/qdrant_storage:/qdrant/storage qdrant/qdrant
```

If it already exists / 如果已存在：

```powershell
docker start pkb-qdrant
```

Check / 检查：

```powershell
curl.exe http://127.0.0.1:6333/collections
```

---

## 6. Restore Python Environment / 恢复 Python 环境

```powershell
cd <your-repo-path>\personal-project-secretary\rag_mvp
py -3.11 -m venv .venv
.\.venv\Scripts\activate
pip install -r ..\requirements.txt
```

---

## 7. Restore Config / 恢复配置

```powershell
Copy-Item .\config.example.py .\config.py
```

Edit `config.py` / 编辑 `config.py`：

```python
KNOWLEDGE_ROOT = Path(r"D:\Personal_Knowledge_Base")
COLLECTION_NAME = "personal_knowledge_base"
```

---

## 8. Rebuild Index / 重建索引

Markdown is the primary data source, so Qdrant can be rebuilt.

Markdown 是主数据源，因此 Qdrant 可以从 Markdown 重新生成。

```powershell
python check_env.py
python update_index.py
python list_docs.py
```

If you need a full rebuild / 如需完全重建：

```powershell
python rebuild_index.py --execute
```

---

## 9. Validate M1 Functions / 验证 M1 能力

```powershell
python status.py
python search_docs.py "project status" --show-text
python ask.py --project Demo_Project "What is the project status?"
python project_report.py --project Demo_Project
python time_report.py --project Demo_Project --mode weekly
```

---

## 10. Validate M2 Functions / 验证 M2 能力

```powershell
python next_action.py --project Demo_Project
python project_brief.py --project Demo_Project
python multi_project_status.py
python priority_advisor.py
python review_assistant.py --project Demo_Project
python secretary_report.py
python milestone_closeout.py --milestone M2
```

Then / 然后：

```powershell
python update_index.py
```

---

## 11. Backup After Restore / 恢复后备份

```powershell
python backup_kb.py
```

---

## 12. Notes / 注意事项

- Do not restore `.venv`; recreate it.
- Do not treat Qdrant as the only source of truth.
- Keep Markdown files as the primary source.
- Keep private knowledge base outside the GitHub repository.
- Do not commit `config.py`, Qdrant data, backups, or private reports.

- 不建议恢复旧 `.venv`，应重新创建。
- 不要把 Qdrant 当作唯一数据源。
- Markdown 文件是主数据源。
- 私人知识库应放在 GitHub 仓库之外。
- 不要提交 `config.py`、Qdrant 数据、备份包或私人报告。
