"""Read-only, snapshot-backed projections for the orchestration ledger.

This module intentionally does not share the writer's connection lifecycle.
``OrchestrationLedger`` remains the only canonical writer; reports use the
classes below so an analysis cannot initialize schema, switch journal mode, or
commit against the live audit database.
"""

from __future__ import annotations

import json
import sqlite3
import tempfile
import threading
from collections import defaultdict
from contextlib import AbstractContextManager, ExitStack
from pathlib import Path
from typing import Any

from .orchestration_ledger import OrchestrationLedger
from .idempotency_codec import decode_summary as _decode_idempotency_summary
from .ledger_file_gate import ledger_access_gate


def _readonly_uri(path: Path, *, immutable: bool = False) -> str:
    query = "mode=ro"
    if immutable:
        query += "&immutable=1"
    return f"{path.resolve(strict=True).as_uri()}?{query}"


def _proof_cache_summary(rows: dict[str, list[sqlite3.Row]], *, stage_limit: int = 100) -> dict[str, Any]:
    accepted_runs = {str(row["run_id"]) for row in rows["runs"] if str(row["status"] or "") == "accepted"}
    accepted_checkpoints = {str(row["run_id"]) for row in rows["checkpoints"] if str(row["status"] or "") == "accepted"}
    proof_duration = {str(row["proof_id"]): max(0, int(row["duration_ms"] or 0)) for row in rows["proofs"]}
    overall = {"eligible": 0, "hits": 0, "misses": 0, "known_hits": 0, "known_ms": 0, "accepted_opportunities": 0, "accepted_hits": 0, "checkpoint_opportunities": 0, "checkpoint_hits": 0}
    by_stage: dict[tuple[str, str], dict[str, int]] = {}
    misses: dict[str, int] = {}
    run_ids: set[str] = set()
    accepted_run_ids: set[str] = set()
    checkpoint_run_ids: set[str] = set()
    times: list[str] = []
    for event in rows["events"]:
        event_type = str(event["event_type"] or "")
        if event_type not in {"proof_cache_hit", "proof_cache_miss"}:
            continue
        try:
            payload = json.loads(event["payload_json"] or "{}")
        except (TypeError, json.JSONDecodeError):
            payload = {}
        payload = payload if isinstance(payload, dict) else {}
        stage = str(payload.get("stage_id") or "unknown") or "unknown"
        version = str(payload.get("stage_version") or "unknown") or "unknown"
        key = (stage, version)
        bucket = by_stage.setdefault(key, {"eligible": 0, "hits": 0, "misses": 0, "known_hits": 0, "known_ms": 0, "accepted_opportunities": 0, "accepted_hits": 0, "checkpoint_opportunities": 0, "checkpoint_hits": 0})
        run_id = str(event["run_id"])
        hit = event_type == "proof_cache_hit"
        overall["eligible"] += 1
        bucket["eligible"] += 1
        run_ids.add(run_id)
        if hit:
            overall["hits"] += 1
            bucket["hits"] += 1
            source_id = str(payload.get("source_proof_id") or "")
            if source_id in proof_duration:
                overall["known_hits"] += 1
                overall["known_ms"] += proof_duration[source_id]
                bucket["known_hits"] += 1
                bucket["known_ms"] += proof_duration[source_id]
        else:
            overall["misses"] += 1
            bucket["misses"] += 1
            reason = str(payload.get("reason") or "")
            misses[reason if reason in {"cold", "input_fingerprint_changed", "stage_version_changed"} else "other"] = misses.get(reason if reason in {"cold", "input_fingerprint_changed", "stage_version_changed"} else "other", 0) + 1
        if run_id in accepted_runs:
            accepted_run_ids.add(run_id)
            overall["accepted_opportunities"] += 1
            bucket["accepted_opportunities"] += 1
            if hit:
                overall["accepted_hits"] += 1
                bucket["accepted_hits"] += 1
        if run_id in accepted_checkpoints:
            checkpoint_run_ids.add(run_id)
            overall["checkpoint_opportunities"] += 1
            bucket["checkpoint_opportunities"] += 1
            if hit:
                overall["checkpoint_hits"] += 1
                bucket["checkpoint_hits"] += 1
        if str(event["event_time"] or ""):
            times.append(str(event["event_time"]))
    ordered = sorted(by_stage.items(), key=lambda item: (-item[1]["eligible"], item[0][0], item[0][1]))
    bounded = max(1, min(int(stage_limit), 100))
    stages = [{"stage_id": key[0], "stage_version": key[1], "eligible": item["eligible"], "hits": item["hits"], "misses": item["misses"], "hit_rate": round(item["hits"] / item["eligible"], 6) if item["eligible"] else None, "saved_ms": item["known_ms"] if item["known_hits"] == item["hits"] else None, "saved_ms_known": item["known_ms"], "saved_ms_known_hits": item["known_hits"], "saved_ms_complete": item["known_hits"] == item["hits"], "accepted_run_opportunities": item["accepted_opportunities"], "accepted_run_hits": item["accepted_hits"], "accepted_checkpoint_opportunities": item["checkpoint_opportunities"], "accepted_checkpoint_hits": item["checkpoint_hits"]} for key, item in ordered[:bounded]]
    eligible, hits = overall["eligible"], overall["hits"]
    return {"schema_version": 1, "source": "eocl_proof_cache_events_and_proofs", "eligible": eligible, "hits": hits, "misses": overall["misses"], "hit_rate": round(hits / eligible, 6) if eligible else None, "miss_reasons": dict(sorted(misses.items())), "fingerprint_classes": {"exact_reuse": hits, "cold": misses.get("cold", 0), "input_fingerprint_changed": misses.get("input_fingerprint_changed", 0), "stage_version_changed": misses.get("stage_version_changed", 0), "other_miss": misses.get("other", 0)}, "saved_ms": overall["known_ms"] if overall["known_hits"] == hits else None, "saved_ms_known": overall["known_ms"], "saved_ms_known_hits": overall["known_hits"], "saved_ms_complete": overall["known_hits"] == hits, "run_relation": {"runs_with_opportunities": len(run_ids), "accepted_runs_with_opportunities": len(accepted_run_ids), "accepted_checkpoint_runs_with_opportunities": len(checkpoint_run_ids), "accepted_run_opportunities": overall["accepted_opportunities"], "accepted_run_hits": overall["accepted_hits"], "unaccepted_run_opportunities": max(0, eligible - overall["accepted_opportunities"]), "accepted_checkpoint_opportunities": overall["checkpoint_opportunities"], "accepted_checkpoint_hits": overall["checkpoint_hits"]}, "evidence_window": {"first_event_at": min(times) if times else None, "last_event_at": max(times) if times else None}, "stages": stages, "stage_limit": bounded, "stage_rows_truncated": len(ordered) > bounded, "model_free": True, "content_free": True, "raw_input_fingerprints_included": False, "_stage_group_count": len(ordered)}


class LedgerReadSession(AbstractContextManager["LedgerReadSession"]):
    """One explicit, transactionally-consistent read-only SQLite session."""

    def __init__(self, path: Path, *, immutable: bool = False) -> None:
        self.path = Path(path).resolve(strict=True)
        self.immutable = immutable
        self.connection: sqlite3.Connection | None = None
        self._resources: ExitStack | None = None
        self.statement_count = 0

    def __enter__(self) -> "LedgerReadSession":
        resources = ExitStack()
        resources.enter_context(ledger_access_gate(self.path))
        try:
            connection = sqlite3.connect(_readonly_uri(self.path, immutable=self.immutable), uri=True, timeout=5.0)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA query_only=ON")
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute("PRAGMA busy_timeout=5000")
            connection.execute("BEGIN")
        except Exception:
            resources.close()
            raise
        self._resources = resources
        self.connection = connection
        return self

    def rows(self, query: str, parameters: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
        if self.connection is None:
            raise RuntimeError("LedgerReadSession is not open")
        self.statement_count += 1
        return self.connection.execute(query, parameters).fetchall()

    def one(self, query: str, parameters: tuple[Any, ...] = ()) -> sqlite3.Row | None:
        if self.connection is None:
            raise RuntimeError("LedgerReadSession is not open")
        self.statement_count += 1
        return self.connection.execute(query, parameters).fetchone()

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        try:
            if self.connection is not None:
                try:
                    self.connection.rollback()
                finally:
                    self.connection.close()
                    self.connection = None
        finally:
            if self._resources is not None:
                self._resources.close()
                self._resources = None


class LedgerFacts(OrchestrationLedger):
    """Bulk-loaded, read-only fact view with the existing projection semantics.

    It subclasses the writer only to reuse its mature pure projection methods.
    ``__init__`` deliberately does not call the writer initializer and all data
    accessors are overridden to use immutable in-memory facts.
    """

    def __init__(self, *, path: Path, rows: dict[str, list[sqlite3.Row]], proof_cache_summary: dict[str, Any]) -> None:
        self.path = path
        self.workspace = path.parent.parent.parent
        self.state_dir = path.parent
        self._lock = threading.RLock()
        self._proof_cache_stage_group_count = int(proof_cache_summary.pop("_stage_group_count", 0))
        self._proof_cache_summary = proof_cache_summary
        self.fact_load_statements = len(rows)
        self._economics_cache: dict[str, dict[str, Any]] = {}
        self._evaluation_cache: dict[str, dict[str, Any]] = {}
        self._runs = {str(row["run_id"]): self._run_row(row) for row in rows["runs"]}
        self._waves_by_run: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self._delegations_by_wave: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self._event_rows_by_run: dict[str, list[sqlite3.Row]] = defaultdict(list)
        self._events_by_run: dict[str, list[dict[str, Any]]] = {}
        self._proof_rows_by_run: dict[str, list[sqlite3.Row]] = defaultdict(list)
        self._proofs_by_run: dict[str, list[dict[str, Any]]] = {}
        self._checkpoints_by_run: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.idempotency_records = [{**dict(row), "summary": _decode_idempotency_summary(row)} for row in rows["idempotency_records"]]
        self._p5_epoch_rows = list(rows.get("p5_experiment_epochs", ()))
        for row in rows["waves"]:
            self._waves_by_run[str(row["run_id"])].append({
                "wave_id": row["wave_id"], "run_id": row["run_id"], "ordinal": int(row["ordinal"]),
                "execution_mode": row["execution_mode"], "base_head": row["base_head"],
                "worktree_fp": row["worktree_fp"], "contract_fp": row["contract_fp"], "status": row["status"],
                "started_at": row["started_at"], "finished_at": row["finished_at"],
                "metadata": json.loads(row["metadata_json"] or "{}"),
            })
        for row in rows["delegations"]:
            self._delegations_by_wave[str(row["wave_id"])].append({
                "delegation_id": row["delegation_id"], "wave_id": row["wave_id"],
                "parent_delegation_id": row["parent_delegation_id"], "authority_owner": row["authority_owner"],
                "route_requested": row["route_requested"], "route_resolved": row["route_resolved"],
                "model": row["model"], "effort": row["effort"],
                "allowed_scope": json.loads(row["allowed_scope_json"] or "[]"), "status": row["status"],
                "started_at": row["started_at"], "finished_at": row["finished_at"],
                "metadata": json.loads(row["metadata_json"] or "{}"),
            })
        for row in rows["events"]:
            self._event_rows_by_run[str(row["run_id"])].append(row)
        for row in rows["proofs"]:
            self._proof_rows_by_run[str(row["run_id"])].append(row)
        for row in rows["checkpoints"]:
            self._checkpoints_by_run[str(row["run_id"])].append({
                "checkpoint_id": row["checkpoint_id"], "run_id": row["run_id"], "wave_id": row["wave_id"],
                "git_head": row["git_head"], "proof_fingerprint": row["proof_fingerprint"],
                "status": row["status"], "created_at": row["created_at"],
                "metadata": json.loads(row["metadata_json"] or "{}"),
            })
        for items in self._waves_by_run.values():
            items.sort(key=lambda item: int(item["ordinal"]))
        for items in self._delegations_by_wave.values():
            items.sort(key=lambda item: str(item.get("started_at") or ""))
        for items in self._event_rows_by_run.values():
            items.sort(key=lambda item: int(item["seq"]))
        for items in self._proof_rows_by_run.values():
            items.sort(key=lambda item: (str(item["finished_at"] or ""), str(item["proof_id"])))
        for items in self._checkpoints_by_run.values():
            items.sort(key=lambda item: (str(item.get("created_at") or ""), str(item["checkpoint_id"])))

    @classmethod
    def load(cls, session: LedgerReadSession) -> "LedgerFacts":
        tables = ("runs", "waves", "delegations", "events", "proofs", "checkpoints", "idempotency_records", "p5_experiment_epochs")
        rows = {table: session.rows(f"SELECT * FROM {table}") for table in tables}
        proof_cache_summary = _proof_cache_summary(rows)
        return cls(path=session.path, rows=rows, proof_cache_summary=proof_cache_summary)

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        run = self._runs.get(str(run_id))
        return dict(run) if run is not None else None

    def _connect(self) -> Any:
        raise RuntimeError("LedgerFacts is an in-memory analysis view and must not open SQLite connections")

    def list_runs(self, *, limit: int = 20, status: str = "") -> list[dict[str, Any]]:
        bounded_limit = max(1, min(int(limit), 5000))
        selected = [item for item in self._runs.values() if not status or item.get("status") == status]
        return [dict(item) for item in sorted(selected, key=lambda item: (str(item["started_at"]), str(item["run_id"])), reverse=True)[:bounded_limit]]

    def accepted_representative_runs(self, *, limit: int) -> list[dict[str, Any]]:
        bounded_limit = max(1, min(int(limit), 5000))
        selected: list[dict[str, Any]] = []
        for run in sorted(self._runs.values(), key=lambda item: (str(item.get("started_at") or ""), str(item.get("run_id") or ""))):
            metadata = run.get("metadata") if isinstance(run.get("metadata"), dict) else {}
            evaluation = metadata.get("evaluation") if isinstance(metadata.get("evaluation"), dict) else {}
            if run.get("status") != "accepted":
                continue
            if str(evaluation.get("provenance") or "").lower() not in {"", "representative"}:
                continue
            if str(evaluation.get("policy") or "").lower() not in {"", "chatweb_mcp"}:
                continue
            selected.append(dict(run))
            if len(selected) >= bounded_limit:
                break
        return selected

    def latest_solution_shadow_run_ids(self, *, limit: int) -> list[str]:
        bounded_limit = max(1, min(int(limit), 100))
        observed: list[tuple[int, str]] = []
        for run_id, events in self._event_rows_by_run.items():
            latest = max((int(row["seq"]) for row in events if str(row["event_type"] or "") == "solution_shadow_recommended"), default=0)
            if latest:
                observed.append((latest, run_id))
        return [run_id for _, run_id in sorted(observed, reverse=True)[:bounded_limit]]

    def p5_latest_epoch(self) -> dict[str, Any] | None:
        if not self._p5_epoch_rows:
            return None
        row = max(self._p5_epoch_rows, key=lambda item: (str(item["updated_at"] or ""), str(item["activation_epoch_id"] or "")))
        return self._p5_epoch_row(row)

    def list_waves(self, run_id: str) -> list[dict[str, Any]]:
        return list(self._waves_by_run.get(str(run_id), ()))

    def list_delegations(self, wave_id: str) -> list[dict[str, Any]]:
        return list(self._delegations_by_wave.get(str(wave_id), ()))

    def list_events(self, run_id: str, *, wave_id: str | None = None) -> list[dict[str, Any]]:
        key = str(run_id)
        events = self._events_by_run.get(key)
        if events is None:
            events = [self._event_row(row) for row in self._event_rows_by_run.get(key, ())]
            self._events_by_run[key] = events
        return [item for item in events if not wave_id or str(item.get("wave_id") or "") == wave_id]

    def list_proofs(self, run_id: str, *, wave_id: str | None = None) -> list[dict[str, Any]]:
        key = str(run_id)
        proofs = self._proofs_by_run.get(key)
        if proofs is None:
            proofs = [self._proof_row(row) for row in self._proof_rows_by_run.get(key, ())]
            self._proofs_by_run[key] = proofs
        return [item for item in proofs if not wave_id or str(item.get("wave_id") or "") == wave_id]

    def list_checkpoints(self, run_id: str, *, wave_id: str | None = None) -> list[dict[str, Any]]:
        checkpoints = self._checkpoints_by_run.get(str(run_id), ())
        return [item for item in checkpoints if not wave_id or str(item.get("wave_id") or "") == wave_id]

    def list_usage_events(self, run_id: str, *, limit: int | None = 100) -> list[dict[str, Any]]:
        items = [{**(event.get("payload") or {}), "seq": event["seq"], "event_time": event["event_time"]} for event in self.list_events(run_id) if event.get("event_type") == "usage_event"]
        if limit is None:
            return items
        return items[-max(1, min(int(limit), 500)):]

    def list_observation_spans(self, run_id: str, *, limit: int = 500) -> list[dict[str, Any]]:
        bounded_limit = max(1, min(int(limit), 1000))
        return [
            {**(event.get("payload") or {}), "seq": event["seq"], "event_time": event["event_time"]}
            for event in self.list_events(run_id)
            if event.get("event_type") == "observation_span_recorded"
        ][:bounded_limit]

    def proof_cache_opportunity_summary(self, *, stage_limit: int = 100) -> dict[str, Any]:
        # The bulk snapshot is intentionally bounded at load time; do not reopen SQLite.
        result = dict(self._proof_cache_summary)
        bounded = max(1, min(int(stage_limit), 100))
        result["stages"] = list(result.get("stages") or [])[:bounded]
        result["stage_limit"] = bounded
        result["stage_rows_truncated"] = self._proof_cache_stage_group_count > bounded
        return result

    def accepted_result_economics(self, run_id: str) -> dict[str, Any]:
        key = str(run_id)
        if key not in self._economics_cache:
            self._economics_cache[key] = OrchestrationLedger.accepted_result_economics(self, key)
        return self._economics_cache[key]

    def accepted_result_evaluation(self, run_id: str) -> dict[str, Any]:
        key = str(run_id)
        if key not in self._evaluation_cache:
            self._evaluation_cache[key] = OrchestrationLedger.accepted_result_evaluation(self, key)
        return self._evaluation_cache[key]


class LedgerAnalysisSnapshot(AbstractContextManager["LedgerAnalysisSnapshot"]):
    """Backup a live ledger once, then expose all analysis facts from the copy."""

    def __init__(self, ledger_path: Path) -> None:
        self.ledger_path = Path(ledger_path).resolve(strict=True)
        self._temporary: tempfile.TemporaryDirectory[str] | None = None
        self._reader: LedgerReadSession | None = None
        self.facts: LedgerFacts | None = None
        self.live_backup_connections = 0

    def __enter__(self) -> "LedgerAnalysisSnapshot":
        self._temporary = tempfile.TemporaryDirectory(prefix="coding-tools-ledger-analysis-")
        snapshot_path = Path(self._temporary.name) / "ledger.sqlite3"
        with LedgerReadSession(self.ledger_path) as source:
            destination = sqlite3.connect(snapshot_path)
            try:
                if source.connection is None:
                    raise RuntimeError("source reader did not open")
                source.connection.backup(destination, pages=256, sleep=0.01)
                destination.commit()
                self.live_backup_connections = 1
            finally:
                destination.close()
        self._reader = LedgerReadSession(snapshot_path, immutable=True)
        self._reader.__enter__()
        self.facts = LedgerFacts.load(self._reader)
        return self

    @property
    def ledger(self) -> LedgerFacts:
        if self.facts is None:
            raise RuntimeError("LedgerAnalysisSnapshot is not open")
        return self.facts

    @property
    def statement_count(self) -> int:
        return self._reader.statement_count if self._reader is not None else 0

    @property
    def reader(self) -> LedgerReadSession:
        """Expose the active immutable reader to opt-in analysis fact loaders."""
        if self._reader is None:
            raise RuntimeError("LedgerAnalysisSnapshot is not open")
        return self._reader

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self._reader is not None:
            self._reader.__exit__(exc_type, exc, traceback)
            self._reader = None
        if self._temporary is not None:
            self._temporary.cleanup()
            self._temporary = None
        self.facts = None


def open_ledger_analysis_snapshot(workspace: Path) -> LedgerAnalysisSnapshot:
    root = Path(workspace).resolve(strict=False)
    ledger_path = root / ".coding-tools" / "orchestration" / "ledger.sqlite3"
    if not ledger_path.is_file():
        raise FileNotFoundError(f"orchestration ledger does not exist: {ledger_path}")
    return LedgerAnalysisSnapshot(ledger_path)


def organic_rework_summary(
    ledger: LedgerFacts,
    *,
    since: str = "",
    until: str = "",
    limit: int = 500,
) -> dict[str, Any]:
    """The existing organic-rework projection, evaluated solely from bulk facts."""
    bounded_limit = max(1, min(int(limit), 5000))
    since_value = str(since or "")[:64].strip()
    until_value = str(until or "")[:64].strip()
    selected_all = []
    for run in ledger._runs.values():
        metadata = run.get("metadata") if isinstance(run.get("metadata"), dict) else {}
        evaluation = metadata.get("evaluation") if isinstance(metadata.get("evaluation"), dict) else {}
        provenance = str(evaluation.get("provenance") or "").lower()
        policy = str(evaluation.get("policy") or "").lower()
        started_at = str(run.get("started_at") or "")
        if run.get("status") != "accepted" or provenance not in {"", "representative"} or policy not in {"", "chatweb_mcp"}:
            continue
        if since_value and started_at < since_value:
            continue
        if until_value and started_at > until_value:
            continue
        selected_all.append(run)
    selected_all.sort(key=lambda item: (str(item.get("started_at") or ""), str(item.get("run_id") or "")))
    truncated = len(selected_all) > bounded_limit
    selected = selected_all[:bounded_limit]
    first_pass_tta: list[int] = []
    repaired_tta: list[int] = []
    first_pass = repaired = total_replans = included = explicit_model_route = 0
    deterministic_routes = {"unknown", "deterministic", "mcp_deterministic"}
    for run in selected:
        run_id = str(run["run_id"])
        actual_routes = {
            str(delegation.get("route_resolved") or "").strip().lower()
            for wave in ledger.list_waves(run_id)
            for delegation in ledger.list_delegations(str(wave["wave_id"]))
            if str(delegation.get("route_resolved") or "").strip()
        }
        if any(route not in deterministic_routes for route in actual_routes):
            explicit_model_route += 1
            continue
        latest_route: dict[str, Any] = {}
        points: list[tuple[str, int]] = []
        for event in ledger._event_rows_by_run.get(run_id, ()):
            event_type = str(event["event_type"] or "")
            if event_type == "route_selected":
                payload = json.loads(event["payload_json"] or "{}")
                latest_route = payload if isinstance(payload, dict) else {}
            state = str(event["state_after"] or "").strip()
            event_ms = ledger._timestamp_millis(event["event_time"])
            if state and event_ms is not None and (not points or points[-1][0] != state):
                points.append((state, event_ms))
        route = str(latest_route.get("resolved") or "unknown").strip().lower()
        if route not in {"", *deterministic_routes}:
            explicit_model_route += 1
            continue
        included += 1
        waves = ledger.list_waves(run_id)
        replan_count = sum(1 for wave in waves if str(wave.get("status") or "") == "replanned")
        total_replans += replan_count
        started_ms = ledger._timestamp_millis(run.get("started_at"))
        finished_ms = ledger._timestamp_millis(run.get("finished_at"))
        tta = max(0, int(finished_ms - started_ms)) if started_ms is not None and finished_ms is not None and finished_ms >= started_ms else None
        if replan_count:
            repaired += 1
            if isinstance(tta, int) and not isinstance(tta, bool) and tta >= 0:
                repaired_tta.append(tta)
        else:
            first_pass += 1
            if isinstance(tta, int) and not isinstance(tta, bool) and tta >= 0:
                first_pass_tta.append(tta)
    preflight_errors: dict[str, int] = {}
    for row in ledger.idempotency_records:
        if str(row.get("operation") or "") != "agent_workflow" or str(row.get("status") or "") != "failed":
            continue
        started_at = str(row.get("started_at") or "")
        if since_value and started_at < since_value or until_value and started_at > until_value:
            continue
        summary = row.get("summary") if isinstance(row.get("summary"), dict) else {}
        if not isinstance(summary, dict) or summary.get("workflow_patch_preflight") != 1:
            continue
        error_code = str(summary.get("error_code") or "unknown")
        preflight_errors[error_code] = preflight_errors.get(error_code, 0) + 1

    def percentile(values: list[int], value: int) -> int | None:
        if not values:
            return None
        ordered = sorted(values)
        return int(ordered[max(1, min(len(ordered), (len(ordered) * value + 99) // 100)) - 1])

    first_p50, first_p90 = percentile(first_pass_tta, 50), percentile(first_pass_tta, 90)
    repaired_p50, repaired_p90 = percentile(repaired_tta, 50), percentile(repaired_tta, 90)
    return {
        "schema_version": 1, "baseline_policy": "chatweb_mcp",
        "window": {"since": since_value or None, "until": until_value or None, "basis": "run_started_at"},
        "accepted_runs_scanned": len(selected), "accepted_runs": included, "accepted_runs_truncated": truncated,
        "excluded": {"explicit_model_route": explicit_model_route}, "first_pass_accepted": first_pass,
        "repaired_accepted": repaired, "first_pass_rate": round(first_pass / included, 6) if included else None,
        "repaired_rate": round(repaired / included, 6) if included else None, "repair": {"replan_count": total_replans},
        "preflight_avoided": {"count": sum(preflight_errors.values()), "error_codes": dict(sorted(preflight_errors.items())), "meaning": "known no-write patch failures stopped before orchestration run creation"},
        "tta_ms": {"first_pass_p50": first_p50, "first_pass_p90": first_p90, "repaired_p50": repaired_p50, "repaired_p90": repaired_p90, "repaired_to_first_pass_p50_multiplier": round(repaired_p50 / first_p50, 6) if isinstance(repaired_p50, int) and isinstance(first_p50, int) and first_p50 > 0 else None, "repaired_to_first_pass_p90_multiplier": round(repaired_p90 / first_p90, 6) if isinstance(repaired_p90, int) and isinstance(first_p90, int) and first_p90 > 0 else None},
        "cost_roi_policy": "use only causally attributed complete accepted-result cost; unknown is not zero",
        "provenance_filter": "exclude benchmark/synthetic and explicit model-routed accepted runs", "model_free": True, "content_free": True,
    }
