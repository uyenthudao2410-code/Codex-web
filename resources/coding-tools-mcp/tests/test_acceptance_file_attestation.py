from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from coding_tools_mcp.errors import ToolFailure
from coding_tools_mcp.server import Runtime, validate_arguments


class AcceptanceFileAttestationTests(unittest.TestCase):
    @staticmethod
    def _accepting_run(runtime: Runtime):
        state = runtime.task_state.ensure_started("acceptance file attestation fixture")
        identity = runtime._orchestration_workspace_identity(".")
        ctx = runtime.orchestration_control.begin(
            objective="acceptance file attestation fixture",
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

    def test_accept_attests_unchanged_file_without_false_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "app.py"
            source.write_bytes(b"VALUE = 1\n")
            (root / "unrelated.py").write_text("UNRELATED = True\n", encoding="utf-8")
            runtime = Runtime(root)
            try:
                ctx = self._accepting_run(runtime)
                expected_sha256 = hashlib.sha256(source.read_bytes()).hexdigest()
                args = {
                    "action": "accept",
                    "run_id": ctx.run_id,
                    "wave_id": ctx.wave_id,
                    "acceptance_files": [{"path": "app.py", "sha256": expected_sha256}],
                }
                validate_arguments("task_control", args)
                accepted = runtime.task_control(args)
                self.assertTrue(accepted["accepted"])
                self.assertEqual(runtime.task_state.get()["modified_files"], [])
                checkpoint = runtime.orchestration_ledger.list_checkpoints(ctx.run_id)[-1]
                receipts = checkpoint["metadata"]["accepted_files"]
                self.assertTrue(receipts["complete"])
                self.assertEqual(receipts["source"], "explicit_acceptance_attestations")
                self.assertEqual(receipts["count"], 1)
                receipt = receipts["files"][0]
                self.assertEqual(receipt["path"], "app.py")
                self.assertEqual(receipt["sha256"], expected_sha256)
                self.assertEqual(receipt["expected_sha256"], expected_sha256)
                self.assertEqual(receipt["receipt_kind"], "existing_file_attestation")
                self.assertEqual(receipt["run_id"], ctx.run_id)
                self.assertEqual(receipt["wave_id"], ctx.wave_id)
                self.assertTrue(receipt["restart_safe"])
                self.assertTrue(receipt["content_addressed"])
                self.assertNotIn("unrelated.py", [item["path"] for item in receipts["files"]])
                report = accepted["completion_report"]
                self.assertEqual(report["what_changed"]["source"], "accepted_checkpoint_file_attestations")
                self.assertEqual(report["what_changed"]["files"][0]["receipt_kind"], "existing_file_attestation")
                self.assertEqual(report["what_changed"]["files"][0]["run_id"], ctx.run_id)
                self.assertEqual(report["what_changed"]["files"][0]["wave_id"], ctx.wave_id)
            finally:
                runtime.close()

    def test_sha_mismatch_fails_before_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "app.py").write_bytes(b"VALUE = 1\n")
            runtime = Runtime(root)
            try:
                ctx = self._accepting_run(runtime)
                with self.assertRaises(ToolFailure) as mismatch:
                    runtime.task_control({
                        "action": "accept",
                        "run_id": ctx.run_id,
                        "wave_id": ctx.wave_id,
                        "acceptance_files": [{"path": "app.py", "sha256": "0" * 64}],
                    })
                self.assertEqual(mismatch.exception.code, "ACCEPTANCE_FILE_SHA_MISMATCH")
                self.assertEqual(runtime.orchestration_control.snapshot(ctx.run_id).state, "ACCEPTING")
                self.assertEqual(runtime.orchestration_ledger.list_checkpoints(ctx.run_id), [])
                self.assertEqual(runtime.task_state.get()["modified_files"], [])
            finally:
                runtime.close()

    def test_noncurrent_wave_fails_before_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "app.py"
            source.write_bytes(b"VALUE = 1\n")
            runtime = Runtime(root)
            try:
                ctx = self._accepting_run(runtime)
                expected_sha256 = hashlib.sha256(source.read_bytes()).hexdigest()
                with self.assertRaises(ToolFailure) as mismatch:
                    runtime.task_control({
                        "action": "accept",
                        "run_id": ctx.run_id,
                        "wave_id": "wrong-wave",
                        "acceptance_files": [{"path": "app.py", "sha256": expected_sha256}],
                    })
                self.assertEqual(mismatch.exception.code, "ORCHESTRATION_WAVE_MISMATCH")
                self.assertEqual(runtime.orchestration_control.snapshot(ctx.run_id).state, "ACCEPTING")
                self.assertEqual(runtime.orchestration_ledger.list_checkpoints(ctx.run_id), [])
            finally:
                runtime.close()


if __name__ == "__main__":
    unittest.main()
