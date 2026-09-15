from __future__ import annotations

"""Durable, content-free telemetry for long-running controller continuity.

This domain deliberately stores only typed machine facts.  It never accepts a
free-form payload, prompt, transcript, source, command output, or reasoning.
"""

import hashlib
import json
import re
import sqlite3
from datetime import datetime, timezone
from typing import Any

from .ledger_event_chain import append_hash_chained_event


CONTINUITY_TELEMETRY_EVENT_TYPES = frozenset(
    {
        "manual_nudge",
        "interruption",
        "replan",
        "report_gate",
        "continuation_attempt",
        "continuation_success",
        "continuation_failure",
        "reconnect",
        "restart",
        "resume",
        "duplicate_effect_prevented",
        "terminal",
        "blocker",
        "accepted_checkpoint",
    }
)
CONTINUITY_TELEMETRY_OUTCOMES = frozenset(
    {"", "attempted", "observed", "succeeded", "failed", "prevented", "blocked", "terminal", "pending"}
)
CONTINUITY_TELEMETRY_PROVENANCE = frozenset({"natural", "synthetic", "legacy_unknown"})
_ID_RE = re.compile(r"^[A-Za-z0-9_.:@-]+$")
_MAX_ID = 256
_MAX_CODE = 128
_MAX_DURATION_MS = 30 * 24 * 60 * 60 * 1000


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _typed_id(value: Any, field: str, *, required: bool = False, limit: int = _MAX_ID) -> str:
    text = str(value or "").strip()
    if not text:
        if required:
            raise ValueError(f"CONTINUITY_TELEMETRY_{field.upper()}_REQUIRED")
        return ""
    if len(text) > limit or _ID_RE.fullmatch(text) is None:
        raise ValueError(f"CONTINUITY_TELEMETRY_{field.upper()}_INVALID")
    return text


def _row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "logical_id": str(row["logical_id"]),
        "run_id": str(row["run_id"]),
        "wave_id": str(row["wave_id"]),
        "event_type": str(row["event_type"]),
        "problem_id": str(row["problem_id"]),
        "problem_revision": int(row["problem_revision"]),
        "task_context_id": str(row["task_context_id"]),
        "activation_epoch_id": str(row["activation_epoch_id"]),
        "process_instance_id": str(row["process_instance_id"]),
        "server_instance_id": str(row["server_instance_id"]),
        "restart_ticket_id": str(row["restart_ticket_id"]),
        "outcome": str(row["outcome"]),
        "code": str(row["code"]),
        "duration_ms": None if row["duration_ms"] is None else int(row["duration_ms"]),
        "provenance": str(row["provenance"] or "legacy_unknown"),
        "event_time": str(row["event_time"]),
        "record_sha256": str(row["record_sha256"]),
    }


def _identity_payload(record: dict[str, Any]) -> dict[str, Any]:
    return {key: record[key] for key in (
        "logical_id", "run_id", "wave_id", "event_type", "problem_id", "problem_revision",
        "task_context_id", "activation_epoch_id", "process_instance_id", "server_instance_id",
        "restart_ticket_id", "outcome", "code", "duration_ms",
    )}


class ContinuityTelemetryLedgerMixin:
    """Typed optimization telemetry stored in the canonical orchestration DB."""

    @staticmethod
    def _continuity_telemetry_ensure_schema(connection: sqlite3.Connection) -> None:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS continuity_telemetry (
                logical_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
                wave_id TEXT NOT NULL DEFAULT '',
                event_type TEXT NOT NULL,
                problem_id TEXT NOT NULL DEFAULT '',
                problem_revision INTEGER NOT NULL DEFAULT 0 CHECK(problem_revision>=0),
                task_context_id TEXT NOT NULL DEFAULT '',
                activation_epoch_id TEXT NOT NULL DEFAULT '',
                process_instance_id TEXT NOT NULL DEFAULT '',
                server_instance_id TEXT NOT NULL DEFAULT '',
                restart_ticket_id TEXT NOT NULL DEFAULT '',
                outcome TEXT NOT NULL DEFAULT '',
                code TEXT NOT NULL DEFAULT '',
                duration_ms INTEGER,
                provenance TEXT NOT NULL DEFAULT 'legacy_unknown'
                    CHECK(provenance IN ('natural','synthetic','legacy_unknown')),
                event_time TEXT NOT NULL,
                record_sha256 TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_continuity_telemetry_run_time
                ON continuity_telemetry(run_id,event_time,logical_id);
            CREATE INDEX IF NOT EXISTS idx_continuity_telemetry_problem_time
                ON continuity_telemetry(problem_id,problem_revision,event_time,logical_id);
            CREATE INDEX IF NOT EXISTS idx_continuity_telemetry_type_time
                ON continuity_telemetry(event_type,event_time,logical_id);
            """
        )
        columns = {
            str(row["name"] if isinstance(row, sqlite3.Row) else row[1])
            for row in connection.execute("PRAGMA table_info(continuity_telemetry)").fetchall()
        }
        if "provenance" not in columns:
            connection.execute(
                "ALTER TABLE continuity_telemetry ADD COLUMN provenance TEXT NOT NULL "
                "DEFAULT 'legacy_unknown' CHECK(provenance IN ('natural','synthetic','legacy_unknown'))"
            )

    def record_continuity_telemetry(
        self,
        *,
        logical_id: str,
        run_id: str,
        event_type: str,
        wave_id: str = "",
        problem_id: str = "",
        problem_revision: int = 0,
        task_context_id: str = "",
        activation_epoch_id: str = "",
        process_instance_id: str = "",
        server_instance_id: str = "",
        restart_ticket_id: str = "",
        outcome: str = "",
        code: str = "",
        duration_ms: int | None = None,
        provenance: str = "legacy_unknown",
    ) -> dict[str, Any]:
        logical = _typed_id(logical_id, "logical_id", required=True)
        run = _typed_id(run_id, "run_id", required=True)
        wave = _typed_id(wave_id, "wave_id")
        kind = str(event_type or "").strip().lower()
        if kind not in CONTINUITY_TELEMETRY_EVENT_TYPES:
            raise ValueError("CONTINUITY_TELEMETRY_EVENT_TYPE_INVALID")
        problem = _typed_id(problem_id, "problem_id")
        revision = int(problem_revision or 0)
        if problem and revision < 1:
            raise ValueError("CONTINUITY_TELEMETRY_PROBLEM_REVISION_REQUIRED")
        if not problem and revision != 0:
            raise ValueError("CONTINUITY_TELEMETRY_PROBLEM_REVISION_INVALID")
        result = str(outcome or "").strip().lower()
        if result not in CONTINUITY_TELEMETRY_OUTCOMES:
            raise ValueError("CONTINUITY_TELEMETRY_OUTCOME_INVALID")
        evidence_provenance = str(provenance or "").strip().lower()
        if evidence_provenance not in CONTINUITY_TELEMETRY_PROVENANCE:
            raise ValueError("CONTINUITY_TELEMETRY_PROVENANCE_INVALID")
        machine_code = _typed_id(code, "code", limit=_MAX_CODE)
        duration: int | None
        if duration_ms is None:
            duration = None
        else:
            duration = int(duration_ms)
            if duration < 0 or duration > _MAX_DURATION_MS:
                raise ValueError("CONTINUITY_TELEMETRY_DURATION_INVALID")
        record = {
            "logical_id": logical,
            "run_id": run,
            "wave_id": wave,
            "event_type": kind,
            "problem_id": problem,
            "problem_revision": revision,
            "task_context_id": _typed_id(task_context_id, "task_context_id"),
            "activation_epoch_id": _typed_id(activation_epoch_id, "activation_epoch_id"),
            "process_instance_id": _typed_id(process_instance_id, "process_instance_id"),
            "server_instance_id": _typed_id(server_instance_id, "server_instance_id"),
            "restart_ticket_id": _typed_id(restart_ticket_id, "restart_ticket_id"),
            "outcome": result,
            "code": machine_code,
            "duration_ms": duration,
            "provenance": evidence_provenance,
        }
        # Provenance is attribution metadata, not event identity. Excluding it
        # preserves legacy digests and prevents replay/reconnect from creating
        # duplicates merely because provenance classification changed.
        digest = hashlib.sha256(_json(_identity_payload(record)).encode("utf-8")).hexdigest()
        event_time = _now()
        with self._lock, self._connect() as connection:
            self._continuity_telemetry_ensure_schema(connection)
            connection.execute("BEGIN IMMEDIATE")
            if connection.execute("SELECT 1 FROM runs WHERE run_id=?", (run,)).fetchone() is None:
                raise ValueError("CONTINUITY_TELEMETRY_RUN_NOT_FOUND")
            if wave:
                wave_row = connection.execute("SELECT run_id FROM waves WHERE wave_id=?", (wave,)).fetchone()
                if wave_row is None or str(wave_row["run_id"]) != run:
                    raise ValueError("CONTINUITY_TELEMETRY_WAVE_MISMATCH")
            existing = connection.execute(
                "SELECT * FROM continuity_telemetry WHERE logical_id=?", (logical,)
            ).fetchone()
            if existing is not None:
                current = _row(existing)
                if current["record_sha256"] != digest:
                    raise ValueError("CONTINUITY_TELEMETRY_LOGICAL_ID_CONFLICT")
                connection.commit()
                return {"created": False, "idempotent": True, "event": current}
            connection.execute(
                """INSERT INTO continuity_telemetry(
                    logical_id,run_id,wave_id,event_type,problem_id,problem_revision,task_context_id,
                    activation_epoch_id,process_instance_id,server_instance_id,restart_ticket_id,outcome,
                    code,duration_ms,provenance,event_time,record_sha256
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    logical, run, wave, kind, problem, revision, record["task_context_id"],
                    record["activation_epoch_id"], record["process_instance_id"], record["server_instance_id"],
                    record["restart_ticket_id"], result, machine_code, duration, evidence_provenance, event_time, digest,
                ),
            )
            append_hash_chained_event(
                connection,
                run_id=run,
                event_type="continuity_telemetry_recorded",
                wave_id=wave or None,
                delegation_id=None,
                state_before="",
                state_after="",
                payload={**record, "record_sha256": digest},
                event_time=event_time,
                sanitize=lambda value: value,
                serialize=_json,
                bounded_text=lambda value, limit: str(value or "")[:limit],
            )
            stored = connection.execute(
                "SELECT * FROM continuity_telemetry WHERE logical_id=?", (logical,)
            ).fetchone()
            connection.commit()
        assert stored is not None
        return {"created": True, "idempotent": False, "event": _row(stored)}

    def list_continuity_telemetry(
        self,
        *,
        run_id: str = "",
        problem_id: str = "",
        problem_revision: int = 0,
        limit: int = 200,
    ) -> dict[str, Any]:
        run = _typed_id(run_id, "run_id")
        problem = _typed_id(problem_id, "problem_id")
        revision = int(problem_revision or 0)
        if revision and not problem:
            raise ValueError("CONTINUITY_TELEMETRY_PROBLEM_REQUIRED")
        bounded_limit = max(1, min(int(limit), 1000))
        clauses: list[str] = []
        params: list[Any] = []
        if run:
            clauses.append("run_id=?")
            params.append(run)
        if problem:
            clauses.append("problem_id=?")
            params.append(problem)
            if revision:
                clauses.append("problem_revision=?")
                params.append(revision)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        with self._lock, self._connect() as connection:
            self._continuity_telemetry_ensure_schema(connection)
            rows = connection.execute(
                f"SELECT * FROM continuity_telemetry{where} ORDER BY event_time,logical_id LIMIT ?",
                [*params, bounded_limit + 1],
            ).fetchall()
        truncated = len(rows) > bounded_limit
        return {
            "schema_version": 1,
            "events": [_row(row) for row in rows[:bounded_limit]],
            "truncated": truncated,
            "complete": not truncated,
        }

    def continuity_telemetry_summary(
        self,
        *,
        run_id: str = "",
        problem_id: str = "",
        problem_revision: int = 0,
        limit: int = 1000,
    ) -> dict[str, Any]:
        listed = self.list_continuity_telemetry(
            run_id=run_id,
            problem_id=problem_id,
            problem_revision=problem_revision,
            limit=limit,
        )
        events = listed["events"]
        counts: dict[str, int] = {}
        outcomes: dict[str, int] = {}
        codes: dict[str, int] = {}
        provenance_counts = {key: 0 for key in sorted(CONTINUITY_TELEMETRY_PROVENANCE)}
        durations: dict[str, list[int]] = {}
        for event in events:
            kind = str(event["event_type"])
            counts[kind] = counts.get(kind, 0) + 1
            outcome = str(event["outcome"] or "")
            if outcome:
                outcomes[outcome] = outcomes.get(outcome, 0) + 1
            code = str(event["code"] or "")
            if code:
                codes[code] = codes.get(code, 0) + 1
            evidence_provenance = str(event.get("provenance") or "legacy_unknown")
            provenance_counts[evidence_provenance] = provenance_counts.get(evidence_provenance, 0) + 1
            if event["duration_ms"] is not None:
                durations.setdefault(kind, []).append(int(event["duration_ms"]))

        def duration_summary(kind: str) -> dict[str, int | float] | None:
            values = durations.get(kind) or []
            if not values:
                return None
            total = sum(values)
            return {"count": len(values), "total_ms": total, "max_ms": max(values), "avg_ms": total / len(values)}

        return {
            "schema_version": 1,
            "complete": bool(listed["complete"]),
            "event_count": len(events),
            "counts_by_type": counts,
            "counts_by_outcome": outcomes,
            "counts_by_code": codes,
            "counts_by_provenance": provenance_counts,
            "natural_event_count": provenance_counts.get("natural", 0),
            "synthetic_event_count": provenance_counts.get("synthetic", 0),
            "legacy_unknown_event_count": provenance_counts.get("legacy_unknown", 0),
            "manual_nudge_count": counts.get("manual_nudge", 0),
            "interruption_count": counts.get("interruption", 0),
            "replan_count": counts.get("replan", 0),
            "report_gate_count": counts.get("report_gate", 0),
            "continuation_attempt_count": counts.get("continuation_attempt", 0),
            "continuation_success_count": counts.get("continuation_success", 0),
            "continuation_failure_count": counts.get("continuation_failure", 0),
            "reconnect_count": counts.get("reconnect", 0),
            "restart_count": counts.get("restart", 0),
            "resume_count": counts.get("resume", 0),
            "duplicate_effect_prevented_count": counts.get("duplicate_effect_prevented", 0),
            "terminal_count": counts.get("terminal", 0),
            "blocker_count": counts.get("blocker", 0),
            "accepted_checkpoint_count": counts.get("accepted_checkpoint", 0),
            "time_to_resume_ms": duration_summary("resume"),
            "replan_duration_ms": duration_summary("replan"),
            "report_gate_wait_ms": duration_summary("report_gate"),
        }
