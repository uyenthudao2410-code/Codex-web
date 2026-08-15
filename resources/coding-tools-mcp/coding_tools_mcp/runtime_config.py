from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from .envutils import ENV_PREFIX, truthy_env
from .errors import ToolFailure
from .fs_utils import is_relative_to


@dataclass(frozen=True)
class ModeCapabilities:
    """What a permission mode allows. Gates consult this instead of comparing mode strings."""

    network: bool
    shell_expansion: bool
    inline_script: bool
    landlock: bool
    secret_env_filter: bool
    global_tmp_write: str  # "blocked" | "tmp-prefix" | "allowed"
    skip_all_permissions: bool


@dataclass(frozen=True)
class ShellEnvPolicy:
    inherit: str = "core"
    include_only: tuple[str, ...] = ()
    exclude: tuple[str, ...] = ()
    set: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class RuntimePolicy:
    permission_mode: str
    shell_env_policy: ShellEnvPolicy
    allow_network: bool
    fake_readonly_annotations: bool = False

KILL_SESSION_STATUSES = ("terminated", "killed", "exited", "terminating", "not_found")

PERMISSION_MODE_CAPABILITIES: dict[str, ModeCapabilities] = {
    "safe": ModeCapabilities(
        network=False,
        shell_expansion=False,
        inline_script=False,
        landlock=True,
        secret_env_filter=True,
        global_tmp_write="blocked",
        skip_all_permissions=False,
    ),
    "trusted": ModeCapabilities(
        network=True,
        shell_expansion=True,
        inline_script=True,
        landlock=True,
        secret_env_filter=True,
        global_tmp_write="tmp-prefix",
        skip_all_permissions=False,
    ),
    "dangerous": ModeCapabilities(
        network=True,
        shell_expansion=True,
        inline_script=True,
        landlock=False,
        secret_env_filter=False,
        global_tmp_write="allowed",
        skip_all_permissions=True,
    ),
}

PERMISSION_MODE_CHOICES = tuple(PERMISSION_MODE_CAPABILITIES)

POSIX_CORE_ENV_NAMES = {"PATH", "LANG", "LC_ALL", "TERM"}
# Not POSIX core, but inherited under inherit="core" so git helper subprocesses and
# exec_command share the host's global git config (e.g. safe.directory entries).
GIT_ENV_NAMES = {"GIT_CONFIG_GLOBAL"}
WINDOWS_CORE_ENV_NAMES = {
    "PATH", "PATHEXT", "COMSPEC", "SYSTEMROOT", "WINDIR",
    "SYSTEMDRIVE", "PROGRAMDATA", "PROGRAMFILES", "PROGRAMFILES(X86)",
    "PROGRAMW6432", "COMMONPROGRAMFILES", "COMMONPROGRAMFILES(X86)",
    "COMMONPROGRAMW6432", "ALLUSERSPROFILE", "PUBLIC",
    "LOCALAPPDATA", "APPDATA", "USERPROFILE", "HOMEDRIVE", "HOMEPATH",
}

RISKY_ENV_NAMES = {
    "BASH_ENV",
    "ENV",
    "LD_PRELOAD",
    "LD_LIBRARY_PATH",
    "DYLD_INSERT_LIBRARIES",
    "PYTHONPATH",
    "PYTHONSTARTUP",
    "NODE_OPTIONS",
    "PERL5LIB",
    "PERL5OPT",
    "RUBYOPT",
    "RUBYLIB",
}

RUNTIME_ROOT_DIR_NAME = "coding-tools-mcp"

SENSITIVE_ENV_RE = re.compile(r"(token|secret|credential|api[_-]?key|password|passwd|private)", re.I)
SENSITIVE_VALUE_RE = re.compile(
    r"(COMPLIANCE_SHOULD_NOT_LEAK|-----BEGIN [A-Z ]*PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9_]+|sk-[A-Za-z0-9_-]{16,}|AKIA[0-9A-Z]{16})"
)

SHELL_ENV_INHERIT_CHOICES = ("core", "all", "none")

def env_pattern_matches(name: str, patterns: tuple[str, ...]) -> bool:
    upper_name = name.upper()
    return any(fnmatch.fnmatchcase(upper_name, pattern.upper()) for pattern in patterns)


def is_risky_env_name(name: str) -> bool:
    upper = name.upper()
    return upper in RISKY_ENV_NAMES or upper.startswith("DYLD_")


def is_filtered_env_var(name: str, value: str) -> bool:
    return bool(SENSITIVE_ENV_RE.search(name) or is_risky_env_name(name) or SENSITIVE_VALUE_RE.search(value))


def is_core_command_env_name(name: str) -> bool:
    upper = name.upper()
    if os.name == "nt":
        return upper in WINDOWS_CORE_ENV_NAMES
    return upper in POSIX_CORE_ENV_NAMES or upper in GIT_ENV_NAMES or upper.startswith("LC_")


def split_env_patterns(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(part.strip() for part in value.split(",") if part.strip())


def parse_shell_env_set(value: str | None) -> dict[str, str]:
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{ENV_PREFIX}_SHELL_ENV_SET must be a JSON object") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"{ENV_PREFIX}_SHELL_ENV_SET must be a JSON object")
    return {str(key): str(item) for key, item in parsed.items()}


def env_int(name: str, fallback: int) -> int:
    raw = (os.environ.get(name) or "").strip()
    try:
        return int(raw) if raw else fallback
    except ValueError:
        return fallback


def configured_runtime_root() -> Path | None:
    configured = os.environ.get(f"{ENV_PREFIX}_RUNTIME_ROOT") or ""
    if not configured.strip():
        return None
    return Path(configured).expanduser()


def runtime_parent_root() -> Path:
    return configured_runtime_root() or Path(tempfile.gettempdir()) / RUNTIME_ROOT_DIR_NAME


def runtime_parent_fallback_root() -> Path | None:
    if configured_runtime_root() is not None:
        return None
    if os.name == "nt":
        return None
    fallback = Path("/tmp") / RUNTIME_ROOT_DIR_NAME
    if fallback == runtime_parent_root():
        return None
    return fallback


def workspace_runtime_hash(workspace: Path) -> str:
    resolved = workspace.expanduser().resolve(strict=False)
    return hashlib.sha256(str(resolved).encode("utf-8")).hexdigest()[:16]


def runtime_dir_for_workspace(workspace: Path, instance_id: str) -> Path:
    root = runtime_parent_root()
    try:
        root_in_workspace = is_relative_to(root.resolve(strict=False), workspace.expanduser().resolve(strict=False))
    except OSError:
        root_in_workspace = False
    if root_in_workspace:
        if configured_runtime_root() is not None:
            raise ToolFailure(
                "INVALID_ARGUMENT",
                f"{ENV_PREFIX}_RUNTIME_ROOT must be outside the configured workspace.",
                category="validation",
            )
        root = runtime_parent_fallback_root() or root
    return root / workspace_runtime_hash(workspace) / instance_id


def fallback_runtime_dir_for_workspace(workspace: Path, instance_id: str) -> Path | None:
    fallback = runtime_parent_fallback_root()
    if fallback is None:
        return None
    return fallback / workspace_runtime_hash(workspace) / instance_id


def shell_env_policy_from_args(args: argparse.Namespace) -> ShellEnvPolicy:
    raw_inherit = args.shell_env_inherit or os.environ.get(f"{ENV_PREFIX}_SHELL_ENV_INHERIT") or "core"
    inherit = raw_inherit.strip().lower()
    if inherit not in SHELL_ENV_INHERIT_CHOICES:
        supported = ", ".join(SHELL_ENV_INHERIT_CHOICES)
        raise ValueError(f"shell env inherit must be one of: {supported}")
    return ShellEnvPolicy(
        inherit=inherit,
        include_only=split_env_patterns(os.environ.get(f"{ENV_PREFIX}_SHELL_ENV_INCLUDE_ONLY")),
        exclude=split_env_patterns(os.environ.get(f"{ENV_PREFIX}_SHELL_ENV_EXCLUDE")),
        set=parse_shell_env_set(os.environ.get(f"{ENV_PREFIX}_SHELL_ENV_SET")),
    )


def permission_mode_from_args(args: argparse.Namespace) -> str:
    skip_all = bool(getattr(args, "dangerously_skip_all_permissions", False)) or truthy_env(
        os.environ.get(f"{ENV_PREFIX}_DANGEROUSLY_SKIP_ALL_PERMISSIONS")
    )
    raw_mode = (
        getattr(args, "permission_mode", None)
        or os.environ.get(f"{ENV_PREFIX}_PERMISSION_MODE")
        or ("dangerous" if skip_all else "safe")
    )
    mode = raw_mode.strip().lower()
    if mode not in PERMISSION_MODE_CHOICES:
        supported = ", ".join(PERMISSION_MODE_CHOICES)
        raise ValueError(f"permission mode must be one of: {supported}")
    return "dangerous" if skip_all else mode


def fake_readonly_annotations_from_args(args: argparse.Namespace, permission_mode: str) -> bool:
    requested = bool(getattr(args, "dangerously_fake_readonly_annotations", False)) or truthy_env(
        os.environ.get(f"{ENV_PREFIX}_DANGEROUSLY_FAKE_READONLY_ANNOTATIONS")
    )
    if requested and permission_mode != "dangerous":
        raise ValueError(
            "--dangerously-fake-readonly-annotations requires --permission-mode dangerous"
        )
    return requested


def runtime_policy_from_args(args: argparse.Namespace) -> RuntimePolicy:
    permission_mode = permission_mode_from_args(args)
    allow_network = (
        PERMISSION_MODE_CAPABILITIES[permission_mode].network
        or bool(getattr(args, "allow_network", False))
        or truthy_env(os.environ.get(f"{ENV_PREFIX}_ALLOW_NETWORK"))
    )
    return RuntimePolicy(
        permission_mode=permission_mode,
        shell_env_policy=shell_env_policy_from_args(args),
        allow_network=allow_network,
        fake_readonly_annotations=fake_readonly_annotations_from_args(args, permission_mode),
    )

