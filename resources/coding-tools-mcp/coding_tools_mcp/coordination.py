from __future__ import annotations

import hashlib
import json
import os
import secrets
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .envutils import ENV_PREFIX
from .acceptance_receipts import (
    _accepted_checkpoint_metadata,
    _accepted_checkpoint_file_receipts,
    _durable_wave_acceptance_paths,
    _verify_activation_source_checkpoint,
    _verify_lifecycle_snapshot,
    has_passed_proof,
    passed_proof_fingerprint,
    validate_passed_proof_source_binding,
)
from .codex_bridge import CodexBridgeError
from .controller_continuity import ControllerContinuityControlMixin
from .activation_capability import valid_activation_operation_id
from .activation_lifecycle import ActivationLifecycleMixin
from .errors import ToolFailure
from .fs_utils import is_relative_to
from .goal_pursuit import GoalPursuitControlMixin
from .lifecycle_census import lifecycle_census, open_lifecycle_census_snapshot, read_task_projection
from .orchestration_control import OrchestrationControlError
from .p5_control import P5ControlMixin
from .problem_lineage import ProblemLineageError
from .problem_lineage_control import ProblemLineageControlMixin
from .product_session_receipts import (
    record_accepted_remaining_criterion,
    record_continuity_read_receipt,
    record_current_continuity_core,
    record_execution_control_center_progress,
    record_goal_runtime_receipts,
)
from .solution_shadow_control import SolutionShadowControlMixin
from .restart_ticket import (
    SUPERVISOR_RESTART_TICKET_PREFIX,
    SUPERVISOR_RESTART_TICKET_TTL_MS,
    build_supervisor_restart_ticket,
    is_workspace_maintenance_reason,
    observe_installed_restart_ticket,
    supervisor_restart_response,
    supervisor_restart_ticket_matches,
)

BACKGROUND_OPERATION_WAIT_MAX_MS = 60_000
COORDINATION_LANE_OUTPUT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "status": {
            "type": "string",
            "enum": ["completed", "blocked", "needs_input"],
        },
        "summary": {"type": "string", "maxLength": 2_000},
        "question": {"type": ["string", "null"], "maxLength": 1_000},
        "findings": {
            "type": "array",
            "maxItems": 8,
            "items": {"type": "string", "maxLength": 700},
        },
        "missing_proof": {
            "type": "array",
            "maxItems": 8,
            "items": {"type": "string", "maxLength": 700},
        },
        "next_action": {"type": "string", "maxLength": 1_000},
        "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
    },
    "required": [
        "status",
        "summary",
        "question",
        "findings",
        "missing_proof",
        "next_action",
        "confidence",
    ],
}
class CoordinationMixin(ActivationLifecycleMixin, ControllerContinuityControlMixin, GoalPursuitControlMixin, SolutionShadowControlMixin, P5ControlMixin, ProblemLineageControlMixin):
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
            return result

    def cancel_activation(self, operation_id: str) -> bool:
        with self.activation_lock:
            self._activation_cleanup_locked()
            if not self.activation_fence:
                return False
            if str(self.activation_fence.get("operation_id") or "") != str(operation_id or ""):
                raise ToolFailure("ACTIVATION_OPERATION_MISMATCH", "Activation fence belongs to another operation.", category="validation")
            self.activation_fence = None
            return True

    def _coordination_ids(self, args: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], str, str]:
        self._reconcile_task_orchestration_projection()
        state = self.task_state.get()
        projection = state.get("orchestration") if isinstance(state.get("orchestration"), dict) else {}
        run_id = str(args.get("run_id") or projection.get("run_id") or "").strip()
        wave_id = str(args.get("wave_id") or projection.get("wave_id") or "").strip()
        if not run_id and not self.task_state.is_scoped():
            active = self.orchestration_ledger.current_active_run()
            run_id = str(active.get("run_id") or "") if active else ""
            if run_id and not wave_id:
                waves = self.orchestration_ledger.list_waves(run_id)
                wave_id = str(waves[-1].get("wave_id") or "") if waves else ""
        return state, projection, run_id, wave_id

    def _require_operator_report_ack(self, operation: str) -> None:
        pending = self.task_state.pending_completion_report()
        if pending is None:
            return
        raise ToolFailure(
            "OPERATOR_REPORT_ACK_REQUIRED",
            f"Present and acknowledge the pending operator completion report before {operation}.",
            category="runtime",
            retryable=True,
            details=pending,
        )

    @staticmethod
    def _coordination_lane_outcome(bridge_result: dict[str, Any]) -> dict[str, Any]:
        observation = bridge_result.get("observation") if isinstance(bridge_result.get("observation"), dict) else {}
        status = str(observation.get("status") or bridge_result.get("status") or "unknown")
        terminal = bool(observation.get("terminal")) or status in {
            "completed",
            "failed",
            "interrupted",
            "deadline",
        }
        text = str(observation.get("agent_text") or "").strip()
        try:
            parsed = json.loads(text) if text else None
        except (TypeError, ValueError, json.JSONDecodeError):
            parsed = None
        if isinstance(parsed, dict):
            response = {
                "status": str(parsed.get("status") or "blocked"),
                "summary": str(parsed.get("summary") or "")[:2_000],
                "question": str(parsed.get("question") or "")[:1_000] or None,
                "findings": [str(item)[:700] for item in list(parsed.get("findings") or [])[:8]],
                "missing_proof": [str(item)[:700] for item in list(parsed.get("missing_proof") or [])[:8]],
                "next_action": str(parsed.get("next_action") or "")[:1_000],
                "confidence": str(parsed.get("confidence") or "low"),
            }
        elif text:
            response = {
                "status": "blocked",
                "summary": "Codex returned an unstructured response.",
                "question": None,
                "findings": [],
                "missing_proof": ["structured_lane_output"],
                "next_action": "Review the bounded agent_text and repacket instead of retrying unchanged.",
                "confidence": "low",
                "agent_text": text[:4_000],
            }
        else:
            response = {
                "status": "blocked" if terminal else "running",
                "summary": "No terminal structured result is available yet.",
                "question": None,
                "findings": [],
                "missing_proof": [],
                "next_action": "Poll the lane with task_control action=lane lane_action=observe.",
                "confidence": "low",
            }
        return {
            "status": status,
            "terminal": terminal,
            "thread_id": str(bridge_result.get("thread_id") or ""),
            "turn_id": str(bridge_result.get("turn_id") or observation.get("turn_id") or ""),
            "session_id": str(bridge_result.get("session_id") or ""),
            "lifetime": str(bridge_result.get("lifetime") or "persistent"),
            "creation_mode": bridge_result.get("creation_mode"),
            "route": observation.get("route") or bridge_result.get("route"),
            "wall_time_ms": observation.get("wall_time_ms"),
            "economics": observation.get("economics"),
            "deadline_hit": bool(observation.get("deadline_hit", bridge_result.get("deadline_hit", False))),
            "error": observation.get("error"),
            "response": response,
        }

    def _record_coordination_lane_outcome(
        self,
        lane: dict[str, Any],
        bridge_result: dict[str, Any],
    ) -> dict[str, Any]:
        outcome = self._coordination_lane_outcome(bridge_result)
        response = outcome["response"]
        if not outcome["terminal"]:
            lifecycle = "active"
        elif outcome["status"] == "completed" and response.get("status") == "completed":
            lifecycle = "idle"
        else:
            lifecycle = "waiting"
        route = outcome.get("route") if isinstance(outcome.get("route"), dict) else {}
        lane_id = str(lane["lane_id"])
        updated = self.orchestration_ledger.update_agent_lane(
            lane_id,
            lifecycle=lifecycle,
            thread_id=outcome.get("thread_id") or lane.get("thread_id") or "",
            session_id=outcome.get("session_id") or lane.get("session_id") or "",
            last_turn_id=outcome.get("turn_id") or lane.get("last_turn_id") or "",
            profile=str(route.get("profile") or lane.get("profile") or ""),
            model=str(route.get("model") or lane.get("model") or ""),
            effort=str(route.get("effort") or lane.get("effort") or ""),
            metadata={
                "last_bridge_status": outcome["status"],
                "deadline_hit": outcome["deadline_hit"],
                "last_wall_time_ms": outcome.get("wall_time_ms"),
                "last_economics": outcome.get("economics"),
                "owner_process_instance_id": self.process_instance_id,
            },
        ) or lane
        if outcome["terminal"] and outcome.get("turn_id"):
            kind = "question" if response.get("question") else "result"
            stable_id = hashlib.sha256(
                f"{lane_id}:{outcome['turn_id']}:{kind}".encode("utf-8")
            ).hexdigest()
            self.orchestration_ledger.append_coordination_message(
                message_id=stable_id,
                run_id=str(updated.get("run_id") or ""),
                wave_id=str(updated.get("wave_id") or ""),
                lane_id=lane_id,
                direction="codex_to_chatweb",
                kind=kind,
                status="pending",
                base_head=str(updated.get("base_head") or ""),
                worktree_fp=str(updated.get("worktree_fp") or ""),
                payload={
                    "turn_id": outcome["turn_id"],
                    "bridge_status": outcome["status"],
                    "response": response,
                    "error": outcome.get("error"),
                    "economics": outcome.get("economics"),
                    "deadline_hit": outcome.get("deadline_hit"),
                },
            )
        return {"lane": updated, "outcome": outcome}

    def _coordination_lane(self, args: dict[str, Any]) -> dict[str, Any]:
        state, projection, run_id, wave_id = self._coordination_ids(args)
        lane_action = str(args.get("lane_action") or "list").strip().lower()
        if lane_action == "list":
            return {
                "state": state,
                "lanes": self.orchestration_ledger.list_agent_lanes(
                    run_id=run_id,
                    lifecycle=str(args.get("lifecycle") or "").strip(),
                ),
            }

        semantic_key = str(args.get("semantic_key") or "").strip()
        lane_id = str(args.get("lane_id") or "").strip()
        lane = self.orchestration_ledger.get_agent_lane(lane_id) if lane_id else None
        if lane is None and semantic_key and run_id:
            lane = self.orchestration_ledger.find_agent_lane(
                run_id=run_id,
                semantic_key=semantic_key,
            )

        if lane_action == "start":
            if not semantic_key:
                raise ToolFailure(
                    "SEMANTIC_KEY_REQUIRED",
                    "semantic_key is required when lane_action=start.",
                    category="validation",
                )
            if lane is not None:
                return {
                    "status": "existing_lane",
                    "lane": lane,
                    "recommended_next_action": "Use lane_action=continue; duplicate persistent lanes are not auto-created.",
                }
            prompt = str(args.get("prompt") or "").strip()
            if not prompt:
                raise ToolFailure("PROMPT_REQUIRED", "prompt is required when lane_action=start.", category="validation")
            profile = str(args.get("profile") or "cross_file").strip().lower()
            lane_id = lane_id or secrets.token_urlsafe(12)
            identity = self._orchestration_workspace_identity(".")
            contract_fp = str(args.get("contract_fingerprint") or projection.get("contract_fp") or "")
            claimed_lane_id = self.orchestration_ledger.upsert_agent_lane(
                lane_id=lane_id,
                run_id=run_id,
                wave_id=wave_id,
                semantic_key=semantic_key,
                role=str(args.get("role") or "executor")[:100],
                lifecycle="starting",
                profile=profile,
                model=str(args.get("model") or ""),
                effort=str(args.get("effort") or ""),
                base_head=str(identity.get("base_head") or ""),
                worktree_fp=str(identity.get("worktree_fp") or ""),
                contract_fp=contract_fp,
                metadata={
                    "created_by": "ChatWeb Sol",
                    "conversation_epoch": args.get("conversation_epoch", 1),
                    "owner_process_instance_id": self.process_instance_id,
                },
            )
            if claimed_lane_id != lane_id:
                existing_lane = self.orchestration_ledger.get_agent_lane(claimed_lane_id)
                return {
                    "status": "existing_lane",
                    "lane": existing_lane,
                    "recommended_next_action": "Use lane_action=continue; a concurrent caller already claimed this semantic lane.",
                }
            lane = self.orchestration_ledger.get_agent_lane(lane_id) or {"lane_id": lane_id}
            self.orchestration_ledger.append_coordination_message(
                run_id=run_id,
                wave_id=wave_id,
                lane_id=lane_id,
                direction="chatweb_to_codex",
                kind="instruction",
                base_head=str(identity.get("base_head") or ""),
                worktree_fp=str(identity.get("worktree_fp") or ""),
                payload={
                    "prompt": prompt,
                    "summary": str(args.get("summary") or semantic_key)[:1_000],
                    "profile": profile,
                },
            )
            try:
                bridge_result = self._codex_bridge.run(
                    prompt,
                    profile=profile,
                    model=str(args.get("model") or "").strip() or None,
                    effort=str(args.get("effort") or "").strip().lower() or None,
                    lifetime="persistent",
                    deadline_ms=max(0, min(int(args.get("deadline_ms", 0)), 30_000)),
                    output_schema=COORDINATION_LANE_OUTPUT_SCHEMA,
                    wait_ms=max(0, min(int(args.get("wait_ms", 0)), 30_000)),
                )
            except CodexBridgeError as exc:
                updated = self.orchestration_ledger.update_agent_lane(
                    lane_id,
                    lifecycle="waiting",
                    metadata={"last_error": exc.code, "retryable": exc.retryable},
                ) or lane
                self.orchestration_ledger.append_coordination_message(
                    run_id=run_id,
                    wave_id=wave_id,
                    lane_id=lane_id,
                    direction="codex_to_chatweb",
                    kind="error",
                    payload={"code": exc.code, "message": str(exc), "retryable": exc.retryable},
                )
                return {
                    "status": "blocked",
                    "lane": updated,
                    "error": {"code": exc.code, "message": str(exc), "retryable": exc.retryable},
                    "recommended_next_action": "Repacket or choose one policy-approved alternative; do not retry unchanged.",
                }
            route = bridge_result.get("route") if isinstance(bridge_result.get("route"), dict) else {}
            lane = self.orchestration_ledger.update_agent_lane(
                lane_id,
                lifecycle="active",
                thread_id=str(bridge_result.get("thread_id") or ""),
                session_id=str(bridge_result.get("session_id") or ""),
                last_turn_id=str(bridge_result.get("turn_id") or ""),
                profile=str(route.get("profile") or profile),
                model=str(route.get("model") or ""),
                effort=str(route.get("effort") or ""),
                metadata={"owner_process_instance_id": self.process_instance_id},
            ) or lane
            return {"status": "started", **self._record_coordination_lane_outcome(lane, bridge_result)}

        if lane is None:
            raise ToolFailure("LANE_NOT_FOUND", "The requested persistent lane was not found.", category="not_found")
        lane_id = str(lane["lane_id"])
        if lane_action == "close":
            updated = self.orchestration_ledger.update_agent_lane(
                lane_id,
                lifecycle="closed",
                metadata={"closed_reason": str(args.get("reason") or "closed_by_chatweb")[:1_000]},
            ) or lane
            self.orchestration_ledger.append_coordination_message(
                run_id=str(updated.get("run_id") or ""),
                wave_id=str(updated.get("wave_id") or ""),
                lane_id=lane_id,
                direction="system",
                kind="lane_closed",
                payload={"reason": str(args.get("reason") or "closed_by_chatweb")[:1_000]},
            )
            return {"status": "closed", "lane": updated}

        if lane_action == "observe":
            if not self._codex_bridge.owns_thread(str(lane.get("thread_id") or "")):
                return {
                    "status": "waiting",
                    "lane": lane,
                    "messages": self.orchestration_ledger.list_coordination_messages(
                        lane_id=lane_id,
                        status="pending",
                        limit=max(1, min(int(args.get("limit", 20)), 100)),
                    ),
                    "reason": "live_turn_handle_not_owned_after_runtime_rollover",
                    "recommended_next_action": "Use lane_action=continue to resume the persisted thread with a compact delta packet.",
                }
            observation = self._codex_bridge.observe(
                thread_id=str(lane.get("thread_id") or ""),
                turn_id=str(args.get("turn_id") or lane.get("last_turn_id") or "") or None,
                after_cursor=max(0, int(args.get("after_cursor", 0))),
                wait_ms=max(0, min(int(args.get("wait_ms", 0)), 30_000)),
                max_events=max(1, min(int(args.get("max_events", 50)), 100)),
            )
            bridge_result = {
                "status": observation.get("status"),
                "thread_id": lane.get("thread_id"),
                "turn_id": observation.get("turn_id") or lane.get("last_turn_id"),
                "session_id": lane.get("session_id"),
                "lifetime": "persistent",
                "route": {
                    "profile": lane.get("profile"),
                    "model": lane.get("model"),
                    "effort": lane.get("effort"),
                },
                "observation": observation,
            }
            return {"status": "observed", **self._record_coordination_lane_outcome(lane, bridge_result)}

        if lane_action != "continue":
            raise ToolFailure(
                "INVALID_LANE_ACTION",
                f"Unsupported lane_action: {lane_action}",
                category="validation",
            )
        if str(lane.get("lifecycle") or "") == "closed":
            raise ToolFailure("LANE_CLOSED", "The persistent lane is closed.", category="runtime")
        prompt = str(args.get("prompt") or "").strip()
        if not prompt:
            raise ToolFailure("PROMPT_REQUIRED", "prompt is required when lane_action=continue.", category="validation")
        identity = self._orchestration_workspace_identity(".")
        current_contract = str(args.get("contract_fingerprint") or lane.get("contract_fp") or "")
        drift = {
            "base_head": [lane.get("base_head"), identity.get("base_head")],
            "worktree_fp": [lane.get("worktree_fp"), identity.get("worktree_fp")],
            "contract_fp": [lane.get("contract_fp"), current_contract],
        }
        changed = {
            key: values for key, values in drift.items()
            if values[0] and values[1] and values[0] != values[1]
        }
        if changed and not bool(args.get("allow_rebase", False)):
            return {
                "status": "blocked",
                "lane": lane,
                "reason": "lane_base_drift",
                "drift": changed,
                "recommended_next_action": "Revalidate affected evidence, then continue with allow_rebase=true and a material reason.",
            }
        if changed:
            reason = str(args.get("reason") or "").strip()
            if not reason:
                raise ToolFailure(
                    "REBASE_REASON_REQUIRED",
                    "reason is required when allow_rebase=true and lane state drifted.",
                    category="validation",
                )
            lane = self.orchestration_ledger.update_agent_lane(
                lane_id,
                base_head=str(identity.get("base_head") or ""),
                worktree_fp=str(identity.get("worktree_fp") or ""),
                contract_fp=current_contract,
                metadata={
                    "rebase_reason": reason[:1_000],
                    "revalidated_at": datetime.now(timezone.utc).isoformat(),
                    "owner_process_instance_id": self.process_instance_id,
                },
            ) or lane
            self.orchestration_ledger.append_coordination_message(
                run_id=str(lane.get("run_id") or ""),
                wave_id=str(lane.get("wave_id") or ""),
                lane_id=lane_id,
                direction="system",
                kind="lane_rebased",
                base_head=str(identity.get("base_head") or ""),
                worktree_fp=str(identity.get("worktree_fp") or ""),
                payload={"reason": reason[:1_000], "drift": changed},
            )
        self.orchestration_ledger.append_coordination_message(
            run_id=str(lane.get("run_id") or ""),
            wave_id=str(lane.get("wave_id") or ""),
            lane_id=lane_id,
            direction="chatweb_to_codex",
            kind="instruction",
            base_head=str(lane.get("base_head") or ""),
            worktree_fp=str(lane.get("worktree_fp") or ""),
            payload={"prompt": prompt, "summary": str(args.get("summary") or "lane continuation")[:1_000]},
        )
        profile = str(args.get("profile") or lane.get("profile") or "cross_file")
        try:
            if self._codex_bridge.owns_thread(str(lane.get("thread_id") or "")):
                bridge_result = self._codex_bridge.continue_thread(
                    thread_id=str(lane.get("thread_id") or ""),
                    prompt=prompt,
                    model=str(args.get("model") or lane.get("model") or "").strip() or None,
                    effort=str(args.get("effort") or lane.get("effort") or "").strip().lower() or None,
                    deadline_ms=max(0, min(int(args.get("deadline_ms", 0)), 30_000)),
                    output_schema=COORDINATION_LANE_OUTPUT_SCHEMA,
                    wait_ms=max(0, min(int(args.get("wait_ms", 0)), 30_000)),
                )
            else:
                bridge_result = self._codex_bridge.resume_persistent_thread(
                    thread_id=str(lane.get("thread_id") or ""),
                    expected_session_id=str(lane.get("session_id") or ""),
                    prompt=prompt,
                    profile=profile,
                    model=str(args.get("model") or lane.get("model") or "").strip() or None,
                    effort=str(args.get("effort") or lane.get("effort") or "").strip().lower() or None,
                    deadline_ms=max(0, min(int(args.get("deadline_ms", 0)), 30_000)),
                    output_schema=COORDINATION_LANE_OUTPUT_SCHEMA,
                    wait_ms=max(0, min(int(args.get("wait_ms", 0)), 30_000)),
                )
        except CodexBridgeError as exc:
            updated = self.orchestration_ledger.update_agent_lane(
                lane_id,
                lifecycle="waiting",
                metadata={"last_error": exc.code, "retryable": exc.retryable},
            ) or lane
            self.orchestration_ledger.append_coordination_message(
                run_id=str(updated.get("run_id") or ""),
                wave_id=str(updated.get("wave_id") or ""),
                lane_id=lane_id,
                direction="codex_to_chatweb",
                kind="error",
                payload={"code": exc.code, "message": str(exc), "retryable": exc.retryable},
            )
            return {
                "status": "blocked",
                "lane": updated,
                "error": {"code": exc.code, "message": str(exc), "retryable": exc.retryable},
                "recommended_next_action": "Repacket or select one different route; do not retry unchanged.",
            }
        return {"status": "continued", **self._record_coordination_lane_outcome(lane, bridge_result)}

    def _supervisor_restart_request_path(self) -> Path:
        raw = os.environ.get(f"{ENV_PREFIX}_SUPERVISOR_REQUEST_FILE", "").strip()
        if not raw:
            raise ToolFailure(
                "SUPERVISOR_UNAVAILABLE",
                "This MCP runtime is not attached to an Electron supervisor restart channel.",
                category="runtime",
                retryable=False,
            )
        request_path = Path(raw).expanduser().resolve(strict=False)
        if is_relative_to(request_path, self.workspace.root):
            raise ToolFailure(
                "UNSAFE_SUPERVISOR_CHANNEL",
                "Supervisor restart requests must be stored outside the project workspace.",
                category="permission",
                retryable=False,
            )
        if not request_path.parent.is_dir():
            raise ToolFailure(
                "SUPERVISOR_UNAVAILABLE",
                "The Electron supervisor request directory is unavailable.",
                category="runtime",
                retryable=True,
            )
        return request_path

    def _enqueue_runtime_restart(self, args: dict[str, Any]) -> dict[str, Any]:
        if args.get("confirm_restart") is not True:
            raise ToolFailure(
                "RESTART_CONFIRMATION_REQUIRED",
                "Set confirm_restart=true only after the user explicitly requests a runtime restart.",
                category="permission",
                retryable=False,
            )
        reason = str(args.get("reason") or "User requested runtime restart")
        allow_acceptance_pending = args.get("allow_acceptance_pending") is True
        target_workspace = (
            str(self._current_request_workspace_root())
            if is_workspace_maintenance_reason(reason)
            else str(self.workspace.root)
        )
        with self.sessions_lock:
            active_commands = sum(1 for session in self.sessions.values() if session.process.poll() is None)
            starting_commands = int(self.starting_sessions)
        with self.background_operations_lock:
            active_background = sum(
                1
                for item in self.background_operations.values()
                if item.get("workspace") == str(self.workspace.root) and not item["event"].is_set()
            )
        if active_commands or starting_commands or active_background:
            raise ToolFailure(
                "RUNTIME_BUSY",
                "Refusing to restart while commands or background workflows are still active.",
                category="runtime",
                retryable=True,
                details={
                    "active_commands": active_commands,
                    "starting_commands": starting_commands,
                    "active_background_operations": active_background,
                },
            )

        request_path = self._supervisor_restart_request_path()
        with self.supervisor_request_lock:
            now_ms = int(time.time() * 1000)
            processing_path = request_path.with_name(f"{request_path.name}.processing")
            fence_operation_id = str(self.activation_fence.get("operation_id") or "") if self.activation_fence else ""
            for existing_path in (processing_path, request_path):
                if not existing_path.is_file():
                    continue
                try:
                    existing = json.loads(existing_path.read_text(encoding="utf-8"))
                except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                    continue
                if supervisor_restart_ticket_matches(
                    existing,
                    now_ms=now_ms,
                    workspace=str(self.workspace.root),
                    process_instance_id=self.process_instance_id,
                    server_instance_id=self.server_instance_id,
                    tool_contract_sha256=str(self.tool_contract["sha256"]),
                    fence_operation_id=fence_operation_id,
                    allow_acceptance_pending=allow_acceptance_pending,
                    target_workspace=target_workspace,
                ):
                    return supervisor_restart_response(existing, already_pending=True)

            # Keep the operation identity compatible with every activation
            # boundary.  ``token_urlsafe`` may begin with ``-`` or ``_``;
            # prefixing it with an alphanumeric value makes the generated
            # ticket valid for the stricter Recovery Host/MCP operation
            # contract while retaining the opaque random suffix.
            ticket_id = f"{SUPERVISOR_RESTART_TICKET_PREFIX}{secrets.token_urlsafe(12)}"
            # Build and serialize the complete envelope before installing the
            # in-memory fence. After the fence is installed, only the atomic
            # filesystem operation remains.
            ticket = build_supervisor_restart_ticket(
                ticket_id=ticket_id,
                now_ms=now_ms,
                workspace=str(self.workspace.root),
                process_instance_id=self.process_instance_id,
                server_instance_id=self.server_instance_id,
                tool_contract_sha256=str(self.tool_contract["sha256"]),
                reason=reason,
                allow_acceptance_pending=allow_acceptance_pending,
                target_workspace=target_workspace,
            )
            serialized_ticket = json.dumps(ticket, ensure_ascii=False, sort_keys=True)
            temporary = request_path.with_name(f".{request_path.name}.{ticket_id}.tmp")
            preflight = self.activation_preflight(
                operation_id=ticket_id,
                expires_at_unix_ms=now_ms + SUPERVISOR_RESTART_TICKET_TTL_MS,
                allow_acceptance_pending=allow_acceptance_pending,
                allow_self_controller_lease=True,
                prepare=True,
                ignore_active_tool_calls=1,
            )
            if not preflight.get("safe"):
                raise ToolFailure(
                    str(preflight.get("code") or "ORCHESTRATION_STATE_UNCERTAIN"),
                    f"Controlled restart preflight refused: {preflight.get('reason') or 'runtime state is not safe'}.",
                    category="runtime",
                    retryable=str(preflight.get("code") or "") == "RUNTIME_BUSY",
                    details=preflight,
                )
            try:
                temporary.write_text(serialized_ticket, encoding="utf-8")
                os.replace(temporary, request_path)
            except Exception as exc:
                installation_state = observe_installed_restart_ticket(request_path, ticket)
                if installation_state in {"absent", "different"}:
                    try:
                        self.cancel_activation(ticket_id)
                    except (ToolFailure, RuntimeError):
                        pass
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass
                if installation_state == "exact":
                    return supervisor_restart_response(ticket, already_pending=False)
                if installation_state == "unknown":
                    raise ToolFailure(
                        "SUPERVISOR_REQUEST_STATE_UNCERTAIN",
                        "The supervisor restart ticket may have been installed; admission remains fenced until the supervisor consumes it or the fence expires.",
                        category="runtime",
                        retryable=False,
                        details={"error": str(exc), "installation_state": installation_state},
                    ) from exc
                raise ToolFailure(
                    "SUPERVISOR_REQUEST_FAILED",
                    "Could not enqueue the Electron supervisor restart request.",
                    category="runtime",
                    retryable=True,
                    details={"error": str(exc)},
                ) from exc
            return supervisor_restart_response(ticket, already_pending=False)

    def _abort_task_orchestration(self, state: dict[str, Any], *, reason: str) -> dict[str, Any] | None:
        projection = state.get("orchestration") if isinstance(state.get("orchestration"), dict) else {}
        run_id = str(projection.get("run_id") or "").strip()
        if not run_id:
            return None
        ctx = self.orchestration_control.snapshot(run_id)
        if ctx is None:
            return None
        if ctx.state in {"CHECKPOINTED", "BLOCKED", "ABORTED"}:
            return ctx.projection()
        try:
            self.orchestration_control.transition(ctx, "ABORTED", reason=reason)
        except OrchestrationControlError as exc:
            raise ToolFailure(
                "ORCHESTRATION_ABORT_FAILED",
                str(exc),
                category="runtime",
                retryable=False,
                details={"run_id": run_id, "state": ctx.state, "reason": reason, **getattr(exc, "details", {})},
            ) from exc
        self._project_orchestration(ctx, event="task_orchestration_aborted")
        return ctx.projection()

    def task_control(self, args: dict[str, Any]) -> dict[str, Any]:
        action = str(args.get("action", "get")).lower()
        acceptance_files = args.get("acceptance_files") if "acceptance_files" in args else None
        if action == "accept" and "payload" in args:
            payload = args.get("payload")
            if not isinstance(payload, dict):
                raise ToolFailure(
                    "ACCEPTANCE_PAYLOAD_INVALID",
                    "Final-acceptance compatibility payload must be an object.",
                    category="validation",
                )
            unexpected = sorted(set(payload) - {"acceptance_files"})
            if unexpected or "acceptance_files" not in payload:
                raise ToolFailure(
                    "ACCEPTANCE_PAYLOAD_INVALID",
                    "Final-acceptance compatibility payload may contain only acceptance_files.",
                    category="validation",
                    details={"unsupported": unexpected},
                )
            if "acceptance_files" in args:
                raise ToolFailure(
                    "ACCEPTANCE_TRANSPORT_AMBIGUOUS",
                    "Supply acceptance_files through exactly one transport.",
                    category="validation",
                )
            acceptance_files = payload.get("acceptance_files")
        if action == "restart_runtime":
            return self._enqueue_runtime_restart(args)
        requested_run = str(args.get("run_id") or "").strip()
        if requested_run:
            self._assert_task_control_workspace(requested_run)
        exact_recovery_run = str(
            getattr(self.request_context, "stateless_exact_run_recovery_id", "") or ""
        ).strip()
        projection_recovery_run = requested_run if (
            action == "get" or (requested_run and requested_run == exact_recovery_run)
        ) else ""
        try:
            self._reconcile_task_orchestration_projection(requested_run_id=projection_recovery_run)
        except RuntimeError as exc:
            raise ToolFailure(
                "EXACT_RUN_RECOVERY_REFUSED",
                str(exc),
                category="runtime",
                retryable=False,
                details={"run_id": requested_run},
            ) from exc
        if projection_recovery_run:
            recovered_ctx = self.orchestration_control.snapshot(projection_recovery_run)
            recovered_state = self.task_state.get()
            if (
                recovered_ctx is not None
                and recovered_ctx.state in {"CHECKPOINTED", "REPLAN", "BLOCKED", "ABORTED"}
                and not str(recovered_state.get("completion_report_id") or "").strip()
            ):
                recovered_result = self._orchestration_result(recovered_ctx, write_reports=False)
                recovered_report = (
                    recovered_result.get("completion_report")
                    if isinstance(recovered_result, dict)
                    else None
                )
                if not isinstance(recovered_report, dict):
                    raise ToolFailure(
                        "EXACT_RUN_REPORT_MATERIALIZATION_FAILED",
                        "Exact-run recovery reached a report-bearing state but no completion report was derived.",
                        category="runtime",
                        retryable=False,
                        details={
                            "run_id": projection_recovery_run,
                            "wave_id": recovered_ctx.wave_id,
                            "state": recovered_ctx.state,
                        },
                    )
                persisted_state = self.task_state.set_completion_report(recovered_report)
                persisted_report_id = str(persisted_state.get("completion_report_id") or "").strip()
                persisted_report = (
                    persisted_state.get("completion_report")
                    if isinstance(persisted_state.get("completion_report"), dict)
                    else {}
                )
                persisted_source = (
                    persisted_report.get("source_run_wave")
                    if isinstance(persisted_report.get("source_run_wave"), dict)
                    else {}
                )
                if (
                    not persisted_report_id
                    or str(persisted_source.get("run_id") or "") != projection_recovery_run
                    or str(persisted_source.get("wave_id") or "") != str(recovered_ctx.wave_id or "")
                ):
                    raise ToolFailure(
                        "EXACT_RUN_REPORT_MATERIALIZATION_FAILED",
                        "Exact-run completion report did not persist against the recovered RUN/WAVE projection.",
                        category="runtime",
                        retryable=False,
                        details={
                            "run_id": projection_recovery_run,
                            "wave_id": recovered_ctx.wave_id,
                            "state": recovered_ctx.state,
                        },
                    )
        if action == "p5":
            return self._p5_control(args)
        if action == "problem":
            return self._problem_control(args)
        if action == "goal":
            result = self._goal_control(args)
            record_goal_runtime_receipts(self, args, result)
            return result
        if action == "continuity":
            result = self._controller_continuity_control(args)
            record_current_continuity_core(self, args, result)
            record_continuity_read_receipt(self, args, result)
            return result
        if action == "run_continuation":
            return self._run_continuation_control(args)
        if action == "get":
            return self._coordination_get_state()
        if action == "lane":
            return self._coordination_lane(args)
        if action == "events":
            _state, _projection, run_id, _wave_id = self._coordination_ids(args)
            if not run_id:
                raise ToolFailure("ORCHESTRATION_RUN_NOT_FOUND", "No orchestration run is associated with the current task.", category="not_found")
            replay = self.orchestration_ledger.list_events_since(
                run_id,
                after_seq=max(0, int(args.get("after_seq", 0))),
                limit=max(1, min(int(args.get("limit", 100)), 500)),
            )
            replay["recommended_next_action"] = (
                "Call task_control action=events with after_seq=next_after_seq until has_more=false."
                if replay.get("has_more")
                else "Event replay is current; continue from task state, pending messages, and the latest handoff capsule."
            )
            identity = self._current_hub_client()
            observed = replay.get("events") or []
            if identity and observed:
                replay["client_cursor"] = self.orchestration_ledger.advance_hub_client_cursor(
                    client_id=self._hub_client_record_id(identity),
                    run_id=run_id,
                    last_event_seq=int(observed[-1].get("seq") or 0),
                )
            return replay
        if action == "messages":
            _state, _projection, run_id, _wave_id = self._coordination_ids(args)
            return {
                "messages": self.orchestration_ledger.list_coordination_messages(
                    run_id=run_id,
                    lane_id=str(args.get("lane_id") or "").strip(),
                    status=str(args.get("message_status") or "pending").strip(),
                    direction=str(args.get("direction") or "").strip(),
                    limit=max(1, min(int(args.get("limit", 20)), 100)),
                )
            }
        if action == "ack":
            message_id = str(args.get("message_id") or "").strip()
            if not message_id:
                raise ToolFailure("MESSAGE_ID_REQUIRED", "message_id is required when action=ack.", category="validation")
            message = self.orchestration_ledger.acknowledge_coordination_message(message_id)
            if message is not None:
                return {"acknowledged": True, "message": message}
            state = self.task_state.get()
            current_report_id = str(state.get("completion_report_id") or "").strip()
            try:
                acknowledged_state = self.task_state.ack_completion_report(message_id)
            except ValueError as exc:
                if "ambiguous across task contexts" in str(exc):
                    raise ToolFailure(
                        "OPERATOR_REPORT_ACK_AMBIGUOUS",
                        str(exc),
                        category="conflict",
                        details={"report_id": message_id},
                    ) from exc
                if current_report_id and message_id == current_report_id:
                    raise ToolFailure(
                        "OPERATOR_REPORT_ACK_INVALID",
                        str(exc),
                        category="runtime",
                        retryable=True,
                        details={"report_id": message_id},
                    ) from exc
                raise ToolFailure(
                    "MESSAGE_NOT_FOUND",
                    "The coordination message or workspace-local completion report was not found.",
                    category="not_found",
                ) from exc
            ack_projection = (
                acknowledged_state.get("orchestration")
                if isinstance(acknowledged_state.get("orchestration"), dict)
                else {}
            )
            ack_run_id = str(ack_projection.get("run_id") or "")
            auto_resume = None
            if ack_run_id:
                self._run_continuation_record_telemetry(
                    ack_run_id, "report_gate", outcome="succeeded", code="REPORT_ACKNOWLEDGED", marker=message_id
                )
                auto_resume = self._run_continuation_try_auto_resume(
                    run_id=ack_run_id, trigger="report_gate", marker=message_id
                )
            return {
                "acknowledged": True,
                "acknowledgement_type": "operator_completion_report",
                "report_id": message_id,
                "state": self.task_state.get() if auto_resume is not None else acknowledged_state,
                "continuation_auto_resume": auto_resume,
            }
        if action == "handoff":
            state, projection, run_id, wave_id = self._coordination_ids(args)
            handoff_action = str(args.get("handoff_action") or "get").strip().lower()
            if handoff_action == "get":
                capsule = self.orchestration_ledger.latest_handoff_capsule(run_id=run_id)
                return {
                    "capsule": capsule,
                    "recommended_next_action": (
                        "Resume from this capsule and pending messages; do not replay the previous ChatWeb transcript."
                        if capsule else
                        "Record a bounded handoff capsule before rolling to a new ChatWeb conversation."
                    ),
                }
            if handoff_action != "record":
                raise ToolFailure("INVALID_HANDOFF_ACTION", f"Unsupported handoff_action: {handoff_action}", category="validation")
            payload = args.get("payload")
            if not isinstance(payload, dict):
                raise ToolFailure("HANDOFF_PAYLOAD_REQUIRED", "payload object is required when handoff_action=record.", category="validation")
            if "problem_lineage" in payload:
                raise ToolFailure(
                    "HANDOFF_PRL_FIELD_RESERVED",
                    "problem_lineage is derived from exact PRL links and cannot be caller-supplied in a handoff payload.",
                    category="validation",
                )
            hub_identity = self._current_hub_client() or {}
            if hub_identity.get("client_type") == "electron" and hub_identity.get("client_id") == "electron-panel":
                state, projection, run_id, wave_id = self.panel_handoff_state(args.get("run_id"), args.get("wave_id"))
            pending_messages = self.orchestration_ledger.list_coordination_messages(
                run_id=run_id,
                status="pending",
                limit=50,
            )
            active_lanes = self.orchestration_ledger.list_agent_lanes(run_id=run_id)
            augmented = dict(payload)
            workspace_snapshot = self._orchestration_workspace_identity(".")
            workspace_identity = workspace_snapshot.get("workspace_identity") if isinstance(workspace_snapshot.get("workspace_identity"), dict) else {}
            proof_ids = [
                str(item.get("proof_id") or "")
                for item in self.orchestration_ledger.list_proofs(run_id, wave_id=wave_id or None)
                if str(item.get("proof_id") or "").strip()
            ][:100]
            problem_lineage = self.orchestration_ledger.problem_handoff_for_run(run_id) if run_id else None
            if problem_lineage is not None:
                augmented["problem_lineage"] = problem_lineage
            augmented["runtime"] = {
                "task_id": state.get("task_id"),
                "objective": state.get("objective"),
                "task_status": state.get("status"),
                "current_step": state.get("current_step"),
                "next_step": state.get("next_step"),
                "run_id": run_id,
                "wave_id": wave_id,
                "orchestration_state": projection.get("orchestration_state"),
                "base_head": projection.get("base_head"),
                "worktree_fp": projection.get("worktree_fp"),
                "contract_fp": projection.get("contract_fp"),
                "workspace_id": workspace_identity.get("workspace_id"),
                "root_id": workspace_identity.get("root_id"),
                "session_workspace_id": workspace_identity.get("session_workspace_id"),
                "authority_from": str(hub_identity.get("client_id") or "runtime")[:128],
                "authority_to": str(payload.get("authority_to") or "")[:128],
                "write_lease_id": projection.get("write_lease_id"),
                "write_owner": projection.get("write_owner"),
                "delegation_id": projection.get("delegation_id"),
                "source_fingerprint": workspace_snapshot.get("source_fingerprint"),
                "diff_fp": workspace_snapshot.get("worktree_fp"),
                "dirty_paths": list(workspace_snapshot.get("dirty_paths") or [])[:200],
                "proof_ids": proof_ids,
                "unresolved_risks": [str(item)[:500] for item in (payload.get("unresolved_risks") or [])[:50]] if isinstance(payload.get("unresolved_risks"), list) else [],
                "active_lane_ids": [
                    row["lane_id"] for row in active_lanes
                    if row.get("lifecycle") not in {"closed"}
                ][:20],
                "pending_message_ids": [row["message_id"] for row in pending_messages][:50],
            }
            try:
                capsule = self.orchestration_ledger.record_handoff_capsule(
                    run_id=run_id,
                    wave_id=wave_id,
                    conversation_epoch=max(1, int(args.get("conversation_epoch", 1))),
                    payload=augmented,
                )
            except ValueError as exc:
                raise ToolFailure(
                    "HANDOFF_CAPSULE_TOO_LARGE",
                    str(exc),
                    category="validation",
                    details={"strategy": "Store hashes, proof ids and next actions instead of transcript or raw command output."},
                ) from exc
            return {
                "recorded": True,
                "capsule": capsule,
                "recommended_next_action": "Open a fresh ChatWeb conversation, fetch this capsule, then poll pending messages.",
            }
        if action == "quality":
            state = self.task_state.get()
            projection = state.get("orchestration") if isinstance(state.get("orchestration"), dict) else {}
            run_id = str(args.get("run_id") or projection.get("run_id") or "").strip()
            wave_id = str(args.get("wave_id") or "").strip()
            if not run_id:
                raise ToolFailure("ORCHESTRATION_RUN_NOT_FOUND", "No orchestration run is available for a quality outcome.", category="not_found")
            outcome = args.get("quality_outcome")
            if not isinstance(outcome, dict):
                raise ToolFailure("QUALITY_OUTCOME_REQUIRED", "quality_outcome is required when action=quality.", category="validation")
            try:
                recorded = self.orchestration_ledger.record_quality_outcome(run_id=run_id, wave_id=wave_id, outcome=outcome)
            except ValueError as exc:
                raise ToolFailure("QUALITY_OUTCOME_INVALID", str(exc), category="validation") from exc
            return {"recorded": True, "quality_outcome": recorded}
        if action == "observation":
            state = self.task_state.get()
            projection = state.get("orchestration") if isinstance(state.get("orchestration"), dict) else {}
            run_id = str(args.get("run_id") or projection.get("run_id") or "").strip()
            wave_id = str(args.get("wave_id") or "").strip()
            if not run_id:
                raise ToolFailure("ORCHESTRATION_RUN_NOT_FOUND", "No orchestration run is available for an observation span.", category="not_found")
            span = args.get("observation_span")
            if not isinstance(span, dict):
                raise ToolFailure("OBSERVATION_SPAN_REQUIRED", "observation_span is required when action=observation.", category="validation")
            try:
                recorded = self.orchestration_ledger.record_observation_span(run_id=run_id, wave_id=wave_id, span=span)
            except ValueError as exc:
                raise ToolFailure("OBSERVATION_SPAN_INVALID", str(exc), category="validation") from exc
            control_center_receipt = record_execution_control_center_progress(
                self,
                run_id=run_id,
                wave_id=wave_id,
                span=span,
            )
            return {
                "recorded": bool(recorded.get("recorded")),
                "observation_span": recorded,
                "control_center_receipt": control_center_receipt,
                "critical_path": self.orchestration_ledger.critical_path_analysis(run_id),
            }
        if action == "solution_shadow":
            return self._solution_shadow_control(
                args,
                args.get("solution_shadow_recommendation"),
                transport="typed_solution_shadow",
            )
        if action in {"audit", "accept", "reject"}:
            state = self.task_state.get()
            projection = state.get("orchestration") if isinstance(state.get("orchestration"), dict) else {}
            run_id = str(args.get("run_id") or projection.get("run_id") or "").strip()
            if not run_id:
                raise ToolFailure("ORCHESTRATION_RUN_NOT_FOUND", "No orchestration run is associated with the current task.", category="not_found")
            ctx = self.orchestration_control.snapshot(run_id)
            if ctx is None:
                raise ToolFailure("ORCHESTRATION_RUN_NOT_FOUND", "The requested orchestration run was not found.", category="not_found")
            if action == "audit":
                reports = self.orchestration_report.write_reports(run_id)
                limit = max(1, min(int(args.get("limit", 20)), 100))
                wave_filter = str(args.get("wave_id") or "").strip()
                if wave_filter or "after_seq" in args:
                    try:
                        summary = self.orchestration_ledger.evidence_query(
                            run_id,
                            wave_id=wave_filter,
                            after_seq=max(0, int(args.get("after_seq", 0))) if "after_seq" in args else None,
                            limit=limit,
                        )
                    except ValueError as exc:
                        raise ToolFailure(
                            "ORCHESTRATION_WAVE_NOT_FOUND",
                            str(exc),
                            category="not_found",
                            details={"run_id": run_id, "wave_id": wave_filter},
                        ) from exc
                else:
                    summary = self.orchestration_ledger.export_summary(run_id)
                    summary["events"] = summary.get("events", [])[-limit:]
                    summary["proofs"] = summary.get("proofs", [])[-limit:]
                orchestration_result = self._orchestration_result(ctx, write_reports=False)
                return {
                    "state": state,
                    "orchestration": orchestration_result,
                    "completion_report": (orchestration_result or {}).get("completion_report"),
                    "audit": summary,
                    "resources": self.execution_resource_governor.snapshot(),
                    "reports": reports,
                }
            if action == "accept":
                controller_acceptance_started_ms = self.orchestration_control.observation_now_ms()
                controller = self._require_hub_controller(run_id)
                if ctx.state != "ACCEPTING":
                    raise ToolFailure(
                        "FINAL_ACCEPTANCE_NOT_READY",
                        f"Run is in {ctx.state}, not ACCEPTING.",
                        category="runtime",
                        retryable=True,
                        details={"run_id": run_id, "wave_id": ctx.wave_id, "state": ctx.state},
                    )
                requested_wave_id = str(args.get("wave_id") or "").strip()
                if requested_wave_id and requested_wave_id != ctx.wave_id:
                    raise ToolFailure(
                        "ORCHESTRATION_WAVE_MISMATCH",
                        "Final acceptance must target the current wave of the requested run.",
                        category="runtime",
                        retryable=False,
                        details={"run_id": run_id, "requested_wave_id": requested_wave_id, "current_wave_id": ctx.wave_id},
                    )
                proofs = self.orchestration_ledger.list_proofs(run_id, wave_id=ctx.wave_id)
                proof_fp = passed_proof_fingerprint(proofs)
                run = self.orchestration_ledger.get_run(run_id)
                run_metadata = run.get("metadata") if isinstance(run, dict) and isinstance(run.get("metadata"), dict) else {}
                run_workspace_identity = (
                    run_metadata.get("workspace_identity")
                    if isinstance(run_metadata.get("workspace_identity"), dict)
                    else {}
                )
                scope_root = self._workspace_root_for_identity(run_workspace_identity.get("root_id")) or self.workspace.root
                identity = self._orchestration_workspace_identity(str(scope_root))
                if run_workspace_identity:
                    self._assert_orchestration_workspace_scope(identity.get("workspace_identity") or {}, run_id=run_id)
                accepted_by = str((self._current_hub_client() or {}).get("client_id") or "ChatWeb Sol")
                accepted_files = _accepted_checkpoint_file_receipts(
                    scope_root,
                    self.orchestration_ledger,
                    state.get("modified_files"),
                    acceptance_files=acceptance_files,
                    run_id=run_id,
                    wave_id=ctx.wave_id,
                )
                explicit_acceptance_paths = (
                    [
                        str(item.get("path") or "")
                        for item in accepted_files.get("files", [])
                        if isinstance(item, dict)
                        and str(item.get("receipt_kind") or "") == "explicit_existing_file"
                        and str(item.get("path") or "")
                    ]
                    if accepted_files.get("source") == "explicit_acceptance_attestations"
                    else None
                )
                durable_mutation, _durable_paths = _durable_wave_acceptance_paths(
                    self.orchestration_ledger,
                    run_id,
                    ctx.wave_id,
                    workspace=scope_root,
                    explicit_attested_paths=explicit_acceptance_paths,
                    explicit_attestations=(
                        acceptance_files
                        if accepted_files.get("source") == "explicit_acceptance_attestations"
                        else None
                    ),
                )
                receipt_mutation = any(
                    isinstance(item, dict)
                    and str(item.get("receipt_kind") or "") in {
                        "explicit_existing_file",
                        "task_modified_file",
                        "durable_wave_patch_surface",
                    }
                    for item in (accepted_files.get("files") or [])
                )
                if (durable_mutation or receipt_mutation) and not has_passed_proof(proofs):
                    raise ToolFailure(
                        "ACCEPTANCE_PROOF_REQUIRED",
                        "Mutation-bearing acceptance requires at least one passed proof for this exact RUN/WAVE.",
                        category="runtime",
                        retryable=False,
                        details={"run_id": run_id, "wave_id": ctx.wave_id},
                    )
                proof_source_binding = {"required": False, "reason": "no_mutation"}
                if durable_mutation or receipt_mutation:
                    proof_source_binding = validate_passed_proof_source_binding(
                        scope_root,
                        proofs,
                        current_base_head=str(identity.get("base_head") or ""),
                        current_contract_fp=str(ctx.contract_fp or ""),
                        accepted_paths=[
                            str(item.get("path") or "")
                            for item in (accepted_files.get("files") or [])
                            if isinstance(item, dict) and str(item.get("path") or "")
                        ],
                    )
                coverage_manifest, criterion_dispositions = args.get("problem_coverage_manifest"), args.get("problem_criterion_dispositions")
                resolution_envelope = self._problem_resolution_envelope(args.get("problem_resolution_envelope"))
                controller_authority = self._problem_chatweb_controller_authority(run_id, controller=controller) if criterion_dispositions is not None else None
                try:
                    problem_outcome = self.orchestration_ledger.problem_prepare_eocl_outcome_claim(
                        run_id=run_id, wave_id=ctx.wave_id,
                        git_head=str(identity.get("base_head") or ""), worktree_fp=str(identity.get("worktree_fp") or ""),
                        proof_fingerprint=proof_fp, accepted_files=accepted_files, durable_mutation=durable_mutation,
                        coverage_manifest=coverage_manifest, criterion_dispositions=criterion_dispositions,
                        resolution_envelope=resolution_envelope,
                        controller_authority=controller_authority,
                    )
                except ProblemLineageError as exc:
                    missing = coverage_manifest is None and "coverage manifest" in str(exc)
                    missing_dispositions = criterion_dispositions is None and "dispositions must map" in str(exc)
                    code = "PRL_COVERAGE_MANIFEST_REQUIRED" if missing else "PRL_CRITERION_DISPOSITIONS_REQUIRED" if missing_dispositions else "PRL_OUTCOME_CLAIM_INVALID"
                    if resolution_envelope is None and "resolution envelope is required" in str(exc):
                        code = "PRL_RESOLUTION_ENVELOPE_REQUIRED"
                    raise ToolFailure(code, str(exc), category="validation") from exc
                if proofs and any(str(item.get("status") or "") == "passed" for item in proofs):
                    if self.orchestration_ledger.latest_quality_outcome(run_id) is None:
                        self.orchestration_ledger.record_quality_outcome(
                            run_id=run_id,
                            wave_id=ctx.wave_id,
                            outcome={"source": "accepted_proof_auto_v1", "oracle_pass": True},
                        )
                checkpoint_metadata = _accepted_checkpoint_metadata(identity, accepted_by=accepted_by, accepted_files=accepted_files)
                if proof_source_binding.get("required") is True:
                    checkpoint_metadata["proof_source_binding"] = proof_source_binding
                if problem_outcome.get("required"):
                    checkpoint_metadata.update({"problem_outcome_claim": problem_outcome["claim"], "problem_outcome_claim_sha256": problem_outcome["claim_sha256"]})
                _checkpoint_ctx, checkpoint_result = self.orchestration_control.checkpoint_with_receipt(
                    ctx,
                    reason="controller_acceptance" if controller else "chatweb_sol_acceptance",
                    git_head=str(identity.get("base_head") or ""),
                    proof_fingerprint=proof_fp,
                    status="accepted",
                    metadata=checkpoint_metadata,
                )
                self.orchestration_control.record_controller_acceptance_observations(
                    ctx,
                    controller_started_ms=controller_acceptance_started_ms,
                )
                checkpoint_id = str(checkpoint_result.get("checkpoint_id") or "")
                self._run_continuation_record_telemetry(
                    run_id, "accepted_checkpoint", outcome="succeeded", code="CONTROLLER_ACCEPTED", marker=checkpoint_id
                )
                record_accepted_remaining_criterion(
                    self,
                    run_id=run_id,
                    wave_id=ctx.wave_id,
                    coverage_manifest=coverage_manifest,
                    checkpoint_id=checkpoint_id,
                )
                problem_outcome_bridge = self._problem_reconcile_after_checkpoint(
                    run_id=run_id, wave_id=ctx.wave_id, checkpoint_id=checkpoint_id, identity=identity,
                ) if problem_outcome.get("required") else {"recorded": False, "reason": problem_outcome.get("reason")}
                self._project_orchestration(ctx, event="final_acceptance_recorded")
                accepted_state = self.task_state.update({
                    "status": "completed",
                    "current_step": "Completed - operator report required",
                    "next_step": "Present completion_report to the operator before starting another material wave.",
                    "failure": None,
                    "orchestration": ctx.projection(),
                }, event="task_accepted")
                orchestration_result = self._orchestration_result(ctx)
                return {
                    "accepted": True,
                    "state": accepted_state,
                    "orchestration": orchestration_result,
                    "completion_report": (orchestration_result or {}).get("completion_report"),
                    "problem_outcome_bridge": problem_outcome_bridge,
                    "reconciliation_status": problem_outcome_bridge.get("status"),
                }
            reason = str(args.get("reason", "")).strip()
            if not reason:
                raise ToolFailure("REJECTION_REASON_REQUIRED", "reason is required when action=reject.", category="validation")
            if ctx.state != "ACCEPTING":
                raise ToolFailure(
                    "FINAL_ACCEPTANCE_NOT_READY",
                    f"Run is in {ctx.state}, not ACCEPTING.",
                    category="runtime",
                    retryable=True,
                    details={"run_id": run_id, "wave_id": ctx.wave_id, "state": ctx.state},
                )
            self._require_hub_controller(run_id)
            self.orchestration_control.record_failure(ctx, "SOL_REJECTED", payload={"reason": reason})
            self._project_orchestration(ctx, event="final_acceptance_rejected")
            rejected_state = self.task_state.update({
                "status": "waiting",
                "current_step": "Replan required - operator report required",
                "next_step": "Present completion_report to the operator, then provide replan_reason and changed evidence/scope/strategy before another execution wave.",
                "failure": reason,
                "orchestration": ctx.projection(),
            }, event="task_rejected")
            orchestration_result = self._orchestration_result(ctx)
            return {
                "rejected": True,
                "state": rejected_state,
                "orchestration": orchestration_result,
                "completion_report": (orchestration_result or {}).get("completion_report"),
            }
        if action == "operation":
            operation_id = str(args.get("operation_id", "")).strip()
            if not operation_id:
                raise ToolFailure("INVALID_ARGUMENT", "operation_id is required when action=operation.", category="validation")
            with self.background_operations_lock:
                operation = self.background_operations.get(operation_id)
                if operation is not None and operation.get("workspace") != str(self.workspace.root):
                    operation = None
            if operation is None:
                durable = self.orchestration_ledger.get_background_operation(operation_id)
                if durable is None:
                    raise ToolFailure("NOT_FOUND", "Background operation was not found.", category="runtime", retryable=False)
                if durable.get("status") == "running":
                    durable = self.orchestration_ledger.finish_background_operation(
                        operation_id,
                        status="orphaned",
                        summary={"orphan_reason": "in_memory_handle_missing"},
                    ) or durable
                durable = dict(durable)
                durable["durable_only"] = True
                durable["requires_progress_report"] = False
                if durable.get("status") == "orphaned":
                    durable["message"] = (
                        "The MCP runtime that owned this operation is gone. Resume from durable task/proof/lane state; "
                        "do not assume the Python worker is still running."
                    )
                elif durable.get("status") == "completed":
                    durable["message"] = "The durable summary is available, but the prior runtime's full result payload is not retained."
                return {"state": self.task_state.get(), "background_operation": durable}
            wait_ms = min(max(int(args.get("wait_ms", 0)), 0), BACKGROUND_OPERATION_WAIT_MAX_MS)
            if wait_ms and not operation["event"].is_set():
                operation["event"].wait(wait_ms / 1000)
            snapshot = self._background_operation_snapshot(operation, include_result=True)
            if snapshot["status"] == "running":
                snapshot["message"] = "Operation is still running. Report progress to the user before waiting again."
            return {"state": self.task_state.get(), "background_operation": snapshot}
        if action == "history":
            return {"tasks": self.task_state.history(int(args.get("limit", 20)))}
        if action == "clear":
            self._require_operator_report_ack("clearing the current task")
            self._abort_task_orchestration(self.task_state.get(), reason="task_cleared")
            return {"state": self.task_state.clear(), "cleared": True}
        if action == "start":
            objective = str(args.get("objective", "")).strip()
            if not objective:
                raise ToolFailure("INVALID_ARGUMENT", "objective is required when action=start.", category="validation")
            self._require_operator_report_ack("starting a new task")
            self._abort_task_orchestration(self.task_state.get(), reason="task_replaced")
            changes = {
                "objective": objective,
                "steps": args.get("steps", []),
                "current_step": args.get("current_step", ""),
                "next_step": args.get("next_step", ""),
                "status": "active",
                "failure": None,
                "new_task": True,
            }
            return {"state": self.task_state.update(changes, event="task_started")}
        if action == "update":
            payload = args.get("payload")
            if isinstance(payload, dict) and payload.get("extension") == "operator_report_ack_v1":
                unexpected = sorted(set(payload) - {"extension", "report_id"})
                if unexpected:
                    raise ToolFailure(
                        "OPERATOR_REPORT_ACK_INVALID",
                        "operator_report_ack_v1 payload contains unsupported fields.",
                        category="validation",
                        details={"unsupported": unexpected},
                    )
                report_id = str(payload.get("report_id") or "").strip()
                if not report_id:
                    raise ToolFailure(
                        "OPERATOR_REPORT_ACK_INVALID",
                        "operator_report_ack_v1 payload.report_id is required.",
                        category="validation",
                    )
                try:
                    state = self.task_state.ack_completion_report(report_id)
                except ValueError as exc:
                    raise ToolFailure(
                        "OPERATOR_REPORT_ACK_INVALID",
                        str(exc),
                        category="runtime",
                        retryable=True,
                        details={"report_id": report_id},
                    ) from exc
                return {"state": state, "acknowledged": True, "report_id": report_id}
            if isinstance(payload, dict) and payload.get("extension") == "solution_shadow_v1":
                unexpected = sorted(set(payload) - {"extension", "recommendation"})
                if unexpected:
                    raise ToolFailure(
                        "SOLUTION_SHADOW_EXTENSION_INVALID",
                        "solution_shadow_v1 payload contains unsupported fields.",
                        category="validation",
                        details={"unsupported": unexpected},
                    )
                recommendation = payload.get("recommendation")
                if not isinstance(recommendation, dict):
                    raise ToolFailure(
                        "SOLUTION_SHADOW_INVALID",
                        "solution_shadow_v1 payload.recommendation must be an object.",
                        category="validation",
                    )
                return self._solution_shadow_control(
                    args,
                    recommendation,
                    transport="frozen_chatgpt_schema_extension_v1",
                )
            self._require_operator_report_ack("updating the task")
            changes = {key: args[key] for key in ("objective", "steps", "current_step", "next_step", "status", "failure", "complete_step_ids") if key in args}
            return {"state": self.task_state.update(changes)}
        if action == "pause":
            state = self.task_state.pause(str(args.get("reason", "Paused by user")))
            current = state.get("current_command") if isinstance(state, dict) else None
            if isinstance(current, dict) and current.get("session_id"):
                try:
                    self.kill_session({"session_id": str(current["session_id"]), "signal": "TERM", "wait_ms": 1000})
                except ToolFailure:
                    pass
            return {"state": self.task_state.get(), "paused": True}
        if action == "resume":
            self._require_operator_report_ack("resuming the task")
            return {"state": self.task_state.resume(str(args.get("next_step", "")))}
        if action == "stop":
            explicit_run_id = str(args.get("run_id") or "").strip()
            if explicit_run_id:
                ctx = self.orchestration_control.snapshot(explicit_run_id)
                if ctx is None:
                    raise ToolFailure("NOT_FOUND", "Orchestration run was not found.", category="runtime", retryable=False)
                self._require_hub_controller(explicit_run_id)
                if ctx.state not in {"CHECKPOINTED", "BLOCKED", "ABORTED"}:
                    try:
                        self.orchestration_control.transition(ctx, "ABORTED", reason=str(args.get("reason") or "task_stopped"))
                    except OrchestrationControlError as exc:
                        raise ToolFailure("ORCHESTRATION_ABORT_FAILED", str(exc), category="runtime", retryable=False, details={"run_id": explicit_run_id, "state": ctx.state, **getattr(exc, "details", {})}) from exc
                current_state = self.task_state.get()
                current_projection = current_state.get("orchestration") if isinstance(current_state.get("orchestration"), dict) else {}
                orchestration_result = self._orchestration_result(ctx)
                return {
                    "state": current_state,
                    "stopped": ctx.state == "ABORTED",
                    "already_terminal": ctx.state != "ABORTED",
                    "target_run_id": explicit_run_id,
                    "detached": str(current_projection.get("run_id") or "") != explicit_run_id,
                    "orchestration": orchestration_result,
                    "completion_report": (orchestration_result or {}).get("completion_report"),
                }
            previous = self.task_state.get()
            aborted_projection = self._abort_task_orchestration(previous, reason="task_stopped")
            changes = {
                "status": "stopped",
                "failure": str(args.get("reason", "Stopped by user")),
                "next_step": str(args.get("next_step", "Resume or start a new task.")),
            }
            if aborted_projection is not None:
                changes["orchestration"] = aborted_projection
            state = self.task_state.update(changes, event="task_stopped")
            current = state.get("current_command") if isinstance(state, dict) else None
            if isinstance(current, dict) and current.get("session_id"):
                try:
                    self.kill_session({"session_id": str(current["session_id"]), "signal": "TERM", "wait_ms": 1000})
                except ToolFailure:
                    pass
            return {"state": state, "stopped": True}
        raise ToolFailure("INVALID_ARGUMENT", f"Unknown task action: {action}", category="validation")
