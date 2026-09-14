from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from .code_mode import (
    CODE_MODE_BINDING_OPERATIONS,
    CODE_MODE_BINDING_SCHEMA_VERSION,
    code_mode_worker_isolation_status,
)


# Public contract metadata. The exact tools/list SHA remains the audit identity.
# Breaking changes still require a real current tools/list/server/discover
# receipt. A reviewed cached-client rollover may only use the exact compatibility
# relation below together with separate current-process ChatWeb tools/call
# contact evidence; metadata by itself never grants connector freshness.
TOOL_CONTRACT_SCHEMA_VERSION = 1
SMART_TOOL_PROFILE = "smart-v3"
SMART_TOOL_CONTRACT_COMPATIBLE_PREDECESSORS_BY_SHA: dict[str, tuple[str, ...]] = {
    # Intentionally no d69436... -> d52c889... edge. Bounded Goal pagination
    # adds optional request fields, so cached predecessor requests remain wire
    # valid, but a predecessor client cannot express candidate_cursor or
    # candidate_limit. Treating that client as freshness-compatible would make
    # the runtime READY while the public capability is still unavailable.
    # The current pagination contract therefore requires a real tools/list
    # rediscovery; older reviewed compatibility edges remain available below.
    # Reviewed 2026-09-10: the exact prepare -> execute RUN/WAVE binding adds
    # only optional agent_workflow inputs.  The expanded
    # problem_resolution_envelope schema makes the already-enforced runtime
    # validator visible to clients; it does not remove any request that the
    # previous runtime accepted.  Cached 09e1... clients therefore remain
    # valid for the narrow, attested, no-workspace activation bootstrap.
    "d52c8895711d4655be0bdbe35cff6e3dcd1bd72f5caa98563ad37dd34835b677": (
        "09e1ca748a1319b814734967959d667aa111d70c1e3720353e3c83b1da22ccb9",
    ),
    # Reviewed 2026-09-09: exact prepare -> execute RUN/WAVE binding adds only
    # optional agent_workflow inputs and keeps every prior request valid. The
    # runtime validates both identifiers against the caller-scoped active
    # prepare lineage before a new RUN or write lease can be created.
    "09e1ca748a1319b814734967959d667aa111d70c1e3720353e3c83b1da22ccb9": (
        "98064347d3d27bec950b64d57319a3bc4a442bc12f6849a583cae7560f395f97",
    ),
    # Reviewed 2026-09-08: durable RUN continuation is additive inside the
    # existing eight-tool smart-v3 surface. agent_workflow keeps accepting the
    # legacy string continuation and additionally accepts the bounded grant
    # object; task_control retains every existing action and adds optional
    # continuation controls. Cached 642... clients therefore remain valid for
    # the narrow current-process bootstrap only; this relation never certifies
    # rediscovery, controller authority, dispatch, or an effect.
    "98064347d3d27bec950b64d57319a3bc4a442bc12f6849a583cae7560f395f97": (
        "6420537a2150a7d8e0152eabde4b298c3c689645a4515ba17fd254d60fc43cdf",
    ),
    # Reviewed 2026-09-04: bounded context controls on agent_workflow are
    # optional/additive, existing maxima are only widened, and the public
    # smart-v3 surface remains exactly eight tools. Older requests therefore
    # remain valid when they omit the new fields.
    "6420537a2150a7d8e0152eabde4b298c3c689645a4515ba17fd254d60fc43cdf": (
        "6bc9eaf623ada4b15c77f2926eb17a49dbcdb1606c407afddc97b9115ba397c1",
    ),
    # Reviewed 2026-09-01: Goal resolution and controller continuity add only
    # optional, fail-closed inputs/actions to the existing task_control tool.
    # The public surface remains exactly eight tools and older requests remain
    # valid because they omit these fields.
    "6bc9eaf623ada4b15c77f2926eb17a49dbcdb1606c407afddc97b9115ba397c1": (
        "c244ed297f707f9df48c1e5d6c7e204693f281a755c2e6344bde78e94abb8251",
    ),
    # Reviewed 2026-08-28: adopt_existing_files adds an optional, fail-closed
    # no-write adoption input to the two existing smart workflow tools. Older
    # clients remain valid because their requests omit the new field.
    "c244ed297f707f9df48c1e5d6c7e204693f281a755c2e6344bde78e94abb8251": (
        "57ed56a4f008287d9d9fdef035fa248f91cce4d58e935280b28963e4126a8053",
    ),
    # Reviewed 2026-08-26: this exact smart-v3/v1 tools/list contract is
    # additive relative to the previously approved ChatGPT snapshot. Keying the
    # relation by the exact current SHA makes any later schema drift fail closed
    # until it is separately reviewed and declared.
    "57ed56a4f008287d9d9fdef035fa248f91cce4d58e935280b28963e4126a8053": (
        "34cbb4c3ce3668f86ef6340dcb210d07425814c40ba734180ee1c026c96d409c",
    ),
}


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(char in "0123456789abcdef" for char in value)


def smart_tool_contract_compatible_predecessors(current_sha256: str) -> list[str]:
    """Return the fail-closed transitive closure of reviewed compatibility edges.

    Each map entry remains one explicitly reviewed direct edge.  Publishing its
    closure lets a cached client skip several additive releases without turning
    an unknown or cyclic graph into compatibility authority.
    """
    current = str(current_sha256 or "").strip().lower()
    if not _is_sha256(current):
        return []

    ordered: list[str] = []
    emitted: set[str] = set()
    visiting: set[str] = set()
    visited: set[str] = set()
    valid = True

    def visit(node: str) -> None:
        nonlocal valid
        if not valid or node in visited:
            return
        if node in visiting:
            valid = False
            return
        visiting.add(node)
        for raw_predecessor in SMART_TOOL_CONTRACT_COMPATIBLE_PREDECESSORS_BY_SHA.get(node, ()):
            predecessor = str(raw_predecessor or "").strip().lower()
            if not _is_sha256(predecessor):
                valid = False
                break
            if predecessor not in emitted:
                emitted.add(predecessor)
                ordered.append(predecessor)
            visit(predecessor)
            if not valid:
                break
        visiting.remove(node)
        visited.add(node)

    visit(current)
    return ordered if valid else []


TOOL_RISK_CLASSES = ("read_only", "project_write", "job_run", "account_manage", "unknown")
TOOL_MUTATION_CLASSES = ("none", "project", "job", "control", "unknown")
TOOL_CONCURRENCY_CLASSES = ("runtime_managed", "session_managed", "serialized", "unknown")
TOOL_METADATA_OWNERSHIP = {
    "mcp_annotation_owner": "python:ToolSpec",
    "native_execution_risk_owner": "rust:ToolMetadata/ToolRisk",
    "authority_owner": "EOCL+permission+write_lease",
}

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

CAPABILITY_VOCABULARY = (
    "bounded_evidence",
    "repository_read",
    "semantic_navigation",
    "candidate_patch_proposal",
    "parallel_delegation",
)
OPENCODE_SAFE_TOOLS = frozenset({"read", "glob", "grep", "list", "lsp"})


@dataclass(frozen=True)
class CapabilityProfile:
    name: str
    capabilities: frozenset[str]
    tool_names: frozenset[str] = frozenset()
    checkout_write: bool = False
    network: bool = False
    direct_tool_access: bool = False
    authority_owner: str = "EOCL+permission+write_lease"

    def projection(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "capabilities": sorted(self.capabilities),
            "tool_names": sorted(self.tool_names),
            "checkout_write": self.checkout_write,
            "network": self.network,
            "direct_tool_access": self.direct_tool_access,
            "security_boundary": False,
            "authority_owner": self.authority_owner,
        }


CAPABILITY_PROFILES: dict[str, CapabilityProfile] = {
    "candidate_mini": CapabilityProfile(
        "candidate_mini", frozenset({"bounded_evidence", "candidate_patch_proposal"})
    ),
    "candidate_luna": CapabilityProfile(
        "candidate_luna", frozenset({"bounded_evidence", "candidate_patch_proposal"})
    ),
    "cross_file": CapabilityProfile(
        "cross_file", frozenset({"bounded_evidence", "repository_read", "semantic_navigation", "candidate_patch_proposal"})
    ),
    "deep_code": CapabilityProfile(
        "deep_code", frozenset({"bounded_evidence", "repository_read", "semantic_navigation", "candidate_patch_proposal"})
    ),
    "consequential": CapabilityProfile(
        "consequential", frozenset({"bounded_evidence", "repository_read", "semantic_navigation", "candidate_patch_proposal"})
    ),
    "parallel_extreme": CapabilityProfile(
        "parallel_extreme", frozenset({"bounded_evidence", "repository_read", "semantic_navigation", "candidate_patch_proposal", "parallel_delegation"})
    ),
    "packet": CapabilityProfile("packet", frozenset({"bounded_evidence"})),
    "scoped": CapabilityProfile("scoped", frozenset({"bounded_evidence", "repository_read", "semantic_navigation"})),
    "critical": CapabilityProfile("critical", frozenset({"bounded_evidence", "repository_read", "semantic_navigation"})),
    "history": CapabilityProfile("history", frozenset({"bounded_evidence", "repository_read"})),
    "opencode_readonly": CapabilityProfile(
        "opencode_readonly",
        frozenset({"bounded_evidence", "repository_read", "semantic_navigation"}),
        tool_names=OPENCODE_SAFE_TOOLS,
        direct_tool_access=True,
    ),
}

AGENT_EXECUTION_ROUTES = {
    "mini": {"profile": "candidate_mini", "model": "gpt-5.4-mini", "effort": "low", "deadline_ms": 10_000, "high_cost": False},
    "luna": {"profile": "candidate_luna", "model": "gpt-5.6-luna", "effort": "high", "deadline_ms": 15_000, "high_cost": False},
    "terra": {"profile": "cross_file", "model": "gpt-5.6-terra", "effort": "high", "deadline_ms": 25_000, "high_cost": False},
    "sol_xhigh": {"profile": "deep_code", "model": "gpt-5.6-sol", "effort": "xhigh", "deadline_ms": 30_000, "high_cost": False},
    "sol_max": {"profile": "consequential", "model": "gpt-5.6-sol", "effort": "max", "deadline_ms": 30_000, "high_cost": True},
    "sol_ultra": {"profile": "parallel_extreme", "model": "gpt-5.6-sol", "effort": "ultra", "deadline_ms": 30_000, "high_cost": True},
}


@dataclass(frozen=True)
class ToolPresentation:
    card: str = "generic"
    title: str = ""

    def projection(self, fallback_title: str) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "card": self.card,
            "title": self.title or fallback_title,
        }


@dataclass(frozen=True)
class ToolSpec:
    """Metadata contract for one Python MCP tool.

    Execution authority deliberately does not live here. EOCL, permission policy,
    workspace checks, and write leases remain the enforcement plane.
    """

    title: str
    description: str
    read_only: bool = False
    destructive: bool = False
    idempotent: bool = False
    open_world: bool = False
    risk_class: str = "unknown"
    error_status: str | None = None
    content_builder: Callable[[dict[str, Any]], list[dict[str, Any]]] | None = None
    gated_by: str | None = None
    capability: str = "unspecified"
    mutation_class: str = "unknown"
    concurrency: str = "runtime_managed"
    timeout_policy: str = "handler_owned"
    cancellable: bool = False
    presentation: ToolPresentation = field(default_factory=ToolPresentation)

    def __post_init__(self) -> None:
        if self.risk_class not in TOOL_RISK_CLASSES:
            raise ValueError(f"Unsupported ToolSpec risk_class: {self.risk_class}")
        if self.mutation_class not in TOOL_MUTATION_CLASSES:
            raise ValueError(f"Unsupported ToolSpec mutation_class: {self.mutation_class}")
        if self.concurrency not in TOOL_CONCURRENCY_CLASSES:
            raise ValueError(f"Unsupported ToolSpec concurrency: {self.concurrency}")


def _image_content(payload: dict[str, Any]) -> list[dict[str, Any]]:
    encoded = str(payload.pop("_mcp_image_data", ""))
    return [{"type": "image", "data": encoded, "mimeType": str(payload.get("mime_type", "application/octet-stream"))}]


def _spec(
    title: str,
    description: str,
    *,
    card: str = "generic",
    capability: str = "unspecified",
    mutation_class: str = "unknown",
    **kwargs: Any,
) -> ToolSpec:
    return ToolSpec(
        title=title,
        description=description,
        capability=capability,
        mutation_class=mutation_class,
        presentation=ToolPresentation(card=card),
        **kwargs,
    )


TOOL_REGISTRY: dict[str, ToolSpec] = {
    "server_info": _spec("Server info", "Return server, workspace, project-context, auth, policy, and fixed-tool metadata.", read_only=True, idempotent=True, card="status", capability="runtime_read", mutation_class="none"),
    "workspace_context": _spec("Inspect workspace", "Preferred read-only tool when the user asks what is in the current working directory or wants a quick project overview. Returns the active workspace, default directory, project type, root entries, Git status, and task summary in one call; do not use exec_command merely to list files.", read_only=True, idempotent=True, risk_class="read_only", card="workspace", capability="repository_read", mutation_class="none"),
    "codex_bridge": _spec("Bridge to local Codex", "Coordinate a cost-aware independent Codex App Server reviewer sidecar with packet/scoped/critical/history profiles, explicit model/effort/deadlines, bridge-owned continuation, capacity cooldowns, and token telemetry. It shares Codex Desktop auth/history but never controls a live Desktop turn; every bridge turn is approvalPolicy=never, read-only, and no-network.", read_only=True, card="agent", capability="bounded_evidence", mutation_class="none", cancellable=True),
    "agent_workflow": _spec("Run complete agent workflow", "Primary tool for end-to-end work. Use one call for bug diagnosis, feature development, greenfield project creation, refactoring, test-failure repair, build/release verification, document work, or task resume. It bundles context collection, file creation or patches, commands, tests, builds, artifacts, Git diff, and persistent task state so the model must not repeat environment checks or low-level tool calls.", destructive=True, risk_class="project_write", card="workflow", capability="project_workflow", mutation_class="project", concurrency="serialized", cancellable=True),
    "prepare_coding_context": _spec("Prepare coding context", "Preferred first step for coding tasks: inspect the project, task state, instructions and Git once, batch-search multiple queries, and read the most relevant files in one cached call.", read_only=True, idempotent=True, card="workspace", capability="repository_read", mutation_class="none"),
    "apply_changes_and_verify": _spec("Apply changes and verify", "Preferred execution step: apply one or more patches, run multiple checks, optionally test/build, collect Git diff and update task state in one continuous call. Original low-level tools remain available as fallbacks.", destructive=True, card="diff", capability="project_write", mutation_class="project", concurrency="serialized"),
    "task_control": _spec("Control persistent task", "Control persistent task/orchestration state, coordination lanes and handoffs, or enqueue an explicitly confirmed runtime restart for the owning Electron supervisor.", idempotent=True, card="status", capability="orchestration_control", mutation_class="control", concurrency="serialized"),
    "read_files": _spec("Read multiple files", "Read one or more UTF-8 workspace files in one bounded call.", read_only=True, idempotent=True, card="read", capability="repository_read", mutation_class="none"),
    "file_batch": _spec("Batch file operations", "Create directories or copy, move, and delete multiple workspace paths in one bounded atomic-style request.", destructive=True, card="files", capability="project_write", mutation_class="project", concurrency="serialized"),
    "command_control": _spec("Control command session", "Poll, write to, terminate, or page output from a running command session.", risk_class="job_run", card="terminal", capability="job_control", mutation_class="job", concurrency="session_managed", cancellable=True),
    "git_inspect": _spec("Inspect Git repository", "Run status, diff, log, show, or blame through one compact Git inspection tool.", read_only=True, idempotent=True, card="diff", capability="repository_read", mutation_class="none"),
    "document_workflow": _spec("Read or create documents in one step", "Mandatory fast path for PDF, Word, Markdown, and text tasks. To create content from a PDF/DOCX, call action=inspect exactly once, reason over the returned text, then call action=create exactly once with target/content. Create supports .docx, .md, and .txt and already returns size, line count, SHA256, and preview, so never probe Python/PDF dependencies, use exec_command/apply_patch, repeat extraction, or run a separate verification command.", destructive=True, risk_class="project_write", card="document", capability="document", mutation_class="project", concurrency="serialized"),
    "document_extract": _spec("Extract Word or PDF", "Extract text and metadata from a workspace DOCX, PDF, or supported text document.", read_only=True, idempotent=True, card="document", capability="document_read", mutation_class="none"),
    "document_create": _spec("Create Word document", "Create a DOCX file directly in the workspace from structured plain text or Markdown-like content.", destructive=True, card="document", capability="document_write", mutation_class="project"),
    "document_convert": _spec("Convert document to Word", "Convert a workspace PDF or supported text document into a DOCX file without Base64 round-trips.", destructive=True, card="document", capability="document_write", mutation_class="project"),
    "check_exec_environment": _spec("Check exec environment", "Return lightweight exec_command sandbox and environment status known to the server.", read_only=True, idempotent=True, card="status", capability="runtime_read", mutation_class="none"),
    "get_default_cwd": _spec("Get default cwd (deprecated)", "Deprecated compatibility stub: always returns the workspace root. Transport-level default_cwd was removed; pass explicit paths/workdir per call.", read_only=True, idempotent=True, capability="runtime_read", mutation_class="none"),
    "set_default_cwd": _spec("Set default cwd (deprecated)", "Deprecated compatibility stub: transport-level default_cwd is no longer mutable. Pass explicit paths/workdir per call.", idempotent=True, capability="runtime_control", mutation_class="control"),
    "task_state_get": _spec("Get task state", "Read the persistent coding-task objective, progress, commands, results, modified files, failure, and next step.", read_only=True, idempotent=True, card="status", capability="orchestration_read", mutation_class="none"),
    "task_state_update": _spec("Update task state", "Create or update the persistent coding-task objective, plan progress, failure, and next step.", idempotent=True, card="status", capability="orchestration_control", mutation_class="control"),
    "task_state_clear": _spec("Clear task state", "Clear the current workspace task state after a task is finished or deliberately abandoned.", destructive=True, idempotent=True, card="status", capability="orchestration_control", mutation_class="control"),
    "task_state_pause": _spec("Pause task", "Pause the current persistent task without losing progress.", idempotent=True, card="status", capability="orchestration_control", mutation_class="control"),
    "task_state_resume": _spec("Resume task", "Resume a paused persistent task from its recorded next step.", idempotent=True, card="status", capability="orchestration_control", mutation_class="control"),
    "task_history_list": _spec("List task history", "List archived tasks for the current workspace.", read_only=True, idempotent=True, card="status", capability="orchestration_read", mutation_class="none"),
    "read_file": _spec("Read file", "Read a UTF-8 text file slice inside the configured workspace.", read_only=True, idempotent=True, card="read", capability="repository_read", mutation_class="none"),
    "list_dir": _spec("List directory", "List directory entries inside the configured workspace.", read_only=True, idempotent=True, card="search", capability="repository_read", mutation_class="none"),
    "list_files": _spec("List files", "List workspace files using glob filters.", read_only=True, idempotent=True, card="search", capability="repository_read", mutation_class="none"),
    "search_text": _spec("Search text", "Search UTF-8 workspace files for text or regex matches.", read_only=True, idempotent=True, card="search", capability="repository_read", mutation_class="none"),
    "apply_patch": _spec("Apply patch", "Stage, validate, and atomically replace files from a patch envelope inside the workspace.", destructive=True, card="diff", capability="project_write", mutation_class="project", concurrency="serialized"),
    "exec_command": _spec("Execute command", "Fallback for a focused workspace command only when no high-level workflow can perform it. Never use this tool to list a directory, inspect or create PDF/DOCX/Markdown/text documents, probe Python or PDF dependencies, or verify a document write; workspace_context and document_workflow perform those tasks with fewer round trips.", destructive=True, open_world=True, risk_class="job_run", error_status="failed", card="terminal", capability="job_run", mutation_class="job", concurrency="session_managed", cancellable=True),
    "verify_build": _spec("Build and verify project", "Detect the project, run its tests and build under the command policy, verify artifacts, read version metadata, hash outputs, and return a build report.", destructive=True, open_world=True, error_status="failed", card="terminal", capability="job_run", mutation_class="job", concurrency="session_managed", cancellable=True),
    "write_stdin": _spec("Write stdin", "Poll or interact with a running command session. Pass empty chars to wait for more output; pass non-empty chars to write to stdin.", card="terminal", capability="job_control", mutation_class="job", concurrency="session_managed"),
    "kill_session": _spec("Kill session", "Terminate a server-managed running command session.", destructive=True, card="terminal", capability="job_control", mutation_class="job", concurrency="session_managed", cancellable=True),
    "read_output": _spec("Read output", "Read retained stdout or stderr by output_ref with per-stream byte offset pagination.", read_only=True, idempotent=True, card="terminal", capability="job_read", mutation_class="none"),
    "git_status": _spec("Git status", "Return git working tree status for the workspace.", read_only=True, idempotent=True, card="status", capability="repository_read", mutation_class="none"),
    "git_diff": _spec("Git diff", "Return unified git diff for workspace changes.", read_only=True, idempotent=True, card="diff", capability="repository_read", mutation_class="none"),
    "git_log": _spec("Git log", "Return recent git commits with bounded structured metadata.", read_only=True, idempotent=True, card="search", capability="repository_read", mutation_class="none"),
    "git_show": _spec("Git show", "Return bounded git show output for a revision.", read_only=True, idempotent=True, card="diff", capability="repository_read", mutation_class="none"),
    "git_blame": _spec("Git blame", "Return bounded git blame metadata for a workspace file.", read_only=True, idempotent=True, card="read", capability="repository_read", mutation_class="none"),
    "request_permissions": _spec("Request permissions", "Report scoped permission-request status without silently granting operations.", read_only=True, risk_class="read_only", card="approval", capability="permission_read", mutation_class="none"),
    "view_image": _spec("View image", "Return a workspace image as MCP image content.", read_only=True, idempotent=True, risk_class="read_only", content_builder=_image_content, gated_by="enable_view_image", card="image", capability="repository_read", mutation_class="none"),
}


class ToolContractRuntime:
    """Read-only registry/view layer. It never grants execution authority."""

    def __init__(self, registry: dict[str, ToolSpec] | None = None) -> None:
        self.registry = registry or TOOL_REGISTRY

    def exposed_names(self, mode: str, *, gate_resolver: Callable[[str], bool]) -> list[str]:
        allowed = TOOL_MODE_ALLOWLISTS.get(mode, TOOL_MODE_ALLOWLISTS["coding"])
        if mode == "full":
            allowed = frozenset(self.registry)
        return [
            name
            for name, spec in self.registry.items()
            if name in allowed and (spec.gated_by is None or gate_resolver(spec.gated_by))
        ]

    def annotations(self, name: str, *, fake_readonly: bool = False) -> dict[str, Any]:
        spec = self.registry[name]
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

    def definition(
        self,
        name: str,
        *,
        input_schema: dict[str, Any],
        output_schema: dict[str, Any],
        fake_readonly: bool = False,
    ) -> dict[str, Any]:
        annotations = self.annotations(name, fake_readonly=fake_readonly)
        return {
            "name": name,
            "title": annotations["title"],
            "description": self.registry[name].description,
            "inputSchema": input_schema,
            "outputSchema": output_schema,
            "annotations": annotations,
        }

    def presentation(self, name: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        spec = self.registry[name]
        presentation = spec.presentation.projection(spec.title)
        source = payload if isinstance(payload, dict) else {}
        for key in ("status", "exit_code", "command_id", "session_id", "path", "target", "mime_type"):
            value = source.get(key)
            if value is None or isinstance(value, (dict, list)):
                continue
            text = str(value)
            presentation[key] = text[:500] if isinstance(value, str) else value
        return presentation

    def metadata_contract(self) -> dict[str, Any]:
        smart_names = sorted(TOOL_MODE_ALLOWLISTS["smart"])
        return {
            "schema_version": 2,
            "risk_vocabulary": list(TOOL_RISK_CLASSES),
            "mutation_vocabulary": list(TOOL_MUTATION_CLASSES),
            "concurrency_vocabulary": list(TOOL_CONCURRENCY_CLASSES),
            "ownership": dict(TOOL_METADATA_OWNERSHIP),
            "runtime": {
                "implementation": "python:ToolContractRuntime",
                "execution_handlers": "python:Runtime",
                "authority": "external",
            },
            "smart_v3_risk": {name: self.registry[name].risk_class for name in smart_names},
            "smart_v3_tools": {
                name: {
                    "risk": self.registry[name].risk_class,
                    "capability": self.registry[name].capability,
                    "mutation_class": self.registry[name].mutation_class,
                    "concurrency": self.registry[name].concurrency,
                    "timeout_policy": self.registry[name].timeout_policy,
                    "cancellable": self.registry[name].cancellable,
                    "presentation": self.registry[name].presentation.projection(self.registry[name].title),
                }
                for name in smart_names
            },
            "capability_profiles": {
                name: profile.projection() for name, profile in sorted(CAPABILITY_PROFILES.items())
            },
            "experimental_code_mode": {
                "enabled": False,
                "status": "gated",
                "reason": "isolated_worker_runtime_not_implemented",
                "required_boundary": "isolated_worker_with_host_bindings_only",
                "direct_filesystem": False,
                "network": False,
                "environment_secrets": False,
                "subprocess": False,
                "host_binding_proxy": {
                    "status": "ready",
                    "schema_version": CODE_MODE_BINDING_SCHEMA_VERSION,
                    "read_only": True,
                    "operations": list(CODE_MODE_BINDING_OPERATIONS),
                },
                "worker_isolation": code_mode_worker_isolation_status(),
            },
        }


TOOL_CONTRACT_RUNTIME = ToolContractRuntime()


def tool_metadata_contract() -> dict[str, Any]:
    return TOOL_CONTRACT_RUNTIME.metadata_contract()
