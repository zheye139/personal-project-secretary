---
title: rag_mvp Engineering Notes / rag_mvp 工程说明
created: 2026-05-26
category: summary
project: personal-project-secretary
doc_type: rag_mvp_readme
tags: [RAG, engineering, M1, M2, personal-secretary, Ollama, Qdrant]
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

The project is not a model training project. It is a local knowledge workflow.

本项目不是模型训练项目，而是本地知识工作流。

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

## 6. Future Optimization / 后续优化

Incremental indexing and hybrid retrieval are intentionally not part of M2 closeout.

增量索引和混合检索不纳入 M2 封版范围。

They are planned as later optimization work.

它们计划作为后续优化专项单独处理。
