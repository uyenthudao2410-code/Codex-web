from __future__ import annotations

import math
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any


MEASUREMENT = "accepted_result_operations_v1"
MISSING_POLICY = "unknown_not_zero"


def _parse_time(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _finite_nonnegative(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    measured = float(value)
    return measured if math.isfinite(measured) and measured >= 0 else None


def _nearest_rank(values: list[int], percentile: int) -> int | None:
    if not values:
        return None
    ordered = sorted(max(0, int(value)) for value in values)
    rank = max(1, min(len(ordered), math.ceil(len(ordered) * max(1, min(percentile, 100)) / 100)))
    return ordered[rank - 1]


def operations_analytics(
    ledger: Any,
    *,
    performance: dict[str, Any] | None = None,
    days: int = 7,
    now: str | None = None,
    row_limit: int = 50,
) -> dict[str, Any]:
    """Project terminal-run operations KPIs without turning missing evidence into zero."""
    bounded_days = max(1, min(int(days), 31))
    bounded_rows = max(1, min(int(row_limit), 200))
    end = _parse_time(now) if now else datetime.now(timezone.utc)
    if end is None:
        raise ValueError("operations analytics now must be ISO-8601 when supplied")
    start = end - timedelta(days=bounded_days)

    with ledger._lock, ledger._connect() as connection:
        rows = connection.execute(
            """SELECT run_id,status,started_at,finished_at
               FROM runs
               WHERE finished_at IS NOT NULL AND finished_at<>''
               ORDER BY finished_at DESC, run_id DESC"""
        ).fetchall()

    terminal: list[dict[str, Any]] = []
    for row in rows:
        finished = _parse_time(row["finished_at"])
        if finished is None or finished < start or finished > end:
            continue
        terminal.append({
            "run_id": str(row["run_id"]),
            "status": str(row["status"] or "unknown").strip().lower() or "unknown",
            "finished_at": str(row["finished_at"] or ""),
            "finished": finished,
        })

    run_metrics = performance.get("run_metrics") if isinstance(performance, dict) else {}
    if not isinstance(run_metrics, dict):
        run_metrics = {}

    accepted_count = 0
    first_pass_count = 0
    tta_values: list[int] = []
    phase_coverage_values: list[float] = []
    total_waves = 0
    total_replans = 0
    replanned_accepted = 0
    proof_records = 0
    tool_calls_total = 0
    tool_call_samples = 0
    provider_cost_total = 0.0
    provider_cost_samples = 0
    system_cost_total = 0.0
    system_cost_samples = 0
    status_counts: Counter[str] = Counter()
    result_rows: list[dict[str, Any]] = []

    bucket_count = bounded_days * 24
    current_hour = int(end.timestamp() // 3600)
    first_hour = current_hour - bucket_count + 1
    hourly = {hour: {"terminal": 0, "accepted": 0, "first_pass": 0} for hour in range(first_hour, current_hour + 1)}

    for item in terminal:
        run_id = item["run_id"]
        status = item["status"]
        status_counts[status] += 1
        hour_key = int(item["finished"].timestamp() // 3600)
        if hour_key in hourly:
            hourly[hour_key]["terminal"] += 1

        perf_metric = run_metrics.get(run_id)
        observed_tool_calls: int | None = None
        if isinstance(perf_metric, dict):
            raw_calls = perf_metric.get("tool_calls")
            if isinstance(raw_calls, int) and not isinstance(raw_calls, bool) and raw_calls >= 0:
                observed_tool_calls = raw_calls

        row_result: dict[str, Any] = {
            "run_id": run_id,
            "status": status,
            "finished_at": item["finished_at"],
            "accepted": status == "accepted",
            "tta_ms": None,
            "first_pass": None,
            "replan_count": None,
            "wave_count": None,
            "tool_calls": observed_tool_calls,
            "tool_calls_measurement": "performance_trace_run_metrics" if observed_tool_calls is not None else "unobserved",
            "provider_cost_usd": None,
            "provider_cost_measurement": "unobserved",
            "total_system_cost_usd": None,
            "total_system_cost_measurement": "unobserved",
        }

        if status == "accepted":
            accepted_count += 1
            if hour_key in hourly:
                hourly[hour_key]["accepted"] += 1
            economics = ledger.accepted_result_economics(run_id)
            evaluation = ledger.accepted_result_evaluation(run_id)

            first_pass = economics.get("first_pass_accepted") is True
            row_result["first_pass"] = first_pass
            if first_pass:
                first_pass_count += 1
                if hour_key in hourly:
                    hourly[hour_key]["first_pass"] += 1

            tta = economics.get("tta_ms")
            if isinstance(tta, (int, float)) and not isinstance(tta, bool) and tta >= 0:
                measured_tta = int(tta)
                tta_values.append(measured_tta)
                row_result["tta_ms"] = measured_tta

            phase = economics.get("phase_timing") if isinstance(economics.get("phase_timing"), dict) else {}
            phase_coverage = _finite_nonnegative(phase.get("tta_coverage"))
            if phase_coverage is not None:
                phase_coverage_values.append(min(1.0, phase_coverage))

            wave_count = len(ledger.list_waves(run_id))
            row_result["wave_count"] = wave_count
            total_waves += wave_count

            repair = economics.get("repair") if isinstance(economics.get("repair"), dict) else {}
            replan_count = int(repair.get("replan_count") or 0)
            row_result["replan_count"] = replan_count
            total_replans += replan_count
            if replan_count > 0:
                replanned_accepted += 1

            proof = economics.get("proof") if isinstance(economics.get("proof"), dict) else {}
            proof_records += max(0, int(proof.get("records") or 0))

            if observed_tool_calls is not None:
                tool_call_samples += 1
                tool_calls_total += observed_tool_calls

            provider = economics.get("provider_economics") if isinstance(economics.get("provider_economics"), dict) else {}
            provider_cost = _finite_nonnegative(provider.get("provider_cost"))
            if provider.get("cost_complete") is True and provider.get("attribution_complete") is True and provider_cost is not None:
                provider_cost_samples += 1
                provider_cost_total += provider_cost
                row_result["provider_cost_usd"] = round(provider_cost, 12)
                row_result["provider_cost_measurement"] = "measured_attributed_complete"

            total_cost = evaluation.get("total_monetary_cost") if isinstance(evaluation.get("total_monetary_cost"), dict) else {}
            total_cost_value = _finite_nonnegative(total_cost.get("value"))
            if total_cost.get("complete") is True and total_cost_value is not None:
                system_cost_samples += 1
                system_cost_total += total_cost_value
                row_result["total_system_cost_usd"] = round(total_cost_value, 12)
                row_result["total_system_cost_measurement"] = "controller_plus_provider_complete"

        if len(result_rows) < bounded_rows:
            result_rows.append(row_result)

    terminal_count = len(terminal)
    window_hours = bounded_days * 24
    tool_missing = max(0, accepted_count - tool_call_samples)
    provider_missing = max(0, accepted_count - provider_cost_samples)
    system_missing = max(0, accepted_count - system_cost_samples)
    hourly_rows = [{"hour": _iso(datetime.fromtimestamp(hour * 3600, tz=timezone.utc)), **hourly[hour]} for hour in range(first_hour, current_hour + 1)]

    phase_p50 = None
    if phase_coverage_values:
        ranked = _nearest_rank([round(value * 1_000_000) for value in phase_coverage_values], 50)
        phase_p50 = round((ranked or 0) / 1_000_000, 6)

    return {
        "schema_version": 1,
        "measurement": MEASUREMENT,
        "missing_measurement_policy": MISSING_POLICY,
        "window": {"start": _iso(start), "end": _iso(end), "days": bounded_days, "hours": window_hours, "basis": "terminal_run_finished_at_utc"},
        "outcomes": {
            "terminal_runs": terminal_count,
            "accepted": accepted_count,
            "nonaccepted_terminal": max(0, terminal_count - accepted_count),
            "by_status": dict(sorted(status_counts.items())),
            "acceptance_rate": round(accepted_count / terminal_count, 6) if terminal_count else None,
            "first_pass_accepted": first_pass_count,
            "first_pass_rate": round(first_pass_count / accepted_count, 6) if accepted_count else None,
        },
        "speed": {
            "tta_samples": len(tta_values),
            "tta_missing_accepted": max(0, accepted_count - len(tta_values)),
            "p50_ms": _nearest_rank(tta_values, 50),
            "p90_ms": _nearest_rank(tta_values, 90),
            "throughput_accepted_per_hour": round(accepted_count / window_hours, 6),
            "throughput_accepted_per_day": round(accepted_count / bounded_days, 6),
            "phase_coverage_samples": len(phase_coverage_values),
            "phase_coverage_p50": phase_p50,
            "measurement": "accepted_result_eocl_tta",
        },
        "efficiency": {
            "accepted_results": accepted_count,
            "wave_count_total": total_waves,
            "waves_per_accepted": round(total_waves / accepted_count, 6) if accepted_count else None,
            "replanned_accepted": replanned_accepted,
            "replan_rate": round(replanned_accepted / accepted_count, 6) if accepted_count else None,
            "replan_count_total": total_replans,
            "replans_per_accepted": round(total_replans / accepted_count, 6) if accepted_count else None,
            "proof_records_total": proof_records,
            "proof_records_per_accepted": round(proof_records / accepted_count, 6) if accepted_count else None,
            "tool_calls": {
                "observed_accepted": tool_call_samples,
                "missing_accepted": tool_missing,
                "coverage": round(tool_call_samples / accepted_count, 6) if accepted_count else None,
                "total_observed": tool_calls_total if tool_call_samples else None,
                "mean_per_observed_accepted": round(tool_calls_total / tool_call_samples, 6) if tool_call_samples else None,
                "measurement": "performance_trace_run_metrics",
                "missing_measurement_policy": MISSING_POLICY,
            },
        },
        "cost": {
            "provider_observed": {
                "complete_accepted": provider_cost_samples,
                "missing_accepted": provider_missing,
                "coverage": round(provider_cost_samples / accepted_count, 6) if accepted_count else None,
                "total_usd": round(provider_cost_total, 12) if provider_cost_samples else None,
                "mean_per_complete_accepted_usd": round(provider_cost_total / provider_cost_samples, 12) if provider_cost_samples else None,
                "measurement": "measured_attributed_complete_only",
                "missing_measurement_policy": MISSING_POLICY,
            },
            "total_system": {
                "complete_accepted": system_cost_samples,
                "missing_accepted": system_missing,
                "coverage": round(system_cost_samples / accepted_count, 6) if accepted_count else None,
                "total_usd": round(system_cost_total, 12) if system_cost_samples else None,
                "mean_per_complete_accepted_usd": round(system_cost_total / system_cost_samples, 12) if system_cost_samples else None,
                "measurement": "controller_plus_attributed_provider_complete_only",
                "missing_measurement_policy": MISSING_POLICY,
            },
        },
        "hourly": hourly_rows,
        "runs": result_rows,
        "sources": {"outcomes": "orchestration_ledger.runs", "accepted_result": "accepted_result_economics_and_evaluation", "tool_calls": "performance_trace.run_metrics"},
        "content_free": True,
    }
