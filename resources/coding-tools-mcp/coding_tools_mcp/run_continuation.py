from __future__ import annotations

"""Bounded durable execution grants and proposal contracts for an existing RUN.

This is deliberately not a second Task/Goal state machine.  The model receives
only a constrained proposal contract; workflow, patch, check, Job and final
acceptance authority remain in their established MCP owners.
"""

import hashlib
import json
import re
import sqlite3
import time
from typing import Any, Iterable

from .errors import ToolFailure
from .ledger_event_chain import append_hash_chained_event


RUN_CONTINUATION_SCHEMA_VERSION = 2
RUN_CONTINUATION_ROUTE = "sol_xhigh"
RUN_CONTINUATION_PROFILE = "continuation_proposal"
RUN_CONTINUATION_MAX_DURATION_SECONDS = 15 * 60
RUN_CONTINUATION_MAX_DECISION_TURNS = 12
RUN_CONTINUATION_MAX_PATCH_ATTEMPTS = 3
RUN_CONTINUATION_LEASE_SECONDS = 60
RUN_CONTINUATION_MAX_EVIDENCE_REQUESTS = 16
RUN_CONTINUATION_MAX_REPLACEMENTS = 32
RUN_CONTINUATION_MAX_NEW_FILES = 16

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_OPAQUE_RE = re.compile(r"^[A-Za-z0-9._:-]{1,256}$")
_SENSITIVE_RE = re.compile(r"(authorization|credential|password|passwd|secret|token|api[_-]?key|private[_-]?key)", re.I)
_SENSITIVE_CONTENT_ASSIGNMENT_RE = re.compile(
    r"(?i)[\"']?(?:api[_-]?key|access[_-]?token|auth[_-]?token|client[_-]?secret|private[_-]?key|secret|password|token)[\"']?\s*[:=]"
)
_SENSITIVE_CONTENT_AUTHORIZATION_RE = re.compile(r"(?i)\bauthorization\s*:\s*(?:bearer|token)\b")
_SENSITIVE_CONTENT_PRIVATE_KEY_RE = re.compile(r"(?i)-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----")
_FORBIDDEN_SCOPE_PARTS = frozenset({".git", ".coding-tools", "node_modules", "__pycache__", "dist"})
_SHELL_PROGRAMS = frozenset({"bash", "cmd", "cmd.exe", "powershell", "pwsh", "sh", "zsh"})


def _proposal_string_schema(*, maximum: int, pattern: str | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"type": "string", "minLength": 1, "maxLength": maximum}
    if pattern:
        result["pattern"] = pattern
    return result


_PROPOSAL_SHA256 = _proposal_string_schema(maximum=64, pattern=r"^[0-9a-f]{64}$")
_PROPOSAL_PATH = _proposal_string_schema(maximum=2_000)
_PROPOSAL_REASON = _proposal_string_schema(maximum=2_000)
_PROPOSAL_REPLACEMENT = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "path": _PROPOSAL_PATH,
        "old": _proposal_string_schema(maximum=32_000),
        "new": {"type": "string", "maxLength": 32_000},
    },
    "required": ["path", "old", "new"],
}
_PROPOSAL_NEW_FILE = {
    "type": "object",
    "additionalProperties": False,
    "properties": {"path": _PROPOSAL_PATH, "content": {"type": "string", "maxLength": 48_000}},
    "required": ["path", "content"],
}


def _proposal_variant(kind: str, properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "kind": {"type": "string", "enum": [kind]},
            "reason": _PROPOSAL_REASON,
            "evidence_hash": _PROPOSAL_SHA256,
            **properties,
        },
        "required": ["kind", "reason", "evidence_hash", *required],
    }


RUN_CONTINUATION_PROPOSAL_SCHEMA: dict[str, Any] = {
    "oneOf": [
        _proposal_variant(
            "READ",
            {
                "read_requests": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": RUN_CONTINUATION_MAX_EVIDENCE_REQUESTS,
                    "items": {"type": "object", "additionalProperties": False, "properties": {"path": _PROPOSAL_PATH}, "required": ["path"]},
                },
            },
            ["read_requests"],
        ),
        _proposal_variant(
            "PATCH",
            {
                "replacements": {"type": "array", "maxItems": RUN_CONTINUATION_MAX_REPLACEMENTS, "items": _PROPOSAL_REPLACEMENT},
                "new_files": {"type": "array", "maxItems": RUN_CONTINUATION_MAX_NEW_FILES, "items": _PROPOSAL_NEW_FILE},
                "selected_check_hashes": {"type": "array", "minItems": 1, "maxItems": 16, "items": _PROPOSAL_SHA256},
            },
            ["selected_check_hashes"],
        ),
        _proposal_variant("READY", {}, []),
        _proposal_variant("BLOCKED", {}, []),
    ],
}


class RunContinuationError(ValueError):
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


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _now_ms() -> int:
    return int(time.time() * 1_000)


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _event_sanitize(value: Any, *, key: str = "") -> Any:
    """Events in this module carry identifiers and hashes only."""
    if _SENSITIVE_RE.search(key):
        return "[REDACTED]"
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return value[:512]
    if isinstance(value, dict):
        return {str(name)[:128]: _event_sanitize(item, key=str(name)) for name, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_event_sanitize(item) for item in value[:100]]
    return str(value)[:512]


def _bounded(value: Any, limit: int = 512) -> str:
    text = str(value or "").strip()
    return text if len(text) <= limit else text[:limit]


def _contains_sensitive_model_content(value: Any) -> bool:
    """Fail closed before source or Problem material leaves MCP for a proposal model.

    This is intentionally a detection boundary, not a redactor. Rewriting
    source silently would invalidate the evidence hash and could cause a model
    to propose a patch against context it never actually saw.
    """
    if isinstance(value, str):
        return bool(
            _SENSITIVE_CONTENT_ASSIGNMENT_RE.search(value)
            or _SENSITIVE_CONTENT_AUTHORIZATION_RE.search(value)
            or _SENSITIVE_CONTENT_PRIVATE_KEY_RE.search(value)
        )
    if isinstance(value, dict):
        return any(_contains_sensitive_model_content(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_sensitive_model_content(item) for item in value)
    return False


def _require_opaque(value: Any, field: str, *, limit: int = 256) -> str:
    text = _bounded(value, limit)
    if not text or not _OPAQUE_RE.fullmatch(text):
        raise RunContinuationError("RUN_CONTINUATION_POLICY_INVALID", f"{field} must be a bounded opaque identifier.")
    return text


def _require_sha256(value: Any, field: str) -> str:
    text = _bounded(value, 64).lower()
    if not _SHA256_RE.fullmatch(text):
        raise RunContinuationError("RUN_CONTINUATION_POLICY_INVALID", f"{field} must be a SHA-256 hex digest.")
    return text


def _normalize_path(value: Any, field: str) -> str:
    raw = _bounded(value, 2_000).replace("\\", "/")
    if not raw or raw.startswith("/") or ":" in raw:
        raise RunContinuationError("RUN_CONTINUATION_SCOPE_INVALID", f"{field} must be a relative workspace path.")
    parts = tuple(part for part in raw.split("/") if part)
    if not parts or any(part in {".", ".."} for part in parts):
        raise RunContinuationError("RUN_CONTINUATION_SCOPE_INVALID", f"{field} contains an unsafe path traversal.")
    lowered = {part.lower() for part in parts}
    if lowered.intersection(_FORBIDDEN_SCOPE_PARTS) or any(_SENSITIVE_RE.search(part) for part in parts):
        raise RunContinuationError("RUN_CONTINUATION_SCOPE_PROTECTED", f"{field} includes a protected runtime or sensitive path.")
    return "/".join(parts)


def _normalize_paths(value: Any, field: str, *, minimum: int = 0) -> list[str]:
    if not isinstance(value, list):
        raise RunContinuationError("RUN_CONTINUATION_POLICY_INVALID", f"{field} must be an array of relative paths.")
    normalized = sorted({_normalize_path(item, field) for item in value})
    if len(normalized) < minimum:
        raise RunContinuationError("RUN_CONTINUATION_SCOPE_INVALID", f"{field} needs at least {minimum} path(s).")
    return normalized


def _normalize_effect_artifact_path(value: Any, field: str) -> str:
    """Allow only the dedicated retained backup subtree, never generic .coding-tools writes."""
    raw = _bounded(value, 2_000).replace("\\", "/")
    parts = tuple(part for part in raw.split("/") if part)
    if (
        len(parts) < 4
        or parts[:3] != (".coding-tools", "orchestration", "continuation-effects")
        or raw.startswith("/")
        or ":" in raw
        or any(part in {".", ".."} or _SENSITIVE_RE.search(part) for part in parts[3:])
    ):
        raise RunContinuationError("RUN_CONTINUATION_EFFECT_INVALID", f"{field} is outside the dedicated retained effect-backup subtree.")
    return "/".join(parts)


def _normalize_technical_replan(value: Any) -> dict[str, Any]:
    """Keep model-visible failed-proof feedback bounded and reconstructable.

    This payload is produced by the deterministic proof owner, never by the
    proposal model.  It is persisted only while the next proposal is pending
    so its evidence hash can be recomputed after an ordinary driver restart.
    """
    if value is None:
        return {}
    if not isinstance(value, dict) or set(value) != {
        "failure", "check_id", "check_definition_hash", "proof_id", "exit_code", "summary",
    }:
        raise RunContinuationError("RUN_CONTINUATION_REPLAN_INVALID", "Technical replan feedback has an invalid shape.")
    exit_code = value.get("exit_code")
    if exit_code is not None and (isinstance(exit_code, bool) or not isinstance(exit_code, int)):
        raise RunContinuationError("RUN_CONTINUATION_REPLAN_INVALID", "Technical replan exit_code must be an integer or null.")
    return {
        "failure": _require_opaque(value.get("failure"), "technical_replan.failure", limit=128),
        "check_id": _require_opaque(value.get("check_id"), "technical_replan.check_id", limit=128),
        "check_definition_hash": _require_sha256(value.get("check_definition_hash"), "technical_replan.check_definition_hash"),
        "proof_id": _bounded(value.get("proof_id"), 256),
        "exit_code": exit_code,
        "summary": _bounded(value.get("summary"), 2_000),
    }


def parse_run_continuation_proposal(
    value: Any,
    *,
    expected_evidence_hash: str,
    read_paths: Iterable[str],
    write_paths: Iterable[str],
    protected_paths: Iterable[str],
    approved_check_hashes: Iterable[str],
) -> dict[str, Any]:
    """Fail closed on an App Server proposal before any effect is considered.

    JSON Schema constrains the provider response, but this validator is the
    authoritative boundary: it verifies the current evidence binding and the
    immutable continuation policy after transport decoding.
    """
    if not isinstance(value, dict):
        raise RunContinuationError("RUN_CONTINUATION_PROPOSAL_INVALID", "The continuation proposal must be an object.")
    kind = _bounded(value.get("kind"), 16).upper()
    expected = _require_sha256(expected_evidence_hash, "expected_evidence_hash")
    provided = _require_sha256(value.get("evidence_hash"), "proposal.evidence_hash")
    if provided != expected:
        raise RunContinuationError(
            "RUN_CONTINUATION_EVIDENCE_STALE",
            "The model proposal was generated from different evidence; discard it instead of applying it.",
        )
    reason = _bounded(value.get("reason"), 2_000)
    if not reason:
        raise RunContinuationError("RUN_CONTINUATION_PROPOSAL_INVALID", "The continuation proposal requires a bounded reason.")
    allowed_read = {_normalize_path(item, "read scope") for item in read_paths}
    allowed_write = {_normalize_path(item, "write scope") for item in write_paths}
    protected = {_normalize_path(item, "protected scope") for item in protected_paths}
    approved = {_require_sha256(item, "approved check hash") for item in approved_check_hashes}
    common = {"kind", "reason", "evidence_hash"}

    if kind == "READ":
        if set(value) != common.union({"read_requests"}):
            raise RunContinuationError("RUN_CONTINUATION_PROPOSAL_INVALID", "READ contains unsupported fields.")
        requests = value.get("read_requests")
        if not isinstance(requests, list) or not requests or len(requests) > RUN_CONTINUATION_MAX_EVIDENCE_REQUESTS:
            raise RunContinuationError("RUN_CONTINUATION_PROPOSAL_INVALID", "READ requires 1 to 16 exact read requests.")
        normalized: list[dict[str, str]] = []
        for request in requests:
            if not isinstance(request, dict) or set(request) != {"path"}:
                raise RunContinuationError("RUN_CONTINUATION_PROPOSAL_INVALID", "Each READ request must contain exactly path.")
            path = _normalize_path(request.get("path"), "READ path")
            if path not in allowed_read:
                raise RunContinuationError("RUN_CONTINUATION_READ_SCOPE_DENIED", "A READ request is outside the immutable read scope.", details={"path": path})
            normalized.append({"path": path})
        if len({item["path"] for item in normalized}) != len(normalized):
            raise RunContinuationError("RUN_CONTINUATION_PROPOSAL_INVALID", "READ requests must not repeat a path.")
        return {"kind": kind, "reason": reason, "evidence_hash": provided, "read_requests": normalized}

    if kind == "PATCH":
        permitted = common.union({"replacements", "new_files", "selected_check_hashes"})
        if set(value).difference(permitted):
            raise RunContinuationError("RUN_CONTINUATION_PROPOSAL_INVALID", "PATCH contains unsupported fields.")
        raw_replacements = value.get("replacements") or []
        raw_new_files = value.get("new_files") or []
        if not isinstance(raw_replacements, list) or not isinstance(raw_new_files, list):
            raise RunContinuationError("RUN_CONTINUATION_PROPOSAL_INVALID", "PATCH replacements and new_files must be arrays.")
        if not raw_replacements and not raw_new_files:
            raise RunContinuationError("RUN_CONTINUATION_PROPOSAL_INVALID", "PATCH must contain at least one replacement or new file.")
        if len(raw_replacements) > RUN_CONTINUATION_MAX_REPLACEMENTS or len(raw_new_files) > RUN_CONTINUATION_MAX_NEW_FILES:
            raise RunContinuationError("RUN_CONTINUATION_PROPOSAL_INVALID", "PATCH exceeds the bounded change count.")
        replacements: list[dict[str, str]] = []
        new_files: list[dict[str, str]] = []
        seen: set[str] = set()
        for replacement in raw_replacements:
            if not isinstance(replacement, dict) or set(replacement) != {"path", "old", "new"}:
                raise RunContinuationError("RUN_CONTINUATION_PROPOSAL_INVALID", "Each replacement must contain exactly path, old and new.")
            path = _normalize_path(replacement.get("path"), "PATCH path")
            old, new = str(replacement.get("old") or ""), str(replacement.get("new") or "")
            if path not in allowed_write or path in protected:
                raise RunContinuationError("RUN_CONTINUATION_SCOPE_DENIED", "PATCH replacement exceeds the immutable write scope.", details={"path": path})
            if not old or len(old) > 32_000 or len(new) > 32_000 or path in seen:
                raise RunContinuationError("RUN_CONTINUATION_PROPOSAL_INVALID", "PATCH replacement text/path is invalid or duplicated.")
            seen.add(path)
            replacements.append({"path": path, "old": old, "new": new})
        for new_file in raw_new_files:
            if not isinstance(new_file, dict) or set(new_file) != {"path", "content"}:
                raise RunContinuationError("RUN_CONTINUATION_PROPOSAL_INVALID", "Each new file must contain exactly path and content.")
            path, content = _normalize_path(new_file.get("path"), "PATCH new-file path"), str(new_file.get("content") or "")
            if path not in allowed_write or path in protected:
                raise RunContinuationError("RUN_CONTINUATION_SCOPE_DENIED", "PATCH new-file exceeds the immutable write scope.", details={"path": path})
            if len(content) > 48_000 or path in seen:
                raise RunContinuationError("RUN_CONTINUATION_PROPOSAL_INVALID", "PATCH new-file content/path is invalid or duplicated.")
            seen.add(path)
            new_files.append({"path": path, "content": content})
        raw_hashes = value.get("selected_check_hashes")
        if not isinstance(raw_hashes, list) or not raw_hashes or len(raw_hashes) > 16:
            raise RunContinuationError("RUN_CONTINUATION_PROPOSAL_INVALID", "PATCH requires 1 to 16 selected approved check hashes.")
        selected = [_require_sha256(item, "selected_check_hash") for item in raw_hashes]
        if len(set(selected)) != len(selected) or any(item not in approved for item in selected):
            raise RunContinuationError("RUN_CONTINUATION_CHECK_DENIED", "PATCH selected a check outside the immutable policy.")
        if set(selected) != approved:
            raise RunContinuationError(
                "RUN_CONTINUATION_REQUIRED_CHECK_MISSING",
                "Every approved check is mandatory continuation proof; the model cannot choose a sufficient subset.",
                details={"required_count": len(approved), "selected_count": len(selected)},
            )
        return {"kind": kind, "reason": reason, "evidence_hash": provided, "replacements": replacements, "new_files": new_files, "selected_check_hashes": selected}

    if kind in {"READY", "BLOCKED"}:
        if set(value) != common:
            raise RunContinuationError("RUN_CONTINUATION_PROPOSAL_INVALID", f"{kind} contains unsupported fields.")
        return {"kind": kind, "reason": reason, "evidence_hash": provided}
    raise RunContinuationError("RUN_CONTINUATION_PROPOSAL_INVALID", "Proposal kind must be READ, PATCH, READY or BLOCKED.")


def _normalize_check(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {
        "check_id", "argv", "cwd", "environment_hash", "definition_hash"
    }:
        raise RunContinuationError(
            "RUN_CONTINUATION_CHECK_INVALID",
            "Each approved check must contain exactly check_id, argv, cwd, environment_hash, and definition_hash.",
        )
    check_id = _require_opaque(value.get("check_id"), "approved_checks.check_id", limit=128)
    argv = value.get("argv")
    if not isinstance(argv, list) or not argv or len(argv) > 32 or any(not isinstance(item, str) or not item.strip() for item in argv):
        raise RunContinuationError("RUN_CONTINUATION_CHECK_INVALID", "approved_checks.argv must be a non-empty bounded argv array.")
    argv_values = [str(item).strip() for item in argv]
    if len("\0".join(argv_values).encode("utf-8")) > 8_192:
        raise RunContinuationError("RUN_CONTINUATION_CHECK_INVALID", "approved_checks.argv is too large.")
    if argv_values[0].lower() in _SHELL_PROGRAMS:
        raise RunContinuationError("RUN_CONTINUATION_CHECK_INVALID", "Approved checks must use structured argv, not a shell program.")
    if any(_SENSITIVE_RE.search(item) for item in argv_values):
        raise RunContinuationError("RUN_CONTINUATION_CHECK_INVALID", "Approved checks cannot contain secret-like arguments.")
    cwd = _normalize_path(value.get("cwd"), "approved_checks.cwd")
    environment_hash = _require_sha256(value.get("environment_hash"), "approved_checks.environment_hash")
    definition_hash = _require_sha256(value.get("definition_hash"), "approved_checks.definition_hash")
    definition = {
        "check_id": check_id,
        "argv": argv_values,
        "cwd": cwd,
        "environment_hash": environment_hash,
    }
    calculated = hashlib.sha256(_canonical_json(definition).encode("utf-8")).hexdigest()
    if calculated != definition_hash:
        raise RunContinuationError(
            "RUN_CONTINUATION_CHECK_HASH_MISMATCH",
            "The supplied check definition_hash does not bind the exact approved argv/cwd/environment hash.",
            details={"check_id": check_id},
        )
    return {**definition, "definition_hash": definition_hash}


def build_run_continuation_policy(
    request: dict[str, Any],
    *,
    run_id: str,
    workspace_id: str,
    problem_id: str,
    problem_revision: int,
    contract_fingerprint: str,
    tool_contract_sha256: str,
    runtime_behavior_fingerprint: str,
    activation_epoch_id: str,
    activation_admission: str,
    issuer_client_id: str,
) -> dict[str, Any]:
    """Build the immutable, content-free policy that the driver will later consume."""
    if not isinstance(request, dict) or request.get("action") != "grant":
        raise RunContinuationError("RUN_CONTINUATION_REQUEST_INVALID", "continuation.action must be grant.")
    allowed_keys = {
        "action", "read_paths", "write_paths", "protected_paths", "approved_checks",
        "max_duration_seconds", "max_decision_turns", "max_patch_attempts",
    }
    unexpected = sorted(set(request).difference(allowed_keys))
    if unexpected:
        raise RunContinuationError(
            "RUN_CONTINUATION_REQUEST_INVALID",
            "Continuation grant requests cannot select their own route, profile, authority, or environment.",
            details={"unexpected": unexpected},
        )
    normalized_run = _require_opaque(run_id, "run_id")
    normalized_workspace = _require_opaque(workspace_id, "workspace_id", limit=512)
    normalized_problem = _require_opaque(problem_id, "problem_id")
    if isinstance(problem_revision, bool) or not isinstance(problem_revision, int) or problem_revision < 1:
        raise RunContinuationError("RUN_CONTINUATION_POLICY_INVALID", "problem_revision must be a positive integer.")
    read_paths = _normalize_paths(request.get("read_paths"), "read_paths", minimum=1)
    write_paths = _normalize_paths(request.get("write_paths"), "write_paths", minimum=1)
    protected_paths = _normalize_paths(request.get("protected_paths"), "protected_paths")
    overlap = sorted(set(write_paths).intersection(protected_paths))
    if overlap:
        raise RunContinuationError(
            "RUN_CONTINUATION_SCOPE_PROTECTED",
            "write_paths overlap protected_paths.",
            details={"paths": overlap},
        )
    checks_raw = request.get("approved_checks")
    if not isinstance(checks_raw, list) or not checks_raw or len(checks_raw) > 16:
        raise RunContinuationError("RUN_CONTINUATION_CHECK_INVALID", "approved_checks must contain 1 to 16 exact command definitions.")
    checks = [_normalize_check(item) for item in checks_raw]
    check_ids = [str(item["check_id"]) for item in checks]
    check_hashes = [str(item["definition_hash"]) for item in checks]
    if len(set(check_ids)) != len(check_ids) or len(set(check_hashes)) != len(check_hashes):
        raise RunContinuationError("RUN_CONTINUATION_CHECK_INVALID", "approved_checks must have unique ids and definition hashes.")

    def bounded_int(name: str, ceiling: int) -> int:
        raw = request.get(name)
        if isinstance(raw, bool) or not isinstance(raw, int) or raw < 1 or raw > ceiling:
            raise RunContinuationError(
                "RUN_CONTINUATION_BUDGET_INVALID",
                f"{name} must be an integer from 1 through {ceiling}; continuation grants never auto-escalate budgets.",
            )
        return raw

    return {
        "schema_version": RUN_CONTINUATION_SCHEMA_VERSION,
        "run_id": normalized_run,
        "workspace_id": normalized_workspace,
        "problem_id": normalized_problem,
        "problem_revision": problem_revision,
        "contract_fingerprint": _require_sha256(contract_fingerprint, "contract_fingerprint"),
        "tool_contract_sha256": _require_sha256(tool_contract_sha256, "tool_contract_sha256"),
        "runtime_behavior_fingerprint": _require_sha256(runtime_behavior_fingerprint, "runtime_behavior_fingerprint"),
        "activation_epoch_id": _require_opaque(activation_epoch_id, "activation_epoch_id"),
        "activation_admission": _require_opaque(activation_admission, "activation_admission", limit=32),
        "issuer_client_id": _require_opaque(issuer_client_id, "issuer_client_id"),
        "route": RUN_CONTINUATION_ROUTE,
        "profile": RUN_CONTINUATION_PROFILE,
        "acceptance_mode": "controller_required",
        "restart_policy": "official_runtime_admission_required",
        "read_paths": read_paths,
        "write_paths": write_paths,
        "protected_paths": protected_paths,
        "approved_checks": checks,
        "max_duration_seconds": bounded_int("max_duration_seconds", RUN_CONTINUATION_MAX_DURATION_SECONDS),
        "max_decision_turns": bounded_int("max_decision_turns", RUN_CONTINUATION_MAX_DECISION_TURNS),
        "max_patch_attempts": bounded_int("max_patch_attempts", RUN_CONTINUATION_MAX_PATCH_ATTEMPTS),
    }


def _policy_projection(policy: dict[str, Any]) -> dict[str, Any]:
    """Operator status intentionally exposes check identities/hashes, not argv."""
    return {
        "schema_version": policy.get("schema_version"),
        "run_id": policy.get("run_id"),
        "workspace_id": policy.get("workspace_id"),
        "problem_id": policy.get("problem_id"),
        "problem_revision": policy.get("problem_revision"),
        "contract_fingerprint": policy.get("contract_fingerprint"),
        "tool_contract_sha256": policy.get("tool_contract_sha256"),
        "runtime_behavior_fingerprint": policy.get("runtime_behavior_fingerprint"),
        "activation_epoch_id": policy.get("activation_epoch_id"),
        "activation_admission": policy.get("activation_admission"),
        "route": policy.get("route"),
        "profile": policy.get("profile"),
        "acceptance_mode": policy.get("acceptance_mode"),
        "restart_policy": policy.get("restart_policy"),
        "read_paths": list(policy.get("read_paths") or []),
        "write_paths": list(policy.get("write_paths") or []),
        "protected_paths": list(policy.get("protected_paths") or []),
        "approved_checks": [
            {"check_id": item.get("check_id"), "cwd": item.get("cwd"), "definition_hash": item.get("definition_hash")}
            for item in policy.get("approved_checks") or []
            if isinstance(item, dict)
        ],
        "budgets": {
            "max_duration_seconds": policy.get("max_duration_seconds"),
            "max_decision_turns": policy.get("max_decision_turns"),
            "max_patch_attempts": policy.get("max_patch_attempts"),
        },
    }


class RunContinuationLedgerMixin:
    """Same-ledger grant/cursor projection used by the continuation driver."""

    @staticmethod
    def _run_continuation_ensure_schema(connection: sqlite3.Connection) -> None:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS run_continuations (
                run_id TEXT PRIMARY KEY REFERENCES runs(run_id) ON DELETE CASCADE,
                workspace_id TEXT NOT NULL,
                problem_id TEXT NOT NULL,
                problem_revision INTEGER NOT NULL CHECK(problem_revision>=1),
                policy_json TEXT NOT NULL,
                policy_sha256 TEXT NOT NULL,
                issuer_receipt_sha256 TEXT NOT NULL,
                policy_revision INTEGER NOT NULL DEFAULT 1,
                enabled INTEGER NOT NULL DEFAULT 1,
                pause_reason TEXT NOT NULL DEFAULT '',
                revoked_at TEXT,
                driver_generation INTEGER NOT NULL DEFAULT 0,
                claimed_runtime_instance TEXT NOT NULL DEFAULT '',
                claim_expires_at_unix_ms INTEGER NOT NULL DEFAULT 0,
                next_action_seq INTEGER NOT NULL DEFAULT 1,
                consumed_event_seq INTEGER NOT NULL DEFAULT 0,
                pending_action_id TEXT NOT NULL DEFAULT '',
                pending_evidence_hash TEXT NOT NULL DEFAULT '',
                pending_evidence_paths_json TEXT NOT NULL DEFAULT '[]',
                pending_replan_json TEXT NOT NULL DEFAULT '{}',
                pending_dispatch_action_id TEXT NOT NULL DEFAULT '',
                pending_job_id TEXT NOT NULL DEFAULT '',
                pending_patch_action_id TEXT NOT NULL DEFAULT '',
                lane_id TEXT NOT NULL DEFAULT '',
                thread_id TEXT NOT NULL DEFAULT '',
                last_turn_id TEXT NOT NULL DEFAULT '',
                remaining_decision_turns INTEGER NOT NULL,
                remaining_patch_attempts INTEGER NOT NULL,
                expires_at_unix_ms INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_run_continuations_eligible
                ON run_continuations(enabled, expires_at_unix_ms, claim_expires_at_unix_ms);
            CREATE TABLE IF NOT EXISTS run_continuation_effects (
                action_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
                driver_generation INTEGER NOT NULL,
                effect_kind TEXT NOT NULL,
                manifest_json TEXT NOT NULL,
                manifest_sha256 TEXT NOT NULL,
                status TEXT NOT NULL,
                recovery_reason TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_run_continuation_effects_run
                ON run_continuation_effects(run_id, status);
            """
        )
        columns = {str(row["name"]) for row in connection.execute("PRAGMA table_info(run_continuations)").fetchall()}
        if "pending_evidence_hash" not in columns:
            connection.execute("ALTER TABLE run_continuations ADD COLUMN pending_evidence_hash TEXT NOT NULL DEFAULT ''")
        if "pending_evidence_paths_json" not in columns:
            connection.execute("ALTER TABLE run_continuations ADD COLUMN pending_evidence_paths_json TEXT NOT NULL DEFAULT '[]'")
        if "pending_dispatch_action_id" not in columns:
            connection.execute("ALTER TABLE run_continuations ADD COLUMN pending_dispatch_action_id TEXT NOT NULL DEFAULT ''")
        if "pending_replan_json" not in columns:
            connection.execute("ALTER TABLE run_continuations ADD COLUMN pending_replan_json TEXT NOT NULL DEFAULT '{}'")
        if "pending_patch_action_id" not in columns:
            connection.execute("ALTER TABLE run_continuations ADD COLUMN pending_patch_action_id TEXT NOT NULL DEFAULT ''")

    @staticmethod
    def _normalize_effect_manifest(value: Any) -> dict[str, Any]:
        if not isinstance(value, dict) or set(value) != {"files", "backup_root"}:
            raise RunContinuationError("RUN_CONTINUATION_EFFECT_INVALID", "Effect manifest must contain exactly files and backup_root.")
        backup_root = _normalize_effect_artifact_path(value.get("backup_root"), "effect backup_root")
        files = value.get("files")
        if not isinstance(files, list) or not files or len(files) > RUN_CONTINUATION_MAX_REPLACEMENTS + RUN_CONTINUATION_MAX_NEW_FILES:
            raise RunContinuationError("RUN_CONTINUATION_EFFECT_INVALID", "Effect manifest requires a bounded non-empty file list.")
        normalized: list[dict[str, str]] = []
        seen: set[str] = set()
        for item in files:
            if not isinstance(item, dict) or set(item) != {"path", "preimage_sha256", "postimage_sha256", "backup_path"}:
                raise RunContinuationError("RUN_CONTINUATION_EFFECT_INVALID", "Each effect manifest row must contain exact path, preimage, postimage and backup path.")
            path = _normalize_path(item.get("path"), "effect path")
            preimage = str(item.get("preimage_sha256") or "")
            if preimage != "absent":
                preimage = _require_sha256(preimage, "effect preimage_sha256")
            postimage = _require_sha256(item.get("postimage_sha256"), "effect postimage_sha256")
            backup_path = _normalize_effect_artifact_path(item.get("backup_path"), "effect backup_path")
            if not backup_path.startswith(backup_root + "/"):
                raise RunContinuationError("RUN_CONTINUATION_EFFECT_INVALID", "Effect backup_path must stay beneath the action backup_root.")
            if path in seen:
                raise RunContinuationError("RUN_CONTINUATION_EFFECT_INVALID", "Effect manifest repeats a path.")
            seen.add(path)
            normalized.append({"path": path, "preimage_sha256": preimage, "postimage_sha256": postimage, "backup_path": backup_path})
        return {"files": sorted(normalized, key=lambda item: item["path"]), "backup_root": backup_root}

    def prepare_run_continuation_effect(
        self,
        *,
        run_id: str,
        driver_generation: int,
        runtime_instance_id: str,
        action_id: str,
        effect_kind: str,
        manifest: dict[str, Any],
    ) -> dict[str, Any]:
        normalized_run = _require_opaque(run_id, "run_id")
        normalized_action = _require_sha256(action_id, "action_id")
        kind = _require_opaque(effect_kind, "effect_kind", limit=64)
        normalized_manifest = self._normalize_effect_manifest(manifest)
        manifest_json = _canonical_json(normalized_manifest)
        manifest_sha = hashlib.sha256(manifest_json.encode("utf-8")).hexdigest()
        now = _utc_now()
        with self._lock, self._connect() as connection:
            self._run_continuation_ensure_schema(connection)
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT * FROM run_continuations WHERE run_id=?", (normalized_run,)).fetchone()
            record = self._run_continuation_row(row) if row is not None else None
            self._assert_run_continuation_row(
                record,
                run_id=normalized_run,
                driver_generation=driver_generation,
                runtime_instance_id=runtime_instance_id,
            )
            if record is None or record["pending_action_id"] != normalized_action:
                raise RunContinuationError("RUN_CONTINUATION_ACTION_MISMATCH", "Only the exact pending action may prepare a filesystem effect.")
            existing = connection.execute("SELECT * FROM run_continuation_effects WHERE action_id=?", (normalized_action,)).fetchone()
            if existing is not None:
                if str(existing["manifest_sha256"]) != manifest_sha or str(existing["effect_kind"]) != kind:
                    raise RunContinuationError("RUN_CONTINUATION_EFFECT_CONFLICT", "The pending action already has a different immutable effect journal.")
                connection.commit()
                return {"prepared": False, "idempotent": True, "status": str(existing["status"]), "manifest_sha256": manifest_sha}
            connection.execute(
                "INSERT INTO run_continuation_effects(action_id,run_id,driver_generation,effect_kind,manifest_json,manifest_sha256,status,recovery_reason,created_at,updated_at) VALUES(?,?,?,?,?,?,'pending','',?,?)",
                (normalized_action, normalized_run, int(driver_generation), kind, manifest_json, manifest_sha, now, now),
            )
            self._append_run_continuation_event(
                connection,
                run_id=normalized_run,
                event_type="run_continuation_effect_prepared",
                payload={"action_id": normalized_action, "driver_generation": driver_generation, "effect_kind": kind, "manifest_sha256": manifest_sha},
            )
            connection.commit()
        return {"prepared": True, "idempotent": False, "status": "pending", "manifest_sha256": manifest_sha}

    def get_run_continuation_effect(self, action_id: str) -> dict[str, Any] | None:
        normalized_action = _require_sha256(action_id, "action_id")
        with self._lock, self._connect() as connection:
            self._run_continuation_ensure_schema(connection)
            row = connection.execute("SELECT * FROM run_continuation_effects WHERE action_id=?", (normalized_action,)).fetchone()
        if row is None:
            return None
        return {
            "action_id": str(row["action_id"]), "run_id": str(row["run_id"]), "driver_generation": int(row["driver_generation"]),
            "effect_kind": str(row["effect_kind"]), "manifest": json.loads(str(row["manifest_json"])),
            "manifest_sha256": str(row["manifest_sha256"]), "status": str(row["status"]),
            "recovery_reason": str(row["recovery_reason"]), "created_at": str(row["created_at"]), "updated_at": str(row["updated_at"]),
        }

    def record_run_continuation_effect_observation(
        self,
        *,
        run_id: str,
        driver_generation: int,
        runtime_instance_id: str,
        action_id: str,
        status: str,
        recovery_reason: str = "",
    ) -> dict[str, Any]:
        normalized_run, normalized_action = _require_opaque(run_id, "run_id"), _require_sha256(action_id, "action_id")
        target = _bounded(status, 32).lower()
        if target not in {"applied", "not_applied", "recovery_required"}:
            raise RunContinuationError("RUN_CONTINUATION_EFFECT_INVALID", "Effect observation status is invalid.")
        reason = _bounded(recovery_reason, 512)
        now = _utc_now()
        with self._lock, self._connect() as connection:
            self._run_continuation_ensure_schema(connection)
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT * FROM run_continuations WHERE run_id=?", (normalized_run,)).fetchone()
            record = self._run_continuation_row(row) if row is not None else None
            self._assert_run_continuation_row(
                record,
                run_id=normalized_run,
                driver_generation=driver_generation,
                runtime_instance_id=runtime_instance_id,
            )
            effect = connection.execute("SELECT * FROM run_continuation_effects WHERE action_id=? AND run_id=?", (normalized_action, normalized_run)).fetchone()
            if effect is None:
                raise RunContinuationError("RUN_CONTINUATION_EFFECT_MISSING", "No prepared effect journal exists for the pending action.")
            previous = str(effect["status"])
            if previous not in {"pending", target}:
                raise RunContinuationError("RUN_CONTINUATION_EFFECT_CONFLICT", "Effect journal has a conflicting terminal observation.")
            connection.execute(
                "UPDATE run_continuation_effects SET status=?,recovery_reason=?,updated_at=? WHERE action_id=?",
                (target, reason, now, normalized_action),
            )
            self._append_run_continuation_event(
                connection,
                run_id=normalized_run,
                event_type="run_continuation_effect_observed",
                payload={"action_id": normalized_action, "driver_generation": driver_generation, "status": target, "recovery_reason": reason},
            )
            connection.commit()
        result = self.get_run_continuation_effect(normalized_action)
        assert result is not None
        return result

    def reconcile_run_continuation_pending_action(
        self,
        *,
        run_id: str,
        action_id: str,
        effect_status: str,
        recovery_reason: str,
        controller_fencing_token: object,
        terminal_job_id: str = "",
    ) -> dict[str, Any]:
        """Terminalize a classified pending effect through the controller path.

        This is deliberately narrower than ordinary execution: it can run after
        pause, revoke, claim expiry, or grant expiry, but only on the exact
        pending action, only after filesystem state has been classified, and
        only after a still-bound managed Job is independently known terminal.
        It never replays a patch or turns an unknown dispatch into a result.
        """
        normalized_run = _require_opaque(run_id, "run_id")
        normalized_action = _require_sha256(action_id, "action_id")
        target = _bounded(effect_status, 32).lower()
        if target not in {"applied", "not_applied", "recovery_required"}:
            raise RunContinuationError("RUN_CONTINUATION_EFFECT_INVALID", "Reconciliation effect status is invalid.")
        reason = _bounded(recovery_reason, 512)
        controller_token = _bounded(controller_fencing_token, 256)
        if not controller_token:
            raise RunContinuationError("RUN_CONTINUATION_CONTROLLER_REQUIRED", "Pending-effect reconciliation requires an active controller receipt.")
        terminal_job = _require_opaque(terminal_job_id, "terminal_job_id") if terminal_job_id else ""
        now_ms = _now_ms()
        now = _utc_now()
        with self._lock, self._connect() as connection:
            self._run_continuation_ensure_schema(connection)
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT * FROM run_continuations WHERE run_id=?", (normalized_run,)).fetchone()
            record = self._run_continuation_row(row) if row is not None else None
            if record is None:
                raise RunContinuationError("RUN_CONTINUATION_GRANT_REQUIRED", "No continuation record exists for reconciliation.")
            if (
                record["enabled"]
                and str(record["claimed_runtime_instance"] or "")
                and now_ms < int(record["claim_expires_at_unix_ms"])
            ):
                raise RunContinuationError(
                    "RUN_CONTINUATION_DRIVER_ACTIVE",
                    "Pause or revoke the currently live driver claim before controller reconciliation.",
                )
            if record["pending_action_id"] != normalized_action:
                raise RunContinuationError("RUN_CONTINUATION_ACTION_MISMATCH", "Only the exact pending action may be reconciled.")
            pending_job = str(record["pending_job_id"] or "")
            if pending_job and pending_job != terminal_job:
                raise RunContinuationError(
                    "RUN_CONTINUATION_JOB_OUTCOME_UNKNOWN",
                    "The pending managed proof Job is not proven terminal; do not terminalize the action.",
                )
            effect = connection.execute(
                "SELECT * FROM run_continuation_effects WHERE action_id=? AND run_id=?",
                (normalized_action, normalized_run),
            ).fetchone()
            if effect is None:
                raise RunContinuationError("RUN_CONTINUATION_EFFECT_MISSING", "No exact effect journal exists for the pending action.")
            previous = str(effect["status"])
            if previous not in {"pending", target}:
                raise RunContinuationError("RUN_CONTINUATION_EFFECT_CONFLICT", "Effect journal has a conflicting terminal observation.")
            connection.execute(
                "UPDATE run_continuation_effects SET status=?,recovery_reason=?,updated_at=? WHERE action_id=?",
                (target, reason, now, normalized_action),
            )
            connection.execute(
                """UPDATE run_continuations
                   SET pending_action_id='',pending_evidence_hash='',pending_evidence_paths_json='[]',pending_replan_json='{}',
                       pending_dispatch_action_id='',pending_job_id='',pending_patch_action_id='',updated_at=?
                   WHERE run_id=?""",
                (now, normalized_run),
            )
            self._append_run_continuation_event(
                connection,
                run_id=normalized_run,
                event_type="run_continuation_reconciliation_terminalized",
                payload={
                    "action_id": normalized_action,
                    "effect_status": target,
                    "recovery_reason": reason,
                    "terminal_job_id": terminal_job,
                    "controller_fencing_token_sha256": hashlib.sha256(controller_token.encode("utf-8")).hexdigest(),
                },
            )
            updated = connection.execute("SELECT * FROM run_continuations WHERE run_id=?", (normalized_run,)).fetchone()
            connection.commit()
        assert updated is not None
        continuation = self._run_continuation_row(updated)
        continuation["policy"] = _policy_projection(continuation["policy"])
        return continuation

    @staticmethod
    def _run_continuation_row(row: sqlite3.Row) -> dict[str, Any]:
        policy = json.loads(str(row["policy_json"] or "{}"))
        return {
            "run_id": str(row["run_id"]),
            "workspace_id": str(row["workspace_id"]),
            "problem_id": str(row["problem_id"]),
            "problem_revision": int(row["problem_revision"]),
            "policy_sha256": str(row["policy_sha256"]),
            "issuer_receipt_sha256": str(row["issuer_receipt_sha256"]),
            "policy_revision": int(row["policy_revision"]),
            "enabled": bool(row["enabled"]),
            "pause_reason": str(row["pause_reason"]),
            "revoked_at": row["revoked_at"],
            "driver_generation": int(row["driver_generation"]),
            "claimed_runtime_instance": str(row["claimed_runtime_instance"]),
            "claim_expires_at_unix_ms": int(row["claim_expires_at_unix_ms"]),
            "next_action_seq": int(row["next_action_seq"]),
            "consumed_event_seq": int(row["consumed_event_seq"]),
            "pending_action_id": str(row["pending_action_id"]),
            "pending_evidence_hash": str(row["pending_evidence_hash"]),
            "pending_evidence_paths": json.loads(str(row["pending_evidence_paths_json"] or "[]")),
            "pending_replan": json.loads(str(row["pending_replan_json"] or "{}")),
            "pending_dispatch_action_id": str(row["pending_dispatch_action_id"]),
            "pending_job_id": str(row["pending_job_id"]),
            "pending_patch_action_id": str(row["pending_patch_action_id"]),
            "lane_id": str(row["lane_id"]),
            "thread_id": str(row["thread_id"]),
            "last_turn_id": str(row["last_turn_id"]),
            "remaining_decision_turns": int(row["remaining_decision_turns"]),
            "remaining_patch_attempts": int(row["remaining_patch_attempts"]),
            "expires_at_unix_ms": int(row["expires_at_unix_ms"]),
            "created_at": str(row["created_at"]),
            "updated_at": str(row["updated_at"]),
            "policy": policy,
        }

    @staticmethod
    def _append_run_continuation_event(
        connection: sqlite3.Connection,
        *,
        run_id: str,
        event_type: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        return append_hash_chained_event(
            connection,
            run_id=run_id,
            event_type=event_type,
            wave_id=None,
            delegation_id=None,
            state_before="",
            state_after="",
            payload=payload,
            event_time=_utc_now(),
            sanitize=_event_sanitize,
            serialize=_canonical_json,
            bounded_text=_bounded,
        )

    def _run_continuation_get_raw(self, run_id: str) -> dict[str, Any] | None:
        normalized = _require_opaque(run_id, "run_id")
        with self._lock, self._connect() as connection:
            self._run_continuation_ensure_schema(connection)
            row = connection.execute("SELECT * FROM run_continuations WHERE run_id=?", (normalized,)).fetchone()
        return self._run_continuation_row(row) if row is not None else None

    def get_run_continuation(self, run_id: str) -> dict[str, Any] | None:
        record = self._run_continuation_get_raw(run_id)
        if record is None:
            return None
        record["policy"] = _policy_projection(record["policy"])
        return record

    def issue_run_continuation(
        self,
        *,
        run_id: str,
        policy: dict[str, Any],
        issuer_receipt_sha256: str,
        now_unix_ms: int | None = None,
    ) -> dict[str, Any]:
        normalized_run = _require_opaque(run_id, "run_id")
        if str(policy.get("run_id") or "") != normalized_run:
            raise RunContinuationError("RUN_CONTINUATION_POLICY_INVALID", "Policy RUN does not match the grant target.")
        receipt = _require_sha256(issuer_receipt_sha256, "issuer_receipt_sha256")
        policy_json = _canonical_json(policy)
        policy_sha = hashlib.sha256(policy_json.encode("utf-8")).hexdigest()
        now_ms = _now_ms() if now_unix_ms is None else int(now_unix_ms)
        expires_at = now_ms + int(policy["max_duration_seconds"]) * 1_000
        now = _utc_now()
        with self._lock, self._connect() as connection:
            self._run_continuation_ensure_schema(connection)
            connection.execute("BEGIN IMMEDIATE")
            run = connection.execute("SELECT status FROM runs WHERE run_id=?", (normalized_run,)).fetchone()
            if run is None:
                raise RunContinuationError("ORCHESTRATION_RUN_NOT_FOUND", "Cannot issue a continuation grant for a missing RUN.")
            if str(run["status"] or "") != "active":
                raise RunContinuationError("RUN_CONTINUATION_RUN_NOT_ACTIVE", "Continuation grants require an active RUN.")
            existing_row = connection.execute("SELECT * FROM run_continuations WHERE run_id=?", (normalized_run,)).fetchone()
            if existing_row is not None:
                existing = self._run_continuation_row(existing_row)
                if existing["enabled"] and existing["policy_sha256"] == policy_sha and existing["issuer_receipt_sha256"] == receipt:
                    connection.commit()
                    existing["policy"] = _policy_projection(existing["policy"])
                    return {"status": "GRANTED", "idempotent": True, "continuation": existing}
                if existing["enabled"]:
                    raise RunContinuationError(
                        "RUN_CONTINUATION_GRANT_CONFLICT",
                        "The RUN already has an enabled immutable continuation policy; revoke it before issuing a different policy.",
                        details={"policy_sha256": existing["policy_sha256"]},
                    )
                if existing["pending_action_id"] or existing["pending_job_id"]:
                    raise RunContinuationError(
                        "RUN_CONTINUATION_EFFECT_PENDING",
                        "A revoked continuation still has a pending effect; reconcile it before issuing a replacement policy.",
                    )
                policy_revision = int(existing["policy_revision"]) + 1
                connection.execute(
                    """UPDATE run_continuations
                       SET workspace_id=?,problem_id=?,problem_revision=?,policy_json=?,policy_sha256=?,issuer_receipt_sha256=?,
                           policy_revision=?,enabled=1,pause_reason='',revoked_at=NULL,driver_generation=0,
                           claimed_runtime_instance='',claim_expires_at_unix_ms=0,next_action_seq=1,consumed_event_seq=0,pending_evidence_hash='',pending_evidence_paths_json='[]',pending_replan_json='{}',pending_dispatch_action_id='',pending_patch_action_id='',
                           remaining_decision_turns=?,remaining_patch_attempts=?,expires_at_unix_ms=?,updated_at=?
                       WHERE run_id=?""",
                    (
                        policy["workspace_id"], policy["problem_id"], int(policy["problem_revision"]), policy_json, policy_sha,
                        receipt, policy_revision, int(policy["max_decision_turns"]), int(policy["max_patch_attempts"]), expires_at,
                        now, normalized_run,
                    ),
                )
                event_type = "run_continuation_regranted"
            else:
                policy_revision = 1
                connection.execute(
                    """INSERT INTO run_continuations(
                           run_id,workspace_id,problem_id,problem_revision,policy_json,policy_sha256,issuer_receipt_sha256,
                           policy_revision,enabled,pause_reason,revoked_at,driver_generation,claimed_runtime_instance,
                           claim_expires_at_unix_ms,next_action_seq,consumed_event_seq,pending_action_id,pending_evidence_hash,pending_evidence_paths_json,pending_replan_json,pending_dispatch_action_id,pending_job_id,pending_patch_action_id,lane_id,
                           thread_id,last_turn_id,remaining_decision_turns,remaining_patch_attempts,expires_at_unix_ms,created_at,updated_at
                       ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        normalized_run, policy["workspace_id"], policy["problem_id"], int(policy["problem_revision"]), policy_json,
                        policy_sha, receipt, policy_revision, 1, "", None, 0, "", 0, 1, 0, "", "", "[]", "{}", "", "", "", "", "", "",
                        int(policy["max_decision_turns"]), int(policy["max_patch_attempts"]), expires_at, now, now,
                    ),
                )
                event_type = "run_continuation_granted"
            self._append_run_continuation_event(
                connection,
                run_id=normalized_run,
                event_type=event_type,
                payload={
                    "policy_sha256": policy_sha,
                    "issuer_receipt_sha256": receipt,
                    "policy_revision": policy_revision,
                    "expires_at_unix_ms": expires_at,
                    "route": RUN_CONTINUATION_ROUTE,
                    "profile": RUN_CONTINUATION_PROFILE,
                },
            )
            row = connection.execute("SELECT * FROM run_continuations WHERE run_id=?", (normalized_run,)).fetchone()
            connection.commit()
        assert row is not None
        result = self._run_continuation_row(row)
        result["policy"] = _policy_projection(result["policy"])
        return {"status": "GRANTED", "idempotent": False, "continuation": result}

    def _assert_run_continuation_row(
        self,
        record: dict[str, Any] | None,
        *,
        run_id: str,
        driver_generation: int | None = None,
        runtime_instance_id: str = "",
        now_unix_ms: int | None = None,
    ) -> dict[str, Any]:
        if record is None:
            raise RunContinuationError("RUN_CONTINUATION_GRANT_REQUIRED", "No durable execution grant exists for this RUN.")
        now_ms = _now_ms() if now_unix_ms is None else int(now_unix_ms)
        if not record["enabled"] or record["revoked_at"]:
            raise RunContinuationError("RUN_CONTINUATION_REVOKED", "The continuation grant is revoked or disabled.")
        if now_ms >= int(record["expires_at_unix_ms"]):
            raise RunContinuationError("RUN_CONTINUATION_EXPIRED", "The continuation grant has expired.")
        if driver_generation is not None and int(driver_generation) != int(record["driver_generation"]):
            raise RunContinuationError(
                "RUN_CONTINUATION_STALE_GENERATION",
                "The driver generation is fenced; discard the stale continuation action.",
                details={"run_id": run_id, "expected_generation": record["driver_generation"]},
            )
        if driver_generation is not None:
            runtime = _require_opaque(runtime_instance_id, "runtime_instance_id")
            if str(record["claimed_runtime_instance"] or "") != runtime:
                raise RunContinuationError(
                    "RUN_CONTINUATION_CLAIM_OWNER_MISMATCH",
                    "The continuation claim belongs to a different runtime instance.",
                    details={"run_id": run_id},
                )
            if now_ms >= int(record["claim_expires_at_unix_ms"]):
                raise RunContinuationError(
                    "RUN_CONTINUATION_CLAIM_EXPIRED",
                    "The continuation claim expired; reacquire through the fenced driver claim path.",
                    retryable=True,
                    details={"run_id": run_id},
                )
        return record

    def claim_run_continuation(
        self,
        *,
        run_id: str,
        runtime_instance_id: str,
        expected_generation: int,
        now_unix_ms: int | None = None,
        lease_seconds: int = RUN_CONTINUATION_LEASE_SECONDS,
    ) -> dict[str, Any]:
        normalized_run = _require_opaque(run_id, "run_id")
        runtime = _require_opaque(runtime_instance_id, "runtime_instance_id")
        if isinstance(expected_generation, bool) or not isinstance(expected_generation, int) or expected_generation < 0:
            raise RunContinuationError("RUN_CONTINUATION_GENERATION_INVALID", "expected_generation must be a non-negative integer.")
        if isinstance(lease_seconds, bool) or not isinstance(lease_seconds, int) or lease_seconds < 1 or lease_seconds > RUN_CONTINUATION_LEASE_SECONDS:
            raise RunContinuationError("RUN_CONTINUATION_CLAIM_INVALID", "lease_seconds is outside the bounded continuation claim policy.")
        now_ms = _now_ms() if now_unix_ms is None else int(now_unix_ms)
        now = _utc_now()
        with self._lock, self._connect() as connection:
            self._run_continuation_ensure_schema(connection)
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT * FROM run_continuations WHERE run_id=?", (normalized_run,)).fetchone()
            record = self._run_continuation_row(row) if row is not None else None
            record = self._assert_run_continuation_row(record, run_id=normalized_run, now_unix_ms=now_ms)
            current_generation = int(record["driver_generation"])
            if expected_generation != current_generation:
                connection.commit()
                return {"claimed": False, "reason": "stale_generation", "continuation": self.get_run_continuation(normalized_run)}
            active_owner = str(record["claimed_runtime_instance"])
            active_claim = int(record["claim_expires_at_unix_ms"]) > now_ms
            if active_claim and active_owner and active_owner != runtime:
                connection.commit()
                return {"claimed": False, "reason": "claimed_by_other_runtime", "continuation": self.get_run_continuation(normalized_run)}
            next_generation = current_generation if active_claim and active_owner == runtime else current_generation + 1
            expires_at = now_ms + lease_seconds * 1_000
            connection.execute(
                """UPDATE run_continuations
                   SET driver_generation=?,claimed_runtime_instance=?,claim_expires_at_unix_ms=?,updated_at=?
                   WHERE run_id=?""",
                (next_generation, runtime, expires_at, now, normalized_run),
            )
            self._append_run_continuation_event(
                connection,
                run_id=normalized_run,
                event_type="run_continuation_claimed",
                payload={"driver_generation": next_generation, "claim_expires_at_unix_ms": expires_at, "reclaimed": bool(active_owner and active_owner != runtime)},
            )
            updated = connection.execute("SELECT * FROM run_continuations WHERE run_id=?", (normalized_run,)).fetchone()
            connection.commit()
        assert updated is not None
        continuation = self._run_continuation_row(updated)
        continuation["policy"] = _policy_projection(continuation["policy"])
        return {"claimed": True, "reason": "claimed", "continuation": continuation}

    def renew_run_continuation_claim(
        self,
        *,
        run_id: str,
        runtime_instance_id: str,
        driver_generation: int,
        now_unix_ms: int | None = None,
        lease_seconds: int = RUN_CONTINUATION_LEASE_SECONDS,
    ) -> dict[str, Any]:
        """Renew only the exact, still-live owner claim; never revive it."""
        normalized_run = _require_opaque(run_id, "run_id")
        runtime = _require_opaque(runtime_instance_id, "runtime_instance_id")
        if isinstance(driver_generation, bool) or not isinstance(driver_generation, int) or driver_generation < 1:
            raise RunContinuationError("RUN_CONTINUATION_GENERATION_INVALID", "driver_generation must be a positive integer.")
        if isinstance(lease_seconds, bool) or not isinstance(lease_seconds, int) or lease_seconds < 1 or lease_seconds > RUN_CONTINUATION_LEASE_SECONDS:
            raise RunContinuationError("RUN_CONTINUATION_CLAIM_INVALID", "lease_seconds is outside the bounded continuation claim policy.")
        now_ms = _now_ms() if now_unix_ms is None else int(now_unix_ms)
        now = _utc_now()
        with self._lock, self._connect() as connection:
            self._run_continuation_ensure_schema(connection)
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT * FROM run_continuations WHERE run_id=?", (normalized_run,)).fetchone()
            record = self._run_continuation_row(row) if row is not None else None
            record = self._assert_run_continuation_row(
                record,
                run_id=normalized_run,
                driver_generation=driver_generation,
                runtime_instance_id=runtime,
                now_unix_ms=now_ms,
            )
            expires_at = now_ms + lease_seconds * 1_000
            connection.execute(
                "UPDATE run_continuations SET claim_expires_at_unix_ms=?,updated_at=? WHERE run_id=?",
                (expires_at, now, normalized_run),
            )
            self._append_run_continuation_event(
                connection,
                run_id=normalized_run,
                event_type="run_continuation_claim_renewed",
                payload={"driver_generation": driver_generation, "claim_expires_at_unix_ms": expires_at},
            )
            updated = connection.execute("SELECT * FROM run_continuations WHERE run_id=?", (normalized_run,)).fetchone()
            connection.commit()
        assert updated is not None
        continuation = self._run_continuation_row(updated)
        continuation["policy"] = _policy_projection(continuation["policy"])
        return continuation

    def assert_run_continuation_execution(
        self,
        *,
        run_id: str,
        driver_generation: int,
        runtime_instance_id: str,
        paths: Iterable[str] = (),
        check_definition_hash: str = "",
        now_unix_ms: int | None = None,
    ) -> dict[str, Any]:
        record = self._run_continuation_get_raw(run_id)
        record = self._assert_run_continuation_row(
            record,
            run_id=run_id,
            driver_generation=driver_generation,
            runtime_instance_id=runtime_instance_id,
            now_unix_ms=now_unix_ms,
        )
        policy = record["policy"]
        requested_paths = {_normalize_path(item, "execution path") for item in paths}
        allowed = set(policy.get("write_paths") or [])
        protected = set(policy.get("protected_paths") or [])
        denied = sorted(path for path in requested_paths if path not in allowed or path in protected)
        if denied:
            raise RunContinuationError(
                "RUN_CONTINUATION_SCOPE_DENIED",
                "The delegated action exceeds the immutable continuation write scope.",
                details={"paths": denied},
            )
        if check_definition_hash:
            check_hash = _require_sha256(check_definition_hash, "check_definition_hash")
            approved = {str(item.get("definition_hash") or "") for item in policy.get("approved_checks") or [] if isinstance(item, dict)}
            if check_hash not in approved:
                raise RunContinuationError(
                    "RUN_CONTINUATION_CHECK_DENIED",
                    "The delegated action selected a check not bound into the grant policy.",
                )
        return record

    def reserve_run_continuation_action(
        self,
        *,
        run_id: str,
        driver_generation: int,
        runtime_instance_id: str,
        action_kind: str,
        request_hash: str,
        evidence_hash: str = "",
        evidence_paths: Iterable[str] = (),
        technical_replan: dict[str, Any] | None = None,
        expected_action_seq: int,
        now_unix_ms: int | None = None,
    ) -> dict[str, Any]:
        normalized_run = _require_opaque(run_id, "run_id")
        kind = _require_opaque(action_kind, "action_kind", limit=64)
        request_digest = _require_sha256(request_hash, "request_hash")
        evidence_digest = _require_sha256(evidence_hash, "evidence_hash") if evidence_hash else ""
        normalized_evidence_paths = _normalize_paths(list(evidence_paths), "evidence_paths")
        normalized_replan = _normalize_technical_replan(technical_replan)
        if isinstance(expected_action_seq, bool) or not isinstance(expected_action_seq, int) or expected_action_seq < 1:
            raise RunContinuationError("RUN_CONTINUATION_ACTION_INVALID", "expected_action_seq must be a positive integer.")
        now_ms = _now_ms() if now_unix_ms is None else int(now_unix_ms)
        now = _utc_now()
        with self._lock, self._connect() as connection:
            self._run_continuation_ensure_schema(connection)
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT * FROM run_continuations WHERE run_id=?", (normalized_run,)).fetchone()
            record = self._run_continuation_row(row) if row is not None else None
            record = self._assert_run_continuation_row(
                record,
                run_id=normalized_run,
                driver_generation=driver_generation,
                runtime_instance_id=runtime_instance_id,
                now_unix_ms=now_ms,
            )
            allowed_reads = set(record["policy"].get("read_paths") or [])
            denied_evidence_paths = sorted(set(normalized_evidence_paths).difference(allowed_reads))
            if denied_evidence_paths:
                raise RunContinuationError(
                    "RUN_CONTINUATION_READ_SCOPE_DENIED",
                    "An evidence packet includes a path outside the immutable continuation read scope.",
                    details={"paths": denied_evidence_paths},
                )
            if int(record["remaining_decision_turns"]) < 1:
                raise RunContinuationError("RUN_CONTINUATION_DECISION_BUDGET_EXHAUSTED", "No continuation decision turns remain.")
            current_seq = int(record["next_action_seq"])
            action_id = hashlib.sha256(
                f"run-continuation-v1\0{normalized_run}\0{record['policy_revision']}\0{expected_action_seq}\0{kind}\0{request_digest}".encode("utf-8")
            ).hexdigest()
            if record["pending_action_id"]:
                if record["pending_action_id"] == action_id:
                    connection.commit()
                    return {"reserved": False, "idempotent": True, "action_id": action_id, "continuation": self.get_run_continuation(normalized_run)}
                raise RunContinuationError("RUN_CONTINUATION_ACTION_PENDING", "Reconcile the existing pending continuation action before reserving another.")
            if expected_action_seq != current_seq:
                raise RunContinuationError(
                    "RUN_CONTINUATION_ACTION_SEQUENCE_STALE",
                    "The continuation action cursor changed; do not create a second effect identity.",
                    details={"expected_action_seq": current_seq},
                )
            connection.execute(
                """UPDATE run_continuations
                   SET pending_action_id=?,pending_evidence_hash=?,pending_evidence_paths_json=?,pending_replan_json=?,pending_dispatch_action_id='',pending_job_id='',pending_patch_action_id='',next_action_seq=?,remaining_decision_turns=remaining_decision_turns-1,updated_at=?
                   WHERE run_id=?""",
                (action_id, evidence_digest, _canonical_json(normalized_evidence_paths), _canonical_json(normalized_replan), current_seq + 1, now, normalized_run),
            )
            self._append_run_continuation_event(
                connection,
                run_id=normalized_run,
                event_type="run_continuation_action_reserved",
                payload={"action_id": action_id, "action_seq": current_seq, "action_kind": kind, "driver_generation": driver_generation, "request_hash": request_digest, "evidence_hash": evidence_digest, "evidence_path_count": len(normalized_evidence_paths), "technical_replan": bool(normalized_replan)},
            )
            updated = connection.execute("SELECT * FROM run_continuations WHERE run_id=?", (normalized_run,)).fetchone()
            connection.commit()
        assert updated is not None
        continuation = self._run_continuation_row(updated)
        continuation["policy"] = _policy_projection(continuation["policy"])
        return {"reserved": True, "idempotent": False, "action_id": action_id, "continuation": continuation}

    def complete_run_continuation_action(
        self,
        *,
        run_id: str,
        driver_generation: int,
        runtime_instance_id: str,
        action_id: str,
        consumed_event_seq: int = 0,
    ) -> dict[str, Any]:
        normalized_run = _require_opaque(run_id, "run_id")
        normalized_action = _require_sha256(action_id, "action_id")
        if isinstance(consumed_event_seq, bool) or not isinstance(consumed_event_seq, int) or consumed_event_seq < 0:
            raise RunContinuationError("RUN_CONTINUATION_ACTION_INVALID", "consumed_event_seq must be non-negative.")
        now = _utc_now()
        with self._lock, self._connect() as connection:
            self._run_continuation_ensure_schema(connection)
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT * FROM run_continuations WHERE run_id=?", (normalized_run,)).fetchone()
            record = self._run_continuation_row(row) if row is not None else None
            record = self._assert_run_continuation_row(
                record,
                run_id=normalized_run,
                driver_generation=driver_generation,
                runtime_instance_id=runtime_instance_id,
            )
            if record["pending_action_id"] != normalized_action:
                raise RunContinuationError("RUN_CONTINUATION_ACTION_MISMATCH", "Only the exact pending action can advance the continuation cursor.")
            connection.execute(
                """UPDATE run_continuations
                   SET pending_action_id='',pending_evidence_hash='',pending_evidence_paths_json='[]',pending_replan_json='{}',pending_dispatch_action_id='',pending_job_id='',pending_patch_action_id='',consumed_event_seq=MAX(consumed_event_seq,?),updated_at=? WHERE run_id=?""",
                (consumed_event_seq, now, normalized_run),
            )
            self._append_run_continuation_event(
                connection,
                run_id=normalized_run,
                event_type="run_continuation_action_completed",
                payload={"action_id": normalized_action, "driver_generation": driver_generation, "consumed_event_seq": consumed_event_seq},
            )
            updated = connection.execute("SELECT * FROM run_continuations WHERE run_id=?", (normalized_run,)).fetchone()
            connection.commit()
        assert updated is not None
        continuation = self._run_continuation_row(updated)
        continuation["policy"] = _policy_projection(continuation["policy"])
        return continuation

    def consume_run_continuation_patch_attempt(
        self,
        *,
        run_id: str,
        driver_generation: int,
        runtime_instance_id: str,
        action_id: str,
    ) -> dict[str, Any]:
        """Atomically spend one PATCH budget unit for one exact pending action."""
        normalized_run = _require_opaque(run_id, "run_id")
        normalized_action = _require_sha256(action_id, "action_id")
        now = _utc_now()
        with self._lock, self._connect() as connection:
            self._run_continuation_ensure_schema(connection)
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT * FROM run_continuations WHERE run_id=?", (normalized_run,)).fetchone()
            record = self._run_continuation_row(row) if row is not None else None
            record = self._assert_run_continuation_row(
                record,
                run_id=normalized_run,
                driver_generation=driver_generation,
                runtime_instance_id=runtime_instance_id,
            )
            if record["pending_action_id"] != normalized_action:
                raise RunContinuationError("RUN_CONTINUATION_ACTION_MISMATCH", "Only the exact pending action may spend a PATCH attempt.")
            spent_for = str(record["pending_patch_action_id"] or "")
            if spent_for:
                if spent_for != normalized_action:
                    raise RunContinuationError("RUN_CONTINUATION_PATCH_ATTEMPT_CONFLICT", "A different PATCH attempt is already bound to the pending action.")
                connection.commit()
                record["policy"] = _policy_projection(record["policy"])
                return {"consumed": False, "idempotent": True, "continuation": record}
            if int(record["remaining_patch_attempts"]) < 1:
                raise RunContinuationError("RUN_CONTINUATION_PATCH_BUDGET_EXHAUSTED", "No continuation PATCH attempts remain.")
            connection.execute(
                "UPDATE run_continuations SET pending_patch_action_id=?,remaining_patch_attempts=remaining_patch_attempts-1,updated_at=? WHERE run_id=?",
                (normalized_action, now, normalized_run),
            )
            self._append_run_continuation_event(
                connection,
                run_id=normalized_run,
                event_type="run_continuation_patch_attempt_consumed",
                payload={"action_id": normalized_action, "driver_generation": driver_generation},
            )
            updated = connection.execute("SELECT * FROM run_continuations WHERE run_id=?", (normalized_run,)).fetchone()
            connection.commit()
        assert updated is not None
        continuation = self._run_continuation_row(updated)
        continuation["policy"] = _policy_projection(continuation["policy"])
        return {"consumed": True, "idempotent": False, "continuation": continuation}

    def set_run_continuation_state(
        self,
        *,
        run_id: str,
        action: str,
        reason: str = "",
    ) -> dict[str, Any]:
        normalized_run = _require_opaque(run_id, "run_id")
        operation = _bounded(action, 32).lower()
        if operation not in {"pause", "resume", "revoke"}:
            raise RunContinuationError("RUN_CONTINUATION_CONTROL_INVALID", "Unsupported continuation control action.")
        bounded_reason = _bounded(reason, 512)
        now = _utc_now()
        with self._lock, self._connect() as connection:
            self._run_continuation_ensure_schema(connection)
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT * FROM run_continuations WHERE run_id=?", (normalized_run,)).fetchone()
            record = self._run_continuation_row(row) if row is not None else None
            if record is None:
                raise RunContinuationError("RUN_CONTINUATION_GRANT_REQUIRED", "No continuation grant exists for this RUN.")
            if operation == "resume" and record["revoked_at"]:
                raise RunContinuationError("RUN_CONTINUATION_REVOKED", "A revoked grant cannot be resumed; issue a new immutable grant.")
            enabled = 1 if operation == "resume" else 0
            revoked_at = now if operation == "revoke" else record["revoked_at"]
            pause_reason = "" if operation == "resume" else (bounded_reason or operation)
            next_generation = int(record["driver_generation"]) + 1
            connection.execute(
                """UPDATE run_continuations
                   SET enabled=?,pause_reason=?,revoked_at=?,driver_generation=?,claimed_runtime_instance='',
                       claim_expires_at_unix_ms=0,updated_at=? WHERE run_id=?""",
                (enabled, pause_reason, revoked_at, next_generation, now, normalized_run),
            )
            self._append_run_continuation_event(
                connection,
                run_id=normalized_run,
                event_type=f"run_continuation_{operation}d" if operation != "revoke" else "run_continuation_revoked",
                payload={"reason": pause_reason, "driver_generation": next_generation, "pending_action": bool(record["pending_action_id"]), "pending_job": bool(record["pending_job_id"])},
            )
            updated = connection.execute("SELECT * FROM run_continuations WHERE run_id=?", (normalized_run,)).fetchone()
            connection.commit()
        assert updated is not None
        result = self._run_continuation_row(updated)
        result["policy"] = _policy_projection(result["policy"])
        return result

    def set_run_continuation_dispatch(
        self,
        *,
        run_id: str,
        driver_generation: int,
        runtime_instance_id: str,
        action_id: str,
        lane_id: str,
        thread_id: str,
        turn_id: str,
    ) -> dict[str, Any]:
        """Persist the exact no-tools lane/turn selected for one pending action."""
        normalized_run = _require_opaque(run_id, "run_id")
        normalized_action = _require_sha256(action_id, "action_id")
        lane = _require_opaque(lane_id, "lane_id")
        thread = _require_opaque(thread_id, "thread_id")
        turn = _require_opaque(turn_id, "turn_id")
        now = _utc_now()
        with self._lock, self._connect() as connection:
            self._run_continuation_ensure_schema(connection)
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT * FROM run_continuations WHERE run_id=?", (normalized_run,)).fetchone()
            record = self._run_continuation_row(row) if row is not None else None
            record = self._assert_run_continuation_row(
                record,
                run_id=normalized_run,
                driver_generation=driver_generation,
                runtime_instance_id=runtime_instance_id,
            )
            if record["pending_action_id"] != normalized_action:
                raise RunContinuationError("RUN_CONTINUATION_ACTION_MISMATCH", "Only the exact pending action may bind a model dispatch.")
            existing_action = str(record["pending_dispatch_action_id"])
            if existing_action:
                existing = (record["lane_id"], record["thread_id"], record["last_turn_id"])
                requested = (lane, thread, turn)
                if existing_action != normalized_action or existing != requested:
                    raise RunContinuationError("RUN_CONTINUATION_DISPATCH_PENDING", "A different model dispatch is already recorded for the pending action.")
                connection.commit()
                record["policy"] = _policy_projection(record["policy"])
                return record
            if record["lane_id"] and record["lane_id"] != lane:
                raise RunContinuationError("RUN_CONTINUATION_DISPATCH_PENDING", "The continuation lane identity cannot change while the grant is active.")
            if record["thread_id"] and record["thread_id"] != thread:
                raise RunContinuationError("RUN_CONTINUATION_DISPATCH_PENDING", "The continuation thread identity cannot change while the grant is active.")
            connection.execute(
                "UPDATE run_continuations SET lane_id=?,thread_id=?,last_turn_id=?,pending_dispatch_action_id=?,updated_at=? WHERE run_id=?",
                (lane, thread, turn, normalized_action, now, normalized_run),
            )
            self._append_run_continuation_event(
                connection,
                run_id=normalized_run,
                event_type="run_continuation_dispatch_recorded",
                payload={"action_id": normalized_action, "driver_generation": driver_generation, "lane_id": lane, "thread_id": thread, "turn_id": turn},
            )
            updated = connection.execute("SELECT * FROM run_continuations WHERE run_id=?", (normalized_run,)).fetchone()
            connection.commit()
        assert updated is not None
        result = self._run_continuation_row(updated)
        result["policy"] = _policy_projection(result["policy"])
        return result

    def set_run_continuation_pending_job(
        self,
        *,
        run_id: str,
        driver_generation: int,
        runtime_instance_id: str,
        action_id: str,
        job_id: str = "",
    ) -> dict[str, Any]:
        """Bind the exact managed proof Job to a pending action, or clear it after terminal observation.

        The managed-process ledger is the lifecycle authority for the process
        itself. This projection is only the continuation cursor that prevents a
        later driver from assuming a missing/unknown proof command is safe to
        repeat.
        """
        normalized_run = _require_opaque(run_id, "run_id")
        normalized_action = _require_sha256(action_id, "action_id")
        normalized_job = _require_opaque(job_id, "job_id") if job_id else ""
        now = _utc_now()
        with self._lock, self._connect() as connection:
            self._run_continuation_ensure_schema(connection)
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT * FROM run_continuations WHERE run_id=?", (normalized_run,)).fetchone()
            record = self._run_continuation_row(row) if row is not None else None
            record = self._assert_run_continuation_row(
                record,
                run_id=normalized_run,
                driver_generation=driver_generation,
                runtime_instance_id=runtime_instance_id,
            )
            if record["pending_action_id"] != normalized_action:
                raise RunContinuationError("RUN_CONTINUATION_ACTION_MISMATCH", "Only the exact pending action may bind a managed proof Job.")
            existing = str(record["pending_job_id"])
            if existing and normalized_job and existing != normalized_job:
                raise RunContinuationError("RUN_CONTINUATION_JOB_PENDING", "A different managed proof Job is already pending for this action.")
            if existing == normalized_job:
                connection.commit()
                record["policy"] = _policy_projection(record["policy"])
                return record
            connection.execute(
                "UPDATE run_continuations SET pending_job_id=?,updated_at=? WHERE run_id=?",
                (normalized_job, now, normalized_run),
            )
            self._append_run_continuation_event(
                connection,
                run_id=normalized_run,
                event_type="run_continuation_check_job_bound" if normalized_job else "run_continuation_check_job_cleared",
                payload={"action_id": normalized_action, "driver_generation": driver_generation, "job_id": normalized_job},
            )
            updated = connection.execute("SELECT * FROM run_continuations WHERE run_id=?", (normalized_run,)).fetchone()
            connection.commit()
        assert updated is not None
        result = self._run_continuation_row(updated)
        result["policy"] = _policy_projection(result["policy"])
        return result


class RunContinuationMixin:
    """Grant/control hooks; the separated driver owns model observation and effects."""

    def _run_continuation_value(self, args: dict[str, Any], *, workflow: str, phase: str) -> str | dict[str, Any]:
        raw = args.get("continuation")
        if isinstance(raw, dict):
            return self._run_continuation_grant(args, raw)
        if raw is not None and not isinstance(raw, str):
            raise ToolFailure(
                "INVALID_ARGUMENT",
                "agent_workflow continuation must be either the legacy source-fenced token or an explicit continuation grant request object.",
                category="validation",
            )
        return str(raw or "").strip()

    @staticmethod
    def _run_continuation_tool_failure(exc: RunContinuationError) -> ToolFailure:
        return ToolFailure(exc.code, str(exc), category="security" if "DENIED" in exc.code or "REQUIRED" in exc.code else "validation", retryable=exc.retryable, details=exc.details)

    def _run_continuation_grant(self, args: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
        workflow = str(args.get("workflow") or "custom").strip().lower()
        phase = str(args.get("phase") or "prepare").strip().lower()
        if phase != "prepare" or workflow not in {"bugfix", "feature"}:
            raise ToolFailure(
                "RUN_CONTINUATION_GRANT_PHASE_INVALID",
                "A continuation grant is explicit preflight authority for a bounded bugfix or feature RUN; it cannot be attached to arbitrary execution/resume phases.",
                category="validation",
            )
        objective = str(args.get("objective") or self.task_state.get().get("objective") or "").strip()
        if not objective:
            raise ToolFailure("RUN_CONTINUATION_OBJECTIVE_REQUIRED", "A continuation grant requires a non-empty existing RUN objective.", category="validation")
        ctx, identity = self._agent_orchestration_context(args, objective=objective)
        controller = self._require_hub_controller(ctx.run_id)
        if controller is None:
            raise ToolFailure(
                "RUN_CONTINUATION_CONTROLLER_REQUIRED",
                "A background continuation grant is denied without the authenticated active ChatWeb controller; missing identity is never a trusted-local bypass.",
                category="security",
            )
        hub = self._current_hub_client() or {}
        if (
            str(hub.get("client_type") or "") != "chatweb"
            or str(hub.get("role") or "") != "controller"
            or str(hub.get("identity_source") or "") != "attested_transport"
            or hub.get("attestation_verified") is not True
        ):
            raise ToolFailure(
                "RUN_CONTINUATION_CONTROLLER_ATTESTATION_REQUIRED",
                "A continuation grant requires an attested ChatWeb controller identity, not a copied hub_client object.",
                category="security",
            )
        binding = self.orchestration_ledger.controller_run_problem_binding(ctx.run_id)
        if not isinstance(binding, dict):
            raise ToolFailure(
                "RUN_CONTINUATION_PROBLEM_BINDING_REQUIRED",
                "A continuation grant must bind exactly one current Problem Revision to its RUN.",
                category="security",
            )
        workspace_identity = identity.get("workspace_identity") if isinstance(identity.get("workspace_identity"), dict) else {}
        workspace_id = str(workspace_identity.get("workspace_id") or "").strip()
        if not workspace_id:
            raise ToolFailure("RUN_CONTINUATION_WORKSPACE_REQUIRED", "The current workspace identity is unavailable; grant issuance fails closed.", category="security")
        loaded_identity = self._loaded_behavior_identity()
        admission = self.activation_admission_snapshot()
        admission_state = str(admission.get("admission") or "").lower()
        epoch_id = str(admission.get("activation_epoch_id") or "").strip()
        if admission_state != "open" or not epoch_id:
            raise ToolFailure(
                "RUN_CONTINUATION_ADMISSION_REQUIRED",
                "Continuation grants require a currently admitted runtime epoch; partial startup and stale connector state cannot be used as authority.",
                category="runtime",
                details={"activation": admission},
            )
        try:
            policy = build_run_continuation_policy(
                request,
                run_id=ctx.run_id,
                workspace_id=workspace_id,
                problem_id=str(binding.get("problem_id") or ""),
                problem_revision=int(binding.get("problem_revision") or 0),
                contract_fingerprint=ctx.contract_fp,
                tool_contract_sha256=str(self.tool_contract.get("sha256") or ""),
                runtime_behavior_fingerprint=str(loaded_identity.get("fingerprint") or ""),
                activation_epoch_id=epoch_id,
                activation_admission=admission_state,
                issuer_client_id=self._hub_client_record_id(hub),
            )
            current_environment_hash = self._run_continuation_environment_hash()
            mismatched_checks = [
                str(item.get("check_id") or "")
                for item in policy.get("approved_checks") or []
                if isinstance(item, dict) and str(item.get("environment_hash") or "") != current_environment_hash
            ]
            if mismatched_checks:
                raise ToolFailure(
                    "RUN_CONTINUATION_ENVIRONMENT_MISMATCH",
                    "Each immutable approved check must bind the currently admitted continuation execution environment.",
                    category="validation",
                    details={"check_ids": mismatched_checks, "current_environment_hash": current_environment_hash},
                )
            issuer_receipt = hashlib.sha256(
                _canonical_json({
                    "run_id": ctx.run_id,
                    "controller_lease_id": controller.get("lease_id"),
                    "controller_fencing_token": controller.get("fencing_token"),
                    "controller_client_id": self._hub_client_record_id(hub),
                    "tool_contract_sha256": self.tool_contract.get("sha256"),
                }).encode("utf-8")
            ).hexdigest()
            issued = self.orchestration_ledger.issue_run_continuation(
                run_id=ctx.run_id,
                policy=policy,
                issuer_receipt_sha256=issuer_receipt,
            )
        except RunContinuationError as exc:
            raise self._run_continuation_tool_failure(exc) from exc
        self._project_orchestration(ctx, event="run_continuation_granted")
        return {
            "workflow": workflow,
            "phase": "prepare",
            "continuation": issued,
            "orchestration": self._orchestration_result(ctx),
            "task": self.task_state.get(),
            "recommended_next_action": "The grant is durable and binds the current continuation execution environment. Start it explicitly through task_control action=run_continuation/run_continuation_action=start; MCP, not the model, will then own exact dispatch observation, mutation, proof, and the technical ACCEPTING transition.",
        }

    def _run_continuation_canonical_evidence(
        self,
        policy: dict[str, Any],
        *,
        objective: str,
        selected_read_paths: Iterable[str] = (),
        technical_replan: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], str]:
        """Create the content-bounded packet that a no-tools model may reason over."""
        revision = self.orchestration_ledger.problem_get_exact_revision(
            str(policy["problem_id"]),
            int(policy["problem_revision"]),
            expected_contract_fingerprint=str(policy["contract_fingerprint"]),
        )
        capsule = revision.get("capsule") if isinstance(revision.get("capsule"), dict) else None
        if capsule is None:
            raise ToolFailure("RUN_CONTINUATION_PROBLEM_CONTEXT_INVALID", "The exact bound Problem Revision has no valid contract capsule.", category="runtime")
        if _contains_sensitive_model_content(objective) or _contains_sensitive_model_content(capsule):
            raise ToolFailure(
                "RUN_CONTINUATION_EVIDENCE_SENSITIVE",
                "Problem material contains sensitive-like content and cannot be sent to a continuation proposal model.",
                category="security",
            )
        root = self.workspace.root.resolve(strict=False)
        allowed_read_paths = [_normalize_path(path, "read scope") for path in policy.get("read_paths") or []]
        requested_read_paths = _normalize_paths(list(selected_read_paths), "selected_read_paths")
        denied_read_paths = sorted(set(requested_read_paths).difference(allowed_read_paths))
        if denied_read_paths:
            raise ToolFailure(
                "RUN_CONTINUATION_READ_SCOPE_DENIED",
                "The requested continuation evidence is outside the immutable read scope.",
                category="security",
                details={"paths": denied_read_paths},
            )
        files: list[dict[str, str]] = []
        for path in requested_read_paths:
            normalized = _normalize_path(path, "read scope")
            target = (root / normalized).resolve(strict=False)
            if not target.is_relative_to(root) or not target.is_file():
                raise ToolFailure("RUN_CONTINUATION_EVIDENCE_UNAVAILABLE", "A granted read path is not a current workspace file.", category="runtime", details={"path": normalized})
            try:
                text = target.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                raise ToolFailure("RUN_CONTINUATION_EVIDENCE_UNAVAILABLE", "A granted read path could not be read as UTF-8.", category="runtime", details={"path": normalized}) from exc
            if len(text.encode("utf-8")) > 48_000:
                raise ToolFailure("RUN_CONTINUATION_EVIDENCE_TOO_LARGE", "A granted read path exceeds the bounded continuation packet limit.", category="validation", details={"path": normalized})
            if _contains_sensitive_model_content(text):
                raise ToolFailure(
                    "RUN_CONTINUATION_EVIDENCE_SENSITIVE",
                    "A granted read path contains sensitive-like content and cannot be sent to a continuation proposal model.",
                    category="security",
                    details={"path": normalized},
                )
            files.append({"path": normalized, "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(), "content": text})
        identity = self._orchestration_workspace_identity(".")
        evidence = {
            "schema_version": 1,
            "objective": _bounded(objective, 2_000),
            "problem_contract": capsule,
            "read_files": files,
            "available_read_paths": allowed_read_paths,
            "write_paths": list(policy.get("write_paths") or []),
            "protected_paths": list(policy.get("protected_paths") or []),
            "approved_check_hashes": [str(item.get("definition_hash") or "") for item in policy.get("approved_checks") or [] if isinstance(item, dict)],
            "source_identity": {"base_head": identity.get("base_head"), "worktree_fp": identity.get("worktree_fp")},
        }
        normalized_replan = _normalize_technical_replan(technical_replan)
        if normalized_replan:
            if _contains_sensitive_model_content(normalized_replan):
                raise ToolFailure(
                    "RUN_CONTINUATION_EVIDENCE_SENSITIVE",
                    "Technical replan material contains sensitive-like content and cannot be sent to a continuation proposal model.",
                    category="security",
                )
            evidence["technical_replan"] = normalized_replan
        digest = hashlib.sha256(_canonical_json(evidence).encode("utf-8")).hexdigest()
        return evidence, digest

    def _run_continuation_prompt(self, *, policy: dict[str, Any], evidence: dict[str, Any], evidence_hash: str) -> str:
        packet = {
            "continuation_contract": {
                "route": policy.get("route"),
                "profile": policy.get("profile"),
                "acceptance_mode": policy.get("acceptance_mode"),
                "instruction": "Choose exactly one proposal kind: READ, PATCH, READY, or BLOCKED. Never ask for expanded scope, a new check, a new budget, or authority. Copy evidence_hash exactly.",
            },
            "evidence_hash": evidence_hash,
            "evidence": evidence,
        }
        return "Bounded durable continuation packet:\n" + _canonical_json(packet)

    def _run_continuation_start_driver(self, args: dict[str, Any]) -> dict[str, Any]:
        run_id = str(args.get("run_id") or "").strip()
        if not run_id:
            projection = self.task_state.get().get("orchestration")
            run_id = str((projection or {}).get("run_id") or "") if isinstance(projection, dict) else ""
        if not run_id:
            raise ToolFailure("ORCHESTRATION_RUN_NOT_FOUND", "run_id is required to start a continuation driver.", category="not_found")
        record = self.orchestration_ledger._run_continuation_get_raw(run_id)
        if record is None:
            raise ToolFailure("RUN_CONTINUATION_GRANT_REQUIRED", "A continuation driver requires a prior immutable grant.", category="security")
        policy = record["policy"]
        try:
            # Dispatch is an externally observable continuation boundary.  Do
            # not claim a driver or start a model turn under an old admitted
            # runtime, behavior fingerprint, base/worktree, or RUN context.
            self._run_continuation_assert_runtime(policy)
            self._run_continuation_context(record)
            claim = self.orchestration_ledger.claim_run_continuation(
                run_id=run_id,
                runtime_instance_id=self._run_continuation_runtime_instance_id(),
                expected_generation=int(record["driver_generation"]),
            )
            if not claim.get("claimed"):
                raise RunContinuationError("RUN_CONTINUATION_DRIVER_BUSY", "Another admitted runtime currently owns this continuation driver.", retryable=True, details={"reason": claim.get("reason")})
            continuation = claim["continuation"]
            generation = int(continuation["driver_generation"])
            raw_policy = self.orchestration_ledger._run_continuation_get_raw(run_id)
            if raw_policy is None:
                raise RunContinuationError("RUN_CONTINUATION_GRANT_REQUIRED", "Continuation grant disappeared during driver claim.")
            policy = raw_policy["policy"]
            objective = str((self.orchestration_ledger.get_run(run_id) or {}).get("objective") or "").strip()
            # Start with the immutable Problem capsule and a declared bounded
            # read catalogue. The model must explicitly request source bytes;
            # this keeps READ meaningful instead of handing it every granted
            # file and then accepting a no-op request loop.
            evidence, evidence_hash = self._run_continuation_canonical_evidence(
                policy, objective=objective, selected_read_paths=()
            )
            request_hash = hashlib.sha256(_canonical_json({"evidence_hash": evidence_hash, "profile": RUN_CONTINUATION_PROFILE}).encode("utf-8")).hexdigest()
            reservation = self.orchestration_ledger.reserve_run_continuation_action(
                run_id=run_id,
                driver_generation=generation,
                runtime_instance_id=self._run_continuation_runtime_instance_id(),
                action_kind="proposal",
                request_hash=request_hash,
                evidence_hash=evidence_hash,
                evidence_paths=(),
                expected_action_seq=int(continuation["next_action_seq"]),
            )
            if not reservation.get("reserved"):
                raise RunContinuationError("RUN_CONTINUATION_ACTION_PENDING", "The continuation proposal action is already reserved; reconcile it before dispatch.")
            action_id = str(reservation["action_id"])
            bridge = self._codex_bridge.run(
                self._run_continuation_prompt(policy=policy, evidence=evidence, evidence_hash=evidence_hash),
                profile=RUN_CONTINUATION_PROFILE,
                lifetime="persistent",
                output_schema=RUN_CONTINUATION_PROPOSAL_SCHEMA,
            )
            thread_id, turn_id = str(bridge.get("thread_id") or ""), str(bridge.get("turn_id") or "")
            if not thread_id or not turn_id:
                raise RunContinuationError("RUN_CONTINUATION_DISPATCH_FAILED", "The bridge did not return a durable thread and turn identity.")
            lane_id = hashlib.sha256(f"run-continuation-lane-v1\0{run_id}\0{policy['policy_sha256'] if 'policy_sha256' in policy else evidence_hash}".encode("utf-8")).hexdigest()
            self.orchestration_ledger.set_run_continuation_dispatch(
                run_id=run_id,
                driver_generation=generation,
                runtime_instance_id=self._run_continuation_runtime_instance_id(),
                action_id=action_id,
                lane_id=lane_id,
                thread_id=thread_id,
                turn_id=turn_id,
            )
            self._run_continuation_start_worker(run_id=run_id, driver_generation=generation)
        except RunContinuationError as exc:
            raise self._run_continuation_tool_failure(exc) from exc
        except Exception as exc:
            code = str(getattr(exc, "code", "RUN_CONTINUATION_DISPATCH_FAILED"))
            raise ToolFailure(code, str(exc), category="runtime", retryable=bool(getattr(exc, "retryable", False))) from exc
        return {
            "run_id": run_id,
            "action_id": action_id,
            "driver_generation": generation,
            "status": "PROPOSING",
            "thread_id": thread_id,
            "turn_id": turn_id,
            "evidence_hash": evidence_hash,
            "recommended_next_action": "The admitted MCP driver is observing this exact bridge turn without copying the ChatWeb controller. Inspect task_control run_continuation=get/observe for a durable status; it will never launch a second turn when dispatch outcome is unknown.",
        }

    def _run_continuation_control(self, args: dict[str, Any]) -> dict[str, Any]:
        action = str(args.get("run_continuation_action") or "get").strip().lower()
        run_id = str(args.get("run_id") or "").strip()
        if not run_id:
            state = self.task_state.get()
            projection = state.get("orchestration") if isinstance(state.get("orchestration"), dict) else {}
            run_id = str(projection.get("run_id") or "").strip()
        if not run_id:
            raise ToolFailure("ORCHESTRATION_RUN_NOT_FOUND", "run_id is required when controlling a continuation grant.", category="not_found")
        if action == "get":
            continuation = self.orchestration_ledger.get_run_continuation(run_id)
            return {
                "run_id": run_id,
                "continuation": continuation,
                "status": "MISSING" if continuation is None else "OK",
                "continuation_environment_hash": self._run_continuation_environment_hash(),
                "environment_hash_schema_version": 1,
            }
        if action == "start":
            controller = self._require_hub_controller(run_id)
            if controller is None:
                raise ToolFailure("RUN_CONTINUATION_CONTROLLER_REQUIRED", "Starting a continuation driver requires the active authenticated ChatWeb controller.", category="security")
            return self._run_continuation_start_driver({**args, "run_id": run_id})
        if action == "observe":
            # Observing an already-issued grant never turns a missing controller
            # into write/acceptance authority. It only lets a caller obtain the
            # exact driver result; the driver itself remains MCP-owned.
            return self._run_continuation_observe_driver(run_id=run_id)
        if action == "reconcile":
            controller = self._require_hub_controller(run_id)
            if controller is None:
                raise ToolFailure("RUN_CONTINUATION_CONTROLLER_REQUIRED", "Effect reconciliation requires the active authenticated ChatWeb controller.", category="security")
            return self._run_continuation_reconcile_driver(
                run_id=run_id,
                controller_fencing_token=controller.get("fencing_token"),
            )
        if action not in {"pause", "resume", "revoke"}:
            raise ToolFailure("RUN_CONTINUATION_CONTROL_INVALID", "Unsupported run_continuation_action.", category="validation")
        controller = self._require_hub_controller(run_id)
        if controller is None:
            raise ToolFailure("RUN_CONTINUATION_CONTROLLER_REQUIRED", "Continuation control requires the active authenticated ChatWeb controller.", category="security")
        try:
            continuation = self.orchestration_ledger.set_run_continuation_state(
                run_id=run_id,
                action=action,
                reason=str(args.get("continuation_reason") or ""),
            )
        except RunContinuationError as exc:
            raise self._run_continuation_tool_failure(exc) from exc
        return {"run_id": run_id, "continuation": continuation, "status": action.upper(), "controller_fencing_token": controller.get("fencing_token")}
