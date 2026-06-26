import json
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

import api_app
import ask
import search_docs


class FakeQdrantClient:
    def get_collections(self):
        return []

    def close(self) -> None:
        pass


class FakeResponse:
    def __init__(self, status_code: int = 200) -> None:
        self.status_code = status_code


class ApiAppTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(api_app.app)

    def assert_no_windows_absolute_path(self, payload) -> None:
        text = json.dumps(payload, ensure_ascii=False)
        self.assertNotIn("D:\\", text)

    def assert_no_search_private_fields(self, payload) -> None:
        text = json.dumps(payload, ensure_ascii=False)
        for field in [
            '"source"',
            '"point_id"',
            '"payload"',
            '"text"',
        ]:
            self.assertNotIn(field, text)
        self.assert_no_windows_absolute_path(payload)

    def assert_no_ask_private_fields(self, payload) -> None:
        text = json.dumps(payload, ensure_ascii=False)
        for field in [
            '"source"',
            '"text"',
            '"prompt"',
            '"raw_context"',
            '"contexts"',
        ]:
            self.assertNotIn(field, text)
        self.assertNotIn("raw context", text.lower())
        self.assert_no_windows_absolute_path(payload)

    def test_root_returns_local_homepage(self) -> None:
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers["content-type"])
        self.assertIn("Personal Project Secretary", response.text)
        self.assertNotIn("D:\\", response.text)

    def test_homepage_contains_read_only_api_links(self) -> None:
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Local only", response.text)
        self.assertIn("Read-only by default", response.text)
        self.assertIn("No public network", response.text)
        self.assertIn("No index/rebuild/backup execution from Web", response.text)
        self.assertIn("will not execute ask, search, index, rebuild, or backup", response.text)
        for path in [
            "/ask",
            "/search",
            "/diagnostics",
            "/troubleshooting",
            "/api",
            "/docs",
            "/api/v1/health",
            "/api/v1/commands",
            "/api/v1/discovery/summary",
            "/api/v1/discovery/projects",
        ]:
            self.assertIn(path, response.text)

    def test_search_page_returns_html(self) -> None:
        response = self.client.get("/search")

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers["content-type"])
        self.assertIn("Search Documents", response.text)
        self.assertIn("Read-only by default", response.text)
        self.assertIn("Local only", response.text)
        self.assertIn("No public network", response.text)
        self.assertIn("Home", response.text)
        self.assertIn("Search", response.text)
        self.assertIn("Ask", response.text)
        self.assertIn("/troubleshooting", response.text)
        self.assertIn("does not run Ask", response.text)
        self.assertIn("Default mode is keyword", response.text)
        self.assertIn("show_text is off by default", response.text)
        self.assertIn(
            "Search failed. Please check Diagnostics and confirm local Qdrant/Ollama services are running.",
            response.text,
        )
        self.assertNotIn("Traceback", response.text)
        self.assertNotIn("D:\\", response.text)

    def test_ask_page_returns_html(self) -> None:
        response = self.client.get("/ask")

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers["content-type"])
        self.assertIn("Ask Knowledge Base", response.text)
        self.assertIn("Local only", response.text)
        self.assertIn("Ask mode", response.text)
        self.assertIn("Read-only by default", response.text)
        self.assertIn("No public network", response.text)
        self.assertIn("Home", response.text)
        self.assertIn("Search", response.text)
        self.assertIn("Ask", response.text)
        self.assertIn("/troubleshooting", response.text)
        self.assertIn("save_log", response.text)
        self.assertIn("local Ollama", response.text)
        self.assertIn("will not write to the knowledge base", response.text)
        self.assertIn("Default search_mode is hybrid", response.text)
        self.assertIn("save_log is fixed to false", response.text)
        self.assertIn(
            "Ask failed. Please check Diagnostics and confirm local Ollama and Qdrant are running.",
            response.text,
        )
        self.assertNotIn("Traceback", response.text)
        self.assertNotIn("D:\\", response.text)

    def test_diagnostics_page_returns_html(self) -> None:
        response = self.client.get("/diagnostics")

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers["content-type"])
        self.assertIn("System Diagnostics", response.text)
        self.assertIn("Local only", response.text)
        self.assertIn("Read-only diagnostics", response.text)
        self.assertIn("/troubleshooting", response.text)
        self.assertIn(
            "Diagnostics check failed. Please inspect local terminal logs and the troubleshooting guide.",
            response.text,
        )
        self.assertNotIn("D:\\", response.text)

    def test_troubleshooting_page_returns_html(self) -> None:
        response = self.client.get("/troubleshooting")

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers["content-type"])
        self.assertIn("Troubleshooting Guide", response.text)
        self.assertIn("Local only", response.text)
        self.assertIn("Read-only guide", response.text)
        self.assertIn("This page does not execute Ask, Search, index, rebuild, or backup", response.text)
        self.assertIn("docker ps", response.text)
        self.assertIn("ollama list", response.text)
        self.assertNotIn("D:\\", response.text)
        self.assertNotIn("Traceback", response.text)

    def test_api_root_info(self) -> None:
        response = self.client.get("/api")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["service"], api_app.SERVICE_NAME)
        self.assertEqual(data["api_version"], api_app.API_VERSION)
        self.assertEqual(data["docs_url"], "/docs")
        self.assertEqual(data["health_url"], "/api/v1/health")
        self.assertIn("discovery_urls", data)
        self.assert_no_windows_absolute_path(data)

    def test_api_info(self) -> None:
        response = self.client.get("/api/v1")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["service"], api_app.SERVICE_NAME)
        self.assertEqual(data["api_version"], api_app.API_VERSION)
        self.assert_no_windows_absolute_path(data)

    def test_health(self) -> None:
        response = self.client.get("/api/v1/health")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assert_no_windows_absolute_path(data)

    def test_diagnostics_api_returns_safe_checks(self) -> None:
        with (
            patch("api_app.command_registry.list_commands", return_value=[{"id": "one"}]),
            patch("api_app.project_discovery.load_manifest", return_value={}),
            patch(
                "api_app.project_discovery.build_summary",
                return_value={"project_count": 2, "total_files": 10},
            ),
            patch("api_app.search_docs.get_qdrant_client", return_value=FakeQdrantClient()),
            patch("api_app.requests.get", return_value=FakeResponse(200)),
        ):
            response = self.client.get("/api/v1/diagnostics")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertIn("checks", data)
        self.assertEqual(data["checks"]["commands"]["count"], 1)
        self.assertEqual(data["checks"]["discovery"]["project_count"], 2)
        self.assertEqual(data["checks"]["discovery"]["file_count"], 10)
        self.assertEqual(data["checks"]["qdrant"]["status"], "ok")
        self.assertEqual(data["checks"]["ollama"]["status"], "ok")
        text = json.dumps(data, ensure_ascii=False)
        self.assertNotIn("Traceback", text)
        self.assertNotIn("http://", text)
        self.assertNotIn("https://", text)
        self.assert_no_windows_absolute_path(data)

    def test_diagnostics_api_failures_are_safe(self) -> None:
        with (
            patch(
                "api_app.command_registry.list_commands",
                side_effect=RuntimeError("D:\\Private\\commands"),
            ),
            patch(
                "api_app.project_discovery.load_manifest",
                side_effect=RuntimeError("D:\\Private\\manifest.json"),
            ),
            patch(
                "api_app.search_docs.get_qdrant_client",
                side_effect=RuntimeError("http://127.0.0.1:6333"),
            ),
            patch(
                "api_app.requests.get",
                side_effect=RuntimeError("http://127.0.0.1:11434"),
            ),
        ):
            response = self.client.get("/api/v1/diagnostics")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "error")
        self.assertIn("checks", data)
        self.assertEqual(data["checks"]["commands"]["message"], "Service is not available")
        self.assertEqual(data["checks"]["discovery"]["message"], "Service is not available")
        self.assertEqual(data["checks"]["qdrant"]["message"], "Service is not available")
        self.assertEqual(data["checks"]["ollama"]["message"], "Service is not available")
        text = json.dumps(data, ensure_ascii=False)
        self.assertNotIn("Traceback", text)
        self.assertNotIn("http://", text)
        self.assertNotIn("https://", text)
        self.assert_no_windows_absolute_path(data)

    def test_search_uses_keyword_mode_by_default(self) -> None:
        safe_result = {
            "status": "ok",
            "query": "test",
            "mode": "keyword",
            "limit": 5,
            "count": 0,
            "results": [],
        }

        with patch("api_app.search_docs.search_documents", return_value=safe_result) as search_mock:
            response = self.client.get("/api/v1/search?q=test")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["mode"], "keyword")
        search_mock.assert_called_once()
        self.assertEqual(search_mock.call_args.kwargs["query"], "test")
        self.assertEqual(search_mock.call_args.kwargs["mode"], "keyword")
        self.assertFalse(search_mock.call_args.kwargs["show_text"])
        self.assert_no_search_private_fields(data)

    def test_search_invalid_mode_returns_safe_error(self) -> None:
        response = self.client.get("/api/v1/search?q=test&mode=invalid")

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data["status"], "error")
        self.assertEqual(data["code"], "invalid_search_request")
        self.assert_no_windows_absolute_path(data)

    def test_search_empty_query_returns_safe_error(self) -> None:
        response = self.client.get("/api/v1/search?q=%20%20%20")

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data["status"], "error")
        self.assertEqual(data["code"], "invalid_search_request")
        self.assert_no_windows_absolute_path(data)

    def test_search_limit_over_max_returns_422(self) -> None:
        with patch("api_app.search_docs.search_documents") as search_mock:
            response = self.client.get("/api/v1/search?q=test&limit=21")

        self.assertEqual(response.status_code, 422)
        search_mock.assert_not_called()

    def test_search_api_strips_private_fields_from_response(self) -> None:
        unsafe_result = {
            "status": "ok",
            "query": "test",
            "mode": "keyword",
            "limit": 5,
            "count": 1,
            "results": [
                {
                    "title": "Safe title",
                    "source": "D:\\Private\\note.md",
                    "point_id": "abc",
                    "payload": {"text": "Markdown full text"},
                    "text": "Markdown full text",
                }
            ],
        }

        with patch("api_app.search_docs.search_documents", return_value=unsafe_result):
            response = self.client.get("/api/v1/search?q=test")

        self.assertEqual(response.status_code, 200)
        self.assert_no_search_private_fields(response.json())

    def test_search_documents_sanitizes_raw_results(self) -> None:
        raw_results = [
            {
                "score": 0.95,
                "mode": "keyword",
                "point_id": "abc",
                "payload": {
                    "title": "Safe title",
                    "file_name": "D:\\Private\\note.md",
                    "project": "Demo",
                    "doc_type": "progress_log",
                    "category": "project",
                    "tags": ["RAG", "D:\\Private"],
                    "chunk_index": 0,
                    "updated_at": "2026-06-23",
                    "source": "D:\\Private\\note.md",
                    "text": "Markdown full text that should not be exposed",
                },
            }
        ]

        with (
            patch("search_docs.get_qdrant_client", return_value=FakeQdrantClient()),
            patch("search_docs.keyword_search", return_value=raw_results),
        ):
            data = search_docs.search_documents(" test ")

        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["query"], "test")
        self.assertEqual(data["mode"], "keyword")
        self.assertEqual(data["limit"], 5)
        self.assertEqual(data["count"], 1)
        self.assertNotIn("snippet", data["results"][0])
        self.assert_no_search_private_fields(data)

    def test_search_documents_show_text_returns_short_snippet(self) -> None:
        raw_text = "A" * 500
        raw_results = [
            {
                "score": 0.95,
                "mode": "keyword",
                "payload": {
                    "title": "Safe title",
                    "file_name": "note.md",
                    "project": "Demo",
                    "doc_type": "progress_log",
                    "category": "project",
                    "tags": ["RAG"],
                    "chunk_index": 0,
                    "updated_at": "2026-06-23",
                    "text": raw_text,
                },
            }
        ]

        with (
            patch("search_docs.get_qdrant_client", return_value=FakeQdrantClient()),
            patch("search_docs.keyword_search", return_value=raw_results),
        ):
            data = search_docs.search_documents(
                "test",
                show_text=True,
                snippet_chars=40,
            )

        snippet = data["results"][0]["snippet"]
        self.assertLessEqual(len(snippet), 43)
        self.assertTrue(snippet.endswith("..."))
        self.assertNotEqual(snippet, raw_text)
        self.assert_no_search_private_fields(data)

    def test_ask_uses_hybrid_mode_by_default(self) -> None:
        safe_result = {
            "status": "ok",
            "question": "test",
            "answer": "safe answer",
            "search_mode": "hybrid",
            "count": 0,
            "sources": [],
            "save_log": False,
        }

        with patch("api_app.ask.ask_question", return_value=safe_result) as ask_mock:
            response = self.client.post(
                "/api/v1/ask",
                json={"question": "test"},
            )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["search_mode"], "hybrid")
        self.assertFalse(data["save_log"])
        ask_mock.assert_called_once()
        self.assertEqual(ask_mock.call_args.kwargs["question"], "test")
        self.assertEqual(ask_mock.call_args.kwargs["search_mode"], "hybrid")
        self.assertFalse(ask_mock.call_args.kwargs["save_log"])
        self.assert_no_ask_private_fields(data)

    def test_ask_empty_question_returns_safe_error(self) -> None:
        response = self.client.post(
            "/api/v1/ask",
            json={"question": "   "},
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data["status"], "error")
        self.assertEqual(data["code"], "invalid_ask_request")
        self.assert_no_windows_absolute_path(data)

    def test_ask_invalid_search_mode_returns_safe_error(self) -> None:
        response = self.client.post(
            "/api/v1/ask",
            json={"question": "test", "search_mode": "invalid"},
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data["status"], "error")
        self.assertEqual(data["code"], "invalid_ask_request")
        self.assert_no_windows_absolute_path(data)

    def test_ask_limit_over_max_returns_422(self) -> None:
        with patch("api_app.ask.ask_question") as ask_mock:
            response = self.client.post(
                "/api/v1/ask",
                json={"question": "test", "limit": 11},
            )

        self.assertEqual(response.status_code, 422)
        ask_mock.assert_not_called()

    def test_ask_save_log_true_is_rejected(self) -> None:
        with patch("ask.save_qa_log") as save_mock:
            response = self.client.post(
                "/api/v1/ask",
                json={"question": "test", "save_log": True},
            )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data["status"], "error")
        self.assertEqual(data["code"], "invalid_ask_request")
        save_mock.assert_not_called()
        self.assert_no_windows_absolute_path(data)

    def test_ask_api_strips_private_fields_from_response(self) -> None:
        unsafe_result = {
            "status": "ok",
            "question": "test",
            "answer": "safe answer",
            "search_mode": "hybrid",
            "count": 1,
            "sources": [
                {
                    "title": "Safe title",
                    "source": "D:\\Private\\note.md",
                    "text": "Markdown full text",
                    "prompt": "hidden prompt",
                    "raw_context": {"source": "D:\\Private\\note.md"},
                }
            ],
            "contexts": [{"text": "hidden"}],
            "save_log": False,
        }

        with patch("api_app.ask.ask_question", return_value=unsafe_result):
            response = self.client.post(
                "/api/v1/ask",
                json={"question": "test"},
            )

        self.assertEqual(response.status_code, 200)
        self.assert_no_ask_private_fields(response.json())

    def test_ask_api_error_does_not_return_exception_text(self) -> None:
        with patch(
            "api_app.ask.ask_question",
            side_effect=RuntimeError("D:\\Private\\ollama_url"),
        ):
            response = self.client.post(
                "/api/v1/ask",
                json={"question": "test"},
            )

        self.assertEqual(response.status_code, 503)
        data = response.json()
        self.assertEqual(data["status"], "error")
        self.assertEqual(data["code"], "ask_unavailable")
        self.assertNotIn("ollama", json.dumps(data, ensure_ascii=False).lower())
        self.assert_no_windows_absolute_path(data)

    def test_ask_question_sanitizes_sources_and_does_not_save_log(self) -> None:
        contexts = [
            {
                "score": 0.95,
                "mode": "hybrid",
                "title": "Safe title",
                "file_name": "D:\\Private\\note.md",
                "project": "Demo",
                "doc_type": "progress_log",
                "category": "project",
                "tags": ["RAG", "D:\\Private"],
                "chunk_index": 0,
                "updated_at": "2026-06-23",
                "source": "D:\\Private\\note.md",
                "text": "Markdown full text",
            }
        ]

        with (
            patch("ask.search_context", return_value=contexts),
            patch("ask.generate_answer", return_value="safe answer"),
            patch("ask.save_qa_log") as save_mock,
        ):
            data = ask.ask_question(" test ")

        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["question"], "test")
        self.assertEqual(data["answer"], "safe answer")
        self.assertEqual(data["search_mode"], "hybrid")
        self.assertFalse(data["save_log"])
        save_mock.assert_not_called()
        self.assert_no_ask_private_fields(data)

    def test_commands(self) -> None:
        response = self.client.get("/api/v1/commands")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertIn("commands", data)
        self.assertIsInstance(data["commands"], list)
        self.assert_no_windows_absolute_path(data)

    def test_commands_do_not_expose_script(self) -> None:
        response = self.client.get("/api/v1/commands")

        self.assertEqual(response.status_code, 200)
        text = json.dumps(response.json(), ensure_ascii=False)
        self.assertNotIn('"script"', text)

    def test_discovery_summary_is_sanitized(self) -> None:
        summary = {
            "manifest_path": "D:\\Private\\index_manifest.json",
            "knowledge_root": "D:\\Private",
            "total_files": 1,
            "total_chunks": 2,
            "project_count": 1,
            "category_count": 1,
            "doc_type_count": 1,
            "tag_count": 1,
            "projects": [],
            "categories": [],
            "doc_types": [],
            "tags": [],
        }

        with (
            patch("api_app.project_discovery.load_manifest", return_value={}),
            patch("api_app.project_discovery.build_summary", return_value=summary),
        ):
            response = self.client.get("/api/v1/discovery/summary")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertNotIn("manifest_path", data)
        self.assertNotIn("knowledge_root", data)
        self.assertEqual(data["total_files"], 1)
        self.assert_no_windows_absolute_path(data)

    def test_discovery_manifest_error_is_safe(self) -> None:
        with patch(
            "api_app.project_discovery.load_manifest",
            side_effect=RuntimeError("D:\\Private\\index_manifest.json"),
        ):
            response = self.client.get("/api/v1/discovery/summary")

        self.assertEqual(response.status_code, 503)
        data = response.json()
        self.assertEqual(data["status"], "error")
        self.assertEqual(data["code"], "manifest_unavailable")
        self.assertEqual(data["message"], "Discovery manifest is unavailable.")
        self.assert_no_windows_absolute_path(data)

    def test_default_host_is_localhost(self) -> None:
        self.assertEqual(api_app.DEFAULT_HOST, "127.0.0.1")

    def test_favicon_does_not_404(self) -> None:
        response = self.client.get("/favicon.ico")

        self.assertEqual(response.status_code, 204)


if __name__ == "__main__":
    unittest.main()
