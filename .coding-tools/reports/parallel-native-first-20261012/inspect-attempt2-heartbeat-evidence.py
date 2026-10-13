"""Bounded credential-free attempt2 heartbeat and historical UNKNOWN evidence."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PROFILE = Path(os.environ["APPDATA"]) / "web-mcp-assistant"


def read(file):
    raw = file.read_bytes()
    return json.loads(raw.decode("utf-8-sig")), hashlib.sha256(raw).hexdigest()


def pick(value, names):
    return {key: value.get(key) for key in names}


def main():
    before, before_hash = read(HERE / "server-readiness-full-canary-r3-attempt2.json")
    after, after_hash = read(HERE / "server-readiness-full-canary-r3-attempt2-failed.json")
    status, status_hash = read(PROFILE / "control-plane-connected-agent-status.json")
    supervisor, supervisor_hash = read(PROFILE / "recovery-supervisor-status.json")
    lock, lock_hash = read(PROFILE / "control-plane-node.json.connected-agent.lock")
    canary = HERE / "canary/shared-mcp-receipt-bf3876b82a8a4eafbc83fec7c6e9b244.ndjson"
    rows = [json.loads(line) for line in canary.read_text(encoding="utf-8-sig").splitlines()]
    final = next(row for row in reversed(rows) if row.get("phase") == "final")
    old_ids = {item["action_id"] for item in before["historical_unknown_actions_preserved"]}
    new_ids = {item["action_id"] for item in after["historical_unknown_actions_preserved"]}
    source = ROOT / "control-plane/control_plane/node_agent.py"
    report = {"schema_version": 1, "operation": "attempt2_heartbeat_policy_lock_audit", "read_only": True,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "observed_git_head": "7999c4151cb501db86f2e4d0a2275d33fc248324",
        "canary_attempt_id": final["attempt_id"], "canary_final": pick(final, (
            "observed_at_ms", "ok", "error_code", "proof_counts", "unresolved_original_actions",
            "requires_reconciliation", "task_closed_verified", "writer_released_verified", "elapsed_seconds")),
        "central_failure_snapshot_at_ms": after["capture_completed_at_ms"],
        "central_node_at_failure": pick(after["node"], (
            "last_seen_at_ms", "policy_expires_at_ms", "heartbeat_age_ms", "heartbeat_fresh_60000_ms",
            "runtime_instance_id", "mcp_server_instance_id", "activation_epoch", "readiness")),
        "last_heartbeat_age_at_canary_failure_ms": final["observed_at_ms"] - after["node"]["last_seen_at_ms"],
        "policy_expired_before_canary_failure_ms": final["observed_at_ms"] - after["node"]["policy_expires_at_ms"],
        "local_worker_observation": status,
        "local_supervisor_observation": pick(supervisor, (
            "state", "control_plane_agent_state", "control_plane_agent_pid", "control_plane_agent_last_started_at",
            "control_plane_agent_last_error_code", "last_check_at")),
        "worker_lock_pid_matches_observed_supervisor_and_status": lock["pid"] == status["agent_pid"] == supervisor["control_plane_agent_pid"],
        "new_unknown_action_ids_since_attempt2_preflight": sorted(new_ids - old_ids),
        "retained_unknowns": [pick(item, (
            "action_id", "workspace_id", "workspace_generation", "created_at_ms", "disposition", "task_id"))
            | {"diagnostics": [receipt["safe_diagnostics"]["diagnostic_code"] for receipt in item["receipts"]]}
            for item in after["historical_unknown_actions_preserved"]],
        "evidence_sha256": {"before_server": before_hash, "after_server": after_hash,
            "local_worker_status": status_hash, "local_supervisor_status": supervisor_hash, "local_worker_lock": lock_hash,
            "canary_ndjson": hashlib.sha256(canary.read_bytes()).hexdigest(),
            "current_working_tree_node_agent": hashlib.sha256(source.read_bytes()).hexdigest()},
        "source_failure_path": "A typed busy poll escapes a successful-heartbeat iteration; shared failures then delay all heartbeat work up to300s",
        "source_fix": "Skip only exact typed busy lane; preserve successful-heartbeat interval on other capability failure; retain heartbeat transport backoff",
        "proof_limit": "The prior per-iteration error is not retained by the overwritten diagnostic status. Canonical stale heartbeat and unchanged worker identity plus reproduced source path support the scheduling diagnosis; exact historical busy reason remains inferred.",
        "production_mutation_performed": False, "historical_receipts_modified": False}
    output = HERE / "attempt2-heartbeat-policy-audit.json"
    with output.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
    print(json.dumps({"report_path": str(output), "new_unknown_action_ids": report["new_unknown_action_ids_since_attempt2_preflight"],
        "heartbeat_age_at_failure_ms": report["last_heartbeat_age_at_canary_failure_ms"],
        "worker_pid": status["agent_pid"], "current_worker_iteration_state": status["last_iteration_state"]}))


if __name__ == "__main__":
    main()
