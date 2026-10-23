from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from coding_tools_mcp.patching import apply_update_hunks, parse_patch
from coding_tools_mcp.processes import ExecSession
from coding_tools_mcp.protocol import dispatch_rpc
from coding_tools_mcp.server import Runtime
from coding_tools_mcp.tool_results import make_tool_result
from coding_tools_mcp.errors import ToolFailure


class PatchFidelityTests(unittest.TestCase):
    def test_patch_parser_splits_only_literal_lf(self) -> None:
        separators = "alpha\x0cbeta\x85gamma\u2028delta\u2029omega"
        operations = parse_patch(
            "*** Begin Patch\n"
            "*** Add File: exact.txt\n"
            f"+{separators}\n"
            "*** End Patch\n"
        )
        self.assertEqual(len(operations), 1)
        self.assertEqual(operations[0].add_content, separators + "\n")

    def test_update_preserves_non_lf_codepoints_and_trailing_newline(self) -> None:
        prefix = "alpha\x0cbeta\x85gamma\u2028delta\u2029omega"
        original = prefix + "\nTARGET = 1\n"
        updated = apply_update_hunks(original, [["-TARGET = 1", "+TARGET = 2"]], "exact.txt")
        self.assertEqual(updated, prefix + "\nTARGET = 2\n")

    def test_update_preserves_absent_trailing_newline_and_crlf(self) -> None:
        self.assertEqual(
            apply_update_hunks("TARGET = 1", [["-TARGET = 1", "+TARGET = 2"]]),
            "TARGET = 2",
        )
        self.assertEqual(
            apply_update_hunks("A\r\nTARGET = 1\r\n", [["-TARGET = 1", "+TARGET = 2"]]),
            "A\r\nTARGET = 2\r\n",
        )


class ModelFacingErrorTests(unittest.TestCase):
    def test_terminal_error_tells_model_not_to_repeat_unchanged(self) -> None:
        result = make_tool_result(
            "write_stdin",
            {
                "ok": False,
                "error": {
                    "code": "COMMAND_NOT_FOUND",
                    "message": "Command session was not found.",
                    "category": "not_found",
                    "retryable": False,
                    "details": {},
                },
            },
            is_error=True,
        )
        text = result["content"][-1]["text"]
        self.assertIn("COMMAND_NOT_FOUND: Command session was not found.", text)
        self.assertIn("Category: not_found.", text)
        self.assertIn("Retryable: no.", text)
        self.assertIn("Do not repeat this call unchanged.", text)

    def test_retryable_error_surfaces_hint_without_terminal_instruction(self) -> None:
        result = make_tool_result(
            "apply_patch",
            {
                "ok": False,
                "error": {
                    "code": "PATCH_CONTEXT_NOT_FOUND",
                    "message": "Patch context changed.",
                    "category": "validation",
                    "retryable": True,
                    "details": {"retry_hint": "Read the file again and regenerate the hunk."},
                },
            },
            is_error=True,
        )
        text = result["content"][-1]["text"]
        self.assertIn("Category: validation.", text)
        self.assertIn("Retryable: yes.", text)
        self.assertIn("Retry: Read the file again and regenerate the hunk.", text)
        self.assertNotIn("Do not repeat this call unchanged.", text)


class OutputRetentionTests(unittest.TestCase):
    def test_head_and_tail_survive_middle_eviction_with_metrics(self) -> None:
        process = MagicMock()
        session = ExecSession("session-1", process, buffer_limit=64)
        payload = b"ROOTERR!" + (b"m" * 100) + b"FINAL"
        session.append_stdout(payload)

        retained = session.retained_output_bytes()
        metrics = session.retained_stream_metrics("stdout")
        self.assertIn(b"ROOTERR!", retained)
        self.assertIn(b"FINAL", retained)
        self.assertIn(b"evicted from middle", retained)
        self.assertEqual(metrics["head_retained_bytes"], 8)
        self.assertEqual(metrics["total_retained_bytes"], 64)
        self.assertGreater(metrics["evicted_gap_bytes"], 0)
        self.assertGreater(metrics["evict_events"], 0)
        self.assertEqual(metrics["evicted_bytes_total"], metrics["evicted_gap_bytes"])

        head_page = session.retained_stream_window("stdout", 0, 64)
        self.assertEqual(head_page["data"], b"ROOTERR!")
        self.assertEqual(head_page["next_offset"], metrics["tail_start_offset"])
        self.assertEqual(head_page["omitted_bytes"], metrics["evicted_gap_bytes"])

        tail_page = session.retained_stream_window(
            "stdout", int(head_page["next_offset"]), 64
        )
        self.assertTrue(tail_page["data"].endswith(b"FINAL"))


class MultiConsumerCursorTests(unittest.TestCase):
    def test_consumers_observe_command_output_independently(self) -> None:
        process = MagicMock()
        process.poll.return_value = None
        session = ExecSession("session-consumers", process, buffer_limit=128)
        session.append_stdout(b"first")
        a1 = session.snapshot_since_cursor(4096, consumer_id="chatweb")
        b1 = session.snapshot_since_cursor(4096, consumer_id="supervisor")
        self.assertEqual(a1["stdout"], "first")
        self.assertEqual(b1["stdout"], "first")
        self.assertEqual(session.snapshot_since_cursor(4096, consumer_id="chatweb")["stdout"], "")
        session.append_stdout(b"-second")
        self.assertEqual(session.snapshot_since_cursor(4096, consumer_id="chatweb")["stdout"], "-second")
        self.assertEqual(session.snapshot_since_cursor(4096, consumer_id="supervisor")["stdout"], "-second")


class ProtocolRegressionTests(unittest.TestCase):
    def test_duplicate_initialize_requests_are_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temp, patch.dict(
            "os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}
        ):
            runtime = Runtime(Path(temp))
            request = {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": runtime.protocol_version,
                    "clientInfo": {"name": "sdk-smoke", "version": "1"},
                },
            }
            first = dispatch_rpc(runtime, {**request, "id": 1})
            second = dispatch_rpc(runtime, {**request, "id": 0})
            self.assertIsNotNone(first)
            self.assertIsNotNone(second)
            assert first is not None and second is not None
            self.assertIn("result", first)
            self.assertIn("result", second)
            self.assertEqual(second["id"], 0)
            self.assertEqual(len(runtime.exposed_tool_names()), 8)
            runtime.close()


class CommandHandleMigrationTests(unittest.TestCase):
    def test_control_plane_structured_argv_requires_attested_bridge_identity(self) -> None:
        try:
            temporary_workspace = tempfile.TemporaryDirectory(dir=str(Path(__file__).resolve().anchor))
        except OSError as error:
            self.skipTest(f"The Windows drive root is not writable for the isolated sandbox fixture: {error}")
        with temporary_workspace as temp:
            # The admission assertion is platform-neutral; use the explicit
            # dangerous fixture mode so Linux's standalone Landlock helper is
            # not part of this bridge-identity test.
            runtime = Runtime(Path(temp), permission_mode="dangerous")
            try:
                with self.assertRaises(Exception) as denied:
                    runtime.exec_command({
                        "cmd": "echo",
                        "argv": ["echo", "must-not-run"],
                        "yield_time_ms": 1000,
                    })
                # On Windows the denial can arrive from either of two
                # designed pre-execution guards, depending on the host
                # token posture seen by the production path (observed to
                # differ across GitHub runner allocations): the
                # native-token guard on an elevated/high-integrity host,
                # or the bridge-identity check itself. Both are the
                # correct fail-closed outcome; the security property is
                # that execution never proceeds unattested.
                allowed_denials = {"CONTROL_PLANE_STRUCTURED_ARGV_DENIED"}
                if os.name == "nt":
                    allowed_denials.add("NATIVE_ELEVATED_HOST_DENIED")
                self.assertIn(
                    getattr(denied.exception, "code", ""),
                    allowed_denials,
                )
                if os.name == "nt":
                    # The attested half exercises native argv execution,
                    # which by design cannot run on an elevated /
                    # high-integrity host (the native-token guard inside
                    # the MXC invocation builder denies it). Which guard
                    # fired on the FIRST call depends on call shape, so
                    # gate the second half on the host posture itself:
                    # on an elevated host the denial asserted above is
                    # the complete correct outcome for this test.
                    from coding_tools_mcp.processes import windows_host_token_posture

                    posture = windows_host_token_posture()
                    if posture["elevated"] or posture["integrity_rid"] > 0x2000:
                        return

                runtime.request_context.hub_client = {
                    "client_id": "electron-control-plane-exec-bridge",
                    "client_type": "electron",
                    "attestation_verified": True,
                }
                with patch("coding_tools_mcp.exec_tools.is_sandboxed_execution", return_value=True), \
                     patch("coding_tools_mcp.exec_tools.windows_sandbox_feature_enabled", return_value=False):
                    payload = runtime.exec_command({
                        "cmd": "node",
                        "argv": ["node", "-e", "console.log('bridge-argv-ok')"],
                        "_windows_native_argv_prefixes": [["node", "-e"]],
                        "yield_time_ms": 1000,
                        "max_output_bytes": 4096,
                        "verbosity": "full",
                    })
                    # MXC preparation can consume the initial yield budget;
                    # running is an observation of this command, not a retry.
                    stdout = str(payload.get("stdout") or "")
                    command_id = str(payload["command_id"])
                    for _ in range(30):
                        if payload["status"] != "running":
                            break
                        payload = runtime.write_stdin({
                            "command_id": command_id,
                            "chars": "",
                            "yield_time_ms": 1000,
                            "max_output_bytes": 4096,
                            "verbosity": "full",
                        })
                        stdout += str(payload.get("stdout") or "")
                    self.assertEqual(payload["status"], "exited")
                    self.assertEqual(payload["exit_code"], 0)
                    self.assertIn("bridge-argv-ok", stdout)
                if sys.platform == "win32":
                    self.assertTrue(any(
                        "temporary system-drive junction" in str(warning)
                        for warning in payload.get("warnings", [])
                    ))
            finally:
                runtime.close()

    # Simulates the Windows MXC preflight by patching os.name; other
    # platform checks in the exec path follow the real host, so the
    # scenario is only faithful on a Windows host.
    @unittest.skipUnless(os.name == "nt", "Windows MXC preflight simulation requires a Windows host")
    def test_control_plane_structured_argv_fails_closed_when_mxc_preflight_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp), permission_mode="dangerous")
            try:
                runtime.request_context.hub_client = {
                    "client_id": "electron-control-plane-exec-bridge",
                    "client_type": "electron",
                    "attestation_verified": True,
                }
                with (
                    patch("coding_tools_mcp.exec_tools.os.name", "nt"),
                    patch("coding_tools_mcp.exec_tools.is_sandboxed_execution", return_value=True),
                    patch("coding_tools_mcp.exec_tools.windows_sandbox_feature_enabled", return_value=False),
                    patch("coding_tools_mcp.exec_tools.build_mxc_invocation", side_effect=ToolFailure(
                        "SANDBOX_UNAVAILABLE",
                        "BaseContainer test fixture unavailable.",
                        category="security",
                    )),
                    patch("coding_tools_mcp.exec_tools.processes.spawn_process") as spawn,
                ):
                    with self.assertRaises(Exception) as denied:
                        runtime.exec_command({
                            "cmd": "node",
                            "argv": ["node", "--version"],
                            "yield_time_ms": 1000,
                        })
                self.assertEqual(getattr(denied.exception, "code", ""), "SANDBOX_UNAVAILABLE")
                spawn.assert_not_called()
            finally:
                runtime.close()

    def test_exec_returns_command_id_and_canonical_command_output_refs(self) -> None:
        with tempfile.TemporaryDirectory() as temp, patch.dict(
            "os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}
        ):
            runtime = Runtime(Path(temp))
            try:
                payload = runtime.exec_command({
                    "cmd": "echo command-id-ok",
                    "yield_time_ms": 1000,
                    "max_output_bytes": 4096,
                    "verbosity": "full",
                })
                self.assertEqual(payload["command_id"], payload["session_id"])
                self.assertTrue(payload["output_refs"]["stdout"].startswith("command:"))
                self.assertTrue(payload["legacy_output_refs"]["stdout"].startswith("session:"))

                read = runtime.command_control({
                    "action": "read",
                    "output_ref": payload["output_refs"]["stdout"],
                    "offset": 0,
                    "limit": 4096,
                })
                self.assertEqual(read["command_id"], payload["command_id"])
                self.assertIn("command-id-ok", read["content"])

                legacy = runtime.command_control({
                    "action": "read",
                    "output_ref": payload["legacy_output_refs"]["stdout"],
                    "offset": 0,
                    "limit": 4096,
                })
                self.assertEqual(legacy["command_id"], payload["command_id"])
            finally:
                runtime.close()

    def test_command_control_accepts_preferred_command_id_and_rejects_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            try:
                payload = runtime.exec_command({
                    "cmd": "echo poll-by-command-id",
                    "yield_time_ms": 1000,
                    "max_output_bytes": 4096,
                    "verbosity": "full",
                })
                polled = runtime.command_control({
                    "action": "poll",
                    "command_id": payload["command_id"],
                    "yield_time_ms": 0,
                    "max_output_bytes": 4096,
                    "verbosity": "full",
                })
                self.assertEqual(polled["command_id"], payload["command_id"])
                with self.assertRaises(Exception) as conflict:
                    runtime.command_control({
                        "action": "poll",
                        "command_id": "preferred",
                        "session_id": "different-legacy",
                    })
                self.assertIn("different commands", str(conflict.exception))
            finally:
                runtime.close()

    def test_legacy_session_alias_usage_is_counted_for_deprecation_telemetry(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            try:
                self.assertEqual(runtime.legacy_session_alias_uses, 0)
                payload = runtime.exec_command({
                    "cmd": "echo alias-telemetry",
                    "yield_time_ms": 1000,
                    "max_output_bytes": 4096,
                    "verbosity": "full",
                })
                runtime.command_control({
                    "action": "poll",
                    "command_id": payload["command_id"],
                    "yield_time_ms": 0,
                    "max_output_bytes": 4096,
                    "verbosity": "full",
                })
                self.assertEqual(runtime.legacy_session_alias_uses, 0)
                runtime.command_control({
                    "action": "poll",
                    "session_id": payload["command_id"],
                    "yield_time_ms": 0,
                    "max_output_bytes": 4096,
                    "verbosity": "full",
                })
                self.assertEqual(runtime.legacy_session_alias_uses, 1)
            finally:
                runtime.close()


if __name__ == "__main__":
    unittest.main()
