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
from datetime import datetime, timezone
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
UNRESOLVED_EFFECT_STATUSES = {
    "background_operations": frozenset({"running", "unknown", "in_progress"}),
    "idempotency_records": frozenset({"running", "unknown", "in_progress"}),
    # Managed jobs use lifecycle terminology rather than the idempotency
    # vocabulary.  An orphaned job is still an unresolved process boundary;
    # it is not evidence that the process is dead or that its effect is safe
    # to replay.
    "managed_process_jobs": frozenset(
        {"starting", "running", "active", "waiting", "idle", "terminating", "orphaned", "unknown", "in_progress"}
    ),
}
POINTER_ONLY_SAFE_RELATIONS = frozenset(
    {"ENGINEERING_ATTEMPT_BOUND", "LINK", "USER_FEEDBACK"}
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


def _problem_projection_reconciliation_plan(connection: sqlite3.Connection) -> dict[str, object]:
    """Describe a safe pointer-only projection repair without applying it.

    A recovery candidate may contain immutable problem events that arrived after
    the copied ``problem_threads`` projection.  Advancing only the projection
    pointer is safe to *propose* when every tail event keeps the current
    revision/state and is a non-transition relation.  This verifier never
    writes the pointer; a supported runtime reconciliation API and owner
    authority are still required before any application.
    """
    thread_columns = {str(row[1]) for row in connection.execute("PRAGMA table_info(problem_threads)")}
    event_columns = {str(row[1]) for row in connection.execute("PRAGMA table_info(problem_events)")}
    required_thread = {
        "problem_id",
        "current_revision",
        "resolution_state",
        "latest_problem_event_seq",
        "latest_problem_event_hash",
    }
    required_event = {
        "problem_id",
        "seq",
        "problem_revision",
        "relation_type",
        "link_status",
        "link_role",
        "state_before",
        "state_after",
        "event_id",
        "event_hash",
        "prev_hash",
    }
    if not required_thread.issubset(thread_columns) or not required_event.issubset(event_columns):
        return {"applicable": False, "plans": [], "valid": False, "can_apply": False}

    plans: list[dict[str, object]] = []
    for thread in connection.execute(
        "SELECT problem_id,current_revision,resolution_state,latest_problem_event_seq,latest_problem_event_hash FROM problem_threads ORDER BY problem_id"
    ):
        problem_id = str(thread["problem_id"])
        pointer_seq = int(thread["latest_problem_event_seq"] or 0)
        pointer_hash = str(thread["latest_problem_event_hash"] or "")
        tail = connection.execute(
            """SELECT seq,problem_revision,relation_type,link_status,link_role,
                      state_before,state_after,event_id,event_hash,prev_hash
                 FROM problem_events
                WHERE problem_id=? AND seq>?
                ORDER BY seq""",
            (problem_id, pointer_seq),
        ).fetchall()
        if not tail:
            continue
        reasons: list[str] = []
        tail_rows: list[dict[str, object]] = []
        expected_prev = pointer_hash
        for row in tail:
            relation = str(row["relation_type"] or "")
            event_revision = int(row["problem_revision"] or 0)
            state_before = str(row["state_before"] or "")
            state_after = str(row["state_after"] or "")
            link_status = str(row["link_status"] or "")
            link_role = str(row["link_role"] or "")
            event_reasons: list[str] = []
            if event_revision != int(thread["current_revision"]):
                event_reasons.append("REVISION_MISMATCH")
            if state_before != str(thread["resolution_state"] or "") or state_after != state_before:
                event_reasons.append("STATE_TRANSITION_OR_MISMATCH")
            if relation not in POINTER_ONLY_SAFE_RELATIONS:
                event_reasons.append("TRANSITION_RELATION")
            if link_status != "EXACT":
                event_reasons.append("LINK_NOT_EXACT")
            if relation == "ENGINEERING_ATTEMPT_BOUND" and link_role != "PRIMARY":
                event_reasons.append("PRIMARY_BINDING_REQUIRED")
            if str(row["prev_hash"] or "") != expected_prev:
                event_reasons.append("TAIL_HASH_LINK_MISMATCH")
            if event_reasons:
                reasons.extend(f"seq={int(row['seq'])}:{reason}" for reason in event_reasons)
            expected_prev = str(row["event_hash"] or "")
            tail_rows.append(
                {
                    "seq": int(row["seq"]),
                    "event_id": str(row["event_id"] or ""),
                    "event_hash": str(row["event_hash"] or ""),
                    "relation_type": relation,
                    "link_status": link_status,
                    "link_role": link_role,
                    "problem_revision": event_revision,
                    "state_before": state_before,
                    "state_after": state_after,
                }
            )
        last = tail_rows[-1]
        plans.append(
            {
                "problem_id": problem_id,
                "classification": "POINTER_ONLY_SAFE" if not reasons else "BLOCKED_UNSAFE_TAIL",
                "can_apply": False,
                "authority_required": "RUNTIME_RECONCILIATION",
                "current_pointer_seq": pointer_seq,
                "current_pointer_hash": pointer_hash,
                "proposed_pointer_seq": int(last["seq"]),
                "proposed_pointer_hash": str(last["event_hash"]),
                "tail_event_count": len(tail_rows),
                "tail_events": tail_rows,
                "reasons": reasons,
            }
        )
    return {
        "applicable": True,
        "plans": plans,
        "valid": all(plan["classification"] == "POINTER_ONLY_SAFE" for plan in plans),
        "can_apply": False,
        "requires_supported_runtime_api": True,
    }


def _parse_timestamp(value: object) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _json_object(value: object) -> dict[str, object]:
    if not value:
        return {}
    try:
        parsed = json.loads(str(value))
    except (TypeError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _explicit_no_effect(summary: dict[str, object]) -> bool:
    """Return True only when the record explicitly proves no effect occurred.

    Error categories such as validation/security/permission are not enough:
    a lost acknowledgement can happen after an effect even when the request
    was rejected by a later guard.  This intentionally conservative predicate
    keeps those rows in manual reconciliation unless a typed no-effect field
    was persisted by the runtime.
    """
    if summary.get("outcome_unknown") is False:
        return True
    if summary.get("effect_applied") is False:
        return True
    if str(summary.get("effect_state") or "").strip().lower() in {
        "not_applied",
        "never_sent",
        "not_started",
        "rejected_before_effect",
        "pre_effect_rejected",
    }:
        return True
    if str(summary.get("dispatch_state") or "").strip().lower() in {
        "not_sent",
        "never_sent",
        "rejected_before_effect",
        "cancelled_before_send",
    }:
        return True
    if str(summary.get("local_admission") or "").strip().lower() in {
        "not_admitted",
        "rejected_before_effect",
        "never_sent",
    }:
        return True
    return False


def _effect_row_identity(table: str, row: sqlite3.Row) -> str:
    if table == "background_operations":
        return str(row["operation_id"] or "")
    if table == "idempotency_records":
        return str(row["idempotency_key"] or "")
    return str(row["job_id"] or "")


def _effect_row_operation(table: str, row: sqlite3.Row) -> str:
    if table == "background_operations":
        return str(row["tool"] or "")
    if table == "idempotency_records":
        return str(row["operation"] or "")
    return str(row["resource_class"] or "")


def _effect_row_process(table: str, row: sqlite3.Row) -> str:
    if table == "background_operations":
        return str(row["server_instance_id"] or "")
    return str(row["process_instance_id"] or "")


def _effect_row_summary(table: str, row: sqlite3.Row) -> dict[str, object]:
    field = "summary_json" if table != "managed_process_jobs" else "metadata_json"
    return _json_object(row[field])


def _snapshot_frontier(connection: sqlite3.Connection) -> str:
    candidates: list[str] = []
    for table, columns in {
        "background_operations": ("started_at", "updated_at", "finished_at"),
        "idempotency_records": ("started_at", "updated_at", "finished_at"),
        "managed_process_jobs": ("started_at", "updated_at", "finished_at"),
        "events": ("event_time",),
    }.items():
        if table not in table_names(connection):
            continue
        available = {str(item[1]) for item in connection.execute(f"PRAGMA table_info({quote(table)})")}
        for column in columns:
            if column not in available:
                continue
            for row in connection.execute(f"SELECT {quote(column)} AS value FROM {quote(table)} WHERE {quote(column)} IS NOT NULL"):
                value = str(row["value"] or "")
                if _parse_timestamp(value) is not None:
                    candidates.append(value)
    if not candidates:
        return ""
    return max(candidates, key=lambda value: _parse_timestamp(value) or datetime.min.replace(tzinfo=timezone.utc))


def _unknown_effects(connection: sqlite3.Connection) -> dict[str, object]:
    """Inventory unresolved effect rows without changing any status.

    The report deliberately has two independent classifications:

    * ``liveness_classification`` says whether an unfinished row is a stale
      candidate relative to its durable parent (not a live-process verdict);
    * ``effect_safety_classification`` says whether a typed no-effect proof is
      present.  Anything else remains owner/manual evidence and cannot be
      replayed or silently terminalized.
    """
    result: dict[str, object] = {}
    all_rows: list[dict[str, object]] = []
    frontier = _snapshot_frontier(connection)
    run_status: dict[str, str] = {
        str(row["run_id"]): str(row["status"] or "")
        for row in connection.execute("SELECT run_id,status FROM runs")
    } if "runs" in table_names(connection) else {}
    wave_status: dict[str, str] = {
        str(row["wave_id"]): str(row["status"] or "")
        for row in connection.execute("SELECT wave_id,status FROM waves")
    } if "waves" in table_names(connection) else {}

    for table in sorted(UNKNOWN_EFFECT_TABLES):
        if table not in table_names(connection):
            continue
        columns = {str(row[1]) for row in connection.execute(f"PRAGMA table_info({quote(table)})")}
        status = next((name for name in ("status", "lifecycle_state", "state") if name in columns), None)
        if status is None:
            result[table] = {"unknown_status": True}
            continue
        rows = connection.execute(f"SELECT * FROM {quote(table)} ORDER BY rowid").fetchall()
        counts = Counter(str(row[status] or "") for row in rows)
        unresolved = 0
        table_rows: list[dict[str, object]] = []
        for row in rows:
            row_status = str(row[status] or "")
            if row_status not in UNRESOLVED_EFFECT_STATUSES.get(table, frozenset()):
                continue
            unresolved += 1
            run_id = str(row["run_id"] or "") if "run_id" in columns else ""
            wave_id = str(row["wave_id"] or "") if "wave_id" in columns else ""
            parent_run = run_status.get(run_id, "") if run_id else ""
            parent_wave = wave_status.get(wave_id, "") if wave_id else ""
            summary = _effect_row_summary(table, row)
            finished = str(row["finished_at"] or "") if "finished_at" in columns else ""
            unfinished = not bool(finished)
            parent_terminal_or_missing = not run_id or not parent_run or parent_run not in {"active", "running", "executing", "accepting"}
            if unfinished and parent_terminal_or_missing:
                liveness_classification = "STALE_CANDIDATE"
            elif unfinished:
                liveness_classification = "UNRESOLVED_ACTIVE_PARENT"
            else:
                liveness_classification = "TERMINAL_UNKNOWN"
            no_effect = _explicit_no_effect(summary)
            effect_safety = "ORPHAN_SAFE_CANDIDATE" if no_effect else "OWNER_MANUAL_EVIDENCE"
            error_code = str(summary.get("error_code") or (row["error_code"] if "error_code" in columns else "") or "")
            item = {
                "table": table,
                "identity": _effect_row_identity(table, row),
                "status": row_status,
                "operation": _effect_row_operation(table, row),
                "process_or_server_instance_id": _effect_row_process(table, row),
                "run_id": run_id,
                "wave_id": wave_id,
                "parent_run_status": parent_run,
                "parent_wave_status": parent_wave,
                "error_code": error_code,
                "liveness_classification": liveness_classification,
                "effect_safety_classification": effect_safety,
                "replay_allowed": False,
                "finished_at_present": bool(finished),
                "updated_at": str(row["updated_at"] or "") if "updated_at" in columns else "",
            }
            table_rows.append(item)
            all_rows.append(item)
        result[table] = {
            "counts": dict(sorted(counts.items())),
            "unresolved_effect_count": unresolved,
            "row_sample_limit": 25,
            "rows": table_rows[:25],
            "classification_counts": dict(sorted(Counter(str(item["liveness_classification"]) for item in table_rows).items())),
            "effect_safety_counts": dict(sorted(Counter(str(item["effect_safety_classification"]) for item in table_rows).items())),
        }

    def aggregate(field: str) -> dict[str, int]:
        return dict(sorted(Counter(str(item.get(field) or "<empty>") for item in all_rows).items()))

    safety_counts = Counter(str(item["effect_safety_classification"]) for item in all_rows)
    liveness_counts = Counter(str(item["liveness_classification"]) for item in all_rows)
    return {
        "snapshot_frontier": frontier,
        "tables": result,
        "unresolved_effect_count": len(all_rows),
        "classification_counts": dict(sorted(liveness_counts.items())),
        "effect_safety_counts": dict(sorted(safety_counts.items())),
        "orphan_safe_candidate_count": int(safety_counts.get("ORPHAN_SAFE_CANDIDATE", 0)),
        "owner_manual_evidence_count": int(safety_counts.get("OWNER_MANUAL_EVIDENCE", 0)),
        "stale_candidate_count": int(liveness_counts.get("STALE_CANDIDATE", 0)),
        "replay_allowed_count": 0,
        "aggregate_counts": {
            "process_or_server_instance_id": aggregate("process_or_server_instance_id"),
            "run_id": aggregate("run_id"),
            "wave_id": aggregate("wave_id"),
            "operation": aggregate("operation"),
            "error_code": aggregate("error_code"),
        },
        "sample_rows": all_rows[:25],
        "stale_candidates": [
            item for item in all_rows if item["liveness_classification"] == "STALE_CANDIDATE"
        ][:25],
        # A non-zero unresolved count is intentionally not called reconciled,
        # even if an individual row is an orphan-safe candidate.
        "reconciled": not all_rows,
    }


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


def _isolated_projection_reconciliation_probe(candidate: Path) -> dict[str, object]:
    """Apply only the proposed projection pointer update to a disposable clone.

    This is a semantics probe for the quarantined candidate.  It is deliberately
    not exposed as an importer/switch API and never opens the canonical ledger.
    """
    with tempfile.TemporaryDirectory(prefix="codex-ledger-projection-probe-") as temp:
        root = Path(temp)
        target = root / "ledger.sqlite3"
        shutil.copyfile(candidate, target)
        connection = sqlite3.connect(target)
        connection.row_factory = sqlite3.Row
        try:
            plan_before = _problem_projection_reconciliation_plan(connection)
            if not plan_before.get("applicable"):
                return {
                    "applicable": False,
                    "can_apply": False,
                    "valid": False,
                    "reason": "PROBLEM_PROJECTION_SCHEMA_NOT_APPLICABLE",
                }
            plans = plan_before.get("plans") or []
            if not plans or not plan_before.get("valid"):
                return {
                    "applicable": True,
                    "can_apply": False,
                    "valid": False,
                    "reason": "POINTER_ONLY_PLAN_NOT_SAFE",
                    "plans": plans,
                }
            before_threads = {
                str(row["problem_id"]): (
                    int(row["current_revision"]),
                    str(row["resolution_state"]),
                    int(row["latest_problem_event_seq"]),
                    str(row["latest_problem_event_hash"] or ""),
                )
                for row in connection.execute(
                    "SELECT problem_id,current_revision,resolution_state,latest_problem_event_seq,latest_problem_event_hash FROM problem_threads"
                )
            }
            before_events = [
                tuple(row)
                for row in connection.execute(
                    "SELECT problem_id,seq,event_id,event_hash,prev_hash FROM problem_events ORDER BY seq"
                )
            ]
            connection.execute("BEGIN IMMEDIATE")
            applied = 0
            for plan in plans:
                updated = connection.execute(
                    """UPDATE problem_threads
                          SET latest_problem_event_seq=?, latest_problem_event_hash=?
                        WHERE problem_id=?
                          AND latest_problem_event_seq=?
                          AND latest_problem_event_hash=?""",
                    (
                        int(plan["proposed_pointer_seq"]),
                        str(plan["proposed_pointer_hash"]),
                        str(plan["problem_id"]),
                        int(plan["current_pointer_seq"]),
                        str(plan["current_pointer_hash"]),
                    ),
                )
                if updated.rowcount != 1:
                    raise RuntimeError("RECOVERY_PROJECTION_POINTER_COMPARE_AND_SWAP_FAILED")
                applied += updated.rowcount
            connection.commit()
            after_projection = _problem_projection(connection)
            after_plan = _problem_projection_reconciliation_plan(connection)
            after_threads = {
                str(row["problem_id"]): (
                    int(row["current_revision"]),
                    str(row["resolution_state"]),
                    int(row["latest_problem_event_seq"]),
                    str(row["latest_problem_event_hash"] or ""),
                )
                for row in connection.execute(
                    "SELECT problem_id,current_revision,resolution_state,latest_problem_event_seq,latest_problem_event_hash FROM problem_threads"
                )
            }
            after_events = [
                tuple(row)
                for row in connection.execute(
                    "SELECT problem_id,seq,event_id,event_hash,prev_hash FROM problem_events ORDER BY seq"
                )
            ]
            integrity = str(connection.execute("PRAGMA integrity_check").fetchone()[0])
            foreign_keys = len(list(connection.execute("PRAGMA foreign_key_check")))
            state_preserved = all(
                after_threads.get(problem_id, (None, None))[0:2] == before[0:2]
                for problem_id, before in before_threads.items()
            )
            events_preserved = before_events == after_events
            return {
                "applicable": True,
                "can_apply": False,
                "clone_only": True,
                "applied_pointer_count": applied,
                "projection_valid_after": bool(after_projection.get("valid")),
                "remaining_plan_count": len(after_plan.get("plans") or []),
                "state_and_revision_preserved": state_preserved,
                "events_preserved": events_preserved,
                "integrity": integrity,
                "foreign_key_rows": foreign_keys,
                "valid": bool(
                    applied == len(plans)
                    and after_projection.get("valid")
                    and not after_plan.get("plans")
                    and state_preserved
                    and events_preserved
                    and integrity == "ok"
                    and foreign_keys == 0
                ),
            }
        finally:
            connection.close()


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
        projection_plans = {
            name: _problem_projection_reconciliation_plan(connection)
            for name, connection in connections.items()
        }
        effects = {name: _unknown_effects(connection) for name, connection in connections.items()}
    finally:
        for connection in connections.values():
            connection.close()
    append_probe = _append_and_duplicate_probe(candidate)
    projection_probe = _isolated_projection_reconciliation_probe(candidate)
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
        "problem_projection_reconciliation": projection_plans,
        "unknown_effects": effects,
        "append_duplicate_authority_probe": append_probe,
        "isolated_projection_reconciliation_probe": projection_probe,
        "gates": {
            "structural_candidate": structural_ok,
            "problem_projection_reconciled": projection_ok,
            "problem_projection_pointer_plan_safe": bool(
                projection_plans["candidate"].get("valid")
                and projection_plans["candidate"].get("plans")
            ),
            "unknown_effects_reconciled": effect_ok,
            "append_duplicate_probe": bool(append_probe.get("valid")),
            "isolated_projection_reconciliation_probe": bool(projection_probe.get("valid")),
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
