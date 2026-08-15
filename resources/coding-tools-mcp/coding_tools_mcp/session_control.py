from __future__ import annotations

import re
import secrets
import signal
import subprocess
import time
from pathlib import Path
from typing import Any

from . import processes
from .errors import ToolFailure
from .fs_utils import truncate_bytes
from .processes import (
    COMPLETED_SESSION_TTL_SECONDS,
    EXEC_PREVIEW_BYTES,
    HARD_KILL_SIGNAL,
    MAX_RETAINED_OUTPUT_SESSIONS,
    MAX_RUNTIME_OUTPUT_BYTES,
    SESSION_BUFFER_BYTES,
    ExecSession,
    terminate_process_group,
)


def read_output_action(output_ref: str, *, offset: int = 0, limit: int | None = None) -> dict[str, Any]:
    return {
        "tool": "read_output",
        "arguments": {
            "output_ref": output_ref,
            "offset": offset,
            "limit": EXEC_PREVIEW_BYTES if limit is None else limit,
        },
    }


class SessionControlMixin:
    def _make_session(
        self,
        process: subprocess.Popen[bytes],
        *,
        timeout_at: float | None = None,
        warnings: list[str] | None = None,
        pty_master_fd: int | None = None,
    ) -> ExecSession:
        return ExecSession(
            session_id=secrets.token_urlsafe(18),
            process=process,
            timeout_at=timeout_at,
            warnings=warnings or [],
            pty_master_fd=pty_master_fd,
        )

    def _remember_output_session(self, session: ExecSession) -> None:
        session.refresh_status()
        with self.sessions_lock:
            self.output_sessions.pop(session.session_id, None)
            self.output_sessions[session.session_id] = session
            self._evict_retained_locked()

    def _retained_output_bytes_locked(self) -> int:
        return sum(session.retained_bytes for session in self.sessions.values()) + sum(
            session.retained_bytes for session in self.output_sessions.values()
        )

    def _principal_retained_output_bytes_locked(self) -> dict[str, int]:
        totals: dict[str, int] = {}
        for session_id, session in self.output_sessions.items():
            principal = self.session_principals.get(session_id, "default")
            totals[principal] = totals.get(principal, 0) + session.retained_bytes
        for session_id, session in self.sessions.items():
            principal = self.session_principals.get(session_id, "default")
            totals[principal] = totals.get(principal, 0) + session.retained_bytes
        return totals

    def _evict_principal_overflow_locked(self) -> None:
        totals = self._principal_retained_output_bytes_locked()
        for principal, total in totals.items():
            if total <= processes.PRINCIPAL_MAX_RETAINED_OUTPUT_BYTES:
                continue
            overflow = total - processes.PRINCIPAL_MAX_RETAINED_OUTPUT_BYTES
            oldest = [
                (session_id, session)
                for session_id, session in self.output_sessions.items()
                if self.session_principals.get(session_id, "default") == principal
            ]
            oldest.sort(key=lambda item: item[1].completed_at or 0)
            for session_id, session in oldest:
                if overflow <= 0:
                    break
                self.output_sessions.pop(session_id, None)
                self.session_principals.pop(session_id, None)
                overflow -= session.retained_bytes

    def _evict_retained_locked(self) -> None:
        self._evict_principal_overflow_locked()
        retained = self._retained_output_bytes_locked()
        while self.output_sessions and (
            len(self.output_sessions) > MAX_RETAINED_OUTPUT_SESSIONS
            or retained > MAX_RUNTIME_OUTPUT_BYTES
        ):
            oldest = self.output_sessions.pop(next(iter(self.output_sessions)))
            self.session_principals.pop(oldest.session_id, None)
            retained -= oldest.retained_bytes

    def _complete_session(self, session: ExecSession) -> None:
        session.refresh_status()
        if session.process.poll() is None:
            return
        with self.sessions_lock:
            self.sessions.pop(session.session_id, None)
            principal = self.session_principals.get(session.session_id)
            if principal is not None:
                current = self.principal_active_counts.get(principal, 0)
                self.principal_active_counts[principal] = max(0, current - 1)
        self._remember_output_session(session)

    def _prune_sessions(self) -> None:
        with self.sessions_lock:
            active = list(self.sessions.values())
        for session in active:
            session.refresh_status()
            if session.process.poll() is not None:
                self._complete_session(session)
        cutoff = time.time() - COMPLETED_SESSION_TTL_SECONDS
        with self.sessions_lock:
            expired = [
                session_id
                for session_id, session in self.output_sessions.items()
                if session.completed_at is not None and session.completed_at < cutoff
            ]
            for session_id in expired:
                self.output_sessions.pop(session_id, None)
            self._evict_retained_locked()

    def _get_output_session(self, session_id: str) -> ExecSession:
        self._prune_sessions()
        with self.sessions_lock:
            session = self.sessions.get(session_id) or self.output_sessions.get(session_id)
        if session is None:
            raise ToolFailure("SESSION_NOT_FOUND", "Output session not found.", category="runtime")
        return session

    def _format_session_output(self, session: ExecSession, payload: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
        terminal = payload.get("status") != "running"
        if terminal:
            self._complete_session(session)
        payload["command_id"] = session.session_id
        payload.setdefault("session_id", session.session_id)
        if payload.get("status") == "running":
            payload["next_action"] = {
                "tool": "command_control",
                "arguments": {
                    "action": "poll",
                    "command_id": session.session_id,
                    "yield_time_ms": 10000,
                },
            }
        output_refs = {
            "stdout": f"command:{session.session_id}:stdout",
            "stderr": f"command:{session.session_id}:stderr",
        }
        legacy_output_refs = {
            "stdout": f"session:{session.session_id}:stdout",
            "stderr": f"session:{session.session_id}:stderr",
        }
        truncated_streams: list[str] = []
        for stream in ("stdout", "stderr"):
            omitted = payload.get(f"{stream}_omitted_bytes")
            if payload.get(f"{stream}_truncated") or (
                isinstance(omitted, int) and omitted > 0
            ):
                truncated_streams.append(stream)
        output_stream = (
            truncated_streams[0]
            if truncated_streams
            else "stderr"
            if not payload.get("stdout") and payload.get("stderr")
            else "stdout"
        )
        output_ref = output_refs[output_stream]
        truncated = bool(payload.get("truncated"))
        if truncated:
            if not truncated_streams:
                truncated_streams.append(output_stream)
            if terminal:
                self._remember_output_session(session)
            payload["output_ref"] = output_ref
            payload["output_stream"] = output_stream
            payload["output_refs"] = output_refs
            payload["legacy_output_refs"] = legacy_output_refs
            payload["output_truncated"] = True
            payload["truncated_output_streams"] = truncated_streams
            read_actions = [read_output_action(output_refs[stream]) for stream in truncated_streams]
            payload["next_actions"] = read_actions
            if terminal:
                payload["next_action"] = read_actions[0]
        verbosity = str(args.get("verbosity", "")).strip().lower()
        if not verbosity:
            return payload
        if verbosity not in {"summary", "preview", "full"}:
            raise ToolFailure(
                "INVALID_ARGUMENT",
                "verbosity must be one of: summary, preview, full.",
                category="validation",
            )
        if terminal and not truncated:
            self._remember_output_session(session)
        payload["summary"] = self._session_output_summary(session, payload)
        payload["output_ref"] = output_ref
        payload["output_stream"] = output_stream
        payload["output_refs"] = output_refs
        payload["legacy_output_refs"] = legacy_output_refs
        if verbosity == "full":
            return payload
        compact = {
            key: value
            for key, value in payload.items()
            if key
            not in {
                "stdout",
                "stderr",
                "stdout_truncated",
                "stderr_truncated",
                "stdout_truncated_by",
                "stderr_truncated_by",
                "stdout_output_lines",
                "stderr_output_lines",
                "stdout_output_bytes",
                "stderr_output_bytes",
                "stdout_omitted_bytes",
                "stderr_omitted_bytes",
            }
        }
        if verbosity == "preview":
            preview_limit = int(args.get("preview_bytes", EXEC_PREVIEW_BYTES))
            preview, preview_truncated = truncate_bytes(session.retained_output_bytes(), preview_limit)
            compact["preview"] = preview
            compact["preview_truncated"] = preview_truncated
            compact["truncated"] = bool(compact.get("truncated") or preview_truncated)
            if preview_truncated and not compact.get("truncated_output_streams"):
                preview_streams = [
                    stream
                    for stream in ("stdout", "stderr")
                    if session.retained_stream_bytes(stream)[2] > 0
                ]
                compact["truncated_output_streams"] = preview_streams
                preview_actions = [read_output_action(output_refs[stream]) for stream in preview_streams]
                compact["next_actions"] = preview_actions
                if terminal and preview_actions:
                    compact["next_action"] = preview_actions[0]
        return compact

    def _session_output_summary(self, session: ExecSession, payload: dict[str, Any]) -> str:
        retained = session.retained_output_bytes().decode("utf-8", errors="replace")
        lines = retained.splitlines()
        tail = next((line.strip() for line in reversed(lines) if line.strip()), "")
        if len(tail) > 120:
            tail = tail[:117] + "..."
        elapsed = float(payload.get("elapsed_ms") or 0) / 1000.0
        exit_code = payload.get("exit_code")
        status = f"exit {exit_code}" if exit_code is not None else str(payload.get("status", "running"))
        parts = [status, f"{elapsed:.1f}s", f"{len(lines)} lines"]
        if tail:
            parts.append(f"tail: {tail!r}")
        return " | ".join(parts)

    def read_output(self, args: dict[str, Any]) -> dict[str, Any]:
        output_ref = str(args.get("output_ref", ""))
        match = re.fullmatch(r"(command|session):([^:]+):(full|stdout|stderr)", output_ref)
        if not match:
            raise ToolFailure(
                "INVALID_ARGUMENT",
                "output_ref must look like command:<id>:stdout; legacy session:<id>:stdout is also accepted.",
                category="validation",
            )
        session = self._get_output_session(match.group(2))
        session.refresh_status()
        ref_stream = match.group(3)
        requested_stream = str(args.get("stream", "") or "")
        if requested_stream and requested_stream not in {"stdout", "stderr"}:
            raise ToolFailure("INVALID_ARGUMENT", "stream must be stdout or stderr.", category="validation")
        if ref_stream in {"stdout", "stderr"} and requested_stream and requested_stream != ref_stream:
            raise ToolFailure("INVALID_ARGUMENT", "stream does not match output_ref.", category="validation")
        stream = ref_stream if ref_stream in {"stdout", "stderr"} else requested_stream or "stdout"
        requested_offset = max(0, int(args.get("offset", 0)))
        limit = max(1, min(int(args.get("limit", EXEC_PREVIEW_BYTES)), SESSION_BUFFER_BYTES))
        window = session.retained_stream_window(stream, requested_offset, limit)
        chunk = window["data"]
        offset = int(window["offset"])
        next_offset = window["next_offset"]
        omitted_bytes = int(window["omitted_bytes"])
        dropped_bytes = int(window["evicted_bytes_total"])
        warnings: list[str] = []
        if omitted_bytes:
            warnings.append(f"{stream} offset crossed bytes evicted from the middle retention gap")
        if window["evicted_gap_bytes"]:
            warnings.append(f"middle {stream} output was evicted; the frozen head and rolling tail were preserved")
        if ref_stream == "full":
            warnings.append("legacy full output_ref defaults to stdout; use output_refs for stable stream paging")
        result = {
            "output_ref": output_ref,
            "command_id": session.session_id,
            "session_id": session.session_id,
            "stream_output_ref": f"command:{session.session_id}:{stream}",
            "legacy_stream_output_ref": f"session:{session.session_id}:{stream}",
            "stream": stream,
            "offset": offset,
            "requested_offset": requested_offset,
            "limit": limit,
            "content": chunk.decode("utf-8", errors="replace"),
            "next_offset": next_offset,
            "total_retained_bytes": window["total_retained_bytes"],
            "retained_start_offset": window["retained_start_offset"],
            "tail_start_offset": window["tail_start_offset"],
            "total_stream_bytes": window["total_stream_bytes"],
            "stdout_dropped_bytes": session.stdout_dropped_bytes,
            "stderr_dropped_bytes": session.stderr_dropped_bytes,
            "stream_dropped_bytes": dropped_bytes,
            "head_retained_bytes": window["head_retained_bytes"],
            "tail_retained_bytes": window["tail_retained_bytes"],
            "evicted_gap_bytes": window["evicted_gap_bytes"],
            "evict_events": window["evict_events"],
            "evicted_bytes_total": window["evicted_bytes_total"],
            "omitted_bytes": omitted_bytes,
            "truncated": next_offset is not None or omitted_bytes > 0,
            "ok": True,
            "warnings": warnings,
        }
        if next_offset is not None:
            result["next_action"] = read_output_action(
                str(result["stream_output_ref"]), offset=next_offset, limit=limit
            )
        return result

    def write_stdin(self, args: dict[str, Any]) -> dict[str, Any]:
        session_id = self._command_handle(args)
        session = self._get_session(session_id)
        session.refresh_status()
        consumer_id = str(args.get("consumer_id", "") or "").strip()
        if len(consumer_id) > 128:
            raise ToolFailure("INVALID_ARGUMENT", "consumer_id must be at most 128 characters.", category="validation")
        chars = str(args.get("chars", ""))
        if session.process.poll() is not None:
            if chars:
                raise ToolFailure("COMMAND_CLOSED", "Command is closed; stdin write blocked.", category="runtime")
            payload = session.snapshot_since_cursor(int(args.get("max_output_bytes", 65536)), consumer_id=consumer_id)
            return self._format_session_output(session, payload, args)
        if chars:
            session.write_input(chars.encode("utf-8"))
        wait_until = time.time() + (int(args.get("yield_time_ms", 10000)) / 1000.0)
        first_output_at: float | None = None
        while time.time() < wait_until and session.process.poll() is None:
            try:
                task_status = str(self.task_state.get().get("status", ""))
            except Exception:
                task_status = ""
            if task_status in {"paused", "stopped"}:
                terminate_process_group(session.process, signal.SIGTERM)
                session.refresh_status()
                payload = session.snapshot_since_cursor(int(args.get("max_output_bytes", 65536)), consumer_id=consumer_id)
                payload["task_control"] = task_status
                payload["status"] = task_status
                return self._format_session_output(session, payload, args)
            time.sleep(0.02)
            with session.lock:
                has_new_output = (
                    session.stdout_total_bytes > session.stdout_cursor
                    or session.stderr_total_bytes > session.stderr_cursor
                )
                if has_new_output and not chars:
                    break
                if has_new_output and chars:
                    if first_output_at is None:
                        first_output_at = time.time()
                    if time.time() - first_output_at >= 0.05:
                        break
        payload = session.snapshot_since_cursor(int(args.get("max_output_bytes", 65536)), consumer_id=consumer_id)
        return self._format_session_output(session, payload, args)

    def _wait_for_session_exit(self, session: ExecSession, wait_seconds: float) -> bool:
        try:
            session.process.wait(timeout=max(0.0, wait_seconds))
        except subprocess.TimeoutExpired:
            pass
        session.refresh_status()
        session.drain_readers()
        return session.process.poll() is not None

    def kill_session(self, args: dict[str, Any]) -> dict[str, Any]:
        session_id = self._command_handle(args)
        session = self._get_session(session_id)
        signal_name = str(args.get("signal", "TERM"))
        force = signal_name == "KILL"
        signum = {"TERM": signal.SIGTERM, "KILL": HARD_KILL_SIGNAL, "INT": signal.SIGINT}.get(
            signal_name,
            signal.SIGTERM,
        )
        evict = True
        if session.process.poll() is None:
            session.terminating = True
            terminate_process_group(session.process, signum, force=force)
            exited = self._wait_for_session_exit(session, int(args.get("wait_ms", 5000)) / 1000.0)
            if not exited and not force:
                force = True
                terminate_process_group(session.process, HARD_KILL_SIGNAL, force=True)
                exited = self._wait_for_session_exit(session, int(args.get("kill_wait_ms", 2000)) / 1000.0)
            if exited:
                killed = True
                status = "killed" if force else "terminated"
            else:
                killed = False
                evict = False
                status = "terminating"
        else:
            killed = False
            status = "exited"
        signal_sent = "SIGKILL" if force else signal.Signals(signum).name
        payload = session.snapshot_since_cursor(int(args.get("max_output_bytes", 65536)))
        payload.update({"killed": killed, "status": status, "evicted": evict, "signal_sent": signal_sent})
        payload = self._format_session_output(session, payload, args)
        if status == "terminating":
            warnings = list(payload.get("warnings", []))
            warnings.append("Process did not exit after TERM/SIGKILL; session retained for retry or watchdog cleanup.")
            payload["warnings"] = warnings
            payload["next_action"] = "retry kill_session or wait for watchdog cleanup"
        if evict:
            with self.sessions_lock:
                self.sessions.pop(session_id, None)
        return payload

    def cancel_session(self, session_id: str) -> None:
        with self.sessions_lock:
            session = self.sessions.pop(session_id, None)
        if session is None:
            return
        session.refresh_status()
        if session.process.poll() is None:
            terminate_process_group(session.process, signal.SIGTERM)

    def cancel_request(self, request_id: str | int) -> None:
        with self.request_sessions_lock:
            session_id = self.request_sessions.get(request_id)
        if session_id is not None:
            self.cancel_session(session_id)

    def _get_session(self, session_id: str) -> ExecSession:
        self._prune_sessions()
        with self.sessions_lock:
            session = self.sessions.get(session_id) or self.output_sessions.get(session_id)
        if session is None:
            raise ToolFailure("COMMAND_NOT_FOUND", "Command handle was not found.", category="not_found")
        return session
