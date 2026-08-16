from __future__ import annotations

import argparse
import json
import os
import secrets
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from coding_tools_mcp.execution_resources import (  # noqa: E402
    ACTIVE_LIFECYCLES,
    ExecutionResourceGovernor,
    process_identity_token,
    process_is_alive,
)
from coding_tools_mcp.orchestration_ledger import OrchestrationLedger  # noqa: E402


def _current_invocation_pids() -> set[int]:
    pids = {os.getpid()}
    try:
        import psutil

        pids.update(int(parent.pid) for parent in psutil.Process().parents())
    except (ImportError, OSError, RuntimeError):
        pass
    return {pid for pid in pids if pid > 0}


def _public_job(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "job_id": row.get("job_id"),
        "run_id": row.get("run_id"),
        "wave_id": row.get("wave_id"),
        "command_id": row.get("command_id"),
        "owner": row.get("owner"),
        "resource_class": row.get("resource_class"),
        "lifecycle_state": row.get("lifecycle_state"),
        "root_pid": row.get("root_pid"),
    }


def _select_owned_codex_sidecar(
    rows: list[dict[str, Any]],
    active_claims: list[dict[str, Any]],
) -> tuple[dict[str, Any] | None, str]:
    if active_claims:
        return None, "active_scheduling_claims_present"
    if len(rows) != 1:
        return None, "active_managed_work_ambiguous"
    row = rows[0]
    if not (
        str(row.get("owner") or "") == "codex-app-server"
        and str(row.get("command_id") or "").startswith("codex-app-server-")
        and str(row.get("resource_class") or "") == "MEDIUM"
        and not str(row.get("run_id") or "")
        and not str(row.get("wave_id") or "")
        and str(row.get("lifecycle_state") or "") in ACTIVE_LIFECYCLES
        and int(row.get("root_pid") or 0) > 1
        and bool(str(row.get("root_process_token") or ""))
    ):
        return None, "active_job_not_owned_codex_sidecar"
    return row, "eligible"


def _terminate_windows_tree(pid: int) -> bool:
    if os.name != "nt":
        return False
    try:
        completed = subprocess.run(
            ["taskkill.exe", "/PID", str(pid), "/T", "/F"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
            check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return completed.returncode == 0 or not process_is_alive(pid)


def repair_owned_codex_sidecar(
    governor: ExecutionResourceGovernor,
    rows: list[dict[str, Any]],
    active_claims: list[dict[str, Any]],
    *,
    is_alive: Callable[[int], bool] = process_is_alive,
    identity_token: Callable[[int], str] = process_identity_token,
    terminate_tree: Callable[[int], bool] | None = None,
) -> dict[str, Any]:
    row, reason = _select_owned_codex_sidecar(rows, active_claims)
    if row is None:
        return {"attempted": False, "repaired": False, "reason": reason}
    pid = int(row["root_pid"])
    expected_token = str(row["root_process_token"])
    if not is_alive(pid):
        governor.reconcile()
        remaining = {item["job_id"] for item in governor._rows(active_only=True)}
        repaired = str(row["job_id"]) not in remaining
        return {
            "attempted": False,
            "repaired": repaired,
            "reason": "process_already_gone" if repaired else "process_liveness_uncertain",
        }
    observed_token = identity_token(pid)
    if not observed_token or observed_token != expected_token:
        return {
            "attempted": False,
            "repaired": False,
            "reason": "process_identity_mismatch",
        }
    if terminate_tree is None:
        if os.name != "nt":
            return {
                "attempted": False,
                "repaired": False,
                "reason": "unsupported_platform",
            }
        terminate_tree = _terminate_windows_tree
    if not terminate_tree(pid):
        return {"attempted": True, "repaired": False, "reason": "tree_termination_failed"}
    deadline = time.time() + 5.0
    while time.time() < deadline and is_alive(pid):
        if identity_token(pid) != expected_token:
            break
        time.sleep(0.05)
    if is_alive(pid) and identity_token(pid) == expected_token:
        return {"attempted": True, "repaired": False, "reason": "tree_still_alive"}
    governor.reconcile()
    remaining = {item["job_id"] for item in governor._rows(active_only=True)}
    repaired = str(row["job_id"]) not in remaining
    return {
        "attempted": True,
        "repaired": repaired,
        "reason": "repaired" if repaired else "ledger_reconciliation_incomplete",
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Conservatively reconcile durable managed-process scheduling state."
    )
    parser.add_argument("--workspace", default=".")
    parser.add_argument(
        "--repair-owned-codex-sidecar",
        action="store_true",
        help="Terminate only a uniquely verified runtime-owned Codex App Server sidecar.",
    )
    args = parser.parse_args()

    workspace = Path(args.workspace).expanduser().resolve(strict=False)
    ledger = OrchestrationLedger(workspace)
    nonce = secrets.token_hex(8)
    governor = ExecutionResourceGovernor(
        workspace,
        ledger,
        process_instance_id=f"resource-reconcile-{nonce}",
        runtime_instance_id=f"resource-reconcile-{nonce}",
    )
    reconciliation = governor.reconcile()
    active_rows = governor._rows(active_only=True)
    invocation_pids = _current_invocation_pids()
    current_invocation_rows = [
        row
        for row in active_rows
        if int(row.get("root_pid") or 0) in invocation_pids
        and governor._row_age_seconds(row) <= 30.0
    ]
    remaining_rows = [row for row in active_rows if row not in current_invocation_rows]
    active_claims = governor._claim_rows(active_only=True)
    repair = None
    if args.repair_owned_codex_sidecar:
        repair = repair_owned_codex_sidecar(governor, remaining_rows, active_claims)
        active_rows = governor._rows(active_only=True)
        current_invocation_rows = [
            row
            for row in active_rows
            if int(row.get("root_pid") or 0) in invocation_pids
            and governor._row_age_seconds(row) <= 30.0
        ]
        remaining_rows = [row for row in active_rows if row not in current_invocation_rows]
        active_claims = governor._claim_rows(active_only=True)
    result = {
        "schema_version": 1,
        "workspace": str(workspace),
        "reconciliation": reconciliation,
        "active_command_count": len(remaining_rows),
        "active_claim_count": len(active_claims),
        "ignored_current_process_rows": len(current_invocation_rows),
        "orphaned_count": sum(
            1 for row in remaining_rows if row.get("lifecycle_state") == "orphaned"
        ),
        "active_jobs": [_public_job(row) for row in remaining_rows[:20]],
        "quiescent": not remaining_rows and not active_claims,
    }
    if repair is not None:
        result["repair"] = repair
    print(json.dumps(result, sort_keys=True))
    return 0 if result["quiescent"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
