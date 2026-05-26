---
title: Command Reference / 命令速查表
created: 2026-05-26
category: summary
project: personal-project-secretary
doc_type: command_reference
tags: [commands, PowerShell, RAG, Qdrant, Ollama, Python, M1, M2, personal-secretary]
---

# Command Reference / 命令速查表

This document lists common commands for the local knowledge base manager and M2 personal secretary layer.

本文档集中记录本地知识库管理员工具箱和 M2 个人秘书层的常用命令。

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
docker run -d --name pkb-qdrant -p 6333:6333 -v D:/Personal_Knowledge_Base/99_System/qdrant_storage:/qdrant/storage qdrant/qdrant
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

## 12. Backup, Export, and Maintenance / 备份、导出与维护

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
