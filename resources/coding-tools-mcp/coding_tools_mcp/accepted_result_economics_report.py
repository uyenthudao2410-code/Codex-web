from __future__ import annotations

import json
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any

from .orchestration_ledger import OrchestrationLedger
from .rework_diagnosis import repair_cause_for_failure_class

DETERMINISTIC_ROUTES = frozenset({"", "unknown", "deterministic", "mcp_deterministic", "controller_manual"})
FOCUS_WORKFLOWS = frozenset({"feature", "bugfix", "diagnose"})
CURRENT_DRE_CAUSES = frozenset({"source_base_drift", "acceptance_correction"})


def _percentile(values: list[int], percentile: int) -> int | None:
    if not values:
        return None
    ordered = sorted(max(0, int(value)) for value in values)
    rank = max(1, min(len(ordered), (len(ordered) * percentile + 99) // 100))
    return ordered[rank - 1]


def _ratio(numerator: int | float | None, denominator: int | float | None) -> float | None:
    if not isinstance(numerator, (int, float)) or isinstance(numerator, bool):
        return None
    if not isinstance(denominator, (int, float)) or isinstance(denominator, bool) or denominator <= 0:
        return None
    return round(float(numerator) / float(denominator), 6)


def _performance_state(workspace: Path) -> dict[str, Any]:
    path = workspace / ".coding-tools" / "performance.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def _workflow(run: dict[str, Any]) -> str:
    metadata = run.get("metadata") if isinstance(run.get("metadata"), dict) else {}
    return str(metadata.get("workflow") or "unknown").strip().lower() or "unknown"


def _first_base_head(ledger: OrchestrationLedger, run_id: str) -> str:
    waves = ledger.list_waves(run_id)
    return str(waves[0].get("base_head") or "").strip().lower() if waves else ""


def _is_deterministic_run(ledger: OrchestrationLedger, run_id: str) -> bool:
    actual_routes = {
        str(delegation.get("route_resolved") or "").strip().lower()
        for wave in ledger.list_waves(run_id)
        for delegation in ledger.list_delegations(str(wave["wave_id"]))
        if str(delegation.get("route_resolved") or "").strip()
    }
    if any(route not in DETERMINISTIC_ROUTES for route in actual_routes):
        return False
    economics = ledger.accepted_result_economics(run_id)
    route = str((economics.get("route") or {}).get("resolved") or "unknown").strip().lower()
    return route in DETERMINISTIC_ROUTES


def _accepted_runs(ledger: OrchestrationLedger, *, limit: int) -> list[dict[str, Any]]:
    bounded_limit = max(1, min(int(limit), 5000))
    connection = sqlite3.connect(ledger.path, timeout=5.0)
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute(
            """
            SELECT run_id
            FROM runs
            WHERE status='accepted'
              AND (json_extract(metadata_json, '$.evaluation.provenance') IS NULL
                   OR lower(json_extract(metadata_json, '$.evaluation.provenance'))='representative')
              AND (json_extract(metadata_json, '$.evaluation.policy') IS NULL
                   OR lower(json_extract(metadata_json, '$.evaluation.policy'))='chatweb_mcp')
            ORDER BY started_at, run_id
            LIMIT ?
            """,
            (bounded_limit,),
        ).fetchall()
    finally:
        connection.close()
    result: list[dict[str, Any]] = []
    for row in rows:
        run_id = str(row["run_id"])
        run = ledger.get_run(run_id)
        if run is not None and _is_deterministic_run(ledger, run_id):
            result.append(run)
    return result


def _resource_distribution(metrics: list[dict[str, Any]]) -> dict[str, Any]:
    keys = ("local_execution_ms", "estimated_wait_ms", "tool_calls", "errors", "request_bytes", "response_bytes", "model_visible_bytes")
    result: dict[str, Any] = {}
    for key in keys:
        values = [int(item[key]) for item in metrics if isinstance(item.get(key), int) and not isinstance(item.get(key), bool) and int(item[key]) >= 0]
        result[key] = {"samples": len(values), "p50": _percentile(values, 50), "p90": _percentile(values, 90), "total": sum(values) if values else None}
    result["estimated_wait_to_local_execution_ratio"] = _ratio(result["estimated_wait_ms"]["total"], result["local_execution_ms"]["total"])
    result["estimated_wait_semantics"] = "gap_between_consecutive_mcp_tool_calls_capped_at_30_minutes; may include controller/model/network/operator time; not proven avoidable loss and not provider billing"
    return result


def _cost_coverage(evaluations: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(evaluations)
    total_cost_complete = controller_cost_observed = controller_token_any = provider_usage_observed = provider_cost_complete = 0
    for item in evaluations:
        controller = item.get("controller") if isinstance(item.get("controller"), dict) else {}
        if isinstance(controller.get("monetary_cost"), (int, float)) and not isinstance(controller.get("monetary_cost"), bool):
            controller_cost_observed += 1
        usage = controller.get("usage") if isinstance(controller.get("usage"), dict) else {}
        if any(isinstance(value, int) and not isinstance(value, bool) for value in usage.values()):
            controller_token_any += 1
        external = item.get("external") if isinstance(item.get("external"), dict) else {}
        provider = external.get("provider_economics") if isinstance(external.get("provider_economics"), dict) else {}
        if int(provider.get("usage_event_count") or 0) > 0:
            provider_usage_observed += 1
        if provider.get("cost_complete") is True and provider.get("attribution_complete") is True:
            provider_cost_complete += 1
        total_cost = item.get("total_monetary_cost") if isinstance(item.get("total_monetary_cost"), dict) else {}
        if total_cost.get("complete") is True and isinstance(total_cost.get("value"), (int, float)):
            total_cost_complete += 1
    return {"accepted_runs": total, "total_monetary_cost_complete_runs": total_cost_complete, "total_monetary_cost_coverage": _ratio(total_cost_complete, total), "controller_cost_observed_runs": controller_cost_observed, "controller_cost_coverage": _ratio(controller_cost_observed, total), "controller_token_any_observed_runs": controller_token_any, "controller_token_any_coverage": _ratio(controller_token_any, total), "provider_usage_observed_runs": provider_usage_observed, "provider_cost_complete_runs": provider_cost_complete, "missing_monetary_cost_is_zero": False, "car_available": bool(total and total_cost_complete == total), "policy": "monetary CAR requires complete accepted-result cost coverage; partial resource evidence remains descriptive"}


def _current_source_dre(ledger: OrchestrationLedger, runs: list[dict[str, Any]], *, source_head: str, source_worktree_clean: bool | None) -> dict[str, Any]:
    normalized_head = str(source_head or "").strip().lower()
    current = [run for run in runs if normalized_head and _first_base_head(ledger, str(run["run_id"])) == normalized_head]
    cause_events: Counter[str] = Counter({name: 0 for name in CURRENT_DRE_CAUSES})
    affected: dict[str, set[str]] = {name: set() for name in CURRENT_DRE_CAUSES}
    repaired_runs = 0
    for run in current:
        run_id = str(run["run_id"])
        economics = ledger.accepted_result_economics(run_id)
        if int((economics.get("repair") or {}).get("replan_count") or 0) > 0:
            repaired_runs += 1
        for event in ledger.list_events(run_id):
            if str(event.get("event_type") or "") != "failure_observed":
                continue
            payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
            cause = repair_cause_for_failure_class(str(payload.get("failure_class") or ""))
            if cause in CURRENT_DRE_CAUSES:
                cause_events[cause] += 1
                affected[cause].add(run_id)
    denominator = len(current)
    exact_current = source_worktree_clean is True
    decision_status = "insufficient_head_window_volume" if not denominator else ("observed_exact_current_source" if exact_current else "head_window_descriptive_current_worktree_not_clean")
    return {"source_head": normalized_head or None, "source_worktree_clean": source_worktree_clean, "exact_current_source_window": bool(exact_current and normalized_head), "window_basis": "accepted deterministic representative runs whose first wave base_head equals the supplied code-bearing HEAD", "accepted_runs": denominator, "repaired_runs": repaired_runs, "repaired_rate": _ratio(repaired_runs, denominator), "mechanisms": {cause: {"events": int(cause_events[cause]), "affected_accepted_runs": len(affected[cause]), "events_per_100_accepted": round(100 * cause_events[cause] / denominator, 6) if denominator else None, "affected_runs_per_100_accepted": round(100 * len(affected[cause]) / denominator, 6) if denominator else None} for cause in sorted(CURRENT_DRE_CAUSES)}, "decision_status": decision_status, "historical_counts_are_not_used_as_current_incidence": True, "no_effect_estimate_from_this_observational_window": True}


def accepted_result_economics_report(workspace: Path, ledger: OrchestrationLedger, *, source_head: str = "", source_worktree_clean: bool | None = None, limit: int = 5000, tail_n: int = 10) -> dict[str, Any]:
    root = workspace.resolve()
    runs = _accepted_runs(ledger, limit=limit)
    performance = _performance_state(root)
    run_metrics = performance.get("run_metrics") if isinstance(performance.get("run_metrics"), dict) else {}
    first_perf: list[dict[str, Any]] = []
    repaired_perf: list[dict[str, Any]] = []
    all_perf: list[dict[str, Any]] = []
    evaluations: list[dict[str, Any]] = []
    tail_by_workflow: dict[str, list[dict[str, Any]]] = {name: [] for name in sorted(FOCUS_WORKFLOWS)}
    for run in runs:
        run_id = str(run["run_id"])
        economics = ledger.accepted_result_economics(run_id)
        evaluation = ledger.accepted_result_evaluation(run_id)
        evaluations.append(evaluation)
        metric = run_metrics.get(run_id) if isinstance(run_metrics.get(run_id), dict) else None
        replans = int((economics.get("repair") or {}).get("replan_count") or 0)
        if metric is not None:
            all_perf.append(metric)
            (repaired_perf if replans else first_perf).append(metric)
        workflow = _workflow(run)
        ttar = economics.get("tta_ms")
        if workflow in tail_by_workflow and isinstance(ttar, int) and not isinstance(ttar, bool) and ttar >= 0:
            phase = economics.get("phase_timing") if isinstance(economics.get("phase_timing"), dict) else {}
            mcp = evaluation.get("mcp") if isinstance(evaluation.get("mcp"), dict) else {}
            tail_by_workflow[workflow].append({"run_id": run_id, "ttar_ms": int(ttar), "replan_count": replans, "first_pass_accepted": replans == 0, "phase_timing_complete": phase.get("complete") is True, "phase_by_state_ms": dict(phase.get("by_state_ms") or {}), "proof_duration_ms": mcp.get("proof_duration_ms"), "performance": {key: metric.get(key) if metric is not None else None for key in ("tool_calls", "errors", "local_execution_ms", "estimated_wait_ms", "response_bytes", "model_visible_bytes")}})
    bounded_tail_n = max(1, min(int(tail_n), 50))
    for workflow in tail_by_workflow:
        tail_by_workflow[workflow] = sorted(tail_by_workflow[workflow], key=lambda item: (-int(item["ttar_ms"]), str(item["run_id"])))[:bounded_tail_n]
    global_wait = performance.get("estimated_wait_ms") if isinstance(performance.get("estimated_wait_ms"), int) else None
    global_local = performance.get("local_execution_ms") if isinstance(performance.get("local_execution_ms"), int) else None
    return {"schema_version": 1, "north_star": "accepted_result_economic_loss_under_fixed_quality_security_authority_correctness_floors", "cohort": {"accepted_deterministic_representative_runs": len(runs), "performance_run_metrics_observed": len(all_perf), "performance_run_metrics_coverage": _ratio(len(all_perf), len(runs)), "performance_run_metrics_retention_is_bounded": True}, "resource_vector": {"all_accepted": _resource_distribution(all_perf), "first_pass": _resource_distribution(first_perf), "repaired": _resource_distribution(repaired_perf), "global_inter_tool_gap_context": {"estimated_wait_ms": global_wait, "local_execution_ms": global_local, "estimated_wait_to_local_execution_ratio": _ratio(global_wait, global_local), "scope": "performance trace lifetime, not accepted-run-only", "estimated_wait_is_proven_avoidable": False}, "monetary_and_token_coverage": _cost_coverage(evaluations), "missing_measurements_remain_unknown": True}, "proof_economics": ledger.proof_cache_opportunity_summary(), "current_source_dre": _current_source_dre(ledger, runs, source_head=source_head, source_worktree_clean=source_worktree_clean), "tail_forensics": {"top_n": bounded_tail_n, "by_workflow": tail_by_workflow, "interpretation": "ranked descriptive cohort; inspect dominant wait/proof/replan states before changing architecture"}, "decision_policy": {"historical_dre_counts_do_not_justify_new_hardening_without_current_incidence": True, "estimated_wait_is_not_assumed_avoidable": True, "proof_cache_low_hit_rate_does_not_by_itself_justify_new_cache_architecture": True, "partial_resource_vector_can_guide_measurement_but_not_monetary_car_claims": True, "p4_modeling_not_required": True, "automatic_routing_or_p5_activation": False}, "model_free": True, "content_free": True}
