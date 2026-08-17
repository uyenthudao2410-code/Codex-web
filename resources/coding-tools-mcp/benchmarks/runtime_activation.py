from __future__ import annotations

import argparse
import json
import sqlite3
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from coding_tools_mcp.orchestration_ledger import _proof_cache_opportunity_summary


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def _status_counts(connection: sqlite3.Connection, table: str, column: str = "status") -> dict[str, int]:
    rows = connection.execute(f"SELECT {column}, COUNT(*) FROM {table} GROUP BY {column}").fetchall()
    return {str(row[0]): int(row[1]) for row in rows}


def _parse_time(value: str) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def _percentile(values: list[float], quantile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int((len(ordered) - 1) * quantile + 0.999999)))
    return round(float(ordered[index]), 3)


def _json_object(value: object) -> dict[str, Any]:
    try:
        parsed = json.loads(str(value or "{}"))
    except (TypeError, ValueError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _tta_summary(values: list[float]) -> dict[str, Any]:
    return {
        "n": len(values),
        "p50_seconds": round(float(statistics.median(values)), 3) if values else None,
        "p90_seconds": _percentile(values, 0.90),
    }


def _count_map(value: object) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, int] = {}
    for key, raw in value.items():
        try:
            count = max(0, int(raw))
        except (TypeError, ValueError):
            continue
        if count:
            result[str(key)] = count
    return result


def _accepted_run_cohorts(connection: sqlite3.Connection) -> tuple[list[float], list[dict[str, Any]], dict[str, Any]]:
    accepted_rows = connection.execute(
        "SELECT run_id, started_at, finished_at, metadata_json "
        "FROM runs WHERE status='accepted' AND finished_at IS NOT NULL"
    ).fetchall()

    latest_route_by_run: dict[str, str] = {}
    route_rows = connection.execute(
        "SELECT run_id, payload_json FROM events WHERE event_type='route_selected' ORDER BY seq"
    ).fetchall()
    for run_id_raw, payload_raw in route_rows:
        payload = _json_object(payload_raw)
        route = str(payload.get("resolved") or "").strip()
        if route:
            latest_route_by_run[str(run_id_raw)] = route

    replanned_runs = {
        str(row[0])
        for row in connection.execute("SELECT DISTINCT run_id FROM waves WHERE status='replanned'").fetchall()
    }

    tta_seconds: list[float] = []
    grouped: dict[tuple[str, str, str, str, str], list[float]] = {}
    complete = 0
    for run_id_raw, started_raw, finished_raw, metadata_raw in accepted_rows:
        started = _parse_time(str(started_raw))
        finished = _parse_time(str(finished_raw))
        if started is None or finished is None or finished < started:
            continue
        duration = (finished - started).total_seconds()
        tta_seconds.append(duration)

        run_id = str(run_id_raw)
        metadata = _json_object(metadata_raw)
        workflow = str(metadata.get("workflow") or "").strip()
        phase = str(metadata.get("phase") or "").strip()
        entry_surface = str(metadata.get("entry_surface") or "").strip()
        if not entry_surface and workflow and phase:
            entry_surface = "agent_workflow"
        entry_surface = entry_surface or "unknown"
        task_class = str(metadata.get("task_class") or workflow or "unknown").strip() or "unknown"
        route = latest_route_by_run.get(run_id, "unknown")
        acceptance_status = "accepted"
        repair_status = "repaired" if run_id in replanned_runs else "first_pass"
        if "unknown" not in {entry_surface, route, task_class}:
            complete += 1
        key = (entry_surface, route, task_class, acceptance_status, repair_status)
        grouped.setdefault(key, []).append(duration)

    cohorts: list[dict[str, Any]] = []
    for key in sorted(grouped):
        entry_surface, route, task_class, acceptance_status, repair_status = key
        cohorts.append(
            {
                "entry_surface": entry_surface,
                "route": route,
                "task_class": task_class,
                "acceptance_status": acceptance_status,
                "repair_status": repair_status,
                **_tta_summary(grouped[key]),
            }
        )
    total = len(tta_seconds)
    coverage = {
        "total": total,
        "complete": complete,
        "incomplete": total - complete,
        "complete_ratio": round(complete / total, 6) if total else None,
    }
    return tta_seconds, cohorts, coverage


def build_snapshot(workspace: Path) -> dict[str, Any]:
    root = workspace.resolve()
    performance = _read_json(root / ".coding-tools" / "performance.json")
    ledger_path = root / ".coding-tools" / "orchestration" / "ledger.sqlite3"
    ledger: dict[str, Any] = {"present": ledger_path.is_file()}
    if ledger_path.is_file():
        connection = sqlite3.connect(ledger_path)
        try:
            run_counts = _status_counts(connection, "runs")
            wave_counts = _status_counts(connection, "waves")
            idempotency_counts = _status_counts(connection, "idempotency_records")
            background_counts = _status_counts(connection, "background_operations")
            lane_counts = _status_counts(connection, "agent_lanes", "lifecycle")
            tta_seconds, accepted_run_cohorts, cohort_coverage = _accepted_run_cohorts(connection)
            proof_count = int(connection.execute("SELECT COUNT(*) FROM proofs").fetchone()[0])
            handoff_count = int(connection.execute("SELECT COUNT(*) FROM handoff_capsules").fetchone()[0])
            proof_cache_opportunity = _proof_cache_opportunity_summary(connection)
            ledger = {
                "present": True,
                "run_status_counts": run_counts,
                "wave_status_counts": wave_counts,
                "idempotency_status_counts": idempotency_counts,
                "background_status_counts": background_counts,
                "lane_lifecycle_counts": lane_counts,
                "proof_records": proof_count,
                "handoff_capsules": handoff_count,
                "accepted_run_tta": _tta_summary(tta_seconds),
                "accepted_run_cohort_coverage": cohort_coverage,
                "accepted_run_cohorts": accepted_run_cohorts,
                "proof_cache_opportunity": proof_cache_opportunity,
            }
        finally:
            connection.close()
    performance_version = int(performance.get("version", 0) or 0)
    eligible = int(performance.get("idempotency_eligible_calls", 0) or 0)
    eligible_with_key = int(performance.get("idempotency_eligible_key_calls", 0) or 0)
    legacy_coverage = round(eligible_with_key / eligible, 6) if eligible else None
    required = int(performance.get("idempotency_required_calls", 0) or 0)
    required_with_key = int(performance.get("idempotency_required_key_calls", 0) or 0)
    required_coverage = round(required_with_key / required, 6) if required else None
    policy_epoch = str(performance.get("idempotency_policy_epoch") or "")
    current_required = int(performance.get("idempotency_current_policy_required_calls", 0) or 0)
    current_required_with_key = int(performance.get("idempotency_current_policy_required_key_calls", 0) or 0)
    current_required_coverage = round(current_required_with_key / current_required, 6) if current_required else None
    optional = int(performance.get("idempotency_optional_calls", 0) or 0)
    optional_with_key = int(performance.get("idempotency_optional_key_calls", 0) or 0)
    if performance_version >= 5 and policy_epoch:
        coverage_source = "required_current_policy"
        decision_coverage = current_required_coverage
    else:
        coverage_source = "required_v5" if performance_version >= 5 else "legacy_v4"
        decision_coverage = required_coverage if coverage_source == "required_v5" else legacy_coverage
    error_class_counts = _count_map(performance.get("error_class_counts"))
    classified_error_samples = sum(error_class_counts.values())
    unknown_error_samples = int(error_class_counts.get("UNKNOWN", 0))
    unknown_error_share = round(unknown_error_samples / classified_error_samples, 6) if classified_error_samples else None
    error_taxonomy_epoch = str(performance.get("error_taxonomy_epoch") or "").strip()
    error_taxonomy_current_counts = _count_map(performance.get("error_taxonomy_current_counts"))
    error_taxonomy_current_samples = sum(error_taxonomy_current_counts.values())
    error_taxonomy_current_unknown_samples = int(error_taxonomy_current_counts.get("UNKNOWN", 0))
    error_taxonomy_current_typed_samples = error_taxonomy_current_samples - error_taxonomy_current_unknown_samples
    error_taxonomy_current_typed_coverage = (
        round(error_taxonomy_current_typed_samples / error_taxonomy_current_samples, 6)
        if error_taxonomy_current_samples else None
    )
    error_taxonomy_current_unknown_share = (
        round(error_taxonomy_current_unknown_samples / error_taxonomy_current_samples, 6)
        if error_taxonomy_current_samples else None
    )
    phase_timing_samples = int(performance.get("phase_timing_samples", 0) or 0)
    phase_timing_ms = _count_map(performance.get("phase_timing_ms"))
    localization_samples = int(performance.get("localization_samples", 0) or 0)
    localization_queries = int(performance.get("localization_queries", 0) or 0)
    lsp_available_samples = int(performance.get("lsp_available_samples", 0) or 0)
    lsp_attempted_queries = int(performance.get("lsp_attempted_queries", 0) or 0)
    lsp_handled_queries = int(performance.get("lsp_handled_queries", 0) or 0)
    fallback_search_queries = int(performance.get("fallback_search_queries", 0) or 0)
    return {
        "benchmark": "runtime activation telemetry snapshot",
        "evidence_class": "local_runtime_measurement_snapshot",
        "schema_version": 3,
        "captured_at": utc_now(),
        "workspace": str(root),
        "performance": {
            "version": performance_version,
            "tool_calls": int(performance.get("tool_calls", 0) or 0),
            "errors": int(performance.get("errors", 0) or 0),
            "local_execution_ms": int(performance.get("local_execution_ms", 0) or 0),
            "estimated_wait_ms": int(performance.get("estimated_wait_ms", 0) or 0),
            "idempotency_eligible_calls": eligible,
            "idempotency_eligible_key_calls": eligible_with_key,
            "idempotency_legacy_coverage": legacy_coverage,
            "idempotency_required_calls": required,
            "idempotency_required_key_calls": required_with_key,
            "idempotency_required_coverage": required_coverage,
            "idempotency_policy_epoch": policy_epoch or None,
            "idempotency_current_policy_required_calls": current_required,
            "idempotency_current_policy_required_key_calls": current_required_with_key,
            "idempotency_current_policy_required_coverage": current_required_coverage,
            "idempotency_current_policy_by_operation": dict(performance.get("idempotency_current_policy_by_operation", {}) or {}),
            "idempotency_optional_calls": optional,
            "idempotency_optional_key_calls": optional_with_key,
            "idempotency_auto_key_calls": int(performance.get("idempotency_auto_key_calls", 0) or 0),
            "idempotency_coverage": decision_coverage,
            "idempotency_coverage_source": coverage_source,
            "idempotency_coverage_target": 0.95,
            "idempotency_coverage_gate_passed": decision_coverage is not None and decision_coverage >= 0.95,
            "idempotency_v5_epoch": "post_activation_only" if performance_version >= 5 else "not_active",
            "error_class_counts": error_class_counts,
            "error_classified_samples": classified_error_samples,
            "error_unknown_samples": unknown_error_samples,
            "error_unknown_share": unknown_error_share,
            "error_taxonomy_epoch": error_taxonomy_epoch or None,
            "error_taxonomy_current_counts": error_taxonomy_current_counts,
            "error_taxonomy_current_samples": error_taxonomy_current_samples,
            "error_taxonomy_current_typed_samples": error_taxonomy_current_typed_samples,
            "error_taxonomy_current_unknown_samples": error_taxonomy_current_unknown_samples,
            "error_taxonomy_current_typed_coverage": error_taxonomy_current_typed_coverage,
            "error_taxonomy_current_unknown_share": error_taxonomy_current_unknown_share,
            "error_taxonomy_current_status": "observed" if error_taxonomy_current_samples else "no_current_epoch_samples",
            "error_taxonomy_historical_backfill": False,
            "phase_timing_samples": phase_timing_samples,
            "phase_timing_ms": phase_timing_ms,
            "phase_timing_available": bool(phase_timing_samples and phase_timing_ms),
            "localization_samples": localization_samples,
            "localization_queries": localization_queries,
            "lsp_available_samples": lsp_available_samples,
            "lsp_available_rate": round(lsp_available_samples / localization_samples, 6) if localization_samples else None,
            "lsp_attempted_queries": lsp_attempted_queries,
            "lsp_handled_queries": lsp_handled_queries,
            "lsp_hit_rate": round(lsp_handled_queries / lsp_attempted_queries, 6) if lsp_attempted_queries else None,
            "fallback_search_queries": fallback_search_queries,
            "fallback_search_rate": round(fallback_search_queries / localization_queries, 6) if localization_queries else None,
            "proof_cache_eligible": int(performance.get("proof_cache_eligible", 0) or 0),
            "proof_cache_hits": int(performance.get("proof_cache_hits", 0) or 0),
            "proof_cache_misses": int(performance.get("proof_cache_misses", 0) or 0),
            "proof_cache_miss_reasons": dict(performance.get("proof_cache_miss_reasons", {}) or {}),
            "proof_cache_saved_ms": int(performance.get("proof_cache_saved_ms", 0) or 0),
            "execution_mode_counts": performance.get("execution_mode_counts", {}),
            "route_resolved_counts": performance.get("route_resolved_counts", {}),
            "orchestration_state_counts": performance.get("orchestration_state_counts", {}),
            "run_metrics": performance.get("run_metrics", {}),
        },
        "ledger": ledger,
        "notes": [
            "estimated_wait_ms is a runtime gap proxy, not pure network/model latency",
            "PerformanceTrace v5 retains cumulative required-idempotency coverage for audit; when a named current policy epoch exists, production coverage gates use only post-policy required samples and never backfill historical misses",
            "optional idempotency covers side effects whose exact repeat can be intentional; it must not be forced into the required replay-protection gate",
            "v5 required/optional/error/phase counters begin with the activated v5 runtime epoch and are not retroactively inferred from v4 history",
            "cumulative error_class_counts remain an audit projection across v5 history; the named error_taxonomy_current_counts epoch is prospective-only and historical UNKNOWN observations are never backfilled",
            "error_taxonomy_current_typed_coverage uses only current-epoch classified errors as its denominator; an empty current epoch remains null/no_current_epoch_samples rather than being treated as perfect coverage",
            "phase_timing_available reports measured phase samples only; missing provider/model timing is not estimated from EOCL execution windows",
            "proof-cache coverage uses eligible proof stages as the denominator; miss reasons classify cold, fingerprint, or stage-version invalidation without changing reuse semantics",
            "LSP/localization rates use only live composite-read measurements; cached replay is excluded by the Runtime extractor and unavailable semantic providers remain explicit fallback evidence",
            "accepted-run TTA is measured from durable run timestamps and is not a model-only latency metric",
            "accepted-run cohort dimensions are derived only from durable run metadata/events/wave state; missing dimensions remain unknown",
            "routing comparisons should use complete homogeneous accepted-run cohorts rather than raw global TTA",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", default="../..")
    parser.add_argument("--label", default="snapshot")
    args = parser.parse_args()
    workspace = Path(args.workspace).resolve()
    report = build_snapshot(workspace)
    report_dir = Path(__file__).resolve().parent / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    safe_label = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in args.label).strip("-") or "snapshot"
    target = report_dir / f"runtime-activation-{safe_label}-{stamp}.json"
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"report: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
