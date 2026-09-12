from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SOURCE_ROOT = Path(__file__).resolve().parents[1]
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from coding_tools_mcp.errors import ToolFailure
from coding_tools_mcp.prepared_workflow_binding import validate_prepared_workflow_binding
from coding_tools_mcp.server import Runtime
from coding_tools_mcp.tool_schema import input_schemas, validate_arguments


class OrchestrationWorkflowIntegrationTests(unittest.TestCase):
    def test_prepare_execute_exact_binding_reuses_one_run_for_refined_objective(self) -> None:
        with tempfile.TemporaryDirectory() as temp, patch.dict(
            "os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}
        ):
            root = Path(temp)
            target = root / "app.py"
            target.write_text("VALUE = 1\n", encoding="utf-8")
            runtime = Runtime(root, permission_mode="dangerous")
            try:
                prepared = runtime.agent_workflow({
                    "workflow": "bugfix",
                    "phase": "prepare",
                    "objective": "investigate the exact value defect",
                    "queries": ["VALUE"],
                    "evaluation": {"provenance": "synthetic"},
                })
                binding = prepared["prepared_binding"]
                self.assertEqual(binding["run_id"], prepared["orchestration"]["run_id"])
                self.assertEqual(binding["wave_id"], prepared["orchestration"]["wave_id"])
                self.assertIn("run_id", input_schemas()["agent_workflow"]["properties"])
                self.assertIn("wave_id", input_schemas()["agent_workflow"]["properties"])

                execute_args = {
                    "workflow": "bugfix",
                    "phase": "execute",
                    "objective": "set the proven value to two",
                    "run_id": binding["run_id"],
                    "wave_id": binding["wave_id"],
                    "execution_route": "deterministic",
                    "patch": "*** Begin Patch\n*** Update File: app.py\n@@\n-VALUE = 1\n+VALUE = 2\n*** End Patch",
                    "verification": "none",
                    "evaluation": {"provenance": "synthetic"},
                }
                validate_arguments("agent_workflow", execute_args)
                executed = runtime.call_tool("agent_workflow", execute_args)["structuredContent"]

                self.assertEqual(executed["orchestration"]["run_id"], binding["run_id"])
                self.assertEqual(executed["orchestration"]["wave_id"], binding["wave_id"])
                self.assertEqual(len(runtime.orchestration_ledger.list_runs(limit=10)), 1)
                self.assertEqual(target.read_text(encoding="utf-8"), "VALUE = 2\n")
            finally:
                runtime.close()

    def test_prepare_execute_refined_objective_without_binding_fails_before_rebind(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "app.py"
            target.write_text("VALUE = 1\n", encoding="utf-8")
            runtime = Runtime(root, permission_mode="dangerous")
            try:
                prepared = runtime.agent_workflow({
                    "workflow": "bugfix",
                    "phase": "prepare",
                    "objective": "investigate the exact value defect",
                    "queries": ["VALUE"],
                    "evaluation": {"provenance": "synthetic"},
                })
                with self.assertRaises(ToolFailure) as caught:
                    runtime.agent_workflow({
                        "workflow": "bugfix",
                        "phase": "execute",
                        "objective": "set the proven value to two",
                        "execution_route": "deterministic",
                        "patch": "*** Begin Patch\n*** Update File: app.py\n@@\n-VALUE = 1\n+VALUE = 2\n*** End Patch",
                        "verification": "none",
                        "evaluation": {"provenance": "synthetic"},
                    })
                self.assertEqual(caught.exception.code, "PREPARED_RUN_BINDING_REQUIRED")
                self.assertEqual(caught.exception.details, prepared["prepared_binding"])
                self.assertEqual(len(runtime.orchestration_ledger.list_runs(limit=10)), 1)
                self.assertEqual(target.read_text(encoding="utf-8"), "VALUE = 1\n")
            finally:
                runtime.close()

    def test_prepare_execute_wrong_exact_binding_fails_before_new_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
            runtime = Runtime(root, permission_mode="dangerous")
            try:
                prepared = runtime.agent_workflow({
                    "workflow": "bugfix",
                    "phase": "prepare",
                    "objective": "investigate the exact value defect",
                    "queries": ["VALUE"],
                    "evaluation": {"provenance": "synthetic"},
                })
                with self.assertRaises(ToolFailure) as caught:
                    runtime.agent_workflow({
                        "workflow": "bugfix",
                        "phase": "execute",
                        "objective": "set the proven value to two",
                        "run_id": prepared["prepared_binding"]["run_id"],
                        "wave_id": "wrong-wave",
                        "execution_route": "deterministic",
                        "patch": "*** Begin Patch\n*** Update File: app.py\n@@\n-VALUE = 1\n+VALUE = 2\n*** End Patch",
                        "verification": "none",
                        "evaluation": {"provenance": "synthetic"},
                    })
                self.assertEqual(caught.exception.code, "PREPARED_RUN_BINDING_MISMATCH")
                self.assertEqual(len(runtime.orchestration_ledger.list_runs(limit=10)), 1)
            finally:
                runtime.close()

    def test_prepared_binding_requires_a_pair_and_execute_phase(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp), permission_mode="dangerous")
            try:
                with self.assertRaises(ToolFailure) as incomplete:
                    runtime.agent_workflow({
                        "workflow": "bugfix",
                        "phase": "execute",
                        "run_id": "prepared-run",
                    })
                self.assertEqual(incomplete.exception.code, "PREPARED_RUN_BINDING_INCOMPLETE")

                with self.assertRaises(ToolFailure) as wrong_phase:
                    runtime.agent_workflow({
                        "workflow": "bugfix",
                        "phase": "run",
                        "run_id": "prepared-run",
                        "wave_id": "prepared-wave",
                    })
                self.assertEqual(wrong_phase.exception.code, "PREPARED_RUN_BINDING_PHASE_INVALID")
                self.assertEqual(runtime.orchestration_ledger.list_runs(limit=10), [])
            finally:
                runtime.close()

    def test_prepared_binding_requires_canonical_exact_wave_prepare_evidence(self) -> None:
        class LedgerWithoutPrepare:
            @staticmethod
            def list_events(run_id: str, *, wave_id: str) -> list[dict[str, str]]:
                self.assertEqual(run_id, "prepared-run")
                self.assertEqual(wave_id, "prepared-wave")
                return []

        current_ctx = type(
            "PreparedContext",
            (),
            {"run_id": "prepared-run", "wave_id": "prepared-wave", "state": "PREFLIGHT"},
        )()
        with self.assertRaises(ToolFailure) as caught:
            validate_prepared_workflow_binding(
                {
                    "workflow": "bugfix",
                    "phase": "execute",
                    "run_id": "prepared-run",
                    "wave_id": "prepared-wave",
                },
                current_task={"task_id": "task-1"},
                projection={"run_id": "prepared-run", "wave_id": "prepared-wave"},
                current_ctx=current_ctx,
                current_run={
                    "task_id": "task-1",
                    "metadata": {"workflow": "bugfix", "phase": "prepare"},
                },
                ledger=LedgerWithoutPrepare(),
            )
        self.assertEqual(caught.exception.code, "PREPARED_RUN_BINDING_MISMATCH")
        self.assertFalse(caught.exception.details["exact_wave_context_prepared"])

    def test_replanned_run_prepare_execute_binding_uses_exact_wave_prepare_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "app.py"
            target.write_text("VALUE = 1\n", encoding="utf-8")
            runtime = Runtime(root, permission_mode="dangerous")
            try:
                blocked = runtime.agent_workflow({
                    "workflow": "bugfix",
                    "phase": "run",
                    "objective": "change value with unavailable coordination",
                    "execution_mode": "coordinated_multi_worktree",
                    "evaluation": {"provenance": "synthetic"},
                    "verification": "none",
                })
                self.assertEqual(blocked["orchestration"]["orchestration_state"], "REPLAN")
                run_id = blocked["orchestration"]["run_id"]
                self.assertEqual(runtime.orchestration_ledger.get_run(run_id)["metadata"]["phase"], "run")

                report_id = runtime.task_state.pending_completion_report()["report_id"]
                acknowledged = runtime.task_control({
                    "action": "update",
                    "payload": {"extension": "operator_report_ack_v1", "report_id": report_id},
                })
                self.assertTrue(acknowledged["acknowledged"])

                prepared = runtime.agent_workflow({
                    "workflow": "bugfix",
                    "phase": "prepare",
                    "objective": "prepare deterministic value repair",
                    "execution_mode": "mcp_only",
                    "replan_reason": "coordination is unavailable; prepare the deterministic repair",
                    "queries": ["VALUE"],
                    "evaluation": {"provenance": "synthetic"},
                })
                binding = prepared["prepared_binding"]
                self.assertEqual(binding["run_id"], run_id)
                self.assertEqual(runtime.orchestration_ledger.get_run(run_id)["metadata"]["phase"], "run")
                events = runtime.orchestration_ledger.list_events(run_id, wave_id=binding["wave_id"])
                self.assertTrue(any(item["event_type"] == "context_prepared" for item in events))

                executed = runtime.agent_workflow({
                    "workflow": "bugfix",
                    "phase": "execute",
                    "objective": "apply deterministic value repair",
                    "run_id": binding["run_id"],
                    "wave_id": binding["wave_id"],
                    "execution_mode": "mcp_only",
                    "execution_route": "deterministic",
                    "patch": "*** Begin Patch\n*** Update File: app.py\n@@\n-VALUE = 1\n+VALUE = 2\n*** End Patch",
                    "verification": "none",
                    "evaluation": {"provenance": "synthetic"},
                })
                self.assertEqual(executed["orchestration"]["run_id"], run_id)
                self.assertEqual(executed["orchestration"]["wave_id"], binding["wave_id"])
                self.assertEqual(target.read_text(encoding="utf-8"), "VALUE = 2\n")
            finally:
                runtime.close()

    def test_runtime_records_content_free_a2_stage_spans_without_new_contract_surface(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
            runtime = Runtime(root, permission_mode="dangerous")
            try:
                result = runtime.agent_workflow({
                    "workflow": "bugfix",
                    "phase": "run",
                    "objective": "change value",
                    "evaluation": {"provenance": "benchmark"},
                    "patch": "*** Begin Patch\n*** Update File: app.py\n@@\n-VALUE = 1\n+VALUE = 2\n*** End Patch",
                    "verification": "none",
                    "include_diff": False,
                })
                run_id = result["orchestration"]["run_id"]
                wave_id = result["orchestration"]["wave_id"]
                before_acceptance = runtime.orchestration_ledger.list_observation_spans(run_id)
                by_stage = {str(item["stage"]): item for item in before_acceptance}
                self.assertEqual(set(by_stage), {"preflight", "localization", "routing", "execution", "proof"})
                self.assertTrue(all(item["source"] == "coding_mcp_runtime" for item in by_stage.values()))
                self.assertTrue(all(item["measurement"] == "observed_stage_duration" for item in by_stage.values()))
                self.assertEqual(len({item["clock_domain"] for item in by_stage.values()}), 1)
                self.assertTrue(all(float(item["duration_ms"]) >= 0 for item in by_stage.values()))
                self.assertTrue(all("turn_id" not in item and "trace_id" not in item for item in by_stage.values()))

                runtime.orchestration_ledger.record_proof(
                    run_id=run_id,
                    wave_id=wave_id,
                    stage_id="a2-stage-span-fixture",
                    stage_version="1",
                    input_fingerprint="a2-stage-span-fixture-proof",
                    status="passed",
                )
                accepted = runtime.task_control({
                    "action": "accept",
                    "run_id": run_id,
                    "reason": "accept stage-observation regression fixture",
                })
                self.assertTrue(accepted["accepted"])
                final_spans = runtime.orchestration_ledger.list_observation_spans(run_id)
                acceptance = [item for item in final_spans if item.get("stage") == "acceptance"]
                self.assertEqual(len(acceptance), 1)
                self.assertEqual(acceptance[0]["span_id"], f"a2-runtime-stage-v1:{wave_id}:acceptance")
            finally:
                runtime.close()

    def test_coordination_unavailable_forces_replan_and_explicit_new_wave(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
            runtime = Runtime(root, permission_mode="dangerous")
            blocked = runtime.agent_workflow({
                "workflow": "feature",
                "phase": "run",
                "objective": "change value",
                "execution_mode": "coordinated_multi_worktree",
                "evaluation": {"provenance": "benchmark"},
                "verification": "none",
            })
            self.assertEqual(blocked["orchestration"]["orchestration_state"], "REPLAN")
            self.assertEqual(blocked["execution"]["reason"], "SUPERVISOR_NOT_READY")

            with self.assertRaises(ToolFailure) as pending_report:
                runtime.agent_workflow({
                    "workflow": "feature",
                    "phase": "execute",
                    "objective": "change value",
                    "execution_mode": "mcp_only",
                    "patch": "*** Begin Patch\n*** Update File: app.py\n@@\n-VALUE = 1\n+VALUE = 2\n*** End Patch",
                    "verification": "none",
                })
            self.assertEqual(pending_report.exception.code, "OPERATOR_REPORT_ACK_REQUIRED")
            report_id = runtime.task_state.pending_completion_report()["report_id"]
            acknowledged = runtime.task_control({
                "action": "update",
                "payload": {"extension": "operator_report_ack_v1", "report_id": report_id},
            })
            self.assertTrue(acknowledged["acknowledged"])

            with self.assertRaises(ToolFailure) as missing_reason:
                runtime.agent_workflow({
                    "workflow": "feature",
                    "phase": "execute",
                    "objective": "change value",
                    "execution_mode": "mcp_only",
                    "patch": "*** Begin Patch\n*** Update File: app.py\n@@\n-VALUE = 1\n+VALUE = 2\n*** End Patch",
                    "verification": "none",
                })
            self.assertEqual(missing_reason.exception.code, "REPLAN_REASON_REQUIRED")

            result = runtime.agent_workflow({
                "workflow": "feature",
                "phase": "execute",
                "objective": "change value with deterministic writer",
                "execution_mode": "mcp_only",
                "replan_reason": "coordination adapter is unavailable; use one deterministic writer",
                "patch": "*** Begin Patch\n*** Update File: app.py\n@@\n-VALUE = 1\n+VALUE = 2\n*** End Patch",
                "verification": "none",
                "include_diff": False,
            })
            self.assertEqual(result["orchestration"]["orchestration_state"], "ACCEPTING")
            waves = runtime.orchestration_ledger.list_waves(result["orchestration"]["run_id"])
            self.assertEqual(waves[0]["metadata"]["effective_objective"], "change value")
            self.assertEqual(waves[0]["metadata"]["objective_revision"], 1)
            self.assertEqual(waves[1]["metadata"]["effective_objective"], "change value with deterministic writer")
            self.assertEqual(waves[1]["metadata"]["objective_revision"], 2)
            accepting_report = result["orchestration"]["completion_report"]
            self.assertTrue(accepting_report["operator_visible_required"])
            self.assertEqual(accepting_report["accepted_or_not"], "PENDING_FINAL_ACCEPTANCE")
            self.assertEqual(
                accepting_report["source_run_wave"]["objective_provenance"]["effective_objective"],
                "change value with deterministic writer",
            )
            self.assertEqual(accepting_report["source_run_wave"]["objective_provenance"]["objective_revision"], 2)
            self.assertEqual(accepting_report["report_contract"], [
                "WHAT CHANGED", "CURRENT STATE", "SOURCE / RUN / WAVE ID", "PROOF ACTUALLY RUN",
                "ACCEPTED OR NOT", "WHAT REMAINS", "NEXT CRITICAL ACTION",
            ])
            audit = runtime.task_control({"action": "audit", "run_id": result["orchestration"]["run_id"], "limit": 100})
            self.assertEqual(audit["completion_report"]["accepted_or_not"], "PENDING_FINAL_ACCEPTANCE")
            self.assertEqual(len(audit["audit"]["waves"]), 2)
            self.assertTrue(audit["audit"]["integrity"]["ok"])
            self.assertEqual(audit["orchestration"]["wave_id"], result["orchestration"]["wave_id"])
            self.assertEqual(audit["orchestration"]["orchestration_state"], "ACCEPTING")
            filtered = runtime.task_control({
                "action": "audit",
                "run_id": result["orchestration"]["run_id"],
                "wave_id": result["orchestration"]["wave_id"],
                "limit": 5,
            })
            self.assertEqual(filtered["audit"]["query"]["wave_id"], result["orchestration"]["wave_id"])
            self.assertEqual([item["wave_id"] for item in filtered["audit"]["waves"]], [result["orchestration"]["wave_id"]])
            self.assertTrue(filtered["audit"]["model_free"])
            self.assertFalse(filtered["audit"]["raw_transcript_included"])
            runtime.orchestration_ledger.record_proof(
                run_id=result["orchestration"]["run_id"],
                wave_id=result["orchestration"]["wave_id"],
                stage_id="replanned-wave-fixture",
                stage_version="1",
                input_fingerprint="replanned-wave-fixture-proof",
                status="passed",
            )
            accepted = runtime.task_control({
                "action": "accept",
                "run_id": result["orchestration"]["run_id"],
                "reason": "regression test accepts the proven replacement wave",
            })
            self.assertTrue(accepted["accepted"])
            self.assertEqual(accepted["orchestration"]["wave_id"], result["orchestration"]["wave_id"])
            self.assertEqual(accepted["orchestration"]["orchestration_state"], "CHECKPOINTED")
            self.assertEqual(accepted["completion_report"]["accepted_or_not"], "ACCEPTED")
            self.assertTrue(accepted["completion_report"]["operator_visible_required"])
            self.assertIn("before starting another material wave", accepted["completion_report"]["next_critical_action"])
            runtime.close()

    def test_reject_requires_reason_and_keeps_same_run_in_replan(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
            runtime = Runtime(root, permission_mode="dangerous")
            result = runtime.agent_workflow({
                "workflow": "bugfix",
                "phase": "execute",
                "objective": "change value",
                "evaluation": {"provenance": "benchmark"},
                "patch": "*** Begin Patch\n*** Update File: app.py\n@@\n-VALUE = 1\n+VALUE = 2\n*** End Patch",
                "verification": "none",
                "include_diff": False,
            })
            run_id = result["orchestration"]["run_id"]
            with self.assertRaises(ToolFailure) as missing_reason:
                runtime.task_control({"action": "reject", "run_id": run_id})
            self.assertEqual(missing_reason.exception.code, "REJECTION_REASON_REQUIRED")
            rejected = runtime.task_control({"action": "reject", "run_id": run_id, "reason": "adjacent invariant still under-proven"})
            self.assertTrue(rejected["rejected"])
            self.assertEqual(rejected["orchestration"]["orchestration_state"], "REPLAN")
            self.assertEqual(rejected["orchestration"]["run_id"], run_id)
            self.assertEqual(rejected["completion_report"]["accepted_or_not"], "NOT_ACCEPTED_REPLAN_REQUIRED")
            self.assertEqual(rejected["completion_report"]["blocker_or_failure"]["failure_class"], "SOL_REJECTED")
            self.assertTrue(rejected["completion_report"]["operator_visible_required"])
            runtime.close()

    def test_reconnect_repairs_acceptance_projection_from_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
            runtime = Runtime(root, permission_mode="dangerous")
            result = runtime.agent_workflow({
                "workflow": "bugfix",
                "phase": "execute",
                "objective": "change value",
                "evaluation": {"provenance": "benchmark"},
                "patch": "*** Begin Patch\n*** Update File: app.py\n@@\n-VALUE = 1\n+VALUE = 2\n*** End Patch",
                "verification": "none",
                "include_diff": False,
            })
            self.assertEqual(result["orchestration"]["orchestration_state"], "ACCEPTING")
            runtime.task_state.update({
                "status": "waiting",
                "current_step": "Waiting for model",
                "next_step": "Wait for the old response stream.",
            })
            runtime.close()

            recovered = Runtime(root, permission_mode="dangerous")
            try:
                self.assertTrue(recovered.reconciled_task_orchestration)
                state = recovered.task_state.get()
                self.assertEqual(state["orchestration"]["orchestration_state"], "ACCEPTING")
                self.assertEqual(state["current_step"], "Awaiting acceptance")
                self.assertIn("task_control action=accept or reject", state["next_step"])
            finally:
                recovered.close()


if __name__ == "__main__":
    unittest.main()
