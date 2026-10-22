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
from .approved_patch_verification import require_initial_verification_origin
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
from .runtime_config import env_pattern_matches, is_core_command_env_name, is_filtered_env_var, is_sandboxed_execution
from .task_state import command_payload_succeeded
from .windows_mxc_sandbox import build_mxc_invocation, cleanup_mxc_invocation
from .windows_execution_policy import WindowsExecutionDecision, decide_windows_execution
from .windows_mxc_state_aware import (
    MxcWindowsSandboxManager,
    build_mxc_windows_sandbox_invocation,
    cleanup_mxc_windows_sandbox_invocation,
    windows_sandbox_feature_enabled,
)
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
    def _exec_public_schema_arguments(self, args: dict[str, Any]) -> dict[str, Any]:
        """Keep local attested routing policy outside the public MCP schema."""
        identity = self._current_hub_client()
        if args.get("argv") is not None and isinstance(identity, dict) \
                and identity.get("client_id") == "electron-control-plane-exec-bridge" \
                and identity.get("client_type") == "electron" \
                and identity.get("attestation_verified") is True:
            return {key: value for key, value in args.items()
                    if key not in {"_windows_execution_mode", "_windows_native_argv_prefixes"}}
        return args

    def exec_command(self, args: dict[str, Any]) -> dict[str, Any]:
        self._prune_sessions()
        bridge_argv = args.get("argv")
        raw_argv = args.get("_argv")
        structured_argv: list[str] | None = None
        if bridge_argv is not None:
            identity = self._current_hub_client()
            if not isinstance(identity, dict) or identity.get("client_id") != "electron-control-plane-exec-bridge" \
                    or identity.get("client_type") != "electron" \
                    or identity.get("attestation_verified") is not True:
                raise ToolFailure(
                    "CONTROL_PLANE_STRUCTURED_ARGV_DENIED",
                    "Structured argv is reserved for the attested local control-plane bridge.",
                    category="security",
                )
            if raw_argv is not None or not isinstance(bridge_argv, list) or not bridge_argv or len(bridge_argv) > 32:
                raise ToolFailure(
                    "INVALID_ARGUMENT",
                    "Control-plane structured argv must be a bounded non-empty string array.",
                    category="validation",
                )
            structured_argv = [str(item) for item in bridge_argv]
            if any(
                not item
                or "\x00" in item
                or "\r" in item
                or "\n" in item
                or any(token in item for token in (";", "&&", "||", "`", "$(", "|", ">", "<"))
                for item in structured_argv
            ):
                raise ToolFailure(
                    "INVALID_ARGUMENT",
                    "Control-plane structured argv contains an unsafe argument.",
                    category="validation",
                )
            if len("\0".join(structured_argv).encode("utf-8")) > 8_192:
                raise ToolFailure(
                    "INVALID_ARGUMENT",
                    "Control-plane structured argv exceeds its bounded size.",
                    category="validation",
                )
            if str(args.get("cmd", "")) != structured_argv[0]:
                raise ToolFailure(
                    "INVALID_ARGUMENT",
                    "Control-plane cmd must equal the structured executable name.",
                    category="validation",
                )
            # This string is an audit/resource label only. It is never supplied
            # to a shell: process creation below uses the original argv list.
            cmd = structured_argv[0]
        elif raw_argv is not None:
            if args.get("_approved_patch_verification_origin") is not None:
                require_initial_verification_origin(self, args)
            elif args.get("_continuation_internal") is not True:
                raise ToolFailure(
                    "INTERNAL_STRUCTURED_ARGV_DENIED",
                    "Structured argv execution is reserved for the continuation proof driver.",
                    category="security",
                )
            if "cmd" in args:
                raise ToolFailure("INVALID_ARGUMENT", "Internal structured argv execution cannot also receive cmd.", category="validation")
            if not isinstance(raw_argv, list) or not raw_argv or len(raw_argv) > 32:
                raise ToolFailure("INVALID_ARGUMENT", "Internal structured argv must be a bounded non-empty string array.", category="validation")
            structured_argv = [str(item) for item in raw_argv]
            if any(not item or "\x00" in item or "\r" in item or "\n" in item for item in structured_argv):
                raise ToolFailure("INVALID_ARGUMENT", "Internal structured argv contains an unsafe argument.", category="validation")
            if len("\0".join(structured_argv).encode("utf-8")) > 8_192:
                raise ToolFailure("INVALID_ARGUMENT", "Internal structured argv exceeds its bounded size.", category="validation")
            # This string is an audit/resource label only. It is never supplied
            # to a shell: process creation below uses the original argv list.
            cmd = " ".join(structured_argv)
        else:
            cmd = str(args.get("cmd", ""))
            if not cmd:
                raise ToolFailure("INVALID_ARGUMENT", "cmd is required.", category="validation")
        workdir_arg = args.get("workdir", args.get("cwd", "."))
        if "workdir" in args and "cwd" in args and str(args["workdir"]) != str(args["cwd"]):
            raise ToolFailure("INVALID_ARGUMENT", "workdir and cwd refer to different directories.", category="validation")
        workdir = self.resolve_existing(str(workdir_arg))
        if not workdir.path.is_dir():
            raise ToolFailure("NOT_A_DIRECTORY", "workdir is not a directory.", category="validation")
        if structured_argv is None:
            self._check_command_policy(cmd, args)
        else:
            self._check_structured_argv_policy(structured_argv, args)
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
        popen_cmd: Any = structured_argv if structured_argv is not None else cmd
        popen_shell = structured_argv is None
        popen_extra = process_group_popen_kwargs()
        # The operator's local mode runs as the host user. Keep its evidence
        # distinct from the native ProcessContainer and isolated VM backends.
        windows_local = os.name == "nt" and not is_sandboxed_execution()
        windows_mxc = (
            os.name == "nt"
            and structured_argv is not None
            and not windows_local
        )
        windows_decision = None
        if windows_local:
            windows_decision = WindowsExecutionDecision("local", "host_user", "operator_local", tuple(structured_argv or ()))
        elif windows_mxc:
            windows_decision = decide_windows_execution(
                structured_argv, args, attested_bridge=bridge_argv is not None,
                approved_internal_argv=raw_argv is not None,
            )
        windows_mxc_invocation = None
        windows_mxc_stateful = False
        windows_mxc_session_holder: dict[str, ExecSession | None] = {"session": None}
        sandbox_cleanup_callback = None
        if self.landlock_enabled() and not windows_mxc:
            try:
                landlock_fd = open_landlock_ruleset(
                    self._current_request_workspace_root(),
                    guard_allow_roots(),
                    write_roots=self.landlock_write_roots(),
                )
                popen_cmd = landlock_exec_argv(landlock_fd, popen_cmd)
                popen_shell = False
                popen_extra["pass_fds"] = (landlock_fd,)
            except ToolFailure as exc:
                if exc.code != "SANDBOX_UNAVAILABLE":
                    raise
                landlock_warning = landlock_unavailable_warning(exc)
        no_start_details = {"execution_started": False} if args.get("_approved_patch_verification_origin") is not None else {}
        with self.activation_lock, self.sessions_lock:
            try:
                self._activation_require_executor_available_locked()
                self._activation_cleanup_locked()
                if self.activation_fence:
                    raise ToolFailure(
                        "RUNTIME_ACTIVATION_PENDING",
                        "The runtime is draining for a controlled code activation; retry after reconnect.",
                        category="runtime", retryable=True,
                        details={"operation_id": str(self.activation_fence.get("operation_id") or "")},
                    )
            except ToolFailure as exc:
                if no_start_details:
                    exc.details = {**exc.details, **no_start_details}
                if landlock_fd is not None:
                    os.close(landlock_fd)
                raise
            if self._closed:
                if landlock_fd is not None:
                    os.close(landlock_fd)
                raise ToolFailure("SESSION_CLOSED", "Runtime is closed.", category="runtime", details=no_start_details)
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
                    details={"max_active_sessions": MAX_ACTIVE_EXEC_SESSIONS, **no_start_details},
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
                        **no_start_details,
                    },
                )
            self.starting_sessions += 1
        process: subprocess.Popen[bytes] | None = None
        spawn_attempted = False
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
                    metadata={
                        "workspace_identity": command_workspace_identity,
                        **(windows_decision.metadata() if windows_decision is not None else {}),
                    },
                )
            except ExecutionResourceError as exc:
                raise ToolFailure(
                    exc.code,
                    exc.message,
                    category="runtime",
                    retryable=exc.retryable,
                    details=exc.details,
                ) from exc
            if windows_mxc:
                workspace_root = self._current_request_workspace_root()
                if windows_decision.execution_backend == "isolated":
                    if not windows_sandbox_feature_enabled():
                        raise ToolFailure(
                            "WINDOWS_SANDBOX_FEATURE_DISABLED",
                            "This command requires the isolated Windows Sandbox runner.",
                            category="security", details={"execution_started": False, **windows_decision.metadata()},
                        )
                    with self.sessions_lock:
                        sandbox_manager = getattr(self, "_windows_mxc_sandbox_manager", None)
                        if sandbox_manager is None:
                            sandbox_manager = MxcWindowsSandboxManager()
                            self._windows_mxc_sandbox_manager = sandbox_manager
                    invocation = build_mxc_windows_sandbox_invocation(
                        list(windows_decision.argv),
                        manager=sandbox_manager,
                        workspace_root=workspace_root,
                        workdir=workdir.path,
                        timeout_ms=timeout_ms,
                        extra_environment=args.get("env", {}),
                        tty=tty,
                    )
                    windows_mxc_stateful = True
                    def cleanup_stateful_sandbox() -> bool:
                        session_state = windows_mxc_session_holder["session"]
                        abort = session_state is None or bool(
                            session_state.timed_out
                            or session_state.sandbox_abort_on_cleanup
                            or session_state.signal_name is not None
                        )
                        return cleanup_mxc_windows_sandbox_invocation(invocation, abort=abort, retire_when_idle=False)
                    sandbox_cleanup_callback = cleanup_stateful_sandbox
                else:
                    invocation = build_mxc_invocation(
                        list(windows_decision.argv),
                        workspace_root=workspace_root,
                        workdir=workdir.path,
                        timeout_ms=timeout_ms,
                        extra_environment=args.get("env", {}),
                        allow_workspace_executable=windows_decision.policy_decision != "native_safe_command",
                    )
                    sandbox_cleanup_callback = lambda: cleanup_mxc_invocation(invocation)
                windows_mxc_invocation = invocation
                popen_cmd = list(invocation.argv)
                popen_shell = False
                env = invocation.environment
                # VM startup is a separate lifecycle phase, not command runtime.
                deadline = time.time() + (timeout_ms / 1000.0)
            if args.get("_approved_patch_verification_origin") is not None:
                require_initial_verification_origin(self, args)
            spawn_attempted = True
            process, pty_master_fd = spawn_process(
                popen_cmd,
                cwd=str(workdir.path),
                shell=popen_shell,
                env=env,
                tty=tty,
                popen_kwargs=popen_extra,
                **({"windows_job_limits": processes.WindowsJobLimits(cpu_time_ms=timeout_ms)}
                   if windows_decision is not None and windows_decision.execution_backend in {"native", "local"} else {}),
            )
            self.execution_resource_governor.bind_process(admission, process)
            session_warnings = [landlock_warning] if landlock_warning else []
            if windows_mxc_invocation is not None and getattr(windows_mxc_invocation, "cwd_alias_path", None) is not None:
                session_warnings.append(
                    "Windows sandbox uses a temporary system-drive junction for this non-system-drive working directory; "
                    "the junction targets the registered workspace and is removed when the process tree ends."
                )
            session = self._make_session(
                process,
                session_id=command_id,
                managed_job_id=admission.job_id,
                owner_run_id=admission.run_id,
                owner_wave_id=admission.wave_id,
                resource_class=admission.resource_class,
                timeout_at=deadline,
                warnings=session_warnings or None,
                pty_master_fd=pty_master_fd,
                cleanup_callback=sandbox_cleanup_callback,
                execution_metadata=windows_decision.metadata() if windows_decision is not None else None,
            )
            if windows_mxc_stateful:
                windows_mxc_session_holder["session"] = session
                session.sandbox_idle_generation = windows_mxc_invocation.lease_generation
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
        except Exception as error:
            if (args.get("_approved_patch_verification_origin") is not None and not spawn_attempted
                    and process is None and isinstance(error, ToolFailure)):
                error.details = {**error.details, "execution_started": False}
            with self.sessions_lock:
                if not registered and not slot_released:
                    self.starting_sessions -= 1
            if process is not None and process.poll() is None:
                terminate_process_group(process, signal.SIGTERM)
            if sandbox_cleanup_callback is not None and (process is None or process.poll() is not None):
                sandbox_cleanup_callback()
            if admission is not None:
                self.execution_resource_governor.spawn_failed(admission)
                # A lifecycle rejection before Popen is a known failure of
                # this command, even when starting a new VM can be retried.
                # Bind that claim to the durable Job; a code alone is not proof.
                if not spawn_attempted and process is None and isinstance(error, ToolFailure):
                    try:
                        job = self.execution_resource_governor.find_exact_job(
                            command_id=command_id, job_id=admission.job_id,
                        )
                    except Exception:
                        # Unavailable evidence must not replace the original
                        # failure or manufacture a settled execution outcome.
                        job = None
                    if (
                        job is not None
                        and job.get("command_id") == command_id
                        and job.get("job_id") == admission.job_id
                        and job.get("lifecycle_state") == "spawn_failed"
                        and job.get("root_pid") == 0
                        and job.get("finished_at")
                    ):
                        error.details = {
                            **error.details,
                            "command_id": job["command_id"],
                            "job_id": job["job_id"],
                            "job_lifecycle": "spawn_failed",
                            "root_pid": 0,
                            "execution_started": False,
                            "job_finished_at": job["finished_at"],
                        }
                        error.retryable = False
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
                session.sandbox_abort_on_cleanup = True
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
            continuous_check = getattr(self, "_run_continuous_check", None)
            if callable(continuous_check):
                # Automatic build verification is part of the same workflow
                # budget as the checks before it. Reusing the cancellation-aware
                # command runner prevents a late build from receiving a fresh,
                # independent 600-second deadline.
                return continuous_check(
                    command,
                    relative,
                    min(timeout_seconds * 1000, 600000),
                    owner_run_id=owner_run,
                    owner_wave_id=owner_wave,
                )

            # Compatibility fallback for a narrow non-Runtime embedding.
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
            return {
                "command": command,
                "status": "passed" if command_payload_succeeded(payload) else "failed",
                "exit_code": payload.get("exit_code"),
                "duration_ms": int((time.time() - started) * 1000),
                "summary": str(payload.get("summary") or payload.get("stderr") or payload.get("stdout") or "")[:4000],
                "cancelled": bool(payload.get("cancelled")),
                "timed_out": bool(payload.get("timed_out")),
            }

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
            failed_stage = next(
                (
                    (name, result)
                    for name, result in (("test", report.get("test_result")), ("build", report.get("build_result")))
                    if isinstance(result, dict) and result.get("status") != "passed"
                ),
                ("verification", {}),
            )
            failed_stage_name, failed_stage_result = failed_stage
            if bool(failed_stage_result.get("cancelled")):
                code = "WORKFLOW_RUNTIME_EXCEEDED"
                category = "policy"
                retryable = False
                message = "Build verification was cancelled because the enclosing workflow runtime budget expired."
            elif bool(failed_stage_result.get("timed_out")):
                code = "BUILD_VERIFICATION_TIMEOUT"
                category = "runtime"
                retryable = True
                message = "Build verification command exceeded its own bounded runtime."
            else:
                code = "BUILD_VERIFICATION_FAILED"
                category = "runtime"
                retryable = True
                message = str(report.get("failure") or "Build verification failed.")
            report["error"] = {
                "code": code,
                "message": message,
                "category": category,
                "retryable": retryable,
                "details": {
                    "stage": failed_stage_name,
                    "timed_out": bool(failed_stage_result.get("timed_out")),
                    "cancelled": bool(failed_stage_result.get("cancelled")),
                    "budget_limited": bool(failed_stage_result.get("budget_limited")),
                },
            }
        return report

    def _check_structured_argv_policy(self, argv: list[str], args: dict[str, Any]) -> None:
        """Validate the continuation driver's fixed argv without re-parsing it as shell text.

        The continuation grant already binds the exact argv. This guard defends
        the execution boundary itself: no caller can smuggle a public command
        through the private path, no shell is selected, and network/destructive
        command classes remain subject to the runtime permission posture.
        """
        if not argv:
            raise ToolFailure("INVALID_ARGUMENT", "Internal structured argv is empty.", category="validation")
        executable = Path(argv[0]).name.lower()
        if executable in {
            "bash", "bash.exe", "cmd", "cmd.exe", "powershell", "powershell.exe",
            "pwsh", "pwsh.exe", "sh", "sh.exe", "wscript.exe", "cscript.exe", "zsh", "zsh.exe",
        }:
            raise ToolFailure("INTERNAL_STRUCTURED_ARGV_DENIED", "Internal structured argv cannot invoke a shell.", category="security")
        compact = " ".join(argv).lower()
        if not self.dangerously_skip_all_permissions:
            env = args.get("env", {})
            if isinstance(env, dict) and any(is_filtered_env_var(str(key), str(value)) for key, value in env.items()):
                raise ToolFailure("PERMISSION_REQUIRED", "Sensitive environment variables require explicit permission.", category="permission")
            if DESTRUCTIVE_RE.search(compact):
                raise ToolFailure("PERMISSION_REQUIRED", "Destructive commands are blocked without explicit permission.", category="permission")
            if not self.allow_network and NETWORK_RE.search(compact) and not is_literal_network_reference_command(compact):
                raise ToolFailure("PERMISSION_REQUIRED", "Network access is denied by default.", category="permission")
        self._reject_setuid_executable(argv[0])

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
