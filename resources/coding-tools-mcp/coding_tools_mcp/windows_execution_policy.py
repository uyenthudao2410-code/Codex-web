"""Policy routing for structured Windows commands; never a host-user fallback."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any

from .errors import ToolFailure


WINDOWS_EXECUTION_MODE_ENV = "CODING_TOOLS_MCP_WINDOWS_EXECUTION_MODE"
WINDOWS_EXECUTION_MODES = frozenset({"native_first", "native_only", "isolated"})
_VERSION_TOOLS = frozenset({"git", "node", "python", "python3"})
_SHELLS = frozenset({"bash", "cmd", "powershell", "pwsh", "sh", "wscript", "cscript", "zsh"})


@dataclass(frozen=True)
class WindowsExecutionDecision:
    execution_backend: str
    isolation_level: str
    policy_decision: str
    argv: tuple[str, ...]

    def metadata(self) -> dict[str, str]:
        return {
            "execution_backend": self.execution_backend,
            "isolation_level": self.isolation_level,
            "policy_decision": self.policy_decision,
        }


def _bare_tool(value: str) -> str:
    if any(character in value for character in ("/", "\\", ":")):
        return ""
    return value.lower().removesuffix(".exe")


def _safe_git_metadata(arguments: list[str]) -> bool:
    if not arguments:
        return False
    command, *options = arguments
    if command == "status":
        return all(option in {"--short", "-s", "--porcelain", "--porcelain=v1", "--porcelain=v2", "--branch", "-b", "--untracked-files=no", "--untracked-files=normal", "--untracked-files=all"} for option in options)
    if command == "diff":
        return all(option in {"--stat", "--shortstat", "--numstat", "--name-only", "--name-status", "--cached", "--staged", "--summary", "--check", "--no-ext-diff", "--no-textconv"} for option in options)
    if command == "log":
        index = 0
        while index < len(options):
            option = options[index]
            if option in {"--oneline", "--no-decorate"}:
                index += 1
                continue
            if option in {"-n", "--max-count"} and index + 1 < len(options):
                count = options[index + 1]
                index += 2
            elif option.startswith("--max-count="):
                count = option.split("=", 1)[1]
                index += 1
            else:
                return False
            if not count.isascii() or not count.isdigit() or not 1 <= int(count) <= 100:
                return False
        return True
    return False


def safe_native_argv(argv: list[str]) -> tuple[str, ...] | None:
    """Only metadata/version shapes qualify without explicit project approval."""
    tool = _bare_tool(argv[0]) if argv else ""
    if tool in _VERSION_TOOLS and argv[1:] == ["--version"]:
        return tuple(argv)
    if tool in {"python", "python3"} and argv[1:] == ["-V"]:
        return tuple(argv)
    if tool == "git" and _safe_git_metadata(argv[1:]):
        # Repository fsmonitor and diff helpers can execute code even during a
        # metadata request. Disable those adapters independently of its config.
        options = list(argv[1:])
        if options[0] == "diff":
            options[1:1] = ["--no-ext-diff", "--no-textconv"]
        if options[0] == "log":
            options[1:1] = ["--no-show-signature", "--no-ext-diff", "--no-textconv"]
        return (argv[0], "--no-pager", "--no-optional-locks", "-c", "core.fsmonitor=false", "-c", "core.untrackedCache=false", "-c", "log.showSignature=false", "-c", "diff.submodule=short", *options)
    return None


def _approved_prefixes(value: Any) -> list[list[str]]:
    if not isinstance(value, list) or len(value) > 32:
        raise ToolFailure("WINDOWS_EXECUTION_POLICY_INVALID", "Native argv approval must be a bounded prefix array.", category="security")
    for prefix in value:
        if not isinstance(prefix, list) or not 1 <= len(prefix) <= 32:
            raise ToolFailure("WINDOWS_EXECUTION_POLICY_INVALID", "Native argv approval contains an invalid prefix.", category="security")
        if any(not isinstance(item, str) or not item or item != item.strip() or len(item.encode("utf-8")) > 2048
               or re.search(r"[\x00-\x1f\x7f]", item) or any(token in item for token in (";", "&&", "||", "`", "$(", "|", ">", "<")) for item in prefix):
            raise ToolFailure("WINDOWS_EXECUTION_POLICY_INVALID", "Native argv approval contains an unsafe argument.", category="security")
        tool = _bare_tool(prefix[0])
        if not tool or tool in _SHELLS:
            raise ToolFailure("WINDOWS_EXECUTION_POLICY_INVALID", "Native argv approval must name a direct tool.", category="security")
    return value


def decide_windows_execution(
    argv: list[str], args: dict[str, Any], *, attested_bridge: bool, approved_internal_argv: bool = False,
) -> WindowsExecutionDecision:
    if any(name in args for name in ("_windows_execution_mode", "_windows_native_argv_prefixes")) and not attested_bridge:
        raise ToolFailure("WINDOWS_EXECUTION_POLICY_DENIED", "Only the attested local bridge can supply Windows routing policy.", category="security")
    mode = args.get("_windows_execution_mode", os.environ.get(WINDOWS_EXECUTION_MODE_ENV, "native_first"))
    if not isinstance(mode, str) or mode not in WINDOWS_EXECUTION_MODES:
        raise ToolFailure("WINDOWS_EXECUTION_POLICY_INVALID", "Windows execution mode is invalid.", category="security")
    prefixes = _approved_prefixes(args.get("_windows_native_argv_prefixes", []))
    safe_argv = safe_native_argv(argv)
    approved = approved_internal_argv or any(len(prefix) <= len(argv) and argv[:len(prefix)] == prefix for prefix in prefixes)
    if mode != "isolated" and (safe_argv is not None or approved):
        return WindowsExecutionDecision("native", "process_container", "native_safe_command" if safe_argv is not None else "native_explicit_approval", safe_argv or tuple(argv))
    if mode == "native_only":
        raise ToolFailure("NATIVE_EXECUTION_NOT_APPROVED", "This command requires explicit native approval or an isolated runner.", category="permission", details={"execution_started": False, "policy_decision": "native_unapproved_denied"})
    return WindowsExecutionDecision("isolated", "hypervisor", "isolated_preferred" if mode == "isolated" else "isolated_unapproved_command", tuple(argv))
