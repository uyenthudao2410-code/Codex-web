"""One cold, one warm, one recreated-VM shared MCP node version proof.

Prepare-only until the root controller authorizes a stage with fresh r6 identity.
Durable task/intent idempotency is the source of original handles. Observation
never replays an action. Warm can keep renewing the exact writer while root
performs the supported owned VM stop; after_stop requires root's stop proof.
Credentials and raw failure/output payloads are never printed.
"""
import argparse
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
import subprocess
import sys
import time
import urllib.error
import urllib.request

DEVICE = "4c4b7a5b-7744-49ae-a490-78a528a00471"
WORKSPACE = "workspace_f93b5bac9dc74fae9cea66f44c4ebc94"
PRINCIPAL = "svcprn_cd98750c7c7e45678d201066dc1b7d7a"
GRANT = "mcpsvcgrant_bf8c94291a1b448abcfdaaba5531a5bd"
PROTOCOL = "2026-07-28"
OBSERVE_SECONDS = 900
STAGES = ("cold", "warm", "after_stop")
ARGV = ["node", "--version"]
PHASE = "preflight"

# BEGIN_REVIEWED_R2_UTILITIES
# Direct unchanged copies from verified R2 helper SHA256 a0aa5b81df0c54b66c17cce0647121585ef297b7d16039f7a59ac90e555148f8.

def require(condition, code):
    if not condition:
        raise RuntimeError(code)


def error_code(error):
    # RuntimeError messages below are fixed codes, never external payloads.
    if isinstance(error, RuntimeError):
        return str(error)
    if isinstance(error, urllib.error.HTTPError):
        return "HTTP_" + str(error.code)
    return type(error).__name__


class Mcp:
    def __init__(self, port, token):
        self.url = f"http://127.0.0.1:{port}/mcp"
        self.token = token
        self.counter = 0

    def call(self, name, arguments):
        self.counter += 1
        body = {"jsonrpc": "2.0", "id": self.counter, "method": "tools/call",
                "params": {"name": name, "arguments": arguments,
                           "_meta": {"io.modelcontextprotocol/protocolVersion": PROTOCOL,
                                     "io.modelcontextprotocol/clientCapabilities": {}}}}
        request = urllib.request.Request(
            self.url, data=json.dumps(body, separators=(",", ":")).encode(),
            headers={"Authorization": "Bearer " + self.token,
                     "Content-Type": "application/json", "Accept": "application/json",
                     "MCP-Protocol-Version": PROTOCOL, "Mcp-Method": "tools/call",
                     "Mcp-Name": name}, method="POST")
        with urllib.request.urlopen(request, timeout=15) as response:
            raw = response.read(196609)
            require(len(raw) <= 196608, "MCP_RESPONSE_TOO_LARGE")
            result = json.loads(raw)
        require(result.get("id") == self.counter and "error" not in result,
                "MCP_RPC_ERROR")
        tool_result = result.get("result", {})
        if tool_result.get("isError") is True:
            safe_code = tool_result.get("structuredContent", {}).get("code")
            raise RuntimeError("MCP_TOOL_ERROR_" + safe_code if isinstance(safe_code, str)
                               and re.fullmatch(r"[A-Z][A-Z0-9_]{2,95}", safe_code)
                               else "MCP_TOOL_ERROR")
        observation = tool_result.get("structuredContent")
        require(isinstance(observation, dict), "MCP_STRUCTURED_RESULT_MISSING")
        return observation


def service_state():
    pid = int(subprocess.check_output(
        ["systemctl", "--user", "show", "codex-control-plane.service",
         "--property=MainPID", "--value"], text=True).strip())
    require(pid > 1, "CONTROL_PLANE_SERVICE_NOT_RUNNING")
    environment = dict(item.split("=", 1) for item in
                       Path(f"/proc/{pid}/environ").read_text().split("\0") if "=" in item)
    require(environment.get("CONTROL_PLANE_MCP_AUTH_MODE") == "private_tunnel_service"
            and environment.get("CONTROL_PLANE_MCP_SERVICE_PRINCIPAL_ID") == PRINCIPAL
            and environment.get("CONTROL_PLANE_MCP_SERVICE_GRANT_ID") == GRANT,
            "CANONICAL_SERVICE_AUTHORITY_CHANGED")
    require(environment.get("CONTROL_PLANE_MCP_BIND", "127.0.0.1") == "127.0.0.1",
            "MCP_LISTENER_NOT_LOOPBACK")
    port = int(environment.get("CONTROL_PLANE_MCP_PORT", "8766"))
    require(1024 <= port <= 65535, "MCP_PORT_INVALID")
    database = Path(environment["CONTROL_PLANE_DB"])
    if not database.is_absolute():
        database = Path(f"/proc/{pid}/cwd").resolve() / database
    connection = sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)
    connection.execute("PRAGMA query_only=ON")
    connection.row_factory = sqlite3.Row
    return pid, port, connection


def existing_credential(args, connection):
    path = Path(args.credential_file)
    require(path.is_absolute(), "CREDENTIAL_PATH_NOT_ABSOLUTE")
    info = path.lstat()
    require(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid()
            and info.st_mode & 0o077 == 0 and info.st_size <= 65536,
            "CREDENTIAL_FILE_NOT_PROTECTED")
    raw = path.read_text()
    token = json.loads(raw).get(args.credential_json_key) if args.credential_json_key else raw.strip()
    if isinstance(token, str) and token.startswith("Bearer "):
        token = token[len("Bearer "):]
    require(isinstance(token, str) and re.fullmatch(r"mcpsvc_[A-Za-z0-9_-]{32,128}", token),
            "SERVICE_CREDENTIAL_FORMAT_INVALID")
    digest = hashlib.sha256(b"coding-tools-control-plane:mcp-service-grant:v1\0"
                            + token.encode()).hexdigest()
    grant = connection.execute(
        "SELECT grant_id,owner_id,principal_id,token_digest,scopes_json,expires_at_ms,revoked_at_ms "
        "FROM mcp_service_grants WHERE grant_id=?", (GRANT,)).fetchone()
    require(grant is not None and grant["owner_id"] == "owner_default"
            and grant["principal_id"] == PRINCIPAL and grant["revoked_at_ms"] is None
            and grant["expires_at_ms"] > int(time.time() * 1000) + OBSERVE_SECONDS * 1000
            and {"control-plane.inventory", "control-plane.read", "control-plane.patch"} <= set(json.loads(grant["scopes_json"]))
            and hmac.compare_digest(grant["token_digest"], digest),
            "CREDENTIAL_NOT_EXACT_LIVE_CANONICAL_GRANT")
    return token


def check_target(args, connection, client, task_id=None):
    now = int(time.time() * 1000)
    pilot = connection.execute(
        "SELECT * FROM scoped_pilot_decisions WHERE revoked_at_ms IS NULL AND expires_at_ms>?",
        (now,)).fetchall()
    require(len(pilot) == 1 and pilot[0]["decision_id"] == args.pilot_decision_id
            and pilot[0]["principal_id"] == PRINCIPAL and pilot[0]["binding_id"] == args.binding_id
            and pilot[0]["device_id"] == DEVICE and pilot[0]["workspace_id"] == WORKSPACE
            and pilot[0]["workspace_generation"] == args.new_generation
            and pilot[0]["expires_at_ms"] > now + OBSERVE_SECONDS * 1000,
            "EXACT_CURRENT_PILOT_NOT_READY")
    mode = connection.execute(
        "SELECT state_value FROM control_plane_state WHERE state_key='admission_mode'").fetchone()
    require(mode is not None and mode[0] == "scoped_pilot", "ADMISSION_NOT_SCOPED_PILOT")
    node = connection.execute(
        "SELECT readiness,runtime_instance_id,mcp_server_instance_id,activation_epoch,last_seen_at_ms "
        "FROM nodes WHERE device_id=? AND revoked_at_ms IS NULL", (DEVICE,)).fetchone()
    require(node is not None and node["readiness"] == "ready"
            and node["runtime_instance_id"] == args.process_instance_id
            and node["mcp_server_instance_id"] == args.server_instance_id
            and node["activation_epoch"] == args.activation_epoch
            and now - node["last_seen_at_ms"] <= 90000,
            "PACKAGED_READY_IDENTITY_NOT_CURRENT")
    inventory = client.call("workspace_context", {"operation": "inventory"})
    require(inventory.get("principal_id") == PRINCIPAL and len(inventory.get("targets", [])) == 1,
            "SHARED_MCP_INVENTORY_NOT_EXACT")
    target = inventory["targets"][0]
    require(target.get("binding_id") == args.binding_id and target.get("device_id") == DEVICE
            and target.get("workspace_id") == WORKSPACE
            and target.get("workspace_generation") == args.new_generation
            and target.get("readiness") == "ready" and target.get("presence_state") == "online"
            and target.get("dispatch_state") == "dispatchable"
            and all(target.get("capabilities", {}).get(lane) is True for lane in ("read", "write", "exec")),
            "SHARED_MCP_TARGET_NOT_READY")
    contract = inventory.get("tool_contract", {})
    require(set(contract) == {"schema_version", "profile", "sha256"}
            and contract["schema_version"] == args.facade_schema_version
            and contract["profile"] == "control-plane-private-tunnel-service-v1"
            and contract["sha256"] == args.facade_contract_sha256,
            "SHARED_FACADE_CONTRACT_UNEXPECTED")
    if task_id is not None:
        task = connection.execute("SELECT * FROM mcp_task_sessions WHERE task_id=?", (task_id,)).fetchone()
        require(task is not None and task["principal_id"] == PRINCIPAL
                and task["binding_id"] == args.binding_id and task["workspace_generation"] == args.new_generation
                and task["scoped_pilot_decision_id"] == args.pilot_decision_id
                and task["closed_at_ms"] is None, "TASK_TARGET_CHANGED")
    return contract


def renew(client, task_id, lease_generation):
    lease = client.call("task_control", {"operation": "writer_claim", "task_id": task_id}).get("writer_lease", {})
    require(lease.get("state") == "held" and lease.get("task_id") == task_id
            and lease.get("lease_generation") == lease_generation,
            "ORIGINAL_WRITER_LEASE_GENERATION_CHANGED")


def verified_receipt(connection, result, relay_key, args, contract, task_id, lease_generation, actor, kind):
    action_id = result["action"]["action_id"]
    relay = result.get(relay_key, {})
    receipt_id = relay.get("receipt_id")
    row = connection.execute(
        "SELECT receipt_state,payload_json FROM receipts WHERE receipt_id=? AND action_id=?",
        (receipt_id, action_id)).fetchone()
    require(row is not None and row["receipt_state"] == "completed", "VERIFIED_RECEIPT_NOT_FOUND")
    payload = json.loads(row["payload_json"])
    runtime = {"activation_epoch_id": args.activation_epoch,
               "process_instance_id": args.process_instance_id,
               "server_instance_id": args.server_instance_id,
               "tool_contract_sha256": args.local_tool_contract_sha256}
    require(payload.get("runtime_identity") == runtime and payload.get("facade_contract") == contract
            and payload.get("actor") == {"client_id": actor, "client_type": "electron"}
            and payload.get("operation_kind") == kind
            and payload.get("response_sha256") == relay.get("response_sha256"),
            "RECEIPT_IDENTITY_NOT_EXACT")
    if kind != "control_plane_bounded_file_read":
        require(payload.get("task_id") == task_id
                and payload.get("writer_lease_generation") == lease_generation,
                "RECEIPT_TASK_OR_LEASE_CHANGED")
    attempts = connection.execute(
        "SELECT attempt_id,attempt_number FROM delivery_attempts WHERE action_id=? ORDER BY attempt_number",
        (action_id,)).fetchall()
    require(len(attempts) == 1 and attempts[0]["attempt_number"] == 1,
            "ORIGINAL_ACTION_HAS_UNEXPECTED_DELIVERY_ATTEMPTS")
    return payload, {"receipt_id": receipt_id, "action_id": action_id,
                     "attempt_id": attempts[0]["attempt_id"], "attempt_number": 1,
                     "response_sha256": payload["response_sha256"], "runtime_identity": runtime}


def service_state_pid():
    return int(subprocess.check_output(
        ["systemctl", "--user", "show", "codex-control-plane.service", "--property=MainPID", "--value"],
        text=True).strip())
# END_REVIEWED_R2_UTILITIES


def emit(phase, **fields):
    print(json.dumps({"operation": "r6_three_stage_shared_exec_canary", "phase": phase,
                      "observed_at_ms": int(time.time() * 1000), **fields}, separators=(",", ":")), flush=True)


def handles(connection, prefix):
    task = connection.execute("SELECT task_id FROM mcp_task_open_idempotency WHERE principal_id=? AND idempotency_key=?", (PRINCIPAL, prefix + ":task")).fetchone()
    actions = {}
    for lane in STAGES:
        action = connection.execute("SELECT action_id FROM mcp_exec_intents WHERE principal_id=? AND idempotency_key=?", (PRINCIPAL, prefix + ":" + lane)).fetchone()
        if action:
            actions[lane] = action["action_id"]
    return task["task_id"] if task else None, actions


def census(connection, args):
    return {
        "open_tasks": connection.execute("SELECT COUNT(*) FROM mcp_task_sessions WHERE workspace_generation=? AND closed_at_ms IS NULL", (args.new_generation,)).fetchone()[0],
        "unreleased_writers": connection.execute("SELECT COUNT(*) FROM mcp_task_writer_leases l JOIN mcp_task_sessions t ON t.task_id=l.task_id WHERE t.workspace_generation=? AND l.released_at_ms IS NULL", (args.new_generation,)).fetchone()[0],
        "unsettled_actions": connection.execute("SELECT COUNT(*) FROM actions WHERE workspace_generation=? AND settled_at_ms IS NULL", (args.new_generation,)).fetchone()[0],
    }


def lease_identity(connection, task_id, *, live=False):
    row = connection.execute("SELECT lease_generation,binding_id,expires_at_ms,released_at_ms FROM mcp_task_writer_leases WHERE task_id=? ORDER BY lease_generation DESC LIMIT 1", (task_id,)).fetchone()
    require(row is not None and row["released_at_ms"] is None, "ORIGINAL_WRITER_LEASE_NOT_HELD")
    if live:
        require(row["expires_at_ms"] > int(time.time() * 1000), "ORIGINAL_WRITER_LEASE_EXPIRED_HOLD_REQUIRED")
    return row["lease_generation"]


def observe(client, connection, args, contract, task_id, lease_generation, lane, action_id):
    deadline = time.monotonic() + OBSERVE_SECONDS
    report_at = renew_at = 0
    while True:
        require(service_state_pid() == args.service_pid, "REVIEWED_SERVICE_PROCESS_CHANGED")
        if time.monotonic() - renew_at >= 20 and not args.observe_only:
            require(check_target(args, connection, client, task_id) == contract, "STAGE_AUTHORITY_CHANGED")
            renew(client, task_id, lease_generation)
            renew_at = time.monotonic()
        result = client.call("exec_command", {"operation": "exec_status", "action_id": action_id})
        action = result.get("action", {})
        require(action.get("action_id") == action_id, "ORIGINAL_OBSERVED_ACTION_CHANGED")
        if action.get("settled_at_ms") is not None or result.get("reconciliation_required") is True:
            return result
        if time.monotonic() - report_at >= 45:
            emit("observing_original_job", lane=lane, task_id=task_id, action_id=action_id,
                 central_lifecycle_state=action.get("central_lifecycle_state"))
            report_at = time.monotonic()
        if time.monotonic() >= deadline:
            emit("original_job_observation_timeout", lane=lane, task_id=task_id, action_id=action_id,
                 next_action="Observe or stop this original action; never enqueue a replacement")
            raise RuntimeError("ORIGINAL_JOB_OBSERVATION_TIMEOUT_NO_REPLACEMENT")
        time.sleep(5)


def verified_version(connection, client, args, contract, task_id, lease_generation, lane, action_id):
    result = client.call("exec_command", {"operation": "exec_status", "action_id": action_id})
    require(result.get("execution") == "completed_exec_relay" and result.get("process_state") == "completed"
            and result.get("exit_code") == 0 and result.get("reconciliation_required") is not True,
            "ORIGINAL_JOB_NOT_SUCCESSFUL")
    payload, proof = verified_receipt(connection, result, "exec", args, contract, task_id, lease_generation,
                                      "electron-control-plane-exec-bridge", "control_plane_exec")
    stdout = payload.get("stdout", "")
    version = stdout.strip() if isinstance(stdout, str) else ""
    require(re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+", version) is not None
            and stdout in {version, version + "\n", version + "\r\n"}
            and payload.get("stderr", "") == "" and payload.get("exit_code") == 0
            and payload.get("timed_out") is False and payload.get("truncated") is False,
            "EXACT_NODE_VERSION_OUTPUT_NOT_VERIFIED")
    intent = connection.execute("SELECT argv_json,task_id,writer_lease_generation FROM mcp_exec_intents WHERE action_id=?", (action_id,)).fetchone()
    require(intent is not None and json.loads(intent["argv_json"]) == {"argv": ARGV}
            and intent["task_id"] == task_id and intent["writer_lease_generation"] == lease_generation,
            "ORIGINAL_STRUCTURED_NODE_VERSION_INTENT_CHANGED")
    require(payload.get("action_id") == action_id and payload.get("attempt_id") == proof["attempt_id"]
            and payload.get("job_id") and payload.get("command_id"), "ORIGINAL_NATIVE_JOB_LINEAGE_CHANGED")
    receipt_count = connection.execute("SELECT COUNT(*) FROM receipts WHERE action_id=?", (action_id,)).fetchone()[0]
    require(receipt_count == 1, "ORIGINAL_ACTION_HAS_UNEXPECTED_RECEIPTS")
    proof.update({"lane": lane, "version": version, "exit_code": 0,
                  "job_id": payload["job_id"], "command_id": payload["command_id"],
                  "output_sha256": hashlib.sha256(stdout.encode()).hexdigest()})
    return proof


def close_exact_task(connection, client, args, prefix, task_id):
    known_task, actions = handles(connection, prefix)
    require(known_task == task_id, "ORIGINAL_TASK_HANDLE_CHANGED")
    require(census(connection, args)["unsettled_actions"] == 0, "CLEANUP_DEFERRED_UNSETTLED_ORIGINAL_ACTION")
    for action_id in actions.values():
        row = connection.execute("SELECT delivery_state,settled_at_ms FROM actions WHERE action_id=?", (action_id,)).fetchone()
        require(row and row["delivery_state"] == "settled" and row["settled_at_ms"] is not None,
                "CLEANUP_DEFERRED_UNSETTLED_ORIGINAL_ACTION")
    client.call("task_control", {"operation": "writer_release", "task_id": task_id,
                                "reason": "r6_three_stage_node_version_canary_finished"})
    client.call("workspace_context", {"operation": "task_close", "task_id": task_id})
    require(census(connection, args) == {"open_tasks": 0, "unreleased_writers": 0, "unsettled_actions": 0},
            "EXACT_CANARY_TASK_CLEANUP_NOT_VERIFIED")
    emit("exact_task_closed", task_id=task_id, actions=actions, current_generation_census=census(connection, args))


def main():
    global PHASE
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ("binding-id", "new-generation", "pilot-decision-id", "activation-epoch",
                  "process-instance-id", "server-instance-id", "local-tool-contract-sha256",
                  "facade-contract-sha256", "canary-id", "credential-file"):
        parser.add_argument("--" + field, required=True)
    parser.add_argument("--facade-schema-version", type=int, required=True)
    parser.add_argument("--service-pid", type=int, required=True)
    parser.add_argument("--stage", choices=(*STAGES, "close"), required=True)
    parser.add_argument("--execute-confirmed-ready-pilot", action="store_true")
    parser.add_argument("--observe-only", action="store_true")
    parser.add_argument("--hold-after-warm-seconds", type=int, default=180)
    parser.add_argument("--confirmed-supported-owned-sandbox-stop", action="store_true")
    parser.add_argument("--stopped-sandbox-id")
    parser.add_argument("--supported-stop-receipt-sha256")
    args = parser.parse_args()
    args.credential_json_key = None
    require(re.fullmatch(r"[a-f0-9]{32}", args.canary_id), "CANARY_ID_INVALID")
    require(args.new_generation == "generation_a420c8bfcfcb4e42b5bb7fc5e5cec097"
            and args.binding_id == "bind_71661b1046884174b01c99af5f8546aa"
            and args.pilot_decision_id == "pilot_dfb3174078d842299c41c6638830e505", "AUTHORIZED_MACHINE_PILOT_CHANGED")
    require(args.facade_schema_version == 32 and args.facade_contract_sha256 == "3664b70740d8d7359a3605b5ce42d7cbf3329e27dcfeec27d22b23ec9c631f66"
            and re.fullmatch(r"[a-f0-9]{64}", args.local_tool_contract_sha256), "EXACT_REVIEWED_CONTRACT_REQUIRED")
    require(0 <= args.hold_after_warm_seconds <= 900, "WARM_HOLD_OUT_OF_RANGE")
    require(args.execute_confirmed_ready_pilot or args.observe_only, "EXPLICIT_STAGE_EXECUTION_OR_OBSERVATION_REQUIRED")
    require(not (args.execute_confirmed_ready_pilot and args.observe_only), "STAGE_MODE_AMBIGUOUS")
    if args.stage == "after_stop":
        require(args.confirmed_supported_owned_sandbox_stop
                and re.fullmatch(r"wsb:[a-z0-9]{8}", args.stopped_sandbox_id or "")
                and re.fullmatch(r"[a-f0-9]{64}", args.supported_stop_receipt_sha256 or ""),
                "ROOT_VERIFIED_SUPPORTED_OWNED_STOP_PROOF_REQUIRED")
    prefix = "r6-sandbox-lifecycle-20261012:" + args.canary_id
    pid, port, connection = service_state()
    require(pid == args.service_pid, "REVIEWED_SERVICE_PROCESS_CHANGED")
    client = Mcp(port, existing_credential(args, connection))
    contract = check_target(args, connection, client)
    task_id, actions = handles(connection, prefix)
    if task_id is None:
        require(args.stage == "cold" and args.execute_confirmed_ready_pilot,
                "ORIGINAL_TASK_NOT_FOUND_OBSERVATION_ONLY")
        require(census(connection, args) == {"open_tasks": 0, "unreleased_writers": 0, "unsettled_actions": 0},
                "CURRENT_MACHINE_NOT_IDLE")
        PHASE = "opening_exact_task"
        emit("before_supported_task_open", canary_id=args.canary_id, idempotency_key=prefix + ":task")
        opened = client.call("workspace_context", {"operation": "task_open", "binding_id": args.binding_id,
                             "label": "r6 cold warm and recreated sandbox node version proof", "idempotency_key": prefix + ":task"})
        task_id = opened.get("task", {}).get("task_id")
        require(isinstance(task_id, str) and re.fullmatch(r"task_[a-f0-9]{32}", task_id), "TASK_HANDLE_INVALID")
        lease = client.call("task_control", {"operation": "writer_claim", "task_id": task_id}).get("writer_lease", {})
        require(lease.get("state") == "held" and lease.get("task_id") == task_id
                and lease.get("binding_id") == args.binding_id, "EXACT_CANARY_WRITER_NOT_HELD")
    require(check_target(args, connection, client, task_id) == contract, "ORIGINAL_TASK_TARGET_CHANGED")
    lease_generation = lease_identity(connection, task_id, live=args.stage != "close" and not args.observe_only)
    require(census(connection, args)["open_tasks"] == 1
            and census(connection, args)["unreleased_writers"] == 1,
            "OTHER_CURRENT_TASK_OR_WRITER_PRESENT")
    if args.stage == "close":
        require(args.execute_confirmed_ready_pilot, "SUPPORTED_CLEANUP_EXECUTION_REQUIRED")
        close_exact_task(connection, client, args, prefix, task_id)
        return 0
    proofs = {}
    for prior_lane in STAGES[:STAGES.index(args.stage)]:
        require(prior_lane in actions, "PRIOR_STAGE_ORIGINAL_ACTION_MISSING")
        original_intent = connection.execute(
            "SELECT task_id,writer_lease_generation FROM mcp_exec_intents WHERE action_id=?",
            (actions[prior_lane],)).fetchone()
        require(original_intent is not None and original_intent["task_id"] == task_id,
                "PRIOR_STAGE_TASK_CHANGED")
        original_generation = original_intent["writer_lease_generation"]
        proofs[prior_lane] = verified_version(connection, client, args, contract, task_id,
                                              original_generation, prior_lane, actions[prior_lane])
        proofs[prior_lane]["writer_lease_generation"] = original_generation
    action_id = actions.get(args.stage)
    if action_id is None:
        require(args.execute_confirmed_ready_pilot, "ORIGINAL_ACTION_NOT_FOUND_OBSERVE_ONLY")
        require(census(connection, args)["unsettled_actions"] == 0, "OTHER_UNSETTLED_CURRENT_ACTION")
        renew(client, task_id, lease_generation)
        PHASE = "enqueue_original_" + args.stage
        emit("before_original_stage_enqueue", lane=args.stage, canary_id=args.canary_id, task_id=task_id,
             idempotency_key=prefix + ":" + args.stage,
             root_verified_stop_receipt_sha256=args.supported_stop_receipt_sha256 if args.stage == "after_stop" else None,
             root_verified_stopped_sandbox_id=args.stopped_sandbox_id if args.stage == "after_stop" else None)
        queued = client.call("exec_command", {"operation": "exec_run", "argv": ARGV, "cwd": "",
                                              "timeout_ms": 300000, "max_output_bytes": 4096,
                                              "binding_id": args.binding_id, "task_id": task_id,
                                              "idempotency_key": prefix + ":" + args.stage,
                                              "expected_facade_contract": contract})
        action_id = queued.get("action_id")
        require(isinstance(action_id, str) and re.fullmatch(r"act_[a-f0-9]{32}", action_id)
                and queued.get("replayed") is False, "NEW_ORIGINAL_ACTION_NOT_EXACT")
        actions[args.stage] = action_id
        emit("original_stage_action_queued", lane=args.stage, task_id=task_id, action_id=action_id)
    else:
        emit("recover_original_stage_handle_observe_only", lane=args.stage, task_id=task_id, action_id=action_id,
             no_replay=True)
    PHASE = "observe_original_" + args.stage
    result = observe(client, connection, args, contract, task_id, lease_generation, args.stage, action_id)
    require(result.get("action", {}).get("settled_at_ms") is not None
            and result.get("reconciliation_required") is not True, "ORIGINAL_ACTION_EFFECT_UNKNOWN_DO_NOT_REPLACE")
    try:
        proof = verified_version(connection, client, args, contract, task_id, lease_generation, args.stage, action_id)
        proof["writer_lease_generation"] = lease_generation
        if proofs:
            require(all(prior["version"] == proof["version"] for prior in proofs.values()), "VERSION_CHANGED_ACROSS_STAGES")
        proofs[args.stage] = proof
    except Exception:
        # Terminal FAILED is an observed failed test. Cleanup does not assert
        # success, change the native Job, or create another action.
        if args.execute_confirmed_ready_pilot and census(connection, args)["unsettled_actions"] == 0:
            close_exact_task(connection, client, args, prefix, task_id)
        raise
    emit("original_stage_job_verified", canary_id=args.canary_id, task_id=task_id,
         same_version_across_completed_stages=True, **proof)
    if args.stage == "after_stop":
        if args.execute_confirmed_ready_pilot:
            close_exact_task(connection, client, args, prefix, task_id)
        emit("three_stage_complete", ok=True, canary_id=args.canary_id, task_id=task_id, proofs=proofs,
             root_stop_receipt_sha256=args.supported_stop_receipt_sha256,
             root_stopped_sandbox_id=args.stopped_sandbox_id, current_generation_census=census(connection, args))
    elif args.stage == "warm":
        emit("ready_for_root_supported_owned_vm_stop", ok=True, canary_id=args.canary_id, task_id=task_id,
             proofs=proofs, writer_lease_generation=lease_generation, hold_seconds=args.hold_after_warm_seconds,
             current_generation_census=census(connection, args),
             next_action="Root verifies and stops the exact owned Sandbox, then invokes after_stop using its stop receipt")
        if args.execute_confirmed_ready_pilot:
            PHASE = "hold_exact_writer_during_root_vm_stop"
            deadline = time.monotonic() + args.hold_after_warm_seconds
            while time.monotonic() < deadline:
                task = connection.execute("SELECT closed_at_ms FROM mcp_task_sessions WHERE task_id=?", (task_id,)).fetchone()
                if task and task["closed_at_ms"] is not None:
                    emit("holder_observed_exact_task_closed", ok=True, task_id=task_id)
                    return 0
                require(check_target(args, connection, client, task_id) == contract, "WARM_HOLDER_AUTHORITY_CHANGED")
                renew(client, task_id, lease_generation)
                time.sleep(20)
            emit("warm_writer_hold_elapsed", task_id=task_id,
                 next_action="Renew this exact task before the 60s lease expires; do not create another canary")
    else:
        emit("cold_stage_complete", ok=True, canary_id=args.canary_id, task_id=task_id,
             writer_lease_generation=lease_generation,
             next_action="Invoke warm for this same canary within the 60s writer lease")
    connection.close()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        emit("stage_failed_or_needs_original_observation", ok=False, failure_phase=PHASE,
             error_code=error_code(error),
             next_action="Read original durable handles/receipts; do not enqueue a replacement action")
        sys.exit(1)
