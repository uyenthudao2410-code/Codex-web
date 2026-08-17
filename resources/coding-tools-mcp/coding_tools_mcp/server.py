from __future__ import annotations

import argparse  # noqa: F401  # composition-root namespace
import base64  # noqa: F401  # composition-root namespace
import copy  # noqa: F401  # composition-root namespace
import ctypes  # noqa: F401  # composition-root namespace
import hashlib  # noqa: F401  # composition-root namespace
import html  # noqa: F401  # composition-root namespace
import difflib  # noqa: F401  # composition-root namespace
import fnmatch  # noqa: F401  # composition-root namespace
import functools  # noqa: F401  # composition-root namespace
import hmac  # noqa: F401  # composition-root namespace
import http.server  # noqa: F401  # composition-root namespace
import json  # noqa: F401  # composition-root namespace
import marshal  # noqa: F401  # composition-root namespace
import math  # noqa: F401  # composition-root namespace
import mimetypes  # noqa: F401  # composition-root namespace
import os  # noqa: F401  # composition-root namespace
import posixpath  # noqa: F401  # composition-root namespace
import re  # noqa: F401  # composition-root namespace
import secrets  # noqa: F401  # composition-root namespace
import shlex  # noqa: F401  # composition-root namespace
import shutil  # noqa: F401  # composition-root namespace
import signal  # noqa: F401  # composition-root namespace
import stat  # noqa: F401  # composition-root namespace
import subprocess  # noqa: F401  # composition-root namespace
import sys  # noqa: F401  # composition-root namespace
import tempfile  # noqa: F401  # composition-root namespace
import threading  # noqa: F401  # composition-root namespace
import time  # noqa: F401  # composition-root namespace
import urllib.parse  # noqa: F401  # composition-root namespace
import zipfile  # noqa: F401  # composition-root namespace
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from . import __version__  # noqa: F401  # composition-root namespace
from .budget_control import BudgetDeadline, RetryPolicy  # noqa: F401  # composition-root namespace
from .envutils import ENV_PREFIX, truthy_env  # noqa: F401  # composition-root namespace
from .errors import JsonRpcError, ToolFailure, normalize_exception_group  # noqa: F401  # composition-root namespace
from .execution_resources import ExecutionResourceGovernor  # noqa: F401  # composition-root namespace
from .landlock_exec import libc_syscall  # noqa: F401  # composition-root namespace
from .oauth import (  # noqa: F401  # composition-root namespace
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
from .patching import (  # noqa: F401  # composition-root namespace
    AtomicPatchCommitter,
    FileBaseline,
    StagedFile,
    apply_update_hunks,
    parse_patch,
    read_text_preserve_newlines,
)
from .processes import (  # noqa: F401  # composition-root namespace
    HARD_KILL_SIGNAL,
    SESSION_BUFFER_BYTES,
    ExecSession,
    spawn_process,
    start_reader_threads,
    start_session_watchdog,
    terminate_process_group,
)
from .protocol import (  # noqa: F401  # composition-root namespace
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
from .project_context import ProjectContext, load_project_context  # noqa: F401  # composition-root namespace
from .build_verify import verify_build as run_build_verification  # noqa: F401  # composition-root namespace
from .artifact_refs import build_file_artifact_ref  # noqa: F401  # composition-root namespace
from .codex_bridge import CodexAppServerBridge, CodexBridgeError  # noqa: F401  # composition-root namespace
from .code_mode import CodeModeHostBindingProxy  # noqa: F401  # composition-root namespace
from .document_tools import create_docx, create_text_document, convert_document, extract_document  # noqa: F401  # composition-root namespace
from .opencode_provider import ALLOWED_OPENCODE_MODELS, OpenCodeProviderAdapter, OpenCodeProviderError  # noqa: F401  # composition-root namespace
from .provider_routing import recommendation_id, recommend_shadow_route  # noqa: F401  # composition-root namespace
from .semantic_localization import (  # noqa: F401  # composition-root namespace
    run_semantic_localization,
    semantic_localizer_from_env,
    semantic_provider_status,
)
from .task_state import TaskStateStore  # noqa: F401  # composition-root namespace
from .performance_trace import IDEMPOTENCY_POLICY_EPOCH, PerformanceTraceStore, utc_now  # noqa: F401  # composition-root namespace
from .orchestration_control import OrchestrationControl, OrchestrationControlError, RunContext, normalize_failure_class  # noqa: F401  # composition-root namespace
from .orchestration_ledger import OrchestrationLedger, fingerprint_paths  # noqa: F401  # composition-root namespace
from .orchestration_report import OrchestrationReport  # noqa: F401  # composition-root namespace
from .operator_report import OPERATOR_REPORT_STATES, build_operator_completion_report  # noqa: F401  # composition-root namespace
from .proof_ledger import ProofLedger  # noqa: F401  # composition-root namespace
from .telemetry import SessionTelemetry  # noqa: F401  # composition-root namespace
from .textutils import DEFAULT_MAX_LINES, TextTruncation, truncate_text_head  # noqa: F401  # composition-root namespace
from .tool_results import make_tool_result, model_visible_text_bytes  # noqa: F401  # composition-root namespace
from .tool_contract import (  # noqa: F401  # composition-root namespace
    AGENT_EXECUTION_ROUTES,
    SMART_COMPAT_TOOL_NAMES,
    SMART_TOOL_PROFILE,
    TOOL_CONTRACT_RUNTIME,
    TOOL_CONTRACT_SCHEMA_VERSION,
    TOOL_MODE_ALLOWLISTS,
    TOOL_REGISTRY,
    ToolSpec,
    tool_metadata_contract,
)
from .usage_events import usage_event_from_provider_delegation  # noqa: F401  # composition-root namespace
from .provider_traffic import ProviderTrafficGovernor  # noqa: F401  # composition-root namespace

from .transport_stdio import serve_stdio  # noqa: F401  # composition-root namespace
from .file_tools import FileToolsMixin  # noqa: F401  # composition-root namespace
from .fs_utils import ResolvedPath  # noqa: F401  # composition-root namespace
from .exec_tools import ExecToolsMixin  # noqa: F401  # composition-root namespace
from .git_tools import GitToolsMixin  # noqa: F401  # composition-root namespace
from .session_control import SessionControlMixin  # noqa: F401  # composition-root namespace
from .document_tools import DocumentToolsMixin  # noqa: F401  # composition-root namespace
from .task_state import TaskStateToolsMixin  # noqa: F401  # composition-root namespace


from .exec_tools import permission_failure_diagnostics  # noqa: F401  # composition-root namespace
from .processes import hidden_process_popen_kwargs  # noqa: F401  # composition-root namespace
from .mcp_http_handler import HUB_CLIENT_ID_RE, SERVER_NAME, SERVER_TITLE, HUB_CONTROLLER_LEASE_SECONDS, MCPHandler, MCP_ENDPOINT_PATH, RuntimeHTTPServer, is_loopback_bind_host, server_card_payload  # noqa: F401  # compatibility re-export
from .agent_candidate import AGENT_CANDIDATE_PACKET_MAX_CHARS, AGENT_CANDIDATE_SNIPPET_MAX_COUNT, AGENT_EXTERNAL_REVIEW_ENV, AGENT_REVIEW_DEADLINE_MS, AgentCandidateMixin  # noqa: F401  # compatibility re-export
from .context_tools import ContextToolsMixin  # noqa: F401  # composition-root namespace
from .workflow_tools import AgentWorkflowMixin  # noqa: F401  # composition-root namespace
from .coordination import CoordinationMixin  # noqa: F401  # composition-root namespace

# Re-exports from extracted modules (refactor: keep server.py namespace stable)
from .command_parse import DESTRUCTIVE_RE, INLINE_SCRIPT_PERMISSION, NETWORK_RE, SHELL_EXPANSION_RE, command_executables, explicit_command_path_candidates, inline_script_command, is_literal_network_reference_command, shlex_split, strip_heredoc_payloads  # noqa: F401  # compatibility re-export
from .fs_utils import DEFAULT_EXCLUDED_NAMES, cached_which, entry_for_path, file_entry, find_literal, is_relative_to, matches_any_glob, normalize_rel_display, path_batches, search_match_item, sort_value, truncate_bytes, walk_files  # noqa: F401  # compatibility re-export
from .git_utils import parse_branch_line, parse_git_blame_porcelain, redact_for_trace, require_git, validate_git_ref  # noqa: F401  # compatibility re-export
from .image_utils import IMAGE_RESIZE_MAX_DIMENSION, identify_image, resize_image_bytes, should_resize_image  # noqa: F401  # compatibility re-export
from .landlock_exec import SPECIAL_DEVICE_PATHS, guard_allow_roots, landlock_exec_argv, landlock_status_payload, landlock_unavailable_warning, open_landlock_ruleset  # noqa: F401  # compatibility re-export
from .runtime_config import PERMISSION_MODE_CAPABILITIES, PERMISSION_MODE_CHOICES, RuntimePolicy, SHELL_ENV_INHERIT_CHOICES, ShellEnvPolicy, WINDOWS_CORE_ENV_NAMES, env_int, env_pattern_matches, fallback_runtime_dir_for_workspace, is_core_command_env_name, is_filtered_env_var, runtime_dir_for_workspace, runtime_policy_from_args  # noqa: F401  # compatibility re-export
from .tool_schema import DIFF_CONTINUATION_TOKEN_MAX_CHARS, EVALUATION_SCHEMA_VERSION, input_schemas, tool_annotations, tool_definition, validate_arguments  # noqa: F401  # compatibility re-export
from .transport_http import STATELESS_HTTP_2026_ENV, _decode_mcp_name_header, _first_form_value, _first_header_value, _forwarded_header_param, _http_base_for_bind_host, _request_mcp_name, _safe_external_host, stateless_http_2026_enabled  # noqa: F401  # compatibility re-export



PROCESS_INSTANCE_ID = secrets.token_urlsafe(12)
HUB_PROVIDER_TELEMETRY_STATES = frozenset({"ROUTED", "EXECUTING", "PROVING", "ACCEPTING"})
HUB_PROVIDER_TELEMETRY_STATUSES = frozenset({"active", "completed", "failed"})
HOST_CORRELATION_SCHEMA_VERSION = 1
HOST_CORRELATION_PENDING_TTL_MS = 120_000
HOST_CORRELATION_PENDING_RELATIVE = Path('.coding-tools') / 'evaluation' / 'chatweb-host-turn-pending.json'
HOST_CORRELATION_BINDING_RELATIVE = Path('.coding-tools') / 'evaluation' / 'chatweb-host-turn-binding.json'

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
TRACE_MAX_PAYLOAD_BYTES = 16 * 1024
AUTO_IDEMPOTENCY_KEY_PREFIX = "auto-v1:"
BACKGROUND_BUDGET_POLL_SECONDS = 1.0
BACKGROUND_BUDGET_TERMINAL_GRACE_SECONDS = 5.0
STALE_RECONCILIATION_INTERVAL_SECONDS = 30.0
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




# Documented kill_session status enum; guarded by test_schema_drift.





def normalize_provider_telemetry(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("telemetry must be an object")
    allowed = {
        "schema_version", "event_type", "session_id", "message_id", "provider_id", "model_id",
        "status", "started_at_ms", "completed_at_ms", "duration_ms", "finish", "error_name",
        "provider_cost", "input_tokens", "output_tokens", "reasoning_output_tokens",
        "cache_read_tokens", "cache_write_tokens", "provider_dispatch_id", "provider_delegation_id",
    }
    unexpected = sorted(set(value) - allowed)
    if unexpected:
        raise ValueError("unsupported provider telemetry fields: " + ", ".join(unexpected[:5]))
    if value.get("schema_version") != 1 or value.get("event_type") != "message.updated":
        raise ValueError("unsupported provider telemetry schema")

    def text(name: str, limit: int, *, required: bool = False) -> str:
        result = str(value.get(name) or "").strip()
        if required and not result:
            raise ValueError(f"{name} is required")
        if len(result) > limit or any(ord(ch) < 32 for ch in result):
            raise ValueError(f"invalid {name}")
        return result

    def number(name: str, *, integer: bool = False, required: bool = False) -> int | float | None:
        raw = value.get(name)
        if raw is None:
            if required:
                raise ValueError(f"{name} is required")
            return None
        if isinstance(raw, bool) or not isinstance(raw, (int, float)) or not math.isfinite(float(raw)) or raw < 0:
            raise ValueError(f"invalid {name}")
        if integer and int(raw) != raw:
            raise ValueError(f"invalid {name}")
        return int(raw) if integer else raw

    status = text("status", 32, required=True).lower()
    if status not in HUB_PROVIDER_TELEMETRY_STATUSES:
        raise ValueError("invalid provider telemetry status")
    result: dict[str, Any] = {
        "schema_version": 1,
        "event_type": "message.updated",
        "session_id": text("session_id", 256, required=True),
        "message_id": text("message_id", 256, required=True),
        "provider_id": text("provider_id", 160, required=True),
        "model_id": text("model_id", 200, required=True),
        "status": status,
        "started_at_ms": number("started_at_ms", required=True),
        "provider_cost": number("provider_cost", required=True),
        "input_tokens": number("input_tokens", integer=True, required=True),
        "output_tokens": number("output_tokens", integer=True, required=True),
        "reasoning_output_tokens": number("reasoning_output_tokens", integer=True, required=True),
        "cache_read_tokens": number("cache_read_tokens", integer=True, required=True),
        "cache_write_tokens": number("cache_write_tokens", integer=True, required=True),
    }
    for name in ("completed_at_ms", "duration_ms"):
        measured = number(name)
        if measured is not None:
            result[name] = measured
    for name, limit in (("provider_dispatch_id", 256), ("provider_delegation_id", 256), ("finish", 100), ("error_name", 120)):
        measured = text(name, limit)
        if measured:
            result[name] = measured
    return result


_FAST_TOOL_CACHE: dict[str, tuple[float, int, dict[str, Any]]] = {}
_FAST_TOOL_CACHE_LOCK = threading.Lock()
_WORKSPACE_CACHE_GENERATION: dict[str, int] = {}
_WORKSPACE_PREHEAT_STARTED: set[str] = set()















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


class Runtime(
    FileToolsMixin, ExecToolsMixin, GitToolsMixin, SessionControlMixin, DocumentToolsMixin, TaskStateToolsMixin,
    AgentCandidateMixin, ContextToolsMixin, AgentWorkflowMixin, CoordinationMixin
):
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
        semantic_localizer: Any | None = None,
    ) -> None:
        self.authorized_roots = configured_authorized_roots()
        self.workspace = Workspace(workspace, self.authorized_roots)
        self.tool_mode = os.environ.get(f"{ENV_PREFIX}_TOOL_MODE", "coding").strip().lower()
        if self.tool_mode not in TOOL_MODE_ALLOWLISTS:
            self.tool_mode = "coding"
        self.enable_view_image = enable_view_image
        self._exposed_tool_names = TOOL_CONTRACT_RUNTIME.exposed_names(
            self.tool_mode,
            gate_resolver=lambda attribute: bool(getattr(self, attribute)),
        )
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
        contract_bytes = json.dumps(
            self._tools_list_payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        agent_workflow_tool = next(
            (item for item in self._tools_list_payload["tools"] if item.get("name") == "agent_workflow"),
            {},
        )
        evaluation_schema = (
            ((agent_workflow_tool.get("inputSchema") or {}).get("properties") or {}).get("evaluation")
            if isinstance(agent_workflow_tool, dict)
            else None
        )
        evaluation_schema_bytes = json.dumps(
            evaluation_schema or {},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        self.tool_contract = {
            "schema_version": TOOL_CONTRACT_SCHEMA_VERSION,
            "profile": SMART_TOOL_PROFILE if self.tool_mode == "smart" else self.tool_mode,
            "sha256": hashlib.sha256(contract_bytes).hexdigest(),
            "tool_count": len(self._exposed_tool_names),
            "evaluation": {
                "supported": isinstance(evaluation_schema, dict),
                "schema_version": EVALUATION_SCHEMA_VERSION,
                "sha256": hashlib.sha256(evaluation_schema_bytes).hexdigest(),
            },
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
        self.supervisor_request_lock = threading.Lock()
        self.activation_lock = threading.RLock()
        self.activation_fence: dict[str, Any] | None = None
        self.active_tool_calls = 0
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
        self._semantic_localizer_injected = semantic_localizer is not None
        self.semantic_localizer = (
            semantic_localizer
            if semantic_localizer is not None
            else semantic_localizer_from_env(self.workspace.root)
        )
        # Internal prerequisite for a future isolated Code Mode worker. This
        # proxy is intentionally not model-facing and is not itself an
        # isolation boundary; Code Mode remains disabled until such a worker
        # exists.
        self.code_mode_bindings = CodeModeHostBindingProxy(self)
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
        self.execution_resource_governor = ExecutionResourceGovernor(
            self.workspace.root,
            self.orchestration_ledger,
            process_instance_id=self.process_instance_id,
            runtime_instance_id=self.server_instance_id,
        )
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
        self.stale_run_seconds = stale_run_seconds
        self._last_stale_reconciliation_monotonic = 0.0
        self.reconciled_stale_orchestration_runs = self.orchestration_ledger.reconcile_stale_runs(
            stale_after_seconds=self.stale_run_seconds,
            close_stale_active=False,
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
        self.orchestration_control = self._new_orchestration_control()
        self.reconciled_task_orchestration = self._reconcile_task_orchestration_projection()
        self.proof_ledger = ProofLedger(self.workspace.root, self.orchestration_ledger)
        self.orchestration_report = OrchestrationReport(self.workspace.root, self.orchestration_ledger)
        self._opencode_provider = OpenCodeProviderAdapter(
            lambda: self.workspace.root,
            on_terminal=self._on_opencode_provider_terminal,
            resource_governor=self.execution_resource_governor,
        )
        self.provider_traffic = ProviderTrafficGovernor.from_env()
        self.workspace_switch_lock = threading.RLock()
        self.workspace_generation = 1
        self._codex_bridge = CodexAppServerBridge(
            lambda: self.workspace.root,
            resource_governor=self.execution_resource_governor,
        )
        self._tool_handlers = {name: getattr(self, name) for name in TOOL_REGISTRY}

    def _set_runtime_dir(self, runtime_dir: Path) -> None:
        self.runtime_dir = runtime_dir
        self.home_dir = self.runtime_dir / "home"
        self.tmp_dir = self.runtime_dir / "tmp"
        self.cache_dir = self.runtime_dir / "cache"

    def _new_orchestration_control(self) -> OrchestrationControl:
        return OrchestrationControl(
            self.workspace.root,
            self.orchestration_ledger,
            on_wave_terminal=lambda ctx, state: self.execution_resource_governor.teardown_wave(
                ctx.run_id,
                ctx.wave_id,
                reason=f"orchestration_state:{str(state).lower()}",
            ),
            assert_wave_quiescent=self.execution_resource_governor.assert_wave_quiescent,
        )

    def _reconcile_task_orchestration_projection(self) -> bool:
        state = self.task_state.get()
        if not str(state.get("task_id") or "").strip() and not str(state.get("objective") or "").strip():
            return False
        projection = state.get("orchestration") if isinstance(state.get("orchestration"), dict) else {}
        run_id = str(projection.get("run_id") or "").strip()
        if not run_id:
            active = self.orchestration_ledger.current_active_run()
            run_id = str(active.get("run_id") or "") if active else ""
        if not run_id:
            return False
        run = self.orchestration_ledger.get_run(run_id)
        if not isinstance(run, dict):
            return False
        run_status = str(run.get("status") or "").lower()
        target_state = {
            "accepted": "CHECKPOINTED",
            "blocked": "BLOCKED",
            "aborted": "ABORTED",
            "stale": "ABORTED",
        }.get(run_status)
        ctx = self.orchestration_control.snapshot(run_id)
        if ctx is None:
            return False
        waves = self.orchestration_ledger.list_waves(run_id)
        repaired = dict(projection)
        repaired.update(ctx.projection())
        repaired["run_id"] = run_id
        if waves:
            repaired["wave_id"] = str(waves[-1].get("wave_id") or repaired.get("wave_id") or "")
        if target_state:
            repaired["orchestration_state"] = target_state
            repaired["write_lease_id"] = ""
            repaired["write_owner"] = ""

        canonical_state = str(repaired.get("orchestration_state") or "").upper()
        desired_task: dict[str, Any] = {"orchestration": repaired}
        if canonical_state == "ACCEPTING":
            desired_task.update({
                "status": "waiting",
                "current_step": "Awaiting acceptance",
                "next_step": (
                    "Present orchestration.completion_report to the operator, then inspect the durable proof and "
                    "call task_control action=accept or reject; "
                    "do not retry completed tool calls."
                ),
                "failure": None,
            })
        elif canonical_state == "CHECKPOINTED":
            desired_task.update({
                "status": "completed",
                "current_step": "Completed - operator report required",
                "next_step": "Present orchestration.completion_report to the operator before starting another material wave.",
                "failure": None,
            })
        elif canonical_state == "REPLAN":
            desired_task.update({
                "status": "waiting",
                "current_step": "Replan required - operator report required",
                "next_step": "Present orchestration.completion_report to the operator, then replan from the durable failure; do not retry an unchanged wave.",
                "failure": state.get("failure"),
            })
        elif canonical_state == "BLOCKED":
            desired_task.update({
                "status": "failed",
                "current_step": "Blocked - operator report required",
                "next_step": "Present orchestration.completion_report to the operator, then resolve the durable blocker before another execution wave.",
                "failure": state.get("failure"),
            })
        elif canonical_state == "ABORTED":
            desired_task.update({
                "status": "stopped",
                "current_step": "Aborted - operator report required",
                "next_step": "Present orchestration.completion_report to the operator before any resume; use current source state and do not reuse stale proof.",
                "failure": state.get("failure"),
            })
        current_projection = state.get("orchestration") if isinstance(state.get("orchestration"), dict) else {}
        projection_changed = any(current_projection.get(key) != repaired.get(key) for key in repaired)
        task_changed = any(
            state.get(key) != desired_task[key]
            for key in ("status", "current_step", "next_step", "failure")
            if key in desired_task
        )
        if not projection_changed and not task_changed:
            return False
        self.task_state.update(desired_task, event="orchestration_projection_reconciled")
        return True

    def close(self) -> None:
        self._opencode_provider.close()
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
            if session.managed_job_id and not session.resource_terminal_recorded:
                self.execution_resource_governor.complete(
                    session.managed_job_id,
                    lifecycle_state="runtime_closed",
                    exit_code=session.process.poll(),
                )
                session.resource_terminal_recorded = True
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
            provider_dispatches = self._opencode_provider.active_count()
            if provider_dispatches:
                raise ToolFailure(
                    "WORKSPACE_BUSY",
                    "Cannot switch workspace while an OpenCode provider dispatch is running.",
                    category="runtime",
                    retryable=True,
                    details={"active_provider_dispatches": provider_dispatches},
                )
            old_runtime_dir = self.runtime_dir
            self._opencode_provider.close()
            self._codex_bridge.close()
            self._invalidate_fast_cache()
            self._clear_context_bundle_cache()
            self.workspace = Workspace(target, self.authorized_roots)
            self.default_cwd = self.workspace.root
            self._set_runtime_dir(runtime_dir_for_workspace(self.workspace.root, self.server_instance_id))
            self.fallback_runtime_dir = fallback_runtime_dir_for_workspace(self.workspace.root, self.server_instance_id)
            self.project_context = load_project_context(self.workspace.root)
            if not self._semantic_localizer_injected:
                self.semantic_localizer = semantic_localizer_from_env(self.workspace.root)
            self.task_state = TaskStateStore(self.workspace.root)
            self.performance_trace = PerformanceTraceStore(self.workspace.root)
            self.orchestration_ledger = OrchestrationLedger(self.workspace.root)
            self.execution_resource_governor = ExecutionResourceGovernor(
                self.workspace.root,
                self.orchestration_ledger,
                process_instance_id=self.process_instance_id,
                runtime_instance_id=self.server_instance_id,
            )
            self.orphaned_background_operations = self.orchestration_ledger.mark_orphaned_background_operations(
                current_server_instance_id=self.process_instance_id
            )
            self.orphaned_idempotency_records = self.orchestration_ledger.mark_orphaned_idempotency(
                current_process_instance_id=self.process_instance_id
            )
            self.reconciled_stale_orchestration_runs = self.orchestration_ledger.reconcile_stale_runs(
                stale_after_seconds=self.stale_run_seconds,
                close_stale_active=False,
            )
            self._last_stale_reconciliation_monotonic = 0.0
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
            self.orchestration_control = self._new_orchestration_control()
            self.reconciled_task_orchestration = self._reconcile_task_orchestration_projection()
            self.proof_ledger = ProofLedger(self.workspace.root, self.orchestration_ledger)
            self.orchestration_report = OrchestrationReport(self.workspace.root, self.orchestration_ledger)
            self._opencode_provider = OpenCodeProviderAdapter(
                lambda: self.workspace.root,
                on_terminal=self._on_opencode_provider_terminal,
                resource_governor=self.execution_resource_governor,
            )
            self.provider_traffic = ProviderTrafficGovernor.from_env()
            self._codex_bridge = CodexAppServerBridge(
                lambda: self.workspace.root,
                resource_governor=self.execution_resource_governor,
            )
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

    def _current_hub_client(self) -> dict[str, Any] | None:
        value = getattr(self.request_context, "hub_client", None)
        return value if isinstance(value, dict) and value.get("client_id") else None

    def _maybe_reconcile_stale_orchestration(self, *, force: bool = False) -> list[str]:
        """Run bounded stale cleanup without making every UI poll scan the ledger."""

        now = time.monotonic()
        if not force and now - self._last_stale_reconciliation_monotonic < STALE_RECONCILIATION_INTERVAL_SECONDS:
            return []
        self._last_stale_reconciliation_monotonic = now
        return self.orchestration_ledger.reconcile_stale_runs(
            stale_after_seconds=self.stale_run_seconds,
            close_stale_active=True,
        )

    def _projected_hub_run_id(self) -> str:
        # The task-state projection may lag after a reconnect.  Lease ownership
        # must be selected from the durable ledger instead of a stale stream.
        state = self.task_state.get()
        projection = state.get("orchestration") if isinstance(state.get("orchestration"), dict) else {}
        run_id = str(projection.get("run_id") or "").strip()
        if run_id:
            run = self.orchestration_ledger.get_run(run_id)
            if run and str(run.get("status") or "") == "active":
                return run_id
        active = self.orchestration_ledger.current_active_run()
        return str(active.get("run_id") or "") if active else ""

    def _touch_hub_client(self, identity: dict[str, Any]) -> dict[str, Any]:
        client_id = str(identity.get("client_id") or "").strip()
        client_type = str(identity.get("client_type") or "client").strip()
        role = str(identity.get("role") or "client").strip()
        if not HUB_CLIENT_ID_RE.fullmatch(client_id):
            raise ValueError("invalid Execution Hub client id")
        # Heartbeats are also a safe reconciliation point: persist expired
        # leases and close genuinely abandoned runs while retaining ACCEPTING
        # runs so a new controller can finish the accept/reject decision.
        self._maybe_reconcile_stale_orchestration()
        # Rebuild the compact projection from durable events before claiming a
        # lease.  A reconnect must resume the existing run, never replay the
        # old stream or start a duplicate turn.
        self._reconcile_task_orchestration_projection()
        client = self.orchestration_ledger.upsert_hub_client(
            client_id=client_id,
            client_type=client_type,
            role=role,
            status="online",
            session_instance=str(identity.get("session_instance") or ""),
            runtime_instance_id=self.process_instance_id,
            contract_sha=str(self.tool_contract.get("sha256") or ""),
            capabilities=identity.get("capabilities") if isinstance(identity.get("capabilities"), dict) else {},
        )
        run_id = self._projected_hub_run_id()
        controller = self.orchestration_ledger.get_controller_lease(run_id) if run_id else None
        run = self.orchestration_ledger.get_run(run_id) if run_id else None
        if run and run.get("status") == "active":
            if controller and controller.get("status") == "active" and controller.get("owner_client_id") == client_id:
                renewed = self.orchestration_ledger.acquire_controller_lease(
                    run_id=run_id,
                    owner_client_id=client_id,
                    lease_id=str(controller.get("lease_id") or f"client:{client_id}"),
                    ttl_seconds=HUB_CONTROLLER_LEASE_SECONDS,
                )
                controller = renewed if renewed.get("acquired") else controller
            elif (not controller or controller.get("status") != "active") and client_type == "chatweb":
                claimed = self.orchestration_ledger.acquire_controller_lease(
                    run_id=run_id,
                    owner_client_id=client_id,
                    lease_id=f"client:{client_id}",
                    ttl_seconds=HUB_CONTROLLER_LEASE_SECONDS,
                )
                controller = claimed if claimed.get("acquired") else self.orchestration_ledger.get_controller_lease(run_id)
        return {"client": client, "controller": controller, "run_id": run_id}

    def ingest_provider_telemetry(self, identity: dict[str, Any], value: Any) -> dict[str, Any]:
        client_id = str(identity.get("client_id") or "").strip()
        client_type = str(identity.get("client_type") or "").strip()
        if (client_id, client_type) != ("opencode", "opencode"):
            raise ToolFailure("PROVIDER_TELEMETRY_CLIENT_DENIED", "Only the allowlisted OpenCode worker may publish provider telemetry.", category="security", retryable=False)
        telemetry = normalize_provider_telemetry(value)
        self._touch_hub_client(identity)
        state = self.task_state.get()
        projection = state.get("orchestration") if isinstance(state.get("orchestration"), dict) else {}
        run_id = str(projection.get("run_id") or "").strip()
        wave_id = str(projection.get("wave_id") or "").strip()
        ctx = self.orchestration_control.snapshot(run_id) if run_id else None
        run = self.orchestration_ledger.get_run(run_id) if run_id else None
        if not ctx or not run or run.get("status") != "active" or not wave_id or ctx.wave_id != wave_id or ctx.state not in HUB_PROVIDER_TELEMETRY_STATES:
            raise ToolFailure(
                "PROVIDER_TELEMETRY_CONTEXT_UNAVAILABLE",
                "Provider telemetry is not bound to a current active task-projected orchestration wave.",
                category="runtime",
                retryable=True,
                details={"run_id": run_id, "wave_id": wave_id, "state": ctx.state if ctx else ""},
            )
        provider_id = telemetry["provider_id"]
        model_id = telemetry["model_id"]
        model = model_id if "/" in model_id else f"{provider_id}/{model_id}"
        dispatch: dict[str, Any] | None = None
        provider_dispatch_id = str(telemetry.get("provider_dispatch_id") or "").strip()
        provider_delegation_id = str(telemetry.get("provider_delegation_id") or "").strip()
        if bool(provider_dispatch_id) != bool(provider_delegation_id):
            raise ToolFailure("PROVIDER_TELEMETRY_CORRELATION_INVALID", "Provider telemetry correlation identifiers must be supplied together.", category="validation", retryable=False)
        if provider_dispatch_id:
            try:
                dispatch = self._opencode_provider.observe(provider_dispatch_id)
            except OpenCodeProviderError:
                existing = self.orchestration_ledger.get_delegation(provider_delegation_id)
                metadata = (existing or {}).get("metadata") or {}
                if not existing or str(metadata.get("provider_dispatch_id") or "") != provider_dispatch_id:
                    raise ToolFailure("PROVIDER_TELEMETRY_CORRELATION_UNKNOWN", "Provider telemetry does not map to a known provider dispatch.", category="runtime", retryable=True)
                dispatch = {
                    "dispatch_id": provider_dispatch_id,
                    "delegation_id": provider_delegation_id,
                    "run_id": run_id,
                    "wave_id": str(existing.get("wave_id") or ""),
                    "model": str(existing.get("model") or ""),
                }
            if (
                str(dispatch.get("delegation_id") or "") != provider_delegation_id
                or str(dispatch.get("run_id") or "") != run_id
                or str(dispatch.get("wave_id") or "") != wave_id
                or str(dispatch.get("model") or "") != model
            ):
                raise ToolFailure("PROVIDER_TELEMETRY_CORRELATION_MISMATCH", "Provider telemetry correlation does not match the active run, wave, delegation, or model.", category="security", retryable=False)
        else:
            dispatch = self._opencode_provider.find_by_session(run_id=run_id, wave_id=wave_id, model=model, session_id=telemetry["session_id"])
            if dispatch is None and str(ctx.route_resolved or "").strip().lower() not in {"opencode", model.lower()}:
                raise ToolFailure(
                    "PROVIDER_TELEMETRY_ATTRIBUTION_UNAVAILABLE",
                    "Uncorrelated OpenCode telemetry may only attach to a wave explicitly routed to OpenCode.",
                    category="runtime",
                    retryable=True,
                    details={"run_id": run_id, "wave_id": wave_id, "route_resolved": ctx.route_resolved},
                )
        delegation_id = str((dispatch or {}).get("delegation_id") or "") or "opencode-" + hashlib.sha256(f"{run_id}\0{telemetry['session_id']}\0{telemetry['message_id']}".encode("utf-8")).hexdigest()[:40]
        economics = {
            "input_tokens": telemetry["input_tokens"],
            "cached_input_tokens": telemetry["cache_read_tokens"],
            "output_tokens": telemetry["output_tokens"],
            "reasoning_output_tokens": telemetry["reasoning_output_tokens"],
            "cache_read_tokens": telemetry["cache_read_tokens"],
            "cache_write_tokens": telemetry["cache_write_tokens"],
            "provider_cost": telemetry["provider_cost"],
            "measured": True,
            "source": "opencode",
        }
        message_economics = {
            telemetry["message_id"]: {
                "input_tokens": telemetry["input_tokens"],
                "cached_input_tokens": telemetry["cache_read_tokens"],
                "output_tokens": telemetry["output_tokens"],
                "reasoning_output_tokens": telemetry["reasoning_output_tokens"],
                "cache_read_tokens": telemetry["cache_read_tokens"],
                "cache_write_tokens": telemetry["cache_write_tokens"],
                "provider_cost": telemetry["provider_cost"],
                **({"duration_ms": telemetry["duration_ms"]} if "duration_ms" in telemetry else {}),
            }
        }
        metadata: dict[str, Any] = {
            "source": "opencode:message.updated",
            "provider_id": provider_id,
            "model_id": model_id,
            "session_id": telemetry["session_id"],
            "message_id": telemetry["message_id"],
            "provider_started_at_ms": telemetry["started_at_ms"],
            "provider_cost": telemetry["provider_cost"],
            "economics": economics,
            "message_economics": message_economics,
            "provider_message_status": telemetry["status"],
            "attribution": "correlated_dispatch" if dispatch else "task_projected_opencode_route",
        }
        for key in ("completed_at_ms", "duration_ms", "finish", "error_name"):
            if key in telemetry:
                metadata["provider_completed_at_ms" if key == "completed_at_ms" else key] = telemetry[key]
        if dispatch:
            metadata["provider_dispatch_id"] = str(dispatch.get("dispatch_id") or "")
            metadata["side_effect_class"] = "read_only"
            metadata["read_only_enforced"] = True
        intermediate_tool_calls = bool(dispatch) and telemetry["status"] == "completed" and str(telemetry.get("finish") or "").strip().lower() == "tool-calls"
        delegation_status = "active" if intermediate_tool_calls else telemetry["status"]
        projected = self.orchestration_ledger.upsert_external_delegation(
            delegation_id=delegation_id,
            wave_id=wave_id,
            authority_owner="opencode",
            route_requested="opencode",
            route_resolved=model,
            model=model,
            status=delegation_status,
            metadata=metadata,
        )
        delegation = projected["delegation"]
        usage_event = None
        if projected["changed"]:
            event_type = "external_delegation_finished" if projected["terminal_transition"] else "external_delegation_started" if projected["created"] else "external_delegation_updated"
            self.orchestration_ledger.append_event(
                run_id,
                wave_id=wave_id,
                delegation_id=delegation_id,
                event_type=event_type,
                state_before=ctx.state,
                state_after=ctx.state,
                payload={"source": "opencode:message.updated", "provider_id": provider_id, "model": model, "session_id": telemetry["session_id"], "message_id": telemetry["message_id"], "provider_message_status": telemetry["status"], "finish": telemetry.get("finish") or "", "status": delegation["status"], "economics": economics},
            )
        if delegation_status in {"completed", "failed"}:
            usage_event = usage_event_from_provider_delegation(
                run_id=run_id,
                wave_id=wave_id,
                delegation=delegation,
                source="opencode:provider_dispatch" if dispatch else "opencode:message.updated",
            )
            if usage_event is not None:
                self.orchestration_ledger.record_usage_event(
                    run_id=run_id,
                    wave_id=wave_id,
                    delegation_id=delegation_id,
                    usage_event=usage_event,
                )
        return {"run_id": run_id, "wave_id": wave_id, "delegation_id": delegation_id, "changed": bool(projected["changed"]), "created": bool(projected["created"]), "delegation": delegation, "usage_event": usage_event}

    def _require_provider_supervisor(self, identity: dict[str, Any]) -> None:
        if (str(identity.get("client_id") or ""), str(identity.get("client_type") or "")) != ("electron-panel", "electron"):
            raise ToolFailure("PROVIDER_DISPATCH_CLIENT_DENIED", "Provider dispatch lifecycle is restricted to the Electron supervisor.", category="security", retryable=False)
        self._touch_hub_client(identity)

    def _provider_context(self) -> tuple[str, str, RunContext]:
        state = self.task_state.get()
        projection = state.get("orchestration") if isinstance(state.get("orchestration"), dict) else {}
        run_id = str(projection.get("run_id") or "").strip()
        wave_id = str(projection.get("wave_id") or "").strip()
        ctx = self.orchestration_control.snapshot(run_id) if run_id else None
        run = self.orchestration_ledger.get_run(run_id) if run_id else None
        if not ctx or not run or run.get("status") != "active" or not wave_id or ctx.wave_id != wave_id or ctx.state not in HUB_PROVIDER_TELEMETRY_STATES:
            raise ToolFailure("PROVIDER_DISPATCH_CONTEXT_UNAVAILABLE", "Provider dispatch requires the current active task-projected orchestration wave.", category="runtime", retryable=True)
        return run_id, wave_id, ctx

    @staticmethod
    def _provider_traffic_key(*, run_id: str, wave_id: str, model: str, request_id: str = "", prompt_sha256: str = "") -> str:
        identity = str(request_id or prompt_sha256 or "").strip()
        if not identity:
            return ""
        return hashlib.sha256(f"{run_id}\0{wave_id}\0{model}\0{identity}".encode("utf-8")).hexdigest()

    def provider_traffic_snapshot(self) -> dict[str, Any]:
        capacity_fn = getattr(self._opencode_provider, "capacity_status", None)
        opencode_capacity = capacity_fn() if callable(capacity_fn) else {
            "provider_id": "opencode-go",
            "active_requests": int(self._opencode_provider.active_count()),
            "retained_dispatches": None,
            "retained_limit": None,
            "models": sorted(ALLOWED_OPENCODE_MODELS),
            "read_only_enforced": True,
        }
        return {
            "schema_version": 1,
            "policy": self.provider_traffic.snapshot(models=ALLOWED_OPENCODE_MODELS),
            "capacity": {
                "opencode": opencode_capacity,
                "codex": {"capacity_cooldowns": self._codex_bridge.capacity_status()},
            },
            "automatic_routing": {"enabled": False, "mode": "evidence_gated", "reason": "representative_accepted_cohorts_required"},
        }

    def _shadow_route_context(self) -> tuple[str, str, RunContext]:
        state = self.task_state.get()
        projection = state.get("orchestration") if isinstance(state.get("orchestration"), dict) else {}
        run_id = str(projection.get("run_id") or "").strip()
        wave_id = str(projection.get("wave_id") or "").strip()
        ctx = self.orchestration_control.snapshot(run_id) if run_id else None
        run = self.orchestration_ledger.get_run(run_id) if run_id else None
        allowed_states = {"PREFLIGHT", "READY", "ROUTED", "EXECUTING", "PROVING", "ACCEPTING"}
        if not ctx or not run or run.get("status") != "active" or not wave_id or ctx.wave_id != wave_id or ctx.state not in allowed_states:
            raise ToolFailure("SHADOW_ROUTE_CONTEXT_UNAVAILABLE", "Shadow routing requires the current active task-projected nonterminal orchestration wave.", category="runtime", retryable=True)
        return run_id, wave_id, ctx

    def shadow_route(self, identity: dict[str, Any], features: Any) -> dict[str, Any]:
        self._require_provider_supervisor(identity)
        run_id, wave_id, ctx = self._shadow_route_context()
        try:
            recommendation = recommend_shadow_route(features)
        except ValueError as exc:
            raise ToolFailure("SHADOW_ROUTE_INVALID", str(exc), category="validation", retryable=False) from exc
        recommendation["run_id"] = run_id
        recommendation["wave_id"] = wave_id
        recommendation["recommendation_id"] = recommendation_id(
            run_id=run_id,
            wave_id=wave_id,
            recommendation=recommendation,
        )
        recorded = self.orchestration_ledger.record_shadow_route(
            run_id=run_id,
            wave_id=wave_id,
            recommendation=recommendation,
        )
        return {
            "run_id": run_id,
            "wave_id": wave_id,
            "orchestration_state": ctx.state,
            "recommendation": recommendation,
            "recorded": recorded["recorded"],
            "routing_evidence": self.orchestration_ledger.routing_evidence(run_id),
        }

    def _sync_opencode_dispatch(self, snapshot: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
        provider_status = str(snapshot.get("status") or "")
        if provider_status != "running":
            self.provider_traffic.complete(self._provider_traffic_key(
                run_id=str(snapshot.get("run_id") or ""),
                wave_id=str(snapshot.get("wave_id") or ""),
                model=str(snapshot.get("model") or ""),
                request_id=str(snapshot.get("request_id") or ""),
                prompt_sha256=str(snapshot.get("prompt_sha256") or ""),
            ))
        delegation_status = "active" if provider_status == "running" else "completed" if provider_status == "completed" else "failed"
        metadata = {
            "source": "opencode:provider_adapter",
            "provider_dispatch_id": snapshot["dispatch_id"],
            "session_id": snapshot.get("session_id") or "",
            "side_effect_class": "read_only",
            "read_only_enforced": True,
            "prompt_sha256": snapshot["prompt_sha256"],
            "prompt_bytes": snapshot["prompt_bytes"],
            "result_chars": snapshot.get("result_chars", 0),
            "output_truncated": bool(snapshot.get("output_truncated")),
            "error_class": snapshot.get("error_class"),
            "lifecycle_evidence": snapshot.get("lifecycle_evidence") or {},
            "timing": snapshot.get("timing") or {},
        }
        projected = self.orchestration_ledger.upsert_external_delegation(
            delegation_id=str(snapshot["delegation_id"]),
            wave_id=str(snapshot["wave_id"]),
            authority_owner="opencode",
            route_requested="opencode_read_only",
            route_resolved=str(snapshot["model"]),
            model=str(snapshot["model"]),
            status=delegation_status,
            metadata=metadata,
        )
        if projected["changed"]:
            event_type = "external_delegation_finished" if projected["terminal_transition"] else "external_delegation_started" if projected["created"] else "external_delegation_updated"
            self.orchestration_ledger.append_event(
                ctx.run_id,
                wave_id=ctx.wave_id,
                delegation_id=str(snapshot["delegation_id"]),
                event_type=event_type,
                state_before=ctx.state,
                state_after=ctx.state,
                payload={
                    "source": "opencode:provider_adapter",
                    "provider_dispatch_id": snapshot["dispatch_id"],
                    "model": snapshot["model"],
                    "status": delegation_status,
                    "side_effect_class": "read_only",
                    "read_only_enforced": True,
                    "prompt_sha256": snapshot["prompt_sha256"],
                    "prompt_bytes": snapshot["prompt_bytes"],
                    "error_class": snapshot.get("error_class"),
                    "timing": snapshot.get("timing") or {},
                },
            )
        delegation = projected["delegation"]
        if delegation["status"] in {"completed", "failed"}:
            usage_event = usage_event_from_provider_delegation(
                run_id=ctx.run_id,
                wave_id=ctx.wave_id,
                delegation=delegation,
                source="opencode:provider_dispatch",
                total_ms=(snapshot.get("timing") or {}).get("total_ms"),
            )
            if usage_event is not None:
                self.orchestration_ledger.record_usage_event(
                    run_id=ctx.run_id,
                    wave_id=ctx.wave_id,
                    delegation_id=str(snapshot["delegation_id"]),
                    usage_event=usage_event,
                )
        return delegation

    def _on_opencode_provider_terminal(self, snapshot: dict[str, Any]) -> None:
        ctx = self.orchestration_control.snapshot(str(snapshot.get("run_id") or ""))
        if ctx is None or ctx.wave_id != str(snapshot.get("wave_id") or ""):
            return
        try:
            self._sync_opencode_dispatch(snapshot, ctx)
        except (OSError, RuntimeError, ValueError):
            return

    def dispatch_opencode_provider(self, identity: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
        self._require_provider_supervisor(identity)
        run_id, wave_id, ctx = self._provider_context()
        model = str(payload.get("model") or "").strip()
        if model not in ALLOWED_OPENCODE_MODELS:
            raise ToolFailure("PROVIDER_MODEL_DENIED", "Only the allowlisted OpenCode Go Flash/Pro models may be dispatched.", category="validation", retryable=False)
        prompt = str(payload.get("prompt") or "")
        request_id = str(payload.get("request_id") or "").strip()[:128]
        traffic_key = self._provider_traffic_key(
            run_id=run_id,
            wave_id=wave_id,
            model=model,
            request_id=request_id,
            prompt_sha256=hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        )
        raw_token_budget = payload.get("token_budget")
        if raw_token_budget is not None and (isinstance(raw_token_budget, bool) or not isinstance(raw_token_budget, int) or raw_token_budget < 0):
            raise ToolFailure("PROVIDER_TOKEN_BUDGET_INVALID", "token_budget must be a non-negative integer when provided.", category="validation", retryable=False)
        admission = self.provider_traffic.admit(model, traffic_key, token_budget=raw_token_budget)
        if not admission.get("allowed"):
            raise ToolFailure(
                "PROVIDER_ADMISSION_DENIED",
                f"Provider admission denied: {admission.get('reason')}",
                category="runtime",
                retryable=admission.get("reason") in {"concurrency_exhausted", "rpm_exhausted", "tpm_exhausted"},
                details=admission,
            )
        try:
            snapshot = self._opencode_provider.start(
                run_id=run_id,
                wave_id=wave_id,
                model=model,
                prompt=prompt,
                timeout_ms=int(payload.get("timeout_ms") or 60_000),
                request_id=request_id,
            )
        except OpenCodeProviderError as exc:
            self.provider_traffic.abort(traffic_key)
            raise ToolFailure(exc.code, exc.message, category="runtime", retryable=exc.retryable, details=exc.details) from exc
        delegation = self._sync_opencode_dispatch(snapshot, ctx)
        return {"run_id": run_id, "wave_id": wave_id, "dispatch": snapshot, "delegation": delegation, "admission": admission}

    def observe_opencode_provider(self, identity: dict[str, Any], dispatch_id: str, *, cancel: bool = False) -> dict[str, Any]:
        self._require_provider_supervisor(identity)
        try:
            snapshot = self._opencode_provider.cancel(dispatch_id) if cancel else self._opencode_provider.observe(dispatch_id)
        except OpenCodeProviderError as exc:
            raise ToolFailure(exc.code, exc.message, category="runtime", retryable=exc.retryable, details=exc.details) from exc
        ctx = self.orchestration_control.snapshot(str(snapshot.get("run_id") or ""))
        if ctx is None or ctx.wave_id != str(snapshot.get("wave_id") or ""):
            raise ToolFailure("PROVIDER_DISPATCH_CONTEXT_UNAVAILABLE", "Provider dispatch no longer maps to a known orchestration wave.", category="runtime", retryable=False)
        delegation = self._sync_opencode_dispatch(snapshot, ctx)
        return {"run_id": ctx.run_id, "wave_id": ctx.wave_id, "dispatch": snapshot, "delegation": delegation}

    def _require_hub_controller(self, run_id: str) -> dict[str, Any] | None:
        identity = self._current_hub_client()
        if identity is None:
            return None
        self._touch_hub_client(identity)
        controller = self.orchestration_ledger.get_controller_lease(run_id)
        client_id = str(identity.get("client_id") or "")
        client_type = str(identity.get("client_type") or "client")
        run = self.orchestration_ledger.get_run(run_id)
        if run and run.get("status") == "active":
            if controller and controller.get("status") == "active" and controller.get("owner_client_id") == client_id:
                renewed = self.orchestration_ledger.acquire_controller_lease(
                    run_id=run_id,
                    owner_client_id=client_id,
                    lease_id=str(controller.get("lease_id") or f"client:{client_id}"),
                    ttl_seconds=HUB_CONTROLLER_LEASE_SECONDS,
                )
                controller = renewed if renewed.get("acquired") else controller
            elif (not controller or controller.get("status") != "active") and client_type == "chatweb":
                claimed = self.orchestration_ledger.acquire_controller_lease(
                    run_id=run_id,
                    owner_client_id=client_id,
                    lease_id=f"client:{client_id}",
                    ttl_seconds=HUB_CONTROLLER_LEASE_SECONDS,
                )
                controller = claimed if claimed.get("acquired") else self.orchestration_ledger.get_controller_lease(run_id)
        if not controller or controller.get("status") != "active" or controller.get("owner_client_id") != client_id:
            raise ToolFailure(
                "CONTROLLER_LEASE_REQUIRED",
                "This client is not the active semantic controller for the orchestration run.",
                category="security",
                retryable=True,
                details={
                    "run_id": run_id,
                    "client_id": client_id,
                    "controller": {
                        "owner_client_id": (controller or {}).get("owner_client_id"),
                        "status": (controller or {}).get("status", "missing"),
                        "fencing_token": (controller or {}).get("fencing_token"),
                    },
                },
            )
        return controller

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
            "tool_contract": dict(self.tool_contract),
            "tool_metadata": tool_metadata_contract(),
        }

    def _background_operation_snapshot(self, operation: dict[str, Any], *, include_result: bool = False) -> dict[str, Any]:
        event = operation["event"]
        finished = event.is_set()
        finished_monotonic = operation.get("finished_monotonic")
        observed_monotonic = (
            float(finished_monotonic)
            if finished and isinstance(finished_monotonic, (int, float))
            else time.monotonic()
        )
        payload: dict[str, Any] = {
            "operation_id": operation["operation_id"],
            "tool": operation["tool"],
            "workspace": operation.get("workspace"),
            "status": "completed" if finished else "running",
            "elapsed_seconds": max(0, int(observed_monotonic - operation["started_monotonic"])),
            "requires_progress_report": not finished,
        }
        if finished and operation.get("finished_at"):
            payload["finished_at"] = operation["finished_at"]
        budget = operation.get("budget")
        if isinstance(budget, BudgetDeadline):
            finished_remaining = operation.get("finished_budget_remaining_seconds")
            payload["budget"] = {
                "max_runtime_seconds": budget.max_runtime_seconds,
                "remaining_seconds": (
                    float(finished_remaining)
                    if finished and isinstance(finished_remaining, (int, float))
                    else budget.remaining_seconds()
                ),
                "exceeded": budget.exceeded,
            }
        if finished and operation.get("error"):
            payload["status"] = "failed"
            payload["error"] = operation["error"]
        if include_result and finished and operation.get("result") is not None:
            payload["result"] = operation["result"]
        return payload

    def _background_operation_cancelled(self) -> bool:
        event = getattr(self.request_context, "background_cancel_event", None)
        return bool(event is not None and event.is_set())

    def _background_operation_remaining_seconds(self) -> float | None:
        budget = getattr(self.request_context, "background_budget", None)
        if not isinstance(budget, BudgetDeadline):
            return None
        return budget.remaining_seconds()

    def _start_background_tool(
        self,
        name: str,
        arguments: dict[str, Any],
        *,
        request_id: str | int | None,
    ) -> tuple[dict[str, Any], threading.Event]:
        operation_id = secrets.token_urlsafe(12)
        done = threading.Event()
        worker_done = threading.Event()
        cancel_event = threading.Event()
        finalize_lock = threading.Lock()
        try:
            timeout_seconds = min(int(arguments.get("timeout_seconds", 600)), 3600)
        except (TypeError, ValueError):
            timeout_seconds = 600
        timeout_seconds = max(1, timeout_seconds)
        if name == "agent_workflow":
            try:
                workflow_runtime_seconds = min(
                    max(1, int(arguments.get("max_runtime_seconds", 600))),
                    600,
                )
            except (TypeError, ValueError):
                workflow_runtime_seconds = 600
            timeout_seconds = min(timeout_seconds, workflow_runtime_seconds)
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
            "cancel_event": cancel_event,
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

        def finalize_operation(
            *,
            status: str,
            error: dict[str, Any] | None,
            summary: dict[str, Any],
        ) -> bool:
            with finalize_lock:
                if operation.get("finalized"):
                    return False
                operation["finalized"] = True
                if error is not None:
                    operation["error"] = error
                operation["finished_monotonic"] = time.monotonic()
                operation["finished_at"] = datetime.now(timezone.utc).isoformat()
                operation["finished_budget_remaining_seconds"] = budget.remaining_seconds()
                try:
                    self.orchestration_ledger.finish_background_operation(
                        operation_id,
                        status=status,
                        summary=summary,
                    )
                finally:
                    done.set()
                return True

        def worker() -> None:
            previous_cancel_event = getattr(self.request_context, "background_cancel_event", None)
            previous_budget = getattr(self.request_context, "background_budget", None)
            self.request_context.background_cancel_event = cancel_event
            self.request_context.background_budget = budget
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
                if previous_cancel_event is None:
                    try:
                        del self.request_context.background_cancel_event
                    except AttributeError:
                        pass
                else:
                    self.request_context.background_cancel_event = previous_cancel_event
                if previous_budget is None:
                    try:
                        del self.request_context.background_budget
                    except AttributeError:
                        pass
                else:
                    self.request_context.background_budget = previous_budget
                try:
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
                    budget_error = operation.get("budget_error")
                    error = budget_error if isinstance(budget_error, dict) else operation.get("error")
                    finalize_operation(
                        status=(
                            "timed_out"
                            if isinstance(budget_error, dict)
                            else "failed"
                            if error
                            else "completed"
                        ),
                        error=error if isinstance(error, dict) else None,
                        summary={
                            "result_available_in_memory": result is not None,
                            "result_status": result_status,
                            "error": error,
                            "worker_terminalized": True,
                        },
                    )
                finally:
                    worker_done.set()

        def watchdog() -> None:
            while not done.is_set():
                try:
                    budget.check()
                except ToolFailure as exc:
                    budget_error = {
                        "code": exc.code,
                        "message": exc.message,
                        "category": exc.category,
                        "retryable": False,
                    }
                    operation["budget_error"] = budget_error
                    cancel_event.set()
                    if worker_done.wait(BACKGROUND_BUDGET_TERMINAL_GRACE_SECONDS):
                        return
                    finalize_operation(
                        status="timed_out",
                        error=budget_error,
                        summary={
                            "error": budget_error,
                            "budget": exc.details,
                            "worker_terminalized": False,
                            "terminalization_grace_exceeded": True,
                        },
                    )
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
        args = dict(arguments or {})
        dispatch_started_wall_utc = utc_now()
        dispatch_started_at = time.monotonic()
        try:
            self._activation_enter_tool_call(name, args)
        except ToolFailure as exc:
            return make_tool_result(name, {
                "ok": False,
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "category": exc.category,
                    "retryable": exc.retryable,
                    "details": exc.details,
                },
            }, is_error=True)
        try:
            if not str(args.get("idempotency_key", "") or "").strip():
                if (
                    name == "agent_workflow"
                    and self._idempotency_policy(name, args) == "required"
                ):
                    # Auto-key derivation happens before the normal dispatch validator.
                    # Validate first so an invalid request cannot create a task epoch.
                    validate_arguments(name, args)
                    self._ensure_agent_workflow_task_epoch(args)
                derived_key = self._derive_idempotency_key(name, args)
                if derived_key:
                    args["idempotency_key"] = derived_key
            try:
                result = self._call_tool_dispatch(name, args, request_id=request_id)
            except ExceptionGroup as exc:
                failure = normalize_exception_group(exc)
                self._idempotency_finish(name, args, exc=failure)
                payload = {
                    "ok": False,
                    "error": {
                        "code": failure.code,
                        "message": failure.message,
                        "category": failure.category,
                        "retryable": failure.retryable,
                        "details": failure.details,
                    },
                }
                self._record_task_tool_result(name, args, payload)
                self.emit_tool_trace(
                    name,
                    args,
                    payload,
                    dispatch_started_at,
                    started_wall_utc=dispatch_started_wall_utc,
                )
                return make_tool_result(name, payload, is_error=True)
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
        finally:
            self._activation_leave_tool_call()

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
        started_wall_utc = utc_now()
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
            self.emit_tool_trace(name, args, payload, started_at, started_wall_utc=started_wall_utc)
            content = spec.content_builder(payload) if spec.content_builder else None
            payload.setdefault("presentation", TOOL_CONTRACT_RUNTIME.presentation(name, payload))
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
            self.emit_tool_trace(name, args, payload, started_at, started_wall_utc=started_wall_utc)
            return make_tool_result(name, payload, is_error=True)
        except Exception as exc:  # noqa: BLE001 - tool failures must stay structured
            if isinstance(exc, ExceptionGroup):
                grouped = normalize_exception_group(exc)
                error = {
                    "code": grouped.code,
                    "message": grouped.message,
                    "category": grouped.category,
                    "retryable": grouped.retryable,
                    "details": grouped.details,
                }
            else:
                error = {
                    "code": "INTERNAL_ERROR",
                    "message": str(exc),
                    "category": "internal",
                    "retryable": False,
                    "details": {},
                }
            payload = {"ok": False, "error": error}
            if spec.error_status:
                payload["status"] = spec.error_status
            self._record_task_tool_result(name, args, payload)
            self.emit_tool_trace(name, args, payload, started_at, started_wall_utc=started_wall_utc)
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
            started_wall_utc = utc_now()
            started = time.monotonic()
            try:
                payload = self.workspace_context({"path": ".", "max_entries": 40, "detail": "compact"})
                payload["preheated"] = True
                ok = True
            except Exception:
                ok = False
            finished = time.monotonic()
            finished_wall_utc = utc_now()
            try:
                self.performance_trace.record(
                    tool="workspace_preheat", started_monotonic=started, finished_monotonic=finished, ok=ok,
                    started_wall_utc=started_wall_utc, finished_wall_utc=finished_wall_utc,
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
        result = {
            **ctx.projection(),
            "integrity": self.orchestration_ledger.verify_chain(ctx.run_id),
            "reports": reports,
            "final_acceptance_required": ctx.state == "ACCEPTING",
        }
        if str(ctx.state or "").upper() in OPERATOR_REPORT_STATES:
            result["completion_report"] = build_operator_completion_report(
                ledger=self.orchestration_ledger,
                ctx=ctx,
                task_state=self.task_state.get(),
                reports=reports,
            )
        return result

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
    def _loaded_behavior_identity() -> dict[str, Any]:
        """Fingerprint loaded code objects so restart activation can be proven."""
        targets = {
            "provider_cost_attribution": Runtime.ingest_provider_telemetry,
            "patch_preflight": Runtime._preflight_patch_sequence,
            "verification_workdir": Runtime.verify_build,
            "verification_runner": run_build_verification,
            "stale_reconciliation": OrchestrationLedger.reconcile_stale_runs,
            "routing_policy": Runtime._select_agent_execution_route,
            "external_review_policy": Runtime._maybe_agent_workflow_external_review,
        }
        components = {
            name: hashlib.sha256(marshal.dumps(target.__code__)).hexdigest()
            for name, target in targets.items()
        }
        encoded = json.dumps(components, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return {
            "schema_version": 1,
            "algorithm": "sha256_python_marshal_code",
            "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "fingerprint": hashlib.sha256(encoded).hexdigest(),
            "components": components,
        }

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


    @staticmethod
    def _measured_phase_timing(payload: dict[str, Any]) -> dict[str, Any]:
        """Extract only live measured composite-read timing from a tool result.

        Cached context carries timing from the original execution; replaying it
        into PerformanceTrace would double-count old work, so cached projections
        deliberately return no timing sample here.
        """
        candidates: list[Any] = [payload]
        for key in ("prepared", "context"):
            nested = payload.get(key)
            if isinstance(nested, dict):
                candidates.append(nested)
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            composite = candidate.get("composite_read")
            if not isinstance(composite, dict):
                continue
            cache = composite.get("cache") if isinstance(composite.get("cache"), dict) else {}
            if cache.get("hit"):
                continue
            execution = composite.get("execution") if isinstance(composite.get("execution"), dict) else {}
            timing = execution.get("phase_timing") if isinstance(execution.get("phase_timing"), dict) else {}
            if str(timing.get("source") or "") != "monotonic_local":
                continue
            return {"scope": "composite_read", **timing}
        return {}

    @staticmethod
    def _measured_localization(payload: dict[str, Any]) -> dict[str, Any]:
        """Extract live, content-free localization counts from composite read."""
        candidates: list[Any] = [payload]
        for key in ("prepared", "context"):
            nested = payload.get(key)
            if isinstance(nested, dict):
                candidates.append(nested)
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            composite = candidate.get("composite_read")
            if not isinstance(composite, dict):
                continue
            cache = composite.get("cache") if isinstance(composite.get("cache"), dict) else {}
            if cache.get("hit"):
                continue
            plan = composite.get("plan") if isinstance(composite.get("plan"), dict) else {}
            execution = composite.get("execution") if isinstance(composite.get("execution"), dict) else {}
            localization = execution.get("localization") if isinstance(execution.get("localization"), dict) else {}
            provider = localization.get("provider") if isinstance(localization.get("provider"), dict) else {}
            try:
                query_count = max(0, int(plan.get("query_count", 0) or 0))
                attempted = max(0, int(localization.get("semantic_attempted", 0) or 0))
                handled = max(0, int(localization.get("semantic_handled", 0) or 0))
                fallback = max(0, int(localization.get("text_fallback_queries", 0) or 0))
            except (TypeError, ValueError):
                continue
            if query_count <= 0:
                continue
            return {
                "semantic_available": provider.get("available") is True,
                "query_count": query_count,
                "semantic_attempted": attempted,
                "semantic_handled": handled,
                "text_fallback_queries": fallback,
            }
        return {}

    @staticmethod
    def _measured_result_tail(payload: dict[str, Any]) -> dict[str, Any]:
        """Extract content-free large-result paging measurements."""
        candidates: list[Any] = [payload]
        execution = payload.get("execution")
        if isinstance(execution, dict):
            candidates.append(execution)
        error = payload.get("error")
        if isinstance(error, dict) and isinstance(error.get("details"), dict):
            candidates.append(error["details"])
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            direct = candidate.get("result_tail")
            if isinstance(direct, dict):
                return dict(direct)
            diff = candidate.get("git_diff")
            if isinstance(diff, dict) and isinstance(diff.get("result_tail"), dict):
                return dict(diff["result_tail"])
        return {}

    def emit_tool_trace(
        self,
        name: str,
        args: dict[str, Any],
        payload: dict[str, Any],
        started_at: float,
        *,
        started_wall_utc: str = "",
    ) -> None:
        raw_error = payload.get("error")
        error = raw_error if isinstance(raw_error, dict) else {}
        finished_at = time.monotonic()
        finished_wall_utc = utc_now()
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
            proof_cache_eligible = max(0, int(proof_summary.get("eligible", 0) or 0))
        except (TypeError, ValueError):
            proof_cache_eligible = 0
        try:
            proof_cache_misses = max(0, int(proof_summary.get("cache_misses", 0) or 0))
        except (TypeError, ValueError):
            proof_cache_misses = 0
        raw_miss_reasons = proof_summary.get("cache_miss_reasons")
        proof_cache_miss_reasons = raw_miss_reasons if isinstance(raw_miss_reasons, dict) else {}
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
                started_wall_utc=started_wall_utc,
                finished_wall_utc=finished_wall_utc,
                request_bytes=len(json.dumps(args, ensure_ascii=False, default=str).encode("utf-8")),
                response_bytes=len(json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")),
                model_visible_bytes=model_visible_text_bytes(
                    name,
                    payload,
                    is_error=bool(payload.get("ok") is False),
                ),
                ok=bool(payload.get("ok", False)),
                cache_hit=bool(payload.get("cache_hit") or (isinstance(payload.get("cache"), dict) and payload["cache"].get("hit"))),
                deduplicated=bool(payload.get("deduplicated")),
                idempotency_eligible=self._idempotency_eligible_call(name, args),
                idempotency_key_present=bool(str(args.get("idempotency_key", "") or "").strip()),
                idempotency_policy=self._idempotency_policy(name, args),
                idempotency_key_source=self._idempotency_key_source(args),
                idempotency_operation=self._idempotency_operation(name, args),
                idempotency_missing_reason=self._idempotency_missing_reason(name, args),
                error_class=self._error_class(error),
                proof_cache_eligible=proof_cache_eligible,
                proof_cache_hits=proof_cache_hits,
                proof_cache_misses=proof_cache_misses,
                proof_cache_miss_reasons=proof_cache_miss_reasons,
                proof_cache_saved_ms=proof_cache_saved_ms,
                orchestration=trace_orchestration,
                phase_timing=self._measured_phase_timing(payload),
                localization=self._measured_localization(payload),
                result_tail=self._measured_result_tail(payload),
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
        trace_args = redact_for_trace(args)
        try:
            max_trace_bytes = max(
                1024,
                min(
                    64 * 1024,
                    int(os.environ.get(f"{ENV_PREFIX}_TRACE_MAX_PAYLOAD_BYTES", str(TRACE_MAX_PAYLOAD_BYTES))),
                ),
            )
        except (TypeError, ValueError):
            max_trace_bytes = TRACE_MAX_PAYLOAD_BYTES
        encoded_trace_args = json.dumps(trace_args, ensure_ascii=False, separators=(",", ":"), default=str)
        if len(encoded_trace_args.encode("utf-8")) > max_trace_bytes:
            trace_args = {
                "_trace_truncated": True,
                "_trace_bytes": len(encoded_trace_args.encode("utf-8")),
                "_trace_max_bytes": max_trace_bytes,
                "keys": sorted(str(key) for key in args)[:50],
            }
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
            "args": trace_args,
        }
        print(json.dumps(event, sort_keys=True, separators=(",", ":")), file=sys.stderr, flush=True)

    @staticmethod
    def _idempotency_policy(name: str, args: dict[str, Any]) -> str:
        """Classify replay protection without pretending every mutation has a stable identity."""
        if name == "agent_workflow":
            phase = str(args.get("phase", "prepare")).strip().lower()
            if phase == "execute":
                return "required"
            return "optional" if phase == "run" else "none"
        if name == "task_control":
            action = str(args.get("action", "get")).strip().lower()
            if action in {"accept", "reject"}:
                return "required"
            if action == "handoff":
                return "optional" if str(args.get("handoff_action", "get")).strip().lower() == "record" else "none"
            return "optional" if action in {"start", "update", "pause", "stop", "resume", "clear", "restart_runtime"} else "none"
        if name == "document_workflow":
            return "optional" if str(args.get("action", "inspect")).strip().lower() in {"create", "convert", "rebuild"} else "none"
        if name == "command_control":
            return "optional" if str(args.get("action", "poll")).strip().lower() in {"write", "kill"} else "none"
        if name == "write_stdin":
            return "optional" if bool(str(args.get("chars", ""))) else "none"
        spec = TOOL_REGISTRY.get(name)
        return "optional" if spec and not spec.read_only and (spec.destructive or spec.open_world) else "none"

    @staticmethod
    def _idempotency_operation(name: str, args: dict[str, Any]) -> str:
        if name == "agent_workflow":
            return f"agent_workflow:{str(args.get('phase', 'prepare')).strip().lower()}"
        if name == "task_control":
            return f"task_control:{str(args.get('action', 'get')).strip().lower()}"
        if name == "command_control":
            return f"command_control:{str(args.get('action', 'poll')).strip().lower()}"
        return name

    def _idempotency_missing_reason(self, name: str, args: dict[str, Any]) -> str:
        if self._idempotency_policy(name, args) != "required" or str(args.get("idempotency_key", "") or "").strip():
            return ""
        if name == "agent_workflow":
            return "missing_task_epoch" if not str(self.task_state.get().get("task_id") or "").strip() else "missing_stable_identity"
        if name == "task_control":
            projection = self.task_state.get().get("orchestration", {})
            projection = projection if isinstance(projection, dict) else {}
            if not str(args.get("run_id") or projection.get("run_id") or "").strip():
                return "missing_run"
            if not str(args.get("wave_id") or projection.get("wave_id") or "").strip():
                return "missing_wave"
        return "missing_stable_identity"

    def _ensure_agent_workflow_task_epoch(self, args: dict[str, Any]) -> str:
        if str(args.get("phase", "prepare")).strip().lower() != "execute":
            return ""
        current = self.task_state.get()
        projection = current.get("orchestration") if isinstance(current.get("orchestration"), dict) else {}
        run_id = str(projection.get("run_id") or "").strip()
        current_ctx = self.orchestration_control.snapshot(run_id) if run_id else None
        if current.get("task_id") and current_ctx is not None and current_ctx.state not in {"CHECKPOINTED", "BLOCKED", "ABORTED"}:
            return str(current["task_id"])
        objective = str(args.get("objective") or current.get("objective") or "Complete coding workflow").strip()
        ensured = self.task_state.ensure_started(objective, current_step="Orchestration preflight")
        return str(ensured.get("task_id") or "")

    def _derive_idempotency_key(self, name: str, args: dict[str, Any]) -> str:
        if self._idempotency_policy(name, args) != "required":
            return ""
        current_task = self.task_state.get()
        projection = current_task.get("orchestration") if isinstance(current_task.get("orchestration"), dict) else {}
        run_id = str(args.get("run_id") or projection.get("run_id") or "").strip()
        wave_id = str(args.get("wave_id") or projection.get("wave_id") or "").strip()
        if name == "agent_workflow" and str(args.get("phase", "prepare")).strip().lower() == "execute":
            task_id = str(current_task.get("task_id") or "").strip()
            if not task_id:
                return ""
            operation = "agent_workflow:execute"
            identity_scope = f"task={task_id}"
        elif name == "task_control" and str(args.get("action", "get")).strip().lower() in {"accept", "reject"}:
            if not run_id or not wave_id:
                return ""
            operation = f"task_control:{str(args.get('action')).strip().lower()}"
            identity = self._current_hub_client() or {}
            controller = self.orchestration_ledger.get_controller_lease(run_id) or {}
            caller_id = str(identity.get("client_id") or "local").strip() or "local"
            fencing_token = int(controller.get("fencing_token") or 0)
            identity_scope = f"run={run_id}\0wave={wave_id}\0caller={caller_id}\0fence={fencing_token}"
        else:
            return ""
        request_hash = self._request_hash(args)
        digest = hashlib.sha256(
            f"{operation}\0{identity_scope}\0{request_hash}".encode("utf-8", errors="replace")
        ).hexdigest()
        return f"{AUTO_IDEMPOTENCY_KEY_PREFIX}{digest}"

    @staticmethod
    def _idempotency_key_source(args: dict[str, Any]) -> str:
        key = str(args.get("idempotency_key", "") or "").strip()
        if not key:
            return "none"
        return "derived" if key.startswith(AUTO_IDEMPOTENCY_KEY_PREFIX) else "explicit"

    @staticmethod
    def _error_class(error: dict[str, Any]) -> str:
        code = str(error.get("code") or "").strip().upper()
        category = str(error.get("category") or "").strip().lower()
        if not code:
            return ""
        if code.startswith("CANDIDATE_TARGET_") or code == "INVALID_CANDIDATE_PATH":
            return "CONTROL_PATH"
        if code.startswith("PROOF_CWD"):
            return "CONTROL_CWD"
        if "CONNECTOR" in code:
            return "CONTROL_CONNECTOR"
        if code.startswith(("SCHEMA_", "CONTRACT_", "STALE_CONTRACT")) or code in {"INVALID_TOOL_SCHEMA", "CONTRACT_MISMATCH"}:
            return "CONTROL_SCHEMA"
        if "CAPACITY" in code or code in {"QUEUE_FULL", "RATE_LIMITED"}:
            return "CAPACITY"
        if "TIMEOUT" in code or "DEADLINE" in code:
            return "DEADLINE"
        if code in {"PROMPT_TOO_LARGE", "PROMPT_SIZE_EXCEEDED"}:
            return "PROMPT_SIZE"
        if code.startswith("CANDIDATE_") and code not in {"CANDIDATE_TARGET_MISSING"}:
            return "MODEL_CANDIDATE_INVALID"
        if "BASE_DRIFT" in code or "STALE_BASE" in code:
            return "BASE_DRIFT"
        if "PATCH_AMBIGU" in code:
            return "PATCH_AMBIGUOUS"
        if code.startswith("PROOF_") and any(token in code for token in ("INFRA", "TOOL", "UNAVAILABLE", "TIMEOUT")):
            return "PROOF_INFRA"
        if code.startswith("PROOF_") or code in {"TEST_FAILED", "BUILD_FAILED", "ASSERTION_FAILED"}:
            return "PROOF_CODE_FAILURE"
        if category in {"permission", "security"} or any(token in code for token in ("PERMISSION", "AUTHORITY", "WRITE_LEASE", "CONTROLLER_FENCE")):
            return "AUTHORITY_DENIED"
        if code in {"TASK_PAUSED", "TASK_STOPPED", "USER_BLOCKED", "USER_INPUT_REQUIRED"}:
            return "USER_BLOCKED"
        if code.startswith(("PROVIDER_", "OPENCODE_")):
            return "PROVIDER"
        if code.startswith("IDEMPOT"):
            return "IDEMPOTENCY"
        if category == "validation":
            return "VALIDATION"
        if category == "runtime":
            return "RUNTIME"
        structured_category_classes = {
            "filesystem": "FILESYSTEM",
            "policy": "POLICY",
            "not_found": "NOT_FOUND",
            "internal": "INTERNAL",
            "conflict": "CONFLICT",
        }
        if category in structured_category_classes:
            return structured_category_classes[category]
        return "UNKNOWN"

    @staticmethod
    def _idempotency_eligible_call(name: str, args: dict[str, Any]) -> bool:
        """Legacy v4 denominator retained for historical trace comparability."""
        if name == "agent_workflow":
            return str(args.get("phase", "prepare")).strip().lower() in {"execute", "run"}
        if name == "document_workflow":
            return str(args.get("action", "inspect")).strip().lower() in {"create", "convert"}
        if name == "task_control":
            action = str(args.get("action", "get")).strip().lower()
            if action == "handoff":
                return str(args.get("handoff_action", "get")).strip().lower() == "record"
            return action in {"start", "update", "pause", "stop", "resume", "clear", "accept", "reject", "restart_runtime"}
        if name == "command_control":
            return str(args.get("action", "poll")).strip().lower() in {"write", "kill"}
        if name == "write_stdin":
            return bool(str(args.get("chars", "")))
        spec = TOOL_REGISTRY.get(name)
        return bool(spec and not spec.read_only and (spec.destructive or spec.open_world))



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
                "elicitation": {"supported": False, "required": False},
            }
        return {
            "ok": True,
            "status": "unsupported",
            "grant_id": None,
            "expires_at": None,
            "elicitation": {"supported": False, "required": False},
            "fallback": {
                "mode": "server_policy",
                "permission_mode": self.permission_mode,
                "granted": False,
                "fail_closed": True,
                "recommended_next_action": "Use an operation already allowed by the current server policy, or change the permission mode in the Electron app. Do not retry permission elicitation unchanged on this client.",
            },
            "error": {
                "code": "ELICITATION_UNSUPPORTED",
                "message": "Permission elicitation is not available for this client; no permission was granted.",
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
