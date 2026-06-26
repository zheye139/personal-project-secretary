import re
from pathlib import Path
from typing import Any, Callable

import requests
from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pydantic import BaseModel, Field

import ask
import command_registry
import project_discovery
import search_docs


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
API_VERSION = "v1"
API_PREFIX = f"/api/{API_VERSION}"
SERVICE_NAME = "personal-project-secretary-api"
WEB_INDEX_PATH = Path(__file__).resolve().parent / "web" / "index.html"
WEB_SEARCH_PATH = Path(__file__).resolve().parent / "web" / "search.html"
WEB_ASK_PATH = Path(__file__).resolve().parent / "web" / "ask.html"
WEB_DIAGNOSTICS_PATH = Path(__file__).resolve().parent / "web" / "diagnostics.html"
WEB_TROUBLESHOOTING_PATH = Path(__file__).resolve().parent / "web" / "troubleshooting.html"

SENSITIVE_KEYS = {
    "manifest_path",
    "knowledge_root",
    "source",
    "point_id",
    "payload",
    "text",
    "prompt",
    "raw_context",
    "contexts",
}
WINDOWS_ABSOLUTE_PATH_PATTERN = re.compile(r"[A-Za-z]:[\\/]")


app = FastAPI(
    title="Personal Project Secretary API",
    version=API_VERSION,
    description="Local-only read-only API for Personal Project Secretary metadata.",
)


class AskRequest(BaseModel):
    question: str = Field(...)
    search_mode: str = "hybrid"
    project: str | None = None
    doc_type: str | None = None
    category: str | None = None
    tag: str | None = None
    limit: int = Field(default=5, ge=1, le=10)
    save_log: bool = False


def service_status() -> dict[str, str]:
    return {
        "status": "ok",
        "service": SERVICE_NAME,
        "api_version": API_VERSION,
    }


def api_overview() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": SERVICE_NAME,
        "api_version": API_VERSION,
        "docs_url": "/docs",
        "health_url": f"{API_PREFIX}/health",
        "commands_url": f"{API_PREFIX}/commands",
        "search_url": f"{API_PREFIX}/search",
        "ask_url": f"{API_PREFIX}/ask",
        "diagnostics_url": f"{API_PREFIX}/diagnostics",
        "discovery_urls": {
            "summary": f"{API_PREFIX}/discovery/summary",
            "projects": f"{API_PREFIX}/discovery/projects",
            "doc_types": f"{API_PREFIX}/discovery/doc-types",
            "categories": f"{API_PREFIX}/discovery/categories",
            "tags": f"{API_PREFIX}/discovery/tags",
        },
    }


def safe_error_response(
    code: str,
    message: str,
    status_code: int = 500,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "error",
            "code": code,
            "message": message,
        },
    )


def sanitize_for_api(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: sanitize_for_api(item)
            for key, item in value.items()
            if key not in SENSITIVE_KEYS
        }

    if isinstance(value, list):
        return [sanitize_for_api(item) for item in value]

    if isinstance(value, tuple):
        return [sanitize_for_api(item) for item in value]

    if isinstance(value, str) and WINDOWS_ABSOLUTE_PATH_PATTERN.search(value):
        return ""

    return value


def sanitize_argument(argument: dict[str, Any]) -> dict[str, Any]:
    allowed_keys = {
        "name",
        "flag",
        "type",
        "required",
        "default",
        "choices",
        "description",
        "positional",
        "multiple",
        "example",
        "dangerous",
        "requires_confirmation",
    }
    return sanitize_for_api(
        {
            key: value
            for key, value in argument.items()
            if key in allowed_keys
        }
    )


def sanitize_command(command: dict[str, Any]) -> dict[str, Any]:
    return sanitize_for_api(
        {
            "id": command.get("id", ""),
            "title": command.get("title", ""),
            "description": command.get("description", ""),
            "category": command.get("category", ""),
            "arguments": [
                sanitize_argument(argument)
                for argument in command.get("arguments", [])
                if isinstance(argument, dict)
            ],
            "dangerous": bool(command.get("dangerous", False)),
            "requires_confirmation": bool(command.get("requires_confirmation", False)),
            "tags": command.get("tags", []),
        }
    )


def load_manifest_for_api() -> dict:
    return project_discovery.load_manifest()


def discovery_response(builder: Callable[[dict], Any]) -> Any:
    try:
        manifest = load_manifest_for_api()
        return sanitize_for_api(builder(manifest))
    except Exception:
        return safe_error_response(
            code="manifest_unavailable",
            message="Discovery manifest is unavailable.",
            status_code=503,
        )


def diagnostic_ok(message: str, **details: Any) -> dict[str, Any]:
    return sanitize_for_api(
        {
            "status": "ok",
            "message": message,
            **details,
        }
    )


def diagnostic_error() -> dict[str, str]:
    return {
        "status": "error",
        "message": "Service is not available",
    }


def check_api_status() -> dict[str, str]:
    return diagnostic_ok("API is running")


def check_commands_status() -> dict[str, Any]:
    try:
        commands = command_registry.list_commands()
        return diagnostic_ok(
            "Command registry is readable",
            count=len(commands),
        )
    except Exception:
        return diagnostic_error()


def check_discovery_status() -> dict[str, Any]:
    try:
        manifest = load_manifest_for_api()
        summary = project_discovery.build_summary(manifest)
        return diagnostic_ok(
            "Discovery manifest is readable",
            project_count=int(summary.get("project_count", 0) or 0),
            file_count=int(summary.get("total_files", 0) or 0),
        )
    except Exception:
        return diagnostic_error()


def check_qdrant_status() -> dict[str, str]:
    client = None
    try:
        client = search_docs.get_qdrant_client()
        client.get_collections()
        return diagnostic_ok("Qdrant is reachable")
    except Exception:
        return diagnostic_error()
    finally:
        close = getattr(client, "close", None)
        if callable(close):
            close()


def check_ollama_status() -> dict[str, str]:
    try:
        response = requests.get(
            f"{search_docs.OLLAMA_URL}/api/tags",
            timeout=3,
        )
        if response.status_code == 200:
            return diagnostic_ok("Ollama is reachable")
        return diagnostic_error()
    except Exception:
        return diagnostic_error()


def build_diagnostics() -> dict[str, Any]:
    checks = {
        "api": check_api_status(),
        "commands": check_commands_status(),
        "discovery": check_discovery_status(),
        "qdrant": check_qdrant_status(),
        "ollama": check_ollama_status(),
    }
    overall_status = (
        "ok"
        if all(item.get("status") == "ok" for item in checks.values())
        else "error"
    )

    return sanitize_for_api(
        {
            "status": overall_status,
            "service": SERVICE_NAME,
            "api_version": API_VERSION,
            "checks": checks,
        }
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return safe_error_response(
        code="internal_error",
        message="Internal server error.",
        status_code=500,
    )


@app.get("/", response_class=HTMLResponse)
def read_root() -> Any:
    try:
        content = WEB_INDEX_PATH.read_text(encoding="utf-8")
    except Exception:
        return safe_error_response(
            code="homepage_unavailable",
            message="Local homepage is unavailable.",
            status_code=500,
        )

    return HTMLResponse(content=content)


@app.get("/search", response_class=HTMLResponse)
def read_search_page() -> Any:
    try:
        content = WEB_SEARCH_PATH.read_text(encoding="utf-8")
    except Exception:
        return safe_error_response(
            code="search_page_unavailable",
            message="Local search page is unavailable.",
            status_code=500,
        )

    return HTMLResponse(content=content)


@app.get("/ask", response_class=HTMLResponse)
def read_ask_page() -> Any:
    try:
        content = WEB_ASK_PATH.read_text(encoding="utf-8")
    except Exception:
        return safe_error_response(
            code="ask_page_unavailable",
            message="Local ask page is unavailable.",
            status_code=500,
        )

    return HTMLResponse(content=content)


@app.get("/diagnostics", response_class=HTMLResponse)
def read_diagnostics_page() -> Any:
    try:
        content = WEB_DIAGNOSTICS_PATH.read_text(encoding="utf-8")
    except Exception:
        return safe_error_response(
            code="diagnostics_page_unavailable",
            message="Local diagnostics page is unavailable.",
            status_code=500,
        )

    return HTMLResponse(content=content)


@app.get("/troubleshooting", response_class=HTMLResponse)
def read_troubleshooting_page() -> Any:
    try:
        content = WEB_TROUBLESHOOTING_PATH.read_text(encoding="utf-8")
    except Exception:
        return safe_error_response(
            code="troubleshooting_page_unavailable",
            message="Local troubleshooting page is unavailable.",
            status_code=500,
        )

    return HTMLResponse(content=content)


@app.get("/api")
def read_api_root() -> dict[str, Any]:
    return api_overview()


@app.get("/favicon.ico", include_in_schema=False)
def read_favicon() -> Response:
    return Response(status_code=204)


@app.get(API_PREFIX)
def read_api_info() -> dict[str, Any]:
    return api_overview()


@app.get(f"{API_PREFIX}/health")
def read_health() -> dict[str, str]:
    return service_status()


@app.get(f"{API_PREFIX}/diagnostics")
def read_diagnostics() -> dict[str, Any]:
    return build_diagnostics()


@app.get(f"{API_PREFIX}/commands")
def read_commands() -> dict[str, Any]:
    commands = [
        sanitize_command(command)
        for command in command_registry.list_commands()
    ]
    return sanitize_for_api(
        {
            "status": "ok",
            "commands": commands,
            "categories": command_registry.list_categories(),
        }
    )


@app.get(f"{API_PREFIX}/search")
def read_search(
    q: str = Query(...),
    mode: str = Query(default="keyword"),
    project: str | None = Query(default=None),
    doc_type: str | None = Query(default=None),
    category: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    limit: int = Query(default=5, ge=1, le=20),
    show_text: bool = Query(default=False),
) -> Any:
    try:
        return sanitize_for_api(
            search_docs.search_documents(
                query=q,
                mode=mode,
                project=project,
                doc_type=doc_type,
                category=category,
                tag=tag,
                limit=limit,
                show_text=show_text,
            )
        )
    except ValueError:
        return safe_error_response(
            code="invalid_search_request",
            message="Search request is invalid.",
            status_code=400,
        )
    except Exception:
        return safe_error_response(
            code="search_unavailable",
            message="Search service is unavailable.",
            status_code=503,
        )


@app.post(f"{API_PREFIX}/ask")
def post_ask(request: AskRequest) -> Any:
    try:
        return sanitize_for_api(
            ask.ask_question(
                question=request.question,
                search_mode=request.search_mode,
                project=request.project,
                doc_type=request.doc_type,
                category=request.category,
                tag=request.tag,
                limit=request.limit,
                save_log=request.save_log,
            )
        )
    except ValueError:
        return safe_error_response(
            code="invalid_ask_request",
            message="Ask request is invalid.",
            status_code=400,
        )
    except Exception:
        return safe_error_response(
            code="ask_unavailable",
            message="Ask service is unavailable.",
            status_code=503,
        )


@app.get(f"{API_PREFIX}/discovery/summary")
def read_discovery_summary() -> Any:
    return discovery_response(project_discovery.build_summary)


@app.get(f"{API_PREFIX}/discovery/projects")
def read_discovery_projects() -> Any:
    return discovery_response(project_discovery.discover_projects)


@app.get(f"{API_PREFIX}/discovery/doc-types")
def read_discovery_doc_types(project: str | None = Query(default=None)) -> Any:
    return discovery_response(
        lambda manifest: project_discovery.discover_doc_types(
            manifest,
            project=project,
        )
    )


@app.get(f"{API_PREFIX}/discovery/categories")
def read_discovery_categories() -> Any:
    return discovery_response(project_discovery.discover_categories)


@app.get(f"{API_PREFIX}/discovery/tags")
def read_discovery_tags(project: str | None = Query(default=None)) -> Any:
    return discovery_response(
        lambda manifest: project_discovery.discover_tags(
            manifest,
            project=project,
        )
    )
