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
D:\Projects\personal-project-secretary
D:\Personal_Knowledge_Base
```

---

## 2. Copy Example Knowledge Base / 复制示例知识库

```powershell
Copy-Item .\examples\Personal_Knowledge_Base_Template D:\Personal_Knowledge_Base -Recurse
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
docker run -d --name pkb-qdrant -p 6333:6333 -v D:/Personal_Knowledge_Base/99_System/qdrant_storage:/qdrant/storage qdrant/qdrant
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
KNOWLEDGE_ROOT = Path(r"D:\Personal_Knowledge_Base")
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
