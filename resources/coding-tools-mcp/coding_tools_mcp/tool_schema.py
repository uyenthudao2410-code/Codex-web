from __future__ import annotations

import functools
from typing import Any

from .command_parse import INLINE_SCRIPT_PERMISSION
from .errors import JsonRpcError, ToolFailure
from .image_utils import IMAGE_RESIZE_MAX_DIMENSION
from .tool_contract import TOOL_CONTRACT_RUNTIME


DIFF_CONTINUATION_TOKEN_MAX_CHARS = 8192

EVALUATION_SCHEMA_VERSION = 2

def object_schema(properties: dict[str, Any] | None = None, required: list[str] | None = None) -> dict[str, Any]:
    merged = dict(properties or {})
    merged.setdefault(
        "task_context_id",
        {
            "type": "string",
            "minLength": 1,
            "maxLength": 128,
            "description": (
                "Optional MCP 2026 application-state handle. Reuse the task_context_id returned by a prior "
                "tool result to continue the same isolated task/run across stateless calls. Omitting it starts "
                "a fresh isolated context rather than inheriting another client's task."
            ),
        },
    )
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
    return TOOL_CONTRACT_RUNTIME.definition(
        name,
        input_schema=input_schemas()[name],
        output_schema=tool_output_schema(),
        fake_readonly=fake_readonly,
    )


def tool_annotations(name: str, *, fake_readonly: bool = False) -> dict[str, Any]:
    """Return a tool's MCP annotations.

    ``fake_readonly`` serves clients that refuse to call, or prompt on every call
    to, a tool annotated as mutating, which no server-side permission mode can
    influence. It reports every tool as read-only and non-destructive even though
    `apply_patch` and `exec_command` still mutate and still execute. Only
    `tools/list` may pass it: `server_info` and the server card must keep
    reporting the real annotations so the override stays discoverable.
    """
    return TOOL_CONTRACT_RUNTIME.annotations(name, fake_readonly=fake_readonly)


@functools.cache
def input_schemas() -> dict[str, dict[str, Any]]:
    # Cached: callers only read the returned tree, and rebuilding the full
    # ~190-line schema dict on every tools/call dispatch is measurable.
    string = {"type": "string"}
    integer = {"type": "integer"}
    boolean = {"type": "boolean"}
    string_array = {"type": "array", "items": {"type": "string"}}
    existing_file_adoptions = {
        "type": "array",
        "minItems": 1,
        "maxItems": 64,
        "items": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "path": {**string, "minLength": 1, "maxLength": 2000},
                "sha256": {**string, "minLength": 64, "maxLength": 64},
            },
            "required": ["path", "sha256"],
        },
        "description": (
            "Exact-byte, no-write adoption of pre-existing dirty source for the current EOCL wave. "
            "Every path must be inside the active write lease and its current SHA-256 must match."
        ),
    }
    return {
        "server_info": object_schema(),
        "agent_workflow": object_schema({
            "workflow": {**string, "enum": ["bugfix", "feature", "greenfield", "refactor", "test_failure", "build_release", "diagnose", "document", "resume", "custom"], "default": "custom", "description": "End-to-end task family. Select the closest intent instead of assembling low-level tools."},
            "phase": {**string, "enum": ["prepare", "execute", "run", "resume"], "default": "prepare", "description": "prepare gathers all context; execute applies a complete plan; run does both when changes are already known; resume restores persisted state and only missing context."},
            "execution_route": {**string, "enum": ["auto", "deterministic", "mini", "luna", "terra", "sol_xhigh", "sol_max", "sol_ultra"], "default": "auto", "description": "Primary implementation route. During ROI measurement, auto is fail-closed to deterministic so it cannot create model cost without representative paired evidence. Mini/Luna are explicit paired-study routes; Terra/Sol are explicit escalation or experiments. Sol max/ultra additionally require allow_high_cost=true."},
            "allow_high_cost": {**boolean, "default": False, "description": "Explicit acknowledgement required for sol_max or sol_ultra. This never makes those routes automatic."},
            "execution_mode": {**string, "enum": ["auto", "mcp_only", "bounded_candidate", "deep_single_lane", "coordinated_multi_worktree"], "default": "auto", "description": "EOCL execution mode. auto derives the mode from the resolved route. coordinated_multi_worktree is rejected unless runtime coordination readiness is proven."},
            "replan_reason": {**string, "description": "Required when continuing an active orchestration run from REPLAN; creates a new wave instead of silently changing route/authority."},
            "contract_fingerprint": {**string, "maxLength": 512, "description": "Optional settled-contract identity. Non-hash values are deterministically hashed before entering the audit ledger."},
            "problem_context": {
                "type": "object", "additionalProperties": False,
                "properties": {
                    "work_origin": {**string, "enum": ["problem", "non_problem", "unknown"], "default": "unknown"},
                    "problem_id": {**string, "maxLength": 128},
                    "problem_revision": {**integer, "minimum": 1, "maximum": 1000000},
                    "contract_fingerprint": {**string, "minLength": 64, "maxLength": 64},
                    "resolution_claim": {**string, "enum": ["none", "full_problem"], "default": "none"},
                    "frame": {
                        "type": "object",
                        "additionalProperties": True,
                        "description": "Optional typed shadow Problem Frame packet. It is normalized and hashed by runtime; it never grants authority or changes routing/mutation policy.",
                    },
                },
                "description": "Optional v11 PRL capture declaration. problem requires an exact immutable revision binding; non_problem creates no fake lineage; unknown stays policy-ineligible. Reserved workspace/base/trace authority is runtime-derived.",
            },
            "idempotency_key": {**string, "maxLength": 128, "description": "Optional durable mutation identity for execute/run. Reusing the same key+request deduplicates across MCP reconnect/restart; conflicting reuse fails closed."},
            "p5_assignment_id": {**string, "maxLength": 128, "description": "Optional immutable P5 assignment. Valid only for feature/bugfix execute or run after task_control p5 protocol_start; the runtime binds it to the acquired write lease before any write-capable call."},
            "continuation": {**string, "maxLength": DIFF_CONTINUATION_TOKEN_MAX_CHARS, "description": "Opaque source-fenced continuation returned by a prior large agent_workflow diff. Use only with phase=resume; source/scope/options drift fails closed."},
            "committed_review": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "base_commit": {**string, "pattern": "^[0-9a-fA-F]{40}$", "description": "Exact local Git commit object used as the comparison base; aliases and lazy fetch are rejected."},
                    "head_commit": {**string, "pattern": "^[0-9a-fA-F]{40}$", "description": "Exact local Git commit object under review."},
                    "paths": {"type": "array", "maxItems": 20, "items": {**string, "maxLength": 512}, "description": "Optional normalized repository-relative committed paths; the current worktree is not read as the diff source."},
                    "max_bytes": {**integer, "minimum": 1024, "maximum": 262144, "default": 65536},
                    "max_lines": {**integer, "minimum": 10, "maximum": 2000, "default": 1000},
                    "continuation": {**string, "maxLength": DIFF_CONTINUATION_TOKEN_MAX_CHARS, "description": "Signed continuation from this same immutable committed review; all range/scope/bounds must match."},
                },
                "required": ["base_commit", "head_commit"],
                "description": "Optional deterministic, read-only review of one immutable committed range. Valid only with phase=prepare; it remains inside agent_workflow and does not add a public MCP tool.",
            },
            "max_auto_steps": {**integer, "minimum": 1, "maximum": 256, "default": 64, "description": "Deterministic admission cap for planned workflow steps; no automatic retry loop is created."},
            "max_tool_hops": {**integer, "minimum": 1, "maximum": 512, "default": 96, "description": "Deterministic admission cap for planned internal tool hops."},
            "max_attempts": {**integer, "minimum": 1, "maximum": 10, "default": 1, "description": "Attempt budget. Current mutation policy remains manual-replan-only; unsafe side effects are never auto-replayed."},
            "max_runtime_seconds": {**integer, "minimum": 1, "maximum": 600, "default": 600, "description": "Upper bound applied to the workflow timeout budget."},
            "max_estimated_credits": {"type": "number", "minimum": 0, "default": 0, "description": "Optional candidate-model estimated-credit ceiling; 0 disables the credit cap. Enforced before mutation when usage economics are available."},
            "evaluation": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "pair_id": {**string, "maxLength": 128, "description": "Explicit paired-evaluation identity. Use the same value only for runs sharing source, task semantics and oracle."},
                    "policy": {**string, "maxLength": 100, "description": "Measured policy identifier. This tag never grants routing authority."},
                    "policy_version": {**string, "maxLength": 64},
                    "topology_id": {**string, "maxLength": 100},
                    "router_id": {**string, "maxLength": 100},
                    "router_version": {**string, "maxLength": 64},
                    "worker_count": {**integer, "minimum": 0, "maximum": 32},
                    "review_policy": {**string, "maxLength": 100},
                    "task_class": {**string, "maxLength": 100, "description": "Representative task class used for stratified paired analysis."},
                    "oracle_id": {**string, "maxLength": 128, "description": "Stable identity of the exact acceptance oracle shared by a pair."},
                    "provenance": {**string, "enum": ["representative", "benchmark", "synthetic"], "description": "Evidence provenance. Benchmark/synthetic rows are excluded from promotion evidence."},
                    "trace_id": {**string, "maxLength": 128},
                    "turn_id": {**string, "maxLength": 128},
                    "replicate_id": {**string, "maxLength": 128},
                    "order_index": {**integer, "minimum": 0, "maximum": 1000000},
                    "session_id": {**string, "maxLength": 128},
                    "cache_stratum": {**string, "enum": ["cold", "warm", "unknown"], "description": "Controlled cache/thread stratum; unknown is not pair-eligible."},
                    "environment_id": {**string, "maxLength": 256, "description": "Identity of the controlled environment manifest; only its SHA-256 is stored."},
                    "controller": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "source": {**string, "enum": ["client_reported", "provider_reported"]},
                            "started_at": {**string, "description": "Optional controller wall-clock start in ISO-8601. Omit when the client cannot measure it."},
                            "monetary_cost": {"type": "number", "minimum": 0},
                            "input_tokens": {**integer, "minimum": 0},
                            "cached_input_tokens": {**integer, "minimum": 0},
                            "output_tokens": {**integer, "minimum": 0},
                            "reasoning_output_tokens": {**integer, "minimum": 0},
                        },
                    },
                },
                "description": "Optional measurement tags for controlled paired evaluation. Server-owned task/tool/runtime fingerprints are added at run creation. Missing controller usage/cost remains unknown rather than zero.",
            },
            "solution_shadow_recommendation": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "recommendation_id": {**string, "maxLength": 128},
                    "candidate_solution_scope": {**string, "enum": ["localized_symbol", "localized_file", "bounded_multi_file", "cross_subsystem", "unknown"]},
                    "estimated_touched_surface": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "files": {**integer, "minimum": 0},
                            "symbols": {**integer, "minimum": 0},
                            "lines": {**integer, "minimum": 0},
                        },
                    },
                    "root_cause_confidence": {**string, "enum": ["low", "medium", "high", "unknown"]},
                    "oracle_strength": {**string, "enum": ["weak", "moderate", "strong", "unknown"]},
                    "expected_repair_risk": {**string, "enum": ["low", "medium", "high", "unknown"]},
                    "smallest_causal_solution": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "scope": {**string, "enum": ["localized_symbol", "localized_file", "bounded_multi_file", "cross_subsystem", "unknown"]},
                            "estimated_touched_surface": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "files": {**integer, "minimum": 0},
                                    "symbols": {**integer, "minimum": 0},
                                    "lines": {**integer, "minimum": 0},
                                },
                            },
                        },
                        "required": ["scope", "estimated_touched_surface"],
                    },
                },
                "required": ["recommendation_id", "candidate_solution_scope", "estimated_touched_surface", "root_cause_confidence", "oracle_strength", "expected_repair_risk", "smallest_causal_solution"],
                "description": "P4 shadow-only pre-mutation solution recommendation. Representative feature/bugfix mutation fails closed unless this recommendation was supplied here or already recorded before the first write lease.",
            },
            "objective": {**string, "description": "Concrete task objective, for example 'find and fix the login crash' or 'create a React dashboard from zero'."},
            "path": {**string, "default": ".", "description": "Project path relative to the configured workspace; for phase=prepare/run it also scopes bounded context collection."},
            "workdir": {**string, "description": "Command working directory relative to the workspace; defaults to path."},
            "queries": {"type": "array", "maxItems": 12, "items": string, "description": "Code symbols, errors, or phrases to search concurrently during phase=prepare/run bounded context collection."},
            "paths": {"type": "array", "maxItems": 40, "items": string, "description": "Likely files to prioritize and read during phase=prepare/run bounded context collection."},
            "regex": {**boolean, "default": False, "description": "Use regular-expression matching for phase=prepare/run context queries."},
            "case_sensitive": {**boolean, "default": False, "description": "Use case-sensitive matching for phase=prepare/run context queries."},
            "include_globs": {**string_array, "description": "Optional include globs forwarded unchanged to phase=prepare/run context collection."},
            "exclude_globs": {**string_array, "description": "Optional exclude globs forwarded unchanged to phase=prepare/run context collection."},
            "max_files": {**integer, "minimum": 1, "maximum": 30, "default": 12, "description": "Maximum files materialized by phase=prepare/run context collection."},
            "max_entries": {**integer, "minimum": 1, "maximum": 500, "default": 120, "description": "Maximum workspace entries collected during phase=prepare/run context collection."},
            "max_matches_per_query": {**integer, "minimum": 1, "maximum": 100, "default": 20, "description": "Maximum matches retained per phase=prepare/run context query."},
            "max_total_bytes": {**integer, "minimum": 4096, "maximum": 1048576, "default": 262144, "description": "Maximum total source bytes materialized by phase=prepare/run context collection."},
            "max_lines_per_file": {**integer, "minimum": 1, "maximum": 5000, "default": 2000, "description": "Maximum source lines materialized per file during phase=prepare/run context collection. The default preserves the existing 2,000-line bound; the finite opt-in remains additionally bounded by max_total_bytes and the per-file byte cap."},
            "force_refresh": {**boolean, "default": False, "description": "Bypass reusable context cache entries for phase=prepare/run context collection."},
            "directories": {"type": "array", "maxItems": 40, "items": string, "description": "Directories to create for greenfield or feature workflows."},
            "files": {"type": "array", "maxItems": 40, "items": {"type": "object", "properties": {"path": string, "content": string}, "required": ["path", "content"], "additionalProperties": False}, "description": "Complete new files to create, especially for greenfield projects."},
            "patch": {**string, "description": "One complete apply_patch envelope for existing-file changes."},
            "patches": {"type": "array", "maxItems": 6, "items": string, "description": "Complete related patch envelopes, applied in order."},
            "adopt_existing_files": existing_file_adoptions,
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
            "max_lines_per_file": {**integer, "minimum": 1, "maximum": 5000, "default": 2000, "description": "Maximum source lines materialized per file during phase=prepare/run context collection. The default preserves the existing 2,000-line bound; the finite opt-in remains additionally bounded by max_total_bytes and the per-file byte cap."},
            "force_refresh": {**boolean, "default": False},
        }),
        "apply_changes_and_verify": object_schema({
            "objective": string,
            "patch": string,
            "patches": {"type": "array", "maxItems": 10, "items": string},
            "adopt_existing_files": existing_file_adoptions,
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
            "action": {**string, "enum": ["get", "operation", "start", "update", "pause", "stop", "resume", "clear", "history", "audit", "accept", "reject", "lane", "events", "messages", "ack", "handoff", "quality", "observation", "solution_shadow", "problem", "goal", "continuity", "p5", "restart_runtime"], "default": "get"},
            "goal_action": {**string, "enum": ["get", "resolve"], "default": "get", "description": "Resolve and read the current Problem-backed Goal without creating authority or selecting by timestamp."},
            "goal_event": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "problem_id": {**string, "maxLength": 128},
                    "problem_revision": {**integer, "minimum": 1, "maximum": 1000000},
                    "run_id": {**string, "maxLength": 128},
                },
                "description": "Optional exact Goal/Problem or RUN binding. With multiple unresolved Goals, omission fails closed to a bounded candidate list.",
            },
            "continuity_action": {**string, "enum": ["policy", "get", "checkpoint", "ack", "reattach"], "default": "get", "description": "Read or advance bounded controller continuity, including exact same-role Goal reattach, without adding a public tool or granting write/acceptance authority."},
            "continuity_event": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "problem_id": {**string, "maxLength": 128},
                    "problem_revision": {**integer, "minimum": 1, "maximum": 1000000},
                    "material_event_kind": {**string, "maxLength": 96},
                    "material_event_id": {**string, "maxLength": 128},
                    "ack_id": {**string, "maxLength": 128},
                    "reattach_id": {**string, "maxLength": 128},
                    "continuity_core_fingerprint": {**string, "minLength": 64, "maxLength": 64},
                    "knowledge_revision": {**integer, "minimum": 1, "maximum": 1000000000},
                },
                "description": "Strict controller-continuity request. Source/runtime/material-state/capsule/authority fields are runtime-derived and cannot be caller-supplied.",
            },
            "run_id": {**string, "description": "Optional orchestration run id; defaults to the current task projection."},
            "wave_id": {**string, "description": "Optional orchestration wave id; defaults to the current task projection."},
            "acceptance_files": {
                "type": "array",
                "maxItems": 256,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "path": {**string, "minLength": 1, "maxLength": 2000},
                        "sha256": {**string, "minLength": 64, "maxLength": 64},
                    },
                    "required": ["path", "sha256"],
                },
                "description": "Optional exact-byte source-file attestations for action=accept. The runtime hashes current workspace bytes, fails closed on mismatch, and does not classify attested unchanged files as mutations.",
            },
            "problem_coverage_manifest": {
                "type": "object",
                "additionalProperties": {"type": "array", "maxItems": 100, "items": {**string, "maxLength": 128}},
                "description": "For a REQUIRED full_problem v11 wave only: maps every stable criterion ID to passed proof IDs from this exact accepted wave. The runtime validates and freezes it; it cannot create proof or accept a run.",
            },
            "problem_criterion_dispositions": {
                "type": "object",
                "additionalProperties": {**string, "enum": ["SATISFIED_NON_CODE"]},
                "description": "For a NOT_APPLICABLE full_problem v11 wave only: maps every and only current criterion ID to SATISFIED_NON_CODE. It requires zero mutation/source receipts and current ChatWeb controller authority.",
            },
            "problem_resolution_envelope": {
                "type": "object",
                "additionalProperties": True,
                "description": "Required for a full_problem acceptance claim: bounded direct outcomes, relevant invariants/truth domains, evidence provenance, excluded scope, and an executed/passed closure-falsification probe.",
            },
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
            "message_id": {**string, "description": "Coordination message id or current operator completion report id required by action=ack."},
            "message_status": {**string, "enum": ["pending", "acknowledged"], "default": "pending"},
            "direction": {**string, "enum": ["chatweb_to_codex", "codex_to_chatweb", "system"]},
            "handoff_action": {**string, "enum": ["get", "record"], "default": "get"},
            "conversation_epoch": {**integer, "minimum": 1, "default": 1},
            "payload": {"type": "object", "additionalProperties": True, "description": "Bounded handoff capsule payload. Raw transcript, source files and command output must not be included."},
            "quality_outcome": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "oracle_pass": boolean,
                    "critical_defect_count": {**integer, "minimum": 0},
                    "noncritical_defect_count": {**integer, "minimum": 0},
                    "regression_escape": boolean,
                    "rollback_required": boolean,
                    "manual_fix_required": boolean,
                    "maintainability_gate": {**string, "enum": ["pass", "fail", "not_applicable", "unknown"]},
                    "reviewer_blinded": boolean,
                    "observation_window_end": string,
                    "source": {**string, "maxLength": 128},
                },
                "description": "Immediate or delayed operational quality observation; never include private reasoning or raw source content.",
            },
            "solution_shadow_recommendation": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "recommendation_id": {**string, "maxLength": 128},
                    "candidate_solution_scope": {**string, "enum": ["localized_symbol", "localized_file", "bounded_multi_file", "cross_subsystem", "unknown"]},
                    "estimated_touched_surface": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "files": {**integer, "minimum": 0},
                            "symbols": {**integer, "minimum": 0},
                            "lines": {**integer, "minimum": 0},
                        },
                    },
                    "root_cause_confidence": {**string, "enum": ["low", "medium", "high", "unknown"]},
                    "oracle_strength": {**string, "enum": ["weak", "moderate", "strong", "unknown"]},
                    "expected_repair_risk": {**string, "enum": ["low", "medium", "high", "unknown"]},
                    "smallest_causal_solution": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "scope": {**string, "enum": ["localized_symbol", "localized_file", "bounded_multi_file", "cross_subsystem", "unknown"]},
                            "estimated_touched_surface": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "files": {**integer, "minimum": 0},
                                    "symbols": {**integer, "minimum": 0},
                                    "lines": {**integer, "minimum": 0},
                                },
                            },
                        },
                        "required": ["scope", "estimated_touched_surface"],
                    },
                },
                "required": ["recommendation_id", "candidate_solution_scope", "estimated_touched_surface", "root_cause_confidence", "oracle_strength", "expected_repair_risk", "smallest_causal_solution"],
                "description": "P4 shadow-only pre-mutation solution recommendation for feature/bugfix runs. It never changes routing, mutation, proof, or acceptance policy.",
            },
            "problem_event": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "operation": {**string, "enum": ["open", "link", "observe_feedback", "confirm", "reopen", "revise", "block", "abandon", "reconcile_provisional", "get"], "default": "get"},
                    "event_id": {**string, "maxLength": 128},
                    "problem_id": {**string, "maxLength": 128},
                    "problem_revision": {**integer, "minimum": 1, "maximum": 1000000},
                    "expected_revision": {**integer, "minimum": 1, "maximum": 1000000},
                    "expected_contract_fingerprint": {**string, "minLength": 64, "maxLength": 64},
                    "task_id": {**string, "maxLength": 128},
                    "turn_id": {**string, "maxLength": 128},
                    "trace_id": {**string, "maxLength": 128},
                    "run_id": {**string, "maxLength": 128},
                    "wave_id": {**string, "maxLength": 128},
                    "checkpoint_id": {**string, "maxLength": 128, "description": "Exact accepted checkpoint identity required only by reconcile_provisional."},
                    "capsule_id": {**string, "maxLength": 128},
                    "conversation_epoch": {**integer, "minimum": 0, "maximum": 1000000},
                    "task_class": {**string, "enum": ["feature", "bugfix", "diagnose", "test_failure", "build_release", "custom", "refactor", "unknown"]},
                    "engineering_floor": {**string, "enum": ["REQUIRED", "NOT_APPLICABLE", "UNKNOWN"]},
                    "relation_type": {**string, "enum": ["OPEN", "LINK", "NO_RUN_CREATED", "ENGINEERING_ATTEMPT_BOUND", "USER_FEEDBACK", "PROVISIONAL_RESOLUTION", "CONFIRMED_RESOLUTION", "REOPEN", "REVISION", "BLOCK", "ABANDON"]},
                    "link_status": {**string, "enum": ["EXACT", "AMBIGUOUS", "UNLINKED"]},
                    "link_role": {**string, "enum": ["PRIMARY", "SECONDARY"]},
                    "feedback_intent": {**string, "enum": ["CONFIRM_RESOLVED", "PARTIAL_RESOLUTION", "SAME_PROBLEM_STILL_FAILING", "CORRECT_UNDERSTANDING", "CORRECT_TARGET_OR_SCOPE", "CORRECT_TECHNICAL_RESULT", "CORRECT_PROOF_OR_VERIFICATION", "ADD_CONSTRAINT_OR_REQUIREMENT", "PROVIDE_NEW_EVIDENCE", "PREFERENCE_CHANGE", "NEW_PROBLEM", "SUPERSEDE_OR_CANCEL", "UNKNOWN"]},
                    "causal_mechanism": {**string, "enum": ["ASSISTANT_MISUNDERSTANDING", "WRONG_ROOT_CAUSE", "WRONG_TARGET_OR_WORKSPACE", "INSUFFICIENT_SOLUTION_SCOPE", "IMPLEMENTATION_DEFECT", "PROOF_ORACLE_GAP", "RUNTIME_OR_ENVIRONMENT_FAILURE", "SOURCE_OR_STATE_DRIFT", "STALE_CONTEXT_OR_REPLAY", "USER_NEW_INFORMATION", "REQUIREMENT_EVOLUTION", "USER_PREFERENCE_CHANGE", "EXTERNAL_DEPENDENCY_CHANGE", "UNKNOWN"]},
                    "economic_class": {**string, "enum": ["AVOIDABLE_CORRECTION", "PRODUCTIVE_CLARIFICATION", "LEGITIMATE_REQUIREMENT_GROWTH", "NEUTRAL_FOLLOWUP", "UNKNOWN"]},
                    "provenance": {**string, "enum": ["HOST_OBSERVED", "CONTROLLER_REPORTED_EXPLICIT_USER", "DETERMINISTIC_EVIDENCE", "HUMAN_ANNOTATED", "SHADOW_MODEL_INFERRED", "UNKNOWN"]},
                    "evidence_level": {**string, "enum": ["OBSERVED", "DERIVED_HIGH_CONFIDENCE", "INFERRED", "UNKNOWN"]},
                    "reason_code": {**string, "enum": ["none", "user_confirmation", "explicit_same_problem_correction", "explicit_contract_revision", "blocked_external_dependency", "blocked_missing_problem_context", "abandoned_by_user", "no_run_created", "engineering_attempt_bound", "ambiguous_relation", "unlinked_relation"]},
                    "occurred_at": {**string, "maxLength": 128, "description": "Optional attested external occurrence time. Runtime-owned recorded_at is not caller supplied."},
                    "occurred_at_source": {**string, "enum": ["RUNTIME", "HOST", "EXPLICIT_USER", "HUMAN_REVIEW", "EXTERNAL"]},
                    "contract_capsule": {
                        "type": "object", "additionalProperties": False,
                        "properties": {
                            "objective_summary": {**string, "maxLength": 2000},
                            "acceptance_criteria": {"type": "array", "minItems": 1, "maxItems": 100, "items": {"type": "object", "additionalProperties": False, "properties": {"criterion_id": {**string, "maxLength": 128}, "summary": {**string, "maxLength": 800}}, "required": ["criterion_id", "summary"]}},
                            "protected_invariants": {"type": "array", "maxItems": 40, "items": {**string, "maxLength": 800}},
                            "constraints": {"type": "array", "maxItems": 40, "items": {**string, "maxLength": 800}},
                            "unresolved_conditions": {"type": "array", "maxItems": 40, "items": {**string, "maxLength": 800}},
                        },
                        "required": ["objective_summary", "acceptance_criteria", "protected_invariants", "constraints", "unresolved_conditions"],
                        "description": "Bounded typed semantic contract. Raw prompts, transcripts, source, command output, credentials, personal data, reasoning, and arbitrary JSON are rejected before durable write.",
                    },
                },
                "required": ["operation"],
                "description": "Typed v11 Problem Resolution Lineage event. Public callers cannot grant provenance, evidence, clock, binding, guard, policy, or transition authority. Semantic transitions consume an exact host-turn receipt under a current ChatWeb controller; provisional resolution is checkpoint-reconciled only.",
            },
            "p5_experiment": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "operation": {**string, "enum": ["status", "prepare_a0", "open", "pause", "resume", "close", "hard_stop", "enroll", "assign", "protocol_start", "outcome", "analyze"], "default": "status"},
                    "activation_epoch_id": {**string, "maxLength": 128},
                    "manifest": {"type": "object", "additionalProperties": True, "description": "Exact P5 manifest. The runtime validates the normative v2 field set before opening an epoch."},
                    "manifest_sha256": {**string, "minLength": 64, "maxLength": 64},
                    "seed_handle": {**string, "maxLength": 256, "description": "Opaque secret:// handle only. Raw P5 randomization seed material is never accepted by MCP arguments or ledger events."},
                    "reason": {**string, "maxLength": 512},
                    "enrolled": {**boolean, "default": False},
                    "pre_arm_action_attested": {**boolean, "default": False, "description": "Required true immediately before immutable assignment; it records that no arm action or first write occurred."},
                    "assignment_id": {**string, "maxLength": 128},
                    "received_arm": {**string, "enum": ["control", "treatment"]},
                    "protocol_id": {**string, "enum": ["eocl-current-control-v1", "lean-causal-fix-gate-v1"]},
                    "candidate": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "task_assignment_id": {**string, "maxLength": 256},
                            "repository_identity_fp": {**string, "minLength": 64, "maxLength": 64},
                            "initial_task_spec_fp": {**string, "minLength": 64, "maxLength": 64},
                            "initial_target_source_block_id": {**string, "maxLength": 256},
                            "task_class": {**string, "enum": ["feature", "bugfix"]},
                            "representative_natural_task": boolean,
                            "exact_source_identity_available": boolean,
                            "observed_oracle_available": boolean,
                            "bounded_scope_feasible": boolean,
                            "no_conflicting_writer_or_lease": boolean,
                            "no_stale_or_recovery_state": boolean,
                            "not_high_risk": boolean,
                            "common_execution_contract_available": boolean,
                            "controller_context_fp": {**string, "maxLength": 128},
                            "session_cluster_id": {**string, "maxLength": 128},
                            "isolation_status": {**string, "enum": ["isolated", "shared_context_prohibited", "unknown"]},
                        },
                        "required": ["task_assignment_id", "repository_identity_fp", "initial_task_spec_fp", "initial_target_source_block_id", "task_class", "representative_natural_task", "exact_source_identity_available", "observed_oracle_available", "bounded_scope_feasible", "no_conflicting_writer_or_lease", "no_stale_or_recovery_state", "not_high_risk", "common_execution_contract_available"],
                    },
                    "outcome": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "terminal_status": {**string, "enum": ["accepted", "rejected", "failed", "blocked", "aborted", "timeout"]},
                            "terminal_at": {**string, "maxLength": 128},
                            "qualifying_acceptance_at": {**string, "maxLength": 128},
                            "post_assignment_replan_count": {**integer, "minimum": 0},
                            "immediate_oracle_pass": boolean,
                            "immediate_proof_observed": boolean,
                            "immediate_quality_status": {**string, "enum": ["pass", "fail", "not_applicable", "unknown"]},
                            "delayed_followup_status": {**string, "maxLength": 64},
                            "quality_followup_interference": {**string, "enum": ["none", "nonoverlapping_mutation", "overlapping_mutation", "attribution_unknown"]},
                            "adherence_status": {**string, "enum": ["adherent", "noncompliant", "crossover", "unknown"]},
                            "protocol_completed_at": {**string, "maxLength": 128},
                            "critical_security_or_data_loss": boolean,
                            "manual_rescue_or_fix": boolean,
                        },
                        "required": ["terminal_status"],
                    },
                },
                "required": ["operation"],
                "description": "Fail-closed P5 epoch lifecycle, arm-neutral enrollment, immutable blocked assignment, protocol, outcome, and feasibility analysis. This stays inside task_control; it does not add a ninth public tool or auto-activate treatment.",
            },
            "observation_span": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "span_id": {**string, "maxLength": 128},
                    "stage": {**string, "maxLength": 100},
                    "source": {**string, "maxLength": 128},
                    "measurement": {**string, "maxLength": 100},
                    "clock_domain": {**string, "maxLength": 160},
                    "start_ms": {"type": "number", "minimum": 0},
                    "end_ms": {"type": "number", "minimum": 0},
                    "parent_span_id": {**string, "maxLength": 128},
                    "depends_on": {"type": "array", "maxItems": 32, "items": {**string, "maxLength": 128}},
                    "trace_id": {**string, "maxLength": 128},
                    "turn_id": {**string, "maxLength": 128},
                    "observer_plane": {**string, "maxLength": 100},
                },
                "required": ["span_id", "stage", "source", "measurement", "clock_domain", "start_ms", "end_ms"],
                "description": "Content-free observed timing span. start_ms/end_ms share the declared monotonic clock_domain; cross-clock ordering requires explicit dependency identity.",
            },
            "confirm_restart": {**boolean, "default": False, "description": "Required true for action=restart_runtime. Set only after an explicit user request; the MCP only enqueues a delayed one-shot ticket for the owning Electron supervisor."},
            "allow_acceptance_pending": {**boolean, "default": False, "description": "For a controlled runtime restart, explicitly confirm that durable ACCEPTING state may be preserved across reconnect."},
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
                "max_lines": {**integer, "minimum": 1, "maximum": 5000, "default": 2000},
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
                "run_id": {
                    **string,
                    "maxLength": 128,
                    "description": "Optional explicit EOCL run owner. When omitted, only the caller's request-scoped task projection may be inherited; unscoped calls remain unowned.",
                },
                "wave_id": {
                    **string,
                    "maxLength": 128,
                    "description": "Optional explicit EOCL wave owner. Must be paired with run_id and match the caller's current scoped task projection when one exists.",
                },
                "resource_class": {
                    **string,
                    "enum": ["LIGHT", "MEDIUM", "HEAVY"],
                    "description": "Optional execution resource classification. HEAVY commands require a current EOCL RUN/WAVE owner.",
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
