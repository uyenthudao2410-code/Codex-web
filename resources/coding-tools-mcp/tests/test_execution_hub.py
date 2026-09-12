import http.client
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

import coding_tools_mcp.mcp_http_handler as mcp_http_handler_module
from coding_tools_mcp.server import (
    MCPHandler,
    Runtime,
    RuntimeHTTPServer,
    STATELESS_PROTOCOL_VERSION,
)
from coding_tools_mcp.provider_traffic import ProviderTrafficGovernor
from coding_tools_mcp.usage_reservations import UsageReservationStore


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
        self.stateless_task_contexts = {}
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

    def post_stateless(self, *, action="get", client_id="", client_type="", after_seq=None, run_id=None):
        logical_client = client_id or "chatweb"
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
        task_context_id = self.stateless_task_contexts.get(logical_client)
        if task_context_id:
            arguments["task_context_id"] = task_context_id
        if after_seq is not None:
            arguments["after_seq"] = after_seq
        if run_id is not None:
            arguments["run_id"] = run_id
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
            parsed = json.loads(raw.decode("utf-8")) if raw else {}
            structured = parsed.get("result", {}).get("structuredContent", {}) if isinstance(parsed, dict) else {}
            returned_context_id = structured.get("task_context_id") if isinstance(structured, dict) else None
            if returned_context_id:
                self.stateless_task_contexts[logical_client] = str(returned_context_id)
            return response.status, parsed
        finally:
            connection.close()

    def claim_chatweb_controller(self):
        clients = [
            item
            for item in self.runtime.orchestration_ledger.list_hub_clients()
            if str(item.get("client_id") or "").startswith("chatweb:")
        ]
        self.assertEqual(len(clients), 1, clients)
        chatweb_id = str(clients[0]["client_id"])
        claimed = self.runtime.orchestration_ledger.acquire_controller_lease(
            run_id=self.ctx.run_id,
            owner_client_id=chatweb_id,
            lease_id=f"test:{chatweb_id}",
            ttl_seconds=60,
        )
        self.assertTrue(claimed["acquired"], claimed)
        return claimed

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

    def get_live_snapshot(self):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        try:
            connection.request("GET", "/__control/orchestration/live", headers={"Authorization": f"Bearer {self.TOKEN}"})
            response = connection.getresponse()
            return response.status, json.loads(response.read().decode("utf-8"))
        finally:
            connection.close()

    def get_dashboard_analytics(self):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        try:
            connection.request("GET", "/__control/orchestration/analytics", headers={"Authorization": f"Bearer {self.TOKEN}"})
            response = connection.getresponse()
            return response.status, json.loads(response.read().decode("utf-8"))
        finally:
            connection.close()

    def test_task_list_uses_the_canonical_orchestration_ledger_not_task_state_projection(self) -> None:
        self.runtime.task_state.update({
            "objective": "projection-only stale objective",
            "status": "paused",
        })

        status, body = self.get_snapshot()

        self.assertEqual(status, 200, body)
        task_list = body["task_list"]
        expected = self.runtime.orchestration_ledger.get_run(self.ctx.run_id)
        self.assertEqual(task_list["schema_version"], 1)
        self.assertEqual(task_list["source"], "orchestration_ledger")
        self.assertEqual(task_list["current"]["run_id"], self.ctx.run_id)
        self.assertEqual(task_list["current"]["task_id"], expected["task_id"])
        self.assertEqual(task_list["current"]["objective"], expected["objective"])
        self.assertNotEqual(task_list["current"]["objective"], "projection-only stale objective")
        self.assertIn(self.ctx.run_id, [item["run_id"] for item in task_list["history"]])

    def test_task_snapshot_preserves_bounded_structured_task_evidence_for_exact_run(self) -> None:
        self.runtime.task_state.update({
            "steps": [{"id": "step-1", "text": "Verify task bridge", "status": "completed", "updated_at": "2026-09-09T00:00:00Z"}],
        })
        self.runtime.task_state.record_build_report({
            "overall_status": "passed",
            "project": {"type": "electron", "name": "coding-tools-mcp", "version": "1.0.0"},
            "test_result": {
                "command": "node --test focused",
                "status": "passed",
                "exit_code": 0,
                "duration_ms": 42,
                "summary": "green",
                "finished_at": "2026-09-09T00:00:01Z",
            },
            "artifacts": [{"path": "dist/app.exe", "size": 123, "sha256": "a" * 64}],
        })
        self.runtime.task_state.record_tool_result(
            "apply_patch",
            {},
            {"ok": True, "affected_files": [{"path": "electron/main.js", "operation": "update"}]},
        )
        self.runtime.task_state.update({"failure": "bounded failure detail"})
        self.runtime.task_state.record_command_started(
            "node --test focused",
            "task-bridge-command",
            ".",
            owner_run_id=self.ctx.run_id,
            owner_wave_id=self.ctx.wave_id,
        )

        status, body = self.get_snapshot()

        self.assertEqual(status, 200, body)
        task = body["task"]
        self.assertEqual(task["task_id"], self.runtime.task_state.get()["task_id"])
        self.assertEqual(task["run_id"], self.ctx.run_id)
        self.assertEqual(task["wave_id"], self.ctx.wave_id)
        self.assertEqual(task["steps"][0]["text"], "Verify task bridge")
        self.assertEqual(task["test_results"][0]["status"], "passed")
        self.assertEqual(len(task["modified_files"]), 1)
        self.assertEqual(task["modified_files"][0]["path"], "electron/main.js")
        self.assertEqual(task["modified_files"][0]["operation"], "update")
        self.assertTrue(task["modified_files"][0]["updated_at"])
        self.assertEqual(task["current_command"]["workdir"], ".")
        self.assertEqual(task["failure"], "bounded failure detail")
        self.assertEqual(task["last_build_report"]["project"]["type"], "electron")
        self.assertEqual(task["last_build_report"]["artifacts"][0]["sha256"], "a" * 64)

    def test_live_snapshot_skips_heavy_analytics_but_preserves_control_state(self) -> None:
        def unexpected_heavy_call(*_args, **_kwargs):
            raise AssertionError("live control snapshot must not execute heavyweight analytics")

        ledger = self.runtime.orchestration_ledger
        source_key = os.path.normcase(os.path.abspath(str(self.runtime.workspace.root)))
        self.runtime._orchestration_workspace_identity_cache[source_key] = {
            "base_head": "hub-test-head",
            "worktree_fp": "hub-test-fp",
            "source_fingerprint": "hub-test-fp",
            "dirty_paths": [],
            "dirty_source_paths": [],
            "observed_at": "2026-08-30T00:00:00+00:00",
            "observation_source": "exact_workspace_identity",
        }
        ledger.append_event(
            self.ctx.run_id,
            wave_id=self.ctx.wave_id,
            event_type="usage_event",
            payload={
                "usage_id": "live-controller-usage",
                "turn_id": "turn-live",
                "trace_id": "trace-live",
                "actor": "controller",
                "provider_id": "openai",
                "model": "gpt-5.6-sol",
                "usage": {
                    "input_total_tokens": 100,
                    "input_cached_tokens": 30,
                    "output_total_tokens": 20,
                    "output_reasoning_tokens": 5,
                    "total_tokens": 120,
                },
                "measurement": {"usage": "measured", "cost": "unobserved"},
                "provenance": {"usage": "client_reported", "cost": "unobserved"},
                "cost": {"provider_cost": None},
            },
        )
        ledger.append_event(
            self.ctx.run_id,
            wave_id=self.ctx.wave_id,
            event_type="usage_event",
            payload={
                "usage_id": "live-provider-usage",
                "actor": "provider",
                "provider_id": "opencode-go",
                "model": "deepseek-v4-flash",
                "usage": {
                    "input_total_tokens": 80,
                    "input_cached_tokens": 20,
                    "output_total_tokens": 12,
                    "output_reasoning_tokens": 3,
                    "total_tokens": 92,
                },
                "measurement": {"usage": "measured", "cost": "measured"},
                "provenance": {"usage": "provider_reported", "cost": "provider_reported"},
                "cost": {"provider_cost": 0.003},
            },
        )
        observed_usage_limits = []
        original_list_usage_events = ledger.list_usage_events

        def bounded_usage_events(run_id, *, limit=100):
            observed_usage_limits.append(limit)
            return original_list_usage_events(run_id, limit=limit)

        original_usage = ledger.usage_analytics
        original_routing = ledger.routing_evidence
        original_flight = ledger.flight_recorder
        original_export = ledger.export_summary
        original_operations = mcp_http_handler_module.operations_analytics
        original_stale_reconcile = self.runtime._maybe_reconcile_stale_orchestration
        original_projection_reconcile = self.runtime._reconcile_task_orchestration_projection
        original_resource_reconcile = self.runtime.execution_resource_governor.reconcile
        original_verify = ledger.verify_chain
        original_list_waves = ledger.list_waves
        original_list_events = ledger.list_events
        original_list_proofs = ledger.list_proofs
        original_list_checkpoints = ledger.list_checkpoints
        original_controller = ledger.get_controller_lease
        original_current_active = ledger.current_active_run
        original_source_identity = self.runtime._orchestration_workspace_identity
        ledger.usage_analytics = unexpected_heavy_call
        ledger.routing_evidence = unexpected_heavy_call
        ledger.flight_recorder = unexpected_heavy_call
        ledger.export_summary = unexpected_heavy_call
        mcp_http_handler_module.operations_analytics = unexpected_heavy_call
        self.runtime._maybe_reconcile_stale_orchestration = unexpected_heavy_call
        self.runtime._reconcile_task_orchestration_projection = unexpected_heavy_call
        self.runtime.execution_resource_governor.reconcile = unexpected_heavy_call
        ledger.verify_chain = unexpected_heavy_call
        ledger.list_waves = unexpected_heavy_call
        ledger.list_events = unexpected_heavy_call
        ledger.list_proofs = unexpected_heavy_call
        ledger.list_checkpoints = unexpected_heavy_call
        ledger.get_controller_lease = unexpected_heavy_call
        ledger.current_active_run = unexpected_heavy_call
        ledger.list_usage_events = bounded_usage_events
        self.runtime._orchestration_workspace_identity = unexpected_heavy_call
        try:
            status, body = self.get_live_snapshot()
        finally:
            ledger.usage_analytics = original_usage
            ledger.routing_evidence = original_routing
            ledger.flight_recorder = original_flight
            ledger.export_summary = original_export
            mcp_http_handler_module.operations_analytics = original_operations
            self.runtime._maybe_reconcile_stale_orchestration = original_stale_reconcile
            self.runtime._reconcile_task_orchestration_projection = original_projection_reconcile
            self.runtime.execution_resource_governor.reconcile = original_resource_reconcile
            ledger.verify_chain = original_verify
            ledger.list_waves = original_list_waves
            ledger.list_events = original_list_events
            ledger.list_proofs = original_list_proofs
            ledger.list_checkpoints = original_list_checkpoints
            ledger.get_controller_lease = original_controller
            ledger.current_active_run = original_current_active
            ledger.list_usage_events = original_list_usage_events
            self.runtime._orchestration_workspace_identity = original_source_identity

        self.assertEqual(status, 200, body)
        self.assertEqual(body["snapshot_scope"], "live_control")
        self.assertEqual(body["integrity"]["code"], "UNVERIFIED_ON_LIVE_PATH")
        for key in ("task", "run", "waves", "events", "proofs", "delegations", "runtime_activity", "clients", "authority", "continuity", "provider_traffic", "runtime", "direct_usage", "tool_call_metering", "chatweb_measurement", "context_observability", "goal_pursuit", "problem_economics", "truth_snapshot"):
            self.assertIn(key, body)
        self.assertEqual(observed_usage_limits, [8])
        self.assertEqual(body["runtime"]["tools"], list(self.runtime.exposed_tool_names()))
        self.assertEqual(len(body["runtime"]["tools"]), 8)
        direct = body["direct_usage"]
        self.assertEqual(direct["source"], "bounded_recent_direct_usage_events")
        self.assertEqual(direct["missing_measurement_policy"], "unknown_not_zero")
        self.assertEqual(direct["controller"]["usage"]["input_total_tokens"], 100)
        self.assertEqual(direct["controller"]["usage"]["input_cached_tokens"], 30)
        self.assertEqual(direct["controller"]["usage"]["output_total_tokens"], 20)
        self.assertEqual(direct["controller"]["usage"]["output_reasoning_tokens"], 5)
        self.assertEqual(direct["controller"]["provenance"]["usage"], "client_reported")
        self.assertEqual(direct["controller"]["trace_id"], "trace-live")
        self.assertEqual(direct["provider"]["usage"]["input_total_tokens"], 80)
        self.assertEqual(direct["provider"]["cost"]["provider_cost"], 0.003)
        self.assertEqual(direct["provider"]["provenance"]["usage"], "provider_reported")
        tool_call_metering = body["tool_call_metering"]
        self.assertEqual(tool_call_metering["measurement"], "unobserved")
        self.assertEqual(tool_call_metering["source"], "chatweb_tool_call_card")
        self.assertEqual(tool_call_metering["provenance"], "client_receipt_required")
        self.assertEqual(tool_call_metering["missing_measurement_policy"], "unknown_not_zero")
        self.assertIsNone(tool_call_metering["total_tokens"])
        self.assertIsNone(tool_call_metering["latest"])
        self.assertEqual(tool_call_metering["reason"], "client_receipt_not_exposed_by_mcp_transport")
        chatweb_measurement = body["chatweb_measurement"]
        self.assertEqual(chatweb_measurement["accounting_claim"], "partial")
        self.assertFalse(chatweb_measurement["full_chatweb_accounting"])
        self.assertEqual(chatweb_measurement["missing_measurement_policy"], "unknown_not_zero")
        self.assertTrue(chatweb_measurement["controller_usage"]["ingress_supported"])
        self.assertEqual(chatweb_measurement["controller_usage"]["transport"], "mcp_tools_call_meta")
        self.assertEqual(chatweb_measurement["controller_usage"]["meta_key"], "io.coding-tools/controllerUsage")
        self.assertEqual(chatweb_measurement["controller_usage"]["observation"], "observed")
        self.assertEqual(chatweb_measurement["controller_usage"]["latest_usage_id"], "live-controller-usage")
        self.assertEqual(chatweb_measurement["controller_usage"]["turn_id"], "turn-live")
        self.assertEqual(chatweb_measurement["controller_usage"]["provenance"], "client_reported")
        host_envelope = chatweb_measurement["controller_usage"]["host_envelope"]
        self.assertEqual(host_envelope["observation"], "unobserved")
        self.assertEqual(host_envelope["classification"], "unobserved")
        self.assertEqual(host_envelope["lifecycle"], "unobserved")
        self.assertFalse(chatweb_measurement["controller_usage"]["post_turn_sideband"]["supported"])
        self.assertEqual(
            chatweb_measurement["controller_usage"]["post_turn_sideband"]["reason"],
            "no_supported_post_turn_controller_usage_transport",
        )
        self.assertEqual(chatweb_measurement["tool_call_tokens"]["observation"], "unavailable")
        self.assertEqual(
            chatweb_measurement["tool_call_tokens"]["reason"],
            "client_receipt_not_exposed_by_mcp_transport",
        )
        self.assertEqual(chatweb_measurement["tool_inventory"]["tool_count"], 8)
        self.assertEqual(chatweb_measurement["tool_inventory"]["contract_tool_count"], 8)
        self.assertIn("session_measurement_coverage_not_proven", chatweb_measurement["blocking_reasons"])
        self.assertIn("controller_usage_envelope_not_observed", chatweb_measurement["blocking_reasons"])
        self.assertIn("client_receipt_not_exposed_by_mcp_transport", chatweb_measurement["blocking_reasons"])
        observability = body["context_observability"]
        capabilities = observability["capability_matrix"]
        self.assertEqual(capabilities["exact_controller_usage"]["status"], "supported")
        self.assertEqual(capabilities["exact_controller_usage"]["observation"], "observed")
        self.assertEqual(capabilities["exact_session_identity"]["status"], "partial")
        self.assertEqual(
            capabilities["exact_session_identity"]["product_session_id"]["status"],
            "unobserved",
        )
        self.assertEqual(
            capabilities["exact_session_identity"]["turn_trace_identity"]["trace_id"],
            "trace-live",
        )
        self.assertEqual(capabilities["exact_context_pressure"]["status"], "unobserved")
        self.assertIsNone(capabilities["exact_context_pressure"]["value"])
        self.assertEqual(capabilities["controller_knowledge_revision"]["status"], "supported")
        self.assertEqual(capabilities["controller_knowledge_revision"]["observation"], "unobserved")
        self.assertIsNone(capabilities["controller_knowledge_revision"]["knowledge_revision"])
        self.assertEqual(capabilities["heuristic_rotation_signals"]["status"], "available")
        self.assertEqual(capabilities["heuristic_rotation_signals"]["source"], "heuristic")
        self.assertTrue(capabilities["heuristic_rotation_signals"]["not_rotation_authority"])
        self.assertEqual(observability["rotation_policy"]["automatic_handoff"], "off")
        goal = body["goal_pursuit"]
        self.assertEqual(goal["status"], "unavailable")
        self.assertEqual(goal["missing_reason"], "goal_prl_schema_inactive")
        self.assertIsNone(goal["identity"])
        self.assertIsNone(goal["completion"]["criteria_total"])
        self.assertIsNone(goal["completion"]["criteria_proven"])
        self.assertFalse(goal["authority"]["acceptance_authority_granted"])
        economics = body["problem_economics"]
        self.assertEqual(economics["status"], "unavailable")
        self.assertTrue(economics["heartbeat_analytics_forbidden"])
        self.assertIsNone(economics["observed_values"])
        truth = body["truth_snapshot"]
        self.assertEqual(truth["source"]["git_head"], "hub-test-head")
        self.assertEqual(truth["source"]["worktree_fp"], "hub-test-fp")
        self.assertEqual(truth["source"]["observation_source"], "exact_workspace_identity")
        self.assertEqual(truth["orchestration"]["run_id"], self.ctx.run_id)
        self.assertEqual(truth["orchestration"]["wave_id"], self.ctx.wave_id)
        self.assertIn("automatic_routing", body["provider_traffic"])
        for key in ("usage_events", "usage_analytics", "operations_analytics", "routing_evidence", "flight_recorder", "history", "lanes", "resume_packet"):
            self.assertNotIn(key, body)

        full_status, full = self.get_snapshot()
        self.assertEqual(full_status, 200, full)
        self.assertIn("usage_analytics", full)
        self.assertIn("operations_analytics", full)
        self.assertIn("routing_evidence", full)

    def test_live_snapshot_transports_latest_turn_evidence_and_fails_closed(self) -> None:
        base = {
            "schema_version": 1,
            "measurement": "chat_turn_measurements_v1",
            "missing_measurement_policy": "unknown_not_zero",
            "content_free": True,
        }
        reader_target = "coding_tools_mcp.live_control._latest_chat_turn_measurement"
        cases = {
            "measured_zero": {
                **base,
                "journal_available": True,
                "latest_turn": {"kind": "exact", "point": 0, "lower": 0, "upper": 0},
                "missing_reason": None,
            },
            "unknown": {
                **base,
                "journal_available": True,
                "latest_turn": None,
                "missing_reason": "latest_turn_unmeasured",
            },
        }
        for label, expected in cases.items():
            with self.subTest(case=label):
                with patch(reader_target, return_value=expected) as reader:
                    status, body = self.get_live_snapshot()
                self.assertEqual(status, 200, body)
                self.assertEqual(body["snapshot_scope"], "live_control")
                self.assertEqual(body["latest_turn_measurement"], expected)
                reader.assert_called_once_with(self.runtime.orchestration_ledger.workspace)

        with self.subTest(case="reader_exception"):
            with patch(reader_target, side_effect=OSError("test journal unavailable")) as reader:
                status, body = self.get_live_snapshot()
            self.assertEqual(status, 200, body)
            self.assertEqual(body["latest_turn_measurement"], {
                **base,
                "journal_available": False,
                "latest_turn": None,
                "missing_reason": "chat_journal_unavailable",
            })
            reader.assert_called_once_with(self.runtime.orchestration_ledger.workspace)

        with self.subTest(case="admission_closed"):
            with patch.object(
                self.runtime,
                "activation_admission_snapshot",
                return_value={"admission_open": False, "state": "UPDATE_INCOMPLETE"},
            ), patch(
                reader_target,
                side_effect=AssertionError("closed admission must not read the chat journal"),
            ) as reader:
                status, body = self.get_live_snapshot()
            self.assertEqual(status, 200, body)
            self.assertEqual(body["snapshot_scope"], "live_control")
            self.assertEqual(body["state"], "UPDATE_INCOMPLETE")
            self.assertFalse(body["activation"]["admission_open"])
            self.assertNotIn("latest_turn_measurement", body)
            reader.assert_not_called()

    def test_live_snapshot_does_not_recover_a_cold_orchestration_context(self) -> None:
        # Simulate a process restart: the durable run remains, but the
        # in-memory context cache is empty.  The live read must stay bounded and
        # write-free instead of replaying waves/events or expiring a fence.
        self.runtime.orchestration_control._contexts.pop(self.ctx.run_id, None)
        ledger = self.runtime.orchestration_ledger
        with patch.object(ledger, "list_waves", side_effect=AssertionError("live path must not scan waves")), patch.object(
            ledger, "list_events", side_effect=AssertionError("live path must not scan events")
        ), patch.object(ledger, "assert_write_fence", side_effect=AssertionError("live path must not maintain leases")):
            status, body = self.get_live_snapshot()
        self.assertEqual(status, 200, body)
        self.assertEqual(body["snapshot_scope"], "live_control")
        self.assertEqual(body["authority"]["write"]["status"], "released")

    def test_live_snapshot_does_not_adopt_an_unbound_active_ledger_run(self) -> None:
        # The canonical ledger deliberately keeps the active row created by
        # setUp, but an empty task-state projection means the current UI has no
        # execution binding.  Observation of that row must not become authority
        # for the high-frequency live path.
        self.runtime.task_state.update({"orchestration": {}}, event="hub_test_projection_unbound")
        ledger = self.runtime.orchestration_ledger
        with patch.object(
            ledger,
            "peek_current_active_run",
            side_effect=AssertionError("live path must not adopt an unbound ledger run"),
        ), patch.object(
            ledger,
            "get_run",
            side_effect=AssertionError("live path must not read an unbound ledger run"),
        ), patch.object(
            ledger,
            "live_run_projection",
            side_effect=AssertionError("live path must not project an unbound ledger run"),
        ):
            status, body = self.get_live_snapshot()

        self.assertEqual(status, 200, body)
        self.assertEqual(body["snapshot_scope"], "live_control")
        self.assertEqual(body["run_id"], "")
        self.assertIsNone(body["run"])
        self.assertEqual(body["waves"], [])
        self.assertEqual(body["events"], [])
        self.assertEqual(body["proofs"], [])
        self.assertEqual(body["delegations"], [])
        self.assertEqual(body["counts"], {"events": 0, "waves": 0, "checkpoints": 0})
        self.assertEqual(body["continuity"]["reason_codes"], ["NO_ACTIVE_EXECUTION"])
        self.assertEqual(body["goal_pursuit"]["status"], "unavailable")
        self.assertEqual(body["goal_pursuit"]["missing_reason"], "run_id_missing")

    def test_live_snapshot_composes_observed_goal_without_polling_economics(self) -> None:
        summary = {
            "identity": {
                "problem_id": "problem-live",
                "problem_revision": 3,
                "contract_fingerprint": "contract-fp",
                "criteria_fingerprint": "criteria-fp",
            },
            "problem_state": "OPEN",
            "resolution_status": "IN_PROGRESS",
            "completion": {
                "status": "observed",
                "criteria_total": 5,
                "criteria_proven": 2,
                "criteria_unresolved": 3,
                "exact_coverage_status": "PARTIAL",
                "missing_reason": None,
            },
            "next_critical_gap": "Capture cross-session proof",
            "next_critical_gap_id": "criterion-3",
            "next_action": "SATISFY_UNRESOLVED_CRITERION",
            "decision_state_provenance": "CANONICAL_PRL_EOCL_PROOF_JOIN_BOUNDED",
            "stop": {"legitimate_stop": False, "reason": "NONE"},
            "fact_window": {"truncated": False},
            "authority": {
                "mutation_authority_granted": False,
                "acceptance_authority_granted": False,
                "problem_revision_authority_granted": False,
            },
        }
        ledger = self.runtime.orchestration_ledger
        with patch.object(ledger, "goal_pursuit_live_summary", return_value=summary) as projector:
            status, body = self.get_live_snapshot()
        self.assertEqual(status, 200, body)
        projector.assert_called_once_with(run_id=self.ctx.run_id)
        goal = body["goal_pursuit"]
        self.assertEqual(goal["status"], "observed")
        self.assertEqual(goal["identity"]["problem_id"], "problem-live")
        self.assertEqual(goal["identity"]["problem_revision"], 3)
        self.assertEqual(goal["completion"]["criteria_proven"], 2)
        self.assertEqual(goal["completion"]["criteria_total"], 5)
        self.assertEqual(goal["current_run_wave"]["run_id"], self.ctx.run_id)
        self.assertEqual(goal["current_run_wave"]["wave_id"], self.ctx.wave_id)
        self.assertFalse(goal["authority"]["mutation_authority_granted"])
        self.assertFalse(goal["authority"]["acceptance_authority_granted"])
        economics = body["problem_economics"]
        self.assertEqual(economics["status"], "analytics_available_off_fast_path")
        self.assertEqual(economics["source"], "offline_immutable_snapshot_report")
        self.assertTrue(economics["heartbeat_analytics_forbidden"])
        self.assertIsNone(economics["observed_values"])

    def test_live_snapshot_reads_the_exact_current_problem_binding(self) -> None:
        ledger = self.runtime.orchestration_ledger
        ledger.migrate_problem_lineage_schema()
        opened = ledger.problem_record_event(
            {
                "operation": "open",
                "event_id": "hub-live-goal-open",
                "task_id": "hub-live-goal-task",
                "task_class": "feature",
                "engineering_floor": "REQUIRED",
                "contract_capsule": {
                    "objective_summary": "Expose bounded Goal truth",
                    "acceptance_criteria": [
                        {"criterion_id": "goal-ui", "summary": "Goal identity is visible"},
                        {"criterion_id": "continuity-ui", "summary": "Continuity remains truthful"},
                    ],
                    "protected_invariants": ["Preserve the eight-tool contract"],
                    "constraints": ["No inferred authority"],
                    "unresolved_conditions": [],
                },
                "provenance": "CONTROLLER_REPORTED_EXPLICIT_USER",
                "evidence_level": "OBSERVED",
            },
            now="2026-09-01T00:00:00+00:00",
            authority_context="RUNTIME_EXPLICIT_USER",
        )
        problem_id = str(opened["event"]["problem_id"])
        ledger.problem_record_event(
            {
                "operation": "link",
                "event_id": "hub-live-goal-bind",
                "problem_id": problem_id,
                "problem_revision": 1,
                "run_id": self.ctx.run_id,
                "wave_id": self.ctx.wave_id,
                "relation_type": "ENGINEERING_ATTEMPT_BOUND",
                "provenance": "DETERMINISTIC_EVIDENCE",
                "evidence_level": "OBSERVED",
            },
            now="2026-09-01T00:00:00+00:00",
            authority_context="RUNTIME_BINDING",
        )
        status, body = self.get_live_snapshot()
        self.assertEqual(status, 200, body)
        goal = body["goal_pursuit"]
        self.assertEqual(goal["status"], "observed")
        self.assertEqual(goal["identity"]["problem_id"], problem_id)
        self.assertEqual(goal["identity"]["problem_revision"], 1)
        self.assertEqual(goal["resolution_status"], "IN_PROGRESS")
        self.assertEqual(goal["completion"]["criteria_total"], 2)
        self.assertEqual(goal["completion"]["criteria_proven"], 0)
        self.assertEqual(goal["next_critical_gap_id"], "goal-ui")
        self.assertEqual(goal["knowledge"]["status"], "unavailable")
        self.assertTrue(goal["knowledge"]["controller_recovery_required"])
        self.assertEqual(
            body["problem_economics"]["status"], "analytics_available_off_fast_path"
        )

    def test_dashboard_analytics_isolated_from_live_control_polling(self) -> None:
        ledger = self.runtime.orchestration_ledger
        original_usage = ledger.usage_analytics
        original_operations = mcp_http_handler_module.operations_analytics
        observed = {}

        def usage(*, days=7, now=None):
            observed["usage"] = (days, now)
            return original_usage(days=days, now=now)

        def operations(*args, days=7, now=None, **kwargs):
            observed["operations"] = (days, now)
            return original_operations(*args, days=days, now=now, **kwargs)

        ledger.usage_analytics = usage
        mcp_http_handler_module.operations_analytics = operations
        try:
            status, body = self.get_dashboard_analytics()
        finally:
            ledger.usage_analytics = original_usage
            mcp_http_handler_module.operations_analytics = original_operations
        self.assertEqual(status, 200, body)
        self.assertEqual(body["schema_version"], 1)
        self.assertEqual(body["snapshot_scope"], "dashboard_analytics")
        self.assertTrue(body["content_free"])
        self.assertEqual(body["window_days"], 7)
        self.assertTrue(str(body["generated_at"]).endswith("Z"), body)
        self.assertEqual(observed["usage"], observed["operations"])
        self.assertEqual(observed["usage"][0], 7)
        self.assertEqual(observed["usage"][1], body["generated_at"])
        self.assertIn("usage_analytics", body)
        self.assertIn("operations_analytics", body)
        self.assertNotIn("task", body)
        self.assertNotIn("events", body)

    def structured(self, body):
        self.assertNotIn("error", body, body)
        return body["result"]["structuredContent"]

    def test_registers_clients_without_stealing_live_controller(self) -> None:
        status, body = self.post_stateless(action="get", client_id="chatweb", client_type="chatweb")
        self.assertEqual(status, 200, body)
        self.structured(body)
        self.claim_chatweb_controller()
        controller = self.runtime.orchestration_ledger.get_controller_lease(self.ctx.run_id)
        self.assertIsNotNone(controller)
        chatweb_id = controller["owner_client_id"]
        self.assertTrue(chatweb_id.startswith("chatweb:"), chatweb_id)
        initial_fencing_token = int(controller["fencing_token"])

        status, body = self.post_stateless(action="get", client_id="codex-desktop", client_type="codex_desktop")
        self.assertEqual(status, 200, body)
        self.structured(body)
        controller_after = self.runtime.orchestration_ledger.get_controller_lease(self.ctx.run_id)
        self.assertEqual(controller_after["owner_client_id"], chatweb_id)
        self.assertEqual(controller_after["fencing_token"], initial_fencing_token)

        status, body = self.post_stateless(action="get", client_id="opencode", client_type="opencode")
        self.assertEqual(status, 200, body)
        self.structured(body)
        controller_after_opencode = self.runtime.orchestration_ledger.get_controller_lease(self.ctx.run_id)
        self.assertEqual(controller_after_opencode["owner_client_id"], chatweb_id)
        self.assertEqual(controller_after_opencode["fencing_token"], initial_fencing_token)
        clients = {item["client_id"]: item for item in self.runtime.orchestration_ledger.list_hub_clients()}
        self.assertTrue(clients[chatweb_id]["online"])
        self.assertTrue(clients["codex-desktop"]["online"])
        self.assertTrue(clients["opencode"]["online"])
        self.assertEqual(clients["codex-desktop"]["role"], "worker")
        self.assertEqual(clients["opencode"]["role"], "worker")

    def test_event_cursors_advance_only_over_observed_events(self) -> None:
        self.post_stateless(action="get", client_id="chatweb", client_type="chatweb")
        self.runtime.orchestration_ledger.append_event(self.ctx.run_id, event_type="hub_probe", payload={"n": 1})
        status, body = self.post_stateless(
            action="events",
            client_id="chatweb",
            client_type="chatweb",
            after_seq=0,
            run_id=self.ctx.run_id,
        )
        self.assertEqual(status, 200, body)
        structured = self.structured(body)
        observed_seq = structured["events"][-1]["seq"]
        chatweb_id = structured["client_cursor"]["client_id"]
        self.assertTrue(chatweb_id.startswith("chatweb:"), chatweb_id)
        self.assertEqual(structured["client_cursor"]["last_event_seq"], observed_seq)

        self.post_stateless(
            action="events",
            client_id="chatweb",
            client_type="chatweb",
            after_seq=999999,
            run_id=self.ctx.run_id,
        )
        cursor = self.runtime.orchestration_ledger.get_hub_client_cursor(client_id=chatweb_id, run_id=self.ctx.run_id)
        self.assertEqual(cursor["last_event_seq"], observed_seq)

        desktop_status, desktop_body = self.post_stateless(
            action="events",
            client_id="codex-desktop",
            client_type="codex_desktop",
            after_seq=0,
            run_id=self.ctx.run_id,
        )
        self.assertEqual(desktop_status, 200, desktop_body)
        desktop_structured = self.structured(desktop_body)
        desktop_id = desktop_structured["client_cursor"]["client_id"]
        self.assertEqual(desktop_id, "codex-desktop")
        desktop = self.runtime.orchestration_ledger.get_hub_client_cursor(client_id=desktop_id, run_id=self.ctx.run_id)
        self.assertEqual(desktop["last_event_seq"], observed_seq)

    def test_opencode_provider_telemetry_is_exact_idempotent_and_fail_closed(self) -> None:
        telemetry = {
            "schema_version": 1, "event_type": "message.updated", "session_id": "ses-telemetry", "message_id": "msg-telemetry",
            "provider_id": "opencode-go", "model_id": "deepseek-v4-flash", "status": "active", "started_at_ms": 1000,
            "provider_cost": 0.0, "input_tokens": 0, "output_tokens": 0, "reasoning_output_tokens": 0, "cache_read_tokens": 0, "cache_write_tokens": 0,
        }
        payload = {"action": "provider_telemetry", "client_id": "opencode", "client_type": "opencode", "telemetry": telemetry}
        status, rejected = self.post_hub(payload)
        self.assertEqual(status, 409, rejected)
        self.assertEqual(rejected["code"], "PROVIDER_TELEMETRY_CONTEXT_UNAVAILABLE")
        control = self.runtime.orchestration_control
        control.mark_ready(self.ctx)
        control.select_route(self.ctx, {"requested": "opencode", "selected": "opencode", "reason": "test"})
        control.transition(self.ctx, "EXECUTING", reason="provider_inference")
        status, started = self.post_hub(payload)
        self.assertEqual(status, 200, started)
        self.assertTrue(started["created"])
        delegation_id = started["delegation_id"]
        self.assertEqual(started["delegation"]["model"], "opencode-go/deepseek-v4-flash")
        event_count = len(self.runtime.orchestration_ledger.list_events(self.ctx.run_id))
        status, duplicate = self.post_hub(payload)
        self.assertEqual(status, 200, duplicate)
        self.assertFalse(duplicate["changed"])
        self.assertEqual(len(self.runtime.orchestration_ledger.list_events(self.ctx.run_id)), event_count)
        completed = {**telemetry, "status": "completed", "completed_at_ms": 1600, "duration_ms": 600, "finish": "stop", "provider_cost": 0.004, "input_tokens": 100, "output_tokens": 20, "reasoning_output_tokens": 4, "cache_read_tokens": 40, "cache_write_tokens": 2}
        status, finished = self.post_hub({**payload, "telemetry": completed})
        self.assertEqual(status, 200, finished)
        self.assertEqual(finished["delegation_id"], delegation_id)
        self.assertEqual(finished["delegation"]["status"], "completed")
        economics = finished["delegation"]["metadata"]["economics"]
        self.assertEqual((economics["input_tokens"], economics["cached_input_tokens"], economics["output_tokens"], economics["reasoning_output_tokens"]), (100, 40, 20, 4))
        self.assertEqual((economics["cache_read_tokens"], economics["cache_write_tokens"], economics["provider_cost"]), (40, 2, 0.004))
        usage = finished["usage_event"]
        self.assertEqual(usage["measurement"]["usage"], "measured")
        self.assertEqual(usage["measurement"]["cost"], "measured")
        self.assertEqual(usage["measurement"]["queue_timing"], "unobserved")
        self.assertEqual(usage["measurement"]["provider_timing"], "measured")
        self.assertIsNone(usage["timing"]["queue_ms"])
        self.assertEqual(usage["timing"]["provider_ms"], 600)
        self.assertIsNone(usage["timing"]["total_ms"])
        self.assertEqual(usage["usage"]["uncached_input_tokens"], 60)
        stale = {**telemetry, "input_tokens": 10, "output_tokens": 2}
        status, stale_result = self.post_hub({**payload, "telemetry": stale})
        self.assertEqual(status, 200, stale_result)
        self.assertFalse(stale_result["changed"])
        self.assertEqual(stale_result["delegation"]["status"], "completed")
        self.assertEqual(stale_result["delegation"]["metadata"]["economics"]["input_tokens"], 100)
        event_types = [item["event_type"] for item in self.runtime.orchestration_ledger.list_events(self.ctx.run_id)]
        self.assertIn("external_delegation_started", event_types)
        self.assertIn("external_delegation_finished", event_types)
        snapshot_status, snapshot = self.get_snapshot()
        self.assertEqual(snapshot_status, 200)
        projected = next(item for item in snapshot["delegations"] if item["delegation_id"] == delegation_id)
        self.assertEqual(projected["metadata"]["economics"]["input_tokens"], 100)
        self.assertEqual(len(snapshot["usage_events"]), 1)
        self.assertEqual(snapshot["usage_events"][0]["usage_id"], usage["usage_id"])

    def test_uncorrelated_opencode_telemetry_cannot_contaminate_deterministic_wave(self) -> None:
        control = self.runtime.orchestration_control
        control.mark_ready(self.ctx)
        control.select_route(self.ctx, {"requested": "deterministic", "selected": "deterministic", "reason": "measurement_hold"})
        control.transition(self.ctx, "EXECUTING", reason="deterministic_work")
        telemetry = {
            "schema_version": 1, "event_type": "message.updated", "session_id": "ses-unrelated", "message_id": "msg-unrelated",
            "provider_id": "opencode-go", "model_id": "deepseek-v4-pro", "status": "completed", "started_at_ms": 1000,
            "completed_at_ms": 1600, "duration_ms": 600, "provider_cost": 0.25, "input_tokens": 100,
            "output_tokens": 20, "reasoning_output_tokens": 4, "cache_read_tokens": 40, "cache_write_tokens": 0,
        }
        status, rejected = self.post_hub({"action": "provider_telemetry", "client_id": "opencode", "client_type": "opencode", "telemetry": telemetry})
        self.assertEqual(status, 409, rejected)
        self.assertEqual(rejected["code"], "PROVIDER_TELEMETRY_ATTRIBUTION_UNAVAILABLE")
        self.assertEqual(self.runtime.orchestration_ledger.list_delegations(self.ctx.wave_id), [])
        self.assertEqual(self.runtime.orchestration_ledger.list_usage_events(self.ctx.run_id), [])

    def test_provider_dispatch_is_supervisor_only_and_telemetry_correlates_to_adapter_delegation(self) -> None:
        class FakeProvider:
            def __init__(self):
                self.snapshot = None

            def start(self, *, run_id, wave_id, model, prompt, timeout_ms, request_id):
                self.snapshot = {
                    "dispatch_id": "dispatch-1", "request_id": request_id, "run_id": run_id, "wave_id": wave_id,
                    "delegation_id": "delegation-provider-1", "provider_id": "opencode-go", "model": model,
                    "status": "running", "session_id": "ses-adapter", "prompt_sha256": "abc", "prompt_bytes": len(prompt.encode()),
                    "result_text": "", "result_chars": 0, "output_truncated": False, "stdout_bytes": 0, "stderr_bytes": 0,
                    "returncode": None, "error_class": None, "read_only_enforced": True, "allowed_tools": ["read"],
                    "timing": {"queue_ms": 1, "provider_ms": None, "total_ms": None}, "deduplicated": False,
                }
                return dict(self.snapshot)

            def observe(self, dispatch_id):
                if dispatch_id != "dispatch-1":
                    raise AssertionError(dispatch_id)
                return dict(self.snapshot)

            def cancel(self, dispatch_id):
                self.snapshot = {**self.snapshot, "status": "cancelled", "error_class": "cancelled_or_interrupted", "timing": {"queue_ms": 1, "provider_ms": None, "total_ms": 5}}
                return dict(self.snapshot)

            def find_by_session(self, **kwargs):
                return dict(self.snapshot) if kwargs.get("session_id") == "ses-adapter" else None

            def active_count(self):
                return 1 if self.snapshot and self.snapshot["status"] == "running" else 0

            def close(self):
                return None

        self.runtime._opencode_provider.close()
        self.runtime._opencode_provider = FakeProvider()
        self.runtime.provider_traffic = ProviderTrafficGovernor({"opencode-go/deepseek-v4-flash": {"concurrency": 1}})
        denied_status, denied = self.post_hub({"action": "provider_dispatch", "client_id": "opencode", "client_type": "opencode", "model": "opencode-go/deepseek-v4-flash", "prompt": "inspect"})
        self.assertEqual(denied_status, 409, denied)
        self.assertEqual(denied["code"], "PROVIDER_DISPATCH_CLIENT_DENIED")

        control = self.runtime.orchestration_control
        control.mark_ready(self.ctx)
        control.select_route(self.ctx, {"requested": "opencode", "selected": "opencode", "reason": "test"})
        control.transition(self.ctx, "EXECUTING", reason="provider_inference")
        missing_status, missing = self.post_hub({"action": "provider_dispatch", "client_id": "electron-panel", "client_type": "electron", "model": "opencode-go/deepseek-v4-flash", "prompt": "inspect", "request_id": "missing-budget"})
        self.assertEqual(missing_status, 409, missing)
        self.assertEqual(missing["code"], "PROVIDER_USAGE_RESERVATION_REQUIRED")
        status, started = self.post_hub({"action": "provider_dispatch", "client_id": "electron-panel", "client_type": "electron", "model": "opencode-go/deepseek-v4-flash", "prompt": "inspect", "request_id": "req", "token_budget": 256})
        self.assertEqual(status, 200, started)
        self.assertEqual(started["dispatch"]["status"], "running")
        self.assertTrue(started["delegation"]["metadata"]["read_only_enforced"])
        self.assertNotIn("inspect", repr(started["delegation"]))
        self.assertEqual(started["admission"]["reason"], "admitted")
        reservation_event = next(item for item in self.runtime.orchestration_ledger.list_events(self.ctx.run_id) if item["event_type"] == "usage_reservation_reserved")
        reservation_id = reservation_event["payload"]["reservation_id"]
        reservations = UsageReservationStore(self.runtime.orchestration_ledger)
        reserved = reservations.get(self.ctx.run_id, reservation_id)
        self.assertEqual(reserved["status"], "reserved")
        self.assertEqual(reserved["reservation"], {"unit": "tokens", "units": 256, "measurement": "estimated"})
        blocked_status, blocked = self.post_hub({"action": "provider_dispatch", "client_id": "electron-panel", "client_type": "electron", "model": "opencode-go/deepseek-v4-flash", "prompt": "inspect another", "request_id": "req-2", "token_budget": 128})
        self.assertEqual(blocked_status, 409, blocked)
        self.assertEqual(blocked["code"], "PROVIDER_ADMISSION_DENIED")
        self.assertEqual(blocked["details"]["reason"], "concurrency_exhausted")

        terminal_snapshot = {**started["dispatch"], "status": "completed", "returncode": 0, "timing": {"queue_ms": 1, "provider_ms": 5, "total_ms": 6}}
        self.runtime._opencode_provider.snapshot = terminal_snapshot
        self.runtime._sync_opencode_dispatch(terminal_snapshot, self.ctx)
        indeterminate = reservations.get(self.ctx.run_id, reservation_id)
        self.assertEqual(indeterminate["status"], "indeterminate")
        self.assertEqual(indeterminate["actual"], {"unit": "tokens", "units": None, "measurement": "unobserved"})
        self.assertEqual(self.runtime.orchestration_ledger.list_usage_events(self.ctx.run_id), [])

        telemetry = {
            "schema_version": 1, "event_type": "message.updated", "session_id": "ses-adapter", "message_id": "msg-adapter",
            "provider_dispatch_id": "dispatch-1", "provider_delegation_id": "delegation-provider-1",
            "provider_id": "opencode-go", "model_id": "deepseek-v4-flash", "status": "completed", "started_at_ms": 1000,
            "completed_at_ms": 1600, "duration_ms": 600, "provider_cost": 0.003, "input_tokens": 80, "output_tokens": 12,
            "reasoning_output_tokens": 3, "cache_read_tokens": 20, "cache_write_tokens": 1,
        }
        telemetry_status, measured = self.post_hub({"action": "provider_telemetry", "client_id": "opencode", "client_type": "opencode", "telemetry": telemetry})
        self.assertEqual(telemetry_status, 200, measured)
        self.assertEqual(measured["delegation_id"], "delegation-provider-1")
        self.assertEqual(measured["delegation"]["metadata"]["economics"]["input_tokens"], 80)
        self.assertEqual(len(self.runtime.orchestration_ledger.list_usage_events(self.ctx.run_id)), 1)
        reconciled = reservations.get(self.ctx.run_id, reservation_id)
        self.assertEqual(reconciled["status"], "reconciled")
        self.assertEqual(reconciled["reservation"]["units"], 256)
        self.assertEqual(reconciled["actual"], {"unit": "tokens", "units": 92, "measurement": "measured"})
        duplicate_status, duplicate = self.post_hub({"action": "provider_telemetry", "client_id": "opencode", "client_type": "opencode", "telemetry": telemetry})
        self.assertEqual(duplicate_status, 200, duplicate)
        self.assertEqual(len(self.runtime.orchestration_ledger.list_usage_events(self.ctx.run_id)), 1)
        reservation_events = [item for item in self.runtime.orchestration_ledger.list_events(self.ctx.run_id) if item["event_type"] == "usage_reservation_reconciled"]
        self.assertEqual(len(reservation_events), 1)

        observe_status, observed = self.post_hub({"action": "provider_observe", "client_id": "electron-panel", "client_type": "electron", "dispatch_id": "dispatch-1"})
        self.assertEqual(observe_status, 200, observed)
        usage_before_cancel = self.runtime.orchestration_ledger.list_usage_events(self.ctx.run_id)
        self.assertEqual(len(usage_before_cancel), 1)
        cancel_status, cancelled = self.post_hub({"action": "provider_cancel", "client_id": "electron-panel", "client_type": "electron", "dispatch_id": "dispatch-1"})
        self.assertEqual(cancel_status, 400, cancelled)
        self.assertEqual(cancelled["code"], "INVALID_HUB_REQUEST")
        self.assertIn("usage_id already exists with different evidence", cancelled["error"])
        usage_after_cancel = self.runtime.orchestration_ledger.list_usage_events(self.ctx.run_id)
        self.assertEqual(usage_after_cancel, usage_before_cancel)
        delegation_after_cancel = next(
            item for item in self.runtime.orchestration_ledger.list_delegations(self.ctx.wave_id)
            if item["delegation_id"] == "delegation-provider-1"
        )
        self.assertEqual(delegation_after_cancel["status"], "completed")

    def test_correlated_tool_call_message_is_intermediate_and_final_usage_aggregates_messages(self) -> None:
        control = self.runtime.orchestration_control
        control.mark_ready(self.ctx)
        control.select_route(self.ctx, {"requested": "opencode", "selected": "opencode", "reason": "test"})
        control.transition(self.ctx, "EXECUTING", reason="provider_inference")
        run_id, wave_id = self.ctx.run_id, self.ctx.wave_id

        class FakeProvider:
            def __init__(self):
                self.snapshot = {
                    "dispatch_id": "dispatch-multi", "request_id": "req", "run_id": run_id, "wave_id": wave_id,
                    "delegation_id": "delegation-multi", "provider_id": "opencode-go", "model": "opencode-go/deepseek-v4-flash",
                    "status": "running", "session_id": "ses-multi", "prompt_sha256": "abc", "prompt_bytes": 7,
                    "result_text": "", "result_chars": 0, "output_truncated": False, "stdout_bytes": 0, "stderr_bytes": 0,
                    "returncode": None, "error_class": None, "read_only_enforced": True, "allowed_tools": ["read"],
                    "lifecycle_evidence": {"event_counts": {}, "last_step_finish": "", "last_tool": "", "last_tool_status": ""},
                    "timing": {"queue_ms": 1, "provider_ms": None, "total_ms": None},
                }

            def observe(self, dispatch_id):
                if dispatch_id != "dispatch-multi":
                    raise AssertionError(dispatch_id)
                return dict(self.snapshot)

            def find_by_session(self, **kwargs):
                return dict(self.snapshot) if kwargs.get("session_id") == "ses-multi" else None

            def active_count(self):
                return 1

            def close(self):
                return None

        self.runtime._opencode_provider.close()
        self.runtime._opencode_provider = FakeProvider()
        reservations = UsageReservationStore(self.runtime.orchestration_ledger)
        reservation_id = self.runtime._provider_traffic_key(
            run_id=run_id,
            wave_id=wave_id,
            model="opencode-go/deepseek-v4-flash",
            request_id="req",
            prompt_sha256="abc",
        )
        reservations.reserve(
            run_id=run_id,
            wave_id=wave_id,
            reservation_id=reservation_id,
            request_id="req",
            provider_model="opencode-go/deepseek-v4-flash",
            reserved_units=512,
            expires_at_unix_ms=None,
        )
        common = {
            "schema_version": 1, "event_type": "message.updated", "session_id": "ses-multi",
            "provider_dispatch_id": "dispatch-multi", "provider_delegation_id": "delegation-multi",
            "provider_id": "opencode-go", "model_id": "deepseek-v4-flash", "started_at_ms": 1000,
            "reasoning_output_tokens": 0, "cache_read_tokens": 0, "cache_write_tokens": 0,
        }
        first = {**common, "message_id": "msg-1", "status": "completed", "completed_at_ms": 1600, "duration_ms": 600, "finish": "tool-calls", "provider_cost": 0.001, "input_tokens": 100, "output_tokens": 10}
        status, intermediate = self.post_hub({"action": "provider_telemetry", "client_id": "opencode", "client_type": "opencode", "telemetry": first})
        self.assertEqual(status, 200, intermediate)
        self.assertEqual(intermediate["delegation"]["status"], "active")
        self.assertIsNone(intermediate["usage_event"])
        self.assertEqual(self.runtime.orchestration_ledger.list_usage_events(self.ctx.run_id), [])
        status, duplicate = self.post_hub({"action": "provider_telemetry", "client_id": "opencode", "client_type": "opencode", "telemetry": first})
        self.assertEqual(status, 200, duplicate)
        self.assertFalse(duplicate["changed"])
        second = {**common, "message_id": "msg-2", "status": "completed", "started_at_ms": 1700, "completed_at_ms": 2000, "duration_ms": 300, "finish": "stop", "provider_cost": 0.002, "input_tokens": 50, "output_tokens": 5}
        status, final = self.post_hub({"action": "provider_telemetry", "client_id": "opencode", "client_type": "opencode", "telemetry": second})
        self.assertEqual(status, 200, final)
        self.assertEqual(final["delegation"]["status"], "completed")
        economics = final["delegation"]["metadata"]["economics"]
        self.assertEqual((economics["input_tokens"], economics["output_tokens"]), (150, 15))
        self.assertAlmostEqual(economics["provider_cost"], 0.003)
        usage = self.runtime.orchestration_ledger.list_usage_events(self.ctx.run_id)
        self.assertEqual(len(usage), 1)
        self.assertEqual((usage[0]["usage"]["input_tokens"], usage[0]["usage"]["output_tokens"]), (150, 15))
        self.assertAlmostEqual(usage[0]["cost"]["provider_cost"], 0.003)
        self.assertEqual(usage[0]["timing"]["provider_ms"], 900)
        reconciled = reservations.get(run_id, reservation_id)
        self.assertEqual(reconciled["status"], "reconciled")
        self.assertEqual(reconciled["reservation"]["units"], 512)
        self.assertEqual(reconciled["actual"], {"unit": "tokens", "units": 165, "measurement": "measured"})

    def test_shadow_route_is_idempotent_and_does_not_mutate_execution_authority(self) -> None:
        class NoDispatchProvider:
            def __init__(self):
                self.start_calls = 0

            def start(self, **kwargs):
                self.start_calls += 1
                raise AssertionError("shadow routing must not dispatch a provider")

            def active_count(self):
                return 0

            def close(self):
                return None

            def find_by_session(self, **kwargs):
                return None

        self.runtime._opencode_provider.close()
        provider = NoDispatchProvider()
        self.runtime._opencode_provider = provider
        self.post_stateless(action="get", client_id="chatweb", client_type="chatweb")
        before_ctx = self.runtime.orchestration_control.snapshot(self.ctx.run_id)
        before_controller = self.runtime.orchestration_ledger.get_controller_lease(self.ctx.run_id)
        before_fence = self.runtime.orchestration_ledger.get_write_fence("workspace")
        before_projection = self.runtime.task_state.get().get("orchestration")
        payload = {
            "action": "shadow_route",
            "client_id": "electron-panel",
            "client_type": "electron",
            "features": {
                "side_effect_class": "read_only",
                "scope": "broad",
                "risk": "low",
                "hard_reasoning": False,
            },
        }
        status, first = self.post_hub(payload)
        self.assertEqual(status, 200, first)
        self.assertTrue(first["recorded"])
        self.assertEqual(first["recommendation"]["recommendation"]["model"], "opencode-go/deepseek-v4-flash")
        self.assertFalse(first["recommendation"]["automatic_dispatch"])
        self.assertFalse(first["recommendation"]["mutation_allowed"])
        status, duplicate = self.post_hub(payload)
        self.assertEqual(status, 200, duplicate)
        self.assertFalse(duplicate["recorded"])
        self.assertEqual(
            duplicate["recommendation"]["recommendation_id"],
            first["recommendation"]["recommendation_id"],
        )
        after_ctx = self.runtime.orchestration_control.snapshot(self.ctx.run_id)
        after_controller = self.runtime.orchestration_ledger.get_controller_lease(self.ctx.run_id)
        after_fence = self.runtime.orchestration_ledger.get_write_fence("workspace")
        after_projection = self.runtime.task_state.get().get("orchestration")
        self.assertEqual((after_ctx.state, after_ctx.route_resolved), (before_ctx.state, before_ctx.route_resolved))
        self.assertEqual(after_controller, before_controller)
        self.assertEqual(after_fence, before_fence)
        self.assertEqual(after_projection, before_projection)
        self.assertEqual(provider.start_calls, 0)
        self.assertEqual(len(first["routing_evidence"]["shadow_recommendations"]), 1)
        snapshot_status, snapshot = self.get_snapshot()
        self.assertEqual(snapshot_status, 200)
        self.assertEqual(len(snapshot["routing_evidence"]["shadow_recommendations"]), 1)
        denied_status, denied = self.post_hub({**payload, "client_id": "opencode", "client_type": "opencode"})
        self.assertEqual(denied_status, 409, denied)
        self.assertEqual(denied["code"], "PROVIDER_DISPATCH_CLIENT_DENIED")

    def test_transfer_and_safe_rotation_projection(self) -> None:
        self.post_stateless(action="get", client_id="chatweb", client_type="chatweb")
        self.claim_chatweb_controller()
        initial_controller = self.runtime.orchestration_ledger.get_controller_lease(self.ctx.run_id)
        self.assertIsNotNone(initial_controller)
        initial_fencing_token = int(initial_controller["fencing_token"])
        pre_status, pre = self.get_snapshot()
        self.assertEqual(pre_status, 200)
        self.assertEqual(pre["schema_version"], 2)
        self.assertFalse(pre["provider_traffic"]["automatic_routing"]["enabled"])
        self.assertEqual(pre["flight_recorder"]["run_id"], self.ctx.run_id)
        self.assertEqual(pre["flight_recorder"]["phase_timing"]["source"], "eocl_event_timestamps")
        self.assertTrue(any(item["run_id"] == self.ctx.run_id for item in pre["history"]["runs"]))
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
        self.assertEqual(moved["fencing_token"], initial_fencing_token + 1)

        self.post_stateless(action="get", client_id="chatweb", client_type="chatweb")
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
