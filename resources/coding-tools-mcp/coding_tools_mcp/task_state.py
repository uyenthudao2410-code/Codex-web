from __future__ import annotations

import copy
import errno
import hashlib
import json
import os
import re
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .artifact_refs import command_output_artifact_ref
from .landlock_exec import landlock_status_payload


STATE_VERSION = 2
MAX_EVENTS = 100
MAX_RESULTS = 20
MAX_FILES = 500
MAX_TEXT = 16_000
STALE_ACTIVE_SECONDS = 90
WINDOWS_ATOMIC_REPLACE_ATTEMPTS = 5
WINDOWS_ATOMIC_REPLACE_BASE_DELAY_SECONDS = 0.025
WINDOWS_ATOMIC_REPLACE_WINERRORS = frozenset({5, 32})
WINDOWS_ATOMIC_REPLACE_ERRNOS = frozenset({errno.EACCES, errno.EPERM, errno.EBUSY})

TEST_COMMAND_RE = re.compile(
    r"(?:^|\s)(?:pytest|python\s+-m\s+pytest|npm\s+(?:run\s+)?test|pnpm\s+(?:run\s+)?test|"
    r"yarn\s+test|jest|vitest|cargo\s+test|go\s+test|mvn(?:w)?\s+test|gradle(?:w)?\s+test|"
    r"dotnet\s+test|ctest)(?:\s|$)",
    re.IGNORECASE,
)
BUILD_COMMAND_RE = re.compile(
    r"(?:^|\s)(?:npm\s+run\s+(?:build|dist|package)|pnpm\s+(?:run\s+)?(?:build|dist)|"
    r"yarn\s+(?:build|dist)|electron-builder|cargo\s+build|go\s+build|mvn(?:w)?\s+package|"
    r"gradle(?:w)?\s+build|dotnet\s+(?:build|publish)|python\s+-m\s+build|pyinstaller)(?:\s|$)",
    re.IGNORECASE,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def classify_command(command: str) -> str:
    if TEST_COMMAND_RE.search(command):
        return "test"
    if BUILD_COMMAND_RE.search(command):
        return "build"
    return "command"


def command_payload_succeeded(payload: dict[str, Any]) -> bool:
    """Return true only for a normal successful command terminal state."""
    status = str(payload.get("status") or "").strip().lower()
    if bool(payload.get("timed_out")) or bool(payload.get("killed")):
        return False
    if status in {
        "timeout",
        "timed_out",
        "terminated",
        "killed",
        "cancelled",
        "canceled",
        "failed",
        "error",
    }:
        return False
    if status and status not in {"exited", "completed", "passed"}:
        return False
    return payload.get("exit_code") == 0


def _text(value: Any, limit: int = MAX_TEXT) -> str:
    return str(value or "")[:limit]


def _default_state() -> dict[str, Any]:
    now = utc_now()
    return {
        "version": STATE_VERSION,
        "task_id": "",
        "orchestration": {},
        "objective": "",
        "status": "idle",
        "steps": [],
        "current_step": "",
        "current_command": None,
        "last_command_result": None,
        "completion_report": None,
        "completion_report_id": "",
        "completion_report_acknowledged_id": "",
        "completion_report_acknowledged_at": None,
        "test_results": [],
        "build_results": [],
        "last_build_report": None,
        "modified_files": [],
        "failure": None,
        "next_step": "",
        "created_at": now,
        "updated_at": now,
        "events": [],
    }


def _replace_atomic(source: Path, target: Path) -> None:
    """Retry only transient Windows sharing/access failures around atomic replace."""
    for attempt in range(WINDOWS_ATOMIC_REPLACE_ATTEMPTS):
        try:
            os.replace(source, target)
            return
        except OSError as exc:
            retryable = bool(
                os.name == "nt"
                and (
                    getattr(exc, "winerror", None) in WINDOWS_ATOMIC_REPLACE_WINERRORS
                    or exc.errno in WINDOWS_ATOMIC_REPLACE_ERRNOS
                )
            )
            if not retryable or attempt + 1 >= WINDOWS_ATOMIC_REPLACE_ATTEMPTS:
                raise
            time.sleep(WINDOWS_ATOMIC_REPLACE_BASE_DELAY_SECONDS * (attempt + 1))


class TaskStateStore:
    """Workspace-local, atomic task state used across browser chats and MCP restarts."""

    def __init__(self, workspace: Path, *, scope_id: str = "") -> None:
        self.workspace = workspace.resolve()
        self.scope_id = str(scope_id or "").strip()
        root_state_dir = self.workspace / ".coding-tools"
        if self.scope_id:
            scope_digest = hashlib.sha256(
                self.scope_id.encode("utf-8", errors="surrogatepass")
            ).hexdigest()[:24]
            self.state_dir = root_state_dir / "task-contexts"
            self.path = self.state_dir / f"{scope_digest}.json"
            self.history_path = self.state_dir / f"{scope_digest}-history.json"
        else:
            self.state_dir = root_state_dir
            self.path = self.state_dir / "task-state.json"
            self.history_path = self.state_dir / "task-history.json"
        self._lock = threading.RLock()

    @property
    def state_file_display(self) -> str:
        try:
            return self.path.relative_to(self.workspace).as_posix()
        except ValueError:
            return str(self.path)

    def get(self) -> dict[str, Any]:
        with self._lock:
            return copy.deepcopy(self._read())

    @staticmethod
    def _completion_report_id(report: dict[str, Any]) -> str:
        encoded = json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8", errors="surrogatepass"
        )
        return hashlib.sha256(encoded).hexdigest()

    @classmethod
    def _pending_completion_report_from_state(cls, state: dict[str, Any]) -> dict[str, Any] | None:
        report = state.get("completion_report")
        if not isinstance(report, dict) or report.get("operator_visible_required") is not True:
            return None
        report_id = str(state.get("completion_report_id") or cls._completion_report_id(report))
        if str(state.get("completion_report_acknowledged_id") or "") == report_id:
            return None
        current = report.get("current_state") if isinstance(report.get("current_state"), dict) else {}
        return {
            "report_id": report_id,
            "accepted_or_not": _text(report.get("accepted_or_not"), 200),
            "command_id": _text(report.get("command_id"), 200),
            "orchestration_state": _text(current.get("orchestration_state"), 100),
            "next_critical_action": _text(report.get("next_critical_action"), 1000),
        }

    def pending_completion_report(self) -> dict[str, Any] | None:
        with self._lock:
            pending = self._pending_completion_report_from_state(self._read())
            return copy.deepcopy(pending) if pending is not None else None

    def ack_completion_report(self, report_id: str) -> dict[str, Any]:
        expected = str(report_id or "").strip()
        with self._lock:
            state = self._read()
            pending = self._pending_completion_report_from_state(state)
            if pending is None:
                raise ValueError("No operator completion report is awaiting acknowledgement.")
            if not expected or expected != pending["report_id"]:
                raise ValueError("completion report acknowledgement does not match the pending report id")
            state["completion_report_acknowledged_id"] = expected
            state["completion_report_acknowledged_at"] = utc_now()
            orchestration_state = str(pending.get("orchestration_state") or "").upper()
            if orchestration_state == "ACCEPTING":
                state["current_step"] = "Waiting for ChatWeb Sol acceptance"
            elif orchestration_state == "REPLAN":
                state["current_step"] = "Replan report acknowledged"
            elif orchestration_state == "BLOCKED":
                state["current_step"] = "Blocked report acknowledged"
            elif orchestration_state == "ABORTED":
                state["current_step"] = "Aborted report acknowledged"
            else:
                state["current_step"] = "Operator report acknowledged"
            self._event(state, "operator_completion_report_acknowledged", {"report_id": expected})
            return self._write(state)

    def _require_no_pending_report(self, state: dict[str, Any], operation: str) -> None:
        pending = self._pending_completion_report_from_state(state)
        if pending is not None:
            raise RuntimeError(
                f"operator completion report {pending['report_id']} must be acknowledged before {operation}"
            )

    def ensure_started(self, objective: str, *, current_step: str = "") -> dict[str, Any]:
        """Create a visible task automatically when a client skips explicit task setup."""
        with self._lock:
            state = self._read()
            if self._has_task(state) and str(state.get("status", "")) not in {"completed", "failed", "stopped"}:
                return copy.deepcopy(state)
            if self._has_task(state):
                self._require_no_pending_report(state, "starting a replacement task")
                self._archive(state, "finished")
            state = _default_state()
            state["task_id"] = uuid.uuid4().hex
            state["objective"] = _text(objective or "Workspace task")
            state["status"] = "active"
            state["current_step"] = _text(current_step)
            self._event(state, "task_auto_started", {"objective": state["objective"]})
            return self._write(state)

    def clear(self) -> dict[str, Any]:
        with self._lock:
            state = self._read()
            if self._has_task(state):
                self._require_no_pending_report(state, "clearing the task")
                self._archive(state, "cleared")
            if self.path.exists():
                self.path.unlink()
            return _default_state()

    def history(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._lock:
            raw = self._read_json(self.history_path, [])
            return copy.deepcopy(raw[-max(1, min(limit, 100)):][::-1] if isinstance(raw, list) else [])

    def pause(self, reason: str = "") -> dict[str, Any]:
        with self._lock:
            state = self._read()
            if not self._has_task(state):
                return state
            state["status"] = "paused"
            state["pause_reason"] = _text(reason, 2000)
            self._event(state, "task_paused", {"reason": state["pause_reason"]})
            return self._write(state)

    def resume(self, next_step: str = "") -> dict[str, Any]:
        with self._lock:
            state = self._read()
            if not self._has_task(state):
                return state
            self._require_no_pending_report(state, "resuming the task")
            state["status"] = "active"
            state["pause_reason"] = ""
            if next_step:
                state["next_step"] = _text(next_step)
            self._event(state, "task_resumed", {"next_step": state.get("next_step", "")})
            return self._write(state)

    def update(self, changes: dict[str, Any], *, event: str = "task_updated") -> dict[str, Any]:
        with self._lock:
            state = self._read()
            if changes.get("objective") and not self._has_task(state):
                # Discard anonymous tool traces left before a model explicitly started a task.
                state = _default_state()
            elif changes.get("objective") and self._has_task(state) and changes.get("new_task"):
                self._require_no_pending_report(state, "superseding the task")
                self._archive(state, "superseded")
                state = _default_state()
            if changes.get("objective") and not state.get("task_id"):
                state["task_id"] = uuid.uuid4().hex
            for key in ("objective", "status", "current_step", "next_step"):
                if key in changes:
                    state[key] = _text(changes[key])
            if "orchestration" in changes:
                orchestration = changes.get("orchestration")
                state["orchestration"] = copy.deepcopy(orchestration) if isinstance(orchestration, dict) else {}
            if "failure" in changes:
                failure = changes["failure"]
                state["failure"] = None if failure in (None, "") else _text(failure)
            if "steps" in changes:
                state["steps"] = self._normalize_steps(changes["steps"])
            completed = {str(item) for item in changes.get("complete_step_ids", [])}
            if completed:
                for step in state["steps"]:
                    if step["id"] in completed:
                        step["status"] = "completed"
                        step["updated_at"] = utc_now()
            self._event(state, event, {"fields": sorted(changes)})
            return self._write(state)

    def set_orchestration_projection(self, projection: dict[str, Any], *, event: str = "orchestration_projected") -> dict[str, Any]:
        """Persist the compact current view; the SQLite ledger remains history authority."""
        with self._lock:
            state = self._read()
            if not self._has_task(state):
                return state
            state["orchestration"] = copy.deepcopy(projection)
            self._event(state, event, {"state": str(projection.get("orchestration_state", ""))})
            return self._write(state)

    def set_completion_report(self, report: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            state = self._read()
            if not self._has_task(state):
                return state
            report_id = self._completion_report_id(report)
            previous_id = str(state.get("completion_report_id") or "")
            state["completion_report"] = copy.deepcopy(report)
            state["completion_report_id"] = report_id
            if previous_id != report_id:
                state["completion_report_acknowledged_id"] = ""
                state["completion_report_acknowledged_at"] = None
            accepted_or_not = str(report.get("accepted_or_not") or "")
            current = report.get("current_state") if isinstance(report.get("current_state"), dict) else {}
            orchestration_state = str(current.get("orchestration_state") or "").upper()
            failed = accepted_or_not in {"COMMAND_FAILED", "COMMAND_TERMINATED"}
            if orchestration_state == "ACCEPTING":
                state["current_step"] = "Acceptance decision - operator report required"
            elif orchestration_state == "REPLAN":
                state["current_step"] = "Replan required - operator report required"
            elif orchestration_state == "BLOCKED":
                state["current_step"] = "Blocked - operator report required"
            elif orchestration_state == "ABORTED":
                state["current_step"] = "Aborted - operator report required"
            else:
                state["current_step"] = "Command failed - operator report required" if failed else "Completed - operator report required"
            state["next_step"] = _text(report.get("next_critical_action"), 4000)
            self._event(state, "command_completion_report_required", {
                "command_id": _text(report.get("command_id"), 200),
                "accepted_or_not": _text(accepted_or_not, 200),
                "report_id": report_id,
            })
            return self._write(state)

    def find_command_completion(self, command_id: str) -> dict[str, Any] | None:
        needle = str(command_id or "").strip()
        if not needle:
            return None
        with self._lock:
            candidates = [self._read()]
            history = self._read_json(self.history_path, [])
            if isinstance(history, list):
                candidates.extend(reversed(history[-100:]))
            for state in candidates:
                if not isinstance(state, dict):
                    continue
                report = state.get("completion_report")
                if isinstance(report, dict) and str(report.get("command_id") or "") == needle:
                    return copy.deepcopy(report)
        return None

    def record_tool_result(self, name: str, args: dict[str, Any], payload: dict[str, Any]) -> None:
        if name.startswith("task_state_") or name == "task_history_list":
            return
        with self._lock:
            state = self._read()
            if not self._has_task(state):
                return
            terminal_orchestration = self._has_terminal_orchestration(state)
            ok = payload.get("ok", True) is not False
            if name in {"apply_patch", "apply_changes_and_verify", "agent_workflow", "file_batch", "document_workflow", "document_create", "document_convert"} and ok and not args.get("dry_run"):
                affected_files = payload.get("affected_files", [])
                if name == "agent_workflow" and isinstance(payload.get("execution"), dict):
                    nested = payload["execution"].get("affected_files")
                    if isinstance(nested, list):
                        affected_files = nested
                affected_files = affected_files if isinstance(affected_files, list) else []
                for item in affected_files:
                    if isinstance(item, dict) and item.get("path"):
                        self._add_file(state, str(item["path"]), str(item.get("operation", "update")))
                self._event(state, "files_modified", {"count": len(affected_files)})
            elif name == "exec_command":
                projection = state.get("orchestration") if isinstance(state.get("orchestration"), dict) else {}
                projected_run = str(projection.get("run_id") or "")
                execution_owner = payload.get("execution_owner") if isinstance(payload.get("execution_owner"), dict) else {}
                owner_run = str(execution_owner.get("run_id") or "")
                if projected_run and not terminal_orchestration and owner_run != projected_run:
                    return
                self._record_command_payload(state, _text(args.get("cmd"), 4000), payload)
            elif name == "command_control":
                action = str(args.get("action", "poll")).lower()
                current = state.get("current_command")
                if isinstance(current, dict) and action in {"poll", "write", "kill"}:
                    current_id = str(current.get("session_id") or "")
                    handles = {
                        str(value)
                        for value in (
                            args.get("command_id"),
                            args.get("session_id"),
                            payload.get("command_id"),
                            payload.get("session_id"),
                        )
                        if str(value or "").strip()
                    }
                    if current_id and current_id in handles:
                        if action in {"poll", "write"}:
                            self._record_command_payload(
                                state,
                                _text(current.get("command"), 4000),
                                payload,
                            )
                        elif action == "kill":
                            current["status"] = _text(payload.get("status", "terminated"), 100)
                            current["finished_at"] = utc_now()
                            state["last_command_result"] = {
                                "command_id": current_id,
                                "kind": _text(current.get("kind", "command"), 100),
                                "status": current["status"],
                                "result_status": "failed",
                                "exit_code": payload.get("exit_code"),
                                "duration_ms": payload.get("elapsed_ms"),
                                "finished_at": current["finished_at"],
                            }
                            state["current_command"] = None
                            self._event(state, "command_terminated", {"session_id": current_id})
            elif name == "write_stdin":
                current = state.get("current_command")
                if isinstance(current, dict) and current.get("session_id") == payload.get("session_id"):
                    self._record_command_payload(state, _text(current.get("command"), 4000), payload)
            elif name == "kill_session":
                current = state.get("current_command")
                if isinstance(current, dict) and current.get("session_id") == args.get("session_id"):
                    current["status"] = _text(payload.get("status", "terminated"), 100)
                    current["finished_at"] = utc_now()
                    state["last_command_result"] = {
                        "command_id": _text(current.get("session_id"), 200),
                        "kind": _text(current.get("kind", "command"), 100),
                        "status": current["status"],
                        "result_status": "failed",
                        "exit_code": payload.get("exit_code"),
                        "duration_ms": payload.get("elapsed_ms"),
                        "finished_at": current["finished_at"],
                    }
                    state["current_command"] = None
                    self._event(state, "command_terminated", {"session_id": args.get("session_id")})
            if not ok and name not in {"task_state_get", "task_state_update", "task_state_clear"} and not terminal_orchestration:
                error = payload.get("error") if isinstance(payload.get("error"), dict) else {}
                state["failure"] = _text(error.get("message") or f"{name} failed")
                self._event(state, "tool_failed", {"tool": name, "code": error.get("code")})
            elif ok and not terminal_orchestration:
                state["failure"] = None
                if name == "document_workflow":
                    action = str(args.get("action", "inspect")).lower()
                    if action == "inspect":
                        state["status"] = "waiting"
                        state["current_step"] = "Waiting for model"
                        state["next_step"] = "Generate the result from the inspected content, then save it once."
                    elif action in {"create", "convert", "rebuild"}:
                        state["status"] = "completed"
                        state["current_step"] = "Completed"
                        state["next_step"] = "Review or use the generated document."
                elif name == "agent_workflow":
                    phase = str(payload.get("phase", args.get("phase", ""))).lower()
                    if phase == "prepare":
                        state["status"] = "waiting"
                        state["current_step"] = "Waiting for model"
            self._write(state)

    def record_command_started(
        self,
        command: str,
        session_id: str,
        workdir: str,
        *,
        owner_run_id: str = "",
        owner_wave_id: str = "",
    ) -> None:
        with self._lock:
            state = self._read()
            if not self._has_task(state):
                return
            terminal_orchestration = self._has_terminal_orchestration(state)
            projection = state.get("orchestration") if isinstance(state.get("orchestration"), dict) else {}
            projected_run = str(projection.get("run_id") or "")
            projected_wave = str(projection.get("wave_id") or "")
            if not terminal_orchestration and projected_run and str(owner_run_id or "") != projected_run:
                return
            if not terminal_orchestration and projected_wave and str(owner_wave_id or "") != projected_wave:
                return
            state["current_command"] = {
                "command": _text(command, 4000),
                "kind": classify_command(command),
                "session_id": session_id,
                "workdir": _text(workdir, 2000),
                "status": "running",
                "started_at": utc_now(),
            }
            self._event(state, "command_started", {"command": _text(command, 500), "session_id": session_id})
            self._write(state)

    def record_build_report(self, report: dict[str, Any]) -> None:
        with self._lock:
            state = self._read()
            if not self._has_task(state):
                project = report.get("project") if isinstance(report.get("project"), dict) else {}
                state["objective"] = f"Build and verify {_text(project.get('name') or 'project', 500)}"
                state["task_id"] = uuid.uuid4().hex
                state["status"] = "active"
            terminal_orchestration = self._has_terminal_orchestration(state)
            test_result = report.get("test_result")
            build_result = report.get("build_result")
            if isinstance(test_result, dict):
                state["test_results"] = (state["test_results"] + [test_result])[-MAX_RESULTS:]
            if isinstance(build_result, dict):
                state["build_results"] = (state["build_results"] + [build_result])[-MAX_RESULTS:]
            state["last_build_report"] = copy.deepcopy(report)
            status = str(report.get("overall_status", "unknown"))
            if not terminal_orchestration:
                state["status"] = "completed" if status == "passed" else "failed"
                state["failure"] = None if status == "passed" else _text(report.get("failure") or "Build verification failed")
                state["next_step"] = (
                    "Review or publish the verified artifacts."
                    if status == "passed"
                    else "Fix the failed test/build step, then run verify_build again."
                )
            self._event(state, "build_verification_finished", {"status": status})
            self._write(state)

    def _archive(self, state: dict[str, Any], reason: str) -> None:
        history = self._read_json(self.history_path, [])
        if not isinstance(history, list):
            history = []
        archived = copy.deepcopy(state)
        archived["archived_at"] = utc_now()
        archived["archive_reason"] = reason
        history = (history + [archived])[-100:]
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self._write_json_atomic(self.history_path, history)

    @staticmethod
    def _read_json(path: Path, fallback: Any) -> Any:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return fallback

    @staticmethod
    def _write_json_atomic(path: Path, value: Any) -> None:
        temp = path.with_name(f".{path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
        try:
            temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
            _replace_atomic(temp, path)
        finally:
            temp.unlink(missing_ok=True)

    @staticmethod
    def _has_task(state: dict[str, Any]) -> bool:
        return bool(
            str(state.get("objective") or "").strip()
            or state.get("steps")
            or str(state.get("current_step") or "").strip()
            or str(state.get("next_step") or "").strip()
            or str(state.get("status") or "idle") != "idle"
        )

    @staticmethod
    def _has_terminal_orchestration(state: dict[str, Any]) -> bool:
        projection = state.get("orchestration")
        if not isinstance(projection, dict):
            return False
        return str(projection.get("orchestration_state") or "").upper() in {"CHECKPOINTED", "BLOCKED", "ABORTED"}

    def _record_command_payload(self, state: dict[str, Any], command: str, payload: dict[str, Any]) -> None:
        status = str(payload.get("status", ""))
        session_id = str(payload.get("session_id", ""))
        artifact_ref = command_output_artifact_ref(payload)
        current = state.get("current_command")
        if not isinstance(current, dict) or (session_id and current.get("session_id") != session_id):
            current = {
                "command": command,
                "kind": classify_command(command),
                "session_id": session_id,
                "status": status or "running",
                "started_at": utc_now(),
            }
        if artifact_ref is None and isinstance(current.get("artifact_ref"), dict):
            artifact_ref = copy.deepcopy(current["artifact_ref"])
        current["status"] = status or ("failed" if payload.get("ok") is False else "exited")
        current["exit_code"] = payload.get("exit_code")
        current["elapsed_ms"] = payload.get("elapsed_ms")
        if artifact_ref is not None:
            current["artifact_ref"] = artifact_ref
        if current["status"] == "running":
            state["current_command"] = current
            return
        current["finished_at"] = utc_now()
        kind = str(current.get("kind", classify_command(command)))
        result = {
            "command": command,
            "status": "passed" if command_payload_succeeded(payload) else "failed",
            "exit_code": payload.get("exit_code"),
            "duration_ms": payload.get("elapsed_ms"),
            "summary": _text(payload.get("summary") or payload.get("stderr") or payload.get("stdout"), 2000),
            "finished_at": current["finished_at"],
        }
        if artifact_ref is not None:
            result["artifact_ref"] = artifact_ref
        state["last_command_result"] = {
            "command_id": session_id or _text(current.get("session_id"), 200),
            "kind": kind,
            "status": _text(current.get("status"), 100),
            "result_status": result["status"],
            "exit_code": result.get("exit_code"),
            "duration_ms": result.get("duration_ms"),
            "finished_at": current["finished_at"],
        }
        if kind == "test":
            state["test_results"] = (state["test_results"] + [result])[-MAX_RESULTS:]
        elif kind == "build":
            state["build_results"] = (state["build_results"] + [result])[-MAX_RESULTS:]
        state["current_command"] = None
        if not self._has_terminal_orchestration(state):
            state["status"] = "waiting" if result["status"] == "passed" else "failed"
            state["current_step"] = "Waiting for model" if result["status"] == "passed" else "Command failed"
            if result["status"] == "failed":
                state["failure"] = result["summary"] or f"Command failed with exit code {result['exit_code']}"
        self._event(state, "command_finished", {"command": _text(command, 500), "status": result["status"]})

    def _normalize_steps(self, raw: Any) -> list[dict[str, Any]]:
        if not isinstance(raw, list):
            return []
        now = utc_now()
        steps: list[dict[str, Any]] = []
        for index, item in enumerate(raw[:200], start=1):
            if isinstance(item, str):
                item = {"text": item}
            if not isinstance(item, dict):
                continue
            status = str(item.get("status", "pending"))
            if status not in {"pending", "in_progress", "completed", "failed"}:
                status = "pending"
            steps.append({
                "id": _text(item.get("id") or f"step-{index}", 200),
                "text": _text(item.get("text"), 4000),
                "status": status,
                "updated_at": _text(item.get("updated_at") or now, 100),
            })
        return steps

    def _add_file(self, state: dict[str, Any], path: str, operation: str) -> None:
        existing = {item.get("path"): item for item in state["modified_files"] if isinstance(item, dict)}
        existing[path] = {"path": _text(path, 2000), "operation": _text(operation, 100), "updated_at": utc_now()}
        state["modified_files"] = list(existing.values())[-MAX_FILES:]

    def _event(self, state: dict[str, Any], event: str, details: dict[str, Any]) -> None:
        state["events"] = (state.get("events", []) + [{"time": utc_now(), "event": event, "details": details}])[-MAX_EVENTS:]

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return _default_state()
        try:
            parsed = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            state = _default_state()
            state["failure"] = "The previous task-state file was unreadable and has been reset."
            return state
        state = _default_state()
        if isinstance(parsed, dict):
            state.update(parsed)
        state["version"] = STATE_VERSION
        for key in ("steps", "test_results", "build_results", "modified_files", "events"):
            if not isinstance(state.get(key), list):
                state[key] = []
        if not isinstance(state.get("orchestration"), dict):
            state["orchestration"] = {}
        if not isinstance(state.get("last_command_result"), dict):
            state["last_command_result"] = None
        if not isinstance(state.get("completion_report"), dict):
            state["completion_report"] = None
        if state.get("status") == "active" and not state.get("current_command"):
            try:
                updated = datetime.fromisoformat(str(state.get("updated_at", "")).replace("Z", "+00:00"))
                if (datetime.now(timezone.utc) - updated).total_seconds() >= STALE_ACTIVE_SECONDS:
                    state["status"] = "waiting"
                    state["current_step"] = "Waiting for model"
            except ValueError:
                pass
        return state

    def _write(self, state: dict[str, Any]) -> dict[str, Any]:
        state["updated_at"] = utc_now()
        self.state_dir.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_name(f".{self.path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
        try:
            temp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
            _replace_atomic(temp, self.path)
        finally:
            try:
                temp.unlink(missing_ok=True)
            except OSError:
                pass
        return copy.deepcopy(state)


class ContextualTaskStateStore:
    """Route task projections by execution context while preserving legacy global state."""

    def __init__(self, workspace: Path, scope_provider: Callable[[], str]) -> None:
        self.workspace = workspace.resolve()
        self._scope_provider = scope_provider
        self._global_store = TaskStateStore(self.workspace)
        self._stores: dict[str, TaskStateStore] = {}
        self._lock = threading.RLock()

    def current_scope_id(self) -> str:
        try:
            return str(self._scope_provider() or "").strip()
        except Exception:
            return ""

    def is_scoped(self) -> bool:
        return bool(self.current_scope_id())

    def _current_store(self) -> TaskStateStore:
        scope_id = self.current_scope_id()
        if not scope_id:
            return self._global_store
        with self._lock:
            store = self._stores.get(scope_id)
            if store is None:
                store = TaskStateStore(self.workspace, scope_id=scope_id)
                if (
                    not store.path.exists()
                    and not scope_id.startswith("mcp2026:")
                    and not scope_id.startswith("legacy:")
                ):
                    context_dir = self.workspace / ".coding-tools" / "task-contexts"
                    existing_contexts = list(context_dir.glob("*.json")) if context_dir.exists() else []
                    existing_contexts = [
                        path for path in existing_contexts
                        if not path.name.endswith("-history.json")
                    ]
                    legacy = self._global_store.get()
                    if not existing_contexts and TaskStateStore._has_task(legacy):
                        # One-time migration: the first stateful ChatWeb context adopts
                        # the pre-isolation task. Modern MCP 2026 stateless handles are
                        # explicit new application-state scopes and never adopt global
                        # state; later stateful contexts also always start clean.
                        store._write(legacy)
                self._stores[scope_id] = store
            return store

    @property
    def state_file_display(self) -> str:
        return self._current_store().state_file_display

    def contexts(self, limit: int = 20) -> list[dict[str, Any]]:
        context_dir = self.workspace / ".coding-tools" / "task-contexts"
        if not context_dir.exists():
            return []
        candidates: list[tuple[float, Path, dict[str, Any]]] = []
        for path in context_dir.glob("*.json"):
            if path.name.endswith("-history.json"):
                continue
            try:
                state = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(state, dict):
                    continue
                candidates.append((path.stat().st_mtime, path, state))
            except (OSError, ValueError):
                continue
        bounded = max(1, min(int(limit), 100))
        summaries: list[dict[str, Any]] = []
        for _mtime, path, state in sorted(candidates, key=lambda item: item[0], reverse=True)[:bounded]:
            projection = state.get("orchestration") if isinstance(state.get("orchestration"), dict) else {}
            summaries.append({
                "context_id": path.stem,
                "task_id": state.get("task_id"),
                "objective": state.get("objective"),
                "status": state.get("status"),
                "current_step": state.get("current_step"),
                "updated_at": state.get("updated_at"),
                "run_id": projection.get("run_id"),
                "wave_id": projection.get("wave_id"),
                "orchestration_state": projection.get("orchestration_state"),
                "state_file": path.relative_to(self.workspace).as_posix(),
            })
        return summaries

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        return getattr(self._current_store(), name)


class TaskStateToolsMixin:
    def check_exec_environment(self, args: dict[str, Any]) -> dict[str, Any]:
        landlock = landlock_status_payload()
        warnings: list[str] = []
        if not landlock.get("available"):
            warnings.append("Linux Landlock filesystem confinement is unavailable")
        if self.capabilities.skip_all_permissions:
            warnings.append("permission_mode=dangerous disables MCP safety gates")
        if self.fake_readonly_annotations:
            warnings.append(
                "tools/list annotations are faked as read-only; apply_patch and exec_command still mutate and execute"
            )
        return {
            "ok": True,
            **self._exec_environment_summary(),
            "landlock_enabled": self._landlock_enforced(landlock),
            "landlock_abi": landlock.get("abi_version"),
            "global_tmp_write": self.global_tmp_write_policy(),
            "warnings": warnings,
        }

    def get_default_cwd(self, args: dict[str, Any]) -> dict[str, Any]:
        return {
            "workspace": str(self.workspace.root),
            "default_cwd": self.default_cwd_display(),
            "deprecated": True,
            "deprecation_note": "Transport-level default_cwd has been removed. Every command takes an explicit workspace-relative path or workdir instead.",
        }

    def set_default_cwd(self, args: dict[str, Any]) -> dict[str, Any]:
        return {
            "workspace": str(self.workspace.root),
            "default_cwd": self.default_cwd_display(),
            "deprecated": True,
            "deprecation_note": "Transport-level default_cwd is deprecated and no longer mutable; pass an explicit path/workdir per call instead.",
        }

    def task_state_get(self, args: dict[str, Any]) -> dict[str, Any]:
        return {"state_file": self.task_state.state_file_display, "state": self.task_state.get()}

    def task_state_update(self, args: dict[str, Any]) -> dict[str, Any]:
        changes = dict(args)
        if changes.get("objective") and "status" not in changes:
            changes["status"] = "active"
        return {"state_file": self.task_state.state_file_display, "state": self.task_state.update(changes)}

    def task_state_clear(self, args: dict[str, Any]) -> dict[str, Any]:
        return {"cleared": True, "state_file": self.task_state.state_file_display, "state": self.task_state.clear()}

    def task_state_pause(self, args: dict[str, Any]) -> dict[str, Any]:
        return {"state": self.task_state.pause(str(args.get("reason", "")))}

    def task_state_resume(self, args: dict[str, Any]) -> dict[str, Any]:
        return {"state": self.task_state.resume(str(args.get("next_step", "")))}

    def task_history_list(self, args: dict[str, Any]) -> dict[str, Any]:
        return {"tasks": self.task_state.history(int(args.get("limit", 20)))}
