from __future__ import annotations

import hashlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from coding_tools_mcp.acceptance_receipts import (
    _accepted_file_receipts,
    _durable_wave_acceptance_paths,
)
from coding_tools_mcp.errors import ToolFailure
from coding_tools_mcp.git_tools import _parse_git_status_porcelain_v1_z
from coding_tools_mcp.server import Runtime, validate_arguments
from coding_tools_mcp.solution_economics import record_patch_surface


class AcceptanceFileAttestationTests(unittest.TestCase):
    @staticmethod
    def _accepting_run(
        runtime: Runtime,
        *,
        allowed_paths: list[str] | None = None,
        existing_dirty_source_paths: list[str] | None = None,
        patch_paths: list[str] | None = None,
        proof_statuses: list[str] | None = None,
    ):
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
        runtime.orchestration_control.acquire_write_lease(
            ctx,
            owner="MCP",
            mode="mcp_only",
            allowed_paths=allowed_paths or [],
            existing_dirty_source_paths=existing_dirty_source_paths or [],
        )
        if patch_paths:
            record_patch_surface(
                runtime.orchestration_ledger,
                run_id=ctx.run_id,
                wave_id=ctx.wave_id,
                patch_result={
                    "affected_files": [{"path": path} for path in patch_paths],
                    "additions": len(patch_paths),
                    "removals": 0,
                    "dry_run": False,
                },
            )
        runtime.orchestration_control.begin_proof(ctx)
        statuses = (["passed"] if patch_paths else []) if proof_statuses is None else list(proof_statuses)
        for index, status in enumerate(statuses):
            runtime.orchestration_ledger.record_proof(
                run_id=ctx.run_id,
                wave_id=ctx.wave_id,
                stage_id=f"acceptance-fixture-{index}",
                stage_version="1",
                input_fingerprint=hashlib.sha256(f"fixture-{index}-{status}".encode("utf-8")).hexdigest(),
                status=status,
            )
        runtime.orchestration_control.mark_accepting(ctx, proof_summary={"proof": "green"})
        runtime.task_state.set_orchestration_projection(ctx.projection(), event="test_accepting_projection")
        return ctx

    def test_nul_git_status_parser_preserves_unicode_and_rename_copy_records(self) -> None:
        raw = (
            "## main...origin/main [ahead 1]\0"
            " M café.js\0"
            "R  current.py\0original.py\0"
            "C  copied.py\0source.py\0"
        ).encode("utf-8")
        branch, upstream, ahead, behind, entries = _parse_git_status_porcelain_v1_z(raw)
        self.assertEqual((branch, upstream, ahead, behind), ("main", "origin/main", 1, 0))
        self.assertEqual(entries, [
            {"path": "café.js", "original_path": None, "index_status": " ", "worktree_status": "M"},
            {"path": "current.py", "original_path": "original.py", "index_status": "R", "worktree_status": " "},
            {"path": "copied.py", "original_path": "source.py", "index_status": "C", "worktree_status": " "},
        ])

    def test_nul_git_status_parser_fails_closed_on_invalid_utf8_records_and_oversize(self) -> None:
        invalid_inputs = [
            b"## main\0?? \xff\0",
            b"## main\0R  current.py\0",
            b"## main\0?? missing-terminator",
            b"## main\0bad\0",
        ]
        for raw in invalid_inputs:
            with self.subTest(raw=raw), self.assertRaises(ToolFailure) as malformed:
                _parse_git_status_porcelain_v1_z(raw)
            self.assertEqual(malformed.exception.code, "GIT_STATUS_MALFORMED")
        oversized = ("## main\0" + "".join(f"?? file-{index}.py\0" for index in range(2001))).encode("utf-8")
        with self.assertRaises(ToolFailure) as too_large:
            _parse_git_status_porcelain_v1_z(oversized)
        self.assertEqual(too_large.exception.code, "WORKTREE_STATUS_TOO_LARGE")

    def test_accept_attests_unchanged_file_without_false_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "app.py"
            source.write_bytes(b"VALUE = 1\n")
            (root / "unrelated.py").write_text("UNRELATED = True\n", encoding="utf-8")
            runtime = Runtime(root)
            try:
                ctx = self._accepting_run(runtime, proof_statuses=["passed"])
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
                self.assertEqual(receipts["schema_version"], 2)
                self.assertEqual(receipts["source"], "explicit_acceptance_attestations")
                self.assertEqual(receipts["run_id"], ctx.run_id)
                self.assertEqual(receipts["wave_id"], ctx.wave_id)
                self.assertEqual(receipts["count"], 1)
                receipt = receipts["files"][0]
                self.assertEqual(receipt["path"], "app.py")
                self.assertEqual(receipt["sha256"], expected_sha256)
                self.assertEqual(receipt["expected_sha256"], expected_sha256)
                self.assertEqual(receipt["receipt_kind"], "explicit_existing_file")
                self.assertEqual(receipt["run_id"], ctx.run_id)
                self.assertEqual(receipt["wave_id"], ctx.wave_id)
                self.assertTrue(receipt["restart_safe"])
                self.assertTrue(receipt["content_addressed"])
                self.assertNotIn("unrelated.py", [item["path"] for item in receipts["files"]])
                report = accepted["completion_report"]
                self.assertEqual(report["what_changed"]["source"], "accepted_checkpoint_file_attestations")
                self.assertEqual(report["what_changed"]["files"][0]["receipt_kind"], "explicit_existing_file")
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

    def test_explicit_symlink_attestation_fails_before_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "app.py"
            source.write_bytes(b"VALUE = 1\n")
            with patch.object(Path, "is_symlink", autospec=True, return_value=True):
                with self.assertRaises(ToolFailure) as invalid:
                    _accepted_file_receipts(
                        root,
                        [],
                        acceptance_files=[{
                            "path": "app.py",
                            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                        }],
                        run_id="run-symlink-0001",
                        wave_id="wave-symlink-0001",
                    )
                self.assertEqual(invalid.exception.code, "ACCEPTANCE_FILE_NOT_REGULAR")

    def test_explicit_parent_reparse_component_fails_before_resolve_or_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "linked" / "app.py"
            source.parent.mkdir()
            source.write_bytes(b"VALUE = 1\n")
            unsafe_parent = source.parent
            with patch(
                "coding_tools_mcp.acceptance_receipts._reparse_component",
                side_effect=[None, unsafe_parent],
            ):
                with self.assertRaises(ToolFailure) as invalid:
                    _accepted_file_receipts(
                        root,
                        [],
                        acceptance_files=[{
                            "path": "linked/app.py",
                            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                        }],
                        run_id="run-parent-reparse-0001",
                        wave_id="wave-parent-reparse-0001",
                    )
            self.assertEqual(invalid.exception.code, "ACCEPTANCE_FILE_NOT_REGULAR")
            self.assertTrue(str(invalid.exception.details["unsafe_component"]).endswith("linked"))

    @unittest.skipUnless(os.name == "nt", "Windows protected-path aliases are case-insensitive")
    def test_explicit_coding_tools_case_alias_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            evidence = root / ".coding-tools" / "evidence.txt"
            evidence.parent.mkdir()
            evidence.write_bytes(b"runtime evidence\n")
            with self.assertRaises(ToolFailure) as invalid:
                _accepted_file_receipts(
                    root,
                    [],
                    acceptance_files=[{
                        "path": ".CODING-TOOLS/evidence.txt",
                        "sha256": hashlib.sha256(evidence.read_bytes()).hexdigest(),
                    }],
                    run_id="run-protected-case-0001",
                    wave_id="wave-protected-case-0001",
                )
            self.assertEqual(invalid.exception.code, "ACCEPTANCE_FILE_INVALID")

    @unittest.skipUnless(os.name == "nt", "Windows protected-path aliases are case-insensitive")
    def test_explicit_git_case_alias_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            git_config = root / ".git" / "config"
            git_config.parent.mkdir()
            git_config.write_bytes(b"[core]\n")
            with self.assertRaises(ToolFailure) as invalid:
                _accepted_file_receipts(
                    root,
                    [],
                    acceptance_files=[{
                        "path": ".GIT/config",
                        "sha256": hashlib.sha256(git_config.read_bytes()).hexdigest(),
                    }],
                    run_id="run-protected-git-case-0001",
                    wave_id="wave-protected-git-case-0001",
                )
            self.assertEqual(invalid.exception.code, "ACCEPTANCE_FILE_INVALID")

    def test_real_parent_symlink_is_rejected_when_supported(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "target"
            target.mkdir()
            source = target / "app.py"
            source.write_bytes(b"VALUE = 1\n")
            linked = root / "linked"
            try:
                linked.symlink_to(target, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"directory symlink creation unavailable: {type(exc).__name__}")
            with self.assertRaises(ToolFailure) as invalid:
                _accepted_file_receipts(
                    root,
                    [],
                    acceptance_files=[{
                        "path": "linked/app.py",
                        "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                    }],
                    run_id="run-real-parent-link-0001",
                    wave_id="wave-real-parent-link-0001",
                )
            self.assertEqual(invalid.exception.code, "ACCEPTANCE_FILE_NOT_REGULAR")

    @unittest.skipUnless(os.name == "nt", "Windows protected-path aliases are case-insensitive")
    def test_durable_protected_case_alias_cannot_be_checkpointed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            try:
                ctx = self._accepting_run(
                    runtime,
                    allowed_paths=[".GIT/config"],
                    patch_paths=[".GIT/config"],
                )
                with self.assertRaises(ToolFailure) as invalid:
                    runtime.task_control({"action": "accept", "run_id": ctx.run_id, "wave_id": ctx.wave_id})
                self.assertEqual(invalid.exception.code, "ACCEPTANCE_FILE_ATTESTATION_REQUIRED")
                self.assertEqual(runtime.orchestration_ledger.list_checkpoints(ctx.run_id), [])
            finally:
                runtime.close()

    def test_explicit_receipt_without_passed_proof_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "app.py"
            source.write_bytes(b"VALUE = 1\n")
            runtime = Runtime(root)
            try:
                ctx = self._accepting_run(runtime)
                with self.assertRaises(ToolFailure) as missing:
                    runtime.task_control({
                        "action": "accept",
                        "run_id": ctx.run_id,
                        "wave_id": ctx.wave_id,
                        "acceptance_files": [{
                            "path": "app.py",
                            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                        }],
                    })
                self.assertEqual(missing.exception.code, "ACCEPTANCE_PROOF_REQUIRED")
                self.assertEqual(runtime.orchestration_ledger.list_checkpoints(ctx.run_id), [])
            finally:
                runtime.close()

    def test_duplicate_durable_file_ids_are_incomplete_evidence(self) -> None:
        file_id = hashlib.sha256(b"app.py").hexdigest()

        class DuplicateEventLedger:
            @staticmethod
            def list_events(_run_id):
                return [{
                    "wave_id": "wave-duplicate-0001",
                    "event_type": "patch_surface_observed",
                    "payload": {
                        "complete": True,
                        "file_count": 2,
                        "file_ids": [file_id, file_id],
                    },
                }]

        with self.assertRaises(ToolFailure) as incomplete:
            _durable_wave_acceptance_paths(
                DuplicateEventLedger(),
                "run-duplicate-0001",
                "wave-duplicate-0001",
            )
        self.assertEqual(incomplete.exception.code, "ACCEPTANCE_FILE_ATTESTATION_REQUIRED")


    def test_stateless_accept_recovers_exact_touched_files_from_durable_wave(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "app.py"
            source.write_bytes(b"VALUE = 2\n")
            (root / "unrelated.py").write_text("UNRELATED = True\n", encoding="utf-8")
            runtime = Runtime(root)
            try:
                ctx = self._accepting_run(
                    runtime,
                    allowed_paths=["app.py", "unrelated.py"],
                    patch_paths=["app.py"],
                )
                self.assertEqual(runtime.task_state.get()["modified_files"], [])
                runtime.close()
                runtime = Runtime(root)
                accepted = runtime.task_control({"action": "accept", "run_id": ctx.run_id, "wave_id": ctx.wave_id})
                self.assertTrue(accepted["accepted"])
                checkpoint = runtime.orchestration_ledger.list_checkpoints(ctx.run_id)[-1]
                receipts = checkpoint["metadata"]["accepted_files"]
                self.assertTrue(receipts["complete"])
                self.assertEqual(receipts["source"], "durable_wave_patch_surface")
                self.assertEqual(receipts["count"], 1)
                self.assertEqual([item["path"] for item in receipts["files"]], ["app.py"])
                self.assertEqual(receipts["files"][0]["sha256"], hashlib.sha256(source.read_bytes()).hexdigest())
                self.assertEqual(receipts["files"][0]["receipt_kind"], "durable_wave_patch_surface")
                self.assertEqual(receipts["files"][0]["run_id"], ctx.run_id)
                self.assertEqual(receipts["files"][0]["wave_id"], ctx.wave_id)
                self.assertTrue(receipts["files"][0]["restart_safe"])
                self.assertTrue(receipts["files"][0]["content_addressed"])
            finally:
                runtime.close()

    def test_stateless_accept_excludes_preexisting_dirty_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
            (root / "dirty.py").write_text("DIRTY = True\n", encoding="utf-8")
            runtime = Runtime(root)
            try:
                ctx = self._accepting_run(
                    runtime,
                    allowed_paths=["app.py", "dirty.py"],
                    existing_dirty_source_paths=["dirty.py"],
                    patch_paths=["app.py"],
                )
                accepted = runtime.task_control({"action": "accept", "run_id": ctx.run_id, "wave_id": ctx.wave_id})
                receipts = runtime.orchestration_ledger.list_checkpoints(ctx.run_id)[-1]["metadata"]["accepted_files"]
                self.assertTrue(accepted["accepted"])
                self.assertEqual([item["path"] for item in receipts["files"]], ["app.py"])
                self.assertNotIn("dirty.py", [item["path"] for item in receipts["files"]])
            finally:
                runtime.close()

    def test_stateless_accept_fails_closed_when_touched_file_is_not_safe_lease_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
            (root / "outside.py").write_text("OUTSIDE = True\n", encoding="utf-8")
            runtime = Runtime(root)
            try:
                ctx = self._accepting_run(
                    runtime,
                    allowed_paths=["app.py"],
                    patch_paths=["outside.py"],
                )
                with self.assertRaises(ToolFailure) as missing:
                    runtime.task_control({"action": "accept", "run_id": ctx.run_id, "wave_id": ctx.wave_id})
                self.assertEqual(missing.exception.code, "ACCEPTANCE_FILE_ATTESTATION_REQUIRED")
                self.assertEqual(runtime.orchestration_control.snapshot(ctx.run_id).state, "ACCEPTING")
                self.assertEqual(runtime.orchestration_ledger.list_checkpoints(ctx.run_id), [])
            finally:
                runtime.close()

    def test_explicit_acceptance_cannot_omit_durable_patch_surface(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            app = root / "app.py"
            app.write_text("VALUE = 2\n", encoding="utf-8")
            (root / "other.py").write_text("OTHER = 2\n", encoding="utf-8")
            runtime = Runtime(root)
            try:
                ctx = self._accepting_run(
                    runtime,
                    allowed_paths=["app.py", "other.py"],
                    patch_paths=["app.py", "other.py"],
                )
                with self.assertRaises(ToolFailure) as incomplete:
                    runtime.task_control({
                        "action": "accept",
                        "run_id": ctx.run_id,
                        "wave_id": ctx.wave_id,
                        "acceptance_files": [{"path": "app.py", "sha256": hashlib.sha256(app.read_bytes()).hexdigest()}],
                    })
                self.assertEqual(incomplete.exception.code, "ACCEPTANCE_FILE_ATTESTATION_REQUIRED")
                self.assertEqual(runtime.orchestration_control.snapshot(ctx.run_id).state, "ACCEPTING")
                self.assertEqual(runtime.orchestration_ledger.list_checkpoints(ctx.run_id), [])
            finally:
                runtime.close()

    def test_partial_task_state_is_completed_from_durable_patch_surface(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
            (root / "other.py").write_text("OTHER = 2\n", encoding="utf-8")
            runtime = Runtime(root)
            try:
                ctx = self._accepting_run(
                    runtime,
                    allowed_paths=["app.py", "other.py"],
                    patch_paths=["app.py", "other.py"],
                )
                runtime.task_state.record_tool_result(
                    "apply_patch",
                    {"patch": "fixture"},
                    {"ok": True, "affected_files": [{"path": "app.py", "operation": "update"}]},
                )
                runtime.task_control({"action": "accept", "run_id": ctx.run_id, "wave_id": ctx.wave_id})
                receipts = runtime.orchestration_ledger.list_checkpoints(ctx.run_id)[-1]["metadata"]["accepted_files"]
                self.assertEqual([item["path"] for item in receipts["files"]], ["app.py", "other.py"])
                self.assertEqual({item["receipt_kind"] for item in receipts["files"]}, {"durable_wave_patch_surface"})
            finally:
                runtime.close()

    def test_durable_deleted_file_uses_missing_receipt_without_tombstone_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runtime = Runtime(root)
            try:
                ctx = self._accepting_run(runtime, allowed_paths=["removed.py"], patch_paths=["removed.py"])
                runtime.task_control({"action": "accept", "run_id": ctx.run_id, "wave_id": ctx.wave_id})
                receipt = runtime.orchestration_ledger.list_checkpoints(ctx.run_id)[-1]["metadata"]["accepted_files"]["files"][0]
                self.assertEqual(receipt["state"], "missing")
                self.assertIsNone(receipt["sha256"])
                self.assertEqual(receipt["size_bytes"], 0)
                self.assertTrue(receipt["restart_safe"])
                self.assertFalse(receipt["content_addressed"])
            finally:
                runtime.close()

    def test_mutation_bearing_acceptance_requires_passed_proof(self) -> None:
        for label, statuses in (("no-proof", []), ("failed-only", ["failed"])):
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                (root / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
                runtime = Runtime(root)
                try:
                    ctx = self._accepting_run(
                        runtime,
                        allowed_paths=["app.py"],
                        patch_paths=["app.py"],
                        proof_statuses=statuses,
                    )
                    with self.assertRaises(ToolFailure) as missing:
                        runtime.task_control({"action": "accept", "run_id": ctx.run_id, "wave_id": ctx.wave_id})
                    self.assertEqual(missing.exception.code, "ACCEPTANCE_PROOF_REQUIRED")
                    self.assertEqual(runtime.orchestration_control.snapshot(ctx.run_id).state, "ACCEPTING")
                    self.assertEqual(runtime.orchestration_ledger.list_checkpoints(ctx.run_id), [])
                finally:
                    runtime.close()

    def test_mixed_proof_checkpoint_fingerprint_uses_only_passed_set(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
            runtime = Runtime(root)
            try:
                ctx = self._accepting_run(
                    runtime,
                    allowed_paths=["app.py"],
                    patch_paths=["app.py"],
                    proof_statuses=["failed", "passed"],
                )
                runtime.task_control({"action": "accept", "run_id": ctx.run_id, "wave_id": ctx.wave_id})
                proofs = runtime.orchestration_ledger.list_proofs(ctx.run_id, wave_id=ctx.wave_id)
                passed = [item for item in proofs if item["status"] == "passed"]
                self.assertEqual(len(passed), 1)
                expected = hashlib.sha256(
                    f"{passed[0]['proof_id']}:{passed[0]['input_fingerprint']}".encode("utf-8")
                ).hexdigest()
                checkpoint = runtime.orchestration_ledger.list_checkpoints(ctx.run_id, wave_id=ctx.wave_id)[-1]
                self.assertEqual(checkpoint["proof_fingerprint"], expected)
            finally:
                runtime.close()

    def test_true_no_mutation_acceptance_keeps_complete_zero_file_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            try:
                ctx = self._accepting_run(runtime)
                runtime.task_control({"action": "accept", "run_id": ctx.run_id, "wave_id": ctx.wave_id})
                accepted = runtime.orchestration_ledger.list_checkpoints(ctx.run_id)[-1]["metadata"]["accepted_files"]
                self.assertEqual(accepted["schema_version"], 2)
                self.assertTrue(accepted["complete"])
                self.assertEqual(accepted["count"], 0)
                self.assertEqual(accepted["files"], [])
                checkpoint = runtime.orchestration_ledger.list_checkpoints(ctx.run_id, wave_id=ctx.wave_id)[-1]
                self.assertEqual(checkpoint["proof_fingerprint"], "")
            finally:
                runtime.close()


if __name__ == "__main__":
    unittest.main()
