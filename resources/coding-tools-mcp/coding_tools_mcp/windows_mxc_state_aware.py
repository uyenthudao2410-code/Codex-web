"""State-aware Windows Sandbox adapter for structured workspace commands.

This backend is deliberately separate from the ProcessContainer adapter.  It
uses a pinned, source-built MXC candidate and keeps one Windows Sandbox VM alive
for the lifetime of a Python Runtime, serializing commands because MXC's guest
protocol is single-flight.  The only writable host share is the selected
workspace; approved toolchain directories are mounted read-only; guest network
access is blocked by the Windows Sandbox backend.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .errors import ToolFailure
from .fs_utils import is_relative_to
from .windows_mxc_sandbox import (
    MAX_MXC_CONFIG_ARGUMENT_CHARS,
    _ENV_NAME,
    _RESERVED_ENV_NAMES,
    _SHELL_NAMES,
    _known_toolchains,
    _resolve_executable,
    _system_root,
    _under,
)
from .runtime_config import is_filtered_env_var


MXC_WSB_SOURCE_COMMIT = "cbe1774364ea2ec846f56ab744e43a416f751420"
MXC_WSB_SCHEMA_VERSION = "0.10.0-alpha"
MXC_WSB_LOCAL_PATCH_SHA256 = "85a0991dd4473b31574ad6c71d2c489389e6719a3e6ef9116f5f9156a7b7c8df"
MXC_WSB_BINARY_NAMES = (
    "wxc-exec.exe",
    "wxc-windows-sandbox-daemon.exe",
    "wxc-windows-sandbox-guest.exe",
)
GUEST_WORKSPACE_SHARE = r"C:\CodexWorkspace\share-0"
GUEST_TOOLCHAIN_SHARE_PREFIX = r"C:\CodexToolchains\share-"
MAX_MXC_WSB_PHASE_SECONDS = 210
MAX_MXC_WSB_PHASE_OUTPUT_BYTES = 32 * 1024
MAX_MXC_WSB_PROBE_SECONDS = 75
MAX_MXC_WSB_PROBE_OUTPUT_BYTES = 16 * 1024
_SANDBOX_ID = re.compile(r"^wsb:[0-9a-f]{8}$")

_POWERSHELL_LAUNCHER = r"""
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$requestPath = '__REQUEST_PATH__'
$request = Get-Content -LiteralPath $requestPath -Raw -Encoding UTF8 | ConvertFrom-Json

function Quote-NativeArgument([string]$value) {
  if ($value.Length -gt 0 -and $value -notmatch '[\s"]') { return $value }
  $quoted = $value -replace '(\\*)"', '$1$1\"'
  $quoted = $quoted -replace '(\\+)$', '$1$1'
  return '"' + $quoted + '"'
}

if (-not $request -or -not $request.argv -or $request.argv.Count -lt 1) { exit 126 }
$start = New-Object System.Diagnostics.ProcessStartInfo
$start.FileName = [string]$request.argv[0]
$quoted = New-Object 'System.Collections.Generic.List[string]'
for ($index = 1; $index -lt $request.argv.Count; $index++) {
  [void]$quoted.Add((Quote-NativeArgument ([string]$request.argv[$index])))
}
$start.Arguments = $quoted -join ' '
$start.WorkingDirectory = [string]$request.cwd
$start.UseShellExecute = $false
$start.CreateNoWindow = $true
$start.RedirectStandardInput = $true
$start.RedirectStandardOutput = $true
$start.RedirectStandardError = $true

$start.EnvironmentVariables['TEMP'] = [string]$request.temp
$start.EnvironmentVariables['TMP'] = [string]$request.temp
$start.EnvironmentVariables['TMPDIR'] = [string]$request.temp
$start.EnvironmentVariables['USERPROFILE'] = [string]$request.profile
$start.EnvironmentVariables['HOME'] = [string]$request.profile
$start.EnvironmentVariables['APPDATA'] = [string]$request.appdata
$start.EnvironmentVariables['LOCALAPPDATA'] = [string]$request.localAppdata
$start.EnvironmentVariables['NPM_CONFIG_CACHE'] = [string]$request.npmCache
$start.EnvironmentVariables['NODE_OPTIONS'] = '--preserve-symlinks --preserve-symlinks-main'
$start.EnvironmentVariables['COMSPEC'] = Join-Path $env:SystemRoot 'System32\cmd.exe'
$start.EnvironmentVariables['PATHEXT'] = '.COM;.EXE;.BAT;.CMD'
$start.EnvironmentVariables['PATH'] = @($request.pathEntries) -join ';'
foreach ($entry in $request.env.PSObject.Properties) {
  $start.EnvironmentVariables[$entry.Name] = [string]$entry.Value
}

$child = New-Object System.Diagnostics.Process
$child.StartInfo = $start
if (-not $child.Start()) { exit 126 }
$stdout = $child.StandardOutput.BaseStream.CopyToAsync([Console]::OpenStandardOutput())
$stderr = $child.StandardError.BaseStream.CopyToAsync([Console]::OpenStandardError())
$stdin = [Console]::OpenStandardInput().CopyToAsync($child.StandardInput.BaseStream)
$child.WaitForExit()
try { $child.StandardInput.Close() } catch {}
try { [void]($stdout.GetAwaiter().GetResult()) } catch {}
try { [void]($stderr.GetAwaiter().GetResult()) } catch {}
try { [void]($stdin.GetAwaiter().GetResult()) } catch {}
exit $child.ExitCode
""".strip()


def _failure(code: str, message: str, *, retryable: bool = False, **details: Any) -> ToolFailure:
    return ToolFailure(
        code,
        message,
        category="security",
        retryable=retryable,
        details=details or None,
    )


def _resource_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _windows_sandbox_path() -> Path:
    system_root = _system_root()
    return system_root / "System32" / "WindowsSandbox.exe"


def windows_sandbox_feature_enabled() -> bool:
    """Return whether the optional feature has installed its host executable."""

    if os.name != "nt":
        return False
    try:
        return _windows_sandbox_path().is_file()
    except OSError:
        return False


def _executor_directory() -> Path:
    return _resource_root() / "tools" / "mxc-windows-sandbox"


def verify_mxc_windows_sandbox_candidate() -> dict[str, str]:
    """Verify the exact three source-built MXC files used by this adapter."""

    if os.name != "nt":
        raise _failure("SANDBOX_UNAVAILABLE", "Windows Sandbox execution is available only on Windows.")
    try:
        sandbox_binary = _windows_sandbox_path()
        if not sandbox_binary.is_file():
            raise _failure("WINDOWS_SANDBOX_FEATURE_DISABLED", "Enable Windows Sandbox and restart Windows before using this backend.")
    except ToolFailure:
        raise
    except OSError as error:
        raise _failure("WINDOWS_SANDBOX_FEATURE_DISABLED", "Windows Sandbox is not available on this machine.") from error

    directory = _executor_directory()
    provenance_path = directory / "mxc-windows-sandbox.provenance.json"
    try:
        provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise _failure("SANDBOX_CANDIDATE_PROVENANCE_INVALID", "The MXC Windows Sandbox build provenance is missing or invalid.") from error
    expected_fields = {
        "authenticode", "backend", "binaries", "build_profile", "component",
        "distribution", "experimental", "license", "lifecycle",
        "local_patch_file", "local_patch_sha256", "mxc_crate_version",
        "rustc", "schema_version", "source_commit", "source_commit_signature",
        "source_repository", "target",
    }
    if (
        not isinstance(provenance, dict)
        or set(provenance) != expected_fields
        or provenance.get("component") != "Microsoft MXC Windows Sandbox state-aware candidate"
        or provenance.get("source_repository") != "https://github.com/microsoft/mxc"
        or provenance.get("source_commit") != MXC_WSB_SOURCE_COMMIT
        or provenance.get("local_patch_file") != "scripts/patches/mxc-windows-sandbox-c-drive-share.patch"
        or provenance.get("local_patch_sha256") != MXC_WSB_LOCAL_PATCH_SHA256
        or provenance.get("source_commit_signature") != "unsigned"
        or provenance.get("mxc_crate_version") != "0.8.0"
        or provenance.get("schema_version") != MXC_WSB_SCHEMA_VERSION
        or provenance.get("backend") != "windows_sandbox"
        or provenance.get("lifecycle") != "state-aware"
        or provenance.get("experimental") is not True
        or provenance.get("build_profile") != "release"
        or provenance.get("target") != "x86_64-pc-windows-msvc"
        or provenance.get("authenticode") != "unsigned-local-source-build"
        or provenance.get("distribution") != "development-candidate-only"
        or provenance.get("license") != "MIT"
        or not isinstance(provenance.get("rustc"), str)
        or not isinstance(provenance.get("binaries"), dict)
        or set(provenance["binaries"]) != set(MXC_WSB_BINARY_NAMES)
    ):
        raise _failure("SANDBOX_CANDIDATE_PROVENANCE_INVALID", "The MXC Windows Sandbox provenance does not match the pinned source and patch.")

    observed: dict[str, str] = {}
    for name in MXC_WSB_BINARY_NAMES:
        path = directory / name
        try:
            metadata = path.stat()
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_size <= 0:
                raise OSError("not a regular file")
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError as error:
            raise _failure("SANDBOX_UNAVAILABLE", "The pinned MXC Windows Sandbox candidate is incomplete.", binary=name) from error
        receipt = provenance["binaries"].get(name)
        if (
            not isinstance(receipt, dict)
            or set(receipt) != {"sha256", "size_bytes"}
            or not re.fullmatch(r"[a-f0-9]{64}", str(receipt.get("sha256", "")))
            or not isinstance(receipt.get("size_bytes"), int)
            or isinstance(receipt.get("size_bytes"), bool)
            or receipt["size_bytes"] <= 0
            or metadata.st_size != receipt["size_bytes"]
            or digest != receipt["sha256"]
        ):
            raise _failure("SANDBOX_BINARY_INTEGRITY_FAILED", "The MXC Windows Sandbox candidate failed its build-provenance hash/size check.", binary=name)
        observed[name] = digest
    return observed


def _windows_path_key(path: Path) -> str:
    return os.path.normcase(os.path.normpath(str(path))).casefold()


def _guest_share_map(workspace_root: Path, readonly_roots: list[Path]) -> list[tuple[Path, str]]:
    """Mirror the pinned MXC patch's host→C: guest folder destinations."""

    result = [(workspace_root, GUEST_WORKSPACE_SHARE)]
    result.extend(
        (root, GUEST_TOOLCHAIN_SHARE_PREFIX + str(index))
        for index, root in enumerate(readonly_roots)
    )
    return result


def _guest_path_for_host(
    host_path: str | Path,
    mappings: list[tuple[Path, str]],
) -> str:
    """Translate an absolute host path only when it is inside a mapped share."""

    raw = str(host_path)
    candidate = Path(raw)
    if not candidate.is_absolute():
        return raw
    try:
        resolved = candidate.resolve(strict=False)
    except (OSError, RuntimeError, ValueError):
        resolved = candidate
    for host_root, guest_root in mappings:
        if not _under(resolved, host_root):
            continue
        try:
            relative = resolved.relative_to(host_root)
        except ValueError:
            continue
        parts = [str(part) for part in relative.parts if str(part) not in ("", ".")]
        return guest_root if not parts else guest_root.rstrip("\\") + "\\" + "\\".join(parts)
    return raw


def _guest_environment_value(value: str, mappings: list[tuple[Path, str]]) -> str:
    """Translate absolute path values and semicolon-delimited path lists."""

    raw = str(value)
    if ";" in raw:
        entries = raw.split(";")
        if any(Path(entry).is_absolute() for entry in entries if entry.strip()):
            return ";".join(_guest_path_for_host(entry, mappings) for entry in entries)
    return _guest_path_for_host(raw, mappings)


def _host_toolchains(system_root: Path, workspace_root: Path) -> tuple[list[Path], list[Path]]:
    """Return non-overlapping, read-only roots needed by approved dev tools."""

    legacy_executor_path = _resource_root() / "tools" / "wxc-exec.exe"
    roots, path_entries = _known_toolchains(system_root, legacy_executor_path)
    system32 = (system_root / "System32").resolve(strict=True)
    bundled_tools = (_resource_root() / "tools").resolve(strict=False)
    native_python = _resource_root() / "native-python"

    filtered_roots: list[Path] = []
    for root in roots:
        try:
            canonical = root.resolve(strict=True)
        except OSError:
            continue
        if _windows_path_key(canonical) in {
            _windows_path_key(system32),
            _windows_path_key(bundled_tools),
        }:
            continue
        if _under(canonical, workspace_root):
            continue
        if _under(workspace_root, canonical):
            raise _failure(
                "SANDBOX_TOOLCHAIN_WORKSPACE_OVERLAP",
                "The selected workspace is nested inside an approved host toolchain; refusing to widen the mapped write scope.",
            )
        if canonical not in filtered_roots:
            filtered_roots.append(canonical)

    if native_python.is_dir():
        try:
            canonical_python = native_python.resolve(strict=True)
        except OSError as error:
            raise _failure("SANDBOX_TOOLCHAIN_UNAVAILABLE", "The bundled Python toolchain could not be resolved.") from error
        if not _under(canonical_python, workspace_root) and canonical_python not in filtered_roots:
            if _under(workspace_root, canonical_python):
                raise _failure("SANDBOX_TOOLCHAIN_WORKSPACE_OVERLAP", "The bundled Python toolchain overlaps the selected workspace.")
            filtered_roots.append(canonical_python)
            path_entries.append(canonical_python)

    filtered_paths: list[Path] = []
    for item in path_entries:
        try:
            canonical = item.resolve(strict=True)
        except OSError:
            continue
        if _windows_path_key(canonical) == _windows_path_key(system32):
            continue
        if _windows_path_key(canonical) == _windows_path_key(bundled_tools):
            continue
        if _under(canonical, workspace_root):
            continue
        if canonical.is_dir() and canonical not in filtered_paths:
            filtered_paths.append(canonical)

    # The guest's own System32 and Windows PowerShell are always present; only
    # host toolchain roots are supplied from the selected user's machine.
    guest_paths = [
        Path(r"C:\Windows\System32"),
        Path(r"C:\Windows\System32\WindowsPowerShell\v1.0"),
        *filtered_paths,
    ]
    return filtered_roots, guest_paths


def _validate_argv_and_environment(argv: list[str], extra_environment: Any) -> dict[str, str]:
    if not isinstance(argv, list) or not argv or len(argv) > 32:
        raise _failure("SANDBOX_COMMAND_INVALID", "Structured sandbox argv is outside its bounds.")
    if any(not isinstance(item, str) or not item or "\x00" in item or "\r" in item or "\n" in item for item in argv):
        raise _failure("SANDBOX_COMMAND_INVALID", "Structured sandbox argv contains an invalid argument.")
    if len("\0".join(argv).encode("utf-8")) > 8_192:
        raise _failure("SANDBOX_COMMAND_INVALID", "Structured sandbox argv exceeds its bounded size.")
    if Path(argv[0].replace("\\", "/")).name.lower() in _SHELL_NAMES:
        raise _failure("SANDBOX_SHELL_COMMAND_DENIED", "Choose a direct development tool; an interactive shell is not an allowed top-level command.")
    if extra_environment is None:
        extra_environment = {}
    if not isinstance(extra_environment, dict):
        raise _failure("SANDBOX_ENV_INVALID", "Structured sandbox environment must be an object.")
    environment: dict[str, str] = {}
    seen: set[str] = set()
    total_bytes = 0
    for raw_key, raw_value in extra_environment.items():
        name = str(raw_key)
        value = str(raw_value)
        folded = name.upper()
        value_bytes = len(value.encode("utf-8"))
        if (
            not _ENV_NAME.fullmatch(name)
            or folded in seen
            or any(character in value for character in ("\x00", "\r", "\n"))
            or value_bytes > 8_192
        ):
            raise _failure("SANDBOX_ENV_INVALID", "Structured sandbox environment contains an invalid key or value.")
        seen.add(folded)
        total_bytes += len(name.encode("utf-8")) + value_bytes
        if total_bytes > 32 * 1024:
            raise _failure("SANDBOX_ENV_INVALID", "Structured sandbox environment exceeds its aggregate size limit.")
        if is_filtered_env_var(name, value):
            raise _failure("SANDBOX_ENV_SECRET_DENIED", "Sensitive or loader environment variables cannot be forwarded into the sandbox.", env_key=name)
        if folded in _RESERVED_ENV_NAMES:
            raise _failure("SANDBOX_ENV_OVERRIDE_DENIED", "Reserved sandbox path and process variables cannot be overridden.", env_key=name)
        environment[name] = value
    return environment


def _validate_workspace(workspace_root: Path, workdir: Path) -> tuple[Path, Path]:
    try:
        original_metadata = workspace_root.lstat()
        original_reparse = bool(
            getattr(original_metadata, "st_file_attributes", 0)
            & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        )
        if stat.S_ISLNK(original_metadata.st_mode) or original_reparse:
            raise _failure("SANDBOX_WORKSPACE_INVALID", "The selected workspace cannot be a symbolic link or reparse point.")
        root = workspace_root.resolve(strict=True)
        cwd = workdir.resolve(strict=True)
    except ToolFailure:
        raise
    except OSError as error:
        raise _failure("SANDBOX_WORKSPACE_INVALID", "The selected workspace or working directory is unavailable.") from error
    if not root.is_dir() or not cwd.is_dir() or not _under(cwd, root):
        raise _failure("SANDBOX_WORKSPACE_SCOPE_DENIED", "The command working directory must remain under the selected workspace.")
    if not root.drive or root == Path(root.anchor):
        raise _failure("SANDBOX_WORKSPACE_SCOPE_DENIED", "A drive root cannot be granted as a workspace.")
    return root, cwd


def _phase_config(phase: str, sandbox_id: str | None = None, **fields: Any) -> dict[str, Any]:
    config: dict[str, Any] = {"version": MXC_WSB_SCHEMA_VERSION, "phase": phase}
    if phase == "provision":
        config["containment"] = "windows_sandbox"
    elif sandbox_id:
        config["sandboxId"] = sandbox_id
    config.update(fields)
    return config


def _build_launcher_command(request_path: Path) -> str:
    quoted_path = str(request_path).replace("'", "''")
    script = _POWERSHELL_LAUNCHER.replace("__REQUEST_PATH__", quoted_path)
    # cmd.exe rejects command lines over 8191 characters. Keep the readable
    # source template but remove indentation and blank lines before encoding.
    script = "\n".join(line.strip() for line in script.splitlines() if line.strip())
    encoded_script = base64.b64encode(script.encode("utf-16le")).decode("ascii")
    return (
        "powershell.exe -NoLogo -NoProfile -NonInteractive "
        "-ExecutionPolicy Bypass -EncodedCommand "
        + encoded_script
    )


@dataclass(frozen=True)
class _ActiveSandbox:
    sandbox_id: str
    workspace_root: Path
    readonly_roots: tuple[Path, ...]


@dataclass(frozen=True)
class MxcWindowsSandboxInvocation:
    """Per-command payload, temporary request file and manager lease."""

    argv: tuple[str, ...]
    environment: dict[str, str]
    scratch_directory: Path
    workspace_root: Path
    sandbox_id: str
    manager: "MxcWindowsSandboxManager"


class MxcWindowsSandboxManager:
    """Own at most one warm, exact-workspace Windows Sandbox VM per Runtime."""

    def __init__(self, *, executor_directory: Path | None = None) -> None:
        self.executor_directory = Path(executor_directory or _executor_directory())
        self.executor_path = self.executor_directory / "wxc-exec.exe"
        self._lock = threading.Lock()
        self._active: _ActiveSandbox | None = None
        self._uncertain = False
        self._closed = False

    def _environment(self) -> dict[str, str]:
        system_root = _system_root()
        system32 = system_root / "System32"
        system_drive = os.environ.get("SystemDrive") or system_root.drive
        host_temp = tempfile.gettempdir()
        return {
            "SystemDrive": str(system_drive),
            "SystemRoot": str(system_root),
            "WINDIR": str(system_root),
            "PATH": os.pathsep.join((str(self.executor_directory), str(system32))),
            "TEMP": os.environ.get("TEMP") or host_temp,
            "TMP": os.environ.get("TMP") or os.environ.get("TEMP") or host_temp,
        }

    def _run_envelope(self, config: dict[str, Any], *, timeout_seconds: int = 30) -> dict[str, Any]:
        verify_mxc_windows_sandbox_candidate()
        encoded = base64.b64encode(
            json.dumps(config, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
        ).decode("ascii")
        if len(encoded) > MAX_MXC_CONFIG_ARGUMENT_CHARS:
            raise _failure("SANDBOX_CONFIGURATION_TOO_LARGE", "The Windows Sandbox lifecycle configuration exceeds its bound.")
        try:
            # Use file-backed output, not anonymous pipes: MXC deliberately
            # launches a detached daemon that owns the VM beyond this phase.
            # On Windows, descendants can inherit pipe handles and make
            # communicate()/subprocess.run wait for EOF even after wxc-exec has
            # exited. File-backed capture preserves a bounded phase timeout.
            with tempfile.TemporaryFile(mode="w+b") as stdout_file, tempfile.TemporaryFile(mode="w+b") as stderr_file:
                result = subprocess.run(
                    [str(self.executor_path), "--experimental", "--config-base64", encoded],
                    cwd=str(_resource_root()),
                    env=self._environment(),
                    stdin=subprocess.DEVNULL,
                    stdout=stdout_file,
                    stderr=stderr_file,
                    timeout=timeout_seconds,
                    check=False,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                stdout_file.flush()
                stdout_file.seek(0)
                stdout_bytes = stdout_file.read(MAX_MXC_WSB_PHASE_OUTPUT_BYTES + 1)
        except subprocess.TimeoutExpired as error:
            raise _failure("SANDBOX_STATE_PHASE_TIMEOUT", "The Windows Sandbox lifecycle phase timed out.", retryable=True, phase=config.get("phase")) from error
        except (OSError, subprocess.SubprocessError) as error:
            raise _failure("SANDBOX_STATE_PHASE_FAILED", "The Windows Sandbox lifecycle phase could not be started.", phase=config.get("phase")) from error
        if len(stdout_bytes) > MAX_MXC_WSB_PHASE_OUTPUT_BYTES:
            raise _failure("SANDBOX_STATE_PHASE_OUTPUT_INVALID", "The Windows Sandbox lifecycle phase exceeded its output bound.", phase=config.get("phase"))
        stdout = stdout_bytes.decode("utf-8", errors="replace")
        try:
            payload = json.loads(stdout)
        except (TypeError, ValueError, json.JSONDecodeError) as error:
            raise _failure("SANDBOX_STATE_PHASE_OUTPUT_INVALID", "The Windows Sandbox lifecycle phase returned an invalid response.", phase=config.get("phase")) from error
        if result.returncode != 0:
            error = payload.get("error") if isinstance(payload, dict) else None
            code = error.get("code") if isinstance(error, dict) else None
            raise _failure(
                "SANDBOX_STATE_PHASE_FAILED",
                "The Windows Sandbox lifecycle phase was rejected or failed.",
                retryable=config.get("phase") == "start",
                phase=config.get("phase"),
                backend_error_code=code if isinstance(code, str) and re.fullmatch(r"[a-z_]{3,48}", code) else None,
            )
        if (
            not isinstance(payload, dict)
            or set(payload) != {"result"}
            or not isinstance(payload["result"], dict)
        ):
            raise _failure("SANDBOX_STATE_PHASE_OUTPUT_INVALID", "The Windows Sandbox lifecycle phase returned an invalid result envelope.", phase=config.get("phase"))
        return payload["result"]

    def _provision(self, root: Path, readonly_roots: list[Path]) -> str:
        result = self._run_envelope(
            _phase_config(
                "provision",
                filesystem={
                    "readwritePaths": [str(root)],
                    "readonlyPaths": [str(item) for item in readonly_roots],
                },
            ),
            timeout_seconds=30,
        )
        sandbox_id = result.get("sandboxId")
        if not isinstance(sandbox_id, str) or not _SANDBOX_ID.fullmatch(sandbox_id):
            raise _failure("SANDBOX_STATE_PHASE_OUTPUT_INVALID", "The Windows Sandbox provision phase returned an invalid sandbox identity.")
        if set(result) - {"sandboxId", "metadata"}:
            raise _failure("SANDBOX_STATE_PHASE_OUTPUT_INVALID", "The Windows Sandbox provision phase returned unexpected fields.")
        return sandbox_id

    def _deprovision_id(self, sandbox_id: str) -> None:
        self._run_envelope(
            _phase_config("deprovision", sandbox_id),
            timeout_seconds=MAX_MXC_WSB_PHASE_SECONDS,
        )

    def _ensure_active(self, root: Path, readonly_roots: list[Path]) -> str:
        identity = tuple(_windows_path_key(item) for item in readonly_roots)
        if self._uncertain:
            raise _failure("SANDBOX_STATE_UNCERTAIN", "A prior Windows Sandbox teardown could not be confirmed; automatic execution stays disabled.")
        if self._active is not None:
            active_identity = tuple(_windows_path_key(item) for item in self._active.readonly_roots)
            if _windows_path_key(self._active.workspace_root) == _windows_path_key(root) and active_identity == identity:
                return self._active.sandbox_id
            try:
                self._deprovision_id(self._active.sandbox_id)
            except ToolFailure as error:
                self._uncertain = True
                raise _failure("SANDBOX_TEARDOWN_UNCONFIRMED", "The prior Windows Sandbox could not be safely deprovisioned; no new workspace will be mounted.", retryable=True) from error
            self._active = None

        sandbox_id = self._provision(root, readonly_roots)
        try:
            self._run_envelope(_phase_config("start", sandbox_id), timeout_seconds=MAX_MXC_WSB_PHASE_SECONDS)
        except ToolFailure as error:
            try:
                self._deprovision_id(sandbox_id)
            except ToolFailure:
                self._uncertain = True
            raise error
        self._active = _ActiveSandbox(sandbox_id, root, tuple(readonly_roots))
        return sandbox_id

    def acquire(self, workspace_root: Path, readonly_roots: list[Path]) -> str:
        if self._closed:
            raise _failure("SANDBOX_MANAGER_CLOSED", "The Windows Sandbox manager is closed.")
        if not self._lock.acquire(timeout=30):
            raise _failure("SANDBOX_BUSY", "Another command is using the single Windows Sandbox VM.", retryable=True)
        try:
            if self._closed:
                raise _failure("SANDBOX_MANAGER_CLOSED", "The Windows Sandbox manager is closed.")
            verify_mxc_windows_sandbox_candidate()
            return self._ensure_active(workspace_root, readonly_roots)
        except Exception:
            self._lock.release()
            raise

    def release(self, *, abort: bool = False) -> bool:
        """Release one command lease; terminate the VM after cancellation/failure."""

        cleanup_ok = True
        try:
            if abort and self._active is not None:
                try:
                    self._deprovision_id(self._active.sandbox_id)
                    self._active = None
                except ToolFailure:
                    self._uncertain = True
                    cleanup_ok = False
        finally:
            try:
                self._lock.release()
            except RuntimeError:
                cleanup_ok = False
                self._uncertain = True
        return cleanup_ok

    def close(self) -> bool:
        """Deprovision the owned VM at Runtime shutdown; never force-reclaim."""

        if self._closed:
            return not self._uncertain
        acquired = self._lock.acquire(timeout=MAX_MXC_WSB_PHASE_SECONDS + 5)
        if not acquired:
            self._uncertain = True
            self._closed = True
            return False
        try:
            if self._active is not None:
                try:
                    self._deprovision_id(self._active.sandbox_id)
                    self._active = None
                except ToolFailure:
                    self._uncertain = True
            self._closed = True
            return not self._uncertain
        finally:
            self._lock.release()


def _safe_remove_scratch(workspace_root: Path, scratch_directory: Path) -> bool:
    try:
        root = workspace_root.resolve(strict=True)
        scratch = scratch_directory.absolute()
        if scratch.parent.resolve(strict=True) != root or not scratch.name.startswith(".mxc-wsb-"):
            return False
        metadata = scratch.lstat()
        is_reparse = bool(
            getattr(metadata, "st_file_attributes", 0)
            & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        )
        if stat.S_ISLNK(metadata.st_mode) or is_reparse or not stat.S_ISDIR(metadata.st_mode):
            return False
        shutil.rmtree(scratch)
        return not scratch.exists()
    except (OSError, RuntimeError, ValueError):
        return False


def build_mxc_windows_sandbox_invocation(
    argv: list[str],
    *,
    manager: MxcWindowsSandboxManager,
    workspace_root: Path,
    workdir: Path,
    timeout_ms: int,
    extra_environment: Any = None,
    tty: bool = False,
) -> MxcWindowsSandboxInvocation:
    """Build a shell-free command and lease the exact workspace's warm VM."""

    if os.name != "nt":
        raise _failure("SANDBOX_UNAVAILABLE", "Windows Sandbox execution is available only on Windows.")
    if tty:
        raise _failure("SANDBOX_TTY_UNAVAILABLE", "Interactive TTY sessions are not supported by the Windows Sandbox backend.")
    if not isinstance(timeout_ms, int) or isinstance(timeout_ms, bool) or not 1_000 <= timeout_ms <= 3_600_000:
        raise _failure("SANDBOX_COMMAND_INVALID", "Structured sandbox timeout is outside its bounds.")
    environment = _validate_argv_and_environment(argv, extra_environment)
    root, cwd = _validate_workspace(Path(workspace_root), Path(workdir))
    system_root = _system_root()
    roots, path_entries = _host_toolchains(system_root, root)
    scratch: Path | None = None
    lease_acquired = False
    try:
        sandbox_id = manager.acquire(root, roots)
        lease_acquired = True
        scratch = Path(tempfile.mkdtemp(prefix=".mxc-wsb-", dir=str(root))).resolve(strict=True)
        metadata = scratch.lstat()
        if stat.S_ISLNK(metadata.st_mode) or (
            getattr(metadata, "st_file_attributes", 0)
            & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        ):
            raise _failure("SANDBOX_WORKSPACE_INVALID", "The sandbox request scratch path is a reparse point.")
        resolved_argv, _ = _resolve_executable(
            list(argv),
            workspace_root=root,
            workdir=cwd,
            scratch_directory=scratch,
            roots=roots,
            path_entries=path_entries,
        )
        guest_mappings = _guest_share_map(root, roots)
        resolved_argv = [
            _guest_path_for_host(item, guest_mappings)
            if Path(item).is_absolute()
            else item
            for item in resolved_argv
        ]
        for directory in (scratch / "profile", scratch / "AppData" / "Roaming", scratch / "AppData" / "Local", scratch / "npm-cache"):
            directory.mkdir(parents=True, exist_ok=True)
        request_path = scratch / "exec-request.json"
        guest_scratch = _guest_path_for_host(scratch, guest_mappings)
        guest_request_path = _guest_path_for_host(request_path, guest_mappings)
        guest_path_entries = [
            _guest_path_for_host(item, guest_mappings)
            for item in path_entries
        ]
        request_payload = {
            "argv": resolved_argv,
            "cwd": _guest_path_for_host(cwd, guest_mappings),
            "temp": guest_scratch,
            "profile": _guest_path_for_host(scratch / "profile", guest_mappings),
            "appdata": _guest_path_for_host(scratch / "AppData" / "Roaming", guest_mappings),
            "localAppdata": _guest_path_for_host(scratch / "AppData" / "Local", guest_mappings),
            "npmCache": _guest_path_for_host(scratch / "npm-cache", guest_mappings),
            "pathEntries": guest_path_entries,
            "env": {
                key: _guest_environment_value(value, guest_mappings)
                for key, value in environment.items()
            },
        }
        request_bytes = json.dumps(
            request_payload,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        if len(request_bytes) > 128 * 1024:
            raise _failure("SANDBOX_COMMAND_INVALID", "Structured sandbox request exceeds its bounded size.")
        request_path.write_bytes(request_bytes)
        command_line = _build_launcher_command(guest_request_path)
        config = _phase_config(
            "exec",
            sandbox_id,
            process={
                "commandLine": command_line,
                "cwd": _guest_path_for_host(cwd, guest_mappings),
                "timeout": timeout_ms,
            },
        )
        encoded_config = base64.b64encode(
            json.dumps(config, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
        ).decode("ascii")
        if len(encoded_config) > MAX_MXC_CONFIG_ARGUMENT_CHARS:
            raise _failure("SANDBOX_CONFIGURATION_TOO_LARGE", "The Windows Sandbox exec configuration exceeds its bound.")
        return MxcWindowsSandboxInvocation(
            argv=(str(manager.executor_path), "--experimental", "--config-base64", encoded_config),
            environment=manager._environment(),
            scratch_directory=scratch,
            workspace_root=root,
            sandbox_id=sandbox_id,
            manager=manager,
        )
    except Exception:
        if scratch is not None:
            _safe_remove_scratch(root, scratch)
        if lease_acquired:
            manager.release(abort=True)
        raise


def cleanup_mxc_windows_sandbox_invocation(
    invocation: MxcWindowsSandboxInvocation,
    *,
    abort: bool = False,
) -> bool:
    """Remove only this command's scratch and release the manager's VM lease."""

    scratch_clean = _safe_remove_scratch(invocation.workspace_root, invocation.scratch_directory)
    cleanup_ok = invocation.manager.release(abort=(abort or not scratch_clean))
    return scratch_clean and cleanup_ok


def _run_child(invocation: MxcWindowsSandboxInvocation, *, timeout_seconds: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(invocation.argv),
        cwd=str(invocation.workspace_root),
        env=invocation.environment,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout_seconds,
        check=False,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


def probe_mxc_windows_sandbox_child_process(workspace_root: str) -> dict[str, Any]:
    """Verify mapping, canonical paths, nested Node/npm, and cleanup on one VM."""

    result: dict[str, Any] = {
        "probe": "mxc_wsb_child_process_v1",
        "available": False,
        "reason": None,
    }
    if os.name != "nt":
        result["reason"] = "WINDOWS_ONLY"
        return result
    manager = MxcWindowsSandboxManager()
    root: Path | None = None
    probe_workspace: Path | None = None
    invocations: list[MxcWindowsSandboxInvocation] = []
    scratch_clean = True
    lease_held = False
    try:
        if not isinstance(workspace_root, str) or not workspace_root.strip():
            result["reason"] = "WORKSPACE_INVALID"
            return result
        raw_root = Path(workspace_root)
        root, _ = _validate_workspace(raw_root, raw_root)
        probe_workspace = Path(tempfile.mkdtemp(prefix=".mxc-wsb-probe-", dir=str(root))).resolve(strict=True)
        js_probe = (
            "const fs=require('fs'),cp=require('child_process'),path=require('path'),os=require('os');"
            f"const workspace={json.dumps(GUEST_WORKSPACE_SHARE, ensure_ascii=True)};"
            "let workspaceRealpath=null,cwdRealpath=null,tempCreated=false,childStatus=null,childMarker=false,reason=null;"
            "try{workspaceRealpath=fs.realpathSync.native(workspace);cwdRealpath=fs.realpathSync.native(process.cwd());"
            "const temp=fs.mkdtempSync(path.join(os.tmpdir(),'mxc-wsb-temp-'));fs.rmdirSync(temp);tempCreated=true;"
            "const child=cp.spawnSync(process.execPath,['-e',\"process.stdout.write('MXC_WSB_CHILD_OK')\"],{cwd:process.cwd(),env:process.env,encoding:'utf8'});"
            "childStatus=Number.isInteger(child.status)?child.status:null;childMarker=String(child.stdout||'').includes('MXC_WSB_CHILD_OK');"
            "}catch(e){reason=typeof e.code==='string'?e.code:'PROBE_FAILED'};"
            "process.stdout.write(JSON.stringify({workspace_realpath:workspaceRealpath,cwd_realpath:cwdRealpath,temp_created:tempCreated,child_status:childStatus,child_marker:childMarker,reason}));"
        )
        first = build_mxc_windows_sandbox_invocation(
            ["node", "-e", js_probe],
            manager=manager,
            workspace_root=root,
            workdir=probe_workspace,
            timeout_ms=30_000,
        )
        invocations.append(first)
        lease_held = True
        child_result = _run_child(first, timeout_seconds=MAX_MXC_WSB_PROBE_SECONDS)
        if len(child_result.stdout.encode("utf-8", errors="replace")) > MAX_MXC_WSB_PROBE_OUTPUT_BYTES:
            result["reason"] = "CHILD_PROCESS_PROBE_OUTPUT_TOO_LARGE"
            return result
        payload = None
        for line in reversed(child_result.stdout.splitlines()):
            try:
                candidate = json.loads(line)
            except (TypeError, ValueError, json.JSONDecodeError):
                continue
            if isinstance(candidate, dict) and set(candidate) == {
                "workspace_realpath", "cwd_realpath", "temp_created", "child_status", "child_marker", "reason"
            }:
                payload = candidate
                break
        if payload is None:
            output_state = "EMPTY" if not child_result.stdout.strip() else "UNPARSEABLE"
            exit_code = child_result.returncode
            exit_suffix = f"NEGATIVE_{abs(exit_code)}" if exit_code < 0 else str(exit_code)
            result["reason"] = f"CHILD_PROCESS_PROBE_OUTPUT_{output_state}_EXIT_{exit_suffix}"
            return result
        if child_result.returncode != 0:
            exit_code = child_result.returncode
            exit_suffix = f"NEGATIVE_{abs(exit_code)}" if exit_code < 0 else str(exit_code)
            result["reason"] = f"CHILD_PROCESS_PROBE_EXIT_{exit_suffix}"
            return result
        expected_guest_workspace = Path(GUEST_WORKSPACE_SHARE)
        expected_guest_cwd = Path(_guest_path_for_host(
            probe_workspace,
            [(root, GUEST_WORKSPACE_SHARE)],
        ))
        if payload["workspace_realpath"] is None or (
            _windows_path_key(Path(payload["workspace_realpath"]))
            != _windows_path_key(expected_guest_workspace)
        ):
            result["reason"] = "WINDOWS_WORKSPACE_REALPATH_UNAVAILABLE"
            return result
        if payload["cwd_realpath"] is None or (
            _windows_path_key(Path(payload["cwd_realpath"]))
            != _windows_path_key(expected_guest_cwd)
        ):
            result["reason"] = "WINDOWS_CWD_REALPATH_UNAVAILABLE"
            return result
        if payload["reason"] is not None:
            reason = payload["reason"]
            result["reason"] = (
                "WINDOWS_TEMP_UNAVAILABLE"
                if reason in {"EPERM", "EACCES"}
                else "WINDOWS_CHILD_PROCESS_UNAVAILABLE"
            )
            return result
        if payload["temp_created"] is not True:
            result["reason"] = "WINDOWS_TEMP_UNAVAILABLE"
            return result
        if payload["child_status"] != 0 or payload["child_marker"] is not True:
            result["reason"] = "WINDOWS_CHILD_PROCESS_UNAVAILABLE"
            return result

        # Each build invocation acquires the manager's single-flight lease.
        # Release the first command's lease before asking the same manager to
        # build the npm invocation; the warm VM itself remains active.
        if not manager.release():
            lease_held = False
            result["reason"] = "SANDBOX_PROBE_LEASE_RELEASE_FAILED"
            return result
        lease_held = False

        package = {
            "name": "codex-mxc-wsb-child-probe",
            "version": "1.0.0",
            "scripts": {
                "test": (
                    "node -e \"const fs=require('fs');"
                    "const p=JSON.parse(fs.readFileSync('package.json','utf8'));"
                    "if(p.name!=='codex-mxc-wsb-child-probe'||!process.cwd().toLowerCase().includes('.mxc-wsb-probe-'))process.exit(42);"
                    "console.log('MXC_WSB_NPM_OK')\""
                )
            },
        }
        (probe_workspace / "package.json").write_text(json.dumps(package), encoding="utf-8")
        npm_prefix = build_mxc_windows_sandbox_invocation(
            ["npm", "prefix"],
            manager=manager,
            workspace_root=root,
            workdir=probe_workspace,
            timeout_ms=15_000,
        )
        invocations.append(npm_prefix)
        lease_held = True
        npm_prefix_result = _run_child(npm_prefix, timeout_seconds=MAX_MXC_WSB_PROBE_SECONDS)
        if len(npm_prefix_result.stdout.encode("utf-8", errors="replace")) > MAX_MXC_WSB_PROBE_OUTPUT_BYTES:
            result["reason"] = "CHILD_PROCESS_PROBE_OUTPUT_TOO_LARGE"
            return result
        if npm_prefix_result.returncode != 0:
            exit_code = npm_prefix_result.returncode
            exit_suffix = f"NEGATIVE_{abs(exit_code)}" if exit_code < 0 else str(exit_code)
            result["reason"] = f"WINDOWS_NPM_PREFIX_EXIT_{exit_suffix}"
            return result
        prefix_lines = [line.strip() for line in npm_prefix_result.stdout.splitlines() if line.strip()]
        if not prefix_lines:
            result["reason"] = "WINDOWS_NPM_PREFIX_OUTPUT_INVALID"
            return result
        if _windows_path_key(Path(prefix_lines[-1])) != _windows_path_key(expected_guest_cwd):
            result["reason"] = "WINDOWS_NPM_WORKDIR_MISMATCH"
            return result

        if not manager.release():
            lease_held = False
            result["reason"] = "SANDBOX_PROBE_LEASE_RELEASE_FAILED"
            return result
        lease_held = False

        npm_test = build_mxc_windows_sandbox_invocation(
            ["npm", "test"],
            manager=manager,
            workspace_root=root,
            workdir=probe_workspace,
            timeout_ms=30_000,
        )
        invocations.append(npm_test)
        lease_held = True
        npm_result = _run_child(npm_test, timeout_seconds=MAX_MXC_WSB_PROBE_SECONDS)
        if len(npm_result.stdout.encode("utf-8", errors="replace")) > MAX_MXC_WSB_PROBE_OUTPUT_BYTES:
            result["reason"] = "CHILD_PROCESS_PROBE_OUTPUT_TOO_LARGE"
            return result
        if npm_result.returncode != 0:
            exit_code = npm_result.returncode
            exit_suffix = f"NEGATIVE_{abs(exit_code)}" if exit_code < 0 else str(exit_code)
            result["reason"] = f"WINDOWS_NPM_SCRIPT_EXIT_{exit_suffix}"
            return result
        if "MXC_WSB_NPM_OK" not in npm_result.stdout:
            result["reason"] = "WINDOWS_NPM_SCRIPT_PROCESS_UNAVAILABLE"
            return result
        result["available"] = True
        return result
    except ToolFailure as error:
        code = str(getattr(error, "code", "SANDBOX_UNAVAILABLE"))
        result["reason"] = code if re.fullmatch(r"[A-Z0-9_]{2,96}", code) else "SANDBOX_UNAVAILABLE"
        details = getattr(error, "details", {})
        phase = details.get("phase") if isinstance(details, dict) else None
        backend_error_code = details.get("backend_error_code") if isinstance(details, dict) else None
        if phase in {"provision", "start", "exec", "deprovision"}:
            result["reason"] += f"_{phase.upper()}"
        if isinstance(backend_error_code, str) and re.fullmatch(r"[a-z_]{3,48}", backend_error_code):
            result["reason"] += f"_{backend_error_code.upper()}"
        result["reason"] = result["reason"][:96]
        return result
    except subprocess.TimeoutExpired:
        result["reason"] = "CHILD_PROCESS_PROBE_TIMEOUT"
        return result
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError):
        result["reason"] = "CHILD_PROCESS_PROBE_FAILED"
        return result
    finally:
        for invocation in invocations:
            try:
                scratch_clean = _safe_remove_scratch(invocation.workspace_root, invocation.scratch_directory) and scratch_clean
            except Exception:  # noqa: BLE001 - the result remains fail-closed
                scratch_clean = False
        if lease_held:
            try:
                scratch_clean = manager.release(abort=not scratch_clean) and scratch_clean
            except Exception:  # noqa: BLE001 - the result remains fail-closed
                scratch_clean = False
        if probe_workspace is not None:
            try:
                metadata = probe_workspace.lstat()
                is_reparse = bool(
                    getattr(metadata, "st_file_attributes", 0)
                    & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
                )
                if (
                    root is not None
                    and probe_workspace.parent.resolve(strict=True) == root
                    and probe_workspace.name.startswith(".mxc-wsb-probe-")
                    and not stat.S_ISLNK(metadata.st_mode)
                    and not is_reparse
                    and stat.S_ISDIR(metadata.st_mode)
                ):
                    shutil.rmtree(probe_workspace)
                if probe_workspace.exists():
                    scratch_clean = False
            except (OSError, RuntimeError, ValueError):
                scratch_clean = False
        if not manager.close():
            scratch_clean = False
        if not scratch_clean:
            result["available"] = False
            result["reason"] = "CHILD_PROCESS_PROBE_CLEANUP_UNCERTAIN"
