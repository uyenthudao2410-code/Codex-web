from __future__ import annotations

import hashlib
import json
import os
from typing import Any

from . import __version__
from .envutils import ENV_PREFIX
from .truth_snapshot import build_truth_snapshot


def _compact_command(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    return {key: value.get(key) for key in ("kind", "command", "status", "started_at")}


def _compact_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "seq": int(event.get("seq") or 0),
            "event_type": str(event.get("event_type") or ""),
            "state_before": str(event.get("state_before") or ""),
            "state_after": str(event.get("state_after") or ""),
            "event_time": str(event.get("event_time") or ""),
            "payload": json.dumps(event.get("payload") or {}, ensure_ascii=False)[:400],
            "wave_id": str(event.get("wave_id") or "")[:16],
        }
        for event in events[-15:]
    ]


def _compact_proofs(proofs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "stage_id": str(item.get("stage_id") or ""),
            "status": item.get("status"),
            "duration_ms": item.get("duration_ms"),
            "cache_hit": bool(item.get("cache_hit")),
            "finished_at": str(item.get("finished_at") or ""),
        }
        for item in proofs[-6:]
    ]


def _compact_direct_usage_receipt(event: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(event, dict):
        return None
    usage = event.get("usage") if isinstance(event.get("usage"), dict) else {}
    measurement = event.get("measurement") if isinstance(event.get("measurement"), dict) else {}
    provenance = event.get("provenance") if isinstance(event.get("provenance"), dict) else {}
    cost = event.get("cost") if isinstance(event.get("cost"), dict) else {}
    usage_keys = (
        "input_total_tokens",
        "input_cached_tokens",
        "input_uncached_tokens",
        "uncached_input_tokens",
        "input_tokens",
        "cached_input_tokens",
        "output_total_tokens",
        "output_reasoning_tokens",
        "output_tokens",
        "reasoning_output_tokens",
        "total_tokens",
    )
    return {
        "usage_id": event.get("usage_id") or None,
        "turn_id": event.get("turn_id") or None,
        "event_time": event.get("event_time") or None,
        "actor": event.get("actor") or None,
        "provider_id": event.get("provider_id") or None,
        "model": event.get("model") or event.get("model_id") or None,
        "usage": {key: usage.get(key) for key in usage_keys if key in usage},
        "measurement": {
            "usage": measurement.get("usage") or "unobserved",
            "cost": measurement.get("cost") or "unobserved",
        },
        "provenance": {
            "usage": provenance.get("usage") or provenance.get("source") or "unobserved",
            "cost": provenance.get("cost") or provenance.get("source") or "unobserved",
        },
        "cost": {"provider_cost": cost.get("provider_cost")},
    }


def _direct_usage_projection(events: list[dict[str, Any]]) -> dict[str, Any]:
    latest: dict[str, dict[str, Any] | None] = {"controller": None, "provider": None}
    for event in reversed(events):
        actor = str(event.get("actor") or "provider").strip().lower()
        if actor in latest and latest[actor] is None:
            latest[actor] = _compact_direct_usage_receipt(event)
        if all(latest.values()):
            break
    return {
        "schema_version": 1,
        "source": "bounded_recent_direct_usage_events",
        "missing_measurement_policy": "unknown_not_zero",
        "controller": latest["controller"],
        "provider": latest["provider"],
    }


def _tool_call_metering_projection() -> dict[str, Any]:
    """Project host Tool-call-card token truth without fabricating it.

    ChatWeb/Coding-VP can display a token total after an invocation completes,
    but the current MCP request/response transport does not return that
    host-computed total to this runtime. Keep this plane separate from both
    tools/list and model UsageEvents, and fail closed until an exact client
    receipt exists.
    """
    return {
        "schema_version": 1,
        "measurement": "unobserved",
        "source": "chatweb_tool_call_card",
        "provenance": "client_receipt_required",
        "missing_measurement_policy": "unknown_not_zero",
        "total_tokens": None,
        "latest": None,
        "reason": "client_receipt_not_exposed_by_mcp_transport",
    }


def _bounded_objective_provenance(run: dict[str, Any], wave: dict[str, Any]) -> dict[str, Any]:
    metadata = wave.get("metadata") if isinstance(wave.get("metadata"), dict) else {}
    run_objective = str(run.get("objective") or "")[:4000]
    effective_objective = str(metadata.get("effective_objective") or run_objective)[:4000]
    revision_raw = metadata.get("objective_revision")
    revision = (
        int(revision_raw)
        if isinstance(revision_raw, int) and not isinstance(revision_raw, bool) and revision_raw >= 1
        else 1
    )
    stored_sha = str(metadata.get("objective_sha256") or "").strip().lower()
    calculated_sha = hashlib.sha256(effective_objective.encode("utf-8", errors="replace")).hexdigest()
    return {
        "run_initial_objective": run_objective,
        "effective_objective": effective_objective,
        "objective_revision": revision,
        "objective_sha256": stored_sha or calculated_sha,
        "objective_hash_valid": stored_sha == calculated_sha if stored_sha else None,
        "objective_source": str(metadata.get("objective_source") or "legacy_run_objective"),
        "objective_changed_from_previous": bool(metadata.get("objective_changed_from_previous", False)),
    }


def control_presence_projection(
    runtime: Any,
    *,
    run_id: str,
    state: dict[str, Any],
    run: dict[str, Any],
    events: list[dict[str, Any]],
    integrity: dict[str, Any] | None,
    capsule: dict[str, Any] | None,
    client_online_seconds: float,
    include_cursors: bool,
    latest_material_event_at: str = "",
) -> dict[str, Any]:
    """Project current client/authority/continuity facts without analytics."""
    ledger = runtime.orchestration_ledger
    clients = ledger.list_hub_clients(
        online_within_seconds=client_online_seconds,
        limit=16,
    )
    cursors = ledger.list_hub_client_cursors(run_id=run_id) if include_cursors and run_id else []
    cursor_by_client = {str(item.get("client_id") or ""): item for item in cursors}
    client_view: list[dict[str, Any]] = []
    for client in clients[:16]:
        client_id = str(client.get("client_id") or "")
        item = {
            "client_id": client_id,
            "client_type": client.get("client_type"),
            "role": client.get("role"),
            "status": client.get("status"),
            "online": bool(client.get("online")),
            "activity_state": runtime.hub_client_activity_state(
                client.get("last_seen_at"), active_seconds=client_online_seconds
            ),
            "last_seen_at": client.get("last_seen_at"),
            "runtime_instance_id": client.get("runtime_instance_id"),
            "contract_sha": client.get("contract_sha"),
        }
        if include_cursors:
            item["cursor"] = cursor_by_client.get(client_id)
        client_view.append(item)

    controller = ledger.peek_controller_lease(run_id) if run_id else None
    controller_view = {
        "owner_client_id": (controller or {}).get("owner_client_id", ""),
        "status": (controller or {}).get("status", "unclaimed"),
        "fencing_token": (controller or {}).get("fencing_token", 0),
        "expires_at": (controller or {}).get("expires_at", 0),
        "updated_at": (controller or {}).get("updated_at", ""),
    }
    # The live control path is a bounded read model.  A cold in-memory context
    # must not trigger orchestration recovery, full wave/event scans, or lease
    # maintenance writes from a GET request.
    ctx = runtime.orchestration_control.snapshot(run_id, recover_if_missing=False) if run_id else None
    write_lease = ctx.write_lease if ctx else None
    write_view = {
        "owner": write_lease.owner if write_lease else "",
        "status": "active" if write_lease else "released",
        "fencing_token": write_lease.fencing_token if write_lease else 0,
        "expires_at": write_lease.expires_at if write_lease else 0,
    }

    run_active = bool(run_id and run.get("status") == "active")
    desktop_online = any(
        client.get("client_type") == "codex_desktop" and client.get("online")
        for client in client_view
    )
    reason_codes: list[str] = []
    capsule_status = "missing"
    if capsule:
        capsule_status = "current"
        capsule_created_at = str(capsule.get("created_at") or "")
        control_only_events = {"controller_transferred", "write_lease_renewed"}
        if latest_material_event_at:
            capsule_status = "stale" if latest_material_event_at > capsule_created_at else "current"
        elif any(
            str(event.get("event_time") or "") > capsule_created_at
            and str(event.get("event_type") or "") not in control_only_events
            for event in events
        ):
            capsule_status = "stale"
    if run_active:
        if (integrity or {}).get("ok") is False:
            reason_codes.append("LEDGER_INTEGRITY_FAILED")
        if state.get("status") in {"paused", "stopped", "failed"}:
            reason_codes.append("TASK_NOT_RUNNABLE")
        if not desktop_online:
            reason_codes.append("DESKTOP_OFFLINE")
        if capsule_status == "missing":
            reason_codes.append("CAPSULE_MISSING")
        elif capsule_status == "stale":
            reason_codes.append("CAPSULE_STALE")
        if controller_view["status"] != "active" or controller_view["owner_client_id"] != "codex-desktop":
            reason_codes.append("CONTROLLER_HANDOFF_REQUIRED")
    safe_to_rotate = not run_active or not reason_codes
    if not run_active:
        reason_codes = ["NO_ACTIVE_EXECUTION"]
    elif safe_to_rotate:
        reason_codes = ["READY"]

    return {
        "clients": client_view,
        "cursors": cursors,
        "controller": controller_view,
        "write": write_view,
        "write_lease": write_lease,
        "capsule": capsule,
        "continuity": {
            "safe_to_rotate_chatweb": safe_to_rotate,
            "reason_codes": reason_codes,
            "capsule_status": capsule_status,
            "desktop_online": desktop_online,
            "context_pressure": {"status": "unknown", "source": "host_not_exposed"},
        },
    }


def live_control_snapshot(runtime: Any, *, client_online_seconds: float) -> dict[str, Any]:
    """Return the bounded authoritative state required by the 2-second panel poll."""
    activation = runtime.activation_admission_snapshot(blocking=False)
    if activation.get("admission_open") is not True:
        pending_truth = build_truth_snapshot(
            source=None,
            runtime_identity={
                "runtime_version": __version__,
                "process_instance_id": runtime.process_instance_id,
                "server_instance_id": runtime.server_instance_id,
                "code_revision": str(os.environ.get(f"{ENV_PREFIX}_CODE_REVISION", "")).strip() or None,
                "tool_contract": runtime.tool_contract,
            },
            orchestration=None,
            objective=None,
            proof=None,
            checkpoint=None,
            package=None,
        )
        # A full-clean activation deliberately closes tool admission while the
        # replacement process rebuilds its projection and captures a canonical
        # ledger census.  Panel polling must not compete with that transaction
        # by reconciling and re-verifying the ledger every two seconds.  Return
        # a stable fail-closed shape until the exact epoch is committed READY.
        return {
            "schema_version": 2,
            "snapshot_scope": "live_control",
            "state": "UPDATE_INCOMPLETE",
            "activation": activation,
            "task": {
                "task_id": None,
                "objective": "",
                "status": "waiting",
                "current_step": "Runtime activation pending",
                "next_step": "Wait for the full-clean activation census to complete.",
                "modified_files": [],
                "current_command": None,
                "updated_at": None,
                "pause_reason": "RUNTIME_ACTIVATION_PENDING",
            },
            "run_id": "",
            "run": None,
            "waves": [],
            "events": [],
            "proofs": [],
            "delegations": [],
            "provider_traffic": {"automatic_routing": {}},
            "capsule": None,
            "runtime_activity": {
                "schema_version": 1,
                "state": "IDLE",
                "active": False,
                "active_tool_calls": 0,
                "active_commands": 0,
                "active_background_operations": 0,
                "active_delegations": 0,
                "write_active": False,
                "managed_jobs": [],
                "background_operations": [],
            },
            "counts": {"events": 0, "waves": 0, "checkpoints": 0},
            "integrity": {"ok": False, "code": "UPDATE_INCOMPLETE"},
            "runtime": {
                "process_instance_id": runtime.process_instance_id,
                "server_instance_id": runtime.server_instance_id,
                "tool_contract": runtime.tool_contract,
                "tools": list(runtime.exposed_tool_names()),
            },
            "direct_usage": _direct_usage_projection([]),
            "tool_call_metering": _tool_call_metering_projection(),
            "truth_snapshot": pending_truth,
            "clients": [],
            "authority": {
                "controller": {
                    "owner_client_id": "",
                    "status": "unavailable",
                    "fencing_token": 0,
                    "expires_at": 0,
                    "updated_at": "",
                },
                "write": {
                    "owner": "",
                    "status": "unavailable",
                    "fencing_token": 0,
                    "expires_at": 0,
                },
            },
            "continuity": {
                "safe_to_rotate_chatweb": False,
                "reason_codes": ["RUNTIME_ACTIVATION_PENDING"],
                "capsule_status": "unavailable",
                "desktop_online": False,
                "context_pressure": {"status": "unknown", "source": "activation_pending"},
            },
        }
    state = runtime.task_state.get()
    projection = state.get("orchestration") if isinstance(state.get("orchestration"), dict) else {}
    ledger = runtime.orchestration_ledger
    run_id = str(projection.get("run_id") or "").strip()
    # The task-state projection is the current UI binding.  Ledger rows remain
    # durable execution history, but an "active" row without this exact binding
    # is not authority for the two-second live poll.  Falling back to the newest
    # ledger row can both surface an unrelated stale run and make an idle panel
    # perform unnecessary projection reads on every refresh.

    run = ledger.get_run(run_id) if run_id else None
    live_projection = ledger.live_run_projection(run_id) if run_id else {
        "waves": [], "events": [], "proofs": [], "delegations": [],
        "counts": {"events": 0, "waves": 0, "checkpoints": 0},
        "latest_material_event_at": "",
    }
    waves = list(live_projection.get("waves") or [])
    events = list(live_projection.get("events") or [])
    proofs = list(live_projection.get("proofs") or [])
    delegations = list(live_projection.get("delegations") or [])
    capsule = ledger.latest_handoff_capsule(run_id=run_id) if run_id else None
    integrity = {
        "ok": None,
        "code": "UNVERIFIED_ON_LIVE_PATH",
        "measurement": "not_checked_on_live_path",
    } if run_id else {}
    presence = control_presence_projection(
        runtime,
        run_id=run_id,
        state=state,
        run=run or {},
        events=events,
        integrity=integrity,
        capsule=capsule,
        client_online_seconds=client_online_seconds,
        include_cursors=False,
        latest_material_event_at=str(live_projection.get("latest_material_event_at") or ""),
    )
    provider_traffic = runtime.provider_traffic_snapshot()
    direct_usage = _direct_usage_projection(ledger.list_usage_events(run_id, limit=8) if run_id else [])
    wave_id = str(projection.get("wave_id") or "").strip()
    selected_wave = next(
        (item for item in reversed(waves) if str(item.get("wave_id") or "") == wave_id),
        waves[-1] if waves else {},
    )
    source_identity = runtime._cached_orchestration_workspace_identity()
    # A write lease means the cached source observation can predate mutation.
    # Fail closed until a subsequent exact workspace identity refreshes it.
    if presence["write_lease"] is not None:
        source_identity = {}
    truth_snapshot = build_truth_snapshot(
        source=source_identity,
        runtime_identity={
            "runtime_version": __version__,
            "process_instance_id": runtime.process_instance_id,
            "server_instance_id": runtime.server_instance_id,
            "code_revision": str(os.environ.get(f"{ENV_PREFIX}_CODE_REVISION", "")).strip() or None,
            "tool_contract": runtime.tool_contract,
        },
        orchestration={
            "run_id": run_id,
            "wave_id": wave_id,
            "state": projection.get("orchestration_state"),
            "run_status": (run or {}).get("status"),
            "wave_status": selected_wave.get("status") if isinstance(selected_wave, dict) else None,
            "base_head": selected_wave.get("base_head") if isinstance(selected_wave, dict) else None,
            "worktree_fp": selected_wave.get("worktree_fp") if isinstance(selected_wave, dict) else None,
        },
        objective=_bounded_objective_provenance(run or {}, selected_wave if isinstance(selected_wave, dict) else {}),
        proof=proofs[-1] if proofs else None,
        checkpoint=live_projection.get("latest_checkpoint"),
        package=None,
    )
    return {
        "schema_version": 2,
        "snapshot_scope": "live_control",
        "task": {
            "task_id": state.get("task_id"),
            "objective": str(state.get("objective") or "")[:400],
            "status": state.get("status"),
            "current_step": str(state.get("current_step") or "")[:300],
            "next_step": str(state.get("next_step") or "")[:300],
            "modified_files": [str(item) for item in list(state.get("modified_files") or [])[:10]],
            "current_command": _compact_command(state.get("current_command")),
            "updated_at": state.get("updated_at"),
            "pause_reason": str(state.get("pause_reason") or ""),
        },
        "run_id": run_id,
        "run": run,
        "waves": waves,
        "events": _compact_events(events),
        "proofs": _compact_proofs(proofs),
        "delegations": delegations,
        "provider_traffic": {"automatic_routing": dict(provider_traffic.get("automatic_routing") or {})},
        "capsule": capsule,
        "runtime_activity": runtime.runtime_activity_snapshot(
            write_active=presence["write_lease"] is not None,
            delegations=delegations,
        ),
        "counts": dict(live_projection.get("counts") or {}),
        "integrity": integrity,
        "runtime": {
            "process_instance_id": runtime.process_instance_id,
            "server_instance_id": runtime.server_instance_id,
            "tool_contract": runtime.tool_contract,
            "tools": list(runtime.exposed_tool_names()),
        },
        "direct_usage": direct_usage,
        "tool_call_metering": _tool_call_metering_projection(),
        "truth_snapshot": truth_snapshot,
        "clients": presence["clients"],
        "authority": {"controller": presence["controller"], "write": presence["write"]},
        "continuity": presence["continuity"],
    }
