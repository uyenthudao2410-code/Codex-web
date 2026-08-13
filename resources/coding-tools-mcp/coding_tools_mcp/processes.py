from __future__ import annotations

import os
import signal
import subprocess
import threading
import time
from dataclasses import dataclass, field
from typing import Any, BinaryIO

from .errors import ToolFailure
from .textutils import DEFAULT_MAX_LINES, TextTruncation, truncate_text_tail


SESSION_BUFFER_BYTES = 524_288
SESSION_HEAD_DIVISOR = 8
MAX_CONSUMER_CURSORS = 16
HARD_KILL_SIGNAL = getattr(signal, "SIGKILL", signal.SIGTERM)


def terminate_process_group(
    process: subprocess.Popen[bytes],
    signum: signal.Signals,
    *,
    force: bool = False,
) -> None:
    if not hasattr(os, "killpg"):
        if os.name == "nt":
            # A shell-backed command can exit before its child process, so
            # waiting only for the Popen shell is not evidence that the command
            # tree is gone.  Use the same tree-oriented Windows primitive as the
            # Codex sidecar: /T owns descendants and /F makes cancellation
            # deterministic even when the child ignores CTRL_BREAK.
            try:
                subprocess.run(
                    ["taskkill.exe", "/PID", str(process.pid), "/T", "/F"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=3,
                    check=False,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                try:
                    process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    pass
                return
            except (OSError, subprocess.SubprocessError):
                # Fall through to the direct Popen fallback only when taskkill is
                # unavailable.  The caller will still refresh and report the
                # actual process state rather than assuming success.
                pass
        try:
            if force:
                process.kill()
            else:
                process.terminate()
            process.wait(timeout=1)
        except Exception:
            process.kill()
        return
    try:
        os.killpg(process.pid, signum)
    except ProcessLookupError:
        return
    except Exception:
        process.terminate()
    try:
        process.wait(timeout=1)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, HARD_KILL_SIGNAL)
        except Exception:
            process.kill()


def spawn_process(
    command: Any,
    *,
    cwd: str,
    shell: bool,
    env: dict[str, str],
    tty: bool,
    popen_kwargs: dict[str, Any],
) -> tuple[subprocess.Popen[bytes], int | None]:
    """Spawn a pipe-backed or true POSIX PTY-backed process."""

    if not tty:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            shell=shell,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            **popen_kwargs,
        )
        return process, None
    if os.name == "nt":
        raise ToolFailure(
            "TTY_UNSUPPORTED",
            "tty=true requires ConPTY support, which is not available in this build.",
            category="runtime",
            details={"platform": os.name, "retry_hint": "Run the command without tty=true."},
        )
    try:
        import pty

        master_fd, slave_fd = pty.openpty()
    except (ImportError, OSError) as exc:
        raise ToolFailure(
            "TTY_UNSUPPORTED",
            "A POSIX pseudo-terminal could not be created.",
            category="runtime",
        ) from exc
    try:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            shell=shell,
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            env=env,
            **popen_kwargs,
        )
    except Exception:
        os.close(master_fd)
        raise
    finally:
        os.close(slave_fd)
    return process, master_fd


@dataclass
class ExecSession:
    session_id: str
    process: subprocess.Popen[bytes]
    timeout_at: float | None = None
    warnings: list[str] = field(default_factory=list)
    # Keep a frozen head plus a rolling tail. This preserves startup warnings and
    # first/root-cause errors while still retaining the newest progress. stdout /
    # stderr remain the rolling-tail fields for compatibility with older call
    # sites; the new *_head fields hold the immutable prefix.
    stdout_head: bytearray = field(default_factory=bytearray)
    stderr_head: bytearray = field(default_factory=bytearray)
    stdout: bytearray = field(default_factory=bytearray)
    stderr: bytearray = field(default_factory=bytearray)
    stdout_start_offset: int = 0
    stderr_start_offset: int = 0
    stdout_cursor: int = 0
    stderr_cursor: int = 0
    consumer_cursors: dict[str, tuple[int, int, float]] = field(default_factory=dict)
    stdout_total_bytes: int = 0
    stderr_total_bytes: int = 0
    stdout_dropped_bytes: int = 0
    stderr_dropped_bytes: int = 0
    stdout_evict_events: int = 0
    stderr_evict_events: int = 0
    buffer_limit: int = SESSION_BUFFER_BYTES
    lock: threading.Lock = field(default_factory=threading.Lock)
    reader_threads: list[threading.Thread] = field(default_factory=list)
    started_at: float = field(default_factory=time.time)
    completed_at: float | None = None
    closed: bool = False
    exit_code: int | None = None
    signal_name: str | None = None
    timed_out: bool = False
    terminating: bool = False
    pty_master_fd: int | None = None
    _stdin_closed: bool = False

    @property
    def retained_bytes(self) -> int:
        with self.lock:
            return len(self.stdout_head) + len(self.stdout) + len(self.stderr_head) + len(self.stderr)

    def append_stdout(self, chunk: bytes) -> None:
        with self.lock:
            _append_retained_stream(
                self,
                head=self.stdout_head,
                tail=self.stdout,
                chunk=chunk,
                total_attr="stdout_total_bytes",
                tail_start_attr="stdout_start_offset",
                dropped_attr="stdout_dropped_bytes",
                evict_events_attr="stdout_evict_events",
            )

    def append_stderr(self, chunk: bytes) -> None:
        with self.lock:
            _append_retained_stream(
                self,
                head=self.stderr_head,
                tail=self.stderr,
                chunk=chunk,
                total_attr="stderr_total_bytes",
                tail_start_attr="stderr_start_offset",
                dropped_attr="stderr_dropped_bytes",
                evict_events_attr="stderr_evict_events",
            )

    def write_input(self, data: bytes) -> None:
        if self._stdin_closed:
            raise ToolFailure("SESSION_CLOSED", "Session stdin is closed.", category="runtime")
        try:
            if self.pty_master_fd is not None:
                os.write(self.pty_master_fd, data)
                return
            if self.process.stdin is None or self.process.stdin.closed:
                raise ToolFailure("SESSION_CLOSED", "Session stdin is closed.", category="runtime")
            self.process.stdin.write(data)
            self.process.stdin.flush()
        except (BrokenPipeError, OSError, ValueError) as exc:
            raise ToolFailure("SESSION_CLOSED", "Session stdin is closed.", category="runtime") from exc

    def close_stdin(self) -> None:
        if self.pty_master_fd is not None or self._stdin_closed:
            return
        self._stdin_closed = True
        if self.process.stdin is not None:
            try:
                self.process.stdin.close()
            except OSError:
                pass

    def snapshot_since_cursor(
        self,
        max_output_bytes: int,
        *,
        consumer_id: str = "",
    ) -> dict[str, Any]:
        self.refresh_status()
        consumer = str(consumer_id or "").strip()[:128]
        with self.lock:
            if consumer:
                prior = self.consumer_cursors.get(consumer, (0, 0, 0.0))
                stdout_cursor, stderr_cursor = int(prior[0]), int(prior[1])
            else:
                stdout_cursor, stderr_cursor = self.stdout_cursor, self.stderr_cursor
            stdout_bytes, stdout_omitted = self._unread_stream_locked("stdout", stdout_cursor)
            stderr_bytes, stderr_omitted = self._unread_stream_locked("stderr", stderr_cursor)
            stdout_retention = self._stream_metrics_locked("stdout")
            stderr_retention = self._stream_metrics_locked("stderr")
            if consumer:
                if consumer not in self.consumer_cursors and len(self.consumer_cursors) >= MAX_CONSUMER_CURSORS:
                    oldest = min(self.consumer_cursors, key=lambda key: self.consumer_cursors[key][2])
                    self.consumer_cursors.pop(oldest, None)
                self.consumer_cursors[consumer] = (
                    self.stdout_total_bytes,
                    self.stderr_total_bytes,
                    time.time(),
                )
            else:
                self.stdout_cursor = self.stdout_total_bytes
                self.stderr_cursor = self.stderr_total_bytes
        stdout_truncation = truncate_output_bytes_tail(stdout_bytes, max_output_bytes)
        stderr_truncation = truncate_output_bytes_tail(stderr_bytes, max_output_bytes)
        if self.timed_out:
            status = "timeout"
        elif self.terminating and self.process.poll() is None:
            status = "running"
        elif self.signal_name is not None:
            status = "terminated"
        else:
            status = "running" if self.process.poll() is None else "exited"
        payload: dict[str, Any] = {
            "command_id": self.session_id,
            "session_id": self.session_id,
            "consumer_id": consumer or None,
            "status": status,
            "exit_code": self.exit_code,
            "signal": self.signal_name,
            "timed_out": self.timed_out,
            "stdout": stdout_truncation.content,
            "stderr": stderr_truncation.content,
            "stdout_truncated": stdout_truncation.truncated,
            "stderr_truncated": stderr_truncation.truncated,
            "stdout_truncated_by": stdout_truncation.truncated_by,
            "stderr_truncated_by": stderr_truncation.truncated_by,
            "stdout_output_lines": stdout_truncation.output_lines,
            "stderr_output_lines": stderr_truncation.output_lines,
            "stdout_output_bytes": stdout_truncation.output_bytes,
            "stderr_output_bytes": stderr_truncation.output_bytes,
            "stdout_dropped_bytes": self.stdout_dropped_bytes,
            "stderr_dropped_bytes": self.stderr_dropped_bytes,
            "stdout_omitted_bytes": stdout_omitted,
            "stderr_omitted_bytes": stderr_omitted,
            "output_retention": {
                "stdout": stdout_retention,
                "stderr": stderr_retention,
            },
            "truncated": (
                stdout_truncation.truncated
                or stderr_truncation.truncated
                or stdout_omitted > 0
                or stderr_omitted > 0
            ),
            "ok": True,
        }
        warnings: list[str] = list(self.warnings)
        if stdout_truncation.truncated:
            warnings.append(f"stdout truncated from tail by {stdout_truncation.truncated_by}")
        if stderr_truncation.truncated:
            warnings.append(f"stderr truncated from tail by {stderr_truncation.truncated_by}")
        if stdout_omitted > 0:
            warnings.append("stdout cursor skipped dropped bytes")
        if stderr_omitted > 0:
            warnings.append("stderr cursor skipped dropped bytes")
        if warnings:
            payload["warnings"] = warnings
        return payload

    def refresh_status(self) -> None:
        if self.timeout_at is not None and not self.timed_out and self.process.poll() is None and time.time() >= self.timeout_at:
            self.timed_out = True
            terminate_process_group(self.process, signal.SIGTERM)
            self.drain_readers()
        code = self.process.poll()
        if code is None:
            return
        self.drain_readers()
        self.exit_code = code
        self.terminating = False
        if code < 0:
            values = {item.value for item in signal.Signals}
            self.signal_name = signal.Signals(-code).name if -code in values else str(-code)
        self.closed = True
        if self.completed_at is None:
            self.completed_at = time.time()

    def drain_readers(self, timeout: float = 0.2) -> None:
        deadline = time.time() + timeout
        for thread in list(self.reader_threads):
            remaining = max(0.0, deadline - time.time())
            if remaining <= 0:
                break
            thread.join(timeout=remaining)

    def retained_output_bytes(self) -> bytes:
        with self.lock:
            stdout = self._retained_stream_display_locked("stdout")
            stderr = self._retained_stream_display_locked("stderr")
        sections: list[bytes] = []
        if stdout:
            sections.extend([b"--- stdout ---\n", stdout])
        if stderr:
            if sections:
                sections.append(b"\n")
            sections.extend([b"--- stderr ---\n", stderr])
        return b"".join(sections)

    def retained_stream_bytes(self, stream: str) -> tuple[bytes, int, int, int]:
        """Compatibility view of one retained stream.

        Before eviction the stream is contiguous and starts at offset zero. Once
        a middle gap exists, this legacy view returns the rolling tail and its
        logical start offset. New paging code should use retained_stream_window().
        """
        with self.lock:
            head, tail, tail_start, total, dropped, _events = self._stream_components_locked(stream)
            head_end = len(head)
            if tail_start <= head_end:
                return bytes(head) + bytes(tail), 0, total, dropped
            return bytes(tail), tail_start, total, dropped

    def retained_stream_metrics(self, stream: str) -> dict[str, int]:
        with self.lock:
            return self._stream_metrics_locked(stream)

    def retained_stream_window(self, stream: str, offset: int, limit: int) -> dict[str, Any]:
        """Read one logical stream range without pretending the evicted middle exists."""
        requested = max(0, int(offset))
        limit = max(1, int(limit))
        with self.lock:
            head, tail, tail_start, total, dropped, events = self._stream_components_locked(stream)
            head_end = len(head)
            gap = max(0, tail_start - head_end)
            actual = min(requested, total)
            omitted = 0

            if gap == 0:
                retained = bytes(head) + bytes(tail)
                chunk = retained[actual : actual + limit]
            elif actual < head_end:
                chunk = bytes(head[actual : min(head_end, actual + limit)])
            else:
                if actual < tail_start:
                    omitted = tail_start - actual
                    actual = tail_start
                tail_index = max(0, actual - tail_start)
                chunk = bytes(tail[tail_index : tail_index + limit])

            consumed_to = actual + len(chunk)
            if gap > 0 and requested < head_end and consumed_to >= head_end:
                next_offset = tail_start if tail_start < total else None
                omitted = gap if next_offset is not None else 0
            else:
                next_offset = consumed_to if consumed_to < total else None

            return {
                "data": chunk,
                "offset": actual,
                "requested_offset": requested,
                "next_offset": next_offset,
                "omitted_bytes": omitted,
                "total_stream_bytes": total,
                "total_retained_bytes": len(head) + len(tail),
                "retained_start_offset": 0 if head else tail_start,
                "tail_start_offset": tail_start,
                "head_retained_bytes": head_end,
                "tail_retained_bytes": len(tail),
                "evicted_gap_bytes": gap,
                "evict_events": events,
                "evicted_bytes_total": dropped,
            }

    def _stream_components_locked(
        self, stream: str
    ) -> tuple[bytearray, bytearray, int, int, int, int]:
        if stream == "stdout":
            return (
                self.stdout_head,
                self.stdout,
                self.stdout_start_offset,
                self.stdout_total_bytes,
                self.stdout_dropped_bytes,
                self.stdout_evict_events,
            )
        if stream == "stderr":
            return (
                self.stderr_head,
                self.stderr,
                self.stderr_start_offset,
                self.stderr_total_bytes,
                self.stderr_dropped_bytes,
                self.stderr_evict_events,
            )
        raise ValueError(f"Unknown output stream: {stream}")

    def _stream_metrics_locked(self, stream: str) -> dict[str, int]:
        head, tail, tail_start, total, dropped, events = self._stream_components_locked(stream)
        return {
            "head_retained_bytes": len(head),
            "tail_retained_bytes": len(tail),
            "total_retained_bytes": len(head) + len(tail),
            "total_stream_bytes": total,
            "tail_start_offset": tail_start,
            "evicted_gap_bytes": max(0, tail_start - len(head)),
            "evict_events": events,
            "evicted_bytes_total": dropped,
        }

    def _retained_stream_display_locked(self, stream: str) -> bytes:
        head, tail, tail_start, _total, _dropped, _events = self._stream_components_locked(stream)
        gap = max(0, tail_start - len(head))
        if not gap:
            return bytes(head) + bytes(tail)
        marker = f"\n... {gap} bytes evicted from middle ...\n".encode("utf-8")
        return bytes(head) + marker + bytes(tail)

    def _unread_stream_locked(self, stream: str, cursor: int) -> tuple[bytes, int]:
        head, tail, tail_start, total, _dropped, _events = self._stream_components_locked(stream)
        if cursor >= total:
            return b"", 0
        head_end = len(head)
        position = max(0, cursor)
        parts: list[bytes] = []
        if position < head_end:
            parts.append(bytes(head[position:]))
            position = head_end
        omitted = 0
        if position < tail_start:
            omitted = tail_start - position
            position = tail_start
            parts.append(f"\n... {omitted} bytes evicted from middle ...\n".encode("utf-8"))
        if position < total:
            parts.append(bytes(tail[max(0, position - tail_start) :]))
        return b"".join(parts), omitted


def start_reader_threads(session: ExecSession) -> None:
    def reader(stream: BinaryIO, append: Any) -> None:
        try:
            while True:
                chunk = os.read(stream.fileno(), 4096)
                if not chunk:
                    break
                append(chunk)
        except (OSError, ValueError):
            return
        finally:
            try:
                stream.close()
            except OSError:
                pass

    def pty_reader(fd: int) -> None:
        try:
            while True:
                chunk = os.read(fd, 4096)
                if not chunk:
                    break
                session.append_stdout(chunk)
        except OSError:
            return
        finally:
            try:
                os.close(fd)
            except OSError:
                pass
            if session.pty_master_fd == fd:
                session.pty_master_fd = None

    if session.pty_master_fd is not None:
        thread = threading.Thread(target=pty_reader, args=(session.pty_master_fd,), daemon=True)
        session.reader_threads.append(thread)
        thread.start()
        return
    if session.process.stdout is not None:
        thread = threading.Thread(target=reader, args=(session.process.stdout, session.append_stdout), daemon=True)
        session.reader_threads.append(thread)
        thread.start()
    if session.process.stderr is not None:
        thread = threading.Thread(target=reader, args=(session.process.stderr, session.append_stderr), daemon=True)
        session.reader_threads.append(thread)
        thread.start()


def start_session_watchdog(session: ExecSession) -> None:
    if session.timeout_at is None:
        return

    def watchdog() -> None:
        delay = max(0.0, session.timeout_at - time.time()) if session.timeout_at is not None else 0.0
        try:
            session.process.wait(timeout=delay)
        except subprocess.TimeoutExpired:
            pass
        else:
            session.refresh_status()
            return
        if session.process.poll() is not None or session.timed_out:
            return
        session.timed_out = True
        terminate_process_group(session.process, signal.SIGTERM)
        session.refresh_status()

    threading.Thread(
        target=watchdog,
        name=f"coding-tools-watchdog-{session.session_id}",
        daemon=True,
    ).start()


def _append_retained_stream(
    session: ExecSession,
    *,
    head: bytearray,
    tail: bytearray,
    chunk: bytes,
    total_attr: str,
    tail_start_attr: str,
    dropped_attr: str,
    evict_events_attr: str,
) -> None:
    if not chunk:
        return
    head_limit = min(session.buffer_limit, max(1, session.buffer_limit // SESSION_HEAD_DIVISOR))
    tail_limit = max(0, session.buffer_limit - head_limit)
    remaining = chunk
    if len(head) < head_limit:
        take = min(head_limit - len(head), len(remaining))
        head.extend(remaining[:take])
        remaining = remaining[take:]
    if remaining:
        tail.extend(remaining)

    total = int(getattr(session, total_attr)) + len(chunk)
    setattr(session, total_attr, total)
    overflow = max(0, len(tail) - tail_limit)
    if overflow:
        del tail[:overflow]
        setattr(session, dropped_attr, int(getattr(session, dropped_attr)) + overflow)
        setattr(session, evict_events_attr, int(getattr(session, evict_events_attr)) + 1)
    setattr(session, tail_start_attr, total - len(tail))


def truncate_output_bytes_tail(data: bytes, max_bytes: int, max_lines: int = DEFAULT_MAX_LINES) -> TextTruncation:
    return truncate_text_tail(
        data.decode("utf-8", errors="replace"),
        max_lines=max_lines,
        max_bytes=max_bytes,
    )
