"""Run one reviewed shared MCP exec proof on svhome after READY/pilot confirmation.

Uses the existing canonical service credential, a durable task and writer lease.
Never dispatches a replacement action, even if an HTTP response is lost. Only
supported MCP calls mutate state. SQLite is opened read-only for exact lineage
and cleanup verification. Credentials and raw error payloads stay in memory.
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
RETIRED_GENERATION = "generation_fe5aea8e583749c3bd59986650144bb2"
PRINCIPAL = "svcprn_cd98750c7c7e45678d201066dc1b7d7a"
GRANT = "mcpsvcgrant_bf8c94291a1b448abcfdaaba5531a5bd"
CANARY = ".coding-tools/reports/new-machine-readiness-20261012/shared-exec-canary.cjs"
ARGV = ["node", "--test", CANARY]
MARKER = "NEW_MACHINE_SHARED_MCP_EXEC_20261012_OK"
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
    print(json.dumps({"operation": "shared_exec_canary", "phase": phase,
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
        require(tool_result.get("isError") is not True, "MCP_TOOL_ERROR")
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
            and {"control-plane.inventory", "control-plane.patch"} <= set(json.loads(grant["scopes_json"]))
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
            and target.get("capabilities", {}).get("exec") is True,
            "SHARED_MCP_TARGET_NOT_READY")
    contract = inventory.get("tool_contract", {})
    require(set(contract) == {"schema_version", "profile", "sha256"}
            and contract["schema_version"] == 32
            and contract["profile"] == "control-plane-private-tunnel-service-v1"
            and re.fullmatch(r"[a-f0-9]{64}", contract["sha256"]),
            "SHARED_FACADE_CONTRACT_UNEXPECTED")
    if task_id is not None:
        task = connection.execute("SELECT * FROM mcp_task_sessions WHERE task_id=?", (task_id,)).fetchone()
        require(task is not None and task["principal_id"] == PRINCIPAL
                and task["binding_id"] == args.binding_id and task["workspace_generation"] == args.new_generation
                and task["scoped_pilot_decision_id"] == args.pilot_decision_id
                and task["closed_at_ms"] is None, "TASK_TARGET_CHANGED")
    return contract


def recover_handles(connection, attempt):
    task = connection.execute(
        "SELECT task_id FROM mcp_task_open_idempotency WHERE principal_id=? AND idempotency_key=?",
        (PRINCIPAL, attempt + ":task")).fetchone()
    action = connection.execute(
        "SELECT action_id,task_id FROM mcp_exec_intents WHERE principal_id=? AND idempotency_key=?",
        (PRINCIPAL, attempt + ":exec")).fetchone()
    return (task["task_id"] if task else None, action["action_id"] if action else None)


def observe(client, action_id, seconds, *, task_id=None, lease_generation=None):
    deadline = time.monotonic() + seconds
    last_report = 0
    last_renewal = 0
    while True:
        if task_id is not None and time.monotonic() - last_renewal >= 20:
            renewed = client.call("task_control", {"operation": "writer_claim", "task_id": task_id})
            lease = renewed.get("writer_lease", {})
            require(lease.get("state") == "held" and lease.get("task_id") == task_id
                    and lease.get("lease_generation") == lease_generation,
                    "ORIGINAL_WRITER_LEASE_GENERATION_CHANGED")
            last_renewal = time.monotonic()
        result = client.call("exec_command", {"operation": "exec_status", "action_id": action_id})
        action = result.get("action", {})
        require(action.get("action_id") == action_id, "OBSERVATION_ACTION_CHANGED")
        if result.get("reconciliation_required") is True or result.get("process_state") == "unknown":
            return result
        if result.get("process_state") in {"completed", "failed", "stopped", "refused", "expired"}:
            return result
        if time.monotonic() - last_report >= 45:
            emit("observing_original_action", action_id=action_id,
                 process_state=result.get("process_state"),
                 central_lifecycle_state=action.get("central_lifecycle_state"))
            last_report = time.monotonic()
        require(time.monotonic() < deadline, "ORIGINAL_ACTION_OBSERVATION_TIMEOUT")
        time.sleep(5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ("binding-id", "new-generation", "pilot-decision-id", "activation-epoch",
                  "process-instance-id", "server-instance-id", "local-tool-contract-sha256",
                  "attempt-id", "credential-file"):
        parser.add_argument("--" + field, required=True)
    parser.add_argument("--credential-json-key")
    parser.add_argument("--execute-confirmed-ready-pilot", action="store_true", required=True)
    args = parser.parse_args()
    require(re.fullmatch(r"generation_[a-f0-9]{32}", args.new_generation)
            and args.new_generation != RETIRED_GENERATION, "NEW_GENERATION_INVALID")
    require(re.fullmatch(r"[a-f0-9]{32}", args.attempt_id), "ATTEMPT_ID_INVALID")
    require(re.fullmatch(r"[a-f0-9]{64}", args.local_tool_contract_sha256), "LOCAL_CONTRACT_INVALID")
    attempt = "new-machine-20261012:" + args.attempt_id
    pid, port, connection = service_state()
    client = Mcp(port, existing_credential(args, connection))
    task_id = action_id = None
    terminal = False
    attempt_owned = False
    outcome = {"ok": False, "service_pid": pid, "binding_id": args.binding_id,
               "workspace_generation": args.new_generation, "attempt_id": args.attempt_id}
    try:
        require(recover_handles(connection, attempt) == (None, None), "ATTEMPT_ALREADY_USED_DO_NOT_REDISPATCH")
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
                             "label": "New machine harmless exec proof", "idempotency_key": attempt + ":task"})
        task_id = opened.get("task", {}).get("task_id")
        require(isinstance(task_id, str) and re.fullmatch(r"task_[a-f0-9]{32}", task_id), "TASK_HANDLE_INVALID")
        claimed = client.call("task_control", {"operation": "writer_claim", "task_id": task_id})
        lease = claimed.get("writer_lease", {})
        require(lease.get("state") == "held" and lease.get("task_id") == task_id
                and lease.get("binding_id") == args.binding_id, "WRITER_LEASE_NOT_HELD")
        require(check_target(args, connection, client, task_id) == contract, "FACADE_CONTRACT_CHANGED")
        queued = client.call("exec_command", {"operation": "exec_run", "binding_id": args.binding_id,
                             "task_id": task_id, "argv": ARGV, "cwd": "", "timeout_ms": 300000,
                             "max_output_bytes": 32768, "idempotency_key": attempt + ":exec",
                             "expected_facade_contract": contract})
        action_id = queued.get("action_id")
        require(isinstance(action_id, str) and re.fullmatch(r"act_[a-f0-9]{32}", action_id), "ACTION_HANDLE_INVALID")
        emit("queued_original_action", task_id=task_id, action_id=action_id,
             request_id=queued.get("request_id"), intent_digest=queued.get("intent_digest"), argv=ARGV)
        result = observe(client, action_id, OBSERVE_SECONDS,
                         task_id=task_id, lease_generation=lease["lease_generation"])
        outcome["status"] = result
        terminal = result.get("action", {}).get("settled_at_ms") is not None
        require(result.get("execution") == "completed_exec_relay"
                and result.get("process_state") == "completed" and result.get("exit_code") == 0
                and terminal, "ORIGINAL_EXEC_NOT_VERIFIED_SUCCESS")
        page = client.call("command_control", {"operation": "exec_output", "action_id": action_id,
                           "cursor": 0, "max_bytes": 65536})
        require(page.get("has_output") is True and page.get("exit_code") == 0
                and page.get("truncated") is False and MARKER in page.get("output", ""),
                "CANARY_OUTPUT_NOT_VERIFIED")
        receipt_id = result.get("exec", {}).get("receipt_id")
        receipt = connection.execute(
            "SELECT payload_json FROM receipts WHERE receipt_id=? AND action_id=?", (receipt_id, action_id)).fetchone()
        require(receipt is not None, "VERIFIED_RECEIPT_NOT_FOUND")
        proof = json.loads(receipt["payload_json"])
        expected_runtime = {"activation_epoch_id": args.activation_epoch,
                            "process_instance_id": args.process_instance_id,
                            "server_instance_id": args.server_instance_id,
                            "tool_contract_sha256": args.local_tool_contract_sha256}
        require(proof.get("runtime_identity") == expected_runtime and proof.get("task_id") == task_id
                and proof.get("writer_lease_generation") == lease["lease_generation"]
                and proof.get("local_handle") == result["exec"]["local_handle"]
                and proof.get("response_sha256") == result["exec"]["response_sha256"]
                and proof.get("facade_contract") == contract
                and proof.get("actor") == {"client_id": "electron-control-plane-exec-bridge", "client_type": "electron"}
                and proof.get("job_id") and proof.get("command_id"), "ORIGINAL_JOB_IDENTITY_NOT_VERIFIED")
        outcome.update({"ok": True, "original_job": {key: proof.get(key) for key in
                        ("local_handle", "job_id", "command_id", "run_id", "wave_id", "runtime_identity")},
                        "marker_verified": True, "output_sha256": hashlib.sha256(page["output"].encode()).hexdigest(),
                        "output_bytes": page["total_bytes"]})
    except Exception as error:
        outcome["error_code"] = error_code(error)
    finally:
        if attempt_owned:
            try:
                recovered_task, recovered_action = recover_handles(connection, attempt)
                task_id = task_id or recovered_task
                action_id = action_id or recovered_action
            except Exception as error:
                outcome["handle_recovery_error"] = error_code(error)
        outcome.update({"task_id": task_id, "action_id": action_id})
        if action_id and not terminal:
            try:
                current = client.call("exec_command", {"operation": "exec_status", "action_id": action_id})
                outcome["final_action_status"] = current
                terminal = current.get("action", {}).get("settled_at_ms") is not None
                if not terminal:
                    stopped = client.call("command_control", {"operation": "exec_stop", "action_id": action_id})
                    outcome["stop_request"] = stopped
                    stopped_result = observe(client, action_id, 120)
                    outcome["final_action_status"] = stopped_result
                    terminal = stopped_result.get("action", {}).get("settled_at_ms") is not None
                outcome["action_terminal_verified"] = terminal
            except Exception as error:
                outcome["stop_or_observe_error"] = error_code(error)
            outcome["requires_reconciliation"] = not terminal
        if action_id:
            try:
                receipts = connection.execute(
                    "SELECT receipt_id,receipt_state,received_at_ms,payload_json FROM receipts "
                    "WHERE action_id=? ORDER BY received_at_ms DESC LIMIT 5", (action_id,)).fetchall()
                jobs = []
                for receipt in receipts:
                    payload = json.loads(receipt["payload_json"])
                    if payload.get("operation_kind") == "control_plane_exec" and payload.get("job_id"):
                        jobs.append({"receipt_id": receipt["receipt_id"], "receipt_state": receipt["receipt_state"],
                                     "received_at_ms": receipt["received_at_ms"],
                                     **{key: payload.get(key) for key in
                                        ("job_id", "command_id", "local_handle", "run_id", "wave_id", "runtime_identity")}})
                outcome["receipt_job_observations"] = jobs
            except Exception as error:
                outcome["receipt_job_observation_error"] = error_code(error)
        if task_id:
            for tool, operation, extra in (
                ("task_control", "writer_release", {"reason": "new_machine_canary_finished"}),
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
        connection.close()
        emit("final", **outcome)
    return 0 if outcome["ok"] else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        emit("preflight_failed", ok=False, error_code=error_code(error))
        sys.exit(1)
