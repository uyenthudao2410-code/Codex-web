from __future__ import annotations

"""Guarded local activation for the additive Problem Resolution Lineage schema.

This module is intentionally an operator-only source primitive, not an MCP
action.  It creates one immutable Backup-API preflight snapshot, refuses every
live lifecycle/resource residue, and requires an explicit acknowledgement that
the owned runtime has stopped before calling the supported
``OrchestrationLedger.migrate_problem_lineage_schema`` authority.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .lifecycle_census import lifecycle_census, open_lifecycle_census_snapshot, read_task_projection
from .ledger_maintenance import inspect_maintenance_readiness
from .orchestration_ledger import OrchestrationLedger
from .problem_lineage import PROBLEM_SCHEMA_VERSION, ProblemLineageError


_TERMINAL_P5_LIFECYCLES = frozenset({"EPOCH_CLOSED", "EPOCH_HARD_STOPPED"})


class ProblemLineageActivationError(RuntimeError):
    """Activation preflight or one-way migration guard did not hold."""


@dataclass(frozen=True)
class ProblemLineageActivationReceipt:
    preflight: dict[str, Any]
    migration: dict[str, Any]
    postflight: dict[str, Any]

    def projection(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "preflight": self.preflight,
            "migration": self.migration,
            "postflight": self.postflight,
        }


def _snapshot_projection(workspace: Path, *, observed_at: float) -> dict[str, Any]:
    root = Path(workspace).resolve(strict=False)
    with open_lifecycle_census_snapshot(root) as snapshot:
        census = lifecycle_census(
            snapshot,
            workspace=root,
            observed_at=observed_at,
            grace_seconds=15 * 60,
            stale_after_seconds=24 * 60 * 60,
            projection=read_task_projection(root),
        )
        reader = snapshot._reader
        if reader is None:
            raise ProblemLineageActivationError("immutable activation snapshot reader is unavailable")
        tables = [
            str(row[0])
            for row in reader.rows(
                "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('problem_threads','problem_revisions','problem_events') ORDER BY name"
            )
        ]
        indexes = [
            str(row[0])
            for row in reader.rows(
                "SELECT name FROM sqlite_master WHERE type='index' "
                "AND name IN ('idx_problem_events_problem_seq','idx_problem_events_problem_revision_seq','idx_problem_events_task_turn','idx_problem_events_run_wave','idx_problem_events_one_primary_run_binding') "
                "ORDER BY name"
            )
        ]
        problem_event_columns = [
            str(row[1])
            for row in reader.rows("PRAGMA table_info(problem_events)")
        ] if "problem_events" in tables else []
        event_chain_failures = [
            str(run_id)
            for run_id in sorted(snapshot.facts._runs)
            if snapshot.facts.verify_chain(run_id).get("ok") is not True
        ]
        p5_lifecycles = sorted(
            {
                str(item.get("p5_epoch_lifecycle") or "")
                for item in census.get("runs", [])
                if str(item.get("classification") or "") == "P5_EXPERIMENT_ANCHOR"
            }
        )
        return {
            "snapshot": dict(snapshot.snapshot_metadata),
            "lifecycle": {
                "summary": dict(census.get("summary") or {}),
                "managed_jobs": list(census.get("managed_jobs") or []),
                "terminal_parent_lanes": list(census.get("terminal_parent_lanes") or []),
                "unbound_live_resources": list(census.get("unbound_live_resources") or []),
                "p5_lifecycles": p5_lifecycles,
            },
            "schema": {
                "user_version": int((snapshot.snapshot_metadata or {}).get("schema_version") or 0),
                "problem_tables": tables,
                "problem_indexes": indexes,
                "problem_event_columns": problem_event_columns,
            },
            "event_chain": {
                "checked_runs": len(snapshot.facts._runs),
                "invalid_run_ids": event_chain_failures,
            },
        }


def _assert_preflight(preflight: dict[str, Any], *, activation_preflight: bool) -> None:
    snapshot = preflight.get("snapshot") if isinstance(preflight.get("snapshot"), dict) else {}
    lifecycle = preflight.get("lifecycle") if isinstance(preflight.get("lifecycle"), dict) else {}
    summary = lifecycle.get("summary") if isinstance(lifecycle.get("summary"), dict) else {}
    schema = preflight.get("schema") if isinstance(preflight.get("schema"), dict) else {}
    event_chain = preflight.get("event_chain") if isinstance(preflight.get("event_chain"), dict) else {}
    blockers: list[str] = []
    if snapshot.get("integrity_check") != ["ok"]:
        blockers.append("integrity_check_failed")
    if int(snapshot.get("foreign_key_check_rows") or 0) != 0:
        blockers.append("foreign_key_check_failed")
    if int(summary.get("unexplained_active_runs") or 0) != 0:
        blockers.append("unexplained_active_runs")
    if int(summary.get("unbound_live_resource_residues") or 0) != 0:
        blockers.append("unbound_live_resource_residues")
    if lifecycle.get("managed_jobs"):
        blockers.append("managed_job_residue")
    if lifecycle.get("terminal_parent_lanes"):
        blockers.append("terminal_parent_lane_residue")
    if lifecycle.get("unbound_live_resources"):
        blockers.append("unbound_live_resource_residue")
    if any(value and value not in _TERMINAL_P5_LIFECYCLES for value in lifecycle.get("p5_lifecycles") or []):
        blockers.append("nonterminal_p5_epoch")
    if event_chain.get("invalid_run_ids"):
        blockers.append("run_event_hash_chain_failure")
    current_schema = int(schema.get("user_version") or 0)
    tables, indexes = set(schema.get("problem_tables") or []), set(schema.get("problem_indexes") or [])
    if activation_preflight:
        if current_schema not in {9, 10, 11}:
            blockers.append(f"unexpected_schema_version_{current_schema}")
        elif current_schema == 9:
            if tables:
                blockers.append("problem_tables_present_before_prl_activation")
        elif current_schema == 10:
            expected_v10_tables = {"problem_threads", "problem_events"}
            expected_v10_indexes = {
                "idx_problem_events_problem_seq",
                "idx_problem_events_task_turn",
                "idx_problem_events_run_wave",
                "idx_problem_events_one_primary_run_binding",
            }
            if tables != expected_v10_tables:
                blockers.append("v10_problem_tables_incomplete")
            if indexes != expected_v10_indexes:
                blockers.append("v10_problem_indexes_incomplete")
        else:
            expected_v11_tables = {"problem_threads", "problem_revisions", "problem_events"}
            expected_v11_indexes = {
                "idx_problem_events_problem_seq",
                "idx_problem_events_problem_revision_seq",
                "idx_problem_events_task_turn",
                "idx_problem_events_run_wave",
                "idx_problem_events_one_primary_run_binding",
            }
            if tables != expected_v11_tables:
                blockers.append("v11_problem_tables_incomplete")
            if indexes != expected_v11_indexes:
                blockers.append("v11_problem_indexes_incomplete")
            receipt_columns = {"outcome_receipt_type", "outcome_receipt_id"}
            if receipt_columns.intersection(set(schema.get("problem_event_columns") or [])):
                blockers.append("v11_outcome_receipt_columns_already_present")
    else:
        if current_schema != PROBLEM_SCHEMA_VERSION:
            blockers.append(f"unexpected_schema_version_{current_schema}")
        expected_tables = {"problem_threads", "problem_revisions", "problem_events"}
        expected_indexes = {
            "idx_problem_events_problem_seq",
            "idx_problem_events_problem_revision_seq",
            "idx_problem_events_task_turn",
            "idx_problem_events_run_wave",
            "idx_problem_events_one_primary_run_binding",
        }
        if tables != expected_tables:
            blockers.append("problem_tables_incomplete")
        if indexes != expected_indexes:
            blockers.append("problem_indexes_incomplete")
        receipt_columns = {"outcome_receipt_type", "outcome_receipt_id"}
        if not receipt_columns.issubset(set(schema.get("problem_event_columns") or [])):
            blockers.append("outcome_receipt_columns_missing")
    if blockers:
        raise ProblemLineageActivationError("PRL activation preflight failed: " + ",".join(blockers))


def preflight_problem_lineage_activation(
    workspace: Path,
    *,
    observed_at: float,
    allow_already_active: bool = False,
) -> dict[str, Any]:
    """Read only: one immutable snapshot plus current resource readiness."""
    root = Path(workspace).resolve(strict=False)
    snapshot = _snapshot_projection(root, observed_at=observed_at)
    maintenance = inspect_maintenance_readiness(root)
    result = {
        "schema_version": 1,
        "workspace": str(root),
        **snapshot,
        "maintenance": {
            key: maintenance.get(key)
            for key in (
                "ledger_sha256",
                "logical_sha256",
                "integrity_check",
                "foreign_key_violations",
                "active_controller_leases",
                "active_write_fences",
                "active_managed_jobs",
                "active_background_operations",
                "compact_allowed",
                "blockers",
            )
        },
    }
    current_schema = int(result.get("schema", {}).get("user_version") or 0)
    _assert_preflight(
        result,
        activation_preflight=not (allow_already_active and current_schema == PROBLEM_SCHEMA_VERSION),
    )
    if result["maintenance"].get("blockers"):
        raise ProblemLineageActivationError(
            "PRL activation maintenance readiness failed: " + ",".join(str(item) for item in result["maintenance"]["blockers"])
        )
    return result


def activate_problem_lineage_schema(
    workspace: Path,
    *,
    observed_at: float,
    expected_snapshot_sha256: str,
    expected_logical_sha256: str,
    runtime_stopped: bool,
) -> ProblemLineageActivationReceipt:
    """Run the supported one-way v9/v10/v11→v12 migration after exact preflight.

    The caller must stop the authoritative runtime through its owning Recovery
    Host before passing ``runtime_stopped=True``.  This function never starts,
    restarts, or kills a process and deliberately does not create a workload.
    """
    if runtime_stopped is not True:
        raise ProblemLineageActivationError("PRL canonical migration requires explicit stopped-runtime authority")
    preflight = preflight_problem_lineage_activation(
        workspace,
        observed_at=observed_at,
        allow_already_active=True,
    )
    snapshot = preflight["snapshot"]
    if str(snapshot.get("sha256") or "").lower() != str(expected_snapshot_sha256 or "").lower():
        raise ProblemLineageActivationError("PRL activation snapshot SHA-256 changed or was not explicitly acknowledged")
    if str(snapshot.get("logical_sha256") or "").lower() != str(expected_logical_sha256 or "").lower():
        raise ProblemLineageActivationError("PRL activation logical SHA-256 changed or was not explicitly acknowledged")
    try:
        source_schema = int(preflight["schema"]["user_version"])
        if source_schema == PROBLEM_SCHEMA_VERSION:
            migration = {"migrated": False, "schema_version": PROBLEM_SCHEMA_VERSION}
        else:
            migration = OrchestrationLedger(Path(workspace)).migrate_problem_lineage_schema(expected_schema_version=source_schema)
    except ProblemLineageError as exc:
        raise ProblemLineageActivationError(str(exc)) from exc
    postflight = _snapshot_projection(Path(workspace), observed_at=observed_at)
    _assert_preflight(postflight, activation_preflight=False)
    if str(preflight["event_chain"]) != str(postflight["event_chain"]):
        raise ProblemLineageActivationError("event-chain verification changed during PRL schema activation")
    return ProblemLineageActivationReceipt(
        preflight=preflight,
        migration={"migrated": bool(migration.get("migrated")), "from_schema_version": source_schema, "schema_version": int(migration.get("schema_version") or 0)},
        postflight=postflight,
    )
