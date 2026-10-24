"""Cluster B — ``input_id`` on the MCP wire for the job-input contract.

W5 (``tests/test_job_input.py``) proved the ledger and the internal
``write_stdin`` handler. This suite proves the wire level that W5 left
closed: a real MCP caller goes through the server's own dispatch
(``Runtime.call_tool`` -> ``validate_arguments`` -> handler), so
``input_id`` must be declared in the tool schemas, survive the
``additionalProperties=false`` validator, reach
``SessionControlMixin.write_stdin``, and come back as a typed
``input_receipt`` — for both write paths that exist on the wire:

- ``command_control`` (public smart-v3 facade, action ``write``), and
- ``write_stdin`` (internal tool; callable in smart mode through the
  SMART_COMPAT set).

``exec_command`` deliberately has no ``input_id``: its ``stdin`` is the
initial input of a brand-new command whose session id the caller cannot
know in advance, so per-write dedupe cannot key on it; the operation
level ``idempotency_key`` already covers that call.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

from coding_tools_mcp.errors import JsonRpcError
from coding_tools_mcp.job_input import OUTCOME_DELIVERED, OUTCOME_UNKNOWN
from coding_tools_mcp.processes import ExecSession
from coding_tools_mcp.server import Runtime
from coding_tools_mcp.tool_schema import input_schemas, validate_arguments

INPUT_ID_DESCRIPTION_SNIPPETS = ("idempotency", "duplicate=true")


class _RecordingStdin:
    """A process stdin that records writes and can fail mid-write."""

    def __init__(self, fail: bool = False) -> None:
        self.closed = False
        self.fail = fail
        self.writes: list[bytes] = []
        self.attempts = 0

    def write(self, data: bytes) -> int:
        self.attempts += 1
        if self.fail:
            raise BrokenPipeError("pipe gone mid-write")
        self.writes.append(bytes(data))
        return len(data)

    def flush(self) -> None:
        pass


class _FakeProcess:
    def __init__(self, stdin: _RecordingStdin) -> None:
        self.stdin = stdin
        self.exited = False

    def poll(self):  # noqa: ANN202 - mirrors subprocess.Popen.poll
        return 0 if self.exited else None


class JobInputWireTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self._env = patch.dict("os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"})
        self._env.start()
        self.runtime = Runtime(Path(self._temp.name), permission_mode="safe")
        self._processes: list[_FakeProcess] = []

    def tearDown(self) -> None:
        for process in self._processes:
            process.exited = True
        self.runtime.close()
        self._env.stop()
        self._temp.cleanup()

    # -- fixtures ---------------------------------------------------------

    def _add_session(self, session_id: str, *, fail: bool = False) -> _RecordingStdin:
        stdin = _RecordingStdin(fail=fail)
        process = _FakeProcess(stdin)
        self._processes.append(process)
        session = ExecSession(session_id, process)  # type: ignore[arg-type]
        with self.runtime.sessions_lock:
            self.runtime.sessions[session_id] = session
        return stdin

    def _call(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        result = self.runtime.call_tool(name, args)
        return result["structuredContent"]

    def _command_write(self, session_id: str, **overrides: Any) -> dict[str, Any]:
        args: dict[str, Any] = {
            "action": "write",
            "command_id": session_id,
            "chars": "hello\n",
            "yield_time_ms": 0,
        }
        args.update(overrides)
        return self._call("command_control", args)

    def _write_stdin(self, session_id: str, **overrides: Any) -> dict[str, Any]:
        args: dict[str, Any] = {
            "session_id": session_id,
            "chars": "hello\n",
            "yield_time_ms": 0,
        }
        args.update(overrides)
        return self._call("write_stdin", args)

    # -- schema declaration ------------------------------------------------

    def test_schema_declares_optional_input_id_on_both_write_paths(self) -> None:
        schemas = input_schemas()
        for tool in ("command_control", "write_stdin"):
            with self.subTest(tool=tool):
                schema = schemas[tool]
                self.assertFalse(schema["additionalProperties"])
                self.assertNotIn("input_id", schema["required"])
                prop = schema["properties"]["input_id"]
                self.assertEqual(prop["type"], "string")
                self.assertEqual(prop["maxLength"], 128)
                for snippet in INPUT_ID_DESCRIPTION_SNIPPETS:
                    self.assertIn(snippet, prop["description"])
        # exec_command keeps no input_id (see module docstring).
        self.assertNotIn("input_id", schemas["exec_command"]["properties"])
        # The public smart-v3 surface is still exactly the same 8 tools.
        self.assertEqual(
            set(self.runtime.exposed_tool_names()),
            {
                "workspace_context", "agent_workflow", "task_control",
                "document_workflow", "exec_command", "command_control",
                "request_permissions", "view_image",
            },
        )

    def test_validate_arguments_accepts_input_id_at_the_boundary(self) -> None:
        validate_arguments(
            "command_control",
            {"action": "write", "command_id": "s", "chars": "x", "input_id": "i" * 128},
        )
        validate_arguments(
            "write_stdin",
            {"session_id": "s", "chars": "x", "input_id": "i" * 128},
        )

    # -- (a) + (b): delivered exactly once, duplicate reconciles -----------

    def test_command_control_wire_write_delivers_once_then_duplicate(self) -> None:
        stdin = self._add_session("wire-cc-1")
        first = self._command_write("wire-cc-1", input_id="in-wire-1")
        receipt = first["input_receipt"]
        self.assertEqual(receipt["outcome"], OUTCOME_DELIVERED)
        self.assertFalse(receipt["duplicate"])
        self.assertEqual(receipt["input_id"], "in-wire-1")
        self.assertEqual(receipt["session_id"], "wire-cc-1")
        self.assertEqual(stdin.writes, [b"hello\n"])

        second = self._command_write("wire-cc-1", input_id="in-wire-1")
        self.assertTrue(second["input_receipt"]["duplicate"])
        self.assertEqual(second["input_receipt"]["outcome"], OUTCOME_DELIVERED)
        self.assertEqual(len(stdin.writes), 1, "duplicate input_id must not write again")

    def test_write_stdin_tool_wire_write_delivers_once_then_duplicate(self) -> None:
        stdin = self._add_session("wire-ws-1")
        first = self._write_stdin("wire-ws-1", input_id="in-wire-1")
        self.assertEqual(first["input_receipt"]["outcome"], OUTCOME_DELIVERED)
        self.assertFalse(first["input_receipt"]["duplicate"])
        self.assertEqual(stdin.writes, [b"hello\n"])

        second = self._write_stdin("wire-ws-1", input_id="in-wire-1")
        self.assertTrue(second["input_receipt"]["duplicate"])
        self.assertEqual(len(stdin.writes), 1, "duplicate input_id must not write again")

    # -- (c): mid-write failure -> unknown, never replayed ------------------

    def test_failed_wire_write_is_unknown_and_retry_never_replays(self) -> None:
        stdin = self._add_session("wire-fail-1", fail=True)
        result = self.runtime.call_tool(
            "command_control",
            {
                "action": "write",
                "command_id": "wire-fail-1",
                "chars": "hello\n",
                "yield_time_ms": 0,
                "input_id": "in-fail-1",
            },
        )
        self.assertTrue(result["isError"])
        error = result["structuredContent"]["error"]
        self.assertEqual(error["code"], "JOB_INPUT_OUTCOME_UNKNOWN")
        receipt = error["details"]["input_receipt"]
        self.assertEqual(receipt["outcome"], OUTCOME_UNKNOWN)
        self.assertFalse(receipt["duplicate"])
        self.assertEqual(stdin.attempts, 1)

        retry = self.runtime.call_tool(
            "command_control",
            {
                "action": "write",
                "command_id": "wire-fail-1",
                "chars": "hello\n",
                "yield_time_ms": 0,
                "input_id": "in-fail-1",
            },
        )
        self.assertTrue(retry["isError"])
        retry_receipt = retry["structuredContent"]["error"]["details"]["input_receipt"]
        self.assertEqual(retry_receipt["outcome"], OUTCOME_UNKNOWN)
        self.assertTrue(retry_receipt["duplicate"])
        self.assertEqual(stdin.attempts, 1, "unknown outcome must never auto-replay")
        stored = self.runtime.job_input_receipt("wire-fail-1", "in-fail-1")
        self.assertEqual(stored["outcome"], OUTCOME_UNKNOWN)

    # -- (d): invalid input_id is rejected at the schema layer --------------

    def test_invalid_input_id_rejected_at_schema(self) -> None:
        too_long = "x" * 129
        for tool, base in (
            ("command_control", {"action": "write", "command_id": "s", "chars": "x"}),
            ("write_stdin", {"session_id": "s", "chars": "x"}),
        ):
            with self.subTest(tool=tool, case="too_long"):
                with self.assertRaises(JsonRpcError):
                    validate_arguments(tool, {**base, "input_id": too_long})
            with self.subTest(tool=tool, case="non_string"):
                with self.assertRaises(JsonRpcError):
                    validate_arguments(tool, {**base, "input_id": 123})
            with self.subTest(tool=tool, case="unknown_property_still_rejected"):
                with self.assertRaises(JsonRpcError):
                    validate_arguments(tool, {**base, "input_id": "ok", "bogus": 1})

        # Through the real dispatch the rejection happens before any write.
        stdin = self._add_session("wire-invalid-1")
        with self.assertRaises(JsonRpcError):
            self.runtime.call_tool(
                "command_control",
                {
                    "action": "write",
                    "command_id": "wire-invalid-1",
                    "chars": "hello\n",
                    "yield_time_ms": 0,
                    "input_id": too_long,
                },
            )
        self.assertEqual(stdin.attempts, 0)

    # -- (e): no input_id -> legacy behavior unchanged -----------------------

    def test_wire_write_without_input_id_keeps_legacy_behavior(self) -> None:
        stdin = self._add_session("wire-legacy-1")
        first = self._command_write("wire-legacy-1")
        self.assertNotIn("input_receipt", first)
        second = self._command_write("wire-legacy-1")
        self.assertNotIn("input_receipt", second)
        self.assertEqual(stdin.writes, [b"hello\n", b"hello\n"])

        stdin2 = self._add_session("wire-legacy-2")
        payload = self._write_stdin("wire-legacy-2")
        self.assertNotIn("input_receipt", payload)
        self.assertEqual(stdin2.writes, [b"hello\n"])

    def test_empty_input_id_is_the_legacy_absent_sentinel(self) -> None:
        # The validator does not forbid an empty input_id: by the W5
        # handler convention (and the idempotency_key/consumer_id
        # precedent) an empty value means "no receipted write".
        stdin = self._add_session("wire-empty-1")
        payload = self._command_write("wire-empty-1", input_id="")
        self.assertNotIn("input_receipt", payload)
        self.assertEqual(stdin.writes, [b"hello\n"])


if __name__ == "__main__":
    unittest.main()
