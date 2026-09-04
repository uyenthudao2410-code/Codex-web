from __future__ import annotations

import time
from typing import Any

from .errors import ToolFailure
from .usage_events import usage_event_from_controller_report, validate_controller_usage_report


CONTROLLER_USAGE_META_KEY = "io.coding-tools/controllerUsage"
CONTROLLER_USAGE_STATUS_META_KEY = "io.coding-tools/controllerUsageStatus"
_TRUSTED_CONTROLLER_USAGE_IDENTITY_SOURCES = frozenset({"explicit_headers", "attested_transport"})
_DEFERRED_AGENT_WORKFLOW_BINDING_KEY = "_deferred_agent_workflow_binding"
_SERVER_OWNED_HOST_CORRELATION_SOURCES = frozenset({
    "electron_pending_host_turn",
    "attested_chatweb_transport_trace",
})


def tool_call_name(request: dict[str, Any]) -> str:
    if request.get("method") != "tools/call":
        return ""
    params = request.get("params") if isinstance(request.get("params"), dict) else {}
    return str(params.get("name") or "").strip()


def controller_usage_request(
    request: dict[str, Any],
    identity: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    params = request.get("params") if isinstance(request.get("params"), dict) else {}
    meta = params.get("_meta") if isinstance(params.get("_meta"), dict) else {}
    if CONTROLLER_USAGE_META_KEY not in meta:
        return request, None
    if request.get("method") != "tools/call":
        raise ValueError("controller usage is accepted only on tools/call requests")
    identity_source = str(identity.get("identity_source") or "").strip()
    if identity_source not in _TRUSTED_CONTROLLER_USAGE_IDENTITY_SOURCES:
        raise ValueError("controller usage requires explicit or attested ChatWeb transport provenance")
    if str(identity.get("client_type") or "") != "chatweb" or str(identity.get("role") or "") != "controller":
        raise ValueError("controller usage is accepted only from the ChatWeb controller identity")
    report = validate_controller_usage_report(meta.get(CONTROLLER_USAGE_META_KEY))
    report_run_id = str(report.get("run_id") or "").strip()
    report_wave_id = str(report.get("wave_id") or "").strip()
    name = tool_call_name(request)
    if not report_run_id:
        if name != "agent_workflow":
            raise ValueError("controller usage run_id and wave_id are required after orchestration authority exists")
        report = {
            **report,
            _DEFERRED_AGENT_WORKFLOW_BINDING_KEY: True,
        }
    arguments = params.get("arguments") if isinstance(params.get("arguments"), dict) else {}
    argument_run_id = str(arguments.get("run_id") or "").strip()
    argument_wave_id = str(arguments.get("wave_id") or "").strip()
    if argument_run_id and report_run_id != argument_run_id:
        raise ValueError("controller usage run_id does not match the tool-call run_id")
    if argument_wave_id and report_wave_id != argument_wave_id:
        raise ValueError("controller usage wave_id does not match the tool-call wave_id")
    clean_meta = dict(meta)
    clean_meta.pop(CONTROLLER_USAGE_META_KEY, None)
    clean_params = dict(params)
    clean_params["_meta"] = clean_meta
    clean_request = dict(request)
    clean_request["params"] = clean_params
    return clean_request, report


def active_controller_usage_context(runtime: Any) -> tuple[str, str] | None:
    state = runtime.task_state.get()
    projection = state.get("orchestration") if isinstance(state.get("orchestration"), dict) else {}
    run_id = str(projection.get("run_id") or "").strip()
    wave_id = str(projection.get("wave_id") or "").strip()
    if not run_id or not wave_id:
        return None
    run = runtime.orchestration_ledger.get_run(run_id)
    ctx = runtime.orchestration_control.snapshot(run_id)
    if not run or ctx is None or ctx.wave_id != wave_id:
        return None
    run_status = str(run.get("status") or "").strip().lower()
    orchestration_state = str(getattr(ctx, "state", "") or "").strip().upper()
    if run_status == "active":
        return run_id, wave_id
    # Exact ChatWeb usage is a post-turn receipt: it can arrive immediately
    # after the controller has checkpointed the wave. Keep that narrow
    # terminal window eligible; record_controller_usage still requires the
    # durable controller lease, whose short TTL is the authority/freshness
    # fence for this sideband.
    if run_status == "accepted" and orchestration_state == "CHECKPOINTED":
        return run_id, wave_id
    return None


def record_controller_usage(
    runtime: Any,
    report: dict[str, Any],
    usage_context: tuple[str, str],
) -> dict[str, Any]:
    run_id, wave_id = usage_context
    normalized = dict(report)
    deferred_agent_binding = bool(normalized.pop(_DEFERRED_AGENT_WORKFLOW_BINDING_KEY, False))
    run = runtime.orchestration_ledger.get_run(run_id)
    ctx = runtime.orchestration_control.snapshot(run_id)
    if not run or ctx is None or str(getattr(ctx, "wave_id", "") or "") != wave_id:
        raise ValueError("controller usage requires the exact current orchestration run and wave")
    report_run_id = str(normalized.get("run_id") or "").strip()
    report_wave_id = str(normalized.get("wave_id") or "").strip()
    if not deferred_agent_binding and (report_run_id != run_id or report_wave_id != wave_id):
        raise ValueError("controller usage run_id/wave_id do not match the authoritative orchestration context")
    if deferred_agent_binding:
        if report_run_id or report_wave_id:
            raise ValueError("invalid deferred controller usage binding state")

    metadata = run.get("metadata") if isinstance(run.get("metadata"), dict) else {}
    host_marker = metadata.get("host_correlation") if isinstance(metadata.get("host_correlation"), dict) else {}
    evaluation = metadata.get("evaluation") if isinstance(metadata.get("evaluation"), dict) else {}
    authoritative_turn_id = str(evaluation.get("turn_id") or "").strip()
    authoritative_trace_id = str(evaluation.get("trace_id") or "").strip()
    host_source = str(host_marker.get("source") or "").strip()
    if host_marker.get("eligible") is not True or host_source not in _SERVER_OWNED_HOST_CORRELATION_SOURCES:
        raise ValueError("controller usage requires a server-owned host-turn correlation marker")
    if not authoritative_turn_id or not authoritative_trace_id:
        raise ValueError("controller usage requires authoritative turn_id and trace_id")
    if str(normalized.get("turn_id") or "") != authoritative_turn_id or str(normalized.get("trace_id") or "") != authoritative_trace_id:
        raise ValueError("controller usage turn_id/trace_id do not match the authoritative host turn")
    if host_source == "attested_chatweb_transport_trace":
        identity = runtime._current_hub_client() or {}
        if (
            str(identity.get("client_type") or "") != "chatweb"
            or str(identity.get("role") or "") != "controller"
            or str(identity.get("identity_source") or "") != "attested_transport"
            or identity.get("attestation_verified") is not True
        ):
            raise ValueError("transport-correlated controller usage requires attested ChatWeb transport provenance")
        request_trace = getattr(runtime.request_context, "trace_context", None)
        current_trace_id = str(request_trace.get("trace_id") or "").strip().lower() if isinstance(request_trace, dict) else ""
        if current_trace_id != authoritative_trace_id:
            raise ValueError("transport-correlated controller usage requires the authoritative request trace")
        if authoritative_turn_id != f"chatweb-trace:{authoritative_trace_id}":
            raise ValueError("transport-correlated controller usage has an invalid server-owned turn identity")

    run_status = str(run.get("status") or "").strip().lower()
    orchestration_state = str(getattr(ctx, "state", "") or "").strip().upper()
    if run_status == "accepted" and orchestration_state == "CHECKPOINTED":
        identity = runtime._current_hub_client()
        client_id = runtime._hub_client_record_id(identity) if identity is not None else ""
        controller = runtime.orchestration_ledger.peek_controller_lease(run_id)
        try:
            expires_at = float((controller or {}).get("expires_at") or 0.0)
        except (TypeError, ValueError):
            expires_at = 0.0
        if (not controller or controller.get("status") != "active" or controller.get("owner_client_id") != client_id
                or expires_at <= time.time()):
            raise ValueError("controller usage requires the existing unexpired scoped controller lease after checkpoint")
    elif run_status == "active":
        try:
            runtime._require_hub_controller(run_id)
        except ToolFailure as exc:
            raise ValueError(f"controller usage requires the scoped controller lease: {exc.message}") from exc
    else:
        raise ValueError("controller usage requires an active run or immediate CHECKPOINTED post-turn receipt")

    event = usage_event_from_controller_report(run_id=run_id, wave_id=wave_id, report=normalized)
    receipt = runtime.orchestration_ledger.record_usage_event(
        run_id=run_id,
        wave_id=wave_id,
        delegation_id=str(event["delegation_id"]),
        usage_event=event,
    )
    return {
        "recorded": bool(receipt.get("recorded")),
        "usage_id": str(receipt.get("usage_id") or event.get("usage_id") or ""),
        "turn_id": str(event.get("turn_id") or ""),
    }


def decorate_controller_usage_status(response: dict[str, Any], receipt: dict[str, Any]) -> None:
    result = response.get("result")
    if not isinstance(result, dict):
        return
    meta = result.get("_meta")
    if not isinstance(meta, dict):
        meta = {}
        result["_meta"] = meta
    meta[CONTROLLER_USAGE_STATUS_META_KEY] = {
        "status": "recorded" if receipt.get("recorded") else "duplicate",
        "usage_id": str(receipt.get("usage_id") or ""),
        "turn_id": str(receipt.get("turn_id") or ""),
    }
