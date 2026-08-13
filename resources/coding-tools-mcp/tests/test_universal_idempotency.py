from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from coding_tools_mcp.errors import ToolFailure
from coding_tools_mcp.server import Runtime, validate_arguments


class UniversalIdempotencyTests(unittest.TestCase):
    def test_duplicate_delivery_replays_without_second_side_effect(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            marker = root / "marker.txt"
            runtime = Runtime(root)
            try:
                args = {
                    "cmd": "echo ran >> marker.txt",
                    "yield_time_ms": 1000,
                    "max_output_bytes": 4096,
                    "verbosity": "full",
                    "idempotency_key": "dup-exec-1",
                }
                first = runtime.call_tool("exec_command", dict(args))
                second = runtime.call_tool("exec_command", dict(args))
                self.assertFalse(first.get("isError"))
                self.assertFalse(second.get("isError"))
                self.assertTrue(second["structuredContent"].get("deduplicated"))
                self.assertTrue(second["structuredContent"].get("durable_idempotency"))
                record = second["structuredContent"].get("idempotency") or {}
                self.assertEqual(record.get("status"), "completed")
                lines = marker.read_text(encoding="utf-8").splitlines()
                self.assertEqual(len([line for line in lines if line.strip() == "ran"]), 1)
            finally:
                runtime.close()

    def test_conflicting_reuse_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            try:
                args = {
                    "cmd": "echo once",
                    "yield_time_ms": 1000,
                    "max_output_bytes": 4096,
                    "verbosity": "full",
                    "idempotency_key": "conflict-key",
                }
                runtime.call_tool("exec_command", dict(args))
                changed = dict(args)
                changed["cmd"] = "echo differently"
                result = runtime.call_tool("exec_command", changed)
                self.assertTrue(result.get("isError"))
                error = result.get("structuredContent", {}).get("error") or {}
                self.assertEqual(error.get("code"), "IDEMPOTENCY_CONFLICT")
            finally:
                runtime.close()

    def test_in_progress_claim_blocks_second_copy(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            try:
                args = {
                    "cmd": "echo busy",
                    "yield_time_ms": 1000,
                    "max_output_bytes": 4096,
                    "verbosity": "full",
                    "idempotency_key": "busy-key",
                }
                request_hash = runtime._request_hash(args)
                runtime.orchestration_ledger.claim_idempotency(
                    idempotency_key="busy-key",
                    operation="exec_command",
                    request_hash=request_hash,
                    process_instance_id=runtime.process_instance_id,
                )
                result = runtime.call_tool("exec_command", dict(args))
                self.assertTrue(result.get("isError"))
                error = result.get("structuredContent", {}).get("error") or {}
                self.assertEqual(error.get("code"), "IDEMPOTENCY_IN_PROGRESS")
                self.assertTrue(error.get("retryable"))
            finally:
                runtime.close()

    def test_unknown_outcome_after_process_restart_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            args = {
                "cmd": "echo unknown",
                "yield_time_ms": 1000,
                "max_output_bytes": 4096,
                "verbosity": "full",
                "idempotency_key": "unknown-key",
            }
            first = Runtime(root)
            try:
                request_hash = first._request_hash(args)
                first.orchestration_ledger.claim_idempotency(
                    idempotency_key="unknown-key",
                    operation="exec_command",
                    request_hash=request_hash,
                    process_instance_id="prior-mcp-process",
                )
            finally:
                first.close()
            restored = Runtime(root)
            try:
                result = restored.call_tool("exec_command", dict(args))
                self.assertTrue(result.get("isError"))
                error = result.get("structuredContent", {}).get("error") or {}
                self.assertEqual(error.get("code"), "IDEMPOTENCY_OUTCOME_UNKNOWN")
            finally:
                restored.close()

    def test_replay_survives_runtime_restart(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            args = {
                "cmd": "echo persisted",
                "yield_time_ms": 1000,
                "max_output_bytes": 4096,
                "verbosity": "full",
                "idempotency_key": "restart-key",
            }
            first = Runtime(root)
            try:
                first.call_tool("exec_command", dict(args))
            finally:
                first.close()
            restored = Runtime(root)
            try:
                replay = restored.call_tool("exec_command", dict(args))
                self.assertTrue(replay["structuredContent"].get("deduplicated"))
            finally:
                restored.close()

    def test_terminal_failure_recorded_and_repeated_call_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            try:
                args = {
                    "patch": "not a valid patch envelope",
                    "idempotency_key": "terminal-key",
                }
                first = runtime.call_tool("apply_patch", dict(args))
                self.assertTrue(first.get("isError"))
                error = first.get("structuredContent", {}).get("error") or {}
                self.assertEqual(error.get("code"), "PATCH_FAILED")
                repeated = runtime.call_tool("apply_patch", dict(args))
                self.assertTrue(repeated.get("isError"))
                repeated_error = repeated.get("structuredContent", {}).get("error") or {}
                self.assertEqual(repeated_error.get("code"), "IDEMPOTENT_REQUEST_FAILED")
            finally:
                runtime.close()

    def test_exposed_schemas_accept_idempotency_key(self) -> None:
        with tempfile.TemporaryDirectory() as temp, patch.dict(
            "os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}
        ):
            runtime = Runtime(Path(temp))
            try:
                for name in runtime.exposed_tool_names():
                    try:
                        validate_arguments(name, {"idempotency_key": "schema-key"})
                    except Exception as exc:
                        self.assertNotIn(
                            "idempotency_key",
                            str(getattr(exc, "message", exc)),
                            f"{name} rejected idempotency_key",
                        )
            finally:
                runtime.close()


class DefaultCwdDeprecationTests(unittest.TestCase):
    def test_set_default_cwd_is_deprecated_noop(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            try:
                payload = runtime.set_default_cwd({"path": "."})
                self.assertTrue(payload.get("deprecated"))
                self.assertTrue(payload.get("deprecation_note"))
                self.assertEqual(runtime.default_cwd, runtime.workspace.root)
                self.assertEqual(payload["default_cwd"], runtime.default_cwd_display())
            finally:
                runtime.close()

    def test_get_default_cwd_returns_workspace_root_and_deprecation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            try:
                payload = runtime.get_default_cwd({})
                self.assertTrue(payload.get("deprecated"))
                self.assertEqual(str(payload["workspace"]), str(runtime.workspace.root))
            finally:
                runtime.close()

    def test_smart_surface_does_not_expose_default_cwd_tools(self) -> None:
        with tempfile.TemporaryDirectory() as temp, patch.dict(
            "os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}
        ):
            runtime = Runtime(Path(temp))
            try:
                names = runtime.exposed_tool_names()
                self.assertEqual(len(names), 8)
                self.assertNotIn("get_default_cwd", names)
                self.assertNotIn("set_default_cwd", names)
            finally:
                runtime.close()


if __name__ == "__main__":
    unittest.main()
