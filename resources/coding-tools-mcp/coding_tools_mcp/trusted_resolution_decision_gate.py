"""TG12 evidence-only retain/simplify/remove decision gate."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .egri_p5_continuity_readiness import (
    EGRI_P5_CONTINUITY_READINESS_SCHEMA_VERSION,
)


TRUSTED_RESOLUTION_DECISION_SCHEMA_VERSION = 1
TRUSTED_RESOLUTION_OUTCOME_RECEIPT_SCHEMA_VERSION = 1
_EFFECT_CLASSES = frozenset(
    {
        "MATERIAL_IMPROVEMENT",
        "NO_MATERIAL_BENEFIT",
        "NEGATIVE_TRANSFER",
        "INCONCLUSIVE",
    }
)


def _text(value: Any) -> str:
    return str(value or "").strip()


def _digest(value: Any) -> str | None:
    text = _text(value).lower()
    if len(text) == 64 and all(character in "0123456789abcdef" for character in text):
        return text
    return None


def _integer(
    value: Any,
    *,
    minimum: int = 0,
    maximum: int | None = None,
) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        return None
    if maximum is not None and value > maximum:
        return None
    return value


def _validate_outcome_receipt(value: Mapping[str, Any] | None) -> dict[str, Any]:
    if value is None:
        return {
            "status": "MISSING",
            "valid": False,
            "reason_codes": ["prospective_outcome_receipt_missing"],
        }
    reasons: list[str] = []
    allowed = {
        "schema_version",
        "receipt_id",
        "study_id",
        "treatment_id",
        "common_baseline_fingerprint",
        "treatment_fingerprint",
        "canonical_ledger_snapshot_sha256",
        "source_identity_fingerprint",
        "runtime_identity_fingerprint",
        "analysis_fingerprint",
        "prospective",
        "natural_workload_only",
        "source_tests_only",
        "synthetic_or_fixture_evidence",
        "assignment_before_arm_action_verified",
        "same_common_baseline_both_arms_verified",
        "same_continuity_semantics_both_arms_verified",
        "session_boundary_strata_complete",
        "study_integrity_pass",
        "quality_floor_pass",
        "authority_floor_pass",
        "preregistered_analysis_gate_pass",
        "qualifying_rows_control",
        "qualifying_rows_treatment",
        "minimum_qualifying_rows_per_arm",
        "state_loss_count",
        "duplicate_work_count",
        "trusted_resolution_rate_basis_points_control",
        "trusted_resolution_rate_basis_points_treatment",
        "ttpr_median_ms_control",
        "ttpr_median_ms_treatment",
        "accepted_result_economic_loss_microunits_control",
        "accepted_result_economic_loss_microunits_treatment",
        "capability_overhead_microunits",
        "material_economics_improvement_threshold_basis_points",
        "preregistered_effect_classification",
        "automatic_decision",
        "automatic_production_change",
    }
    if set(value) != allowed:
        reasons.append("outcome_receipt_fields_not_exact")
    if value.get("schema_version") != TRUSTED_RESOLUTION_OUTCOME_RECEIPT_SCHEMA_VERSION:
        reasons.append("outcome_receipt_schema_version_invalid")
    for field in ("receipt_id", "study_id", "treatment_id"):
        text = _text(value.get(field))
        if not text or len(text) > 128:
            reasons.append(f"{field}_invalid")
    digests: dict[str, str | None] = {}
    for field in (
        "common_baseline_fingerprint",
        "treatment_fingerprint",
        "canonical_ledger_snapshot_sha256",
        "source_identity_fingerprint",
        "runtime_identity_fingerprint",
        "analysis_fingerprint",
    ):
        digests[field] = _digest(value.get(field))
        if digests[field] is None:
            reasons.append(f"{field}_invalid")
    boolean_fields = (
        "prospective",
        "natural_workload_only",
        "source_tests_only",
        "synthetic_or_fixture_evidence",
        "assignment_before_arm_action_verified",
        "same_common_baseline_both_arms_verified",
        "same_continuity_semantics_both_arms_verified",
        "session_boundary_strata_complete",
        "study_integrity_pass",
        "quality_floor_pass",
        "authority_floor_pass",
        "preregistered_analysis_gate_pass",
        "automatic_decision",
        "automatic_production_change",
    )
    for field in boolean_fields:
        if not isinstance(value.get(field), bool):
            reasons.append(f"{field}_must_be_boolean")
    for field in ("automatic_decision", "automatic_production_change"):
        if value.get(field) is not False:
            reasons.append(f"{field}_must_be_false")
    integer_contracts = {
        "qualifying_rows_control": (0, None),
        "qualifying_rows_treatment": (0, None),
        "minimum_qualifying_rows_per_arm": (1, None),
        "state_loss_count": (0, None),
        "duplicate_work_count": (0, None),
        "trusted_resolution_rate_basis_points_control": (0, 10_000),
        "trusted_resolution_rate_basis_points_treatment": (0, 10_000),
        "ttpr_median_ms_control": (0, None),
        "ttpr_median_ms_treatment": (0, None),
        "accepted_result_economic_loss_microunits_control": (1, None),
        "accepted_result_economic_loss_microunits_treatment": (0, None),
        "capability_overhead_microunits": (0, None),
        "material_economics_improvement_threshold_basis_points": (1, 10_000),
    }
    metrics: dict[str, int | None] = {}
    for field, (minimum, maximum) in integer_contracts.items():
        metrics[field] = _integer(value.get(field), minimum=minimum, maximum=maximum)
        if metrics[field] is None:
            reasons.append(f"{field}_invalid")
    effect_class = _text(value.get("preregistered_effect_classification"))
    if effect_class not in _EFFECT_CLASSES:
        reasons.append("preregistered_effect_classification_invalid")
        effect_class = "INCONCLUSIVE"
    return {
        "status": "VALID" if not reasons else "INVALID",
        "valid": not reasons,
        "reason_codes": reasons,
        "receipt_id": _text(value.get("receipt_id")) or None,
        "study_id": _text(value.get("study_id")) or None,
        "treatment_id": _text(value.get("treatment_id")) or None,
        "common_baseline_fingerprint": digests.get("common_baseline_fingerprint"),
        "treatment_fingerprint": digests.get("treatment_fingerprint"),
        "evidence_identity": {
            "canonical_ledger_snapshot_sha256": digests.get(
                "canonical_ledger_snapshot_sha256"
            ),
            "source_identity_fingerprint": digests.get("source_identity_fingerprint"),
            "runtime_identity_fingerprint": digests.get("runtime_identity_fingerprint"),
            "analysis_fingerprint": digests.get("analysis_fingerprint"),
        },
        "evidence_flags": {field: value.get(field) for field in boolean_fields},
        "metrics": metrics,
        "preregistered_effect_classification": effect_class,
    }


def _tg11_contract(value: Mapping[str, Any]) -> dict[str, Any]:
    schema_ok = (
        value.get("schema_version") == EGRI_P5_CONTINUITY_READINESS_SCHEMA_VERSION
    )
    prereg = value.get("preregistration") if isinstance(value.get("preregistration"), Mapping) else {}
    aa_health = (
        value.get("aa_instrumentation_health")
        if isinstance(value.get("aa_instrumentation_health"), Mapping)
        else {}
    )
    authority = value.get("authority") if isinstance(value.get("authority"), Mapping) else {}
    no_side_effect = all(
        authority.get(field) is False
        for field in (
            "p5_epoch_opened",
            "assignment_created",
            "egri_treatment_activated",
            "production_behavior_changed",
            "policy_promoted",
        )
    )
    valid = schema_ok and prereg.get("valid") is True and no_side_effect
    ready = (
        valid
        and value.get("status") == "READY_FOR_EXPLICIT_EGRI_AB_STUDY_OPEN"
        and aa_health.get("valid") is True
        and aa_health.get("baseline_fingerprint_matches") is True
        and aa_health.get("study_id_matches") is True
    )
    treatment = prereg.get("treatment_identity") if isinstance(prereg.get("treatment_identity"), Mapping) else {}
    return {
        "valid": valid,
        "ready": ready,
        "schema_ok": schema_ok,
        "no_side_effect": no_side_effect,
        "study_id": _text(prereg.get("study_id")) or None,
        "treatment_id": _text(treatment.get("id")) or None,
        "treatment_fingerprint": _digest(treatment.get("fingerprint")),
        "common_baseline_fingerprint": _digest(prereg.get("common_baseline_fingerprint")),
    }


def _effect_projection(receipt: Mapping[str, Any]) -> dict[str, Any]:
    metrics = receipt.get("metrics") if isinstance(receipt.get("metrics"), Mapping) else {}
    control_economics = metrics.get("accepted_result_economic_loss_microunits_control")
    treatment_economics = metrics.get("accepted_result_economic_loss_microunits_treatment")
    if not isinstance(control_economics, int) or control_economics <= 0 or not isinstance(treatment_economics, int):
        improvement_bps = None
        economics_benefit = None
    else:
        economics_benefit = control_economics - treatment_economics
        improvement_bps = (economics_benefit * 10_000) // control_economics
    control_resolution = metrics.get("trusted_resolution_rate_basis_points_control")
    treatment_resolution = metrics.get("trusted_resolution_rate_basis_points_treatment")
    control_ttpr = metrics.get("ttpr_median_ms_control")
    treatment_ttpr = metrics.get("ttpr_median_ms_treatment")
    resolution_noninferior = bool(
        isinstance(control_resolution, int)
        and isinstance(treatment_resolution, int)
        and treatment_resolution >= control_resolution
    )
    ttpr_noninferior = bool(
        isinstance(control_ttpr, int)
        and isinstance(treatment_ttpr, int)
        and treatment_ttpr <= control_ttpr
    )
    negative_transfer = bool(
        isinstance(control_resolution, int)
        and isinstance(treatment_resolution, int)
        and isinstance(control_ttpr, int)
        and isinstance(treatment_ttpr, int)
        and isinstance(control_economics, int)
        and isinstance(treatment_economics, int)
        and (
            treatment_resolution < control_resolution
            or treatment_ttpr > control_ttpr
            or treatment_economics > control_economics
        )
    )
    threshold = metrics.get("material_economics_improvement_threshold_basis_points")
    material_improvement = bool(
        isinstance(improvement_bps, int)
        and isinstance(threshold, int)
        and improvement_bps >= threshold
        and resolution_noninferior
        and ttpr_noninferior
    )
    return {
        "accepted_result_economics_improvement_basis_points": improvement_bps,
        "accepted_result_economics_benefit_microunits": economics_benefit,
        "trusted_resolution_noninferior": resolution_noninferior,
        "ttpr_noninferior": ttpr_noninferior,
        "negative_transfer": negative_transfer,
        "material_economics_improvement": material_improvement,
    }


def trusted_resolution_decision_gate(
    tg11_readiness: Mapping[str, Any],
    *,
    outcome_receipt: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Project a TG12 disposition; never mutate a study, policy, or product."""

    if not isinstance(tg11_readiness, Mapping):
        raise TypeError("tg11_readiness must be a TG11 report mapping")
    upstream = _tg11_contract(tg11_readiness)
    receipt = _validate_outcome_receipt(outcome_receipt)
    identity_match = bool(
        receipt.get("study_id")
        and receipt.get("study_id") == upstream.get("study_id")
        and receipt.get("treatment_id") == upstream.get("treatment_id")
        and receipt.get("treatment_fingerprint") == upstream.get("treatment_fingerprint")
        and receipt.get("common_baseline_fingerprint")
        == upstream.get("common_baseline_fingerprint")
    )
    flags = receipt.get("evidence_flags") if isinstance(receipt.get("evidence_flags"), Mapping) else {}
    metrics = receipt.get("metrics") if isinstance(receipt.get("metrics"), Mapping) else {}
    minimum = metrics.get("minimum_qualifying_rows_per_arm")
    sample_floor = bool(
        isinstance(minimum, int)
        and isinstance(metrics.get("qualifying_rows_control"), int)
        and isinstance(metrics.get("qualifying_rows_treatment"), int)
        and metrics["qualifying_rows_control"] >= minimum
        and metrics["qualifying_rows_treatment"] >= minimum
    )
    safety_floor = (
        metrics.get("state_loss_count") == 0
        and metrics.get("duplicate_work_count") == 0
    )
    evidence_floor = bool(
        receipt.get("valid")
        and identity_match
        and flags.get("prospective") is True
        and flags.get("natural_workload_only") is True
        and flags.get("source_tests_only") is False
        and flags.get("synthetic_or_fixture_evidence") is False
        and flags.get("assignment_before_arm_action_verified") is True
        and flags.get("same_common_baseline_both_arms_verified") is True
        and flags.get("same_continuity_semantics_both_arms_verified") is True
        and flags.get("session_boundary_strata_complete") is True
        and flags.get("study_integrity_pass") is True
        and flags.get("quality_floor_pass") is True
        and flags.get("authority_floor_pass") is True
        and flags.get("preregistered_analysis_gate_pass") is True
        and sample_floor
        and safety_floor
    )
    effect = _effect_projection(receipt)
    declared_effect = receipt.get("preregistered_effect_classification")
    effect_supported = (
        declared_effect == "MATERIAL_IMPROVEMENT"
        and effect["material_economics_improvement"] is True
    ) or (
        declared_effect == "NEGATIVE_TRANSFER" and effect["negative_transfer"] is True
    ) or (
        declared_effect == "NO_MATERIAL_BENEFIT"
        and effect["material_economics_improvement"] is False
        and effect["negative_transfer"] is False
    ) or declared_effect == "INCONCLUSIVE"
    economics_benefit = effect.get("accepted_result_economics_benefit_microunits")
    overhead = metrics.get("capability_overhead_microunits")
    simplification_supported = bool(
        declared_effect == "NO_MATERIAL_BENEFIT"
        and isinstance(economics_benefit, int)
        and isinstance(overhead, int)
        and overhead >= max(0, economics_benefit)
    )

    if not upstream["valid"]:
        status = "INVALID_TG11_READINESS_REPORT"
        disposition = "HOLD"
    elif not upstream["ready"]:
        status = "HOLD_TG11_EGRI_STUDY_NOT_READY"
        disposition = "HOLD"
    elif outcome_receipt is None:
        status = "AWAITING_PROSPECTIVE_NATURAL_OUTCOME_RECEIPT"
        disposition = "HOLD"
    elif not receipt["valid"]:
        status = "INVALID_PROSPECTIVE_OUTCOME_RECEIPT"
        disposition = "HOLD"
    elif not identity_match:
        status = "INVALID_STUDY_IDENTITY_BINDING"
        disposition = "HOLD"
    elif not evidence_floor:
        status = "HOLD_EVIDENCE_FLOORS_NOT_PROVEN"
        disposition = "HOLD"
    elif not effect_supported:
        status = "HOLD_EFFECT_CLASSIFICATION_NOT_SUPPORTED_BY_METRICS"
        disposition = "HOLD"
    elif declared_effect == "MATERIAL_IMPROVEMENT":
        status = "RETAIN_CANDIDATE_FOR_EXPLICIT_OPERATOR_REVIEW"
        disposition = "RETAIN"
    elif declared_effect == "NEGATIVE_TRANSFER":
        status = "REMOVE_CANDIDATE_FOR_EXPLICIT_OPERATOR_REVIEW"
        disposition = "REMOVE"
    elif simplification_supported:
        status = "SIMPLIFY_CANDIDATE_FOR_EXPLICIT_OPERATOR_REVIEW"
        disposition = "SIMPLIFY"
    else:
        status = "HOLD_NO_MATERIAL_DISPOSITION"
        disposition = "HOLD"

    return {
        "schema_version": TRUSTED_RESOLUTION_DECISION_SCHEMA_VERSION,
        "status": status,
        "disposition": disposition,
        "readiness_gates": {
            "tg11_study_readiness": "PASS" if upstream["ready"] else "HOLD",
            "prospective_outcome_receipt": receipt["status"],
            "exact_study_identity_binding": "PASS" if identity_match else "HOLD",
            "natural_non_source_test_evidence": (
                "PASS"
                if flags.get("natural_workload_only") is True
                and flags.get("source_tests_only") is False
                and flags.get("synthetic_or_fixture_evidence") is False
                else "HOLD"
            ),
            "qualifying_sample": "PASS" if sample_floor else "HOLD",
            "state_loss_zero": "PASS" if metrics.get("state_loss_count") == 0 else "HOLD",
            "duplicate_work_zero": (
                "PASS" if metrics.get("duplicate_work_count") == 0 else "HOLD"
            ),
            "quality_authority_integrity": "PASS" if evidence_floor else "HOLD",
            "preregistered_effect_supported": "PASS" if effect_supported else "HOLD",
            "explicit_operator_disposition_acceptance": "REQUIRED",
        },
        "upstream_contract": upstream,
        "outcome_receipt": receipt,
        "effect_projection": effect,
        "decision_basis": {
            "preregistered_effect_classification": declared_effect,
            "effect_classification_supported": effect_supported,
            "simplification_overhead_support": simplification_supported,
            "bundle_level_only": True,
            "component_level_disposition_requires_separate_preregistered_ablation": True,
        },
        "authority": {
            "decision_automatically_accepted": False,
            "policy_promoted": False,
            "capability_retained": False,
            "capability_simplified": False,
            "capability_removed": False,
            "production_behavior_changed": False,
            "study_mutated": False,
            "explicit_operator_acceptance_still_required": True,
        },
        "policy": {
            "read_only_evidence_projection": True,
            "source_tests_are_not_outcome_evidence": True,
            "synthetic_evidence_cannot_drive_disposition": True,
            "unknown_is_not_zero": True,
            "qualifying_sample_required": True,
            "state_loss_must_equal_zero": True,
            "duplicate_work_must_equal_zero": True,
            "material_economics_improvement_required_for_retain": True,
            "automatic_promotion": False,
            "public_mcp_tool_added": False,
        },
    }
