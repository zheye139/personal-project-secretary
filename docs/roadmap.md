---
title: Roadmap / 路线图
category: summary
project: personal-project-secretary
doc_type: roadmap
tags: [roadmap, bilingual, RAG, WebUI, automation]
---

# Roadmap / 路线图

This project is designed as a local-first personal project secretary and knowledge base manager.  
本项目定位为本地优先的个人项目秘书与知识库管理员系统。

## Short Term / 短期

Complete the local command-line toolbox.  
继续完善本地命令行工具箱。

Goals / 目标：

- stable Markdown ingestion / 稳定 Markdown 入库
- metadata validation / 元数据校验
- Qdrant rebuild / Qdrant 索引重建
- project templates / 项目模板
- backup and restore / 备份与恢复
- project reports / 项目报告
- daily and weekly reports / 日报与周报

## Mid Term / 中期

Build a local Web UI inspired by Open WebUI and AnythingLLM.  
参考 Open WebUI / AnythingLLM 构建本地 Web UI。

Goals / 目标：

- system dashboard / 系统仪表盘
- knowledge-base chat page / 知识库问答页面
- document browser / 文档浏览页面
- report generation page / 报告生成页面
- maintenance buttons / 维护操作按钮

## Long Term / 长期

Add an automation layer inspired by Khoj, OpenAgent, GAIA, and OpenClaw.  
参考 Khoj / OpenAgent / GAIA / OpenClaw 增加自动化执行层。

Goals / 目标：

- automatic inbox import / 自动导入 Inbox
- automatic indexing / 自动更新索引
- automatic daily and weekly reports / 自动生成日报周报
- automatic backup / 自动备份
- safe execution policies / 安全执行策略
- agent integration / Agent 接入

## Milestone Plan / 里程碑计划

### M1: Local Knowledge Base Manager / 本地知识库管理员

- Markdown knowledge base / Markdown 知识库
- Frontmatter metadata / Frontmatter 元数据
- Qdrant indexing / Qdrant 入库
- RAG Q&A / RAG 问答
- reports / 报告
- backup / 备份
- restore docs / 恢复文档

### M2: Personal Secretary Layer / 个人秘书能力层

- next action extraction / 下一步任务提取
- project brief / 项目简报
- multi-project status / 多项目状态汇总
- priority advisor / 优先级建议
- review assistant / 项目复盘助手

### M3: Web UI / Web 界面

- local FastAPI service / 本地 FastAPI 服务
- dashboard / 仪表盘
- chat UI / 问答界面
- document management / 文档管理
- report generation / 报告生成

### M4: Automation Layer / 自动化执行层

- daily workflow / 每日工作流
- weekly workflow / 每周工作流
- OpenClaw integration / OpenClaw 接入
- safe executor / 安全执行器