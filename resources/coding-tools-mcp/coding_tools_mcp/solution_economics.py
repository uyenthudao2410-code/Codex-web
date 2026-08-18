from __future__ import annotations

from typing import Any

from .orchestration_ledger import OrchestrationLedger


SOLUTION_SHADOW_EVENT = "solution_shadow_recommended"
ELIGIBLE_WORKFLOWS = frozenset({"feature", "bugfix"})
SCOPE_VALUES = frozenset({"localized_symbol", "localized_file", "bounded_multi_file", "cross_subsystem", "unknown"})
CONFIDENCE_VALUES = frozenset({"low", "medium", "high", "unknown"})
ORACLE_VALUES = frozenset({"weak", "moderate", "strong", "unknown"})
RISK_VALUES = frozenset({"low", "medium", "high", "unknown"})
SURFACE_KEYS = frozenset({"files", "symbols", "lines"})
EVALUATION_PROVENANCE_VALUES = frozenset({"representative", "benchmark", "synthetic"})


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


def _observed_stage_duration(ledger: OrchestrationLedger, run_id: str, stage: str) -> float | None:
    spans = [item for item in ledger.list_observation_spans(run_id, limit=1000) if str(item.get("stage") or "") == stage]
    if not spans:
        return None
    return round(sum(max(0.0, float(item.get("duration_ms") or 0.0)) for item in spans), 6)


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
    accepted_files = None
    file_measurement = "unobserved"
    if accepted_checkpoints:
        metadata = accepted_checkpoints[-1].get("metadata") if isinstance(accepted_checkpoints[-1].get("metadata"), dict) else {}
        receipts = metadata.get("accepted_files") if isinstance(metadata.get("accepted_files"), dict) else {}
        if receipts:
            file_measurement = "accepted_file_receipts_complete" if receipts.get("complete") is True else "accepted_file_receipts_incomplete"
            count = receipts.get("count")
            if receipts.get("complete") is True and isinstance(count, int) and not isinstance(count, bool) and count >= 0:
                accepted_files = count

    proof_records = mcp.get("proof_records") if isinstance(mcp.get("proof_records"), int) else 0
    proof_duration = mcp.get("proof_duration_ms") if proof_records > 0 else None
    replan_count = int((economics.get("repair") or {}).get("replan_count") or 0)
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
                "repaired": (replan_count > 0) if outcome_final else None,
                "replan_count": replan_count,
            },
            "ttar_ms": milestones.get("time_to_accepted_ms"),
            "touched_surface": {
                "files": accepted_files,
                "files_measurement": file_measurement,
                "lines": None,
                "symbols": None,
                "lines_measurement": "unobserved",
                "symbols_measurement": "unobserved",
            },
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
        "automatic_policy_activation": False,
        "production_behavior_changed": False,
        "content_free": True,
    }


def _p50(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return round(float(ordered[(len(ordered) - 1) // 2]), 6)


def solution_shadow_population_report(ledger: OrchestrationLedger, *, limit: int = 100) -> dict[str, Any]:
    bounded_limit = max(1, min(int(limit), 100))
    reports = []
    for run in ledger.list_runs(limit=bounded_limit):
        report = solution_shadow_run_report(ledger, str(run.get("run_id") or ""))
        if report.get("status") == "observed":
            reports.append(report)
    terminal = [item for item in reports if (item.get("outcome") or {}).get("final") is True]
    representative_terminal = [item for item in terminal if item.get("evidence_provenance") == "representative"]
    signals = ("candidate_solution_scope", "root_cause_confidence", "oracle_strength", "expected_repair_risk")
    by_signal: dict[str, list[dict[str, Any]]] = {}
    variation: dict[str, bool] = {}
    representative_variation: dict[str, bool] = {}
    for signal in signals:
        groups: dict[str, list[dict[str, Any]]] = {}
        for report in terminal:
            recommendation = report.get("recommendation") if isinstance(report.get("recommendation"), dict) else {}
            groups.setdefault(str(recommendation.get(signal) or "unknown"), []).append(report)
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
        }
        for item in terminal
    ]
    descriptive_available = bool(terminal and any(variation.values()))
    representative_descriptive_available = bool(representative_terminal and any(representative_variation.values()))
    return {
        "schema_version": 1,
        "mode": "solution_economics_shadow_v1",
        "population_scope": "latest_runs_v1",
        "scan_limit": bounded_limit,
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
        "records": records,
        "p4_gate": {
            "status": (
                "representative_descriptive_comparison_available_but_unvalidated"
                if representative_descriptive_available
                else "nonrepresentative_descriptive_comparison_only"
                if descriptive_available
                else "collecting"
            ),
            "can_answer_which_signals_predict_repair": False,
            "reason": "predictive_validation_not_yet_established",
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
        },
        "content_free": True,
    }
