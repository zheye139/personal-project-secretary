---
title: rag_mvp Engineering Notes
category: summary
project: personal-project-secretary
doc_type: rag_mvp_readme
tags: [RAG, README, engineering, bilingual, Ollama, Qdrant]
---

# rag_mvp Engineering Notes

`rag_mvp` is the command-line core of Personal Project Secretary + Knowledge Base Manager.

`rag_mvp` 是本项目的命令行核心工程。

## Architecture / 架构

```text
Markdown knowledge base
    ↓
ingest.py parses Frontmatter and chunks documents
    ↓
Ollama bge-m3 creates embeddings
    ↓
Docker Qdrant stores vector index
    ↓
ask.py and search_docs.py retrieve relevant chunks
    ↓
Ollama qwen3:8b generates answers and reports
```

## Core Scripts / 核心脚本

- `check_env.py` - environment check / 环境检查
- `ingest.py` - ingest Markdown documents / Markdown 入库
- `ask.py` - RAG Q&A / RAG 问答
- `search_docs.py` - search chunks without LLM / 不调用大模型的片段搜索
- `add_note.py` - add Markdown notes / 新增 Markdown 记录
- `inbox_import.py` - import Inbox notes / 导入 Inbox 记录
- `update_index.py` - check + ingest + list documents / 一键检查、入库、列出文档
- `status.py` - system overview / 系统状态总览
- `project_report.py` - project report / 项目报告
- `time_report.py` - daily or weekly report / 日报或周报
- `backup_kb.py` - backup knowledge base / 备份知识库
- `rebuild_index.py` - rebuild Qdrant index / 重建 Qdrant 索引
- `validate_kb.py` - validate Markdown metadata / 校验 Markdown 元数据
- `repair_frontmatter.py` - repair missing Frontmatter / 修复 Frontmatter
- `export_project.py` - export project package / 导出项目资料包

## Configuration / 配置

Do not commit `config.py`. Commit `config.example.py` only.  
不要提交 `config.py`，只提交 `config.example.py`。

```powershell
Copy-Item .\config.example.py .\config.py
```

`KNOWLEDGE_ROOT` should point to your private Markdown knowledge base.  
`KNOWLEDGE_ROOT` 应指向私人 Markdown 知识库目录。

## Data Principle / 数据原则

```text
Markdown is the source of truth.
Qdrant is a rebuildable index.
Ollama is the local model service.
Python scripts are the automation layer.
```

中文总结：

```text
Markdown 是主数据源。
Qdrant 是可重建索引。
Ollama 是本地模型服务。
Python 脚本是自动化工具层。
```

## Development Notes / 开发说明

- Keep scripts small and composable. / 脚本保持小而可组合。
- Keep paths in `config.py`. / 路径集中放在 `config.py`。
- Avoid committing private data. / 不提交私人数据。
- Run `python update_index.py` after adding or editing Markdown. / 新增或修改 Markdown 后执行 `python update_index.py`。
