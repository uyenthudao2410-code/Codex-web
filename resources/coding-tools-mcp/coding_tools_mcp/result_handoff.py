from __future__ import annotations

from typing import Any


LARGE_RESULT_HANDOFF_SCHEMA_VERSION = 1


def truncation_reason(truncated_by: object, *, retention_lost: bool = False) -> str:
    if retention_lost:
        return "OUTPUT_RETENTION_BOUND"
    return "LINE_BUDGET" if str(truncated_by or "").lower() == "lines" else "BYTE_BUDGET"


def large_result_handoff(
    *,
    kind: str,
    source_identity: dict[str, Any],
    scope_identity: dict[str, Any],
    reason: str,
    next_operation: dict[str, Any] | None,
    continuation: object,
    has_more: bool,
    continuation_recovers_all_omitted_data: bool,
    narrow_scope_hint: str | None = None,
) -> dict[str, Any]:
    """Build the bounded, transport-neutral contract for an incomplete result."""

    payload: dict[str, Any] = {
        "schema_version": LARGE_RESULT_HANDOFF_SCHEMA_VERSION,
        "kind": kind,
        "source_identity": dict(source_identity),
        "scope_identity": dict(scope_identity),
        "reason": reason,
        "next_operation": dict(next_operation) if isinstance(next_operation, dict) else None,
        "continuation": continuation,
        "has_more": bool(has_more),
        "recoverability": {
            "continuation_recovers_all_omitted_data": bool(
                continuation_recovers_all_omitted_data
            ),
        },
    }
    if narrow_scope_hint:
        payload["narrow_scope_hint"] = str(narrow_scope_hint)[:500]
    return payload
