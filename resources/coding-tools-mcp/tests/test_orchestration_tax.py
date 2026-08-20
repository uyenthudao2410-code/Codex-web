from __future__ import annotations

import unittest

from benchmarks.orchestration_tax import orchestration_tax_report


class _FakeLedger:
    def __init__(self, *, candidate_output_tokens: int | None = 70) -> None:
        self.records = {
            "baseline": {
                "run_id": "baseline",
                "pairing_eligible": True,
                "evaluation": {"pair_id": "pair-1", "policy": "chatweb_mcp", "provenance": "representative"},
                "controller": {"usage": {"input_tokens": 80, "output_tokens": 20}},
            },
            "candidate": {
                "run_id": "candidate",
                "pairing_eligible": True,
                "evaluation": {"pair_id": "pair-1", "policy": "solo_fast", "provenance": "representative"},
                "controller": {"usage": {"input_tokens": 80, "output_tokens": candidate_output_tokens}},
            },
        }

    def paired_policy_evaluation(self, **_: object) -> dict[str, object]:
        return {
            "baseline_policy": "chatweb_mcp",
            "results": [{
                "candidate_policy": "solo_fast",
                "pair_count": 1,
                "pairs": [{
                    "pair_id": "pair-1",
                    "baseline_accepted": True,
                    "candidate_accepted": True,
                    "baseline_first_pass": True,
                    "candidate_first_pass": True,
                }],
            }],
        }

    def list_runs(self, *, limit: int) -> list[dict[str, str]]:
        del limit
        return [{"run_id": "baseline"}, {"run_id": "candidate"}]

    def accepted_result_evaluation(self, run_id: str) -> dict[str, object]:
        return self.records[run_id]

    def list_usage_events(self, run_id: str, *, limit: int | None) -> list[dict[str, object]]:
        del run_id, limit
        return []


class OrchestrationTaxTests(unittest.TestCase):
    def test_uses_only_canonical_pairs_and_reports_observed_multiplier(self) -> None:
        report = orchestration_tax_report(_FakeLedger(), min_pairs=1, min_task_classes=1)
        result = report["results"][0]
        self.assertEqual(result["status"], "observed")
        self.assertEqual(result["complete_usage_pairs"], 1)
        self.assertEqual(result["total_usage_multiplier"]["p50"], 1.5)
        self.assertEqual(result["root_work_amplification_delta"]["p50"], 0.0)
        self.assertTrue(report["policy"]["canonical_pair_ids_are_authoritative_whitelist"])
        self.assertTrue(report["policy"]["unknown_is_not_zero"])
        self.assertFalse(report["automatic_activation"])

    def test_missing_controller_usage_is_unknown_not_zero_and_holds(self) -> None:
        report = orchestration_tax_report(_FakeLedger(candidate_output_tokens=None), min_pairs=1, min_task_classes=1)
        result = report["results"][0]
        pair = result["pairs"][0]
        self.assertEqual(result["status"], "hold")
        self.assertEqual(result["complete_usage_pairs"], 0)
        self.assertIsNone(pair["total_usage_multiplier"])
        self.assertEqual(pair["reason"], "controller_token_usage_incomplete")
        self.assertIn("usage_coverage_incomplete", result["hold_reasons"])
        self.assertFalse(result["automatic_activation"])


if __name__ == "__main__":
    unittest.main()
