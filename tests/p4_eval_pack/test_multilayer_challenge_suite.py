from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "run_multilayer_challenge_suite.py"
SPEC = importlib.util.spec_from_file_location("multilayer_suite", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
SUITE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SUITE)


class MultilayerChallengeSuiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = SUITE.load_json(SUITE.CATALOG_PATH)
        cls.oracles = SUITE.load_json(SUITE.ORACLE_PATH)
        cls.sources = SUITE.load_json(SUITE.SOURCE_PATH)
        cls.known = SUITE.load_json(SUITE.KNOWN_PATH)

    def test_bundle_has_twelve_layers_and_public_hidden_split(self) -> None:
        report = SUITE.validate_bundle(self.catalog, self.oracles, self.sources, self.known)
        self.assertEqual(set(report["layer_counts"]), SUITE.EXPECTED_LAYERS)
        self.assertGreaterEqual(report["challenge_count"], 36)
        self.assertEqual(report["challenge_count"], report["oracle_count"])
        self.assertGreaterEqual(report["research_source_count"], 10)
        self.assertTrue(report["public_hidden_split"])
        self.assertTrue(report["nonpromotion_policy"])

    def test_all_non_stress_reference_responses_satisfy_their_oracles(self) -> None:
        oracle_by_id = {str(item["id"]): item for item in self.oracles["oracles"]}
        for challenge in self.catalog["challenges"]:
            oracle = oracle_by_id[str(challenge["id"])]
            if oracle["oracle_kind"] == "stress_case_signature":
                continue
            with self.subTest(challenge=challenge["id"]):
                result = SUITE.grade_one(
                    challenge,
                    oracle,
                    oracle["reference_response"],
                    stress_cases={},
                    known=self.known,
                )
                self.assertEqual(result["status"], "PASS", result)

    def test_state_machine_rejects_mid_execution_route_change(self) -> None:
        challenge = next(item for item in self.catalog["challenges"] if item["id"] == "ML-L02-002")
        self.assertEqual(
            SUITE.state_machine_truth(challenge["public_input"]),
            {"final_state": "PROVING", "illegal_event_indexes": [3]},
        )

    def test_web_reducer_is_idempotent_and_rejects_stale_versions(self) -> None:
        challenge = next(item for item in self.catalog["challenges"] if item["id"] == "ML-L05-001")
        self.assertEqual(
            SUITE.web_reducer_truth(challenge["public_input"]),
            {"side_effect_count": 2, "final_version": 7, "rejected_count": 1, "duplicate_ignored_count": 1},
        )

    def test_cpm_truth_has_expected_makespan_and_critical_path(self) -> None:
        challenge = next(item for item in self.catalog["challenges"] if item["id"] == "ML-L10-001")
        self.assertEqual(SUITE.cpm_truth(challenge["public_input"]), {"makespan": 13, "critical_path": ["A", "B", "D", "F"]})

    def test_resource_schedule_enforces_precedence_and_capacity(self) -> None:
        challenge = next(item for item in self.catalog["challenges"] if item["id"] == "ML-L10-002")
        valid, detail = SUITE.resource_schedule_valid(challenge["public_input"], {"start_times": {"A": 0, "B": 3, "C": 3, "D": 5}})
        self.assertTrue(valid, detail)
        invalid, invalid_detail = SUITE.resource_schedule_valid(challenge["public_input"], {"start_times": {"A": 0, "B": 2, "C": 3, "D": 5}})
        self.assertFalse(invalid)
        self.assertTrue(invalid_detail["precedence_violations"] or invalid_detail["resource_violations"])

    def test_time_cost_oracle_finds_minimum_cost_under_deadline(self) -> None:
        challenge = next(item for item in self.catalog["challenges"] if item["id"] == "ML-L10-003")
        valid, detail = SUITE.time_cost_valid(challenge["public_input"], {"selected_modes": {"A": "crash", "B": "normal", "C": "crash"}})
        self.assertTrue(valid, detail)
        self.assertEqual(detail["duration"], 9)
        self.assertEqual(detail["cost"], 19)
        self.assertEqual(detail["minimum_cost"], 19)

    def test_resolved_canonical_and_fixture_diagnostics_are_clean(self) -> None:
        canonical = set(self.known["canonical_blind_spot_case_ids"])
        fixtures = set(self.known["fixture_defect_case_ids"])
        failed = set(self.known["expected_failed_case_ids"])
        self.assertEqual(canonical, set())
        self.assertEqual(fixtures, set())
        self.assertFalse(canonical & fixtures)
        self.assertEqual(fixtures, failed)
        self.assertEqual(self.known["expected_passed"], 35)
        self.assertEqual(self.known["expected_failed"], 0)


if __name__ == "__main__":
    unittest.main()
