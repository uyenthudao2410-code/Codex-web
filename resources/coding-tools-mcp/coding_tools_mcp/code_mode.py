from __future__ import annotations

import json
import re
from collections.abc import Mapping
from pathlib import Path, PurePosixPath
from typing import Any

from .errors import ToolFailure
from .semantic_localization import run_semantic_localization


CODE_MODE_BINDING_SCHEMA_VERSION = 1
CODE_MODE_BINDING_MAX_REQUEST_BYTES = 32 * 1024
CODE_MODE_BINDING_MAX_RESPONSE_BYTES = 256 * 1024
CODE_MODE_BINDING_OPERATIONS = (
    "list_files",
    "read_text",
    "search_text",
    "semantic_search",
)
CODE_MODE_REQUIRED_ISOLATION_GUARANTEES = (
    "no_direct_filesystem",
    "no_network",
    "no_inherited_environment_secrets",
    "no_unrestricted_subprocess",
    "bounded_framed_host_binding_only_ipc",
)
_CODE_MODE_BINDING_OPERATION_SET = frozenset(CODE_MODE_BINDING_OPERATIONS)
_WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:/")
_WINDOWS_DEVICE_RE = re.compile(r"^(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?$", re.IGNORECASE)


def code_mode_worker_isolation_status() -> dict[str, Any]:
    """Truthful readiness for executing untrusted Code Mode programs.

    Process-tree cleanup and write confinement are useful controls, but they
    are not a capability boundary for arbitrary generated code. Keep the gate
    blocked until one backend proves every required guarantee.
    """

    return {
        "status": "blocked",
        "reason": "verified_binding_only_backend_unavailable",
        "backend": None,
        "required_guarantees": list(CODE_MODE_REQUIRED_ISOLATION_GUARANTEES),
        "observed_nonqualifying_primitives": {
            "windows_job_object": "process_lifecycle_only",
            "linux_landlock": "write_confinement_only",
        },
        "embedded_capability_runtime": "not_configured",
    }


def _fail(code: str, message: str) -> ToolFailure:
    return ToolFailure(code, message, category="security", retryable=False)


def _serialized_size(value: Any) -> int:
    try:
        encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ToolFailure(
            "CODE_MODE_BINDING_INVALID",
            "Code Mode binding payload must be JSON serializable.",
            category="validation",
            retryable=False,
        ) from exc
    return len(encoded)


def _project_relative_path(value: Any, *, default: str = ".") -> str:
    text = str(default if value is None else value).strip().replace("\\", "/")
    if not text:
        text = default
    if (
        "\x00" in text
        or ":" in text
        or text.startswith("/")
        or text.startswith("//")
        or _WINDOWS_DRIVE_RE.match(text)
        or text == "~"
        or text.startswith("~/")
    ):
        raise _fail("CODE_MODE_BINDING_PATH_DENIED", "Code Mode binding paths must be project-relative.")
    pure = PurePosixPath(text)
    if any(part == ".." for part in pure.parts):
        raise _fail("CODE_MODE_BINDING_PATH_DENIED", "Code Mode binding paths must remain inside the project.")
    if any(_WINDOWS_DEVICE_RE.match(part) for part in pure.parts):
        raise _fail("CODE_MODE_BINDING_PATH_DENIED", "Code Mode binding paths cannot use reserved device names.")
    normalized = pure.as_posix()
    return "." if normalized in {"", "."} else normalized


def _bounded_int(value: Any, *, default: int, minimum: int, maximum: int, name: str) -> int:
    raw = default if value is None else value
    if isinstance(raw, bool):
        raise ToolFailure("CODE_MODE_BINDING_INVALID", f"{name} must be an integer.", category="validation")
    try:
        result = int(raw)
    except (TypeError, ValueError) as exc:
        raise ToolFailure("CODE_MODE_BINDING_INVALID", f"{name} must be an integer.", category="validation") from exc
    if result < minimum or result > maximum:
        raise ToolFailure(
            "CODE_MODE_BINDING_INVALID",
            f"{name} is outside the Code Mode binding limit.",
            category="validation",
        )
    return result


def _bounded_strings(value: Any, *, name: str, maximum_items: int, maximum_bytes: int) -> list[str]:
    if not isinstance(value, list) or not value or len(value) > maximum_items:
        raise ToolFailure("CODE_MODE_BINDING_INVALID", f"{name} must be a bounded non-empty list.", category="validation")
    result: list[str] = []
    for item in value:
        text = str(item).strip()
        if not text or "\x00" in text or len(text.encode("utf-8")) > maximum_bytes:
            raise ToolFailure("CODE_MODE_BINDING_INVALID", f"{name} contains an invalid value.", category="validation")
        result.append(text)
    return result


def _exact_arguments(arguments: Mapping[str, Any], allowed: frozenset[str]) -> None:
    unexpected = sorted(set(arguments) - allowed)
    if unexpected:
        raise _fail("CODE_MODE_BINDING_DENIED", "Code Mode binding arguments contain unsupported fields.")


class CodeModeHostBindingProxy:
    """Internal read-only host bindings for a future isolated Code Mode worker.

    This object is deliberately not a generic Runtime/tool dispatcher. The worker
    runtime is still absent; callers must not treat this proxy as an isolation
    boundary by itself.
    """

    def __init__(self, runtime: Any) -> None:
        self._runtime = runtime

    def call(self, request: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(request, Mapping):
            raise ToolFailure("CODE_MODE_BINDING_INVALID", "Code Mode binding request must be an object.", category="validation")
        if _serialized_size(request) > CODE_MODE_BINDING_MAX_REQUEST_BYTES:
            raise _fail("CODE_MODE_BINDING_REQUEST_TOO_LARGE", "Code Mode binding request exceeded the byte limit.")
        unexpected = sorted(set(request) - {"schema_version", "operation", "arguments"})
        if unexpected or request.get("schema_version") != CODE_MODE_BINDING_SCHEMA_VERSION:
            raise _fail("CODE_MODE_BINDING_DENIED", "Unsupported Code Mode binding request contract.")
        operation = str(request.get("operation") or "").strip()
        if operation not in _CODE_MODE_BINDING_OPERATION_SET:
            raise _fail("CODE_MODE_BINDING_DENIED", "Requested Code Mode host binding is not allowlisted.")
        raw_arguments = request.get("arguments", {})
        if not isinstance(raw_arguments, Mapping):
            raise ToolFailure("CODE_MODE_BINDING_INVALID", "Code Mode binding arguments must be an object.", category="validation")
        arguments = dict(raw_arguments)

        if operation == "read_text":
            result = self._read_text(arguments)
        elif operation == "list_files":
            result = self._list_files(arguments)
        elif operation == "search_text":
            result = self._search_text(arguments)
        else:
            result = self._semantic_search(arguments)

        envelope = {
            "schema_version": CODE_MODE_BINDING_SCHEMA_VERSION,
            "operation": operation,
            "read_only": True,
            "result": result,
        }
        if _serialized_size(envelope) > CODE_MODE_BINDING_MAX_RESPONSE_BYTES:
            raise _fail("CODE_MODE_BINDING_RESPONSE_TOO_LARGE", "Code Mode binding response exceeded the byte limit.")
        return envelope

    def _resolve_primary_workspace_path(self, raw_path: Any) -> str:
        path = _project_relative_path(raw_path)
        resolved = self._runtime.workspace.resolve_existing(path)
        try:
            relative = resolved.path.relative_to(self._runtime.workspace.root)
        except ValueError as exc:
            raise _fail("CODE_MODE_BINDING_PATH_DENIED", "Code Mode binding path resolved outside the primary project.") from exc
        return "." if str(relative) == "." else relative.as_posix()

    def _read_text(self, arguments: dict[str, Any]) -> dict[str, Any]:
        _exact_arguments(arguments, frozenset({"path", "start_line", "max_lines", "max_bytes"}))
        path = self._resolve_primary_workspace_path(arguments.get("path"))
        start_line = _bounded_int(arguments.get("start_line"), default=1, minimum=1, maximum=1_000_000, name="start_line")
        max_lines = _bounded_int(arguments.get("max_lines"), default=400, minimum=1, maximum=2_000, name="max_lines")
        max_bytes = _bounded_int(arguments.get("max_bytes"), default=64 * 1024, minimum=1, maximum=128 * 1024, name="max_bytes")
        raw = self._runtime.read_file({"path": path, "start_line": start_line, "max_lines": max_lines, "max_bytes": max_bytes})
        return {
            key: raw.get(key)
            for key in (
                "path", "content", "encoding", "start_line", "end_line", "total_lines", "total_bytes",
                "bytes_read", "truncated", "truncated_by", "next_start_line", "warnings",
            )
        }

    def _list_files(self, arguments: dict[str, Any]) -> dict[str, Any]:
        _exact_arguments(arguments, frozenset({"path", "patterns", "max_results"}))
        path = self._resolve_primary_workspace_path(arguments.get("path"))
        patterns = arguments.get("patterns", ["**/*"])
        patterns = _bounded_strings(patterns, name="patterns", maximum_items=8, maximum_bytes=200)
        max_results = _bounded_int(arguments.get("max_results"), default=100, minimum=1, maximum=200, name="max_results")
        raw = self._runtime.list_files({
            "path": path,
            "patterns": patterns,
            "max_results": max_results,
            "include_hidden": False,
            "include_ignored": False,
            "sort": "path",
        })
        files = []
        for item in raw.get("files", []) if isinstance(raw.get("files"), list) else []:
            if not isinstance(item, dict):
                continue
            safe_path = self._resolve_primary_workspace_path(item.get("path"))
            files.append({
                "path": safe_path,
                "type": item.get("type"),
                "size_bytes": item.get("size_bytes"),
                "modified": item.get("modified"),
            })
        return {
            "path": path,
            "files": files,
            "truncated": raw.get("truncated") is True,
            "warnings": list(raw.get("warnings", []))[:4] if isinstance(raw.get("warnings"), list) else [],
        }

    def _search_text(self, arguments: dict[str, Any]) -> dict[str, Any]:
        _exact_arguments(arguments, frozenset({"path", "query", "case_sensitive", "include_globs", "max_results", "context_lines"}))
        path = self._resolve_primary_workspace_path(arguments.get("path"))
        query = str(arguments.get("query") or "").strip()
        if not query or "\x00" in query or len(query.encode("utf-8")) > 500:
            raise ToolFailure("CODE_MODE_BINDING_INVALID", "query is outside the Code Mode binding limit.", category="validation")
        include_globs = arguments.get("include_globs", ["**/*"])
        include_globs = _bounded_strings(include_globs, name="include_globs", maximum_items=8, maximum_bytes=200)
        max_results = _bounded_int(arguments.get("max_results"), default=30, minimum=1, maximum=50, name="max_results")
        context_lines = _bounded_int(arguments.get("context_lines"), default=0, minimum=0, maximum=2, name="context_lines")
        raw = self._runtime.search_text({
            "path": path,
            "query": query,
            "regex": False,
            "case_sensitive": arguments.get("case_sensitive") is True,
            "include_globs": include_globs,
            "context_lines": context_lines,
            "max_results": max_results,
            "max_preview_bytes": 512,
        })
        matches = []
        for item in raw.get("matches", []) if isinstance(raw.get("matches"), list) else []:
            if not isinstance(item, dict):
                continue
            safe_path = self._resolve_primary_workspace_path(item.get("path"))
            projected = dict(item)
            projected["path"] = safe_path
            matches.append(projected)
        return {
            "query": query,
            "matches": matches,
            "total_matches": int(raw.get("total_matches", len(matches)) or 0),
            "truncated": raw.get("truncated") is True,
            "warnings": list(raw.get("warnings", []))[:4] if isinstance(raw.get("warnings"), list) else [],
        }

    def _semantic_search(self, arguments: dict[str, Any]) -> dict[str, Any]:
        _exact_arguments(arguments, frozenset({"path", "queries", "max_results"}))
        path = self._resolve_primary_workspace_path(arguments.get("path"))
        queries = _bounded_strings(arguments.get("queries"), name="queries", maximum_items=8, maximum_bytes=200)
        max_results = _bounded_int(arguments.get("max_results"), default=20, minimum=1, maximum=50, name="max_results")
        raw = run_semantic_localization(
            self._runtime.semantic_localizer,
            workspace=self._runtime.workspace.root,
            path=path,
            queries=queries,
            max_results=max_results,
        )
        status = raw.get("provider") if isinstance(raw.get("provider"), dict) else {}
        safe_status = {
            key: status.get(key)
            for key in ("schema_version", "available", "provider", "reason", "read_only")
            if key in status
        }
        rows = []
        for row in raw.get("results", []) if isinstance(raw.get("results"), list) else []:
            if not isinstance(row, dict):
                continue
            projected = {
                "query_index": row.get("query_index"),
                "query": row.get("query"),
                "handled": row.get("handled") is True,
                "definitive": row.get("definitive") is True,
                "matches": [],
            }
            for match in row.get("matches", []) if isinstance(row.get("matches"), list) else []:
                if not isinstance(match, dict):
                    continue
                safe_path = self._resolve_primary_workspace_path(match.get("path"))
                safe_match = dict(match)
                safe_match["path"] = safe_path
                projected["matches"].append(safe_match)
            rows.append(projected)
        return {"provider": safe_status, "results": rows}
