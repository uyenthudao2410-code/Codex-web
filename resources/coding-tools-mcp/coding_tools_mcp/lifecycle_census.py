"""Immutable, content-free Gate 0 lifecycle evidence.

This module deliberately does not instantiate the canonical writer, Runtime, or
ExecutionResourceGovernor.  It creates one Backup-API copy, then projects a
consistent read-only classification from that immutable copy.  It must never
reconcile, expire, terminalize, or otherwise mutate lifecycle state.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import tempfile
import time
from collections import Counter, defaultdict
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

from .execution_resources import ACTIVE_LIFECYCLES, process_identity_token, process_is_alive
from .ledger_analysis import LedgerFacts, LedgerReadSession
from .lifecycle_reconciliation import logical_ledger_sha256


LIFECYCLE_CLASSES = frozenset({
    "LIVE_OWNED",
    "P5_EXPERIMENT_ANCHOR",
    "AWAITING_ACCEPTANCE",
    "GRACE_PERIOD_INACTIVE",
    "THRESHOLD_SENSITIVE_STALE_CANDIDATE",
    "STALE_MANAGED_JOB_RESIDUE",
    "TERMINAL_PARENT_CONTRADICTION",
    "ORPHANED_OR_FOREIGN_MANAGED_JOB",
    "PROJECTION_DRIFT",
    "UNEXPLAINED_ACTIVE",
})
_LIVE_LANE_LIFECYCLES = frozenset({"starting", "active", "waiting", "idle"})
_ACTIVE_RUN_STATUS = "active"
_JOB_START_GRACE_SECONDS = 30.0
_SUPPLEMENTAL_TABLES = (
    "agent_lanes",
    "background_operations",
    "write_fences",
    "controller_leases",
    "managed_process_jobs",
    "checkout_resource_claims",
    "handoff_capsules",
    "hub_clients",
    "p5_experiment_epochs",
    "p5_enrollment_decisions",
    "experiment_assignments",
    "p5_arm_protocol_starts",
    "p5_assignment_workflow_bindings",
    "p5_assignment_outcomes",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _parse_timestamp(value: object) -> float | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            return None
        return parsed.timestamp()
    except ValueError:
        return None


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _workspace_checkout_id(workspace: Path) -> str:
    normalized = os.path.normcase(str(Path(workspace).resolve(strict=False)))
    return hashlib.sha256(normalized.encode("utf-8", errors="replace")).hexdigest()


@dataclass(frozen=True)
class ProcessIdentityObservation:
    """Content-free result of a separate, read-only process identity probe."""

    pid: int
    exists: bool
    identity: str


def observe_process_identity(pid: int, expected_token: str) -> ProcessIdentityObservation:
    """Treat a PID as live only when its creation/process token also matches."""
    bounded_pid = int(pid or 0)
    expected = str(expected_token or "").strip()
    if bounded_pid <= 0:
        return ProcessIdentityObservation(pid=bounded_pid, exists=False, identity="NO_PID")
    exists = bool(process_is_alive(bounded_pid))
    if not exists:
        return ProcessIdentityObservation(pid=bounded_pid, exists=False, identity="NOT_RUNNING")
    observed = str(process_identity_token(bounded_pid) or "").strip()
    if not expected or not observed:
        return ProcessIdentityObservation(pid=bounded_pid, exists=True, identity="TOKEN_UNAVAILABLE")
    return ProcessIdentityObservation(
        pid=bounded_pid,
        exists=True,
        identity="MATCH" if observed == expected else "MISMATCH",
    )


class LifecycleFacts:
    """Supplemental immutable rows for Gate 0; the eight LedgerFacts loads stay intact."""

    def __init__(self, rows: dict[str, list[sqlite3.Row]]) -> None:
        self._rows = rows

    @classmethod
    def load(cls, session: LedgerReadSession) -> "LifecycleFacts":
        return cls({table: session.rows(f"SELECT * FROM {table}") for table in _SUPPLEMENTAL_TABLES})

    def rows(self, table: str) -> list[sqlite3.Row]:
        return list(self._rows.get(table, ()))


class LifecycleCensusSnapshot(AbstractContextManager["LifecycleCensusSnapshot"]):
    """Create a temporary Backup-API copy and retain one immutable read transaction."""

    def __init__(self, ledger_path: Path) -> None:
        self.ledger_path = Path(ledger_path).resolve(strict=True)
        self._temporary: tempfile.TemporaryDirectory[str] | None = None
        self._reader: LedgerReadSession | None = None
        self.ledger_facts: LedgerFacts | None = None
        self.lifecycle_facts: LifecycleFacts | None = None
        self.snapshot_metadata: dict[str, Any] = {}
        self.ledger_fact_load_statements = 0
        self.lifecycle_fact_load_statements = 0
        self.live_backup_connections = 0

    def __enter__(self) -> "LifecycleCensusSnapshot":
        self._temporary = tempfile.TemporaryDirectory(prefix="coding-tools-lifecycle-census-")
        copied_path = Path(self._temporary.name) / "ledger.sqlite3"
        with LedgerReadSession(self.ledger_path) as source:
            destination = sqlite3.connect(copied_path)
            try:
                if source.connection is None:
                    raise RuntimeError("lifecycle census source reader did not open")
                source.connection.backup(destination, pages=256, sleep=0.01)
                destination.commit()
                self.live_backup_connections = 1
            finally:
                destination.close()

        self._reader = LedgerReadSession(copied_path, immutable=True)
        self._reader.__enter__()
        reader = self._reader
        integrity = [str(row[0] or "") for row in reader.rows("PRAGMA integrity_check")]
        foreign_keys = [tuple(row) for row in reader.rows("PRAGMA foreign_key_check")]
        schema_row = reader.one("PRAGMA user_version")
        before_ledger_facts = reader.statement_count
        self.ledger_facts = LedgerFacts.load(reader)
        self.ledger_fact_load_statements = reader.statement_count - before_ledger_facts
        before_lifecycle_facts = reader.statement_count
        self.lifecycle_facts = LifecycleFacts.load(reader)
        self.lifecycle_fact_load_statements = reader.statement_count - before_lifecycle_facts
        self.snapshot_metadata = {
            "snapshot_at": _utc_now(),
            "backup_api_copy": True,
            "sha256": _sha256_file(copied_path),
            "logical_sha256": logical_ledger_sha256(reader.connection),
            "size_bytes": int(copied_path.stat().st_size),
            "schema_version": int(schema_row[0] if schema_row is not None else 0),
            "integrity_check": integrity,
            "foreign_key_check_rows": len(foreign_keys),
            "immutable": True,
            "query_only": True,
        }
        return self

    @property
    def facts(self) -> LedgerFacts:
        if self.ledger_facts is None:
            raise RuntimeError("LifecycleCensusSnapshot is not open")
        return self.ledger_facts

    @property
    def lifecycle(self) -> LifecycleFacts:
        if self.lifecycle_facts is None:
            raise RuntimeError("LifecycleCensusSnapshot is not open")
        return self.lifecycle_facts

    @property
    def statement_count(self) -> int:
        return self._reader.statement_count if self._reader is not None else 0

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self._reader is not None:
            self._reader.__exit__(exc_type, exc, traceback)
            self._reader = None
        if self._temporary is not None:
            self._temporary.cleanup()
            self._temporary = None
        self.ledger_facts = None
        self.lifecycle_facts = None


def open_lifecycle_census_snapshot(workspace: Path) -> LifecycleCensusSnapshot:
    root = Path(workspace).resolve(strict=False)
    ledger_path = root / ".coding-tools" / "orchestration" / "ledger.sqlite3"
    if not ledger_path.is_file():
        raise FileNotFoundError(f"orchestration ledger does not exist: {ledger_path}")
    return LifecycleCensusSnapshot(ledger_path)


def read_task_projection(workspace: Path) -> dict[str, Any]:
    """Read the unscoped projection or a content-free contextual projection set."""
    root = Path(workspace).resolve(strict=False)
    path = root / ".coding-tools" / "task-state.json"
    global_projection: dict[str, Any] | None = None
    global_status = "missing"
    if path.is_file():
        global_status = "unreadable"
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            payload = None
        if not isinstance(payload, dict) or not isinstance(payload.get("orchestration"), dict):
            return {"available": False, "status": "invalid" if payload is not None else global_status, "orchestration": {}}
        orchestration = payload["orchestration"]
        global_projection = {
            "run_id": str(orchestration.get("run_id") or "").strip(),
            "wave_id": str(orchestration.get("wave_id") or "").strip(),
            "orchestration_state": str(orchestration.get("orchestration_state") or "").strip(),
        }
        if any(global_projection.values()):
            return {
                "available": True,
                "status": "readable",
                "orchestration": global_projection,
                "mode": "global",
                "context_count": 0,
                "contextual_sha256": "",
            }

    context_dir = root / ".coding-tools" / "task-contexts"
    context_paths = sorted(
        path for path in context_dir.glob("*.json")
        if not path.name.endswith("-history.json")
    ) if context_dir.is_dir() else []
    if context_paths:
        contextual: list[dict[str, str]] = []
        invalid_count = 0
        for context_path in context_paths:
            try:
                value = json.loads(context_path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError):
                invalid_count += 1
                continue
            orchestration = value.get("orchestration") if isinstance(value, dict) else None
            if not isinstance(orchestration, dict):
                invalid_count += 1
                continue
            contextual.append({
                "context_id": context_path.stem,
                "run_id": str(orchestration.get("run_id") or "").strip(),
                "wave_id": str(orchestration.get("wave_id") or "").strip(),
                "orchestration_state": str(orchestration.get("orchestration_state") or "").strip().upper(),
            })
        encoded = json.dumps(contextual, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return {
            "available": invalid_count == 0,
            "status": "contextual" if invalid_count == 0 else "contextual_invalid",
            "orchestration": {},
            "mode": "contextual",
            "context_count": len(context_paths),
            "contextual_sha256": hashlib.sha256(encoded.encode("utf-8", errors="surrogatepass")).hexdigest(),
            "contextual_projections": contextual,
            "invalid_context_count": invalid_count,
        }

    if global_projection is not None:
        return {
            "available": True,
            "status": "readable",
            "orchestration": global_projection,
            "mode": "global",
            "context_count": 0,
            "contextual_sha256": "",
        }
    return {"available": False, "status": global_status, "orchestration": {}}


def _latest_timestamp(rows: list[sqlite3.Row], field: str) -> str:
    values = [str(row[field] or "") for row in rows if field in row.keys() and str(row[field] or "")]
    return max(values) if values else ""


def _row_groups(rows: list[sqlite3.Row], key: str) -> dict[str, list[sqlite3.Row]]:
    result: dict[str, list[sqlite3.Row]] = defaultdict(list)
    for row in rows:
        value = str(row[key] or "").strip() if key in row.keys() else ""
        if value:
            result[value].append(row)
    return result


def _is_live_controller(row: sqlite3.Row, observed_at: float) -> bool:
    return str(row["status"] or "") == "active" and float(row["expires_at"] or 0) > observed_at


def _is_live_fence(row: sqlite3.Row, observed_at: float) -> bool:
    return str(row["status"] or "") == "active" and float(row["expires_at"] or 0) > observed_at


def _is_live_background_operation(row: sqlite3.Row, observed_at: float, grace_seconds: float) -> bool:
    if str(row["status"] or "") != "running":
        return False
    updated_at = _parse_timestamp(row["updated_at"] if "updated_at" in row.keys() else None)
    started_at = _parse_timestamp(row["started_at"] if "started_at" in row.keys() else None)
    latest = updated_at if updated_at is not None else started_at
    if latest is None:
        return True
    return max(0.0, observed_at - latest) <= grace_seconds


def _latest_state_after(facts: LedgerFacts, run_id: str) -> str:
    events = facts.list_events(run_id)
    for event in reversed(events):
        state = str(event.get("state_after") or "").strip().upper()
        if state:
            return state
    return ""


def _last_event_guard(facts: LedgerFacts, run_id: str) -> dict[str, Any]:
    rows = facts._event_rows_by_run.get(run_id, ())
    if not rows:
        return {"seq": 0, "hash": ""}
    row = rows[-1]
    return {"seq": int(row["seq"] or 0), "hash": str(row["event_hash"] or "")}


def _projection_status(
    projection: Mapping[str, Any] | None,
    *,
    facts: LedgerFacts,
    records: list[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    value = dict(projection or {})
    nested = value.get("orchestration") if isinstance(value.get("orchestration"), Mapping) else value
    run_id = str(nested.get("run_id") or "").strip()
    wave_id = str(nested.get("wave_id") or "").strip()
    state = str(nested.get("orchestration_state") or "").strip()
    mode = str(value.get("mode") or ("global" if value.get("available") is True else "")).strip().lower()
    if mode == "contextual" and value.get("available") is True:
        contextual = value.get("contextual_projections")
        entries = list(contextual) if isinstance(contextual, list) else []
        by_run: dict[str, list[dict[str, str]]] = defaultdict(list)
        malformed = False
        for item in entries:
            if not isinstance(item, Mapping):
                malformed = True
                continue
            identity = {
                "run_id": str(item.get("run_id") or "").strip(),
                "wave_id": str(item.get("wave_id") or "").strip(),
                "orchestration_state": str(item.get("orchestration_state") or "").strip().upper(),
            }
            present = [bool(identity[field]) for field in ("run_id", "wave_id", "orchestration_state")]
            if any(present) and not all(present):
                malformed = True
            if identity["run_id"]:
                by_run[identity["run_id"]].append(identity)

        relevant_classes = {
            "LIVE_OWNED",
            "AWAITING_ACCEPTANCE",
            "GRACE_PERIOD_INACTIVE",
            "TERMINAL_PARENT_CONTRADICTION",
            "UNEXPLAINED_ACTIVE",
        }
        relevant = [
            dict(item) for item in (records or [])
            if str(item.get("classification") or "") in relevant_classes
        ]
        missing: list[str] = []
        conflicting: list[str] = []
        for record in relevant:
            relevant_run_id = str(record.get("run_id") or "").strip()
            waves = facts.list_waves(relevant_run_id) if relevant_run_id else []
            expected_wave_id = str(waves[-1].get("wave_id") or "").strip() if waves else ""
            expected_state = str(record.get("latest_state_after") or "").strip().upper()
            candidates = by_run.get(relevant_run_id, [])
            exact = [
                item for item in candidates
                if item["wave_id"] == expected_wave_id and item["orchestration_state"] == expected_state
            ]
            if not relevant_run_id or not expected_wave_id or not expected_state or not exact:
                missing.append(relevant_run_id)
            if any(item not in exact for item in candidates):
                conflicting.append(relevant_run_id)

        digest = str(value.get("contextual_sha256") or "").strip().lower()
        context_count = value.get("context_count")
        consistent = bool(
            not malformed
            and not missing
            and not conflicting
            and isinstance(context_count, int)
            and not isinstance(context_count, bool)
            and context_count > 0
            and len(digest) == 64
            and all(char in "0123456789abcdef" for char in digest)
        )
        return {
            "available": True,
            "classification": "CONTEXTUAL_PROJECTIONS" if consistent else "PROJECTION_DRIFT",
            "mode": "contextual",
            "run_id": "",
            "wave_id": "",
            "orchestration_state": "",
            "context_count": context_count if isinstance(context_count, int) else 0,
            "contextual_sha256": digest,
            "relevant_run_count": len(relevant),
            "bound_relevant_run_count": len(relevant) - len(set(missing)),
            "missing_run_count": len(set(missing)),
            "conflicting_run_count": len(set(conflicting)),
            "malformed_context_projection": malformed,
        }
    if value.get("available") is not True:
        return {
            "available": False,
            "classification": "PROJECTION_UNAVAILABLE",
            "run_id": run_id,
            "wave_id": wave_id,
            "orchestration_state": state,
            "source_status": str(value.get("status") or "unavailable"),
        }
    if not run_id and not wave_id and not state:
        active_runs = [
            item for item in facts.list_runs(limit=5000)
            if str(item.get("status") or "").strip().lower() == _ACTIVE_RUN_STATUS
        ]
        if active_runs:
            return {
                "available": True,
                "classification": "PROJECTION_DRIFT",
                "run_id": "",
                "wave_id": "",
                "orchestration_state": "",
                "reason": "active_ledger_run_missing_projection",
                "active_run_count": len(active_runs),
            }
        return {
            "available": bool(value.get("available", True)),
            "classification": "NO_ACTIVE_PROJECTION",
            "mode": "global",
            "run_id": "",
            "wave_id": "",
            "orchestration_state": "",
            "context_count": 0,
            "contextual_sha256": "",
        }
    run = facts.get_run(run_id) if run_id else None
    waves = facts.list_waves(run_id) if run else []
    current_wave_id = str(waves[-1].get("wave_id") or "").strip() if waves else ""
    wave_matches = bool(run and wave_id and current_wave_id and wave_id == current_wave_id)
    run_status = str(run.get("status") or "").strip().lower() if run else ""
    canonical_state = _latest_state_after(facts, run_id) if run else ""
    projected_state = state.upper()
    expected_state = ""
    consistent_classification = "PROJECTION_CONSISTENT"
    if run_status == "accepted" or canonical_state == "CHECKPOINTED":
        expected_state, consistent_classification = "CHECKPOINTED", "CHECKPOINTED"
    elif run_status == "blocked" or canonical_state == "BLOCKED":
        expected_state, consistent_classification = "BLOCKED", "BLOCKED"
    elif run_status in {"aborted", "stale", "reconciled", "reconciled_stale"} or canonical_state in {"ABORTED", "STALE", "RECONCILED"}:
        expected_state, consistent_classification = "ABORTED", "ABORTED"
    elif run_status == _ACTIVE_RUN_STATUS and canonical_state and canonical_state not in {"CHECKPOINTED", "BLOCKED", "ABORTED", "STALE", "RECONCILED"}:
        expected_state = canonical_state
    consistent = bool(run and wave_matches and expected_state and projected_state == expected_state)
    return {
        "available": bool(value.get("available", True)),
        "classification": consistent_classification if consistent else "PROJECTION_DRIFT",
        "mode": "global",
        "run_id": run_id,
        "wave_id": wave_id,
        "orchestration_state": state,
        "run_found": run is not None,
        "run_active": run_status == _ACTIVE_RUN_STATUS,
        "wave_matches_run": wave_matches if wave_id else None,
        "current_wave_id": current_wave_id,
        "canonical_run_status": run_status,
        "canonical_orchestration_state": canonical_state,
        "expected_projection_state": expected_state,
        "context_count": 0,
        "contextual_sha256": "",
    }


def lifecycle_census(
    snapshot: LifecycleCensusSnapshot,
    *,
    workspace: Path,
    observed_at: float,
    grace_seconds: float = 15 * 60,
    stale_after_seconds: float = 24 * 60 * 60,
    projection: Mapping[str, Any] | None = None,
    process_probe: Callable[[int, str], ProcessIdentityObservation] = observe_process_identity,
) -> dict[str, Any]:
    """Classify current lifecycle evidence without altering the canonical ledger."""
    if observed_at < 0:
        raise ValueError("observed_at must be a non-negative Unix timestamp")
    grace = max(0.0, float(grace_seconds))
    stale_after = max(grace, float(stale_after_seconds))
    facts = snapshot.facts
    lifecycle = snapshot.lifecycle
    expected_checkout = _workspace_checkout_id(workspace)

    runs = {str(item.get("run_id") or ""): item for item in facts.list_runs(limit=5000)}
    lanes_by_run = _row_groups(lifecycle.rows("agent_lanes"), "run_id")
    background_by_run = _row_groups(lifecycle.rows("background_operations"), "run_id")
    fence_by_run = _row_groups(lifecycle.rows("write_fences"), "run_id")
    lease_by_run = _row_groups(lifecycle.rows("controller_leases"), "run_id")
    jobs_by_run = _row_groups(lifecycle.rows("managed_process_jobs"), "run_id")
    handoffs_by_run = _row_groups(lifecycle.rows("handoff_capsules"), "run_id")

    p5_epochs = lifecycle.rows("p5_experiment_epochs")
    p5_by_run = {
        str(row["ledger_run_id"]): row
        for row in p5_epochs
        if str(row["ledger_run_id"] or "").strip()
    }

    job_records: list[dict[str, Any]] = []
    for row in lifecycle.rows("managed_process_jobs"):
        state = str(row["lifecycle_state"] or "")
        if state not in ACTIVE_LIFECYCLES:
            continue
        run_id = str(row["run_id"] or "")
        job_id = str(row["job_id"] or "")
        started_at = str(row["started_at"] or "")
        updated_at = str(row["updated_at"] or "")
        checkout_relation = "CURRENT" if str(row["checkout_id"] or "") == expected_checkout else "FOREIGN"
        pid = int(row["root_pid"] or 0)
        age = None
        updated_ts = _parse_timestamp(updated_at) or _parse_timestamp(started_at)
        if updated_ts is not None:
            age = max(0.0, observed_at - updated_ts)
        if pid <= 0:
            identity = "NO_PID"
            if age is not None and age <= _JOB_START_GRACE_SECONDS:
                classification = "GRACE_PERIOD_INACTIVE"
            elif age is not None:
                classification = "STALE_MANAGED_JOB_RESIDUE"
            else:
                classification = "ORPHANED_OR_FOREIGN_MANAGED_JOB"
        else:
            observation = process_probe(pid, str(row["root_process_token"] or ""))
            identity = observation.identity
            if observation.exists and observation.identity == "MATCH":
                classification = (
                    "LIVE_OWNED"
                    if state != "orphaned" and checkout_relation == "CURRENT"
                    else "ORPHANED_OR_FOREIGN_MANAGED_JOB"
                )
            elif not observation.exists or observation.identity == "MISMATCH":
                classification = "STALE_MANAGED_JOB_RESIDUE"
            else:
                classification = "ORPHANED_OR_FOREIGN_MANAGED_JOB"
        job_records.append({
            "job_id": job_id,
            "run_id": run_id,
            "wave_id": str(row["wave_id"] or ""),
            "lifecycle_state": state,
            "classification": classification,
            "checkout_relation": checkout_relation,
            "root_pid": pid,
            "job_updated_at": updated_at,
            "identity": identity,
            "age_seconds": round(age, 6) if age is not None else None,
        })

    terminal_parent_ids: set[str] = set()
    for run_id, run in runs.items():
        if str(run.get("status") or "") == _ACTIVE_RUN_STATUS:
            continue
        child_wave_active = any(str(item.get("status") or "") == "active" for item in facts.list_waves(run_id))
        child_lane_live = any(str(row["lifecycle"] or "") in _LIVE_LANE_LIFECYCLES for row in lanes_by_run.get(run_id, ()))
        child_background_live = any(
            _is_live_background_operation(row, observed_at, grace)
            for row in background_by_run.get(run_id, ())
        )
        child_fence_live = any(_is_live_fence(row, observed_at) for row in fence_by_run.get(run_id, ()))
        child_lease_live = any(_is_live_controller(row, observed_at) for row in lease_by_run.get(run_id, ()))
        child_job_live = any(item["classification"] == "LIVE_OWNED" for item in job_records if item["run_id"] == run_id)
        if any((child_wave_active, child_lane_live, child_background_live, child_fence_live, child_lease_live, child_job_live)):
            terminal_parent_ids.add(run_id)

    records: list[dict[str, Any]] = []
    relevant_ids = {
        run_id for run_id, run in runs.items() if str(run.get("status") or "") == _ACTIVE_RUN_STATUS
    } | set(p5_by_run) | terminal_parent_ids
    for run_id in sorted(relevant_ids):
        run = runs.get(run_id)
        if run is None:
            continue
        lane_rows = lanes_by_run.get(run_id, ())
        background_rows = background_by_run.get(run_id, ())
        fence_rows = fence_by_run.get(run_id, ())
        lease_rows = lease_by_run.get(run_id, ())
        run_jobs = [item for item in job_records if item["run_id"] == run_id]
        ownership = {
            "active_controller_leases": sum(1 for row in lease_rows if _is_live_controller(row, observed_at)),
            "active_write_fences": sum(1 for row in fence_rows if _is_live_fence(row, observed_at)),
            "running_background_operations": sum(
                1 for row in background_rows
                if _is_live_background_operation(row, observed_at, grace)
            ),
            "live_agent_lanes": sum(1 for row in lane_rows if str(row["lifecycle"] or "") in _LIVE_LANE_LIFECYCLES),
            "live_managed_jobs": sum(1 for item in run_jobs if item["classification"] == "LIVE_OWNED"),
        }
        stale_background_operations = sum(
            1 for row in background_rows
            if str(row["status"] or "") == "running"
            and not _is_live_background_operation(row, observed_at, grace)
        )
        latest_candidates = [
            str(run.get("started_at") or ""),
            _latest_timestamp(facts._event_rows_by_run.get(run_id, ()), "event_time"),
            _latest_timestamp([row for row in lifecycle.rows("managed_process_jobs") if str(row["run_id"] or "") == run_id], "updated_at"),
            _latest_timestamp(lane_rows, "updated_at"),
            _latest_timestamp(background_rows, "updated_at"),
            _latest_timestamp(handoffs_by_run.get(run_id, ()), "created_at"),
        ]
        latest_candidates.extend(
            str(item.get("started_at") or "") for item in facts.list_waves(run_id)
        )
        latest_candidates.extend(
            str(item.get("finished_at") or "") for item in facts.list_waves(run_id)
        )
        latest_activity_at = max((item for item in latest_candidates if item), default="")
        latest_ts = _parse_timestamp(latest_activity_at)
        activity_age = max(0.0, observed_at - latest_ts) if latest_ts is not None else None
        latest_state = _latest_state_after(facts, run_id)
        reasons: list[str] = []
        if run_id in p5_by_run:
            classification = "P5_EXPERIMENT_ANCHOR"
            reasons.append("p5_epoch_ledger_anchor")
        elif run_id in terminal_parent_ids:
            classification = "TERMINAL_PARENT_CONTRADICTION"
            reasons.append("terminal_run_has_live_child_resource_or_wave")
        elif latest_state == "ACCEPTING":
            classification = "AWAITING_ACCEPTANCE"
            reasons.append("latest_canonical_state_accepting")
        elif any(int(value) > 0 for value in ownership.values()):
            classification = "LIVE_OWNED"
            reasons.append("live_ownership_present")
        elif activity_age is None:
            classification = "UNEXPLAINED_ACTIVE"
            reasons.append("no_parseable_activity_timestamp")
        elif activity_age <= grace:
            classification = "GRACE_PERIOD_INACTIVE"
            reasons.append("inactive_within_grace_period")
        else:
            classification = "THRESHOLD_SENSITIVE_STALE_CANDIDATE"
            reasons.append("inactive_without_live_ownership")
            if activity_age >= stale_after:
                reasons.append("meets_current_stale_threshold")
            else:
                reasons.append("below_current_stale_threshold")
        records.append({
            "run_id": run_id,
            "run_status": str(run.get("status") or ""),
            "classification": classification,
            "reasons": reasons,
            "latest_activity_at": latest_activity_at or None,
            "activity_age_seconds": round(activity_age, 6) if activity_age is not None else None,
            "latest_state_after": latest_state or None,
            "last_event": _last_event_guard(facts, run_id),
            "ownership": ownership,
            "stale_background_operations": stale_background_operations,
            "p5_epoch_lifecycle": str(p5_by_run[run_id]["lifecycle"] or "") if run_id in p5_by_run else None,
            "managed_job_classifications": sorted({item["classification"] for item in run_jobs}),
        })

    terminal_parent_lanes = []
    for record in records:
        if record["classification"] != "TERMINAL_PARENT_CONTRADICTION":
            continue
        for row in lanes_by_run.get(str(record["run_id"]), ()):
            if str(row["lifecycle"] or "") not in _LIVE_LANE_LIFECYCLES:
                continue
            terminal_parent_lanes.append({
                "lane_id": str(row["lane_id"] or ""),
                "run_id": str(record["run_id"]),
                "wave_id": str(row["wave_id"] or ""),
                "lane_lifecycle": str(row["lifecycle"] or ""),
                "lane_updated_at": str(row["updated_at"] or ""),
                "parent_status": str(record["run_status"] or ""),
                "last_event": dict(record["last_event"]),
            })

    unbound_live_resources: list[dict[str, Any]] = []

    def record_unbound(
        *,
        resource_type: str,
        resource_id: str,
        run_id: str,
        lifecycle_state: str,
        updated_at: str,
    ) -> None:
        if run_id and run_id in runs:
            return
        unbound_live_resources.append({
            "classification": "UNEXPLAINED_ACTIVE",
            "resource_type": resource_type,
            "resource_id": resource_id,
            "run_id": run_id,
            "lifecycle_state": lifecycle_state,
            "updated_at": updated_at or None,
            "reason": "live_resource_has_no_canonical_run_parent",
        })

    for row in lifecycle.rows("agent_lanes"):
        lifecycle_state = str(row["lifecycle"] or "")
        if lifecycle_state in _LIVE_LANE_LIFECYCLES:
            record_unbound(
                resource_type="agent_lane",
                resource_id=str(row["lane_id"] or ""),
                run_id=str(row["run_id"] or ""),
                lifecycle_state=lifecycle_state,
                updated_at=str(row["updated_at"] or ""),
            )
    for row in lifecycle.rows("controller_leases"):
        if _is_live_controller(row, observed_at):
            record_unbound(
                resource_type="controller_lease",
                resource_id=str(row["lease_id"] or ""),
                run_id=str(row["run_id"] or ""),
                lifecycle_state=str(row["status"] or ""),
                updated_at=str(row["updated_at"] or ""),
            )
    for row in lifecycle.rows("write_fences"):
        if _is_live_fence(row, observed_at):
            record_unbound(
                resource_type="write_fence",
                resource_id=str(row["scope_key"] or ""),
                run_id=str(row["run_id"] or ""),
                lifecycle_state=str(row["status"] or ""),
                updated_at=str(row["updated_at"] or ""),
            )
    for row in lifecycle.rows("background_operations"):
        if _is_live_background_operation(row, observed_at, grace):
            record_unbound(
                resource_type="background_operation",
                resource_id=str(row["operation_id"] or ""),
                run_id=str(row["run_id"] or ""),
                lifecycle_state=str(row["status"] or ""),
                updated_at=str(row["updated_at"] or ""),
            )
    for item in job_records:
        if item["classification"] == "LIVE_OWNED":
            record_unbound(
                resource_type="managed_process_job",
                resource_id=str(item["job_id"]),
                run_id=str(item["run_id"]),
                lifecycle_state=str(item["lifecycle_state"]),
                updated_at=str(item["job_updated_at"]),
            )

    projection_result = _projection_status(projection, facts=facts, records=records)
    counts = Counter(str(item["classification"]) for item in records)
    job_counts = Counter(str(item["classification"]) for item in job_records)
    return {
        "schema_version": 1,
        "classification_vocabulary": sorted(LIFECYCLE_CLASSES),
        "observed_at_unix_seconds": round(float(observed_at), 6),
        "thresholds": {"grace_seconds": grace, "stale_after_seconds": stale_after, "job_start_grace_seconds": _JOB_START_GRACE_SECONDS},
        "snapshot": dict(snapshot.snapshot_metadata),
        "read_contract": {
            "ledger_facts_fact_load_statements": snapshot.ledger_fact_load_statements,
            "lifecycle_facts_fact_load_statements": snapshot.lifecycle_fact_load_statements,
            "canonical_writer_instantiated": False,
            "runtime_instantiated": False,
            "execution_resource_governor_instantiated": False,
        },
        "runs": records,
        "managed_jobs": job_records,
        "terminal_parent_lanes": terminal_parent_lanes,
        "unbound_live_resources": unbound_live_resources,
        "projection": projection_result,
        "summary": {
            "run_classification_counts": dict(sorted(counts.items())),
            "managed_job_classification_counts": dict(sorted(job_counts.items())),
            "ordinary_active_runs": sum(1 for item in records if item["run_status"] == _ACTIVE_RUN_STATUS and item["classification"] != "P5_EXPERIMENT_ANCHOR"),
            "unexplained_active_runs": sum(1 for item in records if item["classification"] == "UNEXPLAINED_ACTIVE"),
            "unbound_live_resource_residues": len(unbound_live_resources),
            "stale_background_operation_residues": sum(
                1 for row in lifecycle.rows("background_operations")
                if str(row["status"] or "") == "running"
                and not _is_live_background_operation(row, observed_at, grace)
            ),
            "projection_drift": projection_result["classification"] == "PROJECTION_DRIFT",
            "p5_epochs": len(p5_epochs),
        },
        "content_free": True,
        "mutated_canonical_ledger": False,
    }
