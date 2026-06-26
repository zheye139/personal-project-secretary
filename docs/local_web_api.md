---
title: Local Web API / 本地 Web API
category: documentation
doc_type: local_web_api
version: v0.4.0-local-console-webapi
---

# Local Web API / 本地 Web API

M4 adds a local FastAPI API and browser Web interface.

M4 新增了一个本地 FastAPI API 和浏览器 Web 界面。

## Start / 启动

```powershell
cd rag_mvp
.\run_api.ps1
```

The default address is / 默认地址为:

```text
http://127.0.0.1:8000/
```

## Pages / 页面

- `/`: local homepage / 本地首页
- `/search`: local Search page / 本地 Search 页面
- `/ask`: local Ask page / 本地 Ask 页面
- `/diagnostics`: local diagnostics page / 本地诊断页面
- `/troubleshooting`: local troubleshooting guide / 本地故障排查指南
- `/docs`: FastAPI documentation / FastAPI 文档
- `/api`: API overview / API 概览

## API

- `GET /api`
- `GET /api/v1/health`
- `GET /api/v1/commands`
- `GET /api/v1/discovery/summary`
- `GET /api/v1/discovery/projects`
- `GET /api/v1/discovery/doc-types`
- `GET /api/v1/discovery/categories`
- `GET /api/v1/discovery/tags`
- `GET /api/v1/search`
- `POST /api/v1/ask`
- `GET /api/v1/diagnostics`

## Safety Boundary / 安全边界

- The API binds to `127.0.0.1` by default.
- The Web/API service is not intended for public-network exposure.
- Web pages do not use external CDN assets.
- Web pages do not load public-network resources.
- Web pages do not execute `update_index`, `rebuild`, `backup`, or `add_note`.
- Search does not write to the knowledge base.
- Ask does not save QA logs by default.
- `save_log=true` is currently rejected.
- API responses do not return local absolute paths.
- API responses do not return raw context.
- API responses do not return prompts.
- API responses do not return raw payloads.
- API responses do not return full Markdown `text`.
- API responses do not return source paths.
- Error prompts do not display stack traces or raw exception text.

中文：

- API 默认绑定到 `127.0.0.1`。
- Web/API 服务不用于公网暴露。
- Web 页面不使用外部 CDN 资源。
- Web 页面不加载公网资源。
- Web 页面不会执行 `update_index`、`rebuild`、`backup` 或 `add_note`。
- Search 不会写入知识库。
- Ask 默认不会保存 QA 日志。
- 当前会拒绝 `save_log=true`。
- API 响应不会返回本地绝对路径。
- API 响应不会返回原始上下文。
- API 响应不会返回 prompts。
- API 响应不会返回原始 payloads。
- API 响应不会返回完整的 Markdown `text`。
- API 响应不会返回 source paths。
- 错误提示不会显示堆栈跟踪或原始异常文本。

## Notes / 备注

Search and Ask depend on local Qdrant and the current index state. Ask and vector/hybrid retrieval can also depend on local Ollama.

Search 和 Ask 依赖本地 Qdrant 以及当前索引状态。Ask 和 vector/hybrid 检索也可能依赖本地 Ollama。