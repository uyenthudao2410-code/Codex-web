"""Run one reviewed shared MCP create, exact patch and exec proof on svhome after READY/pilot confirmation.

Uses the existing canonical service credential, a durable task and writer lease.
Never dispatches a replacement action, even if an HTTP response is lost. Only
supported MCP calls mutate state. SQLite is opened read-only for exact lineage
and cleanup verification. Credentials and raw error payloads stay in memory.
"""

import argparse
import base64
import zlib
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
RETIRED_GENERATION = "generation_fe5aea8e583749c3bd59986650144bb2"
PRINCIPAL = "svcprn_cd98750c7c7e45678d201066dc1b7d7a"
GRANT = "mcpsvcgrant_bf8c94291a1b448abcfdaaba5531a5bd"
CANARY = ".coding-tools/reports/shared-write-exec-20261012-r8/shared-write-exec-check-r8.cjs"
ARGV = ["node", "--test", CANARY]
MARKER = "NEW_MACHINE_SHARED_MCP_WRITE_EXEC_20261012_OK"
TARGET = "tests/fixtures/new-machine-shared-write-proof-20261012-r8.txt"
INITIAL = "NEW_MACHINE_SHARED_MCP_WRITE_20261012_CREATED\nstage=doc_create"
FINAL = MARKER + "\nstage=exact_patch"
PROTOCOL = "2026-07-28"
OBSERVE_SECONDS = 900


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


def emit(phase, **fields):
    print(json.dumps({"operation": "shared_write_exec_canary", "phase": phase,
                      "observed_at_ms": int(time.time() * 1000), **fields},
                     separators=(",", ":")), flush=True)


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


LANES = {
    "create": ("mcp_document_write_intents", "document_workflow", "doc_status"),
    "read_initial": ("mcp_file_read_intents", "workspace_context", "read_status"),
    "patch": ("mcp_standing_patch_intents", "agent_workflow", "patch_status"),
    "read_final": ("mcp_file_read_intents", "workspace_context", "read_status"),
    "exec": ("mcp_exec_intents", "exec_command", "exec_status"),
}


def recover_handles(connection, attempt):
    task = connection.execute(
        "SELECT task_id FROM mcp_task_open_idempotency WHERE principal_id=? AND idempotency_key=?",
        (PRINCIPAL, attempt + ":task")).fetchone()
    actions = {}
    for lane, (table, _tool, _operation) in LANES.items():
        # Table names are fixed above, never user input.
        row = connection.execute(
            f"SELECT action_id FROM {table} WHERE principal_id=? AND idempotency_key=?",
            (PRINCIPAL, attempt + ":" + lane)).fetchone()
        if row:
            actions[lane] = row["action_id"]
    return (task["task_id"] if task else None, actions)


def renew(client, task_id, lease_generation):
    lease = client.call("task_control", {"operation": "writer_claim", "task_id": task_id}).get("writer_lease", {})
    require(lease.get("state") == "held" and lease.get("task_id") == task_id
            and lease.get("lease_generation") == lease_generation,
            "ORIGINAL_WRITER_LEASE_GENERATION_CHANGED")


def observe(client, lane, action_id, seconds, task_id, lease_generation):
    _table, tool, operation = LANES[lane]
    deadline = time.monotonic() + seconds
    last_report = last_renewal = 0
    while True:
        if time.monotonic() - last_renewal >= 20:
            renew(client, task_id, lease_generation)
            last_renewal = time.monotonic()
        result = client.call(tool, {"operation": operation, "action_id": action_id})
        action = result.get("action", {})
        require(action.get("action_id") == action_id, "OBSERVATION_ACTION_CHANGED")
        if action.get("settled_at_ms") is not None or result.get("reconciliation_required") is True:
            return result
        if time.monotonic() - last_report >= 45:
            emit("observing_original_action", lane=lane, action_id=action_id,
                 central_lifecycle_state=action.get("central_lifecycle_state"))
            last_report = time.monotonic()
        require(time.monotonic() < deadline, "ORIGINAL_ACTION_OBSERVATION_TIMEOUT")
        time.sleep(5)


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


def patch_envelope():
    initial_digest = hashlib.sha256(INITIAL.encode()).hexdigest()
    final_digest = hashlib.sha256(FINAL.encode()).hexdigest()
    body = base64.b64encode(zlib.compress(FINAL.encode())).decode()
    envelope = ("*** Begin Patch\n*** Write Exact File: " + TARGET + "\n"
                "@@ encoding=zlib-base64 preimage_sha256=" + initial_digest
                + " postimage_sha256=" + final_digest + "\n+" + body + "\n*** End Patch\n")
    return envelope, initial_digest, final_digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ("binding-id", "new-generation", "pilot-decision-id", "activation-epoch",
                  "process-instance-id", "server-instance-id", "local-tool-contract-sha256",
                  "facade-contract-sha256", "attempt-id", "credential-file"):
        parser.add_argument("--" + field, required=True)
    parser.add_argument("--facade-schema-version", type=int, required=True)
    parser.add_argument("--service-pid", type=int, required=True)
    parser.add_argument("--execute-confirmed-ready-pilot", action="store_true", required=True)
    args = parser.parse_args()
    args.credential_json_key = None
    require(re.fullmatch(r"generation_[a-f0-9]{32}", args.new_generation)
            and args.new_generation != RETIRED_GENERATION, "NEW_GENERATION_INVALID")
    require(re.fullmatch(r"[a-f0-9]{32}", args.attempt_id), "ATTEMPT_ID_INVALID")
    require(all(re.fullmatch(r"[a-f0-9]{64}", value) for value in
                (args.local_tool_contract_sha256, args.facade_contract_sha256)), "CONTRACT_DIGEST_INVALID")
    require(args.facade_schema_version >= 32, "FACADE_SCHEMA_INVALID")
    attempt = "shared-write-exec-r8-20261012:" + args.attempt_id
    pid, port, connection = service_state()
    require(pid == args.service_pid, "REVIEWED_SERVICE_PROCESS_CHANGED")
    client = Mcp(port, existing_credential(args, connection))
    task_id = lease_generation = None
    actions = {}
    attempt_owned = False
    outcome = {"ok": False, "service_pid": pid, "binding_id": args.binding_id,
               "workspace_generation": args.new_generation, "attempt_id": args.attempt_id,
               "target": TARGET, "proofs": {}, "semantic_acceptance_performed": False}
    try:
        require(recover_handles(connection, attempt) == (None, {}), "ATTEMPT_ALREADY_USED_DO_NOT_REDISPATCH")
        attempt_owned = True
        contract = check_target(args, connection, client)
        require(connection.execute(
            "SELECT COUNT(*) FROM mcp_task_sessions WHERE binding_id=? AND closed_at_ms IS NULL",
            (args.binding_id,)).fetchone()[0] == 0, "CURRENT_TARGET_HAS_OPEN_TASK")
        require(connection.execute(
            "SELECT COUNT(*) FROM actions WHERE device_id=? AND workspace_id=? "
            "AND workspace_generation=? AND settled_at_ms IS NULL",
            (DEVICE, WORKSPACE, args.new_generation)).fetchone()[0] == 0,
            "CURRENT_GENERATION_HAS_UNSETTLED_ACTION")
        opened = client.call("workspace_context", {"operation": "task_open", "binding_id": args.binding_id,
                             "label": "New machine shared write and exec proof", "idempotency_key": attempt + ":task"})
        task_id = opened.get("task", {}).get("task_id")
        require(isinstance(task_id, str) and re.fullmatch(r"task_[a-f0-9]{32}", task_id), "TASK_HANDLE_INVALID")
        lease = client.call("task_control", {"operation": "writer_claim", "task_id": task_id}).get("writer_lease", {})
        require(lease.get("state") == "held" and lease.get("task_id") == task_id
                and lease.get("binding_id") == args.binding_id, "WRITER_LEASE_NOT_HELD")
        lease_generation = lease["lease_generation"]

        def queue(lane, tool, arguments):
            require(check_target(args, connection, client, task_id) == contract, "FACADE_CONTRACT_CHANGED")
            renew(client, task_id, lease_generation)
            require(lane not in recover_handles(connection, attempt)[1], "LANE_ALREADY_USED_DO_NOT_REDISPATCH")
            require(service_state_pid() == args.service_pid, "REVIEWED_SERVICE_PROCESS_CHANGED")
            queued = client.call(tool, {**arguments, "binding_id": args.binding_id, "task_id": task_id,
                                       "idempotency_key": attempt + ":" + lane,
                                       "expected_facade_contract": contract})
            action_id = queued.get("action_id")
            require(isinstance(action_id, str) and re.fullmatch(r"act_[a-f0-9]{32}", action_id), "ACTION_HANDLE_INVALID")
            require(queued.get("replayed") is False, "UNEXPECTED_REPLAY")
            actions[lane] = action_id
            emit("queued_original_action", lane=lane, task_id=task_id, action_id=action_id,
                 request_id=queued.get("request_id"), intent_digest=queued.get("intent_digest"))
            result = observe(client, lane, action_id, OBSERVE_SECONDS, task_id, lease_generation)
            outcome["proofs"][lane] = {"status": result}
            require(result.get("action", {}).get("settled_at_ms") is not None
                    and result.get("reconciliation_required") is not True, "ORIGINAL_ACTION_NOT_SETTLED")
            return result

        created = queue("create", "document_workflow", {"operation": "doc_create", "target": TARGET,
                                                         "content": INITIAL, "overwrite": False})
        require(created.get("execution") == "completed_document_write_relay", "DOCUMENT_CREATE_NOT_VERIFIED")
        payload, proof = verified_receipt(connection, created, "document", args, contract, task_id,
                                         lease_generation, "electron-control-plane-document-bridge",
                                         "control_plane_document_write")
        require(payload.get("target") == TARGET and payload.get("operation") == "document_create"
                and payload.get("result", {}).get("sha256") == hashlib.sha256(INITIAL.encode()).hexdigest()
                and payload.get("result", {}).get("size") == len(INITIAL.encode()), "CREATED_BYTES_NOT_VERIFIED")
        outcome["proofs"]["create"]["receipt"] = proof
        emit("create_verified", **proof)

        def readback(lane, expected):
            result = queue(lane, "workspace_context", {"operation": "read_file", "path": TARGET,
                                                       "start_line": 1, "max_lines": 20, "max_bytes": 4096})
            file = result.get("file_read", {}).get("file", {})
            require(result.get("execution") == "completed_file_read_relay" and result.get("file_accessed") is True
                    and file.get("path") == TARGET and file.get("content") == expected
                    and file.get("content_sha256") == hashlib.sha256(expected.encode()).hexdigest()
                    and file.get("truncated") is False and file.get("total_bytes") == len(expected.encode())
                    and file.get("bytes_read") == len(expected.encode()), "EXACT_READBACK_NOT_VERIFIED")
            _payload, proof = verified_receipt(connection, result, "file_read", args, contract, task_id,
                                               lease_generation, "electron-control-plane-file-read-bridge",
                                               "control_plane_bounded_file_read")
            outcome["proofs"][lane]["receipt"] = proof
            emit("readback_verified", lane=lane, content_sha256=file["content_sha256"], **proof)

        readback("read_initial", INITIAL)
        envelope, preimage, postimage = patch_envelope()
        patched = queue("patch", "agent_workflow", {"operation": "apply_patch", "path": TARGET,
                                                     "preimage_sha256": preimage,
                                                     "patch_sha256": hashlib.sha256(envelope.encode()).hexdigest(),
                                                     "validation_profile": "targeted", "patch_envelope": envelope})
        require(patched.get("patch_applied") is True and patched.get("patch_effect_state") == "verified_applied",
                "EXACT_PATCH_NOT_VERIFIED")
        payload, proof = verified_receipt(connection, patched, "patch", args, contract, task_id, lease_generation,
                                         "electron-control-plane-approved-patch-bridge", "control_plane_approved_patch")
        require(payload.get("file") == {"path": TARGET, "preimage_sha256": preimage,
                                        "postimage_sha256": postimage, "bytes_written": len(FINAL.encode())}
                and payload.get("local_semantic_acceptance") == "pending"
                and payload.get("run_id") and payload.get("wave_id"), "PATCH_POSTIMAGE_OR_LINEAGE_NOT_VERIFIED")
        proof.update({key: payload[key] for key in ("run_id", "wave_id", "local_semantic_acceptance")})
        outcome["proofs"]["patch"]["receipt"] = proof
        emit("patch_verified", preimage_sha256=preimage, postimage_sha256=postimage, **proof)
        readback("read_final", FINAL)

        executed = queue("exec", "exec_command", {"operation": "exec_run", "argv": ARGV, "cwd": "",
                                                    "timeout_ms": 300000, "max_output_bytes": 32768})
        require(executed.get("execution") == "completed_exec_relay"
                and executed.get("process_state") == "completed" and executed.get("exit_code") == 0,
                "ORIGINAL_EXEC_NOT_VERIFIED_SUCCESS")
        page = client.call("command_control", {"operation": "exec_output", "action_id": actions["exec"],
                                                "cursor": 0, "max_bytes": 65536})
        require(page.get("has_output") is True and page.get("exit_code") == 0 and page.get("truncated") is False
                and MARKER + " sha256=" + postimage in page.get("output", ""), "CHECKER_OUTPUT_NOT_VERIFIED")
        payload, proof = verified_receipt(connection, executed, "exec", args, contract, task_id, lease_generation,
                                         "electron-control-plane-exec-bridge", "control_plane_exec")
        require(payload.get("local_handle") == executed["exec"]["local_handle"]
                and payload.get("job_id") and payload.get("command_id"), "ORIGINAL_JOB_IDENTITY_NOT_VERIFIED")
        proof.update({key: payload.get(key) for key in ("local_handle", "job_id", "command_id", "run_id", "wave_id")})
        proof["output_sha256"] = hashlib.sha256(page["output"].encode()).hexdigest()
        proof["output_bytes"] = page["total_bytes"]
        outcome["proofs"]["exec"]["receipt"] = proof
        outcome.update({"ok": True, "final_sha256": postimage, "marker_verified": True})
        emit("original_job_verified", **proof)
    except Exception as error:
        outcome["error_code"] = error_code(error)
    finally:
        if attempt_owned:
            try:
                recovered_task, recovered_actions = recover_handles(connection, attempt)
                task_id = task_id or recovered_task
                actions.update(recovered_actions)
            except Exception as error:
                outcome["handle_recovery_error"] = error_code(error)
        outcome.update({"task_id": task_id, "action_ids": actions})
        unresolved = []
        for lane, action_id in actions.items():
            try:
                result = client.call(LANES[lane][1], {"operation": LANES[lane][2], "action_id": action_id})
                effect_unknown = (result.get("reconciliation_required") is True
                                  or result.get("process_state") == "unknown")
                if result.get("action", {}).get("settled_at_ms") is None and not effect_unknown:
                    if lane == "exec":
                        outcome["stop_request"] = client.call("command_control", {"operation": "exec_stop", "action_id": action_id})
                    if task_id and lease_generation:
                        result = observe(client, lane, action_id, 120, task_id, lease_generation)
                outcome.setdefault("final_action_status", {})[lane] = result
                if (result.get("action", {}).get("settled_at_ms") is None
                        or result.get("reconciliation_required") is True
                        or result.get("process_state") == "unknown"):
                    unresolved.append(lane)
            except Exception as error:
                outcome.setdefault("final_observation_errors", {})[lane] = error_code(error)
                unresolved.append(lane)
        outcome["unresolved_original_actions"] = unresolved
        outcome["requires_reconciliation"] = bool(unresolved)
        if task_id and not unresolved:
            for tool, operation, extra in (
                ("task_control", "writer_release", {"reason": "shared_write_exec_canary_finished"}),
                ("workspace_context", "task_close", {})):
                try:
                    client.call(tool, {"operation": operation, "task_id": task_id, **extra})
                except Exception as error:
                    outcome[operation + "_error"] = error_code(error)
            try:
                task = connection.execute("SELECT closed_at_ms FROM mcp_task_sessions WHERE task_id=?", (task_id,)).fetchone()
                held = connection.execute(
                    "SELECT COUNT(*) FROM mcp_task_writer_leases WHERE task_id=? AND released_at_ms IS NULL",
                    (task_id,)).fetchone()[0]
                outcome["task_closed_verified"] = task is not None and task["closed_at_ms"] is not None
                outcome["writer_released_verified"] = held == 0
                outcome["ok"] = outcome["ok"] and outcome["task_closed_verified"] and held == 0
            except Exception as error:
                outcome["cleanup_verification_error"] = error_code(error)
                outcome["ok"] = False
        elif task_id:
            outcome["cleanup_deferred_pending_effect"] = True
            outcome["ok"] = False
        connection.close()
        emit("final", **outcome)
    return 0 if outcome["ok"] else 1


def service_state_pid():
    return int(subprocess.check_output(
        ["systemctl", "--user", "show", "codex-control-plane.service", "--property=MainPID", "--value"],
        text=True).strip())


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        emit("preflight_failed", ok=False, error_code=error_code(error))
        sys.exit(1)


