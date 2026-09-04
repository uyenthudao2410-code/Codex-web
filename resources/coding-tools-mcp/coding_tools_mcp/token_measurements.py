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
    """One effective measurement per (turn_id, trace_id): exact wins."""
    features_by_turn: dict[tuple[str, str], dict[str, Any]] = {}
    exact_by_turn: dict[tuple[str, str], dict[str, Any]] = {}
    order: list[tuple[str, str]] = []
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
            if key not in features_by_turn:
                features_by_turn[key] = event
                order.append(key)
            else:
                features_by_turn[key] = event
        elif event_type == "host_turn_span":
            # Completion signal for turns that predate structural features:
            # they count as unknown, never zero.
            if key not in features_by_turn and key not in order:
                order.append(key)
        elif event_type == "controller_usage":
            measured = exact_measurement(event)
            if measured is not None:
                exact_by_turn[key] = measured
                if key not in features_by_turn and key not in order:
                    order.append(key)
    turns = order[-max(1, max_turns):]
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
    return {
        "turns_total": len(measurements),
        "turns_exact": exact,
        "turns_estimated": estimated,
        "turns_unknown": unknown,
        "session_total": total,
        "latest_turn": latest,
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
