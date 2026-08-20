from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from close_model_extreme_evaluation import build_manifest, render_summary, verify_manifest, verify_report


class ModelExtremeCloseoutTests(unittest.TestCase):
    def _fixture(self, root: Path) -> tuple[Path, Path, str]:
        public = root / "tests/model_eval_pack/public"
        private = root / "tests/model_eval_pack/private"
        results = root / "tests/model_eval_pack/results"
        public.mkdir(parents=True)
        private.mkdir(parents=True)
        results.mkdir(parents=True)
        (public / "model_extreme_challenges_v1.json").write_text('{"challenges": []}\n', encoding="utf-8")
        (public / "model_extreme_feedback_v1.json").write_text('{"feedback": []}\n', encoding="utf-8")
        oracle = private / "model_extreme_oracles_v1.json"
        oracle.write_text('{"private": true}\n', encoding="utf-8")
        oracle_sha = hashlib.sha256(oracle.read_bytes()).hexdigest()
        responses = results / "responses.json"
        responses.write_text('{"responses": {}}\n', encoding="utf-8")
        report = {
            "schema_version": 1,
            "runner": "p4-mx-model-extreme-v1",
            "status": "FAIL",
            "response_mode": "external_model_responses",
            "evidence_policy": {
                "source_class": "benchmark",
                "promotion_eligible": False,
                "canonical_mutation_allowed": False,
                "p5_automatic_start": False,
                "automatic_policy_activation": False,
            },
            "canonical_before": {"state": "COLLECTING"},
            "canonical_after": {"state": "COLLECTING"},
            "canonical_non_interference": "PASS",
            "summary": {
                "total": 2,
                "attempted": 2,
                "first_pass": 1,
                "repaired": 0,
                "failed": 0,
                "hard_fail_count": 1,
                "unknown": 0,
                "first_pass_rate": 0.5,
                "repair_recovery_rate": None,
                "final_pass_rate": 0.5,
                "unknown_coverage": 0.0,
                "unknown_is_not_zero": True,
            },
            "family_outcomes": {},
            "dimension_scores": {
                "correctness": {
                    "pass": 1, "fail": 1, "unknown": 0, "observed": 2,
                    "score": 0.5, "weight": 100.0, "unknown_is_not_zero": True,
                }
            },
            "observed_weighted_score": 0.5,
            "challenges": [
                {
                    "id": "MX-E-001", "tier": "Extreme", "family": "x",
                    "status": "FIRST_PASS", "repair_opportunity": False,
                    "dimensions": ["correctness"],
                },
                {
                    "id": "MX-U-001", "tier": "Ultra", "family": "u",
                    "status": "HARD_FAIL", "repair_opportunity": False,
                    "dimensions": ["correctness"],
                },
            ],
        }
        report_path = results / "report.json"
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        return report_path, responses, oracle_sha

    def test_manifest_binds_artifacts_mixed_effort_and_nonpromotion(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            report_path, responses_path, oracle_sha = self._fixture(root)
            manifest = build_manifest(
                repo_root=root,
                report_path=report_path,
                responses_path=responses_path,
                candidate_model="gpt-test-mini",
                evaluation_date="2026-08-20",
                expected_private_oracle_sha256=oracle_sha,
                expected_extreme_count=1,
                expected_ultra_count=1,
            )
            self.assertEqual(verify_manifest(
                repo_root=root, report_path=report_path, responses_path=responses_path, manifest=manifest,
            ), [])
            self.assertEqual(manifest["effort_policy"]["Extreme"]["resolved_effort"], "medium")
            self.assertEqual(manifest["effort_policy"]["Ultra"]["resolved_effort"], "low")
            self.assertEqual(manifest["effort_policy"]["cases"]["MX-U-001"]["resolved_effort"], "low")
            self.assertEqual(
                manifest["transport_policy"]["non_terminal_medium_timeout"],
                "transport_failure_not_model_fail",
            )
            self.assertFalse(manifest["closeout_policy"]["p5_may_be_opened"])
            self.assertFalse(manifest["closeout_policy"]["automatic_policy_activation"])
            rendered = render_summary(json.loads(report_path.read_text(encoding="utf-8")), manifest)
            self.assertIn("1 Extreme at `medium` + 1 Ultra at `low`", rendered)
            self.assertIn("response filename containing `medium`", rendered)
            self.assertTrue(rendered.isascii())
            self.assertIn("` | `tests/model_eval_pack/public/model_extreme_challenges_v1.json`", rendered)

    def test_verifier_detects_dimension_drift_and_artifact_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            report_path, responses_path, oracle_sha = self._fixture(root)
            manifest = build_manifest(
                repo_root=root,
                report_path=report_path,
                responses_path=responses_path,
                candidate_model="gpt-test-mini",
                evaluation_date="2026-08-20",
                expected_private_oracle_sha256=oracle_sha,
                expected_extreme_count=1,
                expected_ultra_count=1,
            )
            responses_path.write_text('{"responses": {"changed": true}}\n', encoding="utf-8")
            errors = verify_manifest(
                repo_root=root, report_path=report_path, responses_path=responses_path, manifest=manifest,
            )
            self.assertIn("artifact hash mismatch: responses", errors)

            report = json.loads(report_path.read_text(encoding="utf-8"))
            report["dimension_scores"]["correctness"]["score"] = 0.25
            self.assertTrue(any("dimension_scores.correctness.score" in item for item in verify_report(report)))


if __name__ == "__main__":
    unittest.main()
