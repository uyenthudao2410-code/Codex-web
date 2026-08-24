from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from coding_tools_mcp.orchestration_control import OrchestrationControlError
from coding_tools_mcp.server import Runtime


def _routed(control, *, objective: str):
    context = control.begin(
        objective=objective,
        task_id=f"task-{objective}",
        execution_mode="mcp_only",
        base_head="head-1",
        worktree_fp=f"fp-{objective}",
        metadata={"workspace_identity": {"workspace_id": objective, "root_id": objective}},
    )
    control.mark_ready(context)
    control.select_route(
        context,
        {"requested": "deterministic", "selected": "deterministic", "reason": "test"},
    )
    return context


class MultiWorkspaceLifecycleTests(unittest.TestCase):
    def test_different_workspace_ledgers_allow_concurrent_write_leases(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            primary = base / "primary"
            authorized = base / "authorized"
            primary.mkdir()
            authorized.mkdir()
            with patch.dict(os.environ, {
                "CODING_TOOLS_MCP_TOOL_MODE": "smart",
                "CODING_TOOLS_MCP_AUTHORIZED_ROOTS": json.dumps([str(authorized)]),
            }):
                runtime = Runtime(primary)
            try:
                primary_control = runtime.orchestration_control
                primary_context = _routed(primary_control, objective="primary")
                primary_lease = primary_control.acquire_write_lease(
                    primary_context,
                    owner="writer-primary",
                    mode="test",
                )

                runtime.request_context.workspace_root = str(authorized.resolve())
                authorized_control = runtime.orchestration_control
                authorized_context = _routed(authorized_control, objective="authorized")
                authorized_lease = authorized_control.acquire_write_lease(
                    authorized_context,
                    owner="writer-authorized",
                    mode="test",
                )

                self.assertNotEqual(primary_lease.lease_id, authorized_lease.lease_id)
                self.assertIsNot(primary_control.ledger, authorized_control.ledger)
                self.assertEqual(primary_control.ledger.get_run(primary_context.run_id)["metadata"]["workspace_identity"]["workspace_id"], "primary")
                self.assertEqual(authorized_control.ledger.get_run(authorized_context.run_id)["metadata"]["workspace_identity"]["workspace_id"], "authorized")
            finally:
                if hasattr(runtime.request_context, "workspace_root"):
                    del runtime.request_context.workspace_root
                runtime.close()

    def test_same_workspace_ledger_rejects_second_write_lease(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = Runtime(root)
            second = Runtime(root)
            try:
                first_context = _routed(first.orchestration_control, objective="same-root-first")
                first.orchestration_control.acquire_write_lease(
                    first_context,
                    owner="writer-one",
                    mode="test",
                )
                second_context = _routed(second.orchestration_control, objective="same-root-second")
                with self.assertRaises(OrchestrationControlError) as failure:
                    second.orchestration_control.acquire_write_lease(
                        second_context,
                        owner="writer-two",
                        mode="test",
                    )
                self.assertEqual(failure.exception.code, "WRITE_LEASE_CONFLICT")
            finally:
                second.close()
                first.close()


if __name__ == "__main__":
    unittest.main()
