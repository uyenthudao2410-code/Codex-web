from __future__ import annotations

import time
from typing import Any

from .errors import ToolFailure
from .lifecycle_census import lifecycle_census, open_lifecycle_census_snapshot, read_task_projection


class ActivationLifecycleMixin:
    """Runtime activation admission and immutable lifecycle snapshot helpers."""

    def _activation_owned_codex_sidecar_rows(self, managed: dict[str, Any]) -> list[dict[str, Any]]:
        bridge_job_id = str(getattr(self._codex_bridge, "_managed_job_id", "") or "")
        if not bridge_job_id:
            return []
        jobs = managed.get("jobs") if isinstance(managed.get("jobs"), list) else []
        return [
            row
            for row in jobs
            if isinstance(row, dict)
            and str(row.get("job_id") or "") == bridge_job_id
            and str(row.get("owner") or "") == "codex-app-server"
            and str(row.get("command_id") or "").startswith("codex-app-server-")
            and str(row.get("resource_class") or "") == "MEDIUM"
            and not str(row.get("run_id") or "")
            and not str(row.get("wave_id") or "")
            and str(row.get("lifecycle_state") or "") in {"starting", "running", "terminating", "orphaned"}
        ]

    def _activation_cleanup_locked(self) -> None:
        fence = self.activation_fence
        if fence and int(fence.get("expires_at_unix_ms") or 0) <= int(time.time() * 1000):
            self.activation_fence = None

    def _activation_enter_tool_call(self, name: str = "", args: dict[str, Any] | None = None) -> None:
        with self.activation_lock:
            self._activation_cleanup_locked()
            if self.activation_fence:
                if name == "task_control" and str((args or {}).get("action") or "").lower() == "restart_runtime":
                    self.active_tool_calls += 1
                    return
                raise ToolFailure(
                    "RUNTIME_ACTIVATION_PENDING",
                    "The runtime is draining for a controlled code activation; retry after reconnect.",
                    category="runtime",
                    retryable=True,
                    details={"operation_id": str(self.activation_fence.get("operation_id") or "")},
                )
            self.active_tool_calls += 1

    def _activation_leave_tool_call(self) -> None:
        with self.activation_lock:
            self.active_tool_calls = max(0, int(self.active_tool_calls) - 1)

    def _activation_lifecycle_summary(self) -> dict[str, Any]:
        """Project activation blockers from one immutable Gate 0 snapshot."""
        observed_at = time.time()
        with open_lifecycle_census_snapshot(self.workspace.root) as snapshot:
            census = lifecycle_census(
                snapshot,
                workspace=self.workspace.root,
                observed_at=observed_at,
                grace_seconds=15 * 60,
                stale_after_seconds=self.stale_run_seconds,
                projection=read_task_projection(self.workspace.root),
            )
        run_ids_by_class: dict[str, list[str]] = {}
        for item in census.get("runs", []):
            if not isinstance(item, dict):
                continue
            classification = str(item.get("classification") or "")
            run_id = str(item.get("run_id") or "")
            if classification and run_id:
                run_ids_by_class.setdefault(classification, []).append(run_id)
        return {
            "snapshot": dict(census.get("snapshot") or {}),
            "classification_counts": dict((census.get("summary") or {}).get("run_classification_counts") or {}),
            "run_ids_by_class": {key: sorted(values)[:20] for key, values in sorted(run_ids_by_class.items())},
            "unexplained_active_runs": int((census.get("summary") or {}).get("unexplained_active_runs") or 0),
            "unbound_live_resource_residues": int((census.get("summary") or {}).get("unbound_live_resource_residues") or 0),
            "unbound_live_resources": [
                dict(item) for item in census.get("unbound_live_resources", [])
                if isinstance(item, dict)
            ],
            "p5_lifecycles": sorted({
                str(item.get("p5_epoch_lifecycle") or "")
                for item in census.get("runs", [])
                if isinstance(item, dict) and str(item.get("classification") or "") == "P5_EXPERIMENT_ANCHOR"
            }),
        }
