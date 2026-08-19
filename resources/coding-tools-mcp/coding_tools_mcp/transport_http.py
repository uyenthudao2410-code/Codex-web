from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import threading
import time
import urllib.parse
from dataclasses import dataclass
from typing import Any

from .envutils import ENV_PREFIX, truthy_env


HTTP_SESSION_TTL_SECONDS = 60 * 60
MAX_TRACKED_SESSION_ALIASES = 512
HTTP_SESSION_SCOPE_PREFIX = "ws1"
HTTP_SESSION_SCOPE_HEX_CHARS = 16


class StaleHTTPSessionError(RuntimeError):
    pass


def workspace_session_scope(workspace: Any, auth_token: str | None = None) -> str:
    normalized = os.path.normcase(os.path.abspath(os.fspath(workspace)))
    material = b"coding-tools-mcp-workspace-session-v1\0" + normalized.encode("utf-8", errors="surrogatepass")
    if auth_token:
        digest = hmac.new(str(auth_token).encode("utf-8"), material, hashlib.sha256).hexdigest()
    else:
        digest = hashlib.sha256(material).hexdigest()
    return digest[:HTTP_SESSION_SCOPE_HEX_CHARS]


def new_workspace_session_id(
    workspace: Any,
    auth_token: str | None = None,
    *,
    execution_scoped: bool = False,
    execution_context_id: str = "",
) -> str:
    scope = workspace_session_scope(workspace, auth_token)
    if execution_scoped:
        context_id = str(execution_context_id or secrets.token_hex(8)).lower()
        if len(context_id) != 16 or any(char not in "0123456789abcdef" for char in context_id):
            raise ValueError("execution_context_id must be 16 lowercase hex characters")
        token = f"ctx_{context_id}_{secrets.token_urlsafe(12)}"
    else:
        token = f"legacy_{secrets.token_urlsafe(18)}"
    return f"{HTTP_SESSION_SCOPE_PREFIX}.{scope}.{token}"


def session_execution_context_id(session_id: str) -> str:
    parts = str(session_id).split(".", 2)
    if len(parts) != 3:
        return ""
    token = parts[2]
    if not token.startswith("ctx_"):
        return ""
    raw = token[4:]
    context_id, separator, alias = raw.partition("_")
    if not separator or not alias:
        return ""
    if len(context_id) != 16 or any(char not in "0123456789abcdef" for char in context_id):
        return ""
    return context_id


def _session_workspace_scope(session_id: str) -> str | None:
    if not str(session_id).startswith(f"{HTTP_SESSION_SCOPE_PREFIX}."):
        return None
    parts = str(session_id).split(".", 2)
    if len(parts) != 3:
        return ""
    scope = parts[1].lower()
    if len(scope) != HTTP_SESSION_SCOPE_HEX_CHARS or any(char not in "0123456789abcdef" for char in scope):
        return ""
    if not parts[2]:
        return ""
    return scope


@dataclass
class HTTPSessionRecord:
    runtime: Any
    last_seen: float


class HTTPSessionRuntimeView:
    """Per-session protocol/task identity backed by one shared process Runtime."""

    def __init__(self, runtime: Any, *, session_id: str, execution_context_id: str) -> None:
        self._runtime = runtime
        self.http_session_id = session_id
        self.execution_context_id = execution_context_id
        self.initialized = False
        self.protocol_version = getattr(runtime, "protocol_version", "")

    def __getattr__(self, name: str) -> Any:
        return getattr(self._runtime, name)


class HTTPSessionManager:
    """Route all authenticated HTTP sessions through one shared Runtime while isolating stateful ChatWeb execution contexts."""

    def __init__(self, runtime: Any) -> None:
        self._runtime = runtime
        self._sessions: dict[str, HTTPSessionRecord] = {}
        self._lock = threading.Lock()
        self._closed = False

    def create(self, *, execution_scoped: bool = False) -> Any:
        self.prune()
        with self._lock:
            if self._closed:
                raise RuntimeError("HTTP session manager is closed")
            if not execution_scoped:
                session_id = self._runtime.http_session_id
                self._sessions[session_id] = HTTPSessionRecord(
                    runtime=self._runtime,
                    last_seen=time.time(),
                )
                self._trim_locked()
                return self._runtime
            context_id = secrets.token_hex(8)
            session_id = new_workspace_session_id(
                self._runtime.workspace.root,
                getattr(self._runtime, "auth_token", None),
                execution_scoped=True,
                execution_context_id=context_id,
            )
            view = HTTPSessionRuntimeView(
                self._runtime,
                session_id=session_id,
                execution_context_id=context_id,
            )
            self._sessions[session_id] = HTTPSessionRecord(runtime=view, last_seen=time.time())
            self._trim_locked()
            return view

    def get(self, session_id: str) -> Any | None:
        self.prune()
        presented_scope = _session_workspace_scope(session_id)
        current_scope = workspace_session_scope(
            self._runtime.workspace.root,
            getattr(self._runtime, "auth_token", None),
        )
        if presented_scope is not None and presented_scope != current_scope:
            raise StaleHTTPSessionError("MCP session is scoped to a different workspace")
        with self._lock:
            if self._closed:
                return None
            record = self._sessions.get(session_id)
            if record is not None:
                record.last_seen = time.time()
                return record.runtime

            execution_context_id = session_execution_context_id(session_id)
            if execution_context_id:
                # A stateful alias can survive server recreation. Mint a new alias
                # while retaining the encoded execution-context id and task state.
                canonical_id = new_workspace_session_id(
                    self._runtime.workspace.root,
                    getattr(self._runtime, "auth_token", None),
                    execution_scoped=True,
                    execution_context_id=execution_context_id,
                )
                view = HTTPSessionRuntimeView(
                    self._runtime,
                    session_id=canonical_id,
                    execution_context_id=execution_context_id,
                )
                now = time.time()
                rebound = HTTPSessionRecord(runtime=view, last_seen=now)
                self._sessions[session_id] = rebound
                self._sessions[canonical_id] = rebound
                self._trim_locked()
                return view

            if presented_scope is None:
                self._runtime.legacy_session_alias_uses += 1
            # Legacy ids remain aliases for the process-global projection. This
            # preserves old tunnel/reconnect behavior during migration.
            self._sessions[session_id] = HTTPSessionRecord(
                runtime=self._runtime,
                last_seen=time.time(),
            )
            self._trim_locked()
            return self._runtime

    def delete(self, session_id: str) -> bool:
        with self._lock:
            if self._closed:
                return False
            record = self._sessions.pop(session_id, None)
            if record is not None and isinstance(record.runtime, HTTPSessionRuntimeView):
                aliases = [
                    key for key, value in self._sessions.items()
                    if value.runtime is record.runtime
                ]
                for key in aliases:
                    self._sessions.pop(key, None)
            return True

    def prune(self) -> None:
        cutoff = time.time() - HTTP_SESSION_TTL_SECONDS
        with self._lock:
            expired = [
                session_id
                for session_id, record in self._sessions.items()
                if record.last_seen < cutoff
            ]
            for session_id in expired:
                self._sessions.pop(session_id, None)
            self._trim_locked()

    def _trim_locked(self) -> None:
        if len(self._sessions) <= MAX_TRACKED_SESSION_ALIASES:
            return
        newest = sorted(
            self._sessions.items(),
            key=lambda item: item[1].last_seen,
            reverse=True,
        )[:MAX_TRACKED_SESSION_ALIASES]
        self._sessions = dict(newest)

    def stats(self) -> dict[str, int]:
        with self._lock:
            context_ids = {
                str(getattr(record.runtime, "execution_context_id", "") or "")
                for record in self._sessions.values()
                if str(getattr(record.runtime, "execution_context_id", "") or "")
            }
            return {
                "tracked_aliases": len(self._sessions),
                "shared_runtimes": 0 if self._closed else 1,
                "execution_contexts": len(context_ids),
            }

    def close(self) -> None:
        with self._lock:
            self._closed = True
            self._sessions.clear()

STATELESS_HTTP_2026_ENV = f"{ENV_PREFIX}_STATELESS_HTTP_2026"


def _http_base_for_bind_host(host: str, port: int) -> str:
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    return f"http://{host}:{port}"


def _first_header_value(value: str | None) -> str:
    return (value or "").split(",", 1)[0].strip()


def _first_form_value(params: dict[str, list[str]], key: str) -> str:
    values = params.get(key)
    return values[0] if values else ""


def stateless_http_2026_enabled() -> bool:
    """Both MCP eras are served by default on every transport, matching upstream.

    Legacy 2025-11-25/2025-06-18 clients are unaffected: they never send a
    modern MCP-Protocol-Version header or params._meta protocolVersion.
    Operators can explicitly disable the modern era with
    CODING_TOOLS_MCP_STATELESS_HTTP_2026=0.
    """

    raw = os.environ.get(STATELESS_HTTP_2026_ENV)
    if raw is None:
        return True
    return truthy_env(raw)


def _decode_mcp_name_header(value: str) -> str | None:
    if not (value.startswith("=?base64?") and value.endswith("?=")):
        return value
    try:
        raw = base64.b64decode(value[len("=?base64?") : -2], validate=True)
        return raw.decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return None


def _request_mcp_name(request: dict[str, Any]) -> str | None:
    params = request.get("params")
    if not isinstance(params, dict):
        return None
    method = str(request.get("method") or "")
    if method in {"tools/call", "prompts/get"}:
        value = params.get("name")
        return value if isinstance(value, str) else None
    if method == "resources/read":
        value = params.get("uri")
        return value if isinstance(value, str) else None
    return None


def _forwarded_header_param(value: str | None, name: str) -> str:
    first = _first_header_value(value)
    for part in first.split(";"):
        key, sep, raw = part.strip().partition("=")
        if sep and key.lower() == name:
            return raw.strip().strip('"')
    return ""


def _safe_external_host(host: str) -> str:
    host = host.strip()
    if not host or any(ch.isspace() or ch in "/\\@?#" for ch in host):
        return ""
    try:
        parsed = urllib.parse.urlsplit(f"//{host}")
        _ = parsed.port
    except ValueError:
        return ""
    if not parsed.hostname or parsed.username is not None or parsed.password is not None:
        return ""
    return host
