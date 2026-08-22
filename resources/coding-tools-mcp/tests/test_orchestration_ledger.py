from __future__ import annotations

import json
import tempfile
import unittest
import zlib
from pathlib import Path

from coding_tools_mcp.orchestration_ledger import OrchestrationLedger


class OrchestrationLedgerTests(unittest.TestCase):
    def test_proof_cache_opportunity_summary_is_content_free_and_acceptance_aware(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            accepted = ledger.create_run(objective="accepted cache opportunity")
            accepted_wave = ledger.create_wave(accepted, execution_mode="mcp_only")
            ledger.append_event(
                accepted,
                wave_id=accepted_wave,
                event_type="proof_cache_miss",
                payload={
                    "stage_id": "verify:tests",
                    "stage_version": "1",
                    "input_fingerprint": "secret-fingerprint-cold",
                    "reason": "cold",
                },
            )
            source_proof = ledger.record_proof(
                run_id=accepted,
                wave_id=accepted_wave,
                stage_id="verify:tests",
                stage_version="1",
                input_fingerprint="secret-fingerprint-cold",
                status="passed",
                duration_ms=125,
            )
            ledger.append_event(
                accepted,
                wave_id=accepted_wave,
                event_type="proof_cache_hit",
                payload={
                    "stage_id": "verify:tests",
                    "stage_version": "1",
                    "input_fingerprint": "secret-fingerprint-cold",
                    "source_proof_id": source_proof,
                },
            )
            ledger.record_checkpoint(
                run_id=accepted,
                wave_id=accepted_wave,
                git_head="head",
                proof_fingerprint="proof",
                status="accepted",
            )
            ledger.finish_wave(accepted_wave, status="accepted")
            ledger.finish_run(accepted, status="accepted")

            active = ledger.create_run(objective="unaccepted cache opportunity")
            active_wave = ledger.create_wave(active, execution_mode="mcp_only")
            ledger.append_event(
                active,
                wave_id=active_wave,
                event_type="proof_cache_miss",
                payload={
                    "stage_id": "verify:tests",
                    "stage_version": "2",
                    "input_fingerprint": "secret-fingerprint-changed",
                    "reason": "input_fingerprint_changed",
                },
            )
            ledger.append_event(
                active,
                wave_id=active_wave,
                event_type="proof_cache_hit",
                payload={
                    "stage_id": "verify:tests",
                    "stage_version": "2",
                    "input_fingerprint": "secret-fingerprint-missing-source",
                    "source_proof_id": "missing-source-proof",
                },
            )

            summary = ledger.proof_cache_opportunity_summary()
            self.assertEqual((summary["eligible"], summary["hits"], summary["misses"]), (4, 2, 2))
            self.assertEqual(summary["hit_rate"], 0.5)
            self.assertEqual(summary["miss_reasons"], {"cold": 1, "input_fingerprint_changed": 1})
            self.assertEqual(summary["fingerprint_classes"]["exact_reuse"], 2)
            self.assertEqual(summary["fingerprint_classes"]["cold"], 1)
            self.assertEqual(summary["fingerprint_classes"]["input_fingerprint_changed"], 1)
            self.assertEqual(summary["saved_ms_known"], 125)
            self.assertEqual(summary["saved_ms_known_hits"], 1)
            self.assertFalse(summary["saved_ms_complete"])
            self.assertIsNone(summary["saved_ms"])
            self.assertEqual(summary["run_relation"]["runs_with_opportunities"], 2)
            self.assertEqual(summary["run_relation"]["accepted_runs_with_opportunities"], 1)
            self.assertEqual(summary["run_relation"]["accepted_checkpoint_runs_with_opportunities"], 1)
            self.assertEqual(summary["run_relation"]["accepted_run_opportunities"], 2)
            self.assertEqual(summary["run_relation"]["accepted_run_hits"], 1)
            self.assertEqual(summary["run_relation"]["unaccepted_run_opportunities"], 2)
            self.assertEqual(len(summary["stages"]), 2)
            self.assertEqual({item["stage_version"] for item in summary["stages"]}, {"1", "2"})
            serialized = json.dumps(summary, ensure_ascii=False)
            self.assertNotIn("secret-fingerprint", serialized)
            self.assertNotIn(source_proof, serialized)
            self.assertTrue(summary["model_free"])
            self.assertTrue(summary["content_free"])
            self.assertFalse(summary["raw_input_fingerprints_included"])

    def test_accepted_result_evaluation_keeps_unobserved_controller_cost_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(
                objective="representative paired task",
                task_id="task-eval",
                metadata={
                    "workflow": "bugfix",
                    "evaluation": {
                        "pair_id": "pair-1",
                        "policy": "chatweb_mcp",
                        "task_class": "localized_bug",
                        "oracle_id": "oracle-1",
                        "provenance": "representative",
                        "task_spec_fp": "task-spec-1",
                        "environment_fp": "env-1",
                        "tool_contract_fp": "tool-1",
                        "evaluation_schema_fp": "eval-1",
                        "runtime_version": "0.4.3",
                        "cache_stratum": "cold",
                    },
                },
            )
            wave_id = ledger.create_wave(
                run_id,
                execution_mode="mcp_only",
                base_head="head-1",
                worktree_fp="tree-1",
                contract_fp="contract-1",
            )
            ledger.append_event(run_id, wave_id=wave_id, event_type="route_selected", state_after="READY", payload={"requested": "deterministic", "resolved": "deterministic"})
            ledger.append_event(run_id, wave_id=wave_id, event_type="write_lease_acquired", state_after="ROUTED")
            ledger.record_proof(run_id=run_id, wave_id=wave_id, stage_id="tests", stage_version="1", input_fingerprint="proof-1", status="passed", duration_ms=125)
            ledger.record_checkpoint(run_id=run_id, wave_id=wave_id, git_head="head-1", proof_fingerprint="proof-1", metadata={"accepted_by": "chatweb"})
            ledger.finish_wave(wave_id, status="accepted")
            ledger.finish_run(run_id, status="accepted")

            record = ledger.accepted_result_evaluation(run_id)
            self.assertTrue(record["accepted"])
            self.assertTrue(record["pairing_eligible"])
            self.assertEqual(record["evaluation"]["task_class"], "localized_bug")
            self.assertEqual(record["source"]["base_head"], "head-1")
            self.assertIsNotNone(record["milestones"]["time_to_first_route_ms"])
            self.assertIsNotNone(record["milestones"]["time_to_first_write_ms"])
            self.assertIsNotNone(record["milestones"]["time_to_first_green_ms"])
            self.assertIsNotNone(record["milestones"]["time_to_accepted_ms"])
            self.assertEqual(record["mcp"]["proof_duration_ms"], 125)
            self.assertEqual(record["controller"]["measurement"], "unobserved_outside_mcp")
            self.assertIsNone(record["controller"]["pre_mcp_ms"])
            self.assertIsNone(record["controller"]["monetary_cost"])
            self.assertFalse(record["total_monetary_cost"]["complete"])
            self.assertEqual(record["total_monetary_cost"]["reason"], "controller_cost_unobserved")

    def test_paired_policy_evaluation_is_fail_closed_without_total_controller_cost(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))

            def accepted(policy: str, route: str) -> str:
                run_id = ledger.create_run(
                    objective="same representative task",
                    metadata={
                        "workflow": "bugfix",
                        "evaluation": {
                            "pair_id": "pair-roi-1",
                            "policy": policy,
                            "task_class": "localized_bug",
                            "oracle_id": "oracle-roi-1",
                            "provenance": "representative",
                            "task_spec_fp": "task-roi-1",
                            "environment_fp": "env-roi-1",
                            "tool_contract_fp": "tool-roi-1",
                            "evaluation_schema_fp": "eval-roi-1",
                            "runtime_version": "0.4.3",
                            "cache_stratum": "cold",
                        },
                    },
                )
                mode = "mcp_only" if route == "deterministic" else "bounded_candidate"
                wave_id = ledger.create_wave(
                    run_id,
                    execution_mode=mode,
                    base_head="same-head",
                    worktree_fp="same-tree",
                    contract_fp="same-contract",
                )
                ledger.append_event(run_id, wave_id=wave_id, event_type="route_selected", state_after="READY", payload={"requested": route, "resolved": route})
                ledger.record_proof(run_id=run_id, wave_id=wave_id, stage_id="tests", stage_version="1", input_fingerprint=f"proof-{policy}", status="passed", duration_ms=10)
                ledger.record_checkpoint(run_id=run_id, wave_id=wave_id, git_head="same-head", proof_fingerprint=f"proof-{policy}", metadata={"accepted_by": "chatweb"})
                ledger.finish_wave(wave_id, status="accepted")
                ledger.finish_run(run_id, status="accepted")
                return run_id

            accepted("chatweb_mcp", "deterministic")
            accepted("mini", "mini")
            comparison = ledger.paired_policy_evaluation(candidate_policies=("mini",), min_pairs=1, min_task_classes=1)
            result = comparison["results"][0]
            self.assertEqual(result["pair_count"], 1)
            self.assertEqual(result["accepted_pair_count"], 1)
            self.assertEqual(result["status"], "hold")
            self.assertIn("controller_cost_unobserved", result["hold_reasons"])
            self.assertEqual(result["pareto_status"], "indeterminate_total_cost")
            regret = result["routing_placement_regret"]
            self.assertEqual(regret["status"], "hold")
            self.assertEqual(regret["measurement_status"], "incomplete")
            self.assertIn("outcome_incomplete", regret["hold_reasons"])
            self.assertEqual(regret["predicted_policy_score"]["coverage"], 0.0)
            self.assertIsNone(regret["scalar_regret"]["value"])
            self.assertFalse(result["automatic_activation"])

    def test_paired_policy_evaluation_scans_beyond_history_ui_cap(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))

            def tagged(policy: str) -> None:
                run_id = ledger.create_run(
                    objective="older representative pair",
                    metadata={
                        "workflow": "bugfix",
                        "evaluation": {
                            "pair_id": "older-pair",
                            "policy": policy,
                            "task_class": "localized_bug",
                            "oracle_id": "older-oracle",
                            "provenance": "representative",
                            "task_spec_fp": "older-task",
                            "environment_fp": "older-env",
                            "tool_contract_fp": "older-tool",
                            "evaluation_schema_fp": "older-eval",
                            "runtime_version": "0.4.3",
                            "cache_stratum": "cold",
                        },
                    },
                )
                wave_id = ledger.create_wave(
                    run_id,
                    execution_mode="mcp_only",
                    base_head="older-head",
                    worktree_fp="older-tree",
                    contract_fp="older-contract",
                )
                ledger.record_checkpoint(run_id=run_id, wave_id=wave_id, git_head="older-head", proof_fingerprint=f"proof-{policy}", metadata={"accepted_by": "chatweb"})
                ledger.finish_wave(wave_id, status="accepted")
                ledger.finish_run(run_id, status="accepted")

            tagged("chatweb_mcp")
            tagged("mini")
            for index in range(101):
                ledger.create_run(objective=f"newer decoy {index}", metadata={"workflow": "diagnose"})

            comparison = ledger.paired_policy_evaluation(candidate_policies=("mini",), limit=500, min_pairs=1, min_task_classes=1)
            self.assertGreater(comparison["ledger_run_count"], 100)
            self.assertEqual(comparison["tagged_runs_scanned"], 2)
            self.assertEqual(comparison["results"][0]["pair_count"], 1)

    def test_paired_policy_evaluation_zero_pairs_is_indeterminate(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            comparison = ledger.paired_policy_evaluation(candidate_policies=("mini",), min_pairs=1, min_task_classes=1)
            result = comparison["results"][0]
            self.assertEqual(comparison["ledger_run_count"], 0)
            self.assertEqual(comparison["tagged_runs_scanned"], 0)
            self.assertEqual(result["pair_count"], 0)
            self.assertEqual(result["pareto_status"], "indeterminate_no_pairs")
            regret = result["routing_placement_regret"]
            self.assertEqual(regret["status"], "hold")
            self.assertEqual(regret["measurement_status"], "indeterminate_no_comparable_pairs")
            self.assertIsNone(regret["predicted_policy_score"]["coverage"])
            self.assertIsNone(regret["scalar_regret"]["value"])

    def test_paired_policy_evaluation_accepts_server_first_policy_names(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))

            def accepted(policy: str) -> None:
                run_id = ledger.create_run(
                    objective="same portable strong-oracle validation",
                    metadata={
                        "workflow": "test_failure",
                        "evaluation": {
                            "pair_id": "p3-server-first-pair",
                            "policy": policy,
                            "policy_version": "v1",
                            "task_class": "portable_strong_oracle_validation",
                            "oracle_id": "p3-oracle-v1",
                            "provenance": "representative",
                            "task_spec_fp": "p3-task-fp",
                            "environment_fp": "p3-env-fp",
                            "tool_contract_fp": "p3-tool-fp",
                            "evaluation_schema_fp": "p3-eval-fp",
                            "runtime_version": "0.4.3",
                            "cache_stratum": "cold",
                        },
                    },
                )
                wave_id = ledger.create_wave(
                    run_id,
                    execution_mode="mcp_only",
                    base_head="p3-head",
                    worktree_fp="p3-tree",
                    contract_fp="p3-contract",
                )
                ledger.append_event(
                    run_id,
                    wave_id=wave_id,
                    event_type="route_selected",
                    state_after="READY",
                    payload={"requested": "deterministic", "resolved": "deterministic"},
                )
                ledger.record_quality_outcome(
                    run_id=run_id,
                    wave_id=wave_id,
                    outcome={"source": "p3-test-oracle", "oracle_pass": True, "critical_defect_count": 0},
                )
                ledger.record_checkpoint(
                    run_id=run_id,
                    wave_id=wave_id,
                    git_head="p3-head",
                    proof_fingerprint=f"proof-{policy}",
                    metadata={"accepted_by": "chatweb"},
                )
                ledger.finish_wave(wave_id, status="accepted")
                ledger.finish_run(run_id, status="accepted")

            accepted("LOCAL_FIRST_V1")
            accepted("SERVER_FIRST_DETERMINISTIC_V1")

            comparison = ledger.paired_policy_evaluation(
                baseline_policy="LOCAL_FIRST_V1",
                candidate_policies=("SERVER_FIRST_DETERMINISTIC_V1",),
                min_pairs=1,
                min_task_classes=1,
            )
            result = comparison["results"][0]
            self.assertEqual(comparison["baseline_policy"], "local_first_v1")
            self.assertEqual(comparison["candidate_policies"], ["server_first_deterministic_v1"])
            self.assertEqual(result["candidate_policy"], "server_first_deterministic_v1")
            self.assertEqual(result["pair_count"], 1)
            self.assertEqual(result["task_classes"], ["portable_strong_oracle_validation"])
            self.assertFalse(result["automatic_activation"])

    def test_paired_policy_evaluation_keeps_nonaccepted_server_first_run_in_itt_denominator(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))

            def assigned(policy: str, *, accepted: bool, repaired: bool) -> None:
                run_id = ledger.create_run(
                    objective="same portable strong-oracle validation",
                    metadata={
                        "workflow": "test_failure",
                        "evaluation": {
                            "pair_id": "p3-itt-pair",
                            "policy": policy,
                            "policy_version": "v1",
                            "task_class": "portable_strong_oracle_validation",
                            "oracle_id": "p3-oracle-v1",
                            "provenance": "representative",
                            "task_spec_fp": "p3-itt-task-fp",
                            "environment_fp": "p3-itt-env-fp",
                            "tool_contract_fp": "p3-itt-tool-fp",
                            "evaluation_schema_fp": "p3-itt-eval-fp",
                            "runtime_version": "0.4.3",
                            "cache_stratum": "cold",
                        },
                    },
                )
                wave_id = ledger.create_wave(
                    run_id,
                    execution_mode="mcp_only",
                    base_head="p3-itt-head",
                    worktree_fp="p3-itt-tree",
                    contract_fp="p3-itt-contract",
                )
                ledger.append_event(
                    run_id,
                    wave_id=wave_id,
                    event_type="route_selected",
                    state_after="READY",
                    payload={"requested": "deterministic", "resolved": "deterministic"},
                )
                terminal_wave_id = wave_id
                if repaired:
                    ledger.append_event(
                        run_id,
                        wave_id=wave_id,
                        event_type="failure_observed",
                        state_before="EXECUTING",
                        state_after="REPLAN",
                        payload={"failure_class": "CHECK_FAILED"},
                    )
                    ledger.finish_wave(wave_id, status="replanned")
                    terminal_wave_id = ledger.create_wave(
                        run_id,
                        execution_mode="mcp_only",
                        base_head="p3-itt-head",
                        worktree_fp="p3-itt-tree",
                        contract_fp="p3-itt-contract",
                    )
                if accepted:
                    ledger.record_quality_outcome(
                        run_id=run_id,
                        wave_id=terminal_wave_id,
                        outcome={"source": "p3-test-oracle", "oracle_pass": True, "critical_defect_count": 0},
                    )
                    ledger.record_checkpoint(
                        run_id=run_id,
                        wave_id=terminal_wave_id,
                        git_head="p3-itt-head",
                        proof_fingerprint=f"proof-{policy}",
                        metadata={"accepted_by": "chatweb"},
                    )
                    ledger.finish_wave(terminal_wave_id, status="accepted")
                    ledger.finish_run(run_id, status="accepted")
                else:
                    ledger.finish_wave(terminal_wave_id, status="aborted")
                    ledger.finish_run(run_id, status="aborted")

            assigned("LOCAL_FIRST_V1", accepted=True, repaired=False)
            assigned("SERVER_FIRST_DETERMINISTIC_V1", accepted=False, repaired=True)

            comparison = ledger.paired_policy_evaluation(
                baseline_policy="LOCAL_FIRST_V1",
                candidate_policies=("SERVER_FIRST_DETERMINISTIC_V1",),
                min_pairs=1,
                min_task_classes=1,
            )
            result = comparison["results"][0]
            self.assertEqual(result["pair_count"], 1)
            self.assertEqual(result["accepted_pair_count"], 0)
            self.assertEqual(result["baseline_acceptance_rate"], 1.0)
            self.assertEqual(result["candidate_acceptance_rate"], 0.0)
            self.assertEqual(result["baseline_first_pass_rate"], 1.0)
            self.assertEqual(result["candidate_first_pass_rate"], 0.0)
            self.assertEqual(result["baseline_repair_rate"], 0.0)
            self.assertEqual(result["candidate_repair_rate"], 1.0)
            self.assertTrue(result["analysis_population"]["intention_to_treat"])
            self.assertFalse(result["analysis_population"]["survivor_filter"])
            self.assertEqual(result["tta_ms"]["candidate_p50"], None)
            self.assertIn("quality_floor_non_regression_not_proven", result["hold_reasons"])

    def test_paired_policy_evaluation_reports_component_regret_for_observed_dominance(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))

            def accepted(policy: str, route: str, cost: float, defects: int, started_at: str, accepted_at: str) -> None:
                run_id = ledger.create_run(
                    objective="paired observed regret",
                    metadata={
                        "workflow": "bugfix",
                        "evaluation": {
                            "pair_id": "pair-regret-dominance",
                            "policy": policy,
                            "task_class": "localized_bug",
                            "oracle_id": "oracle-regret",
                            "provenance": "representative",
                            "task_spec_fp": "task-regret",
                            "environment_fp": "env-regret",
                            "tool_contract_fp": "tool-regret",
                            "evaluation_schema_fp": "eval-regret",
                            "runtime_version": "0.4.3",
                            "cache_stratum": "cold",
                            "controller": {"source": "client_reported", "monetary_cost": cost},
                        },
                    },
                )
                wave_id = ledger.create_wave(
                    run_id,
                    execution_mode="mcp_only" if route == "deterministic" else "bounded_candidate",
                    base_head="head-regret",
                    worktree_fp="tree-regret",
                    contract_fp="contract-regret",
                )
                ledger.append_event(run_id, wave_id=wave_id, event_type="route_selected", payload={"resolved": route})
                ledger.record_quality_outcome(
                    run_id=run_id,
                    wave_id=wave_id,
                    outcome={"source": "paired-oracle", "oracle_pass": defects == 0, "critical_defect_count": defects},
                )
                checkpoint_id = ledger.record_checkpoint(
                    run_id=run_id,
                    wave_id=wave_id,
                    git_head="head-regret",
                    proof_fingerprint=f"proof-{policy}",
                    status="accepted",
                )
                ledger.finish_wave(wave_id, status="accepted")
                ledger.finish_run(run_id, status="accepted")
                with ledger._lock, ledger._connect() as connection:
                    connection.execute("UPDATE runs SET started_at=? WHERE run_id=?", (started_at, run_id))
                    connection.execute("UPDATE checkpoints SET created_at=? WHERE checkpoint_id=?", (accepted_at, checkpoint_id))

            accepted("chatweb_mcp", "deterministic", 2.0, 1, "2026-08-18T00:00:00Z", "2026-08-18T00:00:02Z")
            accepted("mini", "mini", 1.0, 0, "2026-08-18T00:01:00Z", "2026-08-18T00:01:01Z")
            result = ledger.paired_policy_evaluation(candidate_policies=("mini",), min_pairs=1, min_task_classes=1)["results"][0]
            pair = result["pairs"][0]["routing_placement_regret"]
            self.assertTrue(pair["outcome_complete"])
            self.assertEqual(pair["status"], "observed_pareto_dominance")
            self.assertEqual(pair["best_observed_comparable_action"], "mini")
            self.assertIsNone(pair["predicted_policy_score"]["baseline"])
            self.assertIsNone(pair["regret_estimate"]["scalar"])
            baseline_components = pair["regret_estimate"]["components_by_policy"]["chatweb_mcp"]
            self.assertEqual(baseline_components["critical_defect_count"], 1.0)
            self.assertEqual(baseline_components["time_to_accepted_ms"], 1000.0)
            self.assertEqual(baseline_components["total_monetary_cost"], 1.0)
            self.assertEqual(pair["regret_estimate"]["components_by_policy"]["mini"]["time_to_accepted_ms"], 0.0)
            regret = result["routing_placement_regret"]
            self.assertEqual(regret["status"], "observed")
            self.assertEqual(regret["measurement_status"], "observed_component_regret")
            self.assertEqual(regret["best_action_pairs"], 1)
            self.assertFalse(regret["automatic_activation"])

    def test_paired_policy_evaluation_tradeoff_never_invents_scalar_regret(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))

            def accepted(policy: str, route: str, cost: float, started_at: str, accepted_at: str) -> None:
                run_id = ledger.create_run(
                    objective="paired tradeoff regret",
                    metadata={
                        "workflow": "bugfix",
                        "evaluation": {
                            "pair_id": "pair-regret-tradeoff",
                            "policy": policy,
                            "task_class": "localized_bug",
                            "oracle_id": "oracle-tradeoff",
                            "provenance": "representative",
                            "task_spec_fp": "task-tradeoff",
                            "environment_fp": "env-tradeoff",
                            "tool_contract_fp": "tool-tradeoff",
                            "evaluation_schema_fp": "eval-tradeoff",
                            "runtime_version": "0.4.3",
                            "cache_stratum": "cold",
                            "controller": {"source": "client_reported", "monetary_cost": cost},
                        },
                    },
                )
                wave_id = ledger.create_wave(
                    run_id,
                    execution_mode="mcp_only" if route == "deterministic" else "bounded_candidate",
                    base_head="head-tradeoff",
                    worktree_fp="tree-tradeoff",
                    contract_fp="contract-tradeoff",
                )
                ledger.append_event(run_id, wave_id=wave_id, event_type="route_selected", payload={"resolved": route})
                ledger.record_quality_outcome(run_id=run_id, wave_id=wave_id, outcome={
                    "source": "paired-oracle", "oracle_pass": True, "critical_defect_count": 0,
                })
                checkpoint_id = ledger.record_checkpoint(
                    run_id=run_id,
                    wave_id=wave_id,
                    git_head="head-tradeoff",
                    proof_fingerprint=f"proof-{policy}",
                    status="accepted",
                )
                ledger.finish_wave(wave_id, status="accepted")
                ledger.finish_run(run_id, status="accepted")
                with ledger._lock, ledger._connect() as connection:
                    connection.execute("UPDATE runs SET started_at=? WHERE run_id=?", (started_at, run_id))
                    connection.execute("UPDATE checkpoints SET created_at=? WHERE checkpoint_id=?", (accepted_at, checkpoint_id))

            accepted("chatweb_mcp", "deterministic", 1.0, "2026-08-18T00:00:00Z", "2026-08-18T00:00:02Z")
            accepted("mini", "mini", 2.0, "2026-08-18T00:01:00Z", "2026-08-18T00:01:01Z")
            result = ledger.paired_policy_evaluation(candidate_policies=("mini",), min_pairs=1, min_task_classes=1)["results"][0]
            pair = result["pairs"][0]["routing_placement_regret"]
            self.assertEqual(pair["status"], "tradeoff_requires_calibrated_utility")
            self.assertIsNone(pair["best_observed_comparable_action"])
            self.assertIsNone(pair["regret_estimate"]["scalar"])
            self.assertIsNone(pair["regret_estimate"]["components_by_policy"]["mini"])
            regret = result["routing_placement_regret"]
            self.assertEqual(regret["status"], "hold")
            self.assertEqual(regret["measurement_status"], "tradeoff_requires_calibrated_utility")
            self.assertIn("utility_weights_not_calibrated", regret["hold_reasons"])
            self.assertFalse(regret["automatic_activation"])

    def test_paired_policy_evaluation_rejects_worktree_identity_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))

            def accepted(policy: str, worktree_fp: str) -> None:
                run_id = ledger.create_run(
                    objective="same causal task",
                    metadata={
                        "workflow": "bugfix",
                        "evaluation": {
                            "pair_id": "pair-drift",
                            "policy": policy,
                            "task_class": "localized_bug",
                            "oracle_id": "oracle-drift",
                            "provenance": "representative",
                            "task_spec_fp": "task-drift",
                            "environment_fp": "env-drift",
                            "tool_contract_fp": "tool-drift",
                            "evaluation_schema_fp": "eval-drift",
                            "runtime_version": "0.4.3",
                            "cache_stratum": "cold",
                        },
                    },
                )
                wave_id = ledger.create_wave(
                    run_id,
                    execution_mode="mcp_only",
                    base_head="same-head",
                    worktree_fp=worktree_fp,
                    contract_fp="same-contract",
                )
                ledger.finish_wave(wave_id, status="accepted")
                ledger.finish_run(run_id, status="accepted")

            accepted("chatweb_mcp", "tree-a")
            accepted("mini", "tree-b")
            comparison = ledger.paired_policy_evaluation(candidate_policies=("mini",), min_pairs=1, min_task_classes=1)
            self.assertEqual(comparison["results"][0]["pair_count"], 0)
            self.assertEqual(comparison["excluded"]["identity_mismatch"], 1)
            self.assertEqual(comparison["identity_mismatch_reasons"]["worktree_fp"], 1)
            self.assertEqual(comparison["identity_mismatch_reasons"]["pair_fingerprint"], 1)

    def test_quality_outcome_projects_known_defects_and_proof_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(
                objective="representative Mini quality",
                metadata={"workflow": "bugfix", "promotion_provenance": "representative"},
            )
            wave_id = ledger.create_wave(run_id, execution_mode="bounded_candidate")
            ledger.append_event(run_id, wave_id=wave_id, event_type="route_selected", payload={"resolved": "mini"})
            ledger.record_proof(
                run_id=run_id,
                wave_id=wave_id,
                stage_id="focused",
                stage_version="1",
                input_fingerprint="quality-proof",
                status="passed",
            )
            recorded = ledger.record_quality_outcome(
                run_id=run_id,
                wave_id=wave_id,
                outcome={
                    "oracle_pass": True,
                    "critical_defect_count": 0,
                    "source": "delayed_project_observation",
                },
            )
            self.assertEqual(recorded["critical_defect_count"], 0)
            ledger.finish_wave(wave_id, status="accepted")
            ledger.finish_run(run_id, status="accepted")

            economics = ledger.accepted_result_economics(run_id)
            self.assertEqual(
                economics["critical_defects"],
                {"status": "known", "count": 0, "source": "delayed_project_observation"},
            )
            mini = next(item for item in ledger.routing_promotion_readiness()["routes"] if item["route"] == "mini")
            self.assertEqual(mini["critical_defect_known_zero_samples"], 1)
            self.assertEqual(mini["proof_or_oracle_complete_samples"], 1)
            self.assertNotIn("critical_defect_evidence_incomplete", mini["hold_reasons"])
            self.assertNotIn("proof_or_oracle_evidence_incomplete", mini["hold_reasons"])

    def test_external_candidate_credit_delta_is_not_total_system_cost(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))

            def accepted(policy: str, route: str, credits: float | None) -> None:
                run_id = ledger.create_run(
                    objective="paired credit semantics",
                    metadata={
                        "workflow": "bugfix",
                        "evaluation": {
                            "pair_id": "pair-credit",
                            "policy": policy,
                            "task_class": "localized_bug",
                            "oracle_id": "oracle-credit",
                            "provenance": "representative",
                            "task_spec_fp": "task-credit",
                            "environment_fp": "env-credit",
                            "tool_contract_fp": "tool-credit",
                            "evaluation_schema_fp": "eval-credit",
                            "runtime_version": "0.4.3",
                            "cache_stratum": "cold",
                        },
                    },
                )
                mode = "mcp_only" if route == "deterministic" else "bounded_candidate"
                wave_id = ledger.create_wave(
                    run_id,
                    execution_mode=mode,
                    base_head="head-credit",
                    worktree_fp="tree-credit",
                    contract_fp="contract-credit",
                )
                ledger.append_event(run_id, wave_id=wave_id, event_type="route_selected", payload={"resolved": route})
                if credits is not None:
                    delegation = ledger.create_delegation(
                        wave_id,
                        authority_owner="candidate",
                        route_requested=route,
                        route_resolved=route,
                        model="model",
                        metadata={"economics": {"estimated_credits": credits}},
                    )
                    ledger.finish_delegation(delegation, status="completed")
                ledger.record_quality_outcome(
                    run_id=run_id,
                    wave_id=wave_id,
                    outcome={"critical_defect_count": 0, "oracle_pass": True, "source": "test"},
                )
                ledger.finish_wave(wave_id, status="accepted")
                ledger.finish_run(run_id, status="accepted")

            accepted("chatweb_mcp", "deterministic", None)
            accepted("mini", "mini", 0.125)
            result = ledger.paired_policy_evaluation(
                candidate_policies=("mini",),
                min_pairs=1,
                min_task_classes=1,
            )["results"][0]
            self.assertEqual(
                result["external_candidate_credit_delta"]["measurement"],
                "estimated_external_candidate_credits_only_not_total_system_cost",
            )
            self.assertEqual(result["external_candidate_credit_delta"]["p50"], 0.125)
            self.assertFalse(result["total_monetary_cost"]["complete"])

    def test_events_survive_restart_and_hash_chain_verifies(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            run_id = ledger.create_run(objective="ship behavior", task_id="task-1")
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only", base_head="abc", worktree_fp="fp")
            ledger.append_event(run_id, wave_id=wave_id, event_type="preflight", state_after="PREFLIGHT")
            ledger.append_event(run_id, wave_id=wave_id, event_type="ready", state_before="PREFLIGHT", state_after="READY")

            restored = OrchestrationLedger(root)
            events = restored.list_events(run_id)
            self.assertEqual([item["event_type"] for item in events], ["preflight", "ready"])
            integrity = restored.verify_chain(run_id)
            self.assertTrue(integrity["ok"])
            self.assertEqual(integrity["checked"], 2)

    def test_large_proof_metadata_is_compressed_and_round_trips_after_restart(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            run_id = ledger.create_run(objective="compressed proof metadata")
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
            metadata = {"payload": "repeated-proof-metadata-" * 400, "nested": {"value": 7}}
            proof_id = ledger.record_proof(
                run_id=run_id,
                wave_id=wave_id,
                stage_id="large-metadata",
                stage_version="1",
                input_fingerprint="large-metadata-fp",
                status="passed",
                metadata=metadata,
            )
            with ledger._lock, ledger._connect() as connection:
                raw = connection.execute(
                    "SELECT metadata_json FROM proofs WHERE proof_id=?",
                    (proof_id,),
                ).fetchone()[0]
            self.assertIsInstance(raw, bytes)
            self.assertTrue(raw.startswith(b"WCPM1\0"))
            restored = OrchestrationLedger(root)
            self.assertEqual(restored.list_proofs(run_id)[0]["metadata"], metadata)
            self.assertTrue(restored.verify_chain(run_id)["ok"])

    def test_legacy_text_proof_metadata_remains_readable(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(objective="legacy proof metadata")
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
            proof_id = ledger.record_proof(
                run_id=run_id,
                wave_id=wave_id,
                stage_id="legacy-metadata",
                stage_version="1",
                input_fingerprint="legacy-metadata-fp",
                status="passed",
                metadata={"small": "value"},
            )
            with ledger._lock, ledger._connect() as connection:
                raw = connection.execute(
                    "SELECT metadata_json FROM proofs WHERE proof_id=?",
                    (proof_id,),
                ).fetchone()[0]
            self.assertIsInstance(raw, str)
            self.assertEqual(ledger.list_proofs(run_id)[0]["metadata"], {"small": "value"})

    def test_corrupt_compressed_proof_metadata_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(objective="corrupt proof metadata")
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
            proof_id = ledger.record_proof(
                run_id=run_id,
                wave_id=wave_id,
                stage_id="corrupt-metadata",
                stage_version="1",
                input_fingerprint="corrupt-metadata-fp",
                status="passed",
            )
            with ledger._lock, ledger._connect() as connection:
                connection.execute(
                    "UPDATE proofs SET metadata_json=? WHERE proof_id=?",
                    (b"WCPM1\0not-zlib", proof_id),
                )
            with self.assertRaises(zlib.error):
                ledger.list_proofs(run_id)

    def test_observation_spans_reconstruct_explicit_critical_path_without_parallel_double_count(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(objective="critical path")
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
            spans = [
                {"span_id": "controller", "stage": "controller", "source": "chatweb", "measurement": "observed", "clock_domain": "chatweb", "start_ms": 10, "end_ms": 110},
                {"span_id": "tool", "stage": "tool", "source": "mcp", "measurement": "observed", "clock_domain": "mcp", "start_ms": 1, "end_ms": 51, "depends_on": ["controller"]},
                {"span_id": "provider", "stage": "provider", "source": "provider", "measurement": "observed", "clock_domain": "provider", "start_ms": 5, "end_ms": 85, "depends_on": ["controller"]},
                {"span_id": "accept", "stage": "accept", "source": "chatweb", "measurement": "observed", "clock_domain": "chatweb", "start_ms": 120, "end_ms": 140, "depends_on": ["tool", "provider"]},
            ]
            for span in spans:
                ledger.record_observation_span(run_id=run_id, wave_id=wave_id, span=span)

            analysis = ledger.critical_path_analysis(run_id)
            self.assertTrue(analysis["complete"])
            self.assertEqual(analysis["critical_path_ms"], 200.0)
            self.assertEqual(analysis["path_span_ids"], ["controller", "provider", "accept"])
            self.assertEqual(analysis["span_count"], 4)
            self.assertEqual(analysis["cross_clock_edges"], 4)

    def test_observation_span_analysis_fails_closed_on_missing_dependency(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(objective="incomplete critical path")
            ledger.record_observation_span(
                run_id=run_id,
                span={
                    "span_id": "visible",
                    "stage": "assistant_response_visible",
                    "source": "electron",
                    "measurement": "observed_host_visible",
                    "clock_domain": "electron-renderer",
                    "start_ms": 10,
                    "end_ms": 20,
                    "depends_on": ["unknown-controller-span"],
                },
            )
            analysis = ledger.critical_path_analysis(run_id)
            self.assertFalse(analysis["complete"])
            self.assertIn("missing_dependency_spans", analysis["reasons"])
            self.assertEqual(analysis["missing_dependency_span_ids"], ["unknown-controller-span"])

    def test_observation_span_id_is_idempotent_but_conflicts_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(objective="span identity")
            span = {"span_id": "same", "stage": "tool", "source": "mcp", "measurement": "observed", "clock_domain": "mcp", "start_ms": 1, "end_ms": 2}
            first = ledger.record_observation_span(run_id=run_id, span=span)
            second = ledger.record_observation_span(run_id=run_id, span=span)
            self.assertTrue(first["recorded"])
            self.assertFalse(second["recorded"])
            with self.assertRaisesRegex(ValueError, "different evidence"):
                ledger.record_observation_span(run_id=run_id, span={**span, "end_ms": 3})

    def test_sensitive_payload_is_redacted_but_identity_remains(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(objective="safe audit")
            wave_id = ledger.create_wave(run_id, execution_mode="bounded_candidate")
            ledger.append_event(
                run_id,
                wave_id=wave_id,
                event_type="model_dispatch_started",
                payload={
                    "prompt": "super secret prompt",
                    "api_token": "secret-token",
                    "model": "gpt-test",
                    "economics": {
                        "input_tokens": 1200,
                        "cached_input_tokens": 900,
                        "output_tokens": 80,
                        "reasoning_output_tokens": 12,
                        "cached_tokens": 900,
                        "token": "must-stay-secret",
                        "input_tokens_string": "not-a-counter",
                    },
                },
            )
            payload = ledger.list_events(run_id)[0]["payload"]
            self.assertEqual(payload["api_token"], "[REDACTED]")
            self.assertTrue(payload["prompt"]["redacted"])
            self.assertEqual(payload["model"], "gpt-test")
            self.assertEqual(len(payload["prompt"]["sha256"]), 64)
            economics = payload["economics"]
            self.assertEqual(economics["input_tokens"], 1200)
            self.assertEqual(economics["cached_input_tokens"], 900)
            self.assertEqual(economics["output_tokens"], 80)
            self.assertEqual(economics["reasoning_output_tokens"], 12)
            self.assertEqual(economics["cached_tokens"], 900)
            self.assertEqual(economics["token"], "[REDACTED]")
            self.assertEqual(economics["input_tokens_string"], "[REDACTED]")

    def test_external_delegation_upsert_is_idempotent_monotonic_and_terminal(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(objective="external telemetry")
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
            common = dict(
                delegation_id="opencode-delegation",
                wave_id=wave_id,
                authority_owner="opencode",
                route_requested="opencode",
                route_resolved="opencode-go/deepseek-v4-flash",
                model="opencode-go/deepseek-v4-flash",
            )
            first = ledger.upsert_external_delegation(**common, status="active", metadata={"economics": {"input_tokens": 10, "output_tokens": 2, "cache_read_tokens": 4}})
            nested = ledger.upsert_external_delegation(**common, status="active", metadata={"timing": {"queue_ms": 2, "provider_ms": None, "total_ms": None}})
            self.assertTrue(nested["changed"])
            self.assertEqual(nested["delegation"]["metadata"]["timing"]["queue_ms"], 2)
            self.assertTrue(first["created"])
            duplicate = ledger.upsert_external_delegation(**common, status="active", metadata={"economics": {"input_tokens": 10, "output_tokens": 2, "cache_read_tokens": 4}})
            self.assertFalse(duplicate["changed"])
            completed = ledger.upsert_external_delegation(**common, status="completed", metadata={"economics": {"input_tokens": 100, "output_tokens": 20, "cache_read_tokens": 40}})
            self.assertTrue(completed["terminal_transition"])
            stale = ledger.upsert_external_delegation(**common, status="active", metadata={"economics": {"input_tokens": 1, "output_tokens": 1, "cache_read_tokens": 1}})
            self.assertFalse(stale["changed"])
            self.assertEqual(stale["delegation"]["status"], "completed")
            self.assertEqual(stale["delegation"]["metadata"]["economics"]["input_tokens"], 100)
            self.assertEqual(stale["delegation"]["metadata"]["economics"]["cache_read_tokens"], 40)

    def test_external_delegation_aggregates_message_economics_and_freezes_conflicting_terminal(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(objective="aggregate provider messages")
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
            common = dict(
                delegation_id="opencode-provider-aggregate",
                wave_id=wave_id,
                authority_owner="opencode",
                route_requested="opencode",
                route_resolved="opencode-go/deepseek-v4-flash",
                model="opencode-go/deepseek-v4-flash",
            )
            first = ledger.upsert_external_delegation(**common, status="active", metadata={"message_economics": {"msg-1": {"input_tokens": 100, "output_tokens": 10, "provider_cost": 0.001, "duration_ms": 600}}})
            duplicate = ledger.upsert_external_delegation(**common, status="active", metadata={"message_economics": {"msg-1": {"input_tokens": 100, "output_tokens": 10, "provider_cost": 0.001, "duration_ms": 600}}})
            self.assertTrue(first["created"])
            self.assertFalse(duplicate["changed"])
            second = ledger.upsert_external_delegation(**common, status="completed", metadata={"message_economics": {"msg-2": {"input_tokens": 50, "output_tokens": 5, "provider_cost": 0.002, "duration_ms": 300}}})
            economics = second["delegation"]["metadata"]["economics"]
            self.assertEqual((economics["input_tokens"], economics["output_tokens"]), (150, 15))
            self.assertAlmostEqual(economics["provider_cost"], 0.003)
            self.assertEqual(second["delegation"]["metadata"]["provider_message_duration_ms"], 900)
            conflicting = ledger.upsert_external_delegation(**common, status="failed", metadata={"error_class": "deadline_or_timeout", "timing": {"total_ms": 45000}})
            self.assertFalse(conflicting["changed"])
            self.assertEqual(conflicting["delegation"]["status"], "completed")
            self.assertNotIn("error_class", conflicting["delegation"]["metadata"])

    def test_shadow_route_record_is_idempotent_and_projects_actual_run_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(objective="shadow routing")
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
            recommendation = {
                "recommendation_id": "shadow-route-1",
                "mode": "shadow_only",
                "features": {"side_effect_class": "read_only", "scope": "broad"},
                "recommendation": {"route": "opencode_read_only_flash", "model": "opencode-go/deepseek-v4-flash"},
                "automatic_dispatch": False,
                "mutation_allowed": False,
            }
            first = ledger.record_shadow_route(run_id=run_id, wave_id=wave_id, recommendation=recommendation)
            duplicate = ledger.record_shadow_route(run_id=run_id, wave_id=wave_id, recommendation=recommendation)
            self.assertTrue(first["recorded"])
            self.assertFalse(duplicate["recorded"])
            ledger.upsert_external_delegation(
                delegation_id="actual-1",
                wave_id=wave_id,
                authority_owner="opencode",
                route_requested="opencode_read_only",
                route_resolved="opencode-go/deepseek-v4-flash",
                model="opencode-go/deepseek-v4-flash",
                status="completed",
                metadata={"side_effect_class": "read_only"},
            )
            projected = ledger.routing_evidence(run_id)
            self.assertEqual(len(projected["shadow_recommendations"]), 1)
            self.assertEqual(projected["shadow_recommendations"][0]["recommendation_id"], "shadow-route-1")
            self.assertEqual(len(projected["actual_delegations"]), 1)
            self.assertEqual(projected["actual_delegations"][0]["delegation_id"], "actual-1")
            self.assertEqual(projected["accepted_result"]["run_id"], run_id)
            self.assertFalse(projected["accepted_result"]["accepted"])

    def test_routing_evidence_projects_similar_accepted_cohorts_and_warm_threads(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            for repaired in (False, True):
                historical = ledger.create_run(objective="historical bugfix", metadata={"workflow": "bugfix"})
                first_wave = ledger.create_wave(historical, execution_mode="bounded_candidate")
                ledger.append_event(
                    historical,
                    wave_id=first_wave,
                    event_type="route_selected",
                    payload={"resolved": "mini", "model": "gpt-5.4-mini", "effort": "low", "profile": "candidate_mini"},
                )
                if repaired:
                    ledger.finish_wave(first_wave, status="replanned")
                    second_wave = ledger.create_wave(historical, execution_mode="bounded_candidate")
                    ledger.append_event(
                        historical,
                        wave_id=second_wave,
                        event_type="route_selected",
                        payload={"resolved": "mini", "model": "gpt-5.4-mini", "effort": "low", "profile": "candidate_mini"},
                    )
                    ledger.finish_wave(second_wave, status="accepted")
                else:
                    ledger.finish_wave(first_wave, status="accepted")
                ledger.finish_run(historical, status="accepted")

            current = ledger.create_run(objective="current bugfix", metadata={"workflow": "bugfix"})
            current_wave = ledger.create_wave(current, execution_mode="mcp_only")
            ledger.upsert_agent_lane(
                lane_id="warm-lane",
                run_id=current,
                wave_id=current_wave,
                semantic_key="review",
                lifecycle="idle",
                thread_id="thread-warm",
            )
            ledger.upsert_agent_lane(
                lane_id="waiting-lane",
                run_id=current,
                wave_id=current_wave,
                semantic_key="investigate",
                lifecycle="waiting",
            )

            projected = ledger.routing_evidence(current)
            cohorts = projected["similar_accepted_cohorts"]
            self.assertEqual(cohorts["task_class"], "bugfix")
            self.assertEqual(cohorts["sampled_runs"], 2)
            self.assertEqual(len(cohorts["cohorts"]), 1)
            mini = cohorts["cohorts"][0]
            self.assertEqual(mini["route"], "mini")
            self.assertEqual(mini["accepted_results"], 2)
            self.assertEqual(mini["first_pass_accepted"], 1)
            self.assertEqual(mini["first_pass_rate"], 0.5)
            self.assertEqual(mini["repaired_results"], 1)
            self.assertIsNone(mini["provider_cost"]["total"])
            self.assertEqual(mini["provider_cost"]["measurement"], "unobserved")
            health = projected["warm_thread_health"]
            self.assertEqual(health["lane_count"], 2)
            self.assertEqual(health["reusable_lane_count"], 1)
            self.assertEqual(health["reusable_lane_ids"], ["warm-lane"])
            self.assertFalse(health["automatic_reuse"])
            self.assertTrue(cohorts["model_free"])
            self.assertTrue(health["content_free"])
            self.assertFalse(projected["promotion_readiness"]["automatic_activation"])

    def test_routing_promotion_readiness_excludes_benchmarks_and_unverified_samples(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            benchmark = ledger.create_run(
                objective="Localized strong-oracle Mini benchmark only in tmp/execution-hub-benchmark/case.py",
                metadata={"workflow": "test_failure"},
            )
            benchmark_wave = ledger.create_wave(benchmark, execution_mode="bounded_candidate")
            ledger.append_event(benchmark, wave_id=benchmark_wave, event_type="route_selected", payload={"resolved": "mini"})
            ledger.finish_wave(benchmark_wave, status="accepted")
            ledger.finish_run(benchmark, status="accepted")

            unverified = ledger.create_run(objective="ordinary bugfix", metadata={"workflow": "bugfix"})
            unverified_wave = ledger.create_wave(unverified, execution_mode="bounded_candidate")
            ledger.append_event(unverified, wave_id=unverified_wave, event_type="route_selected", payload={"resolved": "mini"})
            ledger.finish_wave(unverified_wave, status="accepted")
            ledger.finish_run(unverified, status="accepted")

            readiness = ledger.routing_promotion_readiness()
            self.assertFalse(readiness["automatic_activation"])
            self.assertEqual(readiness["policy_status"], "advisory_not_activation_authority")
            mini = next(item for item in readiness["routes"] if item["route"] == "mini")
            self.assertEqual(mini["accepted_observed"], 2)
            self.assertEqual(mini["representative_accepted"], 0)
            self.assertEqual(mini["benchmark_or_synthetic_excluded"], 1)
            self.assertEqual(mini["unverified_provenance"], 1)
            self.assertEqual(mini["status"], "hold")
            self.assertIn("insufficient_representative_accepted_results", mini["hold_reasons"])
            self.assertIn("unverified_provenance_excluded", mini["hold_reasons"])

    def test_routing_promotion_readiness_holds_sufficient_samples_without_defect_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            workflows = ("bugfix", "feature", "test_failure")
            for index in range(10):
                run_id = ledger.create_run(
                    objective=f"representative project task {index}",
                    metadata={
                        "workflow": workflows[index % len(workflows)],
                        "promotion_provenance": "representative",
                    },
                )
                wave_id = ledger.create_wave(run_id, execution_mode="bounded_candidate")
                ledger.append_event(run_id, wave_id=wave_id, event_type="route_selected", payload={"resolved": "luna"})
                ledger.finish_wave(wave_id, status="accepted")
                ledger.finish_run(run_id, status="accepted")

            readiness = ledger.routing_promotion_readiness()
            luna = next(item for item in readiness["routes"] if item["route"] == "luna")
            self.assertEqual(luna["representative_accepted"], 10)
            self.assertEqual(luna["task_class_count"], 3)
            self.assertEqual(luna["status"], "hold")
            self.assertIn("critical_defect_evidence_incomplete", luna["hold_reasons"])
            self.assertFalse(readiness["automatic_activation"])

    def test_accepted_result_economics_keeps_measured_provider_cost_separate_from_estimated_credits(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(objective="accepted economics", metadata={"workflow": "bugfix"})
            first_wave = ledger.create_wave(run_id, execution_mode="bounded_candidate")
            ledger.append_event(
                run_id,
                wave_id=first_wave,
                event_type="route_selected",
                payload={"requested": "mini", "resolved": "mini", "model": "gpt-5.4-mini", "effort": "low", "profile": "candidate_mini"},
            )
            candidate = ledger.create_delegation(
                first_wave,
                authority_owner="CODEX:mini",
                route_requested="mini",
                route_resolved="mini",
                model="gpt-5.4-mini",
                effort="low",
                metadata={"economics": {"estimated_credits": 0.125, "pricing_basis": "observed-rate-card", "model": "gpt-5.4-mini"}},
            )
            ledger.finish_delegation(candidate, status="blocked")
            ledger.append_event(run_id, wave_id=first_wave, delegation_id=candidate, event_type="failure_observed", payload={"failure_class": "CANDIDATE_BLOCKED"})
            ledger.record_proof(
                run_id=run_id,
                wave_id=first_wave,
                stage_id="focused",
                stage_version="1",
                input_fingerprint="failed-proof",
                status="failed",
            )
            ledger.finish_wave(first_wave, status="replanned")

            second_wave = ledger.create_wave(run_id, execution_mode="mcp_only")
            ledger.append_event(
                run_id,
                wave_id=second_wave,
                event_type="route_selected",
                payload={"requested": "opencode", "resolved": "opencode_read_only_flash", "model": "opencode-go/deepseek-v4-flash", "effort": None, "profile": "read_only"},
            )
            provider_delegation = ledger.create_delegation(
                second_wave,
                authority_owner="OPENCODE:flash",
                route_requested="opencode",
                route_resolved="opencode_read_only_flash",
                model="opencode-go/deepseek-v4-flash",
                metadata={"timing": {"queue_ms": 12, "provider_ms": 34, "total_ms": 46}},
            )
            ledger.finish_delegation(provider_delegation, status="completed")
            ledger.record_usage_event(
                run_id=run_id,
                wave_id=second_wave,
                delegation_id=provider_delegation,
                usage_event={
                    "schema_version": 1,
                    "usage_id": "usage-1",
                    "run_id": run_id,
                    "wave_id": second_wave,
                    "delegation_id": provider_delegation,
                    "provider_id": "opencode-go",
                    "model_id": "deepseek-v4-flash",
                    "model": "opencode-go/deepseek-v4-flash",
                    "status": "completed",
                    "provenance": {"source": "opencode:provider_dispatch"},
                    "measurement": {"usage": "measured", "cost": "measured"},
                    "usage": {"input_tokens": 100, "cached_input_tokens": 40, "uncached_input_tokens": 60, "output_tokens": 12, "reasoning_output_tokens": 2, "cache_read_tokens": 40, "cache_write_tokens": 1},
                    "cost": {"provider_cost": 0.003, "kind": "provider_reported"},
                },
            )
            ledger.record_proof(
                run_id=run_id,
                wave_id=second_wave,
                stage_id="focused",
                stage_version="1",
                input_fingerprint="green-proof",
                status="passed",
            )
            ledger.record_checkpoint(
                run_id=run_id,
                wave_id=second_wave,
                git_head="head",
                proof_fingerprint="green-proof",
                status="accepted",
            )
            ledger.finish_wave(second_wave, status="accepted")
            ledger.finish_run(run_id, status="accepted")

            evidence = ledger.accepted_result_economics(run_id)
            self.assertTrue(evidence["accepted"])
            self.assertFalse(evidence["first_pass_accepted"])
            self.assertEqual(evidence["repair"], {"replan_count": 1, "failure_event_count": 1})
            self.assertEqual(evidence["route"]["resolved"], "opencode_read_only_flash")
            self.assertEqual(evidence["route"]["model"], "opencode-go/deepseek-v4-flash")
            self.assertEqual(evidence["proof"]["records"], 2)
            self.assertEqual(evidence["proof"]["passed"], 1)
            self.assertEqual(evidence["proof"]["failed"], 1)
            self.assertEqual(evidence["proof"]["accepted_checkpoint_count"], 1)
            self.assertEqual(evidence["phase_timing"]["source"], "eocl_event_timestamps")
            self.assertIsInstance(evidence["phase_timing"]["by_state_ms"], dict)
            self.assertIsInstance(evidence["phase_timing"]["methodology_phase_ms"], dict)
            if evidence["tta_ms"]:
                self.assertGreaterEqual(evidence["phase_timing"]["tta_coverage"], 0)
                self.assertLessEqual(evidence["phase_timing"]["tta_coverage"], 1)
            self.assertEqual(evidence["provider_economics"]["usage_event_count"], 1)
            self.assertTrue(evidence["provider_economics"]["cost_complete"])
            self.assertAlmostEqual(evidence["provider_economics"]["provider_cost"], 0.003)
            self.assertTrue(evidence["provider_economics"]["attribution_complete"])
            self.assertAlmostEqual(evidence["provider_economics"]["attributed_provider_cost"], 0.003)
            self.assertEqual(evidence["provider_economics"]["usage"]["input_tokens"], 100)
            self.assertEqual(evidence["provider_economics"]["usage"]["cached_input_tokens"], 40)
            self.assertEqual(evidence["provider_economics"]["timing"]["measurement"], "delegation_metadata")
            self.assertTrue(evidence["provider_economics"]["timing"]["overlaps_eocl_windows"])
            self.assertEqual(evidence["provider_economics"]["timing"]["components_ms"], {"queue_ms": 12, "provider_ms": 34, "total_ms": 46})
            self.assertEqual(evidence["provider_economics"]["timing"]["sample_counts"], {"queue_ms": 1, "provider_ms": 1, "total_ms": 1})
            self.assertEqual(evidence["candidate_economics"]["estimated_credits"], 0.125)
            self.assertEqual(evidence["candidate_economics"]["pricing_bases"], ["observed-rate-card"])
            self.assertEqual(evidence["critical_defects"], {"status": "unknown", "count": None, "source": "not_recorded"})
            self.assertIsNotNone(evidence["tta_ms"])
            self.assertEqual(ledger.routing_evidence(run_id)["accepted_result"], evidence)
            session_provider = ledger.session_query(run_id)["accepted_result"]["provider_economics"]
            self.assertTrue(session_provider["attribution_complete"])
            self.assertAlmostEqual(session_provider["attributed_provider_cost"], 0.003)

    def test_accepted_result_provider_cost_is_unknown_when_cost_coverage_is_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(objective="partial provider economics")
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
            common = {
                "schema_version": 1,
                "run_id": run_id,
                "wave_id": wave_id,
                "provider_id": "provider",
                "model_id": "model",
                "model": "provider/model",
                "status": "completed",
                "usage": {"input_tokens": 10, "cached_input_tokens": 0, "uncached_input_tokens": 10, "output_tokens": 1, "reasoning_output_tokens": 0, "cache_read_tokens": 0, "cache_write_tokens": 0},
            }
            ledger.record_usage_event(
                run_id=run_id,
                wave_id=wave_id,
                delegation_id="d1",
                usage_event={**common, "usage_id": "u1", "delegation_id": "d1", "measurement": {"usage": "measured", "cost": "measured"}, "cost": {"provider_cost": 0.001}},
            )
            ledger.record_usage_event(
                run_id=run_id,
                wave_id=wave_id,
                delegation_id="d2",
                usage_event={**common, "usage_id": "u2", "delegation_id": "d2", "measurement": {"usage": "measured", "cost": "unobserved"}, "cost": {"provider_cost": None}},
            )
            ledger.finish_wave(wave_id, status="accepted")
            ledger.finish_run(run_id, status="accepted")
            provider = ledger.accepted_result_economics(run_id)["provider_economics"]
            self.assertEqual(provider["usage_event_count"], 2)
            self.assertEqual(provider["cost_measured_event_count"], 1)
            self.assertFalse(provider["cost_complete"])
            self.assertIsNone(provider["provider_cost"])
            self.assertEqual(provider["usage"]["input_tokens"], 20)

    def test_total_cost_rejects_measured_but_uncorrelated_provider_usage(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(
                objective="provider attribution guard",
                metadata={"evaluation": {"controller": {"source": "client_reported", "monetary_cost": 0.01}}},
            )
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only", base_head="head")
            ledger.record_usage_event(
                run_id=run_id,
                wave_id=wave_id,
                delegation_id="uncorrelated",
                usage_event={
                    "schema_version": 1, "usage_id": "usage-uncorrelated", "run_id": run_id, "wave_id": wave_id,
                    "delegation_id": "uncorrelated", "provider_id": "opencode-go", "model_id": "deepseek-v4-pro",
                    "model": "opencode-go/deepseek-v4-pro", "status": "completed",
                    "provenance": {"source": "opencode:message.updated"},
                    "measurement": {"usage": "measured", "cost": "measured"},
                    "usage": {"input_tokens": 10, "cached_input_tokens": 0, "uncached_input_tokens": 10, "output_tokens": 1, "reasoning_output_tokens": 0, "cache_read_tokens": 0, "cache_write_tokens": 0},
                    "cost": {"provider_cost": 0.002, "kind": "provider_reported"},
                },
            )
            ledger.finish_wave(wave_id, status="accepted")
            ledger.finish_run(run_id, status="accepted")
            provider = ledger.accepted_result_economics(run_id)["provider_economics"]
            self.assertTrue(provider["cost_complete"])
            self.assertFalse(provider["attribution_complete"])
            self.assertAlmostEqual(provider["provider_cost"], 0.002)
            self.assertIsNone(provider["attributed_provider_cost"])
            total = ledger.accepted_result_evaluation(run_id)["total_monetary_cost"]
            self.assertFalse(total["complete"])
            self.assertIsNone(total["value"])
            self.assertEqual(total["reason"], "provider_cost_attribution_incomplete")

    def test_export_summary_includes_checkpoint_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(objective="accepted behavior", task_id="task-checkpoint")
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only", base_head="abc123", worktree_fp="fp")
            checkpoint_id = ledger.record_checkpoint(
                run_id=run_id,
                wave_id=wave_id,
                git_head="abc123",
                proof_fingerprint="proof-fp",
                status="accepted",
                metadata={"accepted_by": "ChatWeb Sol"},
            )

            summary = ledger.export_summary(run_id)

            self.assertEqual(len(summary["checkpoints"]), 1)
            checkpoint = summary["checkpoints"][0]
            self.assertEqual(checkpoint["checkpoint_id"], checkpoint_id)
            self.assertEqual(checkpoint["wave_id"], wave_id)
            self.assertEqual(checkpoint["git_head"], "abc123")
            self.assertEqual(checkpoint["proof_fingerprint"], "proof-fp")
            self.assertEqual(checkpoint["status"], "accepted")
            self.assertEqual(checkpoint["metadata"]["accepted_by"], "ChatWeb Sol")


    def test_event_replay_uses_stable_non_consumptive_sequence_cursor(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(objective="replay")
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
            for index in range(5):
                ledger.append_event(run_id, wave_id=wave_id, event_type=f"event-{index}")
            page1 = ledger.list_events_since(run_id, after_seq=0, limit=2)
            self.assertEqual([item["event_type"] for item in page1["events"]], ["event-0", "event-1"])
            self.assertTrue(page1["has_more"])
            page1_again = ledger.list_events_since(run_id, after_seq=0, limit=2)
            self.assertEqual(page1_again["events"], page1["events"])
            page2 = ledger.list_events_since(run_id, after_seq=page1["next_after_seq"], limit=10)
            self.assertEqual([item["event_type"] for item in page2["events"]], ["event-2", "event-3", "event-4"])
            self.assertFalse(page2["has_more"])

    def test_flight_recorder_and_phase_timing_are_bounded_and_timestamp_derived(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(objective="flight recorder")
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
            ledger.append_event(run_id, wave_id=wave_id, event_type="preflight", state_after="PREFLIGHT", event_time="2026-08-14T00:00:00.000Z")
            ledger.append_event(run_id, wave_id=wave_id, event_type="routed", state_before="PREFLIGHT", state_after="ROUTED", event_time="2026-08-14T00:00:00.100Z")
            ledger.append_event(run_id, wave_id=wave_id, event_type="execute", state_before="ROUTED", state_after="EXECUTING", event_time="2026-08-14T00:00:00.300Z")
            ledger.append_event(run_id, wave_id=wave_id, event_type="prove", state_before="EXECUTING", state_after="PROVING", event_time="2026-08-14T00:00:00.500Z", payload={"prompt": "must remain redacted"})
            timing = ledger.run_phase_timing(run_id)
            self.assertEqual(timing["source"], "eocl_event_timestamps")
            self.assertEqual(timing["by_state_ms"]["PREFLIGHT"], 100)
            self.assertEqual(timing["by_state_ms"]["ROUTED"], 200)
            self.assertEqual(timing["by_state_ms"]["EXECUTING"], 200)
            self.assertEqual(timing["methodology_phase_ms"]["preflight_ms"], 100)
            self.assertEqual(timing["methodology_phase_ms"]["dispatch_window_ms"], 200)
            self.assertEqual(timing["methodology_phase_ms"]["execution_window_ms"], 200)
            self.assertIsNone(timing["methodology_phase_ms"]["proof_ms"])
            self.assertEqual(timing["observed_ms"], 500)
            self.assertIsNone(timing["tta_ms"])
            self.assertIsNone(timing["unattributed_ms"])
            self.assertIsNone(timing["tta_coverage"])
            self.assertFalse(timing["meets_coverage_floor"])
            self.assertFalse(timing["meets_coverage_target"])
            self.assertIsNone(timing["segments"][-1]["duration_ms"])
            self.assertFalse(timing["complete"])
            recorder = ledger.flight_recorder(run_id, limit=2)
            self.assertEqual([item["state_after"] for item in recorder["events"]], ["EXECUTING", "PROVING"])
            self.assertTrue(recorder["has_more"])
            self.assertTrue(recorder["events"][-1]["payload"]["prompt"]["redacted"])
            delta = ledger.flight_recorder(run_id, after_seq=recorder["events"][-2]["seq"], limit=10)
            self.assertEqual([item["state_after"] for item in delta["events"]], ["PROVING"])
            self.assertFalse(delta["has_more"])
            self.assertEqual(len(ledger.list_runs(limit=1)), 1)

    def test_terminal_phase_timing_reports_unattributed_time_and_coverage_gates(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(objective="coverage truth")
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
            with ledger._lock, ledger._connect() as connection:
                connection.execute(
                    "UPDATE runs SET started_at=?, finished_at=?, status='accepted' WHERE run_id=?",
                    ("2026-08-14T00:00:00.000Z", "2026-08-14T00:00:01.000Z", run_id),
                )
            ledger.append_event(run_id, wave_id=wave_id, event_type="preflight", state_after="PREFLIGHT", event_time="2026-08-14T00:00:00.100Z")
            ledger.append_event(run_id, wave_id=wave_id, event_type="routed", state_before="PREFLIGHT", state_after="ROUTED", event_time="2026-08-14T00:00:00.300Z")
            ledger.append_event(run_id, wave_id=wave_id, event_type="execute", state_before="ROUTED", state_after="EXECUTING", event_time="2026-08-14T00:00:00.600Z")
            ledger.append_event(run_id, wave_id=wave_id, event_type="prove", state_before="EXECUTING", state_after="PROVING", event_time="2026-08-14T00:00:00.800Z")

            timing = ledger.run_phase_timing(run_id)
            self.assertEqual(timing["tta_ms"], 1000)
            self.assertEqual(timing["observed_ms"], 900)
            self.assertEqual(timing["unattributed_ms"], 100)
            self.assertEqual(timing["tta_coverage"], 0.9)
            self.assertEqual(timing["coverage_floor"], 0.9)
            self.assertEqual(timing["coverage_target"], 0.95)
            self.assertTrue(timing["meets_coverage_floor"])
            self.assertFalse(timing["meets_coverage_target"])
            self.assertTrue(timing["complete"])

    def test_evidence_query_is_bounded_wave_scoped_and_content_free(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(objective="resume evidence", task_id="task-evidence")
            first_wave = ledger.create_wave(run_id, execution_mode="mcp_only")
            second_wave = ledger.create_wave(run_id, execution_mode="bounded_candidate")
            ledger.append_event(run_id, wave_id=first_wave, event_type="first-wave", state_after="READY")
            first_second_wave_event = ledger.append_event(
                run_id,
                wave_id=second_wave,
                event_type="dispatch",
                state_after="EXECUTING",
                payload={"prompt": "never expose this prompt"},
            )
            ledger.append_event(run_id, wave_id=second_wave, event_type="prove", state_after="PROVING")
            ledger.append_event(run_id, wave_id=second_wave, event_type="accept", state_after="ACCEPTING")
            proof_id = ledger.record_proof(
                run_id=run_id,
                wave_id=second_wave,
                stage_id="focused",
                stage_version="1",
                input_fingerprint="fp",
                status="passed",
            )
            delegation_id = ledger.create_delegation(
                second_wave,
                authority_owner="CODEX:mini",
                route_requested="mini",
                route_resolved="mini",
                model="gpt-5.4-mini",
                effort="low",
                metadata={"prompt": "delegation prompt is redacted in storage"},
            )
            checkpoint_id = ledger.record_checkpoint(
                run_id=run_id,
                wave_id=second_wave,
                git_head="head",
                proof_fingerprint="proof-fp",
            )
            capsule = ledger.record_handoff_capsule(
                run_id=run_id,
                wave_id=second_wave,
                payload={"next_action": "continue evidence"},
            )

            recent = ledger.evidence_query(run_id, wave_id=second_wave, limit=2)
            self.assertEqual(recent["query"]["wave_id"], second_wave)
            self.assertEqual([item["wave_id"] for item in recent["events"]], [second_wave, second_wave])
            self.assertEqual([item["event_type"] for item in recent["events"]], ["prove", "accept"])
            self.assertTrue(recent["omitted_earlier_events"])
            self.assertEqual(recent["relationships"]["task_id"], "task-evidence")
            self.assertEqual(recent["relationships"]["proof_ids"], [proof_id])
            self.assertEqual(recent["relationships"]["delegation_ids"], [delegation_id])
            self.assertEqual(recent["relationships"]["checkpoint_ids"], [checkpoint_id])
            self.assertEqual(recent["latest_handoff_capsule"]["capsule_id"], capsule["capsule_id"])
            self.assertNotIn("payload", recent["latest_handoff_capsule"])
            self.assertEqual(recent["proofs"][0]["artifact_ref"]["kind"], "orchestration_proof")
            self.assertTrue(recent["proofs"][0]["artifact_ref"]["restart_safe"])
            self.assertEqual(recent["latest_handoff_capsule"]["artifact_ref"]["kind"], "handoff_capsule")
            self.assertTrue(recent["latest_handoff_capsule"]["artifact_ref"]["content_addressed"])
            self.assertTrue(recent["model_free"])
            self.assertTrue(recent["content_free"])
            self.assertFalse(recent["raw_transcript_included"])

            delta = ledger.evidence_query(
                run_id,
                wave_id=second_wave,
                after_seq=first_second_wave_event["seq"],
                limit=1,
            )
            self.assertEqual([item["event_type"] for item in delta["events"]], ["prove"])
            self.assertTrue(delta["has_more"])
            self.assertFalse(delta["omitted_earlier_events"])
            self.assertTrue(delta["integrity"]["ok"])

    def test_session_query_prunes_by_priority_under_one_item_budget(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(objective="priority resume", task_id="task-priority")
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
            ledger.append_event(run_id, wave_id=wave_id, event_type="context_prepared", state_after="PREFLIGHT", payload={"prompt": "never expose raw prompt"})
            ledger.append_event(run_id, wave_id=wave_id, event_type="route_selected", state_after="ROUTED")
            ledger.append_event(run_id, wave_id=wave_id, event_type="failure_observed", state_after="REPLAN")
            ledger.append_event(run_id, wave_id=wave_id, event_type="awaiting_final_acceptance", state_after="ACCEPTING")
            proof_id = ledger.record_proof(
                run_id=run_id,
                wave_id=wave_id,
                stage_id="focused",
                stage_version="1",
                input_fingerprint="fp-priority",
                status="passed",
            )
            ledger.record_checkpoint(
                run_id=run_id,
                wave_id=wave_id,
                git_head="head-priority",
                proof_fingerprint="proof-priority",
            )
            ledger.create_delegation(
                wave_id,
                authority_owner="CODEX:mini",
                route_requested="mini",
                route_resolved="mini",
                model="gpt-5.4-mini",
                effort="low",
            )
            ledger.record_handoff_capsule(
                run_id=run_id,
                wave_id=wave_id,
                payload={"next_action": "continue"},
            )

            session = ledger.session_query(run_id, wave_id=wave_id, limit=6)
            self.assertEqual(session["query"]["mode"], "model_free_priority")
            self.assertEqual(session["query"]["limit"], 6)
            self.assertLessEqual(len(session["items"]), 6)
            self.assertGreater(session["pruning"]["omitted_items"], 0)
            ranks = {"critical": 0, "acceptance": 1, "proof": 2, "route": 3, "context": 4, "recent": 5}
            projected = [ranks[item["priority"]] for item in session["items"]]
            self.assertEqual(projected, sorted(projected))
            self.assertEqual(session["items"][0]["priority"], "critical")
            proof_items = [item for item in session["items"] if item.get("kind") == "proof"]
            self.assertTrue(proof_items)
            self.assertEqual(proof_items[0]["proof_id"], proof_id)
            self.assertEqual(proof_items[0]["artifact_ref"]["kind"], "orchestration_proof")
            self.assertNotIn("never expose raw prompt", json.dumps(session, ensure_ascii=False))
            self.assertTrue(session["model_free"])
            self.assertTrue(session["content_free"])
            self.assertFalse(session["raw_transcript_included"])

    def test_durable_idempotency_deduplicates_and_rejects_conflicting_reuse(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = OrchestrationLedger(root)
            claim = first.claim_idempotency(
                idempotency_key="workflow-1",
                operation="agent_workflow",
                request_hash="hash-a",
                process_instance_id="process-a",
            )
            self.assertTrue(claim["claimed"])
            completed = first.finish_idempotency(
                "workflow-1", request_hash="hash-a", status="completed", summary={"run_id": "run-a"}
            )
            self.assertEqual(completed["status"], "completed")

            restored = OrchestrationLedger(root)
            duplicate = restored.claim_idempotency(
                idempotency_key="workflow-1",
                operation="agent_workflow",
                request_hash="hash-a",
                process_instance_id="process-b",
            )
            self.assertFalse(duplicate["claimed"])
            self.assertEqual(duplicate["reason"], "completed")
            self.assertEqual(duplicate["record"]["summary"]["run_id"], "run-a")

            conflict = restored.claim_idempotency(
                idempotency_key="workflow-1",
                operation="agent_workflow",
                request_hash="hash-b",
                process_instance_id="process-b",
            )
            self.assertEqual(conflict["reason"], "conflict")

    def test_in_progress_idempotency_becomes_unknown_after_process_restart(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            ledger.claim_idempotency(
                idempotency_key="workflow-crash",
                operation="agent_workflow",
                request_hash="hash-crash",
                process_instance_id="old-process",
            )
            changed = ledger.mark_orphaned_idempotency(current_process_instance_id="new-process")
            self.assertEqual(changed, 1)
            record = ledger.get_idempotency("workflow-crash")
            self.assertEqual(record["status"], "unknown")
            self.assertEqual(record["summary"]["outcome_unknown_reason"], "mcp_process_restarted")

    def test_organic_rework_summary_excludes_candidate_routes_and_counts_preflight_avoids(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))

            first_pass = ledger.create_run(objective="organic first pass")
            first_wave = ledger.create_wave(first_pass, execution_mode="mcp_only")
            ledger.finish_wave(first_wave, status="accepted")
            ledger.finish_run(first_pass, status="accepted")

            repaired = ledger.create_run(objective="organic repaired")
            repaired_wave = ledger.create_wave(repaired, execution_mode="mcp_only")
            ledger.finish_wave(repaired_wave, status="replanned")
            repaired_wave_2 = ledger.create_wave(repaired, execution_mode="mcp_only")
            ledger.finish_wave(repaired_wave_2, status="accepted")
            ledger.finish_run(repaired, status="accepted")

            candidate = ledger.create_run(objective="explicit mini candidate")
            candidate_wave = ledger.create_wave(candidate, execution_mode="bounded_candidate")
            ledger.create_delegation(
                candidate_wave,
                authority_owner="CODEX:mini",
                route_requested="mini",
                route_resolved="mini",
                model="gpt-5.4-mini",
                effort="low",
            )
            ledger.finish_wave(candidate_wave, status="accepted")
            ledger.finish_run(candidate, status="accepted")

            ledger.claim_idempotency(
                idempotency_key="preflight-avoid",
                operation="agent_workflow",
                request_hash="preflight-hash",
                process_instance_id="process",
            )
            ledger.finish_idempotency(
                "preflight-avoid",
                request_hash="preflight-hash",
                status="failed",
                summary={
                    "error_code": "PATCH_CONTEXT_AMBIGUOUS",
                    "outcome_unknown": False,
                    "workflow_patch_preflight": True,
                },
            )

            summary = ledger.organic_rework_summary()
            self.assertEqual(summary["accepted_runs"], 2)
            self.assertEqual(summary["first_pass_accepted"], 1)
            self.assertEqual(summary["repaired_accepted"], 1)
            self.assertEqual(summary["repair"]["replan_count"], 1)
            self.assertEqual(summary["excluded"]["explicit_model_route"], 1)
            self.assertEqual(summary["preflight_avoided"]["count"], 1)
            self.assertEqual(
                summary["preflight_avoided"]["error_codes"],
                {"PATCH_CONTEXT_AMBIGUOUS": 1},
            )
            self.assertTrue(summary["model_free"])
            self.assertTrue(summary["content_free"])


if __name__ == "__main__":
    unittest.main()
