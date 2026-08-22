from __future__ import annotations

import unittest

from coding_tools_mcp.p5_treatment import p5_controlled_treatment_plan, p5_implementation_contract


def readiness(*, start_ready: bool, lifecycle: str = "NOT_READY", legacy: bool = False) -> dict[str, object]:
    return {
        "p5_experiment_start_ready": start_ready,
        "p5_experiment_epoch_lifecycle": lifecycle,
        "p5_legacy_predictive_treatment_readiness": legacy,
        "predictive_validation": {"validated_signals": []},
    }


def eligible_kwargs() -> dict[str, bool]:
    return {
        "stable_quality_oracle": True,
        "bounded_change_surface": True,
        "exact_source_identity_available": True,
        "no_conflicting_writer_or_lease": True,
        "no_stale_or_recovery_state": True,
        "representative_natural_task": True,
        "not_high_risk": True,
        "common_execution_contract_available": True,
    }


class P5TreatmentTests(unittest.TestCase):
    def test_implementation_contract_is_gated_and_never_automatic(self) -> None:
        contract = p5_implementation_contract(experiment_start_ready=False, validated_signals=[])
        self.assertEqual(contract["implementation_status"], "IMPLEMENTED_GATED")
        self.assertEqual(contract["treatment_status"], "GATED_OFF")
        self.assertFalse(contract["epoch_active"])
        self.assertFalse(contract["treatment_active"])
        self.assertFalse(contract["automatic_start"])
        self.assertFalse(contract["automatic_production_promotion"])
        self.assertFalse(contract["shadow_recommendation_can_activate_treatment"])
        self.assertFalse(contract["cost_policy"]["missing_cost_is_zero"])

    def test_p4_c_legacy_signal_does_not_open_or_activate_experiment(self) -> None:
        contract = p5_implementation_contract(
            experiment_start_ready=False,
            treatment_readiness=True,
            validated_signals=["expected_repair_risk"],
        )
        self.assertTrue(contract["legacy_predictive_treatment_readiness"])
        self.assertFalse(contract["experiment_start_ready"])
        self.assertFalse(contract["epoch_active"])
        self.assertEqual(contract["treatment_status"], "GATED_OFF")

    def test_ready_eligible_task_waits_for_explicit_enrollment_and_epoch(self) -> None:
        plan = p5_controlled_treatment_plan(
            readiness(start_ready=True), task_class="bugfix", **eligible_kwargs()
        )
        self.assertEqual(plan["decision"], "ELIGIBLE_AWAITING_EXPLICIT_ENROLLMENT")
        self.assertTrue(plan["task_eligible_before_arm_reveal"])
        self.assertFalse(plan["explicit_enrollment_may_proceed"])
        self.assertFalse(plan["immutable_assignment_may_proceed"])
        requested = p5_controlled_treatment_plan(
            readiness(start_ready=True),
            task_class="bugfix",
            explicit_enrollment_requested=True,
            **eligible_kwargs(),
        )
        self.assertEqual(requested["decision"], "ELIGIBLE_AWAITING_EXPLICIT_EPOCH_OPEN")
        self.assertFalse(requested["explicit_enrollment_may_proceed"])
        self.assertFalse(requested["immutable_assignment_may_proceed"])

    def test_active_epoch_allows_assignment_without_p4_c_or_preassignment_treatment_bundle(self) -> None:
        plan = p5_controlled_treatment_plan(
            readiness(start_ready=True, lifecycle="EPOCH_ACTIVE", legacy=False),
            task_class="feature",
            explicit_enrollment_requested=True,
            causal_fix_gate_passed=False,
            oracle_settled_before_mutation=False,
            **eligible_kwargs(),
        )
        self.assertEqual(plan["decision"], "ELIGIBLE_FOR_IMMUTABLE_ASSIGNMENT")
        self.assertTrue(plan["immutable_assignment_may_proceed"])
        self.assertTrue(plan["deprecated_task_treatment_inputs_ignored"]["causal_fix_gate_passed"])
        self.assertFalse(plan["treatment_active"])

    def test_ineligible_workflow_fails_closed_before_arm_reveal(self) -> None:
        plan = p5_controlled_treatment_plan(
            readiness(start_ready=True, lifecycle="EPOCH_ACTIVE"),
            task_class="diagnose",
            explicit_enrollment_requested=True,
            **eligible_kwargs(),
        )
        self.assertEqual(plan["decision"], "HOLD_ARM_NEUTRAL_ELIGIBILITY")
        self.assertIn("eligible_feature_or_bugfix", plan["hold_reasons"])
        self.assertFalse(plan["immutable_assignment_may_proceed"])


if __name__ == "__main__":
    unittest.main()
