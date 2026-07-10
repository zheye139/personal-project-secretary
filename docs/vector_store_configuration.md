---
title: Vector Store Configuration
category: documentation
doc_type: deployment_guide
version: v0.5.0-vector-store-config
tags: [vector-store, qdrant, configuration, deployment, vmware, network]
---

# Vector Store Configuration

# Vector Store 与 Qdrant 配置说明

## 1. What Is the Vector Store Layer? / 什么是 Vector Store 配置层

In M5, `Vector Store` means the application-side configuration and connection layer used to access the vector database.

在 M5 中，Vector Store 指项目访问向量数据库时使用的统一配置和连接层。

Current implementation:

```text
Knowledge Operating System
    ↓
vector_store_config.py
    ↓
Qdrant
```

Current backend:

```text
Qdrant only
```

M5 does not yet include Milvus, pgvector, Weaviate, or other backends.

---

## 2. Why This Layer Exists / 为什么需要这一层

Old assumption:

```text
Qdrant must run at:
http://127.0.0.1:6333
```

M5:

```text
Qdrant may run on:
- the current PC
- Docker
- Windows/Linux service
- a LAN server
- the development PC
- another reachable host
```

The application only needs the Qdrant URL, timeout, and collection name.

---

## 3. Configuration Priority / 配置优先级

```text
environment variables
    ↓
config.py
    ↓
built-in defaults
```

环境变量适合部署差异；`config.py` 适合本地私人配置；默认值用于最小启动。

---

## 4. Supported Environment Variables / 环境变量

| Variable | Example | Purpose |
|---|---|---|
| `PKB_KNOWLEDGE_ROOT` | `<your-knowledge-root>` | private Markdown knowledge base |
| `PKB_OLLAMA_URL` | `http://127.0.0.1:11434` | Ollama service |
| `PKB_CHAT_MODEL` | `qwen3:8b` | chat model |
| `PKB_EMBED_MODEL` | `bge-m3:latest` | embedding model |
| `PKB_QDRANT_URL` | `http://127.0.0.1:6333` | Qdrant service |
| `PKB_QDRANT_TIMEOUT` | `120` | timeout in seconds |
| `PKB_QDRANT_COLLECTION` | `personal_knowledge_base` | collection name |

---

## 5. Local Qdrant / 本机 Qdrant

```powershell
$env:PKB_QDRANT_URL = "http://127.0.0.1:6333"
$env:PKB_QDRANT_COLLECTION = "personal_knowledge_base"
```

Check:

```powershell
curl.exe http://127.0.0.1:6333/
curl.exe http://127.0.0.1:6333/collections
```

---

## 6. LAN or Remote Qdrant / 局域网或远程 Qdrant

```powershell
$env:PKB_QDRANT_URL = "http://<qdrant-host>:6333"
$env:PKB_QDRANT_COLLECTION = "personal_knowledge_base"
```

Check network:

```powershell
ping <qdrant-host>

Test-NetConnection <qdrant-host> -Port 6333

curl.exe http://<qdrant-host>:6333/
```

Expected:

```text
TcpTestSucceeded : True
```

---

## 7. VMware NAT Mode / VMware NAT 模式

Recommended for the M5 VM-to-host validation:

```text
VMware Network Adapter:
NAT
```

Typical structure:

```text
Host Windows
├─ VMware Network Adapter VMnet8
└─ Docker + Qdrant

Virtual Machine
└─ Knowledge Operating System
```

On the host:

```powershell
ipconfig
```

Find:

```text
VMware Network Adapter VMnet8
IPv4 Address: <host-ip>
```

In the VM:

```powershell
Test-NetConnection <host-ip> -Port 6333
curl.exe http://<host-ip>:6333/
```

Then:

```powershell
$env:PKB_QDRANT_URL = "http://<host-ip>:6333"
```

Important:

```text
127.0.0.1 in the VM means the VM itself.
```

---

## 8. Docker Port Exposure / Docker 端口映射

Check:

```powershell
docker ps
```

For cross-PC access, the port mapping should normally be reachable, for example:

```text
0.0.0.0:6333->6333/tcp
```

If Qdrant is only bound to:

```text
127.0.0.1:6333
```

another PC or VM may not be able to access it.

---

## 9. Windows Firewall / Windows 防火墙

If ping works but TCP 6333 fails:

```powershell
Test-NetConnection <host-ip> -Port 6333
```

check:

- Qdrant container/service is running
- Docker port is published
- Windows Firewall allows inbound TCP 6333
- the active network profile is correct

For a trusted private test network, create a limited inbound TCP 6333 rule.

Do not expose Qdrant directly to the public Internet without a dedicated security design.

---

## 10. Collection Consistency / Collection 名称一致性

Check existing collections:

```powershell
curl.exe http://<qdrant-host>:6333/collections
```

If Qdrant contains:

```text
personal_knowledge_base
```

configure:

```powershell
$env:PKB_QDRANT_COLLECTION = "personal_knowledge_base"
```

Do not accidentally use a different name unless you intend to create a new collection.

---

## 11. Non-destructive Validation / 非破坏性验证

```powershell
python check_env.py
python status.py
python inspect_collection.py
python list_docs.py

python search_docs.py "M5 Vector Store"
python ask.py "请简单说明当前知识库是什么"
```

---

## 12. Common Errors / 常见错误

### 12.1 `No module named 'qdrant_client'`

Cause:

```text
The current Python environment has not installed qdrant-client.
```

Fix:

```powershell
python -m pip install -r ..\requirements.txt
```

or:

```powershell
python -m pip install qdrant-client
```

Package name:

```text
qdrant-client
```

Import name:

```text
qdrant_client
```

---

### 12.2 Collection does not exist / Collection 不存在

Check:

```powershell
python check_env.py
curl.exe http://<qdrant-host>:6333/collections
```

Make sure:

```text
PKB_QDRANT_COLLECTION
=
existing target collection name
```

---

### 12.3 Qdrant connection failed / Qdrant 连接失败

Check:

```powershell
Test-NetConnection <qdrant-host> -Port 6333
curl.exe http://<qdrant-host>:6333/
```

---

### 12.4 Wrong use of `127.0.0.1`

```text
127.0.0.1 always means the current machine.
```

A VM cannot use its own `127.0.0.1` to access Qdrant on the host.

---

### 12.5 Port 6333 is blocked

Check:

- Docker mapping
- Qdrant process
- Windows Firewall
- VMware network mode
- network profile

---

## 13. Security Boundary / 安全边界

M5 supports LAN / remote Qdrant connectivity, but does not provide a public-network security solution.

Recommended:

- trusted private network
- limited firewall scope
- no direct public exposure
- keep private knowledge-base files outside the GitHub repository
