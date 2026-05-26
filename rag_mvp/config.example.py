from pathlib import Path


# =========================
# Knowledge base root
# =========================
# This path should point to your own local Markdown knowledge base directory,
# not to the GitHub code repository directory.
#
# Recommended default:
#   Path.home() / "Personal_Knowledge_Base"
#
# Example alternatives:
#   Path(r"D:\Personal_Knowledge_Base")
#   Path("/home/user/Personal_Knowledge_Base")

KNOWLEDGE_ROOT = Path.home() / "Personal_Knowledge_Base"


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
NEXT_ACTION_DIR = KNOWLEDGE_ROOT / "05_Summaries" / "next_actions"
PROJECT_BRIEF_DIR = KNOWLEDGE_ROOT / "05_Summaries" / "project_briefs"
MULTI_PROJECT_STATUS_DIR = KNOWLEDGE_ROOT / "05_Summaries" / "multi_project_status"
PRIORITY_ADVICE_DIR = KNOWLEDGE_ROOT / "05_Summaries" / "priority_advice"
REVIEW_REPORT_DIR = KNOWLEDGE_ROOT / "05_Summaries" / "review_reports"
SECRETARY_REPORT_DIR = KNOWLEDGE_ROOT / "05_Summaries" / "secretary_reports"
PROJECT_EXPORT_DIR = KNOWLEDGE_ROOT / "05_Summaries" / "project_exports"
MILESTONE_CLOSEOUT_DIR = KNOWLEDGE_ROOT / "05_Summaries" / "milestone_closeouts"
MILESTONE_REPORT_DIR = KNOWLEDGE_ROOT / "05_Summaries" / "milestone_reports"

BACKUP_DIR = KNOWLEDGE_ROOT / "99_System" / "backups"
