from __future__ import annotations

"""Read-only P5 enrollment planning.

The functions here do not open an epoch, choose an arm, or change production
behavior. Those consequential actions are owned by the canonical ledger once
an operator has supplied an exact frozen manifest and secret-backed assignment
seed. Keeping this planner arm-neutral prevents a P4-C score or a task-local
recommendation from becoming a hidden treatment trigger.
"""

from typing import Any

from .p5_experiment import P5_ELIGIBLE_WORKFLOWS


def p5_implementation_contract(
    *,
    experiment_start_ready: bool = False,
    epoch_lifecycle: str = "NOT_READY",
    validated_signals: list[str] | None = None,
    treatment_readiness: bool | None = None,
) -> dict[str, Any]:
    """Project source capability separately from the live experiment state.

    ``treatment_readiness`` is retained solely as an explicitly named legacy
    P4-C/P5 coupling signal. It never grants activation or assignment rights.
    """

    signals = sorted({str(item).strip() for item in (validated_signals or []) if str(item).strip()})
    lifecycle = str(epoch_lifecycle or "NOT_READY").strip().upper()
    if lifecycle not in {"NOT_READY", "START_READY", "EPOCH_ACTIVE", "EPOCH_PAUSED", "EPOCH_CLOSED", "EPOCH_HARD_STOPPED"}:
        lifecycle = "NOT_READY"
    legacy_ready = treatment_readiness is True
    return {
        "schema_version": 2,
        "mode": "prospective_rework_experiment_v2",
        "source_implementation_status": "IMPLEMENTED_GATED",
        "implementation_status": "IMPLEMENTED_GATED",
        "experiment_start_ready": experiment_start_ready is True,
        "experiment_epoch_lifecycle": lifecycle,
        "epoch_active": lifecycle == "EPOCH_ACTIVE",
        "treatment_status": (
            "EPOCH_ACTIVE" if lifecycle == "EPOCH_ACTIVE"
            else "EPOCH_PAUSED" if lifecycle == "EPOCH_PAUSED"
            else "START_READY_AWAITING_EXPLICIT_OPERATOR_OPEN" if experiment_start_ready is True
            else "GATED_OFF"
        ),
        "treatment_active": False,
        "automatic_start": False,
        "automatic_production_promotion": False,
        "explicit_operator_epoch_open_required": True,
        "explicit_enrollment_only": True,
        "shadow_recommendation_can_activate_treatment": False,
        "eligible_workflows": sorted(P5_ELIGIBLE_WORKFLOWS),
        "validated_predictive_signals": signals,
        "legacy_predictive_treatment_readiness": legacy_ready,
        "legacy_predictive_treatment_readiness_deprecated": True,
        "treatment_controls": {
            "causal_fix_gate_required_for_treatment_arm": True,
            "oracle_settlement_before_mutation_required": True,
            "bounded_change_surface_required": True,
            "stable_quality_oracle_required": True,
            "common_execution_contract_required_for_both_arms": True,
            "assignment_before_arm_action_or_write_required": True,
        },
        "promotion_requirements": {
            "causal_efficacy_required": True,
            "quality_floor_must_hold": True,
            "repair_or_replan_must_not_worsen": True,
            "restricted_time_economics_required": True,
            "accepted_result_resource_economics_required": True,
            "resource_overhead_noninferiority_required": True,
            "monetary_cost_noninferiority_when_complete": True,
            "separate_operator_release_acceptance_required": True,
        },
        "cost_policy": {
            "car_requires_complete_total_cost_coverage": True,
            "incomplete_car_status": "unavailable",
            "missing_cost_is_zero": False,
            "partial_resource_vector_remains_descriptive": True,
            "estimated_wait_is_not_provider_billing": True,
        },
        "global_server_first": False,
        "content_free": True,
    }


def p5_controlled_treatment_plan(
    readiness: dict[str, Any],
    *,
    task_class: str,
    stable_quality_oracle: bool = False,
    bounded_change_surface: bool = False,
    exact_source_identity_available: bool = False,
    no_conflicting_writer_or_lease: bool = False,
    no_stale_or_recovery_state: bool = False,
    representative_natural_task: bool = False,
    not_high_risk: bool = False,
    common_execution_contract_available: bool = False,
    explicit_enrollment_requested: bool = False,
    # Deprecated aliases retained for callers of the prior planner. They are
    # deliberately not eligibility gates because the causal-fix bundle belongs
    # only to a treatment arm after immutable assignment.
    causal_fix_gate_passed: bool | None = None,
    oracle_settled_before_mutation: bool | None = None,
) -> dict[str, Any]:
    workflow = str(task_class or "").strip().lower()
    start_ready = readiness.get("p5_experiment_start_ready") is True
    lifecycle = str(readiness.get("p5_experiment_epoch_lifecycle") or "NOT_READY").strip().upper()
    requirements = {
        "experiment_start_ready": start_ready,
        "eligible_feature_or_bugfix": workflow in P5_ELIGIBLE_WORKFLOWS,
        "representative_natural_task": representative_natural_task is True,
        "exact_source_identity_available": exact_source_identity_available is True,
        "stable_quality_oracle": stable_quality_oracle is True,
        "bounded_change_surface": bounded_change_surface is True,
        "no_conflicting_writer_or_lease": no_conflicting_writer_or_lease is True,
        "no_stale_or_recovery_state": no_stale_or_recovery_state is True,
        "not_high_risk": not_high_risk is True,
        "common_execution_contract_available": common_execution_contract_available is True,
    }
    task_eligible = all(value for key, value in requirements.items() if key != "experiment_start_ready")
    epoch_active = lifecycle == "EPOCH_ACTIVE"
    enrollment_may_proceed = bool(epoch_active and task_eligible and explicit_enrollment_requested is True)
    assignment_may_proceed = enrollment_may_proceed
    if not task_eligible:
        decision = "HOLD_ARM_NEUTRAL_ELIGIBILITY"
    elif explicit_enrollment_requested is not True:
        decision = "ELIGIBLE_AWAITING_EXPLICIT_ENROLLMENT"
    elif lifecycle == "EPOCH_PAUSED":
        decision = "ELIGIBLE_EPOCH_PAUSED"
    elif not epoch_active:
        decision = "ELIGIBLE_AWAITING_EXPLICIT_EPOCH_OPEN"
    else:
        decision = "ELIGIBLE_FOR_IMMUTABLE_ASSIGNMENT"
    predictive = readiness.get("predictive_validation")
    signals = predictive.get("validated_signals") if isinstance(predictive, dict) else []
    return {
        "schema_version": 2,
        "mode": "prospective_rework_experiment_v2",
        "implementation_status": "IMPLEMENTED_GATED",
        "decision": decision,
        "task_class": workflow or "unknown",
        "requirements": requirements,
        "hold_reasons": [key for key, passed in requirements.items() if not passed],
        "task_eligible_before_arm_reveal": task_eligible,
        "explicit_enrollment_may_proceed": enrollment_may_proceed,
        "immutable_assignment_may_proceed": assignment_may_proceed,
        "experiment_epoch_lifecycle": lifecycle,
        "treatment_active": False,
        "automatic_start": False,
        "production_behavior_changed": False,
        "deprecated_task_treatment_inputs_ignored": {
            "causal_fix_gate_passed": causal_fix_gate_passed is not None,
            "oracle_settled_before_mutation": oracle_settled_before_mutation is not None,
        },
        "implementation_contract": p5_implementation_contract(
            experiment_start_ready=start_ready,
            epoch_lifecycle=lifecycle,
            validated_signals=signals if isinstance(signals, list) else [],
            treatment_readiness=readiness.get("p5_legacy_predictive_treatment_readiness") is True,
        ),
        "content_free": True,
    }
