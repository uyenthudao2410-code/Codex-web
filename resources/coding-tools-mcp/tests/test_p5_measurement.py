from __future__ import annotations

import unittest

from coding_tools_mcp.p5_measurement import p5_baseline_snapshot


def readiness(*, ready: bool) -> dict[str, object]:
    return {
        "p5_controlled_treatment_may_be_opened": ready,
        "p5_implementation": {
            "implementation_status": "OPEN_DORMANT",
            "treatment_status": "READY_FOR_EXPLICIT_ENROLLMENT" if ready else "GATED_OFF",
            "treatment_active": False,
        },
    }


def rework() -> dict[str, object]:
    return {
        "accepted_runs": 100,
        "first_pass_accepted": 60,
        "repaired_accepted": 40,
        "first_pass_rate": 0.6,
        "repaired_rate": 0.4,
        "repair": {"replan_count": 55},
        "tta_ms": {
            "first_pass_p50": 100.0,
            "first_pass_p90": 200.0,
            "repaired_p50": 450.0,
            "repaired_p90": 900.0,
            "repaired_to_first_pass_p50_multiplier": 4.5,
            "repaired_to_first_pass_p90_multiplier": 4.5,
        },
    }


class P5MeasurementTests(unittest.TestCase):
    def test_observational_baseline_does_not_start_treatment_or_create_samples(self) -> None:
        report = p5_baseline_snapshot(readiness(ready=False), rework())
        self.assertTrue(report["baseline_observed"])
        self.assertFalse(report["canonical_readiness_passed"])
        self.assertFalse(report["treatment_started"])
        self.assertFalse(report["samples_created"])
        self.assertEqual(report["control_observations_created"], 0)
        self.assertEqual(report["treatment_observations_created"], 0)
        self.assertFalse(report["production_behavior_changed"])
        self.assertEqual(report["promotion_evaluation"]["status"], "NOT_STARTED")

    def test_rework_and_ttar_metrics_are_preserved_without_promotion_inference(self) -> None:
        report = p5_baseline_snapshot(readiness(ready=False), rework())
        baseline = report["observational_baseline"]
        self.assertEqual(baseline["accepted_runs"], 100)
        self.assertEqual(baseline["first_pass_rate"], 0.6)
        self.assertEqual(baseline["repaired_rate"], 0.4)
        self.assertEqual(baseline["replan_count"], 55)
        self.assertEqual(baseline["ttar_ms"]["repaired_to_first_pass_p50_multiplier"], 4.5)
        self.assertIsNone(report["promotion_evaluation"]["promotion_decision"])
        self.assertEqual(
            report["promotion_evaluation"]["materiality_threshold_status"],
            "unspecified_requires_explicit_experiment_contract",
        )

    def test_missing_cost_coverage_keeps_car_unavailable_and_never_zero(self) -> None:
        report = p5_baseline_snapshot(readiness(ready=False), rework())
        car = report["observational_baseline"]["car"]
        self.assertEqual(car["status"], "unavailable")
        self.assertFalse(car["coverage_complete"])
        self.assertIsNone(car["first_pass_p50"])
        self.assertIsNone(car["repaired_p50"])
        self.assertFalse(car["missing_cost_is_zero"])

    def test_complete_cost_coverage_exposes_car_without_making_promotion_decision(self) -> None:
        organic = rework()
        organic["accepted_result_cost"] = {
            "coverage_complete": True,
            "first_pass_p50": 2.0,
            "repaired_p50": 5.0,
        }
        report = p5_baseline_snapshot(readiness(ready=True), organic)
        car = report["observational_baseline"]["car"]
        self.assertEqual(car["status"], "available")
        self.assertEqual(car["first_pass_p50"], 2.0)
        self.assertEqual(car["repaired_p50"], 5.0)
        self.assertEqual(car["repaired_to_first_pass_p50_multiplier"], 2.5)
        self.assertIsNone(report["promotion_evaluation"]["promotion_decision"])
        self.assertFalse(report["treatment_started"])
        self.assertFalse(report["samples_created"])

    def test_boolean_values_are_not_accepted_as_numeric_metrics(self) -> None:
        organic = rework()
        organic["accepted_runs"] = True
        report = p5_baseline_snapshot(readiness(ready=False), organic)
        self.assertFalse(report["baseline_observed"])
        self.assertIsNone(report["observational_baseline"]["accepted_runs"])


if __name__ == "__main__":
    unittest.main()
