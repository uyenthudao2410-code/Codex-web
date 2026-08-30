from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from coding_tools_mcp.mcp_http_handler import MCPHandler
from coding_tools_mcp.server import Runtime
from coding_tools_mcp.truth_snapshot import TRUTH_MATCH_STATES, build_truth_snapshot, match_state


class TruthSnapshotTests(unittest.TestCase):
    def test_match_state_is_fail_closed_and_uses_exact_four_state_vocabulary(self) -> None:
        self.assertEqual(TRUTH_MATCH_STATES, ("MATCHED", "MISMATCHED", "UNKNOWN", "NOT_APPLICABLE"))
        self.assertEqual(match_state("same", "same"), "MATCHED")
        self.assertEqual(match_state("left", "right"), "MISMATCHED")
        self.assertEqual(match_state("", "right"), "UNKNOWN")
        self.assertEqual(match_state(None, "right"), "UNKNOWN")
        self.assertEqual(match_state("left", "right", applicable=False), "NOT_APPLICABLE")

    def test_snapshot_keeps_missing_package_evidence_unknown(self) -> None:
        snapshot = build_truth_snapshot(
            source={
                "base_head": "abc",
                "source_fingerprint": "fp",
                "dirty_source_paths": ["app.py"],
                "observed_at": "2026-08-30T00:00:00+00:00",
                "observation_source": "exact_workspace_identity",
            },
            runtime_identity={"runtime_version": "1", "code_revision": "abc"},
            orchestration={"run_id": "run", "wave_id": "wave", "base_head": "abc", "worktree_fp": "fp"},
            objective={"effective_objective": "do one thing", "objective_revision": 2, "objective_hash_valid": True},
            proof={"proof_id": "proof", "status": "passed"},
            checkpoint={"checkpoint_id": "checkpoint", "status": "accepted"},
        )
        self.assertTrue(snapshot["read_only"])
        self.assertTrue(snapshot["source"]["dirty"])
        self.assertEqual(snapshot["source"]["observed_at"], "2026-08-30T00:00:00+00:00")
        self.assertEqual(snapshot["source"]["observation_source"], "exact_workspace_identity")
        self.assertEqual(snapshot["comparisons"]["runtime_code_vs_source_head"], "MATCHED")
        self.assertEqual(snapshot["comparisons"]["wave_worktree_vs_source_worktree"], "MATCHED")
        self.assertEqual(snapshot["package"]["state"], "UNKNOWN")
        self.assertEqual(snapshot["comparisons"]["package_revision_vs_source_head"], "UNKNOWN")
        self.assertEqual(snapshot["orchestration"]["effective_objective"], "do one thing")
        self.assertEqual(snapshot["orchestration"]["objective_revision"], 2)

    def test_runtime_source_identity_cache_returns_a_memory_only_copy(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp), permission_mode="safe")
            try:
                key = os.path.normcase(os.path.abspath(str(runtime.workspace.root)))
                runtime._orchestration_workspace_identity_cache[key] = {
                    "base_head": "abc",
                    "worktree_fp": "fp",
                    "source_fingerprint": "fp",
                    "dirty_source_paths": [],
                    "observed_at": "2026-08-30T00:00:00+00:00",
                    "observation_source": "exact_workspace_identity",
                }
                first = runtime._cached_orchestration_workspace_identity()
                first["base_head"] = "mutated-copy"
                second = runtime._cached_orchestration_workspace_identity()
                self.assertEqual(second["base_head"], "abc")
                self.assertEqual(second["observation_source"], "exact_workspace_identity")
            finally:
                runtime.close()

    def test_authenticated_orchestration_projection_contains_internal_truth_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temp, patch.dict(os.environ, {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}):
            runtime = Runtime(Path(temp), permission_mode="safe")
            try:
                task = runtime.task_state.ensure_started("truth snapshot active wave")
                ctx = runtime.orchestration_control.begin(
                    objective="truth snapshot active wave",
                    task_id=str(task["task_id"]),
                    execution_mode="mcp_only",
                    base_head="abc",
                    worktree_fp="fp",
                )
                runtime.task_state.set_orchestration_projection(ctx.projection(), event="truth_snapshot_test_linked")
                handler = object.__new__(MCPHandler)
                handler._runtime = runtime
                projection = handler.control_orchestration_snapshot()
                truth = projection["truth_snapshot"]
                self.assertEqual(truth["schema_version"], 1)
                self.assertTrue(truth["read_only"])
                self.assertEqual(truth["runtime"]["process_instance_id"], runtime.process_instance_id)
                self.assertEqual(truth["runtime"]["server_instance_id"], runtime.server_instance_id)
                self.assertEqual(truth["runtime"]["tool_contract"]["tool_count"], 8)
                self.assertEqual(truth["state_vocabulary"], list(TRUTH_MATCH_STATES))
                self.assertEqual(truth["orchestration"]["wave_id"], ctx.wave_id)
                self.assertEqual(truth["orchestration"]["effective_objective"], "truth snapshot active wave")
                self.assertNotIn("auth_token", str(truth).lower())
            finally:
                runtime.close()


if __name__ == "__main__":
    unittest.main()
