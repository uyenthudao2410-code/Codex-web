from __future__ import annotations

from collections import Counter
import hashlib
import math
from statistics import NormalDist
from typing import Any

from .orchestration_ledger import OrchestrationLedger
from .rework_diagnosis import high_confidence_replan_reason_category, repair_cause_for_failure_class


SOLUTION_SHADOW_EVENT = "solution_shadow_recommended"
SOLUTION_SHADOW_PATCH_SURFACE_EVENT = "solution_shadow_patch_surface_observed"
PATCH_SURFACE_EVENT = "patch_surface_observed"
PATCH_SURFACE_EVENT_TYPES = frozenset({PATCH_SURFACE_EVENT, SOLUTION_SHADOW_PATCH_SURFACE_EVENT})
ELIGIBLE_WORKFLOWS = frozenset({"feature", "bugfix"})
SCOPE_VALUES = frozenset({"localized_symbol", "localized_file", "bounded_multi_file", "cross_subsystem", "unknown"})
CONFIDENCE_VALUES = frozenset({"low", "medium", "high", "unknown"})
ORACLE_VALUES = frozenset({"weak", "moderate", "strong", "unknown"})
RISK_VALUES = frozenset({"low", "medium", "high", "unknown"})
SURFACE_KEYS = frozenset({"files", "symbols", "lines"})
EVALUATION_PROVENANCE_VALUES = frozenset({"representative", "benchmark", "synthetic"})
PATCH_SURFACE_FILE_ID_LIMIT = 256
PREDICTIVE_SIGNAL_NAMES = (
    "candidate_solution_scope",
    "root_cause_confidence",
    "oracle_strength",
    "expected_repair_risk",
    "smallest_causal_solution_scope",
)
REPLAN_DIAGNOSTIC_CATEGORIES = (
    "causal_solution_repair",
    "oracle_selection_repair",
    "formatting_only_repair",
    "environment_or_baseline_repair",
    "orchestration_repair",
    "unclassified",
)
REPLAN_DIAGNOSTIC_CATEGORY_BY_CAUSE = {
    "patch_context_ambiguity": "causal_solution_repair",
    "wrong_root_cause": "causal_solution_repair",
    "missing_requirement": "causal_solution_repair",
    "oracle_weakness": "oracle_selection_repair",
    "source_base_drift": "environment_or_baseline_repair",
    "environment_workdir": "environment_or_baseline_repair",
    "runtime_tool_failure": "orchestration_repair",
    "provider_capacity": "orchestration_repair",
    "proof_timeout": "orchestration_repair",
    "acceptance_correction": "orchestration_repair",
}


def _run_workflow(run: dict[str, Any] | None) -> str:
    metadata = run.get("metadata") if isinstance(run, dict) and isinstance(run.get("metadata"), dict) else {}
    return str(metadata.get("workflow") or "").strip().lower()


def _run_evidence_provenance(run: dict[str, Any] | None) -> str:
    metadata = run.get("metadata") if isinstance(run, dict) and isinstance(run.get("metadata"), dict) else {}
    evaluation = metadata.get("evaluation") if isinstance(metadata.get("evaluation"), dict) else {}
    value = str(evaluation.get("provenance") or "").strip().lower()
    return value if value in EVALUATION_PROVENANCE_VALUES else "unlabeled"


def _bounded_identifier(value: Any, *, name: str, limit: int = 128) -> str:
    text = str(value or "").strip()
    if not text or len(text) > limit or any(ord(char) < 32 for char in text):
        raise ValueError(f"{name} must be a non-empty bounded identifier")
    return text


def _path_identity(value: Any) -> str:
    path = str(value or "").strip().replace("\\", "/")
    return hashlib.sha256(path.encode("utf-8")).hexdigest() if path else ""


def _enum(value: Any, *, name: str, allowed: frozenset[str]) -> str:
    text = str(value or "").strip().lower()
    if text not in allowed:
        raise ValueError(f"{name} is invalid")
    return text


def _surface(value: Any, *, name: str) -> dict[str, int]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    extras = set(value) - SURFACE_KEYS
    if extras:
        raise ValueError(f"{name} contains unsupported fields")
    result: dict[str, int] = {}
    for key in sorted(SURFACE_KEYS):
        observed = value.get(key)
        if observed is None:
            continue
        if isinstance(observed, bool) or not isinstance(observed, int) or observed < 0:
            raise ValueError(f"{name}.{key} must be a non-negative integer when observed")
        result[key] = observed
    return result


def normalize_solution_shadow_recommendation(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("solution shadow recommendation must be an object")
    allowed = {
        "recommendation_id",
        "candidate_solution_scope",
        "estimated_touched_surface",
        "root_cause_confidence",
        "oracle_strength",
        "expected_repair_risk",
        "smallest_causal_solution",
    }
    if set(value) - allowed:
        raise ValueError("solution shadow recommendation contains unsupported fields")
    smallest = value.get("smallest_causal_solution")
    if not isinstance(smallest, dict) or set(smallest) - {"scope", "estimated_touched_surface"}:
        raise ValueError("smallest_causal_solution must contain only scope and estimated_touched_surface")
    return {
        "schema_version": 1,
        "recommendation_id": _bounded_identifier(value.get("recommendation_id"), name="recommendation_id"),
        "mode": "shadow_only",
        "candidate_solution_scope": _enum(value.get("candidate_solution_scope"), name="candidate_solution_scope", allowed=SCOPE_VALUES),
        "estimated_touched_surface": _surface(value.get("estimated_touched_surface"), name="estimated_touched_surface"),
        "root_cause_confidence": _enum(value.get("root_cause_confidence"), name="root_cause_confidence", allowed=CONFIDENCE_VALUES),
        "oracle_strength": _enum(value.get("oracle_strength"), name="oracle_strength", allowed=ORACLE_VALUES),
        "expected_repair_risk": _enum(value.get("expected_repair_risk"), name="expected_repair_risk", allowed=RISK_VALUES),
        "smallest_causal_solution": {
            "scope": _enum(smallest.get("scope"), name="smallest_causal_solution.scope", allowed=SCOPE_VALUES),
            "estimated_touched_surface": _surface(
                smallest.get("estimated_touched_surface"),
                name="smallest_causal_solution.estimated_touched_surface",
            ),
        },
        "automatic_policy_activation": False,
        "production_behavior_changed": False,
    }


def record_solution_shadow(
    ledger: OrchestrationLedger,
    *,
    run_id: str,
    wave_id: str,
    recommendation: dict[str, Any],
) -> dict[str, Any]:
    run = ledger.get_run(run_id)
    if run is None:
        raise ValueError("solution shadow run was not found")
    if str(run.get("status") or "") != "active":
        raise ValueError("solution shadow can only be recorded for an active run")
    workflow = _run_workflow(run)
    if workflow not in ELIGIBLE_WORKFLOWS:
        raise ValueError("solution shadow is limited to feature and bugfix workflows")
    waves = ledger.list_waves(run_id)
    wave = next((item for item in waves if str(item.get("wave_id") or "") == wave_id), None)
    if wave is None or str(wave.get("status") or "") != "active":
        raise ValueError("solution shadow wave must be the active wave of the run")

    normalized = normalize_solution_shadow_recommendation(recommendation)
    payload = {**normalized, "task_class": workflow, "recording_policy": "task_level_pre_first_write_v1"}
    events = ledger.list_events(run_id)
    existing = [item for item in events if str(item.get("event_type") or "") == SOLUTION_SHADOW_EVENT]
    if existing:
        first = existing[0]
        stored = first.get("payload") if isinstance(first.get("payload"), dict) else {}
        if str(stored.get("recommendation_id") or "") == normalized["recommendation_id"]:
            if stored != payload:
                raise ValueError("recommendation_id was already used with different solution shadow evidence")
            return {
                "recorded": False,
                "recommendation_id": normalized["recommendation_id"],
                "event_id": first.get("event_id"),
                "seq": first.get("seq"),
            }
        raise ValueError("a task-level solution shadow recommendation is already recorded for this run")
    if any(str(item.get("event_type") or "") == "write_lease_acquired" for item in events):
        raise ValueError("solution shadow recommendation must be recorded before the first write lease")

    event = ledger.append_event(run_id, wave_id=wave_id, event_type=SOLUTION_SHADOW_EVENT, payload=payload)
    return {
        "recorded": True,
        "recommendation_id": normalized["recommendation_id"],
        "event_id": event["event_id"],
        "seq": event["seq"],
    }


def _patch_surface_payload(patch_result: dict[str, Any]) -> dict[str, Any]:
    additions = patch_result.get("additions")
    removals = patch_result.get("removals")
    if (
        isinstance(additions, bool)
        or not isinstance(additions, int)
        or additions < 0
        or isinstance(removals, bool)
        or not isinstance(removals, int)
        or removals < 0
    ):
        raise ValueError("patch surface additions/removals must be non-negative integers")
    affected = patch_result.get("affected_files") if isinstance(patch_result.get("affected_files"), list) else []
    file_ids = sorted({
        identity
        for item in affected
        if isinstance(item, dict)
        for identity in [_path_identity(item.get("path"))]
        if identity
    })
    if not file_ids:
        raise ValueError("patch surface requires at least one affected file")
    complete = len(file_ids) <= PATCH_SURFACE_FILE_ID_LIMIT
    return {
        "schema_version": 1,
        "measurement": "applied_patch_delta_v1",
        "file_count": len(file_ids),
        "file_ids": file_ids[:PATCH_SURFACE_FILE_ID_LIMIT],
        "complete": complete,
        "additions": additions,
        "removals": removals,
        "line_changes": additions + removals,
        "content_free": True,
        "production_behavior_changed": False,
    }


def record_patch_surface(
    ledger: OrchestrationLedger,
    *,
    run_id: str,
    wave_id: str,
    patch_result: dict[str, Any],
) -> dict[str, Any]:
    """Record content-free applied-patch work for every authoritative mutation."""
    if patch_result.get("dry_run") is True:
        return {"recorded": False, "reason": "dry_run"}
    event = ledger.append_event(
        run_id,
        wave_id=wave_id,
        event_type=PATCH_SURFACE_EVENT,
        payload=_patch_surface_payload(patch_result),
    )
    return {"recorded": True, "event_id": event["event_id"], "seq": event["seq"]}


def record_solution_shadow_patch_surface(
    ledger: OrchestrationLedger,
    *,
    run_id: str,
    wave_id: str,
    patch_result: dict[str, Any],
) -> dict[str, Any]:
    """Backward-compatible P4-only patch event for historical callers/fixtures."""
    events = ledger.list_events(run_id)
    if not any(str(item.get("event_type") or "") == SOLUTION_SHADOW_EVENT for item in events):
        return {"recorded": False, "reason": "solution_shadow_unenrolled"}
    if patch_result.get("dry_run") is True:
        return {"recorded": False, "reason": "dry_run"}
    event = ledger.append_event(
        run_id,
        wave_id=wave_id,
        event_type=SOLUTION_SHADOW_PATCH_SURFACE_EVENT,
        payload=_patch_surface_payload(patch_result),
    )
    return {"recorded": True, "event_id": event["event_id"], "seq": event["seq"]}


def _observed_stage_duration(ledger: OrchestrationLedger, run_id: str, stage: str) -> float | None:
    spans = [item for item in ledger.list_observation_spans(run_id, limit=1000) if str(item.get("stage") or "") == stage]
    if not spans:
        return None
    return round(sum(max(0.0, float(item.get("duration_ms") or 0.0)) for item in spans), 6)


def _accepted_touched_surface(
    ledger: OrchestrationLedger,
    run_id: str,
    accepted_checkpoints: list[dict[str, Any]],
) -> dict[str, Any]:
    accepted_files = None
    file_measurement = "unobserved"
    receipt_ids: set[str] = set()
    receipt_ids_complete = False
    if accepted_checkpoints:
        metadata = accepted_checkpoints[-1].get("metadata") if isinstance(accepted_checkpoints[-1].get("metadata"), dict) else {}
        receipts = metadata.get("accepted_files") if isinstance(metadata.get("accepted_files"), dict) else {}
        if receipts:
            complete = receipts.get("complete") is True
            file_measurement = "accepted_file_receipts_complete" if complete else "accepted_file_receipts_incomplete"
            count = receipts.get("count")
            files = receipts.get("files") if isinstance(receipts.get("files"), list) else []
            for item in files:
                identity = _path_identity(item.get("path")) if isinstance(item, dict) else ""
                if identity:
                    receipt_ids.add(identity)
            receipt_ids_complete = complete and isinstance(count, int) and not isinstance(count, bool) and count >= 0 and len(receipt_ids) == count
            if complete and isinstance(count, int) and not isinstance(count, bool) and count >= 0:
                accepted_files = count

    surface_events = [
        item for item in ledger.list_events(run_id)
        if str(item.get("event_type") or "") in PATCH_SURFACE_EVENT_TYPES
    ]
    observed_ids: set[str] = set()
    additions = 0
    removals = 0
    events_complete = bool(surface_events)
    for event in surface_events:
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        events_complete = events_complete and payload.get("complete") is True
        observed_ids.update(str(item) for item in payload.get("file_ids", []) if isinstance(item, str) and item)
        additions += int(payload.get("additions") or 0)
        removals += int(payload.get("removals") or 0)
    line_coverage_complete = bool(
        surface_events
        and events_complete
        and receipt_ids_complete
        and observed_ids == receipt_ids
    )
    return {
        "files": accepted_files,
        "files_measurement": file_measurement,
        "lines": additions + removals if line_coverage_complete else None,
        "symbols": None,
        "lines_measurement": "applied_patch_delta_complete_v1" if line_coverage_complete else "applied_patch_delta_incomplete_v1" if surface_events else "unobserved",
        "symbols_measurement": "unobserved_semantic_symbol_delta_not_instrumented",
        "observed_patch_additions": additions if surface_events else None,
        "observed_patch_removals": removals if surface_events else None,
        "observed_patch_line_changes": additions + removals if surface_events else None,
        "patch_surface_event_count": len(surface_events),
        "patch_surface_file_count": len(observed_ids),
        "line_coverage_complete": line_coverage_complete,
    }


def _surface_comparison(estimated: Any, actual: dict[str, Any]) -> dict[str, Any]:
    estimate = estimated if isinstance(estimated, dict) else {}
    metrics: dict[str, Any] = {}
    for key in sorted(SURFACE_KEYS):
        expected = estimate.get(key)
        observed = actual.get(key)
        comparable = (
            isinstance(expected, int) and not isinstance(expected, bool)
            and isinstance(observed, int) and not isinstance(observed, bool)
        )
        metrics[key] = {
            "estimated": expected if isinstance(expected, int) and not isinstance(expected, bool) else None,
            "actual": observed if isinstance(observed, int) and not isinstance(observed, bool) else None,
            "delta": observed - expected if comparable else None,
            "absolute_error": abs(observed - expected) if comparable else None,
        }
    return {"metrics": metrics, "all_metrics_comparable": all(item["delta"] is not None for item in metrics.values())}


def _structured_replan_diagnostics(events: list[dict[str, Any]]) -> dict[str, Any]:
    replan_events = sorted(
        [item for item in events if str(item.get("state_after") or "").upper() == "REPLAN"],
        key=lambda item: int(item.get("seq") or 0),
    )
    reason_events = sorted(
        [item for item in events if str(item.get("event_type") or "") == "wave_replanned"],
        key=lambda item: int(item.get("seq") or 0),
    )
    failure_classes: Counter[str] = Counter()
    causes: Counter[str] = Counter()
    categories: Counter[str] = Counter()
    unclassified_failure_classes: Counter[str] = Counter()
    classification_sources: Counter[str] = Counter()
    reason_rules: Counter[str] = Counter()
    structured = 0
    classified = 0
    reason_fallback = 0
    for index, event in enumerate(replan_events):
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        failure_class = str(payload.get("failure_class") or "").strip().upper()
        cause = None
        if failure_class:
            structured += 1
            failure_classes[failure_class] += 1
            cause = repair_cause_for_failure_class(failure_class)
        if cause is not None:
            causes[cause] += 1
            categories[REPLAN_DIAGNOSTIC_CATEGORY_BY_CAUSE.get(cause, "unclassified")] += 1
            classification_sources["structured_failure_class"] += 1
            classified += 1
            continue

        if failure_class:
            unclassified_failure_classes[failure_class] += 1
        reason_payload = (
            reason_events[index].get("payload")
            if index < len(reason_events) and isinstance(reason_events[index].get("payload"), dict)
            else {}
        )
        reason_category, reason_rule = high_confidence_replan_reason_category(reason_payload.get("reason"))
        if reason_category is not None and reason_rule is not None:
            categories[reason_category] += 1
            classification_sources["durable_wave_replanned_reason_high_confidence"] += 1
            reason_rules[reason_rule] += 1
            reason_fallback += 1
            classified += 1
            continue
        categories["unclassified"] += 1
        classification_sources["unclassified"] += 1
    return {
        "schema_version": 1,
        "classification_method": "structured_failure_class_then_durable_replan_reason_v2",
        "diagnostic_only_not_repair_label": True,
        "historical_repaired_boolean_unchanged": True,
        "durable_replan_reason_used": reason_fallback > 0,
        "free_text_replan_reason_used": reason_fallback > 0,
        "reason_fallback_is_high_confidence_rules_only": True,
        "replan_transition_events": len(replan_events),
        "structured_failure_class_events": structured,
        "durable_wave_replanned_reason_events": len(reason_events),
        "classified_replan_events": classified,
        "classification_coverage": round(classified / len(replan_events), 6) if replan_events else None,
        "reason_fallback_events": reason_fallback,
        "classification_source_counts": dict(sorted(classification_sources.items())),
        "high_confidence_reason_rule_counts": dict(sorted(reason_rules.items())),
        "failure_class_counts": dict(sorted(failure_classes.items())),
        "cause_counts": dict(sorted(causes.items())),
        "derived_category_counts": {name: int(categories.get(name, 0)) for name in REPLAN_DIAGNOSTIC_CATEGORIES},
        "unclassified_structured_failure_classes": dict(sorted(unclassified_failure_classes.items())),
    }


def _causal_solution_repair_label(repair: dict[str, Any]) -> bool | None:
    if repair.get("workflow_replanned") is False:
        return False
    if repair.get("workflow_replanned") is not True:
        return None
    diagnostics = repair.get("replan_diagnostics") if isinstance(repair.get("replan_diagnostics"), dict) else {}
    total = int(diagnostics.get("replan_transition_events") or 0)
    classified = int(diagnostics.get("classified_replan_events") or 0)
    categories = diagnostics.get("derived_category_counts") if isinstance(diagnostics.get("derived_category_counts"), dict) else {}
    causal_events = int(categories.get("causal_solution_repair") or 0)
    post_replan_patch_events = int(repair.get("post_replan_patch_surface_events") or 0)
    if causal_events > 0 and post_replan_patch_events > 0:
        return True
    if total > 0 and classified == total:
        return False
    return None


def _repair_taxonomy(events: list[dict[str, Any]], replan_count: int) -> dict[str, Any]:
    replan_seqs = [
        int(item.get("seq") or 0)
        for item in events
        if str(item.get("state_after") or "").upper() == "REPLAN"
    ]
    first_replan_seq = min(replan_seqs) if replan_seqs else None
    post_replan_patch_events = [
        item
        for item in events
        if first_replan_seq is not None
        and int(item.get("seq") or 0) > first_replan_seq
        and str(item.get("event_type") or "") in PATCH_SURFACE_EVENT_TYPES
    ]
    workflow_replanned = replan_count > 0
    source_reworked_after_replan = bool(workflow_replanned and post_replan_patch_events)
    result = {
        "repaired": source_reworked_after_replan,
        "workflow_replanned": workflow_replanned,
        "proof_only_replan": bool(workflow_replanned and not source_reworked_after_replan),
        "replan_count": replan_count,
        "first_replan_seq": first_replan_seq,
        "post_replan_patch_surface_events": len(post_replan_patch_events),
        "label_method": "post_replan_applied_patch_delta_v1",
        "replan_diagnostics": _structured_replan_diagnostics(events),
    }
    result["causal_solution_repair"] = _causal_solution_repair_label(result)
    result["causal_solution_repair_label_method"] = "replan_diagnostics_plus_post_replan_patch_v1"
    return result


def _source_state_summary(
    ledger: OrchestrationLedger,
    run_id: str,
    *,
    prediction_wave_id: str,
) -> dict[str, Any]:
    waves = ledger.list_waves(run_id)
    normalized_prediction_wave_id = str(prediction_wave_id or "").strip()
    source_waves = [
        item
        for item in waves
        if normalized_prediction_wave_id
        and str(item.get("wave_id") or "").strip() == normalized_prediction_wave_id
    ]
    base_heads = sorted({
        str(item.get("base_head") or "").strip()
        for item in source_waves
        if str(item.get("base_head") or "").strip()
    })
    worktree_fingerprints = sorted({
        str(item.get("worktree_fp") or "").strip()
        for item in source_waves
        if str(item.get("worktree_fp") or "").strip()
    })
    run_base_heads = sorted({
        str(item.get("base_head") or "").strip()
        for item in waves
        if str(item.get("base_head") or "").strip()
    })
    run_worktree_fingerprints = sorted({
        str(item.get("worktree_fp") or "").strip()
        for item in waves
        if str(item.get("worktree_fp") or "").strip()
    })
    return {
        "measurement": "solution_shadow_prediction_wave_identity_v2",
        "wave_count": len(waves),
        "base_head_count": len(base_heads),
        "worktree_fingerprint_count": len(worktree_fingerprints),
        "base_head_changed_within_run": len(run_base_heads) > 1,
        "worktree_changed_within_run": len(run_worktree_fingerprints) > 1,
        "base_head_identities": base_heads,
        "worktree_fingerprint_identities": worktree_fingerprints,
        "prediction_wave_id": normalized_prediction_wave_id or None,
        "prediction_wave_found": bool(source_waves),
        "run_base_head_count": len(run_base_heads),
        "run_worktree_fingerprint_count": len(run_worktree_fingerprints),
        "content_free": True,
    }


def solution_shadow_run_report(ledger: OrchestrationLedger, run_id: str) -> dict[str, Any]:
    run = ledger.get_run(run_id)
    if run is None:
        return {"schema_version": 1, "run_id": run_id, "status": "missing", "recommendation": None, "outcome": None}
    events = ledger.list_events(run_id)
    shadows = [item for item in events if str(item.get("event_type") or "") == SOLUTION_SHADOW_EVENT]
    if not shadows:
        return {
            "schema_version": 1,
            "run_id": run_id,
            "status": "unenrolled",
            "task_class": _run_workflow(run) or None,
            "recommendation": None,
            "outcome": None,
            "automatic_policy_activation": False,
            "content_free": True,
        }

    shadow = shadows[0]
    recommendation = shadow.get("payload") if isinstance(shadow.get("payload"), dict) else {}
    first_write = next((item for item in events if str(item.get("event_type") or "") == "write_lease_acquired"), None)
    economics = ledger.accepted_result_economics(run_id)
    evaluation = ledger.accepted_result_evaluation(run_id)
    mcp = evaluation.get("mcp") if isinstance(evaluation.get("mcp"), dict) else {}
    milestones = evaluation.get("milestones") if isinstance(evaluation.get("milestones"), dict) else {}
    quality = economics.get("quality_outcome") if isinstance(economics.get("quality_outcome"), dict) else {}
    manual_fix = quality.get("manual_fix_required") if isinstance(quality.get("manual_fix_required"), bool) else None

    accepted_checkpoints = [item for item in ledger.list_checkpoints(run_id) if str(item.get("status") or "") == "accepted"]
    touched_surface = _accepted_touched_surface(ledger, run_id, accepted_checkpoints)

    proof_records = mcp.get("proof_records") if isinstance(mcp.get("proof_records"), int) else 0
    proof_duration = mcp.get("proof_duration_ms") if proof_records > 0 else None
    replan_count = int((economics.get("repair") or {}).get("replan_count") or 0)
    repair_taxonomy = _repair_taxonomy(events, replan_count)
    run_status = str(run.get("status") or "")
    outcome_final = run_status != "active"
    repair_result = repair_taxonomy if outcome_final else {
        "repaired": None,
        "workflow_replanned": None,
        "proof_only_replan": None,
        "replan_count": replan_count,
        "first_replan_seq": repair_taxonomy["first_replan_seq"],
        "post_replan_patch_surface_events": repair_taxonomy["post_replan_patch_surface_events"],
        "label_method": repair_taxonomy["label_method"],
        "replan_diagnostics": repair_taxonomy["replan_diagnostics"],
        "causal_solution_repair": None,
        "causal_solution_repair_label_method": repair_taxonomy["causal_solution_repair_label_method"],
    }
    return {
        "schema_version": 1,
        "run_id": run_id,
        "status": "observed",
        "task_class": _run_workflow(run) or None,
        "evidence_provenance": _run_evidence_provenance(run),
        "source_state": _source_state_summary(
            ledger,
            run_id,
            prediction_wave_id=str(shadow.get("wave_id") or ""),
        ),
        "recommendation": {**recommendation, "seq": shadow.get("seq"), "event_time": shadow.get("event_time")},
        "pre_mutation": {
            "recorded_before_first_write": first_write is None or int(shadow.get("seq") or 0) < int(first_write.get("seq") or 0),
            "recommendation_seq": shadow.get("seq"),
            "first_write_seq": first_write.get("seq") if first_write else None,
        },
        "outcome": {
            "final": outcome_final,
            "accepted": bool(economics.get("accepted")),
            "first_pass_accepted": bool(economics.get("first_pass_accepted")) if outcome_final else None,
            "repair": {"final": outcome_final, **repair_result},
            "ttar_ms": milestones.get("time_to_accepted_ms"),
            "touched_surface": touched_surface,
            "proof_cost": {
                "duration_ms": proof_duration,
                "records": proof_records,
                "measurement": "proof_record_duration" if proof_records > 0 else "unobserved",
                "monetary_cost": None,
            },
            "local_execution_ms": _observed_stage_duration(ledger, run_id, "local_execution"),
            "wait_ms": _observed_stage_duration(ledger, run_id, "wait"),
            "manual_intervention": manual_fix,
            "manual_intervention_source": "quality_outcome.manual_fix_required" if manual_fix is not None else "unobserved",
        },
        "recommendation_vs_outcome": {
            "candidate_surface": _surface_comparison(recommendation.get("estimated_touched_surface"), touched_surface),
            "smallest_causal_surface": _surface_comparison(
                (recommendation.get("smallest_causal_solution") or {}).get("estimated_touched_surface")
                if isinstance(recommendation.get("smallest_causal_solution"), dict) else {},
                touched_surface,
            ),
        },
        "automatic_policy_activation": False,
        "production_behavior_changed": False,
        "content_free": True,
    }


def _p50(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return round(float(ordered[(len(ordered) - 1) // 2]), 6)


def _signal_value(report: dict[str, Any], signal: str) -> str:
    recommendation = report.get("recommendation") if isinstance(report.get("recommendation"), dict) else {}
    if signal == "smallest_causal_solution_scope":
        smallest = recommendation.get("smallest_causal_solution") if isinstance(recommendation.get("smallest_causal_solution"), dict) else {}
        return str(smallest.get("scope") or "unknown")
    return str(recommendation.get(signal) or "unknown")


def _raw_repair_label(report: dict[str, Any]) -> int | None:
    repair = (report.get("outcome") or {}).get("repair") if isinstance(report.get("outcome"), dict) else {}
    repaired = repair.get("repaired") if isinstance(repair, dict) else None
    return 1 if repaired is True else 0 if repaired is False else None


def _repair_label(report: dict[str, Any]) -> int | None:
    repair = (report.get("outcome") or {}).get("repair") if isinstance(report.get("outcome"), dict) else {}
    repaired = repair.get("causal_solution_repair") if isinstance(repair, dict) else None
    return 1 if repaired is True else 0 if repaired is False else None


def _predictive_validation_fingerprint(report: dict[str, Any]) -> tuple[Any, ...]:
    recommendation = report.get("recommendation") if isinstance(report.get("recommendation"), dict) else {}
    source_state = report.get("source_state") if isinstance(report.get("source_state"), dict) else {}
    base_heads = tuple(sorted({
        str(item).strip()
        for item in source_state.get("base_head_identities", [])
        if isinstance(item, str) and str(item).strip()
    }))
    worktrees = tuple(sorted({
        str(item).strip()
        for item in source_state.get("worktree_fingerprint_identities", [])
        if isinstance(item, str) and str(item).strip()
    }))
    return (
        str(report.get("run_id") or "").strip(),
        str(report.get("task_class") or "").strip(),
        base_heads,
        worktrees,
        str(recommendation.get("event_time") or "").strip(),
        tuple(_signal_value(report, signal) for signal in PREDICTIVE_SIGNAL_NAMES),
        _repair_label(report),
    )


def _deduplicate_predictive_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    unique: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    duplicate_count = 0
    for row in rows:
        fingerprint = _predictive_validation_fingerprint(row)
        if fingerprint in seen:
            duplicate_count += 1
            continue
        seen.add(fingerprint)
        unique.append(row)
    return (unique, duplicate_count)


def _source_state_identity(report: dict[str, Any]) -> str:
    source_state = report.get("source_state") if isinstance(report.get("source_state"), dict) else {}
    base_heads = sorted({
        str(item).strip()
        for item in source_state.get("base_head_identities", [])
        if isinstance(item, str) and str(item).strip()
    })
    worktrees = sorted({
        str(item).strip()
        for item in source_state.get("worktree_fingerprint_identities", [])
        if isinstance(item, str) and str(item).strip()
    })
    if len(base_heads) == 1 and len(worktrees) == 1:
        return f"base:{base_heads[0]}|worktree:{worktrees[0]}"
    if len(base_heads) == 1 and not worktrees:
        return f"base:{base_heads[0]}"
    if len(worktrees) == 1 and not base_heads:
        return f"worktree:{worktrees[0]}"
    return ""


def _aggregate_replan_diagnostics(reports: list[dict[str, Any]]) -> dict[str, Any]:
    def summarize(group: list[dict[str, Any]]) -> dict[str, Any]:
        failure_classes: Counter[str] = Counter()
        causes: Counter[str] = Counter()
        categories: Counter[str] = Counter()
        unclassified_failure_classes: Counter[str] = Counter()
        classification_sources: Counter[str] = Counter()
        reason_rules: Counter[str] = Counter()
        replan_events = 0
        structured_events = 0
        classified_events = 0
        reason_fallback_events = 0
        post_replan_patch_surface_events = 0
        replanned_runs = 0
        for report in group:
            repair = (report.get("outcome") or {}).get("repair") if isinstance(report.get("outcome"), dict) else {}
            if not isinstance(repair, dict):
                continue
            if repair.get("workflow_replanned") is True:
                replanned_runs += 1
            post_replan_patch_surface_events += int(repair.get("post_replan_patch_surface_events") or 0)
            diagnostics = repair.get("replan_diagnostics") if isinstance(repair.get("replan_diagnostics"), dict) else {}
            replan_events += int(diagnostics.get("replan_transition_events") or 0)
            structured_events += int(diagnostics.get("structured_failure_class_events") or 0)
            classified_events += int(diagnostics.get("classified_replan_events") or 0)
            reason_fallback_events += int(diagnostics.get("reason_fallback_events") or 0)
            failure_classes.update({str(key): int(value) for key, value in (diagnostics.get("failure_class_counts") or {}).items()})
            causes.update({str(key): int(value) for key, value in (diagnostics.get("cause_counts") or {}).items()})
            categories.update({str(key): int(value) for key, value in (diagnostics.get("derived_category_counts") or {}).items()})
            classification_sources.update({
                str(key): int(value)
                for key, value in (diagnostics.get("classification_source_counts") or {}).items()
            })
            reason_rules.update({
                str(key): int(value)
                for key, value in (diagnostics.get("high_confidence_reason_rule_counts") or {}).items()
            })
            unclassified_failure_classes.update({
                str(key): int(value)
                for key, value in (diagnostics.get("unclassified_structured_failure_classes") or {}).items()
            })
        return {
            "run_count": len(group),
            "replanned_run_count": replanned_runs,
            "replan_transition_events": replan_events,
            "structured_failure_class_events": structured_events,
            "structured_failure_class_coverage": (
                round(structured_events / replan_events, 6) if replan_events else None
            ),
            "classified_replan_events": classified_events,
            "classification_coverage": round(classified_events / replan_events, 6) if replan_events else None,
            "reason_fallback_events": reason_fallback_events,
            "post_replan_patch_surface_events": post_replan_patch_surface_events,
            "classification_source_counts": dict(sorted(classification_sources.items())),
            "high_confidence_reason_rule_counts": dict(sorted(reason_rules.items())),
            "failure_class_counts": dict(sorted(failure_classes.items())),
            "cause_counts": dict(sorted(causes.items())),
            "derived_category_counts": {
                name: int(categories.get(name, 0)) for name in REPLAN_DIAGNOSTIC_CATEGORIES
            },
            "unclassified_structured_failure_classes": dict(sorted(unclassified_failure_classes.items())),
        }

    raw_repaired = [item for item in reports if _raw_repair_label(item) == 1]
    raw_nonrepaired = [item for item in reports if _raw_repair_label(item) == 0]
    causal_repaired = [item for item in reports if _repair_label(item) == 1]
    causal_nonrepaired = [item for item in reports if _repair_label(item) == 0]
    causal_unknown = [item for item in reports if _repair_label(item) is None]
    return {
        "schema_version": 1,
        "scope": "representative_terminal_runs",
        "historical_repair_label_method": "post_replan_applied_patch_delta_v1",
        "predictive_repair_label_method": "replan_diagnostics_plus_post_replan_patch_v1",
        "diagnostic_classification_method": "structured_failure_class_then_durable_replan_reason_v2",
        "diagnostic_only_not_repair_label": True,
        "historical_repaired_boolean_unchanged": True,
        "free_text_replan_reason_used": any(
            bool((((item.get("outcome") or {}).get("repair") or {}).get("replan_diagnostics") or {}).get("free_text_replan_reason_used"))
            for item in reports
        ),
        "overall": summarize(reports),
        "by_source_repair_label": {
            "repaired": summarize(raw_repaired),
            "nonrepaired": summarize(raw_nonrepaired),
        },
        "by_causal_solution_repair_label": {
            "repaired": summarize(causal_repaired),
            "nonrepaired": summarize(causal_nonrepaired),
            "unknown": summarize(causal_unknown),
        },
    }


def _wilson_interval(successes: int, total: int, z: float) -> tuple[float, float]:
    if total <= 0:
        return (0.0, 1.0)
    p = successes / total
    z2 = z * z
    denominator = 1.0 + z2 / total
    center = (p + z2 / (2.0 * total)) / denominator
    radius = z * math.sqrt((p * (1.0 - p) + z2 / (4.0 * total)) / total) / denominator
    return (max(0.0, center - radius), min(1.0, center + radius))


def _loocv_brier(rows: list[dict[str, Any]], signal: str) -> tuple[float | None, float | None, float | None]:
    usable = [(row, _repair_label(row)) for row in rows if _signal_value(row, signal) != "unknown"]
    usable = [(row, label) for row, label in usable if label is not None]
    if len(usable) < 2 or len({label for _, label in usable}) < 2:
        return (None, None, None)
    baseline_errors: list[float] = []
    signal_errors: list[float] = []
    for index, (held, label) in enumerate(usable):
        training = usable[:index] + usable[index + 1 :]
        if not training:
            continue
        baseline_probability = sum(item_label for _, item_label in training) / len(training)
        held_value = _signal_value(held, signal)
        bucket = [item_label for item, item_label in training if _signal_value(item, signal) == held_value]
        signal_probability = sum(bucket) / len(bucket) if bucket else baseline_probability
        baseline_errors.append((baseline_probability - label) ** 2)
        signal_errors.append((signal_probability - label) ** 2)
    if not baseline_errors:
        return (None, None, None)
    baseline = sum(baseline_errors) / len(baseline_errors)
    signal_score = sum(signal_errors) / len(signal_errors)
    return (round(baseline, 6), round(signal_score, 6), round(baseline - signal_score, 6))


def _holdout_brier(
    training: list[tuple[dict[str, Any], int]],
    held_out: list[tuple[dict[str, Any], int]],
    signal: str,
) -> tuple[list[float], list[float]]:
    if len(training) < 2 or not held_out or len({label for _, label in training}) < 2:
        return ([], [])
    baseline_probability = sum(label for _, label in training) / len(training)
    bucket_outcomes: dict[str, list[int]] = {}
    for item, label in training:
        bucket_outcomes.setdefault(_signal_value(item, signal), []).append(label)
    baseline_errors: list[float] = []
    signal_errors: list[float] = []
    for item, label in held_out:
        bucket = bucket_outcomes.get(_signal_value(item, signal), [])
        signal_probability = sum(bucket) / len(bucket) if bucket else baseline_probability
        baseline_errors.append((baseline_probability - label) ** 2)
        signal_errors.append((signal_probability - label) ** 2)
    return (baseline_errors, signal_errors)


def _leave_task_class_out_brier(rows: list[dict[str, Any]], signal: str) -> dict[str, Any]:
    usable = [
        (row, label)
        for row in rows
        for label in [_repair_label(row)]
        if label is not None and _signal_value(row, signal) != "unknown" and str(row.get("task_class") or "").strip()
    ]
    task_classes = sorted({str(row.get("task_class") or "").strip() for row, _ in usable})
    sample_counts = {
        task_class: sum(1 for row, _ in usable if str(row.get("task_class") or "").strip() == task_class)
        for task_class in task_classes
    }
    if len(task_classes) < 2:
        return {
            "evaluable": False,
            "reason": "at_least_two_task_classes_required",
            "task_class_count": len(task_classes),
            "task_class_sample_counts": sample_counts,
            "required_folds": len(task_classes),
            "evaluated_folds": 0,
            "baseline_brier": None,
            "signal_brier": None,
            "brier_gain": None,
        }

    baseline_errors: list[float] = []
    signal_errors: list[float] = []
    evaluated_folds = 0
    fold_failures: list[str] = []
    for task_class in task_classes:
        training = [(row, label) for row, label in usable if str(row.get("task_class") or "").strip() != task_class]
        held_out = [(row, label) for row, label in usable if str(row.get("task_class") or "").strip() == task_class]
        fold_baseline, fold_signal = _holdout_brier(training, held_out, signal)
        if not fold_baseline:
            fold_failures.append(task_class)
            continue
        baseline_errors.extend(fold_baseline)
        signal_errors.extend(fold_signal)
        evaluated_folds += 1
    evaluable = bool(baseline_errors and evaluated_folds == len(task_classes))
    if not evaluable:
        return {
            "evaluable": False,
            "reason": "every_task_class_fold_requires_training_outcome_variation",
            "task_class_count": len(task_classes),
            "task_class_sample_counts": sample_counts,
            "required_folds": len(task_classes),
            "evaluated_folds": evaluated_folds,
            "unevaluable_task_classes": fold_failures,
            "baseline_brier": None,
            "signal_brier": None,
            "brier_gain": None,
        }
    baseline = sum(baseline_errors) / len(baseline_errors)
    signal_score = sum(signal_errors) / len(signal_errors)
    return {
        "evaluable": True,
        "reason": "leave_one_task_class_out",
        "task_class_count": len(task_classes),
        "task_class_sample_counts": sample_counts,
        "required_folds": len(task_classes),
        "evaluated_folds": evaluated_folds,
        "baseline_brier": round(baseline, 6),
        "signal_brier": round(signal_score, 6),
        "brier_gain": round(baseline - signal_score, 6),
    }


def _leave_source_state_out_brier(rows: list[dict[str, Any]], signal: str) -> dict[str, Any]:
    candidates = [
        (row, label)
        for row in rows
        for label in [_repair_label(row)]
        if label is not None and _signal_value(row, signal) != "unknown"
    ]
    usable = [(row, label, _source_state_identity(row)) for row, label in candidates]
    missing_identity = sum(1 for _, _, identity in usable if not identity)
    if missing_identity:
        return {
            "evaluable": False,
            "reason": "single_source_state_identity_required_for_every_sample",
            "source_state_count": len({identity for _, _, identity in usable if identity}),
            "source_state_sample_counts": {},
            "missing_source_state_samples": missing_identity,
            "required_folds": 0,
            "evaluated_folds": 0,
            "baseline_brier": None,
            "signal_brier": None,
            "brier_gain": None,
        }
    source_states = sorted({identity for _, _, identity in usable})
    sample_counts = {
        identity: sum(1 for _, _, observed in usable if observed == identity)
        for identity in source_states
    }
    if len(source_states) < 2:
        return {
            "evaluable": False,
            "reason": "at_least_two_source_states_required",
            "source_state_count": len(source_states),
            "source_state_sample_counts": sample_counts,
            "missing_source_state_samples": 0,
            "required_folds": len(source_states),
            "evaluated_folds": 0,
            "baseline_brier": None,
            "signal_brier": None,
            "brier_gain": None,
        }

    baseline_errors: list[float] = []
    signal_errors: list[float] = []
    evaluated_folds = 0
    fold_failures: list[str] = []
    for source_state in source_states:
        training = [(row, label) for row, label, identity in usable if identity != source_state]
        held_out = [(row, label) for row, label, identity in usable if identity == source_state]
        fold_baseline, fold_signal = _holdout_brier(training, held_out, signal)
        if not fold_baseline:
            fold_failures.append(source_state)
            continue
        baseline_errors.extend(fold_baseline)
        signal_errors.extend(fold_signal)
        evaluated_folds += 1
    evaluable = bool(baseline_errors and evaluated_folds == len(source_states))
    if not evaluable:
        return {
            "evaluable": False,
            "reason": "every_source_state_fold_requires_training_outcome_variation",
            "source_state_count": len(source_states),
            "source_state_sample_counts": sample_counts,
            "missing_source_state_samples": 0,
            "required_folds": len(source_states),
            "evaluated_folds": evaluated_folds,
            "unevaluable_source_states": fold_failures,
            "baseline_brier": None,
            "signal_brier": None,
            "brier_gain": None,
        }
    baseline = sum(baseline_errors) / len(baseline_errors)
    signal_score = sum(signal_errors) / len(signal_errors)
    return {
        "evaluable": True,
        "reason": "leave_one_source_state_out",
        "source_state_count": len(source_states),
        "source_state_sample_counts": sample_counts,
        "missing_source_state_samples": 0,
        "required_folds": len(source_states),
        "evaluated_folds": evaluated_folds,
        "baseline_brier": round(baseline, 6),
        "signal_brier": round(signal_score, 6),
        "brier_gain": round(baseline - signal_score, 6),
    }


def _temporal_holdout_brier(rows: list[dict[str, Any]], signal: str) -> dict[str, Any]:
    usable = [
        (row, label, str((row.get("recommendation") or {}).get("event_time") or "").strip())
        for row in rows
        for label in [_repair_label(row)]
        if label is not None
        and _signal_value(row, signal) != "unknown"
        and isinstance(row.get("recommendation"), dict)
        and str((row.get("recommendation") or {}).get("event_time") or "").strip()
    ]
    usable.sort(key=lambda item: item[2])
    if len(usable) < 4:
        return {
            "evaluable": False,
            "reason": "ordered_training_and_holdout_support_required",
            "ordered_samples": len(usable),
            "training_samples": 0,
            "holdout_samples": 0,
            "baseline_brier": None,
            "signal_brier": None,
            "brier_gain": None,
        }
    split = max(2, (len(usable) * 2) // 3)
    split = min(split, len(usable) - 2)
    training = [(row, label) for row, label, _ in usable[:split]]
    held_out = [(row, label) for row, label, _ in usable[split:]]
    if len({label for _, label in training}) < 2 or len({label for _, label in held_out}) < 2:
        return {
            "evaluable": False,
            "reason": "training_and_later_holdout_outcome_variation_required",
            "ordered_samples": len(usable),
            "training_samples": len(training),
            "holdout_samples": len(held_out),
            "baseline_brier": None,
            "signal_brier": None,
            "brier_gain": None,
        }
    baseline_errors, signal_errors = _holdout_brier(training, held_out, signal)
    if not baseline_errors:
        return {
            "evaluable": False,
            "reason": "temporal_training_support_insufficient",
            "ordered_samples": len(usable),
            "training_samples": len(training),
            "holdout_samples": len(held_out),
            "baseline_brier": None,
            "signal_brier": None,
            "brier_gain": None,
        }
    baseline = sum(baseline_errors) / len(baseline_errors)
    signal_score = sum(signal_errors) / len(signal_errors)
    return {
        "evaluable": True,
        "reason": "earliest_two_thirds_train_latest_third_holdout",
        "ordered_samples": len(usable),
        "training_samples": len(training),
        "holdout_samples": len(held_out),
        "baseline_brier": round(baseline, 6),
        "signal_brier": round(signal_score, 6),
        "brier_gain": round(baseline - signal_score, 6),
    }


def _rolling_temporal_holdout_brier(
    rows: list[dict[str, Any]],
    signal: str,
    *,
    blocks: int = 10,
) -> dict[str, Any]:
    usable = [
        (row, label, str((row.get("recommendation") or {}).get("event_time") or "").strip())
        for row in rows
        for label in [_repair_label(row)]
        if label is not None
        and _signal_value(row, signal) != "unknown"
        and isinstance(row.get("recommendation"), dict)
        and str((row.get("recommendation") or {}).get("event_time") or "").strip()
    ]
    usable.sort(key=lambda item: item[2])
    if len(usable) < 6:
        return {
            "evaluable": False,
            "reason": "ordered_rolling_training_and_holdout_support_required",
            "ordered_samples": len(usable),
            "block_count": blocks,
            "required_windows": 0,
            "evaluated_windows": 0,
            "baseline_brier": None,
            "signal_brier": None,
            "brier_gain": None,
            "min_brier_gain": None,
            "window_brier_gains": [],
        }
    block_count = max(3, min(int(blocks), len(usable) // 2))
    block_size = max(1, len(usable) // block_count)
    baseline_errors: list[float] = []
    signal_errors: list[float] = []
    window_gains: list[float] = []
    unevaluable_windows: list[int] = []
    required_windows = 0
    for block in range(2, block_count):
        start = block * block_size
        if start >= len(usable):
            break
        end = len(usable) if block == block_count - 1 else min(len(usable), (block + 1) * block_size)
        if end <= start:
            continue
        required_windows += 1
        training = [(row, label) for row, label, _ in usable[:start]]
        held_out = [(row, label) for row, label, _ in usable[start:end]]
        if len({label for _, label in training}) < 2 or len({label for _, label in held_out}) < 2:
            unevaluable_windows.append(block)
            continue
        fold_baseline, fold_signal = _holdout_brier(training, held_out, signal)
        if not fold_baseline:
            unevaluable_windows.append(block)
            continue
        baseline_errors.extend(fold_baseline)
        signal_errors.extend(fold_signal)
        gain = (sum(fold_baseline) - sum(fold_signal)) / len(fold_baseline)
        window_gains.append(round(gain, 6))
    evaluable = bool(required_windows >= 2 and len(window_gains) == required_windows and baseline_errors)
    if not evaluable:
        return {
            "evaluable": False,
            "reason": "every_rolling_window_requires_training_and_holdout_outcome_variation",
            "ordered_samples": len(usable),
            "block_count": block_count,
            "block_size": block_size,
            "required_windows": required_windows,
            "evaluated_windows": len(window_gains),
            "unevaluable_windows": unevaluable_windows,
            "baseline_brier": None,
            "signal_brier": None,
            "brier_gain": None,
            "min_brier_gain": None,
            "window_brier_gains": window_gains,
        }
    baseline = sum(baseline_errors) / len(baseline_errors)
    signal_score = sum(signal_errors) / len(signal_errors)
    return {
        "evaluable": True,
        "reason": "expanding_training_rolling_forward_holdouts",
        "ordered_samples": len(usable),
        "block_count": block_count,
        "block_size": block_size,
        "required_windows": required_windows,
        "evaluated_windows": len(window_gains),
        "unevaluable_windows": [],
        "baseline_brier": round(baseline, 6),
        "signal_brier": round(signal_score, 6),
        "brier_gain": round(baseline - signal_score, 6),
        "min_brier_gain": min(window_gains),
        "window_brier_gains": window_gains,
    }


def _predictive_validation(reports: list[dict[str, Any]]) -> dict[str, Any]:
    raw_labeled = [item for item in reports if _repair_label(item) is not None]
    labeled, exact_duplicate_count = _deduplicate_predictive_rows(raw_labeled)
    outcome_variation = len({_repair_label(item) for item in labeled}) >= 2
    group_counts = {
        signal: len({value for item in labeled for value in [_signal_value(item, signal)] if value != "unknown"})
        for signal in PREDICTIVE_SIGNAL_NAMES
    }
    comparison_count = sum(count * (count - 1) // 2 for count in group_counts.values() if count >= 2)
    familywise_alpha = 0.05
    per_comparison_alpha = familywise_alpha / comparison_count if comparison_count else None
    z = NormalDist().inv_cdf(1.0 - per_comparison_alpha / 2.0) if per_comparison_alpha else None
    signals: dict[str, Any] = {}
    validated: list[str] = []
    for signal in PREDICTIVE_SIGNAL_NAMES:
        known = [item for item in labeled if _signal_value(item, signal) != "unknown"]
        groups: dict[str, list[int]] = {}
        for item in known:
            label = _repair_label(item)
            if label is not None:
                groups.setdefault(_signal_value(item, signal), []).append(label)
        baseline_brier, signal_brier, brier_gain = _loocv_brier(labeled, signal)
        intervals: dict[str, list[float]] = {}
        if z is not None:
            for value, outcomes in groups.items():
                low, high = _wilson_interval(sum(outcomes), len(outcomes), z)
                intervals[value] = [round(low, 6), round(high, 6)]
        separated_pairs: list[list[str]] = []
        values = sorted(intervals)
        for index, left in enumerate(values):
            for right in values[index + 1 :]:
                if intervals[left][1] < intervals[right][0] or intervals[right][1] < intervals[left][0]:
                    separated_pairs.append([left, right])
        family_holdout = _leave_task_class_out_brier(labeled, signal)
        source_state_holdout = _leave_source_state_out_brier(labeled, signal)
        temporal_holdout = _temporal_holdout_brier(labeled, signal)
        rolling_temporal_holdout = _rolling_temporal_holdout_brier(labeled, signal)
        pooled_validated = bool(outcome_variation and brier_gain is not None and brier_gain > 0 and separated_pairs)
        blockers: list[str] = []
        if not outcome_variation:
            blockers.append("repair_outcome_variation_missing")
        if brier_gain is None or brier_gain <= 0:
            blockers.append("pooled_leave_one_out_brier_gain_not_positive")
        if not separated_pairs:
            blockers.append("familywise_wilson_separation_missing")
        if family_holdout.get("evaluable") is not True:
            blockers.append("task_family_holdout_not_evaluable")
        elif not isinstance(family_holdout.get("brier_gain"), (int, float)) or family_holdout["brier_gain"] <= 0:
            blockers.append("task_family_holdout_brier_gain_not_positive")
        if source_state_holdout.get("evaluable") is not True:
            blockers.append("source_state_holdout_not_evaluable")
        elif not isinstance(source_state_holdout.get("brier_gain"), (int, float)) or source_state_holdout["brier_gain"] <= 0:
            blockers.append("source_state_holdout_brier_gain_not_positive")
        if temporal_holdout.get("evaluable") is not True:
            blockers.append("temporal_holdout_not_evaluable")
        elif not isinstance(temporal_holdout.get("brier_gain"), (int, float)) or temporal_holdout["brier_gain"] <= 0:
            blockers.append("temporal_holdout_brier_gain_not_positive")
        if rolling_temporal_holdout.get("evaluable") is not True:
            blockers.append("rolling_temporal_holdout_not_evaluable")
        elif not isinstance(rolling_temporal_holdout.get("min_brier_gain"), (int, float)) or rolling_temporal_holdout["min_brier_gain"] <= 0:
            blockers.append("rolling_temporal_holdout_brier_gain_not_positive")
        signal_validated = bool(pooled_validated and not blockers)
        if signal_validated:
            validated.append(signal)
        signals[signal] = {
            "known_value_samples": len(known),
            "unknown_value_samples": len(labeled) - len(known),
            "bucket_count": len(groups),
            "leave_one_out_baseline_brier": baseline_brier,
            "leave_one_out_signal_brier": signal_brier,
            "leave_one_out_brier_gain": brier_gain,
            "familywise_wilson_intervals": intervals,
            "separated_bucket_pairs": separated_pairs,
            "pooled_predictive_signal": pooled_validated,
            "task_family_holdout": family_holdout,
            "source_state_holdout": source_state_holdout,
            "temporal_holdout": temporal_holdout,
            "rolling_temporal_holdout": rolling_temporal_holdout,
            "validation_blockers": blockers,
            "validated_predictive_signal": signal_validated,
        }
    if validated:
        status = "predictive_signal_validation_available"
        reason = "representative_pooled_family_source_temporal_robustness_established"
    elif not labeled:
        status = "collecting"
        reason = "no_representative_terminal_outcomes"
    elif not outcome_variation:
        status = "collecting"
        reason = "representative_repair_outcome_variation_missing"
    else:
        status = "representative_descriptive_comparison_available_but_unvalidated"
        reason = "predictive_validation_not_yet_established"
    return {
        "schema_version": 1,
        "status": status,
        "reason": reason,
        "representative_terminal_outcomes": len(labeled),
        "representative_terminal_outcomes_raw": len(raw_labeled),
        "exact_duplicate_terminal_outcomes_excluded": exact_duplicate_count,
        "duplicate_support_policy": "exact_validation_evidence_deduplicated_v1",
        "source_state_identity_policy": "single_base_head_and_worktree_with_single_component_fallback_v1",
        "outcome_variation": outcome_variation,
        "familywise_confidence": 0.95,
        "comparison_count": comparison_count,
        "per_comparison_alpha": round(per_comparison_alpha, 8) if per_comparison_alpha is not None else None,
        "method": "pooled_loocv_brier_plus_bonferroni_wilson_plus_family_source_rolling_temporal_holdout_v5_causal_solution_repair",
        "robustness_requirements": {
            "exact_duplicate_support_excluded": True,
            "pooled_leave_one_out_brier_gain_positive": True,
            "familywise_wilson_separation": True,
            "leave_one_task_class_out_brier_gain_positive": True,
            "leave_one_source_state_out_brier_gain_positive": True,
            "latest_third_temporal_holdout_brier_gain_positive": True,
            "rolling_temporal_holdout_min_brier_gain_positive": True,
        },
        "repair_label_method": "replan_diagnostics_plus_post_replan_patch_v1",
        "historical_repair_label_method": "post_replan_applied_patch_delta_v1",
        "validated_signals": validated,
        "signals": signals,
        "causal_claim_allowed": False,
    }


def _latest_solution_shadow_run_ids(ledger: OrchestrationLedger, *, limit: int) -> list[str]:
    """Return the newest enrolled shadow runs without letting unrelated run churn evict evidence."""
    bulk_reader = getattr(ledger, "latest_solution_shadow_run_ids", None)
    if callable(bulk_reader):
        return bulk_reader(limit=limit)
    with ledger._lock, ledger._connect() as connection:
        rows = connection.execute(
            """
            SELECT run_id, MAX(seq) AS shadow_seq
            FROM events
            WHERE event_type=?
            GROUP BY run_id
            ORDER BY shadow_seq DESC
            LIMIT ?
            """,
            (SOLUTION_SHADOW_EVENT, limit),
        ).fetchall()
    return [str(row["run_id"]) for row in rows]


def solution_shadow_population_report(ledger: OrchestrationLedger, *, limit: int = 100) -> dict[str, Any]:
    bounded_limit = max(1, min(int(limit), 100))
    reports = []
    for run_id in _latest_solution_shadow_run_ids(ledger, limit=bounded_limit):
        report = solution_shadow_run_report(ledger, run_id)
        if report.get("status") == "observed":
            reports.append(report)
    terminal = [item for item in reports if (item.get("outcome") or {}).get("final") is True]
    representative_terminal = [item for item in terminal if item.get("evidence_provenance") == "representative"]
    signals = PREDICTIVE_SIGNAL_NAMES
    by_signal: dict[str, list[dict[str, Any]]] = {}
    variation: dict[str, bool] = {}
    representative_variation: dict[str, bool] = {}
    for signal in signals:
        groups: dict[str, list[dict[str, Any]]] = {}
        for report in terminal:
            groups.setdefault(_signal_value(report, signal), []).append(report)
        rows = []
        for value, group in sorted(groups.items()):
            outcomes = [item.get("outcome") or {} for item in group]
            representative_group = [item for item in group if item.get("evidence_provenance") == "representative"]
            representative_outcomes = [item.get("outcome") or {} for item in representative_group]
            raw_repaired = sum(1 for item in outcomes if (item.get("repair") or {}).get("repaired") is True)
            representative_raw_repaired = sum(
                1 for item in representative_outcomes if (item.get("repair") or {}).get("repaired") is True
            )
            repair_labels = [_repair_label(item) for item in group]
            known_repair_labels = [label for label in repair_labels if label is not None]
            repaired = sum(1 for label in known_repair_labels if label == 1)
            representative_repair_labels = [_repair_label(item) for item in representative_group]
            representative_known_repair_labels = [label for label in representative_repair_labels if label is not None]
            representative_repaired = sum(1 for label in representative_known_repair_labels if label == 1)
            accepted = sum(1 for item in outcomes if item.get("accepted") is True)
            first_pass = sum(1 for item in outcomes if item.get("first_pass_accepted") is True)
            ttar = [float(item["ttar_ms"]) for item in outcomes if isinstance(item.get("ttar_ms"), (int, float)) and not isinstance(item.get("ttar_ms"), bool)]
            rows.append({
                "value": value,
                "sample_count": len(group),
                "accepted_count": accepted,
                "first_pass_accepted_count": first_pass,
                "first_pass_acceptance_rate": round(first_pass / len(group), 6) if group else None,
                "raw_post_replan_patch_repaired_count": raw_repaired,
                "raw_post_replan_patch_repair_rate": round(raw_repaired / len(group), 6) if group else None,
                "repaired_count": repaired,
                "repair_label_known_count": len(known_repair_labels),
                "repair_label_unknown_count": len(group) - len(known_repair_labels),
                "repair_rate": round(repaired / len(known_repair_labels), 6) if known_repair_labels else None,
                "representative_sample_count": len(representative_group),
                "representative_raw_post_replan_patch_repaired_count": representative_raw_repaired,
                "representative_repaired_count": representative_repaired,
                "representative_repair_label_known_count": len(representative_known_repair_labels),
                "representative_repair_label_unknown_count": len(representative_group) - len(representative_known_repair_labels),
                "representative_repair_rate": (
                    round(representative_repaired / len(representative_known_repair_labels), 6)
                    if representative_known_repair_labels else None
                ),
                "ttar_samples": len(ttar),
                "ttar_p50_ms": _p50(ttar),
            })
        by_signal[signal] = rows
        variation[signal] = len(groups) >= 2
        representative_variation[signal] = sum(1 for row in rows if row["representative_sample_count"] > 0) >= 2

    predictor_coverage: dict[str, Any] = {}
    low_variance_signals: list[str] = []
    for signal in signals:
        representative_rows = [row for row in by_signal[signal] if row["representative_sample_count"] > 0]
        observed_values = {
            str(row["value"]): int(row["representative_sample_count"])
            for row in representative_rows
            if str(row["value"]) != "unknown"
        }
        known_samples = sum(observed_values.values())
        low_variance = len(observed_values) < 2
        if low_variance:
            low_variance_signals.append(signal)
        predictor_coverage[signal] = {
            "representative_samples": sum(int(row["representative_sample_count"]) for row in representative_rows),
            "known_value_samples": known_samples,
            "unknown_value_samples": sum(
                int(row["representative_sample_count"])
                for row in representative_rows
                if str(row["value"]) == "unknown"
            ),
            "observed_non_unknown_values": observed_values,
            "bucket_count": len(observed_values),
            "low_variance": low_variance,
        }

    representative_task_class_counts = dict(sorted(Counter(
        str(item.get("task_class") or "unknown") for item in representative_terminal
    ).items()))
    representative_base_heads = sorted({
        identity
        for item in representative_terminal
        for identity in (item.get("source_state") or {}).get("base_head_identities", [])
        if isinstance(identity, str) and identity
    })
    representative_worktree_fingerprints = sorted({
        identity
        for item in representative_terminal
        for identity in (item.get("source_state") or {}).get("worktree_fingerprint_identities", [])
        if isinstance(identity, str) and identity
    })
    representative_event_times = sorted(
        str((item.get("recommendation") or {}).get("event_time") or "")
        for item in representative_terminal
        if str((item.get("recommendation") or {}).get("event_time") or "")
    )
    prediction_source_state_diversity_observed = (
        len(representative_base_heads) > 1
        or len(representative_worktree_fingerprints) > 1
    )
    within_run_source_state_drift_observed = any(
        bool((item.get("source_state") or {}).get("base_head_changed_within_run"))
        or bool((item.get("source_state") or {}).get("worktree_changed_within_run"))
        for item in representative_terminal
    )

    overall_repaired = sum(1 for item in terminal if ((item.get("outcome") or {}).get("repair") or {}).get("repaired") is True)
    representative_repaired = sum(
        1 for item in representative_terminal if ((item.get("outcome") or {}).get("repair") or {}).get("repaired") is True
    )
    causal_labels = [_repair_label(item) for item in terminal]
    causal_known = [label for label in causal_labels if label is not None]
    causal_repaired = sum(1 for label in causal_known if label == 1)
    representative_causal_labels = [_repair_label(item) for item in representative_terminal]
    representative_causal_known = [label for label in representative_causal_labels if label is not None]
    representative_causal_repaired = sum(1 for label in representative_causal_known if label == 1)
    provenance_counts: dict[str, int] = {}
    terminal_provenance_counts: dict[str, int] = {}
    for item in reports:
        key = str(item.get("evidence_provenance") or "unlabeled")
        provenance_counts[key] = provenance_counts.get(key, 0) + 1
    for item in terminal:
        key = str(item.get("evidence_provenance") or "unlabeled")
        terminal_provenance_counts[key] = terminal_provenance_counts.get(key, 0) + 1
    records = [
        {
            "run_id": item.get("run_id"),
            "task_class": item.get("task_class"),
            "evidence_provenance": item.get("evidence_provenance"),
            "source_state": item.get("source_state"),
            "predictors": {
                "candidate_solution_scope": (item.get("recommendation") or {}).get("candidate_solution_scope"),
                "estimated_touched_surface": (item.get("recommendation") or {}).get("estimated_touched_surface"),
                "root_cause_confidence": (item.get("recommendation") or {}).get("root_cause_confidence"),
                "oracle_strength": (item.get("recommendation") or {}).get("oracle_strength"),
                "expected_repair_risk": (item.get("recommendation") or {}).get("expected_repair_risk"),
                "smallest_causal_solution": (item.get("recommendation") or {}).get("smallest_causal_solution"),
            },
            "outcome": item.get("outcome"),
            "comparison": item.get("recommendation_vs_outcome"),
        }
        for item in terminal
    ]
    descriptive_available = bool(terminal and any(variation.values()))
    representative_descriptive_available = bool(representative_terminal and any(representative_variation.values()))
    predictive_validation = _predictive_validation(representative_terminal)
    replan_diagnostics = _aggregate_replan_diagnostics(representative_terminal)
    can_answer = bool(predictive_validation["validated_signals"])
    return {
        "schema_version": 1,
        "mode": "solution_economics_shadow_v1",
        "population_scope": "latest_shadow_runs_v2",
        "scan_limit": bounded_limit,
        "scan_limit_semantics": "shadow_runs_with_solution_shadow_event",
        "cohort": {
            "shadow_tasks": len(reports),
            "terminal_shadow_tasks": len(terminal),
            "repaired_tasks": overall_repaired,
            "repair_rate": round(overall_repaired / len(terminal), 6) if terminal else None,
            "historical_repair_label_method": "post_replan_applied_patch_delta_v1",
            "causal_solution_repair_tasks": causal_repaired,
            "causal_solution_nonrepair_tasks": len(causal_known) - causal_repaired,
            "causal_solution_repair_unknown_tasks": len(terminal) - len(causal_known),
            "causal_solution_repair_rate": round(causal_repaired / len(causal_known), 6) if causal_known else None,
            "predictive_repair_label_method": "replan_diagnostics_plus_post_replan_patch_v1",
            "provenance_counts": provenance_counts,
            "terminal_provenance_counts": terminal_provenance_counts,
            "representative_terminal_shadow_tasks": len(representative_terminal),
            "representative_repaired_tasks": representative_repaired,
            "representative_nonrepaired_tasks": len(representative_terminal) - representative_repaired,
            "representative_causal_solution_repair_tasks": representative_causal_repaired,
            "representative_causal_solution_nonrepair_tasks": len(representative_causal_known) - representative_causal_repaired,
            "representative_causal_solution_repair_unknown_tasks": len(representative_terminal) - len(representative_causal_known),
        },
        "predictor_variation": variation,
        "representative_predictor_variation": representative_variation,
        "predictor_coverage": predictor_coverage,
        "workload_guidance": {
            "low_variance_signals": low_variance_signals,
            "naturally_diverse_representative_workload_required": bool(low_variance_signals),
            "representative_task_class_counts": representative_task_class_counts,
            "shadow_prediction_manipulation_for_variance_forbidden": True,
        },
        "measurement_design": {
            "design": "longitudinal_evolving_checkout_v1",
            "representative_base_head_count": len(representative_base_heads),
            "representative_worktree_fingerprint_count": len(representative_worktree_fingerprints),
            "source_state_drift_observed": (
                prediction_source_state_diversity_observed
                or within_run_source_state_drift_observed
            ),
            "prediction_source_state_diversity_observed": prediction_source_state_diversity_observed,
            "within_run_source_state_drift_observed": within_run_source_state_drift_observed,
            "first_representative_shadow_event_time": representative_event_times[0] if representative_event_times else None,
            "last_representative_shadow_event_time": representative_event_times[-1] if representative_event_times else None,
            "iid_assumption": False,
            "association_only": True,
            "time_or_source_state_confounding_eliminated": False,
            "predictive_task_family_holdout_required": True,
            "predictive_source_state_holdout_required": True,
            "predictive_temporal_holdout_required": True,
            "predictive_rolling_temporal_holdout_required": True,
        },
        "replan_diagnostics": replan_diagnostics,
        "by_signal": by_signal,
        "predictive_validation": predictive_validation,
        "records": records,
        "p4_gate": {
            "status": predictive_validation["status"] if representative_terminal else "nonrepresentative_descriptive_comparison_only" if descriptive_available else "collecting",
            "can_answer_which_signals_predict_repair": can_answer,
            "reason": predictive_validation["reason"] if representative_terminal else "representative_evidence_required" if descriptive_available else "predictive_validation_not_yet_established",
            "validated_signals": list(predictive_validation["validated_signals"]),
            "representative_terminal_tasks": len(representative_terminal),
            "representative_repaired_tasks": representative_causal_repaired,
            "representative_nonrepaired_tasks": len(representative_causal_known) - representative_causal_repaired,
            "representative_unknown_repair_tasks": len(representative_terminal) - len(representative_causal_known),
            "representative_raw_post_replan_patch_repaired_tasks": representative_repaired,
            "repair_label_method": "replan_diagnostics_plus_post_replan_patch_v1",
            "automatic_policy_activation": False,
        },
        "policy": {
            "shadow_only": True,
            "loc_is_explanatory_not_objective": True,
            "unknown_is_not_zero": True,
            "cross_task_counterfactual_inference_forbidden": True,
            "predictive_promotion_requires_representative_provenance": True,
            "benchmark_synthetic_unlabeled_are_not_promotion_evidence": True,
            "predictive_validation_is_association_not_causality": True,
            "predictive_validation_requires_task_family_holdout": True,
            "predictive_validation_requires_source_state_holdout": True,
            "predictive_validation_requires_temporal_holdout": True,
            "predictive_validation_requires_rolling_temporal_holdout": True,
            "longitudinal_evolving_checkout_not_iid": True,
            "source_state_time_drift_reported": True,
            "semantic_localization_is_measurement_context_not_repair_label": True,
            "repair_label_uses_post_replan_patch_surface": True,
            "historical_repaired_boolean_preserved": True,
            "predictive_repair_label_uses_causal_replan_diagnostics": True,
            "durable_replan_reason_fallback_is_diagnostic_only": True,
            "workflow_replan_is_not_solution_repair": True,
            "p5_automatic_start": False,
        },
        "content_free": True,
    }
