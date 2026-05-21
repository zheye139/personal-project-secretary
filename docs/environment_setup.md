---
title: Environment Setup / 环境安装说明
category: summary
project: personal-project-secretary
doc_type: environment_setup
tags: [environment, setup, Python, Ollama, Qdrant, bilingual]
---

# Environment Setup / 环境安装说明

This document explains how to install and restore the runtime environment.  
本文档说明如何安装和恢复运行环境。

## 1. Required Software / 必要软件

Recommended / 推荐：

- Windows 10/11
- Python 3.11
- Docker Desktop
- Ollama
- VS Code
- Git
- PowerShell

Python 3.11 is recommended for the first public release.  
第一版公开发布建议优先使用 Python 3.11。

## 2. Install Ollama Models / 安装 Ollama 模型

```powershell
ollama pull qwen3:8b
ollama pull bge-m3
ollama list
```

Check Ollama API / 检查 Ollama API：

```powershell
curl.exe http://127.0.0.1:11434/api/tags
```

If `ollama list` shows `bge-m3:latest`, set:

```python
EMBED_MODEL = "bge-m3:latest"
```

如果显示 `bge-m3:latest`，请在 `config.py` 中保持一致。

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

## 4. Create Python Virtual Environment / 创建 Python 虚拟环境

```powershell
cd <your-repo-path>\personal-project-secretary\rag_mvp
py -3.11 -m venv .venv
.\.venv\Scripts\activate
pip install -r ..\requirements.txt
```

This project is a script-based MVP. It does not use `setup.py` or `pip install .`.  
本项目是脚本型 MVP，不使用 `setup.py` 或 `pip install .`。

## 5. Configure config.py / 配置 config.py

```powershell
Copy-Item .\config.example.py .\config.py
```

Edit / 编辑：

```python
KNOWLEDGE_ROOT = Path(r"D:\Personal_Knowledge_Base")
OLLAMA_URL = "http://127.0.0.1:11434"
CHAT_MODEL = "qwen3:8b"
EMBED_MODEL = "bge-m3:latest"
QDRANT_URL = "http://127.0.0.1:6333"
COLLECTION_NAME = "personal_knowledge_base"
```

`KNOWLEDGE_ROOT` must point to your Markdown knowledge base, not to the GitHub repository.  
`KNOWLEDGE_ROOT` 必须指向 Markdown 知识库目录，而不是 GitHub 仓库目录。

## 6. Check Environment / 环境自检

```powershell
python check_env.py
```

Expected / 预期：

```text
Ollama is accessible.
Qdrant is accessible.
The chat model exists.
The embedding model exists.
```

## 7. Index Documents / 重新入库

```powershell
python update_index.py
```

This command runs environment check, document ingestion, and document listing.  
该命令会执行环境检查、文档入库和文档列表输出。

## 8. Test / 测试

```powershell
python status.py
python ask.py "What is the current project status?"
python search_docs.py "Python environment" --show-text
```

## 9. Common Issues / 常见问题

### Ollama connection failed / Ollama 无法连接

```powershell
ollama list
curl.exe http://127.0.0.1:11434/api/tags
```

### Qdrant connection failed / Qdrant 无法连接

```powershell
docker ps -a
docker start pkb-qdrant
curl.exe http://127.0.0.1:6333/collections
```

### bge-m3 model name mismatch / bge-m3 模型名不匹配

Check / 检查：

```powershell
ollama list
```

Then update `EMBED_MODEL` in `config.py`.  
然后修改 `config.py` 中的 `EMBED_MODEL`。
