from __future__ import annotations

import hashlib
import math
from statistics import NormalDist
from typing import Any

from .orchestration_ledger import OrchestrationLedger


SOLUTION_SHADOW_EVENT = "solution_shadow_recommended"
SOLUTION_SHADOW_PATCH_SURFACE_EVENT = "solution_shadow_patch_surface_observed"
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


def record_solution_shadow_patch_surface(
    ledger: OrchestrationLedger,
    *,
    run_id: str,
    wave_id: str,
    patch_result: dict[str, Any],
) -> dict[str, Any]:
    """Record exact applied-patch line work without persisting source paths/content."""
    events = ledger.list_events(run_id)
    if not any(str(item.get("event_type") or "") == SOLUTION_SHADOW_EVENT for item in events):
        return {"recorded": False, "reason": "solution_shadow_unenrolled"}
    if patch_result.get("dry_run") is True:
        return {"recorded": False, "reason": "dry_run"}
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
    event = ledger.append_event(
        run_id,
        wave_id=wave_id,
        event_type=SOLUTION_SHADOW_PATCH_SURFACE_EVENT,
        payload={
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
        },
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
        if str(item.get("event_type") or "") == SOLUTION_SHADOW_PATCH_SURFACE_EVENT
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
        and str(item.get("event_type") or "") == SOLUTION_SHADOW_PATCH_SURFACE_EVENT
    ]
    workflow_replanned = replan_count > 0
    source_reworked_after_replan = bool(workflow_replanned and post_replan_patch_events)
    return {
        "repaired": source_reworked_after_replan,
        "workflow_replanned": workflow_replanned,
        "proof_only_replan": bool(workflow_replanned and not source_reworked_after_replan),
        "replan_count": replan_count,
        "first_replan_seq": first_replan_seq,
        "post_replan_patch_surface_events": len(post_replan_patch_events),
        "label_method": "post_replan_applied_patch_delta_v1",
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
    return {
        "schema_version": 1,
        "run_id": run_id,
        "status": "observed",
        "task_class": _run_workflow(run) or None,
        "evidence_provenance": _run_evidence_provenance(run),
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
            "repair": {
                "final": outcome_final,
                **repair_taxonomy if outcome_final else {
                    "repaired": None,
                    "workflow_replanned": None,
                    "proof_only_replan": None,
                    "replan_count": replan_count,
                    "first_replan_seq": repair_taxonomy["first_replan_seq"],
                    "post_replan_patch_surface_events": repair_taxonomy["post_replan_patch_surface_events"],
                    "label_method": repair_taxonomy["label_method"],
                },
            },
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


def _repair_label(report: dict[str, Any]) -> int | None:
    repair = (report.get("outcome") or {}).get("repair") if isinstance(report.get("outcome"), dict) else {}
    repaired = repair.get("repaired") if isinstance(repair, dict) else None
    return 1 if repaired is True else 0 if repaired is False else None


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


def _predictive_validation(reports: list[dict[str, Any]]) -> dict[str, Any]:
    labeled = [item for item in reports if _repair_label(item) is not None]
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
        signal_validated = bool(outcome_variation and brier_gain is not None and brier_gain > 0 and separated_pairs)
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
            "validated_predictive_signal": signal_validated,
        }
    if validated:
        status = "predictive_signal_validation_available"
        reason = "representative_out_of_sample_gain_with_familywise_interval_separation"
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
        "outcome_variation": outcome_variation,
        "familywise_confidence": 0.95,
        "comparison_count": comparison_count,
        "per_comparison_alpha": round(per_comparison_alpha, 8) if per_comparison_alpha is not None else None,
        "method": "leave_one_out_brier_plus_bonferroni_wilson_separation_v2_source_repair",
        "repair_label_method": "post_replan_applied_patch_delta_v1",
        "validated_signals": validated,
        "signals": signals,
        "causal_claim_allowed": False,
    }


def _latest_solution_shadow_run_ids(ledger: OrchestrationLedger, *, limit: int) -> list[str]:
    """Return the newest enrolled shadow runs without letting unrelated run churn evict evidence."""
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
            repaired = sum(1 for item in outcomes if (item.get("repair") or {}).get("repaired") is True)
            representative_repaired = sum(
                1 for item in representative_outcomes if (item.get("repair") or {}).get("repaired") is True
            )
            accepted = sum(1 for item in outcomes if item.get("accepted") is True)
            first_pass = sum(1 for item in outcomes if item.get("first_pass_accepted") is True)
            ttar = [float(item["ttar_ms"]) for item in outcomes if isinstance(item.get("ttar_ms"), (int, float)) and not isinstance(item.get("ttar_ms"), bool)]
            rows.append({
                "value": value,
                "sample_count": len(group),
                "accepted_count": accepted,
                "first_pass_accepted_count": first_pass,
                "first_pass_acceptance_rate": round(first_pass / len(group), 6) if group else None,
                "repaired_count": repaired,
                "repair_rate": round(repaired / len(group), 6) if group else None,
                "representative_sample_count": len(representative_group),
                "representative_repaired_count": representative_repaired,
                "representative_repair_rate": (
                    round(representative_repaired / len(representative_group), 6) if representative_group else None
                ),
                "ttar_samples": len(ttar),
                "ttar_p50_ms": _p50(ttar),
            })
        by_signal[signal] = rows
        variation[signal] = len(groups) >= 2
        representative_variation[signal] = sum(1 for row in rows if row["representative_sample_count"] > 0) >= 2

    overall_repaired = sum(1 for item in terminal if ((item.get("outcome") or {}).get("repair") or {}).get("repaired") is True)
    representative_repaired = sum(
        1 for item in representative_terminal if ((item.get("outcome") or {}).get("repair") or {}).get("repaired") is True
    )
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
            "provenance_counts": provenance_counts,
            "terminal_provenance_counts": terminal_provenance_counts,
            "representative_terminal_shadow_tasks": len(representative_terminal),
            "representative_repaired_tasks": representative_repaired,
            "representative_nonrepaired_tasks": len(representative_terminal) - representative_repaired,
        },
        "predictor_variation": variation,
        "representative_predictor_variation": representative_variation,
        "by_signal": by_signal,
        "predictive_validation": predictive_validation,
        "records": records,
        "p4_gate": {
            "status": predictive_validation["status"] if representative_terminal else "nonrepresentative_descriptive_comparison_only" if descriptive_available else "collecting",
            "can_answer_which_signals_predict_repair": can_answer,
            "reason": predictive_validation["reason"] if representative_terminal else "representative_evidence_required" if descriptive_available else "predictive_validation_not_yet_established",
            "validated_signals": list(predictive_validation["validated_signals"]),
            "representative_terminal_tasks": len(representative_terminal),
            "representative_repaired_tasks": representative_repaired,
            "representative_nonrepaired_tasks": len(representative_terminal) - representative_repaired,
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
            "repair_label_uses_post_replan_patch_surface": True,
            "workflow_replan_is_not_solution_repair": True,
            "p5_automatic_start": False,
        },
        "content_free": True,
    }
