from __future__ import annotations

from typing import Any

from .task_state import command_presentation


class CoordinationStatusMixin:
    """Read-only task-control status projection, kept outside mutation control."""

    def _coordination_get_state(self) -> dict[str, Any]:
        # The stream is not the source of truth after reconnect. Repair the
        # compact view from the SQLite ledger before returning status.
        with self.background_operations_lock:
            memory_operations = {
                item["operation_id"]: self._background_operation_snapshot(item)
                for item in self.background_operations.values()
                if item.get("workspace") == str(self.workspace.root)
            }
        durable_operations = {
            item["operation_id"]: item
            for item in self.orchestration_ledger.list_background_operations(limit=20)
        }
        durable_operations.update(memory_operations)
        operations = sorted(
            durable_operations.values(),
            key=lambda item: str(item.get("updated_at") or item.get("started_at") or ""),
        )
        unresolved_stale_runs = self.orchestration_ledger.stale_run_candidates(
            stale_after_seconds=self.stale_run_seconds
        )
        resources = self.execution_resource_governor.snapshot()
        return {
            "state": command_presentation(
                self.task_state.get(), governor=self.execution_resource_governor,
                workspace=self.task_state.current_workspace(),
            ),
            "resources": resources,
            "operations": operations[-8:],
            "recovery": {
                "orphaned_background_operations": self.orphaned_background_operations,
                "orphaned_idempotency_records": self.orphaned_idempotency_records,
                "stale_orchestration_runs": unresolved_stale_runs,
                "unresolved_stale_orchestration_runs": unresolved_stale_runs,
                "reconciled_stale_orchestration_runs": list(self.reconciled_stale_orchestration_runs),
                "task_orchestration_projection_reconciled": bool(self.reconciled_task_orchestration),
                "agent_lanes_waiting_after_restart": self.recovered_agent_lanes,
            },
        }
