from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def hub_client_activity_state(
    last_seen_at: object,
    *,
    active_seconds: float,
    recent_seconds: float = 600.0,
) -> str:
    text = str(last_seen_at or "").strip()
    if not text:
        return "NO_SIGNAL"
    try:
        observed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return "NO_SIGNAL"
    if observed.tzinfo is None:
        observed = observed.replace(tzinfo=timezone.utc)
    age_seconds = max(
        0.0,
        datetime.now(timezone.utc).timestamp() - observed.astimezone(timezone.utc).timestamp(),
    )
    active_window = max(0.0, float(active_seconds))
    if age_seconds <= active_window:
        return "ACTIVE"
    if age_seconds <= max(active_window, float(recent_seconds)):
        return "RECENT"
    return "NO_SIGNAL"


def runtime_activity_snapshot(
    runtime: Any,
    *,
    write_active: bool = False,
    delegations: list[dict[str, Any]] | None = None,
    limit: int = 8,
) -> dict[str, Any]:
    bounded_limit = max(1, min(int(limit), 20))
    managed = runtime.execution_resource_governor.snapshot(limit=max(12, bounded_limit))
    active_job_states = {"starting", "running", "terminating", "orphaned"}
    managed_jobs = [
        dict(item)
        for item in (managed.get("jobs") or [])
        if str(item.get("lifecycle_state") or "").lower() in active_job_states
    ][:bounded_limit]
    with runtime.sessions_lock:
        live_exec_sessions = sum(
            1 for session in runtime.sessions.values() if session.process.poll() is None
        ) + max(0, int(runtime.starting_sessions))
    with runtime.background_operations_lock:
        active_background = [
            runtime._background_operation_snapshot(item)
            for item in runtime.background_operations.values()
            if item.get("workspace") == str(runtime.workspace.root)
            and item.get("event") is not None
            and not item["event"].is_set()
        ][:bounded_limit]
    terminal_delegations = {"completed", "failed", "cancelled", "stopped", "rejected"}
    active_delegations = [
        item
        for item in (delegations or [])
        if str(item.get("status") or "").strip()
        and str(item.get("status") or "").lower() not in terminal_delegations
    ]
    active_tool_calls = max(0, int(runtime.active_tool_calls))
    active_commands = max(
        max(0, int(managed.get("active_command_count") or 0)),
        live_exec_sessions,
    )
    state = (
        "DELEGATING"
        if active_delegations
        else "WRITING"
        if write_active
        else "ACTIVE"
        if active_tool_calls or active_commands or active_background
        else "IDLE"
    )
    return {
        "schema_version": 1,
        "state": state,
        "active": state != "IDLE",
        "active_tool_calls": active_tool_calls,
        "active_commands": active_commands,
        "active_background_operations": len(active_background),
        "active_delegations": len(active_delegations),
        "write_active": bool(write_active),
        "managed_jobs": managed_jobs,
        "background_operations": [
            {
                key: item.get(key)
                for key in ("operation_id", "tool", "status", "elapsed_seconds")
            }
            for item in active_background
        ],
    }


class RuntimeActivityMixin:
    hub_client_activity_state = staticmethod(hub_client_activity_state)
    runtime_activity_snapshot = runtime_activity_snapshot

    def _record_successful_rpc_contact(
        self,
        request: dict[str, Any],
        response: dict[str, Any] | None,
        identity: dict[str, Any],
    ) -> None:
        if request.get("method") == "tools/call" and isinstance(response, dict) and "error" not in response:
            self._record_client_contact(identity, method="tools/call")

    def _record_client_contact(self, identity: dict[str, Any], *, method: str) -> None:
        if str(method or "").strip() != "tools/call":
            return
        client_id = str(identity.get("client_id") or "").strip()
        client_type = str(identity.get("client_type") or "client").strip()
        if not client_id or client_type != "chatweb":
            return
        capabilities = identity.get("capabilities") if isinstance(identity.get("capabilities"), dict) else {}
        receipt = {
            "client_id": client_id,
            "client_type": client_type,
            "client_name": str(capabilities.get("client_name") or "")[:100],
            "client_version": str(capabilities.get("client_version") or "")[:50],
            "method": "tools/call",
            "contract_sha256": str(self.tool_contract.get("sha256") or ""),
            "process_instance_id": self.process_instance_id,
            "server_instance_id": self.server_instance_id,
            "observed_at": datetime.now(timezone.utc).isoformat(),
        }
        with self.tool_contact_lock:
            self.tool_contact_receipts[self._hub_client_record_id(identity)] = receipt

    def connector_client_contact(self, *, blocking: bool = True) -> dict[str, Any]:
        acquired = self.tool_contact_lock.acquire(blocking=blocking)
        if not acquired:
            return {
                "observed": False,
                "current_contract_contact": False,
                "method": None,
                "contract_sha256": None,
                "observed_at": None,
                "client_id": None,
                "client_name": None,
                "process_instance_id": None,
                "server_instance_id": None,
                "snapshot_busy": True,
            }
        try:
            candidates = [dict(receipt) for receipt in self.tool_contact_receipts.values()]
        finally:
            self.tool_contact_lock.release()
        latest = max(candidates, key=lambda item: str(item.get("observed_at") or ""), default=None)
        current_sha = str(self.tool_contract.get("sha256") or "")
        current = bool(
            latest
            and str(latest.get("client_type") or "") == "chatweb"
            and str(latest.get("method") or "") == "tools/call"
            and str(latest.get("contract_sha256") or "") == current_sha
            and str(latest.get("process_instance_id") or "") == self.process_instance_id
            and str(latest.get("server_instance_id") or "") == self.server_instance_id
        )
        return {
            "observed": latest is not None,
            "current_contract_contact": current,
            "method": str((latest or {}).get("method") or "") or None,
            "contract_sha256": str((latest or {}).get("contract_sha256") or "") or None,
            "observed_at": str((latest or {}).get("observed_at") or "") or None,
            "client_id": str((latest or {}).get("client_id") or "") or None,
            "client_name": str((latest or {}).get("client_name") or "") or None,
            "process_instance_id": str((latest or {}).get("process_instance_id") or "") or None,
            "server_instance_id": str((latest or {}).get("server_instance_id") or "") or None,
            "snapshot_busy": False,
        }
