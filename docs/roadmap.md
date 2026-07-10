---
title: Roadmap / 路线图
category: summary
project: personal-project-secretary
doc_type: roadmap
tags: [roadmap, bilingual, RAG, indexing, retrieval, personal-secretary, automation]
---

# Roadmap / 路线图

Knowledge Operating System is a local-first personal project secretary and knowledge-management system.

Knowledge Operating System 是一个本地优先的个人项目秘书与知识管理系统。

---

## Completed / 已完成

### M1: Local Knowledge Base Infrastructure / 本地知识库基础设施

- Markdown knowledge base
- Frontmatter metadata
- Qdrant indexing
- RAG Q&A
- reports
- backup and restore
- validation and repair tools

### M2: Personal Secretary Analysis Layer / 个人秘书分析层

- next action extraction
- project brief
- multi-project status
- priority advisor
- review assistant
- secretary report
- milestone closeout

### M3: Index and Retrieval Optimization / 索引与检索优化

- index manifest
- incremental indexing
- single-file update
- project-level update
- full rebuild
- keyword search
- hybrid search
- retrieval evaluation

### M4: Local Console, API, and Web Interface / 本地控制台、API 与 Web

- command registry
- local launcher
- project discovery
- FastAPI API
- local Web pages
- diagnostics
- troubleshooting pages
- local-first safety boundary

### M5: Vector Store Configuration and Cross-PC Deployment Validation / Vector Store 配置层与跨 PC 部署验证

- `vector_store_config.py`
- Qdrant URL configuration
- Qdrant timeout configuration
- collection configuration
- environment-variable override
- local Qdrant
- LAN / remote Qdrant
- development-PC validation
- VM-to-host Qdrant validation
- Search validation
- Ask validation
- local Web/API validation
- new-PC deployment documentation

---

## Current Boundary / 当前边界

M5 currently supports Qdrant as the Vector Store backend.

当前 M5 仍只实现 Qdrant 后端。

M6-M10 are future directions and are not implemented in the M5 release.