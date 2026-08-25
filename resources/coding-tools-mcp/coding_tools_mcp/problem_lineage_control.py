from __future__ import annotations

"""Trusted task-control adapter for v11 Problem Resolution Lineage events."""

from datetime import datetime, timezone
from typing import Any

from .errors import ToolFailure
from .host_correlation import (
    claim_pending_host_turn,
    consume_pending_host_turn,
    restore_pending_host_turn,
)
from .problem_lineage import ProblemLineageError


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


class ProblemLineageControlMixin:
    """The parent supplies task state, workspace, and the canonical ledger."""

    _PROBLEM_EXPLICIT_TRANSITIONS = frozenset({"open", "confirm", "reopen", "revise", "block", "abandon"})
    _PROBLEM_CALLER_AUTHORITY_FIELDS = frozenset({"provenance", "evidence_level"})
    _PROBLEM_CALLER_CLOCK_FIELDS = frozenset({"occurred_at", "occurred_at_source"})

    def _problem_claim_host_identity(self, event: dict[str, Any]) -> dict[str, Any]:
        claimed = claim_pending_host_turn(
            self.workspace.root,
            process_instance_id=self.process_instance_id,
        )
        if claimed is None:
            raise ToolFailure(
                "PRL_HOST_IDENTITY_UNAVAILABLE",
                "Problem authority requires a current one-shot pending host-turn receipt.",
                category="authorization",
            )
        supplied_turn = str(event.get("turn_id") or "")
        supplied_trace = str(event.get("trace_id") or "")
        if (supplied_turn or supplied_trace) and (
            supplied_turn != str(claimed["turn_id"])
            or supplied_trace != str(claimed["trace_id"])
        ):
            restore_pending_host_turn(self.workspace.root, claimed)
            raise ToolFailure(
                "PRL_HOST_IDENTITY_MISMATCH",
                "Problem authority must match the exact claimed turn and trace identity.",
                category="authorization",
            )
        event["turn_id"] = str(claimed["turn_id"])
        event["trace_id"] = str(claimed["trace_id"])
        return claimed

    def _problem_chatweb_controller_authority(
        self,
        run_id: str = "",
        *,
        controller: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        identity = self._current_hub_client()
        if (
            not isinstance(identity, dict)
            or str(identity.get("client_type") or "") != "chatweb"
            or str(identity.get("role") or "") != "controller"
        ):
            raise ToolFailure(
                "PRL_CHATWEB_CONTROLLER_REQUIRED",
                "A current ChatWeb Execution Hub controller identity is required.",
                category="authorization",
            )
        try:
            touched = self._touch_hub_client(identity)
        except (TypeError, ValueError) as exc:
            raise ToolFailure(
                "PRL_CHATWEB_CONTROLLER_REQUIRED",
                "The current ChatWeb Execution Hub identity could not be verified.",
                category="authorization",
            ) from exc
        current_client = touched.get("client") if isinstance(touched, dict) and isinstance(touched.get("client"), dict) else touched
        client_id = self._hub_client_record_id(identity)
        if (
            str(current_client.get("client_id") or "") != client_id
            or str(current_client.get("client_type") or "") != "chatweb"
            or str(current_client.get("role") or "") != "controller"
            or str(current_client.get("status") or "") != "online"
            or str(current_client.get("runtime_instance_id") or "") != self.process_instance_id
        ):
            raise ToolFailure(
                "PRL_CHATWEB_CONTROLLER_REQUIRED",
                "The ChatWeb controller is not current in this MCP runtime.",
                category="authorization",
            )
        authority = {
            "client_id": client_id,
            "client_type": "chatweb",
            "runtime_instance_id": self.process_instance_id,
        }
        if run_id:
            exact = controller if isinstance(controller, dict) else self._require_hub_controller(run_id)
            if not isinstance(exact, dict):
                raise ToolFailure(
                    "CONTROLLER_LEASE_REQUIRED",
                    "The exact run requires a current ChatWeb controller lease.",
                    category="security",
                    retryable=True,
                    details={"run_id": run_id},
                )
            assertion = self.orchestration_ledger.assert_controller_lease(
                run_id=run_id,
                owner_client_id=client_id,
                lease_id=str(exact.get("lease_id") or ""),
                fencing_token=int(exact.get("fencing_token") or 0),
            )
            if assertion.get("valid") is not True:
                raise ToolFailure(
                    "CONTROLLER_LEASE_REQUIRED",
                    "The exact ChatWeb controller lease is missing or stale.",
                    category="security",
                    retryable=True,
                    details={"run_id": run_id, "reason": assertion.get("reason")},
                )
            authority.update({
                "lease_id": str(exact.get("lease_id") or ""),
                "fencing_token": int(exact.get("fencing_token") or 0),
            })
        return authority

    def _problem_validate_exact_references(self, event: dict[str, Any]) -> None:
        run_id, wave_id = str(event.get("run_id") or "").strip(), str(event.get("wave_id") or "").strip()
        if run_id:
            if self.orchestration_ledger.get_run(run_id) is None:
                raise ToolFailure("PRL_RUN_NOT_FOUND", "Problem event references an unknown exact run identity.", category="validation")
            if wave_id and not any(str(item.get("wave_id") or "") == wave_id for item in self.orchestration_ledger.list_waves(run_id)):
                raise ToolFailure("PRL_WAVE_NOT_FOUND", "Problem event wave does not belong to its exact run identity.", category="validation")
        elif wave_id:
            raise ToolFailure("PRL_RUN_REQUIRED_FOR_WAVE", "Problem event wave identity requires its exact run identity.", category="validation")
    @staticmethod
    def _problem_runtime_authority(event: dict[str, Any]) -> str:
        operation = str(event.get("operation") or "").strip().lower()
        provenance = str(event.get("provenance") or "").strip().upper()
        intent = str(event.get("feedback_intent") or "UNKNOWN").strip().upper()
        if operation == "provisional_resolve":
            raise ToolFailure("PRL_TRANSITION_RUNTIME_ONLY", "Provisional resolution is created only by the accepted EOCL bridge.", category="authorization")
        if operation == "link":
            raise ToolFailure("PRL_BINDING_RUNTIME_ONLY", "Problem binding is created only by the internal host/run binding workflow.", category="authorization")
        if operation == "observe_feedback":
            return "RUNTIME_OBSERVATION"
        if operation == "open":
            if provenance == "CONTROLLER_REPORTED_EXPLICIT_USER": return "RUNTIME_EXPLICIT_USER"
        if operation == "confirm":
            if intent != "CONFIRM_RESOLVED":
                raise ToolFailure("PRL_CONFIRM_INTENT_REQUIRED", "confirm requires structured feedback_intent=CONFIRM_RESOLVED.", category="validation")
            if provenance == "CONTROLLER_REPORTED_EXPLICIT_USER": return "RUNTIME_EXPLICIT_USER"
        if operation == "reopen":
            if intent not in {"SAME_PROBLEM_STILL_FAILING", "PARTIAL_RESOLUTION", "CORRECT_UNDERSTANDING", "CORRECT_TARGET_OR_SCOPE", "CORRECT_TECHNICAL_RESULT", "CORRECT_PROOF_OR_VERIFICATION"}:
                raise ToolFailure("PRL_REOPEN_INTENT_REQUIRED", "reopen requires a structured same-problem correction intent.", category="validation")
            if provenance == "CONTROLLER_REPORTED_EXPLICIT_USER": return "RUNTIME_EXPLICIT_USER"
        if operation == "revise":
            if provenance == "CONTROLLER_REPORTED_EXPLICIT_USER": return "RUNTIME_EXPLICIT_USER"
        if operation == "block":
            if provenance == "CONTROLLER_REPORTED_EXPLICIT_USER": return "RUNTIME_EXPLICIT_USER"
        if operation == "abandon":
            if provenance == "CONTROLLER_REPORTED_EXPLICIT_USER": return "RUNTIME_EXPLICIT_USER"
        raise ToolFailure("PRL_TRANSITION_AUTHORITY_REQUIRED", "This operation requires explicit-user, reviewed, or deterministic runtime authority; host identity and model inference are insufficient.", category="authorization")

    def _problem_source_identity_for_run(self, run_id: str) -> dict[str, Any]:
        run = self.orchestration_ledger.get_run(run_id)
        metadata = run.get("metadata") if isinstance(run, dict) and isinstance(run.get("metadata"), dict) else {}
        workspace_identity = metadata.get("workspace_identity") if isinstance(metadata.get("workspace_identity"), dict) else {}
        scope_root = self._workspace_root_for_identity(workspace_identity.get("root_id")) or self.workspace.root
        identity = self._orchestration_workspace_identity(str(scope_root))
        if workspace_identity:
            self._assert_orchestration_workspace_scope(identity.get("workspace_identity") or {}, run_id=run_id)
        return identity

    def _problem_reconcile_after_checkpoint(
        self,
        *,
        run_id: str,
        wave_id: str,
        checkpoint_id: str,
        identity: dict[str, Any],
    ) -> dict[str, Any]:
        try:
            result = self.orchestration_ledger.problem_reconcile_provisional_from_checkpoint(
                run_id=run_id,
                wave_id=wave_id,
                checkpoint_id=checkpoint_id,
                current_git_head=str(identity.get("base_head") or ""),
                current_worktree_fp=str(identity.get("worktree_fp") or ""),
                now=_utc_now(),
            )
        except Exception as exc:
            return {
                "recorded": False,
                "status": "RECONCILIATION_REQUIRED",
                "reason": "bridge_append_failed",
                "error_type": type(exc).__name__,
            }
        if result.get("recorded") is not True and result.get("idempotent") is not True:
            return {**result, "status": "RECONCILIATION_REQUIRED"}
        return result

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
        if operation == "reconcile_provisional":
            if set(event) != {"operation", "run_id", "wave_id", "checkpoint_id"}:
                raise ToolFailure(
                    "PRL_RECONCILIATION_CONTRACT_INVALID",
                    "reconcile_provisional accepts only exact run, wave, and checkpoint identities.",
                    category="validation",
                )
            self._problem_validate_exact_references(event)
            self._problem_chatweb_controller_authority(str(event["run_id"]))
            identity = self._problem_source_identity_for_run(str(event["run_id"]))
            result = self._problem_reconcile_after_checkpoint(
                run_id=str(event["run_id"]),
                wave_id=str(event["wave_id"]),
                checkpoint_id=str(event["checkpoint_id"]),
                identity=identity,
            )
            if result.get("status") == "RECONCILIATION_REQUIRED":
                raise ToolFailure(
                    "PRL_RECONCILIATION_REQUIRED",
                    "The exact accepted checkpoint could not be reconciled to a provisional outcome.",
                    category="runtime",
                    retryable=True,
                    details={"run_id": event["run_id"], "wave_id": event["wave_id"], "checkpoint_id": event["checkpoint_id"], "reason": result.get("reason")},
                )
            return {
                "problem": result,
                "receipt_id": str((result.get("event") or {}).get("event_hash") or ""),
                "authority": {"transition_authority": "RUNTIME_RECONCILIATION", "execution_acceptance_changed": False, "source_mutation_performed": False, "p5_assignment_created": False},
            }
        supplied_provenance = str(event.get("provenance") or "").strip().upper()
        if supplied_provenance == "HUMAN_ANNOTATED":
            raise ToolFailure("PRL_HUMAN_REVIEW_RECEIPT_REQUIRED", "Human-annotated authority is disabled until an exact review receipt contract exists.", category="authorization")
        if operation == "link":
            raise ToolFailure("PRL_BINDING_RUNTIME_ONLY", "Problem binding is created only by the internal host/run binding workflow.", category="authorization")
        if operation == "provisional_resolve":
            raise ToolFailure("PRL_TRANSITION_RUNTIME_ONLY", "Provisional resolution is created only by the accepted EOCL bridge.", category="authorization")
        if operation == "block" and supplied_provenance == "DETERMINISTIC_EVIDENCE":
            raise ToolFailure("PRL_GUARD_RUNTIME_ONLY", "Deterministic problem guards are emitted only by trusted runtime checks.", category="authorization")
        if any(name in event for name in self._PROBLEM_CALLER_CLOCK_FIELDS):
            raise ToolFailure("PRL_CLOCK_FIELDS_FORBIDDEN", "Public semantic events cannot supply occurrence clock authority.", category="authorization")
        if any(name in event for name in self._PROBLEM_CALLER_AUTHORITY_FIELDS):
            raise ToolFailure("PRL_CALLER_AUTHORITY_FORBIDDEN", "Public problem events cannot supply provenance or evidence authority.", category="authorization")
        if not str(event.get("task_id") or "").strip():
            event["task_id"] = str(self.task_state.get().get("task_id") or "").strip()
        self._problem_validate_exact_references(event)
        if operation not in self._PROBLEM_EXPLICIT_TRANSITIONS and operation != "observe_feedback":
            raise ToolFailure("PRL_TRANSITION_AUTHORITY_REQUIRED", "The public problem operation has no trusted runtime adapter.", category="authorization")
        self._problem_chatweb_controller_authority(str(event.get("run_id") or ""))
        claimed = self._problem_claim_host_identity(event)
        event["provenance"] = "HOST_OBSERVED" if operation == "observe_feedback" else "CONTROLLER_REPORTED_EXPLICIT_USER"
        event["evidence_level"] = "OBSERVED"
        authority = self._problem_runtime_authority(event)
        try:
            result = self.orchestration_ledger.problem_record_event(event, now=_utc_now(), authority_context=authority)
        except ProblemLineageError as exc:
            restore_pending_host_turn(self.workspace.root, claimed)
            code = "PRL_SCHEMA_NOT_ACTIVATED" if "schema is not activated" in str(exc) else "PRL_EVENT_INVALID"
            raise ToolFailure(code, str(exc), category="validation") from exc
        except Exception:
            restore_pending_host_turn(self.workspace.root, claimed)
            raise
        consume_pending_host_turn(claimed)
        return {
            "problem": result,
            "receipt_id": str((result.get("event") or {}).get("event_hash") or ""),
            "authority": {"transition_authority": authority, "execution_acceptance_changed": False, "source_mutation_performed": False, "p5_assignment_created": False},
        }
