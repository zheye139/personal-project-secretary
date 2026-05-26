from pathlib import Path


# =========================
# Knowledge base root
# =========================
# This path should point to your own local Markdown knowledge base directory,
# NOT the GitHub code repository directory.
#
# Recommended separation:
#   Code repository:
#       D:\Projects\personal-project-secretary
#   Knowledge base:
#       D:\Personal_Knowledge_Base
#
# Windows example:
#   Path(r"D:\Personal_Knowledge_Base")
#
# Linux/macOS example:
#   Path("/home/user/Personal_Knowledge_Base")

KNOWLEDGE_ROOT = Path(r"D:\Personal_Knowledge_Base")


# =========================
# Ollama config
# =========================

OLLAMA_URL = "http://127.0.0.1:11434"

CHAT_MODEL = "qwen3:8b"
EMBED_MODEL = "bge-m3:latest"


# =========================
# Qdrant config
# =========================

QDRANT_URL = "http://127.0.0.1:6333"

# Recommended collection name.
# You may change it, but if you change it after indexing,
# run ingest.py or rebuild_index.py again to create and populate the new collection.
COLLECTION_NAME = "personal_knowledge_base"


# =========================
# Chunking and search config
# =========================

CHUNK_MAX_CHARS = 800
SEARCH_LIMIT = 5


# =========================
# Output directories
# =========================

QA_LOG_DIR = KNOWLEDGE_ROOT / "05_Summaries" / "qa_logs"
QA_LOG_ARCHIVE_DIR = KNOWLEDGE_ROOT / "05_Summaries" / "qa_logs_archived"

PROJECT_REPORT_DIR = KNOWLEDGE_ROOT / "05_Summaries" / "project_reports"
TIME_REPORT_DIR = KNOWLEDGE_ROOT / "05_Summaries" / "time_reports"

BACKUP_DIR = KNOWLEDGE_ROOT / "99_System" / "backups"

# =========================
# Output directories - M2
# =========================

PROJECT_EXPORT_DIR = KNOWLEDGE_ROOT / "05_Summaries" / "project_exports"

MILESTONE_REPORT_DIR = KNOWLEDGE_ROOT / "05_Summaries" / "milestone_reports"

NEXT_ACTION_DIR = KNOWLEDGE_ROOT / "05_Summaries" / "next_actions"

PROJECT_BRIEF_DIR = KNOWLEDGE_ROOT / "05_Summaries" / "project_briefs"

MULTI_PROJECT_STATUS_DIR = KNOWLEDGE_ROOT / "05_Summaries" / "multi_project_status"

REVIEW_REPORT_DIR = KNOWLEDGE_ROOT / "05_Summaries" / "review_reports"

SECRETARY_REPORT_DIR = KNOWLEDGE_ROOT / "05_Summaries" / "secretary_reports"

MILESTONE_REPORT_DIR = KNOWLEDGE_ROOT / "05_Summaries" / "milestone_reports"