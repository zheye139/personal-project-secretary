---

## title: M4 Release Notes / M4 发布说明  
category: documentation  
doc_type: release_notes  
version: v0.4.0-local-console-webapi

# M4 Release Notes / M4 发布说明

## Version / 版本

```text
v0.4.0-local-console-webapi
```

M4 adds a local console, local FastAPI API, and local browser Web interface on top of the M1-M3 command-line RAG workflow.

M4 在 M1-M3 命令行 RAG 工作流基础上，新增了本地终端菜单、本地 FastAPI API 和本地浏览器 Web 界面。

---

## Main Additions / 主要新增内容

### 1. Local Console / 本地终端菜单

M4 adds a terminal launcher:

```text
rag_mvp/launcher.py
```

It provides a guided menu for common local workflows, including status checks, ask, search, reports, retrieval evaluation, backup, advanced maintenance, and starting the local API server.

M4 新增本地终端菜单入口，可用于引导式执行常见本地工作流，包括状态检查、问答、搜索、报告、检索评估、备份、高级维护以及启动本地 API 服务。

---

### 2. Command Registry / 命令注册表

M4 adds:

```text
rag_mvp/command_registry.py
```

The command registry records command metadata and provides a unified source for launcher and future UI integrations.

命令注册表用于统一登记常用命令及其元数据，为 launcher 和后续 UI 集成提供统一来源。

---

### 3. Project Discovery / 项目发现

M4 adds:

```text
rag_mvp/project_discovery.py
```

It discovers projects, categories, document types, tags, files, and summary information from the local manifest.

项目发现工具可从本地 manifest 中发现项目、分类、文档类型、标签、文件和汇总信息。

---

### 4. Local FastAPI API / 本地 FastAPI API

M4 adds:

```text
rag_mvp/api_app.py
rag_mvp/run_api.ps1
```

Start the local API/Web service:

```powershell
cd rag_mvp
.\run_api.ps1
```

Default address:

```text
http://127.0.0.1:8000/
```

M4 新增本地 FastAPI API 和启动脚本，默认绑定 `127.0.0.1`，用于本机访问。

---

### 5. Local Web Pages / 本地 Web 页面

M4 adds the following local browser pages:

```text
/
 /search
 /ask
 /diagnostics
 /troubleshooting
 /docs
 /api
```

Page files:

```text
rag_mvp/web/index.html
rag_mvp/web/search.html
rag_mvp/web/ask.html
rag_mvp/web/diagnostics.html
rag_mvp/web/troubleshooting.html
```

页面作用：

- `/`：本地首页
    
- `/search`：本地知识库搜索页面
    
- `/ask`：本地 RAG 问答页面
    
- `/diagnostics`：本地服务状态诊断页面
    
- `/troubleshooting`：本地故障排查说明页面
    
- `/docs`：FastAPI 自动文档
    
- `/api`：API 总览
    

---

## Main API Endpoints / 主要 API

M4 includes:

```text
GET  /api
GET  /api/v1/health
GET  /api/v1/commands
GET  /api/v1/discovery/summary
GET  /api/v1/discovery/projects
GET  /api/v1/discovery/doc-types
GET  /api/v1/discovery/categories
GET  /api/v1/discovery/tags
GET  /api/v1/search
POST /api/v1/ask
GET  /api/v1/diagnostics
```

---

## Search / 搜索能力

Search API:

```text
GET /api/v1/search
```

Main behavior:

- Default mode: `keyword`
    
- Supports `keyword`, `vector`, and `hybrid`
    
- Limit maximum: `20`
    
- Does not write to the knowledge base
    
- Does not return raw payload
    
- Does not return source path
    
- Does not return point id
    
- Does not return full Markdown text by default
    

搜索能力默认使用 `keyword` 模式，也支持 `vector` 和 `hybrid`。Search 不写入知识库，不返回原始 payload、本地 source 路径、point id 或完整 Markdown 正文。

---

## Ask / 问答能力

Ask API:

```text
POST /api/v1/ask
```

Main behavior:

- Default search mode: `hybrid`
    
- Limit maximum: `10`
    
- Calls local Ollama for answer generation
    
- Uses local Qdrant for retrieval
    
- `save_log=false` by default
    
- `save_log=true` is currently rejected
    
- Does not return raw context
    
- Does not return prompt
    
- Does not return source path
    
- Does not return full Markdown text
    

Ask 页面和 API 用于本地 RAG 问答。当前默认不保存 QA log，且 `save_log=true` 会被拒绝。

---

## Diagnostics / 诊断能力

Diagnostics page:

```text
/diagnostics
```

Diagnostics API:

```text
GET /api/v1/diagnostics
```

It checks local service status, including:

- API
    
- command registry
    
- discovery / manifest
    
- Qdrant
    
- Ollama
    

诊断页面用于检查本地 API、命令注册表、项目发现、Qdrant 和 Ollama 的状态。

---

## Troubleshooting / 故障排查

Troubleshooting page:

```text
/troubleshooting
```

It provides local troubleshooting guidance for:

- API service unavailable
    
- Search failed
    
- Ask failed
    
- Qdrant unavailable
    
- Ollama unavailable
    
- 404 pages
    
- information that should not appear in Web/API responses
    

故障排查页面用于说明本地服务异常、Search 失败、Ask 失败、Qdrant/Ollama 不可用等常见情况。

---

## Safety Boundary / 安全边界

M4 keeps a conservative local-first safety boundary:

- API binds to `127.0.0.1` by default.
    
- Not intended for public-network exposure.
    
- Web pages do not use external CDN assets.
    
- Web pages do not load public-network resources.
    
- Web pages do not execute `update_index`, `rebuild`, `backup`, or `add_note`.
    
- Search does not write to the knowledge base.
    
- Ask does not save QA logs by default.
    
- `save_log=true` is currently rejected.
    
- API/Web responses should not expose local absolute paths.
    
- API/Web responses should not expose config URLs.
    
- API/Web responses should not expose raw context.
    
- API/Web responses should not expose prompts.
    
- API/Web responses should not expose raw payloads.
    
- API/Web responses should not expose full Markdown text.
    
- API/Web responses should not expose source paths.
    
- Error messages should not expose stack traces or raw exception text.
    

M4 继续保持本地优先和保守安全边界。Web/API 默认只用于本机访问，不面向公网部署，不从 Web 执行索引、重建、备份、写笔记等操作。

---

## Test Command / 测试命令

Recommended local test command:

```powershell
cd rag_mvp
.\.venv\Scripts\python.exe -m py_compile ask.py search_docs.py api_app.py tests\test_api_app.py
.\.venv\Scripts\python.exe -m tabnanny ask.py search_docs.py api_app.py tests\test_api_app.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_api_app.py"
```

---

## Known Limitations / 已知限制

- Search and Ask depend on local Qdrant and current index state.
    
- Vector and hybrid retrieval may call local Ollama embedding.
    
- Ask depends on local Ollama answer generation.
    
- Ask may take longer than normal API requests.
    
- No public-network deployment support.
    
- No multi-user login system.
    
- No Web write operations.
    
- No Web-triggered indexing, rebuild, or backup.
    
- Detailed troubleshooting may still require checking local terminal logs.
    

---

## Suggested Next Stage / 下一阶段建议

After M4, the next recommended stage is M5:

```text
M5: release packaging, documentation polish, and GitHub release preparation
```

M5 can focus on:

- installation verification
    
- README polish
    
- release tag
    
- GitHub release notes
    
- example knowledge-base template
    
- screenshots
    
- new-user startup workflow