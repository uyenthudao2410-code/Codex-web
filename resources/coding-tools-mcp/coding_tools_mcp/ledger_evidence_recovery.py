"""Guarded evidence-only recovery for the canonical orchestration ledger.

This module reconnects immutable historical evidence to the current ledger.  It
does *not* restore controller authority or effect rows and it never starts,
stops, kills, or restarts a runtime.  The only canonical mutation it performs
is an atomic append of allowlisted immutable rows followed by a compare-and-
swap update of problem-event projection pointers whose tail is proven to be a
non-transitioning, exact, same-revision chain.

The operation is intentionally split into a read-only preflight and an apply
step.  Apply requires an operator quiesce receipt, exact physical/logical
snapshot identities, an exclusive application gate, and a rollback backup.
Unknown effect rows remain in the current ledger exactly as observed; they are
reported as withheld evidence and are never replayed or terminalized.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import tempfile
from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from .ledger_file_gate import ledger_access_gate
from .lifecycle_reconciliation import logical_ledger_sha256
from .ledger_maintenance import inspect_maintenance_readiness


EVIDENCE_TABLES = (
    "runs",
    "waves",
    "checkpoints",
    "proofs",
    "events",
    "problem_events",
    "continuity_telemetry",
    "controller_knowledge_acks",
)

AUTHORITY_TABLES = frozenset(
    {
        "controller_goal_attachments",
        "controller_leases",
        "write_fences",
        "hub_clients",
        "controller_reattach_receipts",
        "checkout_resource_claims",
        "agent_lanes",
        "run_continuations",
        "goal_continuations",
        "hub_client_cursors",
    }
)

EFFECT_TABLES = frozenset(
    {"background_operations", "idempotency_records", "managed_process_jobs"}
)

SAFE_POINTER_RELATIONS = frozenset(
    {"ENGINEERING_ATTEMPT_BOUND", "LINK", "USER_FEEDBACK"}
)

_INSERT_ORDER = (
    "runs",
    "waves",
    "checkpoints",
    "proofs",
    "events",
    "problem_events",
    "continuity_telemetry",
    "controller_knowledge_acks",
)


class LedgerEvidenceRecoveryError(RuntimeError):
    """A guarded evidence recovery invariant did not hold."""


@dataclass(frozen=True)
class RecoverySnapshot:
    physical_sha256: str
    logical_sha256: str
    integrity: str
    foreign_key_rows: int
    schema_version: int
    size_bytes: int

    def projection(self) -> dict[str, Any]:
        return {
            "sha256": self.physical_sha256,
            "logical_sha256": self.logical_sha256,
            "integrity_check": self.integrity,
            "foreign_key_check_rows": self.foreign_key_rows,
            "schema_version": self.schema_version,
            "size_bytes": self.size_bytes,
        }


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _quote(identifier: str) -> str:
    return '"' + str(identifier).replace('"', '""') + '"'


def _table_names(connection: sqlite3.Connection) -> tuple[str, ...]:
    return tuple(
        str(row[0])
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
    )


def _schema_rows(connection: sqlite3.Connection) -> dict[tuple[str, str], str]:
    return {
        (str(row[0]), str(row[1])): str(row[2] or "")
        for row in connection.execute(
            "SELECT type,name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name"
        )
    }


def _table_columns(connection: sqlite3.Connection, table: str) -> tuple[list[str], list[str]]:
    info = list(connection.execute(f"PRAGMA table_info({_quote(table)})"))
    columns = [str(row[1]) for row in info]
    primary = [str(row[1]) for row in sorted(info, key=lambda row: row[5]) if row[5]]
    if not primary:
        raise LedgerEvidenceRecoveryError(f"RECOVERY_TABLE_WITHOUT_PRIMARY_KEY:{table}")
    return columns, primary


def _keyed_rows(connection: sqlite3.Connection, table: str) -> tuple[list[str], dict[tuple[Any, ...], tuple[Any, ...]]]:
    columns, primary = _table_columns(connection, table)
    indices = [columns.index(name) for name in primary]
    result: dict[tuple[Any, ...], tuple[Any, ...]] = {}
    for raw in connection.execute(f"SELECT * FROM {_quote(table)}"):
        values = tuple(raw)
        key = tuple(values[index] for index in indices)
        if key in result:
            raise LedgerEvidenceRecoveryError(f"RECOVERY_DUPLICATE_IDENTITY:{table}")
        result[key] = values
    return columns, result


def _open_readonly(path: Path, *, immutable: bool) -> sqlite3.Connection:
    if immutable:
        uri = path.resolve(strict=True).as_uri() + "?mode=ro&immutable=1"
        connection = sqlite3.connect(uri, uri=True, timeout=5.0)
    else:
        uri = path.resolve(strict=True).as_uri() + "?mode=ro"
        connection = sqlite3.connect(uri, uri=True, timeout=5.0)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    connection.execute("PRAGMA busy_timeout=5000")
    return connection


def _open_writer(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path, timeout=5.0)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA busy_timeout=5000")
    return connection


def _snapshot(path: Path, *, immutable: bool) -> RecoverySnapshot:
    connection = _open_readonly(path, immutable=immutable)
    try:
        integrity = str(connection.execute("PRAGMA integrity_check").fetchone()[0] or "")
        foreign_keys = list(connection.execute("PRAGMA foreign_key_check"))
        schema_row = connection.execute("PRAGMA user_version").fetchone()
        return RecoverySnapshot(
            physical_sha256=_sha256_file(path),
            logical_sha256=logical_ledger_sha256(connection),
            integrity=integrity,
            foreign_key_rows=len(foreign_keys),
            schema_version=int(schema_row[0] if schema_row else 0),
            size_bytes=int(path.stat().st_size),
        )
    finally:
        connection.close()


def _assert_snapshot(snapshot: RecoverySnapshot, *, label: str) -> None:
    if snapshot.integrity.lower() != "ok":
        raise LedgerEvidenceRecoveryError(f"{label}_INTEGRITY_FAILED")
    if snapshot.foreign_key_rows:
        raise LedgerEvidenceRecoveryError(f"{label}_FOREIGN_KEY_FAILED")


def _validate_expected_snapshot(
    snapshot: RecoverySnapshot,
    expected: dict[str, str],
    *,
    label: str,
) -> None:
    _assert_snapshot(snapshot, label=label)
    for key, actual in (
        ("sha256", snapshot.physical_sha256),
        ("logical_sha256", snapshot.logical_sha256),
    ):
        requested = str(expected.get(key) or "").strip().lower()
        if requested and requested != actual.lower():
            raise LedgerEvidenceRecoveryError(f"{label}_{key.upper()}_MISMATCH")


def _table_diffs(
    current: sqlite3.Connection,
    candidate: sqlite3.Connection,
) -> tuple[dict[str, list[tuple[Any, ...]]], dict[str, int], dict[str, int]]:
    current_tables = _table_names(current)
    if current_tables != _table_names(candidate):
        raise LedgerEvidenceRecoveryError("RECOVERY_SCHEMA_TABLE_SET_MISMATCH")
    schema_current = _schema_rows(current)
    if schema_current != _schema_rows(candidate):
        raise LedgerEvidenceRecoveryError("RECOVERY_SCHEMA_DEFINITION_MISMATCH")
    additions: dict[str, list[tuple[Any, ...]]] = {}
    withheld: dict[str, int] = {}
    unexpected: dict[str, int] = {}
    for table in current_tables:
        current_columns, current_rows = _keyed_rows(current, table)
        candidate_columns, candidate_rows = _keyed_rows(candidate, table)
        if current_columns != candidate_columns:
            raise LedgerEvidenceRecoveryError(f"RECOVERY_SCHEMA_COLUMNS_MISMATCH:{table}")
        missing = set(current_rows) - set(candidate_rows)
        if missing:
            raise LedgerEvidenceRecoveryError(f"RECOVERY_CURRENT_ROWS_MISSING:{table}:{len(missing)}")
        changed = [key for key in set(current_rows) & set(candidate_rows) if current_rows[key] != candidate_rows[key]]
        if changed:
            raise LedgerEvidenceRecoveryError(f"RECOVERY_CURRENT_ROWS_CHANGED:{table}:{len(changed)}")
        new_keys = set(candidate_rows) - set(current_rows)
        if not new_keys:
            continue
        rows = [candidate_rows[key] for key in sorted(new_keys, key=repr)]
        if table in EVIDENCE_TABLES:
            additions[table] = rows
        elif table in AUTHORITY_TABLES or table in EFFECT_TABLES:
            withheld[table] = len(rows)
        else:
            unexpected[table] = len(rows)
    if unexpected:
        raise LedgerEvidenceRecoveryError(
            "RECOVERY_UNEXPECTED_TABLE_ADDITIONS:" + json.dumps(unexpected, sort_keys=True)
        )
    return additions, withheld, unexpected


def _json_object(value: Any) -> dict[str, Any]:
    try:
        parsed = json.loads(str(value or "{}"))
    except (TypeError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _event_chain(connection: sqlite3.Connection) -> dict[str, Any]:
    columns = {str(row[1]) for row in connection.execute("PRAGMA table_info(events)")}
    required = {
        "seq",
        "event_id",
        "run_id",
        "wave_id",
        "delegation_id",
        "event_type",
        "state_before",
        "state_after",
        "event_time",
        "payload_json",
        "prev_hash",
        "event_hash",
    }
    if not required.issubset(columns):
        raise LedgerEvidenceRecoveryError("RECOVERY_EVENT_CHAIN_SCHEMA_MISMATCH")
    previous_by_run: dict[str, str] = {}
    last_seq = 0
    count = 0
    for row in connection.execute("SELECT * FROM events ORDER BY seq"):
        seq = int(row["seq"])
        if seq <= last_seq:
            raise LedgerEvidenceRecoveryError("RECOVERY_EVENT_SEQUENCE_INVALID")
        last_seq = seq
        run_id = str(row["run_id"] or "")
        previous = previous_by_run.get(run_id, "")
        if str(row["prev_hash"] or "") != previous:
            raise LedgerEvidenceRecoveryError(f"RECOVERY_EVENT_CHAIN_LINK_INVALID:{run_id}")
        try:
            payload = json.loads(str(row["payload_json"] or "{}"))
        except json.JSONDecodeError as exc:
            raise LedgerEvidenceRecoveryError(f"RECOVERY_EVENT_PAYLOAD_INVALID:{run_id}") from exc
        material = {
            "event_id": row["event_id"],
            "run_id": row["run_id"],
            "wave_id": row["wave_id"] or "",
            "delegation_id": row["delegation_id"] or "",
            "event_type": row["event_type"],
            "state_before": row["state_before"],
            "state_after": row["state_after"],
            "event_time": row["event_time"],
            "payload": payload,
            "prev_hash": row["prev_hash"] or "",
        }
        digest = hashlib.sha256(
            json.dumps(material, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
        ).hexdigest()
        if digest != str(row["event_hash"] or ""):
            raise LedgerEvidenceRecoveryError(f"RECOVERY_EVENT_HASH_INVALID:{run_id}")
        previous_by_run[run_id] = str(row["event_hash"] or "")
        count += 1
    return {"event_count": count, "run_count": len(previous_by_run), "valid": True}


def _problem_projection_plans(
    current: sqlite3.Connection,
    candidate: sqlite3.Connection,
    allowed_problem_ids: set[str],
) -> list[dict[str, Any]]:
    required_threads = {
        "problem_id",
        "current_revision",
        "resolution_state",
        "latest_problem_event_seq",
        "latest_problem_event_hash",
    }
    required_events = {
        "problem_id",
        "seq",
        "problem_revision",
        "relation_type",
        "link_status",
        "link_role",
        "state_before",
        "state_after",
        "event_hash",
        "prev_hash",
        "recorded_at",
    }
    if not required_threads.issubset({str(r[1]) for r in current.execute("PRAGMA table_info(problem_threads)")}):
        raise LedgerEvidenceRecoveryError("RECOVERY_PROBLEM_THREAD_SCHEMA_MISMATCH")
    if not required_events.issubset({str(r[1]) for r in current.execute("PRAGMA table_info(problem_events)")}):
        raise LedgerEvidenceRecoveryError("RECOVERY_PROBLEM_EVENT_SCHEMA_MISMATCH")
    plans: list[dict[str, Any]] = []
    for thread in current.execute(
        "SELECT problem_id,current_revision,resolution_state,latest_problem_event_seq,latest_problem_event_hash FROM problem_threads ORDER BY problem_id"
    ):
        problem_id = str(thread["problem_id"])
        pointer_seq = int(thread["latest_problem_event_seq"] or 0)
        pointer_hash = str(thread["latest_problem_event_hash"] or "")
        candidate_tail = candidate.execute(
            """SELECT seq,problem_revision,relation_type,link_status,link_role,
                      state_before,state_after,event_id,event_hash,prev_hash,recorded_at
                 FROM problem_events WHERE problem_id=? AND seq>? ORDER BY seq""",
            (problem_id, pointer_seq),
        ).fetchall()
        if not candidate_tail:
            continue
        if problem_id not in allowed_problem_ids:
            raise LedgerEvidenceRecoveryError(f"RECOVERY_PROBLEM_NOT_ALLOWLISTED:{problem_id}")
        expected_prev = pointer_hash
        tail: list[dict[str, Any]] = []
        reasons: list[str] = []
        for row in candidate_tail:
            row_reasons: list[str] = []
            if int(row["problem_revision"] or 0) != int(thread["current_revision"]):
                row_reasons.append("REVISION_MISMATCH")
            state_before = str(row["state_before"] or "")
            state_after = str(row["state_after"] or "")
            if state_before != str(thread["resolution_state"] or "") or state_after != state_before:
                row_reasons.append("STATE_TRANSITION_OR_MISMATCH")
            relation = str(row["relation_type"] or "")
            if relation not in SAFE_POINTER_RELATIONS:
                row_reasons.append("TRANSITION_RELATION")
            if str(row["link_status"] or "") != "EXACT":
                row_reasons.append("LINK_NOT_EXACT")
            if relation == "ENGINEERING_ATTEMPT_BOUND" and str(row["link_role"] or "") != "PRIMARY":
                row_reasons.append("PRIMARY_BINDING_REQUIRED")
            if str(row["prev_hash"] or "") != expected_prev:
                row_reasons.append("TAIL_HASH_LINK_MISMATCH")
            if row_reasons:
                reasons.extend(f"seq={int(row['seq'])}:{reason}" for reason in row_reasons)
            expected_prev = str(row["event_hash"] or "")
            tail.append(
                {
                    "seq": int(row["seq"]),
                    "event_id": str(row["event_id"] or ""),
                    "event_hash": str(row["event_hash"] or ""),
                    "recorded_at": str(row["recorded_at"] or ""),
                    "relation_type": relation,
                    "link_status": str(row["link_status"] or ""),
                    "link_role": str(row["link_role"] or ""),
                    "problem_revision": int(row["problem_revision"] or 0),
                    "state_before": state_before,
                    "state_after": state_after,
                }
            )
        plan = {
            "problem_id": problem_id,
            "classification": "POINTER_ONLY_SAFE" if not reasons else "BLOCKED_UNSAFE_TAIL",
            "current_pointer_seq": pointer_seq,
            "current_pointer_hash": pointer_hash,
            "proposed_pointer_seq": tail[-1]["seq"],
            "proposed_pointer_hash": tail[-1]["event_hash"],
            "updated_at": tail[-1]["recorded_at"],
            "tail_event_count": len(tail),
            "tail_events": tail,
            "reasons": reasons,
        }
        if reasons:
            raise LedgerEvidenceRecoveryError(
                "RECOVERY_PROBLEM_POINTER_UNSAFE:" + json.dumps(plan, sort_keys=True)
            )
        plans.append(plan)
    return plans


def _new_run_ids(current: sqlite3.Connection, candidate: sqlite3.Connection) -> set[str]:
    _, old = _keyed_rows(current, "runs")
    _, new = _keyed_rows(candidate, "runs")
    return {str(key[0]) for key in set(new) - set(old)}


def _current_run_ids(current: sqlite3.Connection) -> set[str]:
    _, rows = _keyed_rows(current, "runs")
    return {str(key[0]) for key in rows}


def _evidence_identity(
    table: str,
    columns: list[str],
    primary_columns: list[str],
    values: tuple[Any, ...],
) -> str:
    """Return the exact operator-facing identity for one immutable row.

    Prefer the table's stable semantic identity (for example
    ``continuity_telemetry.logical_id`` or ``events.event_id``) over a storage
    sequence.  Composite keys are represented with a table-qualified
    deterministic token so an operator can never accidentally authorize an
    identity shared by two tables.
    """

    record = dict(zip(columns, values))
    for preferred in ("logical_id", "event_id", "ack_id", "checkpoint_id", "proof_id", "wave_id"):
        if preferred in record and record.get(preferred) not in (None, ""):
            return str(record[preferred])
    primary_values = [str(record.get(name) or "") for name in primary_columns]
    if len(primary_values) == 1:
        return primary_values[0]
    return f"{table}:" + "|".join(primary_values)


def _validate_allowlists(
    current: sqlite3.Connection,
    candidate: sqlite3.Connection,
    additions: dict[str, list[tuple[Any, ...]]],
    *,
    allowed_run_ids: set[str],
    allowed_existing_run_ids: set[str],
    allowed_problem_ids: set[str],
    allowed_evidence_ids: set[str],
    allowed_existing_evidence_ids: set[str],
) -> None:
    if not allowed_run_ids:
        raise LedgerEvidenceRecoveryError("RECOVERY_RUN_ALLOWLIST_REQUIRED")
    actual_runs = _new_run_ids(current, candidate)
    if actual_runs != allowed_run_ids:
        raise LedgerEvidenceRecoveryError(
            "RECOVERY_RUN_ALLOWLIST_MISMATCH:" + json.dumps({"expected": sorted(allowed_run_ids), "actual": sorted(actual_runs)})
        )
    current_run_ids = _current_run_ids(current)
    table_metadata = {
        table: _table_columns(current, table)
        for table in EVIDENCE_TABLES
    }
    actual_existing_run_ids: set[str] = set()
    actual_existing_evidence_ids: set[str] = set()
    for table, rows in additions.items():
        columns, primary_columns = table_metadata[table]
        for values in rows:
            record = dict(zip(columns, values))
            record_run = str(record.get("run_id") or "")
            if record_run:
                if record_run in allowed_run_ids:
                    pass
                elif record_run in current_run_ids:
                    actual_existing_run_ids.add(record_run)
                    if record_run not in allowed_existing_run_ids:
                        raise LedgerEvidenceRecoveryError(
                            f"RECOVERY_EXISTING_RUN_NOT_ALLOWLISTED:{table}:{record_run}"
                        )
                    identity = _evidence_identity(table, columns, primary_columns, values)
                    actual_existing_evidence_ids.add(identity)
                    if identity not in allowed_existing_evidence_ids:
                        raise LedgerEvidenceRecoveryError(
                            f"RECOVERY_EXISTING_EVIDENCE_ID_NOT_ALLOWLISTED:{table}:{identity}"
                        )
                else:
                    raise LedgerEvidenceRecoveryError(f"RECOVERY_EVIDENCE_RUN_NOT_ALLOWLISTED:{table}:{record_run}")
            problem_id = str(record.get("problem_id") or "")
            if problem_id and problem_id not in allowed_problem_ids:
                raise LedgerEvidenceRecoveryError(f"RECOVERY_EVIDENCE_PROBLEM_NOT_ALLOWLISTED:{table}:{problem_id}")
            if table == "controller_knowledge_acks":
                identity = _evidence_identity(table, columns, primary_columns, values)
                if identity not in allowed_evidence_ids:
                    raise LedgerEvidenceRecoveryError(f"RECOVERY_EVIDENCE_ID_NOT_ALLOWLISTED:{table}:{identity}")
    if actual_existing_run_ids != allowed_existing_run_ids:
        raise LedgerEvidenceRecoveryError(
            "RECOVERY_EXISTING_RUN_ALLOWLIST_MISMATCH:"
            + json.dumps(
                {
                    "expected": sorted(allowed_existing_run_ids),
                    "actual": sorted(actual_existing_run_ids),
                },
                sort_keys=True,
            )
        )
    if actual_existing_evidence_ids != allowed_existing_evidence_ids:
        raise LedgerEvidenceRecoveryError(
            "RECOVERY_EXISTING_EVIDENCE_ALLOWLIST_MISMATCH:"
            + json.dumps(
                {
                    "expected": sorted(allowed_existing_evidence_ids),
                    "actual": sorted(actual_existing_evidence_ids),
                },
                sort_keys=True,
            )
        )


def _effect_status_counts(connection: sqlite3.Connection, table: str) -> dict[str, int]:
    columns = {str(row[1]) for row in connection.execute(f"PRAGMA table_info({_quote(table)})")}
    status = next((value for value in ("status", "state", "lifecycle_state") if value in columns), None)
    if status is None:
        return {"<unknown>": int(connection.execute(f"SELECT COUNT(*) FROM {_quote(table)}").fetchone()[0])}
    return {
        str(row[0] or ""): int(row[1])
        for row in connection.execute(
            f"SELECT {_quote(status)},COUNT(*) FROM {_quote(table)} GROUP BY {_quote(status)} ORDER BY {_quote(status)}"
        )
    }


def _clone_evidence_apply(
    current_path: Path,
    candidate_path: Path,
    plans: list[dict[str, Any]],
    additions: dict[str, list[tuple[Any, ...]]],
) -> tuple[Path, RecoverySnapshot]:
    directory = Path(tempfile.mkdtemp(prefix="ledger-evidence-recovery-probe-"))
    clone = directory / "clone.sqlite3"
    source = _open_readonly(current_path, immutable=False)
    try:
        destination = sqlite3.connect(clone)
        try:
            source.backup(destination, pages=256, sleep=0.01)
            destination.commit()
        finally:
            destination.close()
    finally:
        source.close()
    connection = _open_writer(clone)
    try:
        connection.execute("BEGIN IMMEDIATE")
        for table in _INSERT_ORDER:
            rows = additions.get(table, [])
            if not rows:
                continue
            columns, _ = _table_columns(connection, table)
            placeholders = ",".join("?" for _ in columns)
            connection.executemany(
                f"INSERT INTO {_quote(table)} ({','.join(_quote(c) for c in columns)}) VALUES ({placeholders})",
                rows,
            )
        for plan in plans:
            updated = connection.execute(
                """UPDATE problem_threads
                   SET latest_problem_event_seq=?, latest_problem_event_hash=?, updated_at=?
                 WHERE problem_id=? AND current_revision=? AND resolution_state=?
                   AND latest_problem_event_seq=? AND latest_problem_event_hash=?""",
                (
                    int(plan["proposed_pointer_seq"]),
                    str(plan["proposed_pointer_hash"]),
                    str(plan["updated_at"]),
                    str(plan["problem_id"]),
                    int(plan["tail_events"][0]["problem_revision"]),
                    str(plan["tail_events"][0]["state_before"]),
                    int(plan["current_pointer_seq"]),
                    str(plan["current_pointer_hash"]),
                ),
            ).rowcount
            if updated != 1:
                raise LedgerEvidenceRecoveryError("RECOVERY_PROJECTION_CAS_PROBE_FAILED")
        if list(connection.execute("PRAGMA foreign_key_check")):
            raise LedgerEvidenceRecoveryError("RECOVERY_PROJECTION_PROBE_FOREIGN_KEY_FAILED")
        if str(connection.execute("PRAGMA integrity_check").fetchone()[0]) != "ok":
            raise LedgerEvidenceRecoveryError("RECOVERY_PROJECTION_PROBE_INTEGRITY_FAILED")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    snapshot = _snapshot(clone, immutable=True)
    _assert_snapshot(snapshot, label="RECOVERY_PROJECTION_PROBE")
    clone.chmod(0o400)
    return directory, snapshot


def _load_quiesce_receipt(path: Path, workspace: Path, snapshot: RecoverySnapshot) -> dict[str, Any]:
    try:
        receipt = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LedgerEvidenceRecoveryError("RECOVERY_QUIESCE_RECEIPT_INVALID") from exc
    if not isinstance(receipt, dict):
        raise LedgerEvidenceRecoveryError("RECOVERY_QUIESCE_RECEIPT_INVALID")
    expected_workspace = str(workspace.resolve(strict=False))
    expected_ledger = str((workspace / ".coding-tools" / "orchestration" / "ledger.sqlite3").resolve(strict=False))
    if receipt.get("schema_version") != 1 or receipt.get("kind") != "LEDGER_RECOVERY_QUIESCE":
        raise LedgerEvidenceRecoveryError("RECOVERY_QUIESCE_RECEIPT_SCHEMA_MISMATCH")
    if receipt.get("runtime_stopped") is not True:
        raise LedgerEvidenceRecoveryError("RECOVERY_QUIESCE_RECEIPT_RUNTIME_NOT_STOPPED")
    if str(Path(str(receipt.get("workspace") or "")).resolve(strict=False)) != expected_workspace:
        raise LedgerEvidenceRecoveryError("RECOVERY_QUIESCE_RECEIPT_WORKSPACE_MISMATCH")
    if str(Path(str(receipt.get("ledger_path") or "")).resolve(strict=False)) != expected_ledger:
        raise LedgerEvidenceRecoveryError("RECOVERY_QUIESCE_RECEIPT_LEDGER_MISMATCH")
    source = receipt.get("source_snapshot") if isinstance(receipt.get("source_snapshot"), dict) else {}
    if str(source.get("sha256") or "").lower() != snapshot.physical_sha256.lower():
        raise LedgerEvidenceRecoveryError("RECOVERY_QUIESCE_RECEIPT_PHYSICAL_SHA_MISMATCH")
    if str(source.get("logical_sha256") or "").lower() != snapshot.logical_sha256.lower():
        raise LedgerEvidenceRecoveryError("RECOVERY_QUIESCE_RECEIPT_LOGICAL_SHA_MISMATCH")
    if source.get("integrity_check") != "ok" or int(source.get("foreign_key_check_rows") or 0) != 0:
        raise LedgerEvidenceRecoveryError("RECOVERY_QUIESCE_RECEIPT_SOURCE_NOT_CLEAN")
    ownership = receipt.get("ownership") if isinstance(receipt.get("ownership"), dict) else {}
    if any(int(ownership.get(key) or 0) != 0 for key in ("active_controller_leases", "active_write_fences", "active_managed_jobs", "active_background_operations")):
        raise LedgerEvidenceRecoveryError("RECOVERY_QUIESCE_RECEIPT_LIVE_OWNERSHIP")
    if not str(receipt.get("operator_authority") or "").strip():
        raise LedgerEvidenceRecoveryError("RECOVERY_QUIESCE_RECEIPT_AUTHORITY_REQUIRED")
    return receipt


def _safe_receipt_identity(value: Any) -> str:
    text = str(value or "").strip()
    if not text or len(text) > 128:
        raise LedgerEvidenceRecoveryError("RECOVERY_RECEIPT_IDENTITY_INVALID")
    return text


def preflight_evidence_recovery(
    workspace: Path,
    *,
    candidate: Path,
    expected_current_sha256: str = "",
    expected_current_logical_sha256: str = "",
    expected_candidate_sha256: str = "",
    expected_candidate_logical_sha256: str = "",
    allowed_run_ids: set[str],
    allowed_problem_ids: set[str],
    allowed_evidence_ids: set[str] | None = None,
    allowed_existing_run_ids: set[str] | None = None,
    allowed_existing_evidence_ids: set[str] | None = None,
) -> dict[str, Any]:
    root = Path(workspace).resolve(strict=False)
    ledger = root / ".coding-tools" / "orchestration" / "ledger.sqlite3"
    candidate_path = Path(candidate).resolve(strict=True)
    if candidate_path == ledger.resolve(strict=False):
        raise LedgerEvidenceRecoveryError("RECOVERY_CANDIDATE_MUST_BE_EXTERNAL")
    current_snapshot = _snapshot(ledger, immutable=False)
    candidate_snapshot = _snapshot(candidate_path, immutable=True)
    _validate_expected_snapshot(
        current_snapshot,
        {"sha256": expected_current_sha256, "logical_sha256": expected_current_logical_sha256},
        label="RECOVERY_CURRENT",
    )
    _validate_expected_snapshot(
        candidate_snapshot,
        {"sha256": expected_candidate_sha256, "logical_sha256": expected_candidate_logical_sha256},
        label="RECOVERY_CANDIDATE",
    )
    current = _open_readonly(ledger, immutable=False)
    source_candidate = _open_readonly(candidate_path, immutable=True)
    try:
        additions, withheld, _ = _table_diffs(current, source_candidate)
        _validate_allowlists(
            current,
            source_candidate,
            additions,
            allowed_run_ids=set(allowed_run_ids),
            allowed_existing_run_ids=set(allowed_existing_run_ids or set()),
            allowed_problem_ids=set(allowed_problem_ids),
            allowed_evidence_ids=set(allowed_evidence_ids or set()),
            allowed_existing_evidence_ids=set(allowed_existing_evidence_ids or set()),
        )
        _event_chain(source_candidate)
        plans = _problem_projection_plans(current, source_candidate, set(allowed_problem_ids))
        probe_directory, probe_snapshot = _clone_evidence_apply(ledger, candidate_path, plans, additions)
        maintenance = inspect_maintenance_readiness(root)
        effect_withheld = {
            table: {
                "row_count": int(count),
                "status_counts": _effect_status_counts(source_candidate, table),
            }
            for table, count in sorted(withheld.items())
            if table in EFFECT_TABLES
        }
        authority_withheld = {table: int(count) for table, count in sorted(withheld.items()) if table in AUTHORITY_TABLES}
        return {
            "schema_version": 1,
            "kind": "LEDGER_EVIDENCE_RECOVERY_PREFLIGHT",
            "workspace": str(root),
            "ledger_path": str(ledger),
            "candidate_path": str(candidate_path),
            "current_snapshot": current_snapshot.projection(),
            "candidate_snapshot": candidate_snapshot.projection(),
            "expected_allowlists": {
                "run_ids": sorted(allowed_run_ids),
                "existing_run_ids": sorted(allowed_existing_run_ids or set()),
                "problem_ids": sorted(allowed_problem_ids),
                "evidence_ids": sorted(allowed_evidence_ids or set()),
                "existing_evidence_ids": sorted(allowed_existing_evidence_ids or set()),
            },
            "immutable_additions": {table: len(rows) for table, rows in sorted(additions.items())},
            "withheld_authority": authority_withheld,
            "withheld_effects": effect_withheld,
            "pointer_plans": plans,
            "probe": {
                "directory": str(probe_directory),
                "snapshot": probe_snapshot.projection(),
                "canonical_mutated": False,
            },
            "maintenance": {
                key: maintenance.get(key)
                for key in (
                    "active_controller_leases",
                    "active_write_fences",
                    "active_managed_jobs",
                    "active_background_operations",
                    "integrity_check",
                    "foreign_key_violations",
                    "logical_sha256",
                )
            },
            "recovery_policy": {
                "evidence_only": True,
                "authority_imported": False,
                "effect_rows_imported": False,
                "replay_allowed": 0,
                "activation_eligible": False,
                "runtime_stopped_required_for_apply": True,
                "exclusive_gate_required_for_apply": True,
                "rollback_backup_required_for_apply": True,
                "withheld_rows_require_separate_owner_review": bool(withheld),
            },
            # Withheld authority/effect rows are deliberately *not* a reason
            # to block an evidence-only append. They are never imported or
            # replayed; they remain an explicit owner-review obligation.
            "apply_eligible": bool(plans and maintenance.get("compact_allowed")),
        }
    finally:
        source_candidate.close()
        current.close()


def _backup_live(ledger: Path, destination: Path) -> RecoverySnapshot:
    if destination.exists():
        raise LedgerEvidenceRecoveryError("RECOVERY_ROLLBACK_BACKUP_MUST_BE_NEW")
    destination.parent.mkdir(parents=True, exist_ok=True)
    source = _open_readonly(ledger, immutable=False)
    try:
        output = sqlite3.connect(destination)
        try:
            source.backup(output, pages=256, sleep=0.01)
            output.commit()
        finally:
            output.close()
    finally:
        source.close()
    snapshot = _snapshot(destination, immutable=True)
    _assert_snapshot(snapshot, label="RECOVERY_ROLLBACK_BACKUP")
    destination.chmod(0o400)
    return snapshot


def _insert_additions(connection: sqlite3.Connection, additions: dict[str, list[tuple[Any, ...]]]) -> dict[str, int]:
    inserted: dict[str, int] = {}
    for table in _INSERT_ORDER:
        rows = additions.get(table, [])
        if not rows:
            continue
        columns, _ = _table_columns(connection, table)
        placeholders = ",".join("?" for _ in columns)
        connection.executemany(
            f"INSERT INTO {_quote(table)} ({','.join(_quote(c) for c in columns)}) VALUES ({placeholders})",
            rows,
        )
        inserted[table] = len(rows)
    return inserted


def _apply_pointer_cas(connection: sqlite3.Connection, plans: list[dict[str, Any]]) -> None:
    for plan in plans:
        revision = int(plan["tail_events"][0]["problem_revision"])
        state = str(plan["tail_events"][0]["state_before"])
        updated = connection.execute(
            """UPDATE problem_threads
               SET latest_problem_event_seq=?, latest_problem_event_hash=?, updated_at=?
             WHERE problem_id=? AND current_revision=? AND resolution_state=?
               AND latest_problem_event_seq=? AND latest_problem_event_hash=?""",
            (
                int(plan["proposed_pointer_seq"]),
                str(plan["proposed_pointer_hash"]),
                str(plan["updated_at"]),
                str(plan["problem_id"]),
                revision,
                state,
                int(plan["current_pointer_seq"]),
                str(plan["current_pointer_hash"]),
            ),
        ).rowcount
        if updated != 1:
            raise LedgerEvidenceRecoveryError(f"RECOVERY_PROJECTION_CAS_FAILED:{plan['problem_id']}")


def apply_evidence_recovery(
    workspace: Path,
    *,
    candidate: Path,
    preflight: dict[str, Any],
    quiesce_receipt: Path,
    rollback_backup: Path,
    runtime_stopped: bool,
    authority: str,
) -> dict[str, Any]:
    if runtime_stopped is not True:
        raise LedgerEvidenceRecoveryError("RECOVERY_APPLY_REQUIRES_RUNTIME_STOPPED")
    if not str(authority or "").strip():
        raise LedgerEvidenceRecoveryError("RECOVERY_APPLY_AUTHORITY_REQUIRED")
    root = Path(workspace).resolve(strict=False)
    ledger = root / ".coding-tools" / "orchestration" / "ledger.sqlite3"
    candidate_path = Path(candidate).resolve(strict=True)
    if str(preflight.get("kind") or "") != "LEDGER_EVIDENCE_RECOVERY_PREFLIGHT":
        raise LedgerEvidenceRecoveryError("RECOVERY_PREFLIGHT_RECEIPT_INVALID")
    if str(Path(str(preflight.get("workspace") or "")).resolve(strict=False)) != str(root):
        raise LedgerEvidenceRecoveryError("RECOVERY_PREFLIGHT_WORKSPACE_MISMATCH")
    if str(Path(str(preflight.get("candidate_path") or "")).resolve(strict=False)) != str(candidate_path):
        raise LedgerEvidenceRecoveryError("RECOVERY_PREFLIGHT_CANDIDATE_MISMATCH")
    if preflight.get("apply_eligible") is not True:
        raise LedgerEvidenceRecoveryError("RECOVERY_PREFLIGHT_NOT_APPLY_ELIGIBLE")
    expected_current = preflight.get("current_snapshot") if isinstance(preflight.get("current_snapshot"), dict) else {}
    expected_candidate = preflight.get("candidate_snapshot") if isinstance(preflight.get("candidate_snapshot"), dict) else {}
    expected_probe = preflight.get("probe", {}).get("snapshot", {}) if isinstance(preflight.get("probe"), dict) else {}
    receipt_authority = _safe_receipt_identity(authority)
    expected_allowlists = preflight.get("expected_allowlists") if isinstance(preflight.get("expected_allowlists"), dict) else {}
    with ledger_access_gate(ledger, exclusive=True, timeout_seconds=5.0):
        before = _snapshot(ledger, immutable=False)
        if before.physical_sha256.lower() != str(expected_current.get("sha256") or "").lower() or before.logical_sha256.lower() != str(expected_current.get("logical_sha256") or "").lower():
            raise LedgerEvidenceRecoveryError("RECOVERY_PREFLIGHT_SOURCE_DRIFT")
        if _sha256_file(candidate_path).lower() != str(expected_candidate.get("sha256") or "").lower():
            raise LedgerEvidenceRecoveryError("RECOVERY_CANDIDATE_DRIFT")
        _load_quiesce_receipt(Path(quiesce_receipt).resolve(strict=True), root, before)
        rollback_snapshot = _backup_live(ledger, Path(rollback_backup).resolve())
        current = _open_readonly(ledger, immutable=False)
        source_candidate = _open_readonly(candidate_path, immutable=True)
        probe_directory: Path | None = None
        try:
            additions, withheld, _ = _table_diffs(current, source_candidate)
            _validate_allowlists(
                current,
                source_candidate,
                additions,
                allowed_run_ids=set(expected_allowlists.get("run_ids") or []),
                allowed_existing_run_ids=set(expected_allowlists.get("existing_run_ids") or []),
                allowed_problem_ids=set(expected_allowlists.get("problem_ids") or []),
                allowed_evidence_ids=set(expected_allowlists.get("evidence_ids") or []),
                allowed_existing_evidence_ids=set(expected_allowlists.get("existing_evidence_ids") or []),
            )
            plans = _problem_projection_plans(current, source_candidate, set(expected_allowlists.get("problem_ids") or []))
            withheld_effects = {
                table: {"row_count": int(count), "status_counts": _effect_status_counts(source_candidate, table)}
                for table, count in sorted(withheld.items())
                if table in EFFECT_TABLES
            }
            probe_directory, probe_snapshot = _clone_evidence_apply(ledger, candidate_path, plans, additions)
            if probe_snapshot.logical_sha256.lower() != str(expected_probe.get("logical_sha256") or "").lower():
                raise LedgerEvidenceRecoveryError("RECOVERY_PREFLIGHT_PROBE_DRIFT")
        finally:
            source_candidate.close()
            current.close()
        connection = _open_writer(ledger)
        committed = False
        try:
            connection.execute("BEGIN IMMEDIATE")
            locked = _snapshot(ledger, immutable=False)
            if locked.logical_sha256.lower() != before.logical_sha256.lower() or locked.physical_sha256.lower() != before.physical_sha256.lower():
                raise LedgerEvidenceRecoveryError("RECOVERY_SOURCE_DRIFT_UNDER_GATE")
            inserted = _insert_additions(connection, additions)
            _apply_pointer_cas(connection, plans)
            if list(connection.execute("PRAGMA foreign_key_check")):
                raise LedgerEvidenceRecoveryError("RECOVERY_POST_APPLY_FOREIGN_KEY_FAILED")
            if str(connection.execute("PRAGMA integrity_check").fetchone()[0]) != "ok":
                raise LedgerEvidenceRecoveryError("RECOVERY_POST_APPLY_INTEGRITY_FAILED")
            _event_chain(connection)
            connection.commit()
            committed = True
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
            if probe_directory is not None:
                shutil.rmtree(probe_directory, ignore_errors=True)
        after = _snapshot(ledger, immutable=False)
        if after.logical_sha256.lower() != str(expected_probe.get("logical_sha256") or "").lower():
            raise LedgerEvidenceRecoveryError(
                "RECOVERY_POSTFLIGHT_LOGICAL_MISMATCH_ROLLBACK_BACKUP_AVAILABLE"
            )
        if after.integrity.lower() != "ok" or after.foreign_key_rows:
            raise LedgerEvidenceRecoveryError(
                "RECOVERY_POSTFLIGHT_INTEGRITY_FAILED_ROLLBACK_BACKUP_AVAILABLE"
            )
    return {
        "schema_version": 1,
        "kind": "LEDGER_EVIDENCE_RECOVERY_APPLIED",
        "workspace": str(root),
        "ledger_path": str(ledger),
        "candidate_path": str(candidate_path),
        "authority": receipt_authority,
        "runtime_stopped": True,
        "committed": committed,
        "before": before.projection(),
        "after": after.projection(),
        "rollback_backup": {
            "path": str(Path(rollback_backup).resolve()),
            "snapshot": rollback_snapshot.projection(),
        },
        "inserted_evidence": inserted,
        "withheld_authority": {table: int(count) for table, count in sorted(withheld.items()) if table in AUTHORITY_TABLES},
        "withheld_effects": withheld_effects,
        "replay_allowed": 0,
        "problem_pointer_updates": [
            {
                "problem_id": plan["problem_id"],
                "from_seq": plan["current_pointer_seq"],
                "to_seq": plan["proposed_pointer_seq"],
            }
            for plan in plans
        ],
    }


def capture_quiesce_receipt(
    workspace: Path,
    *,
    output: Path,
    runtime_stopped: bool,
    operator_authority: str,
) -> dict[str, Any]:
    """Capture a content-free stopped-runtime receipt; never stops anything."""
    if runtime_stopped is not True:
        raise LedgerEvidenceRecoveryError("RECOVERY_QUIESCE_CAPTURE_REQUIRES_RUNTIME_STOPPED")
    if not str(operator_authority or "").strip():
        raise LedgerEvidenceRecoveryError("RECOVERY_QUIESCE_CAPTURE_AUTHORITY_REQUIRED")
    root = Path(workspace).resolve(strict=False)
    ledger = root / ".coding-tools" / "orchestration" / "ledger.sqlite3"
    snapshot = _snapshot(ledger, immutable=False)
    maintenance = inspect_maintenance_readiness(root)
    if not maintenance.get("compact_allowed"):
        raise LedgerEvidenceRecoveryError(
            "RECOVERY_QUIESCE_CAPTURE_LIVE_OWNERSHIP:" + ",".join(str(item) for item in maintenance.get("blockers") or [])
        )
    receipt = {
        "schema_version": 1,
        "kind": "LEDGER_RECOVERY_QUIESCE",
        "captured_at": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        "workspace": str(root),
        "ledger_path": str(ledger),
        "runtime_stopped": True,
        "operator_authority": str(operator_authority).strip(),
        "source_snapshot": snapshot.projection(),
        "ownership": {
            "active_controller_leases": int(maintenance.get("active_controller_leases") or 0),
            "active_write_fences": int(maintenance.get("active_write_fences") or 0),
            "active_managed_jobs": int(maintenance.get("active_managed_jobs") or 0),
            "active_background_operations": int(maintenance.get("active_background_operations") or 0),
        },
        "policy": "evidence_only_no_authority_or_effect_replay",
    }
    output = Path(output).resolve()
    if output.exists():
        raise LedgerEvidenceRecoveryError("RECOVERY_QUIESCE_RECEIPT_MUST_BE_NEW")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    output.chmod(0o400)
    return receipt
