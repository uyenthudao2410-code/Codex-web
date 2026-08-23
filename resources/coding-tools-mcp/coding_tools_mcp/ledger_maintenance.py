"""Fail-closed maintenance for the canonical orchestration ledger.

This is deliberately separate from normal writer/readers. It never truncates
or VACUUMs the live file: compaction is an Online Backup API copy validated
before a guarded atomic replacement.
"""

from __future__ import annotations

import errno
import hashlib
import json
import os
import sqlite3
import tempfile
import time
from pathlib import Path
from typing import Any

from .idempotency_codec import decode_summary, secret_key_findings
from .ledger_analysis import LedgerReadSession
from .ledger_file_gate import ledger_access_gate, ledger_exclusive_gate_held
from .orchestration_ledger import OrchestrationLedger


TABLES = ("runs", "waves", "delegations", "events", "proofs", "checkpoints", "idempotency_records")
ACTIVE_JOB_STATES = ("starting", "running", "terminating", "orphaned")
ACTIVE_BACKGROUND_STATES = ("running",)


def _ledger_path(workspace: Path) -> Path:
    path = Path(workspace).resolve(strict=False) / ".coding-tools" / "orchestration" / "ledger.sqlite3"
    if not path.is_file():
        raise FileNotFoundError(f"orchestration ledger does not exist: {path}")
    return path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _table_counts(connection: sqlite3.Connection) -> dict[str, int]:
    return {table: int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]) for table in TABLES}


def _logical_sha256(connection: sqlite3.Connection) -> str:
    """Hash the complete logical SQLite dump, including committed WAL-visible state."""
    digest = hashlib.sha256()
    for statement in connection.iterdump():
        digest.update(statement.encode("utf-8", errors="surrogatepass"))
        digest.update(b"\n")
    return digest.hexdigest()


def _sidecar_state(ledger: Path) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for name, suffix in (("wal", "-wal"), ("shm", "-shm")):
        path = Path(f"{ledger}{suffix}")
        exists = path.exists()
        size = path.stat().st_size if exists else 0
        result[name] = {
            "path": str(path),
            "exists": exists,
            "size_bytes": int(size),
            "sha256": _sha256(path) if exists and size else "",
        }
    return result


def _secret_findings(connection: sqlite3.Connection) -> dict[str, int]:
    findings: dict[str, int] = {}
    for row in connection.execute("SELECT * FROM idempotency_records"):
        for key in secret_key_findings(decode_summary(row)):
            findings[f"idempotency_records.{key}"] = findings.get(f"idempotency_records.{key}", 0) + 1
    for row in connection.execute("SELECT payload_json FROM events"):
        try:
            payload = json.loads(row[0] or "{}")
        except (TypeError, json.JSONDecodeError):
            continue
        for key in secret_key_findings(payload if isinstance(payload, dict) else {}):
            findings[f"events.{key}"] = findings.get(f"events.{key}", 0) + 1
    return dict(sorted(findings.items()))


def _maintenance_facts(connection: sqlite3.Connection, ledger: Path) -> dict[str, Any]:
    now = time.time()
    integrity = str(connection.execute("PRAGMA integrity_check").fetchone()[0])
    foreign_keys = [tuple(row) for row in connection.execute("PRAGMA foreign_key_check")]
    active_leases = int(
        connection.execute(
            "SELECT COUNT(*) FROM controller_leases WHERE status='active' AND expires_at>?",
            (now,),
        ).fetchone()[0]
    )
    active_fences = int(
        connection.execute(
            "SELECT COUNT(*) FROM write_fences WHERE status='active' AND expires_at>?",
            (now,),
        ).fetchone()[0]
    )
    job_placeholders = ",".join("?" for _ in ACTIVE_JOB_STATES)
    active_jobs = int(
        connection.execute(
            f"SELECT COUNT(*) FROM managed_process_jobs WHERE lifecycle_state IN ({job_placeholders})",
            ACTIVE_JOB_STATES,
        ).fetchone()[0]
    )
    background_placeholders = ",".join("?" for _ in ACTIVE_BACKGROUND_STATES)
    active_background = int(
        connection.execute(
            f"SELECT COUNT(*) FROM background_operations WHERE status IN ({background_placeholders})",
            ACTIVE_BACKGROUND_STATES,
        ).fetchone()[0]
    )
    counts = _table_counts(connection)
    head = connection.execute("SELECT seq,event_hash FROM events ORDER BY seq DESC LIMIT 1").fetchone()
    findings = _secret_findings(connection)
    logical_sha256 = _logical_sha256(connection)
    result = {
        "schema_version": 2,
        "ledger_path": str(ledger),
        "ledger_sha256": _sha256(ledger),
        "logical_sha256": logical_sha256,
        "size_bytes": ledger.stat().st_size,
        "sidecars": _sidecar_state(ledger),
        "integrity_check": integrity,
        "foreign_key_violations": len(foreign_keys),
        "counts": counts,
        "max_event_seq": int(head[0]) if head else 0,
        "head_event_hash": str(head[1]) if head else "",
        "active_controller_leases": active_leases,
        "active_write_fences": active_fences,
        "active_managed_jobs": active_jobs,
        "active_background_operations": active_background,
        "secret_key_findings": findings,
    }
    blockers: list[str] = []
    if integrity.lower() != "ok":
        blockers.append("integrity_check_failed")
    if foreign_keys:
        blockers.append("foreign_key_check_failed")
    if active_leases:
        blockers.append("active_controller_leases")
    if active_fences:
        blockers.append("active_write_fences")
    if active_jobs:
        blockers.append("active_managed_jobs")
    if active_background:
        blockers.append("active_background_operations")
    if findings:
        blockers.append("secret_key_findings")
    return {**result, "compact_allowed": not blockers, "blockers": blockers}


def _read_maintenance_facts(ledger: Path) -> dict[str, Any]:
    with LedgerReadSession(ledger) as session:
        if session.connection is None:
            raise RuntimeError("read-only maintenance session did not open")
        return _maintenance_facts(session.connection, ledger)


def _require_same_logical_source(expected: dict[str, Any], current: dict[str, Any], *, phase: str) -> None:
    keys = ("logical_sha256", "counts", "max_event_seq", "head_event_hash", "secret_key_findings")
    drift = [key for key in keys if current.get(key) != expected.get(key)]
    if drift:
        raise RuntimeError(f"ledger logical source changed during {phase}: {','.join(drift)}")


def _fsync_file(path: Path) -> None:
    fd = os.open(str(path), os.O_RDWR)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _fsync_parent_directory(path: Path) -> dict[str, Any]:
    """Flush rename metadata where the platform exposes directory fsync."""
    if os.name == "nt":
        return {
            "attempted": False,
            "supported": False,
            "synced": False,
            "reason": "directory_fsync_not_exposed_by_os_fsync_on_windows",
        }
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    fd = os.open(str(path.parent), flags)
    try:
        try:
            os.fsync(fd)
        except OSError as exc:
            if exc.errno in {errno.EBADF, errno.EINVAL, getattr(errno, "ENOTSUP", -1)}:
                return {
                    "attempted": True,
                    "supported": False,
                    "synced": False,
                    "reason": f"directory_fsync_unsupported_errno_{exc.errno}",
                }
            raise
    finally:
        os.close(fd)
    return {"attempted": True, "supported": True, "synced": True, "reason": ""}


def _checkpoint_source_wal(ledger: Path) -> dict[str, Any]:
    if not ledger_exclusive_gate_held(ledger):
        raise RuntimeError("WAL checkpoint requires exclusive ledger maintenance authority")
    connection = sqlite3.connect(ledger, timeout=5.0)
    try:
        connection.execute("PRAGMA busy_timeout=5000")
        row = connection.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
        connection.commit()
    finally:
        connection.close()
    busy, log_frames, checkpointed_frames = (int(value) for value in (row or (1, 0, 0)))
    wal = Path(f"{ledger}-wal")
    wal_bytes = wal.stat().st_size if wal.exists() else 0
    if busy or wal_bytes:
        raise RuntimeError(
            f"ledger WAL could not be safely checkpointed: busy={busy}, wal_bytes={wal_bytes}"
        )
    return {
        "busy": busy,
        "log_frames": log_frames,
        "checkpointed_frames": checkpointed_frames,
        "wal_bytes_after": int(wal_bytes),
    }


def _remove_safe_sidecars(ledger: Path) -> list[str]:
    """Remove only proven-empty WAL state while exclusive authority is held."""
    if not ledger_exclusive_gate_held(ledger):
        raise RuntimeError("sidecar cleanup requires exclusive ledger maintenance authority")
    state = _sidecar_state(ledger)
    if state["wal"]["size_bytes"]:
        raise RuntimeError("refusing ledger replacement while a non-empty WAL sidecar exists")
    removed: list[str] = []
    for suffix in ("-wal", "-shm"):
        sidecar = Path(f"{ledger}{suffix}")
        if sidecar.exists():
            sidecar.unlink()
            removed.append(str(sidecar))
    residual = _sidecar_state(ledger)
    if residual["wal"]["exists"] or residual["shm"]["exists"]:
        raise RuntimeError("ledger sidecars reappeared before atomic replacement")
    return removed


def inspect_maintenance_readiness(workspace: Path) -> dict[str, Any]:
    """Read-only preflight; a non-empty blocker list means compaction is illegal."""
    ledger = _ledger_path(workspace)
    result = _read_maintenance_facts(ledger)
    return {
        **result,
        "policy": "requires_explicit_runtime_stop_exact_source_digest_exclusive_gate_and_logical_identity",
    }


def compact_ledger(workspace: Path, *, expected_sha256: str, runtime_stopped: bool) -> dict[str, Any]:
    """Compact only after the caller has stopped the ledger owner explicitly."""
    if not runtime_stopped:
        raise PermissionError("ledger compaction requires explicit runtime_stopped confirmation")
    before = inspect_maintenance_readiness(workspace)
    if not before["compact_allowed"]:
        raise RuntimeError(f"ledger maintenance preflight failed: {','.join(before['blockers'])}")
    if str(expected_sha256).lower() != str(before["ledger_sha256"]).lower():
        raise RuntimeError("ledger source digest changed or was not explicitly acknowledged")
    source = _ledger_path(workspace)
    with ledger_access_gate(source, exclusive=True, timeout_seconds=5.0):
        exclusive_source = _read_maintenance_facts(source)
        if not exclusive_source["compact_allowed"]:
            raise RuntimeError(
                f"ledger maintenance final preflight failed: {','.join(exclusive_source['blockers'])}"
            )
        _require_same_logical_source(before, exclusive_source, phase="exclusive gate acquisition")

        wal_checkpoint = _checkpoint_source_wal(source)
        checkpointed_source = _read_maintenance_facts(source)
        if not checkpointed_source["compact_allowed"]:
            raise RuntimeError(
                f"ledger maintenance post-checkpoint preflight failed: {','.join(checkpointed_source['blockers'])}"
            )
        _require_same_logical_source(exclusive_source, checkpointed_source, phase="WAL checkpoint")

        # Keep the candidate on the source filesystem so os.replace remains atomic.
        with tempfile.TemporaryDirectory(prefix=".ledger-maintenance-", dir=str(source.parent)) as directory:
            replacement = Path(directory) / "ledger.compact.sqlite3"
            with LedgerReadSession(source) as reader:
                destination = sqlite3.connect(replacement)
                try:
                    if reader.connection is None:
                        raise RuntimeError("maintenance source reader did not open")
                    reader.connection.backup(destination, pages=256, sleep=0.01)
                    destination.commit()
                finally:
                    destination.close()

            candidate_connection = sqlite3.connect(replacement)
            candidate_connection.row_factory = sqlite3.Row
            try:
                candidate = _maintenance_facts(candidate_connection, replacement)
            finally:
                candidate_connection.close()
            if not candidate["compact_allowed"]:
                raise RuntimeError(
                    f"replacement ledger failed validation: {','.join(candidate['blockers'])}"
                )
            _require_same_logical_source(checkpointed_source, candidate, phase="candidate backup validation")

            _fsync_file(replacement)

            final_source = _read_maintenance_facts(source)
            if not final_source["compact_allowed"]:
                raise RuntimeError(
                    f"ledger maintenance final blocker check failed: {','.join(final_source['blockers'])}"
                )
            _require_same_logical_source(checkpointed_source, final_source, phase="pre-replace revalidation")

            removed_sidecars = _remove_safe_sidecars(source)
            os.replace(replacement, source)
            _fsync_file(source)
            directory_sync = _fsync_parent_directory(source)

    return {
        "schema_version": 2,
        "replaced": True,
        "before": before,
        "exclusive_source": exclusive_source,
        "checkpointed_source": checkpointed_source,
        "final_source": final_source,
        "candidate_logical_sha256": candidate["logical_sha256"],
        "after_sha256": _sha256(source),
        "wal_checkpoint": wal_checkpoint,
        "removed_sidecars": removed_sidecars,
        "durability": {
            "candidate_fsync": True,
            "replacement_fsync": True,
            "parent_directory": directory_sync,
        },
        "restart_required": True,
        "append_smoke_required": True,
    }


def post_restart_append_smoke(workspace: Path, *, explicitly_authorized: bool) -> dict[str, Any]:
    """Append a bounded evidence-only run after the real owner is restarted."""
    if not explicitly_authorized:
        raise PermissionError("post-restart append smoke requires explicit authorization")
    _ledger_path(workspace)
    ledger = OrchestrationLedger(Path(workspace))
    run_id = ledger.create_run(objective="ledger maintenance append smoke", metadata={"maintenance_smoke": True})
    wave_id = ledger.create_wave(run_id, execution_mode="mcp_only", metadata={"maintenance_smoke": True})
    ledger.finish_wave(wave_id, status="accepted")
    ledger.finish_run(run_id, status="accepted", metadata={"maintenance_smoke": True})
    integrity = ledger.verify_chain(run_id)
    if integrity.get("ok") is not True:
        raise RuntimeError("post-restart append smoke did not produce a valid event chain")
    return {"schema_version": 1, "smoke_appended": True, "run_id": run_id, "wave_id": wave_id, "chain_valid": True}
