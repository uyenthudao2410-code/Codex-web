from __future__ import annotations

import json
import math
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any

from .usage_ledger import canonical_usage_payload
from .token_measurements import summarize_workspace as summarize_chat_turn_measurements


MEASUREMENT = "accepted_result_operations_v1"
MISSING_POLICY = "unknown_not_zero"
CONTROLLER_CALIBRATION_MIN_SAMPLES = 5
CONTEXT_ESTIMATE_BYTES_PER_TOKEN_P10 = 6.0
CONTEXT_ESTIMATE_BYTES_PER_TOKEN_P50 = 4.0
CONTEXT_ESTIMATE_BYTES_PER_TOKEN_P90 = 2.0


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


def _nearest_rank_float(values: list[float], percentile: int) -> float | None:
    if not values:
        return None
    ordered = sorted(max(0.0, float(value)) for value in values if math.isfinite(float(value)))
    if not ordered:
        return None
    rank = max(1, min(len(ordered), math.ceil(len(ordered) * max(1, min(percentile, 100)) / 100)))
    return ordered[rank - 1]


def _observed_nonnegative_int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    measured = float(value)
    if not math.isfinite(measured) or measured < 0:
        return None
    return int(measured)


def _controller_token_estimate(
    *,
    accepted_runs: int,
    exact_runs: int,
    missing_exact_runs: int,
    eligible_missing_runs: int,
    missing_model_visible_bytes: int,
    calibration_ratios: list[float],
) -> dict[str, Any]:
    base = {
        "scope": "accepted_runs_finished_in_window_missing_exact_controller_only",
        "accepted_runs": accepted_runs,
        "exact_runs": exact_runs,
        "missing_exact_runs": missing_exact_runs,
        "eligible_missing_runs": eligible_missing_runs,
        "calibration_samples": len(calibration_ratios),
        "calibration_min_samples": CONTROLLER_CALIBRATION_MIN_SAMPLES,
        "missing_measurement_policy": MISSING_POLICY,
        "content_free": True,
    }
    if accepted_runs <= 0:
        return {
            **base,
            "status": "unknown",
            "measurement": "UNKNOWN",
            "confidence": "unknown",
            "method": None,
            "estimate": None,
            "missing_reason": "no_accepted_runs_in_window",
        }
    if missing_exact_runs <= 0:
        return {
            **base,
            "status": "exact",
            "measurement": "EXACT",
            "confidence": "exact",
            "method": "exact_controller_usage_event",
            "estimate": None,
            "missing_reason": None,
        }
    if eligible_missing_runs <= 0 or missing_model_visible_bytes <= 0:
        return {
            **base,
            "status": "unknown",
            "measurement": "UNKNOWN",
            "confidence": "unknown",
            "method": None,
            "estimate": None,
            "missing_reason": "model_visible_bytes_unobserved_for_missing_controller_runs",
        }

    if len(calibration_ratios) >= CONTROLLER_CALIBRATION_MIN_SAMPLES:
        p10_ratio = _nearest_rank_float(calibration_ratios, 10)
        p50_ratio = _nearest_rank_float(calibration_ratios, 50)
        p90_ratio = _nearest_rank_float(calibration_ratios, 90)
        if p10_ratio is not None and p50_ratio is not None and p90_ratio is not None:
            confidence = "high" if len(calibration_ratios) >= 30 else "medium" if len(calibration_ratios) >= 12 else "low"
            return {
                **base,
                "status": "calibrated_estimate",
                "measurement": "CALIBRATED_ESTIMATE",
                "confidence": confidence,
                "method": "exact_controller_tokens_per_model_visible_byte_v1",
                "estimate": {
                    "p10_total_tokens": max(0, round(missing_model_visible_bytes * p10_ratio)),
                    "p50_total_tokens": max(0, round(missing_model_visible_bytes * p50_ratio)),
                    "p90_total_tokens": max(0, round(missing_model_visible_bytes * p90_ratio)),
                },
                "provenance": "exact_controller_usage_event+performance_trace.run_metrics.model_visible_bytes",
                "missing_reason": None,
            }

    return {
        **base,
        "status": "context_estimate",
        "measurement": "CONTEXT_ESTIMATE",
        "confidence": "low",
        "method": "model_visible_bytes_context_prior_v1",
        "estimate": {
            "p10_context_tokens": max(0, round(missing_model_visible_bytes / CONTEXT_ESTIMATE_BYTES_PER_TOKEN_P10)),
            "p50_context_tokens": max(0, round(missing_model_visible_bytes / CONTEXT_ESTIMATE_BYTES_PER_TOKEN_P50)),
            "p90_context_tokens": max(0, round(missing_model_visible_bytes / CONTEXT_ESTIMATE_BYTES_PER_TOKEN_P90)),
            "not_controller_total": True,
        },
        "prior": {
            "p10_bytes_per_token": CONTEXT_ESTIMATE_BYTES_PER_TOKEN_P10,
            "p50_bytes_per_token": CONTEXT_ESTIMATE_BYTES_PER_TOKEN_P50,
            "p90_bytes_per_token": CONTEXT_ESTIMATE_BYTES_PER_TOKEN_P90,
        },
        "provenance": "performance_trace.run_metrics.model_visible_bytes; explicit context estimate only",
        "missing_reason": "exact_calibration_below_minimum",
    }


def _tool_call_token_measurements(
    *,
    performance: dict[str, Any] | None,
    start: datetime,
    end: datetime,
    calibration_ratios: list[float],
) -> dict[str, Any]:
    """Estimate tokens over every tool call in the window, not just accepted runs.

    Casual ChatWeb turns never create EOCL runs, so the accepted-runs estimate
    stays unknown for them even though every call's model-visible bytes pass
    through this runtime (the one choke point we own, OpenRouter-style). This
    projection aggregates the persisted performance-trace hourly buckets
    instead, using the same calibrated-or-prior ladder and the same honesty
    labels. Context bytes are not controller/model totals.
    """
    base = {
        "scope": "all_tool_calls_in_window",
        "window": {"start": _iso(start), "end": _iso(end), "basis": "performance_trace_hourly_utc"},
        "calibration_samples": len(calibration_ratios),
        "calibration_min_samples": CONTROLLER_CALIBRATION_MIN_SAMPLES,
        "missing_measurement_policy": MISSING_POLICY,
        "content_free": True,
    }
    buckets = (performance or {}).get("hourly_metrics") if isinstance(performance, dict) else {}
    calls = 0
    visible_bytes = 0
    visible_chars = 0
    if isinstance(buckets, dict):
        try:
            start_hour = int(start.timestamp() // 3600)
            end_hour = int(end.timestamp() // 3600)
        except (OverflowError, OSError, ValueError):
            start_hour = end_hour = None
        if start_hour is not None:
            for raw_hour, bucket in buckets.items():
                try:
                    hour = int(raw_hour)
                except (TypeError, ValueError):
                    continue
                if hour < start_hour or hour > end_hour:
                    continue
                if not isinstance(bucket, dict):
                    continue
                try:
                    calls += max(0, int(bucket.get("tool_calls") or 0))
                    visible_bytes += max(0, int(bucket.get("model_visible_bytes") or 0))
                    visible_chars += max(0, int(bucket.get("model_visible_chars") or 0))
                except (TypeError, ValueError):
                    continue
    base.update({
        "tool_calls": calls or None,
        "model_visible_bytes": visible_bytes or None,
        "model_visible_chars": visible_chars or None,
    })
    if calls <= 0 or visible_bytes <= 0:
        return {
            **base,
            "status": "unknown",
            "measurement": "UNKNOWN",
            "confidence": "unknown",
            "method": None,
            "estimate": None,
            "missing_reason": "no_tool_call_bytes_in_window",
        }
    if len(calibration_ratios) >= CONTROLLER_CALIBRATION_MIN_SAMPLES:
        p10_ratio = _nearest_rank_float(calibration_ratios, 10)
        p50_ratio = _nearest_rank_float(calibration_ratios, 50)
        p90_ratio = _nearest_rank_float(calibration_ratios, 90)
        if p10_ratio is not None and p50_ratio is not None and p90_ratio is not None:
            confidence = "high" if len(calibration_ratios) >= 30 else "medium" if len(calibration_ratios) >= 12 else "low"
            return {
                **base,
                "status": "calibrated_estimate",
                "measurement": "CALIBRATED_ESTIMATE",
                "confidence": confidence,
                "method": "exact_controller_tokens_per_model_visible_byte_v1",
                "estimate": {
                    "p10_total_tokens": max(0, round(visible_bytes * p10_ratio)),
                    "p50_total_tokens": max(0, round(visible_bytes * p50_ratio)),
                    "p90_total_tokens": max(0, round(visible_bytes * p90_ratio)),
                },
                "provenance": "exact_controller_usage_event+performance_trace.hourly_metrics.model_visible_bytes",
                "missing_reason": None,
            }
    return {
        **base,
        "status": "context_estimate",
        "measurement": "CONTEXT_ESTIMATE",
        "confidence": "low",
        "method": "model_visible_bytes_context_prior_v1",
        "estimate": {
            "p10_context_tokens": max(0, round(visible_bytes / CONTEXT_ESTIMATE_BYTES_PER_TOKEN_P10)),
            "p50_context_tokens": max(0, round(visible_bytes / CONTEXT_ESTIMATE_BYTES_PER_TOKEN_P50)),
            "p90_context_tokens": max(0, round(visible_bytes / CONTEXT_ESTIMATE_BYTES_PER_TOKEN_P90)),
            "not_controller_total": True,
        },
        "prior": {
            "p10_bytes_per_token": CONTEXT_ESTIMATE_BYTES_PER_TOKEN_P10,
            "p50_bytes_per_token": CONTEXT_ESTIMATE_BYTES_PER_TOKEN_P50,
            "p90_bytes_per_token": CONTEXT_ESTIMATE_BYTES_PER_TOKEN_P90,
        },
        "provenance": "performance_trace.hourly_metrics.model_visible_bytes; explicit context estimate only",
        "missing_reason": "exact_calibration_below_minimum",
    }


def _chat_turn_measurements(ledger: Any) -> dict[str, Any]:
    """Session per-turn token summary from the Electron host journal.

    The orchestration ledger only holds EOCL-bound exact usage; casual
    ChatWeb turns live in the host observation journal instead. This
    projection is best-effort and fail-closed: any unreadable journal
    yields journal_available False with null totals (unknown, never zero)
    and never breaks the analytics payload.
    """
    try:
        workspace = getattr(ledger, "workspace", None)
        if workspace is None:
            raise ValueError("ledger workspace unavailable")
        return summarize_chat_turn_measurements(workspace)
    except Exception:
        return {
            "schema_version": 1,
            "measurement": "chat_turn_measurements_v1",
            "missing_measurement_policy": MISSING_POLICY,
            "method": "structural-chars-v1",
            "content_free": True,
            "journal_available": False,
            "turns_total": 0,
            "turns_exact": 0,
            "turns_estimated": 0,
            "turns_unknown": 0,
            "session_total": {"point": None, "lower": None, "upper": None},
            "latest_turn": None,
            "blend": "unknown",
            "missing_reason": "chat_journal_unavailable",
        }


def _json_object(value: Any) -> dict[str, Any]:
    try:
        parsed = json.loads(str(value or "{}"))
    except (TypeError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _phase_metrics(run: dict[str, Any], events: list[dict[str, Any]]) -> tuple[int | None, float | None]:
    started = _parse_time(run.get("started_at"))
    finished = _parse_time(run.get("finished_at"))
    if started is None or finished is None or finished < started:
        return None, None
    tta_ms = max(0, int((finished - started).total_seconds() * 1000))
    points: list[tuple[str, datetime]] = []
    for event in events:
        state = str(event.get("state_after") or "").strip()
        at = _parse_time(event.get("event_time"))
        if not state or at is None:
            continue
        if points and points[-1][0] == state:
            continue
        points.append((state, at))
    observed_ms = 0
    for index, (_state, at) in enumerate(points):
        end_at = points[index + 1][1] if index + 1 < len(points) else finished
        observed_ms += max(0, int((end_at - at).total_seconds() * 1000))
    coverage = round(min(1.0, observed_ms / tta_ms), 6) if tta_ms > 0 else None
    return tta_ms, coverage


def _window_evidence(ledger: Any, start: datetime, end: datetime) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    """Read a terminal result window with a fixed number of SQL statements."""
    start_iso = _iso(start)
    end_iso = _iso(end)
    with ledger._lock, ledger._connect() as connection:
        run_rows = connection.execute(
            """SELECT run_id,status,started_at,finished_at,metadata_json
               FROM runs
               WHERE finished_at IS NOT NULL AND finished_at<>''
                 AND julianday(finished_at) >= julianday(?)
                 AND julianday(finished_at) <= julianday(?)
               ORDER BY finished_at DESC, run_id DESC""",
            (start_iso, end_iso),
        ).fetchall()
        wave_rows = connection.execute(
            """SELECT w.run_id,COUNT(*) AS wave_count,
                      SUM(CASE WHEN lower(w.status)='replanned' THEN 1 ELSE 0 END) AS replan_count
               FROM waves w JOIN runs r ON r.run_id=w.run_id
               WHERE lower(r.status)='accepted'
                 AND julianday(r.finished_at) >= julianday(?)
                 AND julianday(r.finished_at) <= julianday(?)
               GROUP BY w.run_id""",
            (start_iso, end_iso),
        ).fetchall()
        proof_rows = connection.execute(
            """SELECT p.run_id,COUNT(*) AS proof_count
               FROM proofs p JOIN runs r ON r.run_id=p.run_id
               WHERE lower(r.status)='accepted'
                 AND julianday(r.finished_at) >= julianday(?)
                 AND julianday(r.finished_at) <= julianday(?)
               GROUP BY p.run_id""",
            (start_iso, end_iso),
        ).fetchall()
        event_rows = connection.execute(
            """SELECT e.run_id,e.seq,e.event_type,e.state_after,e.event_time,e.payload_json
               FROM events e JOIN runs r ON r.run_id=e.run_id
               WHERE lower(r.status)='accepted'
                 AND julianday(r.finished_at) >= julianday(?)
                 AND julianday(r.finished_at) <= julianday(?)
               ORDER BY e.run_id,e.seq""",
            (start_iso, end_iso),
        ).fetchall()

    terminal = [{
        "run_id": str(row["run_id"]),
        "status": str(row["status"] or "unknown").strip().lower() or "unknown",
        "started_at": str(row["started_at"] or ""),
        "finished_at": str(row["finished_at"] or ""),
        "finished": _parse_time(row["finished_at"]),
        "metadata": _json_object(row["metadata_json"]),
    } for row in run_rows]
    metrics: dict[str, dict[str, Any]] = {}
    for row in wave_rows:
        metrics.setdefault(str(row["run_id"]), {}).update({
            "wave_count": max(0, int(row["wave_count"] or 0)),
            "replan_count": max(0, int(row["replan_count"] or 0)),
        })
    for row in proof_rows:
        metrics.setdefault(str(row["run_id"]), {})["proof_count"] = max(0, int(row["proof_count"] or 0))
    for row in event_rows:
        metrics.setdefault(str(row["run_id"]), {}).setdefault("events", []).append({
            "seq": int(row["seq"] or 0),
            "event_type": str(row["event_type"] or ""),
            "state_after": str(row["state_after"] or ""),
            "event_time": str(row["event_time"] or ""),
            "payload": _json_object(row["payload_json"]),
        })
    return terminal, metrics


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

    terminal, window_metrics = _window_evidence(ledger, start, end)
    terminal = [item for item in terminal if item.get("finished") is not None]

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
    accepted_run_ids: set[str] = set()
    controller_usage_observed = 0
    controller_usage_exact = 0
    controller_exact_runs = 0
    controller_missing_exact_runs = 0
    controller_estimate_eligible_missing_runs = 0
    controller_missing_model_visible_bytes = 0
    controller_calibration_ratios: list[float] = []
    provider_usage_observed = 0
    provider_usage_exact = 0
    usage_observed = 0
    usage_exact = 0
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
            accepted_run_ids.add(run_id)
            if hour_key in hourly:
                hourly[hour_key]["accepted"] += 1
            evidence = window_metrics.get(run_id) or {}
            events = evidence.get("events") if isinstance(evidence.get("events"), list) else []
            all_usage_events = [
                event.get("payload") or {}
                for event in events
                if event.get("event_type") == "usage_event"
                and isinstance(event.get("payload"), dict)
            ]
            exact_controller_events = 0
            exact_controller_tokens = 0
            invalid_controller_exact_event = False
            for usage_event in all_usage_events:
                actor = str(usage_event.get("actor") or "provider").strip().lower()
                measurement = usage_event.get("measurement") if isinstance(usage_event.get("measurement"), dict) else {}
                attribution = usage_event.get("attribution") if isinstance(usage_event.get("attribution"), dict) else {}
                exact = str(attribution.get("status") or "").strip().lower() == "exact" and str(measurement.get("usage") or "").strip().lower() == "measured"
                controller_tokens = 0
                if actor == "controller" and exact:
                    try:
                        controller_tokens = canonical_usage_payload(usage_event)["total_tokens"]
                    except ValueError:
                        # Retain observed coverage, but never calibrate a
                        # run from a partial exact controller token sum.
                        invalid_controller_exact_event = True
                        exact = False
                usage_observed += 1
                usage_exact += int(exact)
                if actor == "controller":
                    controller_usage_observed += 1
                    controller_usage_exact += int(exact)
                    if exact:
                        exact_controller_events += 1
                        exact_controller_tokens += max(0, int(controller_tokens))
                else:
                    provider_usage_observed += 1
                    provider_usage_exact += int(exact)
            model_visible_bytes = _observed_nonnegative_int(perf_metric.get("model_visible_bytes")) if isinstance(perf_metric, dict) else None
            if exact_controller_events > 0 and not invalid_controller_exact_event:
                controller_exact_runs += 1
                if exact_controller_tokens > 0 and model_visible_bytes is not None and model_visible_bytes > 0:
                    controller_calibration_ratios.append(exact_controller_tokens / model_visible_bytes)
            else:
                controller_missing_exact_runs += 1
                if model_visible_bytes is not None and model_visible_bytes > 0:
                    controller_estimate_eligible_missing_runs += 1
                    controller_missing_model_visible_bytes += model_visible_bytes
            replan_count = max(0, int(evidence.get("replan_count") or 0))
            first_pass = replan_count == 0
            row_result["first_pass"] = first_pass
            if first_pass:
                first_pass_count += 1
                if hour_key in hourly:
                    hourly[hour_key]["first_pass"] += 1

            measured_tta, phase_coverage = _phase_metrics(item, events)
            if measured_tta is not None:
                tta_values.append(measured_tta)
                row_result["tta_ms"] = measured_tta
            if phase_coverage is not None:
                phase_coverage_values.append(min(1.0, phase_coverage))

            wave_count = max(0, int(evidence.get("wave_count") or 0))
            row_result["wave_count"] = wave_count
            total_waves += wave_count

            row_result["replan_count"] = replan_count
            total_replans += replan_count
            if replan_count > 0:
                replanned_accepted += 1

            proof_records += max(0, int(evidence.get("proof_count") or 0))

            if observed_tool_calls is not None:
                tool_call_samples += 1
                tool_calls_total += observed_tool_calls

            usage_events = [usage_event for usage_event in all_usage_events if str(usage_event.get("actor") or "provider").strip().lower() != "controller"]
            measured_costs: list[float] = []
            attribution_complete = bool(usage_events)
            for usage_event in usage_events:
                measurement = usage_event.get("measurement") if isinstance(usage_event.get("measurement"), dict) else {}
                cost_payload = usage_event.get("cost") if isinstance(usage_event.get("cost"), dict) else {}
                measured = _finite_nonnegative(cost_payload.get("provider_cost"))
                if measurement.get("cost") == "measured" and measured is not None:
                    measured_costs.append(measured)
                provenance = usage_event.get("provenance") if isinstance(usage_event.get("provenance"), dict) else {}
                if str(provenance.get("source") or "").strip() != "opencode:provider_dispatch":
                    attribution_complete = False
            cost_complete = bool(usage_events) and len(measured_costs) == len(usage_events)
            provider_cost = round(sum(measured_costs), 12) if cost_complete else None
            if cost_complete and attribution_complete and provider_cost is not None:
                provider_cost_samples += 1
                provider_cost_total += provider_cost
                row_result["provider_cost_usd"] = round(provider_cost, 12)
                row_result["provider_cost_measurement"] = "measured_attributed_complete"

            metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
            evaluation = metadata.get("evaluation") if isinstance(metadata.get("evaluation"), dict) else {}
            controller = evaluation.get("controller") if isinstance(evaluation.get("controller"), dict) else {}
            controller_cost = _finite_nonnegative(controller.get("monetary_cost"))
            provider_cost_value = provider_cost if cost_complete and attribution_complete else None
            total_cost_value = (
                round(controller_cost + (provider_cost_value or 0.0), 12)
                if controller_cost is not None and (provider_cost_value is not None or not usage_events)
                else None
            )
            if total_cost_value is not None:
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
    recent = performance.get("recent") if isinstance(performance, dict) else []
    if not isinstance(recent, list):
        recent = []
    retained_invocation_ids: set[str] = set()
    for event in recent:
        if not isinstance(event, dict) or str(event.get("run_id") or "") not in accepted_run_ids:
            continue
        invocation = event.get("invocation") if isinstance(event.get("invocation"), dict) else {}
        invocation_id = str(invocation.get("invocation_id") or "").strip()
        if invocation_id:
            retained_invocation_ids.add(invocation_id)
    expected_tool_invocations = tool_calls_total if tool_call_samples and tool_calls_total > 0 else None
    retained_tool_invocations = len(retained_invocation_ids) if expected_tool_invocations is not None else None
    tool_invocation_coverage = (
        round(min(retained_tool_invocations, expected_tool_invocations) / expected_tool_invocations, 6)
        if retained_tool_invocations is not None and expected_tool_invocations
        else None
    )
    controller_coverage = round(controller_usage_exact / controller_usage_observed, 6) if controller_usage_observed else None
    provider_coverage = round(provider_usage_exact / provider_usage_observed, 6) if provider_usage_observed else None
    exact_run_attribution = round(usage_exact / usage_observed, 6) if usage_observed else None
    cost_coverage = round(system_cost_samples / accepted_count, 6) if accepted_count else None
    hourly_rows = [{"hour": _iso(datetime.fromtimestamp(hour * 3600, tz=timezone.utc)), **hourly[hour]} for hour in range(first_hour, current_hour + 1)]

    phase_p50 = None
    if phase_coverage_values:
        ranked = _nearest_rank([round(value * 1_000_000) for value in phase_coverage_values], 50)
        phase_p50 = round((ranked or 0) / 1_000_000, 6)

    controller_token_estimate = _controller_token_estimate(
        accepted_runs=accepted_count,
        exact_runs=controller_exact_runs,
        missing_exact_runs=controller_missing_exact_runs,
        eligible_missing_runs=controller_estimate_eligible_missing_runs,
        missing_model_visible_bytes=controller_missing_model_visible_bytes,
        calibration_ratios=controller_calibration_ratios,
    )

    tool_call_token_measurements = _tool_call_token_measurements(
        performance=performance if isinstance(performance, dict) else None,
        start=start,
        end=end,
        calibration_ratios=controller_calibration_ratios,
    )

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
        "controller_token_estimate": controller_token_estimate,
        "tool_call_token_measurements": tool_call_token_measurements,
        "turn_token_measurements": _chat_turn_measurements(ledger),
        "measurement_coverage": {
            "missing_measurement_policy": MISSING_POLICY,
            "controller_usage": {
                "observed": controller_usage_observed,
                "exact": controller_usage_exact,
                "coverage": controller_coverage,
                "measurement": "exact_usage_event_attribution",
                "provenance": "orchestration_ledger.usage_event",
                "missing_reason": None if controller_usage_observed else "no_controller_usage_event_in_window",
            },
            "provider_usage": {
                "observed": provider_usage_observed,
                "exact": provider_usage_exact,
                "coverage": provider_coverage,
                "measurement": "exact_usage_event_attribution",
                "provenance": "orchestration_ledger.usage_event",
                "missing_reason": None if provider_usage_observed else "no_provider_usage_event_in_window",
            },
            "tool_invocation": {
                "observed": retained_tool_invocations,
                "expected": expected_tool_invocations,
                "coverage": tool_invocation_coverage,
                "measurement": "retained_tool_invocation_event_over_expected_tool_calls",
                "provenance": "performance_trace.recent+run_metrics",
                "missing_reason": None if expected_tool_invocations is not None else "expected_tool_call_denominator_unobserved",
            },
            "tool_card_tokens": {
                "coverage": None,
                "measurement": "unobserved",
                "provenance": "client_receipt_required",
                "missing_reason": "client_receipt_not_exposed_by_mcp_transport",
            },
            "cost": {
                "observed": system_cost_samples,
                "expected": accepted_count if accepted_count else None,
                "coverage": cost_coverage,
                "measurement": "controller_plus_attributed_provider_complete_only",
                "provenance": "accepted_result_operations.cost.total_system",
                "missing_reason": None if accepted_count and system_cost_samples == accepted_count else "accepted_result_cost_incomplete_or_unobserved",
            },
            "exact_run_attribution": {
                "observed": usage_observed,
                "exact": usage_exact,
                "coverage": exact_run_attribution,
                "measurement": "exact_usage_event_attribution",
                "provenance": "orchestration_ledger.usage_event.attribution",
                "missing_reason": None if usage_observed else "no_usage_event_in_window",
            },
        },
        "hourly": hourly_rows,
        "runs": result_rows,
        "sources": {"outcomes": "orchestration_ledger.runs_window", "accepted_result": "orchestration_ledger.fixed_window_batch_v1", "tool_calls": "performance_trace.run_metrics"},
        "content_free": True,
    }
