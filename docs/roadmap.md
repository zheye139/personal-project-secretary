---
title: Roadmap / 路线图
category: summary
project: personal-project-secretary
doc_type: roadmap
tags: [roadmap, bilingual, RAG, indexing, retrieval, personal-secretary, automation]
---

# Roadmap / 路线图

This project is designed as a local-first personal project secretary and knowledge base manager.

本项目定位为本地优先的个人项目秘书与知识库管理员系统。

---

## Completed / 已完成

### M1: Local Knowledge Base Manager / 本地知识库管理员

- Markdown knowledge base / Markdown 知识库
- Frontmatter metadata / Frontmatter 元数据
- Qdrant indexing / Qdrant 入库
- RAG Q&A / RAG 问答
- reports / 报告
- backup / 备份
- restore docs / 恢复文档
- validation and repair tools / 校验与修复工具

### M2: Personal Secretary Layer / 个人秘书能力层

- next action extraction / 下一步任务提取
- project brief / 项目简报
- multi-project status / 多项目状态汇总
- priority advisor / 优先级建议
- review assistant / 项目复盘助手
- secretary report / 个人秘书汇报
- milestone closeout / 阶段封版

### M3: Index and Retrieval Optimization / 索引与检索能力优化

- `index_manifest.json` and manifest utilities / manifest 状态记录与工具函数
- incremental indexing / 增量索引
- single-file update / 单文件更新
- project-level update / 项目级更新
- full rebuild entry / 全量重建入口
- keyword search / 关键词检索
- hybrid search / 混合检索
- `ask.py` retrieval mode selection / 问答检索模式选择
- retrieval evaluation set and script / 检索评估测试集与评估脚本

---

## Later Direction / 后续方向

### M5: Local API and Web UI / 本地 API 与 Web UI

Possible later stage after the command-line workflow is stable.

在命令行工作流稳定后，可作为后续阶段。

Goals / 目标：

- local FastAPI service / 本地 FastAPI 服务
- dashboard / 仪表盘
- chat UI / 问答界面
- document browser / 文档浏览页面
- report generation page / 报告生成页面
- maintenance buttons / 维护操作按钮

### M6: Automation Layer / 自动化执行层

Goals / 目标：

- automatic inbox import / 自动导入 Inbox
- automatic indexing / 自动更新索引
- automatic daily and weekly reports / 自动生成日报周报
- automatic backup / 自动备份
- safe execution policies / 安全执行策略
- OpenClaw or agent integration / OpenClaw 或 Agent 接入
