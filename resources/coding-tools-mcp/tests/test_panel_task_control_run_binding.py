from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from coding_tools_mcp.server import Runtime
from coding_tools_mcp.task_state import TaskStateStore


def _prepare(runtime: Runtime, path: str, objective: str) -> str:
    result = runtime.call_tool("agent_workflow", {
        "workflow": "diagnose",
        "phase": "prepare",
        "path": path,
        "objective": objective,
        "execution_route": "deterministic",
        "execution_mode": "mcp_only",
        "verification": "none",
    })
    assert not result.get("isError"), result
    return str(result["structuredContent"]["orchestration"]["run_id"])


def _make_runtime(base: Path, with_authorized: bool):
    primary = base / "primary"
    primary.mkdir()
    authorized = base / "authorized"
    roots: list[str] = []
    if with_authorized:
        authorized.mkdir()
        roots = [str(authorized)]
    env = {
        "CODING_TOOLS_MCP_TOOL_MODE": "smart",
        "CODING_TOOLS_MCP_AUTHORIZED_ROOTS": json.dumps(roots),
    }
    with patch.dict(os.environ, env):
        runtime = Runtime(primary)
    return runtime, primary, authorized


class PanelTaskControlRunBindingTests(unittest.TestCase):
    def test_stop_with_explicit_run_aborts_only_that_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            runtime, primary, authorized = _make_runtime(base, True)
            try:
                run_primary = _prepare(runtime, str(primary), "primary run")
                run_authorized = _prepare(runtime, str(authorized), "authorized run")
                stopped = runtime.call_tool("task_control", {"action": "stop", "run_id": run_primary})
                self.assertFalse(stopped.get("isError"), stopped)
                ctx = runtime.orchestration_control.snapshot(run_primary)
                self.assertIsNotNone(ctx)
                assert ctx is not None
                self.assertEqual(ctx.state, "ABORTED")
                other = runtime._orchestration_ledger_for_root(authorized.resolve()).get_run(run_authorized)
                self.assertIsInstance(other, dict)
                assert isinstance(other, dict)
                self.assertNotEqual(str(other.get("status") or ""), "aborted")
            finally:
                runtime.close()

    def test_pause_with_explicit_run_acts_on_that_run_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            runtime, primary, authorized = _make_runtime(base, True)
            try:
                run_primary = _prepare(runtime, str(primary), "primary run")
                run_authorized = _prepare(runtime, str(authorized), "authorized run")
                before = TaskStateStore(primary).get().get("status")
                paused = runtime.call_tool("task_control", {"action": "pause", "run_id": run_authorized})
                self.assertFalse(paused.get("isError"), paused)
                self.assertEqual(TaskStateStore(authorized).get().get("status"), "paused")
                self.assertEqual(TaskStateStore(primary).get().get("status"), before)
            finally:
                runtime.close()

    def test_resume_with_explicit_run_reactivates_that_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            runtime, primary, authorized = _make_runtime(base, True)
            try:
                _prepare(runtime, str(primary), "primary run")
                run_authorized = _prepare(runtime, str(authorized), "authorized run")
                paused = runtime.call_tool("task_control", {"action": "pause", "run_id": run_authorized})
                self.assertFalse(paused.get("isError"), paused)
                resumed = runtime.call_tool("task_control", {"action": "resume", "run_id": run_authorized})
                self.assertFalse(resumed.get("isError"), resumed)
                self.assertEqual(TaskStateStore(authorized).get().get("status"), "active")
            finally:
                runtime.close()

    def test_clear_with_explicit_run_clears_only_that_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            runtime, primary, authorized = _make_runtime(base, True)
            try:
                _prepare(runtime, str(primary), "primary run")
                run_authorized = _prepare(runtime, str(authorized), "authorized run")
                cleared = runtime.call_tool("task_control", {"action": "clear", "run_id": run_authorized})
                self.assertFalse(cleared.get("isError"), cleared)
                self.assertFalse(TaskStateStore._has_task(TaskStateStore(authorized).get()))
                self.assertTrue(TaskStateStore._has_task(TaskStateStore(primary).get()))
            finally:
                runtime.close()

    def test_no_run_id_mutation_with_multiple_roots_refuses_and_changes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            runtime, primary, _authorized = _make_runtime(base, True)
            try:
                _prepare(runtime, str(primary), "primary run")
                before_status = TaskStateStore(primary).get().get("status")
                before_task = TaskStateStore(primary).get().get("task_id")
                refused = runtime.call_tool("task_control", {"action": "pause"})
                self.assertTrue(refused.get("isError"), refused)
                self.assertEqual(
                    refused["structuredContent"]["error"]["code"],
                    "WORKSPACE_TARGET_REQUIRED",
                )
                self.assertEqual(TaskStateStore(primary).get().get("status"), before_status)
                self.assertEqual(TaskStateStore(primary).get().get("task_id"), before_task)
            finally:
                runtime.close()

    def test_unknown_run_id_mutation_refuses_and_changes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            runtime, primary, _authorized = _make_runtime(base, True)
            try:
                _prepare(runtime, str(primary), "primary run")
                before_status = TaskStateStore(primary).get().get("status")
                refused = runtime.call_tool(
                    "task_control",
                    {"action": "pause", "run_id": "0123456789abcdef0123456789abcdef"},
                )
                self.assertTrue(refused.get("isError"), refused)
                self.assertEqual(
                    refused["structuredContent"]["error"]["code"],
                    "WORKSPACE_TARGET_REQUIRED",
                )
                self.assertEqual(TaskStateStore(primary).get().get("status"), before_status)
            finally:
                runtime.close()

    def test_no_run_id_pause_with_single_root_keeps_primary_back_compat(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            runtime, primary, _authorized = _make_runtime(base, False)
            try:
                _prepare(runtime, str(primary), "primary run")
                paused = runtime.call_tool("task_control", {"action": "pause"})
                self.assertFalse(paused.get("isError"), paused)
                self.assertEqual(TaskStateStore(primary).get().get("status"), "paused")
            finally:
                runtime.close()


if __name__ == "__main__":
    unittest.main()
