from __future__ import annotations

import copy
import hashlib
import json
import threading
import time
from pathlib import Path
from typing import Any

from .performance_trace import utc_now


_FAST_TOOL_CACHE: dict[str, tuple[float, int, dict[str, Any]]] = {}
_FAST_TOOL_CACHE_LOCK = threading.Lock()
_WORKSPACE_CACHE_GENERATION: dict[str, int] = {}
_WORKSPACE_PREHEAT_STARTED: set[str] = set()


class RuntimeCacheMixin:
    """Small process-local cache scoped to the active workspace."""

    def _workspace_cache_namespace(self) -> str:
        return str(self.workspace.root).casefold()

    def _cache_generation(self) -> int:
        with _FAST_TOOL_CACHE_LOCK:
            return _WORKSPACE_CACHE_GENERATION.get(self._workspace_cache_namespace(), 0)

    def _fast_cache_key(self, tool: str, args: dict[str, Any], *, file_paths: list[Path] | None = None) -> str:
        fingerprints: list[tuple[str, int, int]] = []
        for path in file_paths or []:
            try:
                stat_result = path.stat()
                fingerprints.append((str(path), stat_result.st_size, stat_result.st_mtime_ns))
            except OSError:
                fingerprints.append((str(path), -1, -1))
        raw = json.dumps(
            {"workspace": str(self.workspace.root), "tool": tool, "args": args, "files": fingerprints},
            ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str,
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _fast_cache_get(self, key: str, ttl_seconds: int) -> dict[str, Any] | None:
        now = time.monotonic()
        generation = self._cache_generation()
        with _FAST_TOOL_CACHE_LOCK:
            cached = _FAST_TOOL_CACHE.get(key)
        if not cached or cached[1] != generation or now - cached[0] > ttl_seconds:
            return None
        payload = copy.deepcopy(cached[2])
        payload["cache"] = {"hit": True, "age_ms": int((now - cached[0]) * 1000)}
        payload["cache_hit"] = True
        return payload

    def _fast_cache_put(self, key: str, payload: dict[str, Any]) -> None:
        generation = self._cache_generation()
        with _FAST_TOOL_CACHE_LOCK:
            if len(_FAST_TOOL_CACHE) >= 128:
                oldest = min(_FAST_TOOL_CACHE, key=lambda item: _FAST_TOOL_CACHE[item][0])
                _FAST_TOOL_CACHE.pop(oldest, None)
            _FAST_TOOL_CACHE[key] = (time.monotonic(), generation, copy.deepcopy(payload))

    def _invalidate_fast_cache(self) -> None:
        namespace = self._workspace_cache_namespace()
        with _FAST_TOOL_CACHE_LOCK:
            _WORKSPACE_CACHE_GENERATION[namespace] = _WORKSPACE_CACHE_GENERATION.get(namespace, 0) + 1

    def preheat_workspace_async(self) -> None:
        namespace = self._workspace_cache_namespace()
        with _FAST_TOOL_CACHE_LOCK:
            if namespace in _WORKSPACE_PREHEAT_STARTED:
                return
            _WORKSPACE_PREHEAT_STARTED.add(namespace)

        def preheat() -> None:
            started_wall_utc = utc_now()
            started = time.monotonic()
            try:
                payload = self.workspace_context({"path": ".", "max_entries": 40, "detail": "compact"})
                payload["preheated"] = True
                ok = True
            except Exception:
                ok = False
            finished = time.monotonic()
            finished_wall_utc = utc_now()
            try:
                self.performance_trace.record(
                    tool="workspace_preheat", started_monotonic=started, finished_monotonic=finished, ok=ok,
                    started_wall_utc=started_wall_utc, finished_wall_utc=finished_wall_utc,
                    orchestration=self.task_state.get().get("orchestration", {}),
                )
            except Exception:
                pass

        threading.Thread(target=preheat, name="coding-tools-preheat", daemon=True).start()
