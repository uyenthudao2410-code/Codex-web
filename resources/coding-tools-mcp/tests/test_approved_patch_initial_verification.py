from __future__ import annotations

import base64
import hashlib
import json
import tempfile
import time
import unittest
import zlib
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from coding_tools_mcp.approved_patch_verification import (
    APPROVED_PATCH_VERIFICATION_ORIGIN, normalize_initial_verification,
)
from coding_tools_mcp.errors import ToolFailure
from coding_tools_mcp.server import Runtime
from coding_tools_mcp.tool_schema import validate_arguments


class ApprovedPatchInitialVerificationTests(unittest.TestCase):
    EXPIRY_MS = int(time.time() * 1000) + 3600000
    @staticmethod
    def actor() -> dict:
        return {"client_id": "electron-control-plane-approved-patch-bridge", "client_type": "electron",
                "identity_source": "attested_transport", "attestation_verified": True}

    @staticmethod
    def plan() -> dict:
        return {"argv": ["node", "--test", "tests/value.test.js"], "cwd": "",
                "timeout_ms": 60000, "max_output_bytes": 32768}

    def args(self) -> dict:
        before, after = b"VALUE = 1\n", b"VALUE = 2\n"
        payload = base64.b64encode(zlib.compress(after)).decode("ascii")
        patch = ("*** Begin Patch\n*** Write Exact File: value.py\n"
                 f"@@ encoding=zlib-base64 preimage_sha256={hashlib.sha256(before).hexdigest()} "
                 f"postimage_sha256={hashlib.sha256(after).hexdigest()}\n+{payload}\n*** End Patch")
        return {"workflow": "custom", "phase": "execute", "execution_mode": "mcp_only",
                "execution_route": "deterministic", "verification": "none", "patch": patch,
                "objective": "Fix exact value and prove its behavior", "initial_verification": self.plan(),
                "initial_verification_expires_at_ms": self.EXPIRY_MS,
                "idempotency_key": "approved-patch-initial-proof"}

    def runtime(self, root: Path) -> Runtime:
        (root / "value.py").write_bytes(b"VALUE = 1\n")
        runtime = Runtime(root, permission_mode="dangerous")
        runtime.request_context.hub_client = self.actor()
        return runtime

    def test_schema_exact_plan_and_canonical_hash(self) -> None:
        validate_arguments("agent_workflow", self.args())
        plan = normalize_initial_verification(self.plan())
        canonical = json.dumps(self.plan(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        self.assertEqual(plan.sha256, hashlib.sha256(canonical.encode()).hexdigest())
        original = self.plan()
        frozen = normalize_initial_verification(original)
        original["argv"].append("changed")
        self.assertEqual(frozen.argv, ("node", "--test", "tests/value.test.js"))
        with self.assertRaises(Exception):
            validate_arguments("agent_workflow", {**self.args(), "initial_verification": {**self.plan(), "origin": True}})

    def test_legacy_binding_and_task_spec_hash_do_not_gain_null_fields(self) -> None:
        args = {"workflow": "custom", "phase": "execute", "objective": "legacy", "verification": "none"}
        normalized, _budget = Runtime._agent_admission_budget(args)
        self.assertNotIn("initial_verification", normalized)
        self.assertNotIn("initial_verification_expires_at_ms", normalized)
        stable = {"objective": "legacy", "workflow": "custom", "path": ".", "workdir": ".",
                  "verification": "none", "test_command": "", "build_command": ""}
        expected = hashlib.sha256(json.dumps(stable, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        self.assertEqual(Runtime._evaluation_task_spec_fingerprint(args), expected)
        expected_request = hashlib.sha256(json.dumps(args, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        self.assertEqual(Runtime._request_hash(args), expected_request)

    def test_admitted_trailing_newline_patch_bytes_remain_exact(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runtime = self.runtime(root)
            args = self.args()
            args["patch"] += "\n"
            runtime.exec_command = MagicMock(return_value={"status": "exited", "exit_code": 0})
            runtime.apply_patch = MagicMock(wraps=runtime.apply_patch)
            try:
                result = runtime.agent_workflow(args)
                self.assertEqual(result["execution"]["initial_verification"]["proof_status"], "passed")
                actual = [call.args[0] for call in runtime.apply_patch.call_args_list if call.args[0].get("dry_run") is False]
                self.assertEqual(len(actual), 1)
                self.assertEqual(actual[0]["patch"], args["patch"])
                self.assertEqual((root / "value.py").read_bytes(), b"VALUE = 2\n")
            finally:
                runtime.close()

    def test_wrong_actor_and_unsafe_plan_deny_before_patch_or_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runtime = self.runtime(root)
            runtime.exec_command = MagicMock(side_effect=AssertionError("must not execute"))
            try:
                for change in ("wrong_actor", "unattested", "shell", "cwd", "cwd_dot", "cwd_empty_segment",
                               "argv_control", "argv_untrimmed", "argv_oversized_bytes", "dry_run", "extra_command", "plain_patch"):
                    runtime.request_context.hub_client = self.actor()
                    args = self.args()
                    if change == "wrong_actor":
                        runtime.request_context.hub_client["client_id"] = "electron-control-plane-exec-bridge"
                    elif change == "unattested":
                        runtime.request_context.hub_client["attestation_verified"] = False
                    elif change == "shell":
                        args["initial_verification"]["argv"] = ["cmd.exe", "/c", "node --test"]
                    elif change == "cwd":
                        args["initial_verification"]["cwd"] = "../elsewhere"
                    elif change == "cwd_dot":
                        args["initial_verification"]["cwd"] = "."
                    elif change == "cwd_empty_segment":
                        args["initial_verification"]["cwd"] = "a//b"
                    elif change == "argv_control":
                        args["initial_verification"]["argv"][2] = "test\tfile"
                    elif change == "argv_untrimmed":
                        args["initial_verification"]["argv"][0] = " node"
                    elif change == "argv_oversized_bytes":
                        args["initial_verification"]["argv"][2] = "é" * 1025
                    elif change == "dry_run":
                        args["dry_run"] = True
                    elif change == "extra_command":
                        args["commands"] = ["node --test"]
                    else:
                        args["patch"] = "*** Begin Patch\n*** Update File: value.py\n@@\n-VALUE = 1\n+VALUE = 2\n*** End Patch"
                    with self.subTest(change=change), self.assertRaises(ToolFailure):
                        runtime.agent_workflow(args)
                    self.assertEqual((root / "value.py").read_bytes(), b"VALUE = 1\n")
                    self.assertEqual(runtime.orchestration_ledger.list_runs(limit=10), [])
                runtime.exec_command.assert_not_called()
            finally:
                runtime.close()

    def test_passed_structured_check_has_real_source_bound_proof_and_dedup(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runtime = self.runtime(root)
            captured = []
            def execute(args: dict) -> dict:
                captured.append(args)
                self.assertEqual((root / "value.py").read_bytes(), b"VALUE = 2\n")
                return {"status": "exited", "exit_code": 0, "command_id": "command_fixture",
                        "execution_owner": {"job_id": "job_fixture"}}
            runtime.exec_command = execute
            try:
                result = runtime.agent_workflow(self.args())
                self.assertEqual(len(captured), 1)
                command = captured[0]
                self.assertNotIn("cmd", command)
                self.assertNotIn("argv", command)
                self.assertNotIn("_continuation_internal", command)
                self.assertEqual(command["_argv"], self.plan()["argv"])
                self.assertIs(command["_approved_patch_verification_origin"], APPROVED_PATCH_VERIFICATION_ORIGIN)
                self.assertEqual(command["run_id"], result["orchestration"]["run_id"])
                self.assertEqual(command["wave_id"], result["orchestration"]["wave_id"])
                self.assertEqual(result["orchestration"]["orchestration_state"], "ACCEPTING")
                execution = result["execution"]
                summary = execution["initial_verification"]
                self.assertEqual(summary["proof_status"], "passed")
                self.assertEqual(summary["plan_sha256"], normalize_initial_verification(self.plan()).sha256)
                self.assertEqual(len(summary["proof_fingerprint"]), 64)
                proofs = runtime.orchestration_ledger.list_proofs(command["run_id"], wave_id=command["wave_id"])
                self.assertEqual(summary["proof_ids"], [proofs[0]["proof_id"]])
                self.assertEqual(proofs[0]["metadata"]["initial_verification"], self.plan())
                self.assertEqual(proofs[0]["metadata"]["proof_source_binding"]["paths"], ["value.py"])
                self.assertEqual(summary["command_id"], "command_fixture")
                self.assertEqual(summary["job_id"], "job_fixture")
                duplicate = runtime.agent_workflow(self.args())
                self.assertTrue(duplicate["deduplicated"])
                self.assertEqual(duplicate["idempotency"]["summary"]["initial_verification"], summary)
                self.assertEqual(len(captured), 1)
                changed = self.args()
                changed["initial_verification"]["timeout_ms"] += 1
                with self.assertRaises(ToolFailure) as drift:
                    runtime.agent_workflow(changed)
                self.assertEqual(drift.exception.code, "IDEMPOTENCY_CONFLICT")
            finally:
                runtime.close()

    def test_failed_and_timed_out_proof_preserve_effect_and_do_not_replay(self) -> None:
        for mode in ("failed", "timed_out", "launch_denied", "unknown"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                runtime = self.runtime(root)
                if mode == "launch_denied":
                    runtime.exec_command = MagicMock(side_effect=ToolFailure("EXECUTOR_UNAVAILABLE", "no start", details={"execution_started": False}))
                elif mode == "unknown":
                    runtime.exec_command = MagicMock(side_effect=ToolFailure("SESSION_CLOSED", "uncertain after spawn"))
                else:
                    runtime.exec_command = MagicMock(return_value={"status": "timeout" if mode == "timed_out" else "exited",
                        "exit_code": None if mode == "timed_out" else 1, "timed_out": mode == "timed_out"})
                try:
                    if mode == "unknown":
                        with self.assertRaises(ToolFailure):
                            runtime.agent_workflow(self.args())
                        self.assertEqual(runtime.orchestration_ledger.get_idempotency(self.args()["idempotency_key"])["status"], "unknown")
                        with self.assertRaises(ToolFailure) as duplicate:
                            runtime.agent_workflow(self.args())
                        self.assertEqual(duplicate.exception.code, "IDEMPOTENCY_OUTCOME_UNKNOWN")
                    else:
                        result = runtime.agent_workflow(self.args())
                        summary = result["execution"]["initial_verification"]
                        self.assertEqual(summary["proof_status"], "timed_out" if mode == "timed_out" else "failed")
                        self.assertIsNone(summary["proof_fingerprint"])
                        self.assertEqual(result["orchestration"]["orchestration_state"], "REPLAN")
                        self.assertEqual(result["execution"]["patch_effect"], {"applied": True, "affected_files": [{"path": "value.py", "operation": "update"}]})
                        duplicate = runtime.agent_workflow(self.args())
                        self.assertTrue(duplicate["deduplicated"])
                        self.assertEqual(duplicate["idempotency"]["summary"]["initial_verification"], summary)
                        self.assertEqual(len(summary["proof_ids"]), 1)
                    self.assertEqual((root / "value.py").read_bytes(), b"VALUE = 2\n")
                    runtime.exec_command.assert_called_once()
                finally:
                    runtime.close()

    def test_forged_private_origin_rejected_without_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runtime = self.runtime(root)
            try:
                plan = normalize_initial_verification(self.plan(), expires_at_ms=self.EXPIRY_MS)
                with self.assertRaises(ToolFailure) as denied:
                    runtime.exec_command({"_argv": list(plan.argv), "_approved_patch_verification_origin": True,
                        "_approved_patch_verification_plan": plan, "workdir": ".", "timeout_ms": plan.timeout_ms,
                        "max_output_bytes": plan.max_output_bytes, "run_id": "fake", "wave_id": "fake"})
                self.assertEqual(denied.exception.code, "APPROVED_PATCH_VERIFICATION_ORIGIN_DENIED")
                self.assertEqual(runtime.orchestration_ledger.list_runs(limit=10), [])
            finally:
                runtime.close()

    def test_executor_uses_structured_mxc_and_never_shell(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runtime = self.runtime(root)
            plan = normalize_initial_verification(self.plan(), expires_at_ms=self.EXPIRY_MS)
            run_id = runtime.orchestration_ledger.create_run(objective="isolated executor forwarding test")
            wave_id = runtime.orchestration_ledger.create_wave(run_id, execution_mode="mcp_only")
            runtime.task_state.update({"orchestration": {"run_id": run_id, "wave_id": wave_id}})
            runtime.execution_resource_governor.admit = MagicMock(return_value=SimpleNamespace(job_id="fake_job"))
            runtime.execution_resource_governor.spawn_failed = MagicMock()
            runtime.landlock_enabled = MagicMock(return_value=False)
            invocation = SimpleNamespace(argv=["mxc_fixture", "structured_request"], environment={})
            try:
                with patch("coding_tools_mcp.exec_tools.is_sandboxed_execution", return_value=True), \
                     patch("coding_tools_mcp.exec_tools.windows_sandbox_feature_enabled", return_value=False), \
                     patch("coding_tools_mcp.exec_tools.build_mxc_invocation", return_value=invocation) as mxc, \
                     patch("coding_tools_mcp.exec_tools.cleanup_mxc_invocation"), \
                     patch("coding_tools_mcp.exec_tools.spawn_process", side_effect=RuntimeError("test stops before process creation")) as spawn:
                    with self.assertRaisesRegex(RuntimeError, "test stops"):
                        runtime.exec_command({"_argv": list(plan.argv), "_approved_patch_verification_origin": APPROVED_PATCH_VERIFICATION_ORIGIN,
                            "_approved_patch_verification_plan": plan, "workdir": ".", "timeout_ms": plan.timeout_ms,
                            "max_output_bytes": plan.max_output_bytes, "run_id": run_id, "wave_id": wave_id})
                    if __import__("os").name == "nt":
                        self.assertEqual(mxc.call_args.args[0], self.plan()["argv"])
                        self.assertEqual(spawn.call_args.args[0], invocation.argv)
                    else:
                        self.assertEqual(spawn.call_args.args[0], self.plan()["argv"])
                    self.assertIs(spawn.call_args.kwargs["shell"], False)
                    admitted = runtime.execution_resource_governor.admit.call_args.kwargs
                    self.assertEqual(admitted["run_id"], run_id)
                    self.assertEqual(admitted["wave_id"], wave_id)
            finally:
                runtime.close()

    def test_expiry_denies_before_write_and_after_write_before_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runtime = self.runtime(root)
            try:
                expired = self.args()
                expired["initial_verification_expires_at_ms"] = 1
                with self.assertRaises(ToolFailure) as denied:
                    runtime.agent_workflow(expired)
                self.assertEqual(denied.exception.code, "APPROVED_PATCH_VERIFICATION_EXPIRED")
                self.assertEqual((root / "value.py").read_bytes(), b"VALUE = 1\n")
                self.assertEqual(runtime.orchestration_ledger.list_runs(limit=10), [])
                now = [time.time()]
                original_patch = runtime.apply_patch
                def apply_then_expire(args: dict) -> dict:
                    result = original_patch(args)
                    if args.get("dry_run") is False:
                        now[0] = self.EXPIRY_MS / 1000 + 1
                    return result
                runtime.apply_patch = apply_then_expire
                with patch("coding_tools_mcp.approved_patch_verification.authority_clock", side_effect=lambda: now[0]), \
                     patch("coding_tools_mcp.exec_tools.spawn_process", side_effect=AssertionError("expired command must not start")) as spawn:
                    result = runtime.agent_workflow(self.args())
                    spawn.assert_not_called()
                self.assertEqual((root / "value.py").read_bytes(), b"VALUE = 2\n")
                self.assertEqual(result["orchestration"]["orchestration_state"], "REPLAN")
                self.assertTrue(result["execution"]["patch_effect"]["applied"])
                self.assertEqual(result["execution"]["initial_verification"]["proof_status"], "failed")
                self.assertIsNone(result["execution"]["initial_verification"]["proof_fingerprint"])
                missing = self.args()
                missing.pop("initial_verification_expires_at_ms")
                with self.assertRaises(ToolFailure):
                    runtime.agent_workflow(missing)
                extra = {"initial_verification_expires_at_ms": self.EXPIRY_MS}
                with self.assertRaises(ToolFailure):
                    runtime.agent_workflow(extra)
            finally:
                runtime.close()

    def test_expiry_while_waiting_patch_lock_prevents_transaction_write(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runtime = self.runtime(root)
            now = [time.time()]
            original_patch = runtime.apply_patch
            original_lock = runtime.patch_lock
            class ExpiringLock:
                def __enter__(self):
                    now[0] = ApprovedPatchInitialVerificationTests.EXPIRY_MS / 1000 + 1
                def __exit__(self, *ignored):
                    return False
            def lock_wait(args: dict) -> dict:
                if args.get("_approved_patch_verification_plan") is not None:
                    runtime.patch_lock = ExpiringLock()
                return original_patch(args)
            runtime.apply_patch = lock_wait
            runtime.exec_command = MagicMock(side_effect=AssertionError("no check after pre-write denial"))
            try:
                with patch("coding_tools_mcp.approved_patch_verification.authority_clock", side_effect=lambda: now[0]):
                    with self.assertRaises(ToolFailure) as denied:
                        runtime.agent_workflow(self.args())
                self.assertEqual(denied.exception.code, "APPROVED_PATCH_VERIFICATION_EXPIRED")
                self.assertTrue(denied.exception.details["workflow_patch_preflight"])
                self.assertEqual((root / "value.py").read_bytes(), b"VALUE = 1\n")
                runtime.exec_command.assert_not_called()
                record = runtime.orchestration_ledger.get_idempotency(self.args()["idempotency_key"])
                self.assertEqual(record["status"], "failed")
                self.assertFalse(record["summary"]["outcome_unknown"])
            finally:
                runtime.patch_lock = original_lock
                runtime.close()


if __name__ == "__main__":
    unittest.main()
