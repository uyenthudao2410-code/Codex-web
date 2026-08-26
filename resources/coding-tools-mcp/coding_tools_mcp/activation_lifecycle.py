from __future__ import annotations

import os
import secrets
import time
from typing import Any

from .envutils import ENV_PREFIX
from .errors import ToolFailure
from .lifecycle_census import lifecycle_census, open_lifecycle_census_snapshot, read_task_projection


class ActivationLifecycleMixin:
    """Runtime activation admission and immutable lifecycle snapshot helpers."""

    def _initialize_activation_admission(self) -> None:
        """Bind startup activation admission to the supervisor-provided epoch.

        The environment is intentionally read once during Runtime construction.
        A closed startup gate therefore cannot be bypassed by changing the
        process environment after the runtime has started; only the exact
        control action for this epoch can open admission.
        """
        epoch_id = str(os.environ.get(f"{ENV_PREFIX}_ACTIVATION_EPOCH_ID") or "").strip()
        configured_gate = str(os.environ.get(f"{ENV_PREFIX}_ACTIVATION_GATE") or "").strip().lower()
        self.activation_epoch_id = epoch_id or None
        self.activation_gate_config = configured_gate or "open"
        self.activation_admission = "closed" if configured_gate == "closed" else "open"

    def activation_admission_snapshot(self) -> dict[str, Any]:
        """Return the current startup epoch/admission state for operator payloads."""
        with self.activation_lock:
            admission = str(getattr(self, "activation_admission", "open") or "open").lower()
            return {
                "activation_epoch_id": getattr(self, "activation_epoch_id", None),
                "activation_gate": admission,
                "activation_admission": admission,
                "admission": admission,
                "admission_open": admission == "open",
                "configured_gate": str(getattr(self, "activation_gate_config", "open") or "open"),
            }

    def complete_activation_epoch(self, activation_epoch_id: object) -> dict[str, Any]:
        """Open admission only when the supervisor supplies the exact epoch."""
        supplied = str(activation_epoch_id or "").strip()
        with self.activation_lock:
            expected = str(getattr(self, "activation_epoch_id", None) or "")
            if not expected or not supplied or not secrets.compare_digest(supplied, expected):
                raise ToolFailure(
                    "UPDATE_INCOMPLETE",
                    "The activation epoch does not match the startup epoch; runtime admission remains closed.",
                    category="runtime",
                    retryable=False,
                    details={
                        "activation_epoch_id": getattr(self, "activation_epoch_id", None),
                        "admission": str(getattr(self, "activation_admission", "closed") or "closed"),
                    },
                )
            self.activation_admission = "open"
            return {
                "ok": True,
                "action": "complete_epoch",
                **self.activation_admission_snapshot(),
            }

    def close_activation_epoch(self, activation_epoch_id: object) -> dict[str, Any]:
        """Close admission for an epoch while a supervisor rolls back/fails."""
        supplied = str(activation_epoch_id or "").strip()
        with self.activation_lock:
            expected = str(getattr(self, "activation_epoch_id", None) or "")
            if not expected or not supplied or not secrets.compare_digest(supplied, expected):
                raise ToolFailure(
                    "UPDATE_INCOMPLETE",
                    "The activation epoch does not match the startup epoch; runtime admission remains closed.",
                    category="runtime",
                    retryable=False,
                    details={"activation_epoch_id": getattr(self, "activation_epoch_id", None)},
                )
            self.activation_admission = "closed"
            return {"ok": True, "action": "close_epoch", **self.activation_admission_snapshot()}

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
            if str(getattr(self, "activation_admission", "open") or "open").lower() != "open":
                snapshot = self.activation_admission_snapshot()
                raise ToolFailure(
                    "RUNTIME_ACTIVATION_PENDING",
                    "Runtime activation is incomplete; complete the startup activation epoch before calling tools.",
                    category="runtime",
                    retryable=True,
                    details=snapshot,
                )
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
