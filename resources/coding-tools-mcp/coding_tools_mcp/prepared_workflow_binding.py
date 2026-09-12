from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .errors import ToolFailure


@dataclass(frozen=True)
class PreparedWorkflowBinding:
    """Validated caller-scoped identity for a split prepare/execute workflow."""

    requested_run_id: str = ""
    requested_wave_id: str = ""
    execute_candidate: bool = False
    verified: bool = False


def resolve_prepared_objective_boundary(
    binding: PreparedWorkflowBinding,
    *,
    explicit_objective: str,
    current_task: dict[str, Any],
    current_run: dict[str, Any],
    current_ctx: Any,
    ledger: Any,
    task_state: Any,
) -> tuple[dict[str, Any], dict[str, Any], str, Any]:
    """Reuse an exact prepared lineage or detach an unrelated projection."""

    projection = current_task.get("orchestration") if isinstance(current_task.get("orchestration"), dict) else {}
    run_id = str(projection.get("run_id") or "")
    if current_ctx is None or not explicit_objective or str(current_ctx.state) not in {"PREFLIGHT", "READY"}:
        return current_task, projection, run_id, current_ctx

    provenance = ledger.wave_objective_provenance(current_ctx.run_id, current_ctx.wave_id)
    current_objective = str(
        (provenance or {}).get("effective_objective")
        or current_run.get("objective")
        or ""
    ).strip()
    current_task_id = str(current_task.get("task_id") or "").strip()
    run_task_id = str(current_run.get("task_id") or "").strip()
    task_mismatch = bool(current_task_id and run_task_id and current_task_id != run_task_id)
    objective_mismatch = bool(current_objective and current_objective != explicit_objective)
    if not task_mismatch and not objective_mismatch:
        return current_task, projection, run_id, current_ctx
    if binding.verified and not task_mismatch:
        return current_task, projection, run_id, current_ctx
    if binding.execute_candidate and objective_mismatch and not task_mismatch:
        raise ToolFailure(
            "PREPARED_RUN_BINDING_REQUIRED",
            "The execute objective differs from the active prepare objective. Retry once with the exact run_id and wave_id returned by prepare; no new RUN was created.",
            category="runtime",
            retryable=True,
            details={"run_id": current_ctx.run_id, "wave_id": current_ctx.wave_id},
        )

    updated = task_state.update(
        {
            "objective": explicit_objective,
            "status": "active",
            "failure": None,
            "current_step": "Orchestration preflight",
            "next_step": "",
            "new_task": True,
        },
        event="task_started",
    )
    return updated, {}, "", None


def validate_prepared_workflow_binding(
    args: dict[str, Any],
    *,
    current_task: dict[str, Any],
    projection: dict[str, Any],
    current_ctx: Any,
    current_run: dict[str, Any],
    ledger: Any,
) -> PreparedWorkflowBinding:
    """Fail closed before a split execute can create another RUN or lease."""

    requested_phase = str(args.get("phase", "prepare")).strip().lower() or "prepare"
    requested_run_id = str(args.get("run_id") or "").strip()
    requested_wave_id = str(args.get("wave_id") or "").strip()
    if bool(requested_run_id) != bool(requested_wave_id):
        raise ToolFailure(
            "PREPARED_RUN_BINDING_INCOMPLETE",
            "agent_workflow execute must supply run_id and wave_id together when binding a prepared workflow.",
            category="validation",
            retryable=False,
        )
    if requested_run_id and requested_phase != "execute":
        raise ToolFailure(
            "PREPARED_RUN_BINDING_PHASE_INVALID",
            "An exact prepared RUN/WAVE binding is valid only with agent_workflow phase=execute.",
            category="validation",
            retryable=False,
            details={"phase": requested_phase},
        )

    projected_run_id = str(projection.get("run_id") or "").strip()
    projected_wave_id = str(projection.get("wave_id") or "").strip()
    if requested_run_id and (
        projected_run_id != requested_run_id
        or projected_wave_id != requested_wave_id
    ):
        raise ToolFailure(
            "PREPARED_RUN_BINDING_MISMATCH",
            "The requested prepared RUN/WAVE does not match the caller's current scoped task projection.",
            category="runtime",
            retryable=False,
            details={
                "requested_run_id": requested_run_id,
                "requested_wave_id": requested_wave_id,
                "projected_run_id": projected_run_id or None,
                "projected_wave_id": projected_wave_id or None,
            },
        )

    metadata = current_run.get("metadata") if isinstance(current_run.get("metadata"), dict) else {}
    run_phase = str(metadata.get("phase") or "").strip().lower()
    prepared_workflow = str(metadata.get("workflow") or "").strip().lower()
    requested_workflow = str(args.get("workflow", "custom")).strip().lower() or "custom"
    current_task_id = str(current_task.get("task_id") or "").strip()
    run_task_id = str(current_run.get("task_id") or "").strip()
    exact_wave_prepared = False
    if current_ctx is not None:
        exact_wave_prepared = any(
            str(item.get("event_type") or "") == "context_prepared"
            for item in ledger.list_events(current_ctx.run_id, wave_id=current_ctx.wave_id)
        )
    execute_candidate = bool(
        current_ctx is not None
        and requested_phase == "execute"
        and exact_wave_prepared
        and prepared_workflow == requested_workflow
        and str(current_ctx.state) in {"PREFLIGHT", "READY"}
        and current_task_id
        and current_task_id == run_task_id
    )
    if requested_run_id:
        exact_context = bool(
            current_ctx is not None
            and str(current_ctx.run_id) == requested_run_id
            and str(current_ctx.wave_id) == requested_wave_id
        )
        if not exact_context or not execute_candidate:
            raise ToolFailure(
                "PREPARED_RUN_BINDING_MISMATCH",
                "The requested RUN/WAVE is not the caller's current compatible prepare lineage.",
                category="runtime",
                retryable=False,
                details={
                    "requested_run_id": requested_run_id,
                    "requested_wave_id": requested_wave_id,
                    "current_state": str(current_ctx.state) if current_ctx is not None else None,
                    "run_phase": run_phase or None,
                    "prepared_workflow": prepared_workflow or None,
                    "exact_wave_context_prepared": exact_wave_prepared,
                },
            )

    return PreparedWorkflowBinding(
        requested_run_id=requested_run_id,
        requested_wave_id=requested_wave_id,
        execute_candidate=execute_candidate,
        verified=bool(requested_run_id),
    )
