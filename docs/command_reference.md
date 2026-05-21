---
title: Command Reference / 命令速查表
category: summary
project: personal-project-secretary
doc_type: command_reference
tags: [commands, PowerShell, bilingual, RAG, Ollama, Qdrant]
---

# Command Reference / 命令速查表

## Enter Project / 进入工程目录

```powershell
cd <your-repo-path>\personal-project-secretary\rag_mvp
.\.venv\Scripts\activate
```

## Ollama / Ollama 命令

```powershell
ollama --version
ollama list
ollama pull qwen3:8b
ollama pull bge-m3
curl.exe http://127.0.0.1:11434/api/tags
```

## Qdrant and Docker / Qdrant 与 Docker

```powershell
docker ps
docker ps -a
docker start pkb-qdrant
docker restart pkb-qdrant
docker logs pkb-qdrant --tail 100
curl.exe http://127.0.0.1:6333/
curl.exe http://127.0.0.1:6333/collections
```

Create Qdrant container / 创建 Qdrant 容器：

```powershell
docker run -d --name pkb-qdrant -p 6333:6333 -v D:/Personal_Knowledge_Base/99_System/qdrant_storage:/qdrant/storage qdrant/qdrant
```

## Python Environment / Python 环境

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\activate
pip install -r ..\requirements.txt
pip freeze > ..\requirements.lock.txt
```

## Environment Check / 环境检查

```powershell
python check_env.py
python status.py
python list_docs.py
python inspect_collection.py
```

## Indexing / 入库与索引

```powershell
python ingest.py
python update_index.py
python rebuild_index.py --execute
```

## Ask / RAG 问答

```powershell
python ask.py "What is the current project status?"
python ask.py --project Demo_Project "What is the project progress?"
python ask.py --doc-type environment_setup "How do I reinstall the Python environment?"
python ask.py --category problem "What problems have been recorded?"
python ask.py --tag RAG "What has been completed?"
```

## Search Documents / 搜索知识库片段

```powershell
python search_docs.py "Python environment" --show-text
python search_docs.py --doc-type environment_setup "Python environment" --show-text
python search_docs.py --category problem "Qdrant connection" --show-text
python search_docs.py --tag RAG "system progress" --show-text
```

## Add Notes / 新增记录

```powershell
python add_note.py --category project --project Demo_Project --doc-type progress_log --title "Progress title" --tags "RAG,progress" --content "Progress content"
python add_note.py --category problem --project Demo_Project --title "Issue title" --tags "RAG,issue" --content "Issue content"
python add_note.py --category decision --project Demo_Project --title "Decision title" --tags "RAG,decision" --content "Decision content"
python update_index.py
```

## Reports / 报告

```powershell
python project_report.py --project Demo_Project
python time_report.py --project Demo_Project --mode daily
python time_report.py --project Demo_Project --mode weekly
python update_index.py
```

## Backup / 备份

```powershell
python backup_kb.py
```

## Syntax Check / 语法与缩进检查

```powershell
python -m py_compile ask.py
python -m tabnanny ask.py
python -m py_compile config.py check_env.py ingest.py ask.py search_docs.py list_docs.py inspect_collection.py update_index.py status.py add_note.py project_report.py time_report.py backup_kb.py
```

## Troubleshooting / 故障排查

Ollama / Ollama：

```powershell
ollama list
curl.exe http://127.0.0.1:11434/api/tags
```

Qdrant / Qdrant：

```powershell
docker ps -a
docker start pkb-qdrant
curl.exe http://127.0.0.1:6333/collections
```

Rebuild index / 重建索引：

```powershell
curl.exe -X DELETE http://127.0.0.1:6333/collections/personal_knowledge_base
python ingest.py
python list_docs.py
```
