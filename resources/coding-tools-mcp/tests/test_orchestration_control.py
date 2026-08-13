from __future__ import annotations

import tempfile
import time
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


    def test_workspace_fence_blocks_concurrent_writer_and_increments_after_release(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            first_control = OrchestrationControl(root, ledger)
            first = first_control.begin(objective="first", task_id="t1", execution_mode="mcp_only", base_head="a", worktree_fp="w1")
            first_control.mark_ready(first)
            first_control.select_route(first, {"requested": "auto", "selected": "deterministic"})
            lease1 = first_control.acquire_write_lease(first, owner="MCP", mode="mcp_only")
            self.assertEqual(lease1.fencing_token, 1)

            second_control = OrchestrationControl(root, OrchestrationLedger(root))
            second = second_control.begin(objective="second", task_id="t2", execution_mode="mcp_only", base_head="a", worktree_fp="w2")
            second_control.mark_ready(second)
            second_control.select_route(second, {"requested": "auto", "selected": "deterministic"})
            with self.assertRaises(OrchestrationControlError) as conflict:
                second_control.acquire_write_lease(second, owner="MCP-2", mode="mcp_only")
            self.assertEqual(conflict.exception.code, "WRITE_LEASE_CONFLICT")

            first_control.revoke_write_lease(first, reason="handoff")
            lease2 = second_control.acquire_write_lease(second, owner="MCP-2", mode="mcp_only")
            self.assertEqual(lease2.fencing_token, 2)

            first.write_lease = lease1
            first.state = "EXECUTING"
            with self.assertRaises(OrchestrationControlError) as stale:
                first_control.assert_write_allowed(first, owner="MCP")
            self.assertEqual(stale.exception.code, "STALE_WRITE_FENCE")

    def test_write_lease_expiry_and_renewal_are_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            control = OrchestrationControl(root, ledger)
            ctx = control.begin(objective="ttl", task_id="ttl", execution_mode="mcp_only", base_head="a", worktree_fp="w")
            control.mark_ready(ctx)
            control.select_route(ctx, {"requested": "auto", "selected": "deterministic"})
            lease = control.acquire_write_lease(ctx, owner="MCP", mode="mcp_only", ttl_seconds=0.08)
            before = lease.expires_at
            renewed = control.renew_write_lease(ctx, owner="MCP", ttl_seconds=0.15)
            self.assertGreater(renewed.expires_at, before)
            time.sleep(0.18)
            with self.assertRaises(OrchestrationControlError) as expired:
                control.assert_write_allowed(ctx, owner="MCP")
            self.assertEqual(expired.exception.code, "WRITE_LEASE_EXPIRED")


if __name__ == "__main__":
    unittest.main()
