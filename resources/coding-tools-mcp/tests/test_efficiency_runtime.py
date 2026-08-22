from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import time
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from coding_tools_mcp.orchestration_ledger import OrchestrationLedger
from coding_tools_mcp.performance_trace import ERROR_TAXONOMY_EPOCH, PerformanceTraceStore
from coding_tools_mcp.server import Runtime, server_card_payload
from coding_tools_mcp.task_state import TaskStateStore
from coding_tools_mcp.tool_contract import CAPABILITY_PROFILES, TOOL_CONTRACT_RUNTIME


class EfficiencyRuntimeTests(unittest.TestCase):
    def test_result_tail_telemetry_counts_continuation_rereads_and_stale_events(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            store = PerformanceTraceStore(Path(temp))
            tail = {
                "source_total_bytes": 10_000,
                "page_output_bytes": 1_000,
                "remaining_bytes": 9_000,
                "truncated": True,
                "continuation_offered": True,
                "continuation_read": True,
                "continuation_reread": True,
                "continuation_stale": False,
            }
            state = store.record(
                tool="agent_workflow", started_monotonic=1.0, finished_monotonic=1.1,
                result_tail=tail, orchestration={"run_id": "run-tail"},
            )
            self.assertEqual(state["result_tail_samples"], 1)
            self.assertEqual(state["result_tail_source_bytes"], 10_000)
            self.assertEqual(state["result_tail_page_bytes"], 1_000)
            self.assertEqual(state["result_tail_remaining_bytes"], 9_000)
            self.assertEqual(state["result_truncated_calls"], 1)
            self.assertEqual(state["result_continuation_offered"], 1)
            self.assertEqual(state["result_continuation_reads"], 1)
            self.assertEqual(state["result_continuation_rereads"], 1)
            self.assertEqual(state["result_continuation_stale"], 0)
            self.assertEqual(state["run_metrics"]["run-tail"]["result_continuation_reads"], 1)
            self.assertEqual(Runtime._measured_result_tail({"execution": {"git_diff": {"result_tail": tail}}}), tail)
            stale = Runtime._measured_result_tail({"error": {"details": {"result_tail": {"continuation_stale": True}}}})
            self.assertTrue(stale["continuation_stale"])

    def test_performance_trace_v6_records_model_visible_bytes_run_metrics_and_measured_phase_timing(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            store = PerformanceTraceStore(Path(temp))
            state = store.record(
                tool="agent_workflow",
                started_monotonic=10.0,
                finished_monotonic=11.0,
                started_wall_utc="2026-08-15T00:00:00.000Z",
                finished_wall_utc="2026-08-15T00:00:01.000Z",
                request_bytes=100,
                response_bytes=200,
                model_visible_bytes=80,
                idempotency_eligible=True,
                idempotency_key_present=True,
                idempotency_policy="required",
                idempotency_key_source="derived",
                idempotency_operation="agent_workflow:execute",
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
                localization={
                    "semantic_available": True,
                    "query_count": 3,
                    "semantic_attempted": 3,
                    "semantic_handled": 2,
                    "text_fallback_queries": 1,
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
            self.assertEqual(state["version"], 6)
            self.assertEqual(state["idempotency_eligible_calls"], 1)
            self.assertEqual(state["idempotency_eligible_key_calls"], 1)
            self.assertEqual(state["idempotency_key_calls"], 1)
            self.assertEqual(state["idempotency_required_calls"], 1)
            self.assertEqual(state["idempotency_required_key_calls"], 1)
            self.assertEqual(state["idempotency_auto_key_calls"], 1)
            self.assertEqual(state["idempotency_policy_epoch"], "task_epoch_v1")
            self.assertEqual(state["idempotency_current_policy_required_calls"], 1)
            self.assertEqual(state["idempotency_current_policy_required_key_calls"], 1)
            self.assertEqual(state["idempotency_current_policy_by_operation"]["agent_workflow:execute"]["keyed"], 1)
            self.assertEqual(state["proof_cache_eligible"], 3)
            self.assertEqual(state["proof_cache_hits"], 2)
            self.assertEqual(state["proof_cache_misses"], 1)
            self.assertEqual(state["proof_cache_miss_reasons"], {"input_fingerprint_changed": 1})
            self.assertEqual(state["proof_cache_saved_ms"], 1750)
            self.assertEqual(state["execution_mode_counts"], {"mcp_only": 1})
            self.assertEqual(state["route_resolved_counts"], {"deterministic": 1})
            self.assertEqual(state["orchestration_state_counts"], {"ACCEPTING": 1})
            event = state["recent"][-1]
            self.assertEqual(event["started_at"], "2026-08-15T00:00:00.000Z")
            self.assertEqual(event["finished_at"], "2026-08-15T00:00:01.000Z")
            self.assertEqual(event["wall_time_source"], "operation_boundary")
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
            self.assertEqual(state["localization_samples"], 1)
            self.assertEqual(state["localization_queries"], 3)
            self.assertEqual(state["lsp_available_samples"], 1)
            self.assertEqual(state["lsp_attempted_queries"], 3)
            self.assertEqual(state["lsp_handled_queries"], 2)
            self.assertEqual(state["fallback_search_queries"], 1)
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
            self.assertEqual(metric["localization_samples"], 1)
            self.assertEqual(metric["lsp_handled_queries"], 2)
            self.assertEqual(metric["fallback_search_queries"], 1)

    def test_performance_trace_v6_hourly_metrics_bucket_by_started_hour_and_prune_rolling_window(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            store = PerformanceTraceStore(Path(temp))
            state = store.record(
                tool="agent_workflow",
                started_monotonic=10.0,
                finished_monotonic=11.0,
                started_wall_utc="2026-08-18T10:15:00.000Z",
                finished_wall_utc="2026-08-18T10:15:01.000Z",
                request_bytes=100,
                response_bytes=200,
                model_visible_bytes=80,
                cache_hit=True,
                orchestration={"run_id": "run-hourly"},
            )
            first_hour = int(datetime.fromisoformat("2026-08-18T10:15:00+00:00").timestamp() // 3600)
            self.assertIn(first_hour, state["hourly_metrics"])
            bucket = state["hourly_metrics"][first_hour]
            self.assertEqual(bucket["hour"], first_hour)
            self.assertEqual(bucket["tool_calls"], 1)
            self.assertEqual(bucket["cache_hits"], 1)
            self.assertEqual(bucket["model_visible_bytes"], 80)
            self.assertEqual(bucket["request_bytes"], 100)
            self.assertEqual(bucket["response_bytes"], 200)
            self.assertEqual(bucket["local_execution_ms"], 1000)
            self.assertEqual(bucket["last_finished_at"], "2026-08-18T10:15:01.000Z")

            second = store.record(
                tool="exec_command",
                started_monotonic=12.0,
                finished_monotonic=12.5,
                started_wall_utc="2026-08-18T10:45:00.000Z",
                finished_wall_utc="2026-08-18T10:45:00.500Z",
                model_visible_bytes=20,
                ok=False,
            )
            same_hour = int(datetime.fromisoformat("2026-08-18T10:45:00+00:00").timestamp() // 3600)
            self.assertEqual(same_hour, first_hour)
            self.assertEqual(second["hourly_metrics"][first_hour]["tool_calls"], 2)
            self.assertEqual(second["hourly_metrics"][first_hour]["errors"], 1)
            self.assertEqual(second["hourly_metrics"][first_hour]["model_visible_bytes"], 100)

            third = store.record(
                tool="task_control",
                started_monotonic=13.0,
                finished_monotonic=13.1,
                started_wall_utc="2026-08-18T11:00:00.000Z",
                finished_wall_utc="2026-08-18T11:00:00.100Z",
                model_visible_bytes=7,
            )
            next_hour = int(datetime.fromisoformat("2026-08-18T11:00:00+00:00").timestamp() // 3600)
            self.assertNotEqual(next_hour, first_hour)
            self.assertEqual(third["hourly_metrics"][next_hour]["tool_calls"], 1)
            self.assertEqual(third["hourly_metrics"][next_hour]["model_visible_bytes"], 7)

    def test_performance_trace_v6_hourly_metrics_normalize_rejects_stale_and_malformed_buckets(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state_dir = root / ".coding-tools"
            state_dir.mkdir(parents=True)
            stale_hour = int(time.time() // 3600) - 400
            current_hour = int(time.time() // 3600)
            (state_dir / "performance.json").write_text(json.dumps({
                "version": 6,
                "hourly_metrics": {
                    str(stale_hour): {"hour": stale_hour, "tool_calls": 3, "model_visible_bytes": 99},
                    str(current_hour): {"hour": current_hour, "tool_calls": 1, "model_visible_bytes": 10, "errors": -5, "last_finished_at": "x" * 90},
                    "not-a-number": {"hour": 0, "tool_calls": 1},
                    str(current_hour + 5): "garbage",
                },
            }), encoding="utf-8")
            store = PerformanceTraceStore(root)
            normalized = store.get()["hourly_metrics"]
            self.assertNotIn(stale_hour, normalized)
            self.assertIn(current_hour, normalized)
            self.assertEqual(normalized[current_hour]["tool_calls"], 1)
            self.assertEqual(normalized[current_hour]["errors"], 0)
            self.assertEqual(normalized[current_hour]["model_visible_bytes"], 10)
            self.assertLessEqual(len(normalized[current_hour]["last_finished_at"]), 40)

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

    def test_runtime_localization_extractor_counts_live_composite_only(self) -> None:
        live = {
            "context": {
                "composite_read": {
                    "plan": {"query_count": 2},
                    "cache": {"hit": False},
                    "execution": {"localization": {
                        "provider": {"available": True, "provider": "native-lsp-test"},
                        "semantic_attempted": 2,
                        "semantic_handled": 1,
                        "text_fallback_queries": 1,
                    }},
                }
            }
        }
        self.assertEqual(Runtime._measured_localization(live), {
            "semantic_available": True,
            "query_count": 2,
            "semantic_attempted": 2,
            "semantic_handled": 1,
            "text_fallback_queries": 1,
        })
        cached = json.loads(json.dumps(live))
        cached["context"]["composite_read"]["cache"]["hit"] = True
        self.assertEqual(Runtime._measured_localization(cached), {})

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
                self.assertEqual(event["wall_time_source"], "operation_boundary")
                self.assertLessEqual(event["started_at"], event["finished_at"])
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

    def test_required_idempotency_keys_use_task_epoch_for_workflow_and_authority_epoch_for_accept(self) -> None:
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
                self.assertEqual(first, runtime._derive_idempotency_key("agent_workflow", request))
                with (
                    patch.object(runtime, "_current_hub_client", return_value={"client_id": "chatweb"}),
                    patch.object(runtime.orchestration_ledger, "get_controller_lease", return_value={"fencing_token": 2}),
                ):
                    chat_accept_new_wave = runtime._derive_idempotency_key("task_control", {"action": "accept"})
                self.assertNotEqual(chat_accept, chat_accept_new_wave)

                runtime.task_state.update({"status": "completed"})
                runtime.task_state.ensure_started("derive key again")
                self.assertNotEqual(first, runtime._derive_idempotency_key("agent_workflow", request))
            finally:
                runtime.close()

    def test_error_taxonomy_uses_structured_code_and_category_only(self) -> None:
        self.assertEqual(Runtime._error_class({"code": "CANDIDATE_TARGET_MISSING", "category": "validation"}), "CONTROL_PATH")
        self.assertEqual(Runtime._error_class({"code": "PROMPT_TOO_LARGE", "category": "runtime"}), "PROMPT_SIZE")
        self.assertEqual(Runtime._error_class({"code": "PROVIDER_CAPACITY", "category": "runtime"}), "CAPACITY")
        self.assertEqual(Runtime._error_class({"code": "PERMISSION_REQUIRED", "category": "permission"}), "AUTHORITY_DENIED")
        self.assertEqual(Runtime._error_class({"code": "SOMETHING_NEW", "category": "runtime"}), "RUNTIME")
        self.assertEqual(Runtime._error_class({"code": "WRITE_FAILED", "category": "filesystem"}), "FILESYSTEM")
        self.assertEqual(Runtime._error_class({"code": "RULE_DENIED", "category": "policy"}), "POLICY")
        self.assertEqual(Runtime._error_class({"code": "MISSING_RESOURCE", "category": "not_found"}), "NOT_FOUND")
        self.assertEqual(Runtime._error_class({"code": "UNEXPECTED_STATE", "category": "internal"}), "INTERNAL")
        self.assertEqual(Runtime._error_class({"code": "STATE_RACE", "category": "conflict"}), "CONFLICT")
        self.assertEqual(Runtime._error_class({"code": "SOMETHING_NEW", "category": "novel"}), "UNKNOWN")

    def test_error_taxonomy_epoch_preserves_cumulative_unknown_without_backfill(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state_dir = root / ".coding-tools"
            state_dir.mkdir(parents=True)
            (state_dir / "performance.json").write_text(json.dumps({
                "version": 6,
                "tool_calls": 463,
                "errors": 463,
                "error_class_counts": {"RUNTIME": 169, "UNKNOWN": 45},
            }), encoding="utf-8")
            store = PerformanceTraceStore(root)
            migrated = store.get()
            self.assertEqual(migrated["error_class_counts"], {"RUNTIME": 169, "UNKNOWN": 45})
            self.assertEqual(migrated["error_taxonomy_epoch"], ERROR_TAXONOMY_EPOCH)
            self.assertEqual(migrated["error_taxonomy_current_counts"], {})

            observed = store.record(
                tool="exec_command",
                started_monotonic=1.0,
                finished_monotonic=1.1,
                ok=False,
                error_class="FILESYSTEM",
            )
            self.assertEqual(observed["error_class_counts"], {"RUNTIME": 169, "UNKNOWN": 45, "FILESYSTEM": 1})
            self.assertEqual(observed["error_taxonomy_current_counts"], {"FILESYSTEM": 1})

    def test_workspace_context_exposes_non_secret_runtime_activation_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp, patch.dict("os.environ", {
            "CODING_TOOLS_MCP_TOOL_MODE": "smart",
            "CODING_TOOLS_MCP_NATIVE_LSP_URL": "",
            "CODING_TOOLS_MCP_NATIVE_LSP_CREDENTIAL_FILE": "",
            "APPDATA": "",
        }):
            runtime = Runtime(Path(temp), permission_mode="safe")
            try:
                compact = runtime.workspace_context({"detail": "compact"})
                self.assertNotIn("runtime", compact)
                context = runtime.workspace_context({"detail": "full"})
                identity = context["runtime"]
                self.assertTrue(identity["runtime_version"])
                self.assertEqual(identity["server_instance_id"], runtime.server_instance_id)
                self.assertEqual(identity["process_instance_id"], runtime.process_instance_id)
                self.assertEqual(identity["performance_trace_version"], 6)
                self.assertEqual(identity["idempotency_policy_epoch"], "task_epoch_v1")
                self.assertIn("git_head", identity["source"])
                self.assertIn("worktree_fp", identity["source"])
                self.assertEqual(identity["stale_run_threshold_seconds"], runtime.stale_run_seconds)
                contract = identity["tool_contract"]
                self.assertEqual(contract["schema_version"], 1)
                self.assertEqual(contract["profile"], "smart-v3")
                self.assertEqual(contract["tool_count"], 8)
                self.assertEqual(len(contract["sha256"]), 64)
                self.assertEqual(contract["sha256"], "ab122032f504f960a0f3dc33af6d8d0996f6aca927f2b849be389e51c2820e36")
                self.assertTrue(contract["evaluation"]["supported"])
                self.assertEqual(contract["evaluation"]["schema_version"], 2)
                self.assertEqual(
                    contract["evaluation"]["sha256"],
                    "eaf5c214b1f8e596cc06c4922c67d8a09a5a9e5b7e145b40b9dc591bf283e913",
                )
                metadata = identity["tool_metadata"]
                self.assertEqual(metadata["schema_version"], 2)
                self.assertEqual(metadata["risk_vocabulary"], ["read_only", "project_write", "job_run", "account_manage", "unknown"])
                self.assertEqual(metadata["ownership"]["mcp_annotation_owner"], "python:ToolSpec")
                self.assertEqual(metadata["ownership"]["native_execution_risk_owner"], "rust:ToolMetadata/ToolRisk")
                self.assertEqual(metadata["ownership"]["authority_owner"], "EOCL+permission+write_lease")
                self.assertEqual(metadata["smart_v3_risk"]["workspace_context"], "read_only")
                self.assertEqual(metadata["smart_v3_risk"]["agent_workflow"], "project_write")
                self.assertEqual(metadata["smart_v3_risk"]["exec_command"], "job_run")
                self.assertEqual(metadata["smart_v3_risk"]["command_control"], "job_run")
                self.assertEqual(metadata["smart_v3_risk"]["task_control"], "unknown")
                self.assertEqual(metadata["runtime"]["implementation"], "python:ToolContractRuntime")
                self.assertEqual(metadata["smart_v3_tools"]["exec_command"]["presentation"]["card"], "terminal")
                self.assertEqual(metadata["smart_v3_tools"]["agent_workflow"]["mutation_class"], "project")
                self.assertFalse(metadata["capability_profiles"]["candidate_mini"]["checkout_write"])
                self.assertEqual(
                    metadata["capability_profiles"]["opencode_readonly"]["tool_names"],
                    ["glob", "grep", "list", "lsp", "read"],
                )
                self.assertFalse(metadata["experimental_code_mode"]["enabled"])
                self.assertEqual(metadata["experimental_code_mode"]["status"], "gated")
                semantic = identity["semantic_localization"]
                self.assertFalse(semantic["available"])
                self.assertTrue(semantic["read_only"])
                self.assertEqual(semantic["reason"], "NATIVE_LSP_BINDING_NOT_CONFIGURED")
                card = server_card_payload(runtime)
                self.assertEqual(card["tools"]["contractSha256"], contract["sha256"])
                self.assertEqual(runtime.tool_contract["tool_count"], 8)
                self.assertNotIn("auth_token", identity)
            finally:
                runtime.close()

    def test_tool_contract_runtime_preserves_smart_surface_and_owns_presentation(self) -> None:
        names = TOOL_CONTRACT_RUNTIME.exposed_names("smart", gate_resolver=lambda _name: True)
        self.assertEqual(set(names), {
            "workspace_context", "agent_workflow", "task_control", "document_workflow",
            "exec_command", "command_control", "request_permissions", "view_image",
        })
        self.assertEqual(len(names), 8)
        self.assertEqual(TOOL_CONTRACT_RUNTIME.presentation("git_diff")["card"], "diff")
        self.assertFalse(CAPABILITY_PROFILES["deep_code"].checkout_write)
        self.assertFalse(CAPABILITY_PROFILES["deep_code"].network)

    def test_stale_run_reconciliation_preserves_live_owners(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            now = time.time()
            stale_run = ledger.create_run(objective="abandoned")
            stale_wave = ledger.create_wave(stale_run, execution_mode="mcp_only")
            protected_run = ledger.create_run(objective="still running")
            protected_wave = ledger.create_wave(protected_run, execution_mode="mcp_only")
            ledger.start_background_operation(
                operation_id="op-live",
                server_instance_id="server",
                tool="agent_workflow",
                run_id=protected_run,
                summary={},
            )
            controller_run = ledger.create_run(objective="waiting for controller")
            controller_wave = ledger.create_wave(controller_run, execution_mode="mcp_only")
            ledger.upsert_hub_client(client_id="chatweb-test", client_type="chatweb", role="controller")
            ledger.acquire_controller_lease(
                run_id=controller_run,
                owner_client_id="chatweb-test",
                lease_id="lease-live",
                ttl_seconds=10_000,
            )
            candidates = ledger.stale_run_candidates(stale_after_seconds=3600, now=now + 7200)
            self.assertIn(stale_run, candidates)
            self.assertNotIn(protected_run, candidates)
            self.assertNotIn(controller_run, candidates)
            reconciled = ledger.reconcile_stale_runs(stale_after_seconds=3600, now=now + 7200)
            self.assertIn(stale_run, reconciled)
            self.assertNotIn(protected_run, reconciled)
            self.assertNotIn(controller_run, reconciled)
            self.assertEqual(ledger.stale_run_candidates(stale_after_seconds=3600, now=now + 7200), [])
            self.assertEqual(ledger.get_run(stale_run)["status"], "stale")
            self.assertEqual(ledger.get_run(protected_run)["status"], "active")
            self.assertEqual(ledger.get_run(controller_run)["status"], "active")
            stale_wave_row = next(item for item in ledger.list_waves(stale_run) if item["wave_id"] == stale_wave)
            self.assertEqual(stale_wave_row["status"], "aborted")
            self.assertIsNotNone(stale_wave_row["finished_at"])
            self.assertEqual(ledger.list_waves(protected_run)[0]["wave_id"], protected_wave)
            self.assertEqual(ledger.list_waves(controller_run)[0]["wave_id"], controller_wave)
            events = ledger.list_events(stale_run)
            self.assertEqual(events[-1]["event_type"], "run_stale_reconciled")
            self.assertEqual(events[-1]["state_after"], "ABORTED")
            self.assertTrue(any(item["event_type"] == "wave_lifecycle_reconciled" for item in events))

    def test_stale_reconciliation_repairs_terminal_parent_active_waves_idempotently(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            cases = {
                "accepted": ("accepted", "CHECKPOINTED"),
                "blocked": ("blocked", "BLOCKED"),
                "aborted": ("aborted", "ABORTED"),
                "stale": ("aborted", "ABORTED"),
            }
            for run_status, (wave_status, state_after) in cases.items():
                run_id = ledger.create_run(objective=f"repair {run_status}")
                wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
                ledger.finish_run(run_id, status=run_status)
                self.assertEqual(ledger.reconcile_stale_runs(now=time.time()), [])
                wave = next(item for item in ledger.list_waves(run_id) if item["wave_id"] == wave_id)
                self.assertEqual(wave["status"], wave_status)
                self.assertIsNotNone(wave["finished_at"])
                repair_events = [
                    item for item in ledger.list_events(run_id)
                    if item["event_type"] == "wave_lifecycle_reconciled"
                ]
                self.assertEqual(len(repair_events), 1)
                self.assertEqual(repair_events[0]["state_after"], state_after)
                self.assertEqual(ledger.reconcile_stale_runs(now=time.time()), [])
                self.assertEqual(
                    len([item for item in ledger.list_events(run_id) if item["event_type"] == "wave_lifecycle_reconciled"]),
                    1,
                )
                self.assertTrue(ledger.verify_chain(run_id)["ok"])

    def test_runtime_reconciles_stale_parent_accepting_task_projection(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            run_id = ledger.create_run(objective="stale acceptance")
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
            ledger.finish_run(run_id, status="stale", metadata={"stale_reason": "fixture"})
            store = TaskStateStore(root)
            store.update({"objective": "stale acceptance", "new_task": True})
            store.set_orchestration_projection({
                "run_id": run_id,
                "wave_id": wave_id,
                "orchestration_state": "ACCEPTING",
                "write_lease_id": "old-lease",
                "write_owner": "MCP",
            })

            runtime = Runtime(root, permission_mode="safe")
            try:
                state = runtime.task_state.get()
                projection = state["orchestration"]
                self.assertTrue(runtime.reconciled_task_orchestration)
                self.assertEqual(projection["orchestration_state"], "ABORTED")
                self.assertEqual(projection["run_id"], run_id)
                self.assertEqual(projection["wave_id"], wave_id)
                self.assertEqual(projection["write_lease_id"], "")
                self.assertEqual(projection["write_owner"], "")
                self.assertEqual(ledger.get_run(run_id)["status"], "stale")
                self.assertEqual(ledger.list_waves(run_id)[0]["status"], "aborted")
                self.assertEqual(state["events"][-1]["event"], "orchestration_projection_reconciled")
                identity = runtime.workspace_context({"detail": "full"})["runtime"]
                self.assertTrue(identity["task_orchestration_projection_reconciled"])
            finally:
                runtime.close()

    def test_runtime_startup_preserves_stale_candidates_until_explicit_reconcile(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            run_id = ledger.create_run(objective="abandoned runtime")
            ledger.create_wave(run_id, execution_mode="mcp_only")
            future = time.time() + 7200
            with (
                patch.dict("os.environ", {"CODING_TOOLS_MCP_STALE_RUN_SECONDS": "3600"}),
                patch("coding_tools_mcp.orchestration_ledger.time.time", return_value=future),
            ):
                runtime = Runtime(root, permission_mode="safe")
                try:
                    identity = runtime.workspace_context({"detail": "full"})["runtime"]
                    recovery = runtime.task_control({"action": "get"})["recovery"]
                finally:
                    runtime.close()
            self.assertEqual(ledger.get_run(run_id)["status"], "active")
            self.assertEqual(identity["stale_orchestration_runs"], 1)
            self.assertEqual(identity["unresolved_stale_orchestration_runs"], 1)
            self.assertEqual(identity["reconciled_stale_orchestration_runs"], 0)
            self.assertEqual(recovery["stale_orchestration_runs"], [run_id])
            self.assertEqual(recovery["unresolved_stale_orchestration_runs"], [run_id])
            self.assertEqual(recovery["reconciled_stale_orchestration_runs"], [])
            loaded = identity["loaded_behavior"]
            self.assertEqual(len(loaded["fingerprint"]), 64)
            self.assertEqual(
                set(loaded["components"]),
                {
                    "provider_cost_attribution",
                    "patch_preflight",
                    "verification_workdir",
                    "verification_runner",
                    "stale_reconciliation",
                    "routing_policy",
                    "external_review_policy",
                    "committed_review",
                },
            )
            self.assertEqual(ledger.reconcile_stale_runs(stale_after_seconds=3600, now=future), [run_id])
            self.assertEqual(ledger.get_run(run_id)["status"], "stale")

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
                self.assertEqual(first["source_fingerprint"], first["worktree_fp"])
                self.assertEqual(first["runtime_worktree_fingerprint"], first["worktree_fp"])
                runtime._invalidate_fast_cache()
                runtime_identity = runtime.workspace_context({"detail": "full"})["runtime"]["source"]
                self.assertTrue(runtime_identity["is_repo"])
                self.assertEqual(runtime_identity["git_head"], first["base_head"])
                self.assertEqual(runtime_identity["worktree_fp"], first["worktree_fp"])
                self.assertFalse(runtime_identity["dirty"])
                runtime_state = root / ".coding-tools" / "volatile.json"
                runtime_state.parent.mkdir(parents=True, exist_ok=True)
                runtime_state.write_text('{"tick": 1}\n', encoding="utf-8")
                second = runtime._orchestration_workspace_identity(".")
                self.assertEqual(first["worktree_fp"], second["worktree_fp"])
                self.assertEqual(first["source_fingerprint"], second["source_fingerprint"])
                self.assertNotIn(".coding-tools/volatile.json", second["dirty_paths"])
                self.assertNotIn(".coding-tools/volatile.json", second["dirty_source_paths"])
                source.write_text("VALUE = 2\n", encoding="utf-8")
                third = runtime._orchestration_workspace_identity(".")
                self.assertNotEqual(second["worktree_fp"], third["worktree_fp"])
                self.assertNotEqual(second["source_fingerprint"], third["source_fingerprint"])
                self.assertIn("app.py", third["dirty_paths"])
                self.assertIn("app.py", third["dirty_source_paths"])
            finally:
                runtime.close()


if __name__ == "__main__":
    unittest.main()
