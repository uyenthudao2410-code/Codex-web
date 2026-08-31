from __future__ import annotations

"""Bounded, content-free shadow frame and resolution-envelope contracts.

The contracts in this module are deliberately additive to PRL/EOCL.  They do
not infer a root cause, grant authority, or turn a technical checkpoint into a
user outcome.  They only make the model that was used for a bounded claim
explicit, hashable, and safe to persist in run/wave metadata.
"""

import base64
import binascii
import hashlib
import json
import re
import unicodedata
from typing import Any
from urllib.parse import unquote


FRAME_SCHEMA_VERSION = 1
ENVELOPE_SCHEMA_VERSION = 1
MAX_FRAME_BYTES = 24_576
MAX_ENVELOPE_BYTES = 32_768
_ID_RE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_SECRET_RE = re.compile(
    r"(?:\b(?:api[_-]?key|secret|token|password|passwd|authorization)\b\s*[:=]|"
    r"\bBearer\s+[A-Za-z0-9._~+/-]{12,}|\b(?:sk|gh[pousr])_[A-Za-z0-9_-]{12,}|"
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)",
    re.I,
)
_EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
_PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d[\d .()-]{7,}\d)(?!\d)")
_PERCENT_RE = re.compile(r"%(?:[0-9A-Fa-f]{2})")
_ESCAPED_ASCII_RE = re.compile(r"\\(?:u[0-9A-Fa-f]{4}|x[0-9A-Fa-f]{2})")
_BASE64_TOKEN_RE = re.compile(r"(?<![A-Za-z0-9_-])[A-Za-z0-9_-]{16,}={0,2}(?![A-Za-z0-9_-])")
_HEX_TOKEN_RE = re.compile(r"(?<![0-9A-Fa-f])[0-9A-Fa-f]{24,}(?![0-9A-Fa-f])")
_PRIVACY_SCAN_MAX_DEPTH = 2
_PRIVACY_SCAN_MAX_VARIANTS = 32
_PRIVACY_SCAN_MAX_DECODED_BYTES = 32_768


class ResolutionContractError(ValueError):
    """A supplied shadow frame or envelope is not safe/canonical."""


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def contract_sha256(value: Any) -> str:
    return hashlib.sha256(_json(value).encode("utf-8")).hexdigest()


def _decoded_printable(value: bytes) -> str | None:
    if not value or len(value) > _PRIVACY_SCAN_MAX_DECODED_BYTES:
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


def _privacy_scan_variants(value: str) -> tuple[str, ...]:
    """Return bounded, syntax-triggered variants for durable privacy checks."""
    pending = [unicodedata.normalize("NFKC", value)]
    variants: list[str] = []
    seen: set[str] = set()
    decoded_bytes = 0
    for depth in range(_PRIVACY_SCAN_MAX_DEPTH + 1):
        next_pending: list[str] = []
        for current in pending:
            if current in seen:
                continue
            seen.add(current)
            variants.append(current)
            folded = "".join(char for char in current if unicodedata.category(char) != "Cf")
            if folded not in seen:
                variants.append(folded)
                seen.add(folded)
            if len(variants) > _PRIVACY_SCAN_MAX_VARIANTS:
                raise ResolutionContractError("privacy scan exceeded its bounded variant budget")
            if depth == _PRIVACY_SCAN_MAX_DEPTH:
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
                if decoded_bytes > _PRIVACY_SCAN_MAX_DECODED_BYTES:
                    raise ResolutionContractError("privacy scan exceeded its bounded decoded-byte budget")
                candidate = _decoded_printable(decoded)
                if candidate is not None:
                    next_pending.append(candidate)
            for token in _HEX_TOKEN_RE.findall(current):
                try:
                    decoded = bytes.fromhex(token)
                except ValueError:
                    continue
                decoded_bytes += len(decoded)
                if decoded_bytes > _PRIVACY_SCAN_MAX_DECODED_BYTES:
                    raise ResolutionContractError("privacy scan exceeded its bounded decoded-byte budget")
                candidate = _decoded_printable(decoded)
                if candidate is not None:
                    next_pending.append(candidate)
        pending = next_pending
    return tuple(variants)


def _text(value: Any, name: str, *, required: bool = False, limit: int = 800) -> str:
    if value is None:
        result = ""
    elif not isinstance(value, str):
        raise ResolutionContractError(f"{name} must be a string")
    else:
        result = unicodedata.normalize("NFKC", value).strip()
    if len(result) > limit:
        raise ResolutionContractError(f"{name} exceeds its bounded length")
    if required and not result:
        raise ResolutionContractError(f"{name} is required")
    for variant in _privacy_scan_variants(result):
        if _SECRET_RE.search(variant) or _EMAIL_RE.search(variant) or _PHONE_RE.search(variant):
            raise ResolutionContractError(f"{name} contains credential-like or personal data")
    return result


def _id(value: Any, name: str, *, required: bool = True) -> str:
    result = _text(value, name, required=required, limit=128)
    if result and not _ID_RE.fullmatch(result):
        raise ResolutionContractError(f"{name} must be a bounded opaque identifier")
    return result


def _bounded_list(value: Any, name: str, *, required: bool = False, limit: int = 32, item_limit: int = 800) -> list[str]:
    if value is None:
        value = []
    if not isinstance(value, list) or len(value) > limit:
        raise ResolutionContractError(f"{name} must be a bounded list")
    items = [_text(item, f"{name} item", required=True, limit=item_limit) for item in value]
    if required and not items:
        raise ResolutionContractError(f"{name} must not be empty")
    if len(set(items)) != len(items):
        raise ResolutionContractError(f"{name} must contain unique values")
    return items


def _object(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ResolutionContractError(f"{name} must be an object")
    return value


def _bounded_object_size(value: Any, name: str, limit: int) -> None:
    if len(_json(value).encode("utf-8")) > limit:
        raise ResolutionContractError(f"{name} exceeds its bounded durable size")


def normalize_problem_frame(value: Any) -> dict[str, Any]:
    """Canonicalize a shadow frame packet without granting any authority."""
    raw = _object(value, "problem_frame")
    allowed = {
        "schema_version", "frame_id", "frame_revision", "observation", "a_star",
        "governing_invariants", "ownership", "hypotheses", "counterevidence",
        "decision_delta", "closure_falsifier", "authority_side_effects",
    }
    if set(raw) - allowed:
        raise ResolutionContractError("problem_frame contains disallowed fields")
    if raw.get("schema_version", FRAME_SCHEMA_VERSION) != FRAME_SCHEMA_VERSION:
        raise ResolutionContractError("problem_frame schema_version is unsupported")
    frame_id = _id(raw.get("frame_id"), "frame_id")
    revision = raw.get("frame_revision")
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 1 or revision > 1_000_000:
        raise ResolutionContractError("frame_revision must be a bounded positive integer")
    a_star = _object(raw.get("a_star"), "a_star")
    if set(a_star) - {"domains", "phenomena", "ownership_boundaries", "relations"}:
        raise ResolutionContractError("a_star contains disallowed fields")
    normalized_a_star = {
        "domains": _bounded_list(a_star.get("domains"), "a_star.domains", required=True),
        "phenomena": _bounded_list(a_star.get("phenomena"), "a_star.phenomena", required=True),
        "ownership_boundaries": _bounded_list(a_star.get("ownership_boundaries"), "a_star.ownership_boundaries"),
        "relations": _bounded_list(a_star.get("relations"), "a_star.relations"),
    }
    invariants: list[dict[str, str]] = []
    for item in _object_list(raw.get("governing_invariants"), "governing_invariants", max_items=40):
        if set(item) != {"invariant_id", "summary"}:
            raise ResolutionContractError("each governing invariant must contain invariant_id and summary")
        invariants.append({"invariant_id": _id(item.get("invariant_id"), "invariant_id"), "summary": _text(item.get("summary"), "invariant summary", required=True)})
    ownership: list[dict[str, Any]] = []
    for item in _object_list(raw.get("ownership"), "ownership", max_items=32):
        if set(item) != {"authoritative_owner", "allowed_writers", "derived_consumers"}:
            raise ResolutionContractError("each ownership item has an invalid shape")
        ownership.append({
            "authoritative_owner": _text(item.get("authoritative_owner"), "authoritative_owner", required=True),
            "allowed_writers": _bounded_list(item.get("allowed_writers"), "allowed_writers"),
            "derived_consumers": _bounded_list(item.get("derived_consumers"), "derived_consumers"),
        })
    hypotheses: list[dict[str, str]] = []
    for item in _object_list(raw.get("hypotheses"), "hypotheses", max_items=40):
        if set(item) != {"hypothesis_id", "mechanism", "prediction", "falsifier"}:
            raise ResolutionContractError("each hypothesis has an invalid shape")
        hypotheses.append({
            "hypothesis_id": _id(item.get("hypothesis_id"), "hypothesis_id"),
            "mechanism": _text(item.get("mechanism"), "hypothesis mechanism", required=True),
            "prediction": _text(item.get("prediction"), "hypothesis prediction", required=True),
            "falsifier": _text(item.get("falsifier"), "hypothesis falsifier", required=True),
        })
    counterevidence: list[dict[str, str]] = []
    for item in _object_list(raw.get("counterevidence"), "counterevidence", max_items=40):
        if set(item) != {"observation_id", "summary", "impact"}:
            raise ResolutionContractError("each counterevidence item has an invalid shape")
        counterevidence.append({
            "observation_id": _id(item.get("observation_id"), "observation_id"),
            "summary": _text(item.get("summary"), "counterevidence summary", required=True),
            "impact": _text(item.get("impact"), "counterevidence impact", required=True),
        })
    decision_delta = _object(raw.get("decision_delta"), "decision_delta")
    if set(decision_delta) != {"tested_observation", "changed_decision", "next_action", "rationale"}:
        raise ResolutionContractError("decision_delta has an invalid shape")
    if not isinstance(decision_delta.get("changed_decision"), bool):
        raise ResolutionContractError("decision_delta.changed_decision must be boolean")
    normalized = {
        "schema_version": FRAME_SCHEMA_VERSION,
        "frame_id": frame_id,
        "frame_revision": revision,
        "observation": _text(raw.get("observation"), "observation", required=True, limit=2_000),
        "a_star": normalized_a_star,
        "governing_invariants": invariants,
        "ownership": ownership,
        "hypotheses": hypotheses,
        "counterevidence": counterevidence,
        "decision_delta": {
            "tested_observation": _text(decision_delta.get("tested_observation"), "decision_delta.tested_observation", required=True),
            "changed_decision": bool(decision_delta["changed_decision"]),
            "next_action": _text(decision_delta.get("next_action"), "decision_delta.next_action", required=True),
            "rationale": _text(decision_delta.get("rationale"), "decision_delta.rationale", required=True),
        },
        "closure_falsifier": _text(raw.get("closure_falsifier"), "closure_falsifier", required=True),
        "authority_side_effects": False,
    }
    if raw.get("authority_side_effects") not in {None, False}:
        raise ResolutionContractError("problem_frame is shadow-only and cannot request authority side effects")
    _bounded_object_size(normalized, "problem_frame", MAX_FRAME_BYTES)
    return normalized


def counterevidence_frame_update_advisory(frame: dict[str, Any]) -> dict[str, Any]:
    """Project a content-free frame-review advisory without granting authority.

    The frame contract does not infer whether an observation is materially
    contradictory.  When the caller records counterevidence, this projection
    therefore recommends an explicit materiality review and a frame update or
    explanation before a same-family mutation retry.  It never blocks a route,
    grants mutation authority, or claims that the frame was actually updated.
    """

    counterevidence_count = len(frame.get("counterevidence") or [])
    decision_changed = bool((frame.get("decision_delta") or {}).get("changed_decision"))
    review_recommended = counterevidence_count > 0
    return {
        "schema_version": 1,
        "status": "COUNTEREVIDENCE_REQUIRES_FRAME_REVIEW" if review_recommended else "NO_COUNTEREVIDENCE_RECORDED",
        "counterevidence_count": counterevidence_count,
        "decision_changed_attested": decision_changed,
        "frame_update_or_explanation_recommended": review_recommended,
        "same_family_retry_materiality_review_recommended": review_recommended,
        "materiality_inferred": False,
        "authority": "ADVISORY_ONLY",
        "automatic_mutation_gate": False,
    }


def normalize_resolution_envelope(value: Any) -> dict[str, Any]:
    """Canonicalize a bounded closure envelope for an exact accepted claim."""
    raw = _object(value, "resolution_envelope")
    allowed = {"schema_version", "direct_outcomes", "relevant_invariants", "truth_domains", "adjacent_risks", "excluded_scope", "required_evidence", "closure_falsification_probe"}
    if set(raw) - allowed:
        raise ResolutionContractError("resolution_envelope contains disallowed fields")
    if raw.get("schema_version", ENVELOPE_SCHEMA_VERSION) != ENVELOPE_SCHEMA_VERSION:
        raise ResolutionContractError("resolution_envelope schema_version is unsupported")
    outcomes: list[dict[str, str]] = []
    for item in _object_list(raw.get("direct_outcomes"), "direct_outcomes", max_items=40, required=True):
        if set(item) != {"outcome_id", "summary"}:
            raise ResolutionContractError("each direct outcome must contain outcome_id and summary")
        outcomes.append({"outcome_id": _id(item.get("outcome_id"), "outcome_id"), "summary": _text(item.get("summary"), "outcome summary", required=True)})
    invariants = _bounded_list(raw.get("relevant_invariants"), "relevant_invariants", required=True)
    domains = _bounded_list(raw.get("truth_domains"), "truth_domains", required=True)
    risks: list[dict[str, str]] = []
    for item in _object_list(raw.get("adjacent_risks"), "adjacent_risks", max_items=40):
        if set(item) != {"risk_id", "summary", "basis"}:
            raise ResolutionContractError("each adjacent risk has an invalid shape")
        risks.append({"risk_id": _id(item.get("risk_id"), "risk_id"), "summary": _text(item.get("summary"), "risk summary", required=True), "basis": _text(item.get("basis"), "risk basis", required=True)})
    evidence: list[dict[str, str]] = []
    for item in _object_list(raw.get("required_evidence"), "required_evidence", max_items=64, required=True):
        if set(item) != {"evidence_id", "kind", "provenance", "status"}:
            raise ResolutionContractError("each required evidence item has an invalid shape")
        status = _text(item.get("status"), "evidence status", required=True, limit=64).lower()
        if status not in {"observed", "derived", "not_applicable"}:
            raise ResolutionContractError("evidence status must be observed, derived, or not_applicable")
        evidence.append({"evidence_id": _id(item.get("evidence_id"), "evidence_id"), "kind": _text(item.get("kind"), "evidence kind", required=True, limit=128), "provenance": _text(item.get("provenance"), "evidence provenance", required=True, limit=128), "status": status})
    probe = _object(raw.get("closure_falsification_probe"), "closure_falsification_probe")
    if set(probe) != {"probe_id", "method", "expected_failure_signal", "executed", "result"}:
        raise ResolutionContractError("closure_falsification_probe has an invalid shape")
    if probe.get("executed") is not True or _text(probe.get("result"), "probe result", required=True, limit=32).lower() != "passed":
        raise ResolutionContractError("closure_falsification_probe must be executed and passed before trusted closure")
    normalized = {
        "schema_version": ENVELOPE_SCHEMA_VERSION,
        "direct_outcomes": outcomes,
        "relevant_invariants": invariants,
        "truth_domains": domains,
        "adjacent_risks": risks,
        "excluded_scope": _bounded_list(raw.get("excluded_scope"), "excluded_scope"),
        "required_evidence": evidence,
        "closure_falsification_probe": {
            "probe_id": _id(probe.get("probe_id"), "probe_id"),
            "method": _text(probe.get("method"), "probe method", required=True),
            "expected_failure_signal": _text(probe.get("expected_failure_signal"), "expected_failure_signal", required=True),
            "executed": True,
            "result": "passed",
        },
    }
    _bounded_object_size(normalized, "resolution_envelope", MAX_ENVELOPE_BYTES)
    return normalized


def _object_list(value: Any, name: str, *, max_items: int, required: bool = False) -> list[dict[str, Any]]:
    if value is None:
        value = []
    if not isinstance(value, list) or len(value) > max_items:
        raise ResolutionContractError(f"{name} must be a bounded list")
    if required and not value:
        raise ResolutionContractError(f"{name} must not be empty")
    if any(not isinstance(item, dict) for item in value):
        raise ResolutionContractError(f"{name} items must be objects")
    return list(value)
