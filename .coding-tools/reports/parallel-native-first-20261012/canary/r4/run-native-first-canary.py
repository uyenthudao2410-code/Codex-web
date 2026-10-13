"""Single-use shared MCP canary; execute only after reviewed exact READY pilot.

All mutations use existing MCP task/writer/read/patch/exec contracts. SQLite is
read-only evidence. A lost response recovers the original handle; it never
redispatches a lane. Credentials, environments, file bodies and exec output are
kept in memory. The NDJSON stream contains only bounded evidence projections.
"""

import argparse
import base64
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
import zlib

FIXTURE = "tests/fixtures/native-first-canary"
PROTOCOL = "2026-07-28"
OBSERVE_SECONDS = 300
IDENTIFIER = re.compile(r"[A-Za-z0-9_-][A-Za-z0-9_-]{0,127}")
SHA = re.compile(r"[a-f0-9]{64}")
READ = ("mcp_file_read_intents", "workspace_context", "read_status")
PATCH = ("mcp_standing_patch_intents", "agent_workflow", "patch_status")
EXEC = ("mcp_exec_intents", "exec_command", "exec_status")
LANES = {**{f"read_{i:03}": READ for i in range(1, 101)},
         **{f"patch_{i:03}": PATCH for i in range(1, 21)},
         **{f"readback_{i:03}": READ for i in range(1, 21)},
         **{f"node_{i:02}": EXEC for i in range(1, 11)},
         **{f"git_{name}": EXEC for name in ("status", "diff", "log")},
         "build": EXEC}


def sha(value):
    return hashlib.sha256(value).hexdigest()


def fixture_content(index, patched=False):
    return (f"NATIVE_FIRST_CANARY_V1\nfile={index:03}\n"
            f"stage={'patched' if patched else 'seed'}\n")


def fixture_path(index):
    return f"{FIXTURE}/file-{index:03}.txt"


def build_source():
    return """'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const crypto = require('node:crypto');
assert.equal(process.platform, 'win32');
const digest = crypto.createHash('sha256');
for (let i = 1; i <= 100; i += 1) {
  const index = String(i).padStart(3, '0');
  const expected = `NATIVE_FIRST_CANARY_V1\\nfile=${index}\\nstage=${i <= 20 ? 'patched' : 'seed'}\\n`;
  const value = fs.readFileSync(`file-${index}.txt`);
  assert.deepEqual(value, Buffer.from(expected, 'utf8'));
  digest.update(value);
}
const artifact = 'NATIVE_FIRST_CANARY_BUILD_V1 ' + digest.digest('hex') + '\\n';
fs.writeFileSync('build-artifact.txt', artifact, {encoding: 'utf8', flag: 'wx'});
console.log(artifact.trim());
"""


def build_artifact():
    data = b"".join(fixture_content(i, i <= 20).encode() for i in range(1, 101))
    return "NATIVE_FIRST_CANARY_BUILD_V1 " + sha(data) + "\n"


def require(condition, code):
    if not condition:
        raise RuntimeError(code)


def error_code(error):
    if isinstance(error, RuntimeError) and re.fullmatch(r"[A-Z][A-Z0-9_]{2,127}", str(error)):
        return str(error)
    if isinstance(error, urllib.error.HTTPError):
        return "HTTP_" + str(error.code)
    return type(error).__name__


def emit(phase, **fields):
    print(json.dumps({"operation": "native_first_shared_mcp_canary", "phase": phase,
                      "observed_at_ms": int(time.time() * 1000), **fields},
                     separators=(",", ":")), flush=True)


class Mcp:
    def __init__(self, port, token):
        self.url, self.token, self.counter = f"http://127.0.0.1:{port}/mcp", token, 0

    def call(self, name, arguments):
        self.counter += 1
        body = {"jsonrpc": "2.0", "id": self.counter, "method": "tools/call",
                "params": {"name": name, "arguments": arguments,
                           "_meta": {"io.modelcontextprotocol/protocolVersion": PROTOCOL,
                                     "io.modelcontextprotocol/clientCapabilities": {}}}}
        request = urllib.request.Request(self.url, data=json.dumps(body).encode(), method="POST",
            headers={"Authorization": "Bearer " + self.token, "Content-Type": "application/json",
                     "Accept": "application/json", "MCP-Protocol-Version": PROTOCOL,
                     "Mcp-Method": "tools/call", "Mcp-Name": name})
        with urllib.request.urlopen(request, timeout=15) as response:
            raw = response.read(196609)
        require(len(raw) <= 196608, "MCP_RESPONSE_TOO_LARGE")
        result = json.loads(raw)
        require(result.get("id") == self.counter and "error" not in result, "MCP_RPC_ERROR")
        tool_result = result.get("result", {})
        if tool_result.get("isError") is True:
            code = tool_result.get("structuredContent", {}).get("code")
            raise RuntimeError("MCP_TOOL_ERROR_" + code if isinstance(code, str)
                               and re.fullmatch(r"[A-Z][A-Z0-9_]{2,95}", code) else "MCP_TOOL_ERROR")
        observation = tool_result.get("structuredContent")
        require(isinstance(observation, dict), "MCP_STRUCTURED_RESULT_MISSING")
        return observation


def service_pid():
    result = subprocess.run(["systemctl", "--user", "show", "codex-control-plane.service",
                             "--property=MainPID", "--value"], capture_output=True, text=True, timeout=10)
    require(result.returncode == 0 and result.stdout.strip().isdigit(), "SERVICE_PID_UNAVAILABLE")
    return int(result.stdout.strip())


def service_state(args):
    pid = service_pid()
    require(pid == args.service_pid and pid > 1, "REVIEWED_SERVICE_PROCESS_CHANGED")
    environment = dict(item.split("=", 1) for item in Path(f"/proc/{pid}/environ").read_text().split("\0") if "=" in item)
    require(environment.get("CONTROL_PLANE_MCP_AUTH_MODE") == "private_tunnel_service"
            and environment.get("CONTROL_PLANE_MCP_SERVICE_PRINCIPAL_ID") == args.principal_id
            and environment.get("CONTROL_PLANE_MCP_SERVICE_GRANT_ID") == args.grant_id,
            "CANONICAL_SERVICE_AUTHORITY_CHANGED")
    require(environment.get("CONTROL_PLANE_MCP_BIND", "127.0.0.1") == "127.0.0.1", "MCP_LISTENER_NOT_LOOPBACK")
    port = int(environment.get("CONTROL_PLANE_MCP_PORT", "8766"))
    require(1024 <= port <= 65535, "MCP_PORT_INVALID")
    packages = { (Path(value).resolve() / "control_plane").resolve()
                 for value in environment.get("PYTHONPATH", "").split(":")
                 if value and (Path(value) / "control_plane/mcp_facade.py").is_file() }
    require(len(packages) == 1, "SERVING_PACKAGE_NOT_UNIQUE")
    package = packages.pop()
    require(package.is_relative_to(Path.home().resolve()), "SERVING_PACKAGE_OUTSIDE_HOME")
    for name, digest in (("mcp_facade.py", args.serving_mcp_facade_sha256),
                         ("node_agent.py", args.serving_node_agent_sha256)):
        require(sha((package / name).read_bytes()) == digest, "SERVING_SOURCE_PIN_CHANGED")
    database = Path(environment["CONTROL_PLANE_DB"])
    if not database.is_absolute():
        database = Path(f"/proc/{pid}/cwd").resolve() / database
    connection = sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)
    connection.execute("PRAGMA query_only=ON")
    connection.row_factory = sqlite3.Row
    return port, connection


def credential(args, connection):
    path = Path(args.credential_file)
    require(path.is_absolute(), "CREDENTIAL_PATH_NOT_ABSOLUTE")
    info = path.lstat()
    require(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid()
            and info.st_mode & 0o077 == 0 and info.st_size <= 65536, "CREDENTIAL_FILE_NOT_PROTECTED")
    token = path.read_text().strip().removeprefix("Bearer ")
    require(re.fullmatch(r"mcpsvc_[A-Za-z0-9_-]{32,128}", token), "SERVICE_CREDENTIAL_FORMAT_INVALID")
    digest = sha(b"coding-tools-control-plane:mcp-service-grant:v1\0" + token.encode())
    row = connection.execute("SELECT * FROM mcp_service_grants WHERE grant_id=?", (args.grant_id,)).fetchone()
    require(row is not None and row["owner_id"] == "owner_default" and row["principal_id"] == args.principal_id
            and row["revoked_at_ms"] is None and row["expires_at_ms"] > int(time.time() * 1000) + 1800000
            and {"control-plane.inventory", "control-plane.read", "control-plane.patch"} <= set(json.loads(row["scopes_json"]))
            and hmac.compare_digest(row["token_digest"], digest), "CREDENTIAL_NOT_EXACT_LIVE_CANONICAL_GRANT")
    return token


def check_target(args, connection, client, task_id=None):
    now = int(time.time() * 1000)
    rows = connection.execute("SELECT * FROM scoped_pilot_decisions WHERE principal_id=? AND binding_id=? AND device_id=? AND workspace_id=? AND workspace_generation=? AND revoked_at_ms IS NULL AND expires_at_ms>?", (args.principal_id, args.binding_id, args.device_id, args.workspace_id, args.workspace_generation, now)).fetchall()
    require(len(rows) == 1, "EXACT_CURRENT_PILOT_NOT_READY")
    target = rows[0]
    for key, expected in (("decision_id", args.pilot_decision_id), ("principal_id", args.principal_id),
                          ("binding_id", args.binding_id), ("device_id", args.device_id),
                          ("workspace_id", args.workspace_id), ("workspace_generation", args.workspace_generation)):
        require(target[key] == expected, "EXACT_CURRENT_PILOT_NOT_READY")
    require(target["expires_at_ms"] > now + 1800000, "PILOT_EXPIRY_TOO_NEAR")
    mode = connection.execute("SELECT state_value FROM control_plane_state WHERE state_key='admission_mode'").fetchone()
    require(mode is not None and mode[0] == "scoped_pilot", "ADMISSION_NOT_SCOPED_PILOT")
    node = connection.execute("SELECT * FROM nodes WHERE device_id=? AND revoked_at_ms IS NULL", (args.device_id,)).fetchone()
    require(node is not None and node["readiness"] == "ready" and now - node["last_seen_at_ms"] <= 90000
            and node["runtime_instance_id"] == args.process_instance_id
            and node["mcp_server_instance_id"] == args.server_instance_id
            and node["activation_epoch"] == args.activation_epoch, "PACKAGED_READY_IDENTITY_NOT_CURRENT")
    inventory = client.call("workspace_context", {"operation": "inventory"})
    require(inventory.get("principal_id") == args.principal_id, "SHARED_MCP_PRINCIPAL_CHANGED")
    matches = [item for item in inventory.get("targets", []) if item.get("binding_id") == args.binding_id]
    require(len(matches) == 1, "SHARED_MCP_INVENTORY_NOT_EXACT")
    target = matches[0]
    require(target.get("binding_id") == args.binding_id and target.get("device_id") == args.device_id
            and target.get("workspace_id") == args.workspace_id and target.get("workspace_generation") == args.workspace_generation
            and target.get("readiness") == "ready" and target.get("presence_state") == "online"
            and target.get("dispatch_state") == "dispatchable"
            and all(target.get("capabilities", {}).get(lane) is True for lane in ("read", "write", "exec")), "SHARED_MCP_TARGET_NOT_READY")
    contract = {"schema_version": args.facade_schema_version, "profile": "control-plane-private-tunnel-service-v1",
                "sha256": args.facade_contract_sha256}
    require(inventory.get("tool_contract") == contract, "SHARED_FACADE_CONTRACT_CHANGED")
    require(service_pid() == args.service_pid, "REVIEWED_SERVICE_PROCESS_CHANGED")
    if task_id:
        row = connection.execute("SELECT * FROM mcp_task_sessions WHERE task_id=?", (task_id,)).fetchone()
        require(row is not None and row["principal_id"] == args.principal_id and row["binding_id"] == args.binding_id
                and row["workspace_generation"] == args.workspace_generation
                and row["scoped_pilot_decision_id"] == args.pilot_decision_id and row["closed_at_ms"] is None, "TASK_TARGET_CHANGED")
    return contract


def recover(connection, principal, attempt):
    row = connection.execute("SELECT task_id FROM mcp_task_open_idempotency WHERE principal_id=? AND idempotency_key=?", (principal, attempt + ":task")).fetchone()
    actions = {}
    for lane, (table, _tool, _operation) in LANES.items():
        row_action = connection.execute(f"SELECT action_id FROM {table} WHERE principal_id=? AND idempotency_key=?", (principal, attempt + ":" + lane)).fetchone()
        if row_action:
            actions[lane] = row_action["action_id"]
    return row["task_id"] if row else None, actions


def renew(client, task_id, generation):
    lease = client.call("task_control", {"operation": "writer_claim", "task_id": task_id}).get("writer_lease", {})
    require(lease.get("state") == "held" and lease.get("task_id") == task_id and lease.get("lease_generation") == generation, "ORIGINAL_WRITER_LEASE_GENERATION_CHANGED")


def unknown(result):
    return (result.get("reconciliation_required") is True or result.get("process_state") == "unknown"
            or result.get("action", {}).get("central_lifecycle_state") == "reconcile_required")


def observe(client, lane, action_id, task_id, generation, seconds=OBSERVE_SECONDS):
    _, tool, operation = LANES[lane]
    deadline, last_renewal, last_report = time.monotonic() + seconds, 0, 0
    while True:
        if time.monotonic() - last_renewal >= 20:
            renew(client, task_id, generation)
            last_renewal = time.monotonic()
        result = client.call(tool, {"operation": operation, "action_id": action_id})
        action = result.get("action", {})
        require(action.get("action_id") == action_id, "OBSERVATION_ACTION_CHANGED")
        if action.get("settled_at_ms") is not None or unknown(result):
            return result
        if time.monotonic() - last_report >= 45:
            emit("observing_original_action", lane=lane, action_id=action_id, state=action.get("central_lifecycle_state"))
            last_report = time.monotonic()
        require(time.monotonic() < deadline, "ORIGINAL_ACTION_OBSERVATION_TIMEOUT")
        time.sleep(0.75)


def receipt(connection, result, relay_key, args, contract, task_id, generation, actor, kind):
    action_id = result["action"]["action_id"]
    relay = result.get(relay_key, {})
    row = connection.execute("SELECT receipt_state,payload_json FROM receipts WHERE receipt_id=? AND action_id=?", (relay.get("receipt_id"), action_id)).fetchone()
    require(row is not None and row["receipt_state"] == "completed", "VERIFIED_RECEIPT_NOT_FOUND")
    payload = json.loads(row["payload_json"])
    runtime = {"activation_epoch_id": args.activation_epoch, "process_instance_id": args.process_instance_id,
               "server_instance_id": args.server_instance_id, "tool_contract_sha256": args.local_tool_contract_sha256}
    require(payload.get("runtime_identity") == runtime and payload.get("facade_contract") == contract
            and payload.get("actor") == {"client_id": actor, "client_type": "electron"}
            and payload.get("operation_kind") == kind and payload.get("response_sha256") == relay.get("response_sha256"), "RECEIPT_IDENTITY_NOT_EXACT")
    action = connection.execute("SELECT task_id FROM mcp_task_action_links WHERE action_id=?", (action_id,)).fetchone()
    require(action is not None and action["task_id"] == task_id, "ACTION_TASK_CHANGED")
    if kind != "control_plane_bounded_file_read":
        require(payload.get("task_id") == task_id and payload.get("writer_lease_generation") == generation, "RECEIPT_TASK_OR_LEASE_CHANGED")
    attempts = connection.execute("SELECT attempt_id,attempt_number FROM delivery_attempts WHERE action_id=? ORDER BY attempt_number", (action_id,)).fetchall()
    require(len(attempts) == 1 and attempts[0]["attempt_number"] == 1, "UNEXPECTED_DELIVERY_ATTEMPTS")
    proof = {"receipt_id": relay["receipt_id"], "action_id": action_id, "attempt_id": attempts[0]["attempt_id"],
             "attempt_number": 1, "response_sha256": payload["response_sha256"], "runtime_identity": runtime}
    return payload, proof


def envelope(index):
    preimage, final = fixture_content(index).encode(), fixture_content(index, True).encode()
    text = (f"*** Begin Patch\n*** Write Exact File: {fixture_path(index)}\n"
            f"@@ encoding=zlib-base64 preimage_sha256={sha(preimage)} postimage_sha256={sha(final)}\n"
            f"+{base64.b64encode(zlib.compress(final)).decode()}\n*** End Patch\n")
    return text, sha(preimage), sha(final)


def summary(result):
    action = result.get("action", {})
    return {"action_id": action.get("action_id"), "settled_at_ms": action.get("settled_at_ms"),
            "state": action.get("central_lifecycle_state"), "execution": result.get("execution"),
            "process_state": result.get("process_state"), "reconciliation_required": unknown(result)}


def run(args):
    port, connection = service_state(args)
    client = Mcp(port, credential(args, connection))
    attempt = "parallel-native-first-20261012:" + args.attempt_id
    task_id = generation = None
    actions, proofs = {}, {}
    owned = False
    outcome = {"ok": False, "attempt_id": args.attempt_id, "binding_id": args.binding_id,
               "workspace_id": args.workspace_id, "workspace_generation": args.workspace_generation,
               "service_pid": args.service_pid, "proofs": proofs, "semantic_acceptance_performed": False,
               "fixture_preparation": "local_seed_separate_from_remote_read_patch_proof"}
    started = time.monotonic()
    try:
        require(recover(connection, args.principal_id, attempt) == (None, {}), "ATTEMPT_ALREADY_USED_DO_NOT_REDISPATCH")
        owned = True
        contract = check_target(args, connection, client)
        require(connection.execute("SELECT COUNT(*) FROM mcp_task_sessions WHERE binding_id=? AND closed_at_ms IS NULL", (args.binding_id,)).fetchone()[0] == 0, "CURRENT_TARGET_HAS_OPEN_TASK")
        require(connection.execute("SELECT COUNT(*) FROM actions WHERE device_id=? AND workspace_id=? AND workspace_generation=? AND settled_at_ms IS NULL", (args.device_id, args.workspace_id, args.workspace_generation)).fetchone()[0] == 0, "CURRENT_TARGET_HAS_UNSETTLED_ACTION")
        opened = client.call("workspace_context", {"operation": "task_open", "binding_id": args.binding_id,
            "label": "Native first 100 reads 20 patches 10 Node jobs and Git canary", "idempotency_key": attempt + ":task"})
        task_id = opened.get("task", {}).get("task_id")
        require(isinstance(task_id, str) and re.fullmatch(r"task_[a-f0-9]{32}", task_id), "TASK_HANDLE_INVALID")
        lease = client.call("task_control", {"operation": "writer_claim", "task_id": task_id}).get("writer_lease", {})
        require(lease.get("state") == "held" and lease.get("task_id") == task_id and lease.get("binding_id") == args.binding_id, "WRITER_LEASE_NOT_HELD")
        generation = lease["lease_generation"]
        emit("task_and_writer_held", task_id=task_id, writer_lease_generation=generation)

        def queue(lane, tool, arguments):
            require(check_target(args, connection, client, task_id) == contract, "FACADE_CONTRACT_CHANGED")
            renew(client, task_id, generation)
            require(lane not in recover(connection, args.principal_id, attempt)[1], "LANE_ALREADY_USED_DO_NOT_REDISPATCH")
            queued = client.call(tool, {**arguments, "binding_id": args.binding_id, "task_id": task_id,
                "idempotency_key": attempt + ":" + lane, "expected_facade_contract": contract})
            action_id = queued.get("action_id")
            require(isinstance(action_id, str) and re.fullmatch(r"act_[a-f0-9]{32}", action_id), "ACTION_HANDLE_INVALID")
            require(queued.get("replayed") is False, "UNEXPECTED_REPLAY")
            actions[lane] = action_id
            emit("queued_original_action", lane=lane, action_id=action_id, intent_digest=queued.get("intent_digest"))
            result = observe(client, lane, action_id, task_id, generation)
            require(result.get("action", {}).get("settled_at_ms") is not None and not unknown(result), "ORIGINAL_ACTION_NOT_SETTLED")
            return result

        def read(lane, path, expected):
            result = queue(lane, "workspace_context", {"operation": "read_file", "path": path,
                "start_line": 1, "max_lines": 20, "max_bytes": 4096})
            file = result.get("file_read", {}).get("file", {})
            require(result.get("execution") == "completed_file_read_relay" and result.get("file_accessed") is True
                    and file.get("path") == path and file.get("content") == expected
                    and file.get("content_sha256") == sha(expected.encode()) and file.get("truncated") is False
                    and file.get("total_bytes") == len(expected.encode()) and file.get("bytes_read") == len(expected.encode()), "EXACT_READ_NOT_VERIFIED")
            _, proof = receipt(connection, result, "file_read", args, contract, task_id, generation,
                               "electron-control-plane-file-read-bridge", "control_plane_bounded_file_read")
            proofs[lane] = {**proof, "path": path, "content_sha256": file["content_sha256"]}
            emit("read_verified", lane=lane, **proofs[lane])

        for index in range(1, 101):
            read(f"read_{index:03}", fixture_path(index), fixture_content(index))
        emit("wave_completed", wave="100_reads", completed=100)
        for index in range(1, 21):
            text, preimage, postimage = envelope(index)
            lane = f"patch_{index:03}"
            result = queue(lane, "agent_workflow", {"operation": "apply_patch", "path": fixture_path(index),
                "preimage_sha256": preimage, "patch_sha256": sha(text.encode()), "validation_profile": "targeted", "patch_envelope": text})
            require(result.get("patch_applied") is True and result.get("patch_effect_state") == "verified_applied", "EXACT_PATCH_NOT_VERIFIED")
            payload, proof = receipt(connection, result, "patch", args, contract, task_id, generation,
                "electron-control-plane-approved-patch-bridge", "control_plane_approved_patch")
            require(payload.get("file") == {"path": fixture_path(index), "preimage_sha256": preimage,
                    "postimage_sha256": postimage, "bytes_written": len(fixture_content(index, True).encode())}
                    and payload.get("run_id") and payload.get("wave_id") and payload.get("local_semantic_acceptance") == "pending", "PATCH_POSTIMAGE_OR_LINEAGE_NOT_VERIFIED")
            proofs[lane] = {**proof, "postimage_sha256": postimage, "run_id": payload["run_id"], "wave_id": payload["wave_id"]}
            emit("patch_verified", lane=lane, **proofs[lane])
            read(f"readback_{index:03}", fixture_path(index), fixture_content(index, True))
        emit("wave_completed", wave="20_patches_and_readbacks", completed=20)

        jobs = [(f"node_{i:02}", ["node", "--version"], "", "native_safe_command") for i in range(1, 11)]
        jobs += [("git_status", ["git", "status", "--short", "--untracked-files=no"], "", "native_safe_command"),
                 ("git_diff", ["git", "diff", "--stat"], "", "native_safe_command"),
                 ("git_log", ["git", "log", "--oneline", "-n", "3"], "", "native_safe_command")]
        if args.include_approved_build:
            jobs.append(("build", ["node", "trusted-build.js"], FIXTURE, "native_explicit_approval"))
        for lane, argv, cwd, decision in jobs:
            result = queue(lane, "exec_command", {"operation": "exec_run", "argv": argv, "cwd": cwd,
                "timeout_ms": 120000, "max_output_bytes": 32768})
            require(result.get("execution") == "completed_exec_relay" and result.get("process_state") == "completed"
                    and result.get("exit_code") == 0, "ORIGINAL_EXEC_NOT_VERIFIED_SUCCESS")
            payload, proof = receipt(connection, result, "exec", args, contract, task_id, generation,
                                     "electron-control-plane-exec-bridge", "control_plane_exec")
            metadata = {"execution_backend": "native", "isolation_level": "process_container", "policy_decision": decision}
            require(all(payload.get(key) == value and result.get("exec", {}).get(key) == value for key, value in metadata.items()), "NATIVE_ROUTING_RECEIPT_NOT_VERIFIED")
            require(payload.get("local_handle") == result["exec"]["local_handle"] and all(payload.get(key) for key in ("job_id", "command_id", "run_id", "wave_id")), "ORIGINAL_JOB_IDENTITY_NOT_VERIFIED")
            page = client.call("command_control", {"operation": "exec_output", "action_id": actions[lane], "cursor": 0, "max_bytes": 65536})
            require(page.get("has_output") is True and page.get("exit_code") == 0 and page.get("truncated") is False
                    and all(page.get(key) == value for key, value in metadata.items()), "ORIGINAL_OUTPUT_NOT_VERIFIED")
            require(payload.get("status") == "exited" and payload.get("timed_out") is False
                    and payload.get("truncated") is False and payload.get("stderr") == "", "EXEC_TERMINAL_PAYLOAD_INVALID")
            stdout = payload.get("stdout", "")
            if lane.startswith("node_"):
                require(re.fullmatch(r"v\d+\.\d+\.\d+\s*", stdout), "NODE_VERSION_OUTPUT_INVALID")
            if lane == "build":
                require(stdout == build_artifact(), "BUILD_MARKER_NOT_VERIFIED")
            proofs[lane] = {**proof, **metadata, **{key: payload[key] for key in ("job_id", "command_id", "run_id", "wave_id")},
                            "stdout_sha256": sha(stdout.encode()), "output_bytes": payload["output_bytes"]}
            emit("native_job_verified", lane=lane, **proofs[lane])
        require(len({proofs[f"node_{i:02}"]["job_id"] for i in range(1, 11)}) == 10, "NODE_JOBS_NOT_UNIQUE")
        if args.include_approved_build:
            LANES["build_readback"] = READ
            read("build_readback", FIXTURE + "/build-artifact.txt", build_artifact())
        outcome["ok"] = True
        emit("wave_completed", wave="native_exec", node_jobs=10, git_jobs=3, approved_build=args.include_approved_build)
    except Exception as error:
        outcome["error_code"] = error_code(error)
    finally:
        if owned:
            try:
                recovered_task, recovered_actions = recover(connection, args.principal_id, attempt)
                task_id = task_id or recovered_task
                actions.update(recovered_actions)
            except Exception as error:
                outcome["handle_recovery_error"] = error_code(error)
                outcome["ok"] = False
        unresolved = []
        for lane, action_id in actions.items():
            try:
                _, tool, operation = LANES[lane]
                result = client.call(tool, {"operation": operation, "action_id": action_id})
                if result.get("action", {}).get("settled_at_ms") is None and not unknown(result) and task_id and generation:
                    if LANES[lane] == EXEC:
                        client.call("command_control", {"operation": "exec_stop", "action_id": action_id})
                    result = observe(client, lane, action_id, task_id, generation, seconds=120)
                outcome.setdefault("final_action_status", {})[lane] = summary(result)
                if result.get("action", {}).get("settled_at_ms") is None or unknown(result):
                    unresolved.append(lane)
            except Exception as error:
                outcome.setdefault("final_observation_errors", {})[lane] = error_code(error)
                unresolved.append(lane)
        outcome.update({"task_id": task_id, "action_ids": actions, "unresolved_original_actions": unresolved,
                        "requires_reconciliation": bool(unresolved)})
        if task_id and not unresolved and "handle_recovery_error" not in outcome:
            for tool, operation, extra in (("task_control", "writer_release", {"reason": "native_first_canary_finished"}),
                                            ("workspace_context", "task_close", {})):
                try:
                    client.call(tool, {"operation": operation, "task_id": task_id, **extra})
                except Exception as error:
                    outcome[operation + "_error"] = error_code(error)
            try:
                task = connection.execute("SELECT closed_at_ms FROM mcp_task_sessions WHERE task_id=?", (task_id,)).fetchone()
                held = connection.execute("SELECT COUNT(*) FROM mcp_task_writer_leases WHERE task_id=? AND released_at_ms IS NULL", (task_id,)).fetchone()[0]
                outcome["task_closed_verified"] = task is not None and task["closed_at_ms"] is not None
                outcome["writer_released_verified"] = held == 0
                outcome["ok"] = outcome["ok"] and outcome["task_closed_verified"] and held == 0
            except Exception as error:
                outcome["cleanup_verification_error"] = error_code(error)
                outcome["ok"] = False
        elif task_id:
            outcome["cleanup_deferred_pending_effect"] = True
            outcome["ok"] = False
        outcome["elapsed_seconds"] = round(time.monotonic() - started, 3)
        outcome["proof_counts"] = {name: sum(lane.startswith(prefix) for lane in proofs)
                                   for name, prefix in (("reads", "read_"), ("patches", "patch_"), ("readbacks", "readback_"), ("node_jobs", "node_"), ("git_jobs", "git_"))}
        connection.close()
        emit("final", **outcome)
    return 0 if outcome["ok"] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ("principal-id", "grant-id", "device-id", "workspace-id", "binding-id", "workspace-generation",
                  "pilot-decision-id", "activation-epoch", "process-instance-id", "server-instance-id",
                  "local-tool-contract-sha256", "facade-contract-sha256", "serving-mcp-facade-sha256",
                  "serving-node-agent-sha256", "attempt-id", "credential-file"):
        parser.add_argument("--" + field, required=True)
    parser.add_argument("--facade-schema-version", type=int, required=True)
    parser.add_argument("--service-pid", type=int, required=True)
    parser.add_argument("--execute-confirmed-ready-pilot", action="store_true", required=True)
    parser.add_argument("--include-approved-build", action="store_true")
    args = parser.parse_args()
    for key, value in vars(args).items():
        if key.endswith("sha256"):
            require(SHA.fullmatch(value), "CONTRACT_DIGEST_INVALID")
        elif key.endswith("_id") or key.endswith("_generation") or key == "activation_epoch":
            require(IDENTIFIER.fullmatch(value), "IDENTITY_ARGUMENT_INVALID")
    require(re.fullmatch(r"[a-f0-9]{32}", args.attempt_id), "ATTEMPT_ID_INVALID")
    require(args.facade_schema_version >= 32 and args.service_pid > 1, "SERVICE_CONTRACT_ARGUMENT_INVALID")
    if args.include_approved_build:
        LANES["build_readback"] = READ
    return run(args)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        emit("preflight_failed", ok=False, error_code=error_code(error))
        sys.exit(1)
