from __future__ import annotations

"""Nested task-control adapter for typed Problem Resolution Lineage events."""

from datetime import datetime, timezone
from typing import Any

from .errors import ToolFailure
from .host_correlation import peek_pending_host_turn
from .problem_lineage import ProblemLineageError


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


class ProblemLineageControlMixin:
    """The parent supplies task state, workspace, hub identity, and ledger."""

    def _problem_pending_host_identity(self) -> dict[str, str] | None:
        """Peek, never consume, the short-lived content-free host identity."""
        pending = peek_pending_host_turn(self.workspace.root)
        if pending is None:
            return None
        return {"turn_id": str(pending["turn_id"]), "trace_id": str(pending["trace_id"])}

    def _problem_validate_exact_references(self, event: dict[str, Any]) -> None:
        run_id = str(event.get("run_id") or "").strip()
        wave_id = str(event.get("wave_id") or "").strip()
        if run_id:
            run = self.orchestration_ledger.get_run(run_id)
            if run is None:
                raise ToolFailure("PRL_RUN_NOT_FOUND", "Problem event references an unknown exact run identity.", category="validation")
            if wave_id and not any(str(item.get("wave_id") or "") == wave_id for item in self.orchestration_ledger.list_waves(run_id)):
                raise ToolFailure("PRL_WAVE_NOT_FOUND", "Problem event wave does not belong to its exact run identity.", category="validation")
        elif wave_id:
            raise ToolFailure("PRL_RUN_REQUIRED_FOR_WAVE", "Problem event wave identity requires its exact run identity.", category="validation")

        if str(event.get("provenance") or "").upper() == "HOST_OBSERVED":
            pending = self._problem_pending_host_identity()
            if pending is None:
                raise ToolFailure("PRL_HOST_IDENTITY_UNAVAILABLE", "Host-observed lineage requires a current content-free pending host identity.", category="validation")
            if str(event.get("turn_id") or "") != pending["turn_id"] or str(event.get("trace_id") or "") != pending["trace_id"]:
                raise ToolFailure("PRL_HOST_IDENTITY_MISMATCH", "Host-observed lineage must match the exact pending turn and trace identity.", category="validation")

    def _problem_control(self, args: dict[str, Any]) -> dict[str, Any]:
        request = args.get("problem_event")
        if not isinstance(request, dict):
            raise ToolFailure("PRL_EVENT_REQUIRED", "task_control action=problem requires a typed problem_event object.", category="validation")
        event = dict(request)
        operation = str(event.get("operation") or "").strip().lower()
        if operation == "get":
            try:
                result = self.orchestration_ledger.problem_get(str(event.get("problem_id") or ""))
            except ProblemLineageError as exc:
                code = "PRL_SCHEMA_NOT_ACTIVATED" if "schema is not activated" in str(exc) else "PRL_EVENT_INVALID"
                raise ToolFailure(code, str(exc), category="validation") from exc
            if result is None:
                raise ToolFailure("PRL_PROBLEM_NOT_FOUND", "Problem lineage identity was not found.", category="not_found")
            return {"problem": result}

        if not str(event.get("task_id") or "").strip():
            current = self.task_state.get()
            event["task_id"] = str(current.get("task_id") or "").strip()
        self._problem_validate_exact_references(event)
        try:
            result = self.orchestration_ledger.problem_record_event(event, now=_utc_now())
        except ProblemLineageError as exc:
            code = "PRL_SCHEMA_NOT_ACTIVATED" if "schema is not activated" in str(exc) else "PRL_EVENT_INVALID"
            raise ToolFailure(code, str(exc), category="validation") from exc
        return {
            "problem": result,
            "authority": {
                "execution_acceptance_changed": False,
                "source_mutation_performed": False,
                "p5_assignment_created": False,
            },
        }
