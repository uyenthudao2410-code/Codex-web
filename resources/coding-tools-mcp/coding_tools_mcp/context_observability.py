from __future__ import annotations

from typing import Any

from .controller_reattach import run_binding_from_metadata


def _unknown_knowledge(reason: str) -> dict[str, Any]:
    return {
        "status": "unobserved", "reason": reason, "linkage": None,
        "workspace_id": None, "problem_id": None, "problem_revision": None,
        "knowledge_revision": None, "checkpoint_id": None, "checkpoint_created_at": None,
    }


def controller_knowledge_for_run(
    ledger: Any, run_id: str, *, run: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Read an exact Problem/knowledge watermark without activating schemas."""
    run_key = str(run_id or "").strip()[:256]
    if not run_key:
        return _unknown_knowledge("run_id_missing")
    run_row = run if isinstance(run, dict) else ledger.get_run(run_key)
    if not isinstance(run_row, dict):
        return _unknown_knowledge("run_not_found")
    metadata = run_row.get("metadata") if isinstance(run_row.get("metadata"), dict) else {}
    binding = run_binding_from_metadata(metadata)
    if not isinstance(binding, dict):
        return _unknown_knowledge("exact_problem_binding_missing")
    workspace_id = str(binding.get("workspace_id") or "").strip()
    problem_id = str(binding.get("problem_id") or "").strip()
    problem_revision = binding.get("problem_revision")
    if not workspace_id:
        return _unknown_knowledge("exact_workspace_identity_missing")
    with ledger._lock, ledger._connect() as connection:
        available = {
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name IN ('problem_threads','controller_knowledge_checkpoints')"
            ).fetchall()
        }
        if available != {"problem_threads", "controller_knowledge_checkpoints"}:
            return _unknown_knowledge("continuity_schema_unavailable")
        thread = connection.execute(
            "SELECT current_revision FROM problem_threads WHERE problem_id=?", (problem_id,)
        ).fetchone()
        if thread is None:
            return _unknown_knowledge("problem_not_found")
        if int(thread["current_revision"]) != int(problem_revision or 0):
            return _unknown_knowledge("run_problem_revision_stale")
        checkpoint = connection.execute(
            """SELECT checkpoint_id,problem_revision,knowledge_revision,
                      material_event_kind,material_event_id,created_at
               FROM controller_knowledge_checkpoints
               WHERE workspace_id=? AND problem_id=? AND problem_revision=?
               ORDER BY knowledge_revision DESC LIMIT 1""",
            (workspace_id, problem_id, int(problem_revision)),
        ).fetchone()
    if checkpoint is None:
        return _unknown_knowledge("knowledge_checkpoint_missing")
    return {
        "status": "observed", "reason": None,
        "linkage": "exact_run_problem_binding", "workspace_id": workspace_id,
        "problem_id": problem_id, "problem_revision": int(checkpoint["problem_revision"]),
        "knowledge_revision": int(checkpoint["knowledge_revision"]),
        "checkpoint_id": str(checkpoint["checkpoint_id"]),
        "material_event_kind": str(checkpoint["material_event_kind"]),
        "material_event_id": str(checkpoint["material_event_id"]),
        "checkpoint_created_at": str(checkpoint["created_at"]),
    }


def context_observability_projection(
    *, run_id: str, clients: list[dict[str, Any]], direct_usage: dict[str, Any],
    capsule: dict[str, Any] | None, events: list[dict[str, Any]],
    counts: dict[str, Any], controller_knowledge: dict[str, Any],
) -> dict[str, Any]:
    """Build TG5 capability truth from already-bounded live inputs."""
    controller = direct_usage.get("controller") if isinstance(direct_usage, dict) else None
    measurement = controller.get("measurement") if isinstance(controller, dict) else {}
    provenance = controller.get("provenance") if isinstance(controller, dict) else {}
    usage_observed = bool(
        isinstance(measurement, dict) and measurement.get("usage") == "measured"
        and isinstance(provenance, dict)
        and provenance.get("usage") in {"client_reported", "provider_reported"}
    )
    turn_id = str(controller.get("turn_id") or "") if isinstance(controller, dict) else ""
    trace_id = str(controller.get("trace_id") or "") if isinstance(controller, dict) else ""
    transport_sessions = sorted({
        str(client.get("session_instance") or "") for client in clients
        if client.get("client_type") == "chatweb" and client.get("role") == "controller"
        and str(client.get("session_instance") or "")
    })[:4]
    exact_turn_trace = bool(turn_id and trace_id)
    host_spans = [
        event for event in events
        if str(event.get("event_type") or "") == "observation_span_recorded"
        and isinstance(event.get("payload"), dict)
        and event["payload"].get("observer_plane") == "electron_chatgpt_dom"
    ]
    knowledge_linked = [
        event for event in host_spans
        if isinstance(event["payload"].get("controller_knowledge_at_observation"), dict)
        and event["payload"]["controller_knowledge_at_observation"].get("status") == "observed"
    ]
    signals = [
        {"name": "run_event_count", "value": int(counts.get("events") or 0) if run_id else None, "window": "current_exact_run"},
        {"name": "recent_host_turn_span_count", "value": len(host_spans) if run_id else None, "window": "bounded_recent_events_max_15"},
        {"name": "recent_exact_controller_usage_receipt", "value": usage_observed, "window": "bounded_latest_receipt"},
        {"name": "conversation_epoch", "value": capsule.get("conversation_epoch") if isinstance(capsule, dict) else None, "window": "latest_handoff_capsule"},
        {"name": "continuity_capsule_bytes", "value": capsule.get("bytes") if isinstance(capsule, dict) else None, "window": "latest_handoff_capsule"},
    ]
    return {
        "schema_version": 1, "source": "bounded_live_control_inputs",
        "missing_measurement_policy": "unknown_not_zero",
        "capability_matrix": {
            "exact_controller_usage": {
                "status": "supported", "observation": "observed" if usage_observed else "unobserved",
                "transport": "mcp_tools_call_meta", "coverage": "bounded_recent_only",
            },
            "exact_session_identity": {
                "status": "partial" if transport_sessions or exact_turn_trace else "unobserved",
                "product_session_id": {"status": "unobserved", "value": None},
                "opaque_transport_session": {
                    "status": "observed" if transport_sessions else "unobserved",
                    "values": transport_sessions, "not_product_chat_session": True,
                },
                "turn_trace_identity": {
                    "status": "observed" if exact_turn_trace else "unobserved",
                    "turn_id": turn_id or None, "trace_id": trace_id or None,
                },
            },
            "exact_context_pressure": {
                "status": "unobserved", "value": None, "source": "host_not_exposed",
                "bytes_or_revision_fallback_forbidden": True,
            },
            "controller_knowledge_revision": {
                **controller_knowledge,
                "status": "supported", "observation": controller_knowledge.get("status"),
            },
            "heuristic_rotation_signals": {
                "status": "available", "source": "heuristic", "signals": signals,
                "not_exact_context_pressure": True, "not_rotation_authority": True,
            },
        },
        "material_host_observation_linkage": {
            "recent_host_span_count": len(host_spans),
            "recent_knowledge_linked_span_count": len(knowledge_linked),
            "window": "bounded_recent_events_max_15",
        },
        "rotation_policy": {
            "automatic_handoff": "off", "safe_to_rotate_source": "continuity_authority_projection",
            "context_signal_is_not_rotation_authority": True,
        },
    }
