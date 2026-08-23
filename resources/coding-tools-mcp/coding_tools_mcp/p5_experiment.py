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
P5_A0_HORIZON_SECONDS = 4 * 60 * 60
P5_CONTROL_POLICY_ID = "eocl-current-control-v1"
P5_TREATMENT_POLICY_ID = "lean-causal-fix-gate-v1"
P5_ENVIRONMENT_METHOD_VERSION = "p5-environment-v1"


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


def build_p5_a0_manifest(
    *,
    source_contract: Mapping[str, Any],
    runtime_contract: Mapping[str, Any],
    environment_fp: str,
    seed_commitment_sha256: str,
) -> dict[str, Any]:
    """Build the production P5-A0 manifest from live content-free identities."""

    source = _required_mapping(source_contract, "source_contract")
    runtime = _required_mapping(runtime_contract, "runtime_contract")
    manifest = {
        "schema_version": P5_EXPERIMENT_SCHEMA_VERSION,
        "experiment_id": "p5-lean-causal-fix-p5-a0-v1",
        "phase": "P5-A0",
        "study_type": "shadow_aa",
        "automatic_activation": False,
        "automatic_production_promotion": False,
        "control_policy": {"id": P5_CONTROL_POLICY_ID},
        "treatment_policy": {
            "id": P5_TREATMENT_POLICY_ID,
            "implementation_fingerprint": sha256_text(P5_TREATMENT_POLICY_ID),
            "vary_only": "prewrite_causal_fix_protocol",
        },
        "source_contract": {
            "control_plane_source_head": source.get("control_plane_source_head"),
            "upstream_identity": source.get("upstream_identity"),
            "source_worktree_clean_required": True,
            "no_conflicting_writer_required": True,
        },
        "runtime_contract": {
            "runtime_version": runtime.get("runtime_version"),
            "runtime_policy_fp": runtime.get("runtime_policy_fp"),
            "tool_contract_fp": runtime.get("tool_contract_fp"),
            "evaluation_schema_fp": runtime.get("evaluation_schema_fp"),
            "public_tool_count": runtime.get("public_tool_count"),
        },
        "environment_contract": {"environment_fp": environment_fp, "method_version": P5_ENVIRONMENT_METHOD_VERSION},
        "common_execution_contract": {"policy_sha256": sha256_text("p5-common-execution-contract-v1")},
        "eligibility_contract": {
            "version": "p5-eligibility-v2",
            "reason_vocabulary_sha256": sha256_text("p5-eligibility-reason-vocabulary-v2"),
            "high_risk_exclusion_sha256": sha256_text("p5-high-risk-exclusion-v1"),
        },
        "enrollment_contract": {"version": "p5-enrollment-v1", "policy_sha256": sha256_text("p5-enrollment-policy-v1")},
        "assignment": {
            "randomization_unit": "stable_task_assignment",
            "unit_canonicalization_version": P5_ASSIGNMENT_UNIT_VERSION,
            "algorithm": P5_ASSIGNMENT_ALGORITHM,
            "strata": ["feature", "bugfix"],
            "block_size": 4,
            "allocation": {"control": 0.5, "treatment": 0.5},
            "seed_commitment_sha256": seed_commitment_sha256,
            "restart_safe_seed_contract_sha256": sha256_text("p5-secret-handle-contract-v1"),
            "never_reseed_within_epoch": True,
            "assignment_before_first_arm_action": True,
            "assignment_before_first_write": True,
        },
        "outcome_contract": {
            "horizon_seconds": P5_A0_HORIZON_SECONDS,
            "horizon_anchor": "assignment_at",
            "immediate_oracle_required": True,
            "intercurrent_event_matrix_sha256": sha256_text("p5-intercurrent-event-matrix-v1"),
            "followup_interference_policy_sha256": sha256_text("p5-followup-interference-policy-v1"),
        },
        "analysis": {
            "analyzer_sha256": analyzer_source_fingerprint(),
            "intention_to_treat": True,
            "survivor_filter": False,
            "target_population_weights_sha256": sha256_text("p5-target-population-weights-v1"),
        },
        "missing_data": {"missing_is_unknown_not_zero": True, "missing_quality_is_not_pass": True, "missing_cost_is_not_zero": True},
        "stop_rule": {
            "stop_on_assignment_conflict": True,
            "stop_on_late_assignment": True,
            "stop_on_manifest_epoch_drift": True,
            "stop_on_authority_or_write_lease_violation": True,
            "stop_on_source_identity_violation": True,
            "stop_on_critical_security_or_data_loss_defect": True,
        },
    }
    return validate_manifest(manifest)


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


_FUNNEL_STAGES = (
    "assigned",
    "protocol_started",
    "prewrite_bound",
    "first_write_recorded",
    "terminal_finalized",
    "immediate_quality_complete",
    "delayed_followup_complete",
    "delayed_followup_interfered",
)


def _funnel_stage_counts() -> dict[str, int]:
    return {stage: 0 for stage in _FUNNEL_STAGES}


def _expected_assignment_arms(phase: str) -> tuple[str, ...]:
    if phase == "P5-A0":
        return ("control_a", "control_b")
    return ("control", "treatment")


def _delayed_followup_complete(outcome: Mapping[str, Any] | None) -> bool:
    if not outcome:
        return False
    status = str(outcome.get("delayed_followup_status") or "").strip().lower()
    return status not in {"", "unknown", "pending", "pending_or_unknown"}


def _funnel_integrity(
    *,
    phase: str,
    assignments: list[Mapping[str, Any]],
    enrollment_rows: list[Mapping[str, Any]],
    outcomes_by_assignment: Mapping[str, Mapping[str, Any]],
    protocol_starts_by_assignment: Mapping[str, Mapping[str, Any]],
    workflow_bindings_by_assignment: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    """Build the preregistered structural funnel without inferential SRM.

    A canary is too small for a sample-ratio p-value to establish randomizer
    correctness.  Instead, replay the durable 2/2 block shape, reconcile every
    table join, and expose stage losses by immutable assigned arm and stratum.
    Incomplete live blocks are expected and reported, not treated as imbalance.
    """

    expected_arms = _expected_assignment_arms(phase)
    by_arm = {arm: _funnel_stage_counts() for arm in expected_arms}
    by_stratum = {stratum: _funnel_stage_counts() for stratum in sorted(P5_ELIGIBLE_WORKFLOWS)}
    blocks: dict[tuple[str, int], list[Mapping[str, Any]]] = {}
    enrollment_ids = {str(row.get("enrollment_id") or "") for row in enrollment_rows if row.get("enrolled") is True}
    assigned_enrollment_ids = {str(row.get("enrollment_id") or "") for row in assignments}
    assigned_ids = {str(row.get("assignment_id") or "") for row in assignments}
    violations: set[str] = set()
    received_arm_crossover_ids: list[str] = []
    binding_mismatch_ids: list[str] = []
    protocol_mismatch_ids: list[str] = []

    for assignment in assignments:
        assignment_id = str(assignment.get("assignment_id") or "")
        assigned_arm = str(assignment.get("assigned_arm") or "")
        task_class = str(assignment.get("task_class") or "")
        if assigned_arm not in by_arm:
            violations.add("invalid_assigned_arm")
            by_arm.setdefault(assigned_arm or "invalid", _funnel_stage_counts())
        if task_class not in by_stratum:
            violations.add("invalid_assignment_stratum")
            by_stratum.setdefault(task_class or "invalid", _funnel_stage_counts())
        block_id = assignment.get("block_id")
        block_slot = assignment.get("block_slot")
        if isinstance(block_id, bool) or not isinstance(block_id, int) or isinstance(block_slot, bool) or not isinstance(block_slot, int):
            violations.add("invalid_block_identity")
        else:
            blocks.setdefault((task_class, block_id), []).append(assignment)

        protocol = protocol_starts_by_assignment.get(assignment_id)
        binding = workflow_bindings_by_assignment.get(assignment_id)
        outcome = outcomes_by_assignment.get(assignment_id)
        try:
            expected_received = received_arm(phase=phase, assigned_arm=assigned_arm)
        except P5ExperimentError:
            expected_received = ""
            violations.add("invalid_assigned_arm")
        observed_received = str((protocol or outcome or {}).get("received_arm") or "")
        if protocol and observed_received != expected_received:
            protocol_mismatch_ids.append(assignment_id)
            violations.add("protocol_received_arm_mismatch")
        if outcome and str(outcome.get("received_arm") or "") != expected_received:
            received_arm_crossover_ids.append(assignment_id)
            violations.add("received_arm_crossover")
        if binding and (not protocol or not str((protocol or {}).get("first_write_at") or "")):
            binding_mismatch_ids.append(assignment_id)
            violations.add("prewrite_binding_without_runtime_first_write")

        stages = {
            "assigned": True,
            "protocol_started": protocol is not None,
            "prewrite_bound": binding is not None,
            "first_write_recorded": bool(protocol and str(protocol.get("first_write_at") or "")),
            "terminal_finalized": outcome is not None and str(outcome.get("terminal_status") or "").lower() in P5_TERMINAL_STATUSES,
            "immediate_quality_complete": outcome is not None and str(outcome.get("immediate_quality_status") or "") in {"pass", "fail", "not_applicable"},
            "delayed_followup_complete": _delayed_followup_complete(outcome),
            "delayed_followup_interfered": outcome is not None and str(outcome.get("quality_followup_interference") or "") != "none",
        }
        for stage, reached in stages.items():
            if reached:
                by_arm[assigned_arm][stage] += 1
                by_stratum[task_class][stage] += 1

    completed_blocks: list[dict[str, Any]] = []
    partial_blocks: list[dict[str, Any]] = []
    expected_counts = {arm: 2 for arm in expected_arms}
    for (task_class, block_id), rows in sorted(blocks.items()):
        slots = [row.get("block_slot") for row in rows]
        arms = [str(row.get("assigned_arm") or "") for row in rows]
        slot_set = {slot for slot in slots if isinstance(slot, int) and not isinstance(slot, bool)}
        slots_valid = len(slots) == len(slot_set) and slot_set.issubset({0, 1, 2, 3})
        arm_counts = {arm: arms.count(arm) for arm in expected_arms}
        descriptor = {
            "task_class": task_class,
            "block_id": block_id,
            "assigned_slots": sorted(slot_set),
            "missing_slots": sorted({0, 1, 2, 3} - slot_set),
            "arm_counts": arm_counts,
        }
        if len(rows) == 4 and slot_set == {0, 1, 2, 3}:
            descriptor["balanced"] = bool(slots_valid and arm_counts == expected_counts)
            completed_blocks.append(descriptor)
            if not descriptor["balanced"]:
                violations.add("completed_block_schedule_mismatch")
        else:
            descriptor["balanced"] = None
            partial_blocks.append(descriptor)
            if not slots_valid:
                violations.add("invalid_partial_block_slots")

    unknown_protocol_ids = sorted(set(protocol_starts_by_assignment) - assigned_ids)
    unknown_binding_ids = sorted(set(workflow_bindings_by_assignment) - assigned_ids)
    unknown_outcome_ids = sorted(set(outcomes_by_assignment) - assigned_ids)
    if unknown_protocol_ids:
        violations.add("protocol_without_assignment")
    if unknown_binding_ids:
        violations.add("prewrite_binding_without_assignment")
    if unknown_outcome_ids:
        violations.add("outcome_without_assignment")
    unenrolled_assignment_ids = sorted(
        str(row.get("assignment_id") or "")
        for row in assignments
        if str(row.get("enrollment_id") or "") not in enrollment_ids
    )
    if unenrolled_assignment_ids:
        violations.add("assignment_without_enrollment")

    total = _funnel_stage_counts()
    for counts in by_arm.values():
        for stage in _FUNNEL_STAGES:
            total[stage] += counts[stage]
    structural = {
        "method": "completed_block_shape_and_exact_event_accounting_v1",
        "inferential_srm_p_value": None,
        "inferential_srm_not_applicable_reason": "structural_2x2_block_replay_is_primary_integrity_evidence",
        "completed_block_count": len(completed_blocks),
        "partial_block_count": len(partial_blocks),
        "completed_blocks": completed_blocks,
        "partial_blocks": partial_blocks,
        "completed_blocks_balanced": all(item["balanced"] is True for item in completed_blocks),
    }
    integrity = {
        "structural_block_schedule": structural,
        "losses": {
            "enrollment_to_assignment": {
                "enrolled_without_assignment_count": len(enrollment_ids - assigned_enrollment_ids),
                "assignment_without_enrollment_ids": unenrolled_assignment_ids,
            },
            "assignment_to_protocol_start": {"missing_count": total["assigned"] - total["protocol_started"]},
            "protocol_start_to_prewrite_binding": {"missing_count": total["protocol_started"] - total["prewrite_bound"]},
            "prewrite_binding_to_first_write_record": {"missing_count": total["prewrite_bound"] - total["first_write_recorded"]},
            "assignment_to_terminal_outcome": {"missing_count": total["assigned"] - total["terminal_finalized"]},
            "terminal_to_immediate_quality": {"missing_count": total["terminal_finalized"] - total["immediate_quality_complete"]},
            "terminal_to_delayed_followup": {"missing_count": total["terminal_finalized"] - total["delayed_followup_complete"]},
        },
        "received_arm": {
            "protocol_received_arm_mismatch_ids": sorted(protocol_mismatch_ids),
            "outcome_crossover_ids": sorted(received_arm_crossover_ids),
            "binding_first_write_mismatch_ids": sorted(binding_mismatch_ids),
        },
        "orphan_rows": {
            "protocol_assignment_ids": unknown_protocol_ids,
            "workflow_binding_assignment_ids": unknown_binding_ids,
            "outcome_assignment_ids": unknown_outcome_ids,
        },
        "hard_stop_reason_codes": sorted(violations),
    }
    return total, {"by_assigned_arm": by_arm, "by_stratum": by_stratum, "integrity": integrity}, sorted(violations)


def canary_analyzer(
    *,
    manifest: Mapping[str, Any],
    epoch: Mapping[str, Any],
    assignments: list[Mapping[str, Any]],
    outcomes_by_assignment: Mapping[str, Mapping[str, Any]],
    enrollment_rows: list[Mapping[str, Any]],
    integrity_events: list[Mapping[str, Any]],
    protocol_starts: list[Mapping[str, Any]] | None = None,
    workflow_bindings: list[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Deterministic feasibility/integrity analyzer; it never estimates efficacy."""

    normalized = validate_manifest(manifest)
    horizon = int(_required_mapping(normalized["outcome_contract"], "outcome_contract")["horizon_seconds"])
    protocol_starts_by_assignment = {
        str(item.get("assignment_id") or ""): item
        for item in (protocol_starts or [])
        if str(item.get("assignment_id") or "")
    }
    workflow_bindings_by_assignment = {
        str(item.get("assignment_id") or ""): item
        for item in (workflow_bindings or [])
        if str(item.get("assignment_id") or "")
    }
    projection = [
        project_assignment_outcome(item, outcomes_by_assignment.get(str(item.get("assignment_id") or "")), horizon_seconds=horizon)
        for item in assignments
    ]
    for item in projection:
        assignment_id = str(item["assignment_id"])
        protocol = protocol_starts_by_assignment.get(assignment_id)
        if protocol and item["received_arm"] is None:
            item["received_arm"] = protocol.get("received_arm") or None
        item["protocol_started"] = protocol is not None
        item["prewrite_bound"] = assignment_id in workflow_bindings_by_assignment
        item["first_write_recorded"] = bool(protocol and str(protocol.get("first_write_at") or ""))
    total_funnel, funnel_detail, funnel_violations = _funnel_integrity(
        phase=str(normalized["phase"]),
        assignments=assignments,
        enrollment_rows=enrollment_rows,
        outcomes_by_assignment=outcomes_by_assignment,
        protocol_starts_by_assignment=protocol_starts_by_assignment,
        workflow_bindings_by_assignment=workflow_bindings_by_assignment,
    )
    assigned = total_funnel["assigned"]
    terminal = total_funnel["terminal_finalized"]
    immediate_complete = total_funnel["immediate_quality_complete"]
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
    hard_stop_required = bool(stop_events or funnel_violations)
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
            "protocol_started": total_funnel["protocol_started"],
            "prewrite_bound": total_funnel["prewrite_bound"],
            "first_write_recorded": total_funnel["first_write_recorded"],
            "terminal_finalized": terminal,
            "assigned_without_finalized_outcome": unresolved,
            "immediate_quality_complete": immediate_complete,
            "delayed_followup_complete": total_funnel["delayed_followup_complete"],
            "delayed_followup_interfered": total_funnel["delayed_followup_interfered"],
        },
        "assignment": {
            "by_arm": by_arm,
            "by_stratum": by_stratum,
            "all_assigned_retained_in_itt": len(projection) == assigned,
            "assigned_rows": projection,
        },
        "funnel_by_assigned_arm": funnel_detail["by_assigned_arm"],
        "funnel_by_stratum": funnel_detail["by_stratum"],
        "integrity": {
            "hard_stop_required": hard_stop_required,
            "hard_stop_event_types": sorted(set(stop_events)),
            "hard_stop_reason_codes": sorted(set(funnel_violations)),
            "pause_required": missing_outcome_pause_required,
            "pause_reason": "closed_epoch_has_unfinalized_itt_rows" if missing_outcome_pause_required else None,
            "analyzer_hash": _required_mapping(normalized["analysis"], "analysis")["analyzer_sha256"],
            "funnel_integrity": funnel_detail["integrity"],
        },
        "phase_claim_boundary": (
            "A/A instrumentation only; both assigned arms must receive control behavior."
            if normalized["phase"] == "P5-A0"
            else "Feasibility/integrity only; no efficacy or promotion claim."
        ),
        "content_free": True,
    }
