"""Arm-neutral TG10 readiness gate for a prospective rotation advisory study."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .natural_problem_cohort import NATURAL_PROBLEM_COHORT_SCHEMA_VERSION


ROTATION_ADVISORY_STUDY_SCHEMA_VERSION = 1
ROTATION_ADVISORY_PREREGISTRATION_SCHEMA_VERSION = 1
_REQUIRED_STRATA = frozenset(
    {
        "problem_task_class",
        "execution_route",
        "quality_oracle",
        "source_identity",
        "session_boundary_condition",
    }
)
_REQUIRED_OUTCOMES = frozenset(
    {
        "ttpr",
        "resume_success",
        "wrong_frame_or_reopen",
        "controller_lag_or_control_gap",
        "total_resource_economics",
        "user_or_operator_burden",
    }
)


def _text(value: Any) -> str:
    return str(value or "").strip()


def _digest(value: Any) -> bool:
    text = _text(value).lower()
    return len(text) == 64 and all(character in "0123456789abcdef" for character in text)


def _contract() -> dict[str, Any]:
    return {
        "study_kind": "prospective_rotation_advisory_policy_study",
        "arms": {
            "control": "manual_rotation_only",
            "treatment": "advisory_rotation_recommendation",
        },
        "automatic_hard_rotation": False,
        "hard_rotation_is_later_separate_policy": True,
        "inputs": {
            "exact_context_and_usage_when_available": True,
            "otherwise_only_preregistered_heuristic_policy": True,
            "required_strata": sorted(_REQUIRED_STRATA),
        },
        "common_baseline": [
            "goal_pursuit_projector",
            "controller_knowledge_checkpoint_and_recovery",
            "continuity_core",
            "same_role_resume",
            "ui_independent_execution",
            "same_usage_and_economics_instrumentation",
        ],
        "outcomes": sorted(_REQUIRED_OUTCOMES),
        "promotion_floors": {
            "qualifying_sample_required": True,
            "state_loss_must_equal_zero": True,
            "duplicate_work_must_equal_zero": True,
            "outcome_economics_must_improve_materially": True,
            "automatic_promotion": False,
            "separate_operator_acceptance_required": True,
        },
    }


def _validate_preregistration(value: Mapping[str, Any] | None) -> dict[str, Any]:
    if value is None:
        return {
            "status": "MISSING",
            "valid": False,
            "reason_codes": ["prospective_preregistration_missing"],
            "study_id": None,
            "policy_fingerprint": None,
        }
    reasons: list[str] = []
    allowed = {
        "schema_version",
        "study_id",
        "policy_id",
        "policy_version",
        "policy_fingerprint",
        "common_baseline_fingerprint",
        "strata",
        "outcomes",
        "minimum_qualifying_rows_per_arm",
        "assignment_before_arm_action",
        "same_continuity_semantics_both_arms",
        "automatic_hard_rotation",
        "automatic_promotion",
    }
    if set(value) != allowed:
        reasons.append("preregistration_fields_not_exact")
    if value.get("schema_version") != ROTATION_ADVISORY_PREREGISTRATION_SCHEMA_VERSION:
        reasons.append("preregistration_schema_version_invalid")
    for field in ("study_id", "policy_id", "policy_version"):
        text = _text(value.get(field))
        if not text or len(text) > 128:
            reasons.append(f"{field}_invalid")
    if not _digest(value.get("policy_fingerprint")):
        reasons.append("policy_fingerprint_invalid")
    if not _digest(value.get("common_baseline_fingerprint")):
        reasons.append("common_baseline_fingerprint_invalid")
    strata = value.get("strata")
    if not isinstance(strata, list) or set(strata) != _REQUIRED_STRATA:
        reasons.append("required_strata_incomplete")
    outcomes = value.get("outcomes")
    if not isinstance(outcomes, list) or set(outcomes) != _REQUIRED_OUTCOMES:
        reasons.append("required_outcomes_incomplete")
    minimum = value.get("minimum_qualifying_rows_per_arm")
    if isinstance(minimum, bool) or not isinstance(minimum, int) or minimum < 1:
        reasons.append("minimum_qualifying_rows_per_arm_invalid")
    for field in ("assignment_before_arm_action", "same_continuity_semantics_both_arms"):
        if value.get(field) is not True:
            reasons.append(f"{field}_must_be_true")
    for field in ("automatic_hard_rotation", "automatic_promotion"):
        if value.get(field) is not False:
            reasons.append(f"{field}_must_be_false")
    return {
        "status": "VALID" if not reasons else "INVALID",
        "valid": not reasons,
        "reason_codes": reasons,
        "study_id": _text(value.get("study_id")) or None,
        "policy_fingerprint": _text(value.get("policy_fingerprint")).lower() or None,
        "content_free_contract": True,
    }


def rotation_advisory_study_readiness(
    natural_cohort: Mapping[str, Any],
    *,
    preregistration: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return readiness only; never assign an arm or open an experiment epoch."""

    if not isinstance(natural_cohort, Mapping):
        raise TypeError("natural_cohort must be a TG9 report mapping")
    tg9_schema_ok = natural_cohort.get("schema_version") == NATURAL_PROBLEM_COHORT_SCHEMA_VERSION
    policy = natural_cohort.get("policy") if isinstance(natural_cohort.get("policy"), Mapping) else {}
    tg9_read_only = (
        policy.get("read_only_immutable_snapshot_required") is True
        and policy.get("no_writer_problem_run_wave_epoch_or_schema_activation") is True
        and policy.get("descriptive_cohort_is_not_causal_evidence") is True
    )
    tg9_gate = (
        natural_cohort.get("tg10_manual_continuity_safety_gate")
        if isinstance(natural_cohort.get("tg10_manual_continuity_safety_gate"), Mapping)
        else {}
    )
    manual_safe = (
        tg9_schema_ok
        and tg9_read_only
        and tg9_gate.get("manual_continuity_proven_safe") is True
        and tg9_gate.get("status") == "PASS"
    )
    prereg = _validate_preregistration(preregistration)
    gates = {
        "tg9_schema": "PASS" if tg9_schema_ok else "FAIL",
        "tg9_read_only_descriptive_contract": "PASS" if tg9_read_only else "FAIL",
        "manual_continuity_safe": "PASS" if manual_safe else "HOLD",
        "prospective_preregistration": prereg["status"],
        "explicit_operator_study_open": "REQUIRED",
    }
    if not tg9_schema_ok or not tg9_read_only:
        status = "INVALID_TG9_REPORT"
    elif not manual_safe:
        status = "HOLD_MANUAL_CONTINUITY_NOT_PROVEN"
    elif preregistration is None:
        status = "AWAITING_PROSPECTIVE_PREREGISTRATION"
    elif not prereg["valid"]:
        status = "INVALID_PROSPECTIVE_PREREGISTRATION"
    else:
        status = "READY_FOR_EXPLICIT_OPERATOR_STUDY_OPEN"
    return {
        "schema_version": ROTATION_ADVISORY_STUDY_SCHEMA_VERSION,
        "status": status,
        "readiness_gates": gates,
        "manual_continuity_safety": {
            "proven_safe": manual_safe,
            "source": "TG9_exact_n5_manual_continuity_safety_gate",
            "tg9_status": natural_cohort.get("status"),
            "missing_reason": None if manual_safe else "safe_manual_continuity_gate_not_passed",
        },
        "preregistration": prereg,
        "study_contract": _contract(),
        "authority": {
            "study_epoch_opened": False,
            "assignment_created": False,
            "arm_revealed": False,
            "rotation_recommendation_emitted": False,
            "production_behavior_changed": False,
            "automatic_hard_rotation_authorized": False,
            "automatic_promotion_authorized": False,
            "explicit_operator_study_open_still_required": True,
        },
        "policy": {
            "read_only_readiness_projection": True,
            "tg9_descriptive_rows_are_not_causal_evidence": True,
            "manual_continuity_must_be_safe_before_study": True,
            "assignment_must_precede_arm_action": True,
            "unknown_is_not_zero": True,
            "public_mcp_tool_added": False,
        },
    }
