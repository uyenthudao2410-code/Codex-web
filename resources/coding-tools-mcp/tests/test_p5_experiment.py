from __future__ import annotations

import hashlib
import subprocess
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from coding_tools_mcp.errors import ToolFailure
from coding_tools_mcp.orchestration_ledger import OrchestrationLedger
from coding_tools_mcp.p5_experiment import (
    P5_EPOCH_ACTIVE,
    P5_EPOCH_HARD_STOPPED,
    P5ExperimentError,
    analyzer_source_fingerprint,
)
from coding_tools_mcp.secret_broker import SecretBroker
from coding_tools_mcp.server import Runtime
from coding_tools_mcp.tool_schema import input_schemas


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def manifest(*, phase: str = "P5-A0", seed: str = "fixture-seed") -> dict[str, object]:
    study_type = {
        "P5-A0": "shadow_aa",
        "P5-A": "randomized_feasibility",
        "P5-B": "randomized_confirmatory",
    }[phase]
    return {
        "schema_version": 2,
        "experiment_id": f"p5-lean-causal-fix-{phase.lower()}-v1",
        "phase": phase,
        "study_type": study_type,
        "automatic_activation": False,
        "automatic_production_promotion": False,
        "control_policy": {"id": "eocl-current-control-v1"},
        "treatment_policy": {
            "id": "lean-causal-fix-gate-v1",
            "implementation_fingerprint": digest("lean-causal-fix-gate-v1"),
            "vary_only": "prewrite_causal_fix_protocol",
        },
        "source_contract": {
            "control_plane_source_head": "fixture-head",
            "upstream_identity": "fixture-upstream",
            "source_worktree_clean_required": True,
            "no_conflicting_writer_required": True,
        },
        "runtime_contract": {
            "runtime_version": "fixture-runtime",
            "runtime_policy_fp": digest("runtime-policy"),
            "tool_contract_fp": digest("tool-contract"),
            "evaluation_schema_fp": digest("evaluation-schema"),
            "public_tool_count": 8,
        },
        "environment_contract": {"environment_fp": digest("environment"), "method_version": "p5-environment-v1"},
        "common_execution_contract": {"policy_sha256": digest("common-contract")},
        "eligibility_contract": {
            "version": "p5-eligibility-v2",
            "reason_vocabulary_sha256": digest("eligibility-reasons"),
            "high_risk_exclusion_sha256": digest("high-risk-exclusion"),
        },
        "enrollment_contract": {"version": "p5-enrollment-v1", "policy_sha256": digest("enrollment-policy")},
        "assignment": {
            "randomization_unit": "stable_task_assignment",
            "unit_canonicalization_version": "p5-assignment-unit-v1",
            "algorithm": "stratified_permuted_block_v1",
            "strata": ["feature", "bugfix"],
            "block_size": 4,
            "allocation": {"control": 0.5, "treatment": 0.5},
            "seed_commitment_sha256": digest(seed),
            "restart_safe_seed_contract_sha256": digest("secret-handle-contract"),
            "never_reseed_within_epoch": True,
            "assignment_before_first_arm_action": True,
            "assignment_before_first_write": True,
        },
        "outcome_contract": {
            "horizon_seconds": 3600,
            "horizon_anchor": "assignment_at",
            "immediate_oracle_required": True,
            "intercurrent_event_matrix_sha256": digest("intercurrent-matrix"),
            "followup_interference_policy_sha256": digest("interference-policy"),
        },
        "analysis": {
            "analyzer_sha256": analyzer_source_fingerprint(),
            "intention_to_treat": True,
            "survivor_filter": False,
            "target_population_weights_sha256": digest("target-population-weights"),
        },
        "missing_data": {
            "missing_is_unknown_not_zero": True,
            "missing_quality_is_not_pass": True,
            "missing_cost_is_not_zero": True,
        },
        "stop_rule": {
            "stop_on_assignment_conflict": True,
            "stop_on_late_assignment": True,
            "stop_on_manifest_epoch_drift": True,
            "stop_on_authority_or_write_lease_violation": True,
            "stop_on_source_identity_violation": True,
            "stop_on_critical_security_or_data_loss_defect": True,
        },
    }


def candidate(index: int, *, task_class: str = "feature") -> dict[str, object]:
    return {
        "task_assignment_id": f"task-{index}",
        "repository_identity_fp": digest("repo"),
        "initial_task_spec_fp": digest(f"spec-{index}"),
        "initial_target_source_block_id": f"source-block-{index}",
        "task_class": task_class,
        "representative_natural_task": True,
        "exact_source_identity_available": True,
        "observed_oracle_available": True,
        "bounded_scope_feasible": True,
        "no_conflicting_writer_or_lease": True,
        "no_stale_or_recovery_state": True,
        "not_high_risk": True,
        "common_execution_contract_available": True,
        "controller_context_fp": digest(f"controller-{index}"),
        "isolation_status": "isolated",
    }


class P5ExperimentLedgerTests(unittest.TestCase):
    def open_epoch(self, ledger: OrchestrationLedger, *, phase: str = "P5-A0") -> tuple[dict[str, object], dict[str, object]]:
        source = manifest(phase=phase)
        opened = ledger.p5_open_epoch(
            manifest=source,
            seed_material="fixture-seed",
            seed_handle="secret://experiment/p5/a",
        )
        self.assertTrue(opened["opened"])
        return source, opened["epoch"]

    def enroll_assign(self, ledger: OrchestrationLedger, epoch: dict[str, object], source: dict[str, object], index: int) -> dict[str, object]:
        item = candidate(index)
        enrolled = ledger.p5_record_enrollment(
            activation_epoch_id=str(epoch["activation_epoch_id"]), candidate=item, enrolled=True
        )
        self.assertTrue(enrolled["recorded"])
        assigned = ledger.p5_assign(
            activation_epoch_id=str(epoch["activation_epoch_id"]),
            candidate=item,
            manifest_sha256=str(epoch["manifest_sha256"]),
            seed_material="fixture-seed",
            pre_arm_action_attested=True,
        )
        self.assertTrue(assigned["assigned"])
        return assigned["assignment"]

    def test_epoch_open_is_explicit_secret_backed_and_nonautomatic(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            template = manifest()
            template["template_only"] = True
            with self.assertRaises(P5ExperimentError):
                ledger.p5_open_epoch(
                    manifest=template,
                    seed_material="fixture-seed",
                    seed_handle="secret://experiment/p5/a",
                )
            source, epoch = self.open_epoch(ledger)
            self.assertEqual(epoch["lifecycle"], P5_EPOCH_ACTIVE)
            self.assertEqual(epoch["manifest_sha256"], hashlib.sha256(
                __import__("json").dumps(source, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest())
            event = ledger.list_events(str(epoch["ledger_run_id"]))[-1]
            self.assertEqual(event["event_type"], "p5_epoch_opened")
            self.assertNotIn("fixture-seed", str(event))
            self.assertFalse(event["payload"]["automatic_activation"])

    def test_p5_uses_existing_task_control_surface_without_a_ninth_tool(self) -> None:
        schema = input_schemas()["task_control"]
        self.assertIn("p5", schema["properties"]["action"]["enum"])
        self.assertIn("p5_experiment", schema["properties"])
        with tempfile.TemporaryDirectory() as temp, patch.dict("os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}):
            runtime = Runtime(Path(temp), permission_mode="safe")
            try:
                status = runtime.task_control({"action": "p5", "p5_experiment": {"operation": "status"}})
                self.assertIsNone(status["p5"])
                self.assertEqual(runtime.tool_contract["tool_count"], 8)
                self.assertEqual(status["p5_seed"]["seed_handle"], "secret://experiment/p5/a")
                self.assertFalse(status["p5_seed"]["available"])
                self.assertIsNone(status["p5_seed"]["seed_commitment_sha256"])
                self.assertTrue(status["p5_seed"]["content_free"])
                self.assertFalse(status["automatic_activation"])
                self.assertFalse(status["automatic_production_promotion"])
            finally:
                runtime.close()

    def test_source_contract_ignores_an_evidence_only_git_commit(self) -> None:
        with tempfile.TemporaryDirectory() as temp, patch.dict("os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}):
            root = Path(temp)
            def git(*args: str) -> str:
                return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True).stdout.strip()
            git("init")
            git("config", "user.email", "p5-test@example.invalid")
            git("config", "user.name", "P5 Test")
            (root / "source.txt").write_text("source\n", encoding="utf-8")
            git("add", "source.txt")
            git("commit", "-m", "source")
            source_commit = git("rev-parse", "HEAD")
            (root / ".coding-tools").mkdir()
            (root / ".coding-tools" / "evidence.json").write_text("{}\n", encoding="utf-8")
            git("add", ".coding-tools/evidence.json")
            git("commit", "-m", "evidence only")
            runtime = Runtime(root, permission_mode="safe")
            try:
                observed = runtime._p5_source_contract()
                self.assertEqual(observed["control_plane_source_head"], source_commit)
                self.assertEqual(observed["source_identity_scope"], "code_excluding_runtime_evidence_v1")
                self.assertTrue(observed["source_worktree_clean"])
            finally:
                runtime.close()

    def test_open_rejects_an_active_workspace_writer_when_manifest_requires_quiescence(self) -> None:
        with tempfile.TemporaryDirectory() as temp, patch.dict("os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}):
            runtime = Runtime(Path(temp), permission_mode="safe")
            try:
                observed_runtime = runtime._p5_runtime_contract()
                observed_source = {
                    "control_plane_source_head": "fixture-head",
                    "upstream_identity": "fixture-upstream",
                    "source_worktree_clean": True,
                    "head_matches_upstream": True,
                    "worktree_fp": "fixture-worktree",
                }
                frozen = manifest()
                frozen["runtime_contract"] = observed_runtime
                frozen["analysis"]["analyzer_sha256"] = observed_runtime["analyzer_sha256"]
                frozen["source_contract"]["control_plane_source_head"] = observed_source["control_plane_source_head"]
                frozen["source_contract"]["upstream_identity"] = observed_source["upstream_identity"]
                acquired = runtime.orchestration_ledger.acquire_write_fence(
                    scope_key="workspace",
                    lease_id="fixture-lease",
                    owner="fixture-owner",
                    run_id="fixture-run",
                    wave_id="fixture-wave",
                )
                self.assertTrue(acquired["acquired"])
                with patch.object(runtime, "_p5_source_contract", return_value=observed_source):
                    with self.assertRaises(ToolFailure) as denied:
                        runtime.task_control({
                            "action": "p5",
                            "p5_experiment": {"operation": "open", "manifest": frozen, "seed_handle": "secret://experiment/p5/a"},
                        })
                self.assertEqual(denied.exception.code, "P5_MANIFEST_RUNTIME_DRIFT")
                self.assertIn("active_workspace_write_fence", denied.exception.details["mismatches"])
            finally:
                runtime.close()

    def test_task_control_open_uses_the_secret_broker_and_creates_one_explicit_epoch(self) -> None:
        with tempfile.TemporaryDirectory() as temp, patch.dict("os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}):
            runtime = Runtime(
                Path(temp),
                permission_mode="safe",
                secret_broker=SecretBroker({"secret://experiment/p5/a": "fixture-seed"}),
            )
            try:
                seed_status = runtime.task_control({"action": "p5", "p5_experiment": {"operation": "status"}})["p5_seed"]
                self.assertTrue(seed_status["available"])
                self.assertEqual(seed_status["seed_commitment_sha256"], hashlib.sha256(b"fixture-seed").hexdigest())
                self.assertNotIn("fixture-seed", str(seed_status))
                observed_runtime = runtime._p5_runtime_contract()
                observed_source = {
                    "control_plane_source_head": "fixture-head",
                    "upstream_identity": "fixture-upstream",
                    "source_worktree_clean": True,
                    "head_matches_upstream": True,
                    "worktree_fp": "fixture-worktree",
                }
                frozen = manifest()
                frozen["runtime_contract"] = observed_runtime
                frozen["analysis"]["analyzer_sha256"] = observed_runtime["analyzer_sha256"]
                frozen["source_contract"]["control_plane_source_head"] = observed_source["control_plane_source_head"]
                frozen["source_contract"]["upstream_identity"] = observed_source["upstream_identity"]
                with patch.object(runtime, "_p5_source_contract", return_value=observed_source):
                    opened = runtime.task_control({
                        "action": "p5",
                        "p5_experiment": {"operation": "open", "manifest": frozen, "seed_handle": "secret://experiment/p5/a"},
                    })
                self.assertTrue(opened["p5"]["opened"])
                self.assertEqual(opened["p5"]["epoch"]["lifecycle"], P5_EPOCH_ACTIVE)
                self.assertNotIn("fixture-seed", str(opened))
            finally:
                runtime.close()

    def test_agent_workflow_records_the_p5_prewrite_binding_before_its_write_call(self) -> None:
        with tempfile.TemporaryDirectory() as temp, patch.dict("os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}):
            runtime = Runtime(
                Path(temp),
                permission_mode="safe",
                secret_broker=SecretBroker({"secret://experiment/p5/a": "fixture-seed"}),
            )
            try:
                observed_runtime = runtime._p5_runtime_contract()
                observed_source = {
                    "control_plane_source_head": "fixture-head",
                    "upstream_identity": "fixture-upstream",
                    "source_worktree_clean": True,
                    "head_matches_upstream": True,
                    "worktree_fp": "fixture-worktree",
                }
                frozen = manifest()
                frozen["runtime_contract"] = observed_runtime
                frozen["analysis"]["analyzer_sha256"] = observed_runtime["analyzer_sha256"]
                frozen["source_contract"]["control_plane_source_head"] = observed_source["control_plane_source_head"]
                frozen["source_contract"]["upstream_identity"] = observed_source["upstream_identity"]
                with patch.object(runtime, "_p5_source_contract", return_value=observed_source):
                    epoch = runtime.task_control({
                        "action": "p5",
                        "p5_experiment": {
                            "operation": "open",
                            "manifest": frozen,
                            "seed_handle": "secret://experiment/p5/a",
                        },
                    })["p5"]["epoch"]
                item = candidate(77)
                runtime.task_control({
                    "action": "p5",
                    "p5_experiment": {
                        "operation": "enroll",
                        "activation_epoch_id": epoch["activation_epoch_id"],
                        "candidate": item,
                        "enrolled": True,
                    },
                })
                assignment = runtime.task_control({
                    "action": "p5",
                    "p5_experiment": {
                        "operation": "assign",
                        "activation_epoch_id": epoch["activation_epoch_id"],
                        "candidate": item,
                        "manifest_sha256": epoch["manifest_sha256"],
                        "seed_handle": "secret://experiment/p5/a",
                        "pre_arm_action_attested": True,
                    },
                })["p5"]["assignment"]
                runtime.task_control({
                    "action": "p5",
                    "p5_experiment": {
                        "operation": "protocol_start",
                        "assignment_id": assignment["assignment_id"],
                        "received_arm": "control",
                        "protocol_id": "eocl-current-control-v1",
                    },
                })
                with patch.object(
                    runtime,
                    "apply_changes_and_verify",
                    return_value={"ok": False, "error": {"code": "TEST_STOP"}},
                ):
                    result = runtime.agent_workflow({
                        "workflow": "feature",
                        "phase": "execute",
                        "objective": "exercise P5 workflow lease binding",
                        "patches": [],
                        "evaluation": {"provenance": "synthetic"},
                        "p5_assignment_id": assignment["assignment_id"],
                    })
                self.assertFalse(result["execution"]["ok"])
                binding = result["p5_workflow_binding"]
                self.assertTrue(binding["recorded"])
                self.assertEqual(binding["assignment_id"], assignment["assignment_id"])
                snapshot = runtime.orchestration_ledger.p5_epoch_snapshot(epoch["activation_epoch_id"])
                self.assertEqual(snapshot["workflow_bindings"][0]["assignment_id"], assignment["assignment_id"])
                self.assertTrue(snapshot["workflow_bindings"][0]["write_lease_id"])
                self.assertNotIn("fixture-seed", str(result))
            finally:
                runtime.close()

    def test_assignment_requires_prior_eligible_enrollment_and_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            source, epoch = self.open_epoch(ledger)
            with self.assertRaises(P5ExperimentError):
                ledger.p5_assign(
                    activation_epoch_id=str(epoch["activation_epoch_id"]),
                    candidate=candidate(1),
                    manifest_sha256=str(epoch["manifest_sha256"]),
                    seed_material="fixture-seed",
                    pre_arm_action_attested=True,
                )
            first = self.enroll_assign(ledger, epoch, source, 1)
            replay = ledger.p5_assign(
                activation_epoch_id=str(epoch["activation_epoch_id"]),
                candidate=candidate(1),
                manifest_sha256=str(epoch["manifest_sha256"]),
                seed_material="fixture-seed",
                pre_arm_action_attested=True,
            )
            self.assertTrue(replay["idempotent"])
            self.assertEqual(replay["assignment"]["assignment_id"], first["assignment_id"])
            events = ledger.list_events(str(epoch["ledger_run_id"]))
            self.assertLess(
                next(item["seq"] for item in events if item["event_type"] == "p5_enrollment_decision_recorded"),
                next(item["seq"] for item in events if item["event_type"] == "p5_assignment_recorded"),
            )

    def test_parallel_assignments_consume_distinct_atomic_block_slots(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            source, epoch = self.open_epoch(ledger, phase="P5-A")
            barrier = threading.Barrier(4)
            def enroll_then_assign(index: int) -> dict[str, object]:
                item = candidate(index)
                ledger.p5_record_enrollment(activation_epoch_id=str(epoch["activation_epoch_id"]), candidate=item, enrolled=True)
                barrier.wait(timeout=5)
                return ledger.p5_assign(
                    activation_epoch_id=str(epoch["activation_epoch_id"]),
                    candidate=item,
                    manifest_sha256=str(epoch["manifest_sha256"]),
                    seed_material="fixture-seed",
                    pre_arm_action_attested=True,
                )["assignment"]
            with ThreadPoolExecutor(max_workers=4) as pool:
                assignments = list(pool.map(enroll_then_assign, range(4)))
            slots = {(item["block_id"], item["block_slot"]) for item in assignments}
            self.assertEqual(slots, {(0, 0), (0, 1), (0, 2), (0, 3)})
            self.assertEqual(sorted(item["assigned_arm"] for item in assignments), ["control", "control", "treatment", "treatment"])
            self.assertEqual(ledger.verify_chain(str(epoch["ledger_run_id"]))["ok"], True)

    def test_aa_receives_control_and_outcome_stays_in_itt(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            source, epoch = self.open_epoch(ledger)
            assignment = self.enroll_assign(ledger, epoch, source, 1)
            protocol = ledger.p5_record_arm_protocol_start(
                assignment_id=str(assignment["assignment_id"]),
                received_arm="control",
                protocol_id="eocl-current-control-v1",
            )
            self.assertTrue(protocol["recorded"])
            with self.assertRaises(P5ExperimentError):
                ledger.p5_bind_workflow_prewrite(
                    assignment_id=str(assignment["assignment_id"]),
                    workflow="bugfix",
                    run_id="p5-test-run",
                    wave_id="p5-test-wave",
                    write_lease_id="p5-test-lease",
                )
            binding = ledger.p5_bind_workflow_prewrite(
                assignment_id=str(assignment["assignment_id"]),
                workflow="feature",
                run_id="p5-test-run",
                wave_id="p5-test-wave",
                write_lease_id="p5-test-lease",
            )
            self.assertTrue(binding["recorded"])
            snapshot = ledger.p5_epoch_snapshot(str(epoch["activation_epoch_id"]))
            self.assertEqual(snapshot["workflow_bindings"][0]["assignment_id"], assignment["assignment_id"])
            self.assertEqual(snapshot["workflow_bindings"][0]["workflow"], "feature")
            outcome = ledger.p5_record_outcome(
                assignment_id=str(assignment["assignment_id"]),
                outcome={
                    "terminal_status": "accepted",
                    "qualifying_acceptance_at": datetime.now(timezone.utc).isoformat(),
                    "post_assignment_replan_count": 0,
                    "immediate_oracle_pass": True,
                    "immediate_proof_observed": True,
                    "immediate_quality_status": "pass",
                    "quality_followup_interference": "none",
                    "adherence_status": "adherent",
                },
            )
            self.assertTrue(outcome["recorded"])
            report = ledger.p5_analyze_epoch(str(epoch["activation_epoch_id"]))
            self.assertEqual(report["efficacy_decision"], "NOT_EVALUATED")
            self.assertEqual(report["assignment"]["assigned_rows"][0]["received_arm"], "control")
            self.assertTrue(report["assignment"]["assigned_rows"][0]["in_intention_to_treat"])
            self.assertEqual(report["funnel"]["assigned"], 1)

    def test_protocol_cannot_claim_a_first_write_without_a_bound_workflow_lease(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            source, epoch = self.open_epoch(ledger)
            assignment = self.enroll_assign(ledger, epoch, source, 1)
            with self.assertRaises(P5ExperimentError):
                ledger.p5_record_arm_protocol_start(
                    assignment_id=str(assignment["assignment_id"]),
                    received_arm="control",
                    protocol_id="eocl-current-control-v1",
                    first_write_at=datetime.now(timezone.utc).isoformat(),
                )
            protocol = ledger.p5_record_arm_protocol_start(
                assignment_id=str(assignment["assignment_id"]),
                received_arm="control",
                protocol_id="eocl-current-control-v1",
            )
            self.assertTrue(protocol["recorded"])
            binding = ledger.p5_bind_workflow_prewrite(
                assignment_id=str(assignment["assignment_id"]),
                workflow="feature",
                run_id="p5-bound-run",
                wave_id="p5-bound-wave",
                write_lease_id="p5-bound-lease",
            )
            self.assertTrue(binding["recorded"])
            replay = ledger.p5_bind_workflow_prewrite(
                assignment_id=str(assignment["assignment_id"]),
                workflow="feature",
                run_id="p5-bound-run",
                wave_id="p5-bound-wave",
                write_lease_id="p5-bound-lease",
            )
            self.assertTrue(replay["idempotent"])
            events = ledger.list_events(str(epoch["ledger_run_id"]))
            self.assertLess(
                next(item["seq"] for item in events if item["event_type"] == "p5_arm_protocol_started"),
                next(item["seq"] for item in events if item["event_type"] == "p5_workflow_prewrite_bound"),
            )

    def test_closed_epoch_rejects_assignment_and_critical_outcome_hard_stops(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            source, epoch = self.open_epoch(ledger, phase="P5-A")
            assignment = self.enroll_assign(ledger, epoch, source, 1)
            ledger.p5_record_arm_protocol_start(
                assignment_id=str(assignment["assignment_id"]),
                received_arm=str(assignment["assigned_arm"]),
                protocol_id="lean-causal-fix-gate-v1" if assignment["assigned_arm"] == "treatment" else "eocl-current-control-v1",
            )
            outcome = ledger.p5_record_outcome(
                assignment_id=str(assignment["assignment_id"]),
                outcome={"terminal_status": "failed", "critical_security_or_data_loss": True},
            )
            self.assertTrue(outcome["hard_stopped"])
            snapshot = ledger.p5_epoch_snapshot(str(epoch["activation_epoch_id"]))
            self.assertEqual(snapshot["epoch"]["lifecycle"], P5_EPOCH_HARD_STOPPED)
            with self.assertRaises(P5ExperimentError):
                ledger.p5_record_enrollment(
                    activation_epoch_id=str(epoch["activation_epoch_id"]), candidate=candidate(2), enrolled=True
                )


if __name__ == "__main__":
    unittest.main()
