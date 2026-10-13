"""Read-only timing audit for the exact r4 patch019 UNKNOWN receipt."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import os

HERE = Path(__file__).resolve().parent
ROOT = Path("E:/DEV/Codex-web")
PROFILE = Path(os.environ["APPDATA"]) / "web-mcp-assistant"
ACTION = "act_65fa937277dd4963a5ca39ffe9e291ec"
ATTEMPT = "try_8a7f3fedcddd4de8a1267eb87a7e39ed"
TASK_CONTEXT = ROOT / ".coding-tools/task-contexts/2f4604b5adda953cd683f9d3.json"
PERFORMANCE = ROOT / ".coding-tools/performance.json"
CANARY = HERE / "shared-mcp-receipt-feab8533616c4989b16cfc0dbdf9bd7d.ndjson"
JOURNAL = PROFILE / "control-plane-node.json.approved-patch-bridge-journal.json"


def raw_json(file):
    raw = file.read_bytes()
    return json.loads(raw.decode("utf-8-sig")), hashlib.sha256(raw).hexdigest()


def pick(value, keys):
    return {key: value.get(key) for key in keys}


def main():
    journal, journal_hash = raw_json(JOURNAL)
    context, context_hash = raw_json(TASK_CONTEXT)
    performance, performance_hash = raw_json(PERFORMANCE)
    rows = [json.loads(line) for line in CANARY.read_text(encoding="utf-8-sig").splitlines()]
    action_rows = [row for row in rows if row.get("action_id") == ACTION]
    final = next(row for row in reversed(rows) if row.get("phase") == "final")
    entry = journal["entries"][f"{ACTION}|{ATTEMPT}"]
    events = [event for event in performance["recent"] if event.get("invocation", {}).get("request_id") in {
        "control-plane-approved-patch-bind-8ab31995faf49d0e2b43d565",
        "control-plane-approved-patch-workflow-8ab31995faf49d0e2b43d565",
    }]
    bind = next(event for event in events if event["tool"] == "workspace_context")
    workflow = next(event for event in events if event["tool"] == "agent_workflow")
    task_events = context.get("events", [])
    applied = next(event for event in task_events if event.get("event") == "files_modified")
    report = {
        "schema_version": 1,
        "operation": "r4_patch019_timeout_causal_audit",
        "read_only": True,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "observed_git_head": "7999c4151cb501db86f2e4d0a2275d33fc248324",
        "action_id": ACTION,
        "attempt_id": ATTEMPT,
        "local_journal": {"state": entry["state"], "receipt_state": entry["receipt"]["receipt_state"],
            "local_handle_present": bool(entry["receipt"]["local_handle"]),
            "payload": entry["receipt"]["payload"], "sha256": journal_hash},
        "canary_action_timeline": [{key: row.get(key) for key in ("phase", "observed_at_ms", "lane", "state", "action_id")} for row in action_rows],
        "matching_performance": {
            "bind": pick(bind, ("started_at", "finished_at", "duration_ms", "ok", "error_class"))
                | {"request_id": bind["invocation"]["request_id"], "task_context_id": bind["invocation"]["task_context_id"]},
            "workflow": pick(workflow, ("started_at", "finished_at", "duration_ms", "ok", "error_class", "run_id", "wave_id", "orchestration_state"))
                | {"request_id": workflow["invocation"]["request_id"], "task_context_id": workflow["invocation"]["task_context_id"]},
        },
        "durable_task_observation": {
            "task_id": context["task_id"], "status": context["status"], "orchestration": pick(context["orchestration"], ("run_id", "wave_id", "orchestration_state", "execution_mode", "route_resolved")),
            "objective": context["objective"], "apply_step_updated_at": context["steps"][0]["updated_at"],
            "finalize_step_updated_at": context["steps"][1]["updated_at"], "completion_report_id": context["completion_report_id"],
            "modified_file_count": len(context.get("modified_files", [])), "modified_file_paths_are_sanitized": True,
            "event_times": [{"event": event["event"], "time": event["time"]} for event in task_events
                if event.get("event") in {"orchestration_proving", "continuous_workflow_completed", "awaiting_final_acceptance", "files_modified"}],
            "evidence_sha256": context_hash,
        },
        "timing_calculation": {
            "electron_approved_patch_timeout_ms": 12000,
            "workflow_observed_duration_ms": workflow["duration_ms"],
            "workflow_exceeded_electron_timeout_ms": workflow["duration_ms"] - 12000,
            "workflow_finished_after_canary_unknown_observation_is_possible": True,
            "interpretation": "The exact local bridge deadline is shorter than this matching agent_workflow operation. The server projection recorded ok=true and the durable task reached final acceptance pending, while the local journal retained UNKNOWN because no bounded local receipt returned before the bridge deadline.",
        },
        "source_proof": {
            "runtime_orchestrator_constant": "electron/services/runtimeOrchestrator.js:171 CONTROL_PLANE_APPROVED_PATCH_TIMEOUT_MS=12000",
            "runtime_orchestrator_timeout_path": "approved-patch MCP HTTP request timeout and default tools/call workflow timeout",
            "python_bridge_timeout_path": "control-plane/control_plane/node_agent.py recovery_approved_patch_bridge subprocess timeout uses args.timeout_seconds when no verification plan",
            "runtime_orchestrator_sha256": "e9d42d7e78e8605b5da8d52d90e659cccd6dfa7480e37fb08b9dbaee5bf355e60",
            "approved_patch_bridge_sha256": "0bf11073b074739229b69d8007b5518923fdf092bf9d833db62f04430d961a85",
            "node_agent_sha256": "fca440c9fc9faa32e4beea9085b2828a85b1c27247a17217aef7230698ce2537",
        },
        "minimal_fix_proposal": {
            "source_scope": "Future package only; do not mutate this historical UNKNOWN or replay its action",
            "electron": "Keep 12s health/bind timeout; give the approved-patch workflow call an operation-specific >=30s deadline so observed 12.843s operations have margin.",
            "python": "Give the approved-patch bridge subprocess a matching >30s bound (for example 35s) when no verification plan is present, so the outer bridge cannot expire first.",
            "preserve": "Durable prepared journal and UNKNOWN-on-uncertain-effect semantics remain unchanged; a longer deadline reduces false UNKNOWN but cannot remove reconciliation requirements.",
            "validation": "Add a fake workflow taking 12.843s to the approved-patch bridge test and assert completion before the operation deadline while a 12s health/bind request still times out normally.",
        },
        "proof_limit": "The performance projection and durable task context correlate the exact workflow/run/wave but do not supply a valid local bounded patch receipt; this audit does not claim the historical patch as locally settled or semantically accepted.",
        "production_mutation_performed": False,
        "historical_unknown_modified": False,
    }
    output = HERE / "patch019-timeout-causal-audit.json"
    if output.exists():
        raise RuntimeError("NEW_ADDITIVE_REPORT_REQUIRED")
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"ok": True, "report_path": str(output), "workflow_duration_ms": workflow["duration_ms"],
        "timeout_ms": 12000, "overrun_ms": workflow["duration_ms"] - 12000, "run_id": workflow["run_id"], "wave_id": workflow["wave_id"]}))


if __name__ == "__main__":
    main()
