"""Run one packaged-candidate native child-token probe through the live MCP."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import re
import sys
import time

if "_BASE_CANARY" in globals():
    base = _BASE_CANARY
else:
    BASE_PATH = Path(__file__).resolve().parents[1] / "r4" / "run-native-first-canary.py"
    spec = importlib.util.spec_from_file_location("native_first_base", BASE_PATH)
    base = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(base)

LANE = "token_probe"
base.LANES[LANE] = base.EXEC
TOKEN_SCRIPT = ".coding-tools/reports/parallel-native-first-20261012/canary/r5/token-child-launcher.js"
TOKEN_ARGV = ["node", TOKEN_SCRIPT]
METADATA = {"execution_backend": "native", "isolation_level": "process_container", "policy_decision": "native_explicit_approval"}


def emit(phase, **values):
    print(json.dumps({"operation": "packaged_native_child_token_canary", "phase": phase,
                      "observed_at_ms": int(time.time() * 1000), **values}, separators=(",", ":")), flush=True)


def run(args):
    port, connection = base.service_state(args)
    client = base.Mcp(port, base.credential(args, connection))
    attempt = "packaged-token-20261013:" + args.attempt_id
    task_id = generation = action_id = None
    owned = False
    outcome = {"ok": False, "attempt_id": args.attempt_id, "binding_id": args.binding_id,
               "workspace_id": args.workspace_id, "workspace_generation": args.workspace_generation,
               "dispatch_argv": TOKEN_ARGV, "semantic_acceptance_performed": False,
               "production_policy_mutation_performed": True}
    started = time.monotonic()
    try:
        base.require(base.recover(connection, args.principal_id, attempt) == (None, {}), "ATTEMPT_ALREADY_USED_DO_NOT_REDISPATCH")
        contract = base.check_target(args, connection, client)
        base.require(args.workspace_id == "workspace_f93b5bac9dc74fae9cea66f44c4ebc94", "EXACT_CODEX_SCOPE_REQUIRED")
        base.require(connection.execute("SELECT COUNT(*) FROM mcp_task_sessions WHERE binding_id=? AND closed_at_ms IS NULL", (args.binding_id,)).fetchone()[0] == 0, "CURRENT_TARGET_HAS_OPEN_TASK")
        base.require(connection.execute("SELECT COUNT(*) FROM actions WHERE device_id=? AND workspace_id=? AND workspace_generation=? AND settled_at_ms IS NULL", (args.device_id, args.workspace_id, args.workspace_generation)).fetchone()[0] == 0, "CURRENT_TARGET_HAS_UNSETTLED_ACTION")
        owned = True
        opened = client.call("workspace_context", {"operation": "task_open", "binding_id": args.binding_id,
            "label": "Packaged native child token probe", "idempotency_key": attempt + ":task"})
        task_id = opened.get("task", {}).get("task_id")
        base.require(isinstance(task_id, str) and re.fullmatch(r"task_[a-f0-9]{32}", task_id), "TASK_HANDLE_INVALID")
        lease = client.call("task_control", {"operation": "writer_claim", "task_id": task_id}).get("writer_lease", {})
        base.require(lease.get("state") == "held" and lease.get("task_id") == task_id
                     and lease.get("binding_id") == args.binding_id, "WRITER_LEASE_NOT_HELD")
        generation = lease["lease_generation"]
        emit("dispatching_one_original_action", task_id=task_id, writer_lease_generation=generation)
        queued = client.call("exec_command", {"operation": "exec_run", "argv": TOKEN_ARGV, "cwd": "",
            "timeout_ms": 30_000, "max_output_bytes": 65_536, "binding_id": args.binding_id, "task_id": task_id,
            "idempotency_key": attempt + ":" + LANE, "expected_facade_contract": contract})
        action_id = queued.get("action_id")
        base.require(isinstance(action_id, str) and re.fullmatch(r"act_[a-f0-9]{32}", action_id)
                     and queued.get("replayed") is False, "ORIGINAL_ACTION_HANDLE_INVALID")
        result = base.observe(client, LANE, action_id, task_id, generation, seconds=180)
        base.require(result.get("execution") == "completed_exec_relay" and result.get("process_state") == "completed"
                     and result.get("exit_code") == 0 and not base.unknown(result), "TOKEN_EXEC_NOT_VERIFIED_SUCCESS")
        payload, proof = base.receipt(connection, result, "exec", args, contract, task_id, generation,
                                      "electron-control-plane-exec-bridge", "control_plane_exec")
        base.require(all(payload.get(key) == value and result.get("exec", {}).get(key) == value for key, value in METADATA.items()), "NATIVE_ROUTING_RECEIPT_NOT_VERIFIED")
        base.require(payload.get("status") == "exited" and payload.get("timed_out") is False
                     and payload.get("truncated") is False and payload.get("stderr") == "", "EXEC_TERMINAL_PAYLOAD_INVALID")
        base.require(payload.get("local_handle") == result["exec"].get("local_handle")
                     and all(payload.get(key) for key in ("job_id", "command_id")), "DURABLE_JOB_IDENTITY_NOT_EXACT")
        page = client.call("command_control", {"operation": "exec_output", "action_id": action_id, "cursor": 0, "max_bytes": 65_536})
        base.require(page.get("has_output") is True and page.get("exit_code") == 0 and page.get("truncated") is False
                     and all(page.get(key) == value for key, value in METADATA.items()), "ORIGINAL_OUTPUT_NOT_VERIFIED")
        launcher = json.loads(str(payload.get("stdout") or "").strip())
        facts = launcher.get("child_facts") if isinstance(launcher, dict) else None
        base.require(isinstance(facts, dict) and facts.get("complete") is True
                     and facts.get("open_process_token") is True and facts.get("app_container") is True
                     and facts.get("elevated") is False and isinstance(facts.get("integrity_rid"), int)
                     and facts["integrity_rid"] < 12_288 and facts.get("integrity_sid_valid") is True
                     and facts.get("admin_sid_query_ok") is True and facts.get("administrator_group_deny_only") is True
                     and facts.get("administrator_group_enabled") is False
                     and facts.get("sensitive_privileges_enabled") == 0
                     and facts.get("sensitive_luid_lookup_success_count") == 11
                     and all(value == 0 for value in (facts.get("query_errors") or {}).values()), "TOKEN_FACTS_NOT_RESTRICTED")
        proof.update({key: payload[key] for key in ("job_id", "command_id", "local_handle")})
        proof.update({**METADATA, "stdout_sha256": base.sha(payload["stdout"].encode()), "exit_code": 0})
        outcome.update(ok=True, proof=proof, launcher_report=launcher, child_facts=facts,
                       terminal_observed_at_ms=int(time.time() * 1000), execution_owner_job_id=payload["job_id"])
        emit("terminal_token_verified", **proof, execution_owner_job_id=payload["job_id"], child_facts=facts)
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
                client.call("task_control", {"operation": "writer_release", "task_id": task_id, "reason": "packaged_token_probe_finished"})
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
    for field in ("principal-id", "grant-id", "device-id", "workspace-id", "binding-id", "workspace-generation",
                  "pilot-decision-id", "activation-epoch", "process-instance-id", "server-instance-id",
                  "local-tool-contract-sha256", "facade-contract-sha256", "serving-mcp-facade-sha256",
                  "serving-node-agent-sha256", "attempt-id", "credential-file"):
        parser.add_argument("--" + field, required=True)
    parser.add_argument("--facade-schema-version", type=int, required=True)
    parser.add_argument("--service-pid", type=int, required=True)
    parser.add_argument("--execute-confirmed-packaged-token", action="store_true", required=True)
    args = parser.parse_args()
    base.require(args.execute_confirmed_packaged_token and re.fullmatch(r"[a-f0-9]{32}", args.attempt_id), "TOKEN_CANARY_ARGUMENT_INVALID")
    for key, value in vars(args).items():
        if key.endswith("sha256"):
            base.require(base.SHA.fullmatch(value), "CONTRACT_DIGEST_INVALID")
        elif key.endswith("_id") or key.endswith("_generation") or key == "activation_epoch":
            base.require(base.IDENTIFIER.fullmatch(value), "IDENTITY_ARGUMENT_INVALID")
    base.require(args.facade_schema_version >= 32 and args.service_pid > 1, "SERVICE_CONTRACT_ARGUMENT_INVALID")
    return run(args)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        emit("preflight_failed", ok=False, error_code=base.error_code(error))
        sys.exit(1)
