from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

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

    def test_patch_preflight_failure_is_known_terminal_without_run_or_write(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "a.py").write_text("A = 1\n", encoding="utf-8")
            (root / "b.py").write_text("VALUE = 1\nVALUE = 1\n", encoding="utf-8")
            runtime = Runtime(root, permission_mode="dangerous")
            args = {
                "workflow": "bugfix",
                "phase": "execute",
                "execution_route": "deterministic",
                "idempotency_key": "known-preflight-failure",
                "patches": [
                    "*** Begin Patch\n*** Update File: a.py\n@@\n-A = 1\n+A = 2\n*** End Patch",
                    "*** Begin Patch\n*** Update File: b.py\n@@\n-VALUE = 1\n+VALUE = 2\n*** End Patch",
                ],
                "verification": "none",
            }
            try:
                with self.assertRaises(ToolFailure) as caught:
                    runtime.agent_workflow(args)
                self.assertEqual(caught.exception.code, "PATCH_CONTEXT_AMBIGUOUS")
                record = runtime.orchestration_ledger.get_idempotency("known-preflight-failure")
                self.assertEqual(record["status"], "failed")
                self.assertFalse(record["summary"]["outcome_unknown"])
                self.assertTrue(record["summary"]["workflow_patch_preflight"])
                self.assertEqual(runtime.orchestration_ledger.list_runs(limit=10), [])
                self.assertEqual((root / "a.py").read_text(encoding="utf-8"), "A = 1\n")
                self.assertEqual((root / "b.py").read_text(encoding="utf-8"), "VALUE = 1\nVALUE = 1\n")

                malformed = {
                    "workflow": "bugfix",
                    "phase": "execute",
                    "execution_route": "deterministic",
                    "idempotency_key": "known-preflight-parse-failure",
                    "patch": "not a patch envelope",
                    "verification": "none",
                }
                with self.assertRaises(ToolFailure) as malformed_error:
                    runtime.agent_workflow(malformed)
                self.assertEqual(malformed_error.exception.code, "PATCH_FAILED")
                parse_record = runtime.orchestration_ledger.get_idempotency("known-preflight-parse-failure")
                self.assertEqual(parse_record["status"], "failed")
                self.assertFalse(parse_record["summary"]["outcome_unknown"])
                self.assertTrue(parse_record["summary"]["workflow_patch_preflight"])
                self.assertEqual(runtime.orchestration_ledger.list_runs(limit=10), [])
            finally:
                runtime.close()

    def test_auto_key_initial_execute_uses_task_epoch_and_new_task_allows_same_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temp, patch.dict(
            "os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}
        ):
            root = Path(temp)
            args = {"workflow": "feature", "phase": "execute", "objective": "same semantic payload"}

            first = Runtime(root)
            first._agent_workflow_impl = MagicMock(return_value=self._result())
            first_result = first.call_tool("agent_workflow", dict(args))["structuredContent"]
            first_key = str((first_result.get("idempotency") or {}).get("idempotency_key") or "")
            first_task_id = str(first.task_state.get().get("task_id") or "")
            self.assertTrue(first_key.startswith("auto-v1:"))
            self.assertTrue(first_task_id)
            first._agent_workflow_impl.assert_called_once()
            first.close()

            restored = Runtime(root)
            restored._agent_workflow_impl = MagicMock(side_effect=AssertionError("same task retry must replay"))
            replay = restored.call_tool("agent_workflow", dict(args))["structuredContent"]
            self.assertTrue(replay.get("deduplicated"))
            self.assertEqual((replay.get("idempotency") or {}).get("idempotency_key"), first_key)
            self.assertEqual(restored.task_state.get().get("task_id"), first_task_id)
            restored._agent_workflow_impl.assert_not_called()
            restored.task_state.update({"status": "completed"})
            restored.close()

            new_task = Runtime(root)
            new_task._agent_workflow_impl = MagicMock(return_value=self._result())
            second_result = new_task.call_tool("agent_workflow", dict(args))["structuredContent"]
            second_key = str((second_result.get("idempotency") or {}).get("idempotency_key") or "")
            second_task_id = str(new_task.task_state.get().get("task_id") or "")
            self.assertTrue(second_key.startswith("auto-v1:"))
            self.assertNotEqual(second_key, first_key)
            self.assertNotEqual(second_task_id, first_task_id)
            new_task._agent_workflow_impl.assert_called_once()
            new_task.close()

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
