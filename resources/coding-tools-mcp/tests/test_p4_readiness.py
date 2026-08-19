from __future__ import annotations

import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from coding_tools_mcp.orchestration_ledger import OrchestrationLedger


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "report_p4_readiness.py"
SPEC = importlib.util.spec_from_file_location("report_p4_readiness_test_module", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
P4 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P4)


def git(cwd: Path | None, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )


class P4ReadinessTests(unittest.TestCase):
    def test_git_baseline_requires_clean_upstream_matched_head(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            origin = root / "origin.git"
            work = root / "work"
            git(None, "init", "--bare", str(origin))
            git(None, "clone", str(origin), str(work))
            git(work, "config", "user.email", "p4@example.invalid")
            git(work, "config", "user.name", "P4 Test")
            git(work, "config", "core.autocrlf", "false")
            (work / "README.md").write_text("baseline\n", encoding="utf-8")
            git(work, "add", "README.md")
            git(work, "commit", "-m", "baseline")
            git(work, "branch", "-M", "main")
            git(work, "push", "-u", "origin", "main")

            baseline = P4._git_baseline_status(work)
            self.assertTrue(baseline["worktree_clean"])
            self.assertTrue(baseline["upstream_configured"])
            self.assertTrue(baseline["head_matches_upstream"])
            self.assertTrue(baseline["p5_baseline_ready"])

            (work / "README.md").write_text("dirty\n", encoding="utf-8")
            dirty = P4._git_baseline_status(work)
            self.assertFalse(dirty["worktree_clean"])
            self.assertFalse(dirty["p5_baseline_ready"])

    def test_empirical_completion_does_not_open_p5_on_dirty_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            OrchestrationLedger(root).create_run(objective="p4 readiness fixture")
            population = {
                "population_scope": "fixture",
                "scan_limit": 100,
                "scan_limit_semantics": "fixture",
                "cohort": {"shadow_tasks": 1},
                "representative_predictor_variation": {"oracle_strength": False},
                "predictor_coverage": {"oracle_strength": {"low_variance": True}},
                "workload_guidance": {"low_variance_signals": ["oracle_strength"]},
                "measurement_design": {"design": "longitudinal_evolving_checkout_v1", "iid_assumption": False},
                "replan_diagnostics": {"scope": "representative_terminal_runs"},
                "predictive_validation": {"validated_signals": ["expected_repair_risk"]},
                "p4_gate": {"can_answer_which_signals_predict_repair": True},
                "policy": {"p5_automatic_start": False},
            }
            dirty_baseline = {
                "is_repo": True,
                "worktree_clean": False,
                "upstream_configured": True,
                "head_matches_upstream": True,
                "p5_baseline_ready": False,
                "requirement": "clean_upstream_matched_head_v1",
            }
            with patch.object(P4, "solution_shadow_population_report", return_value=population), patch.object(
                P4, "_git_baseline_status", return_value=dirty_baseline
            ):
                report = P4.p4_readiness_report(root)
            self.assertTrue(report["p4_empirically_complete"])
            self.assertFalse(report["p5_baseline_ready"])
            self.assertFalse(report["p5_controlled_treatment_may_be_opened"])
            self.assertEqual(
                report["p5_readiness_requirements"],
                {
                    "p4_gate_can_answer_which_signals_predict_repair": True,
                    "validated_predictive_signal_present": True,
                    "clean_upstream_matched_baseline": False,
                },
            )
            self.assertEqual(report["state"], "EMPIRICALLY_COMPLETE_BASELINE_NOT_READY")
            self.assertEqual(report["predictor_coverage"], population["predictor_coverage"])
            self.assertEqual(report["workload_guidance"], population["workload_guidance"])
            self.assertEqual(report["measurement_design"], population["measurement_design"])
            self.assertEqual(report["replan_diagnostics"], population["replan_diagnostics"])

            clean_baseline = {**dirty_baseline, "worktree_clean": True, "p5_baseline_ready": True}
            with patch.object(P4, "solution_shadow_population_report", return_value=population), patch.object(
                P4, "_git_baseline_status", return_value=clean_baseline
            ):
                ready = P4.p4_readiness_report(root)
            self.assertTrue(ready["p5_controlled_treatment_may_be_opened"])
            self.assertEqual(ready["state"], "EMPIRICALLY_COMPLETE")
            self.assertTrue(all(ready["p5_readiness_requirements"].values()))

    def test_p5_requires_a_validated_predictive_signal_even_if_gate_flag_is_true(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            OrchestrationLedger(root).create_run(objective="p4 readiness fixture")
            population = {
                "cohort": {"shadow_tasks": 1},
                "predictive_validation": {"validated_signals": []},
                "p4_gate": {"can_answer_which_signals_predict_repair": True},
            }
            clean_baseline = {
                "is_repo": True,
                "worktree_clean": True,
                "upstream_configured": True,
                "head_matches_upstream": True,
                "p5_baseline_ready": True,
                "requirement": "clean_upstream_matched_head_v1",
            }
            with patch.object(P4, "solution_shadow_population_report", return_value=population), patch.object(
                P4, "_git_baseline_status", return_value=clean_baseline
            ):
                report = P4.p4_readiness_report(root)
            self.assertFalse(report["p4_empirically_complete"])
            self.assertFalse(report["p5_controlled_treatment_may_be_opened"])
            self.assertEqual(
                report["p5_readiness_requirements"],
                {
                    "p4_gate_can_answer_which_signals_predict_repair": True,
                    "validated_predictive_signal_present": False,
                    "clean_upstream_matched_baseline": True,
                },
            )

    def test_p5_requires_the_p4_predictive_gate_even_when_a_signal_and_baseline_exist(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            OrchestrationLedger(root).create_run(objective="p4 readiness fixture")
            population = {
                "cohort": {"shadow_tasks": 1},
                "predictive_validation": {"validated_signals": ["expected_repair_risk"]},
                "p4_gate": {"can_answer_which_signals_predict_repair": False},
            }
            clean_baseline = {
                "is_repo": True,
                "worktree_clean": True,
                "upstream_configured": True,
                "head_matches_upstream": True,
                "p5_baseline_ready": True,
                "requirement": "clean_upstream_matched_head_v1",
            }
            with patch.object(P4, "solution_shadow_population_report", return_value=population), patch.object(
                P4, "_git_baseline_status", return_value=clean_baseline
            ):
                report = P4.p4_readiness_report(root)
            self.assertFalse(report["p4_empirically_complete"])
            self.assertFalse(report["p5_controlled_treatment_may_be_opened"])
            self.assertEqual(
                report["p5_readiness_requirements"],
                {
                    "p4_gate_can_answer_which_signals_predict_repair": False,
                    "validated_predictive_signal_present": True,
                    "clean_upstream_matched_baseline": True,
                },
            )


if __name__ == "__main__":
    unittest.main()
