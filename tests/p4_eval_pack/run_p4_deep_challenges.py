from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent


def find_repo_root(start: Path) -> Path | None:
    for candidate in (start, *start.parents):
        if (candidate / "resources" / "coding-tools-mcp" / "scripts" / "report_p4_readiness.py").is_file():
            return candidate
    return None


def synthetic_row(index: int, *, task_class: str, risk: str, repaired: bool | None) -> dict[str, Any]:
    day = 1 + index // 24
    hour = index % 24
    return {
        "task_class": task_class,
        "evidence_provenance": "synthetic",
        "recommendation": {
            "candidate_solution_scope": "localized_file",
            "root_cause_confidence": "high",
            "oracle_strength": "strong",
            "expected_repair_risk": risk,
            "smallest_causal_solution": {"scope": "localized_symbol"},
            "event_time": f"2026-01-{day:02d}T{hour:02d}:00:00Z",
        },
        "outcome": {
            "final": True,
            "repair": {
                "repaired": repaired,
                "causal_solution_repair": repaired,
            },
        },
    }


def stable_rows(count: int = 160) -> list[dict[str, Any]]:
    rows = []
    for index in range(count):
        task_class = "bugfix" if index % 2 == 0 else "feature"
        repaired = (index // 2) % 2 == 1
        rows.append(synthetic_row(
            index,
            task_class=task_class,
            risk="high" if repaired else "low",
            repaired=repaired,
        ))
    return rows


def family_proxy_rows(count: int = 160) -> list[dict[str, Any]]:
    rows = []
    for index in range(count):
        task_class = "bugfix" if index % 2 == 0 else "feature"
        repaired = task_class == "feature"
        rows.append(synthetic_row(
            index,
            task_class=task_class,
            risk="high" if repaired else "low",
            repaired=repaired,
        ))
    return rows


def temporal_reversal_rows() -> list[dict[str, Any]]:
    rows = []
    for index in range(360):
        task_class = "bugfix" if index % 2 == 0 else "feature"
        repaired = (index // 2) % 2 == 1
        aligned = "high" if repaired else "low"
        risk = aligned if index < 240 else "low" if repaired else "high"
        rows.append(synthetic_row(index, task_class=task_class, risk=risk, repaired=repaired))
    return rows


def source_epoch_proxy_rows() -> list[dict[str, Any]]:
    rows = []
    for index in range(180):
        task_class = "bugfix" if index % 2 == 0 else "feature"
        repaired = index >= 120
        rows.append(synthetic_row(
            index,
            task_class=task_class,
            risk="high" if repaired else "low",
            repaired=repaired,
        ))
    return rows


def mild_overlapping_rows() -> list[dict[str, Any]]:
    rows = []
    seen = {"low": 0, "high": 0}
    for index in range(200):
        risk = "high" if index % 2 else "low"
        ordinal = seen[risk]
        seen[risk] += 1
        # 58% vs 42% is deliberately strong enough to improve pooled LOOCV
        # Brier score at n=100 per bucket, while the 95% Wilson intervals
        # still overlap. This isolates the interval-separation gate instead
        # of accidentally failing earlier on non-positive pooled gain.
        repaired = ordinal < (58 if risk == "high" else 42)
        task_class = "bugfix" if (index // 2) % 2 == 0 else "feature"
        rows.append(synthetic_row(index, task_class=task_class, risk=risk, repaired=repaired))
    return rows


def null_rows(count: int = 160) -> list[dict[str, Any]]:
    rows = []
    for index in range(count):
        risk = "high" if index % 2 else "low"
        repaired = (index // 2) % 2 == 1
        task_class = "bugfix" if (index // 4) % 2 == 0 else "feature"
        rows.append(synthetic_row(index, task_class=task_class, risk=risk, repaired=repaired))
    return rows


def low_variance_rows(count: int = 160) -> list[dict[str, Any]]:
    rows = []
    for index in range(count):
        task_class = "bugfix" if index % 2 == 0 else "feature"
        repaired = (index // 2) % 2 == 1
        rows.append(synthetic_row(index, task_class=task_class, risk="low", repaired=repaired))
    return rows


def reporter(repo_root: Path) -> dict[str, Any]:
    script = repo_root / "resources" / "coding-tools-mcp" / "scripts" / "report_p4_readiness.py"
    proc = subprocess.run(
        [sys.executable, str(script), "--workspace", str(repo_root)],
        cwd=repo_root,
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"canonical reporter failed with exit code {proc.returncode}: {(proc.stderr or '')[-1000:]}")
    return json.loads(proc.stdout)


def canonical_snapshot(report: dict[str, Any]) -> dict[str, Any]:
    gate = report.get("p4_gate") if isinstance(report.get("p4_gate"), dict) else {}
    validation = report.get("predictive_validation") if isinstance(report.get("predictive_validation"), dict) else {}
    return {
        "p4_gate_status": gate.get("status"),
        "p4_can_answer": gate.get("can_answer_which_signals_predict_repair"),
        "validated_signals": validation.get("validated_signals"),
        "p4_empirically_complete": report.get("p4_empirically_complete"),
        "p5_baseline_ready": report.get("p5_baseline_ready"),
        "p5_controlled_treatment_may_be_opened": report.get("p5_controlled_treatment_may_be_opened"),
        "p5_automatic_start": report.get("p5_automatic_start"),
        "automatic_policy_activation": report.get("automatic_policy_activation"),
    }


def challenge_result(name: str, validation: dict[str, Any], *, expected_valid: bool, extra_ok: bool = True) -> dict[str, Any]:
    signal = validation["signals"]["expected_repair_risk"]
    observed_valid = "expected_repair_risk" in validation["validated_signals"]
    passed = observed_valid is expected_valid and extra_ok
    return {
        "name": name,
        "status": "PASS" if passed else "FAIL",
        "expected_valid": expected_valid,
        "observed_valid": observed_valid,
        "pooled_predictive_signal": signal["pooled_predictive_signal"],
        "pooled_brier_gain": signal["leave_one_out_brier_gain"],
        "separated_bucket_pairs": signal["separated_bucket_pairs"],
        "task_family_holdout": signal["task_family_holdout"],
        "temporal_holdout": signal["temporal_holdout"],
        "validation_blockers": signal["validation_blockers"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run P4 deep adversarial robustness challenges without promotion evidence writes.")
    parser.add_argument("--repo-root", type=Path, default=None)
    args = parser.parse_args()
    repo_root = args.repo_root.resolve() if args.repo_root else find_repo_root(HERE)
    if repo_root is None:
        raise SystemExit("repository root with canonical P4 reporter was not found")

    sys.path.insert(0, str(repo_root / "resources" / "coding-tools-mcp"))
    from coding_tools_mcp.solution_economics import _predictive_validation  # type: ignore

    before = reporter(repo_root)

    stable = _predictive_validation(stable_rows())
    family_proxy = _predictive_validation(family_proxy_rows())
    temporal_reversal = _predictive_validation(temporal_reversal_rows())
    source_epoch = _predictive_validation(source_epoch_proxy_rows())
    mild = _predictive_validation(mild_overlapping_rows())
    null = _predictive_validation(null_rows())
    low_variance = _predictive_validation(low_variance_rows())
    unknown = _predictive_validation(stable_rows() + [
        synthetic_row(160 + index, task_class="bugfix" if index % 2 == 0 else "feature", risk="high", repaired=None)
        for index in range(40)
    ])

    challenges = [
        challenge_result("stable_cross_family_cross_time_signal", stable, expected_valid=True),
        challenge_result(
            "family_confounded_perfect_pool",
            family_proxy,
            expected_valid=False,
            extra_ok=family_proxy["signals"]["expected_repair_risk"]["pooled_predictive_signal"] is True,
        ),
        challenge_result(
            "late_temporal_direction_reversal",
            temporal_reversal,
            expected_valid=False,
            extra_ok=(
                temporal_reversal["signals"]["expected_repair_risk"]["pooled_predictive_signal"] is True
                and temporal_reversal["signals"]["expected_repair_risk"]["temporal_holdout"]["evaluable"] is True
                and temporal_reversal["signals"]["expected_repair_risk"]["temporal_holdout"]["brier_gain"] < 0
            ),
        ),
        challenge_result("source_epoch_proxy", source_epoch, expected_valid=False),
        challenge_result(
            "positive_brier_without_interval_separation",
            mild,
            expected_valid=False,
            extra_ok=(
                mild["signals"]["expected_repair_risk"]["leave_one_out_brier_gain"] > 0
                and not mild["signals"]["expected_repair_risk"]["separated_bucket_pairs"]
            ),
        ),
        challenge_result("balanced_null_signal", null, expected_valid=False),
        challenge_result("low_variance_single_bucket", low_variance, expected_valid=False),
        challenge_result(
            "unknown_labels_are_not_zero",
            unknown,
            expected_valid=True,
            extra_ok=unknown["representative_terminal_outcomes"] == 160,
        ),
    ]

    after = reporter(repo_root)
    before_snapshot = canonical_snapshot(before)
    after_snapshot = canonical_snapshot(after)
    non_interference = before_snapshot == after_snapshot

    current_validation = before.get("predictive_validation") if isinstance(before.get("predictive_validation"), dict) else {}
    current_signals = current_validation.get("signals") if isinstance(current_validation.get("signals"), dict) else {}
    current_gap = {
        name: {
            "pooled_brier_gain": detail.get("leave_one_out_brier_gain"),
            "separated_bucket_pairs": detail.get("separated_bucket_pairs"),
            "task_family_holdout": detail.get("task_family_holdout"),
            "temporal_holdout": detail.get("temporal_holdout"),
            "validation_blockers": detail.get("validation_blockers"),
        }
        for name, detail in current_signals.items()
        if isinstance(detail, dict)
    }
    transition_target = {
        "p4_gate_status": "predictive_signal_validation_available",
        "p4_can_answer": True,
        "validated_signals": "at_least_one_representative_signal",
        "p4_empirically_complete": True,
        "p5_baseline_ready": True,
        "p5_controlled_treatment_may_be_opened": True,
        "p5_automatic_start": False,
        "automatic_policy_activation": False,
    }
    all_challenges_pass = all(item["status"] == "PASS" for item in challenges)
    result = {
        "schema_version": 1,
        "runner": "p4-deep-challenges-v1",
        "status": "PASS" if all_challenges_pass and non_interference else "FAIL",
        "evidence_policy": {
            "source_class": "synthetic_benchmark",
            "promotion_eligible": False,
            "canonical_mutation_allowed": False,
            "not_a_sample_count_promotion_rehearsal": True,
        },
        "canonical_before": before_snapshot,
        "canonical_after": after_snapshot,
        "canonical_non_interference": "PASS" if non_interference else "FAIL",
        "current_validation_method": current_validation.get("method"),
        "current_signal_gap": current_gap,
        "challenges": challenges,
        "transition_target": transition_target,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
