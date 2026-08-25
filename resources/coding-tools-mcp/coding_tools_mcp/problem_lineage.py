from __future__ import annotations

"""Authority-safe Problem Resolution Lineage in the canonical SQLite ledger.

V11 separates opaque identity, authority to change canonical state and later
policy eligibility.  It records a small typed contract revision, never raw
prompts, transcripts, command output, source content, or arbitrary JSON.
"""

import hashlib
import json
import re
import sqlite3
import time
import base64
import binascii
import unicodedata
from datetime import datetime
from typing import Any
from urllib.parse import unquote


PROBLEM_SCHEMA_VERSION = 11
PROBLEM_EVENT_SCHEMA_LEGACY = 1
PROBLEM_EVENT_SCHEMA_CURRENT = 2
PROBLEM_CAPSULE_MAX_BYTES = 8_192
PROBLEM_OUTCOME_CLAIM_MAX_BYTES = 131_072
_ID_RE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_FP_RE = re.compile(r"^[0-9a-f]{64}$")
_SECRET_RE = re.compile(r"(?:\b(?:api[_-]?key|secret|token|password|passwd|authorization)\b\s*[:=]|\bBearer\s+[A-Za-z0-9._~+/-]{12,}|\bsk-[A-Za-z0-9_-]{12,}|\bgh[pousr]_[A-Za-z0-9_-]{12,}|\bgithub_pat_[A-Za-z0-9_-]{12,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)", re.I)
_EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
_PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d[\d .()-]{7,}\d)(?!\d)")
_PERCENT_RE = re.compile(r"%(?:[0-9A-Fa-f]{2})")
_ESCAPED_ASCII_RE = re.compile(r"\\(?:u[0-9A-Fa-f]{4}|x[0-9A-Fa-f]{2})")
_BASE64_TOKEN_RE = re.compile(r"(?<![A-Za-z0-9_-])[A-Za-z0-9_-]{16,}={0,2}(?![A-Za-z0-9_-])")
_HEX_TOKEN_RE = re.compile(r"(?<![0-9A-Fa-f])[0-9A-Fa-f]{24,}(?![0-9A-Fa-f])")
_SECRET_SCAN_MAX_DEPTH = 2
_SECRET_SCAN_MAX_VARIANTS = 32
_SECRET_SCAN_MAX_DECODED_BYTES = 32_768

PROBLEM_OPERATIONS = frozenset({"open", "link", "observe_feedback", "provisional_resolve", "confirm", "reopen", "revise", "block", "abandon", "get"})
PROBLEM_RELATION_TYPES = frozenset({"OPEN", "LINK", "NO_RUN_CREATED", "ENGINEERING_ATTEMPT_BOUND", "USER_FEEDBACK", "PROVISIONAL_RESOLUTION", "CONFIRMED_RESOLUTION", "REOPEN", "REVISION", "BLOCK", "ABANDON"})
PROBLEM_LINK_STATUSES = frozenset({"EXACT", "AMBIGUOUS", "UNLINKED"})
PROBLEM_LINK_ROLES = frozenset({"PRIMARY", "SECONDARY"})
PROBLEM_STATES = frozenset({"OPEN", "PROVISIONALLY_RESOLVED", "RESOLVED_CONFIRMED", "REOPENED", "REVISED", "BLOCKED", "ABANDONED"})
PROBLEM_ENGINEERING_FLOORS = frozenset({"REQUIRED", "NOT_APPLICABLE", "UNKNOWN"})
PROBLEM_TASK_CLASSES = frozenset({"feature", "bugfix", "diagnose", "test_failure", "build_release", "custom", "refactor", "unknown"})
PROBLEM_WORK_ORIGINS = frozenset({"problem", "non_problem", "unknown"})
PROBLEM_RESOLUTION_CLAIMS = frozenset({"none", "full_problem"})
PROBLEM_FEEDBACK_INTENTS = frozenset({"CONFIRM_RESOLVED", "PARTIAL_RESOLUTION", "SAME_PROBLEM_STILL_FAILING", "CORRECT_UNDERSTANDING", "CORRECT_TARGET_OR_SCOPE", "CORRECT_TECHNICAL_RESULT", "CORRECT_PROOF_OR_VERIFICATION", "ADD_CONSTRAINT_OR_REQUIREMENT", "PROVIDE_NEW_EVIDENCE", "PREFERENCE_CHANGE", "NEW_PROBLEM", "SUPERSEDE_OR_CANCEL", "UNKNOWN"})
PROBLEM_CAUSAL_MECHANISMS = frozenset({"ASSISTANT_MISUNDERSTANDING", "WRONG_ROOT_CAUSE", "WRONG_TARGET_OR_WORKSPACE", "INSUFFICIENT_SOLUTION_SCOPE", "IMPLEMENTATION_DEFECT", "PROOF_ORACLE_GAP", "RUNTIME_OR_ENVIRONMENT_FAILURE", "SOURCE_OR_STATE_DRIFT", "STALE_CONTEXT_OR_REPLAY", "USER_NEW_INFORMATION", "REQUIREMENT_EVOLUTION", "USER_PREFERENCE_CHANGE", "EXTERNAL_DEPENDENCY_CHANGE", "UNKNOWN"})
PROBLEM_ECONOMIC_CLASSES = frozenset({"AVOIDABLE_CORRECTION", "PRODUCTIVE_CLARIFICATION", "LEGITIMATE_REQUIREMENT_GROWTH", "NEUTRAL_FOLLOWUP", "UNKNOWN"})
PROBLEM_PROVENANCE = frozenset({"HOST_OBSERVED", "CONTROLLER_REPORTED_EXPLICIT_USER", "DETERMINISTIC_EVIDENCE", "HUMAN_ANNOTATED", "SHADOW_MODEL_INFERRED", "UNKNOWN"})
PROBLEM_EVIDENCE_LEVELS = frozenset({"OBSERVED", "DERIVED_HIGH_CONFIDENCE", "INFERRED", "UNKNOWN"})
PROBLEM_OCCURRED_AT_SOURCES = frozenset({"RUNTIME", "HOST", "EXPLICIT_USER", "HUMAN_REVIEW", "EXTERNAL"})
PROBLEM_REASON_CODES = frozenset({"none", "user_confirmation", "explicit_same_problem_correction", "explicit_contract_revision", "blocked_external_dependency", "blocked_missing_problem_context", "abandoned_by_user", "no_run_created", "engineering_attempt_bound", "ambiguous_relation", "unlinked_relation"})

_CLOSED_STATES = frozenset({"RESOLVED_CONFIRMED", "ABANDONED"})
_AUTHORITY = {
    "open": frozenset({"RUNTIME_EXPLICIT_USER", "RUNTIME_HUMAN_REVIEW"}),
    "link": frozenset({"RUNTIME_BINDING", "RUNTIME_OBSERVATION"}),
    "observe_feedback": frozenset({"RUNTIME_OBSERVATION", "RUNTIME_EXPLICIT_USER", "RUNTIME_HUMAN_REVIEW"}),
    "provisional_resolve": frozenset({"RUNTIME_EOCL", "RUNTIME_RECONCILIATION"}),
    "confirm": frozenset({"RUNTIME_EXPLICIT_USER", "RUNTIME_HUMAN_REVIEW"}),
    "reopen": frozenset({"RUNTIME_EXPLICIT_USER", "RUNTIME_HUMAN_REVIEW"}),
    "revise": frozenset({"RUNTIME_EXPLICIT_USER", "RUNTIME_HUMAN_REVIEW"}),
    "block": frozenset({"RUNTIME_GUARD", "RUNTIME_OPERATOR", "RUNTIME_EXPLICIT_USER", "RUNTIME_HUMAN_REVIEW"}),
    "abandon": frozenset({"RUNTIME_OPERATOR", "RUNTIME_EXPLICIT_USER", "RUNTIME_HUMAN_REVIEW"}),
}
_ELIGIBLE_AUTHORITY_PROVENANCE = frozenset({
    ("RUNTIME_EXPLICIT_USER", "CONTROLLER_REPORTED_EXPLICIT_USER"),
    ("RUNTIME_HUMAN_REVIEW", "HUMAN_ANNOTATED"),
    ("RUNTIME_BINDING", "DETERMINISTIC_EVIDENCE"),
    ("RUNTIME_GUARD", "DETERMINISTIC_EVIDENCE"),
    ("RUNTIME_EOCL", "DETERMINISTIC_EVIDENCE"),
    ("RUNTIME_RECONCILIATION", "DETERMINISTIC_EVIDENCE"),
})


class ProblemLineageError(ValueError):
    pass


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def _text(value: Any, name: str, *, required: bool = False, limit: int = 128) -> str:
    result = str(value or "").strip()
    if len(result) > limit:
        raise ProblemLineageError(f"{name} exceeds its bounded length")
    if required and not result:
        raise ProblemLineageError(f"{name} is required")
    return result


def _opaque(value: Any, name: str, *, required: bool = False) -> str:
    result = _text(value, name, required=required)
    if result and not _ID_RE.fullmatch(result):
        raise ProblemLineageError(f"{name} must be an opaque bounded identifier")
    return result


def _upper(value: Any, name: str, allowed: frozenset[str], default: str) -> str:
    result = _text(value, name).upper() or default
    if result not in allowed:
        raise ProblemLineageError(f"{name} is invalid")
    return result


def _lower(value: Any, name: str, allowed: frozenset[str], default: str) -> str:
    result = _text(value, name).lower() or default
    if result not in allowed:
        raise ProblemLineageError(f"{name} is invalid")
    return result


def _integer(value: Any, name: str, *, default: int = 0, required: bool = False) -> int:
    if value is None or value == "":
        if required:
            raise ProblemLineageError(f"{name} is required")
        return default
    if isinstance(value, bool) or not isinstance(value, int) or value < 0 or value > 1_000_000:
        raise ProblemLineageError(f"{name} must be a bounded nonnegative integer")
    if required and value < 1:
        raise ProblemLineageError(f"{name} must be positive")
    return value


def _timestamp(value: Any, name: str) -> str:
    result = _text(value, name, limit=128)
    if not result:
        return ""
    try:
        parsed = datetime.fromisoformat(result.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ProblemLineageError(f"{name} must be an offset-aware ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ProblemLineageError(f"{name} must be an offset-aware ISO-8601 timestamp")
    return result


def _decoded_printable(value: bytes) -> str | None:
    if not value or len(value) > _SECRET_SCAN_MAX_DECODED_BYTES:
        return None
    try:
        text = value.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return None
    return text if all(char.isprintable() or char in "\t\r\n" for char in text) else None


def _escape_ascii_variant(value: str) -> str | None:
    if not _ESCAPED_ASCII_RE.search(value):
        return None
    try:
        return _ESCAPED_ASCII_RE.sub(lambda item: chr(int(item.group(0)[2:], 16)), value)
    except (TypeError, ValueError):
        return None


def _encoded_text_variants(value: str) -> tuple[str, ...]:
    """Return bounded, syntax-triggered scan variants without guessing entropy."""
    pending = [unicodedata.normalize("NFKC", value)]
    variants: list[str] = []
    seen: set[str] = set()
    decoded_bytes = 0
    for depth in range(_SECRET_SCAN_MAX_DEPTH + 1):
        next_pending: list[str] = []
        for current in pending:
            if current in seen:
                continue
            seen.add(current); variants.append(current)
            folded = "".join(char for char in current if unicodedata.category(char) != "Cf")
            if folded not in seen:
                variants.append(folded); seen.add(folded)
            if len(variants) > _SECRET_SCAN_MAX_VARIANTS:
                raise ProblemLineageError("contract capsule privacy scan exceeded its bounded variant budget")
            if depth == _SECRET_SCAN_MAX_DEPTH:
                continue
            if _PERCENT_RE.search(current):
                candidate = unquote(current)
                if candidate != current:
                    next_pending.append(candidate)
            escaped = _escape_ascii_variant(current)
            if escaped is not None and escaped != current:
                next_pending.append(escaped)
            for token in _BASE64_TOKEN_RE.findall(current):
                padded = token + "=" * (-len(token) % 4)
                try:
                    decoded = base64.b64decode(padded, altchars=b"-_", validate=True)
                except (ValueError, binascii.Error):
                    continue
                decoded_bytes += len(decoded)
                if decoded_bytes > _SECRET_SCAN_MAX_DECODED_BYTES:
                    raise ProblemLineageError("contract capsule privacy scan exceeded its bounded decoded-byte budget")
                candidate = _decoded_printable(decoded)
                if candidate is not None:
                    next_pending.append(candidate)
            for token in _HEX_TOKEN_RE.findall(current):
                try:
                    decoded = bytes.fromhex(token)
                except ValueError:
                    continue
                decoded_bytes += len(decoded)
                if decoded_bytes > _SECRET_SCAN_MAX_DECODED_BYTES:
                    raise ProblemLineageError("contract capsule privacy scan exceeded its bounded decoded-byte budget")
                candidate = _decoded_printable(decoded)
                if candidate is not None:
                    next_pending.append(candidate)
        pending = next_pending
    return tuple(variants)


def _safe_capsule_text(value: Any, name: str, *, limit: int, required: bool = False) -> str:
    result = unicodedata.normalize("NFKC", str(value or "")).strip()
    if len(result) > limit:
        raise ProblemLineageError(f"{name} exceeds its bounded length")
    if required and not result:
        raise ProblemLineageError(f"{name} is required")
    for variant in _encoded_text_variants(result):
        if _SECRET_RE.search(variant):
            raise ProblemLineageError("contract capsule contains credential-like material; use an approved opaque reference")
        if _EMAIL_RE.search(variant) or _PHONE_RE.search(variant):
            raise ProblemLineageError("contract capsule contains personal data; abstract it before durable storage")
    return result


def _capsule(value: Any, *, required: bool) -> dict[str, Any] | None:
    if value is None:
        if required:
            raise ProblemLineageError("typed contract_capsule is required")
        return None
    if not isinstance(value, dict):
        raise ProblemLineageError("contract_capsule must be an object")
    keys = {"objective_summary", "acceptance_criteria", "protected_invariants", "constraints", "unresolved_conditions"}
    if set(value) - keys:
        raise ProblemLineageError("contract_capsule contains disallowed fields")
    criteria = value.get("acceptance_criteria")
    if not isinstance(criteria, list) or not criteria or len(criteria) > 100:
        raise ProblemLineageError("acceptance_criteria must be a non-empty bounded list")
    normalized_criteria: list[dict[str, str]] = []
    ids: set[str] = set()
    for item in criteria:
        if not isinstance(item, dict) or set(item) != {"criterion_id", "summary"}:
            raise ProblemLineageError("each acceptance criterion must contain exactly criterion_id and summary")
        criterion_id = _opaque(item.get("criterion_id"), "criterion_id", required=True)
        if criterion_id in ids:
            raise ProblemLineageError("acceptance criterion IDs must be stable and unique")
        ids.add(criterion_id)
        normalized_criteria.append({"criterion_id": criterion_id, "summary": _safe_capsule_text(item.get("summary"), "criterion summary", limit=800, required=True)})

    def list_of_text(name: str) -> list[str]:
        items = value.get(name, [])
        if not isinstance(items, list) or len(items) > 40:
            raise ProblemLineageError(f"{name} must be a bounded list")
        return [_safe_capsule_text(item, name, limit=800, required=True) for item in items]

    normalized = {
        "objective_summary": _safe_capsule_text(value.get("objective_summary"), "objective_summary", limit=2_000, required=True),
        "acceptance_criteria": normalized_criteria,
        "protected_invariants": list_of_text("protected_invariants"),
        "constraints": list_of_text("constraints"),
        "unresolved_conditions": list_of_text("unresolved_conditions"),
    }
    if len(_json(normalized).encode("utf-8")) > PROBLEM_CAPSULE_MAX_BYTES:
        raise ProblemLineageError("contract_capsule exceeds the 8 KiB durable privacy budget")
    return normalized


def _fingerprints(capsule: dict[str, Any]) -> tuple[str, str]:
    return _sha(_json(capsule)), _sha(_json(capsule["acceptance_criteria"]))


def _normalize(event: Any) -> dict[str, Any]:
    if not isinstance(event, dict):
        raise ProblemLineageError("problem_event must be an object")
    allowed = {
        "operation", "event_id", "problem_id", "problem_revision", "expected_revision", "expected_contract_fingerprint",
        "task_id", "turn_id", "trace_id", "run_id", "wave_id", "capsule_id", "conversation_epoch",
        "task_class", "engineering_floor", "relation_type", "link_status", "link_role", "feedback_intent",
        "causal_mechanism", "economic_class", "provenance", "evidence_level", "reason_code",
        "contract_capsule", "occurred_at", "occurred_at_source",
    }
    if set(event) - allowed:
        raise ProblemLineageError("problem_event contains disallowed fields")
    operation = _lower(event.get("operation"), "operation", PROBLEM_OPERATIONS, "get")
    event_id = _opaque(event.get("event_id"), "event_id", required=operation != "get")
    problem_id = _opaque(event.get("problem_id"), "problem_id")
    if operation == "open" and not problem_id:
        problem_id = "prl-" + _sha(event_id)[:32]
    link_status = _upper(event.get("link_status"), "link_status", PROBLEM_LINK_STATUSES, "EXACT")
    if operation == "open" and link_status != "EXACT":
        raise ProblemLineageError("open must create an exact canonical problem revision")
    if link_status != "EXACT" and operation not in {"link", "observe_feedback"}:
        raise ProblemLineageError("only link or observation events may be ambiguous or unlinked")
    if operation not in {"get", "open"} and link_status == "EXACT" and not problem_id:
        raise ProblemLineageError("exact problem event requires problem_id")
    if link_status != "EXACT" and problem_id:
        raise ProblemLineageError("ambiguous or unlinked events must not attach a problem_id")
    revision = _integer(event.get("problem_revision"), "problem_revision", required=link_status == "EXACT" and operation not in {"open", "revise", "get"})
    if link_status != "EXACT" and revision:
        raise ProblemLineageError("ambiguous or unlinked events must not attach a problem_revision")
    if operation == "open" and revision not in {0, 1}:
        raise ProblemLineageError("open creates revision 1; caller cannot select another revision")
    if operation == "revise" and revision:
        raise ProblemLineageError("revise derives its new revision after compare-and-swap")
    relation = {"open": "OPEN", "link": "LINK", "observe_feedback": "USER_FEEDBACK", "provisional_resolve": "PROVISIONAL_RESOLUTION", "confirm": "CONFIRMED_RESOLUTION", "reopen": "REOPEN", "revise": "REVISION", "block": "BLOCK", "abandon": "ABANDON", "get": "LINK"}[operation]
    allowed_relations = {
        "open": {"OPEN"},
        "link": {"LINK", "NO_RUN_CREATED", "ENGINEERING_ATTEMPT_BOUND"},
        "observe_feedback": {"USER_FEEDBACK"},
        "provisional_resolve": {"PROVISIONAL_RESOLUTION"},
        "confirm": {"CONFIRMED_RESOLUTION"},
        "reopen": {"REOPEN"},
        "revise": {"REVISION"},
        "block": {"BLOCK"},
        "abandon": {"ABANDON"},
        "get": {"LINK"},
    }
    occurred_at = _timestamp(event.get("occurred_at"), "occurred_at")
    occurred_source = _upper(event.get("occurred_at_source"), "occurred_at_source", PROBLEM_OCCURRED_AT_SOURCES, "") if occurred_at else ""
    if occurred_at and not occurred_source:
        raise ProblemLineageError("occurred_at_source is required when occurred_at is supplied")
    expected_fp = _text(event.get("expected_contract_fingerprint"), "expected_contract_fingerprint", limit=64).lower()
    if expected_fp and not _FP_RE.fullmatch(expected_fp):
        raise ProblemLineageError("expected_contract_fingerprint must be a SHA-256 digest")
    if operation == "revise" and not expected_fp:
        raise ProblemLineageError("revise requires expected_contract_fingerprint")
    relation_type = _upper(event.get("relation_type"), "relation_type", PROBLEM_RELATION_TYPES, relation)
    if relation_type not in allowed_relations[operation]:
        raise ProblemLineageError("relation_type is not valid for this explicit problem operation")
    submitted_reason = _lower(event.get("reason_code"), "reason_code", PROBLEM_REASON_CODES, "none")
    derived_reason = {
        "confirm": "user_confirmation",
        "reopen": "explicit_same_problem_correction",
        "revise": "explicit_contract_revision",
        "abandon": "abandoned_by_user",
    }.get(operation)
    if derived_reason:
        if submitted_reason not in {"none", derived_reason}:
            raise ProblemLineageError("reason_code conflicts with the explicit canonical transition")
        submitted_reason = derived_reason
    elif operation == "block" and submitted_reason not in {"blocked_external_dependency", "blocked_missing_problem_context"}:
        raise ProblemLineageError("block requires a typed blocked reason_code")
    return {
        "operation": operation, "event_id": event_id, "problem_id": problem_id, "problem_revision": revision,
        "expected_revision": _integer(event.get("expected_revision"), "expected_revision", required=operation == "revise"), "expected_contract_fingerprint": expected_fp,
        "task_id": _opaque(event.get("task_id"), "task_id"), "turn_id": _opaque(event.get("turn_id"), "turn_id"), "trace_id": _opaque(event.get("trace_id"), "trace_id"), "run_id": _opaque(event.get("run_id"), "run_id"), "wave_id": _opaque(event.get("wave_id"), "wave_id"), "capsule_id": _opaque(event.get("capsule_id"), "capsule_id"), "conversation_epoch": _integer(event.get("conversation_epoch"), "conversation_epoch"),
        "task_class": _lower(event.get("task_class"), "task_class", PROBLEM_TASK_CLASSES, "unknown"), "engineering_floor": _upper(event.get("engineering_floor"), "engineering_floor", PROBLEM_ENGINEERING_FLOORS, "UNKNOWN"),
        "relation_type": relation_type, "link_status": link_status, "link_role": _upper(event.get("link_role"), "link_role", PROBLEM_LINK_ROLES, "PRIMARY"),
        "feedback_intent": _upper(event.get("feedback_intent"), "feedback_intent", PROBLEM_FEEDBACK_INTENTS, "UNKNOWN"), "causal_mechanism": _upper(event.get("causal_mechanism"), "causal_mechanism", PROBLEM_CAUSAL_MECHANISMS, "UNKNOWN"), "economic_class": _upper(event.get("economic_class"), "economic_class", PROBLEM_ECONOMIC_CLASSES, "UNKNOWN"),
        "provenance": _upper(event.get("provenance"), "provenance", PROBLEM_PROVENANCE, "UNKNOWN"), "evidence_level": _upper(event.get("evidence_level"), "evidence_level", PROBLEM_EVIDENCE_LEVELS, "UNKNOWN"), "reason_code": submitted_reason,
        "contract_capsule": _capsule(event.get("contract_capsule"), required=operation in {"open", "revise"}), "occurred_at": occurred_at, "occurred_at_source": occurred_source,
    }


def _event(row: sqlite3.Row) -> dict[str, Any]:
    keys = set(row.keys())
    def get(key: str, default: Any = "") -> Any: return row[key] if key in keys else default
    schema = int(get("event_schema_version", 1))
    raw_eligible = bool(get("eligible_for_policy", 0))
    return {"seq": int(get("seq", 0)), "event_id": str(get("event_id")), "event_schema_version": schema, "problem_id": get("problem_id") or None, "problem_revision": int(get("problem_revision", 0) or 0) or None, "task_id": str(get("task_id")), "turn_id": str(get("turn_id")), "trace_id": str(get("trace_id")), "run_id": str(get("run_id")), "wave_id": str(get("wave_id")), "capsule_id": str(get("capsule_id")), "conversation_epoch": int(get("conversation_epoch", 0) or 0), "relation_type": str(get("relation_type")), "link_status": str(get("link_status")), "link_role": str(get("link_role")), "feedback_intent": str(get("feedback_intent")), "causal_mechanism": str(get("causal_mechanism")), "economic_class": str(get("economic_class")), "provenance": str(get("provenance")), "evidence_level": str(get("evidence_level")), "eligible_for_policy": raw_eligible if schema > 1 else False, "legacy_eligible_for_policy": raw_eligible if schema == 1 else False, "transition_authority": str(get("transition_authority")), "state_before": str(get("state_before")), "state_after": str(get("state_after")), "reason_code": str(get("reason_code")), "criteria_count": int(get("criteria_count", 0) or 0), "criteria_fingerprint": str(get("criteria_fingerprint")), "contract_fingerprint": str(get("contract_fingerprint")), "recorded_at": str(get("recorded_at")), "occurred_at": str(get("occurred_at")), "occurred_at_source": str(get("occurred_at_source")), "clock_authority": str(get("clock_authority")), "event_time": str(get("event_time")), "prev_hash": str(get("prev_hash")), "event_hash": str(get("event_hash"))}


def _revision(row: sqlite3.Row) -> dict[str, Any]:
    try: capsule = json.loads(str(row["typed_contract_capsule"] or ""))
    except (TypeError, json.JSONDecodeError): capsule = None
    valid = isinstance(capsule, dict) and _sha(_json(capsule)) == str(row["contract_fingerprint"] or "")
    return {"problem_id": str(row["problem_id"]), "revision": int(row["revision"]), "contract_fingerprint": str(row["contract_fingerprint"]), "criteria_fingerprint": str(row["criteria_fingerprint"]), "criteria_count": int(row["criteria_count"]), "task_class": str(row["task_class"]), "engineering_floor": str(row["engineering_floor"]), "created_event_seq": int(row["created_event_seq"]), "created_at": str(row["created_at"]), "creation_authority": str(row["creation_authority"]), "capsule_valid": valid, "capsule": capsule if valid else None}


def problem_event_hash_material(value: dict[str, Any], *, state_before: str, state_after: str, prev_hash: str) -> dict[str, Any]:
    if int(value.get("event_schema_version") or 1) <= 1:
        names = ("event_id", "problem_id", "task_id", "turn_id", "trace_id", "run_id", "wave_id", "capsule_id", "conversation_epoch", "relation_type", "link_status", "link_role", "feedback_intent", "causal_mechanism", "economic_class", "provenance", "evidence_level", "eligible_for_policy", "reason_code", "criteria_count", "criteria_fingerprint", "event_time")
        material = {name: value.get(name) for name in names}
        material["eligible_for_policy"] = value.get("legacy_eligible_for_policy", value.get("eligible_for_policy"))
        return {**material, "state_before": state_before, "state_after": state_after, "prev_hash": prev_hash}
    names = ("event_schema_version", "event_id", "problem_id", "problem_revision", "task_id", "turn_id", "trace_id", "run_id", "wave_id", "capsule_id", "conversation_epoch", "relation_type", "link_status", "link_role", "feedback_intent", "causal_mechanism", "economic_class", "provenance", "evidence_level", "eligible_for_policy", "transition_authority", "reason_code", "criteria_count", "criteria_fingerprint", "contract_fingerprint", "recorded_at", "occurred_at", "occurred_at_source", "clock_authority")
    return {**{name: value.get(name) for name in names}, "state_before": state_before, "state_after": state_after, "prev_hash": prev_hash}


_event_hash_material = problem_event_hash_material


class ProblemLineageLedgerMixin:
    @staticmethod
    def _problem_ensure_schema(connection: sqlite3.Connection) -> None:
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS problem_threads (
                problem_id TEXT PRIMARY KEY,current_revision INTEGER NOT NULL,resolution_state TEXT NOT NULL,task_class TEXT NOT NULL,engineering_floor TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,closed_at TEXT,latest_problem_event_seq INTEGER NOT NULL DEFAULT 0,latest_problem_event_hash TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS problem_revisions (
                problem_id TEXT NOT NULL REFERENCES problem_threads(problem_id) ON DELETE RESTRICT,revision INTEGER NOT NULL CHECK(revision>=1),contract_fingerprint TEXT NOT NULL,criteria_fingerprint TEXT NOT NULL,criteria_count INTEGER NOT NULL,typed_contract_capsule TEXT NOT NULL,task_class TEXT NOT NULL,engineering_floor TEXT NOT NULL,created_event_seq INTEGER NOT NULL DEFAULT 0,created_at TEXT NOT NULL,creation_authority TEXT NOT NULL,PRIMARY KEY(problem_id,revision)
            );
            CREATE TABLE IF NOT EXISTS problem_events (
                seq INTEGER PRIMARY KEY AUTOINCREMENT,event_id TEXT NOT NULL UNIQUE,event_schema_version INTEGER NOT NULL DEFAULT 2,problem_id TEXT REFERENCES problem_threads(problem_id) ON DELETE RESTRICT,problem_revision INTEGER,task_id TEXT NOT NULL DEFAULT '',turn_id TEXT NOT NULL DEFAULT '',trace_id TEXT NOT NULL DEFAULT '',run_id TEXT NOT NULL DEFAULT '',wave_id TEXT NOT NULL DEFAULT '',capsule_id TEXT NOT NULL DEFAULT '',conversation_epoch INTEGER NOT NULL DEFAULT 0,relation_type TEXT NOT NULL,link_status TEXT NOT NULL,link_role TEXT NOT NULL,feedback_intent TEXT NOT NULL,causal_mechanism TEXT NOT NULL,economic_class TEXT NOT NULL,provenance TEXT NOT NULL,evidence_level TEXT NOT NULL,eligible_for_policy INTEGER NOT NULL DEFAULT 0,transition_authority TEXT NOT NULL DEFAULT '',state_before TEXT NOT NULL DEFAULT '',state_after TEXT NOT NULL DEFAULT '',reason_code TEXT NOT NULL DEFAULT 'none',criteria_count INTEGER NOT NULL DEFAULT 0,criteria_fingerprint TEXT NOT NULL DEFAULT '',contract_fingerprint TEXT NOT NULL DEFAULT '',request_hash TEXT NOT NULL,recorded_at TEXT,occurred_at TEXT NOT NULL DEFAULT '',occurred_at_source TEXT NOT NULL DEFAULT '',clock_authority TEXT NOT NULL DEFAULT '',event_time TEXT NOT NULL DEFAULT '',prev_hash TEXT NOT NULL DEFAULT '',event_hash TEXT NOT NULL,
                CHECK((event_schema_version=1) OR (event_schema_version=2 AND recorded_at IS NOT NULL AND recorded_at<>'')),
                CHECK((event_schema_version=1) OR ((occurred_at='' AND occurred_at_source='' AND clock_authority='') OR (occurred_at<>'' AND occurred_at_source<>'' AND clock_authority<>''))),
                CHECK((event_schema_version=1) OR ((link_status='EXACT' AND problem_id IS NOT NULL AND problem_revision IS NOT NULL) OR (link_status<>'EXACT' AND problem_id IS NULL AND problem_revision IS NULL))),
                FOREIGN KEY(problem_id,problem_revision) REFERENCES problem_revisions(problem_id,revision) ON DELETE RESTRICT
            );
            CREATE INDEX IF NOT EXISTS idx_problem_events_problem_seq ON problem_events(problem_id,seq);
            CREATE INDEX IF NOT EXISTS idx_problem_events_problem_revision_seq ON problem_events(problem_id,problem_revision,seq);
            CREATE INDEX IF NOT EXISTS idx_problem_events_task_turn ON problem_events(task_id,turn_id,seq);
            CREATE INDEX IF NOT EXISTS idx_problem_events_run_wave ON problem_events(run_id,wave_id,seq);
            CREATE UNIQUE INDEX IF NOT EXISTS idx_problem_events_one_primary_run_binding ON problem_events(run_id) WHERE run_id<>'' AND link_status='EXACT' AND link_role='PRIMARY' AND relation_type IN ('LINK','ENGINEERING_ATTEMPT_BOUND');
        """)

    def problem_lineage_schema_version(self) -> int:
        with self._lock, self._connect() as connection:
            return int(connection.execute("PRAGMA user_version").fetchone()[0])

    @classmethod
    def _upgrade_v10(cls, connection: sqlite3.Connection) -> None:
        for name in ("idx_problem_events_problem_seq", "idx_problem_events_task_turn", "idx_problem_events_run_wave", "idx_problem_events_one_primary_run_binding"):
            connection.execute(f"DROP INDEX IF EXISTS {name}")
        connection.execute("ALTER TABLE problem_events RENAME TO problem_events_v10_legacy")
        cls._problem_ensure_schema(connection)
        connection.execute("""INSERT INTO problem_events(seq,event_id,event_schema_version,problem_id,problem_revision,task_id,turn_id,trace_id,run_id,wave_id,capsule_id,conversation_epoch,relation_type,link_status,link_role,feedback_intent,causal_mechanism,economic_class,provenance,evidence_level,eligible_for_policy,transition_authority,state_before,state_after,reason_code,criteria_count,criteria_fingerprint,contract_fingerprint,request_hash,recorded_at,occurred_at,occurred_at_source,clock_authority,event_time,prev_hash,event_hash)
            SELECT seq,event_id,1,problem_id,NULL,task_id,turn_id,trace_id,run_id,wave_id,capsule_id,conversation_epoch,relation_type,link_status,link_role,feedback_intent,causal_mechanism,economic_class,provenance,evidence_level,eligible_for_policy,'',state_before,state_after,reason_code,criteria_count,criteria_fingerprint,'',request_hash,NULL,'','','',event_time,prev_hash,event_hash FROM problem_events_v10_legacy ORDER BY seq""")
        connection.execute("DROP TABLE problem_events_v10_legacy")

    def migrate_problem_lineage_schema(self, *, expected_schema_version: int = 9) -> dict[str, Any]:
        if expected_schema_version not in {9, 10}:
            raise ProblemLineageError("PRL migration requires explicit expected schema version 9 or 10")
        with self._lock, self._connect() as connection:
            current = int(connection.execute("PRAGMA user_version").fetchone()[0])
            if current == PROBLEM_SCHEMA_VERSION:
                return {"migrated": False, "schema_version": current, "legacy_events_preserved": True}
            if current != expected_schema_version:
                raise ProblemLineageError(f"PRL migration requires schema v{expected_schema_version}, found v{current}")
            connection.execute("BEGIN IMMEDIATE")
            if current == 10: self._upgrade_v10(connection)
            else: self._problem_ensure_schema(connection)
            connection.execute(f"PRAGMA user_version={PROBLEM_SCHEMA_VERSION}")
        return {"migrated": True, "schema_version": PROBLEM_SCHEMA_VERSION, "legacy_events_preserved": True}

    def _require_problem_schema(self, connection: sqlite3.Connection) -> None:
        if int(connection.execute("PRAGMA user_version").fetchone()[0]) != PROBLEM_SCHEMA_VERSION:
            raise ProblemLineageError("PRL schema is not activated; supported v9/v10-to-v11 migration authority is required")

    @staticmethod
    def _revision_row(connection: sqlite3.Connection, problem_id: str, revision: int) -> sqlite3.Row | None:
        return connection.execute("SELECT * FROM problem_revisions WHERE problem_id=? AND revision=?", (problem_id, revision)).fetchone()

    @staticmethod
    def _clock_authority(event: dict[str, Any], authority: str) -> str:
        if not event["occurred_at"]: return ""
        source = event["occurred_at_source"]
        allowed = {("RUNTIME", "RUNTIME_EOCL"): "RUNTIME_OWNED", ("RUNTIME", "RUNTIME_RECONCILIATION"): "RUNTIME_OWNED", ("RUNTIME", "RUNTIME_GUARD"): "RUNTIME_OWNED", ("HOST", "RUNTIME_BINDING"): "HOST_ATTESTED", ("HOST", "RUNTIME_OBSERVATION"): "HOST_ATTESTED", ("EXPLICIT_USER", "RUNTIME_EXPLICIT_USER"): "EXPLICIT_USER_ATTESTED", ("HUMAN_REVIEW", "RUNTIME_HUMAN_REVIEW"): "HUMAN_REVIEWED", ("EXTERNAL", "RUNTIME_HUMAN_REVIEW"): "AUTHORIZED_EXTERNAL", ("EXTERNAL", "RUNTIME_OPERATOR"): "AUTHORIZED_EXTERNAL"}
        result = allowed.get((source, authority))
        if not result: raise ProblemLineageError("occurred_at is not trusted by the supplied runtime authority")
        return result

    @staticmethod
    def _after(operation: str, before: str) -> str:
        return {"open": "OPEN", "revise": "OPEN", "provisional_resolve": "PROVISIONALLY_RESOLVED", "confirm": "RESOLVED_CONFIRMED", "reopen": "REOPENED", "block": "BLOCKED", "abandon": "ABANDONED"}.get(operation, before)

    @staticmethod
    def _allowed_transition(before: str, after: str, operation: str) -> bool:
        if operation in {"link", "observe_feedback"}: return before == after
        if operation == "revise": return after == "OPEN"
        return after in {"OPEN": {"OPEN", "PROVISIONALLY_RESOLVED", "REOPENED", "REVISED", "BLOCKED", "ABANDONED"}, "REOPENED": {"REOPENED", "PROVISIONALLY_RESOLVED", "REVISED", "BLOCKED", "ABANDONED"}, "REVISED": {"REVISED", "PROVISIONALLY_RESOLVED", "REOPENED", "BLOCKED", "ABANDONED"}, "PROVISIONALLY_RESOLVED": {"PROVISIONALLY_RESOLVED", "RESOLVED_CONFIRMED", "REOPENED", "REVISED", "BLOCKED", "ABANDONED"}, "RESOLVED_CONFIRMED": {"RESOLVED_CONFIRMED", "REOPENED", "REVISED"}, "BLOCKED": {"BLOCKED", "REOPENED", "REVISED", "ABANDONED"}, "ABANDONED": {"ABANDONED", "REOPENED", "REVISED"}}.get(before, set())

    def _record_eligible(self, connection: sqlite3.Connection, event: dict[str, Any], authority: str, row: sqlite3.Row | None, clock: str) -> bool:
        if event["link_status"] != "EXACT" or row is None or event["operation"] == "observe_feedback": return False
        if (authority, event["provenance"]) not in _ELIGIBLE_AUTHORITY_PROVENANCE or event["evidence_level"] not in {"OBSERVED", "DERIVED_HIGH_CONFIDENCE"}: return False
        if event["occurred_at"] and not clock: return False
        if event["operation"] == "link" and event["run_id"]:
            wave = connection.execute("SELECT metadata_json FROM waves WHERE run_id=? AND wave_id=?", (event["run_id"], event["wave_id"])).fetchone()
            try:
                context = json.loads(wave["metadata_json"] or "{}").get("problem_resolution", {}) if wave is not None else {}
            except (TypeError, json.JSONDecodeError):
                context = {}
            if not isinstance(context, dict) or context.get("work_origin") != "problem": return False
        return bool(authority and _revision(row)["capsule_valid"])

    def problem_record_event(
        self,
        event: dict[str, Any],
        *,
        now: str,
        authority_context: str = "",
        reconciliation: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        normalized = _normalize(event)
        if normalized["operation"] == "get": raise ProblemLineageError("get does not record a problem event")
        if authority_context not in _AUTHORITY.get(normalized["operation"], frozenset()): raise ProblemLineageError("problem operation lacks the required runtime transition authority")
        recorded_at = _timestamp(now, "runtime recorded_at")
        clock = self._clock_authority(normalized, authority_context)
        with self._lock, self._connect() as connection:
            self._require_problem_schema(connection); connection.execute("BEGIN IMMEDIATE")
            if reconciliation is not None:
                self._problem_validate_reconciliation(connection, reconciliation)
            contract = normalized["contract_capsule"]
            input_fp = _fingerprints(contract)[0] if contract else ""
            material = {**{key: value for key, value in normalized.items() if key != "contract_capsule"}, "contract_fingerprint": input_fp, "authority_context": authority_context}
            request_hash = _sha(_json(material))
            existing = connection.execute("SELECT * FROM problem_events WHERE event_id=?", (normalized["event_id"],)).fetchone()
            if existing is not None:
                if str(existing["request_hash"] or "") != request_hash: raise ProblemLineageError("problem event id conflicts with immutable prior bytes")
                projection = _event(existing)
                return {"recorded": False, "idempotent": True, "event": projection, "thread": self.problem_get(str(projection.get("problem_id") or ""), connection=connection)}
            thread = connection.execute("SELECT * FROM problem_threads WHERE problem_id=?", (normalized["problem_id"],)).fetchone() if normalized["problem_id"] else None
            revision_row: sqlite3.Row | None = None; event_revision = 0; created_revision = False; contract_fp = ""; criteria_fp = ""; criteria_count = 0
            if normalized["operation"] == "open":
                if thread is not None: raise ProblemLineageError("open cannot reuse an existing problem_id")
                assert contract is not None
                contract_fp, criteria_fp = _fingerprints(contract); criteria_count = len(contract["acceptance_criteria"]); event_revision = 1
                connection.execute("INSERT INTO problem_threads(problem_id,current_revision,resolution_state,task_class,engineering_floor,created_at,updated_at,closed_at,latest_problem_event_seq,latest_problem_event_hash) VALUES(?,?,?,?,?,?,?,?,?,?)", (normalized["problem_id"], 1, "OPEN", normalized["task_class"], normalized["engineering_floor"], recorded_at, recorded_at, None, 0, ""))
                connection.execute("INSERT INTO problem_revisions(problem_id,revision,contract_fingerprint,criteria_fingerprint,criteria_count,typed_contract_capsule,task_class,engineering_floor,created_event_seq,created_at,creation_authority) VALUES(?,?,?,?,?,?,?,?,?,?,?)", (normalized["problem_id"], 1, contract_fp, criteria_fp, criteria_count, _json(contract), normalized["task_class"], normalized["engineering_floor"], 0, recorded_at, authority_context))
                thread = connection.execute("SELECT * FROM problem_threads WHERE problem_id=?", (normalized["problem_id"],)).fetchone(); revision_row = self._revision_row(connection, normalized["problem_id"], 1); before, after = "", "OPEN"
            elif normalized["link_status"] != "EXACT":
                before = after = ""
            else:
                if thread is None: raise ProblemLineageError("exact problem event references an unknown problem_id")
                before = str(thread["resolution_state"])
                if normalized["operation"] == "revise":
                    current = int(thread["current_revision"]); current_row = self._revision_row(connection, normalized["problem_id"], current)
                    if current_row is None: raise ProblemLineageError("BLOCKED_MISSING_PROBLEM_CONTEXT")
                    if normalized["expected_revision"] != current or normalized["expected_contract_fingerprint"] != str(current_row["contract_fingerprint"]): raise ProblemLineageError("problem revision compare-and-swap failed")
                    assert contract is not None
                    contract_fp, criteria_fp = _fingerprints(contract); criteria_count = len(contract["acceptance_criteria"]); event_revision = current + 1; created_revision = True; after = self._after("revise", before)
                    connection.execute("INSERT INTO problem_revisions(problem_id,revision,contract_fingerprint,criteria_fingerprint,criteria_count,typed_contract_capsule,task_class,engineering_floor,created_event_seq,created_at,creation_authority) VALUES(?,?,?,?,?,?,?,?,?,?,?)", (normalized["problem_id"], event_revision, contract_fp, criteria_fp, criteria_count, _json(contract), normalized["task_class"], normalized["engineering_floor"], 0, recorded_at, authority_context))
                    revision_row = self._revision_row(connection, normalized["problem_id"], event_revision)
                else:
                    event_revision = normalized["problem_revision"]; revision_row = self._revision_row(connection, normalized["problem_id"], event_revision)
                    if revision_row is None: raise ProblemLineageError("BLOCKED_MISSING_PROBLEM_CONTEXT")
                    if normalized["operation"] not in {"link", "observe_feedback"} and event_revision != int(thread["current_revision"]): raise ProblemLineageError("canonical transition must target the exact current problem revision")
                    after = self._after(normalized["operation"], before); contract_fp = str(revision_row["contract_fingerprint"]); criteria_fp = str(revision_row["criteria_fingerprint"]); criteria_count = int(revision_row["criteria_count"])
                if not self._allowed_transition(before, after, normalized["operation"]): raise ProblemLineageError("problem state transition is invalid")
            if normalized["run_id"] and normalized["link_status"] == "EXACT" and normalized["link_role"] == "PRIMARY" and normalized["relation_type"] in {"LINK", "ENGINEERING_ATTEMPT_BOUND"}:
                prior = connection.execute("SELECT problem_id,problem_revision FROM problem_events WHERE run_id=? AND link_status='EXACT' AND link_role='PRIMARY' AND relation_type IN ('LINK','ENGINEERING_ATTEMPT_BOUND')", (normalized["run_id"],)).fetchone()
                if prior is not None:
                    if str(prior["problem_id"] or "") != normalized["problem_id"] or int(prior["problem_revision"] or 0) != event_revision: raise ProblemLineageError("a run already has a different primary problem revision")
                    raise ProblemLineageError("a run already has a primary problem binding")
            eligible = self._record_eligible(connection, normalized, authority_context, revision_row, clock)
            previous = connection.execute("SELECT event_hash FROM problem_events WHERE problem_id=? ORDER BY seq DESC LIMIT 1", (normalized["problem_id"],)).fetchone() if normalized["problem_id"] else None
            prev_hash = str(previous["event_hash"] or "") if previous is not None else ""
            hash_material = problem_event_hash_material({**normalized, "event_schema_version": 2, "problem_revision": event_revision or None, "eligible_for_policy": eligible, "transition_authority": authority_context, "criteria_count": criteria_count, "criteria_fingerprint": criteria_fp, "contract_fingerprint": contract_fp, "recorded_at": recorded_at, "clock_authority": clock}, state_before=before, state_after=after, prev_hash=prev_hash)
            event_hash = _sha(_json(hash_material))
            connection.execute("""INSERT INTO problem_events(event_id,event_schema_version,problem_id,problem_revision,task_id,turn_id,trace_id,run_id,wave_id,capsule_id,conversation_epoch,relation_type,link_status,link_role,feedback_intent,causal_mechanism,economic_class,provenance,evidence_level,eligible_for_policy,transition_authority,state_before,state_after,reason_code,criteria_count,criteria_fingerprint,contract_fingerprint,request_hash,recorded_at,occurred_at,occurred_at_source,clock_authority,event_time,prev_hash,event_hash) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (normalized["event_id"], 2, normalized["problem_id"] or None, event_revision or None, normalized["task_id"], normalized["turn_id"], normalized["trace_id"], normalized["run_id"], normalized["wave_id"], normalized["capsule_id"], normalized["conversation_epoch"], normalized["relation_type"], normalized["link_status"], normalized["link_role"], normalized["feedback_intent"], normalized["causal_mechanism"], normalized["economic_class"], normalized["provenance"], normalized["evidence_level"], int(eligible), authority_context, before, after, normalized["reason_code"], criteria_count, criteria_fp, contract_fp, request_hash, recorded_at, normalized["occurred_at"], normalized["occurred_at_source"], clock, "", prev_hash, event_hash))
            stored = connection.execute("SELECT * FROM problem_events WHERE event_id=?", (normalized["event_id"],)).fetchone(); assert stored is not None
            stored_event = _event(stored)
            if normalized["problem_id"]:
                if created_revision:
                    connection.execute("UPDATE problem_threads SET current_revision=?,resolution_state=?,task_class=?,engineering_floor=?,updated_at=?,closed_at=?,latest_problem_event_seq=?,latest_problem_event_hash=? WHERE problem_id=?", (event_revision, after, normalized["task_class"], normalized["engineering_floor"], recorded_at, None, stored_event["seq"], event_hash, normalized["problem_id"]))
                elif normalized["operation"] not in {"link", "observe_feedback"}:
                    connection.execute("UPDATE problem_threads SET resolution_state=?,updated_at=?,closed_at=?,latest_problem_event_seq=?,latest_problem_event_hash=? WHERE problem_id=?", (after, recorded_at, recorded_at if after in _CLOSED_STATES else None, stored_event["seq"], event_hash, normalized["problem_id"]))
                else:
                    connection.execute("UPDATE problem_threads SET updated_at=?,latest_problem_event_seq=?,latest_problem_event_hash=? WHERE problem_id=?", (recorded_at, stored_event["seq"], event_hash, normalized["problem_id"]))
                if normalized["operation"] in {"open", "revise"}: connection.execute("UPDATE problem_revisions SET created_event_seq=? WHERE problem_id=? AND revision=?", (stored_event["seq"], normalized["problem_id"], event_revision))
            result = self.problem_get(normalized["problem_id"], connection=connection) if normalized["problem_id"] else None
        return {"recorded": True, "idempotent": False, "event": stored_event, "thread": result}

    def problem_get(self, problem_id: str, *, connection: sqlite3.Connection | None = None, limit: int = 200) -> dict[str, Any] | None:
        problem_id = _opaque(problem_id, "problem_id", required=True)
        if connection is None:
            with self._lock, self._connect() as active:
                self._require_problem_schema(active)
                return self.problem_get(problem_id, connection=active, limit=limit)
        thread = connection.execute("SELECT * FROM problem_threads WHERE problem_id=?", (problem_id,)).fetchone()
        if thread is None: return None
        current = self._revision_row(connection, problem_id, int(thread["current_revision"]))
        current_projection = _revision(current) if current is not None else None
        events = connection.execute("SELECT * FROM problem_events WHERE problem_id=? ORDER BY seq LIMIT ?", (problem_id, max(1, min(int(limit), 500)))).fetchall()
        thread_projection = {"problem_id": str(thread["problem_id"]), "current_revision": int(thread["current_revision"]), "resolution_state": str(thread["resolution_state"]), "task_class": str(thread["task_class"]), "engineering_floor": str(thread["engineering_floor"]), "created_at": str(thread["created_at"]), "updated_at": str(thread["updated_at"]), "closed_at": str(thread["closed_at"] or "") or None, "latest_problem_event_seq": int(thread["latest_problem_event_seq"]), "latest_problem_event_hash": str(thread["latest_problem_event_hash"]), "current_revision_contract": current_projection}
        return {"thread": thread_projection, "current_revision": current_projection, "legacy_or_missing_contract": current_projection is None or not current_projection["capsule_valid"], "events": [_event(row) for row in events], "events_truncated": len(events) >= max(1, min(int(limit), 500))}

    def problem_get_exact_revision(self, problem_id: str, revision: int, *, expected_contract_fingerprint: str = "") -> dict[str, Any]:
        problem_id = _opaque(problem_id, "problem_id", required=True); revision = _integer(revision, "problem_revision", required=True); expected = _text(expected_contract_fingerprint, "expected_contract_fingerprint", limit=64).lower()
        with self._lock, self._connect() as connection:
            self._require_problem_schema(connection); row = self._revision_row(connection, problem_id, revision)
            if row is None: raise ProblemLineageError("BLOCKED_MISSING_PROBLEM_CONTEXT")
            result = _revision(row)
        if not result["capsule_valid"] or (expected and expected != result["contract_fingerprint"]): raise ProblemLineageError("BLOCKED_MISSING_PROBLEM_CONTEXT" if not result["capsule_valid"] else "problem revision contract fingerprint mismatch")
        return result

    def problem_find_exact_host_identity(self, *, turn_id: str, trace_id: str) -> dict[str, Any]:
        turn_id = _opaque(turn_id, "turn_id", required=True); trace_id = _opaque(trace_id, "trace_id", required=True)
        with self._lock, self._connect() as connection:
            if int(connection.execute("PRAGMA user_version").fetchone()[0]) != PROBLEM_SCHEMA_VERSION: return {"status": "schema_inactive", "problem_id": None, "problem_revision": None}
            rows = connection.execute("SELECT DISTINCT problem_id,problem_revision FROM problem_events WHERE turn_id=? AND trace_id=? AND link_status='EXACT' AND event_schema_version=2 AND problem_id IS NOT NULL AND problem_revision IS NOT NULL ORDER BY problem_id,problem_revision", (turn_id, trace_id)).fetchall()
        if len(rows) == 1: return {"status": "exact", "problem_id": str(rows[0]["problem_id"]), "problem_revision": int(rows[0]["problem_revision"])}
        if len(rows) > 1: return {"status": "ambiguous", "problem_id": None, "problem_revision": None, "candidate_count": len(rows)}
        return {"status": "unlinked", "problem_id": None, "problem_revision": None}

    def problem_handoff_for_run(self, run_id: str) -> dict[str, Any] | None:
        run_id = _opaque(run_id, "run_id", required=True)
        with self._lock, self._connect() as connection:
            if int(connection.execute("PRAGMA user_version").fetchone()[0]) != PROBLEM_SCHEMA_VERSION: return None
            rows = connection.execute("SELECT DISTINCT problem_id,problem_revision FROM problem_events WHERE run_id=? AND link_status='EXACT' AND link_role='PRIMARY' AND relation_type IN ('LINK','ENGINEERING_ATTEMPT_BOUND') AND event_schema_version=2 AND problem_id IS NOT NULL AND problem_revision IS NOT NULL ORDER BY problem_id,problem_revision", (run_id,)).fetchall()
            if len(rows) != 1: return None
            problem_id, revision = str(rows[0]["problem_id"]), int(rows[0]["problem_revision"]); revision_row = self._revision_row(connection, problem_id, revision); thread = connection.execute("SELECT * FROM problem_threads WHERE problem_id=?", (problem_id,)).fetchone()
            if revision_row is None or thread is None: return {"active_problem_id": problem_id, "problem_revision": revision, "context_status": "BLOCKED_MISSING_PROBLEM_CONTEXT", "policy_eligible": False}
            context = _revision(revision_row); events = connection.execute("SELECT * FROM problem_events WHERE problem_id=? AND problem_revision=? ORDER BY seq", (problem_id, revision)).fetchall()
        feedback = next((row for row in reversed(events) if str(row["relation_type"] or "") == "USER_FEEDBACK"), None)
        return {"active_problem_id": problem_id, "problem_revision": revision, "contract_fingerprint": context["contract_fingerprint"], "problem_state": str(thread["resolution_state"]) if int(thread["current_revision"]) == revision else "HISTORICAL_REVISION", "context_status": "VALID" if context["capsule_valid"] else "BLOCKED_MISSING_PROBLEM_CONTEXT", "policy_eligible": bool(context["capsule_valid"]), "latest_feedback_relation": str(feedback["feedback_intent"] if feedback is not None else "UNKNOWN"), "engineering_floor": context["engineering_floor"]}

    @staticmethod
    def _problem_coverage_manifest(
        connection: sqlite3.Connection,
        *,
        run_id: str,
        wave_id: str,
        criteria: set[str],
        manifest: Any,
    ) -> dict[str, list[str]]:
        if not isinstance(manifest, dict) or set(manifest) != criteria:
            raise ProblemLineageError("coverage manifest must map every and only current revision criterion IDs")
        normalized: dict[str, list[str]] = {}
        for criterion in sorted(criteria):
            proof_ids = manifest[criterion]
            if not isinstance(proof_ids, list) or not proof_ids or len(proof_ids) > 100:
                raise ProblemLineageError("required_criterion_proof_missing")
            normalized[criterion] = [_opaque(value, "proof_id", required=True) for value in proof_ids]
            if len(set(normalized[criterion])) != len(normalized[criterion]):
                raise ProblemLineageError("criterion coverage proof IDs must not repeat")
            for proof_id in normalized[criterion]:
                proof = connection.execute(
                    "SELECT run_id,wave_id,status FROM proofs WHERE proof_id=?",
                    (proof_id,),
                ).fetchone()
                if (
                    proof is None
                    or str(proof["run_id"]) != run_id
                    or str(proof["wave_id"]) != wave_id
                    or str(proof["status"]).lower() != "passed"
                ):
                    raise ProblemLineageError("criterion_proof_not_passed_exact_wave")
        return normalized

    @staticmethod
    def _problem_non_code_dispositions(criteria: set[str], dispositions: Any) -> dict[str, str]:
        if not isinstance(dispositions, dict) or set(dispositions) != criteria:
            raise ProblemLineageError("non-code dispositions must map every and only current revision criterion IDs")
        normalized: dict[str, str] = {}
        for criterion in sorted(criteria):
            if dispositions[criterion] != "SATISFIED_NON_CODE":
                raise ProblemLineageError("non-code criterion disposition must be SATISFIED_NON_CODE")
            normalized[criterion] = "SATISFIED_NON_CODE"
        return normalized

    @staticmethod
    def _problem_accepted_files_identity(accepted_files: Any, *, run_id: str, wave_id: str) -> tuple[dict[str, Any], str]:
        if not isinstance(accepted_files, dict):
            raise ProblemLineageError("accepted source receipt contract is required")
        files = accepted_files.get("files")
        count = accepted_files.get("count")
        total_bytes = accepted_files.get("total_bytes")
        if (
            accepted_files.get("complete") is not True
            or str(accepted_files.get("run_id") or "") != run_id
            or str(accepted_files.get("wave_id") or "") != wave_id
            or not isinstance(files, list)
            or isinstance(count, bool)
            or not isinstance(count, int)
            or count != len(files)
            or isinstance(total_bytes, bool)
            or not isinstance(total_bytes, int)
            or total_bytes < 0
        ):
            raise ProblemLineageError("accepted source receipt contract is invalid")
        canonical = json.loads(_json(accepted_files))
        return canonical, _sha(_json(canonical))

    @staticmethod
    def _problem_current_controller_receipt(
        connection: sqlite3.Connection,
        *,
        run_id: str,
        authority: Any,
    ) -> dict[str, Any]:
        if not isinstance(authority, dict):
            raise ProblemLineageError("NOT_APPLICABLE requires current ChatWeb controller authority")
        client_id = str(authority.get("client_id") or "")
        lease_id = str(authority.get("lease_id") or "")
        runtime_instance_id = str(authority.get("runtime_instance_id") or "")
        fencing_token = authority.get("fencing_token")
        if not client_id or not lease_id or not runtime_instance_id or isinstance(fencing_token, bool) or not isinstance(fencing_token, int) or fencing_token < 1:
            raise ProblemLineageError("NOT_APPLICABLE controller authority receipt is invalid")
        client = connection.execute("SELECT * FROM hub_clients WHERE client_id=?", (client_id,)).fetchone()
        lease = connection.execute("SELECT * FROM controller_leases WHERE run_id=?", (run_id,)).fetchone()
        if (
            client is None
            or str(client["client_type"] or "") != "chatweb"
            or str(client["role"] or "") != "controller"
            or str(client["status"] or "") != "online"
            or str(client["runtime_instance_id"] or "") != runtime_instance_id
            or lease is None
            or str(lease["status"] or "") != "active"
            or float(lease["expires_at"] or 0) <= time.time()
            or str(lease["owner_client_id"] or "") != client_id
            or str(lease["lease_id"] or "") != lease_id
            or int(lease["fencing_token"] or 0) != fencing_token
        ):
            raise ProblemLineageError("NOT_APPLICABLE requires the exact current ChatWeb controller lease")
        return {
            "client_id": client_id,
            "client_type": "chatweb",
            "runtime_instance_id": runtime_instance_id,
            "lease_id": lease_id,
            "fencing_token": fencing_token,
        }

    def problem_prepare_eocl_outcome_claim(
        self,
        *,
        run_id: str,
        wave_id: str,
        git_head: str,
        worktree_fp: str,
        proof_fingerprint: str,
        accepted_files: dict[str, Any],
        durable_mutation: bool,
        coverage_manifest: Any = None,
        criterion_dispositions: Any = None,
        controller_authority: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        with self._lock, self._connect() as connection:
            if int(connection.execute("PRAGMA user_version").fetchone()[0]) != PROBLEM_SCHEMA_VERSION:
                return {"required": False, "reason": "schema_inactive"}
            wave = connection.execute(
                "SELECT metadata_json FROM waves WHERE wave_id=? AND run_id=?",
                (wave_id, run_id),
            ).fetchone()
            if wave is None:
                raise ProblemLineageError("problem outcome claim references an unknown exact run/wave")
            metadata = json.loads(wave["metadata_json"] or "{}")
            context = metadata.get("problem_resolution") if isinstance(metadata.get("problem_resolution"), dict) else {}
            if context.get("work_origin") != "problem" or context.get("resolution_claim") != "full_problem":
                return {"required": False, "reason": "not_exact_full_problem_claim"}
            problem_id = _opaque(context.get("problem_id"), "problem_id", required=True)
            revision_number = _integer(context.get("problem_revision"), "problem_revision", required=True)
            row = self._revision_row(connection, problem_id, revision_number)
            thread = connection.execute("SELECT current_revision FROM problem_threads WHERE problem_id=?", (problem_id,)).fetchone()
            if row is None or thread is None:
                raise ProblemLineageError("BLOCKED_MISSING_PROBLEM_CONTEXT")
            revision = _revision(row)
            if (
                not revision["capsule_valid"]
                or int(thread["current_revision"]) != revision_number
                or str(context.get("contract_fingerprint") or "") != revision["contract_fingerprint"]
                or str(context.get("engineering_floor") or "") != revision["engineering_floor"]
            ):
                raise ProblemLineageError("BLOCKED_MISSING_PROBLEM_CONTEXT")
            if not str(git_head or "") or not str(worktree_fp or ""):
                raise ProblemLineageError("problem outcome claim requires exact current Git HEAD and worktree fingerprint")
            canonical_files, accepted_files_sha256 = self._problem_accepted_files_identity(
                accepted_files,
                run_id=run_id,
                wave_id=wave_id,
            )
            criteria = {str(item["criterion_id"]) for item in revision["capsule"]["acceptance_criteria"]}
            floor = revision["engineering_floor"]
            if floor == "REQUIRED":
                if criterion_dispositions is not None:
                    raise ProblemLineageError("REQUIRED engineering floor accepts proof coverage only")
                evidence = {
                    "kind": "proof_coverage",
                    "coverage_manifest": self._problem_coverage_manifest(
                        connection,
                        run_id=run_id,
                        wave_id=wave_id,
                        criteria=criteria,
                        manifest=coverage_manifest,
                    ),
                }
                evidence["coverage_manifest_sha256"] = _sha(_json(evidence["coverage_manifest"]))
                if not str(proof_fingerprint or ""):
                    raise ProblemLineageError("REQUIRED engineering floor requires passed proof authority")
            elif floor == "NOT_APPLICABLE":
                if coverage_manifest is not None or "coverage_manifest" in context:
                    raise ProblemLineageError("NOT_APPLICABLE rejects the legacy empty proof-list coverage path")
                if durable_mutation or canonical_files["count"] != 0 or canonical_files["total_bytes"] != 0 or canonical_files["files"]:
                    raise ProblemLineageError("NOT_APPLICABLE requires zero mutation and zero source receipts")
                dispositions = self._problem_non_code_dispositions(criteria, criterion_dispositions)
                evidence = {
                    "kind": "non_code_dispositions",
                    "criterion_dispositions": dispositions,
                    "criterion_dispositions_sha256": _sha(_json(dispositions)),
                    "controller_authority": self._problem_current_controller_receipt(
                        connection,
                        run_id=run_id,
                        authority=controller_authority,
                    ),
                }
            else:
                raise ProblemLineageError("engineering_floor_unknown")
            claim = {
                "schema_version": 1,
                "resolution_claim": "full_problem",
                "run_id": run_id,
                "wave_id": wave_id,
                "problem_id": problem_id,
                "problem_revision": revision_number,
                "contract_fingerprint": revision["contract_fingerprint"],
                "criteria_fingerprint": revision["criteria_fingerprint"],
                "criteria_count": revision["criteria_count"],
                "engineering_floor": floor,
                "source": {
                    "git_head": str(git_head),
                    "worktree_fp": str(worktree_fp),
                    "proof_fingerprint": str(proof_fingerprint or ""),
                    "accepted_files_sha256": accepted_files_sha256,
                },
                "evidence": evidence,
            }
            encoded = _json(claim).encode("utf-8")
            if len(encoded) > PROBLEM_OUTCOME_CLAIM_MAX_BYTES:
                raise ProblemLineageError("problem outcome claim exceeds its bounded size")
            claim_sha256 = hashlib.sha256(encoded).hexdigest()
            existing = context.get("outcome_claim")
            existing_sha256 = str(context.get("outcome_claim_sha256") or "")
            if existing is not None:
                if _json(existing) != _json(claim) or existing_sha256 != claim_sha256:
                    raise ProblemLineageError("problem outcome claim is immutable within a wave")
                return {"required": True, "recorded": False, "idempotent": True, "claim": claim, "claim_sha256": claim_sha256}
            context["outcome_claim"] = claim
            context["outcome_claim_sha256"] = claim_sha256
            if floor == "REQUIRED":
                context["coverage_manifest"] = evidence["coverage_manifest"]
                context["coverage_manifest_sha256"] = evidence["coverage_manifest_sha256"]
            else:
                context["criterion_dispositions"] = evidence["criterion_dispositions"]
                context["criterion_dispositions_sha256"] = evidence["criterion_dispositions_sha256"]
            metadata["problem_resolution"] = context
            connection.execute("UPDATE waves SET metadata_json=? WHERE wave_id=? AND run_id=?", (_json(metadata), wave_id, run_id))
        return {"required": True, "recorded": True, "idempotent": False, "claim": claim, "claim_sha256": claim_sha256}

    def problem_record_coverage_manifest(self, *, run_id: str, wave_id: str, manifest: dict[str, Any]) -> dict[str, Any]:
        """Compatibility helper for REQUIRED floors; N/A must use typed dispositions."""
        with self._lock, self._connect() as connection:
            self._require_problem_schema(connection)
            wave = connection.execute("SELECT metadata_json FROM waves WHERE wave_id=? AND run_id=?", (wave_id, run_id)).fetchone()
            if wave is None:
                raise ProblemLineageError("problem coverage references an unknown exact run/wave")
            metadata = json.loads(wave["metadata_json"] or "{}")
            context = metadata.get("problem_resolution") if isinstance(metadata.get("problem_resolution"), dict) else {}
            if context.get("work_origin") != "problem" or context.get("resolution_claim") != "full_problem":
                raise ProblemLineageError("coverage manifest requires an exact full_problem wave")
            problem_id = _opaque(context.get("problem_id"), "problem_id", required=True)
            revision_number = _integer(context.get("problem_revision"), "problem_revision", required=True)
            row = self._revision_row(connection, problem_id, revision_number)
            if row is None or not _revision(row)["capsule_valid"]:
                raise ProblemLineageError("BLOCKED_MISSING_PROBLEM_CONTEXT")
            revision = _revision(row)
            if revision["engineering_floor"] != "REQUIRED":
                raise ProblemLineageError("coverage proof lists are valid only for REQUIRED engineering floors")
            criteria = {str(item["criterion_id"]) for item in revision["capsule"]["acceptance_criteria"]}
            normalized = self._problem_coverage_manifest(connection, run_id=run_id, wave_id=wave_id, criteria=criteria, manifest=manifest)
            digest = _sha(_json(normalized))
            if "coverage_manifest" in context:
                if _json(context["coverage_manifest"]) != _json(normalized):
                    raise ProblemLineageError("criterion coverage manifest is immutable within a wave")
                return {"recorded": False, "idempotent": True, "manifest_sha256": digest}
            context["coverage_manifest"], context["coverage_manifest_sha256"] = normalized, digest
            metadata["problem_resolution"] = context
            connection.execute("UPDATE waves SET metadata_json=? WHERE wave_id=? AND run_id=?", (_json(metadata), wave_id, run_id))
        return {"recorded": True, "idempotent": False, "manifest_sha256": digest}

    def _problem_validate_reconciliation(self, connection: sqlite3.Connection, reconciliation: dict[str, str]) -> dict[str, Any]:
        required = {"run_id", "wave_id", "checkpoint_id", "current_git_head", "current_worktree_fp", "claim_sha256", "terminal_event_time"}
        if not isinstance(reconciliation, dict) or set(reconciliation) != required:
            raise ProblemLineageError("reconciliation contract is invalid")
        run_id, wave_id, checkpoint_id = reconciliation["run_id"], reconciliation["wave_id"], reconciliation["checkpoint_id"]
        checkpoint = connection.execute(
            "SELECT * FROM checkpoints WHERE checkpoint_id=? AND run_id=? AND wave_id=? AND status='accepted'",
            (checkpoint_id, run_id, wave_id),
        ).fetchone()
        run = connection.execute("SELECT status FROM runs WHERE run_id=?", (run_id,)).fetchone()
        wave = connection.execute("SELECT status FROM waves WHERE run_id=? AND wave_id=?", (run_id, wave_id)).fetchone()
        if checkpoint is None or run is None or wave is None or str(run["status"] or "") != "accepted" or str(wave["status"] or "") != "accepted":
            raise ProblemLineageError("accepted terminal EOCL checkpoint is missing")
        terminal_event_time = ""
        for row in connection.execute(
            "SELECT state_after,event_time,payload_json FROM events WHERE run_id=? AND wave_id=? AND event_type='state_transition' ORDER BY seq",
            (run_id, wave_id),
        ).fetchall():
            try:
                payload = json.loads(row["payload_json"] or "{}")
            except (TypeError, json.JSONDecodeError):
                continue
            if str(row["state_after"] or "") == "CHECKPOINTED" and str(payload.get("checkpoint_id") or "") == checkpoint_id:
                terminal_event_time = str(row["event_time"] or "")
                break
        if not terminal_event_time or terminal_event_time != reconciliation["terminal_event_time"]:
            raise ProblemLineageError("accepted checkpoint lacks its exact terminal EOCL event")
        metadata = json.loads(checkpoint["metadata_json"] or "{}")
        claim = metadata.get("problem_outcome_claim")
        claim_sha256 = str(metadata.get("problem_outcome_claim_sha256") or "")
        if not isinstance(claim, dict) or claim_sha256 != _sha(_json(claim)) or claim_sha256 != reconciliation["claim_sha256"]:
            raise ProblemLineageError("frozen problem outcome claim is missing or changed")
        if (
            claim.get("schema_version") != 1
            or claim.get("resolution_claim") != "full_problem"
            or str(claim.get("run_id") or "") != run_id
            or str(claim.get("wave_id") or "") != wave_id
        ):
            raise ProblemLineageError("frozen problem outcome claim identity is invalid")
        source = claim.get("source") if isinstance(claim.get("source"), dict) else {}
        accepted_files = metadata.get("accepted_files")
        if (
            str(checkpoint["git_head"] or "") != str(source.get("git_head") or "")
            or str(checkpoint["proof_fingerprint"] or "") != str(source.get("proof_fingerprint") or "")
            or str(metadata.get("worktree_fp") or "") != str(source.get("worktree_fp") or "")
            or str(reconciliation["current_git_head"]) != str(source.get("git_head") or "")
            or str(reconciliation["current_worktree_fp"]) != str(source.get("worktree_fp") or "")
            or not isinstance(accepted_files, dict)
            or _sha(_json(accepted_files)) != str(source.get("accepted_files_sha256") or "")
        ):
            raise ProblemLineageError("accepted source evidence or current source identity changed")
        problem_id = _opaque(claim.get("problem_id"), "problem_id", required=True)
        revision_number = _integer(claim.get("problem_revision"), "problem_revision", required=True)
        revision_row = self._revision_row(connection, problem_id, revision_number)
        thread = connection.execute("SELECT current_revision FROM problem_threads WHERE problem_id=?", (problem_id,)).fetchone()
        if revision_row is None or thread is None:
            raise ProblemLineageError("BLOCKED_MISSING_PROBLEM_CONTEXT")
        revision = _revision(revision_row)
        if (
            not revision["capsule_valid"]
            or int(thread["current_revision"]) != revision_number
            or claim.get("contract_fingerprint") != revision["contract_fingerprint"]
            or claim.get("criteria_fingerprint") != revision["criteria_fingerprint"]
            or claim.get("criteria_count") != revision["criteria_count"]
            or claim.get("engineering_floor") != revision["engineering_floor"]
        ):
            raise ProblemLineageError("current problem revision changed after checkpoint")
        criteria = {str(item["criterion_id"]) for item in revision["capsule"]["acceptance_criteria"]}
        evidence = claim.get("evidence") if isinstance(claim.get("evidence"), dict) else {}
        if revision["engineering_floor"] == "REQUIRED":
            manifest = self._problem_coverage_manifest(connection, run_id=run_id, wave_id=wave_id, criteria=criteria, manifest=evidence.get("coverage_manifest"))
            if evidence.get("kind") != "proof_coverage" or evidence.get("coverage_manifest_sha256") != _sha(_json(manifest)):
                raise ProblemLineageError("frozen proof coverage changed")
        elif revision["engineering_floor"] == "NOT_APPLICABLE":
            canonical_files, _ = self._problem_accepted_files_identity(accepted_files, run_id=run_id, wave_id=wave_id)
            dispositions = self._problem_non_code_dispositions(criteria, evidence.get("criterion_dispositions"))
            if (
                evidence.get("kind") != "non_code_dispositions"
                or evidence.get("criterion_dispositions_sha256") != _sha(_json(dispositions))
                or canonical_files["count"] != 0
                or canonical_files["total_bytes"] != 0
                or canonical_files["files"]
                or not isinstance(evidence.get("controller_authority"), dict)
            ):
                raise ProblemLineageError("frozen non-code disposition authority changed")
        else:
            raise ProblemLineageError("engineering_floor_unknown")
        return claim

    def problem_reconcile_provisional_from_checkpoint(
        self,
        *,
        run_id: str,
        wave_id: str,
        checkpoint_id: str,
        current_git_head: str,
        current_worktree_fp: str,
        now: str,
    ) -> dict[str, Any]:
        with self._lock, self._connect() as connection:
            if int(connection.execute("PRAGMA user_version").fetchone()[0]) != PROBLEM_SCHEMA_VERSION:
                return {"recorded": False, "reason": "schema_inactive"}
            checkpoint = connection.execute(
                "SELECT metadata_json FROM checkpoints WHERE checkpoint_id=? AND run_id=? AND wave_id=?",
                (checkpoint_id, run_id, wave_id),
            ).fetchone()
            if checkpoint is None:
                return {"recorded": False, "reason": "accepted_checkpoint_missing"}
            metadata = json.loads(checkpoint["metadata_json"] or "{}")
            claim = metadata.get("problem_outcome_claim")
            claim_sha256 = str(metadata.get("problem_outcome_claim_sha256") or "")
            if not isinstance(claim, dict) or claim_sha256 != _sha(_json(claim)):
                return {"recorded": False, "reason": "frozen_problem_outcome_claim_missing"}
            problem_id = str(claim.get("problem_id") or "")
            revision_number = int(claim.get("problem_revision") or 0)
            terminal_event_time = ""
            for row in connection.execute(
                "SELECT state_after,event_time,payload_json FROM events WHERE run_id=? AND wave_id=? AND event_type='state_transition' ORDER BY seq",
                (run_id, wave_id),
            ).fetchall():
                try:
                    payload = json.loads(row["payload_json"] or "{}")
                except (TypeError, json.JSONDecodeError):
                    continue
                if str(row["state_after"] or "") == "CHECKPOINTED" and str(payload.get("checkpoint_id") or "") == checkpoint_id:
                    terminal_event_time = str(row["event_time"] or "")
                    break
            if not terminal_event_time:
                return {"recorded": False, "reason": "accepted_terminal_event_missing"}
            event_id = "prl-provisional-v11-" + _sha("\x1f".join((run_id, wave_id, problem_id, str(revision_number), checkpoint_id)))
            reconciliation = {
                "run_id": run_id,
                "wave_id": wave_id,
                "checkpoint_id": checkpoint_id,
                "current_git_head": current_git_head,
                "current_worktree_fp": current_worktree_fp,
                "claim_sha256": claim_sha256,
                "terminal_event_time": terminal_event_time,
            }
            existing = connection.execute("SELECT * FROM problem_events WHERE event_id=?", (event_id,)).fetchone()
            if existing is not None:
                self._problem_validate_reconciliation(connection, reconciliation)
                projection = _event(existing)
                if (
                    projection["problem_id"] != problem_id
                    or projection["problem_revision"] != revision_number
                    or projection["run_id"] != run_id
                    or projection["wave_id"] != wave_id
                    or projection["relation_type"] != "PROVISIONAL_RESOLUTION"
                    or projection["provenance"] != "DETERMINISTIC_EVIDENCE"
                    or projection["evidence_level"] != "OBSERVED"
                    or projection["transition_authority"] not in {"RUNTIME_EOCL", "RUNTIME_RECONCILIATION"}
                ):
                    raise ProblemLineageError("historical provisional event conflicts with the exact checkpoint claim")
                return {"recorded": False, "idempotent": True, "event": projection, "thread": self.problem_get(problem_id, connection=connection)}
        return self.problem_record_event(
            {
                "operation": "provisional_resolve",
                "event_id": event_id,
                "problem_id": problem_id,
                "problem_revision": revision_number,
                "run_id": run_id,
                "wave_id": wave_id,
                "relation_type": "PROVISIONAL_RESOLUTION",
                "provenance": "DETERMINISTIC_EVIDENCE",
                "evidence_level": "OBSERVED",
                "occurred_at": terminal_event_time,
                "occurred_at_source": "RUNTIME",
            },
            now=now,
            authority_context="RUNTIME_RECONCILIATION",
            reconciliation=reconciliation,
        )

    def problem_record_provisional_from_eocl(self, *, run_id: str, wave_id: str, checkpoint_id: str, now: str) -> dict[str, Any]:
        """Compatibility wrapper; reconciliation still requires the exact frozen checkpoint."""
        with self._lock, self._connect() as connection:
            checkpoint = connection.execute(
                "SELECT git_head,metadata_json FROM checkpoints WHERE checkpoint_id=? AND run_id=? AND wave_id=?",
                (checkpoint_id, run_id, wave_id),
            ).fetchone()
        if checkpoint is None:
            return {"recorded": False, "reason": "accepted_checkpoint_missing"}
        metadata = json.loads(checkpoint["metadata_json"] or "{}")
        return self.problem_reconcile_provisional_from_checkpoint(
            run_id=run_id,
            wave_id=wave_id,
            checkpoint_id=checkpoint_id,
            current_git_head=str(checkpoint["git_head"] or ""),
            current_worktree_fp=str(metadata.get("worktree_fp") or ""),
            now=now,
        )

    def problem_verify_chain(self, problem_id: str) -> dict[str, Any]:
        result = self.problem_get(problem_id, limit=500)
        if result is None: raise ProblemLineageError("problem was not found")
        previous = ""
        for event in result["events"]:
            if event["prev_hash"] != previous: return {"ok": False, "reason": "prev_hash_mismatch", "seq": event["seq"]}
            material = problem_event_hash_material(event, state_before=event["state_before"], state_after=event["state_after"], prev_hash=previous)
            if _sha(_json(material)) != event["event_hash"]: return {"ok": False, "reason": "event_hash_mismatch", "seq": event["seq"]}
            previous = event["event_hash"]
        return {"ok": True, "event_count": len(result["events"]), "last_event_hash": previous}
