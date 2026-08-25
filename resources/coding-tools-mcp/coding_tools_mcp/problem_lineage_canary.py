"""Read-only C4 readiness receipt for the PRL v11 measurement instrument."""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from typing import Any

from .acceptance_receipts import passed_proof_fingerprint
from .ledger_analysis import LedgerFacts
from .problem_lineage import PROBLEM_EVENT_SCHEMA_CURRENT, PROBLEM_SCHEMA_VERSION, ProblemLineageError, _capsule
from .problem_resolution_economics import ProblemLineageFacts


PROBLEM_LINEAGE_CANARY_SCHEMA_VERSION = 2
PRL_V11_CODEBOOK_VERSION = "1.0.0"
PRL_V11_COHORT_RULES_VERSION = "1.0.0"
_AUTHORITATIVE_CONFIRMATION_AUTHORITIES = frozenset({"RUNTIME_EXPLICIT_USER", "RUNTIME_HUMAN_REVIEW"})


def _text(value: Any) -> str:
    return str(value or "").strip()


def _current(event: dict[str, Any]) -> bool:
    return int(event.get("event_schema_version") or 1) == PROBLEM_EVENT_SCHEMA_CURRENT


def _sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _coverage(numerator: int, denominator: int, *, invalid: Counter[str] | None = None, contract: str = "") -> dict[str, Any]:
    rate = round(numerator / denominator, 6) if denominator else None
    interval: list[float] | None = None
    if denominator:
        z = 1.959963984540054
        center = (numerator + z * z / 2) / (denominator + z * z)
        margin = z * math.sqrt((numerator * (denominator - numerator) / denominator + z * z / 4) / denominator) / (1 + z * z / denominator)
        interval = [round(max(0.0, center - margin), 6), round(min(1.0, center + margin), 6)]
    result: dict[str, Any] = {"numerator": numerator, "denominator": denominator, "rate": rate, "wilson_95_interval": interval, "small_n_policy": "descriptive_mechanics_only_not_efficacy_inference"}
    if invalid is not None:
        result["invalid_reason_counts"] = dict(sorted(invalid.items()))
    if contract:
        result["verification_contract"] = contract
    return result


def _revision_contract_verdict(revision: dict[str, Any], facts: ProblemLineageFacts) -> tuple[bool, str, dict[str, Any] | None]:
    problem_id, number = _text(revision.get("problem_id")), revision.get("revision")
    raw = revision.get("typed_contract_capsule")
    if not problem_id or not isinstance(number, int) or isinstance(number, bool) or number < 1 or not isinstance(raw, str):
        return False, "revision_identity_invalid", None
    try:
        capsule = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return False, "capsule_json_invalid", None
    if not isinstance(capsule, dict) or json.dumps(capsule, ensure_ascii=False, sort_keys=True, separators=(",", ":")) != raw:
        return False, "capsule_not_canonical", None
    try:
        normalized = _capsule(capsule, required=True)
    except ProblemLineageError:
        return False, "capsule_contract_or_privacy_invalid", None
    if normalized != capsule:
        return False, "capsule_contract_not_normalized", None
    if not isinstance(revision.get("criteria_count"), int) or isinstance(revision.get("criteria_count"), bool) or revision["criteria_count"] != len(capsule["acceptance_criteria"]):
        return False, "criteria_count_invalid", None
    contract_fp, criteria_fp = _sha(capsule), _sha(capsule["acceptance_criteria"])
    if revision.get("contract_fingerprint") != contract_fp or revision.get("criteria_fingerprint") != criteria_fp:
        return False, "revision_fingerprint_invalid", None
    events = facts.events_for_revision(problem_id, number)
    created_seq = revision.get("created_event_seq")
    creation = next((event for event in events if event.get("seq") == created_seq), None)
    expected_relation = "OPEN" if number == 1 else "REVISION"
    if creation is None or not bool(creation.get("eligible_for_policy")) or _text(creation.get("relation_type")) != expected_relation:
        return False, "revision_creation_event_invalid", None
    if creation.get("contract_fingerprint") != contract_fp or creation.get("criteria_fingerprint") != criteria_fp or creation.get("criteria_count") != revision["criteria_count"]:
        return False, "revision_creation_metadata_mismatch", None
    return True, "ok", {"capsule": capsule, "contract_fingerprint": contract_fp, "criteria_fingerprint": criteria_fp, "criteria_count": revision["criteria_count"], "engineering_floor": revision.get("engineering_floor"), "task_class": revision.get("task_class")}


def _revision_integrity_index(problems: ProblemLineageFacts) -> tuple[dict[tuple[str, int], dict[str, Any]], Counter[str]]:
    index: dict[tuple[str, int], dict[str, Any]] = {}
    reasons: Counter[str] = Counter()
    for revision in problems.revisions:
        problem_id, number = _text(revision.get("problem_id")), revision.get("revision")
        if not isinstance(number, int) or isinstance(number, bool):
            reasons["revision_identity_invalid"] += 1
            continue
        valid, reason, item = _revision_contract_verdict(revision, problems)
        if not valid or item is None:
            reasons[reason] += 1
        else:
            index[(problem_id, number)] = item
    return index, reasons


def _current_projection_integrity(problems: ProblemLineageFacts, index: dict[tuple[str, int], dict[str, Any]]) -> Counter[str]:
    reasons: Counter[str] = Counter()
    thread_ids = {_text(thread.get("problem_id")) for thread in problems.threads}
    for revision in problems.revisions:
        if _text(revision.get("problem_id")) not in thread_ids:
            reasons["orphan_revision_row"] += 1
    for thread in problems.threads:
        problem_id, current = _text(thread.get("problem_id")), thread.get("current_revision")
        if not isinstance(current, int) or isinstance(current, bool) or current < 1:
            reasons["current_revision_invalid"] += 1; continue
        numbers = [item.get("revision") for item in problems.revisions_for_problem(problem_id)]
        if numbers != list(range(1, current + 1)):
            reasons["revision_sequence_noncontiguous"] += 1; continue
        revision = index.get((problem_id, current))
        if revision is None:
            reasons["current_revision_contract_invalid"] += 1; continue
        if thread.get("task_class") != revision["task_class"] or thread.get("engineering_floor") != revision["engineering_floor"]:
            reasons["current_revision_projection_metadata_mismatch"] += 1
    return reasons


def _full_claim_unit(ledger: LedgerFacts, problems: ProblemLineageFacts, run_id: str, wave: dict[str, Any], index: dict[tuple[str, int], dict[str, Any]]) -> tuple[bool, str]:
    metadata = wave.get("metadata") if isinstance(wave.get("metadata"), dict) else {}
    context = metadata.get("problem_resolution") if isinstance(metadata.get("problem_resolution"), dict) else {}
    if not isinstance(context, dict) or context.get("work_origin") != "problem" or context.get("resolution_claim") != "full_problem":
        return False, "context_invalid"
    problem_id, number, fingerprint = context.get("problem_id"), context.get("problem_revision"), context.get("contract_fingerprint")
    if not isinstance(problem_id, str) or not isinstance(number, int) or isinstance(number, bool) or not isinstance(fingerprint, str):
        return False, "context_identity_invalid"
    revision = index.get((problem_id, number))
    if revision is None or fingerprint != revision["contract_fingerprint"] or context.get("engineering_floor") != revision["engineering_floor"]:
        return False, "revision_missing_or_invalid"
    links = [event for event in problems.events_for_revision(problem_id, number) if _current(event) and _text(event.get("relation_type")) == "ENGINEERING_ATTEMPT_BOUND" and event.get("run_id") == run_id and event.get("wave_id") == wave.get("wave_id") and _text(event.get("link_status")) == "EXACT"]
    if not links:
        return False, "exact_attempt_binding_missing"
    criteria = {item["criterion_id"] for item in revision["capsule"]["acceptance_criteria"]}
    manifest = context.get("coverage_manifest")
    if revision["engineering_floor"] == "REQUIRED":
        if not isinstance(manifest, dict) or set(manifest) != criteria or context.get("coverage_manifest_sha256") != _sha(manifest):
            return False, "manifest_contract_invalid"
        proof_ids: set[str] = set()
        for criterion in criteria:
            items = manifest.get(criterion)
            if not isinstance(items, list) or not items or len(items) != len(set(items)):
                return False, "manifest_contract_invalid"
            proof_ids.update(items)
    elif revision["engineering_floor"] == "NOT_APPLICABLE":
        dispositions = context.get("criterion_dispositions")
        if not isinstance(dispositions, dict) or set(dispositions) != criteria or any(item != "SATISFIED_NON_CODE" for item in dispositions.values()) or context.get("criterion_dispositions_sha256") != _sha(dispositions):
            return False, "manifest_contract_invalid"
        proof_ids = set()
    else:
        return False, "manifest_contract_invalid"
    proofs = ledger.list_proofs(run_id, wave_id=str(wave.get("wave_id") or ""))
    by_id = {proof.get("proof_id"): proof for proof in proofs}
    for proof_id in proof_ids:
        proof = by_id.get(proof_id)
        if proof is None or proof.get("status") != "passed" or not _text(proof.get("input_fingerprint")):
            return False, "proof_not_passed_exact_wave"
    proof_fp = passed_proof_fingerprint(proofs)
    checkpoints = [checkpoint for checkpoint in ledger.list_checkpoints(run_id, wave_id=str(wave.get("wave_id") or "")) if checkpoint.get("status") == "accepted" and checkpoint.get("proof_fingerprint") == proof_fp]
    if not checkpoints or ledger.get_run(run_id) is None or ledger.get_run(run_id).get("status") != "accepted" or wave.get("status") != "accepted":
        return False, "accepted_checkpoint_missing_or_unbound"
    checkpoint = checkpoints[-1]
    if any(_text(proof.get("finished_at")) > _text(checkpoint.get("created_at")) for proof in proofs if _text(proof.get("finished_at"))):
        return False, "temporal_order_invalid"
    checkpoint_id = _text(checkpoint.get("checkpoint_id"))
    expected_id = "prl-provisional-v11-" + hashlib.sha256("\x1f".join((run_id, str(wave.get("wave_id") or ""), problem_id, str(number), checkpoint_id)).encode()).hexdigest()
    bridge = next((event for event in problems.events_for_revision(problem_id, number) if _current(event) and event.get("event_id") == expected_id and event.get("run_id") == run_id and event.get("wave_id") == wave.get("wave_id") and _text(event.get("relation_type")) == "PROVISIONAL_RESOLUTION" and _text(event.get("transition_authority")) in {"RUNTIME_EOCL", "RUNTIME_RECONCILIATION"}), None)
    if bridge is None:
        return False, "provisional_bridge_missing_or_mismatch"
    if _text(bridge.get("recorded_at")) < _text(checkpoint.get("created_at")):
        return False, "temporal_order_invalid"
    return True, "ok"


def _full_claim_exact_coverage(ledger: LedgerFacts, problems: ProblemLineageFacts, index: dict[tuple[str, int], dict[str, Any]]) -> dict[str, Any]:
    total = complete = 0; reasons: Counter[str] = Counter()
    for run in ledger.list_runs(limit=5000):
        run_id = _text(run.get("run_id"))
        for wave in ledger.list_waves(run_id):
            metadata = wave.get("metadata") if isinstance(wave.get("metadata"), dict) else {}
            context = metadata.get("problem_resolution") if isinstance(metadata.get("problem_resolution"), dict) else {}
            if not isinstance(context, dict) or context.get("work_origin") != "problem" or context.get("resolution_claim") != "full_problem":
                continue
            total += 1
            valid, reason = _full_claim_unit(ledger, problems, run_id, wave, index)
            if valid: complete += 1
            else: reasons[reason] += 1
    return _coverage(complete, total, invalid=reasons, contract="exact_revision_manifest_proof_checkpoint_bridge_v1")


def problem_lineage_canary_report(ledger: LedgerFacts, problems: ProblemLineageFacts, *, integrity_check: str, foreign_key_violations: int) -> dict[str, Any]:
    if not isinstance(ledger, LedgerFacts) or not isinstance(problems, ProblemLineageFacts):
        raise TypeError("problem-lineage canary requires immutable LedgerFacts and ProblemLineageFacts")
    if problems.schema_version != PROBLEM_SCHEMA_VERSION:
        return {"schema_version": PROBLEM_LINEAGE_CANARY_SCHEMA_VERSION, "status": "PRL_SCHEMA_INACTIVE", "observed_schema_version": problems.schema_version, "policy": {"no_writer": True, "no_historical_backfill": True, "natural_cohort_not_inferred": True}}
    current_events = [event for event in problems.events if _current(event)]
    index, revision_reasons = _revision_integrity_index(problems)
    projection_reasons = _current_projection_integrity(problems, index)
    revision_pairs = set(index)
    attempts = [event for event in current_events if _text(event.get("relation_type")) == "ENGINEERING_ATTEMPT_BOUND"]
    exact_attempts = [event for event in attempts if _text(event.get("link_status")) == "EXACT" and (event.get("problem_id"), event.get("problem_revision")) in revision_pairs]
    confirmations = [event for event in current_events if _text(event.get("relation_type")) == "CONFIRMED_RESOLUTION"]
    authoritative = [event for event in confirmations if _text(event.get("transition_authority")) in _AUTHORITATIVE_CONFIRMATION_AUTHORITIES and _text(event.get("state_after")) == "RESOLVED_CONFIRMED"]
    clock_events = [event for event in current_events if _text(event.get("occurred_at"))]
    trusted_clocks = [event for event in clock_events if _text(event.get("occurred_at_source")) and _text(event.get("clock_authority"))]
    invalid_chains = sum(1 for thread in problems.threads if not problems.verify_chain(_text(thread.get("problem_id"))).get("ok"))
    full_claims = _full_claim_exact_coverage(ledger, problems, index)
    integrity_ok = _text(integrity_check).lower() == "ok" and foreign_key_violations == 0 and invalid_chains == 0 and not revision_reasons and not projection_reasons
    status = "C4_INTEGRITY_BLOCKED" if not integrity_ok else "C4_MECHANICS_BLOCKED" if full_claims["numerator"] != full_claims["denominator"] else "C4_SOURCE_READY_AWAITING_NATURAL_CANARY"
    return {
        "schema_version": PROBLEM_LINEAGE_CANARY_SCHEMA_VERSION, "status": status,
        "codebook": {"problem_identity_version": PRL_V11_CODEBOOK_VERSION, "action_kind_version": PRL_V11_CODEBOOK_VERSION, "cohort_rules_version": PRL_V11_COHORT_RULES_VERSION, "semantic_change_rule": "bump_version_and_start_or_stratify_a_new_cohort"},
        "natural_evidence": {"attested": False, "observed_current_v11_events": len(current_events), "natural_event_count": None, "reason": "the_ledger_does_not_classify_records_as_natural_and_this_report_never_fabricates_a_cohort"},
        "integrity": {"sqlite_integrity_check": _text(integrity_check) or "unknown", "foreign_key_violations": foreign_key_violations, "problem_chain_invalid_threads": invalid_chains, "revision_contract_invalid_revisions": sum(revision_reasons.values()), "current_revision_projection_invalid_threads": sum(projection_reasons.values()), "orphan_or_noncontiguous_revision_rows": revision_reasons.get("orphan_revision_row", 0) + projection_reasons.get("revision_sequence_noncontiguous", 0), "revision_integrity_reason_counts": dict(sorted((revision_reasons + projection_reasons).items())), "all_observed_checks_pass": integrity_ok},
        "mechanics": {"exact_revision_binding": _coverage(len(exact_attempts), len(attempts)), "criterion_to_proof_structural_coverage": full_claims, "authoritative_confirmation": _coverage(len(authoritative), len(confirmations)), "attested_occurrence_clock": _coverage(len(trusted_clocks), len(clock_events))},
        "manual_review_queue": {"problem_identity_units": len(problems.revisions), "action_kind_events": len(current_events), "transition_authority_events": len(current_events), "timestamp_authority_events": len(clock_events), "capsule_privacy_review_units": len(problems.revisions), "criterion_proof_attribution_units": full_claims["denominator"], "ambiguous_or_unlinked_events": sum(1 for event in current_events if _text(event.get("link_status")) != "EXACT"), "false_split_merge": "manual_double_annotation_required;_not_inferred_from_aggregate_ledger_data", "reliability": "not_observed_until_independent_annotation_is_recorded"},
        "policy": {"immutable_snapshot_required": True, "no_writer_or_schema_mutation": True, "no_raw_problem_or_capsule_content": True, "natural_cohort_not_inferred": True, "no_c5_shadow_or_c6_treatment_activation": True, "no_efficacy_or_policy_promotion": True},
    }
