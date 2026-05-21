# Examples

This directory contains a minimal example knowledge base template for testing **Personal Project Secretary + Knowledge Base Manager**.

It is safe to publish because it only contains demo data and does not include any private project information.

---

## Directory Structure

```text
examples/
├─ README.md
└─ Personal_Knowledge_Base_Template/
   ├─ 00_Inbox/
   ├─ 01_Projects/
   │  └─ Demo_Project/
   │     ├─ project_overview.md
   │     ├─ progress_log.md
   │     ├─ issues.md
   │     ├─ decisions.md
   │     ├─ next_steps.md
   │     └─ notes/
   │        └─ example_note.md
   ├─ 02_Knowledge/
   │  └─ demo_knowledge_note.md
   ├─ 03_Decisions/
   ├─ 04_Problems/
   ├─ 05_Summaries/
   ├─ 06_Attachments/
   └─ 99_System/
      └─ docs/
```

---

## Purpose

This example knowledge base is provided so that new users can test the system without using private data.

You can use it to test:

1. Markdown indexing.
2. Frontmatter metadata parsing.
3. Qdrant vector storage.
4. Ollama-based embedding.
5. RAG question answering.
6. Project filtering.
7. Document type filtering.
8. Category and tag filtering.

---

## How to Use

### 1. Copy the Example Knowledge Base

Copy the template to your own local path.

Example:

```powershell
Copy-Item .\examples\Personal_Knowledge_Base_Template D:\Personal_Knowledge_Base -Recurse
```

You can also choose another location, for example:

```powershell
Copy-Item .\examples\Personal_Knowledge_Base_Template D:\My_Knowledge_Base -Recurse
```

---

### 2. Configure `KNOWLEDGE_ROOT`

Go to the `rag_mvp` directory:

```powershell
cd .\rag_mvp
```

Copy the example configuration file:

```powershell
Copy-Item .\config.example.py .\config.py
```

Edit `config.py` and set `KNOWLEDGE_ROOT` to the copied knowledge base path.

Example:

```python
KNOWLEDGE_ROOT = Path(r"D:\Personal_Knowledge_Base")
```

If you copied it to another location, use that path instead:

```python
KNOWLEDGE_ROOT = Path(r"D:\My_Knowledge_Base")
```

---

### 3. Start Required Services

Make sure Ollama is running and the required models are installed:

```powershell
ollama pull qwen3:8b
ollama pull bge-m3
```

Start Qdrant with Docker:

```powershell
docker run -d --name pkb-qdrant -p 6333:6333 -v D:/Personal_Knowledge_Base/99_System/qdrant_storage:/qdrant/storage qdrant/qdrant
```

If the container already exists, run:

```powershell
docker start pkb-qdrant
```

---

### 4. Create and Activate Python Environment

From the `rag_mvp` directory:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\activate
pip install -r ..\requirements.txt
```

---

### 5. Check the Environment

```powershell
python check_env.py
```

Expected result:

```text
Ollama is accessible.
Qdrant is accessible.
The required models are available.
```

---

### 6. Index the Example Knowledge Base

```powershell
python update_index.py
```

This command will:

1. Check the environment.
2. Index Markdown files.
3. List indexed documents.

---

### 7. Ask a Question

Example:

```powershell
python ask.py --project Demo_Project "What is the current status of the demo project?"
```

You can also ask in Chinese:

```powershell
python ask.py --project Demo_Project "Demo 项目当前进展如何？"
```

---

## Useful Test Commands

Search indexed chunks without calling the chat model:

```powershell
python search_docs.py --project Demo_Project "project status" --show-text
```

Ask about the demo project:

```powershell
python ask.py --project Demo_Project "What has been completed?"
```

Ask about next steps:

```powershell
python ask.py --project Demo_Project --doc-type next_steps "What should be done next?"
```

Ask about issues:

```powershell
python ask.py --project Demo_Project --doc-type issues "What issue was recorded?"
```

Ask about the local RAG knowledge note:

```powershell
python ask.py --category knowledge "What is local RAG?"
```

Generate a project report:

```powershell
python project_report.py --project Demo_Project
```

Generate a weekly report:

```powershell
python time_report.py --project Demo_Project --mode weekly
```

---

## Example Frontmatter

Each Markdown file should include Frontmatter metadata.

Example:

```markdown
---
title: Demo Project Overview
created: 2026-01-01
category: project
project: Demo_Project
doc_type: project_overview
tags: [demo, example, project]
---
```

Important fields:

| Field | Description |
|---|---|
| `title` | Document title |
| `created` | Creation time |
| `category` | Knowledge category, such as `project`, `knowledge`, `problem`, `summary` |
| `project` | Project name |
| `doc_type` | Document type, such as `progress_log`, `issues`, `decision`, `note` |
| `tags` | Tags used for filtering and search |

---

## Notes

1. The example knowledge base is for testing only.
2. Do not put private information in this folder if you plan to publish it.
3. Your real knowledge base should be stored outside the GitHub repository.
4. `KNOWLEDGE_ROOT` should point to your real or example knowledge base directory.
5. Qdrant data can be rebuilt from Markdown files.

---

## Recommended Next Step

After confirming the example works, create your own private knowledge base directory and update `KNOWLEDGE_ROOT` in `config.py`.

Recommended structure:

```text
Your_Knowledge_Base/
├─ 00_Inbox/
├─ 01_Projects/
├─ 02_Knowledge/
├─ 03_Decisions/
├─ 04_Problems/
├─ 05_Summaries/
├─ 06_Attachments/
└─ 99_System/
```

Then run:

```powershell
python update_index.py
python status.py
```