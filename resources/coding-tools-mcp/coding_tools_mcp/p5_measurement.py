from __future__ import annotations

from typing import Any


def _metric(value: Any) -> int | float | None:
    if isinstance(value, bool):
        return None
    return value if isinstance(value, (int, float)) else None


def _car_snapshot(organic_rework: dict[str, Any]) -> dict[str, Any]:
    cost = organic_rework.get("accepted_result_cost")
    if not isinstance(cost, dict):
        cost = {}
    first_pass = _metric(cost.get("first_pass_p50"))
    repaired = _metric(cost.get("repaired_p50"))
    coverage_complete = cost.get("coverage_complete") is True
    available = bool(coverage_complete and first_pass is not None and repaired is not None)
    return {
        "status": "available" if available else "unavailable",
        "coverage_complete": coverage_complete,
        "first_pass_p50": first_pass if available else None,
        "repaired_p50": repaired if available else None,
        "repaired_to_first_pass_p50_multiplier": (
            round(repaired / first_pass, 6)
            if available and first_pass not in (None, 0) and repaired is not None
            else None
        ),
        "missing_cost_is_zero": False,
        "reason": (
            "complete_accepted_result_cost_coverage"
            if available
            else "complete_accepted_result_cost_coverage_required"
        ),
    }


def p5_baseline_snapshot(
    readiness: dict[str, Any],
    organic_rework: dict[str, Any],
) -> dict[str, Any]:
    tta = organic_rework.get("tta_ms")
    if not isinstance(tta, dict):
        tta = {}
    implementation = readiness.get("p5_implementation")
    if not isinstance(implementation, dict):
        implementation = {}
    accepted_runs = _metric(organic_rework.get("accepted_runs"))
    return {
        "schema_version": 2,
        "mode": "prospective_rework_experiment_v2",
        "implementation_status": str(implementation.get("implementation_status") or "IMPLEMENTED_GATED"),
        "baseline_kind": "organic_rework_observational_v1",
        "baseline_observed": bool(isinstance(accepted_runs, (int, float)) and accepted_runs > 0),
        "p5_experiment_start_ready": readiness.get("p5_experiment_start_ready") is True,
        "p5_experiment_epoch_lifecycle": str(readiness.get("p5_experiment_epoch_lifecycle") or "NOT_READY"),
        "legacy_predictive_treatment_readiness": readiness.get("p5_legacy_predictive_treatment_readiness") is True,
        "canonical_readiness_passed": readiness.get("p5_experiment_start_ready") is True,
        "treatment_started": False,
        "samples_created": False,
        "control_observations_created": 0,
        "treatment_observations_created": 0,
        "automatic_start": False,
        "production_behavior_changed": False,
        "observational_baseline": {
            "accepted_runs": accepted_runs,
            "first_pass_accepted": _metric(organic_rework.get("first_pass_accepted")),
            "repaired_accepted": _metric(organic_rework.get("repaired_accepted")),
            "first_pass_rate": _metric(organic_rework.get("first_pass_rate")),
            "repaired_rate": _metric(organic_rework.get("repaired_rate")),
            "replan_count": _metric((organic_rework.get("repair") or {}).get("replan_count"))
            if isinstance(organic_rework.get("repair"), dict)
            else None,
            "ttar_ms": {
                "first_pass_p50": _metric(tta.get("first_pass_p50")),
                "first_pass_p90": _metric(tta.get("first_pass_p90")),
                "repaired_p50": _metric(tta.get("repaired_p50")),
                "repaired_p90": _metric(tta.get("repaired_p90")),
                "repaired_to_first_pass_p50_multiplier": _metric(
                    tta.get("repaired_to_first_pass_p50_multiplier")
                ),
                "repaired_to_first_pass_p90_multiplier": _metric(
                    tta.get("repaired_to_first_pass_p90_multiplier")
                ),
            },
            "car": _car_snapshot(organic_rework),
        },
        "promotion_evaluation": {
            "status": "NOT_STARTED",
            "quality_floor_evidence_status": "not_collected",
            "repair_or_replan_no_harm_evidence_status": "not_collected",
            "ttar_comparison_status": "not_collected",
            "car_comparison_status": "not_collected",
            "materiality_threshold_status": "unspecified_requires_explicit_experiment_contract",
            "promotion_decision": None,
        },
        "evidence_policy": {
            "observational_baseline_is_treatment_evidence": False,
            "baseline_snapshot_creates_samples": False,
            "baseline_snapshot_creates_assignments": False,
            "organic_baseline_joins_p5_itt": False,
            "missing_cost_is_zero": False,
            "synthetic_promotion_allowed": False,
        },
        "content_free": True,
    }
