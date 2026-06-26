# Quick Start / 快速开始

This guide helps you run **Personal Project Secretary + Knowledge Base Manager** with the example knowledge base.

本文档用于帮助你使用示例知识库快速运行“个人项目秘书 + 知识库管理员系统”。

---

## 1. Repository and Knowledge Base / 代码仓库与知识库目录

Keep the code repository and the private knowledge base separate.

请将代码仓库和私人知识库目录分开管理。

```text
Code repository / 代码仓库：
<your-repo-path>\personal-project-secretary

Knowledge base / 知识库：
<your-knowledge-root>
```

Windows example / Windows 示例：

```text
<your-repo-path>\personal-project-secretary
<your-knowledge-root>
```

---

## 2. Copy Example Knowledge Base / 复制示例知识库

```powershell
Copy-Item .\examples\Personal_Knowledge_Base_Template <your-knowledge-root> -Recurse
```

You can choose another location, but `KNOWLEDGE_ROOT` must point to that location.

你可以选择其他目录，但 `KNOWLEDGE_ROOT` 必须指向该知识库目录。

---

## 3. Install Ollama Models / 安装 Ollama 模型

```powershell
ollama pull qwen3:8b
ollama pull bge-m3
```

Check installed models / 查看已安装模型：

```powershell
ollama list
```

---

## 4. Start Qdrant / 启动 Qdrant

```powershell
docker run -d --name pkb-qdrant -p 6333:6333 -v <your-knowledge-root>/99_System/qdrant_storage:/qdrant/storage qdrant/qdrant
```

If the container already exists / 如果容器已存在：

```powershell
docker start pkb-qdrant
```

Check Qdrant / 检查 Qdrant：

```powershell
curl.exe http://127.0.0.1:6333/collections
```

---

## 5. Create Python Environment / 创建 Python 虚拟环境

```powershell
cd <your-repo-path>\personal-project-secretary\rag_mvp
py -3.11 -m venv .venv
.\.venv\Scripts\activate
pip install -r ..\requirements.txt
```

---

## 6. Create Local Config / 创建本地配置

```powershell
Copy-Item .\config.example.py .\config.py
```

Edit `config.py` / 编辑 `config.py`：

```python
KNOWLEDGE_ROOT = Path(r"<your-knowledge-root>")
```

---

## 7. Check Environment / 检查环境

```powershell
python check_env.py
```

---

## 8. Index Documents / 文档入库

```powershell
python update_index.py
```

---

## 9. Ask a Question / 提问测试

```powershell
python ask.py --project Demo_Project "What is the current status of the demo project?"
```

中文也可以：

```powershell
python ask.py --project Demo_Project "Demo 项目当前状态是什么？"
```

---

## 10. Test M2 Personal Secretary Layer / 测试 M2 个人秘书能力

```powershell
python next_action.py --project Demo_Project
python project_brief.py --project Demo_Project
python multi_project_status.py
python priority_advisor.py
python review_assistant.py --project Demo_Project
python secretary_report.py
```

Run a milestone closeout check / 执行阶段封版检查：

```powershell
python milestone_closeout.py --milestone M2
```

After generating reports, index them again / 生成报告后重新入库：

```powershell
python update_index.py
```


---

## 11. Test M3 Index and Retrieval Layer / 测试 M3 索引与检索能力

Run incremental index / 执行增量索引：

```powershell
python update_index.py
```

Run keyword and hybrid search / 执行关键词检索和混合检索：

```powershell
python search_docs.py --mode keyword "update_index.py" --show-text
python search_docs.py --mode hybrid "M3 incremental indexing" --show-text
```

Ask with hybrid retrieval / 使用混合检索问答：

```powershell
python ask.py --search-mode hybrid "What did M3 improve?"
```

Run retrieval evaluation / 执行检索评估：

```powershell
python retrieval_eval.py --mode all
```

Close out M3 / M3 阶段封版：

```powershell
python milestone_closeout.py --milestone M3
```

---

## 12. M4 Local Web/API Quick Start / M4 本地 Web/API 快速开始

Start the local API/Web service / 启动本地 API/Web 服务:

```powershell
cd rag_mvp
.\run_api.ps1
```

Open in a browser / 在浏览器中打开:

```text
http://127.0.0.1:8000/
http://127.0.0.1:8000/search
http://127.0.0.1:8000/ask
http://127.0.0.1:8000/diagnostics
http://127.0.0.1:8000/troubleshooting
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/api
```

Page usage / 页面使用说明:

- `/search` searches the local knowledge base.
- `/ask` runs local RAG question answering.
- `/diagnostics` checks API, Qdrant, Ollama, Discovery, and Commands status.
- `/troubleshooting` provides local troubleshooting guidance.
- `/docs` opens FastAPI automatic documentation.
- `/api` returns the API overview JSON.

中文：

- `/search` 用于搜索本地知识库。
- `/ask` 用于运行本地 RAG 问答。
- `/diagnostics` 用于检查 API、Qdrant、Ollama、Discovery 和 Commands 状态。
- `/troubleshooting` 提供本地故障排查指导。
- `/docs` 打开 FastAPI 自动文档。
- `/api` 返回 API 概览 JSON。

Safety notes / 安全说明:

- Ask does not save QA logs by default.
- `save_log=true` is currently rejected by the Ask API.
- Web pages do not execute `update_index`, `rebuild`, `backup`, or `add_note`.
- The service binds to `127.0.0.1` by default and is not intended for public-network exposure.

中文：

- Ask 默认不会保存 QA 日志。
- 当前 Ask API 会拒绝 `save_log=true`。
- Web 页面不会执行 `update_index`、`rebuild`、`backup` 或 `add_note`。
- 服务默认绑定到 `127.0.0.1`，并且不用于公网暴露。