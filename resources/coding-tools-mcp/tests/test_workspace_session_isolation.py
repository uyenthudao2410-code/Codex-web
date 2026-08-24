from __future__ import annotations

import http.client
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from coding_tools_mcp.protocol import PROTOCOL_VERSION
from coding_tools_mcp.server import MCPHandler, Runtime, RuntimeHTTPServer
from coding_tools_mcp.task_state import TaskStateStore


class WorkspaceSessionIsolationTests(unittest.TestCase):
    @unittest.skipUnless(os.name == "nt", "Windows canonicalization contract")
    def test_windows_case_and_separator_aliases_share_workspace_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            primary = base / "Primary"
            authorized = base / "Authorized"
            primary.mkdir()
            authorized.mkdir()
            with patch.dict(os.environ, {
                "CODING_TOOLS_MCP_TOOL_MODE": "smart",
                "CODING_TOOLS_MCP_AUTHORIZED_ROOTS": json.dumps([str(authorized)]),
            }):
                runtime = Runtime(primary)
            try:
                canonical = runtime.workspace_context({"path": str(authorized), "detail": "compact"})
                alias = str(authorized).swapcase().replace("\\", "/")
                aliased = runtime.workspace_context({"path": alias, "detail": "compact"})
                self.assertFalse(canonical.get("isError"), canonical)
                self.assertFalse(aliased.get("isError"), aliased)
                self.assertEqual(aliased["workspace"], canonical["workspace"])
                self.assertEqual(aliased["workspace_id"], canonical["workspace_id"])
            finally:
                runtime.close()

    def test_workspace_context_projects_task_state_from_requested_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            primary = base / "primary"
            authorized = base / "authorized"
            primary.mkdir()
            authorized.mkdir()
            with patch.dict(os.environ, {
                "CODING_TOOLS_MCP_TOOL_MODE": "smart",
                "CODING_TOOLS_MCP_AUTHORIZED_ROOTS": json.dumps([str(authorized)]),
            }):
                runtime = Runtime(primary)
            try:
                runtime.task_state.update({"objective": "primary-only", "status": "active"})
                TaskStateStore(authorized).update({"objective": "authorized-only", "status": "active"})

                selected = runtime.workspace_context({"path": str(authorized), "detail": "compact"})
                self.assertEqual(selected["workspace"], str(authorized.resolve()))
                self.assertNotEqual(selected["workspace_id"], runtime._content_free_workspace_root_id(primary))
                self.assertEqual(selected["task"]["objective"], "authorized-only")

                primary_view = runtime.workspace_context({"path": str(primary), "detail": "compact"})
                self.assertEqual(primary_view["workspace"], str(primary.resolve()))
                self.assertEqual(primary_view["task"]["objective"], "primary-only")
            finally:
                runtime.close()

    def test_task_context_cannot_switch_bound_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            primary = base / "primary"
            authorized = base / "authorized"
            primary.mkdir()
            authorized.mkdir()
            with patch.dict(os.environ, {
                "CODING_TOOLS_MCP_TOOL_MODE": "smart",
                "CODING_TOOLS_MCP_AUTHORIZED_ROOTS": json.dumps([str(authorized)]),
            }):
                runtime = Runtime(primary, transport="http")
            runtime.request_context.hub_client = {
                "client_id": "chatweb:test",
                "client_type": "chatweb",
                "execution_context_id": "ctx-bound-workspace",
            }
            try:
                first = runtime.call_tool("workspace_context", {"path": str(authorized), "detail": "compact"})
                self.assertFalse(first["isError"], first)
                rejected = runtime.call_tool("workspace_context", {"path": str(primary), "detail": "compact"})
                self.assertTrue(rejected["isError"], rejected)
                self.assertEqual(
                    rejected["structuredContent"]["error"]["code"],
                    "TASK_CONTEXT_WORKSPACE_MISMATCH",
                )
            finally:
                del runtime.request_context.hub_client
                runtime.close()

    def test_mutation_without_workspace_target_is_rejected_when_multiple_roots_are_authorized(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            primary = base / "primary"
            authorized = base / "authorized"
            primary.mkdir()
            authorized.mkdir()
            with patch.dict(os.environ, {
                "CODING_TOOLS_MCP_TOOL_MODE": "smart",
                "CODING_TOOLS_MCP_AUTHORIZED_ROOTS": json.dumps([str(authorized)]),
            }):
                runtime = Runtime(primary)
            try:
                result = runtime.call_tool("exec_command", {"cmd": "echo must-not-run"})
                self.assertTrue(result["isError"], result)
                self.assertEqual(
                    result["structuredContent"]["error"]["code"],
                    "WORKSPACE_TARGET_REQUIRED",
                )
                self.assertEqual(
                    result["structuredContent"]["error"]["details"]["required_fields"],
                    ["workdir", "task_context_id"],
                )
            finally:
                runtime.close()

    def test_bound_task_context_is_a_valid_default_exec_workdir(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            primary = base / "primary"
            authorized = base / "authorized"
            primary.mkdir()
            authorized.mkdir()
            with patch.dict(os.environ, {
                "CODING_TOOLS_MCP_TOOL_MODE": "smart",
                "CODING_TOOLS_MCP_AUTHORIZED_ROOTS": json.dumps([str(authorized)]),
            }):
                runtime = Runtime(primary, transport="http")
            identity = {
                "client_id": "chatweb:scoped-exec",
                "client_type": "chatweb",
                "execution_context_id": "mcp2026:scoped-exec-context",
            }
            runtime.request_context.hub_client = dict(identity)
            try:
                bound = runtime.call_tool("workspace_context", {
                    "path": str(authorized), "detail": "compact",
                })
                self.assertFalse(bound["isError"], bound)
                runtime._set_request_workspace_scope("exec_command", {"cmd": "echo scoped"})
                runtime._preflight_tool_workspace_scope("exec_command", {"cmd": "echo scoped"})
                self.assertEqual(runtime.resolve_existing(".").path, authorized.resolve())
                self.assertEqual(runtime._current_request_workspace_root(), authorized.resolve())
            finally:
                del runtime.request_context.hub_client
                if hasattr(runtime.request_context, "workspace_root"):
                    del runtime.request_context.workspace_root
                runtime.close()

    def test_task_control_rejects_run_from_another_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            primary = base / "primary"
            authorized = base / "authorized"
            primary.mkdir()
            authorized.mkdir()
            with patch.dict(os.environ, {
                "CODING_TOOLS_MCP_TOOL_MODE": "smart",
                "CODING_TOOLS_MCP_AUTHORIZED_ROOTS": json.dumps([str(authorized)]),
            }):
                runtime = Runtime(primary)
            try:
                result = runtime.call_tool("agent_workflow", {
                    "workflow": "diagnose",
                    "phase": "prepare",
                    "path": str(authorized),
                    "objective": "authorized run",
                    "execution_route": "deterministic",
                    "execution_mode": "mcp_only",
                    "verification": "none",
                })
                self.assertFalse(result["isError"], result)
                run_id = result["structuredContent"]["orchestration"]["run_id"]
                rejected = runtime.call_tool("task_control", {"action": "get", "run_id": run_id})
                self.assertTrue(rejected["isError"], rejected)
                self.assertEqual(
                    rejected["structuredContent"]["error"]["code"],
                    "RUN_WORKSPACE_MISMATCH",
                )
            finally:
                runtime.close()

    def test_task_control_rejects_uncached_run_from_another_workspace_after_restart(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            primary = base / "primary"
            authorized = base / "authorized"
            primary.mkdir()
            authorized.mkdir()
            env = {
                "CODING_TOOLS_MCP_TOOL_MODE": "smart",
                "CODING_TOOLS_MCP_AUTHORIZED_ROOTS": json.dumps([str(authorized)]),
            }
            with patch.dict(os.environ, env):
                first = Runtime(primary)
            try:
                created = first.call_tool("agent_workflow", {
                    "workflow": "diagnose",
                    "phase": "prepare",
                    "path": str(authorized),
                    "objective": "authorized run survives restart lookup",
                    "execution_route": "deterministic",
                    "execution_mode": "mcp_only",
                    "verification": "none",
                })
                self.assertFalse(created["isError"], created)
                run_id = created["structuredContent"]["orchestration"]["run_id"]
            finally:
                first.close()

            with patch.dict(os.environ, env):
                second = Runtime(primary)
            try:
                rejected = second.call_tool("task_control", {"action": "get", "run_id": run_id})
                self.assertTrue(rejected["isError"], rejected)
                self.assertEqual(
                    rejected["structuredContent"]["error"]["code"],
                    "RUN_WORKSPACE_MISMATCH",
                )
            finally:
                second.close()

    def test_task_context_workspace_binding_survives_runtime_restart(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            primary = base / "primary"
            authorized = base / "authorized"
            primary.mkdir()
            authorized.mkdir()
            environment = {
                "CODING_TOOLS_MCP_TOOL_MODE": "smart",
                "CODING_TOOLS_MCP_AUTHORIZED_ROOTS": json.dumps([str(authorized)]),
            }
            identity = {
                "client_id": "chatweb:restart",
                "client_type": "chatweb",
                "execution_context_id": "mcp2026:restart-bound-context",
            }
            with patch.dict(os.environ, environment):
                first = Runtime(primary, transport="http")
            try:
                first.request_context.hub_client = dict(identity)
                first.request_context.workspace_root = str(authorized.resolve())
                first._touch_hub_client(identity)
                del first.request_context.workspace_root
                bound = first.call_tool("workspace_context", {"path": str(authorized), "detail": "compact"})
                self.assertFalse(bound["isError"], bound)
                registry_path = primary / ".coding-tools" / "orchestration" / "task-context-workspaces.json"
                self.assertTrue(registry_path.is_file())
                first.request_context.workspace_root = str(authorized.resolve())
                first._touch_hub_client(identity)
                del first.request_context.workspace_root
                prepared = first.call_tool("agent_workflow", {
                    "workflow": "diagnose",
                    "phase": "prepare",
                    "objective": "restart-scoped-authorized-task",
                    "execution_route": "deterministic",
                    "execution_mode": "mcp_only",
                    "verification": "none",
                })
                self.assertFalse(prepared["isError"], prepared)
                run_id = prepared["structuredContent"]["orchestration"]["run_id"]
            finally:
                del first.request_context.hub_client
                first.close()

            with patch.dict(os.environ, environment):
                second = Runtime(primary, transport="http")
            try:
                second.request_context.hub_client = dict(identity)
                second.request_context.workspace_root = str(authorized.resolve())
                second._touch_hub_client(identity)
                del second.request_context.workspace_root
                restored = second.call_tool("workspace_context", {"detail": "compact"})
                self.assertFalse(restored["isError"], restored)
                self.assertEqual(restored["structuredContent"]["workspace"], str(authorized.resolve()))
                second.request_context.workspace_root = str(authorized.resolve())
                second._touch_hub_client(identity)
                del second.request_context.workspace_root
                state = second.call_tool("task_control", {"action": "get"})
                self.assertFalse(state["isError"], state)
                self.assertEqual(
                    state["structuredContent"]["state"]["orchestration"]["run_id"],
                    run_id,
                )
            finally:
                del second.request_context.hub_client
                second.close()

    def test_legacy_workspace_context_mapping_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            primary = Path(temp) / "primary"
            primary.mkdir()
            registry_path = primary / ".coding-tools" / "orchestration" / "task-context-workspaces.json"
            registry_path.parent.mkdir(parents=True)
            registry_path.write_text(json.dumps({
                "schema_version": 0,
                "contexts": {"mcp2026:legacy-context": {"root": "unknown"}},
            }), encoding="utf-8")
            with patch.dict(os.environ, {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}):
                runtime = Runtime(primary, transport="http")
            runtime.request_context.hub_client = {
                "client_id": "chatweb:legacy",
                "client_type": "chatweb",
                "execution_context_id": "mcp2026:legacy-context",
            }
            try:
                result = runtime.call_tool("workspace_context", {"detail": "compact"})
                self.assertTrue(result["isError"], result)
                self.assertEqual(
                    result["structuredContent"]["error"]["code"],
                    "UNKNOWN_LEGACY_WORKSPACE",
                )
                runtime.request_context.hub_client["execution_context_id"] = "mcp2026:new-context"
                recovered = runtime.call_tool("workspace_context", {"path": str(primary), "detail": "compact"})
                self.assertFalse(recovered["isError"], recovered)
                persisted = json.loads(registry_path.read_text(encoding="utf-8"))
                self.assertIn("mcp2026:legacy-context", persisted.get("legacy_contexts", {}))
            finally:
                del runtime.request_context.hub_client
                runtime.close()

    def test_authorized_project_is_valid_execution_scope_without_switching_primary_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            workspace = base / "current"
            authorized = base / "authorized"
            workspace.mkdir()
            authorized.mkdir()
            (authorized / "project.txt").write_text("authorized\n", encoding="utf-8")
            with patch.dict(os.environ, {
                "CODING_TOOLS_MCP_TOOL_MODE": "smart",
                "CODING_TOOLS_MCP_AUTHORIZED_ROOTS": json.dumps([str(authorized)]),
            }):
                runtime = Runtime(workspace)
            try:
                command_result = runtime.call_tool("exec_command", {
                    "cmd": "python --version",
                    "workdir": str(authorized),
                })
                self.assertFalse(command_result["isError"], command_result)
                self.assertEqual(command_result["structuredContent"]["exit_code"], 0)
                self.assertEqual(runtime.workspace.root, workspace.resolve())

                workflow_result = runtime.agent_workflow({
                    "workflow": "diagnose",
                    "phase": "prepare",
                    "path": str(authorized),
                    "objective": "inspect an explicitly authorized project",
                    "execution_route": "deterministic",
                    "execution_mode": "mcp_only",
                    "verification": "none",
                })
                self.assertEqual(workflow_result["phase"], "prepare")
                self.assertEqual(runtime.workspace.root, workspace.resolve())
                self.assertIn(authorized.resolve(), runtime.workspace.authorized_roots)
            finally:
                runtime.close()

    def test_unauthorized_project_is_rejected_before_task_or_background_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            workspace = base / "current"
            outsider = base / "outsider"
            workspace.mkdir()
            outsider.mkdir()
            with patch.dict(os.environ, {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}):
                runtime = Runtime(workspace)
            try:
                before = runtime.task_state.get()
                before_background = set(runtime.background_operations)
                before_sessions = set(runtime.sessions)

                command_result = runtime.call_tool("exec_command", {
                    "cmd": "echo must-not-run",
                    "workdir": str(outsider),
                })
                self.assertTrue(command_result["isError"])
                self.assertEqual(
                    command_result["structuredContent"]["error"]["code"],
                    "STALE_WORKSPACE_CONTEXT",
                )

                workflow_result = runtime.call_tool("agent_workflow", {
                    "workflow": "bugfix",
                    "phase": "run",
                    "path": str(outsider),
                    "objective": "must not attach an unauthorized project to this task state",
                    "execution_route": "deterministic",
                    "execution_mode": "mcp_only",
                    "verification": "none",
                })
                self.assertTrue(workflow_result["isError"])
                self.assertEqual(
                    workflow_result["structuredContent"]["error"]["code"],
                    "STALE_WORKSPACE_CONTEXT",
                )

                after = runtime.task_state.get()
                self.assertEqual(after.get("task_id"), before.get("task_id"))
                self.assertEqual(after.get("objective"), before.get("objective"))
                self.assertEqual(after.get("events"), before.get("events"))
                self.assertEqual(set(runtime.background_operations), before_background)
                self.assertEqual(set(runtime.sessions), before_sessions)
            finally:
                runtime.close()

    def test_scoped_session_survives_authorized_roots_update(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            workspace = base / "current"
            authorized = base / "authorized"
            workspace.mkdir()
            authorized.mkdir()
            with patch.dict(os.environ, {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}):
                runtime = Runtime(workspace, transport="http")
            server = RuntimeHTTPServer(("127.0.0.1", 0), MCPHandler, runtime, runtime_factory=None)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            port = int(server.server_address[1])
            try:
                status, headers, initialized = self._post(port, {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": PROTOCOL_VERSION,
                        "capabilities": {},
                        "clientInfo": {"name": "authorized-root-session-test", "version": "1"},
                    },
                })
                self.assertEqual(status, 200, initialized)
                session_id = headers.get("mcp-session-id", "")
                self.assertTrue(session_id.startswith("ws1."), session_id)

                updated = runtime.set_authorized_roots([str(authorized)])
                self.assertIn(str(authorized.resolve()), updated["authorized_roots"])
                self.assertEqual(runtime.workspace.root, workspace.resolve())
                self.assertNotEqual(runtime.http_session_id, session_id)

                status, _headers, current = self._post(
                    port,
                    {
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "tools/call",
                        "params": {"name": "workspace_context", "arguments": {"detail": "compact"}},
                    },
                    session_id=session_id,
                    protocol_version=PROTOCOL_VERSION,
                )
                self.assertEqual(status, 200, current)
                self.assertFalse(current["result"]["isError"])
                self.assertEqual(current["result"]["structuredContent"]["workspace"], str(workspace.resolve()))
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)
                self.assertFalse(thread.is_alive())

    def test_scoped_session_fails_closed_after_workspace_switch_and_reinitialize_recovers(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            first = base / "first"
            second = base / "second"
            first.mkdir()
            second.mkdir()
            with patch.dict(os.environ, {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}):
                runtime = Runtime(first, transport="http")
            server = RuntimeHTTPServer(("127.0.0.1", 0), MCPHandler, runtime, runtime_factory=None)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            port = int(server.server_address[1])
            try:
                status, headers, initialized = self._post(port, {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": PROTOCOL_VERSION,
                        "capabilities": {},
                        "clientInfo": {"name": "workspace-isolation-test", "version": "1"},
                    },
                })
                self.assertEqual(status, 200, initialized)
                old_session = headers.get("mcp-session-id", "")
                self.assertTrue(old_session.startswith("ws1."), old_session)

                switched = runtime.switch_workspace(second)
                self.assertTrue(switched["changed"])
                self.assertNotEqual(runtime.http_session_id, old_session)
                before = runtime.task_state.get()

                status, headers, rejected = self._post(
                    port,
                    {
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "tools/call",
                        "params": {"name": "workspace_context", "arguments": {"detail": "compact"}},
                    },
                    session_id=old_session,
                    protocol_version=PROTOCOL_VERSION,
                )
                self.assertEqual(status, 409, rejected)
                self.assertNotIn("mcp-session-id", headers)
                self.assertEqual(rejected["error"]["code"], -32023)
                self.assertEqual(rejected["error"]["data"]["code"], "STALE_WORKSPACE_CONTEXT")
                self.assertEqual(rejected["error"]["data"]["workspace"], str(second.resolve()))
                after = runtime.task_state.get()
                self.assertEqual(after.get("task_id"), before.get("task_id"))
                self.assertEqual(after.get("events"), before.get("events"))

                status, headers, reinitialized = self._post(port, {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": PROTOCOL_VERSION,
                        "capabilities": {},
                        "clientInfo": {"name": "workspace-isolation-test", "version": "1"},
                    },
                })
                self.assertEqual(status, 200, reinitialized)
                new_session = headers.get("mcp-session-id", "")
                self.assertTrue(new_session.startswith("ws1."), new_session)
                self.assertNotEqual(new_session, old_session)

                status, _headers, current = self._post(
                    port,
                    {
                        "jsonrpc": "2.0",
                        "id": 4,
                        "method": "tools/call",
                        "params": {"name": "workspace_context", "arguments": {"detail": "compact"}},
                    },
                    session_id=new_session,
                    protocol_version=PROTOCOL_VERSION,
                )
                self.assertEqual(status, 200, current)
                self.assertFalse(current["result"]["isError"])
                self.assertEqual(current["result"]["structuredContent"]["workspace"], str(second.resolve()))
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)
                self.assertFalse(thread.is_alive())

    def test_two_initialized_chatweb_sessions_keep_independent_tasks_and_runs(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            workspace = base / "current"
            authorized = base / "authorized"
            workspace.mkdir()
            authorized.mkdir()
            with patch.dict(os.environ, {
                "CODING_TOOLS_MCP_TOOL_MODE": "smart",
                "CODING_TOOLS_MCP_AUTHORIZED_ROOTS": json.dumps([str(authorized)]),
            }):
                runtime = Runtime(workspace, transport="http")
            server = RuntimeHTTPServer(("127.0.0.1", 0), MCPHandler, runtime, runtime_factory=None)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            port = int(server.server_address[1])
            try:
                initialize = {
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": PROTOCOL_VERSION,
                        "capabilities": {},
                        "clientInfo": {"name": "chatweb-isolation-test", "version": "1"},
                    },
                }
                status, headers_a, body_a = self._post(port, {**initialize, "id": 1})
                self.assertEqual(status, 200, body_a)
                status, headers_b, body_b = self._post(port, {**initialize, "id": 2})
                self.assertEqual(status, 200, body_b)
                session_a = headers_a.get("mcp-session-id", "")
                session_b = headers_b.get("mcp-session-id", "")
                self.assertTrue(session_a.startswith("ws1."), session_a)
                self.assertTrue(session_b.startswith("ws1."), session_b)
                self.assertNotEqual(session_a, session_b)
                self.assertEqual(server.sessions.stats()["shared_runtimes"], 1)
                self.assertEqual(server.sessions.stats()["execution_contexts"], 2)

                def workflow_call(request_id: int, objective: str, path: str, session_id: str) -> dict:
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
                                    "path": path,
                                    "objective": objective,
                                    "execution_route": "deterministic",
                                    "execution_mode": "mcp_only",
                                    "verification": "none",
                                },
                            },
                        },
                        session_id=session_id,
                        protocol_version=PROTOCOL_VERSION,
                    )
                    self.assertEqual(status, 200, body)
                    self.assertFalse(body["result"]["isError"], body)
                    return body["result"]["structuredContent"]

                result_a = workflow_call(3, "task-a-primary", str(workspace), session_a)
                result_b = workflow_call(4, "task-b-authorized", str(authorized), session_b)
                run_a = result_a["orchestration"]["run_id"]
                run_b = result_b["orchestration"]["run_id"]
                self.assertNotEqual(run_a, run_b)

                def task_get(request_id: int, session_id: str) -> dict:
                    status, _headers, body = self._post(
                        port,
                        {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "method": "tools/call",
                            "params": {"name": "task_control", "arguments": {"action": "get"}},
                        },
                        session_id=session_id,
                        protocol_version=PROTOCOL_VERSION,
                    )
                    self.assertEqual(status, 200, body)
                    self.assertFalse(body["result"]["isError"], body)
                    return body["result"]["structuredContent"]["state"]

                state_a = task_get(5, session_a)
                state_b = task_get(6, session_b)
                self.assertEqual(state_a["objective"], "task-a-primary")
                self.assertEqual(state_b["objective"], "task-b-authorized")
                self.assertEqual(state_a["orchestration"]["run_id"], run_a)
                self.assertEqual(state_b["orchestration"]["run_id"], run_b)
                self.assertNotEqual(state_a["task_id"], state_b["task_id"])

                controller_a = runtime.orchestration_ledger.get_controller_lease(run_a)
                controller_b = runtime.orchestration_ledger.get_controller_lease(run_b)
                self.assertTrue(str(controller_a["owner_client_id"]).startswith("chatweb:"), controller_a)
                self.assertTrue(str(controller_b["owner_client_id"]).startswith("chatweb:"), controller_b)
                self.assertNotEqual(controller_a["owner_client_id"], controller_b["owner_client_id"])
                contexts = runtime.task_state.contexts()
                self.assertEqual(len(contexts), 2, contexts)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)
                self.assertFalse(thread.is_alive())

    def test_background_worker_keeps_chatweb_execution_context(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            with patch.dict(os.environ, {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}):
                runtime = Runtime(Path(temp))
            original = runtime._tool_handlers["agent_workflow"]
            observed: dict[str, object] = {}
            try:
                identity = {
                    "client_id": "chatweb",
                    "client_type": "chatweb",
                    "role": "controller",
                    "execution_context_id": "0123456789abcdef",
                    "session_instance": "background-test",
                    "capabilities": {},
                }
                runtime.request_context.hub_client = identity
                runtime.request_context.stateless_task_context_id = "ctx-background-test"
                scoped = runtime.task_state.update({
                    "objective": "background-context-task",
                    "status": "active",
                })

                def fake_agent(_args: dict) -> dict:
                    observed["state"] = runtime.task_state.get()
                    observed["identity"] = runtime._current_hub_client()
                    observed["scope"] = runtime._current_task_scope_id()
                    return {"ok": True, "phase": "run", "affected_files": []}

                runtime._tool_handlers["agent_workflow"] = fake_agent
                operation, done = runtime._start_background_tool(
                    "agent_workflow",
                    {
                        "workflow": "diagnose",
                        "phase": "run",
                        "objective": "background-context-task",
                        "path": ".",
                        "execution_route": "deterministic",
                        "execution_mode": "mcp_only",
                        "verification": "none",
                    },
                    request_id="background-context-test",
                )
                self.assertTrue(done.wait(5), operation)
                self.assertIsNone(operation.get("error"), operation)
                self.assertEqual(observed["state"]["task_id"], scoped["task_id"])
                self.assertEqual(
                    observed["identity"]["execution_context_id"],
                    "0123456789abcdef",
                )
                self.assertEqual(observed["scope"], "mcp2026:ctx-background-test")
            finally:
                runtime._tool_handlers["agent_workflow"] = original
                if hasattr(runtime.request_context, "hub_client"):
                    del runtime.request_context.hub_client
                if hasattr(runtime.request_context, "stateless_task_context_id"):
                    del runtime.request_context.stateless_task_context_id
                runtime.close()

    def test_legacy_unscoped_session_alias_is_stably_isolated_from_global_task(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            with patch.dict(os.environ, {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}):
                runtime = Runtime(Path(temp), transport="http")
            server = RuntimeHTTPServer(("127.0.0.1", 0), MCPHandler, runtime, runtime_factory=None)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            port = int(server.server_address[1])
            try:
                runtime.task_state.update({"objective": "global-sentinel", "status": "active"})
                alias_a = "legacy-session-from-pre-scope-runtime-a"
                alias_b = runtime.http_session_id

                resolved_a = server.sessions.get(alias_a)
                resolved_a_repeat = server.sessions.get(alias_a)
                resolved_b = server.sessions.get(alias_b)
                self.assertIsNot(resolved_a, runtime)
                self.assertIs(resolved_a_repeat, resolved_a)
                self.assertIsNot(resolved_b, runtime)
                self.assertTrue(resolved_a.execution_context_id.startswith("legacy:"))
                self.assertTrue(resolved_b.execution_context_id.startswith("legacy:"))
                self.assertNotEqual(resolved_a.execution_context_id, resolved_b.execution_context_id)
                self.assertTrue(resolved_a.http_session_id.startswith("ws1."))
                self.assertIn(".ctxl_", resolved_a.http_session_id)

                def task_call(request_id: int, session_id: str, arguments: dict) -> tuple[dict, str]:
                    status, headers, body = self._post(
                        port,
                        {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "method": "tools/call",
                            "params": {"name": "task_control", "arguments": arguments},
                        },
                        session_id=session_id,
                        protocol_version=PROTOCOL_VERSION,
                    )
                    self.assertEqual(status, 200, body)
                    self.assertIn("result", body, body)
                    self.assertFalse(body["result"]["isError"], body)
                    return body["result"]["structuredContent"], headers.get("mcp-session-id", "")

                state_a, canonical_a = task_call(1, alias_a, {"action": "get"})
                state_b, canonical_b = task_call(2, alias_b, {"action": "get"})
                self.assertNotEqual(state_a["state"].get("objective"), "global-sentinel")
                self.assertNotEqual(state_b["state"].get("objective"), "global-sentinel")
                self.assertNotEqual(canonical_a, alias_a)
                self.assertNotEqual(canonical_b, alias_b)
                self.assertIn(".ctxl_", canonical_a)
                self.assertIn(".ctxl_", canonical_b)

                started_a, _ = task_call(3, alias_a, {"action": "start", "objective": "legacy-alias-a"})
                started_b, _ = task_call(4, alias_b, {"action": "start", "objective": "legacy-alias-b"})
                self.assertEqual(started_a["state"]["objective"], "legacy-alias-a")
                self.assertEqual(started_b["state"]["objective"], "legacy-alias-b")

                current_a, _ = task_call(5, canonical_a, {"action": "get"})
                current_b, _ = task_call(6, canonical_b, {"action": "get"})
                self.assertEqual(current_a["state"]["objective"], "legacy-alias-a")
                self.assertEqual(current_b["state"]["objective"], "legacy-alias-b")
                self.assertNotEqual(current_a["state"]["task_id"], current_b["state"]["task_id"])
                self.assertEqual(runtime.task_state.get()["objective"], "global-sentinel")
                self.assertGreaterEqual(runtime.legacy_session_alias_uses, 2)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)
                self.assertFalse(thread.is_alive())

    @staticmethod
    def _post(
        port: int,
        payload: dict,
        *,
        session_id: str = "",
        protocol_version: str = "",
    ) -> tuple[int, dict[str, str], dict]:
        headers = {"Content-Type": "application/json"}
        if session_id:
            headers["Mcp-Session-Id"] = session_id
        if protocol_version:
            headers["MCP-Protocol-Version"] = protocol_version
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        try:
            connection.request("POST", "/mcp", body=json.dumps(payload).encode("utf-8"), headers=headers)
            response = connection.getresponse()
            raw = response.read()
            decoded = json.loads(raw.decode("utf-8")) if raw else {}
            return response.status, {key.lower(): value for key, value in response.getheaders()}, decoded
        finally:
            connection.close()


if __name__ == "__main__":
    unittest.main()
