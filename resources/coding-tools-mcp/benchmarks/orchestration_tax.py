from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from coding_tools_mcp.orchestration_ledger import OrchestrationLedger
from coding_tools_mcp.usage_ledger import canonical_usage_payload


def _nonnegative_int(value: Any) -> int | None:
    return int(value) if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def _nearest_rank(values: list[float], percentile: int) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    rank = max(1, min(len(ordered), (len(ordered) * percentile + 99) // 100))
    return round(float(ordered[rank - 1]), 6)


def _controller_token_total(record: dict[str, Any]) -> tuple[int | None, str | None]:
    controller = record.get("controller") if isinstance(record.get("controller"), dict) else {}
    usage = controller.get("usage") if isinstance(controller.get("usage"), dict) else {}
    input_tokens = _nonnegative_int(usage.get("input_tokens"))
    output_tokens = _nonnegative_int(usage.get("output_tokens"))
    if input_tokens is None or output_tokens is None:
        return None, "controller_token_usage_incomplete"
    return input_tokens + output_tokens, None


def _provider_token_total(ledger: Any, run_id: str) -> tuple[int | None, str | None, int]:
    events = [
        item
        for item in ledger.list_usage_events(run_id, limit=None)
        if str(item.get("actor") or "provider").strip().lower() != "controller"
    ]
    if not events:
        return 0, None, 0
    total = 0
    for event in events:
        try:
            canonical = canonical_usage_payload(event)
        except ValueError:
            return None, "provider_token_usage_invalid", len(events)
        tokens = _nonnegative_int(canonical.get("total_tokens"))
        if tokens is None:
            return None, "provider_token_usage_incomplete", len(events)
        total += tokens
    return total, None, len(events)


def _run_usage(ledger: Any, record: dict[str, Any]) -> dict[str, Any]:
    controller_tokens, controller_reason = _controller_token_total(record)
    provider_tokens, provider_reason, provider_events = _provider_token_total(ledger, str(record.get("run_id") or ""))
    complete = controller_tokens is not None and provider_tokens is not None
    total_tokens = controller_tokens + provider_tokens if complete else None
    if not complete:
        reason = controller_reason or provider_reason or "token_usage_incomplete"
    elif controller_tokens == 0:
        reason = "controller_token_denominator_zero"
    else:
        reason = None
    amplification = (
        round(float(total_tokens) / float(controller_tokens), 6)
        if complete and controller_tokens and total_tokens is not None
        else None
    )
    return {
        "complete": complete,
        "reason": reason,
        "controller_tokens": controller_tokens,
        "provider_tokens": provider_tokens,
        "provider_usage_events": provider_events,
        "total_tokens": total_tokens,
        "root_work_amplification": amplification,
        "measurement": {
            "controller": "input_tokens_plus_output_tokens_cached_and_reasoning_subsets_not_double_counted",
            "provider": "sum_canonical_total_tokens_across_non_controller_usage_events",
            "unknown_is_not_zero": True,
        },
    }


def orchestration_tax_report(
    ledger: Any,
    *,
    baseline_policy: str = "chatweb_mcp",
    candidate_policies: tuple[str, ...] = ("solo_fast",),
    limit: int = 500,
    min_pairs: int = 10,
    min_task_classes: int = 3,
) -> dict[str, Any]:
    baseline = str(baseline_policy).strip().lower()
    candidates = tuple(dict.fromkeys(str(item).strip().lower() for item in candidate_policies if str(item).strip()))
    canonical = ledger.paired_policy_evaluation(
        baseline_policy=baseline,
        candidate_policies=candidates,
        limit=limit,
        min_pairs=min_pairs,
        min_task_classes=min_task_classes,
    )
    results = canonical.get("results") if isinstance(canonical.get("results"), list) else []
    wanted_pair_ids = {
        str(pair.get("pair_id") or "")
        for result in results
        if isinstance(result, dict)
        for pair in (result.get("pairs") if isinstance(result.get("pairs"), list) else [])
        if isinstance(pair, dict) and str(pair.get("pair_id") or "")
    }
    wanted_policies = {baseline, *candidates}
    index: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for run in ledger.list_runs(limit=max(1, int(limit))):
        run_id = str(run.get("run_id") or "")
        record = ledger.accepted_result_evaluation(run_id)
        evaluation = record.get("evaluation") if isinstance(record.get("evaluation"), dict) else {}
        pair_id = str(evaluation.get("pair_id") or "")
        policy = str(evaluation.get("policy") or "").strip().lower()
        if (
            record.get("pairing_eligible") is True
            and pair_id in wanted_pair_ids
            and policy in wanted_policies
            and evaluation.get("provenance") == "representative"
        ):
            index.setdefault((pair_id, policy), []).append(record)

    tax_results: list[dict[str, Any]] = []
    for canonical_result in results:
        if not isinstance(canonical_result, dict):
            continue
        candidate = str(canonical_result.get("candidate_policy") or "").strip().lower()
        exposed_pairs = canonical_result.get("pairs") if isinstance(canonical_result.get("pairs"), list) else []
        pair_rows: list[dict[str, Any]] = []
        multipliers: list[float] = []
        amplification_deltas: list[float] = []
        incomplete_reasons: dict[str, int] = {}
        for canonical_pair in exposed_pairs:
            if not isinstance(canonical_pair, dict):
                continue
            pair_id = str(canonical_pair.get("pair_id") or "")
            baseline_records = index.get((pair_id, baseline), [])
            candidate_records = index.get((pair_id, candidate), [])
            reason = None
            baseline_usage = None
            candidate_usage = None
            multiplier = None
            amplification_delta = None
            if len(baseline_records) != 1 or len(candidate_records) != 1:
                reason = "canonical_pair_run_resolution_ambiguous"
            else:
                baseline_usage = _run_usage(ledger, baseline_records[0])
                candidate_usage = _run_usage(ledger, candidate_records[0])
                baseline_total = baseline_usage.get("total_tokens")
                candidate_total = candidate_usage.get("total_tokens")
                if baseline_usage.get("complete") is not True:
                    reason = str(baseline_usage.get("reason") or "baseline_usage_incomplete")
                elif candidate_usage.get("complete") is not True:
                    reason = str(candidate_usage.get("reason") or "candidate_usage_incomplete")
                elif not isinstance(baseline_total, int) or baseline_total <= 0:
                    reason = "baseline_total_token_denominator_zero"
                else:
                    multiplier = round(float(candidate_total) / float(baseline_total), 6)
                    baseline_amp = baseline_usage.get("root_work_amplification")
                    candidate_amp = candidate_usage.get("root_work_amplification")
                    amplification_delta = (
                        round(float(candidate_amp) - float(baseline_amp), 6)
                        if isinstance(baseline_amp, (int, float)) and isinstance(candidate_amp, (int, float))
                        else None
                    )
                    if amplification_delta is None:
                        reason = "root_work_amplification_incomplete"
                        multiplier = None
            if reason:
                incomplete_reasons[reason] = incomplete_reasons.get(reason, 0) + 1
                amplification_delta = None
            else:
                multipliers.append(float(multiplier))
                amplification_deltas.append(float(amplification_delta))
            pair_rows.append({
                "pair_id": pair_id,
                "canonical_outcome": canonical_pair,
                "baseline_run_id": baseline_records[0].get("run_id") if len(baseline_records) == 1 else None,
                "candidate_run_id": candidate_records[0].get("run_id") if len(candidate_records) == 1 else None,
                "baseline_usage": baseline_usage,
                "candidate_usage": candidate_usage,
                "total_usage_multiplier": multiplier,
                "root_work_amplification_delta": amplification_delta,
                "complete": reason is None,
                "reason": reason,
            })

        pair_count = int(canonical_result.get("pair_count") or 0)
        truncated = pair_count > len(exposed_pairs)
        hold_reasons: list[str] = []
        if not exposed_pairs:
            hold_reasons.append("no_canonical_comparable_pairs")
        if truncated:
            hold_reasons.append("canonical_pair_rows_truncated")
        if incomplete_reasons:
            hold_reasons.append("usage_coverage_incomplete")
        tax_results.append({
            "candidate_policy": candidate,
            "status": "observed" if exposed_pairs and not hold_reasons else "hold",
            "hold_reasons": hold_reasons,
            "canonical_pair_count": pair_count,
            "canonical_pairs_exposed": len(exposed_pairs),
            "complete_usage_pairs": len(multipliers),
            "usage_coverage": round(len(multipliers) / len(exposed_pairs), 6) if exposed_pairs else None,
            "incomplete_reasons": dict(sorted(incomplete_reasons.items())),
            "total_usage_multiplier": {
                "definition": "candidate_total_observed_tokens / baseline_total_observed_tokens",
                "p50": _nearest_rank(multipliers, 50),
                "p90": _nearest_rank(multipliers, 90),
                "samples": len(multipliers),
            },
            "root_work_amplification_delta": {
                "definition": "candidate(total_observed_tokens/controller_tokens) - baseline(total_observed_tokens/controller_tokens)",
                "p50": _nearest_rank(amplification_deltas, 50),
                "p90": _nearest_rank(amplification_deltas, 90),
                "samples": len(amplification_deltas),
            },
            "automatic_activation": False,
            "pairs": pair_rows,
        })

    return {
        "schema_version": 1,
        "benchmark": "solo_fast_orchestration_tax",
        "evidence_class": "representative_paired_research_nonpromoting",
        "canonical_pairing_source": "OrchestrationLedger.paired_policy_evaluation",
        "baseline_policy": baseline,
        "candidate_policies": list(candidates),
        "canonical_pairing": canonical,
        "results": tax_results,
        "policy": {
            "canonical_pair_ids_are_authoritative_whitelist": True,
            "historical_counterfactuals_forbidden": True,
            "unknown_is_not_zero": True,
            "missing_usage_blocks_ratio": True,
            "quality_floor_remains_canonical_pair_evaluator_owned": True,
            "automatic_activation": False,
        },
        "automatic_activation": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Report Solo Fast orchestration tax from canonical representative paired evidence.")
    parser.add_argument("--workspace", default=".")
    parser.add_argument("--baseline-policy", default="chatweb_mcp")
    parser.add_argument("--candidate-policy", action="append", dest="candidate_policies")
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--min-pairs", type=int, default=10)
    parser.add_argument("--min-task-classes", type=int, default=3)
    args = parser.parse_args()
    ledger = OrchestrationLedger(Path(args.workspace))
    report = orchestration_tax_report(
        ledger,
        baseline_policy=args.baseline_policy,
        candidate_policies=tuple(args.candidate_policies or ("solo_fast",)),
        limit=args.limit,
        min_pairs=args.min_pairs,
        min_task_classes=args.min_task_classes,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
