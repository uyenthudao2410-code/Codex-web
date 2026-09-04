from __future__ import annotations

import http.client
import json
import os
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from coding_tools_mcp.controller_usage_ingress import CONTROLLER_USAGE_META_KEY, CONTROLLER_USAGE_STATUS_META_KEY
from coding_tools_mcp.connector_attestation import CONNECTOR_ATTESTATION_HEADER, build_connector_attestation
from coding_tools_mcp.host_correlation import HOST_CORRELATION_PENDING_RELATIVE, HOST_CORRELATION_SCHEMA_VERSION
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
ENDPOINT_META_KEY = "io.coding-tools/endpoint"
ENDPOINT_ROUTING_META_KEY = "io.coding-tools/routingInstructions"


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
                "CODING_TOOLS_MCP_DEVICE_ID": "11111111-1111-4111-8111-111111111111",
                "CODING_TOOLS_MCP_DEVICE_INSTANCE_ID": "device-instance-office-0001",
                "CODING_TOOLS_MCP_DEVICE_DISPLAY_NAME": "Office Workstation",
                "CODING_TOOLS_MCP_CONNECTOR_ATTESTATION_SECRET": "test-connector-attestation-secret",
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
            # Model the managed Coding Tunnel, which explicitly forwards its
            # caller identity to MCP.  A separate regression below exercises
            # a direct loopback request without these provenance headers.
            "X-Coding-Tools-Client-Id": "chatweb",
            "X-Coding-Tools-Client-Type": "chatweb",
        }
        headers.update(extra_headers or {})
        if CONNECTOR_ATTESTATION_HEADER not in headers and "X-Coding-Tools-Client-Id" in headers and "X-Coding-Tools-Client-Type" in headers:
            headers[CONNECTOR_ATTESTATION_HEADER] = build_connector_attestation(
                "test-connector-attestation-secret",
                client_id=headers["X-Coding-Tools-Client-Id"],
                client_type=headers["X-Coding-Tools-Client-Type"],
                activation_epoch_id=getattr(self.runtime, "activation_epoch_id", ""),
                process_instance_id=self.runtime.process_instance_id,
                server_instance_id=self.runtime.server_instance_id,
                contract_sha256=self.runtime.tool_contract["sha256"],
            )
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
    def controller_usage(turn_id: str, *, output_tokens: int = 20, run_id: str = "", wave_id: str = "") -> dict:
        report = {
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
        if run_id and wave_id:
            report.update({"run_id": run_id, "wave_id": wave_id})
        return report

    def stage_host_turn(self, turn_id: str, trace_id: str = "trace-controller-usage") -> None:
        target = Path(self.temp.name) / HOST_CORRELATION_PENDING_RELATIVE
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps({
            "schema_version": HOST_CORRELATION_SCHEMA_VERSION,
            "turn_id": turn_id,
            "trace_id": trace_id,
            "staged_at_unix_ms": int(time.time() * 1000),
        }), encoding="utf-8")

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
        server_info = result["_meta"]["io.modelcontextprotocol/serverInfo"]
        self.assertEqual(server_info["name"], "coding-tools-mcp")
        self.assertIn("Office Workstation", server_info["title"])
        endpoint = result["_meta"][ENDPOINT_META_KEY]
        self.assertEqual(endpoint["endpoint_scope"], "device_installation")
        self.assertEqual(endpoint["display_name"], "Office Workstation")
        self.assertEqual(endpoint["device_instance_id"], "device-instance-office-0001")
        self.assertTrue(endpoint["automatic"])
        self.assertNotIn("11111111-1111-4111-8111-111111111111", json.dumps(endpoint))
        self.assertIn(endpoint["route_key"], result["_meta"][ENDPOINT_ROUTING_META_KEY])
        discovery = self.runtime.connector_tool_discovery()
        self.assertTrue(discovery["current_contract_observed"])
        self.assertEqual(discovery["identity_source"], "attested_transport")
        self.assertTrue(discovery["attestation_verified"])
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
        self.assertEqual(body["result"]["_meta"][ENDPOINT_META_KEY]["endpoint_id"], endpoint["endpoint_id"])
        discovery = self.runtime.connector_tool_discovery()
        self.assertTrue(discovery["current_contract_observed"])
        self.assertEqual(discovery["identity_source"], "attested_transport")
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

    def test_loopback_tools_list_without_identity_headers_is_not_authoritative_discovery(self) -> None:
        self.assertFalse(self.runtime.connector_tool_discovery()["observed"])
        headers = {
            "Content-Type": "application/json",
            "MCP-Protocol-Version": STATELESS_PROTOCOL_VERSION,
            "Mcp-Method": "tools/list",
        }
        body = json.dumps({"jsonrpc": "2.0", "id": 99, "method": "tools/list", "params": modern_params()}).encode("utf-8")
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        try:
            connection.request("POST", "/mcp", body=body, headers=headers)
            response = connection.getresponse()
            payload = json.loads(response.read().decode("utf-8"))
        finally:
            connection.close()
        self.assertEqual(response.status, 200)
        self.assertEqual({item["name"] for item in payload["result"]["tools"]}, EXPECTED_SMART_TOOLS)
        discovery = self.runtime.connector_tool_discovery()
        self.assertFalse(discovery["observed"])
        self.assertFalse(discovery["current_contract_observed"])

    def test_attestation_without_explicit_identity_is_observed_but_not_authoritative(self) -> None:
        activation_epoch_id = "activation-implicit-attestation-0001"
        self.runtime.activation_epoch_id = activation_epoch_id
        attestation = build_connector_attestation(
            "test-connector-attestation-secret",
            client_id="chatweb",
            client_type="chatweb",
            activation_epoch_id=activation_epoch_id,
            process_instance_id=self.runtime.process_instance_id,
            server_instance_id=self.runtime.server_instance_id,
            contract_sha256=self.runtime.tool_contract["sha256"],
        )
        headers = {
            "Content-Type": "application/json",
            "MCP-Protocol-Version": STATELESS_PROTOCOL_VERSION,
            "Mcp-Method": "tools/list",
            CONNECTOR_ATTESTATION_HEADER: attestation,
        }
        body = json.dumps({
            "jsonrpc": "2.0",
            "id": 103,
            "method": "tools/list",
            "params": modern_params(),
        }).encode("utf-8")
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        try:
            connection.request("POST", "/mcp", body=body, headers=headers)
            response = connection.getresponse()
            payload = json.loads(response.read().decode("utf-8"))
        finally:
            connection.close()
        self.assertEqual(response.status, 200)
        self.assertEqual({item["name"] for item in payload["result"]["tools"]}, EXPECTED_SMART_TOOLS)
        discovery = self.runtime.connector_tool_discovery()
        self.assertFalse(discovery["observed"])
        self.assertFalse(discovery["current_contract_observed"])
        self.assertIsNone(discovery["identity_source"])

    def test_explicit_chatweb_headers_without_attestation_are_not_authoritative(self) -> None:
        self.assertFalse(self.runtime.connector_tool_discovery()["observed"])
        status, _, payload = self.request(
            "tools/list",
            modern_params(),
            request_id=100,
            extra_headers={CONNECTOR_ATTESTATION_HEADER: ""},
        )
        self.assertEqual(status, 200)
        self.assertIn("result", payload)
        discovery = self.runtime.connector_tool_discovery()
        self.assertFalse(discovery["observed"])
        self.assertFalse(discovery["current_contract_observed"])

    def test_long_lived_managed_attestation_records_authoritative_discovery(self) -> None:
        self.assertFalse(self.runtime.connector_tool_discovery()["observed"])
        attestation = build_connector_attestation(
            "test-connector-attestation-secret",
            client_id="chatweb",
            client_type="chatweb",
            activation_epoch_id=getattr(self.runtime, "activation_epoch_id", ""),
            process_instance_id=self.runtime.process_instance_id,
            server_instance_id=self.runtime.server_instance_id,
            contract_sha256=self.runtime.tool_contract["sha256"],
            issued_at_unix_ms=int(time.time() * 1000) - 24 * 60 * 60 * 1000,
        )
        status, _, payload = self.request(
            "tools/list",
            modern_params(),
            request_id=104,
            extra_headers={CONNECTOR_ATTESTATION_HEADER: attestation},
        )
        self.assertEqual(status, 200)
        self.assertIn("result", payload)
        discovery = self.runtime.connector_tool_discovery()
        self.assertTrue(discovery["current_contract_observed"])
        self.assertEqual(discovery["identity_source"], "attested_transport")
        self.assertTrue(discovery["attestation_verified"])
        self.assertEqual(discovery["process_instance_id"], self.runtime.process_instance_id)
        self.assertEqual(discovery["server_instance_id"], self.runtime.server_instance_id)

    def test_untrusted_loopback_observation_cannot_overwrite_attested_discovery(self) -> None:
        status, _, payload = self.request("tools/list", modern_params(), request_id=101)
        self.assertEqual(status, 200)
        self.assertIn("result", payload)
        authoritative = self.runtime.connector_tool_discovery()
        self.assertTrue(authoritative["current_contract_observed"])
        self.assertTrue(authoritative["attestation_verified"])

        headers = {
            "Content-Type": "application/json",
            "MCP-Protocol-Version": STATELESS_PROTOCOL_VERSION,
            "Mcp-Method": "tools/list",
        }
        body = json.dumps({"jsonrpc": "2.0", "id": 102, "method": "tools/list", "params": modern_params()}).encode("utf-8")
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        try:
            connection.request("POST", "/mcp", body=body, headers=headers)
            response = connection.getresponse()
            response.read()
        finally:
            connection.close()
        self.assertEqual(response.status, 200)
        after_untrusted = self.runtime.connector_tool_discovery()
        self.assertTrue(after_untrusted["current_contract_observed"])
        self.assertTrue(after_untrusted["attestation_verified"])
        self.assertEqual(after_untrusted["observed_at"], authoritative["observed_at"])

    def test_tools_call_records_current_contact_without_fabricating_discovery(self) -> None:
        self.assertFalse(self.runtime.connector_tool_discovery()["observed"])
        self.assertFalse(self.runtime.connector_client_contact()["observed"])
        self.assertEqual(self.runtime.connector_controller_usage_envelope()["classification"], "unobserved")

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
        envelope = self.runtime.connector_controller_usage_envelope()
        self.assertTrue(envelope["current_process_observed"])
        self.assertEqual(envelope["classification"], "absent_so_far")
        self.assertEqual(envelope["call_count"], 1)
        self.assertEqual(envelope["meta_present_count"], 0)
        self.assertEqual(envelope["meta_absent_count"], 1)
        self.assertFalse(envelope["latest_meta_present"])
        self.assertEqual(envelope["identity_source"], "attested_transport")
        self.assertTrue(envelope["attestation_verified"])

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
        self.assertEqual(health["connector_controller_usage_envelope"]["classification"], "absent_so_far")

    def test_activation_pending_tool_error_does_not_record_connector_contact(self) -> None:
        self.assertFalse(self.runtime.connector_tool_discovery()["observed"])
        self.assertFalse(self.runtime.connector_client_contact()["observed"])
        self.runtime.activation_epoch_id = "activation-pending-contact-0001"
        self.runtime.activation_gate_config = "closed"
        self.runtime.activation_admission = "closed"

        status, _, body = self.tool_call(
            "task_control",
            {"action": "get"},
            request_id=4,
        )

        self.assertEqual(status, 200)
        self.assertTrue(body["result"]["isError"])
        self.assertEqual(
            body["result"]["structuredContent"]["error"]["code"],
            "RUNTIME_ACTIVATION_PENDING",
        )
        self.assertFalse(
            self.runtime.connector_client_contact()["observed"],
            "a tool-level activation error is not a successful connector contact",
        )
        self.assertFalse(self.runtime.connector_tool_discovery()["observed"])
        self.assertFalse(self.runtime.connector_activation_bootstrap()["observed"])

    def test_closed_epoch_workspace_context_keeps_first_bootstrap_across_retries_and_open_retry(self) -> None:
        self.assertTrue(self.runtime.tool_contract["compatible_predecessor_sha256"])
        self.runtime.activation_epoch_id = "activation-bootstrap-connector-0001"
        self.runtime.activation_gate_config = "closed"
        self.runtime.activation_admission = "closed"

        status, _, body = self.tool_call(
            "workspace_context",
            {"path": "definitely-not-an-authorized-or-existing-workspace", "detail": "compact"},
            request_id=5,
            extra_headers={
                "X-Coding-Tools-Client-Id": "chatweb-bootstrap-first",
                "X-Coding-Tools-Client-Type": "chatweb",
            },
        )

        self.assertEqual(status, 200)
        self.assertFalse(body["result"]["isError"])
        structured = body["result"]["structuredContent"]
        self.assertTrue(structured["ok"])
        self.assertFalse(structured["completed"])
        self.assertFalse(structured["workspace_accessed"])
        self.assertTrue(structured["activation_bootstrap"]["accepted"])
        self.assertTrue(structured["activation_bootstrap"]["retry_required"])
        self.assertEqual(
            structured["activation_bootstrap"]["activation_epoch_id"],
            "activation-bootstrap-connector-0001",
        )
        self.assertFalse(self.runtime.connector_client_contact()["observed"])
        self.assertFalse(self.runtime.connector_tool_discovery()["observed"])
        bootstrap = self.runtime.connector_activation_bootstrap()
        self.assertTrue(bootstrap["current_contract_contact"])
        self.assertEqual(bootstrap["tool_name"], "workspace_context")
        self.assertEqual(bootstrap["activation_epoch_id"], "activation-bootstrap-connector-0001")
        self.assertEqual(bootstrap["client_type"], "chatweb")
        self.assertFalse(bootstrap["workspace_accessed"])
        self.assertFalse(self.runtime.connector_client_contact()["observed"])

        first_observed_at = bootstrap["observed_at"]
        first_client_id = bootstrap["client_id"]
        status, _, retry_body = self.tool_call(
            "workspace_context",
            {"path": "still-not-an-authorized-or-existing-workspace", "detail": "compact"},
            request_id=6,
            extra_headers={
                "X-Coding-Tools-Client-Id": "chatweb-bootstrap-retry",
                "X-Coding-Tools-Client-Type": "chatweb",
            },
        )
        self.assertEqual(status, 200)
        self.assertTrue(retry_body["result"]["structuredContent"]["activation_bootstrap"]["retry_required"])
        after_closed_retry = self.runtime.connector_activation_bootstrap()
        self.assertEqual(after_closed_retry["observed_at"], first_observed_at)
        self.assertEqual(after_closed_retry["client_id"], first_client_id)
        self.assertEqual(len(self.runtime.activation_bootstrap_receipts), 1)

        self.runtime.activation_admission = "open"
        status, _, open_body = self.tool_call(
            "workspace_context",
            {"path": self.temp.name, "detail": "compact", "max_entries": 1},
            request_id=7,
            extra_headers={
                "X-Coding-Tools-Client-Id": "chatweb-bootstrap-retry",
                "X-Coding-Tools-Client-Type": "chatweb",
            },
        )
        self.assertEqual(status, 200)
        self.assertFalse(open_body["result"]["isError"])
        opened = open_body["result"]["structuredContent"]
        self.assertTrue(opened["ok"])
        self.assertEqual(Path(opened["workspace"]).resolve(), Path(self.temp.name).resolve())
        self.assertNotIn("activation_bootstrap", opened)
        after_open_retry = self.runtime.connector_activation_bootstrap()
        self.assertEqual(after_open_retry["observed_at"], first_observed_at)
        self.assertEqual(after_open_retry["client_id"], first_client_id)

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

    def test_task_control_recovers_exact_run_from_archived_context_after_terminal_pollution(self) -> None:
        context_id = "archived-continuity-context"
        status, _, prepared = self.tool_call(
            "agent_workflow",
            {
                "task_context_id": context_id,
                "workflow": "diagnose",
                "phase": "prepare",
                "objective": "archived-stateless-continuity",
                "execution_route": "deterministic",
                "execution_mode": "mcp_only",
                "verification": "none",
                "path": ".",
            },
            request_id=127,
        )
        self.assertEqual(status, 200)
        prepared_result = prepared["result"]["structuredContent"]
        run_id = prepared_result["orchestration"]["run_id"]
        store = TaskStateStore(Path(self.temp.name), scope_id=f"mcp2026:{context_id}")
        canonical = store.get()
        canonical_task_id = canonical["task_id"]
        canonical_objective = canonical["objective"]

        store.update({"status": "failed", "failure": "archive canonical projection"})
        store.ensure_started("polluting-auto-start-like-task")
        polluted_task_id = store.get()["task_id"]
        self.assertNotEqual(polluted_task_id, canonical_task_id)
        store.update({"status": "failed", "failure": "terminal pollution"})

        status, _, recovered = self.tool_call(
            "task_control",
            {"action": "audit", "run_id": run_id},
            request_id=128,
        )
        self.assertEqual(status, 200)
        self.assertFalse(recovered["result"]["isError"], recovered)
        self.assertEqual(recovered["result"]["_meta"][TASK_CONTEXT_META_KEY], context_id)
        recovered_state = recovered["result"]["structuredContent"]["state"]
        self.assertEqual(recovered_state["task_id"], canonical_task_id)
        self.assertEqual(recovered_state["objective"], canonical_objective)
        self.assertEqual(recovered_state["orchestration"]["run_id"], run_id)
        persisted_state = store.get()
        self.assertEqual(persisted_state["task_id"], canonical_task_id)
        self.assertEqual(persisted_state["objective"], canonical_objective)
        self.assertEqual(persisted_state["orchestration"]["run_id"], run_id)

        status, _, resumed = self.tool_call(
            "task_control",
            {"action": "get", "task_context_id": context_id},
            request_id=1281,
        )
        self.assertEqual(status, 200)
        self.assertFalse(resumed["result"]["isError"], resumed)
        self.assertEqual(resumed["result"]["_meta"][TASK_CONTEXT_META_KEY], context_id)
        resumed_state = resumed["result"]["structuredContent"]["state"]
        self.assertEqual(resumed_state["task_id"], canonical_task_id)
        self.assertEqual(resumed_state["orchestration"]["run_id"], run_id)
        self.assertTrue(any(item.get("task_id") == polluted_task_id for item in store.history(100)))

    def test_task_control_exact_run_recovery_refuses_active_conflicting_task(self) -> None:
        context_id = "active-conflict-continuity-context"
        status, _, prepared = self.tool_call(
            "agent_workflow",
            {
                "task_context_id": context_id,
                "workflow": "diagnose",
                "phase": "prepare",
                "objective": "active-conflict-canonical",
                "execution_route": "deterministic",
                "execution_mode": "mcp_only",
                "verification": "none",
                "path": ".",
            },
            request_id=129,
        )
        self.assertEqual(status, 200)
        run_id = prepared["result"]["structuredContent"]["orchestration"]["run_id"]
        store = TaskStateStore(Path(self.temp.name), scope_id=f"mcp2026:{context_id}")
        store.update({"status": "failed", "failure": "archive canonical projection"})
        store.ensure_started("active-conflicting-task")

        status, _, refused = self.tool_call(
            "task_control",
            {"action": "get", "run_id": run_id},
            request_id=130,
        )
        self.assertEqual(status, 200)
        self.assertTrue(refused["result"]["isError"], refused)
        error = refused["result"]["structuredContent"]["error"]
        self.assertEqual(error["code"], "EXACT_RUN_RECOVERY_REFUSED")
        self.assertNotEqual(refused["result"]["_meta"][TASK_CONTEXT_META_KEY], context_id)
        self.assertEqual(store.get()["objective"], "active-conflicting-task")

    def test_task_control_exact_run_recovery_refuses_pending_operator_report(self) -> None:
        context_id = "pending-report-continuity-context"
        status, _, prepared = self.tool_call(
            "agent_workflow",
            {
                "task_context_id": context_id,
                "workflow": "diagnose",
                "phase": "prepare",
                "objective": "pending-report-canonical",
                "execution_route": "deterministic",
                "execution_mode": "mcp_only",
                "verification": "none",
                "path": ".",
            },
            request_id=131,
        )
        self.assertEqual(status, 200)
        run_id = prepared["result"]["structuredContent"]["orchestration"]["run_id"]
        store = TaskStateStore(Path(self.temp.name), scope_id=f"mcp2026:{context_id}")
        store.update({"status": "failed", "failure": "archive canonical projection"})
        store.ensure_started("terminal-task-with-pending-report")
        store.update({"status": "failed"})
        store.set_completion_report({
            "schema_version": 1,
            "operator_visible_required": True,
            "accepted_or_not": "COMMAND_FAILED",
            "current_state": {},
            "next_critical_action": "operator must acknowledge before replacement",
        })
        pending = store.pending_completion_report()
        self.assertIsNotNone(pending)

        status, _, refused = self.tool_call(
            "task_control",
            {"action": "get", "run_id": run_id},
            request_id=132,
        )
        self.assertEqual(status, 200)
        self.assertTrue(refused["result"]["isError"], refused)
        self.assertEqual(
            refused["result"]["structuredContent"]["error"]["code"],
            "EXACT_RUN_RECOVERY_REFUSED",
        )
        self.assertNotEqual(refused["result"]["_meta"][TASK_CONTEXT_META_KEY], context_id)
        self.assertEqual(store.pending_completion_report()["report_id"], pending["report_id"])

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
        self.stage_host_turn("controller-turn-1")
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
        orchestration = prepared["result"]["structuredContent"]["orchestration"]
        run_id = orchestration["run_id"]
        wave_id = orchestration["wave_id"]

        usage = self.controller_usage("controller-turn-1", run_id=run_id, wave_id=wave_id)
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
        envelope = self.runtime.connector_controller_usage_envelope()
        self.assertEqual(envelope["classification"], "present")
        self.assertGreaterEqual(envelope["meta_present_count"], 1)
        self.assertGreaterEqual(envelope["meta_absent_count"], 1)

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

        conflict = self.controller_usage("controller-turn-1", output_tokens=21, run_id=run_id, wave_id=wave_id)
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
        self.stage_host_turn("controller-first-turn")
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

    def test_attested_trace_correlates_external_chatweb_usage_without_electron_pending_file(self) -> None:
        trace_id = "a" * 32
        traceparent = f"00-{trace_id}-{'b' * 16}-01"
        context_id = "usage-attested-trace-context"
        status, _, prepared = self.tool_call(
            "agent_workflow",
            {
                "task_context_id": context_id,
                "workflow": "diagnose",
                "phase": "prepare",
                "objective": "controller-usage-attested-trace",
                "execution_route": "deterministic",
                "execution_mode": "mcp_only",
                "verification": "none",
                "path": ".",
            },
            request_id=346,
            extra_headers={"traceparent": traceparent},
        )
        self.assertEqual(status, 200)
        self.assertFalse(prepared["result"]["isError"], prepared)
        structured = prepared["result"]["structuredContent"]
        run_id = structured["orchestration"]["run_id"]
        wave_id = structured["orchestration"]["wave_id"]
        run = self.runtime.orchestration_ledger.get_run(run_id)
        metadata = run["metadata"]
        self.assertEqual(metadata["host_correlation"]["source"], "attested_chatweb_transport_trace")
        self.assertTrue(metadata["host_correlation"]["eligible"])
        self.assertTrue(metadata["host_correlation"]["content_free"])
        self.assertEqual(metadata["evaluation"]["trace_id"], trace_id)
        turn_id = f"chatweb-trace:{trace_id}"
        self.assertEqual(metadata["evaluation"]["turn_id"], turn_id)

        usage = self.controller_usage(turn_id, run_id=run_id, wave_id=wave_id)
        usage["trace_id"] = trace_id
        wrong_trace = "c" * 32
        status, _, rejected = self.tool_call(
            "task_control",
            {"action": "get", "task_context_id": context_id},
            request_id=347,
            controller_usage=usage,
            extra_headers={"traceparent": f"00-{wrong_trace}-{'d' * 16}-01"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(rejected["error"]["code"], -32602)
        self.assertIn("authoritative request trace", rejected["error"]["message"])
        self.assertEqual(self.runtime.orchestration_ledger.list_usage_events(run_id, limit=None), [])

        status, _, recorded = self.tool_call(
            "task_control",
            {"action": "get", "task_context_id": context_id},
            request_id=348,
            controller_usage=usage,
            extra_headers={"traceparent": traceparent},
        )
        self.assertEqual(status, 200)
        self.assertFalse(recorded["result"]["isError"], recorded)
        receipt = recorded["result"]["_meta"][CONTROLLER_USAGE_STATUS_META_KEY]
        self.assertEqual(receipt["status"], "recorded")
        self.assertEqual(receipt["turn_id"], turn_id)
        events = self.runtime.orchestration_ledger.list_usage_events(run_id, limit=None)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["turn_id"], turn_id)
        self.assertEqual(events[0]["usage"]["total_tokens"], 120)

    def test_transport_trace_never_becomes_host_authority_without_connector_attestation(self) -> None:
        trace_id = "e" * 32
        status, _, prepared = self.tool_call(
            "agent_workflow",
            {
                "task_context_id": "usage-unattested-trace-context",
                "workflow": "diagnose",
                "phase": "prepare",
                "objective": "controller-usage-unattested-trace",
                "execution_route": "deterministic",
                "execution_mode": "mcp_only",
                "verification": "none",
                "path": ".",
            },
            request_id=349,
            extra_headers={
                "traceparent": f"00-{trace_id}-{'f' * 16}-01",
                CONNECTOR_ATTESTATION_HEADER: "",
            },
        )
        self.assertEqual(status, 200)
        self.assertFalse(prepared["result"]["isError"], prepared)
        run_id = prepared["result"]["structuredContent"]["orchestration"]["run_id"]
        metadata = self.runtime.orchestration_ledger.get_run(run_id)["metadata"]
        self.assertNotIn("host_correlation", metadata)
        self.assertNotIn("turn_id", metadata.get("evaluation", {}))
        self.assertNotIn("trace_id", metadata.get("evaluation", {}))

    def test_existing_agent_workflow_rejects_deferred_usage_before_dispatch(self) -> None:
        context_id = "usage-existing-agent-context"
        self.stage_host_turn("controller-existing-agent-turn")
        status, _, prepared = self.tool_call(
            "agent_workflow",
            {
                "task_context_id": context_id,
                "workflow": "diagnose",
                "phase": "prepare",
                "objective": "controller-usage-existing-agent-run",
                "execution_route": "deterministic",
                "execution_mode": "mcp_only",
                "verification": "none",
                "path": ".",
            },
            request_id=341,
        )
        self.assertEqual(status, 200)
        self.assertFalse(prepared["result"]["isError"], prepared)
        orchestration = prepared["result"]["structuredContent"]["orchestration"]
        run_id = orchestration["run_id"]
        wave_id = orchestration["wave_id"]
        waves_before = len(self.runtime.orchestration_ledger.export_summary(run_id)["waves"])

        status, _, rejected = self.tool_call(
            "agent_workflow",
            {
                "task_context_id": context_id,
                "workflow": "diagnose",
                "phase": "prepare",
                "execution_route": "deterministic",
                "execution_mode": "mcp_only",
                "verification": "none",
                "path": ".",
            },
            request_id=342,
            controller_usage=self.controller_usage("controller-existing-agent-turn"),
        )
        self.assertEqual(status, 200)
        self.assertEqual(rejected["error"]["code"], -32602)
        self.assertIn("run_id and wave_id are required", rejected["error"]["message"])
        events = self.runtime.orchestration_ledger.list_usage_events(run_id, limit=None)
        self.assertEqual([item for item in events if item.get("actor") == "controller"], [])
        summary = self.runtime.orchestration_ledger.export_summary(run_id)
        self.assertEqual(len(summary["waves"]), waves_before)
        self.assertEqual(summary["waves"][-1]["wave_id"], wave_id)

    def test_fresh_context_does_not_inherit_another_context_controller_usage_authority(self) -> None:
        status, _, context_a = self.tool_call(
            "agent_workflow",
            {
                "task_context_id": "usage-cross-context-a",
                "workflow": "diagnose",
                "phase": "prepare",
                "objective": "controller-usage-cross-context-a",
                "execution_route": "deterministic",
                "execution_mode": "mcp_only",
                "verification": "none",
                "path": ".",
            },
            request_id=343,
        )
        self.assertEqual(status, 200)
        self.assertFalse(context_a["result"]["isError"], context_a)
        run_a = context_a["result"]["structuredContent"]["orchestration"]["run_id"]

        self.stage_host_turn("controller-cross-context-b-turn")
        status, _, context_b = self.tool_call(
            "agent_workflow",
            {
                "task_context_id": "usage-cross-context-b",
                "workflow": "diagnose",
                "phase": "prepare",
                "objective": "controller-usage-cross-context-b",
                "execution_route": "deterministic",
                "execution_mode": "mcp_only",
                "verification": "none",
                "path": ".",
            },
            request_id=344,
            controller_usage=self.controller_usage("controller-cross-context-b-turn"),
        )
        self.assertEqual(status, 200)
        self.assertFalse(context_b["result"]["isError"], context_b)
        structured_b = context_b["result"]["structuredContent"]
        run_b = structured_b["orchestration"]["run_id"]
        wave_b = structured_b["orchestration"]["wave_id"]
        self.assertNotEqual(run_b, run_a)
        receipt = context_b["result"]["_meta"][CONTROLLER_USAGE_STATUS_META_KEY]
        self.assertEqual(receipt["status"], "recorded")
        controller_b = [
            item for item in self.runtime.orchestration_ledger.list_usage_events(run_b, limit=None)
            if item.get("actor") == "controller"
        ]
        self.assertEqual(len(controller_b), 1)
        self.assertEqual(controller_b[0]["wave_id"], wave_b)
        self.assertEqual(controller_b[0]["turn_id"], "controller-cross-context-b-turn")
        self.assertEqual([
            item for item in self.runtime.orchestration_ledger.list_usage_events(run_a, limit=None)
            if item.get("actor") == "controller"
        ], [])

        self.stage_host_turn("controller-cross-context-b-second")
        status, _, rejected = self.tool_call(
            "agent_workflow",
            {
                "task_context_id": "usage-cross-context-b",
                "workflow": "diagnose",
                "phase": "prepare",
                "execution_route": "deterministic",
                "execution_mode": "mcp_only",
                "verification": "none",
                "path": ".",
            },
            request_id=345,
            controller_usage=self.controller_usage("controller-cross-context-b-second"),
        )
        self.assertEqual(status, 200)
        self.assertEqual(rejected["error"]["code"], -32602)
        self.assertIn("run_id and wave_id are required", rejected["error"]["message"])

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
