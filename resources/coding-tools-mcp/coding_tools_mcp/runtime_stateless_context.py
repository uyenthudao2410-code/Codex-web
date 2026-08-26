from __future__ import annotations

import hashlib
from typing import Any

from .task_state import TaskStateStore


class RuntimeStatelessContextMixin:
    """Exact-run recovery for stateless ChatWeb application contexts."""

    def stateless_task_context_for_run(self, run_id: object, *, logical_client_id: str = "chatweb") -> str:
        expected_run_id = str(run_id or "").strip()
        logical_client = str(logical_client_id or "").strip()
        if not expected_run_id or not logical_client:
            return ""
        root = self._known_run_workspace(expected_run_id)
        if root is None:
            return ""
        matches: list[str] = []
        for context_id in self.workspace_context_registry.context_ids_for_workspace(root):
            store = TaskStateStore(root, scope_id=f"mcp2026:{context_id}")
            if not store.path.exists():
                continue
            state = store.get()
            projection = state.get("orchestration") if isinstance(state.get("orchestration"), dict) else {}
            if str(projection.get("run_id") or "").strip() == expected_run_id:
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
        controller = self._orchestration_ledger_for_root(root).get_controller_lease(expected_run_id)
        if (
            isinstance(controller, dict)
            and controller.get("status") == "active"
            and str(controller.get("owner_client_id") or "") != expected_owner
        ):
            return ""
        return context_id
