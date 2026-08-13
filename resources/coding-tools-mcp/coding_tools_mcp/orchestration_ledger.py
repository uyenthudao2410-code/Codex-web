from __future__ import annotations

import hashlib
from contextlib import contextmanager
import json
import os
import re
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = 1
_MAX_TEXT = 16_000
_SECRET_KEY_RE = re.compile(r"(authorization|credential|password|passwd|secret|token|api[_-]?key|private[_-]?key)", re.I)
_SENSITIVE_PAYLOAD_KEYS = {
    "content",
    "file_content",
    "prompt",
    "raw_prompt",
    "patch",
    "stdout",
    "stderr",
    "agent_text",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _bounded_text(value: Any, limit: int = _MAX_TEXT) -> str:
    text = str(value or "")
    return text if len(text) <= limit else text[:limit] + "..."


def _sanitize(value: Any, *, key: str = "") -> Any:
    if _SECRET_KEY_RE.search(key):
        return "[REDACTED]"
    if key.lower() in _SENSITIVE_PAYLOAD_KEYS:
        text = str(value or "")
        return {
            "redacted": True,
            "sha256": hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest(),
            "bytes": len(text.encode("utf-8", errors="replace")),
        }
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return _bounded_text(value)
    if isinstance(value, dict):
        return {str(k)[:200]: _sanitize(v, key=str(k)) for k, v in list(value.items())[:200]}
    if isinstance(value, (list, tuple, set)):
        return [_sanitize(item) for item in list(value)[:500]]
    return _bounded_text(value)


def fingerprint_paths(root: Path, paths: Iterable[str], *, extra: dict[str, Any] | None = None) -> str:
    """Content fingerprint for the selected workspace paths plus stable metadata."""
    digest = hashlib.sha256()
    root = root.resolve(strict=False)
    for raw in sorted({str(item).replace("\\", "/") for item in paths if str(item).strip()}):
        digest.update(raw.encode("utf-8", errors="replace"))
        target = (root / Path(*raw.split("/"))).resolve(strict=False)
        try:
            if not target.is_relative_to(root):
                digest.update(b"<outside>")
                continue
            if target.is_file():
                with target.open("rb") as handle:
                    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                        digest.update(chunk)
            elif target.exists():
                digest.update(b"<non-file>")
            else:
                digest.update(b"<missing>")
        except OSError as exc:
            digest.update(f"<error:{type(exc).__name__}>".encode("ascii", errors="replace"))
    if extra:
        digest.update(_json(_sanitize(extra)).encode("utf-8"))
    return digest.hexdigest()


class OrchestrationLedger:
    """Durable append-only orchestration audit source for one workspace.

    The ledger stores structured control/evidence identity, not raw prompts, patches,
    file contents, stdout, or stderr. Events are hash-chained per run so accidental
    truncation/reordering can be detected during postmortem or report generation.
    """

    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace.resolve(strict=False)
        self.state_dir = self.workspace / ".coding-tools" / "orchestration"
        self.path = self.state_dir / "ledger.sqlite3"
        self._lock = threading.RLock()
        self._ensure_schema()

    @contextmanager
    def _connect(self):
        self.state_dir.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=5.0)
        connection.row_factory = sqlite3.Row
        try:
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute("PRAGMA busy_timeout=5000")
            try:
                connection.execute("PRAGMA journal_mode=WAL")
            except sqlite3.DatabaseError:
                pass
            connection.execute("PRAGMA synchronous=NORMAL")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _ensure_schema(self) -> None:
        with self._lock, self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL DEFAULT '',
                    objective TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    finished_at TEXT,
                    metadata_json TEXT NOT NULL DEFAULT '{}'
                );
                CREATE TABLE IF NOT EXISTS waves (
                    wave_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
                    ordinal INTEGER NOT NULL,
                    execution_mode TEXT NOT NULL,
                    base_head TEXT NOT NULL DEFAULT '',
                    worktree_fp TEXT NOT NULL DEFAULT '',
                    contract_fp TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    finished_at TEXT,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    UNIQUE(run_id, ordinal)
                );
                CREATE TABLE IF NOT EXISTS delegations (
                    delegation_id TEXT PRIMARY KEY,
                    wave_id TEXT NOT NULL REFERENCES waves(wave_id) ON DELETE CASCADE,
                    parent_delegation_id TEXT,
                    authority_owner TEXT NOT NULL,
                    route_requested TEXT NOT NULL DEFAULT '',
                    route_resolved TEXT NOT NULL DEFAULT '',
                    model TEXT NOT NULL DEFAULT '',
                    effort TEXT NOT NULL DEFAULT '',
                    allowed_scope_json TEXT NOT NULL DEFAULT '[]',
                    status TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    finished_at TEXT,
                    metadata_json TEXT NOT NULL DEFAULT '{}'
                );
                CREATE TABLE IF NOT EXISTS events (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL UNIQUE,
                    run_id TEXT NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
                    wave_id TEXT,
                    delegation_id TEXT,
                    event_type TEXT NOT NULL,
                    state_before TEXT NOT NULL DEFAULT '',
                    state_after TEXT NOT NULL DEFAULT '',
                    event_time TEXT NOT NULL,
                    payload_json TEXT NOT NULL DEFAULT '{}',
                    prev_hash TEXT NOT NULL DEFAULT '',
                    event_hash TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_events_run_seq ON events(run_id, seq);
                CREATE INDEX IF NOT EXISTS idx_events_wave_seq ON events(wave_id, seq);
                CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
                CREATE TABLE IF NOT EXISTS proofs (
                    proof_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
                    wave_id TEXT NOT NULL REFERENCES waves(wave_id) ON DELETE CASCADE,
                    stage_id TEXT NOT NULL,
                    stage_version TEXT NOT NULL,
                    input_fingerprint TEXT NOT NULL,
                    status TEXT NOT NULL,
                    command_hash TEXT NOT NULL DEFAULT '',
                    started_at TEXT NOT NULL,
                    finished_at TEXT NOT NULL,
                    duration_ms INTEGER NOT NULL DEFAULT 0,
                    exit_code INTEGER,
                    cache_hit INTEGER NOT NULL DEFAULT 0,
                    upstream_json TEXT NOT NULL DEFAULT '[]',
                    metadata_json TEXT NOT NULL DEFAULT '{}'
                );
                CREATE INDEX IF NOT EXISTS idx_proofs_lookup
                    ON proofs(stage_id, stage_version, input_fingerprint, status, finished_at);
                CREATE INDEX IF NOT EXISTS idx_proofs_wave ON proofs(wave_id, finished_at);
                CREATE TABLE IF NOT EXISTS checkpoints (
                    checkpoint_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
                    wave_id TEXT,
                    git_head TEXT NOT NULL DEFAULT '',
                    proof_fingerprint TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    metadata_json TEXT NOT NULL DEFAULT '{}'
                );
                """
            )
            connection.execute(f"PRAGMA user_version={SCHEMA_VERSION}")

    def create_run(
        self,
        *,
        objective: str,
        task_id: str = "",
        metadata: dict[str, Any] | None = None,
        run_id: str | None = None,
    ) -> str:
        run_id = run_id or uuid.uuid4().hex
        now = utc_now()
        with self._lock, self._connect() as connection:
            connection.execute(
                "INSERT INTO runs(run_id,task_id,objective,status,started_at,metadata_json) VALUES(?,?,?,?,?,?)",
                (run_id, _bounded_text(task_id, 256), _bounded_text(objective, 4000), "active", now, _json(_sanitize(metadata or {}))),
            )
        return run_id

    def finish_run(self, run_id: str, *, status: str, metadata: dict[str, Any] | None = None) -> None:
        now = utc_now()
        with self._lock, self._connect() as connection:
            row = connection.execute("SELECT metadata_json FROM runs WHERE run_id=?", (run_id,)).fetchone()
            existing = json.loads(row[0]) if row else {}
            existing.update(_sanitize(metadata or {}))
            connection.execute(
                "UPDATE runs SET status=?, finished_at=?, metadata_json=? WHERE run_id=?",
                (_bounded_text(status, 64), now, _json(existing), run_id),
            )

    def create_wave(
        self,
        run_id: str,
        *,
        execution_mode: str,
        base_head: str = "",
        worktree_fp: str = "",
        contract_fp: str = "",
        metadata: dict[str, Any] | None = None,
        wave_id: str | None = None,
    ) -> str:
        wave_id = wave_id or uuid.uuid4().hex
        now = utc_now()
        with self._lock, self._connect() as connection:
            ordinal = int(connection.execute("SELECT COALESCE(MAX(ordinal),0)+1 FROM waves WHERE run_id=?", (run_id,)).fetchone()[0])
            connection.execute(
                """INSERT INTO waves(
                    wave_id,run_id,ordinal,execution_mode,base_head,worktree_fp,contract_fp,status,started_at,metadata_json
                ) VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (
                    wave_id,
                    run_id,
                    ordinal,
                    _bounded_text(execution_mode, 100),
                    _bounded_text(base_head, 128),
                    _bounded_text(worktree_fp, 128),
                    _bounded_text(contract_fp, 128),
                    "active",
                    now,
                    _json(_sanitize(metadata or {})),
                ),
            )
        return wave_id

    def set_wave_execution_mode(self, wave_id: str, execution_mode: str) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                "UPDATE waves SET execution_mode=? WHERE wave_id=?",
                (_bounded_text(execution_mode, 100), wave_id),
            )

    def finish_wave(self, wave_id: str, *, status: str, metadata: dict[str, Any] | None = None) -> None:
        now = utc_now()
        with self._lock, self._connect() as connection:
            row = connection.execute("SELECT metadata_json FROM waves WHERE wave_id=?", (wave_id,)).fetchone()
            existing = json.loads(row[0]) if row else {}
            existing.update(_sanitize(metadata or {}))
            connection.execute(
                "UPDATE waves SET status=?, finished_at=?, metadata_json=? WHERE wave_id=?",
                (_bounded_text(status, 64), now, _json(existing), wave_id),
            )

    def create_delegation(
        self,
        wave_id: str,
        *,
        authority_owner: str,
        route_requested: str = "",
        route_resolved: str = "",
        model: str = "",
        effort: str = "",
        parent_delegation_id: str | None = None,
        allowed_scope: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        delegation_id: str | None = None,
    ) -> str:
        delegation_id = delegation_id or uuid.uuid4().hex
        now = utc_now()
        with self._lock, self._connect() as connection:
            connection.execute(
                """INSERT INTO delegations(
                    delegation_id,wave_id,parent_delegation_id,authority_owner,route_requested,route_resolved,
                    model,effort,allowed_scope_json,status,started_at,metadata_json
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    delegation_id,
                    wave_id,
                    parent_delegation_id,
                    _bounded_text(authority_owner, 200),
                    _bounded_text(route_requested, 100),
                    _bounded_text(route_resolved, 100),
                    _bounded_text(model, 200),
                    _bounded_text(effort, 50),
                    _json(_sanitize(allowed_scope or [])),
                    "active",
                    now,
                    _json(_sanitize(metadata or {})),
                ),
            )
        return delegation_id

    def finish_delegation(self, delegation_id: str, *, status: str, metadata: dict[str, Any] | None = None) -> None:
        now = utc_now()
        with self._lock, self._connect() as connection:
            row = connection.execute("SELECT metadata_json FROM delegations WHERE delegation_id=?", (delegation_id,)).fetchone()
            existing = json.loads(row[0]) if row else {}
            existing.update(_sanitize(metadata or {}))
            connection.execute(
                "UPDATE delegations SET status=?, finished_at=?, metadata_json=? WHERE delegation_id=?",
                (_bounded_text(status, 64), now, _json(existing), delegation_id),
            )

    def append_event(
        self,
        run_id: str,
        *,
        event_type: str,
        wave_id: str | None = None,
        delegation_id: str | None = None,
        state_before: str = "",
        state_after: str = "",
        payload: dict[str, Any] | None = None,
        event_time: str | None = None,
    ) -> dict[str, Any]:
        event_id = uuid.uuid4().hex
        event_time = event_time or utc_now()
        safe_payload = _sanitize(payload or {})
        with self._lock, self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            previous = connection.execute(
                "SELECT event_hash FROM events WHERE run_id=? ORDER BY seq DESC LIMIT 1", (run_id,)
            ).fetchone()
            prev_hash = str(previous[0]) if previous else ""
            core = {
                "event_id": event_id,
                "run_id": run_id,
                "wave_id": wave_id or "",
                "delegation_id": delegation_id or "",
                "event_type": event_type,
                "state_before": state_before,
                "state_after": state_after,
                "event_time": event_time,
                "payload": safe_payload,
                "prev_hash": prev_hash,
            }
            event_hash = hashlib.sha256(_json(core).encode("utf-8")).hexdigest()
            cursor = connection.execute(
                """INSERT INTO events(
                    event_id,run_id,wave_id,delegation_id,event_type,state_before,state_after,event_time,payload_json,prev_hash,event_hash
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    event_id,
                    run_id,
                    wave_id,
                    delegation_id,
                    _bounded_text(event_type, 100),
                    _bounded_text(state_before, 64),
                    _bounded_text(state_after, 64),
                    event_time,
                    _json(safe_payload),
                    prev_hash,
                    event_hash,
                ),
            )
            seq = int(cursor.lastrowid)
            connection.commit()
        return {**core, "seq": seq, "event_hash": event_hash}

    def list_events(self, run_id: str, *, wave_id: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM events WHERE run_id=?"
        params: list[Any] = [run_id]
        if wave_id:
            query += " AND wave_id=?"
            params.append(wave_id)
        query += " ORDER BY seq"
        with self._lock, self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [self._event_row(row) for row in rows]

    def latest_event(self, run_id: str, *, event_types: set[str] | None = None) -> dict[str, Any] | None:
        with self._lock, self._connect() as connection:
            if event_types:
                values = sorted(event_types)
                placeholders = ",".join("?" for _ in values)
                row = connection.execute(
                    f"SELECT * FROM events WHERE run_id=? AND event_type IN ({placeholders}) ORDER BY seq DESC LIMIT 1",
                    [run_id, *values],
                ).fetchone()
            else:
                row = connection.execute("SELECT * FROM events WHERE run_id=? ORDER BY seq DESC LIMIT 1", (run_id,)).fetchone()
        return self._event_row(row) if row else None

    @staticmethod
    def _event_row(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "seq": int(row["seq"]),
            "event_id": row["event_id"],
            "run_id": row["run_id"],
            "wave_id": row["wave_id"],
            "delegation_id": row["delegation_id"],
            "event_type": row["event_type"],
            "state_before": row["state_before"],
            "state_after": row["state_after"],
            "event_time": row["event_time"],
            "payload": json.loads(row["payload_json"] or "{}"),
            "prev_hash": row["prev_hash"],
            "event_hash": row["event_hash"],
        }

    def verify_chain(self, run_id: str) -> dict[str, Any]:
        previous = ""
        checked = 0
        for event in self.list_events(run_id):
            core = {
                "event_id": event["event_id"],
                "run_id": event["run_id"],
                "wave_id": event.get("wave_id") or "",
                "delegation_id": event.get("delegation_id") or "",
                "event_type": event["event_type"],
                "state_before": event.get("state_before") or "",
                "state_after": event.get("state_after") or "",
                "event_time": event["event_time"],
                "payload": event.get("payload") or {},
                "prev_hash": previous,
            }
            expected = hashlib.sha256(_json(core).encode("utf-8")).hexdigest()
            if event.get("prev_hash") != previous or event.get("event_hash") != expected:
                return {"ok": False, "checked": checked, "failed_seq": event["seq"]}
            previous = expected
            checked += 1
        return {"ok": True, "checked": checked, "head_hash": previous}

    def record_proof(
        self,
        *,
        run_id: str,
        wave_id: str,
        stage_id: str,
        stage_version: str,
        input_fingerprint: str,
        status: str,
        command_hash: str = "",
        started_at: str | None = None,
        finished_at: str | None = None,
        duration_ms: int = 0,
        exit_code: int | None = None,
        cache_hit: bool = False,
        upstream_proof_ids: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        proof_id: str | None = None,
    ) -> str:
        proof_id = proof_id or uuid.uuid4().hex
        finished_at = finished_at or utc_now()
        started_at = started_at or finished_at
        with self._lock, self._connect() as connection:
            connection.execute(
                """INSERT INTO proofs(
                    proof_id,run_id,wave_id,stage_id,stage_version,input_fingerprint,status,command_hash,
                    started_at,finished_at,duration_ms,exit_code,cache_hit,upstream_json,metadata_json
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    proof_id,
                    run_id,
                    wave_id,
                    _bounded_text(stage_id, 200),
                    _bounded_text(stage_version, 100),
                    _bounded_text(input_fingerprint, 128),
                    _bounded_text(status, 64),
                    _bounded_text(command_hash, 128),
                    started_at,
                    finished_at,
                    max(0, int(duration_ms)),
                    exit_code,
                    1 if cache_hit else 0,
                    _json(_sanitize(upstream_proof_ids or [])),
                    _json(_sanitize(metadata or {})),
                ),
            )
        return proof_id

    def find_cached_pass(self, *, stage_id: str, stage_version: str, input_fingerprint: str) -> dict[str, Any] | None:
        with self._lock, self._connect() as connection:
            row = connection.execute(
                """SELECT * FROM proofs
                WHERE stage_id=? AND stage_version=? AND input_fingerprint=? AND status='passed'
                ORDER BY finished_at DESC LIMIT 1""",
                (stage_id, stage_version, input_fingerprint),
            ).fetchone()
        return self._proof_row(row) if row else None

    def list_proofs(self, run_id: str, *, wave_id: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM proofs WHERE run_id=?"
        params: list[Any] = [run_id]
        if wave_id:
            query += " AND wave_id=?"
            params.append(wave_id)
        query += " ORDER BY finished_at, proof_id"
        with self._lock, self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [self._proof_row(row) for row in rows]

    @staticmethod
    def _proof_row(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "proof_id": row["proof_id"],
            "run_id": row["run_id"],
            "wave_id": row["wave_id"],
            "stage_id": row["stage_id"],
            "stage_version": row["stage_version"],
            "input_fingerprint": row["input_fingerprint"],
            "status": row["status"],
            "command_hash": row["command_hash"],
            "started_at": row["started_at"],
            "finished_at": row["finished_at"],
            "duration_ms": int(row["duration_ms"] or 0),
            "exit_code": row["exit_code"],
            "cache_hit": bool(row["cache_hit"]),
            "upstream_proof_ids": json.loads(row["upstream_json"] or "[]"),
            "metadata": json.loads(row["metadata_json"] or "{}"),
        }

    def record_checkpoint(
        self,
        *,
        run_id: str,
        wave_id: str | None,
        git_head: str,
        proof_fingerprint: str,
        status: str = "accepted",
        metadata: dict[str, Any] | None = None,
    ) -> str:
        checkpoint_id = uuid.uuid4().hex
        with self._lock, self._connect() as connection:
            connection.execute(
                "INSERT INTO checkpoints VALUES(?,?,?,?,?,?,?,?)",
                (
                    checkpoint_id,
                    run_id,
                    wave_id,
                    _bounded_text(git_head, 128),
                    _bounded_text(proof_fingerprint, 128),
                    _bounded_text(status, 64),
                    utc_now(),
                    _json(_sanitize(metadata or {})),
                ),
            )
        return checkpoint_id

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        with self._lock, self._connect() as connection:
            row = connection.execute("SELECT * FROM runs WHERE run_id=?", (run_id,)).fetchone()
        if not row:
            return None
        return {
            "run_id": row["run_id"],
            "task_id": row["task_id"],
            "objective": row["objective"],
            "status": row["status"],
            "started_at": row["started_at"],
            "finished_at": row["finished_at"],
            "metadata": json.loads(row["metadata_json"] or "{}"),
        }

    def list_waves(self, run_id: str) -> list[dict[str, Any]]:
        with self._lock, self._connect() as connection:
            rows = connection.execute("SELECT * FROM waves WHERE run_id=? ORDER BY ordinal", (run_id,)).fetchall()
        return [
            {
                "wave_id": row["wave_id"],
                "run_id": row["run_id"],
                "ordinal": int(row["ordinal"]),
                "execution_mode": row["execution_mode"],
                "base_head": row["base_head"],
                "worktree_fp": row["worktree_fp"],
                "contract_fp": row["contract_fp"],
                "status": row["status"],
                "started_at": row["started_at"],
                "finished_at": row["finished_at"],
                "metadata": json.loads(row["metadata_json"] or "{}"),
            }
            for row in rows
        ]

    def list_delegations(self, wave_id: str) -> list[dict[str, Any]]:
        with self._lock, self._connect() as connection:
            rows = connection.execute("SELECT * FROM delegations WHERE wave_id=? ORDER BY started_at", (wave_id,)).fetchall()
        return [
            {
                "delegation_id": row["delegation_id"],
                "wave_id": row["wave_id"],
                "parent_delegation_id": row["parent_delegation_id"],
                "authority_owner": row["authority_owner"],
                "route_requested": row["route_requested"],
                "route_resolved": row["route_resolved"],
                "model": row["model"],
                "effort": row["effort"],
                "allowed_scope": json.loads(row["allowed_scope_json"] or "[]"),
                "status": row["status"],
                "started_at": row["started_at"],
                "finished_at": row["finished_at"],
                "metadata": json.loads(row["metadata_json"] or "{}"),
            }
            for row in rows
        ]

    def current_active_run(self, *, task_id: str = "") -> dict[str, Any] | None:
        with self._lock, self._connect() as connection:
            if task_id:
                row = connection.execute(
                    "SELECT * FROM runs WHERE task_id=? AND status='active' ORDER BY started_at DESC LIMIT 1", (task_id,)
                ).fetchone()
            else:
                row = connection.execute("SELECT * FROM runs WHERE status='active' ORDER BY started_at DESC LIMIT 1").fetchone()
        if not row:
            return None
        return self.get_run(str(row["run_id"]))

    def export_summary(self, run_id: str) -> dict[str, Any]:
        run = self.get_run(run_id) or {}
        waves = self.list_waves(run_id)
        events = self.list_events(run_id)
        proofs = self.list_proofs(run_id)
        delegations = [item for wave in waves for item in self.list_delegations(wave["wave_id"])]
        return {
            "run": run,
            "waves": waves,
            "delegations": delegations,
            "events": events,
            "proofs": proofs,
            "integrity": self.verify_chain(run_id),
        }
