from __future__ import annotations

import hashlib
from typing import Any

from .errors import ToolFailure
from .task_state import TaskStateStore


class RuntimeStatelessContextMixin:
    """Exact-run recovery for stateless ChatWeb application contexts."""

    def panel_handoff_state(self, run_id: object, wave_id: object = "") -> tuple[dict[str, Any], dict[str, Any], str, str]:
        """Read the panel's exact projection without adopting a task context.

        The authenticated panel reads this same unscoped workspace projection.
        Its client label selects this adapter; it grants no controller or write
        authority. A stale or missing selection must not fall back to another RUN.
        """
        requested_run = str(run_id or "").strip()
        if not requested_run:
            raise ToolFailure(
                "HANDOFF_RUN_REQUIRED", "Panel handoff requires the displayed RUN.",
                category="validation", retryable=False,
            )
        state = TaskStateStore(self._current_request_workspace_root()).get()
        projection = state.get("orchestration") if isinstance(state.get("orchestration"), dict) else {}
        canonical_run = self.orchestration_ledger.get_run(requested_run)
        context = self.orchestration_control.snapshot(requested_run)
        current_wave = str(context.wave_id or "") if context is not None else ""
        if (
            not isinstance(canonical_run, dict)
            or context is None or not current_wave
            or str(projection.get("run_id") or "") != requested_run
            or str(projection.get("wave_id") or "") != current_wave
            or not str(canonical_run.get("task_id") or "").strip()
            or str(state.get("task_id") or "") != str(canonical_run.get("task_id") or "")
            or not str(state.get("objective") or "").strip()
            or (str(wave_id or "").strip() and str(wave_id).strip() != current_wave)
        ):
            raise ToolFailure(
                "HANDOFF_PANEL_BINDING_MISMATCH",
                "The displayed panel RUN/WAVE no longer has an exact task binding; refresh the panel.",
                category="runtime", retryable=False,
                details={"run_id": requested_run},
            )
        return state, context.projection(), requested_run, current_wave

    def stateless_task_context_for_run(self, run_id: object, *, logical_client_id: str = "chatweb") -> str:
        expected_run_id = str(run_id or "").strip()
        logical_client = str(logical_client_id or "").strip()
        if not expected_run_id or not logical_client:
            return ""
        root = self._known_run_workspace(expected_run_id)
        if root is None:
            return ""
        ledger = self._orchestration_ledger_for_root(root)
        canonical_run = ledger.get_run(expected_run_id)
        canonical_task_id = str((canonical_run or {}).get("task_id") or "").strip()
        if not canonical_task_id:
            return ""
        matches: list[str] = []
        for context_id in self.workspace_context_registry.context_ids_for_workspace(root):
            store = TaskStateStore(root, scope_id=f"mcp2026:{context_id}")
            if not store.path.exists():
                continue
            state = store.get()
            projection = state.get("orchestration") if isinstance(state.get("orchestration"), dict) else {}
            projected_run_id = str(projection.get("run_id") or "").strip()
            if projected_run_id == expected_run_id:
                matches.append(context_id)
                continue
            if TaskStateStore._pending_completion_report_from_state(state) is not None:
                continue
            has_task = TaskStateStore._has_task(state)
            if has_task and str(state.get("status") or "").strip().lower() not in {
                "completed",
                "failed",
                "stopped",
            }:
                continue
            projected_state = str(projection.get("orchestration_state") or "").strip().upper()
            if projected_state and projected_state not in {"CHECKPOINTED", "BLOCKED", "ABORTED"}:
                continue
            if projected_run_id:
                projected_run = ledger.get_run(projected_run_id)
                if not isinstance(projected_run, dict) or str(projected_run.get("status") or "") == "active":
                    continue
            archived_match = any(
                isinstance(item, dict)
                and str(item.get("task_id") or "").strip() == canonical_task_id
                and str(
                    (item.get("orchestration") if isinstance(item.get("orchestration"), dict) else {}).get("run_id")
                    or ""
                ).strip() == expected_run_id
                for item in store.history(limit=100)
            )
            if archived_match:
                matches.append(context_id)
        matches = sorted(set(matches))
        if len(matches) > 1:
            raise ValueError("exact run maps to multiple persisted stateless task contexts")
        if not matches:
            return ""
        context_id = matches[0]
        execution_context_id = "mcp2026:" + hashlib.sha256(
            f"mcp2026-task:{context_id}".encode("utf-8")
        ).hexdigest()[:56]
        expected_owner = self._hub_client_record_id({
            "client_id": logical_client,
            "client_type": "chatweb",
            "execution_context_id": execution_context_id,
        })
        controller = ledger.get_controller_lease(expected_run_id)
        if (
            isinstance(controller, dict)
            and controller.get("status") == "active"
            and str(controller.get("owner_client_id") or "") != expected_owner
        ):
            return ""
        return context_id
