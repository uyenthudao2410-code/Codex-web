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
                objective="deep behavior narrowed",
            )
            self.assertEqual(ctx.state, "PREFLIGHT")
            self.assertNotEqual(ctx.wave_id, old_wave)
            waves = ledger.list_waves(ctx.run_id)
            self.assertEqual(len(waves), 2)
            first = ledger.wave_objective_provenance(ctx.run_id, old_wave)
            second = ledger.wave_objective_provenance(ctx.run_id, ctx.wave_id)
            self.assertEqual(first["effective_objective"], "deep behavior")
            self.assertEqual(first["objective_revision"], 1)
            self.assertEqual(first["objective_source"], "run_initial_objective")
            self.assertTrue(first["objective_hash_valid"])
            self.assertEqual(second["effective_objective"], "deep behavior narrowed")
            self.assertEqual(second["objective_revision"], 2)
            self.assertEqual(second["objective_source"], "replan_request")
            self.assertTrue(second["objective_changed_from_previous"])
            self.assertTrue(second["objective_hash_valid"])

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
            lease = control.acquire_write_lease(
                ctx,
                owner="MCP",
                mode="mcp_only",
                owner_session="session-a",
                source_fingerprint="source-a",
                runtime_worktree_fingerprint="runtime-a",
                allowed_paths=["app.py"],
                protected_paths=[".coding-tools", ".git"],
                existing_dirty_source_paths=["known.py"],
            )

            recovered = OrchestrationControl(root, OrchestrationLedger(root)).recover(ctx.run_id)
            self.assertIsNotNone(recovered)
            assert recovered is not None
            self.assertEqual(recovered.state, "EXECUTING")
            self.assertIsNotNone(recovered.write_lease)
            self.assertEqual(recovered.write_lease.lease_id, lease.lease_id)
            self.assertEqual(recovered.write_lease.owner_session, "session-a")
            self.assertEqual(recovered.write_lease.source_fingerprint, "source-a")
            self.assertEqual(recovered.write_lease.runtime_worktree_fingerprint, "runtime-a")
            self.assertEqual(recovered.write_lease.allowed_paths, ("app.py",))
            self.assertEqual(recovered.write_lease.existing_dirty_source_paths, ("known.py",))


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
            lease = control.acquire_write_lease(ctx, owner="MCP", mode="mcp_only", ttl_seconds=1.0)
            before = lease.expires_at
            renewed = control.renew_write_lease(ctx, owner="MCP", ttl_seconds=2.0)
            self.assertGreater(renewed.expires_at, before)
            time.sleep(2.1)
            with self.assertRaises(OrchestrationControlError) as expired:
                control.assert_write_allowed(ctx, owner="MCP")
            self.assertEqual(expired.exception.code, "WRITE_LEASE_EXPIRED")

    def test_write_lease_enforces_session_source_dirty_and_protected_scope(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            control = OrchestrationControl(root, ledger)
            ctx = control.begin(objective="source fence", task_id="source-fence", execution_mode="mcp_only", base_head="base", worktree_fp="source-a")
            control.mark_ready(ctx)
            control.select_route(ctx, {"requested": "auto", "selected": "deterministic"})
            control.acquire_write_lease(
                ctx,
                owner="MCP",
                mode="mcp_only",
                owner_session="session-a",
                source_fingerprint="source-a",
                runtime_worktree_fingerprint="source-a",
                allowed_paths=["app.py"],
                existing_dirty_source_paths=["known.py"],
            )
            control.assert_write_allowed(
                ctx,
                owner="MCP",
                owner_session="session-a",
                paths=["app.py"],
                base_head="base",
                source_fingerprint="source-a",
                runtime_worktree_fingerprint="source-a",
                dirty_source_paths=["known.py"],
            )
            with self.assertRaises(OrchestrationControlError) as wrong_session:
                control.assert_write_allowed(ctx, owner="MCP", owner_session="session-b")
            self.assertEqual(wrong_session.exception.code, "WRITE_SESSION_MISMATCH")
            with self.assertRaises(OrchestrationControlError) as foreign_dirty:
                control.assert_write_allowed(
                    ctx,
                    owner="MCP",
                    owner_session="session-a",
                    source_fingerprint="source-b",
                    runtime_worktree_fingerprint="source-b",
                    dirty_source_paths=["known.py", "foreign.py"],
                )
            self.assertEqual(foreign_dirty.exception.code, "FOREIGN_DIRTY_SOURCE")
            self.assertEqual(foreign_dirty.exception.details["foreign_dirty_source_paths"], ["foreign.py"])
            with self.assertRaises(OrchestrationControlError) as source_drift:
                control.assert_write_allowed(
                    ctx,
                    owner="MCP",
                    owner_session="session-a",
                    source_fingerprint="source-b",
                    runtime_worktree_fingerprint="source-b",
                    dirty_source_paths=["known.py"],
                )
            self.assertEqual(source_drift.exception.code, "SOURCE_DRIFT")
            with self.assertRaises(OrchestrationControlError) as protected:
                control.assert_write_allowed(
                    ctx,
                    owner="MCP",
                    owner_session="session-a",
                    paths=[".coding-tools/state.json"],
                    source_fingerprint="source-a",
                    runtime_worktree_fingerprint="source-a",
                    dirty_source_paths=["known.py"],
                )
            self.assertEqual(protected.exception.code, "PROTECTED_PATH_WRITE")
            with self.assertRaises(OrchestrationControlError) as protected_casefold:
                control.assert_write_allowed(
                    ctx,
                    owner="MCP",
                    owner_session="session-a",
                    paths=[".GIT/config"],
                    source_fingerprint="source-a",
                    runtime_worktree_fingerprint="source-a",
                    dirty_source_paths=["known.py"],
                )
            self.assertEqual(protected_casefold.exception.code, "PROTECTED_PATH_WRITE")
            with self.assertRaises(OrchestrationControlError) as scope:
                control.assert_write_allowed(
                    ctx,
                    owner="MCP",
                    owner_session="session-a",
                    paths=["other.py"],
                    source_fingerprint="source-a",
                    runtime_worktree_fingerprint="source-a",
                    dirty_source_paths=["known.py"],
                )
            self.assertEqual(scope.exception.code, "WRITE_SCOPE_VIOLATION")


if __name__ == "__main__":
    unittest.main()
