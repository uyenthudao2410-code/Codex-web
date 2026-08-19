import http.client
import json
import os
import tempfile
import threading
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from coding_tools_mcp.server import MCPHandler, PROTOCOL_VERSION, Runtime, RuntimeHTTPServer


class HubServer:
    def __init__(self, root: Path, token: str) -> None:
        self.runtime = Runtime(root, transport="http", auth_token=token)
        self.server = RuntimeHTTPServer(("127.0.0.1", 0), MCPHandler, self.runtime, runtime_factory=None)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.port = int(self.server.server_address[1])
        self.token = token

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.runtime.close()

    def post_rpc(self, request, *, session_id="", client_id="", client_type="", protocol_version=""):
        body = json.dumps(request).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Content-Length": str(len(body)),
        }
        if session_id:
            headers["Mcp-Session-Id"] = session_id
        if protocol_version:
            headers["MCP-Protocol-Version"] = protocol_version
        if client_id:
            headers["X-Coding-Tools-Client-Id"] = client_id
        if client_type:
            headers["X-Coding-Tools-Client-Type"] = client_type
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        try:
            connection.request("POST", "/mcp", body=body, headers=headers)
            response = connection.getresponse()
            raw = response.read()
            payload = json.loads(raw.decode("utf-8")) if raw else {}
            return response.status, dict(response.headers), payload
        finally:
            connection.close()

    def post_hub(self, payload):
        body = json.dumps(payload).encode("utf-8")
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        try:
            connection.request(
                "POST",
                "/__control/hub",
                body=body,
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json",
                    "Content-Length": str(len(body)),
                },
            )
            response = connection.getresponse()
            raw = response.read()
            return response.status, json.loads(raw.decode("utf-8")) if raw else {}
        finally:
            connection.close()

    def snapshot(self):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        try:
            connection.request("GET", "/__control/orchestration", headers={"Authorization": f"Bearer {self.token}"})
            response = connection.getresponse()
            return response.status, json.loads(response.read().decode("utf-8"))
        finally:
            connection.close()


def tool_call(request_id, action, **arguments):
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": "tools/call",
        "params": {"name": "task_control", "arguments": {"action": action, **arguments}},
    }


class ExecutionHubFaultTests(unittest.TestCase):
    TOKEN = "hub-fault-test-token-0123456789"

    def setUp(self) -> None:
        self.previous_tool_mode = os.environ.get("CODING_TOOLS_MCP_TOOL_MODE")
        os.environ["CODING_TOOLS_MCP_TOOL_MODE"] = "smart"
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        if self.previous_tool_mode is None:
            os.environ.pop("CODING_TOOLS_MCP_TOOL_MODE", None)
        else:
            os.environ["CODING_TOOLS_MCP_TOOL_MODE"] = self.previous_tool_mode
        self.temp.cleanup()

    def start_linked_run(self, hub: HubServer):
        state = hub.runtime.task_state.update({"objective": "Execution Hub fault test", "status": "active"})
        ctx = hub.runtime.orchestration_control.begin(
            objective="Execution Hub fault test",
            task_id=str(state["task_id"]),
            execution_mode="mcp_only",
            base_head="fault-head",
            worktree_fp="fault-fp",
        )
        hub.runtime.task_state.set_orchestration_projection(ctx.projection(), event="fault_test_linked")
        return state, ctx

    def test_orchestration_snapshot_projects_runtime_activity_and_client_recency(self) -> None:
        hub = HubServer(self.root, self.TOKEN)
        admission = None
        operation_id = "fabric-runtime-activity-test"
        try:
            now = datetime.now(timezone.utc)
            self.assertEqual(
                hub.runtime.hub_client_activity_state(now.isoformat(), active_seconds=45.0),
                "ACTIVE",
            )
            self.assertEqual(
                hub.runtime.hub_client_activity_state(
                    (now - timedelta(seconds=120)).isoformat(), active_seconds=45.0
                ),
                "RECENT",
            )
            self.assertEqual(
                hub.runtime.hub_client_activity_state(
                    (now - timedelta(hours=1)).isoformat(), active_seconds=45.0
                ),
                "NO_SIGNAL",
            )
            self.assertEqual(
                hub.runtime.hub_client_activity_state("", active_seconds=45.0),
                "NO_SIGNAL",
            )

            status, _headers, response = hub.post_rpc(
                tool_call(1, "get"), client_id="chatweb", client_type="chatweb"
            )
            self.assertEqual(status, 200, response)
            admission = hub.runtime.execution_resource_governor.admit(
                command="python -V",
                command_id="fabric-runtime-command",
                resource_class="LIGHT",
            )
            hub.runtime.active_tool_calls = 2
            operation = {
                "operation_id": operation_id,
                "tool": "agent_workflow",
                "workspace": str(self.root),
                "started_monotonic": time.monotonic(),
                "event": threading.Event(),
                "budget": None,
            }
            with hub.runtime.background_operations_lock:
                hub.runtime.background_operations[operation_id] = operation

            snapshot_status, snapshot = hub.snapshot()
            self.assertEqual(snapshot_status, 200, snapshot)
            activity = snapshot["runtime_activity"]
            self.assertEqual(activity["state"], "ACTIVE")
            self.assertEqual(activity["active_tool_calls"], 2)
            self.assertGreaterEqual(activity["active_commands"], 1)
            self.assertEqual(activity["active_background_operations"], 1)
            self.assertFalse(activity["write_active"])
            self.assertEqual(activity["active_delegations"], 0)
            self.assertTrue(
                any(item["command_id"] == "fabric-runtime-command" for item in activity["managed_jobs"])
            )
            self.assertTrue(
                any(item["operation_id"] == operation_id for item in activity["background_operations"])
            )
            chat_client = next(
                item for item in snapshot["clients"] if item.get("client_type") == "chatweb"
            )
            self.assertEqual(chat_client["activity_state"], "ACTIVE")

            hub.runtime.active_tool_calls = 0
            with hub.runtime.background_operations_lock:
                hub.runtime.background_operations.pop(operation_id, None)
            hub.runtime.execution_resource_governor.complete(
                admission.job_id, lifecycle_state="exited", exit_code=0
            )
            admission = None
            idle = hub.runtime.runtime_activity_snapshot(write_active=False, delegations=[])
            self.assertEqual(idle["state"], "IDLE")
            writing = hub.runtime.runtime_activity_snapshot(write_active=True, delegations=[])
            self.assertEqual(writing["state"], "WRITING")
            delegating = hub.runtime.runtime_activity_snapshot(
                write_active=True, delegations=[{"status": "active"}]
            )
            self.assertEqual(delegating["state"], "DELEGATING")
        finally:
            hub.runtime.active_tool_calls = 0
            with hub.runtime.background_operations_lock:
                hub.runtime.background_operations.pop(operation_id, None)
            if admission is not None:
                hub.runtime.execution_resource_governor.complete(
                    admission.job_id, lifecycle_state="exited", exit_code=0
                )
            hub.close()

    def test_two_clients_share_one_runtime_with_independent_cursors_and_fenced_controller(self) -> None:
        hub = HubServer(self.root, self.TOKEN)
        try:
            state, ctx = self.start_linked_run(hub)
            hub.runtime.orchestration_ledger.append_event(ctx.run_id, event_type="shared_truth_1", payload={"n": 1})

            status, chat_headers, chat_get = hub.post_rpc(tool_call(1, "get"), client_id="chatweb", client_type="chatweb")
            self.assertEqual(status, 200, chat_get)
            self.assertNotIn("error", chat_get, chat_get)
            chat_session = chat_headers.get("Mcp-Session-Id")
            self.assertTrue(chat_session)
            chat_state = chat_get["result"]["structuredContent"]["state"]
            self.assertEqual(chat_state["task_id"], state["task_id"])

            status, _headers, desktop_get = hub.post_rpc(
                tool_call(2, "get"), client_id="codex-desktop", client_type="codex_desktop"
            )
            self.assertEqual(status, 200, desktop_get)
            self.assertNotIn("error", desktop_get, desktop_get)
            desktop_state = desktop_get["result"]["structuredContent"]["state"]
            self.assertEqual(desktop_state["task_id"], state["task_id"])
            self.assertEqual(hub.server.sessions.stats()["shared_runtimes"], 1)

            controller = hub.runtime.orchestration_ledger.get_controller_lease(ctx.run_id)
            chatweb_controller_id = str(controller["owner_client_id"])
            self.assertTrue(chatweb_controller_id.startswith("chatweb:"), chatweb_controller_id)
            self.assertEqual(controller["fencing_token"], 1)

            _status, _headers, chat_events = hub.post_rpc(
                tool_call(3, "events", after_seq=0),
                session_id=chat_session,
                client_id="chatweb",
                client_type="chatweb",
                protocol_version=PROTOCOL_VERSION,
            )
            chat_cursor = chat_events["result"]["structuredContent"]["client_cursor"]["last_event_seq"]
            _status, _headers, desktop_events = hub.post_rpc(
                tool_call(4, "events", after_seq=0), client_id="codex-desktop", client_type="codex_desktop"
            )
            desktop_cursor = desktop_events["result"]["structuredContent"]["client_cursor"]["last_event_seq"]
            self.assertEqual(chat_cursor, desktop_cursor)

            hub.runtime.orchestration_ledger.append_event(ctx.run_id, event_type="shared_truth_2", payload={"n": 2})
            _status, _headers, chat_events_2 = hub.post_rpc(
                tool_call(5, "events", after_seq=chat_cursor),
                session_id=chat_session,
                client_id="chatweb",
                client_type="chatweb",
                protocol_version=PROTOCOL_VERSION,
            )
            chat_cursor_2 = chat_events_2["result"]["structuredContent"]["client_cursor"]["last_event_seq"]
            self.assertGreater(chat_cursor_2, chat_cursor)
            desktop_record = hub.runtime.orchestration_ledger.get_hub_client_cursor(
                client_id="codex-desktop", run_id=ctx.run_id
            )
            self.assertEqual(desktop_record["last_event_seq"], desktop_cursor)

            transfer_status, transfer = hub.post_hub(
                {"action": "transfer_controller", "run_id": ctx.run_id, "target_client_id": "codex-desktop"}
            )
            self.assertEqual(transfer_status, 200, transfer)
            self.assertEqual(transfer["fencing_token"], 2)
            stale = hub.runtime.orchestration_ledger.assert_controller_lease(
                run_id=ctx.run_id,
                owner_client_id=chatweb_controller_id,
                lease_id=f"client:{chatweb_controller_id}",
                fencing_token=1,
            )
            self.assertFalse(stale["valid"])

            status, _headers, rejected = hub.post_rpc(
                tool_call(6, "accept", run_id=ctx.run_id),
                session_id=chat_session,
                client_id="chatweb",
                client_type="chatweb",
                protocol_version=PROTOCOL_VERSION,
            )
            self.assertEqual(status, 200)
            self.assertIn("CONTROLLER_LEASE_REQUIRED", json.dumps(rejected))

            status, _headers, desktop_accept = hub.post_rpc(
                tool_call(7, "accept", run_id=ctx.run_id), client_id="codex-desktop", client_type="codex_desktop"
            )
            self.assertEqual(status, 200)
            self.assertNotIn("CONTROLLER_LEASE_REQUIRED", json.dumps(desktop_accept))
            self.assertIn("FINAL_ACCEPTANCE_NOT_READY", json.dumps(desktop_accept))
        finally:
            hub.close()

    def test_chatweb_accept_reclaims_expired_explicit_historical_run(self) -> None:
        hub = HubServer(self.root, self.TOKEN)
        try:
            _state, historical = self.start_linked_run(hub)
            status, initial_headers, initial = hub.post_rpc(
                tool_call(1, "get"), client_id="chatweb", client_type="chatweb"
            )
            self.assertEqual(status, 200, initial)
            chat_session = initial_headers.get("Mcp-Session-Id")
            self.assertTrue(chat_session)
            first_controller = hub.runtime.orchestration_ledger.get_controller_lease(historical.run_id)
            self.assertIsNotNone(first_controller)
            first_chatweb_controller_id = str(first_controller["owner_client_id"])
            self.assertTrue(first_chatweb_controller_id.startswith("chatweb:"), first_chatweb_controller_id)
            self.assertEqual(first_controller["fencing_token"], 1)

            control = hub.runtime.orchestration_control
            control.mark_ready(historical)
            control.select_route(historical, {"requested": "deterministic", "selected": "deterministic", "reason": "test"})
            control.transition(historical, "EXECUTING", reason="test_execution")
            control.transition(historical, "PROVING", reason="test_proof")
            proof_id = hub.runtime.orchestration_ledger.record_proof(
                run_id=historical.run_id,
                wave_id=historical.wave_id,
                stage_id="verify:tests",
                stage_version="1",
                input_fingerprint="historical-expired-controller-proof",
                status="passed",
            )
            control.mark_accepting(historical, proof_summary={"proof_ids": [proof_id]})
            with hub.runtime.orchestration_ledger._lock, hub.runtime.orchestration_ledger._connect() as connection:
                connection.execute(
                    "UPDATE controller_leases SET expires_at=0 WHERE run_id=?",
                    (historical.run_id,),
                )
            self.assertEqual(
                hub.runtime.orchestration_ledger.get_controller_lease(historical.run_id)["status"],
                "expired",
            )

            _ambient_state, ambient = self.start_linked_run(hub)
            self.assertNotEqual(ambient.run_id, historical.run_id)
            status, _headers, accepted = hub.post_rpc(
                tool_call(2, "accept", run_id=historical.run_id),
                session_id=chat_session,
                client_id="chatweb",
                client_type="chatweb",
                protocol_version=PROTOCOL_VERSION,
            )
            self.assertEqual(status, 200, accepted)
            self.assertNotIn("error", accepted, accepted)
            structured = accepted["result"]["structuredContent"]
            self.assertTrue(structured["accepted"])
            self.assertEqual(structured["orchestration"]["orchestration_state"], "CHECKPOINTED")
            reclaimed = hub.runtime.orchestration_ledger.get_controller_lease(historical.run_id)
            reclaimed_chatweb_controller_id = str(reclaimed["owner_client_id"])
            self.assertTrue(reclaimed_chatweb_controller_id.startswith("chatweb:"), reclaimed_chatweb_controller_id)
            self.assertEqual(reclaimed_chatweb_controller_id, first_chatweb_controller_id)
            self.assertEqual(reclaimed["status"], "active")
            self.assertEqual(reclaimed["fencing_token"], 2)
            self.assertEqual(hub.runtime.orchestration_ledger.get_run(historical.run_id)["status"], "accepted")
            self.assertEqual(hub.runtime.orchestration_ledger.get_run(ambient.run_id)["status"], "active")
        finally:
            hub.close()

    def test_explicit_stop_aborts_detached_run_without_replacing_current_projection(self) -> None:
        hub = HubServer(self.root, self.TOKEN)
        try:
            _state, historical = self.start_linked_run(hub)
            _ambient_state, ambient = self.start_linked_run(hub)
            self.assertNotEqual(ambient.run_id, historical.run_id)
            status, _headers, desktop_rejected = hub.post_rpc(tool_call(1, "stop", run_id=historical.run_id), client_id="codex-desktop", client_type="codex_desktop")
            self.assertEqual(status, 200, desktop_rejected)
            self.assertIn("CONTROLLER_LEASE_REQUIRED", json.dumps(desktop_rejected))
            self.assertEqual(hub.runtime.orchestration_ledger.get_run(historical.run_id)["status"], "active")
            status, _headers, stopped = hub.post_rpc(tool_call(2, "stop", run_id=historical.run_id), client_id="chatweb", client_type="chatweb")
            self.assertEqual(status, 200, stopped)
            self.assertNotIn("error", stopped, stopped)
            structured = stopped["result"]["structuredContent"]
            self.assertTrue(structured["stopped"])
            self.assertTrue(structured["detached"])
            self.assertEqual(structured["orchestration"]["orchestration_state"], "ABORTED")
            self.assertEqual(structured["completion_report"]["accepted_or_not"], "NOT_ACCEPTED_ABORTED")
            self.assertTrue(structured["completion_report"]["operator_visible_required"])
            self.assertEqual(structured["state"]["orchestration"]["run_id"], ambient.run_id)
            self.assertEqual(hub.runtime.orchestration_ledger.get_run(historical.run_id)["status"], "aborted")
            self.assertEqual(hub.runtime.orchestration_ledger.get_run(ambient.run_id)["status"], "active")
        finally:
            hub.close()

    def test_old_authenticated_session_alias_rebinds_after_runtime_restart_and_preserves_durable_truth(self) -> None:
        first = HubServer(self.root, self.TOKEN)
        try:
            state, ctx = self.start_linked_run(first)
            capsule = first.runtime.orchestration_ledger.record_handoff_capsule(
                run_id=ctx.run_id,
                wave_id=ctx.wave_id,
                payload={"goal": "survive runtime restart", "next_action": "continue from durable truth"},
            )
            initialize = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "codex-desktop-proxy", "version": "1"},
                },
            }
            status, headers, initialized = first.post_rpc(
                initialize, client_id="codex-desktop", client_type="codex_desktop"
            )
            self.assertEqual(status, 200, initialized)
            self.assertNotIn("error", initialized, initialized)
            old_session = headers.get("Mcp-Session-Id")
            self.assertTrue(old_session)
            first_process = first.runtime.process_instance_id
            first_server = first.runtime.server_instance_id
        finally:
            first.close()

        second = HubServer(self.root, self.TOKEN)
        try:
            # process_instance_id is intentionally one identity per Python OS process;
            # this harness recreates Runtime/server objects in the same pytest process.
            self.assertEqual(second.runtime.process_instance_id, first_process)
            self.assertNotEqual(second.runtime.server_instance_id, first_server)
            status, headers, resumed = second.post_rpc(
                tool_call(2, "get"),
                session_id=old_session,
                client_id="codex-desktop",
                client_type="codex_desktop",
                protocol_version=PROTOCOL_VERSION,
            )
            self.assertEqual(status, 200, resumed)
            self.assertNotIn("error", resumed, resumed)
            resumed_state = resumed["result"]["structuredContent"]["state"]
            self.assertEqual(resumed_state["task_id"], state["task_id"])
            self.assertEqual(resumed_state["orchestration"]["run_id"], ctx.run_id)
            self.assertEqual(second.server.sessions.stats()["shared_runtimes"], 1)
            new_session = headers.get("Mcp-Session-Id")
            self.assertTrue(new_session)
            self.assertNotEqual(new_session, old_session)
            self.assertNotEqual(new_session, second.runtime.http_session_id)

            snapshot_status, snapshot = second.snapshot()
            self.assertEqual(snapshot_status, 200)
            self.assertEqual(snapshot["run"]["run_id"], ctx.run_id)
            self.assertEqual(snapshot["capsule"]["capsule_id"], capsule["capsule_id"])
            self.assertEqual(snapshot["capsule"]["sha256"], capsule["sha256"])
            self.assertEqual(snapshot["runtime"]["process_instance_id"], second.runtime.process_instance_id)
            self.assertEqual(snapshot["runtime"]["server_instance_id"], second.runtime.server_instance_id)
        finally:
            second.close()


if __name__ == "__main__":
    unittest.main()
