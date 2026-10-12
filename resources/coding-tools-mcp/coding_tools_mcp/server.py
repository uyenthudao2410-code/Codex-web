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
from pathlib import Path
from typing import Any

from . import __version__  # noqa: F401  # composition-root namespace
from .budget_control import BudgetDeadline, RetryPolicy  # noqa: F401  # composition-root namespace
from .envutils import ENV_PREFIX, truthy_env  # noqa: F401  # composition-root namespace
from .errors import JsonRpcError, ToolFailure, normalize_exception_group  # noqa: F401  # composition-root namespace
from .endpoint_identity import (  # noqa: F401  # composition-root namespace
    ENDPOINT_META_KEY,
    ENDPOINT_ROUTING_INSTRUCTIONS_META_KEY,
    endpoint_identity_payload,
    endpoint_routing_instructions,
    endpoint_server_title,
)
from .execution_resources import (  # noqa: F401  # composition-root namespace
    ExecutionResourceError,
    ExecutionResourceGovernor,
)
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
from .secret_broker import (  # noqa: F401  # composition-root namespace
    AUTH_HANDLE_ENV,
    MCP_AUTH_HANDLE,
    SecretBroker,
    SecretBrokerError,
)
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
from .task_state import ContextualTaskStateStore, TaskStateStore  # noqa: F401  # composition-root namespace
from .workspace_context_registry import WorkspaceContextRegistry  # noqa: F401  # composition-root namespace
from .performance_trace import IDEMPOTENCY_POLICY_EPOCH, PerformanceTraceStore, build_tool_invocation_context, utc_now  # noqa: F401  # composition-root namespace
from .orchestration_control import OrchestrationControl, OrchestrationControlError, RunContext, normalize_failure_class  # noqa: F401  # composition-root namespace
from .orchestration_ledger import OrchestrationLedger, fingerprint_paths  # noqa: F401  # composition-root namespace
from .continuation_driver import ContinuationDriverMixin  # noqa: F401  # composition-root namespace
from .run_continuation import RunContinuationMixin  # noqa: F401  # composition-root namespace
from .continuation_consent_http import ContinuationConsentChallengeStore  # noqa: F401  # composition-root namespace
from .coordination_status import CoordinationStatusMixin  # noqa: F401  # composition-root namespace
from .orchestration_report import OrchestrationReport  # noqa: F401  # composition-root namespace
from .projection_rebuild import reconcile_task_orchestration_projection  # noqa: F401  # composition-root namespace
from .operator_report import build_command_completion_report, build_orchestration_runtime_result  # noqa: F401  # composition-root namespace
from .proof_ledger import ProofLedger  # noqa: F401  # composition-root namespace
from .telemetry import SessionTelemetry  # noqa: F401  # composition-root namespace
from .textutils import DEFAULT_MAX_LINES, TextTruncation, truncate_text_head  # noqa: F401  # composition-root namespace
from .tool_results import make_tool_result, model_visible_text_bytes, model_visible_text_chars  # noqa: F401  # composition-root namespace
from .tool_contract import (  # noqa: F401  # composition-root namespace
    AGENT_EXECUTION_ROUTES,
    SMART_COMPAT_TOOL_NAMES,
    SMART_TOOL_PROFILE,
    TOOL_CONTRACT_RUNTIME,
    TOOL_CONTRACT_SCHEMA_VERSION,
    TOOL_MODE_ALLOWLISTS,
    TOOL_REGISTRY,
    ToolSpec,
    smart_tool_contract_compatible_predecessors,
    tool_metadata_contract,
)
from .usage_events import usage_event_from_provider_delegation  # noqa: F401  # composition-root namespace
from .usage_reservations import UsageReservationError, UsageReservationStore  # noqa: F401  # composition-root namespace
from .provider_traffic import ProviderTrafficGovernor  # noqa: F401  # composition-root namespace
from .provider_runtime import HUB_PROVIDER_TELEMETRY_STATES, USAGE_RESERVATION_TERMINAL_GRACE_MS, ProviderRuntimeMixin  # noqa: F401  # composition-root namespace
from .provider_telemetry import HUB_PROVIDER_TELEMETRY_STATUSES, normalize_provider_telemetry  # noqa: F401  # compatibility re-export
from .runtime_activity import RuntimeActivityMixin  # noqa: F401  # composition-root namespace
from .connector_attestation import CONNECTOR_ATTESTATION_ENV  # noqa: F401  # composition-root namespace
from .workspace_scope import Workspace, _PrimaryLedgerCompatibilityView, configured_authorized_roots  # noqa: F401  # compatibility re-export
from .runtime_background import BACKGROUND_BUDGET_POLL_SECONDS, BACKGROUND_BUDGET_TERMINAL_GRACE_SECONDS, MAX_BACKGROUND_OPERATIONS, BackgroundOperationsMixin  # noqa: F401  # compatibility re-export
from .runtime_cache import RuntimeCacheMixin  # noqa: F401  # composition-root namespace
from .runtime_behavior_identity import RuntimeBehaviorIdentityMixin  # noqa: F401  # composition-root namespace
from .runtime_stateless_context import RuntimeStatelessContextMixin  # noqa: F401  # composition-root namespace

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
from .transport_http import STATELESS_HTTP_2026_ENV, _decode_mcp_name_header, _first_form_value, _first_header_value, _forwarded_header_param, _http_base_for_bind_host, _request_mcp_name, _safe_external_host, new_workspace_session_id, stateless_http_2026_enabled  # noqa: F401  # compatibility re-export



PROCESS_INSTANCE_ID = secrets.token_urlsafe(12)
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
IDEMPOTENCY_RESULT_MAX_BYTES = 256 * 1024
TRACE_MAX_PAYLOAD_BYTES = 16 * 1024
AUTO_IDEMPOTENCY_KEY_PREFIX = "auto-v1:"
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





_FAST_TOOL_CACHE: dict[str, tuple[float, int, dict[str, Any]]] = {}
_FAST_TOOL_CACHE_LOCK = threading.Lock()
_WORKSPACE_CACHE_GENERATION: dict[str, int] = {}
_WORKSPACE_PREHEAT_STARTED: set[str] = set()















class Runtime(
    FileToolsMixin, ExecToolsMixin, GitToolsMixin, SessionControlMixin, DocumentToolsMixin, TaskStateToolsMixin,
    AgentCandidateMixin, ContextToolsMixin, ContinuationDriverMixin, RunContinuationMixin, AgentWorkflowMixin, CoordinationStatusMixin, CoordinationMixin, RuntimeActivityMixin,
    BackgroundOperationsMixin, RuntimeCacheMixin, RuntimeBehaviorIdentityMixin, RuntimeStatelessContextMixin,
    ProviderRuntimeMixin,
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
        secret_broker: SecretBroker | None = None,
    ) -> None:
        self.authorized_roots = configured_authorized_roots()
        self.workspace = Workspace(workspace, self.authorized_roots)
        self.workspace_context_registry = WorkspaceContextRegistry(self.workspace.root)
        self._workspace_component_lock = threading.RLock()
        self._orchestration_workspace_identity_cache: dict[str, dict[str, Any]] = {}
        self._orchestration_ledgers: dict[str, OrchestrationLedger] = {}
        self._orchestration_controls: dict[str, OrchestrationControl] = {}
        self._execution_resource_governors: dict[str, ExecutionResourceGovernor] = {}
        self._proof_ledgers: dict[str, ProofLedger] = {}
        self._orchestration_reports: dict[str, OrchestrationReport] = {}
        self._primary_ledger_view: _PrimaryLedgerCompatibilityView | None = None
        self._task_context_workspace_ids: dict[str, str] = {}
        self._task_context_workspace_lock = threading.RLock()
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
        contract_sha256 = hashlib.sha256(contract_bytes).hexdigest()
        self.tool_contract = {
            "schema_version": TOOL_CONTRACT_SCHEMA_VERSION,
            "profile": SMART_TOOL_PROFILE if self.tool_mode == "smart" else self.tool_mode,
            "sha256": contract_sha256,
            "tool_count": len(self._exposed_tool_names),
            "compatible_predecessor_sha256": (
                smart_tool_contract_compatible_predecessors(contract_sha256)
                if self.tool_mode == "smart"
                else []
            ),
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
        # The managed Electron Tunnel injects one lifecycle-bound HMAC
        # attestation over the exact connector/runtime tuple. Keep the secret
        # process-local and never expose it through health, receipts, or tool
        # output.
        self.connector_attestation_secret = str(
            os.environ.get(CONNECTOR_ATTESTATION_ENV) or ""
        ).strip() or None
        self.secret_broker = secret_broker or SecretBroker()
        self.oauth_config = oauth_config
        self.server_instance_id = secrets.token_urlsafe(12)
        self.process_instance_id = PROCESS_INSTANCE_ID
        self.run_continuation_consent_challenges = ContinuationConsentChallengeStore()
        self.run_continuation_consent_http_origin = ""
        self._set_runtime_dir(runtime_dir_for_workspace(self.workspace.root, self.server_instance_id))
        self.fallback_runtime_dir = fallback_runtime_dir_for_workspace(self.workspace.root, self.server_instance_id)
        self.default_cwd = self.workspace.root
        self.sessions: dict[str, ExecSession] = {}
        self.output_sessions: dict[str, ExecSession] = {}
        self.sessions_lock = threading.Lock()
        self.supervisor_request_lock = threading.Lock()
        self.activation_lock = threading.RLock()
        self._initialize_activation_admission()
        self._initialize_projection_rebuild()
        self.activation_fence: dict[str, Any] | None = None
        self.active_tool_calls = 0
        self.session_principals: dict[str, str] = {}
        self.principal_active_counts: dict[str, int] = {}
        self.legacy_session_alias_uses = 0
        self.starting_sessions = 0
        self._closed = False
        self.http_session_id = new_workspace_session_id(self.workspace.root, self.auth_token)
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
        self.tool_discovery_lock = threading.Lock()
        self.tool_discovery_receipts: dict[str, dict[str, Any]] = {}
        self.tool_contact_lock = threading.Lock()
        self.tool_contact_receipts: dict[str, dict[str, Any]] = {}
        self.controller_usage_envelope_receipts: dict[str, dict[str, Any]] = {}
        self.activation_bootstrap_lock = threading.Lock()
        self.activation_bootstrap_receipts: dict[str, dict[str, Any]] = {}
        # Background operations are process-scoped rather than HTTP-session-scoped.
        # A reconnect in the same MCP process must be able to poll the original
        # Event/result instead of falsely declaring it orphaned.
        self.background_operations = PROCESS_BACKGROUND_OPERATIONS
        self.background_operations_lock = PROCESS_BACKGROUND_OPERATIONS_LOCK
        self.initialized = False
        self.telemetry = SessionTelemetry(permission_mode=self.permission_mode, transport=transport)
        self.task_state = ContextualTaskStateStore(
            self.workspace.root,
            self._current_task_scope_id,
            self._current_task_workspace_root,
            lambda: self.workspace.authorized_roots,
        )
        self.performance_trace = PerformanceTraceStore(self.workspace.root)
        self._orchestration_ledger_primary = OrchestrationLedger(self.workspace.root)
        self._orchestration_ledgers[str(self.workspace.root)] = self._orchestration_ledger_primary
        self._execution_resource_governor_primary = ExecutionResourceGovernor(
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
        # Lifecycle terminalization is an explicit exact-ID maintenance action.
        # Runtime construction must neither expire leases nor invoke the legacy
        # bulk reconciler merely because a controller process restarted.
        self.reconciled_stale_orchestration_runs: list[str] = []
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
        self._execution_resource_governors[str(self.workspace.root)] = self._execution_resource_governor_primary
        self._orchestration_control_primary = self._new_orchestration_control(self.workspace.root)
        self._orchestration_controls[str(self.workspace.root)] = self._orchestration_control_primary
        self.reconciled_task_orchestration = self._reconcile_task_orchestration_projection()
        if self.activation_epoch_id:
            self._projection_rebuild_census(reconciliation_already_performed=True)
        self._proof_ledger_primary = ProofLedger(self.workspace.root, self.orchestration_ledger)
        self._proof_ledgers[str(self.workspace.root)] = self._proof_ledger_primary
        self._orchestration_report_primary = OrchestrationReport(self.workspace.root, self.orchestration_ledger)
        self._orchestration_reports[str(self.workspace.root)] = self._orchestration_report_primary
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
            secret_broker=self.secret_broker,
        )
        self._tool_handlers = {name: getattr(self, name) for name in TOOL_REGISTRY}

    def _set_runtime_dir(self, runtime_dir: Path) -> None:
        self.runtime_dir = runtime_dir
        self.home_dir = self.runtime_dir / "home"
        self.tmp_dir = self.runtime_dir / "tmp"
        self.cache_dir = self.runtime_dir / "cache"

    def _current_request_workspace_root(self) -> Path:
        raw = getattr(self.request_context, "workspace_root", None)
        if raw:
            try:
                candidate = Path(raw).resolve(strict=False)
                if candidate.is_dir() and self.workspace._is_allowed(candidate):
                    return candidate
            except (OSError, RuntimeError, TypeError, ValueError):
                pass
        binding_id = self._current_workspace_binding_id()
        if binding_id:
            root = self._bound_task_context_workspace(binding_id)
            if root is not None:
                return root
        return self.workspace.root

    def _current_task_workspace_root(self) -> Path:
        return self._current_request_workspace_root()

    def _component_root_key(self, root: Path | None = None) -> str:
        return str((root or self._current_request_workspace_root()).resolve(strict=False))

    @property
    def orchestration_ledger(self) -> OrchestrationLedger:
        root = self._current_request_workspace_root()
        ledger = self._orchestration_ledger_for_root(root)
        if str(root) == str(self.workspace.root) and not getattr(self.request_context, "workspace_root", None):
            if self._primary_ledger_view is None or self._primary_ledger_view._primary is not ledger:
                self._primary_ledger_view = _PrimaryLedgerCompatibilityView(self, ledger)
            return self._primary_ledger_view  # type: ignore[return-value]
        return ledger

    def _orchestration_ledger_for_root(self, root: Path) -> OrchestrationLedger:
        key = self._component_root_key(root)
        with self._workspace_component_lock:
            ledger = self._orchestration_ledgers.get(key)
            if ledger is None:
                ledger = OrchestrationLedger(Path(key))
                self._orchestration_ledgers[key] = ledger
            return ledger

    @property
    def orchestration_control(self) -> OrchestrationControl:
        key = self._component_root_key()
        with self._workspace_component_lock:
            control = self._orchestration_controls.get(key)
            if control is None:
                control = self._new_orchestration_control(Path(key))
                self._orchestration_controls[key] = control
            return control

    @property
    def execution_resource_governor(self) -> ExecutionResourceGovernor:
        return self._execution_resource_governor_for_root(self._current_request_workspace_root())

    def _execution_resource_governor_for_root(self, root: Path) -> ExecutionResourceGovernor:
        key = self._component_root_key(root)
        with self._workspace_component_lock:
            governor = self._execution_resource_governors.get(key)
            if governor is None:
                governor = ExecutionResourceGovernor(
                    Path(key),
                    self._orchestration_ledger_for_root(Path(key)),
                    process_instance_id=self.process_instance_id,
                    runtime_instance_id=self.server_instance_id,
                )
                self._execution_resource_governors[key] = governor
            return governor

    @property
    def proof_ledger(self) -> ProofLedger:
        key = self._component_root_key()
        with self._workspace_component_lock:
            proof = self._proof_ledgers.get(key)
            if proof is None:
                proof = ProofLedger(Path(key), self.orchestration_ledger)
                self._proof_ledgers[key] = proof
            return proof

    @property
    def orchestration_report(self) -> OrchestrationReport:
        key = self._component_root_key()
        with self._workspace_component_lock:
            report = self._orchestration_reports.get(key)
            if report is None:
                report = OrchestrationReport(Path(key), self.orchestration_ledger)
                self._orchestration_reports[key] = report
            return report

    def _new_orchestration_control(self, root: Path | None = None) -> OrchestrationControl:
        scope_root = (root or self._current_request_workspace_root()).resolve(strict=False)
        ledger = self._orchestration_ledger_for_root(scope_root)
        governor = self._execution_resource_governor_for_root(scope_root)
        return OrchestrationControl(
            scope_root,
            ledger,
            on_wave_terminal=lambda ctx, state: governor.teardown_wave(
                ctx.run_id,
                ctx.wave_id,
                reason=f"orchestration_state:{str(state).lower()}",
            ),
            assert_wave_quiescent=governor.assert_wave_quiescent,
        )

    def _reconcile_task_orchestration_projection(self, *, requested_run_id: object = "") -> bool:
        repaired = reconcile_task_orchestration_projection(self, requested_run_id=requested_run_id)
        if repaired:
            self._projection_rebuild_receipt = None
            self._projection_rebuild_failure = {
                "valid": False,
                "code": "UPDATE_INCOMPLETE",
                "reasons": ["PROJECTION_CHANGED_AFTER_RECEIPT", "RECEIPT_MISSING"],
            }
        return repaired

    def close(self) -> None:
        self._opencode_provider.close()
        self._codex_bridge.close()
        with self.sessions_lock:
            if self._closed:
                return
            self._closed = True
            self._activation_admission_changed.set()
            sessions = list(self.sessions.values())
            self.sessions.clear()
            self.output_sessions.clear()
            self.session_principals.clear()
            self.principal_active_counts.clear()
        for session in sessions:
            session.refresh_status()
            if session.process.poll() is None:
                session.sandbox_abort_on_cleanup = True
                terminate_process_group(session.process, signal.SIGTERM)
            if session.process.poll() is not None:
                session.cleanup_sandbox_state()
            if session.managed_job_id and not session.resource_terminal_recorded:
                self.execution_resource_governor.complete(
                    session.managed_job_id,
                    lifecycle_state="runtime_closed",
                    exit_code=session.process.poll(),
                )
                session.resource_terminal_recorded = True
            session.drain_readers()
        sandbox_manager = getattr(self, "_windows_mxc_sandbox_manager", None)
        if sandbox_manager is not None and not sandbox_manager.close():
            sys.stderr.write(
                "Windows Sandbox teardown could not be confirmed; the next exec remains fail-closed.\n"
            )
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
            self.workspace_context_registry = WorkspaceContextRegistry(self.workspace.root)
            with self._task_context_workspace_lock:
                self._task_context_workspace_ids.clear()
            self.http_session_id = new_workspace_session_id(self.workspace.root, self.auth_token)
            self.default_cwd = self.workspace.root
            self._set_runtime_dir(runtime_dir_for_workspace(self.workspace.root, self.server_instance_id))
            self.fallback_runtime_dir = fallback_runtime_dir_for_workspace(self.workspace.root, self.server_instance_id)
            self.project_context = load_project_context(self.workspace.root)
            if not self._semantic_localizer_injected:
                self.semantic_localizer = semantic_localizer_from_env(self.workspace.root)
            self.task_state = ContextualTaskStateStore(
                self.workspace.root,
                self._current_task_scope_id,
                self._current_task_workspace_root,
                lambda: self.workspace.authorized_roots,
            )
            self.performance_trace = PerformanceTraceStore(self.workspace.root)
            self._orchestration_ledger_primary = OrchestrationLedger(self.workspace.root)
            self._orchestration_ledgers[str(self.workspace.root)] = self._orchestration_ledger_primary
            self._execution_resource_governor_primary = ExecutionResourceGovernor(
                self.workspace.root,
                self.orchestration_ledger,
                process_instance_id=self.process_instance_id,
                runtime_instance_id=self.server_instance_id,
            )
            self._execution_resource_governors[str(self.workspace.root)] = self._execution_resource_governor_primary
            self.orphaned_background_operations = self.orchestration_ledger.mark_orphaned_background_operations(
                current_server_instance_id=self.process_instance_id
            )
            self.orphaned_idempotency_records = self.orchestration_ledger.mark_orphaned_idempotency(
                current_process_instance_id=self.process_instance_id
            )
            # Workspace switching is not lifecycle-maintenance authority.  Keep
            # the current exact-ID reconciliation receipt scoped to its prior
            # workspace and never invoke the legacy bulk reconciler here.
            self.reconciled_stale_orchestration_runs = []
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
            self._orchestration_control_primary = self._new_orchestration_control(self.workspace.root)
            self._orchestration_controls[str(self.workspace.root)] = self._orchestration_control_primary
            self.reconciled_task_orchestration = self._reconcile_task_orchestration_projection()
            if self.activation_epoch_id:
                self._projection_rebuild_census(reconciliation_already_performed=True)
            self._proof_ledger_primary = ProofLedger(self.workspace.root, self.orchestration_ledger)
            self._proof_ledgers[str(self.workspace.root)] = self._proof_ledger_primary
            self._orchestration_report_primary = OrchestrationReport(self.workspace.root, self.orchestration_ledger)
            self._orchestration_reports[str(self.workspace.root)] = self._orchestration_report_primary
            self._opencode_provider = OpenCodeProviderAdapter(
                lambda: self.workspace.root,
                on_terminal=self._on_opencode_provider_terminal,
                resource_governor=self.execution_resource_governor,
            )
            self.provider_traffic = ProviderTrafficGovernor.from_env()
            self._codex_bridge = CodexAppServerBridge(
                lambda: self.workspace.root,
                resource_governor=self.execution_resource_governor,
                secret_broker=self.secret_broker,
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
        endpoint = endpoint_identity_payload(self)
        routing_instructions = endpoint_routing_instructions(endpoint)
        return {
            "protocolVersion": self.protocol_version,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {
                "name": SERVER_NAME,
                "title": endpoint_server_title(endpoint),
                "version": __version__,
            },
            "instructions": (
                routing_instructions
                + "\n\n"
                + self.project_context.server_instructions()
            ),
            "_meta": {
                ENDPOINT_META_KEY: endpoint,
                ENDPOINT_ROUTING_INSTRUCTIONS_META_KEY: routing_instructions,
            },
        }

    def list_tools(self) -> dict[str, Any]:
        self._record_tool_discovery()
        return self._tools_list_payload

    def _current_hub_client(self) -> dict[str, Any] | None:
        value = getattr(self.request_context, "hub_client", None)
        return value if isinstance(value, dict) and value.get("client_id") else None

    def _current_stateless_task_context_id(self) -> str:
        return str(getattr(self.request_context, "stateless_task_context_id", "") or "").strip()

    def _current_workspace_binding_id(self) -> str:
        """Return the durable key used to bind an execution to a workspace."""
        stateless_task_context_id = self._current_stateless_task_context_id()
        if stateless_task_context_id:
            return stateless_task_context_id
        identity = self._current_hub_client()
        if identity is not None and str(identity.get("client_type") or "") == "chatweb":
            execution_context_id = str(identity.get("execution_context_id") or "").strip()
            if execution_context_id:
                return execution_context_id
        return ""

    def _current_task_scope_id(self) -> str:
        """Return the task-state namespace for the current execution.

        The MCP-2026 opaque context is the durable workspace binding key, but
        task-state storage must retain the modern namespace marker so it never
        adopts a legacy/global task projection during first use.
        """
        stateless_task_context_id = self._current_stateless_task_context_id()
        if stateless_task_context_id:
            return f"mcp2026:{stateless_task_context_id}"
        return self._current_workspace_binding_id()

    def _bind_task_context_workspace(self, workspace_id: str, *, scope_id: str | None = None) -> None:
        scope = str(scope_id if scope_id is not None else self._current_workspace_binding_id()).strip()
        if not scope:
            return
        target = str(workspace_id or "").strip()
        if not target:
            return
        root = self._workspace_root_for_identity(target)
        if root is None:
            raise ToolFailure(
                "WORKSPACE_SCOPE_INCONSISTENT",
                "The resolved workspace identity has no authorized canonical root.",
                category="security",
                retryable=False,
                details={"workspace_id": target},
            )
        with self._task_context_workspace_lock:
            existing = self._task_context_workspace_ids.get(scope)
            if existing and existing != target:
                raise ToolFailure(
                    "TASK_CONTEXT_WORKSPACE_MISMATCH",
                    "The task context is already bound to a different workspace.",
                    category="security",
                    retryable=False,
                    details={"task_context_id": scope, "expected_workspace_id": existing, "received_workspace_id": target},
                )
            registered = self.workspace_context_registry.lookup(scope)
            if isinstance(registered, dict) and registered.get("legacy") is True:
                raise ToolFailure(
                    "UNKNOWN_LEGACY_WORKSPACE",
                    "The persisted task context has no trustworthy workspace identity.",
                    category="security",
                    retryable=False,
                    details={"task_context_id": scope, "reason": str(registered.get("reason") or "legacy_workspace_mapping")},
                )
            if isinstance(registered, dict):
                registered_workspace = str(registered.get("workspace_id") or "").strip()
                registered_root = str(registered.get("canonical_root") or "").strip()
                if registered_workspace and registered_workspace != target:
                    raise ToolFailure(
                        "TASK_CONTEXT_WORKSPACE_MISMATCH",
                        "The task context is already bound to a different workspace.",
                        category="security",
                        retryable=False,
                        details={"task_context_id": scope, "expected_workspace_id": registered_workspace, "received_workspace_id": target},
                    )
                if registered_root and Path(registered_root).resolve(strict=False) != root.resolve(strict=False):
                    raise ToolFailure(
                        "WORKSPACE_SCOPE_INCONSISTENT",
                        "The persisted task context root does not match its workspace identity.",
                        category="security",
                        retryable=False,
                        details={"task_context_id": scope, "workspace_id": target},
                    )
            else:
                try:
                    self.workspace_context_registry.bind(
                        scope,
                        workspace_id=target,
                        canonical_root=root,
                    )
                except ValueError as exc:
                    raise ToolFailure(
                        "TASK_CONTEXT_WORKSPACE_MISMATCH",
                        "The task context is already bound to a different workspace.",
                        category="security",
                        retryable=False,
                        details={"task_context_id": scope},
                    ) from exc
            self._task_context_workspace_ids[scope] = target

    def _bound_task_context_workspace(self, scope_id: object) -> Path | None:
        scope = str(scope_id or "").strip()
        if not scope:
            return None
        with self._task_context_workspace_lock:
            root_id = self._task_context_workspace_ids.get(scope, "")
        if root_id:
            root = self._workspace_root_for_identity(root_id)
            if root is not None:
                return root
        registered = self.workspace_context_registry.lookup(scope)
        if registered is None:
            return None
        if registered.get("legacy") is True:
            raise ToolFailure(
                "UNKNOWN_LEGACY_WORKSPACE",
                "The persisted task context has no trustworthy workspace identity.",
                category="security",
                retryable=False,
                details={"task_context_id": scope, "reason": str(registered.get("reason") or "legacy_workspace_mapping")},
            )
        workspace_id = str(registered.get("workspace_id") or "").strip()
        canonical_root = str(registered.get("canonical_root") or "").strip()
        if not workspace_id or not canonical_root:
            raise ToolFailure(
                "UNKNOWN_LEGACY_WORKSPACE",
                "The persisted task context is missing workspace identity evidence.",
                category="security",
                retryable=False,
                details={"task_context_id": scope},
            )
        try:
            root = Path(canonical_root).resolve(strict=True)
        except (OSError, RuntimeError):
            raise ToolFailure(
                "UNKNOWN_LEGACY_WORKSPACE",
                "The persisted task context root no longer exists.",
                category="security",
                retryable=False,
                details={"task_context_id": scope, "workspace_id": workspace_id},
            ) from None
        if not self.workspace._is_allowed(root):
            raise ToolFailure(
                "WORKSPACE_NOT_AUTHORIZED",
                "The persisted task context workspace is not authorized by the current Runtime.",
                category="security",
                retryable=False,
                details={"task_context_id": scope, "workspace_id": workspace_id},
            )
        actual_workspace_id = self._content_free_workspace_root_id(root)
        if actual_workspace_id != workspace_id:
            raise ToolFailure(
                "WORKSPACE_SCOPE_INCONSISTENT",
                "The persisted task context workspace identity does not match its canonical root.",
                category="security",
                retryable=False,
                details={"task_context_id": scope, "workspace_id": workspace_id},
            )
        with self._task_context_workspace_lock:
            self._task_context_workspace_ids[scope] = workspace_id
        return root

    def _workspace_identity_for_request(self, raw_path: object = ".") -> tuple[ResolvedPath, Path, dict[str, Any]]:
        requested = str(raw_path or ".")
        binding_id = self._current_workspace_binding_id()
        bound_root: Path | None = None
        if requested in {"", "."} and binding_id:
            bound_root = self._bound_task_context_workspace(binding_id)
        resolved = self._resolve_authorized_execution_scope(
            str(bound_root) if bound_root is not None else requested,
            field="path",
        )
        scope_root = self.workspace._containing_root(resolved.path) or self.workspace.root
        identity = self._workspace_scope_identity(resolved)
        # Bind the opaque execution context, not the workspace identity, to the
        # resolved root.  Workspace IDs are values in the binding; using one as
        # the registry key would let a caller reuse a task context across
        # authorized roots and silently rebind its task state.
        self._bind_task_context_workspace(
            str(identity.get("workspace_id") or ""),
            scope_id=binding_id,
        )
        self.request_context.workspace_root = str(scope_root)
        return resolved, scope_root, identity

    @staticmethod
    def _task_control_lifecycle_read_only(args: dict[str, Any]) -> bool:
        """Return whether task_control may observe without changing task lifecycle.

        Tool-level annotations are deliberately conservative because
        ``task_control`` contains both EOCL mutations and read-only inspection.
        Keep that distinction here so a rejected cross-workspace inspection can
        never write a failure, REPLAN, or completion projection in whichever
        workspace happened to be selected for the request.
        """
        action = str(args.get("action", "get") or "get").strip().lower()
        if action in {"get", "history", "operation", "audit", "events", "messages"}:
            return True
        if action == "lane":
            return str(args.get("lane_action", "list") or "list").strip().lower() in {"list", "observe"}
        if action == "handoff":
            return str(args.get("handoff_action", "get") or "get").strip().lower() == "get"
        if action == "p5":
            experiment = args.get("p5_experiment")
            return isinstance(experiment, dict) and str(experiment.get("operation") or "status").strip().lower() == "status"
        if action == "problem":
            event = args.get("problem_event")
            return isinstance(event, dict) and str(event.get("operation") or "get").strip().lower() == "get"
        return False

    def _should_record_task_tool_result(self, name: str, args: dict[str, Any]) -> bool:
        spec = TOOL_REGISTRY.get(name)
        if spec is not None and spec.read_only is True:
            return False
        return not (name == "task_control" and self._task_control_lifecycle_read_only(args))

    def _set_request_workspace_scope(self, name: str, args: dict[str, Any]) -> None:
        has_multiple_roots = len(self.workspace.authorized_roots) > 1
        binding_id = self._current_workspace_binding_id()
        bound_root: Path | None = None
        if binding_id:
            bound_root = self._bound_task_context_workspace(binding_id)
        mutation = (
            name in {"agent_workflow", "exec_command", "document_workflow", "apply_changes_and_verify"}
            or (name == "task_control" and not self._task_control_lifecycle_read_only(args))
        )
        path_supplied = any(
            key in args and str(args.get(key) or "").strip() not in {"", "."}
            for key in ("path", "workdir")
        )
        if name == "workspace_context" and not path_supplied and bound_root is None:
            # The caller relies on the active workspace binding.  When the
            # bound drive is gone there is no safe fallback directory.
            self._require_active_workspace_binding_available()
        run_bound_root: Path | None = None
        if name == "task_control" and mutation and bound_root is None and not path_supplied:
            requested_run_id = str(args.get("run_id") or "").strip()
            if requested_run_id:
                # A run ID is an allowed workspace authority for task_control,
                # but only when its ledger location resolves to one configured
                # canonical root.  This keeps a legacy client from falling
                # back to the primary workspace merely because it lacks a
                # stateless task-context handle.
                run_bound_root = self._known_run_workspace(requested_run_id)
        if has_multiple_roots and mutation and bound_root is None and not path_supplied and name != "workspace_context":
            if run_bound_root is not None:
                self.request_context.workspace_root = str(run_bound_root)
                return
            required_fields = (
                ["workdir", "task_context_id"]
                if name == "exec_command"
                else ["task_context_id", "run_id"]
                if name == "task_control"
                else ["path", "task_context_id"]
            )
            raise ToolFailure(
                "WORKSPACE_TARGET_REQUIRED",
                "Mutating operations must name a workspace when multiple authorized roots are available.",
                category="security",
                retryable=False,
                details={
                    "authorized_workspace_count": len(self.workspace.authorized_roots),
                    "required_fields": required_fields,
                },
            )
        raw_path: object | None = None
        if name == "workspace_context":
            raw_path = args.get("path", ".")
        elif name == "agent_workflow":
            raw_path = args.get("path", ".")
        elif name == "exec_command":
            raw_path = args.get("workdir", args.get("path", "."))
        elif name in {"document_workflow", "prepare_coding_context", "apply_changes_and_verify"}:
            raw_path = args.get("path", ".")
        else:
            if binding_id:
                if bound_root is not None:
                    self.request_context.workspace_root = str(bound_root)
                    return
        if raw_path is None:
            return
        _resolved, scope_root, _identity = self._workspace_identity_for_request(raw_path)
        self.request_context.workspace_root = str(scope_root)

    @staticmethod
    def _hub_client_record_id(identity: dict[str, Any]) -> str:
        client_id = str(identity.get("client_id") or "").strip()
        execution_context_id = str(identity.get("execution_context_id") or "").strip()
        if str(identity.get("client_type") or "") == "chatweb" and execution_context_id:
            return f"{client_id}:{execution_context_id[:16]}"
        return client_id

    def _maybe_reconcile_stale_orchestration(self, *, force: bool = False) -> list[str]:
        """Preserve lifecycle evidence until the exact-ID authority is invoked.

        A heartbeat/UI poll is not sufficient authority to expire a lease or
        terminalize a threshold-sensitive run.  Gate 0 maintenance therefore
        uses ``reconcile_exact_stale_run`` after a fresh immutable census and a
        stopped-runtime fence; this compatibility hook intentionally performs
        no ledger mutation.
        """
        _ = force
        return []

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
        task_id = str(state.get("task_id") or "").strip()
        if task_id:
            active = self.orchestration_ledger.current_active_run(task_id=task_id)
            if active:
                return str(active.get("run_id") or "")
        if self.task_state.is_scoped():
            return ""
        active = self.orchestration_ledger.current_active_run()
        return str(active.get("run_id") or "") if active else ""

    def _touch_hub_client(self, identity: dict[str, Any]) -> dict[str, Any]:
        logical_client_id = str(identity.get("client_id") or "").strip()
        client_id = self._hub_client_record_id(identity)
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
            metadata={
                "logical_client_id": logical_client_id,
                "execution_context_id": str(identity.get("execution_context_id") or "")[:64],
            },
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
        auto_resume = None
        if (
            run
            and run.get("status") == "active"
            and client_type == "chatweb"
            and controller
            and controller.get("status") == "active"
            and controller.get("owner_client_id") == client_id
        ):
            auto_resume = self._run_continuation_try_auto_resume(
                run_id=run_id,
                trigger="reconnect",
                marker=str(identity.get("session_instance") or identity.get("execution_context_id") or client_id),
            )
        return {"client": client, "controller": controller, "run_id": run_id, "auto_resume": auto_resume}

    def _require_hub_controller(self, run_id: str) -> dict[str, Any] | None:
        identity = self._current_hub_client()
        if identity is None:
            return None
        self._continuity_assert_run_controller(run_id)
        self._touch_hub_client(identity)
        controller = self.orchestration_ledger.get_controller_lease(run_id)
        client_id = self._hub_client_record_id(identity)
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

    def _claim_hub_controller_for_run(self, run_id: str) -> dict[str, Any] | None:
        identity = self._current_hub_client()
        if identity is None or str(identity.get("client_type") or "") != "chatweb":
            return None
        self._continuity_assert_run_controller(run_id)
        client_id = self._hub_client_record_id(identity)
        current = self.orchestration_ledger.get_controller_lease(run_id)
        if current and current.get("status") == "active" and current.get("owner_client_id") != client_id:
            return current
        claimed = self.orchestration_ledger.acquire_controller_lease(
            run_id=run_id,
            owner_client_id=client_id,
            lease_id=f"client:{client_id}",
            ttl_seconds=HUB_CONTROLLER_LEASE_SECONDS,
        )
        return claimed if claimed.get("acquired") else self.orchestration_ledger.get_controller_lease(run_id)

    def exposed_tool_names(self) -> list[str]:
        return list(self._exposed_tool_names)

    def auth_enabled(self) -> bool:
        return self.auth_token is not None or self.oauth_config is not None

    def oauth_enabled(self) -> bool:
        return self.oauth_config is not None

    def default_cwd_display(self) -> str:
        return normalize_rel_display(self._request_default_cwd(), self.workspace.root)

    def _request_default_cwd(self) -> Path:
        """Select the default directory inside the request's resolved workspace.

        A process still has one legacy ``default_cwd`` for unscoped clients.
        A stateless task context is stronger: relative paths in that request
        must resolve below its bound root, never below the primary runtime root.
        """
        root = self._current_request_workspace_root()
        try:
            default = self.default_cwd.resolve(strict=False)
        except (OSError, RuntimeError):
            return root
        return default if self.workspace._containing_root(default) == root else root

    def resolve_existing(self, raw_path: str = ".") -> ResolvedPath:
        return self.workspace.resolve_existing_at(self._request_default_cwd(), raw_path)

    def _resolve_authorized_execution_scope(self, raw_path: object, *, field: str) -> ResolvedPath:
        """Resolve a tool target against the primary workspace plus explicit authorized roots."""
        raw = str(raw_path or ".")
        try:
            return self.resolve_existing(raw)
        except ToolFailure as exc:
            if exc.code == "PATH_OUTSIDE_WORKSPACE":
                raise ToolFailure(
                    "STALE_WORKSPACE_CONTEXT",
                    f"{field} is outside the configured workspace and authorized roots.",
                    category="security",
                    retryable=False,
                    details={
                        "field": field,
                        "workspace": str(self.workspace.root),
                        "authorized_roots": [
                            str(item)
                            for item in self.workspace.authorized_roots
                            if item != self.workspace.root
                        ],
                        "received": raw,
                    },
                ) from exc
            raise

    @staticmethod
    def _content_free_workspace_root_id(path: Path) -> str:
        normalized = os.path.normcase(os.path.normpath(str(path.resolve(strict=False))))
        return hashlib.sha256(
            ("coding-tools-workspace-root-v1\0" + normalized).encode("utf-8", errors="replace")
        ).hexdigest()

    def _workspace_scope_identity(self, resolved: ResolvedPath) -> dict[str, Any]:
        scope_root = self.workspace._containing_root(resolved.path) or self.workspace.root
        root_id = self._content_free_workspace_root_id(scope_root)
        # A workspace identity belongs to the canonical root selected by the
        # request, not to the Runtime's primary root.  The latter caused an
        # authorized project to inherit the primary project's task/run scope.
        workspace_id = root_id
        requested_path_id = hashlib.sha256(
            ("coding-tools-requested-path-v1\0" + os.path.normcase(str(resolved.path))).encode(
                "utf-8", errors="replace"
            )
        ).hexdigest()
        return {
            "schema_version": 1,
            "content_free": True,
            "workspace_id": workspace_id,
            "session_workspace_id": workspace_id,
            "root_id": root_id,
            "requested_path_id": requested_path_id,
            "scope_kind": "primary" if scope_root == self.workspace.root else "authorized",
            "scope_matches_session_workspace": root_id == workspace_id,
            "workspace_generation": int(self.workspace_generation),
        }

    def _workspace_root_for_identity(self, root_id: object) -> Path | None:
        expected = str(root_id or "").strip()
        if not expected:
            return None
        for root in self.workspace.authorized_roots:
            if self._content_free_workspace_root_id(root) == expected:
                return root
        return None

    def _known_run_workspace(self, run_id: object) -> Path | None:
        expected = str(run_id or "").strip()
        if not expected:
            return None
        current_root = self._current_request_workspace_root()
        current = self._orchestration_ledger_for_root(current_root).get_run(expected)
        if isinstance(current, dict):
            return current_root
        # A stateless/reconnected request may arrive before the authorized
        # workspace's ledger has been touched in this Runtime generation.  Do
        # not treat that as evidence that the run is unknown: lazily inspect
        # every configured canonical root so task_control cannot fall back to
        # the primary workspace state for a run belonging elsewhere.
        roots: list[Path] = [self.workspace.root, *self.workspace.authorized_roots]
        with self._workspace_component_lock:
            roots.extend(Path(key) for key in self._orchestration_ledgers)
        seen: set[str] = set()
        for root in roots:
            canonical = root.resolve(strict=False)
            key = str(canonical)
            if key in seen or canonical == current_root.resolve(strict=False):
                continue
            seen.add(key)
            ledger = self._orchestration_ledger_for_root(canonical)
            if isinstance(ledger.get_run(expected), dict):
                return canonical
        return None

    def _assert_task_control_workspace(self, run_id: object) -> None:
        expected_root = self._known_run_workspace(run_id)
        if expected_root is None:
            return
        current_root = self._current_request_workspace_root()
        if expected_root.resolve(strict=False) != current_root.resolve(strict=False):
            raise ToolFailure(
                "RUN_WORKSPACE_MISMATCH",
                "The requested orchestration run belongs to a different workspace.",
                category="security",
                retryable=False,
                details={
                    "run_id": str(run_id),
                    "expected_workspace": str(expected_root),
                    "received_workspace": str(current_root),
                },
            )

    def _assert_orchestration_workspace_scope(self, identity: dict[str, Any], *, run_id: object = "") -> None:
        owner_run = str(run_id or "").strip()
        if not owner_run:
            state = self.task_state.get()
            projection = state.get("orchestration") if isinstance(state.get("orchestration"), dict) else {}
            owner_run = str(projection.get("run_id") or "").strip()
        if not owner_run:
            return
        run = self.orchestration_ledger.get_run(owner_run)
        if not isinstance(run, dict):
            self._assert_task_control_workspace(owner_run)
            return
        if str(run.get("status") or "") != "active":
            return
        metadata = run.get("metadata") if isinstance(run.get("metadata"), dict) else {}
        expected = metadata.get("workspace_identity") if isinstance(metadata.get("workspace_identity"), dict) else {}
        expected_root = str(expected.get("root_id") or "").strip()
        expected_workspace = str(expected.get("workspace_id") or "").strip()
        actual_root = str(identity.get("root_id") or "").strip()
        actual_workspace = str(identity.get("workspace_id") or "").strip()
        if (
            (expected_root and actual_root and expected_root != actual_root)
            or (expected_workspace and actual_workspace and expected_workspace != actual_workspace)
        ):
            raise ToolFailure(
                "ORCHESTRATION_WORKSPACE_MISMATCH",
                "The requested project root does not match the active orchestration run.",
                category="security",
                retryable=False,
                details={
                    "run_id": owner_run,
                    "expected_root_id": expected_root,
                    "received_root_id": actual_root,
                    "content_free": True,
                },
            )

    def _preflight_tool_workspace_scope(self, name: str, args: dict[str, Any]) -> None:
        if name == "agent_workflow":
            path_value = args.get("path", ".")
            path_scope = self._resolve_authorized_execution_scope(path_value, field="path")
            path_identity = self._workspace_scope_identity(path_scope)
            if "workdir" in args:
                workdir_scope = self._resolve_authorized_execution_scope(args.get("workdir", path_value), field="workdir")
                workdir_identity = self._workspace_scope_identity(workdir_scope)
                if workdir_identity["root_id"] != path_identity["root_id"]:
                    raise ToolFailure(
                        "ORCHESTRATION_WORKSPACE_MISMATCH",
                        "agent_workflow path and workdir resolve to different authorized project roots.",
                        category="security",
                        retryable=False,
                        details={"content_free": True},
                    )
            self._assert_orchestration_workspace_scope(path_identity)
            return
        if name == "exec_command":
            workdir_value = args.get("workdir", args.get("cwd", "."))
            workdir_scope = self._resolve_authorized_execution_scope(workdir_value, field="workdir")
            self._assert_orchestration_workspace_scope(
                self._workspace_scope_identity(workdir_scope),
                run_id=args.get("run_id", ""),
            )

    def resolve_for_write(self, raw_path: str) -> ResolvedPath:
        return self.workspace.resolve_for_write_at(self._request_default_cwd(), raw_path)

    def git_path_filter(self, raw_path: str) -> str:
        scope_root = self._current_request_workspace_root().resolve(strict=False)
        target = self._request_default_cwd() if raw_path == "." else self.resolve_for_write(raw_path).path
        containing_root = self.workspace._containing_root(target.resolve(strict=False))
        if containing_root is None or containing_root.resolve(strict=False) != scope_root:
            raise ToolFailure(
                "ORCHESTRATION_WORKSPACE_MISMATCH",
                "Git path filter does not belong to the request-bound workspace.",
                category="security",
                retryable=False,
            )
        return normalize_rel_display(target, scope_root)

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
        endpoint = endpoint_identity_payload(self)
        return {
            "server": SERVER_NAME,
            "title": endpoint_server_title(endpoint),
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
            "endpoint": endpoint,
            "activation": self.activation_admission_snapshot(),
            **self.activation_admission_snapshot(),
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

    def _task_state_for_trace(self) -> dict[str, Any]:
        """Read optional telemetry context without bypassing tool error handling."""
        try:
            state = self.task_state.get()
        except ToolFailure:
            return {}
        return state if isinstance(state, dict) else {}

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
        invocation = build_tool_invocation_context(
            tool=name,
            args=args,
            request_id=request_id,
            started_wall_utc=dispatch_started_wall_utc,
            hub=self._current_hub_client() or {},
            task=self._task_state_for_trace(),
            trace_context=getattr(self.request_context, "trace_context", {}),
            task_context_id=self._current_stateless_task_context_id(),
            process_instance_id=str(self.process_instance_id),
        )

        def traced(result: dict[str, Any]) -> dict[str, Any]:
            structured = result.get("structuredContent") if isinstance(result.get("structuredContent"), dict) else {}
            payload = structured or {"ok": not bool(result.get("isError"))}
            self.emit_tool_trace(
                name,
                args,
                payload,
                dispatch_started_at,
                started_wall_utc=dispatch_started_wall_utc,
                invocation=invocation,
            )
            return result

        activation_bootstrap = self.activation_connector_bootstrap_for_call(name)
        if activation_bootstrap is not None:
            return traced(make_tool_result(
                name, activation_bootstrap, is_error=activation_bootstrap.get("ok") is False
            ))
        had_workspace_root = hasattr(self.request_context, "workspace_root")
        previous_workspace_root = getattr(self.request_context, "workspace_root", None)
        try:
            self._set_request_workspace_scope(name, args)
        except ToolFailure as exc:
            if had_workspace_root:
                self.request_context.workspace_root = previous_workspace_root
            else:
                try:
                    del self.request_context.workspace_root
                except AttributeError:
                    pass
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
            payload["presentation"] = TOOL_CONTRACT_RUNTIME.presentation(name, payload)
            return traced(make_tool_result(name, payload, is_error=True))
        if name in {"agent_workflow", "exec_command"}:
            try:
                self._preflight_tool_workspace_scope(name, args)
            except ToolFailure as exc:
                if had_workspace_root:
                    self.request_context.workspace_root = previous_workspace_root
                else:
                    try:
                        del self.request_context.workspace_root
                    except AttributeError:
                        pass
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
                payload["presentation"] = TOOL_CONTRACT_RUNTIME.presentation(name, payload)
                return traced(make_tool_result(name, payload, is_error=True))
        try:
            self._activation_enter_tool_call(name, args)
        except ToolFailure as exc:
            if had_workspace_root:
                self.request_context.workspace_root = previous_workspace_root
            else:
                try:
                    del self.request_context.workspace_root
                except AttributeError:
                    pass
            return traced(make_tool_result(name, {
                "ok": False,
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "category": exc.category,
                    "retryable": exc.retryable,
                    "details": exc.details,
                },
            }, is_error=True))
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
                return traced(make_tool_result(name, payload, is_error=True))
            except Exception as exc:
                self._idempotency_finish(name, args, exc=exc)
                self.emit_tool_trace(
                    name,
                    args,
                    {
                        "ok": False,
                        "error": {
                            "code": str(getattr(exc, "code", type(exc).__name__)),
                            "category": str(getattr(exc, "category", "internal")),
                            "retryable": bool(getattr(exc, "retryable", False)),
                        },
                    },
                    dispatch_started_at,
                    started_wall_utc=dispatch_started_wall_utc,
                    invocation=invocation,
                )
                raise
            failure = None
            structured = result.get("structuredContent") if isinstance(result.get("structuredContent"), dict) else {}
            if result.get("isError") or structured.get("ok") is False:
                failure = structured.get("error") if isinstance(structured.get("error"), dict) else {}
            if not structured.get("deduplicated"):
                self._idempotency_finish(name, args, result=result, failure=failure)
            return traced(result)
        finally:
            self._activation_leave_tool_call()
            if had_workspace_root:
                self.request_context.workspace_root = previous_workspace_root
            else:
                try:
                    del self.request_context.workspace_root
                except AttributeError:
                    pass

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
        self._preflight_tool_workspace_scope(name, args)
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
        args = arguments or {}
        compatibility_call = self.tool_mode == "smart" and name in SMART_COMPAT_TOOL_NAMES
        handler = self._tool_handlers.get(name) if name in self._exposed_tool_name_set or compatibility_call else None
        if handler is None:
            raise JsonRpcError(-32602, f"Unknown tool: {name}", {"reason": "unknown_tool"})
        spec = TOOL_REGISTRY[name]
        validate_arguments(name, args)
        if name in {"agent_workflow", "exec_command"}:
            self._preflight_tool_workspace_scope(name, args)
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
                self.ensure_tool_task_started(objective, current_step=TOOL_REGISTRY[name].title)
            self.request_context.request_id = request_id
            try:
                payload = self._invoke_with_read_retry(name, handler, args, spec)
            finally:
                if request_id is not None:
                    with self.request_sessions_lock:
                        self.request_sessions.pop(request_id, None)
                self.request_context.request_id = None
            payload.setdefault("ok", True)
            task_read_only = name == "task_control" and self._task_control_lifecycle_read_only(args)
            if spec.read_only is not True and name not in {"agent_workflow", "document_workflow"} and not task_read_only and not payload.get("deduplicated"):
                self._invalidate_fast_cache()
            if self._should_record_task_tool_result(name, args):
                self._record_task_tool_result(name, args, payload)
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
            if self._should_record_task_tool_result(name, args):
                self._record_task_tool_result(name, args, payload)
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
            if self._should_record_task_tool_result(name, args):
                self._record_task_tool_result(name, args, payload)
            return make_tool_result(name, payload, is_error=True)

    @staticmethod
    def _plain_command_completion_required(name: str, args: dict[str, Any], payload: dict[str, Any]) -> bool:
        if isinstance(payload.get("completion_report"), dict):
            return False
        status = str(payload.get("status") or "").lower()
        if name == "command_control":
            action = str(args.get("action", "poll")).lower()
            return action in {"poll", "write", "kill"} and status not in {"", "running", "terminating"}
        if name == "exec_command":
            return payload.get("ok") is False or status in {"failed", "timed_out", "timeout", "killed", "terminated", "stopped"}
        if name == "write_stdin":
            return status not in {"", "running", "terminating"}
        if name == "kill_session":
            return status not in {"", "running", "terminating"}
        return False

    def _record_task_tool_result(self, name: str, args: dict[str, Any], payload: dict[str, Any]) -> None:
        if not self._should_record_task_tool_result(name, args):
            return
        try:
            self.task_state.record_tool_result(name, args, payload)
            if not self._plain_command_completion_required(name, args, payload):
                return
            state = self.task_state.get()
            projection = state.get("orchestration") if isinstance(state.get("orchestration"), dict) else {}
            if str(projection.get("orchestration_state") or "").strip():
                return
            report = build_command_completion_report(
                task_state=state,
                workspace_identity=self._orchestration_workspace_identity("."),
            )
            if report is None:
                return
            self.task_state.set_completion_report(report)
            payload["completion_report"] = report
            payload["operator_visible_required"] = True
        except Exception:
            # State persistence must never turn a successful coding operation into a failed tool call.
            pass

    def server_info(self, args: dict[str, Any]) -> dict[str, Any]:
        return self.server_info_payload()

    def _orchestration_workspace_identity(self, path_value: object = ".") -> dict[str, Any]:
        requested = str(path_value or ".")
        bound_root = None
        if requested in {"", "."}:
            bound_root = self._bound_task_context_workspace(self._current_workspace_binding_id())
        resolved = self._resolve_authorized_execution_scope(
            str(bound_root) if bound_root is not None else requested,
            field="path",
        )
        workspace_identity = self._workspace_scope_identity(resolved)
        scope_root = self._workspace_root_for_identity(workspace_identity.get("root_id")) or self.workspace.root
        self.request_context.workspace_root = str(scope_root)
        try:
            status = self.git_status({"path": str(resolved.path), "max_entries": 2000}, source_identity_only=True)
        except ToolFailure:
            raise
        except (OSError, ValueError) as exc:
            raise ToolFailure(
                "WORKTREE_IDENTITY_UNAVAILABLE",
                "The exact source worktree identity could not be observed.",
                category="runtime",
                details={"error_type": type(exc).__name__},
            ) from exc
        if status.get("truncated") is True:
            raise ToolFailure(
                "WORKTREE_STATUS_TRUNCATED",
                "Git status exceeded the bounded exact-source identity limit.",
                category="validation",
                details={"max_entries": 2000},
            )
        raw_entries = status.get("entries") if isinstance(status.get("entries"), list) else []
        entries: list[dict[str, str]] = []
        for item in raw_entries:
            if not isinstance(item, dict):
                continue
            portable_path = str(item.get("path") or "").replace("\\", "/")
            if not portable_path.strip():
                continue
            protected_key = portable_path.casefold() if os.name == "nt" else portable_path
            if protected_key == ".coding-tools" or protected_key.startswith(".coding-tools/"):
                continue
            entries.append({
                "path": portable_path,
                "index_status": str(item.get("index_status") or ""),
                "worktree_status": str(item.get("worktree_status") or ""),
            })
        dirty_paths = [item["path"] for item in entries]
        head = str(status.get("head") or "")
        worktree_fp = fingerprint_paths(
            scope_root,
            dirty_paths,
            extra={"head": head, "branch": status.get("branch"), "entries": entries},
        )
        identity = {
            "is_repo": bool(status.get("is_repo")),
            "base_head": head,
            "branch": str(status.get("branch") or ""),
            "worktree_fp": worktree_fp,
            "source_fingerprint": worktree_fp,
            "runtime_worktree_fingerprint": worktree_fp,
            "dirty_paths": dirty_paths,
            "dirty_source_paths": list(dirty_paths),
            "workspace_identity": workspace_identity,
            "observed_at": datetime.now(timezone.utc).isoformat(),
            "observation_source": "exact_workspace_identity",
        }
        cache_key = os.path.normcase(os.path.abspath(str(scope_root)))
        with self._workspace_component_lock:
            self._orchestration_workspace_identity_cache[cache_key] = copy.deepcopy(identity)
        return identity

    def _cached_orchestration_workspace_identity(self) -> dict[str, Any]:
        """Return the last exact source observation without touching Git or disk."""
        cache_key = os.path.normcase(os.path.abspath(str(self.workspace.root)))
        with self._workspace_component_lock:
            identity = self._orchestration_workspace_identity_cache.get(cache_key)
            return copy.deepcopy(identity) if isinstance(identity, dict) else {}

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
        rebind = getattr(self, "_rebind_current_background_operation", None)
        if callable(rebind):
            rebind(ctx)
        try:
            self.task_state.set_orchestration_projection(ctx.projection(), event=event)
        except (OSError, ValueError):
            pass

    def _orchestration_result(self, ctx: RunContext | None, *, write_reports: bool = True) -> dict[str, Any] | None:
        return self._activation_orchestration_result(
            build_orchestration_runtime_result(self, ctx, write_reports=write_reports)
        )

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
        try:
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
        except ToolFailure as exc:
            if exc.code != "COMMAND_NOT_FOUND":
                raise
            try:
                report = self.task_state.find_command_completion(command_id)
            except ValueError as lookup_error:
                raise ToolFailure(
                    "COMMAND_COMPLETION_AMBIGUOUS",
                    str(lookup_error),
                    category="conflict",
                    details={"command_id": command_id},
                ) from lookup_error
            try:
                managed_job = self.execution_resource_governor.find_exact_job(
                    command_id=command_id
                )
            except ExecutionResourceError as lookup_error:
                raise ToolFailure(
                    lookup_error.code,
                    lookup_error.message,
                    category="conflict",
                    retryable=lookup_error.retryable,
                    details=lookup_error.details,
                ) from lookup_error
            if managed_job is not None and managed_job.get("terminal") is not True:
                if report is not None:
                    raise ToolFailure(
                        "COMMAND_COMPLETION_CONFLICT",
                        "The durable completion report conflicts with a nonterminal managed job.",
                        category="conflict",
                        details={
                            "command_id": command_id,
                            "job_id": managed_job.get("job_id"),
                            "lifecycle_state": managed_job.get("lifecycle_state"),
                        },
                    )
                raise
            if report is None and managed_job is None:
                raise
            recovered = {
                "ok": True,
                "status": "reconciled_terminal",
                "command_id": command_id,
                "reconciled": True,
                "reconciled_sources": [
                    source
                    for source, present in (
                        ("task_state_completion_report", report is not None),
                        ("managed_process_job", managed_job is not None),
                    )
                    if present
                ],
                "warning": "The live command handle is gone; durable terminal evidence was recovered instead.",
            }
            if report is not None:
                recovered.update(
                    {
                        "operator_visible_required": True,
                        "completion_report_id": TaskStateStore._completion_report_id(report),
                        "completion_report": report,
                    }
                )
            if managed_job is not None:
                recovered.update(
                    {
                        "job_id": managed_job.get("job_id"),
                        "lifecycle_state": managed_job.get("lifecycle_state"),
                        "exit_code": managed_job.get("exit_code"),
                        "result_status": managed_job.get("result_status"),
                        "managed_job": managed_job,
                    }
                )
            return recovered
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
        invocation: dict[str, Any] | None = None,
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
        trace_orchestration = result_orchestration or self._task_state_for_trace().get("orchestration", {})
        result_tail = self._measured_result_tail(payload)
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
                model_visible_chars=model_visible_text_chars(
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
                result_tail=result_tail,
                invocation=invocation,
                outcome={
                    "error_code": str(error.get("code") or ""),
                    "error_category": str(error.get("category") or ""),
                    "retryable": bool(error.get("retryable", False)),
                },
                truncated=bool(payload.get("truncated") or result_tail.get("truncated")),
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
        self._preflight_tool_workspace_scope("agent_workflow", args)
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
    secret_broker: SecretBroker | None = None,
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
        secret_broker=secret_broker,
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
    try:
        secret_broker = SecretBroker.from_environment()
        auth_handle = str(os.environ.pop(AUTH_HANDLE_ENV, "") or MCP_AUTH_HANDLE).strip()
        broker_auth_token = secret_broker.resolve(auth_handle) if auth_handle else None
    except SecretBrokerError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    auth_token = args.auth_token or broker_auth_token or None
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

    runtime = build_runtime(
        args,
        runtime_policy,
        auth_token=auth_token,
        oauth_config=oauth_config,
        transport="http",
        secret_broker=secret_broker,
    )
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
            secret_broker=secret_broker,
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
        secret_broker = SecretBroker.from_environment()
        os.environ.pop(AUTH_HANDLE_ENV, None)
    except SecretBrokerError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    try:
        runtime_policy = runtime_policy_from_args(args)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    runtime = build_runtime(args, runtime_policy, secret_broker=secret_broker)
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
