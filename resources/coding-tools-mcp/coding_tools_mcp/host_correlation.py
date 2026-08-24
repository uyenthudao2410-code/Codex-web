from __future__ import annotations

"""Content-free exact host-turn correlation primitives.

The Electron host stages one short-lived opaque turn/trace pair.  The MCP
runtime claims that record before creating a new run, then publishes the same
pair with the resulting run/wave.  This leaf module deliberately has no
ledger, Runtime, task-control, or problem-lineage dependency so each consumer
uses the identical validation and one-shot filesystem semantics.
"""

import json
import os
import secrets
import time
from pathlib import Path
from typing import Any


HOST_CORRELATION_SCHEMA_VERSION = 1
HOST_CORRELATION_PENDING_TTL_MS = 120_000
HOST_CORRELATION_PENDING_RELATIVE = Path(".coding-tools") / "evaluation" / "chatweb-host-turn-pending.json"
HOST_CORRELATION_BINDING_RELATIVE = Path(".coding-tools") / "evaluation" / "chatweb-host-turn-binding.json"


def validate_pending_host_turn(value: Any, *, now_ms: float | None = None) -> dict[str, Any] | None:
    """Return a current content-free pending identity, or ``None``.

    The caller supplies ``now_ms`` in tests so validation is deterministic.
    This function intentionally rejects a matching PID-style opaque string
    with control characters, an invalid schema, future staging, or an expired
    record; identity equality alone is not enough to establish a live turn.
    """
    if not isinstance(value, dict):
        return None
    allowed = {"schema_version", "turn_id", "trace_id", "staged_at_unix_ms"}
    if set(value) - allowed or value.get("schema_version") != HOST_CORRELATION_SCHEMA_VERSION:
        return None
    turn_id = str(value.get("turn_id") or "").strip()
    trace_id = str(value.get("trace_id") or "").strip()
    staged_at = value.get("staged_at_unix_ms")
    if not turn_id or len(turn_id) > 128 or not trace_id or len(trace_id) > 128:
        return None
    if any(ord(char) < 32 for char in turn_id + trace_id):
        return None
    if isinstance(staged_at, bool) or not isinstance(staged_at, (int, float)):
        return None
    current_ms = time.time() * 1000 if now_ms is None else float(now_ms)
    if float(staged_at) > current_ms + 5_000 or current_ms - float(staged_at) > HOST_CORRELATION_PENDING_TTL_MS:
        return None
    return {"turn_id": turn_id, "trace_id": trace_id, "staged_at_unix_ms": float(staged_at)}


def peek_pending_host_turn(workspace: Path, *, now_ms: float | None = None) -> dict[str, Any] | None:
    """Read a pending identity without consuming it."""
    path = workspace / HOST_CORRELATION_PENDING_RELATIVE
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return validate_pending_host_turn(value, now_ms=now_ms)


def claim_pending_host_turn(
    workspace: Path,
    *,
    process_instance_id: str,
    now_ms: float | None = None,
) -> dict[str, Any] | None:
    """Atomically claim a valid one-shot pending host identity.

    Invalid or expired claims are removed rather than restored.  A valid claim
    carries a private ``_claim_path`` for the runtime to restore on pre-run
    failure or consume after the exact run/wave binding is published.
    """
    pending = workspace / HOST_CORRELATION_PENDING_RELATIVE
    claim = pending.with_name(f".{pending.name}.{process_instance_id}.{secrets.token_urlsafe(6)}.claim")
    try:
        os.replace(pending, claim)
    except FileNotFoundError:
        return None
    except OSError:
        return None
    try:
        value = json.loads(claim.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        value = None
    record = validate_pending_host_turn(value, now_ms=now_ms)
    if record is None:
        try:
            claim.unlink(missing_ok=True)
        except OSError:
            pass
        return None
    return {**record, "_claim_path": claim}


def discard_pending_host_turn(workspace: Path, *, process_instance_id: str, now_ms: float | None = None) -> None:
    claimed = claim_pending_host_turn(workspace, process_instance_id=process_instance_id, now_ms=now_ms)
    claim_path = claimed.get("_claim_path") if claimed else None
    if isinstance(claim_path, Path):
        try:
            claim_path.unlink(missing_ok=True)
        except OSError:
            pass


def restore_pending_host_turn(workspace: Path, claimed: dict[str, Any]) -> None:
    claim = claimed.get("_claim_path")
    if not isinstance(claim, Path) or not claim.exists():
        return
    pending = workspace / HOST_CORRELATION_PENDING_RELATIVE
    try:
        if pending.exists():
            claim.unlink(missing_ok=True)
        else:
            os.replace(claim, pending)
    except OSError:
        try:
            claim.unlink(missing_ok=True)
        except OSError:
            pass


def publish_host_turn_binding(
    workspace: Path,
    claimed: dict[str, Any],
    *,
    process_instance_id: str,
    run_id: str,
    wave_id: str,
    now_ms: float | None = None,
) -> bool:
    """Publish the exact host-to-run/wave binding and consume its claim."""
    target = workspace / HOST_CORRELATION_BINDING_RELATIVE
    temporary = target.with_name(f".{target.name}.{process_instance_id}.{secrets.token_urlsafe(6)}.tmp")
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": HOST_CORRELATION_SCHEMA_VERSION,
            "turn_id": claimed["turn_id"],
            "trace_id": claimed["trace_id"],
            "run_id": run_id,
            "wave_id": wave_id,
            "bound_at_unix_ms": int(time.time() * 1000 if now_ms is None else now_ms),
        }
        temporary.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        os.replace(temporary, target)
        return True
    except OSError:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        return False
    finally:
        claim = claimed.get("_claim_path")
        if isinstance(claim, Path):
            try:
                claim.unlink(missing_ok=True)
            except OSError:
                pass
