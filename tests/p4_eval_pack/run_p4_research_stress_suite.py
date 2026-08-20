from __future__ import annotations

import argparse
import copy
import json
import math
import random
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable


HERE = Path(__file__).resolve().parent
START = datetime(2026, 1, 1, tzinfo=timezone.utc)
LITERATURE = {
    "temporal_validation": {
        "id": "temporally_consistent_validation_2025",
        "topic": "temporal ordering and future-information leakage",
    },
    "jit_delay": {
        "id": "jit_sdp_verification_latency",
        "topic": "delayed defect labels and verification latency",
    },
    "imbalance": {
        "id": "saito_rehmsmeier_2015_pr_imbalance",
        "topic": "precision-recall evaluation under severe class imbalance",
    },
    "noisy_labels": {
        "id": "olmin_lindsten_2022_noisy_labels",
        "topic": "robustness and reliability under label noise",
    },
    "local_calibration": {
        "id": "luo_et_al_2022_local_calibration",
        "topic": "average calibration can hide local miscalibration",
    },
    "spurious_shift": {
        "id": "zhou_et_al_2021_spurious_shift",
        "topic": "spurious features under distribution shift",
    },
    "temporal_shift": {
        "id": "han_huang_wang_2024_temporal_shift",
        "topic": "model assessment under temporal distribution shift",
    },
    "multiple_comparisons": {
        "id": "demsar_2006_multiple_datasets",
        "topic": "multiple comparisons and robust comparative evaluation",
    },
}


def find_repo_root(start: Path) -> Path | None:
    for candidate in (start, *start.parents):
        if (candidate / "resources" / "coding-tools-mcp" / "scripts" / "report_p4_readiness.py").is_file():
            return candidate
    return None


def event_time(index: int) -> str:
    return (START + timedelta(minutes=index)).isoformat().replace("+00:00", "Z")


def row(
    index: int,
    *,
    risk: str,
    repaired: bool | None,
    task_class: str = "bugfix",
    source_epoch: str = "epoch-a",
    stress_group: str = "group-a",
    run_id: str | None = None,
) -> dict[str, Any]:
    return {
        "run_id": run_id or f"synthetic-{index:06d}",
        "task_class": task_class,
        "stress_group": stress_group,
        "evidence_provenance": "synthetic",
        "source_class": "synthetic_benchmark",
        "promotion_eligible": False,
        "source_state": {
            "base_head_identities": [source_epoch],
            "worktree_fingerprint_identities": [f"wt-{source_epoch}"],
        },
        "recommendation": {
            "candidate_solution_scope": "localized_file",
            "root_cause_confidence": "high",
            "oracle_strength": "strong",
            "expected_repair_risk": risk,
            "smallest_causal_solution": {"scope": "localized_symbol"},
            "event_time": event_time(index),
        },
        "outcome": {
            "final": True,
            "repair": {
                "repaired": repaired,
                "causal_solution_repair": repaired,
            },
        },
    }


def repaired_label(item: dict[str, Any]) -> int | None:
    repair = (item.get("outcome") or {}).get("repair") if isinstance(item.get("outcome"), dict) else {}
    value = repair.get("causal_solution_repair") if isinstance(repair, dict) else None
    return 1 if value is True else 0 if value is False else None


def risk_value(item: dict[str, Any]) -> str:
    recommendation = item.get("recommendation") if isinstance(item.get("recommendation"), dict) else {}
    return str(recommendation.get("expected_repair_risk") or "unknown")


def stable_rows(count: int = 240) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index in range(count):
        repaired = (index // 2) % 2 == 1
        rows.append(row(
            index,
            risk="high" if repaired else "low",
            repaired=repaired,
            task_class="bugfix" if index % 2 == 0 else "feature",
            source_epoch=f"epoch-{index % 3}",
            stress_group=f"group-{index % 4}",
        ))
    return rows


def null_rows(count: int = 320) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index in range(count):
        risk = "high" if index % 2 else "low"
        repaired = ((index * 37) % 100) < 50
        rows.append(row(
            index,
            risk=risk,
            repaired=repaired,
            task_class="bugfix" if (index // 2) % 2 == 0 else "feature",
            source_epoch=f"epoch-{index % 3}",
            stress_group=f"group-{index % 4}",
        ))
    return rows


def mild_rows(per_bucket: int = 100) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    bucket_seen = {"low": 0, "high": 0}
    for index in range(per_bucket * 2):
        risk = "high" if index % 2 else "low"
        ordinal = bucket_seen[risk]
        bucket_seen[risk] += 1
        rate = 58 if risk == "high" else 42
        repaired = ((ordinal * 37) % 100) < rate
        rows.append(row(
            index,
            risk=risk,
            repaired=repaired,
            task_class="bugfix" if (index // 2) % 2 == 0 else "feature",
            source_epoch=f"epoch-{index % 3}",
            stress_group=f"group-{index % 4}",
        ))
    return rows


def rare_positive_rows(count: int = 2000, *, signal: bool) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    high_seen = 0
    for index in range(count):
        block = index // 20
        high_offset = block % 4
        is_high = index % 20 == high_offset
        if is_high:
            ordinal = high_seen
            high_seen += 1
            repaired = ordinal % 10 < 4
        else:
            repaired = False
        if signal:
            risk = "high" if is_high else "low"
        else:
            risk = "high" if index % 2 else "low"
        rows.append(row(
            index,
            risk=risk,
            repaired=repaired,
            task_class="bugfix" if index % 2 == 0 else "feature",
            source_epoch=f"epoch-{index % 4}",
            stress_group=f"group-{index % 5}",
        ))
    return rows


def family_proxy_rows(count: int = 240) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index in range(count):
        task_class = "feature" if index % 2 else "bugfix"
        repaired = task_class == "feature"
        rows.append(row(index, risk="high" if repaired else "low", repaired=repaired, task_class=task_class))
    return rows


def late_reversal_rows(count: int = 360) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    split = (count * 2) // 3
    for index in range(count):
        repaired = (index // 2) % 2 == 1
        aligned = "high" if repaired else "low"
        risk = aligned if index < split else ("low" if repaired else "high")
        rows.append(row(index, risk=risk, repaired=repaired, task_class="bugfix" if index % 2 == 0 else "feature"))
    return rows


def sequential_source_proxy_rows(count: int = 360) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    split = (count * 2) // 3
    for index in range(count):
        late = index >= split
        repaired = late
        rows.append(row(
            index,
            risk="high" if late else "low",
            repaired=repaired,
            task_class="bugfix" if index % 2 == 0 else "feature",
            source_epoch="epoch-late" if late else "epoch-early",
        ))
    return rows


def interleaved_source_proxy_rows(count: int = 320) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index in range(count):
        epoch_b = index % 2 == 1
        repaired = epoch_b
        rows.append(row(
            index,
            risk="high" if repaired else "low",
            repaired=repaired,
            task_class="bugfix" if (index // 2) % 2 == 0 else "feature",
            source_epoch="epoch-b" if epoch_b else "epoch-a",
            stress_group=f"group-{(index // 4) % 3}",
        ))
    return rows


def stable_cross_source_rows(count: int = 320) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index in range(count):
        repaired = (index // 2) % 2 == 1
        rows.append(row(
            index,
            risk="high" if repaired else "low",
            repaired=repaired,
            task_class="bugfix" if index % 2 == 0 else "feature",
            source_epoch=f"epoch-{(index // 4) % 4}",
            stress_group=f"group-{(index // 4) % 4}",
        ))
    return rows


def recurrent_middle_drift_rows(count: int = 600) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    reverse_start = count // 3
    reverse_end = reverse_start + count // 10
    for index in range(count):
        repaired = (index // 2) % 2 == 1
        reversed_window = reverse_start <= index < reverse_end
        risk = ("low" if repaired else "high") if reversed_window else ("high" if repaired else "low")
        rows.append(row(
            index,
            risk=risk,
            repaired=repaired,
            task_class="bugfix" if index % 2 == 0 else "feature",
            source_epoch=f"epoch-{index % 4}",
            stress_group=f"group-{index % 5}",
        ))
    return rows


def simpson_rows(count: int = 500) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: dict[tuple[str, str], int] = defaultdict(int)
    group_seen = defaultdict(int)
    for index in range(count):
        group = "group-b" if index % 5 == 0 else "group-a"
        ordinal_group = group_seen[group]
        group_seen[group] += 1
        if group == "group-a":
            risk = "low" if ordinal_group % 5 == 0 else "high"
            rate = 70 if risk == "low" else 60
        else:
            risk = "high" if ordinal_group % 5 == 0 else "low"
            rate = 10 if risk == "high" else 20
        key = (group, risk)
        ordinal = seen[key]
        seen[key] += 1
        repaired = ((ordinal * 37) % 100) < rate
        rows.append(row(
            index,
            risk=risk,
            repaired=repaired,
            task_class="bugfix" if index % 2 == 0 else "feature",
            source_epoch=f"epoch-{index % 3}",
            stress_group=group,
        ))
    return rows


def noisy_rows(flip_percent: int, count: int = 800) -> list[dict[str, Any]]:
    rows = stable_rows(count)
    for index, item in enumerate(rows):
        label = repaired_label(item)
        if label is not None and ((index * 37) % 100) < flip_percent:
            flipped = not bool(label)
            item["outcome"]["repair"]["repaired"] = flipped
            item["outcome"]["repair"]["causal_solution_repair"] = flipped
    return rows


def prevalence_shift_rows(count: int = 900) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: dict[tuple[str, str], int] = defaultdict(int)
    for index in range(count):
        late = index >= (count * 2) // 3
        risk = "high" if index % 2 else "low"
        rates = {"high": 70, "low": 25} if late else {"high": 25, "low": 5}
        key = ("late" if late else "early", risk)
        ordinal = seen[key]
        seen[key] += 1
        repaired = ((ordinal * 37) % 100) < rates[risk]
        rows.append(row(
            index,
            risk=risk,
            repaired=repaired,
            task_class="bugfix" if (index // 2) % 2 == 0 else "feature",
            source_epoch=f"epoch-{index % 3}",
            stress_group=f"group-{index % 4}",
        ))
    return rows


def censored_recent(rows: list[dict[str, Any]], recent_count: int) -> list[dict[str, Any]]:
    result = copy.deepcopy(rows)
    for item in result[-recent_count:]:
        item["outcome"]["repair"]["repaired"] = None
        item["outcome"]["repair"]["causal_solution_repair"] = None
    return result


def late_materialized_reversal(count: int = 480, recent_count: int = 120) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    mature = stable_rows(count)
    materialized = copy.deepcopy(mature)
    for item in materialized[-recent_count:]:
        label = repaired_label(item)
        if label is not None:
            flipped = not bool(label)
            item["outcome"]["repair"]["repaired"] = flipped
            item["outcome"]["repair"]["causal_solution_repair"] = flipped
            item["recommendation"]["expected_repair_risk"] = "high" if not flipped else "low"
    return censored_recent(materialized, recent_count), materialized


def reporter(repo_root: Path) -> dict[str, Any]:
    script = repo_root / "resources" / "coding-tools-mcp" / "scripts" / "report_p4_readiness.py"
    proc = subprocess.run([sys.executable, str(script), "--workspace", str(repo_root)], cwd=repo_root, text=True, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(f"canonical reporter failed: {(proc.stderr or '')[-1000:]}")
    return json.loads(proc.stdout)


def snapshot(report: dict[str, Any]) -> dict[str, Any]:
    gate = report.get("p4_gate") if isinstance(report.get("p4_gate"), dict) else {}
    validation = report.get("predictive_validation") if isinstance(report.get("predictive_validation"), dict) else {}
    return {
        "state": report.get("state"),
        "p4_gate_status": gate.get("status"),
        "p4_can_answer": gate.get("can_answer_which_signals_predict_repair"),
        "validated_signals": validation.get("validated_signals"),
        "p4_empirically_complete": report.get("p4_empirically_complete"),
        "p5_controlled_treatment_may_be_opened": report.get("p5_controlled_treatment_may_be_opened"),
        "p5_automatic_start": report.get("p5_automatic_start"),
        "automatic_policy_activation": report.get("automatic_policy_activation"),
    }


def signal_detail(validation: dict[str, Any]) -> dict[str, Any]:
    return validation["signals"]["expected_repair_risk"]


def is_valid(validation: dict[str, Any]) -> bool:
    return "expected_repair_risk" in validation.get("validated_signals", [])


def brier_holdout(training: list[dict[str, Any]], held: list[dict[str, Any]]) -> dict[str, Any]:
    train = [(item, repaired_label(item)) for item in training]
    train = [(item, label) for item, label in train if label is not None]
    test = [(item, repaired_label(item)) for item in held]
    test = [(item, label) for item, label in test if label is not None]
    if len(train) < 2 or not test or len({label for _, label in train}) < 2 or len({label for _, label in test}) < 2:
        return {"evaluable": False, "gain": None, "samples": len(test)}
    baseline_p = sum(label for _, label in train) / len(train)
    buckets: dict[str, list[int]] = defaultdict(list)
    for item, label in train:
        buckets[risk_value(item)].append(label)
    baseline = 0.0
    model = 0.0
    for item, label in test:
        outcomes = buckets.get(risk_value(item), [])
        probability = sum(outcomes) / len(outcomes) if outcomes else baseline_p
        baseline += (baseline_p - label) ** 2
        model += (probability - label) ** 2
    return {
        "evaluable": True,
        "gain": round((baseline - model) / len(test), 6),
        "samples": len(test),
    }


def grouped_holdout(rows: list[dict[str, Any]], key: Callable[[dict[str, Any]], str]) -> dict[str, Any]:
    groups = sorted({key(item) for item in rows if key(item)})
    details: dict[str, Any] = {}
    gains: list[float] = []
    for group in groups:
        training = [item for item in rows if key(item) != group]
        held = [item for item in rows if key(item) == group]
        result = brier_holdout(training, held)
        details[group] = result
        if result["evaluable"]:
            gains.append(float(result["gain"]))
    return {
        "group_count": len(groups),
        "evaluable_groups": len(gains),
        "min_gain": round(min(gains), 6) if gains else None,
        "mean_gain": round(sum(gains) / len(gains), 6) if gains else None,
        "groups": details,
    }


def source_epoch(item: dict[str, Any]) -> str:
    state = item.get("source_state") if isinstance(item.get("source_state"), dict) else {}
    heads = state.get("base_head_identities") if isinstance(state.get("base_head_identities"), list) else []
    return str(heads[0]) if len(heads) == 1 else ""


def rolling_temporal(rows: list[dict[str, Any]], blocks: int = 10) -> dict[str, Any]:
    ordered = sorted(rows, key=lambda item: str((item.get("recommendation") or {}).get("event_time") or ""))
    size = max(1, len(ordered) // blocks)
    gains: list[float] = []
    details: list[dict[str, Any]] = []
    for block in range(2, blocks):
        start = block * size
        end = len(ordered) if block == blocks - 1 else min(len(ordered), (block + 1) * size)
        if start >= len(ordered):
            break
        result = brier_holdout(ordered[:start], ordered[start:end])
        details.append({"block": block, **result})
        if result["evaluable"]:
            gains.append(float(result["gain"]))
    return {
        "evaluable_blocks": len(gains),
        "min_gain": round(min(gains), 6) if gains else None,
        "mean_gain": round(sum(gains) / len(gains), 6) if gains else None,
        "blocks": details,
    }


def oos_bucket_diagnostics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(rows, key=lambda item: str((item.get("recommendation") or {}).get("event_time") or ""))
    split = (len(ordered) * 2) // 3
    train = [(item, repaired_label(item)) for item in ordered[:split]]
    train = [(item, label) for item, label in train if label is not None]
    test = [(item, repaired_label(item)) for item in ordered[split:]]
    test = [(item, label) for item, label in test if label is not None]
    buckets: dict[str, list[int]] = defaultdict(list)
    for item, label in train:
        buckets[risk_value(item)].append(label)
    scored: list[tuple[float, int, str]] = []
    for item, label in test:
        outcomes = buckets.get(risk_value(item), [])
        if not outcomes:
            continue
        scored.append((sum(outcomes) / len(outcomes), label, str(item.get("stress_group") or "")))
    if not scored:
        return {"evaluable": False}
    by_score: dict[float, list[int]] = defaultdict(list)
    by_group: dict[str, list[tuple[float, int]]] = defaultdict(list)
    for score, label, group in scored:
        by_score[score].append(label)
        by_group[group].append((score, label))
    ece = sum(len(labels) * abs(score - sum(labels) / len(labels)) for score, labels in by_score.items()) / len(scored)
    group_errors = {}
    for group, values in by_group.items():
        group_errors[group] = round(sum(abs(score - label) for score, label in values) / len(values), 6)
    ranked = sorted(scored, key=lambda item: item[0], reverse=True)
    positives = sum(label for _, label, _ in ranked)
    true_seen = 0
    ap_sum = 0.0
    for rank, (_, label, _) in enumerate(ranked, start=1):
        if label:
            true_seen += 1
            ap_sum += true_seen / rank
    ap = ap_sum / positives if positives else 0.0
    prevalence = positives / len(ranked)
    return {
        "evaluable": True,
        "samples": len(scored),
        "ece": round(ece, 6),
        "average_precision": round(ap, 6),
        "prevalence": round(prevalence, 6),
        "ap_lift_over_prevalence": round(ap - prevalence, 6),
        "worst_group_absolute_error": max(group_errors.values()) if group_errors else None,
        "group_absolute_errors": group_errors,
        "probability_semantics": "out_of_sample_empirical_bucket_probability_not_native_ordinal_probability",
    }


def add_case(cases: list[dict[str, Any]], *, case_id: str, layer: str, literature: list[str], passed: bool, observed: Any, expected: Any, severity: str = "gate") -> None:
    cases.append({
        "id": case_id,
        "layer": layer,
        "literature": literature,
        "severity": severity,
        "status": "PASS" if passed else "FAIL",
        "expected": expected,
        "observed": observed,
    })


def main() -> int:
    parser = argparse.ArgumentParser(description="Research-driven, non-promoting P4 stress suite.")
    parser.add_argument("--repo-root", type=Path, default=None)
    args = parser.parse_args()
    repo_root = args.repo_root.resolve() if args.repo_root else find_repo_root(HERE)
    if repo_root is None:
        raise SystemExit("repository root was not found")
    sys.path.insert(0, str(repo_root / "resources" / "coding-tools-mcp"))
    from coding_tools_mcp.solution_economics import _predictive_validation  # type: ignore

    before = reporter(repo_root)
    cases: list[dict[str, Any]] = []
    blind_spots: list[str] = []

    stable = stable_rows()
    stable_v = _predictive_validation(stable)
    null = null_rows()
    null_v = _predictive_validation(null)
    mild = mild_rows()
    mild_v = _predictive_validation(mild)

    add_case(cases, case_id="I01_stable_signal_recovers", layer="integrity", literature=["multiple_comparisons"], passed=is_valid(stable_v), observed=is_valid(stable_v), expected=True)
    add_case(cases, case_id="I02_balanced_null_rejected", layer="integrity", literature=["multiple_comparisons"], passed=not is_valid(null_v), observed=is_valid(null_v), expected=False)
    unknown = stable + [row(10000 + i, risk="high", repaired=None, task_class="feature") for i in range(80)]
    unknown_v = _predictive_validation(unknown)
    add_case(cases, case_id="I03_unknown_labels_not_zero", layer="integrity", literature=["jit_delay"], passed=unknown_v["representative_terminal_outcomes"] == stable_v["representative_terminal_outcomes"], observed=unknown_v["representative_terminal_outcomes"], expected=stable_v["representative_terminal_outcomes"])
    permuted = copy.deepcopy(stable)
    random.Random(71231).shuffle(permuted)
    permuted_v = _predictive_validation(permuted)
    add_case(cases, case_id="I04_row_permutation_invariant", layer="integrity", literature=["temporal_validation"], passed=permuted_v == stable_v, observed=permuted_v == stable_v, expected=True)
    add_case(cases, case_id="I05_mild_effect_needs_interval_separation", layer="statistics", literature=["multiple_comparisons"], passed=(signal_detail(mild_v)["leave_one_out_brier_gain"] > 0 and not is_valid(mild_v) and not signal_detail(mild_v)["separated_bucket_pairs"]), observed={"valid": is_valid(mild_v), "gain": signal_detail(mild_v)["leave_one_out_brier_gain"], "pairs": signal_detail(mild_v)["separated_bucket_pairs"]}, expected="positive_gain_but_unvalidated_without_separation")
    add_case(cases, case_id="I06_low_variance_rejected", layer="integrity", literature=["multiple_comparisons"], passed=not is_valid(_predictive_validation([row(i, risk="low", repaired=(i % 2 == 0), task_class="bugfix" if i % 3 else "feature") for i in range(240)])), observed="evaluated", expected="reject_single_bucket")

    family_v = _predictive_validation(family_proxy_rows())
    add_case(cases, case_id="G01_task_class_proxy_rejected", layer="group_robustness", literature=["spurious_shift"], passed=not is_valid(family_v), observed=is_valid(family_v), expected=False)
    source_seq_v = _predictive_validation(sequential_source_proxy_rows())
    add_case(cases, case_id="G02_sequential_source_proxy_rejected", layer="source_state", literature=["temporal_validation", "spurious_shift"], passed=not is_valid(source_seq_v), observed=is_valid(source_seq_v), expected=False)
    source_interleaved = interleaved_source_proxy_rows()
    source_interleaved_v = _predictive_validation(source_interleaved)
    source_diag = grouped_holdout(source_interleaved, source_epoch)
    source_proxy_pass = not is_valid(source_interleaved_v)
    add_case(cases, case_id="G03_interleaved_source_epoch_proxy_rejected", layer="source_state", literature=["spurious_shift", "temporal_shift"], passed=source_proxy_pass, observed={"canonical_valid": is_valid(source_interleaved_v), "source_holdout": source_diag}, expected="canonical_reject_without_cross_source_support")
    if not source_proxy_pass:
        blind_spots.append("source_epoch_proxy_can_pass_without_cross_source_generalization")
    cross_source = stable_cross_source_rows()
    cross_source_v = _predictive_validation(cross_source)
    cross_source_diag = grouped_holdout(cross_source, source_epoch)
    add_case(cases, case_id="G04_cross_source_stable_signal_recovers", layer="source_state", literature=["temporal_shift"], passed=is_valid(cross_source_v) and (cross_source_diag["min_gain"] or 0) > 0, observed={"canonical_valid": is_valid(cross_source_v), "source_holdout": cross_source_diag}, expected="accept_and_positive_cross_source_gain")

    simpson = simpson_rows()
    simpson_v = _predictive_validation(simpson)
    simpson_diag = grouped_holdout(simpson, lambda item: str(item.get("stress_group") or ""))
    simpson_pass = not is_valid(simpson_v)
    add_case(cases, case_id="G05_simpson_subgroup_reversal_rejected", layer="group_robustness", literature=["spurious_shift", "local_calibration"], passed=simpson_pass, observed={"canonical_valid": is_valid(simpson_v), "subgroup_holdout": simpson_diag}, expected="reject_pooled_signal_with_within_group_reversal")
    if not simpson_pass:
        blind_spots.append("pooled_signal_can_hide_subgroup_reversal")
    subgroup_cal = oos_bucket_diagnostics(simpson)
    add_case(cases, case_id="G06_local_reliability_diagnostic_exposed", layer="calibration", literature=["local_calibration"], passed=subgroup_cal.get("evaluable") is True and subgroup_cal.get("worst_group_absolute_error", 0) > 0.25, observed=subgroup_cal, expected="detect_large_local_error", severity="diagnostic")

    late = late_reversal_rows()
    late_v = _predictive_validation(late)
    add_case(cases, case_id="T01_late_direction_reversal_rejected", layer="temporal", literature=["temporal_validation", "temporal_shift"], passed=not is_valid(late_v), observed=is_valid(late_v), expected=False)
    recurrent = recurrent_middle_drift_rows()
    recurrent_v = _predictive_validation(recurrent)
    recurrent_diag = rolling_temporal(recurrent)
    recurrent_should_reject = not is_valid(recurrent_v)
    add_case(cases, case_id="T02_recurrent_middle_drift_rejected", layer="temporal", literature=["temporal_shift"], passed=recurrent_should_reject, observed={"canonical_valid": is_valid(recurrent_v), "rolling": recurrent_diag}, expected="reject_if_any_material_rolling_window_reverses")
    if not recurrent_should_reject:
        blind_spots.append("single_latest_third_holdout_can_miss_recurrent_middle_drift")
    stable_roll = rolling_temporal(stable_rows(600))
    add_case(cases, case_id="T03_stable_rolling_windows_positive", layer="temporal", literature=["temporal_shift"], passed=stable_roll["evaluable_blocks"] >= 4 and (stable_roll["min_gain"] or 0) > 0, observed=stable_roll, expected="multiple_positive_rolling_windows")
    censored, materialized = late_materialized_reversal()
    censored_v = _predictive_validation(censored)
    materialized_v = _predictive_validation(materialized)
    add_case(cases, case_id="T04_recent_censored_labels_excluded", layer="temporal", literature=["jit_delay"], passed=censored_v["representative_terminal_outcomes"] == len(censored) - 120, observed=censored_v["representative_terminal_outcomes"], expected=len(censored) - 120)
    add_case(cases, case_id="T05_late_label_maturation_can_change_decision", layer="temporal", literature=["jit_delay", "temporal_validation"], passed=is_valid(censored_v) and not is_valid(materialized_v), observed={"before_maturation": is_valid(censored_v), "after_maturation": is_valid(materialized_v)}, expected={"before_maturation": True, "after_maturation": False}, severity="diagnostic")
    add_case(cases, case_id="T06_event_time_drives_order_not_input_order", layer="temporal", literature=["temporal_validation"], passed=_predictive_validation(list(reversed(stable))) == stable_v, observed="compared", expected="identical")

    rare_signal = rare_positive_rows(signal=True)
    rare_signal_v = _predictive_validation(rare_signal)
    rare_null = rare_positive_rows(signal=False)
    rare_null_v = _predictive_validation(rare_null)
    add_case(cases, case_id="S01_rare_positive_strong_signal_recovers", layer="imbalance", literature=["imbalance"], passed=is_valid(rare_signal_v), observed={"valid": is_valid(rare_signal_v), "positive_count": sum(repaired_label(item) or 0 for item in rare_signal)}, expected="validated_despite_rare_positive_class")
    add_case(cases, case_id="S02_rare_positive_null_rejected", layer="imbalance", literature=["imbalance"], passed=not is_valid(rare_null_v), observed=is_valid(rare_null_v), expected=False)
    rare_pr = oos_bucket_diagnostics(rare_signal)
    add_case(cases, case_id="S03_pr_diagnostic_has_lift", layer="imbalance", literature=["imbalance"], passed=rare_pr.get("evaluable") is True and rare_pr.get("ap_lift_over_prevalence", 0) > 0.15, observed=rare_pr, expected="average_precision_materially_above_prevalence", severity="diagnostic")
    rare_null_pr = oos_bucket_diagnostics(rare_null)
    add_case(cases, case_id="S04_pr_null_has_little_lift", layer="imbalance", literature=["imbalance"], passed=rare_null_pr.get("evaluable") is True and rare_null_pr.get("ap_lift_over_prevalence", 1) < 0.05, observed=rare_null_pr, expected="average_precision_near_prevalence", severity="diagnostic")
    add_case(cases, case_id="S05_noisy_labels_5pct_remain_directional", layer="label_noise", literature=["noisy_labels"], passed=is_valid(_predictive_validation(noisy_rows(5))), observed="evaluated", expected="strong_signal_survives_small_symmetric_noise", severity="diagnostic")
    noisy30 = _predictive_validation(noisy_rows(30))
    add_case(cases, case_id="S06_noisy_labels_30pct_report_weaker_gain", layer="label_noise", literature=["noisy_labels"], passed=(signal_detail(noisy30)["leave_one_out_brier_gain"] or 0) < signal_detail(stable_v)["leave_one_out_brier_gain"], observed={"noisy_gain": signal_detail(noisy30)["leave_one_out_brier_gain"], "clean_gain": signal_detail(stable_v)["leave_one_out_brier_gain"]}, expected="gain_degrades_under_heavy_noise", severity="diagnostic")

    duplicated = []
    for replica in range(4):
        for item in mild:
            duplicated.append(copy.deepcopy(item))
    duplicated_v = _predictive_validation(duplicated)
    duplicate_pass = is_valid(duplicated_v) == is_valid(mild_v)
    add_case(cases, case_id="M01_exact_duplicate_support_cannot_promote", layer="metamorphic", literature=["multiple_comparisons"], passed=duplicate_pass, observed={"original_valid": is_valid(mild_v), "duplicated_valid": is_valid(duplicated_v), "original_n": len(mild), "duplicated_n": len(duplicated)}, expected="same_validation_decision")
    if not duplicate_pass:
        blind_spots.append("exact_duplicate_rows_can_inflate_support_and_change_promotion_decision")
    unknown_augmented = copy.deepcopy(mild) + [row(20000 + i, risk="high", repaired=None) for i in range(500)]
    unknown_aug_v = _predictive_validation(unknown_augmented)
    add_case(cases, case_id="M02_unknown_label_injection_invariant", layer="metamorphic", literature=["jit_delay"], passed=unknown_aug_v == mild_v, observed=unknown_aug_v == mild_v, expected=True)
    label_shuffle = copy.deepcopy(stable)
    labels = [repaired_label(item) for item in label_shuffle]
    random.Random(8021).shuffle(labels)
    for item, label in zip(label_shuffle, labels):
        value = bool(label)
        item["outcome"]["repair"]["repaired"] = value
        item["outcome"]["repair"]["causal_solution_repair"] = value
    shuffled_v = _predictive_validation(label_shuffle)
    add_case(cases, case_id="M03_label_permutation_null_rejected", layer="metamorphic", literature=["multiple_comparisons"], passed=not is_valid(shuffled_v), observed=is_valid(shuffled_v), expected=False)
    prevalence = prevalence_shift_rows()
    prevalence_v = _predictive_validation(prevalence)
    prevalence_diag = oos_bucket_diagnostics(prevalence)
    add_case(cases, case_id="M04_prevalence_shift_keeps_discrimination_diagnostic", layer="distribution_shift", literature=["imbalance", "temporal_shift"], passed=(signal_detail(prevalence_v)["leave_one_out_brier_gain"] or 0) > 0, observed={"valid": is_valid(prevalence_v), "diagnostic": prevalence_diag}, expected="positive_discrimination_even_if_calibration_drifts", severity="diagnostic")
    add_case(cases, case_id="M05_prevalence_shift_calibration_drift_detected", layer="calibration", literature=["local_calibration", "temporal_shift"], passed=prevalence_diag.get("evaluable") is True and prevalence_diag.get("ece", 0) > 0.05, observed=prevalence_diag, expected="nontrivial_oos_empirical_bucket_calibration_error", severity="diagnostic")
    clean_cal = oos_bucket_diagnostics(stable)
    add_case(cases, case_id="M06_clean_empirical_bucket_calibration", layer="calibration", literature=["local_calibration"], passed=clean_cal.get("evaluable") is True and clean_cal.get("ece", 1) < 0.02, observed=clean_cal, expected="low_empirical_bucket_ece", severity="diagnostic")

    add_case(cases, case_id="R01_bonferroni_alpha_contract", layer="statistics", literature=["multiple_comparisons"], passed=stable_v.get("per_comparison_alpha") is not None and stable_v.get("per_comparison_alpha") <= 0.05, observed=stable_v.get("per_comparison_alpha"), expected="<=0.05")
    add_case(cases, case_id="R02_causal_claim_remains_forbidden", layer="governance", literature=["spurious_shift"], passed=stable_v.get("causal_claim_allowed") is False, observed=stable_v.get("causal_claim_allowed"), expected=False)
    add_case(cases, case_id="R03_benchmark_rows_explicitly_nonpromoting", layer="governance", literature=[], passed=all(item.get("promotion_eligible") is False and item.get("source_class") == "synthetic_benchmark" for item in stable + mild + null), observed="checked", expected="all_false_and_synthetic_benchmark")

    after = reporter(repo_root)
    before_snapshot = snapshot(before)
    after_snapshot = snapshot(after)
    add_case(cases, case_id="R04_canonical_before_after_noninterference", layer="governance", literature=[], passed=before_snapshot == after_snapshot, observed={"before": before_snapshot, "after": after_snapshot}, expected="identical")
    add_case(cases, case_id="R05_benchmark_cannot_start_p5", layer="governance", literature=[], passed=after_snapshot["p5_automatic_start"] is False and after_snapshot["automatic_policy_activation"] is False, observed=after_snapshot, expected="automatic_activation_false")

    layer_counts: dict[str, dict[str, int]] = defaultdict(lambda: {"pass": 0, "fail": 0})
    for case in cases:
        layer_counts[case["layer"]]["pass" if case["status"] == "PASS" else "fail"] += 1
    failures = [case for case in cases if case["status"] == "FAIL"]
    result = {
        "schema_version": 1,
        "runner": "p4-research-stress-suite-v1",
        "status": "PASS" if not failures else "FAIL",
        "research_use": "literature_inspired_failure_mechanisms_not_direct_prescriptions_for_p4",
        "evidence_policy": {
            "source_class": "synthetic_benchmark",
            "promotion_eligible": False,
            "canonical_mutation_allowed": False,
            "p5_automatic_start": False,
            "automatic_policy_activation": False,
        },
        "literature_map": LITERATURE,
        "case_count": len(cases),
        "passed": len(cases) - len(failures),
        "failed": len(failures),
        "layer_counts": dict(sorted(layer_counts.items())),
        "blind_spots": sorted(set(blind_spots)),
        "canonical_before": before_snapshot,
        "canonical_after": after_snapshot,
        "cases": cases,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
