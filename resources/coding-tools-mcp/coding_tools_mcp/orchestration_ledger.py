from __future__ import annotations

import hashlib
from contextlib import contextmanager
import json
import math
import re
import sqlite3
import threading
import time
import uuid
import zlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .artifact_refs import handoff_capsule_artifact_ref, proof_artifact_ref
from .idempotency_codec import decode_summary as _decode_idempotency_summary, encode_summary as _encode_idempotency_summary
from .ledger_file_gate import ledger_access_gate
from .ledger_event_chain import append_hash_chained_event
from .lifecycle_reconciliation import LifecycleReconciliationLedgerMixin
from .observation_spans import ObservationSpanLedgerMixin
from .p5_experiment_store import P5ExperimentLedgerMixin
from .problem_lineage import ProblemLineageLedgerMixin
from .quality_outcomes import QualityOutcomeLedgerMixin
from .usage_ledger import (
    CANONICAL_USAGE_KEYS,
    canonical_usage_payload,
    list_usage_events as _list_usage_events,
    recent_usage_events as _recent_usage_events,
    record_usage_event as _record_usage_event,
    usage_analytics as _usage_analytics,
)

SCHEMA_VERSION = 9
_MAX_TEXT = 16_000
_PROOF_METADATA_COMPRESSION_PREFIX = b"WCPM1\0"
_PROOF_METADATA_COMPRESSION_MIN_BYTES = 4_096
HANDOFF_CAPSULE_MAX_BYTES = 8_192
_SECRET_KEY_RE = re.compile(r"(authorization|credential|password|passwd|secret|token|api[_-]?key|private[_-]?key)", re.I)
_SAFE_NUMERIC_USAGE_KEYS = {
    "input_tokens",
    "cached_input_tokens",
    "uncached_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
    "cached_tokens",
    "cache_read_tokens",
    "cache_write_tokens",
    *CANONICAL_USAGE_KEYS,
}
_PROVIDER_MESSAGE_NUMERIC_KEYS = frozenset({
    "input_tokens",
    "cached_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
    "cache_read_tokens",
    "cache_write_tokens",
    "provider_cost",
    "duration_ms",
})
_MAX_PROVIDER_MESSAGE_ECONOMICS = 128
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
def resource_claim_owner_hash(owner_type: str, owner_id: str) -> str:
    material = f"webcodex-resource-claim-v1\0{str(owner_type).upper()}\0{owner_id}"
    return hashlib.sha256(material.encode("utf-8", errors="replace")).hexdigest()
def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
def _encode_proof_metadata(value: dict[str, Any]) -> str | bytes:
    text = _json(_sanitize(value))
    raw = text.encode("utf-8")
    if len(raw) < _PROOF_METADATA_COMPRESSION_MIN_BYTES:
        return text
    encoded = _PROOF_METADATA_COMPRESSION_PREFIX + zlib.compress(raw)
    return encoded if len(encoded) < len(raw) else text

def _decode_proof_metadata(value: Any) -> dict[str, Any]:
    if value is None or value == "":
        return {}
    if isinstance(value, str):
        decoded = json.loads(value)
    else:
        raw = bytes(value)
        if raw.startswith(_PROOF_METADATA_COMPRESSION_PREFIX):
            raw = zlib.decompress(raw[len(_PROOF_METADATA_COMPRESSION_PREFIX):])
        decoded = json.loads(raw.decode("utf-8"))
    if not isinstance(decoded, dict):
        raise ValueError("proof metadata must decode to a JSON object")
    return decoded

def _bounded_text(value: Any, limit: int = _MAX_TEXT) -> str:
    text = str(value or "")
    return text if len(text) <= limit else text[:limit] + "..."

def _sanitize(value: Any, *, key: str = "") -> Any:
    normalized_key = key.lower()
    if normalized_key in _SAFE_NUMERIC_USAGE_KEYS:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
            return "[REDACTED]"
        return value
    if normalized_key != "fencing_token" and _SECRET_KEY_RE.search(key):
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

def _proof_cache_opportunity_summary(
    connection: sqlite3.Connection,
    *,
    stage_limit: int = 100,
) -> dict[str, Any]:
    """Aggregate content-free proof-cache opportunity evidence from the EOCL ledger."""
    bounded_stage_limit = max(1, min(int(stage_limit), 100))
    opportunity_cte = """
        WITH opportunities AS (
            SELECT
                e.run_id AS run_id,
                e.event_type AS event_type,
                e.event_time AS event_time,
                COALESCE(NULLIF(CAST(json_extract(e.payload_json, '$.stage_id') AS TEXT), ''), 'unknown') AS stage_id,
                COALESCE(NULLIF(CAST(json_extract(e.payload_json, '$.stage_version') AS TEXT), ''), 'unknown') AS stage_version,
                CASE WHEN e.event_type='proof_cache_hit' THEN 1 ELSE 0 END AS is_hit,
                CASE WHEN e.event_type='proof_cache_miss' THEN 1 ELSE 0 END AS is_miss,
                CASE
                    WHEN json_extract(e.payload_json, '$.reason') IN ('cold', 'input_fingerprint_changed', 'stage_version_changed')
                    THEN CAST(json_extract(e.payload_json, '$.reason') AS TEXT)
                    ELSE 'other'
                END AS miss_class,
                CASE WHEN r.status='accepted' THEN 1 ELSE 0 END AS accepted_run,
                CASE WHEN EXISTS(
                    SELECT 1 FROM checkpoints c
                    WHERE c.run_id=e.run_id AND c.status='accepted'
                ) THEN 1 ELSE 0 END AS accepted_checkpoint,
                CASE
                    WHEN e.event_type='proof_cache_hit' AND p.proof_id IS NOT NULL
                    THEN MAX(0, CAST(p.duration_ms AS INTEGER))
                    ELSE NULL
                END AS source_duration_ms
            FROM events e
            JOIN runs r ON r.run_id=e.run_id
            LEFT JOIN proofs p
              ON e.event_type='proof_cache_hit'
             AND p.proof_id=CAST(json_extract(e.payload_json, '$.source_proof_id') AS TEXT)
            WHERE e.event_type IN ('proof_cache_hit', 'proof_cache_miss')
        )
    """
    overall = connection.execute(
        opportunity_cte
        + """
        SELECT
            COUNT(*),
            COALESCE(SUM(is_hit), 0),
            COALESCE(SUM(is_miss), 0),
            COALESCE(SUM(CASE WHEN is_hit=1 AND source_duration_ms IS NOT NULL THEN 1 ELSE 0 END), 0),
            COALESCE(SUM(CASE WHEN is_hit=1 AND source_duration_ms IS NOT NULL THEN source_duration_ms ELSE 0 END), 0),
            COUNT(DISTINCT run_id),
            COUNT(DISTINCT CASE WHEN accepted_run=1 THEN run_id END),
            COUNT(DISTINCT CASE WHEN accepted_checkpoint=1 THEN run_id END),
            COALESCE(SUM(accepted_run), 0),
            COALESCE(SUM(CASE WHEN accepted_run=1 THEN is_hit ELSE 0 END), 0),
            COALESCE(SUM(accepted_checkpoint), 0),
            COALESCE(SUM(CASE WHEN accepted_checkpoint=1 THEN is_hit ELSE 0 END), 0),
            MIN(event_time),
            MAX(event_time)
        FROM opportunities
        """
    ).fetchone()
    eligible = int(overall[0] or 0)
    hits = int(overall[1] or 0)
    misses = int(overall[2] or 0)
    known_saved_hits = int(overall[3] or 0)
    known_saved_ms = int(overall[4] or 0)
    miss_rows = connection.execute(
        opportunity_cte
        + """
        SELECT miss_class, COUNT(*)
        FROM opportunities
        WHERE is_miss=1
        GROUP BY miss_class
        ORDER BY COUNT(*) DESC, miss_class
        """
    ).fetchall()
    miss_reasons = {str(row[0]): int(row[1]) for row in miss_rows if int(row[1] or 0) > 0}
    stage_rows = connection.execute(
        opportunity_cte
        + """
        SELECT
            stage_id,
            stage_version,
            COUNT(*) AS eligible,
            COALESCE(SUM(is_hit), 0) AS hits,
            COALESCE(SUM(is_miss), 0) AS misses,
            COALESCE(SUM(CASE WHEN is_hit=1 AND source_duration_ms IS NOT NULL THEN 1 ELSE 0 END), 0) AS known_saved_hits,
            COALESCE(SUM(CASE WHEN is_hit=1 AND source_duration_ms IS NOT NULL THEN source_duration_ms ELSE 0 END), 0) AS known_saved_ms,
            COALESCE(SUM(accepted_run), 0) AS accepted_run_opportunities,
            COALESCE(SUM(CASE WHEN accepted_run=1 THEN is_hit ELSE 0 END), 0) AS accepted_run_hits,
            COALESCE(SUM(accepted_checkpoint), 0) AS accepted_checkpoint_opportunities,
            COALESCE(SUM(CASE WHEN accepted_checkpoint=1 THEN is_hit ELSE 0 END), 0) AS accepted_checkpoint_hits
        FROM opportunities
        GROUP BY stage_id, stage_version
        ORDER BY eligible DESC, stage_id, stage_version
        LIMIT ?
        """,
        (bounded_stage_limit,),
    ).fetchall()
    stages: list[dict[str, Any]] = []
    for row in stage_rows:
        stage_eligible = int(row[2] or 0)
        stage_hits = int(row[3] or 0)
        stage_known_saved_hits = int(row[5] or 0)
        stage_known_saved_ms = int(row[6] or 0)
        stage_saved_complete = stage_known_saved_hits == stage_hits
        stages.append({
            "stage_id": str(row[0]),
            "stage_version": str(row[1]),
            "eligible": stage_eligible,
            "hits": stage_hits,
            "misses": int(row[4] or 0),
            "hit_rate": round(stage_hits / stage_eligible, 6) if stage_eligible else None,
            "saved_ms": stage_known_saved_ms if stage_saved_complete else None,
            "saved_ms_known": stage_known_saved_ms,
            "saved_ms_known_hits": stage_known_saved_hits,
            "saved_ms_complete": stage_saved_complete,
            "accepted_run_opportunities": int(row[7] or 0),
            "accepted_run_hits": int(row[8] or 0),
            "accepted_checkpoint_opportunities": int(row[9] or 0),
            "accepted_checkpoint_hits": int(row[10] or 0),
        })
    saved_complete = known_saved_hits == hits
    accepted_run_opportunities = int(overall[8] or 0)
    accepted_checkpoint_opportunities = int(overall[10] or 0)
    fingerprint_classes = {
        "exact_reuse": hits,
        "cold": int(miss_reasons.get("cold", 0)),
        "input_fingerprint_changed": int(miss_reasons.get("input_fingerprint_changed", 0)),
        "stage_version_changed": int(miss_reasons.get("stage_version_changed", 0)),
        "other_miss": int(miss_reasons.get("other", 0)),
    }
    stage_group_count = int(connection.execute(
        opportunity_cte + "SELECT COUNT(*) FROM (SELECT 1 FROM opportunities GROUP BY stage_id, stage_version)"
    ).fetchone()[0] or 0)
    return {
        "schema_version": 1,
        "source": "eocl_proof_cache_events_and_proofs",
        "eligible": eligible,
        "hits": hits,
        "misses": misses,
        "hit_rate": round(hits / eligible, 6) if eligible else None,
        "miss_reasons": miss_reasons,
        "fingerprint_classes": fingerprint_classes,
        "saved_ms": known_saved_ms if saved_complete else None,
        "saved_ms_known": known_saved_ms,
        "saved_ms_known_hits": known_saved_hits,
        "saved_ms_complete": saved_complete,
        "run_relation": {
            "runs_with_opportunities": int(overall[5] or 0),
            "accepted_runs_with_opportunities": int(overall[6] or 0),
            "accepted_checkpoint_runs_with_opportunities": int(overall[7] or 0),
            "accepted_run_opportunities": accepted_run_opportunities,
            "accepted_run_hits": int(overall[9] or 0),
            "unaccepted_run_opportunities": max(0, eligible - accepted_run_opportunities),
            "accepted_checkpoint_opportunities": accepted_checkpoint_opportunities,
            "accepted_checkpoint_hits": int(overall[11] or 0),
        },
        "evidence_window": {"first_event_at": overall[12], "last_event_at": overall[13]},
        "stages": stages,
        "stage_limit": bounded_stage_limit,
        "stage_rows_truncated": stage_group_count > bounded_stage_limit,
        "model_free": True,
        "content_free": True,
        "raw_input_fingerprints_included": False,
    }

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
        # Fingerprint metadata is already a bounded, caller-selected identity
        # contract.  Do not pass it through the audit-payload sanitizer: that
        # helper intentionally truncates lists and would make Python disagree
        # with the Electron activation verifier after 500 dirty entries.
        digest.update(_json(extra).encode("utf-8"))
    return digest.hexdigest()

class OrchestrationLedger(LifecycleReconciliationLedgerMixin, ObservationSpanLedgerMixin, P5ExperimentLedgerMixin, ProblemLineageLedgerMixin, QualityOutcomeLedgerMixin):
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
        with ledger_access_gate(self.path):
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
                CREATE INDEX IF NOT EXISTS idx_runs_status_started_run ON runs(status, started_at, run_id);
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
                CREATE INDEX IF NOT EXISTS idx_delegations_wave_started ON delegations(wave_id, started_at);
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
                CREATE INDEX IF NOT EXISTS idx_events_run_time_type ON events(run_id, event_time DESC, event_type);
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
                CREATE INDEX IF NOT EXISTS idx_proofs_run_finished ON proofs(run_id, finished_at, proof_id);
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
                CREATE INDEX IF NOT EXISTS idx_checkpoints_run_created ON checkpoints(run_id, created_at, checkpoint_id);
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
                CREATE INDEX IF NOT EXISTS idx_background_operations_run_status_updated ON background_operations(run_id, status, updated_at DESC);
                CREATE TABLE IF NOT EXISTS write_fences (
                    scope_key TEXT PRIMARY KEY,
                    fencing_token INTEGER NOT NULL DEFAULT 0,
                    lease_id TEXT NOT NULL DEFAULT '',
                    owner TEXT NOT NULL DEFAULT '',
                    run_id TEXT NOT NULL DEFAULT '',
                    wave_id TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'released',
                    expires_at REAL NOT NULL DEFAULT 0,
                    updated_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_write_fences_status
                    ON write_fences(status, expires_at);
                CREATE TABLE IF NOT EXISTS idempotency_records (
                    idempotency_key TEXT PRIMARY KEY,
                    operation TEXT NOT NULL,
                    request_hash TEXT NOT NULL,
                    status TEXT NOT NULL,
                    process_instance_id TEXT NOT NULL DEFAULT '',
                    run_id TEXT NOT NULL DEFAULT '',
                    wave_id TEXT NOT NULL DEFAULT '',
                    started_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    finished_at TEXT,
                    summary_json TEXT NOT NULL DEFAULT '{}',
                    error_code TEXT NOT NULL DEFAULT '',
                    workflow_patch_preflight INTEGER NOT NULL DEFAULT 0,
                    summary_codec TEXT NOT NULL DEFAULT 'plain_json',
                    summary_blob BLOB
                );
                CREATE INDEX IF NOT EXISTS idx_idempotency_records_status
                    ON idempotency_records(status, updated_at DESC);
                CREATE TABLE IF NOT EXISTS hub_clients (
                    client_id TEXT PRIMARY KEY,
                    client_type TEXT NOT NULL DEFAULT '',
                    role TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'online',
                    session_instance TEXT NOT NULL DEFAULT '',
                    runtime_instance_id TEXT NOT NULL DEFAULT '',
                    contract_sha TEXT NOT NULL DEFAULT '',
                    connected_at TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL,
                    capabilities_json TEXT NOT NULL DEFAULT '{}',
                    metadata_json TEXT NOT NULL DEFAULT '{}'
                );
                CREATE INDEX IF NOT EXISTS idx_hub_clients_status_seen
                    ON hub_clients(status, last_seen_at DESC);
                CREATE TABLE IF NOT EXISTS hub_client_cursors (
                    client_id TEXT NOT NULL REFERENCES hub_clients(client_id) ON DELETE CASCADE,
                    run_id TEXT NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
                    last_event_seq INTEGER NOT NULL DEFAULT 0,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY(client_id, run_id)
                );
                CREATE INDEX IF NOT EXISTS idx_hub_client_cursors_run
                    ON hub_client_cursors(run_id, last_event_seq DESC);
                CREATE TABLE IF NOT EXISTS controller_leases (
                    run_id TEXT PRIMARY KEY REFERENCES runs(run_id) ON DELETE CASCADE,
                    fencing_token INTEGER NOT NULL DEFAULT 0,
                    lease_id TEXT NOT NULL DEFAULT '',
                    owner_client_id TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'released',
                    expires_at REAL NOT NULL DEFAULT 0,
                    updated_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_controller_leases_status
                    ON controller_leases(status, expires_at);
                CREATE TABLE IF NOT EXISTS managed_process_jobs (
                    job_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL DEFAULT '',
                    wave_id TEXT NOT NULL DEFAULT '',
                    command_id TEXT NOT NULL UNIQUE,
                    owner TEXT NOT NULL DEFAULT '',
                    checkout_id TEXT NOT NULL,
                    resource_class TEXT NOT NULL,
                    root_pid INTEGER NOT NULL DEFAULT 0,
                    root_process_token TEXT NOT NULL DEFAULT '',
                    process_instance_id TEXT NOT NULL DEFAULT '',
                    runtime_instance_id TEXT NOT NULL DEFAULT '',
                    lifecycle_state TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    finished_at TEXT,
                    metadata_json TEXT NOT NULL DEFAULT '{}'
                );
                CREATE INDEX IF NOT EXISTS idx_managed_process_wave_state
                    ON managed_process_jobs(run_id, wave_id, lifecycle_state, updated_at DESC);
                CREATE INDEX IF NOT EXISTS idx_managed_process_checkout_state
                    ON managed_process_jobs(checkout_id, resource_class, lifecycle_state, updated_at DESC);
                DROP INDEX IF EXISTS idx_managed_process_one_heavy_checkout;
                CREATE TABLE IF NOT EXISTS checkout_resource_claims (
                    claim_id TEXT PRIMARY KEY,
                    checkout_id TEXT NOT NULL,
                    resource_class TEXT NOT NULL,
                    owner_type TEXT NOT NULL,
                    owner_id_hash TEXT NOT NULL,
                    lifecycle_state TEXT NOT NULL,
                    acquired_at TEXT NOT NULL,
                    expires_at REAL NOT NULL DEFAULT 0,
                    updated_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_checkout_resource_claim_state
                    ON checkout_resource_claims(checkout_id, lifecycle_state, updated_at DESC);
                CREATE UNIQUE INDEX IF NOT EXISTS idx_checkout_resource_one_active_heavy
                    ON checkout_resource_claims(checkout_id)
                    WHERE resource_class='HEAVY' AND lifecycle_state='active';
                """
            )
            self._p5_ensure_schema(connection)
            for column in ("error_code TEXT NOT NULL DEFAULT ''", "workflow_patch_preflight INTEGER NOT NULL DEFAULT 0", "summary_codec TEXT NOT NULL DEFAULT 'plain_json'", "summary_blob BLOB"):
                try:
                    connection.execute(f"ALTER TABLE idempotency_records ADD COLUMN {column}")
                except sqlite3.OperationalError as exc:
                    if "duplicate column name" not in str(exc).lower():
                        raise
            now = utc_now()
            active_jobs = connection.execute(
                """SELECT job_id,checkout_id FROM managed_process_jobs
                   WHERE resource_class='HEAVY'
                     AND lifecycle_state IN ('starting','running','terminating','orphaned')"""
            ).fetchall()
            for row in active_jobs:
                job_id = str(row["job_id"])
                claim_id = hashlib.sha256(
                    f"webcodex-managed-claim-v1\0{job_id}".encode("utf-8", errors="replace")
                ).hexdigest()
                connection.execute(
                    """INSERT OR IGNORE INTO checkout_resource_claims(
                           claim_id,checkout_id,resource_class,owner_type,owner_id_hash,
                           lifecycle_state,acquired_at,expires_at,updated_at
                       ) VALUES(?,?,?,?,?,'active',?,0,?)""",
                    (
                        claim_id,
                        str(row["checkout_id"]),
                        "HEAVY",
                        "MANAGED_JOB",
                        resource_claim_owner_hash("MANAGED_JOB", job_id),
                        now,
                        now,
                    ),
                )
            current_schema_version = int(connection.execute("PRAGMA user_version").fetchone()[0])
            # A later additive migration (for example PRL v10) must survive a
            # normal Runtime/ledger construction.  The v9 bootstrap remains
            # responsible only for databases at or below its own version; it
            # never decrements an already activated schema.
            if current_schema_version <= SCHEMA_VERSION:
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
        objective: str | None = None,
        objective_source: str = "",
        wave_id: str | None = None,
    ) -> str:
        wave_id = wave_id or uuid.uuid4().hex
        now = utc_now()
        with self._lock, self._connect() as connection:
            run_row = connection.execute("SELECT objective FROM runs WHERE run_id=?", (run_id,)).fetchone()
            if run_row is None:
                raise ValueError("wave run was not found")
            ordinal = int(connection.execute("SELECT COALESCE(MAX(ordinal),0)+1 FROM waves WHERE run_id=?", (run_id,)).fetchone()[0])
            previous_row = connection.execute(
                "SELECT metadata_json FROM waves WHERE run_id=? ORDER BY ordinal DESC LIMIT 1",
                (run_id,),
            ).fetchone()
            run_objective = _bounded_text(run_row["objective"], 4000)
            previous_metadata = json.loads(previous_row["metadata_json"] or "{}") if previous_row else {}
            previous_objective = _bounded_text(previous_metadata.get("effective_objective") or run_objective, 4000)
            effective_objective = _bounded_text(
                objective if objective is not None else (previous_objective if previous_row else run_objective),
                4000,
            )
            previous_revision_raw = previous_metadata.get("objective_revision", 1)
            previous_revision = (
                int(previous_revision_raw)
                if isinstance(previous_revision_raw, int) and not isinstance(previous_revision_raw, bool) and previous_revision_raw >= 1
                else 1
            )
            objective_changed = bool(previous_row and effective_objective != previous_objective)
            objective_revision = previous_revision + 1 if objective_changed else previous_revision
            source = _bounded_text(
                objective_source
                or ("previous_wave_inherited" if previous_row else "run_initial_objective"),
                100,
            )
            wave_metadata = dict(metadata or {})
            wave_metadata.update({
                "effective_objective": effective_objective,
                "objective_revision": objective_revision,
                "objective_sha256": hashlib.sha256(effective_objective.encode("utf-8", errors="replace")).hexdigest(),
                "objective_source": source,
                "objective_changed_from_previous": objective_changed,
            })
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
                    _json(_sanitize(wave_metadata)),
                ),
            )
        return wave_id

    def wave_objective_provenance(self, run_id: str, wave_id: str) -> dict[str, Any]:
        run = self.get_run(run_id) or {}
        wave = next((item for item in self.list_waves(run_id) if str(item.get("wave_id") or "") == wave_id), {})
        metadata = wave.get("metadata") if isinstance(wave.get("metadata"), dict) else {}
        run_objective = _bounded_text(run.get("objective") or "", 4000)
        explicit = bool(str(metadata.get("effective_objective") or "").strip())
        effective_objective = _bounded_text(metadata.get("effective_objective") or run_objective, 4000)
        revision_raw = metadata.get("objective_revision")
        revision = (
            int(revision_raw)
            if isinstance(revision_raw, int) and not isinstance(revision_raw, bool) and revision_raw >= 1
            else 1
        )
        stored_sha = str(metadata.get("objective_sha256") or "").strip().lower()
        calculated_sha = hashlib.sha256(effective_objective.encode("utf-8", errors="replace")).hexdigest()
        return {
            "effective_objective": effective_objective,
            "objective_revision": revision,
            "objective_sha256": stored_sha or calculated_sha,
            "objective_source": str(metadata.get("objective_source") or "legacy_run_objective"),
            "objective_changed_from_previous": bool(metadata.get("objective_changed_from_previous", False)),
            "objective_hash_valid": stored_sha == calculated_sha if stored_sha else None,
            "legacy_fallback": not explicit,
        }

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

    @staticmethod
    def _delegation_row(row: sqlite3.Row) -> dict[str, Any]:
        return {
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

    def get_delegation(self, delegation_id: str) -> dict[str, Any] | None:
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM delegations WHERE delegation_id=?",
                (_bounded_text(delegation_id, 256),),
            ).fetchone()
        return self._delegation_row(row) if row else None

    def upsert_external_delegation(
        self,
        *,
        delegation_id: str,
        wave_id: str,
        authority_owner: str,
        route_requested: str,
        route_resolved: str,
        model: str,
        status: str,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        """Idempotently project provider telemetry into one canonical delegation."""
        terminal_statuses = {"completed", "failed"}
        incoming_status = _bounded_text(status, 64).strip().lower()
        if incoming_status not in {"active", *terminal_statuses}:
            raise ValueError("invalid external delegation status")
        delegation = _bounded_text(delegation_id, 256).strip()
        wave = _bounded_text(wave_id, 256).strip()
        owner = _bounded_text(authority_owner, 200).strip()
        route_requested_value = _bounded_text(route_requested, 100)
        route_resolved_value = _bounded_text(route_resolved, 100)
        model_value = _bounded_text(model, 200)
        if not delegation or not wave or not owner or not model_value:
            raise ValueError("external delegation identity is incomplete")
        safe_metadata = _sanitize(metadata or {})
        now = utc_now()

        def merge_metadata(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
            merged = dict(existing)
            for key, value in incoming.items():
                if key == "message_economics" and isinstance(value, dict):
                    messages = dict(merged.get("message_economics") or {})
                    for raw_message_id, raw_metrics in value.items():
                        message_id = _bounded_text(raw_message_id, 256).strip()
                        if not message_id or not isinstance(raw_metrics, dict):
                            continue
                        if message_id not in messages and len(messages) >= _MAX_PROVIDER_MESSAGE_ECONOMICS:
                            continue
                        current = dict(messages.get(message_id) or {})
                        for metric, metric_value in raw_metrics.items():
                            if metric not in _PROVIDER_MESSAGE_NUMERIC_KEYS:
                                continue
                            if isinstance(metric_value, bool) or not isinstance(metric_value, (int, float)) or metric_value < 0:
                                continue
                            previous = current.get(metric)
                            current[metric] = max(previous, metric_value) if isinstance(previous, (int, float)) and not isinstance(previous, bool) else metric_value
                        messages[message_id] = current
                    merged["message_economics"] = messages
                    totals: dict[str, int | float] = {metric: 0 for metric in _PROVIDER_MESSAGE_NUMERIC_KEYS}
                    for metrics in messages.values():
                        if not isinstance(metrics, dict):
                            continue
                        for metric in _PROVIDER_MESSAGE_NUMERIC_KEYS:
                            measured = metrics.get(metric)
                            if isinstance(measured, (int, float)) and not isinstance(measured, bool) and measured >= 0:
                                totals[metric] += measured
                    merged["economics"] = {
                        "input_tokens": totals["input_tokens"],
                        "cached_input_tokens": totals["cached_input_tokens"],
                        "output_tokens": totals["output_tokens"],
                        "reasoning_output_tokens": totals["reasoning_output_tokens"],
                        "cache_read_tokens": totals["cache_read_tokens"],
                        "cache_write_tokens": totals["cache_write_tokens"],
                        "provider_cost": totals["provider_cost"],
                        "measured": True,
                        "source": "opencode",
                    }
                    merged["provider_message_duration_ms"] = totals["duration_ms"]
                elif key == "economics" and isinstance(value, dict):
                    economics = dict(merged.get("economics") or {})
                    for metric, metric_value in value.items():
                        if metric in _SAFE_NUMERIC_USAGE_KEYS or metric == "provider_cost":
                            if isinstance(metric_value, bool) or not isinstance(metric_value, (int, float)):
                                continue
                            previous = economics.get(metric)
                            economics[metric] = max(previous, metric_value) if isinstance(previous, (int, float)) and not isinstance(previous, bool) else metric_value
                        elif metric_value not in {None, ""}:
                            economics[metric] = metric_value
                    merged[key] = economics
                elif key == "provider_started_at_ms" and isinstance(value, (int, float)) and not isinstance(value, bool):
                    previous = merged.get(key)
                    merged[key] = min(previous, value) if isinstance(previous, (int, float)) and previous > 0 else value
                elif key in {"provider_completed_at_ms", "duration_ms", "provider_cost"} and isinstance(value, (int, float)) and not isinstance(value, bool):
                    previous = merged.get(key)
                    merged[key] = max(previous, value) if isinstance(previous, (int, float)) else value
                elif value is not None and value != "":
                    merged[key] = value
            return merged

        with self._lock, self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT * FROM delegations WHERE delegation_id=?", (delegation,)).fetchone()
            if row:
                if str(row["wave_id"]) != wave:
                    raise ValueError("external delegation cannot move between orchestration waves")
                if str(row["authority_owner"]) != owner:
                    raise ValueError("external delegation authority changed")
                if str(row["model"]) and str(row["model"]) != model_value:
                    raise ValueError("external delegation model changed")
                current_status = str(row["status"] or "active").lower()
                if current_status in terminal_statuses and incoming_status != current_status:
                    connection.commit()
                    return {"created": False, "changed": False, "terminal_transition": False, "delegation": self._delegation_row(row)}
                merged_metadata = merge_metadata(json.loads(row["metadata_json"] or "{}"), safe_metadata)
                next_status = current_status if current_status in terminal_statuses else incoming_status
                terminal_transition = current_status not in terminal_statuses and next_status in terminal_statuses
                finished_at = row["finished_at"] or (now if terminal_transition else None)
                metadata_json = _json(merged_metadata)
                changed = next_status != current_status or metadata_json != str(row["metadata_json"] or "{}")
                if changed:
                    connection.execute(
                        "UPDATE delegations SET status=?, finished_at=?, metadata_json=? WHERE delegation_id=?",
                        (next_status, finished_at, metadata_json, delegation),
                    )
                updated = connection.execute("SELECT * FROM delegations WHERE delegation_id=?", (delegation,)).fetchone()
                connection.commit()
                assert updated is not None
                return {"created": False, "changed": changed, "terminal_transition": terminal_transition, "delegation": self._delegation_row(updated)}

            terminal = incoming_status in terminal_statuses
            initial_metadata = merge_metadata({}, safe_metadata)
            connection.execute(
                """INSERT INTO delegations(
                    delegation_id,wave_id,parent_delegation_id,authority_owner,route_requested,route_resolved,
                    model,effort,allowed_scope_json,status,started_at,finished_at,metadata_json
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (delegation, wave, None, owner, route_requested_value, route_resolved_value, model_value, "", "[]", incoming_status, now, now if terminal else None, _json(initial_metadata)),
            )
            created = connection.execute("SELECT * FROM delegations WHERE delegation_id=?", (delegation,)).fetchone()
            connection.commit()
            assert created is not None
            return {"created": True, "changed": True, "terminal_transition": terminal, "delegation": self._delegation_row(created)}

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
        with self._lock, self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            event = append_hash_chained_event(
                connection,
                run_id=run_id,
                event_type=event_type,
                wave_id=wave_id,
                delegation_id=delegation_id,
                state_before=state_before,
                state_after=state_after,
                payload=payload,
                event_time=event_time or utc_now(),
                sanitize=_sanitize,
                serialize=_json,
                bounded_text=_bounded_text,
            )
        return event
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

    def live_run_projection(
        self,
        run_id: str,
        *,
        wave_limit: int = 3,
        event_limit: int = 15,
        proof_limit: int = 6,
        delegation_limit: int = 4,
    ) -> dict[str, Any]:
        """Return only the bounded run facts needed by frequent UI polling."""
        run_key = _bounded_text(run_id, 256)
        waves_limit = max(1, min(int(wave_limit), 20))
        events_limit = max(1, min(int(event_limit), 100))
        proofs_limit = max(1, min(int(proof_limit), 50))
        delegations_limit = max(1, min(int(delegation_limit), 50))
        with self._lock, self._connect() as connection:
            wave_rows = connection.execute(
                "SELECT * FROM waves WHERE run_id=? ORDER BY ordinal DESC LIMIT ?",
                (run_key, waves_limit),
            ).fetchall()
            event_rows = connection.execute(
                "SELECT * FROM events WHERE run_id=? ORDER BY seq DESC LIMIT ?",
                (run_key, events_limit),
            ).fetchall()
            proof_rows = connection.execute(
                "SELECT * FROM proofs WHERE run_id=? ORDER BY finished_at DESC,proof_id DESC LIMIT ?",
                (run_key, proofs_limit),
            ).fetchall()
            delegation_rows = connection.execute(
                """SELECT d.* FROM delegations d
                   JOIN waves w ON w.wave_id=d.wave_id
                   WHERE w.run_id=?
                   ORDER BY d.started_at DESC,d.delegation_id DESC LIMIT ?""",
                (run_key, delegations_limit),
            ).fetchall()
            counts = connection.execute(
                """SELECT
                       (SELECT COUNT(*) FROM events WHERE run_id=?),
                       (SELECT COUNT(*) FROM waves WHERE run_id=?),
                       (SELECT COUNT(*) FROM checkpoints WHERE run_id=?)""",
                (run_key, run_key, run_key),
            ).fetchone()
            latest_material = connection.execute(
                """SELECT event_time FROM events
                   WHERE run_id=?
                     AND event_type NOT IN ('controller_transferred','write_lease_renewed')
                   ORDER BY event_time DESC LIMIT 1""",
                (run_key,),
            ).fetchone()
        return {
            "waves": [
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
                for row in reversed(wave_rows)
            ],
            "events": [self._event_row(row) for row in reversed(event_rows)],
            "proofs": [self._proof_row(row) for row in reversed(proof_rows)],
            "delegations": [self._delegation_row(row) for row in reversed(delegation_rows)],
            "counts": {
                "events": int(counts[0] or 0) if counts else 0,
                "waves": int(counts[1] or 0) if counts else 0,
                "checkpoints": int(counts[2] or 0) if counts else 0,
            },
            "latest_material_event_at": str(latest_material[0] or "") if latest_material else "",
        }

    def record_usage_event(
        self,
        *,
        run_id: str,
        wave_id: str,
        delegation_id: str,
        usage_event: dict[str, Any],
    ) -> dict[str, Any]:
        return _record_usage_event(
            self,
            run_id=run_id,
            wave_id=wave_id,
            delegation_id=delegation_id,
            usage_event=_sanitize(usage_event),
        )

    def list_usage_events(self, run_id: str, *, limit: int | None = 100) -> list[dict[str, Any]]:
        return _list_usage_events(self, run_id, limit=limit)

    def recent_usage_events(self, *, limit: int = 8) -> list[dict[str, Any]]:
        return _recent_usage_events(self, limit=limit)

    def usage_analytics(self, *, days: int = 7, now: str | None = None) -> dict[str, Any]:
        return _usage_analytics(self, days=days, now=now)

    def record_shadow_route(
        self,
        *,
        run_id: str,
        wave_id: str,
        recommendation: dict[str, Any],
    ) -> dict[str, Any]:
        recommendation_id = _bounded_text(recommendation.get("recommendation_id"), 256).strip()
        if not recommendation_id:
            raise ValueError("recommendation_id is required")
        with self._lock:
            with self._connect() as connection:
                rows = connection.execute(
                    "SELECT event_id,payload_json FROM events WHERE run_id=? AND event_type='shadow_route_recommended' ORDER BY seq",
                    (_bounded_text(run_id, 256),),
                ).fetchall()
            for row in rows:
                payload = json.loads(row["payload_json"] or "{}")
                if str(payload.get("recommendation_id") or "") == recommendation_id:
                    return {"recorded": False, "event_id": row["event_id"], "recommendation_id": recommendation_id}
            event_id = self.append_event(
                run_id,
                wave_id=wave_id,
                event_type="shadow_route_recommended",
                payload=recommendation,
            )
            return {"recorded": True, "event_id": event_id, "recommendation_id": recommendation_id}

    def list_shadow_routes(self, run_id: str, *, limit: int = 50) -> list[dict[str, Any]]:
        bounded_limit = max(1, min(int(limit), 200))
        with self._lock, self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM events WHERE run_id=? AND event_type='shadow_route_recommended' ORDER BY seq DESC LIMIT ?",
                (_bounded_text(run_id, 256), bounded_limit),
            ).fetchall()
        events = [self._event_row(row) for row in reversed(rows)]
        return [
            {**(item.get("payload") or {}), "seq": item["seq"], "event_time": item["event_time"]}
            for item in events
        ]

    @staticmethod
    def _route_task_class(run: dict[str, Any] | None) -> str:
        metadata = run.get("metadata") if isinstance(run, dict) and isinstance(run.get("metadata"), dict) else {}
        evaluation = metadata.get("evaluation") if isinstance(metadata.get("evaluation"), dict) else {}
        return _bounded_text(evaluation.get("task_class") or metadata.get("task_class") or metadata.get("workflow") or "", 100).lower()

    @staticmethod
    def _nearest_rank(values: list[int], percentile: int) -> int | None:
        if not values:
            return None
        ordered = sorted(max(0, int(value)) for value in values)
        rank = max(1, min(len(ordered), (len(ordered) * max(1, min(percentile, 100)) + 99) // 100))
        return ordered[rank - 1]

    def similar_accepted_route_cohorts(self, run_id: str, *, limit: int = 24) -> dict[str, Any]:
        """Summarize accepted results from the same durable task class without prompts/transcripts."""
        current = self.get_run(run_id)
        task_class = self._route_task_class(current)
        bounded_limit = max(1, min(int(limit), 50))
        if not task_class:
            return {
                "schema_version": 1,
                "task_class": None,
                "sampled_runs": 0,
                "cohorts": [],
                "status": "insufficient_task_class",
                "model_free": True,
                "content_free": True,
            }

        matching = [
            run for run in self.list_runs(limit=100, status="accepted")
            if run.get("run_id") != run_id and self._route_task_class(run) == task_class
        ][:bounded_limit]
        groups: dict[str, dict[str, Any]] = {}
        for run in matching:
            economics = self.accepted_result_economics(str(run["run_id"]))
            route = economics.get("route") if isinstance(economics.get("route"), dict) else {}
            resolved = _bounded_text(route.get("resolved") or "unknown", 100) or "unknown"
            group = groups.setdefault(resolved, {
                "route": resolved,
                "accepted_results": 0,
                "first_pass_accepted": 0,
                "repaired_results": 0,
                "tta_samples_ms": [],
                "provider_cost_complete_samples": 0,
                "provider_cost_total": 0.0,
                "candidate_credit_samples": 0,
                "candidate_credits_total": 0.0,
            })
            group["accepted_results"] += 1
            if economics.get("first_pass_accepted") is True:
                group["first_pass_accepted"] += 1
            else:
                group["repaired_results"] += 1
            tta = economics.get("tta_ms")
            if isinstance(tta, (int, float)) and not isinstance(tta, bool) and tta >= 0:
                group["tta_samples_ms"].append(int(tta))
            provider = economics.get("provider_economics") if isinstance(economics.get("provider_economics"), dict) else {}
            provider_cost = provider.get("provider_cost")
            if provider.get("cost_complete") is True and isinstance(provider_cost, (int, float)) and not isinstance(provider_cost, bool) and provider_cost >= 0:
                group["provider_cost_complete_samples"] += 1
                group["provider_cost_total"] += float(provider_cost)
            candidate = economics.get("candidate_economics") if isinstance(economics.get("candidate_economics"), dict) else {}
            credits = candidate.get("estimated_credits")
            if isinstance(credits, (int, float)) and not isinstance(credits, bool) and credits >= 0:
                group["candidate_credit_samples"] += 1
                group["candidate_credits_total"] += float(credits)

        cohorts: list[dict[str, Any]] = []
        for route, group in groups.items():
            accepted_count = int(group["accepted_results"])
            tta_samples = list(group.pop("tta_samples_ms"))
            provider_samples = int(group["provider_cost_complete_samples"])
            candidate_samples = int(group["candidate_credit_samples"])
            cohorts.append({
                "route": route,
                "accepted_results": accepted_count,
                "first_pass_accepted": int(group["first_pass_accepted"]),
                "first_pass_rate": round(int(group["first_pass_accepted"]) / accepted_count, 6) if accepted_count else None,
                "repaired_results": int(group["repaired_results"]),
                "tta": {
                    "samples": len(tta_samples),
                    "p50_ms": self._nearest_rank(tta_samples, 50),
                    "p90_ms": self._nearest_rank(tta_samples, 90),
                    "method": "nearest_rank",
                },
                "provider_cost": {
                    "complete_samples": provider_samples,
                    "total": round(float(group["provider_cost_total"]), 9) if provider_samples else None,
                    "measurement": "measured_complete_only" if provider_samples else "unobserved",
                },
                "candidate_credits": {
                    "samples": candidate_samples,
                    "total": round(float(group["candidate_credits_total"]), 6) if candidate_samples else None,
                    "measurement": "estimated" if candidate_samples else "unobserved",
                },
            })
        cohorts.sort(key=lambda item: (-int(item["accepted_results"]), str(item["route"])))
        return {
            "schema_version": 1,
            "task_class": task_class,
            "sampled_runs": len(matching),
            "cohorts": cohorts,
            "status": "observed" if matching else "no_matching_accepted_runs",
            "model_free": True,
            "content_free": True,
        }

    @staticmethod
    def _promotion_sample_provenance(run: dict[str, Any]) -> str:
        metadata = run.get("metadata") if isinstance(run.get("metadata"), dict) else {}
        evaluation = metadata.get("evaluation") if isinstance(metadata.get("evaluation"), dict) else {}
        explicit = _bounded_text(
            evaluation.get("provenance") or metadata.get("promotion_provenance") or metadata.get("evidence_provenance") or "",
            80,
        ).strip().lower()
        if explicit in {"representative", "representative_project_task", "organic_representative"}:
            return "representative"
        if explicit in {"benchmark", "synthetic", "fixture", "non_representative"}:
            return "benchmark_or_synthetic"
        objective = _bounded_text(run.get("objective") or "", 2000).lower()
        synthetic_markers = (
            "execution-hub-benchmark",
            "benchmark fixture",
            "benchmark only",
            "paired benchmark",
            "synthetic no-op",
            "synthetic noop",
            "not production source",
        )
        if any(marker in objective for marker in synthetic_markers):
            return "benchmark_or_synthetic"
        return "unverified"

    def routing_promotion_readiness(self, *, limit: int = 100) -> dict[str, Any]:
        """Project fail-closed promotion evidence without granting routing authority."""
        bounded_limit = max(1, min(int(limit), 100))
        groups: dict[str, dict[str, Any]] = {}
        for run in self.list_runs(limit=bounded_limit, status="accepted"):
            economics = self.accepted_result_economics(str(run["run_id"]))
            route = economics.get("route") if isinstance(economics.get("route"), dict) else {}
            resolved = _bounded_text(route.get("resolved") or "unknown", 100) or "unknown"
            if resolved in {"unknown", "deterministic", "mcp_deterministic", "controller_manual"}:
                continue
            provenance = self._promotion_sample_provenance(run)
            group = groups.setdefault(resolved, {
                "route": resolved,
                "accepted_observed": 0,
                "representative_accepted": 0,
                "benchmark_or_synthetic_excluded": 0,
                "unverified_provenance": 0,
                "task_classes": set(),
                "first_pass_representative": 0,
                "repaired_representative": 0,
                "tta_representative_samples": 0,
                "provider_cost_complete_samples": 0,
                "candidate_credit_samples": 0,
                "critical_defect_known_zero_samples": 0,
                "critical_defect_nonzero_samples": 0,
                "critical_defect_unknown_samples": 0,
                "proof_or_oracle_complete_samples": 0,
            })
            group["accepted_observed"] += 1
            if provenance == "benchmark_or_synthetic":
                group["benchmark_or_synthetic_excluded"] += 1
                continue
            if provenance != "representative":
                group["unverified_provenance"] += 1
                continue
            group["representative_accepted"] += 1
            task_class = self._route_task_class(run)
            if task_class:
                group["task_classes"].add(task_class)
            if economics.get("first_pass_accepted") is True:
                group["first_pass_representative"] += 1
            else:
                group["repaired_representative"] += 1
            if isinstance(economics.get("tta_ms"), (int, float)) and not isinstance(economics.get("tta_ms"), bool):
                group["tta_representative_samples"] += 1
            provider = economics.get("provider_economics") if isinstance(economics.get("provider_economics"), dict) else {}
            if provider.get("cost_complete") is True:
                group["provider_cost_complete_samples"] += 1
            candidate = economics.get("candidate_economics") if isinstance(economics.get("candidate_economics"), dict) else {}
            if isinstance(candidate.get("estimated_credits"), (int, float)) and not isinstance(candidate.get("estimated_credits"), bool):
                group["candidate_credit_samples"] += 1
            defects = economics.get("critical_defects") if isinstance(economics.get("critical_defects"), dict) else {}
            if defects.get("status") == "known" and defects.get("count") == 0:
                group["critical_defect_known_zero_samples"] += 1
            elif defects.get("status") == "known" and isinstance(defects.get("count"), int) and defects.get("count") > 0:
                group["critical_defect_nonzero_samples"] += 1
            else:
                group["critical_defect_unknown_samples"] += 1
            proof = economics.get("proof") if isinstance(economics.get("proof"), dict) else {}
            quality = economics.get("quality_outcome") if isinstance(economics.get("quality_outcome"), dict) else {}
            if int(proof.get("passed") or 0) > 0 or (quality.get("oracle_pass") is True and bool(str(quality.get("source") or "").strip())):
                group["proof_or_oracle_complete_samples"] += 1

        routes: list[dict[str, Any]] = []
        for resolved, group in groups.items():
            representative = int(group["representative_accepted"])
            task_classes = sorted(str(item) for item in group["task_classes"])
            reasons: list[str] = []
            if representative < 10:
                reasons.append("insufficient_representative_accepted_results")
            if len(task_classes) < 3:
                reasons.append("insufficient_task_class_diversity")
            if int(group["unverified_provenance"]) > 0:
                reasons.append("unverified_provenance_excluded")
            if int(group["critical_defect_nonzero_samples"]) > 0:
                reasons.append("critical_defect_observed")
            elif representative and int(group["critical_defect_known_zero_samples"]) < representative:
                reasons.append("critical_defect_evidence_incomplete")
            if representative and int(group["proof_or_oracle_complete_samples"]) < representative:
                reasons.append("proof_or_oracle_evidence_incomplete")
            if representative and int(group["tta_representative_samples"]) < representative:
                reasons.append("tta_evidence_incomplete")
            routes.append({
                "route": resolved,
                "status": "eligible_for_manual_review" if not reasons else "hold",
                "hold_reasons": reasons,
                "accepted_observed": int(group["accepted_observed"]),
                "representative_accepted": representative,
                "benchmark_or_synthetic_excluded": int(group["benchmark_or_synthetic_excluded"]),
                "unverified_provenance": int(group["unverified_provenance"]),
                "task_classes": task_classes,
                "task_class_count": len(task_classes),
                "first_pass_representative": int(group["first_pass_representative"]),
                "repaired_representative": int(group["repaired_representative"]),
                "tta_representative_samples": int(group["tta_representative_samples"]),
                "provider_cost_complete_samples": int(group["provider_cost_complete_samples"]),
                "candidate_credit_samples": int(group["candidate_credit_samples"]),
                "critical_defect_known_zero_samples": int(group["critical_defect_known_zero_samples"]),
                "critical_defect_nonzero_samples": int(group["critical_defect_nonzero_samples"]),
                "critical_defect_unknown_samples": int(group["critical_defect_unknown_samples"]),
                "proof_or_oracle_complete_samples": int(group["proof_or_oracle_complete_samples"]),
            })
        routes.sort(key=lambda item: str(item["route"]))
        return {
            "schema_version": 1,
            "policy": "candidate_v1_advisory",
            "policy_status": "advisory_not_activation_authority",
            "thresholds": {"min_representative_accepted_results": 10, "min_task_classes": 3},
            "provenance": {
                "representative_requires_explicit_metadata": True,
                "known_benchmark_or_synthetic_is_excluded": True,
                "unverified_is_excluded": True,
            },
            "routes": routes,
            "automatic_activation": False,
            "model_free": True,
            "content_free": True,
        }

    def warm_thread_health(self, run_id: str) -> dict[str, Any]:
        lanes = self.list_agent_lanes(run_id=run_id)
        lifecycle_counts: dict[str, int] = {}
        reusable_lane_ids: list[str] = []
        for lane in lanes:
            lifecycle = _bounded_text(lane.get("lifecycle") or "unknown", 64) or "unknown"
            lifecycle_counts[lifecycle] = lifecycle_counts.get(lifecycle, 0) + 1
            has_thread = bool(str(lane.get("thread_id") or lane.get("session_id") or "").strip())
            if lifecycle in {"active", "idle"} and has_thread:
                reusable_lane_ids.append(str(lane.get("lane_id") or "")[:256])
        return {
            "measurement": "durable_lane_state",
            "lane_count": len(lanes),
            "lifecycle_counts": lifecycle_counts,
            "reusable_lane_count": len(reusable_lane_ids),
            "reusable_lane_ids": reusable_lane_ids[:20],
            "automatic_reuse": False,
            "model_free": True,
            "content_free": True,
        }

    def routing_evidence(self, run_id: str, *, limit: int = 8) -> dict[str, Any]:
        bounded_limit = max(1, min(int(limit), 50))
        actual_delegations: list[dict[str, Any]] = []
        for wave in self.list_waves(run_id):
            actual_delegations.extend(self.list_delegations(str(wave["wave_id"])))
        return {
            "shadow_recommendations": self.list_shadow_routes(run_id, limit=bounded_limit),
            "actual_delegations": actual_delegations[-bounded_limit:],
            "usage_events": self.list_usage_events(run_id, limit=bounded_limit),
            "accepted_result": self.accepted_result_economics(run_id),
            "similar_accepted_cohorts": self.similar_accepted_route_cohorts(run_id, limit=max(8, bounded_limit * 3)),
            "promotion_readiness": self.routing_promotion_readiness(),
            "warm_thread_health": self.warm_thread_health(run_id),
        }

    def accepted_result_economics(self, run_id: str) -> dict[str, Any]:
        """Project durable evidence for cost/time per accepted result.

        Provider-reported monetary cost and Codex rate-card credit estimates are
        intentionally separate channels. Missing measurements remain unknown;
        this projection never turns absent telemetry into zero cost or a router
        promotion signal.
        """
        run = self.get_run(run_id)
        if run is None:
            return {
                "schema_version": 1,
                "run_id": run_id,
                "status": "missing",
                "accepted": False,
                "first_pass_accepted": False,
                "tta_ms": None,
                "route": {"resolved": "unknown", "model": None, "effort": None, "profile": None},
                "repair": {"replan_count": 0, "failure_event_count": 0},
                "proof": {"records": 0, "passed": 0, "failed": 0},
                "phase_timing": {
                    "source": "eocl_event_timestamps",
                    "complete": False,
                    "tta_ms": None,
                    "observed_ms": 0,
                    "unattributed_ms": None,
                    "tta_coverage": None,
                    "coverage_floor": 0.90,
                    "coverage_target": 0.95,
                    "meets_coverage_floor": False,
                    "meets_coverage_target": False,
                    "by_state_ms": {},
                    "methodology_phase_ms": {},
                },
                "provider_economics": {
                    "usage_event_count": 0,
                    "cost_measured_event_count": 0,
                    "cost_complete": False,
                    "provider_cost": None,
                    "attribution_complete": False,
                    "attributed_provider_cost": None,
                    "attribution_sources": [],
                    "usage": {},
                    "timing": {
                        "measurement": "unobserved",
                        "overlaps_eocl_windows": True,
                        "components_ms": {"queue_ms": None, "provider_ms": None, "total_ms": None},
                        "sample_counts": {"queue_ms": 0, "provider_ms": 0, "total_ms": 0},
                    },
                },
                "candidate_economics": {"observations": 0, "estimated_credits": None, "pricing_bases": []},
                "critical_defects": {"status": "unknown", "count": None, "source": "not_recorded"},
            }

        waves = self.list_waves(run_id)
        events = self.list_events(run_id)
        proofs = self.list_proofs(run_id)
        checkpoints = self.list_checkpoints(run_id)
        delegations: list[dict[str, Any]] = []
        for wave in waves:
            delegations.extend(self.list_delegations(str(wave["wave_id"])))

        latest_route: dict[str, Any] = {}
        failure_event_count = 0
        for event in events:
            payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
            if event.get("event_type") == "route_selected":
                latest_route = dict(payload)
            elif event.get("event_type") == "failure_observed":
                failure_event_count += 1

        replans = sum(1 for wave in waves if str(wave.get("status") or "") == "replanned")
        accepted = str(run.get("status") or "") == "accepted"
        phase_timing = self.run_phase_timing(run_id)
        tta_ms = phase_timing.get("tta_ms")
        observed_phase_ms = max(0, int(phase_timing.get("observed_ms") or 0))
        tta_coverage = phase_timing.get("tta_coverage")

        quality_outcome = self.latest_quality_outcome(run_id)
        usage_events = [
            item
            for item in self.list_usage_events(run_id, limit=None)
            if str(item.get("actor") or "provider").strip().lower() != "controller"
        ]
        legacy_usage_keys = (
            "input_tokens",
            "cached_input_tokens",
            "uncached_input_tokens",
            "output_tokens",
            "reasoning_output_tokens",
            "cache_read_tokens",
            "cache_write_tokens",
        )
        usage_totals = {key: 0 for key in (*legacy_usage_keys, *CANONICAL_USAGE_KEYS)}
        measured_costs: list[float] = []
        attribution_sources: set[str] = set()
        provider_models: set[str] = set()
        provider_ids: set[str] = set()
        for usage_event in usage_events:
            usage = usage_event.get("usage") if isinstance(usage_event.get("usage"), dict) else {}
            for key in legacy_usage_keys:
                value = usage.get(key)
                if isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0:
                    usage_totals[key] += int(value)
            try:
                canonical = canonical_usage_payload(usage_event)
            except ValueError:
                canonical = {}
            for key in CANONICAL_USAGE_KEYS:
                value = canonical.get(key)
                if isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0:
                    usage_totals[key] += int(value)
            measurement = usage_event.get("measurement") if isinstance(usage_event.get("measurement"), dict) else {}
            provenance = usage_event.get("provenance") if isinstance(usage_event.get("provenance"), dict) else {}
            source = str(provenance.get("source") or "").strip()
            if source:
                attribution_sources.add(source)
            cost = usage_event.get("cost") if isinstance(usage_event.get("cost"), dict) else {}
            provider_cost = cost.get("provider_cost")
            if measurement.get("cost") == "measured" and isinstance(provider_cost, (int, float)) and not isinstance(provider_cost, bool) and provider_cost >= 0:
                measured_costs.append(float(provider_cost))
            provider_id = str(usage_event.get("provider_id") or "").strip()
            model = str(usage_event.get("model") or usage_event.get("model_id") or "").strip()
            if provider_id:
                provider_ids.add(provider_id)
            if model:
                provider_models.add(model)
        cost_complete = bool(usage_events) and len(measured_costs) == len(usage_events)
        attribution_complete = bool(usage_events) and all(
            str((item.get("provenance") or {}).get("source") or "").strip() == "opencode:provider_dispatch"
            for item in usage_events
            if isinstance(item, dict)
        )

        provider_timing_values: dict[str, list[int]] = {"queue_ms": [], "provider_ms": [], "total_ms": []}
        for delegation in delegations:
            metadata = delegation.get("metadata") if isinstance(delegation.get("metadata"), dict) else {}
            timing = metadata.get("timing") if isinstance(metadata.get("timing"), dict) else {}
            for key in provider_timing_values:
                value = timing.get(key)
                if isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0:
                    provider_timing_values[key].append(int(value))
        provider_timing_components = {
            key: sum(values) if values else None
            for key, values in provider_timing_values.items()
        }
        provider_timing_samples = {key: len(values) for key, values in provider_timing_values.items()}
        provider_timing_observed = any(provider_timing_samples.values())

        estimated_credits: list[float] = []
        pricing_bases: set[str] = set()
        candidate_models: set[str] = set()
        for delegation in delegations:
            metadata = delegation.get("metadata") if isinstance(delegation.get("metadata"), dict) else {}
            economics = metadata.get("economics") if isinstance(metadata.get("economics"), dict) else {}
            estimate = economics.get("estimated_credits")
            if isinstance(estimate, (int, float)) and not isinstance(estimate, bool) and estimate >= 0:
                estimated_credits.append(float(estimate))
                model = str(delegation.get("model") or economics.get("model") or "").strip()
                if model:
                    candidate_models.add(model)
                pricing_basis = str(economics.get("pricing_basis") or "").strip()
                if pricing_basis:
                    pricing_bases.add(pricing_basis)

        proof_passed = sum(1 for proof in proofs if str(proof.get("status") or "") == "passed")
        proof_failed = len(proofs) - proof_passed
        accepted_checkpoints = sum(1 for checkpoint in checkpoints if str(checkpoint.get("status") or "") == "accepted")
        critical_count = quality_outcome.get("critical_defect_count") if isinstance(quality_outcome, dict) else None
        critical_defects = (
            {"status": "known", "count": int(critical_count), "source": str(quality_outcome.get("source") or "quality_outcome_recorded")}
            if isinstance(critical_count, int) and not isinstance(critical_count, bool) and critical_count >= 0
            else {"status": "unknown", "count": None, "source": "not_recorded"}
        )

        return {
            "schema_version": 1,
            "run_id": run_id,
            "status": str(run.get("status") or ""),
            "accepted": accepted,
            "first_pass_accepted": bool(accepted and replans == 0),
            "tta_ms": tta_ms,
            "route": {
                "resolved": str(latest_route.get("resolved") or "unknown"),
                "model": latest_route.get("model"),
                "effort": latest_route.get("effort"),
                "profile": latest_route.get("profile"),
            },
            "repair": {"replan_count": replans, "failure_event_count": failure_event_count},
            "proof": {
                "records": len(proofs),
                "passed": proof_passed,
                "failed": proof_failed,
                "accepted_checkpoint_count": accepted_checkpoints,
            },
            "phase_timing": {
                "source": phase_timing.get("source"),
                "complete": bool(phase_timing.get("complete")),
                "tta_ms": tta_ms,
                "observed_ms": observed_phase_ms,
                "unattributed_ms": phase_timing.get("unattributed_ms"),
                "tta_coverage": tta_coverage,
                "coverage_floor": phase_timing.get("coverage_floor"),
                "coverage_target": phase_timing.get("coverage_target"),
                "meets_coverage_floor": bool(phase_timing.get("meets_coverage_floor")),
                "meets_coverage_target": bool(phase_timing.get("meets_coverage_target")),
                "by_state_ms": dict(phase_timing.get("by_state_ms") or {}),
                "methodology_phase_ms": dict(phase_timing.get("methodology_phase_ms") or {}),
            },
            "provider_economics": {
                "usage_event_count": len(usage_events),
                "cost_measured_event_count": len(measured_costs),
                "cost_complete": cost_complete,
                "provider_cost": round(sum(measured_costs), 12) if cost_complete else None,
                "attribution_complete": attribution_complete,
                "attributed_provider_cost": round(sum(measured_costs), 12) if cost_complete and attribution_complete else None,
                "attribution_sources": sorted(attribution_sources),
                "usage": usage_totals,
                "providers": sorted(provider_ids),
                "models": sorted(provider_models),
                "measurement": "provider_reported" if usage_events else "unobserved",
                "timing": {
                    "measurement": "delegation_metadata" if provider_timing_observed else "unobserved",
                    "overlaps_eocl_windows": True,
                    "components_ms": provider_timing_components,
                    "sample_counts": provider_timing_samples,
                },
            },
            "candidate_economics": {
                "observations": len(estimated_credits),
                "estimated_credits": round(sum(estimated_credits), 6) if estimated_credits else None,
                "pricing_bases": sorted(pricing_bases),
                "models": sorted(candidate_models),
                "measurement": "estimated_rate_card" if estimated_credits else "unobserved",
            },
            "quality_outcome": dict(quality_outcome or {}),
            "critical_defects": critical_defects,
        }

    def accepted_result_evaluation(self, run_id: str) -> dict[str, Any]:
        """Return one normalized task/run row for accepted-result economics.

        The MCP cannot observe ChatWeb time or token/cost usage before the first MCP
        call unless a trusted client explicitly reports it in ``metadata.evaluation``.
        Missing controller telemetry therefore remains ``None`` rather than becoming
        zero. This projection is content-free and derived from durable ledger facts.
        """
        run = self.get_run(run_id)
        economics = self.accepted_result_economics(run_id)
        if run is None:
            return {
                "schema_version": 1,
                "run_id": run_id,
                "status": "missing",
                "accepted": False,
                "pairing_eligible": False,
                "controller": {"measurement": "unobserved_outside_mcp", "pre_mcp_ms": None, "monetary_cost": None, "usage": {}},
                "total_monetary_cost": {"value": None, "complete": False, "reason": "controller_cost_unobserved"},
            }

        metadata = run.get("metadata") if isinstance(run.get("metadata"), dict) else {}
        evaluation = metadata.get("evaluation") if isinstance(metadata.get("evaluation"), dict) else {}
        controller = evaluation.get("controller") if isinstance(evaluation.get("controller"), dict) else {}
        waves = self.list_waves(run_id)
        events = self.list_events(run_id)
        proofs = self.list_proofs(run_id)
        checkpoints = self.list_checkpoints(run_id)
        first_wave = waves[0] if waves else {}
        run_started_at = str(run.get("started_at") or "") or None
        run_started_ms = self._timestamp_millis(run_started_at)

        def first_event_time(event_types: set[str]) -> str | None:
            for event in events:
                if str(event.get("event_type") or "") in event_types:
                    value = str(event.get("event_time") or "")
                    if value:
                        return value
            return None

        def elapsed_from_start(value: str | None) -> int | None:
            value_ms = self._timestamp_millis(value)
            if run_started_ms is None or value_ms is None:
                return None
            return max(0, int(value_ms - run_started_ms))

        first_route_at = first_event_time({"route_selected"})
        first_external_dispatch_at = first_event_time({"delegation_started", "external_delegation_started", "model_dispatch_started"})
        first_write_at = first_event_time({"write_lease_acquired"})
        passed_proofs = [item for item in proofs if str(item.get("status") or "") == "passed" and str(item.get("finished_at") or "")]
        first_green_at = str(passed_proofs[0].get("finished_at") or "") if passed_proofs else None
        accepted_checkpoints = [item for item in checkpoints if str(item.get("status") or "") == "accepted"]
        accepted_at = (
            str(accepted_checkpoints[0].get("created_at") or "")
            if accepted_checkpoints
            else (str(run.get("finished_at") or "") if economics.get("accepted") else None)
        )

        controller_started_at = str(controller.get("started_at") or "") or None
        controller_started_ms = self._timestamp_millis(controller_started_at)
        pre_mcp_ms = (
            max(0, int(run_started_ms - controller_started_ms))
            if run_started_ms is not None and controller_started_ms is not None and run_started_ms >= controller_started_ms
            else None
        )
        controller_usage: dict[str, int | None] = {}
        for key in ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens"):
            value = controller.get(key)
            controller_usage[key] = int(value) if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None
        controller_cost = controller.get("monetary_cost")
        controller_cost_value = (
            float(controller_cost)
            if isinstance(controller_cost, (int, float)) and not isinstance(controller_cost, bool) and controller_cost >= 0
            else None
        )
        controller_observed = bool(controller_started_at or controller_cost_value is not None or any(value is not None for value in controller_usage.values()))

        provider = economics.get("provider_economics") if isinstance(economics.get("provider_economics"), dict) else {}
        provider_cost = provider.get("provider_cost")
        provider_usage_count = int(provider.get("usage_event_count") or 0)
        provider_cost_value = (
            float(provider_cost)
            if provider.get("cost_complete") is True
            and provider.get("attribution_complete") is True
            and isinstance(provider_cost, (int, float))
            else None
        )
        total_cost_complete = controller_cost_value is not None and (provider_cost_value is not None or provider_usage_count == 0)
        total_cost_value = None
        if total_cost_complete:
            total_cost_value = round(controller_cost_value + (provider_cost_value or 0.0), 12)
        if controller_cost_value is None:
            total_cost_reason = "controller_cost_unobserved"
        elif provider_usage_count and provider.get("attribution_complete") is not True:
            total_cost_reason = "provider_cost_attribution_incomplete"
        elif provider_usage_count and provider.get("cost_complete") is not True:
            total_cost_reason = "provider_cost_measurement_incomplete"
        else:
            total_cost_reason = None

        evaluation_identity = {
            "pair_id": _bounded_text(evaluation.get("pair_id") or "", 128) or None,
            "policy": _bounded_text(evaluation.get("policy") or "", 64).lower() or None,
            "policy_version": _bounded_text(evaluation.get("policy_version") or "", 64) or None,
            "topology_id": _bounded_text(evaluation.get("topology_id") or "", 100) or None,
            "router_id": _bounded_text(evaluation.get("router_id") or "", 100) or None,
            "router_version": _bounded_text(evaluation.get("router_version") or "", 64) or None,
            "task_class": self._route_task_class(run) or None,
            "oracle_id": _bounded_text(evaluation.get("oracle_id") or "", 128) or None,
            "provenance": self._promotion_sample_provenance(run),
            "task_spec_fp": _bounded_text(evaluation.get("task_spec_fp") or "", 128) or None,
            "environment_fp": _bounded_text(evaluation.get("environment_fp") or "", 128) or None,
            "tool_contract_fp": _bounded_text(evaluation.get("tool_contract_fp") or "", 128) or None,
            "evaluation_schema_fp": _bounded_text(evaluation.get("evaluation_schema_fp") or "", 128) or None,
            "runtime_version": _bounded_text(evaluation.get("runtime_version") or "", 80) or None,
            "cache_stratum": _bounded_text(evaluation.get("cache_stratum") or "", 32).lower() or None,
            "trace_id": _bounded_text(evaluation.get("trace_id") or "", 128) or None,
            "turn_id": _bounded_text(evaluation.get("turn_id") or "", 128) or None,
            "replicate_id": _bounded_text(evaluation.get("replicate_id") or "", 128) or None,
            "session_id": _bounded_text(evaluation.get("session_id") or "", 128) or None,
            "order_index": evaluation.get("order_index") if isinstance(evaluation.get("order_index"), int) and not isinstance(evaluation.get("order_index"), bool) else None,
            "schema_version": evaluation.get("schema_version") if isinstance(evaluation.get("schema_version"), int) and not isinstance(evaluation.get("schema_version"), bool) else None,
        }
        source_identity = {
            "base_head": str(first_wave.get("base_head") or "") or None,
            "worktree_fp": str(first_wave.get("worktree_fp") or "") or None,
            "contract_fp": str(first_wave.get("contract_fp") or "") or None,
        }
        pair_basis = {
            "task_spec_fp": evaluation_identity["task_spec_fp"],
            "base_head": source_identity["base_head"],
            "worktree_fp": source_identity["worktree_fp"],
            "contract_fp": source_identity["contract_fp"],
            "oracle_id": evaluation_identity["oracle_id"],
            "task_class": evaluation_identity["task_class"],
            "environment_fp": evaluation_identity["environment_fp"],
            "tool_contract_fp": evaluation_identity["tool_contract_fp"],
            "evaluation_schema_fp": evaluation_identity["evaluation_schema_fp"],
            "runtime_version": evaluation_identity["runtime_version"],
            "cache_stratum": evaluation_identity["cache_stratum"] if evaluation_identity["cache_stratum"] in {"cold", "warm"} else None,
        }
        pair_identity_complete = all(bool(value) for value in pair_basis.values())
        pair_fingerprint = hashlib.sha256(_json(pair_basis).encode("utf-8")).hexdigest() if pair_identity_complete else None
        evaluation_identity["pair_fingerprint"] = pair_fingerprint
        pairing_eligible = bool(
            evaluation_identity["pair_id"]
            and evaluation_identity["policy"]
            and evaluation_identity["provenance"] == "representative"
            and pair_identity_complete
        )
        return {
            "schema_version": 1,
            "run_id": run_id,
            "task_id": str(run.get("task_id") or ""),
            "status": str(run.get("status") or ""),
            "accepted": bool(economics.get("accepted")),
            "first_pass_accepted": bool(economics.get("first_pass_accepted")),
            "pairing_eligible": pairing_eligible,
            "evaluation": evaluation_identity,
            "source": source_identity,
            "route": dict(economics.get("route") or {}),
            "milestones": {
                "run_started_at": run_started_at,
                "first_route_at": first_route_at,
                "first_external_dispatch_at": first_external_dispatch_at,
                "first_write_at": first_write_at,
                "first_green_at": first_green_at,
                "accepted_at": accepted_at,
                "time_to_first_route_ms": elapsed_from_start(first_route_at),
                "time_to_first_external_dispatch_ms": elapsed_from_start(first_external_dispatch_at),
                "time_to_first_write_ms": elapsed_from_start(first_write_at),
                "time_to_first_green_ms": elapsed_from_start(first_green_at),
                "time_to_accepted_ms": elapsed_from_start(accepted_at),
            },
            "controller": {
                "measurement": str(controller.get("source") or "client_reported") if controller_observed else "unobserved_outside_mcp",
                "started_at": controller_started_at,
                "pre_mcp_ms": pre_mcp_ms,
                "usage": controller_usage,
                "monetary_cost": controller_cost_value,
            },
            "mcp": {
                "orchestration_tta_ms": economics.get("tta_ms"),
                "phase_timing": dict(economics.get("phase_timing") or {}),
                "proof_duration_ms": sum(max(0, int(item.get("duration_ms") or 0)) for item in proofs),
                "proof_records": len(proofs),
                "replan_count": int((economics.get("repair") or {}).get("replan_count") or 0),
                "failure_event_count": int((economics.get("repair") or {}).get("failure_event_count") or 0),
            },
            "external": {
                "provider_economics": dict(provider),
                "candidate_economics": dict(economics.get("candidate_economics") or {}),
            },
            "quality": {
                "accepted": bool(economics.get("accepted")),
                "first_pass_accepted": bool(economics.get("first_pass_accepted")),
                "critical_defects": dict(economics.get("critical_defects") or {}),
                "outcome": dict(economics.get("quality_outcome") or {}),
            },
            "total_monetary_cost": {
                "value": total_cost_value,
                "complete": total_cost_complete,
                "reason": total_cost_reason,
            },
        }

    def paired_policy_evaluation(
        self,
        *,
        baseline_policy: str = "chatweb_mcp",
        candidate_policies: Iterable[str] = ("mini", "luna"),
        limit: int = 500,
        min_pairs: int = 10,
        min_task_classes: int = 3,
    ) -> dict[str, Any]:
        """Compare explicitly paired representative runs without survivor bias."""
        baseline = _bounded_text(baseline_policy, 64).lower() or "chatweb_mcp"
        candidates = tuple(dict.fromkeys(_bounded_text(item, 64).lower() for item in candidate_policies if _bounded_text(item, 64)))
        bounded_limit = max(1, min(int(limit), 500))
        groups: dict[str, dict[str, list[dict[str, Any]]]] = {}
        excluded = {"not_pair_tagged": 0, "non_representative": 0, "identity_incomplete": 0, "identity_mismatch": 0, "duplicate_policy_run": 0}
        identity_mismatch_reasons: dict[str, int] = {}
        policy_names = (baseline, *candidates)
        placeholders = ",".join("?" for _ in policy_names)
        with self._lock, self._connect() as connection:
            ledger_run_count = int(connection.execute("SELECT COUNT(*) FROM runs").fetchone()[0])
            rows = connection.execute(
                f"""SELECT * FROM runs
                    WHERE json_extract(metadata_json, '$.evaluation.pair_id') IS NOT NULL
                      AND lower(json_extract(metadata_json, '$.evaluation.policy')) IN ({placeholders})
                    ORDER BY started_at DESC, run_id DESC
                    LIMIT ?""",
                (*policy_names, bounded_limit),
            ).fetchall()
        tagged_runs = [self._run_row(row) for row in rows]
        for run in tagged_runs:
            record = self.accepted_result_evaluation(str(run.get("run_id") or ""))
            evaluation = record.get("evaluation") if isinstance(record.get("evaluation"), dict) else {}
            pair_id = str(evaluation.get("pair_id") or "")
            policy = str(evaluation.get("policy") or "")
            if not pair_id or policy not in {baseline, *candidates}:
                excluded["not_pair_tagged"] += 1
                continue
            if evaluation.get("provenance") != "representative":
                excluded["non_representative"] += 1
                continue
            if record.get("pairing_eligible") is not True:
                excluded["identity_incomplete"] += 1
                continue
            groups.setdefault(pair_id, {}).setdefault(policy, []).append(record)

        def metric_percentile(values: list[float], percentile: int) -> float | None:
            if not values:
                return None
            ordered = sorted(values)
            rank = max(1, min(len(ordered), (len(ordered) * percentile + 99) // 100))
            return round(float(ordered[rank - 1]), 6)

        def observed_regret_pair(
            base: dict[str, Any],
            candidate: dict[str, Any],
            candidate_policy: str,
        ) -> dict[str, Any]:
            """Project regret only from one explicit representative causal pair."""

            def observed_action(record: dict[str, Any]) -> dict[str, Any]:
                quality = record.get("quality") if isinstance(record.get("quality"), dict) else {}
                outcome = quality.get("outcome") if isinstance(quality.get("outcome"), dict) else {}
                defects = quality.get("critical_defects") if isinstance(quality.get("critical_defects"), dict) else {}
                defect_count = defects.get("count")
                defect_value = (
                    int(defect_count)
                    if defects.get("status") == "known"
                    and isinstance(defect_count, int)
                    and not isinstance(defect_count, bool)
                    and defect_count >= 0
                    else None
                )
                quality_source = str(outcome.get("source") or "").strip() or None
                oracle_pass = outcome.get("oracle_pass") if isinstance(outcome.get("oracle_pass"), bool) else None
                tta = (record.get("milestones") or {}).get("time_to_accepted_ms")
                tta_value = (
                    float(tta)
                    if record.get("accepted") is True
                    and isinstance(tta, (int, float))
                    and not isinstance(tta, bool)
                    and tta >= 0
                    else None
                )
                total_cost = record.get("total_monetary_cost") if isinstance(record.get("total_monetary_cost"), dict) else {}
                cost = total_cost.get("value")
                cost_value = (
                    float(cost)
                    if total_cost.get("complete") is True
                    and isinstance(cost, (int, float))
                    and not isinstance(cost, bool)
                    and cost >= 0
                    else None
                )
                return {
                    "accepted": bool(record.get("accepted")),
                    "first_pass_accepted": bool(record.get("first_pass_accepted")),
                    "quality": {
                        "source": quality_source,
                        "oracle_pass": oracle_pass,
                        "critical_defect_count": defect_value,
                        "complete": bool(quality_source and defect_value is not None),
                    },
                    "time_to_accepted_ms": tta_value,
                    "total_monetary_cost": cost_value,
                    "total_monetary_cost_complete": bool(total_cost.get("complete")),
                }

            observed = {
                baseline: observed_action(base),
                candidate_policy: observed_action(candidate),
            }
            missing: list[str] = []
            for action, evidence in observed.items():
                if not (evidence.get("quality") or {}).get("complete"):
                    missing.append(f"{action}:quality_outcome")
                if evidence.get("time_to_accepted_ms") is None:
                    missing.append(f"{action}:time_to_accepted_result")
                if evidence.get("total_monetary_cost") is None:
                    missing.append(f"{action}:total_monetary_cost")

            best_action: str | None = None
            status = "outcome_incomplete"
            component_regret: dict[str, dict[str, float] | None] = {baseline: None, candidate_policy: None}
            if not missing:
                vectors = {
                    action: {
                        "critical_defect_count": float((evidence.get("quality") or {}).get("critical_defect_count")),
                        "time_to_accepted_ms": float(evidence["time_to_accepted_ms"]),
                        "total_monetary_cost": float(evidence["total_monetary_cost"]),
                    }
                    for action, evidence in observed.items()
                }

                def dominates(left: dict[str, float], right: dict[str, float]) -> bool:
                    keys = ("critical_defect_count", "time_to_accepted_ms", "total_monetary_cost")
                    return all(left[key] <= right[key] for key in keys) and any(left[key] < right[key] for key in keys)

                if dominates(vectors[baseline], vectors[candidate_policy]):
                    best_action = baseline
                    status = "observed_pareto_dominance"
                elif dominates(vectors[candidate_policy], vectors[baseline]):
                    best_action = candidate_policy
                    status = "observed_pareto_dominance"
                elif vectors[baseline] == vectors[candidate_policy]:
                    status = "no_dominance"
                else:
                    status = "tradeoff_requires_calibrated_utility"

                if best_action is not None:
                    best = vectors[best_action]
                    for action, vector in vectors.items():
                        component_regret[action] = {
                            "critical_defect_count": round(vector["critical_defect_count"] - best["critical_defect_count"], 6),
                            "time_to_accepted_ms": round(vector["time_to_accepted_ms"] - best["time_to_accepted_ms"], 6),
                            "total_monetary_cost": round(vector["total_monetary_cost"] - best["total_monetary_cost"], 12),
                        }

            return {
                "schema_version": 1,
                "status": status,
                "outcome_complete": not missing,
                "missing_observations": missing,
                "actual_outcomes": observed,
                "best_observed_comparable_action": best_action,
                "predicted_policy_score": {
                    "measurement": "unobserved_not_recorded",
                    "baseline": None,
                    "candidate": None,
                },
                "regret_estimate": {
                    "scalar": None,
                    "scalar_status": "utility_weights_not_calibrated",
                    "components_by_policy": component_regret,
                    "component_basis": "observed_action_minus_best_observed_comparable_action",
                },
                "comparability_basis": "explicit_representative_pair_identity_and_pair_fingerprint",
                "historical_or_similar_task_counterfactual_used": False,
            }

        results: list[dict[str, Any]] = []
        for policy in candidates:
            pair_rows: list[dict[str, Any]] = []
            for pair_id, policy_rows in groups.items():
                baselines = policy_rows.get(baseline, [])
                candidate_rows = policy_rows.get(policy, [])
                if len(baselines) != 1 or len(candidate_rows) != 1:
                    if baselines or candidate_rows:
                        excluded["duplicate_policy_run"] += 1
                    continue
                base = baselines[0]
                candidate = candidate_rows[0]
                base_eval = base["evaluation"]
                candidate_eval = candidate["evaluation"]
                identity_fields = {
                    "base_head": (base["source"].get("base_head"), candidate["source"].get("base_head")),
                    "worktree_fp": (base["source"].get("worktree_fp"), candidate["source"].get("worktree_fp")),
                    "contract_fp": (base["source"].get("contract_fp"), candidate["source"].get("contract_fp")),
                    "oracle_id": (base_eval.get("oracle_id"), candidate_eval.get("oracle_id")),
                    "task_class": (base_eval.get("task_class"), candidate_eval.get("task_class")),
                    "task_spec_fp": (base_eval.get("task_spec_fp"), candidate_eval.get("task_spec_fp")),
                    "environment_fp": (base_eval.get("environment_fp"), candidate_eval.get("environment_fp")),
                    "tool_contract_fp": (base_eval.get("tool_contract_fp"), candidate_eval.get("tool_contract_fp")),
                    "evaluation_schema_fp": (base_eval.get("evaluation_schema_fp"), candidate_eval.get("evaluation_schema_fp")),
                    "runtime_version": (base_eval.get("runtime_version"), candidate_eval.get("runtime_version")),
                    "cache_stratum": (base_eval.get("cache_stratum"), candidate_eval.get("cache_stratum")),
                    "pair_fingerprint": (base_eval.get("pair_fingerprint"), candidate_eval.get("pair_fingerprint")),
                }
                mismatches = [key for key, values in identity_fields.items() if not values[0] or values[0] != values[1]]
                if mismatches:
                    excluded["identity_mismatch"] += 1
                    for field in mismatches:
                        identity_mismatch_reasons[field] = identity_mismatch_reasons.get(field, 0) + 1
                    continue
                base_tta = base.get("milestones", {}).get("time_to_accepted_ms")
                candidate_tta = candidate.get("milestones", {}).get("time_to_accepted_ms")
                base_credits = (base.get("external", {}).get("candidate_economics") or {}).get("estimated_credits")
                candidate_credits = (candidate.get("external", {}).get("candidate_economics") or {}).get("estimated_credits")
                if base_credits is None and str((base.get("route") or {}).get("resolved") or "") in {"deterministic", "mcp_deterministic", "unknown"}:
                    base_credits = 0.0
                regret = observed_regret_pair(base, candidate, policy)
                pair_rows.append({
                    "pair_id": pair_id,
                    "task_class": base_eval.get("task_class"),
                    "baseline_accepted": bool(base.get("accepted")),
                    "candidate_accepted": bool(candidate.get("accepted")),
                    "baseline_first_pass": bool(base.get("first_pass_accepted")),
                    "candidate_first_pass": bool(candidate.get("first_pass_accepted")),
                    "baseline_repaired": int((base.get("mcp") or {}).get("replan_count") or 0) > 0,
                    "candidate_repaired": int((candidate.get("mcp") or {}).get("replan_count") or 0) > 0,
                    "baseline_tta_ms": base_tta,
                    "candidate_tta_ms": candidate_tta,
                    "tta_delta_ms": (
                        int(candidate_tta) - int(base_tta)
                        if base.get("accepted") and candidate.get("accepted") and isinstance(base_tta, (int, float)) and isinstance(candidate_tta, (int, float))
                        else None
                    ),
                    "baseline_controller_cost": (base.get("controller") or {}).get("monetary_cost"),
                    "candidate_controller_cost": (candidate.get("controller") or {}).get("monetary_cost"),
                    "baseline_external_candidate_credits": base_credits,
                    "candidate_external_candidate_credits": candidate_credits,
                    "external_candidate_credit_delta": (
                        round(float(candidate_credits) - float(base_credits), 6)
                        if isinstance(candidate_credits, (int, float)) and isinstance(base_credits, (int, float))
                        else None
                    ),
                    "baseline_critical_defects": (base.get("quality") or {}).get("critical_defects"),
                    "candidate_critical_defects": (candidate.get("quality") or {}).get("critical_defects"),
                    "baseline_total_cost": (base.get("total_monetary_cost") or {}).get("value"),
                    "candidate_total_cost": (candidate.get("total_monetary_cost") or {}).get("value"),
                    "routing_placement_regret": regret,
                })

            task_classes = sorted({str(row["task_class"]) for row in pair_rows if row.get("task_class")})
            accepted_pairs = [row for row in pair_rows if row["baseline_accepted"] and row["candidate_accepted"]]
            tta_deltas = [float(row["tta_delta_ms"]) for row in accepted_pairs if isinstance(row.get("tta_delta_ms"), (int, float))]
            baseline_ttas = [float(row["baseline_tta_ms"]) for row in accepted_pairs if isinstance(row.get("baseline_tta_ms"), (int, float))]
            candidate_ttas = [float(row["candidate_tta_ms"]) for row in accepted_pairs if isinstance(row.get("candidate_tta_ms"), (int, float))]
            external_credit_deltas = [float(row["external_candidate_credit_delta"]) for row in pair_rows if isinstance(row.get("external_candidate_credit_delta"), (int, float))]
            total_cost_pairs = [row for row in accepted_pairs if isinstance(row.get("baseline_total_cost"), (int, float)) and isinstance(row.get("candidate_total_cost"), (int, float))]
            regret_pairs = [row["routing_placement_regret"] for row in pair_rows]
            complete_regret_pairs = [item for item in regret_pairs if item.get("outcome_complete") is True]
            best_action_pairs = [item for item in complete_regret_pairs if item.get("best_observed_comparable_action")]
            tradeoff_pairs = [item for item in complete_regret_pairs if item.get("status") == "tradeoff_requires_calibrated_utility"]
            no_dominance_pairs = [item for item in complete_regret_pairs if item.get("status") == "no_dominance"]
            regret_hold_reasons: list[str] = []
            if not pair_rows:
                regret_measurement_status = "indeterminate_no_comparable_pairs"
                regret_hold_reasons.append("no_comparable_pairs")
            elif len(complete_regret_pairs) < len(pair_rows):
                regret_measurement_status = "incomplete"
                regret_hold_reasons.append("outcome_incomplete")
            elif tradeoff_pairs:
                regret_measurement_status = "tradeoff_requires_calibrated_utility"
                regret_hold_reasons.append("utility_weights_not_calibrated")
            elif best_action_pairs:
                regret_measurement_status = "observed_component_regret"
            else:
                regret_measurement_status = "observed_no_dominance"
            reasons: list[str] = []
            if len(pair_rows) < max(1, int(min_pairs)):
                reasons.append("insufficient_paired_results")
            if len(task_classes) < max(1, int(min_task_classes)):
                reasons.append("insufficient_task_class_diversity")
            if any(not row["baseline_accepted"] or not row["candidate_accepted"] for row in pair_rows):
                reasons.append("quality_floor_non_regression_not_proven")
            if any(
                not isinstance(row.get("baseline_critical_defects"), dict)
                or row["baseline_critical_defects"].get("status") != "known"
                or not isinstance(row.get("candidate_critical_defects"), dict)
                or row["candidate_critical_defects"].get("status") != "known"
                for row in pair_rows
            ):
                reasons.append("critical_defect_evidence_incomplete")
            if any(
                isinstance(row.get("candidate_critical_defects"), dict)
                and isinstance(row["candidate_critical_defects"].get("count"), int)
                and row["candidate_critical_defects"].get("count") > 0
                for row in pair_rows
            ):
                reasons.append("quality_floor_non_regression_not_proven")
            if len(total_cost_pairs) < len(accepted_pairs):
                reasons.append("controller_cost_unobserved")
            if len(accepted_pairs) != len(pair_rows):
                reasons.append("accepted_result_tta_incomplete")
            if not pair_rows:
                pareto_status = "indeterminate_no_pairs"
            elif len(total_cost_pairs) < len(accepted_pairs):
                pareto_status = "indeterminate_total_cost"
            else:
                pareto_status = "manual_review_required"
            results.append({
                "candidate_policy": policy,
                "status": "eligible_for_manual_roi_review" if not reasons else "hold",
                "hold_reasons": list(dict.fromkeys(reasons)),
                "pair_count": len(pair_rows),
                "accepted_pair_count": len(accepted_pairs),
                "baseline_acceptance_rate": round(sum(1 for row in pair_rows if row["baseline_accepted"]) / len(pair_rows), 6) if pair_rows else None,
                "candidate_acceptance_rate": round(sum(1 for row in pair_rows if row["candidate_accepted"]) / len(pair_rows), 6) if pair_rows else None,
                "baseline_first_pass_rate": round(sum(1 for row in pair_rows if row["baseline_first_pass"]) / len(pair_rows), 6) if pair_rows else None,
                "candidate_first_pass_rate": round(sum(1 for row in pair_rows if row["candidate_first_pass"]) / len(pair_rows), 6) if pair_rows else None,
                "baseline_repair_rate": round(sum(1 for row in pair_rows if row["baseline_repaired"]) / len(pair_rows), 6) if pair_rows else None,
                "candidate_repair_rate": round(sum(1 for row in pair_rows if row["candidate_repaired"]) / len(pair_rows), 6) if pair_rows else None,
                "analysis_population": {
                    "basis": "explicit_representative_comparable_pairs_status_independent",
                    "intention_to_treat": True,
                    "survivor_filter": False,
                    "tta_condition": "both_actions_accepted",
                },
                "task_classes": task_classes,
                "task_class_count": len(task_classes),
                "tta_ms": {
                    "baseline_p50": metric_percentile(baseline_ttas, 50),
                    "baseline_p90": metric_percentile(baseline_ttas, 90),
                    "candidate_p50": metric_percentile(candidate_ttas, 50),
                    "candidate_p90": metric_percentile(candidate_ttas, 90),
                    "delta_p50": metric_percentile(tta_deltas, 50),
                    "delta_p90": metric_percentile(tta_deltas, 90),
                },
                "external_candidate_credit_delta": {
                    "samples": len(external_credit_deltas),
                    "p50": metric_percentile(external_credit_deltas, 50),
                    "p90": metric_percentile(external_credit_deltas, 90),
                    "measurement": "estimated_external_candidate_credits_only_not_total_system_cost",
                },
                "total_monetary_cost": {
                    "comparable_pairs": len(total_cost_pairs),
                    "complete": bool(pair_rows) and len(total_cost_pairs) == len(accepted_pairs) == len(pair_rows),
                    "reason": None if bool(pair_rows) and len(total_cost_pairs) == len(accepted_pairs) == len(pair_rows) else "controller_cost_unobserved",
                },
                "routing_placement_regret": {
                    "status": "hold" if regret_hold_reasons else "observed",
                    "measurement_status": regret_measurement_status,
                    "hold_reasons": regret_hold_reasons,
                    "comparable_pairs": len(pair_rows),
                    "complete_outcome_pairs": len(complete_regret_pairs),
                    "best_action_pairs": len(best_action_pairs),
                    "tradeoff_pairs": len(tradeoff_pairs),
                    "no_dominance_pairs": len(no_dominance_pairs),
                    "predicted_policy_score": {
                        "measurement": "unobserved_not_recorded",
                        "eligible_pairs": len(pair_rows),
                        "observed_pairs": 0,
                        "coverage": 0.0 if pair_rows else None,
                    },
                    "scalar_regret": {
                        "value": None,
                        "measurement": "unavailable_without_calibrated_utility",
                        "utility_weights_calibrated": False,
                    },
                    "automatic_activation": False,
                },
                "pareto_status": pareto_status,
                "automatic_activation": False,
                "pairs": pair_rows[:100],
            })
        return {
            "schema_version": 1,
            "north_star": "quality_floor_then_cost_and_time_to_accepted_result",
            "baseline_policy": baseline,
            "candidate_policies": list(candidates),
            "ledger_run_count": ledger_run_count,
            "tagged_runs_scanned": len(tagged_runs),
            "thresholds": {
                "min_pairs": max(1, int(min_pairs)),
                "min_task_classes": max(1, int(min_task_classes)),
                "savings_threshold": "learn_from_representative_paired_data",
            },
            "excluded": excluded,
            "identity_mismatch_reasons": identity_mismatch_reasons,
            "results": results,
            "regret_methodology": {
                "source": "orchestration_ledger_explicit_representative_pairs",
                "best_observed_action_rule": "weak_pareto_dominance_on_observed_quality_time_and_total_cost_with_one_strict_improvement",
                "quality_metric": "critical_defect_count_from_explicit_quality_outcome",
                "predicted_policy_score": "unobserved_not_recorded",
                "scalar_regret": "unavailable_without_calibrated_utility_weights",
                "historical_or_similar_task_counterfactual_forbidden": True,
            },
            "automatic_activation": False,
            "controller_cost_policy": "unknown_is_not_zero",
            "model_free": True,
            "content_free": True,
        }

    def list_events_since(
        self,
        run_id: str,
        *,
        after_seq: int = 0,
        limit: int = 100,
    ) -> dict[str, Any]:
        bounded_limit = max(1, min(int(limit), 500))
        with self._lock, self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM events WHERE run_id=? AND seq>? ORDER BY seq LIMIT ?",
                (run_id, max(0, int(after_seq)), bounded_limit + 1),
            ).fetchall()
        has_more = len(rows) > bounded_limit
        selected = rows[:bounded_limit]
        events = [self._event_row(row) for row in selected]
        return {
            "run_id": run_id,
            "after_seq": max(0, int(after_seq)),
            "events": events,
            "next_after_seq": int(events[-1]["seq"]) if events else max(0, int(after_seq)),
            "has_more": has_more,
        }

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
                    _encode_proof_metadata(metadata or {}),
                ),
            )
        return proof_id

    def proof_cache_lookup(self, *, stage_id: str, stage_version: str, input_fingerprint: str) -> dict[str, Any]:
        """Classify one proof-cache opportunity without changing reuse semantics."""
        stage = _bounded_text(stage_id, 200)
        version = _bounded_text(stage_version, 100)
        fingerprint = _bounded_text(input_fingerprint, 128)
        with self._lock, self._connect() as connection:
            exact = connection.execute(
                """SELECT * FROM proofs
                WHERE stage_id=? AND stage_version=? AND input_fingerprint=? AND status='passed'
                ORDER BY finished_at DESC LIMIT 1""",
                (stage, version, fingerprint),
            ).fetchone()
            if exact is not None:
                return {"eligible": True, "hit": True, "reason": "exact_fingerprint", "source_proof": self._proof_row(exact)}
            same_version = connection.execute(
                """SELECT * FROM proofs
                WHERE stage_id=? AND stage_version=? AND status='passed'
                ORDER BY finished_at DESC LIMIT 1""",
                (stage, version),
            ).fetchone()
            if same_version is not None:
                return {
                    "eligible": True,
                    "hit": False,
                    "reason": "input_fingerprint_changed",
                    "source_proof": self._proof_row(same_version),
                }
            same_stage = connection.execute(
                """SELECT * FROM proofs
                WHERE stage_id=? AND status='passed'
                ORDER BY finished_at DESC LIMIT 1""",
                (stage,),
            ).fetchone()
        if same_stage is not None:
            return {
                "eligible": True,
                "hit": False,
                "reason": "stage_version_changed",
                "source_proof": self._proof_row(same_stage),
            }
        return {"eligible": True, "hit": False, "reason": "cold", "source_proof": None}

    def proof_cache_opportunity_summary(self, *, stage_limit: int = 100) -> dict[str, Any]:
        """Project bounded proof-cache opportunity evidence without exposing fingerprints."""
        with self._lock, self._connect() as connection:
            return _proof_cache_opportunity_summary(connection, stage_limit=stage_limit)

    def find_cached_pass(self, *, stage_id: str, stage_version: str, input_fingerprint: str) -> dict[str, Any] | None:
        lookup = self.proof_cache_lookup(
            stage_id=stage_id,
            stage_version=stage_version,
            input_fingerprint=input_fingerprint,
        )
        return lookup["source_proof"] if lookup["hit"] else None

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
            "metadata": _decode_proof_metadata(row["metadata_json"]),
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
            self._insert_checkpoint_row(
                connection,
                checkpoint_id=checkpoint_id,
                run_id=run_id,
                wave_id=wave_id,
                git_head=git_head,
                proof_fingerprint=proof_fingerprint,
                status=status,
                metadata=metadata,
            )
        return checkpoint_id

    @staticmethod
    def _insert_checkpoint_row(
        connection: sqlite3.Connection,
        *,
        checkpoint_id: str,
        run_id: str,
        wave_id: str | None,
        git_head: str,
        proof_fingerprint: str,
        status: str,
        metadata: dict[str, Any] | None,
    ) -> str:
        """Insert a checkpoint using the caller's transaction."""
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

    def accept_checkpoint_atomic(
        self,
        *,
        run_id: str,
        wave_id: str,
        git_head: str,
        proof_fingerprint: str,
        status: str = "accepted",
        metadata: dict[str, Any] | None = None,
        state_before: str = "ACCEPTING",
        state_after: str = "CHECKPOINTED",
        reason: str = "chatweb_sol_acceptance",
        delegation_id: str | None = None,
    ) -> dict[str, Any]:
        """Atomically append terminal acceptance and its checkpoint receipt.

        The state-transition event, run/wave terminal updates, and checkpoint
        row share one ``BEGIN IMMEDIATE`` transaction.  Any injected or
        unexpected failure rolls all three back, leaving the authoritative
        ledger in ``ACCEPTING`` with a valid prior event-chain head.
        """
        checkpoint_id = uuid.uuid4().hex
        now = utc_now()
        with self._lock, self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            run = connection.execute(
                "SELECT status FROM runs WHERE run_id=?",
                (run_id,),
            ).fetchone()
            wave = connection.execute(
                "SELECT run_id,status FROM waves WHERE wave_id=?",
                (wave_id,),
            ).fetchone()
            if run is None or wave is None or str(wave["run_id"] or "") != str(run_id):
                raise ValueError("atomic checkpoint run/wave was not found")
            if str(run["status"] or "") != "active" or str(wave["status"] or "") != "active":
                raise ValueError("atomic checkpoint requires an active run and wave")
            event = append_hash_chained_event(
                connection,
                run_id=run_id,
                wave_id=wave_id,
                delegation_id=delegation_id,
                event_type="state_transition",
                state_before=_bounded_text(state_before, 64),
                state_after=_bounded_text(state_after, 64),
                payload={"reason": reason, "checkpoint_id": checkpoint_id},
                event_time=now,
                sanitize=_sanitize,
                serialize=_json,
                bounded_text=_bounded_text,
            )
            connection.execute(
                "UPDATE waves SET status=?, finished_at=? WHERE wave_id=?",
                (_bounded_text(status, 64), now, wave_id),
            )
            connection.execute(
                "UPDATE runs SET status=?, finished_at=? WHERE run_id=?",
                (_bounded_text(status, 64), now, run_id),
            )
            self._insert_checkpoint_row(
                connection,
                checkpoint_id=checkpoint_id,
                run_id=run_id,
                wave_id=wave_id,
                git_head=git_head,
                proof_fingerprint=proof_fingerprint,
                status=status,
                metadata=metadata,
            )
        return {"checkpoint_id": checkpoint_id, "event": event}

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

    @staticmethod
    def _hub_client_row(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "client_id": row["client_id"],
            "client_type": row["client_type"],
            "role": row["role"],
            "status": row["status"],
            "session_instance": row["session_instance"],
            "runtime_instance_id": row["runtime_instance_id"],
            "contract_sha": row["contract_sha"],
            "connected_at": row["connected_at"],
            "last_seen_at": row["last_seen_at"],
            "capabilities": json.loads(row["capabilities_json"] or "{}"),
            "metadata": json.loads(row["metadata_json"] or "{}"),
        }

    def upsert_hub_client(
        self,
        *,
        client_id: str,
        client_type: str,
        role: str,
        status: str = "online",
        session_instance: str = "",
        runtime_instance_id: str = "",
        contract_sha: str = "",
        capabilities: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        client = _bounded_text(client_id, 128).strip()
        if not client:
            raise ValueError("client_id is required")
        now = utc_now()
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT connected_at, metadata_json FROM hub_clients WHERE client_id=?",
                (client,),
            ).fetchone()
            connected_at = str(row["connected_at"]) if row else now
            existing = json.loads(row["metadata_json"] or "{}") if row else {}
            existing.update(_sanitize(metadata or {}))
            connection.execute(
                """INSERT INTO hub_clients(
                    client_id,client_type,role,status,session_instance,runtime_instance_id,
                    contract_sha,connected_at,last_seen_at,capabilities_json,metadata_json
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(client_id) DO UPDATE SET
                    client_type=excluded.client_type,role=excluded.role,status=excluded.status,
                    session_instance=excluded.session_instance,runtime_instance_id=excluded.runtime_instance_id,
                    contract_sha=excluded.contract_sha,last_seen_at=excluded.last_seen_at,
                    capabilities_json=excluded.capabilities_json,metadata_json=excluded.metadata_json""",
                (
                    client,
                    _bounded_text(client_type, 64),
                    _bounded_text(role, 64),
                    _bounded_text(status, 32),
                    _bounded_text(session_instance, 256),
                    _bounded_text(runtime_instance_id, 256),
                    _bounded_text(contract_sha, 128),
                    connected_at,
                    now,
                    _json(_sanitize(capabilities or {})),
                    _json(existing),
                ),
            )
        result = self.get_hub_client(client)
        assert result is not None
        return result

    def get_hub_client(self, client_id: str) -> dict[str, Any] | None:
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM hub_clients WHERE client_id=?",
                (_bounded_text(client_id, 128),),
            ).fetchone()
        return self._hub_client_row(row) if row else None

    def list_hub_clients(self, *, online_within_seconds: float = 45.0) -> list[dict[str, Any]]:
        cutoff = datetime.fromtimestamp(
            time.time() - max(1.0, float(online_within_seconds)), timezone.utc
        ).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        with self._lock, self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM hub_clients ORDER BY last_seen_at DESC, client_id"
            ).fetchall()
        clients = [self._hub_client_row(row) for row in rows]
        for client in clients:
            client["online"] = bool(
                client.get("status") == "online"
                and str(client.get("last_seen_at") or "") >= cutoff
            )
        return clients

    def set_hub_client_status(self, client_id: str, status: str) -> dict[str, Any] | None:
        with self._lock, self._connect() as connection:
            cursor = connection.execute(
                "UPDATE hub_clients SET status=?, last_seen_at=? WHERE client_id=?",
                (_bounded_text(status, 32), utc_now(), _bounded_text(client_id, 128)),
            )
            if not cursor.rowcount:
                return None
        return self.get_hub_client(client_id)

    def advance_hub_client_cursor(self, *, client_id: str, run_id: str, last_event_seq: int) -> dict[str, Any]:
        client = _bounded_text(client_id, 128).strip()
        run = _bounded_text(run_id, 256).strip()
        if not client or not run:
            raise ValueError("client_id and run_id are required")
        seq = max(0, int(last_event_seq))
        now = utc_now()
        with self._lock, self._connect() as connection:
            if not connection.execute("SELECT 1 FROM hub_clients WHERE client_id=?", (client,)).fetchone():
                raise ValueError("hub client is not registered")
            if not connection.execute("SELECT 1 FROM runs WHERE run_id=?", (run,)).fetchone():
                raise ValueError("orchestration run does not exist")
            connection.execute(
                """INSERT INTO hub_client_cursors(client_id,run_id,last_event_seq,updated_at)
                VALUES(?,?,?,?)
                ON CONFLICT(client_id,run_id) DO UPDATE SET
                    last_event_seq=MAX(hub_client_cursors.last_event_seq, excluded.last_event_seq),
                    updated_at=CASE
                        WHEN excluded.last_event_seq > hub_client_cursors.last_event_seq THEN excluded.updated_at
                        ELSE hub_client_cursors.updated_at END""",
                (client, run, seq, now),
            )
            row = connection.execute(
                "SELECT * FROM hub_client_cursors WHERE client_id=? AND run_id=?",
                (client, run),
            ).fetchone()
        assert row is not None
        return {
            "client_id": row["client_id"],
            "run_id": row["run_id"],
            "last_event_seq": int(row["last_event_seq"] or 0),
            "updated_at": row["updated_at"],
        }

    def get_hub_client_cursor(self, *, client_id: str, run_id: str) -> dict[str, Any] | None:
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM hub_client_cursors WHERE client_id=? AND run_id=?",
                (_bounded_text(client_id, 128), _bounded_text(run_id, 256)),
            ).fetchone()
        if not row:
            return None
        return {
            "client_id": row["client_id"],
            "run_id": row["run_id"],
            "last_event_seq": int(row["last_event_seq"] or 0),
            "updated_at": row["updated_at"],
        }

    def list_hub_client_cursors(self, *, run_id: str = "") -> list[dict[str, Any]]:
        query = "SELECT * FROM hub_client_cursors"
        params: list[Any] = []
        if run_id:
            query += " WHERE run_id=?"
            params.append(_bounded_text(run_id, 256))
        query += " ORDER BY updated_at DESC, client_id"
        with self._lock, self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [
            {
                "client_id": row["client_id"],
                "run_id": row["run_id"],
                "last_event_seq": int(row["last_event_seq"] or 0),
                "updated_at": row["updated_at"],
            }
            for row in rows
        ]

    @staticmethod
    def _controller_lease_row(row: sqlite3.Row) -> dict[str, Any]:
        status = str(row["status"])
        expires_at = float(row["expires_at"] or 0)
        if status == "active" and expires_at <= time.time():
            status = "expired"
        return {
            "run_id": row["run_id"],
            "fencing_token": int(row["fencing_token"] or 0),
            "lease_id": row["lease_id"],
            "owner_client_id": row["owner_client_id"],
            "status": status,
            "expires_at": expires_at,
            "updated_at": row["updated_at"],
        }

    def expire_controller_leases(self, *, now: float | None = None) -> list[str]:
        """Persist expiry for controller leases whose TTL has elapsed.

        Lease readers historically derived ``expired`` in memory while leaving the
        SQLite row ``active``.  That made a restarted client see ghost ownership
        until another acquisition happened.  Reconciliation is deliberately
        idempotent and returns the affected run ids for health reporting.
        """

        now_ts = time.time() if now is None else float(now)
        updated_at = utc_now()
        with self._lock, self._connect() as connection:
            rows = connection.execute(
                "SELECT run_id FROM controller_leases WHERE status='active' AND expires_at<=?",
                (now_ts,),
            ).fetchall()
            if rows:
                connection.execute(
                    """UPDATE controller_leases
                       SET status='expired', updated_at=?
                       WHERE status='active' AND expires_at<=?""",
                    (updated_at, now_ts),
                )
        return [str(row["run_id"]) for row in rows]

    def get_controller_lease(self, run_id: str) -> dict[str, Any] | None:
        self.expire_controller_leases()
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM controller_leases WHERE run_id=?",
                (_bounded_text(run_id, 256),),
            ).fetchone()
        return self._controller_lease_row(row) if row else None

    def peek_controller_lease(self, run_id: str) -> dict[str, Any] | None:
        """Read current controller ownership without persisting lease maintenance."""
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM controller_leases WHERE run_id=?",
                (_bounded_text(run_id, 256),),
            ).fetchone()
        return self._controller_lease_row(row) if row else None

    def acquire_controller_lease(
        self,
        *,
        run_id: str,
        owner_client_id: str,
        lease_id: str,
        ttl_seconds: float = 60.0,
    ) -> dict[str, Any]:
        run = _bounded_text(run_id, 256).strip()
        owner = _bounded_text(owner_client_id, 128).strip()
        lease = _bounded_text(lease_id, 256).strip()
        if not run or not owner or not lease:
            raise ValueError("run_id, owner_client_id and lease_id are required")
        now = time.time()
        expires_at = now + max(1.0, float(ttl_seconds))
        with self._lock, self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            if not connection.execute("SELECT 1 FROM runs WHERE run_id=?", (run,)).fetchone():
                raise ValueError("orchestration run does not exist")
            if not connection.execute("SELECT 1 FROM hub_clients WHERE client_id=?", (owner,)).fetchone():
                raise ValueError("controller client is not registered")
            row = connection.execute(
                "SELECT * FROM controller_leases WHERE run_id=?", (run,)
            ).fetchone()
            if row and row["status"] == "active" and float(row["expires_at"] or 0) > now:
                current = self._controller_lease_row(row)
                if row["owner_client_id"] != owner or row["lease_id"] != lease:
                    connection.commit()
                    return {"acquired": False, "reason": "active_lease", "current": current}
                connection.execute(
                    "UPDATE controller_leases SET expires_at=?, updated_at=? WHERE run_id=?",
                    (expires_at, utc_now(), run),
                )
                connection.commit()
                current["expires_at"] = expires_at
                current["updated_at"] = utc_now()
                current["status"] = "active"
                return {"acquired": True, "renewed": True, **current}
            token = int(row["fencing_token"] or 0) + 1 if row else 1
            updated_at = utc_now()
            connection.execute(
                """INSERT INTO controller_leases(
                    run_id,fencing_token,lease_id,owner_client_id,status,expires_at,updated_at
                ) VALUES(?,?,?,?,?,?,?)
                ON CONFLICT(run_id) DO UPDATE SET
                    fencing_token=excluded.fencing_token,lease_id=excluded.lease_id,
                    owner_client_id=excluded.owner_client_id,status='active',
                    expires_at=excluded.expires_at,updated_at=excluded.updated_at""",
                (run, token, lease, owner, "active", expires_at, updated_at),
            )
            connection.commit()
        return {
            "acquired": True,
            "renewed": False,
            "run_id": run,
            "fencing_token": token,
            "lease_id": lease,
            "owner_client_id": owner,
            "status": "active",
            "expires_at": expires_at,
            "updated_at": updated_at,
        }

    def assert_controller_lease(
        self,
        *,
        run_id: str,
        owner_client_id: str,
        lease_id: str,
        fencing_token: int,
    ) -> dict[str, Any]:
        current = self.get_controller_lease(run_id)
        if current is None:
            return {"valid": False, "reason": "missing"}
        if current["status"] != "active":
            return {"valid": False, "reason": current["status"], "current": current}
        if (
            current["owner_client_id"] != owner_client_id
            or current["lease_id"] != lease_id
            or current["fencing_token"] != int(fencing_token)
        ):
            return {"valid": False, "reason": "stale", "current": current}
        return {"valid": True, "current": current}

    def release_controller_lease(
        self,
        *,
        run_id: str,
        owner_client_id: str,
        lease_id: str,
        fencing_token: int,
    ) -> bool:
        with self._lock, self._connect() as connection:
            cursor = connection.execute(
                """UPDATE controller_leases SET status='released', updated_at=?
                WHERE run_id=? AND owner_client_id=? AND lease_id=? AND fencing_token=? AND status='active'""",
                (
                    utc_now(),
                    _bounded_text(run_id, 256),
                    _bounded_text(owner_client_id, 128),
                    _bounded_text(lease_id, 256),
                    int(fencing_token),
                ),
            )
        return bool(cursor.rowcount)

    def operator_transfer_controller(
        self,
        *,
        run_id: str,
        target_client_id: str,
        lease_id: str,
        ttl_seconds: float = 60.0,
        online_within_seconds: float = 45.0,
    ) -> dict[str, Any]:
        run = _bounded_text(run_id, 256).strip()
        target = _bounded_text(target_client_id, 128).strip()
        lease = _bounded_text(lease_id, 256).strip()
        if not run or not target or not lease:
            raise ValueError("run_id, target_client_id and lease_id are required")
        cutoff = datetime.fromtimestamp(
            time.time() - max(1.0, float(online_within_seconds)), timezone.utc
        ).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        now = time.time()
        expires_at = now + max(1.0, float(ttl_seconds))
        with self._lock, self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            if not connection.execute("SELECT 1 FROM runs WHERE run_id=?", (run,)).fetchone():
                raise ValueError("orchestration run does not exist")
            client = connection.execute(
                "SELECT * FROM hub_clients WHERE client_id=?", (target,)
            ).fetchone()
            if (
                not client
                or client["status"] != "online"
                or str(client["last_seen_at"] or "") < cutoff
            ):
                connection.commit()
                return {"transferred": False, "reason": "target_offline", "target_client_id": target}
            row = connection.execute(
                "SELECT * FROM controller_leases WHERE run_id=?", (run,)
            ).fetchone()
            token = int(row["fencing_token"] or 0) + 1 if row else 1
            updated_at = utc_now()
            connection.execute(
                """INSERT INTO controller_leases(
                    run_id,fencing_token,lease_id,owner_client_id,status,expires_at,updated_at
                ) VALUES(?,?,?,?,?,?,?)
                ON CONFLICT(run_id) DO UPDATE SET
                    fencing_token=excluded.fencing_token,lease_id=excluded.lease_id,
                    owner_client_id=excluded.owner_client_id,status='active',
                    expires_at=excluded.expires_at,updated_at=excluded.updated_at""",
                (run, token, lease, target, "active", expires_at, updated_at),
            )
            connection.commit()
        return {
            "transferred": True,
            "run_id": run,
            "target_client_id": target,
            "owner_client_id": target,
            "lease_id": lease,
            "fencing_token": token,
            "status": "active",
            "expires_at": expires_at,
            "updated_at": updated_at,
        }

    def acquire_write_fence(
        self,
        *,
        scope_key: str,
        lease_id: str,
        owner: str,
        run_id: str,
        wave_id: str,
        ttl_seconds: float = 60.0,
    ) -> dict[str, Any]:
        now = time.time()
        ttl = max(0.05, float(ttl_seconds))
        expires_at = now + ttl
        scope = _bounded_text(scope_key or "workspace", 256)
        lease = _bounded_text(lease_id, 256)
        with self._lock, self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT * FROM write_fences WHERE scope_key=?", (scope,)).fetchone()
            if row and row["status"] == "active" and float(row["expires_at"] or 0) > now and row["lease_id"] != lease:
                current = self._write_fence_row(row)
                connection.commit()
                return {"acquired": False, "reason": "active_lease", "current": current}
            token = int(row["fencing_token"] or 0) + 1 if row else 1
            connection.execute(
                """INSERT INTO write_fences(
                    scope_key,fencing_token,lease_id,owner,run_id,wave_id,status,expires_at,updated_at
                ) VALUES(?,?,?,?,?,?,?,?,?)
                ON CONFLICT(scope_key) DO UPDATE SET
                    fencing_token=excluded.fencing_token,lease_id=excluded.lease_id,owner=excluded.owner,
                    run_id=excluded.run_id,wave_id=excluded.wave_id,status='active',
                    expires_at=excluded.expires_at,updated_at=excluded.updated_at""",
                (scope, token, lease, _bounded_text(owner, 200), _bounded_text(run_id, 256), _bounded_text(wave_id, 256), "active", expires_at, utc_now()),
            )
            connection.commit()
        return {
            "acquired": True,
            "scope_key": scope,
            "lease_id": lease,
            "owner": owner,
            "run_id": run_id,
            "wave_id": wave_id,
            "fencing_token": token,
            "expires_at": expires_at,
            "status": "active",
        }

    @staticmethod
    def _write_fence_row(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "scope_key": row["scope_key"],
            "fencing_token": int(row["fencing_token"] or 0),
            "lease_id": row["lease_id"],
            "owner": row["owner"],
            "run_id": row["run_id"],
            "wave_id": row["wave_id"],
            "status": row["status"],
            "expires_at": float(row["expires_at"] or 0),
            "updated_at": row["updated_at"],
        }

    def get_write_fence(self, scope_key: str = "workspace") -> dict[str, Any] | None:
        with self._lock, self._connect() as connection:
            row = connection.execute("SELECT * FROM write_fences WHERE scope_key=?", (_bounded_text(scope_key, 256),)).fetchone()
        return self._write_fence_row(row) if row else None

    def assert_write_fence(
        self,
        *,
        scope_key: str,
        lease_id: str,
        fencing_token: int,
        owner: str,
    ) -> dict[str, Any]:
        now = time.time()
        with self._lock, self._connect() as connection:
            row = connection.execute("SELECT * FROM write_fences WHERE scope_key=?", (_bounded_text(scope_key, 256),)).fetchone()
            if not row:
                return {"valid": False, "reason": "missing"}
            current = self._write_fence_row(row)
            if current["status"] != "active":
                return {"valid": False, "reason": "inactive", "current": current}
            if current["expires_at"] <= now:
                connection.execute(
                    "UPDATE write_fences SET status='expired', updated_at=? WHERE scope_key=? AND fencing_token=?",
                    (utc_now(), current["scope_key"], current["fencing_token"]),
                )
                current["status"] = "expired"
                return {"valid": False, "reason": "expired", "current": current}
            if current["lease_id"] != lease_id or current["fencing_token"] != int(fencing_token) or current["owner"] != owner:
                return {"valid": False, "reason": "stale", "current": current}
            return {"valid": True, "current": current}

    def renew_write_fence(
        self,
        *,
        scope_key: str,
        lease_id: str,
        fencing_token: int,
        owner: str,
        ttl_seconds: float = 60.0,
    ) -> dict[str, Any]:
        check = self.assert_write_fence(
            scope_key=scope_key, lease_id=lease_id, fencing_token=fencing_token, owner=owner
        )
        if not check.get("valid"):
            return {"renewed": False, **check}
        expires_at = time.time() + max(0.05, float(ttl_seconds))
        with self._lock, self._connect() as connection:
            cursor = connection.execute(
                """UPDATE write_fences SET expires_at=?, updated_at=?
                WHERE scope_key=? AND lease_id=? AND fencing_token=? AND owner=? AND status='active'""",
                (expires_at, utc_now(), _bounded_text(scope_key, 256), _bounded_text(lease_id, 256), int(fencing_token), _bounded_text(owner, 200)),
            )
        return {"renewed": bool(cursor.rowcount), "expires_at": expires_at, "fencing_token": int(fencing_token)}

    def release_write_fence(
        self,
        *,
        scope_key: str,
        lease_id: str,
        fencing_token: int,
        owner: str,
    ) -> bool:
        with self._lock, self._connect() as connection:
            cursor = connection.execute(
                """UPDATE write_fences SET status='released', updated_at=?
                WHERE scope_key=? AND lease_id=? AND fencing_token=? AND owner=? AND status='active'""",
                (utc_now(), _bounded_text(scope_key, 256), _bounded_text(lease_id, 256), int(fencing_token), _bounded_text(owner, 200)),
            )
        return bool(cursor.rowcount)

    @staticmethod
    def _idempotency_row(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "idempotency_key": row["idempotency_key"],
            "operation": row["operation"],
            "request_hash": row["request_hash"],
            "status": row["status"],
            "process_instance_id": row["process_instance_id"],
            "run_id": row["run_id"],
            "wave_id": row["wave_id"],
            "started_at": row["started_at"],
            "updated_at": row["updated_at"],
            "finished_at": row["finished_at"],
            "summary": _decode_idempotency_summary(row),
        }

    def claim_idempotency(
        self,
        *,
        idempotency_key: str,
        operation: str,
        request_hash: str,
        process_instance_id: str,
        run_id: str = "",
        wave_id: str = "",
    ) -> dict[str, Any]:
        key = _bounded_text(idempotency_key, 128)
        now = utc_now()
        with self._lock, self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM idempotency_records WHERE idempotency_key=?", (key,)
            ).fetchone()
            if row:
                existing = self._idempotency_row(row)
                connection.commit()
                if existing["operation"] != operation or existing["request_hash"] != request_hash:
                    return {"claimed": False, "reason": "conflict", "record": existing}
                return {"claimed": False, "reason": existing["status"], "record": existing}
            connection.execute(
                """INSERT INTO idempotency_records(
                    idempotency_key,operation,request_hash,status,process_instance_id,
                    run_id,wave_id,started_at,updated_at,finished_at,summary_json
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    key,
                    _bounded_text(operation, 100),
                    _bounded_text(request_hash, 128),
                    "in_progress",
                    _bounded_text(process_instance_id, 256),
                    _bounded_text(run_id, 256),
                    _bounded_text(wave_id, 256),
                    now,
                    now,
                    None,
                    "{}",
                ),
            )
            connection.commit()
        return {
            "claimed": True,
            "reason": "new",
            "record": {
                "idempotency_key": key,
                "operation": operation,
                "request_hash": request_hash,
                "status": "in_progress",
                "process_instance_id": process_instance_id,
                "run_id": run_id,
                "wave_id": wave_id,
                "started_at": now,
                "updated_at": now,
                "finished_at": None,
                "summary": {},
            },
        }

    def finish_idempotency(
        self,
        idempotency_key: str,
        *,
        request_hash: str,
        status: str,
        summary: dict[str, Any] | None = None,
        run_id: str = "",
        wave_id: str = "",
    ) -> dict[str, Any] | None:
        now = utc_now()
        key = _bounded_text(idempotency_key, 128)
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT request_hash FROM idempotency_records WHERE idempotency_key=?", (key,)
            ).fetchone()
            if not row or str(row["request_hash"]) != request_hash:
                return None
            summary_json, summary_codec, summary_blob, error_code, workflow_patch_preflight = _encode_idempotency_summary(summary or {}, sanitize=_sanitize)
            connection.execute(
                """UPDATE idempotency_records
                SET status=?, run_id=CASE WHEN ?<>'' THEN ? ELSE run_id END,
                    wave_id=CASE WHEN ?<>'' THEN ? ELSE wave_id END,
                    updated_at=?, finished_at=?, summary_json=?, error_code=?, workflow_patch_preflight=?, summary_codec=?, summary_blob=?
                WHERE idempotency_key=? AND request_hash=?""",
                (
                    _bounded_text(status, 64),
                    run_id, _bounded_text(run_id, 256),
                    wave_id, _bounded_text(wave_id, 256),
                    now,
                    now,
                    summary_json,
                    error_code,
                    workflow_patch_preflight,
                    summary_codec,
                    summary_blob,
                    key,
                    request_hash,
                ),
            )
            updated = connection.execute(
                "SELECT * FROM idempotency_records WHERE idempotency_key=?", (key,)
            ).fetchone()
        return self._idempotency_row(updated) if updated else None

    def get_idempotency(self, idempotency_key: str) -> dict[str, Any] | None:
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM idempotency_records WHERE idempotency_key=?",
                (_bounded_text(idempotency_key, 128),),
            ).fetchone()
        return self._idempotency_row(row) if row else None

    def mark_orphaned_idempotency(self, *, current_process_instance_id: str) -> int:
        now = utc_now()
        with self._lock, self._connect() as connection:
            rows = connection.execute(
                """SELECT * FROM idempotency_records
                WHERE status='in_progress' AND process_instance_id<>?""",
                (current_process_instance_id,),
            ).fetchall()
            for row in rows:
                summary = _decode_idempotency_summary(row)
                summary["outcome_unknown_reason"] = "mcp_process_restarted"
                summary_json, summary_codec, summary_blob, error_code, workflow_patch_preflight = _encode_idempotency_summary(summary, sanitize=_sanitize)
                connection.execute(
                    """UPDATE idempotency_records
                    SET status='unknown', updated_at=?, finished_at=?, summary_json=?, error_code=?, workflow_patch_preflight=?, summary_codec=?, summary_blob=?
                    WHERE idempotency_key=?""",
                    (now, now, summary_json, error_code, workflow_patch_preflight, summary_codec, summary_blob, row["idempotency_key"]),
                )
        return len(rows)

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        with self._lock, self._connect() as connection:
            row = connection.execute("SELECT * FROM runs WHERE run_id=?", (run_id,)).fetchone()
        if not row:
            return None
        return self._run_row(row)

    @staticmethod
    def _run_row(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "run_id": row["run_id"],
            "task_id": row["task_id"],
            "objective": row["objective"],
            "status": row["status"],
            "started_at": row["started_at"],
            "finished_at": row["finished_at"],
            "metadata": json.loads(row["metadata_json"] or "{}"),
        }

    def list_runs(self, *, limit: int = 20, status: str = "") -> list[dict[str, Any]]:
        bounded_limit = max(1, min(int(limit), 100))
        query = "SELECT * FROM runs"
        params: list[Any] = []
        if status:
            query += " WHERE status=?"
            params.append(_bounded_text(status, 64))
        query += " ORDER BY started_at DESC, run_id DESC LIMIT ?"
        params.append(bounded_limit)
        with self._lock, self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [self._run_row(row) for row in rows]

    def host_observation_eligible_runs(self) -> list[dict[str, str]]:
        """Return runs with server-owned durable proof of an organic Electron host-turn claim."""
        with self._lock, self._connect() as connection:
            rows = connection.execute(
                "SELECT run_id,metadata_json FROM runs ORDER BY started_at, run_id"
            ).fetchall()
        eligible: list[dict[str, str]] = []
        for row in rows:
            try:
                metadata = json.loads(row["metadata_json"] or "{}")
            except (TypeError, json.JSONDecodeError):
                continue
            marker = metadata.get("host_correlation") if isinstance(metadata.get("host_correlation"), dict) else {}
            if (
                marker.get("schema_version") != 1
                or marker.get("source") != "electron_pending_host_turn"
                or marker.get("eligible") is not True
            ):
                continue
            evaluation = metadata.get("evaluation") if isinstance(metadata.get("evaluation"), dict) else {}
            trace_id = _bounded_text(evaluation.get("trace_id") or "", 128).strip()
            turn_id = _bounded_text(evaluation.get("turn_id") or "", 128).strip()
            if not trace_id or not turn_id:
                continue
            eligible.append({"run_id": str(row["run_id"] or ""), "trace_id": trace_id, "turn_id": turn_id})
        return eligible

    def current_baseline_summary(self) -> dict[str, Any]:
        """Return content-free current population/coverage facts from the canonical ledger."""
        with self._lock, self._connect() as connection:
            run_rows = connection.execute(
                "SELECT run_id,status,metadata_json FROM runs ORDER BY started_at, run_id"
            ).fetchall()
            event_rows = connection.execute(
                """SELECT run_id,event_type,state_after,payload_json
                   FROM events
                   WHERE event_type IN ('failure_observed','route_selected','quality_outcome_recorded')
                      OR state_after='REPLAN'
                   ORDER BY seq"""
            ).fetchall()

        status_counts: dict[str, int] = {}
        pair_tagged_runs = 0
        pair_ids: set[str] = set()
        eligible_experimental_runs = 0
        experimental_run_ids: set[str] = set()
        controller_started_runs = 0
        controller_usage_runs = 0
        controller_complete_usage_runs = 0
        controller_cost_runs = 0
        controller_observed_runs = 0
        controller_source_runs = 0
        controller_source_counts: dict[str, int] = {}
        token_keys = ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens")
        experimental_provenance = {"representative", "benchmark", "synthetic"}
        for row in run_rows:
            status = str(row["status"] or "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
            try:
                metadata = json.loads(row["metadata_json"] or "{}")
            except (TypeError, json.JSONDecodeError):
                metadata = {}
            evaluation = metadata.get("evaluation") if isinstance(metadata.get("evaluation"), dict) else {}
            pair_id = _bounded_text(evaluation.get("pair_id") or "", 128).strip()
            if pair_id:
                pair_tagged_runs += 1
                pair_ids.add(pair_id)
            policy = _bounded_text(evaluation.get("policy") or "", 100).strip().lower()
            provenance = _bounded_text(evaluation.get("provenance") or "", 80).strip().lower()
            eligible_experiment = bool(pair_id and policy and provenance in experimental_provenance)
            if not eligible_experiment:
                continue
            eligible_experimental_runs += 1
            experimental_run_ids.add(str(row["run_id"] or ""))
            controller = evaluation.get("controller") if isinstance(evaluation.get("controller"), dict) else {}
            source = _bounded_text(controller.get("source") or "", 64).strip().lower()
            has_source = source in {"client_reported", "provider_reported"}
            has_started = self._timestamp_millis(str(controller.get("started_at") or "")) is not None
            usage_observed = [
                isinstance(controller.get(key), int)
                and not isinstance(controller.get(key), bool)
                and int(controller.get(key)) >= 0
                for key in token_keys
            ]
            has_usage = any(usage_observed)
            has_complete_usage = all(usage_observed)
            cost = controller.get("monetary_cost")
            has_cost = isinstance(cost, (int, float)) and not isinstance(cost, bool) and float(cost) >= 0
            controller_started_runs += int(has_started)
            controller_usage_runs += int(has_usage)
            controller_complete_usage_runs += int(has_complete_usage)
            controller_cost_runs += int(has_cost)
            controller_observed_runs += int(has_started or has_usage or has_cost)
            controller_source_runs += int(has_source)
            if has_source:
                controller_source_counts[source] = controller_source_counts.get(source, 0) + 1

        replan_transitions = 0
        failure_event_count = 0
        failure_classes: dict[str, int] = {}
        route_event_count = 0
        route_counts: dict[str, int] = {}
        quality_event_count = 0
        quality_runs: set[str] = set()
        latest_quality_by_run: dict[str, dict[str, Any]] = {}
        for row in event_rows:
            event_type = str(row["event_type"] or "")
            if str(row["state_after"] or "") == "REPLAN":
                replan_transitions += 1
            try:
                payload = json.loads(row["payload_json"] or "{}")
            except (TypeError, json.JSONDecodeError):
                payload = {}
            if event_type == "failure_observed":
                failure_event_count += 1
                failure_class = _bounded_text(payload.get("failure_class") or "UNKNOWN", 80).strip().upper() or "UNKNOWN"
                failure_classes[failure_class] = failure_classes.get(failure_class, 0) + 1
            elif event_type == "route_selected":
                route_event_count += 1
                route = _bounded_text(
                    payload.get("resolved") or payload.get("route_resolved") or "unknown", 80
                ).strip().lower() or "unknown"
                route_counts[route] = route_counts.get(route, 0) + 1
            elif event_type == "quality_outcome_recorded":
                quality_event_count += 1
                quality_run_id = str(row["run_id"] or "")
                quality_runs.add(quality_run_id)
                latest_quality_by_run[quality_run_id] = payload

        run_count = len(run_rows)

        def coverage(count: int) -> float | None:
            return round(count / run_count, 6) if run_count else None

        def experimental_coverage(count: int) -> float | None:
            return round(count / eligible_experimental_runs, 6) if eligible_experimental_runs else None

        experimental_quality_run_ids = experimental_run_ids & set(latest_quality_by_run)
        quality_outcome_runs = len(experimental_quality_run_ids)
        quality_oracle_runs = 0
        quality_oracle_failed_runs = 0
        quality_critical_defect_runs = 0
        quality_critical_defect_nonzero_runs = 0
        quality_noncritical_defect_runs = 0
        quality_manual_fix_runs = 0
        quality_manual_fix_required_runs = 0
        quality_regression_escape_runs = 0
        quality_regression_escape_true_runs = 0
        quality_rollback_runs = 0
        quality_rollback_required_runs = 0
        quality_maintainability_runs = 0
        quality_observation_window_runs = 0
        quality_source_counts: dict[str, int] = {}
        for quality_run_id in experimental_quality_run_ids:
            outcome = latest_quality_by_run[quality_run_id]
            source = _bounded_text(outcome.get("source") or "", 128).strip()
            if source:
                quality_source_counts[source] = quality_source_counts.get(source, 0) + 1
            oracle_pass = outcome.get("oracle_pass")
            if isinstance(oracle_pass, bool):
                quality_oracle_runs += 1
                quality_oracle_failed_runs += int(not oracle_pass)
            critical_defects = outcome.get("critical_defect_count")
            if isinstance(critical_defects, int) and not isinstance(critical_defects, bool) and critical_defects >= 0:
                quality_critical_defect_runs += 1
                quality_critical_defect_nonzero_runs += int(critical_defects > 0)
            noncritical_defects = outcome.get("noncritical_defect_count")
            if isinstance(noncritical_defects, int) and not isinstance(noncritical_defects, bool) and noncritical_defects >= 0:
                quality_noncritical_defect_runs += 1
            manual_fix_required = outcome.get("manual_fix_required")
            if isinstance(manual_fix_required, bool):
                quality_manual_fix_runs += 1
                quality_manual_fix_required_runs += int(manual_fix_required)
            regression_escape = outcome.get("regression_escape")
            if isinstance(regression_escape, bool):
                quality_regression_escape_runs += 1
                quality_regression_escape_true_runs += int(regression_escape)
            rollback_required = outcome.get("rollback_required")
            if isinstance(rollback_required, bool):
                quality_rollback_runs += 1
                quality_rollback_required_runs += int(rollback_required)
            maintainability = _bounded_text(outcome.get("maintainability_gate") or "", 32).strip().lower()
            if maintainability in {"pass", "fail", "not_applicable", "unknown"}:
                quality_maintainability_runs += 1
            if _bounded_text(outcome.get("observation_window_end") or "", 128).strip():
                quality_observation_window_runs += 1

        quality_hold_reasons: list[str] = []
        if eligible_experimental_runs == 0:
            quality_hold_reasons.append("no_eligible_experimental_runs")
        else:
            if quality_outcome_runs < eligible_experimental_runs:
                quality_hold_reasons.append("quality_outcome_coverage_incomplete")
            if quality_oracle_runs < eligible_experimental_runs:
                quality_hold_reasons.append("oracle_quality_evidence_incomplete")
            if quality_critical_defect_runs < eligible_experimental_runs:
                quality_hold_reasons.append("critical_defect_evidence_incomplete")
            if quality_oracle_failed_runs:
                quality_hold_reasons.append("oracle_failure_observed")
            if quality_critical_defect_nonzero_runs:
                quality_hold_reasons.append("critical_defect_observed")
            if quality_regression_escape_true_runs:
                quality_hold_reasons.append("regression_escape_observed")
            if quality_rollback_required_runs:
                quality_hold_reasons.append("rollback_required_observed")

        promotion_hold_reasons: list[str] = []
        if eligible_experimental_runs == 0:
            promotion_hold_reasons.append("no_eligible_experimental_runs")
        elif controller_cost_runs < eligible_experimental_runs:
            promotion_hold_reasons.append("controller_cost_coverage_incomplete")

        return {
            "schema_version": 1,
            "source": "orchestration_ledger",
            "run_count": run_count,
            "run_status_counts": dict(sorted(status_counts.items())),
            "replan_transitions": replan_transitions,
            "failure_events": {
                "count": failure_event_count,
                "classes": dict(sorted(failure_classes.items())),
            },
            "route_decisions": {
                "count": route_event_count,
                "resolved_counts": dict(sorted(route_counts.items())),
                "basis": "route_selected_events",
            },
            "pairing": {
                "pair_tagged_runs": pair_tagged_runs,
                "unique_pair_ids": len(pair_ids),
            },
            "quality_outcomes": {
                "event_count": quality_event_count,
                "runs_with_outcome": len(quality_runs),
                "run_coverage": coverage(len(quality_runs)),
                "all_history_basis": "explicit_quality_outcome_recorded_events",
                "eligible_experimental_runs": eligible_experimental_runs,
                "experimental_runs_with_outcome": quality_outcome_runs,
                "experimental_coverage_rate": experimental_coverage(quality_outcome_runs),
                "experimental_coverage_status": "observed" if eligible_experimental_runs else "no_eligible_experimental_runs",
                "runs_with_oracle_observation": quality_oracle_runs,
                "runs_with_critical_defect_count": quality_critical_defect_runs,
                "runs_with_noncritical_defect_count": quality_noncritical_defect_runs,
                "runs_with_manual_fix_observation": quality_manual_fix_runs,
                "runs_with_regression_escape_observation": quality_regression_escape_runs,
                "runs_with_rollback_observation": quality_rollback_runs,
                "runs_with_maintainability_gate": quality_maintainability_runs,
                "runs_with_observation_window_end": quality_observation_window_runs,
                "source_counts": dict(sorted(quality_source_counts.items())),
                "oracle_failed_runs": quality_oracle_failed_runs,
                "critical_defect_nonzero_runs": quality_critical_defect_nonzero_runs,
                "manual_fix_required_runs": quality_manual_fix_required_runs,
                "regression_escape_true_runs": quality_regression_escape_true_runs,
                "rollback_required_runs": quality_rollback_required_runs,
                "denominator": "explicit_evaluation_enrollment_v1",
                "eligibility": {
                    "requires_pair_id": True,
                    "requires_policy": True,
                    "allowed_provenance": sorted(experimental_provenance),
                    "status_independent": True,
                    "accepted_state_alone_is_not_quality_evidence": True,
                    "historical_backfill_requires_exact_evidence": True,
                },
                "unknown_is_not_good": True,
                "promotion_quality": {
                    "status": "eligible_for_analysis" if not quality_hold_reasons else "hold",
                    "hold_reasons": quality_hold_reasons,
                    "requires_complete_quality_outcome_coverage": True,
                    "requires_complete_oracle_coverage": True,
                    "requires_complete_critical_defect_coverage": True,
                    "automatic_promotion": False,
                },
            },
            "controller_coverage": {
                "eligible_experimental_runs": eligible_experimental_runs,
                "runs_observed": controller_observed_runs,
                "runs_with_started_at": controller_started_runs,
                "runs_with_token_usage": controller_usage_runs,
                "runs_with_complete_token_usage": controller_complete_usage_runs,
                "runs_with_monetary_cost": controller_cost_runs,
                "runs_with_source": controller_source_runs,
                "source_counts": dict(sorted(controller_source_counts.items())),
                "observed_rate": experimental_coverage(controller_observed_runs),
                "started_at_rate": experimental_coverage(controller_started_runs),
                "token_usage_rate": experimental_coverage(controller_usage_runs),
                "complete_token_usage_rate": experimental_coverage(controller_complete_usage_runs),
                "monetary_cost_rate": experimental_coverage(controller_cost_runs),
                "source_rate": experimental_coverage(controller_source_runs),
                "denominator": "explicit_evaluation_enrollment_v1",
                "eligibility": {
                    "requires_pair_id": True,
                    "requires_policy": True,
                    "allowed_provenance": sorted(experimental_provenance),
                    "status_independent": True,
                    "organic_trace_turn_identity_alone_is_ineligible": True,
                },
                "unknown_is_not_zero": True,
                "promotion_economics": {
                    "status": "eligible_for_analysis" if not promotion_hold_reasons else "hold",
                    "hold_reasons": promotion_hold_reasons,
                    "requires_complete_controller_cost_coverage": True,
                    "automatic_promotion": False,
                },
            },
            "content_free": True,
        }

    def organic_rework_summary(
        self,
        *,
        since: str = "",
        until: str = "",
        limit: int = 500,
    ) -> dict[str, Any]:
        """Summarize organic ChatWeb+MCP accepted-result rework without synthetic load."""
        bounded_limit = max(1, min(int(limit), 5000))
        since_value = _bounded_text(since, 64).strip()
        until_value = _bounded_text(until, 64).strip()
        clauses = [
            "status='accepted'",
            "(json_extract(metadata_json, '$.evaluation.provenance') IS NULL OR lower(json_extract(metadata_json, '$.evaluation.provenance'))='representative')",
            "(json_extract(metadata_json, '$.evaluation.policy') IS NULL OR lower(json_extract(metadata_json, '$.evaluation.policy'))='chatweb_mcp')",
        ]
        params: list[Any] = []
        if since_value:
            clauses.append("started_at>=?")
            params.append(since_value)
        if until_value:
            clauses.append("started_at<=?")
            params.append(until_value)
        query = f"SELECT * FROM runs WHERE {' AND '.join(clauses)} ORDER BY started_at, run_id LIMIT ?"
        with self._lock, self._connect() as connection:
            rows = connection.execute(query, [*params, bounded_limit + 1]).fetchall()
        truncated = len(rows) > bounded_limit
        selected = rows[:bounded_limit]

        first_pass_tta: list[int] = []
        repaired_tta: list[int] = []
        first_pass = 0
        repaired = 0
        total_replans = 0
        included = 0
        explicit_model_route = 0
        for row in selected:
            run_id = str(row["run_id"])
            actual_routes = {
                str(delegation.get("route_resolved") or "").strip().lower()
                for wave in self.list_waves(run_id)
                for delegation in self.list_delegations(str(wave["wave_id"]))
                if str(delegation.get("route_resolved") or "").strip()
            }
            if any(route not in {"unknown", "deterministic", "mcp_deterministic"} for route in actual_routes):
                explicit_model_route += 1
                continue
            economics = self.accepted_result_economics(run_id)
            route = str((economics.get("route") or {}).get("resolved") or "unknown").strip().lower()
            if route not in {"", "unknown", "deterministic", "mcp_deterministic"}:
                explicit_model_route += 1
                continue
            included += 1
            replan_count = int((economics.get("repair") or {}).get("replan_count") or 0)
            total_replans += replan_count
            tta = economics.get("tta_ms")
            if replan_count:
                repaired += 1
                if isinstance(tta, int) and not isinstance(tta, bool) and tta >= 0:
                    repaired_tta.append(tta)
            else:
                first_pass += 1
                if isinstance(tta, int) and not isinstance(tta, bool) and tta >= 0:
                    first_pass_tta.append(tta)

        preflight_clauses = [
            "operation='agent_workflow'",
            "status='failed'",
            "(workflow_patch_preflight=1 OR (summary_codec='plain_json' AND json_extract(summary_json, '$.workflow_patch_preflight')=1))",
        ]
        preflight_params: list[Any] = []
        if since_value:
            preflight_clauses.append("started_at>=?")
            preflight_params.append(since_value)
        if until_value:
            preflight_clauses.append("started_at<=?")
            preflight_params.append(until_value)
        with self._lock, self._connect() as connection:
            preflight_rows = connection.execute(
                f"""SELECT COALESCE(NULLIF(error_code, ''), json_extract(summary_json, '$.error_code'), 'unknown') AS error_code,
                            COUNT(*) AS count
                    FROM idempotency_records
                    WHERE {' AND '.join(preflight_clauses)}
                    GROUP BY error_code
                    ORDER BY count DESC, error_code""",
                preflight_params,
            ).fetchall()
        preflight_errors = {str(row["error_code"]): int(row["count"]) for row in preflight_rows}

        def percentile(values: list[int], percentile_value: int) -> int | None:
            if not values:
                return None
            ordered = sorted(values)
            rank = max(1, min(len(ordered), (len(ordered) * percentile_value + 99) // 100))
            return int(ordered[rank - 1])

        first_p50 = percentile(first_pass_tta, 50)
        first_p90 = percentile(first_pass_tta, 90)
        repaired_p50 = percentile(repaired_tta, 50)
        repaired_p90 = percentile(repaired_tta, 90)
        return {
            "schema_version": 1,
            "baseline_policy": "chatweb_mcp",
            "window": {
                "since": since_value or None,
                "until": until_value or None,
                "basis": "run_started_at",
            },
            "accepted_runs_scanned": len(selected),
            "accepted_runs": included,
            "accepted_runs_truncated": truncated,
            "excluded": {"explicit_model_route": explicit_model_route},
            "first_pass_accepted": first_pass,
            "repaired_accepted": repaired,
            "first_pass_rate": round(first_pass / included, 6) if included else None,
            "repaired_rate": round(repaired / included, 6) if included else None,
            "repair": {"replan_count": total_replans},
            "preflight_avoided": {
                "count": sum(preflight_errors.values()),
                "error_codes": preflight_errors,
                "meaning": "known no-write patch failures stopped before orchestration run creation",
            },
            "tta_ms": {
                "first_pass_p50": first_p50,
                "first_pass_p90": first_p90,
                "repaired_p50": repaired_p50,
                "repaired_p90": repaired_p90,
                "repaired_to_first_pass_p50_multiplier": (
                    round(repaired_p50 / first_p50, 6)
                    if isinstance(repaired_p50, int) and isinstance(first_p50, int) and first_p50 > 0
                    else None
                ),
                "repaired_to_first_pass_p90_multiplier": (
                    round(repaired_p90 / first_p90, 6)
                    if isinstance(repaired_p90, int) and isinstance(first_p90, int) and first_p90 > 0
                    else None
                ),
            },
            "cost_roi_policy": "use only causally attributed complete accepted-result cost; unknown is not zero",
            "provenance_filter": "exclude benchmark/synthetic and explicit model-routed accepted runs",
            "model_free": True,
            "content_free": True,
        }

    @staticmethod
    def _timestamp_millis(value: Any) -> int | None:
        text = str(value or "").strip()
        if not text:
            return None
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return int(parsed.timestamp() * 1000)

    def run_phase_timing(self, run_id: str) -> dict[str, Any]:
        run = self.get_run(run_id)
        if run is None:
            return {
                "run_id": run_id,
                "source": "eocl_event_timestamps",
                "segments": [],
                "by_state_ms": {},
                "methodology_phase_ms": {},
                "tta_ms": None,
                "observed_ms": 0,
                "unattributed_ms": None,
                "tta_coverage": None,
                "coverage_floor": 0.90,
                "coverage_target": 0.95,
                "meets_coverage_floor": False,
                "meets_coverage_target": False,
                "complete": False,
            }
        points: list[dict[str, Any]] = []
        for event in self.list_events(run_id):
            state = str(event.get("state_after") or "").strip()
            started_ms = self._timestamp_millis(event.get("event_time"))
            if not state or started_ms is None:
                continue
            if points and points[-1]["state"] == state:
                continue
            points.append({"state": state, "started_at": event.get("event_time"), "started_ms": started_ms, "seq": event.get("seq")})
        started_ms = self._timestamp_millis(run.get("started_at"))
        finished_ms = self._timestamp_millis(run.get("finished_at"))
        segments: list[dict[str, Any]] = []
        by_state: dict[str, int] = {}
        for index, point in enumerate(points):
            end_ms = points[index + 1]["started_ms"] if index + 1 < len(points) else finished_ms
            ended_at = points[index + 1]["started_at"] if index + 1 < len(points) else run.get("finished_at")
            duration_ms = max(0, int(end_ms - point["started_ms"])) if end_ms is not None else None
            segments.append({"state": point["state"], "start_seq": point["seq"], "started_at": point["started_at"], "ended_at": ended_at, "duration_ms": duration_ms})
            if duration_ms is not None:
                by_state[point["state"]] = by_state.get(point["state"], 0) + duration_ms
        methodology_phase_ms = {
            "preflight_ms": by_state.get("PREFLIGHT"),
            "ready_wait_ms": by_state.get("READY"),
            "dispatch_window_ms": by_state.get("ROUTED"),
            "execution_window_ms": by_state.get("EXECUTING"),
            "proof_ms": by_state.get("PROVING"),
            "accept_wait_ms": by_state.get("ACCEPTING"),
            "replan_ms": by_state.get("REPLAN"),
        }
        observed_ms = sum(by_state.values())
        tta_ms = (
            max(0, int(finished_ms - started_ms))
            if started_ms is not None and finished_ms is not None and finished_ms >= started_ms
            else None
        )
        unattributed_ms = max(0, tta_ms - observed_ms) if tta_ms is not None else None
        tta_coverage = None
        if tta_ms is not None and tta_ms > 0:
            tta_coverage = round(min(1.0, observed_ms / tta_ms), 6)
        coverage_floor = 0.90
        coverage_target = 0.95
        return {
            "run_id": run_id,
            "source": "eocl_event_timestamps",
            "segments": segments[-64:],
            "by_state_ms": by_state,
            "methodology_phase_ms": methodology_phase_ms,
            "tta_ms": tta_ms,
            "observed_ms": observed_ms,
            "unattributed_ms": unattributed_ms,
            "tta_coverage": tta_coverage,
            "coverage_floor": coverage_floor,
            "coverage_target": coverage_target,
            "meets_coverage_floor": bool(tta_coverage is not None and tta_coverage >= coverage_floor),
            "meets_coverage_target": bool(tta_coverage is not None and tta_coverage >= coverage_target),
            "complete": bool(run.get("finished_at")) and bool(points),
        }

    @staticmethod
    def _flight_event(event: dict[str, Any]) -> dict[str, Any]:
        payload = event.get("payload") or {}
        encoded = _json(payload).encode("utf-8")
        if len(encoded) > 2_000:
            payload = {"bounded": True, "bytes": len(encoded), "sha256": hashlib.sha256(encoded).hexdigest()}
        return {
            "seq": int(event.get("seq") or 0),
            "event_type": str(event.get("event_type") or ""),
            "state_before": str(event.get("state_before") or ""),
            "state_after": str(event.get("state_after") or ""),
            "event_time": str(event.get("event_time") or ""),
            "wave_id": str(event.get("wave_id") or ""),
            "delegation_id": str(event.get("delegation_id") or ""),
            "payload": payload,
        }

    def flight_recorder(self, run_id: str, *, after_seq: int | None = None, limit: int = 40) -> dict[str, Any]:
        bounded_limit = max(1, min(int(limit), 100))
        if after_seq is None:
            all_events = self.list_events(run_id)
            selected = all_events[-bounded_limit:]
            has_more = len(all_events) > len(selected)
            requested_after = int(selected[0]["seq"]) - 1 if selected else 0
        else:
            requested_after = max(0, int(after_seq))
            delta = self.list_events_since(run_id, after_seq=requested_after, limit=bounded_limit)
            selected = delta["events"]
            has_more = bool(delta["has_more"])
        events = [self._flight_event(item) for item in selected]
        return {
            "run_id": run_id,
            "after_seq": requested_after,
            "events": events,
            "next_after_seq": int(events[-1]["seq"]) if events else requested_after,
            "has_more": has_more,
            "phase_timing": self.run_phase_timing(run_id),
        }

    def evidence_query(
        self,
        run_id: str,
        *,
        wave_id: str = "",
        after_seq: int | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        """Return bounded content-free evidence for resume and filtered audit."""
        run = self.get_run(run_id)
        if run is None:
            raise ValueError("orchestration run does not exist")
        bounded_limit = max(1, min(int(limit), 100))
        requested_wave = _bounded_text(wave_id, 256).strip()
        all_waves = self.list_waves(run_id)
        selected_waves = all_waves
        if requested_wave:
            selected_waves = [item for item in all_waves if str(item.get("wave_id") or "") == requested_wave]
            if not selected_waves:
                raise ValueError("orchestration wave does not belong to run")

        event_query = "SELECT * FROM events WHERE run_id=?"
        event_params: list[Any] = [_bounded_text(run_id, 256)]
        if requested_wave:
            event_query += " AND wave_id=?"
            event_params.append(requested_wave)
        if after_seq is None:
            event_query += " ORDER BY seq DESC LIMIT ?"
            event_params.append(bounded_limit + 1)
            with self._lock, self._connect() as connection:
                rows = connection.execute(event_query, event_params).fetchall()
            has_more = len(rows) > bounded_limit
            selected_rows = list(reversed(rows[:bounded_limit]))
            requested_after = int(selected_rows[0]["seq"] or 0) - 1 if selected_rows else 0
            omitted_earlier_events = has_more
        else:
            requested_after = max(0, int(after_seq))
            event_query += " AND seq>? ORDER BY seq LIMIT ?"
            event_params.extend([requested_after, bounded_limit + 1])
            with self._lock, self._connect() as connection:
                rows = connection.execute(event_query, event_params).fetchall()
            has_more = len(rows) > bounded_limit
            selected_rows = rows[:bounded_limit]
            omitted_earlier_events = False

        events = [self._flight_event(self._event_row(row)) for row in selected_rows]
        proofs = self.list_proofs(run_id, wave_id=requested_wave or None)[-bounded_limit:]
        checkpoints = self.list_checkpoints(run_id, wave_id=requested_wave or None)[-bounded_limit:]
        delegations = [
            item
            for wave in selected_waves
            for item in self.list_delegations(str(wave.get("wave_id") or ""))
        ][-bounded_limit:]
        capsule = self.latest_handoff_capsule(run_id=run_id)
        capsule_locator = None
        if capsule is not None:
            capsule_locator = {
                "capsule_id": capsule.get("capsule_id"),
                "run_id": capsule.get("run_id"),
                "wave_id": capsule.get("wave_id"),
                "status": capsule.get("status"),
                "created_at": capsule.get("created_at"),
                "sha256": capsule.get("sha256"),
                "bytes": capsule.get("bytes"),
                "artifact_ref": handoff_capsule_artifact_ref(capsule),
            }

        proof_view = [{
            "proof_id": item.get("proof_id"),
            "wave_id": item.get("wave_id"),
            "stage_id": item.get("stage_id"),
            "status": item.get("status"),
            "duration_ms": item.get("duration_ms"),
            "exit_code": item.get("exit_code"),
            "cache_hit": item.get("cache_hit"),
            "finished_at": item.get("finished_at"),
            "artifact_ref": proof_artifact_ref(item),
        } for item in proofs]
        delegation_view = [{
            "delegation_id": item.get("delegation_id"),
            "wave_id": item.get("wave_id"),
            "authority_owner": item.get("authority_owner"),
            "route_resolved": item.get("route_resolved"),
            "model": item.get("model"),
            "effort": item.get("effort"),
            "status": item.get("status"),
            "started_at": item.get("started_at"),
            "finished_at": item.get("finished_at"),
        } for item in delegations]
        checkpoint_view = [{
            "checkpoint_id": item.get("checkpoint_id"),
            "wave_id": item.get("wave_id"),
            "git_head": item.get("git_head"),
            "proof_fingerprint": item.get("proof_fingerprint"),
            "status": item.get("status"),
            "created_at": item.get("created_at"),
        } for item in checkpoints]
        wave_view = selected_waves[-bounded_limit:]
        return {
            "schema_version": 1,
            "query": {
                "run_id": run_id,
                "wave_id": requested_wave or None,
                "after_seq": requested_after,
                "limit": bounded_limit,
                "mode": "model_free",
            },
            "run": run,
            "waves": wave_view,
            "events": events,
            "proofs": proof_view,
            "delegations": delegation_view,
            "checkpoints": checkpoint_view,
            "latest_handoff_capsule": capsule_locator,
            "phase_timing": self.run_phase_timing(run_id),
            "accepted_result": self.accepted_result_economics(run_id),
            "relationships": {
                "task_id": run.get("task_id"),
                "run_id": run_id,
                "wave_ids": [item.get("wave_id") for item in wave_view],
                "event_seqs": [item.get("seq") for item in events],
                "proof_ids": [item.get("proof_id") for item in proof_view],
                "delegation_ids": [item.get("delegation_id") for item in delegation_view],
                "checkpoint_ids": [item.get("checkpoint_id") for item in checkpoint_view],
                "capsule_id": capsule_locator.get("capsule_id") if capsule_locator else None,
            },
            "next_after_seq": int(events[-1]["seq"]) if events else requested_after,
            "has_more": has_more,
            "omitted_earlier_events": omitted_earlier_events,
            "model_free": True,
            "content_free": True,
            "raw_transcript_included": False,
            "integrity": self.verify_chain(run_id),
        }

    @staticmethod
    def _session_event_priority(event: dict[str, Any]) -> tuple[int, str]:
        event_type = str(event.get("event_type") or "").lower()
        state_after = str(event.get("state_after") or "").upper()
        if any(token in event_type for token in ("failure", "replan", "reject", "blocked", "abort", "error")) or state_after in {"REPLAN", "BLOCKED", "ABORTED"}:
            return 0, "critical"
        if any(token in event_type for token in ("accept", "checkpoint")) or state_after in {"ACCEPTING", "CHECKPOINTED"}:
            return 1, "acceptance"
        if any(token in event_type for token in ("proof", "prove", "verification", "test", "build")) or state_after == "PROVING":
            return 2, "proof"
        if any(token in event_type for token in ("route", "delegation", "model", "provider")) or state_after in {"ROUTED", "EXECUTING"}:
            return 3, "route"
        if any(token in event_type for token in ("context", "prepare", "read", "search")) or state_after in {"PREFLIGHT", "READY"}:
            return 4, "context"
        return 5, "recent"

    def session_query(
        self,
        run_id: str,
        *,
        wave_id: str = "",
        limit: int = 12,
    ) -> dict[str, Any]:
        """Project the highest-value durable resume evidence under one item budget."""
        budget = max(1, min(int(limit), 50))
        evidence = self.evidence_query(run_id, wave_id=wave_id, limit=100)
        candidates: list[tuple[int, int, dict[str, Any]]] = []

        for event in evidence.get("events", []):
            if not isinstance(event, dict):
                continue
            rank, priority = self._session_event_priority(event)
            seq = int(event.get("seq") or 0)
            candidates.append((rank, -seq, {
                "kind": "event",
                "priority": priority,
                "seq": seq,
                "wave_id": event.get("wave_id"),
                "delegation_id": event.get("delegation_id"),
                "event_type": event.get("event_type"),
                "state_before": event.get("state_before"),
                "state_after": event.get("state_after"),
                "event_time": event.get("event_time"),
                "payload": event.get("payload"),
            }))

        for index, proof in enumerate(reversed(evidence.get("proofs", []))):
            if not isinstance(proof, dict):
                continue
            candidates.append((2, index, {
                "kind": "proof",
                "priority": "proof",
                "proof_id": proof.get("proof_id"),
                "wave_id": proof.get("wave_id"),
                "stage_id": proof.get("stage_id"),
                "status": proof.get("status"),
                "duration_ms": proof.get("duration_ms"),
                "exit_code": proof.get("exit_code"),
                "cache_hit": proof.get("cache_hit"),
                "finished_at": proof.get("finished_at"),
                "artifact_ref": proof.get("artifact_ref"),
            }))

        for index, checkpoint in enumerate(reversed(evidence.get("checkpoints", []))):
            if not isinstance(checkpoint, dict):
                continue
            candidates.append((1, index, {"kind": "checkpoint", "priority": "acceptance", **checkpoint}))

        for index, delegation in enumerate(reversed(evidence.get("delegations", []))):
            if not isinstance(delegation, dict):
                continue
            candidates.append((3, index, {"kind": "delegation", "priority": "route", **delegation}))

        capsule = evidence.get("latest_handoff_capsule")
        if isinstance(capsule, dict):
            candidates.append((1, -1, {
                "kind": "handoff",
                "priority": "acceptance",
                "capsule_id": capsule.get("capsule_id"),
                "wave_id": capsule.get("wave_id"),
                "status": capsule.get("status"),
                "created_at": capsule.get("created_at"),
                "artifact_ref": capsule.get("artifact_ref"),
            }))

        ordered = sorted(candidates, key=lambda item: (item[0], item[1], str(item[2].get("kind") or "")))
        selected = [item[2] for item in ordered[:budget]]
        priority_counts: dict[str, int] = {}
        for item in selected:
            priority = str(item.get("priority") or "recent")
            priority_counts[priority] = priority_counts.get(priority, 0) + 1

        economics = evidence.get("accepted_result") if isinstance(evidence.get("accepted_result"), dict) else {}
        provider = economics.get("provider_economics") if isinstance(economics.get("provider_economics"), dict) else {}
        candidate = economics.get("candidate_economics") if isinstance(economics.get("candidate_economics"), dict) else {}
        run = evidence.get("run") if isinstance(evidence.get("run"), dict) else {}
        waves = evidence.get("waves") if isinstance(evidence.get("waves"), list) else []
        active_wave = waves[-1] if waves else None
        return {
            "schema_version": 1,
            "query": {
                "run_id": run_id,
                "wave_id": str(wave_id or "").strip() or None,
                "limit": budget,
                "mode": "model_free_priority",
            },
            "run": {
                "run_id": run.get("run_id"),
                "task_id": run.get("task_id"),
                "status": run.get("status"),
                "started_at": run.get("started_at"),
                "finished_at": run.get("finished_at"),
            },
            "wave": active_wave,
            "items": selected,
            "pruning": {
                "candidate_items": len(candidates),
                "returned_items": len(selected),
                "omitted_items": max(0, len(candidates) - len(selected)),
                "priority_counts": priority_counts,
            },
            "accepted_result": {
                "accepted": bool(economics.get("accepted")),
                "first_pass_accepted": bool(economics.get("first_pass_accepted")),
                "tta_ms": economics.get("tta_ms"),
                "route": economics.get("route"),
                "repair": economics.get("repair"),
                "proof": economics.get("proof"),
                "provider_economics": {
                    "usage_event_count": provider.get("usage_event_count", 0),
                    "cost_complete": bool(provider.get("cost_complete")),
                    "provider_cost": provider.get("provider_cost"),
                    "attribution_complete": bool(provider.get("attribution_complete")),
                    "attributed_provider_cost": provider.get("attributed_provider_cost"),
                    "measurement": provider.get("measurement", "unobserved"),
                },
                "candidate_economics": {
                    "observations": candidate.get("observations", 0),
                    "estimated_credits": candidate.get("estimated_credits"),
                    "measurement": candidate.get("measurement", "unobserved"),
                },
            },
            "relationships": evidence.get("relationships"),
            "integrity": evidence.get("integrity"),
            "model_free": True,
            "content_free": True,
            "raw_transcript_included": False,
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
        self.expire_controller_leases()
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

    def peek_current_active_run(self, *, task_id: str = "") -> dict[str, Any] | None:
        """Read the newest active run without triggering lease maintenance."""
        with self._lock, self._connect() as connection:
            if task_id:
                row = connection.execute(
                    "SELECT * FROM runs WHERE task_id=? AND status='active' ORDER BY started_at DESC LIMIT 1",
                    (_bounded_text(task_id, 256),),
                ).fetchone()
            else:
                row = connection.execute(
                    "SELECT * FROM runs WHERE status='active' ORDER BY started_at DESC LIMIT 1"
                ).fetchone()
        return self._run_row(row) if row else None

    def _stale_active_run_candidates(
        self,
        connection: sqlite3.Connection,
        *,
        now_ts: float,
        cutoff: str,
    ) -> list[tuple[str, str]]:
        """Return inactive active runs that currently have no live ownership."""
        stale: list[tuple[str, str]] = []
        rows = connection.execute(
            """SELECT r.run_id, r.started_at,
                      MAX(e.event_time) AS event_time,
                      MAX(w.started_at) AS wave_started_at,
                      MAX(w.finished_at) AS wave_finished_at,
                      MAX(b.updated_at) AS background_updated_at,
                      MAX(l.updated_at) AS lane_updated_at,
                      MAX(h.created_at) AS handoff_created_at
               FROM runs r
               LEFT JOIN events e ON e.run_id=r.run_id
               LEFT JOIN waves w ON w.run_id=r.run_id
               LEFT JOIN background_operations b ON b.run_id=r.run_id
               LEFT JOIN agent_lanes l ON l.run_id=r.run_id
               LEFT JOIN handoff_capsules h ON h.run_id=r.run_id
               WHERE r.status='active'
               GROUP BY r.run_id, r.started_at"""
        ).fetchall()
        for row in rows:
            run_id = str(row["run_id"])
            latest_event = connection.execute(
                "SELECT state_after FROM events WHERE run_id=? ORDER BY seq DESC LIMIT 1",
                (run_id,),
            ).fetchone()
            if latest_event and str(latest_event["state_after"] or "").upper() == "ACCEPTING":
                continue
            if connection.execute(
                "SELECT 1 FROM background_operations WHERE run_id=? AND status='running' LIMIT 1",
                (run_id,),
            ).fetchone():
                continue
            if connection.execute(
                "SELECT 1 FROM agent_lanes WHERE run_id=? AND lifecycle IN ('active','waiting','idle') LIMIT 1",
                (run_id,),
            ).fetchone():
                continue
            if connection.execute(
                "SELECT 1 FROM write_fences WHERE run_id=? AND status='active' AND expires_at>? LIMIT 1",
                (run_id, now_ts),
            ).fetchone():
                continue
            if connection.execute(
                "SELECT 1 FROM controller_leases WHERE run_id=? AND status='active' AND expires_at>? LIMIT 1",
                (run_id, now_ts),
            ).fetchone():
                continue
            activity = max(
                str(row[key] or "")
                for key in (
                    "started_at", "event_time", "wave_started_at", "wave_finished_at",
                    "background_updated_at", "lane_updated_at", "handoff_created_at",
                )
            )
            if activity and activity < cutoff:
                latest_wave = connection.execute(
                    "SELECT wave_id FROM waves WHERE run_id=? ORDER BY ordinal DESC LIMIT 1",
                    (run_id,),
                ).fetchone()
                stale.append((run_id, str(latest_wave["wave_id"]) if latest_wave else ""))
        return stale

    def stale_run_candidates(
        self,
        *,
        stale_after_seconds: float = 24 * 60 * 60,
        now: float | None = None,
    ) -> list[str]:
        """Read-only current health view of stale active runs with no live ownership."""
        now_ts = time.time() if now is None else float(now)
        self.expire_controller_leases(now=now_ts)
        threshold = max(60.0, float(stale_after_seconds))
        cutoff = datetime.fromtimestamp(now_ts - threshold, timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        with self._lock, self._connect() as connection:
            candidates = self._stale_active_run_candidates(connection, now_ts=now_ts, cutoff=cutoff)
        return [run_id for run_id, _wave_id in candidates]

    def reconcile_stale_runs(
        self,
        *,
        stale_after_seconds: float = 24 * 60 * 60,
        now: float | None = None,
        close_stale_active: bool = True,
    ) -> list[str]:
        """Close abandoned active runs without touching work that still has live ownership.

        This is lifecycle hygiene, not garbage collection: rows and evidence are retained.
        A run is protected while it owns a live background operation, an active/waiting
        agent lane, or a non-expired write/controller fence. Only inactivity older than
        the bounded threshold becomes ``stale`` when ``close_stale_active`` is true.
        Runtime startup uses false so unrelated stale candidates remain read-only health
        signals until an operator explicitly reconciles them. Terminal-parent wave
        contradictions are always repaired. The return value is the set of active stale
        runs closed by this call; use ``stale_run_candidates`` for current health.
        """

        now_ts = time.time() if now is None else float(now)
        self.expire_controller_leases(now=now_ts)
        threshold = max(60.0, float(stale_after_seconds))
        cutoff = datetime.fromtimestamp(now_ts - threshold, timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        terminal_repairs: list[tuple[str, str, str]] = []
        with self._lock, self._connect() as connection:
            terminal_rows = connection.execute(
                """SELECT r.run_id, r.status AS run_status, w.wave_id
                   FROM runs r
                   JOIN waves w ON w.run_id=r.run_id
                   WHERE r.status IN ('accepted','blocked','aborted','stale')
                     AND w.status='active'
                   ORDER BY r.started_at, w.ordinal"""
            ).fetchall()
            terminal_repairs = [
                (str(row["run_id"]), str(row["run_status"]), str(row["wave_id"]))
                for row in terminal_rows
            ]
            stale = (
                self._stale_active_run_candidates(connection, now_ts=now_ts, cutoff=cutoff)
                if close_stale_active
                else []
            )
        terminal_state = {
            "accepted": ("accepted", "CHECKPOINTED"),
            "blocked": ("blocked", "BLOCKED"),
            "aborted": ("aborted", "ABORTED"),
            "stale": ("aborted", "ABORTED"),
        }
        for run_id, run_status, wave_id in terminal_repairs:
            wave_status, state_after = terminal_state[run_status]
            self.finish_wave(
                wave_id,
                status=wave_status,
                metadata={"reconciled_from_run_status": run_status, "reconcile_reason": "terminal_parent"},
            )
            self.append_event(
                run_id,
                wave_id=wave_id,
                event_type="wave_lifecycle_reconciled",
                state_before="active",
                state_after=state_after,
                payload={"reason": "terminal_parent", "run_status": run_status, "wave_status": wave_status},
            )
        for run_id, wave_id in stale:
            for wave in self.list_waves(run_id):
                if str(wave.get("status") or "") != "active":
                    continue
                active_wave_id = str(wave["wave_id"])
                self.finish_wave(
                    active_wave_id,
                    status="aborted",
                    metadata={"reconciled_from_run_status": "stale", "reconcile_reason": "inactivity_timeout"},
                )
                self.append_event(
                    run_id,
                    wave_id=active_wave_id,
                    event_type="wave_lifecycle_reconciled",
                    state_before="active",
                    state_after="ABORTED",
                    payload={"reason": "inactivity_timeout", "run_status": "stale", "wave_status": "aborted"},
                )
            self.finish_run(
                run_id,
                status="stale",
                metadata={"stale_reason": "inactivity_timeout", "stale_after_seconds": threshold},
            )
            self.append_event(
                run_id,
                wave_id=wave_id,
                event_type="run_stale_reconciled",
                state_before="active",
                state_after="ABORTED",
                payload={"reason": "inactivity_timeout", "stale_after_seconds": threshold},
            )
        return [run_id for run_id, _wave_id in stale]

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
