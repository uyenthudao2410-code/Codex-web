from __future__ import annotations

import http.client
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from coding_tools_mcp.errors import ToolFailure
from coding_tools_mcp.protocol import PROTOCOL_VERSION
from coding_tools_mcp.server import MCPHandler, Runtime, RuntimeHTTPServer
from coding_tools_mcp.task_state import TaskStateStore


class OperatorReportIsolationTests(unittest.TestCase):
    def test_read_only_audit_preserves_acknowledged_terminal_report_latch(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
            runtime = Runtime(root, permission_mode="dangerous")
            try:
                result = runtime.agent_workflow({
                    "workflow": "bugfix",
                    "phase": "execute",
                    "objective": "accepted audit latch fixture",
                    "evaluation": {"provenance": "benchmark"},
                    "patch": "*** Begin Patch\n*** Update File: app.py\n@@\n-VALUE = 1\n+VALUE = 2\n*** End Patch",
                    "verification": "none",
                    "include_diff": False,
                })
                run_id = result["orchestration"]["run_id"]
                accepted = runtime.task_control({
                    "action": "accept",
                    "run_id": run_id,
                    "reason": "fixture accepts proven terminal wave",
                })
                self.assertTrue(accepted["accepted"])
                pending = runtime.task_state.pending_completion_report()
                self.assertIsNotNone(pending)
                report_id = str(pending["report_id"])

                acknowledged = runtime.task_control({"action": "ack", "message_id": report_id})
                self.assertTrue(acknowledged["acknowledged"])
                self.assertIsNone(runtime.task_state.pending_completion_report())

                audit = runtime.task_control({"action": "audit", "run_id": run_id, "limit": 20})
                self.assertEqual(audit["completion_report"]["accepted_or_not"], "ACCEPTED")
                after = runtime.task_state.get()
                self.assertEqual(after["completion_report_id"], report_id)
                self.assertEqual(after["completion_report_acknowledged_id"], report_id)
                self.assertIsNone(runtime.task_state.pending_completion_report())
            finally:
                runtime.close()

    def test_historical_audit_cannot_replace_current_operator_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
            runtime = Runtime(root, permission_mode="dangerous")
            try:
                first = runtime.agent_workflow({
                    "workflow": "bugfix",
                    "phase": "execute",
                    "objective": "first accepted run",
                    "evaluation": {"provenance": "benchmark"},
                    "patch": "*** Begin Patch\n*** Update File: app.py\n@@\n-VALUE = 1\n+VALUE = 2\n*** End Patch",
                    "verification": "none",
                    "include_diff": False,
                })
                first_run_id = first["orchestration"]["run_id"]
                runtime.task_control({
                    "action": "accept",
                    "run_id": first_run_id,
                    "reason": "fixture accepts first run",
                })
                first_pending = runtime.task_state.pending_completion_report()
                self.assertIsNotNone(first_pending)
                runtime.task_control({
                    "action": "update",
                    "payload": {
                        "extension": "operator_report_ack_v1",
                        "report_id": first_pending["report_id"],
                    },
                })
                runtime.task_control({"action": "start", "objective": "second accepted run"})

                second = runtime.agent_workflow({
                    "workflow": "bugfix",
                    "phase": "execute",
                    "objective": "second accepted run",
                    "evaluation": {"provenance": "benchmark"},
                    "patch": "*** Begin Patch\n*** Update File: app.py\n@@\n-VALUE = 2\n+VALUE = 3\n*** End Patch",
                    "verification": "none",
                    "include_diff": False,
                })
                second_run_id = second["orchestration"]["run_id"]
                runtime.task_control({
                    "action": "accept",
                    "run_id": second_run_id,
                    "reason": "fixture accepts second run",
                })
                before = runtime.task_state.get()
                current_report_id = before["completion_report_id"]
                self.assertEqual(
                    before["completion_report"]["source_run_wave"]["run_id"],
                    second_run_id,
                )

                historical = runtime.task_control({
                    "action": "audit",
                    "run_id": first_run_id,
                    "limit": 20,
                })
                self.assertEqual(
                    historical["completion_report"]["source_run_wave"]["run_id"],
                    first_run_id,
                )
                historical_report_id = TaskStateStore._completion_report_id(
                    historical["completion_report"]
                )
                after = runtime.task_state.get()
                self.assertEqual(after["completion_report_id"], current_report_id)
                self.assertEqual(
                    after["completion_report"]["source_run_wave"]["run_id"],
                    second_run_id,
                )
                self.assertEqual(
                    runtime.task_state.pending_completion_report()["report_id"],
                    current_report_id,
                )

                with self.assertRaises(ToolFailure) as stale_ack:
                    runtime.task_control({
                        "action": "update",
                        "payload": {
                            "extension": "operator_report_ack_v1",
                            "report_id": historical_report_id,
                        },
                    })
                self.assertEqual(stale_ack.exception.code, "OPERATOR_REPORT_ACK_INVALID")
                acknowledged = runtime.task_control({
                    "action": "update",
                    "payload": {
                        "extension": "operator_report_ack_v1",
                        "report_id": current_report_id,
                    },
                })
                self.assertTrue(acknowledged["acknowledged"])
                started = runtime.task_control({"action": "start", "objective": "third task"})
                self.assertEqual(started["state"]["objective"], "third task")
            finally:
                runtime.close()

    def test_operator_report_latch_blocks_replacement_until_exact_ack(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            try:
                runtime.task_state.update({"objective": "terminal command", "status": "active"})
                runtime.task_state.record_command_started("delivery-helper", "command-delivery", ".")
                payload = {
                    "ok": True,
                    "status": "exited",
                    "command_id": "command-delivery",
                    "session_id": "command-delivery",
                    "exit_code": 0,
                    "elapsed_ms": 7,
                }
                runtime._record_task_tool_result(
                    "command_control",
                    {"action": "poll", "command_id": "command-delivery"},
                    payload,
                )
                pending = runtime.task_state.pending_completion_report()
                self.assertIsNotNone(pending)
                report_id = str(pending["report_id"])

                for args in (
                    {"action": "start", "objective": "replacement"},
                    {"action": "clear"},
                    {"action": "resume", "next_step": "unsafe"},
                    {"action": "update", "current_step": "hide report"},
                ):
                    with self.assertRaises(ToolFailure) as blocked:
                        runtime.task_control(args)
                    self.assertEqual(blocked.exception.code, "OPERATOR_REPORT_ACK_REQUIRED")

                with self.assertRaises(ToolFailure) as blocked_workflow:
                    runtime.agent_workflow({
                        "workflow": "diagnose",
                        "phase": "prepare",
                        "objective": "must report first",
                        "execution_mode": "mcp_only",
                        "verification": "none",
                    })
                self.assertEqual(blocked_workflow.exception.code, "OPERATOR_REPORT_ACK_REQUIRED")

                with self.assertRaises(ToolFailure) as wrong_ack:
                    runtime.task_control({
                        "action": "update",
                        "payload": {"extension": "operator_report_ack_v1", "report_id": "wrong"},
                    })
                self.assertEqual(wrong_ack.exception.code, "OPERATOR_REPORT_ACK_INVALID")

                with self.assertRaises(ToolFailure) as wrong_legacy_ack:
                    runtime.task_control({"action": "ack", "message_id": "wrong"})
                self.assertEqual(wrong_legacy_ack.exception.code, "MESSAGE_NOT_FOUND")

                acknowledged = runtime.task_control({"action": "ack", "message_id": report_id})
                self.assertTrue(acknowledged["acknowledged"])
                self.assertEqual(acknowledged["acknowledgement_type"], "operator_completion_report")
                self.assertIsNone(runtime.task_state.pending_completion_report())
                repeated = runtime.task_control({"action": "ack", "message_id": report_id})
                self.assertTrue(repeated["acknowledged"])
                self.assertEqual(repeated["report_id"], report_id)
                started = runtime.task_control({"action": "start", "objective": "replacement"})
                self.assertEqual(started["state"]["objective"], "replacement")
            finally:
                runtime.close()

    def test_eocl_task_ignores_foreign_and_unowned_command_projection(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            try:
                runtime.task_state.update({
                    "objective": "owned task",
                    "status": "active",
                    "orchestration": {
                        "orchestration_state": "EXECUTING",
                        "run_id": "run-a",
                        "wave_id": "wave-a",
                    },
                })
                runtime.task_state.record_command_started(
                    "foreign", "foreign", ".", owner_run_id="run-b", owner_wave_id="wave-b"
                )
                self.assertIsNone(runtime.task_state.get()["current_command"])
                runtime.task_state.record_command_started("unowned", "unowned", ".")
                self.assertIsNone(runtime.task_state.get()["current_command"])
                runtime.task_state.record_command_started(
                    "owned", "owned", ".", owner_run_id="run-a", owner_wave_id="wave-a"
                )
                self.assertEqual(runtime.task_state.get()["current_command"]["session_id"], "owned")

                runtime._record_task_tool_result(
                    "exec_command",
                    {"cmd": "foreign-result"},
                    {
                        "ok": True,
                        "status": "exited",
                        "exit_code": 0,
                        "session_id": "foreign-result",
                        "execution_owner": {"run_id": "run-b", "wave_id": "wave-b"},
                    },
                )
                self.assertIsNone(runtime.task_state.get()["last_command_result"])
            finally:
                runtime.close()

    def test_preinitialize_compatibility_sessions_are_same_root_but_task_isolated(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with patch.dict(os.environ, {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}):
                runtime = Runtime(root, transport="http")
            server = RuntimeHTTPServer(("127.0.0.1", 0), MCPHandler, runtime, runtime_factory=None)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            port = int(server.server_address[1])
            try:
                status, headers_a, body_a = self._post(port, {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}})
                self.assertEqual(status, 200, body_a)
                status, headers_b, body_b = self._post(port, {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
                self.assertEqual(status, 200, body_b)
                session_a = headers_a.get("mcp-session-id", "")
                session_b = headers_b.get("mcp-session-id", "")
                self.assertTrue(session_a.startswith("ws1."), session_a)
                self.assertTrue(session_b.startswith("ws1."), session_b)
                self.assertNotEqual(session_a, session_b)
                self.assertEqual(server.sessions.stats()["execution_contexts"], 2)

                result_a = self._prepare(port, session_a, 3, "compat-a")
                result_b = self._prepare(port, session_b, 4, "compat-b")
                self.assertNotEqual(result_a["orchestration"]["run_id"], result_b["orchestration"]["run_id"])
                state_a = self._task_get(port, session_a, 5)
                state_b = self._task_get(port, session_b, 6)
                self.assertEqual(state_a["objective"], "compat-a")
                self.assertEqual(state_b["objective"], "compat-b")
                self.assertNotEqual(state_a["task_id"], state_b["task_id"])
                self.assertEqual(len(runtime.exposed_tool_names()), 8)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)
                self.assertFalse(thread.is_alive())

    @staticmethod
    def _post(port: int, payload: dict, *, session_id: str = "") -> tuple[int, dict[str, str], dict]:
        headers = {"Content-Type": "application/json"}
        if session_id:
            headers["Mcp-Session-Id"] = session_id
            headers["MCP-Protocol-Version"] = PROTOCOL_VERSION
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        try:
            connection.request("POST", "/mcp", body=json.dumps(payload).encode("utf-8"), headers=headers)
            response = connection.getresponse()
            raw = response.read()
            body = json.loads(raw.decode("utf-8")) if raw else {}
            return response.status, {key.lower(): value for key, value in response.getheaders()}, body
        finally:
            connection.close()

    def _prepare(self, port: int, session_id: str, request_id: int, objective: str) -> dict:
        status, _headers, body = self._post(
            port,
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": "tools/call",
                "params": {
                    "name": "agent_workflow",
                    "arguments": {
                        "workflow": "diagnose",
                        "phase": "prepare",
                        "objective": objective,
                        "execution_route": "deterministic",
                        "execution_mode": "mcp_only",
                        "verification": "none",
                    },
                },
            },
            session_id=session_id,
        )
        self.assertEqual(status, 200, body)
        self.assertFalse(body["result"]["isError"], body)
        return body["result"]["structuredContent"]

    def _task_get(self, port: int, session_id: str, request_id: int) -> dict:
        status, _headers, body = self._post(
            port,
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": "tools/call",
                "params": {"name": "task_control", "arguments": {"action": "get"}},
            },
            session_id=session_id,
        )
        self.assertEqual(status, 200, body)
        self.assertFalse(body["result"]["isError"], body)
        return body["result"]["structuredContent"]["state"]


if __name__ == "__main__":
    unittest.main()
