"""Observe native-first acceptance inputs without starting a runner or VM."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
from datetime import datetime, timezone


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def projection(root: Path, name: str) -> dict:
    source = root / ".coding-tools" / name
    if not source.exists():
        return {"present": False}
    raw = source.read_bytes()
    value = json.loads(raw)
    result = {"present": True, "sha256": hashlib.sha256(raw).hexdigest()}
    if name == "task-state.json":
        result["status"] = value.get("status")
        orchestration = value.get("orchestration", {})
        if isinstance(orchestration, dict):
            result["orchestration"] = {
                key: orchestration[key] for key in ("run_id", "wave_id", "status") if key in orchestration
            }
    elif name == "task-history.json":
        records = value if isinstance(value, list) else value.get("tasks", value.get("history", []))
        result["record_count"] = len(records) if isinstance(records, list) else None
    elif isinstance(value, dict):
        # Only numeric aggregates enter this report. No command text, paths,
        # credentials, or internal credit estimates become billing claims.
        result["numeric_aggregates"] = {
            key: item for key, item in value.items()
            if isinstance(item, (int, float)) and not isinstance(item, bool)
            and not any(term in key.lower() for term in ("credit", "cost", "price", "billing"))
        }
    return result


def observe(root: Path) -> dict:
    report = {
        "schema_version": 1,
        "observation_started_at": now(),
        "machine": os.environ.get("COMPUTERNAME", "unknown"),
        "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
        "branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=root, text=True).strip(),
        "measurement_kind": "read_only_observation",
        "vm_started_by_observer": False,
        "cold_start_measured": False,
        "projections": {name: projection(root, name) for name in (
            "performance.json", "task-history.json", "task-state.json"
        )},
    }
    ledger = root / ".coding-tools/orchestration/ledger.sqlite3"
    if ledger.exists():
        with sqlite3.connect(ledger.as_uri() + "?mode=ro", uri=True, timeout=5) as database:
            database.execute("BEGIN")
            report["canonical_ledger"] = {
                "source": ".coding-tools/orchestration/ledger.sqlite3",
                "run_count": database.execute("SELECT count(*) FROM runs").fetchone()[0],
                "run_states": dict(database.execute("SELECT status,count(*) FROM runs GROUP BY status")),
                "wave_count": database.execute("SELECT count(*) FROM waves").fetchone()[0],
                "wave_states": dict(database.execute("SELECT status,count(*) FROM waves GROUP BY status")),
                "job_states": dict(database.execute(
                    "SELECT lifecycle_state,count(*) FROM managed_process_jobs GROUP BY lifecycle_state"
                )),
            }
    if os.name == "nt":
        command = (
            "$items=@(Get-Process -ErrorAction SilentlyContinue | Where-Object { "
            "$_.ProcessName -match '^(WindowsSandbox|WindowsSandboxClient|WindowsSandboxServer|"
            "WindowsSandboxRemoteSession|VmmemWindowsSandbox|wxc-exec|wxc-windows-sandbox-daemon|"
            "wxc-windows-sandbox-guest)$' } | Select-Object ProcessName,Id,WorkingSet64);"
            "ConvertTo-Json -InputObject $items -Compress"
        )
        observation = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
            shell=False, capture_output=True, text=True, check=True, timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        report["observed_runner_processes"] = json.loads(observation.stdout or "[]")
        report["memory_semantics"] = "OS working set at observation; not a VM memory reservation or peak"
    report["observation_finished_at"] = now()
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    if not output.is_relative_to(root / ".coding-tools/reports"):
        parser.error("output must be inside this repository's .coding-tools/reports")
    if output.exists():
        parser.error("use a new output name to preserve prior evidence")
    report = observe(root)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"report": str(output), "git_head": report["git_head"],
                      "observed_runner_count": len(report.get("observed_runner_processes", []))}))


if __name__ == "__main__":
    main()
