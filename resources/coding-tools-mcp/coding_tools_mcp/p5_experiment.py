from __future__ import annotations

"""Fail-closed P5 prospective-experiment contracts and pure projections.

This module deliberately contains no filesystem or SQLite writes.  The
orchestration ledger owns durable state and calls these helpers to canonicalize
the experimental contract, derive an epoch identity, and project all assigned
rows.  Keeping the scientific contract pure makes it possible to test replay
and analyzer determinism without a live runtime or treatment activation.
"""

import hashlib
import hmac
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping


P5_EXPERIMENT_SCHEMA_VERSION = 2
P5_ASSIGNMENT_UNIT_VERSION = "p5-assignment-unit-v1"
P5_ASSIGNMENT_ALGORITHM = "stratified_permuted_block_v1"
P5_ELIGIBLE_WORKFLOWS = frozenset({"feature", "bugfix"})
P5_EPOCH_ACTIVE = "EPOCH_ACTIVE"
P5_EPOCH_PAUSED = "EPOCH_PAUSED"
P5_EPOCH_CLOSED = "EPOCH_CLOSED"
P5_EPOCH_HARD_STOPPED = "EPOCH_HARD_STOPPED"
P5_EPOCH_TERMINAL = frozenset({P5_EPOCH_CLOSED, P5_EPOCH_HARD_STOPPED})
P5_TERMINAL_STATUSES = frozenset({"accepted", "rejected", "failed", "blocked", "aborted", "timeout"})
P5_INTERFERENCE_STATUSES = frozenset({"none", "nonoverlapping_mutation", "overlapping_mutation", "attribution_unknown"})


class P5ExperimentError(ValueError):
    """A P5 contract violates a preregistered or fail-closed invariant."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def analyzer_source_fingerprint() -> str:
    """Exact source identity for the deterministic feasibility analyzer."""

    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def _required_mapping(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise P5ExperimentError(f"{name} must be an object")
    return dict(value)


def _required_text(value: Any, name: str, *, max_length: int = 256) -> str:
    text = str(value or "").strip()
    if not text or len(text) > max_length:
        raise P5ExperimentError(f"{name} is required")
    return text


def _sha256(value: Any, name: str) -> str:
    text = _required_text(value, name, max_length=64).lower()
    if len(text) != 64 or any(char not in "0123456789abcdef" for char in text):
        raise P5ExperimentError(f"{name} must be a SHA-256 hex digest")
    return text


def _bool(value: Any, name: str, expected: bool = True) -> bool:
    if value is not expected:
        expected_text = "true" if expected else "false"
        raise P5ExperimentError(f"{name} must be {expected_text}")
    return bool(value)


def validate_manifest(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and canonicalize the v2 manifest needed before an epoch opens.

    Dynamic source/runtime/environment values are intentionally manifest inputs,
    not inferred from a historical report.  That prevents a stale readiness
    report from silently activating a live experiment.
    """

    value = _required_mapping(manifest, "manifest")
    if value.get("schema_version") != P5_EXPERIMENT_SCHEMA_VERSION:
        raise P5ExperimentError(f"schema_version must be {P5_EXPERIMENT_SCHEMA_VERSION}")
    experiment_id = _required_text(value.get("experiment_id"), "experiment_id")
    phase = _required_text(value.get("phase"), "phase", max_length=32)
    if phase not in {"P5-A0", "P5-A", "P5-B"}:
        raise P5ExperimentError("phase must be P5-A0, P5-A, or P5-B")
    study_type = _required_text(value.get("study_type"), "study_type", max_length=64)
    expected_study = {
        "P5-A0": "shadow_aa",
        "P5-A": "randomized_feasibility",
        "P5-B": "randomized_confirmatory",
    }[phase]
    if study_type != expected_study:
        raise P5ExperimentError(f"{phase} requires study_type={expected_study}")
    _bool(value.get("automatic_activation"), "automatic_activation", False)
    _bool(value.get("automatic_production_promotion"), "automatic_production_promotion", False)

    control_policy = _required_mapping(value.get("control_policy"), "control_policy")
    treatment_policy = _required_mapping(value.get("treatment_policy"), "treatment_policy")
    _required_text(control_policy.get("id"), "control_policy.id")
    _required_text(treatment_policy.get("id"), "treatment_policy.id")
    _sha256(treatment_policy.get("implementation_fingerprint"), "treatment_policy.implementation_fingerprint")
    if treatment_policy.get("vary_only") != "prewrite_causal_fix_protocol":
        raise P5ExperimentError("treatment_policy.vary_only must freeze the prewrite causal-fix protocol")

    source_contract = _required_mapping(value.get("source_contract"), "source_contract")
    runtime_contract = _required_mapping(value.get("runtime_contract"), "runtime_contract")
    environment_contract = _required_mapping(value.get("environment_contract"), "environment_contract")
    _required_text(source_contract.get("control_plane_source_head"), "source_contract.control_plane_source_head")
    _required_text(source_contract.get("upstream_identity"), "source_contract.upstream_identity")
    _bool(source_contract.get("source_worktree_clean_required"), "source_contract.source_worktree_clean_required")
    _bool(source_contract.get("no_conflicting_writer_required"), "source_contract.no_conflicting_writer_required")
    _required_text(runtime_contract.get("runtime_version"), "runtime_contract.runtime_version")
    for field in ("runtime_policy_fp", "tool_contract_fp", "evaluation_schema_fp"):
        _sha256(runtime_contract.get(field), f"runtime_contract.{field}")
    if runtime_contract.get("public_tool_count") != 8:
        raise P5ExperimentError("runtime_contract.public_tool_count must remain 8")
    _sha256(environment_contract.get("environment_fp"), "environment_contract.environment_fp")
    if environment_contract.get("method_version") != "p5-environment-v1":
        raise P5ExperimentError("environment_contract.method_version must be p5-environment-v1")

    common_execution = _required_mapping(value.get("common_execution_contract"), "common_execution_contract")
    _sha256(common_execution.get("policy_sha256"), "common_execution_contract.policy_sha256")
    eligibility_contract = _required_mapping(value.get("eligibility_contract"), "eligibility_contract")
    enrollment_contract = _required_mapping(value.get("enrollment_contract"), "enrollment_contract")
    if eligibility_contract.get("version") != "p5-eligibility-v2":
        raise P5ExperimentError("eligibility_contract.version must be p5-eligibility-v2")
    _sha256(eligibility_contract.get("reason_vocabulary_sha256"), "eligibility_contract.reason_vocabulary_sha256")
    _sha256(eligibility_contract.get("high_risk_exclusion_sha256"), "eligibility_contract.high_risk_exclusion_sha256")
    if enrollment_contract.get("version") != "p5-enrollment-v1":
        raise P5ExperimentError("enrollment_contract.version must be p5-enrollment-v1")
    _sha256(enrollment_contract.get("policy_sha256"), "enrollment_contract.policy_sha256")

    assignment = _required_mapping(value.get("assignment"), "assignment")
    if assignment.get("randomization_unit") != "stable_task_assignment":
        raise P5ExperimentError("assignment.randomization_unit must be stable_task_assignment")
    if assignment.get("unit_canonicalization_version") != P5_ASSIGNMENT_UNIT_VERSION:
        raise P5ExperimentError("assignment.unit_canonicalization_version is unsupported")
    if assignment.get("algorithm") != P5_ASSIGNMENT_ALGORITHM:
        raise P5ExperimentError("assignment.algorithm is unsupported")
    if sorted(assignment.get("strata") or []) != sorted(P5_ELIGIBLE_WORKFLOWS):
        raise P5ExperimentError("assignment.strata must be feature and bugfix")
    if assignment.get("block_size") != 4:
        raise P5ExperimentError("assignment.block_size must be 4")
    allocation = _required_mapping(assignment.get("allocation"), "assignment.allocation")
    if allocation.get("control") != 0.5 or allocation.get("treatment") != 0.5:
        raise P5ExperimentError("assignment.allocation must be a 1:1 control/treatment allocation")
    _sha256(assignment.get("seed_commitment_sha256"), "assignment.seed_commitment_sha256")
    _sha256(assignment.get("restart_safe_seed_contract_sha256"), "assignment.restart_safe_seed_contract_sha256")
    _bool(assignment.get("never_reseed_within_epoch"), "assignment.never_reseed_within_epoch")
    _bool(assignment.get("assignment_before_first_arm_action"), "assignment.assignment_before_first_arm_action")
    _bool(assignment.get("assignment_before_first_write"), "assignment.assignment_before_first_write")

    outcome_contract = _required_mapping(value.get("outcome_contract"), "outcome_contract")
    horizon = outcome_contract.get("horizon_seconds")
    if isinstance(horizon, bool) or not isinstance(horizon, int) or horizon <= 0:
        raise P5ExperimentError("outcome_contract.horizon_seconds must be a positive integer")
    if outcome_contract.get("horizon_anchor") != "assignment_at":
        raise P5ExperimentError("outcome_contract.horizon_anchor must be assignment_at")
    _bool(outcome_contract.get("immediate_oracle_required"), "outcome_contract.immediate_oracle_required")
    _sha256(outcome_contract.get("intercurrent_event_matrix_sha256"), "outcome_contract.intercurrent_event_matrix_sha256")
    _sha256(outcome_contract.get("followup_interference_policy_sha256"), "outcome_contract.followup_interference_policy_sha256")

    analysis = _required_mapping(value.get("analysis"), "analysis")
    _sha256(analysis.get("analyzer_sha256"), "analysis.analyzer_sha256")
    _bool(analysis.get("intention_to_treat"), "analysis.intention_to_treat")
    _bool(analysis.get("survivor_filter"), "analysis.survivor_filter", False)
    _sha256(analysis.get("target_population_weights_sha256"), "analysis.target_population_weights_sha256")
    missing = _required_mapping(value.get("missing_data"), "missing_data")
    _bool(missing.get("missing_is_unknown_not_zero"), "missing_data.missing_is_unknown_not_zero")
    _bool(missing.get("missing_quality_is_not_pass"), "missing_data.missing_quality_is_not_pass")
    _bool(missing.get("missing_cost_is_not_zero"), "missing_data.missing_cost_is_not_zero")
    stop_rule = _required_mapping(value.get("stop_rule"), "stop_rule")
    for name in (
        "stop_on_assignment_conflict",
        "stop_on_late_assignment",
        "stop_on_manifest_epoch_drift",
        "stop_on_authority_or_write_lease_violation",
        "stop_on_source_identity_violation",
        "stop_on_critical_security_or_data_loss_defect",
    ):
        _bool(stop_rule.get(name), f"stop_rule.{name}")
    return json.loads(canonical_json(value))


def manifest_sha256(manifest: Mapping[str, Any]) -> str:
    return sha256_json(validate_manifest(manifest))


def activation_epoch_id(manifest: Mapping[str, Any]) -> str:
    normalized = validate_manifest(manifest)
    treatment = _required_mapping(normalized["treatment_policy"], "treatment_policy")
    runtime = _required_mapping(normalized["runtime_contract"], "runtime_contract")
    environment = _required_mapping(normalized["environment_contract"], "environment_contract")
    assignment = _required_mapping(normalized["assignment"], "assignment")
    analysis = _required_mapping(normalized["analysis"], "analysis")
    common = _required_mapping(normalized["common_execution_contract"], "common_execution_contract")
    material = {
        "manifest_sha256": sha256_json(normalized),
        "treatment_implementation_fp": treatment["implementation_fingerprint"],
        "common_execution_contract_fp": common["policy_sha256"],
        "tool_contract_fp": runtime["tool_contract_fp"],
        "evaluation_schema_fp": runtime["evaluation_schema_fp"],
        "runtime_policy_fp": runtime["runtime_policy_fp"],
        "environment_fp": environment["environment_fp"],
        "assignment_algorithm_version": assignment["algorithm"],
        "analyzer_sha256": analysis["analyzer_sha256"],
    }
    return sha256_json(material)


def assignment_unit_fingerprint(
    *,
    task_assignment_id: str,
    repository_identity_fp: str,
    initial_task_spec_fp: str,
    initial_target_source_block_id: str,
) -> str:
    return sha256_json({
        "version": P5_ASSIGNMENT_UNIT_VERSION,
        "task_assignment_id": _required_text(task_assignment_id, "task_assignment_id"),
        "repository_identity_fp": _sha256(repository_identity_fp, "repository_identity_fp"),
        "initial_task_spec_fp": _sha256(initial_task_spec_fp, "initial_task_spec_fp"),
        "initial_target_source_block_id": _required_text(initial_target_source_block_id, "initial_target_source_block_id"),
    })


def eligibility_decision(candidate: Mapping[str, Any]) -> dict[str, Any]:
    """Evaluate arm-neutral eligibility before the assignment service runs."""

    value = _required_mapping(candidate, "candidate")
    workflow = str(value.get("task_class") or "").strip().lower()
    requirements = {
        "eligible_feature_or_bugfix": workflow in P5_ELIGIBLE_WORKFLOWS,
        "representative_natural_task": value.get("representative_natural_task") is True,
        "exact_source_identity_available": value.get("exact_source_identity_available") is True,
        "observed_oracle_available": value.get("observed_oracle_available") is True,
        "bounded_scope_feasible": value.get("bounded_scope_feasible") is True,
        "no_conflicting_writer_or_lease": value.get("no_conflicting_writer_or_lease") is True,
        "no_stale_or_recovery_state": value.get("no_stale_or_recovery_state") is True,
        "not_high_risk": value.get("not_high_risk") is True,
        "common_execution_contract_available": value.get("common_execution_contract_available") is True,
    }
    return {
        "task_class": workflow or "unknown",
        "eligible": all(requirements.values()),
        "requirements": requirements,
        "reason_codes": [name for name, passed in requirements.items() if not passed],
        "arm_revealed": False,
    }


def _hmac(seed: str, material: str) -> bytes:
    return hmac.new(seed.encode("utf-8"), material.encode("utf-8"), hashlib.sha256).digest()


def permuted_block_arms(*, seed: str, activation_epoch: str, stratum: str, block_id: int, phase: str) -> list[str]:
    """Return the concealed, restart-safe order for a single 2/2 block.

    The caller must keep ``seed`` in a secret broker.  This function never
    returns the seed or persists it; only a commitment appears in durable state.
    """

    if not isinstance(seed, str) or not seed:
        raise P5ExperimentError("assignment seed material is unavailable")
    if stratum not in P5_ELIGIBLE_WORKFLOWS or block_id < 0:
        raise P5ExperimentError("assignment block identity is invalid")
    if phase == "P5-A0":
        arms = ["control_a", "control_a", "control_b", "control_b"]
    elif phase in {"P5-A", "P5-B"}:
        arms = ["control", "control", "treatment", "treatment"]
    else:
        raise P5ExperimentError("assignment phase is invalid")
    salt = f"p5-permuted-block-v1\0{activation_epoch}\0{stratum}\0{block_id}"
    for index in range(len(arms) - 1, 0, -1):
        draw = int.from_bytes(_hmac(seed, f"{salt}\0{index}"), "big") % (index + 1)
        arms[index], arms[draw] = arms[draw], arms[index]
    return arms


def received_arm(*, phase: str, assigned_arm: str) -> str:
    if phase == "P5-A0":
        if assigned_arm not in {"control_a", "control_b"}:
            raise P5ExperimentError("P5-A0 assignment arm is invalid")
        return "control"
    if assigned_arm not in {"control", "treatment"}:
        raise P5ExperimentError("treatment assignment arm is invalid")
    return assigned_arm


def _parse_time(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def project_assignment_outcome(assignment: Mapping[str, Any], outcome: Mapping[str, Any] | None, *, horizon_seconds: int) -> dict[str, Any]:
    """Project one immutable assignment into the ITT denominator.

    Missing immediate quality/proof is a primary non-success; missing monetary
    cost stays unknown and is deliberately absent from this primary projection.
    """

    assigned_arm = str(assignment.get("assigned_arm") or "")
    base = {
        "assignment_id": str(assignment.get("assignment_id") or ""),
        "assignment_unit_fp": str(assignment.get("assignment_unit_fp") or ""),
        "task_class": str(assignment.get("task_class") or "unknown"),
        "assigned_arm": assigned_arm,
        "received_arm": None,
        "assignment_at": assignment.get("created_at"),
        "in_intention_to_treat": True,
        "terminal_status": "unknown_not_finalized",
        "primary_first_pass_accepted_by_h": False,
        "primary_non_success_reason": "outcome_not_finalized",
        "restricted_time_seconds": horizon_seconds,
        "immediate_quality_status": "unknown",
        "delayed_followup_status": "pending_or_unknown",
        "quality_followup_interference": "attribution_unknown",
        "post_assignment_replan_count": None,
        "adherence_status": "unknown",
    }
    if not outcome:
        return base
    terminal = str(outcome.get("terminal_status") or "").lower()
    base["terminal_status"] = terminal if terminal in P5_TERMINAL_STATUSES else "unknown_not_finalized"
    base["received_arm"] = outcome.get("received_arm") or None
    base["post_assignment_replan_count"] = outcome.get("post_assignment_replan_count")
    base["adherence_status"] = str(outcome.get("adherence_status") or "unknown")
    base["immediate_quality_status"] = str(outcome.get("immediate_quality_status") or "unknown")
    interference = str(outcome.get("quality_followup_interference") or "attribution_unknown")
    base["quality_followup_interference"] = interference if interference in P5_INTERFERENCE_STATUSES else "attribution_unknown"
    base["delayed_followup_status"] = str(outcome.get("delayed_followup_status") or "pending_or_unknown")
    assigned_at = _parse_time(assignment.get("created_at"))
    accepted_at = _parse_time(outcome.get("qualifying_acceptance_at"))
    elapsed = None
    if assigned_at is not None and accepted_at is not None:
        elapsed = max(0.0, (accepted_at - assigned_at).total_seconds())
        base["restricted_time_seconds"] = min(horizon_seconds, round(elapsed, 6))
    replan_count = outcome.get("post_assignment_replan_count")
    replan_ok = isinstance(replan_count, int) and not isinstance(replan_count, bool) and replan_count == 0
    immediate_ok = outcome.get("immediate_oracle_pass") is True and outcome.get("immediate_proof_observed") is True
    accepted_by_h = bool(terminal == "accepted" and elapsed is not None and elapsed <= horizon_seconds)
    if accepted_by_h and replan_ok and immediate_ok:
        base["primary_first_pass_accepted_by_h"] = True
        base["primary_non_success_reason"] = None
        return base
    if terminal != "accepted":
        base["primary_non_success_reason"] = "terminal_not_accepted"
    elif elapsed is None or elapsed > horizon_seconds:
        base["primary_non_success_reason"] = "accepted_after_h_or_time_unknown"
    elif not replan_ok:
        base["primary_non_success_reason"] = "post_assignment_replan_or_unknown"
    elif not immediate_ok:
        base["primary_non_success_reason"] = "immediate_oracle_or_proof_missing_or_failed"
    else:
        base["primary_non_success_reason"] = "unclassified_primary_non_success"
    return base


def canary_analyzer(
    *,
    manifest: Mapping[str, Any],
    epoch: Mapping[str, Any],
    assignments: list[Mapping[str, Any]],
    outcomes_by_assignment: Mapping[str, Mapping[str, Any]],
    enrollment_rows: list[Mapping[str, Any]],
    integrity_events: list[Mapping[str, Any]],
) -> dict[str, Any]:
    """Deterministic feasibility/integrity analyzer; it never estimates efficacy."""

    normalized = validate_manifest(manifest)
    horizon = int(_required_mapping(normalized["outcome_contract"], "outcome_contract")["horizon_seconds"])
    projection = [
        project_assignment_outcome(item, outcomes_by_assignment.get(str(item.get("assignment_id") or "")), horizon_seconds=horizon)
        for item in assignments
    ]
    assigned = len(projection)
    terminal = sum(1 for item in projection if item["terminal_status"] in P5_TERMINAL_STATUSES)
    immediate_complete = sum(1 for item in projection if item["immediate_quality_status"] in {"pass", "fail", "not_applicable"})
    unresolved = [item["assignment_id"] for item in projection if item["terminal_status"] == "unknown_not_finalized"]
    critical_integrity_types = {
        "p5_assignment_conflict",
        "p5_late_assignment_rejected",
        "p5_manifest_epoch_drift",
        "p5_authority_or_write_lease_violation",
        "p5_source_identity_violation",
        "p5_critical_security_or_data_loss_defect",
    }
    stop_events = [
        str(item.get("event_type") or "") for item in integrity_events
        if str(item.get("event_type") or "") in critical_integrity_types
    ]
    hard_stop_required = bool(stop_events)
    missing_outcome_pause_required = bool(
        str(epoch.get("lifecycle") or "") in P5_EPOCH_TERMINAL and unresolved
    )
    by_arm: dict[str, int] = {}
    by_stratum: dict[str, int] = {}
    for item in projection:
        by_arm[item["assigned_arm"]] = by_arm.get(item["assigned_arm"], 0) + 1
        by_stratum[item["task_class"]] = by_stratum.get(item["task_class"], 0) + 1
    enrolled = sum(1 for row in enrollment_rows if row.get("enrolled") is True)
    eligible = sum(1 for row in enrollment_rows if row.get("eligible") is True)
    return {
        "schema_version": 1,
        "analysis_kind": "p5_feasibility_and_integrity_v1",
        "experiment_id": normalized["experiment_id"],
        "activation_epoch_id": epoch.get("activation_epoch_id"),
        "phase": normalized["phase"],
        "study_type": normalized["study_type"],
        "efficacy_decision": "NOT_EVALUATED",
        "promotion_decision": None,
        "automatic_policy_activation": False,
        "automatic_production_promotion": False,
        "funnel": {
            "assessed": len(enrollment_rows),
            "eligible": eligible,
            "eligible_but_not_enrolled": max(0, eligible - enrolled),
            "enrolled": enrolled,
            "assigned": assigned,
            "terminal_finalized": terminal,
            "assigned_without_finalized_outcome": unresolved,
            "immediate_quality_complete": immediate_complete,
        },
        "assignment": {
            "by_arm": by_arm,
            "by_stratum": by_stratum,
            "all_assigned_retained_in_itt": len(projection) == assigned,
            "assigned_rows": projection,
        },
        "integrity": {
            "hard_stop_required": hard_stop_required,
            "hard_stop_event_types": sorted(set(stop_events)),
            "pause_required": missing_outcome_pause_required,
            "pause_reason": "closed_epoch_has_unfinalized_itt_rows" if missing_outcome_pause_required else None,
            "analyzer_hash": _required_mapping(normalized["analysis"], "analysis")["analyzer_sha256"],
        },
        "phase_claim_boundary": (
            "A/A instrumentation only; both assigned arms must receive control behavior."
            if normalized["phase"] == "P5-A0"
            else "Feasibility/integrity only; no efficacy or promotion claim."
        ),
        "content_free": True,
    }
