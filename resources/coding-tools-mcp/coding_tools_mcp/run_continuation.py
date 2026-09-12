from __future__ import annotations

"""Bounded durable execution ledger cursor and runtime driver for an existing RUN.

Immutable proposal, scope, policy, and consent validation live in
continuation_contract.py. This module owns only durable continuation state,
driver fencing, and the runtime-facing continuation flow.
"""

import hashlib
import json
import sqlite3
from typing import Any, Iterable

from .continuation_contract import (
    RUN_CONTINUATION_LEASE_SECONDS,
    RUN_CONTINUATION_MAX_NEW_FILES,
    RUN_CONTINUATION_MAX_REPLACEMENTS,
    RUN_CONTINUATION_PROPOSAL_SCHEMA,
    RUN_CONTINUATION_PROFILE,
    RUN_CONTINUATION_ROUTE,
    RUN_CONTINUATION_SCHEMA_VERSION,
    RunContinuationError,
    _bounded,
    _canonical_json,
    _contains_sensitive_model_content,
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
    bind_run_continuation_consent,
    build_run_continuation_policy,
    continuation_consent_descriptor,
    parse_run_continuation_proposal,
)
from .errors import ToolFailure
from .continuation_consent_http import CONTINUATION_CONSENT_HTTP_PATH
from .host_correlation import (
    claim_pending_continuation_consent,
    consume_pending_continuation_consent,
    restore_pending_continuation_consent,
)
from .ledger_event_chain import append_hash_chained_event


class RunContinuationLedgerMixin:
    """Same-ledger grant/cursor projection used by the continuation driver."""

    @staticmethod
    def _run_continuation_ensure_schema(connection: sqlite3.Connection) -> None:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS run_continuations (
                run_id TEXT PRIMARY KEY REFERENCES runs(run_id) ON DELETE CASCADE,
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
                       SET workspace_id=?,problem_id=?,problem_revision=?,policy_json=?,policy_sha256=?,issuer_receipt_sha256=?,
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
    ) -> dict[str, Any]:
        if record is None:
            raise RunContinuationError("RUN_CONTINUATION_GRANT_REQUIRED", "No durable execution grant exists for this RUN.")
        now_ms = _now_ms() if now_unix_ms is None else int(now_unix_ms)
        if not record["enabled"] or record["revoked_at"]:
            raise RunContinuationError("RUN_CONTINUATION_REVOKED", "The continuation grant is revoked or disabled.")
        if now_ms >= int(record["expires_at_unix_ms"]):
            raise RunContinuationError("RUN_CONTINUATION_EXPIRED", "The continuation grant has expired.")
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
            )
            allowed_reads = set(record["policy"].get("read_paths") or [])
            denied_evidence_paths = sorted(set(normalized_evidence_paths).difference(allowed_reads))
            if denied_evidence_paths:
                raise RunContinuationError(
                    "RUN_CONTINUATION_READ_SCOPE_DENIED",
                    "An evidence packet includes a path outside the immutable continuation read scope.",
                    details={"paths": denied_evidence_paths},
                )
            if int(record["remaining_decision_turns"]) < 1:
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
            connection.execute(
                """UPDATE run_continuations
                   SET pending_action_id=?,pending_evidence_hash=?,pending_evidence_paths_json=?,pending_replan_json=?,pending_dispatch_action_id='',pending_job_id='',pending_patch_action_id='',next_action_seq=?,remaining_decision_turns=remaining_decision_turns-1,updated_at=?
                   WHERE run_id=?""",
                (action_id, evidence_digest, _canonical_json(normalized_evidence_paths), _canonical_json(normalized_replan), current_seq + 1, now, normalized_run),
            )
            self._append_run_continuation_event(
                connection,
                run_id=normalized_run,
                event_type="run_continuation_action_reserved",
                payload={"action_id": action_id, "action_seq": current_seq, "action_kind": kind, "driver_generation": driver_generation, "request_hash": request_digest, "evidence_hash": evidence_digest, "evidence_path_count": len(normalized_evidence_paths), "technical_replan": bool(normalized_replan)},
            )
            updated = connection.execute("SELECT * FROM run_continuations WHERE run_id=?", (normalized_run,)).fetchone()
            connection.commit()
        assert updated is not None
        continuation = self._run_continuation_row(updated)
        continuation["policy"] = _policy_projection(continuation["policy"])
        return {"reserved": True, "idempotent": False, "action_id": action_id, "continuation": continuation}

    def complete_run_continuation_action(
        self,
        *,
        run_id: str,
        driver_generation: int,
        runtime_instance_id: str,
        action_id: str,
        consumed_event_seq: int = 0,
    ) -> dict[str, Any]:
        normalized_run = _require_opaque(run_id, "run_id")
        normalized_action = _require_sha256(action_id, "action_id")
        if isinstance(consumed_event_seq, bool) or not isinstance(consumed_event_seq, int) or consumed_event_seq < 0:
            raise RunContinuationError("RUN_CONTINUATION_ACTION_INVALID", "consumed_event_seq must be non-negative.")
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
                raise RunContinuationError("RUN_CONTINUATION_ACTION_MISMATCH", "Only the exact pending action can advance the continuation cursor.")
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
            if int(record["remaining_patch_attempts"]) < 1:
                raise RunContinuationError("RUN_CONTINUATION_PATCH_BUDGET_EXHAUSTED", "No continuation PATCH attempts remain.")
            connection.execute(
                "UPDATE run_continuations SET pending_patch_action_id=?,remaining_patch_attempts=remaining_patch_attempts-1,updated_at=? WHERE run_id=?",
                (normalized_action, now, normalized_run),
            )
            self._append_run_continuation_event(
                connection,
                run_id=normalized_run,
                event_type="run_continuation_patch_attempt_consumed",
                payload={"action_id": normalized_action, "driver_generation": driver_generation},
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


class RunContinuationMixin:
    """Grant/control hooks; the separated driver owns model observation and effects."""

    def _run_continuation_value(self, args: dict[str, Any], *, workflow: str, phase: str) -> str | dict[str, Any]:
        raw = args.get("continuation")
        if isinstance(raw, dict):
            return self._run_continuation_grant(args, raw)
        if raw is not None and not isinstance(raw, str):
            raise ToolFailure(
                "INVALID_ARGUMENT",
                "agent_workflow continuation must be either the legacy source-fenced token or an explicit continuation grant request object.",
                category="validation",
            )
        return str(raw or "").strip()

    @staticmethod
    def _run_continuation_tool_failure(exc: RunContinuationError) -> ToolFailure:
        return ToolFailure(exc.code, str(exc), category="security" if "DENIED" in exc.code or "REQUIRED" in exc.code else "validation", retryable=exc.retryable, details=exc.details)

    def _run_continuation_http_challenge(
        self,
        *,
        policy: dict[str, Any],
        controller: dict[str, Any],
        descriptor: dict[str, Any],
    ) -> dict[str, Any]:
        """Issue a local approval only for the current attested ChatWeb turn."""
        host_turn = self._attested_chatweb_transport_turn()
        origin = str(getattr(self, "run_continuation_consent_http_origin", "") or "").rstrip("/")
        store = getattr(self, "run_continuation_consent_challenges", None)
        if host_turn is None or not origin or store is None:
            return {}
        issued = store.issue(
            descriptor=descriptor,
            policy=policy,
            controller=controller,
            host_turn=host_turn,
        )
        return {
            "approval_url": f"{origin}{CONTINUATION_CONSENT_HTTP_PATH}#{issued['token']}",
            "approval_challenge_id": issued["challenge_id"],
            "approval_descriptor_sha256": issued["descriptor_sha256"],
            "approval_expires_at_unix_ms": issued["expires_at_unix_ms"],
            "approval_behavior": "A local explicit button press grants and starts this exact bounded continuation. The page is unavailable through the managed tunnel, and its one-shot token is never sent in the URL request target.",
        }

    def _run_continuation_approve_http_challenge(self, approved: dict[str, Any]) -> dict[str, Any]:
        """Finalize one loopback approval without borrowing a later ChatWeb turn."""
        policy = approved.get("policy") if isinstance(approved.get("policy"), dict) else {}
        receipt = approved.get("receipt") if isinstance(approved.get("receipt"), dict) else {}
        controller = approved.get("controller") if isinstance(approved.get("controller"), dict) else {}
        run_id = str(policy.get("run_id") or "").strip()
        if not run_id:
            raise ToolFailure("RUN_CONTINUATION_APPROVAL_INVALID", "The local approval has no exact RUN binding.", category="security")
        try:
            bound_policy = bind_run_continuation_consent(policy, receipt)
        except RunContinuationError as exc:
            raise self._run_continuation_tool_failure(exc) from exc
        self._run_continuation_assert_runtime(bound_policy)
        current_ctx = self.orchestration_control.snapshot(run_id)
        if current_ctx is None or str(current_ctx.wave_id) != str(bound_policy.get("grant_wave_id") or ""):
            raise ToolFailure("RUN_CONTINUATION_WAVE_STALE", "The RUN/WAVE changed before local approval.", category="security")
        current_controller = self.orchestration_ledger.peek_controller_lease(run_id) or {}
        if (
            str(current_controller.get("status") or "") == "active"
            and (
                str(current_controller.get("owner_client_id") or "") != str(controller.get("owner_client_id") or "")
                or int(current_controller.get("fencing_token") or 0) != int(controller.get("fencing_token") or 0)
            )
        ):
            raise ToolFailure("RUN_CONTINUATION_CONTROLLER_CHANGED", "Controller authority changed after the approval challenge was issued.", category="security")
        issuer_receipt = hashlib.sha256(
            _canonical_json({
                "run_id": run_id,
                "controller_lease_id": controller.get("lease_id"),
                "controller_fencing_token": controller.get("fencing_token"),
                "controller_client_id": str(bound_policy.get("issuer_client_id") or ""),
                "tool_contract_sha256": self.tool_contract.get("sha256"),
                "consent_receipt_id": receipt.get("receipt_id"),
                "consent_scope_sha256": continuation_consent_descriptor(bound_policy)["scope_sha256"],
            }).encode("utf-8")
        ).hexdigest()
        try:
            issued = self.orchestration_ledger.issue_run_continuation(
                run_id=run_id,
                policy=bound_policy,
                issuer_receipt_sha256=issuer_receipt,
            )
        except RunContinuationError as exc:
            raise self._run_continuation_tool_failure(exc) from exc
        self._project_orchestration(current_ctx, event="run_continuation_granted")
        try:
            started = self._run_continuation_start_driver({"run_id": run_id})
        except ToolFailure as exc:
            return {
                "run_id": run_id,
                "status": "GRANTED_NOT_STARTED",
                "grant_status": issued.get("status"),
                "code": exc.code,
                "message": exc.message,
            }
        return {**started, "grant_status": issued.get("status"), "approval_challenge_id": approved.get("challenge_id")}

    def _run_continuation_grant(self, args: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
        workflow = str(args.get("workflow") or "custom").strip().lower()
        phase = str(args.get("phase") or "prepare").strip().lower()
        if phase != "prepare" or workflow not in {"bugfix", "feature"}:
            raise ToolFailure(
                "RUN_CONTINUATION_GRANT_PHASE_INVALID",
                "A continuation grant is explicit preflight authority for a bounded bugfix or feature RUN; it cannot be attached to arbitrary execution/resume phases.",
                category="validation",
            )
        objective = str(args.get("objective") or self.task_state.get().get("objective") or "").strip()
        if not objective:
            raise ToolFailure("RUN_CONTINUATION_OBJECTIVE_REQUIRED", "A continuation grant requires a non-empty existing RUN objective.", category="validation")
        ctx, identity = self._agent_orchestration_context(args, objective=objective)
        controller = self._require_hub_controller(ctx.run_id)
        if controller is None:
            raise ToolFailure(
                "RUN_CONTINUATION_CONTROLLER_REQUIRED",
                "A background continuation grant is denied without the authenticated active ChatWeb controller; missing identity is never a trusted-local bypass.",
                category="security",
            )
        hub = self._current_hub_client() or {}
        if (
            str(hub.get("client_type") or "") != "chatweb"
            or str(hub.get("role") or "") != "controller"
            or str(hub.get("identity_source") or "") != "attested_transport"
            or hub.get("attestation_verified") is not True
        ):
            raise ToolFailure(
                "RUN_CONTINUATION_CONTROLLER_ATTESTATION_REQUIRED",
                "A continuation grant requires an attested ChatWeb controller identity, not a copied hub_client object.",
                category="security",
            )
        binding = self.orchestration_ledger.controller_run_problem_binding(ctx.run_id)
        if not isinstance(binding, dict):
            raise ToolFailure(
                "RUN_CONTINUATION_PROBLEM_BINDING_REQUIRED",
                "A continuation grant must bind exactly one current Problem Revision to its RUN.",
                category="security",
            )
        workspace_identity = identity.get("workspace_identity") if isinstance(identity.get("workspace_identity"), dict) else {}
        workspace_id = str(workspace_identity.get("workspace_id") or "").strip()
        if not workspace_id:
            raise ToolFailure("RUN_CONTINUATION_WORKSPACE_REQUIRED", "The current workspace identity is unavailable; grant issuance fails closed.", category="security")
        loaded_identity = self._loaded_behavior_identity()
        admission = self.activation_admission_snapshot()
        admission_state = str(admission.get("admission") or "").lower()
        epoch_id = str(admission.get("activation_epoch_id") or "").strip()
        if admission_state != "open" or not epoch_id:
            raise ToolFailure(
                "RUN_CONTINUATION_ADMISSION_REQUIRED",
                "Continuation grants require a currently admitted runtime epoch; partial startup and stale connector state cannot be used as authority.",
                category="runtime",
                details={"activation": admission},
            )
        claimed_consent: dict[str, Any] | None = None
        try:
            policy = build_run_continuation_policy(
                request,
                run_id=ctx.run_id,
                workspace_id=workspace_id,
                problem_id=str(binding.get("problem_id") or ""),
                problem_revision=int(binding.get("problem_revision") or 0),
                contract_fingerprint=ctx.contract_fp,
                tool_contract_sha256=str(self.tool_contract.get("sha256") or ""),
                runtime_behavior_fingerprint=str(loaded_identity.get("fingerprint") or ""),
                activation_epoch_id=epoch_id,
                activation_admission=admission_state,
                issuer_client_id=self._hub_client_record_id(hub),
                wave_id=ctx.wave_id,
            )
            consent_descriptor = continuation_consent_descriptor(policy)
            current_environment_hash = self._run_continuation_environment_hash()
            mismatched_checks = [
                str(item.get("check_id") or "")
                for item in policy.get("approved_checks") or []
                if isinstance(item, dict) and str(item.get("environment_hash") or "") != current_environment_hash
            ]
            if mismatched_checks:
                raise ToolFailure(
                    "RUN_CONTINUATION_ENVIRONMENT_MISMATCH",
                    "Each immutable approved check must bind the currently admitted continuation execution environment.",
                    category="validation",
                    details={"check_ids": mismatched_checks, "current_environment_hash": current_environment_hash},
                )
            claimed_consent = claim_pending_continuation_consent(
                self.workspace.root,
                process_instance_id=self.process_instance_id,
                expected_descriptor=consent_descriptor,
            )
            if claimed_consent is None:
                approval = self._run_continuation_http_challenge(
                    policy=policy,
                    controller=controller,
                    descriptor=consent_descriptor,
                )
                raise ToolFailure(
                    "RUN_CONTINUATION_CONSENT_REQUIRED",
                    "No current exact host receipt authorizes this bounded background continuation. A visible user turn is provenance only, not consent.",
                    category="security",
                    details={
                        "continuation_consent_request": consent_descriptor,
                        "user_command": "/coding-tools-continue-consent " + _canonical_json(consent_descriptor),
                        **approval,
                    },
                )
            policy = bind_run_continuation_consent(policy, claimed_consent)
            issuer_receipt = hashlib.sha256(
                _canonical_json({
                    "run_id": ctx.run_id,
                    "controller_lease_id": controller.get("lease_id"),
                    "controller_fencing_token": controller.get("fencing_token"),
                    "controller_client_id": self._hub_client_record_id(hub),
                    "tool_contract_sha256": self.tool_contract.get("sha256"),
                    "consent_receipt_id": claimed_consent["receipt_id"],
                    "consent_scope_sha256": consent_descriptor["scope_sha256"],
                }).encode("utf-8")
            ).hexdigest()
            issued = self.orchestration_ledger.issue_run_continuation(
                run_id=ctx.run_id,
                policy=policy,
                issuer_receipt_sha256=issuer_receipt,
            )
        except RunContinuationError as exc:
            if claimed_consent is not None:
                restore_pending_continuation_consent(self.workspace.root, claimed_consent)
            raise self._run_continuation_tool_failure(exc) from exc
        except ToolFailure:
            if claimed_consent is not None:
                restore_pending_continuation_consent(self.workspace.root, claimed_consent)
            raise
        else:
            assert claimed_consent is not None
            consume_pending_continuation_consent(claimed_consent)
        self._project_orchestration(ctx, event="run_continuation_granted")
        return {
            "workflow": workflow,
            "phase": "prepare",
            "continuation": issued,
            "orchestration": self._orchestration_result(ctx),
            "task": self.task_state.get(),
            "recommended_next_action": "The grant is durable and binds the current continuation execution environment. Start it explicitly through task_control action=run_continuation/run_continuation_action=start; MCP, not the model, will then own exact dispatch observation, mutation, proof, and the technical ACCEPTING transition.",
        }

    def _run_continuation_canonical_evidence(
        self,
        policy: dict[str, Any],
        *,
        objective: str,
        selected_read_paths: Iterable[str] = (),
        technical_replan: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], str]:
        """Create the content-bounded packet that a no-tools model may reason over."""
        revision = self.orchestration_ledger.problem_get_exact_revision(
            str(policy["problem_id"]),
            int(policy["problem_revision"]),
            expected_contract_fingerprint=str(policy["contract_fingerprint"]),
        )
        capsule = revision.get("capsule") if isinstance(revision.get("capsule"), dict) else None
        if capsule is None:
            raise ToolFailure("RUN_CONTINUATION_PROBLEM_CONTEXT_INVALID", "The exact bound Problem Revision has no valid contract capsule.", category="runtime")
        if _contains_sensitive_model_content(objective) or _contains_sensitive_model_content(capsule):
            raise ToolFailure(
                "RUN_CONTINUATION_EVIDENCE_SENSITIVE",
                "Problem material contains sensitive-like content and cannot be sent to a continuation proposal model.",
                category="security",
            )
        root = self.workspace.root.resolve(strict=False)
        allowed_read_paths = [_normalize_path(path, "read scope") for path in policy.get("read_paths") or []]
        requested_read_paths = _normalize_paths(list(selected_read_paths), "selected_read_paths")
        denied_read_paths = sorted(set(requested_read_paths).difference(allowed_read_paths))
        if denied_read_paths:
            raise ToolFailure(
                "RUN_CONTINUATION_READ_SCOPE_DENIED",
                "The requested continuation evidence is outside the immutable read scope.",
                category="security",
                details={"paths": denied_read_paths},
            )
        files: list[dict[str, str]] = []
        for path in requested_read_paths:
            normalized = _normalize_path(path, "read scope")
            target = (root / normalized).resolve(strict=False)
            if not target.is_relative_to(root) or not target.is_file():
                raise ToolFailure("RUN_CONTINUATION_EVIDENCE_UNAVAILABLE", "A granted read path is not a current workspace file.", category="runtime", details={"path": normalized})
            try:
                text = target.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                raise ToolFailure("RUN_CONTINUATION_EVIDENCE_UNAVAILABLE", "A granted read path could not be read as UTF-8.", category="runtime", details={"path": normalized}) from exc
            if len(text.encode("utf-8")) > 48_000:
                raise ToolFailure("RUN_CONTINUATION_EVIDENCE_TOO_LARGE", "A granted read path exceeds the bounded continuation packet limit.", category="validation", details={"path": normalized})
            if _contains_sensitive_model_content(text):
                raise ToolFailure(
                    "RUN_CONTINUATION_EVIDENCE_SENSITIVE",
                    "A granted read path contains sensitive-like content and cannot be sent to a continuation proposal model.",
                    category="security",
                    details={"path": normalized},
                )
            files.append({"path": normalized, "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(), "content": text})
        identity = self._orchestration_workspace_identity(".")
        evidence = {
            "schema_version": 1,
            "objective": _bounded(objective, 2_000),
            "problem_contract": capsule,
            "read_files": files,
            "available_read_paths": allowed_read_paths,
            "write_paths": list(policy.get("write_paths") or []),
            "protected_paths": list(policy.get("protected_paths") or []),
            "approved_check_hashes": [str(item.get("definition_hash") or "") for item in policy.get("approved_checks") or [] if isinstance(item, dict)],
            "source_identity": {"base_head": identity.get("base_head"), "worktree_fp": identity.get("worktree_fp")},
        }
        normalized_replan = _normalize_technical_replan(technical_replan)
        if normalized_replan:
            if _contains_sensitive_model_content(normalized_replan):
                raise ToolFailure(
                    "RUN_CONTINUATION_EVIDENCE_SENSITIVE",
                    "Technical replan material contains sensitive-like content and cannot be sent to a continuation proposal model.",
                    category="security",
                )
            evidence["technical_replan"] = normalized_replan
        digest = hashlib.sha256(_canonical_json(evidence).encode("utf-8")).hexdigest()
        return evidence, digest

    def _run_continuation_prompt(self, *, policy: dict[str, Any], evidence: dict[str, Any], evidence_hash: str) -> str:
        packet = {
            "continuation_contract": {
                "route": policy.get("route"),
                "profile": policy.get("profile"),
                "acceptance_mode": policy.get("acceptance_mode"),
                "instruction": "Choose exactly one proposal kind: READ, PATCH, READY, or BLOCKED. Never ask for expanded scope, a new check, a new budget, or authority. Copy evidence_hash exactly.",
                # The observed App Server profile fails a turn when supplied
                # an outputSchema. The response remains typed at the MCP
                # boundary: this inline contract plus
                # parse_run_continuation_proposal() rejects every malformed,
                # stale, out-of-scope, or incomplete proposal before any
                # effect is possible.
                "response_encoding": {
                    "format": "the entire response must be one JSON object: begin with {, end with }, and contain no Markdown, code fence, label, or surrounding prose; invalid JSON is rejected without an effect",
                    "canonical_json_schema": RUN_CONTINUATION_PROPOSAL_SCHEMA,
                    "policy_rules": [
                        "The JSON Schema is part of this prompt, not a provider outputSchema; it defines every nested object and forbids extra fields.",
                        "READ paths must be distinct values from evidence.available_read_paths.",
                        "PATCH replacement and new-file paths must be in evidence.write_paths and outside evidence.protected_paths; every replacement old value must be the exact current preimage.",
                        "PATCH must include at least one replacement or new file and selected_check_hashes must contain every distinct value in evidence.approved_check_hashes exactly once.",
                    ],
                },
            },
            "evidence_hash": evidence_hash,
            "evidence": evidence,
        }
        return "Bounded durable continuation packet:\n" + _canonical_json(packet)

    def _run_continuation_start_driver(self, args: dict[str, Any]) -> dict[str, Any]:
        run_id = str(args.get("run_id") or "").strip()
        if not run_id:
            projection = self.task_state.get().get("orchestration")
            run_id = str((projection or {}).get("run_id") or "") if isinstance(projection, dict) else ""
        if not run_id:
            raise ToolFailure("ORCHESTRATION_RUN_NOT_FOUND", "run_id is required to start a continuation driver.", category="not_found")
        record = self.orchestration_ledger._run_continuation_get_raw(run_id)
        if record is None:
            raise ToolFailure("RUN_CONTINUATION_GRANT_REQUIRED", "A continuation driver requires a prior immutable grant.", category="security")
        policy = record["policy"]
        if record.get("pending_action_id") or record.get("pending_job_id") or record.get("pending_patch_action_id"):
            self._run_continuation_fail_closed_pause(run_id, "restart_pending_dispatch_or_effect_requires_reconciliation")
            raise ToolFailure(
                "RUN_CONTINUATION_RECOVERY_RECONCILE_REQUIRED",
                "A prior continuation dispatch, proof Job, or effect is still pending. Do not resume the App Server lane or start another turn; reconcile the exact pending outcome first.",
                category="runtime",
            )
        try:
            # Dispatch is an externally observable continuation boundary.  Do
            # not claim a driver or start a model turn under an old admitted
            # runtime, behavior fingerprint, base/worktree, or RUN context.
            self._run_continuation_assert_runtime(policy)
            ctx, _identity = self._run_continuation_context(record)
            admission_before_claim = self.activation_admission_snapshot()
            epoch_changed = (
                str(admission_before_claim.get("activation_epoch_id") or "")
                != str(policy.get("activation_epoch_id") or "")
            )
            wave_changed = str(ctx.wave_id) != str(policy.get("grant_wave_id") or "")
            if record.get("thread_id") and (epoch_changed or wave_changed):
                try:
                    self._run_continuation_validate_execution_rebind(record, ctx)
                except ToolFailure as exc:
                    code = "RUN_CONTINUATION_EPOCH_STALE" if epoch_changed else "RUN_CONTINUATION_WAVE_STALE"
                    raise RunContinuationError(code, str(exc)) from exc
            claim = self.orchestration_ledger.claim_run_continuation(
                run_id=run_id,
                runtime_instance_id=self._run_continuation_runtime_instance_id(),
                expected_generation=int(record["driver_generation"]),
            )
            if not claim.get("claimed"):
                raise RunContinuationError("RUN_CONTINUATION_DRIVER_BUSY", "Another admitted runtime currently owns this continuation driver.", retryable=True, details={"reason": claim.get("reason")})
            continuation = claim["continuation"]
            generation = int(continuation["driver_generation"])
            raw_policy = self.orchestration_ledger._run_continuation_get_raw(run_id)
            if raw_policy is None:
                raise RunContinuationError("RUN_CONTINUATION_GRANT_REQUIRED", "Continuation grant disappeared during driver claim.")
            policy = raw_policy["policy"]
            restored_lane = False
            if raw_policy.get("thread_id"):
                consent = policy.get("consent") if isinstance(policy.get("consent"), dict) else {}
                descriptor = continuation_consent_descriptor(policy)
                if (
                    not str(consent.get("receipt_id") or "")
                    or str(consent.get("scope_sha256") or "") != descriptor["scope_sha256"]
                ):
                    raise RunContinuationError(
                        "RUN_CONTINUATION_CONSENT_REQUIRED",
                        "Persistent-lane recovery requires the original exact one-shot consent receipt.",
                    )
                session_id = str(raw_policy.get("thread_session_id") or "")
                if not session_id:
                    raise RunContinuationError(
                        "RUN_CONTINUATION_SESSION_REQUIRED",
                        "Persistent-lane recovery requires the durable App Server session identity.",
                    )
                restored = self._codex_bridge.restore_persistent_thread(
                    thread_id=str(raw_policy["thread_id"]),
                    expected_session_id=session_id,
                    profile=RUN_CONTINUATION_PROFILE,
                    model="gpt-5.6-sol",
                    effort="xhigh",
                )
                if str(restored.get("thread_id") or "") != str(raw_policy["thread_id"]) or str(restored.get("session_id") or "") != session_id:
                    raise RunContinuationError(
                        "RUN_CONTINUATION_SESSION_MISMATCH",
                        "The App Server did not restore the exact durable continuation lane/session.",
                    )
                restored_lane = True
            objective = str((self.orchestration_ledger.get_run(run_id) or {}).get("objective") or "").strip()
            # Start with the immutable Problem capsule and a declared bounded
            # read catalogue. The model must explicitly request source bytes;
            # this keeps READ meaningful instead of handing it every granted
            # file and then accepting a no-op request loop.
            evidence, evidence_hash = self._run_continuation_canonical_evidence(
                policy, objective=objective, selected_read_paths=()
            )
            request_hash = hashlib.sha256(_canonical_json({"evidence_hash": evidence_hash, "profile": RUN_CONTINUATION_PROFILE}).encode("utf-8")).hexdigest()
            reservation = self.orchestration_ledger.reserve_run_continuation_action(
                run_id=run_id,
                driver_generation=generation,
                runtime_instance_id=self._run_continuation_runtime_instance_id(),
                action_kind="proposal",
                request_hash=request_hash,
                evidence_hash=evidence_hash,
                evidence_paths=(),
                expected_action_seq=int(continuation["next_action_seq"]),
            )
            if not reservation.get("reserved"):
                raise RunContinuationError("RUN_CONTINUATION_ACTION_PENDING", "The continuation proposal action is already reserved; reconcile it before dispatch.")
            action_id = str(reservation["action_id"])
            prompt = self._run_continuation_prompt(policy=policy, evidence=evidence, evidence_hash=evidence_hash)
            bridge = (
                self._codex_bridge.continue_thread(
                    thread_id=str(raw_policy["thread_id"]),
                    prompt=prompt,
                    output_schema=None,
                )
                if restored_lane
                else self._codex_bridge.run(
                    prompt,
                    profile=RUN_CONTINUATION_PROFILE,
                    lifetime="persistent",
                    # The model has no tool or write capability and its response
                    # is parsed fail-closed before MCP can consider an effect.
                    output_schema=None,
                )
            )
            thread_id, turn_id = str(bridge.get("thread_id") or ""), str(bridge.get("turn_id") or "")
            session_id = str(bridge.get("session_id") or raw_policy.get("thread_session_id") or "")
            if not thread_id or not turn_id or not session_id:
                raise RunContinuationError("RUN_CONTINUATION_DISPATCH_FAILED", "The bridge did not return a durable thread and turn identity.")
            lane_id = hashlib.sha256(f"run-continuation-lane-v1\0{run_id}\0{policy['policy_sha256'] if 'policy_sha256' in policy else evidence_hash}".encode("utf-8")).hexdigest()
            self.orchestration_ledger.set_run_continuation_dispatch(
                run_id=run_id,
                driver_generation=generation,
                runtime_instance_id=self._run_continuation_runtime_instance_id(),
                action_id=action_id,
                lane_id=lane_id,
                thread_id=thread_id,
                turn_id=turn_id,
                session_id=session_id,
            )
            self._run_continuation_start_worker(run_id=run_id, driver_generation=generation)
        except RunContinuationError as exc:
            raise self._run_continuation_tool_failure(exc) from exc
        except Exception as exc:
            code = str(getattr(exc, "code", "RUN_CONTINUATION_DISPATCH_FAILED"))
            raise ToolFailure(code, str(exc), category="runtime", retryable=bool(getattr(exc, "retryable", False))) from exc
        return {
            "run_id": run_id,
            "action_id": action_id,
            "driver_generation": generation,
            "status": "PROPOSING",
            "thread_id": thread_id,
            "turn_id": turn_id,
            "evidence_hash": evidence_hash,
            "recommended_next_action": "The admitted MCP driver is observing this exact bridge turn without copying the ChatWeb controller. Inspect task_control run_continuation=get/observe for a durable status; it will never launch a second turn when dispatch outcome is unknown.",
        }

    def _run_continuation_control(self, args: dict[str, Any]) -> dict[str, Any]:
        action = str(args.get("run_continuation_action") or "get").strip().lower()
        run_id = str(args.get("run_id") or "").strip()
        if not run_id:
            state = self.task_state.get()
            projection = state.get("orchestration") if isinstance(state.get("orchestration"), dict) else {}
            run_id = str(projection.get("run_id") or "").strip()
        if not run_id:
            raise ToolFailure("ORCHESTRATION_RUN_NOT_FOUND", "run_id is required when controlling a continuation grant.", category="not_found")
        if action == "get":
            continuation = self.orchestration_ledger.get_run_continuation(run_id)
            return {
                "run_id": run_id,
                "continuation": continuation,
                "status": "MISSING" if continuation is None else "OK",
                "continuation_environment_hash": self._run_continuation_environment_hash(),
                "environment_hash_schema_version": 1,
            }
        if action == "start":
            controller = self._require_hub_controller(run_id)
            if controller is None:
                raise ToolFailure("RUN_CONTINUATION_CONTROLLER_REQUIRED", "Starting a continuation driver requires the active authenticated ChatWeb controller.", category="security")
            self._run_continuation_record_telemetry(
                run_id, "manual_nudge", outcome="observed", code="EXPLICIT_START", marker=str(controller.get("fencing_token") or "")
            )
            return self._run_continuation_start_driver({**args, "run_id": run_id})
        if action == "observe":
            # Observing an already-issued grant never turns a missing controller
            # into write/acceptance authority. It only lets a caller obtain the
            # exact driver result; the driver itself remains MCP-owned.
            return self._run_continuation_observe_driver(run_id=run_id)
        if action == "reconcile":
            controller = self._require_hub_controller(run_id)
            if controller is None:
                raise ToolFailure("RUN_CONTINUATION_CONTROLLER_REQUIRED", "Effect reconciliation requires the active authenticated ChatWeb controller.", category="security")
            return self._run_continuation_reconcile_driver(
                run_id=run_id,
                controller_fencing_token=controller.get("fencing_token"),
            )
        if action not in {"pause", "resume", "revoke"}:
            raise ToolFailure("RUN_CONTINUATION_CONTROL_INVALID", "Unsupported run_continuation_action.", category="validation")
        controller = self._require_hub_controller(run_id)
        if controller is None:
            raise ToolFailure("RUN_CONTINUATION_CONTROLLER_REQUIRED", "Continuation control requires the active authenticated ChatWeb controller.", category="security")
        try:
            continuation = self.orchestration_ledger.set_run_continuation_state(
                run_id=run_id,
                action=action,
                reason=str(args.get("continuation_reason") or ""),
            )
        except RunContinuationError as exc:
            raise self._run_continuation_tool_failure(exc) from exc
        return {"run_id": run_id, "continuation": continuation, "status": action.upper(), "controller_fencing_token": controller.get("fencing_token")}
