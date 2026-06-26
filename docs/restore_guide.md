---
title: Restore Guide / 恢复流程
created: 2026-05-26
category: summary
project: personal-project-secretary
doc_type: restore_guide
tags: [restore, migration, backup, RAG, Qdrant, Ollama, M1, M2, M3, retrieval]
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
<your-knowledge-root>
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
docker run -d --name pkb-qdrant -p 6333:6333 -v <your-knowledge-root>/99_System/qdrant_storage:/qdrant/storage qdrant/qdrant
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
KNOWLEDGE_ROOT = Path(r"<your-knowledge-root>")
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

## 11. Restore M3 Index and Retrieval Features / 恢复 M3 索引与检索能力

After restoring Markdown files and Python dependencies, rebuild the Qdrant index from Markdown.

恢复 Markdown 文件和 Python 依赖后，应从 Markdown 重新构建 Qdrant 索引。

Recommended sequence / 推荐流程：

```powershell
python manifest_utils.py --init --overwrite
python update_index.py --force-all --skip-check
python list_docs.py
python health_check_full.py
```

Validate search modes / 验证检索模式：

```powershell
python search_docs.py --mode vector "project status" --show-text
python search_docs.py --mode keyword "update_index.py" --show-text
python search_docs.py --mode hybrid "M3 incremental indexing" --show-text
```

Validate ask retrieval modes / 验证问答检索模式：

```powershell
python ask.py --search-mode vector "What is the project status?"
python ask.py --search-mode keyword "What does update_index.py do?"
python ask.py --search-mode hybrid "What did M3 improve?"
```

Validate retrieval evaluation / 验证检索评估：

```powershell
python retrieval_eval.py --mode all
python update_index.py --project Personal_Project_Assistant
```

If Qdrant shard loading fails, for example `OffsetOutOfBounds`, Qdrant storage may be damaged. Back up the storage directory and rebuild the index from Markdown.

如果 Qdrant shard 加载失败，例如出现 `OffsetOutOfBounds`，可能是 Qdrant 本地 storage 损坏。请先备份 storage 目录，再从 Markdown 重建索引。

Recovery command / 恢复命令：

```powershell
python rebuild_index.py --execute --skip-check --skip-snapshot
```


---

## 12. Backup After Restore / 恢复后备份

```powershell
python backup_kb.py
```

---

## 13. Notes / 注意事项

- Do not restore `.venv`; recreate it.
- Do not treat Qdrant as the only source of truth.
- Keep Markdown files as the primary source.
- Keep private knowledge base outside the GitHub repository.
- Do not commit `config.py`, Qdrant data, backups, or private reports.

---

## 14. M4 API/Web Restore Notes

After restoring code from GitHub:

- Copy `config.example.py` to local `config.py`.
- Reinstall Python dependencies from `requirements.txt`.
- Reconnect local Qdrant and local Ollama.
- Rebuild or refresh the Qdrant index from the private Markdown knowledge base.
- Start the local Web/API service with `.\run_api.ps1` from the `rag_mvp` directory.

GitHub restores code capability only. It does not restore:

- real private knowledge-base Markdown content
- Qdrant storage data
- backup data
- local `.env` files
- local `config.py`
- local runtime manifests

The Web/API layer restores the local interface, Search API, Ask API, Diagnostics page, and Troubleshooting page. It does not restore personal knowledge-base content by itself.

- 不建议恢复旧 `.venv`，应重新创建。
- 不要把 Qdrant 当作唯一数据源。
- Markdown 文件是主数据源。
- 私人知识库应放在 GitHub 仓库之外。
- 不要提交 `config.py`、Qdrant 数据、备份包或私人报告。
