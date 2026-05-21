---
title: Restore Guide / 恢复流程
category: summary
project: personal-project-secretary
doc_type: restore_guide
tags: [restore, migration, backup, bilingual, Ollama, Qdrant]
---

# Restore Guide / 恢复流程

This guide explains how to restore the system on a new computer or after reinstalling Windows.  
本文档说明如何在新电脑或重装系统后恢复本系统。

## 1. Restore Goal / 恢复目标

Restore these parts / 需要恢复：

- Markdown knowledge base / Markdown 知识库
- Ollama models / Ollama 模型
- Docker Qdrant / Docker Qdrant 服务
- Python virtual environment / Python 虚拟环境
- Qdrant vector index / Qdrant 向量索引

Markdown is the source of truth. Qdrant can be rebuilt.  
Markdown 是主数据源，Qdrant 可以重新生成。

## 2. Restore Files / 恢复文件

Restore your private knowledge base to a local directory, for example:

```text
D:\Personal_Knowledge_Base
```

Do not put private data inside the GitHub repository.  
不要把真实私人知识库放入 GitHub 代码仓库。

## 3. Install Ollama Models / 安装 Ollama 模型

```powershell
ollama pull qwen3:8b
ollama pull bge-m3
ollama list
```

## 4. Restore Qdrant / 恢复 Qdrant

```powershell
docker run -d --name pkb-qdrant -p 6333:6333 -v D:/Personal_Knowledge_Base/99_System/qdrant_storage:/qdrant/storage qdrant/qdrant
```

If the container already exists:

```powershell
docker start pkb-qdrant
```

Check:

```powershell
curl.exe http://127.0.0.1:6333/
curl.exe http://127.0.0.1:6333/collections
```

## 5. Restore Python Environment / 恢复 Python 环境

```powershell
cd <your-repo-path>\personal-project-secretary\rag_mvp
py -3.11 -m venv .venv
.\.venv\Scripts\activate
pip install -r ..\requirements.txt
```

## 6. Restore Config / 恢复配置

```powershell
Copy-Item .\config.example.py .\config.py
```

Edit `config.py`:

```python
KNOWLEDGE_ROOT = Path(r"D:\Personal_Knowledge_Base")
COLLECTION_NAME = "personal_knowledge_base"
```

## 7. Rebuild Index / 重建索引

```powershell
python check_env.py
python update_index.py
```

To force rebuild:

```powershell
curl.exe -X DELETE http://127.0.0.1:6333/collections/personal_knowledge_base
python ingest.py
python list_docs.py
```

## 8. Verify / 验证恢复结果

```powershell
python status.py
python list_docs.py
python ask.py "What is the current project status?"
```

中文测试：

```powershell
python ask.py "当前项目进行到哪里了？"
```

## 9. After Restore / 恢复后的建议

```powershell
python project_report.py --project Demo_Project
python time_report.py --project Demo_Project --mode weekly
python backup_kb.py
```

## 10. Notes / 注意事项

- Do not backup `.venv`; recreate it when needed. / `.venv` 不需要备份，恢复时重新创建。
- Do not rely on old Qdrant data; rebuild from Markdown when needed. / 不依赖旧 Qdrant 数据，可从 Markdown 重新生成。
- Keep real knowledge-base data outside GitHub. / 真实知识库数据不要放进 GitHub。
