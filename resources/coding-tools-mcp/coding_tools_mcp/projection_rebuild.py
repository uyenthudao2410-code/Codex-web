"""Fail-closed task-projection rebuild receipts for activation epochs.

The canonical orchestration ledger remains the durable causal source.  This
module repairs only the compact task-state projection, then binds the observed
projection to one immutable lifecycle-census snapshot and the current runtime
identity.  Receipts are process-local evidence; they never replace or mutate
the ledger.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


PROJECTION_REBUILD_SCHEMA_VERSION = 1
PROJECTION_REBUILD_KIND = "coding_tools_mcp_projection_rebuild"
PROJECTION_REBUILD_MAX_AGE_MS = 5 * 60 * 1000
PROJECTION_REBUILD_FUTURE_SKEW_MS = 1_000
PROJECTION_REBUILD_ALLOWED_CLASSIFICATIONS = frozenset({
    "NO_ACTIVE_PROJECTION",
    "PROJECTION_CONSISTENT",
    "CHECKPOINTED",
    "BLOCKED",
    "ABORTED",
})

_HEX_DIGITS = frozenset("0123456789abcdef")
_RECEIPT_FIELDS = frozenset({
    "schema_version",
    "kind",
    "activation_epoch_id",
    "process_instance_id",
    "server_instance_id",
    "workspace",
    "ledger_snapshot_sha256",
    "ledger_logical_sha256",
    "ledger_integrity",
    "projection_classification",
    "projection",
    "completed_at",
    "completed_at_unix_ms",
    "reconciled",
    "integrity_sha256",
})
_LEDGER_INTEGRITY_FIELDS = frozenset({
    "backup_api_copy",
    "immutable",
    "query_only",
    "integrity_check",
    "foreign_key_check_rows",
})
_PROJECTION_FIELDS = frozenset({"run_id", "wave_id", "orchestration_state"})
_UNSET = object()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def canonical_sha256(value: Any) -> str:
    """Return the deterministic SHA-256 used by rebuild receipt integrity."""
    return hashlib.sha256(_canonical_json(value).encode("utf-8", errors="surrogatepass")).hexdigest()


def _without_integrity(receipt: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in receipt.items() if key != "integrity_sha256"}


def _is_digest(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(char in _HEX_DIGITS for char in value)


def _canonical_workspace(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    try:
        return str(Path(text).resolve(strict=False))
    except (OSError, RuntimeError, TypeError, ValueError):
        return ""


def _workspace_matches(left: Any, right: Any) -> bool:
    first = _canonical_workspace(left)
    second = _canonical_workspace(right)
    return bool(first and second and os.path.normcase(first) == os.path.normcase(second))


def _iso_at(unix_ms: int) -> str:
    return (
        datetime.fromtimestamp(unix_ms / 1000, timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def _parse_timestamp(value: Any) -> int | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text[:-1] + "+00:00" if text.endswith("Z") else text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return int(round(parsed.timestamp() * 1000))


def _projection_identity(value: Mapping[str, Any] | None) -> dict[str, str]:
    source = dict(value or {})
    nested = source.get("orchestration")
    if isinstance(nested, Mapping):
        source = dict(nested)
    return {
        "run_id": str(source.get("run_id") or "").strip(),
        "wave_id": str(source.get("wave_id") or "").strip(),
        "orchestration_state": str(source.get("orchestration_state") or "").strip().upper(),
    }


def _ledger_integrity(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "backup_api_copy": snapshot.get("backup_api_copy") is True,
        "immutable": snapshot.get("immutable") is True,
        "query_only": snapshot.get("query_only") is True,
        "integrity_check": list(snapshot.get("integrity_check") or []),
        "foreign_key_check_rows": snapshot.get("foreign_key_check_rows"),
    }


def _classification_matches_projection(classification: str, projection: Mapping[str, Any]) -> bool:
    if any(
        not isinstance(projection.get(field), str) or len(str(projection.get(field))) > 256
        for field in _PROJECTION_FIELDS
    ):
        return False
    run_id = str(projection.get("run_id") or "")
    wave_id = str(projection.get("wave_id") or "")
    state = str(projection.get("orchestration_state") or "")
    if classification == "NO_ACTIVE_PROJECTION":
        return not run_id and not wave_id and not state
    if not run_id or not wave_id or not state:
        return False
    expected_terminal = {
        "CHECKPOINTED": "CHECKPOINTED",
        "BLOCKED": "BLOCKED",
        "ABORTED": "ABORTED",
    }.get(classification)
    return expected_terminal is None or state == expected_terminal


def build_projection_rebuild_receipt(
    *,
    activation_epoch_id: Any,
    process_instance_id: Any,
    server_instance_id: Any,
    workspace: Path | str,
    ledger_snapshot: Mapping[str, Any],
    projection_classification: Any,
    projection: Mapping[str, Any] | None,
    reconciled: bool,
    completed_at_unix_ms: int | None = None,
) -> dict[str, Any]:
    """Build one canonical receipt from a post-reconciliation census snapshot."""
    epoch_id = str(activation_epoch_id or "").strip()
    process_id = str(process_instance_id or "").strip()
    server_id = str(server_instance_id or "").strip()
    root = _canonical_workspace(workspace)
    classification = str(projection_classification or "").strip().upper()
    physical_sha256 = str(ledger_snapshot.get("sha256") or "").strip().lower()
    logical_sha256 = str(ledger_snapshot.get("logical_sha256") or "").strip().lower()
    integrity = _ledger_integrity(ledger_snapshot)
    projection_identity = _projection_identity(projection)
    recorded_at = int(time.time() * 1000) if completed_at_unix_ms is None else completed_at_unix_ms
    if (
        not epoch_id
        or len(epoch_id) > 256
        or not process_id
        or len(process_id) > 256
        or not server_id
        or len(server_id) > 256
        or not root
        or len(root) > 4_096
        or not isinstance(recorded_at, int)
        or isinstance(recorded_at, bool)
        or recorded_at <= 0
        or classification not in PROJECTION_REBUILD_ALLOWED_CLASSIFICATIONS
        or not _classification_matches_projection(classification, projection_identity)
        or not _is_digest(physical_sha256)
        or not _is_digest(logical_sha256)
        or integrity != {
            "backup_api_copy": True,
            "immutable": True,
            "query_only": True,
            "integrity_check": ["ok"],
            "foreign_key_check_rows": 0,
        }
        or reconciled is not True
    ):
        raise ValueError("projection rebuild receipt requires a complete current epoch and immutable ledger census")
    receipt = {
        "schema_version": PROJECTION_REBUILD_SCHEMA_VERSION,
        "kind": PROJECTION_REBUILD_KIND,
        "activation_epoch_id": epoch_id,
        "process_instance_id": process_id,
        "server_instance_id": server_id,
        "workspace": root,
        "ledger_snapshot_sha256": physical_sha256,
        "ledger_logical_sha256": logical_sha256,
        "ledger_integrity": integrity,
        "projection_classification": classification,
        "projection": projection_identity,
        "completed_at": _iso_at(recorded_at),
        "completed_at_unix_ms": recorded_at,
        "reconciled": reconciled,
    }
    return {**receipt, "integrity_sha256": canonical_sha256(receipt)}


def build_projection_rebuild_receipt_from_census(
    census: Mapping[str, Any],
    **identity: Any,
) -> dict[str, Any]:
    """Build a receipt using the snapshot and projection from one census result."""
    snapshot = census.get("snapshot") if isinstance(census.get("snapshot"), Mapping) else {}
    projection = census.get("projection") if isinstance(census.get("projection"), Mapping) else {}
    return build_projection_rebuild_receipt(
        ledger_snapshot=snapshot,
        projection_classification=projection.get("classification"),
        projection=projection,
        **identity,
    )


def validate_projection_rebuild_receipt(
    receipt: Any,
    *,
    activation_epoch_id: Any = _UNSET,
    process_instance_id: Any = _UNSET,
    server_instance_id: Any = _UNSET,
    workspace: Any = _UNSET,
    ledger_snapshot: Mapping[str, Any] | None = None,
    process_started_at_unix_ms: int | None = None,
    epoch_started_at_unix_ms: int | None = None,
    now_unix_ms: int | None = None,
    max_age_ms: int = PROJECTION_REBUILD_MAX_AGE_MS,
) -> dict[str, Any]:
    """Validate a receipt and optional current runtime/snapshot expectations.

    Validation is deliberately non-throwing so health and activation endpoints
    can remain observable while returning ``UPDATE_INCOMPLETE`` evidence.
    """
    reasons: list[str] = []
    if not isinstance(receipt, Mapping):
        return {"valid": False, "code": "UPDATE_INCOMPLETE", "reasons": ["RECEIPT_MISSING"]}
    value = dict(receipt)
    if frozenset(value) != _RECEIPT_FIELDS:
        reasons.append("RECEIPT_FIELDS_INVALID")
    if value.get("schema_version") != PROJECTION_REBUILD_SCHEMA_VERSION or value.get("kind") != PROJECTION_REBUILD_KIND:
        reasons.append("RECEIPT_SCHEMA_INVALID")
    for field in ("activation_epoch_id", "process_instance_id", "server_instance_id"):
        item = value.get(field)
        if not isinstance(item, str) or not item.strip() or len(item) > 256:
            reasons.append(f"{field.upper()}_INVALID")
    workspace_value = value.get("workspace")
    if not isinstance(workspace_value, str) or not workspace_value.strip() or len(workspace_value) > 4_096:
        reasons.append("WORKSPACE_INVALID")
    if not _is_digest(value.get("ledger_snapshot_sha256")) or not _is_digest(value.get("ledger_logical_sha256")):
        reasons.append("LEDGER_HASH_INVALID")
    ledger_integrity = value.get("ledger_integrity")
    expected_integrity = {
        "backup_api_copy": True,
        "immutable": True,
        "query_only": True,
        "integrity_check": ["ok"],
        "foreign_key_check_rows": 0,
    }
    if not isinstance(ledger_integrity, Mapping) or frozenset(ledger_integrity) != _LEDGER_INTEGRITY_FIELDS or dict(ledger_integrity) != expected_integrity:
        reasons.append("LEDGER_INTEGRITY_INVALID")
    classification = str(value.get("projection_classification") or "")
    projection = value.get("projection")
    if (
        classification not in PROJECTION_REBUILD_ALLOWED_CLASSIFICATIONS
        or not isinstance(projection, Mapping)
        or frozenset(projection) != _PROJECTION_FIELDS
        or not _classification_matches_projection(classification, projection if isinstance(projection, Mapping) else {})
    ):
        reasons.append("PROJECTION_CLASSIFICATION_INVALID")
    if value.get("reconciled") is not True:
        reasons.append("RECONCILIATION_FLAG_INVALID")
    completed_ms = value.get("completed_at_unix_ms")
    if not isinstance(completed_ms, int) or isinstance(completed_ms, bool) or completed_ms <= 0:
        reasons.append("RECEIPT_TIMESTAMP_INVALID")
        completed_ms = 0
    parsed_ms = _parse_timestamp(value.get("completed_at"))
    if (
        parsed_ms is None
        or not completed_ms
        or abs(parsed_ms - completed_ms) > 1
        or str(value.get("completed_at") or "") != _iso_at(completed_ms)
    ):
        reasons.append("RECEIPT_TIMESTAMP_MISMATCH")
    now_ms = int(time.time() * 1000) if now_unix_ms is None else now_unix_ms
    if not isinstance(now_ms, int) or isinstance(now_ms, bool) or now_ms <= 0:
        reasons.append("VALIDATION_TIMESTAMP_INVALID")
    elif completed_ms:
        if completed_ms > now_ms + PROJECTION_REBUILD_FUTURE_SKEW_MS:
            reasons.append("RECEIPT_FROM_FUTURE")
        if not isinstance(max_age_ms, int) or isinstance(max_age_ms, bool) or max_age_ms <= 0:
            reasons.append("RECEIPT_MAX_AGE_INVALID")
        elif now_ms - completed_ms > max_age_ms:
            reasons.append("RECEIPT_STALE")
    for label, lower_bound in (
        ("PROCESS", process_started_at_unix_ms),
        ("EPOCH", epoch_started_at_unix_ms),
    ):
        if lower_bound is not None:
            if not isinstance(lower_bound, int) or isinstance(lower_bound, bool) or lower_bound <= 0:
                reasons.append(f"{label}_START_TIMESTAMP_INVALID")
            elif completed_ms and completed_ms < lower_bound:
                reasons.append(f"RECEIPT_PRECEDES_{label}")
    expectations = (
        ("ACTIVATION_EPOCH_ID_MISMATCH", activation_epoch_id, value.get("activation_epoch_id")),
        ("PROCESS_INSTANCE_ID_MISMATCH", process_instance_id, value.get("process_instance_id")),
        ("SERVER_INSTANCE_ID_MISMATCH", server_instance_id, value.get("server_instance_id")),
    )
    for reason, expected, observed in expectations:
        if expected is not _UNSET and str(expected or "").strip() != str(observed or "").strip():
            reasons.append(reason)
    if workspace is not _UNSET and not _workspace_matches(workspace, value.get("workspace")):
        reasons.append("WORKSPACE_MISMATCH")
    if ledger_snapshot is not None:
        if str(ledger_snapshot.get("sha256") or "").lower() != str(value.get("ledger_snapshot_sha256") or ""):
            reasons.append("LEDGER_SNAPSHOT_SHA256_MISMATCH")
        if str(ledger_snapshot.get("logical_sha256") or "").lower() != str(value.get("ledger_logical_sha256") or ""):
            reasons.append("LEDGER_LOGICAL_SHA256_MISMATCH")
        if _ledger_integrity(ledger_snapshot) != expected_integrity:
            reasons.append("CURRENT_LEDGER_INTEGRITY_INVALID")
    integrity_sha256 = value.get("integrity_sha256")
    if not _is_digest(integrity_sha256) or integrity_sha256 != canonical_sha256(_without_integrity(value)):
        reasons.append("RECEIPT_INTEGRITY_INVALID")
    unique_reasons = list(dict.fromkeys(reasons))
    return {
        "valid": not unique_reasons,
        "code": "READY" if not unique_reasons else "UPDATE_INCOMPLETE",
        "reasons": unique_reasons,
        "projection_classification": classification or None,
    }


def reconcile_task_orchestration_projection(runtime: Any) -> bool:
    """Repair the compact task projection from current canonical ledger facts."""
    state = runtime.task_state.get()
    if not str(state.get("task_id") or "").strip() and not str(state.get("objective") or "").strip():
        return False
    projection = state.get("orchestration") if isinstance(state.get("orchestration"), dict) else {}
    run_id = str(projection.get("run_id") or "").strip()
    task_id = str(state.get("task_id") or "").strip()
    if not run_id and task_id:
        active = runtime.orchestration_ledger.current_active_run(task_id=task_id)
        run_id = str(active.get("run_id") or "") if active else ""
    if not run_id and not task_id and not runtime.task_state.is_scoped():
        active = runtime.orchestration_ledger.current_active_run()
        run_id = str(active.get("run_id") or "") if active else ""
    if not run_id:
        return False
    run = runtime.orchestration_ledger.get_run(run_id)
    if not isinstance(run, dict):
        return False
    target_state = {
        "accepted": "CHECKPOINTED",
        "blocked": "BLOCKED",
        "aborted": "ABORTED",
        "stale": "ABORTED",
    }.get(str(run.get("status") or "").lower())
    ctx = runtime.orchestration_control.snapshot(run_id)
    if ctx is None:
        return False
    waves = runtime.orchestration_ledger.list_waves(run_id)
    repaired = dict(projection)
    repaired.update(ctx.projection())
    repaired["run_id"] = run_id
    if waves:
        repaired["wave_id"] = str(waves[-1].get("wave_id") or repaired.get("wave_id") or "")
    if target_state:
        repaired["orchestration_state"] = target_state
        repaired["write_lease_id"] = ""
        repaired["write_owner"] = ""

    canonical_state = str(repaired.get("orchestration_state") or "").upper()
    desired_task: dict[str, Any] = {"orchestration": repaired}
    if canonical_state == "ACCEPTING":
        desired_task.update({
            "status": "waiting",
            "current_step": "Awaiting acceptance",
            "next_step": (
                "Present orchestration.completion_report to the operator, then inspect the durable proof and "
                "call task_control action=accept or reject; do not retry completed tool calls."
            ),
            "failure": None,
        })
    elif canonical_state == "CHECKPOINTED":
        desired_task.update({
            "status": "completed",
            "current_step": "Completed - operator report required",
            "next_step": "Present orchestration.completion_report to the operator before starting another material wave.",
            "failure": None,
        })
    elif canonical_state == "REPLAN":
        desired_task.update({
            "status": "waiting",
            "current_step": "Replan required - operator report required",
            "next_step": "Present orchestration.completion_report to the operator, then replan from the durable failure; do not retry an unchanged wave.",
            "failure": state.get("failure"),
        })
    elif canonical_state == "BLOCKED":
        desired_task.update({
            "status": "failed",
            "current_step": "Blocked - operator report required",
            "next_step": "Present orchestration.completion_report to the operator, then resolve the durable blocker before another execution wave.",
            "failure": state.get("failure"),
        })
    elif canonical_state == "ABORTED":
        desired_task.update({
            "status": "stopped",
            "current_step": "Aborted - operator report required",
            "next_step": "Present orchestration.completion_report to the operator before any resume; use current source state and do not reuse stale proof.",
            "failure": state.get("failure"),
        })
    current_projection = state.get("orchestration") if isinstance(state.get("orchestration"), dict) else {}
    projection_changed = any(current_projection.get(key) != repaired.get(key) for key in repaired)
    task_changed = any(
        state.get(key) != desired_task[key]
        for key in ("status", "current_step", "next_step", "failure")
        if key in desired_task
    )
    if not projection_changed and not task_changed:
        return False
    runtime.task_state.update(desired_task, event="orchestration_projection_reconciled")
    return True
