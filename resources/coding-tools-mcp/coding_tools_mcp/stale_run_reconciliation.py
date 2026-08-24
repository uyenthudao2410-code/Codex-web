"""Guarded, exact-ID stale-run reconciliation for the canonical ledger.

This operator-only primitive is intentionally not an MCP action.  It begins
from one immutable Backup-API census, refuses unrelated lifecycle residue, and
requires the Recovery Host-owned runtime to be stopped before it calls the
supported exact-ID ledger authority.  It neither creates workload nor uses the
legacy bulk stale-run helper.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .lifecycle_census import lifecycle_census, open_lifecycle_census_snapshot, read_task_projection
from .orchestration_ledger import OrchestrationLedger


class ExactStaleRunReconciliationError(RuntimeError):
    """An exact stale-run maintenance guard did not hold."""


@dataclass(frozen=True)
class ExactStaleRunReconciliationReceipt:
    preflight: dict[str, Any]
    reconciliation: dict[str, Any]
    postflight: dict[str, Any]

    def projection(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "preflight": _safe_projection(self.preflight),
            "reconciliation": _safe_projection(self.reconciliation),
            "postflight": _safe_projection(self.postflight),
        }


def _safe_projection(value: dict[str, Any]) -> dict[str, Any]:
    target = value.get("target") if isinstance(value.get("target"), dict) else {}
    snapshot = value.get("snapshot") if isinstance(value.get("snapshot"), dict) else {}
    lifecycle = value.get("lifecycle") if isinstance(value.get("lifecycle"), dict) else {}
    return {
        "snapshot": {
            key: snapshot.get(key)
            for key in ("snapshot_at", "sha256", "logical_sha256", "size_bytes", "schema_version", "integrity_check", "foreign_key_check_rows")
        },
        "lifecycle": {
            key: lifecycle.get(key)
            for key in ("ordinary_active_runs", "unexplained_active_runs", "unbound_live_resource_residues", "projection_drift", "p5_epochs")
        },
        "target": {
            key: target.get(key)
            for key in ("status", "classification", "reason_codes", "has_live_ownership", "already_reconciled")
        },
        **({
            key: value.get(key)
            for key in ("changed", "idempotent", "chain_ok")
            if key in value
        }),
    }


def _reconciled_stale_target_record(snapshot: Any, *, run_id: str) -> dict[str, Any] | None:
    """Return the narrow terminal projection that census intentionally omits.

    ``lifecycle_census`` is an active-state classifier: it does not emit an
    ordinary terminal run unless that run has a live child contradiction.  A
    successful exact reconciliation therefore disappears from its ``runs``
    list.  The idempotent path must not mistake that deliberate omission for a
    missing target, but it also must not make arbitrary terminal rows eligible.
    Only a stale run whose *current* final event is the exact reconciliation
    receipt is accepted here.
    """
    facts = snapshot.facts
    lifecycle = snapshot.lifecycle
    run = facts.get_run(run_id)
    if run is None or str(run.get("status") or "").lower() != "stale":
        return None
    events = facts.list_events(run_id)
    if not events:
        return None
    last = events[-1]
    if str(last.get("event_type") or "") != "run_stale_reconciled":
        return None
    if str(last.get("state_after") or "").upper() != "ABORTED":
        return None
    p5_epoch = next(
        (
            row
            for row in lifecycle.rows("p5_experiment_epochs")
            if str(row["ledger_run_id"] or "") == run_id
        ),
        None,
    )
    return {
        "run_id": run_id,
        "run_status": "stale",
        "classification": "RECONCILED_STALE",
        "reasons": ("exact_stale_reconciliation_receipt",),
        # The receipt is necessarily the latest activity after reconciliation;
        # this matches the optimistic activity guard in the ledger authority.
        "latest_activity_at": str(last.get("event_time") or ""),
        "last_event": {
            "seq": int(last.get("seq") or 0),
            "hash": str(last.get("event_hash") or ""),
        },
        # A terminal run with a live child would be emitted by the census as a
        # TERMINAL_PARENT_CONTRADICTION instead of reaching this fallback.
        "ownership": {},
        "p5_epoch_lifecycle": str(p5_epoch["lifecycle"] or "") if p5_epoch is not None else None,
    }


def _snapshot_preflight(workspace: Path, *, run_id: str, observed_at: float) -> dict[str, Any]:
    root = Path(workspace).resolve(strict=False)
    identifier = str(run_id or "").strip()
    if not identifier or len(identifier) > 256:
        raise ExactStaleRunReconciliationError("exact stale-run reconciliation requires one bounded run_id")
    with open_lifecycle_census_snapshot(root) as snapshot:
        census = lifecycle_census(
            snapshot,
            workspace=root,
            observed_at=observed_at,
            grace_seconds=15 * 60,
            stale_after_seconds=24 * 60 * 60,
            projection=read_task_projection(root),
        )
        record = next((item for item in census.get("runs", []) if str(item.get("run_id") or "") == identifier), None)
        if record is None:
            record = _reconciled_stale_target_record(snapshot, run_id=identifier)
        if record is None:
            raise ExactStaleRunReconciliationError("exact stale-run target is absent from the immutable lifecycle census")
        ownership = record.get("ownership") if isinstance(record.get("ownership"), dict) else {}
        return {
            "snapshot": dict(snapshot.snapshot_metadata),
            "lifecycle": {
                "ordinary_active_runs": int((census.get("summary") or {}).get("ordinary_active_runs") or 0),
                "unexplained_active_runs": int((census.get("summary") or {}).get("unexplained_active_runs") or 0),
                "unbound_live_resource_residues": int((census.get("summary") or {}).get("unbound_live_resource_residues") or 0),
                "projection_drift": bool((census.get("summary") or {}).get("projection_drift")),
                "p5_epochs": int((census.get("summary") or {}).get("p5_epochs") or 0),
                "managed_job_residue": bool(census.get("managed_jobs")),
                "terminal_parent_lane_residue": bool(census.get("terminal_parent_lanes")),
            },
            "target": {
                "run_id": identifier,
                "status": str(record.get("run_status") or ""),
                "classification": str(record.get("classification") or ""),
                "reason_codes": tuple(sorted(str(item) for item in record.get("reasons") or [])),
                "latest_activity_at": str(record.get("latest_activity_at") or ""),
                "last_event_seq": int((record.get("last_event") or {}).get("seq") or 0),
                "last_event_hash": str((record.get("last_event") or {}).get("hash") or ""),
                "has_live_ownership": any(int(value or 0) > 0 for value in ownership.values()),
                "p5_epoch_lifecycle": str(record.get("p5_epoch_lifecycle") or ""),
                "already_reconciled": str(record.get("run_status") or "") == "stale",
            },
            "observed_at_unix_seconds": float(observed_at),
            "stale_after_seconds": float((census.get("thresholds") or {}).get("stale_after_seconds") or 0),
        }


def _assert_preflight(preflight: dict[str, Any]) -> None:
    snapshot = preflight.get("snapshot") if isinstance(preflight.get("snapshot"), dict) else {}
    lifecycle = preflight.get("lifecycle") if isinstance(preflight.get("lifecycle"), dict) else {}
    target = preflight.get("target") if isinstance(preflight.get("target"), dict) else {}
    blockers: list[str] = []
    if snapshot.get("integrity_check") != ["ok"]:
        blockers.append("integrity_check_failed")
    if int(snapshot.get("foreign_key_check_rows") or 0) != 0:
        blockers.append("foreign_key_check_failed")
    if int(lifecycle.get("unexplained_active_runs") or 0) != 0:
        blockers.append("unexplained_active_runs")
    if int(lifecycle.get("unbound_live_resource_residues") or 0) != 0:
        blockers.append("unbound_live_resource_residues")
    if lifecycle.get("managed_job_residue"):
        blockers.append("managed_job_residue")
    if lifecycle.get("terminal_parent_lane_residue"):
        blockers.append("terminal_parent_lane_residue")
    status = str(target.get("status") or "")
    if status == "stale":
        if not target.get("already_reconciled"):
            blockers.append("terminal_target_without_reconciliation_receipt")
        if str(target.get("classification") or "") != "RECONCILED_STALE":
            blockers.append("terminal_target_has_live_child_or_unrecognized_lifecycle")
    else:
        if status != "active":
            blockers.append("target_not_active")
        if str(target.get("classification") or "") != "THRESHOLD_SENSITIVE_STALE_CANDIDATE":
            blockers.append("target_not_threshold_candidate")
        if "meets_current_stale_threshold" not in set(target.get("reason_codes") or ()):
            blockers.append("target_below_stale_threshold")
        if target.get("has_live_ownership"):
            blockers.append("target_has_live_ownership")
    if target.get("p5_epoch_lifecycle"):
        blockers.append("target_is_p5_anchor")
    if not str(target.get("latest_activity_at") or ""):
        blockers.append("target_activity_guard_missing")
    if blockers:
        raise ExactStaleRunReconciliationError("exact stale-run preflight failed: " + ",".join(blockers))


def preflight_exact_stale_run_reconciliation(workspace: Path, *, run_id: str, observed_at: float) -> dict[str, Any]:
    """Read only: produce one guarded immutable exact-run preflight."""
    result = _snapshot_preflight(workspace, run_id=run_id, observed_at=observed_at)
    _assert_preflight(result)
    return result


def reconcile_exact_stale_run(
    workspace: Path,
    *,
    run_id: str,
    observed_at: float,
    expected_snapshot_sha256: str,
    expected_logical_sha256: str,
    runtime_stopped: bool,
    authority: str,
) -> ExactStaleRunReconciliationReceipt:
    """Reconcile one preflighted row while the canonical runtime is stopped."""
    if runtime_stopped is not True:
        raise ExactStaleRunReconciliationError("exact stale-run reconciliation requires explicit stopped-runtime authority")
    preflight = preflight_exact_stale_run_reconciliation(workspace, run_id=run_id, observed_at=observed_at)
    snapshot = preflight["snapshot"]
    if str(snapshot.get("sha256") or "").lower() != str(expected_snapshot_sha256 or "").lower():
        raise ExactStaleRunReconciliationError("exact stale-run physical snapshot changed or was not acknowledged")
    if str(snapshot.get("logical_sha256") or "").lower() != str(expected_logical_sha256 or "").lower():
        raise ExactStaleRunReconciliationError("exact stale-run logical snapshot changed or was not acknowledged")
    target = preflight["target"]
    reconciliation = OrchestrationLedger(Path(workspace)).reconcile_exact_stale_run(
        run_id=str(target["run_id"]),
        expected_logical_sha256=str(snapshot["logical_sha256"]),
        expected_run_status=str(target["status"]),
        expected_latest_activity_at=str(target["latest_activity_at"]),
        expected_run_last_event_seq=int(target["last_event_seq"]),
        expected_run_last_event_hash=str(target["last_event_hash"]),
        observed_at_unix_seconds=float(preflight["observed_at_unix_seconds"]),
        stale_after_seconds=float(preflight["stale_after_seconds"]),
        authority=str(authority),
    )
    postflight = _snapshot_preflight(workspace, run_id=run_id, observed_at=observed_at)
    _assert_preflight(postflight)
    chain_ok = bool(OrchestrationLedger(Path(workspace)).verify_chain(str(run_id)).get("ok"))
    if not chain_ok:
        raise ExactStaleRunReconciliationError("exact stale-run reconciliation invalidated the target hash chain")
    return ExactStaleRunReconciliationReceipt(
        preflight=preflight,
        reconciliation={**reconciliation, "chain_ok": chain_ok},
        postflight=postflight,
    )
