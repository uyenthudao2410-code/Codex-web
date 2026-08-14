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
IDEMPOTENCY_POLICIES = frozenset({"none", "optional", "required"})
IDEMPOTENCY_KEY_SOURCES = frozenset({"none", "explicit", "derived"})
ERROR_CLASSES = frozenset({
    "CONTROL_PATH", "CONTROL_CWD", "CONTROL_SCHEMA", "CONTROL_CONNECTOR",
    "CAPACITY", "DEADLINE", "PROMPT_SIZE", "MODEL_CANDIDATE_INVALID",
    "BASE_DRIFT", "PATCH_AMBIGUOUS", "PROOF_INFRA", "PROOF_CODE_FAILURE",
    "AUTHORITY_DENIED", "USER_BLOCKED", "PROVIDER", "IDEMPOTENCY",
    "VALIDATION", "RUNTIME", "UNKNOWN",
})
PHASE_TIMING_KEYS = (
    "preflight_ms", "workspace_ms", "localization_ms", "packet_build_ms",
    "queue_ms", "dispatch_transport_ms", "transport_ms", "model_wall_ms",
    "provider_ms", "candidate_validate_ms", "apply_ms", "materialization_ms",
    "proof_ms", "accept_wait_ms", "replan_ms", "handoff_ms", "total_ms",
    "total_tta_ms",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


class PerformanceTraceStore:
    """Small workspace-local performance ledger for MCP calls.

    The gap between the previous tool completion and the next tool start is an
    estimate of model/network wait time, not local execution time.
    """

    schema_version = 5

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
        idempotency_policy: str = "none",
        idempotency_key_source: str = "none",
        error_class: str = "",
        proof_cache_eligible: int = 0,
        proof_cache_hits: int = 0,
        proof_cache_misses: int = 0,
        proof_cache_miss_reasons: dict[str, Any] | None = None,
        proof_cache_saved_ms: int = 0,
        orchestration: dict[str, Any] | None = None,
        phase_timing: dict[str, Any] | None = None,
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
            measured_phase_timing = self._normalize_phase_timing(phase_timing)
            measured_miss_reasons = self._normalize_count_map(proof_cache_miss_reasons)
            measured_policy = str(idempotency_policy or "none").strip().lower()
            if measured_policy not in IDEMPOTENCY_POLICIES:
                measured_policy = "none"
            measured_key_source = str(idempotency_key_source or "none").strip().lower()
            if measured_key_source not in IDEMPOTENCY_KEY_SOURCES or not idempotency_key_present:
                measured_key_source = "none"
            measured_error_class = self._normalize_error_class(error_class) if not ok else ""
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
                "idempotency_policy": measured_policy,
                "idempotency_key_source": measured_key_source,
                "error_class": measured_error_class,
                "proof_cache_eligible": max(0, int(proof_cache_eligible)),
                "proof_cache_hits": max(0, int(proof_cache_hits)),
                "proof_cache_misses": max(0, int(proof_cache_misses)),
                "proof_cache_miss_reasons": measured_miss_reasons,
                "proof_cache_saved_ms": max(0, int(proof_cache_saved_ms)),
                "ok": bool(ok),
                "run_id": str(orchestration.get("run_id") or ""),
                "wave_id": str(orchestration.get("wave_id") or ""),
                "delegation_id": str(orchestration.get("delegation_id") or ""),
                "execution_mode": execution_mode,
                "route_requested": str(orchestration.get("route_requested") or ""),
                "route_resolved": route_resolved,
                "orchestration_state": orchestration_state,
                "phase_timing": measured_phase_timing,
            }
            state["tool_calls"] += 1
            state["errors"] += 0 if ok else 1
            state["cache_hits"] += 1 if cache_hit else 0
            state["deduplicated_calls"] += 1 if deduplicated else 0
            state["idempotency_eligible_calls"] += 1 if idempotency_eligible else 0
            state["idempotency_eligible_key_calls"] += 1 if idempotency_eligible and idempotency_key_present else 0
            state["idempotency_key_calls"] += 1 if idempotency_key_present else 0
            if measured_policy == "required":
                state["idempotency_required_calls"] += 1
                state["idempotency_required_key_calls"] += 1 if idempotency_key_present else 0
            elif measured_policy == "optional":
                state["idempotency_optional_calls"] += 1
                state["idempotency_optional_key_calls"] += 1 if idempotency_key_present else 0
            if measured_key_source == "derived":
                state["idempotency_auto_key_calls"] += 1
            if measured_error_class:
                state["error_class_counts"][measured_error_class] = int(state["error_class_counts"].get(measured_error_class, 0)) + 1
            state["proof_cache_eligible"] += event["proof_cache_eligible"]
            state["proof_cache_hits"] += event["proof_cache_hits"]
            state["proof_cache_misses"] += event["proof_cache_misses"]
            for reason, count in measured_miss_reasons.items():
                state["proof_cache_miss_reasons"][reason] = int(state["proof_cache_miss_reasons"].get(reason, 0)) + count
            state["proof_cache_saved_ms"] += event["proof_cache_saved_ms"]
            state["local_execution_ms"] += duration_ms
            state["estimated_wait_ms"] += wait_before_ms
            state["request_bytes"] += event["request_bytes"]
            state["response_bytes"] += event["response_bytes"]
            state["model_visible_bytes"] += event["model_visible_bytes"]
            if measured_phase_timing:
                state["phase_timing_samples"] += 1
                for key, value in measured_phase_timing.items():
                    if not key.endswith("_ms"):
                        continue
                    state["phase_timing_ms"][key] = int(state["phase_timing_ms"].get(key, 0)) + int(value)
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
                    "idempotency_required_calls": 0,
                    "idempotency_required_key_calls": 0,
                    "idempotency_optional_calls": 0,
                    "idempotency_optional_key_calls": 0,
                    "idempotency_auto_key_calls": 0,
                    "error_class_counts": {},
                    "proof_cache_eligible": 0,
                    "proof_cache_hits": 0,
                    "proof_cache_misses": 0,
                    "proof_cache_miss_reasons": {},
                    "proof_cache_saved_ms": 0,
                    "phase_timing_samples": 0,
                    "phase_timing_ms": {},
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
                if measured_policy == "required":
                    metric["idempotency_required_calls"] += 1
                    metric["idempotency_required_key_calls"] += 1 if idempotency_key_present else 0
                elif measured_policy == "optional":
                    metric["idempotency_optional_calls"] += 1
                    metric["idempotency_optional_key_calls"] += 1 if idempotency_key_present else 0
                if measured_key_source == "derived":
                    metric["idempotency_auto_key_calls"] += 1
                if measured_error_class:
                    metric["error_class_counts"][measured_error_class] = int(metric["error_class_counts"].get(measured_error_class, 0)) + 1
                metric.setdefault("proof_cache_eligible", 0)
                metric.setdefault("proof_cache_misses", 0)
                metric.setdefault("proof_cache_miss_reasons", {})
                metric["proof_cache_eligible"] += event["proof_cache_eligible"]
                metric["proof_cache_hits"] += event["proof_cache_hits"]
                metric["proof_cache_misses"] += event["proof_cache_misses"]
                for reason, count in measured_miss_reasons.items():
                    metric["proof_cache_miss_reasons"][reason] = int(metric["proof_cache_miss_reasons"].get(reason, 0)) + count
                metric["proof_cache_saved_ms"] += event["proof_cache_saved_ms"]
                if measured_phase_timing:
                    metric["phase_timing_samples"] += 1
                    for key, value in measured_phase_timing.items():
                        if not key.endswith("_ms"):
                            continue
                        metric["phase_timing_ms"][key] = int(metric["phase_timing_ms"].get(key, 0)) + int(value)
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
            "version": 5,
            "tool_calls": 0,
            "errors": 0,
            "cache_hits": 0,
            "deduplicated_calls": 0,
            "idempotency_eligible_calls": 0,
            "idempotency_eligible_key_calls": 0,
            "idempotency_key_calls": 0,
            "idempotency_required_calls": 0,
            "idempotency_required_key_calls": 0,
            "idempotency_optional_calls": 0,
            "idempotency_optional_key_calls": 0,
            "idempotency_auto_key_calls": 0,
            "error_class_counts": {},
            "proof_cache_eligible": 0,
            "proof_cache_hits": 0,
            "proof_cache_misses": 0,
            "proof_cache_miss_reasons": {},
            "proof_cache_saved_ms": 0,
            "local_execution_ms": 0,
            "estimated_wait_ms": 0,
            "request_bytes": 0,
            "response_bytes": 0,
            "model_visible_bytes": 0,
            "phase_timing_samples": 0,
            "phase_timing_ms": {},
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
        for key in ("execution_mode_counts", "route_resolved_counts", "orchestration_state_counts", "run_metrics", "proof_cache_miss_reasons", "error_class_counts"):
            if not isinstance(state.get(key), dict):
                state[key] = {}
        if not isinstance(state.get("phase_timing_ms"), dict):
            state["phase_timing_ms"] = {}
        for key in (
            "idempotency_key_calls", "idempotency_eligible_calls", "idempotency_eligible_key_calls",
            "idempotency_required_calls", "idempotency_required_key_calls",
            "idempotency_optional_calls", "idempotency_optional_key_calls", "idempotency_auto_key_calls",
            "proof_cache_eligible", "proof_cache_hits", "proof_cache_misses", "proof_cache_saved_ms",
            "model_visible_bytes", "phase_timing_samples",
        ):
            try:
                state[key] = max(0, int(state.get(key, 0)))
            except (TypeError, ValueError):
                state[key] = 0
        state["proof_cache_miss_reasons"] = self._normalize_count_map(state["proof_cache_miss_reasons"])
        state["error_class_counts"] = self._normalize_count_map(state["error_class_counts"])
        normalized_phase_totals: dict[str, int] = {}
        for key, value in state["phase_timing_ms"].items():
            if not str(key).endswith("_ms") or isinstance(value, bool):
                continue
            try:
                measured = int(value)
            except (TypeError, ValueError):
                continue
            if measured >= 0:
                normalized_phase_totals[str(key)] = measured
        state["phase_timing_ms"] = normalized_phase_totals
        for metric in state["run_metrics"].values():
            if not isinstance(metric, dict):
                continue
            metric.setdefault("phase_timing_samples", 0)
            metric.setdefault("phase_timing_ms", {})
            metric.setdefault("proof_cache_eligible", 0)
            metric.setdefault("proof_cache_hits", 0)
            metric.setdefault("proof_cache_misses", 0)
            metric.setdefault("proof_cache_miss_reasons", {})
            metric.setdefault("proof_cache_saved_ms", 0)
            metric.setdefault("idempotency_required_calls", 0)
            metric.setdefault("idempotency_required_key_calls", 0)
            metric.setdefault("idempotency_optional_calls", 0)
            metric.setdefault("idempotency_optional_key_calls", 0)
            metric.setdefault("idempotency_auto_key_calls", 0)
            metric.setdefault("error_class_counts", {})
            metric["proof_cache_miss_reasons"] = self._normalize_count_map(metric["proof_cache_miss_reasons"])
            metric["error_class_counts"] = self._normalize_count_map(metric["error_class_counts"])
            if not isinstance(metric["phase_timing_ms"], dict):
                metric["phase_timing_ms"] = {}
        return state

    @staticmethod
    def _normalize_count_map(value: dict[str, Any] | None) -> dict[str, int]:
        if not isinstance(value, dict):
            return {}
        result: dict[str, int] = {}
        for raw_key, raw_count in list(value.items())[:50]:
            key = str(raw_key or "").strip()[:80]
            if not key or isinstance(raw_count, bool):
                continue
            try:
                count = int(raw_count)
            except (TypeError, ValueError):
                continue
            if count > 0:
                result[key] = count
        return result

    @staticmethod
    def _normalize_error_class(value: Any) -> str:
        normalized = str(value or "").strip().upper()
        return normalized if normalized in ERROR_CLASSES else "UNKNOWN"

    @staticmethod
    def _normalize_phase_timing(value: dict[str, Any] | None) -> dict[str, Any]:
        if not isinstance(value, dict):
            return {}
        result: dict[str, Any] = {}
        scope = str(value.get("scope") or "").strip()[:80]
        source = str(value.get("source") or "").strip()[:80]
        if scope:
            result["scope"] = scope
        if source:
            result["source"] = source
        for key in PHASE_TIMING_KEYS:
            raw = value.get(key)
            if isinstance(raw, bool) or not isinstance(raw, (int, float)):
                continue
            measured = int(raw)
            if measured >= 0:
                result[key] = measured
        if not any(key.endswith("_ms") for key in result):
            return {}
        return result

    def _write(self, state: dict[str, Any]) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_name(f".{self.path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
        try:
            temp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
            os.replace(temp, self.path)
        finally:
            temp.unlink(missing_ok=True)
