from __future__ import annotations

import hashlib
import time
from typing import Any

from .errors import ToolFailure
from .opencode_provider import ALLOWED_OPENCODE_MODELS, OpenCodeProviderError
from .orchestration_control import RunContext
from .provider_routing import recommendation_id, recommend_shadow_route
from .provider_telemetry import normalize_provider_telemetry
from .usage_events import usage_event_from_provider_delegation
from .usage_reservations import UsageReservationError, UsageReservationStore


HUB_PROVIDER_TELEMETRY_STATES = frozenset({"ROUTED", "EXECUTING", "PROVING", "ACCEPTING"})
USAGE_RESERVATION_TERMINAL_GRACE_MS = 120_000


class ProviderRuntimeMixin:
    def ingest_provider_telemetry(self, identity: dict[str, Any], value: Any) -> dict[str, Any]:
        client_id = str(identity.get("client_id") or "").strip()
        client_type = str(identity.get("client_type") or "").strip()
        if (client_id, client_type) != ("opencode", "opencode"):
            raise ToolFailure("PROVIDER_TELEMETRY_CLIENT_DENIED", "Only the allowlisted OpenCode worker may publish provider telemetry.", category="security", retryable=False)
        telemetry = normalize_provider_telemetry(value)
        self._touch_hub_client(identity)
        state = self.task_state.get()
        projection = state.get("orchestration") if isinstance(state.get("orchestration"), dict) else {}
        run_id = str(projection.get("run_id") or "").strip()
        wave_id = str(projection.get("wave_id") or "").strip()
        ctx = self.orchestration_control.snapshot(run_id) if run_id else None
        run = self.orchestration_ledger.get_run(run_id) if run_id else None
        if not ctx or not run or run.get("status") != "active" or not wave_id or ctx.wave_id != wave_id or ctx.state not in HUB_PROVIDER_TELEMETRY_STATES:
            raise ToolFailure(
                "PROVIDER_TELEMETRY_CONTEXT_UNAVAILABLE",
                "Provider telemetry is not bound to a current active task-projected orchestration wave.",
                category="runtime",
                retryable=True,
                details={"run_id": run_id, "wave_id": wave_id, "state": ctx.state if ctx else ""},
            )
        provider_id = telemetry["provider_id"]
        model_id = telemetry["model_id"]
        model = model_id if "/" in model_id else f"{provider_id}/{model_id}"
        dispatch: dict[str, Any] | None = None
        provider_dispatch_id = str(telemetry.get("provider_dispatch_id") or "").strip()
        provider_delegation_id = str(telemetry.get("provider_delegation_id") or "").strip()
        if bool(provider_dispatch_id) != bool(provider_delegation_id):
            raise ToolFailure("PROVIDER_TELEMETRY_CORRELATION_INVALID", "Provider telemetry correlation identifiers must be supplied together.", category="validation", retryable=False)
        if provider_dispatch_id:
            try:
                dispatch = self._opencode_provider.observe(provider_dispatch_id)
            except OpenCodeProviderError:
                existing = self.orchestration_ledger.get_delegation(provider_delegation_id)
                metadata = (existing or {}).get("metadata") or {}
                if not existing or str(metadata.get("provider_dispatch_id") or "") != provider_dispatch_id:
                    raise ToolFailure("PROVIDER_TELEMETRY_CORRELATION_UNKNOWN", "Provider telemetry does not map to a known provider dispatch.", category="runtime", retryable=True)
                dispatch = {
                    "dispatch_id": provider_dispatch_id,
                    "delegation_id": provider_delegation_id,
                    "run_id": run_id,
                    "wave_id": str(existing.get("wave_id") or ""),
                    "model": str(existing.get("model") or ""),
                }
            if (
                str(dispatch.get("delegation_id") or "") != provider_delegation_id
                or str(dispatch.get("run_id") or "") != run_id
                or str(dispatch.get("wave_id") or "") != wave_id
                or str(dispatch.get("model") or "") != model
            ):
                raise ToolFailure("PROVIDER_TELEMETRY_CORRELATION_MISMATCH", "Provider telemetry correlation does not match the active run, wave, delegation, or model.", category="security", retryable=False)
        else:
            dispatch = self._opencode_provider.find_by_session(run_id=run_id, wave_id=wave_id, model=model, session_id=telemetry["session_id"])
            if dispatch is None and str(ctx.route_resolved or "").strip().lower() not in {"opencode", model.lower()}:
                raise ToolFailure(
                    "PROVIDER_TELEMETRY_ATTRIBUTION_UNAVAILABLE",
                    "Uncorrelated OpenCode telemetry may only attach to a wave explicitly routed to OpenCode.",
                    category="runtime",
                    retryable=True,
                    details={"run_id": run_id, "wave_id": wave_id, "route_resolved": ctx.route_resolved},
                )
        delegation_id = str((dispatch or {}).get("delegation_id") or "") or "opencode-" + hashlib.sha256(f"{run_id}\0{telemetry['session_id']}\0{telemetry['message_id']}".encode("utf-8")).hexdigest()[:40]
        usage_reservation_id = ""
        if dispatch is not None:
            existing_delegation = self.orchestration_ledger.get_delegation(delegation_id)
            existing_metadata = (existing_delegation or {}).get("metadata") or {}
            usage_reservation_id = str(existing_metadata.get("usage_reservation_id") or "").strip()
            if not usage_reservation_id:
                usage_reservation_id = self._provider_traffic_key(
                    run_id=run_id,
                    wave_id=wave_id,
                    model=model,
                    request_id=str(dispatch.get("request_id") or ""),
                    prompt_sha256=str(dispatch.get("prompt_sha256") or ""),
                )
            try:
                self._usage_reservation_store().require(
                    run_id=run_id,
                    wave_id=wave_id,
                    reservation_id=usage_reservation_id,
                    provider_model=model,
                    allowed_statuses=("reserved", "indeterminate", "reconciled"),
                    allow_expired=True,
                )
            except UsageReservationError as exc:
                raise self._usage_reservation_failure(exc) from exc
        economics = {
            "input_tokens": telemetry["input_tokens"],
            "cached_input_tokens": telemetry["cache_read_tokens"],
            "output_tokens": telemetry["output_tokens"],
            "reasoning_output_tokens": telemetry["reasoning_output_tokens"],
            "cache_read_tokens": telemetry["cache_read_tokens"],
            "cache_write_tokens": telemetry["cache_write_tokens"],
            "provider_cost": telemetry["provider_cost"],
            "measured": True,
            "source": "opencode",
        }
        message_economics = {
            telemetry["message_id"]: {
                "input_tokens": telemetry["input_tokens"],
                "cached_input_tokens": telemetry["cache_read_tokens"],
                "output_tokens": telemetry["output_tokens"],
                "reasoning_output_tokens": telemetry["reasoning_output_tokens"],
                "cache_read_tokens": telemetry["cache_read_tokens"],
                "cache_write_tokens": telemetry["cache_write_tokens"],
                "provider_cost": telemetry["provider_cost"],
                **({"duration_ms": telemetry["duration_ms"]} if "duration_ms" in telemetry else {}),
            }
        }
        metadata: dict[str, Any] = {
            "source": "opencode:message.updated",
            "provider_id": provider_id,
            "model_id": model_id,
            "session_id": telemetry["session_id"],
            "message_id": telemetry["message_id"],
            "provider_started_at_ms": telemetry["started_at_ms"],
            "provider_cost": telemetry["provider_cost"],
            "economics": economics,
            "message_economics": message_economics,
            "provider_message_status": telemetry["status"],
            "attribution": "correlated_dispatch" if dispatch else "task_projected_opencode_route",
        }
        for key in ("completed_at_ms", "duration_ms", "finish", "error_name"):
            if key in telemetry:
                metadata["provider_completed_at_ms" if key == "completed_at_ms" else key] = telemetry[key]
        if dispatch:
            metadata["provider_dispatch_id"] = str(dispatch.get("dispatch_id") or "")
            metadata["usage_reservation_id"] = usage_reservation_id
            metadata["side_effect_class"] = "read_only"
            metadata["read_only_enforced"] = True
        intermediate_tool_calls = bool(dispatch) and telemetry["status"] == "completed" and str(telemetry.get("finish") or "").strip().lower() == "tool-calls"
        delegation_status = "active" if intermediate_tool_calls else telemetry["status"]
        projected = self.orchestration_ledger.upsert_external_delegation(
            delegation_id=delegation_id,
            wave_id=wave_id,
            authority_owner="opencode",
            route_requested="opencode",
            route_resolved=model,
            model=model,
            status=delegation_status,
            metadata=metadata,
        )
        delegation = projected["delegation"]
        usage_event = None
        if projected["changed"]:
            event_type = "external_delegation_finished" if projected["terminal_transition"] else "external_delegation_started" if projected["created"] else "external_delegation_updated"
            self.orchestration_ledger.append_event(
                run_id,
                wave_id=wave_id,
                delegation_id=delegation_id,
                event_type=event_type,
                state_before=ctx.state,
                state_after=ctx.state,
                payload={"source": "opencode:message.updated", "provider_id": provider_id, "model": model, "session_id": telemetry["session_id"], "message_id": telemetry["message_id"], "provider_message_status": telemetry["status"], "finish": telemetry.get("finish") or "", "status": delegation["status"], "economics": economics},
            )
        if delegation_status in {"completed", "failed"}:
            usage_event = usage_event_from_provider_delegation(
                run_id=run_id,
                wave_id=wave_id,
                delegation=delegation,
                source="opencode:provider_dispatch" if dispatch else "opencode:message.updated",
            )
            if usage_event is not None:
                self.orchestration_ledger.record_usage_event(
                    run_id=run_id,
                    wave_id=wave_id,
                    delegation_id=delegation_id,
                    usage_event=usage_event,
                )
                if dispatch is not None and str((usage_event.get("measurement") or {}).get("usage") or "") == "measured":
                    total_tokens = (usage_event.get("usage") or {}).get("total_tokens")
                    if isinstance(total_tokens, bool) or not isinstance(total_tokens, int) or total_tokens < 0:
                        raise ToolFailure("USAGE_RESERVATION_ACTUAL_INVALID", "Measured UsageEvent total_tokens is invalid for reconciliation.", category="runtime", retryable=False)
                    try:
                        self._usage_reservation_store().reconcile(
                            run_id=run_id,
                            wave_id=wave_id,
                            reservation_id=usage_reservation_id,
                            provider_model=model,
                            actual_units=total_tokens,
                            usage_id=str(usage_event.get("usage_id") or ""),
                        )
                    except UsageReservationError as exc:
                        raise self._usage_reservation_failure(exc) from exc
        return {"run_id": run_id, "wave_id": wave_id, "delegation_id": delegation_id, "changed": bool(projected["changed"]), "created": bool(projected["created"]), "delegation": delegation, "usage_event": usage_event}

    def _require_provider_supervisor(self, identity: dict[str, Any]) -> None:
        if (str(identity.get("client_id") or ""), str(identity.get("client_type") or "")) != ("electron-panel", "electron"):
            raise ToolFailure("PROVIDER_DISPATCH_CLIENT_DENIED", "Provider dispatch lifecycle is restricted to the Electron supervisor.", category="security", retryable=False)
        self._touch_hub_client(identity)

    def _provider_context(self) -> tuple[str, str, RunContext]:
        state = self.task_state.get()
        projection = state.get("orchestration") if isinstance(state.get("orchestration"), dict) else {}
        run_id = str(projection.get("run_id") or "").strip()
        wave_id = str(projection.get("wave_id") or "").strip()
        ctx = self.orchestration_control.snapshot(run_id) if run_id else None
        run = self.orchestration_ledger.get_run(run_id) if run_id else None
        if not ctx or not run or run.get("status") != "active" or not wave_id or ctx.wave_id != wave_id or ctx.state not in HUB_PROVIDER_TELEMETRY_STATES:
            raise ToolFailure("PROVIDER_DISPATCH_CONTEXT_UNAVAILABLE", "Provider dispatch requires the current active task-projected orchestration wave.", category="runtime", retryable=True)
        return run_id, wave_id, ctx

    @staticmethod
    def _provider_traffic_key(*, run_id: str, wave_id: str, model: str, request_id: str = "", prompt_sha256: str = "") -> str:
        identity = str(request_id or prompt_sha256 or "").strip()
        if not identity:
            return ""
        return hashlib.sha256(f"{run_id}\0{wave_id}\0{model}\0{identity}".encode("utf-8")).hexdigest()

    def _usage_reservation_store(self) -> UsageReservationStore:
        return UsageReservationStore(self.orchestration_ledger)

    @staticmethod
    def _usage_reservation_failure(exc: UsageReservationError) -> ToolFailure:
        return ToolFailure(exc.code, str(exc), category="runtime", retryable=False)

    def provider_traffic_snapshot(self) -> dict[str, Any]:
        capacity_fn = getattr(self._opencode_provider, "capacity_status", None)
        opencode_capacity = capacity_fn() if callable(capacity_fn) else {
            "provider_id": "opencode-go",
            "active_requests": int(self._opencode_provider.active_count()),
            "retained_dispatches": None,
            "retained_limit": None,
            "models": sorted(ALLOWED_OPENCODE_MODELS),
            "read_only_enforced": True,
        }
        return {
            "schema_version": 1,
            "policy": self.provider_traffic.snapshot(models=ALLOWED_OPENCODE_MODELS),
            "capacity": {
                "opencode": opencode_capacity,
                "codex": {"capacity_cooldowns": self._codex_bridge.capacity_status()},
            },
            "automatic_routing": {"enabled": False, "mode": "evidence_gated", "reason": "representative_accepted_cohorts_required"},
        }

    def _shadow_route_context(self) -> tuple[str, str, RunContext]:
        state = self.task_state.get()
        projection = state.get("orchestration") if isinstance(state.get("orchestration"), dict) else {}
        run_id = str(projection.get("run_id") or "").strip()
        wave_id = str(projection.get("wave_id") or "").strip()
        ctx = self.orchestration_control.snapshot(run_id) if run_id else None
        run = self.orchestration_ledger.get_run(run_id) if run_id else None
        allowed_states = {"PREFLIGHT", "READY", "ROUTED", "EXECUTING", "PROVING", "ACCEPTING"}
        if not ctx or not run or run.get("status") != "active" or not wave_id or ctx.wave_id != wave_id or ctx.state not in allowed_states:
            raise ToolFailure("SHADOW_ROUTE_CONTEXT_UNAVAILABLE", "Shadow routing requires the current active task-projected nonterminal orchestration wave.", category="runtime", retryable=True)
        return run_id, wave_id, ctx

    def shadow_route(self, identity: dict[str, Any], features: Any) -> dict[str, Any]:
        self._require_provider_supervisor(identity)
        run_id, wave_id, ctx = self._shadow_route_context()
        try:
            recommendation = recommend_shadow_route(features)
        except ValueError as exc:
            raise ToolFailure("SHADOW_ROUTE_INVALID", str(exc), category="validation", retryable=False) from exc
        recommendation["run_id"] = run_id
        recommendation["wave_id"] = wave_id
        recommendation["recommendation_id"] = recommendation_id(
            run_id=run_id,
            wave_id=wave_id,
            recommendation=recommendation,
        )
        recorded = self.orchestration_ledger.record_shadow_route(
            run_id=run_id,
            wave_id=wave_id,
            recommendation=recommendation,
        )
        return {
            "run_id": run_id,
            "wave_id": wave_id,
            "orchestration_state": ctx.state,
            "recommendation": recommendation,
            "recorded": recorded["recorded"],
            "routing_evidence": self.orchestration_ledger.routing_evidence(run_id),
        }

    def _sync_opencode_dispatch(self, snapshot: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
        provider_status = str(snapshot.get("status") or "")
        reservation_id = self._provider_traffic_key(
            run_id=str(snapshot.get("run_id") or ""),
            wave_id=str(snapshot.get("wave_id") or ""),
            model=str(snapshot.get("model") or ""),
            request_id=str(snapshot.get("request_id") or ""),
            prompt_sha256=str(snapshot.get("prompt_sha256") or ""),
        )
        try:
            if provider_status == "running":
                self._usage_reservation_store().require(
                    run_id=ctx.run_id,
                    wave_id=ctx.wave_id,
                    reservation_id=reservation_id,
                    provider_model=str(snapshot.get("model") or ""),
                )
            else:
                self._usage_reservation_store().mark_indeterminate(
                    run_id=ctx.run_id,
                    wave_id=ctx.wave_id,
                    reservation_id=reservation_id,
                    provider_model=str(snapshot.get("model") or ""),
                    reason="provider_terminal_without_exact_usage",
                )
        except UsageReservationError as exc:
            raise self._usage_reservation_failure(exc) from exc
        if provider_status != "running":
            self.provider_traffic.complete(self._provider_traffic_key(
                run_id=str(snapshot.get("run_id") or ""),
                wave_id=str(snapshot.get("wave_id") or ""),
                model=str(snapshot.get("model") or ""),
                request_id=str(snapshot.get("request_id") or ""),
                prompt_sha256=str(snapshot.get("prompt_sha256") or ""),
            ))
        delegation_status = "active" if provider_status == "running" else "completed" if provider_status == "completed" else "failed"
        metadata = {
            "source": "opencode:provider_adapter",
            "provider_dispatch_id": snapshot["dispatch_id"],
            "usage_reservation_id": reservation_id,
            "session_id": snapshot.get("session_id") or "",
            "side_effect_class": "read_only",
            "read_only_enforced": True,
            "prompt_sha256": snapshot["prompt_sha256"],
            "prompt_bytes": snapshot["prompt_bytes"],
            "result_chars": snapshot.get("result_chars", 0),
            "output_truncated": bool(snapshot.get("output_truncated")),
            "error_class": snapshot.get("error_class"),
            "lifecycle_evidence": snapshot.get("lifecycle_evidence") or {},
            "timing": snapshot.get("timing") or {},
        }
        projected = self.orchestration_ledger.upsert_external_delegation(
            delegation_id=str(snapshot["delegation_id"]),
            wave_id=str(snapshot["wave_id"]),
            authority_owner="opencode",
            route_requested="opencode_read_only",
            route_resolved=str(snapshot["model"]),
            model=str(snapshot["model"]),
            status=delegation_status,
            metadata=metadata,
        )
        if projected["changed"]:
            event_type = "external_delegation_finished" if projected["terminal_transition"] else "external_delegation_started" if projected["created"] else "external_delegation_updated"
            self.orchestration_ledger.append_event(
                ctx.run_id,
                wave_id=ctx.wave_id,
                delegation_id=str(snapshot["delegation_id"]),
                event_type=event_type,
                state_before=ctx.state,
                state_after=ctx.state,
                payload={
                    "source": "opencode:provider_adapter",
                    "provider_dispatch_id": snapshot["dispatch_id"],
                    "model": snapshot["model"],
                    "status": delegation_status,
                    "side_effect_class": "read_only",
                    "read_only_enforced": True,
                    "prompt_sha256": snapshot["prompt_sha256"],
                    "prompt_bytes": snapshot["prompt_bytes"],
                    "error_class": snapshot.get("error_class"),
                    "timing": snapshot.get("timing") or {},
                },
            )
        delegation = projected["delegation"]
        if delegation["status"] in {"completed", "failed"}:
            usage_event = usage_event_from_provider_delegation(
                run_id=ctx.run_id,
                wave_id=ctx.wave_id,
                delegation=delegation,
                source="opencode:provider_dispatch",
                total_ms=(snapshot.get("timing") or {}).get("total_ms"),
            )
            if usage_event is not None:
                self.orchestration_ledger.record_usage_event(
                    run_id=ctx.run_id,
                    wave_id=ctx.wave_id,
                    delegation_id=str(snapshot["delegation_id"]),
                    usage_event=usage_event,
                )
        return delegation

    def _on_opencode_provider_terminal(self, snapshot: dict[str, Any]) -> None:
        ctx = self.orchestration_control.snapshot(str(snapshot.get("run_id") or ""))
        if ctx is None or ctx.wave_id != str(snapshot.get("wave_id") or ""):
            return
        try:
            self._sync_opencode_dispatch(snapshot, ctx)
        except (OSError, RuntimeError, ValueError, ToolFailure):
            return

    def dispatch_opencode_provider(self, identity: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
        self._require_provider_supervisor(identity)
        run_id, wave_id, ctx = self._provider_context()
        model = str(payload.get("model") or "").strip()
        if model not in ALLOWED_OPENCODE_MODELS:
            raise ToolFailure("PROVIDER_MODEL_DENIED", "Only the allowlisted OpenCode Go Flash/Pro models may be dispatched.", category="validation", retryable=False)
        prompt = str(payload.get("prompt") or "")
        request_id = str(payload.get("request_id") or "").strip()[:128]
        traffic_key = self._provider_traffic_key(
            run_id=run_id,
            wave_id=wave_id,
            model=model,
            request_id=request_id,
            prompt_sha256=hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        )
        raw_token_budget = payload.get("token_budget")
        if raw_token_budget is None:
            raise ToolFailure("PROVIDER_USAGE_RESERVATION_REQUIRED", "Provider dispatch requires an explicit token_budget reservation authority.", category="validation", retryable=False)
        if isinstance(raw_token_budget, bool) or not isinstance(raw_token_budget, int) or raw_token_budget <= 0:
            raise ToolFailure("PROVIDER_TOKEN_BUDGET_INVALID", "token_budget must be a positive integer.", category="validation", retryable=False)
        admission = self.provider_traffic.admit(model, traffic_key, token_budget=raw_token_budget)
        if not admission.get("allowed"):
            raise ToolFailure(
                "PROVIDER_ADMISSION_DENIED",
                f"Provider admission denied: {admission.get('reason')}",
                category="runtime",
                retryable=admission.get("reason") in {"concurrency_exhausted", "rpm_exhausted", "tpm_exhausted"},
                details=admission,
            )
        timeout_ms = int(payload.get("timeout_ms") or 60_000)
        try:
            durable_reservation = self._usage_reservation_store().reserve(
                run_id=run_id,
                wave_id=wave_id,
                reservation_id=traffic_key,
                request_id=request_id or traffic_key,
                provider_model=model,
                reserved_units=raw_token_budget,
                expires_at_unix_ms=int(time.time() * 1000) + timeout_ms + USAGE_RESERVATION_TERMINAL_GRACE_MS,
            )
        except UsageReservationError as exc:
            if not admission.get("deduplicated"):
                self.provider_traffic.abort(traffic_key)
            raise self._usage_reservation_failure(exc) from exc
        try:
            snapshot = self._opencode_provider.start(
                run_id=run_id,
                wave_id=wave_id,
                model=model,
                prompt=prompt,
                timeout_ms=timeout_ms,
                request_id=request_id,
            )
        except OpenCodeProviderError as exc:
            if not admission.get("deduplicated"):
                self.provider_traffic.abort(traffic_key)
            if durable_reservation.get("changed"):
                try:
                    self._usage_reservation_store().abort(
                        run_id=run_id,
                        wave_id=wave_id,
                        reservation_id=traffic_key,
                        provider_model=model,
                        reason="provider_start_failed",
                    )
                except UsageReservationError:
                    pass
            raise ToolFailure(exc.code, exc.message, category="runtime", retryable=exc.retryable, details=exc.details) from exc
        delegation = self._sync_opencode_dispatch(snapshot, ctx)
        return {"run_id": run_id, "wave_id": wave_id, "dispatch": snapshot, "delegation": delegation, "admission": admission}

    def observe_opencode_provider(self, identity: dict[str, Any], dispatch_id: str, *, cancel: bool = False) -> dict[str, Any]:
        self._require_provider_supervisor(identity)
        try:
            snapshot = self._opencode_provider.cancel(dispatch_id) if cancel else self._opencode_provider.observe(dispatch_id)
        except OpenCodeProviderError as exc:
            raise ToolFailure(exc.code, exc.message, category="runtime", retryable=exc.retryable, details=exc.details) from exc
        ctx = self.orchestration_control.snapshot(str(snapshot.get("run_id") or ""))
        if ctx is None or ctx.wave_id != str(snapshot.get("wave_id") or ""):
            raise ToolFailure("PROVIDER_DISPATCH_CONTEXT_UNAVAILABLE", "Provider dispatch no longer maps to a known orchestration wave.", category="runtime", retryable=False)
        delegation = self._sync_opencode_dispatch(snapshot, ctx)
        return {"run_id": ctx.run_id, "wave_id": ctx.wave_id, "dispatch": snapshot, "delegation": delegation}

