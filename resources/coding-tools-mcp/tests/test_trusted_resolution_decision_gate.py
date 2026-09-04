from __future__ import annotations

import unittest

from coding_tools_mcp.egri_p5_continuity_readiness import (
    EGRI_P5_CONTINUITY_READINESS_SCHEMA_VERSION,
)
from coding_tools_mcp.trusted_resolution_decision_gate import (
    trusted_resolution_decision_gate,
)


BASELINE_FINGERPRINT = "a" * 64
TREATMENT_FINGERPRINT = "b" * 64


def tg11_readiness(*, ready: bool = True) -> dict[str, object]:
    return {
        "schema_version": EGRI_P5_CONTINUITY_READINESS_SCHEMA_VERSION,
        "status": (
            "READY_FOR_EXPLICIT_EGRI_AB_STUDY_OPEN"
            if ready
            else "HOLD_AA_INSTRUMENTATION_HEALTH_NOT_PROVEN"
        ),
        "preregistration": {
            "valid": True,
            "study_id": "egri-continuity-ab-v1",
            "common_baseline_fingerprint": BASELINE_FINGERPRINT,
            "treatment_identity": {
                "id": "egri-enrichment",
                "version": "1",
                "fingerprint": TREATMENT_FINGERPRINT,
            },
        },
        "aa_instrumentation_health": {
            "valid": ready,
            "baseline_fingerprint_matches": ready,
            "study_id_matches": ready,
        },
        "authority": {
            "p5_epoch_opened": False,
            "assignment_created": False,
            "egri_treatment_activated": False,
            "production_behavior_changed": False,
            "policy_promoted": False,
        },
    }


def outcome(
    *,
    effect: str = "MATERIAL_IMPROVEMENT",
    treatment_economics: int = 800_000,
    treatment_resolution: int = 9_600,
    treatment_ttpr: int = 80_000,
    overhead: int = 50_000,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "receipt_id": "egri-outcome-v1",
        "study_id": "egri-continuity-ab-v1",
        "treatment_id": "egri-enrichment",
        "common_baseline_fingerprint": BASELINE_FINGERPRINT,
        "treatment_fingerprint": TREATMENT_FINGERPRINT,
        "canonical_ledger_snapshot_sha256": "c" * 64,
        "source_identity_fingerprint": "d" * 64,
        "runtime_identity_fingerprint": "e" * 64,
        "analysis_fingerprint": "f" * 64,
        "prospective": True,
        "natural_workload_only": True,
        "source_tests_only": False,
        "synthetic_or_fixture_evidence": False,
        "assignment_before_arm_action_verified": True,
        "same_common_baseline_both_arms_verified": True,
        "same_continuity_semantics_both_arms_verified": True,
        "session_boundary_strata_complete": True,
        "study_integrity_pass": True,
        "quality_floor_pass": True,
        "authority_floor_pass": True,
        "preregistered_analysis_gate_pass": True,
        "qualifying_rows_control": 10,
        "qualifying_rows_treatment": 10,
        "minimum_qualifying_rows_per_arm": 5,
        "state_loss_count": 0,
        "duplicate_work_count": 0,
        "trusted_resolution_rate_basis_points_control": 9_500,
        "trusted_resolution_rate_basis_points_treatment": treatment_resolution,
        "ttpr_median_ms_control": 100_000,
        "ttpr_median_ms_treatment": treatment_ttpr,
        "accepted_result_economic_loss_microunits_control": 1_000_000,
        "accepted_result_economic_loss_microunits_treatment": treatment_economics,
        "capability_overhead_microunits": overhead,
        "material_economics_improvement_threshold_basis_points": 1_000,
        "preregistered_effect_classification": effect,
        "automatic_decision": False,
        "automatic_production_change": False,
    }


class TrustedResolutionDecisionGateTests(unittest.TestCase):
    def test_upstream_hold_cannot_be_bypassed_by_strong_outcome_receipt(self) -> None:
        result = trusted_resolution_decision_gate(
            tg11_readiness(ready=False),
            outcome_receipt=outcome(),
        )
        self.assertEqual(result["status"], "HOLD_TG11_EGRI_STUDY_NOT_READY")
        self.assertEqual(result["disposition"], "HOLD")
        self.assertFalse(result["authority"]["policy_promoted"])

    def test_missing_natural_outcome_defaults_to_hold(self) -> None:
        result = trusted_resolution_decision_gate(tg11_readiness())
        self.assertEqual(
            result["status"],
            "AWAITING_PROSPECTIVE_NATURAL_OUTCOME_RECEIPT",
        )
        self.assertEqual(result["disposition"], "HOLD")

    def test_source_test_or_synthetic_evidence_cannot_drive_disposition(self) -> None:
        invalid = outcome()
        invalid["source_tests_only"] = True
        invalid["synthetic_or_fixture_evidence"] = True
        result = trusted_resolution_decision_gate(
            tg11_readiness(),
            outcome_receipt=invalid,
        )
        self.assertEqual(result["status"], "HOLD_EVIDENCE_FLOORS_NOT_PROVEN")
        self.assertEqual(result["disposition"], "HOLD")

    def test_material_economics_with_zero_loss_and_duplicate_is_retain_candidate(self) -> None:
        result = trusted_resolution_decision_gate(
            tg11_readiness(),
            outcome_receipt=outcome(),
        )
        self.assertEqual(
            result["status"],
            "RETAIN_CANDIDATE_FOR_EXPLICIT_OPERATOR_REVIEW",
        )
        self.assertEqual(result["disposition"], "RETAIN")
        self.assertEqual(
            result["effect_projection"][
                "accepted_result_economics_improvement_basis_points"
            ],
            2_000,
        )
        self.assertFalse(result["authority"]["capability_retained"])
        self.assertTrue(result["authority"]["explicit_operator_acceptance_still_required"])

    def test_no_material_benefit_with_overhead_is_simplify_candidate(self) -> None:
        result = trusted_resolution_decision_gate(
            tg11_readiness(),
            outcome_receipt=outcome(
                effect="NO_MATERIAL_BENEFIT",
                treatment_economics=950_000,
                overhead=60_000,
            ),
        )
        self.assertEqual(
            result["status"],
            "SIMPLIFY_CANDIDATE_FOR_EXPLICIT_OPERATOR_REVIEW",
        )
        self.assertEqual(result["disposition"], "SIMPLIFY")
        self.assertTrue(result["decision_basis"]["bundle_level_only"])

    def test_negative_transfer_is_remove_candidate_but_does_not_remove(self) -> None:
        result = trusted_resolution_decision_gate(
            tg11_readiness(),
            outcome_receipt=outcome(
                effect="NEGATIVE_TRANSFER",
                treatment_economics=1_100_000,
                treatment_resolution=9_400,
                treatment_ttpr=110_000,
            ),
        )
        self.assertEqual(
            result["status"],
            "REMOVE_CANDIDATE_FOR_EXPLICIT_OPERATOR_REVIEW",
        )
        self.assertEqual(result["disposition"], "REMOVE")
        self.assertFalse(result["authority"]["capability_removed"])
        self.assertFalse(result["authority"]["production_behavior_changed"])

    def test_identity_mismatch_fails_before_effect_classification(self) -> None:
        mismatched = outcome()
        mismatched["treatment_fingerprint"] = "0" * 64
        result = trusted_resolution_decision_gate(
            tg11_readiness(),
            outcome_receipt=mismatched,
        )
        self.assertEqual(result["status"], "INVALID_STUDY_IDENTITY_BINDING")
        self.assertEqual(result["disposition"], "HOLD")

    def test_declared_material_effect_must_match_metrics(self) -> None:
        inconsistent = outcome(
            effect="MATERIAL_IMPROVEMENT",
            treatment_economics=980_000,
        )
        result = trusted_resolution_decision_gate(
            tg11_readiness(),
            outcome_receipt=inconsistent,
        )
        self.assertEqual(
            result["status"],
            "HOLD_EFFECT_CLASSIFICATION_NOT_SUPPORTED_BY_METRICS",
        )
        self.assertEqual(result["disposition"], "HOLD")


if __name__ == "__main__":
    unittest.main()
