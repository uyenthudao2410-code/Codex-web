from __future__ import annotations

"""MCP-owned execution of one already-authorized RUN continuation proposal.

The App Server model is deliberately only a no-tools proposal generator. This
module retains all mutable authority in the existing MCP/EOCL primitives:
RUN/WAVE state, write lease, exact patch application, structured proof command,
and the final ``ACCEPTING`` transition. It never creates a second scheduler or
accepts a business outcome on behalf of ChatWeb/Sol.
"""

import base64
import hashlib
import json
import os
import platform
import re
import tempfile
import threading
import time
import zlib
from pathlib import Path
from typing import Any, Iterable

from .errors import ToolFailure
from .orchestration_control import OrchestrationControlError, RunContext
from .problem_lineage import ProblemLineageError
from .run_continuation import (
    GOAL_CONTINUATION_NO_PROGRESS,
    RUN_CONTINUATION_PROFILE,
    RunContinuationError,
    _canonical_json,
    _normalize_effect_artifact_path,
    _normalize_path,
    _now_ms,
    parse_run_continuation_proposal,
)
from .solution_economics import record_patch_surface
from .task_state import command_payload_succeeded


CONTINUATION_DRIVER_POLL_MS = 5_000
CONTINUATION_DRIVER_MAX_OUTPUT_BYTES = 131_072
CONTINUATION_ENVIRONMENT_SCHEMA_VERSION = 1
_SENSITIVE_FAILURE_OUTPUT_RE = re.compile(r"(authorization|credential|password|passwd|secret|token|api[_-]?key|private[_-]?key)", re.I)


def continuation_execution_environment_hash() -> str:
    """Hash the non-secret execution identity that an approved argv binds.

    The hash is intentionally not an inventory of environment variables. It is
    a compact guard against silently running an immutable argv under a changed
    OS/Python/runtime-home identity. The caller sees only the digest.
    """
    material = {
        "schema_version": CONTINUATION_ENVIRONMENT_SCHEMA_VERSION,
        "os_name": os.name,
        "platform_system": platform.system(),
        "platform_release": platform.release(),
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
        "python_executable_sha256": hashlib.sha256(os.path.normcase(os.path.abspath(os.sys.executable)).encode("utf-8")).hexdigest(),
    }
    return hashlib.sha256(_canonical_json(material).encode("utf-8")).hexdigest()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _safe_workspace_path(root: Path, relative: str) -> Path:
    normalized = _normalize_path(relative, "continuation path")
    target = (root / normalized).resolve(strict=False)
    if not target.is_relative_to(root):
        raise ToolFailure("RUN_CONTINUATION_SCOPE_DENIED", "Continuation path escapes its workspace.", category="security")
    return target


def _safe_effect_backup_path(root: Path, relative: str) -> Path:
    """Resolve only the ledger-validated retained effect subtree, never generic evidence paths."""
    normalized = _normalize_effect_artifact_path(relative, "continuation backup path")
    target = (root / normalized).resolve(strict=False)
    if not target.is_relative_to(root):
        raise ToolFailure("RUN_CONTINUATION_EFFECT_INVALID", "Continuation backup path escapes its workspace.", category="security")
    return target


def _effect_backup_marker(path: Path) -> Path:
    return path.with_name(path.name + ".absent.json")


def _atomic_write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, raw_temp = tempfile.mkstemp(prefix=".continuation-effect-", dir=path.parent)
    temp = Path(raw_temp)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
        _fsync_directory(path.parent)
    finally:
        try:
            temp.unlink(missing_ok=True)
        except OSError:
            pass


def _fsync_directory(directory: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    try:
        fd = os.open(directory, flags)
    except OSError:
        return
    try:
        os.fsync(fd)
    except OSError:
        pass
    finally:
        os.close(fd)


def materialize_continuation_effect_backups(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    """Write retained preimages before a patch, idempotently and content-free in ledger.

    Existing-file backups contain the original bytes at the exact manifest path.
    A new file gets a tiny retained absent-marker instead; its declared preimage
    is still hash-bound in the ledger manifest. Neither source content nor the
    marker payload is copied into the canonical ledger.
    """
    rows = manifest.get("files") if isinstance(manifest, dict) else None
    if not isinstance(rows, list) or not rows:
        raise ToolFailure("RUN_CONTINUATION_EFFECT_INVALID", "Effect backup materialization requires a manifest file list.", category="validation")
    root = root.resolve(strict=False)
    written = 0
    reused = 0
    for row in rows:
        if not isinstance(row, dict):
            raise ToolFailure("RUN_CONTINUATION_EFFECT_INVALID", "Effect backup manifest row is invalid.", category="validation")
        source = _safe_workspace_path(root, str(row.get("path") or ""))
        backup = _safe_effect_backup_path(root, str(row.get("backup_path") or ""))
        expected = str(row.get("preimage_sha256") or "")
        if source.exists() and source.is_dir():
            raise ToolFailure("RUN_CONTINUATION_EFFECT_INVALID", "Effect target is a directory.", category="validation")
        current = source.read_bytes() if source.exists() else None
        current_hash = "absent" if current is None else _sha256(current)
        if current_hash != expected:
            raise ToolFailure(
                "RUN_CONTINUATION_EFFECT_PREIMAGE_STALE",
                "Effect preimage changed before retained backup materialization.",
                category="conflict",
                retryable=True,
                details={"path": str(row.get("path") or "")},
            )
        if current is None:
            marker = _effect_backup_marker(backup)
            marker_data = b'{"schema_version":1,"preimage":"absent"}\n'
            if marker.exists():
                if marker.read_bytes() != marker_data:
                    raise ToolFailure("RUN_CONTINUATION_EFFECT_BACKUP_CONFLICT", "Absent-marker backup has unexpected content.", category="runtime")
                reused += 1
            else:
                _atomic_write_bytes(marker, marker_data)
                written += 1
            continue
        if backup.exists():
            if backup.is_dir() or _sha256(backup.read_bytes()) != expected:
                raise ToolFailure("RUN_CONTINUATION_EFFECT_BACKUP_CONFLICT", "Retained effect backup does not match its manifest preimage.", category="runtime")
            reused += 1
            continue
        _atomic_write_bytes(backup, current)
        written += 1
    return {"written": written, "reused": reused, "retained": True}


def observe_continuation_effect(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    """Classify exact current images; mixed images are never replayed or rolled back."""
    rows = manifest.get("files") if isinstance(manifest, dict) else None
    if not isinstance(rows, list) or not rows:
        raise ToolFailure("RUN_CONTINUATION_EFFECT_INVALID", "Effect observation requires a manifest file list.", category="validation")
    root = root.resolve(strict=False)
    states: list[str] = []
    backup_missing: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            raise ToolFailure("RUN_CONTINUATION_EFFECT_INVALID", "Effect observation manifest row is invalid.", category="validation")
        path = str(row.get("path") or "")
        target = _safe_workspace_path(root, path)
        if target.exists() and target.is_dir():
            states.append("unknown")
        else:
            digest = "absent" if not target.exists() else _sha256(target.read_bytes())
            if digest == str(row.get("postimage_sha256") or ""):
                states.append("postimage")
            elif digest == str(row.get("preimage_sha256") or ""):
                states.append("preimage")
            else:
                states.append("unknown")
        backup = _safe_effect_backup_path(root, str(row.get("backup_path") or ""))
        expected = str(row.get("preimage_sha256") or "")
        if expected == "absent":
            marker = _effect_backup_marker(backup)
            if not marker.exists():
                backup_missing.append(path)
        elif not backup.exists() or backup.is_dir() or _sha256(backup.read_bytes()) != expected:
            backup_missing.append(path)
    if all(item == "postimage" for item in states):
        outcome = "applied"
    elif all(item == "preimage" for item in states):
        outcome = "not_applied"
    else:
        outcome = "recovery_required"
    return {"status": outcome, "backup_complete": not backup_missing, "backup_missing_paths": backup_missing, "states": states}


class ContinuationDriverMixin:
    """Driver and recovery methods mixed into the MCP Runtime composition root."""

    def _run_continuation_environment_hash(self) -> str:
        return continuation_execution_environment_hash()

    def _run_continuation_runtime_instance_id(self) -> str:
        return f"mcp:{self.process_instance_id}"

    @staticmethod
    def _run_continuation_failure_summary(result: dict[str, Any]) -> str:
        summary = str(result.get("summary") or "").strip()
        if _SENSITIVE_FAILURE_OUTPUT_RE.search(summary):
            return "[failure output withheld because it contains sensitive-like text]"
        return summary[:2_000]

    def _run_continuation_record_telemetry(
        self,
        run_id: str,
        event_type: str,
        *,
        outcome: str = "",
        code: str = "",
        duration_ms: int | None = None,
        marker: str = "",
    ) -> dict[str, Any] | None:
        """Persist only bounded machine facts; telemetry never grants authority."""
        try:
            record = self.orchestration_ledger._run_continuation_get_raw(run_id)
            ctx = self.orchestration_control.snapshot(run_id)
            policy = record.get("policy") if isinstance(record, dict) and isinstance(record.get("policy"), dict) else {}
            problem_id = str(policy.get("problem_id") or "")
            problem_revision = int(policy.get("problem_revision") or 0)
            if record is None:
                handoff = self.orchestration_ledger.problem_handoff_for_run(run_id)
                if isinstance(handoff, dict) and str(handoff.get("context_status") or "") == "VALID":
                    bound_problem_id = str(handoff.get("active_problem_id") or "")
                    bound_problem_revision = int(handoff.get("problem_revision") or 0)
                    if bound_problem_id and bound_problem_revision >= 1:
                        problem_id = bound_problem_id
                        problem_revision = bound_problem_revision
                else:
                    problem_id = ""
                    problem_revision = 0
            admission = self.activation_admission_snapshot()
            safe_code = re.sub(r"[^A-Za-z0-9_.:@-]+", "_", str(code or ""))[:128]
            logical_seed = {
                "run_id": run_id,
                "wave_id": str(ctx.wave_id if ctx is not None else ""),
                "event_type": event_type,
                "marker": str(marker or "")[:256],
                "outcome": outcome,
                "code": safe_code,
            }
            logical_id = "continuity-" + hashlib.sha256(
                _canonical_json(logical_seed).encode("utf-8")
            ).hexdigest()
            return self.orchestration_ledger.record_continuity_telemetry(
                logical_id=logical_id,
                run_id=run_id,
                wave_id=str(ctx.wave_id if ctx is not None else ""),
                event_type=event_type,
                problem_id=problem_id,
                problem_revision=problem_revision,
                task_context_id=str(self._current_stateless_task_context_id() or ""),
                activation_epoch_id=str(admission.get("activation_epoch_id") or ""),
                process_instance_id=str(getattr(self, "process_instance_id", "") or ""),
                server_instance_id=str(getattr(self, "server_instance_id", "") or ""),
                restart_ticket_id=str(
                    admission.get("restart_ticket_id") or admission.get("ticket_id") or ""
                ),
                outcome=outcome,
                code=safe_code,
                duration_ms=duration_ms,
            )
        except Exception:
            # Optimization telemetry is deliberately non-authoritative. A
            # telemetry failure cannot turn a safe continuation into a write.
            return None

    def _run_continuation_validate_execution_rebind(
        self, record: dict[str, Any], ctx: RunContext
    ) -> dict[str, Any]:
        """Prove execution-only continuity without changing immutable consent."""
        policy = record["policy"]
        run_id = str(record["run_id"])
        self._run_continuation_assert_runtime(policy)
        if str(self.tool_contract.get("sha256") or "") != str(policy.get("tool_contract_sha256") or ""):
            raise ToolFailure(
                "RUN_CONTINUATION_TOOL_CONTRACT_DRIFT",
                "The current public tool contract differs from the immutable continuation grant.",
                category="security",
            )
        try:
            self.orchestration_ledger.problem_get_exact_revision(
                str(policy["problem_id"]),
                int(policy["problem_revision"]),
                expected_contract_fingerprint=str(policy["contract_fingerprint"]),
            )
        except ProblemLineageError as exc:
            raise ToolFailure(
                "RUN_CONTINUATION_PROBLEM_BINDING_STALE",
                "Execution rebind requires the exact current Problem revision and an active PRL schema.",
                category="security",
            ) from exc
        binding = self.orchestration_ledger.controller_run_problem_binding(run_id)
        if not isinstance(binding, dict) or (
            str(binding.get("workspace_id") or policy["workspace_id"]) != str(policy["workspace_id"])
            or str(binding.get("problem_id") or "") != str(policy["problem_id"])
            or int(binding.get("problem_revision") or 0) != int(policy["problem_revision"])
        ):
            raise ToolFailure(
                "RUN_CONTINUATION_PROBLEM_BINDING_STALE",
                "The active RUN is not bound to the immutable continuation Problem revision.",
                category="security",
            )
        source = self._orchestration_workspace_identity(".")
        if (
            str(source.get("base_head") or "") != str(ctx.base_head or "")
            or str(source.get("worktree_fp") or "") != str(ctx.worktree_fp or "")
            or str(ctx.contract_fp or "") != str(policy.get("contract_fingerprint") or "")
        ):
            raise ToolFailure(
                "RUN_CONTINUATION_EVIDENCE_STALE",
                "Execution rebind requires the exact current RUN source and contract.",
                category="runtime",
                retryable=True,
            )
        controller_identity = self._continuity_current_controller_identity(required=True)
        assert controller_identity is not None
        attachment = self._continuity_assert_run_controller(run_id)
        controller = self.orchestration_ledger.get_controller_lease(run_id) or {}
        current_owner = str(controller_identity.get("owner_client_id") or "")
        if (
            not attachment
            or str(controller.get("status") or "") != "active"
            or str(controller.get("owner_client_id") or "") != current_owner
        ):
            raise ToolFailure(
                "RUN_CONTINUATION_CONTROLLER_REQUIRED",
                "Execution rebind requires the current durable Goal controller lease.",
                category="security",
            )
        admission = self.activation_admission_snapshot()
        successor_activation = (
            str(admission.get("activation_epoch_id") or "")
            != str(policy.get("activation_epoch_id") or "")
        )
        issuer = str(policy.get("issuer_client_id") or "")
        if successor_activation or current_owner != issuer:
            reattach_id = str(attachment.get("last_reattach_id") or "")
            receipt = (
                self.orchestration_ledger.controller_reattach_receipt(reattach_id)
                if reattach_id
                else None
            )
            transfers = receipt.get("active_run_transfers") if isinstance(receipt, dict) else []
            transferred_ids = {
                str(item.get("run_id") or "") for item in transfers or [] if isinstance(item, dict)
            }
            if (
                not isinstance(receipt, dict)
                or str(receipt.get("workspace_id") or "") != str(policy["workspace_id"])
                or str(receipt.get("problem_id") or "") != str(policy["problem_id"])
                or int(receipt.get("problem_revision") or 0) != int(policy["problem_revision"])
                or str(receipt.get("owner_client_id") or "") != current_owner
                or run_id not in transferred_ids
            ):
                raise ToolFailure(
                    "RUN_CONTINUATION_REATTACH_RECEIPT_REQUIRED",
                    "A different ChatWeb endpoint may inherit execution only through its exact durable reattach receipt.",
                    category="security",
                )
        return {
            "run_id": run_id,
            "wave_rebound": str(ctx.wave_id) != str(policy.get("grant_wave_id") or ""),
            "successor_activation": successor_activation,
            "controller_owner": current_owner,
        }

    def _run_continuation_try_auto_resume(
        self, *, run_id: str, trigger: str, marker: str = ""
    ) -> dict[str, Any]:
        """Resume one exact durable RUN only when all original authority still holds."""
        with self._run_continuation_driver_lock():
            record = self.orchestration_ledger._run_continuation_get_raw(run_id)
            if record is None:
                ctx_before_materialize = self.orchestration_control.snapshot(run_id)
                try:
                    materialized = self.orchestration_ledger.materialize_matching_goal_continuation(
                        run_id=run_id,
                        grant_wave_id=str(getattr(ctx_before_materialize, "wave_id", "") or ""),
                    )
                except RunContinuationError as exc:
                    code = str(exc.code)
                    self._run_continuation_record_telemetry(
                        run_id,
                        "continuation_failure",
                        outcome="failed",
                        code=code,
                        marker=marker or trigger,
                    )
                    return {"status": "BLOCKED", "run_id": run_id, "reason": code, "continue_observing": False}
                if str(materialized.get("status") or "") == "MISSING":
                    return {"status": "MISSING", "run_id": run_id}
                record = self.orchestration_ledger._run_continuation_get_raw(run_id)
                if record is None:
                    return {"status": "BLOCKED", "run_id": run_id, "reason": "GOAL_CONTINUATION_MATERIALIZATION_LOST"}
            pending = bool(
                record.get("pending_action_id")
                or record.get("pending_job_id")
                or record.get("pending_patch_action_id")
            )
            if pending:
                same_runtime_live = (
                    str(record.get("claimed_runtime_instance") or "")
                    == self._run_continuation_runtime_instance_id()
                    and _now_ms() < int(record.get("claim_expires_at_unix_ms") or 0)
                )
                if same_runtime_live and record.get("enabled"):
                    return {"status": "ALREADY_ACTIVE", "run_id": run_id}
                self._run_continuation_fail_closed_pause(run_id, "auto_resume_pending_effect")
                self._run_continuation_record_telemetry(
                    run_id,
                    "duplicate_effect_prevented",
                    outcome="prevented",
                    code="RUN_CONTINUATION_RECOVERY_RECONCILE_REQUIRED",
                    marker=marker or str(record.get("pending_action_id") or "pending"),
                )
                return {
                    "status": "RECOVERY_RECONCILE_REQUIRED",
                    "run_id": run_id,
                    "continue_observing": False,
                }
            if record.get("revoked_at"):
                self._run_continuation_record_telemetry(
                    run_id, "blocker", outcome="blocked", code="RUN_CONTINUATION_REVOKED", marker=marker
                )
                return {"status": "BLOCKED", "run_id": run_id, "reason": "RUN_CONTINUATION_REVOKED"}
            if _now_ms() >= int(record.get("expires_at_unix_ms") or 0):
                self._run_continuation_record_telemetry(
                    run_id, "blocker", outcome="blocked", code="RUN_CONTINUATION_EXPIRED", marker=marker
                )
                return {"status": "BLOCKED", "run_id": run_id, "reason": "RUN_CONTINUATION_EXPIRED"}
            ctx = self.orchestration_control.snapshot(run_id)
            if ctx is None:
                return {"status": "BLOCKED", "run_id": run_id, "reason": "RUN_CONTINUATION_RUN_CONTEXT_MISSING"}
            if ctx.state == "ACCEPTING":
                return {"status": "AWAITING_FINAL_ACCEPTANCE", "run_id": run_id, "wave_id": ctx.wave_id}
            if ctx.state in {"CHECKPOINTED", "BLOCKED", "ABORTED"}:
                event_type = "terminal" if ctx.state in {"CHECKPOINTED", "ABORTED"} else "blocker"
                self._run_continuation_record_telemetry(
                    run_id, event_type, outcome="terminal" if event_type == "terminal" else "blocked",
                    code=f"ORCHESTRATION_{ctx.state}", marker=marker,
                )
                return {"status": "TERMINAL", "run_id": run_id, "reason": f"ORCHESTRATION_{ctx.state}"}
            if ctx.state in {"EXECUTING", "PROVING"}:
                self._run_continuation_record_telemetry(
                    run_id, "blocker", outcome="blocked", code="RUN_CONTINUATION_STAGE_AMBIGUOUS", marker=marker
                )
                return {"status": "BLOCKED", "run_id": run_id, "reason": "RUN_CONTINUATION_STAGE_AMBIGUOUS"}
            try:
                rebind = self._run_continuation_validate_execution_rebind(record, ctx)
                if ctx.state == "REPLAN":
                    identity = self._orchestration_workspace_identity(".")
                    ctx = self.orchestration_control.begin_replan_wave(
                        ctx,
                        execution_mode="deep_single_lane",
                        base_head=str(identity.get("base_head") or ""),
                        worktree_fp=str(identity.get("worktree_fp") or ""),
                        contract_fp=str(record["policy"].get("contract_fingerprint") or ""),
                        reason=f"AUTO_RESUME_{str(trigger).upper()[:64]}",
                        metadata={"continuation": True, "auto_resume": True, "trigger": str(trigger)[:64]},
                    )
                    self._project_orchestration(ctx, event="run_continuation_auto_replan_wave")
                    self._run_continuation_record_telemetry(
                        run_id, "replan", outcome="succeeded", code="AUTO_RESUME_REPLAN", marker=ctx.wave_id
                    )
                    record = self.orchestration_ledger._run_continuation_get_raw(run_id) or record
                    rebind = self._run_continuation_validate_execution_rebind(record, ctx)
                if not record.get("enabled"):
                    record = self.orchestration_ledger.set_run_continuation_state(
                        run_id=run_id, action="resume", reason=f"auto_resume:{str(trigger)[:64]}"
                    )
                self._run_continuation_record_telemetry(
                    run_id, "continuation_attempt", outcome="attempted", code="AUTO_RESUME", marker=marker or trigger
                )
                started = self._run_continuation_start_driver({"run_id": run_id})
            except (RunContinuationError, ToolFailure, OrchestrationControlError) as exc:
                code = str(getattr(exc, "code", "RUN_CONTINUATION_AUTO_RESUME_FAILED"))
                self._run_continuation_record_telemetry(
                    run_id, "continuation_failure", outcome="failed", code=code, marker=marker or trigger
                )
                return {"status": "BLOCKED", "run_id": run_id, "reason": code, "continue_observing": False}
            self._run_continuation_record_telemetry(
                run_id, "continuation_success", outcome="succeeded", code="AUTO_RESUME", marker=marker or trigger
            )
            self._run_continuation_record_telemetry(
                run_id, "resume", outcome="succeeded", code=str(trigger)[:128], marker=marker or trigger
            )
            if str(trigger).lower() in {"reconnect", "reattach"}:
                self._run_continuation_record_telemetry(
                    run_id, "reconnect", outcome="succeeded", code=str(trigger)[:128], marker=marker or trigger
                )
            if rebind.get("successor_activation"):
                self._run_continuation_record_telemetry(
                    run_id, "restart", outcome="succeeded", code="SUCCESSOR_ACTIVATION", marker=marker or trigger
                )
            return {**started, "auto_resumed": True, "trigger": trigger, "execution_rebind": rebind}

    def _run_continuation_driver_lock(self) -> threading.RLock:
        lock = getattr(self, "_continuation_driver_lock", None)
        if lock is None:
            lock = threading.RLock()
            self._continuation_driver_lock = lock
        return lock

    def _run_continuation_start_worker(self, *, run_id: str, driver_generation: int) -> None:
        """Observe the exact dispatch without copying the request/hub controller context."""
        with self._run_continuation_driver_lock():
            workers = getattr(self, "_continuation_driver_workers", None)
            if workers is None:
                workers = {}
                self._continuation_driver_workers = workers
            active = workers.get(run_id)
            if isinstance(active, threading.Thread) and active.is_alive():
                return

            def worker() -> None:
                try:
                    while not bool(getattr(self, "_closed", False)):
                        outcome = self._run_continuation_observe_driver(
                            run_id=run_id,
                            expected_generation=driver_generation,
                            wait_ms=CONTINUATION_DRIVER_POLL_MS,
                        )
                        if not bool(outcome.get("continue_observing")):
                            return
                except Exception as exc:  # Defensive terminal boundary for detached work.
                    code = str(getattr(exc, "code", "RUN_CONTINUATION_DRIVER_FAILED"))[:128]
                    self._run_continuation_fail_closed_pause(run_id, f"driver:{code}")
                finally:
                    with self._run_continuation_driver_lock():
                        current = getattr(self, "_continuation_driver_workers", {}).get(run_id)
                        if current is threading.current_thread():
                            self._continuation_driver_workers.pop(run_id, None)

            thread = threading.Thread(target=worker, name=f"mcp-continuation-{run_id[:8]}", daemon=True)
            workers[run_id] = thread
            thread.start()

    def _run_continuation_fail_closed_pause(self, run_id: str, reason: str) -> None:
        """A detached driver may only reduce authority, never grant it."""
        try:
            record = self.orchestration_ledger._run_continuation_get_raw(run_id)
            if record is not None and record.get("enabled"):
                self.orchestration_ledger.set_run_continuation_state(run_id=run_id, action="pause", reason=reason[:512])
            self._run_continuation_record_telemetry(
                run_id, "interruption", outcome="observed", code=reason, marker=reason[:128]
            )
        except Exception:
            # A failed safety projection cannot justify retrying an unknown write.
            return

    def _run_continuation_assert_runtime(self, policy: dict[str, Any]) -> None:
        admission = self.activation_admission_snapshot()
        if str(admission.get("admission") or "").lower() != "open" or not str(admission.get("activation_epoch_id") or ""):
            raise ToolFailure("RUN_CONTINUATION_ADMISSION_REQUIRED", "Continuation driver requires an officially admitted runtime.", category="runtime")
        loaded = self._loaded_behavior_identity()
        if str(loaded.get("fingerprint") or "") != str(policy.get("runtime_behavior_fingerprint") or ""):
            raise ToolFailure("RUN_CONTINUATION_RUNTIME_DRIFT", "The currently loaded MCP behavior differs from the immutable continuation grant.", category="runtime")

    def _run_continuation_context(self, record: dict[str, Any]) -> tuple[RunContext, dict[str, Any]]:
        ctx = self.orchestration_control.snapshot(str(record["run_id"]))
        if ctx is None:
            raise ToolFailure("RUN_CONTINUATION_RUN_CONTEXT_MISSING", "The granted RUN has no recoverable orchestration context.", category="runtime")
        identity = self._orchestration_workspace_identity(".")
        if (
            str(identity.get("base_head") or "") != str(ctx.base_head or "")
            or str(identity.get("worktree_fp") or "") != str(ctx.worktree_fp or "")
            or str(ctx.contract_fp or "") != str(record["policy"].get("contract_fingerprint") or "")
        ):
            self._run_continuation_replan(ctx, "BASE_DRIFT", {"reason": "continuation source or contract drift"})
            raise ToolFailure("RUN_CONTINUATION_EVIDENCE_STALE", "RUN source/worktree/contract changed after continuation grant issuance.", category="runtime", retryable=True)
        route = {"requested": "sol_xhigh", "selected": "sol_xhigh", "profile": RUN_CONTINUATION_PROFILE, "model": "gpt-5.6-sol", "effort": "xhigh"}
        try:
            self.orchestration_control.resolve_execution_mode(ctx, "deep_single_lane")
            if ctx.state == "PREFLIGHT":
                self.orchestration_control.mark_ready(ctx, readiness={"continuation_grant": True, "route": "sol_xhigh"})
            if ctx.state == "READY":
                self.orchestration_control.select_route(ctx, route)
            if ctx.state != "ROUTED":
                raise ToolFailure("RUN_CONTINUATION_STATE_INVALID", "Continuation mutation/proof requires a routed RUN wave.", category="runtime", details={"state": ctx.state})
            if not ctx.delegation_id:
                self.orchestration_control.start_delegation(
                    ctx,
                    authority_owner="MCP",
                    route=route,
                    allowed_scope=list(record["policy"].get("write_paths") or []),
                    metadata={"kind": "run_continuation_driver", "model_is_proposal_only": True},
                )
            self._project_orchestration(ctx, event="run_continuation_routed")
        except OrchestrationControlError as exc:
            raise ToolFailure(exc.code, str(exc), category="runtime", retryable=True, details=exc.details) from exc
        return ctx, identity

    def _run_continuation_acquire_write(self, ctx: RunContext, identity: dict[str, Any], policy: dict[str, Any]) -> None:
        try:
            self.orchestration_control.acquire_write_lease(
                ctx,
                owner="MCP",
                mode="continuation_effect_journal",
                allowed_paths=list(policy.get("write_paths") or []),
                delegation_id=ctx.delegation_id,
                owner_session="run_continuation_driver",
                source_fingerprint=str(identity.get("source_fingerprint") or identity.get("worktree_fp") or ""),
                runtime_worktree_fingerprint=str(identity.get("runtime_worktree_fingerprint") or identity.get("worktree_fp") or ""),
                protected_paths=list(policy.get("protected_paths") or []),
                existing_dirty_source_paths=list(identity.get("dirty_source_paths") or identity.get("dirty_paths") or []),
            )
            self._project_orchestration(ctx, event="run_continuation_write_lease_acquired")
        except OrchestrationControlError as exc:
            raise ToolFailure(exc.code, str(exc), category="runtime", retryable=True, details=exc.details) from exc

    def _run_continuation_replan(self, ctx: RunContext, failure: str, payload: dict[str, Any]) -> None:
        if ctx.state in {"PREFLIGHT", "READY", "ROUTED", "EXECUTING", "PROVING", "ACCEPTING"}:
            try:
                self.orchestration_control.record_failure(ctx, failure, payload=payload)
                self._project_orchestration(ctx, event="run_continuation_replan_required")
            except OrchestrationControlError:
                return

    def _run_continuation_begin_technical_replan(
        self,
        *,
        ctx: RunContext,
        record: dict[str, Any],
        reason: str,
        payload: dict[str, Any],
    ) -> RunContext:
        """Create the next same-RUN technical WAVE from the post-effect bytes."""
        self._run_continuation_replan(ctx, reason, payload)
        if ctx.state != "REPLAN":
            raise ToolFailure("RUN_CONTINUATION_REPLAN_REQUIRED", "The failed continuation action did not reach the durable REPLAN state.", category="runtime")
        identity = self._orchestration_workspace_identity(".")
        try:
            replanned = self.orchestration_control.begin_replan_wave(
                ctx,
                execution_mode="deep_single_lane",
                base_head=str(identity.get("base_head") or ""),
                worktree_fp=str(identity.get("worktree_fp") or ""),
                contract_fp=str(record["policy"].get("contract_fingerprint") or ""),
                reason=reason,
                metadata={"continuation": True, "technical_replan": True, "failure": reason, "proof_id": payload.get("proof_id", "")},
            )
        except OrchestrationControlError as exc:
            raise ToolFailure(exc.code, str(exc), category="runtime", retryable=True, details=exc.details) from exc
        self._project_orchestration(replanned, event="run_continuation_technical_replan_wave")
        self._run_continuation_record_telemetry(
            ctx.run_id, "replan", outcome="observed", code=reason, marker=replanned.wave_id
        )
        return replanned

    def _run_continuation_dispatch_repair(
        self,
        *,
        record: dict[str, Any],
        ctx: RunContext,
        technical_replan: dict[str, Any],
        consumed_event_seq: int,
    ) -> dict[str, Any]:
        """Continue the exact proposal thread with bounded failed-proof evidence."""
        if record.get("pending_action_id"):
            raise ToolFailure("RUN_CONTINUATION_ACTION_PENDING", "A repair turn cannot replace an unresolved continuation action.", category="runtime")
        routed_ctx, _identity = self._run_continuation_context(record)
        if routed_ctx.wave_id != ctx.wave_id:
            raise ToolFailure("RUN_CONTINUATION_REPLAN_WAVE_STALE", "The continuation repair wave changed before dispatch.", category="runtime", retryable=True)
        evidence, evidence_hash = self._run_continuation_current_evidence(
            {**record, "pending_evidence_paths": [], "pending_replan": technical_replan}
        )
        request_hash = hashlib.sha256(
            _canonical_json({"kind": "technical_repair", "evidence_hash": evidence_hash, "proof_id": technical_replan["proof_id"]}).encode("utf-8")
        ).hexdigest()
        reservation = self.orchestration_ledger.reserve_run_continuation_action(
            run_id=ctx.run_id,
            driver_generation=int(record["driver_generation"]),
            runtime_instance_id=self._run_continuation_runtime_instance_id(),
            action_kind="repair_proposal",
            request_hash=request_hash,
            evidence_hash=evidence_hash,
            evidence_paths=[],
            technical_replan=technical_replan,
            expected_action_seq=int(record["next_action_seq"]),
        )
        if not reservation.get("reserved"):
            raise ToolFailure("RUN_CONTINUATION_ACTION_PENDING", "The technical repair action is already reserved; reconcile it before dispatch.", category="runtime")
        if not self._codex_bridge.owns_thread(str(record.get("thread_id") or "")):
            raise ToolFailure("RUN_CONTINUATION_DISPATCH_UNKNOWN", "The exact persisted continuation thread is not owned for technical repair dispatch.", category="runtime")
        bridge = self._codex_bridge.continue_thread(
            thread_id=str(record["thread_id"]),
            prompt=self._run_continuation_prompt(policy=record["policy"], evidence=evidence, evidence_hash=evidence_hash),
            output_schema=None,
        )
        thread_id, turn_id = str(bridge.get("thread_id") or ""), str(bridge.get("turn_id") or "")
        if thread_id != str(record["thread_id"]) or not turn_id:
            raise ToolFailure("RUN_CONTINUATION_DISPATCH_FAILED", "The bridge did not retain the exact continuation thread for technical repair.", category="runtime")
        action_id = str(reservation["action_id"])
        dispatch = self.orchestration_ledger.set_run_continuation_dispatch(
            run_id=ctx.run_id,
            driver_generation=int(record["driver_generation"]),
            runtime_instance_id=self._run_continuation_runtime_instance_id(),
            action_id=action_id,
            lane_id=str(record["lane_id"]),
            thread_id=thread_id,
            turn_id=turn_id,
        )
        return {
            "status": "PROPOSING",
            "run_id": ctx.run_id,
            "wave_id": ctx.wave_id,
            "action_id": action_id,
            "turn_id": turn_id,
            "evidence_hash": evidence_hash,
            "continuation": dispatch,
            "technical_replan": True,
            "continue_observing": True,
            "consumed_event_seq": consumed_event_seq,
        }

    def _run_continuation_exact_patch(
        self,
        proposal: dict[str, Any],
        *,
        action_id: str,
    ) -> tuple[dict[str, Any], str, list[str]]:
        root = self.workspace.root.resolve(strict=False)
        postimages: dict[str, bytes] = {}
        for replacement in proposal.get("replacements") or []:
            path = _normalize_path(replacement.get("path"), "PATCH path")
            target = _safe_workspace_path(root, path)
            if not target.exists() or target.is_dir():
                raise ToolFailure("RUN_CONTINUATION_PATCH_CONTEXT_MISSING", "PATCH replacement target is not a current file.", category="conflict", retryable=True, details={"path": path})
            try:
                current = target.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                raise ToolFailure("RUN_CONTINUATION_PATCH_ENCODING", "PATCH replacement target is not readable UTF-8.", category="validation", details={"path": path}) from exc
            old = str(replacement.get("old") or "")
            if current.count(old) != 1:
                raise ToolFailure("RUN_CONTINUATION_PATCH_AMBIGUOUS", "PATCH replacement must match exactly one current occurrence.", category="conflict", retryable=True, details={"path": path})
            postimages[path] = current.replace(old, str(replacement.get("new") or ""), 1).encode("utf-8")
        for created in proposal.get("new_files") or []:
            path = _normalize_path(created.get("path"), "PATCH new-file path")
            target = _safe_workspace_path(root, path)
            if target.exists():
                raise ToolFailure("RUN_CONTINUATION_PATCH_CONFLICT", "PATCH new file already exists.", category="conflict", retryable=True, details={"path": path})
            postimages[path] = str(created.get("content") or "").encode("utf-8")
        if not postimages:
            raise ToolFailure("RUN_CONTINUATION_PROPOSAL_INVALID", "PATCH proposal contains no exact file result.", category="validation")
        backup_root = f".coding-tools/orchestration/continuation-effects/{action_id}"
        manifest_rows: list[dict[str, str]] = []
        sections: list[str] = ["*** Begin Patch"]
        for path in sorted(postimages):
            target = _safe_workspace_path(root, path)
            before = None if not target.exists() else target.read_bytes()
            preimage = "absent" if before is None else _sha256(before)
            postimage = _sha256(postimages[path])
            manifest_rows.append({
                "path": path,
                "preimage_sha256": preimage,
                "postimage_sha256": postimage,
                "backup_path": f"{backup_root}/{path}",
            })
            encoded = base64.b64encode(zlib.compress(postimages[path], level=9)).decode("ascii")
            sections.extend([
                f"*** Write Exact File: {path}",
                f"@@ encoding=zlib-base64 preimage_sha256={preimage} postimage_sha256={postimage}",
                f"+{encoded}",
            ])
        sections.append("*** End Patch")
        return {"backup_root": backup_root, "files": manifest_rows}, "\n".join(sections), sorted(postimages)

    def _run_continuation_current_evidence(self, record: dict[str, Any]) -> tuple[dict[str, Any], str]:
        objective = str((self.orchestration_ledger.get_run(str(record["run_id"])) or {}).get("objective") or "")
        return self._run_continuation_canonical_evidence(
            record["policy"],
            objective=objective,
            selected_read_paths=record.get("pending_evidence_paths") or [],
            technical_replan=record.get("pending_replan") or None,
        )

    def _run_continuation_dispatch_next(
        self,
        record: dict[str, Any],
        *,
        requested_paths: Iterable[str],
        parent_action_id: str,
        consumed_event_seq: int,
        technical_replan: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        # A READ is a new model dispatch. Revalidate the exact RUN/WAVE identity
        # before reserving it so a later source/worktree drift cannot turn a
        # previously safe read catalogue into a new continuation turn.
        self._run_continuation_context(record)
        policy = record["policy"]
        selected_paths = sorted({_normalize_path(path, "READ path") for path in requested_paths})
        packet_record = {**record, "pending_evidence_paths": selected_paths, "pending_replan": technical_replan or {}}
        _evidence, evidence_hash = self._run_continuation_current_evidence(packet_record)
        request_hash = hashlib.sha256(_canonical_json({"parent_action_id": parent_action_id, "kind": "read", "paths": selected_paths, "evidence_hash": evidence_hash}).encode("utf-8")).hexdigest()
        reservation = self.orchestration_ledger.reserve_run_continuation_action(
            run_id=str(record["run_id"]),
            driver_generation=int(record["driver_generation"]),
            runtime_instance_id=self._run_continuation_runtime_instance_id(),
            action_kind="proposal",
            request_hash=request_hash,
            evidence_hash=evidence_hash,
            evidence_paths=selected_paths,
            technical_replan=technical_replan,
            expected_action_seq=int(record["next_action_seq"]),
        )
        if not reservation.get("reserved"):
            raise ToolFailure("RUN_CONTINUATION_ACTION_PENDING", "The next continuation proposal is already reserved; it must be reconciled first.", category="runtime")
        action_id = str(reservation["action_id"])
        evidence, actual_hash = self._run_continuation_current_evidence(
            packet_record
        )
        if actual_hash != evidence_hash:
            raise ToolFailure("RUN_CONTINUATION_EVIDENCE_STALE", "Source changed while preparing the bounded READ response.", category="runtime", retryable=True)
        if not self._codex_bridge.owns_thread(str(record["thread_id"])):
            raise ToolFailure("RUN_CONTINUATION_DISPATCH_UNKNOWN", "The exact persisted proposal thread is not owned by this MCP bridge process.", category="runtime")
        bridge = self._codex_bridge.continue_thread(
            thread_id=str(record["thread_id"]),
            prompt=self._run_continuation_prompt(policy=policy, evidence=evidence, evidence_hash=evidence_hash),
            output_schema=None,
        )
        thread_id, turn_id = str(bridge.get("thread_id") or ""), str(bridge.get("turn_id") or "")
        if thread_id != str(record["thread_id"]) or not turn_id:
            raise ToolFailure("RUN_CONTINUATION_DISPATCH_FAILED", "The bridge did not retain the exact continuation thread/turn identity.", category="runtime")
        dispatch = self.orchestration_ledger.set_run_continuation_dispatch(
            run_id=str(record["run_id"]),
            driver_generation=int(record["driver_generation"]),
            runtime_instance_id=self._run_continuation_runtime_instance_id(),
            action_id=action_id,
            lane_id=str(record["lane_id"]),
            thread_id=thread_id,
            turn_id=turn_id,
        )
        return {"status": "PROPOSING", "run_id": record["run_id"], "action_id": action_id, "turn_id": turn_id, "evidence_hash": evidence_hash, "continuation": dispatch, "continue_observing": True, "consumed_event_seq": consumed_event_seq}

    def _run_continuation_run_check(
        self,
        *,
        check: dict[str, Any],
        ctx: RunContext,
        record: dict[str, Any],
        action_id: str,
    ) -> tuple[dict[str, Any], str]:
        expected_environment = str(check.get("environment_hash") or "")
        if expected_environment != self._run_continuation_environment_hash():
            raise ToolFailure("RUN_CONTINUATION_ENVIRONMENT_DRIFT", "The approved proof argv is not bound to the current execution environment.", category="runtime", retryable=True, details={"check_id": check.get("check_id")})
        identity = self._orchestration_workspace_identity(".")
        proof_fp = self.proof_ledger.fingerprint(
            stage_id=f"run-continuation-check:{str(check.get('definition_hash') or '')[:16]}",
            base_head=str(identity.get("base_head") or ctx.base_head),
            worktree_fp=str(identity.get("worktree_fp") or ""),
            contract_fp=ctx.contract_fp,
            input_paths=list(record["policy"].get("write_paths") or []),
            config={"definition_hash": check.get("definition_hash"), "environment_hash": expected_environment},
            upstream_proof_ids=[],
        )

        def runner() -> dict[str, Any]:
            runtime_instance_id = self._run_continuation_runtime_instance_id()
            self.orchestration_ledger.assert_run_continuation_execution(
                run_id=ctx.run_id,
                driver_generation=int(record["driver_generation"]),
                runtime_instance_id=runtime_instance_id,
                check_definition_hash=str(check.get("definition_hash") or ""),
            )
            payload = self.exec_command({
                "_continuation_internal": True,
                "_argv": list(check.get("argv") or []),
                "workdir": str(check.get("cwd") or "."),
                "timeout_ms": 600_000,
                "yield_time_ms": 0,
                "max_output_bytes": CONTINUATION_DRIVER_MAX_OUTPUT_BYTES,
                "verbosity": "summary",
                "run_id": ctx.run_id,
                "wave_id": ctx.wave_id,
                "principal_id": "run-continuation-driver",
            })
            owner = payload.get("execution_owner") if isinstance(payload.get("execution_owner"), dict) else {}
            job_id = str(owner.get("job_id") or "")
            if not job_id:
                raise ToolFailure("RUN_CONTINUATION_JOB_MISSING", "Structured proof execution did not return its managed Job identity.", category="runtime")
            self.orchestration_ledger.set_run_continuation_pending_job(
                run_id=ctx.run_id,
                driver_generation=int(record["driver_generation"]),
                runtime_instance_id=runtime_instance_id,
                action_id=action_id,
                job_id=job_id,
            )
            while payload.get("status") == "running":
                payload = self.write_stdin({
                    "session_id": str(payload["session_id"]), "chars": "", "yield_time_ms": 30_000,
                    "max_output_bytes": CONTINUATION_DRIVER_MAX_OUTPUT_BYTES, "verbosity": "summary",
                })
                self.orchestration_ledger.renew_run_continuation_claim(
                    run_id=ctx.run_id,
                    runtime_instance_id=runtime_instance_id,
                    driver_generation=int(record["driver_generation"]),
                )
                self.orchestration_ledger.assert_run_continuation_execution(
                    run_id=ctx.run_id,
                    driver_generation=int(record["driver_generation"]),
                    runtime_instance_id=runtime_instance_id,
                    check_definition_hash=str(check.get("definition_hash") or ""),
                )
            self.orchestration_ledger.set_run_continuation_pending_job(
                run_id=ctx.run_id,
                driver_generation=int(record["driver_generation"]),
                runtime_instance_id=runtime_instance_id,
                action_id=action_id,
                job_id="",
            )
            return {
                "status": "passed" if command_payload_succeeded(payload) else "failed",
                "exit_code": payload.get("exit_code"),
                "duration_ms": int(payload.get("elapsed_ms") or 0),
                "summary": str(payload.get("summary") or payload.get("stderr") or payload.get("stdout") or "")[:8_000],
                "job_id": job_id,
                "command_id": payload.get("command_id"),
            }

        result, proof_id = self.proof_ledger.run_cached(
            run_id=ctx.run_id,
            wave_id=ctx.wave_id,
            stage_id=f"run-continuation-check:{str(check.get('definition_hash') or '')[:16]}",
            input_fingerprint=proof_fp,
            command=f"structured-argv:{str(check.get('definition_hash') or '')}",
            upstream_proof_ids=[],
            metadata={"kind": "run_continuation_check", "definition_hash": check.get("definition_hash"), "check_id": check.get("check_id")},
            runner=runner,
        )
        return result, proof_id

    def _run_continuation_complete_proof(
        self,
        *,
        record: dict[str, Any],
        action_id: str,
        ctx: RunContext,
        selected_hashes: Iterable[str],
        consumed_event_seq: int,
    ) -> dict[str, Any]:
        approved_checks = [item for item in record["policy"].get("approved_checks") or [] if isinstance(item, dict)]
        required_hashes = {str(item.get("definition_hash") or "") for item in approved_checks}
        selected = {str(item) for item in selected_hashes}
        if not required_hashes or selected != required_hashes:
            raise ToolFailure(
                "RUN_CONTINUATION_REQUIRED_CHECK_MISSING",
                "Every approved continuation check is mandatory before technical ACCEPTING.",
                category="security",
                details={"required_count": len(required_hashes), "selected_count": len(selected)},
            )
        checks = approved_checks
        if ctx.state == "ROUTED":
            self._run_continuation_acquire_write(ctx, self._orchestration_workspace_identity("."), record["policy"])
        try:
            if ctx.state == "EXECUTING":
                self.orchestration_control.begin_proof(ctx)
                self._project_orchestration(ctx, event="run_continuation_proving")
            if ctx.state != "PROVING":
                raise ToolFailure("RUN_CONTINUATION_STATE_INVALID", "Continuation proof requires PROVING state.", category="runtime", details={"state": ctx.state})
        except OrchestrationControlError as exc:
            raise ToolFailure(exc.code, str(exc), category="runtime", details=exc.details) from exc
        results: list[dict[str, Any]] = []
        proof_ids: list[str] = []
        for check in checks:
            self.orchestration_ledger.assert_run_continuation_execution(
                run_id=ctx.run_id,
                driver_generation=int(record["driver_generation"]),
                runtime_instance_id=self._run_continuation_runtime_instance_id(),
                check_definition_hash=str(check.get("definition_hash") or ""),
            )
            result, proof_id = self._run_continuation_run_check(check=check, ctx=ctx, record=record, action_id=action_id)
            results.append(result)
            proof_ids.append(proof_id)
            if result.get("status") != "passed":
                observation_kwargs: dict[str, str] = {}
                if str(record.get("parent_episode_id") or ""):
                    proof_identity = hashlib.sha256(
                        _canonical_json({
                            "schema_version": 1,
                            "kind": "approved_check",
                            "proof_id": str(proof_id),
                            "definition_hash": str(check.get("definition_hash") or ""),
                            "status": "failed",
                        }).encode("utf-8")
                    ).hexdigest()
                    observation_kwargs = {
                        "proof_observation_id": hashlib.sha256(
                            f"goal-continuation-proof-v1\0no_progress\0{proof_identity}".encode("utf-8")
                        ).hexdigest(),
                        "proof_identity_sha256": proof_identity,
                        "proof_outcome": "no_progress",
                    }
                completed = self.orchestration_ledger.complete_run_continuation_action(
                    run_id=ctx.run_id,
                    driver_generation=int(record["driver_generation"]),
                    runtime_instance_id=self._run_continuation_runtime_instance_id(),
                    action_id=action_id,
                    consumed_event_seq=consumed_event_seq,
                    **observation_kwargs,
                )
                goal_observation = completed.get("goal_observation") if isinstance(completed, dict) else None
                if isinstance(goal_observation, dict) and goal_observation.get("stopped"):
                    return {
                        "status": "PAUSED",
                        "run_id": ctx.run_id,
                        "proof_ids": proof_ids,
                        "check_results": results,
                        "reason": GOAL_CONTINUATION_NO_PROGRESS,
                        "no_progress_count": goal_observation.get("no_progress_count"),
                        "continue_observing": False,
                    }
                technical_replan = {
                    "failure": "CHECK_FAILED",
                    "check_id": str(check.get("check_id") or "unknown-check"),
                    "check_definition_hash": str(check.get("definition_hash") or ""),
                    "proof_id": str(proof_id),
                    "exit_code": result.get("exit_code"),
                    "summary": self._run_continuation_failure_summary(result),
                }
                raw = self.orchestration_ledger._run_continuation_get_raw(ctx.run_id)
                if raw is None:
                    raise ToolFailure("RUN_CONTINUATION_GRANT_REQUIRED", "Continuation grant disappeared after failed proof.", category="runtime")
                replanned_ctx = self._run_continuation_begin_technical_replan(
                    ctx=ctx,
                    record=raw,
                    reason="CHECK_FAILED",
                    payload={"proof_id": proof_id, "check_id": check.get("check_id"), "definition_hash": check.get("definition_hash")},
                )
                try:
                    repaired = self._run_continuation_dispatch_repair(
                        record=raw,
                        ctx=replanned_ctx,
                        technical_replan=technical_replan,
                        consumed_event_seq=consumed_event_seq,
                    )
                except (RunContinuationError, ToolFailure) as exc:
                    self._run_continuation_fail_closed_pause(ctx.run_id, f"technical_repair:{exc.code}")
                    return {
                        "status": "REPLAN_REQUIRED",
                        "run_id": ctx.run_id,
                        "proof_ids": proof_ids,
                        "check_results": results,
                        "reason": exc.code,
                        "continue_observing": False,
                    }
                return {**repaired, "proof_ids": proof_ids, "check_results": results}
        success_observation_kwargs: dict[str, str] = {}
        if str(record.get("parent_episode_id") or ""):
            proof_identity = hashlib.sha256(
                _canonical_json({
                    "schema_version": 1,
                    "kind": "approved_checks",
                    "proof_ids": sorted(str(item) for item in proof_ids),
                    "definition_hashes": sorted(required_hashes),
                    "status": "passed",
                }).encode("utf-8")
            ).hexdigest()
            success_observation_kwargs = {
                "proof_observation_id": hashlib.sha256(
                    f"goal-continuation-proof-v1\0progress\0{proof_identity}".encode("utf-8")
                ).hexdigest(),
                "proof_identity_sha256": proof_identity,
                "proof_outcome": "progress",
            }
        self.orchestration_ledger.complete_run_continuation_action(
            run_id=ctx.run_id,
            driver_generation=int(record["driver_generation"]),
            runtime_instance_id=self._run_continuation_runtime_instance_id(),
            action_id=action_id,
            consumed_event_seq=consumed_event_seq,
            **success_observation_kwargs,
        )
        try:
            self.orchestration_control.mark_accepting(ctx, proof_summary={"continuation": True, "proof_ids": proof_ids, "checks": [item.get("check_id") for item in checks]})
            self._project_orchestration(ctx, event="run_continuation_accepting")
            self._run_continuation_record_telemetry(
                ctx.run_id, "report_gate", outcome="pending", code="FINAL_ACCEPTANCE_REQUIRED", marker=ctx.wave_id
            )
        except OrchestrationControlError as exc:
            raise ToolFailure(exc.code, str(exc), category="runtime", details=exc.details) from exc
        return {"status": "ACCEPTING", "run_id": ctx.run_id, "wave_id": ctx.wave_id, "proof_ids": proof_ids, "check_results": results, "continue_observing": False, "recommended_next_action": "MCP completed exact technical proof. ChatWeb Sol must inspect the diff/proof and use task_control accept or reject; this is not final business acceptance."}

    def _run_continuation_apply_patch(
        self,
        *,
        record: dict[str, Any],
        action_id: str,
        proposal: dict[str, Any],
        consumed_event_seq: int,
    ) -> dict[str, Any]:
        _evidence, current_hash = self._run_continuation_current_evidence(record)
        if current_hash != str(record.get("pending_evidence_hash") or ""):
            ctx = self.orchestration_control.snapshot(str(record["run_id"]))
            if ctx is not None:
                self._run_continuation_replan(ctx, "BASE_DRIFT", {"reason": "proposal evidence hash no longer matches current source"})
            self._run_continuation_fail_closed_pause(str(record["run_id"]), "evidence_stale_before_patch")
            return {"status": "REPLAN_REQUIRED", "run_id": record["run_id"], "reason": "RUN_CONTINUATION_EVIDENCE_STALE", "continue_observing": False}
        # Validate RUN/WAVE and source identity before creating any retained
        # backup or journal entry.  A stale grant may leave no new effect
        # artifact merely because a model turn completed late.
        try:
            ctx, identity = self._run_continuation_context(record)
        except ToolFailure as exc:
            self._run_continuation_fail_closed_pause(str(record["run_id"]), f"patch:context:{exc.code}")
            return {
                "status": "REPLAN_REQUIRED",
                "run_id": record["run_id"],
                "reason": str(exc.code),
                "continue_observing": False,
            }
        manifest, patch, paths = self._run_continuation_exact_patch(proposal, action_id=action_id)
        try:
            runtime_instance_id = self._run_continuation_runtime_instance_id()
            self.orchestration_ledger.assert_run_continuation_execution(
                run_id=str(record["run_id"]),
                driver_generation=int(record["driver_generation"]),
                runtime_instance_id=runtime_instance_id,
                paths=paths,
            )
            self.orchestration_ledger.consume_run_continuation_patch_attempt(
                run_id=str(record["run_id"]),
                driver_generation=int(record["driver_generation"]),
                runtime_instance_id=runtime_instance_id,
                action_id=action_id,
            )
            self.orchestration_ledger.prepare_run_continuation_effect(
                run_id=str(record["run_id"]),
                driver_generation=int(record["driver_generation"]),
                runtime_instance_id=runtime_instance_id,
                action_id=action_id,
                effect_kind="patch",
                manifest=manifest,
            )
            materialize_continuation_effect_backups(self.workspace.root, manifest)
            self._run_continuation_acquire_write(ctx, identity, record["policy"])
            self.orchestration_control.assert_write_allowed(
                ctx,
                owner="MCP",
                owner_session="run_continuation_driver",
                paths=paths,
                base_head=str(identity.get("base_head") or ""),
                source_fingerprint=str(identity.get("source_fingerprint") or identity.get("worktree_fp") or ""),
                runtime_worktree_fingerprint=str(identity.get("runtime_worktree_fingerprint") or identity.get("worktree_fp") or ""),
                dirty_source_paths=list(identity.get("dirty_source_paths") or identity.get("dirty_paths") or []),
            )
            patch_result = self.apply_patch({"patch": patch, "dry_run": False})
            observed = observe_continuation_effect(self.workspace.root, manifest)
            if observed["status"] != "applied":
                self.orchestration_ledger.record_run_continuation_effect_observation(
                    run_id=ctx.run_id,
                    driver_generation=int(record["driver_generation"]),
                    runtime_instance_id=runtime_instance_id,
                    action_id=action_id,
                    status="recovery_required", recovery_reason="post_patch_images_not_all_postimage"
                )
                self._run_continuation_fail_closed_pause(ctx.run_id, "patch_postimage_unknown")
                self._run_continuation_replan(ctx, "PATCH_RECOVERY_REQUIRED", observed)
                return {"status": "PATCH_RECOVERY_REQUIRED", "run_id": ctx.run_id, "effect": observed, "continue_observing": False}
            self.orchestration_ledger.record_run_continuation_effect_observation(
                run_id=ctx.run_id,
                driver_generation=int(record["driver_generation"]),
                runtime_instance_id=runtime_instance_id,
                action_id=action_id,
                status="applied",
            )
            receipt = record_patch_surface(
                self.orchestration_ledger,
                run_id=ctx.run_id,
                wave_id=ctx.wave_id,
                patch_result=patch_result,
            )
            if receipt.get("recorded") is not True:
                raise ToolFailure(
                    "RUN_CONTINUATION_MUTATION_RECEIPT_REQUIRED",
                    "The applied continuation patch did not produce its durable mutation receipt.",
                    category="runtime",
                )
        except (RunContinuationError, ToolFailure) as exc:
            code = str(getattr(exc, "code", "RUN_CONTINUATION_PATCH_FAILED"))
            ctx = self.orchestration_control.snapshot(str(record["run_id"]))
            if ctx is not None:
                self._run_continuation_replan(ctx, code, {"action_id": action_id})
            self._run_continuation_fail_closed_pause(str(record["run_id"]), f"patch:{code}")
            return {"status": "REPLAN_REQUIRED", "run_id": record["run_id"], "reason": code, "continue_observing": False}
        return self._run_continuation_complete_proof(
            record=record, action_id=action_id, ctx=ctx, selected_hashes=proposal.get("selected_check_hashes") or [], consumed_event_seq=consumed_event_seq
        )

    def _run_continuation_observe_driver(
        self,
        *,
        run_id: str,
        expected_generation: int | None = None,
        wait_ms: int = 0,
    ) -> dict[str, Any]:
        with self._run_continuation_driver_lock():
            record = self.orchestration_ledger._run_continuation_get_raw(run_id)
            if record is None:
                return {"status": "MISSING", "run_id": run_id, "continue_observing": False}
            generation = int(record["driver_generation"])
            if expected_generation is not None and generation != int(expected_generation):
                return {"status": "STALE_GENERATION", "run_id": run_id, "continue_observing": False}
            try:
                runtime_instance_id = self._run_continuation_runtime_instance_id()
                self.orchestration_ledger.renew_run_continuation_claim(
                    run_id=run_id,
                    runtime_instance_id=runtime_instance_id,
                    driver_generation=generation,
                )
                self.orchestration_ledger.assert_run_continuation_execution(
                    run_id=run_id,
                    driver_generation=generation,
                    runtime_instance_id=runtime_instance_id,
                )
                self._run_continuation_assert_runtime(record["policy"])
            except (RunContinuationError, ToolFailure) as exc:
                self._run_continuation_fail_closed_pause(run_id, f"runtime:{getattr(exc, 'code', 'unknown')}")
                return {"status": "PAUSED", "run_id": run_id, "reason": str(getattr(exc, "code", "RUN_CONTINUATION_RUNTIME_INVALID")), "continue_observing": False}
            action_id = str(record.get("pending_action_id") or "")
            if not action_id:
                return {"status": "IDLE", "run_id": run_id, "continuation": self.orchestration_ledger.get_run_continuation(run_id), "continue_observing": False}
            if self.orchestration_ledger.get_run_continuation_effect(action_id) is not None:
                self._run_continuation_fail_closed_pause(run_id, "effect_reconciliation_requires_active_controller")
                return {"status": "RECONCILIATION_REQUIRED", "run_id": run_id, "action_id": action_id, "continue_observing": False}
            if str(record.get("pending_dispatch_action_id") or "") != action_id or not str(record.get("thread_id") or "") or not str(record.get("last_turn_id") or ""):
                self._run_continuation_fail_closed_pause(run_id, "dispatch_identity_unknown")
                return {"status": "DISPATCH_UNKNOWN", "run_id": run_id, "action_id": action_id, "continue_observing": False}
            if not self._codex_bridge.owns_thread(str(record["thread_id"])):
                self._run_continuation_fail_closed_pause(run_id, "bridge_turn_not_owned_after_restart")
                return {"status": "DISPATCH_UNKNOWN", "run_id": run_id, "action_id": action_id, "continue_observing": False}
            try:
                observed = self._codex_bridge.observe(
                    thread_id=str(record["thread_id"]), turn_id=str(record["last_turn_id"]), after_cursor=int(record.get("consumed_event_seq") or 0), wait_ms=wait_ms
                )
            except Exception as exc:
                self._run_continuation_fail_closed_pause(run_id, f"bridge_observe:{getattr(exc, 'code', type(exc).__name__)}")
                return {"status": "DISPATCH_UNKNOWN", "run_id": run_id, "action_id": action_id, "continue_observing": False}
            if not observed.get("terminal"):
                return {"status": "PROPOSING", "run_id": run_id, "action_id": action_id, "turn_id": record["last_turn_id"], "continue_observing": True}
            if str(observed.get("status") or "") != "completed":
                self._run_continuation_fail_closed_pause(run_id, f"proposal_terminal:{observed.get('status')}")
                return {"status": "PROPOSAL_FAILED", "run_id": run_id, "action_id": action_id, "continue_observing": False}
            try:
                decoded = json.loads(str(observed.get("agent_text") or ""))
                proposal = parse_run_continuation_proposal(
                    decoded,
                    expected_evidence_hash=str(record.get("pending_evidence_hash") or ""),
                    read_paths=record["policy"].get("read_paths") or [],
                    write_paths=record["policy"].get("write_paths") or [],
                    protected_paths=record["policy"].get("protected_paths") or [],
                    approved_check_hashes=[str(item.get("definition_hash") or "") for item in record["policy"].get("approved_checks") or [] if isinstance(item, dict)],
                )
            except (ValueError, RunContinuationError) as exc:
                self._run_continuation_fail_closed_pause(run_id, f"proposal_invalid:{getattr(exc, 'code', 'json')}")
                return {"status": "PROPOSAL_REJECTED", "run_id": run_id, "action_id": action_id, "reason": str(getattr(exc, "code", "RUN_CONTINUATION_PROPOSAL_INVALID")), "continue_observing": False}
            cursor = int(observed.get("next_cursor") or record.get("consumed_event_seq") or 0)
            if proposal["kind"] == "READ":
                completed = self.orchestration_ledger.complete_run_continuation_action(
                    run_id=run_id,
                    driver_generation=generation,
                    runtime_instance_id=runtime_instance_id,
                    action_id=action_id,
                    consumed_event_seq=cursor,
                )
                raw = self.orchestration_ledger._run_continuation_get_raw(run_id)
                if raw is None:
                    raise ToolFailure("RUN_CONTINUATION_GRANT_REQUIRED", "Continuation grant disappeared after terminal READ observation.", category="runtime")
                return self._run_continuation_dispatch_next(
                    raw,
                    requested_paths=[str(item["path"]) for item in proposal["read_requests"]],
                    parent_action_id=action_id,
                    consumed_event_seq=cursor,
                    technical_replan=record.get("pending_replan") or None,
                )
            if proposal["kind"] == "PATCH":
                return self._run_continuation_apply_patch(record=record, action_id=action_id, proposal=proposal, consumed_event_seq=cursor)
            if proposal["kind"] == "READY":
                try:
                    ctx, _identity = self._run_continuation_context(record)
                    return self._run_continuation_complete_proof(
                        record=record, action_id=action_id, ctx=ctx,
                        selected_hashes=[str(item.get("definition_hash") or "") for item in record["policy"].get("approved_checks") or [] if isinstance(item, dict)],
                        consumed_event_seq=cursor,
                    )
                except ToolFailure as exc:
                    ctx = self.orchestration_control.snapshot(run_id)
                    if ctx is not None:
                        self._run_continuation_replan(ctx, str(exc.code), {"action_id": action_id})
                    self._run_continuation_fail_closed_pause(run_id, f"ready:{exc.code}")
                    return {"status": "REPLAN_REQUIRED", "run_id": run_id, "reason": exc.code, "continue_observing": False}
            self.orchestration_ledger.complete_run_continuation_action(
                run_id=run_id,
                driver_generation=generation,
                runtime_instance_id=runtime_instance_id,
                action_id=action_id,
                consumed_event_seq=cursor,
            )
            ctx = self.orchestration_control.snapshot(run_id)
            raw = self.orchestration_ledger._run_continuation_get_raw(run_id)
            if ctx is not None and raw is not None and int(raw.get("remaining_decision_turns") or 0) > 0:
                technical_replan = {
                    "failure": "MODEL_BLOCKED",
                    "check_id": "model-proposal",
                    "check_definition_hash": hashlib.sha256(b"run-continuation-model-blocked-v1").hexdigest(),
                    "proof_id": action_id,
                    "exit_code": None,
                    "summary": str(proposal.get("reason") or "Model requested a non-authoritative stop.")[:2_000],
                }
                replanned = self._run_continuation_begin_technical_replan(
                    ctx=ctx,
                    record=raw,
                    reason="RUN_CONTINUATION_MODEL_BLOCKED",
                    payload={"action_id": action_id},
                )
                try:
                    return self._run_continuation_dispatch_repair(
                        record=raw,
                        ctx=replanned,
                        technical_replan=technical_replan,
                        consumed_event_seq=cursor,
                    )
                except (RunContinuationError, ToolFailure) as exc:
                    self._run_continuation_fail_closed_pause(run_id, f"model_blocked_repair:{exc.code}")
                    return {"status": "REPLAN_REQUIRED", "run_id": run_id, "reason": exc.code, "continue_observing": False}
            self._run_continuation_fail_closed_pause(run_id, "decision_budget_exhausted")
            self._run_continuation_record_telemetry(
                run_id, "blocker", outcome="blocked", code="RUN_CONTINUATION_DECISION_BUDGET_EXHAUSTED", marker=action_id
            )
            return {"status": "BLOCKED", "run_id": run_id, "reason": "RUN_CONTINUATION_DECISION_BUDGET_EXHAUSTED", "continue_observing": False}

    def _run_continuation_reconcile_driver(self, *, run_id: str, controller_fencing_token: object) -> dict[str, Any]:
        with self._run_continuation_driver_lock():
            record = self.orchestration_ledger._run_continuation_get_raw(run_id)
            if record is None:
                return {"status": "MISSING", "run_id": run_id, "continue_observing": False}
            action_id = str(record.get("pending_action_id") or "")
            if not action_id:
                return {"status": "IDLE", "run_id": run_id, "continue_observing": False}
            effect = self.orchestration_ledger.get_run_continuation_effect(action_id)
            if effect is None:
                self._run_continuation_fail_closed_pause(run_id, "pending_dispatch_requires_exact_bridge_observation")
                return {"status": "DISPATCH_UNKNOWN", "run_id": run_id, "action_id": action_id, "continue_observing": False}
            terminal_job_id = ""
            pending_job_id = str(record.get("pending_job_id") or "")
            if pending_job_id:
                managed_job = self.execution_resource_governor.find_exact_job(job_id=pending_job_id)
                if managed_job is None or managed_job.get("terminal") is not True:
                    self._run_continuation_fail_closed_pause(run_id, "pending_proof_job_outcome_unknown")
                    return {
                        "status": "PROOF_OUTCOME_UNKNOWN",
                        "run_id": run_id,
                        "action_id": action_id,
                        "job_id": pending_job_id,
                        "continue_observing": False,
                        "recommended_next_action": "The exact proof Job is not proven terminal. Keep the continuation paused; do not clear or replay its pending effect.",
                    }
                terminal_job_id = pending_job_id
            observed = observe_continuation_effect(self.workspace.root, effect["manifest"])
            target = str(observed["status"])
            reason = ""
            if target == "applied":
                reason = "effect_reobserved_proof_outcome_unknown"
            elif target == "not_applied":
                reason = "effect_reobserved_preimage_no_replay_without_exact_proposal"
            else:
                reason = "effect_reobserved_mixed_or_unknown_images"
            try:
                continuation = self.orchestration_ledger.reconcile_run_continuation_pending_action(
                    run_id=run_id,
                    action_id=action_id,
                    effect_status=target,
                    recovery_reason=reason,
                    controller_fencing_token=controller_fencing_token,
                    terminal_job_id=terminal_job_id,
                )
            except RunContinuationError as exc:
                return {"status": "PATCH_RECOVERY_REQUIRED", "run_id": run_id, "action_id": action_id, "reason": exc.code, "continue_observing": False}
            ctx = self.orchestration_control.snapshot(run_id)
            replanned_wave_id = ""
            if ctx is not None:
                try:
                    replanned = self._run_continuation_begin_technical_replan(
                        ctx=ctx,
                        record=continuation,
                        reason="PATCH_RECOVERY_REQUIRED",
                        payload={"action_id": action_id, "effect_status": target, "backup_complete": observed["backup_complete"]},
                    )
                    replanned_wave_id = replanned.wave_id
                except ToolFailure as exc:
                    return {"status": "PATCH_RECOVERY_REQUIRED", "run_id": run_id, "action_id": action_id, "reason": exc.code, "continue_observing": False}
            auto_resume = self._run_continuation_try_auto_resume(
                run_id=run_id, trigger="reconcile", marker=action_id
            )
            return {
                "status": "PATCH_RECOVERY_REPLANNED",
                "run_id": run_id,
                "wave_id": replanned_wave_id,
                "action_id": action_id,
                "effect": observed,
                "continuation": continuation,
                "auto_resume": auto_resume,
                "continue_observing": bool(auto_resume.get("continue_observing")),
                "recommended_next_action": "The exact pending effect was classified without replay. Eligible immutable continuation authority is resumed automatically; typed safety or authority blockers remain stopped.",
            }
