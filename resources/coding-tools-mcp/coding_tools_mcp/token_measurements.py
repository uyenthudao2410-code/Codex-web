from __future__ import annotations

"""Per-turn ChatWeb token measurements from the Electron host journal.

The orchestration ledger only records EOCL-bound exact usage; casual
ChatWeb turns never reach it. This module projects per-turn measurements
from the content-free host observation journal
(``.coding-tools/evaluation/chatweb-host-observations.jsonl`` + rotated
``.1``) that the Electron side appends:

- exact controller receipts (``controller_usage`` with all four counters),
- structural features (``turn_features``: ordinal/duration/tool cards and
  visible character/code-block counts, numbers only).

Precedence per turn is exact > structural estimate > unknown, mirroring
``electron/services/tokenMeasurement.js`` (the cross-language contract).
Structural totals use the documented chars ladder (6/4/2, P10/P50/P90),
confidence ``none`` until exact samples calibrate it. Missing stays null,
never zero. No prompt/response/URL/conversation content is read: only the
numeric observation fields above are consumed.
"""

from pathlib import Path
from typing import Any
import json
import math


MEASUREMENT = "chat_turn_measurements_v1"
MISSING_POLICY = "unknown_not_zero"
STRUCTURAL_METHOD = "structural-chars-v1"
STRUCTURAL_CHARS_PER_TOKEN_P10 = 6.0
STRUCTURAL_CHARS_PER_TOKEN_P50 = 4.0
STRUCTURAL_CHARS_PER_TOKEN_P90 = 2.0
MAX_TURNS = 200
MAX_JOURNAL_LINES = 20000
RECENT_TURNS = 20
LIVE_TAIL_LINES = 400
LIVE_TAIL_BYTES = 256 * 1024

JOURNAL_RELATIVE = Path(".coding-tools") / "evaluation" / "chatweb-host-observations.jsonl"


def _nonnegative_int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if not math.isfinite(float(value)) or float(value) < 0:
        return None
    return int(value)


def _journal_files(workspace: Path) -> list[Path]:
    root = Path(workspace)
    main = root / JOURNAL_RELATIVE
    rotated = Path(str(main) + ".1")
    # Rotation renames the current file to .1 before a fresh file starts,
    # so chronological order is rotated first, then main.
    return [rotated, main]


def read_journal_events(workspace: Any, *, limit: int = MAX_JOURNAL_LINES) -> tuple[list[dict[str, Any]], bool]:
    """Read bounded raw journal lines. Returns (events, journal_available)."""
    try:
        root = Path(workspace)
    except (TypeError, ValueError):
        return [], False
    events: list[dict[str, Any]] = []
    available = False

    for path in _journal_files(root):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        available = True
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                value = json.loads(line)
            except ValueError:
                continue
            if isinstance(value, dict):
                events.append(value)
            if len(events) >= limit:
                break
        if len(events) >= limit:
            break
    return events[-limit:], available


def exact_measurement(receipt: dict[str, Any]) -> dict[str, Any] | None:
    if not isinstance(receipt, dict):
        return None
    turn_id = str(receipt.get("turn_id") or "").strip()
    trace_id = str(receipt.get("trace_id") or "").strip()
    if not turn_id or not trace_id:
        return None
    counters = {key: _nonnegative_int(receipt.get(key)) for key in (
        "input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens")}
    if any(value is None for value in counters.values()):
        return None
    input_tokens = int(counters["input_tokens"])
    cached_tokens = int(counters["cached_input_tokens"])
    output_tokens = int(counters["output_tokens"])
    reasoning_tokens = int(counters["reasoning_output_tokens"])
    if cached_tokens > input_tokens:
        return None
    if reasoning_tokens > output_tokens:
        return None
    total = input_tokens + output_tokens
    return {
        "kind": "exact",
        "turn_id": turn_id,
        "trace_id": trace_id,
        "wall_time_ms": _nonnegative_int(receipt.get("wall_time_ms")),
        "total": {"point": total, "lower": total, "upper": total},
        "input": {"point": input_tokens, "lower": input_tokens, "upper": input_tokens},
        "output": {"point": output_tokens, "lower": output_tokens, "upper": output_tokens},
        "confidence": "exact",
        "method_version": "exact-receipt-v1",
        "calibration": None,
    }


def structural_estimate(features: dict[str, Any]) -> dict[str, Any] | None:
    """Bounded total-only estimate from visible character counts.

    Input/output split stays null: hidden history and reasoning make the
    split unknowable without exact samples. The 6/4/2 chars-per-token
    ladder mirrors the analytics context prior; confidence is always none
    until exact samples calibrate this cohort.
    """
    if not isinstance(features, dict):
        return None
    turn_id = str(features.get("turn_id") or "").strip()
    trace_id = str(features.get("trace_id") or "").strip()
    if not turn_id or not trace_id:
        return None
    user_chars = _nonnegative_int(features.get("user_chars"))
    asst_chars = _nonnegative_int(features.get("asst_chars"))
    if user_chars is None or asst_chars is None:
        return None
    total_chars = user_chars + asst_chars
    if total_chars <= 0:
        return None
    return {
        "kind": "structural_estimate",
        "turn_id": turn_id,
        "trace_id": trace_id,
        "wall_time_ms": _nonnegative_int(features.get("wall_time_ms")),
        "total": {
            "point": round(total_chars / STRUCTURAL_CHARS_PER_TOKEN_P50),
            "lower": round(total_chars / STRUCTURAL_CHARS_PER_TOKEN_P10),
            "upper": round(total_chars / STRUCTURAL_CHARS_PER_TOKEN_P90),
        },
        "input": None,
        "output": None,
        "confidence": "none",
        "method_version": STRUCTURAL_METHOD,
        "calibration": None,
    }


def effective_turn_measurements(events: list[Any], *, max_turns: int = MAX_TURNS) -> list[dict[str, Any]]:
    """One effective measurement per (turn_id, trace_id): exact wins.

    Journal append order is the freshness authority for structural snapshots.
    A later ``turn_features`` event replaces an earlier interim snapshot for
    the same turn.  If that latest snapshot is malformed, its measurement is
    unknown rather than a stale interim value or a fabricated zero.
    """
    features_by_turn: dict[tuple[str, str], dict[str, Any]] = {}
    exact_by_turn: dict[tuple[str, str], dict[str, Any]] = {}
    # A regular dict preserves insertion order. Re-inserting a key lets a
    # later journal event move that turn to the freshness position without an
    # O(n) remove from a long history for every streaming update.
    order: dict[tuple[str, str], None] = {}

    def mark_fresh(key: tuple[str, str]) -> None:
        order.pop(key, None)
        order[key] = None

    for event in events:
        if not isinstance(event, dict):
            continue
        event_type = str(event.get("event_type") or "")
        turn_id = str(event.get("turn_id") or "").strip()
        trace_id = str(event.get("trace_id") or "").strip()
        if not turn_id or not trace_id:
            continue
        key = (turn_id, trace_id)
        if event_type == "turn_features":
            # ``host_turn_span`` is normally appended before the first
            # structural snapshot.  Keep exactly one ordered turn slot while
            # replacing the raw snapshot on every later streaming/final emit.
            # Keeping a malformed latest snapshot is deliberate: the
            # structural gate below then fails closed to unknown instead of
            # retaining a stale interim estimate.
            mark_fresh(key)
            features_by_turn[key] = event
        elif event_type == "host_turn_span":
            # Completion signal for turns that predate structural features:
            # they count as unknown, never zero.
            mark_fresh(key)
        elif event_type == "controller_usage":
            measured = exact_measurement(event)
            if measured is not None:
                exact_by_turn[key] = measured
                mark_fresh(key)
    turns = list(order)[-max(1, max_turns):]
    measurements: list[dict[str, Any]] = []
    for key in turns:
        if key in exact_by_turn:
            measurements.append(exact_by_turn[key])
            continue
        estimated = structural_estimate(features_by_turn[key]) if key in features_by_turn else None
        if estimated is not None:
            measurements.append(estimated)
            continue
        measurements.append({
            "kind": "unknown",
            "turn_id": key[0],
            "trace_id": key[1],
            "wall_time_ms": None,
            "total": None,
            "input": None,
            "output": None,
            "confidence": "none",
            "method_version": None,
            "calibration": None,
            "reason": "no_exact_no_structural_features",
        })
    return measurements


def summarize_measurements(measurements: list[dict[str, Any]]) -> dict[str, Any]:
    exact = sum(1 for item in measurements if item.get("kind") == "exact")
    estimated = sum(1 for item in measurements if item.get("kind") == "structural_estimate")
    unknown = sum(1 for item in measurements if item.get("kind") == "unknown")
    measured = [item for item in measurements if isinstance(item.get("total"), dict)]
    if measured:
        total = {
            "point": sum(int(item["total"]["point"]) for item in measured),
            "lower": sum(int(item["total"]["lower"]) for item in measured),
            "upper": sum(int(item["total"]["upper"]) for item in measured),
        }
    else:
        total = {"point": None, "lower": None, "upper": None}
    latest = None
    for item in reversed(measurements):
        total_block = item.get("total") if isinstance(item.get("total"), dict) else None
        latest = {
            "kind": str(item.get("kind") or "unknown"),
            "point": int(total_block["point"]) if total_block else None,
            "lower": int(total_block["lower"]) if total_block else None,
            "upper": int(total_block["upper"]) if total_block else None,
        }
        break
    recent_turns = []
    for item in reversed(measurements[-RECENT_TURNS:]):
        total_block = item.get("total") if isinstance(item.get("total"), dict) else None
        recent_turns.append({
            "wall_time_ms": item.get("wall_time_ms"),
            "kind": str(item.get("kind") or "unknown"),
            "point": int(total_block["point"]) if total_block else None,
            "lower": int(total_block["lower"]) if total_block else None,
            "upper": int(total_block["upper"]) if total_block else None,
        })
    return {
        "turns_total": len(measurements),
        "turns_exact": exact,
        "turns_estimated": estimated,
        "turns_unknown": unknown,
        "session_total": total,
        "latest_turn": latest,
        "recent_turns": recent_turns,
    }


def summarize_workspace(workspace: Any, *, max_turns: int = MAX_TURNS) -> dict[str, Any]:
    """Session-level per-turn token summary for the dashboard.

    Never raises: an unreadable journal yields journal_available False with
    null totals (unknown, never zero).
    """
    base = {
        "schema_version": 1,
        "measurement": MEASUREMENT,
        "missing_measurement_policy": MISSING_POLICY,
        "method": STRUCTURAL_METHOD,
        "content_free": True,
        "journal_available": False,
    }
    try:
        events, available = read_journal_events(workspace)
    except (OSError, ValueError):
        available = False
        events = []
    base["journal_available"] = bool(available)
    if not available:
        return {
            **base,
            **summarize_measurements([]),
            "latest_turn": None,
            "missing_reason": "chat_journal_unavailable",
        }
    measurements = effective_turn_measurements(events, max_turns=max_turns)
    summary = summarize_measurements(measurements)
    kinds = {item.get("kind") for item in measurements}
    if not kinds:
        blend = "unknown"
    elif kinds == {"exact"}:
        blend = "exact"
    elif kinds == {"structural_estimate"}:
        blend = "estimated"
    elif "unknown" in kinds and len(kinds) == 1:
        blend = "unknown"
    elif "exact" in kinds or "structural_estimate" in kinds:
        blend = "mixed"
    else:
        blend = "unknown"
    return {
        **base,
        **summary,
        "blend": blend,
        "missing_reason": None if measurements and summary["turns_unknown"] == 0 else (
            "no_measured_turns" if not measurements else "some_turns_unmeasured"),
    }


def latest_turn_measurement(workspace: Any, *, tail_lines: int = LIVE_TAIL_LINES) -> dict[str, Any]:
    """Cheapest live read for the 4-6s pulse path: journal tail only.

    The newest turn always appends to the main journal file, so rotation
    can be ignored here. Input/read errors return unavailable; unknown stays
    null, never zero.
    """
    base = {
        "schema_version": 1,
        "measurement": MEASUREMENT,
        "missing_measurement_policy": MISSING_POLICY,
        "content_free": True,
        "journal_available": False,
        "latest_turn": None,
    }
    try:
        root = Path(workspace)
        path = root / JOURNAL_RELATIVE
        rows = _read_complete_journal_tail(path, tail_lines=tail_lines)
    except (OSError, ValueError, TypeError, OverflowError):
        return {**base, "missing_reason": "chat_journal_unavailable"}
    events: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        row = row.strip()
        if not row:
            continue
        try:
            value = json.loads(row.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            if index == len(rows) - 1:
                return {**base, "journal_available": True, "missing_reason": "latest_tail_record_invalid"}
            continue
        if not isinstance(value, dict):
            if index == len(rows) - 1:
                return {**base, "journal_available": True, "missing_reason": "latest_tail_record_invalid"}
            continue
        events.append(value)
    base["journal_available"] = True
    measurements = effective_turn_measurements(events, max_turns=MAX_TURNS)
    if not measurements:
        return {**base, "missing_reason": "no_turn_in_tail"}
    latest = summarize_measurements(measurements)["latest_turn"]
    if latest is None or latest.get("point") is None:
        return {**base, "latest_turn": None, "missing_reason": "latest_turn_unmeasured"}
    return {**base, "latest_turn": latest, "missing_reason": None}


def _read_complete_journal_tail(path: Path, *, tail_lines: int, tail_bytes: int = LIVE_TAIL_BYTES) -> list[bytes]:
    """Return only complete JSONL rows from a bounded file tail.

    A journal can be appended while the live pulse reads it.  The first row in
    a byte tail may have started before the window, and the final row may still
    be mid-write, so both fragments are discarded.  This intentionally favors
    ``unknown`` over a speculative latest measurement.
    """
    line_limit = max(1, int(tail_lines))
    byte_limit = max(1, int(tail_bytes))
    with open(path, "rb") as handle:
        handle.seek(0, 2)
        size = handle.tell()
        start = max(0, size - byte_limit)
        handle.seek(start)
        payload = handle.read(min(byte_limit, size))

    if not payload:
        return []
    if start > 0:
        _, separator, payload = payload.partition(b"\n")
        if not separator:
            return []
    if not payload.endswith(b"\n"):
        payload, separator, _ = payload.rpartition(b"\n")
        if not separator:
            return []
        payload += separator
    rows = payload.split(b"\n")[:-1]
    while rows and not rows[-1].strip():
        rows.pop()
    return rows[-line_limit:]
