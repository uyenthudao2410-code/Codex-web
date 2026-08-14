import http.client
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path

from coding_tools_mcp.server import (
    MCPHandler,
    Runtime,
    RuntimeHTTPServer,
    STATELESS_PROTOCOL_VERSION,
)


class ExecutionHubHTTPTests(unittest.TestCase):
    TOKEN = "execution-hub-test-token-012345"

    def setUp(self) -> None:
        self.previous_tool_mode = os.environ.get("CODING_TOOLS_MCP_TOOL_MODE")
        os.environ["CODING_TOOLS_MCP_TOOL_MODE"] = "smart"
        self.temp = tempfile.TemporaryDirectory()
        self.runtime = Runtime(Path(self.temp.name), transport="http", auth_token=self.TOKEN)
        self.server = RuntimeHTTPServer(("127.0.0.1", 0), MCPHandler, self.runtime, runtime_factory=None)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.port = int(self.server.server_address[1])
        state = self.runtime.task_state.update({"objective": "Execution Hub integration test", "status": "active"})
        self.ctx = self.runtime.orchestration_control.begin(
            objective="Execution Hub integration test",
            task_id=str(state["task_id"]),
            execution_mode="mcp_only",
            base_head="hub-test-head",
            worktree_fp="hub-test-fp",
        )
        self.runtime.task_state.set_orchestration_projection(self.ctx.projection(), event="hub_test_linked")

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.runtime.close()
        self.temp.cleanup()
        if self.previous_tool_mode is None:
            os.environ.pop("CODING_TOOLS_MCP_TOOL_MODE", None)
        else:
            os.environ["CODING_TOOLS_MCP_TOOL_MODE"] = self.previous_tool_mode

    def post_stateless(self, *, action="get", client_id="", client_type="", after_seq=None):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.TOKEN}",
            "MCP-Protocol-Version": STATELESS_PROTOCOL_VERSION,
            "Mcp-Method": "tools/call",
            "Mcp-Name": "task_control",
        }
        if client_id:
            headers["X-Coding-Tools-Client-Id"] = client_id
        if client_type:
            headers["X-Coding-Tools-Client-Type"] = client_type
        arguments = {"action": action}
        if after_seq is not None:
            arguments["after_seq"] = after_seq
        params = {
            "name": "task_control",
            "arguments": arguments,
            "_meta": {
                "io.modelcontextprotocol/protocolVersion": STATELESS_PROTOCOL_VERSION,
                "io.modelcontextprotocol/clientCapabilities": {},
                "io.modelcontextprotocol/clientInfo": {"name": "hub-test", "version": "1"},
            },
        }
        body = json.dumps({"jsonrpc": "2.0", "id": f"hub-{client_id or 'chatweb'}-{action}", "method": "tools/call", "params": params})
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        try:
            connection.request("POST", "/mcp", body=body, headers=headers)
            response = connection.getresponse()
            raw = response.read()
            return response.status, json.loads(raw.decode("utf-8")) if raw else {}
        finally:
            connection.close()

    def post_hub(self, payload, *, authorized=True):
        headers = {"Content-Type": "application/json"}
        if authorized:
            headers["Authorization"] = f"Bearer {self.TOKEN}"
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        try:
            connection.request("POST", "/__control/hub", body=json.dumps(payload), headers=headers)
            response = connection.getresponse()
            raw = response.read()
            return response.status, json.loads(raw.decode("utf-8")) if raw else {}
        finally:
            connection.close()

    def get_snapshot(self):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        try:
            connection.request("GET", "/__control/orchestration", headers={"Authorization": f"Bearer {self.TOKEN}"})
            response = connection.getresponse()
            return response.status, json.loads(response.read().decode("utf-8"))
        finally:
            connection.close()

    def structured(self, body):
        self.assertNotIn("error", body, body)
        return body["result"]["structuredContent"]

    def test_registers_clients_without_stealing_live_controller(self) -> None:
        status, body = self.post_stateless(action="get")
        self.assertEqual(status, 200, body)
        self.structured(body)
        controller = self.runtime.orchestration_ledger.get_controller_lease(self.ctx.run_id)
        self.assertEqual(controller["owner_client_id"], "chatweb")
        self.assertEqual(controller["fencing_token"], 1)

        status, body = self.post_stateless(action="get", client_id="codex-desktop", client_type="codex_desktop")
        self.assertEqual(status, 200, body)
        self.structured(body)
        controller_after = self.runtime.orchestration_ledger.get_controller_lease(self.ctx.run_id)
        self.assertEqual(controller_after["owner_client_id"], "chatweb")
        self.assertEqual(controller_after["fencing_token"], 1)

        status, body = self.post_stateless(action="get", client_id="opencode", client_type="opencode")
        self.assertEqual(status, 200, body)
        self.structured(body)
        controller_after_opencode = self.runtime.orchestration_ledger.get_controller_lease(self.ctx.run_id)
        self.assertEqual(controller_after_opencode["owner_client_id"], "chatweb")
        self.assertEqual(controller_after_opencode["fencing_token"], 1)
        clients = {item["client_id"]: item for item in self.runtime.orchestration_ledger.list_hub_clients()}
        self.assertTrue(clients["chatweb"]["online"])
        self.assertTrue(clients["codex-desktop"]["online"])
        self.assertTrue(clients["opencode"]["online"])
        self.assertEqual(clients["codex-desktop"]["role"], "worker")
        self.assertEqual(clients["opencode"]["role"], "worker")

    def test_event_cursors_advance_only_over_observed_events(self) -> None:
        self.post_stateless(action="get")
        self.runtime.orchestration_ledger.append_event(self.ctx.run_id, event_type="hub_probe", payload={"n": 1})
        status, body = self.post_stateless(action="events", after_seq=0)
        self.assertEqual(status, 200, body)
        structured = self.structured(body)
        observed_seq = structured["events"][-1]["seq"]
        self.assertEqual(structured["client_cursor"]["last_event_seq"], observed_seq)

        self.post_stateless(action="events", after_seq=999999)
        cursor = self.runtime.orchestration_ledger.get_hub_client_cursor(client_id="chatweb", run_id=self.ctx.run_id)
        self.assertEqual(cursor["last_event_seq"], observed_seq)

        self.post_stateless(action="events", client_id="codex-desktop", client_type="codex_desktop", after_seq=0)
        desktop = self.runtime.orchestration_ledger.get_hub_client_cursor(client_id="codex-desktop", run_id=self.ctx.run_id)
        self.assertEqual(desktop["last_event_seq"], observed_seq)

    def test_transfer_and_safe_rotation_projection(self) -> None:
        self.post_stateless(action="get")
        pre_status, pre = self.get_snapshot()
        self.assertEqual(pre_status, 200)
        self.assertEqual(pre["schema_version"], 2)
        self.assertFalse(pre["continuity"]["safe_to_rotate_chatweb"])
        self.assertIn("DESKTOP_OFFLINE", pre["continuity"]["reason_codes"])

        status, heartbeat = self.post_hub({"action": "heartbeat", "client_id": "codex-desktop", "client_type": "codex_desktop"})
        self.assertEqual(status, 200, heartbeat)
        self.runtime.orchestration_ledger.record_handoff_capsule(
            run_id=self.ctx.run_id,
            wave_id=self.ctx.wave_id,
            payload={"goal": "continue Execution Hub test", "next_action": "resume from durable state"},
        )
        status, moved = self.post_hub({"action": "transfer_controller", "run_id": self.ctx.run_id, "target_client_id": "codex-desktop"})
        self.assertEqual(status, 200, moved)
        self.assertTrue(moved["transferred"])
        self.assertEqual(moved["fencing_token"], 2)

        self.post_stateless(action="get")
        post_status, post = self.get_snapshot()
        self.assertEqual(post_status, 200)
        self.assertEqual(post["authority"]["controller"]["owner_client_id"], "codex-desktop")
        self.assertTrue(post["continuity"]["safe_to_rotate_chatweb"], post["continuity"])
        self.assertEqual(post["continuity"]["reason_codes"], ["READY"])
        self.assertEqual(post["continuity"]["context_pressure"]["status"], "unknown")
        self.assertEqual(post["resume_packet"]["run_id"], self.ctx.run_id)
        self.assertEqual(post["resume_packet"]["capsule"]["capsule_id"], post["capsule"]["capsule_id"])
        self.assertTrue(any(item["client_id"] == "codex-desktop" and item["online"] for item in post["clients"]))

        self.runtime.orchestration_ledger.append_event(
            self.ctx.run_id,
            wave_id=self.ctx.wave_id,
            event_type="proof_observed_after_handoff",
            state_before=self.ctx.state,
            state_after=self.ctx.state,
            payload={"proof": "new"},
        )
        _stale_status, stale = self.get_snapshot()
        self.assertFalse(stale["continuity"]["safe_to_rotate_chatweb"])
        self.assertEqual(stale["continuity"]["capsule_status"], "stale")
        self.assertIn("CAPSULE_STALE", stale["continuity"]["reason_codes"])

        unauthorized, _body = self.post_hub({"action": "heartbeat", "client_id": "x", "client_type": "client"}, authorized=False)
        self.assertEqual(unauthorized, 401)


if __name__ == "__main__":
    unittest.main()
