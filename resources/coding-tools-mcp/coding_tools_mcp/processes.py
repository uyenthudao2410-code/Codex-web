from __future__ import annotations

import os
import signal
import subprocess
import threading
import time
from dataclasses import dataclass, field
from typing import Any, BinaryIO, Callable

from .envutils import ENV_PREFIX
from .errors import ToolFailure
from .textutils import DEFAULT_MAX_LINES, TextTruncation, truncate_text_tail


SESSION_BUFFER_BYTES = 524_288
SESSION_HEAD_DIVISOR = 8
MAX_CONSUMER_CURSORS = 16
HARD_KILL_SIGNAL = getattr(signal, "SIGKILL", signal.SIGTERM)


EXEC_PREVIEW_BYTES = 4096
MAX_ACTIVE_EXEC_SESSIONS = 16
MAX_RETAINED_OUTPUT_SESSIONS = 32
COMPLETED_SESSION_TTL_SECONDS = 300
MAX_RUNTIME_OUTPUT_BYTES = 16 * 1024 * 1024
try:
    PRINCIPAL_MAX_ACTIVE_SESSIONS = max(
        1,
        min(
            MAX_ACTIVE_EXEC_SESSIONS,
            int(os.environ.get(f"{ENV_PREFIX}_PRINCIPAL_MAX_SESSIONS", "8")),
        ),
    )
except (TypeError, ValueError):
    PRINCIPAL_MAX_ACTIVE_SESSIONS = 8
PRINCIPAL_MAX_RETAINED_OUTPUT_BYTES = 4 * 1024 * 1024
ECOSYSTEM_CACHE_ENV_NAMES = {
    "MAVEN_USER_HOME",
    "GRADLE_USER_HOME",
    "NPM_CONFIG_CACHE",
    "npm_config_cache",
    "PIP_CACHE_DIR",
    "GOCACHE",
    "GOMODCACHE",
    "CARGO_HOME",
    "RUSTUP_HOME",
}
WINDOWS_JOB_OBJECT_ENV = "CODING_TOOLS_MCP_WINDOWS_JOB_OBJECT"

_JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
_JOB_OBJECT_LIMIT_ACTIVE_PROCESS = 0x00000008
_JOB_OBJECT_LIMIT_JOB_MEMORY = 0x00000200
_JOB_OBJECT_LIMIT_JOB_TIME = 0x00000004
_JOB_OBJECT_EXTENDED_LIMIT_INFORMATION_CLASS = 9
_JOB_OBJECT_CPU_RATE_CONTROL_INFORMATION_CLASS = 15
_WINDOWS_CREATE_SUSPENDED = 0x00000004


@dataclass(frozen=True)
class WindowsJobLimits:
    """Required native process-tree limits, applied before any child resumes."""

    memory_bytes: int = 2 * 1024 * 1024 * 1024
    active_processes: int = 64
    cpu_rate_percent: int = 50
    cpu_time_ms: int = 300_000


_kernel32: Any = None
_ntdll: Any = None
if os.name == "nt":
    try:
        import ctypes
        from ctypes import wintypes

        _kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        _ntdll = ctypes.WinDLL("ntdll", use_last_error=True)
        _kernel32.CreateJobObjectW.argtypes = [wintypes.LPVOID, wintypes.LPCWSTR]
        _kernel32.CreateJobObjectW.restype = wintypes.HANDLE
        _kernel32.SetInformationJobObject.argtypes = [
            wintypes.HANDLE,
            ctypes.c_int,
            wintypes.LPVOID,
            wintypes.DWORD,
        ]
        _kernel32.SetInformationJobObject.restype = wintypes.BOOL
        _kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        _kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
        _kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        _kernel32.CloseHandle.restype = wintypes.BOOL
        _ntdll.NtResumeProcess.argtypes = [wintypes.HANDLE]
        _ntdll.NtResumeProcess.restype = ctypes.c_long

        class _JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
            _fields_ = [
                ("PerProcessUserTimeLimit", ctypes.c_int64),
                ("PerJobUserTimeLimit", ctypes.c_int64),
                ("LimitFlags", ctypes.c_uint32),
                ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t),
                ("ActiveProcessLimit", ctypes.c_uint32),
                ("Affinity", ctypes.c_size_t),
                ("PriorityClass", ctypes.c_uint32),
                ("SchedulingClass", ctypes.c_uint32),
            ]

        class _IO_COUNTERS(ctypes.Structure):
            _fields_ = [
                ("ReadOperationCount", ctypes.c_uint64),
                ("WriteOperationCount", ctypes.c_uint64),
                ("OtherOperationCount", ctypes.c_uint64),
                ("ReadTransferCount", ctypes.c_uint64),
                ("WriteTransferCount", ctypes.c_uint64),
                ("OtherTransferCount", ctypes.c_uint64),
            ]

        class _JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
            _fields_ = [
                ("BasicLimitInformation", _JOBOBJECT_BASIC_LIMIT_INFORMATION),
                ("IoInfo", _IO_COUNTERS),
                ("ProcessMemoryLimit", ctypes.c_size_t),
                ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t),
                ("PeakJobMemoryUsed", ctypes.c_size_t),
            ]

        class _JOBOBJECT_CPU_RATE_CONTROL_INFORMATION(ctypes.Structure):
            _fields_ = [("ControlFlags", ctypes.c_uint32), ("CpuRate", ctypes.c_uint32)]
    except Exception:  # noqa: BLE001 - job objects are an optimization, never a requirement
        _kernel32 = None
        _ntdll = None


def windows_job_object_enabled() -> bool:
    if os.name != "nt" or _kernel32 is None:
        return False
    raw = os.environ.get(WINDOWS_JOB_OBJECT_ENV)
    if raw is not None and str(raw).strip() in {"0", "false", "off", "no"}:
        return False
    return True


def windows_host_token_posture() -> dict[str, Any]:
    """Read only elevation/integrity; do not expose account identity or groups."""
    if os.name != "nt" or _kernel32 is None:
        raise ToolFailure("NATIVE_TOKEN_POSTURE_UNAVAILABLE", "Windows native token posture could not be verified.", category="security")
    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    open_token = advapi32.OpenProcessToken
    open_token.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)]
    open_token.restype = wintypes.BOOL
    get_information = advapi32.GetTokenInformation
    get_information.argtypes = [wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    get_information.restype = wintypes.BOOL
    current_process = _kernel32.GetCurrentProcess
    current_process.restype = wintypes.HANDLE
    token = wintypes.HANDLE()
    if not open_token(current_process(), 0x8, ctypes.byref(token)):  # TOKEN_QUERY
        raise ToolFailure("NATIVE_TOKEN_POSTURE_UNAVAILABLE", "The native host token could not be queried.", category="security")
    try:
        elevation = wintypes.DWORD()
        returned = wintypes.DWORD()
        if not get_information(token, 20, ctypes.byref(elevation), ctypes.sizeof(elevation), ctypes.byref(returned)):
            raise ToolFailure("NATIVE_TOKEN_POSTURE_UNAVAILABLE", "The native host elevation could not be verified.", category="security")
        get_information(token, 25, None, 0, ctypes.byref(returned))
        if not 1 <= returned.value <= 65536:
            raise ToolFailure("NATIVE_TOKEN_POSTURE_UNAVAILABLE", "The native host integrity could not be verified.", category="security")
        buffer = ctypes.create_string_buffer(returned.value)
        if not get_information(token, 25, buffer, len(buffer), ctypes.byref(returned)):
            raise ToolFailure("NATIVE_TOKEN_POSTURE_UNAVAILABLE", "The native host integrity could not be verified.", category="security")
        sid = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_void_p)).contents.value
        count = advapi32.GetSidSubAuthorityCount
        count.argtypes = [wintypes.LPVOID]
        count.restype = ctypes.POINTER(ctypes.c_ubyte)
        subauthority = advapi32.GetSidSubAuthority
        subauthority.argtypes = [wintypes.LPVOID, wintypes.DWORD]
        subauthority.restype = ctypes.POINTER(wintypes.DWORD)
        rid = int(subauthority(sid, int(count(sid).contents.value) - 1).contents.value)
        return {"elevated": bool(elevation.value), "integrity_rid": rid}
    finally:
        _kernel32.CloseHandle(token)


def require_windows_native_token() -> None:
    posture = windows_host_token_posture()
    if posture["elevated"] or posture["integrity_rid"] > 0x2000:  # medium integrity
        raise ToolFailure("NATIVE_ELEVATED_HOST_DENIED", "Native execution requires a non-elevated Windows host process.", category="security", details={"execution_started": False})


def _attach_windows_job(process: subprocess.Popen[Any], limits: WindowsJobLimits | None = None) -> bool:
    """Attach the spawned process to a kill-on-close Job Object.

    Closing the job handle later becomes a deterministic whole-tree kill:
    every descendant the command created dies with the job, regardless of
    whether it ignored console control events.
    """

    if _kernel32 is None:
        return False
    handle = None
    try:
        handle = _kernel32.CreateJobObjectW(None, None)
        if not handle:
            return False
        info = _JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        info.BasicLimitInformation.LimitFlags = _JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if limits is not None:
            info.BasicLimitInformation.LimitFlags |= (
                _JOB_OBJECT_LIMIT_ACTIVE_PROCESS | _JOB_OBJECT_LIMIT_JOB_MEMORY | _JOB_OBJECT_LIMIT_JOB_TIME
            )
            info.BasicLimitInformation.ActiveProcessLimit = limits.active_processes
            info.BasicLimitInformation.PerJobUserTimeLimit = limits.cpu_time_ms * 10_000
            info.JobMemoryLimit = limits.memory_bytes
        size = ctypes.sizeof(info)
        if not _kernel32.SetInformationJobObject(
            handle, _JOB_OBJECT_EXTENDED_LIMIT_INFORMATION_CLASS, ctypes.byref(info), size
        ):
            _kernel32.CloseHandle(handle)
            return False
        if limits is not None:
            cpu_info = _JOBOBJECT_CPU_RATE_CONTROL_INFORMATION()
            cpu_info.ControlFlags = 0x1 | 0x4  # ENABLE | HARD_CAP
            cpu_info.CpuRate = limits.cpu_rate_percent * 100
            if not _kernel32.SetInformationJobObject(
                handle, _JOB_OBJECT_CPU_RATE_CONTROL_INFORMATION_CLASS,
                ctypes.byref(cpu_info), ctypes.sizeof(cpu_info),
            ):
                _kernel32.CloseHandle(handle)
                return False
        process_handle = getattr(process, "_handle", None)
        if process_handle is None or not _kernel32.AssignProcessToJobObject(handle, process_handle):
            _kernel32.CloseHandle(handle)
            return False
        setattr(process, "_coding_tools_job_handle", handle)
        return True
    except Exception:  # noqa: BLE001 - fall back to taskkill tree termination
        if handle:
            try:
                _kernel32.CloseHandle(handle)
            except Exception:
                pass
        return False


def _close_windows_job(process: subprocess.Popen[Any]) -> bool:
    handle = getattr(process, "_coding_tools_job_handle", None)
    if not handle:
        return False
    try:
        _kernel32.CloseHandle(handle)
    except Exception:  # noqa: BLE001
        pass
    setattr(process, "_coding_tools_job_handle", None)
    return True


def managed_process_creationflags(creationflags: int = 0) -> int:
    """Suspend a Windows child until its kill-on-close Job Object is attached."""

    flags = int(creationflags)
    if windows_job_object_enabled():
        flags |= _WINDOWS_CREATE_SUSPENDED
    return flags


def attach_managed_process(process: subprocess.Popen[Any], *, limits: WindowsJobLimits | None = None) -> bool:
    """Attach and resume a Windows process; return whether Job ownership exists."""

    if not windows_job_object_enabled():
        if limits is not None:
            process.kill()
            process.wait(timeout=3)
            raise ToolFailure("NATIVE_RESOURCE_LIMITS_UNAVAILABLE", "Native execution requires Windows Job Object limits.", category="security")
        return False
    attached = bool(getattr(process, "_coding_tools_job_handle", None))
    if not attached:
        attached = _attach_windows_job(process, limits)
    if not attached and limits is not None:
        # The process was created suspended. Never resume a native executor
        # after failing to install its complete resource/lifecycle boundary.
        setattr(process, "_coding_tools_created_suspended", False)
        process.kill()
        process.wait(timeout=3)
        raise ToolFailure("NATIVE_RESOURCE_LIMITS_UNAVAILABLE", "The native process-tree limits could not be installed.", category="security")
    if bool(getattr(process, "_coding_tools_created_suspended", False)):
        resumed = False
        try:
            process_handle = getattr(process, "_handle", None)
            if process_handle is not None and _ntdll is not None:
                resumed = _ntdll.NtResumeProcess(process_handle) == 0
        except Exception:  # noqa: BLE001 - termination fallback still owns the tree
            resumed = False
        setattr(process, "_coding_tools_created_suspended", False)
        if not resumed:
            _close_windows_job(process)
            try:
                process.kill()
            except OSError:
                pass
            raise ToolFailure(
                "PROCESS_RESUME_FAILED",
                "The managed Windows process could not be resumed after Job Object attachment.",
                category="runtime",
                retryable=True,
            )
    return attached


def terminate_process_group(
    process: subprocess.Popen[Any],
    signum: signal.Signals,
    *,
    force: bool = False,
) -> None:
    if not hasattr(os, "killpg"):
        if os.name == "nt":
            if _close_windows_job(process):
                try:
                    process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    pass
                return
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
    windows_job_limits: WindowsJobLimits | None = None,
) -> tuple[subprocess.Popen[bytes], int | None]:
    """Spawn a pipe-backed or true POSIX PTY-backed process."""

    use_job_object = os.name == "nt" and windows_job_object_enabled()
    if windows_job_limits is not None and not use_job_object:
        raise ToolFailure("NATIVE_RESOURCE_LIMITS_UNAVAILABLE", "Native execution requires Windows Job Object limits.", category="security")
    if use_job_object:
        popen_kwargs = {
            **popen_kwargs,
            "creationflags": managed_process_creationflags(
                int(popen_kwargs.get("creationflags", 0))
            ),
        }

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
        if use_job_object:
            setattr(process, "_coding_tools_created_suspended", True)
            attach_managed_process(process, limits=windows_job_limits)
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
    managed_job_id: str = ""
    owner_run_id: str = ""
    owner_wave_id: str = ""
    resource_class: str = "LIGHT"
    execution_metadata: dict[str, str] = field(default_factory=dict)
    resource_terminal_recorded: bool = False
    timeout_at: float | None = None
    warnings: list[str] = field(default_factory=list)
    cleanup_callback: Callable[[], None] | None = None
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
    sandbox_abort_on_cleanup: bool = False
    sandbox_idle_generation: int | None = None
    pty_master_fd: int | None = None
    _stdin_closed: bool = False

    def cleanup_sandbox_state(self) -> None:
        """Run the optional per-command sandbox scratch cleanup once."""
        with self.lock:
            callback = self.cleanup_callback
            self.cleanup_callback = None
        if callback is not None:
            try:
                cleanup_result = callback()
                if cleanup_result is False:
                    with self.lock:
                        self.warnings.append(
                            "Sandbox cleanup could not be confirmed; automatic execution remains fail-closed."
                        )
            except Exception:  # noqa: BLE001 - scratch cleanup cannot replace the process receipt
                with self.lock:
                    self.warnings.append(
                        "Sandbox cleanup failed; automatic execution remains fail-closed."
                    )

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
            session.cleanup_sandbox_state()
            return
        if session.process.poll() is not None or session.timed_out:
            return
        session.timed_out = True
        terminate_process_group(session.process, signal.SIGTERM)
        session.refresh_status()
        if session.process.poll() is not None:
            session.cleanup_sandbox_state()

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


def hidden_process_popen_kwargs() -> dict[str, Any]:
    """Prevent console helper processes from flashing a window on Windows."""
    if os.name != "nt":
        return {}
    creation_flag = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return {"creationflags": creation_flag} if creation_flag else {}

def process_group_popen_kwargs() -> dict[str, Any]:
    if hasattr(os, "setsid"):
        return {"start_new_session": True}
    if os.name == "nt":
        creation_flags = (
            getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            | getattr(subprocess, "CREATE_NO_WINDOW", 0)
        )
        if creation_flags:
            return {"creationflags": creation_flags}
    return {}
