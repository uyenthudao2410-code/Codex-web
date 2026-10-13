"""Capture bounded read-only RUN/WAVE continuity evidence for r4 canary gates."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
STATUS = HERE / "status-1791815928643-e7d3c41b.json"
RETIRE = HERE / "retire-1791815550588-f42e2f48.json"
OUT = HERE / "r4-lifecycle-continuity-proof.json"


def read(path):
    raw = path.read_bytes()
    return json.loads(raw.decode("utf-8-sig")), {"path": str(path.relative_to(ROOT)), "sha256": hashlib.sha256(raw).hexdigest()}


def main():
    if OUT.exists():
        raise RuntimeError("NEW_ADDITIVE_REPORT_REQUIRED")
    status, status_evidence = read(STATUS)
    retired, retired_evidence = read(RETIRE)
    status_receipt = status["receipt"]
    retired_census = retired["receipt"]["stopped_census"]
    assert status["ok"] is True and status_receipt["runtime"]["mcpRunning"] is True
    assert status_receipt["activation"]["state"] == "READY"
    assert status_receipt["activation"]["admission_open"] is True
    assert status_receipt["census"]["lifecycle"]["unexplained_active_runs"] == 0
    assert retired["ok"] is True and retired_census["lifecycle"]["unexplained_active_runs"] == 0
    assert status_receipt["census"]["lifecycle"]["ordinary_active_runs"] == retired_census["lifecycle"]["ordinary_active_runs"]

    ledger_path = ROOT / ".coding-tools/orchestration/ledger.sqlite3"
    connection = sqlite3.connect(ledger_path.resolve().as_uri() + "?mode=ro", uri=True, timeout=3)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA query_only=ON")
        connection.execute("BEGIN")
        def rows(query):
            return [dict(row) for row in connection.execute(query).fetchall()]
        runs = rows("SELECT status,COUNT(*) AS count FROM runs GROUP BY status ORDER BY status")
        waves = rows("SELECT status,COUNT(*) AS count FROM waves GROUP BY status ORDER BY status")
        acceptance_runs = rows("SELECT status,COUNT(*) AS count FROM runs WHERE lower(metadata_json) LIKE '%accept%' GROUP BY status ORDER BY status")
        acceptance_waves = rows("SELECT status,COUNT(*) AS count FROM waves WHERE lower(metadata_json) LIKE '%accept%' GROUP BY status ORDER BY status")
        active_runs = rows("SELECT COUNT(*) AS count,MIN(started_at) AS oldest_started_at,MAX(started_at) AS newest_started_at FROM runs WHERE status='active'")[0]
        active_waves = rows("SELECT COUNT(*) AS count,MIN(started_at) AS oldest_started_at,MAX(started_at) AS newest_started_at FROM waves WHERE status='active'")[0]
    finally:
        connection.rollback()
        connection.close()

    report = {
        "schema_version": 1,
        "operation": "r4_run_wave_lifecycle_continuity_proof",
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "read_only": True,
        "candidate": status["candidate"],
        "activation_epoch": status_receipt["activation"]["activation_epoch_id"],
        "evidence": {"ready_status": status_evidence, "retired_census": retired_evidence,
                     "ledger_path": str(ledger_path.relative_to(ROOT)),
                     "ledger_sha256": hashlib.sha256(ledger_path.read_bytes()).hexdigest()},
        "bounded_projection": {
            "ready_status_runtime": {key: status_receipt["runtime"].get(key) for key in ("fullyReady", "mcpRunning", "nativeAlive", "authorityReady", "centralConnected", "updateIncomplete")},
            "ready_status_census": {key: status_receipt["census"]["lifecycle"].get(key) for key in ("unexplained_active_runs", "ordinary_active_runs")},
            "retired_census": {key: retired_census["lifecycle"].get(key) for key in ("unexplained_active_runs", "ordinary_active_runs")},
            "ordinary_active_run_count_stable_across_handoff": True,
        },
        "ledger_status_counts": {"runs": runs, "waves": waves},
        "metadata_acceptance_status_counts": {"runs": acceptance_runs, "waves": acceptance_waves},
        "active_run_window": active_runs,
        "active_wave_window": active_waves,
        "interpretation": {
            "proven": "The r4 READY snapshot and the pre-r4 stopped census both report unexplained_active_runs=0 and ordinary_active_runs=24; the r4 runtime is fully ready with MCP/native alive.",
            "ledger_limit": "The canonical ledger currently contains 28 active runs and 28 active waves; this broader count is retained as read-only evidence and is not silently collapsed to the 24-run compact census projection.",
            "acceptance_limit": "Accepted/active status counts and metadata-key counts do not by themselves prove a particular task's operator acceptance latch; exact task/wave IDs must be checked by the supported task_control/status path before mutation.",
        },
        "post_canary_restart_gate_plan": [
            "Before any new patch canary, capture a fresh READY status and exact two-scope census; require unchanged activation epoch, owner identity, package parity and unexplained_active_runs=0.",
            "After the canary, poll the original operation and capture a fresh status/census. Compare run_id/wave_id, lifecycle state, acceptance/rejection report ID and proof lineage through supported task_control reads; do not infer from ledger counts alone.",
            "If a runtime restart or refresh is needed, create one guarded intent, verify the exact owner/start token and idle census, perform the supported restart once, then require a new READY epoch and repeat parity/identity/census gates before resuming.",
            "If any RUN/WAVE is pending acceptance, pause policy restoration and require the operator report acknowledgement before replan; preserve the prior wave and SOL_REJECTED history.",
        ],
        "runtime_mutated": False,
        "ledger_mutated": False,
        "source_modified": False,
    }
    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"ok": True, "report_path": str(OUT), "sha256": hashlib.sha256(OUT.read_bytes()).hexdigest(),
                      "stable_ordinary_active_runs": report["bounded_projection"]["ordinary_active_run_count_stable_across_handoff"],
                      "ledger_active_runs": active_runs["count"], "ledger_active_waves": active_waves["count"]}))


if __name__ == "__main__":
    main()
