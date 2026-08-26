from __future__ import annotations

import http.client
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from coding_tools_mcp.controller_usage_ingress import CONTROLLER_USAGE_META_KEY, CONTROLLER_USAGE_STATUS_META_KEY
from coding_tools_mcp.protocol import STATELESS_PROTOCOL_VERSION
from coding_tools_mcp.server import MCPHandler, Runtime, RuntimeHTTPServer
from coding_tools_mcp.task_state import TaskStateStore


EXPECTED_SMART_TOOLS = {
    "workspace_context",
    "agent_workflow",
    "task_control",
    "document_workflow",
    "exec_command",
    "command_control",
    "request_permissions",
    "view_image",
}

TASK_CONTEXT_META_KEY = "io.coding-tools/taskContextId"


def modern_params(extra: dict | None = None) -> dict:
    payload = dict(extra or {})
    payload["_meta"] = {
        "io.modelcontextprotocol/protocolVersion": STATELESS_PROTOCOL_VERSION,
        "io.modelcontextprotocol/clientCapabilities": {},
        "io.modelcontextprotocol/clientInfo": {"name": "raw-canary", "version": "1"},
    }
    return payload


class StatelessHttp2026Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.env = patch.dict(
            os.environ,
            {
                "CODING_TOOLS_MCP_TOOL_MODE": "smart",
                "CODING_TOOLS_MCP_STATELESS_HTTP_2026": "1",
            },
        )
        self.env.start()
        self.runtime = Runtime(Path(self.temp.name), transport="http")
        self.server = RuntimeHTTPServer(("127.0.0.1", 0), MCPHandler, self.runtime, runtime_factory=None)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.port = int(self.server.server_address[1])

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.assertFalse(self.thread.is_alive())
        self.env.stop()
        self.temp.cleanup()

    def request(self, method: str, params: dict, *, request_id: int = 1, extra_headers: dict[str, str] | None = None) -> tuple[int, dict[str, str], dict]:
        headers = {
            "Content-Type": "application/json",
            "MCP-Protocol-Version": STATELESS_PROTOCOL_VERSION,
            "Mcp-Method": method,
        }
        headers.update(extra_headers or {})
        body = json.dumps({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}).encode("utf-8")
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        try:
            connection.request("POST", "/mcp", body=body, headers=headers)
            response = connection.getresponse()
            raw = response.read()
            decoded = json.loads(raw.decode("utf-8")) if raw else {}
            return response.status, {key.lower(): value for key, value in response.getheaders()}, decoded
        finally:
            connection.close()

    def tool_call(
        self,
        name: str,
        arguments: dict,
        *,
        request_id: int,
        controller_usage: dict | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> tuple[int, dict[str, str], dict]:
        params = modern_params({"name": name, "arguments": arguments})
        if controller_usage is not None:
            params["_meta"][CONTROLLER_USAGE_META_KEY] = controller_usage
        return self.request(
            "tools/call",
            params,
            request_id=request_id,
            extra_headers={"Mcp-Name": name, **(extra_headers or {})},
        )

    @staticmethod
    def controller_usage(turn_id: str, *, output_tokens: int = 20) -> dict:
        return {
            "schema_version": 1,
            "turn_id": turn_id,
            "trace_id": "trace-controller-usage",
            "provider_id": "openai",
            "model_id": "gpt-5.6-sol",
            "source": "client_reported",
            "accounting_profile": "openai_compatible",
            "input_tokens": 100,
            "cached_input_tokens": 30,
            "output_tokens": output_tokens,
            "reasoning_output_tokens": 5,
        }

    def test_discover_and_tools_list_are_stateless_and_self_describing(self) -> None:
        self.assertFalse(self.runtime.connector_tool_discovery()["observed"])
        status, headers, body = self.request("server/discover", modern_params())
        self.assertEqual(status, 200)
        self.assertNotIn("mcp-session-id", headers)
        result = body["result"]
        self.assertIn(STATELESS_PROTOCOL_VERSION, result["supportedVersions"])
        self.assertEqual(result["resultType"], "complete")
        self.assertEqual(result["ttlMs"], 0)
        self.assertEqual(result["cacheScope"], "private")
        self.assertEqual(result["_meta"]["io.modelcontextprotocol/serverInfo"]["name"], "coding-tools-mcp")
        discovery = self.runtime.connector_tool_discovery()
        self.assertTrue(discovery["current_contract_observed"])
        self.assertEqual(discovery["contract_sha256"], self.runtime.tool_contract["sha256"])
        self.assertEqual(discovery["client_id"], "chatweb")

        status, headers, body = self.request("tools/list", modern_params(), request_id=2)
        self.assertEqual(status, 200)
        self.assertNotIn("mcp-session-id", headers)
        self.assertEqual({tool["name"] for tool in body["result"]["tools"]}, EXPECTED_SMART_TOOLS)
        tools = {tool["name"]: tool for tool in body["result"]["tools"]}
        self.assertIn("task_context_id", tools["task_control"]["inputSchema"]["properties"])
        self.assertIn(TASK_CONTEXT_META_KEY, body["result"]["_meta"])
        self.assertEqual(body["result"]["resultType"], "complete")
        discovery = self.runtime.connector_tool_discovery()
        self.assertTrue(discovery["current_contract_observed"])
        self.assertEqual(discovery["contract_sha256"], self.runtime.tool_contract["sha256"])
        self.assertEqual(discovery["client_id"], "chatweb")
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        try:
            connection.request("GET", "/__control/health")
            response = connection.getresponse()
            health = json.loads(response.read().decode("utf-8"))
        finally:
            connection.close()
        self.assertEqual(response.status, 200)
        self.assertTrue(health["connector_tool_discovery"]["current_contract_observed"])

    def test_tools_call_records_current_contact_without_fabricating_discovery(self) -> None:
        self.assertFalse(self.runtime.connector_tool_discovery()["observed"])
        self.assertFalse(self.runtime.connector_client_contact()["observed"])

        status, _, body = self.tool_call(
            "workspace_context",
            {"detail": "compact", "max_entries": 1},
            request_id=3,
        )
        self.assertEqual(status, 200)
        self.assertFalse(body["result"]["isError"])
        self.assertFalse(self.runtime.connector_tool_discovery()["observed"])

        contact = self.runtime.connector_client_contact()
        self.assertTrue(contact["current_contract_contact"])
        self.assertEqual(contact["contract_sha256"], self.runtime.tool_contract["sha256"])
        self.assertEqual(contact["method"], "tools/call")
        self.assertEqual(contact["client_id"], "chatweb")
        self.assertEqual(contact["process_instance_id"], self.runtime.process_instance_id)
        self.assertEqual(contact["server_instance_id"], self.runtime.server_instance_id)

        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        try:
            connection.request("GET", "/__control/health")
            response = connection.getresponse()
            health = json.loads(response.read().decode("utf-8"))
        finally:
            connection.close()
        self.assertEqual(response.status, 200)
        self.assertFalse(health["connector_tool_discovery"]["observed"])
        self.assertTrue(health["connector_client_contact"]["current_contract_contact"])

    def test_stateless_task_contexts_isolate_global_and_parallel_runs(self) -> None:
        global_state = self.runtime.task_state.ensure_started("global-sentinel")
        self.assertEqual(global_state["objective"], "global-sentinel")

        status, _, body = self.tool_call("task_control", {"action": "get"}, request_id=20)
        self.assertEqual(status, 200)
        self.assertFalse(body["result"]["isError"])
        minted = body["result"]["_meta"][TASK_CONTEXT_META_KEY]
        structured = body["result"]["structuredContent"]
        self.assertEqual(structured["task_context_id"], minted)
        self.assertNotEqual(structured["state"]["objective"], "global-sentinel")
        self.assertEqual(self.runtime.task_state.get()["objective"], "global-sentinel")

        def prepare(context_id: str, objective: str, request_id: int) -> dict:
            status, _, response = self.tool_call(
                "agent_workflow",
                {
                    "task_context_id": context_id,
                    "workflow": "diagnose",
                    "phase": "prepare",
                    "objective": objective,
                    "execution_route": "deterministic",
                    "execution_mode": "mcp_only",
                    "verification": "none",
                    "path": ".",
                },
                request_id=request_id,
            )
            self.assertEqual(status, 200)
            self.assertFalse(response["result"]["isError"])
            result = response["result"]["structuredContent"]
            self.assertEqual(result["task_context_id"], context_id)
            return result

        first = prepare("context-a", "stateless-context-a", 21)
        second = prepare("context-b", "stateless-context-b", 22)
        first_run = first["orchestration"]["run_id"]
        second_run = second["orchestration"]["run_id"]
        self.assertTrue(first_run)
        self.assertTrue(second_run)
        self.assertNotEqual(first_run, second_run)

        for request_id, context_id, objective, run_id in (
            (23, "context-a", "stateless-context-a", first_run),
            (24, "context-b", "stateless-context-b", second_run),
        ):
            status, _, response = self.tool_call(
                "task_control",
                {"action": "get", "task_context_id": context_id},
                request_id=request_id,
            )
            self.assertEqual(status, 200)
            result = response["result"]["structuredContent"]
            self.assertEqual(result["task_context_id"], context_id)
            self.assertEqual(result["state"]["objective"], objective)
            self.assertEqual(result["state"]["orchestration"]["run_id"], run_id)
        self.assertEqual(self.runtime.task_state.get()["objective"], "global-sentinel")

    def test_task_control_recovers_exact_run_context_when_connector_omits_handle(self) -> None:
        context_id = "continuity-context"
        status, _, prepared = self.tool_call(
            "agent_workflow",
            {
                "task_context_id": context_id,
                "workflow": "diagnose",
                "phase": "prepare",
                "objective": "stateless-continuity",
                "execution_route": "deterministic",
                "execution_mode": "mcp_only",
                "verification": "none",
                "path": ".",
            },
            request_id=120,
        )
        self.assertEqual(status, 200)
        prepared_result = prepared["result"]["structuredContent"]
        run_id = prepared_result["orchestration"]["run_id"]
        wave_id = prepared_result["orchestration"]["wave_id"]

        status, _, fetched = self.tool_call(
            "task_control",
            {"action": "get", "run_id": run_id},
            request_id=121,
        )
        self.assertEqual(status, 200)
        self.assertFalse(fetched["result"]["isError"], fetched)
        self.assertEqual(fetched["result"]["_meta"][TASK_CONTEXT_META_KEY], context_id)
        fetched_state = fetched["result"]["structuredContent"]["state"]
        self.assertEqual(fetched_state["orchestration"]["run_id"], run_id)

        store = TaskStateStore(Path(self.temp.name), scope_id=f"mcp2026:{context_id}")
        store.set_completion_report({
            "schema_version": 1,
            "operator_visible_required": True,
            "accepted_or_not": "NOT_ACCEPTED_REPLAN_REQUIRED",
            "current_state": {"orchestration_state": "REPLAN"},
            "source_run_wave": {"run_id": run_id, "wave_id": wave_id},
            "next_critical_action": "continue with changed evidence",
        })
        report_id = store.get()["completion_report_id"]
        status, _, acknowledged = self.tool_call(
            "task_control",
            {"action": "ack", "run_id": run_id, "wave_id": wave_id, "message_id": report_id},
            request_id=122,
        )
        self.assertEqual(status, 200)
        self.assertFalse(acknowledged["result"]["isError"], acknowledged)
        self.assertEqual(acknowledged["result"]["_meta"][TASK_CONTEXT_META_KEY], context_id)
        self.assertEqual(store.get()["completion_report_acknowledged_id"], report_id)

        status, _, fresh = self.tool_call("task_control", {"action": "get"}, request_id=123)
        self.assertEqual(status, 200)
        self.assertNotEqual(fresh["result"]["_meta"][TASK_CONTEXT_META_KEY], context_id)

        controller = self.runtime.orchestration_ledger.get_controller_lease(run_id)
        self.assertIsNotNone(controller)
        self.assertTrue(self.runtime.orchestration_ledger.release_controller_lease(
            run_id=run_id,
            owner_client_id=controller["owner_client_id"],
            lease_id=controller["lease_id"],
            fencing_token=controller["fencing_token"],
        ))
        self.runtime.orchestration_ledger.upsert_hub_client(
            client_id="codex-desktop",
            client_type="codex_desktop",
            role="worker",
        )
        claimed = self.runtime.orchestration_ledger.acquire_controller_lease(
            run_id=run_id,
            owner_client_id="codex-desktop",
            lease_id="desktop-controller",
            ttl_seconds=60,
        )
        self.assertTrue(claimed["acquired"], claimed)
        status, _, foreign_owned = self.tool_call(
            "task_control",
            {"action": "get", "run_id": run_id},
            request_id=124,
        )
        self.assertEqual(status, 200)
        self.assertNotEqual(foreign_owned["result"]["_meta"][TASK_CONTEXT_META_KEY], context_id)

    def test_workspace_context_returns_the_minted_task_context_id(self) -> None:
        status, _, response = self.tool_call(
            "workspace_context",
            {"detail": "compact", "path": "."},
            request_id=25,
        )
        self.assertEqual(status, 200)
        self.assertFalse(response["result"]["isError"], response)
        result = response["result"]
        minted = result["_meta"][TASK_CONTEXT_META_KEY]
        self.assertEqual(result["structuredContent"]["task_context_id"], minted)

    def test_task_control_stop_recovers_exact_run_context_when_connector_omits_handle(self) -> None:
        context_id = "stop-continuity-context"
        status, _, prepared = self.tool_call(
            "agent_workflow",
            {
                "task_context_id": context_id,
                "workflow": "diagnose",
                "phase": "prepare",
                "objective": "stateless-stop-continuity",
                "execution_route": "deterministic",
                "execution_mode": "mcp_only",
                "verification": "none",
                "path": ".",
            },
            request_id=125,
        )
        self.assertEqual(status, 200)
        prepared_result = prepared["result"]["structuredContent"]
        run_id = prepared_result["orchestration"]["run_id"]
        self.assertEqual(self.runtime.orchestration_ledger.get_run(run_id)["status"], "active")

        status, _, stopped = self.tool_call(
            "task_control",
            {"action": "stop", "run_id": run_id, "reason": "superseded exact run"},
            request_id=126,
        )
        self.assertEqual(status, 200)
        self.assertFalse(stopped["result"]["isError"], stopped)
        self.assertEqual(stopped["result"]["_meta"][TASK_CONTEXT_META_KEY], context_id)
        stopped_result = stopped["result"]["structuredContent"]
        self.assertTrue(stopped_result["stopped"])
        self.assertEqual(stopped_result["target_run_id"], run_id)
        self.assertFalse(stopped_result["detached"])
        self.assertEqual(stopped_result["orchestration"]["run_id"], run_id)
        self.assertEqual(stopped_result["orchestration"]["orchestration_state"], "ABORTED")
        self.assertEqual(self.runtime.orchestration_ledger.get_run(run_id)["status"], "aborted")

    def test_controller_usage_binds_to_scoped_run_and_deduplicates_before_dispatch(self) -> None:
        context_id = "usage-context"
        status, _, prepared = self.tool_call(
            "agent_workflow",
            {
                "task_context_id": context_id,
                "workflow": "diagnose",
                "phase": "prepare",
                "objective": "controller-usage-existing-run",
                "execution_route": "deterministic",
                "execution_mode": "mcp_only",
                "verification": "none",
                "path": ".",
            },
            request_id=30,
        )
        self.assertEqual(status, 200)
        run_id = prepared["result"]["structuredContent"]["orchestration"]["run_id"]

        usage = self.controller_usage("controller-turn-1")
        status, _, recorded = self.tool_call(
            "task_control",
            {"action": "get", "task_context_id": context_id},
            request_id=31,
            controller_usage=usage,
        )
        self.assertEqual(status, 200)
        receipt = recorded["result"]["_meta"][CONTROLLER_USAGE_STATUS_META_KEY]
        self.assertEqual(receipt["status"], "recorded")
        self.assertEqual(receipt["turn_id"], "controller-turn-1")
        self.assertTrue(receipt["usage_id"])

        events = self.runtime.orchestration_ledger.list_usage_events(run_id, limit=None)
        controller_events = [item for item in events if item.get("actor") == "controller"]
        self.assertEqual(len(controller_events), 1)
        self.assertEqual(controller_events[0]["turn_id"], "controller-turn-1")
        self.assertEqual(controller_events[0]["usage"]["input_total_tokens"], 100)
        self.assertEqual(controller_events[0]["usage"]["input_cached_tokens"], 30)
        self.assertEqual(controller_events[0]["usage"]["output_total_tokens"], 20)
        self.assertEqual(controller_events[0]["usage"]["total_tokens"], 120)

        status, _, duplicate = self.tool_call(
            "task_control",
            {"action": "get", "task_context_id": context_id},
            request_id=32,
            controller_usage=usage,
        )
        self.assertEqual(status, 200)
        self.assertEqual(duplicate["result"]["_meta"][CONTROLLER_USAGE_STATUS_META_KEY]["status"], "duplicate")
        self.assertEqual(len([
            item for item in self.runtime.orchestration_ledger.list_usage_events(run_id, limit=None)
            if item.get("actor") == "controller"
        ]), 1)

        conflict = self.controller_usage("controller-turn-1", output_tokens=21)
        status, _, rejected = self.tool_call(
            "task_control",
            {"action": "get", "task_context_id": context_id},
            request_id=33,
            controller_usage=conflict,
        )
        self.assertEqual(status, 200)
        self.assertEqual(rejected["error"]["code"], -32602)
        self.assertIn("different evidence", rejected["error"]["message"])

    def test_first_agent_workflow_usage_is_prevalidated_then_bound_after_run_creation(self) -> None:
        usage = self.controller_usage("controller-first-turn")
        status, _, body = self.tool_call(
            "agent_workflow",
            {
                "task_context_id": "usage-first-context",
                "workflow": "diagnose",
                "phase": "prepare",
                "objective": "controller-usage-first-run",
                "execution_route": "deterministic",
                "execution_mode": "mcp_only",
                "verification": "none",
                "path": ".",
            },
            request_id=34,
            controller_usage=usage,
        )
        self.assertEqual(status, 200)
        self.assertFalse(body["result"]["isError"])
        receipt = body["result"]["_meta"][CONTROLLER_USAGE_STATUS_META_KEY]
        self.assertEqual(receipt["status"], "recorded")
        structured = body["result"]["structuredContent"]
        run_id = structured["orchestration"]["run_id"]
        wave_id = structured["orchestration"]["wave_id"]
        events = self.runtime.orchestration_ledger.list_usage_events(run_id, limit=None)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["wave_id"], wave_id)
        self.assertEqual(events[0]["actor"], "controller")
        self.assertEqual(events[0]["turn_id"], "controller-first-turn")

    def test_controller_usage_rejects_invalid_or_non_chatweb_reports_before_first_run(self) -> None:
        invalid = self.controller_usage("invalid-first-turn")
        invalid["cached_input_tokens"] = -1
        args = {
            "task_context_id": "usage-invalid-context",
            "workflow": "diagnose",
            "phase": "prepare",
            "objective": "must-not-start-invalid-usage",
            "execution_route": "deterministic",
            "execution_mode": "mcp_only",
            "verification": "none",
            "path": ".",
        }
        status, _, body = self.tool_call("agent_workflow", args, request_id=35, controller_usage=invalid)
        self.assertEqual(status, 200)
        self.assertEqual(body["error"]["code"], -32602)
        self.assertEqual(self.runtime.orchestration_ledger.list_runs(limit=10), [])

        status, _, body = self.tool_call(
            "agent_workflow",
            {**args, "task_context_id": "usage-non-chatweb-context"},
            request_id=36,
            controller_usage=self.controller_usage("non-chatweb-turn"),
            extra_headers={
                "X-Coding-Tools-Client-Id": "electron-panel",
                "X-Coding-Tools-Client-Type": "electron",
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["error"]["code"], -32602)
        self.assertEqual(self.runtime.orchestration_ledger.list_runs(limit=10), [])

    def test_tools_call_ignores_legacy_session_header_and_never_echoes_it(self) -> None:
        status, headers, body = self.request(
            "tools/call",
            modern_params({"name": "workspace_context", "arguments": {"detail": "compact", "path": "."}}),
            request_id=3,
            extra_headers={"Mcp-Name": "workspace_context", "Mcp-Session-Id": "legacy-session-must-be-ignored"},
        )
        self.assertEqual(status, 200)
        self.assertNotIn("mcp-session-id", headers)
        self.assertEqual(body["result"]["resultType"], "complete")
        self.assertFalse(body["result"]["isError"])

    def test_header_and_meta_contract_fail_closed(self) -> None:
        status, _, body = self.request("tools/list", modern_params(), extra_headers={"Mcp-Method": "wrong/method"})
        self.assertEqual(status, 400)
        self.assertEqual(body["error"]["code"], -32020)

        missing_caps = {"_meta": {"io.modelcontextprotocol/protocolVersion": STATELESS_PROTOCOL_VERSION}}
        status, _, body = self.request("tools/list", missing_caps, request_id=4)
        self.assertEqual(status, 200)
        self.assertEqual(body["error"]["code"], -32602)

        status, _, body = self.request("tools/call", modern_params({"name": "workspace_context", "arguments": {}}), request_id=5)
        self.assertEqual(status, 400)
        self.assertEqual(body["error"]["code"], -32020)

    def test_modern_initialize_is_removed(self) -> None:
        status, headers, body = self.request("initialize", modern_params(), request_id=6)
        self.assertEqual(status, 404)
        self.assertNotIn("mcp-session-id", headers)
        self.assertEqual(body["error"]["code"], -32601)

    def test_canary_disabled_rejects_modern_request_without_affecting_legacy_default(self) -> None:
        with patch.dict(os.environ, {"CODING_TOOLS_MCP_STATELESS_HTTP_2026": "0"}):
            status, headers, body = self.request("tools/list", modern_params(), request_id=7)
        self.assertEqual(status, 400)
        self.assertNotIn("mcp-session-id", headers)
        self.assertEqual(body["error"]["code"], -32022)

    def test_modern_era_is_served_by_default_without_the_canary_flag(self) -> None:
        with patch.dict(os.environ):
            os.environ.pop("CODING_TOOLS_MCP_STATELESS_HTTP_2026", None)
            status, headers, body = self.request("tools/list", modern_params(), request_id=8)
        self.assertEqual(status, 200)
        self.assertNotIn("mcp-session-id", headers)
        self.assertIn("result", body)
        self.assertIn("tools", body["result"])

    def test_legacy_handshake_still_works_when_modern_era_is_default_on(self) -> None:
        with patch.dict(os.environ):
            os.environ.pop("CODING_TOOLS_MCP_STATELESS_HTTP_2026", None)
            legacy_headers = {
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            }
            body = json.dumps({
                "jsonrpc": "2.0",
                "id": 9,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-11-25",
                    "capabilities": {},
                    "clientInfo": {"name": "legacy-client", "version": "1"},
                },
            }).encode("utf-8")
            connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
            try:
                connection.request("POST", "/mcp", body=body, headers=legacy_headers)
                response = connection.getresponse()
                raw = response.read()
                decoded = json.loads(raw.decode("utf-8")) if raw else {}
                self.assertEqual(response.status, 200)
                self.assertIn("result", decoded)
                self.assertIn("protocolVersion", decoded["result"])
            finally:
                connection.close()

    def test_legacy_sessionless_initialized_notification_is_a_noop(self) -> None:
        """Accept tunnel probes that omit the legacy session header on this no-op.

        The server-issued session remains required for stateful requests.  This
        narrow compatibility path only prevents a legacy tunnel health probe
        from failing after its successful initialize response; it must not
        create a session or record connector discovery.
        """
        with patch.dict(os.environ):
            os.environ.pop("CODING_TOOLS_MCP_STATELESS_HTTP_2026", None)
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            }
            initialize = json.dumps({
                "jsonrpc": "2.0",
                "id": 10,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "tunnel-probe", "version": "1"},
                },
            }).encode("utf-8")
            connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
            try:
                connection.request("POST", "/mcp", body=initialize, headers=headers)
                initialized = connection.getresponse()
                self.assertEqual(initialized.status, 200)
                self.assertTrue(initialized.getheader("Mcp-Session-Id"))
                initialized.read()
            finally:
                connection.close()

            notification = json.dumps({
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {},
            }).encode("utf-8")
            connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
            try:
                connection.request("POST", "/mcp", body=notification, headers=headers)
                response = connection.getresponse()
                self.assertEqual(response.status, 202)
                self.assertEqual(response.read(), b"")
            finally:
                connection.close()

        self.assertFalse(self.runtime.connector_tool_discovery()["observed"])

    def test_initialized_notification_allows_legacy_transport_protocol_header(self) -> None:
        """A stateful tunnel probe may reuse a transport-default protocol header.

        ``notifications/initialized`` is a no-op.  It must not fail the whole
        channel merely because its header differs from the version negotiated
        by ``initialize``; stateful requests remain strict.
        """
        with patch.dict(os.environ):
            os.environ.pop("CODING_TOOLS_MCP_STATELESS_HTTP_2026", None)
            initialize = json.dumps({
                "jsonrpc": "2.0",
                "id": 11,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "tunnel-probe", "version": "1"},
                },
            }).encode("utf-8")
            connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
            try:
                connection.request(
                    "POST",
                    "/mcp",
                    body=initialize,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json, text/event-stream",
                    },
                )
                initialized = connection.getresponse()
                self.assertEqual(initialized.status, 200)
                session_id = initialized.getheader("Mcp-Session-Id")
                self.assertTrue(session_id)
                initialized.read()
            finally:
                connection.close()

            notification = json.dumps({
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {},
            }).encode("utf-8")
            connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
            try:
                connection.request(
                    "POST",
                    "/mcp",
                    body=notification,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json, text/event-stream",
                        "Mcp-Session-Id": session_id,
                        "MCP-Protocol-Version": "2025-03-26",
                    },
                )
                response = connection.getresponse()
                self.assertEqual(response.status, 202)
                self.assertEqual(response.read(), b"")
            finally:
                connection.close()


if __name__ == "__main__":
    unittest.main()
