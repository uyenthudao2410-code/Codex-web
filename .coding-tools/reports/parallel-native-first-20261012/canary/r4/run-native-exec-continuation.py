"""Read-only continuation proof plus fresh native exec actions.

This harness never requeues an action from the original canary.  It accepts the
original failed receipt only when all file-read/patch/readback actions are
terminal, the original task and writer are closed/released, and the sole
missing proof is the standalone exec identity check.  It then opens a fresh
task and runs only new native exec actions, an approved build, and its bounded
artifact readback.
"""

import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path

if "_BASE_CANARY" not in globals():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "reviewed_native_canary", Path(__file__).with_name("run-native-first-canary.py"))
    _BASE_CANARY = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(_BASE_CANARY)
base = _BASE_CANARY

FIXTURE = "tests/fixtures/native-first-canary"
CONTINUATION = "native-exec-continuation-20261013:"
LANES = {
    **{f"node_{i:02}": base.EXEC for i in range(1, 11)},
    "git_status": base.EXEC, "git_diff": base.EXEC, "git_log": base.EXEC,
    "build": base.EXEC, "build_readback": base.READ,
}
base.LANES.update(LANES)
SHA = re.compile(r"[a-f0-9]{64}")
IDENTIFIER = base.IDENTIFIER


def require(condition, code):
    if not condition:
        raise RuntimeError(code)


def sha(value):
    return hashlib.sha256(value).hexdigest()


def error_code(error):
    if isinstance(error, RuntimeError) and re.fullmatch(r"[A-Z][A-Z0-9_]{2,127}", str(error)):
        return str(error)
    return type(error).__name__


def emit(phase, **fields):
    print(json.dumps({"operation": "native_exec_continuation", "phase": phase,
                      "observed_at_ms": int(time.time() * 1000), **fields},
                     separators=(",", ":")), flush=True)


def load_ndjson(path):
    raw = Path(path).read_bytes()
    require(len(raw) <= 8 * 1024 * 1024, "FAILED_RECEIPT_TOO_LARGE")
    rows = [json.loads(line) for line in raw.decode("utf-8-sig").splitlines() if line.strip()]
    require(rows and all(isinstance(row, dict) for row in rows), "FAILED_RECEIPT_INVALID")
    return raw, rows


def validate_failed_receipt(path, expected_sha256):
    if "_FAILED_RECEIPT_BYTES" in globals():
        raw = _FAILED_RECEIPT_BYTES
        require(isinstance(raw, bytes), "FAILED_RECEIPT_INVALID")
        rows = [json.loads(line) for line in raw.decode("utf-8-sig").splitlines() if line.strip()]
    else:
        raw, rows = load_ndjson(path)
    require(SHA.fullmatch(expected_sha256) and sha(raw) == expected_sha256, "FAILED_RECEIPT_HASH_MISMATCH")
    finals = [row for row in rows if row.get("phase") == "final"]
    require(len(finals) == 1, "FAILED_RECEIPT_FINAL_NOT_UNIQUE")
    final = finals[0]
    require(final.get("ok") is False and final.get("error_code") == "ORIGINAL_JOB_IDENTITY_NOT_VERIFIED",
            "FAILED_RECEIPT_WRONG_TERMINAL_FAILURE")
    require(final.get("proof_counts") == {"reads": 100, "patches": 20, "readbacks": 20,
                                           "node_jobs": 0, "git_jobs": 0}, "FAILED_RECEIPT_PARTIAL_COUNTS_INVALID")
    require(final.get("unresolved_original_actions") == [] and final.get("requires_reconciliation") is False,
            "FAILED_RECEIPT_UNRESOLVED_ACTIONS")
    require(final.get("task_closed_verified") is True and final.get("writer_released_verified") is True,
            "FAILED_RECEIPT_TASK_NOT_CLOSED")
    status = final.get("final_action_status", {}).get("node_01", {})
    require(status.get("state") == "completed" and status.get("process_state") == "completed"
            and status.get("reconciliation_required") is False, "FAILED_NODE_ACTION_NOT_TERMINAL")
    require(final.get("task_id", "").startswith("task_") and final.get("attempt_id"),
            "FAILED_RECEIPT_IDENTITY_MISSING")
    return {"sha256": expected_sha256, "record_count": len(rows), "final": final}


def build_artifact():
    data = b"".join(base.fixture_content(i, i <= 20).encode() for i in range(1, 101))
    return "NATIVE_FIRST_CANARY_BUILD_V1 " + sha(data) + "\n"


def validate_exec_result(result, proof, metadata):
    payload = proof
    for value in (payload.get("job_id"), payload.get("command_id"), payload.get("local_handle")):
        require(isinstance(value, str) and bool(value), "ORIGINAL_JOB_IDENTITY_NOT_VERIFIED")
    # Standalone exec permits empty run_id/wave_id.  Bind identity to the
    # action, task, attempt and runtime metadata instead of inventing lineage.
    require(all(payload.get(key) == value and result.get("exec", {}).get(key) == value
                for key, value in metadata.items()), "NATIVE_ROUTING_RECEIPT_NOT_VERIFIED")
    require(payload.get("status") == "exited" and payload.get("timed_out") is False
            and payload.get("truncated") is False and payload.get("stderr") == "", "EXEC_TERMINAL_PAYLOAD_INVALID")


def run(args):
    prior = validate_failed_receipt(args.failed_receipt, args.failed_receipt_sha256)
    final = prior["final"]
    require(final.get("binding_id") == args.binding_id and final.get("workspace_id") == args.workspace_id
            and final.get("workspace_generation") == args.workspace_generation,
            "FAILED_RECEIPT_WORKSPACE_SCOPE_CHANGED")
    identities = [proof.get("runtime_identity") for lane, proof in final.get("proofs", {}).items()
                  if isinstance(proof, dict) and isinstance(proof.get("runtime_identity"), dict)]
    if identities:
        expected_identity = {"activation_epoch_id": args.activation_epoch,
                             "process_instance_id": args.process_instance_id,
                             "server_instance_id": args.server_instance_id,
                             "tool_contract_sha256": args.local_tool_contract_sha256}
        require(all(identity == expected_identity for identity in identities), "FAILED_RECEIPT_RUNTIME_IDENTITY_CHANGED")
    port, connection = base.service_state(args)
    client = base.Mcp(port, base.credential(args, connection))
    attempt = CONTINUATION + args.attempt_id
    task_id = generation = None
    actions, proofs = {}, {}
    owned = False
    outcome = {"ok": False, "attempt_id": args.attempt_id, "source_partial": prior,
               "workspace_id": args.workspace_id, "workspace_generation": args.workspace_generation,
               "binding_id": args.binding_id, "activation_epoch": args.activation_epoch,
               "process_instance_id": args.process_instance_id, "server_instance_id": args.server_instance_id,
               "local_tool_contract_sha256": args.local_tool_contract_sha256,
               "proofs": proofs, "semantic_acceptance_performed": False,
               "fixture_preparation": "reuse_existing_native_first_fixture; no original action replay"}
    started = time.monotonic()
    try:
        require(base.recover(connection, args.principal_id, attempt) == (None, {}), "ATTEMPT_ALREADY_USED_DO_NOT_REDISPATCH")
        contract = base.check_target(args, connection, client)
        require(connection.execute("SELECT COUNT(*) FROM mcp_task_sessions WHERE binding_id=? AND closed_at_ms IS NULL",
                                   (args.binding_id,)).fetchone()[0] == 0, "CURRENT_TARGET_HAS_OPEN_TASK")
        require(connection.execute("SELECT COUNT(*) FROM actions WHERE device_id=? AND workspace_id=? AND workspace_generation=? AND settled_at_ms IS NULL",
                                   (args.device_id, args.workspace_id, args.workspace_generation)).fetchone()[0] == 0,
                "CURRENT_TARGET_HAS_UNSETTLED_ACTION")
        opened = client.call("workspace_context", {"operation": "task_open", "binding_id": args.binding_id,
            "label": "Native exec continuation 10 Node 3 Git approved build", "idempotency_key": attempt + ":task"})
        task_id = opened.get("task", {}).get("task_id")
        require(isinstance(task_id, str) and re.fullmatch(r"task_[a-f0-9]{32}", task_id), "TASK_HANDLE_INVALID")
        lease = client.call("task_control", {"operation": "writer_claim", "task_id": task_id}).get("writer_lease", {})
        require(lease.get("state") == "held" and lease.get("task_id") == task_id, "WRITER_LEASE_NOT_HELD")
        generation = lease["lease_generation"]
        owned = True

        def queue(lane, argv, cwd, decision):
            base.require(base.check_target(args, connection, client, task_id) == contract, "FACADE_CONTRACT_CHANGED")
            base.renew(client, task_id, generation)
            require(lane not in base.recover(connection, args.principal_id, attempt)[1], "LANE_ALREADY_USED_DO_NOT_REDISPATCH")
            queued = client.call("exec_command", {"operation": "exec_run", "argv": argv, "cwd": cwd,
                "timeout_ms": 120000, "max_output_bytes": 32768, "binding_id": args.binding_id,
                "task_id": task_id, "idempotency_key": attempt + ":" + lane, "expected_facade_contract": contract})
            action_id = queued.get("action_id")
            require(isinstance(action_id, str) and re.fullmatch(r"act_[a-f0-9]{32}", action_id), "ACTION_HANDLE_INVALID")
            require(queued.get("replayed") is False, "UNEXPECTED_REPLAY")
            actions[lane] = action_id
            result = base.observe(client, lane, action_id, task_id, generation)
            require(result.get("action", {}).get("settled_at_ms") is not None and not base.unknown(result), "ORIGINAL_ACTION_NOT_SETTLED")
            payload, proof = base.receipt(connection, result, "exec", args, contract, task_id, generation,
                                          "electron-control-plane-exec-bridge", "control_plane_exec")
            metadata = {"execution_backend": "native", "isolation_level": "process_container", "policy_decision": decision}
            validate_exec_result(result, payload, metadata)
            proofs[lane] = {**proof, **metadata, **{key: payload[key] for key in ("job_id", "command_id", "local_handle")},
                            "run_id": payload.get("run_id", ""), "wave_id": payload.get("wave_id", ""),
                            "stdout_sha256": sha(payload.get("stdout", "").encode()), "output_bytes": payload.get("output_bytes")}
            return result, payload

        jobs = [(f"node_{i:02}", ["node", "--version"], "", "native_safe_command") for i in range(1, 11)]
        jobs += [("git_status", ["git", "status", "--short", "--untracked-files=no"], "", "native_safe_command"),
                 ("git_diff", ["git", "diff", "--stat"], "", "native_safe_command"),
                 ("git_log", ["git", "log", "--oneline", "-n", "3"], "", "native_safe_command"),
                 ("build", ["node", "trusted-build.js"], FIXTURE, "native_explicit_approval")]
        require(args.trusted_build_explicitly_approved is True, "EXACT_TRUSTED_BUILD_APPROVAL_REQUIRED")
        require(not (Path(FIXTURE) / "build-artifact.txt").exists(), "BUILD_ARTIFACT_EXISTS_DO_NOT_REDISPATCH")
        for lane, argv, cwd, decision in jobs:
            result, payload = queue(lane, argv, cwd, decision)
            require(result.get("execution") == "completed_exec_relay" and result.get("process_state") == "completed"
                    and result.get("exit_code") == 0, "ORIGINAL_EXEC_NOT_VERIFIED_SUCCESS")
            if lane.startswith("node_"):
                require(re.fullmatch(r"v\d+\.\d+\.\d+\s*", payload.get("stdout", "")), "NODE_VERSION_OUTPUT_INVALID")
            if lane == "build":
                require(payload.get("stdout") == build_artifact(), "BUILD_MARKER_NOT_VERIFIED")
        require(len({proofs[f"node_{i:02}"]["job_id"] for i in range(1, 11)}) == 10, "NODE_JOBS_NOT_UNIQUE")
        read_result = client.call("workspace_context", {"operation": "read_file", "path": FIXTURE + "/build-artifact.txt",
            "start_line": 1, "max_lines": 20, "max_bytes": 4096, "binding_id": args.binding_id, "task_id": task_id,
            "idempotency_key": attempt + ":build_readback", "expected_facade_contract": contract})
        # Artifact readback is a new action; no original read lane is reused.
        action_id = read_result.get("action_id")
        require(isinstance(action_id, str), "BUILD_READBACK_ACTION_INVALID")
        actions["build_readback"] = action_id
        read_result = base.observe(client, "build_readback", action_id, task_id, generation)
        file = read_result.get("file_read", {}).get("file", {})
        require(file.get("content") == build_artifact() and file.get("content_sha256") == sha(build_artifact().encode()), "BUILD_READBACK_NOT_VERIFIED")
        _, proof = base.receipt(connection, read_result, "file_read", args, contract, task_id, generation,
                                "electron-control-plane-file-read-bridge", "control_plane_bounded_file_read")
        proofs["build_readback"] = {**proof, "path": FIXTURE + "/build-artifact.txt", "content_sha256": file["content_sha256"]}
        outcome["ok"] = True
    except Exception as error:
        outcome["error_code"] = error_code(error)
    finally:
        if owned and task_id:
            for tool, operation, extra in (("task_control", "writer_release", {"reason": "native_exec_continuation_finished"}),
                                           ("workspace_context", "task_close", {})):
                try: client.call(tool, {"operation": operation, "task_id": task_id, **extra})
                except Exception as error: outcome[operation + "_error"] = error_code(error)
            try:
                outcome["task_closed_verified"] = connection.execute("SELECT closed_at_ms FROM mcp_task_sessions WHERE task_id=?", (task_id,)).fetchone()[0] is not None
                outcome["writer_released_verified"] = connection.execute("SELECT COUNT(*) FROM mcp_task_writer_leases WHERE task_id=? AND released_at_ms IS NULL", (task_id,)).fetchone()[0] == 0
                outcome["ok"] = outcome["ok"] and outcome["task_closed_verified"] and outcome["writer_released_verified"]
            except Exception as error: outcome["cleanup_verification_error"] = error_code(error); outcome["ok"] = False
        outcome.update({"task_id": task_id, "action_ids": actions, "elapsed_seconds": round(time.monotonic() - started, 3),
                        "proof_counts": {"node_jobs": sum(k.startswith("node_") for k in proofs), "git_jobs": sum(k.startswith("git_") for k in proofs),
                                         "approved_build": int("build" in proofs), "build_readback": int("build_readback" in proofs)}})
        connection.close()
        emit("final", **outcome)
    return 0 if outcome["ok"] else 1


def main():
    parser = argparse.ArgumentParser()
    for field in ("principal-id", "grant-id", "device-id", "workspace-id", "binding-id", "workspace-generation",
                  "pilot-decision-id", "activation-epoch", "process-instance-id", "server-instance-id",
                  "local-tool-contract-sha256", "facade-contract-sha256", "serving-mcp-facade-sha256",
                  "serving-node-agent-sha256", "failed-receipt", "failed-receipt-sha256", "attempt-id", "credential-file"):
        parser.add_argument("--" + field, required=True)
    parser.add_argument("--facade-schema-version", type=int, required=True)
    parser.add_argument("--service-pid", type=int, required=True)
    parser.add_argument("--trusted-build-explicitly-approved", action="store_true", required=True)
    parser.add_argument("--execute-confirmed-continuation", action="store_true", required=True)
    args = parser.parse_args()
    require(args.execute_confirmed_continuation and args.facade_schema_version >= 32 and args.service_pid > 1, "CONTINUATION_EXECUTION_ARGUMENT_INVALID")
    require(re.fullmatch(r"[a-f0-9]{32}", args.attempt_id), "ATTEMPT_ID_INVALID")
    for key, value in vars(args).items():
        if key.endswith("sha256"): require(SHA.fullmatch(value), "CONTRACT_DIGEST_INVALID")
        elif key.endswith("_id") or key.endswith("_generation") or key in {"activation_epoch", "attempt_id"}: require(IDENTIFIER.fullmatch(value), "IDENTITY_ARGUMENT_INVALID")
    return run(args)


if __name__ == "__main__":
    try: sys.exit(main())
    except Exception as error:
        emit("preflight_failed", ok=False, error_code=error_code(error)); sys.exit(1)
