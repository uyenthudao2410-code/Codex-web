from __future__ import annotations

import unittest

from coding_tools_mcp.p5_treatment import p5_controlled_treatment_plan, p5_implementation_contract


def readiness(*, ready: bool, signals: list[str] | None = None) -> dict[str, object]:
    return {
        "p5_controlled_treatment_may_be_opened": ready,
        "p5_automatic_start": False,
        "automatic_policy_activation": False,
        "predictive_validation": {"validated_signals": signals or []},
    }


class P5TreatmentTests(unittest.TestCase):
    def test_implementation_contract_is_always_dormant_and_nonautomatic(self) -> None:
        gated = p5_implementation_contract(treatment_readiness=False, validated_signals=[])
        ready = p5_implementation_contract(
            treatment_readiness=True,
            validated_signals=["expected_repair_risk"],
        )
        self.assertEqual(gated["implementation_status"], "OPEN_DORMANT")
        self.assertEqual(gated["treatment_status"], "GATED_OFF")
        self.assertEqual(ready["treatment_status"], "READY_FOR_EXPLICIT_ENROLLMENT")
        self.assertFalse(gated["treatment_active"])
        self.assertFalse(ready["treatment_active"])
        self.assertFalse(ready["automatic_start"])
        self.assertFalse(ready["shadow_recommendation_can_activate_treatment"])
        self.assertFalse(ready["cost_policy"]["missing_cost_is_zero"])
        self.assertEqual(ready["cost_policy"]["incomplete_car_status"], "unavailable")

    def test_live_readiness_gate_cannot_be_bypassed_by_task_controls(self) -> None:
        plan = p5_controlled_treatment_plan(
            readiness(ready=False, signals=[]),
            task_class="feature",
            stable_quality_oracle=True,
            causal_fix_gate_passed=True,
            oracle_settled_before_mutation=True,
            bounded_change_surface=True,
            explicit_enrollment_requested=True,
        )
        self.assertEqual(plan["decision"], "HOLD_CANONICAL_READINESS")
        self.assertFalse(plan["explicit_enrollment_may_proceed"])
        self.assertFalse(plan["treatment_active"])

    def test_ready_task_still_waits_for_explicit_enrollment(self) -> None:
        plan = p5_controlled_treatment_plan(
            readiness(ready=True, signals=["expected_repair_risk"]),
            task_class="bugfix",
            stable_quality_oracle=True,
            causal_fix_gate_passed=True,
            oracle_settled_before_mutation=True,
            bounded_change_surface=True,
        )
        self.assertEqual(plan["decision"], "READY_AWAITING_EXPLICIT_ENROLLMENT")
        self.assertTrue(plan["task_contract_passed"])
        self.assertFalse(plan["explicit_enrollment_may_proceed"])
        self.assertFalse(plan["treatment_active"])

    def test_explicit_ready_task_is_only_eligible_not_activated(self) -> None:
        plan = p5_controlled_treatment_plan(
            readiness(ready=True, signals=["expected_repair_risk"]),
            task_class="feature",
            stable_quality_oracle=True,
            causal_fix_gate_passed=True,
            oracle_settled_before_mutation=True,
            bounded_change_surface=True,
            explicit_enrollment_requested=True,
        )
        self.assertEqual(plan["decision"], "ELIGIBLE_FOR_EXPLICIT_CONTROLLED_ENROLLMENT")
        self.assertTrue(plan["explicit_enrollment_may_proceed"])
        self.assertFalse(plan["treatment_active"])
        self.assertFalse(plan["production_behavior_changed"])

    def test_missing_control_or_ineligible_workflow_fails_closed(self) -> None:
        missing_control = p5_controlled_treatment_plan(
            readiness(ready=True, signals=["expected_repair_risk"]),
            task_class="feature",
            stable_quality_oracle=True,
            causal_fix_gate_passed=False,
            oracle_settled_before_mutation=True,
            bounded_change_surface=True,
            explicit_enrollment_requested=True,
        )
        ineligible = p5_controlled_treatment_plan(
            readiness(ready=True, signals=["expected_repair_risk"]),
            task_class="diagnose",
            stable_quality_oracle=True,
            causal_fix_gate_passed=True,
            oracle_settled_before_mutation=True,
            bounded_change_surface=True,
            explicit_enrollment_requested=True,
        )
        self.assertEqual(missing_control["decision"], "HOLD_TASK_CONTRACT")
        self.assertIn("causal_fix_gate_passed", missing_control["hold_reasons"])
        self.assertFalse(missing_control["explicit_enrollment_may_proceed"])
        self.assertEqual(ineligible["decision"], "HOLD_TASK_CONTRACT")
        self.assertIn("eligible_feature_or_bugfix", ineligible["hold_reasons"])
        self.assertFalse(ineligible["explicit_enrollment_may_proceed"])


if __name__ == "__main__":
    unittest.main()
