from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from coding_tools_mcp.errors import ToolFailure
from coding_tools_mcp.server import Runtime, validate_arguments


class UniversalIdempotencyTests(unittest.TestCase):
    @staticmethod
    def _accepting_run(runtime: Runtime):
        state = runtime.task_state.ensure_started("idempotency acceptance fixture")
        identity = runtime._orchestration_workspace_identity(".")
        ctx = runtime.orchestration_control.begin(
            objective="idempotency acceptance fixture",
            task_id=str(state.get("task_id") or ""),
            execution_mode="mcp_only",
            base_head=str(identity.get("base_head") or ""),
            worktree_fp=str(identity.get("worktree_fp") or ""),
        )
        runtime.orchestration_control.mark_ready(ctx)
        runtime.orchestration_control.select_route(
            ctx,
            {"requested": "deterministic", "selected": "deterministic", "reason": "test_fixture"},
        )
        runtime.orchestration_control.acquire_write_lease(ctx, owner="MCP", mode="mcp_only")
        runtime.orchestration_control.begin_proof(ctx)
        runtime.orchestration_control.mark_accepting(ctx, proof_summary={"proof": "green"})
        runtime.task_state.set_orchestration_projection(ctx.projection(), event="test_accepting_projection")
        return ctx

    def test_required_task_control_accept_duplicate_replays_without_second_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as temp, patch.dict(
            "os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}
        ):
            runtime = Runtime(Path(temp))
            try:
                ctx = self._accepting_run(runtime)
                args = {"action": "accept", "run_id": ctx.run_id}
                first = runtime.call_tool("task_control", dict(args))
                second = runtime.call_tool("task_control", dict(args))
                self.assertFalse(first.get("isError"))
                self.assertTrue(first["structuredContent"]["accepted"])
                self.assertFalse(second.get("isError"))
                self.assertTrue(second["structuredContent"]["deduplicated"])
                self.assertTrue(second["structuredContent"]["durable_idempotency"])
                self.assertEqual(len(runtime.orchestration_ledger.list_checkpoints(ctx.run_id)), 1)
                self.assertEqual(runtime.orchestration_control.snapshot(ctx.run_id).state, "CHECKPOINTED")
            finally:
                runtime.close()

    def test_required_task_control_reject_duplicate_replays_without_second_failure_event(self) -> None:
        with tempfile.TemporaryDirectory() as temp, patch.dict(
            "os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}
        ):
            runtime = Runtime(Path(temp))
            try:
                ctx = self._accepting_run(runtime)
                args = {"action": "reject", "run_id": ctx.run_id, "reason": "fixture rejection"}
                first = runtime.call_tool("task_control", dict(args))
                second = runtime.call_tool("task_control", dict(args))
                self.assertFalse(first.get("isError"))
                self.assertTrue(first["structuredContent"]["rejected"])
                self.assertFalse(second.get("isError"))
                self.assertTrue(second["structuredContent"]["deduplicated"])
                events = runtime.orchestration_ledger.list_events_since(ctx.run_id, after_seq=0, limit=100)["events"]
                failures = [item for item in events if item.get("event_type") == "failure_observed"]
                self.assertEqual(len(failures), 1)
                self.assertEqual(runtime.orchestration_control.snapshot(ctx.run_id).state, "REPLAN")
            finally:
                runtime.close()

    def test_required_task_control_conflicting_reuse_fails_before_opposite_action(self) -> None:
        with tempfile.TemporaryDirectory() as temp, patch.dict(
            "os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}
        ):
            runtime = Runtime(Path(temp))
            try:
                ctx = self._accepting_run(runtime)
                shared_key = "task-control-conflict"
                accepted = runtime.call_tool(
                    "task_control",
                    {"action": "accept", "run_id": ctx.run_id, "idempotency_key": shared_key},
                )
                self.assertFalse(accepted.get("isError"))
                rejected = runtime.call_tool(
                    "task_control",
                    {
                        "action": "reject",
                        "run_id": ctx.run_id,
                        "reason": "must not execute",
                        "idempotency_key": shared_key,
                    },
                )
                self.assertTrue(rejected.get("isError"))
                self.assertEqual(rejected["structuredContent"]["error"]["code"], "IDEMPOTENCY_CONFLICT")
                events = runtime.orchestration_ledger.list_events_since(ctx.run_id, after_seq=0, limit=100)["events"]
                self.assertEqual([item for item in events if item.get("event_type") == "failure_observed"], [])
                self.assertEqual(len(runtime.orchestration_ledger.list_checkpoints(ctx.run_id)), 1)
            finally:
                runtime.close()

    def test_required_task_control_prior_process_unknown_outcome_fails_closed(self) -> None:
        for action in ("accept", "reject"):
            with self.subTest(action=action), tempfile.TemporaryDirectory() as temp, patch.dict(
                "os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}
            ):
                root = Path(temp)
                first = Runtime(root)
                ctx = self._accepting_run(first)
                args = {"action": action, "run_id": ctx.run_id, "idempotency_key": f"unknown-{action}"}
                if action == "reject":
                    args["reason"] = "unknown prior outcome"
                request_hash = first._request_hash(args)
                first.orchestration_ledger.claim_idempotency(
                    idempotency_key=str(args["idempotency_key"]),
                    operation="task_control",
                    request_hash=request_hash,
                    process_instance_id="prior-mcp-process",
                    run_id=ctx.run_id,
                    wave_id=ctx.wave_id,
                )
                first.close()

                restored = Runtime(root)
                try:
                    result = restored.call_tool("task_control", dict(args))
                    self.assertTrue(result.get("isError"))
                    self.assertEqual(result["structuredContent"]["error"]["code"], "IDEMPOTENCY_OUTCOME_UNKNOWN")
                    self.assertEqual(restored.orchestration_control.snapshot(ctx.run_id).state, "ACCEPTING")
                    self.assertEqual(restored.orchestration_ledger.list_checkpoints(ctx.run_id), [])
                    events = restored.orchestration_ledger.list_events_since(ctx.run_id, after_seq=0, limit=100)["events"]
                    self.assertEqual([item for item in events if item.get("event_type") == "failure_observed"], [])
                finally:
                    restored.close()

    def test_duplicate_delivery_replays_without_second_side_effect(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            marker = root / "marker.txt"
            runtime = Runtime(root)
            try:
                args = {
                    "cmd": "echo ran >> marker.txt",
                    "yield_time_ms": 1000,
                    "max_output_bytes": 4096,
                    "verbosity": "full",
                    "idempotency_key": "dup-exec-1",
                }
                first = runtime.call_tool("exec_command", dict(args))
                second = runtime.call_tool("exec_command", dict(args))
                self.assertFalse(first.get("isError"))
                self.assertFalse(second.get("isError"))
                self.assertIsInstance(second.get("content"), list)
                self.assertTrue(second["structuredContent"].get("deduplicated"))
                self.assertTrue(second["structuredContent"].get("durable_idempotency"))
                record = second["structuredContent"].get("idempotency") or {}
                self.assertEqual(record.get("status"), "completed")
                lines = marker.read_text(encoding="utf-8").splitlines()
                self.assertEqual(len([line for line in lines if line.strip() == "ran"]), 1)
            finally:
                runtime.close()

    def test_conflicting_reuse_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            try:
                args = {
                    "cmd": "echo once",
                    "yield_time_ms": 1000,
                    "max_output_bytes": 4096,
                    "verbosity": "full",
                    "idempotency_key": "conflict-key",
                }
                runtime.call_tool("exec_command", dict(args))
                changed = dict(args)
                changed["cmd"] = "echo differently"
                result = runtime.call_tool("exec_command", changed)
                self.assertTrue(result.get("isError"))
                error = result.get("structuredContent", {}).get("error") or {}
                self.assertEqual(error.get("code"), "IDEMPOTENCY_CONFLICT")
            finally:
                runtime.close()

    def test_in_progress_claim_blocks_second_copy(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            try:
                args = {
                    "cmd": "echo busy",
                    "yield_time_ms": 1000,
                    "max_output_bytes": 4096,
                    "verbosity": "full",
                    "idempotency_key": "busy-key",
                }
                request_hash = runtime._request_hash(args)
                runtime.orchestration_ledger.claim_idempotency(
                    idempotency_key="busy-key",
                    operation="exec_command",
                    request_hash=request_hash,
                    process_instance_id=runtime.process_instance_id,
                )
                result = runtime.call_tool("exec_command", dict(args))
                self.assertTrue(result.get("isError"))
                error = result.get("structuredContent", {}).get("error") or {}
                self.assertEqual(error.get("code"), "IDEMPOTENCY_IN_PROGRESS")
                self.assertTrue(error.get("retryable"))
            finally:
                runtime.close()

    def test_unknown_outcome_after_process_restart_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            args = {
                "cmd": "echo unknown",
                "yield_time_ms": 1000,
                "max_output_bytes": 4096,
                "verbosity": "full",
                "idempotency_key": "unknown-key",
            }
            first = Runtime(root)
            try:
                request_hash = first._request_hash(args)
                first.orchestration_ledger.claim_idempotency(
                    idempotency_key="unknown-key",
                    operation="exec_command",
                    request_hash=request_hash,
                    process_instance_id="prior-mcp-process",
                )
            finally:
                first.close()
            restored = Runtime(root)
            try:
                result = restored.call_tool("exec_command", dict(args))
                self.assertTrue(result.get("isError"))
                error = result.get("structuredContent", {}).get("error") or {}
                self.assertEqual(error.get("code"), "IDEMPOTENCY_OUTCOME_UNKNOWN")
            finally:
                restored.close()

    def test_replay_survives_runtime_restart(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            args = {
                "cmd": "echo persisted",
                "yield_time_ms": 1000,
                "max_output_bytes": 4096,
                "verbosity": "full",
                "idempotency_key": "restart-key",
            }
            first = Runtime(root)
            try:
                first.call_tool("exec_command", dict(args))
            finally:
                first.close()
            restored = Runtime(root)
            try:
                replay = restored.call_tool("exec_command", dict(args))
                self.assertTrue(replay["structuredContent"].get("deduplicated"))
            finally:
                restored.close()

    def test_terminal_failure_recorded_and_repeated_call_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            try:
                args = {
                    "patch": "not a valid patch envelope",
                    "idempotency_key": "terminal-key",
                }
                first = runtime.call_tool("apply_patch", dict(args))
                self.assertTrue(first.get("isError"))
                error = first.get("structuredContent", {}).get("error") or {}
                self.assertEqual(error.get("code"), "PATCH_FAILED")
                repeated = runtime.call_tool("apply_patch", dict(args))
                self.assertTrue(repeated.get("isError"))
                repeated_error = repeated.get("structuredContent", {}).get("error") or {}
                self.assertEqual(repeated_error.get("code"), "IDEMPOTENT_REQUEST_FAILED")
            finally:
                runtime.close()

    def test_exposed_schemas_accept_idempotency_key(self) -> None:
        with tempfile.TemporaryDirectory() as temp, patch.dict(
            "os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}
        ):
            runtime = Runtime(Path(temp))
            try:
                for name in runtime.exposed_tool_names():
                    try:
                        validate_arguments(name, {"idempotency_key": "schema-key"})
                    except Exception as exc:
                        self.assertNotIn(
                            "idempotency_key",
                            str(getattr(exc, "message", exc)),
                            f"{name} rejected idempotency_key",
                        )
            finally:
                runtime.close()


class DefaultCwdDeprecationTests(unittest.TestCase):
    def test_set_default_cwd_is_deprecated_noop(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            try:
                payload = runtime.set_default_cwd({"path": "."})
                self.assertTrue(payload.get("deprecated"))
                self.assertTrue(payload.get("deprecation_note"))
                self.assertEqual(runtime.default_cwd, runtime.workspace.root)
                self.assertEqual(payload["default_cwd"], runtime.default_cwd_display())
            finally:
                runtime.close()

    def test_get_default_cwd_returns_workspace_root_and_deprecation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            try:
                payload = runtime.get_default_cwd({})
                self.assertTrue(payload.get("deprecated"))
                self.assertEqual(str(payload["workspace"]), str(runtime.workspace.root))
            finally:
                runtime.close()

    def test_smart_surface_does_not_expose_default_cwd_tools(self) -> None:
        with tempfile.TemporaryDirectory() as temp, patch.dict(
            "os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}
        ):
            runtime = Runtime(Path(temp))
            try:
                names = runtime.exposed_tool_names()
                self.assertEqual(len(names), 8)
                self.assertNotIn("get_default_cwd", names)
                self.assertNotIn("set_default_cwd", names)
            finally:
                runtime.close()


if __name__ == "__main__":
    unittest.main()
