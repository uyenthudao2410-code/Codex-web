from __future__ import annotations

from pathlib import Path
from typing import Any


SEMANTIC_LOCALIZATION_SCHEMA_VERSION = 1
DEFAULT_UNAVAILABLE_REASON = "NATIVE_LSP_BINDING_NOT_CONFIGURED"


class UnavailableSemanticLocalizationProvider:
    """Truthful default until an authenticated native semantic adapter is bound."""

    def status(self) -> dict[str, Any]:
        return {
            "schema_version": SEMANTIC_LOCALIZATION_SCHEMA_VERSION,
            "available": False,
            "provider": None,
            "reason": DEFAULT_UNAVAILABLE_REASON,
            "read_only": True,
        }

    def localize(
        self,
        *,
        workspace: Path,
        path: str,
        queries: list[str],
        max_results: int,
    ) -> list[dict[str, Any]]:
        del workspace, path, queries, max_results
        return []


def semantic_provider_status(provider: Any) -> dict[str, Any]:
    """Normalize provider status without inventing availability."""
    try:
        raw = provider.status() if provider is not None and hasattr(provider, "status") else {}
    except Exception as exc:
        return {
            "schema_version": SEMANTIC_LOCALIZATION_SCHEMA_VERSION,
            "available": False,
            "provider": None,
            "reason": "SEMANTIC_PROVIDER_STATUS_FAILED",
            "error_class": type(exc).__name__,
            "read_only": True,
        }
    status = raw if isinstance(raw, dict) else {}
    available = status.get("available") is True
    provider_name = str(status.get("provider") or "").strip()[:120] or None
    reason = str(status.get("reason") or "").strip()[:240]
    result: dict[str, Any] = {
        "schema_version": SEMANTIC_LOCALIZATION_SCHEMA_VERSION,
        "available": available,
        "provider": provider_name,
        "read_only": True,
    }
    if reason:
        result["reason"] = reason
    elif not available:
        result["reason"] = DEFAULT_UNAVAILABLE_REASON
    return result


def _normalize_match(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    path = str(value.get("path") or "").strip()[:1000]
    if not path:
        return None
    result: dict[str, Any] = {"path": path}
    for key in ("line", "column", "end_line", "end_column"):
        raw = value.get(key)
        if isinstance(raw, int) and not isinstance(raw, bool) and raw >= 0:
            result[key] = raw
    for key, limit in (("kind", 120), ("symbol", 500), ("preview", 1200)):
        raw = str(value.get(key) or "").strip()
        if raw:
            result[key] = raw[:limit]
    return result


def run_semantic_localization(
    provider: Any,
    *,
    workspace: Path,
    path: str,
    queries: list[str],
    max_results: int,
) -> dict[str, Any]:
    """Call one read-only provider batch and normalize results for deterministic fallback."""
    status = semantic_provider_status(provider)
    if not status["available"] or not queries:
        return {"provider": status, "results": []}
    try:
        raw_rows = provider.localize(
            workspace=workspace,
            path=path,
            queries=list(queries),
            max_results=max(1, int(max_results)),
        )
    except Exception as exc:
        failed = dict(status)
        failed.update({
            "available": False,
            "reason": "SEMANTIC_PROVIDER_CALL_FAILED",
            "error_class": type(exc).__name__,
        })
        return {
            "provider": failed,
            "results": [
                {"query_index": index, "query": query, "handled": False, "definitive": False, "matches": []}
                for index, query in enumerate(queries)
            ],
        }

    rows = raw_rows if isinstance(raw_rows, list) else []
    by_index: dict[int, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        raw_index = row.get("query_index")
        index = raw_index if isinstance(raw_index, int) and not isinstance(raw_index, bool) else -1
        if index < 0 or index >= len(queries):
            raw_query = str(row.get("query") or "")
            try:
                index = queries.index(raw_query)
            except ValueError:
                continue
        matches: list[dict[str, Any]] = []
        for match in row.get("matches", []) if isinstance(row.get("matches"), list) else []:
            normalized = _normalize_match(match)
            if normalized is not None:
                matches.append(normalized)
            if len(matches) >= max_results:
                break
        definitive = row.get("definitive") is True
        handled = row.get("handled") is True and (bool(matches) or definitive)
        by_index[index] = {
            "query_index": index,
            "query": queries[index],
            "handled": handled,
            "definitive": definitive,
            "matches": matches,
        }

    return {
        "provider": status,
        "results": [
            by_index.get(index, {
                "query_index": index,
                "query": query,
                "handled": False,
                "definitive": False,
                "matches": [],
            })
            for index, query in enumerate(queries)
        ],
    }
