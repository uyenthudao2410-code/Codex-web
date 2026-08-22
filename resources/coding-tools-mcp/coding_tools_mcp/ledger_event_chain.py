from __future__ import annotations

"""Small transaction-local primitive shared by canonical ledger domains."""

import hashlib
import uuid
from typing import Any, Callable


def append_hash_chained_event(
    connection: Any,
    *,
    run_id: str,
    event_type: str,
    wave_id: str | None,
    delegation_id: str | None,
    state_before: str,
    state_after: str,
    payload: dict[str, Any] | None,
    event_time: str,
    sanitize: Callable[[Any], Any],
    serialize: Callable[[Any], str],
    bounded_text: Callable[[Any, int], str],
) -> dict[str, Any]:
    """Append a standard event without committing the caller's transaction."""

    event_id = uuid.uuid4().hex
    safe_payload = sanitize(payload or {})
    previous = connection.execute(
        "SELECT event_hash FROM events WHERE run_id=? ORDER BY seq DESC LIMIT 1", (run_id,)
    ).fetchone()
    prev_hash = str(previous[0]) if previous else ""
    core = {
        "event_id": event_id,
        "run_id": run_id,
        "wave_id": wave_id or "",
        "delegation_id": delegation_id or "",
        "event_type": event_type,
        "state_before": state_before,
        "state_after": state_after,
        "event_time": event_time,
        "payload": safe_payload,
        "prev_hash": prev_hash,
    }
    event_hash = hashlib.sha256(serialize(core).encode("utf-8")).hexdigest()
    cursor = connection.execute(
        """INSERT INTO events(
            event_id,run_id,wave_id,delegation_id,event_type,state_before,state_after,event_time,payload_json,prev_hash,event_hash
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
        (
            event_id,
            run_id,
            wave_id,
            delegation_id,
            bounded_text(event_type, 100),
            bounded_text(state_before, 64),
            bounded_text(state_after, 64),
            event_time,
            serialize(safe_payload),
            prev_hash,
            event_hash,
        ),
    )
    return {**core, "seq": int(cursor.lastrowid), "event_hash": event_hash}
