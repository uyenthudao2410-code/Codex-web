from __future__ import annotations

from typing import Any

from .errors import ToolFailure
from .usage_events import usage_event_from_controller_report, validate_controller_usage_report


CONTROLLER_USAGE_META_KEY = "io.coding-tools/controllerUsage"
CONTROLLER_USAGE_STATUS_META_KEY = "io.coding-tools/controllerUsageStatus"


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
    if str(identity.get("client_type") or "") != "chatweb" or str(identity.get("role") or "") != "controller":
        raise ValueError("controller usage is accepted only from the ChatWeb controller identity")
    report = validate_controller_usage_report(meta.get(CONTROLLER_USAGE_META_KEY))
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
    if not run or str(run.get("status") or "") != "active" or ctx is None or ctx.wave_id != wave_id:
        return None
    return run_id, wave_id


def record_controller_usage(
    runtime: Any,
    report: dict[str, Any],
    usage_context: tuple[str, str],
) -> dict[str, Any]:
    run_id, wave_id = usage_context
    try:
        runtime._require_hub_controller(run_id)
    except ToolFailure as exc:
        raise ValueError(f"controller usage requires the scoped controller lease: {exc.message}") from exc
    event = usage_event_from_controller_report(run_id=run_id, wave_id=wave_id, report=report)
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
