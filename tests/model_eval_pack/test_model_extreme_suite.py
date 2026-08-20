from __future__ import annotations

import copy
import unittest
from pathlib import Path

import run_model_extreme_suite as mx


HERE = Path(__file__).resolve().parent


class ModelExtremeSuiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = mx.load_json(mx.CATALOG_PATH)
        cls.feedback = mx.load_json(mx.FEEDBACK_PATH)
        cls.oracles = mx.load_json(mx.ORACLE_PATH)
        cls.sources = mx.load_json(mx.SOURCE_PATH)
        cls.oracle_by_id = {str(item["id"]): item for item in cls.oracles["oracles"]}
        cls.challenge_by_id = {str(item["id"]): item for item in cls.catalog["challenges"]}
        cls.hard = set(cls.catalog["hard_fail_action_tags"])

    def test_bundle_has_24_extreme_6_ultra_and_public_private_split(self) -> None:
        result = mx.validate_bundle(self.catalog, self.feedback, self.oracles, self.sources)
        self.assertEqual(result["challenge_count"], 30)
        self.assertEqual(result["tier_counts"], {"Extreme": 24, "Ultra": 6})
        self.assertTrue(result["public_private_split"])
        self.assertTrue(result["nonpromotion_policy"])

    def test_recursive_public_leak_guard_rejects_nested_private_key(self) -> None:
        bad = copy.deepcopy(self.catalog)
        bad["challenges"][0].setdefault("public_context", {})["nested"] = {"grade_spec": {"x": 1}}
        with self.assertRaises(ValueError):
            mx.validate_bundle(bad, self.feedback, self.oracles, self.sources)

    def test_cli_requires_explicit_external_or_self_test_mode(self) -> None:
        with self.assertRaises(SystemExit):
            mx.build_parser().parse_args(["--repo-root", "."])

    def test_missing_model_response_is_unknown_not_zero(self) -> None:
        challenge = self.challenge_by_id["MX-RL-001"]
        result = mx.grade_challenge(challenge, self.oracle_by_id["MX-RL-001"], None, self.hard)
        self.assertEqual(result["status"], "UNKNOWN")
        summary = mx.aggregate_summary([result])
        self.assertEqual(summary["unknown"], 1)
        self.assertIsNone(summary["final_pass_rate"])
        self.assertTrue(summary["unknown_is_not_zero"])

    def test_reference_answer_is_first_pass(self) -> None:
        challenge = self.challenge_by_id["MX-CS-001"]
        oracle = self.oracle_by_id["MX-CS-001"]
        result = mx.grade_challenge(challenge, oracle, {"first_attempt": copy.deepcopy(oracle["reference_response"])}, self.hard)
        self.assertEqual(result["status"], "FIRST_PASS")

    def test_failed_first_attempt_can_recover_after_staged_feedback(self) -> None:
        challenge = self.challenge_by_id["MX-DF-002"]
        oracle = self.oracle_by_id["MX-DF-002"]
        envelope = {
            "first_attempt": {"decision": "patch_product", "action_tags": []},
            "repair_attempt": copy.deepcopy(oracle["reference_response"]),
        }
        result = mx.grade_challenge(challenge, oracle, envelope, self.hard)
        self.assertEqual(result["status"], "REPAIRED")
        self.assertTrue(result["repair_opportunity"])
        staged = mx.feedback_after_failed_first_attempt(self.feedback, "MX-DF-002")
        self.assertIsNotNone(staged)
        self.assertIn("observation", staged)

    def test_hard_fail_action_cannot_be_repaired_away(self) -> None:
        challenge = self.challenge_by_id["MX-AG-001"]
        oracle = self.oracle_by_id["MX-AG-001"]
        first = copy.deepcopy(oracle["reference_response"])
        first["action_tags"] = ["test_deletion"]
        envelope = {"first_attempt": first, "repair_attempt": copy.deepcopy(oracle["reference_response"])}
        result = mx.grade_challenge(challenge, oracle, envelope, self.hard)
        self.assertEqual(result["status"], "HARD_FAIL")
        self.assertIn("test_deletion", result["detail"]["hard_fail_tags"])

    def test_feedback_ids_are_repair_eligible_only(self) -> None:
        repair_ids = {str(item["id"]) for item in self.catalog["challenges"] if item.get("repair_eligible") is True}
        feedback_ids = {str(item["id"]) for item in self.feedback["feedback"]}
        self.assertTrue(feedback_ids)
        self.assertTrue(feedback_ids.issubset(repair_ids))

    def test_every_challenge_is_nonpromoting(self) -> None:
        self.assertTrue(mx._policy_ok(self.catalog["evidence_policy"]))
        self.assertTrue(all(mx._policy_ok(item) for item in self.catalog["challenges"]))

    def test_weighted_unknown_dimensions_are_excluded_not_zeroed(self) -> None:
        results = [
            {"status": "FIRST_PASS", "dimensions": ["correctness"], "family": "x"},
            {"status": "UNKNOWN", "dimensions": ["security"], "family": "x"},
        ]
        summary, weighted = mx.summarize_dimensions(results, self.catalog["dimension_weights"])
        self.assertEqual(summary["correctness"]["score"], 1.0)
        self.assertIsNone(summary["security"]["score"])
        self.assertEqual(weighted, 1.0)

    def test_ultra_order_constraint_detects_integration_error(self) -> None:
        challenge = self.challenge_by_id["MX-U-001"]
        oracle = self.oracle_by_id["MX-U-001"]
        good = mx.grade_challenge(challenge, oracle, {"first_attempt": copy.deepcopy(oracle["reference_response"])}, self.hard)
        self.assertEqual(good["status"], "FIRST_PASS")
        bad_response = copy.deepcopy(oracle["reference_response"])
        bad_response["sequence"] = list(reversed(bad_response["sequence"]))
        bad = mx.grade_challenge(challenge, oracle, {"first_attempt": bad_response}, self.hard)
        self.assertEqual(bad["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
