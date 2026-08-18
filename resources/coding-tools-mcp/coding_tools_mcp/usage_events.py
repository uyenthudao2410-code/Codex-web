from __future__ import annotations

import hashlib
import math
from typing import Any

from .usage_pricing import derive_cost


USAGE_EVENT_SCHEMA_VERSION = 1


def _nonnegative_number(value: Any) -> int | float | None:
    if value is None or isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if not math.isfinite(float(value)) or value < 0:
        return None
    return value


def _nonnegative_int(value: Any) -> int:
    measured = _nonnegative_number(value)
    return max(0, int(measured or 0))


def classify_provider_error(error_name: str = "", *, status: str = "") -> str | None:
    if str(status).strip().lower() != "failed":
        return None
    normalized = str(error_name or "").strip().lower()
    if any(term in normalized for term in ("rate", "quota", "capacity", "overload", "429")):
        return "capacity_or_rate_limit"
    if any(term in normalized for term in ("auth", "credential", "permission", "forbidden", "unauthorized")):
        return "auth_or_permission"
    if any(term in normalized for term in ("timeout", "deadline")):
        return "deadline_or_timeout"
    if any(term in normalized for term in ("cancel", "interrupt", "abort")):
        return "cancelled_or_interrupted"
    if any(term in normalized for term in ("network", "socket", "connection", "transport", "disconnect")):
        return "transport"
    return "provider_error"


def build_usage_event(
    *,
    run_id: str,
    wave_id: str,
    delegation_id: str,
    provider_id: str,
    model_id: str,
    status: str,
    source: str,
    input_tokens: Any = 0,
    cached_input_tokens: Any = 0,
    output_tokens: Any = 0,
    reasoning_output_tokens: Any = 0,
    cache_read_tokens: Any = 0,
    cache_write_tokens: Any = 0,
    provider_cost: Any = None,
    queue_ms: Any = None,
    provider_ms: Any = None,
    total_ms: Any = None,
    error_name: str = "",
) -> dict[str, Any]:
    input_count = _nonnegative_int(input_tokens)
    cached_count = min(input_count, _nonnegative_int(cached_input_tokens))
    cost = _nonnegative_number(provider_cost)
    queue = _nonnegative_number(queue_ms)
    provider = _nonnegative_number(provider_ms)
    total = _nonnegative_number(total_ms)
    model = str(model_id or "").strip()
    provider_name = str(provider_id or "").strip()
    resolved_model = model if "/" in model else f"{provider_name}/{model}"
    usage_id = hashlib.sha256(
        f"{run_id}\0{wave_id}\0{delegation_id}\0{source}".encode("utf-8")
    ).hexdigest()
    usage = {
        "input_tokens": input_count,
        "cached_input_tokens": cached_count,
        "uncached_input_tokens": max(0, input_count - cached_count),
        "output_tokens": _nonnegative_int(output_tokens),
        "reasoning_output_tokens": _nonnegative_int(reasoning_output_tokens),
        "cache_read_tokens": _nonnegative_int(cache_read_tokens),
        "cache_write_tokens": _nonnegative_int(cache_write_tokens),
    }
    derived_cost_usd: float | None = None
    derived_components: dict[str, float] | None = None
    cost_kind = "provider_reported" if cost is not None else "unobserved"
    if cost is None:
        derived = derive_cost(usage, resolved_model)
        if derived is not None:
            derived_cost_usd, derived_components = derived
            cost_kind = "pricing_derived"
    return {
        "schema_version": USAGE_EVENT_SCHEMA_VERSION,
        "usage_id": usage_id,
        "run_id": str(run_id),
        "wave_id": str(wave_id),
        "delegation_id": str(delegation_id),
        "provider_id": provider_name,
        "model_id": model,
        "model": resolved_model,
        "status": str(status or "").strip().lower(),
        "provenance": {
            "source": str(source or "")[:160],
            "usage": "provider_reported",
            "cost": cost_kind,
            "timing": "provider_message_timestamps" if provider is not None else "unobserved",
        },
        "measurement": {
            "usage": "measured",
            "cost": "measured" if cost is not None else ("derived" if derived_cost_usd is not None else "unobserved"),
            "queue_timing": "measured" if queue is not None else "unobserved",
            "provider_timing": "measured" if provider is not None else "unobserved",
            "total_timing": "measured" if total is not None else "unobserved",
        },
        "usage": usage,
        "cost": {
            "provider_cost": cost,
            "derived_cost_usd": derived_cost_usd,
            "derived_components": derived_components,
            "kind": cost_kind,
        },
        "timing": {
            "queue_ms": queue,
            "provider_ms": provider,
            "total_ms": total,
        },
        "error": {
            "class": classify_provider_error(error_name, status=status),
        },
    }


def usage_event_from_provider_telemetry(
    *,
    run_id: str,
    wave_id: str,
    delegation_id: str,
    telemetry: dict[str, Any],
    source: str = "opencode:message.updated",
) -> dict[str, Any]:
    return build_usage_event(
        run_id=run_id,
        wave_id=wave_id,
        delegation_id=delegation_id,
        provider_id=str(telemetry.get("provider_id") or ""),
        model_id=str(telemetry.get("model_id") or ""),
        status=str(telemetry.get("status") or ""),
        source=source,
        input_tokens=telemetry.get("input_tokens"),
        cached_input_tokens=telemetry.get("cache_read_tokens"),
        output_tokens=telemetry.get("output_tokens"),
        reasoning_output_tokens=telemetry.get("reasoning_output_tokens"),
        cache_read_tokens=telemetry.get("cache_read_tokens"),
        cache_write_tokens=telemetry.get("cache_write_tokens"),
        provider_cost=telemetry.get("provider_cost"),
        provider_ms=telemetry.get("duration_ms"),
        error_name=str(telemetry.get("error_name") or ""),
    )


def usage_event_from_provider_delegation(
    *,
    run_id: str,
    wave_id: str,
    delegation: dict[str, Any],
    source: str = "opencode:provider_dispatch",
    total_ms: Any = None,
) -> dict[str, Any] | None:
    metadata = delegation.get("metadata") if isinstance(delegation.get("metadata"), dict) else {}
    economics = metadata.get("economics") if isinstance(metadata.get("economics"), dict) else {}
    if not economics or economics.get("measured") is not True:
        return None
    model = str(delegation.get("model") or "").strip()
    provider_id = str(metadata.get("provider_id") or "").strip()
    model_id = str(metadata.get("model_id") or "").strip()
    if not provider_id and "/" in model:
        provider_id = model.split("/", 1)[0]
    if not model_id:
        model_id = model.split("/", 1)[1] if "/" in model else model
    timing = metadata.get("timing") if isinstance(metadata.get("timing"), dict) else {}
    return build_usage_event(
        run_id=run_id,
        wave_id=wave_id,
        delegation_id=str(delegation.get("delegation_id") or ""),
        provider_id=provider_id,
        model_id=model_id,
        status=str(delegation.get("status") or ""),
        source=source,
        input_tokens=economics.get("input_tokens"),
        cached_input_tokens=economics.get("cached_input_tokens"),
        output_tokens=economics.get("output_tokens"),
        reasoning_output_tokens=economics.get("reasoning_output_tokens"),
        cache_read_tokens=economics.get("cache_read_tokens"),
        cache_write_tokens=economics.get("cache_write_tokens"),
        provider_cost=economics.get("provider_cost"),
        queue_ms=timing.get("queue_ms"),
        provider_ms=metadata.get("provider_message_duration_ms"),
        total_ms=total_ms if total_ms is not None else timing.get("total_ms"),
        error_name=str(metadata.get("error_class") or metadata.get("error_name") or ""),
    )
