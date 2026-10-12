from __future__ import annotations

"""Durable RUN continuation ledger mixin."""

import hashlib
import json
import sqlite3
from typing import Any, Iterable

from .continuation_contract import (
    RUN_CONTINUATION_LEASE_SECONDS,
    RUN_CONTINUATION_MAX_NEW_FILES,
    RUN_CONTINUATION_MAX_REPLACEMENTS,
    RUN_CONTINUATION_PROFILE,
    RUN_CONTINUATION_ROUTE,
    RunContinuationError,
    _bounded,
    _canonical_json,
    _event_sanitize,
    _normalize_effect_artifact_path,
    _normalize_path,
    _normalize_paths,
    _normalize_technical_replan,
    _now_ms,
    _policy_projection,
    _require_opaque,
    _require_sha256,
    _utc_now,
)
from .goal_continuation_ledger import GOAL_CONTINUATION_NO_PROGRESS, GoalContinuationLedgerMixin
from .ledger_event_chain import append_hash_chained_event


class RunContinuationLedgerMixin(GoalContinuationLedgerMixin):
    """Same-ledger grant/cursor projection used by the continuation driver."""

    @staticmethod
    def _run_continuation_ensure_schema(connection: sqlite3.Connection) -> None:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS goal_continuations (
                episode_id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                problem_id TEXT NOT NULL,
                problem_revision INTEGER NOT NULL CHECK(problem_revision>=1),
                policy_json TEXT NOT NULL,
                policy_sha256 TEXT NOT NULL,
                issuer_receipt_sha256 TEXT NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1,
                pause_reason TEXT NOT NULL DEFAULT '',
                revoked_at TEXT,
                remaining_decision_turns INTEGER NOT NULL,
                remaining_patch_attempts INTEGER NOT NULL,
                no_progress_count INTEGER NOT NULL DEFAULT 0,
                expires_at_unix_ms INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE UNIQUE INDEX IF NOT EXISTS idx_goal_continuations_active_identity
                ON goal_continuations(workspace_id, problem_id, problem_revision)
                WHERE enabled=1 AND revoked_at IS NULL;
            CREATE TABLE IF NOT EXISTS goal_continuation_observations (
                observation_id TEXT PRIMARY KEY,
                episode_id TEXT NOT NULL REFERENCES goal_continuations(episode_id) ON DELETE CASCADE,
                run_id TEXT NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
                action_id TEXT NOT NULL,
                outcome TEXT NOT NULL CHECK(outcome IN ('progress','no_progress')),
                proof_identity_sha256 TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_goal_continuation_observations_episode
                ON goal_continuation_observations(episode_id, created_at);
            CREATE TABLE IF NOT EXISTS run_continuations (
                run_id TEXT PRIMARY KEY REFERENCES runs(run_id) ON DELETE CASCADE,
                parent_episode_id TEXT NOT NULL DEFAULT '',
                workspace_id TEXT NOT NULL,
                problem_id TEXT NOT NULL,
                problem_revision INTEGER NOT NULL CHECK(problem_revision>=1),
                policy_json TEXT NOT NULL,
                policy_sha256 TEXT NOT NULL,
                issuer_receipt_sha256 TEXT NOT NULL,
                policy_revision INTEGER NOT NULL DEFAULT 1,
                enabled INTEGER NOT NULL DEFAULT 1,
                pause_reason TEXT NOT NULL DEFAULT '',
                revoked_at TEXT,
                driver_generation INTEGER NOT NULL DEFAULT 0,
                claimed_runtime_instance TEXT NOT NULL DEFAULT '',
                claim_expires_at_unix_ms INTEGER NOT NULL DEFAULT 0,
                next_action_seq INTEGER NOT NULL DEFAULT 1,
                consumed_event_seq INTEGER NOT NULL DEFAULT 0,
                pending_action_id TEXT NOT NULL DEFAULT '',
                pending_evidence_hash TEXT NOT NULL DEFAULT '',
                pending_evidence_paths_json TEXT NOT NULL DEFAULT '[]',
                pending_replan_json TEXT NOT NULL DEFAULT '{}',
                pending_dispatch_action_id TEXT NOT NULL DEFAULT '',
                pending_job_id TEXT NOT NULL DEFAULT '',
                pending_patch_action_id TEXT NOT NULL DEFAULT '',
                lane_id TEXT NOT NULL DEFAULT '',
                thread_id TEXT NOT NULL DEFAULT '',
                thread_session_id TEXT NOT NULL DEFAULT '',
                last_turn_id TEXT NOT NULL DEFAULT '',
                remaining_decision_turns INTEGER NOT NULL,
                remaining_patch_attempts INTEGER NOT NULL,
                expires_at_unix_ms INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_run_continuations_eligible
                ON run_continuations(enabled, expires_at_unix_ms, claim_expires_at_unix_ms);
            CREATE TABLE IF NOT EXISTS run_continuation_effects (
                action_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
                driver_generation INTEGER NOT NULL,
                effect_kind TEXT NOT NULL,
                manifest_json TEXT NOT NULL,
                manifest_sha256 TEXT NOT NULL,
                status TEXT NOT NULL,
                recovery_reason TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_run_continuation_effects_run
                ON run_continuation_effects(run_id, status);
            """
        )
        columns = {str(row["name"]) for row in connection.execute("PRAGMA table_info(run_continuations)").fetchall()}
        if "parent_episode_id" not in columns:
            connection.execute("ALTER TABLE run_continuations ADD COLUMN parent_episode_id TEXT NOT NULL DEFAULT ''")
        if "pending_evidence_hash" not in columns:
            connection.execute("ALTER TABLE run_continuations ADD COLUMN pending_evidence_hash TEXT NOT NULL DEFAULT ''")
        if "pending_evidence_paths_json" not in columns:
            connection.execute("ALTER TABLE run_continuations ADD COLUMN pending_evidence_paths_json TEXT NOT NULL DEFAULT '[]'")
        if "pending_dispatch_action_id" not in columns:
            connection.execute("ALTER TABLE run_continuations ADD COLUMN pending_dispatch_action_id TEXT NOT NULL DEFAULT ''")
        if "pending_replan_json" not in columns:
            connection.execute("ALTER TABLE run_continuations ADD COLUMN pending_replan_json TEXT NOT NULL DEFAULT '{}'")
        if "pending_patch_action_id" not in columns:
            connection.execute("ALTER TABLE run_continuations ADD COLUMN pending_patch_action_id TEXT NOT NULL DEFAULT ''")
        if "thread_session_id" not in columns:
            connection.execute("ALTER TABLE run_continuations ADD COLUMN thread_session_id TEXT NOT NULL DEFAULT ''")

    @staticmethod
    def _normalize_effect_manifest(value: Any) -> dict[str, Any]:
        if not isinstance(value, dict) or set(value) != {"files", "backup_root"}:
            raise RunContinuationError("RUN_CONTINUATION_EFFECT_INVALID", "Effect manifest must contain exactly files and backup_root.")
        backup_root = _normalize_effect_artifact_path(value.get("backup_root"), "effect backup_root")
        files = value.get("files")
        if not isinstance(files, list) or not files or len(files) > RUN_CONTINUATION_MAX_REPLACEMENTS + RUN_CONTINUATION_MAX_NEW_FILES:
            raise RunContinuationError("RUN_CONTINUATION_EFFECT_INVALID", "Effect manifest requires a bounded non-empty file list.")
        normalized: list[dict[str, str]] = []
        seen: set[str] = set()
        for item in files:
            if not isinstance(item, dict) or set(item) != {"path", "preimage_sha256", "postimage_sha256", "backup_path"}:
                raise RunContinuationError("RUN_CONTINUATION_EFFECT_INVALID", "Each effect manifest row must contain exact path, preimage, postimage and backup path.")
            path = _normalize_path(item.get("path"), "effect path")
            preimage = str(item.get("preimage_sha256") or "")
            if preimage != "absent":
                preimage = _require_sha256(preimage, "effect preimage_sha256")
            postimage = _require_sha256(item.get("postimage_sha256"), "effect postimage_sha256")
            backup_path = _normalize_effect_artifact_path(item.get("backup_path"), "effect backup_path")
            if not backup_path.startswith(backup_root + "/"):
                raise RunContinuationError("RUN_CONTINUATION_EFFECT_INVALID", "Effect backup_path must stay beneath the action backup_root.")
            if path in seen:
                raise RunContinuationError("RUN_CONTINUATION_EFFECT_INVALID", "Effect manifest repeats a path.")
            seen.add(path)
            normalized.append({"path": path, "preimage_sha256": preimage, "postimage_sha256": postimage, "backup_path": backup_path})
        return {"files": sorted(normalized, key=lambda item: item["path"]), "backup_root": backup_root}

    def prepare_run_continuation_effect(
        self,
        *,
        run_id: str,
        driver_generation: int,
        runtime_instance_id: str,
        action_id: str,
        effect_kind: str,
        manifest: dict[str, Any],
    ) -> dict[str, Any]:
        normalized_run = _require_opaque(run_id, "run_id")
        normalized_action = _require_sha256(action_id, "action_id")
        kind = _require_opaque(effect_kind, "effect_kind", limit=64)
        normalized_manifest = self._normalize_effect_manifest(manifest)
        manifest_json = _canonical_json(normalized_manifest)
        manifest_sha = hashlib.sha256(manifest_json.encode("utf-8")).hexdigest()
        now = _utc_now()
        with self._lock, self._connect() as connection:
            self._run_continuation_ensure_schema(connection)
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT * FROM run_continuations WHERE run_id=?", (normalized_run,)).fetchone()
            record = self._run_continuation_row(row) if row is not None else None
            self._assert_run_continuation_row(
                record,
                run_id=normalized_run,
                driver_generation=driver_generation,
                runtime_instance_id=runtime_instance_id,
            )
            if record is None or record["pending_action_id"] != normalized_action:
                raise RunContinuationError("RUN_CONTINUATION_ACTION_MISMATCH", "Only the exact pending action may prepare a filesystem effect.")
            existing = connection.execute("SELECT * FROM run_continuation_effects WHERE action_id=?", (normalized_action,)).fetchone()
            if existing is not None:
                if str(existing["manifest_sha256"]) != manifest_sha or str(existing["effect_kind"]) != kind:
                    raise RunContinuationError("RUN_CONTINUATION_EFFECT_CONFLICT", "The pending action already has a different immutable effect journal.")
                connection.commit()
                return {"prepared": False, "idempotent": True, "status": str(existing["status"]), "manifest_sha256": manifest_sha}
            connection.execute(
                "INSERT INTO run_continuation_effects(action_id,run_id,driver_generation,effect_kind,manifest_json,manifest_sha256,status,recovery_reason,created_at,updated_at) VALUES(?,?,?,?,?,?,'pending','',?,?)",
                (normalized_action, normalized_run, int(driver_generation), kind, manifest_json, manifest_sha, now, now),
            )
            self._append_run_continuation_event(
                connection,
                run_id=normalized_run,
                event_type="run_continuation_effect_prepared",
                payload={"action_id": normalized_action, "driver_generation": driver_generation, "effect_kind": kind, "manifest_sha256": manifest_sha},
            )
            connection.commit()
        return {"prepared": True, "idempotent": False, "status": "pending", "manifest_sha256": manifest_sha}

    def get_run_continuation_effect(self, action_id: str) -> dict[str, Any] | None:
        normalized_action = _require_sha256(action_id, "action_id")
        with self._lock, self._connect() as connection:
            self._run_continuation_ensure_schema(connection)
            row = connection.execute("SELECT * FROM run_continuation_effects WHERE action_id=?", (normalized_action,)).fetchone()
        if row is None:
            return None
        return {
            "action_id": str(row["action_id"]), "run_id": str(row["run_id"]), "driver_generation": int(row["driver_generation"]),
            "effect_kind": str(row["effect_kind"]), "manifest": json.loads(str(row["manifest_json"])),
            "manifest_sha256": str(row["manifest_sha256"]), "status": str(row["status"]),
            "recovery_reason": str(row["recovery_reason"]), "created_at": str(row["created_at"]), "updated_at": str(row["updated_at"]),
        }

    def record_run_continuation_effect_observation(
        self,
        *,
        run_id: str,
        driver_generation: int,
        runtime_instance_id: str,
        action_id: str,
        status: str,
        recovery_reason: str = "",
    ) -> dict[str, Any]:
        normalized_run, normalized_action = _require_opaque(run_id, "run_id"), _require_sha256(action_id, "action_id")
        target = _bounded(status, 32).lower()
        if target not in {"applied", "not_applied", "recovery_required"}:
            raise RunContinuationError("RUN_CONTINUATION_EFFECT_INVALID", "Effect observation status is invalid.")
        reason = _bounded(recovery_reason, 512)
        now = _utc_now()
        with self._lock, self._connect() as connection:
            self._run_continuation_ensure_schema(connection)
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT * FROM run_continuations WHERE run_id=?", (normalized_run,)).fetchone()
            record = self._run_continuation_row(row) if row is not None else None
            self._assert_run_continuation_row(
                record,
                run_id=normalized_run,
                driver_generation=driver_generation,
                runtime_instance_id=runtime_instance_id,
            )
            effect = connection.execute("SELECT * FROM run_continuation_effects WHERE action_id=? AND run_id=?", (normalized_action, normalized_run)).fetchone()
            if effect is None:
                raise RunContinuationError("RUN_CONTINUATION_EFFECT_MISSING", "No prepared effect journal exists for the pending action.")
            previous = str(effect["status"])
            if previous not in {"pending", target}:
                raise RunContinuationError("RUN_CONTINUATION_EFFECT_CONFLICT", "Effect journal has a conflicting terminal observation.")
            connection.execute(
                "UPDATE run_continuation_effects SET status=?,recovery_reason=?,updated_at=? WHERE action_id=?",
                (target, reason, now, normalized_action),
            )
            self._append_run_continuation_event(
                connection,
                run_id=normalized_run,
                event_type="run_continuation_effect_observed",
                payload={"action_id": normalized_action, "driver_generation": driver_generation, "status": target, "recovery_reason": reason},
            )
            connection.commit()
        result = self.get_run_continuation_effect(normalized_action)
        assert result is not None
        return result

    def reconcile_run_continuation_pending_action(
        self,
        *,
        run_id: str,
        action_id: str,
        effect_status: str,
        recovery_reason: str,
        controller_fencing_token: object,
        terminal_job_id: str = "",
    ) -> dict[str, Any]:
        """Terminalize a classified pending effect through the controller path.

        This is deliberately narrower than ordinary execution: it can run after
        pause, revoke, claim expiry, or grant expiry, but only on the exact
        pending action, only after filesystem state has been classified, and
        only after a still-bound managed Job is independently known terminal.
        It never replays a patch or turns an unknown dispatch into a result.
        """
        normalized_run = _require_opaque(run_id, "run_id")
        normalized_action = _require_sha256(action_id, "action_id")
        target = _bounded(effect_status, 32).lower()
        if target not in {"applied", "not_applied", "recovery_required"}:
            raise RunContinuationError("RUN_CONTINUATION_EFFECT_INVALID", "Reconciliation effect status is invalid.")
        reason = _bounded(recovery_reason, 512)
        controller_token = _bounded(controller_fencing_token, 256)
        if not controller_token:
            raise RunContinuationError("RUN_CONTINUATION_CONTROLLER_REQUIRED", "Pending-effect reconciliation requires an active controller receipt.")
        terminal_job = _require_opaque(terminal_job_id, "terminal_job_id") if terminal_job_id else ""
        now_ms = _now_ms()
        now = _utc_now()
        with self._lock, self._connect() as connection:
            self._run_continuation_ensure_schema(connection)
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT * FROM run_continuations WHERE run_id=?", (normalized_run,)).fetchone()
            record = self._run_continuation_row(row) if row is not None else None
            if record is None:
                raise RunContinuationError("RUN_CONTINUATION_GRANT_REQUIRED", "No continuation record exists for reconciliation.")
            if (
                record["enabled"]
                and str(record["claimed_runtime_instance"] or "")
                and now_ms < int(record["claim_expires_at_unix_ms"])
            ):
                raise RunContinuationError(
                    "RUN_CONTINUATION_DRIVER_ACTIVE",
                    "Pause or revoke the currently live driver claim before controller reconciliation.",
                )
            if record["pending_action_id"] != normalized_action:
                raise RunContinuationError("RUN_CONTINUATION_ACTION_MISMATCH", "Only the exact pending action may be reconciled.")
            pending_job = str(record["pending_job_id"] or "")
            if pending_job and pending_job != terminal_job:
                raise RunContinuationError(
                    "RUN_CONTINUATION_JOB_OUTCOME_UNKNOWN",
                    "The pending managed proof Job is not proven terminal; do not terminalize the action.",
                )
            effect = connection.execute(
                "SELECT * FROM run_continuation_effects WHERE action_id=? AND run_id=?",
                (normalized_action, normalized_run),
            ).fetchone()
            if effect is None:
                raise RunContinuationError("RUN_CONTINUATION_EFFECT_MISSING", "No exact effect journal exists for the pending action.")
            previous = str(effect["status"])
            if previous not in {"pending", target}:
                raise RunContinuationError("RUN_CONTINUATION_EFFECT_CONFLICT", "Effect journal has a conflicting terminal observation.")
            connection.execute(
                "UPDATE run_continuation_effects SET status=?,recovery_reason=?,updated_at=? WHERE action_id=?",
                (target, reason, now, normalized_action),
            )
            connection.execute(
                """UPDATE run_continuations
                   SET pending_action_id='',pending_evidence_hash='',pending_evidence_paths_json='[]',pending_replan_json='{}',
                       pending_dispatch_action_id='',pending_job_id='',pending_patch_action_id='',updated_at=?
                   WHERE run_id=?""",
                (now, normalized_run),
            )
            self._append_run_continuation_event(
                connection,
                run_id=normalized_run,
                event_type="run_continuation_reconciliation_terminalized",
                payload={
                    "action_id": normalized_action,
                    "effect_status": target,
                    "recovery_reason": reason,
                    "terminal_job_id": terminal_job,
                    "controller_fencing_token_sha256": hashlib.sha256(controller_token.encode("utf-8")).hexdigest(),
                },
            )
            updated = connection.execute("SELECT * FROM run_continuations WHERE run_id=?", (normalized_run,)).fetchone()
            connection.commit()
        assert updated is not None
        continuation = self._run_continuation_row(updated)
        continuation["policy"] = _policy_projection(continuation["policy"])
        return continuation

    @staticmethod
    def _run_continuation_row(row: sqlite3.Row) -> dict[str, Any]:
        policy = json.loads(str(row["policy_json"] or "{}"))
        return {
            "run_id": str(row["run_id"]),
            "parent_episode_id": str(row["parent_episode_id"]),
            "workspace_id": str(row["workspace_id"]),
            "problem_id": str(row["problem_id"]),
            "problem_revision": int(row["problem_revision"]),
            "policy_sha256": str(row["policy_sha256"]),
            "issuer_receipt_sha256": str(row["issuer_receipt_sha256"]),
            "policy_revision": int(row["policy_revision"]),
            "enabled": bool(row["enabled"]),
            "pause_reason": str(row["pause_reason"]),
            "revoked_at": row["revoked_at"],
            "driver_generation": int(row["driver_generation"]),
            "claimed_runtime_instance": str(row["claimed_runtime_instance"]),
            "claim_expires_at_unix_ms": int(row["claim_expires_at_unix_ms"]),
            "next_action_seq": int(row["next_action_seq"]),
            "consumed_event_seq": int(row["consumed_event_seq"]),
            "pending_action_id": str(row["pending_action_id"]),
            "pending_evidence_hash": str(row["pending_evidence_hash"]),
            "pending_evidence_paths": json.loads(str(row["pending_evidence_paths_json"] or "[]")),
            "pending_replan": json.loads(str(row["pending_replan_json"] or "{}")),
            "pending_dispatch_action_id": str(row["pending_dispatch_action_id"]),
            "pending_job_id": str(row["pending_job_id"]),
            "pending_patch_action_id": str(row["pending_patch_action_id"]),
            "lane_id": str(row["lane_id"]),
            "thread_id": str(row["thread_id"]),
            "thread_session_id": str(row["thread_session_id"]),
            "last_turn_id": str(row["last_turn_id"]),
            "remaining_decision_turns": int(row["remaining_decision_turns"]),
            "remaining_patch_attempts": int(row["remaining_patch_attempts"]),
            "expires_at_unix_ms": int(row["expires_at_unix_ms"]),
            "created_at": str(row["created_at"]),
            "updated_at": str(row["updated_at"]),
            "policy": policy,
        }

    @staticmethod
    def _append_run_continuation_event(
        connection: sqlite3.Connection,
        *,
        run_id: str,
        event_type: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        return append_hash_chained_event(
            connection,
            run_id=run_id,
            event_type=event_type,
            wave_id=None,
            delegation_id=None,
            state_before="",
            state_after="",
            payload=payload,
            event_time=_utc_now(),
            sanitize=_event_sanitize,
            serialize=_canonical_json,
            bounded_text=_bounded,
        )

    def _run_continuation_get_raw(self, run_id: str) -> dict[str, Any] | None:
        normalized = _require_opaque(run_id, "run_id")
        with self._lock, self._connect() as connection:
            self._run_continuation_ensure_schema(connection)
            row = connection.execute("SELECT * FROM run_continuations WHERE run_id=?", (normalized,)).fetchone()
        return self._run_continuation_row(row) if row is not None else None

    def get_run_continuation(self, run_id: str) -> dict[str, Any] | None:
        record = self._run_continuation_get_raw(run_id)
        if record is None:
            return None
        record["policy"] = _policy_projection(record["policy"])
        return record

    def issue_run_continuation(
        self,
        *,
        run_id: str,
        policy: dict[str, Any],
        issuer_receipt_sha256: str,
        now_unix_ms: int | None = None,
    ) -> dict[str, Any]:
        normalized_run = _require_opaque(run_id, "run_id")
        if str(policy.get("run_id") or "") != normalized_run:
            raise RunContinuationError("RUN_CONTINUATION_POLICY_INVALID", "Policy RUN does not match the grant target.")
        receipt = _require_sha256(issuer_receipt_sha256, "issuer_receipt_sha256")
        policy_json = _canonical_json(policy)
        policy_sha = hashlib.sha256(policy_json.encode("utf-8")).hexdigest()
        now_ms = _now_ms() if now_unix_ms is None else int(now_unix_ms)
        expires_at = now_ms + int(policy["max_duration_seconds"]) * 1_000
        now = _utc_now()
        with self._lock, self._connect() as connection:
            self._run_continuation_ensure_schema(connection)
            connection.execute("BEGIN IMMEDIATE")
            run = connection.execute("SELECT status FROM runs WHERE run_id=?", (normalized_run,)).fetchone()
            if run is None:
                raise RunContinuationError("ORCHESTRATION_RUN_NOT_FOUND", "Cannot issue a continuation grant for a missing RUN.")
            if str(run["status"] or "") != "active":
                raise RunContinuationError("RUN_CONTINUATION_RUN_NOT_ACTIVE", "Continuation grants require an active RUN.")
            existing_row = connection.execute("SELECT * FROM run_continuations WHERE run_id=?", (normalized_run,)).fetchone()
            if existing_row is not None:
                existing = self._run_continuation_row(existing_row)
                if existing["enabled"] and existing["policy_sha256"] == policy_sha and existing["issuer_receipt_sha256"] == receipt:
                    connection.commit()
                    existing["policy"] = _policy_projection(existing["policy"])
                    return {"status": "GRANTED", "idempotent": True, "continuation": existing}
                if existing["enabled"]:
                    raise RunContinuationError(
                        "RUN_CONTINUATION_GRANT_CONFLICT",
                        "The RUN already has an enabled immutable continuation policy; revoke it before issuing a different policy.",
                        details={"policy_sha256": existing["policy_sha256"]},
                    )
                if existing["pending_action_id"] or existing["pending_job_id"]:
                    raise RunContinuationError(
                        "RUN_CONTINUATION_EFFECT_PENDING",
                        "A revoked continuation still has a pending effect; reconcile it before issuing a replacement policy.",
                    )
                policy_revision = int(existing["policy_revision"]) + 1
                connection.execute(
                    """UPDATE run_continuations
                       SET parent_episode_id='',workspace_id=?,problem_id=?,problem_revision=?,policy_json=?,policy_sha256=?,issuer_receipt_sha256=?,
                           policy_revision=?,enabled=1,pause_reason='',revoked_at=NULL,
                           claimed_runtime_instance='',claim_expires_at_unix_ms=0,next_action_seq=1,consumed_event_seq=0,pending_evidence_hash='',pending_evidence_paths_json='[]',pending_replan_json='{}',pending_dispatch_action_id='',pending_patch_action_id='',
                           lane_id='',thread_id='',thread_session_id='',last_turn_id='',
                           remaining_decision_turns=?,remaining_patch_attempts=?,expires_at_unix_ms=?,updated_at=?
                       WHERE run_id=?""",
                    (
                        policy["workspace_id"], policy["problem_id"], int(policy["problem_revision"]), policy_json, policy_sha,
                        receipt, policy_revision, int(policy["max_decision_turns"]), int(policy["max_patch_attempts"]), expires_at,
                        now, normalized_run,
                    ),
                )
                event_type = "run_continuation_regranted"
            else:
                policy_revision = 1
                connection.execute(
                    """INSERT INTO run_continuations(
                           run_id,workspace_id,problem_id,problem_revision,policy_json,policy_sha256,issuer_receipt_sha256,
                           policy_revision,enabled,pause_reason,revoked_at,driver_generation,claimed_runtime_instance,
                           claim_expires_at_unix_ms,next_action_seq,consumed_event_seq,pending_action_id,pending_evidence_hash,pending_evidence_paths_json,pending_replan_json,pending_dispatch_action_id,pending_job_id,pending_patch_action_id,lane_id,
                           thread_id,thread_session_id,last_turn_id,remaining_decision_turns,remaining_patch_attempts,expires_at_unix_ms,created_at,updated_at
                       ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        normalized_run, policy["workspace_id"], policy["problem_id"], int(policy["problem_revision"]), policy_json,
                        policy_sha, receipt, policy_revision, 1, "", None, 0, "", 0, 1, 0, "", "", "[]", "{}", "", "", "", "", "", "", "",
                        int(policy["max_decision_turns"]), int(policy["max_patch_attempts"]), expires_at, now, now,
                    ),
                )
                event_type = "run_continuation_granted"
            self._append_run_continuation_event(
                connection,
                run_id=normalized_run,
                event_type=event_type,
                payload={
                    "policy_sha256": policy_sha,
                    "issuer_receipt_sha256": receipt,
                    "policy_revision": policy_revision,
                    "expires_at_unix_ms": expires_at,
                    "route": RUN_CONTINUATION_ROUTE,
                    "profile": RUN_CONTINUATION_PROFILE,
                },
            )
            row = connection.execute("SELECT * FROM run_continuations WHERE run_id=?", (normalized_run,)).fetchone()
            connection.commit()
        assert row is not None
        result = self._run_continuation_row(row)
        result["policy"] = _policy_projection(result["policy"])
        return {"status": "GRANTED", "idempotent": False, "continuation": result}

    def _assert_run_continuation_row(
        self,
        record: dict[str, Any] | None,
        *,
        run_id: str,
        driver_generation: int | None = None,
        runtime_instance_id: str = "",
        now_unix_ms: int | None = None,
        connection: sqlite3.Connection | None = None,
    ) -> dict[str, Any]:
        if record is None:
            raise RunContinuationError("RUN_CONTINUATION_GRANT_REQUIRED", "No durable execution grant exists for this RUN.")
        now_ms = _now_ms() if now_unix_ms is None else int(now_unix_ms)
        if not record["enabled"] or record["revoked_at"]:
            raise RunContinuationError("RUN_CONTINUATION_REVOKED", "The continuation grant is revoked or disabled.")
        if now_ms >= int(record["expires_at_unix_ms"]):
            raise RunContinuationError("RUN_CONTINUATION_EXPIRED", "The continuation grant has expired.")
        parent_episode = str(record.get("parent_episode_id") or "")
        if parent_episode:
            parent = self._assert_goal_continuation_row(
                self._goal_continuation_get_raw(parent_episode, connection=connection),
                episode_id=parent_episode,
                now_unix_ms=now_ms,
            )
            if (
                str(parent["workspace_id"]) != str(record["workspace_id"])
                or str(parent["problem_id"]) != str(record["problem_id"])
                or int(parent["problem_revision"]) != int(record["problem_revision"])
            ):
                raise RunContinuationError(
                    "GOAL_CONTINUATION_CHILD_BINDING_MISMATCH",
                    "Child continuation identity no longer matches its parent Goal episode.",
                )
        if driver_generation is not None and int(driver_generation) != int(record["driver_generation"]):
            raise RunContinuationError(
                "RUN_CONTINUATION_STALE_GENERATION",
                "The driver generation is fenced; discard the stale continuation action.",
                details={"run_id": run_id, "expected_generation": record["driver_generation"]},
            )
        if driver_generation is not None:
            runtime = _require_opaque(runtime_instance_id, "runtime_instance_id")
            if str(record["claimed_runtime_instance"] or "") != runtime:
                raise RunContinuationError(
                    "RUN_CONTINUATION_CLAIM_OWNER_MISMATCH",
                    "The continuation claim belongs to a different runtime instance.",
                    details={"run_id": run_id},
                )
            if now_ms >= int(record["claim_expires_at_unix_ms"]):
                raise RunContinuationError(
                    "RUN_CONTINUATION_CLAIM_EXPIRED",
                    "The continuation claim expired; reacquire through the fenced driver claim path.",
                    retryable=True,
                    details={"run_id": run_id},
                )
        return record

    def claim_run_continuation(
        self,
        *,
        run_id: str,
        runtime_instance_id: str,
        expected_generation: int,
        now_unix_ms: int | None = None,
        lease_seconds: int = RUN_CONTINUATION_LEASE_SECONDS,
    ) -> dict[str, Any]:
        normalized_run = _require_opaque(run_id, "run_id")
        runtime = _require_opaque(runtime_instance_id, "runtime_instance_id")
        if isinstance(expected_generation, bool) or not isinstance(expected_generation, int) or expected_generation < 0:
            raise RunContinuationError("RUN_CONTINUATION_GENERATION_INVALID", "expected_generation must be a non-negative integer.")
        if isinstance(lease_seconds, bool) or not isinstance(lease_seconds, int) or lease_seconds < 1 or lease_seconds > RUN_CONTINUATION_LEASE_SECONDS:
            raise RunContinuationError("RUN_CONTINUATION_CLAIM_INVALID", "lease_seconds is outside the bounded continuation claim policy.")
        now_ms = _now_ms() if now_unix_ms is None else int(now_unix_ms)
        now = _utc_now()
        with self._lock, self._connect() as connection:
            self._run_continuation_ensure_schema(connection)
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT * FROM run_continuations WHERE run_id=?", (normalized_run,)).fetchone()
            record = self._run_continuation_row(row) if row is not None else None
            record = self._assert_run_continuation_row(record, run_id=normalized_run, now_unix_ms=now_ms)
            current_generation = int(record["driver_generation"])
            if expected_generation != current_generation:
                connection.commit()
                return {"claimed": False, "reason": "stale_generation", "continuation": self.get_run_continuation(normalized_run)}
            active_owner = str(record["claimed_runtime_instance"])
            active_claim = int(record["claim_expires_at_unix_ms"]) > now_ms
            if active_claim and active_owner and active_owner != runtime:
                connection.commit()
                return {"claimed": False, "reason": "claimed_by_other_runtime", "continuation": self.get_run_continuation(normalized_run)}
            next_generation = current_generation if active_claim and active_owner == runtime else current_generation + 1
            expires_at = now_ms + lease_seconds * 1_000
            connection.execute(
                """UPDATE run_continuations
                   SET driver_generation=?,claimed_runtime_instance=?,claim_expires_at_unix_ms=?,updated_at=?
                   WHERE run_id=?""",
                (next_generation, runtime, expires_at, now, normalized_run),
            )
            self._append_run_continuation_event(
                connection,
                run_id=normalized_run,
                event_type="run_continuation_claimed",
                payload={"driver_generation": next_generation, "claim_expires_at_unix_ms": expires_at, "reclaimed": bool(active_owner and active_owner != runtime)},
            )
            updated = connection.execute("SELECT * FROM run_continuations WHERE run_id=?", (normalized_run,)).fetchone()
            connection.commit()
        assert updated is not None
        continuation = self._run_continuation_row(updated)
        continuation["policy"] = _policy_projection(continuation["policy"])
        return {"claimed": True, "reason": "claimed", "continuation": continuation}

    def renew_run_continuation_claim(
        self,
        *,
        run_id: str,
        runtime_instance_id: str,
        driver_generation: int,
        now_unix_ms: int | None = None,
        lease_seconds: int = RUN_CONTINUATION_LEASE_SECONDS,
    ) -> dict[str, Any]:
        """Renew only the exact, still-live owner claim; never revive it."""
        normalized_run = _require_opaque(run_id, "run_id")
        runtime = _require_opaque(runtime_instance_id, "runtime_instance_id")
        if isinstance(driver_generation, bool) or not isinstance(driver_generation, int) or driver_generation < 1:
            raise RunContinuationError("RUN_CONTINUATION_GENERATION_INVALID", "driver_generation must be a positive integer.")
        if isinstance(lease_seconds, bool) or not isinstance(lease_seconds, int) or lease_seconds < 1 or lease_seconds > RUN_CONTINUATION_LEASE_SECONDS:
            raise RunContinuationError("RUN_CONTINUATION_CLAIM_INVALID", "lease_seconds is outside the bounded continuation claim policy.")
        now_ms = _now_ms() if now_unix_ms is None else int(now_unix_ms)
        now = _utc_now()
        with self._lock, self._connect() as connection:
            self._run_continuation_ensure_schema(connection)
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT * FROM run_continuations WHERE run_id=?", (normalized_run,)).fetchone()
            record = self._run_continuation_row(row) if row is not None else None
            record = self._assert_run_continuation_row(
                record,
                run_id=normalized_run,
                driver_generation=driver_generation,
                runtime_instance_id=runtime,
                now_unix_ms=now_ms,
            )
            expires_at = now_ms + lease_seconds * 1_000
            connection.execute(
                "UPDATE run_continuations SET claim_expires_at_unix_ms=?,updated_at=? WHERE run_id=?",
                (expires_at, now, normalized_run),
            )
            self._append_run_continuation_event(
                connection,
                run_id=normalized_run,
                event_type="run_continuation_claim_renewed",
                payload={"driver_generation": driver_generation, "claim_expires_at_unix_ms": expires_at},
            )
            updated = connection.execute("SELECT * FROM run_continuations WHERE run_id=?", (normalized_run,)).fetchone()
            connection.commit()
        assert updated is not None
        continuation = self._run_continuation_row(updated)
        continuation["policy"] = _policy_projection(continuation["policy"])
        return continuation

    def assert_run_continuation_execution(
        self,
        *,
        run_id: str,
        driver_generation: int,
        runtime_instance_id: str,
        paths: Iterable[str] = (),
        check_definition_hash: str = "",
        now_unix_ms: int | None = None,
    ) -> dict[str, Any]:
        record = self._run_continuation_get_raw(run_id)
        record = self._assert_run_continuation_row(
            record,
            run_id=run_id,
            driver_generation=driver_generation,
            runtime_instance_id=runtime_instance_id,
            now_unix_ms=now_unix_ms,
        )
        policy = record["policy"]
        requested_paths = {_normalize_path(item, "execution path") for item in paths}
        allowed = set(policy.get("write_paths") or [])
        protected = set(policy.get("protected_paths") or [])
        denied = sorted(path for path in requested_paths if path not in allowed or path in protected)
        if denied:
            raise RunContinuationError(
                "RUN_CONTINUATION_SCOPE_DENIED",
                "The delegated action exceeds the immutable continuation write scope.",
                details={"paths": denied},
            )
        if check_definition_hash:
            check_hash = _require_sha256(check_definition_hash, "check_definition_hash")
            approved = {str(item.get("definition_hash") or "") for item in policy.get("approved_checks") or [] if isinstance(item, dict)}
            if check_hash not in approved:
                raise RunContinuationError(
                    "RUN_CONTINUATION_CHECK_DENIED",
                    "The delegated action selected a check not bound into the grant policy.",
                )
        return record

    def reserve_run_continuation_action(
        self,
        *,
        run_id: str,
        driver_generation: int,
        runtime_instance_id: str,
        action_kind: str,
        request_hash: str,
        evidence_hash: str = "",
        evidence_paths: Iterable[str] = (),
        technical_replan: dict[str, Any] | None = None,
        expected_action_seq: int,
        now_unix_ms: int | None = None,
    ) -> dict[str, Any]:
        normalized_run = _require_opaque(run_id, "run_id")
        kind = _require_opaque(action_kind, "action_kind", limit=64)
        request_digest = _require_sha256(request_hash, "request_hash")
        evidence_digest = _require_sha256(evidence_hash, "evidence_hash") if evidence_hash else ""
        normalized_evidence_paths = _normalize_paths(list(evidence_paths), "evidence_paths")
        normalized_replan = _normalize_technical_replan(technical_replan)
        if isinstance(expected_action_seq, bool) or not isinstance(expected_action_seq, int) or expected_action_seq < 1:
            raise RunContinuationError("RUN_CONTINUATION_ACTION_INVALID", "expected_action_seq must be a positive integer.")
        now_ms = _now_ms() if now_unix_ms is None else int(now_unix_ms)
        now = _utc_now()
        with self._lock, self._connect() as connection:
            self._run_continuation_ensure_schema(connection)
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT * FROM run_continuations WHERE run_id=?", (normalized_run,)).fetchone()
            record = self._run_continuation_row(row) if row is not None else None
            record = self._assert_run_continuation_row(
                record,
                run_id=normalized_run,
                driver_generation=driver_generation,
                runtime_instance_id=runtime_instance_id,
                now_unix_ms=now_ms,
                connection=connection,
            )
            allowed_reads = set(record["policy"].get("read_paths") or [])
            denied_evidence_paths = sorted(set(normalized_evidence_paths).difference(allowed_reads))
            if denied_evidence_paths:
                raise RunContinuationError(
                    "RUN_CONTINUATION_READ_SCOPE_DENIED",
                    "An evidence packet includes a path outside the immutable continuation read scope.",
                    details={"paths": denied_evidence_paths},
                )
            parent_episode = str(record.get("parent_episode_id") or "")
            parent = None
            remaining_decision_turns = int(record["remaining_decision_turns"])
            if parent_episode:
                parent = self._assert_goal_continuation_row(
                    self._goal_continuation_get_raw(parent_episode, connection=connection),
                    episode_id=parent_episode,
                    now_unix_ms=now_ms,
                )
                remaining_decision_turns = int(parent["remaining_decision_turns"])
            if remaining_decision_turns < 1:
                raise RunContinuationError("RUN_CONTINUATION_DECISION_BUDGET_EXHAUSTED", "No continuation decision turns remain.")
            current_seq = int(record["next_action_seq"])
            action_id = hashlib.sha256(
                f"run-continuation-v1\0{normalized_run}\0{record['policy_revision']}\0{expected_action_seq}\0{kind}\0{request_digest}".encode("utf-8")
            ).hexdigest()
            if record["pending_action_id"]:
                if record["pending_action_id"] == action_id:
                    connection.commit()
                    return {"reserved": False, "idempotent": True, "action_id": action_id, "continuation": self.get_run_continuation(normalized_run)}
                raise RunContinuationError("RUN_CONTINUATION_ACTION_PENDING", "Reconcile the existing pending continuation action before reserving another.")
            if expected_action_seq != current_seq:
                raise RunContinuationError(
                    "RUN_CONTINUATION_ACTION_SEQUENCE_STALE",
                    "The continuation action cursor changed; do not create a second effect identity.",
                    details={"expected_action_seq": current_seq},
                )
            next_remaining_decision_turns = remaining_decision_turns - 1
            if parent is not None:
                connection.execute(
                    "UPDATE goal_continuations SET remaining_decision_turns=?,updated_at=? WHERE episode_id=?",
                    (next_remaining_decision_turns, now, parent_episode),
                )
            connection.execute(
                """UPDATE run_continuations
                   SET pending_action_id=?,pending_evidence_hash=?,pending_evidence_paths_json=?,pending_replan_json=?,pending_dispatch_action_id='',pending_job_id='',pending_patch_action_id='',next_action_seq=?,remaining_decision_turns=?,updated_at=?
                   WHERE run_id=?""",
                (action_id, evidence_digest, _canonical_json(normalized_evidence_paths), _canonical_json(normalized_replan), current_seq + 1, next_remaining_decision_turns, now, normalized_run),
            )
            self._append_run_continuation_event(
                connection,
                run_id=normalized_run,
                event_type="run_continuation_action_reserved",
                payload={"action_id": action_id, "action_seq": current_seq, "action_kind": kind, "driver_generation": driver_generation, "request_hash": request_digest, "evidence_hash": evidence_digest, "evidence_path_count": len(normalized_evidence_paths), "technical_replan": bool(normalized_replan), "parent_episode_id": parent_episode, "remaining_decision_turns": next_remaining_decision_turns},
            )
            updated = connection.execute("SELECT * FROM run_continuations WHERE run_id=?", (normalized_run,)).fetchone()
            connection.commit()
        assert updated is not None
        continuation = self._run_continuation_row(updated)
        continuation["policy"] = _policy_projection(continuation["policy"])
        return {"reserved": True, "idempotent": False, "action_id": action_id, "continuation": continuation}

    def release_run_continuation_action(
        self,
        *,
        run_id: str,
        driver_generation: int,
        runtime_instance_id: str,
        action_id: str,
    ) -> dict[str, Any]:
        """Release an exact decision reservation only while replay is provably safe.

        The action sequence is intentionally not rewound. A released action id
        therefore cannot be regenerated even though its decision-budget unit is
        returned to the bounded grant.
        """
        normalized_run = _require_opaque(run_id, "run_id")
        normalized_action = _require_sha256(action_id, "action_id")
        now = _utc_now()
        with self._lock, self._connect() as connection:
            self._run_continuation_ensure_schema(connection)
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT * FROM run_continuations WHERE run_id=?", (normalized_run,)).fetchone()
            record = self._run_continuation_row(row) if row is not None else None
            record = self._assert_run_continuation_row(
                record,
                run_id=normalized_run,
                driver_generation=driver_generation,
                runtime_instance_id=runtime_instance_id,
                connection=connection,
            )
            if record["pending_action_id"] != normalized_action:
                raise RunContinuationError(
                    "RUN_CONTINUATION_ACTION_MISMATCH",
                    "Only the exact pending action can release its decision reservation.",
                )
            downstream = [
                name
                for name, value in (
                    ("dispatch", record["pending_dispatch_action_id"]),
                    ("job", record["pending_job_id"]),
                    ("patch", record["pending_patch_action_id"]),
                )
                if value
            ]
            if downstream:
                raise RunContinuationError(
                    "RUN_CONTINUATION_EFFECT_RECONCILE_REQUIRED",
                    "The pending action has downstream execution state; reconcile it before releasing the reservation.",
                    details={"pending": downstream},
                )
            effect = connection.execute(
                "SELECT status FROM run_continuation_effects WHERE action_id=? AND run_id=?",
                (normalized_action, normalized_run),
            ).fetchone()
            effect_status = str(effect["status"]) if effect is not None else ""
            if effect is not None and effect_status != "not_applied":
                raise RunContinuationError(
                    "RUN_CONTINUATION_EFFECT_RECONCILE_REQUIRED",
                    "The pending action has an effect whose outcome is not safely classified as not_applied.",
                    details={"effect_status": effect_status},
                )
            parent_episode = str(record.get("parent_episode_id") or "")
            parent = None
            restored_decision_turns = int(record["remaining_decision_turns"]) + 1
            if parent_episode:
                parent = self._assert_goal_continuation_row(
                    self._goal_continuation_get_raw(parent_episode, connection=connection),
                    episode_id=parent_episode,
                )
                restored_decision_turns = int(parent["remaining_decision_turns"]) + 1
                if restored_decision_turns > int(parent["policy"]["max_decision_turns"]):
                    raise RunContinuationError(
                        "GOAL_CONTINUATION_BUDGET_CONFLICT",
                        "Decision budget refund would exceed the immutable Goal episode budget.",
                    )
                connection.execute(
                    "UPDATE goal_continuations SET remaining_decision_turns=?,updated_at=? WHERE episode_id=?",
                    (restored_decision_turns, now, parent_episode),
                )
            connection.execute(
                """UPDATE run_continuations
                   SET pending_action_id='',pending_evidence_hash='',pending_evidence_paths_json='[]',pending_replan_json='{}',
                       pending_dispatch_action_id='',pending_job_id='',pending_patch_action_id='',
                       remaining_decision_turns=?,updated_at=?
                   WHERE run_id=?""",
                (restored_decision_turns, now, normalized_run),
            )
            self._append_run_continuation_event(
                connection,
                run_id=normalized_run,
                event_type="run_continuation_action_released",
                payload={
                    "action_id": normalized_action,
                    "driver_generation": driver_generation,
                    "effect_status": effect_status,
                    "decision_budget_restored": True,
                    "parent_episode_id": parent_episode,
                    "remaining_decision_turns": restored_decision_turns,
                },
            )
            updated = connection.execute("SELECT * FROM run_continuations WHERE run_id=?", (normalized_run,)).fetchone()
            connection.commit()
        assert updated is not None
        continuation = self._run_continuation_row(updated)
        continuation["policy"] = _policy_projection(continuation["policy"])
        return continuation

    def complete_run_continuation_action(
        self,
        *,
        run_id: str,
        driver_generation: int,
        runtime_instance_id: str,
        action_id: str,
        consumed_event_seq: int = 0,
        proof_observation_id: str = "",
        proof_identity_sha256: str = "",
        proof_outcome: str = "",
    ) -> dict[str, Any]:
        normalized_run = _require_opaque(run_id, "run_id")
        normalized_action = _require_sha256(action_id, "action_id")
        if isinstance(consumed_event_seq, bool) or not isinstance(consumed_event_seq, int) or consumed_event_seq < 0:
            raise RunContinuationError("RUN_CONTINUATION_ACTION_INVALID", "consumed_event_seq must be non-negative.")
        observation_fields = [bool(proof_observation_id), bool(proof_identity_sha256), bool(proof_outcome)]
        if any(observation_fields) and not all(observation_fields):
            raise RunContinuationError(
                "GOAL_CONTINUATION_OBSERVATION_INVALID",
                "A proof observation requires observation id, proof identity, and outcome together.",
            )
        observation_id = _require_sha256(proof_observation_id, "proof_observation_id") if proof_observation_id else ""
        proof_identity = _require_sha256(proof_identity_sha256, "proof_identity_sha256") if proof_identity_sha256 else ""
        observation_outcome = _bounded(proof_outcome, 32).lower() if proof_outcome else ""
        if observation_outcome and observation_outcome not in {"progress", "no_progress"}:
            raise RunContinuationError(
                "GOAL_CONTINUATION_OBSERVATION_INVALID",
                "Proof observation outcome must be progress or no_progress.",
            )
        now = _utc_now()
        goal_observation: dict[str, Any] | None = None
        with self._lock, self._connect() as connection:
            self._run_continuation_ensure_schema(connection)
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT * FROM run_continuations WHERE run_id=?", (normalized_run,)).fetchone()
            record = self._run_continuation_row(row) if row is not None else None
            record = self._assert_run_continuation_row(
                record,
                run_id=normalized_run,
                driver_generation=driver_generation,
                runtime_instance_id=runtime_instance_id,
                connection=connection,
            )
            if record["pending_action_id"] != normalized_action:
                raise RunContinuationError("RUN_CONTINUATION_ACTION_MISMATCH", "Only the exact pending action can advance the continuation cursor.")
            parent_episode = str(record.get("parent_episode_id") or "")
            if observation_id and parent_episode:
                existing = connection.execute(
                    "SELECT * FROM goal_continuation_observations WHERE observation_id=?",
                    (observation_id,),
                ).fetchone()
                if existing is not None:
                    if (
                        str(existing["episode_id"]) != parent_episode
                        or str(existing["outcome"]) != observation_outcome
                        or str(existing["proof_identity_sha256"]) != proof_identity
                    ):
                        raise RunContinuationError(
                            "GOAL_CONTINUATION_OBSERVATION_CONFLICT",
                            "A proof observation id is already bound to different Goal evidence.",
                        )
                    parent_row = connection.execute(
                        "SELECT * FROM goal_continuations WHERE episode_id=?", (parent_episode,)
                    ).fetchone()
                    if parent_row is None:
                        raise RunContinuationError("GOAL_CONTINUATION_GRANT_REQUIRED", "The parent Goal episode disappeared.")
                    parent = self._goal_continuation_row(parent_row)
                    goal_observation = {
                        "observation_id": observation_id,
                        "outcome": observation_outcome,
                        "idempotent": True,
                        "no_progress_count": int(parent["no_progress_count"]),
                        "stopped": (not parent["enabled"] and str(parent["pause_reason"]) == GOAL_CONTINUATION_NO_PROGRESS),
                        "reason": str(parent["pause_reason"] or ""),
                    }
                else:
                    parent_row = connection.execute(
                        "SELECT * FROM goal_continuations WHERE episode_id=?", (parent_episode,)
                    ).fetchone()
                    parent = self._assert_goal_continuation_row(
                        self._goal_continuation_row(parent_row) if parent_row is not None else None,
                        episode_id=parent_episode,
                    )
                    max_no_progress = int(parent["policy"].get("max_no_progress") or 0)
                    if max_no_progress < 1:
                        raise RunContinuationError(
                            "GOAL_CONTINUATION_POLICY_INVALID",
                            "Goal continuation no-progress threshold is missing or invalid.",
                        )
                    if observation_outcome == "progress":
                        next_no_progress = 0
                    else:
                        next_no_progress = min(int(parent["no_progress_count"]) + 1, max_no_progress)
                    stopped = observation_outcome == "no_progress" and next_no_progress >= max_no_progress
                    connection.execute(
                        """INSERT INTO goal_continuation_observations(
                               observation_id,episode_id,run_id,action_id,outcome,proof_identity_sha256,created_at
                           ) VALUES(?,?,?,?,?,?,?)""",
                        (observation_id, parent_episode, normalized_run, normalized_action, observation_outcome, proof_identity, now),
                    )
                    if stopped:
                        connection.execute(
                            "UPDATE goal_continuations SET enabled=0,pause_reason=?,no_progress_count=?,updated_at=? WHERE episode_id=?",
                            (GOAL_CONTINUATION_NO_PROGRESS, next_no_progress, now, parent_episode),
                        )
                    else:
                        connection.execute(
                            "UPDATE goal_continuations SET no_progress_count=?,updated_at=? WHERE episode_id=?",
                            (next_no_progress, now, parent_episode),
                        )
                    self._append_run_continuation_event(
                        connection,
                        run_id=normalized_run,
                        event_type="goal_continuation_proof_observed",
                        payload={
                            "episode_id": parent_episode,
                            "observation_id": observation_id,
                            "outcome": observation_outcome,
                            "proof_identity_sha256": proof_identity,
                            "no_progress_count": next_no_progress,
                            "max_no_progress": max_no_progress,
                            "stopped": stopped,
                            "reason": GOAL_CONTINUATION_NO_PROGRESS if stopped else "",
                        },
                    )
                    goal_observation = {
                        "observation_id": observation_id,
                        "outcome": observation_outcome,
                        "idempotent": False,
                        "no_progress_count": next_no_progress,
                        "stopped": stopped,
                        "reason": GOAL_CONTINUATION_NO_PROGRESS if stopped else "",
                    }
            connection.execute(
                """UPDATE run_continuations
                   SET pending_action_id='',pending_evidence_hash='',pending_evidence_paths_json='[]',pending_replan_json='{}',pending_dispatch_action_id='',pending_job_id='',pending_patch_action_id='',consumed_event_seq=MAX(consumed_event_seq,?),updated_at=? WHERE run_id=?""",
                (consumed_event_seq, now, normalized_run),
            )
            self._append_run_continuation_event(
                connection,
                run_id=normalized_run,
                event_type="run_continuation_action_completed",
                payload={"action_id": normalized_action, "driver_generation": driver_generation, "consumed_event_seq": consumed_event_seq},
            )
            updated = connection.execute("SELECT * FROM run_continuations WHERE run_id=?", (normalized_run,)).fetchone()
            connection.commit()
        assert updated is not None
        continuation = self._run_continuation_row(updated)
        continuation["policy"] = _policy_projection(continuation["policy"])
        if goal_observation is not None:
            continuation["goal_observation"] = goal_observation
        return continuation

    def consume_run_continuation_patch_attempt(
        self,
        *,
        run_id: str,
        driver_generation: int,
        runtime_instance_id: str,
        action_id: str,
    ) -> dict[str, Any]:
        """Atomically spend one PATCH budget unit for one exact pending action."""
        normalized_run = _require_opaque(run_id, "run_id")
        normalized_action = _require_sha256(action_id, "action_id")
        now = _utc_now()
        with self._lock, self._connect() as connection:
            self._run_continuation_ensure_schema(connection)
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT * FROM run_continuations WHERE run_id=?", (normalized_run,)).fetchone()
            record = self._run_continuation_row(row) if row is not None else None
            record = self._assert_run_continuation_row(
                record,
                run_id=normalized_run,
                driver_generation=driver_generation,
                runtime_instance_id=runtime_instance_id,
                connection=connection,
            )
            if record["pending_action_id"] != normalized_action:
                raise RunContinuationError("RUN_CONTINUATION_ACTION_MISMATCH", "Only the exact pending action may spend a PATCH attempt.")
            spent_for = str(record["pending_patch_action_id"] or "")
            if spent_for:
                if spent_for != normalized_action:
                    raise RunContinuationError("RUN_CONTINUATION_PATCH_ATTEMPT_CONFLICT", "A different PATCH attempt is already bound to the pending action.")
                connection.commit()
                record["policy"] = _policy_projection(record["policy"])
                return {"consumed": False, "idempotent": True, "continuation": record}
            parent_episode = str(record.get("parent_episode_id") or "")
            parent = None
            remaining_patch_attempts = int(record["remaining_patch_attempts"])
            if parent_episode:
                parent = self._assert_goal_continuation_row(
                    self._goal_continuation_get_raw(parent_episode, connection=connection),
                    episode_id=parent_episode,
                )
                remaining_patch_attempts = int(parent["remaining_patch_attempts"])
            if remaining_patch_attempts < 1:
                raise RunContinuationError("RUN_CONTINUATION_PATCH_BUDGET_EXHAUSTED", "No continuation PATCH attempts remain.")
            next_remaining_patch_attempts = remaining_patch_attempts - 1
            if parent is not None:
                connection.execute(
                    "UPDATE goal_continuations SET remaining_patch_attempts=?,updated_at=? WHERE episode_id=?",
                    (next_remaining_patch_attempts, now, parent_episode),
                )
            connection.execute(
                "UPDATE run_continuations SET pending_patch_action_id=?,remaining_patch_attempts=?,updated_at=? WHERE run_id=?",
                (normalized_action, next_remaining_patch_attempts, now, normalized_run),
            )
            self._append_run_continuation_event(
                connection,
                run_id=normalized_run,
                event_type="run_continuation_patch_attempt_consumed",
                payload={"action_id": normalized_action, "driver_generation": driver_generation, "parent_episode_id": parent_episode, "remaining_patch_attempts": next_remaining_patch_attempts},
            )
            updated = connection.execute("SELECT * FROM run_continuations WHERE run_id=?", (normalized_run,)).fetchone()
            connection.commit()
        assert updated is not None
        continuation = self._run_continuation_row(updated)
        continuation["policy"] = _policy_projection(continuation["policy"])
        return {"consumed": True, "idempotent": False, "continuation": continuation}

    def set_run_continuation_state(
        self,
        *,
        run_id: str,
        action: str,
        reason: str = "",
    ) -> dict[str, Any]:
        normalized_run = _require_opaque(run_id, "run_id")
        operation = _bounded(action, 32).lower()
        if operation not in {"pause", "resume", "revoke"}:
            raise RunContinuationError("RUN_CONTINUATION_CONTROL_INVALID", "Unsupported continuation control action.")
        bounded_reason = _bounded(reason, 512)
        now = _utc_now()
        with self._lock, self._connect() as connection:
            self._run_continuation_ensure_schema(connection)
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT * FROM run_continuations WHERE run_id=?", (normalized_run,)).fetchone()
            record = self._run_continuation_row(row) if row is not None else None
            if record is None:
                raise RunContinuationError("RUN_CONTINUATION_GRANT_REQUIRED", "No continuation grant exists for this RUN.")
            if operation == "resume" and record["revoked_at"]:
                raise RunContinuationError("RUN_CONTINUATION_REVOKED", "A revoked grant cannot be resumed; issue a new immutable grant.")
            enabled = 1 if operation == "resume" else 0
            revoked_at = now if operation == "revoke" else record["revoked_at"]
            pause_reason = "" if operation == "resume" else (bounded_reason or operation)
            next_generation = int(record["driver_generation"]) + 1
            connection.execute(
                """UPDATE run_continuations
                   SET enabled=?,pause_reason=?,revoked_at=?,driver_generation=?,claimed_runtime_instance='',
                       claim_expires_at_unix_ms=0,updated_at=? WHERE run_id=?""",
                (enabled, pause_reason, revoked_at, next_generation, now, normalized_run),
            )
            self._append_run_continuation_event(
                connection,
                run_id=normalized_run,
                event_type=f"run_continuation_{operation}d" if operation != "revoke" else "run_continuation_revoked",
                payload={"reason": pause_reason, "driver_generation": next_generation, "pending_action": bool(record["pending_action_id"]), "pending_job": bool(record["pending_job_id"])},
            )
            updated = connection.execute("SELECT * FROM run_continuations WHERE run_id=?", (normalized_run,)).fetchone()
            connection.commit()
        assert updated is not None
        result = self._run_continuation_row(updated)
        result["policy"] = _policy_projection(result["policy"])
        return result

    def set_run_continuation_dispatch(
        self,
        *,
        run_id: str,
        driver_generation: int,
        runtime_instance_id: str,
        action_id: str,
        lane_id: str,
        thread_id: str,
        turn_id: str,
        session_id: str = "",
    ) -> dict[str, Any]:
        """Persist the exact no-tools lane/turn selected for one pending action."""
        normalized_run = _require_opaque(run_id, "run_id")
        normalized_action = _require_sha256(action_id, "action_id")
        lane = _require_opaque(lane_id, "lane_id")
        thread = _require_opaque(thread_id, "thread_id")
        turn = _require_opaque(turn_id, "turn_id")
        session = _require_opaque(session_id, "session_id") if session_id else ""
        now = _utc_now()
        with self._lock, self._connect() as connection:
            self._run_continuation_ensure_schema(connection)
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT * FROM run_continuations WHERE run_id=?", (normalized_run,)).fetchone()
            record = self._run_continuation_row(row) if row is not None else None
            record = self._assert_run_continuation_row(
                record,
                run_id=normalized_run,
                driver_generation=driver_generation,
                runtime_instance_id=runtime_instance_id,
            )
            if record["pending_action_id"] != normalized_action:
                raise RunContinuationError("RUN_CONTINUATION_ACTION_MISMATCH", "Only the exact pending action may bind a model dispatch.")
            existing_action = str(record["pending_dispatch_action_id"])
            if existing_action:
                existing = (record["lane_id"], record["thread_id"], record["thread_session_id"], record["last_turn_id"])
                requested = (lane, thread, session or record["thread_session_id"], turn)
                if existing_action != normalized_action or existing != requested:
                    raise RunContinuationError("RUN_CONTINUATION_DISPATCH_PENDING", "A different model dispatch is already recorded for the pending action.")
                connection.commit()
                record["policy"] = _policy_projection(record["policy"])
                return record
            if record["lane_id"] and record["lane_id"] != lane:
                raise RunContinuationError("RUN_CONTINUATION_DISPATCH_PENDING", "The continuation lane identity cannot change while the grant is active.")
            if record["thread_id"] and record["thread_id"] != thread:
                raise RunContinuationError("RUN_CONTINUATION_DISPATCH_PENDING", "The continuation thread identity cannot change while the grant is active.")
            if record["thread_session_id"] and session and record["thread_session_id"] != session:
                raise RunContinuationError("RUN_CONTINUATION_DISPATCH_PENDING", "The continuation thread session identity cannot change while the grant is active.")
            connection.execute(
                "UPDATE run_continuations SET lane_id=?,thread_id=?,thread_session_id=CASE WHEN ?<>'' THEN ? ELSE thread_session_id END,last_turn_id=?,pending_dispatch_action_id=?,updated_at=? WHERE run_id=?",
                (lane, thread, session, session, turn, normalized_action, now, normalized_run),
            )
            self._append_run_continuation_event(
                connection,
                run_id=normalized_run,
                event_type="run_continuation_dispatch_recorded",
                payload={"action_id": normalized_action, "driver_generation": driver_generation, "lane_id": lane, "thread_id": thread, "session_id": session or record["thread_session_id"], "turn_id": turn},
            )
            updated = connection.execute("SELECT * FROM run_continuations WHERE run_id=?", (normalized_run,)).fetchone()
            connection.commit()
        assert updated is not None
        result = self._run_continuation_row(updated)
        result["policy"] = _policy_projection(result["policy"])
        return result

    def set_run_continuation_pending_job(
        self,
        *,
        run_id: str,
        driver_generation: int,
        runtime_instance_id: str,
        action_id: str,
        job_id: str = "",
    ) -> dict[str, Any]:
        """Bind the exact managed proof Job to a pending action, or clear it after terminal observation.

        The managed-process ledger is the lifecycle authority for the process
        itself. This projection is only the continuation cursor that prevents a
        later driver from assuming a missing/unknown proof command is safe to
        repeat.
        """
        normalized_run = _require_opaque(run_id, "run_id")
        normalized_action = _require_sha256(action_id, "action_id")
        normalized_job = _require_opaque(job_id, "job_id") if job_id else ""
        now = _utc_now()
        with self._lock, self._connect() as connection:
            self._run_continuation_ensure_schema(connection)
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT * FROM run_continuations WHERE run_id=?", (normalized_run,)).fetchone()
            record = self._run_continuation_row(row) if row is not None else None
            record = self._assert_run_continuation_row(
                record,
                run_id=normalized_run,
                driver_generation=driver_generation,
                runtime_instance_id=runtime_instance_id,
            )
            if record["pending_action_id"] != normalized_action:
                raise RunContinuationError("RUN_CONTINUATION_ACTION_MISMATCH", "Only the exact pending action may bind a managed proof Job.")
            existing = str(record["pending_job_id"])
            if existing and normalized_job and existing != normalized_job:
                raise RunContinuationError("RUN_CONTINUATION_JOB_PENDING", "A different managed proof Job is already pending for this action.")
            if existing == normalized_job:
                connection.commit()
                record["policy"] = _policy_projection(record["policy"])
                return record
            connection.execute(
                "UPDATE run_continuations SET pending_job_id=?,updated_at=? WHERE run_id=?",
                (normalized_job, now, normalized_run),
            )
            self._append_run_continuation_event(
                connection,
                run_id=normalized_run,
                event_type="run_continuation_check_job_bound" if normalized_job else "run_continuation_check_job_cleared",
                payload={"action_id": normalized_action, "driver_generation": driver_generation, "job_id": normalized_job},
            )
            updated = connection.execute("SELECT * FROM run_continuations WHERE run_id=?", (normalized_run,)).fetchone()
            connection.commit()
        assert updated is not None
        result = self._run_continuation_row(updated)
        result["policy"] = _policy_projection(result["policy"])
        return result


