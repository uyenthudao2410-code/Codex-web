"""Exact r12 local observations. Reads only; stdout has no credentials/content."""
import datetime
import hashlib
import json
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(r"E:\Github\Tools-Codex-web")
HERE = Path(__file__).resolve().parent
PROFILE = Path(r"C:\Users\daoth\AppData\Roaming\web-mcp-assistant")
ACTION = "act_6aa1329b96c146f38c807f9926b3e684"
TASK = "task_d2c1dd3bff4042d084b045e9bc5a381b"
ATTEMPT = "try_4178cd41d2f3424a81dcb3c4cc706ed1"
NATIVE_CONTEXT = "cpap_8de2cfe03c2a2da52b6fdcaaef626ae31b31fc296a1bb72885c42aad"
NATIVE_REQUEST = "control-plane-approved-patch-workflow-a68e2de8825490466499dacd"
HEAD = "2c554f59cb7b8ffc86ce5e0e28076c792777642f"
SINCE = "2026-10-11T19:49:00.000Z"
FILES = {
    "tests/fixtures/initial-proof-canary-target.cjs": "90363c394e12dd67f9003ef96b033e739c7837b34c238238966df623d9e55650",
    "tests/fixtures/initial-proof-canary-check.cjs": "059c4e83fcbeb07b293312988975b7267d8ab8428872e5ff1211dbf059800230",
}
OLD = {
    "runs": ("run_id", "95e909f0040a448faa9f1f3257e2ee2c", "a167681ee42f25bc76a6eb03f63dfd91ef382924573205835f07d5ab01eef590"),
    "waves": ("wave_id", "c101beadfc6d4f2fbc13845052c84693", "59d351b7afbc33b8e8f8f2f35bf5dfdd1c8a319bab93dd005481f4df36862bce"),
}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def sha(value):
    return hashlib.sha256(value).hexdigest()


def need(value, code):
    if not value:
        raise ValueError(code)


def json_bytes(path):
    raw = path.read_bytes()
    return json.loads(raw), sha(raw)


def collect():
    need(HERE == ROOT / ".coding-tools/reports/unified-setup-20261011/executor-repair/candidate-r12/reconciliation", "EXACT_HELPER_DIRECTORY_REQUIRED")
    pins, pins_sha = json_bytes(HERE.parent / "live-canary/root-reconciled-canary.pins.json")
    need(pins["native_preflight"]["source_head"] == HEAD, "R12_PINS_HEAD_CHANGED")
    head = subprocess.run(["git", "--no-optional-locks", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, check=True, timeout=10).stdout.decode().strip()
    need(head == HEAD, "SOURCE_HEAD_CHANGED")
    hashes = {name: sha((ROOT / name).read_bytes()) for name in FILES}
    need(hashes == FILES, "CANARY_PREIMAGE_OR_CHECKER_CHANGED")
    journal, journal_sha = json_bytes(PROFILE / "control-plane-node.json.approved-patch-bridge-journal.json")
    entry = journal.get("entries", {}).get(ACTION + "|" + ATTEMPT)
    need(isinstance(entry, dict), "EXACT_JOURNAL_ENTRY_MISSING")
    receipt = entry.get("receipt") or {}
    payload = receipt.get("payload") or {}
    need(entry.get("action_id") == ACTION and entry.get("attempt_id") == ATTEMPT
         and receipt.get("action_id") == ACTION and receipt.get("attempt_id") == ATTEMPT
         and entry.get("state") == "unknown" and receipt.get("receipt_state") == "unknown" and receipt.get("receipt_submitted") is True
         and receipt.get("local_handle") == "" and payload.get("code") == "CONTROL_PLANE_APPROVED_PATCH_EFFECT_UNKNOWN"
         and payload.get("diagnostic_code") == "CONTROL_PLANE_APPROVED_PATCH_MCP_REJECTED", "EXACT_JOURNAL_STATE_CHANGED")
    performance, performance_sha = json_bytes(ROOT / ".coding-tools/performance.json")
    rows = [row for row in performance.get("recent", []) if row.get("tool") == "agent_workflow"
            and row.get("started_at") == "2026-10-11T19:50:12.489Z"
            and row.get("invocation", {}).get("request_id") == NATIVE_REQUEST
            and row.get("invocation", {}).get("task_context_id") == NATIVE_CONTEXT]
    need(len(rows) == 1, "EXACT_NATIVE_FAILURE_MISSING")
    row = rows[0]
    need(row.get("outcome") == {"status": "error", "error_code": "WORKTREE_STATUS_TOO_LARGE", "error_category": "validation", "retryable": False}
         and row.get("ok") is False and not row.get("run_id") and not row.get("wave_id")
         and row.get("finished_at") == "2026-10-11T19:50:13.078Z"
         and row.get("invocation", {}).get("client_id") == "electron-control-plane-approved-patch-bridge", "EXACT_NATIVE_FAILURE_CHANGED")
    workspace_rows = [item for item in performance.get("recent", []) if item.get("tool") == "workspace_context"
                      and item.get("started_at") == "2026-10-11T19:50:12.139Z"]
    need(len(workspace_rows) == 1 and workspace_rows[0].get("ok") is True, "EXACT_BOOTSTRAP_SUCCESS_MISSING")
    ledger = ROOT / ".coding-tools/orchestration/ledger.sqlite3"
    db = sqlite3.connect(ledger.resolve(strict=True).as_uri() + "?mode=ro", uri=True, timeout=10)
    db.row_factory = sqlite3.Row
    try:
        db.execute("PRAGMA query_only=ON")
        db.execute("BEGIN")
        protected = {}
        for table, (column, identifier, expected) in OLD.items():
            rows = db.execute(f"SELECT * FROM {table} WHERE {column}=?", (identifier,)).fetchall()
            need(len(rows) == 1, "PROTECTED_ROW_MISSING")
            actual = sha(canonical(dict(rows[0])))
            need(actual == expected, "PROTECTED_ROW_CHANGED")
            protected[table] = {"id": identifier, "sha256": actual, "unchanged": True}
        since_counts = {}
        for table, column in [("runs", "started_at"), ("waves", "started_at"), ("managed_process_jobs", "started_at"), ("proofs", "started_at"), ("events", "event_time"), ("problem_events", "recorded_at")]:
            since_counts[table] = db.execute(f"SELECT count(*) FROM {table} WHERE {column}>=?", (SINCE,)).fetchone()[0]
        need(all(count == 0 for count in since_counts.values()), "NEW_NATIVE_LEDGER_EFFECT_REQUIRES_RECONCILIATION")
        matches = {}
        for table, column in [("runs", "metadata_json"), ("waves", "metadata_json"), ("managed_process_jobs", "metadata_json"), ("proofs", "metadata_json"), ("events", "payload_json")]:
            matches[table] = sum(db.execute(f"SELECT count(*) FROM {table} WHERE {column} LIKE ?", ("%" + identifier + "%",)).fetchone()[0] for identifier in (ACTION, TASK, ATTEMPT, NATIVE_CONTEXT, NATIVE_REQUEST))
        need(all(count == 0 for count in matches.values()), "RELATED_NATIVE_LEDGER_EFFECT_REQUIRES_RECONCILIATION")
        snapshot = {"query_only": bool(db.execute("PRAGMA query_only").fetchone()[0]), "transaction": True, "ledger_path": str(ledger), "events_max_seq": db.execute("SELECT max(seq) FROM events").fetchone()[0]}
    finally:
        db.rollback()
        db.close()
    need({name: sha((ROOT / name).read_bytes()) for name in FILES} == hashes, "CANARY_CHANGED_DURING_READ")
    observed = int(time.time() * 1000)
    return {
        "schema_version": 1, "kind": "r12_query_only_native_no_effect_local", "ok": True,
        "observed_at_ms": observed, "observed_at_utc": datetime.datetime.fromtimestamp(observed / 1000, datetime.timezone.utc).isoformat(),
        "action_id": ACTION, "task_id": TASK, "attempt_id": ATTEMPT,
        "source_head": head, "pins_sha256": pins_sha,
        "native_identity_pins": {key: pins[key] for key in ("activation_epoch", "runtime_instance_id", "mcp_server_instance_id", "native_tool_contract_sha256")},
        "files": hashes, "target_is_exact_preimage": True, "checker_unchanged": True,
        "journal": {"sha256": journal_sha, "state": entry["state"], "receipt_state": receipt["receipt_state"], "receipt_submitted": True, "local_handle": "", "code": payload["code"], "diagnostic_code": payload["diagnostic_code"]},
        "native_failure": {"performance_sha256": performance_sha, "row_sha256": sha(canonical(row)), "tool": row["tool"], "started_at": row["started_at"], "finished_at": row["finished_at"], "error_code": "WORKTREE_STATUS_TOO_LARGE", "error_category": "validation", "retryable": False, "request_id": NATIVE_REQUEST, "task_context_id": NATIVE_CONTEXT, "client_id": row["invocation"]["client_id"], "run_id": "", "wave_id": "", "preceding_workspace_context_succeeded": True},
        "ledger": {"snapshot": snapshot, "since_utc": SINCE, "since_counts": since_counts, "related_id_counts": matches, "protected_records": protected},
        "no_native_patch_effect_observed": True, "active_census_required": True,
        "receipt_terminalized": False, "replay_forbidden": True, "acceptance_performed": False,
        "mutated_canonical_ledger": False, "external_mutation": False, "secret_values_emitted": False,
    }


if __name__ == "__main__":
    try:
        print(json.dumps(collect(), sort_keys=True))
    except Exception as exc:
        code = str(exc) if isinstance(exc, ValueError) and str(exc).replace("_", "").isalnum() and str(exc).isupper() else "QUERY_ONLY_NATIVE_NO_EFFECT_READ_FAILED"
        print(json.dumps({"ok": False, "code": code, "external_mutation": False, "secret_values_emitted": False, "replay_forbidden": True}))
        sys.exit(2)
