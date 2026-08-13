from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from coding_tools_mcp.orchestration_control import OrchestrationControl, OrchestrationControlError
from coding_tools_mcp.orchestration_ledger import OrchestrationLedger


class OrchestrationControlTests(unittest.TestCase):
    def test_state_authority_and_acceptance_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            control = OrchestrationControl(root, ledger)
            ctx = control.begin(
                objective="ship one behavior",
                task_id="task-1",
                execution_mode="mcp_only",
                base_head="abc",
                worktree_fp="fp",
            )
            control.mark_ready(ctx)
            route = {"requested": "auto", "selected": "deterministic", "reason": "known_change"}
            control.select_route(ctx, route)
            lease = control.acquire_write_lease(ctx, owner="MCP", mode="mcp_only", allowed_paths=["app.py"])
            self.assertTrue(lease.lease_id)
            control.assert_write_allowed(ctx, owner="MCP", paths=["app.py"], base_head="abc", worktree_fp="fp")
            with self.assertRaises(OrchestrationControlError) as wrong_owner:
                control.assert_write_allowed(ctx, owner="CODEX:lane")
            self.assertEqual(wrong_owner.exception.code, "WRITE_OWNER_MISMATCH")
            control.begin_proof(ctx)
            self.assertIsNone(ctx.write_lease)
            control.mark_accepting(ctx, proof_summary={"proof": "green"})
            control.checkpoint(ctx)
            self.assertEqual(ctx.state, "CHECKPOINTED")
            self.assertTrue(ledger.verify_chain(ctx.run_id)["ok"])

    def test_failure_revokes_lease_and_requires_new_wave(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            control = OrchestrationControl(root, ledger)
            ctx = control.begin(
                objective="deep behavior",
                task_id="task-2",
                execution_mode="deep_single_lane",
                base_head="abc",
                worktree_fp="fp",
            )
            control.mark_ready(ctx)
            control.select_route(ctx, {"requested": "sol_xhigh", "selected": "sol_xhigh"})
            control.acquire_write_lease(ctx, owner="MCP", mode="deep_single_lane")
            failure_class = control.record_failure(ctx, "DEADLINE")
            self.assertEqual(failure_class, "DEADLINE")
            self.assertEqual(ctx.state, "REPLAN")
            self.assertIsNone(ctx.write_lease)
            old_wave = ctx.wave_id
            control.begin_replan_wave(
                ctx,
                execution_mode="deep_single_lane",
                base_head="abc",
                worktree_fp="fp-2",
                contract_fp="",
                reason="split behavior packet",
            )
            self.assertEqual(ctx.state, "PREFLIGHT")
            self.assertNotEqual(ctx.wave_id, old_wave)
            self.assertEqual(len(ledger.list_waves(ctx.run_id)), 2)

    def test_recovery_reconstructs_active_write_lease(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            control = OrchestrationControl(root, ledger)
            ctx = control.begin(
                objective="recover",
                task_id="task-3",
                execution_mode="mcp_only",
                base_head="base",
                worktree_fp="work",
            )
            control.mark_ready(ctx)
            control.select_route(ctx, {"requested": "auto", "selected": "deterministic"})
            lease = control.acquire_write_lease(ctx, owner="MCP", mode="mcp_only")

            recovered = OrchestrationControl(root, OrchestrationLedger(root)).recover(ctx.run_id)
            self.assertIsNotNone(recovered)
            assert recovered is not None
            self.assertEqual(recovered.state, "EXECUTING")
            self.assertIsNotNone(recovered.write_lease)
            self.assertEqual(recovered.write_lease.lease_id, lease.lease_id)


if __name__ == "__main__":
    unittest.main()
