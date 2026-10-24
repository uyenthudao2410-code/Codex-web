from __future__ import annotations

import hashlib
from typing import Any

from .errors import ToolFailure
from .task_state import TaskStateStore


class RuntimeStatelessContextMixin:
    """Exact-run recovery for stateless ChatWeb application contexts."""

    def _panel_binding_stores(self, root: Any) -> list[TaskStateStore]:
        """Every persisted task-state store of this workspace, de-duplicated.

        The panel's displayed RUN comes from the canonical ledger, while the
        task state that binds it may live in the current request context, the
        unscoped workspace projection, or any persisted ``mcp2026:*`` scoped
        context of the same workspace.  Enumerate all of them by exact path so
        the binding check never has to guess from a single shared slot.
        """
        stores: list[TaskStateStore] = []
        seen: set[str] = set()

        def add(store: TaskStateStore) -> None:
            try:
                key = str(store.path.resolve(strict=False))
            except (OSError, RuntimeError):
                return
            if key not in seen:
                seen.add(key)
                stores.append(store)

        try:
            add(self.task_state._current_store())
        except Exception:
            pass
        add(TaskStateStore(root))
        try:
            context_ids = self.workspace_context_registry.context_ids_for_workspace(root)
        except Exception:
            context_ids = []
        for context_id in context_ids:
            add(TaskStateStore(root, scope_id=f"mcp2026:{context_id}"))
        context_dir = root / ".coding-tools" / "task-contexts"
        if context_dir.is_dir():
            for path in sorted(context_dir.glob("*.json")):
                if path.name.endswith("-history.json"):
                    continue
                try:
                    add(TaskStateStore._from_context_projection_path(root, path))
                except (OSError, ValueError):
                    continue
        return stores

    def panel_handoff_state(self, run_id: object, wave_id: object = "") -> tuple[dict[str, Any], dict[str, Any], str, str, str]:
        """Resolve the panel RUN's exact task binding without adopting a context.

        The authenticated panel displays the RUN from the canonical ledger
        (Electron ``task-state:read`` merges the ledger's current run), while
        the binding task state may be persisted in the unscoped projection or
        in the scoped store that owns the RUN.  The previous gate demanded
        that the single unscoped workspace file simultaneously match the
        RUN, its current wave, and the canonical task; any other activity in
        the same workspace (a finished task, an auto-started replacement, a
        scoped ChatWeb context) overwrote that shared slot and made panel
        handoff fail deterministically, with Refresh unable to help because
        the display and the gate read different sources.

        The binding is still exact and never falls back to another RUN: the
        ledger must hold the RUN with a canonical task id, a persisted task
        state of this workspace must bind that exact task id to that exact
        RUN (current projection, or an archived history entry when the
        owning store no longer points at a different active RUN), and a
        caller-supplied wave must equal the RUN's current wave.  The wave
        stamped on the capsule always comes from the orchestration snapshot,
        not from a possibly stale file projection.  This adapter grants no
        controller or write authority and does not adopt a task context.
        (``stateless_task_context_for_run`` is deliberately not reused: its
        controller-lease guard and multi-match failure are context-adoption
        semantics for ChatWeb, and the panel path must stay independent of
        them.)
        """
        requested_run = str(run_id or "").strip()
        if not requested_run:
            raise ToolFailure(
                "HANDOFF_RUN_REQUIRED", "Panel handoff requires the displayed RUN.",
                category="validation", retryable=False,
            )
        root = self._current_request_workspace_root()
        ledger = self._orchestration_ledger_for_root(root)
        canonical_run = ledger.get_run(requested_run)
        canonical_task_id = (
            str(canonical_run.get("task_id") or "").strip() if isinstance(canonical_run, dict) else ""
        )
        context = self.orchestration_control.snapshot(requested_run)
        current_wave = str(context.wave_id or "") if context is not None else ""
        requested_wave = str(wave_id or "").strip()

        def binds(state: object) -> bool:
            if not isinstance(state, dict) or not canonical_task_id:
                return False
            projection = state.get("orchestration") if isinstance(state.get("orchestration"), dict) else {}
            return (
                str(projection.get("run_id") or "") == requested_run
                and str(state.get("task_id") or "") == canonical_task_id
                and bool(str(state.get("objective") or "").strip())
            )

        binding_state: dict[str, Any] | None = None
        stores = self._panel_binding_stores(root)
        currents: list[tuple[TaskStateStore, dict[str, Any]]] = []
        for store in stores:
            try:
                current = store.get()
            except Exception:
                continue
            currents.append((store, current))
            if binding_state is None and binds(current):
                binding_state = current
        if binding_state is None and canonical_task_id:
            # Archived binding: the owning context has since moved on, but
            # its history still proves this exact task owned this exact RUN.
            # Mirror the stateless recovery guards: never accept the archive
            # of a store that now points at a different active RUN or that
            # holds an unacknowledged operator completion report.
            for store, current in currents:
                if TaskStateStore._pending_completion_report_from_state(current) is not None:
                    continue
                current_projection = (
                    current.get("orchestration") if isinstance(current.get("orchestration"), dict) else {}
                )
                current_run_id = str(current_projection.get("run_id") or "").strip()
                if current_run_id and current_run_id != requested_run:
                    current_run = ledger.get_run(current_run_id)
                    if not isinstance(current_run, dict) or str(current_run.get("status") or "") == "active":
                        continue
                try:
                    history = store.history(limit=100)
                except Exception:
                    continue
                archived = next((item for item in history if binds(item)), None)
                if archived is not None:
                    binding_state = archived
                    break

        failed_checks: list[str] = []
        run_status = (
            str(canonical_run.get("status") or "") if isinstance(canonical_run, dict) else ""
        )
        if not isinstance(canonical_run, dict):
            failed_checks.append("canonical_run_missing")
        if context is None:
            failed_checks.append("orchestration_snapshot_missing")
        elif not current_wave:
            failed_checks.append("current_wave_missing")
        if not canonical_task_id:
            failed_checks.append("canonical_task_id_missing")
        if requested_wave and requested_wave != current_wave:
            failed_checks.append("caller_wave_mismatch")
        if binding_state is None:
            failed_checks.append("exact_task_binding_missing")
        if failed_checks:
            unscoped = TaskStateStore(root).get()
            unscoped_projection = (
                unscoped.get("orchestration") if isinstance(unscoped.get("orchestration"), dict) else {}
            )
            raise ToolFailure(
                "HANDOFF_PANEL_BINDING_MISMATCH",
                "The displayed panel RUN/WAVE no longer has an exact task binding; refresh the panel.",
                category="runtime", retryable=False,
                details={
                    "run_id": requested_run,
                    "run_status": run_status or None,
                    "failed_checks": failed_checks,
                    "canonical_task_id": canonical_task_id or None,
                    "current_wave": current_wave or None,
                    "requested_wave": requested_wave or None,
                    "binding_found": False,
                    "candidate_stores_checked": len(currents),
                    "unscoped_run_id": str(unscoped_projection.get("run_id") or "") or None,
                    "unscoped_task_id": str(unscoped.get("task_id") or "") or None,
                },
            )
        return binding_state, context.projection(), requested_run, current_wave, run_status

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
