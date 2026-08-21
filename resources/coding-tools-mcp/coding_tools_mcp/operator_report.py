from __future__ import annotations

from typing import Any


OPERATOR_REPORT_STATES = {"ACCEPTING", "CHECKPOINTED", "REPLAN", "BLOCKED", "ABORTED"}
REPORT_CONTRACT = [
    "WHAT CHANGED",
    "CURRENT STATE",
    "SOURCE / RUN / WAVE ID",
    "PROOF ACTUALLY RUN",
    "ACCEPTED OR NOT",
    "WHAT REMAINS",
    "NEXT CRITICAL ACTION",
]


def build_orchestration_runtime_result(
    runtime: Any,
    ctx: Any | None,
    *,
    write_reports: bool = True,
) -> dict[str, Any] | None:
    """Build and persist the content-free orchestration/operator projection for a Runtime."""
    if ctx is None:
        return None
    reports: dict[str, Any] = {}
    if write_reports:
        try:
            reports = runtime.orchestration_report.write_reports(ctx.run_id)
        except (OSError, ValueError, KeyError) as exc:
            reports = {"error": str(exc)[:500]}
    result = {
        **ctx.projection(),
        "integrity": runtime.orchestration_ledger.verify_chain(ctx.run_id),
        "reports": reports,
        "final_acceptance_required": ctx.state == "ACCEPTING",
    }
    if str(ctx.state or "").upper() in OPERATOR_REPORT_STATES:
        completion_report = build_operator_completion_report(
            ledger=runtime.orchestration_ledger,
            ctx=ctx,
            task_state=runtime.task_state.get(),
            reports=reports,
        )
        result["completion_report"] = completion_report
        try:
            runtime.task_state.set_completion_report(completion_report)
        except (OSError, ValueError, RuntimeError):
            pass
    return result


def build_command_completion_report(
    *,
    task_state: dict[str, Any],
    workspace_identity: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Build a content-free operator checkpoint for a terminal plain command."""
    last = task_state.get("last_command_result")
    if not isinstance(last, dict) or not str(last.get("command_id") or "").strip():
        return None
    workspace_identity = dict(workspace_identity or {})
    orchestration = task_state.get("orchestration") if isinstance(task_state.get("orchestration"), dict) else {}
    result_status = str(last.get("result_status") or "failed").lower()
    command_status = str(last.get("status") or "").lower()
    terminated = command_status in {"killed", "terminated", "stopped", "timed_out", "timeout"}
    passed = result_status == "passed" and not terminated
    changed_files, change_source = _changed_files(task_state, {})
    kind = str(last.get("kind") or "command")
    proof_rows = []
    if kind in {"test", "build"}:
        proof_rows.append({
            "kind": kind,
            "status": "passed" if passed else "failed",
            "exit_code": last.get("exit_code"),
            "duration_ms": last.get("duration_ms"),
            "command_id": str(last.get("command_id") or ""),
        })
    if terminated:
        decision = "COMMAND_TERMINATED"
    elif passed:
        decision = "COMMAND_COMPLETED_AWAITING_OPERATOR_REPORT"
    else:
        decision = "COMMAND_FAILED"
    blocker = None if passed else {
        "failure_class": "COMMAND_TERMINATED" if terminated else "EXECUTION_COMMAND_FAILED",
        "reason": "The command reached a terminal non-success state.",
        "exit_code": last.get("exit_code"),
    }
    next_action = (
        "Present this completion_report to the operator before starting another material wave."
        if passed
        else "Present this completion_report to the operator, then replan or repair the recorded command failure before continuing."
    )
    remaining = (
        "No further command action is inferred from this terminal command. Report the result before continuing."
        if passed
        else "The terminal command failure must be reported and reconciled before another material wave."
    )
    return {
        "schema_version": 1,
        "operator_visible_required": True,
        "report_contract": list(REPORT_CONTRACT),
        "command_id": str(last.get("command_id") or ""),
        "what_changed": {
            "files": changed_files,
            "source": change_source,
            "raw_source_or_command_output_included": False,
        },
        "current_state": {
            "task_status": str(task_state.get("status") or ""),
            "command": {
                "command_id": str(last.get("command_id") or ""),
                "kind": kind,
                "status": command_status,
                "result_status": result_status,
                "exit_code": last.get("exit_code"),
                "duration_ms": last.get("duration_ms"),
            },
            "git": {
                "head": str(workspace_identity.get("base_head") or ""),
                "branch": str(workspace_identity.get("branch") or ""),
                "worktree_fp": str(workspace_identity.get("worktree_fp") or ""),
                "dirty_paths": list(workspace_identity.get("dirty_paths") or [])[:200],
            },
        },
        "source_run_wave": {
            "task_id": str(task_state.get("task_id") or ""),
            "run_id": str(orchestration.get("run_id") or ""),
            "wave_id": str(orchestration.get("wave_id") or ""),
            "orchestration_state": str(orchestration.get("orchestration_state") or ""),
        },
        "proof_actually_run": {
            "count": len(proof_rows),
            "all_recorded_proofs_passed": bool(proof_rows) and passed,
            "proofs": proof_rows,
        },
        "accepted_or_not": decision,
        "blocker_or_failure": blocker,
        "what_remains": remaining,
        "next_critical_action": next_action,
    }


def _changed_files(task_state: dict[str, Any], checkpoint: dict[str, Any]) -> tuple[list[dict[str, Any]], str]:
    metadata = checkpoint.get("metadata") if isinstance(checkpoint.get("metadata"), dict) else {}
    accepted_files = metadata.get("accepted_files") if isinstance(metadata.get("accepted_files"), dict) else {}
    receipt_files = accepted_files.get("files") if isinstance(accepted_files.get("files"), list) else []
    if receipt_files:
        rows = []
        for item in receipt_files[:100]:
            if not isinstance(item, dict) or not str(item.get("path") or "").strip():
                continue
            rows.append({
                "path": str(item.get("path") or ""),
                "state": str(item.get("state") or ""),
                "sha256": str(item.get("sha256") or "") or None,
            })
        return rows, "accepted_checkpoint_file_receipts"

    modified_files = task_state.get("modified_files") if isinstance(task_state.get("modified_files"), list) else []
    rows = []
    for item in modified_files[:100]:
        if not isinstance(item, dict) or not str(item.get("path") or "").strip():
            continue
        rows.append({
            "path": str(item.get("path") or ""),
            "operation": str(item.get("operation") or ""),
        })
    return rows, "aligned_task_modified_files" if rows else "no_durable_file_receipts"


def build_operator_completion_report(
    *,
    ledger: Any,
    ctx: Any,
    task_state: dict[str, Any] | None = None,
    reports: dict[str, Any] | None = None,
) -> dict[str, Any]:
    task_state = dict(task_state or {})
    reports = dict(reports or {})
    run_id = str(ctx.run_id or "")
    wave_id = str(ctx.wave_id or "")
    orchestration_state = str(ctx.state or "").upper()
    run = ledger.get_run(run_id) or {}
    waves = ledger.list_waves(run_id)
    wave = next((item for item in waves if str(item.get("wave_id") or "") == wave_id), {})
    proofs = ledger.list_proofs(run_id, wave_id=wave_id)
    checkpoints = ledger.list_checkpoints(run_id, wave_id=wave_id)
    checkpoint = checkpoints[-1] if checkpoints else {}
    events = ledger.list_events(run_id, wave_id=wave_id)
    failures = [item for item in events if str(item.get("event_type") or "") == "failure_observed"]
    latest_failure = failures[-1] if failures else {}
    failure_payload = latest_failure.get("payload") if isinstance(latest_failure.get("payload"), dict) else {}
    objective_provenance = ledger.wave_objective_provenance(run_id, wave_id)

    task_projection = task_state.get("orchestration") if isinstance(task_state.get("orchestration"), dict) else {}
    aligned_task = task_state if str(task_projection.get("run_id") or "") == run_id else {}
    changed_files, change_source = _changed_files(aligned_task, checkpoint)
    proof_rows = [
        {
            "proof_id": str(item.get("proof_id") or ""),
            "stage_id": str(item.get("stage_id") or ""),
            "status": str(item.get("status") or ""),
            "duration_ms": item.get("duration_ms"),
            "exit_code": item.get("exit_code"),
            "cache_hit": bool(item.get("cache_hit")),
        }
        for item in proofs[-50:]
    ]
    decision = {
        "CHECKPOINTED": "ACCEPTED",
        "ACCEPTING": "PENDING_FINAL_ACCEPTANCE",
        "REPLAN": "NOT_ACCEPTED_REPLAN_REQUIRED",
        "BLOCKED": "NOT_ACCEPTED_BLOCKED",
        "ABORTED": "NOT_ACCEPTED_ABORTED",
    }.get(orchestration_state, "IN_PROGRESS")
    remaining = {
        "CHECKPOINTED": "No additional semantic work is inferred for this run. Continue from the explicit project plan only after this report is shown to the operator.",
        "ACCEPTING": "Final controller acceptance or rejection is still required for this proven wave.",
        "REPLAN": "A changed evidence, scope, or strategy is required before another execution wave.",
        "BLOCKED": "The durable blocker must be resolved before another execution wave.",
        "ABORTED": "Resume only from current source state with fresh or replanned proof; stale proof must not be reused.",
    }.get(orchestration_state, "Continue only from the durable task state.")
    next_action = {
        "CHECKPOINTED": "Present this completion_report to the operator before starting another material wave.",
        "ACCEPTING": "Present this completion_report to the operator, inspect durable proof, then call task_control action=accept or reject.",
        "REPLAN": "Present this completion_report to the operator, then replan with changed evidence, scope, or strategy.",
        "BLOCKED": "Present this completion_report to the operator, then resolve the recorded blocker.",
        "ABORTED": "Present this completion_report to the operator before any resume or replacement wave.",
    }.get(orchestration_state, "Present current durable state to the operator before continuing.")
    blocker = None
    if latest_failure:
        blocker = {
            "failure_class": str(failure_payload.get("failure_class") or "") or None,
            "reason": str(failure_payload.get("reason") or "") or None,
            "event_seq": latest_failure.get("seq"),
        }
    elif aligned_task.get("failure"):
        blocker = {"failure_class": None, "reason": str(aligned_task.get("failure") or ""), "event_seq": None}

    return {
        "schema_version": 1,
        "operator_visible_required": True,
        "report_contract": list(REPORT_CONTRACT),
        "what_changed": {
            "files": changed_files,
            "source": change_source,
            "raw_source_or_command_output_included": False,
        },
        "current_state": {
            "orchestration_state": orchestration_state,
            "run_status": str(run.get("status") or ""),
            "wave_status": str(wave.get("status") or ""),
            "task_status": str(aligned_task.get("status") or "") or None,
            "integrity": ledger.verify_chain(run_id),
            "reports": reports,
        },
        "source_run_wave": {
            "run_id": run_id,
            "wave_id": wave_id,
            "base_head": str(getattr(ctx, "base_head", "") or ""),
            "worktree_fp": str(getattr(ctx, "worktree_fp", "") or ""),
            "contract_fp": str(getattr(ctx, "contract_fp", "") or ""),
            "objective_provenance": objective_provenance,
        },
        "proof_actually_run": {
            "count": len(proof_rows),
            "all_recorded_proofs_passed": bool(proof_rows) and all(item["status"] == "passed" for item in proof_rows),
            "proofs": proof_rows,
        },
        "accepted_or_not": decision,
        "blocker_or_failure": blocker,
        "what_remains": remaining,
        "next_critical_action": next_action,
    }
