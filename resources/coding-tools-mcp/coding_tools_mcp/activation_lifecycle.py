from __future__ import annotations

import copy
import os
import re
import secrets
import time
from typing import Any

from .envutils import ENV_PREFIX
from .errors import ToolFailure
from .lifecycle_census import lifecycle_census, open_lifecycle_census_snapshot, read_task_projection
from .projection_rebuild import (
    build_projection_rebuild_receipt_from_census,
    validate_projection_rebuild_receipt,
)


READY_COMMIT_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")


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
        allow_acceptance_pending = str(
            os.environ.get(f"{ENV_PREFIX}_ACTIVATION_ALLOW_ACCEPTANCE_PENDING") or ""
        ).strip().lower()
        raw_expiry = str(os.environ.get(f"{ENV_PREFIX}_ACTIVATION_EXPIRES_AT_UNIX_MS") or "").strip()
        try:
            expires_at_unix_ms = int(raw_expiry) if raw_expiry else 0
        except ValueError:
            expires_at_unix_ms = 0
        self.activation_epoch_id = epoch_id or None
        self.activation_gate_config = configured_gate or "open"
        self.activation_admission = "closed" if configured_gate == "closed" else "open"
        # This is startup-bound authority from the exact Recovery Host epoch,
        # not a caller-controlled GET parameter. It preserves durable
        # AWAITING_ACCEPTANCE rows during a process refresh while the ordinary
        # live-work, ownership and ledger-integrity gates remain fail-closed.
        self.activation_allow_acceptance_pending = bool(
            epoch_id and configured_gate == "closed" and allow_acceptance_pending == "true"
        )
        self.activation_expires_at_unix_ms = expires_at_unix_ms if expires_at_unix_ms > 0 else None
        self.activation_ready_commit_digest: str | None = None
        self.activation_completion_closed = False

    def _initialize_projection_rebuild(self) -> None:
        self._projection_rebuild_started_at_unix_ms = int(time.time() * 1000)
        self._projection_rebuild_receipt: dict[str, Any] | None = None
        self._projection_rebuild_failure: dict[str, Any] = {
            "valid": False,
            "code": "UPDATE_INCOMPLETE",
            "reasons": ["RECEIPT_MISSING"],
        }

    def _record_projection_rebuild_receipt(self, census: dict[str, Any], *, reconciled: bool) -> None:
        epoch_id = str(getattr(self, "activation_epoch_id", None) or "").strip()
        if not epoch_id:
            self._projection_rebuild_receipt = None
            self._projection_rebuild_failure = {
                "valid": False,
                "code": "UPDATE_INCOMPLETE",
                "reasons": ["ACTIVATION_EPOCH_ID_MISSING", "RECEIPT_MISSING"],
            }
            return
        try:
            receipt = build_projection_rebuild_receipt_from_census(
                census,
                activation_epoch_id=epoch_id,
                process_instance_id=self.process_instance_id,
                server_instance_id=self.server_instance_id,
                workspace=self.workspace.root,
                reconciled=bool(reconciled),
            )
        except (TypeError, ValueError) as exc:
            self._projection_rebuild_receipt = None
            self._projection_rebuild_failure = {
                "valid": False,
                "code": "UPDATE_INCOMPLETE",
                "reasons": ["PROJECTION_REBUILD_FAILED"],
                "error_type": type(exc).__name__,
            }
            return
        snapshot = census.get("snapshot") if isinstance(census.get("snapshot"), dict) else None
        validation = validate_projection_rebuild_receipt(
            receipt,
            activation_epoch_id=epoch_id,
            process_instance_id=self.process_instance_id,
            server_instance_id=self.server_instance_id,
            workspace=self.workspace.root,
            ledger_snapshot=snapshot,
            process_started_at_unix_ms=self._projection_rebuild_started_at_unix_ms,
        )
        self._projection_rebuild_receipt = receipt if validation.get("valid") is True else None
        self._projection_rebuild_failure = validation

    def projection_rebuild_snapshot(self) -> dict[str, Any]:
        receipt = copy.deepcopy(getattr(self, "_projection_rebuild_receipt", None))
        if receipt is None:
            validation = copy.deepcopy(getattr(self, "_projection_rebuild_failure", {}))
            if not validation:
                validation = {"valid": False, "code": "UPDATE_INCOMPLETE", "reasons": ["RECEIPT_MISSING"]}
        else:
            validation = validate_projection_rebuild_receipt(
                receipt,
                activation_epoch_id=getattr(self, "activation_epoch_id", None),
                process_instance_id=self.process_instance_id,
                server_instance_id=self.server_instance_id,
                workspace=self.workspace.root,
                process_started_at_unix_ms=self._projection_rebuild_started_at_unix_ms,
            )
        return {
            "current": validation.get("valid") is True,
            "receipt": receipt,
            "validation": validation,
        }

    def _projection_rebuild_census(self, *, reconciliation_already_performed: bool = False) -> dict[str, Any]:
        if not reconciliation_already_performed:
            self._reconcile_task_orchestration_projection()
        projection = read_task_projection(self.workspace.root)
        if projection.get("available") is not True:
            # Missing/corrupt task-state is not evidence of an empty projection.
            # Materialize the normalized runtime view only when no canonical
            # run remains active, then independently re-read it through the
            # content-free census reader.  This mutates only the rebuildable
            # projection, never the canonical ledger.
            try:
                if not self.orchestration_ledger.list_runs(limit=1, status="active"):
                    state = self.task_state.get()
                    current = state.get("orchestration") if isinstance(state.get("orchestration"), dict) else {}
                    self.task_state.update(
                        {"orchestration": dict(current)},
                        event="orchestration_projection_materialized",
                    )
            except (OSError, RuntimeError, TypeError, ValueError):
                pass
            projection = read_task_projection(self.workspace.root)
        observed_at = time.time()
        with open_lifecycle_census_snapshot(self.workspace.root) as snapshot:
            census = lifecycle_census(
                snapshot,
                workspace=self.workspace.root,
                observed_at=observed_at,
                grace_seconds=15 * 60,
                stale_after_seconds=self.stale_run_seconds,
                projection=projection,
            )
        self._record_projection_rebuild_receipt(census, reconciled=projection.get("available") is True)
        return census

    def activation_admission_snapshot(self, *, blocking: bool = True) -> dict[str, Any]:
        """Return the startup epoch/admission projection without making health hang.

        Canonical activation preflight deliberately holds ``activation_lock``
        while it captures the immutable ledger census and fences new work. That
        census can take several seconds on a real retained ledger. The health
        endpoint must remain independently observable during that interval, so
        its non-blocking caller receives an explicitly CLOSED/busy projection
        instead of waiting on the census and being misclassified as a dead MCP.
        Mutating and commit paths retain the ordinary blocking snapshot.
        """
        acquired = self.activation_lock.acquire(blocking=blocking)
        if not acquired:
            return {
                "activation_epoch_id": getattr(self, "activation_epoch_id", None),
                "activation_gate": "closed",
                "activation_admission": "closed",
                "admission": "closed",
                "admission_open": False,
                "configured_gate": str(getattr(self, "activation_gate_config", "open") or "open"),
                "ready_commit_digest": None,
                "expires_at_unix_ms": getattr(self, "activation_expires_at_unix_ms", None),
                "completion_closed": True,
                "snapshot_busy": True,
            }
        try:
            admission = str(getattr(self, "activation_admission", "open") or "open").lower()
            expires_at_unix_ms = getattr(self, "activation_expires_at_unix_ms", None)
            return {
                "activation_epoch_id": getattr(self, "activation_epoch_id", None),
                "activation_gate": admission,
                "activation_admission": admission,
                "admission": admission,
                "admission_open": admission == "open",
                "configured_gate": str(getattr(self, "activation_gate_config", "open") or "open"),
                "ready_commit_digest": getattr(self, "activation_ready_commit_digest", None),
                "expires_at_unix_ms": expires_at_unix_ms,
                "completion_closed": bool(getattr(self, "activation_completion_closed", False)),
                "snapshot_busy": False,
            }
        finally:
            self.activation_lock.release()

    def activation_preflight_snapshot(
        self,
        *,
        operation_id: str = "",
        ignore_active_tool_calls: int = 0,
    ) -> dict[str, Any]:
        return {
            **self.activation_preflight(
                operation_id=operation_id,
                ignore_active_tool_calls=ignore_active_tool_calls,
                allow_acceptance_pending=bool(
                    getattr(self, "activation_allow_acceptance_pending", False)
                ),
            ),
            **self.activation_admission_snapshot(),
            "workspace": str(self.workspace.root),
        }

    def complete_activation_epoch(
        self,
        activation_epoch_id: object,
        ready_commit_digest: object,
        expires_at_unix_ms: object,
    ) -> dict[str, Any]:
        """Open admission only for the exact durable epoch commit before expiry."""
        supplied = str(activation_epoch_id or "").strip()
        supplied_digest = str(ready_commit_digest or "").strip()
        try:
            supplied_expiry = int(expires_at_unix_ms or 0)
        except (TypeError, ValueError):
            supplied_expiry = 0
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
            if not READY_COMMIT_DIGEST_RE.fullmatch(supplied_digest):
                raise ToolFailure(
                    "ACTIVATION_EPOCH_READY_COMMIT_DIGEST_INVALID",
                    "Runtime admission requires a canonical lowercase ready commit digest.",
                    category="validation",
                    retryable=False,
                )
            expected_expiry = int(getattr(self, "activation_expires_at_unix_ms", 0) or 0)
            if expected_expiry <= 0 or supplied_expiry != expected_expiry:
                raise ToolFailure(
                    "UPDATE_INCOMPLETE",
                    "The activation expiry does not match the startup-bound epoch; admission remains closed.",
                    category="runtime",
                    retryable=False,
                    details={
                        "activation_epoch_id": expected or None,
                        "expires_at_unix_ms": expected_expiry or None,
                        "supplied_expires_at_unix_ms": supplied_expiry or None,
                    },
                )
            current_digest = str(getattr(self, "activation_ready_commit_digest", None) or "")
            admission = str(getattr(self, "activation_admission", "closed") or "closed").lower()
            if admission == "open":
                if current_digest and secrets.compare_digest(current_digest, supplied_digest):
                    return {"ok": True, "action": "complete_epoch", **self.activation_admission_snapshot()}
                raise ToolFailure(
                    "UPDATE_INCOMPLETE",
                    "Runtime admission is already open for another activation commit.",
                    category="runtime",
                    retryable=False,
                    details=self.activation_admission_snapshot(),
                )
            if bool(getattr(self, "activation_completion_closed", False)):
                raise ToolFailure(
                    "UPDATE_INCOMPLETE",
                    "Runtime activation was rolled back and cannot be reopened in this process.",
                    category="runtime",
                    retryable=False,
                    details=self.activation_admission_snapshot(),
                )
            if int(time.time() * 1000) >= expected_expiry:
                raise ToolFailure(
                    "ACTIVATION_REQUEST_EXPIRED",
                    "The startup-bound activation epoch expired before admission opened.",
                    category="runtime",
                    retryable=False,
                    details={
                        "activation_epoch_id": expected or None,
                        "expires_at_unix_ms": expected_expiry,
                    },
                )
            if current_digest and not secrets.compare_digest(current_digest, supplied_digest):
                raise ToolFailure(
                    "UPDATE_INCOMPLETE",
                    "Runtime activation commit digest changed while admission was closed.",
                    category="runtime",
                    retryable=False,
                )
            projection_rebuild = self.projection_rebuild_snapshot()
            if projection_rebuild.get("current") is not True:
                raise ToolFailure(
                    "UPDATE_INCOMPLETE",
                    "Runtime projection rebuild receipt is missing, stale, or belongs to another activation identity.",
                    category="runtime",
                    retryable=False,
                    details=projection_rebuild.get("validation") or {},
                )
            self.activation_ready_commit_digest = supplied_digest
            self.activation_admission = "open"
            return {
                "ok": True,
                "action": "complete_epoch",
                **self.activation_admission_snapshot(),
            }

    def close_activation_epoch(self, activation_epoch_id: object, ready_commit_digest: object = "") -> dict[str, Any]:
        """Close admission for an epoch while a supervisor rolls back/fails."""
        supplied = str(activation_epoch_id or "").strip()
        supplied_digest = str(ready_commit_digest or "").strip()
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
            current_digest = str(getattr(self, "activation_ready_commit_digest", None) or "")
            if current_digest:
                if not READY_COMMIT_DIGEST_RE.fullmatch(supplied_digest) or not secrets.compare_digest(
                    supplied_digest, current_digest
                ):
                    raise ToolFailure(
                        "UPDATE_INCOMPLETE",
                        "The rollback digest does not match the admitted activation commit.",
                        category="runtime",
                        retryable=False,
                        details=self.activation_admission_snapshot(),
                    )
            self.activation_admission = "closed"
            self.activation_completion_closed = True
            return {"ok": True, "action": "close_epoch", **self.activation_admission_snapshot()}

    def activation_epoch_control(
        self,
        action: str,
        activation_epoch_id: object,
        ready_commit_digest: object = "",
        expires_at_unix_ms: object = 0,
    ) -> dict[str, Any]:
        if action == "complete_epoch":
            return self.complete_activation_epoch(
                activation_epoch_id,
                ready_commit_digest,
                expires_at_unix_ms,
            )
        if action == "close_epoch":
            return self.close_activation_epoch(activation_epoch_id, ready_commit_digest)
        raise ToolFailure(
            "INVALID_ARGUMENT",
            "Unsupported activation epoch control action.",
            category="validation",
        )

    def _activation_orchestration_result(self, result: dict[str, Any] | None) -> dict[str, Any] | None:
        if not isinstance(result, dict):
            return result
        result["activation"] = self.activation_admission_snapshot()
        runtime_payload = result.get("runtime")
        if isinstance(runtime_payload, dict):
            runtime_payload.update(self.activation_admission_snapshot())
        else:
            result["runtime"] = self.activation_admission_snapshot()
        return result

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

    @staticmethod
    def _activation_unbound_residue_counts(
        lifecycle: dict[str, Any],
        owned_codex_sidecars: list[dict[str, Any]],
    ) -> tuple[int, int]:
        """Discount only the activation-owned unbound Codex sidecar residue."""
        unbound_count = int(lifecycle.get("unbound_live_resource_residues") or 0)
        unbound_resources = lifecycle.get("unbound_live_resources")
        sidecar_job_ids = {
            str(row.get("job_id") or "") for row in owned_codex_sidecars
            if str(row.get("job_id") or "")
        }
        owned_sidecar_residues = 0
        if isinstance(unbound_resources, list) and len(unbound_resources) == unbound_count:
            owned_sidecar_residues = len({
                str(row.get("resource_id") or "") for row in unbound_resources
                if isinstance(row, dict)
                and str(row.get("resource_type") or "") == "managed_process_job"
                and str(row.get("resource_id") or "") in sidecar_job_ids
                and not str(row.get("run_id") or "")
            })
        return owned_sidecar_residues, unbound_count - owned_sidecar_residues

    def _activation_cleanup_locked(self) -> None:
        fence = self.activation_fence
        if fence and int(fence.get("expires_at_unix_ms") or 0) <= int(time.time() * 1000):
            self.activation_fence = None

    @staticmethod
    def _activation_projection_classification(lifecycle: dict[str, Any]) -> str:
        projection = lifecycle.get("projection") if isinstance(lifecycle.get("projection"), dict) else {}
        return str(lifecycle.get("projection_classification") or projection.get("classification") or "")

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
        census = self._projection_rebuild_census()
        run_ids_by_class: dict[str, list[str]] = {}
        for item in census.get("runs", []):
            if not isinstance(item, dict):
                continue
            classification = str(item.get("classification") or "")
            run_id = str(item.get("run_id") or "")
            if classification and run_id:
                run_ids_by_class.setdefault(classification, []).append(run_id)
        projection = census.get("projection") if isinstance(census.get("projection"), dict) else {}
        rebuild = self.projection_rebuild_snapshot()
        return {
            "snapshot": dict(census.get("snapshot") or {}),
            "classification_counts": dict((census.get("summary") or {}).get("run_classification_counts") or {}),
            "run_ids_by_class": {key: sorted(values)[:20] for key, values in sorted(run_ids_by_class.items())},
            "projection": dict(projection),
            "projection_classification": str(projection.get("classification") or ""),
            "projection_rebuild": rebuild,
            "projection_rebuild_receipt": copy.deepcopy(rebuild.get("receipt")),
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
