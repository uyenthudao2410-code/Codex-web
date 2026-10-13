"""Prepare/append a rejected result for the exact timeout; never infer read success."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import time

sys.dont_write_bytecode = True
ACTION = "act_1de2cef3dc304d6e8b3f90237d7c136a"
ATTEMPT = "try_8d31c7cfb661441aadb9e620e47508a3"
RECEIPT = "rcpt_03cb8c766afb4a0ab6d5f9c53c75f317"
RECEIPT_DIGEST = "52de73f30a4dfb8a837dda517770173d49c9a121a93dc9c3ab4ba4ad6d4af724"
DEVICE = "4c4b7a5b-7744-49ae-a490-78a528a00471"
WORKSPACE = "workspace_f93b5bac9dc74fae9cea66f44c4ebc94"
GENERATION = "generation_a420c8bfcfcb4e42b5bb7fc5e5cec097"
SERVER_URL = "https://svhome.tail0e4032.ts.net"
EXPECTED_RUNTIME = {"runtime_instance_id": "r2fiLBRSmrFcAi4T", "mcp_server_instance_id": "3ps0AJwnJfhbwdYt",
    "activation_epoch": "activation-mv58t4he-c162dd8a1c513c77581c5adee2ae6762",
    "contract_version": "sha256:0e4733844a471814a3a6240fa9c0423b56195ab80f6e5283b5c978e28edaaed4"}


def require(condition, code):
    if not condition:
        raise RuntimeError(code)


def read(file):
    raw = file.read_bytes()
    require(len(raw) <= 2 * 1024 * 1024, "BOUNDED_RECONCILIATION_EVIDENCE_REQUIRED")
    return json.loads(raw.decode("utf-8-sig")), hashlib.sha256(raw).hexdigest()


def validate_server(server, now):
    require(server.get("ok") is True and server.get("service_stable") is True
            and server.get("source_startup_disk_attestation_matches") is True
            and server.get("sqlite_integrity_ok") is True
            and 0 <= now - server.get("capture_completed_at_ms", 0) <= 120000, "FRESH_EXACT_SERVER_READ067_EVIDENCE_REQUIRED")
    node = server.get("node", {})
    require(node.get("device_id") == DEVICE and node.get("readiness") == "ready"
            and node.get("revoked_at_ms") is None and node.get("heartbeat_fresh_60000_ms") is True
            and all(node.get(key) == value for key, value in EXPECTED_RUNTIME.items()), "EXACT_CURRENT_SERVER_NODE_REQUIRED")
    require(server.get("service_pid") == 970133 and server.get("tool_contract") == {
        "schema_version": 32, "profile": "control-plane-private-tunnel-service-v1",
        "sha256": "3664b70740d8d7359a3605b5ce42d7cbf3329e27dcfeec27d22b23ec9c631f66"}, "EXACT_SERVING_RUNTIME_REQUIRED")
    actions = [item for item in server.get("historical_unknown_actions_preserved", []) if item["action_id"] == ACTION]
    require(len(actions) == 1, "EXACT_ORIGINAL_UNKNOWN_ACTION_REQUIRED")
    action = actions[0]
    require(action["workspace_id"] == WORKSPACE and action["workspace_generation"] == GENERATION
            and action["tool_name"] == "workspace_context" and action["delivery_state"] == "reconcile_required"
            and action["settled_at_ms"] is None and action.get("disposition") is None
            and action["task_id"] == "task_cd3ea31140794fbcb5c598eb29cb9c90"
            and action["delivery_attempts"] == [{"attempt_id": ATTEMPT, "attempt_number": 1, "dispatched_at_ms": 1791810310801}],
            "ORIGINAL_ACTION_LINEAGE_CHANGED")
    receipts = action["receipts"]
    require(len(receipts) == 1 and receipts[0]["receipt_id"] == RECEIPT and receipts[0]["receipt_digest"] == RECEIPT_DIGEST
            and receipts[0]["receipt_state"] == "unknown" and receipts[0]["local_handle_sha256"] is None
            and receipts[0]["safe_diagnostics"] == {"code": "CONTROL_PLANE_FILE_READ_EFFECT_UNKNOWN",
                "diagnostic_code": "CONTROL_PLANE_FILE_READ_TIMEOUT", "operation_kind": "control_plane_bounded_file_read"},
            "ORIGINAL_UNKNOWN_RECEIPT_CHANGED")
    return receipts[0]


def validate_gate(gate, candidate, server_hash, local_hash, journal_hash, now):
    require(gate.get("ok") is True and gate.get("operation") == "original-read067-reconciliation-gate"
            and gate.get("candidate", "").lower() == str(candidate).lower()
            and 0 <= now - gate.get("observed_at_ms", 0) <= 60000, "FRESH_CONTROLLER_RECONCILIATION_GATE_REQUIRED")
    body = gate.get("receipt", {})
    require(body.get("action_id") == ACTION and body.get("attempt_id") == ATTEMPT
            and body.get("runtime_identity") == EXPECTED_RUNTIME
            and body.get("server_evidence_sha256") == server_hash and body.get("local_evidence_sha256") == local_hash
            and body.get("local_journal_sha256") == journal_hash
            and body.get("helper_sha256") == hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "EXACT_CONTROLLER_RECONCILIATION_BINDING_REQUIRED")
    census = body.get("census", {})
    lifecycle = census.get("lifecycle", {})
    require(census.get("content_free") is True and census.get("mutated_canonical_ledger") is False
            and isinstance(lifecycle.get("blockers"), list)
            and all(item == "live_runtime_state_process" for item in lifecycle["blockers"])
            and lifecycle.get("unexplained_active_runs") == 0 and lifecycle.get("unbound_live_resource_residues") == 0
            and all(census.get("counts", {}).get(key) == 0 for key in (
                "active_tool_calls", "active_commands", "starting_commands", "active_background_operations",
                "active_managed_processes", "foreign_heavy_processes", "active_agent_lanes", "owned_codex_sidecar_residues")),
            "CANONICAL_NO_ACTIVE_WORK_CENSUS_REQUIRED")
    for name, expected in body.get("package_sha256", {}).items():
        require(name in {"Coding Tools MCP.exe", "resources/app.asar", "resources/resources/control-plane/node_agent.py"}
                and hashlib.sha256((candidate / name).read_bytes()).hexdigest() == expected, "EXACT_CONTROLLER_PACKAGE_REQUIRED")
    require(set(body.get("package_sha256", {})) == {
        "Coding Tools MCP.exe", "resources/app.asar", "resources/resources/control-plane/node_agent.py"},
        "COMPLETE_CONTROLLER_PACKAGE_PROOF_REQUIRED")


def prepare(server, local, journal, now):
    central = validate_server(server, now)
    entry = journal.get("entries", {}).get(ACTION + "|" + ATTEMPT)
    require(isinstance(entry, dict) and entry["action_id"] == ACTION and entry["attempt_id"] == ATTEMPT and entry["state"] == "unknown",
            "EXACT_ORIGINAL_LOCAL_UNKNOWN_REQUIRED")
    receipt = entry["receipt"]
    require(receipt["receipt_state"] == "unknown" and receipt["receipt_submitted"] is True and receipt["local_handle"] == ""
            and receipt["payload"] == {"schema_version": 1, "operation_kind": "control_plane_bounded_file_read",
                "code": "CONTROL_PLANE_FILE_READ_EFFECT_UNKNOWN", "diagnostic_code": "CONTROL_PLANE_FILE_READ_TIMEOUT"},
            "EXACT_ORIGINAL_LOCAL_RECEIPT_REQUIRED")
    payload_hash = hashlib.sha256(json.dumps(receipt["payload"], separators=(",", ":"), sort_keys=True).encode()).hexdigest()
    require(payload_hash == central["payload_sha256"] and local.get("ok") is True and local["action_id"] == ACTION
            and local["attempt_id"] == ATTEMPT and local.get("read_only") is True
            and local.get("journal_modified") is False and local.get("action_redispatched") is False,
            "EXACT_LOCAL_AND_CENTRAL_TIMEOUT_EVIDENCE_REQUIRED")
    return {"schema_version": 1, "operation_kind": "control_plane_bounded_file_read",
        "code": "FILE_READ_RESULT_REJECTED_OPERATOR_RECONCILIATION", "diagnostic_code": "CONTROL_PLANE_FILE_READ_TIMEOUT",
        "original_unknown_receipt_preserved": True, "original_unknown_receipt_id": RECEIPT,
        "original_unknown_receipt_digest": RECEIPT_DIGEST, "read_may_have_occurred": True,
        "valid_bounded_read_receipt_retained": False, "read_success_claimed": False,
        "action_redispatched": False, "reconciliation_required": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--server-readiness", type=Path, required=True)
    parser.add_argument("--local-evidence", type=Path, required=True)
    parser.add_argument("--controller-gate", type=Path, required=True)
    parser.add_argument("--confirm-rejected-result", action="store_true")
    args = parser.parse_args()
    server, server_hash = read(args.server_readiness)
    local, local_hash = read(args.local_evidence)
    profile = Path(os.environ["APPDATA"]) / "web-mcp-assistant"
    journal_path = profile / "control-plane-node.json.file-read-bridge-journal.json"
    journal, journal_hash = read(journal_path)
    gate, gate_hash = read(args.controller_gate)
    validate_gate(gate, args.candidate, server_hash, local_hash, journal_hash, int(time.time() * 1000))
    payload = prepare(server, local, journal, int(time.time() * 1000))
    payload.update(original_local_journal_sha256=journal_hash, local_evidence_sha256=local_hash, server_evidence_sha256=server_hash)
    result = {"operation": "original_read067_rejected_result_reconciliation", "ok": True,
        "action_id": ACTION, "attempt_id": ATTEMPT, "payload": payload, "node_journal_modified": False,
        "controller_gate_sha256": gate_hash,
        "mode": "append_rejected_result" if args.confirm_rejected_result else "preflight_only"}
    adapter = args.candidate / "resources/resources/control-plane/node_agent.py"
    spec = importlib.util.spec_from_file_location("exact_packaged_node_agent", adapter)
    require(spec is not None and spec.loader is not None, "EXACT_PACKAGED_NODE_AGENT_REQUIRED")
    agent = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(agent)
    observer_args = argparse.Namespace(runtime_mode="packaged", data_root="", project_root=str(args.candidate),
        node=str(args.candidate / "Coding Tools MCP.exe"), timeout_seconds=20)
    identity = agent.observed_runtime_identity(agent.recovery_identity_observation(observer_args, args.candidate))
    require(identity == EXPECTED_RUNTIME and agent.recovery_runtime_status(observer_args, args.candidate).get("strict_ready") == "true",
            "EXACT_CURRENT_READY_RUNTIME_REQUIRED")
    if args.confirm_rejected_result:
        require(gate["receipt"].get("append_authorized") is True, "CONTROLLER_APPEND_AUTHORIZATION_REQUIRED")
        config_path = profile / "control-plane-node.json"
        protected_config, _ = read(config_path)
        require(protected_config.get("device_id") == DEVICE and protected_config.get("server_url") == SERVER_URL
                and str(protected_config.get("node_secret_dpapi", "")).startswith("dpapi-v1:")
                and protected_config.get("node_secret") in (None, "")
                and protected_config.get("node_secret_pending") in (None, ""), "EXACT_PROTECTED_NODE_CONFIG_REQUIRED")
        config = agent._config(config_path)
        require(config["device_id"] == DEVICE and config["server_url"] == SERVER_URL, "EXACT_LOCAL_NODE_REQUIRED")
        # Recheck bounded evidence after the read-only live identity observations.
        validate_gate(gate, args.candidate, server_hash, local_hash, journal_hash, int(time.time() * 1000))
        validate_server(server, int(time.time() * 1000))
        require(hashlib.sha256(journal_path.read_bytes()).hexdigest() == journal_hash, "ORIGINAL_LOCAL_JOURNAL_CHANGED")
        response = agent._request(config["server_url"], f"/v1/nodes/{DEVICE}/receipts",
            {"action_id": ACTION, "attempt_id": ATTEMPT, "receipt_state": "rejected", "local_handle": "", "payload": payload},
            "Node " + config["node_secret"])
        require(response["action_id"] == ACTION and response["attempt_id"] == ATTEMPT and response["receipt_state"] == "rejected"
                and response["delivery_state"] == "settled", "EXACT_ORIGINAL_REJECTED_RECEIPT_REQUIRED")
        result["server_receipt"] = response
        require(hashlib.sha256(journal_path.read_bytes()).hexdigest() == journal_hash, "ORIGINAL_LOCAL_JOURNAL_CHANGED")
    print(json.dumps(result))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        code = str(error) if isinstance(error, RuntimeError) and re.fullmatch(r"[A-Z0-9_]{3,100}", str(error)) else type(error).__name__
        print(json.dumps({"operation": "original_read067_rejected_result_reconciliation", "ok": False, "error_code": code,
                          "next_action": "Observe exact original action and receipt; do not replay or fabricate a successful read."}))
        sys.exit(1)
