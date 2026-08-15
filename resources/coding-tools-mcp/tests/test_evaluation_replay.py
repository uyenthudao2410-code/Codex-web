from __future__ import annotations

import copy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from coding_tools_mcp.evaluation_replay import (
    _attest_trial_accepted_result,
    _paired_eocl_identity_complete,
    build_counterbalanced_plan,
    execute_controlled_replay,
    validate_replay_manifest,
)
from coding_tools_mcp.orchestration_ledger import OrchestrationLedger


class EvaluationReplayTests(unittest.TestCase):
    def manifest(self) -> dict:
        return {
            "schema_version": 1,
            "study_id": "route-study",
            "seed": 73,
            "pair_count": 10,
            "baseline_policy": "chatweb_mcp",
            "candidate_policy": "mini",
            "provenance": "representative",
            "identity": {
                "task_spec_fp": "task-fp",
                "base_head": "a" * 40,
                "contract_fp": "contract-fp",
                "oracle_id": "oracle-1",
                "task_class": "localized_bug",
                "environment_fp": "environment-fp",
                "tool_contract_fp": "tool-fp",
                "evaluation_schema_fp": "evaluation-fp",
                "runtime_version": "0.4.3",
                "cache_stratum": "cold",
            },
        }

    def test_plan_is_deterministic_balanced_and_never_auto_activates(self) -> None:
        first = build_counterbalanced_plan(self.manifest())
        second = build_counterbalanced_plan(self.manifest())
        self.assertEqual(first, second)
        self.assertEqual(first["counterbalance"]["ab_pairs"], 5)
        self.assertEqual(first["counterbalance"]["ba_pairs"], 5)
        self.assertEqual(first["trial_count"], 20)
        self.assertFalse(first["automatic_activation"])
        self.assertTrue(first["promotion_eligible"])
        self.assertEqual(len(first["plan_sha256"]), 64)
        for pair in first["pairs"]:
            self.assertEqual({item["policy"] for item in pair["trials"]}, {"chatweb_mcp", "mini"})
            self.assertEqual({item["evaluation"]["pair_id"] for item in pair["trials"]}, {pair["pair_id"]})

    def test_seed_changes_assignment_without_changing_balance(self) -> None:
        alternate = self.manifest()
        alternate["seed"] = 99
        left = build_counterbalanced_plan(self.manifest())
        right = build_counterbalanced_plan(alternate)
        self.assertEqual(right["counterbalance"]["ab_pairs"], right["counterbalance"]["ba_pairs"])
        self.assertNotEqual([item["order"] for item in left["pairs"]], [item["order"] for item in right["pairs"]])

    def test_odd_pair_count_is_rejected_to_preserve_counterbalance(self) -> None:
        manifest = self.manifest()
        manifest["pair_count"] = 9
        with self.assertRaisesRegex(ValueError, "even integer"):
            build_counterbalanced_plan(manifest)

    def test_synthetic_and_unknown_cache_evidence_are_rejected(self) -> None:
        synthetic = self.manifest()
        synthetic["provenance"] = "synthetic"
        with self.assertRaisesRegex(ValueError, "synthetic replay is intentionally unsupported"):
            validate_replay_manifest(synthetic)
        unknown = self.manifest()
        unknown["identity"]["cache_stratum"] = "unknown"
        with self.assertRaisesRegex(ValueError, "cold or warm"):
            validate_replay_manifest(unknown)

    def test_incomplete_causal_identity_is_rejected(self) -> None:
        manifest = copy.deepcopy(self.manifest())
        manifest["identity"]["oracle_id"] = ""
        with self.assertRaisesRegex(ValueError, "identity.oracle_id"):
            build_counterbalanced_plan(manifest)

    def test_benchmark_plan_is_explicitly_not_promotion_eligible(self) -> None:
        manifest = self.manifest()
        manifest["provenance"] = "benchmark"
        plan = build_counterbalanced_plan(manifest)
        self.assertFalse(plan["promotion_eligible"])
        self.assertFalse(plan["automatic_activation"])

    def test_explicit_executor_uses_fresh_clean_worktree_per_trial_and_never_infers_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            repo.mkdir()

            def git(*args: str) -> subprocess.CompletedProcess[str]:
                return subprocess.run(
                    ["git", "-C", str(repo), *args],
                    check=True,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                )

            git("init")
            (repo / "input.txt").write_text("controlled replay fixture\n", encoding="utf-8")
            git("add", "input.txt")
            subprocess.run(
                [
                    "git", "-C", str(repo),
                    "-c", "user.email=replay-test@example.invalid",
                    "-c", "user.name=Replay Test",
                    "commit", "-m", "fixture",
                ],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            head = git("rev-parse", "HEAD").stdout.strip()
            manifest = self.manifest()
            manifest["pair_count"] = 2
            manifest["identity"]["base_head"] = head
            manifest["source_repo"] = str(repo)
            manifest["command"] = [
                sys.executable,
                "-c",
                "from pathlib import Path; Path('trial-output.txt').write_text('ok', encoding='utf-8')",
            ]
            plan = build_counterbalanced_plan(manifest)
            result = execute_controlled_replay(manifest, plan)
            self.assertTrue(result["infrastructure_complete"])
            self.assertEqual(result["trial_count"], 4)
            self.assertFalse(result["accepted_result_evidence_complete"])
            for trial in result["trials"]:
                self.assertTrue(trial["start_head_verified"])
                self.assertTrue(trial["clean_start_verified"])
                self.assertTrue(trial["cleanup_ok"])
                self.assertEqual(trial["command_exit_code"], 0)
                self.assertIsNone(trial["accepted_result"])
                self.assertEqual(trial["accepted_result_evidence_reason"], "orchestration_ledger_not_found")
                self.assertEqual(trial["acceptance_policy"], "never_infer_acceptance_from_process_exit_code")
                self.assertEqual(len(trial["stdout_sha256"]), 64)
                self.assertEqual(len(trial["stderr_sha256"]), 64)
            self.assertEqual(git("worktree", "list", "--porcelain").stdout.count("worktree "), 1)

    def test_explicit_executor_attests_trial_local_eocl_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            repo.mkdir()

            def git(*args: str) -> subprocess.CompletedProcess[str]:
                return subprocess.run(
                    ["git", "-C", str(repo), *args],
                    check=True,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                )

            git("init")
            package_root = Path(__file__).resolve().parents[1]
            driver = repo / "trial_driver.py"
            driver.write_text(
                "\n".join([
                    "import os, subprocess, sys",
                    f"sys.path.insert(0, {str(package_root)!r})",
                    "from coding_tools_mcp.orchestration_ledger import OrchestrationLedger",
                    "from pathlib import Path",
                    "root = Path.cwd()",
                    "head = subprocess.run(['git', 'rev-parse', 'HEAD'], check=True, capture_output=True, text=True).stdout.strip()",
                    "policy = os.environ['CODING_TOOLS_EVAL_POLICY']",
                    "route = 'deterministic' if policy == 'chatweb_mcp' else policy",
                    "ledger = OrchestrationLedger(root)",
                    "run_id = ledger.create_run(objective='representative replay trial', metadata={'evaluation': {",
                    "    'pair_id': os.environ['CODING_TOOLS_EVAL_PAIR_ID'], 'policy': policy,",
                    "    'replicate_id': os.environ['CODING_TOOLS_EVAL_REPLICATE_ID'], 'order_index': int(os.environ['CODING_TOOLS_EVAL_ORDER_INDEX']),",
                    "    'provenance': 'representative', 'task_spec_fp': 'task-fp', 'oracle_id': 'oracle-1',",
                    "    'task_class': 'localized_bug', 'environment_fp': 'environment-fp', 'tool_contract_fp': 'tool-fp',",
                    "    'evaluation_schema_fp': 'evaluation-fp', 'runtime_version': '0.4.3', 'cache_stratum': 'cold',",
                    "}})",
                    "wave_id = ledger.create_wave(run_id, execution_mode='mcp_only' if route == 'deterministic' else 'bounded_candidate', base_head=head, worktree_fp='clean-source', contract_fp='contract-fp')",
                    "ledger.append_event(run_id, wave_id=wave_id, event_type='route_selected', payload={'requested': policy, 'resolved': route})",
                    "ledger.record_proof(run_id=run_id, wave_id=wave_id, stage_id='oracle', stage_version='1', input_fingerprint='trial-proof', status='passed', duration_ms=1)",
                    "ledger.record_checkpoint(run_id=run_id, wave_id=wave_id, git_head=head, proof_fingerprint='trial-proof')",
                    "ledger.finish_wave(wave_id, status='accepted')",
                    "ledger.finish_run(run_id, status='accepted')",
                ]) + "\n",
                encoding="utf-8",
            )
            (repo / "input.txt").write_text("controlled replay fixture\n", encoding="utf-8")
            git("add", "input.txt", "trial_driver.py")
            subprocess.run(
                ["git", "-C", str(repo), "-c", "user.email=replay-test@example.invalid", "-c", "user.name=Replay Test", "commit", "-m", "fixture"],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            head = git("rev-parse", "HEAD").stdout.strip()
            manifest = self.manifest()
            manifest["pair_count"] = 2
            manifest["identity"]["base_head"] = head
            manifest["source_repo"] = str(repo)
            manifest["command"] = [sys.executable, "trial_driver.py"]
            result = execute_controlled_replay(manifest, build_counterbalanced_plan(manifest))
            self.assertTrue(result["infrastructure_complete"])
            self.assertTrue(result["accepted_result_evidence_complete"])
            self.assertEqual(result["accepted_result_evidence_reason"], "all_trials_attested_by_eocl_ledger")
            for trial in result["trials"]:
                self.assertTrue(trial["accepted_result"]["accepted"])
                self.assertEqual(trial["accepted_result_evidence_reason"], "accepted_eocl_run_attested")
                self.assertEqual(trial["accepted_result"]["route_resolved"], "deterministic" if trial["policy"] == "chatweb_mcp" else trial["policy"])

    def test_trial_attestation_rejects_route_policy_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            manifest = self.manifest()
            ledger = OrchestrationLedger(workspace)
            trial = {
                "pair_id": "route-study-pair-001",
                "replicate_id": "route-study-replicate-001",
                "policy": "mini",
                "order_index": 0,
            }
            run_id = ledger.create_run(objective="wrong route", metadata={"evaluation": {
                "pair_id": trial["pair_id"], "policy": trial["policy"], "replicate_id": trial["replicate_id"], "order_index": 0,
                "provenance": "representative", "task_spec_fp": "task-fp", "oracle_id": "oracle-1", "task_class": "localized_bug",
                "environment_fp": "environment-fp", "tool_contract_fp": "tool-fp", "evaluation_schema_fp": "evaluation-fp",
                "runtime_version": "0.4.3", "cache_stratum": "cold",
            }})
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only", base_head="a" * 40, worktree_fp="clean-source", contract_fp="contract-fp")
            ledger.append_event(run_id, wave_id=wave_id, event_type="route_selected", payload={"requested": "mini", "resolved": "deterministic"})
            ledger.record_proof(run_id=run_id, wave_id=wave_id, stage_id="oracle", stage_version="1", input_fingerprint="proof", status="passed")
            ledger.record_checkpoint(run_id=run_id, wave_id=wave_id, git_head="a" * 40, proof_fingerprint="proof")
            ledger.finish_wave(wave_id, status="accepted")
            ledger.finish_run(run_id, status="accepted")
            accepted, reason = _attest_trial_accepted_result(workspace, validate_replay_manifest(manifest), trial)
            self.assertIsNone(accepted)
            self.assertEqual(reason, "accepted_eocl_route_policy_mismatch")

    def test_paired_eocl_identity_requires_matching_pair_fingerprint(self) -> None:
        matching = [
            {"pair_id": "pair-1", "accepted_result": {"pair_fingerprint": "same"}},
            {"pair_id": "pair-1", "accepted_result": {"pair_fingerprint": "same"}},
        ]
        mismatched = [
            {"pair_id": "pair-1", "accepted_result": {"pair_fingerprint": "first"}},
            {"pair_id": "pair-1", "accepted_result": {"pair_fingerprint": "second"}},
        ]
        self.assertTrue(_paired_eocl_identity_complete(matching))
        self.assertFalse(_paired_eocl_identity_complete(mismatched))
        self.assertFalse(_paired_eocl_identity_complete([{"pair_id": "pair-1", "accepted_result": None}]))


if __name__ == "__main__":
    unittest.main()
