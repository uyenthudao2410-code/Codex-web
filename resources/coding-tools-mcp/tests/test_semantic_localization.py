from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

import coding_tools_mcp.semantic_localization as semantic_module
from coding_tools_mcp.semantic_localization import (
    DEFAULT_UNAVAILABLE_REASON,
    INVALID_BINDING_REASON,
    NATIVE_LSP_CREDENTIAL_FILE_ENV,
    NATIVE_LSP_PROVIDER,
    NATIVE_LSP_URL_ENV,
    NativeRustSemanticLocalizationProvider,
    _read_project_credential,
    _portable_workspace_identity,
    portable_workspace_sha256,
    run_semantic_localization,
    semantic_localizer_from_env,
    semantic_provider_status,
)


VALID_CREDENTIAL = "webcodex_" + "a" * 64


class _Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False


class NativeSemanticLocalizationTests(unittest.TestCase):
    def test_env_factory_defaults_off_and_fails_closed_for_invalid_binding(self) -> None:
        with patch.dict(os.environ, {NATIVE_LSP_URL_ENV: "", NATIVE_LSP_CREDENTIAL_FILE_ENV: ""}):
            provider = semantic_localizer_from_env()
            status = semantic_provider_status(provider)
            self.assertEqual(status["reason"], DEFAULT_UNAVAILABLE_REASON)
            self.assertEqual(status["binding"], {
                "state": "unconfigured",
                "origin_configured": False,
                "credential_file_configured": False,
                "missing": ["origin", "credential_file"],
            })

        with patch.dict(
            os.environ,
            {NATIVE_LSP_URL_ENV: "http://127.0.0.1:45819", NATIVE_LSP_CREDENTIAL_FILE_ENV: ""},
        ):
            status = semantic_provider_status(semantic_localizer_from_env())
        self.assertEqual(status["reason"], INVALID_BINDING_REASON)
        self.assertEqual(status["binding"], {
            "state": "partial",
            "origin_configured": True,
            "credential_file_configured": False,
            "missing": ["credential_file"],
        })

        with tempfile.TemporaryDirectory() as temp:
            credential_file = Path(temp) / "credential"
            credential_file.write_text(VALID_CREDENTIAL + "\n", encoding="utf-8")
            if os.name != "nt":
                credential_file.chmod(0o600)
            with patch.dict(
                os.environ,
                {
                    NATIVE_LSP_URL_ENV: "http://example.com:7777",
                    NATIVE_LSP_CREDENTIAL_FILE_ENV: str(credential_file),
                },
            ):
                status = semantic_provider_status(semantic_localizer_from_env())
            self.assertFalse(status["available"])
            self.assertEqual(status["reason"], INVALID_BINDING_REASON)
            self.assertEqual(status["binding"], {
                "state": "invalid",
                "origin_configured": True,
                "credential_file_configured": True,
                "invalid_component": "origin",
            })
            self.assertNotIn(str(credential_file), json.dumps(status))
            self.assertNotIn(VALID_CREDENTIAL, json.dumps(status))

            credential_file.write_text("not-a-project-credential\n", encoding="utf-8")
            with patch.dict(
                os.environ,
                {
                    NATIVE_LSP_URL_ENV: "http://127.0.0.1:45819",
                    NATIVE_LSP_CREDENTIAL_FILE_ENV: str(credential_file),
                },
            ):
                status = semantic_provider_status(semantic_localizer_from_env())
            self.assertEqual(status["binding"], {
                "state": "invalid",
                "origin_configured": True,
                "credential_file_configured": True,
                "invalid_component": "credential_file",
            })
            self.assertNotIn(str(credential_file), json.dumps(status))

    def test_portable_workspace_identity_matches_rust_windows_contract(self) -> None:
        self.assertEqual(_portable_workspace_identity(r"\\?\E:\Repo\Src", windows=True), "E:/Repo/Src")
        self.assertEqual(
            _portable_workspace_identity(r"\\?\UNC\server\share\repo", windows=True),
            "//server/share/repo",
        )
        self.assertEqual(_portable_workspace_identity("/srv/repo", windows=False), "/srv/repo")

    def test_happy_request_is_loopback_bounded_and_sends_no_raw_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp).resolve()
            provider = NativeRustSemanticLocalizationProvider(
                origin="http://127.0.0.1:45819",
                credential=VALID_CREDENTIAL,
            )
            captured = {}

            def fake_open(request, timeout):
                captured["request"] = request
                captured["timeout"] = timeout
                payload = {
                    "ok": True,
                    "data": {
                        "schema_version": 1,
                        "provider": NATIVE_LSP_PROVIDER,
                        "read_only": True,
                        "results": [
                            {
                                "query_index": 0,
                                "query": "ToolRuntime",
                                "handled": True,
                                "definitive": False,
                                "matches": [{"path": "src/tool_runtime/runtime.rs", "symbol": "ToolRuntime"}],
                            }
                        ],
                    },
                }
                return _Response(json.dumps(payload).encode("utf-8"))

            with patch.object(provider._opener, "open", side_effect=fake_open):
                rows = provider.localize(
                    workspace=workspace,
                    path="src",
                    queries=["ToolRuntime"],
                    max_results=10,
                )
            request = captured["request"]
            body = json.loads(request.data.decode("utf-8"))
            self.assertEqual(body["workspace_sha256"], portable_workspace_sha256(workspace))
            self.assertNotIn(str(workspace), request.data.decode("utf-8"))
            self.assertEqual(request.full_url, "http://127.0.0.1:45819/api/connector/internal/semantic/localize")
            self.assertEqual(request.get_header("Authorization"), f"Bearer {VALID_CREDENTIAL}")
            self.assertEqual(rows[0]["matches"][0]["path"], "src/tool_runtime/runtime.rs")
            status_text = json.dumps(semantic_provider_status(provider))
            self.assertNotIn("45819", status_text)
            self.assertNotIn(VALID_CREDENTIAL, status_text)
            self.assertEqual(semantic_provider_status(provider)["binding"], {
                "state": "configured",
                "origin_configured": True,
                "credential_file_configured": True,
            })

    def test_transport_failure_falls_back_without_secret_or_path_leak(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            provider = NativeRustSemanticLocalizationProvider(
                origin="http://127.0.0.1:45819",
                credential=VALID_CREDENTIAL,
            )
            with patch.object(provider._opener, "open", side_effect=urllib.error.URLError("secret upstream detail")):
                projected = run_semantic_localization(
                    provider,
                    workspace=workspace,
                    path=".",
                    queries=["needle"],
                    max_results=10,
                )
            self.assertFalse(projected["provider"]["available"])
            self.assertEqual(projected["provider"]["reason"], "SEMANTIC_PROVIDER_CALL_FAILED")
            self.assertEqual(projected["results"][0]["handled"], False)
            serialized = json.dumps(projected)
            self.assertNotIn("secret upstream detail", serialized)
            self.assertNotIn(VALID_CREDENTIAL, serialized)
            self.assertNotIn(str(workspace), serialized)

    def test_oversized_response_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            provider = NativeRustSemanticLocalizationProvider(
                origin="http://[::1]:45819",
                credential=VALID_CREDENTIAL,
            )
            raw = b"x" * (semantic_module.NATIVE_LSP_MAX_RESPONSE_BYTES + 1)
            with patch.object(provider._opener, "open", return_value=_Response(raw)):
                projected = run_semantic_localization(
                    provider,
                    workspace=Path(temp),
                    path=".",
                    queries=["needle"],
                    max_results=10,
                )
            self.assertFalse(projected["provider"]["available"])
            self.assertEqual(projected["provider"]["reason"], "SEMANTIC_PROVIDER_CALL_FAILED")

    def test_false_ok_response_and_drive_scope_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            provider = NativeRustSemanticLocalizationProvider(
                origin="http://127.0.0.1:45819",
                credential=VALID_CREDENTIAL,
            )
            with self.assertRaises(ValueError):
                provider.localize(
                    workspace=Path(temp),
                    path="C:/repo/src",
                    queries=["needle"],
                    max_results=10,
                )

            payload = {
                "ok": False,
                "data": {
                    "schema_version": 1,
                    "provider": NATIVE_LSP_PROVIDER,
                    "read_only": True,
                    "results": [],
                },
            }
            with patch.object(
                provider._opener,
                "open",
                return_value=_Response(json.dumps(payload).encode("utf-8")),
            ):
                projected = run_semantic_localization(
                    provider,
                    workspace=Path(temp),
                    path=".",
                    queries=["needle"],
                    max_results=10,
                )
            self.assertFalse(projected["provider"]["available"])
            self.assertEqual(projected["provider"]["reason"], "SEMANTIC_PROVIDER_CALL_FAILED")

    def test_credential_symlink_is_rejected_when_supported(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "credential"
            target.write_text(VALID_CREDENTIAL + "\n", encoding="utf-8")
            if os.name != "nt":
                target.chmod(0o600)
            link = Path(temp) / "credential-link"
            try:
                link.symlink_to(target)
            except OSError as exc:
                self.skipTest(f"symlink creation unavailable on this host: {type(exc).__name__}")
            with self.assertRaises(ValueError):
                _read_project_credential(str(link))

    def test_opener_disables_proxies_and_redirects(self) -> None:
        original = urllib.request.build_opener
        with patch.object(semantic_module.urllib.request, "build_opener", wraps=original) as build_opener:
            NativeRustSemanticLocalizationProvider(
                origin="http://127.0.0.1:45819",
                credential=VALID_CREDENTIAL,
            )
        handlers = build_opener.call_args.args
        proxy = next(item for item in handlers if isinstance(item, urllib.request.ProxyHandler))
        self.assertEqual(proxy.proxies, {})
        self.assertTrue(any(type(item).__name__ == "_NoRedirect" for item in handlers))


if __name__ == "__main__":
    unittest.main()
