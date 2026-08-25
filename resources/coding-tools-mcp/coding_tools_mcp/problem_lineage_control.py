from __future__ import annotations

"""Trusted task-control adapter for v11 Problem Resolution Lineage events."""

from datetime import datetime, timezone
from typing import Any

from .errors import ToolFailure
from .host_correlation import peek_pending_host_turn
from .problem_lineage import ProblemLineageError


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


class ProblemLineageControlMixin:
    """The parent supplies task state, workspace, and the canonical ledger."""

    def _problem_pending_host_identity(self) -> dict[str, str] | None:
        pending = peek_pending_host_turn(self.workspace.root)
        return None if pending is None else {"turn_id": str(pending["turn_id"]), "trace_id": str(pending["trace_id"])}

    def _problem_fill_or_validate_host_identity(self, event: dict[str, Any]) -> None:
        if str(event.get("provenance") or "").upper() != "HOST_OBSERVED":
            return
        pending = self._problem_pending_host_identity()
        if pending is None:
            raise ToolFailure("PRL_HOST_IDENTITY_UNAVAILABLE", "Host-observed lineage requires a current content-free pending host identity.", category="validation")
        supplied_turn, supplied_trace = str(event.get("turn_id") or ""), str(event.get("trace_id") or "")
        if not supplied_turn and not supplied_trace:
            event["turn_id"], event["trace_id"] = pending["turn_id"], pending["trace_id"]
            return
        if supplied_turn != pending["turn_id"] or supplied_trace != pending["trace_id"]:
            raise ToolFailure("PRL_HOST_IDENTITY_MISMATCH", "Host-observed lineage must match the exact pending turn and trace identity.", category="validation")

    def _problem_validate_exact_references(self, event: dict[str, Any]) -> None:
        run_id, wave_id = str(event.get("run_id") or "").strip(), str(event.get("wave_id") or "").strip()
        if run_id:
            if self.orchestration_ledger.get_run(run_id) is None:
                raise ToolFailure("PRL_RUN_NOT_FOUND", "Problem event references an unknown exact run identity.", category="validation")
            if wave_id and not any(str(item.get("wave_id") or "") == wave_id for item in self.orchestration_ledger.list_waves(run_id)):
                raise ToolFailure("PRL_WAVE_NOT_FOUND", "Problem event wave does not belong to its exact run identity.", category="validation")
        elif wave_id:
            raise ToolFailure("PRL_RUN_REQUIRED_FOR_WAVE", "Problem event wave identity requires its exact run identity.", category="validation")
        self._problem_fill_or_validate_host_identity(event)

    @staticmethod
    def _problem_runtime_authority(event: dict[str, Any]) -> str:
        operation = str(event.get("operation") or "").strip().lower()
        provenance = str(event.get("provenance") or "").strip().upper()
        intent = str(event.get("feedback_intent") or "UNKNOWN").strip().upper()
        if operation == "provisional_resolve":
            raise ToolFailure("PRL_TRANSITION_RUNTIME_ONLY", "Provisional resolution is created only by the accepted EOCL bridge.", category="authorization")
        if operation == "link":
            return "RUNTIME_BINDING"
        if operation == "observe_feedback":
            return "RUNTIME_OBSERVATION"
        if operation == "open":
            if provenance == "CONTROLLER_REPORTED_EXPLICIT_USER": return "RUNTIME_EXPLICIT_USER"
            if provenance == "HUMAN_ANNOTATED": return "RUNTIME_HUMAN_REVIEW"
        if operation == "confirm":
            if intent != "CONFIRM_RESOLVED":
                raise ToolFailure("PRL_CONFIRM_INTENT_REQUIRED", "confirm requires structured feedback_intent=CONFIRM_RESOLVED.", category="validation")
            if provenance == "CONTROLLER_REPORTED_EXPLICIT_USER": return "RUNTIME_EXPLICIT_USER"
            if provenance == "HUMAN_ANNOTATED": return "RUNTIME_HUMAN_REVIEW"
        if operation == "reopen":
            if intent not in {"SAME_PROBLEM_STILL_FAILING", "PARTIAL_RESOLUTION", "CORRECT_UNDERSTANDING", "CORRECT_TARGET_OR_SCOPE", "CORRECT_TECHNICAL_RESULT", "CORRECT_PROOF_OR_VERIFICATION"}:
                raise ToolFailure("PRL_REOPEN_INTENT_REQUIRED", "reopen requires a structured same-problem correction intent.", category="validation")
            if provenance == "CONTROLLER_REPORTED_EXPLICIT_USER": return "RUNTIME_EXPLICIT_USER"
            if provenance == "HUMAN_ANNOTATED": return "RUNTIME_HUMAN_REVIEW"
        if operation == "revise":
            if provenance == "CONTROLLER_REPORTED_EXPLICIT_USER": return "RUNTIME_EXPLICIT_USER"
            if provenance == "HUMAN_ANNOTATED": return "RUNTIME_HUMAN_REVIEW"
        if operation == "block":
            if provenance == "DETERMINISTIC_EVIDENCE": return "RUNTIME_GUARD"
            if provenance == "CONTROLLER_REPORTED_EXPLICIT_USER": return "RUNTIME_EXPLICIT_USER"
            if provenance == "HUMAN_ANNOTATED": return "RUNTIME_HUMAN_REVIEW"
        if operation == "abandon":
            if provenance == "CONTROLLER_REPORTED_EXPLICIT_USER": return "RUNTIME_EXPLICIT_USER"
            if provenance == "HUMAN_ANNOTATED": return "RUNTIME_HUMAN_REVIEW"
        raise ToolFailure("PRL_TRANSITION_AUTHORITY_REQUIRED", "This operation requires explicit-user, reviewed, or deterministic runtime authority; host identity and model inference are insufficient.", category="authorization")

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
            event["task_id"] = str(self.task_state.get().get("task_id") or "").strip()
        self._problem_validate_exact_references(event)
        authority = self._problem_runtime_authority(event)
        try:
            result = self.orchestration_ledger.problem_record_event(event, now=_utc_now(), authority_context=authority)
        except ProblemLineageError as exc:
            code = "PRL_SCHEMA_NOT_ACTIVATED" if "schema is not activated" in str(exc) else "PRL_EVENT_INVALID"
            raise ToolFailure(code, str(exc), category="validation") from exc
        return {
            "problem": result,
            "authority": {"transition_authority": authority, "execution_acceptance_changed": False, "source_mutation_performed": False, "p5_assignment_created": False},
        }
