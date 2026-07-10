import os
from pathlib import Path


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except Exception:
        return default


# =========================
# Knowledge base root
# =========================

KNOWLEDGE_ROOT = Path(
    os.environ.get(
        "PKB_KNOWLEDGE_ROOT",
        str(Path.home() / "Personal_Knowledge_Base"),
    )
)


# =========================
# Ollama configuration
# =========================

OLLAMA_URL = os.environ.get(
    "PKB_OLLAMA_URL",
    "http://127.0.0.1:11434",
).strip()

CHAT_MODEL = os.environ.get(
    "PKB_CHAT_MODEL",
    "qwen3:8b",
).strip()

EMBED_MODEL = os.environ.get(
    "PKB_EMBED_MODEL",
    "bge-m3:latest",
).strip()


# =========================
# Qdrant / Vector Store configuration
# =========================

QDRANT_URL = os.environ.get(
    "PKB_QDRANT_URL",
    "http://127.0.0.1:6333",
).strip()

QDRANT_TIMEOUT = _env_int(
    "PKB_QDRANT_TIMEOUT",
    120,
)

COLLECTION_NAME = os.environ.get(
    "PKB_QDRANT_COLLECTION",
    "personal_knowledge_base",
).strip()


# =========================
# Chunking and retrieval
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

PROJECT_EXPORT_DIR = KNOWLEDGE_ROOT / "05_Summaries" / "project_exports"
MILESTONE_REPORT_DIR = KNOWLEDGE_ROOT / "05_Summaries" / "milestone_reports"

NEXT_ACTION_DIR = KNOWLEDGE_ROOT / "05_Summaries" / "next_actions"
PROJECT_BRIEF_DIR = KNOWLEDGE_ROOT / "05_Summaries" / "project_briefs"
MULTI_PROJECT_STATUS_DIR = (
    KNOWLEDGE_ROOT / "05_Summaries" / "multi_project_status"
)
PRIORITY_ADVICE_DIR = (
    KNOWLEDGE_ROOT / "05_Summaries" / "priority_advice"
)
REVIEW_REPORT_DIR = KNOWLEDGE_ROOT / "05_Summaries" / "review_reports"
SECRETARY_REPORT_DIR = (
    KNOWLEDGE_ROOT / "05_Summaries" / "secretary_reports"
)

BACKUP_DIR = KNOWLEDGE_ROOT / "99_System" / "backups"

INDEX_MANIFEST_PATH = (
    KNOWLEDGE_ROOT / "99_System" / "index_manifest.json"
)

EVAL_DIR = KNOWLEDGE_ROOT / "99_System" / "eval"
RETRIEVAL_EVAL_PATH = EVAL_DIR / "retrieval_eval.json"
RETRIEVAL_EVAL_REPORT_DIR = (
    KNOWLEDGE_ROOT
    / "05_Summaries"
    / "retrieval_eval_reports"
)
