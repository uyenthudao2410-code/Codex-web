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
from .codex_bridge import CodexBridgeError
from .errors import ToolFailure
from .fs_utils import is_relative_to
from .orchestration_control import OrchestrationControlError
from .solution_economics import record_solution_shadow, solution_shadow_run_report


SUPERVISOR_RESTART_TICKET_TTL_MS = 60_000
SUPERVISOR_RESTART_RESPONSE_GRACE_MS = 2_000
BACKGROUND_OPERATION_WAIT_MAX_MS = 60_000
MAX_ACCEPTED_FILE_RECEIPTS = 256
MAX_ACCEPTED_RECEIPT_FILE_BYTES = 16 * 1024 * 1024
MAX_ACCEPTED_RECEIPT_TOTAL_BYTES = 64 * 1024 * 1024


def _accepted_file_receipts(workspace: Path, modified_files: Any) -> dict[str, Any]:
    """Build content-free, bounded file receipts for one final acceptance."""
    root = workspace.resolve()
    raw_items = list(modified_files or []) if isinstance(modified_files, list) else []
    normalized: list[str] = []
    incomplete_reasons: set[str] = set()
    for item in raw_items:
        raw = item.get("path") if isinstance(item, dict) else item
        value = str(raw or "").strip().replace("\\", "/")
        while value.startswith("./"):
            value = value[2:]
        if not value or value.startswith(".coding-tools/"):
            continue
        relative = Path(value)
        if relative.is_absolute() or ".." in relative.parts:
            incomplete_reasons.add("unsafe_path")
            continue
        target = (root / relative).resolve(strict=False)
        if not is_relative_to(target, root):
            incomplete_reasons.add("outside_workspace")
            continue
        portable = relative.as_posix()
        if portable not in normalized:
            normalized.append(portable)
    if len(normalized) > MAX_ACCEPTED_FILE_RECEIPTS:
        incomplete_reasons.add("too_many_files")
        normalized = normalized[:MAX_ACCEPTED_FILE_RECEIPTS]

    receipts: list[dict[str, Any]] = []
    total_bytes = 0
    for portable in normalized:
        target = (root / Path(portable)).resolve(strict=False)
        if not target.exists():
            receipts.append({"path": portable, "state": "missing", "sha256": None, "size_bytes": 0})
            continue
        if not target.is_file():
            incomplete_reasons.add("non_file")
            continue
        try:
            size = int(target.stat().st_size)
        except OSError:
            incomplete_reasons.add("stat_failed")
            continue
        if size < 0 or size > MAX_ACCEPTED_RECEIPT_FILE_BYTES or total_bytes + size > MAX_ACCEPTED_RECEIPT_TOTAL_BYTES:
            incomplete_reasons.add("byte_limit")
            continue
        digest = hashlib.sha256()
        try:
            with target.open("rb") as handle:
                while chunk := handle.read(1024 * 1024):
                    digest.update(chunk)
        except OSError:
            incomplete_reasons.add("read_failed")
            continue
        total_bytes += size
        receipts.append({"path": portable, "state": "file", "sha256": digest.hexdigest(), "size_bytes": size})
    return {
        "schema_version": 1,
        "complete": not incomplete_reasons and len(receipts) == len(normalized),
        "count": len(receipts),
        "total_bytes": total_bytes,
        "files": receipts,
        "incomplete_reasons": sorted(incomplete_reasons),
    }

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


class CoordinationMixin:
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

    def activation_preflight(
        self,
        *,
        operation_id: str = "",
        expires_at_unix_ms: int = 0,
        allow_acceptance_pending: bool = False,
        prepare: bool = False,
        ignore_active_tool_calls: int = 0,
    ) -> dict[str, Any]:
        """Return canonical restart safety and optionally fence new tool admission."""
        with self.activation_lock:
            self._activation_cleanup_locked()
            now_ms = int(time.time() * 1000)
            if prepare:
                allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")
                if not (16 <= len(operation_id) <= 128) or any(char not in allowed for char in operation_id):
                    raise ToolFailure("INVALID_OPERATION_ID", "Invalid activation operation_id.", category="validation")
                if expires_at_unix_ms <= now_ms or expires_at_unix_ms > now_ms + 60_000:
                    raise ToolFailure("ACTIVATION_REQUEST_EXPIRED", "Activation expiry must be within the next 60 seconds.", category="validation")
            if self.activation_fence and str(self.activation_fence.get("operation_id") or "") != operation_id:
                return {
                    "safe": False,
                    "code": "RUNTIME_BUSY",
                    "reason": "another_activation_pending",
                    "operation_id": str(self.activation_fence.get("operation_id") or ""),
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
                active_run = self.orchestration_ledger.current_active_run()
            except (sqlite3.Error, OSError) as exc:
                return {
                    "safe": False,
                    "code": "ORCHESTRATION_STATE_UNCERTAIN",
                    "reason": "activation_state_probe_failed",
                    "error_type": type(exc).__name__,
                    "counts": counts,
                }
            orchestration_state = "IDLE"
            run_id = ""
            acceptance_pending = False
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
                else:
                    return {
                        "safe": False,
                        "code": "RUNTIME_BUSY",
                        "reason": "orchestration_active",
                        "run_id": run_id,
                        "orchestration_state": orchestration_state,
                        "counts": counts,
                    }

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
                "reason": "idle" if not acceptance_pending else "acceptance_state_is_durable",
                "run_id": run_id,
                "orchestration_state": orchestration_state,
                "acceptance_pending": acceptance_pending,
                "counts": counts,
                "process_instance_id": self.process_instance_id,
                "server_instance_id": self.server_instance_id,
                "workspace": str(self.workspace.root),
            }
            if prepare:
                self.activation_fence = {
                    "operation_id": operation_id,
                    "expires_at_unix_ms": expires_at_unix_ms,
                    "prepared_at_unix_ms": now_ms,
                }
                result["fenced"] = True
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
            if request_path.is_file():
                try:
                    existing = json.loads(request_path.read_text(encoding="utf-8"))
                except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                    existing = {}
                if (
                    isinstance(existing, dict)
                    and existing.get("action") == "restart"
                    and str(existing.get("workspace") or "").casefold() == str(self.workspace.root).casefold()
                    and int(existing.get("expires_at_unix_ms") or 0) > now_ms
                    and str(existing.get("ticket_id") or "").strip()
                ):
                    return {
                        "accepted": True,
                        "already_pending": True,
                        "restart_ticket": str(existing["ticket_id"]),
                        "expected_disconnect": True,
                        "supervisor": "electron",
                        "not_before_unix_ms": int(existing.get("not_before_unix_ms") or 0),
                        "expires_at_unix_ms": int(existing.get("expires_at_unix_ms") or 0),
                        "recommended_next_action": "Allow the Electron supervisor to consume the pending ticket, then reconnect and verify runtime instance ids changed.",
                    }

            ticket_id = secrets.token_urlsafe(12)
            preflight = self.activation_preflight(
                operation_id=ticket_id,
                expires_at_unix_ms=now_ms + SUPERVISOR_RESTART_TICKET_TTL_MS,
                allow_acceptance_pending=args.get("allow_acceptance_pending") is True,
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
            ticket = {
                "version": 1,
                "action": "restart",
                "ticket_id": ticket_id,
                "requested_at": datetime.now(timezone.utc).isoformat(),
                "requested_at_unix_ms": now_ms,
                "not_before_unix_ms": now_ms + SUPERVISOR_RESTART_RESPONSE_GRACE_MS,
                "expires_at_unix_ms": now_ms + SUPERVISOR_RESTART_TICKET_TTL_MS,
                "workspace": str(self.workspace.root),
                "process_instance_id": self.process_instance_id,
                "server_instance_id": self.server_instance_id,
                "tool_contract_sha256": self.tool_contract["sha256"],
                "reason": str(args.get("reason") or "User requested runtime restart")[:500],
            }
            temporary = request_path.with_name(f".{request_path.name}.{ticket_id}.tmp")
            try:
                temporary.write_text(json.dumps(ticket, ensure_ascii=False, sort_keys=True), encoding="utf-8")
                os.replace(temporary, request_path)
            except OSError as exc:
                self.cancel_activation(ticket_id)
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass
                raise ToolFailure(
                    "SUPERVISOR_REQUEST_FAILED",
                    "Could not enqueue the Electron supervisor restart request.",
                    category="runtime",
                    retryable=True,
                    details={"error": str(exc)},
                ) from exc
            return {
                "accepted": True,
                "already_pending": False,
                "restart_ticket": ticket_id,
                "expected_disconnect": True,
                "supervisor": "electron",
                "not_before_unix_ms": ticket["not_before_unix_ms"],
                "expires_at_unix_ms": ticket["expires_at_unix_ms"],
                "recommended_next_action": "The Electron supervisor will restart after this tool response has time to flush. Reconnect, then verify process_instance_id and server_instance_id changed.",
            }

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

    def _solution_shadow_control(
        self,
        args: dict[str, Any],
        recommendation: Any,
        *,
        transport: str,
    ) -> dict[str, Any]:
        _state, projection, run_id, wave_id = self._coordination_ids(args)
        if not run_id:
            raise ToolFailure("ORCHESTRATION_RUN_NOT_FOUND", "No orchestration run is available for solution shadow evidence.", category="not_found")
        recording = None
        context_recovered = False
        if recommendation is not None:
            if not isinstance(recommendation, dict):
                raise ToolFailure("SOLUTION_SHADOW_INVALID", "solution shadow recommendation must be an object.", category="validation")
            projected_run = str(projection.get("run_id") or "").strip()
            projected_wave = str(projection.get("wave_id") or "").strip()
            if run_id != projected_run or not wave_id or wave_id != projected_wave:
                explicit_run = str(args.get("run_id") or "").strip()
                explicit_wave = str(args.get("wave_id") or "").strip()
                ctx = self.orchestration_control.snapshot(run_id) if explicit_run and explicit_wave else None
                if (
                    ctx is None
                    or ctx.run_id != explicit_run
                    or ctx.wave_id != explicit_wave
                    or ctx.state not in {"PREFLIGHT", "READY"}
                ):
                    raise ToolFailure(
                        "SOLUTION_SHADOW_CONTEXT_MISMATCH",
                        "Solution shadow recording requires the current task-projected run/wave or an explicit current PREFLIGHT/READY run/wave.",
                        category="runtime",
                        retryable=True,
                        details={
                            "run_id": run_id,
                            "wave_id": wave_id,
                            "projected_run_id": projected_run,
                            "projected_wave_id": projected_wave,
                            "explicit_context_recovery": bool(explicit_run and explicit_wave),
                        },
                    )
                self._require_hub_controller(run_id)
                context_recovered = True
            else:
                ctx = self.orchestration_control.snapshot(run_id)
                self._require_hub_controller(run_id)
            try:
                recording = record_solution_shadow(
                    self.orchestration_ledger,
                    run_id=run_id,
                    wave_id=wave_id,
                    recommendation=recommendation,
                )
            except ValueError as exc:
                raise ToolFailure("SOLUTION_SHADOW_INVALID", str(exc), category="validation", retryable=False) from exc
            if context_recovered and ctx is not None:
                self._project_orchestration(ctx, event="solution_shadow_context_recovered")
        return {
            "recording": recording,
            "solution_shadow": solution_shadow_run_report(self.orchestration_ledger, run_id),
            "transport": transport,
            "context_recovered": context_recovered,
            "production_behavior_changed": False,
        }

    def task_control(self, args: dict[str, Any]) -> dict[str, Any]:
        action = str(args.get("action", "get")).lower()
        if action == "restart_runtime":
            return self._enqueue_runtime_restart(args)
        self._reconcile_task_orchestration_projection()
        if action == "get":
            # The stream is not the source of truth after reconnect.  Repair
            # the compact view from the SQLite ledger before returning status.
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
            return {
                "state": self.task_state.get(),
                "resources": self.execution_resource_governor.snapshot(),
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
            if current_report_id and message_id == current_report_id:
                try:
                    acknowledged_state = self.task_state.ack_completion_report(message_id)
                except ValueError as exc:
                    raise ToolFailure(
                        "OPERATOR_REPORT_ACK_INVALID",
                        str(exc),
                        category="runtime",
                        retryable=True,
                        details={"report_id": message_id},
                    ) from exc
                return {
                    "acknowledged": True,
                    "acknowledgement_type": "operator_completion_report",
                    "report_id": message_id,
                    "state": acknowledged_state,
                }
            raise ToolFailure("MESSAGE_NOT_FOUND", "The coordination message or current completion report was not found.", category="not_found")
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
            pending_messages = self.orchestration_ledger.list_coordination_messages(
                run_id=run_id,
                status="pending",
                limit=50,
            )
            active_lanes = self.orchestration_ledger.list_agent_lanes(run_id=run_id)
            augmented = dict(payload)
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
            return {
                "recorded": bool(recorded.get("recorded")),
                "observation_span": recorded,
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
                controller = self._require_hub_controller(run_id)
                if ctx.state != "ACCEPTING":
                    raise ToolFailure(
                        "FINAL_ACCEPTANCE_NOT_READY",
                        f"Run is in {ctx.state}, not ACCEPTING.",
                        category="runtime",
                        retryable=True,
                        details={"run_id": run_id, "wave_id": ctx.wave_id, "state": ctx.state},
                    )
                proofs = self.orchestration_ledger.list_proofs(run_id, wave_id=ctx.wave_id)
                proof_fp = hashlib.sha256(
                    "|".join(f"{item['proof_id']}:{item['input_fingerprint']}" for item in proofs).encode("utf-8")
                ).hexdigest() if proofs else ""
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
                accepted_files = _accepted_file_receipts(scope_root, state.get("modified_files"))
                if proofs and any(str(item.get("status") or "") == "passed" for item in proofs):
                    if self.orchestration_ledger.latest_quality_outcome(run_id) is None:
                        self.orchestration_ledger.record_quality_outcome(
                            run_id=run_id,
                            wave_id=ctx.wave_id,
                            outcome={"source": "accepted_proof_auto_v1", "oracle_pass": True},
                        )
                self.orchestration_control.checkpoint(ctx, reason="controller_acceptance" if controller else "chatweb_sol_acceptance")
                self.orchestration_ledger.record_checkpoint(
                    run_id=run_id,
                    wave_id=ctx.wave_id,
                    git_head=str(identity.get("base_head") or ""),
                    proof_fingerprint=proof_fp,
                    status="accepted",
                    metadata={
                        "accepted_by": accepted_by,
                        "worktree_fp": identity.get("worktree_fp"),
                        "workspace_identity": dict(identity.get("workspace_identity") or {}),
                        "accepted_files": accepted_files,
                    },
                )
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
