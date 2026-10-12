"""Same-window owner intake recovery only; default observe is read-only.

Reuse the frozen v3 definitions without main. No renew/grant/policy/context
operation, SQL writes, command replay, restart, deployment or RUN acceptance.
"""
from __future__ import annotations
import argparse
import base64
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import time

V3_SHA = "a312575854fee785158fa21624a096d7b09ae3701ded38f449a7330ba089ebec"
V3 = Path(__file__).with_name("ubuntu-r10-store-authority-v3-local-proof.py")
SERVICE_INSTANCE = "cp_6766892f5ada47d1862a0d24334f1116"
CONTEXT = "ctx_9e58c758a20249479b6ec806970f68ca"
PILOT = "pilot_25fa8c634f7f40e282c30a303b51bfd0"
REQUESTED = 1791722898491
EXPIRY = 1791726498491
FAILED_EPOCH = "activation-mv3tn5og-8def0602e3d318e0c42052c6eefc00ba"
COLD_ACTION = "act_9482be2aef814d82b3ff4722b5979a25"
COLD_TASK = "task_80e2fb1ba3e449edbfb05d5a53055642"
COLD_ATTEMPT = "try_78e2a7ebbe404afc8d432e5efa5f4152"
COLD_RESPONSE = "dd7a305f5be0ec9383bbf1119e655002345c6a2e685a544879b50b4679ee0b39"
COLD_RECEIPT = "2f6ea10d7542e11920707ef65682b12672019de1fa6686ac47361dbe2ae738b8"
COLD_CONTEXT = "ctx_72a70fa1bd40462fb13a4e08955ea466"
NATIVE_CONTRACT = "bc44c044a0b08dfdea80b8ba0dfcc080e180e21a5460dbf9726b49ac1fa769b0"

class Refused(Exception):
    def __init__(self, code): self.code = code

def need(value, code):
    if not value: raise Refused(code)

def definitions():
    raw = V3.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == V3_SHA, "FROZEN_V3_CHANGED")
    scope = {"__name__": "same_window_frozen_authority_definitions", "__file__": str(V3)}
    exec(compile(raw, str(V3), "exec"), scope)
    return scope

def rows(database, sql, params=()):
    with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True, timeout=5) as connection:
        connection.execute("PRAGMA query_only=ON")
        connection.row_factory = sqlite3.Row
        return [dict(row) for row in connection.execute(sql, params)]

def same_authority(g, health, snapshot, overview, grant):
    need(health["service_instance_id"] == SERVICE_INSTANCE, "SERVING_INSTANCE_CHANGED")
    need(snapshot["actions"] == 38 and snapshot["tasks"] == 10 and snapshot["acceptances"] == 1,
         "POST_COLD_COUNTS_CHANGED")
    need(snapshot["patch_acceptances_sha256"] == "52be68a0dac2b56af51271fb8278bae1b04187f4573266c0051beabbec349309",
         "PENDING_OR_SETTLED_PATCH_ACCEPTANCE_CHANGED")
    raw = g["protected_file"](g["MARKER"])
    marker = json.loads(raw)
    need(marker.get("operation") == "owner_approved_r10_store395_same_scope_60m_v3_local_proof"
        and marker.get("service_instance_id") == SERVICE_INSTANCE and marker.get("phase") == "intake_reopened"
        and marker.get("activation_epoch") == FAILED_EPOCH and marker.get("operator_approved") is True
        and marker.get("source_revision") == g["REVISION"] and marker.get("binding_id") == g["BINDING"]
        and marker.get("device_id") == g["DEVICE"] and marker.get("workspace_id") == g["WORKSPACE"]
        and marker.get("workspace_generation") == g["GENERATION"] and marker.get("reason") == g["REASON"],
        "ORIGINAL_AUTHORITY_MARKER_CHANGED")
    need(marker.get("context_id") == CONTEXT and marker.get("pilot_id") == PILOT
        and marker.get("requested_at_ms") == REQUESTED and marker.get("expires_at_ms") == EXPIRY
        and EXPIRY == REQUESTED + 3600000 and int(time.time() * 1000) < EXPIRY,
        "ORIGINAL_AUTHORITY_WINDOW_EXPIRED_OR_CHANGED")
    need(marker.get("service_grant_sha256") == g["digest"](grant), "ORIGINAL_SERVICE_GRANT_CHANGED")
    g["renewed_authority"](overview, marker)
    return marker, hashlib.sha256(raw).hexdigest()

def cold_guard(g, database):
    action = rows(database, "SELECT * FROM actions WHERE action_id=?", (COLD_ACTION,))
    task = rows(database, "SELECT * FROM mcp_task_sessions WHERE task_id=?", (COLD_TASK,))
    attempts = rows(database, "SELECT * FROM delivery_attempts WHERE action_id=?", (COLD_ACTION,))
    receipts = rows(database, "SELECT * FROM receipts WHERE action_id=? ORDER BY received_at_ms,receipt_id", (COLD_ACTION,))
    intent = rows(database, "SELECT * FROM mcp_exec_intents WHERE action_id=?", (COLD_ACTION,))
    writers = rows(database, "SELECT * FROM mcp_task_writer_leases WHERE task_id=?", (COLD_TASK,))
    context = rows(database, "SELECT * FROM contexts WHERE context_id=?", (COLD_CONTEXT,))
    need(len(action) == len(task) == len(attempts) == len(intent) == len(context) == 1 and receipts,
         "EXACT_COLD_FAMILY_REQUIRED")
    need(action[0]["binding_id"] == g["BINDING"] and action[0]["device_id"] == g["DEVICE"]
        and action[0]["workspace_id"] == g["WORKSPACE"] and action[0]["workspace_generation"] == g["GENERATION"]
        and action[0]["scoped_pilot_decision_id"] == PILOT and action[0]["context_id"] == COLD_CONTEXT
        and action[0]["delivery_state"] == "settled" and action[0]["settled_at_ms"] is not None,
        "COLD_ACTION_NOT_EXACT_SETTLED")
    need(intent[0]["task_id"] == COLD_TASK and intent[0]["binding_id"] == g["BINDING"]
        and intent[0]["principal_id"] == g["PRINCIPAL"] and attempts[0]["attempt_id"] == COLD_ATTEMPT,
        "COLD_INTENT_OR_ATTEMPT_CHANGED")
    receipt = receipts[-1]
    payload = json.loads(receipt["payload_json"])
    need(receipt["receipt_state"] == "completed" and receipt["receipt_digest"] == COLD_RECEIPT
        and payload.get("action_id") == COLD_ACTION and payload.get("task_id") == COLD_TASK
        and payload.get("response_sha256") == COLD_RESPONSE and payload.get("status") == "exited"
        and payload.get("exit_code") == 0 and payload.get("timed_out") is False,
        "COLD_SUCCESS_RECEIPT_CHANGED")
    need(task[0]["closed_at_ms"] is not None and context[0]["closed_at_ms"] is not None
        and writers and all(row["released_at_ms"] is not None for row in writers), "COLD_CLEANUP_INCOMPLETE")
    return g["digest"]({"action": action, "task": task, "attempts": attempts, "receipts": receipts,
                       "intent": intent, "writers": writers, "context": context})

def reopen_identity(g, overview, args):
    need(args.expected_activation_epoch and re.fullmatch(r"activation-[A-Za-z0-9_-]{8,128}", args.expected_activation_epoch)
        and args.expected_activation_epoch not in {FAILED_EPOCH, g["PREDECESSOR_EPOCH"]}, "NEW_RECOVERED_EPOCH_REQUIRED")
    need(args.expected_process_instance and re.fullmatch(r"[A-Za-z0-9_-]{8,128}", args.expected_process_instance)
        and args.expected_server_instance and re.fullmatch(r"[A-Za-z0-9_-]{8,128}", args.expected_server_instance)
        and args.expected_native_contract == NATIVE_CONTRACT, "EXACT_RECOVERED_NATIVE_IDENTITY_REQUIRED")
    nodes = [row for row in overview["nodes"] if row.get("device_id") == g["DEVICE"]]
    need(len(nodes) == 1, "NODE_NOT_UNIQUE")
    node = nodes[0]
    now = overview["observed_at_ms"]
    need(node.get("activation_epoch") == args.expected_activation_epoch
        and node.get("runtime_instance_id") == args.expected_process_instance
        and node.get("mcp_server_instance_id") == args.expected_server_instance
        and node.get("contract_version") == "sha256:" + NATIVE_CONTRACT
        and node.get("readiness") == "ready" and node.get("policy_state") == "enabled"
        and type(node.get("last_seen_at_ms")) is int and 0 <= now - node["last_seen_at_ms"] < 60000
        and type(node.get("policy_expires_at_ms")) is int and node["policy_expires_at_ms"] > now,
        "RECOVERED_NODE_NOT_EXACT_FRESH_READY")
    return node

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("observe", "close", "reopen"), nargs="?", default="observe")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--operator-approved", action="store_true")
    parser.add_argument("--expected-service-instance")
    parser.add_argument("--expected-state-sha256")
    parser.add_argument("--expected-authority-marker-sha256")
    parser.add_argument("--expected-activation-epoch")
    parser.add_argument("--expected-process-instance")
    parser.add_argument("--expected-server-instance")
    parser.add_argument("--expected-native-contract")
    args = parser.parse_args()
    g = definitions()
    origin, token, database, health, snapshot, overview, grant = g["inspect"]()
    marker, marker_sha = same_authority(g, health, snapshot, overview, grant)
    cold_sha = cold_guard(g, database)
    node = [row for row in overview["nodes"] if row.get("device_id") == g["DEVICE"]]
    if args.action == "observe" or not args.execute:
        g["emit"]("r10_same_window_intake_observation", ok=True, remote_mutation=False,
            observed_at_ms=overview["observed_at_ms"], service_instance_id=SERVICE_INSTANCE,
            source_revision=g["REVISION"], package_source_sha256=g["PACKAGE"], binding_id=g["BINDING"],
            admission=overview["admission"]["admission_mode"], state=snapshot, state_sha256=g["digest"](snapshot),
            authority_marker_sha256=marker_sha, cold_family_sha256=cold_sha, requested_at_ms=REQUESTED, expires_at_ms=EXPIRY,
            context_id=CONTEXT, pilot_id=PILOT, service_grant_preserved=g["GRANT"],
            node=None if len(node) != 1 else {key: node[0].get(key) for key in ("activation_epoch", "readiness", "policy_state",
                "last_seen_at_ms", "policy_expires_at_ms", "runtime_instance_id", "mcp_server_instance_id", "contract_version")})
        return
    # The supported recovery API revokes the live pilot. Same-ID close/reopen
    # cannot meet this packet's scope; refuse BEFORE calling any owner API.
    raise Refused("SAME_PILOT_RECOVERY_UNSUPPORTED_PREPARED_OBSERVE_ONLY")
    need(args.operator_approved and args.expected_service_instance == SERVICE_INSTANCE, "EXACT_OWNER_APPROVAL_REQUIRED")
    need(args.expected_state_sha256 == g["digest"](snapshot) and args.expected_authority_marker_sha256 == marker_sha,
         "EXACT_STATE_AND_ORIGINAL_MARKER_PINS_REQUIRED")
    lock = os.open(g["INSTALL"] / ".owner-acceptance-deployment.lock", os.O_CREAT | os.O_RDWR, 0o600)
    try:
        try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError: raise Refused("OWNER_OPERATION_ALREADY_RUNNING") from None
        need(g["state"](database) == snapshot and hashlib.sha256(g["protected_file"](g["MARKER"])).hexdigest() == marker_sha,
             "STATE_OR_AUTHORITY_CHANGED_BEFORE_OPERATION")
        current = g["api"](origin, token, "/v1/ui/overview")
        mode = current["admission"]["admission_mode"]
        need(mode in {"recovery", "scoped_pilot"}, "INTAKE_MODE_CHANGED")
        same_authority(g, health, snapshot, current, g["target"](current))
        target_mode = "recovery" if args.action == "close" else "scoped_pilot"
        if args.action == "reopen": reopen_identity(g, current, args)
        if mode != target_mode: g["api"](origin, token, "/v1/maintenance/admission", {"mode": target_mode})
        final_health = g["api"](origin, token, "/healthz")
        final_overview = g["api"](origin, token, "/v1/ui/overview")
        need(final_health["service_instance_id"] == SERVICE_INSTANCE and final_health["admission_mode"] == target_mode,
             "INTAKE_ACK_OR_SERVICE_CHANGED")
        same_authority(g, final_health, snapshot, final_overview, g["target"](final_overview))
        need(g["state"](database) == snapshot and cold_guard(g, database) == cold_sha
            and hashlib.sha256(g["protected_file"](g["MARKER"])).hexdigest() == marker_sha,
             "INTAKE_OPERATION_CHANGED_RETAINED_STATE")
        g["emit"]("r10_same_window_intake_closed" if args.action == "close" else "r10_same_window_intake_reopened",
            ok=True, remote_mutation=True, admission=target_mode, observed_at_ms=final_overview["observed_at_ms"],
            service_instance_id=SERVICE_INSTANCE, state=snapshot, state_sha256=g["digest"](snapshot),
            authority_marker_sha256=marker_sha, cold_family_sha256=cold_sha, binding_id=g["BINDING"],
            context_id=CONTEXT, pilot_id=PILOT, requested_at_ms=REQUESTED, expires_at_ms=EXPIRY,
            activation_epoch=args.expected_activation_epoch if args.action == "reopen" else None,
            authority_renewed=False, original_marker_modified=False, service_grant_changed=False,
            command_replayed=False, pending_acceptance_changed=False)
    finally:
        fcntl.flock(lock, fcntl.LOCK_UN)
        os.close(lock)

if __name__ == "__main__":
    try: main()
    except Exception as error:
        print(json.dumps({"phase":"r10_same_window_intake_refused", "ok":False,
            "code":getattr(error,"code","SAME_WINDOW_INTAKE_UNEXPECTED_FAILURE"),
            "no_automatic_retry":True, "keep_intake_closed_on_incomplete_recovery":True},separators=(",",":")),flush=True)
        raise SystemExit(2) from None
