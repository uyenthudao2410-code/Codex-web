from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from coding_tools_mcp.orchestration_ledger import OrchestrationLedger
from coding_tools_mcp.performance_trace import PerformanceTraceStore
from coding_tools_mcp.server import Runtime, server_card_payload


class EfficiencyRuntimeTests(unittest.TestCase):
    def test_performance_trace_v5_records_model_visible_bytes_run_metrics_and_measured_phase_timing(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            store = PerformanceTraceStore(Path(temp))
            state = store.record(
                tool="agent_workflow",
                started_monotonic=10.0,
                finished_monotonic=11.0,
                request_bytes=100,
                response_bytes=200,
                model_visible_bytes=80,
                idempotency_eligible=True,
                idempotency_key_present=True,
                idempotency_policy="required",
                idempotency_key_source="derived",
                proof_cache_eligible=3,
                proof_cache_hits=2,
                proof_cache_misses=1,
                proof_cache_miss_reasons={"input_fingerprint_changed": 1, "bad": 0},
                proof_cache_saved_ms=1750,
                phase_timing={
                    "scope": "composite_read",
                    "source": "monotonic_local",
                    "workspace_ms": 10,
                    "localization_ms": 20.9,
                    "materialization_ms": 30,
                    "total_ms": 65,
                    "packet_build_ms": 999,
                    "negative_ms": -1,
                },
                orchestration={
                    "run_id": "run-1",
                    "wave_id": "wave-1",
                    "execution_mode": "mcp_only",
                    "route_requested": "auto",
                    "route_resolved": "deterministic",
                    "orchestration_state": "ACCEPTING",
                },
            )
            self.assertEqual(state["version"], 5)
            self.assertEqual(state["idempotency_eligible_calls"], 1)
            self.assertEqual(state["idempotency_eligible_key_calls"], 1)
            self.assertEqual(state["idempotency_key_calls"], 1)
            self.assertEqual(state["idempotency_required_calls"], 1)
            self.assertEqual(state["idempotency_required_key_calls"], 1)
            self.assertEqual(state["idempotency_auto_key_calls"], 1)
            self.assertEqual(state["proof_cache_eligible"], 3)
            self.assertEqual(state["proof_cache_hits"], 2)
            self.assertEqual(state["proof_cache_misses"], 1)
            self.assertEqual(state["proof_cache_miss_reasons"], {"input_fingerprint_changed": 1})
            self.assertEqual(state["proof_cache_saved_ms"], 1750)
            self.assertEqual(state["execution_mode_counts"], {"mcp_only": 1})
            self.assertEqual(state["route_resolved_counts"], {"deterministic": 1})
            self.assertEqual(state["orchestration_state_counts"], {"ACCEPTING": 1})
            event = state["recent"][-1]
            self.assertTrue(event["idempotency_eligible"])
            self.assertTrue(event["idempotency_key_present"])
            self.assertEqual(event["idempotency_policy"], "required")
            self.assertEqual(event["idempotency_key_source"], "derived")
            self.assertEqual(event["proof_cache_eligible"], 3)
            self.assertEqual(event["proof_cache_hits"], 2)
            self.assertEqual(event["proof_cache_misses"], 1)
            self.assertEqual(event["proof_cache_miss_reasons"], {"input_fingerprint_changed": 1})
            self.assertEqual(event["route_resolved"], "deterministic")
            self.assertEqual(event["model_visible_bytes"], 80)
            self.assertEqual(event["phase_timing"], {
                "scope": "composite_read",
                "source": "monotonic_local",
                "workspace_ms": 10,
                "localization_ms": 20,
                "materialization_ms": 30,
                "total_ms": 65,
                "packet_build_ms": 999,
            })
            self.assertEqual(state["model_visible_bytes"], 80)
            self.assertEqual(state["phase_timing_samples"], 1)
            self.assertEqual(state["phase_timing_ms"], {
                "workspace_ms": 10,
                "localization_ms": 20,
                "materialization_ms": 30,
                "total_ms": 65,
                "packet_build_ms": 999,
            })
            metric = state["run_metrics"]["run-1"]
            self.assertEqual(metric["tool_calls"], 1)
            self.assertEqual(metric["idempotency_eligible_calls"], 1)
            self.assertEqual(metric["idempotency_eligible_key_calls"], 1)
            self.assertEqual(metric["idempotency_required_calls"], 1)
            self.assertEqual(metric["idempotency_required_key_calls"], 1)
            self.assertEqual(metric["proof_cache_eligible"], 3)
            self.assertEqual(metric["proof_cache_misses"], 1)
            self.assertEqual(metric["proof_cache_miss_reasons"], {"input_fingerprint_changed": 1})
            self.assertEqual(metric["proof_cache_saved_ms"], 1750)
            self.assertEqual(metric["model_visible_bytes"], 80)
            self.assertEqual(metric["phase_timing_samples"], 1)
            self.assertEqual(metric["phase_timing_ms"]["localization_ms"], 20)

    def test_runtime_phase_timing_extractor_ignores_cached_or_unmeasured_values(self) -> None:
        live = {
            "prepared": {
                "composite_read": {
                    "cache": {"hit": False},
                    "execution": {"phase_timing": {
                        "source": "monotonic_local",
                        "workspace_ms": 1,
                        "localization_ms": 2,
                        "materialization_ms": 3,
                        "total_ms": 6,
                    }},
                }
            }
        }
        self.assertEqual(Runtime._measured_phase_timing(live), {
            "scope": "composite_read",
            "source": "monotonic_local",
            "workspace_ms": 1,
            "localization_ms": 2,
            "materialization_ms": 3,
            "total_ms": 6,
        })
        cached = json.loads(json.dumps(live))
        cached["prepared"]["composite_read"]["cache"]["hit"] = True
        self.assertEqual(Runtime._measured_phase_timing(cached), {})
        unmeasured = json.loads(json.dumps(live))
        unmeasured["prepared"]["composite_read"]["execution"]["phase_timing"]["source"] = "estimated"
        self.assertEqual(Runtime._measured_phase_timing(unmeasured), {})

    def test_runtime_trace_counts_only_model_facing_text_as_model_visible_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temp, patch.dict("os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}):
            runtime = Runtime(Path(temp), permission_mode="safe")
            try:
                result = runtime.call_tool("workspace_context", {"detail": "compact"})
                expected = sum(
                    len(str(block.get("text") or "").encode("utf-8"))
                    for block in result.get("content", [])
                    if isinstance(block, dict) and block.get("type") == "text"
                )
                event = runtime.performance_trace.get()["recent"][-1]
                self.assertGreater(expected, 0)
                self.assertEqual(event["model_visible_bytes"], expected)
                self.assertGreaterEqual(event["response_bytes"], event["model_visible_bytes"])
            finally:
                runtime.close()

    def test_idempotency_policy_separates_required_identity_from_optional_side_effects(self) -> None:
        self.assertFalse(Runtime._idempotency_eligible_call("workspace_context", {}))
        self.assertFalse(Runtime._idempotency_eligible_call("agent_workflow", {"phase": "prepare"}))
        self.assertTrue(Runtime._idempotency_eligible_call("agent_workflow", {"phase": "execute"}))
        self.assertTrue(Runtime._idempotency_eligible_call("exec_command", {"cmd": "echo ok"}))
        self.assertFalse(Runtime._idempotency_eligible_call("command_control", {"action": "poll"}))
        self.assertTrue(Runtime._idempotency_eligible_call("command_control", {"action": "kill"}))
        self.assertFalse(Runtime._idempotency_eligible_call("task_control", {"action": "handoff", "handoff_action": "get"}))
        self.assertTrue(Runtime._idempotency_eligible_call("task_control", {"action": "handoff", "handoff_action": "record"}))
        self.assertTrue(Runtime._idempotency_eligible_call("task_control", {"action": "restart_runtime"}))
        self.assertEqual(Runtime._idempotency_policy("workspace_context", {}), "none")
        self.assertEqual(Runtime._idempotency_policy("agent_workflow", {"phase": "execute"}), "required")
        self.assertEqual(Runtime._idempotency_policy("agent_workflow", {"phase": "run"}), "optional")
        self.assertEqual(Runtime._idempotency_policy("exec_command", {"cmd": "echo ok"}), "optional")
        self.assertEqual(Runtime._idempotency_policy("command_control", {"action": "kill"}), "optional")
        self.assertEqual(Runtime._idempotency_policy("task_control", {"action": "handoff", "handoff_action": "record"}), "optional")
        self.assertEqual(Runtime._idempotency_policy("task_control", {"action": "restart_runtime"}), "optional")
        self.assertEqual(Runtime._idempotency_policy("task_control", {"action": "accept"}), "required")
        self.assertEqual(Runtime._idempotency_policy("task_control", {"action": "reject"}), "required")

    def test_required_idempotency_key_is_derived_only_from_durable_run_wave_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp), permission_mode="safe")
            try:
                runtime.task_state.ensure_started("derive key")
                runtime.task_state.set_orchestration_projection({
                    "run_id": "run-a",
                    "wave_id": "wave-a",
                    "orchestration_state": "READY",
                }, event="test_projection")
                request = {"phase": "execute", "workflow": "bugfix", "objective": "fix leaf"}
                first = runtime._derive_idempotency_key("agent_workflow", request)
                same = runtime._derive_idempotency_key("agent_workflow", dict(request))
                changed = runtime._derive_idempotency_key("agent_workflow", {**request, "objective": "fix other leaf"})
                self.assertTrue(first.startswith("auto-v1:"))
                self.assertEqual(first, same)
                self.assertNotEqual(first, changed)
                self.assertEqual(runtime._derive_idempotency_key("exec_command", {"cmd": "echo ok"}), "")
                self.assertTrue(runtime._derive_idempotency_key("task_control", {"action": "accept"}).startswith("auto-v1:"))
                with (
                    patch.object(runtime, "_current_hub_client", return_value={"client_id": "chatweb"}),
                    patch.object(runtime.orchestration_ledger, "get_controller_lease", return_value={"fencing_token": 2}),
                ):
                    chat_accept = runtime._derive_idempotency_key("task_control", {"action": "accept"})
                with (
                    patch.object(runtime, "_current_hub_client", return_value={"client_id": "codex-desktop"}),
                    patch.object(runtime.orchestration_ledger, "get_controller_lease", return_value={"fencing_token": 2}),
                ):
                    desktop_accept = runtime._derive_idempotency_key("task_control", {"action": "accept"})
                with (
                    patch.object(runtime, "_current_hub_client", return_value={"client_id": "chatweb"}),
                    patch.object(runtime.orchestration_ledger, "get_controller_lease", return_value={"fencing_token": 3}),
                ):
                    chat_new_fence = runtime._derive_idempotency_key("task_control", {"action": "accept"})
                self.assertNotEqual(chat_accept, desktop_accept)
                self.assertNotEqual(chat_accept, chat_new_fence)
                runtime.task_state.set_orchestration_projection({
                    "run_id": "run-a",
                    "wave_id": "wave-b",
                    "orchestration_state": "READY",
                }, event="test_projection")
                self.assertNotEqual(first, runtime._derive_idempotency_key("agent_workflow", request))
            finally:
                runtime.close()

    def test_error_taxonomy_uses_structured_code_and_category_only(self) -> None:
        self.assertEqual(Runtime._error_class({"code": "CANDIDATE_TARGET_MISSING", "category": "validation"}), "CONTROL_PATH")
        self.assertEqual(Runtime._error_class({"code": "PROMPT_TOO_LARGE", "category": "runtime"}), "PROMPT_SIZE")
        self.assertEqual(Runtime._error_class({"code": "PROVIDER_CAPACITY", "category": "runtime"}), "CAPACITY")
        self.assertEqual(Runtime._error_class({"code": "PERMISSION_REQUIRED", "category": "permission"}), "AUTHORITY_DENIED")
        self.assertEqual(Runtime._error_class({"code": "SOMETHING_NEW", "category": "runtime"}), "RUNTIME")

    def test_workspace_context_exposes_non_secret_runtime_activation_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp, patch.dict("os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}):
            runtime = Runtime(Path(temp), permission_mode="safe")
            try:
                compact = runtime.workspace_context({"detail": "compact"})
                self.assertNotIn("runtime", compact)
                context = runtime.workspace_context({"detail": "full"})
                identity = context["runtime"]
                self.assertEqual(identity["server_instance_id"], runtime.server_instance_id)
                self.assertEqual(identity["process_instance_id"], runtime.process_instance_id)
                self.assertEqual(identity["performance_trace_version"], 5)
                contract = identity["tool_contract"]
                self.assertEqual(contract["schema_version"], 1)
                self.assertEqual(contract["profile"], "smart-v3")
                self.assertEqual(contract["tool_count"], 8)
                self.assertEqual(len(contract["sha256"]), 64)
                metadata = identity["tool_metadata"]
                self.assertEqual(metadata["risk_vocabulary"], ["read_only", "project_write", "job_run", "account_manage", "unknown"])
                self.assertEqual(metadata["ownership"]["mcp_annotation_owner"], "python:ToolSpec")
                self.assertEqual(metadata["ownership"]["native_execution_risk_owner"], "rust:ToolMetadata/ToolRisk")
                self.assertEqual(metadata["ownership"]["authority_owner"], "EOCL+permission+write_lease")
                self.assertEqual(metadata["smart_v3_risk"]["workspace_context"], "read_only")
                self.assertEqual(metadata["smart_v3_risk"]["agent_workflow"], "project_write")
                self.assertEqual(metadata["smart_v3_risk"]["exec_command"], "job_run")
                self.assertEqual(metadata["smart_v3_risk"]["command_control"], "job_run")
                self.assertEqual(metadata["smart_v3_risk"]["task_control"], "unknown")
                card = server_card_payload(runtime)
                self.assertEqual(card["tools"]["contractSha256"], contract["sha256"])
                self.assertEqual(runtime.tool_contract["tool_count"], 8)
                self.assertNotIn("auth_token", identity)
            finally:
                runtime.close()

    def test_stale_run_reconciliation_preserves_live_owners(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            now = time.time()
            stale_run = ledger.create_run(objective="abandoned")
            protected_run = ledger.create_run(objective="still running")
            ledger.start_background_operation(
                operation_id="op-live",
                server_instance_id="server",
                tool="agent_workflow",
                run_id=protected_run,
                summary={},
            )
            reconciled = ledger.reconcile_stale_runs(stale_after_seconds=3600, now=now + 7200)
            self.assertIn(stale_run, reconciled)
            self.assertNotIn(protected_run, reconciled)
            self.assertEqual(ledger.get_run(stale_run)["status"], "stale")
            self.assertEqual(ledger.get_run(protected_run)["status"], "active")
            events = ledger.list_events(stale_run)
            self.assertEqual(events[-1]["event_type"], "run_stale_reconciled")
            self.assertEqual(events[-1]["state_after"], "ABORTED")

    @unittest.skipUnless(shutil.which("git"), "git is required")
    def test_orchestration_identity_ignores_runtime_state_but_detects_source_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
            source = root / "app.py"
            source.write_text("VALUE = 1\n", encoding="utf-8")
            subprocess.run(["git", "add", "app.py"], cwd=root, check=True, capture_output=True)
            subprocess.run(
                ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "base"],
                cwd=root,
                check=True,
                capture_output=True,
            )
            runtime = Runtime(root, permission_mode="safe")
            try:
                first = runtime._orchestration_workspace_identity(".")
                runtime_state = root / ".coding-tools" / "volatile.json"
                runtime_state.parent.mkdir(parents=True, exist_ok=True)
                runtime_state.write_text('{"tick": 1}\n', encoding="utf-8")
                second = runtime._orchestration_workspace_identity(".")
                self.assertEqual(first["worktree_fp"], second["worktree_fp"])
                self.assertNotIn(".coding-tools/volatile.json", second["dirty_paths"])
                source.write_text("VALUE = 2\n", encoding="utf-8")
                third = runtime._orchestration_workspace_identity(".")
                self.assertNotEqual(second["worktree_fp"], third["worktree_fp"])
                self.assertIn("app.py", third["dirty_paths"])
            finally:
                runtime.close()


if __name__ == "__main__":
    unittest.main()
