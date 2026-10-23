from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import threading
import time
import tomllib
import uuid
from collections import deque
from pathlib import Path
from typing import Any, Callable

from .app_server_persistence import restore_persistent_thread as _restore_persistent_thread
from .processes import managed_process_creationflags
from .runtime_config import is_core_command_env_name, is_filtered_env_var
from .secret_broker import OPENAI_API_KEY_HANDLE, SecretBroker


_CODEX_IDENTITY_ENV_NAMES = frozenset({
    "HOME", "USER", "USERNAME", "TEMP", "TMP", "TMPDIR",
    "LOCALAPPDATA", "APPDATA", "USERPROFILE", "CODEX_HOME",
})


_ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
_MAX_STDERR_CHARS = 16_384
_MAX_AGENT_TEXT_CHARS = 65_536
_MAX_EVENT_TEXT_CHARS = 4_096
_MAX_EVENTS = 400
_DEFAULT_REQUEST_TIMEOUT_SECONDS = 20.0
_VALID_EFFORTS = frozenset({"low", "medium", "high", "xhigh", "max", "ultra"})
_CAPACITY_COOLDOWN_SECONDS = 30.0
_MAX_DEADLINE_MS = 30_000
_PRICING_BASIS = "codex_rate_card_observed_2026-08-12"
_CREDIT_RATES_PER_MILLION = {
    "gpt-5.6-sol": (125.0, 12.5, 750.0),
    "gpt-5.6-terra": (62.5, 6.25, 375.0),
    "gpt-5.6-luna": (25.0, 2.5, 150.0),
    "gpt-5.4-mini": (18.75, 1.875, 113.0),
}


def _is_meaningful_observation_event(item: dict[str, Any]) -> bool:
    """Keep observation delivery and its wake predicate on one event contract."""
    return (
        item.get("server_request") is True
        or item.get("method") in {"turn/started", "turn/completed"}
        or (
            item.get("method") == "item/completed"
            and item.get("item_type") not in {None, "userMessage", "agentMessage"}
        )
    )
_REVIEW_FEATURES = {
    "multi_agent": False,
    "apps": False,
    "browser_use": False,
    "browser_use_external": False,
    "computer_use": False,
    "image_generation": False,
    "memories": False,
    "plugins": False,
    "skill_search": False,
    "workspace_dependencies": False,
}
_PROFILE_SPECS: dict[str, dict[str, Any]] = {
    "candidate_mini": {
        "model": "gpt-5.4-mini",
        "effort": "low",
        "recommended_deadline_ms": 10_000,
        "features": {**_REVIEW_FEATURES, "shell_tool": False},
        "base_instructions": (
            "You are a bounded patch-candidate generator. Use only the supplied evidence. "
            "Do not inspect repository files, run commands, browse, modify state, or delegate."
        ),
        "developer_instructions": (
            "Return only the requested structured candidate. If the packet is insufficient, return blocked instead of guessing."
        ),
    },
    "candidate_luna": {
        "model": "gpt-5.6-luna",
        "effort": "high",
        "recommended_deadline_ms": 15_000,
        "features": {**_REVIEW_FEATURES, "shell_tool": False},
        "base_instructions": (
            "You are a bounded patch-candidate generator for a harder localized leaf. Use only supplied evidence. "
            "Do not inspect repository files, run commands, browse, modify state, or delegate."
        ),
        "developer_instructions": (
            "Prefer the smallest causal candidate. Return blocked when exact evidence is insufficient."
        ),
    },
    "cross_file": {
        "model": "gpt-5.6-terra",
        "effort": "high",
        "recommended_deadline_ms": 25_000,
        "features": {**_REVIEW_FEATURES, "shell_tool": True},
        "base_instructions": (
            "You are a bounded cross-file implementation researcher. Inspect only the current workspace as needed, "
            "never modify state, use network access, or delegate. Return a candidate change set for deterministic application."
        ),
        "developer_instructions": "Keep reads scoped to the supplied objective and candidate paths; return evidence-first output.",
    },
    "deep_code": {
        "model": "gpt-5.6-sol",
        "effort": "xhigh",
        "recommended_deadline_ms": 30_000,
        "features": {**_REVIEW_FEATURES, "shell_tool": True},
        "base_instructions": (
            "You are the deep-code lane. Inspect the current workspace read-only, resolve the supplied implementation question, "
            "and return a bounded candidate change set. Never modify state, use network access, or delegate."
        ),
        "developer_instructions": "Optimize for a correct minimal candidate and explicit proof; stop on unresolved shared semantics.",
    },
    "continuation_proposal": {
        "model": "gpt-5.6-sol",
        "effort": "xhigh",
        "recommended_deadline_ms": 30_000,
        "features": {**_REVIEW_FEATURES, "shell_tool": False},
        "locked_route": True,
        "require_default_argv": True,
        "base_instructions": (
            "You are a no-tools continuation proposal generator. Use only the contract and evidence supplied in this turn. "
            "Do not inspect repository files, run commands, browse, use tools, modify state, delegate, or request new authority."
        ),
        "developer_instructions": (
            "Return exactly one JSON object matching the response contract in the prompt, with no Markdown or surrounding prose. "
            "A provider output schema may be absent for compatibility; MCP, not you, validates the complete JSON object, "
            "scope, effects, checks, receipts, and every technical replan decision."
        ),
    },
    "consequential": {
        "model": "gpt-5.6-sol",
        "effort": "max",
        "recommended_deadline_ms": 30_000,
        "features": {**_REVIEW_FEATURES, "shell_tool": True},
        "base_instructions": (
            "You are a consequential-change analysis lane. Inspect the current workspace read-only and return a bounded candidate "
            "only when the supplied invariants are sufficiently settled. Never modify state, use network access, or delegate."
        ),
        "developer_instructions": "Prioritize correctness, security, data and compatibility invariants over breadth or speed.",
    },
    "parallel_extreme": {
        "model": "gpt-5.6-sol",
        "effort": "ultra",
        "recommended_deadline_ms": 30_000,
        "features": {**_REVIEW_FEATURES, "multi_agent": True, "shell_tool": True},
        "base_instructions": (
            "You are the explicitly requested parallel-extreme analysis lane. Use parallel reasoning only for genuinely independent "
            "workstreams, keep repository access read-only, and return one bounded candidate change set. Never use network access."
        ),
        "developer_instructions": (
            "Do not create parallel work for sequential tasks. Reconcile independent findings before returning the candidate."
        ),
    },
    "packet": {
        "model": "gpt-5.4-mini",
        "effort": "low",
        "recommended_deadline_ms": 8_000,
        "features": {**_REVIEW_FEATURES, "shell_tool": False},
        "base_instructions": (
            "You are an independent read-only reviewer. Review only the supplied packet. "
            "Do not inspect repository files, run commands, browse, modify state, or delegate."
        ),
        "developer_instructions": (
            "Use supplied evidence only. If evidence is insufficient, return blocked instead of gathering new evidence. "
            "Return only decision-relevant output."
        ),
    },
    "scoped": {
        "model": "gpt-5.6-luna",
        "effort": "low",
        "recommended_deadline_ms": 20_000,
        "features": {**_REVIEW_FEATURES, "shell_tool": True},
        "base_instructions": (
            "You are an independent read-only code reviewer. Use the supplied evidence first and inspect only the current "
            "workspace when necessary. Never modify state, use network access, or delegate."
        ),
        "developer_instructions": "Prefer the smallest discriminating read or command and return concise evidence.",
    },
    "critical": {
        "model": "gpt-5.6-terra",
        "effort": "medium",
        "recommended_deadline_ms": 30_000,
        "features": {**_REVIEW_FEATURES, "shell_tool": True},
        "base_instructions": (
            "You are an independent read-only critical reviewer. Reconstruct the relevant invariant from evidence, inspect "
            "the current workspace only when required, and report counterexamples or missing proof. Never modify state, use "
            "network access, or delegate."
        ),
        "developer_instructions": "Optimize for correctness and discriminatory proof, not breadth or prose volume.",
    },
    "history": {
        "model": "gpt-5.6-terra",
        "effort": "medium",
        "recommended_deadline_ms": 30_000,
        "features": {**_REVIEW_FEATURES, "shell_tool": True},
        "base_instructions": (
            "You are an independent read-only reviewer operating on an explicitly requested persisted Codex history fork. "
            "Do not modify state, use network access, or delegate."
        ),
        "developer_instructions": "Use inherited history only when it materially answers the question; keep the result concise.",
    },
    # W3 native chat (Work Hub): the only profile whose base instructions are
    # conversational rather than reviewer-shaped. The bridge-wide invariants
    # do not change: approvalPolicy=never, read-only sandbox, no network —
    # the chat can discuss and inspect, never apply changes.
    "chat": {
        "model": "gpt-5.6-terra",
        "effort": "medium",
        "recommended_deadline_ms": 30_000,
        "features": {**_REVIEW_FEATURES, "shell_tool": True},
        "base_instructions": (
            "You are the built-in chat assistant of the Codex-web Work Hub, running as a native "
            "Codex App Server thread for the current workspace. Hold a conversation with the user "
            "and help with questions about this workspace; you may inspect files read-only when "
            "that helps. You cannot modify files, run write actions, or use the network: changes "
            "are executed only through the workspace's own Job/approval flow, never from this chat."
        ),
        "developer_instructions": (
            "Keep answers grounded in the conversation and in workspace evidence you actually read. "
            "When the user asks for a change, describe the concrete change set instead of claiming it was applied."
        ),
    },
}


class CodexBridgeError(RuntimeError):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        retryable: bool = False,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable
        self.details = details or {}


def discover_codex_binary(
    env: dict[str, str] | None = None,
    *,
    which: Callable[[str], str | None] = shutil.which,
) -> Path | None:
    """Find Codex without depending on WindowsApps execution rights."""
    source = os.environ if env is None else env
    for key in ("CODING_TOOLS_MCP_CODEX_BIN", "CODEX_BIN"):
        raw = str(source.get(key, "")).strip()
        if not raw:
            continue
        candidate = Path(raw).expanduser()
        if candidate.is_file():
            return candidate.resolve(strict=False)
        resolved = which(raw)
        if resolved:
            return Path(resolved).resolve(strict=False)

    resolved = which("codex")
    if resolved:
        return Path(resolved).resolve(strict=False)

    local_app_data = str(source.get("LOCALAPPDATA", "")).strip()
    if not local_app_data:
        return None
    base = Path(local_app_data) / "OpenAI" / "Codex" / "bin"
    try:
        candidates = [path for path in base.glob("*/codex.exe") if path.is_file()]
    except OSError:
        return None
    if not candidates:
        return None
    candidates.sort(key=lambda path: path.stat().st_mtime_ns, reverse=True)
    return candidates[0].resolve(strict=False)


def configured_mcp_server_names(codex_home: Path) -> list[str]:
    config_path = codex_home / "config.toml"
    try:
        payload = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, tomllib.TOMLDecodeError):
        return []
    servers = payload.get("mcp_servers")
    if not isinstance(servers, dict):
        return []
    return sorted(str(name) for name in servers if str(name).strip())


def sanitized_codex_env(
    source: dict[str, str] | None = None,
    *,
    secret_broker: SecretBroker | None = None,
) -> dict[str, str]:
    source_env = os.environ if source is None else source
    env: dict[str, str] = {}
    for key, value in source_env.items():
        upper = key.upper()
        if not (is_core_command_env_name(key) or upper in _CODEX_IDENTITY_ENV_NAMES):
            continue
        if is_filtered_env_var(key, value):
            continue
        env[key] = value
    if secret_broker is not None:
        env = secret_broker.inject_env(env, {"OPENAI_API_KEY": OPENAI_API_KEY_HANDLE})
    return env


def _codex_home_hint(source: dict[str, str] | None = None) -> Path:
    env = os.environ if source is None else source
    explicit = str(env.get("CODEX_HOME", "")).strip()
    if explicit:
        return Path(explicit).expanduser().resolve(strict=False)
    return (Path.home() / ".codex").resolve(strict=False)


def _mcp_disable_args(names: list[str]) -> list[str]:
    unsupported = [name for name in names if not re.fullmatch(r"[A-Za-z0-9_-]+", name)]
    if unsupported:
        raise CodexBridgeError(
            "CODEX_MCP_ISOLATION_UNSUPPORTED",
            "Codex MCP isolation cannot safely override one or more configured server names.",
            details={"server_names": unsupported},
        )
    args: list[str] = []
    for name in names:
        args.extend(["-c", f"mcp_servers.{name}.enabled=false"])
    return args


def _bounded(value: object, limit: int) -> str:
    text = str(value or "")
    return text if len(text) <= limit else text[:limit] + "..."


def _norm_path(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    # Canonicalize through realpath so equivalent spellings of the same
    # directory compare equal — most importantly the Windows 8.3 short
    # form (e.g. C:\Users\RUNNER~1\...) that TEMP and legacy environment
    # variables hand out, versus the long form Path.resolve() produces.
    return os.path.normcase(os.path.realpath(os.path.normpath(text)))


def _is_within_workspace(path_value: object, workspace: Path) -> bool:
    child = _norm_path(path_value)
    parent = _norm_path(workspace)
    if not child or not parent:
        return False
    try:
        return os.path.commonpath([child, parent]) == parent
    except ValueError:
        return False


def _usage_economics(token_usage: object, model: str) -> dict[str, Any] | None:
    usage = token_usage if isinstance(token_usage, dict) else None
    last = usage.get("last") if usage else None
    if not isinstance(last, dict):
        return None
    exact_fields = (
        "inputTokens",
        "cachedInputTokens",
        "outputTokens",
        "reasoningOutputTokens",
    )
    exact: dict[str, int] = {}
    for field in exact_fields:
        value = last.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            return None
        exact[field] = value
    input_tokens = exact["inputTokens"]
    cached_tokens = exact["cachedInputTokens"]
    output_tokens = exact["outputTokens"]
    reasoning_tokens = exact["reasoningOutputTokens"]
    if cached_tokens > input_tokens or reasoning_tokens > output_tokens:
        return None
    uncached_tokens = max(0, input_tokens - cached_tokens)
    rates = _CREDIT_RATES_PER_MILLION.get(model)
    estimated_credits = None
    if rates is not None:
        uncached_rate, cached_rate, output_rate = rates
        estimated_credits = round(
            (uncached_tokens * uncached_rate + cached_tokens * cached_rate + output_tokens * output_rate) / 1_000_000,
            6,
        )
    return {
        "model": model,
        "input_tokens": input_tokens,
        "cached_input_tokens": cached_tokens,
        "uncached_input_tokens": uncached_tokens,
        "output_tokens": output_tokens,
        "reasoning_output_tokens": reasoning_tokens,
        "cache_ratio": round(cached_tokens / input_tokens, 4) if input_tokens else 0.0,
        "estimated_credits": estimated_credits,
        "pricing_basis": _PRICING_BASIS if rates is not None else None,
        "estimated": rates is not None,
        "measured": True,
        "usage_provenance": "provider_reported",
        "usage_source": "codex_app_server:thread/tokenUsage/updated",
        "accounting_profile": "openai_compatible",
    }


def _is_capacity_error(error: object) -> bool:
    if not isinstance(error, dict):
        return False
    code = str(error.get("codexErrorInfo", "")).strip().lower()
    message = str(error.get("message", "")).strip().lower()
    return code in {"serveroverloaded", "rate_limit", "ratelimit"} or "at capacity" in message or "overloaded" in message


def _terminate_process_tree(proc: subprocess.Popen[str], *, wait_seconds: float = 1.5) -> None:
    if proc.poll() is not None:
        return
    if os.name == "nt":
        try:
            subprocess.run(
                ["taskkill.exe", "/PID", str(proc.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=max(1.0, wait_seconds),
                check=False,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            return
        except (OSError, subprocess.SubprocessError):
            pass
    try:
        proc.terminate()
        proc.wait(timeout=wait_seconds)
    except (OSError, subprocess.TimeoutExpired):
        try:
            proc.kill()
        except OSError:
            pass


class CodexAppServerBridge:
    """Read-only bridge to an independent local Codex App Server sidecar.

    The sidecar shares Codex Desktop auth, skills, config and persisted history.
    It never claims the live in-memory turn used by Desktop. Existing Desktop
    threads are inspect/fork sources only; bridge-owned turns always use
    approvalPolicy=never and a read-only, no-network sandbox.
    """

    def __init__(
        self,
        workspace_provider: Callable[[], Path],
        *,
        resource_governor=None,
        secret_broker: SecretBroker | None = None,
    ) -> None:
        self._workspace_provider = workspace_provider
        self._resource_governor = resource_governor
        self._secret_broker = secret_broker
        self._managed_job_id = ""
        self._process: subprocess.Popen[str] | None = None
        self._binary: Path | None = None
        self._disabled_mcp_servers: list[str] = []
        self._initialized = False
        self._initialize_result: dict[str, Any] = {}
        self._next_request_id = 1
        self._pending: dict[int, dict[str, Any]] = {}
        self._pending_lock = threading.Lock()
        self._write_lock = threading.Lock()
        self._start_lock = threading.RLock()
        self._condition = threading.Condition(threading.RLock())
        self._events: deque[dict[str, Any]] = deque(maxlen=_MAX_EVENTS)
        self._event_cursor = 0
        self._stderr_tail = ""
        self._owned_threads: dict[str, dict[str, Any]] = {}
        self._turn_states: dict[str, dict[str, Any]] = {}
        self._latest_turn_by_thread: dict[str, str] = {}
        self._capacity_cooldowns: dict[str, dict[str, Any]] = {}
        self._recent_runs: deque[dict[str, Any]] = deque(maxlen=32)
        self._launch_argv_is_default = True
        self._closing = False

    def handle(self, args: dict[str, Any]) -> dict[str, Any]:
        action = str(args.get("action", "status")).strip().lower()
        if action == "status":
            return self.status()
        if action == "models":
            return self.models()
        if action == "threads":
            return self.threads(limit=int(args.get("limit", 10)))
        if action == "run":
            output_schema = args.get("output_schema")
            if output_schema is not None and not isinstance(output_schema, dict):
                raise CodexBridgeError("INVALID_OUTPUT_SCHEMA", "output_schema must be a JSON object.")
            return self.run(
                str(args.get("prompt", "")),
                source_thread_id=str(args.get("source_thread_id", "")).strip() or None,
                profile=str(args.get("profile", "")).strip().lower() or None,
                model=str(args.get("model", "")).strip() or None,
                effort=str(args.get("effort", "")).strip().lower() or None,
                lifetime=str(args.get("lifetime", "ephemeral")).strip().lower() or "ephemeral",
                deadline_ms=int(args.get("deadline_ms", 0)),
                output_schema=output_schema,
                wait_ms=int(args.get("wait_ms", 0)),
            )
        if action == "continue":
            output_schema = args.get("output_schema")
            if output_schema is not None and not isinstance(output_schema, dict):
                raise CodexBridgeError("INVALID_OUTPUT_SCHEMA", "output_schema must be a JSON object.")
            return self.continue_thread(
                thread_id=str(args.get("thread_id", "")).strip(),
                prompt=str(args.get("prompt", "")),
                model=str(args.get("model", "")).strip() or None,
                effort=str(args.get("effort", "")).strip().lower() or None,
                deadline_ms=int(args.get("deadline_ms", 0)),
                output_schema=output_schema,
                wait_ms=int(args.get("wait_ms", 0)),
            )
        if action == "observe":
            return self.observe(
                thread_id=str(args.get("thread_id", "")).strip(),
                turn_id=str(args.get("turn_id", "")).strip() or None,
                after_cursor=int(args.get("after_cursor", 0)),
                wait_ms=int(args.get("wait_ms", 0)),
                max_events=int(args.get("max_events", 50)),
            )
        if action == "interrupt":
            return self.interrupt(
                thread_id=str(args.get("thread_id", "")).strip(),
                turn_id=str(args.get("turn_id", "")).strip(),
            )
        if action == "close":
            self.close()
            return {"ok": True, "connected": False, "closed": True}
        raise CodexBridgeError(
            "INVALID_ACTION",
            f"Unsupported codex_bridge action: {action}",
            details={"supported": ["status", "models", "threads", "run", "continue", "observe", "interrupt", "close"]},
        )

    def status(self) -> dict[str, Any]:
        self._ensure_connected()
        proc = self._process
        init = dict(self._initialize_result)
        user_agent = str(init.get("userAgent", ""))
        version = user_agent.split("/", 1)[1].split(" ", 1)[0] if "/" in user_agent else ""
        return {
            "ok": True,
            "connected": bool(proc and proc.poll() is None and self._initialized),
            "pid": proc.pid if proc else None,
            "binary": str(self._binary) if self._binary else None,
            "codex_home": init.get("codexHome"),
            "codex_version": version or None,
            "platform": init.get("platformFamily") or init.get("platformOs"),
            "workspace": str(self._workspace()),
            "bridge_mode": "independent_app_server_sidecar",
            "shares_codex_home": True,
            "disabled_codex_mcp_servers": list(self._disabled_mcp_servers),
            "live_desktop_turn_attached": False,
            "safety": {
                "approval_policy": "never",
                "sandbox": "read-only",
                "network_access": False,
                "desktop_source_threads": "inspect_or_fork_only",
            },
            "profile_defaults": {
                name: {
                    "model": spec["model"],
                    "effort": spec["effort"],
                    "recommended_deadline_ms": spec["recommended_deadline_ms"],
                }
                for name, spec in _PROFILE_SPECS.items()
            },
            "capacity_cooldowns": self._capacity_status(),
            "recent_runs": list(self._recent_runs)[-5:],
            "stderr_tail": _bounded(self._stderr_tail, 4_000) or None,
        }

    def models(self) -> dict[str, Any]:
        self._ensure_connected()
        result = self._request("model/list", {})
        data = result.get("data") if isinstance(result, dict) else None
        if not isinstance(data, list):
            data = result.get("models") if isinstance(result, dict) else None
        rows: list[dict[str, Any]] = []
        for item in data if isinstance(data, list) else []:
            if not isinstance(item, dict):
                continue
            efforts = item.get("supportedReasoningEfforts")
            rows.append({
                "id": item.get("id") or item.get("model"),
                "display_name": item.get("displayName"),
                "is_default": bool(item.get("isDefault")),
                "default_effort": item.get("defaultReasoningEffort"),
                "supported_efforts": [row.get("reasoningEffort") for row in efforts if isinstance(row, dict) and row.get("reasoningEffort")] if isinstance(efforts, list) else [],
            })
        return {"ok": True, "models": rows, "count": len(rows), "capacity_cooldowns": self._capacity_status()}

    def owns_thread(self, thread_id: str) -> bool:
        """Return whether the current sidecar process owns the supplied thread handle."""
        with self._condition:
            return bool(thread_id and thread_id in self._owned_threads)

    def threads(self, *, limit: int = 10) -> dict[str, Any]:
        self._ensure_connected()
        limit = max(1, min(50, int(limit)))
        scan_limit = max(20, min(200, limit * 5))
        result = self._request("thread/list", {"limit": scan_limit})
        data = result.get("data") if isinstance(result, dict) else []
        rows: list[dict[str, Any]] = []
        for thread in data if isinstance(data, list) else []:
            if not isinstance(thread, dict) or not _is_within_workspace(thread.get("cwd"), self._workspace()):
                continue
            rows.append(self._thread_summary(thread))
            if len(rows) >= limit:
                break
        return {
            "ok": True,
            "workspace": str(self._workspace()),
            "threads": rows,
            "count": len(rows),
            "scanned": len(data) if isinstance(data, list) else 0,
            "scope": "current_workspace_only",
            "note": "Persisted history only; this sidecar does not claim the live in-memory Desktop turn.",
        }

    def run(
        self,
        prompt: str,
        *,
        source_thread_id: str | None = None,
        profile: str | None = None,
        model: str | None = None,
        effort: str | None = None,
        lifetime: str = "ephemeral",
        deadline_ms: int = 0,
        output_schema: dict[str, Any] | None = None,
        wait_ms: int = 0,
    ) -> dict[str, Any]:
        prompt = self._validate_prompt(prompt)
        workspace = self._workspace()
        lifetime = str(lifetime or "ephemeral").strip().lower()
        if lifetime not in {"ephemeral", "persistent"}:
            raise CodexBridgeError(
                "INVALID_LIFETIME",
                "lifetime must be ephemeral or persistent.",
                details={"supported": ["ephemeral", "persistent"]},
            )
        route = self._resolve_route(profile=profile, model=model, effort=effort, source_thread_id=source_thread_id)
        self._ensure_connected()
        self._assert_profile_launch_policy(route)
        self._check_capacity(route["model"])
        common_thread = self._thread_route_params(route, workspace)
        if source_thread_id:
            source_result = self._request("thread/read", {"threadId": source_thread_id, "includeTurns": False})
            source = source_result.get("thread") if isinstance(source_result, dict) else None
            if not isinstance(source, dict):
                raise CodexBridgeError("SOURCE_THREAD_NOT_FOUND", "Codex did not return the requested source thread.")
            if not _is_within_workspace(source.get("cwd"), workspace):
                raise CodexBridgeError(
                    "SOURCE_WORKSPACE_MISMATCH",
                    "The source Codex thread belongs to a different workspace; switch the MCP workspace before forking it.",
                    details={"source_cwd": source.get("cwd"), "workspace": str(workspace)},
                )
            thread_response = self._request(
                "thread/fork",
                {
                    **common_thread,
                    "threadId": source_thread_id,
                    "ephemeral": lifetime == "ephemeral",
                },
            )
            creation_mode = "fork" if lifetime == "ephemeral" else "persistent_fork"
        else:
            thread_response = self._request(
                "thread/start",
                {
                    **common_thread,
                    "ephemeral": lifetime == "ephemeral",
                },
            )
            creation_mode = "new" if lifetime == "ephemeral" else "persistent_new"
        thread = thread_response.get("thread") if isinstance(thread_response, dict) else None
        if not isinstance(thread, dict) or not str(thread.get("id", "")).strip():
            raise CodexBridgeError("THREAD_START_FAILED", "Codex did not return a bridge thread id.")
        thread_id = str(thread["id"])
        with self._condition:
            self._owned_threads[thread_id] = {
                "workspace": str(workspace),
                "source_thread_id": source_thread_id,
                "created_at": time.time(),
                "mode": creation_mode,
                "lifetime": lifetime,
                "profile": route["profile"],
                "model": route["model"],
                "effort": route["effort"],
                "session_id": str(thread.get("sessionId") or ""),
                "reported_model": thread.get("model"),
                "reported_effort": thread.get("reasoningEffort"),
            }
        return self._launch_turn(
            thread_id=thread_id,
            prompt=prompt,
            route=route,
            creation_mode=creation_mode,
            source_thread_id=source_thread_id,
            deadline_ms=deadline_ms,
            output_schema=output_schema,
            wait_ms=wait_ms,
        )

    def restore_persistent_thread(
        self,
        *,
        thread_id: str,
        profile: str,
        model: str | None = None,
        effort: str | None = None,
        expected_session_id: str = "",
        deadline_ms: int = 0,
        output_schema: dict[str, Any] | None = None,
        wait_ms: int = 0,
    ) -> dict[str, Any]:
        """Restore one exact durable App Server lane without launching a turn."""
        return _restore_persistent_thread(
            self,
            error_type=CodexBridgeError,
            workspace_contains=_is_within_workspace,
            thread_id=thread_id,
            profile=profile,
            model=model,
            effort=effort,
            expected_session_id=expected_session_id,
            deadline_ms=deadline_ms,
            output_schema=output_schema,
            wait_ms=wait_ms,
        )

    def resume_persistent_thread(
        self,
        *,
        thread_id: str,
        prompt: str,
        profile: str,
        model: str | None = None,
        effort: str | None = None,
        expected_session_id: str = "",
        deadline_ms: int = 0,
        output_schema: dict[str, Any] | None = None,
        wait_ms: int = 0,
    ) -> dict[str, Any]:
        """Restore a persisted lane, then launch exactly one new caller-authorized turn."""
        restored = self.restore_persistent_thread(
            thread_id=thread_id,
            profile=profile,
            model=model,
            effort=effort,
            expected_session_id=expected_session_id,
        )
        route = restored.get("route") if isinstance(restored.get("route"), dict) else {}
        launched = self._launch_turn(
            thread_id=thread_id,
            prompt=prompt,
            route=route,
            creation_mode="persistent_resume",
            source_thread_id=None,
            deadline_ms=deadline_ms,
            output_schema=output_schema,
            wait_ms=wait_ms,
        )
        return launched

    def continue_thread(
        self,
        *,
        thread_id: str,
        prompt: str,
        model: str | None = None,
        effort: str | None = None,
        deadline_ms: int = 0,
        output_schema: dict[str, Any] | None = None,
        wait_ms: int = 0,
    ) -> dict[str, Any]:
        self._ensure_connected()
        self._require_owned_thread(thread_id)
        prompt = self._validate_prompt(prompt)
        with self._condition:
            owned = dict(self._owned_threads[thread_id])
            latest = self._latest_turn_by_thread.get(thread_id)
            latest_state = dict(self._turn_states.get(latest, {})) if latest else {}
        if latest and str(latest_state.get("status", "inProgress")) not in {"completed", "failed", "interrupted"}:
            raise CodexBridgeError(
                "TURN_ALREADY_ACTIVE",
                "The bridge-owned thread already has an active turn; observe or interrupt it before continuing.",
                retryable=True,
                details={"thread_id": thread_id, "turn_id": latest},
            )
        route = self._resolve_route(
            profile=str(owned.get("profile") or "scoped"),
            model=model or str(owned.get("model") or ""),
            effort=effort or str(owned.get("effort") or ""),
            source_thread_id="history-source" if owned.get("profile") == "history" else None,
            continuing=True,
        )
        self._assert_profile_launch_policy(route)
        self._check_capacity(route["model"])
        with self._condition:
            self._owned_threads[thread_id].update({"model": route["model"], "effort": route["effort"]})
        return self._launch_turn(
            thread_id=thread_id,
            prompt=prompt,
            route=route,
            creation_mode="continue",
            source_thread_id=str(owned.get("source_thread_id") or "") or None,
            deadline_ms=deadline_ms,
            output_schema=output_schema,
            wait_ms=wait_ms,
        )

    def observe(
        self,
        *,
        thread_id: str,
        turn_id: str | None,
        after_cursor: int = 0,
        wait_ms: int = 0,
        max_events: int = 50,
    ) -> dict[str, Any]:
        self._ensure_connected()
        self._require_owned_thread(thread_id)
        wait_ms = max(0, min(30_000, int(wait_ms)))
        max_events = max(1, min(100, int(max_events)))
        after_cursor = max(0, int(after_cursor))
        with self._condition:
            selected_turn = turn_id or self._latest_turn_by_thread.get(thread_id)
            if not selected_turn:
                raise CodexBridgeError("TURN_ID_REQUIRED", "No bridge turn is known for this thread.")
            self._require_owned_turn(thread_id, selected_turn)
            deadline = time.monotonic() + (wait_ms / 1000.0)
            while wait_ms > 0 and not self._has_new_or_terminal(thread_id, selected_turn, after_cursor):
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                self._condition.wait(timeout=remaining)
            state = dict(self._turn_states.get(selected_turn, {}))
            retained_floor_cursor = int(self._events[0].get("cursor", 0)) if self._events else self._event_cursor + 1
            history_gap = bool(self._events) and after_cursor < retained_floor_cursor - 1
            raw_events = [
                dict(item)
                for item in self._events
                if int(item.get("cursor", 0)) > after_cursor
                and item.get("thread_id") == thread_id
                and item.get("turn_id") in {None, selected_turn}
            ]
            meaningful = [
                item
                for item in raw_events
                if _is_meaningful_observation_event(item)
            ]
            events = meaningful[:max_events]
            if len(meaningful) > max_events and events:
                next_cursor = int(events[-1]["cursor"])
            elif raw_events:
                next_cursor = int(raw_events[-1]["cursor"])
            elif history_gap:
                # A stale consumer must rebaseline at the live ring head rather
                # than repeatedly polling an evicted cursor forever.
                next_cursor = self._event_cursor
            else:
                next_cursor = after_cursor
        status = str(state.get("status", "inProgress"))
        terminal = status in {"completed", "interrupted", "failed"}
        if terminal:
            state = self._finalize_turn(selected_turn)
        return {
            "ok": True,
            "thread_id": thread_id,
            "turn_id": selected_turn,
            "status": status,
            "terminal": terminal,
            "agent_text": _bounded(state.get("agent_text", ""), _MAX_AGENT_TEXT_CHARS),
            "error": state.get("error"),
            "token_usage": state.get("token_usage"),
            "route": {"profile": state.get("profile"), "model": state.get("model"), "effort": state.get("effort")},
            "wall_time_ms": state.get("wall_time_ms"),
            "economics": state.get("economics"),
            "events": events,
            "next_cursor": next_cursor,
            "history_gap": history_gap,
            "history_floor_cursor": retained_floor_cursor,
            "requires_progress_report": not terminal,
        }

    def interrupt(self, *, thread_id: str, turn_id: str) -> dict[str, Any]:
        self._ensure_connected()
        self._require_owned_thread(thread_id)
        self._require_owned_turn(thread_id, turn_id)
        self._request("turn/interrupt", {"threadId": thread_id, "turnId": turn_id})
        return {"ok": True, "thread_id": thread_id, "turn_id": turn_id, "interrupt_requested": True}

    def close(self) -> None:
        with self._start_lock:
            self._closing = True
            proc = self._process
            self._process = None
            self._disabled_mcp_servers = []
            self._initialized = False
            self._initialize_result = {}
            with self._condition:
                self._owned_threads.clear()
                self._turn_states.clear()
                self._latest_turn_by_thread.clear()
                self._condition.notify_all()
            self._fail_pending("Codex bridge closed")
            if proc is not None and proc.poll() is None:
                try:
                    if proc.stdin:
                        proc.stdin.close()
                except OSError:
                    pass
                _terminate_process_tree(proc)
            if proc is not None and self._managed_job_id and self._resource_governor is not None:
                self._resource_governor.complete(
                    self._managed_job_id,
                    lifecycle_state="closed",
                    exit_code=proc.poll(),
                )
                self._managed_job_id = ""
            self._closing = False

    def _validate_prompt(self, prompt: str) -> str:
        prompt = prompt.strip()
        if not prompt:
            raise CodexBridgeError("PROMPT_REQUIRED", "codex_bridge run/continue requires a non-empty prompt.")
        if len(prompt) > 20_000:
            raise CodexBridgeError("PROMPT_TOO_LARGE", "codex_bridge prompt exceeds the 20,000 character safety bound.", details={"max_chars": 20_000, "actual_chars": len(prompt)})
        return prompt

    def _resolve_route(self, *, profile: str | None, model: str | None, effort: str | None, source_thread_id: str | None, continuing: bool = False) -> dict[str, Any]:
        profile_name = (profile or ("history" if source_thread_id else "scoped")).strip().lower()
        spec = _PROFILE_SPECS.get(profile_name)
        if spec is None:
            raise CodexBridgeError("INVALID_PROFILE", f"Unknown Codex bridge profile: {profile_name}", details={"supported": list(_PROFILE_SPECS)})
        if not continuing and source_thread_id and profile is not None and profile_name != "history":
            raise CodexBridgeError("HISTORY_PROFILE_REQUIRED", "A persisted Desktop source thread may only be forked with profile=history.")
        if not continuing and profile_name == "history" and not source_thread_id:
            raise CodexBridgeError("SOURCE_THREAD_REQUIRED", "profile=history requires source_thread_id from action=threads.")
        resolved_model = str(model or spec["model"]).strip()
        if not resolved_model or len(resolved_model) > 80:
            raise CodexBridgeError("INVALID_MODEL", "model must be a non-empty model id of at most 80 characters.")
        resolved_effort = str(effort or spec["effort"]).strip().lower()
        if resolved_effort not in _VALID_EFFORTS:
            raise CodexBridgeError("INVALID_EFFORT", f"Unsupported reasoning effort: {resolved_effort}", details={"supported": sorted(_VALID_EFFORTS)})
        if bool(spec.get("locked_route")) and (resolved_model != str(spec["model"]) or resolved_effort != str(spec["effort"])):
            raise CodexBridgeError(
                "PROFILE_ROUTE_LOCKED",
                f"{profile_name} has a fixed model and effort; callers cannot override its continuation safety profile.",
                details={"profile": profile_name, "model": spec["model"], "effort": spec["effort"]},
            )
        return {
            "profile": profile_name,
            "model": resolved_model,
            "effort": resolved_effort,
            "recommended_deadline_ms": int(spec["recommended_deadline_ms"]),
            "features": dict(spec["features"]),
            "base_instructions": str(spec["base_instructions"]),
            "developer_instructions": str(spec["developer_instructions"]),
            "require_default_argv": bool(spec.get("require_default_argv")),
        }

    def _assert_profile_launch_policy(self, route: dict[str, Any]) -> None:
        if not bool(route.get("require_default_argv")):
            return
        if os.environ.get("CODING_TOOLS_MCP_CODEX_ARGV", "").strip() or not self._launch_argv_is_default:
            raise CodexBridgeError(
                "CONTINUATION_PROFILE_UNCERTIFIED_LAUNCH",
                "continuation_proposal requires the bridge's certified default App Server launch; custom argv is not accepted.",
                details={"profile": route.get("profile")},
            )

    def _thread_route_params(self, route: dict[str, Any], workspace: Path) -> dict[str, Any]:
        return {
            "cwd": str(workspace),
            "approvalPolicy": "never",
            "sandbox": "read-only",
            "runtimeWorkspaceRoots": [str(workspace)],
            "model": route["model"],
            "config": {"model_reasoning_effort": route["effort"], "features": route["features"]},
            "baseInstructions": route["base_instructions"],
            "developerInstructions": route["developer_instructions"],
        }

    def _launch_turn(self, *, thread_id: str, prompt: str, route: dict[str, Any], creation_mode: str, source_thread_id: str | None, deadline_ms: int, output_schema: dict[str, Any] | None, wait_ms: int) -> dict[str, Any]:
        self._check_capacity(route["model"])
        workspace = self._workspace()
        params: dict[str, Any] = {
            "threadId": thread_id,
            "input": [{"type": "text", "text": prompt}],
            "cwd": str(workspace),
            "approvalPolicy": "never",
            "sandboxPolicy": {"type": "readOnly", "networkAccess": False},
            "runtimeWorkspaceRoots": [str(workspace)],
            "model": route["model"],
            "effort": route["effort"],
        }
        if output_schema is not None:
            encoded_schema = json.dumps(output_schema, ensure_ascii=False, separators=(",", ":"))
            if len(encoded_schema.encode("utf-8")) > 8_192:
                raise CodexBridgeError("OUTPUT_SCHEMA_TOO_LARGE", "output_schema exceeds the 8 KiB bridge bound.")
            params["outputSchema"] = output_schema
        turn_response = self._request("turn/start", params)
        turn = turn_response.get("turn") if isinstance(turn_response, dict) else None
        if not isinstance(turn, dict) or not str(turn.get("id", "")).strip():
            raise CodexBridgeError("TURN_START_FAILED", "Codex did not return a bridge turn id.")
        turn_id = str(turn["id"])
        with self._condition:
            state = self._turn_states.setdefault(turn_id, {})
            terminal_before_response = str(state.get("status", "")) in {"completed", "failed", "interrupted"}
            state.update({
                "thread_id": thread_id,
                "turn_id": turn_id,
                "profile": route["profile"],
                "model": route["model"],
                "effort": route["effort"],
            })
            if not terminal_before_response:
                state["status"] = str(turn.get("status", "inProgress"))
                state["error"] = turn.get("error")
            state.setdefault("agent_text", "")
            state.setdefault("error", None)
            state.setdefault("started_monotonic", time.monotonic())
            state.setdefault("finalized", False)
            self._latest_turn_by_thread[thread_id] = turn_id
            owned = dict(self._owned_threads.get(thread_id, {}))
            self._condition.notify_all()
        merged_status = str(state.get("status", "inProgress"))
        payload: dict[str, Any] = {
            "ok": True,
            "status": "running" if merged_status == "inProgress" else merged_status,
            "thread_id": thread_id,
            "turn_id": turn_id,
            "creation_mode": creation_mode,
            "lifetime": str(owned.get("lifetime") or "ephemeral"),
            "session_id": str(owned.get("session_id") or "") or None,
            "source_thread_id": source_thread_id,
            "workspace": str(workspace),
            "route": {"profile": route["profile"], "model": route["model"], "effort": route["effort"], "recommended_deadline_ms": route["recommended_deadline_ms"]},
            "history_cost_warning": bool(source_thread_id),
            "safety": {"approval_policy": "never", "sandbox": "read-only", "network_access": False},
            "next_action": "Call codex_bridge action=observe with thread_id and turn_id until terminal.",
        }
        bounded_deadline = max(0, min(_MAX_DEADLINE_MS, int(deadline_ms)))
        if bounded_deadline > 0:
            # `observe()` intentionally wakes on meaningful progress such as
            # turn/started. A launch deadline is different: it covers the full
            # interval in which the turn can reach a terminal state.
            deadline_at = time.monotonic() + (bounded_deadline / 1000.0)
            deadline_cursor = 0
            observation: dict[str, Any] | None = None
            while time.monotonic() < deadline_at:
                remaining_ms = max(1, int((deadline_at - time.monotonic()) * 1000))
                observation = self.observe(
                    thread_id=thread_id,
                    turn_id=turn_id,
                    after_cursor=deadline_cursor,
                    wait_ms=min(30_000, remaining_ms),
                    max_events=50,
                )
                if observation.get("terminal"):
                    observation["deadline_hit"] = False
                    break
                next_cursor = int(observation.get("next_cursor", deadline_cursor))
                if next_cursor <= deadline_cursor:
                    # A non-terminal observation without a later cursor has
                    # consumed its wait interval, so do not busy-loop on it.
                    break
                deadline_cursor = next_cursor
            if observation is None or not observation.get("terminal"):
                if observation is not None:
                    deadline_cursor = int(observation.get("next_cursor", deadline_cursor))
                try:
                    self.interrupt(thread_id=thread_id, turn_id=turn_id)
                except CodexBridgeError as exc:
                    raced = self.observe(thread_id=thread_id, turn_id=turn_id, after_cursor=deadline_cursor, wait_ms=2_000, max_events=50)
                    if raced.get("terminal"):
                        observation = raced
                    elif "no active turn to interrupt" in str(exc).lower():
                        observation = dict(raced)
                        observation.update({
                            "status": "deadline",
                            "terminal": True,
                            "agent_text": "",
                            "deadline_resolution": "app_server_reports_no_active_turn",
                        })
                    else:
                        raise
                else:
                    observation = self.observe(thread_id=thread_id, turn_id=turn_id, after_cursor=deadline_cursor, wait_ms=2_000, max_events=50)
                observation["deadline_hit"] = True
            payload["observation"] = observation
            payload["status"] = observation.get("status", payload["status"])
            payload["deadline_hit"] = bool(observation.get("deadline_hit"))
        elif wait_ms > 0:
            payload["observation"] = self.observe(thread_id=thread_id, turn_id=turn_id, after_cursor=0, wait_ms=wait_ms, max_events=50)
            payload["status"] = payload["observation"].get("status", payload["status"])
        return payload

    def _check_capacity(self, model: str) -> None:
        now = time.monotonic()
        with self._condition:
            state = self._capacity_cooldowns.get(model)
            if state and float(state.get("open_until", 0.0)) <= now:
                self._capacity_cooldowns.pop(model, None)
                state = None
            if state:
                retry_after_ms = max(1, int((float(state["open_until"]) - now) * 1000))
                raise CodexBridgeError("MODEL_CAPACITY_COOLDOWN", f"{model} recently returned a capacity error; use a different route or retry after cooldown.", retryable=True, details={"model": model, "retry_after_ms": retry_after_ms})

    def _capacity_status(self) -> list[dict[str, Any]]:
        now = time.monotonic()
        rows = []
        with self._condition:
            expired = [model for model, state in self._capacity_cooldowns.items() if float(state.get("open_until", 0.0)) <= now]
            for model in expired:
                self._capacity_cooldowns.pop(model, None)
            for model, state in sorted(self._capacity_cooldowns.items()):
                rows.append({"model": model, "retry_after_ms": max(1, int((float(state["open_until"]) - now) * 1000)), "failures": int(state.get("failures", 1))})
        return rows

    def capacity_status(self) -> list[dict[str, Any]]:
        """Return local cooldown evidence without starting the Codex sidecar."""
        return self._capacity_status()

    def _finalize_turn(self, turn_id: str) -> dict[str, Any]:
        with self._condition:
            state = self._turn_states.get(turn_id)
            if not state:
                return {}
            if state.get("finalized"):
                return dict(state)
            status = str(state.get("status", ""))
            if status not in {"completed", "failed", "interrupted"}:
                return dict(state)
            model = str(state.get("model") or "")
            error = state.get("error")
            if status == "failed" and _is_capacity_error(error):
                previous = self._capacity_cooldowns.get(model, {})
                self._capacity_cooldowns[model] = {"failures": int(previous.get("failures", 0)) + 1, "open_until": time.monotonic() + _CAPACITY_COOLDOWN_SECONDS}
            elif status == "completed":
                self._capacity_cooldowns.pop(model, None)
            started = state.get("started_monotonic")
            wall_time_ms = max(0, int((time.monotonic() - float(started)) * 1000)) if isinstance(started, (int, float)) else None
            economics = _usage_economics(state.get("token_usage"), model)
            state["wall_time_ms"] = wall_time_ms
            state["economics"] = economics
            state["finalized"] = True
            self._recent_runs.append({
                "status": status,
                "profile": state.get("profile"),
                "model": model,
                "effort": state.get("effort"),
                "wall_time_ms": wall_time_ms,
                "estimated_credits": economics.get("estimated_credits") if economics else None,
                "input_tokens": economics.get("input_tokens") if economics else None,
                "cached_input_tokens": economics.get("cached_input_tokens") if economics else None,
                "capacity_error": _is_capacity_error(error),
            })
            return dict(state)

    def _workspace(self) -> Path:
        workspace = Path(self._workspace_provider()).expanduser().resolve(strict=False)
        if not workspace.is_dir():
            raise CodexBridgeError("WORKSPACE_UNAVAILABLE", "The current MCP workspace is unavailable.")
        return workspace

    def _ensure_connected(self) -> None:
        with self._start_lock:
            if self._process is not None and self._process.poll() is None and self._initialized:
                return
            self._shutdown_dead_process()
            binary = discover_codex_binary()
            if binary is None:
                raise CodexBridgeError(
                    "CODEX_NOT_FOUND",
                    "Codex CLI was not found. Install Codex Desktop/CLI or set CODING_TOOLS_MCP_CODEX_BIN.",
                    retryable=True,
                )
            workspace = self._workspace()
            codex_home = _codex_home_hint()
            configured_servers = configured_mcp_server_names(codex_home)
            disable_args = _mcp_disable_args(configured_servers)
            child_env = sanitized_codex_env(secret_broker=self._secret_broker)
            argv_override = os.environ.get("CODING_TOOLS_MCP_CODEX_ARGV", "").strip()
            if argv_override:
                try:
                    argv = json.loads(argv_override)
                except json.JSONDecodeError as exc:
                    raise CodexBridgeError(
                        "INVALID_CODEX_ARGV",
                        "CODING_TOOLS_MCP_CODEX_ARGV must be a JSON array of argv tokens.",
                    ) from exc
                if not isinstance(argv, list) or not argv or not all(isinstance(item, str) for item in argv):
                    raise CodexBridgeError(
                        "INVALID_CODEX_ARGV",
                        "CODING_TOOLS_MCP_CODEX_ARGV must be a non-empty JSON array of strings.",
                    )
            else:
                argv = [str(binary), "app-server", "--listen", "stdio://", *disable_args]
            self._launch_argv_is_default = not bool(argv_override)
            creationflags = 0
            if os.name == "nt":
                creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
                if self._resource_governor is not None:
                    creationflags = managed_process_creationflags(creationflags)
            popen_extra: dict[str, Any] = {"creationflags": creationflags}
            if os.name != "nt" and self._resource_governor is not None:
                popen_extra["start_new_session"] = True
            admission = None
            proc = None
            try:
                if self._resource_governor is not None:
                    admission = self._resource_governor.admit(
                        command="codex app-server",
                        command_id=f"codex-app-server-{uuid.uuid4().hex}",
                        owner="codex-app-server",
                        resource_class="MEDIUM",
                    )
                proc = subprocess.Popen(
                    argv,
                    cwd=str(workspace),
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    bufsize=1,
                    env=child_env,
                    **popen_extra,
                )
                if admission is not None:
                    if os.name == "nt" and creationflags & 0x00000004:
                        setattr(proc, "_coding_tools_created_suspended", True)
                    self._resource_governor.bind_process(admission, proc)
                    self._managed_job_id = admission.job_id
            except Exception as exc:
                if proc is not None and proc.poll() is None:
                    _terminate_process_tree(proc, wait_seconds=1.0)
                if admission is not None:
                    self._resource_governor.spawn_failed(admission)
                raise CodexBridgeError(
                    "CODEX_START_FAILED",
                    f"Failed to start Codex App Server: {exc}",
                    retryable=True,
                    details={"binary": str(binary)},
                ) from exc
            self._process = proc
            self._binary = binary
            self._disabled_mcp_servers = configured_servers
            self._initialized = False
            self._stderr_tail = ""
            threading.Thread(target=self._stdout_loop, args=(proc,), name="codex-app-stdout", daemon=True).start()
            threading.Thread(target=self._stderr_loop, args=(proc,), name="codex-app-stderr", daemon=True).start()
            try:
                init = self._request_raw(
                    "initialize",
                    {
                        "clientInfo": {
                            "name": "coding-tools-mcp",
                            "title": "Coding Tools MCP Codex Bridge",
                            "version": "1.0.0",
                        },
                        "capabilities": {"experimentalApi": True},
                    },
                    timeout=_DEFAULT_REQUEST_TIMEOUT_SECONDS,
                )
                self._send_notification("initialized")
            except Exception:
                self._shutdown_dead_process(force=True)
                raise
            self._initialize_result = init if isinstance(init, dict) else {}
            self._initialized = True

    def _shutdown_dead_process(self, *, force: bool = False) -> None:
        proc = self._process
        if proc is None:
            return
        if not force and proc.poll() is None:
            return
        self._process = None
        self._disabled_mcp_servers = []
        self._initialized = False
        self._initialize_result = {}
        with self._condition:
            self._owned_threads.clear()
            self._turn_states.clear()
            self._latest_turn_by_thread.clear()
            self._condition.notify_all()
        self._fail_pending("Codex App Server exited")
        if force and proc.poll() is None:
            _terminate_process_tree(proc, wait_seconds=1.0)
        if self._managed_job_id and self._resource_governor is not None:
            self._resource_governor.complete(
                self._managed_job_id,
                lifecycle_state="terminated" if force else "exited",
                exit_code=proc.poll(),
            )
            self._managed_job_id = ""

    def _request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        self._ensure_connected()
        return self._request_raw(method, params, timeout=_DEFAULT_REQUEST_TIMEOUT_SECONDS)

    def _request_raw(self, method: str, params: dict[str, Any], *, timeout: float) -> dict[str, Any]:
        proc = self._process
        if proc is None or proc.poll() is not None:
            raise CodexBridgeError("CODEX_DISCONNECTED", "Codex App Server is not running.", retryable=True)
        with self._pending_lock:
            request_id = self._next_request_id
            self._next_request_id += 1
            slot = {"event": threading.Event(), "message": None}
            self._pending[request_id] = slot
        try:
            self._write_message({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})
            if not slot["event"].wait(timeout):
                raise CodexBridgeError(
                    "CODEX_REQUEST_TIMEOUT",
                    f"Codex App Server request timed out: {method}",
                    retryable=True,
                    details={"method": method},
                )
            message = slot.get("message")
            if not isinstance(message, dict):
                raise CodexBridgeError("CODEX_PROTOCOL_ERROR", f"Codex returned no response for {method}.")
            if "error" in message:
                error = message.get("error")
                raise CodexBridgeError(
                    "CODEX_REQUEST_FAILED",
                    f"Codex App Server rejected {method}: {_bounded(error, 2_000)}",
                    details={"method": method, "error": error},
                )
            result = message.get("result")
            return result if isinstance(result, dict) else {}
        finally:
            with self._pending_lock:
                self._pending.pop(request_id, None)

    def _send_notification(self, method: str, params: dict[str, Any] | None = None) -> None:
        payload: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            payload["params"] = params
        self._write_message(payload)

    def _write_message(self, payload: dict[str, Any]) -> None:
        proc = self._process
        if proc is None or proc.stdin is None or proc.poll() is not None:
            raise CodexBridgeError("CODEX_DISCONNECTED", "Codex App Server stdin is unavailable.", retryable=True)
        line = json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n"
        with self._write_lock:
            try:
                proc.stdin.write(line)
                proc.stdin.flush()
            except (OSError, BrokenPipeError) as exc:
                raise CodexBridgeError("CODEX_DISCONNECTED", "Codex App Server pipe closed.", retryable=True) from exc

    def _stdout_loop(self, proc: subprocess.Popen[str]) -> None:
        stream = proc.stdout
        if stream is None:
            return
        try:
            for raw in stream:
                line = raw.strip()
                if not line:
                    continue
                try:
                    message = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(message, dict):
                    continue
                if "id" in message and ("result" in message or "error" in message):
                    request_id = message.get("id")
                    if isinstance(request_id, int):
                        with self._pending_lock:
                            slot = self._pending.get(request_id)
                        if slot is not None:
                            slot["message"] = message
                            slot["event"].set()
                    continue
                if "id" in message and "method" in message:
                    self._handle_server_request(message)
                    continue
                method = message.get("method")
                if isinstance(method, str):
                    self._record_notification(method, message.get("params"))
        finally:
            if not self._closing:
                self._fail_pending("Codex App Server stdout closed")
                with self._condition:
                    self._condition.notify_all()

    def _stderr_loop(self, proc: subprocess.Popen[str]) -> None:
        stream = proc.stderr
        if stream is None:
            return
        for raw in stream:
            text = _ANSI_ESCAPE_RE.sub("", raw)
            with self._condition:
                self._stderr_tail = (self._stderr_tail + text)[-_MAX_STDERR_CHARS:]

    def _handle_server_request(self, message: dict[str, Any]) -> None:
        request_id = message.get("id")
        method = str(message.get("method", ""))
        self._append_event(method, message.get("params"), server_request=True)
        try:
            if "approval" in method.lower():
                self._write_message({"jsonrpc": "2.0", "id": request_id, "result": {"decision": "decline"}})
            else:
                self._write_message(
                    {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {"code": -32601, "message": "Coding Tools MCP bridge does not service interactive Codex host requests."},
                    }
                )
        except CodexBridgeError:
            pass

    def _record_notification(self, method: str, params: object) -> None:
        data = params if isinstance(params, dict) else {}
        thread_id = str(data.get("threadId", "")).strip() or None
        turn = data.get("turn") if isinstance(data.get("turn"), dict) else None
        turn_id = str(data.get("turnId", "")).strip() or (str(turn.get("id", "")).strip() if turn else "") or None
        item = data.get("item") if isinstance(data.get("item"), dict) else None
        with self._condition:
            if thread_id and turn_id:
                state = self._turn_states.setdefault(
                    turn_id,
                    {"thread_id": thread_id, "turn_id": turn_id, "status": "inProgress", "agent_text": "", "error": None},
                )
                self._latest_turn_by_thread[thread_id] = turn_id
                if turn:
                    state["status"] = str(turn.get("status", state.get("status", "inProgress")))
                    state["error"] = turn.get("error")
                delta = data.get("delta")
                if method == "item/agentMessage/delta" and isinstance(delta, str):
                    state["agent_text"] = _bounded(str(state.get("agent_text", "")) + delta, _MAX_AGENT_TEXT_CHARS)
                if method == "item/completed" and item and item.get("type") == "agentMessage":
                    text = item.get("text")
                    if isinstance(text, str):
                        state["agent_text"] = _bounded(text, _MAX_AGENT_TEXT_CHARS)
                if method == "thread/tokenUsage/updated" and isinstance(data.get("tokenUsage"), dict):
                    usage = data["tokenUsage"]
                    state["token_usage"] = {
                        "last": usage.get("last"),
                        "total": usage.get("total"),
                        "model_context_window": usage.get("modelContextWindow"),
                    }
                if method == "turn/completed":
                    state["status"] = str(turn.get("status", "completed")) if turn else "completed"
                    state["error"] = turn.get("error") if turn else state.get("error")
            self._append_event_locked(method, data, server_request=False)
            self._condition.notify_all()

    def _append_event(self, method: str, params: object, *, server_request: bool) -> None:
        data = params if isinstance(params, dict) else {}
        with self._condition:
            self._append_event_locked(method, data, server_request=server_request)
            self._condition.notify_all()

    def _append_event_locked(self, method: str, data: dict[str, Any], *, server_request: bool) -> None:
        thread_id = str(data.get("threadId", "")).strip() or None
        turn = data.get("turn") if isinstance(data.get("turn"), dict) else None
        turn_id = str(data.get("turnId", "")).strip() or (str(turn.get("id", "")).strip() if turn else "") or None
        item = data.get("item") if isinstance(data.get("item"), dict) else None
        self._event_cursor += 1
        event: dict[str, Any] = {
            "cursor": self._event_cursor,
            "method": method,
            "thread_id": thread_id,
            "turn_id": turn_id,
        }
        if server_request:
            event["server_request"] = True
            event["decision"] = "decline" if "approval" in method.lower() else "unsupported"
        if turn:
            event["status"] = turn.get("status")
            if turn.get("error") is not None:
                event["error"] = _bounded(turn.get("error"), 2_000)
        delta = data.get("delta")
        if isinstance(delta, str):
            event["delta"] = _bounded(delta, _MAX_EVENT_TEXT_CHARS)
        if item:
            event["item_type"] = item.get("type")
            if item.get("type") == "agentMessage" and isinstance(item.get("text"), str):
                event["text"] = _bounded(item.get("text"), _MAX_EVENT_TEXT_CHARS)
        self._events.append(event)

    def _fail_pending(self, message: str) -> None:
        with self._pending_lock:
            slots = list(self._pending.values())
        for slot in slots:
            if slot.get("message") is None:
                slot["message"] = {"error": {"code": -32099, "message": message}}
            slot["event"].set()

    def _thread_summary(self, thread: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": thread.get("id") or thread.get("sessionId"),
            "session_id": thread.get("sessionId"),
            "name": thread.get("name"),
            "preview": _bounded(thread.get("preview"), 500),
            "cwd": thread.get("cwd"),
            "created_at": thread.get("createdAt"),
            "updated_at": thread.get("updatedAt"),
            "recency_at": thread.get("recencyAt"),
            "source": thread.get("source"),
            "status": thread.get("status"),
            "forked_from_id": thread.get("forkedFromId"),
            "model_provider": thread.get("modelProvider"),
        }

    def _require_owned_thread(self, thread_id: str) -> None:
        if not thread_id:
            raise CodexBridgeError("THREAD_ID_REQUIRED", "A bridge-owned thread_id is required.")
        with self._condition:
            if thread_id not in self._owned_threads:
                raise CodexBridgeError(
                    "THREAD_NOT_OWNED",
                    "The bridge will not control an arbitrary Codex Desktop thread. Use action=run with source_thread_id to create a read-only fork first.",
                    details={"thread_id": thread_id},
                )

    def _require_owned_turn(self, thread_id: str, turn_id: str) -> None:
        with self._condition:
            state = self._turn_states.get(turn_id)
            if not state or state.get("thread_id") != thread_id:
                raise CodexBridgeError("TURN_NOT_OWNED", "The requested turn is not owned by this Codex bridge.")

    def _has_new_or_terminal(self, thread_id: str, turn_id: str, after_cursor: int) -> bool:
        state = self._turn_states.get(turn_id, {})
        if str(state.get("status", "")) in {"completed", "interrupted", "failed"}:
            return True
        return any(
            int(item.get("cursor", 0)) > after_cursor
            and item.get("thread_id") == thread_id
            and item.get("turn_id") in {None, turn_id}
            and _is_meaningful_observation_event(item)
            for item in self._events
        )
