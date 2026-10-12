from __future__ import annotations

import base64
import functools
import http.server
import json
import os
import posixpath
import re
import secrets
import sys
import threading
import time
import urllib.parse
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from . import __version__
from .activation_capability import recovery_activation_capability, valid_activation_control_payload
from .envutils import ENV_PREFIX, truthy_env
from .errors import JsonRpcError, ToolFailure, normalize_exception_group
from .http_origin import _configured_allowed_origins, is_allowed_origin  # noqa: F401  # compatibility re-export
from .oauth import (
    MAX_PENDING_CODES,
    OAUTH_CODE_TTL_SECONDS,
    OAUTH_MAX_BODY_BYTES,
    create_access_token,
    oauth_login_page,
    send_oauth_html,
    valid_pkce_challenge,
    validate_access_token,
    verify_pkce,
)
from .protocol import (
    LEGACY_PROTOCOL_VERSIONS,
    PROTOCOL_VERSION,
    STATELESS_PROTOCOL_VERSION,
    SUPPORTED_PROTOCOL_VERSIONS,
    dispatch_rpc,
    jsonrpc_error,
    protocol_version_is_supported,
    request_protocol_version,
    response_id,
    validate_rpc_envelope,
)
from .controller_usage_ingress import CONTROLLER_USAGE_META_KEY, active_controller_usage_context, controller_usage_request, decorate_controller_usage_status, record_controller_usage, tool_call_name
from .continuation_consent_http import (
    CONTINUATION_CONSENT_HTTP_PATH,
    ContinuationConsentHTTPMixin,
    local_continuation_consent_origin,
)
from .endpoint_identity import workspace_binding_id
from .live_control import control_presence_projection, live_control_snapshot
from .mcp_metadata import MCP_ENDPOINT_PATH, SERVER_NAME, SERVER_TITLE, server_card_payload  # noqa: F401  # compatibility re-export
from .operations_analytics import operations_analytics
from .trace_context import parse_trace_context
from .truth_snapshot import build_truth_snapshot
from .transport_http import (
    STATELESS_HTTP_2026_ENV,
    HTTPSessionManager,
    StaleHTTPSessionError,
    _decode_mcp_name_header,
    _first_form_value,
    _first_header_value,
    _forwarded_header_param,
    _http_base_for_bind_host,
    _request_mcp_name,
    _safe_external_host,
    stateless_http_2026_enabled,
)
from .http_hub_identity import HTTPHubIdentityMixin
from .stateless_context import STATELESS_TASK_CONTEXT_META_KEY, resolve_stateless_task_context
from .task_state import TaskStateStore
from .task_snapshot_projection import build_task_snapshot_projection

if TYPE_CHECKING:
    from .server import Runtime


HUB_CLIENT_ONLINE_SECONDS = 45.0
HUB_CONTROLLER_LEASE_SECONDS = 60.0

HUB_CLIENT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$")

MAX_HTTP_REQUEST_BYTES = 1_048_576

OAUTH_TOKEN_AUTH_METHODS = ("client_secret_basic", "client_secret_post", "none")


def json_response_payload(payload: Any) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")



def is_loopback_bind_host(host: str) -> bool:
    return host in {"localhost", "127.0.0.1", "::1", ""}


class MCPHandler(ContinuationConsentHTTPMixin, HTTPHubIdentityMixin, http.server.BaseHTTPRequestHandler):
    server_version = f"CodingToolsMCP/{__version__}"

    @property
    def runtime(self) -> Runtime:
        runtime = getattr(self, "_runtime", None)
        if runtime is not None:
            return cast(Any, runtime)
        return cast(Any, self.server.control_runtime)  # type: ignore[attr-defined]

    def log_message(self, format: str, *args: Any) -> None:
        print(format % args, file=sys.stderr)

    def send_rpc_error(
        self,
        code: int,
        message: str,
        *,
        status: int = 400,
        request_id: str | int | None = None,
        data: Any = None,
        extra_headers: dict[str, str] | None = None,
        head_only: bool = False,
    ) -> None:
        self.send_json(
            jsonrpc_error(request_id, code, message, data),
            status=status,
            extra_headers=extra_headers,
            head_only=head_only,
        )

    def do_GET(self) -> None:
        if posixpath.normpath(self.path.split("?", 1)[0]) == CONTINUATION_CONSENT_HTTP_PATH:
            self.handle_continuation_consent_get()
            return
        if (
            posixpath.normpath(self.path.split("?", 1)[0]) == MCP_ENDPOINT_PATH
            and self.headers.get("MCP-Protocol-Version") == STATELESS_PROTOCOL_VERSION
            and stateless_http_2026_enabled()
        ):
            self.send_rpc_error(-32601, "GET is not supported by stateless MCP 2026-07-28", status=405)
            return
        self.handle_metadata_request(head_only=False)

    def do_HEAD(self) -> None:
        if (
            posixpath.normpath(self.path.split("?", 1)[0]) == MCP_ENDPOINT_PATH
            and self.headers.get("MCP-Protocol-Version") == STATELESS_PROTOCOL_VERSION
            and stateless_http_2026_enabled()
        ):
            self.send_rpc_error(
                -32601,
                "HEAD is not supported by stateless MCP 2026-07-28",
                status=405,
                head_only=True,
            )
            return
        self.handle_metadata_request(head_only=True)

    def do_DELETE(self) -> None:
        request_path = self.path.split("?", 1)[0]
        if posixpath.normpath(request_path) != MCP_ENDPOINT_PATH:
            self.send_json({"error": "Unknown endpoint"}, status=404)
            return
        if not self.is_authorized():
            self.send_unauthorized()
            return
        if (
            self.headers.get("MCP-Protocol-Version") == STATELESS_PROTOCOL_VERSION
            and stateless_http_2026_enabled()
        ):
            self.send_rpc_error(-32601, "DELETE is not supported by stateless MCP 2026-07-28", status=405)
            return
        session_id = self.headers.get("Mcp-Session-Id")
        if not session_id or not self.server.sessions.delete(session_id):  # type: ignore[attr-defined]
            self.send_rpc_error(-32001, "Unknown MCP session", status=404)
            return
        self.send_response(200)
        self.send_header("Content-Length", "0")
        self.send_cors_headers()
        self.end_headers()

    def do_OPTIONS(self) -> None:
        request_path = self.path.split("?", 1)[0]
        if posixpath.normpath(request_path) not in {
            MCP_ENDPOINT_PATH,
            "/.well-known/mcp.json",
            "/.well-known/mcp/server-card.json",
            "/__control/health",
            "/__control/activation",
            "/__control/workspace",
            "/__control/roots",
            "/__control/orchestration",
            "/__control/orchestration/live",
            "/.well-known/oauth-authorization-server",
            "/.well-known/oauth-protected-resource",
            "/oauth/authorize",
            "/oauth/token",
            "/oauth/register",
            CONTINUATION_CONSENT_HTTP_PATH,
        }:
            self.send_json({"error": "Unknown endpoint"}, status=404)
            return
        origin = self.headers.get("Origin")
        if origin and not is_allowed_origin(origin):
            self.send_json({"error": "Origin denied"}, status=403)
            return
        self.send_response(204)
        self.send_header("Allow", "GET, HEAD, POST, DELETE, OPTIONS")
        self.send_cors_headers()
        self.end_headers()

    def handle_metadata_request(self, *, head_only: bool) -> None:
        request_path = self.path.split("?", 1)[0]
        normalized = posixpath.normpath(request_path)
        if normalized == "/__control/health":
            if not self.is_authorized():
                self.send_unauthorized(head_only=head_only)
                return
            runtime = self.runtime
            sessions_snapshot_busy = not runtime.sessions_lock.acquire(blocking=False)
            if sessions_snapshot_busy:
                active_commands = None
                retained_outputs = None
            else:
                try:
                    active_commands = len(runtime.sessions)
                    retained_outputs = len(runtime.output_sessions)
                finally:
                    runtime.sessions_lock.release()
            # Health is a liveness/identity observation and must not queue behind
            # a concurrent connector/session bookkeeping write.  Each snapshot
            # stays fail-closed when busy; mutation and activation paths retain
            # their ordinary blocking locks.
            connector_discovery = runtime.connector_tool_discovery(blocking=False)
            connector_contact = runtime.connector_client_contact(blocking=False)
            controller_usage_envelope = runtime.connector_controller_usage_envelope(blocking=False)
            connector_activation_bootstrap = runtime.connector_activation_bootstrap(blocking=False)
            http_sessions = self.server.sessions.stats(blocking=False)
            activation = runtime.activation_admission_snapshot(blocking=False)
            health_snapshot_busy = bool(
                sessions_snapshot_busy
                or activation.get("snapshot_busy") is True
                or connector_discovery.get("snapshot_busy") is True
                or connector_contact.get("snapshot_busy") is True
                or controller_usage_envelope.get("snapshot_busy") is True
                or connector_activation_bootstrap.get("snapshot_busy") is True
                or http_sessions.get("snapshot_busy") is True
            )
            self.send_json({
                "ready": not runtime._closed,
                "activation": activation,
                **activation,
                "snapshot_busy": health_snapshot_busy,
                "health_snapshot_busy": health_snapshot_busy,
                "sessions_snapshot_busy": sessions_snapshot_busy,
                "version": __version__,
                "instance_id": runtime.server_instance_id,
                "process_instance_id": runtime.process_instance_id,
                "workspace": str(runtime.workspace.root),
                "default_cwd": runtime.default_cwd_display(),
                "authorized_roots": [str(item) for item in runtime.workspace.authorized_roots if item != runtime.workspace.root],
                "tool_mode": runtime.tool_mode,
                "tool_profile": runtime.tool_contract["profile"],
                "tool_count": len(runtime.exposed_tool_names()),
                "tool_contract": dict(runtime.tool_contract),
                "connector_tool_discovery": connector_discovery,
                "connector_client_contact": connector_contact,
                "connector_controller_usage_envelope": controller_usage_envelope,
                "connector_activation_bootstrap": connector_activation_bootstrap,
                "projection_rebuild": runtime.projection_rebuild_snapshot(),
                "workspace_generation": runtime.workspace_generation,
                "workspace_binding_id": workspace_binding_id(
                    device_instance_id=str(os.environ.get(f"{ENV_PREFIX}_DEVICE_INSTANCE_ID", "") or "").strip(),
                    workspace_root=runtime.workspace.root,
                    generation=runtime.workspace_generation,
                ),
                "code_revision": str(os.environ.get(f"{ENV_PREFIX}_CODE_REVISION", "")).strip() or None,
                "device_id": str(os.environ.get(f"{ENV_PREFIX}_DEVICE_ID", "")).strip() or None,
                "device_instance_id": str(os.environ.get(f"{ENV_PREFIX}_DEVICE_INSTANCE_ID", "")).strip() or None,
                "device_display_name": str(os.environ.get(f"{ENV_PREFIX}_DEVICE_DISPLAY_NAME", "")).strip() or None,
                "active_commands": active_commands,
                "retained_outputs": retained_outputs,
                "legacy_session_alias_uses": runtime.legacy_session_alias_uses,
                "http_sessions": http_sessions,
            }, head_only=head_only)
            return
        if normalized == "/__control/activation":
            if not self.is_authorized():
                self.send_unauthorized(head_only=head_only)
                return
            capability = recovery_activation_capability(self.headers, self.runtime)
            self.send_json(
                self.runtime.activation_preflight_snapshot(
                    operation_id=str(capability["operation_id"]),
                    ignore_active_tool_calls=int(capability["ignore_active_tool_calls"]),
                ),
                head_only=head_only,
            )
            return
        if normalized == "/__control/orchestration/live":
            if not self.is_authorized():
                self.send_unauthorized(head_only=head_only)
                return
            self.send_json(
                live_control_snapshot(self.runtime, client_online_seconds=HUB_CLIENT_ONLINE_SECONDS),
                head_only=head_only,
            )
            return
        if normalized == "/__control/orchestration/analytics":
            if not self.is_authorized():
                self.send_unauthorized(head_only=head_only)
                return
            ledger = self.runtime.orchestration_ledger
            window_days = 7
            generated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            self.send_json({
                "schema_version": 1,
                "snapshot_scope": "dashboard_analytics",
                "generated_at": generated_at,
                "window_days": window_days,
                "usage_analytics": ledger.usage_analytics(days=window_days, now=generated_at),
                "operations_analytics": operations_analytics(
                    ledger,
                    performance=self.runtime.performance_trace.get(),
                    days=window_days,
                    now=generated_at,
                ),
                "content_free": True,
            }, head_only=head_only)
            return
        if normalized == "/__control/orchestration":
            if not self.is_authorized():
                self.send_unauthorized(head_only=head_only)
                return
            self.send_json(self.control_orchestration_snapshot(), head_only=head_only)
            return
        if normalized == "/.well-known/oauth-authorization-server":
            self.handle_oauth_as_metadata(head_only=head_only)
            return
        if normalized in {"/.well-known/oauth-protected-resource", "/.well-known/oauth-protected-resource/mcp"}:
            self.handle_oauth_resource_metadata(head_only=head_only)
            return
        if normalized == "/oauth/authorize" and not head_only:
            self.handle_oauth_authorize_get()
            return
        if normalized == MCP_ENDPOINT_PATH:
            origin = self.headers.get("Origin")
            if origin and not is_allowed_origin(origin):
                self.send_json({"error": "Origin denied"}, status=403, head_only=head_only)
                return
            if not self.is_authorized():
                self.send_unauthorized(head_only=head_only)
                return
            self.send_rpc_error(
                -32000,
                "SSE GET stream is not supported",
                status=405,
                extra_headers={"Allow": "POST, DELETE"},
                head_only=head_only,
            )
            return
        if normalized in {"/.well-known/mcp.json", "/.well-known/mcp/server-card.json"}:
            self.send_json(server_card_payload(self.runtime, oauth_base_url=self.oauth_base_url()), head_only=head_only)
            return
        self.send_json({"error": "Unknown endpoint"}, status=404, head_only=head_only)

    def control_orchestration_snapshot(self) -> dict[str, Any]:
        runtime = self.runtime
        runtime._maybe_reconcile_stale_orchestration()
        # Reconnects must return the canonical ledger state even when the
        # previous response stream was interrupted midway through a turn.
        runtime._reconcile_task_orchestration_projection()
        state = runtime.task_state.get()
        projection = state.get("orchestration") if isinstance(state.get("orchestration"), dict) else {}
        ledger = runtime.orchestration_ledger
        run_id = str(projection.get("run_id") or "").strip()
        if not run_id:
            active = ledger.current_active_run()
            if active:
                run_id = str(active.get("run_id") or "").strip()
        summary = ledger.export_summary(run_id) if run_id else {}
        events = summary.get("events") or []
        compact_events = [
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
        proofs = [
            {
                "stage_id": str(item.get("stage_id") or ""),
                "status": item.get("status"),
                "duration_ms": item.get("duration_ms"),
                "cache_hit": bool(item.get("cache_hit")),
                "finished_at": str(item.get("finished_at") or ""),
            }
            for item in (summary.get("proofs") or [])[-6:]
        ]
        task_projection = build_task_snapshot_projection(state)
        capsule = summary.get("latest_handoff_capsule")
        run = summary.get("run") or {}
        presence = control_presence_projection(
            runtime,
            run_id=run_id,
            state=state,
            run=run,
            events=events,
            integrity=summary.get("integrity"),
            capsule=capsule,
            client_online_seconds=HUB_CLIENT_ONLINE_SECONDS,
            include_cursors=True,
        )
        client_view = presence["clients"]
        cursors = presence["cursors"]
        controller_view = presence["controller"]
        write_view = presence["write"]
        write_lease = presence["write_lease"]
        continuity = presence["continuity"]
        latest_event_seq = int(events[-1].get("seq") or 0) if events else 0
        flight_recorder = ledger.flight_recorder(run_id, limit=40) if run_id else {
            "run_id": "", "after_seq": 0, "events": [], "next_after_seq": 0, "has_more": False,
            "phase_timing": {"run_id": "", "source": "eocl_event_timestamps", "segments": [], "by_state_ms": {}, "complete": False},
        }
        pending_messages = ledger.list_coordination_messages(run_id=run_id, status="pending", limit=100) if run_id else []
        modified_paths = []
        for item in list(state.get("modified_files") or [])[:12]:
            path = item.get("path") if isinstance(item, dict) else item
            if str(path or "").strip():
                modified_paths.append(str(path))
        resume_packet = {
            "version": 1,
            "run_id": run_id,
            "wave_id": str(projection.get("wave_id") or ""),
            "objective": str(state.get("objective") or "")[:600],
            "task_status": state.get("status"),
            "orchestration_state": projection.get("orchestration_state"),
            "current_step": str(state.get("current_step") or "")[:300],
            "next_step": str(state.get("next_step") or "")[:500],
            "latest_event_seq": latest_event_seq,
            "modified_paths": modified_paths,
            "proofs": [{
                "proof_id": item.get("proof_id"),
                "stage_id": item.get("stage_id"),
                "status": item.get("status"),
                "finished_at": item.get("finished_at"),
            } for item in (summary.get("proofs") or [])[-6:]],
            "capsule": ({
                "capsule_id": capsule.get("capsule_id"),
                "sha256": capsule.get("sha256"),
                "bytes": capsule.get("bytes"),
                "conversation_epoch": capsule.get("conversation_epoch"),
                "created_at": capsule.get("created_at"),
            } if capsule else None),
            "controller": controller_view,
            "pending_message_count": len(pending_messages),
        }
        lane_view = [
            {
                "lane_id": str(item.get("lane_id") or ""),
                "lifecycle": item.get("lifecycle"),
                "provider": item.get("provider"),
                "profile": item.get("profile"),
                "model": item.get("model"),
                "updated_at": item.get("updated_at"),
                "last_economics": (item.get("metadata") or {}).get("last_economics"),
            }
            for item in (ledger.list_agent_lanes() or [])[:12]
        ]
        wave_id = str(projection.get("wave_id") or "").strip()
        waves = summary.get("waves") or []
        selected_wave = next(
            (item for item in reversed(waves) if str(item.get("wave_id") or "") == wave_id),
            waves[-1] if waves else {},
        )
        objective = (
            ledger.wave_objective_provenance(run_id, wave_id=str(selected_wave.get("wave_id") or wave_id))
            if run_id and selected_wave
            else {}
        )
        source_identity = runtime._orchestration_workspace_identity(".")
        latest_proof = (summary.get("proofs") or [])[-1] if summary.get("proofs") else {}
        latest_checkpoint = (summary.get("checkpoints") or [])[-1] if summary.get("checkpoints") else {}
        truth_snapshot = build_truth_snapshot(
            source=source_identity,
            runtime_identity={
                "runtime_version": __version__,
                "process_instance_id": runtime.process_instance_id,
                "server_instance_id": runtime.server_instance_id,
                "code_revision": str(os.environ.get(f"{ENV_PREFIX}_CODE_REVISION", "")).strip() or None,
                "tool_contract": dict(runtime.tool_contract),
            },
            orchestration={
                "run_id": run_id,
                "wave_id": wave_id,
                "state": projection.get("orchestration_state"),
                "run_status": run.get("status"),
                "wave_status": selected_wave.get("status") if isinstance(selected_wave, dict) else None,
                "base_head": selected_wave.get("base_head") if isinstance(selected_wave, dict) else None,
                "worktree_fp": selected_wave.get("worktree_fp") if isinstance(selected_wave, dict) else None,
            },
            objective=objective,
            proof=latest_proof,
            checkpoint=latest_checkpoint,
            package=None,
        )
        task_history = [
            {
                "run_id": item.get("run_id"),
                "task_id": item.get("task_id"),
                "objective": str(item.get("objective") or "")[:400],
                "status": item.get("status"),
                "started_at": item.get("started_at"),
                "finished_at": item.get("finished_at"),
            }
            for item in ledger.list_runs(limit=12)
        ]
        current_task = (
            {
                "run_id": run.get("run_id"),
                "task_id": run.get("task_id"),
                "objective": str(run.get("objective") or "")[:400],
                "status": run.get("status"),
                "started_at": run.get("started_at"),
                "finished_at": run.get("finished_at"),
            }
            if isinstance(run, dict) and str(run.get("run_id") or "")
            else None
        )
        return {
            "schema_version": 2,
            "activation": runtime.activation_admission_snapshot(),
            **runtime.activation_admission_snapshot(),
            "task": {
                "task_id": state.get("task_id"),
                "run_id": str(projection.get("run_id") or ""),
                "wave_id": str(projection.get("wave_id") or ""),
                "objective": str(state.get("objective") or "")[:400],
                "status": state.get("status"),
                "current_step": str(state.get("current_step") or "")[:300],
                "next_step": str(state.get("next_step") or "")[:300],
                **task_projection,
                "updated_at": state.get("updated_at"),
                "pause_reason": str(state.get("pause_reason") or ""),
            },
            "run_id": run_id,
            "run": summary.get("run"),
            "waves": (summary.get("waves") or [])[-3:],
            "events": compact_events,
            "proofs": proofs,
            "delegations": (summary.get("delegations") or [])[-4:],
            "lanes": lane_view,
            "usage_events": ledger.recent_usage_events(limit=8),
            "usage_analytics": ledger.usage_analytics(days=7),
            "operations_analytics": operations_analytics(
                ledger,
                performance=runtime.performance_trace.get(),
                days=7,
            ),
            "routing_evidence": ledger.routing_evidence(run_id, limit=8) if run_id else {
                "shadow_recommendations": [], "actual_delegations": [], "usage_events": []
            },
            "provider_traffic": runtime.provider_traffic_snapshot(),
            "flight_recorder": flight_recorder,
            "task_list": {
                "schema_version": 1,
                "source": "orchestration_ledger",
                "current": current_task,
                "history": task_history,
            },
            "history": {"runs": task_history},
            "capsule": summary.get("latest_handoff_capsule"),
            "background_operations": ledger.list_background_operations(limit=8),
            "runtime_activity": runtime.runtime_activity_snapshot(write_active=bool(write_lease), delegations=summary.get("delegations") or []),
            "counts": {
                "events": len(events),
                "waves": len(summary.get("waves") or []),
                "checkpoints": len(summary.get("checkpoints") or []),
            },
            "integrity": summary.get("integrity"),
            "runtime": {
                "process_instance_id": runtime.process_instance_id,
                "server_instance_id": runtime.server_instance_id,
                "tool_contract": runtime.tool_contract,
                **runtime.activation_admission_snapshot(),
            },
            "truth_snapshot": truth_snapshot,
            "clients": client_view,
            "authority": {"controller": controller_view, "write": write_view},
            "cursors": cursors,
            "continuity": continuity,
            "resume_packet": resume_packet,
        }

    def _read_control_json(self) -> dict[str, Any] | None:
        if self.headers.get_content_type().lower() != "application/json":
            self.send_json({"error": "Content-Type must be application/json"}, status=415)
            return None
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_json({"error": "Invalid Content-Length"}, status=400)
            return None
        if length <= 0 or length > 65536:
            self.send_json({"error": "Invalid request size"}, status=413)
            return None
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            self.send_json({"error": str(exc)}, status=400)
            return None
        if not isinstance(payload, dict):
            self.send_json({"error": "JSON body must be an object"}, status=400)
            return None
        return payload

    def handle_control_hub(self) -> None:
        if not self.is_authorized():
            self.send_unauthorized()
            return
        payload = self._read_control_json()
        if payload is None:
            return
        action = str(payload.get("action") or "heartbeat").strip().lower()
        try:
            if action == "heartbeat":
                identity = self._hub_identity_from_values(
                    client_id=str(payload.get("client_id") or ""),
                    client_type=str(payload.get("client_type") or "client"),
                    client_name=str(payload.get("client_name") or ""),
                    client_version=str(payload.get("client_version") or ""),
                )
                result = self.runtime._touch_hub_client(identity)
                self.send_json({"ok": True, "action": action, **result})
                return
            if action == "provider_telemetry":
                identity = self._hub_identity_from_values(
                    client_id=str(payload.get("client_id") or ""),
                    client_type=str(payload.get("client_type") or "client"),
                    client_name=str(payload.get("client_name") or ""),
                    client_version=str(payload.get("client_version") or ""),
                )
                if (identity.get("client_id"), identity.get("client_type")) != ("opencode", "opencode"):
                    raise ValueError("provider telemetry requires the OpenCode proxy identity")
                result = self.runtime.ingest_provider_telemetry(identity, payload.get("telemetry"))
                self.send_json({"ok": True, "action": action, **result})
                return
            if action in {"provider_dispatch", "provider_observe", "provider_cancel"}:
                identity = self._hub_identity_from_values(
                    client_id=str(payload.get("client_id") or ""),
                    client_type=str(payload.get("client_type") or "client"),
                    client_name=str(payload.get("client_name") or ""),
                    client_version=str(payload.get("client_version") or ""),
                )
                if action == "provider_dispatch":
                    result = self.runtime.dispatch_opencode_provider(identity, payload)
                else:
                    dispatch_id = str(payload.get("dispatch_id") or "").strip()
                    if not dispatch_id:
                        raise ValueError("dispatch_id is required")
                    result = self.runtime.observe_opencode_provider(identity, dispatch_id, cancel=action == "provider_cancel")
                self.send_json({"ok": True, "action": action, **result})
                return
            if action == "shadow_route":
                identity = self._hub_identity_from_values(
                    client_id=str(payload.get("client_id") or ""),
                    client_type=str(payload.get("client_type") or "client"),
                    client_name=str(payload.get("client_name") or ""),
                    client_version=str(payload.get("client_version") or ""),
                )
                result = self.runtime.shadow_route(identity, payload.get("features"))
                self.send_json({"ok": True, "action": action, **result})
                return
            if action == "transfer_controller":
                target = str(payload.get("target_client_id") or "").strip()
                if not HUB_CLIENT_ID_RE.fullmatch(target):
                    raise ValueError("valid target_client_id is required")
                run_id = str(payload.get("run_id") or self.runtime._projected_hub_run_id() or "").strip()
                if not run_id:
                    raise ValueError("run_id is required when no task orchestration is active")
                before = self.runtime.orchestration_ledger.get_controller_lease(run_id)
                result = self.runtime.orchestration_ledger.operator_transfer_controller(
                    run_id=run_id,
                    target_client_id=target,
                    lease_id=f"client:{target}",
                    ttl_seconds=HUB_CONTROLLER_LEASE_SECONDS,
                    online_within_seconds=HUB_CLIENT_ONLINE_SECONDS,
                )
                if result.get("transferred"):
                    ctx = self.runtime.orchestration_control.snapshot(run_id)
                    state_name = ctx.state if ctx else ""
                    self.runtime.orchestration_ledger.append_event(
                        run_id,
                        wave_id=ctx.wave_id if ctx else None,
                        event_type="controller_transferred",
                        state_before=state_name,
                        state_after=state_name,
                        payload={
                            "from_client_id": (before or {}).get("owner_client_id", ""),
                            "to_client_id": target,
                            "fencing_token": result.get("fencing_token"),
                        },
                    )
                self.send_json({"ok": bool(result.get("transferred")), "action": action, **result}, status=200 if result.get("transferred") else 409)
                return
            raise ValueError(f"unsupported hub action: {action}")
        except ValueError as exc:
            self.send_json({"error": str(exc), "code": "INVALID_HUB_REQUEST"}, status=400)
        except ToolFailure as exc:
            self.send_json({"error": exc.message, "code": exc.code, "details": exc.details}, status=409)

    def handle_control_activation(self) -> None:
        if not self.is_authorized():
            self.send_unauthorized()
            return
        payload = self._read_control_json()
        if payload is None:
            return
        action = str(payload.get("action") or "").strip().lower()
        if not valid_activation_control_payload(action, payload):
            self.send_json({"error": "Invalid activation control request", "code": "INVALID_ARGUMENT"}, status=400)
            return
        try:
            if action in {"complete_epoch", "close_epoch"}:
                result = self.server.control_runtime.activation_epoch_control(action, payload.get("activation_epoch_id"), payload.get("ready_commit_digest"), payload.get("expires_at_unix_ms"))  # type: ignore[attr-defined]
                self.send_json(result)
                return
            if action == "prepare":
                workspace = str(payload.get("workspace") or "")
                if os.path.normcase(os.path.abspath(workspace)) != os.path.normcase(str(self.runtime.workspace.root)):
                    raise ToolFailure(
                        "WORKSPACE_MISMATCH",
                        "Activation request workspace does not match the running MCP workspace.",
                        category="validation",
                    )
                result = self.runtime.activation_preflight(
                    operation_id=str(payload.get("operation_id") or ""),
                    expires_at_unix_ms=int(payload.get("expires_at_unix_ms") or 0),
                    allow_acceptance_pending=payload.get("allow_acceptance_pending") is True,
                    source_checkpoint=payload.get("source_checkpoint") if "source_checkpoint" in payload else None,
                    prepare=True,
                )
                result["executor_cleanup_supported"] = True
                self.send_json(result, status=200 if result.get("safe") else 409)
                return
            if action == "verify":
                workspace = str(payload.get("workspace") or "")
                if os.path.normcase(os.path.abspath(workspace)) != os.path.normcase(str(self.runtime.workspace.root)):
                    raise ToolFailure(
                        "WORKSPACE_MISMATCH",
                        "Activation verification workspace does not match the running MCP workspace.",
                        category="validation",
                    )
                source_checkpoint = payload.get("source_checkpoint")
                if not isinstance(source_checkpoint, dict):
                    raise ToolFailure(
                        "CHECKPOINT_REQUIRED",
                        "A source_checkpoint is required for post-cancel activation verification.",
                        category="validation",
                    )
                operation_id = str(payload.get("operation_id") or "")
                result = self.runtime.activation_preflight(
                    operation_id=operation_id,
                    source_checkpoint=source_checkpoint,
                    allow_acceptance_pending=payload.get("allow_acceptance_pending") is True,
                    require_unfenced=True,
                    prepare=False,
                )
                result = {
                    **result,
                    "operation_id": operation_id,
                    "fenced": bool(result.get("fenced")),
                    "fence_operation_id": result.get("fence_operation_id"),
                }
                self.send_json(result, status=200 if result.get("safe") else 409)
                return
            cancelled = self.runtime.cancel_activation(str(payload.get("operation_id") or ""))
            self.send_json({
                "cancelled": cancelled,
                "fenced": bool(self.runtime.activation_fence),
                "fence_operation_id": str(self.runtime.activation_fence.get("operation_id") or "") if self.runtime.activation_fence else None,
            })
        except ToolFailure as exc:
            self.send_json({"error": exc.message, "code": exc.code, "details": exc.details}, status=409)
        except (TypeError, ValueError) as exc:
            self.send_json({"error": str(exc), "code": "INVALID_ARGUMENT"}, status=400)

    def handle_control_workspace(self) -> None:
        if not self.is_authorized():
            self.send_unauthorized()
            return
        if self.headers.get_content_type().lower() != "application/json":
            self.send_json({"error": "Content-Type must be application/json"}, status=415)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_json({"error": "Invalid Content-Length"}, status=400)
            return
        if length <= 0 or length > 65536:
            self.send_json({"error": "Invalid request size"}, status=413)
            return
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            workspace = str(payload.get("workspace", "")).strip()
            if not workspace:
                raise ValueError("workspace is required")
            result = self.runtime.switch_workspace(Path(workspace))
        except ToolFailure as exc:
            self.send_json({"error": exc.message, "code": exc.code, "details": exc.details}, status=409)
            return
        except (OSError, ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            self.send_json({"error": str(exc)}, status=400)
            return
        self.send_json(result)

    def handle_control_roots(self) -> None:
        if not self.is_authorized():
            self.send_unauthorized()
            return
        if self.headers.get_content_type().lower() != "application/json":
            self.send_json({"error": "Content-Type must be application/json"}, status=415)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_json({"error": "Invalid Content-Length"}, status=400)
            return
        if length <= 0 or length > 65536:
            self.send_json({"error": "Invalid request size"}, status=413)
            return
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            roots = payload.get("roots", [])
            if not isinstance(roots, list):
                raise ValueError("roots must be an array")
            result = self.runtime.set_authorized_roots([str(item) for item in roots])
        except ToolFailure as exc:
            self.send_json({"error": exc.message, "code": exc.code, "details": exc.details}, status=409)
            return
        except (OSError, ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            self.send_json({"error": str(exc)}, status=400)
            return
        self.send_json(result)

    def do_POST(self) -> None:
        request_path = self.path.split("?", 1)[0]
        normalized = posixpath.normpath(request_path)
        if normalized == CONTINUATION_CONSENT_HTTP_PATH:
            self.handle_continuation_consent_post()
            return
        if normalized == "/__control/workspace":
            self.handle_control_workspace()
            return
        if normalized == "/__control/roots":
            self.handle_control_roots()
            return
        if normalized == "/__control/activation":
            self.handle_control_activation()
            return
        if normalized == "/__control/hub":
            self.handle_control_hub()
            return
        if normalized == "/oauth/authorize":
            self.handle_oauth_authorize_post()
            return
        if normalized == "/oauth/token":
            self.handle_oauth_token()
            return
        if normalized == "/oauth/register":
            self.handle_oauth_register()
            return
        if normalized != MCP_ENDPOINT_PATH:
            self.send_rpc_error(-32601, "Unknown endpoint", status=404)
            return
        origin = self.headers.get("Origin")
        if origin and not is_allowed_origin(origin):
            self.send_rpc_error(-32600, "Origin denied", status=403)
            return
        if not self.is_authorized():
            self.send_unauthorized()
            return
        if self.headers.get_content_type().lower() != "application/json":
            self.send_rpc_error(-32600, "Content-Type must be application/json", status=415)
            return
        protocol_version = self.headers.get("MCP-Protocol-Version")
        if protocol_version and not protocol_version_is_supported(protocol_version):
            self.send_rpc_error(
                -32600,
                "Unsupported MCP protocol version",
                data={"supported": list(SUPPORTED_PROTOCOL_VERSIONS), "received": protocol_version},
            )
            return
        raw_length = self.headers.get("Content-Length")
        if raw_length is None:
            self.send_rpc_error(-32600, "Content-Length is required", status=411)
            return
        try:
            length = int(raw_length)
        except ValueError:
            self.send_rpc_error(-32600, "Content-Length must be a non-negative integer")
            return
        if length < 0:
            self.send_rpc_error(-32600, "Content-Length must be a non-negative integer")
            return
        if length > MAX_HTTP_REQUEST_BYTES:
            self.close_connection = True
            self.send_rpc_error(
                -32600,
                "Request body exceeds maximum size",
                status=413,
                data={"max_bytes": MAX_HTTP_REQUEST_BYTES},
            )
            return
        body = self.rfile.read(length)
        try:
            request = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self.send_rpc_error(-32700, "Parse error")
            return
        if isinstance(request, list):
            self.send_rpc_error(-32600, "JSON-RPC batch requests are not supported by Streamable HTTP")
            return
        if not isinstance(request, dict):
            self.send_rpc_error(-32600, "Invalid Request")
            return
        try:
            validate_rpc_envelope(request)
        except JsonRpcError as exc:
            self.send_rpc_error(
                exc.code, exc.message, status=200, request_id=response_id(request), data=exc.data
            )
            return
        method = request.get("method")
        body_protocol_version = request_protocol_version(request)
        modern_marker = (
            protocol_version == STATELESS_PROTOCOL_VERSION
            or body_protocol_version == STATELESS_PROTOCOL_VERSION
        )
        if modern_marker and not stateless_http_2026_enabled():
            self.send_rpc_error(
                -32022,
                "MCP 2026-07-28 stateless HTTP is disabled for this deployment",
                status=400,
                request_id=request.get("id"),
                data={
                    "supported": list(LEGACY_PROTOCOL_VERSIONS),
                    "requested": STATELESS_PROTOCOL_VERSION,
                    "disable_with": STATELESS_HTTP_2026_ENV,
                },
            )
            return
        if modern_marker:
            if protocol_version != STATELESS_PROTOCOL_VERSION or body_protocol_version != STATELESS_PROTOCOL_VERSION:
                self.send_rpc_error(
                    -32020,
                    "Header mismatch: MCP-Protocol-Version must match params._meta protocolVersion",
                    status=400,
                    request_id=request.get("id"),
                )
                return
            header_method = self.headers.get("Mcp-Method")
            if header_method != method:
                self.send_rpc_error(
                    -32020,
                    "Header mismatch: required Mcp-Method must match the JSON-RPC method",
                    status=400,
                    request_id=request.get("id"),
                    data={"header": header_method, "body": method},
                )
                return
            body_name = _request_mcp_name(request)
            if method in {"tools/call", "prompts/get", "resources/read"}:
                header_name_raw = self.headers.get("Mcp-Name")
                header_name = _decode_mcp_name_header(header_name_raw) if header_name_raw else None
                if not body_name or header_name != body_name:
                    self.send_rpc_error(
                        -32020,
                        "Header mismatch: required Mcp-Name must match the named request",
                        status=400,
                        request_id=request.get("id"),
                        data={"header": header_name, "body": body_name},
                    )
                    return
            self._runtime = self.server.control_runtime  # type: ignore[attr-defined]
            self._send_session_header = False
            # Seed the transport handle before dispatch as a final guard for
            # wrappers that replace or copy the handler state while invoking
            # the request.  ``handle_rpc`` repeats the same normalization and
            # therefore keeps the exact context used by the tool execution.
            if not str(getattr(self, "_stateless_task_context_id", "") or ""):
                try:
                    _, seeded_task_context_id, _, _ = self._stateless_task_context(request)
                    self._stateless_task_context_id = seeded_task_context_id
                except ValueError:
                    # Preserve the typed JSON-RPC validation boundary in
                    # ``handle_rpc``; this pre-seed is only a best-effort
                    # transport integrity check.
                    pass
            response = self.handle_rpc(request, stateless_2026=True)
            # Keep the MCP-2026 application handle at the transport boundary
            # as a second integrity check.  The dispatcher decorates normal
            # tool results, but a response wrapper/proxy must never be able to
            # drop the handle before it is serialized to the client.
            stateless_task_context_id = str(getattr(self, "_stateless_task_context_id", "") or "")
            if response is not None and stateless_task_context_id:
                self._decorate_stateless_task_context(response, stateless_task_context_id)
            if response is None:
                self.send_response(202)
                self.send_cors_headers()
                self.end_headers()
                return
            error = response.get("error") if isinstance(response, dict) else None
            status = 404 if isinstance(error, dict) and error.get("code") == -32601 else 200
            self.send_json(response, status=status)
            return
        session_id = self.headers.get("Mcp-Session-Id")
        created_session = False
        if method == "initialize":
            if session_id:
                self.send_rpc_error(
                    -32600, "initialize must not include Mcp-Session-Id", request_id=request.get("id")
                )
                return
            try:
                self._runtime = self.server.sessions.create(execution_scoped=True)  # type: ignore[attr-defined]
            except RuntimeError as exc:
                self.send_rpc_error(-32000, str(exc), status=503, request_id=request.get("id"))
                return
            self._send_session_header = True
            created_session = True
        elif session_id:
            try:
                runtime = self.server.sessions.get(session_id)  # type: ignore[attr-defined]
            except StaleHTTPSessionError:
                control_runtime = self.server.control_runtime  # type: ignore[attr-defined]
                self.send_rpc_error(
                    -32023,
                    "MCP session belongs to a different workspace. Reinitialize before calling tools in the current workspace.",
                    status=409,
                    request_id=request.get("id"),
                    data={
                        "code": "STALE_WORKSPACE_CONTEXT",
                        "workspace": str(control_runtime.workspace.root),
                        "workspace_generation": control_runtime.workspace_generation,
                    },
                )
                return
            if runtime is None:
                # Tunnel clients can retain an expired session id while reconnecting.
                # Recreate a compatible initialized session instead of returning a
                # hard 404 that causes an aggressive reconnect loop.
                try:
                    runtime = self.server.sessions.create(execution_scoped=True)  # type: ignore[attr-defined]
                    runtime.initialized = True
                    runtime.protocol_version = protocol_version or PROTOCOL_VERSION
                    self._runtime = runtime
                    self._send_session_header = True
                    created_session = True
                except RuntimeError as exc:
                    self.send_rpc_error(-32000, str(exc), status=503, request_id=request.get("id"))
                    return
            else:
                self._runtime = runtime
                self._send_session_header = True
                if not runtime.initialized:
                    # Authenticated proxy/tunnel clients can retain a session alias
                    # across a Runtime recreation. The alias is intentionally mapped
                    # to the new shared Runtime by HTTPSessionManager; initialize that
                    # fresh Runtime with the caller's protocol before dispatch so the
                    # reconnect does not fail as "Server not initialized".
                    runtime.initialized = True
                    runtime.protocol_version = protocol_version or PROTOCOL_VERSION
            if protocol_version and protocol_version != runtime.protocol_version and method != "notifications/initialized":
                self.send_rpc_error(
                    -32600,
                    "MCP-Protocol-Version does not match the initialized session",
                    request_id=request.get("id"),
                    data={"expected": runtime.protocol_version, "received": protocol_version},
                )
                return
        elif method == "ping":
            self._runtime = self.server.control_runtime  # type: ignore[attr-defined]
        elif method == "notifications/initialized":
            # Some legacy tunnel health probes complete their initialize
            # handshake without returning the server-issued session header on
            # this notification.  It has no stateful effect, so accepting the
            # already-validated no-op is safer than minting an unbound session
            # or rejecting an otherwise healthy probe.  Stateful requests
            # continue to require a session (or use their explicit
            # compatibility path below).
            self.send_response(202)
            self.send_cors_headers()
            self.end_headers()
            return
        elif method in {"server/discover", "tools/list", "tools/call"}:
            # Compatibility path for stateless/proxying MCP clients. The response
            # includes Mcp-Session-Id so capable clients become stateful after the
            # first request. Give each compatibility conversation its own execution
            # context instead of aliasing every pre-initialize ChatWeb call to the
            # process-global task projection.
            try:
                self._runtime = self.server.sessions.create(execution_scoped=True)  # type: ignore[attr-defined]
            except RuntimeError as exc:
                self.send_rpc_error(-32000, str(exc), status=503, request_id=request.get("id"))
                return
            self._runtime.initialized = True
            self._runtime.protocol_version = protocol_version or PROTOCOL_VERSION
            self._send_session_header = True
            created_session = True
        else:
            self.send_rpc_error(-32002, "Server not initialized", request_id=request.get("id"))
            return
        response = self.handle_rpc(request)
        if created_session and response is not None and "error" in response:
            self.server.sessions.delete(self.runtime.http_session_id)  # type: ignore[attr-defined]
            self._send_session_header = False
        if response is None:
            self.send_response(202)
            if getattr(self, "_send_session_header", False):
                self.send_header("Mcp-Session-Id", self.runtime.http_session_id)
            self.send_cors_headers()
            self.end_headers()
            return
        self.send_json(response)

    def handle_rpc(
        self,
        request: dict[str, Any],
        *,
        stateless_2026: bool = False,
    ) -> dict[str, Any] | None:
        runtime = self.runtime
        try:
            trace_context = parse_trace_context(
                self.headers.get("traceparent"),
                self.headers.get("tracestate"),
            )
            if trace_context:
                runtime.request_context.trace_context = trace_context
            dispatch_request = request
            task_context_id = ""
            execution_context_id = ""
            exact_run_recovery_id = ""
            if stateless_2026:
                dispatch_request, task_context_id, execution_context_id, exact_run_recovery_id = self._stateless_task_context(request)
            identity = self._hub_identity_from_request(request)
            if stateless_2026:
                identity["execution_context_id"] = execution_context_id
                runtime.request_context.stateless_task_context_id = task_context_id
                if exact_run_recovery_id:
                    runtime.request_context.stateless_exact_run_recovery_id = exact_run_recovery_id
            if dispatch_request.get("method") == "tools/call":
                envelope_params = dispatch_request.get("params") if isinstance(dispatch_request.get("params"), dict) else {}
                envelope_meta = envelope_params.get("_meta") if isinstance(envelope_params.get("_meta"), dict) else {}
                self.server.control_runtime._record_controller_usage_envelope_observation(  # type: ignore[attr-defined]
                    identity,
                    meta_present=CONTROLLER_USAGE_META_KEY in envelope_meta,
                )
            dispatch_request, controller_usage = controller_usage_request(dispatch_request, identity)
            runtime.request_context.hub_client = identity
            # Resolve the requested workspace before registering the controller
            # client.  Controller leases and task projections must be recorded
            # in the same workspace ledger as the tool call, not in the
            # Runtime's primary project ledger.
            if dispatch_request.get("method") == "tools/call":
                params = dispatch_request.get("params") if isinstance(dispatch_request.get("params"), dict) else {}
                tool_name = str(params.get("name") or "")
                tool_args = params.get("arguments") if isinstance(params.get("arguments"), dict) else {}
                if not runtime.activation_connector_bootstrap_allowed(tool_name):
                    try:
                        runtime._set_request_workspace_scope(tool_name, tool_args)
                    except Exception:
                        # The normal tool dispatch remains the typed error boundary;
                        # this pre-registration hint must never turn it into a raw
                        # HTTP/JSON-RPC failure.
                        pass
            # Stateless MCP task contexts are isolation/selection boundaries,
            # not orchestration authority by themselves. Read the exact
            # request-local store explicitly so a RUN projected in another
            # ChatWeb context can never make a fresh context look owned.
            if stateless_2026 and task_context_id:
                predispatch_state = TaskStateStore(
                    runtime._current_request_workspace_root(),
                    scope_id=f"mcp2026:{task_context_id}",
                ).get()
            else:
                predispatch_state = runtime.task_state.get()
            predispatch_projection = (
                predispatch_state.get("orchestration")
                if isinstance(predispatch_state.get("orchestration"), dict)
                else {}
            )
            predispatch_run_id = str(predispatch_projection.get("run_id") or "").strip()
            predispatch_wave_id = str(predispatch_projection.get("wave_id") or "").strip()
            predispatch_orchestration_authority = bool(predispatch_run_id or predispatch_wave_id)
            runtime._touch_hub_client(identity)
            usage_receipt = None
            deferred_controller_usage = False
            if controller_usage is not None:
                report_run_id = str(controller_usage.get("run_id") or "").strip()
                if predispatch_orchestration_authority and not report_run_id:
                    raise ValueError(
                        "controller usage run_id and wave_id are required when orchestration authority already exists"
                    )
                usage_context = active_controller_usage_context(runtime)
                if usage_context is not None:
                    usage_receipt = record_controller_usage(runtime, controller_usage, usage_context)
                elif tool_call_name(dispatch_request) == "agent_workflow":
                    deferred_controller_usage = True
                else:
                    raise ValueError("controller usage requires a scoped active orchestration run and wave")
            response = dispatch_rpc(runtime, dispatch_request, stateless_2026=stateless_2026)
            self.server.control_runtime._record_successful_rpc_contact(  # type: ignore[attr-defined]
                dispatch_request, response, identity
            )
            self.server.control_runtime._record_activation_bootstrap_rpc_contact(  # type: ignore[attr-defined]
                dispatch_request, response, identity
            )
            if controller_usage is not None and deferred_controller_usage:
                usage_context = active_controller_usage_context(runtime)
                if usage_context is None:
                    raise ValueError(
                        "deferred controller usage requires agent_workflow to create an exact orchestration run and wave"
                    )
                result = response.get("result") if isinstance(response, dict) else None
                structured = result.get("structuredContent") if isinstance(result, dict) else None
                response_orchestration = (
                    structured.get("orchestration")
                    if isinstance(structured, dict) and isinstance(structured.get("orchestration"), dict)
                    else {}
                )
                response_run_id = str(response_orchestration.get("run_id") or "").strip()
                response_wave_id = str(response_orchestration.get("wave_id") or "").strip()
                if (response_run_id, response_wave_id) != usage_context:
                    raise ValueError(
                        "deferred controller usage requires the same agent_workflow request to create the exact orchestration run and wave"
                    )
                usage_receipt = record_controller_usage(runtime, controller_usage, usage_context)
            if response is not None and usage_receipt is not None:
                decorate_controller_usage_status(response, usage_receipt)
            if stateless_2026 and response is not None:
                self._decorate_stateless_task_context(response, task_context_id)
            return response
        except ValueError as exc:
            return jsonrpc_error(response_id(request), -32602, str(exc))
        except ExceptionGroup as exc:
            failure = normalize_exception_group(exc)
            return jsonrpc_error(
                response_id(request),
                -32603,
                failure.message,
                {
                    "code": failure.code,
                    "category": failure.category,
                    "retryable": failure.retryable,
                    "details": failure.details,
                },
            )
        except Exception as exc:  # noqa: BLE001 - HTTP must always answer with JSON-RPC
            return jsonrpc_error(response_id(request), -32603, str(exc))
        finally:
            if hasattr(runtime.request_context, "hub_client"):
                delattr(runtime.request_context, "hub_client")
            if hasattr(runtime.request_context, "trace_context"):
                delattr(runtime.request_context, "trace_context")
            if hasattr(runtime.request_context, "workspace_root"):
                delattr(runtime.request_context, "workspace_root")
            if hasattr(runtime.request_context, "stateless_task_context_id"):
                delattr(runtime.request_context, "stateless_task_context_id")
            if hasattr(runtime.request_context, "stateless_exact_run_recovery_id"):
                delattr(runtime.request_context, "stateless_exact_run_recovery_id")

    def _stateless_task_context(self, request: dict[str, Any]) -> tuple[dict[str, Any], str, str, str]:
        """Return a request copy plus an isolated MCP-2026 application-state context."""
        dispatch_request, task_context_id, execution_context_id, exact_run_recovery_id = resolve_stateless_task_context(
            request,
            identity_from_request=self._hub_identity_from_request,
            recover_exact_run_context=lambda run_id, client_id: self.runtime.stateless_task_context_for_run(
                run_id, logical_client_id=client_id
            ),
        )
        self._stateless_task_context_id = task_context_id
        return dispatch_request, task_context_id, execution_context_id, exact_run_recovery_id

    @staticmethod
    def _decorate_stateless_task_context(response: dict[str, Any], task_context_id: str) -> None:
        result = response.get("result")
        if isinstance(result, dict):
            meta = result.get("_meta")
            if not isinstance(meta, dict):
                meta = {}
                result["_meta"] = meta
            meta[STATELESS_TASK_CONTEXT_META_KEY] = task_context_id
            structured = result.get("structuredContent")
            if isinstance(structured, dict):
                # The tool payload may have populated this field from the
                # request-scoped execution identity (or left it as null).
                # The public MCP-2026 application handle is the minted
                # task_context_id, so it must be authoritative in the
                # structured result as well as in _meta.
                structured["task_context_id"] = task_context_id
        error = response.get("error")
        if isinstance(error, dict):
            data = error.get("data")
            if not isinstance(data, dict):
                data = {}
                error["data"] = data
            data.setdefault("task_context_id", task_context_id)


    def is_authorized(self) -> bool:
        if not self.runtime.auth_enabled():
            return True
        header = self.headers.get("Authorization", "").strip()
        if self.runtime.auth_token is not None:
            if secrets.compare_digest(header, f"Bearer {self.runtime.auth_token}"):
                return True
        if self.runtime.oauth_config is not None and header.startswith("Bearer "):
            token = header[len("Bearer "):]
            if validate_access_token(token, self.runtime.oauth_config, self.oauth_base_url()):
                return True
        return False

    def oauth_base_url(self) -> str:
        cfg = self.runtime.oauth_config
        if cfg is not None and cfg.server_url:
            return cfg.server_url.rstrip("/")
        trust_proxy = truthy_env(os.environ.get(f"{ENV_PREFIX}_TRUST_PROXY_HEADERS"))
        proto = _first_header_value(self.headers.get("X-Forwarded-Proto")) if trust_proxy else ""
        if trust_proxy and not proto:
            proto = _forwarded_header_param(self.headers.get("Forwarded"), "proto")
        host = _safe_external_host(_first_header_value(self.headers.get("X-Forwarded-Host"))) if trust_proxy else ""
        if trust_proxy and not host:
            host = _safe_external_host(_forwarded_header_param(self.headers.get("Forwarded"), "host"))
        if not host:
            host = _safe_external_host(self.headers.get("Host", ""))
        if not host:
            server_address = cast(tuple[Any, ...], self.server.server_address)  # type: ignore[attr-defined]
            bind_host = server_address[0]
            bind_port = server_address[1]
            host = _http_base_for_bind_host(str(bind_host), int(bind_port)).removeprefix("http://")
        if proto not in {"http", "https"}:
            host_without_port = host.rsplit(":", 1)[0].strip("[]")
            proto = "http" if is_loopback_bind_host(host_without_port) else "https"
        return f"{proto}://{host}".rstrip("/")

    def send_unauthorized(self, *, head_only: bool = False) -> None:
        if self.runtime.oauth_config is not None:
            base = self.oauth_base_url()
            www_auth = f'Bearer realm="coding-tools-mcp", resource_metadata="{base}/.well-known/oauth-protected-resource"'
        else:
            www_auth = 'Bearer realm="coding-tools-mcp"'
        self.send_rpc_error(
            -32000,
            "Unauthorized",
            status=401,
            extra_headers={"WWW-Authenticate": www_auth},
            head_only=head_only,
        )

    def handle_oauth_as_metadata(self, *, head_only: bool = False) -> None:
        cfg = self.runtime.oauth_config
        if cfg is None:
            self.send_json({"error": "OAuth not configured"}, status=404, head_only=head_only)
            return
        base = self.oauth_base_url()
        self.send_json(
            {
                "issuer": base,
                "authorization_endpoint": f"{base}/oauth/authorize",
                "token_endpoint": f"{base}/oauth/token",
                "registration_endpoint": f"{base}/oauth/register",
                "response_types_supported": ["code"],
                "grant_types_supported": ["authorization_code"],
                "code_challenge_methods_supported": ["S256"],
                "token_endpoint_auth_methods_supported": list(OAUTH_TOKEN_AUTH_METHODS),
            },
            head_only=head_only,
        )

    def handle_oauth_resource_metadata(self, *, head_only: bool = False) -> None:
        cfg = self.runtime.oauth_config
        if cfg is None:
            self.send_json({"error": "OAuth not configured"}, status=404, head_only=head_only)
            return
        base = self.oauth_base_url()
        self.send_json(
            {"resource": f"{base}{MCP_ENDPOINT_PATH}", "authorization_servers": [base], "bearer_methods_supported": ["header"]},
            head_only=head_only,
        )

    _send_html = send_oauth_html
    _oauth_login_page = staticmethod(oauth_login_page)

    def _read_oauth_body(self) -> bytes | None:
        raw_len = self.headers.get("Content-Length")
        if raw_len is None:
            self.send_json({"error": "Content-Length required"}, status=411)
            return None
        try:
            length = int(raw_len)
        except ValueError:
            self.send_json({"error": "Invalid Content-Length"}, status=400)
            return None
        if not (0 <= length <= OAUTH_MAX_BODY_BYTES):
            self.send_json({"error": "Request body too large"}, status=413)
            return None
        return self.rfile.read(length)

    def handle_oauth_authorize_get(self) -> None:
        cfg = self.runtime.oauth_config
        if cfg is None:
            self.send_json({"error": "OAuth not configured"}, status=404)
            return
        params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query, keep_blank_values=True)
        _p = functools.partial(_first_form_value, params)
        client_id = _p("client_id")
        redirect_uri = _p("redirect_uri")
        code_challenge = _p("code_challenge")
        code_challenge_method = _p("code_challenge_method")
        state = _p("state")
        resource = _p("resource")

        if _p("response_type") != "code":
            self._send_html("<h2>Error</h2><p>response_type must be 'code'</p>", status=400)
            return
        if cfg.registry.get(client_id) is None:
            self._send_html("<h2>Error</h2><p>Unknown client_id</p>", status=400)
            return
        if not cfg.registry.accepts_redirect(client_id, redirect_uri):
            self._send_html("<h2>Error</h2><p>redirect_uri is not registered for this client</p>", status=400)
            return
        if code_challenge_method != "S256" or not valid_pkce_challenge(code_challenge):
            self._send_html("<h2>Error</h2><p>code_challenge_method must be S256 and code_challenge is required</p>", status=400)
            return
        if resource.rstrip("/") != self.oauth_base_url():
            self._send_html("<h2>Error</h2><p>resource must identify this MCP server</p>", status=400)
            return

        self._send_html(self._oauth_login_page(
            client_id=client_id, redirect_uri=redirect_uri, code_challenge=code_challenge,
            code_challenge_method=code_challenge_method, state=state, resource=resource,
        ))

    def handle_oauth_authorize_post(self) -> None:
        cfg = self.runtime.oauth_config
        if cfg is None:
            self.send_json({"error": "OAuth not configured"}, status=404)
            return
        body = self._read_oauth_body()
        if body is None:
            return
        if self.headers.get_content_type().lower() != "application/x-www-form-urlencoded":
            self.send_json({"error": "invalid_request", "error_description": "Content-Type must be application/x-www-form-urlencoded"}, status=400)
            return
        params = urllib.parse.parse_qs(body.decode("utf-8", errors="replace"), keep_blank_values=True)
        _p = functools.partial(_first_form_value, params)
        client_id = _p("client_id")
        redirect_uri = _p("redirect_uri")
        code_challenge = _p("code_challenge")
        code_challenge_method = _p("code_challenge_method")
        state = _p("state")
        resource = _p("resource")
        password = _p("password")

        def fail(error: str, status: int = 400) -> None:
            self._send_html(self._oauth_login_page(
                client_id=client_id, redirect_uri=redirect_uri, code_challenge=code_challenge,
                code_challenge_method=code_challenge_method, state=state, resource=resource,
                error=error,
            ), status=status)

        if cfg.registry.get(client_id) is None or not cfg.registry.accepts_redirect(client_id, redirect_uri):
            fail("Invalid client or redirect URI")
            return
        if code_challenge_method != "S256" or not valid_pkce_challenge(code_challenge):
            fail("Invalid PKCE parameters")
            return
        if resource.rstrip("/") != self.oauth_base_url():
            fail("Invalid resource")
            return
        if not secrets.compare_digest(password, cfg.password):
            fail("Invalid password", status=401)
            return

        code = secrets.token_urlsafe(32)
        now = time.time()
        with cfg.pending_codes_lock:
            expired = [k for k, v in cfg.pending_codes.items() if v["expires_at"] < now]
            for k in expired:
                del cfg.pending_codes[k]
            while len(cfg.pending_codes) >= MAX_PENDING_CODES:
                cfg.pending_codes.pop(next(iter(cfg.pending_codes)))
            cfg.pending_codes[code] = {
                "code_challenge": code_challenge,
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "state": state,
                "expires_at": now + OAUTH_CODE_TTL_SECONDS,
                "server_url": self.oauth_base_url(),
                "resource": resource.rstrip("/"),
            }

        qs = urllib.parse.urlencode({"code": code, **({"state": state} if state else {})})
        sep = "&" if "?" in redirect_uri else "?"
        location = redirect_uri + sep + qs
        self.send_response(302)
        self.send_header("Location", location)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def handle_oauth_token(self) -> None:
        cfg = self.runtime.oauth_config
        if cfg is None:
            self.send_json({"error": "unsupported_grant_type"}, status=400)
            return

        def _err(error: str, description: str) -> None:
            self.log_message("OAuth token error: %s - %s", error, description)
            self.send_json({"error": error, "error_description": description}, status=400)

        body = self._read_oauth_body()
        if body is None:
            return
        content_type = self.headers.get("Content-Type", "").split(";")[0].strip().lower()
        if content_type != "application/x-www-form-urlencoded":
            _err("invalid_request", "Content-Type must be application/x-www-form-urlencoded")
            return
        params = urllib.parse.parse_qs(body.decode("utf-8", errors="replace"), keep_blank_values=True)
        _p = functools.partial(_first_form_value, params)
        grant_type = _p("grant_type")
        code = _p("code")
        redirect_uri = _p("redirect_uri")
        code_verifier = _p("code_verifier")
        client_id = _p("client_id")
        client_secret = _p("client_secret")
        resource = _p("resource").rstrip("/")
        presented_auth_method = "client_secret_post" if client_secret else "none"

        # Also accept HTTP Basic auth for client credentials.
        auth_header = self.headers.get("Authorization", "")
        if auth_header.startswith("Basic ") and (not client_id or not client_secret):
            try:
                decoded = base64.b64decode(auth_header[6:]).decode("utf-8")
                basic_id, _, basic_secret = decoded.partition(":")
                if not client_id:
                    client_id = urllib.parse.unquote(basic_id)
                if not client_secret:
                    client_secret = urllib.parse.unquote(basic_secret)
                presented_auth_method = "client_secret_basic"
            except Exception:  # noqa: BLE001
                pass

        if grant_type != "authorization_code":
            _err("unsupported_grant_type", "Only authorization_code is supported")
            return
        if cfg.registry.get(client_id) is None:
            _err("invalid_client", "Unknown client_id")
            return
        if not cfg.registry.authenticates(client_id, client_secret, presented_auth_method):
            _err("invalid_client", "Invalid client_secret")
            return
        if not code:
            _err("invalid_grant", "code is required")
            return
        if not code_verifier or not (43 <= len(code_verifier) <= 128) or not re.fullmatch(r"[A-Za-z0-9\-._~]+", code_verifier):
            _err("invalid_grant", "Invalid code_verifier")
            return

        with cfg.pending_codes_lock:
            code_data = cfg.pending_codes.pop(code, None)

        if code_data is None:
            _err("invalid_grant", "Unknown or already-used authorization code")
            return
        if time.time() > code_data["expires_at"]:
            _err("invalid_grant", "Authorization code expired")
            return
        if not secrets.compare_digest(code_data["client_id"], client_id):
            _err("invalid_grant", "client_id mismatch")
            return
        if not secrets.compare_digest(code_data["redirect_uri"], redirect_uri):
            _err("invalid_grant", "redirect_uri mismatch")
            return
        if not resource or not secrets.compare_digest(str(code_data.get("resource") or ""), resource):
            _err("invalid_target", "resource mismatch")
            return
        if not verify_pkce(code_verifier, code_data["code_challenge"]):
            _err("invalid_grant", "PKCE verification failed")
            return

        server_url = resource
        access_token = create_access_token(cfg, server_url, client_id=client_id)
        self.send_json({"access_token": access_token, "token_type": "Bearer", "expires_in": cfg.token_ttl})

    def handle_oauth_register(self) -> None:
        cfg = self.runtime.oauth_config
        if cfg is None:
            self.send_json({"error": "OAuth not configured"}, status=404)
            return
        body = self._read_oauth_body()
        if body is None:
            return
        if self.headers.get_content_type().lower() != "application/json":
            self.send_json({"error": "invalid_client_metadata", "error_description": "Content-Type must be application/json"}, status=400)
            return
        try:
            metadata = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self.send_json({"error": "invalid_client_metadata", "error_description": "Body must be valid JSON"}, status=400)
            return
        if not isinstance(metadata, dict):
            self.send_json({"error": "invalid_client_metadata", "error_description": "Metadata must be an object"}, status=400)
            return
        try:
            registered = cfg.registry.register(metadata)
        except ValueError as exc:
            self.send_json({"error": "invalid_client_metadata", "error_description": str(exc)}, status=400)
            return
        self.send_json(registered, status=201)

    def send_cors_headers(self) -> None:
        origin = self.headers.get("Origin")
        if origin and is_allowed_origin(origin):
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Methods", "GET, HEAD, POST, DELETE, OPTIONS")
            self.send_header(
                "Access-Control-Allow-Headers",
                "Accept, Authorization, Content-Type, MCP-Protocol-Version, Mcp-Method, Mcp-Name, Mcp-Session-Id, traceparent, tracestate",
            )

    def send_json(
        self,
        payload: Any,
        *,
        status: int = 200,
        extra_headers: dict[str, str] | None = None,
        head_only: bool = False,
    ) -> None:
        body = json_response_payload(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        if getattr(self, "_send_session_header", False):
            self.send_header("Mcp-Session-Id", self.runtime.http_session_id)
        self.send_cors_headers()
        for name, value in (extra_headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        if not head_only:
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
                # A client-side timeout/cancel may close the socket after the
                # handler has completed the tool call. The response is no
                # longer deliverable, but this transport condition must not
                # produce an unhandled traceback or contaminate the MCP
                # process health signal.
                return

class RuntimeHTTPServer(http.server.ThreadingHTTPServer):
    daemon_threads = True
    request_drain_timeout_seconds = 10.0

    def __init__(
        self,
        address: tuple[str, int],
        handler: type[MCPHandler],
        control_runtime: Runtime,
        runtime_factory: Any,
    ) -> None:
        super().__init__(address, handler)
        self._request_threads_lock = threading.Lock()
        self._request_threads: set[threading.Thread] = set()
        self._closing = False
        self.control_runtime = control_runtime
        self.control_runtime.run_continuation_consent_http_origin = local_continuation_consent_origin(self.server_address)
        self.sessions = HTTPSessionManager(control_runtime)

    def process_request(self, request: Any, client_address: Any) -> None:
        """Track handler threads so runtime shutdown cannot race an active request.

        ``ThreadingMixIn`` deliberately uses daemon request threads here.  That is
        appropriate for a long-lived MCP process, but its default ``server_close``
        does not wait for daemon handlers.  Closing the shared Runtime while one
        of those handlers still owns a SQLite connection can leave a Windows
        temporary ledger locked and can make the next request time out.  Keep the
        daemon behaviour, while recording the exact handlers for a bounded drain.
        """
        with self._request_threads_lock:
            if self._closing:
                self.shutdown_request(request)
                return
            thread = threading.Thread(
                target=self.process_request_thread,
                args=(request, client_address),
                daemon=self.daemon_threads,
            )
            self._request_threads.add(thread)
        try:
            thread.start()
        except BaseException:
            with self._request_threads_lock:
                self._request_threads.discard(thread)
            self.shutdown_request(request)
            raise

    def process_request_thread(self, request: Any, client_address: Any) -> None:
        try:
            super().process_request_thread(request, client_address)
        finally:
            with self._request_threads_lock:
                self._request_threads.discard(threading.current_thread())

    def _drain_request_threads(self) -> bool:
        deadline = time.monotonic() + max(0.0, float(self.request_drain_timeout_seconds))
        current = threading.current_thread()
        while True:
            with self._request_threads_lock:
                active = [thread for thread in self._request_threads if thread is not current and thread.is_alive()]
            if not active:
                return True
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return False
            for thread in active:
                thread.join(timeout=min(0.1, remaining))

    def server_close(self) -> None:
        with self._request_threads_lock:
            self._closing = True
        self.sessions.close()
        self._drain_request_threads()
        self.control_runtime.close()
        super().server_close()


