from __future__ import annotations

import csv
import json
from pathlib import Path
from itertools import product

ROOT = Path(__file__).resolve().parent

CONTEXT_TIERS = {
    "S": {
        "files": [1, 3],
        "relevant_loc": [100, 800],
        "dependency_hops": [0, 1],
        "target_symbols": [1, 4],
        "distractor_ratio": 0.20,
        "description": "Localized context with a small dependency surface.",
    },
    "M": {
        "files": [4, 10],
        "relevant_loc": [800, 4000],
        "dependency_hops": [1, 3],
        "target_symbols": [5, 15],
        "distractor_ratio": 0.40,
        "description": "Subsystem-sized context with multiple related modules.",
    },
    "L": {
        "files": [11, 25],
        "relevant_loc": [4000, 15000],
        "dependency_hops": [2, 5],
        "target_symbols": [16, 45],
        "distractor_ratio": 0.60,
        "description": "Cross-subsystem context with nontrivial localization and proof surface.",
    },
    "XL": {
        "files": [26, 60],
        "relevant_loc": [15000, 50000],
        "dependency_hops": [4, 8],
        "target_symbols": [46, 120],
        "distractor_ratio": 0.75,
        "description": "Repository-scale challenge context with substantial distractor material.",
    },
}

FAMILIES = {
    "local_bugfix": {
        "scope": "localized_file",
        "challenge": "Fix a behavior defect with nearby misleading code and preserve boundary semantics.",
        "oracle": "Focused regression plus neighboring invariant tests.",
    },
    "api_feature": {
        "scope": "bounded_multi_file",
        "challenge": "Add an API capability while preserving backward compatibility and serialization contracts.",
        "oracle": "Contract tests, compatibility tests, and end-to-end request/response checks.",
    },
    "cross_file_refactor": {
        "scope": "cross_subsystem",
        "challenge": "Refactor ownership or symbol boundaries across modules without behavior drift.",
        "oracle": "Full focused suite plus import/contract and semantic-equivalence checks.",
    },
    "test_ci_repair": {
        "scope": "bounded_multi_file",
        "challenge": "Repair a deterministic CI/test failure with environment and fixture interactions.",
        "oracle": "Reproducing failing test, targeted suite, and clean rerun.",
    },
    "data_schema_migration": {
        "scope": "cross_subsystem",
        "challenge": "Evolve persisted schema with forward/backward compatibility and migration idempotence.",
        "oracle": "Round-trip migration, old/new fixtures, rollback or downgrade safety checks.",
    },
    "concurrency_lifecycle": {
        "scope": "cross_subsystem",
        "challenge": "Fix ordering, lease, ownership, or stale-state behavior under interleaving events.",
        "oracle": "Deterministic concurrency schedule tests and state-machine invariants.",
    },
    "orchestration_state": {
        "scope": "cross_subsystem",
        "challenge": "Preserve run/wave identity, acceptance ownership, and fail-closed orchestration transitions.",
        "oracle": "Ledger lineage assertions and state-transition tests across restart/reconcile boundaries.",
    },
    "performance_resource_boundary": {
        "scope": "bounded_multi_file",
        "challenge": "Separate resource pressure or queue noise from actual repair/rework causality.",
        "oracle": "Resource-admission fixtures plus functional proof that capacity noise does not relabel outcomes.",
    },
}

OUTCOMES = {
    "first_pass_accepted": {
        "first_pass_accepted": True,
        "replan_count": 0,
        "manual_fix_required": False,
        "oracle_pass": True,
    },
    "rework_required": {
        "first_pass_accepted": False,
        "replan_count": 1,
        "manual_fix_required": True,
        "oracle_pass": True,
    },
}

CONTRACT_CASES = [
    ("C001", "missing_solution_shadow", "Attempt first mutation without a solution shadow.", "fail_closed"),
    ("C002", "late_solution_shadow", "Record the shadow only after first_write_seq.", "fail_closed"),
    ("C003", "conflicting_solution_shadow", "Record conflicting shadow recommendations for one wave.", "fail_closed_or_integrity_error"),
    ("C004", "workspace_identity_mismatch", "Observation belongs to a different workspace identity.", "exclude_or_fail_closed"),
    ("C005", "measurement_epoch_mismatch", "Observation was produced under a stale measurement epoch.", "exclude_or_fail_closed"),
    ("C006", "missing_proof_lineage", "Accepted-looking observation has no proof lineage.", "incomplete_not_promotion_eligible"),
    ("C007", "wrong_wave_proof", "Proof belongs to a different run/wave.", "integrity_error"),
    ("C008", "missing_quality_outcome", "Accepted checkpoint lacks a quality outcome.", "incomplete_not_promotion_eligible"),
    ("C009", "operator_report_wrong_owner", "Completion report is attached to the wrong run/wave.", "integrity_error"),
    ("C010", "operator_report_unacknowledged", "A valid accepted report remains unacknowledged before replacement work.", "block_next_material_wave_only"),
    ("C011", "duplicate_run_wave", "Duplicate ingestion of the same run/wave is attempted.", "deduplicate"),
    ("C012", "benchmark_exclusion", "Synthetic benchmark row is present in the evaluation corpus.", "must_not_affect_canonical_readiness"),
    ("C013", "replay_provenance_spoof", "Replay fixture claims organic/representative provenance.", "reject_provenance"),
    ("C014", "malformed_outcome_class", "Outcome class is missing, unknown, or contradictory.", "fail_closed"),
    ("C015", "unobserved_cost_semantics", "Provider/candidate cost is unobserved.", "remain_unobserved_not_zero"),
    ("C016", "route_drift_in_measurement_epoch", "A deterministic measurement run silently changes route.", "flag_or_fail_closed"),
    ("C017", "base_or_worktree_drift", "Base/worktree changes after preflight without controlled rebase.", "fail_closed"),
    ("C018", "outcome_contradiction", "first_pass_accepted conflicts with repair/replan evidence.", "integrity_error"),
    ("C019", "readiness_non_interference", "Run entire benchmark corpus against isolated storage.", "canonical_readiness_unchanged"),
    ("C020", "canonical_ledger_write_barrier", "Harness attempts to write benchmark fixtures to canonical ledger.", "hard_block"),
]

STAT_CASES = [
    ("S001", "empty_population", "No eligible observations.", "collecting_insufficient_sample"),
    ("S002", "single_class_positive", "Only rework-required observations.", "collecting_insufficient_class_support"),
    ("S003", "single_class_negative", "Only first-pass accepted observations.", "collecting_insufficient_class_support"),
    ("S004", "tiny_balanced_population", "Balanced classes but intentionally below canonical support requirements.", "collecting_insufficient_sample"),
    ("S005", "large_null_signal", "Large balanced population with outcomes randomized independently of all candidate signals.", "no_validated_signal"),
    ("S006", "strong_known_signal", "Large balanced isolated population with a deliberately injected monotonic signal.", "recover_signal_in_isolated_eval"),
    ("S007", "duplicate_leakage", "A small set is duplicated many times to imitate support growth.", "no_support_gain_after_dedup"),
    ("S008", "temporal_leakage", "A feature is derived from information unavailable at prediction time.", "reject_or_flag_leakage"),
    ("S009", "context_confounding", "A candidate signal only works because context tier correlates with outcome.", "reject_unstable_signal"),
    ("S010", "task_family_confounding", "A candidate signal only works in one task family.", "reject_unstable_signal"),
    ("S011", "xl_direction_reversal", "Signal direction reverses in XL while looking strong in S/M/L.", "reject_or_mark_unstable"),
    ("S012", "temporal_holdout_confirmation", "Signal survives an untouched later-time holdout across multiple context tiers.", "diagnostic_confirmation"),
]


def challenge_cases():
    rows = []
    n = 0
    confidences = ["high", "medium", "low", "medium"]
    oracles = ["strong", "moderate", "weak", "strong"]
    risks = ["low", "medium", "high", "medium"]
    tiers = list(CONTEXT_TIERS)
    families = list(FAMILIES)
    for tier, family, outcome in product(tiers, families, OUTCOMES):
        n += 1
        ti = tiers.index(tier)
        fi = families.index(family)
        oi = 0 if outcome == "first_pass_accepted" else 1
        # Rotated metadata prevents a trivial one-feature rule from perfectly encoding the outcome.
        idx = (ti + fi + oi) % 4
        counter_signal = ((ti * 8 + fi) % 5 == 0)
        root_conf = confidences[idx]
        oracle_strength = oracles[(idx + fi) % 4]
        repair_risk = risks[(idx + ti) % 4]
        if counter_signal:
            if outcome == "first_pass_accepted":
                root_conf, oracle_strength, repair_risk = "low", "weak", "high"
            else:
                root_conf, oracle_strength, repair_risk = "high", "strong", "low"
        scale = CONTEXT_TIERS[tier]
        files_mid = round(sum(scale["files"]) / 2)
        loc_mid = round(sum(scale["relevant_loc"]) / 2)
        sym_mid = round(sum(scale["target_symbols"]) / 2)
        if outcome == "first_pass_accepted":
            actual_factor = 1.05 if (fi + ti) % 2 == 0 else 0.90
        else:
            actual_factor = 1.50 if (fi + ti) % 2 == 0 else 1.20
        rows.append({
            "id": f"W{n:03d}",
            "kind": "workflow_challenge",
            "source_class": "synthetic_benchmark",
            "promotion_eligible": False,
            "context_tier": tier,
            "task_family": family,
            "expected_outcome": outcome,
            "challenge": FAMILIES[family]["challenge"],
            "oracle": FAMILIES[family]["oracle"],
            "context": scale,
            "shadow": {
                "candidate_solution_scope": FAMILIES[family]["scope"],
                "estimated_touched_surface": {
                    "files": files_mid,
                    "lines": max(10, int(loc_mid * 0.03)),
                    "symbols": sym_mid,
                },
                "root_cause_confidence": root_conf,
                "oracle_strength": oracle_strength,
                "expected_repair_risk": repair_risk,
                "smallest_causal_solution": {
                    "scope": FAMILIES[family]["scope"],
                    "estimated_touched_surface": {
                        "files": max(1, int(files_mid * 0.7)),
                        "lines": max(5, int(loc_mid * 0.02)),
                        "symbols": max(1, int(sym_mid * 0.7)),
                    },
                },
            },
            "ground_truth": {
                **OUTCOMES[outcome],
                "actual_touched_surface": {
                    "files": max(1, round(files_mid * actual_factor)),
                    "lines": max(5, round(loc_mid * 0.03 * actual_factor)),
                    "symbols": max(1, round(sym_mid * actual_factor)),
                },
                "counter_signal_case": counter_signal,
            },
            "assertions": [
                "solution_shadow_precedes_first_write",
                "workspace_and_measurement_identity_match",
                "proof_lineage_is_owned_by_same_run_wave",
                "quality_outcome_is_recorded",
                "benchmark_provenance_is_excluded_from_promotion_population",
                "observed_outcome_matches_fixture_ground_truth",
            ],
        })
    return rows


def build_manifest():
    cases = []
    for cid, name, setup, expected in CONTRACT_CASES:
        cases.append({
            "id": cid,
            "kind": "contract_integrity",
            "source_class": "synthetic_benchmark",
            "promotion_eligible": False,
            "name": name,
            "setup": setup,
            "expected": expected,
        })
    for cid, name, setup, expected in STAT_CASES:
        cases.append({
            "id": cid,
            "kind": "statistical_readiness",
            "source_class": "synthetic_benchmark",
            "promotion_eligible": False,
            "name": name,
            "setup": setup,
            "expected": expected,
            "storage": "isolated_temporary_fixture_only",
        })
    cases.extend(challenge_cases())
    manifest = {
        "schema_version": 1,
        "battery_id": "p4-ms1-evaluation-battery-v1",
        "purpose": "Evaluate P4/MS1 measurement integrity, readiness discrimination, and large-context robustness without manufacturing canonical promotion evidence.",
        "canonical_readiness_authority": "resources/coding-tools-mcp/scripts/report_p4_readiness.py --workspace .",
        "threshold_policy": "Never hardcode or weaken canonical readiness thresholds in the benchmark. Import/read them from the canonical implementation at integration time.",
        "global_server_first": "OFF",
        "promotion_policy": {
            "synthetic_benchmark": False,
            "replay_fixture": False,
            "organic_representative": "Only canonical organic observations may be promotion-eligible, subject to repository provenance rules.",
        },
        "counts": {
            "contract_integrity": len(CONTRACT_CASES),
            "statistical_readiness": len(STAT_CASES),
            "workflow_challenge": 64,
            "total": len(CONTRACT_CASES) + len(STAT_CASES) + 64,
        },
        "context_tiers": CONTEXT_TIERS,
        "task_families": FAMILIES,
        "cases": cases,
    }
    return manifest


def write_csv(manifest):
    path = ROOT / "p4_evaluation_cases.csv"
    fields = ["id", "kind", "promotion_eligible", "context_tier", "task_family", "expected", "expected_outcome", "name"]
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for c in manifest["cases"]:
            w.writerow({k: c.get(k, "") for k in fields})


def write_protocol(manifest):
    p = ROOT / "p4_evaluation_protocol_v1.md"
    lines = []
    lines.append("# P4/MS1 Evaluation Battery v1")
    lines.append("")
    lines.append("## Purpose")
    lines.append("")
    lines.append("This battery evaluates the P4/MS1 measurement and readiness system. It is deliberately separated from canonical promotion evidence: every synthetic, generated, adversarial, or replay case is `promotion_eligible=false` and must run against isolated storage.")
    lines.append("")
    lines.append("The canonical readiness decision remains the repository reporter:")
    lines.append("")
    lines.append("```bash")
    lines.append("python resources/coding-tools-mcp/scripts/report_p4_readiness.py --workspace .")
    lines.append("```")
    lines.append("")
    lines.append("Do not copy sample-count thresholds into this battery. The integration adapter must read the current canonical implementation so test code cannot silently diverge from the phase gate.")
    lines.append("")
    lines.append("## Design")
    lines.append("")
    lines.append(f"Total cases: **{manifest['counts']['total']}** = 64 workflow challenges + {manifest['counts']['contract_integrity']} integrity cases + {manifest['counts']['statistical_readiness']} statistical/readiness cases.")
    lines.append("")
    lines.append("### Large-context strata")
    lines.append("")
    lines.append("| Tier | Files | Relevant LOC | Dependency hops | Target symbols | Distractor ratio |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for k, v in CONTEXT_TIERS.items():
        lines.append(f"| {k} | {v['files'][0]}-{v['files'][1]} | {v['relevant_loc'][0]}-{v['relevant_loc'][1]} | {v['dependency_hops'][0]}-{v['dependency_hops'][1]} | {v['target_symbols'][0]}-{v['target_symbols'][1]} | {int(v['distractor_ratio']*100)}% |")
    lines.append("")
    lines.append("### Workflow families")
    lines.append("")
    for name, v in FAMILIES.items():
        lines.append(f"- **{name}**: {v['challenge']} Oracle: {v['oracle']}")
    lines.append("")
    lines.append("Each family is crossed with every context tier and two ground-truth outcomes (`first_pass_accepted`, `rework_required`), yielding 8 x 4 x 2 = 64 workflow cases. Metadata is intentionally rotated and includes counter-signal cases so a trivial rule such as 'low confidence means rework' cannot score perfectly.")
    lines.append("")
    lines.append("## Five non-negotiable gates")
    lines.append("")
    lines.append("1. **Measurement integrity gate**: 20/20 contract/integrity cases must behave fail-closed where specified. Missing shadow, wrong ownership, stale identity, duplicate ingestion, or missing proof/quality lineage cannot be silently accepted.")
    lines.append("2. **Benchmark isolation gate**: running all 96 cases must leave the canonical P4 readiness population and result unchanged.")
    lines.append("3. **Null-signal gate**: a large balanced null fixture must produce zero validated predictive signals. Duplicate rows and leakage must not create artificial support.")
    lines.append("4. **Known-signal recovery gate**: an isolated fixture with a strong injected signal should be detectable by the evaluation path, while confounded or XL-reversing variants must be rejected or flagged unstable by the secondary robustness evaluator.")
    lines.append("5. **Organic promotion gate**: only later, genuinely organic representative observations may affect canonical P4/MS1 readiness. The canonical reporter is the sole promotion authority.")
    lines.append("")
    lines.append("## Statistical protocol")
    lines.append("")
    lines.append("Use temporal ordering for development data: tune/inspect on earlier observations and evaluate on a later untouched holdout. Report class support explicitly. For skewed repaired/nonrepair outcomes, include precision/recall and PR-area diagnostics rather than relying on accuracy alone. If a probability/risk score exists, assess calibration separately from discrimination. These diagnostics do not replace the canonical reporter; they reveal whether a validated signal is likely robust enough to trust.")
    lines.append("")
    lines.append("Recommended secondary diagnostics per candidate signal:")
    lines.append("")
    lines.append("- repaired and nonrepair support counts by time window, context tier, and task family;")
    lines.append("- precision, recall, F1, PR-AUC and false-positive/false-negative counts at the chosen decision rule;")
    lines.append("- temporal holdout result and direction/effect stability across S/M/L/XL;")
    lines.append("- family-stratified result to expose task-type confounding;")
    lines.append("- bootstrap confidence interval or repeated time-block sensitivity analysis when sample size permits;")
    lines.append("- calibration/reliability diagnostics only when the signal is interpreted probabilistically.")
    lines.append("")
    lines.append("## Execution modes")
    lines.append("")
    lines.append("### Mode A - unit/contract")
    lines.append("Run C001-C020 using temporary state/ledger fixtures. No canonical workspace writes.")
    lines.append("")
    lines.append("### Mode B - statistical fixtures")
    lines.append("Run S001-S012 using isolated generated populations. Assert expected fail-closed, leakage, null-signal, and known-signal behavior. The generated rows are not representative observations.")
    lines.append("")
    lines.append("### Mode C - large-context workflow challenge")
    lines.append("Run W001-W064 in disposable worktrees or generated fixture repositories. Capture the same P4 evidence fields as normal work, but force benchmark provenance and `promotion_eligible=false`. Validate observed outcomes against ground truth and inspect signal behavior across context strata.")
    lines.append("")
    lines.append("### Mode D - organic shadow evaluation")
    lines.append("Observe normal feature/bugfix work without changing routing or manufacturing outcomes. Keep a time-ordered untouched holdout. Only this mode may feed canonical promotion evidence when repository provenance rules mark an observation eligible.")
    lines.append("")
    lines.append("## Required P4 evidence fields")
    lines.append("")
    lines.append("The adapter should preserve at least: workspace/measurement identity; run/wave identity; solution-shadow ordering; candidate scope; estimated files/lines/symbols; root-cause confidence; oracle strength; expected repair risk; smallest causal solution; actual patch surface; proof lineage/status; first-pass acceptance; replan/failure events; quality outcome; report ownership/lifecycle; and provenance/promotion eligibility.")
    lines.append("")
    lines.append("## Stop conditions")
    lines.append("")
    lines.append("Stop and fix the evaluation system before interpreting predictor quality if any integrity case silently passes invalid evidence, benchmark rows alter canonical readiness, duplicates inflate support, temporal leakage is not detectable, or run/wave/workspace identity can be crossed without rejection.")
    lines.append("")
    lines.append("## Canonical close decision")
    lines.append("")
    lines.append("A green battery means P4 measurement/readiness behavior is trustworthy under controlled challenge. It does **not** close P4/MS1. Closure remains fail-closed and requires the canonical reporter to become ready from organic representative evidence under the frozen measurement contract.")
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    manifest = build_manifest()
    (ROOT / "p4_evaluation_battery_v1.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    write_csv(manifest)
    write_protocol(manifest)
    print(json.dumps(manifest["counts"], indent=2))


if __name__ == "__main__":
    main()
