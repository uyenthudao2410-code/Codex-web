"""Resume only the unproved exec lanes of a terminal continuation.

The failed continuation receipt is immutable input.  Its ten Node jobs and
git_status proof are retained and never dispatched again.  This helper starts
a fresh task for git_diff, git_log, the explicitly approved build, and its
artifact readback.  Exit-zero stderr is retained as bounded process output:
the exec bridge contract treats stdout/stderr as separate output streams and
defines success by terminal status, exit code, timeout and truncation flags.
"""
import argparse, base64, hashlib, importlib.util, json, re, sys, time
from pathlib import Path

if "_BASE_CANARY" not in globals():
    spec = importlib.util.spec_from_file_location("reviewed_native_canary", Path(__file__).with_name("run-native-first-canary.py"))
    _BASE_CANARY = importlib.util.module_from_spec(spec); spec.loader.exec_module(_BASE_CANARY)
base = _BASE_CANARY
FIXTURE = "tests/fixtures/native-first-canary"
RESUME_PREFIX = "native-exec-continuation-resume-20261013:"
SHA = re.compile(r"[a-f0-9]{64}")
IDENTIFIER = base.IDENTIFIER

def require(condition, code):
    if not condition: raise RuntimeError(code)
def sha(value): return hashlib.sha256(value).hexdigest()
def error_code(error):
    value = str(error)
    return value if isinstance(error, RuntimeError) and re.fullmatch(r"[A-Z][A-Z0-9_]{2,127}", value) else type(error).__name__
def emit(phase, **fields):
    print(json.dumps({"operation": "native_exec_continuation_resume", "phase": phase,
                      "observed_at_ms": int(time.time() * 1000), **fields}, separators=(",", ":")), flush=True)

def load_prior(path, expected_hash):
    raw = _PRIOR_RECEIPT_BYTES if "_PRIOR_RECEIPT_BYTES" in globals() else Path(path).read_bytes()
    require(isinstance(raw, bytes) and len(raw) <= 8 * 1024 * 1024 and SHA.fullmatch(expected_hash) and sha(raw) == expected_hash, "PRIOR_CONTINUATION_HASH_MISMATCH")
    rows = [json.loads(line) for line in raw.decode("utf-8-sig").splitlines() if line.strip()]
    finals = [row for row in rows if row.get("phase") == "final" and row.get("operation") == "native_exec_continuation"]
    require(len(finals) == 1, "PRIOR_CONTINUATION_FINAL_NOT_UNIQUE")
    final = finals[0]
    require(final.get("ok") is False and final.get("error_code") == "EXEC_TERMINAL_PAYLOAD_INVALID"
            and final.get("task_closed_verified") is True and final.get("writer_released_verified") is True,
            "PRIOR_CONTINUATION_FAILURE_NOT_SAFE_TO_RESUME")
    require(final.get("proof_counts") == {"node_jobs": 10, "git_jobs": 1, "approved_build": 0, "build_readback": 0},
            "PRIOR_CONTINUATION_PROOF_COUNTS_INVALID")
    proofs = final.get("proofs", {})
    nodes = [proofs.get(f"node_{i:02}") for i in range(1, 11)]
    require(all(isinstance(proof, dict) for proof in nodes) and isinstance(proofs.get("git_status"), dict), "PRIOR_CONTINUATION_PROOFS_INCOMPLETE")
    require(len({proof.get("job_id") for proof in nodes}) == 10, "PRIOR_NODE_JOBS_NOT_UNIQUE")
    for proof in nodes + [proofs["git_status"]]:
        require(proof.get("job_id") and proof.get("command_id") and proof.get("local_handle")
                and proof.get("execution_backend") == "native" and proof.get("isolation_level") == "process_container",
                "PRIOR_NATIVE_JOB_PROOF_INVALID")
    # The failed lane may have a durable action id even though its payload was
    # rejected by the old harness.  It has no proof and is therefore eligible
    # for a fresh, separately idempotent resume lane; no original action id is
    # ever reused by this helper.
    require(all(key not in proofs for key in ("git_diff", "git_log", "build", "build_readback")), "PRIOR_UNPROVED_LANE_ALREADY_PROVED")
    return {"sha256": expected_hash, "record_count": len(rows), "final": final}

def build_artifact():
    data = b"".join(base.fixture_content(i, i <= 20).encode() for i in range(1, 101))
    return "NATIVE_FIRST_CANARY_BUILD_V1 " + sha(data) + "\n"

def validate_exec(result, payload, metadata, allow_stderr=False):
    require(all(payload.get(key) == value and result.get("exec", {}).get(key) == value for key, value in metadata.items()), "NATIVE_ROUTING_RECEIPT_NOT_VERIFIED")
    require(payload.get("job_id") and payload.get("command_id") and payload.get("local_handle"), "EXEC_IDENTITY_NOT_VERIFIED")
    require(payload.get("status") == "exited" and payload.get("exit_code") == 0 and payload.get("timed_out") is False and payload.get("truncated") is False,
            "EXEC_TERMINAL_PAYLOAD_INVALID")
    if not allow_stderr: require(payload.get("stderr") == "", "EXEC_STDERR_NOT_ALLOWED")
    else: require(isinstance(payload.get("stderr"), str) and len(payload["stderr"].encode()) <= 65536, "EXEC_STDERR_BOUND_INVALID")

def run(args):
    prior = load_prior(args.prior_receipt, args.prior_receipt_sha256)
    port, connection = base.service_state(args); client = base.Mcp(port, base.credential(args, connection))
    attempt = RESUME_PREFIX + args.attempt_id; task_id = generation = None; owned = False; actions = {}; proofs = {}
    outcome = {"ok": False, "attempt_id": args.attempt_id, "source_continuation": prior,
               "source_continuation_sha256": args.prior_receipt_sha256, "workspace_id": args.workspace_id,
               "workspace_generation": args.workspace_generation, "binding_id": args.binding_id,
               "activation_epoch": args.activation_epoch, "process_instance_id": args.process_instance_id,
               "server_instance_id": args.server_instance_id, "local_tool_contract_sha256": args.local_tool_contract_sha256,
               "proofs": proofs, "semantic_acceptance_performed": False}
    started = time.monotonic()
    try:
        require(base.recover(connection, args.principal_id, attempt) == (None, {}), "RESUME_ATTEMPT_ALREADY_USED")
        contract = base.check_target(args, connection, client)
        require(connection.execute("SELECT COUNT(*) FROM mcp_task_sessions WHERE binding_id=? AND closed_at_ms IS NULL", (args.binding_id,)).fetchone()[0] == 0, "CURRENT_TARGET_HAS_OPEN_TASK")
        opened = client.call("workspace_context", {"operation": "task_open", "binding_id": args.binding_id,
            "label": "Native exec continuation resume git diff/log approved build", "idempotency_key": attempt + ":task"})
        task_id = opened.get("task", {}).get("task_id"); require(isinstance(task_id, str) and re.fullmatch(r"task_[a-f0-9]{32}", task_id), "TASK_HANDLE_INVALID")
        lease = client.call("task_control", {"operation": "writer_claim", "task_id": task_id}).get("writer_lease", {})
        require(lease.get("state") == "held" and lease.get("task_id") == task_id, "WRITER_LEASE_NOT_HELD"); generation = lease["lease_generation"]; owned = True
        def queue(lane, argv, cwd, decision, allow_stderr=False):
            require(base.check_target(args, connection, client, task_id) == contract, "FACADE_CONTRACT_CHANGED"); base.renew(client, task_id, generation)
            queued = client.call("exec_command", {"operation": "exec_run", "argv": argv, "cwd": cwd, "timeout_ms": 120000,
                "max_output_bytes": 32768, "binding_id": args.binding_id, "task_id": task_id,
                "idempotency_key": attempt + ":" + lane, "expected_facade_contract": contract})
            action_id = queued.get("action_id"); require(isinstance(action_id, str) and re.fullmatch(r"act_[a-f0-9]{32}", action_id), "ACTION_HANDLE_INVALID"); require(queued.get("replayed") is False, "UNEXPECTED_REPLAY")
            actions[lane] = action_id; result = base.observe(client, lane, action_id, task_id, generation)
            require(result.get("action", {}).get("settled_at_ms") is not None and not base.unknown(result), "NEW_ACTION_NOT_SETTLED")
            payload, proof = base.receipt(connection, result, "exec", args, contract, task_id, generation, "electron-control-plane-exec-bridge", "control_plane_exec")
            metadata = {"execution_backend": "native", "isolation_level": "process_container", "policy_decision": decision}
            validate_exec(result, payload, metadata, allow_stderr)
            proofs[lane] = {**proof, **metadata, **{key: payload[key] for key in ("job_id", "command_id", "local_handle")},
                            "run_id": payload.get("run_id", ""), "wave_id": payload.get("wave_id", ""),
                            "stdout_sha256": sha(payload.get("stdout", "").encode()), "output_bytes": payload.get("output_bytes"),
                            "stderr_sha256": sha(payload.get("stderr", "").encode()), "stderr_bytes": len(payload.get("stderr", "").encode()),
                            "stderr_policy": "bounded_exit_zero" if allow_stderr else "empty_required"}
            return result, payload
        for lane, argv, cwd, decision, allow_stderr in [
            ("git_diff", ["git", "diff", "--stat"], "", "native_safe_command", True),
            ("git_log", ["git", "log", "--oneline", "-n", "3"], "", "native_safe_command", True),
            ("build", ["node", "trusted-build.js"], FIXTURE, "native_explicit_approval", False)]:
            result, payload = queue(lane, argv, cwd, decision, allow_stderr)
            require(result.get("execution") == "completed_exec_relay" and result.get("process_state") == "completed", "EXEC_RELAY_NOT_COMPLETED")
            if lane == "build": require(payload.get("stdout") == build_artifact(), "BUILD_MARKER_NOT_VERIFIED")
        read_result = client.call("workspace_context", {"operation": "read_file", "path": FIXTURE + "/build-artifact.txt", "start_line": 1, "max_lines": 20, "max_bytes": 4096,
            "binding_id": args.binding_id, "task_id": task_id, "idempotency_key": attempt + ":build_readback", "expected_facade_contract": contract})
        action_id = read_result.get("action_id"); require(isinstance(action_id, str), "BUILD_READBACK_ACTION_INVALID"); actions["build_readback"] = action_id
        read_result = base.observe(client, "build_readback", action_id, task_id, generation); file = read_result.get("file_read", {}).get("file", {})
        require(file.get("content") == build_artifact() and file.get("content_sha256") == sha(build_artifact().encode()), "BUILD_READBACK_NOT_VERIFIED")
        _, proof = base.receipt(connection, read_result, "file_read", args, contract, task_id, generation, "electron-control-plane-file-read-bridge", "control_plane_bounded_file_read")
        proofs["build_readback"] = {**proof, "path": FIXTURE + "/build-artifact.txt", "content_sha256": file["content_sha256"]}; outcome["ok"] = True
    except Exception as error: outcome["error_code"] = error_code(error)
    finally:
        if owned and task_id:
            for tool, operation, extra in (("task_control", "writer_release", {"reason": "native_exec_continuation_resume_finished"}), ("workspace_context", "task_close", {})):
                try: client.call(tool, {"operation": operation, "task_id": task_id, **extra})
                except Exception as error: outcome[operation + "_error"] = error_code(error)
            try:
                outcome["task_closed_verified"] = connection.execute("SELECT closed_at_ms FROM mcp_task_sessions WHERE task_id=?", (task_id,)).fetchone()[0] is not None
                outcome["writer_released_verified"] = connection.execute("SELECT COUNT(*) FROM mcp_task_writer_leases WHERE task_id=? AND released_at_ms IS NULL", (task_id,)).fetchone()[0] == 0
                outcome["ok"] = outcome["ok"] and outcome["task_closed_verified"] and outcome["writer_released_verified"]
            except Exception as error: outcome["cleanup_verification_error"] = error_code(error); outcome["ok"] = False
        outcome.update({"task_id": task_id, "action_ids": actions, "elapsed_seconds": round(time.monotonic() - started, 3),
                        "proof_counts": {"git_jobs": sum(k in ("git_diff", "git_log") for k in proofs), "approved_build": int("build" in proofs), "build_readback": int("build_readback" in proofs)}})
        connection.close(); emit("final", **outcome)
    return 0 if outcome["ok"] else 1

def main():
    parser = argparse.ArgumentParser()
    for field in ("principal-id", "grant-id", "device-id", "workspace-id", "binding-id", "workspace-generation", "pilot-decision-id", "activation-epoch", "process-instance-id", "server-instance-id", "local-tool-contract-sha256", "facade-contract-sha256", "serving-mcp-facade-sha256", "serving-node-agent-sha256", "prior-receipt", "prior-receipt-sha256", "attempt-id", "credential-file"): parser.add_argument("--" + field, required=True)
    parser.add_argument("--facade-schema-version", type=int, required=True); parser.add_argument("--service-pid", type=int, required=True); parser.add_argument("--trusted-build-explicitly-approved", action="store_true", required=True); parser.add_argument("--execute-confirmed-resume", action="store_true", required=True)
    args = parser.parse_args(); require(args.execute_confirmed_resume and args.trusted_build_explicitly_approved and args.facade_schema_version >= 32 and args.service_pid > 1, "RESUME_EXECUTION_ARGUMENT_INVALID"); require(re.fullmatch(r"[a-f0-9]{32}", args.attempt_id), "ATTEMPT_ID_INVALID")
    for key, value in vars(args).items():
        if key.endswith("sha256"): require(SHA.fullmatch(value), "CONTRACT_DIGEST_INVALID")
        elif key.endswith("_id") or key.endswith("_generation") or key in {"activation_epoch", "attempt_id"}: require(IDENTIFIER.fullmatch(value), "IDENTITY_ARGUMENT_INVALID")
    return run(args)

if __name__ == "__main__":
    try: sys.exit(main())
    except Exception as error: emit("preflight_failed", ok=False, error_code=error_code(error)); sys.exit(1)
