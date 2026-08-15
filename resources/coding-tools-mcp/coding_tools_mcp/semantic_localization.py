from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from .envutils import ENV_PREFIX


SEMANTIC_LOCALIZATION_SCHEMA_VERSION = 1
DEFAULT_UNAVAILABLE_REASON = "NATIVE_LSP_BINDING_NOT_CONFIGURED"
INVALID_BINDING_REASON = "NATIVE_LSP_BINDING_INVALID"
NATIVE_LSP_PROVIDER = "webcodex_native_lsp"
NATIVE_LSP_ENDPOINT_PATH = "/api/connector/internal/semantic/localize"
NATIVE_LSP_URL_ENV = f"{ENV_PREFIX}_NATIVE_LSP_URL"
NATIVE_LSP_CREDENTIAL_FILE_ENV = f"{ENV_PREFIX}_NATIVE_LSP_CREDENTIAL_FILE"
NATIVE_LSP_TIMEOUT_SECONDS = 5.0
NATIVE_LSP_MAX_RESPONSE_BYTES = 1024 * 1024
_PROJECT_CREDENTIAL_RE = re.compile(r"^webcodex_[a-f0-9]{64}$")
_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "::1"})
_BINDING_STATES = frozenset({"unconfigured", "partial", "invalid", "configured"})
_BINDING_COMPONENTS = frozenset({"origin", "credential_file"})


def _semantic_binding_status(
    *,
    state: str,
    origin_configured: bool,
    credential_file_configured: bool,
    invalid_component: str = "",
) -> dict[str, Any]:
    normalized_state = state if state in _BINDING_STATES else "invalid"
    result: dict[str, Any] = {
        "state": normalized_state,
        "origin_configured": bool(origin_configured),
        "credential_file_configured": bool(credential_file_configured),
    }
    missing: list[str] = []
    if not origin_configured:
        missing.append("origin")
    if not credential_file_configured:
        missing.append("credential_file")
    if missing:
        result["missing"] = missing
    if invalid_component in _BINDING_COMPONENTS:
        result["invalid_component"] = invalid_component
    return result


class UnavailableSemanticLocalizationProvider:
    """Truthful default until an authenticated native semantic adapter is bound."""

    def __init__(self, reason: str = DEFAULT_UNAVAILABLE_REASON, *, binding: dict[str, Any] | None = None) -> None:
        self.reason = reason if reason in {DEFAULT_UNAVAILABLE_REASON, INVALID_BINDING_REASON} else DEFAULT_UNAVAILABLE_REASON
        self.binding = binding or _semantic_binding_status(
            state="unconfigured",
            origin_configured=False,
            credential_file_configured=False,
        )

    def status(self) -> dict[str, Any]:
        return {
            "schema_version": SEMANTIC_LOCALIZATION_SCHEMA_VERSION,
            "available": False,
            "provider": None,
            "reason": self.reason,
            "read_only": True,
            "binding": dict(self.binding),
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


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        del req, fp, code, msg, headers, newurl
        return None


def _portable_workspace_identity(path_text: str, *, windows: bool) -> str:
    identity = path_text
    if windows:
        if identity.startswith("\\\\?\\UNC\\"):
            identity = "\\\\" + identity[len("\\\\?\\UNC\\") :]
        elif identity.startswith("\\\\?\\"):
            identity = identity[len("\\\\?\\") :]
        identity = identity.replace("\\", "/")
        if len(identity) >= 2 and identity[1] == ":":
            identity = identity[0].upper() + identity[1:]
    return identity


def portable_workspace_sha256(workspace: Path) -> str:
    resolved = workspace.expanduser().resolve(strict=True)
    identity = _portable_workspace_identity(str(resolved), windows=os.name == "nt")
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def _validated_loopback_origin(raw: str) -> str:
    parsed = urllib.parse.urlsplit(raw.strip())
    if (
        parsed.scheme.lower() != "http"
        or (parsed.hostname or "").lower() not in _LOOPBACK_HOSTS
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
        or parsed.port is None
    ):
        raise ValueError("invalid native LSP origin")
    host = parsed.hostname or ""
    rendered_host = f"[{host}]" if ":" in host else host
    return f"http://{rendered_host}:{parsed.port}"


def _read_project_credential(path_text: str) -> str:
    path = Path(path_text).expanduser()
    if path.is_symlink():
        raise ValueError("project credential file cannot be a symlink")
    info = path.stat()
    if not stat.S_ISREG(info.st_mode):
        raise ValueError("invalid project credential file")
    if os.name != "nt" and info.st_mode & 0o077:
        raise ValueError("project credential file permissions are too broad")
    credential = path.read_text(encoding="utf-8").strip()
    if _PROJECT_CREDENTIAL_RE.fullmatch(credential) is None:
        raise ValueError("invalid project credential")
    return credential


class NativeRustSemanticLocalizationProvider:
    """Read-only semantic bridge over one authenticated loopback endpoint."""

    def __init__(self, *, origin: str, credential: str) -> None:
        self._origin = _validated_loopback_origin(origin)
        if _PROJECT_CREDENTIAL_RE.fullmatch(credential) is None:
            raise ValueError("invalid project credential")
        self._credential = credential
        self._opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect())

    def status(self) -> dict[str, Any]:
        return {
            "schema_version": SEMANTIC_LOCALIZATION_SCHEMA_VERSION,
            "available": True,
            "provider": NATIVE_LSP_PROVIDER,
            "read_only": True,
            "binding": _semantic_binding_status(
                state="configured",
                origin_configured=True,
                credential_file_configured=True,
            ),
        }

    def localize(
        self,
        *,
        workspace: Path,
        path: str,
        queries: list[str],
        max_results: int,
    ) -> list[dict[str, Any]]:
        if not 1 <= len(queries) <= 8:
            raise ValueError("native semantic query count is out of bounds")
        clean_queries = [str(query).strip() for query in queries]
        if any(not query or len(query.encode("utf-8")) > 200 for query in clean_queries):
            raise ValueError("native semantic query is out of bounds")
        bounded_results = int(max_results)
        if not 1 <= bounded_results <= 50:
            raise ValueError("native semantic result limit is out of bounds")
        scope = str(path or ".").strip().replace("\\", "/")
        if (
            scope.startswith("/")
            or (len(scope) >= 2 and scope[1] == ":")
            or ".." in scope.split("/")
            or "\x00" in scope
        ):
            raise ValueError("native semantic scope is invalid")
        body = json.dumps(
            {
                "workspace_sha256": portable_workspace_sha256(workspace),
                "path": scope,
                "queries": clean_queries,
                "max_results": bounded_results,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        request = urllib.request.Request(
            self._origin + NATIVE_LSP_ENDPOINT_PATH,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self._credential}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "coding-tools-mcp-native-lsp/1",
            },
        )
        try:
            with self._opener.open(request, timeout=NATIVE_LSP_TIMEOUT_SECONDS) as response:
                raw = response.read(NATIVE_LSP_MAX_RESPONSE_BYTES + 1)
        except (OSError, TimeoutError, urllib.error.URLError, urllib.error.HTTPError) as exc:
            raise RuntimeError("native semantic transport failed") from exc
        if len(raw) > NATIVE_LSP_MAX_RESPONSE_BYTES:
            raise RuntimeError("native semantic response exceeded limit")
        try:
            envelope = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RuntimeError("native semantic response was invalid") from exc
        data = envelope.get("data") if isinstance(envelope, dict) else None
        if (
            not isinstance(envelope, dict)
            or envelope.get("ok") is not True
            or not isinstance(data, dict)
            or data.get("schema_version") != 1
            or data.get("provider") != NATIVE_LSP_PROVIDER
            or data.get("read_only") is not True
            or not isinstance(data.get("results"), list)
        ):
            raise RuntimeError("native semantic response contract mismatch")
        return data["results"]


def semantic_localizer_from_env() -> Any:
    raw_origin = (os.environ.get(NATIVE_LSP_URL_ENV) or "").strip()
    raw_credential_file = (os.environ.get(NATIVE_LSP_CREDENTIAL_FILE_ENV) or "").strip()
    origin_configured = bool(raw_origin)
    credential_file_configured = bool(raw_credential_file)
    if not raw_origin and not raw_credential_file:
        return UnavailableSemanticLocalizationProvider(
            binding=_semantic_binding_status(
                state="unconfigured",
                origin_configured=False,
                credential_file_configured=False,
            )
        )
    if not raw_origin or not raw_credential_file:
        return UnavailableSemanticLocalizationProvider(
            INVALID_BINDING_REASON,
            binding=_semantic_binding_status(
                state="partial",
                origin_configured=origin_configured,
                credential_file_configured=credential_file_configured,
            ),
        )
    try:
        origin = _validated_loopback_origin(raw_origin)
    except ValueError:
        return UnavailableSemanticLocalizationProvider(
            INVALID_BINDING_REASON,
            binding=_semantic_binding_status(
                state="invalid",
                origin_configured=True,
                credential_file_configured=True,
                invalid_component="origin",
            ),
        )
    try:
        credential = _read_project_credential(raw_credential_file)
    except (OSError, UnicodeError, ValueError):
        return UnavailableSemanticLocalizationProvider(
            INVALID_BINDING_REASON,
            binding=_semantic_binding_status(
                state="invalid",
                origin_configured=True,
                credential_file_configured=True,
                invalid_component="credential_file",
            ),
        )
    return NativeRustSemanticLocalizationProvider(origin=origin, credential=credential)


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
    raw_binding = status.get("binding")
    if isinstance(raw_binding, dict):
        raw_state = str(raw_binding.get("state") or "").strip().lower()
        safe_binding = _semantic_binding_status(
            state=raw_state,
            origin_configured=raw_binding.get("origin_configured") is True,
            credential_file_configured=raw_binding.get("credential_file_configured") is True,
            invalid_component=str(raw_binding.get("invalid_component") or "").strip().lower(),
        )
        raw_missing = raw_binding.get("missing")
        if isinstance(raw_missing, list):
            safe_missing = [str(item) for item in raw_missing if str(item) in _BINDING_COMPONENTS]
            if safe_missing:
                safe_binding["missing"] = safe_missing
        result["binding"] = safe_binding
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
