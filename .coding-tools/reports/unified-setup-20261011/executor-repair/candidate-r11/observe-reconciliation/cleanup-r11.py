"""Root-only once cleanup of the exact rejected r11 action, without replay."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sqlite3
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
OBSERVER_SHA = "6525b2c6069c474c1c0c6e45084f19e4700246d2262b087c633e3692983caf73"


def load_observer():
    path = HERE / "observe-r11.py"
    if not path.is_file() or path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != OBSERVER_SHA:
        raise ValueError("OBSERVER_HASH_CHANGED")
    spec = importlib.util.spec_from_file_location("r11_rejection_cleanup_observer", path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def cleanup(execute):
    observer = load_observer()
    observer.require(execute is True, "ROOT_EXPLICIT_CLEANUP_REQUIRED")
    canary, common, pins, marker, database, family = observer.observed_state()
    try:
        rejection = observer.rejected_receipt(database, family)
        canary.exclusive(canary.NEXT_OPERATION_DIR / "reconciliation-cleanup-intent.json", {
            "action_id": observer.ACTION, "task_id": observer.TASK, "pins_sha256": canary.digest(pins),
            "rejection_receipt_id": rejection["receipt_id"], "reason": "exact settled rejection before patch/proof; no replay"})
        origin, auth = canary.mcp_credentials(common)
        released = canary.call(origin, auth, "task_control", {"operation": "writer_release", "task_id": observer.TASK,
            "reason": "exact rejected canary settled; no patch/proof applied; no replay"})
        observer.require(released.get("execution") == "writer_lease_released", "WRITER_RELEASE_RESPONSE_INVALID")
        canary.exclusive(canary.NEXT_OPERATION_DIR / "reconciliation-writer-released.json", {"task_id": observer.TASK})
        closed = canary.call(origin, auth, "workspace_context", {"operation": "task_close", "task_id": observer.TASK}).get("task", {})
        observer.require(closed.get("task_id") == observer.TASK and closed.get("closed_at_ms") is not None,
            "TASK_CLOSE_RESPONSE_INVALID")
        canary.exclusive(canary.NEXT_OPERATION_DIR / "reconciliation-task-closed.json", {"task_id": observer.TASK, "closed_at_ms": closed["closed_at_ms"]})
        conn = sqlite3.connect(database.as_uri() + "?mode=ro", uri=True, timeout=5)
        try:
            conn.execute("PRAGMA query_only=ON")
            observer.require(conn.execute("SELECT closed_at_ms FROM mcp_task_sessions WHERE task_id=?", (observer.TASK,)).fetchone()[0] is not None
                and conn.execute("SELECT COUNT(*) FROM mcp_task_writer_leases WHERE task_id=? AND released_at_ms IS NULL", (observer.TASK,)).fetchone()[0] == 0,
                "REJECTED_CANARY_CLEANUP_NOT_TERMINAL")
        finally:
            conn.close()
        return {"ok": True, "phase": "cleanup", "action_id": observer.ACTION, "task_id": observer.TASK,
            "terminal_rejection": rejection, "writer_released": True, "task_closed": True,
            "remote_mutation": True, "replay_forbidden": True, "native_semantic_acceptance": "pending"}
    finally:
        if canary._prior_marker_path is not None:
            observer.require(canary.sha(canary._prior_marker_path.read_bytes()) == canary._prior_marker_sha256,
                "PREVIOUS_AUTHORITY_MARKER_CHANGED_DURING_CLEANUP")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("cleanup",))
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(cleanup(args.execute), sort_keys=True))
    except Exception as error:
        print(json.dumps({"ok": False, "phase": "r11_rejected_cleanup_failed", "code": getattr(error, "code", "REJECTED_CLEANUP_UNCERTAIN_NO_RETRY"),
            "replay_forbidden": True}, sort_keys=True))
        raise SystemExit(1) from None
