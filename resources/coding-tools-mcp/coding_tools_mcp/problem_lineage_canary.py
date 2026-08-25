"""Read-only C4 canary receipt for Problem Resolution Lineage v11.

The receipt is deliberately an instrument check, not a cohort classifier or a
policy engine.  It reads one immutable ledger snapshot, reports only aggregate
mechanics and explicitly leaves natural-workload, annotation, and efficacy
claims unobserved until their separately authorized evidence exists.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any

from .ledger_analysis import LedgerFacts
from .problem_lineage import PROBLEM_EVENT_SCHEMA_CURRENT, PROBLEM_SCHEMA_VERSION
from .problem_resolution_economics import ProblemLineageFacts


PROBLEM_LINEAGE_CANARY_SCHEMA_VERSION = 1
PRL_V11_CODEBOOK_VERSION = "1.0.0"
PRL_V11_COHORT_RULES_VERSION = "1.0.0"
_AUTHORITATIVE_CONFIRMATION_AUTHORITIES = frozenset({"RUNTIME_EXPLICIT_USER", "RUNTIME_HUMAN_REVIEW"})


def _text(value: Any) -> str:
    return str(value or "").strip()


def _current(event: dict[str, Any]) -> bool:
    return int(event.get("event_schema_version") or 1) == PROBLEM_EVENT_SCHEMA_CURRENT


def _revision_capsule_is_valid(revision: dict[str, Any]) -> bool:
    """Verify persisted capsule bytes without exposing their contents in a receipt."""
    raw = revision.get("typed_contract_capsule")
    try:
        capsule = json.loads(str(raw or ""))
    except (TypeError, json.JSONDecodeError):
        return False
    if not isinstance(capsule, dict):
        return False
    canonical = json.dumps(capsule, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest() == _text(revision.get("contract_fingerprint"))


def _coverage(numerator: int, denominator: int) -> dict[str, Any]:
    rate = round(numerator / denominator, 6) if denominator else None
    interval: list[float] | None = None
    if denominator:
        # Wilson 95% interval remains descriptive at a small canary n; it is
        # never an efficacy interval or a population claim.
        z = 1.959963984540054
        center = (numerator + z * z / 2) / (denominator + z * z)
        margin = z * math.sqrt((numerator * (denominator - numerator) / denominator + z * z / 4) / denominator) / (1 + z * z / denominator)
        interval = [round(max(0.0, center - margin), 6), round(min(1.0, center + margin), 6)]
    return {
        "numerator": numerator,
        "denominator": denominator,
        "rate": rate,
        "wilson_95_interval": interval,
        "small_n_policy": "descriptive_mechanics_only_not_efficacy_inference",
    }


def _full_claim_manifest_coverage(ledger: LedgerFacts, events: list[dict[str, Any]]) -> dict[str, Any]:
    run_ids = sorted({_text(event.get("run_id")) for event in events if _current(event) and _text(event.get("run_id"))})
    claimed = complete = 0
    for run_id in run_ids:
        for wave in ledger.list_waves(run_id):
            metadata = wave.get("metadata") if isinstance(wave.get("metadata"), dict) else {}
            context = metadata.get("problem_resolution") if isinstance(metadata.get("problem_resolution"), dict) else {}
            if not isinstance(context, dict) or context.get("work_origin") != "problem" or context.get("resolution_claim") != "full_problem":
                continue
            claimed += 1
            manifest = context.get("coverage_manifest")
            if isinstance(manifest, dict) and manifest:
                complete += 1
    return _coverage(complete, claimed)


def problem_lineage_canary_report(
    ledger: LedgerFacts,
    problems: ProblemLineageFacts,
    *,
    integrity_check: str,
    foreign_key_violations: int,
) -> dict[str, Any]:
    """Return a content-free C4 readiness receipt from immutable facts only."""
    if not isinstance(ledger, LedgerFacts) or not isinstance(problems, ProblemLineageFacts):
        raise TypeError("problem-lineage canary requires immutable LedgerFacts and ProblemLineageFacts")

    if problems.schema_version != PROBLEM_SCHEMA_VERSION:
        return {
            "schema_version": PROBLEM_LINEAGE_CANARY_SCHEMA_VERSION,
            "status": "PRL_SCHEMA_INACTIVE",
            "observed_schema_version": problems.schema_version,
            "policy": {"no_writer": True, "no_historical_backfill": True, "natural_cohort_not_inferred": True},
        }

    current_events = [event for event in problems.events if _current(event)]
    revision_pairs = {(str(revision.get("problem_id") or ""), int(revision.get("revision") or 0)) for revision in problems.revisions}
    attempt_events = [event for event in current_events if _text(event.get("relation_type")) == "ENGINEERING_ATTEMPT_BOUND"]
    exact_attempts = [
        event for event in attempt_events
        if _text(event.get("link_status")) == "EXACT"
        and (str(event.get("problem_id") or ""), int(event.get("problem_revision") or 0)) in revision_pairs
    ]
    confirmations = [event for event in current_events if _text(event.get("relation_type")) == "CONFIRMED_RESOLUTION"]
    authoritative_confirmations = [
        event for event in confirmations
        if _text(event.get("transition_authority")) in _AUTHORITATIVE_CONFIRMATION_AUTHORITIES
        and _text(event.get("state_after")) == "RESOLVED_CONFIRMED"
    ]
    clock_events = [event for event in current_events if _text(event.get("occurred_at"))]
    trusted_clock_events = [
        event for event in clock_events
        if _text(event.get("occurred_at_source")) and _text(event.get("clock_authority"))
    ]
    invalid_chains = sum(1 for thread in problems.threads if not problems.verify_chain(_text(thread.get("problem_id"))).get("ok"))
    invalid_capsules = sum(1 for revision in problems.revisions if not _revision_capsule_is_valid(revision))
    ambiguous_or_unlinked = sum(1 for event in current_events if _text(event.get("link_status")) != "EXACT")
    integrity_ok = _text(integrity_check).lower() == "ok" and foreign_key_violations == 0 and invalid_chains == 0

    status = "C4_SOURCE_READY_AWAITING_NATURAL_CANARY" if integrity_ok and invalid_capsules == 0 else "C4_INTEGRITY_BLOCKED"
    return {
        "schema_version": PROBLEM_LINEAGE_CANARY_SCHEMA_VERSION,
        "status": status,
        "codebook": {
            "problem_identity_version": PRL_V11_CODEBOOK_VERSION,
            "action_kind_version": PRL_V11_CODEBOOK_VERSION,
            "cohort_rules_version": PRL_V11_COHORT_RULES_VERSION,
            "semantic_change_rule": "bump_version_and_start_or_stratify_a_new_cohort",
        },
        "natural_evidence": {
            "attested": False,
            "observed_current_v11_events": len(current_events),
            "natural_event_count": None,
            "reason": "the_ledger_does_not_classify_records_as_natural_and_this_report_never_fabricates_a_cohort",
        },
        "integrity": {
            "sqlite_integrity_check": _text(integrity_check) or "unknown",
            "foreign_key_violations": foreign_key_violations,
            "problem_chain_invalid_threads": invalid_chains,
            "typed_contract_capsule_invalid_revisions": invalid_capsules,
            "all_observed_checks_pass": integrity_ok and invalid_capsules == 0,
        },
        "mechanics": {
            "exact_revision_binding": _coverage(len(exact_attempts), len(attempt_events)),
            "criterion_to_proof_structural_coverage": _full_claim_manifest_coverage(ledger, current_events),
            "authoritative_confirmation": _coverage(len(authoritative_confirmations), len(confirmations)),
            "attested_occurrence_clock": _coverage(len(trusted_clock_events), len(clock_events)),
        },
        "manual_review_queue": {
            "problem_identity_units": len(problems.revisions),
            "action_kind_events": len(current_events),
            "transition_authority_events": len(current_events),
            "timestamp_authority_events": len(clock_events),
            "capsule_privacy_review_units": len(problems.revisions),
            "criterion_proof_attribution_units": _full_claim_manifest_coverage(ledger, current_events)["denominator"],
            "ambiguous_or_unlinked_events": ambiguous_or_unlinked,
            "false_split_merge": "manual_double_annotation_required;_not_inferred_from_aggregate_ledger_data",
            "reliability": "not_observed_until_independent_annotation_is_recorded",
        },
        "policy": {
            "immutable_snapshot_required": True,
            "no_writer_or_schema_mutation": True,
            "no_raw_problem_or_capsule_content": True,
            "natural_cohort_not_inferred": True,
            "no_c5_shadow_or_c6_treatment_activation": True,
            "no_efficacy_or_policy_promotion": True,
        },
    }
