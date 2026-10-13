"""Dispatch one trusted isolated Node version action, retaining original handles.

Preparation/import performs no live work. Windows policy and automatic idle
retirement are independently observed by the companion sampler. No retry can
redispatch this attempt, and unresolved effects defer task cleanup.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import re
import sys
import time

if "_BASE_CANARY" not in globals():
    spec = importlib.util.spec_from_file_location("reviewed_native_canary", Path(__file__).with_name("run-native-first-canary.py"))
    _BASE_CANARY = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(_BASE_CANARY)
base = _BASE_CANARY
if "_OVERLAP_CANARY" not in globals():
    spec = importlib.util.spec_from_file_location("reviewed_parallel_canary", Path(__file__).with_name("run-parallel-overlap-canary.py"))
    _OVERLAP_CANARY = importlib.util.module_from_spec(spec)
    _OVERLAP_CANARY._BASE_CANARY = base
    spec.loader.exec_module(_OVERLAP_CANARY)
overlap = _OVERLAP_CANARY
LANE = "isolated_node_version"
base.LANES[LANE] = base.EXEC
METADATA = {"execution_backend": "isolated", "isolation_level": "hypervisor", "policy_decision": "isolated_preferred"}


def emit(phase, **values):
    print(json.dumps({"operation": "isolated_idle_shared_mcp_canary", "phase": phase,
                      "observed_at_ms": int(time.time() * 1000), **values}, separators=(",", ":")), flush=True)


def run(options, args):
    port, connection = base.service_state(args)
    client = base.Mcp(port, base.credential(args, connection))
    attempt = "isolated-idle-20261012:" + options.attempt_id
    task_id = generation = None
    action_id = None
    owned = False
    outcome = {"ok": False, "attempt_id": options.attempt_id, "binding_id": args.binding_id,
               "workspace_id": args.workspace_id, "workspace_generation": args.workspace_generation,
               "dispatch_argv": ["node", "--version"], "automatic_vm_idle_proof": "separate_windows_sampler",
               "runtime_restart_performed": False, "sandbox_stop_dispatched": False, "semantic_acceptance_performed": False}
    started = time.monotonic()
    try:
        base.require(base.recover(connection, args.principal_id, attempt) == (None, {}), "ATTEMPT_ALREADY_USED_DO_NOT_REDISPATCH")
        contract = base.check_target(args, connection, client)
        base.require(args.workspace_label == "Codex-web" and not args.retained_unknown_actions, "EXACT_CODEX_SCOPE_REQUIRED")
        base.require(connection.execute("SELECT COUNT(*) FROM mcp_task_sessions WHERE binding_id=? AND closed_at_ms IS NULL",
                     (args.binding_id,)).fetchone()[0] == 0, "CURRENT_TARGET_HAS_OPEN_TASK")
        overlap.verify_existing_unsettled(args, connection)
        owned = True
        opened = client.call("workspace_context", {"operation": "task_open", "binding_id": args.binding_id,
            "label": "One trusted isolated Node version and automatic idle acceptance", "idempotency_key": attempt + ":task"})
        task_id = opened.get("task", {}).get("task_id")
        base.require(isinstance(task_id, str) and re.fullmatch(r"task_[a-f0-9]{32}", task_id), "TASK_HANDLE_INVALID")
        lease = client.call("task_control", {"operation": "writer_claim", "task_id": task_id}).get("writer_lease", {})
        base.require(lease.get("state") == "held" and lease.get("task_id") == task_id
                     and lease.get("binding_id") == args.binding_id, "WRITER_LEASE_NOT_HELD")
        generation = lease["lease_generation"]
        base.require(base.check_target(args, connection, client, task_id) == contract, "FACADE_CONTRACT_CHANGED")
        base.require(LANE not in base.recover(connection, args.principal_id, attempt)[1], "LANE_ALREADY_USED_DO_NOT_REDISPATCH")
        emit("dispatching_one_original_action", task_id=task_id, writer_lease_generation=generation)
        queued = client.call("exec_command", {"operation": "exec_run", "argv": ["node", "--version"], "cwd": "",
            "timeout_ms": 120000, "max_output_bytes": 32768, "binding_id": args.binding_id, "task_id": task_id,
            "idempotency_key": attempt + ":" + LANE, "expected_facade_contract": contract})
        action_id = queued.get("action_id")
        base.require(isinstance(action_id, str) and re.fullmatch(r"act_[a-f0-9]{32}", action_id)
                     and queued.get("replayed") is False, "ORIGINAL_ACTION_HANDLE_INVALID")
        result = base.observe(client, LANE, action_id, task_id, generation, seconds=360)
        base.require(result.get("execution") == "completed_exec_relay" and result.get("process_state") == "completed"
                     and result.get("exit_code") == 0 and not base.unknown(result), "ISOLATED_EXEC_NOT_VERIFIED_SUCCESS")
        payload, proof = base.receipt(connection, result, "exec", args, contract, task_id, generation,
                                     "electron-control-plane-exec-bridge", "control_plane_exec")
        base.require(all(payload.get(key) == value and result.get("exec", {}).get(key) == value for key, value in METADATA.items()),
                     "ISOLATED_ROUTING_NOT_EXACT")
        base.require(payload.get("status") == "exited" and payload.get("timed_out") is False
                     and payload.get("truncated") is False and payload.get("stderr") == ""
                     and re.fullmatch(r"v\d+\.\d+\.\d+\r?\n?", payload.get("stdout", "")), "NODE_VERSION_TERMINAL_OUTPUT_INVALID")
        base.require(payload.get("local_handle") == result["exec"]["local_handle"]
                     and all(payload.get(key) for key in ("job_id", "command_id")), "ORIGINAL_JOB_IDENTITY_NOT_EXACT")
        # A single isolated hypervisor action has stable Job/command/local
        # handles, but the relay does not attach workflow lineage IDs. Keep
        # that exact empty lineage state; native workflow lanes still require
        # both IDs.
        lineage_empty_isolated = (payload.get("execution_backend") == "isolated"
                                  and payload.get("isolation_level") == "hypervisor"
                                  and payload.get("run_id") == "" and payload.get("wave_id") == "")
        base.require(lineage_empty_isolated or all(payload.get(key) for key in ("run_id", "wave_id")),
                     "ORIGINAL_JOB_IDENTITY_NOT_EXACT")
        page = client.call("command_control", {"operation": "exec_output", "action_id": action_id, "cursor": 0, "max_bytes": 65536})
        base.require(page.get("has_output") is True and page.get("exit_code") == 0 and page.get("truncated") is False
                     and all(page.get(key) == value for key, value in METADATA.items()), "ORIGINAL_OUTPUT_NOT_VERIFIED")
        proof.update({key: payload[key] for key in ("job_id", "command_id", "local_handle", "run_id", "wave_id")})
        proof.update({**METADATA, "stdout_sha256": base.sha(payload["stdout"].encode()), "exit_code": 0})
        outcome.update(ok=True, proof=proof, terminal_observed_at_ms=int(time.time() * 1000))
        emit("isolated_terminal_verified", **outcome["proof"], terminal_observed_at_ms=outcome["terminal_observed_at_ms"])
    except Exception as error:
        outcome["error_code"] = base.error_code(error)
    finally:
        unresolved = False
        if owned:
            try:
                original_task, originals = base.recover(connection, args.principal_id, attempt)
                task_id = task_id or original_task
                action_id = action_id or originals.get(LANE)
                base.require(set(originals) <= {LANE}, "UNEXPECTED_ADDITIONAL_ORIGINAL_ACTION")
                if task_id and generation is None:
                    rows = connection.execute("SELECT lease_generation FROM mcp_task_writer_leases WHERE task_id=? AND released_at_ms IS NULL",
                                              (task_id,)).fetchall()
                    base.require(len(rows) <= 1, "ORIGINAL_WRITER_LEASE_AMBIGUOUS")
                    generation = rows[0][0] if rows else None
                if action_id:
                    status = base.observe(client, LANE, action_id, task_id, generation, seconds=120)
                    unresolved = status.get("action", {}).get("settled_at_ms") is None or base.unknown(status)
                    outcome["final_action_status"] = base.summary(status)
            except Exception as error:
                unresolved = True
                outcome["original_handle_recovery_error"] = base.error_code(error)
        outcome.update(task_id=task_id, action_id=action_id, requires_reconciliation=unresolved)
        if task_id and not unresolved:
            try:
                client.call("task_control", {"operation": "writer_release", "task_id": task_id, "reason": "isolated_idle_canary_finished"})
                client.call("workspace_context", {"operation": "task_close", "task_id": task_id})
                task = connection.execute("SELECT closed_at_ms FROM mcp_task_sessions WHERE task_id=?", (task_id,)).fetchone()
                held = connection.execute("SELECT COUNT(*) FROM mcp_task_writer_leases WHERE task_id=? AND released_at_ms IS NULL", (task_id,)).fetchone()[0]
                outcome.update(task_closed_verified=task is not None and task[0] is not None, writer_released_verified=held == 0)
                outcome["ok"] = outcome["ok"] and outcome["task_closed_verified"] and held == 0
            except Exception as error:
                outcome.update(ok=False, cleanup_error=base.error_code(error))
        elif unresolved:
            outcome.update(ok=False, cleanup_deferred_pending_effect=True)
        connection.close()
        outcome["elapsed_seconds"] = round(time.monotonic() - started, 3)
        emit("final", **outcome)
    return 0 if outcome["ok"] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reviewed-pins")
    parser.add_argument("--reviewed-pins-sha256", required=True)
    parser.add_argument("--attempt-id", required=True)
    parser.add_argument("--credential-file", required=True)
    parser.add_argument("--execute-confirmed-isolated-idle-canary", action="store_true", required=True)
    options = parser.parse_args()
    base.require(options.execute_confirmed_isolated_idle_canary and base.SHA.fullmatch(options.reviewed_pins_sha256)
                 and re.fullmatch(r"[a-f0-9]{32}", options.attempt_id), "CANARY_ARGUMENT_INVALID")
    raw = globals().get("_REVIEWED_PINS_BYTES")
    if raw is None:
        file = Path(options.reviewed_pins or "")
        base.require(file.is_absolute() and file.is_file() and file.stat().st_size <= 32768, "REVIEWED_PINS_PATH_INVALID")
        raw = file.read_bytes()
    base.require(len(raw) <= 32768 and base.sha(raw) == options.reviewed_pins_sha256, "REVIEWED_PINS_CHANGED")
    pins = json.loads(raw.decode("utf-8-sig"))
    base.require(pins.get("purpose") == "isolated-idle" and pins.get("isolated_idle_approved") is True,
                 "REVIEWED_ISOLATED_IDLE_APPROVAL_REQUIRED")
    targets = overlap.reviewed_targets(pins, options.credential_file, require_native_fixture=False)
    return run(options, next(item for item in targets if item.workspace_label == "Codex-web"))


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        emit("preflight_failed", ok=False, error_code=base.error_code(error))
        sys.exit(1)
