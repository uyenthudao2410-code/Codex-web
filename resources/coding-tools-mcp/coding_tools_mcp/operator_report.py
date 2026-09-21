from __future__ import annotations

from datetime import datetime
import re
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
PROBLEM_REPORT_SECTION = "PROBLEM RESOLUTION"
_MAX_VISIBLE_PROBLEM_CRITERIA = 20
_MAX_VISIBLE_UNRESOLVED_CONDITIONS = 20

_EVENT_ID_RE = re.compile(r"^[0-9a-fA-F]{32}$")
_PATH_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
_EVENT_TIME_RE = re.compile(
    r"^(?P<date>[0-9]{4}-[0-9]{2}-[0-9]{2})T"
    r"(?P<time>[0-9]{2}:[0-9]{2}:[0-9]{2})"
    r"(?:\.(?P<fraction>[0-9]{1,6}))?"
    r"(?P<zone>Z|(?P<sign>[+-])(?P<offset_hour>[0-9]{2}):(?P<offset_minute>[0-9]{2}))$",
    re.ASCII,
)
_MAX_PATCH_OBSERVATIONS = 100
_MAX_PATCH_PATH_HASHES = 256
_MAX_EVENT_TIME_LENGTH = 64
_MAX_PATCH_COUNT = (1 << 63) - 1


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
        if write_reports:
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


def _nonnegative_patch_count(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    if value < 0 or value > _MAX_PATCH_COUNT:
        return None
    return value


def _canonical_event_time(value: Any) -> str | None:
    if not isinstance(value, str) or not value or len(value) > _MAX_EVENT_TIME_LENGTH:
        return None
    match = _EVENT_TIME_RE.fullmatch(value)
    if match is None:
        return None
    # `datetime.fromisoformat` in newer Python versions accepts the ISO
    # midnight spelling `24:00:00`.  The ledger contract uses a canonical
    # clock representation with an explicit 00..23 hour range, so validate the
    # wall-clock fields before delegating date/offset validation to datetime.
    hour, minute, second = (int(item) for item in match.group("time").split(":"))
    if hour > 23 or minute > 59 or second > 59:
        return None
    if match.group("zone") != "Z":
        if int(match.group("offset_hour")) > 23 or int(match.group("offset_minute")) > 59:
            return None
    candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return value


def _patch_surface_observation_projection(
    events: list[dict[str, Any]],
    *,
    run_id: str,
    wave_id: str,
) -> dict[str, Any] | None:
    matching = [
        item
        for item in events
        if isinstance(item, dict)
        and str(item.get("event_type") or "") == "patch_surface_observed"
        and str(item.get("run_id") or "") == run_id
        and str(item.get("wave_id") or "") == wave_id
    ]
    if not matching:
        return None

    selected = matching[-_MAX_PATCH_OBSERVATIONS:]
    output_truncated = len(matching) > _MAX_PATCH_OBSERVATIONS
    observations: list[dict[str, Any]] = []
    rejected_event_count = 0

    for event in selected:
        event_id = event.get("event_id")
        seq = event.get("seq")
        event_time = _canonical_event_time(event.get("event_time"))
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else None
        if (
            not isinstance(event_id, str)
            or _EVENT_ID_RE.fullmatch(event_id) is None
            or isinstance(seq, bool)
            or not isinstance(seq, int)
            or seq <= 0
            or event_time is None
            or payload is None
            or type(payload.get("schema_version")) is not int
            or payload.get("schema_version") != 1
            or payload.get("measurement") != "applied_patch_delta_v1"
            or payload.get("content_free") is not True
            or payload.get("production_behavior_changed") is not False
            or not isinstance(payload.get("complete"), bool)
        ):
            rejected_event_count += 1
            continue

        invalid_fields: list[str] = []
        counts: dict[str, int | None] = {}
        for field in ("file_count", "additions", "removals", "line_changes"):
            counts[field] = _nonnegative_patch_count(payload.get(field))
            if counts[field] is None:
                invalid_fields.append(field)

        raw_ids = payload.get("file_ids")
        row_truncated = False
        path_hashes: list[str] = []
        if not isinstance(raw_ids, list):
            invalid_fields.append("file_ids")
        else:
            if len(raw_ids) > _MAX_PATCH_PATH_HASHES:
                row_truncated = True
                invalid_fields.append("file_ids")
            seen: set[str] = set()
            encountered: list[str] = []
            ids_invalid = False
            for item in raw_ids[:_MAX_PATCH_PATH_HASHES]:
                if not isinstance(item, str) or _PATH_HASH_RE.fullmatch(item) is None:
                    ids_invalid = True
                    continue
                if item in seen:
                    ids_invalid = True
                    continue
                seen.add(item)
                encountered.append(item)
            if encountered != sorted(encountered):
                ids_invalid = True
            if ids_invalid:
                invalid_fields.append("file_ids")
            path_hashes = sorted(seen)
        if not path_hashes:
            invalid_fields.append("file_ids")

        producer_complete = bool(payload["complete"])
        file_count = counts["file_count"]
        if file_count is not None:
            if file_count == 0:
                invalid_fields.append("file_count")
            elif producer_complete:
                if file_count != len(path_hashes) or "file_ids" in invalid_fields or row_truncated:
                    counts["file_count"] = None
                    invalid_fields.append("file_count")
            elif file_count < len(path_hashes):
                counts["file_count"] = None
                invalid_fields.append("file_count")
            elif file_count > len(path_hashes):
                row_truncated = True

        additions = counts["additions"]
        removals = counts["removals"]
        line_changes = counts["line_changes"]
        if (
            additions is not None
            and removals is not None
            and line_changes is not None
            and line_changes != additions + removals
        ):
            counts["line_changes"] = None
            invalid_fields.append("line_changes")

        invalid_fields = sorted(set(invalid_fields))
        observation_complete = (
            producer_complete
            and not row_truncated
            and not invalid_fields
            and all(counts[field] is not None for field in counts)
        )
        observations.append({
            "event_id": event_id,
            "seq": seq,
            "event_time": event_time,
            "measurement": "applied_patch_delta_v1",
            "path_hash_semantics": "sha256_of_path_string_not_content_hash",
            "path_hashes_sha256": path_hashes,
            "file_count": counts["file_count"],
            "additions": counts["additions"],
            "removals": counts["removals"],
            "line_changes": counts["line_changes"],
            "producer_complete": producer_complete,
            "complete": observation_complete,
            "truncated": row_truncated,
            "invalid": bool(invalid_fields),
            "invalid_fields": invalid_fields,
        })

    return {
        "schema_version": 1,
        "authority": "observation_only_not_exact_byte_receipt_proof_acceptance_or_user_outcome",
        "matching_event_count": len(matching),
        "observation_count": len(observations),
        "rejected_event_count": rejected_event_count,
        "complete": (
            bool(observations)
            and not output_truncated
            and rejected_event_count == 0
            and all(item["complete"] for item in observations)
        ),
        "truncated": output_truncated or any(item["truncated"] for item in observations),
        "invalid": rejected_event_count > 0 or any(item["invalid"] for item in observations),
        "observations": observations,
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
                "size_bytes": item.get("size_bytes"),
                "receipt_kind": str(item.get("receipt_kind") or "") or None,
                "run_id": str(item.get("run_id") or "") or None,
                "wave_id": str(item.get("wave_id") or "") or None,
            })
        source = str(accepted_files.get("source") or "")
        return rows, (
            "accepted_checkpoint_file_attestations"
            if source == "explicit_acceptance_attestations"
            else "accepted_checkpoint_file_receipts"
        )

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


def _problem_read_unavailable(exc: BaseException) -> dict[str, Any]:
    code = str(getattr(exc, "code", "") or type(exc).__name__)[:128]
    return {"status": "UNAVAILABLE", "missing_reason": code}


def _problem_resolution_projection(
    ledger: Any,
    *,
    run_id: str,
    wave_id: str,
    checkpoint_id: str,
) -> dict[str, Any] | None:
    """Project bounded authoritative Problem facts for an exactly bound RUN."""
    handoff_reader = getattr(ledger, "problem_handoff_for_run", None)
    if not callable(handoff_reader):
        return None
    try:
        handoff = handoff_reader(run_id)
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        return {
            "status": "UNAVAILABLE",
            "missing_reason": str(getattr(exc, "code", "") or type(exc).__name__)[:128],
            "content_free": True,
            "derived_projection_only": True,
            "authority_granted": False,
        }
    if not isinstance(handoff, dict):
        return None
    problem_id = str(handoff.get("active_problem_id") or "")
    try:
        problem_revision = int(handoff.get("problem_revision") or 0)
    except (TypeError, ValueError):
        problem_revision = 0
    if not problem_id or problem_revision < 1:
        return None

    contract = (
        handoff.get("contract_capsule")
        if handoff.get("contract_capsule_included") is True
        and isinstance(handoff.get("contract_capsule"), dict)
        else None
    )
    criteria: list[dict[str, str]] = []
    unresolved_conditions: list[str] = []
    objective_summary: str | None = None
    criteria_truncated = False
    unresolved_conditions_truncated = False
    if contract is not None:
        objective_summary = str(contract.get("objective_summary") or "")[:2000] or None
        raw_criteria = contract.get("acceptance_criteria")
        if isinstance(raw_criteria, list):
            criteria_truncated = len(raw_criteria) > _MAX_VISIBLE_PROBLEM_CRITERIA
            for item in raw_criteria[:_MAX_VISIBLE_PROBLEM_CRITERIA]:
                if not isinstance(item, dict):
                    continue
                criterion_id = str(item.get("criterion_id") or "")[:128]
                if not criterion_id:
                    continue
                criteria.append({
                    "criterion_id": criterion_id,
                    "summary": str(item.get("summary") or "")[:800],
                })
        raw_unresolved = contract.get("unresolved_conditions")
        if isinstance(raw_unresolved, list):
            unresolved_conditions_truncated = (
                len(raw_unresolved) > _MAX_VISIBLE_UNRESOLVED_CONDITIONS
            )
            unresolved_conditions = [
                str(item)[:800]
                for item in raw_unresolved[:_MAX_VISIBLE_UNRESOLVED_CONDITIONS]
                if isinstance(item, str)
            ]

    goal_projection: dict[str, Any]
    goal_reader = getattr(ledger, "goal_pursuit_live_summary", None)
    if callable(goal_reader):
        try:
            raw_goal = goal_reader(run_id=run_id)
            goal_projection = raw_goal if isinstance(raw_goal, dict) else {
                "status": "UNAVAILABLE",
                "missing_reason": "GOAL_SUMMARY_INVALID",
            }
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            goal_projection = _problem_read_unavailable(exc)
    else:
        goal_projection = {"status": "UNAVAILABLE", "missing_reason": "GOAL_SUMMARY_UNAVAILABLE"}

    goal_completion = (
        goal_projection.get("completion")
        if isinstance(goal_projection.get("completion"), dict)
        else {}
    )
    progress = {
        "status": str(goal_completion.get("status") or goal_projection.get("status") or "UNAVAILABLE"),
        "criteria_total": goal_completion.get("criteria_total"),
        "criteria_proven": goal_completion.get("criteria_proven"),
        "criteria_unresolved": goal_completion.get("criteria_unresolved"),
        "coverage_status": goal_completion.get("exact_coverage_status"),
        "missing_reason": goal_completion.get("missing_reason") or goal_projection.get("missing_reason"),
        "next_critical_gap_id": goal_projection.get("next_critical_gap_id"),
        "next_critical_gap": goal_projection.get("next_critical_gap"),
        "next_action": goal_projection.get("next_action"),
        "fact_window": goal_projection.get("fact_window") if isinstance(goal_projection.get("fact_window"), dict) else None,
    }

    telemetry_projection: dict[str, Any]
    telemetry_reader = getattr(ledger, "continuity_telemetry_summary", None)
    if callable(telemetry_reader):
        try:
            raw_telemetry = telemetry_reader(
                problem_id=problem_id,
                problem_revision=problem_revision,
                limit=1000,
            )
            if isinstance(raw_telemetry, dict):
                telemetry_projection = {
                    "status": "AVAILABLE",
                    "complete": bool(raw_telemetry.get("complete")),
                    "event_count": int(raw_telemetry.get("event_count") or 0),
                    "manual_nudge_count": int(raw_telemetry.get("manual_nudge_count") or 0),
                    "interruption_count": int(raw_telemetry.get("interruption_count") or 0),
                    "replan_count": int(raw_telemetry.get("replan_count") or 0),
                    "report_gate_count": int(raw_telemetry.get("report_gate_count") or 0),
                    "continuation_attempt_count": int(raw_telemetry.get("continuation_attempt_count") or 0),
                    "continuation_success_count": int(raw_telemetry.get("continuation_success_count") or 0),
                    "continuation_failure_count": int(raw_telemetry.get("continuation_failure_count") or 0),
                    "reconnect_count": int(raw_telemetry.get("reconnect_count") or 0),
                    "restart_count": int(raw_telemetry.get("restart_count") or 0),
                    "resume_count": int(raw_telemetry.get("resume_count") or 0),
                    "duplicate_effect_prevented_count": int(raw_telemetry.get("duplicate_effect_prevented_count") or 0),
                    "terminal_count": int(raw_telemetry.get("terminal_count") or 0),
                    "blocker_count": int(raw_telemetry.get("blocker_count") or 0),
                    "accepted_checkpoint_count": int(raw_telemetry.get("accepted_checkpoint_count") or 0),
                    "natural_event_count": int(raw_telemetry.get("natural_event_count") or 0),
                    "synthetic_event_count": int(raw_telemetry.get("synthetic_event_count") or 0),
                    "legacy_unknown_event_count": int(raw_telemetry.get("legacy_unknown_event_count") or 0),
                    "time_to_resume_ms": raw_telemetry.get("time_to_resume_ms"),
                    "replan_duration_ms": raw_telemetry.get("replan_duration_ms"),
                    "report_gate_wait_ms": raw_telemetry.get("report_gate_wait_ms"),
                }
            else:
                telemetry_projection = {
                    "status": "UNAVAILABLE",
                    "missing_reason": "CONTINUITY_TELEMETRY_INVALID",
                }
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            telemetry_projection = _problem_read_unavailable(exc)
    else:
        telemetry_projection = {
            "status": "UNAVAILABLE",
            "missing_reason": "CONTINUITY_TELEMETRY_UNAVAILABLE",
        }

    return {
        "status": "AVAILABLE" if str(handoff.get("context_status") or "") == "VALID" else "UNAVAILABLE",
        "problem_id": problem_id,
        "problem_revision": problem_revision,
        "problem_state": str(handoff.get("problem_state") or "UNKNOWN"),
        "resolution_status": str(goal_projection.get("resolution_status") or "UNAVAILABLE"),
        "contract_fingerprint": str(handoff.get("contract_fingerprint") or ""),
        "objective_summary": objective_summary,
        "contract_capsule_included": contract is not None,
        "contract_capsule_omission_reason": handoff.get("contract_capsule_omission_reason"),
        "criteria": criteria,
        "criteria_truncated": criteria_truncated,
        "progress": progress,
        "unresolved_conditions": unresolved_conditions,
        "unresolved_conditions_truncated": unresolved_conditions_truncated,
        "current_attempt": {
            "run_id": run_id,
            "wave_id": wave_id,
            "checkpoint_id": checkpoint_id,
        },
        "latest_feedback_relation": str(handoff.get("latest_feedback_relation") or "UNKNOWN"),
        "event_count": int(handoff.get("event_count") or 0),
        "latest_event": handoff.get("latest_event") if isinstance(handoff.get("latest_event"), dict) else None,
        "optimization_telemetry": telemetry_projection,
        "content_free": True,
        "derived_projection_only": True,
        "authority_granted": False,
    }


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
    patch_surface_observations = _patch_surface_observation_projection(
        events,
        run_id=run_id,
        wave_id=wave_id,
    )
    if (
        not changed_files
        and patch_surface_observations is not None
        and patch_surface_observations["observation_count"] > 0
    ):
        change_source = "canonical_patch_surface_observations"
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

    what_changed: dict[str, Any] = {
        "files": changed_files,
        "source": change_source,
        "raw_source_or_command_output_included": False,
    }
    if patch_surface_observations is not None:
        what_changed["patch_surface_observations"] = patch_surface_observations

    problem_resolution = _problem_resolution_projection(
        ledger,
        run_id=run_id,
        wave_id=wave_id,
        checkpoint_id=str(checkpoint.get("checkpoint_id") or ""),
    )
    report_contract = list(REPORT_CONTRACT)
    if problem_resolution is not None:
        report_contract.insert(2, PROBLEM_REPORT_SECTION)

    return {
        "schema_version": 1,
        "operator_visible_required": True,
        "report_contract": report_contract,
        **({"problem_resolution": problem_resolution} if problem_resolution is not None else {}),
        "what_changed": what_changed,
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
            "checkpoint_id": str(checkpoint.get("checkpoint_id") or ""),
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
