from __future__ import annotations

import os
import re
import secrets
import shutil
import signal
import subprocess
import time
from pathlib import Path, PurePosixPath
from typing import Any

from .artifact_refs import build_file_artifact_ref
from .build_verify import verify_build as run_build_verification
from .command_parse import (
    DESTRUCTIVE_RE,
    INLINE_SCRIPT_PERMISSION,
    NETWORK_RE,
    SHELL_EXPANSION_RE,
    command_executables,
    explicit_command_path_candidates,
    inline_script_command,
    is_literal_network_reference_command,
    shlex_split,
    strip_heredoc_payloads,
)
from .errors import ToolFailure
from .execution_resources import ExecutionResourceError
from .git_utils import require_git
from .landlock_exec import (
    SPECIAL_DEVICE_PATHS,
    guard_allow_roots,
    landlock_exec_argv,
    landlock_unavailable_warning,
    open_landlock_ruleset,
)
from . import processes
from .runtime_config import env_pattern_matches, is_core_command_env_name, is_filtered_env_var
from .task_state import command_payload_succeeded
from .processes import (
    ECOSYSTEM_CACHE_ENV_NAMES,
    MAX_ACTIVE_EXEC_SESSIONS,
    ExecSession,
    hidden_process_popen_kwargs,
    process_group_popen_kwargs,
    spawn_process,
    start_reader_threads,
    start_session_watchdog,
    terminate_process_group,
)


def exec_output_diagnostics(payload: dict[str, Any]) -> list[dict[str, str]]:
    diagnostics: list[dict[str, str]] = []
    stdout = str(payload.get("stdout", ""))
    stderr = str(payload.get("stderr", ""))
    combined = "\n".join(part for part in (stderr, stdout) if part)
    lower = combined.lower()
    if payload.get("timed_out") or payload.get("status") == "timeout":
        diagnostics.append(
            diagnostic(
                "COMMAND_TIMED_OUT",
                evidence="command timed out",
                suggested_fix="Increase timeout_ms only for trusted workloads, or run a narrower command.",
            )
        )
    if payload.get("truncated") or payload.get("stdout_truncated") or payload.get("stderr_truncated"):
        diagnostics.append(
            diagnostic(
                "OUTPUT_TRUNCATED",
                evidence="stdout/stderr exceeded max_output_bytes or session buffer limits",
                severity="warning",
                suggested_fix="Increase max_output_bytes or poll the running session more frequently.",
            )
        )
    if "/dev/null" in lower and "permission denied" in lower:
        diagnostics.append(
            diagnostic(
                "DEV_NULL_DENIED",
                evidence=combined,
                suggested_fix="Landlock special device rules should include WRITE_FILE, TRUNCATE, and IOCTL_DEV for /dev/null.",
            )
        )
    if "could not resolve host" in lower or "temporary failure in name resolution" in lower or "name or service not known" in lower:
        diagnostics.append(
            diagnostic(
                "DNS_RESOLUTION_FAILED",
                evidence=combined,
                suggested_next_command="cat /etc/resolv.conf && getent hosts repo.maven.apache.org",
            )
        )
    if "java.security" in lower and ("permission denied" in lower or "could not" in lower or "error loading" in lower):
        diagnostics.append(
            diagnostic(
                "JDK_SECURITY_CONFIG_BLOCKED",
                evidence=combined,
                suggested_fix="Ensure the JDK security configuration path is included in Landlock read roots.",
            )
        )
    if "tmpdir" in lower and ("permission denied" in lower or "not writable" in lower or "cannot write" in lower):
        diagnostics.append(
            diagnostic(
                "TMPDIR_NOT_WRITABLE",
                evidence=combined,
                suggested_next_command="printf ok > \"$TMPDIR/coding-tools-write-test\"",
            )
        )
    home_error_terms = ("permission denied", "not writable", "cannot write", "eacces")
    home_path_error = any(
        re.search(r"(?:\.coding-tools/home|/home(?:/|[\"'\s]|$))", line)
        and any(term in line for term in home_error_terms)
        for line in lower.splitlines()
    )
    home_error = (
        "$home" in lower
        or "home=" in lower
        or re.search(r"\bhome directory\b", lower)
        or "cannot write to home" in lower
        or re.search(r"not writable:\s+\S*home", lower)
        or re.search(r"permission denied:\s+\S*home", lower)
        or home_path_error
    )
    if home_error and any(term in lower for term in home_error_terms):
        diagnostics.append(
            diagnostic(
                "HOME_NOT_WRITABLE",
                evidence=combined,
                suggested_next_command="printf ok > \"$HOME/coding-tools-write-test\"",
            )
        )
    if "permission denied" in lower and any(root in combined for root in ("/usr", "/bin", "/lib", "/etc", "/usr/local/sdkman")):
        diagnostics.append(
            diagnostic(
                "LANDLOCK_READ_ROOT_BLOCKED",
                evidence=combined,
                suggested_fix="Add the missing toolchain path to CODING_TOOLS_MCP_EXEC_ALLOW_ROOTS or the default read roots.",
            )
        )
    if payload.get("exit_code") == 127 or "command not found" in lower or ("not found" in lower and "exec" in lower):
        diagnostics.append(
            diagnostic(
                "EXECUTABLE_NOT_FOUND",
                evidence=combined or "exit_code=127",
                suggested_next_command="command -v <executable>",
            )
        )
    return diagnostics

def permission_failure_diagnostics(exc: ToolFailure) -> list[dict[str, str]]:
    spec = PERMISSION_FAILURE_DIAGNOSTICS.get(str(exc.details.get("permission") or ""))
    if spec is None:
        return []
    return [
        diagnostic(
            spec["code"],
            evidence=exc.message,
            suggested_fix=spec["suggested_fix"],
            suggested_server_flag=spec.get("suggested_server_flag"),
        )
    ]

PERMISSION_FAILURE_DIAGNOSTICS: dict[str, dict[str, str]] = {
    "network": {
        "code": "NETWORK_PERMISSION_REQUIRED",
        "suggested_fix": "Restart the server with --permission-mode trusted or --allow-network.",
        "suggested_server_flag": "--permission-mode trusted",
    },
    "shell_expansion": {
        "code": "SHELL_EXPANSION_PERMISSION_REQUIRED",
        "suggested_fix": "Restart the server with --permission-mode trusted for local development shell expansion.",
        "suggested_server_flag": "--permission-mode trusted",
    },
    INLINE_SCRIPT_PERMISSION: {
        "code": "INLINE_SCRIPT_PERMISSION_REQUIRED",
        "suggested_fix": "Restart the server with --permission-mode trusted for local development inline scripts.",
        "suggested_server_flag": "--permission-mode trusted",
    },
    "sensitive_env": {
        "code": "SECRET_ENV_REJECTED",
        "suggested_fix": "Remove secret-looking or loader/startup environment variables from exec_command env.",
    },
}

def diagnostic(
    code: str,
    *,
    evidence: str = "",
    severity: str = "error",
    suggested_fix: str | None = None,
    suggested_next_command: str | None = None,
    suggested_server_flag: str | None = None,
) -> dict[str, str]:
    item = {"code": code, "severity": severity}
    if evidence:
        item["evidence"] = truncate_evidence(evidence)
    if suggested_fix:
        item["suggested_fix"] = suggested_fix
    if suggested_next_command:
        item["suggested_next_command"] = suggested_next_command
    if suggested_server_flag:
        item["suggested_server_flag"] = suggested_server_flag
    return item

def truncate_evidence(text: str, limit: int = 240) -> str:
    text = " ".join(text.strip().split())
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


class ExecToolsMixin:
    def exec_command(self, args: dict[str, Any]) -> dict[str, Any]:
        self._prune_sessions()
        cmd = str(args.get("cmd", ""))
        if not cmd:
            raise ToolFailure("INVALID_ARGUMENT", "cmd is required.", category="validation")
        workdir_arg = args.get("workdir", args.get("cwd", "."))
        if "workdir" in args and "cwd" in args and str(args["workdir"]) != str(args["cwd"]):
            raise ToolFailure("INVALID_ARGUMENT", "workdir and cwd refer to different directories.", category="validation")
        workdir = self.resolve_existing(str(workdir_arg))
        if not workdir.path.is_dir():
            raise ToolFailure("NOT_A_DIRECTORY", "workdir is not a directory.", category="validation")
        self._check_command_policy(cmd, args)
        timeout_ms = int(args.get("timeout_ms", 30000))
        yield_ms = int(args.get("yield_time_ms", 10000))
        max_output_bytes = int(args.get("max_output_bytes", 65536))
        tty = bool(args.get("tty", False))
        stdin_text = str(args.get("stdin", ""))
        env = self._command_env(args.get("env", {}))
        start = time.time()
        deadline = start + (timeout_ms / 1000.0)
        landlock_fd: int | None = None
        landlock_warning: str | None = None
        popen_cmd: Any = cmd
        popen_shell = True
        popen_extra = process_group_popen_kwargs()
        if self.landlock_enabled():
            try:
                landlock_fd = open_landlock_ruleset(
                    self._current_request_workspace_root(),
                    guard_allow_roots(),
                    write_roots=self.landlock_write_roots(),
                )
                popen_cmd = landlock_exec_argv(landlock_fd, cmd)
                popen_shell = False
                popen_extra["pass_fds"] = (landlock_fd,)
            except ToolFailure as exc:
                if exc.code != "SANDBOX_UNAVAILABLE":
                    raise
                landlock_warning = landlock_unavailable_warning(exc)
        with self.sessions_lock:
            if self._closed:
                if landlock_fd is not None:
                    os.close(landlock_fd)
                raise ToolFailure("SESSION_CLOSED", "Runtime is closed.", category="runtime")
            principal_id = str(args.get("principal_id", "default") or "").strip()[:64] or "default"
            principal_active = self.principal_active_counts.get(principal_id, 0)
            if len(self.sessions) + self.starting_sessions >= MAX_ACTIVE_EXEC_SESSIONS:
                if landlock_fd is not None:
                    os.close(landlock_fd)
                raise ToolFailure(
                    "SESSION_LIMIT_REACHED",
                    "Too many commands are already running or starting.",
                    category="runtime",
                    retryable=True,
                    details={"max_active_sessions": MAX_ACTIVE_EXEC_SESSIONS},
                )
            if principal_active >= processes.PRINCIPAL_MAX_ACTIVE_SESSIONS:
                if landlock_fd is not None:
                    os.close(landlock_fd)
                raise ToolFailure(
                    "SESSION_LIMIT_REACHED",
                    "This client already reached its per-principal command session quota.",
                    category="runtime",
                    retryable=True,
                    details={
                        "principal_id": principal_id,
                        "max_principal_sessions": processes.PRINCIPAL_MAX_ACTIVE_SESSIONS,
                        "principal_active": principal_active,
                    },
                )
            self.starting_sessions += 1
        process: subprocess.Popen[bytes] | None = None
        session: ExecSession | None = None
        admission = None
        registered = False
        slot_released = False
        try:
            command_id = secrets.token_urlsafe(18)
            projection = self.task_state.get().get("orchestration", {})
            projection = projection if isinstance(projection, dict) else {}
            projected_run = str(projection.get("run_id") or "").strip()
            projected_wave = str(projection.get("wave_id") or "").strip()
            requested_run = str(args.get("run_id") or "").strip()
            requested_wave = str(args.get("wave_id") or "").strip()
            if bool(requested_run) != bool(requested_wave):
                raise ToolFailure(
                    "INVALID_ARGUMENT",
                    "run_id and wave_id must be supplied together.",
                    category="validation",
                )
            if requested_run and projected_run and requested_run != projected_run:
                raise ToolFailure(
                    "EXECUTION_OWNER_MISMATCH",
                    "run_id does not match the task's current orchestration owner.",
                    category="runtime",
                    retryable=True,
                    details={"run_id": requested_run, "current_run_id": projected_run},
                )
            if requested_wave and projected_wave and requested_wave != projected_wave:
                raise ToolFailure(
                    "EXECUTION_OWNER_MISMATCH",
                    "wave_id does not match the task's current orchestration owner.",
                    category="runtime",
                    retryable=True,
                    details={"wave_id": requested_wave, "current_wave_id": projected_wave},
                )
            scope_checker = getattr(self.task_state, "is_scoped", None)
            scoped_projection = bool(scope_checker()) if callable(scope_checker) else False
            if requested_run:
                owner_run = requested_run
                owner_wave = requested_wave
            elif scoped_projection and projected_run and projected_wave:
                owner_run = projected_run
                owner_wave = projected_wave
            else:
                owner_run = ""
                owner_wave = ""
            command_workspace_identity = self._workspace_scope_identity(workdir)
            if owner_run:
                self._assert_orchestration_workspace_scope(command_workspace_identity, run_id=owner_run)
            try:
                admission = self.execution_resource_governor.admit(
                    command=cmd,
                    command_id=command_id,
                    run_id=owner_run,
                    wave_id=owner_wave,
                    owner=principal_id,
                    resource_class=args.get("resource_class", ""),
                    metadata={"workspace_identity": command_workspace_identity},
                )
            except ExecutionResourceError as exc:
                raise ToolFailure(
                    exc.code,
                    exc.message,
                    category="runtime",
                    retryable=exc.retryable,
                    details=exc.details,
                ) from exc
            process, pty_master_fd = spawn_process(
                popen_cmd,
                cwd=str(workdir.path),
                shell=popen_shell,
                env=env,
                tty=tty,
                popen_kwargs=popen_extra,
            )
            self.execution_resource_governor.bind_process(admission, process)
            session = self._make_session(
                process,
                session_id=command_id,
                managed_job_id=admission.job_id,
                owner_run_id=admission.run_id,
                owner_wave_id=admission.wave_id,
                resource_class=admission.resource_class,
                timeout_at=deadline,
                warnings=[landlock_warning] if landlock_warning else None,
                pty_master_fd=pty_master_fd,
            )
            try:
                self.task_state.record_command_started(
                    cmd,
                    session.session_id,
                    workdir.display,
                    owner_run_id=admission.run_id,
                    owner_wave_id=admission.wave_id,
                )
            except Exception:
                pass
            with self.sessions_lock:
                self.starting_sessions -= 1
                slot_released = True
                if not self._closed:
                    self.sessions[session.session_id] = session
                    self.session_principals[session.session_id] = principal_id
                    self.principal_active_counts[principal_id] = (
                        self.principal_active_counts.get(principal_id, 0) + 1
                    )
                    registered = True
            if not registered:
                raise ToolFailure("SESSION_CLOSED", "Runtime closed while the command was starting.", category="runtime")
        except Exception:
            with self.sessions_lock:
                if not registered and not slot_released:
                    self.starting_sessions -= 1
            if process is not None and process.poll() is None:
                terminate_process_group(process, signal.SIGTERM)
            if admission is not None:
                self.execution_resource_governor.spawn_failed(admission)
            raise
        finally:
            if landlock_fd is not None:
                try:
                    os.close(landlock_fd)
                except OSError:
                    pass
        assert session is not None
        request_id = getattr(self.request_context, "request_id", None)
        if isinstance(request_id, (str, int)) and not isinstance(request_id, bool):
            with self.request_sessions_lock:
                self.request_sessions[request_id] = session.session_id
        start_reader_threads(session)
        start_session_watchdog(session)
        try:
            if stdin_text:
                session.write_input(stdin_text.encode("utf-8"))
        except ToolFailure:
            if process.poll() is None:
                raise
        finally:
            if not tty:
                session.close_stdin()
        initial_wait = max(0, min(yield_ms, 30000)) / 1000.0

        def finish() -> dict[str, Any]:
            # snapshot_since_cursor owns the status mapping (running/exited/
            # terminated/timeout) so exec, polling, and kill paths agree.
            payload = session.snapshot_since_cursor(max_output_bytes)
            payload["elapsed_ms"] = int((time.time() - start) * 1000)
            self._add_exec_diagnostics(payload)
            return self._format_session_output(session, payload, args)

        def interrupted_by_task_control() -> str:
            try:
                status = str(self.task_state.get().get("status", ""))
            except Exception:
                return ""
            if status in {"paused", "stopped"} and process.poll() is None:
                terminate_process_group(process, signal.SIGTERM)
                session.refresh_status()
                session.drain_readers()
                return status
            return ""

        while True:
            interrupted = interrupted_by_task_control()
            if interrupted:
                payload = finish()
                payload["task_control"] = interrupted
                payload["status"] = interrupted
                return payload
            if process.poll() is not None:
                session.refresh_status()
                session.drain_readers()
                return finish()
            now = time.time()
            if not tty and now >= deadline:
                session.timed_out = True
                terminate_process_group(process, signal.SIGTERM)
                session.refresh_status()
                session.drain_readers()
                return finish()
            with session.lock:
                tty_has_initial_output = bool(
                    len(session.stdout) > session.stdout_cursor
                    or len(session.stderr) > session.stderr_cursor
                )
            if now - start >= initial_wait or (tty and tty_has_initial_output):
                return finish()
            time.sleep(0.02)

    def verify_build(self, args: dict[str, Any]) -> dict[str, Any]:
        resolved = self.resolve_existing(str(args.get("path", ".")))
        if not resolved.path.is_dir():
            raise ToolFailure("NOT_A_DIRECTORY", "Build verification path must be a directory.", category="validation")
        command_root = self.resolve_existing(str(args.get("workdir", args.get("path", "."))))
        if not command_root.path.is_dir():
            raise ToolFailure("NOT_A_DIRECTORY", "Build verification workdir must be a directory.", category="validation")
        owner_run = str(args.get("run_id") or "").strip()
        owner_wave = str(args.get("wave_id") or "").strip()
        if bool(owner_run) != bool(owner_wave):
            raise ToolFailure(
                "INVALID_ARGUMENT",
                "run_id and wave_id must be supplied together.",
                category="validation",
            )

        def runner(command: str, workdir: Path, timeout_seconds: int) -> dict[str, Any]:
            request_root = self._current_request_workspace_root().resolve(strict=False)
            try:
                relative = workdir.resolve(strict=False).relative_to(request_root).as_posix() or "."
            except ValueError as exc:
                raise ToolFailure(
                    "ORCHESTRATION_WORKSPACE_MISMATCH",
                    "Build verification workdir does not belong to the request-bound workspace.",
                    category="security",
                    retryable=False,
                ) from exc
            started = time.time()
            exec_args: dict[str, Any] = {
                "cmd": command,
                "workdir": relative,
                "timeout_ms": min(timeout_seconds * 1000, 600000),
                "yield_time_ms": 30000,
                "max_output_bytes": 131072,
                "verbosity": "summary",
            }
            if owner_run and owner_wave:
                exec_args.update({"run_id": owner_run, "wave_id": owner_wave})
            payload = self.exec_command(exec_args)
            while payload.get("status") == "running":
                payload = self.write_stdin({
                    "session_id": str(payload["session_id"]),
                    "chars": "",
                    "yield_time_ms": 30000,
                    "max_output_bytes": 131072,
                    "verbosity": "summary",
                })
            result = {
                "command": command,
                "status": "passed" if command_payload_succeeded(payload) else "failed",
                "exit_code": payload.get("exit_code"),
                "duration_ms": int((time.time() - started) * 1000),
                "summary": str(payload.get("summary") or payload.get("stderr") or payload.get("stdout") or "")[:4000],
            }
            return result

        report = run_build_verification(resolved.path, args, runner, command_root=command_root.path)
        hash_algorithm = str(report.get("hash_algorithm") or "sha256")
        for artifact in report.get("artifacts", []) if isinstance(report.get("artifacts"), list) else []:
            if not isinstance(artifact, dict):
                continue
            artifact_ref = build_file_artifact_ref(
                artifact,
                hash_algorithm=hash_algorithm,
                owner_run=owner_run,
                owner_wave=owner_wave,
            )
            if artifact_ref is not None:
                artifact["artifact_ref"] = artifact_ref
        try:
            self.task_state.record_build_report(report)
        except Exception:
            pass
        passed = report.get("overall_status") == "passed"
        report["ok"] = passed
        report["status"] = "passed" if passed else "failed"
        if not passed:
            report["error"] = {
                "code": "BUILD_VERIFICATION_FAILED",
                "message": str(report.get("failure") or "Build verification failed."),
                "category": "runtime",
                "retryable": True,
                "details": {},
            }
        return report

    def _check_command_policy(self, cmd: str, args: dict[str, Any]) -> None:
        if self.dangerously_skip_all_permissions:
            return
        self._check_command_paths(cmd)
        env = args.get("env", {})
        if isinstance(env, dict) and any(
            is_filtered_env_var(str(key), str(value)) for key, value in env.items()
        ):
            raise ToolFailure(
                "PERMISSION_REQUIRED",
                "Sensitive or loader/startup environment variables require explicit permission.",
                category="permission",
                details={"permission": "sensitive_env", "env_keys": sorted(str(key) for key in env)},
            )
        if not self.capabilities.inline_script:
            inline_script = inline_script_command(cmd)
            if inline_script is not None:
                raise ToolFailure(
                    "PERMISSION_REQUIRED",
                    "Inline interpreter or shell code requires explicit permission because network and filesystem effects cannot be verified statically.",
                    category="permission",
                    details={"permission": INLINE_SCRIPT_PERMISSION, **inline_script},
                )
        compact = " ".join(cmd.split()).lower()
        if not self.capabilities.shell_expansion and SHELL_EXPANSION_RE.search(cmd):
            raise ToolFailure(
                "PERMISSION_REQUIRED",
                "Shell command substitution and parameter expansion require explicit permission.",
                category="permission",
                details={"permission": "shell_expansion", "command": compact},
            )
        if re.search(r"(^|[;&|]\s*)rm\s+(-[^\s]*r[^\s]*f|-?[^\s]*f[^\s]*r)\s+/", compact):
            raise ToolFailure(
                "PERMISSION_REQUIRED",
                "Destructive commands are blocked without explicit permission.",
                category="permission",
                details={"permission": "destructive_command", "command": compact},
            )
        if DESTRUCTIVE_RE.search(cmd):
            raise ToolFailure(
                "PERMISSION_REQUIRED",
                "Destructive commands are blocked without explicit permission.",
                category="permission",
                details={"permission": "destructive_command", "command": compact},
            )
        if not self.allow_network and NETWORK_RE.search(cmd) and not is_literal_network_reference_command(cmd):
            raise ToolFailure(
                "PERMISSION_REQUIRED",
                "Network access is denied by default.",
                category="permission",
                details={"permission": "network", "command": compact},
            )

    def _add_exec_diagnostics(self, payload: dict[str, Any]) -> None:
        diagnostics = exec_output_diagnostics(payload)
        if diagnostics:
            payload["diagnostics"] = diagnostics

    def _check_command_paths(self, cmd: str) -> None:
        scannable = strip_heredoc_payloads(cmd)
        try:
            tokens = shlex_split(scannable)
        except ValueError:
            tokens = scannable.split()
        for executable in command_executables(tokens):
            self._reject_setuid_executable(executable)
        for candidate in explicit_command_path_candidates(tokens):
            self._check_command_path_candidate(candidate)

    def _check_command_path_candidate(self, candidate: str) -> None:
        candidate = candidate.strip()
        if not candidate or candidate in {"-", "--"}:
            return

        def escape_failure() -> ToolFailure:
            return ToolFailure(
                "PERMISSION_REQUIRED",
                "Command path escapes the workspace and is blocked.",
                category="permission",
                details={"permission": "filesystem_escape", "path": candidate},
            )

        if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*://", candidate):
            return
        normalized = candidate.replace("\\", "/")
        if normalized in SPECIAL_DEVICE_PATHS:
            return
        if self.is_allowed_command_tmp_path(normalized):
            return
        if (
            normalized.startswith("/")
            or normalized.startswith("~")
            or re.match(r"^[A-Za-z]:/", normalized)
            or any(part == ".." for part in PurePosixPath(normalized).parts)
        ):
            raise escape_failure()
        try:
            self.resolve_existing(normalized)
        except OSError as exc:
            raise ToolFailure(
                "INVALID_ARGUMENT",
                "Command path could not be inspected safely.",
                category="validation",
                details={"path": candidate[:200], "errno": exc.errno, "reason": exc.strerror},
            ) from exc
        except ToolFailure as exc:
            if exc.code == "NOT_FOUND":
                try:
                    self.resolve_for_write(normalized)
                except ToolFailure as write_exc:
                    if write_exc.code == "NOT_FOUND":
                        return
                    if write_exc.code in {"PATH_OUTSIDE_WORKSPACE", "ABSOLUTE_PATH_DENIED", "SYMLINK_ESCAPE"}:
                        raise escape_failure() from write_exc
                    raise
                return
            if exc.code in {"PATH_OUTSIDE_WORKSPACE", "ABSOLUTE_PATH_DENIED", "SYMLINK_ESCAPE"}:
                raise escape_failure() from exc

    def _reject_setuid_executable(self, executable: str) -> None:
        if not executable:
            return
        executable_path = Path(executable) if "/" in executable else Path(shutil.which(executable) or "")
        if not str(executable_path):
            return
        try:
            stat = executable_path.stat()
        except OSError:
            return
        if stat.st_mode & 0o6000:
            raise ToolFailure(
                "PERMISSION_REQUIRED",
                "Setuid/setgid executables are denied because they can bypass runtime process guards.",
                category="permission",
                details={"permission": "privileged_executable", "path": str(executable_path)},
            )

    def _command_env(self, extra: Any) -> dict[str, str]:
        env = self._base_command_env()
        if not self.dangerously_skip_all_permissions:
            env = {key: value for key, value in env.items() if not is_filtered_env_var(key, value)}
            env = {key: value for key, value in env.items() if key not in ECOSYSTEM_CACHE_ENV_NAMES}
        if self.shell_env_policy.exclude:
            env = {
                key: value
                for key, value in env.items()
                if not env_pattern_matches(key, self.shell_env_policy.exclude)
            }
        if self.shell_env_policy.include_only:
            env = {
                key: value
                for key, value in env.items()
                if env_pattern_matches(key, self.shell_env_policy.include_only)
            }
        env.update({str(key): str(value) for key, value in self.shell_env_policy.set.items()})
        self._ensure_runtime_dirs()
        tmp_dir = self.command_tmp_dir()
        env["HOME"] = str(self.command_home_dir())
        env["TMPDIR"] = str(tmp_dir)
        if os.name == "nt":
            env["TEMP"] = str(tmp_dir)
            env["TMP"] = str(tmp_dir)
        if isinstance(extra, dict):
            for key, value in extra.items():
                key_text = str(key)
                value_text = str(value)
                if not self.dangerously_skip_all_permissions and is_filtered_env_var(key_text, value_text):
                    continue
                env[key_text] = value_text
        return env

    def _git_env(self) -> dict[str, str]:
        return self._command_env({})

    def _run_git_text(
        self, cmd: list[str], *, timeout: int | None = None, env: dict[str, str] | None = None
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            cmd,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            env=self._git_env() if env is None else env,
            **hidden_process_popen_kwargs(),
        )

    def _run_git_bytes(
        self, cmd: list[str], *, timeout: int | None = None, env: dict[str, str] | None = None
    ) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            cmd,
            text=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            env=self._git_env() if env is None else env,
            **hidden_process_popen_kwargs(),
        )

    def _git_status_not_repo(self, completed: subprocess.CompletedProcess[str]) -> dict[str, Any]:
        warnings = []
        stderr = completed.stderr.strip()
        if stderr:
            warnings.append(f"git rev-parse failed: {stderr}")
        return {"is_repo": False, "clean": True, "entries": [], "truncated": False, "warnings": warnings}

    def _is_git_repo(self, path: Path, *, env: dict[str, str] | None = None) -> bool:
        completed = self._run_git_text(
            [require_git(), "-C", str(path), "rev-parse", "--is-inside-work-tree"], env=env
        )
        return completed.returncode == 0 and completed.stdout.strip() == "true"

    def _git_rev_parse(self, path: Path, rev: str, *, env: dict[str, str] | None = None) -> str:
        completed = self._run_git_text([require_git(), "-C", str(path), "rev-parse", rev], env=env)
        return completed.stdout.strip() if completed.returncode == 0 else ""

    def _git_path_filters(self, args: dict[str, Any]) -> list[str]:
        path_filters: list[str] = []
        if isinstance(args.get("path"), str):
            path_filters.append(str(args["path"]))
        if isinstance(args.get("paths"), list):
            path_filters.extend(str(item) for item in args["paths"])
        return [self.git_path_filter(path) for path in path_filters]

    def _base_command_env(self) -> dict[str, str]:
        if self.shell_env_policy.inherit == "none":
            return {}
        if self.shell_env_policy.inherit == "all":
            return {str(key): str(value) for key, value in os.environ.items()}
        return {
            str(key): str(value)
            for key, value in os.environ.items()
            if is_core_command_env_name(str(key))
        }
