"""Additive read-only deadline audit; emit allowlisted evidence, never journal payloads."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
REPORTS = Path(__file__).parent
ACTION = "act_1de2cef3dc304d6e8b3f90237d7c136a"
ATTEMPT = "try_8d31c7cfb661441aadb9e620e47508a3"
PREFIX = "72f626fc9fb07f5f10c4855c"
WINDOW = ("2026-10-12T13:04:50", "2026-10-12T13:05:45.999")


def read_json(path):
    raw = path.read_bytes()
    return json.loads(raw.decode("utf-8-sig")), {
        "path": str(path.relative_to(ROOT)),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "size_bytes": len(raw),
    }


def exact_actions(item):
    if isinstance(item, dict):
        if item.get("action_id") == ACTION and "delivery_attempts" in item:
            yield item
        for value in item.values():
            yield from exact_actions(value)
    elif isinstance(item, list):
        for value in item:
            yield from exact_actions(value)


def epoch_ms(timestamp):
    return round(datetime.fromisoformat(timestamp.replace("Z", "+00:00")).timestamp() * 1000)


def main():
    output = REPORTS / sys.argv[1]
    if output.exists() or output.parent != REPORTS or output.suffix != ".json":
        raise RuntimeError("NEW_ADDITIVE_REPORT_REQUIRED")
    readiness, readiness_evidence = read_json(REPORTS / "server-readiness-read067-unknown.json")
    local, local_evidence = read_json(REPORTS / "local-read067-timeout-evidence.json")
    performance, performance_evidence = read_json(ROOT / ".coding-tools/performance.json")
    candidates = list(exact_actions(readiness))
    if len(candidates) != 1:
        raise RuntimeError("EXACT_ORIGINAL_ACTION_REQUIRED")
    action = candidates[0]
    attempts = [row for row in action["delivery_attempts"] if row.get("attempt_id") == ATTEMPT]
    receipts = [row for row in action["receipts"] if row.get("receipt_state") == "unknown"]
    if len(attempts) != 1 or len(receipts) != 1:
        raise RuntimeError("EXACT_ORIGINAL_ATTEMPT_AND_UNKNOWN_RECEIPT_REQUIRED")
    dispatch = attempts[0]["dispatched_at_ms"]
    unknown = receipts[0]["received_at_ms"]
    events = []
    for row in performance.get("recent", []):
        if WINDOW[0] <= row.get("started_at", "") <= WINDOW[1]:
            invocation = row.get("invocation") or {}
            events.append({key: row.get(key) for key in (
                "tool", "started_at", "finished_at", "duration_ms", "ok", "error_class"
            )} | {"request_id": invocation.get("request_id")})
    # The live recent-100 projection can roll off during another canary. Reuse
    # the exact allowlisted observation already preserved by the earlier audit.
    exact_events = [{key: row.get(key) for key in (
        "tool", "started_at", "finished_at", "duration_ms", "ok", "error_class"
    )} | {"request_id": (row.get("invocation") or {}).get("request_id")}
        for row in local["matching_retained_performance_events"]]
    bind = [row for row in exact_events if row["request_id"] == "control-plane-file-read-bind-" + PREFIX]
    reads = [row for row in exact_events if row["request_id"] == "control-plane-file-read-read-" + PREFIX]
    if len(bind) != 1 or reads or not bind[0]["ok"]:
        raise RuntimeError("RETAINED_EXACT_BOOTSTRAP_TIMING_REQUIRED")
    start = epoch_ms(bind[0]["started_at"])
    finish = epoch_ms(bind[0]["finished_at"])
    ledger = ROOT / ".coding-tools/orchestration/ledger.sqlite3"
    connection = sqlite3.connect(ledger.as_uri() + "?mode=ro", uri=True, timeout=2)
    try:
        connection.execute("PRAGMA query_only=ON")
        connection.execute("BEGIN")
        event_count = connection.execute(
            "SELECT COUNT(*) FROM events WHERE event_time>=? AND event_time<=?", WINDOW
        ).fetchone()[0]
        rows = connection.execute(
            "SELECT seq,event_type,event_time,run_id,wave_id,state_before,state_after "
            "FROM events WHERE event_time>=? AND event_time<=? ORDER BY seq LIMIT 80", WINDOW
        ).fetchall()
        ledger_events = [dict(zip((
            "seq", "event_type", "event_time", "run_id", "wave_id", "state_before", "state_after"
        ), row)) for row in rows]
    finally:
        connection.rollback()
        connection.close()
    source_paths = (
        "electron/services/runtimeOrchestrator.js",
        "electron/services/recoveryHost.js",
        "electron/services/recoveryIpc.js",
        "electron/services/recoveryHostLauncher.js",
        "control-plane/control_plane/recovery_file_read_bridge.cjs",
        "control-plane/control_plane/node_agent.py",
        "resources/coding-tools-mcp/coding_tools_mcp/mcp_http_handler.py",
        "resources/coding-tools-mcp/coding_tools_mcp/server.py",
        "resources/coding-tools-mcp/coding_tools_mcp/workspace_context_registry.py",
        "resources/coding-tools-mcp/coding_tools_mcp/orchestration_ledger.py",
    )
    source_hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in source_paths}
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip()
    report = {
        "schema_version": 1,
        "operation": "local_original_read067_timing_audit",
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_head": head,
        "git_branch": branch,
        "source_worktree_hashes": source_hashes,
        "read_only_observation": True,
        "action_id": ACTION,
        "attempt_id": ATTEMPT,
        "evidence": {"readiness": readiness_evidence, "local_timeout": local_evidence,
                     "performance": performance_evidence},
        "performance_window_utc": WINDOW,
        "retained_performance_sample_size": len(performance.get("recent", [])),
        "window_sample_size": len(events),
        "window_events": events,
        "exact_original_events_from_preserved_observation": exact_events,
        "preserved_original_performance_evidence": local["performance_evidence"],
        "projection_limit": "Current recent-100 window can roll off; exact original timing is derived from the preserved local-timeout observation, not inferred from an absent live entry.",
        "measured": {
            "dispatch_at_ms": dispatch,
            "unknown_received_at_ms": unknown,
            "unknown_after_dispatch_ms": unknown - dispatch,
            "bind_tool_start_after_dispatch_ms": start - dispatch,
            "bind_tool_start_after_unknown_ms": start - unknown,
            "bind_tool_wall_duration_ms": finish - start,
            "bind_tool_reported_duration_ms": bind[0]["duration_ms"],
            "matching_retained_read_file_events": len(reads),
            "original_journal_was_unknown": local["journal_projection"]["state"] == "unknown",
        },
        "current_deadline_contract": {
            "local_mcp_each_request_socket_inactivity_ms": 8000,
            "local_mcp_sequential_phases": ["workspace_context", "read_file"],
            "local_mcp_shared_absolute_action_deadline": False,
            "recovery_ipc_read_only_default_socket_inactivity_ms": 15000,
            "file_read_bridge_timeout_override": False,
            "node_file_read_subprocess_default_seconds": 20,
            "actual_node_timeout_argument_observed": False,
        },
        "source_findings": [
            "Recovery IPC invokes each async handler directly; no generic IPC request queue lock was found.",
            "MCP uses ThreadingHTTPServer, with separate request threads; no global FIFO tool lock was found.",
            "Before dispatch_rpc, handle_rpc resolves workspace scope, reads request task state and touches the durable hub client.",
            "Tool performance start is recorded inside Runtime.call_tool, after those HTTP predispatch boundaries.",
            "Task-context registry and ledger use RLocks; registry persists the complete JSON with fsync while locked; ledger connections use SQLite busy_timeout=5000.",
            "A disconnected MCP client does not cancel the handler; later response writes suppress broken pipe.",
        ],
        "hypotheses_not_proven": [
            "The 22.759s dispatch-to-tool-entry gap includes node/Recovery preflight, HTTP scheduling and predispatch; request-arrival clocks do not identify which boundary dominated.",
            "Registry or ledger lock/I/O contention is plausible, but current timing and event projections do not prove the cause or duration.",
        ],
        "canonical_ledger_observation": {
            "read_only_uri": True,
            "query_only": True,
            "transaction_snapshot": True,
            "window_utc": WINDOW,
            "event_count": event_count,
            "allowlisted_events": ledger_events,
            "limit": "These are run lifecycle events, not request-arrival or lock-wait instrumentation; absence does not exclude contention.",
        },
        "recommendation": {
            "current_eight_second_budget": "One observed valid exact bootstrap entered after UNKNOWN; 8s is insufficient for this observed path.",
            "twenty_second_candidate": "20s remains below the observed 22.759s dispatch-to-tool-entry delay.",
            "thirty_second_candidate": "30s is an evidence-backed candidate with about 7s headroom for this one observed delayed bootstrap; it is not a reliability percentile or proven SLA.",
            "align_all_layers": "Prefer one bounded absolute budget for the bind+read operation and give IPC/subprocess additional bounded preflight/return margin. Raising only the inner timeout is clipped by current 15s IPC or configured subprocess budget.",
            "if_retaining_per_request_budgets": "Two sequential 30s requests need outer IPC/subprocess budgets above 60s plus bounded preflight and return margin; do not describe this as a 30s whole-action deadline.",
            "focused_validation": "After an authorized source/package revision, inject a 23s pre-tool delay, verify a single bind/read succeeds within the aligned budget, and verify expiration remains UNKNOWN with no redispatch or unsupported success reconciliation.",
            "current_original_action": "Preserve UNKNOWN and reconcile only the exact original action/attempt through supported authority; late bootstrap success cannot prove bounded file-read success.",
            "freeze": "No source or production changes made by this audit; root continues original rejection and the new canary independently.",
        },
        "source_modified": False,
        "runtime_modified": False,
        "journal_modified": False,
        "action_redispatched": False,
        "commit_push_release_deploy_service_operation_performed": False,
    }
    with output.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
    print(json.dumps({"report_path": str(output), "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                      "measured": report["measured"], "window_sample_size": len(events),
                      "canonical_ledger_event_count": event_count}))


if __name__ == "__main__":
    main()
