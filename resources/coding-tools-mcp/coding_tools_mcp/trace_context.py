from __future__ import annotations

import re
from typing import Any


_TRACEPARENT_RE = re.compile(r"^00-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$")
_TRACESTATE_KEY_RE = re.compile(r"^[a-z][a-z0-9_*/-]{0,255}(?:@[a-z][a-z0-9_*/-]{0,13})?$")
_SECRETISH_KEY_RE = re.compile(r"(authorization|credential|password|passwd|secret|token|api[_-]?key|private[_-]?key)", re.I)
_TRACESTATE_MAX_BYTES = 512
_TRACESTATE_MAX_MEMBERS = 32


def _normalize_tracestate(value: str) -> str:
    raw = str(value or "")
    if not raw:
        return ""
    if len(raw.encode("ascii", errors="ignore")) != len(raw.encode("utf-8")):
        raise ValueError("tracestate must contain printable ASCII only")
    if len(raw.encode("ascii")) > _TRACESTATE_MAX_BYTES:
        raise ValueError("tracestate exceeds the 512-byte bound")
    members = raw.split(",")
    if not 1 <= len(members) <= _TRACESTATE_MAX_MEMBERS:
        raise ValueError("tracestate must contain between 1 and 32 members")
    normalized: list[str] = []
    seen: set[str] = set()
    for member in members:
        item = member.strip()
        if not item or "=" not in item:
            raise ValueError("tracestate members must be key=value pairs")
        key, value_part = item.split("=", 1)
        key = key.strip()
        if not _TRACESTATE_KEY_RE.fullmatch(key) or key in seen:
            raise ValueError("tracestate contains an invalid or duplicate key")
        if _SECRETISH_KEY_RE.search(key):
            raise ValueError("tracestate secret-like keys are not allowed")
        if not value_part or value_part != value_part.strip():
            raise ValueError("tracestate values must be non-empty and cannot have edge whitespace")
        if any(ord(ch) < 0x20 or ord(ch) > 0x7E or ch in {",", "="} for ch in value_part):
            raise ValueError("tracestate contains invalid value characters")
        seen.add(key)
        normalized.append(f"{key}={value_part}")
    return ",".join(normalized)


def parse_trace_context(traceparent: str | None, tracestate: str | None = None) -> dict[str, Any]:
    """Parse the strict W3C v00 request context without creating another authority/store.

    Raw tracestate is transport-only. Callers that persist correlation must use
    ``trace_context_metadata`` so vendor state never enters the canonical ledger.
    """

    parent = str(traceparent or "").strip()
    state = str(tracestate or "").strip()
    if not parent:
        if state:
            raise ValueError("tracestate requires traceparent")
        return {}
    match = _TRACEPARENT_RE.fullmatch(parent)
    if match is None:
        raise ValueError("traceparent must be a W3C version 00 value")
    trace_id, parent_span_id, trace_flags = match.groups()
    if trace_id == "0" * 32 or parent_span_id == "0" * 16:
        raise ValueError("traceparent trace-id and parent-id must be non-zero")
    normalized_state = _normalize_tracestate(state) if state else ""
    return {
        "traceparent": parent,
        "trace_id": trace_id,
        "parent_span_id": parent_span_id,
        "trace_flags": trace_flags,
        "tracestate": normalized_state,
    }


def trace_context_metadata(context: Any) -> dict[str, Any]:
    """Return the bounded content-free subset safe for durable audit metadata."""

    if not isinstance(context, dict) or not context:
        return {}
    trace_id = str(context.get("trace_id") or "")
    parent_span_id = str(context.get("parent_span_id") or "")
    trace_flags = str(context.get("trace_flags") or "")
    if not re.fullmatch(r"[0-9a-f]{32}", trace_id) or trace_id == "0" * 32:
        return {}
    if not re.fullmatch(r"[0-9a-f]{16}", parent_span_id) or parent_span_id == "0" * 16:
        return {}
    if not re.fullmatch(r"[0-9a-f]{2}", trace_flags):
        return {}
    return {
        "trace_context_schema_version": 1,
        "trace_id": trace_id,
        "parent_span_id": parent_span_id,
        "trace_flags": trace_flags,
        "tracestate_present": bool(context.get("tracestate")),
    }
