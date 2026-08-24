from __future__ import annotations

import http.client
import hashlib
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from coding_tools_mcp.protocol import STATELESS_PROTOCOL_VERSION
from coding_tools_mcp.server import MCPHandler, Runtime, RuntimeHTTPServer
from coding_tools_mcp.task_state import TaskStateStore
from coding_tools_mcp.http_exception_boundary import ExceptionSafeMCPHandler


def _modern_params(value: dict) -> dict:
    return {
        **value,
        "_meta": {
            "io.modelcontextprotocol/protocolVersion": STATELESS_PROTOCOL_VERSION,
            "io.modelcontextprotocol/clientCapabilities": {},
            "io.modelcontextprotocol/clientInfo": {"name": "multi-workspace-matrix", "version": "1"},
        },
    }


class MultiWorkspaceHttpMatrixTests(unittest.TestCase):
    def _request(self, port: int, method: str, params: dict, request_id: int) -> dict:
        body = json.dumps({
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params,
        }).encode("utf-8")
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        try:
            connection.request(
                "POST",
                "/mcp",
                body=body,
                headers={
                    "Content-Type": "application/json",
                    "MCP-Protocol-Version": STATELESS_PROTOCOL_VERSION,
                    "Mcp-Method": method,
                    "Mcp-Name": str(params.get("name") or "") if method == "tools/call" else "",
                },
            )
            response = connection.getresponse()
            raw = response.read()
            self.assertEqual(response.status, 200, raw)
            return json.loads(raw.decode("utf-8"))
        finally:
            connection.close()

    def _tool(self, port: int, name: str, arguments: dict, request_id: int) -> dict:
        response = self._request(
            port,
            "tools/call",
            _modern_params({"name": name, "arguments": arguments}),
            request_id,
        )
        self.assertIn("result", response, response)
        return response["result"]

    @staticmethod
    def _server(runtime: Runtime) -> tuple[RuntimeHTTPServer, threading.Thread, int]:
        # The executable bootstrap replaces server.MCPHandler with this
        # exception wrapper.  Exercise that exact production dispatch path,
        # not only the base class imported by isolated unit tests.
        server = RuntimeHTTPServer(("127.0.0.1", 0), ExceptionSafeMCPHandler, runtime, runtime_factory=None)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server, thread, int(server.server_address[1])

    def test_public_stateless_matrix_keeps_two_workspaces_across_restart(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            primary = base / "primary"
            authorized = base / "authorized"
            primary.mkdir()
            authorized.mkdir()
            env = {
                "CODING_TOOLS_MCP_TOOL_MODE": "smart",
                "CODING_TOOLS_MCP_STATELESS_HTTP_2026": "1",
                "CODING_TOOLS_MCP_AUTHORIZED_ROOTS": json.dumps([str(authorized)]),
            }
            with patch.dict(os.environ, env):
                first_runtime = Runtime(primary, transport="http")
            first_server, first_thread, first_port = self._server(first_runtime)
            try:
                auth_context = "matrix-authorized"
                primary_context = "matrix-primary"
                auth_view = self._tool(
                    first_port,
                    "workspace_context",
                    {"task_context_id": auth_context, "path": str(authorized), "detail": "compact"},
                    1,
                )
                primary_view = self._tool(
                    first_port,
                    "workspace_context",
                    {"task_context_id": primary_context, "path": str(primary), "detail": "compact"},
                    2,
                )
                self.assertFalse(auth_view["isError"], auth_view)
                self.assertFalse(primary_view["isError"], primary_view)
                self.assertEqual(auth_view["structuredContent"]["workspace"], str(authorized.resolve()))
                self.assertEqual(primary_view["structuredContent"]["workspace"], str(primary.resolve()))
                self.assertNotEqual(
                    auth_view["structuredContent"]["workspace_id"],
                    primary_view["structuredContent"]["workspace_id"],
                )
                self.assertEqual(
                    auth_view["_meta"]["io.coding-tools/taskContextId"],
                    auth_view["structuredContent"]["task_context_id"],
                )
                registry_path = primary / ".coding-tools" / "orchestration" / "task-context-workspaces.json"
                registry = json.loads(registry_path.read_text(encoding="utf-8"))
                self.assertIn(auth_context, registry["contexts"])
                self.assertEqual(
                    registry["contexts"][auth_context]["workspace_id"],
                    auth_view["structuredContent"]["workspace_id"],
                )
                self.assertFalse(
                    any(str(key).startswith("mcp2026:") for key in registry["contexts"]),
                    registry,
                )
                wrong_workspace_context = self._tool(
                    first_port,
                    "workspace_context",
                    {"task_context_id": auth_context, "path": str(primary), "detail": "compact"},
                    8,
                )
                self.assertTrue(wrong_workspace_context["isError"], wrong_workspace_context)
                self.assertEqual(
                    wrong_workspace_context["structuredContent"]["error"]["code"],
                    "TASK_CONTEXT_WORKSPACE_MISMATCH",
                )

                auth_run_result = self._tool(
                    first_port,
                    "agent_workflow",
                    {
                        "task_context_id": auth_context,
                        "workflow": "diagnose",
                        "phase": "prepare",
                        "objective": "http-authorized-workspace-task",
                        "execution_route": "deterministic",
                        "execution_mode": "mcp_only",
                        "verification": "none",
                    },
                    3,
                )
                primary_run_result = self._tool(
                    first_port,
                    "agent_workflow",
                    {
                        "task_context_id": primary_context,
                        "workflow": "diagnose",
                        "phase": "prepare",
                        "objective": "http-primary-workspace-task",
                        "execution_route": "deterministic",
                        "execution_mode": "mcp_only",
                        "verification": "none",
                    },
                    4,
                )
                self.assertFalse(auth_run_result["isError"], auth_run_result)
                self.assertFalse(primary_run_result["isError"], primary_run_result)
                auth_run = auth_run_result["structuredContent"]["orchestration"]["run_id"]
                primary_run = primary_run_result["structuredContent"]["orchestration"]["run_id"]
                self.assertNotEqual(auth_run, primary_run)

                def task_scope(context_id: str) -> str:
                    return f"mcp2026:{context_id}"

                auth_state_before = TaskStateStore(
                    authorized, scope_id=task_scope(auth_context)
                ).get()
                primary_state_before = TaskStateStore(
                    primary, scope_id=task_scope(primary_context)
                ).get()

                wrong_context = self._tool(
                    first_port,
                    "task_control",
                    {"task_context_id": auth_context, "action": "get", "run_id": primary_run},
                    5,
                )
                self.assertTrue(wrong_context["isError"], wrong_context)
                self.assertEqual(
                    wrong_context["structuredContent"]["error"]["code"],
                    "RUN_WORKSPACE_MISMATCH",
                )
                # A rejected read-only lookup must not record a failure or
                # REPLAN in either task projection.  The HTTP boundary is the
                # important case because it owns stateless context selection.
                self.assertEqual(
                    TaskStateStore(authorized, scope_id=task_scope(auth_context)).get(),
                    auth_state_before,
                )
                self.assertEqual(
                    TaskStateStore(primary, scope_id=task_scope(primary_context)).get(),
                    primary_state_before,
                )

                # HTTP dispatch strips task_context_id from the tool arguments
                # after validating it.  The request-scoped opaque handle must
                # nevertheless resolve the bound workspace before exec_command
                # admission, so callers do not need a redundant workdir/path.
                scoped_exec = self._tool(
                    first_port,
                    "exec_command",
                    {"task_context_id": auth_context, "cmd": "python --version", "timeout_ms": 30_000},
                    9,
                )
                self.assertFalse(scoped_exec["isError"], scoped_exec)
                self.assertEqual(scoped_exec["structuredContent"]["exit_code"], 0)
            finally:
                first_server.shutdown()
                first_server.server_close()
                first_thread.join(timeout=5)
                self.assertFalse(first_thread.is_alive())
                first_runtime.close()

            with patch.dict(os.environ, env):
                second_runtime = Runtime(primary, transport="http")
            second_server, second_thread, second_port = self._server(second_runtime)
            try:
                restored = self._tool(
                    second_port,
                    "workspace_context",
                    {"task_context_id": auth_context, "detail": "compact"},
                    6,
                )
                self.assertFalse(restored["isError"], restored)
                self.assertEqual(restored["structuredContent"]["workspace"], str(authorized.resolve()))
                state = self._tool(
                    second_port,
                    "task_control",
                    {"task_context_id": auth_context, "action": "get"},
                    7,
                )
                self.assertFalse(state["isError"], state)
                self.assertEqual(
                    state["structuredContent"]["state"]["objective"],
                    "http-authorized-workspace-task",
                )

                # ``events`` must resolve the persisted opaque task context
                # before selecting an orchestration ledger.  This is the
                # restart-sensitive counterpart to the earlier ``get`` and
                # cross-workspace rejection checks: a valid authorized context
                # sees its durable event stream, while a primary context may
                # not inspect that run and must leave both projections intact.
                auth_events = self._tool(
                    second_port,
                    "task_control",
                    {"task_context_id": auth_context, "action": "events", "run_id": auth_run},
                    10,
                )
                self.assertFalse(auth_events["isError"], auth_events)
                event_rows = auth_events["structuredContent"]["events"]
                self.assertTrue(event_rows, auth_events)
                self.assertEqual(event_rows[0]["run_id"], auth_run)
                self.assertEqual(event_rows[0]["event_type"], "run_started")

                auth_state_before = TaskStateStore(
                    authorized, scope_id=task_scope(auth_context)
                ).get()
                primary_state_before = TaskStateStore(
                    primary, scope_id=task_scope(primary_context)
                ).get()
                rejected_events = self._tool(
                    second_port,
                    "task_control",
                    {"task_context_id": primary_context, "action": "events", "run_id": auth_run},
                    11,
                )
                self.assertTrue(rejected_events["isError"], rejected_events)
                self.assertEqual(
                    rejected_events["structuredContent"]["error"]["code"],
                    "RUN_WORKSPACE_MISMATCH",
                )
                self.assertEqual(
                    TaskStateStore(authorized, scope_id=task_scope(auth_context)).get(),
                    auth_state_before,
                )
                self.assertEqual(
                    TaskStateStore(primary, scope_id=task_scope(primary_context)).get(),
                    primary_state_before,
                )
            finally:
                second_server.shutdown()
                second_server.server_close()
                second_thread.join(timeout=5)
                self.assertFalse(second_thread.is_alive())
                second_runtime.close()


if __name__ == "__main__":
    unittest.main()
