from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from coding_tools_mcp.orchestration_control import OrchestrationControl
from coding_tools_mcp.orchestration_ledger import OrchestrationLedger
from coding_tools_mcp.truth_snapshot import build_truth_snapshot, match_state


class ExecutableEngineeringCasebookTests(unittest.TestCase):
    """Deterministic regressions for accepted Coding Web engineering lessons."""

    def test_case_01_replan_changes_wave_objective_without_rewriting_run_history(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            control = OrchestrationControl(root, ledger)
            ctx = control.begin(
                objective="Build NSIS package",
                task_id="casebook-objective-provenance",
                execution_mode="deep_single_lane",
                base_head="abc",
                worktree_fp="fp-1",
            )
            control.mark_ready(ctx)
            control.select_route(ctx, {"requested": "sol_xhigh", "selected": "sol_xhigh"})
            control.acquire_write_lease(ctx, owner="MCP", mode="deep_single_lane")
            failure_class = control.record_failure(ctx, "DEADLINE")
            self.assertEqual(failure_class, "DEADLINE")
            self.assertEqual(ctx.state, "REPLAN")

            control.begin_replan_wave(
                ctx,
                execution_mode="deep_single_lane",
                base_head="abc",
                worktree_fp="fp-2",
                contract_fp="",
                reason="replace packaging objective with provenance-only repair",
                objective="Verify wave objective provenance only",
            )

            run = ledger.get_run(ctx.run_id)
            provenance = ledger.wave_objective_provenance(ctx.run_id, wave_id=ctx.wave_id)
            self.assertEqual(run["objective"], "Build NSIS package")
            self.assertEqual(provenance["effective_objective"], "Verify wave objective provenance only")
            self.assertEqual(provenance["objective_revision"], 2)
            self.assertTrue(provenance["objective_changed_from_previous"])
            self.assertTrue(provenance["objective_hash_valid"])
            self.assertEqual(provenance["objective_source"], "replan_request")

    def test_case_02_mismatch_and_missing_package_evidence_never_become_green(self) -> None:
        snapshot = build_truth_snapshot(
            source={
                "base_head": "source-new",
                "source_fingerprint": "fp-source",
                "dirty_source_paths": ["renderer/panel.js"],
            },
            runtime_identity={
                "runtime_version": "0.4.3",
                "process_instance_id": "process",
                "server_instance_id": "server",
                "code_revision": "runtime-old",
                "tool_contract": {"profile": "smart-v3", "tool_count": 8},
            },
            orchestration={
                "run_id": "run",
                "wave_id": "wave",
                "state": "ACCEPTING",
                "base_head": "source-new",
                "worktree_fp": "fp-source",
            },
            objective={
                "run_initial_objective": "initial",
                "effective_objective": "current",
                "objective_revision": 2,
                "objective_hash_valid": True,
            },
            proof={"proof_id": "proof", "status": "passed"},
            checkpoint={},
            package=None,
        )

        self.assertEqual(snapshot["comparisons"]["runtime_code_vs_source_head"], "MISMATCHED")
        self.assertEqual(snapshot["comparisons"]["wave_base_vs_source_head"], "MATCHED")
        self.assertEqual(snapshot["comparisons"]["wave_worktree_vs_source_worktree"], "MATCHED")
        self.assertEqual(snapshot["package"]["state"], "UNKNOWN")
        self.assertEqual(snapshot["comparisons"]["package_revision_vs_source_head"], "UNKNOWN")
        self.assertTrue(snapshot["source"]["dirty"])

    def test_case_03_unknown_and_not_applicable_are_distinct_claim_states(self) -> None:
        self.assertEqual(match_state(None, "expected"), "UNKNOWN")
        self.assertEqual(match_state("", "expected"), "UNKNOWN")
        self.assertEqual(match_state("observed", None), "UNKNOWN")
        self.assertEqual(match_state("observed", "expected", applicable=False), "NOT_APPLICABLE")
        self.assertNotEqual(match_state(None, "expected"), "MATCHED")
        self.assertNotEqual(match_state("observed", "expected", applicable=False), "MATCHED")


if __name__ == "__main__":
    unittest.main()
