from __future__ import annotations

import json
from collections import Counter, defaultdict
from typing import Any

from .orchestration_ledger import OrchestrationLedger


WORKFLOW_ORDER = ("feature", "diagnose", "bugfix", "test_failure", "build_release", "custom", "refactor")
REPAIR_CAUSE_CODES = {
    "patch_context_ambiguity": {
        "PATCH_AMBIGUOUS",
        "PATCH_CONTEXT_AMBIGUOUS",
        "PATCH_CONTEXT_NOT_FOUND",
        "PATCH_HUNKS_OVERLAP",
    },
    "source_base_drift": {"BASE_DRIFT", "CONTRACT_DRIFT"},
    "environment_workdir": {"NOT_A_DIRECTORY", "RUNTIME_DIR_UNWRITABLE"},
    "runtime_tool_failure": {
        "BACKGROUND_OPERATION_FAILED",
        "RUNTIME_ACTIVATION_PENDING",
        "RUNTIME_BUSY",
        "RUNTIME_RESUME_REQUIRED",
        "SEMANTIC_PROVIDER_CALL_FAILED",
        "SEMANTIC_PROVIDER_STATUS_FAILED",
        "WORKFLOW_RUNTIME_EXCEEDED",
    },
    "provider_capacity": {"CAPACITY", "CODEX_CAPACITY", "MODEL_CAPACITY_COOLDOWN", "OPENCODE_PROVIDER_CAPACITY"},
    "proof_timeout": {"PROOF_TIMEOUT"},
    "acceptance_correction": {"SOL_REJECTED"},
}
PLANNED_REPAIR_CAUSES = (
    "patch_context_ambiguity",
    "source_base_drift",
    "wrong_root_cause",
    "oracle_weakness",
    "environment_workdir",
    "runtime_tool_failure",
    "missing_requirement",
    "provider_capacity",
    "proof_timeout",
    "acceptance_correction",
)


def _percentile(values: list[int], percentile: int) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    rank = max(1, min(len(ordered), (len(ordered) * percentile + 99) // 100))
    return int(ordered[rank - 1])


def _workflow_name(metadata: dict[str, Any]) -> str:
    workflow = str(metadata.get("workflow") or "").strip().lower()
    return workflow if workflow in WORKFLOW_ORDER else "unknown"


def repair_cause_for_failure_class(failure_class: str) -> str | None:
    """Map a durable structured failure class to the existing rework cause taxonomy."""
    normalized = str(failure_class or "").strip().upper()
    for cause, codes in REPAIR_CAUSE_CODES.items():
        if normalized in codes:
            return cause
    return None


def high_confidence_replan_reason_category(reason: Any) -> tuple[str | None, str | None]:
    """Classify only durable replan reasons covered by narrow evidence-backed rules."""
    text = " ".join(str(reason or "").strip().lower().split())
    if not text:
        return (None, None)
    if "rustfmt" in text and "formatting-only" in text:
        return ("formatting_only_repair", "rustfmt_formatting_only")
    if "oracle selection" in text and "cargo package" in text and "binary target name" in text:
        return ("oracle_selection_repair", "cargo_binary_name_used_as_package")
    baseline_markers = (
        "19 unrelated", "19 errors", "compute_placement_policy", "broken root lib-test harness",
    )
    if any(marker in text for marker in baseline_markers) and (
        "unrelated" in text or "known" in text or "root lib-test" in text or "cfg(test)" in text
    ):
        return ("environment_or_baseline_repair", "known_unrelated_test_baseline")
    if "wrong root cause" in text:
        return ("causal_solution_repair", "explicit_wrong_root_cause")
    if "missing requirement" in text:
        return ("causal_solution_repair", "explicit_missing_requirement")
    if "supervisor_not_ready" in text or "provider capacity" in text:
        return ("orchestration_repair", "explicit_orchestration_failure")
    return (None, None)


def _repair_cause(failure_class: str) -> str | None:
    return repair_cause_for_failure_class(failure_class)


def _scope_observation(events: list[dict[str, Any]]) -> tuple[int | None, bool]:
    selected: set[str] = set()
    observed = False
    censored = False
    for event in events:
        if event.get("event_type") != "context_prepared":
            continue
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        paths = payload.get("selected_paths")
        if not isinstance(paths, list):
            continue
        observed = True
        normalized = [str(item).strip() for item in paths if str(item).strip()]
        selected.update(normalized)
        if len(paths) >= 40:
            censored = True
    if not observed:
        return None, False
    return len(selected), censored


def _oracle_observation(events: list[dict[str, Any]]) -> bool | None:
    values: list[bool] = []
    for event in events:
        if event.get("event_type") != "oracle_preflight":
            continue
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        if isinstance(payload.get("strong_oracle"), bool):
            values.append(bool(payload["strong_oracle"]))
    if not values:
        return None
    return any(values)


def _countermeasure_report(
    *,
    repair_events: dict[str, int],
    affected_runs: dict[str, int],
    preflight_avoided: dict[str, Any],
) -> list[dict[str, Any]]:
    definitions = (
        ("patch_preflight", "patch_context_ambiguity"),
        ("workdir_resolution", "environment_workdir"),
        ("semantic_localization", "runtime_tool_failure"),
        ("exact_source", "source_base_drift"),
        ("recovery_fencing", "runtime_tool_failure"),
        ("solution_minimization_later", None),
    )
    result: list[dict[str, Any]] = []
    for name, category in definitions:
        active_later = name == "solution_minimization_later"
        direct_evidence: dict[str, Any] = {"status": "not_directly_attributed"}
        if name == "patch_preflight":
            direct_evidence = {
                "status": "guardrail_observed",
                "preflight_avoided_count": int(preflight_avoided.get("count") or 0),
                "error_codes": dict(preflight_avoided.get("error_codes") or {}),
                "meaning": "known no-write patch failures stopped before orchestration run creation",
            }
        elif active_later:
            direct_evidence = {"status": "not_active_in_p2"}
        current = {
            "repair_cause_events": int(repair_events.get(category, 0)) if category else None,
            "affected_repaired_runs": int(affected_runs.get(category, 0)) if category else None,
        }
        result.append({
            "intervention": name,
            "monitored_repair_category": category,
            "baseline": {"status": "missing_comparable_pre_intervention_epoch"},
            "intervention_evidence": direct_evidence,
            "fresh_rerun": current,
            "effect_estimate": None,
            "status": "not_active" if active_later else "hold_not_causally_estimable",
            "hold_reasons": (
                ["intervention_not_active_in_p2"]
                if active_later
                else ["no_comparable_pre_intervention_cohort", "no_frozen_activation_epoch_for_effect_estimation"]
            ),
        })
    return result


def stratified_rework_diagnosis(ledger: OrchestrationLedger, *, limit: int = 5000) -> dict[str, Any]:
    """Diagnose accepted-result rework without converting observational history into causal effects."""
    bounded_limit = max(1, min(int(limit), 5000))
    clauses = [
        "status='accepted'",
        "(json_extract(metadata_json, '$.evaluation.provenance') IS NULL OR lower(json_extract(metadata_json, '$.evaluation.provenance'))='representative')",
        "(json_extract(metadata_json, '$.evaluation.policy') IS NULL OR lower(json_extract(metadata_json, '$.evaluation.policy'))='chatweb_mcp')",
    ]
    with ledger._lock, ledger._connect() as connection:  # package-internal read of the canonical causal store
        rows = connection.execute(
            f"SELECT * FROM runs WHERE {' AND '.join(clauses)} ORDER BY started_at, run_id LIMIT ?",
            [bounded_limit + 1],
        ).fetchall()
        preflight_rows = connection.execute(
            """SELECT COALESCE(json_extract(summary_json, '$.error_code'), 'unknown') AS error_code,
                      COUNT(*) AS count
               FROM idempotency_records
               WHERE operation='agent_workflow'
                 AND status='failed'
                 AND json_extract(summary_json, '$.workflow_patch_preflight')=1
               GROUP BY error_code
               ORDER BY count DESC, error_code"""
        ).fetchall()
    truncated = len(rows) > bounded_limit
    selected = rows[:bounded_limit]
    preflight_errors = {str(row["error_code"]): int(row["count"]) for row in preflight_rows}
    preflight_avoided = {"count": sum(preflight_errors.values()), "error_codes": preflight_errors}

    buckets: dict[str, dict[str, Any]] = {}
    overall_failure_classes: Counter[str] = Counter()
    overall_cause_events: Counter[str] = Counter({cause: 0 for cause in PLANNED_REPAIR_CAUSES})
    overall_cause_runs: dict[str, set[str]] = defaultdict(set)
    overall_unclassified: Counter[str] = Counter()
    overall_reason_categories: Counter[str] = Counter()
    overall_reason_rules: Counter[str] = Counter()
    overall_classification_sources: Counter[str] = Counter()
    overall_direct_structured_mapped = 0
    overall_reason_fallback_structured = 0
    overall_reason_fallback_events = 0
    overall_unclassified_replan_events = 0
    explicit_model_route = 0

    def bucket(workflow: str) -> dict[str, Any]:
        if workflow not in buckets:
            buckets[workflow] = {
                "n": 0,
                "first_pass": 0,
                "repaired": 0,
                "replans": 0,
                "all_ttar": [],
                "first_ttar": [],
                "repaired_ttar": [],
                "failure_classes": Counter(),
                "cause_events": Counter({cause: 0 for cause in PLANNED_REPAIR_CAUSES}),
                "cause_runs": defaultdict(set),
                "unclassified": Counter(),
                "reason_categories": Counter(),
                "reason_rules": Counter(),
                "classification_sources": Counter(),
                "scope_values": [],
                "scope_observed": 0,
                "scope_unknown": 0,
                "scope_censored": 0,
                "oracle_observed": 0,
                "oracle_strong": 0,
                "oracle_not_strong": 0,
                "oracle_unknown": 0,
            }
        return buckets[workflow]

    for row in selected:
        run_id = str(row["run_id"])
        actual_routes = {
            str(delegation.get("route_resolved") or "").strip().lower()
            for wave in ledger.list_waves(run_id)
            for delegation in ledger.list_delegations(str(wave["wave_id"]))
            if str(delegation.get("route_resolved") or "").strip()
        }
        if any(route not in {"unknown", "deterministic", "mcp_deterministic"} for route in actual_routes):
            explicit_model_route += 1
            continue
        economics = ledger.accepted_result_economics(run_id)
        route = str((economics.get("route") or {}).get("resolved") or "unknown").strip().lower()
        if route not in {"", "unknown", "deterministic", "mcp_deterministic"}:
            explicit_model_route += 1
            continue
        try:
            metadata = json.loads(row["metadata_json"] or "{}")
        except (TypeError, json.JSONDecodeError):
            metadata = {}
        if not isinstance(metadata, dict):
            metadata = {}
        workflow = _workflow_name(metadata)
        target = bucket(workflow)
        target["n"] += 1
        replan_count = int((economics.get("repair") or {}).get("replan_count") or 0)
        target["replans"] += replan_count
        ttar = economics.get("tta_ms")
        if isinstance(ttar, int) and not isinstance(ttar, bool) and ttar >= 0:
            target["all_ttar"].append(ttar)
        repaired = replan_count > 0
        if repaired:
            target["repaired"] += 1
            if isinstance(ttar, int) and not isinstance(ttar, bool) and ttar >= 0:
                target["repaired_ttar"].append(ttar)
        else:
            target["first_pass"] += 1
            if isinstance(ttar, int) and not isinstance(ttar, bool) and ttar >= 0:
                target["first_ttar"].append(ttar)

        events = ledger.list_events(run_id)
        scope_size, scope_censored = _scope_observation(events)
        if scope_size is None:
            target["scope_unknown"] += 1
        elif scope_censored:
            target["scope_observed"] += 1
            target["scope_censored"] += 1
        else:
            target["scope_observed"] += 1
            target["scope_values"].append(scope_size)
        oracle = _oracle_observation(events)
        if oracle is None:
            target["oracle_unknown"] += 1
        else:
            target["oracle_observed"] += 1
            if oracle:
                target["oracle_strong"] += 1
            else:
                target["oracle_not_strong"] += 1

        if not repaired:
            continue
        causes_for_run: set[str] = set()
        failure_events = sorted(
            [event for event in events if event.get("event_type") == "failure_observed"],
            key=lambda event: int(event.get("seq") or 0),
        )
        reason_events = sorted(
            [event for event in events if str(event.get("event_type") or "") == "wave_replanned"],
            key=lambda event: int(event.get("seq") or 0),
        )
        for index, event in enumerate(failure_events):
            payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
            failure_class = str(payload.get("failure_class") or "UNKNOWN").strip().upper() or "UNKNOWN"
            target["failure_classes"][failure_class] += 1
            overall_failure_classes[failure_class] += 1
            cause = _repair_cause(failure_class)
            if cause is not None:
                target["cause_events"][cause] += 1
                overall_cause_events[cause] += 1
                causes_for_run.add(cause)
                target["classification_sources"]["structured_failure_class"] += 1
                overall_classification_sources["structured_failure_class"] += 1
                overall_direct_structured_mapped += 1
                continue

            reason_payload = (
                reason_events[index].get("payload")
                if index < len(reason_events) and isinstance(reason_events[index].get("payload"), dict)
                else {}
            )
            category, rule = high_confidence_replan_reason_category(reason_payload.get("reason"))
            if category is not None and rule is not None:
                target["reason_categories"][category] += 1
                target["reason_rules"][rule] += 1
                target["classification_sources"]["durable_wave_replanned_reason_high_confidence"] += 1
                overall_reason_categories[category] += 1
                overall_reason_rules[rule] += 1
                overall_classification_sources["durable_wave_replanned_reason_high_confidence"] += 1
                overall_reason_fallback_structured += 1
                overall_reason_fallback_events += 1
                continue

            target["unclassified"][failure_class] += 1
            overall_unclassified[failure_class] += 1
            target["classification_sources"]["unclassified"] += 1
            overall_classification_sources["unclassified"] += 1
            overall_unclassified_replan_events += 1
        for cause in causes_for_run:
            target["cause_runs"][cause].add(run_id)
            overall_cause_runs[cause].add(run_id)

    ordered_names = [name for name in WORKFLOW_ORDER if name in buckets]
    if "unknown" in buckets:
        ordered_names.append("unknown")
    strata: list[dict[str, Any]] = []
    for name in ordered_names:
        item = buckets[name]
        n = int(item["n"])
        strata.append({
            "workflow": name,
            "n": n,
            "first_pass_accepted": int(item["first_pass"]),
            "repaired_accepted": int(item["repaired"]),
            "first_pass_rate": round(item["first_pass"] / n, 6) if n else None,
            "repaired_rate": round(item["repaired"] / n, 6) if n else None,
            "replan_count": int(item["replans"]),
            "ttar_ms": {
                "all_p50": _percentile(item["all_ttar"], 50),
                "all_p90": _percentile(item["all_ttar"], 90),
                "first_pass_p50": _percentile(item["first_ttar"], 50),
                "first_pass_p90": _percentile(item["first_ttar"], 90),
                "repaired_p50": _percentile(item["repaired_ttar"], 50),
                "repaired_p90": _percentile(item["repaired_ttar"], 90),
            },
            "repair_failure_classes": dict(sorted(item["failure_classes"].items())),
            "repair_causes": {
                "event_counts": {cause: int(item["cause_events"].get(cause, 0)) for cause in PLANNED_REPAIR_CAUSES},
                "affected_run_counts": {cause: len(item["cause_runs"].get(cause, set())) for cause in PLANNED_REPAIR_CAUSES},
                "unclassified_structured_failure_classes": dict(sorted(item["unclassified"].items())),
                "durable_reason_category_counts": dict(sorted(item["reason_categories"].items())),
                "high_confidence_reason_rule_counts": dict(sorted(item["reason_rules"].items())),
                "classification_source_counts": dict(sorted(item["classification_sources"].items())),
            },
            "scope_size": {
                "measurement": "context_prepared.selected_paths_unique",
                "observed_runs": int(item["scope_observed"]),
                "unknown_runs": int(item["scope_unknown"]),
                "censored_at_event_path_cap_runs": int(item["scope_censored"]),
                "p50_paths": _percentile(item["scope_values"], 50),
                "p90_paths": _percentile(item["scope_values"], 90),
            },
            "oracle_strength": {
                "measurement": "oracle_preflight.strong_oracle",
                "observed_runs": int(item["oracle_observed"]),
                "strong_runs": int(item["oracle_strong"]),
                "not_strong_runs": int(item["oracle_not_strong"]),
                "unknown_runs": int(item["oracle_unknown"]),
            },
        })

    overall_events = {cause: int(overall_cause_events.get(cause, 0)) for cause in PLANNED_REPAIR_CAUSES}
    overall_runs = {cause: len(overall_cause_runs.get(cause, set())) for cause in PLANNED_REPAIR_CAUSES}
    included = sum(int(item["n"]) for item in buckets.values())
    mapped_failure_events = overall_direct_structured_mapped + overall_reason_fallback_structured
    unclassified_failure_events = sum(int(count) for count in overall_unclassified.values())
    classified_failure_events = mapped_failure_events + unclassified_failure_events
    oracle_observed_runs = sum(int(item["oracle_observed"]) for item in buckets.values())
    oracle_strong_runs = sum(int(item["oracle_strong"]) for item in buckets.values())
    oracle_not_strong_runs = sum(int(item["oracle_not_strong"]) for item in buckets.values())
    oracle_unknown_runs = sum(int(item["oracle_unknown"]) for item in buckets.values())
    return {
        "schema_version": 1,
        "cohort": "accepted_representative_chatweb_mcp_model_free",
        "accepted_runs_scanned": len(selected),
        "accepted_runs": included,
        "accepted_runs_truncated": truncated,
        "excluded": {"explicit_model_route": explicit_model_route},
        "workflow_strata": strata,
        "overall_repair_failure_classes": dict(sorted(overall_failure_classes.items())),
        "overall_repair_causes": {
            "event_counts": overall_events,
            "affected_run_counts": overall_runs,
            "unclassified_structured_failure_classes": dict(sorted(overall_unclassified.items())),
            "durable_reason_category_counts": dict(sorted(overall_reason_categories.items())),
            "high_confidence_reason_rule_counts": dict(sorted(overall_reason_rules.items())),
            "classification_source_counts": dict(sorted(overall_classification_sources.items())),
        },
        "causal_classification": {
            "basis": "structured_failure_class_then_high_confidence_durable_replan_reason_on_repaired_accepted_runs",
            "total_failure_events": classified_failure_events,
            "mapped_failure_events": mapped_failure_events,
            "unclassified_failure_events": unclassified_failure_events,
            "mapped_event_coverage": (
                round(mapped_failure_events / classified_failure_events, 6)
                if classified_failure_events
                else None
            ),
            "largest_unclassified_failure_class": (
                overall_unclassified.most_common(1)[0][0] if overall_unclassified else None
            ),
            "durable_reason_fallback_events": overall_reason_fallback_events,
            "classified_replan_events": overall_direct_structured_mapped + overall_reason_fallback_events,
            "unclassified_replan_events": overall_unclassified_replan_events,
            "classification_source_counts": dict(sorted(overall_classification_sources.items())),
            "high_confidence_reason_category_counts": dict(sorted(overall_reason_categories.items())),
            "high_confidence_reason_rule_counts": dict(sorted(overall_reason_rules.items())),
            "unclassified_zero_means_absent": False,
        },
        "oracle_observation": {
            "measurement": "oracle_preflight.strong_oracle",
            "eligible_runs": included,
            "observed_runs": oracle_observed_runs,
            "strong_runs": oracle_strong_runs,
            "not_strong_runs": oracle_not_strong_runs,
            "unknown_runs": oracle_unknown_runs,
            "coverage": round(oracle_observed_runs / included, 6) if included else None,
            "unknown_not_imputed": True,
        },
        "preflight_avoided": {
            **preflight_avoided,
            "meaning": "known no-write patch failures stopped before orchestration run creation",
        },
        "countermeasure_evaluation": _countermeasure_report(
            repair_events=overall_events,
            affected_runs=overall_runs,
            preflight_avoided=preflight_avoided,
        ),
        "policy": {
            "accepted_only_observational_cohort": True,
            "not_a_causal_treatment_effect_estimate": True,
            "repair_cause_requires_structured_failure_evidence": True,
            "unknown_scope_or_oracle_not_imputed": True,
            "unmatched_structured_failures_remain_unclassified": True,
            "zero_planned_cause_without_evidence_is_not_proof_of_absence": True,
            "countermeasure_effect_requires_comparable_pre_post_or_paired_evidence": True,
            "scope_path_cap_censored_runs_excluded_from_scope_percentiles": True,
        },
    }
