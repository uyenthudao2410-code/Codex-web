from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from coding_tools_mcp.errors import ToolFailure
from coding_tools_mcp.server import Runtime


class AgentWorkflowIdempotencyTests(unittest.TestCase):
    @staticmethod
    def _result() -> dict:
        return {
            "workflow": "feature",
            "phase": "execute",
            "execution": {"ok": True, "status": "passed", "proof_summary": {"proof_fingerprint": "proof-a"}},
            "orchestration": {"run_id": "run-a", "wave_id": "wave-a", "orchestration_state": "ACCEPTING", "reports": {}},
            "external_review": {"status": "skipped"},
        }

    def test_duplicate_execute_is_not_reinvoked_after_runtime_recreation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            args = {"workflow": "feature", "phase": "execute", "objective": "bounded", "idempotency_key": "stable-op"}
            first = Runtime(root)
            first._agent_workflow_impl = MagicMock(return_value=self._result())
            result = first.agent_workflow(args)
            self.assertTrue(result["durable_idempotency"])
            first._agent_workflow_impl.assert_called_once()
            first.close()

            restored = Runtime(root)
            restored._agent_workflow_impl = MagicMock(side_effect=AssertionError("duplicate execution"))
            duplicate = restored.agent_workflow(args)
            self.assertTrue(duplicate["deduplicated"])
            self.assertTrue(duplicate["durable_idempotency"])
            restored._agent_workflow_impl.assert_not_called()
            restored.close()

    def test_key_reuse_with_different_request_is_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            runtime._agent_workflow_impl = MagicMock(return_value=self._result())
            runtime.agent_workflow({"workflow": "feature", "phase": "execute", "objective": "one", "idempotency_key": "same-key"})
            with self.assertRaises(ToolFailure) as conflict:
                runtime.agent_workflow({"workflow": "feature", "phase": "execute", "objective": "two", "idempotency_key": "same-key"})
            self.assertEqual(conflict.exception.code, "IDEMPOTENCY_CONFLICT")
            runtime.close()

    def test_unknown_outcome_fails_closed_instead_of_replaying(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            args = {"workflow": "feature", "phase": "execute", "objective": "may mutate", "idempotency_key": "unknown-op"}
            runtime = Runtime(root)
            runtime._agent_workflow_impl = MagicMock(side_effect=RuntimeError("crash after possible side effect"))
            with self.assertRaises(RuntimeError):
                runtime.agent_workflow(args)
            self.assertEqual(runtime.orchestration_ledger.get_idempotency("unknown-op")["status"], "unknown")
            runtime.close()

            restored = Runtime(root)
            restored._agent_workflow_impl = MagicMock(side_effect=AssertionError("must not replay unknown"))
            with self.assertRaises(ToolFailure) as unknown:
                restored.agent_workflow(args)
            self.assertEqual(unknown.exception.code, "IDEMPOTENCY_OUTCOME_UNKNOWN")
            restored._agent_workflow_impl.assert_not_called()
            restored.close()

    def test_admission_budget_rejects_oversized_plan_before_execution(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            runtime._agent_workflow_impl = MagicMock(side_effect=AssertionError("budget should reject first"))
            with self.assertRaises(ToolFailure) as budget:
                runtime.agent_workflow({
                    "workflow": "feature",
                    "phase": "execute",
                    "objective": "too much",
                    "files": [{"path": f"f{i}.txt", "content": "x"} for i in range(4)],
                    "max_auto_steps": 2,
                })
            self.assertEqual(budget.exception.code, "WORKFLOW_BUDGET_EXCEEDED")
            runtime._agent_workflow_impl.assert_not_called()
            runtime.close()


if __name__ == "__main__":
    unittest.main()
