"""Guarded exact completed-agent lane reconciliation for a stopped runtime.

The normal lane-closing authority is ``task_control`` on Coding MCP.  This
operator-only primitive exists solely for the bootstrap deadlock in which the
runtime is stopped, activation refuses to start while a lane is live, and the
real external agent task has independently reached a terminal turn.  It reads
one immutable Backup-API census, binds every target identity and terminal-turn
observation, then calls the supported ledger authority method.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .lifecycle_census import lifecycle_census, open_lifecycle_census_snapshot, read_task_projection
from .orchestration_ledger import OrchestrationLedger


_LIVE_LANE_LIFECYCLES = frozenset({"starting", "active", "waiting", "idle"})
_ACTIVE_JOB_LIFECYCLES = frozenset({"starting", "active", "waiting", "idle", "running"})


class ExactCompletedAgentLaneReconciliationError(RuntimeError):
    """An exact completed-agent lane maintenance guard did not hold."""


@dataclass(frozen=True)
class ExactCompletedAgentLaneReconciliationReceipt:
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
    snapshot = value.get("snapshot") if isinstance(value.get("snapshot"), dict) else {}
    lifecycle = value.get("lifecycle") if isinstance(value.get("lifecycle"), dict) else {}
    target = value.get("target") if isinstance(value.get("target"), dict) else {}
    return {
        "snapshot": {
            key: snapshot.get(key)
            for key in (
                "snapshot_at",
                "sha256",
                "logical_sha256",
                "size_bytes",
                "schema_version",
                "integrity_check",
                "foreign_key_check_rows",
            )
        },
        "lifecycle": {
            key: lifecycle.get(key)
            for key in (
                "ordinary_active_runs",
                "awaiting_acceptance_runs",
                "unexplained_active_runs",
                "unbound_live_resource_residues",
                "projection_drift",
                "managed_job_residue",
                "terminal_parent_lane_residue",
            )
        },
        "target": {
            key: target.get(key)
            for key in (
                "lane_id",
                "run_id",
                "wave_id",
                "semantic_key",
                "thread_id",
                "session_id",
                "lane_last_turn_id",
                "external_completed_turn_id",
                "external_thread_status",
                "externally_observed_at",
                "lane_lifecycle",
                "lane_updated_at",
                "run_status",
                "run_state",
                "run_last_event_seq",
                "run_last_event_hash",
                "live_ownership",
                "p5_anchor",
                "already_reconciled",
            )
        },
        **({
            key: value.get(key)
            for key in (
                "changed",
                "idempotent",
                "chain_ok",
                "parent_state",
                "external_completed_turn_id",
            )
            if key in value
        }),
    }


def _json_object(value: object) -> dict[str, Any]:
    try:
        decoded = json.loads(str(value or "{}"))
    except json.JSONDecodeError:
        return {}
    return decoded if isinstance(decoded, dict) else {}


def _snapshot_preflight(
    workspace: Path,
    *,
    lane_id: str,
    run_id: str,
    wave_id: str,
    semantic_key: str,
    thread_id: str,
    session_id: str,
    expected_lane_last_turn_id: str,
    external_completed_turn_id: str,
    external_thread_status: str,
    externally_observed_at: str,
    observed_at: float,
) -> dict[str, Any]:
    root = Path(workspace).resolve(strict=False)
    identifiers = {
        "lane_id": str(lane_id or "").strip(),
        "run_id": str(run_id or "").strip(),
        "wave_id": str(wave_id or "").strip(),
        "semantic_key": str(semantic_key or "").strip(),
        "thread_id": str(thread_id or "").strip(),
        "session_id": str(session_id or "").strip(),
        "expected_lane_last_turn_id": str(expected_lane_last_turn_id or "").strip(),
        "external_completed_turn_id": str(external_completed_turn_id or "").strip(),
        "external_thread_status": str(external_thread_status or "").strip().lower(),
        "externally_observed_at": str(externally_observed_at or "").strip(),
    }
    if not all(identifiers.values()) or any(len(value) > 512 for value in identifiers.values()):
        raise ExactCompletedAgentLaneReconciliationError(
            "exact completed-agent lane reconciliation requires complete bounded identities"
        )
    with open_lifecycle_census_snapshot(root) as snapshot:
        census = lifecycle_census(
            snapshot,
            workspace=root,
            observed_at=observed_at,
            grace_seconds=15 * 60,
            stale_after_seconds=24 * 60 * 60,
            projection=read_task_projection(root),
        )
        lanes = snapshot.lifecycle.rows("agent_lanes")
        lane = next((row for row in lanes if str(row["lane_id"] or "") == identifiers["lane_id"]), None)
        if lane is None:
            raise ExactCompletedAgentLaneReconciliationError(
                "exact completed-agent lane target is absent from the immutable lifecycle census"
            )
        canonical_run_id = str(lane["run_id"] or "")
        canonical_wave_id = str(lane["wave_id"] or "")
        run = snapshot.facts.get_run(canonical_run_id)
        wave = next(
            (item for item in snapshot.facts.list_waves(canonical_run_id) if str(item.get("wave_id") or "") == canonical_wave_id),
            None,
        )
        events = snapshot.facts.list_events(canonical_run_id)
        last = events[-1] if events else {}
        metadata = _json_object(lane["metadata_json"])
        receipt = metadata.get("completed_agent_lane_reconciliation")
        receipt = receipt if isinstance(receipt, dict) else {}
        live_ownership = {
            "active_controller_leases": sum(
                1
                for row in snapshot.lifecycle.rows("controller_leases")
                if str(row["run_id"] or "") == canonical_run_id and str(row["status"] or "") == "active"
            ),
            "active_write_fences": sum(
                1
                for row in snapshot.lifecycle.rows("write_fences")
                if (str(row["run_id"] or "") == canonical_run_id or str(row["wave_id"] or "") == canonical_wave_id)
                and str(row["status"] or "") == "active"
            ),
            "running_background_operations": sum(
                1
                for row in snapshot.lifecycle.rows("background_operations")
                if (str(row["run_id"] or "") == canonical_run_id or str(row["wave_id"] or "") == canonical_wave_id)
                and str(row["status"] or "") == "running"
            ),
            "live_managed_jobs": sum(
                1
                for row in snapshot.lifecycle.rows("managed_process_jobs")
                if (str(row["run_id"] or "") == canonical_run_id or str(row["wave_id"] or "") == canonical_wave_id)
                and str(row["lifecycle_state"] or "") in _ACTIVE_JOB_LIFECYCLES
            ),
            "other_live_agent_lanes": sum(
                1
                for row in lanes
                if str(row["run_id"] or "") == canonical_run_id
                and str(row["lane_id"] or "") != identifiers["lane_id"]
                and str(row["lifecycle"] or "") in _LIVE_LANE_LIFECYCLES
            ),
        }
        p5_anchor = any(
            str(row["ledger_run_id"] or "") == canonical_run_id
            for row in snapshot.lifecycle.rows("p5_experiment_epochs")
        )
        summary = census.get("summary") if isinstance(census.get("summary"), dict) else {}
        classifications = (
            summary.get("run_classification_counts")
            if isinstance(summary.get("run_classification_counts"), dict)
            else {}
        )
        return {
            "snapshot": dict(snapshot.snapshot_metadata),
            "lifecycle": {
                "ordinary_active_runs": int(summary.get("ordinary_active_runs") or 0),
                "awaiting_acceptance_runs": int(classifications.get("AWAITING_ACCEPTANCE") or 0),
                "unexplained_active_runs": int(summary.get("unexplained_active_runs") or 0),
                "unbound_live_resource_residues": int(summary.get("unbound_live_resource_residues") or 0),
                "projection_drift": bool(summary.get("projection_drift")),
                "managed_job_residue": bool(census.get("managed_jobs")),
                "terminal_parent_lane_residue": bool(census.get("terminal_parent_lanes")),
            },
            "target": {
                "lane_id": str(lane["lane_id"] or ""),
                "run_id": canonical_run_id,
                "wave_id": canonical_wave_id,
                "wave_matches_run": bool(wave is not None),
                "semantic_key": str(lane["semantic_key"] or ""),
                "thread_id": str(lane["thread_id"] or ""),
                "session_id": str(lane["session_id"] or ""),
                "lane_last_turn_id": str(lane["last_turn_id"] or ""),
                "external_completed_turn_id": identifiers["external_completed_turn_id"],
                "external_thread_status": identifiers["external_thread_status"],
                "externally_observed_at": identifiers["externally_observed_at"],
                "lane_lifecycle": str(lane["lifecycle"] or "").lower(),
                "lane_updated_at": str(lane["updated_at"] or ""),
                "run_status": str((run or {}).get("status") or "").lower(),
                "run_state": str(last.get("state_after") or "").upper(),
                "run_last_event_seq": int(last.get("seq") or 0),
                "run_last_event_hash": str(last.get("event_hash") or ""),
                "live_ownership": live_ownership,
                "p5_anchor": p5_anchor,
                "already_reconciled": str(lane["lifecycle"] or "").lower() == "closed" and bool(receipt),
                "receipt": receipt,
            },
            "expected": identifiers,
        }


def _assert_preflight(preflight: dict[str, Any]) -> None:
    snapshot = preflight.get("snapshot") if isinstance(preflight.get("snapshot"), dict) else {}
    lifecycle = preflight.get("lifecycle") if isinstance(preflight.get("lifecycle"), dict) else {}
    target = preflight.get("target") if isinstance(preflight.get("target"), dict) else {}
    expected = preflight.get("expected") if isinstance(preflight.get("expected"), dict) else {}
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
    identity_pairs = (
        ("lane_id", "lane_id"),
        ("run_id", "run_id"),
        ("wave_id", "wave_id"),
        ("semantic_key", "semantic_key"),
        ("thread_id", "thread_id"),
        ("session_id", "session_id"),
        ("lane_last_turn_id", "expected_lane_last_turn_id"),
        ("external_completed_turn_id", "external_completed_turn_id"),
        ("external_thread_status", "external_thread_status"),
        ("externally_observed_at", "externally_observed_at"),
    )
    for target_key, expected_key in identity_pairs:
        if str(target.get(target_key) or "") != str(expected.get(expected_key) or ""):
            blockers.append(f"{target_key}_mismatch")
    if not target.get("wave_matches_run"):
        blockers.append("wave_not_bound_to_run")
    if str(target.get("run_status") or "") != "active":
        blockers.append("parent_run_not_active")
    if str(target.get("run_state") or "") != "ACCEPTING":
        blockers.append("parent_run_not_accepting")
    if str(target.get("external_thread_status") or "") not in {"idle", "completed"}:
        blockers.append("external_thread_not_terminal")
    if str(target.get("external_completed_turn_id") or "") == str(target.get("lane_last_turn_id") or ""):
        blockers.append("completion_turn_not_later_than_lane_turn")
    if any(int(value or 0) > 0 for value in (target.get("live_ownership") or {}).values()):
        blockers.append("competing_live_ownership")
    if target.get("p5_anchor"):
        blockers.append("target_is_p5_anchor")
    lane_lifecycle = str(target.get("lane_lifecycle") or "")
    if lane_lifecycle == "closed":
        receipt = target.get("receipt") if isinstance(target.get("receipt"), dict) else {}
        if not target.get("already_reconciled"):
            blockers.append("closed_lane_without_reconciliation_receipt")
        if (
            str(receipt.get("run_id") or "") != str(target.get("run_id") or "")
            or str(receipt.get("wave_id") or "") != str(target.get("wave_id") or "")
            or str(receipt.get("thread_id") or "") != str(target.get("thread_id") or "")
            or str(receipt.get("external_completed_turn_id") or "")
            != str(target.get("external_completed_turn_id") or "")
        ):
            blockers.append("closed_lane_receipt_mismatch")
    elif lane_lifecycle not in _LIVE_LANE_LIFECYCLES:
        blockers.append("lane_lifecycle_not_reconcilable")
    if blockers:
        raise ExactCompletedAgentLaneReconciliationError(
            "exact completed-agent lane preflight failed: " + ",".join(blockers)
        )


def preflight_exact_completed_agent_lane_reconciliation(
    workspace: Path,
    *,
    lane_id: str,
    run_id: str,
    wave_id: str,
    semantic_key: str,
    thread_id: str,
    session_id: str,
    expected_lane_last_turn_id: str,
    external_completed_turn_id: str,
    external_thread_status: str,
    externally_observed_at: str,
    observed_at: float,
) -> dict[str, Any]:
    """Read only: produce one guarded immutable exact-lane preflight."""
    result = _snapshot_preflight(
        workspace,
        lane_id=lane_id,
        run_id=run_id,
        wave_id=wave_id,
        semantic_key=semantic_key,
        thread_id=thread_id,
        session_id=session_id,
        expected_lane_last_turn_id=expected_lane_last_turn_id,
        external_completed_turn_id=external_completed_turn_id,
        external_thread_status=external_thread_status,
        externally_observed_at=externally_observed_at,
        observed_at=observed_at,
    )
    _assert_preflight(result)
    return result


def reconcile_exact_completed_agent_lane(
    workspace: Path,
    *,
    lane_id: str,
    run_id: str,
    wave_id: str,
    semantic_key: str,
    thread_id: str,
    session_id: str,
    expected_lane_last_turn_id: str,
    external_completed_turn_id: str,
    external_thread_status: str,
    externally_observed_at: str,
    observed_at: float,
    expected_snapshot_sha256: str,
    expected_logical_sha256: str,
    runtime_stopped: bool,
    authority: str,
) -> ExactCompletedAgentLaneReconciliationReceipt:
    """Reconcile one preflighted completed external lane while runtime is stopped."""
    if runtime_stopped is not True:
        raise ExactCompletedAgentLaneReconciliationError(
            "exact completed-agent lane reconciliation requires explicit stopped-runtime authority"
        )
    arguments = {
        "lane_id": lane_id,
        "run_id": run_id,
        "wave_id": wave_id,
        "semantic_key": semantic_key,
        "thread_id": thread_id,
        "session_id": session_id,
        "expected_lane_last_turn_id": expected_lane_last_turn_id,
        "external_completed_turn_id": external_completed_turn_id,
        "external_thread_status": external_thread_status,
        "externally_observed_at": externally_observed_at,
        "observed_at": observed_at,
    }
    preflight = preflight_exact_completed_agent_lane_reconciliation(workspace, **arguments)
    snapshot = preflight["snapshot"]
    if str(snapshot.get("sha256") or "").lower() != str(expected_snapshot_sha256 or "").lower():
        raise ExactCompletedAgentLaneReconciliationError(
            "exact completed-agent lane physical snapshot changed or was not acknowledged"
        )
    if str(snapshot.get("logical_sha256") or "").lower() != str(expected_logical_sha256 or "").lower():
        raise ExactCompletedAgentLaneReconciliationError(
            "exact completed-agent lane logical snapshot changed or was not acknowledged"
        )
    target = preflight["target"]
    reconciliation = OrchestrationLedger(Path(workspace)).reconcile_exact_completed_agent_lane(
        lane_id=str(target["lane_id"]),
        expected_logical_sha256=str(snapshot["logical_sha256"]),
        expected_run_id=str(target["run_id"]),
        expected_wave_id=str(target["wave_id"]),
        expected_semantic_key=str(target["semantic_key"]),
        expected_thread_id=str(target["thread_id"]),
        expected_session_id=str(target["session_id"]),
        expected_lane_last_turn_id=str(target["lane_last_turn_id"]),
        expected_lane_lifecycle=str(target["lane_lifecycle"]),
        expected_lane_updated_at=str(target["lane_updated_at"]),
        expected_run_status=str(target["run_status"]),
        expected_run_state=str(target["run_state"]),
        expected_run_last_event_seq=int(target["run_last_event_seq"]),
        expected_run_last_event_hash=str(target["run_last_event_hash"]),
        external_completed_turn_id=str(target["external_completed_turn_id"]),
        external_thread_status=str(target["external_thread_status"]),
        externally_observed_at=str(target["externally_observed_at"]),
        runtime_stopped=True,
        authority=str(authority),
    )
    postflight = _snapshot_preflight(workspace, **arguments)
    _assert_preflight(postflight)
    chain_ok = bool(OrchestrationLedger(Path(workspace)).verify_chain(str(run_id)).get("ok"))
    if not chain_ok:
        raise ExactCompletedAgentLaneReconciliationError(
            "exact completed-agent lane reconciliation invalidated the target hash chain"
        )
    if str(postflight["target"].get("lane_lifecycle") or "") != "closed":
        raise ExactCompletedAgentLaneReconciliationError(
            "exact completed-agent lane postflight did not close the target"
        )
    return ExactCompletedAgentLaneReconciliationReceipt(
        preflight=preflight,
        reconciliation={**reconciliation, "chain_ok": chain_ok},
        postflight=postflight,
    )
