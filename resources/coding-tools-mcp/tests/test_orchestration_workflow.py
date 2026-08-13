from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parents[1]
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from coding_tools_mcp.errors import ToolFailure
from coding_tools_mcp.server import Runtime


class OrchestrationWorkflowIntegrationTests(unittest.TestCase):
    def test_coordination_unavailable_forces_replan_and_explicit_new_wave(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
            runtime = Runtime(root, permission_mode="dangerous")
            blocked = runtime.agent_workflow({
                "workflow": "feature",
                "phase": "run",
                "objective": "change value",
                "execution_mode": "coordinated_multi_worktree",
                "verification": "none",
            })
            self.assertEqual(blocked["orchestration"]["orchestration_state"], "REPLAN")
            self.assertEqual(blocked["execution"]["reason"], "SUPERVISOR_NOT_READY")

            with self.assertRaises(ToolFailure) as missing_reason:
                runtime.agent_workflow({
                    "workflow": "feature",
                    "phase": "execute",
                    "objective": "change value",
                    "execution_mode": "mcp_only",
                    "patch": "*** Begin Patch\n*** Update File: app.py\n@@\n-VALUE = 1\n+VALUE = 2\n*** End Patch",
                    "verification": "none",
                })
            self.assertEqual(missing_reason.exception.code, "REPLAN_REASON_REQUIRED")

            result = runtime.agent_workflow({
                "workflow": "feature",
                "phase": "execute",
                "objective": "change value",
                "execution_mode": "mcp_only",
                "replan_reason": "coordination adapter is unavailable; use one deterministic writer",
                "patch": "*** Begin Patch\n*** Update File: app.py\n@@\n-VALUE = 1\n+VALUE = 2\n*** End Patch",
                "verification": "none",
                "include_diff": False,
            })
            self.assertEqual(result["orchestration"]["orchestration_state"], "ACCEPTING")
            audit = runtime.task_control({"action": "audit", "run_id": result["orchestration"]["run_id"], "limit": 100})
            self.assertEqual(len(audit["audit"]["waves"]), 2)
            self.assertTrue(audit["audit"]["integrity"]["ok"])
            runtime.close()

    def test_reject_requires_reason_and_keeps_same_run_in_replan(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
            runtime = Runtime(root, permission_mode="dangerous")
            result = runtime.agent_workflow({
                "workflow": "bugfix",
                "phase": "execute",
                "objective": "change value",
                "patch": "*** Begin Patch\n*** Update File: app.py\n@@\n-VALUE = 1\n+VALUE = 2\n*** End Patch",
                "verification": "none",
                "include_diff": False,
            })
            run_id = result["orchestration"]["run_id"]
            with self.assertRaises(ToolFailure) as missing_reason:
                runtime.task_control({"action": "reject", "run_id": run_id})
            self.assertEqual(missing_reason.exception.code, "REJECTION_REASON_REQUIRED")
            rejected = runtime.task_control({"action": "reject", "run_id": run_id, "reason": "adjacent invariant still under-proven"})
            self.assertTrue(rejected["rejected"])
            self.assertEqual(rejected["orchestration"]["orchestration_state"], "REPLAN")
            self.assertEqual(rejected["orchestration"]["run_id"], run_id)
            runtime.close()


if __name__ == "__main__":
    unittest.main()
