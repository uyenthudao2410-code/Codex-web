from __future__ import annotations

import hashlib
import math
from typing import Any

from .usage_pricing import derive_cost


USAGE_EVENT_SCHEMA_VERSION = 2
ACCOUNTING_PROFILES = frozenset({"openai_compatible", "gemini", "anthropic"})


def _nonnegative_number(value: Any) -> int | float | None:
    if value is None or isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if not math.isfinite(float(value)) or value < 0:
        return None
    return value


def _nonnegative_int(value: Any) -> int:
    measured = _nonnegative_number(value)
    return max(0, int(measured or 0))


def accounting_profile_for(provider_id: str = "", model_id: str = "") -> str:
    identity = f"{provider_id} {model_id}".strip().lower()
    if "anthropic" in identity or "claude" in identity:
        return "anthropic"
    if "google" in identity or "gemini" in identity:
        return "gemini"
    return "openai_compatible"


def canonicalize_usage(usage: dict[str, Any], accounting_profile: str | None = None) -> dict[str, Any]:
    """Normalize provider-specific token semantics without double counting subsets."""
    source = usage if isinstance(usage, dict) else {}
    profile = str(accounting_profile or source.get("accounting_profile") or "openai_compatible").strip().lower()
    if profile not in ACCOUNTING_PROFILES:
        raise ValueError(f"unsupported token accounting profile: {profile}")

    raw_input = _nonnegative_int(source.get("input_tokens"))
    raw_output = _nonnegative_int(source.get("output_tokens"))
    raw_reasoning = _nonnegative_int(source.get("reasoning_output_tokens"))
    cache_read = _nonnegative_int(source.get("cache_read_tokens"))
    cache_write = _nonnegative_int(source.get("cache_write_tokens"))
    raw_cached = _nonnegative_int(source.get("cached_input_tokens"))

    if profile == "anthropic":
        input_cached = cache_read or raw_cached
        input_uncached = raw_input
        input_cache_creation = cache_write
        input_total = input_uncached + input_cached + input_cache_creation
        output_total = raw_output
        output_reasoning = min(output_total, raw_reasoning)
        output_nonreasoning = max(0, output_total - output_reasoning)
        accounting = {"profile": profile, "input_cached_relation": "separate", "input_cache_creation_relation": "separate", "output_reasoning_relation": "subset"}
    elif profile == "gemini":
        input_total = raw_input
        input_cached = min(input_total, raw_cached or cache_read)
        input_uncached = max(0, input_total - input_cached)
        input_cache_creation = 0
        output_nonreasoning = raw_output
        output_reasoning = raw_reasoning
        output_total = output_nonreasoning + output_reasoning
        accounting = {"profile": profile, "input_cached_relation": "subset", "input_cache_creation_relation": "unobserved", "output_reasoning_relation": "additional"}
    else:
        input_total = raw_input
        input_cached = min(input_total, raw_cached or cache_read)
        input_uncached = max(0, input_total - input_cached)
        input_cache_creation = 0
        output_total = raw_output
        output_reasoning = min(output_total, raw_reasoning)
        output_nonreasoning = max(0, output_total - output_reasoning)
        accounting = {"profile": profile, "input_cached_relation": "subset", "input_cache_creation_relation": "unobserved", "output_reasoning_relation": "subset"}

    return {
        "accounting_profile": profile,
        "input_total_tokens": input_total,
        "input_cached_tokens": input_cached,
        "input_uncached_tokens": input_uncached,
        "input_cache_creation_tokens": input_cache_creation,
        "output_total_tokens": output_total,
        "output_reasoning_tokens": output_reasoning,
        "output_nonreasoning_tokens": output_nonreasoning,
        "total_tokens": input_total + output_total,
        "accounting": accounting,
    }


def controller_usage_delegation_id(run_id: str, wave_id: str, turn_id: str) -> str:
    digest = hashlib.sha256(f"{run_id}\0{wave_id}\0{turn_id}".encode("utf-8")).hexdigest()[:40]
    return f"chatweb-{digest}"


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
    accounting_profile: str | None = None,
    usage_provenance: str = "provider_reported",
    cost_provenance: str | None = None,
    actor: str = "provider",
    identity_key: str = "",
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
    profile = accounting_profile or accounting_profile_for(provider_name, model)
    usage_identity = str(identity_key or delegation_id).strip()
    usage_id = hashlib.sha256(f"usage-v2\0{run_id}\0{wave_id}\0{usage_identity}".encode("utf-8")).hexdigest()
    usage = {
        "input_tokens": input_count,
        "cached_input_tokens": cached_count,
        "uncached_input_tokens": max(0, input_count - cached_count),
        "output_tokens": _nonnegative_int(output_tokens),
        "reasoning_output_tokens": _nonnegative_int(reasoning_output_tokens),
        "cache_read_tokens": _nonnegative_int(cache_read_tokens),
        "cache_write_tokens": _nonnegative_int(cache_write_tokens),
    }
    canonical = canonicalize_usage(usage, profile)
    usage.update({key: value for key, value in canonical.items() if key != "accounting"})
    derived_cost_usd: float | None = None
    derived_components: dict[str, float] | None = None
    usage_source = str(usage_provenance or "provider_reported").strip().lower()
    if usage_source not in {"provider_reported", "client_reported"}:
        raise ValueError("usage_provenance must be provider_reported or client_reported")
    cost_kind = str(cost_provenance or usage_source).strip().lower() if cost is not None else "unobserved"
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
        "actor": "controller" if str(actor).strip().lower() == "controller" else "provider",
        "provider_id": provider_name,
        "model_id": model,
        "model": resolved_model,
        "status": str(status or "").strip().lower(),
        "provenance": {
            "source": str(source or "")[:160],
            "usage": usage_source,
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
        "accounting": canonical["accounting"],
        "cost": {
            "provider_cost": cost,
            "reported_cost": cost,
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


def validate_controller_usage_report(report: Any) -> dict[str, Any]:
    """Validate one bounded exact controller-usage report before any tool side effect."""
    if not isinstance(report, dict):
        raise ValueError("controller usage must be an object")
    schema_version = report.get("schema_version")
    if isinstance(schema_version, bool) or not isinstance(schema_version, int) or schema_version != 1:
        raise ValueError("controller usage must use schema_version=1")
    allowed = {
        "schema_version", "turn_id", "trace_id", "accounting_profile", "provider_id", "model_id", "source",
        "input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens",
        "cache_read_tokens", "cache_write_tokens", "monetary_cost", "provider_cost",
    }
    unexpected = sorted(set(report) - allowed)
    if unexpected:
        raise ValueError("unsupported controller usage fields: " + ", ".join(unexpected[:5]))

    def text(name: str, limit: int, *, required: bool = False) -> str:
        raw = report.get(name)
        if raw is None:
            if required:
                raise ValueError(f"controller usage {name} is required")
            return ""
        if not isinstance(raw, str):
            raise ValueError(f"controller usage {name} must be a string")
        value = raw.strip()
        if required and not value:
            raise ValueError(f"controller usage {name} is required")
        if len(value) > limit or any(ord(ch) < 32 for ch in value):
            raise ValueError(f"invalid controller usage {name}")
        return value

    normalized = dict(report)
    normalized["turn_id"] = text("turn_id", 128, required=True)
    profile = text("accounting_profile", 32).lower() or "openai_compatible"
    if profile not in ACCOUNTING_PROFILES:
        raise ValueError("unsupported controller token accounting profile")
    normalized["accounting_profile"] = profile
    source = text("source", 32).lower() or "client_reported"
    if source not in {"client_reported", "provider_reported"}:
        raise ValueError("controller usage source must be client_reported or provider_reported")
    normalized["source"] = source
    for name, limit in (("trace_id", 128), ("provider_id", 160), ("model_id", 200)):
        if name in report:
            normalized[name] = text(name, limit)

    token_fields = {
        "input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens",
        "cache_read_tokens", "cache_write_tokens",
    }
    required = {"input_tokens", "output_tokens", "reasoning_output_tokens"}
    required.update({"cache_read_tokens", "cache_write_tokens"} if profile == "anthropic" else {"cached_input_tokens"})
    for name in token_fields:
        if name not in report and name not in required:
            continue
        value = report.get(name)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"controller usage {name} must be a non-negative integer")
        normalized[name] = value
    for name in ("monetary_cost", "provider_cost"):
        if name in report and _nonnegative_number(report.get(name)) is None:
            raise ValueError(f"controller usage {name} must be a finite non-negative number")
    if "monetary_cost" in report and "provider_cost" in report:
        if float(report["monetary_cost"]) != float(report["provider_cost"]):
            raise ValueError("controller usage monetary_cost and provider_cost must agree when both are supplied")
    return normalized


def usage_event_from_controller_report(*, run_id: str, wave_id: str, report: dict[str, Any], source: str = "chatweb:mcp_meta") -> dict[str, Any]:
    report = validate_controller_usage_report(report)
    turn_id = report["turn_id"]
    profile = report["accounting_profile"]
    delegation_id = controller_usage_delegation_id(run_id, wave_id, turn_id)
    event = build_usage_event(
        run_id=run_id,
        wave_id=wave_id,
        delegation_id=delegation_id,
        provider_id=str(report.get("provider_id") or "chatweb"),
        model_id=str(report.get("model_id") or "unknown"),
        status="completed",
        source=source,
        input_tokens=report.get("input_tokens"),
        cached_input_tokens=report.get("cached_input_tokens", report.get("cache_read_tokens", 0)),
        output_tokens=report.get("output_tokens"),
        reasoning_output_tokens=report.get("reasoning_output_tokens"),
        cache_read_tokens=report.get("cache_read_tokens", report.get("cached_input_tokens", 0)),
        cache_write_tokens=report.get("cache_write_tokens", 0),
        provider_cost=report.get("monetary_cost", report.get("provider_cost")),
        accounting_profile=profile,
        usage_provenance=str(report.get("source") or "client_reported"),
        cost_provenance=str(report.get("source") or "client_reported"),
        actor="controller",
        identity_key=turn_id,
    )
    event["turn_id"] = turn_id
    trace_id = str(report.get("trace_id") or "").strip()
    if trace_id:
        event["trace_id"] = trace_id[:128]
    return event


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
        accounting_profile=accounting_profile_for(str(telemetry.get("provider_id") or ""), str(telemetry.get("model_id") or "")),
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
        accounting_profile=str(economics.get("accounting_profile") or accounting_profile_for(provider_id, model_id)),
    )
