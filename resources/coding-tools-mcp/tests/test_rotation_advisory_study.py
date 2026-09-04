from __future__ import annotations

import unittest

from coding_tools_mcp.natural_problem_cohort import NATURAL_PROBLEM_COHORT_SCHEMA_VERSION
from coding_tools_mcp.rotation_advisory_study import rotation_advisory_study_readiness


def cohort(*, safe: bool) -> dict[str, object]:
    return {
        "schema_version": NATURAL_PROBLEM_COHORT_SCHEMA_VERSION,
        "status": "DESCRIPTIVE_COHORT_READY" if safe else "DESCRIPTIVE_COHORT_CONTINUITY_INCOMPLETE",
        "policy": {
            "read_only_immutable_snapshot_required": True,
            "no_writer_problem_run_wave_epoch_or_schema_activation": True,
            "descriptive_cohort_is_not_causal_evidence": True,
        },
        "tg10_manual_continuity_safety_gate": {
            "status": "PASS" if safe else "HOLD",
            "manual_continuity_proven_safe": safe,
        },
    }


def preregistration() -> dict[str, object]:
    return {
        "schema_version": 1,
        "study_id": "rotation-advisory-v1",
        "policy_id": "context-pressure-advisory",
        "policy_version": "1",
        "policy_fingerprint": "a" * 64,
        "common_baseline_fingerprint": "b" * 64,
        "strata": [
            "problem_task_class",
            "execution_route",
            "quality_oracle",
            "source_identity",
            "session_boundary_condition",
        ],
        "outcomes": [
            "ttpr",
            "resume_success",
            "wrong_frame_or_reopen",
            "controller_lag_or_control_gap",
            "total_resource_economics",
            "user_or_operator_burden",
        ],
        "minimum_qualifying_rows_per_arm": 5,
        "assignment_before_arm_action": True,
        "same_continuity_semantics_both_arms": True,
        "automatic_hard_rotation": False,
        "automatic_promotion": False,
    }


class RotationAdvisoryStudyTests(unittest.TestCase):
    def test_manual_continuity_hold_prevents_preregistration_from_opening_study(self) -> None:
        result = rotation_advisory_study_readiness(
            cohort(safe=False), preregistration=preregistration()
        )
        self.assertEqual(result["status"], "HOLD_MANUAL_CONTINUITY_NOT_PROVEN")
        self.assertFalse(result["authority"]["study_epoch_opened"])
        self.assertFalse(result["authority"]["assignment_created"])
        self.assertFalse(result["authority"]["rotation_recommendation_emitted"])

    def test_safe_manual_cohort_still_requires_prospective_preregistration(self) -> None:
        result = rotation_advisory_study_readiness(cohort(safe=True))
        self.assertEqual(result["status"], "AWAITING_PROSPECTIVE_PREREGISTRATION")
        self.assertEqual(result["preregistration"]["status"], "MISSING")
        self.assertTrue(result["authority"]["explicit_operator_study_open_still_required"])

    def test_valid_preregistration_only_reaches_explicit_open_readiness(self) -> None:
        result = rotation_advisory_study_readiness(
            cohort(safe=True), preregistration=preregistration()
        )
        self.assertEqual(result["status"], "READY_FOR_EXPLICIT_OPERATOR_STUDY_OPEN")
        self.assertTrue(result["preregistration"]["valid"])
        self.assertFalse(result["authority"]["study_epoch_opened"])
        self.assertFalse(result["study_contract"]["automatic_hard_rotation"])
        self.assertFalse(
            result["study_contract"]["promotion_floors"]["automatic_promotion"]
        )

    def test_invalid_preregistration_fails_closed(self) -> None:
        invalid = preregistration()
        invalid["automatic_hard_rotation"] = True
        invalid["strata"] = ["problem_task_class"]
        result = rotation_advisory_study_readiness(
            cohort(safe=True), preregistration=invalid
        )
        self.assertEqual(result["status"], "INVALID_PROSPECTIVE_PREREGISTRATION")
        self.assertIn(
            "automatic_hard_rotation_must_be_false",
            result["preregistration"]["reason_codes"],
        )
        self.assertIn(
            "required_strata_incomplete", result["preregistration"]["reason_codes"]
        )


if __name__ == "__main__":
    unittest.main()
