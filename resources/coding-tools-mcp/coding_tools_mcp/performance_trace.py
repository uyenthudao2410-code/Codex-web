from __future__ import annotations

import copy
import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MAX_RECENT = 100
MAX_RUN_METRICS = 200
MAX_IDLE_GAP_MS = 30 * 60 * 1000


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


class PerformanceTraceStore:
    """Small workspace-local performance ledger for MCP calls.

    The gap between the previous tool completion and the next tool start is an
    estimate of model/network wait time, not local execution time.
    """

    schema_version = 4

    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace.resolve()
        self.state_dir = self.workspace / ".coding-tools"
        self.path = self.state_dir / "performance.json"
        self._lock = threading.RLock()
        self._last_finished_monotonic: float | None = None

    def record(
        self,
        *,
        tool: str,
        started_monotonic: float,
        finished_monotonic: float,
        request_bytes: int = 0,
        response_bytes: int = 0,
        model_visible_bytes: int = 0,
        ok: bool = True,
        cache_hit: bool = False,
        deduplicated: bool = False,
        idempotency_eligible: bool = False,
        idempotency_key_present: bool = False,
        proof_cache_hits: int = 0,
        proof_cache_saved_ms: int = 0,
        orchestration: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        with self._lock:
            wait_before_ms = 0
            if self._last_finished_monotonic is not None:
                gap = max(0, int((started_monotonic - self._last_finished_monotonic) * 1000))
                if gap <= MAX_IDLE_GAP_MS:
                    wait_before_ms = gap
            self._last_finished_monotonic = finished_monotonic
            duration_ms = max(0, int((finished_monotonic - started_monotonic) * 1000))
            state = self._read()
            orchestration = orchestration or {}
            execution_mode = str(orchestration.get("execution_mode") or "")
            route_resolved = str(orchestration.get("route_resolved") or "")
            orchestration_state = str(orchestration.get("orchestration_state") or "")
            event = {
                "tool": tool,
                "started_at": utc_now(),
                "finished_at": utc_now(),
                "duration_ms": duration_ms,
                "wait_before_ms": wait_before_ms,
                "request_bytes": max(0, int(request_bytes)),
                "response_bytes": max(0, int(response_bytes)),
                "model_visible_bytes": max(0, int(model_visible_bytes)),
                "cache_hit": bool(cache_hit),
                "deduplicated": bool(deduplicated),
                "idempotency_eligible": bool(idempotency_eligible),
                "idempotency_key_present": bool(idempotency_key_present),
                "proof_cache_hits": max(0, int(proof_cache_hits)),
                "proof_cache_saved_ms": max(0, int(proof_cache_saved_ms)),
                "ok": bool(ok),
                "run_id": str(orchestration.get("run_id") or ""),
                "wave_id": str(orchestration.get("wave_id") or ""),
                "delegation_id": str(orchestration.get("delegation_id") or ""),
                "execution_mode": execution_mode,
                "route_requested": str(orchestration.get("route_requested") or ""),
                "route_resolved": route_resolved,
                "orchestration_state": orchestration_state,
            }
            state["tool_calls"] += 1
            state["errors"] += 0 if ok else 1
            state["cache_hits"] += 1 if cache_hit else 0
            state["deduplicated_calls"] += 1 if deduplicated else 0
            state["idempotency_eligible_calls"] += 1 if idempotency_eligible else 0
            state["idempotency_eligible_key_calls"] += 1 if idempotency_eligible and idempotency_key_present else 0
            state["idempotency_key_calls"] += 1 if idempotency_key_present else 0
            state["proof_cache_hits"] += event["proof_cache_hits"]
            state["proof_cache_saved_ms"] += event["proof_cache_saved_ms"]
            state["local_execution_ms"] += duration_ms
            state["estimated_wait_ms"] += wait_before_ms
            state["request_bytes"] += event["request_bytes"]
            state["response_bytes"] += event["response_bytes"]
            state["model_visible_bytes"] += event["model_visible_bytes"]
            state["last_finished_at"] = event["finished_at"]
            for bucket_name, value in (
                ("execution_mode_counts", execution_mode),
                ("route_resolved_counts", route_resolved),
                ("orchestration_state_counts", orchestration_state),
            ):
                if value:
                    bucket = state[bucket_name]
                    bucket[value] = int(bucket.get(value, 0)) + 1
            run_id = event["run_id"]
            if run_id:
                run_metrics = state["run_metrics"]
                if run_id not in run_metrics and len(run_metrics) >= MAX_RUN_METRICS:
                    oldest = min(
                        run_metrics,
                        key=lambda key: str(run_metrics[key].get("last_finished_at") or ""),
                    )
                    run_metrics.pop(oldest, None)
                metric = run_metrics.setdefault(run_id, {
                    "tool_calls": 0,
                    "errors": 0,
                    "local_execution_ms": 0,
                    "estimated_wait_ms": 0,
                    "request_bytes": 0,
                    "response_bytes": 0,
                    "model_visible_bytes": 0,
                    "idempotency_eligible_calls": 0,
                    "idempotency_eligible_key_calls": 0,
                    "proof_cache_hits": 0,
                    "proof_cache_saved_ms": 0,
                    "execution_mode_counts": {},
                    "route_resolved_counts": {},
                    "first_started_at": event["started_at"],
                    "last_finished_at": event["finished_at"],
                })
                metric["tool_calls"] += 1
                metric["errors"] += 0 if ok else 1
                metric["local_execution_ms"] += duration_ms
                metric["estimated_wait_ms"] += wait_before_ms
                metric["request_bytes"] += event["request_bytes"]
                metric["response_bytes"] += event["response_bytes"]
                metric["model_visible_bytes"] += event["model_visible_bytes"]
                metric["idempotency_eligible_calls"] += 1 if idempotency_eligible else 0
                metric["idempotency_eligible_key_calls"] += 1 if idempotency_eligible and idempotency_key_present else 0
                metric["proof_cache_hits"] += event["proof_cache_hits"]
                metric["proof_cache_saved_ms"] += event["proof_cache_saved_ms"]
                metric["last_finished_at"] = event["finished_at"]
                for bucket_name, value in (
                    ("execution_mode_counts", execution_mode),
                    ("route_resolved_counts", route_resolved),
                ):
                    if value:
                        bucket = metric[bucket_name]
                        bucket[value] = int(bucket.get(value, 0)) + 1
            state["recent"] = (state.get("recent", []) + [event])[-MAX_RECENT:]
            self._write(state)
            return copy.deepcopy(state)

    def get(self) -> dict[str, Any]:
        with self._lock:
            return copy.deepcopy(self._read())

    def clear(self) -> dict[str, Any]:
        with self._lock:
            self._last_finished_monotonic = None
            try:
                self.path.unlink(missing_ok=True)
            except OSError:
                pass
            return self._default()

    @staticmethod
    def _default() -> dict[str, Any]:
        return {
            "version": 4,
            "tool_calls": 0,
            "errors": 0,
            "cache_hits": 0,
            "deduplicated_calls": 0,
            "idempotency_eligible_calls": 0,
            "idempotency_eligible_key_calls": 0,
            "idempotency_key_calls": 0,
            "proof_cache_hits": 0,
            "proof_cache_saved_ms": 0,
            "local_execution_ms": 0,
            "estimated_wait_ms": 0,
            "request_bytes": 0,
            "response_bytes": 0,
            "model_visible_bytes": 0,
            "execution_mode_counts": {},
            "route_resolved_counts": {},
            "orchestration_state_counts": {},
            "run_metrics": {},
            "last_finished_at": None,
            "recent": [],
        }

    def _read(self) -> dict[str, Any]:
        state = self._default()
        try:
            parsed = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return state
        if isinstance(parsed, dict):
            state.update(parsed)
        state["version"] = self.schema_version
        if not isinstance(state.get("recent"), list):
            state["recent"] = []
        for key in ("execution_mode_counts", "route_resolved_counts", "orchestration_state_counts", "run_metrics"):
            if not isinstance(state.get(key), dict):
                state[key] = {}
        for key in (
            "idempotency_key_calls", "idempotency_eligible_calls", "idempotency_eligible_key_calls",
            "proof_cache_hits", "proof_cache_saved_ms", "model_visible_bytes",
        ):
            try:
                state[key] = max(0, int(state.get(key, 0)))
            except (TypeError, ValueError):
                state[key] = 0
        return state

    def _write(self, state: dict[str, Any]) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_name(f".{self.path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
        try:
            temp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
            os.replace(temp, self.path)
        finally:
            temp.unlink(missing_ok=True)
