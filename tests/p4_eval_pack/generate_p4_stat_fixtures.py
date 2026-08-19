from __future__ import annotations

import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SEED = 24042026
R = random.Random(SEED)

TIERS = ["S", "M", "L", "XL"]
FAMILIES = [
    "local_bugfix",
    "api_feature",
    "cross_file_refactor",
    "test_ci_repair",
    "data_schema_migration",
    "concurrency_lifecycle",
    "orchestration_state",
    "performance_resource_boundary",
]
SCOPES = ["localized_symbol", "localized_file", "bounded_multi_file", "cross_subsystem"]
CONF = ["low", "medium", "high"]
ORACLE = ["weak", "moderate", "strong"]
RISK = ["low", "medium", "high"]


def rank(v, values):
    return values.index(v)


def row(case_id, i, outcome, signal_strength=0.0, context_tier=None, family=None):
    context_tier = context_tier or TIERS[i % len(TIERS)]
    family = family or FAMILIES[i % len(FAMILIES)]
    outcome_num = 1 if outcome == "rework_required" else 0

    # Candidate metadata is generated independently by default; signal_strength injects correlation.
    if signal_strength > 0 and R.random() < signal_strength:
        if outcome_num:
            root_conf = R.choice(["low", "medium"])
            oracle = R.choice(["weak", "moderate"])
            risk = R.choice(["medium", "high"])
            scope = R.choice(["bounded_multi_file", "cross_subsystem"])
            underestimate = R.uniform(0.25, 0.65)
        else:
            root_conf = R.choice(["medium", "high"])
            oracle = R.choice(["moderate", "strong"])
            risk = R.choice(["low", "medium"])
            scope = R.choice(["localized_symbol", "localized_file", "bounded_multi_file"])
            underestimate = R.uniform(-0.10, 0.15)
    else:
        root_conf = R.choice(CONF)
        oracle = R.choice(ORACLE)
        risk = R.choice(RISK)
        scope = R.choice(SCOPES)
        underestimate = R.uniform(-0.2, 0.7)

    tier_scale = {"S": 1, "M": 4, "L": 12, "XL": 30}[context_tier]
    est_files = max(1, int(tier_scale * R.uniform(0.8, 1.5)))
    actual_files = max(1, int(est_files / max(0.15, 1 - underestimate)))
    est_lines = max(5, int(est_files * R.uniform(12, 45)))
    actual_lines = max(5, int(est_lines / max(0.15, 1 - underestimate)))
    est_symbols = max(1, int(est_files * R.uniform(1.0, 2.5)))
    actual_symbols = max(1, int(est_symbols / max(0.15, 1 - underestimate)))

    return {
        "case_id": case_id,
        "row_id": f"{case_id}-{i:05d}",
        "source_class": "synthetic_benchmark",
        "promotion_eligible": False,
        "observed_order": i,
        "context_tier": context_tier,
        "task_family": family,
        "workspace_identity": "isolated-p4-fixture",
        "measurement_epoch": "fixture-v1",
        "run_id": f"fixture-run-{case_id}-{i:05d}",
        "wave_id": f"fixture-wave-{case_id}-{i:05d}",
        "solution_shadow": {
            "candidate_solution_scope": scope,
            "estimated_touched_surface": {
                "files": est_files,
                "lines": est_lines,
                "symbols": est_symbols,
            },
            "root_cause_confidence": root_conf,
            "oracle_strength": oracle,
            "expected_repair_risk": risk,
            "smallest_causal_solution": {
                "scope": scope,
                "estimated_touched_surface": {
                    "files": max(1, int(est_files * 0.7)),
                    "lines": max(5, int(est_lines * 0.7)),
                    "symbols": max(1, int(est_symbols * 0.7)),
                },
            },
            "recorded_before_first_write": True,
        },
        "actual_touched_surface": {
            "files": actual_files,
            "lines": actual_lines,
            "symbols": actual_symbols,
        },
        "derived_candidate_signals": {
            "root_confidence_rank": rank(root_conf, CONF),
            "oracle_strength_rank": rank(oracle, ORACLE),
            "expected_repair_risk_rank": rank(risk, RISK),
            "surface_underestimate_ratio": max(-1.0, min(1.0, 1 - (est_lines / max(1, actual_lines)))),
            "scope_rank": SCOPES.index(scope),
        },
        "outcome": {
            "class": outcome,
            "first_pass_accepted": not outcome_num,
            "rework_required": bool(outcome_num),
            "replan_count": 1 if outcome_num else 0,
            "failure_event_count": 1 if outcome_num else 0,
        },
        "proof": {"passed": True, "lineage_owned": True},
        "quality_outcome": {
            "oracle_pass": True,
            "regression_escape": False,
            "rollback_required": False,
            "manual_fix_required": bool(outcome_num),
            "maintainability_gate": "pass",
        },
        "duplicate_of": None,
        "leakage_features": {},
    }


def balanced_outcomes(n):
    return ["first_pass_accepted" if i % 2 == 0 else "rework_required" for i in range(n)]


def shuffled_outcomes(n):
    vals = balanced_outcomes(n)
    R.shuffle(vals)
    return vals


def make_case(case_id):
    rows = []
    if case_id == "S001":
        return rows
    if case_id == "S002":
        return [row(case_id, i, "rework_required") for i in range(160)]
    if case_id == "S003":
        return [row(case_id, i, "first_pass_accepted") for i in range(160)]
    if case_id == "S004":
        return [row(case_id, i, o) for i, o in enumerate(balanced_outcomes(12))]
    if case_id == "S005":
        return [row(case_id, i, o, signal_strength=0.0) for i, o in enumerate(shuffled_outcomes(512))]
    if case_id == "S006":
        return [row(case_id, i, o, signal_strength=0.90) for i, o in enumerate(shuffled_outcomes(512))]
    if case_id == "S007":
        base = [row(case_id, i, o, signal_strength=0.75) for i, o in enumerate(shuffled_outcomes(64))]
        out = list(base)
        next_id = len(base)
        for copy_idx in range(7):
            for src in base:
                dup = json.loads(json.dumps(src))
                dup["row_id"] = f"{case_id}-{next_id:05d}"
                dup["observed_order"] = next_id
                dup["duplicate_of"] = src["row_id"]
                out.append(dup)
                next_id += 1
        return out
    if case_id == "S008":
        out = [row(case_id, i, o, signal_strength=0.0) for i, o in enumerate(shuffled_outcomes(384))]
        for r in out:
            r["leakage_features"]["future_rework_label"] = 1 if r["outcome"]["rework_required"] else 0
        return out
    if case_id == "S009":
        # Signal appears useful only because XL is overloaded with rework outcomes.
        for i in range(512):
            tier = TIERS[i % 4]
            p = 0.78 if tier == "XL" else 0.28
            outcome = "rework_required" if R.random() < p else "first_pass_accepted"
            r = row(case_id, i, outcome, signal_strength=0.0, context_tier=tier)
            r["derived_candidate_signals"]["confounded_context_indicator"] = 1 if tier == "XL" else 0
            rows.append(r)
        return rows
    if case_id == "S010":
        # Signal appears useful only because two families have more rework outcomes.
        hot = {"concurrency_lifecycle", "orchestration_state"}
        for i in range(512):
            fam = FAMILIES[i % len(FAMILIES)]
            p = 0.75 if fam in hot else 0.30
            outcome = "rework_required" if R.random() < p else "first_pass_accepted"
            r = row(case_id, i, outcome, signal_strength=0.0, family=fam)
            r["derived_candidate_signals"]["confounded_family_indicator"] = 1 if fam in hot else 0
            rows.append(r)
        return rows
    if case_id == "S011":
        # Same latent risk is predictive for S/M/L, but the emitted candidate signal
        # reverses direction in XL. A robustness evaluator must reject/flag it.
        for i in range(640):
            tier = TIERS[i % 4]
            latent = R.random()
            outcome = "rework_required" if latent > 0.55 else "first_pass_accepted"
            signal_value = (1.0 - latent) if tier == "XL" else latent
            r = row(case_id, i, outcome, signal_strength=0.0, context_tier=tier)
            r["derived_candidate_signals"]["direction_reversal_signal"] = round(signal_value, 6)
            rows.append(r)
        return rows
    if case_id == "S012":
        # Stable signal across time; final 25% is untouched temporal holdout.
        outcomes = shuffled_outcomes(800)
        for i, o in enumerate(outcomes):
            r = row(case_id, i, o, signal_strength=0.82)
            r["split"] = "development" if i < 600 else "temporal_holdout"
            rows.append(r)
        return rows
    raise KeyError(case_id)


def main():
    out_path = ROOT / "p4_statistical_fixtures_v1.jsonl"
    index = {}
    total = 0
    with out_path.open("w", encoding="utf-8") as f:
        for n in range(1, 13):
            case_id = f"S{n:03d}"
            rows = make_case(case_id)
            index[case_id] = {
                "rows": len(rows),
                "promotion_eligible": False,
                "storage": "isolated_temporary_fixture_only",
            }
            for r in rows:
                assert r["promotion_eligible"] is False
                f.write(json.dumps(r, separators=(",", ":")) + "\n")
            total += len(rows)
    (ROOT / "p4_statistical_fixture_index_v1.json").write_text(
        json.dumps({"seed": SEED, "total_rows": total, "cases": index}, indent=2),
        encoding="utf-8",
    )
    print(json.dumps({"total_rows": total, "cases": index}, indent=2))


if __name__ == "__main__":
    main()
