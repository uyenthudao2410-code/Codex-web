from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from coding_tools_mcp.semantic_localization import (
    NATIVE_LSP_PROVIDER,
    NativeRustSemanticLocalizationProvider,
    semantic_provider_health_status,
)
from coding_tools_mcp.server import Runtime


VALID_CREDENTIAL = "webcodex_" + "a" * 64


class _Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False


class _UnhealthyProvider:
    def status(self):
        return {
            "schema_version": 1,
            "available": True,
            "provider": NATIVE_LSP_PROVIDER,
            "read_only": True,
            "binding": {
                "state": "configured",
                "origin_configured": True,
                "credential_file_configured": True,
            },
        }

    def resource_status(self, *, workspace, path):
        del workspace, path
        raise RuntimeError("synthetic resource status failure")

    def localize(self, **kwargs):
        del kwargs
        raise AssertionError("unhealthy provider must fall back before localize")


class _HealthyProvider(_UnhealthyProvider):
    def resource_status(self, *, workspace, path):
        del workspace, path
        return {
            "lifecycle_state": "RUNNING",
            "warm": True,
            "pressure_state": "NORMAL",
            "process_instance_id": "semantic-test-instance",
            "pending_request_count": 0,
            "restart_count": 0,
            "drain_count": 0,
            "observed_at": 1,
        }

    def localize(self, *, workspace, path, queries, max_results, resource_class):
        del workspace, path, max_results, resource_class
        return [
            {
                "query_index": index,
                "query": query,
                "handled": True,
                "definitive": False,
                "matches": [{"path": "app.py", "line": 1, "symbol": query}],
            }
            for index, query in enumerate(queries)
        ]


class SemanticRuntimeHealthTests(unittest.TestCase):
    def test_native_provider_normalizes_absolute_workspace_scope_and_rejects_outside(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            provider = NativeRustSemanticLocalizationProvider(
                origin="http://127.0.0.1:45819",
                credential=VALID_CREDENTIAL,
            )
            payload = {
                "ok": True,
                "data": {
                    "schema_version": 1,
                    "provider": NATIVE_LSP_PROVIDER,
                    "read_only": True,
                    "results": [{
                        "query_index": 0,
                        "query": "KnownSymbol",
                        "handled": True,
                        "matches": [{"path": "app.py", "line": 1}],
                    }],
                },
            }
            captured = {}

            def fake_open(request, timeout):
                captured["request"] = request
                captured["timeout"] = timeout
                return _Response(json.dumps(payload).encode("utf-8"))

            with patch.object(provider._opener, "open", side_effect=fake_open):
                rows = provider.localize(
                    workspace=workspace,
                    path=str(workspace),
                    queries=["KnownSymbol"],
                    max_results=10,
                    resource_class="HEAVY",
                )
            self.assertEqual(len(rows), 1)
            request_payload = json.loads(captured["request"].data.decode("utf-8"))
            self.assertEqual(request_payload["path"], ".")
            self.assertNotIn(str(workspace), captured["request"].data.decode("utf-8"))

            outside = workspace.parent / f"{workspace.name}-outside"
            with self.assertRaises(ValueError):
                provider.resource_status(workspace=workspace, path=str(outside))

    def test_effective_health_fails_closed_when_binding_is_configured_but_resource_probe_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            status = semantic_provider_health_status(
                _UnhealthyProvider(),
                workspace=workspace,
                path=str(workspace),
            )
            self.assertTrue(status["binding_available"])
            self.assertFalse(status["available"])
            self.assertEqual(status["health_state"], "UNAVAILABLE")
            self.assertEqual(status["reason"], "LSP_RESOURCE_STATUS_FAILED")
            self.assertEqual(status["resource"]["error_class"], "RuntimeError")
            self.assertFalse(status["resource"]["observed"])

    def test_workspace_context_full_reports_effective_semantic_health(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runtime = Runtime(root, permission_mode="dangerous")
            try:
                runtime.semantic_localizer = _UnhealthyProvider()
                result = runtime.workspace_context({"path": str(root), "detail": "full"})
                status = result["runtime"]["semantic_localization"]
                self.assertTrue(status["binding_available"])
                self.assertFalse(status["available"])
                self.assertEqual(status["reason"], "LSP_RESOURCE_STATUS_FAILED")
                self.assertFalse(status["resource"]["observed"])
            finally:
                runtime.close()

    def test_prepare_context_preserves_text_fallback_when_resource_health_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "app.py").write_text("KnownSymbol = 1\n", encoding="utf-8")
            runtime = Runtime(root, permission_mode="dangerous")
            try:
                runtime.semantic_localizer = _UnhealthyProvider()
                result = runtime.prepare_coding_context({
                    "path": str(root),
                    "queries": ["KnownSymbol"],
                    "max_files": 2,
                    "force_refresh": True,
                })
                localization = result["composite_read"]["execution"]["localization"]
                self.assertEqual(localization["semantic_handled"], 0)
                self.assertEqual(localization["text_fallback_queries"], 1)
                self.assertEqual(result["searches"][0]["total_matches"], 1)
            finally:
                runtime.close()

    def test_prepare_context_records_semantic_handled_for_healthy_provider(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "app.py").write_text("KnownSymbol = 1\n", encoding="utf-8")
            runtime = Runtime(root, permission_mode="dangerous")
            try:
                runtime.semantic_localizer = _HealthyProvider()
                result = runtime.prepare_coding_context({
                    "path": str(root),
                    "queries": ["KnownSymbol"],
                    "max_files": 2,
                    "force_refresh": True,
                })
                localization = result["composite_read"]["execution"]["localization"]
                self.assertEqual(localization["semantic_attempted"], 1)
                self.assertEqual(localization["semantic_handled"], 1)
                self.assertEqual(localization["text_fallback_queries"], 0)
                self.assertEqual(result["searches"][0]["engine"], f"semantic:{NATIVE_LSP_PROVIDER}")
            finally:
                runtime.close()


if __name__ == "__main__":
    unittest.main()
