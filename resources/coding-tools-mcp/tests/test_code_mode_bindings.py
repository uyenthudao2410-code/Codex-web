from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from coding_tools_mcp.errors import ToolFailure
from coding_tools_mcp.server import Runtime
from coding_tools_mcp.tool_contract import tool_metadata_contract


SMART_CONTRACT_SHA256 = "cf1eab62a466b2fb1c8d80f997ac61ef28255d891f13ad2f245d33015d701e86"


class _SemanticProvider:
    def __init__(self, match_path: str = "src/main.py") -> None:
        self.match_path = match_path

    def status(self) -> dict:
        return {
            "schema_version": 1,
            "available": True,
            "provider": "test-native-semantic",
            "read_only": True,
        }

    def localize(self, *, workspace: Path, path: str, queries: list[str], max_results: int) -> list[dict]:
        del workspace, path, max_results
        return [
            {
                "query_index": index,
                "query": query,
                "handled": True,
                "definitive": False,
                "matches": [{"path": self.match_path, "symbol": "needle", "line": 1, "column": 1}],
            }
            for index, query in enumerate(queries)
        ]


class CodeModeHostBindingTests(unittest.TestCase):
    @staticmethod
    def _request(operation: str, arguments: dict | None = None) -> dict:
        return {"schema_version": 1, "operation": operation, "arguments": arguments or {}}

    def _fixture(self, root: Path) -> None:
        (root / "src").mkdir(parents=True, exist_ok=True)
        (root / "src" / "main.py").write_text("needle = 'safe'\nprint(needle)\n", encoding="utf-8")
        (root / "README.md").write_text("code mode fixture\n", encoding="utf-8")

    def test_read_list_search_and_semantic_are_bounded_read_only_bindings(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._fixture(root)
            runtime = Runtime(root, semantic_localizer=_SemanticProvider())
            try:
                read = runtime.code_mode_bindings.call(self._request("read_text", {
                    "path": "src/main.py",
                    "start_line": 1,
                    "max_lines": 2,
                    "max_bytes": 4096,
                }))
                self.assertTrue(read["read_only"])
                self.assertEqual(read["result"]["path"], "src/main.py")
                self.assertIn("needle", read["result"]["content"])
                self.assertNotIn("next_action", read["result"])

                listed = runtime.code_mode_bindings.call(self._request("list_files", {
                    "path": "src",
                    "patterns": ["*.py"],
                    "max_results": 10,
                }))
                self.assertEqual([item["path"] for item in listed["result"]["files"]], ["src/main.py"])

                searched = runtime.code_mode_bindings.call(self._request("search_text", {
                    "path": "src",
                    "query": "needle",
                    "include_globs": ["*.py"],
                    "max_results": 10,
                    "context_lines": 1,
                }))
                self.assertGreaterEqual(searched["result"]["total_matches"], 1)
                self.assertEqual(searched["result"]["matches"][0]["path"], "src/main.py")

                semantic = runtime.code_mode_bindings.call(self._request("semantic_search", {
                    "path": "src",
                    "queries": ["needle"],
                    "max_results": 10,
                }))
                self.assertTrue(semantic["result"]["provider"]["available"])
                self.assertEqual(semantic["result"]["results"][0]["matches"][0]["path"], "src/main.py")
                serialized = json.dumps(semantic)
                self.assertNotIn(str(root), serialized)
            finally:
                runtime.close()

    def test_unknown_exec_mutation_environment_and_network_operations_are_denied(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            try:
                for operation in (
                    "exec_command",
                    "apply_patch",
                    "task_control",
                    "read_environment",
                    "network_fetch",
                    "call_tool",
                ):
                    with self.subTest(operation=operation), self.assertRaises(ToolFailure) as denied:
                        runtime.code_mode_bindings.call(self._request(operation, {}))
                    self.assertEqual(denied.exception.code, "CODE_MODE_BINDING_DENIED")
            finally:
                runtime.close()

    def test_paths_are_primary_workspace_only_even_when_authorized_roots_exist(self) -> None:
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as external:
            root = Path(temp)
            outside = Path(external)
            self._fixture(root)
            secret = outside / "secret.txt"
            secret.write_text("must not leak\n", encoding="utf-8")
            with patch.dict(os.environ, {"CODING_TOOLS_MCP_AUTHORIZED_ROOTS": json.dumps([str(outside)])}):
                runtime = Runtime(root)
            try:
                denied_paths = [
                    str(secret),
                    "../secret.txt",
                    "C:/Windows/system.ini",
                    "//server/share/file",
                    "~/secret",
                    "src/main.py:secret-stream",
                    "NUL",
                    "src/CON.txt",
                    "src/com1.log",
                ]
                for candidate in denied_paths:
                    with self.subTest(path=candidate), self.assertRaises(ToolFailure) as denied:
                        runtime.code_mode_bindings.call(self._request("read_text", {"path": candidate}))
                    self.assertEqual(denied.exception.code, "CODE_MODE_BINDING_PATH_DENIED")

                link = root / "external-link.txt"
                try:
                    link.symlink_to(secret)
                except OSError:
                    link = None
                if link is not None:
                    with self.assertRaises(ToolFailure) as denied:
                        runtime.code_mode_bindings.call(self._request("read_text", {"path": "external-link.txt"}))
                    self.assertEqual(denied.exception.code, "CODE_MODE_BINDING_PATH_DENIED")
            finally:
                runtime.close()

    def test_request_and_response_byte_caps_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._fixture(root)
            runtime = Runtime(root)
            try:
                with self.assertRaises(ToolFailure) as oversized_request:
                    runtime.code_mode_bindings.call(self._request("search_text", {
                        "path": ".",
                        "query": "x" * (33 * 1024),
                    }))
                self.assertEqual(oversized_request.exception.code, "CODE_MODE_BINDING_REQUEST_TOO_LARGE")

                with patch("coding_tools_mcp.code_mode.CODE_MODE_BINDING_MAX_RESPONSE_BYTES", 128):
                    with self.assertRaises(ToolFailure) as oversized_response:
                        runtime.code_mode_bindings.call(self._request("read_text", {
                            "path": "src/main.py",
                            "max_bytes": 4096,
                        }))
                self.assertEqual(oversized_response.exception.code, "CODE_MODE_BINDING_RESPONSE_TOO_LARGE")
            finally:
                runtime.close()

    def test_semantic_match_path_is_revalidated_before_return(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._fixture(root)
            runtime = Runtime(root, semantic_localizer=_SemanticProvider("C:/outside/secret.py"))
            try:
                with self.assertRaises(ToolFailure) as denied:
                    runtime.code_mode_bindings.call(self._request("semantic_search", {
                        "path": "src",
                        "queries": ["needle"],
                    }))
                self.assertEqual(denied.exception.code, "CODE_MODE_BINDING_PATH_DENIED")
            finally:
                runtime.close()

    def test_metadata_stays_gated_and_smart_surface_is_unchanged(self) -> None:
        metadata = tool_metadata_contract()["experimental_code_mode"]
        self.assertFalse(metadata["enabled"])
        self.assertEqual(metadata["status"], "gated")
        self.assertEqual(metadata["reason"], "isolated_worker_runtime_not_implemented")
        self.assertEqual(metadata["host_binding_proxy"], {
            "status": "ready",
            "schema_version": 1,
            "read_only": True,
            "operations": ["list_files", "read_text", "search_text", "semantic_search"],
        })
        self.assertEqual(metadata["worker_isolation"], {
            "status": "blocked",
            "reason": "verified_binding_only_backend_unavailable",
            "backend": None,
            "required_guarantees": [
                "no_direct_filesystem",
                "no_network",
                "no_inherited_environment_secrets",
                "no_unrestricted_subprocess",
                "bounded_framed_host_binding_only_ipc",
            ],
            "observed_nonqualifying_primitives": {
                "windows_job_object": "process_lifecycle_only",
                "linux_landlock": "write_confinement_only",
            },
            "embedded_capability_runtime": "not_configured",
        })
        self.assertIsNone(metadata["worker_isolation"]["backend"])
        self.assertFalse(metadata["direct_filesystem"])
        self.assertFalse(metadata["network"])
        self.assertFalse(metadata["environment_secrets"])
        self.assertFalse(metadata["subprocess"])

        with tempfile.TemporaryDirectory() as temp, patch.dict(os.environ, {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}):
            runtime = Runtime(Path(temp))
            try:
                self.assertEqual(len(runtime.exposed_tool_names()), 8)
                self.assertEqual(runtime.tool_contract["tool_count"], 8)
                self.assertEqual(runtime.tool_contract["sha256"], SMART_CONTRACT_SHA256)
            finally:
                runtime.close()


if __name__ == "__main__":
    unittest.main()
