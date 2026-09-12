from __future__ import annotations

"""Immutable continuation proposal, scope, policy, and consent contracts.

This leaf module owns pure validation and serialization. The ledger and runtime
driver remain in run_continuation.py so durable state and effects do not become
a second scheduler.
"""

import hashlib
import json
import re
import time
from typing import Any, Iterable


RUN_CONTINUATION_SCHEMA_VERSION = 3
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
    wave_id: str = "",
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
        "grant_wave_id": _require_opaque(wave_id, "wave_id") if wave_id else "",
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


def continuation_consent_descriptor(policy: dict[str, Any]) -> dict[str, Any]:
    """Return the exact, content-free terms a host user must approve once.

    The descriptor is built by the MCP from its immutable policy rather than
    supplied by ChatWeb. Electron only stages it after a user-visible, exact
    command; its receipt is then included in the durable policy hash.
    """
    if not isinstance(policy, dict):
        raise RunContinuationError("RUN_CONTINUATION_POLICY_INVALID", "Cannot build consent terms from an invalid continuation policy.")
    scope = {key: value for key, value in policy.items() if key != "consent"}
    return {
        "action": "authorize_bounded_continuation",
        "run_id": str(scope.get("run_id") or ""),
        "wave_id": str(scope.get("grant_wave_id") or ""),
        "workspace_id": str(scope.get("workspace_id") or ""),
        "problem_id": str(scope.get("problem_id") or ""),
        "problem_revision": int(scope.get("problem_revision") or 0),
        "contract_fingerprint": str(scope.get("contract_fingerprint") or ""),
        "tool_contract_sha256": str(scope.get("tool_contract_sha256") or ""),
        "runtime_behavior_fingerprint": str(scope.get("runtime_behavior_fingerprint") or ""),
        "activation_epoch_id": str(scope.get("activation_epoch_id") or ""),
        "activation_admission": str(scope.get("activation_admission") or ""),
        "issuer_client_id": str(scope.get("issuer_client_id") or ""),
        "scope_sha256": hashlib.sha256(_canonical_json(scope).encode("utf-8")).hexdigest(),
        "read_paths": list(scope.get("read_paths") or []),
        "write_paths": list(scope.get("write_paths") or []),
        "protected_paths": list(scope.get("protected_paths") or []),
        "approved_check_hashes": sorted(
            str(item.get("definition_hash") or "")
            for item in scope.get("approved_checks") or []
            if isinstance(item, dict)
        ),
        "max_duration_seconds": int(scope.get("max_duration_seconds") or 0),
        "max_decision_turns": int(scope.get("max_decision_turns") or 0),
        "max_patch_attempts": int(scope.get("max_patch_attempts") or 0),
    }


def bind_run_continuation_consent(policy: dict[str, Any], claimed: dict[str, Any]) -> dict[str, Any]:
    """Bind a claimed host receipt into the immutable durable policy."""
    descriptor = continuation_consent_descriptor(policy)
    if not isinstance(claimed, dict) or claimed.get("descriptor") != descriptor:
        raise RunContinuationError("RUN_CONTINUATION_CONSENT_MISMATCH", "The host consent does not match the immutable continuation terms.")
    receipt_id = _require_opaque(claimed.get("receipt_id"), "consent receipt_id")
    turn_id = _require_opaque(claimed.get("turn_id"), "consent turn_id")
    trace_id = _require_opaque(claimed.get("trace_id"), "consent trace_id")
    return {
        **policy,
        "consent": {
            "schema_version": 1,
            "receipt_id": receipt_id,
            "turn_id": turn_id,
            "trace_id": trace_id,
            "scope_sha256": descriptor["scope_sha256"],
        },
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
        "grant_wave_id": policy.get("grant_wave_id"),
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
        "consent": {
            "receipt_id": (policy.get("consent") or {}).get("receipt_id"),
            "scope_sha256": (policy.get("consent") or {}).get("scope_sha256"),
        } if isinstance(policy.get("consent"), dict) else None,
    }
