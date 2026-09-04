from __future__ import annotations

import copy
import hashlib
import json
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .trace_context import trace_context_metadata


MAX_RECENT = 100
MAX_RUN_METRICS = 200
MAX_IDLE_GAP_MS = 30 * 60 * 1000
MAX_HOURLY_BUCKETS = 168
IDEMPOTENCY_POLICIES = frozenset({"none", "optional", "required"})
IDEMPOTENCY_KEY_SOURCES = frozenset({"none", "explicit", "derived"})
IDEMPOTENCY_POLICY_EPOCH = "task_epoch_v1"
ERROR_TAXONOMY_EPOCH = "causal_error_taxonomy_v1"
ERROR_CLASSES = frozenset({
    "CONTROL_PATH", "CONTROL_CWD", "CONTROL_SCHEMA", "CONTROL_CONNECTOR",
    "CAPACITY", "DEADLINE", "PROMPT_SIZE", "MODEL_CANDIDATE_INVALID",
    "BASE_DRIFT", "PATCH_AMBIGUOUS", "PROOF_INFRA", "PROOF_CODE_FAILURE",
    "AUTHORITY_DENIED", "USER_BLOCKED", "PROVIDER", "IDEMPOTENCY",
    "VALIDATION", "RUNTIME", "FILESYSTEM", "POLICY", "NOT_FOUND",
    "INTERNAL", "CONFLICT", "UNKNOWN",
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


def build_tool_invocation_context(
    *,
    tool: str,
    args: dict[str, Any],
    request_id: str | int | None,
    started_wall_utc: str,
    hub: dict[str, Any],
    task: dict[str, Any],
    trace_context: dict[str, Any],
    task_context_id: str,
    process_instance_id: str,
) -> dict[str, Any]:
    """Build bounded, content-free correlation for one public tool invocation."""
    orchestration = task.get("orchestration") if isinstance(task.get("orchestration"), dict) else {}
    trace = trace_context_metadata(trace_context)
    request_identity = str(request_id if request_id is not None else "")[:128]
    bounded_task_context_id = str(task_context_id or "")[:128]
    argument_fingerprint = hashlib.sha256(
        json.dumps(args, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode(
            "utf-8", errors="replace"
        )
    ).hexdigest()
    identity_source = "transport_request_id" if request_identity else "runtime_boundary"
    basis = {
        "tool": tool,
        "request_id": request_identity,
        "task_context_id": bounded_task_context_id,
        "session_instance": str(hub.get("session_instance") or "")[:128],
        "execution_context_id": str(hub.get("execution_context_id") or "")[:128],
        "trace_id": str(trace.get("trace_id") or "")[:128],
        "parent_span_id": str(trace.get("parent_span_id") or "")[:128],
        "argument_fingerprint": argument_fingerprint,
    }
    if not request_identity:
        basis.update({
            "process_instance_id": process_instance_id,
            "started_wall_utc": started_wall_utc,
            "thread_id": threading.get_ident(),
        })
    invocation_id = hashlib.sha256(
        json.dumps(basis, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "schema_version": 1,
        "invocation_id": invocation_id,
        "identity_source": identity_source,
        "request_id": request_identity,
        "task_context_id": bounded_task_context_id,
        "task_id": str(task.get("task_id") or "")[:128],
        "session_instance": str(hub.get("session_instance") or "")[:128],
        "execution_context_id": str(hub.get("execution_context_id") or "")[:128],
        "client_id": str(hub.get("client_id") or "")[:64],
        "client_type": str(hub.get("client_type") or "")[:32],
        "turn_id": str(hub.get("turn_id") or orchestration.get("turn_id") or "")[:128],
        "trace_context": trace,
    }


class PerformanceTraceStore:
    """Small workspace-local performance ledger for MCP calls.

    The gap between the previous tool completion and the next tool start is an
    estimate of model/network wait time, not local execution time.
    """

    schema_version = 6

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
        started_wall_utc: str = "",
        finished_wall_utc: str = "",
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
        idempotency_operation: str = "",
        idempotency_missing_reason: str = "",
        error_class: str = "",
        proof_cache_eligible: int = 0,
        proof_cache_hits: int = 0,
        proof_cache_misses: int = 0,
        proof_cache_miss_reasons: dict[str, Any] | None = None,
        proof_cache_saved_ms: int = 0,
        orchestration: dict[str, Any] | None = None,
        phase_timing: dict[str, Any] | None = None,
        localization: dict[str, Any] | None = None,
        result_tail: dict[str, Any] | None = None,
        invocation: dict[str, Any] | None = None,
        outcome: dict[str, Any] | None = None,
        truncated: bool = False,
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
            measured_localization = self._normalize_localization(localization)
            measured_result_tail = self._normalize_result_tail(result_tail)
            measured_invocation = self._normalize_invocation(invocation)
            measured_outcome = self._normalize_outcome(outcome, ok=ok)
            measured_miss_reasons = self._normalize_count_map(proof_cache_miss_reasons)
            measured_policy = str(idempotency_policy or "none").strip().lower()
            if measured_policy not in IDEMPOTENCY_POLICIES:
                measured_policy = "none"
            measured_key_source = str(idempotency_key_source or "none").strip().lower()
            if measured_key_source not in IDEMPOTENCY_KEY_SOURCES or not idempotency_key_present:
                measured_key_source = "none"
            measured_operation = str(idempotency_operation or tool).strip()[:120] or str(tool)[:120]
            measured_missing_reason = str(idempotency_missing_reason or "").strip()[:80]
            if measured_policy != "required" or idempotency_key_present:
                measured_missing_reason = ""
            measured_error_class = self._normalize_error_class(error_class) if not ok else ""
            recorded_wall_utc = utc_now()
            measured_started_wall = str(started_wall_utc or "").strip() or recorded_wall_utc
            measured_finished_wall = str(finished_wall_utc or "").strip() or recorded_wall_utc
            event = {
                "tool": tool,
                "started_at": measured_started_wall,
                "finished_at": measured_finished_wall,
                "wall_time_source": (
                    "operation_boundary"
                    if str(started_wall_utc or "").strip() and str(finished_wall_utc or "").strip()
                    else "record_time_fallback"
                ),
                "duration_ms": duration_ms,
                "wait_before_ms": wait_before_ms,
                "request_bytes": max(0, int(request_bytes)),
                "response_bytes": max(0, int(response_bytes)),
                "model_visible_bytes": max(0, int(model_visible_bytes)),
                "invocation": measured_invocation,
                "outcome": measured_outcome,
                "truncated": bool(truncated),
                "cache_hit": bool(cache_hit),
                "deduplicated": bool(deduplicated),
                "idempotency_eligible": bool(idempotency_eligible),
                "idempotency_key_present": bool(idempotency_key_present),
                "idempotency_policy": measured_policy,
                "idempotency_key_source": measured_key_source,
                "idempotency_operation": measured_operation,
                "idempotency_missing_reason": measured_missing_reason,
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
                "localization": measured_localization,
                "result_tail": measured_result_tail,
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
                state["idempotency_current_policy_required_calls"] += 1
                state["idempotency_current_policy_required_key_calls"] += 1 if idempotency_key_present else 0
                bucket = state["idempotency_current_policy_by_operation"].setdefault(
                    measured_operation,
                    {"calls": 0, "keyed": 0, "missing": 0, "missing_reasons": {}},
                )
                bucket["calls"] += 1
                bucket["keyed"] += 1 if idempotency_key_present else 0
                bucket["missing"] += 0 if idempotency_key_present else 1
                if measured_missing_reason:
                    reasons = bucket["missing_reasons"]
                    reasons[measured_missing_reason] = int(reasons.get(measured_missing_reason, 0)) + 1
            elif measured_policy == "optional":
                state["idempotency_optional_calls"] += 1
                state["idempotency_optional_key_calls"] += 1 if idempotency_key_present else 0
            if measured_key_source == "derived":
                state["idempotency_auto_key_calls"] += 1
            if measured_error_class:
                state["error_class_counts"][measured_error_class] = int(state["error_class_counts"].get(measured_error_class, 0)) + 1
                state["error_taxonomy_current_counts"][measured_error_class] = int(
                    state["error_taxonomy_current_counts"].get(measured_error_class, 0)
                ) + 1
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
            if measured_localization:
                state["localization_samples"] += 1
                state["localization_queries"] += measured_localization["query_count"]
                state["lsp_available_samples"] += 1 if measured_localization["semantic_available"] else 0
                state["lsp_attempted_queries"] += measured_localization["semantic_attempted"]
                state["lsp_handled_queries"] += measured_localization["semantic_handled"]
                state["fallback_search_queries"] += measured_localization["text_fallback_queries"]
            if measured_result_tail:
                state["result_tail_samples"] += 1
                state["result_tail_source_bytes"] += measured_result_tail["source_total_bytes"]
                state["result_tail_page_bytes"] += measured_result_tail["page_output_bytes"]
                state["result_tail_remaining_bytes"] += measured_result_tail["remaining_bytes"]
                state["result_truncated_calls"] += 1 if measured_result_tail["truncated"] else 0
                state["result_continuation_offered"] += 1 if measured_result_tail["continuation_offered"] else 0
                state["result_continuation_reads"] += 1 if measured_result_tail["continuation_read"] else 0
                state["result_continuation_rereads"] += 1 if measured_result_tail["continuation_reread"] else 0
                state["result_continuation_stale"] += 1 if measured_result_tail["continuation_stale"] else 0
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
                    "localization_samples": 0,
                    "localization_queries": 0,
                    "lsp_available_samples": 0,
                    "lsp_attempted_queries": 0,
                    "lsp_handled_queries": 0,
                    "fallback_search_queries": 0,
                    "result_tail_samples": 0,
                    "result_tail_source_bytes": 0,
                    "result_tail_page_bytes": 0,
                    "result_tail_remaining_bytes": 0,
                    "result_truncated_calls": 0,
                    "result_continuation_offered": 0,
                    "result_continuation_reads": 0,
                    "result_continuation_rereads": 0,
                    "result_continuation_stale": 0,
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
                if measured_localization:
                    metric["localization_samples"] += 1
                    metric["localization_queries"] += measured_localization["query_count"]
                    metric["lsp_available_samples"] += 1 if measured_localization["semantic_available"] else 0
                    metric["lsp_attempted_queries"] += measured_localization["semantic_attempted"]
                    metric["lsp_handled_queries"] += measured_localization["semantic_handled"]
                    metric["fallback_search_queries"] += measured_localization["text_fallback_queries"]
                if measured_result_tail:
                    metric["result_tail_samples"] += 1
                    metric["result_tail_source_bytes"] += measured_result_tail["source_total_bytes"]
                    metric["result_tail_page_bytes"] += measured_result_tail["page_output_bytes"]
                    metric["result_tail_remaining_bytes"] += measured_result_tail["remaining_bytes"]
                    metric["result_truncated_calls"] += 1 if measured_result_tail["truncated"] else 0
                    metric["result_continuation_offered"] += 1 if measured_result_tail["continuation_offered"] else 0
                    metric["result_continuation_reads"] += 1 if measured_result_tail["continuation_read"] else 0
                    metric["result_continuation_rereads"] += 1 if measured_result_tail["continuation_reread"] else 0
                    metric["result_continuation_stale"] += 1 if measured_result_tail["continuation_stale"] else 0
                metric["last_finished_at"] = event["finished_at"]
                for bucket_name, value in (
                    ("execution_mode_counts", execution_mode),
                    ("route_resolved_counts", route_resolved),
                ):
                    if value:
                        bucket = metric[bucket_name]
                        bucket[value] = int(bucket.get(value, 0)) + 1
            state["recent"] = (state.get("recent", []) + [event])[-MAX_RECENT:]
            start_hour = self._hour_of(event["started_at"])
            if start_hour is not None:
                bucket = state["hourly_metrics"].setdefault(start_hour, {
                    "hour": start_hour,
                    "tool_calls": 0,
                    "errors": 0,
                    "cache_hits": 0,
                    "request_bytes": 0,
                    "response_bytes": 0,
                    "model_visible_bytes": 0,
                    "local_execution_ms": 0,
                    "estimated_wait_ms": 0,
                    "last_finished_at": "",
                })
                bucket["tool_calls"] += 1
                bucket["errors"] += 0 if ok else 1
                bucket["cache_hits"] += 1 if cache_hit else 0
                bucket["request_bytes"] += event["request_bytes"]
                bucket["response_bytes"] += event["response_bytes"]
                bucket["model_visible_bytes"] += event["model_visible_bytes"]
                bucket["local_execution_ms"] += duration_ms
                bucket["estimated_wait_ms"] += wait_before_ms
                bucket["last_finished_at"] = event["finished_at"]
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
            "version": 6,
            "tool_calls": 0,
            "errors": 0,
            "cache_hits": 0,
            "deduplicated_calls": 0,
            "idempotency_eligible_calls": 0,
            "idempotency_eligible_key_calls": 0,
            "idempotency_key_calls": 0,
            "idempotency_required_calls": 0,
            "idempotency_required_key_calls": 0,
            "idempotency_policy_epoch": IDEMPOTENCY_POLICY_EPOCH,
            "idempotency_current_policy_required_calls": 0,
            "idempotency_current_policy_required_key_calls": 0,
            "idempotency_current_policy_by_operation": {},
            "idempotency_optional_calls": 0,
            "idempotency_optional_key_calls": 0,
            "idempotency_auto_key_calls": 0,
            "error_class_counts": {},
            "error_taxonomy_epoch": ERROR_TAXONOMY_EPOCH,
            "error_taxonomy_current_counts": {},
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
            "localization_samples": 0,
            "localization_queries": 0,
            "lsp_available_samples": 0,
            "lsp_attempted_queries": 0,
            "lsp_handled_queries": 0,
            "fallback_search_queries": 0,
            "result_tail_samples": 0,
            "result_tail_source_bytes": 0,
            "result_tail_page_bytes": 0,
            "result_tail_remaining_bytes": 0,
            "result_truncated_calls": 0,
            "result_continuation_offered": 0,
            "result_continuation_reads": 0,
            "result_continuation_rereads": 0,
            "result_continuation_stale": 0,
            "execution_mode_counts": {},
            "route_resolved_counts": {},
            "orchestration_state_counts": {},
            "run_metrics": {},
            "last_finished_at": None,
            "recent": [],
            "hourly_metrics": {},
        }

    def _read(self) -> dict[str, Any]:
        state = self._default()
        try:
            parsed = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return state
        stored_policy_epoch = str(parsed.get("idempotency_policy_epoch") or "") if isinstance(parsed, dict) else ""
        stored_taxonomy_epoch = str(parsed.get("error_taxonomy_epoch") or "") if isinstance(parsed, dict) else ""
        if isinstance(parsed, dict):
            state.update(parsed)
        state["version"] = self.schema_version
        if stored_policy_epoch != IDEMPOTENCY_POLICY_EPOCH:
            state["idempotency_current_policy_required_calls"] = 0
            state["idempotency_current_policy_required_key_calls"] = 0
            state["idempotency_current_policy_by_operation"] = {}
        state["idempotency_policy_epoch"] = IDEMPOTENCY_POLICY_EPOCH
        if stored_taxonomy_epoch != ERROR_TAXONOMY_EPOCH:
            state["error_taxonomy_current_counts"] = {}
        state["error_taxonomy_epoch"] = ERROR_TAXONOMY_EPOCH
        if not isinstance(state.get("recent"), list):
            state["recent"] = []
        state["hourly_metrics"] = self._normalize_hourly_metrics(state.get("hourly_metrics"))
        for key in ("execution_mode_counts", "route_resolved_counts", "orchestration_state_counts", "run_metrics", "proof_cache_miss_reasons", "error_class_counts", "error_taxonomy_current_counts", "idempotency_current_policy_by_operation"):
            if not isinstance(state.get(key), dict):
                state[key] = {}
        if not isinstance(state.get("phase_timing_ms"), dict):
            state["phase_timing_ms"] = {}
        for key in (
            "idempotency_key_calls", "idempotency_eligible_calls", "idempotency_eligible_key_calls",
            "idempotency_required_calls", "idempotency_required_key_calls",
            "idempotency_current_policy_required_calls", "idempotency_current_policy_required_key_calls",
            "idempotency_optional_calls", "idempotency_optional_key_calls", "idempotency_auto_key_calls",
            "proof_cache_eligible", "proof_cache_hits", "proof_cache_misses", "proof_cache_saved_ms",
            "model_visible_bytes", "phase_timing_samples", "localization_samples", "localization_queries",
            "lsp_available_samples", "lsp_attempted_queries", "lsp_handled_queries", "fallback_search_queries",
            "result_tail_samples", "result_tail_source_bytes", "result_tail_page_bytes", "result_tail_remaining_bytes",
            "result_truncated_calls", "result_continuation_offered", "result_continuation_reads",
            "result_continuation_rereads", "result_continuation_stale",
        ):
            try:
                state[key] = max(0, int(state.get(key, 0)))
            except (TypeError, ValueError):
                state[key] = 0
        state["proof_cache_miss_reasons"] = self._normalize_count_map(state["proof_cache_miss_reasons"])
        state["error_class_counts"] = self._normalize_count_map(state["error_class_counts"])
        state["error_taxonomy_current_counts"] = self._normalize_count_map(state["error_taxonomy_current_counts"])
        normalized_operations: dict[str, dict[str, Any]] = {}
        for raw_operation, raw_bucket in list(state["idempotency_current_policy_by_operation"].items())[:50]:
            operation = str(raw_operation or "").strip()[:120]
            if not operation or not isinstance(raw_bucket, dict):
                continue
            try:
                calls = max(0, int(raw_bucket.get("calls", 0) or 0))
                keyed = min(calls, max(0, int(raw_bucket.get("keyed", 0) or 0)))
                missing = min(calls, max(0, int(raw_bucket.get("missing", calls - keyed) or 0)))
            except (TypeError, ValueError):
                continue
            normalized_operations[operation] = {
                "calls": calls,
                "keyed": keyed,
                "missing": missing,
                "missing_reasons": self._normalize_count_map(raw_bucket.get("missing_reasons")),
            }
        state["idempotency_current_policy_by_operation"] = normalized_operations
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
            metric.setdefault("localization_samples", 0)
            metric.setdefault("localization_queries", 0)
            metric.setdefault("lsp_available_samples", 0)
            metric.setdefault("lsp_attempted_queries", 0)
            metric.setdefault("lsp_handled_queries", 0)
            metric.setdefault("fallback_search_queries", 0)
            metric.setdefault("result_tail_samples", 0)
            metric.setdefault("result_tail_source_bytes", 0)
            metric.setdefault("result_tail_page_bytes", 0)
            metric.setdefault("result_tail_remaining_bytes", 0)
            metric.setdefault("result_truncated_calls", 0)
            metric.setdefault("result_continuation_offered", 0)
            metric.setdefault("result_continuation_reads", 0)
            metric.setdefault("result_continuation_rereads", 0)
            metric.setdefault("result_continuation_stale", 0)
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
    def _hour_of(iso: str) -> int | None:
        if not isinstance(iso, str) or not iso.strip():
            return None
        try:
            parsed = datetime.fromisoformat(iso.strip().replace("Z", "+00:00"))
        except ValueError:
            return None
        return int(parsed.timestamp() // 3600)

    @staticmethod
    def _normalize_hourly_metrics(value: dict[str, Any] | None) -> dict[int, dict[str, Any]]:
        if not isinstance(value, dict):
            return {}
        now_hour = int(time.time() // 3600)
        lower_bound = now_hour - (MAX_HOURLY_BUCKETS - 1)
        upper_bound = now_hour + 1
        result: dict[int, dict[str, Any]] = {}
        for raw_hour, raw_bucket in list(value.items())[:MAX_HOURLY_BUCKETS * 2]:
            try:
                hour = int(raw_hour)
            except (TypeError, ValueError):
                continue
            if hour < lower_bound or hour > upper_bound:
                continue
            if not isinstance(raw_bucket, dict):
                continue
            bucket: dict[str, Any] = {
                "hour": hour,
                "tool_calls": 0,
                "errors": 0,
                "cache_hits": 0,
                "request_bytes": 0,
                "response_bytes": 0,
                "model_visible_bytes": 0,
                "local_execution_ms": 0,
                "estimated_wait_ms": 0,
                "last_finished_at": "",
            }
            for key in (
                "tool_calls", "errors", "cache_hits", "request_bytes",
                "response_bytes", "model_visible_bytes", "local_execution_ms",
                "estimated_wait_ms",
            ):
                try:
                    bucket[key] = max(0, int(raw_bucket.get(key, 0) or 0))
                except (TypeError, ValueError):
                    bucket[key] = 0
            bucket["hour"] = hour
            last_finished = str(raw_bucket.get("last_finished_at") or "").strip()[:40]
            bucket["last_finished_at"] = last_finished
            result[hour] = bucket
        return result

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
    def _normalize_invocation(value: dict[str, Any] | None) -> dict[str, Any]:
        if not isinstance(value, dict):
            return {}
        result: dict[str, Any] = {"schema_version": 1}
        for key, limit in (
            ("invocation_id", 128),
            ("identity_source", 64),
            ("request_id", 128),
            ("task_context_id", 128),
            ("task_id", 128),
            ("session_instance", 128),
            ("execution_context_id", 128),
            ("client_id", 64),
            ("client_type", 32),
            ("turn_id", 128),
        ):
            measured = str(value.get(key) or "").strip()[:limit]
            if measured:
                result[key] = measured
        trace = value.get("trace_context") if isinstance(value.get("trace_context"), dict) else {}
        normalized_trace: dict[str, Any] = {}
        for key, limit in (("trace_id", 128), ("parent_span_id", 128), ("trace_flags", 8)):
            measured = str(trace.get(key) or "").strip()[:limit]
            if measured:
                normalized_trace[key] = measured
        if trace:
            normalized_trace["trace_context_schema_version"] = 1
            normalized_trace["tracestate_present"] = bool(trace.get("tracestate_present"))
        if normalized_trace:
            result["trace_context"] = normalized_trace
        return result if result.get("invocation_id") else {}

    @staticmethod
    def _normalize_outcome(value: dict[str, Any] | None, *, ok: bool) -> dict[str, Any]:
        raw = value if isinstance(value, dict) else {}
        result: dict[str, Any] = {"status": "ok" if ok else "error"}
        if ok:
            return result
        error_code = str(raw.get("error_code") or "TOOL_ERROR").strip()[:128] or "TOOL_ERROR"
        error_category = str(raw.get("error_category") or "runtime").strip()[:64] or "runtime"
        result.update({
            "error_code": error_code,
            "error_category": error_category,
            "retryable": bool(raw.get("retryable", False)),
        })
        return result

    @staticmethod
    def _normalize_localization(value: dict[str, Any] | None) -> dict[str, Any]:
        if not isinstance(value, dict):
            return {}
        result = {
            "semantic_available": value.get("semantic_available") is True,
            "query_count": 0,
            "semantic_attempted": 0,
            "semantic_handled": 0,
            "text_fallback_queries": 0,
        }
        for key in ("query_count", "semantic_attempted", "semantic_handled", "text_fallback_queries"):
            raw = value.get(key)
            if isinstance(raw, bool):
                continue
            try:
                result[key] = max(0, int(raw or 0))
            except (TypeError, ValueError):
                result[key] = 0
        result["semantic_attempted"] = min(result["semantic_attempted"], result["query_count"])
        result["semantic_handled"] = min(result["semantic_handled"], result["semantic_attempted"])
        result["text_fallback_queries"] = min(result["text_fallback_queries"], result["query_count"])
        return result if result["query_count"] > 0 else {}

    @staticmethod
    def _normalize_result_tail(value: dict[str, Any] | None) -> dict[str, Any]:
        if not isinstance(value, dict) or not value:
            return {}
        result: dict[str, Any] = {}
        for key in ("source_total_bytes", "page_output_bytes", "remaining_bytes"):
            raw = value.get(key, 0)
            if isinstance(raw, bool):
                raw = 0
            try:
                result[key] = max(0, int(raw or 0))
            except (TypeError, ValueError):
                result[key] = 0
        for key in (
            "truncated", "continuation_offered", "continuation_read",
            "continuation_reread", "continuation_stale",
        ):
            result[key] = value.get(key) is True
        return result

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
