from __future__ import annotations

import copy
import os
import re
import secrets
import sqlite3
import threading
import time
from typing import Any

from .activation_capability import valid_activation_operation_id
from .acceptance_receipts import _verify_activation_source_checkpoint, _verify_lifecycle_snapshot
from .envutils import ENV_PREFIX
from .endpoint_identity import workspace_binding_id
from .errors import ToolFailure
from .lifecycle_census import lifecycle_census, open_lifecycle_census_snapshot, read_task_projection
from .projection_rebuild import (
    build_projection_rebuild_receipt_from_census,
    validate_projection_rebuild_receipt,
)


READY_COMMIT_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
ACTIVATION_GATE_OPEN = "open"
ACTIVATION_GATE_CLOSED = "closed"
ACTIVATION_GATE_VALUES = frozenset({ACTIVATION_GATE_OPEN, ACTIVATION_GATE_CLOSED})
# A real current-client bootstrap took ~23s to reach READY on the retained
# ledger. Wait inside the read request, not by manufacturing model turns.
# This never extends the startup-bound activation deadline.
ACTIVATION_BOOTSTRAP_WAIT_SECONDS = 25.0
ACTIVATION_BOOTSTRAP_RETRY_AFTER_MS = 5_000


class ActivationLifecycleMixin:
    """Runtime activation admission and immutable lifecycle snapshot helpers."""

    def _activation_paused_self_controller(
        self,
        lifecycle: dict[str, Any],
        live_owned: list[str],
    ) -> dict[str, str]:
        """Return exact self-controller identity only for a quiescent REPLAN.

        The lifecycle classifier remains authoritative and unchanged.  This
        helper merely proves that one LIVE_OWNED row is caused solely by the
        calling ChatWeb controller lease while the task is explicitly paused.
        Any missing, additional, future/unknown, or foreign ownership evidence
        fails closed by returning no allowance.
        """
        try:
            state = self.task_state.get()
            if str(state.get("status") or "").strip().lower() != "paused":
                return {}
            projection = state.get("orchestration") if isinstance(state.get("orchestration"), dict) else {}
            run_id = str(projection.get("run_id") or "").strip()
            if not run_id or run_id not in live_owned:
                return {}
            identity = self._current_hub_client()
            if not isinstance(identity, dict) or str(identity.get("client_type") or "").strip().lower() != "chatweb":
                return {}
            client_id = str(self._hub_client_record_id(identity) or "").strip()
            if not client_id:
                return {}

            lifecycle_counts = lifecycle.get("classification_counts") if isinstance(lifecycle.get("classification_counts"), dict) else {}
            total_live_owned = int(lifecycle_counts.get("LIVE_OWNED") or 0)
            live_records = lifecycle.get("live_owned_runs") if isinstance(lifecycle.get("live_owned_runs"), list) else []
            live_records = [item for item in live_records if isinstance(item, dict)]
            # run_ids_by_class/live_owned_runs are bounded projections.  Never
            # discount from a truncated or internally inconsistent snapshot.
            if total_live_owned != len(live_owned) or total_live_owned != len(live_records):
                return {}
            record = next((item for item in live_records if str(item.get("run_id") or "") == run_id), None)
            if record is None:
                return {}
            if str(record.get("run_status") or "") != "active":
                return {}
            if str(record.get("latest_state_after") or "").upper() != "REPLAN":
                return {}
            ownership = record.get("ownership") if isinstance(record.get("ownership"), dict) else {}
            expected_keys = {
                "active_controller_leases",
                "active_write_fences",
                "running_background_operations",
                "live_agent_lanes",
                "live_managed_jobs",
            }
            if set(ownership) != expected_keys:
                return {}
            observed_ownership = {key: int(ownership.get(key) or 0) for key in expected_keys}
            if observed_ownership != {
                "active_controller_leases": 1,
                "active_write_fences": 0,
                "running_background_operations": 0,
                "live_agent_lanes": 0,
                "live_managed_jobs": 0,
            }:
                return {}
            lease = self.orchestration_ledger.peek_controller_lease(run_id)
            if not isinstance(lease, dict):
                return {}
            if (
                str(lease.get("run_id") or "") != run_id
                or str(lease.get("status") or "") != "active"
                or str(lease.get("owner_client_id") or "") != client_id
            ):
                return {}
            ctx = self.orchestration_control.snapshot(run_id)
            if ctx is None or str(ctx.state or "").upper() != "REPLAN":
                return {}
            if self.orchestration_ledger.verify_chain(run_id).get("ok") is not True:
                return {}
            return {"run_id": run_id, "client_id": client_id}
        except (KeyError, TypeError, ValueError, sqlite3.Error, OSError, RuntimeError, ToolFailure):
            return {}

    def activation_preflight(
        self,
        *,
        operation_id: str = "",
        expires_at_unix_ms: int = 0,
        allow_acceptance_pending: bool = False,
        allow_self_controller_lease: bool = False,
        prepare: bool = False,
        ignore_active_tool_calls: int = 0,
        source_checkpoint: Any = None,
        require_unfenced: bool = False,
    ) -> dict[str, Any]:
        """Return canonical restart safety and optionally fence new tool admission."""
        with self.activation_lock:
            self._activation_cleanup_locked()
            now_ms = int(time.time() * 1000)
            if prepare or require_unfenced:
                if not valid_activation_operation_id(operation_id):
                    raise ToolFailure("INVALID_OPERATION_ID", "Invalid activation operation_id.", category="validation")
            if prepare:
                if expires_at_unix_ms <= now_ms or expires_at_unix_ms > now_ms + 60_000:
                    raise ToolFailure("ACTIVATION_REQUEST_EXPIRED", "Activation expiry must be within the next 60 seconds.", category="validation")
            cleanup = self._activation_executor_cleanup_locked()
            if cleanup and cleanup["state"] != "completed":
                if prepare and cleanup["operation_id"] == operation_id:
                    self.activation_fence = {
                        "operation_id": operation_id,
                        "expires_at_unix_ms": expires_at_unix_ms,
                        "prepared_at_unix_ms": now_ms,
                    }
                return self._activation_executor_cleanup_result_locked(cleanup)
            if self.activation_fence and str(self.activation_fence.get("operation_id") or "") != operation_id:
                return {
                    "safe": False,
                    "code": "RUNTIME_BUSY",
                    "reason": "another_activation_pending",
                    "operation_id": str(self.activation_fence.get("operation_id") or ""),
                }
            if require_unfenced and self.activation_fence:
                return {
                    "safe": False,
                    "code": "RUNTIME_BUSY",
                    "reason": "activation_fence_present",
                    "operation_id": operation_id,
                    "fence_operation_id": str(self.activation_fence.get("operation_id") or ""),
                    "fenced": True,
                }

            with self.sessions_lock:
                active_commands = sum(1 for session in self.sessions.values() if session.process.poll() is None)
                starting_commands = int(self.starting_sessions)
            with self.background_operations_lock:
                active_background = sum(1 for item in self.background_operations.values() if not item["event"].is_set())
            try:
                ledger_background = sum(
                    1 for item in self.orchestration_ledger.list_background_operations(limit=100)
                    if str(item.get("status") or "") == "running"
                )
                managed = self.execution_resource_governor.snapshot(limit=100)
                owned_codex_sidecars = self._activation_owned_codex_sidecar_rows(managed)
                managed_active = max(
                    0,
                    int(managed.get("active_command_count") or 0) - len(owned_codex_sidecars),
                )
                foreign_heavy = self.execution_resource_governor.foreign_heavy_processes()
                active_lanes = len(self.orchestration_ledger.list_agent_lanes(lifecycle="active"))
            except (sqlite3.Error, OSError) as exc:
                return {
                    "safe": False,
                    "code": "ORCHESTRATION_STATE_UNCERTAIN",
                    "reason": "activation_state_probe_failed",
                    "error_type": type(exc).__name__,
                }
            active_tool_calls = max(0, int(self.active_tool_calls) - max(0, int(ignore_active_tool_calls)))
            counts = {
                "active_tool_calls": active_tool_calls,
                "active_commands": active_commands,
                "starting_commands": starting_commands,
                "active_background_operations": max(active_background, ledger_background),
                "active_managed_processes": managed_active,
                "foreign_heavy_processes": len(foreign_heavy),
                "active_agent_lanes": active_lanes,
            }
            if any(counts.values()):
                return {"safe": False, "code": "RUNTIME_BUSY", "reason": "active_runtime_work", "counts": counts}

            try:
                lifecycle = self._activation_lifecycle_summary()
            except (sqlite3.Error, OSError) as exc:
                return {
                    "safe": False,
                    "code": "ORCHESTRATION_STATE_UNCERTAIN",
                    "reason": "activation_state_probe_failed",
                    "error_type": type(exc).__name__,
                    "counts": counts,
                }
            except (RuntimeError, ValueError) as exc:
                return {
                    "safe": False,
                    "code": "ORCHESTRATION_STATE_UNCERTAIN",
                    "reason": "activation_lifecycle_snapshot_failed",
                    "error_type": type(exc).__name__,
                    "counts": counts,
                }
            if not _verify_lifecycle_snapshot(lifecycle):
                return {
                    "safe": False,
                    "code": "ORCHESTRATION_STATE_UNCERTAIN",
                    "reason": "lifecycle_snapshot_integrity_failed",
                    "counts": counts,
                    "lifecycle": lifecycle,
                }
            if self._activation_projection_classification(lifecycle) == "PROJECTION_DRIFT":
                return {"safe": False, "code": "ORCHESTRATION_STATE_UNCERTAIN", "reason": "projection_drift", "counts": counts, "lifecycle": lifecycle}
            lifecycle_counts = lifecycle.get("classification_counts") if isinstance(lifecycle.get("classification_counts"), dict) else {}
            threshold_candidates = int(lifecycle_counts.get("THRESHOLD_SENSITIVE_STALE_CANDIDATE") or 0)
            counts["threshold_sensitive_stale_candidates"] = threshold_candidates
            owned_sidecar_residues, remaining_unbound_residues = (
                self._activation_unbound_residue_counts(lifecycle, owned_codex_sidecars)
            )
            counts["owned_codex_sidecar_residues"] = owned_sidecar_residues
            if int(lifecycle.get("unexplained_active_runs") or 0) or remaining_unbound_residues:
                return {
                    "safe": False,
                    "code": "ORCHESTRATION_STATE_UNCERTAIN",
                    "reason": "lifecycle_unexplained_or_unbound",
                    "counts": counts,
                    "lifecycle": lifecycle,
                }
            run_ids_by_class = lifecycle.get("run_ids_by_class") if isinstance(lifecycle.get("run_ids_by_class"), dict) else {}
            live_owned = list(run_ids_by_class.get("LIVE_OWNED") or [])
            self_controller: dict[str, str] = {}
            counts["self_controller_leases_discounted"] = 0
            if live_owned and allow_self_controller_lease:
                self_controller = self._activation_paused_self_controller(lifecycle, live_owned)
                self_controller_run_id = str(self_controller.get("run_id") or "")
                if self_controller_run_id:
                    live_owned = [run_id for run_id in live_owned if str(run_id) != self_controller_run_id]
                    counts["self_controller_leases_discounted"] = 1
            if live_owned:
                return {
                    "safe": False,
                    "code": "RUNTIME_BUSY",
                    "reason": "lifecycle_live_owned",
                    "run_id": str(live_owned[0]),
                    "counts": counts,
                    "lifecycle": lifecycle,
                }
            awaiting_acceptance = list(run_ids_by_class.get("AWAITING_ACCEPTANCE") or [])
            if awaiting_acceptance and not allow_acceptance_pending:
                return {
                    "safe": False,
                    "code": "ACCEPTANCE_PENDING",
                    "reason": "explicit_acceptance_preservation_required",
                    "run_id": str(awaiting_acceptance[0]),
                    "counts": counts,
                    "lifecycle": lifecycle,
                }
            active_p5 = [item for item in lifecycle.get("p5_lifecycles") or [] if item and item not in {"EPOCH_CLOSED", "EPOCH_HARD_STOPPED"}]
            if active_p5:
                return {
                    "safe": False,
                    "code": "RUNTIME_BUSY",
                    "reason": "p5_epoch_not_terminal",
                    "counts": counts,
                    "lifecycle": lifecycle,
                }
            orchestration_state = "IDLE"
            run_id = ""
            acceptance_pending = bool(awaiting_acceptance)
            active_run = None
            # The classifier is authoritative for threshold-sensitive rows;
            # do not re-open the writer-oriented accessor merely to call them
            # active.  For every other state retain the legacy detailed
            # orchestration guard and acceptance proof.
            if threshold_candidates:
                orchestration_state = "QUIESCENT_WITH_THRESHOLD_CANDIDATES"
                if self_controller:
                    run_id = str(self_controller.get("run_id") or "")
            else:
                try:
                    active_run = self.orchestration_ledger.current_active_execution_run()
                except (sqlite3.Error, OSError) as exc:
                    return {
                        "safe": False,
                        "code": "ORCHESTRATION_STATE_UNCERTAIN",
                        "reason": "activation_state_probe_failed",
                        "error_type": type(exc).__name__,
                        "counts": counts,
                        "lifecycle": lifecycle,
                    }
            if active_run:
                run_id = str(active_run.get("run_id") or "")
                ctx = self.orchestration_control.snapshot(run_id)
                if ctx is None:
                    return {
                        "safe": False,
                        "code": "ORCHESTRATION_STATE_UNCERTAIN",
                        "reason": "active_run_missing_context",
                        "run_id": run_id,
                        "counts": counts,
                    }
                orchestration_state = str(ctx.state or "").upper()
                integrity = self.orchestration_ledger.verify_chain(run_id)
                if not integrity.get("ok", False):
                    return {
                        "safe": False,
                        "code": "ORCHESTRATION_STATE_UNCERTAIN",
                        "reason": "ledger_integrity_failed",
                        "run_id": run_id,
                        "orchestration_state": orchestration_state,
                        "counts": counts,
                    }
                if orchestration_state == "ACCEPTING":
                    acceptance_pending = True
                    if not allow_acceptance_pending:
                        return {
                            "safe": False,
                            "code": "ACCEPTANCE_PENDING",
                            "reason": "explicit_acceptance_preservation_required",
                            "run_id": run_id,
                            "orchestration_state": orchestration_state,
                            "counts": counts,
                        }
                elif self_controller and run_id == str(self_controller.get("run_id") or "") and orchestration_state == "REPLAN":
                    orchestration_state = "QUIESCENT_REPLAN_WITH_SELF_CONTROLLER"
                else:
                    return {
                        "safe": False,
                        "code": "RUNTIME_BUSY",
                        "reason": "orchestration_active",
                        "run_id": run_id,
                        "orchestration_state": orchestration_state,
                        "counts": counts,
                    }

            source_identity = self._orchestration_workspace_identity(str(self.workspace.root)) if source_checkpoint is not None else {}
            checkpoint_verification = None if source_checkpoint is None else _verify_activation_source_checkpoint(
                self.workspace.root, self.orchestration_ledger, source_checkpoint,
                current_git_head=str(source_identity.get("base_head") or ""),
                current_worktree_fp=str(source_identity.get("worktree_fp") or ""), lifecycle=lifecycle,
            )
            if checkpoint_verification is not None and checkpoint_verification.get("ok") is not True:
                return {**checkpoint_verification, "safe": False, "counts": counts, "lifecycle": lifecycle}
            if prepare and owned_codex_sidecars:
                self._codex_bridge.close()
                refreshed_managed = self.execution_resource_governor.snapshot(limit=100)
                remaining_managed = int(refreshed_managed.get("active_command_count") or 0)
                if remaining_managed:
                    failed_counts = dict(counts)
                    failed_counts["active_managed_processes"] = remaining_managed
                    return {
                        "safe": False,
                        "code": "RUNTIME_BUSY",
                        "reason": "internal_service_quiescence_failed",
                        "run_id": run_id,
                        "orchestration_state": orchestration_state,
                        "counts": failed_counts,
                    }

            result = {
                "safe": True,
                "code": "READY",
                "reason": (
                    "paused_replan_self_controller_is_quiescent"
                    if self_controller
                    else "idle" if not acceptance_pending else "acceptance_state_is_durable"
                ),
                "operation_id": operation_id or None,
                "run_id": run_id,
                "orchestration_state": orchestration_state,
                "acceptance_pending": acceptance_pending,
                "counts": counts,
                "process_instance_id": self.process_instance_id,
                "server_instance_id": self.server_instance_id,
                "workspace": str(self.workspace.root),
                "lifecycle": lifecycle,
                "source_checkpoint": checkpoint_verification,
                "fenced": bool(self.activation_fence),
                "fence_operation_id": str(self.activation_fence.get("operation_id") or "") if self.activation_fence else None,
            }
            if prepare:
                self.activation_fence = {
                    "operation_id": operation_id,
                    "expires_at_unix_ms": expires_at_unix_ms,
                    "prepared_at_unix_ms": now_ms,
                }
                result["fenced"] = True
                result["fence_operation_id"] = operation_id
                result["expires_at_unix_ms"] = expires_at_unix_ms
                manager = getattr(self, "_windows_mxc_sandbox_manager", None)
                if manager is not None:
                    cleanup = self._activation_start_executor_cleanup_locked(manager, operation_id, now_ms)
                    return self._activation_executor_cleanup_result_locked(cleanup)
            if cleanup:
                result["executor_cleanup"] = self._activation_executor_cleanup_public(cleanup)
            elif prepare:
                result["executor_cleanup"] = {"state": "not_required", "confirmed": True}
            return result

    def cancel_activation(self, operation_id: str) -> bool:
        with self.activation_lock:
            self._activation_cleanup_locked()
            cleanup = self._activation_executor_cleanup_locked()
            if cleanup and cleanup["state"] != "completed":
                if cleanup["operation_id"] != str(operation_id or ""):
                    raise ToolFailure("ACTIVATION_OPERATION_MISMATCH", "Executor cleanup belongs to another operation.", category="validation")
                self._activation_require_executor_available_locked()
            if not self.activation_fence:
                return False
            if str(self.activation_fence.get("operation_id") or "") != str(operation_id or ""):
                raise ToolFailure("ACTIVATION_OPERATION_MISMATCH", "Activation fence belongs to another operation.", category="validation")
            self.activation_fence = None
            return True

    @staticmethod
    def _activation_executor_cleanup_public(cleanup: dict[str, Any]) -> dict[str, Any]:
        return {
            "state": cleanup["state"],
            "started_at_unix_ms": cleanup["started_at_unix_ms"],
            "deadline_at_unix_ms": cleanup["deadline_at_unix_ms"],
            "retry_after_ms": 1000 if cleanup["state"] == "pending" else 0,
            "confirmed": cleanup["state"] == "completed",
        }

    def _activation_executor_cleanup_locked(self) -> dict[str, Any] | None:
        cleanup = getattr(self, "_activation_executor_cleanup", None)
        if cleanup and cleanup["state"] == "pending" and time.monotonic() >= cleanup["deadline_monotonic"]:
            # Do not reopen admission while a late cleanup thread still owns
            # the manager. Deadline expiry is terminal uncertainty, not success.
            cleanup["state"] = "failed"
        return cleanup

    def _activation_executor_cleanup_result_locked(self, cleanup: dict[str, Any]) -> dict[str, Any]:
        pending = cleanup["state"] == "pending"
        fence = self.activation_fence or {}
        return {
            "safe": False,
            "code": "SANDBOX_CLEANUP_PENDING" if pending else "SANDBOX_TEARDOWN_UNCONFIRMED",
            "reason": "owned_sandbox_cleanup_pending" if pending else "owned_sandbox_cleanup_unconfirmed",
            "operation_id": cleanup["operation_id"],
            "workspace": str(self.workspace.root),
            "process_instance_id": self.process_instance_id,
            "server_instance_id": self.server_instance_id,
            "fenced": bool(fence),
            "fence_operation_id": fence.get("operation_id"),
            "expires_at_unix_ms": fence.get("expires_at_unix_ms"),
            "executor_cleanup": self._activation_executor_cleanup_public(cleanup),
        }

    def _activation_require_executor_available_locked(self) -> None:
        cleanup = self._activation_executor_cleanup_locked()
        if cleanup and cleanup["state"] != "completed":
            result = self._activation_executor_cleanup_result_locked(cleanup)
            raise ToolFailure(
                result["code"],
                "Owned executor cleanup must finish before runtime work or replacement can continue.",
                category="runtime", retryable=cleanup["state"] == "pending", details=result,
            )

    def _activation_start_executor_cleanup_locked(
        self, manager: Any, operation_id: str, now_ms: int,
    ) -> dict[str, Any]:
        # Existing quiescence checks and the admission fence were committed
        # under activation_lock. The close thread never holds that lock during
        # the bounded backend phase, so health, cancel and prepare stay readable.
        timeout_seconds = float(manager.close_timeout_seconds) + 5.0
        cleanup = {
            "state": "pending", "operation_id": operation_id,
            "started_at_unix_ms": now_ms,
            "deadline_at_unix_ms": now_ms + int(timeout_seconds * 1000),
            "deadline_monotonic": time.monotonic() + timeout_seconds,
        }
        self._activation_executor_cleanup = cleanup

        def close_owned_executor() -> None:
            try:
                confirmed = manager.close() is True
            except Exception:  # noqa: BLE001 - teardown failure must keep admission closed
                confirmed = False
            with self.activation_lock:
                if self._activation_executor_cleanup is not cleanup:
                    return
                current = self._activation_executor_cleanup_locked()
                if current is cleanup and cleanup["state"] == "pending":
                    if confirmed and getattr(self, "_windows_mxc_sandbox_manager", None) is manager:
                        self._windows_mxc_sandbox_manager = None
                        cleanup["state"] = "completed"
                    else:
                        cleanup["state"] = "failed"

        try:
            threading.Thread(target=close_owned_executor, name="activation-executor-cleanup", daemon=True).start()
        except RuntimeError:
            cleanup["state"] = "failed"
        return cleanup

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
        if configured_gate and configured_gate not in ACTIVATION_GATE_VALUES:
            raise ToolFailure(
                "ACTIVATION_GATE_INVALID",
                "Coding MCP activation gate must be either 'open' or 'closed'.",
                category="validation",
                retryable=False,
                details={
                    "activation_epoch_id": epoch_id or None,
                    "activation_gate": configured_gate,
                    "supported": sorted(ACTIVATION_GATE_VALUES),
                },
            )
        if epoch_id and configured_gate == ACTIVATION_GATE_OPEN:
            raise ToolFailure(
                "ACTIVATION_GATE_INVALID",
                "Epoch-bound Coding MCP processes must start with admission closed.",
                category="validation",
                retryable=False,
                details={
                    "activation_epoch_id": epoch_id,
                    "activation_gate": configured_gate,
                    "required_gate": ACTIVATION_GATE_CLOSED,
                },
            )
        normalized_gate = (
            ACTIVATION_GATE_CLOSED
            if epoch_id
            else (configured_gate or ACTIVATION_GATE_OPEN)
        )
        self.activation_epoch_id = epoch_id or None
        self.activation_gate_config = normalized_gate
        self.activation_admission = normalized_gate
        # This is startup-bound authority from the exact Recovery Host epoch,
        # not a caller-controlled GET parameter. It preserves durable
        # AWAITING_ACCEPTANCE rows during a process refresh while the ordinary
        # live-work, ownership and ledger-integrity gates remain fail-closed.
        self.activation_allow_acceptance_pending = bool(
            epoch_id and normalized_gate == ACTIVATION_GATE_CLOSED and allow_acceptance_pending == "true"
        )
        self.activation_expires_at_unix_ms = expires_at_unix_ms if expires_at_unix_ms > 0 else None
        self.activation_ready_commit_digest: str | None = None
        self.activation_completion_closed = False
        self._activation_admission_changed = threading.Event()
        self._activation_bootstrap_wait_slots = threading.BoundedSemaphore(4)

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
            cleanup = self._activation_executor_cleanup_locked()
            if cleanup and cleanup["state"] != "completed":
                admission = "closed"
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
                "executor_cleanup": self._activation_executor_cleanup_public(cleanup) if cleanup else None,
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
            "executor_cleanup_supported": True,
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
            def ensure_not_expired() -> None:
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

            ensure_not_expired()
            if current_digest and not secrets.compare_digest(current_digest, supplied_digest):
                raise ToolFailure(
                    "UPDATE_INCOMPLETE",
                    "Runtime activation commit digest changed while admission was closed.",
                    category="runtime",
                    retryable=False,
                )
            projection_rebuild = self.projection_rebuild_snapshot()
            validation = projection_rebuild.get("validation")
            if (
                projection_rebuild.get("current") is not True
                and isinstance(validation, dict)
                and validation.get("valid") is False
                and validation.get("code") == "UPDATE_INCOMPLETE"
                and validation.get("reasons") == ["RECEIPT_STALE"]
            ):
                self._projection_rebuild_census()
                ensure_not_expired()
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
            self._activation_admission_changed.set()
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
            self._activation_admission_changed.set()
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

    def activation_connector_bootstrap_allowed(self, name: str) -> bool:
        """Allow one no-workspace compatibility handshake while admission is closed.

        A cached ChatWeb connector can legitimately know the additive
        ``workspace_context`` schema without issuing a fresh ``tools/list``
        after process replacement.  Ordinary tool execution must remain
        blocked, but returning only a bootstrap receipt gives Recovery Host an
        exact current-process/current-contract contact.  Recovery Host owns
        the separate predecessor review for changed contracts, so this receipt
        must also be available for a same-SHA activation when the predecessor
        list is empty.  No workspace lookup, ledger access, or tool dispatch
        occurs on this path.
        """
        with self.activation_lock:
            return bool(
                str(name or "").strip() == "workspace_context"
                and str(getattr(self, "activation_admission", "open") or "open").lower() != "open"
                and str(getattr(self, "activation_gate_config", "open") or "open").lower() == "closed"
                and str(getattr(self, "activation_epoch_id", None) or "").strip()
                and not bool(getattr(self, "activation_completion_closed", False))
            )

    def _workspace_binding_metadata(self) -> dict[str, Any]:
        """Return content-free binding metadata for the active workspace.

        Safe to expose while admission is closed: only the opaque binding
        digest, the generation, the bare workspace name, and a drive
        existence flag. No file listing, Git access, or source reads occur.
        """

        root = getattr(getattr(self, "workspace", None), "root", None)
        try:
            root_text = str(root) if root is not None else ""
        except Exception:
            root_text = ""
        try:
            available = bool(root_text) and os.path.isdir(root_text)
        except Exception:
            available = False
        try:
            generation = int(getattr(self, "workspace_generation", 0) or 0)
        except (TypeError, ValueError):
            generation = 0
        try:
            name = (root.name if hasattr(root, "name") else "") or ""
        except Exception:
            name = ""
        device_instance_id = str(
            os.environ.get(f"{ENV_PREFIX}_DEVICE_INSTANCE_ID", "") or ""
        ).strip()
        binding = None
        if root_text:
            try:
                binding = workspace_binding_id(
                    device_instance_id=device_instance_id,
                    workspace_root=root,
                    generation=generation,
                )
            except Exception:
                binding = None
        return {
            "workspace_binding_id": binding,
            "workspace_generation": generation,
            "workspace_name": str(name or "")[:80] or None,
            "available": available,
        }

    def _require_active_workspace_binding_available(self) -> dict[str, Any]:
        """Raise WORKSPACE_UNAVAILABLE when the bound drive is gone.

        Callers that rely on the active workspace binding (no explicit path)
        must fail here instead of falling back to another directory.
        """
        binding = self._workspace_binding_metadata()
        if binding.get("available") is not True:
            raise ToolFailure(
                "WORKSPACE_UNAVAILABLE",
                "The active workspace is unavailable. Reselect the workspace before retrying; no fallback directory will be used.",
                category="runtime",
                retryable=False,
                details={"workspace_binding": binding},
            )
        return binding

    def activation_connector_bootstrap_result(self, name: str) -> dict[str, Any] | None:
        with self.activation_lock:
            if str(name or "").strip() != "workspace_context":
                return None
            # Rollback is terminal, not an invitation to keep retrying the
            # same process. Keep this result workspace-free even after a
            # waiter is awakened by shutdown or an exact control rollback.
            if self._closed or self.activation_completion_closed:
                code = "RUNTIME_STOPPING" if self._closed else "ACTIVATION_ROLLED_BACK"
                return {
                    "ok": False, "completed": False, "retryable": False,
                    "workspace_accessed": False,
                    "activation": self.activation_admission_snapshot(),
                    "error": {
                        "code": code,
                        "message": "This runtime cannot complete activation. Use supported Recovery Host recovery; do not repeat this handshake unchanged.",
                        "category": "runtime", "retryable": False,
                    },
                }
            if not self.activation_connector_bootstrap_allowed(name):
                return None
            epoch_id = str(getattr(self, "activation_epoch_id", None) or "")
            expires_at = int(getattr(self, "activation_expires_at_unix_ms", 0) or 0)
            if expires_at > 0 and int(time.time() * 1000) >= expires_at:
                # An expired startup boundary cannot be completed in this process.
                # Keep this early result workspace-free, but never request a retry.
                return {
                    "ok": False,
                    "completed": False,
                    "retryable": False,
                    "workspace_accessed": False,
                    "activation": self.activation_admission_snapshot(),
                    "workspace_binding": self._workspace_binding_metadata(),
                    "error": {
                        "code": "ACTIVATION_REQUEST_EXPIRED",
                        "message": (
                            "The startup-bound activation epoch expired. "
                            "Use supported Recovery Host recovery before retrying."
                        ),
                        "category": "runtime",
                        "retryable": False,
                        "details": {
                            "activation_epoch_id": epoch_id,
                            "expires_at_unix_ms": expires_at,
                        },
                    },
                }
            identity = self._current_hub_client() or {}
            binding_verified = bool(
                str(identity.get("client_type") or "").strip() == "chatweb"
                and str(identity.get("identity_source") or "").strip() == "attested_transport"
                and identity.get("attestation_verified") is True
            )
            if not binding_verified:
                # Compatibility bootstrap is connector authority, not generic
                # liveness. An unattested caller can receive a workspace-free
                # diagnosis, but it must never be told that an authoritative
                # bootstrap was accepted when no durable receipt can be made.
                return {
                    "ok": False,
                    "completed": False,
                    "retryable": False,
                    "workspace_accessed": False,
                    "activation": self.activation_admission_snapshot(),
                    "error": {
                        "code": "CONNECTOR_ACTIVATION_BINDING_UNVERIFIED",
                        "message": (
                            "The connector compatibility bootstrap did not arrive through the "
                            "current managed ChatWeb tunnel attestation. Reattach or refresh the "
                            "managed connector before retrying."
                        ),
                        "category": "runtime",
                        "retryable": False,
                        "details": {
                            "activation_epoch_id": epoch_id,
                            "identity_source": str(identity.get("identity_source") or "unavailable"),
                            "attestation_verified": identity.get("attestation_verified") is True,
                            "attestation_source": str(identity.get("attestation_source") or "unavailable"),
                        },
                    },
                }
            return {
                "ok": True,
                "status": "activation_pending",
                "completed": False,
                "retryable": True,
                "retry_after_ms": min(ACTIVATION_BOOTSTRAP_RETRY_AFTER_MS, max(1, expires_at - int(time.time() * 1000))) if expires_at > 0 else ACTIVATION_BOOTSTRAP_RETRY_AFTER_MS,
                "workspace_accessed": False,
                "activation": self.activation_admission_snapshot(),
                "observed_at_unix_ms": int(time.time() * 1000),
                "workspace_binding": self._workspace_binding_metadata(),
                "activation_bootstrap": {
                    "schema_version": 1,
                    "kind": "connector_compatibility_bootstrap",
                    "accepted": True,
                    "retry_required": True,
                    "activation_epoch_id": epoch_id,
                    "process_instance_id": self.process_instance_id,
                    "server_instance_id": self.server_instance_id,
                },
            }

    def activation_connector_bootstrap_for_call(self, name: str) -> dict[str, Any] | None:
        """Publish real contact before a bounded, workspace-free admission wait.

        Waiting before publishing would deadlock the coordinator: its final
        census needs this exact receipt. No active tool/workspace lease or
        activation lock is held while waiting; only the owning Recovery Host
        can open admission through the existing commit control action.
        """
        pending = self.activation_connector_bootstrap_result(name)
        bootstrap = pending.get("activation_bootstrap") if isinstance(pending, dict) else None
        if not isinstance(bootstrap, dict) or bootstrap.get("accepted") is not True:
            return pending
        self._record_activation_bootstrap_rpc_contact(
            {"method": "tools/call", "params": {"name": name}},
            {"result": {"structuredContent": pending}},
            self._current_hub_client() or {},
        )
        # A bound on waiters protects HTTP capacity during reconnect bursts.
        # Excess callers receive the same honest pending/retry contract.
        if not self._activation_bootstrap_wait_slots.acquire(blocking=False):
            return pending
        try:
            budget = max(0.0, ACTIVATION_BOOTSTRAP_WAIT_SECONDS)
            expires_at = int(getattr(self, "activation_expires_at_unix_ms", 0) or 0)
            if expires_at > 0:
                budget = min(budget, max(0.0, expires_at / 1000 - time.time()))
            deadline = time.monotonic() + budget
            while budget > 0 and not self._closed:
                if self._activation_admission_changed.wait(min(budget, 0.25)):
                    break
                budget = max(0.0, deadline - time.monotonic())
            # Re-read, never replay the pending snapshot after admission has
            # opened. Returning None continues the SAME read call/context
            # through ordinary workspace validation and the admission guard.
            return self.activation_connector_bootstrap_result(name)
        finally:
            self._activation_bootstrap_wait_slots.release()

    def _activation_enter_tool_call(self, name: str = "", args: dict[str, Any] | None = None) -> None:
        with self.activation_lock:
            self._activation_require_executor_available_locked()
            restart_runtime = bool(
                name == "task_control"
                and str((args or {}).get("action") or "").strip().lower() == "restart_runtime"
                and (args or {}).get("confirm_restart") is True
            )
            if (
                str(getattr(self, "activation_admission", "open") or "open").lower() != "open"
                and not restart_runtime
            ):
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
                if restart_runtime:
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
        live_owned_runs: list[dict[str, Any]] = []
        for item in census.get("runs", []):
            if not isinstance(item, dict):
                continue
            classification = str(item.get("classification") or "")
            run_id = str(item.get("run_id") or "")
            if classification and run_id:
                run_ids_by_class.setdefault(classification, []).append(run_id)
            if classification == "LIVE_OWNED" and run_id:
                ownership = item.get("ownership") if isinstance(item.get("ownership"), dict) else {}
                live_owned_runs.append({
                    "run_id": run_id,
                    "run_status": str(item.get("run_status") or ""),
                    "latest_state_after": str(item.get("latest_state_after") or ""),
                    "ownership": {
                        key: int(ownership.get(key) or 0)
                        for key in (
                            "active_controller_leases",
                            "active_write_fences",
                            "running_background_operations",
                            "live_agent_lanes",
                            "live_managed_jobs",
                        )
                    },
                })
        projection = census.get("projection") if isinstance(census.get("projection"), dict) else {}
        rebuild = self.projection_rebuild_snapshot()
        return {
            "snapshot": dict(census.get("snapshot") or {}),
            "classification_counts": dict((census.get("summary") or {}).get("run_classification_counts") or {}),
            "run_ids_by_class": {key: sorted(values)[:20] for key, values in sorted(run_ids_by_class.items())},
            "live_owned_runs": sorted(live_owned_runs, key=lambda item: str(item.get("run_id") or ""))[:20],
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
