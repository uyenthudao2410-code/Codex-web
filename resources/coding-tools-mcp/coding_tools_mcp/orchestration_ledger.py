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


SCHEMA_VERSION = 2
_MAX_TEXT = 16_000
HANDOFF_CAPSULE_MAX_BYTES = 8_192
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
                CREATE TABLE IF NOT EXISTS agent_lanes (
                    lane_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL DEFAULT '',
                    wave_id TEXT NOT NULL DEFAULT '',
                    semantic_key TEXT NOT NULL DEFAULT '',
                    role TEXT NOT NULL DEFAULT '',
                    provider TEXT NOT NULL DEFAULT 'codex_app_server',
                    thread_id TEXT NOT NULL DEFAULT '',
                    session_id TEXT NOT NULL DEFAULT '',
                    lifecycle TEXT NOT NULL,
                    profile TEXT NOT NULL DEFAULT '',
                    model TEXT NOT NULL DEFAULT '',
                    effort TEXT NOT NULL DEFAULT '',
                    base_head TEXT NOT NULL DEFAULT '',
                    worktree_fp TEXT NOT NULL DEFAULT '',
                    contract_fp TEXT NOT NULL DEFAULT '',
                    last_turn_id TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata_json TEXT NOT NULL DEFAULT '{}'
                );
                CREATE INDEX IF NOT EXISTS idx_agent_lanes_run_updated
                    ON agent_lanes(run_id, updated_at DESC);
                CREATE INDEX IF NOT EXISTS idx_agent_lanes_semantic
                    ON agent_lanes(run_id, semantic_key, lifecycle, updated_at DESC);
                CREATE UNIQUE INDEX IF NOT EXISTS idx_agent_lanes_one_live_semantic
                    ON agent_lanes(run_id, semantic_key)
                    WHERE semantic_key<>'' AND lifecycle IN ('starting','active','waiting','idle');
                CREATE TABLE IF NOT EXISTS coordination_messages (
                    message_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL DEFAULT '',
                    wave_id TEXT NOT NULL DEFAULT '',
                    lane_id TEXT NOT NULL DEFAULT '',
                    direction TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    status TEXT NOT NULL,
                    base_head TEXT NOT NULL DEFAULT '',
                    worktree_fp TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    acknowledged_at TEXT,
                    payload_json TEXT NOT NULL DEFAULT '{}'
                );
                CREATE INDEX IF NOT EXISTS idx_coordination_messages_pending
                    ON coordination_messages(run_id, status, created_at);
                CREATE INDEX IF NOT EXISTS idx_coordination_messages_lane
                    ON coordination_messages(lane_id, created_at);
                CREATE TABLE IF NOT EXISTS handoff_capsules (
                    capsule_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL DEFAULT '',
                    wave_id TEXT NOT NULL DEFAULT '',
                    conversation_epoch INTEGER NOT NULL DEFAULT 1,
                    version INTEGER NOT NULL DEFAULT 1,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    sha256 TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_handoff_capsules_run_created
                    ON handoff_capsules(run_id, created_at DESC);
                CREATE TABLE IF NOT EXISTS background_operations (
                    operation_id TEXT PRIMARY KEY,
                    server_instance_id TEXT NOT NULL,
                    tool TEXT NOT NULL,
                    task_id TEXT NOT NULL DEFAULT '',
                    run_id TEXT NOT NULL DEFAULT '',
                    wave_id TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    finished_at TEXT,
                    summary_json TEXT NOT NULL DEFAULT '{}'
                );
                CREATE INDEX IF NOT EXISTS idx_background_operations_status
                    ON background_operations(status, updated_at DESC);
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

    def list_checkpoints(self, run_id: str, *, wave_id: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM checkpoints WHERE run_id=?"
        params: list[Any] = [run_id]
        if wave_id:
            query += " AND wave_id=?"
            params.append(wave_id)
        query += " ORDER BY created_at, checkpoint_id"
        with self._lock, self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [
            {
                "checkpoint_id": row["checkpoint_id"],
                "run_id": row["run_id"],
                "wave_id": row["wave_id"],
                "git_head": row["git_head"],
                "proof_fingerprint": row["proof_fingerprint"],
                "status": row["status"],
                "created_at": row["created_at"],
                "metadata": json.loads(row["metadata_json"] or "{}"),
            }
            for row in rows
        ]

    def upsert_agent_lane(
        self,
        *,
        lane_id: str,
        run_id: str = "",
        wave_id: str = "",
        semantic_key: str = "",
        role: str = "worker",
        provider: str = "codex_app_server",
        thread_id: str = "",
        session_id: str = "",
        lifecycle: str = "active",
        profile: str = "",
        model: str = "",
        effort: str = "",
        base_head: str = "",
        worktree_fp: str = "",
        contract_fp: str = "",
        last_turn_id: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> str:
        now = utc_now()
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT created_at, metadata_json FROM agent_lanes WHERE lane_id=?",
                (lane_id,),
            ).fetchone()
            created_at = str(row["created_at"]) if row else now
            existing = json.loads(row["metadata_json"] or "{}") if row else {}
            existing.update(_sanitize(metadata or {}))
            try:
                connection.execute(
                    """INSERT INTO agent_lanes(
                    lane_id,run_id,wave_id,semantic_key,role,provider,thread_id,session_id,lifecycle,
                    profile,model,effort,base_head,worktree_fp,contract_fp,last_turn_id,created_at,updated_at,metadata_json
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(lane_id) DO UPDATE SET
                    run_id=excluded.run_id,wave_id=excluded.wave_id,semantic_key=excluded.semantic_key,
                    role=excluded.role,provider=excluded.provider,thread_id=excluded.thread_id,
                    session_id=excluded.session_id,lifecycle=excluded.lifecycle,profile=excluded.profile,
                    model=excluded.model,effort=excluded.effort,base_head=excluded.base_head,
                    worktree_fp=excluded.worktree_fp,contract_fp=excluded.contract_fp,
                    last_turn_id=excluded.last_turn_id,updated_at=excluded.updated_at,
                    metadata_json=excluded.metadata_json""",
                    (
                    _bounded_text(lane_id, 256),
                    _bounded_text(run_id, 256),
                    _bounded_text(wave_id, 256),
                    _bounded_text(semantic_key, 512),
                    _bounded_text(role, 100),
                    _bounded_text(provider, 100),
                    _bounded_text(thread_id, 256),
                    _bounded_text(session_id, 256),
                    _bounded_text(lifecycle, 64),
                    _bounded_text(profile, 100),
                    _bounded_text(model, 200),
                    _bounded_text(effort, 50),
                    _bounded_text(base_head, 128),
                    _bounded_text(worktree_fp, 128),
                    _bounded_text(contract_fp, 128),
                    _bounded_text(last_turn_id, 256),
                    created_at,
                    now,
                    _json(existing),
                    ),
                )
            except sqlite3.IntegrityError:
                existing_lane = connection.execute(
                    """SELECT lane_id FROM agent_lanes
                    WHERE run_id=? AND semantic_key=?
                    AND lifecycle IN ('starting','active','waiting','idle')
                    ORDER BY updated_at DESC LIMIT 1""",
                    (_bounded_text(run_id, 256), _bounded_text(semantic_key, 512)),
                ).fetchone()
                if existing_lane:
                    return str(existing_lane["lane_id"])
                raise
        return lane_id

    def update_agent_lane(self, lane_id: str, **changes: Any) -> dict[str, Any] | None:
        allowed = {
            "lifecycle",
            "thread_id",
            "session_id",
            "last_turn_id",
            "base_head",
            "worktree_fp",
            "contract_fp",
            "profile",
            "model",
            "effort",
            "wave_id",
        }
        updates = {key: value for key, value in changes.items() if key in allowed}
        metadata = changes.get("metadata")
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT metadata_json FROM agent_lanes WHERE lane_id=?",
                (lane_id,),
            ).fetchone()
            if not row:
                return None
            assignments: list[str] = []
            params: list[Any] = []
            for key, value in updates.items():
                assignments.append(f"{key}=?")
                params.append(_bounded_text(value, 256))
            if isinstance(metadata, dict):
                existing = json.loads(row["metadata_json"] or "{}")
                existing.update(_sanitize(metadata))
                assignments.append("metadata_json=?")
                params.append(_json(existing))
            assignments.append("updated_at=?")
            params.append(utc_now())
            params.append(lane_id)
            connection.execute(
                f"UPDATE agent_lanes SET {','.join(assignments)} WHERE lane_id=?",
                params,
            )
        return self.get_agent_lane(lane_id)

    @staticmethod
    def _lane_row(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "lane_id": row["lane_id"],
            "run_id": row["run_id"],
            "wave_id": row["wave_id"],
            "semantic_key": row["semantic_key"],
            "role": row["role"],
            "provider": row["provider"],
            "thread_id": row["thread_id"],
            "session_id": row["session_id"],
            "lifecycle": row["lifecycle"],
            "profile": row["profile"],
            "model": row["model"],
            "effort": row["effort"],
            "base_head": row["base_head"],
            "worktree_fp": row["worktree_fp"],
            "contract_fp": row["contract_fp"],
            "last_turn_id": row["last_turn_id"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "metadata": json.loads(row["metadata_json"] or "{}"),
        }

    def get_agent_lane(self, lane_id: str) -> dict[str, Any] | None:
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM agent_lanes WHERE lane_id=?",
                (lane_id,),
            ).fetchone()
        return self._lane_row(row) if row else None

    def find_agent_lane(self, *, run_id: str, semantic_key: str) -> dict[str, Any] | None:
        with self._lock, self._connect() as connection:
            row = connection.execute(
                """SELECT * FROM agent_lanes
                WHERE run_id=? AND semantic_key=? AND lifecycle IN ('active','waiting','idle')
                ORDER BY updated_at DESC LIMIT 1""",
                (run_id, semantic_key),
            ).fetchone()
        return self._lane_row(row) if row else None

    def list_agent_lanes(
        self,
        *,
        run_id: str = "",
        lifecycle: str = "",
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM agent_lanes WHERE 1=1"
        params: list[Any] = []
        if run_id:
            query += " AND run_id=?"
            params.append(run_id)
        if lifecycle:
            query += " AND lifecycle=?"
            params.append(lifecycle)
        query += " ORDER BY updated_at DESC, lane_id"
        with self._lock, self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [self._lane_row(row) for row in rows]

    def append_coordination_message(
        self,
        *,
        direction: str,
        kind: str,
        payload: dict[str, Any],
        run_id: str = "",
        wave_id: str = "",
        lane_id: str = "",
        status: str = "pending",
        base_head: str = "",
        worktree_fp: str = "",
        message_id: str | None = None,
    ) -> str:
        message_id = message_id or uuid.uuid4().hex
        with self._lock, self._connect() as connection:
            connection.execute(
                """INSERT OR IGNORE INTO coordination_messages(
                    message_id,run_id,wave_id,lane_id,direction,kind,status,base_head,worktree_fp,
                    created_at,acknowledged_at,payload_json
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    _bounded_text(message_id, 256),
                    _bounded_text(run_id, 256),
                    _bounded_text(wave_id, 256),
                    _bounded_text(lane_id, 256),
                    _bounded_text(direction, 64),
                    _bounded_text(kind, 100),
                    _bounded_text(status, 64),
                    _bounded_text(base_head, 128),
                    _bounded_text(worktree_fp, 128),
                    utc_now(),
                    None,
                    _json(_sanitize(payload)),
                ),
            )
        return message_id

    @staticmethod
    def _message_row(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "message_id": row["message_id"],
            "run_id": row["run_id"],
            "wave_id": row["wave_id"],
            "lane_id": row["lane_id"],
            "direction": row["direction"],
            "kind": row["kind"],
            "status": row["status"],
            "base_head": row["base_head"],
            "worktree_fp": row["worktree_fp"],
            "created_at": row["created_at"],
            "acknowledged_at": row["acknowledged_at"],
            "payload": json.loads(row["payload_json"] or "{}"),
        }

    def list_coordination_messages(
        self,
        *,
        run_id: str = "",
        lane_id: str = "",
        status: str = "",
        direction: str = "",
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM coordination_messages WHERE 1=1"
        params: list[Any] = []
        for key, value in (
            ("run_id", run_id),
            ("lane_id", lane_id),
            ("status", status),
            ("direction", direction),
        ):
            if value:
                query += f" AND {key}=?"
                params.append(value)
        query += " ORDER BY created_at, message_id LIMIT ?"
        params.append(max(1, min(int(limit), 200)))
        with self._lock, self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [self._message_row(row) for row in rows]

    def acknowledge_coordination_message(self, message_id: str) -> dict[str, Any] | None:
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM coordination_messages WHERE message_id=?",
                (message_id,),
            ).fetchone()
            if not row:
                return None
            if row["status"] != "acknowledged":
                connection.execute(
                    """UPDATE coordination_messages
                    SET status='acknowledged', acknowledged_at=? WHERE message_id=?""",
                    (utc_now(), message_id),
                )
            updated = connection.execute(
                "SELECT * FROM coordination_messages WHERE message_id=?",
                (message_id,),
            ).fetchone()
        return self._message_row(updated)

    def record_handoff_capsule(
        self,
        *,
        payload: dict[str, Any],
        run_id: str = "",
        wave_id: str = "",
        conversation_epoch: int = 1,
        status: str = "active",
        version: int = 1,
        capsule_id: str | None = None,
    ) -> dict[str, Any]:
        capsule_id = capsule_id or uuid.uuid4().hex
        safe_payload = _sanitize(payload)
        encoded = _json(safe_payload).encode("utf-8")
        if len(encoded) > HANDOFF_CAPSULE_MAX_BYTES:
            raise ValueError(f"handoff capsule exceeds {HANDOFF_CAPSULE_MAX_BYTES} bytes")
        digest = hashlib.sha256(encoded).hexdigest()
        created_at = utc_now()
        epoch = max(1, int(conversation_epoch))
        capsule_version = max(1, int(version))
        with self._lock, self._connect() as connection:
            connection.execute(
                """INSERT INTO handoff_capsules(
                    capsule_id,run_id,wave_id,conversation_epoch,version,status,
                    created_at,payload_json,sha256
                ) VALUES(?,?,?,?,?,?,?,?,?)""",
                (
                    _bounded_text(capsule_id, 256),
                    _bounded_text(run_id, 256),
                    _bounded_text(wave_id, 256),
                    epoch,
                    capsule_version,
                    _bounded_text(status, 64),
                    created_at,
                    encoded.decode("utf-8"),
                    digest,
                ),
            )
        return {
            "capsule_id": capsule_id,
            "run_id": run_id,
            "wave_id": wave_id,
            "conversation_epoch": epoch,
            "version": capsule_version,
            "status": status,
            "created_at": created_at,
            "payload": safe_payload,
            "sha256": digest,
            "bytes": len(encoded),
        }

    def latest_handoff_capsule(self, *, run_id: str = "") -> dict[str, Any] | None:
        with self._lock, self._connect() as connection:
            if run_id:
                row = connection.execute(
                    """SELECT * FROM handoff_capsules
                    WHERE run_id=? ORDER BY created_at DESC, capsule_id DESC LIMIT 1""",
                    (run_id,),
                ).fetchone()
            else:
                row = connection.execute(
                    """SELECT * FROM handoff_capsules
                    ORDER BY created_at DESC, capsule_id DESC LIMIT 1"""
                ).fetchone()
        if not row:
            return None
        payload_json = row["payload_json"] or "{}"
        return {
            "capsule_id": row["capsule_id"],
            "run_id": row["run_id"],
            "wave_id": row["wave_id"],
            "conversation_epoch": int(row["conversation_epoch"]),
            "version": int(row["version"]),
            "status": row["status"],
            "created_at": row["created_at"],
            "payload": json.loads(payload_json),
            "sha256": row["sha256"],
            "bytes": len(payload_json.encode("utf-8")),
        }

    def start_background_operation(
        self,
        *,
        operation_id: str,
        server_instance_id: str,
        tool: str,
        task_id: str = "",
        run_id: str = "",
        wave_id: str = "",
        summary: dict[str, Any] | None = None,
    ) -> None:
        now = utc_now()
        with self._lock, self._connect() as connection:
            connection.execute(
                """INSERT INTO background_operations(
                    operation_id,server_instance_id,tool,task_id,run_id,wave_id,status,
                    started_at,updated_at,finished_at,summary_json
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(operation_id) DO UPDATE SET
                    server_instance_id=excluded.server_instance_id,
                    tool=excluded.tool,task_id=excluded.task_id,run_id=excluded.run_id,
                    wave_id=excluded.wave_id,status=excluded.status,
                    updated_at=excluded.updated_at,finished_at=excluded.finished_at,
                    summary_json=excluded.summary_json""",
                (
                    _bounded_text(operation_id, 256),
                    _bounded_text(server_instance_id, 256),
                    _bounded_text(tool, 100),
                    _bounded_text(task_id, 256),
                    _bounded_text(run_id, 256),
                    _bounded_text(wave_id, 256),
                    "running",
                    now,
                    now,
                    None,
                    _json(_sanitize(summary or {})),
                ),
            )

    def finish_background_operation(
        self,
        operation_id: str,
        *,
        status: str,
        summary: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        now = utc_now()
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT summary_json FROM background_operations WHERE operation_id=?",
                (operation_id,),
            ).fetchone()
            if not row:
                return None
            existing = json.loads(row["summary_json"] or "{}")
            existing.update(_sanitize(summary or {}))
            connection.execute(
                """UPDATE background_operations
                SET status=?, updated_at=?, finished_at=?, summary_json=?
                WHERE operation_id=?""",
                (
                    _bounded_text(status, 64),
                    now,
                    now,
                    _json(existing),
                    operation_id,
                ),
            )
        return self.get_background_operation(operation_id)

    def mark_orphaned_background_operations(
        self,
        *,
        current_server_instance_id: str,
    ) -> int:
        now = utc_now()
        changed = 0
        with self._lock, self._connect() as connection:
            rows = connection.execute(
                """SELECT operation_id, summary_json FROM background_operations
                WHERE status='running' AND server_instance_id<>?""",
                (current_server_instance_id,),
            ).fetchall()
            for row in rows:
                summary = json.loads(row["summary_json"] or "{}")
                summary["orphan_reason"] = "mcp_runtime_restarted"
                connection.execute(
                    """UPDATE background_operations
                    SET status='orphaned', updated_at=?, finished_at=?, summary_json=?
                    WHERE operation_id=?""",
                    (now, now, _json(_sanitize(summary)), row["operation_id"]),
                )
                changed += 1
        return changed

    @staticmethod
    def _background_row(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "operation_id": row["operation_id"],
            "server_instance_id": row["server_instance_id"],
            "tool": row["tool"],
            "task_id": row["task_id"],
            "run_id": row["run_id"],
            "wave_id": row["wave_id"],
            "status": row["status"],
            "started_at": row["started_at"],
            "updated_at": row["updated_at"],
            "finished_at": row["finished_at"],
            "summary": json.loads(row["summary_json"] or "{}"),
        }

    def get_background_operation(self, operation_id: str) -> dict[str, Any] | None:
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM background_operations WHERE operation_id=?",
                (operation_id,),
            ).fetchone()
        return self._background_row(row) if row else None

    def list_background_operations(self, *, limit: int = 20) -> list[dict[str, Any]]:
        with self._lock, self._connect() as connection:
            rows = connection.execute(
                """SELECT * FROM background_operations
                ORDER BY updated_at DESC, operation_id DESC LIMIT ?""",
                (max(1, min(int(limit), 200)),),
            ).fetchall()
        return [self._background_row(row) for row in rows]

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
        checkpoints = self.list_checkpoints(run_id)
        delegations = [item for wave in waves for item in self.list_delegations(wave["wave_id"])]
        lanes = self.list_agent_lanes(run_id=run_id)
        messages = self.list_coordination_messages(run_id=run_id, limit=100)
        capsule = self.latest_handoff_capsule(run_id=run_id)
        return {
            "run": run,
            "waves": waves,
            "delegations": delegations,
            "events": events,
            "proofs": proofs,
            "checkpoints": checkpoints,
            "lanes": lanes,
            "messages": messages,
            "latest_handoff_capsule": capsule,
            "integrity": self.verify_chain(run_id),
        }
