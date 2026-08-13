from __future__ import annotations

import argparse
import json
import sqlite3
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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
            accepted_rows = connection.execute(
                "SELECT started_at, finished_at FROM runs WHERE status='accepted' AND finished_at IS NOT NULL"
            ).fetchall()
            tta_seconds: list[float] = []
            for started_raw, finished_raw in accepted_rows:
                started = _parse_time(str(started_raw))
                finished = _parse_time(str(finished_raw))
                if started is not None and finished is not None and finished >= started:
                    tta_seconds.append((finished - started).total_seconds())
            proof_count = int(connection.execute("SELECT COUNT(*) FROM proofs").fetchone()[0])
            handoff_count = int(connection.execute("SELECT COUNT(*) FROM handoff_capsules").fetchone()[0])
            ledger = {
                "present": True,
                "run_status_counts": run_counts,
                "wave_status_counts": wave_counts,
                "idempotency_status_counts": idempotency_counts,
                "background_status_counts": background_counts,
                "lane_lifecycle_counts": lane_counts,
                "proof_records": proof_count,
                "handoff_capsules": handoff_count,
                "accepted_run_tta": {
                    "n": len(tta_seconds),
                    "p50_seconds": round(float(statistics.median(tta_seconds)), 3) if tta_seconds else None,
                    "p90_seconds": _percentile(tta_seconds, 0.90),
                },
            }
        finally:
            connection.close()
    eligible = int(performance.get("idempotency_eligible_calls", 0) or 0)
    eligible_with_key = int(performance.get("idempotency_eligible_key_calls", 0) or 0)
    coverage = round(eligible_with_key / eligible, 6) if eligible else None
    return {
        "benchmark": "runtime activation telemetry snapshot",
        "evidence_class": "local_runtime_measurement_snapshot",
        "schema_version": 1,
        "captured_at": utc_now(),
        "workspace": str(root),
        "performance": {
            "version": int(performance.get("version", 0) or 0),
            "tool_calls": int(performance.get("tool_calls", 0) or 0),
            "errors": int(performance.get("errors", 0) or 0),
            "local_execution_ms": int(performance.get("local_execution_ms", 0) or 0),
            "estimated_wait_ms": int(performance.get("estimated_wait_ms", 0) or 0),
            "idempotency_eligible_calls": eligible,
            "idempotency_eligible_key_calls": eligible_with_key,
            "idempotency_coverage": coverage,
            "proof_cache_hits": int(performance.get("proof_cache_hits", 0) or 0),
            "proof_cache_saved_ms": int(performance.get("proof_cache_saved_ms", 0) or 0),
            "execution_mode_counts": performance.get("execution_mode_counts", {}),
            "route_resolved_counts": performance.get("route_resolved_counts", {}),
            "orchestration_state_counts": performance.get("orchestration_state_counts", {}),
            "run_metrics": performance.get("run_metrics", {}),
        },
        "ledger": ledger,
        "notes": [
            "estimated_wait_ms is a runtime gap proxy, not pure network/model latency",
            "idempotency coverage denominator includes only mutating/expensive calls marked eligible by runtime semantics",
            "accepted-run TTA is measured from durable run timestamps and is not a model-only latency metric",
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
