from __future__ import annotations

import collections
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "p4_evaluation_battery_v1.json"
FIXTURES = ROOT / "p4_statistical_fixtures_v1.jsonl"
INDEX = ROOT / "p4_statistical_fixture_index_v1.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def pearson(xs, ys):
    if len(xs) != len(ys) or len(xs) < 2:
        return float("nan")
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    dx = sum((x - mx) ** 2 for x in xs)
    dy = sum((y - my) ** 2 for y in ys)
    if dx == 0 or dy == 0:
        return float("nan")
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / math.sqrt(dx * dy)


def outcome_vector(rows):
    return [1 if r["outcome"]["rework_required"] else 0 for r in rows]


def signal_corr(rows, key):
    ys = outcome_vector(rows)
    xs = [float(r["derived_candidate_signals"][key]) for r in rows]
    return pearson(xs, ys)


class Battery:
    def __init__(self):
        self.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.index = json.loads(INDEX.read_text(encoding="utf-8"))
        self.rows = [json.loads(line) for line in FIXTURES.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.by_case = collections.defaultdict(list)
        for row in self.rows:
            self.by_case[row["case_id"]].append(row)
        self.results = []
        self.metrics = {}

    def check(self, name, condition, detail=None, layer="isolated"):
        ok = bool(condition)
        self.results.append({"name": name, "status": "PASS" if ok else "FAIL", "layer": layer, "detail": detail})
        if not ok:
            raise AssertionError(f"{name}: {detail}")

    def run(self):
        # Generator determinism and manifest structure.
        before = {p.name: sha256(p) for p in (MANIFEST, FIXTURES, INDEX)}
        subprocess.run([sys.executable, str(ROOT / "generate_p4_eval_battery.py")], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
        subprocess.run([sys.executable, str(ROOT / "generate_p4_stat_fixtures.py")], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
        after = {p.name: sha256(p) for p in (MANIFEST, FIXTURES, INDEX)}
        self.check("generator_determinism", before == after, {"before": before, "after": after})

        cases = self.manifest["cases"]
        ids = [c["id"] for c in cases]
        counts = collections.Counter(c["kind"] for c in cases)
        self.check("manifest_total_96", len(cases) == 96, len(cases))
        self.check("manifest_unique_ids", len(ids) == len(set(ids)), len(set(ids)))
        self.check("manifest_layer_counts", counts == {"contract_integrity": 20, "statistical_readiness": 12, "workflow_challenge": 64}, dict(counts))
        self.check("global_server_first_off", self.manifest["global_server_first"] == "OFF", self.manifest["global_server_first"])
        self.check("synthetic_promotion_policy_false", self.manifest["promotion_policy"]["synthetic_benchmark"] is False)
        self.check("all_benchmark_cases_nonpromotable", all(c["promotion_eligible"] is False for c in cases), sum(c["promotion_eligible"] is False for c in cases))

        # Contract/integrity specs: validate that all invalid evidence paths are fail-closed/excluded by expectation.
        contract = [c for c in cases if c["kind"] == "contract_integrity"]
        allowed_contract_expectations = {
            "fail_closed", "fail_closed_or_integrity_error", "exclude_or_fail_closed",
            "incomplete_not_promotion_eligible", "integrity_error",
            "block_next_material_wave_only", "deduplicate",
            "must_not_affect_canonical_readiness", "reject_provenance",
            "remain_unobserved_not_zero", "flag_or_fail_closed",
            "canonical_readiness_unchanged", "hard_block",
        }
        self.check("contract_specs_all_fail_closed_or_excluded", all(c["expected"] in allowed_contract_expectations for c in contract), [c for c in contract if c["expected"] not in allowed_contract_expectations], layer="spec")

        # Workflow coverage: exact 8 x 4 x 2 cross product and large-context escalation.
        workflow = [c for c in cases if c["kind"] == "workflow_challenge"]
        combos = collections.Counter((c["task_family"], c["context_tier"], c["expected_outcome"]) for c in workflow)
        expected_combos = {
            (family, tier, outcome)
            for family in self.manifest["task_families"]
            for tier in self.manifest["context_tiers"]
            for outcome in ("first_pass_accepted", "rework_required")
        }
        self.check("workflow_cross_product_complete", set(combos) == expected_combos and all(v == 1 for v in combos.values()), {"unique_combos": len(combos)}, layer="spec")
        required_assertions = {
            "solution_shadow_precedes_first_write",
            "workspace_and_measurement_identity_match",
            "proof_lineage_is_owned_by_same_run_wave",
            "quality_outcome_is_recorded",
            "benchmark_provenance_is_excluded_from_promotion_population",
            "observed_outcome_matches_fixture_ground_truth",
        }
        self.check("workflow_assertion_contract_complete", all(required_assertions.issubset(set(c["assertions"])) for c in workflow), layer="spec")
        tiers = self.manifest["context_tiers"]
        tier_order = ["S", "M", "L", "XL"]
        self.check("context_files_monotonic", all(tiers[a]["files"][1] < tiers[b]["files"][1] for a,b in zip(tier_order,tier_order[1:])), {t: tiers[t]["files"] for t in tier_order}, layer="spec")
        self.check("context_loc_monotonic", all(tiers[a]["relevant_loc"][1] < tiers[b]["relevant_loc"][1] for a,b in zip(tier_order,tier_order[1:])), {t: tiers[t]["relevant_loc"] for t in tier_order}, layer="spec")
        self.check("xl_context_is_repository_scale", tiers["XL"]["files"][1] >= 60 and tiers["XL"]["relevant_loc"][1] >= 50000 and tiers["XL"]["distractor_ratio"] >= 0.75, tiers["XL"], layer="spec")
        counter_signal = sum(bool(c["ground_truth"].get("counter_signal_case")) for c in workflow)
        self.check("workflow_counter_signal_present", counter_signal >= 8, counter_signal, layer="spec")

        # Statistical fixture integrity.
        self.check("fixture_row_count_4716", len(self.rows) == 4716, len(self.rows))
        self.check("fixture_index_matches_rows", self.index["total_rows"] == len(self.rows), self.index["total_rows"])
        self.check("fixture_all_nonpromotable", all(r["promotion_eligible"] is False for r in self.rows), layer="isolated")
        self.check("fixture_all_synthetic", all(r["source_class"] == "synthetic_benchmark" for r in self.rows), layer="isolated")
        self.check("fixture_workspace_isolated", all(r["workspace_identity"] == "isolated-p4-fixture" for r in self.rows), layer="isolated")
        self.check("fixture_shadow_prewrite", all(r["solution_shadow"]["recorded_before_first_write"] is True for r in self.rows), layer="isolated")

        # S001-S004: insufficient evidence/class support shapes.
        self.check("S001_empty_population", len(self.by_case["S001"]) == 0, len(self.by_case["S001"]))
        for cid, expected_pos in (("S002", 160), ("S003", 0)):
            rows = self.by_case[cid]
            pos = sum(outcome_vector(rows))
            self.check(f"{cid}_single_class", len(rows) == 160 and pos == expected_pos, {"n": len(rows), "positive": pos})
        rows = self.by_case["S004"]
        self.check("S004_tiny_balanced", len(rows) == 12 and sum(outcome_vector(rows)) == 6, {"n": len(rows), "positive": sum(outcome_vector(rows))})

        # S005: large null population must not contain a meaningful linear candidate signal.
        rows = self.by_case["S005"]
        null_corrs = {k: signal_corr(rows, k) for k in rows[0]["derived_candidate_signals"]}
        max_null = max(abs(v) for v in null_corrs.values() if not math.isnan(v))
        self.metrics["S005_null_correlations"] = null_corrs
        self.check("S005_null_signal", len(rows) == 512 and sum(outcome_vector(rows)) == 256 and max_null < 0.12, {"max_abs_corr": max_null, "correlations": null_corrs})

        # S006: known signal must be strongly recoverable.
        rows = self.by_case["S006"]
        known_corrs = {k: signal_corr(rows, k) for k in rows[0]["derived_candidate_signals"]}
        self.metrics["S006_known_correlations"] = known_corrs
        self.check("S006_known_signal_recovered", max(abs(v) for v in known_corrs.values() if not math.isnan(v)) > 0.75, known_corrs)

        # S007: duplication must not increase effective support.
        rows = self.by_case["S007"]
        originals = [r for r in rows if r["duplicate_of"] is None]
        dupes = [r for r in rows if r["duplicate_of"] is not None]
        self.check("S007_duplicate_support_dedup", len(rows) == 512 and len(originals) == 64 and len(dupes) == 448, {"raw": len(rows), "unique_support": len(originals), "duplicates": len(dupes)})

        # S008: explicit future-label leakage must be detectable.
        rows = self.by_case["S008"]
        ys = outcome_vector(rows)
        leaked = [r["leakage_features"].get("future_rework_label") for r in rows]
        leak_corr = pearson(leaked, ys)
        self.metrics["S008_leakage_corr"] = leak_corr
        self.check("S008_temporal_leakage_detected", leak_corr > 0.999 and all("future_rework_label" in r["leakage_features"] for r in rows), leak_corr)

        # S009/S010: signal is only a group-membership proxy; within group it has no variation.
        rows = self.by_case["S009"]
        between_corr = signal_corr(rows, "confounded_context_indicator")
        within_constant = all(len({r["derived_candidate_signals"]["confounded_context_indicator"] for r in rows if r["context_tier"] == tier}) == 1 for tier in ("S","M","L","XL"))
        self.check("S009_context_confounding_flagged", between_corr > 0.30 and within_constant, {"between_corr": between_corr, "within_group_signal_constant": within_constant})

        rows = self.by_case["S010"]
        between_corr = signal_corr(rows, "confounded_family_indicator")
        families = sorted({r["task_family"] for r in rows})
        within_constant = all(len({r["derived_candidate_signals"]["confounded_family_indicator"] for r in rows if r["task_family"] == fam}) == 1 for fam in families)
        self.check("S010_family_confounding_flagged", between_corr > 0.30 and within_constant, {"between_corr": between_corr, "within_group_signal_constant": within_constant})

        # S011: same candidate must reverse sign in XL.
        rows = self.by_case["S011"]
        tier_corrs = {}
        for tier in ("S","M","L","XL"):
            subset = [r for r in rows if r["context_tier"] == tier]
            tier_corrs[tier] = signal_corr(subset, "direction_reversal_signal")
        self.metrics["S011_tier_correlations"] = tier_corrs
        self.check("S011_xl_direction_reversal", all(tier_corrs[t] > 0.75 for t in ("S","M","L")) and tier_corrs["XL"] < -0.75, tier_corrs)

        # S012: stable known signal survives untouched later holdout.
        rows = self.by_case["S012"]
        split_corrs = {}
        split_counts = {}
        for split in ("development", "temporal_holdout"):
            subset = [r for r in rows if r.get("split") == split]
            split_corrs[split] = signal_corr(subset, "surface_underestimate_ratio")
            split_counts[split] = {"n": len(subset), "positive": sum(outcome_vector(subset))}
        self.metrics["S012_split_correlations"] = split_corrs
        self.check("S012_temporal_holdout_confirmation", split_counts["development"]["n"] == 600 and split_counts["temporal_holdout"]["n"] == 200 and split_corrs["development"] > 0.60 and split_corrs["temporal_holdout"] > 0.60 and abs(split_corrs["development"] - split_corrs["temporal_holdout"]) < 0.15, {"correlations": split_corrs, "counts": split_counts})

        return self.report()

    def report(self):
        passed = sum(r["status"] == "PASS" for r in self.results)
        failed = sum(r["status"] == "FAIL" for r in self.results)
        return {
            "battery_id": self.manifest["battery_id"],
            "scope": "isolated synthetic evaluation only; canonical reporter adapter not executed",
            "canonical_promotion_mutated": False,
            "checks": {"passed": passed, "failed": failed, "total": len(self.results)},
            "results": self.results,
            "metrics": self.metrics,
            "limitations": [
                "C001-C020 are validated here as fail-closed contract specifications, not executed against the live repository runtime.",
                "W001-W064 are validated for coverage/context/ground-truth shape, not executed as 64 real repository repair tasks.",
                "Canonical report_p4_readiness.py was not invoked by this isolated runner; integration must prove pre/post canonical readiness is unchanged.",
            ],
        }


def main():
    report_path = ROOT / "p4_eval_run_report.json"
    try:
        report = Battery().run()
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
        print(json.dumps({"status": "PASS", "report": str(report_path), "checks": report["checks"], "metrics": report["metrics"]}, indent=2))
        return 0
    except Exception as exc:
        partial = {"status": "FAIL", "error": f"{type(exc).__name__}: {exc}"}
        report_path.write_text(json.dumps(partial, indent=2), encoding="utf-8")
        print(json.dumps(partial, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
