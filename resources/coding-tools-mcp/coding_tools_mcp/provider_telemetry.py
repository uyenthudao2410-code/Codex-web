from __future__ import annotations

"""Content-free validation for allowlisted provider telemetry."""

import math
from typing import Any


HUB_PROVIDER_TELEMETRY_STATUSES = frozenset({"active", "completed", "failed"})


def normalize_provider_telemetry(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("telemetry must be an object")
    allowed = {
        "schema_version", "event_type", "session_id", "message_id", "provider_id", "model_id",
        "status", "started_at_ms", "completed_at_ms", "duration_ms", "finish", "error_name",
        "provider_cost", "input_tokens", "output_tokens", "reasoning_output_tokens",
        "cache_read_tokens", "cache_write_tokens", "provider_dispatch_id", "provider_delegation_id",
    }
    unexpected = sorted(set(value) - allowed)
    if unexpected:
        raise ValueError("unsupported provider telemetry fields: " + ", ".join(unexpected[:5]))
    if value.get("schema_version") != 1 or value.get("event_type") != "message.updated":
        raise ValueError("unsupported provider telemetry schema")

    def text(name: str, limit: int, *, required: bool = False) -> str:
        result = str(value.get(name) or "").strip()
        if required and not result:
            raise ValueError(f"{name} is required")
        if len(result) > limit or any(ord(ch) < 32 for ch in result):
            raise ValueError(f"invalid {name}")
        return result

    def number(name: str, *, integer: bool = False, required: bool = False) -> int | float | None:
        raw = value.get(name)
        if raw is None:
            if required:
                raise ValueError(f"{name} is required")
            return None
        if isinstance(raw, bool) or not isinstance(raw, (int, float)) or not math.isfinite(float(raw)) or raw < 0:
            raise ValueError(f"invalid {name}")
        if integer and int(raw) != raw:
            raise ValueError(f"invalid {name}")
        return int(raw) if integer else raw

    status = text("status", 32, required=True).lower()
    if status not in HUB_PROVIDER_TELEMETRY_STATUSES:
        raise ValueError("invalid provider telemetry status")
    result: dict[str, Any] = {
        "schema_version": 1,
        "event_type": "message.updated",
        "session_id": text("session_id", 256, required=True),
        "message_id": text("message_id", 256, required=True),
        "provider_id": text("provider_id", 160, required=True),
        "model_id": text("model_id", 200, required=True),
        "status": status,
        "started_at_ms": number("started_at_ms", required=True),
        "provider_cost": number("provider_cost", required=True),
        "input_tokens": number("input_tokens", integer=True, required=True),
        "output_tokens": number("output_tokens", integer=True, required=True),
        "reasoning_output_tokens": number("reasoning_output_tokens", integer=True, required=True),
        "cache_read_tokens": number("cache_read_tokens", integer=True, required=True),
        "cache_write_tokens": number("cache_write_tokens", integer=True, required=True),
    }
    for name in ("completed_at_ms", "duration_ms"):
        measured = number(name)
        if measured is not None:
            result[name] = measured
    for name, limit in (("provider_dispatch_id", 256), ("provider_delegation_id", 256), ("finish", 100), ("error_name", 120)):
        measured = text(name, limit)
        if measured:
            result[name] = measured
    return result
