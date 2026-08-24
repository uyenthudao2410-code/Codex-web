from __future__ import annotations

"""Durable P5 epoch, enrollment, assignment, and ITT store for the canonical ledger."""

import hashlib
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any

from .p5_experiment import (
    P5_EPOCH_ACTIVE,
    P5_EPOCH_CLOSED,
    P5_EPOCH_HARD_STOPPED,
    P5_EPOCH_PAUSED,
    P5_EPOCH_TERMINAL,
    P5_INTERFERENCE_STATUSES,
    P5_TERMINAL_STATUSES,
    P5ExperimentError,
    activation_epoch_id as p5_activation_epoch_id,
    analyzer_source_fingerprint as p5_analyzer_source_fingerprint,
    assignment_unit_fingerprint as p5_assignment_unit_fingerprint,
    canary_analyzer as p5_canary_analyzer,
    eligibility_decision as p5_eligibility_decision,
    manifest_sha256 as p5_manifest_sha256,
    permuted_block_arms as p5_permuted_block_arms,
    received_arm as p5_received_arm,
    validate_manifest as validate_p5_manifest,
)
from .ledger_event_chain import append_hash_chained_event


def _p5_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _p5_bounded(value: Any, limit: int) -> str:
    text = str(value or "")
    return text if len(text) <= limit else text[:limit] + "..."


def _p5_sanitize(value: Any, *, key: str = "") -> Any:
    # P5 accepts only bounded structured contract facts. Never retain raw
    # prompt/content/patch fields if a direct internal caller violates that
    # boundary; the ordinary ledger sanitizer remains the broader policy.
    if key.lower() in {"content", "prompt", "raw_prompt", "patch", "stdout", "stderr", "seed", "seed_material"}:
        text = str(value or "")
        return {"redacted": True, "sha256": hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest(), "bytes": len(text.encode("utf-8", errors="replace"))}
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return _p5_bounded(value, 16_000)
    if isinstance(value, dict):
        return {str(item)[:200]: _p5_sanitize(current, key=str(item)) for item, current in list(value.items())[:200]}
    if isinstance(value, (list, tuple, set)):
        return [_p5_sanitize(current) for current in list(value)[:500]]
    return _p5_bounded(value, 16_000)


# Keep the extracted ledger-domain implementation independent from its parent
# module while preserving the established bounded JSON representation.
def _bounded_text(value: Any, limit: int = 16_000) -> str:
    return _p5_bounded(value, limit)


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _sanitize(value: Any, *, key: str = "") -> Any:
    return _p5_sanitize(value, key=key)


def utc_now() -> str:
    return _p5_now()


class P5ExperimentLedgerMixin:
    """A mixin; the parent supplies lock, connection, event chain, and serializers."""

    @staticmethod
    def _p5_append_event(connection: Any, run_id: str, **kwargs: Any) -> dict[str, Any]:
        return append_hash_chained_event(
            connection,
            run_id=run_id,
            event_type=str(kwargs.get("event_type") or ""),
            wave_id=kwargs.get("wave_id"),
            delegation_id=kwargs.get("delegation_id"),
            state_before=str(kwargs.get("state_before") or ""),
            state_after=str(kwargs.get("state_after") or ""),
            payload=kwargs.get("payload") if isinstance(kwargs.get("payload"), dict) else {},
            event_time=str(kwargs.get("event_time") or _p5_now()),
            sanitize=_p5_sanitize,
            serialize=lambda value: json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str),
            bounded_text=_p5_bounded,
        )

    def _p5_ensure_schema(self, connection: Any) -> None:
        connection.executescript(
            """
                CREATE TABLE IF NOT EXISTS p5_experiment_epochs (
                    activation_epoch_id TEXT PRIMARY KEY,
                    experiment_id TEXT NOT NULL,
                    ledger_run_id TEXT NOT NULL UNIQUE REFERENCES runs(run_id) ON DELETE RESTRICT,
                    manifest_sha256 TEXT NOT NULL,
                    manifest_json TEXT NOT NULL,
                    phase TEXT NOT NULL,
                    study_type TEXT NOT NULL,
                    lifecycle TEXT NOT NULL,
                    seed_commitment_sha256 TEXT NOT NULL,
                    seed_handle TEXT NOT NULL DEFAULT '',
                    opened_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    closed_at TEXT,
                    hard_stop_reason TEXT NOT NULL DEFAULT '',
                    metadata_json TEXT NOT NULL DEFAULT '{}'
                );
                CREATE INDEX IF NOT EXISTS idx_p5_epochs_experiment_updated
                    ON p5_experiment_epochs(experiment_id, updated_at DESC);
                CREATE UNIQUE INDEX IF NOT EXISTS idx_p5_one_live_epoch_per_experiment
                    ON p5_experiment_epochs(experiment_id)
                    WHERE lifecycle IN ('EPOCH_ACTIVE','EPOCH_PAUSED');
                CREATE TABLE IF NOT EXISTS p5_enrollment_decisions (
                    enrollment_id TEXT PRIMARY KEY,
                    activation_epoch_id TEXT NOT NULL REFERENCES p5_experiment_epochs(activation_epoch_id) ON DELETE RESTRICT,
                    experiment_id TEXT NOT NULL,
                    assignment_unit_fp TEXT NOT NULL,
                    task_class TEXT NOT NULL,
                    eligible INTEGER NOT NULL,
                    enrolled INTEGER NOT NULL,
                    decision_hash TEXT NOT NULL,
                    eligibility_event_seq INTEGER NOT NULL,
                    enrollment_event_seq INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    UNIQUE(experiment_id, activation_epoch_id, assignment_unit_fp)
                );
                CREATE INDEX IF NOT EXISTS idx_p5_enrollment_epoch
                    ON p5_enrollment_decisions(activation_epoch_id, task_class, created_at);
                CREATE TABLE IF NOT EXISTS experiment_assignments (
                    assignment_id TEXT PRIMARY KEY,
                    experiment_id TEXT NOT NULL,
                    activation_epoch_id TEXT NOT NULL REFERENCES p5_experiment_epochs(activation_epoch_id) ON DELETE RESTRICT,
                    assignment_unit_fp TEXT NOT NULL,
                    task_class TEXT NOT NULL,
                    block_id INTEGER NOT NULL,
                    block_slot INTEGER NOT NULL,
                    assigned_arm TEXT NOT NULL,
                    assignment_probability REAL NOT NULL,
                    manifest_sha256 TEXT NOT NULL,
                    enrollment_id TEXT NOT NULL REFERENCES p5_enrollment_decisions(enrollment_id) ON DELETE RESTRICT,
                    assignment_event_seq INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    UNIQUE(experiment_id, assignment_unit_fp),
                    UNIQUE(experiment_id, activation_epoch_id, task_class, block_id, block_slot)
                );
                CREATE INDEX IF NOT EXISTS idx_p5_assignments_epoch_stratum
                    ON experiment_assignments(activation_epoch_id, task_class, block_id, block_slot);
                CREATE TABLE IF NOT EXISTS p5_arm_protocol_starts (
                    assignment_id TEXT PRIMARY KEY REFERENCES experiment_assignments(assignment_id) ON DELETE RESTRICT,
                    activation_epoch_id TEXT NOT NULL REFERENCES p5_experiment_epochs(activation_epoch_id) ON DELETE RESTRICT,
                    received_arm TEXT NOT NULL,
                    protocol_id TEXT NOT NULL,
                    protocol_event_seq INTEGER NOT NULL,
                    started_at TEXT NOT NULL,
                    first_write_at TEXT NOT NULL DEFAULT '',
                    metadata_json TEXT NOT NULL DEFAULT '{}'
                );
                CREATE TABLE IF NOT EXISTS p5_assignment_workflow_bindings (
                    assignment_id TEXT PRIMARY KEY REFERENCES experiment_assignments(assignment_id) ON DELETE RESTRICT,
                    activation_epoch_id TEXT NOT NULL REFERENCES p5_experiment_epochs(activation_epoch_id) ON DELETE RESTRICT,
                    workflow TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    wave_id TEXT NOT NULL,
                    write_lease_id TEXT NOT NULL,
                    prewrite_event_seq INTEGER NOT NULL,
                    prewrite_bound_at TEXT NOT NULL,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    UNIQUE(run_id, wave_id)
                );
                CREATE INDEX IF NOT EXISTS idx_p5_workflow_bindings_epoch
                    ON p5_assignment_workflow_bindings(activation_epoch_id, prewrite_bound_at);
                CREATE TABLE IF NOT EXISTS p5_assignment_outcomes (
                    assignment_id TEXT PRIMARY KEY REFERENCES experiment_assignments(assignment_id) ON DELETE RESTRICT,
                    activation_epoch_id TEXT NOT NULL REFERENCES p5_experiment_epochs(activation_epoch_id) ON DELETE RESTRICT,
                    terminal_status TEXT NOT NULL,
                    terminal_at TEXT NOT NULL DEFAULT '',
                    qualifying_acceptance_at TEXT NOT NULL DEFAULT '',
                    post_assignment_replan_count INTEGER,
                    immediate_oracle_pass INTEGER,
                    immediate_proof_observed INTEGER,
                    immediate_quality_status TEXT NOT NULL DEFAULT 'unknown',
                    delayed_followup_status TEXT NOT NULL DEFAULT 'pending_or_unknown',
                    quality_followup_interference TEXT NOT NULL DEFAULT 'attribution_unknown',
                    received_arm TEXT NOT NULL DEFAULT '',
                    adherence_status TEXT NOT NULL DEFAULT 'unknown',
                    protocol_started_at TEXT NOT NULL DEFAULT '',
                    first_write_at TEXT NOT NULL DEFAULT '',
                    protocol_completed_at TEXT NOT NULL DEFAULT '',
                    critical_security_or_data_loss INTEGER NOT NULL DEFAULT 0,
                    outcome_event_seq INTEGER NOT NULL,
                    recorded_at TEXT NOT NULL,
                    metadata_json TEXT NOT NULL DEFAULT '{}'
                );
                CREATE INDEX IF NOT EXISTS idx_p5_outcomes_epoch_terminal
                    ON p5_assignment_outcomes(activation_epoch_id, terminal_status, recorded_at);

            """
        )

    @staticmethod
    def _p5_epoch_row(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "activation_epoch_id": row["activation_epoch_id"],
            "experiment_id": row["experiment_id"],
            "ledger_run_id": row["ledger_run_id"],
            "manifest_sha256": row["manifest_sha256"],
            "manifest": json.loads(row["manifest_json"] or "{}"),
            "phase": row["phase"],
            "study_type": row["study_type"],
            "lifecycle": row["lifecycle"],
            "seed_commitment_sha256": row["seed_commitment_sha256"],
            "seed_handle": row["seed_handle"],
            "opened_at": row["opened_at"],
            "updated_at": row["updated_at"],
            "closed_at": row["closed_at"],
            "hard_stop_reason": row["hard_stop_reason"],
            "metadata": json.loads(row["metadata_json"] or "{}"),
        }

    @staticmethod
    def _p5_enrollment_row(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "enrollment_id": row["enrollment_id"],
            "activation_epoch_id": row["activation_epoch_id"],
            "experiment_id": row["experiment_id"],
            "assignment_unit_fp": row["assignment_unit_fp"],
            "task_class": row["task_class"],
            "eligible": bool(row["eligible"]),
            "enrolled": bool(row["enrolled"]),
            "decision_hash": row["decision_hash"],
            "eligibility_event_seq": int(row["eligibility_event_seq"]),
            "enrollment_event_seq": int(row["enrollment_event_seq"]),
            "created_at": row["created_at"],
            "metadata": json.loads(row["metadata_json"] or "{}"),
        }

    @staticmethod
    def _p5_assignment_row(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "assignment_id": row["assignment_id"],
            "experiment_id": row["experiment_id"],
            "activation_epoch_id": row["activation_epoch_id"],
            "assignment_unit_fp": row["assignment_unit_fp"],
            "task_class": row["task_class"],
            "block_id": int(row["block_id"]),
            "block_slot": int(row["block_slot"]),
            "assigned_arm": row["assigned_arm"],
            "assignment_probability": float(row["assignment_probability"]),
            "manifest_sha256": row["manifest_sha256"],
            "enrollment_id": row["enrollment_id"],
            "assignment_event_seq": int(row["assignment_event_seq"]),
            "created_at": row["created_at"],
            "metadata": json.loads(row["metadata_json"] or "{}"),
        }

    @staticmethod
    def _p5_outcome_row(row: sqlite3.Row) -> dict[str, Any]:
        def optional_bool(name: str) -> bool | None:
            value = row[name]
            return None if value is None else bool(value)

        return {
            "assignment_id": row["assignment_id"],
            "activation_epoch_id": row["activation_epoch_id"],
            "terminal_status": row["terminal_status"],
            "terminal_at": row["terminal_at"],
            "qualifying_acceptance_at": row["qualifying_acceptance_at"],
            "post_assignment_replan_count": row["post_assignment_replan_count"],
            "immediate_oracle_pass": optional_bool("immediate_oracle_pass"),
            "immediate_proof_observed": optional_bool("immediate_proof_observed"),
            "immediate_quality_status": row["immediate_quality_status"],
            "delayed_followup_status": row["delayed_followup_status"],
            "quality_followup_interference": row["quality_followup_interference"],
            "received_arm": row["received_arm"],
            "adherence_status": row["adherence_status"],
            "protocol_started_at": row["protocol_started_at"],
            "first_write_at": row["first_write_at"],
            "protocol_completed_at": row["protocol_completed_at"],
            "critical_security_or_data_loss": bool(row["critical_security_or_data_loss"]),
            "outcome_event_seq": int(row["outcome_event_seq"]),
            "recorded_at": row["recorded_at"],
            "metadata": json.loads(row["metadata_json"] or "{}"),
        }

    @staticmethod
    def _p5_epoch_for_update(connection: sqlite3.Connection, activation_epoch_id: str) -> sqlite3.Row:
        row = connection.execute(
            "SELECT * FROM p5_experiment_epochs WHERE activation_epoch_id=?",
            (_bounded_text(activation_epoch_id, 128).strip(),),
        ).fetchone()
        if row is None:
            raise P5ExperimentError("P5 activation epoch was not found")
        return row

    @staticmethod
    def _p5_assignment_unit(candidate: dict[str, Any]) -> str:
        return p5_assignment_unit_fingerprint(
            task_assignment_id=str(candidate.get("task_assignment_id") or ""),
            repository_identity_fp=str(candidate.get("repository_identity_fp") or ""),
            initial_task_spec_fp=str(candidate.get("initial_task_spec_fp") or ""),
            initial_target_source_block_id=str(candidate.get("initial_target_source_block_id") or ""),
        )

    def p5_open_epoch(
        self,
        *,
        manifest: dict[str, Any],
        seed_material: str,
        seed_handle: str,
        authority: str = "operator",
    ) -> dict[str, Any]:
        """Explicitly open one immutable epoch after validating its exact contract.

        The seed is checked only against its commitment and never enters an event,
        table payload, exception, or returned projection.  A restarted runtime
        must resolve the same secret handle and commitment before assigning again.
        """
        normalized = validate_p5_manifest(manifest)
        if normalized.get("template_only") is True:
            raise P5ExperimentError("a template-only P5 manifest cannot open an activation epoch")
        manifest_hash = p5_manifest_sha256(normalized)
        epoch_id = p5_activation_epoch_id(normalized)
        assignment = dict(normalized["assignment"])
        commitment = str(assignment["seed_commitment_sha256"])
        if not isinstance(seed_material, str) or not seed_material or hashlib.sha256(seed_material.encode("utf-8")).hexdigest() != commitment:
            raise P5ExperimentError("P5 assignment seed does not match the frozen commitment")
        handle = _bounded_text(seed_handle, 256).strip()
        if not handle.startswith("secret://"):
            raise P5ExperimentError("P5 assignment seed must be supplied through a secret:// handle")
        now = utc_now()
        with self._lock, self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                "SELECT * FROM p5_experiment_epochs WHERE activation_epoch_id=?", (epoch_id,)
            ).fetchone()
            if existing is not None:
                item = self._p5_epoch_row(existing)
                if item["manifest_sha256"] != manifest_hash or item["seed_commitment_sha256"] != commitment:
                    raise P5ExperimentError("P5 activation epoch identity conflicts with its frozen manifest")
                return {"opened": False, "idempotent": True, "epoch": item}
            live = connection.execute(
                "SELECT activation_epoch_id FROM p5_experiment_epochs WHERE experiment_id=? AND lifecycle IN (?, ?)",
                (normalized["experiment_id"], P5_EPOCH_ACTIVE, P5_EPOCH_PAUSED),
            ).fetchone()
            if live is not None:
                raise P5ExperimentError("an experiment already has a live activation epoch")
            ledger_run_id = f"p5-{uuid.uuid4().hex}"
            connection.execute(
                "INSERT INTO runs(run_id,task_id,objective,status,started_at,metadata_json) VALUES(?,?,?,?,?,?)",
                (
                    ledger_run_id,
                    "",
                    _bounded_text(f"P5 {normalized['experiment_id']} {normalized['phase']} epoch", 4000),
                    "active",
                    now,
                    _json(_sanitize({"p5_experiment": True, "manifest_sha256": manifest_hash})),
                ),
            )
            connection.execute(
                """INSERT INTO p5_experiment_epochs(
                    activation_epoch_id,experiment_id,ledger_run_id,manifest_sha256,manifest_json,phase,study_type,lifecycle,
                    seed_commitment_sha256,seed_handle,opened_at,updated_at,metadata_json
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    epoch_id,
                    normalized["experiment_id"],
                    ledger_run_id,
                    manifest_hash,
                    _json(normalized),
                    normalized["phase"],
                    normalized["study_type"],
                    P5_EPOCH_ACTIVE,
                    commitment,
                    handle,
                    now,
                    now,
                    _json(_sanitize({"opened_by": _bounded_text(authority, 128)})),
                ),
            )
            self._p5_append_event(
                connection,
                ledger_run_id,
                event_type="p5_epoch_opened",
                state_before="START_READY",
                state_after=P5_EPOCH_ACTIVE,
                payload={
                    "activation_epoch_id": epoch_id,
                    "experiment_id": normalized["experiment_id"],
                    "manifest_sha256": manifest_hash,
                    "phase": normalized["phase"],
                    "study_type": normalized["study_type"],
                    "seed_commitment_sha256": commitment,
                    "seed_handle": handle,
                    "authority": _bounded_text(authority, 128),
                    "automatic_activation": False,
                },
            )
            row = self._p5_epoch_for_update(connection, epoch_id)
        return {"opened": True, "idempotent": False, "epoch": self._p5_epoch_row(row)}

    def p5_transition_epoch(
        self,
        *,
        activation_epoch_id: str,
        transition: str,
        reason: str = "",
        authority: str = "operator",
    ) -> dict[str, Any]:
        requested = str(transition or "").strip().lower()
        allowed = {
            "pause": (P5_EPOCH_ACTIVE, P5_EPOCH_PAUSED, "p5_epoch_paused"),
            "resume": (P5_EPOCH_PAUSED, P5_EPOCH_ACTIVE, "p5_epoch_resumed"),
            "close": ((P5_EPOCH_ACTIVE, P5_EPOCH_PAUSED), P5_EPOCH_CLOSED, "p5_epoch_closed"),
            "hard_stop": ((P5_EPOCH_ACTIVE, P5_EPOCH_PAUSED), P5_EPOCH_HARD_STOPPED, "p5_epoch_hard_stopped"),
        }
        if requested not in allowed:
            raise P5ExperimentError("P5 epoch transition is unsupported")
        expected, target, event_type = allowed[requested]
        bounded_reason = _bounded_text(reason, 512).strip()
        if requested == "hard_stop" and not bounded_reason:
            raise P5ExperimentError("P5 hard stop requires a bounded reason")
        now = utc_now()
        with self._lock, self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = self._p5_epoch_for_update(connection, activation_epoch_id)
            current = str(row["lifecycle"])
            expected_states = expected if isinstance(expected, tuple) else (expected,)
            if current == target:
                return {"changed": False, "epoch": self._p5_epoch_row(row)}
            if current not in expected_states:
                raise P5ExperimentError(f"P5 epoch transition {requested} is invalid from {current}")
            connection.execute(
                """UPDATE p5_experiment_epochs
                   SET lifecycle=?, updated_at=?, closed_at=?, hard_stop_reason=?
                   WHERE activation_epoch_id=?""",
                (
                    target,
                    now,
                    now if target in P5_EPOCH_TERMINAL else None,
                    bounded_reason if target == P5_EPOCH_HARD_STOPPED else "",
                    row["activation_epoch_id"],
                ),
            )
            self._p5_append_event(
                connection,
                str(row["ledger_run_id"]),
                event_type=event_type,
                state_before=current,
                state_after=target,
                payload={
                    "activation_epoch_id": row["activation_epoch_id"],
                    "experiment_id": row["experiment_id"],
                    "reason": bounded_reason or None,
                    "authority": _bounded_text(authority, 128),
                },
            )
            if target in P5_EPOCH_TERMINAL:
                connection.execute(
                    "UPDATE runs SET status=?, finished_at=? WHERE run_id=?",
                    ("failed" if target == P5_EPOCH_HARD_STOPPED else "completed", now, row["ledger_run_id"]),
                )
            updated = self._p5_epoch_for_update(connection, str(row["activation_epoch_id"]))
        return {"changed": True, "epoch": self._p5_epoch_row(updated)}

    def p5_record_enrollment(
        self,
        *,
        activation_epoch_id: str,
        candidate: dict[str, Any],
        enrolled: bool,
        authority: str = "operator",
    ) -> dict[str, Any]:
        decision = p5_eligibility_decision(candidate)
        unit_fp = self._p5_assignment_unit(candidate)
        enrolled_value = bool(enrolled)
        if enrolled_value and not decision["eligible"]:
            raise P5ExperimentError("ineligible task cannot be enrolled")
        decision_material = {
            "assignment_unit_fp": unit_fp,
            "task_class": decision["task_class"],
            "eligible": decision["eligible"],
            "requirements": decision["requirements"],
            "enrolled": enrolled_value,
        }
        decision_hash = hashlib.sha256(_json(decision_material).encode("utf-8")).hexdigest()
        now = utc_now()
        with self._lock, self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            epoch = self._p5_epoch_for_update(connection, activation_epoch_id)
            if epoch["lifecycle"] != P5_EPOCH_ACTIVE:
                raise P5ExperimentError("P5 enrollment requires an active epoch")
            existing = connection.execute(
                "SELECT * FROM p5_enrollment_decisions WHERE activation_epoch_id=? AND assignment_unit_fp=?",
                (epoch["activation_epoch_id"], unit_fp),
            ).fetchone()
            if existing is not None:
                item = self._p5_enrollment_row(existing)
                if item["decision_hash"] != decision_hash:
                    raise P5ExperimentError("P5 enrollment decision conflicts with immutable prior eligibility")
                return {"recorded": False, "idempotent": True, "enrollment": item}
            eligibility_event = self._p5_append_event(
                connection,
                str(epoch["ledger_run_id"]),
                event_type="p5_eligibility_recorded",
                payload={
                    "activation_epoch_id": epoch["activation_epoch_id"],
                    "assignment_unit_fp": unit_fp,
                    "task_class": decision["task_class"],
                    "eligible": decision["eligible"],
                    "reason_codes": decision["reason_codes"],
                    "arm_revealed": False,
                    "authority": _bounded_text(authority, 128),
                },
            )
            enrollment_event = self._p5_append_event(
                connection,
                str(epoch["ledger_run_id"]),
                event_type="p5_enrollment_decision_recorded",
                payload={
                    "activation_epoch_id": epoch["activation_epoch_id"],
                    "assignment_unit_fp": unit_fp,
                    "eligible": decision["eligible"],
                    "enrolled": enrolled_value,
                    "reason_codes": decision["reason_codes"],
                    "arm_revealed": False,
                    "authority": _bounded_text(authority, 128),
                },
            )
            enrollment_id = uuid.uuid4().hex
            metadata = {
                key: candidate[key]
                for key in ("controller_context_fp", "session_cluster_id", "isolation_status")
                if key in candidate
            }
            connection.execute(
                """INSERT INTO p5_enrollment_decisions(
                    enrollment_id,activation_epoch_id,experiment_id,assignment_unit_fp,task_class,eligible,enrolled,decision_hash,
                    eligibility_event_seq,enrollment_event_seq,created_at,metadata_json
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    enrollment_id,
                    epoch["activation_epoch_id"],
                    epoch["experiment_id"],
                    unit_fp,
                    decision["task_class"],
                    int(decision["eligible"]),
                    int(enrolled_value),
                    decision_hash,
                    eligibility_event["seq"],
                    enrollment_event["seq"],
                    now,
                    _json(_sanitize(metadata)),
                ),
            )
            row = connection.execute("SELECT * FROM p5_enrollment_decisions WHERE enrollment_id=?", (enrollment_id,)).fetchone()
        assert row is not None
        return {"recorded": True, "idempotent": False, "enrollment": self._p5_enrollment_row(row)}

    def p5_assign(
        self,
        *,
        activation_epoch_id: str,
        candidate: dict[str, Any],
        manifest_sha256: str,
        seed_material: str,
        pre_arm_action_attested: bool,
        authority: str = "assignment_service",
    ) -> dict[str, Any]:
        if pre_arm_action_attested is not True:
            raise P5ExperimentError("P5 assignment must be attested before any arm action or first write")
        unit_fp = self._p5_assignment_unit(candidate)
        requested_manifest = _bounded_text(manifest_sha256, 64).strip().lower()
        now = utc_now()
        with self._lock, self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            epoch = self._p5_epoch_for_update(connection, activation_epoch_id)
            if epoch["lifecycle"] != P5_EPOCH_ACTIVE:
                raise P5ExperimentError("P5 assignment requires an active epoch")
            if requested_manifest != epoch["manifest_sha256"]:
                raise P5ExperimentError("P5 assignment manifest does not match the active epoch")
            if not isinstance(seed_material, str) or not seed_material or hashlib.sha256(seed_material.encode("utf-8")).hexdigest() != epoch["seed_commitment_sha256"]:
                raise P5ExperimentError("P5 assignment seed commitment cannot be verified")
            existing = connection.execute(
                "SELECT * FROM experiment_assignments WHERE experiment_id=? AND assignment_unit_fp=?",
                (epoch["experiment_id"], unit_fp),
            ).fetchone()
            if existing is not None:
                item = self._p5_assignment_row(existing)
                if item["activation_epoch_id"] != epoch["activation_epoch_id"] or item["manifest_sha256"] != requested_manifest:
                    raise P5ExperimentError("P5 assignment unit conflicts with a prior immutable assignment")
                return {"assigned": False, "idempotent": True, "assignment": item}
            enrollment = connection.execute(
                "SELECT * FROM p5_enrollment_decisions WHERE activation_epoch_id=? AND assignment_unit_fp=?",
                (epoch["activation_epoch_id"], unit_fp),
            ).fetchone()
            if enrollment is None or not bool(enrollment["eligible"]) or not bool(enrollment["enrolled"]):
                raise P5ExperimentError("P5 assignment requires an earlier eligible enrolled decision")
            task_class = str(enrollment["task_class"])
            used = int(connection.execute(
                "SELECT COUNT(*) FROM experiment_assignments WHERE activation_epoch_id=? AND task_class=?",
                (epoch["activation_epoch_id"], task_class),
            ).fetchone()[0] or 0)
            block_id, block_slot = divmod(used, 4)
            arms = p5_permuted_block_arms(
                seed=seed_material,
                activation_epoch=str(epoch["activation_epoch_id"]),
                stratum=task_class,
                block_id=block_id,
                phase=str(epoch["phase"]),
            )
            assignment_id = uuid.uuid4().hex
            event = self._p5_append_event(
                connection,
                str(epoch["ledger_run_id"]),
                event_type="p5_assignment_recorded",
                payload={
                    "activation_epoch_id": epoch["activation_epoch_id"],
                    "assignment_id": assignment_id,
                    "assignment_unit_fp": unit_fp,
                    "task_class": task_class,
                    "block_id": block_id,
                    "block_slot": block_slot,
                    "assigned_arm": arms[block_slot],
                    "assignment_probability": 0.5,
                    "manifest_sha256": requested_manifest,
                    "pre_arm_action_attested": True,
                    "authority": _bounded_text(authority, 128),
                },
            )
            try:
                connection.execute(
                    """INSERT INTO experiment_assignments(
                        assignment_id,experiment_id,activation_epoch_id,assignment_unit_fp,task_class,block_id,block_slot,assigned_arm,
                        assignment_probability,manifest_sha256,enrollment_id,assignment_event_seq,created_at,metadata_json
                    ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        assignment_id,
                        epoch["experiment_id"],
                        epoch["activation_epoch_id"],
                        unit_fp,
                        task_class,
                        block_id,
                        block_slot,
                        arms[block_slot],
                        0.5,
                        requested_manifest,
                        enrollment["enrollment_id"],
                        event["seq"],
                        now,
                        _json(_sanitize({"pre_arm_action_attested": True})),
                    ),
                )
            except sqlite3.IntegrityError as exc:
                raise P5ExperimentError("P5 assignment uniqueness conflict; enrollment has been fail-closed") from exc
            row = connection.execute("SELECT * FROM experiment_assignments WHERE assignment_id=?", (assignment_id,)).fetchone()
        assert row is not None
        return {"assigned": True, "idempotent": False, "assignment": self._p5_assignment_row(row)}

    def p5_record_arm_protocol_start(
        self,
        *,
        assignment_id: str,
        received_arm: str,
        protocol_id: str,
        first_write_at: str = "",
        authority: str = "runtime",
    ) -> dict[str, Any]:
        now = utc_now()
        received = _bounded_text(received_arm, 32).strip().lower()
        protocol = _bounded_text(protocol_id, 128).strip()
        if not protocol:
            raise P5ExperimentError("P5 arm protocol id is required")
        if _bounded_text(first_write_at, 128).strip():
            raise P5ExperimentError(
                "P5 first-write time is runtime-owned and can only be recorded by a bound agent_workflow write lease"
            )
        with self._lock, self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            assignment = connection.execute("SELECT * FROM experiment_assignments WHERE assignment_id=?", (assignment_id,)).fetchone()
            if assignment is None:
                raise P5ExperimentError("P5 assignment was not found")
            epoch = self._p5_epoch_for_update(connection, str(assignment["activation_epoch_id"]))
            if epoch["lifecycle"] != P5_EPOCH_ACTIVE:
                raise P5ExperimentError("P5 arm protocol cannot start outside an active epoch")
            expected_received = p5_received_arm(phase=str(epoch["phase"]), assigned_arm=str(assignment["assigned_arm"]))
            if received != expected_received:
                raise P5ExperimentError("P5 received arm conflicts with immutable assignment")
            expected_protocol = "eocl-current-control-v1" if received == "control" else "lean-causal-fix-gate-v1"
            if protocol != expected_protocol:
                raise P5ExperimentError("P5 arm protocol does not match the frozen treatment contrast")
            existing = connection.execute("SELECT * FROM p5_arm_protocol_starts WHERE assignment_id=?", (assignment_id,)).fetchone()
            if existing is not None:
                if str(existing["received_arm"]) != received or str(existing["protocol_id"]) != protocol:
                    raise P5ExperimentError("P5 protocol start conflicts with immutable prior arm action")
                return {"recorded": False, "idempotent": True, "assignment_id": assignment_id}
            event = self._p5_append_event(
                connection,
                str(epoch["ledger_run_id"]),
                event_type="p5_arm_protocol_started",
                payload={
                    "activation_epoch_id": epoch["activation_epoch_id"],
                    "assignment_id": assignment_id,
                    "assigned_arm": assignment["assigned_arm"],
                    "received_arm": received,
                    "protocol_id": protocol,
                    "first_write_at": None,
                    "authority": _bounded_text(authority, 128),
                },
            )
            connection.execute(
                """INSERT INTO p5_arm_protocol_starts(
                    assignment_id,activation_epoch_id,received_arm,protocol_id,protocol_event_seq,started_at,first_write_at,metadata_json
                ) VALUES(?,?,?,?,?,?,?,?)""",
                (assignment_id, epoch["activation_epoch_id"], received, protocol, event["seq"], now, "", "{}"),
            )
        return {"recorded": True, "idempotent": False, "assignment_id": assignment_id, "received_arm": received, "protocol_id": protocol}

    def p5_activation_epoch_for_assignment(self, assignment_id: str) -> str:
        """Resolve one immutable assignment to its epoch without exposing arm data."""
        normalized_assignment = _bounded_text(assignment_id, 128).strip()
        if not normalized_assignment:
            raise P5ExperimentError("P5 assignment identity is required")
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT activation_epoch_id FROM experiment_assignments WHERE assignment_id=?",
                (normalized_assignment,),
            ).fetchone()
        if row is None:
            raise P5ExperimentError("P5 assignment was not found")
        return str(row["activation_epoch_id"])

    def p5_bind_workflow_prewrite(
        self,
        *,
        assignment_id: str,
        workflow: str,
        run_id: str,
        wave_id: str,
        write_lease_id: str,
        authority: str = "runtime",
    ) -> dict[str, Any]:
        """Bind the only write-capable workflow to a pre-started P5 protocol.

        The durable binding is recorded after the ordinary workspace fence is
        acquired and before either directory creation or patch application.  It
        is deliberately not an assertion that a physical source mutation later
        succeeded; a terminal P5 outcome still records that distinction.
        """
        normalized_assignment = _bounded_text(assignment_id, 128).strip()
        normalized_workflow = _bounded_text(workflow, 32).strip().lower()
        normalized_run = _bounded_text(run_id, 128).strip()
        normalized_wave = _bounded_text(wave_id, 128).strip()
        normalized_lease = _bounded_text(write_lease_id, 128).strip()
        if not normalized_assignment or not normalized_run or not normalized_wave or not normalized_lease:
            raise P5ExperimentError("P5 workflow binding requires assignment, run, wave, and write lease identities")
        if normalized_workflow not in {"feature", "bugfix"}:
            raise P5ExperimentError("P5 workflow binding only permits feature or bugfix workflows")
        now = utc_now()
        with self._lock, self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            assignment = connection.execute(
                "SELECT * FROM experiment_assignments WHERE assignment_id=?", (normalized_assignment,)
            ).fetchone()
            if assignment is None:
                raise P5ExperimentError("P5 assignment was not found")
            epoch = self._p5_epoch_for_update(connection, str(assignment["activation_epoch_id"]))
            if epoch["lifecycle"] != P5_EPOCH_ACTIVE:
                raise P5ExperimentError("P5 workflow write cannot start outside an active epoch")
            if str(assignment["task_class"]) != normalized_workflow:
                raise P5ExperimentError("P5 workflow does not match the immutable assignment task class")
            protocol = connection.execute(
                "SELECT * FROM p5_arm_protocol_starts WHERE assignment_id=?", (normalized_assignment,)
            ).fetchone()
            if protocol is None:
                raise P5ExperimentError("P5 workflow write requires a prior immutable arm protocol start")
            existing = connection.execute(
                "SELECT * FROM p5_assignment_workflow_bindings WHERE assignment_id=?", (normalized_assignment,)
            ).fetchone()
            if existing is not None:
                if (
                    str(existing["workflow"]) == normalized_workflow
                    and str(existing["run_id"]) == normalized_run
                    and str(existing["wave_id"]) == normalized_wave
                    and str(existing["write_lease_id"]) == normalized_lease
                ):
                    return {
                        "recorded": False,
                        "idempotent": True,
                        "assignment_id": normalized_assignment,
                        "prewrite_bound_at": str(existing["prewrite_bound_at"]),
                    }
                raise P5ExperimentError("P5 assignment is already bound to a different workflow write lease")
            if str(protocol["first_write_at"] or ""):
                raise P5ExperimentError("P5 assignment already has a recorded write binding")
            if connection.execute(
                "SELECT 1 FROM p5_assignment_outcomes WHERE assignment_id=?", (normalized_assignment,)
            ).fetchone() is not None:
                raise P5ExperimentError("P5 assignment outcome is terminal and cannot receive a new workflow write")
            event = self._p5_append_event(
                connection,
                str(epoch["ledger_run_id"]),
                event_type="p5_workflow_prewrite_bound",
                payload={
                    "activation_epoch_id": epoch["activation_epoch_id"],
                    "assignment_id": normalized_assignment,
                    "workflow": normalized_workflow,
                    "run_id": normalized_run,
                    "wave_id": normalized_wave,
                    "write_lease_id": normalized_lease,
                    "authority": _bounded_text(authority, 128),
                },
            )
            connection.execute(
                """INSERT INTO p5_assignment_workflow_bindings(
                    assignment_id,activation_epoch_id,workflow,run_id,wave_id,write_lease_id,
                    prewrite_event_seq,prewrite_bound_at,metadata_json
                ) VALUES(?,?,?,?,?,?,?,?,?)""",
                (
                    normalized_assignment,
                    epoch["activation_epoch_id"],
                    normalized_workflow,
                    normalized_run,
                    normalized_wave,
                    normalized_lease,
                    event["seq"],
                    now,
                    "{}",
                ),
            )
            connection.execute(
                "UPDATE p5_arm_protocol_starts SET first_write_at=? WHERE assignment_id=? AND first_write_at=''",
                (now, normalized_assignment),
            )
        return {
            "recorded": True,
            "idempotent": False,
            "assignment_id": normalized_assignment,
            "workflow": normalized_workflow,
            "run_id": normalized_run,
            "wave_id": normalized_wave,
            "prewrite_bound_at": now,
        }

    def p5_record_outcome(
        self,
        *,
        assignment_id: str,
        outcome: dict[str, Any],
        authority: str = "runtime",
    ) -> dict[str, Any]:
        terminal = _bounded_text(outcome.get("terminal_status"), 32).strip().lower()
        if terminal not in P5_TERMINAL_STATUSES:
            raise P5ExperimentError("P5 terminal_status is invalid")
        replan_count = outcome.get("post_assignment_replan_count")
        if replan_count is not None and (isinstance(replan_count, bool) or not isinstance(replan_count, int) or replan_count < 0):
            raise P5ExperimentError("P5 post_assignment_replan_count must be a non-negative integer or null")
        quality = _bounded_text(outcome.get("immediate_quality_status") or "unknown", 32).strip().lower()
        if quality not in {"pass", "fail", "not_applicable", "unknown"}:
            raise P5ExperimentError("P5 immediate_quality_status is invalid")
        interference = _bounded_text(outcome.get("quality_followup_interference") or "attribution_unknown", 64).strip()
        if interference not in P5_INTERFERENCE_STATUSES:
            raise P5ExperimentError("P5 quality_followup_interference is invalid")
        adherence = _bounded_text(outcome.get("adherence_status") or "unknown", 32).strip().lower()
        if adherence not in {"adherent", "noncompliant", "crossover", "unknown"}:
            raise P5ExperimentError("P5 adherence_status is invalid")
        def optional_bool(name: str) -> int | None:
            value = outcome.get(name)
            if value is None:
                return None
            if not isinstance(value, bool):
                raise P5ExperimentError(f"P5 {name} must be boolean or null")
            return int(value)
        oracle_pass = optional_bool("immediate_oracle_pass")
        proof_observed = optional_bool("immediate_proof_observed")
        critical = outcome.get("critical_security_or_data_loss") is True
        now = utc_now()
        with self._lock, self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            assignment = connection.execute("SELECT * FROM experiment_assignments WHERE assignment_id=?", (assignment_id,)).fetchone()
            if assignment is None:
                raise P5ExperimentError("P5 assignment was not found")
            epoch = self._p5_epoch_for_update(connection, str(assignment["activation_epoch_id"]))
            protocol = connection.execute("SELECT * FROM p5_arm_protocol_starts WHERE assignment_id=?", (assignment_id,)).fetchone()
            if protocol is None:
                raise P5ExperimentError("P5 outcome requires a prior recorded arm protocol start")
            existing = connection.execute("SELECT * FROM p5_assignment_outcomes WHERE assignment_id=?", (assignment_id,)).fetchone()
            if existing is not None:
                raise P5ExperimentError("P5 outcome is immutable; successor work cannot replace a prior assignment outcome")
            event = self._p5_append_event(
                connection,
                str(epoch["ledger_run_id"]),
                event_type="p5_outcome_finalized",
                payload={
                    "activation_epoch_id": epoch["activation_epoch_id"],
                    "assignment_id": assignment_id,
                    "terminal_status": terminal,
                    "post_assignment_replan_count": replan_count,
                    "immediate_oracle_pass": None if oracle_pass is None else bool(oracle_pass),
                    "immediate_proof_observed": None if proof_observed is None else bool(proof_observed),
                    "immediate_quality_status": quality,
                    "quality_followup_interference": interference,
                    "received_arm": protocol["received_arm"],
                    "adherence_status": adherence,
                    "critical_security_or_data_loss": critical,
                    "authority": _bounded_text(authority, 128),
                },
            )
            connection.execute(
                """INSERT INTO p5_assignment_outcomes(
                    assignment_id,activation_epoch_id,terminal_status,terminal_at,qualifying_acceptance_at,post_assignment_replan_count,
                    immediate_oracle_pass,immediate_proof_observed,immediate_quality_status,delayed_followup_status,
                    quality_followup_interference,received_arm,adherence_status,protocol_started_at,first_write_at,protocol_completed_at,
                    critical_security_or_data_loss,outcome_event_seq,recorded_at,metadata_json
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    assignment_id,
                    epoch["activation_epoch_id"],
                    terminal,
                    _bounded_text(outcome.get("terminal_at"), 128).strip() or now,
                    _bounded_text(outcome.get("qualifying_acceptance_at"), 128).strip(),
                    replan_count,
                    oracle_pass,
                    proof_observed,
                    quality,
                    _bounded_text(outcome.get("delayed_followup_status") or "pending_or_unknown", 64).strip(),
                    interference,
                    protocol["received_arm"],
                    adherence,
                    protocol["started_at"],
                    protocol["first_write_at"],
                    _bounded_text(outcome.get("protocol_completed_at"), 128).strip(),
                    int(critical),
                    event["seq"],
                    now,
                    _json(_sanitize({"manual_rescue_or_fix": outcome.get("manual_rescue_or_fix") is True})),
                ),
            )
            if critical:
                connection.execute(
                    """UPDATE p5_experiment_epochs SET lifecycle=?, updated_at=?, closed_at=?, hard_stop_reason=?
                       WHERE activation_epoch_id=?""",
                    (P5_EPOCH_HARD_STOPPED, now, now, "critical_security_or_data_loss_defect", epoch["activation_epoch_id"]),
                )
                self._p5_append_event(
                    connection,
                    str(epoch["ledger_run_id"]),
                    event_type="p5_epoch_hard_stopped",
                    state_before=str(epoch["lifecycle"]),
                    state_after=P5_EPOCH_HARD_STOPPED,
                    payload={"activation_epoch_id": epoch["activation_epoch_id"], "reason": "critical_security_or_data_loss_defect", "automatic_safety_stop": True},
                )
                connection.execute("UPDATE runs SET status='failed', finished_at=? WHERE run_id=?", (now, epoch["ledger_run_id"]))
            row = connection.execute("SELECT * FROM p5_assignment_outcomes WHERE assignment_id=?", (assignment_id,)).fetchone()
        assert row is not None
        return {"recorded": True, "outcome": self._p5_outcome_row(row), "hard_stopped": critical}

    def p5_epoch_snapshot(self, activation_epoch_id: str) -> dict[str, Any]:
        with self._lock, self._connect() as connection:
            epoch_row = self._p5_epoch_for_update(connection, activation_epoch_id)
            epoch = self._p5_epoch_row(epoch_row)
            enrollment = [self._p5_enrollment_row(row) for row in connection.execute(
                "SELECT * FROM p5_enrollment_decisions WHERE activation_epoch_id=? ORDER BY created_at, enrollment_id", (epoch["activation_epoch_id"],)
            ).fetchall()]
            assignments = [self._p5_assignment_row(row) for row in connection.execute(
                "SELECT * FROM experiment_assignments WHERE activation_epoch_id=? ORDER BY task_class, block_id, block_slot", (epoch["activation_epoch_id"],)
            ).fetchall()]
            outcomes = [self._p5_outcome_row(row) for row in connection.execute(
                "SELECT * FROM p5_assignment_outcomes WHERE activation_epoch_id=? ORDER BY recorded_at, assignment_id", (epoch["activation_epoch_id"],)
            ).fetchall()]
            protocol_starts = [
                {
                    "assignment_id": row["assignment_id"],
                    "received_arm": row["received_arm"],
                    "protocol_id": row["protocol_id"],
                    "protocol_event_seq": int(row["protocol_event_seq"]),
                    "started_at": row["started_at"],
                    "first_write_at": row["first_write_at"],
                }
                for row in connection.execute(
                    "SELECT * FROM p5_arm_protocol_starts WHERE activation_epoch_id=? ORDER BY started_at, assignment_id",
                    (epoch["activation_epoch_id"],),
                ).fetchall()
            ]
            workflow_bindings = [
                {
                    "assignment_id": row["assignment_id"],
                    "workflow": row["workflow"],
                    "run_id": row["run_id"],
                    "wave_id": row["wave_id"],
                    "write_lease_id": row["write_lease_id"],
                    "prewrite_event_seq": int(row["prewrite_event_seq"]),
                    "prewrite_bound_at": row["prewrite_bound_at"],
                }
                for row in connection.execute(
                    "SELECT * FROM p5_assignment_workflow_bindings WHERE activation_epoch_id=? ORDER BY prewrite_bound_at, assignment_id",
                    (epoch["activation_epoch_id"],),
                ).fetchall()
            ]
            events = [self._event_row(row) for row in connection.execute(
                "SELECT * FROM events WHERE run_id=? ORDER BY seq", (epoch["ledger_run_id"],)
            ).fetchall()]
        return {
            "epoch": epoch,
            "enrollment": enrollment,
            "assignments": assignments,
            "protocol_starts": protocol_starts,
            "workflow_bindings": workflow_bindings,
            "outcomes": outcomes,
            "events": events,
        }

    def p5_latest_epoch(self) -> dict[str, Any] | None:
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM p5_experiment_epochs ORDER BY updated_at DESC, activation_epoch_id DESC LIMIT 1"
            ).fetchone()
        return self._p5_epoch_row(row) if row is not None else None

    def current_active_execution_run(self, *, task_id: str = "") -> dict[str, Any] | None:
        """Return the newest active EOCL execution run, excluding P5 experiment anchors.

        A live P5 epoch has an audit-anchor run by design.  It is not a writer
        and must not make the runtime's restart preflight report generic active
        work when no actual execution run exists.
        """
        self.expire_controller_leases()
        p5_filter = "COALESCE(json_extract(metadata_json, '$.p5_experiment'), 0) != 1"
        with self._lock, self._connect() as connection:
            if task_id:
                row = connection.execute(
                    f"SELECT * FROM runs WHERE task_id=? AND status='active' AND {p5_filter} "
                    "ORDER BY started_at DESC LIMIT 1",
                    (task_id,),
                ).fetchone()
            else:
                row = connection.execute(
                    f"SELECT * FROM runs WHERE status='active' AND {p5_filter} ORDER BY started_at DESC LIMIT 1"
                ).fetchone()
        if not row:
            return None
        return self.get_run(str(row["run_id"]))

    def p5_analyze_epoch(self, activation_epoch_id: str) -> dict[str, Any]:
        snapshot = self.p5_epoch_snapshot(activation_epoch_id)
        epoch = dict(snapshot["epoch"])
        manifest = dict(epoch["manifest"])
        expected_analyzer = str(dict(manifest["analysis"])["analyzer_sha256"])
        observed_analyzer = p5_analyzer_source_fingerprint()
        if expected_analyzer != observed_analyzer:
            if epoch["lifecycle"] not in P5_EPOCH_TERMINAL:
                self.p5_transition_epoch(
                    activation_epoch_id=activation_epoch_id,
                    transition="hard_stop",
                    reason="analyzer_source_fingerprint_mismatch",
                    authority="p5_analyzer",
                )
            raise P5ExperimentError("P5 analyzer source fingerprint drifted; epoch has been hard-stopped")
        outcomes = {str(item["assignment_id"]): item for item in snapshot["outcomes"]}
        analysis = p5_canary_analyzer(
            manifest=manifest,
            epoch=epoch,
            assignments=list(snapshot["assignments"]),
            outcomes_by_assignment=outcomes,
            enrollment_rows=list(snapshot["enrollment"]),
            integrity_events=list(snapshot["events"]),
            protocol_starts=list(snapshot["protocol_starts"]),
            workflow_bindings=list(snapshot["workflow_bindings"]),
        )
        if analysis["integrity"]["hard_stop_required"] and epoch["lifecycle"] not in P5_EPOCH_TERMINAL:
            reasons = list(analysis["integrity"].get("hard_stop_event_types") or []) + list(
                analysis["integrity"].get("hard_stop_reason_codes") or []
            )
            transition = self.p5_transition_epoch(
                activation_epoch_id=activation_epoch_id,
                transition="hard_stop",
                reason="p5_analyzer_integrity:" + ",".join(sorted(set(reasons))),
                authority="p5_analyzer",
            )
            analysis["integrity"]["epoch_hard_stopped"] = transition["changed"] is True
        else:
            analysis["integrity"]["epoch_hard_stopped"] = False
        return analysis
