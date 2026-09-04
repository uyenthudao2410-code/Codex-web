"""Arm-neutral TG11 readiness for EGRI evaluation without continuity confounding."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .rotation_advisory_study import ROTATION_ADVISORY_STUDY_SCHEMA_VERSION
from .semantic_localization import (
    DEFAULT_UNAVAILABLE_REASON,
    SEMANTIC_LOCALIZATION_SCHEMA_VERSION,
)


EGRI_P5_CONTINUITY_READINESS_SCHEMA_VERSION = 1
EGRI_P5_PREREGISTRATION_SCHEMA_VERSION = 1
EGRI_COMMON_BASELINE_ACCEPTANCE_SCHEMA_VERSION = 1
EGRI_AA_HEALTH_SCHEMA_VERSION = 1

_COMMON_BASELINE_COMPONENTS = frozenset(
    {
        "goal_pursuit_projector",
        "controller_knowledge_checkpoint_and_recovery",
        "continuity_core",
        "same_role_resume",
        "ui_independent_execution",
        "same_usage_and_economics_instrumentation",
    }
)
_TREATMENT_ONLY_COMPONENTS = frozenset(
    {
        "workspace_evidence_index",
        "case_memory",
        "enriched_frame_and_discriminator_packet",
    }
)
_REQUIRED_STRATA = frozenset(
    {
        "problem_task_class",
        "execution_route",
        "quality_oracle",
        "source_identity",
        "session_boundary_condition",
        "continuity_baseline_version",
        "semantic_localization_condition",
    }
)
_REQUIRED_OUTCOMES = frozenset(
    {
        "trusted_problem_resolution",
        "ttpr",
        "accepted_result_economics",
        "accepted_result_quality",
        "resume_success",
        "state_loss",
        "duplicate_work",
        "wrong_frame_or_reopen",
        "rework",
    }
)


def _text(value: Any) -> str:
    return str(value or "").strip()


def _digest(value: Any) -> str | None:
    text = _text(value).lower()
    if len(text) == 64 and all(character in "0123456789abcdef" for character in text):
        return text
    return None


def _missing(kind: str) -> dict[str, Any]:
    return {
        "status": "MISSING",
        "valid": False,
        "reason_codes": [f"{kind}_missing"],
    }


def _validate_common_baseline(value: Mapping[str, Any] | None) -> dict[str, Any]:
    if value is None:
        return _missing("common_baseline_acceptance")
    reasons: list[str] = []
    allowed = {
        "schema_version",
        "acceptance_id",
        "accepted",
        "common_baseline_fingerprint",
        "accepted_components",
        "continuity_contract_version",
        "controller_knowledge_checkpoint_version",
        "same_role_resume_verified",
        "ui_independent_execution_verified",
        "same_usage_and_economics_instrumentation_verified",
        "counterevidence_safety_floor_status",
        "public_tool_count",
    }
    if set(value) != allowed:
        reasons.append("common_baseline_fields_not_exact")
    if value.get("schema_version") != EGRI_COMMON_BASELINE_ACCEPTANCE_SCHEMA_VERSION:
        reasons.append("common_baseline_schema_version_invalid")
    if not _text(value.get("acceptance_id")):
        reasons.append("common_baseline_acceptance_id_invalid")
    if value.get("accepted") is not True:
        reasons.append("common_baseline_not_accepted")
    fingerprint = _digest(value.get("common_baseline_fingerprint"))
    if fingerprint is None:
        reasons.append("common_baseline_fingerprint_invalid")
    components = value.get("accepted_components")
    if not isinstance(components, list) or set(components) != _COMMON_BASELINE_COMPONENTS:
        reasons.append("common_baseline_components_incomplete")
    for field in (
        "continuity_contract_version",
        "controller_knowledge_checkpoint_version",
    ):
        if not _text(value.get(field)):
            reasons.append(f"{field}_invalid")
    for field in (
        "same_role_resume_verified",
        "ui_independent_execution_verified",
        "same_usage_and_economics_instrumentation_verified",
    ):
        if value.get(field) is not True:
            reasons.append(f"{field}_must_be_true")
    if value.get("counterevidence_safety_floor_status") not in {
        "ACCEPTED",
        "NOT_APPLICABLE",
    }:
        reasons.append("counterevidence_safety_floor_status_invalid")
    if value.get("public_tool_count") != 8:
        reasons.append("public_tool_count_must_remain_8")
    return {
        "status": "VALID" if not reasons else "INVALID",
        "valid": not reasons,
        "reason_codes": reasons,
        "acceptance_id": _text(value.get("acceptance_id")) or None,
        "common_baseline_fingerprint": fingerprint,
        "accepted_components": sorted(_COMMON_BASELINE_COMPONENTS),
    }


def _validate_preregistration(value: Mapping[str, Any] | None) -> dict[str, Any]:
    if value is None:
        return _missing("prospective_egri_preregistration")
    reasons: list[str] = []
    allowed = {
        "schema_version",
        "study_id",
        "treatment_id",
        "treatment_version",
        "treatment_fingerprint",
        "common_baseline_fingerprint",
        "treatment_only_components",
        "strata",
        "outcomes",
        "minimum_qualifying_rows_per_arm",
        "assignment_before_arm_action",
        "same_common_baseline_both_arms",
        "same_continuity_semantics_both_arms",
        "treatment_requires_semantic_localization",
        "deterministic_text_search_fallback_required",
        "source_identity_and_freshness_required",
        "max_definition_depth",
        "max_reference_edges",
        "max_call_hierarchy_depth",
        "max_evidence_files",
        "max_evidence_bytes",
        "workspace_evidence_index_is_authority",
        "case_memory_is_authority",
        "automatic_activation",
        "automatic_promotion",
        "public_tool_count",
    }
    if set(value) != allowed:
        reasons.append("preregistration_fields_not_exact")
    if value.get("schema_version") != EGRI_P5_PREREGISTRATION_SCHEMA_VERSION:
        reasons.append("preregistration_schema_version_invalid")
    for field in ("study_id", "treatment_id", "treatment_version"):
        text = _text(value.get(field))
        if not text or len(text) > 128:
            reasons.append(f"{field}_invalid")
    treatment_fingerprint = _digest(value.get("treatment_fingerprint"))
    if treatment_fingerprint is None:
        reasons.append("treatment_fingerprint_invalid")
    baseline_fingerprint = _digest(value.get("common_baseline_fingerprint"))
    if baseline_fingerprint is None:
        reasons.append("common_baseline_fingerprint_invalid")
    components = value.get("treatment_only_components")
    if not isinstance(components, list) or set(components) != _TREATMENT_ONLY_COMPONENTS:
        reasons.append("treatment_only_components_invalid")
    strata = value.get("strata")
    if not isinstance(strata, list) or set(strata) != _REQUIRED_STRATA:
        reasons.append("continuity_and_session_boundary_strata_incomplete")
    outcomes = value.get("outcomes")
    if not isinstance(outcomes, list) or set(outcomes) != _REQUIRED_OUTCOMES:
        reasons.append("required_outcomes_incomplete")
    minimum = value.get("minimum_qualifying_rows_per_arm")
    if isinstance(minimum, bool) or not isinstance(minimum, int) or minimum < 1:
        reasons.append("minimum_qualifying_rows_per_arm_invalid")
    for field in (
        "assignment_before_arm_action",
        "same_common_baseline_both_arms",
        "same_continuity_semantics_both_arms",
        "deterministic_text_search_fallback_required",
        "source_identity_and_freshness_required",
    ):
        if value.get(field) is not True:
            reasons.append(f"{field}_must_be_true")
    for field in (
        "treatment_requires_semantic_localization",
        "workspace_evidence_index_is_authority",
        "case_memory_is_authority",
        "automatic_activation",
        "automatic_promotion",
    ):
        if value.get(field) is not False:
            reasons.append(f"{field}_must_be_false")
    budgets = {
        "max_definition_depth": (1, 8),
        "max_reference_edges": (1, 500),
        "max_call_hierarchy_depth": (1, 8),
        "max_evidence_files": (1, 128),
        "max_evidence_bytes": (1024, 4 * 1024 * 1024),
    }
    for field, (minimum_value, maximum_value) in budgets.items():
        item = value.get(field)
        if (
            isinstance(item, bool)
            or not isinstance(item, int)
            or not minimum_value <= item <= maximum_value
        ):
            reasons.append(f"{field}_invalid")
    if value.get("public_tool_count") != 8:
        reasons.append("public_tool_count_must_remain_8")
    return {
        "status": "VALID" if not reasons else "INVALID",
        "valid": not reasons,
        "reason_codes": reasons,
        "study_id": _text(value.get("study_id")) or None,
        "treatment_identity": {
            "id": _text(value.get("treatment_id")) or None,
            "version": _text(value.get("treatment_version")) or None,
            "fingerprint": treatment_fingerprint,
        },
        "common_baseline_fingerprint": baseline_fingerprint,
        "frozen_strata": sorted(_REQUIRED_STRATA),
        "explicit_budgets": {
            field: value.get(field) for field in budgets
        },
    }


def _validate_aa_health(value: Mapping[str, Any] | None) -> dict[str, Any]:
    if value is None:
        return _missing("aa_instrumentation_health_receipt")
    reasons: list[str] = []
    allowed = {
        "schema_version",
        "receipt_id",
        "study_id",
        "status",
        "common_baseline_fingerprint",
        "manifest_fingerprint",
        "instrumentation_fingerprint",
        "observed_strata",
        "assignment_before_arm_action_verified",
        "arms_content_equivalent",
        "same_continuity_semantics_verified",
        "outcome_instrumentation_complete",
        "state_loss_count",
        "duplicate_work_count",
        "qualifying_observations_per_arm",
        "synthetic_or_fixture_evidence",
        "automatic_activation",
        "automatic_promotion",
    }
    if set(value) != allowed:
        reasons.append("aa_health_fields_not_exact")
    if value.get("schema_version") != EGRI_AA_HEALTH_SCHEMA_VERSION:
        reasons.append("aa_health_schema_version_invalid")
    for field in ("receipt_id", "study_id"):
        if not _text(value.get(field)):
            reasons.append(f"aa_{field}_invalid")
    if value.get("status") != "PASS":
        reasons.append("aa_instrumentation_health_not_pass")
    baseline_fingerprint = _digest(value.get("common_baseline_fingerprint"))
    if baseline_fingerprint is None:
        reasons.append("aa_common_baseline_fingerprint_invalid")
    for field in ("manifest_fingerprint", "instrumentation_fingerprint"):
        if _digest(value.get(field)) is None:
            reasons.append(f"aa_{field}_invalid")
    strata = value.get("observed_strata")
    if not isinstance(strata, list) or set(strata) != _REQUIRED_STRATA:
        reasons.append("aa_continuity_and_session_boundary_strata_incomplete")
    for field in (
        "assignment_before_arm_action_verified",
        "arms_content_equivalent",
        "same_continuity_semantics_verified",
        "outcome_instrumentation_complete",
    ):
        if value.get(field) is not True:
            reasons.append(f"aa_{field}_must_be_true")
    for field in ("state_loss_count", "duplicate_work_count"):
        item = value.get(field)
        if isinstance(item, bool) or not isinstance(item, int) or item != 0:
            reasons.append(f"aa_{field}_must_equal_zero")
    observations = value.get("qualifying_observations_per_arm")
    if isinstance(observations, bool) or not isinstance(observations, int) or observations < 1:
        reasons.append("aa_qualifying_observations_per_arm_invalid")
    for field in (
        "synthetic_or_fixture_evidence",
        "automatic_activation",
        "automatic_promotion",
    ):
        if value.get(field) is not False:
            reasons.append(f"aa_{field}_must_be_false")
    return {
        "status": "VALID" if not reasons else "INVALID",
        "valid": not reasons,
        "reason_codes": reasons,
        "receipt_id": _text(value.get("receipt_id")) or None,
        "study_id": _text(value.get("study_id")) or None,
        "common_baseline_fingerprint": baseline_fingerprint,
        "qualifying_observations_per_arm": (
            observations if isinstance(observations, int) and not isinstance(observations, bool) else None
        ),
    }


def _semantic_condition(value: Mapping[str, Any] | None) -> dict[str, Any]:
    status = value if isinstance(value, Mapping) else {}
    schema_ok = status.get("schema_version") == SEMANTIC_LOCALIZATION_SCHEMA_VERSION
    read_only = status.get("read_only") is True
    available = status.get("available") is True
    reason = _text(status.get("reason")) or None
    if not schema_ok or not read_only:
        return {
            "status": "INVALID_STATUS",
            "safe_for_readiness": False,
            "available": available,
            "reason": reason,
            "deterministic_fallback_required": True,
        }
    if not available:
        typed = reason == DEFAULT_UNAVAILABLE_REASON
        return {
            "status": (
                "UNAVAILABLE_TYPED_FALLBACK_REQUIRED"
                if typed
                else "UNAVAILABLE_UNPROVEN_REASON"
            ),
            "safe_for_readiness": typed,
            "available": False,
            "reason": reason,
            "deterministic_fallback_required": True,
            "semantic_dependency_forbidden": True,
        }
    provider = _text(status.get("provider"))
    exact_current = status.get("exact_current_binding_proven") is True
    source_fenced = status.get("source_identity_and_freshness_proven") is True
    proven = bool(provider and exact_current and source_fenced)
    return {
        "status": "AVAILABLE_PROVEN" if proven else "AVAILABLE_BUT_UNPROVEN",
        "safe_for_readiness": proven,
        "available": True,
        "provider": provider or None,
        "reason": reason,
        "deterministic_fallback_required": True,
        "exact_current_binding_proven": exact_current,
        "source_identity_and_freshness_proven": source_fenced,
    }


def _study_contract() -> dict[str, Any]:
    return {
        "study_kind": "prospective_egri_incremental_reasoning_ab_study",
        "causal_estimand": "incremental_EGRI_reasoning_benefit_above_common_continuity_baseline",
        "common_baseline": sorted(_COMMON_BASELINE_COMPONENTS),
        "treatment_only": sorted(_TREATMENT_ONLY_COMPONENTS),
        "continuity_is_not_treatment": True,
        "semantic_localization_is_capability_gated": True,
        "deterministic_text_search_fallback_required": True,
        "workspace_evidence_index_is_derived_not_authority": True,
        "case_memory_is_derived_not_authority": True,
        "source_files_remain_authority": True,
        "p5_remains_under_task_control": True,
        "public_tool_count": 8,
        "automatic_activation": False,
        "automatic_promotion": False,
    }


def egri_p5_continuity_readiness(
    rotation_readiness: Mapping[str, Any],
    *,
    common_baseline_acceptance: Mapping[str, Any] | None = None,
    preregistration: Mapping[str, Any] | None = None,
    aa_health_receipt: Mapping[str, Any] | None = None,
    semantic_status: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return TG11 readiness only; never open, assign, activate, or promote a study."""

    if not isinstance(rotation_readiness, Mapping):
        raise TypeError("rotation_readiness must be a TG10 report mapping")
    tg10_schema_ok = (
        rotation_readiness.get("schema_version")
        == ROTATION_ADVISORY_STUDY_SCHEMA_VERSION
    )
    manual = (
        rotation_readiness.get("manual_continuity_safety")
        if isinstance(rotation_readiness.get("manual_continuity_safety"), Mapping)
        else {}
    )
    tg10_prereg = (
        rotation_readiness.get("preregistration")
        if isinstance(rotation_readiness.get("preregistration"), Mapping)
        else {}
    )
    tg10_authority = (
        rotation_readiness.get("authority")
        if isinstance(rotation_readiness.get("authority"), Mapping)
        else {}
    )
    tg10_no_side_effect = all(
        tg10_authority.get(field) is False
        for field in (
            "study_epoch_opened",
            "assignment_created",
            "rotation_recommendation_emitted",
            "production_behavior_changed",
        )
    )
    tg10_ready = (
        tg10_schema_ok
        and rotation_readiness.get("status") == "READY_FOR_EXPLICIT_OPERATOR_STUDY_OPEN"
        and manual.get("proven_safe") is True
        and tg10_prereg.get("valid") is True
        and tg10_no_side_effect
    )
    baseline = _validate_common_baseline(common_baseline_acceptance)
    prereg = _validate_preregistration(preregistration)
    aa_health = _validate_aa_health(aa_health_receipt)
    semantic = _semantic_condition(semantic_status)
    baseline_match = bool(
        baseline.get("common_baseline_fingerprint")
        and baseline.get("common_baseline_fingerprint")
        == prereg.get("common_baseline_fingerprint")
    )
    aa_baseline_match = bool(
        baseline.get("common_baseline_fingerprint")
        and baseline.get("common_baseline_fingerprint")
        == aa_health.get("common_baseline_fingerprint")
    )
    study_match = bool(
        prereg.get("study_id")
        and prereg.get("study_id") == aa_health.get("study_id")
    )
    semantic_contract_safe = bool(
        semantic.get("safe_for_readiness")
        and preregistration is not None
        and preregistration.get("treatment_requires_semantic_localization") is False
        and preregistration.get("deterministic_text_search_fallback_required") is True
    )
    aa_pass = bool(aa_health.get("valid") and aa_baseline_match and study_match)

    if not tg10_schema_ok or not tg10_no_side_effect:
        status = "INVALID_TG10_READINESS_REPORT"
    elif not tg10_ready:
        status = "HOLD_TG10_MANUAL_CONTINUITY_NOT_READY"
    elif common_baseline_acceptance is None:
        status = "AWAITING_COMMON_BASELINE_ACCEPTANCE"
    elif not baseline["valid"]:
        status = "INVALID_COMMON_BASELINE_ACCEPTANCE"
    elif preregistration is None:
        status = "AWAITING_PROSPECTIVE_EGRI_PREREGISTRATION"
    elif not prereg["valid"]:
        status = "INVALID_PROSPECTIVE_EGRI_PREREGISTRATION"
    elif not baseline_match:
        status = "INVALID_COMMON_BASELINE_FINGERPRINT_BINDING"
    elif not semantic_contract_safe:
        status = "HOLD_SEMANTIC_CAPABILITY_CONTRACT_NOT_PROVEN"
    elif not aa_pass:
        status = "HOLD_AA_INSTRUMENTATION_HEALTH_NOT_PROVEN"
    else:
        status = "READY_FOR_EXPLICIT_EGRI_AB_STUDY_OPEN"

    return {
        "schema_version": EGRI_P5_CONTINUITY_READINESS_SCHEMA_VERSION,
        "status": status,
        "readiness_gates": {
            "tg10_manual_continuity_readiness": "PASS" if tg10_ready else "HOLD",
            "accepted_common_continuity_baseline": baseline["status"],
            "prospective_egri_preregistration": prereg["status"],
            "common_baseline_fingerprint_binding": "PASS" if baseline_match else "HOLD",
            "semantic_capability_or_deterministic_fallback": (
                "PASS" if semantic_contract_safe else "HOLD"
            ),
            "aa_instrumentation_health": "PASS" if aa_pass else "HOLD",
            "explicit_operator_ab_study_open": "REQUIRED",
        },
        "common_baseline_acceptance": baseline,
        "preregistration": prereg,
        "aa_instrumentation_health": {
            **aa_health,
            "baseline_fingerprint_matches": aa_baseline_match,
            "study_id_matches": study_match,
        },
        "semantic_condition": semantic,
        "study_contract": _study_contract(),
        "authority": {
            "tg10_study_opened": False,
            "p5_epoch_opened": False,
            "assignment_created": False,
            "arm_revealed": False,
            "egri_treatment_activated": False,
            "rotation_recommendation_emitted": False,
            "production_behavior_changed": False,
            "policy_promoted": False,
            "explicit_operator_ab_study_open_still_required": True,
        },
        "policy": {
            "read_only_readiness_projection": True,
            "aa_health_required_before_ab": True,
            "continuity_common_baseline_both_arms": True,
            "unknown_is_not_zero": True,
            "source_tests_are_not_causal_evidence": True,
            "no_new_authority_store": True,
            "public_mcp_tool_added": False,
        },
    }
