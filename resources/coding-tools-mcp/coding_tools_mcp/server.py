from __future__ import annotations

import argparse
import base64
import copy
import ctypes
import hashlib
import html
import difflib
import fnmatch
import functools
import http.server
import json
import mimetypes
import os
import posixpath
import re
import secrets
import shlex
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import threading
import time
import urllib.parse
import zipfile
from collections.abc import Callable, Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, cast

from . import __version__
from .budget_control import BudgetDeadline, RetryPolicy
from .envutils import ENV_PREFIX, truthy_env
from .errors import JsonRpcError, ToolFailure
from .landlock_exec import libc_syscall
from .oauth import (
    OAUTH_CODE_TTL_SECONDS,
    OAUTH_MAX_BODY_BYTES,
    MAX_PENDING_CODES,
    OAUTH_TOKEN_TTL_SECONDS,
    OAuthConfig,
    create_access_token,
    valid_pkce_challenge,
    validate_access_token,
    verify_pkce,
)
from .patching import (
    AtomicPatchCommitter,
    FileBaseline,
    StagedFile,
    apply_update_hunks,
    parse_patch,
    read_text_preserve_newlines,
)
from .processes import (
    HARD_KILL_SIGNAL,
    SESSION_BUFFER_BYTES,
    ExecSession,
    spawn_process,
    start_reader_threads,
    start_session_watchdog,
    terminate_process_group,
)
from .protocol import (
    LEGACY_PROTOCOL_VERSIONS,
    PROTOCOL_VERSION,
    STATELESS_PROTOCOL_VERSION,
    SUPPORTED_PROTOCOL_VERSIONS,
    dispatch_rpc,
    jsonrpc_error,
    protocol_version_is_supported,
    request_protocol_version,
    response_id,
    validate_rpc_envelope,
)
from .project_context import ProjectContext, load_project_context
from .build_verify import verify_build as run_build_verification
from .codex_bridge import CodexAppServerBridge, CodexBridgeError
from .document_tools import create_docx, create_text_document, convert_document, extract_document
from .task_state import TaskStateStore
from .performance_trace import PerformanceTraceStore
from .orchestration_control import OrchestrationControl, OrchestrationControlError, RunContext, normalize_failure_class
from .orchestration_ledger import OrchestrationLedger, fingerprint_paths
from .orchestration_report import OrchestrationReport
from .proof_ledger import ProofLedger
from .telemetry import SessionTelemetry
from .textutils import DEFAULT_MAX_LINES, TextTruncation, truncate_text_head
from .tool_results import make_tool_result
from .transport_http import HTTPSessionManager
from .transport_stdio import serve_stdio


SERVER_NAME = "coding-tools-mcp"
SERVER_TITLE = "Coding Tools MCP"
PROCESS_INSTANCE_ID = secrets.token_urlsafe(12)
TOOL_MODE_ALLOWLISTS = {
    "smart": frozenset({
        "workspace_context", "agent_workflow", "task_control", "document_workflow",
        "exec_command", "command_control", "request_permissions", "view_image",
    }),
    "readonly": frozenset({"server_info", "check_exec_environment", "task_state_get", "task_history_list", "read_file", "list_dir", "list_files", "search_text", "read_output", "git_status", "git_diff", "git_log", "git_show", "git_blame", "view_image"}),
    "coding": frozenset({"server_info", "check_exec_environment", "task_state_get", "task_state_update", "task_state_pause", "task_state_resume", "task_history_list", "read_file", "list_dir", "list_files", "search_text", "apply_patch", "exec_command", "write_stdin", "kill_session", "read_output", "git_status", "git_diff", "git_log", "git_show", "git_blame", "request_permissions", "verify_build", "view_image"}),
    "build": frozenset({"server_info", "check_exec_environment", "task_state_get", "task_state_update", "task_state_pause", "task_state_resume", "task_history_list", "read_file", "list_dir", "list_files", "search_text", "exec_command", "write_stdin", "kill_session", "read_output", "git_status", "git_diff", "git_log", "git_show", "git_blame", "request_permissions", "verify_build", "view_image"}),
    "full": frozenset(),
}
SMART_COMPAT_TOOL_NAMES = frozenset({
    "server_info", "check_exec_environment",
    "task_state_get", "task_state_update", "task_state_clear", "task_state_pause",
    "task_state_resume", "task_history_list", "read_file", "read_files", "list_dir",
    "list_files", "search_text", "prepare_coding_context", "apply_patch",
    "apply_changes_and_verify", "file_batch", "write_stdin", "kill_session",
    "read_output", "git_status", "git_diff", "git_log", "git_show",
    "git_blame", "git_inspect", "verify_build", "codex_bridge",
})

try:
    LONG_TOOL_HANDOFF_SECONDS = min(
        300,
        max(1, int(os.environ.get(f"{ENV_PREFIX}_LONG_TOOL_HANDOFF_SECONDS", "90"))),
    )
except (TypeError, ValueError):
    LONG_TOOL_HANDOFF_SECONDS = 90
BACKGROUND_OPERATION_WAIT_MAX_MS = 60_000
MAX_BACKGROUND_OPERATIONS = 32
IDEMPOTENCY_RESULT_MAX_BYTES = 256 * 1024
BACKGROUND_BUDGET_POLL_SECONDS = 1.0
try:
    READ_RETRY_ATTEMPTS = max(
        1,
        min(4, int(os.environ.get(f"{ENV_PREFIX}_READ_RETRY_ATTEMPTS", "2"))),
    )
except (TypeError, ValueError):
    READ_RETRY_ATTEMPTS = 2
READ_RETRY_POLICY = RetryPolicy(
    max_attempts=READ_RETRY_ATTEMPTS,
    base_delay_seconds=0.25,
    max_delay_seconds=2.0,
    jitter=0.25,
)
PROCESS_BACKGROUND_OPERATIONS: dict[str, dict[str, Any]] = {}
PROCESS_BACKGROUND_OPERATIONS_LOCK = threading.RLock()
AGENT_EXTERNAL_REVIEW_ENV = f"{ENV_PREFIX}_EXTERNAL_REVIEW"
AGENT_REVIEW_PACKET_MAX_DIFF_CHARS = 12_000
AGENT_REVIEW_DEADLINE_MS = 8_000
AGENT_REVIEW_OUTPUT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "verdict": {"type": "string", "enum": ["accept", "fix", "blocked"]},
        "findings": {
            "type": "array",
            "maxItems": 5,
            "items": {"type": "string", "maxLength": 500},
        },
        "missing_proof": {
            "type": "array",
            "maxItems": 5,
            "items": {"type": "string", "maxLength": 500},
        },
        "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
    },
    "required": ["verdict", "findings", "missing_proof", "confidence"],
}
COORDINATION_LANE_OUTPUT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "status": {
            "type": "string",
            "enum": ["completed", "blocked", "needs_input"],
        },
        "summary": {"type": "string", "maxLength": 2_000},
        "question": {"type": ["string", "null"], "maxLength": 1_000},
        "findings": {
            "type": "array",
            "maxItems": 8,
            "items": {"type": "string", "maxLength": 700},
        },
        "missing_proof": {
            "type": "array",
            "maxItems": 8,
            "items": {"type": "string", "maxLength": 700},
        },
        "next_action": {"type": "string", "maxLength": 1_000},
        "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
    },
    "required": [
        "status",
        "summary",
        "question",
        "findings",
        "missing_proof",
        "next_action",
        "confidence",
    ],
}
AGENT_CANDIDATE_PACKET_MAX_CHARS = 14_000

AGENT_CANDIDATE_OUTPUT_SCHEMA = {

    "type": "object",

    "additionalProperties": False,

    "properties": {

        "status": {"type": "string", "enum": ["ready", "blocked"]},

        "summary": {"type": "string", "maxLength": 1_000},

        "replacements": {

            "type": "array",

            "maxItems": 8,

            "items": {

                "type": "object",

                "additionalProperties": False,

                "properties": {

                    "path": {"type": "string", "maxLength": 500},

                    "old": {"type": "string", "maxLength": 8_000},

                    "new": {"type": "string", "maxLength": 8_000},

                },

                "required": ["path", "old", "new"],

            },

        },

        "new_files": {

            "type": "array",

            "maxItems": 4,

            "items": {

                "type": "object",

                "additionalProperties": False,

                "properties": {

                    "path": {"type": "string", "maxLength": 500},

                    "content": {"type": "string", "maxLength": 12_000},

                },

                "required": ["path", "content"],

            },

        },

        "proof": {

            "type": "array",

            "maxItems": 4,

            "items": {"type": "string", "maxLength": 500},

        },

        "confidence": {"type": "string", "enum": ["low", "medium", "high"]},

    },

    "required": ["status", "summary", "replacements", "new_files", "proof", "confidence"],

}

AGENT_EXECUTION_ROUTES = {

    "mini": {"profile": "candidate_mini", "model": "gpt-5.4-mini", "effort": "low", "deadline_ms": 10_000, "high_cost": False},

    "luna": {"profile": "candidate_luna", "model": "gpt-5.6-luna", "effort": "high", "deadline_ms": 15_000, "high_cost": False},

    "terra": {"profile": "cross_file", "model": "gpt-5.6-terra", "effort": "high", "deadline_ms": 25_000, "high_cost": False},

    "sol_xhigh": {"profile": "deep_code", "model": "gpt-5.6-sol", "effort": "xhigh", "deadline_ms": 30_000, "high_cost": False},

    "sol_max": {"profile": "consequential", "model": "gpt-5.6-sol", "effort": "max", "deadline_ms": 30_000, "high_cost": True},

    "sol_ultra": {"profile": "parallel_extreme", "model": "gpt-5.6-sol", "effort": "ultra", "deadline_ms": 30_000, "high_cost": True},

}

MCP_ENDPOINT_PATH = "/mcp"
STATELESS_HTTP_2026_ENV = f"{ENV_PREFIX}_STATELESS_HTTP_2026"
DEFAULT_EXCLUDED_NAMES = {
    ".git",
    ".reference",
    "node_modules",
    "target",
    "dist",
    "build",
    ".venv",
    "venv",
    ".tox",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
}
GREP_MAX_LINE_CHARS = 500
IMAGE_RESIZE_MAX_DIMENSION = 2000
SENSITIVE_ENV_RE = re.compile(r"(token|secret|credential|api[_-]?key|password|passwd|private)", re.I)
SENSITIVE_VALUE_RE = re.compile(
    r"(COMPLIANCE_SHOULD_NOT_LEAK|-----BEGIN [A-Z ]*PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9_]+|sk-[A-Za-z0-9_-]{16,}|AKIA[0-9A-Z]{16})"
)
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
SHELL_ENV_INHERIT_CHOICES = ("core", "all", "none")


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
# Documented kill_session status enum; guarded by test_schema_drift.
KILL_SESSION_STATUSES = ("terminated", "killed", "exited", "terminating", "not_found")
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
NETWORK_RE = re.compile(
    r"(https?://|urllib\.request|urllib3|requests\.|http\.client|\bHTTPConnection\b|\bHTTPSConnection\b|socket\.|aiohttp|httpx|\bcurl\b|\bwget\b|\bnc\b|\bnetcat\b|\bssh\b|\bscp\b|\bftp\b)",
    re.I,
)
SHELL_EXPANSION_RE = re.compile(r"(`|\$\(|\$\{)")
DESTRUCTIVE_RE = re.compile(
    r"(^|\s)(sudo|su|chmod\s+-R|chown\s+-R|mkfs|mount|umount|find\b[^;&|]*\s-delete\b|git\b[^;&|]*\breset\s+--hard\b|git\b[^;&|]*\bclean\s+-[^\s]*[fx][^\s]*|rm\s+-[^\s]*r[^\s]*f|rm\s+-[^\s]*f[^\s]*r)\b",
    re.I,
)
MAX_HTTP_REQUEST_BYTES = 1_048_576
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
SHELL_CONTROL_TOKENS = {"|", "||", "&", "&&", ";", "(", ")"}
REDIRECTION_TOKENS = {">", ">>", "<", "<>", ">&", "<&", "&>", "&>>"}
HEREDOC_TOKENS = {"<<", "<<<"}
PATH_ARGUMENT_COMMANDS = {
    "cat",
    "cd",
    "chdir",
    "chmod",
    "chown",
    "cp",
    "head",
    "less",
    "ln",
    "ls",
    "mkdir",
    "more",
    "mv",
    "rm",
    "rmdir",
    "stat",
    "tail",
    "touch",
    "wc",
}
PATTERN_THEN_PATH_COMMANDS = {"grep", "egrep", "fgrep", "rg", "sed", "awk"}
SCRIPT_COMMANDS = {"bash", "sh", "zsh", "python", "python3", "node", "ruby", "perl"}
ENV_OPTIONS_WITH_ARGUMENT = {
    "-u",
    "--unset",
    "-C",
    "--chdir",
    "-S",
    "--split-string",
    "-a",
    "--argv0",
}
ENV_LONG_OPTIONS_WITH_ARGUMENT = {
    "--unset",
    "--chdir",
    "--split-string",
    "--argv0",
}
ENV_LONG_OPTIONS_WITH_OPTIONAL_ARGUMENT = {
    "--ignore-signal",
    "--default-signal",
    "--block-signal",
}
ENV_SHORT_OPTIONS_WITH_ATTACHED_ARGUMENT = ("-u", "-C", "-S", "-a")
ENV_FLAG_OPTIONS = {
    "-i",
    "--ignore-environment",
    "-0",
    "--null",
    "-v",
    "--debug",
    "--ignore-signal",
    "--default-signal",
    "--block-signal",
    "--list-signal-handling",
}
NETWORK_LITERAL_COMMANDS = {"echo", "printf", "grep", "egrep", "fgrep", "rg", "cat", "head", "tail", "wc"}
INLINE_SCRIPT_PERMISSION = "inline_script"
RUNTIME_ROOT_DIR_NAME = "coding-tools-mcp"
SPECIAL_DEVICE_PATHS = ("/dev/null", "/dev/zero", "/dev/random", "/dev/urandom")
DNS_RESOLVER_READ_ROOTS = (
    "/etc/resolv.conf",
    "/etc/hosts",
    "/etc/nsswitch.conf",
    "/etc/gai.conf",
    "/etc/protocols",
    "/etc/services",
    "/run/systemd/resolve",
    "/run/resolvconf",
)
TOOLCHAIN_READ_ROOTS = (
    "/usr",
    "/bin",
    "/sbin",
    "/lib",
    "/lib64",
    "/etc/alternatives",
    "/etc/ssl",
    "/etc/ca-certificates",
    "/etc/pki",
    "/etc/localtime",
    "/etc/npmrc",
    "/usr/local/sdkman/candidates",
)
OS_METADATA_READ_FILES = (
    "/etc/debian_version",
    "/etc/os-release",
    "/etc/lsb-release",
)
GIT_READ_ROOTS = (
    "/etc/gitconfig",
    "/etc/gitconfig.d",
)
SYSTEM_PATH_ROOT_PREFIXES = (
    "/bin",
    "/sbin",
    "/usr",
    "/lib",
    "/lib64",
    "/etc/alternatives",
    "/usr/local/sdkman/candidates",
)
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


OAUTH_TOKEN_AUTH_METHODS = ("client_secret_basic", "client_secret_post", "none")


def _http_base_for_bind_host(host: str, port: int) -> str:
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    return f"http://{host}:{port}"


def _first_header_value(value: str | None) -> str:
    return (value or "").split(",", 1)[0].strip()


def _first_form_value(params: dict[str, list[str]], key: str) -> str:
    values = params.get(key)
    return values[0] if values else ""


def stateless_http_2026_enabled() -> bool:
    """Both MCP eras are served by default on every transport, matching upstream.

    Legacy 2025-11-25/2025-06-18 clients are unaffected: they never send a
    modern MCP-Protocol-Version header or params._meta protocolVersion.
    Operators can explicitly disable the modern era with
    CODING_TOOLS_MCP_STATELESS_HTTP_2026=0.
    """

    raw = os.environ.get(STATELESS_HTTP_2026_ENV)
    if raw is None:
        return True
    return truthy_env(raw)


def _decode_mcp_name_header(value: str) -> str | None:
    if not (value.startswith("=?base64?") and value.endswith("?=")):
        return value
    try:
        raw = base64.b64decode(value[len("=?base64?") : -2], validate=True)
        return raw.decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return None


def _request_mcp_name(request: dict[str, Any]) -> str | None:
    params = request.get("params")
    if not isinstance(params, dict):
        return None
    method = str(request.get("method") or "")
    if method in {"tools/call", "prompts/get"}:
        value = params.get("name")
        return value if isinstance(value, str) else None
    if method == "resources/read":
        value = params.get("uri")
        return value if isinstance(value, str) else None
    return None


def _forwarded_header_param(value: str | None, name: str) -> str:
    first = _first_header_value(value)
    for part in first.split(";"):
        key, sep, raw = part.strip().partition("=")
        if sep and key.lower() == name:
            return raw.strip().strip('"')
    return ""


def _safe_external_host(host: str) -> str:
    host = host.strip()
    if not host or any(ch.isspace() or ch in "/\\@?#" for ch in host):
        return ""
    try:
        parsed = urllib.parse.urlsplit(f"//{host}")
        _ = parsed.port
    except ValueError:
        return ""
    if not parsed.hostname or parsed.username is not None or parsed.password is not None:
        return ""
    return host


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


@dataclass(frozen=True)
class ToolSpec:
    """Single source of truth for one tool's title, description, and annotation hints.

    Handler methods on Runtime are named exactly after the tool. Input schemas live in
    input_schemas(), keyed by the same names. `error_status` is stamped on failure
    payloads, and `content_builder` converts a success payload into extra MCP
    content blocks (beyond the rendered text).
    """

    title: str
    description: str
    read_only: bool = False
    destructive: bool = False
    idempotent: bool = False
    open_world: bool = False
    error_status: str | None = None
    content_builder: Callable[[dict[str, Any]], list[dict[str, Any]]] | None = None
    gated_by: str | None = None
    """Name of a Runtime attribute that must be truthy for the tool to be exposed."""


def _image_content(payload: dict[str, Any]) -> list[dict[str, Any]]:
    encoded = str(payload.pop("_mcp_image_data", ""))
    return [
        {
            "type": "image",
            "data": encoded,
            "mimeType": str(payload.get("mime_type", "application/octet-stream")),
        }
    ]


TOOL_REGISTRY: dict[str, ToolSpec] = {
    "server_info": ToolSpec(
        title="Server info",
        description="Return server, workspace, project-context, auth, policy, and fixed-tool metadata.",
        read_only=True,
        idempotent=True,
    ),
    "workspace_context": ToolSpec(
        title="Inspect workspace",
        description="Preferred read-only tool when the user asks what is in the current working directory or wants a quick project overview. Returns the active workspace, default directory, project type, root entries, Git status, and task summary in one call; do not use exec_command merely to list files.",
        read_only=True,
        idempotent=True,
    ),
    "codex_bridge": ToolSpec(
        title="Bridge to local Codex",
        description="Coordinate a cost-aware independent Codex App Server reviewer sidecar with packet/scoped/critical/history profiles, explicit model/effort/deadlines, bridge-owned continuation, capacity cooldowns, and token telemetry. It shares Codex Desktop auth/history but never controls a live Desktop turn; every bridge turn is approvalPolicy=never, read-only, and no-network.",
        read_only=True,
    ),
    "agent_workflow": ToolSpec(
        title="Run complete agent workflow",
        description="Primary tool for end-to-end work. Use one call for bug diagnosis, feature development, greenfield project creation, refactoring, test-failure repair, build/release verification, document work, or task resume. It bundles context collection, file creation or patches, commands, tests, builds, artifacts, Git diff, and persistent task state so the model must not repeat environment checks or low-level tool calls.",
        destructive=True,
    ),
    "prepare_coding_context": ToolSpec(
        title="Prepare coding context",
        description="Preferred first step for coding tasks: inspect the project, task state, instructions and Git once, batch-search multiple queries, and read the most relevant files in one cached call.",
        read_only=True,
        idempotent=True,
    ),
    "apply_changes_and_verify": ToolSpec(
        title="Apply changes and verify",
        description="Preferred execution step: apply one or more patches, run multiple checks, optionally test/build, collect Git diff and update task state in one continuous call. Original low-level tools remain available as fallbacks.",
        destructive=True,
    ),
    "task_control": ToolSpec(
        title="Control persistent task",
        description="Start, inspect, update, pause, stop, resume, clear, or list history for the current workspace task.",
        idempotent=True,
    ),
    "read_files": ToolSpec(
        title="Read multiple files",
        description="Read one or more UTF-8 workspace files in one bounded call.",
        read_only=True,
        idempotent=True,
    ),
    "file_batch": ToolSpec(
        title="Batch file operations",
        description="Create directories or copy, move, and delete multiple workspace paths in one bounded atomic-style request.",
        destructive=True,
    ),
    "command_control": ToolSpec(
        title="Control command session",
        description="Poll, write to, terminate, or page output from a running command session.",
    ),
    "git_inspect": ToolSpec(
        title="Inspect Git repository",
        description="Run status, diff, log, show, or blame through one compact Git inspection tool.",
        read_only=True,
        idempotent=True,
    ),
    "document_workflow": ToolSpec(
        title="Read or create documents in one step",
        description="Mandatory fast path for PDF, Word, Markdown, and text tasks. To create content from a PDF/DOCX, call action=inspect exactly once, reason over the returned text, then call action=create exactly once with target/content. Create supports .docx, .md, and .txt and already returns size, line count, SHA256, and preview, so never probe Python/PDF dependencies, use exec_command/apply_patch, repeat extraction, or run a separate verification command.",
        destructive=True,
    ),
    "document_extract": ToolSpec(
        title="Extract Word or PDF",
        description="Extract text and metadata from a workspace DOCX, PDF, or supported text document.",
        read_only=True,
        idempotent=True,
    ),
    "document_create": ToolSpec(
        title="Create Word document",
        description="Create a DOCX file directly in the workspace from structured plain text or Markdown-like content.",
        destructive=True,
    ),
    "document_convert": ToolSpec(
        title="Convert document to Word",
        description="Convert a workspace PDF or supported text document into a DOCX file without Base64 round-trips.",
        destructive=True,
    ),
    "check_exec_environment": ToolSpec(
        title="Check exec environment",
        description="Return lightweight exec_command sandbox and environment status known to the server.",
        read_only=True,
        idempotent=True,
    ),
    "get_default_cwd": ToolSpec(
        title="Get default cwd (deprecated)",
        description="Deprecated compatibility stub: always returns the workspace root. Transport-level default_cwd was removed; pass explicit paths/workdir per call.",
        read_only=True,
        idempotent=True,
    ),
    "set_default_cwd": ToolSpec(
        title="Set default cwd (deprecated)",
        description="Deprecated compatibility stub: transport-level default_cwd is no longer mutable. Pass explicit paths/workdir per call.",
        idempotent=True,
    ),
    "task_state_get": ToolSpec(
        title="Get task state",
        description="Read the persistent coding-task objective, progress, commands, results, modified files, failure, and next step.",
        read_only=True,
        idempotent=True,
    ),
    "task_state_update": ToolSpec(
        title="Update task state",
        description="Create or update the persistent coding-task objective, plan progress, failure, and next step.",
        idempotent=True,
    ),
    "task_state_clear": ToolSpec(
        title="Clear task state",
        description="Clear the current workspace task state after a task is finished or deliberately abandoned.",
        destructive=True,
        idempotent=True,
    ),
    "task_state_pause": ToolSpec(title="Pause task", description="Pause the current persistent task without losing progress.", idempotent=True),
    "task_state_resume": ToolSpec(title="Resume task", description="Resume a paused persistent task from its recorded next step.", idempotent=True),
    "task_history_list": ToolSpec(title="List task history", description="List archived tasks for the current workspace.", read_only=True, idempotent=True),
    "read_file": ToolSpec(
        title="Read file",
        description="Read a UTF-8 text file slice inside the configured workspace.",
        read_only=True,
        idempotent=True,
    ),
    "list_dir": ToolSpec(
        title="List directory",
        description="List directory entries inside the configured workspace.",
        read_only=True,
        idempotent=True,
    ),
    "list_files": ToolSpec(
        title="List files",
        description="List workspace files using glob filters.",
        read_only=True,
        idempotent=True,
    ),
    "search_text": ToolSpec(
        title="Search text",
        description="Search UTF-8 workspace files for text or regex matches.",
        read_only=True,
        idempotent=True,
    ),
    "apply_patch": ToolSpec(
        title="Apply patch",
        description="Stage, validate, and atomically replace files from a patch envelope inside the workspace.",
        destructive=True,
    ),
    "exec_command": ToolSpec(
        title="Execute command",
        description="Fallback for a focused workspace command only when no high-level workflow can perform it. Never use this tool to list a directory, inspect or create PDF/DOCX/Markdown/text documents, probe Python or PDF dependencies, or verify a document write; workspace_context and document_workflow perform those tasks with fewer round trips.",
        destructive=True,
        open_world=True,
        error_status="failed",
    ),
    "verify_build": ToolSpec(
        title="Build and verify project",
        description="Detect the project, run its tests and build under the command policy, verify artifacts, read version metadata, hash outputs, and return a build report.",
        destructive=True,
        open_world=True,
        error_status="failed",
    ),
    "write_stdin": ToolSpec(
        title="Write stdin",
        description=(
            "Poll or interact with a running command session. Pass empty chars to wait for more output; "
            "pass non-empty chars to write to stdin."
        ),
    ),
    "kill_session": ToolSpec(
        title="Kill session",
        description="Terminate a server-managed running command session.",
        destructive=True,
    ),
    "read_output": ToolSpec(
        title="Read output",
        description="Read retained stdout or stderr by output_ref with per-stream byte offset pagination.",
        read_only=True,
        idempotent=True,
    ),
    "git_status": ToolSpec(
        title="Git status",
        description="Return git working tree status for the workspace.",
        read_only=True,
        idempotent=True,
    ),
    "git_diff": ToolSpec(
        title="Git diff",
        description="Return unified git diff for workspace changes.",
        read_only=True,
        idempotent=True,
    ),
    "git_log": ToolSpec(
        title="Git log",
        description="Return recent git commits with bounded structured metadata.",
        read_only=True,
        idempotent=True,
    ),
    "git_show": ToolSpec(
        title="Git show",
        description="Return bounded git show output for a revision.",
        read_only=True,
        idempotent=True,
    ),
    "git_blame": ToolSpec(
        title="Git blame",
        description="Return bounded git blame metadata for a workspace file.",
        read_only=True,
        idempotent=True,
    ),
    "request_permissions": ToolSpec(
        title="Request permissions",
        description="Report scoped permission-request status without silently granting operations.",
        read_only=True,
    ),
    "view_image": ToolSpec(
        title="View image",
        description="Return a workspace image as MCP image content.",
        read_only=True,
        idempotent=True,
        content_builder=_image_content,
        gated_by="enable_view_image",
    ),
}

LANDLOCK_CREATE_RULESET_VERSION = 1
LANDLOCK_RULE_PATH_BENEATH = 1
SYS_LANDLOCK_CREATE_RULESET = 444
SYS_LANDLOCK_ADD_RULE = 445
LANDLOCK_ACCESS_FS_EXECUTE = 1 << 0
LANDLOCK_ACCESS_FS_WRITE_FILE = 1 << 1
LANDLOCK_ACCESS_FS_READ_FILE = 1 << 2
LANDLOCK_ACCESS_FS_READ_DIR = 1 << 3
LANDLOCK_ACCESS_FS_REMOVE_DIR = 1 << 4
LANDLOCK_ACCESS_FS_REMOVE_FILE = 1 << 5
LANDLOCK_ACCESS_FS_MAKE_CHAR = 1 << 6
LANDLOCK_ACCESS_FS_MAKE_DIR = 1 << 7
LANDLOCK_ACCESS_FS_MAKE_REG = 1 << 8
LANDLOCK_ACCESS_FS_MAKE_SOCK = 1 << 9
LANDLOCK_ACCESS_FS_MAKE_FIFO = 1 << 10
LANDLOCK_ACCESS_FS_MAKE_BLOCK = 1 << 11
LANDLOCK_ACCESS_FS_MAKE_SYM = 1 << 12
LANDLOCK_ACCESS_FS_REFER = 1 << 13
LANDLOCK_ACCESS_FS_TRUNCATE = 1 << 14
LANDLOCK_ACCESS_FS_IOCTL_DEV = 1 << 15


def json_response_payload(payload: Any) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


@functools.lru_cache(maxsize=8)
def _configured_allowed_origins(raw: str) -> frozenset[str]:
    return frozenset(item.strip().rstrip("/") for item in raw.split(",") if item.strip())


def is_allowed_origin(origin: str) -> bool:
    # Authentication does not replace browser Origin validation.
    try:
        parsed = urllib.parse.urlparse(origin)
    except ValueError:
        return False
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.params
        or parsed.query
        or parsed.fragment
    ):
        return False
    try:
        _ = parsed.port
    except ValueError:
        return False
    normalized = origin.rstrip("/")
    configured = _configured_allowed_origins(os.environ.get(f"{ENV_PREFIX}_ALLOWED_ORIGINS", ""))
    return parsed.hostname in {"localhost", "127.0.0.1", "::1"} or normalized in configured


def is_loopback_bind_host(host: str) -> bool:
    return host in {"localhost", "127.0.0.1", "::1", ""}


def truncate_bytes(data: bytes, limit: int) -> tuple[str, bool]:
    if limit <= 0:
        limit = 1
    truncated = len(data) > limit
    if truncated:
        marker = b"\n... output truncated ...\n"
        if limit > len(marker) + 2:
            remaining = limit - len(marker)
            head = max(1, remaining // 2)
            tail = max(1, remaining - head)
            data = data[:head] + marker + data[-tail:]
        else:
            data = data[:limit]
    return data.decode("utf-8", errors="replace"), truncated


def truncate_line_chars(line: str, max_chars: int = GREP_MAX_LINE_CHARS) -> tuple[str, bool]:
    if len(line) <= max_chars:
        return line, False
    suffix = " ... [truncated]"
    keep = max(0, max_chars - len(suffix))
    return line[:keep] + suffix, True


def normalize_rel_display(path: Path, root: Path) -> str:
    try:
        rel = path.relative_to(root)
    except ValueError:
        return path.as_posix()
    text = rel.as_posix()
    return "." if text == "" else text


def matches_any_glob(rel: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(rel, pattern) or PurePosixPath(rel).match(pattern) for pattern in patterns)


def file_entry(path: Path, rel: str, path_stat: os.stat_result) -> dict[str, Any]:
    return {
        "path": rel,
        "type": "symlink" if path.is_symlink() else "file",
        "size_bytes": path_stat.st_size,
        "modified": datetime.fromtimestamp(path_stat.st_mtime, timezone.utc).isoformat().replace("+00:00", "Z"),
    }


def search_match_item(
    rel: str,
    line_number: int,
    column: int,
    line: str,
    before: list[str],
    after: list[str],
    max_preview_bytes: int,
) -> dict[str, Any]:
    preview, line_truncated = truncate_line_chars(line)
    preview_truncation = truncate_text_head(preview, max_lines=1, max_bytes=max_preview_bytes)
    item: dict[str, Any] = {
        "path": rel,
        "line": line_number,
        "column": column,
        "preview": preview_truncation.content,
        "before": before,
        "after": after,
    }
    if line_truncated or preview_truncation.truncated:
        item["preview_truncated"] = True
        item["preview_truncated_by"] = "chars" if line_truncated else preview_truncation.truncated_by
    return item


def truncation_fields(truncation: TextTruncation) -> dict[str, Any]:
    return {
        "truncated": truncation.truncated,
        "truncated_by": truncation.truncated_by,
        "output_lines": truncation.output_lines,
        "output_bytes": truncation.output_bytes,
    }


def read_output_action(output_ref: str, *, offset: int = 0, limit: int | None = None) -> dict[str, Any]:
    return {
        "tool": "read_output",
        "arguments": {
            "output_ref": output_ref,
            "offset": offset,
            "limit": EXEC_PREVIEW_BYTES if limit is None else limit,
        },
    }


_TOOL_PATHS: dict[str, str] = {}
_CONTEXT_BUNDLE_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_CONTEXT_BUNDLE_CACHE_LOCK = threading.Lock()
CONTEXT_BUNDLE_CACHE_TTL_SECONDS = 30
_FAST_TOOL_CACHE: dict[str, tuple[float, int, dict[str, Any]]] = {}
_FAST_TOOL_CACHE_LOCK = threading.Lock()
_WORKSPACE_CACHE_GENERATION: dict[str, int] = {}
_WORKSPACE_PREHEAT_STARTED: set[str] = set()


def cached_which(*names: str) -> str | None:
    """shutil.which with a success-only cache: absence keeps re-probing so a
    tool installed mid-session is still picked up."""
    cached = _TOOL_PATHS.get(names[0])
    if cached:
        return cached
    for name in names:
        path = shutil.which(name)
        if path:
            _TOOL_PATHS[names[0]] = path
            return path
    return None


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def landlock_unavailable_warning(exc: ToolFailure) -> str:
    reason = ""
    details = getattr(exc, "details", None)
    if isinstance(details, dict) and details.get("reason"):
        reason = f" ({details['reason']})"
    return (
        "Linux Landlock filesystem confinement is unavailable on this host"
        f"{reason}; exec_command ran with policy checks only. "
        "Use an external sandbox before running untrusted commands."
    )


def landlock_status_payload() -> dict[str, Any]:
    try:
        version = landlock_abi_version()
    except ToolFailure as exc:
        return {
            "available": False,
            "abi_version": None,
            "reason": exc.message,
            "details": exc.details,
        }
    return {
        "available": True,
        "abi_version": version,
    }


def truncate_evidence(text: str, limit: int = 240) -> str:
    text = " ".join(text.strip().split())
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


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


def hidden_process_popen_kwargs() -> dict[str, Any]:
    """Prevent console helper processes from flashing a window on Windows."""
    if os.name != "nt":
        return {}
    creation_flag = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return {"creationflags": creation_flag} if creation_flag else {}


@dataclass
class ResolvedPath:
    display: str
    path: Path
    existed: bool


class Workspace:
    def __init__(self, root: Path, authorized_roots: list[Path] | None = None) -> None:
        self.root = root.expanduser().resolve(strict=True)
        if not self.root.is_dir():
            raise ToolFailure("INVALID_ARGUMENT", "Workspace root must be a directory.", category="validation")
        unsafe_roots = {"/"}
        try:
            unsafe_roots.add(str(Path.home().resolve()))
        except RuntimeError:
            pass
        if str(self.root) in unsafe_roots:
            raise ToolFailure("INVALID_ARGUMENT", "Unsafe workspace root rejected.", category="security")
        roots: list[Path] = [self.root]
        seen = {os.path.normcase(str(self.root))}
        for raw in authorized_roots or []:
            try:
                resolved = raw.expanduser().resolve(strict=True)
            except (OSError, RuntimeError):
                continue
            if not resolved.is_dir() or resolved.parent == resolved:
                continue
            key = os.path.normcase(str(resolved))
            if key in seen:
                continue
            seen.add(key)
            roots.append(resolved)
        self.authorized_roots = tuple(roots)
        self.git_path = shutil.which("git")

    def _candidate(self, base: Path, raw_path: str) -> Path:
        if not isinstance(raw_path, str) or not raw_path:
            raise ToolFailure("INVALID_ARGUMENT", "Path must be a non-empty string.", category="validation")
        if "\x00" in raw_path:
            raise ToolFailure("INVALID_ARGUMENT", "Path contains a NUL byte.", category="validation")
        candidate = Path(raw_path).expanduser()
        if candidate.is_absolute():
            return candidate
        pure = PurePosixPath(raw_path.replace("\\", "/"))
        if any(part == ".." for part in pure.parts):
            raise ToolFailure("PATH_OUTSIDE_WORKSPACE", "Path escapes the configured workspace.", category="security")
        return base.joinpath(candidate)

    def _containing_root(self, path: Path) -> Path | None:
        for root in sorted(self.authorized_roots, key=lambda item: len(str(item)), reverse=True):
            if path == root or is_relative_to(path, root):
                return root
        return None

    def _is_allowed(self, path: Path) -> bool:
        return self._containing_root(path) is not None

    def resolve_existing(self, raw_path: str = ".") -> ResolvedPath:
        return self.resolve_existing_at(self.root, raw_path)

    def resolve_existing_at(self, base: Path, raw_path: str = ".") -> ResolvedPath:
        base = self._validate_base(base)
        candidate = self._candidate(base, raw_path or ".")
        try:
            resolved = candidate.resolve(strict=True)
        except FileNotFoundError as exc:
            raise ToolFailure("NOT_FOUND", f"Path not found: {raw_path}", category="not_found") from exc
        if not self._is_allowed(resolved):
            code = "SYMLINK_ESCAPE" if candidate.is_symlink() else "PATH_OUTSIDE_WORKSPACE"
            raise ToolFailure(code, "Path is outside the configured workspace and authorized roots.", category="security")
        return ResolvedPath(normalize_rel_display(resolved, self.root), resolved, True)

    def resolve_for_write(self, raw_path: str) -> ResolvedPath:
        return self.resolve_for_write_at(self.root, raw_path)

    def resolve_for_write_at(self, base: Path, raw_path: str) -> ResolvedPath:
        candidate_input = Path(raw_path).expanduser()
        if candidate_input.name in {"", ".", ".."}:
            raise ToolFailure("INVALID_ARGUMENT", "Invalid write target.", category="validation")
        base = self._validate_base(base)
        candidate = self._candidate(base, raw_path)
        if candidate.exists() or candidate.is_symlink():
            resolved = candidate.resolve(strict=True)
            if not self._is_allowed(resolved):
                raise ToolFailure("SYMLINK_ESCAPE", "Path escapes the configured workspace.", category="security")
            return ResolvedPath(normalize_rel_display(resolved, self.root), resolved, True)

        parent = candidate.parent
        missing: list[Path] = []
        while not parent.exists():
            missing.append(parent)
            if any(parent == root for root in self.authorized_roots) or parent.parent == parent:
                break
            parent = parent.parent
        try:
            resolved_parent = parent.resolve(strict=True)
        except FileNotFoundError as exc:
            raise ToolFailure("NOT_FOUND", f"Parent directory not found: {raw_path}", category="not_found") from exc
        if not self._is_allowed(resolved_parent):
            raise ToolFailure("PATH_OUTSIDE_WORKSPACE", "Path is outside the configured workspace and authorized roots.", category="security")
        target = resolved_parent.joinpath(*reversed([p.name for p in missing]), candidate.name)
        return ResolvedPath(normalize_rel_display(target, self.root), target, False)

    def _validate_base(self, base: Path) -> Path:
        try:
            resolved = base.resolve(strict=True)
        except FileNotFoundError as exc:
            raise ToolFailure("NOT_FOUND", "Default cwd path no longer exists.", category="not_found") from exc
        if not resolved.is_dir():
            raise ToolFailure("NOT_A_DIRECTORY", "Default cwd is not a directory.", category="validation")
        if not self._is_allowed(resolved):
            raise ToolFailure("PATH_OUTSIDE_WORKSPACE", "Default cwd is outside the configured workspace and authorized roots.", category="security")
        return resolved

    def reject_write_symlink(self, raw_path: str) -> None:
        candidate = self._candidate(self.root, raw_path)
        if candidate.is_symlink():
            raise ToolFailure("SYMLINK_ESCAPE", "Writing through symlinks is denied.", category="security")

    def is_ignored_path(
        self,
        path: Path,
        *,
        include_hidden: bool = False,
        include_ignored: bool = False,
        git_ignored: set[str] | None = None,
    ) -> bool:
        resolved_path = path.resolve(strict=False)
        boundary = self._containing_root(resolved_path)
        if boundary is None:
            return True
        rel = resolved_path.relative_to(boundary)
        parts = rel.parts
        if not include_hidden and any(part.startswith(".") for part in parts if part not in {".", ""}):
            return True
        if not include_ignored and any(part in DEFAULT_EXCLUDED_NAMES for part in parts):
            return True
        if include_ignored:
            return False
        rel_text = rel.as_posix()
        if boundary == self.root and rel_text in (git_ignored if git_ignored is not None else self.git_ignored_paths([rel_text])):
            return True
        return False

    def is_safe_existing_path(self, path: Path) -> bool:
        try:
            resolved = path.resolve(strict=True)
        except FileNotFoundError:
            return False
        return self._is_allowed(resolved)

    def git_ignored_paths(self, rel_paths: list[str]) -> set[str]:
        if not rel_paths:
            return set()
        git = self.git_path
        if not git:
            return set()
        try:
            completed = subprocess.run(
                [git, "-C", str(self.root), "check-ignore", "--stdin", "-z"],
                input="\0".join(rel_paths) + "\0",
                text=True,
                encoding="utf-8",
                errors="replace",
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                timeout=2,
                **hidden_process_popen_kwargs(),
            )
        except (OSError, subprocess.SubprocessError):
            return set()
        if completed.returncode not in {0, 1}:
            return set()
        return {path for path in completed.stdout.split("\0") if path}


def configured_authorized_roots() -> list[Path]:
    raw = os.environ.get(f"{ENV_PREFIX}_AUTHORIZED_ROOTS", "").strip()
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = [item for item in raw.split(os.pathsep) if item]
    if not isinstance(parsed, list):
        return []
    return [Path(str(item)) for item in parsed if str(item).strip()]


class Runtime:
    def __init__(
        self,
        workspace: Path,
        *,
        enable_view_image: bool = True,
        permission_mode: str = "safe",
        shell_env_policy: ShellEnvPolicy | None = None,
        allow_network: bool = False,
        auth_token: str | None = None,
        oauth_config: OAuthConfig | None = None,
        project_context: ProjectContext | None = None,
        fake_readonly_annotations: bool = False,
        transport: str = "stdio",
    ) -> None:
        self.authorized_roots = configured_authorized_roots()
        self.workspace = Workspace(workspace, self.authorized_roots)
        self.tool_mode = os.environ.get(f"{ENV_PREFIX}_TOOL_MODE", "coding").strip().lower()
        if self.tool_mode not in TOOL_MODE_ALLOWLISTS:
            self.tool_mode = "coding"
        allowed_tools = TOOL_MODE_ALLOWLISTS[self.tool_mode]
        if self.tool_mode == "full":
            allowed_tools = frozenset(TOOL_REGISTRY)
        self.enable_view_image = enable_view_image
        self._exposed_tool_names = [
            name
            for name, spec in TOOL_REGISTRY.items()
            if (spec.gated_by is None or getattr(self, spec.gated_by)) and name in allowed_tools
        ]
        self._exposed_tool_name_set = frozenset(self._exposed_tool_names)
        if permission_mode not in PERMISSION_MODE_CHOICES:
            raise ToolFailure(
                "INVALID_ARGUMENT",
                f"Unknown permission mode: {permission_mode}",
                category="validation",
                details={"supported": list(PERMISSION_MODE_CHOICES)},
            )
        self.permission_mode = permission_mode
        self.capabilities = PERMISSION_MODE_CAPABILITIES[permission_mode]
        self.dangerously_skip_all_permissions = self.capabilities.skip_all_permissions
        # Faking annotations is only defensible where the caller has already
        # asserted the workspace is disposable, so bind it to that assertion
        # instead of letting it be set orthogonally.
        if fake_readonly_annotations and permission_mode != "dangerous":
            raise ToolFailure(
                "INVALID_ARGUMENT",
                "fake_readonly_annotations requires permission_mode=dangerous.",
                category="validation",
                details={"permission_mode": permission_mode},
            )
        self.fake_readonly_annotations = fake_readonly_annotations
        # Tool mode is fixed for the lifetime of this Runtime. Cache the complete
        # tools/list payload once so reconnect-heavy tunnel clients do not rebuild
        # the same schemas on every probe.
        self._tools_list_payload = {
            "tools": [
                tool_definition(name, fake_readonly=self.fake_readonly_annotations)
                for name in self._exposed_tool_names
            ]
        }
        self.shell_env_policy = shell_env_policy or ShellEnvPolicy()
        if self.shell_env_policy.inherit not in SHELL_ENV_INHERIT_CHOICES:
            raise ToolFailure(
                "INVALID_ARGUMENT",
                f"Unknown shell env inherit policy: {self.shell_env_policy.inherit}",
                category="validation",
                details={"supported": list(SHELL_ENV_INHERIT_CHOICES)},
            )
        self.allow_network = allow_network or self.capabilities.network
        self.auth_token = auth_token or None
        self.oauth_config = oauth_config
        self.server_instance_id = secrets.token_urlsafe(12)
        self.process_instance_id = PROCESS_INSTANCE_ID
        self._set_runtime_dir(runtime_dir_for_workspace(self.workspace.root, self.server_instance_id))
        self.fallback_runtime_dir = fallback_runtime_dir_for_workspace(self.workspace.root, self.server_instance_id)
        self.default_cwd = self.workspace.root
        self.sessions: dict[str, ExecSession] = {}
        self.output_sessions: dict[str, ExecSession] = {}
        self.sessions_lock = threading.Lock()
        self.session_principals: dict[str, str] = {}
        self.principal_active_counts: dict[str, int] = {}
        self.legacy_session_alias_uses = 0
        self.starting_sessions = 0
        self._closed = False
        self.http_session_id = secrets.token_urlsafe(24)
        self.protocol_version = PROTOCOL_VERSION
        self.patch_baselines: dict[str, str | None] = {}
        self.patch_lock = threading.Lock()
        self.patch_committer = AtomicPatchCommitter()
        # ProjectContext is frozen and derived only from the workspace tree, so
        # per-session HTTP runtimes reuse the server's copy instead of re-running
        # discovery (git ls-files / directory walk) on every connect.
        self.project_context: ProjectContext = (
            project_context if project_context is not None else load_project_context(self.workspace.root)
        )
        self.request_sessions: dict[str | int, str] = {}
        self.request_sessions_lock = threading.Lock()
        self.request_context = threading.local()
        # Background operations are process-scoped rather than HTTP-session-scoped.
        # A reconnect in the same MCP process must be able to poll the original
        # Event/result instead of falsely declaring it orphaned.
        self.background_operations = PROCESS_BACKGROUND_OPERATIONS
        self.background_operations_lock = PROCESS_BACKGROUND_OPERATIONS_LOCK
        self.initialized = False
        self.telemetry = SessionTelemetry(permission_mode=self.permission_mode, transport=transport)
        self.task_state = TaskStateStore(self.workspace.root)
        self.performance_trace = PerformanceTraceStore(self.workspace.root)
        self.orchestration_ledger = OrchestrationLedger(self.workspace.root)
        self.orphaned_background_operations = self.orchestration_ledger.mark_orphaned_background_operations(
            current_server_instance_id=self.process_instance_id
        )
        self.orphaned_idempotency_records = self.orchestration_ledger.mark_orphaned_idempotency(
            current_process_instance_id=self.process_instance_id
        )
        try:
            stale_run_seconds = int(os.environ.get(f"{ENV_PREFIX}_STALE_RUN_SECONDS", str(24 * 60 * 60)))
        except ValueError:
            stale_run_seconds = 24 * 60 * 60
        stale_run_seconds = max(60 * 60, min(stale_run_seconds, 30 * 24 * 60 * 60))
        self.stale_orchestration_runs = self.orchestration_ledger.reconcile_stale_runs(
            stale_after_seconds=stale_run_seconds
        )
        self.recovered_agent_lanes = 0
        for lane in self.orchestration_ledger.list_agent_lanes(lifecycle="active"):
            owner_process = str((lane.get("metadata") or {}).get("owner_process_instance_id") or "")
            if not owner_process or owner_process == self.process_instance_id:
                continue
            if self.orchestration_ledger.update_agent_lane(
                str(lane["lane_id"]),
                lifecycle="waiting",
                metadata={"recovery_reason": "mcp_runtime_restarted"},
            ):
                self.recovered_agent_lanes += 1
        self.orchestration_control = OrchestrationControl(self.workspace.root, self.orchestration_ledger)
        self.proof_ledger = ProofLedger(self.workspace.root, self.orchestration_ledger)
        self.orchestration_report = OrchestrationReport(self.workspace.root, self.orchestration_ledger)
        self.workspace_switch_lock = threading.RLock()
        self.workspace_generation = 1
        self._codex_bridge = CodexAppServerBridge(lambda: self.workspace.root)
        self._tool_handlers = {name: getattr(self, name) for name in TOOL_REGISTRY}

    def _set_runtime_dir(self, runtime_dir: Path) -> None:
        self.runtime_dir = runtime_dir
        self.home_dir = self.runtime_dir / "home"
        self.tmp_dir = self.runtime_dir / "tmp"
        self.cache_dir = self.runtime_dir / "cache"

    def close(self) -> None:
        self._codex_bridge.close()
        with self.sessions_lock:
            if self._closed:
                return
            self._closed = True
            sessions = list(self.sessions.values())
            self.sessions.clear()
            self.output_sessions.clear()
            self.session_principals.clear()
            self.principal_active_counts.clear()
        for session in sessions:
            session.refresh_status()
            if session.process.poll() is None:
                terminate_process_group(session.process, signal.SIGTERM)
            session.drain_readers()
        shutil.rmtree(self.runtime_dir, ignore_errors=True)
        self.telemetry.finish()

    def set_authorized_roots(self, roots: list[str]) -> dict[str, Any]:
        parsed = [Path(str(item)) for item in roots if str(item).strip()]
        with self.workspace_switch_lock:
            self.authorized_roots = parsed
            self.workspace = Workspace(self.workspace.root, self.authorized_roots)
            if not self.workspace._is_allowed(self.default_cwd.resolve(strict=False)):
                self.default_cwd = self.workspace.root
            self.workspace_generation += 1
            return {
                "ready": True,
                "workspace": str(self.workspace.root),
                "authorized_roots": [str(item) for item in self.workspace.authorized_roots if item != self.workspace.root],
                "generation": self.workspace_generation,
            }

    def switch_workspace(self, workspace: Path) -> dict[str, Any]:
        target = workspace.expanduser().resolve(strict=True)
        if not target.is_dir():
            raise ToolFailure("NOT_A_DIRECTORY", "Workspace must be an existing directory.", category="validation")
        with self.workspace_switch_lock:
            with self.sessions_lock:
                active = [session for session in self.sessions.values() if session.process.poll() is None]
                if active or self.starting_sessions:
                    raise ToolFailure(
                        "WORKSPACE_BUSY",
                        "Cannot switch workspace while commands are running.",
                        category="runtime",
                        retryable=True,
                        details={"active_commands": len(active), "starting_commands": self.starting_sessions},
                    )
            with self.background_operations_lock:
                active_background = [
                    item for item in self.background_operations.values()
                    if item.get("workspace") == str(self.workspace.root)
                    and not item["event"].is_set()
                ]
            if active_background:
                raise ToolFailure(
                    "WORKSPACE_BUSY",
                    "Cannot switch workspace while background workflows are running.",
                    category="runtime",
                    retryable=True,
                    details={"active_background_operations": len(active_background)},
                )
            if target == self.workspace.root:
                return {
                    "ready": True,
                    "workspace": str(self.workspace.root),
                    "generation": self.workspace_generation,
                    "changed": False,
                }
            old_runtime_dir = self.runtime_dir
            self._codex_bridge.close()
            self._invalidate_fast_cache()
            self._clear_context_bundle_cache()
            self.workspace = Workspace(target, self.authorized_roots)
            self.default_cwd = self.workspace.root
            self._set_runtime_dir(runtime_dir_for_workspace(self.workspace.root, self.server_instance_id))
            self.fallback_runtime_dir = fallback_runtime_dir_for_workspace(self.workspace.root, self.server_instance_id)
            self.project_context = load_project_context(self.workspace.root)
            self.task_state = TaskStateStore(self.workspace.root)
            self.performance_trace = PerformanceTraceStore(self.workspace.root)
            self.orchestration_ledger = OrchestrationLedger(self.workspace.root)
            self.orphaned_background_operations = self.orchestration_ledger.mark_orphaned_background_operations(
                current_server_instance_id=self.process_instance_id
            )
            self.orphaned_idempotency_records = self.orchestration_ledger.mark_orphaned_idempotency(
                current_process_instance_id=self.process_instance_id
            )
            self.recovered_agent_lanes = 0
            for lane in self.orchestration_ledger.list_agent_lanes(lifecycle="active"):
                owner_process = str((lane.get("metadata") or {}).get("owner_process_instance_id") or "")
                if not owner_process or owner_process == self.process_instance_id:
                    continue
                if self.orchestration_ledger.update_agent_lane(
                    str(lane["lane_id"]),
                    lifecycle="waiting",
                    metadata={"recovery_reason": "workspace_runtime_restarted"},
                ):
                    self.recovered_agent_lanes += 1
            self.orchestration_control = OrchestrationControl(self.workspace.root, self.orchestration_ledger)
            self.proof_ledger = ProofLedger(self.workspace.root, self.orchestration_ledger)
            self.orchestration_report = OrchestrationReport(self.workspace.root, self.orchestration_ledger)
            self._codex_bridge = CodexAppServerBridge(lambda: self.workspace.root)
            with self.patch_lock:
                self.patch_baselines.clear()
            self.workspace_generation += 1
            self._ensure_runtime_dirs()
            shutil.rmtree(old_runtime_dir, ignore_errors=True)
            self.preheat_workspace_async()
            return {
                "ready": True,
                "workspace": str(self.workspace.root),
                "generation": self.workspace_generation,
                "changed": True,
            }

    def _ensure_runtime_dirs(self) -> None:
        candidates = [self.runtime_dir]
        if self.fallback_runtime_dir is not None and self.fallback_runtime_dir not in candidates:
            candidates.append(self.fallback_runtime_dir)
        errors: list[str] = []
        for runtime_dir in candidates:
            self._set_runtime_dir(runtime_dir)
            try:
                for path in (
                    self.runtime_dir.parent,
                    self.runtime_dir,
                    self.home_dir,
                    self.tmp_dir,
                    self.cache_dir,
                ):
                    path.mkdir(parents=True, mode=0o700, exist_ok=True)
                    if os.name != "nt":
                        try:
                            path.chmod(0o700)
                        except OSError:
                            pass
                return
            except OSError as exc:
                errors.append(f"{runtime_dir}: {exc}")
        raise ToolFailure(
            "RUNTIME_DIR_UNWRITABLE",
            "Runtime directory could not be created outside the workspace.",
            category="runtime",
            details={"attempted": errors},
        )

    def command_home_dir(self) -> Path:
        return self.home_dir

    def command_tmp_dir(self) -> Path:
        return self.tmp_dir

    def global_tmp_write_policy(self) -> str:
        return self.capabilities.global_tmp_write

    def shell_expansion_policy(self) -> str:
        return "allowed" if self.capabilities.shell_expansion else "blocked"

    def inline_script_policy(self) -> str:
        return "allowed" if self.capabilities.inline_script else "blocked"

    def secret_env_filter_policy(self) -> str:
        return "enabled" if self.capabilities.secret_env_filter else "disabled"

    def landlock_enabled(self) -> bool:
        return self.capabilities.landlock

    def landlock_write_roots(self) -> list[Path]:
        return [self.runtime_dir]

    def is_allowed_command_tmp_path(self, candidate: str) -> bool:
        if self.capabilities.skip_all_permissions:
            return False
        try:
            resolved = Path(candidate).expanduser().resolve(strict=False)
        except OSError:
            return False
        return is_relative_to(resolved, self.runtime_dir)

    def initialize(self, client_info: dict[str, Any] | None = None) -> dict[str, Any]:
        self.telemetry.record_session_start(client_info, self.protocol_version)
        return {
            "protocolVersion": self.protocol_version,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {
                "name": SERVER_NAME,
                "title": SERVER_TITLE,
                "version": __version__,
            },
            "instructions": self.project_context.server_instructions(),
        }

    def list_tools(self) -> dict[str, Any]:
        return self._tools_list_payload

    def exposed_tool_names(self) -> list[str]:
        return list(self._exposed_tool_names)

    def auth_enabled(self) -> bool:
        return self.auth_token is not None or self.oauth_config is not None

    def oauth_enabled(self) -> bool:
        return self.oauth_config is not None

    def default_cwd_display(self) -> str:
        return normalize_rel_display(self.default_cwd, self.workspace.root)

    def resolve_existing(self, raw_path: str = ".") -> ResolvedPath:
        return self.workspace.resolve_existing_at(self.default_cwd, raw_path)

    def resolve_for_write(self, raw_path: str) -> ResolvedPath:
        return self.workspace.resolve_for_write_at(self.default_cwd, raw_path)

    def git_path_filter(self, raw_path: str) -> str:
        if raw_path == ".":
            return self.default_cwd_display()
        return self.resolve_for_write(raw_path).display

    def _exec_environment_summary(self) -> dict[str, Any]:
        return {
            "workspace": str(self.workspace.root),
            "permission_mode": self.permission_mode,
            "tool_mode": self.tool_mode,
            "network_allowed": self.allow_network,
            "runtime_dir": str(self.runtime_dir),
            "home": str(self.command_home_dir()),
            "tmpdir": str(self.command_tmp_dir()),
            "cache_dir": str(self.cache_dir),
        }

    def _landlock_enforced(self, landlock: dict[str, Any]) -> bool:
        return bool(landlock.get("available")) and self.landlock_enabled()

    def server_info_payload(self) -> dict[str, Any]:
        tools = self.exposed_tool_names()
        landlock = landlock_status_payload()
        landlock["enabled"] = self._landlock_enforced(landlock)
        return {
            "server": SERVER_NAME,
            "title": SERVER_TITLE,
            "version": __version__,
            "protocol_version": self.protocol_version,
            **self._exec_environment_summary(),
            "default_cwd": self.default_cwd_display(),
            "authorized_roots": [str(item) for item in self.workspace.authorized_roots if item != self.workspace.root],
            "auth_enabled": self.auth_enabled(),
            "dangerously_skip_all_permissions": self.dangerously_skip_all_permissions,
            "annotation_override": "fake_readonly" if self.fake_readonly_annotations else None,
            "landlock": landlock,
            "exec_policy": {
                "shell_expansion": self.shell_expansion_policy(),
                "inline_script": self.inline_script_policy(),
                "global_tmp_write": self.global_tmp_write_policy(),
                "secret_env_filter": self.secret_env_filter_policy(),
            },
            "shell_env_inherit": self.shell_env_policy.inherit,
            "shell_env_include_only": list(self.shell_env_policy.include_only),
            "shell_env_exclude": list(self.shell_env_policy.exclude),
            "endpoint_path": MCP_ENDPOINT_PATH,
            "project_context": {
                "root_instruction_files": [item.path for item in self.project_context.root_files],
                "nested_instruction_files": list(self.project_context.nested_files),
                "warnings": list(self.project_context.warnings),
            },
            "tools": tools,
            "tool_count": len(tools),
        }

    def _background_operation_snapshot(self, operation: dict[str, Any], *, include_result: bool = False) -> dict[str, Any]:
        event = operation["event"]
        finished = event.is_set()
        payload: dict[str, Any] = {
            "operation_id": operation["operation_id"],
            "tool": operation["tool"],
            "workspace": operation.get("workspace"),
            "status": "completed" if finished else "running",
            "elapsed_seconds": max(0, int(time.monotonic() - operation["started_monotonic"])),
            "requires_progress_report": not finished,
        }
        budget = operation.get("budget")
        if isinstance(budget, BudgetDeadline):
            payload["budget"] = {
                "max_runtime_seconds": budget.max_runtime_seconds,
                "remaining_seconds": budget.remaining_seconds(),
                "exceeded": budget.exceeded,
            }
        if finished and operation.get("error"):
            payload["status"] = "failed"
            payload["error"] = operation["error"]
        if include_result and finished and operation.get("result") is not None:
            payload["result"] = operation["result"]
        return payload

    def _start_background_tool(
        self,
        name: str,
        arguments: dict[str, Any],
        *,
        request_id: str | int | None,
    ) -> tuple[dict[str, Any], threading.Event]:
        operation_id = secrets.token_urlsafe(12)
        done = threading.Event()
        try:
            timeout_seconds = min(int(arguments.get("timeout_seconds", 600)), 3600)
        except (TypeError, ValueError):
            timeout_seconds = 600
        timeout_seconds = max(1, timeout_seconds)
        budget = BudgetDeadline(max_runtime_seconds=timeout_seconds)
        operation: dict[str, Any] = {
            "operation_id": operation_id,
            "tool": name,
            "workspace": str(self.workspace.root),
            "started_monotonic": time.monotonic(),
            "started_at": datetime.now(timezone.utc).isoformat(),
            "event": done,
            "result": None,
            "error": None,
            "budget": budget,
            "finalized": False,
        }
        current_task = self.task_state.get()
        projection = current_task.get("orchestration") if isinstance(current_task.get("orchestration"), dict) else {}
        self.orchestration_ledger.start_background_operation(
            operation_id=operation_id,
            server_instance_id=self.process_instance_id,
            tool=name,
            task_id=str(current_task.get("task_id") or ""),
            run_id=str(projection.get("run_id") or ""),
            wave_id=str(projection.get("wave_id") or ""),
            summary={
                "phase": str(arguments.get("phase") or ""),
                "objective": str(arguments.get("objective") or "")[:1_000],
                "request_id": str(request_id or ""),
            },
        )

        def worker() -> None:
            try:
                operation["result"] = self._call_tool_sync(name, arguments, request_id=request_id)
            except Exception as exc:  # noqa: BLE001 - background errors must become inspectable state
                operation["error"] = {
                    "code": "BACKGROUND_OPERATION_FAILED",
                    "message": str(exc),
                    "category": "runtime",
                    "retryable": False,
                }
            finally:
                if not operation.get("finalized"):
                    operation["finalized"] = True
                    result = operation.get("result")
                    result_status = ""
                    if isinstance(result, dict):
                        structured = result.get("structuredContent")
                        if isinstance(structured, dict):
                            result_status = str(
                                structured.get("status")
                                or structured.get("phase")
                                or structured.get("workflow")
                                or ""
                            )[:100]
                    self.orchestration_ledger.finish_background_operation(
                        operation_id,
                        status="failed" if operation.get("error") else "completed",
                        summary={
                            "result_available_in_memory": result is not None,
                            "result_status": result_status,
                            "error": operation.get("error"),
                        },
                    )
                    done.set()

        def watchdog() -> None:
            while not done.is_set():
                try:
                    budget.check()
                except ToolFailure as exc:
                    if not operation.get("finalized"):
                        operation["finalized"] = True
                        operation["error"] = {
                            "code": exc.code,
                            "message": exc.message,
                            "category": exc.category,
                            "retryable": False,
                        }
                        self.orchestration_ledger.finish_background_operation(
                            operation_id,
                            status="timed_out",
                            summary={"error": operation["error"], "budget": exc.details},
                        )
                        done.set()
                    return
                done.wait(BACKGROUND_BUDGET_POLL_SECONDS)

        with self.background_operations_lock:
            finished_ids = [
                key for key, item in self.background_operations.items()
                if item["event"].is_set()
            ]
            while len(self.background_operations) >= MAX_BACKGROUND_OPERATIONS and finished_ids:
                self.background_operations.pop(finished_ids.pop(0), None)
            self.background_operations[operation_id] = operation
        threading.Thread(target=worker, name=f"mcp-bg-{name}-{operation_id[:6]}", daemon=True).start()
        threading.Thread(target=watchdog, name=f"mcp-budget-{operation_id[:6]}", daemon=True).start()
        return operation, done

    def call_tool(
        self,
        name: str,
        arguments: dict[str, Any] | None,
        *,
        request_id: str | int | None = None,
    ) -> dict[str, Any]:
        args = arguments or {}
        try:
            result = self._call_tool_dispatch(name, args, request_id=request_id)
        except Exception as exc:
            self._idempotency_finish(name, args, exc=exc)
            raise
        failure = None
        structured = result.get("structuredContent") if isinstance(result.get("structuredContent"), dict) else {}
        if result.get("isError") or structured.get("ok") is False:
            failure = structured.get("error") if isinstance(structured.get("error"), dict) else {}
        if not structured.get("deduplicated"):
            self._idempotency_finish(name, args, result=result, failure=failure)
        return result

    def _idempotency_claim_or_replay(self, name: str, args: dict[str, Any]) -> dict[str, Any] | None:
        if name == "agent_workflow" or name not in TOOL_REGISTRY:
            return None
        idempotency_key = str(args.get("idempotency_key", "") or "").strip()
        if not idempotency_key:
            return None
        if len(idempotency_key) > 128:
            raise ToolFailure(
                "INVALID_ARGUMENT",
                "idempotency_key must be at most 128 characters.",
                category="validation",
            )
        request_hash = self._request_hash(args)
        claim = self.orchestration_ledger.claim_idempotency(
            idempotency_key=idempotency_key,
            operation=name,
            request_hash=request_hash,
            process_instance_id=self.process_instance_id,
        )
        if claim.get("claimed"):
            return None
        reason = str(claim.get("reason") or "")
        record = claim.get("record") if isinstance(claim.get("record"), dict) else {}
        if reason == "conflict":
            raise ToolFailure(
                "IDEMPOTENCY_CONFLICT",
                f"The idempotency_key was already used for a different {name} request.",
                category="validation",
                details={"idempotency_key": idempotency_key, "status": record.get("status")},
            )
        if reason == "completed":
            stored = record.get("summary", {}).get("tool_result")
            if isinstance(stored, dict):
                structured = stored.get("structuredContent")
                if not isinstance(structured, dict):
                    structured = {}
                payload = {
                    **structured,
                    "deduplicated": True,
                    "durable_idempotency": True,
                    "idempotency": {
                        key: record.get(key)
                        for key in ("idempotency_key", "operation", "status", "run_id", "wave_id", "finished_at")
                        if key in record
                    },
                }
                # The orchestration ledger intentionally sanitizes sensitive
                # payload keys before persistence. That includes the MCP
                # envelope's top-level ``content`` field, so returning the
                # stored envelope verbatim would violate MCP's required
                # ``content: list`` result shape. Rebuild the envelope from
                # the durable structured payload instead; redacted fields
                # stay redacted while transport shape remains valid.
                return make_tool_result(
                    name,
                    payload,
                    is_error=bool(stored.get("isError")),
                )
            raise ToolFailure(
                "IDEMPOTENT_REQUEST_FAILED",
                "This idempotent request already completed but its result was too large to replay verbatim. Treat it as done and do not repeat the mutation.",
                category="runtime",
                details={"idempotency_key": idempotency_key, "record": record},
            )
        if reason == "failed":
            raise ToolFailure(
                "IDEMPOTENT_REQUEST_FAILED",
                "This exact idempotent request already reached a known terminal failure; do not repeat it unchanged.",
                category="runtime",
                details={"idempotency_key": idempotency_key, "summary": record.get("summary")},
            )
        if reason == "unknown":
            raise ToolFailure(
                "IDEMPOTENCY_OUTCOME_UNKNOWN",
                "A previous process may have started this idempotent request but its outcome is unknown. Reconcile evidence before any replay.",
                category="runtime",
                details={"idempotency_key": idempotency_key, "summary": record.get("summary")},
            )
        raise ToolFailure(
            "IDEMPOTENCY_IN_PROGRESS",
            "This idempotent request is already in progress; observe the existing task instead of starting another copy.",
            category="runtime",
            retryable=True,
            details={"idempotency_key": idempotency_key, "run_id": record.get("run_id"), "wave_id": record.get("wave_id")},
        )

    def _idempotency_finish(
        self,
        name: str,
        args: dict[str, Any],
        *,
        result: dict[str, Any] | None = None,
        failure: dict[str, Any] | None = None,
        exc: Exception | None = None,
    ) -> None:
        if name == "agent_workflow" or name not in TOOL_REGISTRY:
            return
        idempotency_key = str(args.get("idempotency_key", "") or "").strip()
        if not idempotency_key:
            return
        request_hash = self._request_hash(args)
        if failure is not None:
            retryable = bool(failure.get("retryable", False))
            status = "failed" if not retryable else "unknown"
            self.orchestration_ledger.finish_idempotency(
                idempotency_key,
                request_hash=request_hash,
                status=status,
                summary={
                    "error_code": str(failure.get("code") or "TOOL_ERROR"),
                    "category": str(failure.get("category") or "runtime"),
                    "outcome_unknown": status == "unknown",
                },
            )
            return
        if exc is not None:
            if isinstance(exc, ToolFailure):
                status = "failed" if not exc.retryable else "unknown"
                error_code = str(exc.code)
                category = str(exc.category)
            else:
                status = "failed"
                error_code = str(getattr(exc, "code", type(exc).__name__))
                category = str(getattr(exc, "category", "protocol"))
            self.orchestration_ledger.finish_idempotency(
                idempotency_key,
                request_hash=request_hash,
                status=status,
                summary={
                    "error_code": error_code,
                    "category": category,
                    "outcome_unknown": status == "unknown",
                },
            )
            return
        if result is None:
            return
        serialized = json.dumps(
            result, ensure_ascii=False, separators=(",", ":"), default=str
        ).encode("utf-8", errors="replace")
        if len(serialized) <= IDEMPOTENCY_RESULT_MAX_BYTES:
            summary = {"tool_result": result, "result_bytes": len(serialized)}
        else:
            summary = {"result_bytes": len(serialized), "result_too_large_for_replay": True}
        self.orchestration_ledger.finish_idempotency(
            idempotency_key,
            request_hash=request_hash,
            status="completed",
            summary=summary,
        )

    def _call_tool_dispatch(
        self,
        name: str,
        args: dict[str, Any],
        *,
        request_id: str | int | None = None,
    ) -> dict[str, Any]:
        should_handoff = name == "agent_workflow" and str(args.get("phase", "prepare")).lower() in {"execute", "run"}
        if not should_handoff:
            return self._call_tool_sync(name, args, request_id=request_id)
        operation, done = self._start_background_tool(name, args, request_id=request_id)
        if done.wait(LONG_TOOL_HANDOFF_SECONDS):
            if operation.get("error"):
                raise ToolFailure(
                    "BACKGROUND_OPERATION_FAILED",
                    str(operation["error"].get("message", "Background operation failed")),
                    category="runtime",
                )
            return operation["result"]
        snapshot = self._background_operation_snapshot(operation)
        return make_tool_result(name, {
            "ok": True,
            "status": "running",
            "requires_progress_report": True,
            "message": "The workflow is still running in the background. Report concrete progress to the user before polling it again.",
            "background_operation": snapshot,
            "task": self.task_state.get(),
        }, is_error=False)

    def _invoke_with_read_retry(
        self,
        name: str,
        handler: Callable[[dict[str, Any]], dict[str, Any]],
        args: dict[str, Any],
        spec: ToolSpec,
    ) -> dict[str, Any]:
        policy = READ_RETRY_POLICY
        failure_count = 0
        while True:
            try:
                return handler(args)
            except ToolFailure as exc:
                if spec.read_only is not True or not exc.retryable or failure_count >= policy.max_attempts - 1:
                    raise
                failure_count += 1
                delay = policy.delay_for(failure_count)
                if delay > 0:
                    time.sleep(delay)

    def _call_tool_sync(
        self,
        name: str,
        arguments: dict[str, Any] | None,
        *,
        request_id: str | int | None = None,
    ) -> dict[str, Any]:
        started_at = time.monotonic()
        args = arguments or {}
        compatibility_call = self.tool_mode == "smart" and name in SMART_COMPAT_TOOL_NAMES
        handler = self._tool_handlers.get(name) if name in self._exposed_tool_name_set or compatibility_call else None
        if handler is None:
            raise JsonRpcError(-32602, f"Unknown tool: {name}", {"reason": "unknown_tool"})
        spec = TOOL_REGISTRY[name]
        validate_arguments(name, args)
        try:
            replay = self._idempotency_claim_or_replay(name, args)
            if replay is not None:
                return replay
            current_task = self.task_state.get()
            control_tools = {"task_control", "task_state_get", "task_state_update", "task_state_pause", "task_state_resume", "task_state_clear", "task_history_list"}
            if name not in control_tools and spec.read_only is not True:
                if str(current_task.get("status", "")) == "paused":
                    raise ToolFailure(
                        "TASK_PAUSED",
                        "The current task is paused. Resume it before running mutating tools.",
                        category="runtime",
                        retryable=True,
                    )
                if str(current_task.get("status", "")) == "stopped":
                    raise ToolFailure(
                        "TASK_STOPPED",
                        "The current task was stopped. Start or resume a task before continuing.",
                        category="runtime",
                        retryable=True,
                    )
                objective = {
                    "agent_workflow": str(args.get("objective", "")).strip() or "Complete an end-to-end workspace workflow",
                    "apply_changes_and_verify": str(args.get("objective", "")).strip() or "Apply and verify workspace changes",
                    "apply_patch": "Modify workspace files",
                    "exec_command": "Run a workspace command",
                    "verify_build": "Build and verify the workspace",
                    "document_create": "Create a Word document in the workspace",
                    "document_convert": "Convert a document into the workspace",
                }.get(name, "Complete a workspace task")
                self.task_state.ensure_started(objective, current_step=TOOL_REGISTRY[name].title)
            self.request_context.request_id = request_id
            try:
                payload = self._invoke_with_read_retry(name, handler, args, spec)
            finally:
                if request_id is not None:
                    with self.request_sessions_lock:
                        self.request_sessions.pop(request_id, None)
                self.request_context.request_id = None
            payload.setdefault("ok", True)
            task_read_only = name == "task_control" and str(args.get("action", "get")).lower() in {"get", "history", "operation"}
            if spec.read_only is not True and name not in {"agent_workflow", "document_workflow"} and not task_read_only and not payload.get("deduplicated"):
                self._invalidate_fast_cache()
            self._record_task_tool_result(name, args, payload)
            self.emit_tool_trace(name, args, payload, started_at)
            content = spec.content_builder(payload) if spec.content_builder else None
            return make_tool_result(name, payload, is_error=payload.get("ok") is False, content=content)
        except ToolFailure as exc:
            payload = {
                "ok": False,
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "category": exc.category,
                    "retryable": exc.retryable,
                    "details": exc.details,
                },
            }
            if spec.error_status:
                payload["status"] = spec.error_status
            diagnostics = permission_failure_diagnostics(exc)
            if diagnostics:
                payload["diagnostics"] = diagnostics
            if exc.code == "PERMISSION_REQUIRED":
                permission = exc.details.get("permission")
                payload["permission_request"] = {
                    "tool_name": name,
                    "permission": permission or "unknown",
                    "status": "required",
                    "retryable": True,
                }
            if exc.code == "ELICITATION_UNSUPPORTED":
                payload["status"] = "unsupported"
            self._record_task_tool_result(name, args, payload)
            self.emit_tool_trace(name, args, payload, started_at)
            return make_tool_result(name, payload, is_error=True)
        except Exception as exc:  # noqa: BLE001 - tool failures must stay structured
            payload = {
                "ok": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": str(exc),
                    "category": "internal",
                    "retryable": False,
                    "details": {},
                },
            }
            if spec.error_status:
                payload["status"] = spec.error_status
            self._record_task_tool_result(name, args, payload)
            self.emit_tool_trace(name, args, payload, started_at)
            return make_tool_result(name, payload, is_error=True)

    def _record_task_tool_result(self, name: str, args: dict[str, Any], payload: dict[str, Any]) -> None:
        try:
            self.task_state.record_tool_result(name, args, payload)
        except Exception:
            # State persistence must never turn a successful coding operation into a failed tool call.
            pass

    def server_info(self, args: dict[str, Any]) -> dict[str, Any]:
        return self.server_info_payload()

    def _workspace_cache_namespace(self) -> str:
        return str(self.workspace.root).casefold()

    def _cache_generation(self) -> int:
        with _FAST_TOOL_CACHE_LOCK:
            return _WORKSPACE_CACHE_GENERATION.get(self._workspace_cache_namespace(), 0)

    def _fast_cache_key(self, tool: str, args: dict[str, Any], *, file_paths: list[Path] | None = None) -> str:
        fingerprints: list[tuple[str, int, int]] = []
        for path in file_paths or []:
            try:
                stat_result = path.stat()
                fingerprints.append((str(path), stat_result.st_size, stat_result.st_mtime_ns))
            except OSError:
                fingerprints.append((str(path), -1, -1))
        raw = json.dumps(
            {"workspace": str(self.workspace.root), "tool": tool, "args": args, "files": fingerprints},
            ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str,
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _fast_cache_get(self, key: str, ttl_seconds: int) -> dict[str, Any] | None:
        now = time.monotonic()
        generation = self._cache_generation()
        with _FAST_TOOL_CACHE_LOCK:
            cached = _FAST_TOOL_CACHE.get(key)
        if not cached or cached[1] != generation or now - cached[0] > ttl_seconds:
            return None
        payload = copy.deepcopy(cached[2])
        payload["cache"] = {"hit": True, "age_ms": int((now - cached[0]) * 1000)}
        payload["cache_hit"] = True
        return payload

    def _fast_cache_put(self, key: str, payload: dict[str, Any]) -> None:
        generation = self._cache_generation()
        with _FAST_TOOL_CACHE_LOCK:
            if len(_FAST_TOOL_CACHE) >= 128:
                oldest = min(_FAST_TOOL_CACHE, key=lambda item: _FAST_TOOL_CACHE[item][0])
                _FAST_TOOL_CACHE.pop(oldest, None)
            _FAST_TOOL_CACHE[key] = (time.monotonic(), generation, copy.deepcopy(payload))

    def _invalidate_fast_cache(self) -> None:
        namespace = self._workspace_cache_namespace()
        with _FAST_TOOL_CACHE_LOCK:
            _WORKSPACE_CACHE_GENERATION[namespace] = _WORKSPACE_CACHE_GENERATION.get(namespace, 0) + 1

    def preheat_workspace_async(self) -> None:
        namespace = self._workspace_cache_namespace()
        with _FAST_TOOL_CACHE_LOCK:
            if namespace in _WORKSPACE_PREHEAT_STARTED:
                return
            _WORKSPACE_PREHEAT_STARTED.add(namespace)

        def preheat() -> None:
            started = time.monotonic()
            try:
                payload = self.workspace_context({"path": ".", "max_entries": 40, "detail": "compact"})
                payload["preheated"] = True
                ok = True
            except Exception:
                ok = False
            finished = time.monotonic()
            try:
                self.performance_trace.record(
                    tool="workspace_preheat", started_monotonic=started, finished_monotonic=finished, ok=ok,
                    orchestration=self.task_state.get().get("orchestration", {}),
                )
            except Exception:
                pass

        threading.Thread(target=preheat, name="coding-tools-preheat", daemon=True).start()

    def _orchestration_workspace_identity(self, path_value: object = ".") -> dict[str, Any]:
        try:
            status = self.git_status({"path": str(path_value or "."), "max_entries": 2000})
        except (ToolFailure, OSError, ValueError):
            status = {"is_repo": False, "head": "", "branch": "", "entries": []}
        raw_entries = status.get("entries") if isinstance(status.get("entries"), list) else []
        entries = [
            {
                "path": str(item.get("path") or "").replace("\\", "/"),
                "index_status": str(item.get("index_status") or ""),
                "worktree_status": str(item.get("worktree_status") or ""),
            }
            for item in raw_entries
            if isinstance(item, dict)
            and str(item.get("path") or "").strip()
            and not str(item.get("path") or "").replace("\\", "/").startswith(".coding-tools/")
        ]
        dirty_paths = [item["path"] for item in entries]
        head = str(status.get("head") or "")
        worktree_fp = fingerprint_paths(
            self.workspace.root,
            dirty_paths,
            extra={"head": head, "branch": status.get("branch"), "entries": entries},
        )
        return {
            "is_repo": bool(status.get("is_repo")),
            "base_head": head,
            "branch": str(status.get("branch") or ""),
            "worktree_fp": worktree_fp,
            "dirty_paths": dirty_paths,
        }

    @staticmethod
    def _orchestration_mode_for_route(route: object) -> str:
        selected = str(route or "auto").lower()
        if selected == "deterministic":
            return "mcp_only"
        if selected in {"mini", "luna"}:
            return "bounded_candidate"
        if selected == "sol_ultra":
            return "deep_single_lane"
        if selected in {"terra", "sol_xhigh", "sol_max"}:
            return "deep_single_lane"
        return "auto"

    def _project_orchestration(self, ctx: RunContext, *, event: str = "orchestration_projected") -> None:
        try:
            self.task_state.set_orchestration_projection(ctx.projection(), event=event)
        except (OSError, ValueError):
            pass

    def _orchestration_result(self, ctx: RunContext | None, *, write_reports: bool = True) -> dict[str, Any] | None:
        if ctx is None:
            return None
        reports: dict[str, Any] = {}
        if write_reports:
            try:
                reports = self.orchestration_report.write_reports(ctx.run_id)
            except (OSError, ValueError, KeyError) as exc:
                reports = {"error": str(exc)[:500]}
        return {
            **ctx.projection(),
            "integrity": self.orchestration_ledger.verify_chain(ctx.run_id),
            "reports": reports,
            "final_acceptance_required": ctx.state == "ACCEPTING",
        }

    def codex_bridge(self, args: dict[str, Any]) -> dict[str, Any]:
        try:
            return self._codex_bridge.handle(args)
        except CodexBridgeError as exc:
            raise ToolFailure(
                exc.code,
                str(exc),
                category="runtime",
                retryable=exc.retryable,
                details=exc.details,
            ) from exc

    @staticmethod
    def _agent_review_proof(execution: dict[str, Any], verification: str) -> tuple[dict[str, Any], bool]:
        check_rows: list[dict[str, Any]] = []
        raw_checks = execution.get("check_results", [])
        for item in raw_checks if isinstance(raw_checks, list) else []:
            if not isinstance(item, dict):
                continue
            check_rows.append({
                "exit_code": item.get("exit_code"),
                "timed_out": bool(item.get("timed_out", False)),
                "summary": str(item.get("summary") or "")[:240],
            })
        report = execution.get("build_report") if isinstance(execution.get("build_report"), dict) else {}
        test_result = report.get("test_result") if isinstance(report.get("test_result"), dict) else {}
        build_result = report.get("build_result") if isinstance(report.get("build_result"), dict) else {}
        proof = {
            "verification": verification,
            "checks": check_rows,
            "build": {
                "overall_status": report.get("overall_status"),
                "test_status": test_result.get("status"),
                "build_status": build_result.get("status"),
                "artifact_count": len(report.get("artifacts", [])) if isinstance(report.get("artifacts"), list) else 0,
            },
        }
        strong_oracle = False
        if verification == "tests":
            strong_oracle = test_result.get("status") == "passed"
        elif verification == "build":
            strong_oracle = build_result.get("status") == "passed"
        elif verification == "all":
            strong_oracle = test_result.get("status") == "passed" and build_result.get("status") == "passed"
        return proof, strong_oracle

    @staticmethod

    def _normalize_candidate_path(value: object) -> str:

        path = str(value or "").strip().replace("\\", "/")

        while path.startswith("./"):

            path = path[2:]

        parts = path.split("/") if path else []

        if (

            not path

            or path.startswith("/")

            or re.match(r"^[A-Za-z]:", path)

            or any(part in {"", ".", ".."} for part in parts)

        ):

            raise ToolFailure("INVALID_CANDIDATE_PATH", f"Invalid candidate path: {value}", category="validation")

        return "/".join(parts)



    def _select_agent_execution_route(

        self,

        *,

        workflow: str,

        prepared: dict[str, Any] | None,

        requested: str,

        allow_high_cost: bool,
        strong_oracle: bool = False,

    ) -> dict[str, Any]:

        requested_name = str(requested or "auto").strip().lower() or "auto"

        supported = {"auto", "deterministic", *AGENT_EXECUTION_ROUTES}

        if requested_name not in supported:

            raise ToolFailure(

                "INVALID_EXECUTION_ROUTE",

                f"Unknown execution route: {requested_name}",

                category="validation",

                details={"supported": sorted(supported)},

            )

        if requested_name in {"sol_max", "sol_ultra"} and not allow_high_cost:

            raise ToolFailure(

                "HIGH_COST_ACK_REQUIRED",

                f"execution_route={requested_name} requires allow_high_cost=true.",

                category="validation",

                details={"route": requested_name},

            )

        if requested_name != "auto":

            selected = requested_name

            reason = "explicit_request"

        else:

            selected_paths = list((prepared or {}).get("selected_paths") or [])

            total_bytes = int((prepared or {}).get("total_content_bytes") or 0)

            if workflow in {"diagnose", "document", "resume", "build_release", "greenfield"}:

                selected = "deterministic"

                reason = "workflow_prefers_local_tools"

            elif strong_oracle and workflow in {"bugfix", "test_failure"} and 0 < len(selected_paths) <= 2 and total_bytes <= 24_000:

                selected = "mini"

                reason = "localized_strong_oracle_candidate"

            elif 0 < len(selected_paths) <= 4 and total_bytes <= 60_000:

                selected = "luna"

                reason = "harder_bounded_leaf"

            else:

                selected = "sol_xhigh"

                reason = "deep_or_broad_context"

        if selected == "deterministic":

            return {

                "requested": requested_name,

                "selected": selected,

                "reason": reason,

                "profile": None,

                "model": None,

                "effort": None,

                "high_cost": False,

            }

        spec = AGENT_EXECUTION_ROUTES[selected]

        return {

            "requested": requested_name,

            "selected": selected,

            "reason": reason,

            **spec,

        }



    def _agent_candidate_packet(

        self,

        *,

        workflow: str,

        objective: str,

        prepared: dict[str, Any],

        proof: dict[str, Any],

        selected_route: str,

    ) -> tuple[dict[str, Any], list[str]]:

        allowed_paths = []

        for raw_path in list(prepared.get("selected_paths") or [])[:20]:

            try:

                path = self._normalize_candidate_path(raw_path)

            except ToolFailure:

                continue

            if path not in allowed_paths:

                allowed_paths.append(path)

        files: list[dict[str, str]] = []

        remaining = AGENT_CANDIDATE_PACKET_MAX_CHARS

        for item in list(prepared.get("files") or []):

            if not isinstance(item, dict):

                continue

            try:

                path = self._normalize_candidate_path(item.get("path"))

            except ToolFailure:

                continue

            if path not in allowed_paths:

                continue

            content = str(item.get("content") or "")

            if not content or remaining <= 0:

                continue

            take = min(len(content), 5_000, remaining)

            files.append({"path": path, "content": content[:take]})

            remaining -= take

        searches: list[dict[str, Any]] = []

        for result in list(prepared.get("searches") or [])[:6]:

            if not isinstance(result, dict):

                continue

            matches = []

            for match in list(result.get("matches") or [])[:3]:

                if not isinstance(match, dict):

                    continue

                matches.append({

                    "path": match.get("path"),

                    "line": match.get("line"),

                    "preview": str(match.get("preview") or match.get("text") or "")[:360],

                })

            searches.append({"query": result.get("query"), "matches": matches})

        return ({

            "objective": objective,

            "workflow": workflow,

            "selected_route": selected_route,

            "allowed_paths": allowed_paths,

            "proof": proof,

            "searches": searches,

            "files": files,

            "contract": (

                "Return exact replacements only within allowed_paths. old must be a non-empty exact contiguous substring. "

                "Do not modify tests or unrelated files unless they are explicitly in allowed_paths. If another path or unsettled "

                "semantic decision is required, return status=blocked."

            ),

        }, allowed_paths)



    def _candidate_payload_to_patches(

        self,

        payload: dict[str, Any],

        *,

        allowed_paths: list[str],

    ) -> tuple[list[str], list[dict[str, str]]]:

        allowed = set(allowed_paths)

        replacements = list(payload.get("replacements") or [])

        new_files = list(payload.get("new_files") or [])

        if not replacements and not new_files:

            raise ToolFailure("EMPTY_CANDIDATE", "Candidate returned no changes.", category="validation")

        patches: list[str] = []

        normalized_new_files: list[dict[str, str]] = []

        for item in replacements:

            if not isinstance(item, dict):

                raise ToolFailure("INVALID_CANDIDATE", "Replacement must be an object.", category="validation")

            path = self._normalize_candidate_path(item.get("path"))

            if path not in allowed:

                raise ToolFailure(

                    "CANDIDATE_SCOPE_VIOLATION",

                    f"Candidate tried to modify an unapproved path: {path}",

                    category="validation",

                    details={"allowed_paths": sorted(allowed)},

                )

            old = str(item.get("old") or "")

            new = str(item.get("new") or "")

            if not old:

                raise ToolFailure("INVALID_CANDIDATE", f"Replacement old text is empty for {path}.", category="validation")

            target = (self.workspace.root / Path(*path.split("/"))).resolve(strict=False)

            root = self.workspace.root.resolve(strict=False)

            if not target.is_relative_to(root) or not target.is_file():

                raise ToolFailure("CANDIDATE_TARGET_MISSING", f"Candidate target is not a workspace file: {path}", category="validation")

            try:

                current = target.read_text(encoding="utf-8")

            except (OSError, UnicodeError) as exc:

                raise ToolFailure("CANDIDATE_TARGET_UNREADABLE", str(exc), category="filesystem") from exc

            target_newline = "\r\n" if "\r\n" in current else "\n"
            normalized_old = old.replace("\r\n", "\n").replace("\r", "\n").replace("\n", target_newline)
            normalized_new = new.replace("\r\n", "\n").replace("\r", "\n").replace("\n", target_newline)
            count = current.count(normalized_old)
            if count == 1:
                old, new = normalized_old, normalized_new

            if count != 1:

                raise ToolFailure(

                    "CANDIDATE_NOT_UNIQUE",

                    f"Candidate old text must match exactly once in {path}; matched {count} times.",

                    category="validation",

                    details={"path": path, "matches": count},

                )

            sections = ["*** Begin Patch", f"*** Update File: {path}", "@@"]

            sections.extend(f"-{line}" for line in old.splitlines())

            sections.extend(f"+{line}" for line in new.splitlines())

            sections.append("*** End Patch")

            patches.append("\n".join(sections))

        for item in new_files:

            if not isinstance(item, dict):

                raise ToolFailure("INVALID_CANDIDATE", "new_files entries must be objects.", category="validation")

            path = self._normalize_candidate_path(item.get("path"))

            if path not in allowed:

                raise ToolFailure(

                    "CANDIDATE_SCOPE_VIOLATION",

                    f"Candidate tried to create an unapproved path: {path}",

                    category="validation",

                    details={"allowed_paths": sorted(allowed)},

                )

            target = (self.workspace.root / Path(*path.split("/"))).resolve(strict=False)

            root = self.workspace.root.resolve(strict=False)

            if not target.is_relative_to(root) or target.exists():

                raise ToolFailure("CANDIDATE_NEW_FILE_INVALID", f"Candidate new file is invalid or already exists: {path}", category="validation")

            normalized_new_files.append({"path": path, "content": str(item.get("content") or "")})

        new_file_patch = self._new_files_patch(normalized_new_files)

        if new_file_patch:

            patches.append(new_file_patch)

        return patches, normalized_new_files



    def _generate_agent_candidate(

        self,

        *,

        workflow: str,

        objective: str,

        prepared: dict[str, Any],

        requested_route: str,

        allow_high_cost: bool,

        proof: dict[str, Any],

        routing: dict[str, Any] | None = None,

        orchestration_ctx: RunContext | None = None,

    ) -> dict[str, Any]:

        preflight_test = proof.get("preflight_test") if isinstance(proof.get("preflight_test"), dict) else None
        preflight_build = proof.get("preflight_build") if isinstance(proof.get("preflight_build"), dict) else None
        strong_oracle = any(
            item is not None and item.get("exit_code") not in {None, 0}
            for item in (preflight_test, preflight_build)
        )
        if routing is None:
            routing = self._select_agent_execution_route(

                workflow=workflow,

                prepared=prepared,

                requested=requested_route,

                allow_high_cost=allow_high_cost,
                strong_oracle=strong_oracle,

            )
        else:
            routing = dict(routing)

        if routing["selected"] == "deterministic":

            return {"status": "deterministic", "routing": routing, "patches": []}

        packet, allowed_paths = self._agent_candidate_packet(

            workflow=workflow,

            objective=objective,

            prepared=prepared,

            proof=proof,

            selected_route=str(routing["selected"]),

        )

        if not allowed_paths:

            return {"status": "blocked", "reason": "candidate_scope_missing", "routing": routing, "patches": []}

        prompt = (

            "Bounded implementation candidate packet:\n"

            + json.dumps(packet, ensure_ascii=False, separators=(",", ":"))

            + "\nReturn the structured candidate only. MCP will validate scope, apply the change, and run proof independently."

        )

        if orchestration_ctx is not None:
            self.orchestration_ledger.append_event(
                orchestration_ctx.run_id,
                wave_id=orchestration_ctx.wave_id,
                delegation_id=orchestration_ctx.delegation_id,
                event_type="model_dispatch_started",
                state_before=orchestration_ctx.state,
                state_after=orchestration_ctx.state,
                payload={
                    "route": routing.get("selected"),
                    "profile": routing.get("profile"),
                    "model": routing.get("model"),
                    "effort": routing.get("effort"),
                    "allowed_paths": allowed_paths,
                    "packet_bytes": len(prompt.encode("utf-8")),
                },
            )

        try:

            bridge_result = self._codex_bridge.run(

                prompt,

                profile=str(routing["profile"]),

                model=str(routing["model"]),

                effort=str(routing["effort"]),

                deadline_ms=int(AGENT_EXECUTION_ROUTES[str(routing["selected"])].get("deadline_ms", 0) or 0),

                output_schema=AGENT_CANDIDATE_OUTPUT_SCHEMA,

            )

        except CodexBridgeError as exc:

            if orchestration_ctx is not None:
                self.orchestration_ledger.append_event(
                    orchestration_ctx.run_id,
                    wave_id=orchestration_ctx.wave_id,
                    delegation_id=orchestration_ctx.delegation_id,
                    event_type="model_dispatch_finished",
                    state_before=orchestration_ctx.state,
                    state_after=orchestration_ctx.state,
                    payload={"status": "error", "failure_class": normalize_failure_class(exc.code), "retryable": exc.retryable},
                )

            return {

                "status": "blocked",

                "reason": exc.code,

                "retryable": exc.retryable,

                "routing": routing,

                "patches": [],

                "recommended_next_action": "Return to ChatWeb Sol or choose one different policy-approved route; do not retry unchanged.",

            }

        observation = bridge_result.get("observation") if isinstance(bridge_result.get("observation"), dict) else {}

        status = str(observation.get("status") or bridge_result.get("status") or "unknown")

        if orchestration_ctx is not None:
            self.orchestration_ledger.append_event(
                orchestration_ctx.run_id,
                wave_id=orchestration_ctx.wave_id,
                delegation_id=orchestration_ctx.delegation_id,
                event_type="model_dispatch_finished",
                state_before=orchestration_ctx.state,
                state_after=orchestration_ctx.state,
                payload={
                    "status": status,
                    "wall_time_ms": observation.get("wall_time_ms"),
                    "deadline_hit": bool(observation.get("deadline_hit", bridge_result.get("deadline_hit", False))),
                    "economics": observation.get("economics"),
                },
            )

        base = {

            "routing": routing,

            "model_status": status,

            "wall_time_ms": observation.get("wall_time_ms"),

            "economics": observation.get("economics"),

            "deadline_hit": bool(observation.get("deadline_hit", bridge_result.get("deadline_hit", False))),

            "patches": [],

        }

        if status != "completed":

            return {

                **base,

                "status": "blocked",

                "reason": "candidate_model_not_completed",

                "error": observation.get("error"),

                "recommended_next_action": "Return to ChatWeb Sol; do not serially cascade through every model tier.",

            }

        text = str(observation.get("agent_text") or "").strip()

        try:

            parsed = json.loads(text)

        except (TypeError, ValueError, json.JSONDecodeError):

            parsed = None

        if not isinstance(parsed, dict):

            return {**base, "status": "blocked", "reason": "candidate_output_invalid", "candidate_text": text[:2_000]}

        if str(parsed.get("status") or "blocked") != "ready":

            return {

                **base,

                "status": "blocked",

                "reason": "candidate_reported_blocked",

                "summary": str(parsed.get("summary") or "")[:1_000],

                "confidence": parsed.get("confidence"),

            }

        try:

            patches, new_files = self._candidate_payload_to_patches(parsed, allowed_paths=allowed_paths)

        except ToolFailure as exc:

            return {

                **base,

                "status": "blocked",

                "reason": exc.code,

                "summary": str(parsed.get("summary") or "")[:1_000],

                "validation_error": exc.message,

                "recommended_next_action": "Return candidate validation evidence to ChatWeb Sol; do not apply partial changes.",

            }

        return {

            **base,

            "status": "ready",

            "patches": patches,

            "new_files": new_files,

            "summary": str(parsed.get("summary") or "")[:1_000],

            "proof": list(parsed.get("proof") or [])[:4],

            "confidence": parsed.get("confidence"),

            "allowed_paths": allowed_paths,

        }

    def _maybe_agent_workflow_external_review(
        self,
        *,
        workflow: str,
        objective: str,
        verification: str,
        execution: dict[str, Any],
        dry_run: bool,
    ) -> dict[str, Any]:
        raw_mode = str(os.environ.get(AGENT_EXTERNAL_REVIEW_ENV, "auto")).strip().lower()
        if raw_mode in {"0", "false", "off", "none", "disabled"}:
            return {"plane": "none", "status": "skipped", "reason": "external_review_disabled"}
        force_packet = raw_mode in {"1", "true", "on", "packet", "always"}
        if dry_run:
            return {"plane": "none", "status": "skipped", "reason": "dry_run"}
        if not execution.get("ok"):
            return {"plane": "none", "status": "skipped", "reason": "execution_not_accepted"}
        if workflow in {"diagnose", "document", "resume"}:
            return {"plane": "none", "status": "skipped", "reason": "workflow_has_no_review_value"}

        raw_affected = execution.get("affected_files", [])
        affected_paths = sorted({
            str(item.get("path", "")).strip()
            for item in raw_affected if isinstance(raw_affected, list)
            if isinstance(item, dict) and str(item.get("path", "")).strip()
        })[:32]
        if not affected_paths:
            return {"plane": "none", "status": "skipped", "reason": "no_code_change"}

        diff_result = execution.get("git_diff") if isinstance(execution.get("git_diff"), dict) else {}
        diff_text = str(diff_result.get("diff") or "")
        if not diff_text:
            return {
                "plane": "none",
                "status": "skipped",
                "reason": "packet_evidence_missing",
                "recommended_profile": "scoped",
                "affected_paths": affected_paths,
            }
        if bool(diff_result.get("truncated")) or len(diff_text) > AGENT_REVIEW_PACKET_MAX_DIFF_CHARS:
            return {
                "plane": "none",
                "status": "skipped",
                "reason": "packet_evidence_too_large",
                "recommended_profile": "scoped",
                "affected_paths": affected_paths,
                "diff_sha256": hashlib.sha256(diff_text.encode("utf-8")).hexdigest(),
            }

        proof, strong_oracle = self._agent_review_proof(execution, verification)
        localized = len(affected_paths) <= 2 and len(diff_text) <= 6_000
        if not force_packet and workflow in {"bugfix", "test_failure"} and strong_oracle and localized:
            return {
                "plane": "none",
                "status": "skipped",
                "reason": "localized_change_with_strong_oracle",
                "affected_paths": affected_paths,
            }

        diff_sha256 = hashlib.sha256(diff_text.encode("utf-8")).hexdigest()
        packet = {
            "objective": objective,
            "workflow": workflow,
            "accept": "Find no material defect in the supplied change evidence, or identify a concrete fix/proof gap.",
            "affected_paths": affected_paths,
            "diff_sha256": diff_sha256,
            "proof": proof,
            "diff": diff_text,
            "question": "Review only this packet for material correctness, regression, or missing proof. Do not inspect the repository.",
        }
        prompt = "Independent evidence-only review packet:\n" + json.dumps(packet, ensure_ascii=False, separators=(",", ":"))
        try:
            bridge_result = self._codex_bridge.run(
                prompt,
                profile="packet",
                deadline_ms=AGENT_REVIEW_DEADLINE_MS,
                output_schema=AGENT_REVIEW_OUTPUT_SCHEMA,
            )
        except CodexBridgeError as exc:
            return {
                "plane": "external_mcp",
                "profile": "packet",
                "status": "unavailable",
                "reason": exc.code,
                "retryable": exc.retryable,
                "affected_paths": affected_paths,
                "diff_sha256": diff_sha256,
                "recommended_next_action": "Continue with Sol acceptance; do not repeat an unchanged external-review failure.",
            }

        observation = bridge_result.get("observation") if isinstance(bridge_result.get("observation"), dict) else {}
        status = str(observation.get("status") or bridge_result.get("status") or "unknown")
        review: dict[str, Any] = {
            "plane": "external_mcp",
            "profile": "packet",
            "status": status,
            "route": observation.get("route") or bridge_result.get("route"),
            "wall_time_ms": observation.get("wall_time_ms"),
            "economics": observation.get("economics"),
            "deadline_hit": bool(observation.get("deadline_hit", bridge_result.get("deadline_hit", False))),
            "affected_paths": affected_paths,
            "diff_sha256": diff_sha256,
        }
        if status != "completed":
            review["error"] = observation.get("error")
            review["recommended_next_action"] = "Continue with Sol acceptance or choose one different policy-approved route; do not retry unchanged."
            return review
        reviewer_text = str(observation.get("agent_text") or "").strip()
        try:
            parsed = json.loads(reviewer_text)
        except (TypeError, ValueError, json.JSONDecodeError):
            parsed = None
        if isinstance(parsed, dict):
            verdict = str(parsed.get("verdict") or "blocked")
            review.update({
                "verdict": verdict,
                "findings": list(parsed.get("findings", []))[:5],
                "missing_proof": list(parsed.get("missing_proof", []))[:5],
                "confidence": parsed.get("confidence"),
                "attention_required": verdict != "accept",
            })
        else:
            review.update({"verdict": "blocked", "reviewer_text": reviewer_text[:4_000], "attention_required": True})
        return review
    def workspace_context(self, args: dict[str, Any]) -> dict[str, Any]:
        detail = str(args.get("detail", "compact")).lower()
        cache_args = {"path": str(args.get("path", ".")), "max_entries": int(args.get("max_entries", 40)), "detail": detail}
        cache_key = self._fast_cache_key("workspace_context", cache_args)
        cached = self._fast_cache_get(cache_key, 30)
        if cached is not None:
            return cached
        root_entries = self.list_dir({
            "path": str(args.get("path", ".")),
            "max_entries": min(int(args.get("max_entries", 40)), 500),
            "max_depth": 1,
            "recursive": False,
        })
        try:
            git = self.git_status({"path": str(args.get("path", ".")), "max_entries": 100})
        except Exception as exc:  # non-Git folders remain valid workspaces
            git = {"is_repo": False, "warnings": [str(exc)]}
        project = {"type": "unknown", "name": self.workspace.root.name, "version": ""}
        package = self.workspace.root / "package.json"
        if package.is_file():
            try:
                metadata = json.loads(package.read_text(encoding="utf-8"))
                project = {
                    "type": "electron" if metadata.get("main") else "node",
                    "name": str(metadata.get("name") or self.workspace.root.name),
                    "version": str(metadata.get("version") or ""),
                }
            except (OSError, ValueError):
                pass
        elif (self.workspace.root / "pyproject.toml").is_file():
            project["type"] = "python"
        elif (self.workspace.root / "Cargo.toml").is_file():
            project["type"] = "rust"
        elif (self.workspace.root / "go.mod").is_file():
            project["type"] = "go"
        task = self.task_state.get()
        if detail != "full":
            task = {key: task.get(key) for key in ("task_id", "objective", "status", "current_step", "next_step", "failure")}
            git = {
                "is_repo": git.get("is_repo", False),
                "branch": git.get("branch") or git.get("head"),
                "changed_count": len(git.get("entries", [])) if isinstance(git.get("entries"), list) else int(git.get("changed_count", 0) or 0),
                "truncated": bool(git.get("truncated", False)),
            }
        payload = {
            "workspace": str(self.workspace.root),
            "default_cwd": self.default_cwd_display(),
            "project": project,
            "entries": root_entries.get("entries", []),
            "entries_truncated": root_entries.get("truncated", False),
            "git": git,
            "task": task,
            "tool_mode": self.tool_mode,
            "detail": detail,
            "cache": {"hit": False, "age_ms": 0},
        }
        if detail == "full":
            payload["runtime"] = {
                "server_instance_id": self.server_instance_id,
                "process_instance_id": self.process_instance_id,
                "performance_trace_version": self.performance_trace.schema_version,
                "stale_orchestration_runs": len(self.stale_orchestration_runs),
                "orphaned_background_operations": int(self.orphaned_background_operations),
                "orphaned_idempotency_records": int(self.orphaned_idempotency_records),
                "agent_lanes_waiting_after_restart": int(self.recovered_agent_lanes),
            }
        self._fast_cache_put(cache_key, payload)
        return payload

    def _context_bundle_cache_key(self, args: dict[str, Any]) -> str:
        normalized = {key: value for key, value in args.items() if key != "force_refresh"}
        encoded = json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(f"{self.workspace.root}\n{encoded}".encode("utf-8")).hexdigest()

    def _clear_context_bundle_cache(self) -> None:
        workspace_prefix = hashlib.sha256(f"{self.workspace.root}\n".encode("utf-8")).hexdigest()[:12]
        with _CONTEXT_BUNDLE_CACHE_LOCK:
            stale = [key for key in _CONTEXT_BUNDLE_CACHE if key.startswith(workspace_prefix)]
            for key in stale:
                _CONTEXT_BUNDLE_CACHE.pop(key, None)

    def prepare_coding_context(self, args: dict[str, Any]) -> dict[str, Any]:
        """Build the context a coding model normally gathers through many round trips."""
        cache_key = self._context_bundle_cache_key(args)
        namespaced_key = hashlib.sha256(f"{self.workspace.root}\n".encode("utf-8")).hexdigest()[:12] + cache_key
        now = time.time()
        if not bool(args.get("force_refresh", False)):
            with _CONTEXT_BUNDLE_CACHE_LOCK:
                cached = _CONTEXT_BUNDLE_CACHE.get(namespaced_key)
            if cached and now - cached[0] <= CONTEXT_BUNDLE_CACHE_TTL_SECONDS:
                payload = json.loads(json.dumps(cached[1], ensure_ascii=False))
                payload["cache_hit"] = True
                payload["cache_age_ms"] = int((now - cached[0]) * 1000)
                return payload

        objective = str(args.get("objective", "")).strip()
        raw_queries = args.get("queries", [])
        raw_paths = args.get("paths", [])
        queries = list(dict.fromkeys(str(item).strip() for item in raw_queries if str(item).strip()))[:12]
        requested_paths = list(dict.fromkeys(str(item).strip() for item in raw_paths if str(item).strip()))[:40]
        max_files = min(max(int(args.get("max_files", 12)), 1), 30)
        max_total_bytes = min(max(int(args.get("max_total_bytes", 262144)), 4096), 1048576)
        max_matches = min(max(int(args.get("max_matches_per_query", 20)), 1), 100)

        workspace = self.workspace_context({"path": str(args.get("path", ".")), "max_entries": int(args.get("max_entries", 120))})
        instructions = {
            "root": [
                {"path": item.path, "content": item.content, "truncated": item.truncated}
                for item in self.project_context.root_files
            ],
            "nested_paths": list(self.project_context.nested_files),
            "warnings": list(self.project_context.warnings),
        }
        searches: list[dict[str, Any]] = []
        path_scores: dict[str, int] = {path: 1_000_000 - index for index, path in enumerate(requested_paths)}

        def search_once(query: str) -> dict[str, Any]:
            try:
                result = self.search_text({
                    "query": query,
                    "path": str(args.get("path", ".")),
                    "regex": bool(args.get("regex", False)),
                    "case_sensitive": bool(args.get("case_sensitive", False)),
                    "include_globs": args.get("include_globs", []),
                    "exclude_globs": args.get("exclude_globs", []),
                    "context_lines": 1,
                    "max_results": max_matches,
                    "max_preview_bytes": 360,
                })
                matches = result.get("matches", [])
                return {
                    "query": query,
                    "engine": result.get("engine"),
                    "total_matches": result.get("total_matches", len(matches)),
                    "truncated": result.get("truncated", False),
                    "matches": matches,
                }
            except (ToolFailure, OSError, ValueError) as exc:
                return {"query": query, "error": str(exc), "matches": []}

        if queries:
            with ThreadPoolExecutor(max_workers=min(4, len(queries)), thread_name_prefix="context-search") as pool:
                searches = list(pool.map(search_once, queries))
        for result in searches:
            for match in result.get("matches", []):
                path = str(match.get("path", ""))
                if path:
                    path_scores[path] = path_scores.get(path, 0) + 1

        ranked_paths = sorted(path_scores, key=lambda item: (-path_scores[item], item))[:max_files]
        files: list[dict[str, Any]] = []
        total_bytes = 0
        for path in ranked_paths:
            remaining = max_total_bytes - total_bytes
            if remaining <= 0:
                break
            try:
                item = self.read_file({"path": path, "max_bytes": min(remaining, 131072), "max_lines": 2000})
            except (ToolFailure, OSError, UnicodeError) as exc:
                files.append({"path": path, "error": str(exc)})
                continue
            total_bytes += len(str(item.get("content", "")).encode("utf-8"))
            files.append(item)

        payload = {
            "objective": objective,
            "workspace": workspace,
            "instructions": instructions,
            "searches": searches,
            "files": files,
            "selected_paths": ranked_paths,
            "total_content_bytes": total_bytes,
            "task_resume": self.task_state.get(),
            "cache_hit": False,
            "cache_ttl_seconds": CONTEXT_BUNDLE_CACHE_TTL_SECONDS,
            "recommended_next_action": "Use apply_changes_and_verify with all related patches and required checks in one call.",
        }
        with _CONTEXT_BUNDLE_CACHE_LOCK:
            if len(_CONTEXT_BUNDLE_CACHE) >= 64:
                oldest = min(_CONTEXT_BUNDLE_CACHE, key=lambda key: _CONTEXT_BUNDLE_CACHE[key][0])
                _CONTEXT_BUNDLE_CACHE.pop(oldest, None)
            _CONTEXT_BUNDLE_CACHE[namespaced_key] = (now, payload)
        return payload

    def _run_continuous_check(self, command: str, workdir: str, timeout_ms: int) -> dict[str, Any]:
        started = time.time()
        payload = self.exec_command({
            "cmd": command,
            "workdir": workdir,
            "timeout_ms": timeout_ms,
            "yield_time_ms": 30000,
            "max_output_bytes": 131072,
            "verbosity": "summary",
        })
        while payload.get("status") == "running":
            payload = self.write_stdin({
                "session_id": str(payload.get("session_id", "")),
                "chars": "",
                "yield_time_ms": 30000,
                "max_output_bytes": 131072,
                "verbosity": "summary",
            })
        return {
            "command": command,
            "status": "passed" if payload.get("exit_code") == 0 else str(payload.get("status") or "failed"),
            "exit_code": payload.get("exit_code"),
            "duration_ms": int((time.time() - started) * 1000),
            "summary": str(payload.get("summary") or payload.get("stderr") or payload.get("stdout") or "")[:8000],
            "session_id": payload.get("session_id"),
        }

    def apply_changes_and_verify(self, args: dict[str, Any]) -> dict[str, Any]:
        """Apply one coherent change set, record proof identity, and avoid redundant proof reruns."""
        objective = str(args.get("objective", "")).strip() or "Apply and verify workspace changes"
        orchestration_ctx = args.get("_orchestration_context")
        ctx = orchestration_ctx if isinstance(orchestration_ctx, RunContext) else None
        raw_patches = args.get("patches", [])
        patches = [str(item) for item in raw_patches if str(item).strip()]
        single_patch = str(args.get("patch", "")).strip()
        if single_patch:
            patches.insert(0, single_patch)
        checks = list(dict.fromkeys(str(item).strip() for item in args.get("checks", []) if str(item).strip()))[:8]
        verification = str(args.get("verification", "tests")).lower()
        if verification not in {"none", "tests", "build", "all"}:
            raise ToolFailure("INVALID_ARGUMENT", "verification must be none, tests, build, or all.", category="validation")
        if not patches and not checks and verification == "none":
            raise ToolFailure("INVALID_ARGUMENT", "Provide a patch, check command, or verification step.", category="validation")

        workflow_steps: list[dict[str, str]] = []
        if patches:
            workflow_steps.append({"id": "apply", "text": "Apply workspace changes", "status": "pending"})
        if checks:
            workflow_steps.append({"id": "checks", "text": "Run requested checks", "status": "pending"})
        if verification != "none":
            workflow_steps.append({"id": "verify", "text": "Run tests and build verification", "status": "pending"})
        workflow_steps.append({"id": "finalize", "text": "Finalize verified result", "status": "pending"})

        def set_stage(stage_id: str, current_step: str, *, failed: bool = False) -> None:
            reached = False
            for step in workflow_steps:
                if step["id"] == stage_id:
                    step["status"] = "failed" if failed else "in_progress"
                    reached = True
                elif not reached and step["status"] != "failed":
                    step["status"] = "completed"
                elif reached and step["status"] not in {"completed", "failed"}:
                    step["status"] = "pending"
            self.task_state.update({"steps": workflow_steps, "current_step": current_step})

        def record_failure(code: object, **details: Any) -> None:
            if ctx is None or ctx.state in {"REPLAN", "BLOCKED", "ABORTED", "CHECKPOINTED"}:
                return
            self.orchestration_control.record_failure(ctx, code, payload=details)
            self._project_orchestration(ctx, event="orchestration_failure_projected")

        first_stage = workflow_steps[0]["id"]
        first_text = {
            "apply": "Applying complete change set",
            "checks": "Running requested checks",
            "verify": "Testing and building",
            "finalize": "Finalizing result",
        }[first_stage]
        workflow_steps[0]["status"] = "in_progress"

        self.task_state.update({
            "objective": objective,
            "status": "active",
            "steps": workflow_steps,
            "current_step": first_text,
            "next_step": "Run all requested checks and summarize the result.",
        }, event="continuous_workflow_started")

        workdir = str(args.get("workdir", args.get("path", ".")))
        if ctx is not None:
            identity_before = self._orchestration_workspace_identity(args.get("path", "."))
            try:
                self.orchestration_control.assert_write_allowed(
                    ctx,
                    owner="MCP",
                    base_head=str(identity_before.get("base_head") or ""),
                    worktree_fp=str(identity_before.get("worktree_fp") or ""),
                )
            except OrchestrationControlError as exc:
                record_failure(exc.code, details=exc.details)
                raise ToolFailure(exc.code, str(exc), category="runtime", retryable=True, details=exc.details) from exc

        patch_results: list[dict[str, Any]] = []
        affected_files: list[dict[str, str]] = []
        try:
            for patch_text in patches:
                result = self.apply_patch({"patch": patch_text, "dry_run": bool(args.get("dry_run", False))})
                patch_results.append(result)
                affected_files.extend(result.get("affected_files", []))
        except ToolFailure as exc:
            record_failure(exc.code, message=str(exc))
            raise
        if patches and not bool(args.get("dry_run", False)):
            self._clear_context_bundle_cache()

        if ctx is not None and ctx.state == "EXECUTING":
            self.orchestration_control.begin_proof(ctx)
            self._project_orchestration(ctx, event="orchestration_proving")

        proof_identity = self._orchestration_workspace_identity(args.get("path", ".")) if ctx is not None else {}
        affected_paths = sorted({
            str(item.get("path", "")).strip().replace("\\", "/")
            for item in affected_files
            if isinstance(item, dict) and str(item.get("path", "")).strip()
        })
        proof_ids: list[str] = []
        proof_cache_hits = 0
        proof_cache_saved_ms = 0
        upstream_proof_ids: list[str] = []

        command_results: list[dict[str, Any]] = []
        timeout_ms = min(max(int(args.get("timeout_ms", 600000)), 1000), 600000)
        if checks:
            set_stage("checks", "Running requested checks")
        for command in checks:
            if ctx is None:
                result = self._run_continuous_check(command, workdir, timeout_ms)
            else:
                command_hash = hashlib.sha256(command.encode("utf-8", errors="replace")).hexdigest()
                stage_id = f"check:{command_hash[:16]}"
                proof_fp = self.proof_ledger.fingerprint(
                    stage_id=stage_id,
                    base_head=str(proof_identity.get("base_head") or ctx.base_head),
                    worktree_fp=str(proof_identity.get("worktree_fp") or ""),
                    contract_fp=ctx.contract_fp,
                    input_paths=affected_paths,
                    config={"command_hash": command_hash, "workdir": workdir, "timeout_ms": timeout_ms},
                    upstream_proof_ids=upstream_proof_ids,
                )
                result, proof_id = self.proof_ledger.run_cached(
                    run_id=ctx.run_id,
                    wave_id=ctx.wave_id,
                    stage_id=stage_id,
                    input_fingerprint=proof_fp,
                    command=command,
                    upstream_proof_ids=upstream_proof_ids,
                    metadata={"kind": "check", "workdir": workdir},
                    runner=lambda command=command: self._run_continuous_check(command, workdir, timeout_ms),
                )
                proof_ids.append(proof_id)
                upstream_proof_ids.append(proof_id)
                proof_cache_hits += 1 if result.get("cache_hit") else 0
                proof_cache_saved_ms += max(0, int(result.get("cache_saved_ms", 0) or 0))
            command_results.append(result)
            if result.get("exit_code") != 0:
                failure = f"Check failed: {command}"
                set_stage("checks", "Requested check failed", failed=True)
                record_failure("CHECK_FAILED", command_hash=hashlib.sha256(command.encode("utf-8")).hexdigest())
                self.task_state.update({"status": "waiting", "failure": failure, "current_step": "Replan required", "next_step": "Replan from the failed check; do not retry unchanged."})
                return {
                    "ok": False,
                    "status": "failed",
                    "objective": objective,
                    "patch_results": patch_results,
                    "affected_files": affected_files,
                    "check_results": command_results,
                    "build_report": None,
                    "proof_summary": {"proof_ids": proof_ids, "cache_hits": proof_cache_hits, "cache_saved_ms": proof_cache_saved_ms},
                    "error": {"code": "CHECK_FAILED", "message": failure, "category": "runtime", "retryable": True, "details": {}},
                }

        build_report = None
        if verification != "none":
            set_stage("verify", "Testing and building")
            verify_args = {
                "path": str(args.get("path", ".")),
                "run_tests": verification in {"tests", "all"},
                "run_build": verification in {"build", "all"},
                "test_command": args.get("test_command", ""),
                "build_command": args.get("build_command", ""),
                "artifact_paths": args.get("artifact_paths", []),
                "hash_algorithm": args.get("hash_algorithm", "sha256"),
                "timeout_seconds": min(max(int(args.get("timeout_seconds", 600)), 1), 600),
            }
            if ctx is None:
                build_report = self.verify_build(verify_args)
            else:
                stage_id = f"verify:{verification}"
                proof_fp = self.proof_ledger.fingerprint(
                    stage_id=stage_id,
                    base_head=str(proof_identity.get("base_head") or ctx.base_head),
                    worktree_fp=str(proof_identity.get("worktree_fp") or ""),
                    contract_fp=ctx.contract_fp,
                    input_paths=affected_paths,
                    config=verify_args,
                    upstream_proof_ids=upstream_proof_ids,
                )
                build_report, proof_id = self.proof_ledger.run_cached(
                    run_id=ctx.run_id,
                    wave_id=ctx.wave_id,
                    stage_id=stage_id,
                    input_fingerprint=proof_fp,
                    command=f"verify_build:{verification}",
                    upstream_proof_ids=upstream_proof_ids,
                    metadata={"kind": "verify", "verification": verification},
                    runner=lambda: self.verify_build(verify_args),
                )
                proof_ids.append(proof_id)
                upstream_proof_ids.append(proof_id)
                proof_cache_hits += 1 if build_report.get("cache_hit") else 0
                proof_cache_saved_ms += max(0, int(build_report.get("cache_saved_ms", 0) or 0))
            if build_report.get("ok") is False:
                set_stage("verify", "Verification failed", failed=True)
                error = build_report.get("error") if isinstance(build_report.get("error"), dict) else {}
                record_failure(error.get("code") or "VERIFICATION_FAILED", verification=verification)
                self.task_state.update({
                    "status": "waiting",
                    "failure": str(error.get("message") or "Verification failed"),
                    "current_step": "Replan required",
                    "next_step": "Replan from the failed proof stage; completed proof fingerprints remain auditable.",
                })
                return {
                    "ok": False,
                    "status": "failed",
                    "objective": objective,
                    "patch_results": patch_results,
                    "affected_files": affected_files,
                    "check_results": command_results,
                    "build_report": build_report,
                    "proof_summary": {"proof_ids": proof_ids, "cache_hits": proof_cache_hits, "cache_saved_ms": proof_cache_saved_ms},
                    "error": build_report.get("error"),
                }

        diff = None
        if bool(args.get("include_diff", True)) and affected_files:
            try:
                diff_args: dict[str, Any] = {
                    "unstaged": True,
                    "max_bytes": int(args.get("max_diff_bytes", 131072)),
                }
                if affected_paths:
                    diff_args["paths"] = affected_paths
                else:
                    diff_args["path"] = str(args.get("path", "."))
                diff = self.git_diff(diff_args)
            except (ToolFailure, OSError, ValueError):
                diff = None
        set_stage("finalize", "Finalizing result")
        for step in workflow_steps:
            step["status"] = "completed"
        final_status = "waiting" if ctx is not None else "completed"
        final_step = "Waiting for final acceptance" if ctx is not None else "Completed"
        final_next = (
            "ChatWeb Sol must accept or reject this proven wave via task_control before another implementation wave."
            if ctx is not None
            else "Review the verified changes or continue with the next task."
        )
        proof_fingerprint = hashlib.sha256("|".join(proof_ids).encode("utf-8")).hexdigest() if proof_ids else ""
        self.task_state.update({
            "status": final_status,
            "steps": workflow_steps,
            "current_step": final_step,
            "next_step": final_next,
            "failure": None,
        }, event="continuous_workflow_completed")
        return {
            "ok": True,
            "status": "passed",
            "objective": objective,
            "patch_results": patch_results,
            "affected_files": affected_files,
            "check_results": command_results,
            "build_report": build_report,
            "git_diff": diff,
            "proof_summary": {
                "proof_ids": proof_ids,
                "cache_hits": proof_cache_hits,
                "cache_saved_ms": proof_cache_saved_ms,
                "proof_fingerprint": proof_fingerprint,
                "worktree_fp": str(proof_identity.get("worktree_fp") or ""),
            },
            "next_step": final_next,
        }

    @staticmethod
    def _new_files_patch(files: list[Any]) -> str:
        sections = ["*** Begin Patch"]
        added = 0
        for item in files[:100]:
            if not isinstance(item, dict):
                raise ToolFailure("INVALID_ARGUMENT", "Each files item must contain path and content.", category="validation")
            path = str(item.get("path", "")).strip().replace("\\", "/")
            if not path or path.startswith("/") or ".." in Path(path).parts:
                raise ToolFailure("INVALID_ARGUMENT", f"Invalid new file path: {path!r}", category="validation")
            content = str(item.get("content", ""))
            sections.append(f"*** Add File: {path}")
            lines = content.splitlines()
            sections.extend(f"+{line}" for line in lines)
            if content.endswith(("\n", "\r")) is False and lines:
                pass
            if not lines:
                sections.append("+")
            added += 1
        if not added:
            return ""
        sections.append("*** End Patch")
        return "\n".join(sections)

    def _agent_orchestration_context(
        self,
        args: dict[str, Any],
        *,
        objective: str,
    ) -> tuple[RunContext, dict[str, Any]]:
        current_task = self.task_state.get()
        projection = current_task.get("orchestration") if isinstance(current_task.get("orchestration"), dict) else {}
        run_id = str(projection.get("run_id") or "")
        current_ctx = self.orchestration_control.snapshot(run_id) if run_id else None

        if not current_task.get("task_id") or (
            str(current_task.get("status") or "") in {"completed", "stopped"}
            and (current_ctx is None or current_ctx.state in {"CHECKPOINTED", "BLOCKED", "ABORTED"})
        ):
            current_task = self.task_state.ensure_started(objective, current_step="Orchestration preflight")
            projection = current_task.get("orchestration") if isinstance(current_task.get("orchestration"), dict) else {}
            run_id = str(projection.get("run_id") or "")
            current_ctx = self.orchestration_control.snapshot(run_id) if run_id else None

        identity = self._orchestration_workspace_identity(args.get("path", "."))
        requested_mode = str(args.get("execution_mode", "auto")).strip().lower() or "auto"
        contract_fp = self.orchestration_control.stable_contract_fingerprint(args.get("contract_fingerprint", ""))
        replan_reason = str(args.get("replan_reason", "")).strip()

        if current_ctx is not None:
            if current_ctx.state == "ACCEPTING":
                raise ToolFailure(
                    "FINAL_ACCEPTANCE_REQUIRED",
                    "The previous proven wave is waiting for ChatWeb Sol acceptance. Use task_control action=accept or reject before another implementation wave.",
                    category="runtime",
                    retryable=True,
                    details={"run_id": current_ctx.run_id, "wave_id": current_ctx.wave_id},
                )
            if current_ctx.state in {"ROUTED", "EXECUTING", "PROVING"}:
                self.orchestration_control.record_failure(
                    current_ctx,
                    "RUNTIME_RESUME_REQUIRED",
                    payload={"reason": "A non-terminal wave was recovered outside its original synchronous execution."},
                )
                self._project_orchestration(current_ctx, event="orchestration_replan_required")
                raise ToolFailure(
                    "REPLAN_REQUIRED",
                    "Recovered orchestration state requires an explicit replan_reason before execution can continue.",
                    category="runtime",
                    retryable=True,
                    details={"run_id": current_ctx.run_id, "wave_id": current_ctx.wave_id},
                )
            if current_ctx.state == "REPLAN":
                if not replan_reason:
                    raise ToolFailure(
                        "REPLAN_REASON_REQUIRED",
                        "The current orchestration run is in REPLAN. Provide replan_reason to create a new wave; route/ownership may not change silently.",
                        category="runtime",
                        retryable=True,
                        details={"run_id": current_ctx.run_id, "wave_id": current_ctx.wave_id},
                    )
                current_ctx = self.orchestration_control.begin_replan_wave(
                    current_ctx,
                    execution_mode=requested_mode,
                    base_head=str(identity.get("base_head") or ""),
                    worktree_fp=str(identity.get("worktree_fp") or ""),
                    contract_fp=contract_fp,
                    reason=replan_reason,
                )
            elif current_ctx.state in {"CHECKPOINTED", "BLOCKED", "ABORTED"}:
                current_ctx = None
            elif current_ctx.state in {"PREFLIGHT", "READY"}:
                base_changed = bool(current_ctx.base_head and current_ctx.base_head != str(identity.get("base_head") or ""))
                worktree_changed = bool(current_ctx.worktree_fp and current_ctx.worktree_fp != str(identity.get("worktree_fp") or ""))
                contract_changed = bool(current_ctx.contract_fp and contract_fp and current_ctx.contract_fp != contract_fp)
                if base_changed or worktree_changed or contract_changed:
                    self.orchestration_control.record_failure(
                        current_ctx,
                        "CONTRACT_DRIFT" if contract_changed else "BASE_DRIFT",
                        payload={
                            "base_changed": base_changed,
                            "worktree_changed": worktree_changed,
                            "contract_changed": contract_changed,
                        },
                    )
                    self._project_orchestration(current_ctx, event="orchestration_drift_detected")
                    if not replan_reason:
                        raise ToolFailure(
                            "REPLAN_REASON_REQUIRED",
                            "Base/worktree/contract changed after orchestration preflight. Provide replan_reason to create a new wave.",
                            category="runtime",
                            retryable=True,
                            details={"run_id": current_ctx.run_id, "wave_id": current_ctx.wave_id},
                        )
                    current_ctx = self.orchestration_control.begin_replan_wave(
                        current_ctx,
                        execution_mode=requested_mode,
                        base_head=str(identity.get("base_head") or ""),
                        worktree_fp=str(identity.get("worktree_fp") or ""),
                        contract_fp=contract_fp,
                        reason=replan_reason,
                    )

        if current_ctx is None:
            if current_task.get("task_id") and str(current_task.get("status") or "") in {"completed", "failed", "stopped"}:
                current_task = self.task_state.update(
                    {"objective": objective, "status": "active", "failure": None, "current_step": "Orchestration preflight", "new_task": True},
                    event="task_started",
                )
            current_ctx = self.orchestration_control.begin(
                objective=objective,
                task_id=str(current_task.get("task_id") or ""),
                execution_mode=requested_mode,
                base_head=str(identity.get("base_head") or ""),
                worktree_fp=str(identity.get("worktree_fp") or ""),
                contract_fp=contract_fp,
                metadata={"workflow": str(args.get("workflow", "custom")), "phase": str(args.get("phase", "prepare")), "branch": identity.get("branch")},
            )

        self._project_orchestration(current_ctx, event="orchestration_context_ready")
        return current_ctx, identity

    @staticmethod
    def _validate_execution_mode_route(requested_mode: str, route: dict[str, Any]) -> str:
        requested_mode = str(requested_mode or "auto").strip().lower() or "auto"
        selected = str(route.get("selected") or "deterministic")
        derived = Runtime._orchestration_mode_for_route(selected)
        if requested_mode == "auto":
            return derived
        if requested_mode == "coordinated_multi_worktree":
            return requested_mode
        if requested_mode == "mcp_only" and selected != "deterministic":
            raise ToolFailure("MODE_ROUTE_MISMATCH", "mcp_only execution requires deterministic routing.", category="validation")
        if requested_mode == "bounded_candidate" and selected not in {"mini", "luna"}:
            raise ToolFailure("MODE_ROUTE_MISMATCH", "bounded_candidate execution requires Mini or Luna routing.", category="validation")
        if requested_mode == "deep_single_lane" and selected not in {"terra", "sol_xhigh", "sol_max", "sol_ultra"}:
            raise ToolFailure("MODE_ROUTE_MISMATCH", "deep_single_lane execution requires a deep model route.", category="validation")
        return requested_mode

    @staticmethod
    def _request_hash(args: dict[str, Any]) -> str:
        stable = {key: value for key, value in args.items() if key != "idempotency_key" and not key.startswith("_")}
        encoded = json.dumps(stable, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(encoded.encode("utf-8", errors="replace")).hexdigest()

    @staticmethod
    def _agent_workflow_request_hash(args: dict[str, Any]) -> str:
        return Runtime._request_hash(args)

    @staticmethod
    def _agent_admission_budget(args: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        max_auto_steps = max(1, min(int(args.get("max_auto_steps", 64)), 256))
        max_tool_hops = max(1, min(int(args.get("max_tool_hops", 96)), 512))
        max_attempts = max(1, min(int(args.get("max_attempts", 1)), 10))
        max_runtime_seconds = max(1, min(int(args.get("max_runtime_seconds", 600)), 600))
        try:
            max_estimated_credits = max(0.0, float(args.get("max_estimated_credits", 0.0) or 0.0))
        except (TypeError, ValueError) as exc:
            raise ToolFailure("INVALID_ARGUMENT", "max_estimated_credits must be a non-negative number.", category="validation") from exc
        patches = len(args.get("patches", []) if isinstance(args.get("patches"), list) else []) + (1 if str(args.get("patch", "")).strip() else 0)
        files = len(args.get("files", []) if isinstance(args.get("files"), list) else [])
        directories = len(args.get("directories", []) if isinstance(args.get("directories"), list) else [])
        commands = len(args.get("commands", []) if isinstance(args.get("commands"), list) else [])
        candidate = 1 if str(args.get("execution_route", "auto")) not in {"deterministic"} and not patches else 0
        planned_auto_steps = 2 + patches + files + directories + commands + candidate
        if str(args.get("test_command", "")).strip():
            planned_auto_steps += 1
        if str(args.get("build_command", "")).strip():
            planned_auto_steps += 1
        planned_tool_hops = 2 + commands + (1 if patches or files or directories else 0) + candidate
        if planned_auto_steps > max_auto_steps or planned_tool_hops > max_tool_hops:
            raise ToolFailure(
                "WORKFLOW_BUDGET_EXCEEDED",
                "The planned workflow exceeds the deterministic admission budget.",
                category="policy",
                retryable=False,
                details={
                    "planned_auto_steps": planned_auto_steps,
                    "max_auto_steps": max_auto_steps,
                    "planned_tool_hops": planned_tool_hops,
                    "max_tool_hops": max_tool_hops,
                },
            )
        normalized = dict(args)
        normalized["timeout_seconds"] = min(int(args.get("timeout_seconds", 600)), max_runtime_seconds)
        budget = {
            "max_auto_steps": max_auto_steps,
            "planned_auto_steps": planned_auto_steps,
            "max_tool_hops": max_tool_hops,
            "planned_tool_hops": planned_tool_hops,
            "max_attempts": max_attempts,
            "attempts_used": 1,
            "retry_mode": "manual_replan_only",
            "max_runtime_seconds": max_runtime_seconds,
            "max_estimated_credits": max_estimated_credits,
        }
        normalized["_admission_budget"] = budget
        return normalized, budget

    @staticmethod
    def _agent_idempotency_summary(result: dict[str, Any]) -> dict[str, Any]:
        execution = result.get("execution") if isinstance(result.get("execution"), dict) else {}
        orchestration = result.get("orchestration") if isinstance(result.get("orchestration"), dict) else {}
        proof = execution.get("proof_summary") if isinstance(execution.get("proof_summary"), dict) else {}
        review = result.get("external_review") if isinstance(result.get("external_review"), dict) else {}
        return {
            "workflow": result.get("workflow"),
            "phase": result.get("phase"),
            "execution_status": execution.get("status"),
            "execution_ok": execution.get("ok"),
            "run_id": orchestration.get("run_id"),
            "wave_id": orchestration.get("wave_id"),
            "orchestration_state": orchestration.get("orchestration_state"),
            "proof_fingerprint": proof.get("proof_fingerprint"),
            "external_review_status": review.get("status"),
            "reports": orchestration.get("reports"),
        }

    def agent_workflow(self, args: dict[str, Any]) -> dict[str, Any]:
        normalized, budget = self._agent_admission_budget(args)
        phase = str(normalized.get("phase", "prepare")).lower()
        idempotency_key = str(normalized.get("idempotency_key", "") or "").strip()
        if idempotency_key and len(idempotency_key) > 128:
            raise ToolFailure("INVALID_ARGUMENT", "idempotency_key must be at most 128 characters.", category="validation")
        if phase not in {"execute", "run"} or not idempotency_key:
            result = self._agent_workflow_impl(normalized)
            result["admission_budget"] = budget
            if idempotency_key:
                result["idempotency"] = {"active": False, "reason": "prepare_resume_not_mutating"}
            return result

        request_hash = self._agent_workflow_request_hash(args)
        projection = self.task_state.get().get("orchestration", {})
        run_id = str(projection.get("run_id") or "") if isinstance(projection, dict) else ""
        wave_id = str(projection.get("wave_id") or "") if isinstance(projection, dict) else ""
        claim = self.orchestration_ledger.claim_idempotency(
            idempotency_key=idempotency_key,
            operation="agent_workflow",
            request_hash=request_hash,
            process_instance_id=self.process_instance_id,
            run_id=run_id,
            wave_id=wave_id,
        )
        if not claim.get("claimed"):
            reason = str(claim.get("reason") or "")
            record = claim.get("record") if isinstance(claim.get("record"), dict) else {}
            if reason == "conflict":
                raise ToolFailure(
                    "IDEMPOTENCY_CONFLICT",
                    "The idempotency_key was already used for a different agent_workflow request.",
                    category="validation",
                    details={"idempotency_key": idempotency_key, "status": record.get("status")},
                )
            if reason == "completed":
                return {
                    "workflow": record.get("summary", {}).get("workflow"),
                    "phase": record.get("summary", {}).get("phase"),
                    "deduplicated": True,
                    "durable_idempotency": True,
                    "idempotency": record,
                    "admission_budget": budget,
                    "recommended_next_action": "Use the recorded run/wave/report pointers; do not repeat the mutation.",
                }
            if reason == "failed":
                raise ToolFailure(
                    "IDEMPOTENT_REQUEST_FAILED",
                    "This exact idempotent workflow request already reached a known terminal failure; do not repeat it unchanged.",
                    category="runtime",
                    details={"idempotency_key": idempotency_key, "summary": record.get("summary")},
                )
            if reason == "unknown":
                raise ToolFailure(
                    "IDEMPOTENCY_OUTCOME_UNKNOWN",
                    "A previous process may have started this idempotent workflow but its outcome is unknown. Reconcile evidence before any replay.",
                    category="runtime",
                    details={"idempotency_key": idempotency_key, "summary": record.get("summary")},
                )
            raise ToolFailure(
                "IDEMPOTENCY_IN_PROGRESS",
                "This idempotent workflow is already in progress; observe the existing task instead of starting another copy.",
                category="runtime",
                retryable=True,
                details={"idempotency_key": idempotency_key, "run_id": record.get("run_id"), "wave_id": record.get("wave_id")},
            )

        try:
            result = self._agent_workflow_impl(normalized)
        except Exception as exc:
            known_terminal = isinstance(exc, ToolFailure) and exc.code in {
                "WORKFLOW_BUDGET_EXCEEDED", "WORKFLOW_CREDIT_BUDGET_EXCEEDED", "INVALID_ARGUMENT", "MODE_ROUTE_MISMATCH"
            }
            self.orchestration_ledger.finish_idempotency(
                idempotency_key,
                request_hash=request_hash,
                status="failed" if known_terminal else "unknown",
                summary={
                    "error_code": getattr(exc, "code", type(exc).__name__),
                    "category": getattr(exc, "category", "runtime"),
                    "outcome_unknown": not known_terminal,
                },
            )
            raise
        summary = self._agent_idempotency_summary(result)
        orchestration = result.get("orchestration") if isinstance(result.get("orchestration"), dict) else {}
        record = self.orchestration_ledger.finish_idempotency(
            idempotency_key,
            request_hash=request_hash,
            status="completed",
            summary=summary,
            run_id=str(orchestration.get("run_id") or ""),
            wave_id=str(orchestration.get("wave_id") or ""),
        )
        result["idempotency"] = record
        result["durable_idempotency"] = True
        result["admission_budget"] = budget
        return result

    def _agent_workflow_impl(self, args: dict[str, Any]) -> dict[str, Any]:
        """End-to-end workflow with durable wave audit, explicit authority, proof, and final acceptance state."""
        workflow = str(args.get("workflow", "custom")).lower()
        phase = str(args.get("phase", "prepare")).lower()
        dedup_key = self._fast_cache_key("agent_workflow_execute", args)
        if phase in {"execute", "run"}:
            cached_execution = self._fast_cache_get(dedup_key, 30)
            current_projection = self.task_state.get().get("orchestration", {})
            if cached_execution is not None and str(current_projection.get("orchestration_state") or "") != "REPLAN":
                cached_execution["deduplicated"] = True
                return cached_execution
        supported = {"bugfix", "feature", "greenfield", "refactor", "test_failure", "build_release", "diagnose", "document", "resume", "custom"}
        if workflow not in supported:
            raise ToolFailure("INVALID_ARGUMENT", f"Unknown workflow: {workflow}", category="validation")
        if phase not in {"prepare", "execute", "run", "resume"}:
            raise ToolFailure("INVALID_ARGUMENT", f"Unknown workflow phase: {phase}", category="validation")

        objective = str(args.get("objective", "")).strip() or str(self.task_state.get().get("objective", "")).strip()
        if workflow == "resume" or phase == "resume":
            state = self.task_state.get()
            context_args = {
                "objective": objective,
                "path": args.get("path", "."),
                "queries": args.get("queries", []),
                "paths": args.get("paths", []),
                "max_files": args.get("max_files", 12),
                "max_total_bytes": args.get("max_total_bytes", 262144),
                "force_refresh": True,
            }
            context = self.prepare_coding_context(context_args)
            return {
                "workflow": workflow,
                "phase": "resume",
                "task": state,
                "context": context,
                "recommended_next_action": "Continue from task.next_step. Do not repeat completed searches, reads, commands, tests, or builds.",
            }

        if workflow == "document":
            document_args = dict(args.get("document", {}))
            if not document_args:
                document_args = {key: args[key] for key in ("action", "path", "paths", "source", "target", "title", "content", "overwrite", "max_chars") if key in args}
            result = self.document_workflow(document_args)
            return {"workflow": workflow, "phase": phase, "result": result, "task": self.task_state.get()}

        objective = objective or f"Complete {workflow} workflow"
        ctx, initial_identity = self._agent_orchestration_context(args, objective=objective)
        requested_mode = str(args.get("execution_mode", "auto")).strip().lower() or "auto"
        requested_execution_route = str(args.get("execution_route", "auto")).strip().lower() or "auto"
        if requested_mode == "mcp_only":
            requested_execution_route = "deterministic"
        elif requested_mode == "deep_single_lane" and requested_execution_route == "auto":
            requested_execution_route = "sol_xhigh"
        if requested_mode == "coordinated_multi_worktree" and phase in {"execute", "run"}:
            self.orchestration_control.record_failure(
                ctx,
                "SUPERVISOR_NOT_READY",
                payload={"reason": "No production multi-worktree supervisor adapter is registered in Coding Tools MCP."},
            )
            self._project_orchestration(ctx, event="coordination_not_ready")
            self.task_state.update({
                "status": "waiting",
                "failure": "SUPERVISOR_NOT_READY",
                "current_step": "Replan execution mode",
                "next_step": "Provide replan_reason and select deep_single_lane or activate a verified coordination adapter.",
            })
            return {
                "workflow": workflow,
                "phase": phase,
                "execution": {"ok": False, "status": "blocked", "reason": "SUPERVISOR_NOT_READY"},
                "orchestration": self._orchestration_result(ctx),
                "task": self.task_state.get(),
            }

        should_prepare = phase in {"prepare", "run"}
        should_execute = phase in {"execute", "run"}
        prepared = None
        if should_prepare:
            prepared = self.prepare_coding_context({
                "objective": objective,
                "path": args.get("path", "."),
                "queries": args.get("queries", []),
                "paths": args.get("paths", []),
                "regex": args.get("regex", False),
                "case_sensitive": args.get("case_sensitive", False),
                "include_globs": args.get("include_globs", []),
                "exclude_globs": args.get("exclude_globs", []),
                "max_files": args.get("max_files", 12),
                "max_entries": args.get("max_entries", 120),
                "max_matches_per_query": args.get("max_matches_per_query", 20),
                "max_total_bytes": args.get("max_total_bytes", 262144),
                "force_refresh": args.get("force_refresh", False),
            })
            self.orchestration_ledger.append_event(
                ctx.run_id,
                wave_id=ctx.wave_id,
                event_type="context_prepared",
                state_before=ctx.state,
                state_after=ctx.state,
                payload={
                    "selected_paths": list(prepared.get("selected_paths") or [])[:40] if isinstance(prepared, dict) else [],
                    "total_content_bytes": int(prepared.get("total_content_bytes") or 0) if isinstance(prepared, dict) else 0,
                    "queries": len(args.get("queries", [])),
                },
            )
        if not should_execute:
            self._project_orchestration(ctx, event="orchestration_prepared")
            return {
                "workflow": workflow,
                "phase": "prepare",
                "context": prepared,
                "orchestration": self._orchestration_result(ctx, write_reports=False),
                "recommended_next_action": "Reason once over this bundle, then call agent_workflow phase=execute with the complete change set and verification plan.",
            }

        directories = [str(item).strip() for item in args.get("directories", []) if str(item).strip()]
        patches = [str(item) for item in args.get("patches", []) if str(item).strip()]
        if str(args.get("patch", "")).strip():
            patches.insert(0, str(args["patch"]))
        new_file_patch = self._new_files_patch(list(args.get("files", [])))
        if new_file_patch:
            patches.insert(0, new_file_patch)
        default_verification = {
            "bugfix": "tests", "feature": "tests", "greenfield": "all", "refactor": "tests",
            "test_failure": "tests", "build_release": "all", "diagnose": "none", "custom": "tests",
        }[workflow]
        verification = str(args.get("verification", default_verification)).lower()

        explicit_model_route = requested_execution_route not in {"auto", "deterministic"}
        execution_route: dict[str, Any]
        candidate_result: dict[str, Any] | None = None
        candidate_proof: dict[str, Any] = {
            "verification": verification,
            "commands": list(args.get("commands", args.get("checks", [])))[:6],
            "test_command": str(args.get("test_command", "")),
            "build_command": str(args.get("build_command", "")),
        }
        strong_oracle = False
        candidate_branch = not patches and (phase == "run" or explicit_model_route) and not directories
        if candidate_branch:
            if prepared is None:
                prepared = self.prepare_coding_context({
                    "objective": objective,
                    "path": args.get("path", "."),
                    "queries": args.get("queries", []),
                    "paths": args.get("paths", []),
                    "max_files": args.get("max_files", 12),
                    "max_entries": args.get("max_entries", 120),
                    "max_matches_per_query": args.get("max_matches_per_query", 20),
                    "max_total_bytes": args.get("max_total_bytes", 262144),
                    "force_refresh": args.get("force_refresh", False),
                })
            preflight_timeout_ms = min(max(int(args.get("timeout_seconds", 600)) * 1_000, 1_000), 120_000)
            candidate_workdir = str(args.get("workdir", args.get("path", ".")))
            if candidate_proof["test_command"]:
                candidate_proof["preflight_test"] = self._run_continuous_check(candidate_proof["test_command"], candidate_workdir, preflight_timeout_ms)
            elif candidate_proof["build_command"]:
                candidate_proof["preflight_build"] = self._run_continuous_check(candidate_proof["build_command"], candidate_workdir, preflight_timeout_ms)
            strong_oracle = any(
                isinstance(candidate_proof.get(key), dict) and candidate_proof[key].get("exit_code") not in {None, 0}
                for key in ("preflight_test", "preflight_build")
            )
            self.orchestration_ledger.append_event(
                ctx.run_id,
                wave_id=ctx.wave_id,
                event_type="oracle_preflight",
                state_before=ctx.state,
                state_after=ctx.state,
                payload={"strong_oracle": strong_oracle, "verification": verification},
            )

        if patches:
            execution_route = {
                "requested": requested_execution_route,
                "selected": "deterministic",
                "reason": "caller_supplied_change_set",
                "profile": None,
                "model": None,
                "effort": None,
                "high_cost": False,
            }
        else:
            execution_route = self._select_agent_execution_route(
                workflow=workflow,
                prepared=prepared,
                requested=requested_execution_route,
                allow_high_cost=bool(args.get("allow_high_cost", False)),
                strong_oracle=strong_oracle,
            )

        try:
            resolved_mode = self._validate_execution_mode_route(requested_mode, execution_route)
        except ToolFailure as exc:
            self.orchestration_control.record_failure(ctx, exc.code, payload={"selected_route": execution_route.get("selected")})
            self._project_orchestration(ctx, event="mode_route_mismatch")
            raise
        self.orchestration_control.resolve_execution_mode(ctx, resolved_mode)
        if ctx.state == "PREFLIGHT":
            self.orchestration_control.mark_ready(ctx, readiness={"ready": True, "base_head": ctx.base_head, "worktree_fp": ctx.worktree_fp})
        self.orchestration_control.select_route(ctx, execution_route)
        self._project_orchestration(ctx, event="orchestration_routed")

        if candidate_branch and execution_route.get("selected") != "deterministic":
            allowed_scope = list(prepared.get("selected_paths") or []) if isinstance(prepared, dict) else []
            self.orchestration_control.start_delegation(
                ctx,
                authority_owner=f"CODEX:{execution_route.get('selected')}",
                route=execution_route,
                allowed_scope=allowed_scope,
                metadata={"candidate_only": True, "authoritative_write": False},
            )
            candidate_result = self._generate_agent_candidate(
                workflow=workflow,
                objective=objective,
                prepared=prepared or {},
                requested_route=requested_execution_route,
                allow_high_cost=bool(args.get("allow_high_cost", False)),
                proof=candidate_proof,
                routing=execution_route,
                orchestration_ctx=ctx,
            )
            self.orchestration_control.finish_delegation(
                ctx,
                status="accepted_candidate" if candidate_result.get("status") == "ready" else "blocked",
                metadata={
                    "candidate_status": candidate_result.get("status"),
                    "reason": candidate_result.get("reason"),
                    "wall_time_ms": candidate_result.get("wall_time_ms"),
                    "economics": candidate_result.get("economics"),
                },
            )
            execution_route = dict(candidate_result.get("routing") or execution_route)
            execution_route.update({
                "candidate_status": candidate_result.get("status"),
                "model_status": candidate_result.get("model_status"),
                "wall_time_ms": candidate_result.get("wall_time_ms"),
                "economics": candidate_result.get("economics"),
                "deadline_hit": candidate_result.get("deadline_hit", False),
                "summary": candidate_result.get("summary"),
                "confidence": candidate_result.get("confidence"),
            })
            if candidate_result.get("status") == "ready":
                budget = args.get("_admission_budget") if isinstance(args.get("_admission_budget"), dict) else {}
                economics = candidate_result.get("economics") if isinstance(candidate_result.get("economics"), dict) else {}
                estimated_credits = economics.get("estimated_credits")
                credit_cap = float(budget.get("max_estimated_credits") or 0.0)
                if credit_cap > 0 and isinstance(estimated_credits, (int, float)) and float(estimated_credits) > credit_cap:
                    self.orchestration_control.record_failure(
                        ctx,
                        "WORKFLOW_CREDIT_BUDGET_EXCEEDED",
                        payload={"estimated_credits": float(estimated_credits), "max_estimated_credits": credit_cap},
                        block=True,
                    )
                    self._project_orchestration(ctx, event="credit_budget_exceeded")
                    raise ToolFailure(
                        "WORKFLOW_CREDIT_BUDGET_EXCEEDED",
                        "The candidate route exceeded the configured estimated-credit budget before mutation.",
                        category="policy",
                        details={"estimated_credits": float(estimated_credits), "max_estimated_credits": credit_cap},
                    )
                patches.extend(str(item) for item in candidate_result.get("patches", []) if str(item).strip())
            elif candidate_result.get("status") != "deterministic":
                if ctx.state not in {"REPLAN", "BLOCKED", "ABORTED"}:
                    self.orchestration_control.record_failure(ctx, candidate_result.get("reason", "CANDIDATE_NOT_READY"))
                self._project_orchestration(ctx, event="candidate_blocked")
                self.task_state.update({
                    "status": "waiting",
                    "failure": str(candidate_result.get("reason") or "candidate_not_ready"),
                    "current_step": "Replan required",
                    "next_step": "Provide replan_reason with new evidence/scope/route; do not retry unchanged.",
                })
                execution = {
                    "ok": False,
                    "status": "blocked",
                    "reason": candidate_result.get("reason", "candidate_not_ready"),
                    "recommended_next_action": candidate_result.get(
                        "recommended_next_action",
                        "Return the blocked candidate evidence to ChatWeb Sol and explicitly replan; do not run a serial model cascade.",
                    ),
                }
                return {
                    "workflow": workflow,
                    "phase": "run" if phase == "run" else "execute",
                    "prepared": prepared,
                    "directories": None,
                    "execution_route": execution_route,
                    "execution": execution,
                    "external_review": {"plane": "none", "status": "skipped", "reason": "execution_not_accepted"},
                    "orchestration": self._orchestration_result(ctx),
                    "task": self.task_state.get(),
                }

        identity_before_write = self._orchestration_workspace_identity(args.get("path", "."))
        if (
            (ctx.base_head and ctx.base_head != str(identity_before_write.get("base_head") or ""))
            or (ctx.worktree_fp and ctx.worktree_fp != str(identity_before_write.get("worktree_fp") or ""))
        ):
            self.orchestration_control.record_failure(ctx, "BASE_DRIFT", payload={"stage": "before_write"})
            self._project_orchestration(ctx, event="base_drift_before_write")
            self.task_state.update({"status": "waiting", "failure": "BASE_DRIFT", "next_step": "Replan against the current base/worktree."})
            return {
                "workflow": workflow,
                "phase": "run" if phase == "run" else "execute",
                "prepared": prepared,
                "execution_route": execution_route,
                "execution": {"ok": False, "status": "blocked", "reason": "BASE_DRIFT"},
                "orchestration": self._orchestration_result(ctx),
                "task": self.task_state.get(),
            }

        allowed_write_paths = list(candidate_result.get("allowed_paths") or []) if isinstance(candidate_result, dict) else []
        self.orchestration_control.acquire_write_lease(
            ctx,
            owner="MCP",
            mode=resolved_mode,
            allowed_paths=allowed_write_paths,
            delegation_id=ctx.delegation_id,
        )
        self._project_orchestration(ctx, event="mcp_write_lease_active")

        directory_result = None
        try:
            if directories:
                self.orchestration_control.assert_write_allowed(ctx, owner="MCP")
                directory_result = self.file_batch({
                    "operations": [{"action": "mkdir", "path": path, "parents": True, "exist_ok": True} for path in directories],
                    "dry_run": args.get("dry_run", False),
                })
            execution = self.apply_changes_and_verify({
                "objective": objective,
                "patches": patches,
                "checks": args.get("commands", args.get("checks", [])),
                "path": args.get("path", "."),
                "workdir": args.get("workdir", args.get("path", ".")),
                "verification": verification,
                "test_command": args.get("test_command", ""),
                "build_command": args.get("build_command", ""),
                "artifact_paths": args.get("artifact_paths", []),
                "hash_algorithm": args.get("hash_algorithm", "sha256"),
                "timeout_ms": args.get("timeout_ms", 600000),
                "timeout_seconds": args.get("timeout_seconds", 600),
                "include_diff": args.get("include_diff", True),
                "max_diff_bytes": args.get("max_diff_bytes", 131072),
                "dry_run": args.get("dry_run", False),
                "_orchestration_context": ctx,
            })
        except (ToolFailure, OrchestrationControlError) as exc:
            code = getattr(exc, "code", type(exc).__name__)
            if ctx.state not in {"REPLAN", "BLOCKED", "ABORTED"}:
                self.orchestration_control.record_failure(ctx, code)
            self._project_orchestration(ctx, event="execution_exception")
            self.task_state.update({"status": "waiting", "failure": str(code), "current_step": "Replan required", "next_step": "Provide replan_reason after correcting the failure cause."})
            raise

        if not execution.get("ok"):
            error = execution.get("error") if isinstance(execution.get("error"), dict) else {}
            if ctx.state not in {"REPLAN", "BLOCKED", "ABORTED"}:
                self.orchestration_control.record_failure(ctx, error.get("code") or execution.get("reason") or "EXECUTION_FAILED")
            self._project_orchestration(ctx, event="execution_failed")
            result = {
                "workflow": workflow,
                "phase": "run" if phase == "run" else "execute",
                "prepared": prepared,
                "directories": directory_result,
                "execution_route": execution_route,
                "execution": execution,
                "external_review": {"plane": "none", "status": "skipped", "reason": "execution_not_accepted"},
                "orchestration": self._orchestration_result(ctx),
                "task": self.task_state.get(),
            }
            return result

        self._invalidate_fast_cache()
        external_review = self._maybe_agent_workflow_external_review(
            workflow=workflow,
            objective=objective,
            verification=verification,
            execution=execution,
            dry_run=bool(args.get("dry_run", False)),
        )
        if ctx.state == "PROVING":
            self.orchestration_control.mark_accepting(
                ctx,
                proof_summary={
                    **(execution.get("proof_summary") or {}),
                    "external_review_plane": external_review.get("plane"),
                    "external_review_status": external_review.get("status"),
                },
            )
        self._project_orchestration(ctx, event="awaiting_final_acceptance")
        self.task_state.update({
            "status": "waiting",
            "current_step": "Waiting for ChatWeb Sol acceptance",
            "next_step": "Inspect diff/proof/review, then call task_control action=accept or reject.",
            "failure": None,
            "orchestration": ctx.projection(),
        }, event="final_acceptance_required")
        result = {
            "workflow": workflow,
            "phase": "run" if phase == "run" else "execute",
            "prepared": prepared,
            "directories": directory_result,
            "execution_route": execution_route,
            "execution": execution,
            "external_review": external_review,
            "orchestration": self._orchestration_result(ctx),
            "task": self.task_state.get(),
        }
        self._fast_cache_put(dedup_key, result)
        return result

    def read_files(self, args: dict[str, Any]) -> dict[str, Any]:
        raw_items = args.get("files")
        if raw_items is None:
            raw_items = args.get("paths", [])
        if not isinstance(raw_items, list) or not raw_items:
            raise ToolFailure("INVALID_ARGUMENT", "files or paths must be a non-empty list.", category="validation")
        results: list[dict[str, Any]] = []
        total_bytes = 0
        max_total = min(max(int(args.get("max_total_bytes", 262144)), 1024), 1048576)
        for item in raw_items[:50]:
            spec = {"path": item} if isinstance(item, str) else dict(item) if isinstance(item, dict) else None
            if not spec or not spec.get("path"):
                continue
            remaining = max_total - total_bytes
            if remaining <= 0:
                break
            spec["max_bytes"] = min(int(spec.get("max_bytes", 131072)), remaining)
            payload = self.read_file(spec)
            total_bytes += len(str(payload.get("content", "")).encode("utf-8"))
            results.append(payload)
        return {"files": results, "count": len(results), "total_content_bytes": total_bytes, "truncated": len(results) < len(raw_items)}

    def file_batch(self, args: dict[str, Any]) -> dict[str, Any]:
        operations = args.get("operations", [])
        if not isinstance(operations, list) or not operations:
            raise ToolFailure("INVALID_ARGUMENT", "operations must be a non-empty list.", category="validation")
        dry_run = bool(args.get("dry_run", False))
        results: list[dict[str, Any]] = []
        affected: list[dict[str, str]] = []
        for item in operations[:100]:
            if not isinstance(item, dict):
                raise ToolFailure("INVALID_ARGUMENT", "Each operation must be an object.", category="validation")
            action = str(item.get("action", "")).lower()
            source_raw = str(item.get("path", item.get("source", "")))
            if action == "mkdir":
                target = self.resolve_for_write(source_raw)
                if not dry_run:
                    target.path.mkdir(parents=bool(item.get("parents", True)), exist_ok=bool(item.get("exist_ok", True)))
                results.append({"action": action, "path": target.display})
                affected.append({"path": target.display, "operation": "mkdir"})
                continue
            source = self.resolve_existing(source_raw)
            if action in {"copy", "move"}:
                target = self.resolve_for_write(str(item.get("target", "")))
                if not dry_run:
                    target.path.parent.mkdir(parents=True, exist_ok=True)
                    if target.path.exists() and not bool(item.get("overwrite", False)):
                        raise FileExistsError(target.path)
                    if action == "copy":
                        shutil.copytree(source.path, target.path, dirs_exist_ok=bool(item.get("overwrite", False))) if source.path.is_dir() else shutil.copy2(source.path, target.path)
                    else:
                        if target.path.exists() and not bool(item.get("overwrite", False)):
                            raise FileExistsError(target.path)
                        shutil.move(str(source.path), str(target.path))
                results.append({"action": action, "source": source.display, "target": target.display})
                affected.append({"path": target.display, "operation": action})
            elif action == "delete":
                if not dry_run:
                    if source.path.is_dir():
                        if any(source.path.iterdir()):
                            raise ToolFailure("DIRECTORY_NOT_EMPTY", "Batch delete only removes empty directories.", category="validation", details={"path": source.display})
                        source.path.rmdir()
                    else:
                        source.path.unlink()
                results.append({"action": action, "path": source.display})
                affected.append({"path": source.display, "operation": "delete"})
            else:
                raise ToolFailure("INVALID_ARGUMENT", f"Unknown batch action: {action}", category="validation")
        return {"dry_run": dry_run, "results": results, "count": len(results), "affected_files": [] if dry_run else affected}

    def _coordination_ids(self, args: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], str, str]:
        state = self.task_state.get()
        projection = state.get("orchestration") if isinstance(state.get("orchestration"), dict) else {}
        run_id = str(args.get("run_id") or projection.get("run_id") or "").strip()
        wave_id = str(args.get("wave_id") or projection.get("wave_id") or "").strip()
        return state, projection, run_id, wave_id

    @staticmethod
    def _coordination_lane_outcome(bridge_result: dict[str, Any]) -> dict[str, Any]:
        observation = bridge_result.get("observation") if isinstance(bridge_result.get("observation"), dict) else {}
        status = str(observation.get("status") or bridge_result.get("status") or "unknown")
        terminal = bool(observation.get("terminal")) or status in {
            "completed",
            "failed",
            "interrupted",
            "deadline",
        }
        text = str(observation.get("agent_text") or "").strip()
        try:
            parsed = json.loads(text) if text else None
        except (TypeError, ValueError, json.JSONDecodeError):
            parsed = None
        if isinstance(parsed, dict):
            response = {
                "status": str(parsed.get("status") or "blocked"),
                "summary": str(parsed.get("summary") or "")[:2_000],
                "question": str(parsed.get("question") or "")[:1_000] or None,
                "findings": [str(item)[:700] for item in list(parsed.get("findings") or [])[:8]],
                "missing_proof": [str(item)[:700] for item in list(parsed.get("missing_proof") or [])[:8]],
                "next_action": str(parsed.get("next_action") or "")[:1_000],
                "confidence": str(parsed.get("confidence") or "low"),
            }
        elif text:
            response = {
                "status": "blocked",
                "summary": "Codex returned an unstructured response.",
                "question": None,
                "findings": [],
                "missing_proof": ["structured_lane_output"],
                "next_action": "Review the bounded agent_text and repacket instead of retrying unchanged.",
                "confidence": "low",
                "agent_text": text[:4_000],
            }
        else:
            response = {
                "status": "blocked" if terminal else "running",
                "summary": "No terminal structured result is available yet.",
                "question": None,
                "findings": [],
                "missing_proof": [],
                "next_action": "Poll the lane with task_control action=lane lane_action=observe.",
                "confidence": "low",
            }
        return {
            "status": status,
            "terminal": terminal,
            "thread_id": str(bridge_result.get("thread_id") or ""),
            "turn_id": str(bridge_result.get("turn_id") or observation.get("turn_id") or ""),
            "session_id": str(bridge_result.get("session_id") or ""),
            "lifetime": str(bridge_result.get("lifetime") or "persistent"),
            "creation_mode": bridge_result.get("creation_mode"),
            "route": observation.get("route") or bridge_result.get("route"),
            "wall_time_ms": observation.get("wall_time_ms"),
            "economics": observation.get("economics"),
            "deadline_hit": bool(observation.get("deadline_hit", bridge_result.get("deadline_hit", False))),
            "error": observation.get("error"),
            "response": response,
        }

    def _record_coordination_lane_outcome(
        self,
        lane: dict[str, Any],
        bridge_result: dict[str, Any],
    ) -> dict[str, Any]:
        outcome = self._coordination_lane_outcome(bridge_result)
        response = outcome["response"]
        if not outcome["terminal"]:
            lifecycle = "active"
        elif outcome["status"] == "completed" and response.get("status") == "completed":
            lifecycle = "idle"
        else:
            lifecycle = "waiting"
        route = outcome.get("route") if isinstance(outcome.get("route"), dict) else {}
        lane_id = str(lane["lane_id"])
        updated = self.orchestration_ledger.update_agent_lane(
            lane_id,
            lifecycle=lifecycle,
            thread_id=outcome.get("thread_id") or lane.get("thread_id") or "",
            session_id=outcome.get("session_id") or lane.get("session_id") or "",
            last_turn_id=outcome.get("turn_id") or lane.get("last_turn_id") or "",
            profile=str(route.get("profile") or lane.get("profile") or ""),
            model=str(route.get("model") or lane.get("model") or ""),
            effort=str(route.get("effort") or lane.get("effort") or ""),
            metadata={
                "last_bridge_status": outcome["status"],
                "deadline_hit": outcome["deadline_hit"],
                "last_wall_time_ms": outcome.get("wall_time_ms"),
                "last_economics": outcome.get("economics"),
                "owner_process_instance_id": self.process_instance_id,
            },
        ) or lane
        if outcome["terminal"] and outcome.get("turn_id"):
            kind = "question" if response.get("question") else "result"
            stable_id = hashlib.sha256(
                f"{lane_id}:{outcome['turn_id']}:{kind}".encode("utf-8")
            ).hexdigest()
            self.orchestration_ledger.append_coordination_message(
                message_id=stable_id,
                run_id=str(updated.get("run_id") or ""),
                wave_id=str(updated.get("wave_id") or ""),
                lane_id=lane_id,
                direction="codex_to_chatweb",
                kind=kind,
                status="pending",
                base_head=str(updated.get("base_head") or ""),
                worktree_fp=str(updated.get("worktree_fp") or ""),
                payload={
                    "turn_id": outcome["turn_id"],
                    "bridge_status": outcome["status"],
                    "response": response,
                    "error": outcome.get("error"),
                    "economics": outcome.get("economics"),
                    "deadline_hit": outcome.get("deadline_hit"),
                },
            )
        return {"lane": updated, "outcome": outcome}

    def _coordination_lane(self, args: dict[str, Any]) -> dict[str, Any]:
        state, projection, run_id, wave_id = self._coordination_ids(args)
        lane_action = str(args.get("lane_action") or "list").strip().lower()
        if lane_action == "list":
            return {
                "state": state,
                "lanes": self.orchestration_ledger.list_agent_lanes(
                    run_id=run_id,
                    lifecycle=str(args.get("lifecycle") or "").strip(),
                ),
            }

        semantic_key = str(args.get("semantic_key") or "").strip()
        lane_id = str(args.get("lane_id") or "").strip()
        lane = self.orchestration_ledger.get_agent_lane(lane_id) if lane_id else None
        if lane is None and semantic_key and run_id:
            lane = self.orchestration_ledger.find_agent_lane(
                run_id=run_id,
                semantic_key=semantic_key,
            )

        if lane_action == "start":
            if not semantic_key:
                raise ToolFailure(
                    "SEMANTIC_KEY_REQUIRED",
                    "semantic_key is required when lane_action=start.",
                    category="validation",
                )
            if lane is not None:
                return {
                    "status": "existing_lane",
                    "lane": lane,
                    "recommended_next_action": "Use lane_action=continue; duplicate persistent lanes are not auto-created.",
                }
            prompt = str(args.get("prompt") or "").strip()
            if not prompt:
                raise ToolFailure("PROMPT_REQUIRED", "prompt is required when lane_action=start.", category="validation")
            profile = str(args.get("profile") or "cross_file").strip().lower()
            lane_id = lane_id or secrets.token_urlsafe(12)
            identity = self._orchestration_workspace_identity(".")
            contract_fp = str(args.get("contract_fingerprint") or projection.get("contract_fp") or "")
            claimed_lane_id = self.orchestration_ledger.upsert_agent_lane(
                lane_id=lane_id,
                run_id=run_id,
                wave_id=wave_id,
                semantic_key=semantic_key,
                role=str(args.get("role") or "executor")[:100],
                lifecycle="starting",
                profile=profile,
                model=str(args.get("model") or ""),
                effort=str(args.get("effort") or ""),
                base_head=str(identity.get("base_head") or ""),
                worktree_fp=str(identity.get("worktree_fp") or ""),
                contract_fp=contract_fp,
                metadata={
                    "created_by": "ChatWeb Sol",
                    "conversation_epoch": args.get("conversation_epoch", 1),
                    "owner_process_instance_id": self.process_instance_id,
                },
            )
            if claimed_lane_id != lane_id:
                existing_lane = self.orchestration_ledger.get_agent_lane(claimed_lane_id)
                return {
                    "status": "existing_lane",
                    "lane": existing_lane,
                    "recommended_next_action": "Use lane_action=continue; a concurrent caller already claimed this semantic lane.",
                }
            lane = self.orchestration_ledger.get_agent_lane(lane_id) or {"lane_id": lane_id}
            self.orchestration_ledger.append_coordination_message(
                run_id=run_id,
                wave_id=wave_id,
                lane_id=lane_id,
                direction="chatweb_to_codex",
                kind="instruction",
                base_head=str(identity.get("base_head") or ""),
                worktree_fp=str(identity.get("worktree_fp") or ""),
                payload={
                    "prompt": prompt,
                    "summary": str(args.get("summary") or semantic_key)[:1_000],
                    "profile": profile,
                },
            )
            try:
                bridge_result = self._codex_bridge.run(
                    prompt,
                    profile=profile,
                    model=str(args.get("model") or "").strip() or None,
                    effort=str(args.get("effort") or "").strip().lower() or None,
                    lifetime="persistent",
                    deadline_ms=max(0, min(int(args.get("deadline_ms", 0)), 30_000)),
                    output_schema=COORDINATION_LANE_OUTPUT_SCHEMA,
                    wait_ms=max(0, min(int(args.get("wait_ms", 0)), 30_000)),
                )
            except CodexBridgeError as exc:
                updated = self.orchestration_ledger.update_agent_lane(
                    lane_id,
                    lifecycle="waiting",
                    metadata={"last_error": exc.code, "retryable": exc.retryable},
                ) or lane
                self.orchestration_ledger.append_coordination_message(
                    run_id=run_id,
                    wave_id=wave_id,
                    lane_id=lane_id,
                    direction="codex_to_chatweb",
                    kind="error",
                    payload={"code": exc.code, "message": str(exc), "retryable": exc.retryable},
                )
                return {
                    "status": "blocked",
                    "lane": updated,
                    "error": {"code": exc.code, "message": str(exc), "retryable": exc.retryable},
                    "recommended_next_action": "Repacket or choose one policy-approved alternative; do not retry unchanged.",
                }
            route = bridge_result.get("route") if isinstance(bridge_result.get("route"), dict) else {}
            lane = self.orchestration_ledger.update_agent_lane(
                lane_id,
                lifecycle="active",
                thread_id=str(bridge_result.get("thread_id") or ""),
                session_id=str(bridge_result.get("session_id") or ""),
                last_turn_id=str(bridge_result.get("turn_id") or ""),
                profile=str(route.get("profile") or profile),
                model=str(route.get("model") or ""),
                effort=str(route.get("effort") or ""),
                metadata={"owner_process_instance_id": self.process_instance_id},
            ) or lane
            return {"status": "started", **self._record_coordination_lane_outcome(lane, bridge_result)}

        if lane is None:
            raise ToolFailure("LANE_NOT_FOUND", "The requested persistent lane was not found.", category="not_found")
        lane_id = str(lane["lane_id"])
        if lane_action == "close":
            updated = self.orchestration_ledger.update_agent_lane(
                lane_id,
                lifecycle="closed",
                metadata={"closed_reason": str(args.get("reason") or "closed_by_chatweb")[:1_000]},
            ) or lane
            self.orchestration_ledger.append_coordination_message(
                run_id=str(updated.get("run_id") or ""),
                wave_id=str(updated.get("wave_id") or ""),
                lane_id=lane_id,
                direction="system",
                kind="lane_closed",
                payload={"reason": str(args.get("reason") or "closed_by_chatweb")[:1_000]},
            )
            return {"status": "closed", "lane": updated}

        if lane_action == "observe":
            if not self._codex_bridge.owns_thread(str(lane.get("thread_id") or "")):
                return {
                    "status": "waiting",
                    "lane": lane,
                    "messages": self.orchestration_ledger.list_coordination_messages(
                        lane_id=lane_id,
                        status="pending",
                        limit=max(1, min(int(args.get("limit", 20)), 100)),
                    ),
                    "reason": "live_turn_handle_not_owned_after_runtime_rollover",
                    "recommended_next_action": "Use lane_action=continue to resume the persisted thread with a compact delta packet.",
                }
            observation = self._codex_bridge.observe(
                thread_id=str(lane.get("thread_id") or ""),
                turn_id=str(args.get("turn_id") or lane.get("last_turn_id") or "") or None,
                after_cursor=max(0, int(args.get("after_cursor", 0))),
                wait_ms=max(0, min(int(args.get("wait_ms", 0)), 30_000)),
                max_events=max(1, min(int(args.get("max_events", 50)), 100)),
            )
            bridge_result = {
                "status": observation.get("status"),
                "thread_id": lane.get("thread_id"),
                "turn_id": observation.get("turn_id") or lane.get("last_turn_id"),
                "session_id": lane.get("session_id"),
                "lifetime": "persistent",
                "route": {
                    "profile": lane.get("profile"),
                    "model": lane.get("model"),
                    "effort": lane.get("effort"),
                },
                "observation": observation,
            }
            return {"status": "observed", **self._record_coordination_lane_outcome(lane, bridge_result)}

        if lane_action != "continue":
            raise ToolFailure(
                "INVALID_LANE_ACTION",
                f"Unsupported lane_action: {lane_action}",
                category="validation",
            )
        if str(lane.get("lifecycle") or "") == "closed":
            raise ToolFailure("LANE_CLOSED", "The persistent lane is closed.", category="runtime")
        prompt = str(args.get("prompt") or "").strip()
        if not prompt:
            raise ToolFailure("PROMPT_REQUIRED", "prompt is required when lane_action=continue.", category="validation")
        identity = self._orchestration_workspace_identity(".")
        current_contract = str(args.get("contract_fingerprint") or lane.get("contract_fp") or "")
        drift = {
            "base_head": [lane.get("base_head"), identity.get("base_head")],
            "worktree_fp": [lane.get("worktree_fp"), identity.get("worktree_fp")],
            "contract_fp": [lane.get("contract_fp"), current_contract],
        }
        changed = {
            key: values for key, values in drift.items()
            if values[0] and values[1] and values[0] != values[1]
        }
        if changed and not bool(args.get("allow_rebase", False)):
            return {
                "status": "blocked",
                "lane": lane,
                "reason": "lane_base_drift",
                "drift": changed,
                "recommended_next_action": "Revalidate affected evidence, then continue with allow_rebase=true and a material reason.",
            }
        if changed:
            reason = str(args.get("reason") or "").strip()
            if not reason:
                raise ToolFailure(
                    "REBASE_REASON_REQUIRED",
                    "reason is required when allow_rebase=true and lane state drifted.",
                    category="validation",
                )
            lane = self.orchestration_ledger.update_agent_lane(
                lane_id,
                base_head=str(identity.get("base_head") or ""),
                worktree_fp=str(identity.get("worktree_fp") or ""),
                contract_fp=current_contract,
                metadata={
                    "rebase_reason": reason[:1_000],
                    "revalidated_at": datetime.now(timezone.utc).isoformat(),
                    "owner_process_instance_id": self.process_instance_id,
                },
            ) or lane
            self.orchestration_ledger.append_coordination_message(
                run_id=str(lane.get("run_id") or ""),
                wave_id=str(lane.get("wave_id") or ""),
                lane_id=lane_id,
                direction="system",
                kind="lane_rebased",
                base_head=str(identity.get("base_head") or ""),
                worktree_fp=str(identity.get("worktree_fp") or ""),
                payload={"reason": reason[:1_000], "drift": changed},
            )
        self.orchestration_ledger.append_coordination_message(
            run_id=str(lane.get("run_id") or ""),
            wave_id=str(lane.get("wave_id") or ""),
            lane_id=lane_id,
            direction="chatweb_to_codex",
            kind="instruction",
            base_head=str(lane.get("base_head") or ""),
            worktree_fp=str(lane.get("worktree_fp") or ""),
            payload={"prompt": prompt, "summary": str(args.get("summary") or "lane continuation")[:1_000]},
        )
        profile = str(args.get("profile") or lane.get("profile") or "cross_file")
        try:
            if self._codex_bridge.owns_thread(str(lane.get("thread_id") or "")):
                bridge_result = self._codex_bridge.continue_thread(
                    thread_id=str(lane.get("thread_id") or ""),
                    prompt=prompt,
                    model=str(args.get("model") or lane.get("model") or "").strip() or None,
                    effort=str(args.get("effort") or lane.get("effort") or "").strip().lower() or None,
                    deadline_ms=max(0, min(int(args.get("deadline_ms", 0)), 30_000)),
                    output_schema=COORDINATION_LANE_OUTPUT_SCHEMA,
                    wait_ms=max(0, min(int(args.get("wait_ms", 0)), 30_000)),
                )
            else:
                bridge_result = self._codex_bridge.resume_persistent_thread(
                    thread_id=str(lane.get("thread_id") or ""),
                    expected_session_id=str(lane.get("session_id") or ""),
                    prompt=prompt,
                    profile=profile,
                    model=str(args.get("model") or lane.get("model") or "").strip() or None,
                    effort=str(args.get("effort") or lane.get("effort") or "").strip().lower() or None,
                    deadline_ms=max(0, min(int(args.get("deadline_ms", 0)), 30_000)),
                    output_schema=COORDINATION_LANE_OUTPUT_SCHEMA,
                    wait_ms=max(0, min(int(args.get("wait_ms", 0)), 30_000)),
                )
        except CodexBridgeError as exc:
            updated = self.orchestration_ledger.update_agent_lane(
                lane_id,
                lifecycle="waiting",
                metadata={"last_error": exc.code, "retryable": exc.retryable},
            ) or lane
            self.orchestration_ledger.append_coordination_message(
                run_id=str(updated.get("run_id") or ""),
                wave_id=str(updated.get("wave_id") or ""),
                lane_id=lane_id,
                direction="codex_to_chatweb",
                kind="error",
                payload={"code": exc.code, "message": str(exc), "retryable": exc.retryable},
            )
            return {
                "status": "blocked",
                "lane": updated,
                "error": {"code": exc.code, "message": str(exc), "retryable": exc.retryable},
                "recommended_next_action": "Repacket or select one different route; do not retry unchanged.",
            }
        return {"status": "continued", **self._record_coordination_lane_outcome(lane, bridge_result)}

    def task_control(self, args: dict[str, Any]) -> dict[str, Any]:
        action = str(args.get("action", "get")).lower()
        if action == "get":
            with self.background_operations_lock:
                memory_operations = {
                    item["operation_id"]: self._background_operation_snapshot(item)
                    for item in self.background_operations.values()
                    if item.get("workspace") == str(self.workspace.root)
                }
            durable_operations = {
                item["operation_id"]: item
                for item in self.orchestration_ledger.list_background_operations(limit=20)
            }
            durable_operations.update(memory_operations)
            operations = sorted(
                durable_operations.values(),
                key=lambda item: str(item.get("updated_at") or item.get("started_at") or ""),
            )
            return {
                "state": self.task_state.get(),
                "operations": operations[-8:],
                "recovery": {
                    "orphaned_background_operations": self.orphaned_background_operations,
                    "orphaned_idempotency_records": self.orphaned_idempotency_records,
                    "stale_orchestration_runs": self.stale_orchestration_runs,
                    "agent_lanes_waiting_after_restart": self.recovered_agent_lanes,
                },
            }
        if action == "lane":
            return self._coordination_lane(args)
        if action == "events":
            _state, _projection, run_id, _wave_id = self._coordination_ids(args)
            if not run_id:
                raise ToolFailure("ORCHESTRATION_RUN_NOT_FOUND", "No orchestration run is associated with the current task.", category="not_found")
            replay = self.orchestration_ledger.list_events_since(
                run_id,
                after_seq=max(0, int(args.get("after_seq", 0))),
                limit=max(1, min(int(args.get("limit", 100)), 500)),
            )
            replay["recommended_next_action"] = (
                "Call task_control action=events with after_seq=next_after_seq until has_more=false."
                if replay.get("has_more")
                else "Event replay is current; continue from task state, pending messages, and the latest handoff capsule."
            )
            return replay
        if action == "messages":
            _state, _projection, run_id, _wave_id = self._coordination_ids(args)
            return {
                "messages": self.orchestration_ledger.list_coordination_messages(
                    run_id=run_id,
                    lane_id=str(args.get("lane_id") or "").strip(),
                    status=str(args.get("message_status") or "pending").strip(),
                    direction=str(args.get("direction") or "").strip(),
                    limit=max(1, min(int(args.get("limit", 20)), 100)),
                )
            }
        if action == "ack":
            message_id = str(args.get("message_id") or "").strip()
            if not message_id:
                raise ToolFailure("MESSAGE_ID_REQUIRED", "message_id is required when action=ack.", category="validation")
            message = self.orchestration_ledger.acknowledge_coordination_message(message_id)
            if message is None:
                raise ToolFailure("MESSAGE_NOT_FOUND", "The coordination message was not found.", category="not_found")
            return {"acknowledged": True, "message": message}
        if action == "handoff":
            state, projection, run_id, wave_id = self._coordination_ids(args)
            handoff_action = str(args.get("handoff_action") or "get").strip().lower()
            if handoff_action == "get":
                capsule = self.orchestration_ledger.latest_handoff_capsule(run_id=run_id)
                return {
                    "capsule": capsule,
                    "recommended_next_action": (
                        "Resume from this capsule and pending messages; do not replay the previous ChatWeb transcript."
                        if capsule else
                        "Record a bounded handoff capsule before rolling to a new ChatWeb conversation."
                    ),
                }
            if handoff_action != "record":
                raise ToolFailure("INVALID_HANDOFF_ACTION", f"Unsupported handoff_action: {handoff_action}", category="validation")
            payload = args.get("payload")
            if not isinstance(payload, dict):
                raise ToolFailure("HANDOFF_PAYLOAD_REQUIRED", "payload object is required when handoff_action=record.", category="validation")
            pending_messages = self.orchestration_ledger.list_coordination_messages(
                run_id=run_id,
                status="pending",
                limit=50,
            )
            active_lanes = self.orchestration_ledger.list_agent_lanes(run_id=run_id)
            augmented = dict(payload)
            augmented["runtime"] = {
                "task_id": state.get("task_id"),
                "objective": state.get("objective"),
                "task_status": state.get("status"),
                "current_step": state.get("current_step"),
                "next_step": state.get("next_step"),
                "run_id": run_id,
                "wave_id": wave_id,
                "orchestration_state": projection.get("orchestration_state"),
                "base_head": projection.get("base_head"),
                "worktree_fp": projection.get("worktree_fp"),
                "contract_fp": projection.get("contract_fp"),
                "active_lane_ids": [
                    row["lane_id"] for row in active_lanes
                    if row.get("lifecycle") not in {"closed"}
                ][:20],
                "pending_message_ids": [row["message_id"] for row in pending_messages][:50],
            }
            try:
                capsule = self.orchestration_ledger.record_handoff_capsule(
                    run_id=run_id,
                    wave_id=wave_id,
                    conversation_epoch=max(1, int(args.get("conversation_epoch", 1))),
                    payload=augmented,
                )
            except ValueError as exc:
                raise ToolFailure(
                    "HANDOFF_CAPSULE_TOO_LARGE",
                    str(exc),
                    category="validation",
                    details={"strategy": "Store hashes, proof ids and next actions instead of transcript or raw command output."},
                ) from exc
            return {
                "recorded": True,
                "capsule": capsule,
                "recommended_next_action": "Open a fresh ChatWeb conversation, fetch this capsule, then poll pending messages.",
            }
        if action in {"audit", "accept", "reject"}:
            state = self.task_state.get()
            projection = state.get("orchestration") if isinstance(state.get("orchestration"), dict) else {}
            run_id = str(args.get("run_id") or projection.get("run_id") or "").strip()
            if not run_id:
                raise ToolFailure("ORCHESTRATION_RUN_NOT_FOUND", "No orchestration run is associated with the current task.", category="not_found")
            ctx = self.orchestration_control.snapshot(run_id)
            if ctx is None:
                raise ToolFailure("ORCHESTRATION_RUN_NOT_FOUND", "The requested orchestration run was not found.", category="not_found")
            if action == "audit":
                reports = self.orchestration_report.write_reports(run_id)
                summary = self.orchestration_ledger.export_summary(run_id)
                limit = max(1, min(int(args.get("limit", 20)), 100))
                summary["events"] = summary.get("events", [])[-limit:]
                summary["proofs"] = summary.get("proofs", [])[-limit:]
                return {
                    "state": state,
                    "orchestration": self._orchestration_result(ctx, write_reports=False),
                    "audit": summary,
                    "reports": reports,
                }
            if action == "accept":
                if ctx.state != "ACCEPTING":
                    raise ToolFailure(
                        "FINAL_ACCEPTANCE_NOT_READY",
                        f"Run is in {ctx.state}, not ACCEPTING.",
                        category="runtime",
                        retryable=True,
                        details={"run_id": run_id, "wave_id": ctx.wave_id, "state": ctx.state},
                    )
                proofs = self.orchestration_ledger.list_proofs(run_id, wave_id=ctx.wave_id)
                proof_fp = hashlib.sha256(
                    "|".join(f"{item['proof_id']}:{item['input_fingerprint']}" for item in proofs).encode("utf-8")
                ).hexdigest() if proofs else ""
                identity = self._orchestration_workspace_identity(".")
                self.orchestration_control.checkpoint(ctx, reason="chatweb_sol_acceptance")
                self.orchestration_ledger.record_checkpoint(
                    run_id=run_id,
                    wave_id=ctx.wave_id,
                    git_head=str(identity.get("base_head") or ""),
                    proof_fingerprint=proof_fp,
                    status="accepted",
                    metadata={"accepted_by": "ChatWeb Sol", "worktree_fp": identity.get("worktree_fp")},
                )
                self._project_orchestration(ctx, event="final_acceptance_recorded")
                accepted_state = self.task_state.update({
                    "status": "completed",
                    "current_step": "Completed",
                    "next_step": "Start the next accepted behavior or checkpoint the repository according to project policy.",
                    "failure": None,
                    "orchestration": ctx.projection(),
                }, event="task_accepted")
                return {
                    "accepted": True,
                    "state": accepted_state,
                    "orchestration": self._orchestration_result(ctx),
                }
            reason = str(args.get("reason", "")).strip()
            if not reason:
                raise ToolFailure("REJECTION_REASON_REQUIRED", "reason is required when action=reject.", category="validation")
            if ctx.state != "ACCEPTING":
                raise ToolFailure(
                    "FINAL_ACCEPTANCE_NOT_READY",
                    f"Run is in {ctx.state}, not ACCEPTING.",
                    category="runtime",
                    retryable=True,
                    details={"run_id": run_id, "wave_id": ctx.wave_id, "state": ctx.state},
                )
            self.orchestration_control.record_failure(ctx, "SOL_REJECTED", payload={"reason": reason})
            self._project_orchestration(ctx, event="final_acceptance_rejected")
            rejected_state = self.task_state.update({
                "status": "waiting",
                "current_step": "Replan required",
                "next_step": "Provide replan_reason and a changed evidence/scope/strategy before another execution wave.",
                "failure": reason,
                "orchestration": ctx.projection(),
            }, event="task_rejected")
            return {
                "rejected": True,
                "state": rejected_state,
                "orchestration": self._orchestration_result(ctx),
            }
        if action == "operation":
            operation_id = str(args.get("operation_id", "")).strip()
            if not operation_id:
                raise ToolFailure("INVALID_ARGUMENT", "operation_id is required when action=operation.", category="validation")
            with self.background_operations_lock:
                operation = self.background_operations.get(operation_id)
                if operation is not None and operation.get("workspace") != str(self.workspace.root):
                    operation = None
            if operation is None:
                durable = self.orchestration_ledger.get_background_operation(operation_id)
                if durable is None:
                    raise ToolFailure("NOT_FOUND", "Background operation was not found.", category="runtime", retryable=False)
                if durable.get("status") == "running":
                    durable = self.orchestration_ledger.finish_background_operation(
                        operation_id,
                        status="orphaned",
                        summary={"orphan_reason": "in_memory_handle_missing"},
                    ) or durable
                durable = dict(durable)
                durable["durable_only"] = True
                durable["requires_progress_report"] = False
                if durable.get("status") == "orphaned":
                    durable["message"] = (
                        "The MCP runtime that owned this operation is gone. Resume from durable task/proof/lane state; "
                        "do not assume the Python worker is still running."
                    )
                elif durable.get("status") == "completed":
                    durable["message"] = "The durable summary is available, but the prior runtime's full result payload is not retained."
                return {"state": self.task_state.get(), "background_operation": durable}
            wait_ms = min(max(int(args.get("wait_ms", 0)), 0), BACKGROUND_OPERATION_WAIT_MAX_MS)
            if wait_ms and not operation["event"].is_set():
                operation["event"].wait(wait_ms / 1000)
            snapshot = self._background_operation_snapshot(operation, include_result=True)
            if snapshot["status"] == "running":
                snapshot["message"] = "Operation is still running. Report progress to the user before waiting again."
            return {"state": self.task_state.get(), "background_operation": snapshot}
        if action == "history":
            return {"tasks": self.task_state.history(int(args.get("limit", 20)))}
        if action == "clear":
            return {"state": self.task_state.clear(), "cleared": True}
        if action == "start":
            objective = str(args.get("objective", "")).strip()
            if not objective:
                raise ToolFailure("INVALID_ARGUMENT", "objective is required when action=start.", category="validation")
            changes = {
                "objective": objective,
                "steps": args.get("steps", []),
                "current_step": args.get("current_step", ""),
                "next_step": args.get("next_step", ""),
                "status": "active",
                "failure": None,
                "new_task": True,
            }
            return {"state": self.task_state.update(changes, event="task_started")}
        if action == "update":
            changes = {key: args[key] for key in ("objective", "steps", "current_step", "next_step", "status", "failure", "complete_step_ids") if key in args}
            return {"state": self.task_state.update(changes)}
        if action == "pause":
            state = self.task_state.pause(str(args.get("reason", "Paused by user")))
            current = state.get("current_command") if isinstance(state, dict) else None
            if isinstance(current, dict) and current.get("session_id"):
                try:
                    self.kill_session({"session_id": str(current["session_id"]), "signal": "TERM", "wait_ms": 1000})
                except ToolFailure:
                    pass
            return {"state": self.task_state.get(), "paused": True}
        if action == "resume":
            return {"state": self.task_state.resume(str(args.get("next_step", "")))}
        if action == "stop":
            state = self.task_state.update({"status": "stopped", "failure": str(args.get("reason", "Stopped by user")), "next_step": str(args.get("next_step", "Resume or start a new task."))}, event="task_stopped")
            current = state.get("current_command") if isinstance(state, dict) else None
            if isinstance(current, dict) and current.get("session_id"):
                try:
                    self.kill_session({"session_id": str(current["session_id"]), "signal": "TERM", "wait_ms": 1000})
                except ToolFailure:
                    pass
            return {"state": state, "stopped": True}
        raise ToolFailure("INVALID_ARGUMENT", f"Unknown task action: {action}", category="validation")

    def _command_handle(self, args: dict[str, Any]) -> str:
        command_id = str(args.get("command_id", "") or "").strip()
        session_id = str(args.get("session_id", "") or "").strip()
        if command_id and session_id and command_id != session_id:
            raise ToolFailure(
                "INVALID_ARGUMENT",
                "command_id and deprecated session_id identify different commands.",
                category="validation",
            )
        handle = command_id or session_id
        if not handle:
            raise ToolFailure("INVALID_ARGUMENT", "command_id is required.", category="validation")
        return handle

    def command_control(self, args: dict[str, Any]) -> dict[str, Any]:
        action = str(args.get("action", "poll")).lower()
        if not str(args.get("command_id", "")).strip() and str(args.get("session_id", "")).strip():
            with self.sessions_lock:
                self.legacy_session_alias_uses += 1
        command_id = self._command_handle(args) if action in {"poll", "write", "kill"} else ""
        if action in {"poll", "write"}:
            return self.write_stdin({
                "command_id": command_id,
                "chars": str(args.get("chars", "")) if action == "write" else "",
                "yield_time_ms": args.get("yield_time_ms", 10000),
                "max_output_bytes": args.get("max_output_bytes", 65536),
                "consumer_id": args.get("consumer_id", ""),
                "verbosity": args.get("verbosity", "summary"),
            })
        if action == "kill":
            return self.kill_session({
                "command_id": command_id,
                "signal": args.get("signal", "TERM"),
                "wait_ms": args.get("wait_ms", 3000),
                "verbosity": args.get("verbosity", "summary"),
            })
        if action == "read":
            return self.read_output({
                "output_ref": args.get("output_ref", ""),
                "offset": args.get("offset", 0),
                "limit": args.get("limit", 65536),
                "stream": args.get("stream", ""),
            })
        raise ToolFailure("INVALID_ARGUMENT", f"Unknown command action: {action}", category="validation")

    def git_inspect(self, args: dict[str, Any]) -> dict[str, Any]:
        action = str(args.get("action", "status")).lower()
        payload = {key: value for key, value in args.items() if key != "action"}
        handlers = {"status": self.git_status, "diff": self.git_diff, "log": self.git_log, "show": self.git_show, "blame": self.git_blame}
        if action not in handlers:
            raise ToolFailure("INVALID_ARGUMENT", f"Unknown Git action: {action}", category="validation")
        return handlers[action](payload)

    def document_workflow(self, args: dict[str, Any]) -> dict[str, Any]:
        action = str(args.get("action", "inspect")).lower()
        detail = str(args.get("detail", "compact")).lower()
        capabilities = {
            "runtime_ready": True,
            "dependency_check_required": False,
            "supported_inputs": ["pdf", "docx", "txt", "md", "csv", "json", "xml", "html"],
            "supported_output": ["docx", "md", "txt"],
            "extracts_pdf_page_sizes": True,
            "detects_embedded_images": True,
            "editable_layout_fidelity": "basic",
            "note": "Text and embedded-media structure are inspected locally. Pixel-perfect editable PDF-to-Word reconstruction is not guaranteed.",
        }
        if action == "capabilities":
            return {"capabilities": capabilities}
        if action == "inspect":
            raw_paths = args.get("paths", [])
            single = str(args.get("path", "")).strip()
            paths = [single] if single else []
            paths.extend(str(item).strip() for item in raw_paths if str(item).strip())
            paths = list(dict.fromkeys(paths))[:20]
            if not paths:
                raise ToolFailure("INVALID_ARGUMENT", "path or paths is required for document inspection.", category="validation")
            resolved_paths = [self.resolve_existing(raw_path).path for raw_path in paths]
            cache_key = self._fast_cache_key(
                "document_workflow_inspect",
                {"paths": paths, "max_chars": int(args.get("max_chars", 200000)), "detail": detail},
                file_paths=resolved_paths,
            )
            cached = self._fast_cache_get(cache_key, 300)
            if cached is not None:
                return cached
            documents: list[dict[str, Any]] = []
            for raw_path in paths:
                try:
                    document = self.document_extract({"path": raw_path, "max_chars": int(args.get("max_chars", 200000))})
                    if detail != "layout":
                        document = {key: document.get(key) for key in (
                            "path", "format", "suffix", "size", "page_count", "content", "truncated"
                        ) if key in document}
                    documents.append(document)
                except ToolFailure as exc:
                    documents.append({"path": raw_path, "ok": False, "error": {"code": exc.code, "message": exc.message}})
            payload = {
                "action": action,
                "documents": documents,
                "count": len(documents),
                "detail": detail,
                "recommended_next_action": "Reason over this content once, then call document_workflow action=create once. Do not inspect dependencies, repeat extraction, use exec_command/apply_patch, or run a separate verification command.",
                "cache": {"hit": False, "age_ms": 0},
            }
            if detail == "layout":
                payload["capabilities"] = capabilities
            self._fast_cache_put(cache_key, payload)
            return payload
        if action == "create":
            dedup_key = self._fast_cache_key("document_workflow_create", args)
            cached_create = self._fast_cache_get(dedup_key, 30)
            if cached_create is not None:
                cached_create["deduplicated"] = True
                return cached_create
            target = self.resolve_for_write(str(args.get("target", args.get("path", ""))))
            if target.path.suffix.lower() in {".md", ".txt"}:
                try:
                    result = create_text_document(
                        target.path,
                        str(args.get("content", "")),
                        overwrite=bool(args.get("overwrite", False)),
                    )
                except (OSError, ValueError) as exc:
                    raise ToolFailure("DOCUMENT_WRITE_FAILED", str(exc), category="runtime", retryable=True) from exc
                result["path"] = target.display
                result["affected_files"] = [{"path": target.display, "operation": "create"}]
            else:
                result = self.document_create({
                    "path": target.display,
                    "title": args.get("title", ""),
                    "content": args.get("content", ""),
                    "overwrite": args.get("overwrite", False),
                })
            self._invalidate_fast_cache()
            payload = {"action": action, "result": result, "affected_files": result.get("affected_files", [])}
            self._fast_cache_put(dedup_key, payload)
            return payload
        if action == "convert":
            result = self.document_convert({
                "source": args.get("source", ""),
                "target": args.get("target", ""),
                "overwrite": args.get("overwrite", False),
            })
            self._invalidate_fast_cache()
            return {"action": action, "result": result, "affected_files": result.get("affected_files", [])}
        if action == "rebuild":
            source = self.resolve_existing(str(args.get("source", "")))
            target = self.resolve_for_write(str(args.get("target", "")))
            analysis = extract_document(source.path, min(int(args.get("max_chars", 200000)), 1000000))
            content = str(args.get("content", ""))
            if not content:
                content = str(analysis.get("content", ""))
            title = str(args.get("title", "")).strip() or source.path.stem
            result = create_docx(target.path, title, content, overwrite=bool(args.get("overwrite", False)))
            result["path"] = target.display
            affected = [{"path": target.display, "operation": "create"}]
            self._invalidate_fast_cache()
            return {
                "action": action,
                "source_analysis": analysis,
                "result": result,
                "affected_files": affected,
                "capabilities": capabilities,
                "fidelity_warning": capabilities["note"],
            }
        raise ToolFailure("INVALID_ARGUMENT", f"Unknown document workflow action: {action}", category="validation")

    def document_extract(self, args: dict[str, Any]) -> dict[str, Any]:
        resolved = self.resolve_existing(str(args.get("path", "")))
        if not resolved.path.is_file():
            raise ToolFailure("NOT_A_FILE", "Document path must be a file.", category="validation")
        try:
            return extract_document(resolved.path, min(int(args.get("max_chars", 200000)), 1000000))
        except (OSError, ValueError, RuntimeError, zipfile.BadZipFile) as exc:
            raise ToolFailure("DOCUMENT_READ_FAILED", str(exc), category="runtime", retryable=True) from exc

    def document_create(self, args: dict[str, Any]) -> dict[str, Any]:
        resolved = self.resolve_for_write(str(args.get("path", "")))
        if resolved.path.suffix.lower() != ".docx":
            raise ToolFailure("INVALID_ARGUMENT", "document_create target must end with .docx.", category="validation")
        try:
            result = create_docx(resolved.path, str(args.get("title", "")), str(args.get("content", "")), overwrite=bool(args.get("overwrite", False)))
        except (OSError, ValueError) as exc:
            raise ToolFailure("DOCUMENT_WRITE_FAILED", str(exc), category="runtime", retryable=True) from exc
        result["path"] = resolved.display
        result["affected_files"] = [{"path": resolved.display, "operation": "create"}]
        return result

    def document_convert(self, args: dict[str, Any]) -> dict[str, Any]:
        source = self.resolve_existing(str(args.get("source", "")))
        target = self.resolve_for_write(str(args.get("target", "")))
        try:
            result = convert_document(source.path, target.path, overwrite=bool(args.get("overwrite", False)))
        except (OSError, ValueError, RuntimeError, zipfile.BadZipFile) as exc:
            raise ToolFailure("DOCUMENT_CONVERT_FAILED", str(exc), category="runtime", retryable=True) from exc
        result["source"] = source.display
        result["target"] = target.display
        result["affected_files"] = [{"path": target.display, "operation": "create"}]
        return result

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
        return {"state_file": ".coding-tools/task-state.json", "state": self.task_state.get()}

    def task_state_update(self, args: dict[str, Any]) -> dict[str, Any]:
        changes = dict(args)
        if changes.get("objective") and "status" not in changes:
            changes["status"] = "active"
        return {"state_file": ".coding-tools/task-state.json", "state": self.task_state.update(changes)}

    def task_state_clear(self, args: dict[str, Any]) -> dict[str, Any]:
        return {"cleared": True, "state_file": ".coding-tools/task-state.json", "state": self.task_state.clear()}

    def task_state_pause(self, args: dict[str, Any]) -> dict[str, Any]:
        return {"state": self.task_state.pause(str(args.get("reason", "")))}

    def task_state_resume(self, args: dict[str, Any]) -> dict[str, Any]:
        return {"state": self.task_state.resume(str(args.get("next_step", "")))}

    def task_history_list(self, args: dict[str, Any]) -> dict[str, Any]:
        return {"tasks": self.task_state.history(int(args.get("limit", 20)))}

    def emit_tool_trace(self, name: str, args: dict[str, Any], payload: dict[str, Any], started_at: float) -> None:
        raw_error = payload.get("error")
        error = raw_error if isinstance(raw_error, dict) else {}
        finished_at = time.monotonic()
        duration_ms = int((finished_at - started_at) * 1000)
        execution = payload.get("execution") if isinstance(payload.get("execution"), dict) else {}
        proof_summary = execution.get("proof_summary") if isinstance(execution.get("proof_summary"), dict) else {}
        if not proof_summary and isinstance(payload.get("proof_summary"), dict):
            proof_summary = payload["proof_summary"]
        try:
            proof_cache_hits = max(0, int(proof_summary.get("cache_hits", 0) or 0))
        except (TypeError, ValueError):
            proof_cache_hits = 0
        try:
            proof_cache_saved_ms = max(0, int(proof_summary.get("cache_saved_ms", 0) or 0))
        except (TypeError, ValueError):
            proof_cache_saved_ms = 0
        result_orchestration = payload.get("orchestration") if isinstance(payload.get("orchestration"), dict) else {}
        trace_orchestration = result_orchestration or self.task_state.get().get("orchestration", {})
        try:
            self.performance_trace.record(
                tool=name,
                started_monotonic=started_at,
                finished_monotonic=finished_at,
                request_bytes=len(json.dumps(args, ensure_ascii=False, default=str).encode("utf-8")),
                response_bytes=len(json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")),
                ok=bool(payload.get("ok", False)),
                cache_hit=bool(payload.get("cache_hit") or (isinstance(payload.get("cache"), dict) and payload["cache"].get("hit"))),
                deduplicated=bool(payload.get("deduplicated")),
                idempotency_eligible=self._idempotency_eligible_call(name, args),
                idempotency_key_present=bool(str(args.get("idempotency_key", "") or "").strip()),
                proof_cache_hits=proof_cache_hits,
                proof_cache_saved_ms=proof_cache_saved_ms,
                orchestration=trace_orchestration,
            )
        except Exception:
            pass
        self.telemetry.record_tool_call(
            name,
            ok=bool(payload.get("ok")),
            error_code=error.get("code"),
            duration_ms=duration_ms,
            truncated=bool(payload.get("truncated")),
        )
        if os.environ.get(f"{ENV_PREFIX}_TRACE") != "1":
            return
        event = {
            "event": "tool_call",
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "tool": name,
            "ok": bool(payload.get("ok", False)),
            "status": payload.get("status"),
            "error_code": error.get("code"),
            "duration_ms": duration_ms,
            "session_id": payload.get("session_id"),
            "truncated": payload.get("truncated"),
            "args": redact_for_trace(args),
        }
        print(json.dumps(event, sort_keys=True, separators=(",", ":")), file=sys.stderr, flush=True)

    @staticmethod
    def _idempotency_eligible_call(name: str, args: dict[str, Any]) -> bool:
        """Whether a call belongs in the durable-operation-identity denominator."""
        if name == "agent_workflow":
            return str(args.get("phase", "prepare")).strip().lower() in {"execute", "run"}
        if name == "document_workflow":
            return str(args.get("action", "inspect")).strip().lower() in {"create", "convert"}
        if name == "task_control":
            action = str(args.get("action", "get")).strip().lower()
            if action == "handoff":
                return str(args.get("handoff_action", "get")).strip().lower() == "record"
            return action in {"start", "update", "pause", "stop", "resume", "clear", "accept", "reject"}
        if name == "command_control":
            return str(args.get("action", "poll")).strip().lower() in {"write", "kill"}
        if name == "write_stdin":
            return bool(str(args.get("chars", "")))
        spec = TOOL_REGISTRY.get(name)
        return bool(spec and not spec.read_only and (spec.destructive or spec.open_world))

    def read_file(self, args: dict[str, Any]) -> dict[str, Any]:
        requested_path = str(args.get("path", ""))
        resolved = self.resolve_existing(requested_path)
        if resolved.path.is_dir():
            raise ToolFailure("IS_DIRECTORY", "Path is a directory.", category="validation")
        max_bytes = int(args.get("max_bytes", 131072))
        start_line = int(args.get("start_line", 1))
        end_line = args.get("end_line")
        max_lines = args.get("max_lines")
        if end_line is not None and max_lines is not None:
            calculated_end_line = start_line + int(max_lines) - 1
            if int(end_line) != calculated_end_line:
                raise ToolFailure("INVALID_ARGUMENT", "end_line and max_lines select different ranges.", category="validation")
        if end_line is None and max_lines is not None:
            end_line = start_line + int(max_lines) - 1
        encoding = args.get("encoding", "utf-8")
        if encoding != "utf-8":
            raise ToolFailure("UNSUPPORTED_ENCODING", "Only utf-8 is supported.", category="validation")
        total_bytes = resolved.path.stat().st_size
        with resolved.path.open("rb") as raw_handle:
            if b"\x00" in raw_handle.read(4096):
                raise ToolFailure("BINARY_FILE", "Binary file read blocked for text tool.", category="validation")
        if start_line < 1:
            raise ToolFailure("INVALID_ARGUMENT", "start_line must be >= 1.", category="validation")
        requested_end = int(end_line) if end_line is not None else None
        selected_parts: list[str] = []
        selected_bytes = 0
        total_lines = 0
        selection_complete = False
        try:
            with resolved.path.open("r", encoding="utf-8", errors="strict", newline="") as handle:
                for total_lines, line in enumerate(handle, start=1):
                    if total_lines < start_line:
                        continue
                    if requested_end is not None and total_lines > requested_end:
                        continue
                    if selection_complete:
                        continue
                    selected_parts.append(line)
                    selected_bytes += len(line.encode("utf-8"))
                    if len(selected_parts) > DEFAULT_MAX_LINES or selected_bytes > max_bytes:
                        selection_complete = True
        except UnicodeDecodeError as exc:
            raise ToolFailure("UNSUPPORTED_ENCODING", "File is not valid utf-8.", category="validation") from exc
        selected = "".join(selected_parts)
        truncation = truncate_text_head(selected, max_lines=DEFAULT_MAX_LINES, max_bytes=max_bytes)
        selected = truncation.content
        truncated = truncation.truncated or selection_complete
        end = requested_end if requested_end is not None else total_lines
        if end < start_line:
            selected = ""
        actual_end = min(end, total_lines)
        if truncated and truncation.output_lines > 0:
            actual_end = min(total_lines, start_line + truncation.output_lines - 1)
        next_start_line = actual_end + 1 if truncated and actual_end < total_lines else None
        warnings = []
        if truncated:
            warnings.append("content truncated")
        if truncation.first_line_exceeds_limit:
            warnings.append("first selected line exceeds max_bytes")
        result = {
            "path": resolved.display,
            "content": selected,
            "encoding": "utf-8",
            "max_bytes": max_bytes,
            "start_line": start_line,
            "end_line": actual_end,
            "total_lines": total_lines,
            "total_bytes": total_bytes,
            "bytes_read": len(selected.encode("utf-8")),
            "truncated": truncated,
            "truncated_by": truncation.truncated_by or ("bytes" if selection_complete else None),
            "first_line_exceeds_limit": truncation.first_line_exceeds_limit,
            "output_lines": truncation.output_lines,
            "output_bytes": truncation.output_bytes,
            "next_start_line": next_start_line,
            "warnings": warnings,
        }
        if next_start_line is not None:
            result["next_action"] = {
                "tool": "read_file",
                "arguments": {
                    "path": requested_path,
                    "start_line": next_start_line,
                    "max_bytes": max_bytes,
                },
            }
        return result

    def list_dir(self, args: dict[str, Any]) -> dict[str, Any]:
        resolved = self.resolve_existing(str(args.get("path", ".")))
        if not resolved.path.is_dir():
            raise ToolFailure("NOT_A_DIRECTORY", "Path is not a directory.", category="validation")
        recursive = bool(args.get("recursive", False))
        max_depth = int(args.get("max_depth", 1))
        max_entries = int(args.get("max_entries", 1000))
        include_hidden = bool(args.get("include_hidden", False))
        include_ignored = bool(args.get("include_ignored", False))
        sort_key = args.get("sort", "name")
        entries: list[dict[str, Any]] = []
        truncated = False

        def visit(directory: Path, depth: int) -> None:
            nonlocal truncated
            if truncated:
                return
            try:
                children = list(directory.iterdir())
            except OSError:
                return
            child_rel_paths = [normalize_rel_display(child, self.workspace.root) for child in children]
            ignored = set() if include_ignored else self.workspace.git_ignored_paths(child_rel_paths)
            for child in children:
                if self.workspace.is_ignored_path(
                    child,
                    include_hidden=include_hidden,
                    include_ignored=include_ignored,
                    git_ignored=ignored,
                ):
                    continue
                entries.append(entry_for_path(child, self.workspace.root))
                if len(entries) >= max_entries:
                    truncated = True
                    return
                if recursive and depth < max_depth and child.is_dir() and not child.is_symlink():
                    visit(child, depth + 1)

        visit(resolved.path, 1)
        entries.sort(key=lambda item: sort_value(item, sort_key))
        return {
            "path": resolved.display,
            "entries": entries,
            "truncated": truncated,
            "warnings": ["entry limit reached"] if truncated else [],
        }

    def list_files(self, args: dict[str, Any]) -> dict[str, Any]:
        resolved = self.resolve_existing(str(args.get("path", ".")))
        if not resolved.path.is_dir():
            raise ToolFailure("NOT_A_DIRECTORY", "Path is not a directory.", category="validation")
        patterns_arg = args.get("patterns")
        glob_arg = args.get("glob")
        if isinstance(patterns_arg, list) and patterns_arg:
            patterns = [str(item) for item in patterns_arg]
        elif isinstance(glob_arg, str) and glob_arg:
            patterns = [glob_arg]
        else:
            patterns = ["**/*"]
        exclude_patterns = [str(item) for item in args.get("exclude_patterns", [])]
        include_hidden = bool(args.get("include_hidden", False))
        include_ignored = bool(args.get("include_ignored", False))
        max_results = int(args.get("max_results", 5000))
        fast_result = self._list_files_with_fd(
            resolved,
            patterns,
            exclude_patterns,
            include_hidden=include_hidden,
            include_ignored=include_ignored,
            max_results=max_results,
            sort_key=str(args.get("sort", "path")),
        )
        if fast_result is not None:
            return fast_result
        files: list[dict[str, Any]] = []
        truncated = False
        for batch in path_batches(walk_files(resolved.path), 256):
            # Filter by glob first so git check-ignore only sees candidates.
            candidates = [
                (path, rel)
                for path, rel in ((path, normalize_rel_display(path, self.workspace.root)) for path in batch)
                if matches_any_glob(rel, patterns) and not matches_any_glob(rel, exclude_patterns)
            ]
            ignored = set() if include_ignored else self.workspace.git_ignored_paths([rel for _, rel in candidates])
            for path, rel in candidates:
                if path.is_symlink() and not self.workspace.is_safe_existing_path(path):
                    continue
                if self.workspace.is_ignored_path(
                    path,
                    include_hidden=include_hidden,
                    include_ignored=include_ignored,
                    git_ignored=ignored,
                ):
                    continue
                files.append(file_entry(path, rel, path.lstat()))
                if len(files) >= max_results:
                    truncated = True
                    break
            if truncated:
                break
        files.sort(key=lambda item: item["modified"] if args.get("sort") == "modified" else item["path"])
        return {
            "path": resolved.display,
            "files": files,
            "truncated": truncated,
            "warnings": ["result limit reached"] if truncated else [],
        }

    def _list_files_with_fd(
        self,
        resolved: ResolvedPath,
        patterns: list[str],
        exclude_patterns: list[str],
        *,
        include_hidden: bool,
        include_ignored: bool,
        max_results: int,
        sort_key: str,
    ) -> dict[str, Any] | None:
        fd = cached_which("fd", "fdfind")
        if not fd or not resolved.path.is_dir():
            return None
        args_base = [
            fd,
            "--glob",
            "--color=never",
            "--type",
            "f",
            "--type",
            "l",
            "--max-results",
            str(max_results),
            "--no-require-git",
        ]
        if include_hidden:
            args_base.append("--hidden")
        if include_ignored:
            args_base.append("--no-ignore")
        else:
            for name in sorted(DEFAULT_EXCLUDED_NAMES):
                args_base.extend(["--exclude", name])
        for pattern in exclude_patterns:
            args_base.extend(["--exclude", pattern])

        paths: dict[str, Path] = {}
        for pattern in patterns:
            effective = pattern
            args = list(args_base)
            if "/" in pattern:
                args.append("--full-path")
                if not pattern.startswith("/") and not pattern.startswith("**/") and pattern != "**":
                    effective = f"**/{pattern}"
            args.extend(["--", effective, "."])
            try:
                completed = subprocess.run(
                    args,
                    cwd=str(resolved.path),
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=10,
                    **hidden_process_popen_kwargs(),
                )
            except Exception:
                return None
            if completed.returncode not in {0, 1}:
                return None
            for raw in completed.stdout.splitlines():
                rel_to_search = raw.strip().removeprefix("./")
                if not rel_to_search:
                    continue
                path = resolved.path / rel_to_search
                if path.is_symlink() and not self.workspace.is_safe_existing_path(path):
                    continue
                rel = normalize_rel_display(path, self.workspace.root)
                if matches_any_glob(rel, exclude_patterns):
                    continue
                paths[rel] = path
                if len(paths) >= max_results:
                    break
            if len(paths) >= max_results:
                break
        ignored = set() if include_ignored else self.workspace.git_ignored_paths(list(paths))
        files: list[dict[str, Any]] = []
        for rel, path in paths.items():
            if self.workspace.is_ignored_path(
                path,
                include_hidden=include_hidden,
                include_ignored=include_ignored,
                git_ignored=ignored,
            ):
                continue
            try:
                stat = path.lstat()
            except OSError:
                continue
            files.append(file_entry(path, rel, stat))
        files.sort(key=lambda item: item["modified"] if sort_key == "modified" else item["path"])
        truncated = len(paths) >= max_results
        return {
            "path": resolved.display,
            "files": files,
            "truncated": truncated,
            "engine": "fd",
            "warnings": ["result limit reached"] if truncated else [],
        }

    def search_text(self, args: dict[str, Any]) -> dict[str, Any]:
        query = str(args.get("query", ""))
        if not query:
            raise ToolFailure("INVALID_ARGUMENT", "query is required.", category="validation")
        resolved = self.resolve_existing(str(args.get("path", ".")))
        regex = bool(args.get("regex", False))
        case_sensitive = bool(args.get("case_sensitive", False))
        include_globs = [str(item) for item in args.get("include_globs", [])]
        if isinstance(args.get("glob"), str):
            include_globs.append(str(args["glob"]))
        exclude_globs = [str(item) for item in args.get("exclude_globs", [])]
        context_lines = int(args.get("context_lines", 0))
        max_results = int(args.get("max_results", 1000))
        max_preview_bytes = int(args.get("max_preview_bytes", 512))
        fast_result = self._search_text_with_rg(
            resolved,
            query,
            regex=regex,
            case_sensitive=case_sensitive,
            include_globs=include_globs,
            exclude_globs=exclude_globs,
            context_lines=context_lines,
            max_results=max_results,
            max_preview_bytes=max_preview_bytes,
        )
        if fast_result is not None:
            return fast_result
        matches: list[dict[str, Any]] = []
        total = 0
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            compiled = re.compile(query, flags) if regex else None
        except re.error as exc:
            raise ToolFailure("INVALID_ARGUMENT", f"Invalid regex: {exc}", category="validation") from exc
        needle = query if case_sensitive else query.lower()

        roots = [resolved.path] if resolved.path.is_file() else walk_files(resolved.path)
        for batch in path_batches(roots, 256):
            # Filter by glob first so git check-ignore runs once per batch of
            # candidates instead of once per walked file.
            candidates = []
            for path in batch:
                if path.is_dir():
                    continue
                if path.is_symlink() and not self.workspace.is_safe_existing_path(path):
                    continue
                rel = normalize_rel_display(path, self.workspace.root)
                if include_globs and not matches_any_glob(rel, include_globs):
                    continue
                if matches_any_glob(rel, exclude_globs):
                    continue
                candidates.append((path, rel))
            ignored = self.workspace.git_ignored_paths([rel for _, rel in candidates])
            for path, rel in candidates:
                if self.workspace.is_ignored_path(path, git_ignored=ignored):
                    continue
                try:
                    data = path.read_bytes()
                except OSError:
                    continue
                if b"\x00" in data[:4096]:
                    continue
                try:
                    lines = data.decode("utf-8").splitlines()
                except UnicodeDecodeError:
                    continue
                for index, line in enumerate(lines):
                    if compiled:
                        found = compiled.search(line)
                        if not found:
                            continue
                        column = found.start() + 1
                    else:
                        literal_index = find_literal(line, needle, case_sensitive)
                        if literal_index < 0:
                            continue
                        column = literal_index + 1
                    total += 1
                    if len(matches) >= max_results:
                        continue
                    before = lines[max(0, index - context_lines) : index]
                    after = lines[index + 1 : index + 1 + context_lines]
                    matches.append(search_match_item(rel, index + 1, column, line, before, after, max_preview_bytes))
        return {
            "query": query,
            "matches": matches,
            "total_matches": total,
            "truncated": total > len(matches),
            "warnings": ["result limit reached"] if total > len(matches) else [],
        }

    def _search_text_with_rg(
        self,
        resolved: ResolvedPath,
        query: str,
        *,
        regex: bool,
        case_sensitive: bool,
        include_globs: list[str],
        exclude_globs: list[str],
        context_lines: int,
        max_results: int,
        max_preview_bytes: int,
    ) -> dict[str, Any] | None:
        rg = cached_which("rg")
        if not rg:
            return None
        args = [rg, "--json", "--line-number", "--color=never"]
        if not case_sensitive:
            args.append("--ignore-case")
        if not regex:
            args.append("--fixed-strings")
        for name in sorted(DEFAULT_EXCLUDED_NAMES):
            args.extend(["--glob", f"!{name}/**"])
        for pattern in include_globs:
            args.extend(["--glob", pattern])
        for pattern in exclude_globs:
            args.extend(["--glob", f"!{pattern}"])
        search_path = resolved.display if resolved.display != "." else "."
        args.extend(["--", query, search_path])
        try:
            process = subprocess.Popen(
                args,
                cwd=str(self.workspace.root),
                text=True,
                encoding="utf-8",
                errors="replace",
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                **hidden_process_popen_kwargs(),
            )
        except OSError:
            return None
        timed_out = threading.Event()

        def stop_timed_out_search() -> None:
            timed_out.set()
            try:
                process.kill()
            except OSError:
                pass

        timeout = threading.Timer(10, stop_timed_out_search)
        timeout.daemon = True
        timeout.start()
        matches: list[dict[str, Any]] = []
        total = 0
        truncated = False
        file_cache: dict[str, list[str]] = {}
        assert process.stdout is not None
        try:
            for raw in process.stdout:
                try:
                    event = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if event.get("type") != "match":
                    continue
                data = event.get("data") if isinstance(event.get("data"), dict) else {}
                path_text = data.get("path", {}).get("text") if isinstance(data.get("path"), dict) else None
                line_number = data.get("line_number")
                line_text = data.get("lines", {}).get("text") if isinstance(data.get("lines"), dict) else ""
                if not isinstance(path_text, str) or not isinstance(line_number, int):
                    continue
                total += 1
                if len(matches) >= max_results:
                    truncated = True
                    process.terminate()
                    break
                rel = normalize_rel_display((self.workspace.root / path_text).resolve(), self.workspace.root)
                submatches = data.get("submatches") if isinstance(data.get("submatches"), list) else []
                first_submatch = submatches[0] if submatches and isinstance(submatches[0], dict) else {}
                column = int(first_submatch.get("start", 0)) + 1
                sanitized = str(line_text).replace("\r\n", "\n").replace("\r", "").rstrip("\n")
                lines: list[str] = []
                if context_lines > 0:
                    lines = file_cache.get(rel, [])
                    if rel not in file_cache:
                        try:
                            lines = (self.workspace.root / rel).read_text(encoding="utf-8").splitlines()
                        except OSError:
                            lines = []
                        file_cache[rel] = lines
                index = line_number - 1
                before = lines[max(0, index - context_lines) : index] if lines else []
                after = lines[index + 1 : index + 1 + context_lines] if lines else []
                matches.append(search_match_item(rel, line_number, column, sanitized, before, after, max_preview_bytes))
        finally:
            timeout.cancel()
            try:
                process.stdout.close()
            except OSError:
                pass
            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=1)
        if timed_out.is_set():
            return None
        if not truncated and process.returncode not in {0, 1}:
            return None
        return {
            "query": query,
            "matches": matches,
            "total_matches": total,
            "total_matches_exact": not truncated,
            "truncated": truncated,
            "engine": "rg",
            "warnings": ["result limit reached; search stopped early"] if truncated else [],
        }

    def apply_patch(self, args: dict[str, Any]) -> dict[str, Any]:
        patch = str(args.get("patch", ""))
        dry_run = bool(args.get("dry_run", False))
        with self.patch_lock:
            operations = parse_patch(patch)
            staged: dict[str, StagedFile] = {}
            summaries: list[str] = []
            affected: list[dict[str, str]] = []
            additions = 0
            removals = 0
            for op in operations:
                self._validate_patch_path(op.path, require_existing=op.kind in {"update", "delete"})
                if op.kind in {"add", "update", "delete"}:
                    self.workspace.reject_write_symlink(op.path)
                if op.move_to:
                    self._validate_patch_path(op.move_to, require_existing=False)
                    self.workspace.reject_write_symlink(op.move_to)
                if op.kind == "add":
                    target = self.workspace.resolve_for_write(op.path)
                    if target.existed:
                        raise ToolFailure("PATCH_FAILED", "Cannot add file that already exists.", category="validation")
                    baseline = FileBaseline.capture(target.path)
                    staged[target.display] = StagedFile(
                        target.display,
                        target.path,
                        op.add_content or "",
                        baseline,
                        None,
                    )
                    affected.append({"path": target.display, "operation": "add"})
                    summaries.append(f"A {target.display}")
                    additions += len((op.add_content or "").splitlines())
                elif op.kind == "delete":
                    target = self.workspace.resolve_existing(op.path)
                    if target.path.is_dir():
                        raise ToolFailure("PATCH_FAILED", "Cannot delete a directory.", category="validation")
                    prior = staged.get(target.display)
                    baseline = prior.baseline if prior is not None else FileBaseline.capture(target.path)
                    staged[target.display] = StagedFile(target.display, target.path, None, baseline, baseline.mode)
                    affected.append({"path": target.display, "operation": "delete"})
                    summaries.append(f"D {target.display}")
                    removals += len((baseline.data or b"").splitlines())
                elif op.kind == "update":
                    source = self.workspace.resolve_existing(op.path)
                    if source.path.is_dir():
                        raise ToolFailure("PATCH_FAILED", "Cannot update a directory.", category="validation")
                    prior = staged.get(source.display)
                    if prior is not None and prior.content is None:
                        raise ToolFailure("PATCH_FAILED", "Cannot update a deleted file.", category="validation")
                    baseline = prior.baseline if prior is not None else FileBaseline.capture(source.path)
                    content = prior.content if prior is not None else baseline.text(source.display)
                    assert content is not None
                    updated = apply_update_hunks(content, op.hunks, op.path)
                    for hunk in op.hunks:
                        for line in hunk:
                            additions += line.startswith("+")
                            removals += line.startswith("-")
                    source_mode = prior.mode if prior is not None else baseline.mode
                    if op.move_to:
                        dest = self.workspace.resolve_for_write(op.move_to)
                        if dest.existed and dest.display != source.display:
                            raise ToolFailure("PATCH_FAILED", "Cannot move over an existing file.", category="validation")
                        dest_baseline = baseline if dest.display == source.display else FileBaseline.capture(dest.path)
                        staged[source.display] = StagedFile(
                            source.display,
                            source.path,
                            None,
                            baseline,
                            source_mode,
                        )
                        staged[dest.display] = StagedFile(
                            dest.display,
                            dest.path,
                            updated,
                            dest_baseline,
                            source_mode,
                        )
                        affected.append({"path": dest.display, "old_path": source.display, "operation": "move"})
                        summaries.append(f"R {source.display} -> {dest.display}")
                    else:
                        staged[source.display] = StagedFile(
                            source.display,
                            source.path,
                            updated,
                            baseline,
                            source_mode,
                        )
                        affected.append({"path": source.display, "operation": "update"})
                        summaries.append(f"M {source.display}")
            if not affected:
                raise ToolFailure("PATCH_FAILED", "No files were modified.", category="validation")
            if not dry_run:
                self._commit_staged_files(list(staged.values()))
        return {
            "dry_run": dry_run,
            "clean": True,
            "summary": "\n".join(summaries),
            "affected_files": affected,
            "additions": additions,
            "removals": removals,
            "warnings": [],
        }

    def _validate_patch_path(self, raw_path: str, *, require_existing: bool) -> None:
        if require_existing:
            self.workspace.resolve_existing(raw_path)
        else:
            self.workspace.resolve_for_write(raw_path)

    def _commit_staged_files(self, staged: list[StagedFile]) -> None:
        self.patch_committer.commit(staged)
        for change in staged:
            if change.display in self.patch_baselines:
                continue
            self.patch_baselines[change.display] = (
                None if change.baseline.data is None else change.baseline.data.decode("utf-8", errors="replace")
            )

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
                    self.workspace.root,
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
            if principal_active >= PRINCIPAL_MAX_ACTIVE_SESSIONS:
                if landlock_fd is not None:
                    os.close(landlock_fd)
                raise ToolFailure(
                    "SESSION_LIMIT_REACHED",
                    "This client already reached its per-principal command session quota.",
                    category="runtime",
                    retryable=True,
                    details={
                        "principal_id": principal_id,
                        "max_principal_sessions": PRINCIPAL_MAX_ACTIVE_SESSIONS,
                        "principal_active": principal_active,
                    },
                )
            self.starting_sessions += 1
        process: subprocess.Popen[bytes] | None = None
        session: ExecSession | None = None
        registered = False
        slot_released = False
        try:
            process, pty_master_fd = spawn_process(
                popen_cmd,
                cwd=str(workdir.path),
                shell=popen_shell,
                env=env,
                tty=tty,
                popen_kwargs=popen_extra,
            )
            session = self._make_session(
                process,
                timeout_at=deadline,
                warnings=[landlock_warning] if landlock_warning else None,
                pty_master_fd=pty_master_fd,
            )
            try:
                self.task_state.record_command_started(cmd, session.session_id, workdir.display)
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

        def runner(command: str, workdir: Path, timeout_seconds: int) -> dict[str, Any]:
            relative = workdir.relative_to(self.workspace.root).as_posix() or "."
            started = time.time()
            payload = self.exec_command({
                "cmd": command,
                "workdir": relative,
                "timeout_ms": min(timeout_seconds * 1000, 600000),
                "yield_time_ms": 30000,
                "max_output_bytes": 131072,
                "verbosity": "summary",
            })
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
                "status": "passed" if payload.get("exit_code") == 0 else "failed",
                "exit_code": payload.get("exit_code"),
                "duration_ms": int((time.time() - started) * 1000),
                "summary": str(payload.get("summary") or payload.get("stderr") or payload.get("stdout") or "")[:4000],
            }
            return result

        report = run_build_verification(resolved.path, args, runner)
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
            self.workspace.resolve_existing(normalized)
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
                    self.workspace.resolve_for_write(normalized)
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
            if total <= PRINCIPAL_MAX_RETAINED_OUTPUT_BYTES:
                continue
            overflow = total - PRINCIPAL_MAX_RETAINED_OUTPUT_BYTES
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

    def git_status(self, args: dict[str, Any]) -> dict[str, Any]:
        resolved = self.resolve_existing(str(args.get("path", ".")))
        max_entries = int(args.get("max_entries", 1000))
        include_untracked = bool(args.get("include_untracked", True))
        git = require_git()
        git_env = self._git_env()
        root_check = self._run_git_text(
            [git, "-C", str(resolved.path), "rev-parse", "--show-toplevel"], env=git_env
        )
        if root_check.returncode != 0:
            return self._git_status_not_repo(root_check)
        status_cmd = [git, "-C", str(resolved.path), "status", "--porcelain=v1", "-b"]
        if not include_untracked:
            status_cmd.append("--untracked-files=no")
        completed = self._run_git_text(status_cmd, timeout=10, env=git_env)
        if completed.returncode != 0:
            raise ToolFailure("GIT_ERROR", completed.stderr.strip() or "git status failed", category="runtime")
        lines = completed.stdout.splitlines()
        branch = ""
        upstream = ""
        ahead = 0
        behind = 0
        entries: list[dict[str, Any]] = []
        for line in lines:
            if line.startswith("## "):
                branch, upstream, ahead, behind = parse_branch_line(line[3:])
                continue
            if not line:
                continue
            path_text = line[3:]
            original = None
            if " -> " in path_text:
                original, path_text = path_text.split(" -> ", 1)
            entries.append(
                {
                    "path": path_text,
                    "original_path": original,
                    "index_status": line[0],
                    "worktree_status": line[1],
                }
            )
            if len(entries) >= max_entries:
                break
        return {
            "is_repo": True,
            "branch": branch,
            "head": self._git_rev_parse(resolved.path, "HEAD", env=git_env),
            "upstream": upstream,
            "ahead": ahead,
            "behind": behind,
            "clean": not entries,
            "entries": entries,
            "truncated": len(entries) >= max_entries and len(lines) > max_entries + 1,
        }

    def git_diff(self, args: dict[str, Any]) -> dict[str, Any]:
        git = require_git()
        git_env = self._git_env()
        staged = bool(args.get("staged", False))
        unstaged = bool(args.get("unstaged", True))
        context = int(args.get("context_lines", 3))
        max_bytes = int(args.get("max_bytes", 262144))
        path_filters = self._git_path_filters(args)
        if not self._is_git_repo(self.workspace.root, env=git_env):
            return self._fallback_diff(path_filters, max_bytes)
        chunks: list[bytes] = []
        if unstaged:
            chunks.append(self._run_git_diff(git, context, path_filters, cached=False, env=git_env))
        if staged:
            chunks.append(self._run_git_diff(git, context, path_filters, cached=True, env=git_env))
        combined = b""
        for chunk in chunks:
            if combined and chunk and not combined.endswith(b"\n"):
                combined += b"\n"
            combined += chunk
        diff_truncation = truncate_text_head(combined.decode("utf-8", errors="replace"), max_lines=DEFAULT_MAX_LINES, max_bytes=max_bytes)
        diff_text = diff_truncation.content
        truncated = diff_truncation.truncated
        return {
            "diff": diff_text,
            "files": parse_diff_files(diff_text),
            **truncation_fields(diff_truncation),
            "warnings": ["diff truncated"] if truncated else [],
        }

    def _run_git_diff(
        self, git: str, context: int, path_filters: list[str], *, cached: bool, env: dict[str, str] | None = None
    ) -> bytes:
        cmd = [git, "-C", str(self.workspace.root), "diff", f"--unified={context}"]
        if cached:
            cmd.append("--cached")
        if path_filters:
            cmd.append("--")
            cmd.extend(path_filters)
        completed = self._run_git_bytes(cmd, timeout=10, env=env)
        if completed.returncode not in {0, 1}:
            raise ToolFailure("GIT_ERROR", completed.stderr.decode("utf-8", errors="replace"), category="runtime")
        return completed.stdout

    def _fallback_diff(self, path_filters: list[str], max_bytes: int) -> dict[str, Any]:
        selected = set(path_filters)
        chunks: list[str] = []
        files: list[dict[str, Any]] = []
        for rel, before in sorted(self.patch_baselines.items()):
            if selected and rel not in selected:
                continue
            current_path = self.workspace.resolve_for_write(rel).path
            after = read_text_preserve_newlines(current_path) if current_path.exists() and not current_path.is_dir() else None
            if before == after:
                continue
            before_lines = [] if before is None else before.splitlines(keepends=True)
            after_lines = [] if after is None else after.splitlines(keepends=True)
            chunks.extend(
                difflib.unified_diff(
                    before_lines,
                    after_lines,
                    fromfile=f"a/{rel}",
                    tofile=f"b/{rel}",
                    lineterm="",
                )
            )
            status = "added" if before is None else "deleted" if after is None else "modified"
            files.append({"path": rel, "status": status, "binary": False})
        diff = "\n".join(chunks)
        if diff and not diff.endswith("\n"):
            diff += "\n"
        diff_truncation = truncate_text_head(diff, max_lines=DEFAULT_MAX_LINES, max_bytes=max_bytes)
        diff_text = diff_truncation.content
        truncated = diff_truncation.truncated
        return {
            "diff": diff_text,
            "files": files,
            **truncation_fields(diff_truncation),
            "warnings": ["non-git diff fallback"] + (["diff truncated"] if truncated else []),
        }

    def git_log(self, args: dict[str, Any]) -> dict[str, Any]:
        git = require_git()
        git_env = self._git_env()
        requested_path = str(args.get("path", "."))
        resolved = self.resolve_existing(requested_path)
        if not self._is_git_repo(resolved.path, env=git_env):
            return {"is_repo": False, "commits": [], "truncated": False, "warnings": []}
        ref = validate_git_ref(str(args.get("ref", "HEAD")))
        max_count = int(args.get("max_count", 20))
        skip = int(args.get("skip", 0))
        path_filter = resolved.display
        cmd = [
            git,
            "-C",
            str(self.workspace.root),
            "log",
            f"--max-count={max_count + 1}",
            f"--skip={skip}",
            "--date=iso-strict",
            "--pretty=format:%H%x1f%h%x1f%an%x1f%ae%x1f%ad%x1f%s%x1e",
            ref,
        ]
        if path_filter != ".":
            cmd.extend(["--", path_filter])
        completed = self._run_git_text(cmd, timeout=10, env=git_env)
        if completed.returncode != 0:
            raise ToolFailure("GIT_ERROR", completed.stderr.strip() or "git log failed", category="runtime")
        commits: list[dict[str, Any]] = []
        for record in completed.stdout.split("\x1e"):
            fields = record.strip("\n").split("\x1f")
            if len(fields) < 6 or not fields[0]:
                continue
            commits.append(
                {
                    "hash": fields[0],
                    "short_hash": fields[1],
                    "author_name": fields[2],
                    "author_email": fields[3],
                    "author_date": fields[4],
                    "subject": fields[5],
                }
            )
        truncated = len(commits) > max_count
        result = {
            "is_repo": True,
            "ref": ref,
            "path": path_filter,
            "max_count": max_count,
            "skip": skip,
            "commits": commits[:max_count],
            "truncated": truncated,
            "warnings": ["commit limit reached"] if truncated else [],
        }
        if truncated:
            result["next_action"] = {
                "tool": "git_log",
                "arguments": {
                    "path": requested_path,
                    "ref": ref,
                    "max_count": max_count,
                    "skip": skip + max_count,
                },
            }
        return result

    def git_show(self, args: dict[str, Any]) -> dict[str, Any]:
        git = require_git()
        git_env = self._git_env()
        if not self._is_git_repo(self.workspace.root, env=git_env):
            return {"is_repo": False, "content": "", "files": [], "truncated": False, "warnings": []}
        rev = validate_git_ref(str(args.get("rev", "HEAD")))
        context = int(args.get("context_lines", 3))
        max_bytes = int(args.get("max_bytes", 262144))
        include_diff = bool(args.get("include_diff", True))
        normalized_filters = self._git_path_filters(args)
        cmd = [
            git,
            "-C",
            str(self.workspace.root),
            "show",
            "--no-ext-diff",
            "--format=fuller",
            f"--unified={context}",
        ]
        if not include_diff:
            cmd.append("--no-patch")
        cmd.append(rev)
        if normalized_filters:
            cmd.append("--")
            cmd.extend(normalized_filters)
        completed = self._run_git_bytes(cmd, timeout=10, env=git_env)
        if completed.returncode != 0:
            raise ToolFailure("GIT_ERROR", completed.stderr.decode("utf-8", errors="replace").strip() or "git show failed", category="runtime")
        truncation = truncate_text_head(completed.stdout.decode("utf-8", errors="replace"), max_lines=DEFAULT_MAX_LINES, max_bytes=max_bytes)
        content = truncation.content
        return {
            "is_repo": True,
            "rev": rev,
            "content": content,
            "files": parse_diff_files(content),
            **truncation_fields(truncation),
            "warnings": ["output truncated"] if truncation.truncated else [],
        }

    def git_blame(self, args: dict[str, Any]) -> dict[str, Any]:
        git = require_git()
        git_env = self._git_env()
        requested_path = str(args.get("path", ""))
        resolved = self.resolve_existing(requested_path)
        if resolved.path.is_dir():
            raise ToolFailure("IS_DIRECTORY", "Path is a directory.", category="validation")
        if not self._is_git_repo(self.workspace.root, env=git_env):
            return {"is_repo": False, "path": resolved.display, "lines": [], "truncated": False, "warnings": []}
        ref_arg = args.get("rev")
        ref = validate_git_ref(str(ref_arg)) if isinstance(ref_arg, str) and ref_arg else None
        start_line = int(args.get("start_line", 1))
        end_line = args.get("end_line")
        max_lines = int(args.get("max_lines", 200))
        if end_line is None:
            requested_final_line = start_line + max_lines - 1
        else:
            requested_final_line = int(end_line)
        if requested_final_line < start_line:
            raise ToolFailure("INVALID_ARGUMENT", "end_line must be >= start_line.", category="validation")
        requested_lines = requested_final_line - start_line + 1
        truncated = requested_lines > max_lines
        final_line = min(requested_final_line, start_line + max_lines - 1)
        cmd = [
            git,
            "-C",
            str(self.workspace.root),
            "blame",
            "--line-porcelain",
            "-L",
            f"{start_line},{final_line}",
        ]
        if ref:
            cmd.append(ref)
        cmd.extend(["--", resolved.display])
        completed = self._run_git_text(cmd, timeout=10, env=git_env)
        if completed.returncode != 0:
            raise ToolFailure("GIT_ERROR", completed.stderr.strip() or "git blame failed", category="runtime")
        lines = parse_git_blame_porcelain(completed.stdout)
        if len(lines) > max_lines:
            lines = lines[:max_lines]
            truncated = True
        result = {
            "is_repo": True,
            "path": resolved.display,
            "rev": ref,
            "start_line": start_line,
            "end_line": final_line,
            "max_lines": max_lines,
            "lines": lines,
            "truncated": truncated,
            "warnings": ["line limit reached"] if truncated else [],
        }
        if truncated and final_line < requested_final_line:
            next_arguments: dict[str, Any] = {
                "path": requested_path,
                "start_line": final_line + 1,
                "end_line": requested_final_line,
                "max_lines": max_lines,
            }
            if ref:
                next_arguments["rev"] = ref
            result["next_action"] = {
                "tool": "git_blame",
                "arguments": next_arguments,
            }
        return result

    def request_permissions(self, args: dict[str, Any]) -> dict[str, Any]:
        if self.dangerously_skip_all_permissions:
            return {
                "ok": True,
                "status": "granted",
                "grant_id": "dangerously-skip-all-permissions",
                "expires_at": None,
                "constraints": {
                    "mode": "dangerously_skip_all_permissions",
                    "workspace": str(self.workspace.root),
                    "requested": args,
                },
                "warnings": [
                    "dangerously-skip-all-permissions is enabled; permission-gated operations are auto-granted"
                ],
            }
        return {
            "ok": False,
            "status": "unsupported",
            "grant_id": None,
            "expires_at": None,
            "error": {
                "code": "ELICITATION_UNSUPPORTED",
                "message": "Permission elicitation is not available for this client.",
                "category": "permission",
                "retryable": False,
                "details": {"requested": args},
            },
        }

    def view_image(self, args: dict[str, Any]) -> dict[str, Any]:
        resolved = self.resolve_existing(str(args.get("path", "")))
        max_bytes = int(args.get("max_bytes", 5_242_880))
        max_width = int(args.get("max_width", IMAGE_RESIZE_MAX_DIMENSION))
        max_height = int(args.get("max_height", IMAGE_RESIZE_MAX_DIMENSION))
        auto_resize = bool(args.get("auto_resize", True))
        data = resolved.path.read_bytes()
        mime_type, width, height = identify_image(data, resolved.path)
        if mime_type is None:
            raise ToolFailure("BINARY_FILE", "File is not a supported image.", category="validation")
        original = {"bytes": len(data), "width": width, "height": height, "mime_type": mime_type}
        resized = False
        warnings: list[str] = []
        if auto_resize and should_resize_image(len(data), width, height, max_bytes, max_width, max_height):
            resized_data = resize_image_bytes(data, mime_type, max_width=max_width, max_height=max_height, max_bytes=max_bytes)
            if resized_data is not None:
                data, mime_type = resized_data
                mime_type, width, height = identify_image(data, resolved.path)
                resized = True
            else:
                warnings.append("auto_resize requested but Pillow is not installed or image resize failed")
        if len(data) > max_bytes:
            raise ToolFailure(
                "OUTPUT_TOO_LARGE",
                "Image exceeds max_bytes.",
                category="validation",
                details={"bytes": len(data), "max_bytes": max_bytes, "resize_attempted": auto_resize, "warnings": warnings},
            )
        payload: dict[str, Any] = {
            "path": resolved.display,
            "mime_type": mime_type,
            "bytes": len(data),
            "width": width,
            "height": height,
            "resized": resized,
            "original": original,
            "_mcp_image_data": base64.b64encode(data).decode("ascii"),
            "warnings": warnings,
        }
        return payload


def walk_files(root: Path) -> Iterator[Path]:
    if root.is_file() or root.is_symlink():
        yield root
        return
    for current, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = [name for name in dirs if name not in DEFAULT_EXCLUDED_NAMES]
        current_path = Path(current)
        for name in files:
            yield current_path / name


def path_batches(paths: Iterator[Path], size: int) -> Iterator[list[Path]]:
    batch: list[Path] = []
    for path in paths:
        batch.append(path)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch


def find_literal(line: str, needle: str, case_sensitive: bool) -> int:
    """Return the match index of a pre-normalized needle (lowered unless
    case_sensitive) in line, or -1."""
    haystack = line if case_sensitive else line.lower()
    return haystack.find(needle)


def shlex_split(command: str) -> list[str]:
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    return list(lexer)


def parse_heredoc_delimiter(command: str, start: int) -> tuple[int, str, bool]:
    index = start
    length = len(command)
    strip_tabs = False
    if index < length and command[index] == "-":
        strip_tabs = True
        index += 1
    while index < length and command[index] in " \t":
        index += 1
    delimiter: list[str] = []
    while index < length:
        char = command[index]
        if char in "'\"":
            quote = char
            index += 1
            while index < length and command[index] != quote:
                delimiter.append(command[index])
                index += 1
            if index < length:
                index += 1
            continue
        if char == "\\" and index + 1 < length:
            delimiter.append(command[index + 1])
            index += 2
            continue
        if char.isspace() or char in ";&|<>()":
            break
        delimiter.append(char)
        index += 1
    return index, "".join(delimiter), strip_tabs


def strip_heredoc_payloads(command: str) -> str:
    """Drop heredoc body lines so command scanning sees only live shell code.

    Heredoc bodies are stdin data, not code: scanning XML payloads produces fake
    escape candidates such as ``/modelVersion`` from ``</modelVersion>``. Bash
    starts the body on the line after the operator, so everything else stays
    visible to the scanner: redirections on the operator's own line
    (``cat <<EOF > /etc/cron.d/evil``) and commands after the closing delimiter.
    ``<<`` inside quotes or inside ``((...))`` arithmetic never opens a heredoc,
    which keeps fake heredocs from hiding live commands; an unterminated heredoc
    swallows the remaining lines exactly as bash treats them (as body).
    """
    if "<<" not in command:
        return command
    live: list[str] = []
    pending: list[tuple[str, bool]] = []
    index = 0
    length = len(command)
    in_single = False
    in_double = False
    arith_parens = 0
    while index < length:
        char = command[index]
        if in_single:
            live.append(char)
            in_single = char != "'"
            index += 1
            continue
        if in_double:
            if char == "\\" and index + 1 < length:
                live.append(command[index : index + 2])
                index += 2
                continue
            live.append(char)
            in_double = char != '"'
            index += 1
            continue
        if char == "\\" and index + 1 < length:
            live.append(command[index : index + 2])
            index += 2
            continue
        if char == "'":
            in_single = True
            live.append(char)
            index += 1
            continue
        if char == '"':
            in_double = True
            live.append(char)
            index += 1
            continue
        if arith_parens:
            if char == "(":
                arith_parens += 1
            elif char == ")":
                arith_parens -= 1
            live.append(char)
            index += 1
            continue
        if char == "(" and command[index : index + 2] == "((":
            arith_parens = 2
            live.append("((")
            index += 2
            continue
        if char == "<" and command[index : index + 3] == "<<<":
            live.append("<<<")
            index += 3
            continue
        if char == "<" and command[index : index + 2] == "<<":
            operator_end, delimiter, strip_tabs = parse_heredoc_delimiter(command, index + 2)
            live.append(command[index:operator_end])
            index = operator_end
            if delimiter:
                pending.append((delimiter, strip_tabs))
            continue
        if char == "\n":
            live.append(char)
            index += 1
            for delimiter, strip_tabs in pending:
                while index < length:
                    line_end = command.find("\n", index)
                    if line_end < 0:
                        line_end = length
                    line = command[index:line_end].rstrip("\r")
                    index = line_end + 1
                    if (line.lstrip("\t") if strip_tabs else line) == delimiter:
                        break
            pending = []
            continue
        live.append(char)
        index += 1
    return "".join(live)


def command_executables(tokens: list[str]) -> list[str]:
    executables: list[str] = []
    expect_command = True
    for index, token in enumerate(tokens):
        if not token:
            continue
        if token in SHELL_CONTROL_TOKENS:
            expect_command = True
            continue
        if token in REDIRECTION_TOKENS or token in HEREDOC_TOKENS:
            expect_command = False
            continue
        if token.isdigit() and index + 1 < len(tokens) and tokens[index + 1] in REDIRECTION_TOKENS:
            continue
        if expect_command:
            if is_env_assignment_token(token):
                continue
            executables.append(token)
            expect_command = False
    return executables


def explicit_command_path_candidates(tokens: list[str]) -> list[str]:
    candidates: list[str] = []
    index = 0
    current_command: str | None = None
    current_args: list[str] = []
    while index < len(tokens):
        token = tokens[index]
        if token in SHELL_CONTROL_TOKENS:
            candidates.extend(command_argument_path_candidates(current_command, current_args))
            current_command = None
            current_args = []
            index += 1
            continue
        if token.isdigit() and index + 1 < len(tokens) and tokens[index + 1] in REDIRECTION_TOKENS:
            index += 1
            continue
        if token in REDIRECTION_TOKENS:
            if index + 1 < len(tokens):
                candidates.append(tokens[index + 1])
            index += 2
            continue
        if token in HEREDOC_TOKENS:
            index += 2
            continue
        if current_command is None:
            if not is_env_assignment_token(token):
                current_command = token
        else:
            current_args.append(token)
        index += 1
    candidates.extend(command_argument_path_candidates(current_command, current_args))
    return list(dict.fromkeys(candidates))


def command_argument_path_candidates(command: str | None, args: list[str]) -> list[str]:
    if not command:
        return []
    name = PurePosixPath(command.replace("\\", "/")).name.lower()
    if name == "env":
        candidates, wrapped_command, wrapped_args = env_wrapped_command(args)
        if wrapped_command is not None:
            candidates.extend(command_argument_path_candidates(wrapped_command, wrapped_args))
        return candidates
    if name in PATH_ARGUMENT_COMMANDS:
        return [arg for arg in args if is_inspectable_path_argument(arg)]
    if name in PATTERN_THEN_PATH_COMMANDS:
        return pattern_command_path_candidates(args)
    if name == "find":
        return find_command_path_candidates(args)
    if name in SCRIPT_COMMANDS:
        return script_command_path_candidates(name, args)
    return []


def inline_script_command(command: str) -> dict[str, str] | None:
    try:
        tokens = shlex_split(command)
    except ValueError:
        tokens = command.split()
    index = 0
    current_command: str | None = None
    current_args: list[str] = []
    while index < len(tokens):
        token = tokens[index]
        if token in SHELL_CONTROL_TOKENS:
            result = inline_script_segment(current_command, current_args)
            if result is not None:
                return result
            current_command = None
            current_args = []
            index += 1
            continue
        if token.isdigit() and index + 1 < len(tokens) and tokens[index + 1] in REDIRECTION_TOKENS:
            index += 1
            continue
        if token in HEREDOC_TOKENS:
            result = stdin_script_segment(current_command, current_args, token)
            if result is not None:
                return result
            index += 2
            continue
        if token in REDIRECTION_TOKENS:
            index += 2
            continue
        if current_command is None:
            if not is_env_assignment_token(token):
                current_command = token
        else:
            current_args.append(token)
        index += 1
    return inline_script_segment(current_command, current_args)


def inline_script_segment(command: str | None, args: list[str]) -> dict[str, str] | None:
    if not command:
        return None
    name = PurePosixPath(command.replace("\\", "/")).name.lower()
    if name == "env":
        _candidates, wrapped_command, wrapped_args = env_wrapped_command(args)
        return inline_script_segment(wrapped_command, wrapped_args)
    if name in {"bash", "sh", "zsh"}:
        for arg in args:
            if arg.startswith("-") and "c" in arg.lstrip("-"):
                return {"command": name, "option": arg}
        return None
    if name in {"python", "python3"}:
        if "-c" in args:
            return {"command": name, "option": "-c"}
        if "-" in args:
            return {"command": name, "option": "-"}
        return None
    if name == "node":
        for option in ("-e", "--eval", "-p", "--print"):
            if option in args:
                return {"command": name, "option": option}
    if name in {"ruby", "perl"} and "-e" in args:
        return {"command": name, "option": "-e"}
    return None


def env_wrapped_command(args: list[str]) -> tuple[list[str], str | None, list[str]]:
    candidates: list[str] = []
    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "--":
            index += 1
            break
        if arg in {"-S", "--split-string"}:
            if index + 1 >= len(args):
                return candidates, None, []
            return env_split_command(candidates, args[index + 1])
        if arg.startswith("--split-string="):
            return env_split_command(candidates, arg.split("=", 1)[1])
        if arg.startswith("-S") and arg != "-S":
            return env_split_command(candidates, arg[2:])
        if arg in {"-C", "--chdir"}:
            if index + 1 >= len(args):
                return candidates, None, []
            candidates.append(args[index + 1])
            index += 2
            continue
        if arg.startswith("--chdir="):
            candidates.append(arg.split("=", 1)[1])
            index += 1
            continue
        if arg.startswith("-C") and arg != "-C":
            candidates.append(arg[2:])
            index += 1
            continue
        if arg in ENV_OPTIONS_WITH_ARGUMENT:
            index += 2
            continue
        if any(arg.startswith(f"{option}=") for option in ENV_LONG_OPTIONS_WITH_ARGUMENT):
            index += 1
            continue
        if any(arg.startswith(f"{option}=") for option in ENV_LONG_OPTIONS_WITH_OPTIONAL_ARGUMENT):
            index += 1
            continue
        if any(arg.startswith(prefix) and arg != prefix for prefix in ENV_SHORT_OPTIONS_WITH_ATTACHED_ARGUMENT):
            index += 1
            continue
        if arg in ENV_FLAG_OPTIONS:
            index += 1
            continue
        if arg.startswith("-") or is_env_assignment_token(arg):
            index += 1
            continue
        return candidates, arg, args[index + 1 :]
    if index < len(args):
        return candidates, args[index], args[index + 1 :]
    return candidates, None, []


def env_split_command(candidates: list[str], command: str) -> tuple[list[str], str | None, list[str]]:
    try:
        tokens = shlex_split(command)
    except ValueError:
        tokens = command.split()
    if not tokens:
        return candidates, None, []
    return candidates, tokens[0], tokens[1:]


def stdin_script_segment(command: str | None, args: list[str], redirection: str) -> dict[str, str] | None:
    if not command:
        return None
    name = PurePosixPath(command.replace("\\", "/")).name.lower()
    if name not in SCRIPT_COMMANDS:
        return None
    if name in {"python", "python3"} and "-m" in args:
        return None
    for arg in args:
        if not arg.startswith("-") or arg == "-":
            return None
    return {"command": name, "option": redirection}


def pattern_command_path_candidates(args: list[str]) -> list[str]:
    candidates: list[str] = []
    pattern_consumed = False
    skip_next = False
    for arg in args:
        if skip_next:
            skip_next = False
            continue
        if arg in {"-e", "-f", "--regexp", "--file", "-g", "--glob"}:
            skip_next = True
            continue
        if arg.startswith("-"):
            continue
        if not pattern_consumed:
            pattern_consumed = True
            continue
        if is_inspectable_path_argument(arg):
            candidates.append(arg)
    return candidates


def find_command_path_candidates(args: list[str]) -> list[str]:
    candidates: list[str] = []
    for arg in args:
        if arg in {"!", "(", ")"} or arg.startswith("-"):
            break
        if is_inspectable_path_argument(arg):
            candidates.append(arg)
    return candidates


def script_command_path_candidates(command_name: str, args: list[str]) -> list[str]:
    skip_next = False
    for arg in args:
        if skip_next:
            skip_next = False
            continue
        if command_name in {"bash", "sh", "zsh"} and arg.startswith("-") and "c" in arg.lstrip("-"):
            return []
        if command_name in {"python", "python3"} and arg == "-c":
            return []
        if command_name == "node" and arg in {"-e", "--eval", "-p", "--print"}:
            return []
        if command_name in {"ruby", "perl"} and arg == "-e":
            return []
        if arg in {"-m", "--require", "-r"}:
            skip_next = True
            continue
        if arg.startswith("-"):
            continue
        if command_name.startswith("python") and arg == "-":
            return []
        return [arg] if is_inspectable_path_argument(arg) else []
    return []


def is_env_assignment_token(token: str) -> bool:
    return bool(re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", token))


def is_inspectable_path_argument(token: str) -> bool:
    if not token or token.startswith("-"):
        return False
    normalized = token.replace("\\", "/")
    if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*://", normalized):
        return False
    if normalized.startswith(("/", "~", "./", "../")) or re.match(r"^[A-Za-z]:/", normalized):
        return True
    if "/" in normalized:
        return True
    return "." in PurePosixPath(normalized).name


def is_literal_network_reference_command(command: str) -> bool:
    try:
        tokens = shlex_split(command)
    except ValueError:
        return False
    executables = command_executables(tokens)
    if not executables:
        return False
    return all(
        PurePosixPath(executable.replace("\\", "/")).name.lower() in NETWORK_LITERAL_COMMANDS
        for executable in executables
    )


def entry_for_path(path: Path, root: Path) -> dict[str, Any]:
    stat = path.lstat()
    if path.is_symlink():
        kind = "symlink"
    elif path.is_dir():
        kind = "directory"
    elif path.is_file():
        kind = "file"
    else:
        kind = "other"
    item: dict[str, Any] = {
        "name": path.name,
        "path": normalize_rel_display(path, root),
        "type": kind,
        "size_bytes": stat.st_size,
        "modified": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat().replace("+00:00", "Z"),
        "is_hidden": path.name.startswith("."),
        "is_ignored": False,
    }
    if path.is_symlink():
        try:
            item["symlink_target"] = os.readlink(path)
        except OSError:
            pass
    return item


def sort_value(item: dict[str, Any], sort_key: str) -> Any:
    if sort_key == "type":
        return (item.get("type", ""), item.get("name", ""))
    if sort_key == "modified":
        return (item.get("modified", ""), item.get("name", ""))
    return item.get("name", "")


def parse_branch_line(line: str) -> tuple[str, str, int, int]:
    branch = line
    upstream = ""
    ahead = 0
    behind = 0
    if "..." in line:
        branch, rest = line.split("...", 1)
        upstream = rest.split(" ", 1)[0]
    if "[" in line and "]" in line:
        meta = line.split("[", 1)[1].split("]", 1)[0]
        ahead_match = re.search(r"ahead (\d+)", meta)
        behind_match = re.search(r"behind (\d+)", meta)
        ahead = int(ahead_match.group(1)) if ahead_match else 0
        behind = int(behind_match.group(1)) if behind_match else 0
    return branch.strip(), upstream.strip(), ahead, behind


def require_git() -> str:
    git = cached_which("git")
    if not git:
        raise ToolFailure("GIT_ERROR", "git executable not found.", category="runtime")
    return git


def validate_git_ref(ref: str) -> str:
    if not ref or ref.startswith("-") or "\x00" in ref or "\n" in ref or "\r" in ref:
        raise ToolFailure("INVALID_ARGUMENT", "Invalid git revision.", category="validation")
    return ref


def parse_git_blame_porcelain(output: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    current: dict[str, Any] = {}
    for raw in output.splitlines():
        parts = raw.split()
        if len(parts) >= 3 and re.fullmatch(r"[0-9a-fA-F^]{40}", parts[0]):
            current = {
                "commit": parts[0].lstrip("^"),
                "original_line": int(parts[1]) if parts[1].isdigit() else None,
                "line": int(parts[2]) if parts[2].isdigit() else None,
            }
            continue
        if raw.startswith("author "):
            current["author"] = raw.removeprefix("author ")
            continue
        if raw.startswith("author-mail "):
            current["author_mail"] = raw.removeprefix("author-mail ").strip("<>")
            continue
        if raw.startswith("author-time "):
            value = raw.removeprefix("author-time ")
            current["author_time"] = int(value) if value.isdigit() else value
            continue
        if raw.startswith("summary "):
            current["summary"] = raw.removeprefix("summary ")
            continue
        if raw.startswith("\t"):
            row = dict(current)
            row["content"] = raw[1:]
            rows.append(row)
    return rows


def redact_for_trace(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): "[REDACTED]" if SENSITIVE_ENV_RE.search(str(key)) else redact_for_trace(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_for_trace(item) for item in value[:50]]
    if isinstance(value, tuple):
        return [redact_for_trace(item) for item in value[:50]]
    if isinstance(value, str):
        if SENSITIVE_VALUE_RE.search(value):
            return "[REDACTED]"
        if len(value) > 240:
            return value[:240] + "...[truncated]"
        return value
    return value


class LandlockRulesetAttr(ctypes.Structure):
    _fields_ = [("handled_access_fs", ctypes.c_uint64)]


class LandlockPathBeneathAttr(ctypes.Structure):
    _fields_ = [("allowed_access", ctypes.c_uint64), ("parent_fd", ctypes.c_int)]


def landlock_abi_version() -> int:
    if sys.platform != "linux":
        raise ToolFailure(
            "SANDBOX_UNAVAILABLE",
            "Linux Landlock filesystem confinement is unavailable on this platform.",
            category="security",
        )
    version = libc_syscall(SYS_LANDLOCK_CREATE_RULESET, 0, 0, LANDLOCK_CREATE_RULESET_VERSION)
    if version <= 0:
        err = ctypes.get_errno()
        raise ToolFailure(
            "SANDBOX_UNAVAILABLE",
            "Linux Landlock filesystem confinement is unavailable on this host.",
            category="security",
            details={"errno": err, "reason": os.strerror(err) if err else "unknown"},
        )
    return version


def landlock_handled_access(version: int) -> int:
    handled = (
        LANDLOCK_ACCESS_FS_EXECUTE
        | LANDLOCK_ACCESS_FS_WRITE_FILE
        | LANDLOCK_ACCESS_FS_READ_FILE
        | LANDLOCK_ACCESS_FS_READ_DIR
        | LANDLOCK_ACCESS_FS_REMOVE_DIR
        | LANDLOCK_ACCESS_FS_REMOVE_FILE
        | LANDLOCK_ACCESS_FS_MAKE_CHAR
        | LANDLOCK_ACCESS_FS_MAKE_DIR
        | LANDLOCK_ACCESS_FS_MAKE_REG
        | LANDLOCK_ACCESS_FS_MAKE_SOCK
        | LANDLOCK_ACCESS_FS_MAKE_FIFO
        | LANDLOCK_ACCESS_FS_MAKE_BLOCK
        | LANDLOCK_ACCESS_FS_MAKE_SYM
    )
    if version >= 2:
        handled |= LANDLOCK_ACCESS_FS_REFER
    if version >= 3:
        handled |= LANDLOCK_ACCESS_FS_TRUNCATE
    if version >= 5:
        handled |= LANDLOCK_ACCESS_FS_IOCTL_DEV
    return handled


def landlock_device_access(handled: int) -> int:
    readonly_file_access = handled & (LANDLOCK_ACCESS_FS_EXECUTE | LANDLOCK_ACCESS_FS_READ_FILE)
    return readonly_file_access | (
        handled
        & (
            LANDLOCK_ACCESS_FS_WRITE_FILE
            | LANDLOCK_ACCESS_FS_TRUNCATE
            | LANDLOCK_ACCESS_FS_IOCTL_DEV
        )
    )


def open_landlock_ruleset(workspace: Path, read_roots: list[str], *, write_roots: list[Path] | None = None) -> int:
    version = landlock_abi_version()
    handled = landlock_handled_access(version)
    ruleset_attr = LandlockRulesetAttr(handled)
    ruleset_fd = libc_syscall(
        SYS_LANDLOCK_CREATE_RULESET,
        ctypes.byref(ruleset_attr),
        ctypes.sizeof(ruleset_attr),
        0,
    )
    if ruleset_fd < 0:
        err = ctypes.get_errno()
        raise ToolFailure(
            "SANDBOX_UNAVAILABLE",
            "Failed to create Linux Landlock ruleset for exec_command.",
            category="security",
            details={"errno": err, "reason": os.strerror(err) if err else "unknown"},
        )
    try:
        workspace_access = handled
        readonly_access = handled & (
            LANDLOCK_ACCESS_FS_EXECUTE | LANDLOCK_ACCESS_FS_READ_FILE | LANDLOCK_ACCESS_FS_READ_DIR
        )
        device_access = landlock_device_access(handled)
        add_landlock_path(ruleset_fd, workspace, workspace_access)
        for write_root in write_roots or []:
            add_landlock_path(ruleset_fd, write_root, workspace_access, required=False)
        for read_root in read_roots:
            add_landlock_path(ruleset_fd, Path(read_root), readonly_access, required=False)
        for special in SPECIAL_DEVICE_PATHS:
            add_landlock_path(ruleset_fd, Path(special), device_access, required=False)
        for special_dir in ("/proc/self", "/proc/thread-self", "/dev/fd"):
            add_landlock_path(ruleset_fd, Path(special_dir), readonly_access, required=False)
    except Exception:
        os.close(ruleset_fd)
        raise
    return ruleset_fd


def add_landlock_path(ruleset_fd: int, path: Path, allowed_access: int, *, required: bool = True) -> None:
    try:
        fd = os.open(path, getattr(os, "O_PATH", os.O_RDONLY) | os.O_CLOEXEC)
    except OSError as exc:
        if required:
            raise ToolFailure(
                "SANDBOX_UNAVAILABLE",
                "Failed to open path while preparing Landlock sandbox.",
                category="security",
                details={"path": str(path), "errno": exc.errno, "reason": exc.strerror},
            ) from exc
        return
    try:
        path_attr = LandlockPathBeneathAttr(allowed_access & landlock_path_allowed_access(path), fd)
        rc = libc_syscall(SYS_LANDLOCK_ADD_RULE, ruleset_fd, LANDLOCK_RULE_PATH_BENEATH, ctypes.byref(path_attr), 0)
        if rc < 0 and required:
            err = ctypes.get_errno()
            raise ToolFailure(
                "SANDBOX_UNAVAILABLE",
                "Failed to add path to Landlock sandbox.",
                category="security",
                details={"path": str(path), "errno": err, "reason": os.strerror(err) if err else "unknown"},
            )
    finally:
        os.close(fd)


def landlock_path_allowed_access(path: Path) -> int:
    try:
        mode = path.stat().st_mode
    except OSError:
        return ~0
    if stat.S_ISDIR(mode):
        return ~0
    return (
        LANDLOCK_ACCESS_FS_EXECUTE
        | LANDLOCK_ACCESS_FS_WRITE_FILE
        | LANDLOCK_ACCESS_FS_READ_FILE
        | LANDLOCK_ACCESS_FS_TRUNCATE
        | LANDLOCK_ACCESS_FS_IOCTL_DEV
    )


def landlock_exec_argv(ruleset_fd: int, cmd: str) -> list[str]:
    helper = Path(__file__).with_name("landlock_exec.py")
    return [sys.executable, str(helper), str(ruleset_fd), cmd]


def is_default_system_path_root(resolved: Path) -> bool:
    for prefix_path in _resolved_system_path_root_prefixes():
        if resolved == prefix_path or is_relative_to(resolved, prefix_path):
            return True
    return False


@functools.lru_cache(maxsize=1)
def _resolved_system_path_root_prefixes() -> tuple[Path, ...]:
    prefixes: list[Path] = []
    for prefix in SYSTEM_PATH_ROOT_PREFIXES:
        try:
            prefixes.append(Path(prefix).resolve())
        except OSError:
            prefixes.append(Path(prefix))
    return tuple(prefixes)


def guard_allow_roots() -> list[str]:
    # Keyed on the env vars the computation reads, so repeated exec_command
    # calls skip the dozens of Path.resolve()/is_dir() syscalls while env
    # changes still invalidate the cache.
    return list(
        _guard_allow_roots_cached(
            os.environ.get("JAVA_HOME", ""),
            os.environ.get("PATH", ""),
            os.environ.get(f"{ENV_PREFIX}_EXEC_ALLOW_ROOTS", ""),
        )
    )


@functools.lru_cache(maxsize=8)
def _guard_allow_roots_cached(java_home: str, path_env: str, extra_roots: str) -> tuple[str, ...]:
    roots = set(TOOLCHAIN_READ_ROOTS)
    roots.update(OS_METADATA_READ_FILES)
    roots.update(GIT_READ_ROOTS)
    roots.update(DNS_RESOLVER_READ_ROOTS)
    roots.update(
        {
            str(Path(sys.executable).resolve().parent),
            str(Path(sys.prefix).resolve()),
            str(Path(sys.base_prefix).resolve()),
        }
    )
    if java_home:
        try:
            resolved_java_home = Path(java_home).expanduser().resolve()
        except OSError:
            pass
        else:
            roots.add(str(resolved_java_home))
    for item in path_env.split(os.pathsep):
        if not item:
            continue
        try:
            resolved = Path(item).resolve()
        except OSError:
            continue
        if resolved.is_dir() and is_default_system_path_root(resolved):
            roots.add(str(resolved))
    for item in extra_roots.split(os.pathsep):
        if not item:
            continue
        try:
            resolved = Path(item).expanduser().resolve()
        except OSError:
            continue
        if resolved.is_dir():
            roots.add(str(resolved))
    return tuple(sorted(root for root in roots if root and Path(root).is_absolute()))


def parse_diff_files(diff_text: str) -> list[dict[str, Any]]:
    files: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4:
                path = parts[3][2:] if parts[3].startswith("b/") else parts[3]
                current = {"path": path, "status": "modified", "binary": False}
                files.append(current)
        elif current is not None and line.startswith("new file mode"):
            current["status"] = "added"
        elif current is not None and line.startswith("deleted file mode"):
            current["status"] = "deleted"
        elif current is not None and line.startswith("Binary files"):
            current["binary"] = True
    return files


def identify_image(data: bytes, path: Path) -> tuple[str | None, int | None, int | None]:
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        width = int.from_bytes(data[16:20], "big")
        height = int.from_bytes(data[20:24], "big")
        return "image/png", width, height
    if data.startswith(b"GIF87a") or data.startswith(b"GIF89a"):
        width = int.from_bytes(data[6:8], "little")
        height = int.from_bytes(data[8:10], "little")
        return "image/gif", width, height
    if data.startswith(b"\xff\xd8"):
        image_width, image_height = identify_jpeg_size(data)
        return "image/jpeg", image_width, image_height
    if data.startswith(b"RIFF") and len(data) >= 12 and data[8:12] == b"WEBP":
        image_width, image_height = identify_webp_size(data)
        return "image/webp", image_width, image_height
    guessed, _ = mimetypes.guess_type(path.name)
    if guessed and guessed.startswith("image/"):
        return guessed, None, None
    return None, None, None


def identify_jpeg_size(data: bytes) -> tuple[int | None, int | None]:
    index = 2
    while index + 9 < len(data):
        while index < len(data) and data[index] == 0xFF:
            index += 1
        if index >= len(data):
            break
        marker = data[index]
        index += 1
        if marker in {0xD8, 0xD9}:
            continue
        if marker == 0xDA or index + 2 > len(data):
            break
        segment_length = int.from_bytes(data[index : index + 2], "big")
        if segment_length < 2 or index + segment_length > len(data):
            break
        if marker in {
            0xC0,
            0xC1,
            0xC2,
            0xC3,
            0xC5,
            0xC6,
            0xC7,
            0xC9,
            0xCA,
            0xCB,
            0xCD,
            0xCE,
            0xCF,
        } and segment_length >= 7:
            height = int.from_bytes(data[index + 3 : index + 5], "big")
            width = int.from_bytes(data[index + 5 : index + 7], "big")
            return width, height
        index += segment_length
    return None, None


def identify_webp_size(data: bytes) -> tuple[int | None, int | None]:
    if len(data) < 30:
        return None, None
    chunk = data[12:16]
    if chunk == b"VP8X" and len(data) >= 30:
        width = int.from_bytes(data[24:27], "little") + 1
        height = int.from_bytes(data[27:30], "little") + 1
        return width, height
    if chunk == b"VP8 " and len(data) >= 30 and data[23:26] == b"\x9d\x01\x2a":
        width = int.from_bytes(data[26:28], "little") & 0x3FFF
        height = int.from_bytes(data[28:30], "little") & 0x3FFF
        return width, height
    if chunk == b"VP8L" and len(data) >= 25 and data[20] == 0x2F:
        bits = int.from_bytes(data[21:25], "little")
        width = (bits & 0x3FFF) + 1
        height = ((bits >> 14) & 0x3FFF) + 1
        return width, height
    return None, None


def should_resize_image(
    size_bytes: int,
    width: int | None,
    height: int | None,
    max_bytes: int,
    max_width: int,
    max_height: int,
) -> bool:
    if size_bytes > max_bytes:
        return True
    if width is not None and width > max_width:
        return True
    if height is not None and height > max_height:
        return True
    return False


def resize_image_bytes(
    data: bytes,
    mime_type: str,
    *,
    max_width: int,
    max_height: int,
    max_bytes: int,
) -> tuple[bytes, str] | None:
    try:
        from io import BytesIO
        from PIL import Image  # type: ignore[import-not-found]
    except Exception:
        return None
    try:
        image = Image.open(BytesIO(data))
        image.thumbnail((max_width, max_height))
        output = BytesIO()
        output_format = "JPEG" if mime_type == "image/jpeg" else "PNG" if mime_type == "image/png" else "WEBP"
        save_kwargs: dict[str, Any] = {}
        if output_format in {"JPEG", "WEBP"}:
            save_kwargs["quality"] = 85
            save_kwargs["optimize"] = True
        if output_format == "JPEG" and image.mode not in {"RGB", "L"}:
            image = image.convert("RGB")
        image.save(output, format=output_format, **save_kwargs)
        resized = output.getvalue()
        if len(resized) > max_bytes and output_format in {"JPEG", "WEBP"}:
            for quality in (75, 65, 55):
                output = BytesIO()
                image.save(output, format=output_format, quality=quality, optimize=True)
                resized = output.getvalue()
                if len(resized) <= max_bytes:
                    break
        return resized, mime_type
    except Exception:
        return None


def object_schema(properties: dict[str, Any] | None = None, required: list[str] | None = None) -> dict[str, Any]:
    merged = dict(properties or {})
    merged.setdefault(
        "idempotency_key",
        {
            "type": "string",
            "maxLength": 128,
            "description": (
                "Optional durable request identity. Reusing the same key for an identical call "
                "deduplicates the mutation across MCP reconnect/restart; reusing it for a "
                "different call fails closed."
            ),
        },
    )
    return {
        "type": "object",
        "properties": merged,
        "required": required or [],
        "additionalProperties": False,
    }


def tool_output_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "ok": {"type": "boolean"},
            "error": {
                "type": "object",
                "properties": {
                    "code": {"type": "string"},
                    "message": {"type": "string"},
                    "category": {"type": "string"},
                    "retryable": {"type": "boolean"},
                    "details": {"type": "object", "additionalProperties": True},
                },
                "required": ["code", "message", "category", "retryable", "details"],
                "additionalProperties": True,
            },
        },
        "required": ["ok"],
        "additionalProperties": True,
    }


def validate_arguments(tool_name: str, args: dict[str, Any]) -> None:
    schema = input_schemas()[tool_name]
    try:
        validate_schema_value(args, schema, path="arguments")
    except ToolFailure as exc:
        raise JsonRpcError(-32602, exc.message, {"reason": "invalid_arguments", "code": exc.code}) from exc


def validate_schema_value(value: Any, schema: dict[str, Any], *, path: str) -> None:
    expected_type = schema.get("type")
    if expected_type is not None and not schema_type_matches(value, expected_type):
        raise ToolFailure("INVALID_ARGUMENT", f"{path} must be {schema_type_name(expected_type)}.", category="validation")

    if isinstance(value, str):
        min_length = schema.get("minLength")
        if isinstance(min_length, int) and len(value) < min_length:
            raise ToolFailure("INVALID_ARGUMENT", f"{path} is shorter than {min_length}.", category="validation")
        if "enum" in schema and value not in schema["enum"]:
            raise ToolFailure("INVALID_ARGUMENT", f"{path} must be one of {schema['enum']!r}.", category="validation")

    if isinstance(value, int) and not isinstance(value, bool):
        minimum = schema.get("minimum")
        maximum = schema.get("maximum")
        if isinstance(minimum, (int, float)) and value < minimum:
            raise ToolFailure("INVALID_ARGUMENT", f"{path} must be >= {minimum}.", category="validation")
        if isinstance(maximum, (int, float)) and value > maximum:
            raise ToolFailure("INVALID_ARGUMENT", f"{path} must be <= {maximum}.", category="validation")

    if isinstance(value, list) and isinstance(schema.get("items"), dict):
        item_schema = schema["items"]
        for index, item in enumerate(value):
            validate_schema_value(item, item_schema, path=f"{path}[{index}]")

    if isinstance(value, dict):
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        for key in required:
            if key not in value:
                raise ToolFailure("INVALID_ARGUMENT", f"{path}.{key} is required.", category="validation")
        additional = schema.get("additionalProperties", True)
        for key, item in value.items():
            child_path = f"{path}.{key}"
            if key in properties:
                validate_schema_value(item, properties[key], path=child_path)
            elif additional is False:
                raise ToolFailure("INVALID_ARGUMENT", f"{child_path} is not a recognized argument.", category="validation")
            elif isinstance(additional, dict):
                validate_schema_value(item, additional, path=child_path)


def schema_type_matches(value: Any, expected_type: str | list[str]) -> bool:
    if isinstance(expected_type, list):
        return any(schema_type_matches(value, item) for item in expected_type)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "null":
        return value is None
    if expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "string":
        return isinstance(value, str)
    return False


def schema_type_name(expected_type: str | list[str]) -> str:
    if isinstance(expected_type, list):
        return " or ".join(expected_type)
    return expected_type


def tool_definition(name: str, *, fake_readonly: bool = False) -> dict[str, Any]:
    schemas = input_schemas()
    annotations = tool_annotations(name, fake_readonly=fake_readonly)
    return {
        "name": name,
        "title": annotations["title"],
        "description": TOOL_REGISTRY[name].description,
        "inputSchema": schemas[name],
        "outputSchema": tool_output_schema(),
        "annotations": annotations,
    }


def tool_annotations(name: str, *, fake_readonly: bool = False) -> dict[str, Any]:
    """Return a tool's MCP annotations.

    ``fake_readonly`` serves clients that refuse to call, or prompt on every call
    to, a tool annotated as mutating, which no server-side permission mode can
    influence. It reports every tool as read-only and non-destructive even though
    `apply_patch` and `exec_command` still mutate and still execute. Only
    `tools/list` may pass it: `server_info` and the server card must keep
    reporting the real annotations so the override stays discoverable.
    """
    spec = TOOL_REGISTRY[name]
    if fake_readonly:
        return {
            "title": spec.title,
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": spec.idempotent,
            "openWorldHint": False,
        }
    return {
        "title": spec.title,
        "readOnlyHint": spec.read_only,
        "destructiveHint": spec.destructive,
        "idempotentHint": spec.idempotent,
        "openWorldHint": spec.open_world,
    }


@functools.cache
def input_schemas() -> dict[str, dict[str, Any]]:
    # Cached: callers only read the returned tree, and rebuilding the full
    # ~190-line schema dict on every tools/call dispatch is measurable.
    string = {"type": "string"}
    integer = {"type": "integer"}
    boolean = {"type": "boolean"}
    string_array = {"type": "array", "items": {"type": "string"}}
    return {
        "server_info": object_schema(),
        "agent_workflow": object_schema({
            "workflow": {**string, "enum": ["bugfix", "feature", "greenfield", "refactor", "test_failure", "build_release", "diagnose", "document", "resume", "custom"], "default": "custom", "description": "End-to-end task family. Select the closest intent instead of assembling low-level tools."},
            "phase": {**string, "enum": ["prepare", "execute", "run", "resume"], "default": "prepare", "description": "prepare gathers all context; execute applies a complete plan; run does both when changes are already known; resume restores persisted state and only missing context."},
            "execution_route": {**string, "enum": ["auto", "deterministic", "mini", "luna", "terra", "sol_xhigh", "sol_max", "sol_ultra"], "default": "auto", "description": "Primary implementation route. auto uses Mini for localized bug/test leaves, Luna for harder bounded leaves, otherwise Sol xhigh. Terra is explicit experimental cross-file routing. Sol max/ultra require allow_high_cost=true and are never selected automatically."},
            "allow_high_cost": {**boolean, "default": False, "description": "Explicit acknowledgement required for sol_max or sol_ultra. This never makes those routes automatic."},
            "execution_mode": {**string, "enum": ["auto", "mcp_only", "bounded_candidate", "deep_single_lane", "coordinated_multi_worktree"], "default": "auto", "description": "EOCL execution mode. auto derives the mode from the resolved route. coordinated_multi_worktree is rejected unless runtime coordination readiness is proven."},
            "replan_reason": {**string, "description": "Required when continuing an active orchestration run from REPLAN; creates a new wave instead of silently changing route/authority."},
            "contract_fingerprint": {**string, "maxLength": 512, "description": "Optional settled-contract identity. Non-hash values are deterministically hashed before entering the audit ledger."},
            "idempotency_key": {**string, "maxLength": 128, "description": "Optional durable mutation identity for execute/run. Reusing the same key+request deduplicates across MCP reconnect/restart; conflicting reuse fails closed."},
            "max_auto_steps": {**integer, "minimum": 1, "maximum": 256, "default": 64, "description": "Deterministic admission cap for planned workflow steps; no automatic retry loop is created."},
            "max_tool_hops": {**integer, "minimum": 1, "maximum": 512, "default": 96, "description": "Deterministic admission cap for planned internal tool hops."},
            "max_attempts": {**integer, "minimum": 1, "maximum": 10, "default": 1, "description": "Attempt budget. Current mutation policy remains manual-replan-only; unsafe side effects are never auto-replayed."},
            "max_runtime_seconds": {**integer, "minimum": 1, "maximum": 600, "default": 600, "description": "Upper bound applied to the workflow timeout budget."},
            "max_estimated_credits": {"type": "number", "minimum": 0, "default": 0, "description": "Optional candidate-model estimated-credit ceiling; 0 disables the credit cap. Enforced before mutation when usage economics are available."},
            "objective": {**string, "description": "Concrete task objective, for example 'find and fix the login crash' or 'create a React dashboard from zero'."},
            "path": {**string, "default": ".", "description": "Project path relative to the configured workspace."},
            "workdir": {**string, "description": "Command working directory relative to the workspace; defaults to path."},
            "queries": {"type": "array", "maxItems": 8, "items": string, "description": "Code symbols, errors, or phrases to search concurrently during prepare."},
            "paths": {"type": "array", "maxItems": 20, "items": string, "description": "Likely files to prioritize and read during prepare."},
            "directories": {"type": "array", "maxItems": 40, "items": string, "description": "Directories to create for greenfield or feature workflows."},
            "files": {"type": "array", "maxItems": 40, "items": {"type": "object", "properties": {"path": string, "content": string}, "required": ["path", "content"], "additionalProperties": False}, "description": "Complete new files to create, especially for greenfield projects."},
            "patch": {**string, "description": "One complete apply_patch envelope for existing-file changes."},
            "patches": {"type": "array", "maxItems": 6, "items": string, "description": "Complete related patch envelopes, applied in order."},
            "commands": {"type": "array", "maxItems": 6, "items": string, "description": "Initialization or focused checks to run in order before automatic verification."},
            "verification": {**string, "enum": ["none", "tests", "build", "all"], "description": "Automatic validation level. Defaults are selected from the workflow type."},
            "test_command": string,
            "build_command": string,
            "timeout_seconds": {**integer, "minimum": 1, "maximum": 600, "default": 600},
            "dry_run": {**boolean, "default": False},
            "document": {"type": "object", "additionalProperties": True, "description": "Arguments forwarded to document_workflow when workflow=document."},
        }),
        "workspace_context": object_schema({
            "path": {**string, "default": "."},
            "max_entries": {**integer, "minimum": 1, "maximum": 500, "default": 40},
            "detail": {**string, "enum": ["compact", "full"], "default": "compact", "description": "compact returns only the project, root entries, Git summary and task summary; full includes complete Git and task state."},
        }),
        "codex_bridge": object_schema({
            "action": {**string, "enum": ["status", "models", "threads", "run", "continue", "observe", "interrupt", "close"], "default": "status", "description": "status probes route/capacity state; models lists compact Codex model capabilities; threads lists persisted Desktop history for the current workspace; run starts a new read-only reviewer thread or explicit history fork; continue starts a follow-up only on a bridge-owned thread; observe polls; interrupt stops a bridge-owned turn; close stops the sidecar process tree."},
            "profile": {**string, "enum": ["candidate_mini", "candidate_luna", "cross_file", "deep_code", "consequential", "parallel_extreme", "packet", "scoped", "critical", "history"], "description": "Hidden bridge profile. candidate_mini/luna are no-tools patch candidates; cross_file=Terra high read-only inspection; deep_code=Sol xhigh; consequential=Sol max; parallel_extreme=Sol ultra with multi-agent enabled; packet/scoped/critical/history are review modes."},
            "model": {**string, "maxLength": 80, "description": "Optional Codex model override. Production routing normally uses the profile defaults and records the resolved route."},
            "effort": {**string, "enum": ["low", "medium", "high", "xhigh", "max", "ultra"], "description": "Optional reasoning-effort override. Applied to thread config and turn/start so Desktop ultra defaults do not leak into reviewer lanes."},
            "lifetime": {**string, "enum": ["ephemeral", "persistent"], "default": "ephemeral", "description": "Ephemeral is the default reviewer lifetime. Persistent creates a resumable App Server lane; runtime code must persist and authorize its thread id before later resume."},
            "deadline_ms": {**integer, "minimum": 0, "maximum": 30000, "default": 0, "description": "Optional hard turn deadline. When positive, run/continue waits up to the deadline then interrupts the bridge-owned turn instead of leaving it running."},
            "output_schema": {"type": "object", "additionalProperties": True, "description": "Optional <=8 KiB JSON Schema constraining the final Codex message."},
            "source_thread_id": {**string, "description": "Optional persisted Codex thread id from action=threads. This selects the explicit history profile and forks read-only instead of mutating/resuming the Desktop thread."},
            "prompt": {**string, "maxLength": 20000, "description": "Prompt for action=run or continue. Every turn remains approvalPolicy=never, read-only, and network-disabled."},
            "thread_id": {**string, "description": "Bridge-owned thread id returned by action=run; required for continue/observe/interrupt."},
            "turn_id": {**string, "description": "Bridge-owned turn id returned by action=run."},
            "after_cursor": {**integer, "minimum": 0, "default": 0, "description": "For action=observe, return events newer than this cursor."},
            "wait_ms": {**integer, "minimum": 0, "maximum": 30000, "default": 0, "description": "Bounded wait for action=run/observe; zero returns immediately."},
            "max_events": {**integer, "minimum": 1, "maximum": 100, "default": 50},
            "limit": {**integer, "minimum": 1, "maximum": 50, "default": 10, "description": "Maximum current-workspace threads returned by action=threads."},
        }),
        "prepare_coding_context": object_schema({
            "objective": string,
            "path": {**string, "default": "."},
            "queries": {"type": "array", "maxItems": 12, "items": string},
            "paths": {"type": "array", "maxItems": 40, "items": string},
            "regex": {**boolean, "default": False},
            "case_sensitive": {**boolean, "default": False},
            "include_globs": string_array,
            "exclude_globs": string_array,
            "max_files": {**integer, "minimum": 1, "maximum": 30, "default": 12},
            "max_entries": {**integer, "minimum": 1, "maximum": 500, "default": 120},
            "max_matches_per_query": {**integer, "minimum": 1, "maximum": 100, "default": 20},
            "max_total_bytes": {**integer, "minimum": 4096, "maximum": 1048576, "default": 262144},
            "force_refresh": {**boolean, "default": False},
        }),
        "apply_changes_and_verify": object_schema({
            "objective": string,
            "patch": string,
            "patches": {"type": "array", "maxItems": 10, "items": string},
            "checks": {"type": "array", "maxItems": 8, "items": string},
            "path": {**string, "default": "."},
            "workdir": string,
            "verification": {**string, "enum": ["none", "tests", "build", "all"], "default": "tests"},
            "test_command": string,
            "build_command": string,
            "artifact_paths": string_array,
            "hash_algorithm": {**string, "enum": ["sha256", "sha384", "sha512"], "default": "sha256"},
            "timeout_ms": {**integer, "minimum": 1000, "maximum": 600000, "default": 600000},
            "timeout_seconds": {**integer, "minimum": 1, "maximum": 600, "default": 600},
            "include_diff": {**boolean, "default": True},
            "max_diff_bytes": {**integer, "minimum": 1024, "maximum": 1048576, "default": 131072},
            "dry_run": {**boolean, "default": False},
        }),
        "task_control": object_schema({
            "action": {**string, "enum": ["get", "operation", "start", "update", "pause", "stop", "resume", "clear", "history", "audit", "accept", "reject", "lane", "events", "messages", "ack", "handoff"], "default": "get"},
            "run_id": {**string, "description": "Optional orchestration run id; defaults to the current task projection."},
            "wave_id": {**string, "description": "Optional orchestration wave id; defaults to the current task projection."},
            "operation_id": {**string, "description": "Background operation id returned by a long agent_workflow."},
            "after_seq": {**integer, "minimum": 0, "default": 0, "description": "Durable orchestration event sequence cursor for action=events."},
            "wait_ms": {**integer, "minimum": 0, "maximum": 60000, "default": 0, "description": "Wait up to this many milliseconds for a background operation before returning control."},
            "lane_action": {**string, "enum": ["list", "start", "continue", "observe", "close"], "default": "list", "description": "Manage a durable Codex App Server lane without adding another top-level tool."},
            "lane_id": {**string, "description": "Durable lane id returned by lane_action=start or list."},
            "semantic_key": {**string, "maxLength": 512, "description": "Stable workstream identity. Reuse is based on semantic continuity, not agent identity."},
            "lifecycle": {**string, "enum": ["starting", "active", "waiting", "idle", "closed"], "description": "Optional lane lifecycle filter for lane_action=list."},
            "role": {**string, "maxLength": 100, "description": "Bounded lane role such as executor, reviewer, or investigator."},
            "prompt": {**string, "maxLength": 20000, "description": "Compact delta packet for lane start/continue. The durable ledger stores only a redacted hash/size representation under the prompt key."},
            "summary": {**string, "maxLength": 1000, "description": "Human-readable bounded instruction summary for the coordination ledger."},
            "profile": {**string, "enum": ["candidate_mini", "candidate_luna", "cross_file", "deep_code", "consequential", "parallel_extreme", "packet", "scoped", "critical", "history"], "description": "Codex route profile for a persistent lane."},
            "model": {**string, "maxLength": 80},
            "effort": {**string, "enum": ["low", "medium", "high", "xhigh", "max", "ultra"]},
            "deadline_ms": {**integer, "minimum": 0, "maximum": 30000, "default": 0},
            "turn_id": {**string, "description": "Optional current turn id for lane_action=observe."},
            "after_cursor": {**integer, "minimum": 0, "default": 0},
            "max_events": {**integer, "minimum": 1, "maximum": 100, "default": 50},
            "contract_fingerprint": {**string, "maxLength": 128, "description": "Optional interface/contract fingerprint used by the lane drift gate."},
            "allow_rebase": {**boolean, "default": False, "description": "Allow a lane to continue after base/worktree/contract drift only with a material reason."},
            "message_id": {**string, "description": "Coordination message id required by action=ack."},
            "message_status": {**string, "enum": ["pending", "acknowledged"], "default": "pending"},
            "direction": {**string, "enum": ["chatweb_to_codex", "codex_to_chatweb", "system"]},
            "handoff_action": {**string, "enum": ["get", "record"], "default": "get"},
            "conversation_epoch": {**integer, "minimum": 1, "default": 1},
            "payload": {"type": "object", "additionalProperties": True, "description": "Bounded handoff capsule payload. Raw transcript, source files and command output must not be included."},
            "objective": string,
            "status": {**string, "enum": ["idle", "active", "waiting", "paused", "stopped", "completed", "failed"]},
            "steps": {"type": "array", "items": {"type": "object", "additionalProperties": True}},
            "complete_step_ids": string_array,
            "current_step": string,
            "next_step": string,
            "failure": {"type": ["string", "null"]},
            "reason": string,
            "limit": {**integer, "minimum": 1, "maximum": 100, "default": 20},
        }),
        "read_files": object_schema({
            "files": {"type": "array", "minItems": 1, "maxItems": 50, "items": {"oneOf": [string, {"type": "object", "properties": {"path": string, "start_line": integer, "end_line": integer, "max_lines": integer, "max_bytes": integer}, "required": ["path"], "additionalProperties": False}]}},
            "paths": string_array,
            "max_total_bytes": {**integer, "minimum": 1024, "maximum": 1048576, "default": 262144},
        }),
        "file_batch": object_schema({
            "operations": {"type": "array", "minItems": 1, "maxItems": 100, "items": {
                "type": "object", "properties": {
                    "action": {**string, "enum": ["mkdir", "copy", "move", "delete"]},
                    "path": string, "source": string, "target": string,
                    "parents": boolean, "exist_ok": boolean, "overwrite": boolean,
                }, "required": ["action"], "additionalProperties": False,
            }},
            "dry_run": {**boolean, "default": False},
        }, ["operations"]),
        "command_control": object_schema({
            "action": {**string, "enum": ["poll", "write", "kill", "read"], "default": "poll"},
            "command_id": {**string, "description": "Preferred command handle returned by exec_command."},
            "session_id": {**string, "description": "Deprecated compatibility alias for command_id."},
            "chars": string,
            "yield_time_ms": {**integer, "minimum": 0, "maximum": 30000, "default": 10000},
            "max_output_bytes": {**integer, "minimum": 1, "maximum": 1048576, "default": 65536},
            "consumer_id": {**string, "maxLength": 128, "description": "Optional independent poll cursor identity so multiple clients do not consume each other's command output."},
            "verbosity": {**string, "enum": ["summary", "preview", "full"], "default": "summary"},
            "signal": {**string, "enum": ["TERM", "KILL", "INT"], "default": "TERM"},
            "wait_ms": {**integer, "minimum": 0, "maximum": 30000, "default": 3000},
            "output_ref": string,
            "stream": {**string, "enum": ["stdout", "stderr"]},
            "offset": {**integer, "minimum": 0, "default": 0},
            "limit": {**integer, "minimum": 1, "maximum": 1048576, "default": 65536},
        }),
        "git_inspect": object_schema({
            "action": {**string, "enum": ["status", "diff", "log", "show", "blame"], "default": "status"},
            "path": string, "paths": string_array, "rev": string,
            "staged": boolean, "unstaged": boolean, "include_untracked": boolean, "include_diff": boolean,
            "context_lines": integer, "max_bytes": integer, "max_entries": integer,
            "max_count": integer, "skip": integer, "start_line": integer, "end_line": integer, "max_lines": integer,
        }),
        "document_workflow": object_schema({
            "action": {**string, "enum": ["capabilities", "inspect", "create", "convert", "rebuild"], "default": "inspect", "description": "Use inspect once to read PDF/DOCX/text; use create once to save generated DOCX/Markdown/text with built-in verification."},
            "path": {**string, "description": "Single workspace-relative source path for inspect, or target path for create."},
            "paths": {"type": "array", "maxItems": 20, "items": string, "description": "Workspace-relative document paths to inspect together in one call."},
            "source": {**string, "description": "Workspace-relative source PDF/DOCX/text path for convert or rebuild."},
            "target": {**string, "description": "Workspace-relative output path. Create supports .docx, .md, and .txt."},
            "title": {**string, "description": "Optional DOCX title. Markdown/text content is written exactly as supplied."},
            "content": {**string, "description": "Complete generated document content. Pass it directly once; no Base64, shell, stdin, or patch envelope is needed."},
            "overwrite": {**boolean, "default": False, "description": "Replace an existing target only when explicitly requested."},
            "max_chars": {**integer, "minimum": 1, "maximum": 1000000, "default": 200000, "description": "Maximum extracted source characters returned to the model."},
            "detail": {**string, "enum": ["compact", "layout"], "default": "compact", "description": "compact returns text and essential metadata; layout additionally returns page sizes, images and layout metadata."},
        }),
        "document_extract": object_schema({
            "path": {**string, "minLength": 1},
            "max_chars": {**integer, "minimum": 1, "maximum": 1000000, "default": 200000},
        }, ["path"]),
        "document_create": object_schema({
            "path": {**string, "minLength": 1}, "title": string,
            "content": string, "overwrite": {**boolean, "default": False},
        }, ["path", "content"]),
        "document_convert": object_schema({
            "source": {**string, "minLength": 1}, "target": {**string, "minLength": 1},
            "overwrite": {**boolean, "default": False},
        }, ["source", "target"]),
        "check_exec_environment": object_schema(),
        "get_default_cwd": object_schema(),
        "set_default_cwd": object_schema(
            {
                "path": {**string, "default": "."},
            }
        ),
        "task_state_get": object_schema(),
        "task_state_update": object_schema(
            {
                "objective": string,
                "status": {**string, "enum": ["idle", "active", "paused", "completed", "failed"]},
                "steps": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": string,
                            "text": string,
                            "status": {**string, "enum": ["pending", "in_progress", "completed", "failed"]},
                        },
                        "additionalProperties": False,
                    },
                },
                "complete_step_ids": string_array,
                "current_step": string,
                "next_step": string,
                "failure": {"type": ["string", "null"]},
                "new_task": {**boolean, "default": False},
            }
        ),
        "task_state_clear": object_schema(),
        "task_state_pause": object_schema({"reason": string}),
        "task_state_resume": object_schema({"next_step": string}),
        "task_history_list": object_schema({"limit": {**integer, "minimum": 1, "maximum": 100, "default": 20}}),
        "read_file": object_schema(
            {
                "path": {**string, "minLength": 1},
                "start_line": {**integer, "minimum": 1, "default": 1},
                "end_line": {**integer, "minimum": 1},
                "max_lines": {**integer, "minimum": 1},
                "max_bytes": {**integer, "minimum": 1, "maximum": 1048576, "default": 131072},
                "encoding": {**string, "enum": ["utf-8"], "default": "utf-8"},
            },
            ["path"],
        ),
        "list_dir": object_schema(
            {
                "path": {**string, "default": "."},
                "recursive": {**boolean, "default": False},
                "max_depth": {**integer, "minimum": 1, "maximum": 20, "default": 1},
                "max_entries": {**integer, "minimum": 1, "maximum": 10000, "default": 1000},
                "include_hidden": {**boolean, "default": False},
                "include_ignored": {**boolean, "default": False},
                "sort": {**string, "enum": ["name", "type", "modified"], "default": "name"},
            }
        ),
        "list_files": object_schema(
            {
                "path": {**string, "default": "."},
                "patterns": string_array,
                "glob": string,
                "exclude_patterns": string_array,
                "include_hidden": {**boolean, "default": False},
                "include_ignored": {**boolean, "default": False},
                "max_results": {**integer, "minimum": 1, "maximum": 50000, "default": 5000},
                "sort": {**string, "enum": ["path", "modified"], "default": "path"},
            }
        ),
        "search_text": object_schema(
            {
                "query": {**string, "minLength": 1},
                "path": {**string, "default": "."},
                "regex": {**boolean, "default": False},
                "case_sensitive": {**boolean, "default": False},
                "include_globs": string_array,
                "glob": string,
                "exclude_globs": string_array,
                "context_lines": {**integer, "minimum": 0, "maximum": 5, "default": 0},
                "max_results": {**integer, "minimum": 1, "maximum": 10000, "default": 1000},
                "max_preview_bytes": {**integer, "minimum": 80, "maximum": 4096, "default": 512},
            },
            ["query"],
        ),
        "apply_patch": object_schema({"patch": {**string, "minLength": 1}, "dry_run": {**boolean, "default": False}}, ["patch"]),
        "exec_command": object_schema(
            {
                "cmd": {**string, "minLength": 1},
                "workdir": {**string, "default": "."},
                "cwd": {**string},
                "timeout_ms": {**integer, "minimum": 1, "maximum": 600000, "default": 30000},
                "yield_time_ms": {**integer, "minimum": 0, "maximum": 30000, "default": 10000},
                "max_output_bytes": {**integer, "minimum": 1, "maximum": 1048576, "default": 65536},
                "verbosity": {**string, "enum": ["summary", "preview", "full"]},
                "preview_bytes": {**integer, "minimum": 1, "maximum": 1048576, "default": 4096},
                "stdin": {**string, "default": ""},
                "tty": {**boolean, "default": False},
                "env": {"type": "object", "additionalProperties": {"type": "string"}, "default": {}},
                "principal_id": {
                    **string,
                    "maxLength": 64,
                    "description": "Optional logical client identity (for example chatweb, desktop, supervisor) for per-principal command-slot and retained-output quotas. Defaults to a shared default principal.",
                },
            },
            ["cmd"],
        ),
        "verify_build": object_schema(
            {
                "path": {**string, "default": "."},
                "run_tests": {**boolean, "default": True},
                "run_build": {**boolean, "default": True},
                "test_command": string,
                "build_command": string,
                "artifact_paths": string_array,
                "hash_algorithm": {**string, "enum": ["sha256", "sha384", "sha512"], "default": "sha256"},
                "timeout_seconds": {**integer, "minimum": 1, "maximum": 600, "default": 600},
            }
        ),
        "write_stdin": object_schema(
            {
                "session_id": {**string, "minLength": 1},
                "chars": {**string, "default": ""},
                "yield_time_ms": {**integer, "minimum": 0, "maximum": 30000, "default": 10000},
                "max_output_bytes": {**integer, "minimum": 1, "maximum": 1048576, "default": 65536},
                "verbosity": {**string, "enum": ["summary", "preview", "full"]},
                "preview_bytes": {**integer, "minimum": 1, "maximum": 1048576, "default": 4096},
            },
            ["session_id"],
        ),
        "kill_session": object_schema(
            {
                "session_id": {**string, "minLength": 1},
                "signal": {**string, "enum": ["TERM", "KILL", "INT"], "default": "TERM"},
                "wait_ms": {**integer, "minimum": 0, "maximum": 30000, "default": 5000},
                "max_output_bytes": {**integer, "minimum": 1, "maximum": 1048576, "default": 65536},
                "verbosity": {**string, "enum": ["summary", "preview", "full"]},
                "preview_bytes": {**integer, "minimum": 1, "maximum": 1048576, "default": 4096},
            },
            ["session_id"],
        ),
        "read_output": object_schema(
            {
                "output_ref": {**string, "minLength": 1},
                "stream": {**string, "enum": ["stdout", "stderr"]},
                "offset": {**integer, "minimum": 0, "default": 0},
                "limit": {**integer, "minimum": 1, "maximum": 1048576, "default": 4096},
            },
            ["output_ref"],
        ),
        "git_status": object_schema(
            {
                "path": {**string, "default": "."},
                "include_untracked": {**boolean, "default": True},
                "max_entries": {**integer, "minimum": 1, "maximum": 10000, "default": 1000},
            }
        ),
        "git_diff": object_schema(
            {
                "path": string,
                "paths": string_array,
                "staged": {**boolean, "default": False},
                "unstaged": {**boolean, "default": True},
                "context_lines": {**integer, "minimum": 0, "maximum": 20, "default": 3},
                "max_bytes": {**integer, "minimum": 1, "maximum": 1048576, "default": 262144},
            }
        ),
        "git_log": object_schema(
            {
                "path": {**string, "default": "."},
                "ref": {**string, "default": "HEAD"},
                "max_count": {**integer, "minimum": 1, "maximum": 100, "default": 20},
                "skip": {**integer, "minimum": 0, "maximum": 10000, "default": 0},
            }
        ),
        "git_show": object_schema(
            {
                "rev": {**string, "default": "HEAD"},
                "path": string,
                "paths": string_array,
                "include_diff": {**boolean, "default": True},
                "context_lines": {**integer, "minimum": 0, "maximum": 20, "default": 3},
                "max_bytes": {**integer, "minimum": 1, "maximum": 1048576, "default": 262144},
            }
        ),
        "git_blame": object_schema(
            {
                "path": {**string, "minLength": 1},
                "rev": string,
                "start_line": {**integer, "minimum": 1, "default": 1},
                "end_line": {**integer, "minimum": 1},
                "max_lines": {**integer, "minimum": 1, "maximum": 1000, "default": 200},
            },
            ["path"],
        ),
        "request_permissions": object_schema(
            {
                "tool_name": {**string, "enum": ["exec_command", "apply_patch"]},
                "permission": {
                    **string,
                    "enum": [
                        "network",
                        "destructive_command",
                        "long_timeout",
                        "sensitive_env",
                        "shell_expansion",
                        INLINE_SCRIPT_PERMISSION,
                        "privileged_executable",
                        "write_generated_or_ignored",
                    ],
                },
                "reason": {**string, "minLength": 1},
                "arguments": {"type": "object", "additionalProperties": True},
                "scope": {**string, "enum": ["once", "session"], "default": "once"},
                "ttl_seconds": {**integer, "minimum": 1, "maximum": 3600, "default": 300},
            },
            ["tool_name", "permission", "reason", "arguments"],
        ),
        "view_image": object_schema(
            {
                "path": {**string, "minLength": 1},
                "max_bytes": {**integer, "minimum": 1024, "maximum": 10485760, "default": 5242880},
                "max_width": {**integer, "minimum": 1, "maximum": 10000, "default": IMAGE_RESIZE_MAX_DIMENSION},
                "max_height": {**integer, "minimum": 1, "maximum": 10000, "default": IMAGE_RESIZE_MAX_DIMENSION},
                "auto_resize": {**boolean, "default": True},
            },
            ["path"],
        ),
    }


def _server_card_auth(runtime: Runtime, *, oauth_base_url: str | None = None) -> dict[str, Any]:
    if runtime.oauth_enabled():
        cfg = runtime.oauth_config
        assert cfg is not None
        base = (oauth_base_url or cfg.server_url or "").rstrip("/")
        return {
            "type": "oauth2",
            "scheme": "Bearer",
            "header": "Authorization",
            "authorizationUrl": f"{base}/oauth/authorize",
            "tokenUrl": f"{base}/oauth/token",
        }
    if runtime.auth_token is not None:
        return {"type": "bearer", "scheme": "Bearer", "header": "Authorization"}
    return {"type": "none", "scheme": None, "header": None}


def server_card_payload(runtime: Runtime, *, oauth_base_url: str | None = None) -> dict[str, Any]:
    names = runtime.exposed_tool_names()
    # Always the real annotations, never the tools/list override: this card is
    # what an operator fetches to find out what the endpoint actually does.
    annotations = {name: tool_annotations(name, fake_readonly=False) for name in names}
    read_only = [name for name in names if annotations[name].get("readOnlyHint") is True]
    mutating = [name for name in names if annotations[name].get("readOnlyHint") is not True]
    payload = {
        "protocolVersion": PROTOCOL_VERSION,
        "server": {
            "name": SERVER_NAME,
            "title": SERVER_TITLE,
            "version": __version__,
        },
        "transport": {
            "type": "streamable_http",
            "endpoint": MCP_ENDPOINT_PATH,
            "methods": ["POST", "DELETE", "OPTIONS"],
        },
        "auth": _server_card_auth(runtime, oauth_base_url=oauth_base_url),
        "tools": {
            "count": len(names),
            "names": names,
            "readOnlyHintTrue": read_only,
            "readOnlyHintFalse": mutating,
            "annotationOverride": ("fake_readonly" if runtime.fake_readonly_annotations else None),
        },
        "capabilities": {
            "tools": {"listChanged": False},
        },
    }
    return payload


class MCPHandler(http.server.BaseHTTPRequestHandler):
    server_version = f"CodingToolsMCP/{__version__}"

    @property
    def runtime(self) -> Runtime:
        return cast(Runtime, getattr(self, "_runtime", self.server.control_runtime))  # type: ignore[attr-defined]

    def log_message(self, format: str, *args: Any) -> None:
        print(format % args, file=sys.stderr)

    def send_rpc_error(
        self,
        code: int,
        message: str,
        *,
        status: int = 400,
        request_id: str | int | None = None,
        data: Any = None,
        extra_headers: dict[str, str] | None = None,
        head_only: bool = False,
    ) -> None:
        self.send_json(
            jsonrpc_error(request_id, code, message, data),
            status=status,
            extra_headers=extra_headers,
            head_only=head_only,
        )

    def do_GET(self) -> None:
        if (
            posixpath.normpath(self.path.split("?", 1)[0]) == MCP_ENDPOINT_PATH
            and self.headers.get("MCP-Protocol-Version") == STATELESS_PROTOCOL_VERSION
            and stateless_http_2026_enabled()
        ):
            self.send_rpc_error(-32601, "GET is not supported by stateless MCP 2026-07-28", status=405)
            return
        self.handle_metadata_request(head_only=False)

    def do_HEAD(self) -> None:
        if (
            posixpath.normpath(self.path.split("?", 1)[0]) == MCP_ENDPOINT_PATH
            and self.headers.get("MCP-Protocol-Version") == STATELESS_PROTOCOL_VERSION
            and stateless_http_2026_enabled()
        ):
            self.send_rpc_error(
                -32601,
                "HEAD is not supported by stateless MCP 2026-07-28",
                status=405,
                head_only=True,
            )
            return
        self.handle_metadata_request(head_only=True)

    def do_DELETE(self) -> None:
        request_path = self.path.split("?", 1)[0]
        if posixpath.normpath(request_path) != MCP_ENDPOINT_PATH:
            self.send_json({"error": "Unknown endpoint"}, status=404)
            return
        if not self.is_authorized():
            self.send_unauthorized()
            return
        if (
            self.headers.get("MCP-Protocol-Version") == STATELESS_PROTOCOL_VERSION
            and stateless_http_2026_enabled()
        ):
            self.send_rpc_error(-32601, "DELETE is not supported by stateless MCP 2026-07-28", status=405)
            return
        session_id = self.headers.get("Mcp-Session-Id")
        if not session_id or not self.server.sessions.delete(session_id):  # type: ignore[attr-defined]
            self.send_rpc_error(-32001, "Unknown MCP session", status=404)
            return
        self.send_response(200)
        self.send_header("Content-Length", "0")
        self.send_cors_headers()
        self.end_headers()

    def do_OPTIONS(self) -> None:
        request_path = self.path.split("?", 1)[0]
        if posixpath.normpath(request_path) not in {
            MCP_ENDPOINT_PATH,
            "/.well-known/mcp.json",
            "/.well-known/mcp/server-card.json",
            "/__control/health",
            "/__control/workspace",
            "/__control/roots",
            "/__control/orchestration",
            "/.well-known/oauth-authorization-server",
            "/.well-known/oauth-protected-resource",
            "/oauth/authorize",
            "/oauth/token",
            "/oauth/register",
        }:
            self.send_json({"error": "Unknown endpoint"}, status=404)
            return
        origin = self.headers.get("Origin")
        if origin and not is_allowed_origin(origin):
            self.send_json({"error": "Origin denied"}, status=403)
            return
        self.send_response(204)
        self.send_header("Allow", "GET, HEAD, POST, DELETE, OPTIONS")
        self.send_cors_headers()
        self.end_headers()

    def handle_metadata_request(self, *, head_only: bool) -> None:
        request_path = self.path.split("?", 1)[0]
        normalized = posixpath.normpath(request_path)
        if normalized == "/__control/health":
            if not self.is_authorized():
                self.send_unauthorized(head_only=head_only)
                return
            runtime = self.runtime
            with runtime.sessions_lock:
                active_commands = len(runtime.sessions)
                retained_outputs = len(runtime.output_sessions)
            self.send_json({
                "ready": not runtime._closed,
                "version": __version__,
                "instance_id": runtime.server_instance_id,
                "workspace": str(runtime.workspace.root),
                "default_cwd": runtime.default_cwd_display(),
                "authorized_roots": [str(item) for item in runtime.workspace.authorized_roots if item != runtime.workspace.root],
                "tool_mode": runtime.tool_mode,
                "tool_profile": "smart-v2" if runtime.tool_mode == "smart" else runtime.tool_mode,
                "tool_count": len(runtime.exposed_tool_names()),
                "workspace_generation": runtime.workspace_generation,
                "active_commands": active_commands,
                "retained_outputs": retained_outputs,
                "legacy_session_alias_uses": runtime.legacy_session_alias_uses,
                "http_sessions": self.server.sessions.stats(),
            }, head_only=head_only)
            return
        if normalized == "/__control/orchestration":
            if not self.is_authorized():
                self.send_unauthorized(head_only=head_only)
                return
            self.send_json(self.control_orchestration_snapshot(), head_only=head_only)
            return
        if normalized == "/.well-known/oauth-authorization-server":
            self.handle_oauth_as_metadata(head_only=head_only)
            return
        if normalized in {"/.well-known/oauth-protected-resource", "/.well-known/oauth-protected-resource/mcp"}:
            self.handle_oauth_resource_metadata(head_only=head_only)
            return
        if normalized == "/oauth/authorize" and not head_only:
            self.handle_oauth_authorize_get()
            return
        if normalized == MCP_ENDPOINT_PATH:
            origin = self.headers.get("Origin")
            if origin and not is_allowed_origin(origin):
                self.send_json({"error": "Origin denied"}, status=403, head_only=head_only)
                return
            if not self.is_authorized():
                self.send_unauthorized(head_only=head_only)
                return
            self.send_rpc_error(
                -32000,
                "SSE GET stream is not supported",
                status=405,
                extra_headers={"Allow": "POST, DELETE"},
                head_only=head_only,
            )
            return
        if normalized in {"/.well-known/mcp.json", "/.well-known/mcp/server-card.json"}:
            self.send_json(server_card_payload(self.runtime, oauth_base_url=self.oauth_base_url()), head_only=head_only)
            return
        self.send_json({"error": "Unknown endpoint"}, status=404, head_only=head_only)

    def control_orchestration_snapshot(self) -> dict[str, Any]:
        runtime = self.runtime
        state = runtime.task_state.get()
        projection = state.get("orchestration") if isinstance(state.get("orchestration"), dict) else {}
        ledger = runtime.orchestration_ledger
        run_id = str(projection.get("run_id") or "").strip()
        if not run_id:
            active = ledger.current_active_run()
            if active:
                run_id = str(active.get("run_id") or "").strip()
        summary = ledger.export_summary(run_id) if run_id else {}
        events = summary.get("events") or []
        compact_events = [
            {
                "seq": int(event.get("seq") or 0),
                "event_type": str(event.get("event_type") or ""),
                "state_before": str(event.get("state_before") or ""),
                "state_after": str(event.get("state_after") or ""),
                "event_time": str(event.get("event_time") or ""),
                "payload": json.dumps(event.get("payload") or {}, ensure_ascii=False)[:400],
                "wave_id": str(event.get("wave_id") or "")[:16],
            }
            for event in events[-15:]
        ]
        proofs = [
            {
                "stage_id": str(item.get("stage_id") or ""),
                "status": item.get("status"),
                "duration_ms": item.get("duration_ms"),
                "cache_hit": bool(item.get("cache_hit")),
                "finished_at": str(item.get("finished_at") or ""),
            }
            for item in (summary.get("proofs") or [])[-6:]
        ]
        command = state.get("current_command")
        if isinstance(command, dict):
            command = {key: command.get(key) for key in ("kind", "command", "status", "started_at")}
        return {
            "task": {
                "task_id": state.get("task_id"),
                "objective": str(state.get("objective") or "")[:400],
                "status": state.get("status"),
                "current_step": str(state.get("current_step") or "")[:300],
                "next_step": str(state.get("next_step") or "")[:300],
                "modified_files": [str(item) for item in list(state.get("modified_files") or [])[:10]],
                "current_command": command,
                "updated_at": state.get("updated_at"),
                "pause_reason": str(state.get("pause_reason") or ""),
            },
            "run_id": run_id,
            "run": summary.get("run"),
            "waves": (summary.get("waves") or [])[-3:],
            "events": compact_events,
            "proofs": proofs,
            "delegations": (summary.get("delegations") or [])[-4:],
            "capsule": summary.get("latest_handoff_capsule"),
            "background_operations": ledger.list_background_operations(limit=8),
            "counts": {
                "events": len(events),
                "waves": len(summary.get("waves") or []),
                "checkpoints": len(summary.get("checkpoints") or []),
            },
            "integrity": summary.get("integrity"),
        }

    def handle_control_workspace(self) -> None:
        if not self.is_authorized():
            self.send_unauthorized()
            return
        if self.headers.get_content_type().lower() != "application/json":
            self.send_json({"error": "Content-Type must be application/json"}, status=415)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_json({"error": "Invalid Content-Length"}, status=400)
            return
        if length <= 0 or length > 65536:
            self.send_json({"error": "Invalid request size"}, status=413)
            return
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            workspace = str(payload.get("workspace", "")).strip()
            if not workspace:
                raise ValueError("workspace is required")
            result = self.runtime.switch_workspace(Path(workspace))
        except ToolFailure as exc:
            self.send_json({"error": exc.message, "code": exc.code, "details": exc.details}, status=409)
            return
        except (OSError, ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            self.send_json({"error": str(exc)}, status=400)
            return
        self.send_json(result)

    def handle_control_roots(self) -> None:
        if not self.is_authorized():
            self.send_unauthorized()
            return
        if self.headers.get_content_type().lower() != "application/json":
            self.send_json({"error": "Content-Type must be application/json"}, status=415)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_json({"error": "Invalid Content-Length"}, status=400)
            return
        if length <= 0 or length > 65536:
            self.send_json({"error": "Invalid request size"}, status=413)
            return
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            roots = payload.get("roots", [])
            if not isinstance(roots, list):
                raise ValueError("roots must be an array")
            result = self.runtime.set_authorized_roots([str(item) for item in roots])
        except ToolFailure as exc:
            self.send_json({"error": exc.message, "code": exc.code, "details": exc.details}, status=409)
            return
        except (OSError, ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            self.send_json({"error": str(exc)}, status=400)
            return
        self.send_json(result)

    def do_POST(self) -> None:
        request_path = self.path.split("?", 1)[0]
        normalized = posixpath.normpath(request_path)
        if normalized == "/__control/workspace":
            self.handle_control_workspace()
            return
        if normalized == "/__control/roots":
            self.handle_control_roots()
            return
        if normalized == "/oauth/authorize":
            self.handle_oauth_authorize_post()
            return
        if normalized == "/oauth/token":
            self.handle_oauth_token()
            return
        if normalized == "/oauth/register":
            self.handle_oauth_register()
            return
        if normalized != MCP_ENDPOINT_PATH:
            self.send_rpc_error(-32601, "Unknown endpoint", status=404)
            return
        origin = self.headers.get("Origin")
        if origin and not is_allowed_origin(origin):
            self.send_rpc_error(-32600, "Origin denied", status=403)
            return
        if not self.is_authorized():
            self.send_unauthorized()
            return
        if self.headers.get_content_type().lower() != "application/json":
            self.send_rpc_error(-32600, "Content-Type must be application/json", status=415)
            return
        protocol_version = self.headers.get("MCP-Protocol-Version")
        if protocol_version and not protocol_version_is_supported(protocol_version):
            self.send_rpc_error(
                -32600,
                "Unsupported MCP protocol version",
                data={"supported": list(SUPPORTED_PROTOCOL_VERSIONS), "received": protocol_version},
            )
            return
        raw_length = self.headers.get("Content-Length")
        if raw_length is None:
            self.send_rpc_error(-32600, "Content-Length is required", status=411)
            return
        try:
            length = int(raw_length)
        except ValueError:
            self.send_rpc_error(-32600, "Content-Length must be a non-negative integer")
            return
        if length < 0:
            self.send_rpc_error(-32600, "Content-Length must be a non-negative integer")
            return
        if length > MAX_HTTP_REQUEST_BYTES:
            self.close_connection = True
            self.send_rpc_error(
                -32600,
                "Request body exceeds maximum size",
                status=413,
                data={"max_bytes": MAX_HTTP_REQUEST_BYTES},
            )
            return
        body = self.rfile.read(length)
        try:
            request = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self.send_rpc_error(-32700, "Parse error")
            return
        if isinstance(request, list):
            self.send_rpc_error(-32600, "JSON-RPC batch requests are not supported by Streamable HTTP")
            return
        if not isinstance(request, dict):
            self.send_rpc_error(-32600, "Invalid Request")
            return
        try:
            validate_rpc_envelope(request)
        except JsonRpcError as exc:
            self.send_rpc_error(
                exc.code, exc.message, status=200, request_id=response_id(request), data=exc.data
            )
            return
        method = request.get("method")
        body_protocol_version = request_protocol_version(request)
        modern_marker = (
            protocol_version == STATELESS_PROTOCOL_VERSION
            or body_protocol_version == STATELESS_PROTOCOL_VERSION
        )
        if modern_marker and not stateless_http_2026_enabled():
            self.send_rpc_error(
                -32022,
                "MCP 2026-07-28 stateless HTTP is disabled for this deployment",
                status=400,
                request_id=request.get("id"),
                data={
                    "supported": list(LEGACY_PROTOCOL_VERSIONS),
                    "requested": STATELESS_PROTOCOL_VERSION,
                    "disable_with": STATELESS_HTTP_2026_ENV,
                },
            )
            return
        if modern_marker:
            if protocol_version != STATELESS_PROTOCOL_VERSION or body_protocol_version != STATELESS_PROTOCOL_VERSION:
                self.send_rpc_error(
                    -32020,
                    "Header mismatch: MCP-Protocol-Version must match params._meta protocolVersion",
                    status=400,
                    request_id=request.get("id"),
                )
                return
            header_method = self.headers.get("Mcp-Method")
            if header_method != method:
                self.send_rpc_error(
                    -32020,
                    "Header mismatch: required Mcp-Method must match the JSON-RPC method",
                    status=400,
                    request_id=request.get("id"),
                    data={"header": header_method, "body": method},
                )
                return
            body_name = _request_mcp_name(request)
            if method in {"tools/call", "prompts/get", "resources/read"}:
                header_name_raw = self.headers.get("Mcp-Name")
                header_name = _decode_mcp_name_header(header_name_raw) if header_name_raw else None
                if not body_name or header_name != body_name:
                    self.send_rpc_error(
                        -32020,
                        "Header mismatch: required Mcp-Name must match the named request",
                        status=400,
                        request_id=request.get("id"),
                        data={"header": header_name, "body": body_name},
                    )
                    return
            self._runtime = self.server.control_runtime  # type: ignore[attr-defined]
            self._send_session_header = False
            response = self.handle_rpc(request, stateless_2026=True)
            if response is None:
                self.send_response(202)
                self.send_cors_headers()
                self.end_headers()
                return
            error = response.get("error") if isinstance(response, dict) else None
            status = 404 if isinstance(error, dict) and error.get("code") == -32601 else 200
            self.send_json(response, status=status)
            return
        session_id = self.headers.get("Mcp-Session-Id")
        created_session = False
        if method == "initialize":
            if session_id:
                self.send_rpc_error(
                    -32600, "initialize must not include Mcp-Session-Id", request_id=request.get("id")
                )
                return
            try:
                self._runtime = self.server.sessions.create()  # type: ignore[attr-defined]
            except RuntimeError as exc:
                self.send_rpc_error(-32000, str(exc), status=503, request_id=request.get("id"))
                return
            self._send_session_header = True
            created_session = True
        elif session_id:
            runtime = self.server.sessions.get(session_id)  # type: ignore[attr-defined]
            if runtime is None:
                # Tunnel clients can retain an expired session id while reconnecting.
                # Recreate a compatible initialized session instead of returning a
                # hard 404 that causes an aggressive reconnect loop.
                try:
                    runtime = self.server.sessions.create()  # type: ignore[attr-defined]
                    runtime.initialized = True
                    runtime.protocol_version = protocol_version or PROTOCOL_VERSION
                    self._runtime = runtime
                    self._send_session_header = True
                    created_session = True
                except RuntimeError as exc:
                    self.send_rpc_error(-32000, str(exc), status=503, request_id=request.get("id"))
                    return
            else:
                self._runtime = runtime
                self._send_session_header = True
            if protocol_version and protocol_version != runtime.protocol_version:
                self.send_rpc_error(
                    -32600,
                    "MCP-Protocol-Version does not match the initialized session",
                    request_id=request.get("id"),
                    data={"expected": runtime.protocol_version, "received": protocol_version},
                )
                return
        elif method == "ping":
            self._runtime = self.server.control_runtime  # type: ignore[attr-defined]
        elif method in {"server/discover", "tools/list", "tools/call"}:
            # Compatibility path for stateless/proxying MCP clients. The response
            # includes Mcp-Session-Id so capable clients become stateful after the
            # first request, while discovery no longer fails before initialize.
            try:
                self._runtime = self.server.sessions.create()  # type: ignore[attr-defined]
            except RuntimeError as exc:
                self.send_rpc_error(-32000, str(exc), status=503, request_id=request.get("id"))
                return
            self._runtime.initialized = True
            self._runtime.protocol_version = protocol_version or PROTOCOL_VERSION
            self._send_session_header = True
            created_session = True
        else:
            self.send_rpc_error(-32002, "Server not initialized", request_id=request.get("id"))
            return
        response = self.handle_rpc(request)
        if created_session and response is not None and "error" in response:
            self.server.sessions.delete(self.runtime.http_session_id)  # type: ignore[attr-defined]
            self._send_session_header = False
        if response is None:
            self.send_response(202)
            if getattr(self, "_send_session_header", False):
                self.send_header("Mcp-Session-Id", self.runtime.http_session_id)
            self.send_cors_headers()
            self.end_headers()
            return
        self.send_json(response)

    def handle_rpc(
        self,
        request: dict[str, Any],
        *,
        stateless_2026: bool = False,
    ) -> dict[str, Any] | None:
        try:
            return dispatch_rpc(self.runtime, request, stateless_2026=stateless_2026)
        except Exception as exc:  # noqa: BLE001 - HTTP must always answer with JSON-RPC
            return jsonrpc_error(response_id(request), -32603, str(exc))

    def is_authorized(self) -> bool:
        if not self.runtime.auth_enabled():
            return True
        header = self.headers.get("Authorization", "").strip()
        if self.runtime.auth_token is not None:
            if secrets.compare_digest(header, f"Bearer {self.runtime.auth_token}"):
                return True
        if self.runtime.oauth_config is not None and header.startswith("Bearer "):
            token = header[len("Bearer "):]
            if validate_access_token(token, self.runtime.oauth_config, self.oauth_base_url()):
                return True
        return False

    def oauth_base_url(self) -> str:
        cfg = self.runtime.oauth_config
        if cfg is not None and cfg.server_url:
            return cfg.server_url.rstrip("/")
        trust_proxy = truthy_env(os.environ.get(f"{ENV_PREFIX}_TRUST_PROXY_HEADERS"))
        proto = _first_header_value(self.headers.get("X-Forwarded-Proto")) if trust_proxy else ""
        if trust_proxy and not proto:
            proto = _forwarded_header_param(self.headers.get("Forwarded"), "proto")
        host = _safe_external_host(_first_header_value(self.headers.get("X-Forwarded-Host"))) if trust_proxy else ""
        if trust_proxy and not host:
            host = _safe_external_host(_forwarded_header_param(self.headers.get("Forwarded"), "host"))
        if not host:
            host = _safe_external_host(self.headers.get("Host", ""))
        if not host:
            server_address = cast(tuple[Any, ...], self.server.server_address)  # type: ignore[attr-defined]
            bind_host = server_address[0]
            bind_port = server_address[1]
            host = _http_base_for_bind_host(str(bind_host), int(bind_port)).removeprefix("http://")
        if proto not in {"http", "https"}:
            host_without_port = host.rsplit(":", 1)[0].strip("[]")
            proto = "http" if is_loopback_bind_host(host_without_port) else "https"
        return f"{proto}://{host}".rstrip("/")

    def send_unauthorized(self, *, head_only: bool = False) -> None:
        if self.runtime.oauth_config is not None:
            base = self.oauth_base_url()
            www_auth = f'Bearer realm="coding-tools-mcp", resource_metadata="{base}/.well-known/oauth-protected-resource"'
        else:
            www_auth = 'Bearer realm="coding-tools-mcp"'
        self.send_rpc_error(
            -32000,
            "Unauthorized",
            status=401,
            extra_headers={"WWW-Authenticate": www_auth},
            head_only=head_only,
        )

    def handle_oauth_as_metadata(self, *, head_only: bool = False) -> None:
        cfg = self.runtime.oauth_config
        if cfg is None:
            self.send_json({"error": "OAuth not configured"}, status=404, head_only=head_only)
            return
        base = self.oauth_base_url()
        self.send_json(
            {
                "issuer": base,
                "authorization_endpoint": f"{base}/oauth/authorize",
                "token_endpoint": f"{base}/oauth/token",
                "registration_endpoint": f"{base}/oauth/register",
                "response_types_supported": ["code"],
                "grant_types_supported": ["authorization_code"],
                "code_challenge_methods_supported": ["S256"],
                "token_endpoint_auth_methods_supported": list(OAUTH_TOKEN_AUTH_METHODS),
            },
            head_only=head_only,
        )

    def handle_oauth_resource_metadata(self, *, head_only: bool = False) -> None:
        cfg = self.runtime.oauth_config
        if cfg is None:
            self.send_json({"error": "OAuth not configured"}, status=404, head_only=head_only)
            return
        base = self.oauth_base_url()
        self.send_json(
            {"resource": f"{base}{MCP_ENDPOINT_PATH}", "authorization_servers": [base], "bearer_methods_supported": ["header"]},
            head_only=head_only,
        )

    def _send_html(self, body: str, *, status: int = 200) -> None:
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _oauth_login_page(
        self,
        *,
        client_id: str,
        redirect_uri: str,
        code_challenge: str,
        code_challenge_method: str,
        state: str,
        resource: str,
        error: str = "",
    ) -> str:
        def esc(v: str) -> str:
            return html.escape(v, quote=True)
        error_block = f'<p style="color:red">{html.escape(error)}</p>' if error else ""
        return (
            "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
            "<title>Authorize MCP Server</title>"
            "<style>body{font-family:sans-serif;max-width:380px;margin:4rem auto;padding:1rem}"
            "input{width:100%;padding:.5rem;margin:.4rem 0;box-sizing:border-box}"
            "button{width:100%;padding:.7rem;background:#0066cc;color:#fff;border:none;cursor:pointer}</style>"
            "</head><body>"
            f"<h2>Authorize Coding Tools MCP</h2>"
            f"<p>Client: <strong>{esc(client_id)}</strong></p>"
            f"<p>Redirect URI: <code>{esc(redirect_uri)}</code></p>"
            f"{error_block}"
            "<form method='POST' action='/oauth/authorize'>"
            f"<input type='hidden' name='client_id' value='{esc(client_id)}'>"
            f"<input type='hidden' name='redirect_uri' value='{esc(redirect_uri)}'>"
            f"<input type='hidden' name='code_challenge' value='{esc(code_challenge)}'>"
            f"<input type='hidden' name='code_challenge_method' value='{esc(code_challenge_method)}'>"
            f"<input type='hidden' name='state' value='{esc(state)}'>"
            f"<input type='hidden' name='resource' value='{esc(resource)}'>"
            "<label>Password<input type='password' name='password' autocomplete='current-password' required></label>"
            "<button type='submit'>Authorize</button>"
            "</form></body></html>"
        )

    def _read_oauth_body(self) -> bytes | None:
        raw_len = self.headers.get("Content-Length")
        if raw_len is None:
            self.send_json({"error": "Content-Length required"}, status=411)
            return None
        try:
            length = int(raw_len)
        except ValueError:
            self.send_json({"error": "Invalid Content-Length"}, status=400)
            return None
        if not (0 <= length <= OAUTH_MAX_BODY_BYTES):
            self.send_json({"error": "Request body too large"}, status=413)
            return None
        return self.rfile.read(length)

    def handle_oauth_authorize_get(self) -> None:
        cfg = self.runtime.oauth_config
        if cfg is None:
            self.send_json({"error": "OAuth not configured"}, status=404)
            return
        params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query, keep_blank_values=True)
        _p = functools.partial(_first_form_value, params)
        client_id = _p("client_id")
        redirect_uri = _p("redirect_uri")
        code_challenge = _p("code_challenge")
        code_challenge_method = _p("code_challenge_method")
        state = _p("state")
        resource = _p("resource")

        if _p("response_type") != "code":
            self._send_html("<h2>Error</h2><p>response_type must be 'code'</p>", status=400)
            return
        if cfg.registry.get(client_id) is None:
            self._send_html("<h2>Error</h2><p>Unknown client_id</p>", status=400)
            return
        if not cfg.registry.accepts_redirect(client_id, redirect_uri):
            self._send_html("<h2>Error</h2><p>redirect_uri is not registered for this client</p>", status=400)
            return
        if code_challenge_method != "S256" or not valid_pkce_challenge(code_challenge):
            self._send_html("<h2>Error</h2><p>code_challenge_method must be S256 and code_challenge is required</p>", status=400)
            return
        if resource.rstrip("/") != self.oauth_base_url():
            self._send_html("<h2>Error</h2><p>resource must identify this MCP server</p>", status=400)
            return

        self._send_html(self._oauth_login_page(
            client_id=client_id, redirect_uri=redirect_uri, code_challenge=code_challenge,
            code_challenge_method=code_challenge_method, state=state, resource=resource,
        ))

    def handle_oauth_authorize_post(self) -> None:
        cfg = self.runtime.oauth_config
        if cfg is None:
            self.send_json({"error": "OAuth not configured"}, status=404)
            return
        body = self._read_oauth_body()
        if body is None:
            return
        if self.headers.get_content_type().lower() != "application/x-www-form-urlencoded":
            self.send_json({"error": "invalid_request", "error_description": "Content-Type must be application/x-www-form-urlencoded"}, status=400)
            return
        params = urllib.parse.parse_qs(body.decode("utf-8", errors="replace"), keep_blank_values=True)
        _p = functools.partial(_first_form_value, params)
        client_id = _p("client_id")
        redirect_uri = _p("redirect_uri")
        code_challenge = _p("code_challenge")
        code_challenge_method = _p("code_challenge_method")
        state = _p("state")
        resource = _p("resource")
        password = _p("password")

        def fail(error: str, status: int = 400) -> None:
            self._send_html(self._oauth_login_page(
                client_id=client_id, redirect_uri=redirect_uri, code_challenge=code_challenge,
                code_challenge_method=code_challenge_method, state=state, resource=resource,
                error=error,
            ), status=status)

        if cfg.registry.get(client_id) is None or not cfg.registry.accepts_redirect(client_id, redirect_uri):
            fail("Invalid client or redirect URI")
            return
        if code_challenge_method != "S256" or not valid_pkce_challenge(code_challenge):
            fail("Invalid PKCE parameters")
            return
        if resource.rstrip("/") != self.oauth_base_url():
            fail("Invalid resource")
            return
        if not secrets.compare_digest(password, cfg.password):
            fail("Invalid password", status=401)
            return

        code = secrets.token_urlsafe(32)
        now = time.time()
        with cfg.pending_codes_lock:
            expired = [k for k, v in cfg.pending_codes.items() if v["expires_at"] < now]
            for k in expired:
                del cfg.pending_codes[k]
            while len(cfg.pending_codes) >= MAX_PENDING_CODES:
                cfg.pending_codes.pop(next(iter(cfg.pending_codes)))
            cfg.pending_codes[code] = {
                "code_challenge": code_challenge,
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "state": state,
                "expires_at": now + OAUTH_CODE_TTL_SECONDS,
                "server_url": self.oauth_base_url(),
                "resource": resource.rstrip("/"),
            }

        qs = urllib.parse.urlencode({"code": code, **({"state": state} if state else {})})
        sep = "&" if "?" in redirect_uri else "?"
        location = redirect_uri + sep + qs
        self.send_response(302)
        self.send_header("Location", location)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def handle_oauth_token(self) -> None:
        cfg = self.runtime.oauth_config
        if cfg is None:
            self.send_json({"error": "unsupported_grant_type"}, status=400)
            return

        def _err(error: str, description: str) -> None:
            self.log_message("OAuth token error: %s - %s", error, description)
            self.send_json({"error": error, "error_description": description}, status=400)

        body = self._read_oauth_body()
        if body is None:
            return
        content_type = self.headers.get("Content-Type", "").split(";")[0].strip().lower()
        if content_type != "application/x-www-form-urlencoded":
            _err("invalid_request", "Content-Type must be application/x-www-form-urlencoded")
            return
        params = urllib.parse.parse_qs(body.decode("utf-8", errors="replace"), keep_blank_values=True)
        _p = functools.partial(_first_form_value, params)
        grant_type = _p("grant_type")
        code = _p("code")
        redirect_uri = _p("redirect_uri")
        code_verifier = _p("code_verifier")
        client_id = _p("client_id")
        client_secret = _p("client_secret")
        resource = _p("resource").rstrip("/")
        presented_auth_method = "client_secret_post" if client_secret else "none"

        # Also accept HTTP Basic auth for client credentials.
        auth_header = self.headers.get("Authorization", "")
        if auth_header.startswith("Basic ") and (not client_id or not client_secret):
            try:
                decoded = base64.b64decode(auth_header[6:]).decode("utf-8")
                basic_id, _, basic_secret = decoded.partition(":")
                if not client_id:
                    client_id = urllib.parse.unquote(basic_id)
                if not client_secret:
                    client_secret = urllib.parse.unquote(basic_secret)
                presented_auth_method = "client_secret_basic"
            except Exception:  # noqa: BLE001
                pass

        if grant_type != "authorization_code":
            _err("unsupported_grant_type", "Only authorization_code is supported")
            return
        if cfg.registry.get(client_id) is None:
            _err("invalid_client", "Unknown client_id")
            return
        if not cfg.registry.authenticates(client_id, client_secret, presented_auth_method):
            _err("invalid_client", "Invalid client_secret")
            return
        if not code:
            _err("invalid_grant", "code is required")
            return
        if not code_verifier or not (43 <= len(code_verifier) <= 128) or not re.fullmatch(r"[A-Za-z0-9\-._~]+", code_verifier):
            _err("invalid_grant", "Invalid code_verifier")
            return

        with cfg.pending_codes_lock:
            code_data = cfg.pending_codes.pop(code, None)

        if code_data is None:
            _err("invalid_grant", "Unknown or already-used authorization code")
            return
        if time.time() > code_data["expires_at"]:
            _err("invalid_grant", "Authorization code expired")
            return
        if not secrets.compare_digest(code_data["client_id"], client_id):
            _err("invalid_grant", "client_id mismatch")
            return
        if not secrets.compare_digest(code_data["redirect_uri"], redirect_uri):
            _err("invalid_grant", "redirect_uri mismatch")
            return
        if not resource or not secrets.compare_digest(str(code_data.get("resource") or ""), resource):
            _err("invalid_target", "resource mismatch")
            return
        if not verify_pkce(code_verifier, code_data["code_challenge"]):
            _err("invalid_grant", "PKCE verification failed")
            return

        server_url = resource
        access_token = create_access_token(cfg, server_url, client_id=client_id)
        self.send_json({"access_token": access_token, "token_type": "Bearer", "expires_in": cfg.token_ttl})

    def handle_oauth_register(self) -> None:
        cfg = self.runtime.oauth_config
        if cfg is None:
            self.send_json({"error": "OAuth not configured"}, status=404)
            return
        body = self._read_oauth_body()
        if body is None:
            return
        if self.headers.get_content_type().lower() != "application/json":
            self.send_json({"error": "invalid_client_metadata", "error_description": "Content-Type must be application/json"}, status=400)
            return
        try:
            metadata = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self.send_json({"error": "invalid_client_metadata", "error_description": "Body must be valid JSON"}, status=400)
            return
        if not isinstance(metadata, dict):
            self.send_json({"error": "invalid_client_metadata", "error_description": "Metadata must be an object"}, status=400)
            return
        try:
            registered = cfg.registry.register(metadata)
        except ValueError as exc:
            self.send_json({"error": "invalid_client_metadata", "error_description": str(exc)}, status=400)
            return
        self.send_json(registered, status=201)

    def send_cors_headers(self) -> None:
        origin = self.headers.get("Origin")
        if origin and is_allowed_origin(origin):
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Methods", "GET, HEAD, POST, DELETE, OPTIONS")
            self.send_header(
                "Access-Control-Allow-Headers",
                "Accept, Authorization, Content-Type, MCP-Protocol-Version, Mcp-Method, Mcp-Name, Mcp-Session-Id",
            )

    def send_json(
        self,
        payload: Any,
        *,
        status: int = 200,
        extra_headers: dict[str, str] | None = None,
        head_only: bool = False,
    ) -> None:
        body = json_response_payload(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        if getattr(self, "_send_session_header", False):
            self.send_header("Mcp-Session-Id", self.runtime.http_session_id)
        self.send_cors_headers()
        for name, value in (extra_headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        if not head_only:
            self.wfile.write(body)


class RuntimeHTTPServer(http.server.ThreadingHTTPServer):
    daemon_threads = True

    def __init__(
        self,
        address: tuple[str, int],
        handler: type[MCPHandler],
        control_runtime: Runtime,
        runtime_factory: Any,
    ) -> None:
        super().__init__(address, handler)
        self.control_runtime = control_runtime
        self.sessions = HTTPSessionManager(control_runtime)

    def server_close(self) -> None:
        self.sessions.close()
        self.control_runtime.close()
        super().server_close()


def build_runtime(
    args: argparse.Namespace,
    runtime_policy: RuntimePolicy,
    *,
    auth_token: str | None = None,
    oauth_config: OAuthConfig | None = None,
    emit_warning: bool = True,
    project_context: ProjectContext | None = None,
    transport: str = "stdio",
) -> Runtime:
    workspace = Path(args.workspace or os.environ.get(f"{ENV_PREFIX}_WORKSPACE") or os.getcwd())
    runtime = Runtime(
        workspace,
        enable_view_image=args.enable_view_image,
        permission_mode=runtime_policy.permission_mode,
        shell_env_policy=runtime_policy.shell_env_policy,
        allow_network=runtime_policy.allow_network,
        auth_token=auth_token,
        oauth_config=oauth_config,
        project_context=project_context,
        fake_readonly_annotations=runtime_policy.fake_readonly_annotations,
        transport=transport,
    )
    if emit_warning and runtime.capabilities.skip_all_permissions:
        print(
            "WARNING: permission_mode=dangerous disables MCP safety gates. Use only inside an isolated container or VM.",
            file=sys.stderr,
        )
    if emit_warning and runtime.fake_readonly_annotations:
        print(
            "WARNING: tools/list reports every tool as read-only and non-destructive. "
            "apply_patch and exec_command still mutate the workspace and still run commands. "
            "server_info and the server card keep reporting the real annotations.",
            file=sys.stderr,
        )
    return runtime


AUTH_MODE_CHOICES = ("bearer", "noauth", "oauth")


def run_http(args: argparse.Namespace) -> int:
    auth_mode = (os.environ.get(f"{ENV_PREFIX}_AUTH_MODE") or "").strip().lower()
    if auth_mode and auth_mode not in AUTH_MODE_CHOICES:
        supported = ", ".join(AUTH_MODE_CHOICES)
        print(f"ERROR: {ENV_PREFIX}_AUTH_MODE must be one of: {supported}.", file=sys.stderr)
        return 2
    auth_token = args.auth_token or os.environ.get(f"{ENV_PREFIX}_AUTH_TOKEN") or None
    try:
        runtime_policy = runtime_policy_from_args(args)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    oauth_config: OAuthConfig | None = None
    oauth_mode = (
        getattr(args, "oauth_mode", False)
        or truthy_env(os.environ.get(f"{ENV_PREFIX}_OAUTH_MODE"))
        or auth_mode == "oauth"
    )
    if oauth_mode:
        client_id = os.environ.get(f"{ENV_PREFIX}_OAUTH_CLIENT_ID") or None
        client_secret = os.environ.get(f"{ENV_PREFIX}_OAUTH_CLIENT_SECRET") or None
        env_password = os.environ.get(f"{ENV_PREFIX}_OAUTH_PASSWORD")
        password = env_password or secrets.token_urlsafe(32)
        server_url = (os.environ.get(f"{ENV_PREFIX}_SERVER_URL") or "").rstrip("/") or None
        if not env_password:
            print(f"OAuth authorize password: {password}", file=sys.stderr)
        raw_secret = os.environ.get(f"{ENV_PREFIX}_OAUTH_TOKEN_SECRET") or ""
        if raw_secret:
            try:
                token_secret = bytes.fromhex(raw_secret)
            except ValueError:
                print(
                    f"ERROR: {ENV_PREFIX}_OAUTH_TOKEN_SECRET must be hex-encoded bytes.",
                    file=sys.stderr,
                )
                return 2
            if len(token_secret) < 32:
                print(
                    f"ERROR: {ENV_PREFIX}_OAUTH_TOKEN_SECRET must contain at least 32 bytes.",
                    file=sys.stderr,
                )
                return 2
        else:
            token_secret = secrets.token_bytes(32)
        try:
            token_ttl = int(os.environ.get(f"{ENV_PREFIX}_OAUTH_TOKEN_TTL") or OAUTH_TOKEN_TTL_SECONDS)
        except ValueError:
            print(f"ERROR: {ENV_PREFIX}_OAUTH_TOKEN_TTL must be an integer.", file=sys.stderr)
            return 2
        if not 60 <= token_ttl <= 604_800:
            print(f"ERROR: {ENV_PREFIX}_OAUTH_TOKEN_TTL must be between 60 and 604800 seconds.", file=sys.stderr)
            return 2
        oauth_config = OAuthConfig(
            password=password,
            server_url=server_url,
            token_secret=token_secret,
            token_ttl=token_ttl,
        )
        if client_id:
            raw_redirects = os.environ.get(f"{ENV_PREFIX}_OAUTH_REDIRECT_URIS") or "http://127.0.0.1/callback"
            redirect_uris = tuple(item.strip() for item in raw_redirects.split(",") if item.strip())
            try:
                oauth_config.registry.add_preregistered(
                    client_id,
                    redirect_uris,
                    client_secret=client_secret,
                )
            except ValueError as exc:
                print(f"ERROR: invalid OAuth redirect URI configuration: {exc}", file=sys.stderr)
                return 2
        if auth_token:
            print(
                "Auth: dual credentials enabled — both static bearer token and OAuth 2.1 access tokens will be accepted.",
                file=sys.stderr,
            )

    if (
        not auth_token
        and not oauth_config
        and not is_loopback_bind_host(str(args.host))
        and auth_mode != "noauth"
        and truthy_env(os.environ.get(f"{ENV_PREFIX}_GENERATE_AUTH_TOKEN"))
    ):
        auth_token = secrets.token_urlsafe(32)
        print(f"Generated {ENV_PREFIX}_AUTH_TOKEN for non-loopback binding.", file=sys.stderr)
        print(f"Bearer token: {auth_token}", file=sys.stderr)

    if not auth_token and not oauth_config and not is_loopback_bind_host(str(args.host)):
        print(
            "ERROR: non-loopback HTTP binding requires --auth-token, CODING_TOOLS_MCP_AUTH_TOKEN, or --oauth-mode.",
            file=sys.stderr,
        )
        return 2

    # A tunnel forwards to a loopback bind, so the bind host cannot tell a private
    # sandbox apart from a publicly reachable one. Gate on authentication instead:
    # over HTTP, only callers the operator admitted may be told a false catalog.
    if runtime_policy.fake_readonly_annotations and not auth_token and not oauth_config:
        print(
            "ERROR: --dangerously-fake-readonly-annotations over HTTP requires --auth-token, "
            f"{ENV_PREFIX}_AUTH_TOKEN, or --oauth-mode. "
            "Use stdio for an unauthenticated local sandbox.",
            file=sys.stderr,
        )
        return 2

    runtime = build_runtime(args, runtime_policy, auth_token=auth_token, oauth_config=oauth_config, transport="http")
    runtime.preheat_workspace_async()

    def runtime_factory() -> Runtime:
        return build_runtime(
            args,
            runtime_policy,
            auth_token=auth_token,
            oauth_config=oauth_config,
            emit_warning=False,
            project_context=runtime.project_context,
            transport="http",
        )

    server = RuntimeHTTPServer((args.host, args.port), MCPHandler, runtime, runtime_factory)
    if oauth_config:
        url_label = oauth_config.server_url or "dynamic request URL"
        suffix = " + bearer" if runtime.auth_token else ""
        auth_label = f"oauth2{suffix} enabled (server_url={url_label})"
    elif runtime.auth_token:
        auth_label = "bearer auth enabled"
    else:
        auth_label = "no auth configured"
    base_url = _http_base_for_bind_host(str(args.host), args.port)
    print(f"{SERVER_NAME} listening on {base_url}/mcp ({auth_label})", file=sys.stderr)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 130
    finally:
        server.server_close()
    return 0


def run_stdio(args: argparse.Namespace) -> int:
    try:
        runtime_policy = runtime_policy_from_args(args)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    runtime = build_runtime(args, runtime_policy)
    return serve_stdio(runtime)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Serve workspace-confined coding tools over MCP.")
    parser.add_argument("--workspace", help="workspace root; defaults to CODING_TOOLS_MCP_WORKSPACE or cwd")
    parser.add_argument(
        "--host",
        default=os.environ.get(f"{ENV_PREFIX}_HOST") or "127.0.0.1",
        help=f"bind host; defaults to {ENV_PREFIX}_HOST or 127.0.0.1",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=env_int(f"{ENV_PREFIX}_PORT", 8000),
        help=f"bind port; defaults to {ENV_PREFIX}_PORT or 8000",
    )
    parser.add_argument("--stdio", action="store_true", help="serve newline-delimited JSON-RPC over stdio")
    parser.add_argument(
        "--auth-token",
        default=None,
        help=f"require Authorization: Bearer <token> on /mcp; defaults to {ENV_PREFIX}_AUTH_TOKEN",
    )
    parser.add_argument(
        "--oauth-mode",
        action="store_true",
        default=False,
        help=(
            "enable OAuth 2.1 Authorization Code + PKCE; "
            f"{ENV_PREFIX}_SERVER_URL is optional; when unset OAuth metadata uses the request host; "
            "authorize password is generated when unset; RFC 7591 dynamic registration is enabled"
        ),
    )
    parser.add_argument(
        "--shell-env-inherit",
        choices=SHELL_ENV_INHERIT_CHOICES,
        default=None,
        help=(
            "baseline environment inheritance for exec_command subprocesses; "
            f"defaults to {ENV_PREFIX}_SHELL_ENV_INHERIT or core"
        ),
    )
    parser.add_argument(
        "--permission-mode",
        choices=PERMISSION_MODE_CHOICES,
        default=None,
        help=(
            "exec_command permission mode: safe denies network/shell-expansion/inline-script gates; "
            "trusted allows local development network, shell expansion, and inline scripts; "
            "dangerous disables permission gates"
        ),
    )
    parser.add_argument(
        "--allow-network",
        action="store_true",
        help=(
            "compatibility alias: allow network-looking exec_command calls without changing other gates; "
            f"can also be enabled with {ENV_PREFIX}_ALLOW_NETWORK=1"
        ),
    )
    parser.add_argument(
        "--enable-view-image",
        action="store_true",
        default=os.environ.get("CODING_TOOLS_MCP_ENABLE_VIEW_IMAGE", "1") != "0",
        help="enable the P1 view_image tool",
    )
    parser.add_argument(
        "--dangerously-skip-all-permissions",
        action="store_true",
        help=(
            "compatibility alias for --permission-mode dangerous; workspace path boundaries for direct file tools still apply"
        ),
    )
    parser.add_argument(
        "--dangerously-fake-readonly-annotations",
        action="store_true",
        help=(
            "report every tool in tools/list as read-only and non-destructive for clients that gate on "
            "annotations; mutation and execution still happen; requires --permission-mode dangerous, and "
            "requires auth over HTTP; server_info and the server card keep reporting the real annotations; "
            f"can also be enabled with {ENV_PREFIX}_DANGEROUSLY_FAKE_READONLY_ANNOTATIONS=1"
        ),
    )
    return parser


def install_sigterm_handler() -> None:
    """Exit cleanly on SIGTERM (128 + 15), matching KeyboardInterrupt."""
    if threading.current_thread() is not threading.main_thread():
        return

    def _terminate(signum: int, _frame: object) -> None:
        raise SystemExit(128 + signum)

    try:
        signal.signal(signal.SIGTERM, _terminate)
    except (ValueError, OSError, AttributeError):
        pass


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    install_sigterm_handler()
    return run_stdio(args) if args.stdio else run_http(args)


if __name__ == "__main__":
    raise SystemExit(main())
