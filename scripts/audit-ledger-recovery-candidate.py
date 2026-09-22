"""Verify a quarantined ledger-recovery candidate without applying it.

The verifier is deliberately two-sided:

* the input current/candidate/historical files are opened read-only and are
  hash-checked;
* append and duplicate-effect probes run only against a disposable clone of
  the candidate.

This is a recovery gate report, never an activation or canonical-switch tool.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
import sys
import tempfile
import uuid
from collections import Counter, defaultdict
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1] / "resources" / "coding-tools-mcp"
sys.path.insert(0, str(PACKAGE))
from coding_tools_mcp.orchestration_ledger import OrchestrationLedger  # noqa: E402


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
UNKNOWN_EFFECT_TABLES = frozenset(
    {"background_operations", "idempotency_records", "managed_process_jobs"}
)


def sha(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def ro(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro&immutable=1", uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    return connection


def quote(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def table_names(connection: sqlite3.Connection) -> list[str]:
    return [
        str(row[0])
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
    ]


def keyed_rows(connection: sqlite3.Connection, table: str) -> tuple[list[str], dict[tuple[object, ...], tuple[object, ...]]]:
    info = list(connection.execute(f"PRAGMA table_info({quote(table)})"))
    columns = [str(row[1]) for row in info]
    primary = [str(row[1]) for row in sorted(info, key=lambda row: row[5]) if row[5]]
    if not primary:
        raise RuntimeError(f"RECOVERY_TABLE_WITHOUT_PRIMARY_KEY:{table}")
    indices = [columns.index(name) for name in primary]
    rows: dict[tuple[object, ...], tuple[object, ...]] = {}
    for raw in connection.execute(f"SELECT * FROM {quote(table)}"):
        values = tuple(raw)
        key = tuple(values[index] for index in indices)
        if key in rows:
            raise RuntimeError(f"RECOVERY_DUPLICATE_IDENTITY:{table}")
        rows[key] = values
    return columns, rows


def _event_chain(connection: sqlite3.Connection) -> dict[str, object]:
    columns = {str(row[1]) for row in connection.execute("PRAGMA table_info(events)")}
    required = {"seq", "event_id", "run_id", "wave_id", "delegation_id", "event_type", "state_before", "state_after", "event_time", "payload_json", "prev_hash", "event_hash"}
    if not required.issubset(columns):
        return {"applicable": False, "errors": ["EVENT_CHAIN_SCHEMA_NOT_APPLICABLE"]}
    rows = connection.execute("SELECT * FROM events ORDER BY seq").fetchall()
    run_rows: dict[str, list[sqlite3.Row]] = defaultdict(list)
    seq_seen: set[int] = set()
    sequence_errors = 0
    previous_seq: int | None = None
    for row in rows:
        seq = int(row["seq"])
        if seq in seq_seen or (previous_seq is not None and seq <= previous_seq):
            sequence_errors += 1
        seq_seen.add(seq)
        previous_seq = seq
        run_rows[str(row["run_id"] or "")].append(row)
    link_errors = 0
    digest_errors = 0
    for items in run_rows.values():
        previous = ""
        for row in items:
            if str(row["prev_hash"] or "") != previous:
                link_errors += 1
            try:
                payload = json.loads(str(row["payload_json"] or "{}"))
            except json.JSONDecodeError:
                digest_errors += 1
                previous = str(row["event_hash"] or "")
                continue
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
                digest_errors += 1
            previous = str(row["event_hash"] or "")
    return {
        "applicable": True,
        "event_count": len(rows),
        "run_chain_count": len(run_rows),
        "sequence_errors": sequence_errors,
        "link_errors": link_errors,
        "digest_errors": digest_errors,
        "valid": not (sequence_errors or link_errors or digest_errors),
    }


def _problem_projection(connection: sqlite3.Connection) -> dict[str, object]:
    required = {"problem_id", "latest_problem_event_seq", "latest_problem_event_hash"}
    thread_columns = {str(row[1]) for row in connection.execute("PRAGMA table_info(problem_threads)")}
    event_columns = {str(row[1]) for row in connection.execute("PRAGMA table_info(problem_events)")}
    if not required.issubset(thread_columns) or not {"problem_id", "seq", "event_hash"}.issubset(event_columns):
        return {"applicable": False, "drift": [], "valid": False}
    drift: list[dict[str, object]] = []
    for row in connection.execute("SELECT problem_id,latest_problem_event_seq,latest_problem_event_hash FROM problem_threads"):
        latest = connection.execute(
            "SELECT seq,event_hash FROM problem_events WHERE problem_id=? ORDER BY seq DESC LIMIT 1",
            (row["problem_id"],),
        ).fetchone()
        expected_seq = int(latest["seq"]) if latest else None
        expected_hash = str(latest["event_hash"] or "") if latest else ""
        if int(row["latest_problem_event_seq"] or 0) != (expected_seq or 0) or str(row["latest_problem_event_hash"] or "") != expected_hash:
            drift.append(
                {
                    "problem_id": str(row["problem_id"]),
                    "thread_seq": int(row["latest_problem_event_seq"] or 0),
                    "event_seq": expected_seq,
                }
            )
    return {"applicable": True, "drift": drift, "valid": not drift}


def _unknown_effects(connection: sqlite3.Connection) -> dict[str, object]:
    result: dict[str, object] = {}
    unresolved = 0
    for table in sorted(UNKNOWN_EFFECT_TABLES):
        if table not in table_names(connection):
            continue
        columns = {str(row[1]) for row in connection.execute(f"PRAGMA table_info({quote(table)})")}
        status = next((name for name in ("status", "state", "lifecycle_state") if name in columns), None)
        if status is None:
            result[table] = {"unknown_status": True}
            continue
        counts = Counter(str(row[0] or "") for row in connection.execute(f"SELECT {quote(status)} FROM {quote(table)}"))
        pending = sum(counts.get(value, 0) for value in ("unknown", "in_progress", "running"))
        unresolved += pending
        result[table] = {"counts": dict(sorted(counts.items())), "unresolved_effect_count": pending}
    return {"tables": result, "unresolved_effect_count": unresolved, "reconciled": unresolved == 0}


def _append_and_duplicate_probe(candidate: Path) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="codex-ledger-recovery-candidate-probe-") as temp:
        root = Path(temp)
        target = root / ".coding-tools" / "orchestration" / "ledger.sqlite3"
        target.parent.mkdir(parents=True)
        shutil.copyfile(candidate, target)
        ledger = OrchestrationLedger(root)

        probe_run = "recovery-append-probe-" + uuid.uuid4().hex
        probe_wave = ledger.create_wave(
            ledger.create_run(objective="isolated recovery append probe", run_id=probe_run),
            execution_mode="mcp_only",
            base_head="recovery-probe",
            worktree_fp="recovery-probe",
            contract_fp="recovery-probe",
        )
        appended = ledger.append_event(
            probe_run,
            wave_id=probe_wave,
            event_type="recovery_append_probe",
            state_before="READY",
            state_after="PROVING",
            payload={"probe": True},
        )
        with ledger._connect() as connection:
            persisted = connection.execute("SELECT event_hash,prev_hash FROM events WHERE event_id=?", (appended["event_id"],)).fetchone()
            candidate_integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
            candidate_fk = len(list(connection.execute("PRAGMA foreign_key_check")))
        if persisted is None or str(persisted["event_hash"]) != str(appended["event_hash"]):
            raise RuntimeError("RECOVERY_APPEND_PROBE_NOT_PERSISTED")
        if candidate_integrity != "ok" or candidate_fk:
            raise RuntimeError("RECOVERY_APPEND_PROBE_INTEGRITY_FAILED")

        with ledger._connect() as connection:
            pending = [
                dict(row)
                for row in connection.execute(
                    "SELECT idempotency_key,operation,request_hash FROM idempotency_records WHERE status IN ('unknown','in_progress')"
                )
            ]
            completed = connection.execute(
                "SELECT idempotency_key,operation,request_hash FROM idempotency_records WHERE status='completed' LIMIT 1"
            ).fetchone()
        marked_background = ledger.mark_orphaned_background_operations(current_server_instance_id="recovery-probe-server")
        marked_unknown = ledger.mark_orphaned_idempotency(current_process_instance_id="recovery-probe-process")
        rejected_unknown = 0
        for row in pending:
            result = ledger.claim_idempotency(**row, process_instance_id="recovery-probe-process")
            if result.get("claimed") is not False or result.get("reason") != "unknown":
                raise RuntimeError("RECOVERY_UNKNOWN_REPLAY_NOT_REFUSED")
            rejected_unknown += 1
        duplicate_reason = "not_checked"
        if completed is not None:
            duplicate = ledger.claim_idempotency(
                idempotency_key=str(completed["idempotency_key"]),
                operation=str(completed["operation"]),
                request_hash=str(completed["request_hash"]),
                process_instance_id="recovery-probe-process",
            )
            if duplicate.get("claimed") is not False or duplicate.get("reason") != "completed":
                raise RuntimeError("RECOVERY_COMPLETED_DUPLICATE_NOT_REFUSED")
            duplicate_reason = str(duplicate.get("reason"))
        with ledger._connect() as connection:
            running = int(connection.execute("SELECT COUNT(*) FROM background_operations WHERE status='running'").fetchone()[0]) if "background_operations" in table_names(connection) else 0
            in_progress = int(connection.execute("SELECT COUNT(*) FROM idempotency_records WHERE status='in_progress'").fetchone()[0])
        return {
            "append_persisted": True,
            "append_prev_hash_expected_empty_for_new_run": not bool(str(persisted["prev_hash"] or "")),
            "integrity": candidate_integrity,
            "foreign_key_rows": candidate_fk,
            "background_marked_orphaned": marked_background,
            "idempotency_marked_unknown": marked_unknown,
            "unknown_replay_claims_rejected": rejected_unknown,
            "completed_duplicate_reason": duplicate_reason,
            "post_probe_running_background": running,
            "post_probe_in_progress_idempotency": in_progress,
            "valid": not running and not in_progress,
        }


def audit(current: Path, candidate: Path, historical: Path, expected_runs: set[str], expected: dict[str, str]) -> dict[str, object]:
    paths = [current.resolve(strict=True), candidate.resolve(strict=True), historical.resolve(strict=True)]
    if len(set(paths)) != 3:
        raise RuntimeError("RECOVERY_AUDIT_INPUTS_MUST_BE_DISTINCT")
    observed_hashes = {name: sha(path) for name, path in zip(("current", "candidate", "historical"), paths)}
    for name, expected_hash in expected.items():
        if observed_hashes[name] != expected_hash:
            raise RuntimeError(f"RECOVERY_AUDIT_{name.upper()}_HASH_MISMATCH")
    connections = {name: ro(path) for name, path in zip(("current", "candidate", "historical"), paths)}
    try:
        base, cand, old = (connections["current"], connections["candidate"], connections["historical"])
        names = table_names(base)
        if names != table_names(cand) or names != table_names(old):
            raise RuntimeError("RECOVERY_AUDIT_SCHEMA_MISMATCH")
        preserved = True
        inserted: dict[str, int] = {}
        authority_preserved = True
        authority_historical_only: dict[str, int] = {}
        for table in names:
            _, current_rows = keyed_rows(base, table)
            _, candidate_rows = keyed_rows(cand, table)
            _, historical_rows = keyed_rows(old, table)
            if any(candidate_rows.get(key) != value for key, value in current_rows.items()):
                preserved = False
            extra = set(candidate_rows) - set(current_rows)
            if extra:
                inserted[table] = len(extra)
            if table in AUTHORITY_TABLES:
                authority_preserved = authority_preserved and candidate_rows == current_rows
                historical_only = set(historical_rows) - set(current_rows)
                if historical_only:
                    authority_historical_only[table] = len(historical_only)
        integrity = {name: connection.execute("PRAGMA integrity_check").fetchone()[0] for name, connection in connections.items()}
        foreign_keys = {name: len(list(connection.execute("PRAGMA foreign_key_check"))) for name, connection in connections.items()}
        chains = {name: _event_chain(connection) for name, connection in connections.items()}
        projections = {name: _problem_projection(connection) for name, connection in connections.items()}
        effects = {name: _unknown_effects(connection) for name, connection in connections.items()}
    finally:
        for connection in connections.values():
            connection.close()
    append_probe = _append_and_duplicate_probe(candidate)
    projection_ok = bool(projections["candidate"].get("valid"))
    effect_ok = bool(effects["candidate"].get("reconciled"))
    structural_ok = preserved and authority_preserved and integrity["candidate"] == "ok" and not foreign_keys["candidate"] and bool(chains["candidate"].get("valid"))
    return {
        "schema_version": 1,
        "status": "CANDIDATE_AUDITED",
        "activation_eligible": False,
        "canonical_mutated": False,
        "input_sha256": observed_hashes,
        "expected_run_allowlist": sorted(expected_runs),
        "inserted_rows": inserted,
        "authority_preserved": authority_preserved,
        "historical_authority_rows_withheld": authority_historical_only,
        "current_rows_preserved": preserved,
        "integrity": integrity,
        "foreign_key_rows": foreign_keys,
        "event_chains": chains,
        "problem_projections": projections,
        "unknown_effects": effects,
        "append_duplicate_authority_probe": append_probe,
        "gates": {
            "structural_candidate": structural_ok,
            "problem_projection_reconciled": projection_ok,
            "unknown_effects_reconciled": effect_ok,
            "append_duplicate_probe": bool(append_probe.get("valid")),
            "operator_review": False,
            "supported_canonical_switch": False,
        },
        "required_before_switch": [
            "PROBLEM_PROJECTION_RECONCILIATION",
            "UNKNOWN_EFFECT_RECONCILIATION",
            "AUTHORITY_HIGH_WATER_MARK_REVIEW",
            "OPERATOR_REVIEW_AND_SUPPORTED_SWITCH_CONTRACT",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--current", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--historical", type=Path, required=True)
    parser.add_argument("--expected-current-sha256", required=True)
    parser.add_argument("--expected-candidate-sha256", required=True)
    parser.add_argument("--expected-historical-sha256", required=True)
    parser.add_argument("--run-id", action="append", required=True)
    args = parser.parse_args()
    result = audit(
        args.current,
        args.candidate,
        args.historical,
        set(args.run_id),
        {"current": args.expected_current_sha256, "candidate": args.expected_candidate_sha256, "historical": args.expected_historical_sha256},
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
