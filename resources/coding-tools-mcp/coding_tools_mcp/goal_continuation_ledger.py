from __future__ import annotations

"""Durable Goal-episode continuation ledger operations."""

import hashlib
import json
import sqlite3
from typing import Any

from .continuation_contract import (
    RUN_CONTINUATION_SCHEMA_VERSION,
    RunContinuationError,
    _bounded,
    _canonical_json,
    _now_ms,
    _policy_projection,
    _require_opaque,
    _require_sha256,
    _utc_now,
)
from .controller_reattach import run_binding_from_metadata as _controller_run_binding_from_metadata

GOAL_CONTINUATION_NO_PROGRESS = "GOAL_CONTINUATION_NO_PROGRESS"


class GoalContinuationLedgerMixin:
    @staticmethod
    def _goal_continuation_row(row: sqlite3.Row) -> dict[str, Any]:
        policy = json.loads(str(row["policy_json"] or "{}"))
        return {
            "episode_id": str(row["episode_id"]),
            "workspace_id": str(row["workspace_id"]),
            "problem_id": str(row["problem_id"]),
            "problem_revision": int(row["problem_revision"]),
            "policy_sha256": str(row["policy_sha256"]),
            "issuer_receipt_sha256": str(row["issuer_receipt_sha256"]),
            "enabled": bool(row["enabled"]),
            "pause_reason": str(row["pause_reason"]),
            "revoked_at": row["revoked_at"],
            "remaining_decision_turns": int(row["remaining_decision_turns"]),
            "remaining_patch_attempts": int(row["remaining_patch_attempts"]),
            "no_progress_count": int(row["no_progress_count"]),
            "expires_at_unix_ms": int(row["expires_at_unix_ms"]),
            "created_at": str(row["created_at"]),
            "updated_at": str(row["updated_at"]),
            "policy": policy,
        }

    def _goal_continuation_get_raw(
        self,
        episode_id: str,
        *,
        connection: sqlite3.Connection | None = None,
    ) -> dict[str, Any] | None:
        episode = _require_sha256(episode_id, "episode_id")
        if connection is not None:
            row = connection.execute(
                "SELECT * FROM goal_continuations WHERE episode_id=?", (episode,)
            ).fetchone()
            return self._goal_continuation_row(row) if row is not None else None
        with self._lock, self._connect() as connection:
            self._run_continuation_ensure_schema(connection)
            row = connection.execute(
                "SELECT * FROM goal_continuations WHERE episode_id=?", (episode,)
            ).fetchone()
        return self._goal_continuation_row(row) if row is not None else None

    def get_goal_continuation(self, episode_id: str) -> dict[str, Any] | None:
        record = self._goal_continuation_get_raw(episode_id)
        if record is None:
            return None
        record["policy"] = _policy_projection(record["policy"])
        return record

    @staticmethod
    def _assert_goal_continuation_row(
        record: dict[str, Any] | None,
        *,
        episode_id: str,
        now_unix_ms: int | None = None,
    ) -> dict[str, Any]:
        if record is None:
            raise RunContinuationError(
                "GOAL_CONTINUATION_GRANT_REQUIRED",
                "No durable Goal-episode continuation authority exists.",
            )
        now_ms = _now_ms() if now_unix_ms is None else int(now_unix_ms)
        if record["revoked_at"]:
            raise RunContinuationError(
                "GOAL_CONTINUATION_REVOKED",
                "The Goal-episode continuation authority is revoked.",
                details={"episode_id": episode_id},
            )
        if not record["enabled"]:
            reason = str(record.get("pause_reason") or "GOAL_CONTINUATION_PAUSED")
            code = GOAL_CONTINUATION_NO_PROGRESS if reason == GOAL_CONTINUATION_NO_PROGRESS else "GOAL_CONTINUATION_PAUSED"
            raise RunContinuationError(
                code,
                "The Goal-episode continuation authority is paused.",
                details={"episode_id": episode_id, "pause_reason": reason},
            )
        if now_ms >= int(record["expires_at_unix_ms"]):
            raise RunContinuationError(
                "GOAL_CONTINUATION_EXPIRED",
                "The Goal-episode continuation authority has expired.",
                details={"episode_id": episode_id},
            )
        return record

    def issue_goal_continuation(
        self,
        *,
        policy: dict[str, Any],
        issuer_receipt_sha256: str,
        now_unix_ms: int | None = None,
    ) -> dict[str, Any]:
        if str(policy.get("scope_kind") or "") != "goal_episode":
            raise RunContinuationError(
                "GOAL_CONTINUATION_POLICY_INVALID",
                "Goal continuation issuance requires a goal_episode policy.",
            )
        episode = _require_sha256(policy.get("episode_id"), "episode_id")
        receipt = _require_sha256(issuer_receipt_sha256, "issuer_receipt_sha256")
        origin_run = _require_opaque(policy.get("origin_run_id"), "origin_run_id")
        controller_generation = policy.get("controller_generation")
        if isinstance(controller_generation, bool) or not isinstance(controller_generation, int) or controller_generation < 1:
            raise RunContinuationError(
                "GOAL_CONTINUATION_CONTROLLER_INVALID",
                "Goal continuation authority requires a positive controller generation.",
            )
        policy_json = _canonical_json(policy)
        policy_sha = hashlib.sha256(policy_json.encode("utf-8")).hexdigest()
        now_ms = _now_ms() if now_unix_ms is None else int(now_unix_ms)
        expires_at = now_ms + int(policy["max_duration_seconds"]) * 1_000
        now = _utc_now()
        with self._lock, self._connect() as connection:
            self._run_continuation_ensure_schema(connection)
            self._controller_continuity_ensure_schema(connection)
            connection.execute("BEGIN IMMEDIATE")
            self._controller_assert_goal_run_precondition(
                connection,
                {
                    "workspace_id": str(policy["workspace_id"]),
                    "problem_id": str(policy["problem_id"]),
                    "problem_revision": int(policy["problem_revision"]),
                    "expected_generation": int(controller_generation),
                    "owner_client_id": str(policy["controller_owner_client_id"]),
                    "controller_endpoint_id": str(policy["controller_endpoint_id"]),
                },
            )
            origin = connection.execute(
                "SELECT status FROM runs WHERE run_id=?", (origin_run,)
            ).fetchone()
            if origin is None or str(origin["status"] or "") != "active":
                raise RunContinuationError(
                    "GOAL_CONTINUATION_ORIGIN_RUN_INVALID",
                    "Goal continuation authority requires an active origin RUN.",
                )
            existing_row = connection.execute(
                "SELECT * FROM goal_continuations WHERE episode_id=?", (episode,)
            ).fetchone()
            if existing_row is not None:
                existing = self._goal_continuation_row(existing_row)
                if (
                    existing["enabled"]
                    and not existing["revoked_at"]
                    and existing["policy_sha256"] == policy_sha
                    and existing["issuer_receipt_sha256"] == receipt
                ):
                    connection.commit()
                    existing["policy"] = _policy_projection(existing["policy"])
                    return {"status": "GRANTED", "idempotent": True, "goal_continuation": existing}
                raise RunContinuationError(
                    "GOAL_CONTINUATION_GRANT_CONFLICT",
                    "The content-addressed Goal episode already exists with different or terminal authority.",
                    details={"episode_id": episode},
                )
            competing = connection.execute(
                """SELECT episode_id FROM goal_continuations
                   WHERE workspace_id=? AND problem_id=? AND problem_revision=?
                     AND enabled=1 AND revoked_at IS NULL""",
                (policy["workspace_id"], policy["problem_id"], int(policy["problem_revision"])),
            ).fetchone()
            if competing is not None:
                raise RunContinuationError(
                    "GOAL_CONTINUATION_GRANT_CONFLICT",
                    "Another active Goal continuation already owns this exact Problem Revision.",
                    details={"episode_id": str(competing["episode_id"])},
                )
            connection.execute(
                """INSERT INTO goal_continuations(
                       episode_id,workspace_id,problem_id,problem_revision,policy_json,policy_sha256,
                       issuer_receipt_sha256,enabled,pause_reason,revoked_at,
                       remaining_decision_turns,remaining_patch_attempts,no_progress_count,
                       expires_at_unix_ms,created_at,updated_at
                   ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    episode, policy["workspace_id"], policy["problem_id"], int(policy["problem_revision"]),
                    policy_json, policy_sha, receipt, 1, "", None,
                    int(policy["max_decision_turns"]), int(policy["max_patch_attempts"]), 0,
                    expires_at, now, now,
                ),
            )
            self._append_run_continuation_event(
                connection,
                run_id=origin_run,
                event_type="goal_continuation_granted",
                payload={
                    "episode_id": episode,
                    "policy_sha256": policy_sha,
                    "controller_generation": int(controller_generation),
                    "expires_at_unix_ms": expires_at,
                },
            )
            row = connection.execute(
                "SELECT * FROM goal_continuations WHERE episode_id=?", (episode,)
            ).fetchone()
            connection.commit()
        assert row is not None
        result = self._goal_continuation_row(row)
        result["policy"] = _policy_projection(result["policy"])
        return {"status": "GRANTED", "idempotent": False, "goal_continuation": result}

    def set_goal_continuation_state(
        self,
        *,
        episode_id: str,
        action: str,
        reason: str = "",
    ) -> dict[str, Any]:
        episode = _require_sha256(episode_id, "episode_id")
        operation = _bounded(action, 32).lower()
        if operation not in {"pause", "resume", "revoke"}:
            raise RunContinuationError(
                "GOAL_CONTINUATION_CONTROL_INVALID",
                "Unsupported Goal continuation control action.",
            )
        bounded_reason = _bounded(reason, 512)
        now = _utc_now()
        with self._lock, self._connect() as connection:
            self._run_continuation_ensure_schema(connection)
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM goal_continuations WHERE episode_id=?", (episode,)
            ).fetchone()
            record = self._goal_continuation_row(row) if row is not None else None
            if record is None:
                raise RunContinuationError(
                    "GOAL_CONTINUATION_GRANT_REQUIRED",
                    "No Goal continuation authority exists for this episode.",
                )
            if operation == "resume" and record["revoked_at"]:
                raise RunContinuationError(
                    "GOAL_CONTINUATION_REVOKED",
                    "A revoked Goal continuation cannot be resumed.",
                )
            enabled = 1 if operation == "resume" else 0
            revoked_at = now if operation == "revoke" else record["revoked_at"]
            pause_reason = "" if operation == "resume" else (bounded_reason or operation)
            connection.execute(
                "UPDATE goal_continuations SET enabled=?,pause_reason=?,revoked_at=?,updated_at=? WHERE episode_id=?",
                (enabled, pause_reason, revoked_at, now, episode),
            )
            origin_run = str(record["policy"].get("origin_run_id") or "")
            if origin_run:
                self._append_run_continuation_event(
                    connection,
                    run_id=origin_run,
                    event_type=("goal_continuation_revoked" if operation == "revoke" else f"goal_continuation_{operation}d"),
                    payload={"episode_id": episode, "reason": pause_reason},
                )
            updated = connection.execute(
                "SELECT * FROM goal_continuations WHERE episode_id=?", (episode,)
            ).fetchone()
            connection.commit()
        assert updated is not None
        result = self._goal_continuation_row(updated)
        result["policy"] = _policy_projection(result["policy"])
        return result

    def materialize_goal_continuation(
        self,
        *,
        run_id: str,
        episode_id: str,
        grant_wave_id: str = "",
        now_unix_ms: int | None = None,
    ) -> dict[str, Any]:
        normalized_run = _require_opaque(run_id, "run_id")
        episode = _require_sha256(episode_id, "episode_id")
        wave = _require_opaque(grant_wave_id, "grant_wave_id") if grant_wave_id else ""
        now_ms = _now_ms() if now_unix_ms is None else int(now_unix_ms)
        now = _utc_now()
        with self._lock, self._connect() as connection:
            self._run_continuation_ensure_schema(connection)
            self._controller_continuity_ensure_schema(connection)
            connection.execute("BEGIN IMMEDIATE")
            goal_row = connection.execute(
                "SELECT * FROM goal_continuations WHERE episode_id=?", (episode,)
            ).fetchone()
            goal = self._assert_goal_continuation_row(
                self._goal_continuation_row(goal_row) if goal_row is not None else None,
                episode_id=episode,
                now_unix_ms=now_ms,
            )
            goal_policy = goal["policy"]
            self._controller_assert_goal_run_precondition(
                connection,
                {
                    "workspace_id": str(goal_policy["workspace_id"]),
                    "problem_id": str(goal_policy["problem_id"]),
                    "problem_revision": int(goal_policy["problem_revision"]),
                    "expected_generation": int(goal_policy["controller_generation"]),
                    "owner_client_id": str(goal_policy["controller_owner_client_id"]),
                    "controller_endpoint_id": str(goal_policy["controller_endpoint_id"]),
                },
            )
            run = connection.execute(
                "SELECT status,metadata_json FROM runs WHERE run_id=?", (normalized_run,)
            ).fetchone()
            if run is None or str(run["status"] or "") != "active":
                raise RunContinuationError(
                    "RUN_CONTINUATION_RUN_NOT_ACTIVE",
                    "Goal continuation materialization requires an active child RUN.",
                )
            try:
                metadata = json.loads(str(run["metadata_json"] or "{}"))
            except (TypeError, json.JSONDecodeError):
                metadata = {}
            binding = _controller_run_binding_from_metadata(metadata)
            if not isinstance(binding, dict) or (
                str(binding.get("workspace_id") or "") != str(goal_policy["workspace_id"])
                or str(binding.get("problem_id") or "") != str(goal_policy["problem_id"])
                or int(binding.get("problem_revision") or 0) != int(goal_policy["problem_revision"])
            ):
                raise RunContinuationError(
                    "GOAL_CONTINUATION_CHILD_BINDING_MISMATCH",
                    "Child RUN must bind the exact Goal workspace and Problem Revision before materialization.",
                )
            child_policy = {
                "schema_version": RUN_CONTINUATION_SCHEMA_VERSION,
                "run_id": normalized_run,
                "parent_episode_id": episode,
                "workspace_id": goal_policy["workspace_id"],
                "problem_id": goal_policy["problem_id"],
                "problem_revision": int(goal_policy["problem_revision"]),
                "contract_fingerprint": goal_policy["contract_fingerprint"],
                "tool_contract_sha256": goal_policy["tool_contract_sha256"],
                "runtime_behavior_fingerprint": goal_policy["runtime_behavior_fingerprint"],
                "activation_epoch_id": goal_policy["activation_epoch_id"],
                "activation_admission": goal_policy["activation_admission"],
                "issuer_client_id": goal_policy["issuer_client_id"],
                "grant_wave_id": wave,
                "route": goal_policy["route"],
                "profile": goal_policy["profile"],
                "acceptance_mode": goal_policy["acceptance_mode"],
                "restart_policy": goal_policy["restart_policy"],
                "read_paths": list(goal_policy["read_paths"]),
                "write_paths": list(goal_policy["write_paths"]),
                "protected_paths": list(goal_policy["protected_paths"]),
                "approved_checks": list(goal_policy["approved_checks"]),
                "max_duration_seconds": int(goal_policy["max_duration_seconds"]),
                "max_decision_turns": int(goal_policy["max_decision_turns"]),
                "max_patch_attempts": int(goal_policy["max_patch_attempts"]),
            }
            child_policy_json = _canonical_json(child_policy)
            child_policy_sha = hashlib.sha256(child_policy_json.encode("utf-8")).hexdigest()
            existing_row = connection.execute(
                "SELECT * FROM run_continuations WHERE run_id=?", (normalized_run,)
            ).fetchone()
            if existing_row is not None:
                existing = self._run_continuation_row(existing_row)
                if existing["parent_episode_id"] == episode and existing["enabled"] and not existing["revoked_at"]:
                    connection.commit()
                    existing["policy"] = _policy_projection(existing["policy"])
                    return {"status": "MATERIALIZED", "idempotent": True, "continuation": existing}
                raise RunContinuationError(
                    "RUN_CONTINUATION_GRANT_CONFLICT",
                    "Child RUN already has different continuation authority.",
                )
            connection.execute(
                """INSERT INTO run_continuations(
                       run_id,parent_episode_id,workspace_id,problem_id,problem_revision,policy_json,policy_sha256,issuer_receipt_sha256,
                       policy_revision,enabled,pause_reason,revoked_at,driver_generation,claimed_runtime_instance,
                       claim_expires_at_unix_ms,next_action_seq,consumed_event_seq,pending_action_id,pending_evidence_hash,pending_evidence_paths_json,pending_replan_json,pending_dispatch_action_id,pending_job_id,pending_patch_action_id,lane_id,
                       thread_id,thread_session_id,last_turn_id,remaining_decision_turns,remaining_patch_attempts,expires_at_unix_ms,created_at,updated_at
                   ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    normalized_run, episode, goal["workspace_id"], goal["problem_id"], int(goal["problem_revision"]),
                    child_policy_json, child_policy_sha, goal["issuer_receipt_sha256"], 1, 1, "", None, 0, "", 0, 1, 0,
                    "", "", "[]", "{}", "", "", "", "", "", "", "",
                    int(goal["remaining_decision_turns"]), int(goal["remaining_patch_attempts"]), int(goal["expires_at_unix_ms"]), now, now,
                ),
            )
            self._append_run_continuation_event(
                connection,
                run_id=normalized_run,
                event_type="run_continuation_materialized_from_goal",
                payload={
                    "episode_id": episode,
                    "policy_sha256": child_policy_sha,
                    "remaining_decision_turns": int(goal["remaining_decision_turns"]),
                    "remaining_patch_attempts": int(goal["remaining_patch_attempts"]),
                },
            )
            row = connection.execute(
                "SELECT * FROM run_continuations WHERE run_id=?", (normalized_run,)
            ).fetchone()
            connection.commit()
        assert row is not None
        result = self._run_continuation_row(row)
        result["policy"] = _policy_projection(result["policy"])
        return {"status": "MATERIALIZED", "idempotent": False, "continuation": result}

    def materialize_matching_goal_continuation(
        self,
        *,
        run_id: str,
        grant_wave_id: str = "",
        now_unix_ms: int | None = None,
    ) -> dict[str, Any]:
        """Materialize the one exact live Goal episode already authorized for a child RUN."""
        normalized_run = _require_opaque(run_id, "run_id")
        now_ms = _now_ms() if now_unix_ms is None else int(now_unix_ms)
        with self._lock, self._connect() as connection:
            self._run_continuation_ensure_schema(connection)
            run = connection.execute(
                "SELECT status,metadata_json FROM runs WHERE run_id=?", (normalized_run,)
            ).fetchone()
            if run is None or str(run["status"] or "") != "active":
                raise RunContinuationError(
                    "RUN_CONTINUATION_RUN_NOT_ACTIVE",
                    "Goal continuation auto-materialization requires an active child RUN.",
                )
            try:
                metadata = json.loads(str(run["metadata_json"] or "{}"))
            except (TypeError, json.JSONDecodeError):
                metadata = {}
            binding = _controller_run_binding_from_metadata(metadata)
            if not isinstance(binding, dict):
                return {"status": "MISSING", "run_id": normalized_run}
            workspace_id = str(binding.get("workspace_id") or "").strip()
            problem_id = str(binding.get("problem_id") or "").strip()
            problem_revision = int(binding.get("problem_revision") or 0)
            if not workspace_id or not problem_id or problem_revision < 1:
                return {"status": "MISSING", "run_id": normalized_run}
            rows = connection.execute(
                """SELECT episode_id FROM goal_continuations
                   WHERE workspace_id=? AND problem_id=? AND problem_revision=?
                     AND enabled=1 AND revoked_at IS NULL AND expires_at_unix_ms>?
                   ORDER BY episode_id""",
                (workspace_id, problem_id, problem_revision, now_ms),
            ).fetchall()
        if not rows:
            return {"status": "MISSING", "run_id": normalized_run}
        if len(rows) != 1:
            raise RunContinuationError(
                "GOAL_CONTINUATION_AMBIGUOUS",
                "More than one live Goal continuation matches the exact child RUN binding.",
                details={"run_id": normalized_run, "count": len(rows)},
            )
        return self.materialize_goal_continuation(
            run_id=normalized_run,
            episode_id=str(rows[0]["episode_id"]),
            grant_wave_id=grant_wave_id,
            now_unix_ms=now_ms,
        )

