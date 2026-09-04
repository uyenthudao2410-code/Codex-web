from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from .ledger_analysis import LedgerReadSession
from .orchestration_ledger import OrchestrationLedger
from .rework_diagnosis import repair_cause_for_failure_class
from .usage_ledger import CANONICAL_USAGE_KEYS, canonical_usage_payload

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
    candidate = getattr(ledger, "accepted_representative_runs", None)
    if callable(candidate):
        rows = candidate(limit=bounded_limit)
    else:
        with LedgerReadSession(ledger.path) as reader:
            rows = [{
                "run_id": row["run_id"], "task_id": row["task_id"], "objective": row["objective"],
                "status": row["status"], "started_at": row["started_at"], "finished_at": row["finished_at"],
                "metadata": json.loads(row["metadata_json"] or "{}"),
            } for row in reader.rows("SELECT * FROM runs WHERE status='accepted' ORDER BY started_at, run_id LIMIT ?", (bounded_limit,))]
    rows = sorted(rows, key=lambda item: (str(item.get("started_at") or ""), str(item.get("run_id") or "")))
    result: list[dict[str, Any]] = []
    for row in rows:
        metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
        evaluation = metadata.get("evaluation") if isinstance(metadata.get("evaluation"), dict) else {}
        provenance = str(evaluation.get("provenance") or "").lower()
        policy = str(evaluation.get("policy") or "").lower()
        run_id = str(row["run_id"])
        if provenance in {"", "representative"} and policy in {"", "chatweb_mcp"} and _is_deterministic_run(ledger, run_id):
            result.append(row)
            if len(result) >= bounded_limit:
                break
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


def _empty_usage_bucket() -> dict[str, Any]:
    return {
        "observed_events": 0,
        "exact_events": 0,
        "usage": {key: 0 for key in CANONICAL_USAGE_KEYS},
        "cost_observed_events": 0,
        "cost_usd": 0.0,
    }


def _finalize_usage_bucket(bucket: dict[str, Any]) -> dict[str, Any]:
    observed = int(bucket["observed_events"])
    exact = int(bucket["exact_events"])
    cost_events = int(bucket["cost_observed_events"])
    return {
        "observed_events": observed,
        "exact_events": exact,
        "exact_attribution_coverage": _ratio(exact, observed),
        "usage": dict(bucket["usage"]) if exact else None,
        "cost": {
            "value_usd": round(float(bucket["cost_usd"]), 12) if exact and cost_events == exact else None,
            "observed_events": cost_events,
            "complete_for_exact_usage": bool(exact and cost_events == exact),
        },
    }


def _tool_bucket(events: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "invocations": len(events),
        "errors": sum(1 for item in events if item.get("ok") is False),
        "duration_ms": sum(max(0, int(item.get("duration_ms") or 0)) for item in events),
        "request_bytes": sum(max(0, int(item.get("request_bytes") or 0)) for item in events),
        "response_bytes": sum(max(0, int(item.get("response_bytes") or 0)) for item in events),
        "model_visible_bytes": sum(max(0, int(item.get("model_visible_bytes") or 0)) for item in events),
    }


def _accepted_run_economics(ledger: OrchestrationLedger, run_id: str, performance: dict[str, Any]) -> dict[str, Any]:
    waves = ledger.list_waves(run_id)
    accepted_waves = [item for item in waves if str(item.get("status") or "").lower() == "accepted"]
    final_wave_id = str(accepted_waves[-1].get("wave_id") or "") if accepted_waves else ""
    rework_wave_ids = [str(item.get("wave_id") or "") for item in waves if str(item.get("wave_id") or "") != final_wave_id]
    raw_usage = ledger.list_usage_events(run_id, limit=None)
    buckets = {
        "final": {"controller": _empty_usage_bucket(), "provider": _empty_usage_bucket()},
        "rework": {"controller": _empty_usage_bucket(), "provider": _empty_usage_bucket()},
    }
    turn_ids: set[str] = set()
    trace_ids: set[str] = set()
    exact_total = 0
    for event in raw_usage:
        actor = str(event.get("actor") or "provider").strip().lower()
        if actor not in {"controller", "provider"}:
            continue
        wave_id = str(event.get("wave_id") or "")
        phase = "final" if final_wave_id and wave_id == final_wave_id else "rework"
        bucket = buckets[phase][actor]
        bucket["observed_events"] += 1
        turn_id = str(event.get("turn_id") or "").strip()
        trace_id = str(event.get("trace_id") or "").strip()
        if turn_id:
            turn_ids.add(turn_id[:128])
        if trace_id:
            trace_ids.add(trace_id[:128])
        attribution = event.get("attribution") if isinstance(event.get("attribution"), dict) else {}
        measurement = event.get("measurement") if isinstance(event.get("measurement"), dict) else {}
        if attribution.get("status") != "exact" or measurement.get("usage") != "measured":
            continue
        try:
            canonical = canonical_usage_payload(event)
        except ValueError:
            continue
        bucket["exact_events"] += 1
        exact_total += 1
        for key in CANONICAL_USAGE_KEYS:
            bucket["usage"][key] += max(0, int(canonical.get(key) or 0))
        cost = event.get("cost") if isinstance(event.get("cost"), dict) else {}
        cost_measurement = str(measurement.get("cost") or "").strip().lower()
        cost_value = cost.get("provider_cost") if cost_measurement == "measured" else cost.get("derived_cost_usd")
        if cost_measurement in {"measured", "derived"} and isinstance(cost_value, (int, float)) and not isinstance(cost_value, bool) and cost_value >= 0:
            bucket["cost_observed_events"] += 1
            bucket["cost_usd"] += float(cost_value)

    projected = {
        phase: {actor: _finalize_usage_bucket(value) for actor, value in actors.items()}
        for phase, actors in buckets.items()
    }
    actor_totals: dict[str, dict[str, Any]] = {}
    for actor in ("controller", "provider"):
        observed = sum(projected[phase][actor]["observed_events"] for phase in ("final", "rework"))
        exact = sum(projected[phase][actor]["exact_events"] for phase in ("final", "rework"))
        usage = None
        if exact:
            usage = {
                key: sum(int(projected[phase][actor]["usage"][key]) for phase in ("final", "rework") if projected[phase][actor]["usage"] is not None)
                for key in CANONICAL_USAGE_KEYS
            }
        cost_parts = [projected[phase][actor] for phase in ("final", "rework") if projected[phase][actor]["exact_events"]]
        cost_complete = bool(cost_parts and all(item["cost"]["complete_for_exact_usage"] for item in cost_parts))
        actor_totals[actor] = {
            "observed_events": observed,
            "exact_events": exact,
            "exact_attribution_coverage": _ratio(exact, observed),
            "usage": usage,
            "cost_usd": round(sum(float(item["cost"]["value_usd"]) for item in cost_parts), 12) if cost_complete else None,
            "cost_complete": cost_complete,
        }

    run_metrics = performance.get("run_metrics") if isinstance(performance.get("run_metrics"), dict) else {}
    metric = run_metrics.get(run_id) if isinstance(run_metrics.get(run_id), dict) else None
    expected_tool_calls = int(metric.get("tool_calls") or 0) if metric is not None else 0
    recent = performance.get("recent") if isinstance(performance.get("recent"), list) else []
    tool_events = [
        item for item in recent
        if isinstance(item, dict)
        and str(item.get("run_id") or "") == run_id
        and isinstance(item.get("invocation"), dict)
        and str(item["invocation"].get("invocation_id") or "").strip()
    ]
    tool_split_complete = bool(metric is not None and expected_tool_calls == len(tool_events))
    if tool_split_complete:
        final_tools = [item for item in tool_events if str(item.get("wave_id") or "") == final_wave_id]
        rework_tools = [item for item in tool_events if str(item.get("wave_id") or "") != final_wave_id]
        tool_split: dict[str, Any] = {"final": _tool_bucket(final_tools), "rework": _tool_bucket(rework_tools)}
        tool_split_reason = None
    else:
        tool_split = {"final": None, "rework": None}
        tool_split_reason = "bounded_recent_invocation_retention_does_not_cover_full_run"
    tool_identities = [item["invocation"] for item in tool_events]
    turn_ids.update(str(item.get("turn_id") or "")[:128] for item in tool_identities if str(item.get("turn_id") or "").strip())
    trace_ids.update(
        str(item["trace_context"].get("trace_id") or "")[:128]
        for item in tool_identities
        if isinstance(item.get("trace_context"), dict) and str(item["trace_context"].get("trace_id") or "").strip()
    )
    observed_usage = len(raw_usage)
    return {
        "run_id": run_id,
        "final_wave_id": final_wave_id or None,
        "rework_wave_ids": rework_wave_ids,
        "wave_count": len(waves),
        "usage": projected,
        "totals_by_actor": actor_totals,
        "tool_context": {
            "measurement": "runtime_measured" if metric is not None else "unobserved",
            "run_metrics": {key: metric.get(key) for key in ("tool_calls", "errors", "local_execution_ms", "request_bytes", "response_bytes", "model_visible_bytes")} if metric is not None else None,
            "retained_invocations": len(tool_events),
            "final_rework_split": tool_split,
            "split_complete": tool_split_complete,
            "split_reason": tool_split_reason,
            "exact_tool_card_tokens": None,
            "tool_card_measurement": "unobserved",
        },
        "correlation": {
            "turn_ids": sorted(turn_ids)[:32],
            "trace_ids": sorted(trace_ids)[:32],
            "usage_event_count": observed_usage,
            "exact_usage_event_count": exact_total,
            "tool_invocation_ids_retained": [str(item.get("invocation_id") or "") for item in tool_identities[:32]],
        },
        "coverage": {
            "controller_usage": actor_totals["controller"]["exact_attribution_coverage"],
            "provider_usage": actor_totals["provider"]["exact_attribution_coverage"],
            "tool_invocation": _ratio(len(tool_events), expected_tool_calls) if expected_tool_calls else None,
            "tool_card_tokens": None,
            "exact_run_attribution": _ratio(exact_total, observed_usage),
            "missing_measurement_policy": "unknown_not_zero",
        },
        "system_totals": {
            "tokens": None,
            "cost_usd": None,
            "complete": False,
            "reason": "cross_plane_overlap_not_proven",
        },
    }


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


def _cost_evaluation(run_projection: dict[str, Any], economics: dict[str, Any]) -> dict[str, Any]:
    """Project only fields consumed by this aggregate; avoid a duplicate full evaluation."""
    controller = run_projection["totals_by_actor"]["controller"]
    controller_cost_value = controller.get("cost_usd")
    controller_usage = controller.get("usage") if isinstance(controller.get("usage"), dict) else None
    provider = economics.get("provider_economics") if isinstance(economics.get("provider_economics"), dict) else {}
    provider_cost = provider.get("provider_cost")
    provider_usage_count = int(provider.get("usage_event_count") or 0)
    provider_cost_value = float(provider_cost) if provider.get("cost_complete") is True and provider.get("attribution_complete") is True and isinstance(provider_cost, (int, float)) else None
    controller_usage_count = int(controller.get("observed_events") or 0)
    if controller_usage_count and provider_usage_count:
        complete = False
        total_value = None
        reason = "cross_plane_cost_overlap_not_proven"
    elif controller_usage_count:
        complete = controller_cost_value is not None
        total_value = controller_cost_value if complete else None
        reason = None if complete else "controller_cost_unobserved"
    elif provider_usage_count:
        complete = provider_cost_value is not None
        total_value = provider_cost_value if complete else None
        if provider.get("attribution_complete") is not True:
            reason = "provider_cost_attribution_incomplete"
        elif provider.get("cost_complete") is not True:
            reason = "provider_cost_measurement_incomplete"
        else:
            reason = None
    else:
        complete = False
        total_value = None
        reason = "controller_cost_unobserved"
    return {"controller": {"monetary_cost": controller_cost_value, "usage": controller_usage}, "external": {"provider_economics": provider}, "total_monetary_cost": {"value": total_value, "complete": complete, "reason": reason}}


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
    run_economics: list[dict[str, Any]] = []
    tail_by_workflow: dict[str, list[dict[str, Any]]] = {name: [] for name in sorted(FOCUS_WORKFLOWS)}
    for run in runs:
        run_id = str(run["run_id"])
        economics = ledger.accepted_result_economics(run_id)
        projected_economics = _accepted_run_economics(ledger, run_id, performance)
        run_economics.append(projected_economics)
        evaluations.append(_cost_evaluation(projected_economics, economics))
        metric = run_metrics.get(run_id) if isinstance(run_metrics.get(run_id), dict) else None
        replans = int((economics.get("repair") or {}).get("replan_count") or 0)
        if metric is not None:
            all_perf.append(metric)
            (repaired_perf if replans else first_perf).append(metric)
        workflow = _workflow(run)
        ttar = economics.get("tta_ms")
        if workflow in tail_by_workflow and isinstance(ttar, int) and not isinstance(ttar, bool) and ttar >= 0:
            phase = economics.get("phase_timing") if isinstance(economics.get("phase_timing"), dict) else {}
            proof_duration_ms = sum(max(0, int(item.get("duration_ms") or 0)) for item in ledger.list_proofs(run_id))
            tail_by_workflow[workflow].append({"run_id": run_id, "ttar_ms": int(ttar), "replan_count": replans, "first_pass_accepted": replans == 0, "phase_timing_complete": phase.get("complete") is True, "phase_by_state_ms": dict(phase.get("by_state_ms") or {}), "proof_duration_ms": proof_duration_ms, "performance": {key: metric.get(key) if metric is not None else None for key in ("tool_calls", "errors", "local_execution_ms", "estimated_wait_ms", "response_bytes", "model_visible_bytes")}})
    bounded_tail_n = max(1, min(int(tail_n), 50))
    for workflow in tail_by_workflow:
        tail_by_workflow[workflow] = sorted(tail_by_workflow[workflow], key=lambda item: (-int(item["ttar_ms"]), str(item["run_id"])))[:bounded_tail_n]
    global_wait = performance.get("estimated_wait_ms") if isinstance(performance.get("estimated_wait_ms"), int) else None
    global_local = performance.get("local_execution_ms") if isinstance(performance.get("local_execution_ms"), int) else None
    return {"schema_version": 1, "north_star": "accepted_result_economic_loss_under_fixed_quality_security_authority_correctness_floors", "cohort": {"accepted_deterministic_representative_runs": len(runs), "performance_run_metrics_observed": len(all_perf), "performance_run_metrics_coverage": _ratio(len(all_perf), len(runs)), "performance_run_metrics_retention_is_bounded": True}, "resource_vector": {"all_accepted": _resource_distribution(all_perf), "first_pass": _resource_distribution(first_perf), "repaired": _resource_distribution(repaired_perf), "global_inter_tool_gap_context": {"estimated_wait_ms": global_wait, "local_execution_ms": global_local, "estimated_wait_to_local_execution_ratio": _ratio(global_wait, global_local), "scope": "performance trace lifetime, not accepted-run-only", "estimated_wait_is_proven_avoidable": False}, "monetary_and_token_coverage": _cost_coverage(evaluations), "missing_measurements_remain_unknown": True}, "accepted_result_economics": {"runs": run_economics[-50:], "runs_truncated": len(run_economics) > 50, "missing_measurement_policy": "unknown_not_zero", "system_plane_composition": "separate_until_non_overlap_is_proven"}, "proof_economics": ledger.proof_cache_opportunity_summary(), "current_source_dre": _current_source_dre(ledger, runs, source_head=source_head, source_worktree_clean=source_worktree_clean), "tail_forensics": {"top_n": bounded_tail_n, "by_workflow": tail_by_workflow, "interpretation": "ranked descriptive cohort; inspect dominant wait/proof/replan states before changing architecture"}, "decision_policy": {"historical_dre_counts_do_not_justify_new_hardening_without_current_incidence": True, "estimated_wait_is_not_assumed_avoidable": True, "proof_cache_low_hit_rate_does_not_by_itself_justify_new_cache_architecture": True, "partial_resource_vector_can_guide_measurement_but_not_monetary_car_claims": True, "p4_modeling_not_required": True, "automatic_routing_or_p5_activation": False}, "model_free": True, "content_free": True}
