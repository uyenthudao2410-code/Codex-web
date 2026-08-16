from __future__ import annotations

import hashlib
import json
import os
import secrets
import shutil
import signal
import subprocess
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .artifact_refs import provider_result_artifact_ref
from .processes import spawn_process, terminate_process_group
from .tool_contract import OPENCODE_SAFE_TOOLS
from .usage_events import classify_provider_error


ALLOWED_OPENCODE_MODELS = frozenset({
    "opencode-go/deepseek-v4-flash",
    "opencode-go/deepseek-v4-pro",
})
READ_ONLY_AGENT = "execution-hub-readonly"
MAX_PROMPT_BYTES = 20_000
MAX_RESULT_CHARS = 64 * 1024
MAX_EVENT_LINE_BYTES = 256 * 1024
MAX_RETAINED_DISPATCHES = 32
SAFE_TOOLS = OPENCODE_SAFE_TOOLS
LIFECYCLE_EVENT_TYPES = frozenset({"step_start", "step_finish", "tool_use", "text", "error"})


class OpenCodeProviderError(RuntimeError):
    def __init__(self, code: str, message: str, *, retryable: bool = False, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable
        self.details = details or {}


def read_only_opencode_config() -> dict[str, Any]:
    permission = {
        "*": "deny",
        "read": "allow",
        "glob": "allow",
        "grep": "allow",
        "list": "allow",
        "lsp": "allow",
    }
    return {
        "$schema": "https://opencode.ai/config.json",
        "permission": permission,
        "agent": {
            READ_ONLY_AGENT: {
                "description": "Execution Hub read-only provider worker",
                "mode": "primary",
                "permission": dict(permission),
            }
        },
    }


def _opencode_argv() -> list[str]:
    override = str(os.environ.get("CODING_TOOLS_MCP_OPENCODE_ARGV") or "").strip()
    if override:
        try:
            parsed = json.loads(override)
        except json.JSONDecodeError as exc:
            raise OpenCodeProviderError("INVALID_OPENCODE_ARGV", "CODING_TOOLS_MCP_OPENCODE_ARGV must be a JSON array of argv tokens.") from exc
        if not isinstance(parsed, list) or not parsed or not all(isinstance(item, str) and item for item in parsed):
            raise OpenCodeProviderError("INVALID_OPENCODE_ARGV", "CODING_TOOLS_MCP_OPENCODE_ARGV must be a non-empty JSON array of strings.")
        return list(parsed)
    configured = str(os.environ.get("CODING_TOOLS_MCP_OPENCODE_BIN") or "").strip()
    binary = configured or shutil.which("opencode") or ""
    if not binary:
        raise OpenCodeProviderError("OPENCODE_NOT_FOUND", "OpenCode CLI was not found. Install OpenCode or set CODING_TOOLS_MCP_OPENCODE_BIN.", retryable=True)
    return [binary]


def _child_env(*, dispatch_id: str, delegation_id: str) -> dict[str, str]:
    env = dict(os.environ)
    # Never propagate a server bearer through a provider process. Provider auth
    # remains available through its own OpenCode credential store/environment.
    for key in list(env):
        upper = key.upper()
        if upper in {"CODING_TOOLS_MCP_AUTH_TOKEN", "MCP_AUTH_TOKEN"}:
            env.pop(key, None)
    env["OPENCODE_CONFIG_CONTENT"] = json.dumps(read_only_opencode_config(), separators=(",", ":"))
    env["CODING_TOOLS_MCP_PROVIDER_DISPATCH_ID"] = dispatch_id
    env["CODING_TOOLS_MCP_PROVIDER_DELEGATION_ID"] = delegation_id
    return env


@dataclass
class _Dispatch:
    dispatch_id: str
    request_id: str
    run_id: str
    wave_id: str
    delegation_id: str
    model: str
    prompt_sha256: str
    prompt_bytes: int
    timeout_ms: int
    process: subprocess.Popen[bytes]
    managed_job_id: str
    created_at_ms: int
    started_at_ms: int
    status: str = "running"
    finished_at_ms: int | None = None
    returncode: int | None = None
    session_id: str = ""
    error_class: str | None = None
    cancel_requested: bool = False
    timed_out: bool = False
    policy_violation: bool = False
    stdout_bytes: int = 0
    stderr_bytes: int = 0
    output_truncated: bool = False
    result_parts: list[str] = field(default_factory=list)
    result_chars: int = 0
    event_counts: dict[str, int] = field(default_factory=dict)
    last_step_finish: str = ""
    last_tool: str = ""
    last_tool_status: str = ""
    lock: threading.RLock = field(default_factory=threading.RLock)


class OpenCodeProviderAdapter:
    def __init__(self, workspace_provider, *, on_terminal=None, resource_governor=None) -> None:
        self._workspace_provider = workspace_provider
        self._on_terminal = on_terminal
        self._resource_governor = resource_governor
        self._lock = threading.RLock()
        self._dispatches: dict[str, _Dispatch] = {}

    def _workspace(self) -> Path:
        return Path(self._workspace_provider()).expanduser().resolve(strict=True)

    def _snapshot(self, item: _Dispatch) -> dict[str, Any]:
        with item.lock:
            terminal = item.status in {"completed", "failed", "cancelled", "timed_out"}
            total_ms = max(0, item.finished_at_ms - item.created_at_ms) if terminal and item.finished_at_ms is not None else None
            snapshot = {
                "dispatch_id": item.dispatch_id,
                "request_id": item.request_id,
                "run_id": item.run_id,
                "wave_id": item.wave_id,
                "delegation_id": item.delegation_id,
                "provider_id": "opencode-go",
                "model": item.model,
                "status": item.status,
                "session_id": item.session_id,
                "prompt_sha256": item.prompt_sha256,
                "prompt_bytes": item.prompt_bytes,
                "result_text": "".join(item.result_parts),
                "result_chars": item.result_chars,
                "output_truncated": item.output_truncated,
                "stdout_bytes": item.stdout_bytes,
                "stderr_bytes": item.stderr_bytes,
                "returncode": item.returncode,
                "error_class": item.error_class,
                "read_only_enforced": True,
                "allowed_tools": sorted(SAFE_TOOLS),
                "lifecycle_evidence": {
                    "event_counts": dict(item.event_counts),
                    "last_step_finish": item.last_step_finish,
                    "last_tool": item.last_tool,
                    "last_tool_status": item.last_tool_status,
                },
                "timing": {
                    "queue_ms": max(0, item.started_at_ms - item.created_at_ms),
                    "provider_ms": None,
                    "total_ms": total_ms,
                },
            }
            snapshot["capability_profile"] = "opencode_readonly"
            snapshot["artifact_ref"] = provider_result_artifact_ref(
                dispatch_id=item.dispatch_id,
                run_id=item.run_id,
                wave_id=item.wave_id,
                provider_id="opencode-go",
                model=item.model,
                result_chars=item.result_chars,
                output_truncated=item.output_truncated,
            )
            return snapshot

    def _evict(self) -> None:
        if len(self._dispatches) < MAX_RETAINED_DISPATCHES:
            return
        terminal = [item for item in self._dispatches.values() if item.status != "running"]
        terminal.sort(key=lambda item: item.finished_at_ms or item.created_at_ms)
        while len(self._dispatches) >= MAX_RETAINED_DISPATCHES and terminal:
            self._dispatches.pop(terminal.pop(0).dispatch_id, None)
        if len(self._dispatches) >= MAX_RETAINED_DISPATCHES:
            raise OpenCodeProviderError("OPENCODE_PROVIDER_CAPACITY", "OpenCode provider dispatch capacity is full.", retryable=True)

    def start(self, *, run_id: str, wave_id: str, model: str, prompt: str, timeout_ms: int = 60_000, request_id: str = "") -> dict[str, Any]:
        model = str(model or "").strip()
        if model not in ALLOWED_OPENCODE_MODELS:
            raise OpenCodeProviderError("OPENCODE_MODEL_DENIED", "Only the allowlisted OpenCode Go Flash/Pro models may be dispatched by this adapter.")
        prompt_bytes = str(prompt or "").encode("utf-8")
        if not prompt_bytes or len(prompt_bytes) > MAX_PROMPT_BYTES:
            raise OpenCodeProviderError("OPENCODE_PROMPT_INVALID", f"Provider prompt must be 1..{MAX_PROMPT_BYTES} UTF-8 bytes.")
        timeout_ms = max(100, min(int(timeout_ms), 120_000))
        prompt_sha = hashlib.sha256(prompt_bytes).hexdigest()
        request = str(request_id or "").strip()[:128]
        identity = request or prompt_sha
        signature = hashlib.sha256(f"{run_id}\0{wave_id}\0{model}\0{prompt_sha}".encode("utf-8")).hexdigest()
        dispatch_id = "opencode-provider-" + hashlib.sha256(f"{run_id}\0{wave_id}\0{identity}".encode("utf-8")).hexdigest()[:40]
        delegation_id = "opencode-provider-" + hashlib.sha256(dispatch_id.encode("utf-8")).hexdigest()[:40]
        with self._lock:
            existing = self._dispatches.get(dispatch_id)
            if existing is not None:
                existing_signature = hashlib.sha256(f"{existing.run_id}\0{existing.wave_id}\0{existing.model}\0{existing.prompt_sha256}".encode("utf-8")).hexdigest()
                if existing_signature != signature:
                    raise OpenCodeProviderError("OPENCODE_DISPATCH_CONFLICT", "The provider request identity was reused with different content.")
                result = self._snapshot(existing)
                result["deduplicated"] = True
                return result
            self._evict()
            workspace = self._workspace()
            argv = [*_opencode_argv(), "run", "--model", model, "--format", "json", "--agent", READ_ONLY_AGENT, "--dir", str(workspace)]
            popen_kwargs: dict[str, Any] = {}
            if os.name == "nt":
                popen_kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            elif hasattr(os, "setsid"):
                popen_kwargs["start_new_session"] = True
            created_at_ms = int(time.time() * 1000)
            admission = None
            process = None
            try:
                if self._resource_governor is not None:
                    admission = self._resource_governor.admit(
                        command=f"opencode provider {model}",
                        command_id=dispatch_id,
                        run_id=str(run_id),
                        wave_id=str(wave_id),
                        owner="opencode-provider",
                        resource_class="MEDIUM",
                    )
                process, _ = spawn_process(
                    argv,
                    cwd=str(workspace),
                    shell=False,
                    env=_child_env(dispatch_id=dispatch_id, delegation_id=delegation_id),
                    tty=False,
                    popen_kwargs=popen_kwargs,
                )
                if admission is not None:
                    self._resource_governor.bind_process(admission, process)
            except Exception as exc:
                if process is not None and process.poll() is None:
                    terminate_process_group(process, signal.SIGTERM, force=True)
                if admission is not None:
                    self._resource_governor.spawn_failed(admission)
                raise OpenCodeProviderError("OPENCODE_START_FAILED", "OpenCode provider process could not be started.", retryable=True) from exc
            started_at_ms = int(time.time() * 1000)
            item = _Dispatch(
                dispatch_id=dispatch_id,
                request_id=request,
                run_id=str(run_id),
                wave_id=str(wave_id),
                delegation_id=delegation_id,
                model=model,
                prompt_sha256=prompt_sha,
                prompt_bytes=len(prompt_bytes),
                timeout_ms=timeout_ms,
                process=process,
                managed_job_id=admission.job_id if admission is not None else "",
                created_at_ms=created_at_ms,
                started_at_ms=started_at_ms,
            )
            self._dispatches[dispatch_id] = item
        threading.Thread(target=self._run, args=(item, prompt_bytes), daemon=True, name=f"opencode-provider-{dispatch_id[-8:]}").start()
        result = self._snapshot(item)
        result["deduplicated"] = False
        return result

    def _append_result(self, item: _Dispatch, text: str) -> None:
        if not text:
            return
        with item.lock:
            remaining = MAX_RESULT_CHARS - item.result_chars
            if remaining <= 0:
                item.output_truncated = True
                return
            chunk = text[:remaining]
            item.result_parts.append(chunk)
            item.result_chars += len(chunk)
            if len(chunk) < len(text):
                item.output_truncated = True

    def _handle_stdout_line(self, item: _Dispatch, raw: bytes) -> None:
        with item.lock:
            item.stdout_bytes += len(raw)
        if len(raw) > MAX_EVENT_LINE_BYTES:
            with item.lock:
                item.output_truncated = True
            return
        try:
            event = json.loads(raw.decode("utf-8", errors="replace"))
        except json.JSONDecodeError:
            return
        if not isinstance(event, dict):
            return
        session_id = str(event.get("sessionID") or "")[:256]
        if session_id:
            with item.lock:
                item.session_id = session_id
        event_type = str(event.get("type") or "")
        if event_type in LIFECYCLE_EVENT_TYPES:
            with item.lock:
                item.event_counts[event_type] = min(1_000_000, item.event_counts.get(event_type, 0) + 1)
        if event_type == "text" and isinstance(event.get("part"), dict):
            self._append_result(item, str(event["part"].get("text") or ""))
        elif event_type == "error":
            error = event.get("error")
            name = str(error.get("name") or error.get("code") or "provider_error") if isinstance(error, dict) else "provider_error"
            with item.lock:
                item.error_class = classify_provider_error(name, status="failed") or "provider_error"
        elif event_type == "tool_use" and isinstance(event.get("part"), dict):
            tool = str(event["part"].get("tool") or "").strip()
            state = event["part"].get("state") if isinstance(event["part"].get("state"), dict) else {}
            tool_status = str(state.get("status") or "").strip()[:80]
            with item.lock:
                item.last_tool = tool[:100]
                item.last_tool_status = tool_status
            if tool and tool not in SAFE_TOOLS:
                with item.lock:
                    item.policy_violation = True
                    item.error_class = "side_effect_policy_violation"
        elif event_type == "step_finish":
            part = event.get("part") if isinstance(event.get("part"), dict) else event
            reason = str(part.get("reason") or part.get("finish") or "").strip()[:100]
            if reason:
                with item.lock:
                    item.last_step_finish = reason

    def _read_stdout(self, item: _Dispatch) -> None:
        stream = item.process.stdout
        if stream is None:
            return
        while True:
            raw = stream.readline(MAX_EVENT_LINE_BYTES + 1)
            if not raw:
                return
            self._handle_stdout_line(item, raw)

    def _read_stderr(self, item: _Dispatch) -> None:
        stream = item.process.stderr
        if stream is None:
            return
        while True:
            raw = stream.read(8192)
            if not raw:
                return
            with item.lock:
                item.stderr_bytes += len(raw)

    def _run(self, item: _Dispatch, prompt_bytes: bytes) -> None:
        stdout_thread = threading.Thread(target=self._read_stdout, args=(item,), daemon=True)
        stderr_thread = threading.Thread(target=self._read_stderr, args=(item,), daemon=True)
        stdout_thread.start()
        stderr_thread.start()
        try:
            if item.process.stdin is not None:
                item.process.stdin.write(prompt_bytes)
                item.process.stdin.close()
                item.process.stdin = None
            try:
                returncode = item.process.wait(timeout=item.timeout_ms / 1000.0)
            except subprocess.TimeoutExpired:
                with item.lock:
                    item.timed_out = True
                terminate_process_group(item.process, signal.SIGTERM, force=True)
                returncode = item.process.poll()
        except (BrokenPipeError, OSError):
            terminate_process_group(item.process, signal.SIGTERM, force=True)
            returncode = item.process.poll()
            with item.lock:
                item.error_class = item.error_class or "transport"
        finally:
            stdout_thread.join(timeout=1.0)
            stderr_thread.join(timeout=1.0)
            for stream in (item.process.stdout, item.process.stderr):
                if stream is None:
                    continue
                try:
                    stream.close()
                except OSError:
                    pass
        with item.lock:
            item.returncode = returncode
            item.finished_at_ms = int(time.time() * 1000)
            if item.policy_violation:
                item.status = "failed"
                item.error_class = "side_effect_policy_violation"
            elif item.cancel_requested:
                item.status = "cancelled"
                item.error_class = item.error_class or "cancelled_or_interrupted"
            elif item.timed_out:
                item.status = "timed_out"
                item.error_class = item.error_class or ("provider_cli_idle_timeout_after_tool_calls" if item.last_step_finish.lower() == "tool-calls" else "deadline_or_timeout")
            elif item.error_class is not None or returncode not in {0, None}:
                item.status = "failed"
                item.error_class = item.error_class or "provider_process_error"
            else:
                item.status = "completed"
            terminal_status = item.status
        if item.managed_job_id and self._resource_governor is not None:
            self._resource_governor.complete(
                item.managed_job_id,
                lifecycle_state=terminal_status,
                exit_code=returncode,
            )
        callback = self._on_terminal
        if callback is not None:
            try:
                callback(self._snapshot(item))
            except Exception:
                # Completion remains truthful even if the observer/control plane
                # is concurrently shutting down.
                pass

    def observe(self, dispatch_id: str) -> dict[str, Any]:
        with self._lock:
            item = self._dispatches.get(str(dispatch_id or ""))
        if item is None:
            raise OpenCodeProviderError("OPENCODE_DISPATCH_NOT_FOUND", "OpenCode provider dispatch was not found.")
        return self._snapshot(item)

    def cancel(self, dispatch_id: str) -> dict[str, Any]:
        with self._lock:
            item = self._dispatches.get(str(dispatch_id or ""))
        if item is None:
            raise OpenCodeProviderError("OPENCODE_DISPATCH_NOT_FOUND", "OpenCode provider dispatch was not found.")
        with item.lock:
            if item.status != "running":
                return self._snapshot(item)
            item.cancel_requested = True
        terminate_process_group(item.process, signal.SIGTERM, force=True)
        return self._snapshot(item)

    def find_by_session(self, *, run_id: str, wave_id: str, model: str, session_id: str) -> dict[str, Any] | None:
        target = str(session_id or "")
        if not target:
            return None
        with self._lock:
            items = list(self._dispatches.values())
        for item in items:
            with item.lock:
                if item.run_id == run_id and item.wave_id == wave_id and item.model == model and item.session_id == target:
                    return self._snapshot(item)
        return None

    def active_count(self) -> int:
        with self._lock:
            return sum(1 for item in self._dispatches.values() if item.status == "running")

    def capacity_status(self) -> dict[str, Any]:
        with self._lock:
            active = sum(1 for item in self._dispatches.values() if item.status == "running")
            retained = len(self._dispatches)
        return {
            "provider_id": "opencode-go",
            "active_requests": active,
            "retained_dispatches": retained,
            "retained_limit": MAX_RETAINED_DISPATCHES,
            "models": sorted(ALLOWED_OPENCODE_MODELS),
            "read_only_enforced": True,
            "capability_profile": "opencode_readonly",
        }

    def close(self) -> None:
        self._on_terminal = None
        with self._lock:
            active = [item.dispatch_id for item in self._dispatches.values() if item.status == "running"]
        for dispatch_id in active:
            try:
                self.cancel(dispatch_id)
            except OpenCodeProviderError:
                pass
