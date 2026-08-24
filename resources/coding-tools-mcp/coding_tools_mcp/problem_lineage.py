from __future__ import annotations

"""Typed, content-free Problem Resolution Lineage storage in the EOCL ledger.

The v1 model deliberately owns no transcript, prompt hash, arbitrary JSON
payload, second database, source mutation, proof, or acceptance authority.
It only records exact opaque identities and a small append-only problem-event
chain.  The owning ``OrchestrationLedger`` supplies the lock/connection and
the supported v9 -> v10 migration entry point.
"""

import hashlib
import json
import re
import sqlite3
from typing import Any


PROBLEM_SCHEMA_VERSION = 10
_ID_RE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_FP_RE = re.compile(r"^[0-9a-f]{64}$")

PROBLEM_OPERATIONS = frozenset({"open", "link", "feedback", "resolution", "reopen", "get"})
PROBLEM_RELATION_TYPES = frozenset({
    "OPEN",
    "LINK",
    "NO_RUN_CREATED",
    "ENGINEERING_ATTEMPT_BOUND",
    "USER_FEEDBACK",
    "PROVISIONAL_RESOLUTION",
    "CONFIRMED_RESOLUTION",
    "UNCONFIRMED_RESOLUTION",
    "REOPEN",
    "SUPERSEDE",
    "BLOCK",
    "ABANDON",
})
PROBLEM_LINK_STATUSES = frozenset({"EXACT", "AMBIGUOUS", "UNLINKED"})
PROBLEM_LINK_ROLES = frozenset({"PRIMARY", "SECONDARY"})
PROBLEM_STATES = frozenset({
    "OPEN",
    "PROVISIONALLY_RESOLVED",
    "RESOLVED_CONFIRMED",
    "RESOLVED_UNCONFIRMED",
    "REOPENED",
    "SUPERSEDED",
    "BLOCKED",
    "ABANDONED",
})
PROBLEM_ENGINEERING_FLOORS = frozenset({"REQUIRED", "NOT_APPLICABLE", "UNKNOWN"})
PROBLEM_TASK_CLASSES = frozenset({"feature", "bugfix", "diagnose", "test_failure", "build_release", "custom", "refactor", "unknown"})
PROBLEM_FEEDBACK_INTENTS = frozenset({
    "CONFIRM_RESOLVED",
    "PARTIAL_RESOLUTION",
    "SAME_PROBLEM_STILL_FAILING",
    "CORRECT_UNDERSTANDING",
    "CORRECT_TARGET_OR_SCOPE",
    "CORRECT_TECHNICAL_RESULT",
    "CORRECT_PROOF_OR_VERIFICATION",
    "ADD_CONSTRAINT_OR_REQUIREMENT",
    "PROVIDE_NEW_EVIDENCE",
    "PREFERENCE_CHANGE",
    "NEW_PROBLEM",
    "SUPERSEDE_OR_CANCEL",
    "UNKNOWN",
})
PROBLEM_CAUSAL_MECHANISMS = frozenset({
    "ASSISTANT_MISUNDERSTANDING",
    "WRONG_ROOT_CAUSE",
    "WRONG_TARGET_OR_WORKSPACE",
    "INSUFFICIENT_SOLUTION_SCOPE",
    "IMPLEMENTATION_DEFECT",
    "PROOF_ORACLE_GAP",
    "RUNTIME_OR_ENVIRONMENT_FAILURE",
    "SOURCE_OR_STATE_DRIFT",
    "STALE_CONTEXT_OR_REPLAY",
    "USER_NEW_INFORMATION",
    "REQUIREMENT_EVOLUTION",
    "USER_PREFERENCE_CHANGE",
    "EXTERNAL_DEPENDENCY_CHANGE",
    "UNKNOWN",
})
PROBLEM_ECONOMIC_CLASSES = frozenset({"AVOIDABLE_CORRECTION", "PRODUCTIVE_CLARIFICATION", "LEGITIMATE_REQUIREMENT_GROWTH", "NEUTRAL_FOLLOWUP", "UNKNOWN"})
PROBLEM_PROVENANCE = frozenset({"HOST_OBSERVED", "CONTROLLER_REPORTED_EXPLICIT_USER", "DETERMINISTIC_EVIDENCE", "HUMAN_ANNOTATED", "SHADOW_MODEL_INFERRED", "UNKNOWN"})
PROBLEM_EVIDENCE_LEVELS = frozenset({"OBSERVED", "DERIVED_HIGH_CONFIDENCE", "INFERRED", "UNKNOWN"})
PROBLEM_REASON_CODES = frozenset({
    "none",
    "user_confirmation",
    "explicit_same_problem_correction",
    "explicit_unconfirmed_closure",
    "superseded_by_user",
    "blocked_external_dependency",
    "abandoned_by_user",
    "no_run_created",
    "engineering_attempt_bound",
    "ambiguous_relation",
    "unlinked_relation",
})
_CLOSED_STATES = frozenset({"RESOLVED_CONFIRMED", "RESOLVED_UNCONFIRMED", "SUPERSEDED", "ABANDONED"})
_AUTOMATIC_POLICY_PROVENANCE = frozenset({"HOST_OBSERVED", "CONTROLLER_REPORTED_EXPLICIT_USER", "DETERMINISTIC_EVIDENCE", "HUMAN_ANNOTATED"})


class ProblemLineageError(ValueError):
    """A typed PRL request violates the privacy, linkage, or state contract."""


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _text(value: Any, name: str, *, required: bool = False, limit: int = 128) -> str:
    result = str(value or "").strip()
    if len(result) > limit:
        raise ProblemLineageError(f"{name} exceeds its bounded length")
    if required and not result:
        raise ProblemLineageError(f"{name} is required")
    return result


def _opaque_id(value: Any, name: str, *, required: bool = False) -> str:
    result = _text(value, name, required=required)
    if result and not _ID_RE.fullmatch(result):
        raise ProblemLineageError(f"{name} must be an opaque bounded identifier")
    return result


def _enum(value: Any, name: str, allowed: frozenset[str], *, default: str = "") -> str:
    result = _text(value, name).upper() if allowed and next(iter(allowed)).upper() == next(iter(allowed)) else _text(value, name)
    if not result and default:
        result = default
    if result not in allowed:
        raise ProblemLineageError(f"{name} is invalid")
    return result


def _upper_enum(value: Any, name: str, allowed: frozenset[str], *, default: str) -> str:
    result = _text(value, name).upper() or default
    if result not in allowed:
        raise ProblemLineageError(f"{name} is invalid")
    return result


def _lower_enum(value: Any, name: str, allowed: frozenset[str], *, default: str) -> str:
    result = _text(value, name).lower() or default
    if result not in allowed:
        raise ProblemLineageError(f"{name} is invalid")
    return result


def _bool(value: Any, name: str, *, default: bool = False) -> bool:
    if value is None:
        return default
    if type(value) is not bool:
        raise ProblemLineageError(f"{name} must be boolean")
    return value


def _nonnegative_int(value: Any, name: str, *, default: int = 0, maximum: int = 10_000) -> int:
    if value is None:
        return default
    if isinstance(value, bool) or not isinstance(value, int) or value < 0 or value > maximum:
        raise ProblemLineageError(f"{name} must be a bounded nonnegative integer")
    return value


def _normalize_problem_event(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ProblemLineageError("problem_event must be an object")
    allowed = {
        "operation", "event_id", "problem_id", "task_id", "turn_id", "trace_id", "run_id", "wave_id", "capsule_id",
        "conversation_epoch", "task_class", "engineering_floor", "relation_type", "link_status", "link_role",
        "feedback_intent", "causal_mechanism", "economic_class", "provenance", "evidence_level", "eligible_for_policy",
        "state", "reason_code", "criteria_count", "criteria_fingerprint", "event_time",
    }
    unexpected = sorted(set(value) - allowed)
    if unexpected:
        raise ProblemLineageError("problem_event contains disallowed fields")
    operation = _lower_enum(value.get("operation"), "operation", PROBLEM_OPERATIONS, default="get")
    event_id = _opaque_id(value.get("event_id"), "event_id", required=operation != "get")
    problem_id = _opaque_id(value.get("problem_id"), "problem_id")
    if operation == "open" and not problem_id:
        # `event_id` is caller-generated opaque randomness.  Deriving the
        # thread identity from it preserves open replay/idempotency without
        # storing semantic request text or requiring a second random seed.
        problem_id = f"prl-{hashlib.sha256(event_id.encode('utf-8')).hexdigest()[:32]}"
    if operation != "get" and operation != "open" and not problem_id:
        status = _upper_enum(value.get("link_status"), "link_status", PROBLEM_LINK_STATUSES, default="EXACT")
        if status == "EXACT":
            raise ProblemLineageError("exact problem event requires problem_id")
    task_class = _lower_enum(value.get("task_class"), "task_class", PROBLEM_TASK_CLASSES, default="unknown")
    engineering_floor = _upper_enum(value.get("engineering_floor"), "engineering_floor", PROBLEM_ENGINEERING_FLOORS, default="UNKNOWN")
    link_status = _upper_enum(value.get("link_status"), "link_status", PROBLEM_LINK_STATUSES, default="EXACT")
    link_role = _upper_enum(value.get("link_role"), "link_role", PROBLEM_LINK_ROLES, default="PRIMARY")
    relation_type = _upper_enum(value.get("relation_type"), "relation_type", PROBLEM_RELATION_TYPES, default={
        "open": "OPEN", "link": "LINK", "feedback": "USER_FEEDBACK", "resolution": "PROVISIONAL_RESOLUTION", "reopen": "REOPEN", "get": "LINK",
    }[operation])
    feedback_intent = _upper_enum(value.get("feedback_intent"), "feedback_intent", PROBLEM_FEEDBACK_INTENTS, default="UNKNOWN")
    causal_mechanism = _upper_enum(value.get("causal_mechanism"), "causal_mechanism", PROBLEM_CAUSAL_MECHANISMS, default="UNKNOWN")
    economic_class = _upper_enum(value.get("economic_class"), "economic_class", PROBLEM_ECONOMIC_CLASSES, default="UNKNOWN")
    provenance = _upper_enum(value.get("provenance"), "provenance", PROBLEM_PROVENANCE, default="UNKNOWN")
    evidence_level = _upper_enum(value.get("evidence_level"), "evidence_level", PROBLEM_EVIDENCE_LEVELS, default="UNKNOWN")
    eligible_for_policy = _bool(value.get("eligible_for_policy"), "eligible_for_policy", default=False)
    criteria_count = _nonnegative_int(value.get("criteria_count"), "criteria_count")
    criteria_fingerprint = _text(value.get("criteria_fingerprint"), "criteria_fingerprint", limit=64).lower()
    if criteria_fingerprint and not _FP_RE.fullmatch(criteria_fingerprint):
        raise ProblemLineageError("criteria_fingerprint must be a SHA-256 digest")
    if criteria_count and not criteria_fingerprint:
        raise ProblemLineageError("criteria_fingerprint is required when criteria_count is positive")
    if not criteria_count and criteria_fingerprint:
        raise ProblemLineageError("criteria_fingerprint is not allowed when criteria_count is zero")
    if link_status != "EXACT":
        if problem_id:
            raise ProblemLineageError("ambiguous or unlinked events must not attach a problem_id")
        if eligible_for_policy:
            raise ProblemLineageError("ambiguous or unlinked events are not policy eligible")
    if eligible_for_policy and (provenance not in _AUTOMATIC_POLICY_PROVENANCE or evidence_level not in {"OBSERVED", "DERIVED_HIGH_CONFIDENCE"}):
        raise ProblemLineageError("problem event lacks sufficient provenance for policy eligibility")
    state = _upper_enum(value.get("state"), "state", PROBLEM_STATES, default="OPEN")
    if operation == "reopen":
        state = "REOPENED"
    if operation == "feedback" and feedback_intent == "CONFIRM_RESOLVED":
        state = "RESOLVED_CONFIRMED"
    if operation == "feedback" and feedback_intent in {"PARTIAL_RESOLUTION", "SAME_PROBLEM_STILL_FAILING", "CORRECT_UNDERSTANDING", "CORRECT_TARGET_OR_SCOPE", "CORRECT_TECHNICAL_RESULT", "CORRECT_PROOF_OR_VERIFICATION"}:
        state = "REOPENED"
    reason_code = _lower_enum(value.get("reason_code"), "reason_code", PROBLEM_REASON_CODES, default="none")
    event_time = _text(value.get("event_time"), "event_time", limit=128)
    return {
        "operation": operation,
        "event_id": event_id,
        "problem_id": problem_id,
        "task_id": _opaque_id(value.get("task_id"), "task_id"),
        "turn_id": _opaque_id(value.get("turn_id"), "turn_id"),
        "trace_id": _opaque_id(value.get("trace_id"), "trace_id"),
        "run_id": _opaque_id(value.get("run_id"), "run_id"),
        "wave_id": _opaque_id(value.get("wave_id"), "wave_id"),
        "capsule_id": _opaque_id(value.get("capsule_id"), "capsule_id"),
        "conversation_epoch": _nonnegative_int(value.get("conversation_epoch"), "conversation_epoch", default=0, maximum=1_000_000),
        "task_class": task_class,
        "engineering_floor": engineering_floor,
        "relation_type": relation_type,
        "link_status": link_status,
        "link_role": link_role,
        "feedback_intent": feedback_intent,
        "causal_mechanism": causal_mechanism,
        "economic_class": economic_class,
        "provenance": provenance,
        "evidence_level": evidence_level,
        "eligible_for_policy": eligible_for_policy,
        "state": state,
        "reason_code": reason_code,
        "criteria_count": criteria_count,
        "criteria_fingerprint": criteria_fingerprint,
        "event_time": event_time,
    }


def _event_projection(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "seq": int(row["seq"]), "event_id": str(row["event_id"]), "problem_id": row["problem_id"],
        "task_id": str(row["task_id"]), "turn_id": str(row["turn_id"]), "trace_id": str(row["trace_id"]),
        "run_id": str(row["run_id"]), "wave_id": str(row["wave_id"]), "capsule_id": str(row["capsule_id"]),
        "conversation_epoch": int(row["conversation_epoch"]), "relation_type": str(row["relation_type"]),
        "link_status": str(row["link_status"]), "link_role": str(row["link_role"]),
        "feedback_intent": str(row["feedback_intent"]), "causal_mechanism": str(row["causal_mechanism"]),
        "economic_class": str(row["economic_class"]), "provenance": str(row["provenance"]),
        "evidence_level": str(row["evidence_level"]), "eligible_for_policy": bool(row["eligible_for_policy"]),
        "state_before": str(row["state_before"]), "state_after": str(row["state_after"]),
        "reason_code": str(row["reason_code"]), "criteria_count": int(row["criteria_count"]),
        "criteria_fingerprint": str(row["criteria_fingerprint"]), "event_time": str(row["event_time"]),
        "prev_hash": str(row["prev_hash"]), "event_hash": str(row["event_hash"]),
    }


def _thread_projection(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "problem_id": str(row["problem_id"]), "current_revision": int(row["current_revision"]),
        "resolution_state": str(row["resolution_state"]), "task_class": str(row["task_class"]),
        "engineering_floor": str(row["engineering_floor"]), "created_at": str(row["created_at"]),
        "updated_at": str(row["updated_at"]), "closed_at": str(row["closed_at"] or "") or None,
        "latest_problem_event_seq": int(row["latest_problem_event_seq"]),
        "latest_problem_event_hash": str(row["latest_problem_event_hash"]),
    }


def problem_event_hash_material(value: dict[str, Any], *, state_before: str, state_after: str, prev_hash: str) -> dict[str, Any]:
    """Hash only durable event columns; thread-only input is not duplicated."""
    fields = (
        "event_id", "problem_id", "task_id", "turn_id", "trace_id", "run_id", "wave_id", "capsule_id",
        "conversation_epoch", "relation_type", "link_status", "link_role", "feedback_intent", "causal_mechanism",
        "economic_class", "provenance", "evidence_level", "eligible_for_policy", "reason_code", "criteria_count",
        "criteria_fingerprint", "event_time",
    )
    return {**{field: value.get(field) for field in fields}, "state_before": state_before, "state_after": state_after, "prev_hash": prev_hash}


# Backward-compatible private alias for the existing storage implementation.
_event_hash_material = problem_event_hash_material


class ProblemLineageLedgerMixin:
    """Additive v10 PRL schema and typed append-only event operations."""

    @staticmethod
    def _problem_ensure_schema(connection: sqlite3.Connection) -> None:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS problem_threads (
                problem_id TEXT PRIMARY KEY,
                current_revision INTEGER NOT NULL,
                resolution_state TEXT NOT NULL,
                task_class TEXT NOT NULL,
                engineering_floor TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                closed_at TEXT,
                latest_problem_event_seq INTEGER NOT NULL DEFAULT 0,
                latest_problem_event_hash TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS problem_events (
                seq INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL UNIQUE,
                problem_id TEXT REFERENCES problem_threads(problem_id) ON DELETE RESTRICT,
                task_id TEXT NOT NULL DEFAULT '',
                turn_id TEXT NOT NULL DEFAULT '',
                trace_id TEXT NOT NULL DEFAULT '',
                run_id TEXT NOT NULL DEFAULT '',
                wave_id TEXT NOT NULL DEFAULT '',
                capsule_id TEXT NOT NULL DEFAULT '',
                conversation_epoch INTEGER NOT NULL DEFAULT 0,
                relation_type TEXT NOT NULL,
                link_status TEXT NOT NULL,
                link_role TEXT NOT NULL,
                feedback_intent TEXT NOT NULL,
                causal_mechanism TEXT NOT NULL,
                economic_class TEXT NOT NULL,
                provenance TEXT NOT NULL,
                evidence_level TEXT NOT NULL,
                eligible_for_policy INTEGER NOT NULL DEFAULT 0,
                state_before TEXT NOT NULL DEFAULT '',
                state_after TEXT NOT NULL DEFAULT '',
                reason_code TEXT NOT NULL DEFAULT 'none',
                criteria_count INTEGER NOT NULL DEFAULT 0,
                criteria_fingerprint TEXT NOT NULL DEFAULT '',
                request_hash TEXT NOT NULL,
                event_time TEXT NOT NULL,
                prev_hash TEXT NOT NULL DEFAULT '',
                event_hash TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_problem_events_problem_seq ON problem_events(problem_id, seq);
            CREATE INDEX IF NOT EXISTS idx_problem_events_task_turn ON problem_events(task_id, turn_id, seq);
            CREATE INDEX IF NOT EXISTS idx_problem_events_run_wave ON problem_events(run_id, wave_id, seq);
            CREATE UNIQUE INDEX IF NOT EXISTS idx_problem_events_one_primary_run_binding
                ON problem_events(run_id)
                WHERE run_id<>'' AND link_status='EXACT' AND link_role='PRIMARY'
                  AND relation_type IN ('LINK', 'ENGINEERING_ATTEMPT_BOUND');
            """
        )

    def problem_lineage_schema_version(self) -> int:
        with self._lock, self._connect() as connection:
            row = connection.execute("PRAGMA user_version").fetchone()
        return int(row[0] if row is not None else 0)

    def migrate_problem_lineage_schema(self, *, expected_schema_version: int = 9) -> dict[str, Any]:
        """Forward-only local v9 -> v10 activation; never called by constructor.

        The caller must establish the stopped-writer/backup authority outside
        this source primitive.  No task-control action exposes this migration.
        """
        if expected_schema_version != 9:
            raise ProblemLineageError("PRL migration requires explicit expected schema version 9")
        with self._lock, self._connect() as connection:
            current = int(connection.execute("PRAGMA user_version").fetchone()[0])
            if current == PROBLEM_SCHEMA_VERSION:
                return {"migrated": False, "schema_version": current}
            if current != expected_schema_version:
                raise ProblemLineageError(f"PRL migration requires schema v{expected_schema_version}, found v{current}")
            self._problem_ensure_schema(connection)
            connection.execute(f"PRAGMA user_version={PROBLEM_SCHEMA_VERSION}")
        return {"migrated": True, "schema_version": PROBLEM_SCHEMA_VERSION}

    def _problem_require_schema(self, connection: sqlite3.Connection) -> None:
        current = int(connection.execute("PRAGMA user_version").fetchone()[0])
        if current != PROBLEM_SCHEMA_VERSION:
            raise ProblemLineageError("PRL schema is not activated; supported v9-to-v10 migration authority is required")

    def problem_record_event(self, event: dict[str, Any], *, now: str) -> dict[str, Any]:
        normalized = _normalize_problem_event(event)
        if normalized["operation"] == "get":
            raise ProblemLineageError("get does not record a problem event")
        if not normalized["event_time"]:
            normalized["event_time"] = now
        request_material = {key: value for key, value in normalized.items() if key != "event_time"}
        request_hash = hashlib.sha256(_json(request_material).encode("utf-8")).hexdigest()
        with self._lock, self._connect() as connection:
            self._problem_require_schema(connection)
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute("SELECT * FROM problem_events WHERE event_id=?", (normalized["event_id"],)).fetchone()
            if existing is not None:
                projected = _event_projection(existing)
                if str(existing["request_hash"] or "") != request_hash:
                    raise ProblemLineageError("problem event id conflicts with immutable prior bytes")
                return {"recorded": False, "idempotent": True, "event": projected, "thread": self.problem_get(str(projected.get("problem_id") or ""), connection=connection)}

            thread: sqlite3.Row | None = None
            if normalized["problem_id"]:
                thread = connection.execute("SELECT * FROM problem_threads WHERE problem_id=?", (normalized["problem_id"],)).fetchone()
            if normalized["operation"] == "open":
                if thread is not None:
                    raise ProblemLineageError("open cannot reuse an existing problem_id")
                state_before = ""
                state_after = "OPEN"
                revision = 1
                connection.execute(
                    """INSERT INTO problem_threads(problem_id,current_revision,resolution_state,task_class,engineering_floor,created_at,updated_at,closed_at,latest_problem_event_seq,latest_problem_event_hash)
                       VALUES(?,?,?,?,?,?,?,?,?,?)""",
                    (normalized["problem_id"], revision, state_after, normalized["task_class"], normalized["engineering_floor"], now, now, None, 0, ""),
                )
            elif normalized["link_status"] != "EXACT":
                state_before = ""
                state_after = ""
                revision = 0
            else:
                if thread is None:
                    raise ProblemLineageError("exact problem event references an unknown problem_id")
                state_before = str(thread["resolution_state"])
                state_after = normalized["state"] if normalized["operation"] in {"feedback", "resolution", "reopen"} else state_before
                if normalized["operation"] == "link":
                    state_after = state_before
                if normalized["operation"] == "resolution" and normalized["state"] == "OPEN":
                    state_after = "PROVISIONALLY_RESOLVED"
                allowed = {
                    "OPEN": {"OPEN", "PROVISIONALLY_RESOLVED", "REOPENED", "SUPERSEDED", "BLOCKED", "ABANDONED"},
                    "REOPENED": {"REOPENED", "PROVISIONALLY_RESOLVED", "SUPERSEDED", "BLOCKED", "ABANDONED"},
                    "PROVISIONALLY_RESOLVED": {"PROVISIONALLY_RESOLVED", "RESOLVED_CONFIRMED", "RESOLVED_UNCONFIRMED", "REOPENED", "SUPERSEDED", "BLOCKED", "ABANDONED"},
                    "RESOLVED_CONFIRMED": {"RESOLVED_CONFIRMED", "REOPENED", "SUPERSEDED"},
                    "RESOLVED_UNCONFIRMED": {"RESOLVED_UNCONFIRMED", "REOPENED", "SUPERSEDED"},
                    "BLOCKED": {"BLOCKED", "OPEN", "REOPENED", "ABANDONED", "SUPERSEDED"},
                    "SUPERSEDED": {"SUPERSEDED"},
                    "ABANDONED": {"ABANDONED", "REOPENED"},
                }
                if state_after not in allowed.get(state_before, set()):
                    raise ProblemLineageError("problem state transition is invalid")
                revision = int(thread["current_revision"]) + (1 if state_after == "REOPENED" and state_before != "REOPENED" else 0)

            if normalized["run_id"] and normalized["link_status"] == "EXACT" and normalized["link_role"] == "PRIMARY" and normalized["relation_type"] in {"LINK", "ENGINEERING_ATTEMPT_BOUND"}:
                primary = connection.execute(
                    "SELECT problem_id FROM problem_events WHERE run_id=? AND link_status='EXACT' AND link_role='PRIMARY' AND relation_type IN ('LINK','ENGINEERING_ATTEMPT_BOUND')",
                    (normalized["run_id"],),
                ).fetchone()
                if primary is not None:
                    if str(primary["problem_id"] or "") != normalized["problem_id"]:
                        raise ProblemLineageError("a run already has a different primary problem")
                    raise ProblemLineageError("a run already has a primary problem binding")

            previous = connection.execute(
                "SELECT seq,event_hash FROM problem_events WHERE problem_id=? ORDER BY seq DESC LIMIT 1",
                (normalized["problem_id"],),
            ).fetchone() if normalized["problem_id"] else None
            prev_hash = str(previous["event_hash"] or "") if previous is not None else ""
            material = _event_hash_material(normalized, state_before=state_before, state_after=state_after, prev_hash=prev_hash)
            event_hash = hashlib.sha256(_json(material).encode("utf-8")).hexdigest()
            connection.execute(
                """INSERT INTO problem_events(event_id,problem_id,task_id,turn_id,trace_id,run_id,wave_id,capsule_id,conversation_epoch,relation_type,link_status,link_role,feedback_intent,causal_mechanism,economic_class,provenance,evidence_level,eligible_for_policy,state_before,state_after,reason_code,criteria_count,criteria_fingerprint,request_hash,event_time,prev_hash,event_hash)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (normalized["event_id"], normalized["problem_id"] or None, normalized["task_id"], normalized["turn_id"], normalized["trace_id"], normalized["run_id"], normalized["wave_id"], normalized["capsule_id"], normalized["conversation_epoch"], normalized["relation_type"], normalized["link_status"], normalized["link_role"], normalized["feedback_intent"], normalized["causal_mechanism"], normalized["economic_class"], normalized["provenance"], normalized["evidence_level"], int(normalized["eligible_for_policy"]), state_before, state_after, normalized["reason_code"], normalized["criteria_count"], normalized["criteria_fingerprint"], request_hash, normalized["event_time"], prev_hash, event_hash),
            )
            stored = connection.execute("SELECT * FROM problem_events WHERE event_id=?", (normalized["event_id"],)).fetchone()
            assert stored is not None
            event_row = _event_projection(stored)
            if normalized["problem_id"]:
                closed_at = now if state_after in _CLOSED_STATES else None
                connection.execute(
                    """UPDATE problem_threads SET current_revision=?, resolution_state=?, updated_at=?, closed_at=?, latest_problem_event_seq=?, latest_problem_event_hash=? WHERE problem_id=?""",
                    (revision, state_after, now, closed_at, event_row["seq"], event_hash, normalized["problem_id"]),
                )
            thread_result = self.problem_get(normalized["problem_id"], connection=connection) if normalized["problem_id"] else None
        return {"recorded": True, "idempotent": False, "event": event_row, "thread": thread_result}

    def problem_get(self, problem_id: str, *, connection: sqlite3.Connection | None = None, limit: int = 200) -> dict[str, Any] | None:
        normalized_problem_id = _opaque_id(problem_id, "problem_id", required=True)
        owns_connection = connection is None
        if owns_connection:
            with self._lock, self._connect() as active_connection:
                self._problem_require_schema(active_connection)
                return self.problem_get(normalized_problem_id, connection=active_connection, limit=limit)
        assert connection is not None
        row = connection.execute("SELECT * FROM problem_threads WHERE problem_id=?", (normalized_problem_id,)).fetchone()
        if row is None:
            return None
        bounded_limit = max(1, min(int(limit), 500))
        events = connection.execute("SELECT * FROM problem_events WHERE problem_id=? ORDER BY seq LIMIT ?", (normalized_problem_id, bounded_limit)).fetchall()
        return {"thread": _thread_projection(row), "events": [_event_projection(item) for item in events], "events_truncated": len(events) >= bounded_limit}

    def problem_find_exact_host_identity(self, *, turn_id: str, trace_id: str) -> dict[str, Any]:
        """Resolve an already-recorded host turn only when it names one thread.

        This is a lookup, not a proximity join: both opaque IDs must be exact.
        A v9 ledger intentionally returns ``schema_inactive`` so normal
        execution remains unchanged before the separately authorized v10
        migration.  Multiple distinct threads are reported as ambiguous rather
        than picking a newest event or merging problem history.
        """
        normalized_turn_id = _opaque_id(turn_id, "turn_id", required=True)
        normalized_trace_id = _opaque_id(trace_id, "trace_id", required=True)
        with self._lock, self._connect() as connection:
            current = int(connection.execute("PRAGMA user_version").fetchone()[0])
            if current != PROBLEM_SCHEMA_VERSION:
                return {"status": "schema_inactive", "problem_id": None}
            rows = connection.execute(
                """SELECT DISTINCT problem_id FROM problem_events
                   WHERE turn_id=? AND trace_id=? AND link_status='EXACT'
                     AND problem_id IS NOT NULL AND problem_id<>''
                   ORDER BY problem_id""",
                (normalized_turn_id, normalized_trace_id),
            ).fetchall()
        problem_ids = [str(row["problem_id"] or "") for row in rows if str(row["problem_id"] or "")]
        if len(problem_ids) == 1:
            return {"status": "exact", "problem_id": problem_ids[0]}
        if len(problem_ids) > 1:
            return {"status": "ambiguous", "problem_id": None, "candidate_count": len(problem_ids)}
        return {"status": "unlinked", "problem_id": None}

    def problem_handoff_for_run(self, run_id: str) -> dict[str, Any] | None:
        """Return a derived, content-free PRL capsule for one exact run link."""
        normalized_run_id = _opaque_id(run_id, "run_id", required=True)
        with self._lock, self._connect() as connection:
            current = int(connection.execute("PRAGMA user_version").fetchone()[0])
            if current != PROBLEM_SCHEMA_VERSION:
                return None
            rows = connection.execute(
                """SELECT DISTINCT problem_id FROM problem_events
                   WHERE run_id=? AND link_status='EXACT' AND link_role='PRIMARY'
                     AND relation_type IN ('LINK','ENGINEERING_ATTEMPT_BOUND')
                     AND problem_id IS NOT NULL AND problem_id<>''
                   ORDER BY problem_id""",
                (normalized_run_id,),
            ).fetchall()
            problem_ids = [str(row["problem_id"] or "") for row in rows if str(row["problem_id"] or "")]
            if len(problem_ids) != 1:
                return None
            result = self.problem_get(problem_ids[0], connection=connection, limit=500)
        if result is None:
            return None
        thread = result["thread"]
        events = result["events"]
        latest_feedback = next((item for item in reversed(events) if item["relation_type"] == "USER_FEEDBACK"), None)
        latest_criteria = next((item for item in reversed(events) if int(item["criteria_count"]) > 0), None)
        unresolved = str(thread["resolution_state"]) not in _CLOSED_STATES
        return {
            "active_problem_id": thread["problem_id"],
            "problem_revision": thread["current_revision"],
            "problem_state": thread["resolution_state"],
            "latest_feedback_relation": str((latest_feedback or {}).get("feedback_intent") or "UNKNOWN"),
            "latest_correction_class": str((latest_feedback or {}).get("economic_class") or "UNKNOWN"),
            "unresolved_criteria_count": int((latest_criteria or {}).get("criteria_count") or 0) if unresolved else 0,
            "unresolved_criteria_set_fp": str((latest_criteria or {}).get("criteria_fingerprint") or "") if unresolved else "",
        }

    def problem_verify_chain(self, problem_id: str) -> dict[str, Any]:
        result = self.problem_get(problem_id, limit=500)
        if result is None:
            raise ProblemLineageError("problem was not found")
        previous = ""
        for event in result["events"]:
            if event["prev_hash"] != previous:
                return {"ok": False, "reason": "prev_hash_mismatch", "seq": event["seq"]}
            material = _event_hash_material(event, state_before=event["state_before"], state_after=event["state_after"], prev_hash=previous)
            if hashlib.sha256(_json(material).encode("utf-8")).hexdigest() != event["event_hash"]:
                return {"ok": False, "reason": "event_hash_mismatch", "seq": event["seq"]}
            previous = event["event_hash"]
        return {"ok": True, "event_count": len(result["events"]), "last_event_hash": previous}
