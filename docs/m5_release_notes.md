---
title: M5 Vector Store Configuration and Cross-PC Deployment Validation
category: documentation
doc_type: release_notes
version: v0.5.0-vector-store-config
tags: [M5, vector-store, qdrant, configuration, deployment, vm, cross-pc]
---

# M5 Vector Store Configuration and Cross-PC Deployment Validation

# M5 Vector Store 配置层与跨 PC 部署验证

## Version / 版本

```text
v0.5.0-vector-store-config
```

---

## 1. Overview / 概述

M5 introduces a unified Vector Store configuration layer for Qdrant and validates that the Knowledge Operating System can use Qdrant without requiring Qdrant to run inside the same operating system instance.

M5 新增统一 Vector Store 配置层，并验证 Knowledge Operating System 可以访问其他电脑、宿主机或局域网服务器上的 Qdrant，而不再要求 Qdrant 必须运行在当前系统内部。

M5 changes the deployment assumption from:

```text
application
    ↓
hard-coded localhost Qdrant
```

to:

```text
application
    ↓
Vector Store configuration
    ↓
local / LAN / remote Qdrant
```

---

## 2. Main Additions / 主要新增

### 2.1 Unified Vector Store Configuration / 统一 Vector Store 配置

New shared configuration module:

```text
rag_mvp/vector_store_config.py
```

Main responsibilities:

- read Qdrant URL
- read timeout
- read collection name
- create the shared Qdrant client
- build Qdrant REST URLs
- add the configured Qdrant host to `NO_PROXY` / `no_proxy`

---

### 2.2 Configuration Priority / 配置优先级

```text
environment variables
    ↓
config.py
    ↓
built-in defaults
```

环境变量优先，可以覆盖本地 `config.py`。

---

### 2.3 Supported Environment Variables / 支持的环境变量

| Variable | Purpose |
|---|---|
| `PKB_KNOWLEDGE_ROOT` | private Markdown knowledge-base root |
| `PKB_OLLAMA_URL` | Ollama service URL |
| `PKB_CHAT_MODEL` | chat model name |
| `PKB_EMBED_MODEL` | embedding model name |
| `PKB_QDRANT_URL` | Qdrant service URL |
| `PKB_QDRANT_TIMEOUT` | Qdrant timeout in seconds |
| `PKB_QDRANT_COLLECTION` | Qdrant collection name |

---

### 2.4 Unified Qdrant Client / 统一 Qdrant Client

The main indexing, retrieval, Ask, diagnostics, collection-inspection, and secretary/report scripts now use the shared Vector Store configuration layer.

主要索引、检索、Ask、诊断、Collection 检查以及秘书/报告脚本统一通过 Vector Store 配置层创建 Qdrant Client。

---

### 2.5 Supported Deployment Locations / 支持的部署位置

M5 supports Qdrant running as:

- local Docker container
- local Windows/Linux service
- LAN server
- development PC accessed by a virtual machine
- other reachable Qdrant service

M5 当前只实现 Qdrant 后端，不代表已经支持其他向量数据库。

---

## 3. Validation Results / 验证结果

Validated:

- development-PC local Qdrant connection
- environment-variable overrides
- Qdrant collection discovery
- virtual machine to host/development-PC Qdrant access
- `check_env.py`
- `status.py`
- `inspect_collection.py`
- `search_docs.py`
- `ask.py`
- local FastAPI/Web interface

已完成：

- 开发机本机 Qdrant 连接验证
- 环境变量优先级验证
- Collection 检查
- 虚拟机访问开发机 Qdrant
- Search 检索
- Ask 基础问答
- 本地 FastAPI / Web 使用验证

No real IP address, private knowledge-base path, or private document content is included in this public release.

---

## 4. Example Configuration / 配置示例

Local Qdrant:

```powershell
$env:PKB_QDRANT_URL = "http://127.0.0.1:6333"
$env:PKB_QDRANT_COLLECTION = "personal_knowledge_base"
```

Remote or LAN Qdrant:

```powershell
$env:PKB_QDRANT_URL = "http://<qdrant-host>:6333"
$env:PKB_QDRANT_COLLECTION = "personal_knowledge_base"
```

---

## 5. Important Notes / 重要说明

- `127.0.0.1` always means the current machine.
- A VM must use a reachable host or LAN IP to access Qdrant on another PC.
- The configured collection name must match the target Qdrant collection.
- The remote Qdrant port must be reachable.
- Windows Firewall may need a TCP 6333 inbound rule.
- Docker must publish port 6333 to a reachable address.
- The local Web/API service still binds to `127.0.0.1:8000` by default.

---

## 6. New-PC Python Dependency Note / 新 PC Python 依赖说明

Each PC and each Python virtual environment must install dependencies independently.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -r ..\requirements.txt
```

The pip package name is:

```text
qdrant-client
```

The Python import name is:

```python
from qdrant_client import QdrantClient
```

---

## 7. Non-destructive Validation / 非破坏性验证

```powershell
python check_env.py
python status.py
python inspect_collection.py
python list_docs.py

python search_docs.py "M5 Vector Store"
python ask.py "请简单说明当前知识库是什么"
```

---

## 8. Full Health Check Warning / 完整健康检查提示

`health_check_full.py` is a write-path health test.

It may create, write, search, and delete a temporary Qdrant collection.

执行前应先确认当前测试环境允许创建和删除临时 Collection。

---

## 9. Known Limitations / 已知限制

- Qdrant is currently the only implemented Vector Store backend.
- Remote access depends on network routing, firewall rules, and port exposure.
- Public-network deployment security is not provided.
- Complex Ask requests may take longer on low-performance virtual machines.
- `health_check_full.py` is not a read-only check.
- Markdown remains the source of truth.
- Qdrant remains a rebuildable index.

---

## 10. Next Direction / 下一阶段方向

Planned:

```text
M6: Knowledge Layer
M7: Knowledge Evolution
M8: Secretary Intelligence
M9: Knowledge Graph
M10: Knowledge Operating System closed loop
```

These are future directions and are not included in M5.
