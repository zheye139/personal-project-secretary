# Quick Start / 快速开始

This guide helps you run **Knowledge Operating System** on Windows.

本文档用于帮助你在 Windows 上快速运行 Knowledge Operating System。

---

## 1. Repository and Private Knowledge Base / 代码仓库与私人知识库

Keep them separate.

```text
Code repository:
<your-repo-path>\Knowledge_Operating_System

Private knowledge base:
<your-knowledge-root>
```

Do not upload the real private knowledge base to GitHub.

---

## 2. Install Ollama Models / 安装 Ollama 模型

```powershell
ollama pull qwen3:8b
ollama pull bge-m3
```

Check:

```powershell
ollama list
```

---

## 3. Choose Qdrant Deployment / 选择 Qdrant 部署方式

### A. Local Docker Qdrant / 本机 Docker Qdrant

```powershell
docker run -d `
  --name pkb-qdrant `
  -p 6333:6333 `
  -v <your-knowledge-root>/99_System/qdrant_storage:/qdrant/storage `
  qdrant/qdrant
```

Check:

```powershell
curl.exe http://127.0.0.1:6333/
```

### B. Existing LAN / Remote Qdrant / 已有局域网或远程 Qdrant

```powershell
Test-NetConnection <qdrant-host> -Port 6333
curl.exe http://<qdrant-host>:6333/
```

---

## 4. Create Python Environment / 创建 Python 环境

```powershell
cd <your-repo-path>\Knowledge_Operating_System\rag_mvp

py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -r ..\requirements.txt
```

Each PC and each virtual environment must install dependencies independently.

---

## 5. Configure Environment Variables / 配置环境变量

Local Qdrant:

```powershell
$env:PKB_KNOWLEDGE_ROOT = "<your-knowledge-root>"
$env:PKB_QDRANT_URL = "http://127.0.0.1:6333"
$env:PKB_QDRANT_COLLECTION = "personal_knowledge_base"
```

Remote Qdrant:

```powershell
$env:PKB_KNOWLEDGE_ROOT = "<your-knowledge-root>"
$env:PKB_QDRANT_URL = "http://<qdrant-host>:6333"
$env:PKB_QDRANT_COLLECTION = "personal_knowledge_base"
```

Optional:

```powershell
$env:PKB_QDRANT_TIMEOUT = "120"
$env:PKB_OLLAMA_URL = "http://127.0.0.1:11434"
$env:PKB_CHAT_MODEL = "qwen3:8b"
$env:PKB_EMBED_MODEL = "bge-m3:latest"
```

---

## 6. Non-destructive Environment Check / 非破坏性环境检查

```powershell
python check_env.py
python status.py
python inspect_collection.py
python list_docs.py
```

---

## 7. Search and Ask / 搜索和问答

```powershell
python search_docs.py "M5 Vector Store"

python ask.py "请简单说明当前知识库是什么"
```

---

## 8. Start Local Web/API / 启动本地 Web/API

If PowerShell blocks the script:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Start:

```powershell
.\run_api.ps1
```

Open:

```text
http://127.0.0.1:8000/
http://127.0.0.1:8000/search
http://127.0.0.1:8000/ask
http://127.0.0.1:8000/diagnostics
http://127.0.0.1:8000/docs
```

---

## 9. Index Documents / 文档入库

Only run after confirming the knowledge root and target collection:

```powershell
python update_index.py
```

---

## 10. Full Health Check Warning / 完整健康检查提示

`health_check_full.py` may create, write, search, and delete a temporary Qdrant collection.

Do not treat it as a read-only check.

执行前请先确认当前测试环境允许创建和删除临时 Collection。

---

## 11. Important Notes / 重要说明

- `127.0.0.1` always means the current machine.
- A VM must use a reachable host/LAN IP to access Qdrant on another PC.
- `PKB_QDRANT_COLLECTION` must match the target collection.
- The current Vector Store backend is Qdrant.
- The Web/API server remains local-first and binds to `127.0.0.1` by default.
