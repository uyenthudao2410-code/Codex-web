from __future__ import annotations

import secrets
import sys
import threading
import time
from datetime import datetime, timezone
from typing import Any

from .budget_control import BudgetDeadline
from .errors import ToolFailure
from .trace_context import trace_context_metadata


MAX_BACKGROUND_OPERATIONS = 32
BACKGROUND_BUDGET_POLL_SECONDS = 1.0
BACKGROUND_BUDGET_TERMINAL_GRACE_SECONDS = 5.0


def _server_constant(name: str, default: float | int) -> float | int:
    """Honor stable server.py patch points while this behavior lives here."""
    server = sys.modules.get("coding_tools_mcp.server")
    return getattr(server, name, default) if server is not None else default


def background_operation_durability() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "handle_durability": "ledger",
        "execution_durability": "mcp_process",
        "result_durability": "process_runtime",
        "boundaries": {
            "card_or_transport_loss": "survive",
            "same_process_reconnect": "survive",
            "mcp_process_restart": "reconcile_or_orphan",
            "recovery_host_replacement": "lost_or_orphan",
        },
        "restart_safe": False,
        "content_addressed": False,
    }


class BackgroundOperationsMixin:
    """Bounded background tool lifecycle and durable operation receipts."""

    def _background_operation_snapshot(self, operation: dict[str, Any], *, include_result: bool = False) -> dict[str, Any]:
        event = operation["event"]
        finished = event.is_set()
        finished_monotonic = operation.get("finished_monotonic")
        observed_monotonic = float(finished_monotonic) if finished and isinstance(finished_monotonic, (int, float)) else time.monotonic()
        payload: dict[str, Any] = {
            "operation_id": operation["operation_id"],
            "tool": operation["tool"],
            "workspace": operation.get("workspace"),
            "status": "completed" if finished else "running",
            "elapsed_seconds": max(0, int(observed_monotonic - operation["started_monotonic"])),
            "requires_progress_report": not finished,
            "durability": background_operation_durability(),
        }
        if finished and operation.get("finished_at"):
            payload["finished_at"] = operation["finished_at"]
        budget = operation.get("budget")
        if isinstance(budget, BudgetDeadline):
            finished_remaining = operation.get("finished_budget_remaining_seconds")
            payload["budget"] = {
                "max_runtime_seconds": budget.max_runtime_seconds,
                "remaining_seconds": float(finished_remaining) if finished and isinstance(finished_remaining, (int, float)) else budget.remaining_seconds(),
                "exceeded": budget.exceeded,
            }
        if finished and operation.get("error"):
            payload["status"] = "failed"
            payload["error"] = operation["error"]
        if include_result and finished and operation.get("result") is not None:
            payload["result"] = operation["result"]
        return payload

    def _background_operation_cancelled(self) -> bool:
        event = getattr(self.request_context, "background_cancel_event", None)
        return bool(event is not None and event.is_set())

    def _background_operation_remaining_seconds(self) -> float | None:
        budget = getattr(self.request_context, "background_budget", None)
        return budget.remaining_seconds() if isinstance(budget, BudgetDeadline) else None

    def _start_background_tool(self, name: str, arguments: dict[str, Any], *, request_id: str | int | None) -> tuple[dict[str, Any], threading.Event]:
        operation_id = secrets.token_urlsafe(12)
        done = threading.Event()
        worker_done = threading.Event()
        cancel_event = threading.Event()
        finalize_lock = threading.Lock()
        try:
            timeout_seconds = min(int(arguments.get("timeout_seconds", 600)), 3600)
        except (TypeError, ValueError):
            timeout_seconds = 600
        timeout_seconds = max(1, timeout_seconds)
        if name == "agent_workflow":
            try:
                workflow_runtime_seconds = min(max(1, int(arguments.get("max_runtime_seconds", 600))), 600)
            except (TypeError, ValueError):
                workflow_runtime_seconds = 600
            timeout_seconds = min(timeout_seconds, workflow_runtime_seconds)
        budget = BudgetDeadline(max_runtime_seconds=timeout_seconds)
        hub_identity = dict(self._current_hub_client() or {})
        stateless_task_context_id = self._current_stateless_task_context_id()
        trace_context = dict(getattr(self.request_context, "trace_context", {}) or {})
        workspace_root = getattr(self.request_context, "workspace_root", None)
        trace_metadata = trace_context_metadata(trace_context)
        operation: dict[str, Any] = {
            "operation_id": operation_id,
            "tool": name,
            "workspace": str(workspace_root or self.workspace.root),
            "execution_context_id": str(hub_identity.get("execution_context_id") or "")[:64],
            "started_monotonic": time.monotonic(),
            "started_at": datetime.now(timezone.utc).isoformat(),
            "event": done,
            "result": None,
            "error": None,
            "budget": budget,
            "cancel_event": cancel_event,
            "finalized": False,
        }
        current_task = self.task_state.get()
        projection = current_task.get("orchestration") if isinstance(current_task.get("orchestration"), dict) else {}
        self.orchestration_ledger.start_background_operation(
            operation_id=operation_id,
            server_instance_id=self.process_instance_id,
            tool=name,
            task_id=str(current_task.get("task_id") or ""),
            run_id=str(projection.get("run_id") or ""),
            wave_id=str(projection.get("wave_id") or ""),
            summary={
                "phase": str(arguments.get("phase") or ""),
                "objective": str(arguments.get("objective") or "")[:1_000],
                "request_id": str(request_id or ""),
                "durability": background_operation_durability(),
                **trace_metadata,
            },
        )

        def finalize_operation(*, status: str, error: dict[str, Any] | None, summary: dict[str, Any]) -> bool:
            with finalize_lock:
                if operation.get("finalized"):
                    return False
                operation["finalized"] = True
                if error is not None:
                    operation["error"] = error
                operation["finished_monotonic"] = time.monotonic()
                operation["finished_at"] = datetime.now(timezone.utc).isoformat()
                operation["finished_budget_remaining_seconds"] = budget.remaining_seconds()
                try:
                    self.orchestration_ledger.finish_background_operation(operation_id, status=status, summary=summary)
                finally:
                    done.set()
                return True

        def worker() -> None:
            previous = {
                "background_cancel_event": getattr(self.request_context, "background_cancel_event", None),
                "background_budget": getattr(self.request_context, "background_budget", None),
                "hub_client": getattr(self.request_context, "hub_client", None),
                "stateless_task_context_id": getattr(self.request_context, "stateless_task_context_id", None),
                "trace_context": getattr(self.request_context, "trace_context", None),
                "workspace_root": getattr(self.request_context, "workspace_root", None),
            }
            had = {name: hasattr(self.request_context, name) for name in previous}
            self.request_context.background_cancel_event = cancel_event
            self.request_context.background_budget = budget
            if hub_identity:
                self.request_context.hub_client = dict(hub_identity)
            if stateless_task_context_id:
                self.request_context.stateless_task_context_id = stateless_task_context_id
            if trace_context:
                self.request_context.trace_context = dict(trace_context)
            if workspace_root:
                self.request_context.workspace_root = workspace_root
            try:
                operation["result"] = self._call_tool_sync(name, arguments, request_id=request_id)
            except Exception as exc:  # noqa: BLE001 - background errors must become inspectable state
                operation["error"] = {"code": "BACKGROUND_OPERATION_FAILED", "message": str(exc), "category": "runtime", "retryable": False}
            finally:
                for attribute, value in previous.items():
                    restore_none_by_deletion = attribute in {"background_cancel_event", "background_budget"}
                    if had[attribute] and not (restore_none_by_deletion and value is None):
                        setattr(self.request_context, attribute, value)
                    else:
                        try:
                            delattr(self.request_context, attribute)
                        except AttributeError:
                            pass
                try:
                    result = operation.get("result")
                    result_status = ""
                    if isinstance(result, dict):
                        structured = result.get("structuredContent")
                        if isinstance(structured, dict):
                            result_status = str(structured.get("status") or structured.get("phase") or structured.get("workflow") or "")[:100]
                    budget_error = operation.get("budget_error")
                    error = budget_error if isinstance(budget_error, dict) else operation.get("error")
                    finalize_operation(
                        status="timed_out" if isinstance(budget_error, dict) else "failed" if error else "completed",
                        error=error if isinstance(error, dict) else None,
                        summary={"result_available_in_memory": result is not None, "result_status": result_status, "error": error, "worker_terminalized": True},
                    )
                finally:
                    worker_done.set()

        def watchdog() -> None:
            while not done.is_set():
                try:
                    budget.check()
                except ToolFailure as exc:
                    budget_error = {"code": exc.code, "message": exc.message, "category": exc.category, "retryable": False}
                    operation["budget_error"] = budget_error
                    cancel_event.set()
                    if worker_done.wait(float(_server_constant("BACKGROUND_BUDGET_TERMINAL_GRACE_SECONDS", BACKGROUND_BUDGET_TERMINAL_GRACE_SECONDS))):
                        return
                    finalize_operation(
                        status="timed_out",
                        error=budget_error,
                        summary={"error": budget_error, "budget": exc.details, "worker_terminalized": False, "terminalization_grace_exceeded": True},
                    )
                    return
                done.wait(float(_server_constant("BACKGROUND_BUDGET_POLL_SECONDS", BACKGROUND_BUDGET_POLL_SECONDS)))

        with self.background_operations_lock:
            finished_ids = [key for key, item in self.background_operations.items() if item["event"].is_set()]
            while len(self.background_operations) >= int(_server_constant("MAX_BACKGROUND_OPERATIONS", MAX_BACKGROUND_OPERATIONS)) and finished_ids:
                self.background_operations.pop(finished_ids.pop(0), None)
            self.background_operations[operation_id] = operation
        threading.Thread(target=worker, name=f"mcp-bg-{name}-{operation_id[:6]}", daemon=True).start()
        threading.Thread(target=watchdog, name=f"mcp-budget-{operation_id[:6]}", daemon=True).start()
        return operation, done
