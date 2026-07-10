---
title: Environment Variables
category: documentation
doc_type: environment_guide
version: v0.5.0-vector-store-config
tags: [environment, powershell, configuration, qdrant, ollama, knowledge-root]
---

# Environment Variables

# 环境变量临时、永久设置与检查记录

## 1. Supported Variables / 支持的变量

| Variable | Purpose |
|---|---|
| `PKB_KNOWLEDGE_ROOT` | private knowledge-base root |
| `PKB_OLLAMA_URL` | Ollama URL |
| `PKB_CHAT_MODEL` | chat model |
| `PKB_EMBED_MODEL` | embedding model |
| `PKB_QDRANT_URL` | Qdrant URL |
| `PKB_QDRANT_TIMEOUT` | Qdrant timeout |
| `PKB_QDRANT_COLLECTION` | Qdrant collection |

Configuration priority:

```text
environment variables
    ↓
config.py
    ↓
built-in defaults
```

---

## 2. View Current PowerShell Variables / 查看当前 PowerShell 变量

```powershell
Get-ChildItem Env:PKB_*
```

Single variable:

```powershell
echo $env:PKB_QDRANT_URL
echo $env:PKB_KNOWLEDGE_ROOT
echo $env:PKB_QDRANT_COLLECTION
```

---

## 3. Temporary Variables / 临时变量

Temporary variables only affect the current PowerShell process.

关闭当前 PowerShell 窗口后失效。

Local-PC example:

```powershell
$env:PKB_KNOWLEDGE_ROOT = "<your-knowledge-root>"
$env:PKB_QDRANT_URL = "http://127.0.0.1:6333"
$env:PKB_QDRANT_TIMEOUT = "120"
$env:PKB_QDRANT_COLLECTION = "personal_knowledge_base"

$env:PKB_OLLAMA_URL = "http://127.0.0.1:11434"
$env:PKB_CHAT_MODEL = "qwen3:8b"
$env:PKB_EMBED_MODEL = "bge-m3:latest"
```

VM / remote-Qdrant example:

```powershell
$env:PKB_KNOWLEDGE_ROOT = "<your-knowledge-root>"
$env:PKB_QDRANT_URL = "http://<qdrant-host>:6333"
$env:PKB_QDRANT_TIMEOUT = "120"
$env:PKB_QDRANT_COLLECTION = "personal_knowledge_base"

$env:PKB_OLLAMA_URL = "http://127.0.0.1:11434"
$env:PKB_CHAT_MODEL = "qwen3:8b"
$env:PKB_EMBED_MODEL = "bge-m3:latest"
```

---

## 4. Persistent User Variables / 用户级永久变量

```powershell
[Environment]::SetEnvironmentVariable(
    "PKB_KNOWLEDGE_ROOT",
    "<your-knowledge-root>",
    "User"
)

[Environment]::SetEnvironmentVariable(
    "PKB_QDRANT_URL",
    "http://<qdrant-host>:6333",
    "User"
)

[Environment]::SetEnvironmentVariable(
    "PKB_QDRANT_TIMEOUT",
    "120",
    "User"
)

[Environment]::SetEnvironmentVariable(
    "PKB_QDRANT_COLLECTION",
    "personal_knowledge_base",
    "User"
)

[Environment]::SetEnvironmentVariable(
    "PKB_OLLAMA_URL",
    "http://127.0.0.1:11434",
    "User"
)

[Environment]::SetEnvironmentVariable(
    "PKB_CHAT_MODEL",
    "qwen3:8b",
    "User"
)

[Environment]::SetEnvironmentVariable(
    "PKB_EMBED_MODEL",
    "bge-m3:latest",
    "User"
)
```

After setting user variables:

```text
close PowerShell
open a new PowerShell
```

Then:

```powershell
Get-ChildItem Env:PKB_*
```

---

## 5. Read User-Level Values / 查看用户级变量

```powershell
[Environment]::GetEnvironmentVariable("PKB_KNOWLEDGE_ROOT", "User")
[Environment]::GetEnvironmentVariable("PKB_QDRANT_URL", "User")
[Environment]::GetEnvironmentVariable("PKB_QDRANT_TIMEOUT", "User")
[Environment]::GetEnvironmentVariable("PKB_QDRANT_COLLECTION", "User")
[Environment]::GetEnvironmentVariable("PKB_OLLAMA_URL", "User")
[Environment]::GetEnvironmentVariable("PKB_CHAT_MODEL", "User")
[Environment]::GetEnvironmentVariable("PKB_EMBED_MODEL", "User")
```

---

## 6. Remove User-Level Values / 删除用户级变量

```powershell
[Environment]::SetEnvironmentVariable("PKB_KNOWLEDGE_ROOT", $null, "User")
[Environment]::SetEnvironmentVariable("PKB_QDRANT_URL", $null, "User")
[Environment]::SetEnvironmentVariable("PKB_QDRANT_TIMEOUT", $null, "User")
[Environment]::SetEnvironmentVariable("PKB_QDRANT_COLLECTION", $null, "User")
[Environment]::SetEnvironmentVariable("PKB_OLLAMA_URL", $null, "User")
[Environment]::SetEnvironmentVariable("PKB_CHAT_MODEL", $null, "User")
[Environment]::SetEnvironmentVariable("PKB_EMBED_MODEL", $null, "User")
```

Close and reopen PowerShell after deletion.

---

## 7. Remove Current-Process Variables / 删除当前窗口临时变量

```powershell
Remove-Item Env:PKB_KNOWLEDGE_ROOT -ErrorAction SilentlyContinue
Remove-Item Env:PKB_QDRANT_URL -ErrorAction SilentlyContinue
Remove-Item Env:PKB_QDRANT_TIMEOUT -ErrorAction SilentlyContinue
Remove-Item Env:PKB_QDRANT_COLLECTION -ErrorAction SilentlyContinue
Remove-Item Env:PKB_OLLAMA_URL -ErrorAction SilentlyContinue
Remove-Item Env:PKB_CHAT_MODEL -ErrorAction SilentlyContinue
Remove-Item Env:PKB_EMBED_MODEL -ErrorAction SilentlyContinue
```

---

## 8. Validate Actual Application Values / 验证项目实际读取值

```powershell
python check_env.py
python status.py
```

The application value is more important than the Windows configuration alone.

项目实际读取结果比单独查看 Windows 环境变量更重要。

---

## 9. Important Notes / 重要说明

- `127.0.0.1` means the current machine.
- A VM must use a reachable host or LAN IP for remote Qdrant.
- Temporary variables override persistent values in the current PowerShell process.
- Do not publish real IPs, user names, or private knowledge-base paths.
- Prefer user-level variables over machine-level variables.
- Use temporary variables first during deployment testing.
