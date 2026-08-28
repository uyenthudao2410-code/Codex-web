from __future__ import annotations

import json
from typing import Any


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
    clients = ledger.list_hub_clients(online_within_seconds=client_online_seconds)
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
    ctx = runtime.orchestration_control.snapshot(run_id) if run_id else None
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
            },
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
    if not run_id:
        active = ledger.peek_current_active_run()
        if active:
            run_id = str(active.get("run_id") or "").strip()

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
        },
        "clients": presence["clients"],
        "authority": {"controller": presence["controller"], "write": presence["write"]},
        "continuity": presence["continuity"],
    }
