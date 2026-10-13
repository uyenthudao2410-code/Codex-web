"""One supported packaged scoped poll; original-only action selection is unavailable."""
import argparse
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import re
import sys
import time

sys.dont_write_bytecode = True


def require(condition, code):
    if not condition:
        raise RuntimeError(code)


def invoke(agent, args, pins, lane):
    identity = agent.observed_runtime_identity(agent.recovery_identity_observation(args, Path(args.project_root)))
    expected = {"runtime_instance_id": pins["process_instance_id"], "mcp_server_instance_id": pins["server_instance_id"],
                "activation_epoch": pins["activation_epoch"], "contract_version": "sha256:" + pins["local_tool_contract_sha256"]}
    require(identity == expected, "EXACT_CURRENT_READY_RUNTIME_REQUIRED")
    pollers = {"read": agent.poll_file_read_once, "patch": agent.poll_approved_patch_once, "exec": agent.poll_exec_once}
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        code = pollers[lane](args)
    require(code == 0, "SUPPORTED_SCOPED_POLL_FAILED")
    lines = output.getvalue().splitlines()
    require(len(lines) == 1 and len(lines[0].encode()) <= 65536, "BOUNDED_SINGLE_POLL_RECEIPT_REQUIRED")
    receipt = json.loads(lines[0])
    require(isinstance(receipt, dict), "SCOPED_POLL_RECEIPT_REQUIRED")
    # Return only identifiers, enum states and counts already projected by poller.
    allowed = {"execution", "reason", "received_action_ids", "completed_action_ids", "failed_action_ids", "stopped_action_ids",
               "rejected_action_ids", "unknown_action_ids", "submitted_receipts", "running_action_ids", "resumed",
               "acknowledged_stop_action_ids", "pending_stop_action_ids"}
    return {key: value for key, value in receipt.items() if key in allowed}


def active_original(file):
    require(file.is_file() and file.stat().st_size <= 2 * 1024 * 1024, "BOUNDED_ACTIVE_CANARY_RECEIPT_REQUIRED")
    pending = {}
    for line in file.read_text(encoding="utf-8-sig").splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue  # Tee may be appending the final line.
        if row.get("operation") != "native_first_shared_mcp_canary":
            continue
        phase = row.get("phase")
        if phase == "final":
            return None, row
        if phase == "preflight_failed":
            return None, {"ok": False, "error_code": row.get("error_code", "CANARY_PREFLIGHT_FAILED")}
        lane = row.get("lane")
        if phase == "queued_original_action":
            require(re.fullmatch(r"act_[a-f0-9]{32}", row.get("action_id", "")), "ORIGINAL_ACTION_IDENTIFIER_REQUIRED")
            if re.fullmatch(r"(?:read|readback)_\d{3}", lane or "") or lane == "build_readback":
                kind = "read"
            elif re.fullmatch(r"patch_\d{3}", lane or ""):
                kind = "patch"
            else:
                require(re.fullmatch(r"node_\d{2}|git_(?:status|diff|log)|build", lane or ""), "CURRENT_CANARY_LANE_REQUIRED")
                kind = "exec"
            pending[lane] = {"lane": kind, "canary_lane": lane, "action_id": row["action_id"]}
        elif phase in {"read_verified", "patch_verified", "native_job_verified"}:
            pending.pop(lane, None)
        elif phase == "observing_original_action" and row.get("state") in {"reconcile_required", "unknown", "failed", "rejected", "refused"}:
            return None, {"ok": False, "error_code": "ORIGINAL_CANARY_ACTION_FAILED_OR_UNKNOWN"}
    require(len(pending) <= 1, "SEQUENTIAL_CANARY_HAS_MULTIPLE_PENDING_ACTIONS")
    return next(iter(pending.values()), None), None


def assist(agent, args, pins, file, max_actions, max_seconds, emit, clock=time.monotonic, sleep=time.sleep):
    require(1 <= max_actions <= 160 and 1 <= max_seconds <= 900, "BOUNDED_OPERATOR_ASSISTANCE_REQUIRED")
    started, received, attempted, polls = clock(), set(), set(), 0
    while clock() - started < max_seconds:
        original, terminal = active_original(file)
        if terminal is not None:
            return {"ok": terminal.get("ok") is True, "stop_reason": "original_canary_terminal",
                    "canary_error_code": terminal.get("error_code"), "poll_count": polls, "received_action_ids": sorted(received)}
        if len(received) >= max_actions:
            return {"ok": True, "stop_reason": "action_budget_reached", "poll_count": polls, "received_action_ids": sorted(received)}
        if original is None or (original["lane"] != "exec" and original["action_id"] in attempted):
            sleep(0.5)
            continue
        try:
            receipt = invoke(agent, args, pins, original["lane"])
        except RuntimeError as error:
            if str(error) in {"CONTROL_PLANE_FILE_READ_POLL_ALREADY_RUNNING", "CONTROL_PLANE_APPROVED_PATCH_POLL_ALREADY_RUNNING",
                              "CONTROL_PLANE_EXEC_POLL_ALREADY_RUNNING"}:
                sleep(0.5)  # The existing owner remains authoritative; no lock is touched.
                continue
            raise
        attempted.add(original["action_id"])
        polls += 1
        received.update(receipt.get("received_action_ids", []))
        emit("supported_scoped_poll", original_action_id=original["action_id"], canary_lane=original["canary_lane"],
             poll_receipt=receipt, original_action_received=original["action_id"] in receipt.get("received_action_ids", []),
             other_admitted_action_received=any(value != original["action_id"] for value in receipt.get("received_action_ids", [])))
        if any(receipt.get(key) for key in ("failed_action_ids", "stopped_action_ids", "rejected_action_ids", "unknown_action_ids", "pending_stop_action_ids")) \
                or any((receipt.get("resumed") or {}).get(key) for key in ("failed", "stopped", "unknown")):
            return {"ok": False, "stop_reason": "admitted_action_failure_or_uncertainty", "poll_count": polls, "received_action_ids": sorted(received)}
        sleep(0.5)
    return {"ok": True, "stop_reason": "time_budget_reached", "poll_count": polls, "received_action_ids": sorted(received)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adapter", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--ready-pins", type=Path, required=True)
    parser.add_argument("--lane", choices=("read", "patch", "exec"))
    parser.add_argument("--original-action")
    parser.add_argument("--canary-receipt", type=Path)
    parser.add_argument("--max-actions", type=int, default=160)
    parser.add_argument("--max-seconds", type=int, default=900)
    options = parser.parse_args()
    if options.canary_receipt:
        require(options.canary_receipt.is_absolute() and re.fullmatch(r"shared-mcp-receipt-[a-f0-9]{32}\.ndjson", options.canary_receipt.name),
                "EXACT_ACTIVE_CANARY_RECEIPT_REQUIRED")
    else:
        require(options.lane is not None and re.fullmatch(r"act_[a-f0-9]{32}", options.original_action or ""), "ORIGINAL_ACTION_IDENTIFIER_REQUIRED")
    require(options.adapter.resolve() == options.candidate.resolve() / "resources/resources/control-plane/node_agent.py",
            "EXACT_CANDIDATE_ADAPTER_REQUIRED")
    pins = json.loads(options.ready_pins.read_text(encoding="utf-8-sig"))
    require(pins["workspace_id"] == "workspace_f93b5bac9dc74fae9cea66f44c4ebc94"
            and pins["workspace_generation"] == "generation_a420c8bfcfcb4e42b5bb7fc5e5cec097", "EXACT_CODEX_SCOPE_REQUIRED")
    spec = importlib.util.spec_from_file_location("reviewed_standalone_node_agent", options.adapter)
    require(spec is not None and spec.loader is not None, "EXACT_ADAPTER_LOADER_REQUIRED")
    agent = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(agent)
    # The packaged adapter derives the product profile; caller cannot redirect it.
    base_args = argparse.Namespace(runtime_mode="packaged", data_root="", project_root=str(options.candidate),
        node=str(options.candidate / "Coding Tools MCP.exe"), timeout_seconds=20,
        workspace_id=pins["workspace_id"], workspace_generation=pins["workspace_generation"])
    profile = agent._policy_data_root(base_args)
    base_args.config = str(profile / "control-plane-node.json")
    base_args.workspace_registry = str(profile / "control-plane-workspaces.json")
    if options.canary_receipt:
        def emit(phase, **values):
            print(json.dumps({"operation": "operator_assisted_supported_scoped_poll", "phase": phase,
                              "observed_at_ms": int(time.time() * 1000), **values}), flush=True)
        outcome = assist(agent, base_args, pins, options.canary_receipt, options.max_actions, options.max_seconds, emit)
        emit("final", **outcome, enqueue_or_replay_performed=False, production_cadence_changed=False,
             proof_classification="operator_assisted_delivery_not_latency_benchmark", action_id_filter_supported=False)
        return 0 if outcome["ok"] else 1
    receipt = invoke(agent, base_args, pins, options.lane)
    received = receipt.get("received_action_ids", [])
    print(json.dumps({"operation": "operator_assisted_supported_scoped_poll", "ok": True, "lane": options.lane,
        "original_action_id": options.original_action, "original_action_received": options.original_action in received,
        "other_admitted_action_received": any(value != options.original_action for value in received),
        "poll_receipt": receipt, "scope_selection": "exact_Codex_workspace_generation",
        "action_selection": "central_scope_lane_poll_has_no_action_id_filter", "enqueue_or_replay_performed": False,
        "production_cadence_changed": False, "proof_classification": "operator_assisted_delivery_not_latency_benchmark"}))


if __name__ == "__main__":
    try:
        sys.exit(main() or 0)
    except Exception as error:
        code = str(error) if isinstance(error, RuntimeError) and re.fullmatch(r"[A-Z0-9_]{3,100}", str(error)) else type(error).__name__
        print(json.dumps({"operation": "operator_assisted_supported_scoped_poll", "ok": False, "error_code": code,
                          "next_action": "Observe original action; do not enqueue, replay or remove a busy production lock."}))
        sys.exit(1)
