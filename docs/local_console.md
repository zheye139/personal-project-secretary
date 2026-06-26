---
title: Local Console / 本地控制台
category: documentation
doc_type: local_console
version: v0.4.0-local-console-webapi
---

# Local Console / 本地控制台

The local console is the terminal menu layer for the Personal Project Secretary project.

本地控制台是 Personal Project Secretary 项目的终端菜单层。

## File / 文件

```text
rag_mvp/launcher.py
```

## Start Command / 启动命令

```powershell
cd rag_mvp
.\.venv\Scripts\python.exe launcher.py
```

## Main Features / 主要功能

The launcher provides a guided menu for common local workflows / launcher 为常见的本地工作流提供引导式菜单:

- system status
- ask
- search
- add note
- update index
- reports
- secretary report
- retrieval eval
- backup
- advanced maintenance
- start local API server

## Safety Notes / 安全说明

- Dangerous operations require confirmation.
- `launcher.py` is a menu entry point; it calls existing scripts instead of replacing their logic.
- Windows PowerShell is recommended.
- Some third-party terminals may have Chinese input issues. If input behaves incorrectly, use Windows Terminal or PowerShell directly.
- Keep the private knowledge base outside the GitHub repository.

中文：

- 危险操作需要确认。
- `launcher.py` 是一个菜单入口；它会调用已有脚本，而不是替换这些脚本的逻辑。
- 推荐使用 Windows PowerShell。
- 某些第三方终端可能存在中文输入问题。如果输入行为异常，请直接使用 Windows Terminal 或 PowerShell。
- 请将私有知识库保留在 GitHub 仓库之外。