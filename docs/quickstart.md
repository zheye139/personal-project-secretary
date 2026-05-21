---
title: Quick Start / 快速开始
category: summary
project: personal-project-secretary
doc_type: quickstart
tags: [quickstart, setup, bilingual, RAG, Ollama, Qdrant]
---

# Quick Start / 快速开始

This guide helps you run the local RAG MVP for the first time.  
本文档用于帮助你第一次运行本地 RAG MVP。

## 1. Repository and Knowledge Base / 代码仓库与知识库

Keep them separate.  
建议将两者分开管理。

```text
Code repository / 代码仓库:
D:\Projects\personal-project-secretary

Knowledge base / 私人知识库:
D:\Personal_Knowledge_Base
```

`KNOWLEDGE_ROOT` should point to the knowledge base, not the GitHub repository.  
`KNOWLEDGE_ROOT` 应指向知识库目录，而不是 GitHub 仓库目录。

## 2. Install Ollama Models / 安装 Ollama 模型

```powershell
ollama pull qwen3:8b
ollama pull bge-m3
ollama list
```

If Ollama shows `bge-m3:latest`, set `EMBED_MODEL = "bge-m3:latest"`.  
如果 `ollama list` 显示 `bge-m3:latest`，则配置 `EMBED_MODEL = "bge-m3:latest"`。

## 3. Start Qdrant / 启动 Qdrant

```powershell
docker run -d --name pkb-qdrant -p 6333:6333 -v D:/Personal_Knowledge_Base/99_System/qdrant_storage:/qdrant/storage qdrant/qdrant
```

If the container already exists / 如果容器已经存在：

```powershell
docker start pkb-qdrant
```

Check Qdrant / 检查 Qdrant：

```powershell
curl.exe http://127.0.0.1:6333/
curl.exe http://127.0.0.1:6333/collections
```

## 4. Create Python Environment / 创建 Python 虚拟环境

```powershell
cd <your-repo-path>\personal-project-secretary\rag_mvp
py -3.11 -m venv .venv
.\.venv\Scripts\activate
pip install -r ..\requirements.txt
```

Python 3.11 is recommended.  
推荐使用 Python 3.11。

## 5. Create Local Config / 创建本地配置

```powershell
Copy-Item .\config.example.py .\config.py
```

Edit `config.py` / 编辑 `config.py`：

```python
KNOWLEDGE_ROOT = Path(r"D:\Personal_Knowledge_Base")
COLLECTION_NAME = "personal_knowledge_base"
```

## 6. Prepare Example Knowledge Base / 准备示例知识库

You can copy the template from `examples/Personal_Knowledge_Base_Template` to your local knowledge base path.  
可以将 `examples/Personal_Knowledge_Base_Template` 复制到本地知识库目录作为起点。

## 7. Check Environment / 检查环境

```powershell
python check_env.py
```

Expected result / 预期结果：

```text
Ollama is accessible.
Qdrant is accessible.
The configured chat model exists.
The configured embedding model exists.
```

## 8. Index Documents / 入库文档

```powershell
python update_index.py
```

## 9. Ask a Question / 提问

```powershell
python ask.py "What is the current project status?"
python ask.py "当前项目进行到哪里了？"
```

## 10. Search Without LLM / 只检索，不调用大模型

```powershell
python search_docs.py "project status" --show-text
```

## 11. Generate Reports / 生成报告

```powershell
python project_report.py --project Demo_Project
python time_report.py --project Demo_Project --mode weekly
python update_index.py
```

## 12. Backup / 备份

```powershell
python backup_kb.py
```

## 13. Recommended Daily Flow / 推荐日常流程

```powershell
cd <your-repo-path>\personal-project-secretary\rag_mvp
.\.venv\Scripts\activate
docker start pkb-qdrant
python status.py
python update_index.py
```
