from __future__ import annotations

import hashlib
import http.client
import json
import sqlite3
import subprocess
import tempfile
import threading
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from coding_tools_mcp.server import MCPHandler, Runtime, RuntimeHTTPServer
from coding_tools_mcp.solution_economics import record_patch_surface


class ActivationPreflightTests(unittest.TestCase):
    @staticmethod
    def _canonical_lifecycle_snapshot() -> dict[str, object]:
        return {
            "backup_api_copy": True,
            "immutable": True,
            "query_only": True,
            "integrity_check": ["ok"],
            "foreign_key_check_rows": 0,
            "sha256": "d" * 64,
            "logical_sha256": "e" * 64,
        }

    @staticmethod
    def _accepted_checkpoint_fixture(root: Path, *, auth_token: str = ""):
        subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "fixture@example.invalid"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "Fixture"], cwd=root, check=True)
        source = root / "app.py"
        source.write_text("VALUE = 1\n", encoding="utf-8")
        subprocess.run(["git", "add", "app.py"], cwd=root, check=True)
        subprocess.run(["git", "commit", "-m", "fixture"], cwd=root, check=True, capture_output=True)
        runtime = Runtime(root, auth_token=auth_token)
        state = runtime.task_state.ensure_started("activation source checkpoint fixture")
        identity = runtime._orchestration_workspace_identity(".")
        ctx = runtime.orchestration_control.begin(
            objective="activation source checkpoint fixture",
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
            allowed_paths=["app.py"],
        )
        source.write_text("VALUE = 2\n", encoding="utf-8")
        record_patch_surface(
            runtime.orchestration_ledger,
            run_id=ctx.run_id,
            wave_id=ctx.wave_id,
            patch_result={
                "affected_files": [{"path": "app.py"}],
                "additions": 1,
                "removals": 1,
                "dry_run": False,
            },
        )
        runtime.orchestration_control.begin_proof(ctx)
        runtime.orchestration_ledger.record_proof(
            run_id=ctx.run_id,
            wave_id=ctx.wave_id,
            stage_id="activation-fixture",
            stage_version="1",
            input_fingerprint="b" * 64,
            status="passed",
        )
        runtime.orchestration_control.mark_accepting(ctx, proof_summary={"proof": "green"})
        runtime.task_state.set_orchestration_projection(ctx.projection(), event="test_accepting_projection")
        runtime.task_control({"action": "accept", "run_id": ctx.run_id, "wave_id": ctx.wave_id})
        checkpoint = runtime.orchestration_ledger.list_checkpoints(ctx.run_id, wave_id=ctx.wave_id)[-1]
        return runtime, source, {
            "checkpoint_id": checkpoint["checkpoint_id"],
            "run_id": ctx.run_id,
            "wave_id": ctx.wave_id,
            "proof_fingerprint": checkpoint["proof_fingerprint"],
            "git_head": checkpoint["git_head"],
        }

    def test_get_control_activation_keeps_workspace_identity_when_busy(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            runtime = Runtime(root, auth_token="activation-token")
            runtime.active_tool_calls = 1
            server = RuntimeHTTPServer(("127.0.0.1", 0), MCPHandler, runtime, runtime_factory=None)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            port = int(server.server_address[1])
            try:
                connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
                connection.request("GET", "/__control/activation", headers={
                    "Authorization": "Bearer activation-token",
                })
                response = connection.getresponse()
                result = json.loads(response.read())
                connection.close()
                self.assertEqual(response.status, 200)
                self.assertFalse(result["safe"])
                self.assertEqual(result["code"], "RUNTIME_BUSY")
                self.assertEqual(result["workspace"], str(root))
            finally:
                runtime.active_tool_calls = 0
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)

    def test_authenticated_control_endpoint_prepares_and_cancels_fence(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp), auth_token="activation-token")
            server = RuntimeHTTPServer(("127.0.0.1", 0), MCPHandler, runtime, runtime_factory=None)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            port = int(server.server_address[1])
            operation_id = "activation-operation-http-0001"
            try:
                body = json.dumps({
                    "action": "prepare",
                    "operation_id": operation_id,
                    "expires_at_unix_ms": int(time.time() * 1000) + 30_000,
                    "workspace": str(Path(temp).resolve()),
                    "allow_acceptance_pending": False,
                })
                connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
                connection.request("POST", "/__control/activation", body=body, headers={
                    "Authorization": "Bearer activation-token",
                    "Content-Type": "application/json",
                    "Content-Length": str(len(body.encode("utf-8"))),
                })
                response = connection.getresponse()
                prepared = json.loads(response.read())
                self.assertEqual(response.status, 200)
                self.assertTrue(prepared["fenced"])
                connection.close()

                cancel_body = json.dumps({"action": "cancel", "operation_id": operation_id})
                connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
                connection.request("POST", "/__control/activation", body=cancel_body, headers={
                    "Authorization": "Bearer activation-token",
                    "Content-Type": "application/json",
                    "Content-Length": str(len(cancel_body.encode("utf-8"))),
                })
                response = connection.getresponse()
                cancelled = json.loads(response.read())
                self.assertEqual(response.status, 200)
                self.assertTrue(cancelled["cancelled"])
                connection.close()
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)

    def test_authenticated_prepare_verifies_exact_source_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            runtime, _source, source_checkpoint = self._accepted_checkpoint_fixture(
                root,
                auth_token="activation-token",
            )
            server = RuntimeHTTPServer(("127.0.0.1", 0), MCPHandler, runtime, runtime_factory=None)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            operation_id = "activation-source-checkpoint-http-0001"
            try:
                body = json.dumps({
                    "action": "prepare",
                    "operation_id": operation_id,
                    "expires_at_unix_ms": int(time.time() * 1000) + 30_000,
                    "workspace": str(root),
                    "allow_acceptance_pending": False,
                    "source_checkpoint": source_checkpoint,
                })
                connection = http.client.HTTPConnection("127.0.0.1", int(server.server_address[1]), timeout=5)
                connection.request("POST", "/__control/activation", body=body, headers={
                    "Authorization": "Bearer activation-token",
                    "Content-Type": "application/json",
                    "Content-Length": str(len(body.encode("utf-8"))),
                })
                response = connection.getresponse()
                prepared = json.loads(response.read())
                connection.close()
                self.assertEqual(response.status, 200)
                self.assertTrue(prepared["safe"])
                self.assertEqual(prepared["source_checkpoint"]["code"], "ACTIVATABLE")
                self.assertTrue(runtime.cancel_activation(operation_id))
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)
                runtime.close()

    def test_source_checkpoint_current_receipt_drift_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime, source, source_checkpoint = self._accepted_checkpoint_fixture(Path(temp).resolve())
            try:
                verified = runtime.activation_preflight(source_checkpoint=source_checkpoint)
                self.assertTrue(verified["safe"])
                self.assertEqual(verified["source_checkpoint"]["code"], "ACTIVATABLE")
                source.write_text("VALUE = 3\n", encoding="utf-8")
                refused = runtime.activation_preflight(source_checkpoint=source_checkpoint)
                self.assertFalse(refused["safe"])
                self.assertEqual(refused["code"], "SOURCE_DRIFT")
                self.assertEqual(refused["reason"], "accepted_source_receipt_changed")
            finally:
                runtime.close()

    def test_source_checkpoint_identity_receipts_chain_and_snapshot_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime, _source, source_checkpoint = self._accepted_checkpoint_fixture(Path(temp).resolve())
            try:
                wrong_proof = {**source_checkpoint, "proof_fingerprint": "c" * 64}
                self.assertEqual(
                    runtime.activation_preflight(source_checkpoint=wrong_proof)["code"],
                    "CHECKPOINT_NOT_ACTIVATABLE",
                )
                checkpoint = runtime.orchestration_ledger.list_checkpoints(
                    source_checkpoint["run_id"],
                    wave_id=source_checkpoint["wave_id"],
                )[-1]
                legacy = json.loads(json.dumps(checkpoint))
                legacy["metadata"]["accepted_files"]["schema_version"] = 1
                with patch.object(runtime.orchestration_ledger, "list_checkpoints", return_value=[legacy]):
                    self.assertEqual(
                        runtime.activation_preflight(source_checkpoint=source_checkpoint)["code"],
                        "RECEIPT_INCOMPLETE",
                    )
                invalid_extra_kind = json.loads(json.dumps(checkpoint))
                extra = Path(temp) / "extra.py"
                extra.write_text("EXTRA = True\n", encoding="utf-8")
                extra_bytes = extra.read_bytes()
                extra_sha256 = hashlib.sha256(extra_bytes).hexdigest()
                invalid_extra_kind["metadata"]["accepted_files"]["files"].append({
                    "path": "extra.py",
                    "state": "file",
                    "sha256": extra_sha256,
                    "size_bytes": len(extra_bytes),
                    "receipt_kind": "explicit_existing_file",
                    "run_id": source_checkpoint["run_id"],
                    "wave_id": source_checkpoint["wave_id"],
                    "restart_safe": True,
                    "content_addressed": True,
                    "expected_sha256": extra_sha256,
                })
                invalid_extra_kind["metadata"]["accepted_files"]["count"] += 1
                invalid_extra_kind["metadata"]["accepted_files"]["total_bytes"] += len(extra_bytes)
                with patch.object(runtime.orchestration_ledger, "list_checkpoints", return_value=[invalid_extra_kind]):
                    invalid_provenance = runtime.activation_preflight(source_checkpoint=source_checkpoint)
                    self.assertEqual(invalid_provenance["code"], "RECEIPT_INCOMPLETE")
                    self.assertEqual(invalid_provenance["reason"], "accepted_file_source_provenance_invalid")
                with patch.object(runtime.orchestration_ledger, "verify_chain", return_value={"ok": False}):
                    self.assertEqual(
                        runtime.activation_preflight(source_checkpoint=source_checkpoint)["reason"],
                        "ledger_integrity_failed",
                    )
                incomplete_lifecycle = {
                    "classification_counts": {},
                    "run_ids_by_class": {},
                    "unexplained_active_runs": 0,
                    "unbound_live_resource_residues": 0,
                    "p5_lifecycles": [],
                }
                with patch.object(runtime, "_activation_lifecycle_summary", return_value=incomplete_lifecycle):
                    self.assertEqual(
                        runtime.activation_preflight(source_checkpoint=source_checkpoint)["reason"],
                        "lifecycle_snapshot_integrity_failed",
                    )
                malformed_lifecycle = {
                    **incomplete_lifecycle,
                    "snapshot": {
                        "backup_api_copy": True,
                        "immutable": True,
                        "query_only": True,
                        "integrity_check": ["ok"],
                        "foreign_key_check_rows": "not-an-integer",
                        "sha256": "d" * 64,
                        "logical_sha256": "e" * 64,
                    },
                }
                with patch.object(runtime, "_activation_lifecycle_summary", return_value=malformed_lifecycle):
                    malformed = runtime.activation_preflight(source_checkpoint=source_checkpoint)
                    self.assertEqual(malformed["code"], "ORCHESTRATION_STATE_UNCERTAIN")
                    self.assertEqual(malformed["reason"], "lifecycle_snapshot_integrity_failed")
            finally:
                runtime.close()

    def test_prepare_fences_new_tool_calls_until_cancelled(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            operation_id = "activation-operation-0001"
            try:
                prepared = runtime.activation_preflight(
                    operation_id=operation_id,
                    expires_at_unix_ms=int(time.time() * 1000) + 30_000,
                    prepare=True,
                )
                self.assertTrue(prepared["safe"])
                self.assertTrue(prepared["fenced"])
                self.assertEqual(prepared["fence_operation_id"], operation_id)
                blocked = runtime.call_tool("server_info", {})
                self.assertTrue(blocked["isError"])
                self.assertEqual(
                    blocked["structuredContent"]["error"]["code"],
                    "RUNTIME_ACTIVATION_PENDING",
                )
                self.assertTrue(runtime.cancel_activation(operation_id))
                self.assertFalse(runtime.call_tool("server_info", {})["isError"])
            finally:
                runtime.close()

    def test_active_tool_call_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            try:
                runtime.active_tool_calls = 1
                result = runtime.activation_preflight()
                self.assertFalse(result["safe"])
                self.assertEqual(result["code"], "RUNTIME_BUSY")
                self.assertEqual(result["counts"]["active_tool_calls"], 1)
            finally:
                runtime.active_tool_calls = 0
                runtime.close()

    def test_activation_state_probe_failure_is_structured_and_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            try:
                with (
                    patch.object(
                        runtime.execution_resource_governor,
                        "foreign_heavy_processes",
                        return_value=[],
                    ),
                    patch.object(
                        runtime.orchestration_ledger,
                        "list_agent_lanes",
                        side_effect=sqlite3.OperationalError("missing durable activation state"),
                    ),
                ):
                    result = runtime.activation_preflight()
                self.assertFalse(result["safe"])
                self.assertEqual(result["code"], "ORCHESTRATION_STATE_UNCERTAIN")
                self.assertEqual(result["reason"], "activation_state_probe_failed")
                self.assertEqual(result["error_type"], "OperationalError")
            finally:
                runtime.close()

    def test_owned_codex_sidecar_is_quiesced_only_when_prepare_fences_restart(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            admission = runtime.execution_resource_governor.admit(
                command="codex app-server",
                command_id="codex-app-server-test-owned",
                owner="codex-app-server",
                resource_class="MEDIUM",
            )
            runtime._codex_bridge._managed_job_id = admission.job_id
            operation_id = "activation-codex-sidecar-0001"

            def close_sidecar() -> None:
                runtime.execution_resource_governor.complete(
                    admission.job_id,
                    lifecycle_state="closed",
                    exit_code=0,
                )
                runtime._codex_bridge._managed_job_id = ""

            try:
                inspected = runtime.activation_preflight()
                self.assertTrue(inspected["safe"])
                self.assertEqual(inspected["counts"]["active_managed_processes"], 0)
                with patch.object(runtime._codex_bridge, "close", side_effect=close_sidecar) as close:
                    prepared = runtime.activation_preflight(
                        operation_id=operation_id,
                        expires_at_unix_ms=int(time.time() * 1000) + 30_000,
                        prepare=True,
                    )
                self.assertTrue(prepared["safe"])
                self.assertTrue(prepared["fenced"])
                close.assert_called_once_with()
                self.assertEqual(
                    runtime.execution_resource_governor.snapshot()["active_command_count"],
                    0,
                )
                self.assertTrue(runtime.cancel_activation(operation_id))
            finally:
                runtime._codex_bridge._managed_job_id = ""
                runtime.execution_resource_governor.complete(
                    admission.job_id,
                    lifecycle_state="closed",
                    exit_code=0,
                )
                runtime.close()

    def test_owned_codex_sidecar_unbound_residue_is_closed_during_activation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            admission = runtime.execution_resource_governor.admit(
                command="codex app-server",
                command_id="codex-app-server-test-unbound",
                owner="codex-app-server",
                resource_class="MEDIUM",
            )
            runtime._codex_bridge._managed_job_id = admission.job_id
            lifecycle = {
                "classification_counts": {},
                "run_ids_by_class": {},
                "unexplained_active_runs": 0,
                "unbound_live_resource_residues": 1,
                "unbound_live_resources": [{
                    "resource_type": "managed_process_job",
                    "resource_id": admission.job_id,
                    "run_id": "",
                    "lifecycle_state": "running",
                }],
                "p5_lifecycles": [],
                "snapshot": self._canonical_lifecycle_snapshot(),
            }

            def close_sidecar() -> None:
                runtime.execution_resource_governor.complete(
                    admission.job_id,
                    lifecycle_state="closed",
                    exit_code=0,
                )
                runtime._codex_bridge._managed_job_id = ""

            try:
                with (
                    patch.object(runtime, "_activation_lifecycle_summary", return_value=lifecycle),
                    patch.object(runtime._codex_bridge, "close", side_effect=close_sidecar) as close,
                ):
                    prepared = runtime.activation_preflight(
                        operation_id="activation-codex-sidecar-unbound-0001",
                        expires_at_unix_ms=int(time.time() * 1000) + 30_000,
                        prepare=True,
                    )
                self.assertTrue(prepared["safe"])
                self.assertEqual(prepared["counts"]["owned_codex_sidecar_residues"], 1)
                close.assert_called_once_with()
                self.assertEqual(runtime.execution_resource_governor.snapshot()["active_command_count"], 0)
                self.assertTrue(runtime.cancel_activation("activation-codex-sidecar-unbound-0001"))
            finally:
                runtime._codex_bridge._managed_job_id = ""
                runtime.execution_resource_governor.complete(
                    admission.job_id,
                    lifecycle_state="closed",
                    exit_code=0,
                )
                runtime.close()

    def test_ordinary_medium_managed_work_still_blocks_activation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            admission = runtime.execution_resource_governor.admit(
                command="provider work",
                command_id="ordinary-medium-work",
                owner="opencode-provider",
                resource_class="MEDIUM",
            )
            try:
                result = runtime.activation_preflight()
                self.assertFalse(result["safe"])
                self.assertEqual(result["code"], "RUNTIME_BUSY")
                self.assertEqual(result["counts"]["active_managed_processes"], 1)
            finally:
                runtime.execution_resource_governor.complete(
                    admission.job_id,
                    lifecycle_state="closed",
                    exit_code=0,
                )
                runtime.close()

    def test_codex_sidecar_prepare_fails_closed_when_close_does_not_terminalize_job(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            admission = runtime.execution_resource_governor.admit(
                command="codex app-server",
                command_id="codex-app-server-test-stuck",
                owner="codex-app-server",
                resource_class="MEDIUM",
            )
            runtime._codex_bridge._managed_job_id = admission.job_id
            try:
                self.assertTrue(runtime.activation_preflight()["safe"])
                with patch.object(runtime._codex_bridge, "close", return_value=None):
                    refused = runtime.activation_preflight(
                        operation_id="activation-codex-sidecar-0002",
                        expires_at_unix_ms=int(time.time() * 1000) + 30_000,
                        prepare=True,
                    )
                self.assertFalse(refused["safe"])
                self.assertEqual(refused["code"], "RUNTIME_BUSY")
                self.assertEqual(refused["reason"], "internal_service_quiescence_failed")
                self.assertEqual(refused["counts"]["active_managed_processes"], 1)
                self.assertIsNone(runtime.activation_fence)
            finally:
                runtime._codex_bridge._managed_job_id = ""
                runtime.execution_resource_governor.complete(
                    admission.job_id,
                    lifecycle_state="closed",
                    exit_code=0,
                )
                runtime.close()

    def test_accepting_requires_explicit_preservation_and_valid_integrity(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            try:
                active_run = {"run_id": "run-accepting"}
                accepting = SimpleNamespace(state="ACCEPTING")
                with (
                    patch.object(runtime.orchestration_ledger, "current_active_execution_run", return_value=active_run),
                    patch.object(runtime.orchestration_control, "snapshot", return_value=accepting),
                    patch.object(runtime.orchestration_ledger, "verify_chain", return_value={"ok": True}),
                ):
                    refused = runtime.activation_preflight()
                    self.assertFalse(refused["safe"])
                    self.assertEqual(refused["code"], "ACCEPTANCE_PENDING")
                    allowed = runtime.activation_preflight(allow_acceptance_pending=True)
                    self.assertTrue(allowed["safe"])
                    self.assertTrue(allowed["acceptance_pending"])
            finally:
                runtime.close()

    def test_non_accepting_active_orchestration_and_bad_integrity_are_refused(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            try:
                active_run = {"run_id": "run-active"}
                with (
                    patch.object(runtime.orchestration_ledger, "current_active_execution_run", return_value=active_run),
                    patch.object(runtime.orchestration_control, "snapshot", return_value=SimpleNamespace(state="PROVING")),
                    patch.object(runtime.orchestration_ledger, "verify_chain", return_value={"ok": True}),
                ):
                    self.assertEqual(runtime.activation_preflight()["code"], "RUNTIME_BUSY")
                with (
                    patch.object(runtime.orchestration_ledger, "current_active_execution_run", return_value=active_run),
                    patch.object(runtime.orchestration_control, "snapshot", return_value=SimpleNamespace(state="ACCEPTING")),
                    patch.object(runtime.orchestration_ledger, "verify_chain", return_value={"ok": False}),
                ):
                    self.assertEqual(
                        runtime.activation_preflight(allow_acceptance_pending=True)["code"],
                        "ORCHESTRATION_STATE_UNCERTAIN",
                    )
            finally:
                runtime.close()

    def test_threshold_sensitive_rows_do_not_block_activation_or_call_writer_accessor(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            lifecycle = {
                "classification_counts": {"THRESHOLD_SENSITIVE_STALE_CANDIDATE": 3},
                "run_ids_by_class": {"THRESHOLD_SENSITIVE_STALE_CANDIDATE": ["run-threshold"]},
                "unexplained_active_runs": 0,
                "unbound_live_resource_residues": 0,
                "p5_lifecycles": ["EPOCH_CLOSED"],
                "snapshot": self._canonical_lifecycle_snapshot(),
            }
            try:
                with (
                    patch.object(runtime, "_activation_lifecycle_summary", return_value=lifecycle),
                    patch.object(runtime.orchestration_ledger, "current_active_execution_run", side_effect=AssertionError("must not query writer accessor")),
                ):
                    result = runtime.activation_preflight()
                self.assertTrue(result["safe"])
                self.assertEqual(result["orchestration_state"], "QUIESCENT_WITH_THRESHOLD_CANDIDATES")
                self.assertEqual(result["counts"]["threshold_sensitive_stale_candidates"], 3)
            finally:
                runtime.close()

    def test_unexplained_lifecycle_residue_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            lifecycle = {
                "classification_counts": {"UNEXPLAINED_ACTIVE": 1},
                "run_ids_by_class": {"UNEXPLAINED_ACTIVE": ["run-unknown"]},
                "unexplained_active_runs": 1,
                "unbound_live_resource_residues": 0,
                "p5_lifecycles": [],
                "snapshot": self._canonical_lifecycle_snapshot(),
            }
            try:
                with patch.object(runtime, "_activation_lifecycle_summary", return_value=lifecycle):
                    result = runtime.activation_preflight()
                self.assertFalse(result["safe"])
                self.assertEqual(result["code"], "ORCHESTRATION_STATE_UNCERTAIN")
                self.assertEqual(result["reason"], "lifecycle_unexplained_or_unbound")
            finally:
                runtime.close()


if __name__ == "__main__":
    unittest.main()
