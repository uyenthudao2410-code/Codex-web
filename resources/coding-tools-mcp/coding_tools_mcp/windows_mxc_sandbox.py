"""Pinned Microsoft MXC adapter for Windows Control Plane structured argv.

This adapter deliberately supports only MXC's Windows ProcessContainer path,
with a fresh container identity per command, one writable registered root,
an ephemeral same-root CWD alias for child processes on secondary drives,
network and host-loopback denied, DACL fallback disabled, and a separately
verified toolchain read set. It never falls back to host-user process launch.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import shutil
import stat
import struct
import subprocess
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .errors import ToolFailure
from .fs_utils import is_relative_to
from .runtime_config import is_filtered_env_var


MXC_RELEASE = "v0.8.0"
MXC_EXEC_SHA256 = "6049c64723af1173c3739dc6cd6b2f33f6c021bb2832c4216233cba7f71aee9a"
MAX_MXC_CONFIG_ARGUMENT_CHARS = 24_000
MAX_MXC_PROBE_SECONDS = 8
MAX_MXC_CHILD_PROBE_SECONDS = 18
_ENV_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,127}$")
_RESERVED_ENV_NAMES = frozenset({
    "APPDATA", "COMSPEC", "HOME", "HOMEDRIVE", "HOMEPATH",
    "LOCALAPPDATA", "NPM_CONFIG_CACHE", "PATH", "PATHEXT",
    "SYSTEMROOT", "TEMP", "TMP", "TMPDIR", "USERPROFILE", "WINDIR",
})
_SHELL_NAMES = frozenset({
    "bash", "bash.exe", "cmd", "cmd.exe", "powershell", "powershell.exe",
    "pwsh", "pwsh.exe", "sh", "sh.exe", "wscript.exe", "cscript.exe",
    "zsh", "zsh.exe",
})
_WINDOWS_EXEC_BOOTSTRAP = r"""
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const cp = require('node:child_process');
function fail(code) {
  process.stderr.write(code + '\n');
  process.exit(126);
}
let payload;
try {
  payload = JSON.parse(Buffer.from(process.argv[1] || '', 'base64').toString('utf8'));
} catch (_) {
  fail('SANDBOX_COMMAND_INVALID');
}
if (!payload || typeof payload !== 'object' || Array.isArray(payload)
  || !Array.isArray(payload.argv) || payload.argv.length < 1
  || payload.argv.some((item) => typeof item !== 'string' || !item || item.includes('\0'))
  || typeof payload.workspace_root !== 'string' || !path.isAbsolute(payload.workspace_root)) {
  fail('SANDBOX_COMMAND_INVALID');
}
const workspace = path.resolve(payload.workspace_root);
const temp = path.resolve(os.tmpdir());
const relative = path.relative(workspace, temp);
if (relative === '..' || relative.startsWith('..' + path.sep) || path.isAbsolute(relative)) {
  fail('SANDBOX_TEMP_OUTSIDE_WORKSPACE');
}
try {
  fs.mkdirSync(temp, { recursive: true });
  if (!fs.statSync(temp).isDirectory()) fail('SANDBOX_TEMP_UNAVAILABLE');
} catch (_) {
  fail('SANDBOX_TEMP_UNAVAILABLE');
}
let child;
try {
  child = cp.spawn(payload.argv[0], payload.argv.slice(1), {
    cwd: process.cwd(),
    env: process.env,
    shell: false,
    stdio: 'inherit'
  });
} catch (_) {
  fail('SANDBOX_CHILD_SPAWN_FAILED');
}
child.once('error', () => fail('SANDBOX_CHILD_SPAWN_FAILED'));
child.once('close', (code) => process.exit(Number.isInteger(code) ? code : 126));
"""


@dataclass(frozen=True)
class MxcInvocation:
    """Host-side invocation and exact per-command workspace/alias scratch."""

    argv: tuple[str, ...]
    environment: dict[str, str]
    scratch_directory: Path
    workspace_root: Path
    executor_path: Path
    cwd_alias_root: Path | None
    cwd_alias_path: Path | None


def _failure(code: str, message: str, **details: Any) -> ToolFailure:
    return ToolFailure(code, message, category="security", details=details or None)


def _system_root() -> Path:
    raw = str(os.environ.get("SystemRoot") or os.environ.get("WINDIR") or r"C:\Windows")
    candidate = Path(raw)
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as error:
        raise _failure("SANDBOX_UNAVAILABLE", "Windows system toolchain root is unavailable.") from error
    if not resolved.is_dir():
        raise _failure("SANDBOX_UNAVAILABLE", "Windows system toolchain root is not a directory.")
    return resolved


def _executor_path() -> Path:
    path = Path(__file__).resolve().parents[2] / "tools" / "wxc-exec.exe"
    try:
        metadata = path.stat()
    except OSError as error:
        raise _failure("SANDBOX_UNAVAILABLE", "The pinned Windows sandbox executor is missing.") from error
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_size <= 0:
        raise _failure("SANDBOX_UNAVAILABLE", "The pinned Windows sandbox executor is not a regular file.")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != MXC_EXEC_SHA256:
        raise _failure("SANDBOX_BINARY_INTEGRITY_FAILED", "The bundled Windows sandbox executor failed its pinned SHA-256 check.")
    return path


def _minimal_host_environment(executor_path: Path, system_root: Path) -> dict[str, str]:
    system32 = system_root / "System32"
    return {
        "SystemRoot": str(system_root),
        "WINDIR": str(system_root),
        "PATH": os.pathsep.join((str(executor_path.parent), str(system32))),
        "TEMP": os.environ.get("TEMP", str(system32)),
        "TMP": os.environ.get("TMP", os.environ.get("TEMP", str(system32))),
    }


def _probe_executor(executor_path: Path, system_root: Path) -> None:
    try:
        result = subprocess.run(
            [str(executor_path), "--experimental", "--probe"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=MAX_MXC_PROBE_SECONDS,
            check=False,
            env=_minimal_host_environment(executor_path, system_root),
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise _failure("SANDBOX_UNAVAILABLE", "The Windows sandbox capability probe failed.") from error
    if result.returncode != 0:
        raise _failure("SANDBOX_UNAVAILABLE", "The Windows sandbox capability probe returned an error.")
    try:
        payload = json.loads(result.stdout)
    except (TypeError, ValueError, json.JSONDecodeError) as error:
        raise _failure("SANDBOX_UNAVAILABLE", "The Windows sandbox capability probe returned invalid data.") from error
    if (
        not isinstance(payload, dict)
        or payload.get("tier") != "base-container"
        or payload.get("needsDaclAugmentation") is not False
        or payload.get("probes", {}).get("baseContainerApiPresent") is not True
        or payload.get("probes", {}).get("baseContainerSupportsDenyPaths") is not True
        or payload.get("warnings") not in ([], None)
    ):
        raise _failure(
            "SANDBOX_UNAVAILABLE",
            "Windows lacks the pinned no-DACL filesystem sandbox tier required for Control Plane exec.",
            tier=payload.get("tier") if isinstance(payload, dict) else None,
            needs_dacl_augmentation=payload.get("needsDaclAugmentation") if isinstance(payload, dict) else None,
            deny_paths_supported=(
                payload.get("probes", {}).get("baseContainerSupportsDenyPaths")
                if isinstance(payload, dict) and isinstance(payload.get("probes"), dict) else None
            ),
        )


def _under(path: Path, root: Path) -> bool:
    try:
        return is_relative_to(path, root)
    except (OSError, RuntimeError, ValueError):
        return False


def _known_toolchains(system_root: Path, executor_path: Path) -> tuple[list[Path], list[Path]]:
    """Return narrow read roots and PATH entries for standard developer tools."""

    roots: list[Path] = []
    path_entries: list[Path] = []

    def add_root(value: Path) -> None:
        try:
            candidate = value.resolve(strict=True)
        except OSError:
            return
        if not candidate.is_dir() or candidate in roots:
            return
        # Reject a path that unexpectedly resolves to a volume root. A root
        # grant would be much broader than the toolchain directory requested.
        if candidate == Path(candidate.anchor):
            return
        roots.append(candidate)

    def add_path(value: Path) -> None:
        try:
            candidate = value.resolve(strict=True)
        except OSError:
            return
        if candidate.is_dir() and candidate not in path_entries:
            path_entries.append(candidate)

    system32 = system_root / "System32"
    add_root(system32)
    # AppContainer already has its OS-approved read-only system image. Do not
    # grant Windows folders above System32; put System32 on PATH for child tools.
    add_path(system32)
    add_path(system32 / "WindowsPowerShell" / "v1.0")

    program_bases = [
        Path(str(os.environ.get("ProgramFiles") or r"C:\Program Files")),
        Path(str(os.environ.get("ProgramFiles(x86)") or r"C:\Program Files (x86)")),
    ]
    resources_root = executor_path.parent.parent
    for bundled in (resources_root / "tools", resources_root / "native-python"):
        add_root(bundled)
        add_path(bundled)

    for base in program_bases:
        add_root(base / "nodejs")
        add_path(base / "nodejs")
        # The official Node for Windows distribution reads this OpenSSL
        # configuration outside its installation directory at startup.
        add_root(base / "Common Files" / "SSL")
        add_path(base / "Common Files" / "SSL")
        git_root = base / "Git"
        add_root(git_root)
        for relative in ("cmd", "bin", "mingw64/bin", "usr/bin"):
            add_path(git_root / relative)
        add_path(git_root)
        for candidate in base.glob("Python*"):
            if candidate.is_dir() and re.fullmatch(r"Python\d{2,3}", candidate.name, re.IGNORECASE):
                add_root(candidate)
                add_path(candidate)
        add_root(base / "PowerShell" / "7")
        add_path(base / "PowerShell" / "7")

    # Per-user developer tools are supported only under their conventional,
    # versioned installation directories; arbitrary PATH entries never become
    # filesystem grants.
    local_programs = Path(str(os.environ.get("LOCALAPPDATA") or "")) / "Programs"
    for relative in ("nodejs", "Git"):
        root = local_programs / relative
        add_root(root)
        add_path(root)
    python_parent = local_programs / "Python"
    try:
        python_candidates = list(python_parent.glob("Python*"))
    except OSError:
        python_candidates = []
    for candidate in python_candidates:
        if candidate.is_dir() and re.fullmatch(r"Python\d{2,3}", candidate.name, re.IGNORECASE):
            add_root(candidate)
            add_path(candidate)

    return roots, path_entries


def _windows_path_key(path: Path) -> str:
    return os.path.normcase(os.path.normpath(str(path))).casefold()


def _create_directory_junction(link_path: Path, target_path: Path) -> None:
    """Create one private junction with the native Windows reparse-point API."""

    if os.name != "nt":
        raise _failure("SANDBOX_WORKSPACE_ALIAS_UNAVAILABLE", "Windows workspace aliases are available only on Windows.")
    import ctypes

    target = target_path.resolve(strict=True)
    if not target.is_dir() or not target.drive or not re.match(r"^[A-Za-z]:\\", str(target)):
        raise _failure("SANDBOX_WORKSPACE_ALIAS_UNAVAILABLE", "The selected working directory is not a local drive path.")
    link = link_path.absolute()
    try:
        link.mkdir()
    except OSError as error:
        raise _failure("SANDBOX_WORKSPACE_ALIAS_UNAVAILABLE", "Could not create the temporary child-process working-directory alias.") from error

    substitute = (chr(92) + "??" + chr(92) + str(target)).encode("utf-16-le")
    printable = str(target).encode("utf-16-le")
    path_buffer = substitute + b"\x00\x00" + printable + b"\x00\x00"
    reparse_data_length = 8 + len(path_buffer)
    header = struct.pack(
        "<LHHHHHH",
        0xA0000003,  # IO_REPARSE_TAG_MOUNT_POINT
        reparse_data_length,
        0,
        0,
        len(substitute),
        len(substitute) + 2,
        len(printable),
    )
    reparse_buffer = ctypes.create_string_buffer(header + path_buffer)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create_file = kernel32.CreateFileW
    create_file.argtypes = (
        ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p,
        ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p,
    )
    create_file.restype = ctypes.c_void_p
    device_io_control = kernel32.DeviceIoControl
    device_io_control.argtypes = (
        ctypes.c_void_p, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_uint32,
        ctypes.c_void_p, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32), ctypes.c_void_p,
    )
    device_io_control.restype = ctypes.c_int
    close_handle = kernel32.CloseHandle
    close_handle.argtypes = (ctypes.c_void_p,)
    close_handle.restype = ctypes.c_int
    handle = create_file(
        str(link),
        0x40000000,  # GENERIC_WRITE
        0x00000001 | 0x00000002 | 0x00000004,  # SHARE_READ | SHARE_WRITE | SHARE_DELETE
        None,
        3,  # OPEN_EXISTING
        0x00200000 | 0x02000000,  # OPEN_REPARSE_POINT | BACKUP_SEMANTICS
        None,
    )
    if not handle or handle == ctypes.c_void_p(-1).value:
        error = ctypes.get_last_error()
        try: link.rmdir()
        except OSError: pass
        raise _failure("SANDBOX_WORKSPACE_ALIAS_UNAVAILABLE", "Could not open the temporary alias for the junction policy.", win_error=error)
    try:
        returned = ctypes.c_uint32()
        ok = device_io_control(
            handle,
            0x000900A4,  # FSCTL_SET_REPARSE_POINT
            reparse_buffer,
            len(header + path_buffer),
            None,
            0,
            ctypes.byref(returned),
            None,
        )
        if not ok:
            error = ctypes.get_last_error()
            try: link.rmdir()
            except OSError: pass
            raise _failure("SANDBOX_WORKSPACE_ALIAS_UNAVAILABLE", "Could not bind the temporary alias to the selected working directory.", win_error=error)
    finally:
        close_handle(handle)


def _remove_path_no_follow(path: Path, parent_root: Path) -> bool:
    """Remove a path beneath an exact temporary root without following reparses."""

    try:
        parent = parent_root.resolve(strict=True)
        candidate = path.absolute()
        if candidate.parent.resolve(strict=True) != parent:
            return False
        metadata = candidate.lstat()
        attributes = getattr(metadata, "st_file_attributes", 0)
        is_reparse = bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))
        is_directory = stat.S_ISDIR(metadata.st_mode) or bool(attributes & getattr(stat, "FILE_ATTRIBUTE_DIRECTORY", 0x10))
        if stat.S_ISLNK(metadata.st_mode) or is_reparse:
            if is_directory:
                os.rmdir(candidate)
            else:
                candidate.unlink()
            return not candidate.exists()
        if is_directory:
            for entry in os.scandir(candidate):
                if not _remove_path_no_follow(Path(entry.path), candidate):
                    return False
            candidate.rmdir()
        else:
            candidate.unlink()
        return not candidate.exists()
    except (OSError, RuntimeError, ValueError):
        return False


def cleanup_mxc_cwd_alias(alias_root: Path | None, alias_path: Path | None) -> bool:
    """Remove only the exact per-command CWD alias and its private temp root."""

    if alias_root is None and alias_path is None:
        return True
    if alias_root is None or alias_path is None:
        return False
    try:
        root = alias_root.absolute()
        system_drive = Path(_system_root().anchor).resolve(strict=True)
        metadata = root.lstat()
        attributes = getattr(metadata, "st_file_attributes", 0)
        is_reparse = bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))
        if (
            root.parent.resolve(strict=True) != system_drive
            or not root.name.startswith("codex-mxc-cwd-")
            or not stat.S_ISDIR(metadata.st_mode)
            or stat.S_ISLNK(metadata.st_mode)
            or is_reparse
            or alias_path.absolute().parent != root
            or alias_path.name != "workspace"
        ):
            return False
        return _remove_path_no_follow(root, system_drive)
    except (OSError, RuntimeError, ValueError):
        return False


def cleanup_mxc_invocation(invocation: MxcInvocation) -> bool:
    """Remove per-command sandbox work areas after the process tree is terminal."""

    scratch = cleanup_mxc_scratch(invocation.workspace_root, invocation.scratch_directory)
    alias = cleanup_mxc_cwd_alias(invocation.cwd_alias_root, invocation.cwd_alias_path)
    return scratch and alias


def _build_path_fence(
    workspace_root: Path,
    toolchain_roots: list[Path],
    *,
    extra_write_roots: list[Path] | None = None,
    extra_readonly_roots: list[Path] | None = None,
) -> tuple[list[Path], list[Path]]:
    """Allow traversal to exact granted trees while denying their siblings."""

    extra_write_roots = extra_write_roots or []
    extra_readonly_roots = extra_readonly_roots or []
    write_roots = (workspace_root, *extra_write_roots)
    target_roots = (*write_roots, *extra_readonly_roots, *toolchain_roots)
    write_root_keys = {_windows_path_key(item) for item in write_roots}
    terminal_roots = {_windows_path_key(item) for item in target_roots}
    nodes: dict[str, Path] = {}
    children: dict[str, dict[str, Path]] = {}
    for target in target_roots:
        chain = list(reversed(target.parents)) + [target]
        for node in chain:
            nodes[_windows_path_key(node)] = node
        for parent, child in zip(chain, chain[1:]):
            children.setdefault(_windows_path_key(parent), {})[_windows_path_key(child)] = child

    readonly_paths = [
        node for key, node in nodes.items()
        if key not in write_root_keys
    ]
    denied_paths: dict[str, Path] = {}
    protected_attributes = (
        getattr(stat, "FILE_ATTRIBUTE_HIDDEN", 0x2)
        | getattr(stat, "FILE_ATTRIBUTE_SYSTEM", 0x4)
        | getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    )
    for key, parent in nodes.items():
        if key in terminal_roots:
            continue
        allowed_children = children.get(key, {})
        try:
            entries = list(os.scandir(parent))
        except OSError as error:
            raise _failure(
                "SANDBOX_PATH_FENCE_FAILED",
                "The host could not enumerate an ancestor directory while fencing the selected workspace.",
                win_error=getattr(error, "winerror", None),
            ) from error
        for entry in entries:
            entry_path = Path(entry.path)
            try:
                attributes = getattr(entry.stat(follow_symlinks=False), "st_file_attributes", 0)
            except OSError as error:
                raise _failure(
                    "SANDBOX_PATH_FENCE_FAILED",
                    "The host could not inspect an ancestor entry while fencing the selected workspace.",
                    win_error=getattr(error, "winerror", None),
                ) from error
            # Windows system, hidden, and reparse entries remain denied by the
            # AppContainer's own ACL unless an explicitly granted path reaches
            # them. Do not ask MXC to install redundant host-root denies.
            if attributes & protected_attributes:
                continue
            if _windows_path_key(entry_path) in allowed_children:
                continue
            denied_paths[_windows_path_key(entry_path)] = entry_path
    return readonly_paths, list(denied_paths.values())


def _resolve_executable(
    argv: list[str],
    *,
    workspace_root: Path,
    workdir: Path,
    scratch_directory: Path,
    roots: list[Path],
    path_entries: list[Path],
) -> tuple[list[str], list[Path]]:
    if not argv or not isinstance(argv[0], str):
        raise _failure("SANDBOX_COMMAND_INVALID", "The sandbox command executable is invalid.")
    raw = argv[0]
    base_name = Path(raw.replace("\\", "/")).name.lower()
    if base_name in _SHELL_NAMES:
        raise _failure("SANDBOX_SHELL_COMMAND_DENIED", "Choose a direct development tool; an interactive shell is not an allowed top-level command.")

    is_bare_command = not os.path.isabs(raw) and "/" not in raw and "\\" not in raw
    if is_bare_command and base_name in {"npm", "npm.cmd", "npx", "npx.cmd"}:
        node = next((root / "node.exe" for root in roots if (root / "node.exe").is_file()), None)
        if node is None:
            raise _failure("SANDBOX_TOOLCHAIN_UNAVAILABLE", "The bundled Windows sandbox cannot find an approved Node.js installation.")
        cli_name = "npm-cli.js" if base_name.startswith("npm") else "npx-cli.js"
        source_npm = node.parent / "node_modules" / "npm"
        source_cli = source_npm / "bin" / cli_name
        if not source_cli.is_file():
            raise _failure("SANDBOX_TOOLCHAIN_UNAVAILABLE", "The approved Node.js installation is missing its npm CLI entrypoint.")
        npm_arguments = list(argv[1:])
        separator = npm_arguments.index("--") if "--" in npm_arguments else len(npm_arguments)
        option_arguments = npm_arguments[:separator]
        script_arguments = npm_arguments[separator:]
        explicit_prefixes: list[str] = []
        filtered_options: list[str] = []
        index = 0
        while index < len(option_arguments):
            argument = option_arguments[index]
            if argument == "--prefix":
                if index + 1 >= len(option_arguments) or not option_arguments[index + 1].strip():
                    raise _failure("SANDBOX_COMMAND_INVALID", "npm/npx --prefix requires a workspace working directory.")
                explicit_prefixes.append(option_arguments[index + 1])
                index += 2
                continue
            if argument.startswith("--prefix="):
                value = argument.split("=", 1)[1]
                if not value.strip():
                    raise _failure("SANDBOX_COMMAND_INVALID", "npm/npx --prefix requires a workspace working directory.")
                explicit_prefixes.append(value)
                index += 1
                continue
            filtered_options.append(argument)
            index += 1
        for value in explicit_prefixes:
            prefix_path = Path(value)
            if not prefix_path.is_absolute():
                prefix_path = workdir / prefix_path
            if _windows_path_key(prefix_path.resolve(strict=False)) != _windows_path_key(workdir):
                raise _failure(
                    "SANDBOX_NPM_PREFIX_SCOPE_DENIED",
                    "npm/npx prefix must match the selected working directory; choose the directory with workdir instead.",
                )
        npm_arguments = ["--prefix", str(workdir), *filtered_options, *script_arguments]
        try:
            npm_tree_bytes = 0
            for directory, child_dirs, filenames in os.walk(source_npm, followlinks=False):
                current = Path(directory)
                for name in child_dirs + filenames:
                    entry = current / name
                    metadata = entry.lstat()
                    if stat.S_ISLNK(metadata.st_mode) or (
                        getattr(metadata, "st_file_attributes", 0)
                        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
                    ):
                        raise _failure("SANDBOX_TOOLCHAIN_INVALID", "The installed npm tree contains a reparse point.")
                    if not entry.is_dir():
                        if not entry.is_file():
                            raise _failure("SANDBOX_TOOLCHAIN_INVALID", "The installed npm tree contains a non-regular file.")
                        npm_tree_bytes += metadata.st_size
                        if npm_tree_bytes > 128 * 1024 * 1024:
                            raise _failure("SANDBOX_TOOLCHAIN_INVALID", "The installed npm tree exceeds its bounded copy size.")
            copied_npm = scratch_directory / "npm"
            shutil.copytree(source_npm, copied_npm, symlinks=False)
        except ToolFailure:
            raise
        except OSError as error:
            raise _failure("SANDBOX_TOOLCHAIN_UNAVAILABLE", "The approved npm CLI could not be staged inside the selected workspace.") from error
        cli = copied_npm / "bin" / cli_name
        return [
            str(node.resolve(strict=True)),
            "--preserve-symlinks",
            "--preserve-symlinks-main",
            str(cli.resolve(strict=True)),
            *npm_arguments,
        ], roots

    candidate: Path | None = None
    if os.path.isabs(raw):
        candidate = Path(raw)
    elif any(separator in raw for separator in ("/", "\\")):
        candidate = workdir / raw
    else:
        safe_search_path = os.pathsep.join(str(item) for item in path_entries)
        resolved = shutil.which(raw, path=safe_search_path)
        if resolved:
            candidate = Path(resolved)
    if candidate is None:
        raise _failure("SANDBOX_TOOLCHAIN_UNAVAILABLE", "The command executable is not in an approved workspace or toolchain path.", executable=base_name)
    try:
        executable = candidate.resolve(strict=True)
    except OSError as error:
        raise _failure("SANDBOX_TOOLCHAIN_UNAVAILABLE", "The command executable is missing or unreadable.", executable=base_name) from error
    if not executable.is_file():
        raise _failure("SANDBOX_TOOLCHAIN_UNAVAILABLE", "The command executable is not a regular file.", executable=base_name)
    if _under(executable, workspace_root):
        resolved_argv = [str(executable), *argv[1:]]
        if executable.name.lower() == "node.exe":
            if "--preserve-symlinks-main" not in resolved_argv[1:]:
                resolved_argv.insert(1, "--preserve-symlinks-main")
            if "--preserve-symlinks" not in resolved_argv[1:]:
                resolved_argv.insert(1, "--preserve-symlinks")
        return resolved_argv, roots
    matched_root = next((root for root in roots if _under(executable, root)), None)
    if matched_root is None:
        raise _failure(
            "SANDBOX_TOOLCHAIN_NOT_ALLOWLISTED",
            "The executable is outside the selected workspace and supported read-only toolchains.",
            executable=base_name,
        )
    resolved_argv = [str(executable), *argv[1:]]
    if executable.name.lower() == "node.exe":
        if "--preserve-symlinks-main" not in resolved_argv[1:]:
            resolved_argv.insert(1, "--preserve-symlinks-main")
        if "--preserve-symlinks" not in resolved_argv[1:]:
            resolved_argv.insert(1, "--preserve-symlinks")
    return resolved_argv, roots


def build_mxc_invocation(
    argv: list[str],
    *,
    workspace_root: Path,
    workdir: Path,
    timeout_ms: int,
    extra_environment: Any = None,
) -> MxcInvocation:
    """Build a no-network, exact-root ProcessContainer invocation."""

    if os.name != "nt":
        raise _failure("SANDBOX_UNAVAILABLE", "MXC ProcessContainer is available only on Windows.")
    if not isinstance(argv, list) or not argv or len(argv) > 32:
        raise _failure("SANDBOX_COMMAND_INVALID", "Structured sandbox argv is outside its bounds.")
    if any(not isinstance(item, str) or not item or "\x00" in item or "\r" in item or "\n" in item for item in argv):
        raise _failure("SANDBOX_COMMAND_INVALID", "Structured sandbox argv contains an invalid argument.")
    if not isinstance(timeout_ms, int) or isinstance(timeout_ms, bool) or not 1_000 <= timeout_ms <= 3_600_000:
        raise _failure("SANDBOX_COMMAND_INVALID", "Structured sandbox timeout is outside its bounds.")
    if extra_environment is None:
        extra_environment = {}
    if not isinstance(extra_environment, dict):
        raise _failure("SANDBOX_ENV_INVALID", "Structured sandbox environment must be an object.")
    env_items: list[tuple[str, str]] = []
    seen_environment_names: set[str] = set()
    for key, value in extra_environment.items():
        name = str(key)
        text = str(value)
        folded_name = name.upper()
        if (not _ENV_NAME.fullmatch(name) or folded_name in seen_environment_names
            or any(character in text for character in ("\x00", "\r", "\n"))
            or len(text.encode("utf-8")) > 8192):
            raise _failure("SANDBOX_ENV_INVALID", "Structured sandbox environment contains an invalid key or value.")
        seen_environment_names.add(folded_name)
        if is_filtered_env_var(name, text):
            raise _failure("SANDBOX_ENV_SECRET_DENIED", "Sensitive or loader environment variables cannot be forwarded into the sandbox.", env_key=name)
        if name.upper() in _RESERVED_ENV_NAMES:
            raise _failure("SANDBOX_ENV_OVERRIDE_DENIED", "Reserved sandbox path and process variables cannot be overridden.", env_key=name)
        env_items.append((name, text))

    try:
        root = workspace_root.resolve(strict=True)
        cwd = workdir.resolve(strict=True)
    except OSError as error:
        raise _failure("SANDBOX_WORKSPACE_INVALID", "The selected workspace or working directory is unavailable.") from error
    if not root.is_dir() or not cwd.is_dir() or not _under(cwd, root):
        raise _failure("SANDBOX_WORKSPACE_SCOPE_DENIED", "The command working directory must remain under the selected workspace.")
    if not root.drive or root == Path(root.anchor):
        raise _failure("SANDBOX_WORKSPACE_SCOPE_DENIED", "A drive root cannot be granted as a workspace.")
    system_root = _system_root()
    executor = _executor_path()
    _probe_executor(executor, system_root)
    roots, path_entries = _known_toolchains(system_root, executor)
    cwd_alias_root: Path | None = None
    cwd_alias_path: Path | None = None
    scratch: Path | None = None
    try:
        if root.drive.casefold() != Path(system_root.anchor).drive.casefold():
            # BaseContainer launches child processes with an inaccessible DOS
            # current directory when the selected workspace is on a non-system
            # volume. A one-run CWD junction keeps relative operations on the
            # registered workspace while giving descendants a system-drive path.
            cwd_alias_root = Path(tempfile.mkdtemp(
                prefix="codex-mxc-cwd-", dir=system_root.anchor,
            )).resolve(strict=True)
            cwd_alias_path = cwd_alias_root / "workspace"
            _create_directory_junction(cwd_alias_path, cwd)
        readonly_paths, denied_paths = _build_path_fence(
            root, roots,
            extra_write_roots=[cwd_alias_path] if cwd_alias_path is not None else [],
            extra_readonly_roots=[cwd_alias_root] if cwd_alias_root is not None else [],
        )
        scratch = Path(tempfile.mkdtemp(prefix=".mxc-exec-", dir=str(root))).resolve(strict=True)
        if stat.S_ISLNK(scratch.lstat().st_mode) or (
            getattr(scratch.lstat(), "st_file_attributes", 0)
            & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        ):
            raise _failure("SANDBOX_WORKSPACE_INVALID", "The sandbox scratch path is a reparse point.")
        return _build_mxc_invocation_with_scratch(
            argv=argv, root=root, cwd=cwd, timeout_ms=timeout_ms, extra_env=extra_environment,
            system_root=system_root, executor=executor, roots=roots, path_entries=path_entries,
            readonly_paths=readonly_paths, denied_paths=denied_paths, scratch=scratch,
            cwd_alias_root=cwd_alias_root, cwd_alias_path=cwd_alias_path,
        )
    except Exception:
        if scratch is not None:
            cleanup_mxc_scratch(root, scratch)
        cleanup_mxc_cwd_alias(cwd_alias_root, cwd_alias_path)
        raise


def _build_mxc_invocation_with_scratch(
    *,
    argv: list[str],
    root: Path,
    cwd: Path,
    timeout_ms: int,
    extra_env: dict[str, Any],
    system_root: Path,
    executor: Path,
    roots: list[Path],
    path_entries: list[Path],
    readonly_paths: list[Path],
    denied_paths: list[Path],
    scratch: Path,
    cwd_alias_root: Path | None,
    cwd_alias_path: Path | None,
) -> MxcInvocation:
    resolved_argv, readonly_roots = _resolve_executable(
        list(argv), workspace_root=root, workdir=cwd, scratch_directory=scratch,
        roots=roots, path_entries=path_entries,
    )
    bootstrap_node = next((item / "node.exe" for item in roots if (item / "node.exe").is_file()), None)
    if bootstrap_node is None:
        raise _failure("SANDBOX_TOOLCHAIN_UNAVAILABLE", "The bounded Windows sandbox requires an approved Node.js bootstrap.")
    bootstrap_payload = base64.b64encode(json.dumps({
        "argv": resolved_argv,
        "workspace_root": str(root),
    }, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")).decode("ascii")
    sandbox_command = subprocess.list2cmdline([
        str(bootstrap_node), "--preserve-symlinks", "--preserve-symlinks-main",
        "-e", _WINDOWS_EXEC_BOOTSTRAP, bootstrap_payload,
    ])
    try:
        appdata = scratch / "AppData" / "Roaming"
        local_appdata = scratch / "AppData" / "Local"
        npm_cache = scratch / "npm-cache"
        for directory in (appdata, local_appdata, npm_cache):
            directory.mkdir(parents=True, exist_ok=True)
        safe_path = os.pathsep.join(str(item) for item in path_entries)
        process_environment = [
            f"SystemRoot={system_root}", f"WINDIR={system_root}",
            f"COMSPEC={system_root / 'System32' / 'cmd.exe'}",
            "PATHEXT=.COM;.EXE;.BAT;.CMD",
            f"PATH={safe_path}",
            f"USERPROFILE={scratch}", f"HOME={scratch}",
            f"APPDATA={appdata}", f"LOCALAPPDATA={local_appdata}",
            f"TEMP={scratch}", f"TMP={scratch}", f"TMPDIR={scratch}",
            f"NPM_CONFIG_CACHE={npm_cache}",
            "NODE_OPTIONS=--preserve-symlinks --preserve-symlinks-main",
        ]
        process_environment.extend(f"{key}={value}" for key, value in extra_env.items())
        config = {
            "version": "0.8.0-alpha",
            "containerId": f"codex-{uuid.uuid4().hex}",
            "containment": "processcontainer",
            "lifecycle": {"destroyOnExit": True, "preservePolicy": False},
            "process": {
                "commandLine": sandbox_command,
                "cwd": str(cwd_alias_path or cwd),
                "env": process_environment,
                "timeout": timeout_ms,
            },
            "filesystem": {
                "readwritePaths": [
                    str(root),
                    *([str(cwd_alias_path)] if cwd_alias_path is not None else []),
                ],
                "readonlyPaths": [str(item) for item in readonly_paths],
                "deniedPaths": [str(item) for item in denied_paths],
            },
            "fallback": {"allowDaclMutation": False},
            "network": {
                "egress": {"default": "deny"},
                "ingress": {"default": "deny", "hostLoopback": "deny"},
            },
            "ui": {"disable": False, "clipboard": "none", "injection": False},
        }
        encoded = base64.b64encode(
            json.dumps(config, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
        ).decode("ascii")
        if len(encoded) > MAX_MXC_CONFIG_ARGUMENT_CHARS:
            raise _failure("SANDBOX_CONFIGURATION_TOO_LARGE", "The bounded sandbox configuration exceeds the Windows command-line limit.")
        host_environment = _minimal_host_environment(executor, system_root)
        return MxcInvocation(
            argv=(str(executor), "--experimental", "--config-base64", encoded),
            environment=host_environment,
            scratch_directory=scratch,
            workspace_root=root,
            executor_path=executor,
            cwd_alias_root=cwd_alias_root,
            cwd_alias_path=cwd_alias_path,
        )
    except Exception:
        cleanup_mxc_scratch(root, scratch)
        raise


def cleanup_mxc_scratch(workspace_root: Path, scratch_directory: Path) -> bool:
    """Remove only an exact temporary child of the registered workspace."""

    try:
        root = workspace_root.resolve(strict=True)
        scratch = scratch_directory.absolute()
        if (
            scratch.parent.resolve(strict=True) != root
            or not scratch.name.startswith(".mxc-exec-")
        ):
            return False
        metadata = scratch.lstat()
        reparse = bool(getattr(metadata, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))
        if stat.S_ISLNK(metadata.st_mode) or reparse or not stat.S_ISDIR(metadata.st_mode):
            return False
        shutil.rmtree(scratch)
        return not scratch.exists()
    except (OSError, RuntimeError, ValueError):
        return False


def probe_mxc_child_process(workspace_root: str) -> dict[str, Any]:
    """Verify that the selected Windows sandbox can launch one nested process.

    The MXC capability probe only reports sandbox API availability. This
    bounded smoke test verifies Node/npm child creation, writable temporary
    storage, and Windows realpath support on the exact registered workspace.
    It writes only inside fresh temporary children of that workspace and
    removes them afterward.
    """

    if os.name != "nt":
        return {"probe": "mxc_nested_process_v1", "available": False, "reason": "WINDOWS_ONLY"}
    root: Path | None = None
    invocation: MxcInvocation | None = None
    npm_invocation: MxcInvocation | None = None
    result: subprocess.CompletedProcess[str] | None = None
    npm_result: subprocess.CompletedProcess[str] | None = None
    failure_reason: str | None = None
    cleanup_failed = False
    probe_parent_path: Path | None = None
    try:
        if not isinstance(workspace_root, str) or not workspace_root.strip():
            return {"probe": "mxc_nested_process_v1", "available": False, "reason": "WORKSPACE_INVALID"}
        candidate = Path(workspace_root)
        metadata = candidate.lstat()
        is_reparse = bool(
            getattr(metadata, "st_file_attributes", 0)
            & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        )
        probe_parent_path = candidate.resolve(strict=True)
        if (
            not probe_parent_path.is_dir()
            or probe_parent_path == Path(probe_parent_path.anchor)
            or stat.S_ISLNK(metadata.st_mode)
            or is_reparse
        ):
            return {"probe": "mxc_nested_process_v1", "available": False, "reason": "WORKSPACE_INVALID"}
        root = Path(tempfile.mkdtemp(
            prefix=".mxc-exec-probe-", dir=str(probe_parent_path),
        )).resolve(strict=True)
        child_code = "process.stdout.write('MXC_CHILD_SPAWN_OK\\n')"
        selected_workspace_literal = json.dumps(str(probe_parent_path), ensure_ascii=True)
        parent_code = (
            "const fs=require('fs'),os=require('os'),path=require('path');"
            "const cp=require('child_process');"
            f"const selectedWorkspace={selected_workspace_literal};"
            "const realpathError=(value)=>{try{fs.realpathSync.native(value);return null}"
            "catch(e){return typeof e.code==='string'?e.code:'REALPATH_FAILED'}};"
            "let tempCreated=false,tempError=null;"
            "try{const p=fs.mkdtempSync(path.join(os.tmpdir(),'mxc-temp-probe-'));fs.rmdirSync(p);tempCreated=true}"
            "catch(e){tempError=typeof e.code==='string'?e.code:'TEMP_FAILED'};"
            "const child=cp.spawnSync(process.execPath,["
            "'--preserve-symlinks','--preserve-symlinks-main','-e',"
            f"{json.dumps(child_code)}"
            "],{cwd:process.cwd(),env:process.env,encoding:'utf8'});"
            "process.stdout.write(JSON.stringify({probe:'mxc_nested_process_v1',"
            "status:Number.isInteger(child.status)?child.status:null,"
            "error_code:child.error&&typeof child.error.code==='string'?child.error.code:null,"
            "stdout_marker:String(child.stdout||'').includes('MXC_CHILD_SPAWN_OK'),"
            "workspace_realpath_error:realpathError(selectedWorkspace),"
            "cwd_realpath_error:realpathError(process.cwd()),"
            "temp_created:tempCreated,temp_error:tempError}));"
            "process.stdout.write('\\n')"
        )
        invocation = build_mxc_invocation(
            ["node", "-e", parent_code],
            workspace_root=root,
            workdir=root,
            timeout_ms=10_000,
        )
        result = subprocess.run(
            list(invocation.argv),
            cwd=root,
            env=invocation.environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=MAX_MXC_CHILD_PROBE_SECONDS,
            check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        package = {
            "name": "codex-mxc-child-probe",
            "version": "1.0.0",
            "scripts": {"test": "node -e \"console.log('MXC_NPM_CHILD_OK')\""},
        }
        (root / "package.json").write_text(
            json.dumps(package, ensure_ascii=True), encoding="utf-8",
        )
        npm_invocation = build_mxc_invocation(
            ["npm", "test"],
            workspace_root=root,
            workdir=root,
            timeout_ms=15_000,
        )
        npm_result = subprocess.run(
            list(npm_invocation.argv),
            cwd=root,
            env=npm_invocation.environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=MAX_MXC_CHILD_PROBE_SECONDS,
            check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except subprocess.TimeoutExpired:
        failure_reason = "CHILD_PROCESS_PROBE_TIMEOUT"
    except ToolFailure as error:
        failure_reason = str(getattr(error, "code", "SANDBOX_UNAVAILABLE"))
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError):
        failure_reason = "CHILD_PROCESS_PROBE_FAILED"
    finally:
        scratch_cleaned = True
        for candidate in (invocation, npm_invocation):
            if candidate is not None:
                scratch_cleaned = cleanup_mxc_invocation(candidate) and scratch_cleaned
        if root is not None:
            try:
                if root.exists():
                    metadata = root.lstat()
                    is_reparse = bool(
                        getattr(metadata, "st_file_attributes", 0)
                        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
                    )
                    if (
                        probe_parent_path is not None
                        and root.parent.resolve(strict=True) == probe_parent_path
                        and root.name.startswith(".mxc-exec-probe-")
                        and not stat.S_ISLNK(metadata.st_mode)
                        and not is_reparse
                        and stat.S_ISDIR(metadata.st_mode)
                    ):
                        shutil.rmtree(root)
                cleanup_failed = not scratch_cleaned or root.exists()
            except (OSError, RuntimeError, ValueError):
                cleanup_failed = True

    if cleanup_failed:
        return {"probe": "mxc_nested_process_v1", "available": False, "reason": "CHILD_PROCESS_PROBE_CLEANUP_UNCERTAIN"}
    if failure_reason is not None:
        return {"probe": "mxc_nested_process_v1", "available": False, "reason": failure_reason}
    if result is None or result.returncode != 0:
        return {"probe": "mxc_nested_process_v1", "available": False, "reason": "SANDBOX_PROBE_EXITED"}
    if (len(result.stdout.encode("utf-8", errors="replace")) > 16 * 1024
        or (npm_result is not None and len(npm_result.stdout.encode("utf-8", errors="replace")) > 16 * 1024)):
        return {"probe": "mxc_nested_process_v1", "available": False, "reason": "CHILD_PROCESS_PROBE_OUTPUT_TOO_LARGE"}
    payload = None
    for line in reversed(result.stdout.splitlines()):
        try:
            candidate = json.loads(line)
        except (TypeError, ValueError, json.JSONDecodeError):
            continue
        if (
            isinstance(candidate, dict)
            and candidate.get("probe") == "mxc_nested_process_v1"
            and set(candidate) == {
                "probe", "status", "error_code", "stdout_marker",
                "workspace_realpath_error", "cwd_realpath_error", "temp_created", "temp_error",
            }
            and (candidate.get("status") is None or isinstance(candidate.get("status"), int))
            and (candidate.get("error_code") is None or (
                isinstance(candidate.get("error_code"), str)
                and re.fullmatch(r"[A-Z0-9_]{2,40}", candidate["error_code"]) is not None
            ))
            and isinstance(candidate.get("stdout_marker"), bool)
            and all(candidate.get(key) is None or (
                isinstance(candidate.get(key), str)
                and re.fullmatch(r"[A-Z0-9_]{2,40}", candidate[key]) is not None
            ) for key in ("workspace_realpath_error", "cwd_realpath_error", "temp_error"))
            and isinstance(candidate.get("temp_created"), bool)
        ):
            payload = candidate
            break
    if payload is None:
        return {"probe": "mxc_nested_process_v1", "available": False, "reason": "CHILD_PROCESS_PROBE_OUTPUT_INVALID"}
    if payload["workspace_realpath_error"]:
        return {
            "probe": "mxc_nested_process_v1", "available": False,
            "reason": "WINDOWS_WORKSPACE_REALPATH_" + payload["workspace_realpath_error"],
        }
    if payload["cwd_realpath_error"]:
        return {
            "probe": "mxc_nested_process_v1", "available": False,
            "reason": "WINDOWS_CWD_REALPATH_" + payload["cwd_realpath_error"],
        }
    if not payload["temp_created"]:
        return {
            "probe": "mxc_nested_process_v1", "available": False,
            "reason": "WINDOWS_TEMP_" + (payload["temp_error"] or "UNAVAILABLE"),
        }
    if payload["status"] != 0 or payload["error_code"] is not None or not payload["stdout_marker"]:
        return {
            "probe": "mxc_nested_process_v1", "available": False,
            "reason": "WINDOWS_CHILD_PROCESS_" + (payload["error_code"] or "UNAVAILABLE"),
        }
    if npm_result is None or npm_result.returncode != 0 or "MXC_NPM_CHILD_OK" not in npm_result.stdout:
        return {"probe": "mxc_nested_process_v1", "available": False, "reason": "WINDOWS_NPM_SCRIPT_PROCESS_UNAVAILABLE"}
    return {"probe": "mxc_nested_process_v1", "available": True, "reason": None}
