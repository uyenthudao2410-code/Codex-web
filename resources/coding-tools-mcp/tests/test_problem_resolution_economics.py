from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from coding_tools_mcp.acceptance_receipts import passed_proof_fingerprint
from coding_tools_mcp.ledger_analysis import open_ledger_analysis_snapshot
from coding_tools_mcp.orchestration_ledger import OrchestrationLedger
from coding_tools_mcp.problem_lineage import problem_event_hash_material, problem_outcome_receipt_id
from coding_tools_mcp.problem_resolution_economics import ProblemLineageFacts, problem_resolution_economics_report
from coding_tools_mcp.usage_events import build_usage_event


CAPSULE = {
    "objective_summary": "Resolve the report fixture",
    "acceptance_criteria": [{"criterion_id": "criterion-1", "summary": "Focused proof passes"}],
    "protected_invariants": [], "constraints": [], "unresolved_conditions": [],
}

ENVELOPE = {
    "schema_version": 1,
    "direct_outcomes": [{"outcome_id": "outcome-1", "summary": "The bounded outcome is observable"}],
    "relevant_invariants": ["Preserve the existing public contract"],
    "truth_domains": ["source", "runtime"],
    "adjacent_risks": [],
    "excluded_scope": ["Unrelated modules"],
    "required_evidence": [{"evidence_id": "evidence-1", "kind": "runtime_read", "provenance": "exact accepted wave", "status": "observed"}],
    "closure_falsification_probe": {"probe_id": "probe-1", "method": "Read the bounded outcome again", "expected_failure_signal": "The outcome remains contradicted", "executed": True, "result": "passed"},
}

class ProblemResolutionEconomicsTests(unittest.TestCase):
    def _fixture(self, root: Path) -> None:
        ledger = OrchestrationLedger(root)
        ledger.migrate_problem_lineage_schema()
        opened = ledger.problem_record_event({
            "operation": "open", "event_id": "open", "problem_id": "problem-fixture", "task_id": "task-fixture",
            "task_class": "bugfix", "engineering_floor": "REQUIRED", "contract_capsule": CAPSULE,
            "provenance": "CONTROLLER_REPORTED_EXPLICIT_USER", "evidence_level": "OBSERVED",
            "occurred_at": "2026-08-25T00:00:00Z", "occurred_at_source": "EXPLICIT_USER",
        }, now="2026-08-25T00:00:01Z", authority_context="RUNTIME_EXPLICIT_USER")
        fingerprint = opened["event"]["contract_fingerprint"]
        context = {"schema_version": 1, "work_origin": "problem", "resolution_claim": "full_problem", "problem_id": "problem-fixture", "problem_revision": 1, "contract_fingerprint": fingerprint, "engineering_floor": "REQUIRED", "policy_eligible": False}
        run_id = ledger.create_run(objective="fixture", metadata={"problem_resolution": context})
        wave_id = ledger.create_wave(run_id, execution_mode="mcp_only", metadata={"problem_resolution": context})
        ledger.problem_record_event({
            "operation": "link", "event_id": "link", "problem_id": "problem-fixture", "problem_revision": 1,
            "run_id": run_id, "wave_id": wave_id, "relation_type": "ENGINEERING_ATTEMPT_BOUND",
            "provenance": "DETERMINISTIC_EVIDENCE", "evidence_level": "OBSERVED",
        }, now="2026-08-25T00:00:02Z", authority_context="RUNTIME_BINDING")
        proof = ledger.record_proof(run_id=run_id, wave_id=wave_id, stage_id="focused", stage_version="1", input_fingerprint="proof", status="passed")
        ledger.problem_record_coverage_manifest(run_id=run_id, wave_id=wave_id, manifest={"criterion-1": [proof]})
        # The reporter fixture needs an observed deterministic technical pass;
        # its direct ledger setup is not an EOCL acceptance/reconciliation test.
        ledger.problem_record_event({
            "operation": "provisional_resolve", "event_id": "provisional", "problem_id": "problem-fixture", "problem_revision": 1,
            "run_id": run_id, "wave_id": wave_id, "provenance": "DETERMINISTIC_EVIDENCE", "evidence_level": "OBSERVED",
            "occurred_at": "2026-08-25T00:00:30Z", "occurred_at_source": "RUNTIME",
        }, now="2026-08-25T00:00:31Z", authority_context="RUNTIME_EOCL")
        ledger.problem_record_event({
            "operation": "confirm", "event_id": "confirm", "problem_id": "problem-fixture", "problem_revision": 1,
            "feedback_intent": "CONFIRM_RESOLVED", "provenance": "CONTROLLER_REPORTED_EXPLICIT_USER", "evidence_level": "OBSERVED",
            "turn_id": "turn-confirm", "trace_id": "trace-confirm",
            "outcome_receipt_type": "CHATWEB_EXPLICIT_USER_OUTCOME_V1",
            "outcome_receipt_id": problem_outcome_receipt_id(
                receipt_type="CHATWEB_EXPLICIT_USER_OUTCOME_V1",
                event_id="confirm",
                problem_id="problem-fixture",
                problem_revision=1,
                turn_id="turn-confirm",
                trace_id="trace-confirm",
            ),
            "occurred_at": "2026-08-25T00:01:00Z", "occurred_at_source": "EXPLICIT_USER",
        }, now="2026-08-25T00:01:01Z", authority_context="RUNTIME_OUTCOME_RECEIPT")

    def test_report_separates_resolution_from_administrative_disposition(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._fixture(root)
            with open_ledger_analysis_snapshot(root) as snapshot:
                facts = ProblemLineageFacts.load(snapshot.reader)
                report = problem_resolution_economics_report(snapshot.ledger, facts)
            self.assertEqual(report["status"], "DESCRIPTIVE_ONLY")
            self.assertEqual(report["schema_version"], 7)
            self.assertEqual(report["denominators"]["problem_threads"], 1)
            self.assertEqual(report["resolution_outcomes"]["confirmed_threads"], 1)
            self.assertEqual(report["resolution_outcomes"]["trusted_resolution"]["true"], 1)
            self.assertEqual(report["mechanics_coverage"]["full_claim_waves_with_structural_manifest"], 1)
            self.assertEqual(report["denominators"]["problem_chain_invalid_threads"], 0)
            self.assertTrue(report["resolution_outcomes"]["administrative_disposition_is_not_resolution"])
            self.assertEqual(report["time_to_administrative_disposition"]["observed"], 0)
            self.assertIn("attested_clock_authority_mismatch", report["time_to_provisional"]["missing_or_invalid_reason_counts"])

    def test_mismatched_receipt_digest_is_not_counted_even_when_event_chain_is_rehashed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._fixture(root)
            ledger = OrchestrationLedger(root)
            with ledger._lock, ledger._connect() as connection:
                row = connection.execute("SELECT * FROM problem_events WHERE event_id='confirm'").fetchone()
                assert row is not None
                event = dict(row)
                event["eligible_for_policy"] = bool(event["eligible_for_policy"])
                event["outcome_receipt_id"] = "0" * 64
                material = problem_event_hash_material(
                    event,
                    state_before=str(event["state_before"]),
                    state_after=str(event["state_after"]),
                    prev_hash=str(event["prev_hash"]),
                )
                rewritten_hash = hashlib.sha256(
                    json.dumps(material, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
                ).hexdigest()
                connection.execute(
                    "UPDATE problem_events SET outcome_receipt_id=?,event_hash=? WHERE event_id='confirm'",
                    (event["outcome_receipt_id"], rewritten_hash),
                )
                connection.execute(
                    "UPDATE problem_threads SET latest_problem_event_hash=? WHERE problem_id='problem-fixture'",
                    (rewritten_hash,),
                )
            with open_ledger_analysis_snapshot(root) as snapshot:
                report = problem_resolution_economics_report(
                    snapshot.ledger,
                    ProblemLineageFacts.load(snapshot.reader),
                )
            self.assertEqual(report["denominators"]["problem_chain_invalid_threads"], 0)
            independent = report["revision_4_metrics"]["independent_outcome_evidence_coverage"]
            self.assertEqual(independent["authoritative_confirmation_events"], 1)
            self.assertEqual(independent["receipt_bound_confirmation_events"], 0)
            self.assertEqual(independent["unbound_authoritative_confirmation_events"], 1)
            self.assertEqual(independent["coverage"], 0.0)

    def test_v9_snapshot_is_inactive_and_writer_free(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            OrchestrationLedger(root)
            with open_ledger_analysis_snapshot(root) as snapshot:
                report = problem_resolution_economics_report(snapshot.ledger, ProblemLineageFacts.load(snapshot.reader))
            self.assertEqual(report["status"], "PRL_SCHEMA_INACTIVE")
            self.assertTrue(report["policy"]["no_writer"])

    def test_revision_metrics_do_not_reinterpret_an_older_confirmed_revision(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._fixture(root)
            ledger = OrchestrationLedger(root)
            current = ledger.problem_get("problem-fixture")["current_revision"]
            revised = ledger.problem_record_event({
                "operation": "revise", "event_id": "revise-2", "problem_id": "problem-fixture",
                "expected_revision": 1, "expected_contract_fingerprint": current["contract_fingerprint"],
                "task_class": "bugfix", "engineering_floor": "REQUIRED", "contract_capsule": CAPSULE,
                "provenance": "CONTROLLER_REPORTED_EXPLICIT_USER", "evidence_level": "OBSERVED",
                "occurred_at": "2026-08-25T00:02:00Z", "occurred_at_source": "EXPLICIT_USER",
            }, now="2026-08-25T00:02:01Z", authority_context="RUNTIME_EXPLICIT_USER")
            self.assertEqual(revised["event"]["relation_type"], "REVISION")
            self.assertEqual(revised["thread"]["thread"]["resolution_state"], "OPEN")
            ledger.problem_record_event({
                "operation": "block", "event_id": "block-2", "problem_id": "problem-fixture", "problem_revision": 2,
                "provenance": "DETERMINISTIC_EVIDENCE", "evidence_level": "OBSERVED",
                "reason_code": "blocked_external_dependency",
                "occurred_at": "2026-08-25T00:03:00Z", "occurred_at_source": "RUNTIME",
            }, now="2026-08-25T00:03:01Z", authority_context="RUNTIME_GUARD")
            with open_ledger_analysis_snapshot(root) as snapshot:
                report = problem_resolution_economics_report(snapshot.ledger, ProblemLineageFacts.load(snapshot.reader))
            self.assertEqual(report["analysis_unit"]["primary"], "problem_revision")
            self.assertEqual(report["denominators"]["analysis_problem_revisions"], 2)
            self.assertEqual(report["resolution_outcomes"]["trusted_resolution"]["true"], 1)
            self.assertEqual(report["time_to_confirmed_resolution"]["observed"], 1)

    def test_clock_authority_mismatch_is_missing_not_zero(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._fixture(root)
            with open_ledger_analysis_snapshot(root) as snapshot:
                report = problem_resolution_economics_report(snapshot.ledger, ProblemLineageFacts.load(snapshot.reader))
            metric = report["time_to_provisional"]
            self.assertEqual(metric["observed"], 0)
            self.assertEqual(metric["ordered_exact_values_ms_when_n_le_20"], None)
            self.assertEqual(metric["missing_or_invalid_reason_counts"]["attested_clock_authority_mismatch"], 1)

    def test_revision_4_metrics_use_revision_denominators_and_reopen_invalidates_first_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._fixture(root)
            ledger = OrchestrationLedger(root)
            problem = ledger.problem_get("problem-fixture")
            exact_link = next(
                event for event in problem["events"]
                if event["relation_type"] == "ENGINEERING_ATTEMPT_BOUND"
            )
            run_id, wave_id = exact_link["run_id"], exact_link["wave_id"]
            ledger.append_event(
                run_id,
                wave_id=wave_id,
                event_type="problem_frame_shadow",
                payload={
                    "problem_id": "problem-fixture",
                    "problem_revision": 1,
                    "frame_id": "frame-1",
                    "frame_revision": 1,
                    "decision_changed": True,
                    "counterevidence_count": 1,
                    "counterevidence_advisory_status": "COUNTEREVIDENCE_REQUIRES_FRAME_REVIEW",
                    "frame_update_or_explanation_recommended": True,
                    "materiality_inferred": False,
                    "automatic_mutation_gate": False,
                },
            )
            ledger.append_event(
                run_id,
                wave_id=wave_id,
                event_type="wave_replanned",
                payload={"reason": "authority_recovery"},
            )
            proofs = ledger.list_proofs(run_id, wave_id=wave_id)
            ledger.problem_prepare_eocl_outcome_claim(
                run_id=run_id,
                wave_id=wave_id,
                git_head="head",
                worktree_fp="worktree",
                proof_fingerprint=passed_proof_fingerprint(proofs),
                accepted_files={
                    "schema_version": 2,
                    "source": "task_modified_files",
                    "complete": True,
                    "count": 0,
                    "total_bytes": 0,
                    "run_id": run_id,
                    "wave_id": wave_id,
                    "files": [],
                    "incomplete_reasons": [],
                },
                durable_mutation=False,
                coverage_manifest={"criterion-1": [proofs[0]["proof_id"]]},
                resolution_envelope=ENVELOPE,
            )
            with open_ledger_analysis_snapshot(root) as snapshot:
                before_reopen = problem_resolution_economics_report(
                    snapshot.ledger,
                    ProblemLineageFacts.load(snapshot.reader),
                )["revision_4_metrics"]
            self.assertEqual(before_reopen["first_pass_trusted_resolution"]["numerator"], 1)
            self.assertEqual(before_reopen["first_pass_trusted_resolution"]["denominator"], 1)
            self.assertEqual(before_reopen["false_closure"]["numerator"], 0)
            self.assertEqual(before_reopen["frame_revisions"]["distinct_frame_revisions"], 1)
            self.assertEqual(before_reopen["decision_delta_shadow_attestation_rate"]["rate"], 1.0)
            self.assertEqual(
                before_reopen["decision_delta_shadow_attestation_rate"]["classification"],
                "shadow_attested",
            )
            self.assertFalse(before_reopen["decision_delta_shadow_attestation_rate"]["causal_value_proven"])
            advisory = before_reopen["counterevidence_frame_update_advisory_coverage"]
            self.assertEqual(advisory["observed_counterevidence_events"], 1)
            self.assertEqual(advisory["events_with_update_or_explain_advisory"], 1)
            self.assertEqual(advisory["coverage"], 1.0)
            self.assertEqual(advisory["classification"], "descriptive_advisory_only")
            self.assertFalse(advisory["materiality_inferred"])
            self.assertFalse(advisory["automatic_mutation_gate"])
            self.assertEqual(before_reopen["resolution_envelope_evidence_attestation_coverage"]["coverage"], 1.0)
            self.assertEqual(
                before_reopen["resolution_envelope_evidence_attestation_coverage"]["classification"],
                "descriptive_attested_not_independent_confirmation",
            )
            self.assertFalse(before_reopen["resolution_envelope_evidence_attestation_coverage"]["receipt_bound"])
            self.assertEqual(
                before_reopen["multi_primary_run_revision_rate"]["revisions_with_multiple_primary_runs"],
                0,
            )
            self.assertEqual(
                before_reopen["multi_primary_run_revision_rate"]["classification"],
                "descriptive_multiple_attempt_proxy",
            )
            self.assertFalse(before_reopen["multi_primary_run_revision_rate"]["semantic_sibling_linkage_proven"])
            self.assertEqual(before_reopen["framing_regret"]["status"], "UNAVAILABLE")
            self.assertIsNone(before_reopen["framing_regret"]["value_ms"])
            self.assertTrue(before_reopen["framing_regret"]["unknown_is_not_zero"])
            self.assertEqual(before_reopen["true_sibling_recurrence"]["status"], "UNAVAILABLE")
            self.assertIsNone(before_reopen["true_sibling_recurrence"]["rate"])
            self.assertTrue(before_reopen["true_sibling_recurrence"]["multi_primary_run_is_proxy_only"])
            independent = before_reopen["independent_outcome_evidence_coverage"]
            self.assertEqual(independent["status"], "AVAILABLE")
            self.assertEqual(independent["numerator"], 1)
            self.assertEqual(independent["denominator"], 1)
            self.assertEqual(independent["coverage"], 1.0)
            self.assertEqual(independent["authoritative_confirmation_events"], 1)
            self.assertEqual(independent["receipt_bound_confirmation_events"], 1)
            self.assertEqual(independent["unbound_authoritative_confirmation_events"], 0)
            self.assertTrue(independent["historical_confirmations_not_backfilled"])
            self.assertNotIn("decision_changing_observation_rate", before_reopen)
            self.assertNotIn("outcome_evidence_coverage", before_reopen)
            self.assertNotIn("sibling_recurrence", before_reopen)
            self.assertEqual(
                before_reopen["control_friction_decomposition"]["counts"],
                {"authority_recovery": 1},
            )

            ledger.problem_record_event({
                "operation": "reopen",
                "event_id": "reopen-after-confirmation",
                "problem_id": "problem-fixture",
                "problem_revision": 1,
                "feedback_intent": "SAME_PROBLEM_STILL_FAILING",
                "provenance": "CONTROLLER_REPORTED_EXPLICIT_USER",
                "evidence_level": "OBSERVED",
            }, now="2026-08-25T00:02:00Z", authority_context="RUNTIME_EXPLICIT_USER")
            sibling_context = {
                "schema_version": 1,
                "work_origin": "problem",
                "resolution_claim": "none",
                "problem_id": "problem-fixture",
                "problem_revision": 1,
                "contract_fingerprint": problem["current_revision"]["contract_fingerprint"],
                "engineering_floor": "REQUIRED",
                "policy_eligible": False,
            }
            sibling_run = ledger.create_run(
                objective="sibling repair",
                metadata={"problem_resolution": sibling_context},
            )
            sibling_wave = ledger.create_wave(
                sibling_run,
                execution_mode="mcp_only",
                metadata={"problem_resolution": sibling_context},
            )
            ledger.problem_record_event({
                "operation": "link",
                "event_id": "sibling-link",
                "problem_id": "problem-fixture",
                "problem_revision": 1,
                "run_id": sibling_run,
                "wave_id": sibling_wave,
                "relation_type": "ENGINEERING_ATTEMPT_BOUND",
                "provenance": "DETERMINISTIC_EVIDENCE",
                "evidence_level": "OBSERVED",
            }, now="2026-08-25T00:02:01Z", authority_context="RUNTIME_BINDING")
            with open_ledger_analysis_snapshot(root) as snapshot:
                after_reopen = problem_resolution_economics_report(
                    snapshot.ledger,
                    ProblemLineageFacts.load(snapshot.reader),
                )["revision_4_metrics"]
            self.assertEqual(after_reopen["first_pass_trusted_resolution"]["numerator"], 0)
            self.assertEqual(after_reopen["false_closure"]["numerator"], 1)
            self.assertEqual(
                after_reopen["multi_primary_run_revision_rate"]["revisions_with_multiple_primary_runs"],
                1,
            )

    def test_problem_journey_charges_replan_run_and_keeps_usage_planes_separate(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._fixture(root)
            ledger = OrchestrationLedger(root)
            problem = ledger.problem_get("problem-fixture")
            first_link = next(
                event for event in problem["events"]
                if event["relation_type"] == "ENGINEERING_ATTEMPT_BOUND"
            )
            first_run, first_wave = first_link["run_id"], first_link["wave_id"]
            context = {
                "schema_version": 1,
                "work_origin": "problem",
                "resolution_claim": "full_problem",
                "problem_id": "problem-fixture",
                "problem_revision": 1,
                "contract_fingerprint": problem["current_revision"]["contract_fingerprint"],
                "engineering_floor": "REQUIRED",
                "policy_eligible": False,
            }
            rejected_run = ledger.create_run(
                objective="rejected attempt",
                metadata={"problem_resolution": context},
            )
            rejected_wave = ledger.create_wave(
                rejected_run,
                execution_mode="mcp_only",
                metadata={"problem_resolution": context},
            )
            ledger.problem_record_event({
                "operation": "link",
                "event_id": "link-rejected-run",
                "problem_id": "problem-fixture",
                "problem_revision": 1,
                "run_id": rejected_run,
                "wave_id": rejected_wave,
                "relation_type": "ENGINEERING_ATTEMPT_BOUND",
                "provenance": "DETERMINISTIC_EVIDENCE",
                "evidence_level": "OBSERVED",
            }, now="2026-08-25T00:00:03Z", authority_context="RUNTIME_BINDING")
            ledger.append_event(
                rejected_run,
                wave_id=rejected_wave,
                event_type="wave_replanned",
                payload={"reason": "proof_failed"},
            )

            for run_id, wave_id, actor, tokens, cost in (
                (first_run, first_wave, "controller", 10, 0.10),
                (first_run, first_wave, "provider", 20, 0.20),
                (rejected_run, rejected_wave, "controller", 5, 0.05),
            ):
                delegation_id = f"{actor}-{run_id}"
                event = build_usage_event(
                    run_id=run_id,
                    wave_id=wave_id,
                    delegation_id=delegation_id,
                    provider_id="chatweb" if actor == "controller" else "provider",
                    model_id="controller-model" if actor == "controller" else "provider-model",
                    status="completed",
                    source="chatweb:mcp_meta" if actor == "controller" else "provider:dispatch",
                    input_tokens=tokens,
                    output_tokens=1,
                    provider_cost=cost,
                    actor=actor,
                    usage_provenance="client_reported" if actor == "controller" else "provider_reported",
                )
                ledger.record_usage_event(
                    run_id=run_id,
                    wave_id=wave_id,
                    delegation_id=delegation_id,
                    usage_event=event,
                )
            ledger.finish_wave(first_wave, status="accepted")
            ledger.finish_run(first_run, status="accepted")
            ledger.finish_wave(rejected_wave, status="replanned")
            ledger.finish_run(rejected_run, status="rejected")

            with open_ledger_analysis_snapshot(root) as snapshot:
                report = problem_resolution_economics_report(
                    snapshot.ledger,
                    ProblemLineageFacts.load(snapshot.reader),
                )
            journeys = report["problem_revision_journeys"]
            self.assertEqual(journeys["summary"]["exact_linked_run_count"], 2)
            self.assertEqual(journeys["summary"]["accepted_run_count"], 1)
            self.assertEqual(journeys["summary"]["rejected_or_aborted_run_count"], 1)
            self.assertEqual(journeys["summary"]["replan_wave_count"], 1)
            journey = journeys["journeys"][0]
            self.assertEqual(len(journey["nested_per_run_economics"]), 2)
            self.assertEqual(journey["topology"]["terminal_run_status_counts"], {"accepted": 1, "rejected": 1})
            self.assertEqual(journey["topology"]["terminal_wave_status_counts"], {"accepted": 1, "replanned": 1})
            controller = journey["resources"]["controller_tokens_exact_when_available"]
            provider = journey["resources"]["provider_tokens"]
            self.assertEqual(controller["usage"]["input_total_tokens"], 15)
            self.assertEqual(provider["usage"]["input_total_tokens"], 20)
            self.assertIsNone(journey["resources"]["combined_model_tokens"])
            self.assertTrue(journey["resources"]["cross_plane_token_sum_forbidden"])
            self.assertEqual(
                journey["avoided_duplicate_read_or_localization"]["missing_reason"],
                "causal_avoidance_receipt_not_recorded",
            )

    def test_problem_journey_excludes_wrong_wave_and_partial_usage_attribution(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._fixture(root)
            ledger = OrchestrationLedger(root)
            problem = ledger.problem_get("problem-fixture")
            first_link = next(
                event for event in problem["events"]
                if event["relation_type"] == "ENGINEERING_ATTEMPT_BOUND"
            )
            run_id, exact_wave_id = first_link["run_id"], first_link["wave_id"]
            unrelated_wave_id = ledger.create_wave(
                run_id,
                execution_mode="mcp_only",
                metadata={
                    "problem_resolution": {
                        "schema_version": 1,
                        "work_origin": "problem",
                        "resolution_claim": "full_problem",
                        "problem_id": "different-problem",
                        "problem_revision": 1,
                    },
                },
            )
            for wave_id, delegation_id, tokens, attribution_status in (
                (exact_wave_id, "controller-exact", 10, "exact"),
                (unrelated_wave_id, "controller-wrong-wave", 20, "exact"),
                (exact_wave_id, "", 30, "partial"),
            ):
                event = build_usage_event(
                    run_id=run_id,
                    wave_id=wave_id,
                    delegation_id=delegation_id,
                    provider_id="chatweb",
                    model_id="controller-model",
                    status="completed",
                    source="chatweb:mcp_meta",
                    input_tokens=tokens,
                    output_tokens=1,
                    provider_cost=0.10,
                    actor="controller",
                    usage_provenance="client_reported",
                    attribution_status=attribution_status,
                )
                ledger.record_usage_event(
                    run_id=run_id,
                    wave_id=wave_id,
                    delegation_id=delegation_id,
                    usage_event=event,
                )

            with open_ledger_analysis_snapshot(root) as snapshot:
                report = problem_resolution_economics_report(
                    snapshot.ledger,
                    ProblemLineageFacts.load(snapshot.reader),
                )
            journey = report["problem_revision_journeys"]["journeys"][0]
            controller = journey["resources"]["controller_tokens_exact_when_available"]
            self.assertEqual(report["problem_revision_journeys"]["summary"]["exact_linked_wave_count"], 1)
            self.assertEqual(journey["topology"]["wave_count"], 1)
            self.assertEqual(controller["status"], "PARTIAL")
            self.assertEqual(controller["event_count"], 1)
            self.assertEqual(controller["candidate_event_count"], 3)
            self.assertEqual(controller["excluded_event_count"], 2)
            self.assertEqual(
                controller["exclusion_reason_counts"],
                {"attribution_not_exact": 1, "wave_not_exact_problem_revision": 1},
            )
            self.assertIsNone(controller["usage"])
            self.assertFalse(controller["cost"]["complete"])
            lifecycle = journey["lifecycle_economics"]
            self.assertEqual(lifecycle["schema_version"], 1)
            self.assertIsNone(lifecycle["segments"]["pre_technical_acceptance"]["value_ms"])
            self.assertEqual(
                lifecycle["segments"]["later_unrelated_observation"]["status"],
                "OUT_OF_SCOPE_UNOBSERVED",
            )

    def test_problem_journey_keeps_full_terminal_status_counts(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._fixture(root)
            ledger = OrchestrationLedger(root)
            problem = ledger.problem_get("problem-fixture")
            context = {
                "schema_version": 1,
                "work_origin": "problem",
                "resolution_claim": "full_problem",
                "problem_id": "problem-fixture",
                "problem_revision": 1,
                "contract_fingerprint": problem["current_revision"]["contract_fingerprint"],
                "engineering_floor": "REQUIRED",
                "policy_eligible": False,
            }
            for index, status in enumerate(("blocked", "timeout", "unresolved"), start=1):
                run_id = ledger.create_run(
                    objective=f"{status} attempt",
                    metadata={"problem_resolution": context},
                )
                wave_id = ledger.create_wave(
                    run_id,
                    execution_mode="mcp_only",
                    metadata={"problem_resolution": context},
                )
                ledger.problem_record_event({
                    "operation": "link",
                    "event_id": f"link-terminal-{index}",
                    "problem_id": "problem-fixture",
                    "problem_revision": 1,
                    "run_id": run_id,
                    "wave_id": wave_id,
                    "relation_type": "ENGINEERING_ATTEMPT_BOUND",
                    "provenance": "DETERMINISTIC_EVIDENCE",
                    "evidence_level": "OBSERVED",
                }, now=f"2026-08-25T00:0{index}:10Z", authority_context="RUNTIME_BINDING")
                ledger.finish_wave(wave_id, status=status)
                ledger.finish_run(run_id, status=status)

            with open_ledger_analysis_snapshot(root) as snapshot:
                report = problem_resolution_economics_report(
                    snapshot.ledger,
                    ProblemLineageFacts.load(snapshot.reader),
                )
            topology = report["problem_revision_journeys"]["journeys"][0]["topology"]
            self.assertEqual(
                topology["terminal_run_status_counts"],
                {"blocked": 1, "timeout": 1, "unresolved": 1},
            )
            self.assertEqual(
                topology["terminal_wave_status_counts"],
                {"blocked": 1, "timeout": 1, "unresolved": 1},
            )
            self.assertEqual(
                topology["run_status_counts"],
                {"active": 1, "blocked": 1, "timeout": 1, "unresolved": 1},
            )

    def test_problem_journey_projects_exact_knowledge_recovery_and_capsule_overhead(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._fixture(root)
            ledger = OrchestrationLedger(root)
            problem = ledger.problem_get("problem-fixture")
            run_id = next(
                event["run_id"] for event in problem["events"]
                if event["relation_type"] == "ENGINEERING_ATTEMPT_BOUND"
            )
            for index, kind in enumerate(("PROBLEM_PROVISIONAL_RESOLVED", "NEXT_CRITICAL_ACTION_CHANGED"), start=1):
                ledger.controller_record_knowledge_checkpoint(
                    workspace_id="workspace-fixture",
                    problem_id="problem-fixture",
                    problem_revision=1,
                    material_event_kind=kind,
                    material_event_id=f"material-{index}",
                    material_state_fingerprint=str(index) * 64,
                    capsule_fingerprint="3" * 64,
                    source_fingerprint="4" * 64,
                    runtime_behavior_fingerprint="5" * 64,
                )
            ledger.controller_ack_knowledge(
                ack_id="ack-behind",
                workspace_id="workspace-fixture",
                problem_id="problem-fixture",
                problem_revision=1,
                knowledge_revision=1,
                controller_endpoint_id="controller-endpoint-fixture",
            )
            ledger.record_handoff_capsule(
                run_id=run_id,
                conversation_epoch=2,
                payload={"next_action": "continue exact Problem Revision"},
            )
            ledger.record_handoff_capsule(
                run_id=run_id,
                conversation_epoch=3,
                payload={"next_action": "re-observe the same exact RUN"},
            )

            with open_ledger_analysis_snapshot(root) as snapshot:
                facts = ProblemLineageFacts.load(snapshot.reader)
                report = problem_resolution_economics_report(snapshot.ledger, facts)
            journey = report["problem_revision_journeys"]["journeys"][0]
            continuity = journey["continuity"]
            self.assertEqual(continuity["controller_knowledge_checkpoints"]["value"], 2)
            self.assertEqual(continuity["controller_recovery_events"]["value"], 1)
            self.assertEqual(continuity["stale_ack_recoveries"]["value"], 1)
            self.assertGreater(continuity["recovery_delta_bytes"]["value"], 0)
            self.assertGreater(continuity["capsule_bytes"]["value"], 0)
            self.assertEqual(continuity["conversation_epochs_observed"]["values"], [2, 3])
            self.assertEqual(continuity["capsule_count"]["value"], 2)
            self.assertEqual(journey["topology"]["run_count"], 1)
            self.assertEqual(continuity["resume_successes"]["value"], 0)
            self.assertEqual(continuity["resume_attempts"]["status"], "UNAVAILABLE")
            self.assertEqual(continuity["chatweb_product_sessions_observed"]["status"], "UNAVAILABLE")
            query = report["problem_revision_journeys"]["query_evidence"]
            self.assertLessEqual(query["total_snapshot_fact_load_statements"], 17)
            self.assertEqual(query["n_plus_one_sqlite_queries"], 0)


if __name__ == "__main__":
    unittest.main()
