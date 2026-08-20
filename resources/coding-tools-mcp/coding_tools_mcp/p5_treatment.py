from __future__ import annotations

from typing import Any


P5_ELIGIBLE_WORKFLOWS = frozenset({"feature", "bugfix"})


def p5_implementation_contract(
    *,
    treatment_readiness: bool,
    validated_signals: list[str],
) -> dict[str, Any]:
    signals = sorted({str(item).strip() for item in validated_signals if str(item).strip()})
    return {
        "schema_version": 1,
        "mode": "controlled_rework_reduction_ab_v1",
        "implementation_status": "OPEN_DORMANT",
        "treatment_status": "READY_FOR_EXPLICIT_ENROLLMENT" if treatment_readiness else "GATED_OFF",
        "treatment_active": False,
        "readiness_gate_passed": bool(treatment_readiness),
        "automatic_start": False,
        "explicit_enrollment_only": True,
        "shadow_recommendation_can_activate_treatment": False,
        "eligible_workflows": sorted(P5_ELIGIBLE_WORKFLOWS),
        "validated_predictive_signals": signals,
        "treatment_controls": {
            "causal_fix_gate_required": True,
            "oracle_settlement_before_mutation_required": True,
            "bounded_change_surface_required": True,
            "stable_quality_oracle_required": True,
        },
        "promotion_requirements": {
            "quality_floor_must_hold": True,
            "repair_or_replan_must_not_worsen": True,
            "ttar_must_improve_materially": True,
            "car_must_improve_materially_when_available": True,
        },
        "cost_policy": {
            "car_requires_complete_total_cost_coverage": True,
            "incomplete_car_status": "unavailable",
            "missing_cost_is_zero": False,
        },
        "global_server_first": False,
        "content_free": True,
    }


def p5_controlled_treatment_plan(
    readiness: dict[str, Any],
    *,
    task_class: str,
    stable_quality_oracle: bool = False,
    causal_fix_gate_passed: bool = False,
    oracle_settled_before_mutation: bool = False,
    bounded_change_surface: bool = False,
    explicit_enrollment_requested: bool = False,
) -> dict[str, Any]:
    validation = readiness.get("predictive_validation")
    if not isinstance(validation, dict):
        validation = {}
    validated = validation.get("validated_signals")
    validated_signals = validated if isinstance(validated, list) else []
    treatment_readiness = readiness.get("p5_controlled_treatment_may_be_opened") is True
    workflow = str(task_class or "").strip().lower()
    requirements = {
        "canonical_p5_readiness": treatment_readiness,
        "eligible_feature_or_bugfix": workflow in P5_ELIGIBLE_WORKFLOWS,
        "stable_quality_oracle": stable_quality_oracle is True,
        "causal_fix_gate_passed": causal_fix_gate_passed is True,
        "oracle_settled_before_mutation": oracle_settled_before_mutation is True,
        "bounded_change_surface": bounded_change_surface is True,
        "explicit_enrollment_requested": explicit_enrollment_requested is True,
    }
    task_contract_passed = all(
        requirements[key]
        for key in (
            "eligible_feature_or_bugfix",
            "stable_quality_oracle",
            "causal_fix_gate_passed",
            "oracle_settled_before_mutation",
            "bounded_change_surface",
        )
    )
    may_proceed = bool(treatment_readiness and task_contract_passed and explicit_enrollment_requested)
    if not treatment_readiness:
        decision = "HOLD_CANONICAL_READINESS"
    elif not task_contract_passed:
        decision = "HOLD_TASK_CONTRACT"
    elif not explicit_enrollment_requested:
        decision = "READY_AWAITING_EXPLICIT_ENROLLMENT"
    else:
        decision = "ELIGIBLE_FOR_EXPLICIT_CONTROLLED_ENROLLMENT"
    return {
        "schema_version": 1,
        "mode": "controlled_rework_reduction_ab_v1",
        "implementation_status": "OPEN_DORMANT",
        "decision": decision,
        "task_class": workflow or "unknown",
        "requirements": requirements,
        "hold_reasons": [key for key, passed in requirements.items() if not passed],
        "task_contract_passed": task_contract_passed,
        "explicit_enrollment_may_proceed": may_proceed,
        "treatment_active": False,
        "automatic_start": False,
        "production_behavior_changed": False,
        "validated_predictive_signals": sorted({str(item).strip() for item in validated_signals if str(item).strip()}),
        "implementation_contract": p5_implementation_contract(
            treatment_readiness=treatment_readiness,
            validated_signals=validated_signals,
        ),
        "content_free": True,
    }
