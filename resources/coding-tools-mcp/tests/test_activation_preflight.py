from __future__ import annotations

import hashlib
import hmac
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

from coding_tools_mcp.errors import ToolFailure
from coding_tools_mcp.activation_capability import (
    recovery_activation_capability,
    recovery_activation_ignore_active_tool_calls,
    valid_activation_operation_id,
)
from coding_tools_mcp.server import MCPHandler, Runtime, RuntimeHTTPServer
from coding_tools_mcp.solution_economics import record_patch_surface


class ActivationPreflightTests(unittest.TestCase):
    def test_activation_operation_id_validation_is_strictly_typed_and_untrimmed(self) -> None:
        valid = "restart-operation-0001"
        for value, expected in (
            (valid, True),
            (f" {valid}", False),
            (valid.encode("utf-8"), False),
            (1234567890123456, False),
            (None, False),
        ):
            with self.subTest(value=value):
                self.assertEqual(valid_activation_operation_id(value), expected)

    def test_recovery_activation_capability_authenticates_operation_without_ignoring_self_call(self) -> None:
        handler = object.__new__(MCPHandler)
        token = "activation-token"
        operation_id = "activation-operation-http-0002"
        handler._runtime = SimpleNamespace(auth_token=token)
        handler.headers = {
            "Authorization": f"Bearer {token}",
            "X-Coding-Tools-Activation-Operation": operation_id,
            "X-Coding-Tools-Activation-Proof": hmac.new(
                token.encode("utf-8"),
                f"coding-tools-mcp-activation-preflight:{operation_id}".encode("utf-8"),
                hashlib.sha256,
            ).hexdigest(),
        }
        self.assertEqual(recovery_activation_capability(handler.headers, handler._runtime), {
            "operation_id": operation_id,
            "ignore_active_tool_calls": 0,
        })
        self.assertEqual(recovery_activation_ignore_active_tool_calls(handler.headers, handler._runtime), 0)
        handler.headers["X-Coding-Tools-Activation-Proof"] = "0" * 64
        self.assertEqual(recovery_activation_capability(handler.headers, handler._runtime), {
            "operation_id": "",
            "ignore_active_tool_calls": 0,
        })
        self.assertEqual(recovery_activation_ignore_active_tool_calls(handler.headers, handler._runtime), 0)
        handler.headers["Authorization"] = "Bearer another-token"
        self.assertEqual(recovery_activation_ignore_active_tool_calls(handler.headers, handler._runtime), 0)

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

    def test_workspace_identity_rejects_truncated_git_status(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            try:
                with patch.object(runtime, "git_status", return_value={
                    "is_repo": True,
                    "branch": "main",
                    "head": "a" * 40,
                    "entries": [],
                    "truncated": True,
                }):
                    with self.assertRaises(ToolFailure) as truncated:
                        runtime._orchestration_workspace_identity(".")
                self.assertEqual(truncated.exception.code, "WORKTREE_STATUS_TRUNCATED")
            finally:
                runtime.close()

    @staticmethod
    def _accepted_checkpoint_fixture(root: Path, *, auth_token: str = "", mutate: bool = True):
        subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "fixture@example.invalid"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "Fixture"], cwd=root, check=True)
        source = root / "app.py"
        source.write_text("VALUE = 1\n", encoding="utf-8")
        unrelated = root / "unrelated.py"
        unrelated.write_text("OTHER = 1\n", encoding="utf-8")
        subprocess.run(["git", "add", "app.py", "unrelated.py"], cwd=root, check=True)
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
            allowed_paths=["app.py"] if mutate else [],
        )
        if mutate:
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
        if mutate:
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
                self.assertEqual(prepared["operation_id"], operation_id)
                self.assertEqual(prepared["source_checkpoint"]["code"], "ACTIVATABLE")
                self.assertTrue(runtime.cancel_activation(operation_id))
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)
                runtime.close()

    def test_authenticated_verify_forwards_acceptance_pending_policy(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            runtime = Runtime(root, auth_token="activation-token")
            server = RuntimeHTTPServer(("127.0.0.1", 0), MCPHandler, runtime, runtime_factory=None)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            operation_id = "activation-verify-policy-http-0001"
            source_checkpoint = {
                "checkpoint_id": "checkpoint-verify-policy-0001",
                "run_id": "run-verify-policy-0001",
                "wave_id": "wave-verify-policy-0001",
                "proof_fingerprint": "a" * 64,
                "git_head": "b" * 40,
            }

            def activation_preflight(**kwargs: object) -> dict[str, object]:
                allowed = kwargs.get("allow_acceptance_pending") is True
                return {
                    "safe": allowed,
                    "code": "READY" if allowed else "ACCEPTANCE_PENDING",
                    "workspace": str(root),
                    "acceptance_pending": True,
                    "fenced": False,
                    "fence_operation_id": None,
                }

            try:
                with patch.object(runtime, "activation_preflight", side_effect=activation_preflight) as preflight:
                    for allowed, expected_status, expected_code in (
                        (False, 409, "ACCEPTANCE_PENDING"),
                        (True, 200, "READY"),
                    ):
                        with self.subTest(allow_acceptance_pending=allowed):
                            body = json.dumps({
                                "action": "verify",
                                "operation_id": operation_id,
                                "workspace": str(root),
                                "source_checkpoint": source_checkpoint,
                                "allow_acceptance_pending": allowed,
                            })
                            connection = http.client.HTTPConnection(
                                "127.0.0.1",
                                int(server.server_address[1]),
                                timeout=5,
                            )
                            connection.request("POST", "/__control/activation", body=body, headers={
                                "Authorization": "Bearer activation-token",
                                "Content-Type": "application/json",
                                "Content-Length": str(len(body.encode("utf-8"))),
                            })
                            response = connection.getresponse()
                            result = json.loads(response.read())
                            connection.close()

                            self.assertEqual(response.status, expected_status)
                            self.assertEqual(result["code"], expected_code)

                    self.assertEqual(
                        [call.kwargs["allow_acceptance_pending"] for call in preflight.call_args_list],
                        [False, True],
                    )
                    for call in preflight.call_args_list:
                        self.assertTrue(call.kwargs["require_unfenced"])
                        self.assertFalse(call.kwargs["prepare"])
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

    def test_source_checkpoint_unreceipted_dirty_source_drift_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            runtime, _source, source_checkpoint = self._accepted_checkpoint_fixture(root)
            try:
                self.assertTrue(runtime.activation_preflight(source_checkpoint=source_checkpoint)["safe"])
                (root / "unrelated.py").write_text("OTHER = 2\n", encoding="utf-8")
                refused = runtime.activation_preflight(source_checkpoint=source_checkpoint)
                self.assertFalse(refused["safe"])
                self.assertEqual(refused["code"], "SOURCE_DRIFT")
                self.assertEqual(refused["reason"], "worktree_fingerprint_changed")
            finally:
                runtime.close()

    def test_true_no_mutation_checkpoint_is_exactly_activatable(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime, _source, source_checkpoint = self._accepted_checkpoint_fixture(
                Path(temp).resolve(),
                mutate=False,
            )
            try:
                self.assertEqual(source_checkpoint["proof_fingerprint"], "")
                verified = runtime.activation_preflight(source_checkpoint=source_checkpoint)
                self.assertTrue(verified["safe"])
                self.assertEqual(verified["source_checkpoint"]["code"], "ACTIVATABLE")
                self.assertEqual(verified["source_checkpoint"]["accepted_file_count"], 0)
            finally:
                runtime.close()

    def test_empty_proof_is_rejected_for_mutation_bearing_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime, _source, source_checkpoint = self._accepted_checkpoint_fixture(Path(temp).resolve())
            try:
                refused = runtime.activation_preflight(source_checkpoint={
                    **source_checkpoint,
                    "proof_fingerprint": "",
                })
                self.assertFalse(refused["safe"])
                self.assertEqual(refused["code"], "CHECKPOINT_NOT_ACTIVATABLE")
                self.assertIn(refused["reason"], {"checkpoint_identity_mismatch", "proof_fingerprint_mismatch"})
            finally:
                runtime.close()

    def test_source_checkpoint_noncanonical_authority_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime, _source, source_checkpoint = self._accepted_checkpoint_fixture(Path(temp).resolve())
            try:
                invalid_values = []
                for field in ("checkpoint_id", "run_id", "wave_id"):
                    invalid_values.extend([
                        {**source_checkpoint, field: f" {source_checkpoint[field]}"},
                        {**source_checkpoint, field: f"{source_checkpoint[field]} "},
                        {**source_checkpoint, field: 123},
                    ])
                invalid_values.extend([
                    {**source_checkpoint, "proof_fingerprint": source_checkpoint["proof_fingerprint"].upper()},
                    {**source_checkpoint, "proof_fingerprint": f" {source_checkpoint['proof_fingerprint']}"},
                    {**source_checkpoint, "proof_fingerprint": 123},
                    {**source_checkpoint, "git_head": source_checkpoint["git_head"].upper()},
                    {**source_checkpoint, "git_head": f"{source_checkpoint['git_head']} "},
                    {**source_checkpoint, "git_head": 123},
                ])
                for invalid in invalid_values:
                    with self.subTest(invalid=invalid):
                        result = runtime.activation_preflight(source_checkpoint=invalid)
                        self.assertEqual(result["code"], "CHECKPOINT_NOT_ACTIVATABLE")
                        self.assertEqual(result["reason"], "source_checkpoint_identity_invalid")
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
                for label, snapshot_patch in (
                    ("integrity", {"integrity_check": ["corrupt"]}),
                    ("foreign-keys", {"foreign_key_check_rows": 1}),
                    ("mutable", {"immutable": False}),
                    ("writer-enabled", {"query_only": False}),
                    ("physical-sha", {"sha256": "bad"}),
                    ("logical-sha", {"logical_sha256": "bad"}),
                ):
                    with self.subTest(snapshot=label), patch.object(
                        runtime,
                        "_activation_lifecycle_summary",
                        return_value={
                            **incomplete_lifecycle,
                            "snapshot": {**self._canonical_lifecycle_snapshot(), **snapshot_patch},
                        },
                    ):
                        refused = runtime.activation_preflight(source_checkpoint=source_checkpoint)
                        self.assertEqual(refused["code"], "ORCHESTRATION_STATE_UNCERTAIN")
                        self.assertEqual(refused["reason"], "lifecycle_snapshot_integrity_failed")
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
                self.assertEqual(prepared["operation_id"], operation_id)
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

    def test_prepare_rejects_operation_ids_with_non_alphanumeric_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            try:
                for operation_id in ("_activation-operation-0001", "-activation-operation-0001"):
                    with self.subTest(operation_id=operation_id), self.assertRaises(ToolFailure) as raised:
                        runtime.activation_preflight(
                            operation_id=operation_id,
                            expires_at_unix_ms=int(time.time() * 1000) + 30_000,
                            prepare=True,
                        )
                    self.assertEqual(raised.exception.code, "INVALID_OPERATION_ID")
                    self.assertIsNone(runtime.activation_fence)
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

    def test_signed_snapshot_reuses_exact_fence_only_after_restart_tool_call_leaves(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            operation_id = "activation-deferred-restart-0001"
            try:
                prepared = runtime.activation_preflight(
                    operation_id=operation_id,
                    expires_at_unix_ms=int(time.time() * 1000) + 30_000,
                    prepare=True,
                )
                self.assertTrue(prepared["safe"])
                self.assertTrue(prepared["fenced"])
                runtime.active_tool_calls = 1
                while_active = runtime.activation_preflight_snapshot(
                    operation_id=operation_id,
                )
                self.assertFalse(while_active["safe"])
                self.assertEqual(while_active["code"], "RUNTIME_BUSY")
                self.assertEqual(while_active["counts"]["active_tool_calls"], 1)
                runtime.active_tool_calls = 0
                same_operation = runtime.activation_preflight_snapshot(
                    operation_id=operation_id,
                )
                self.assertTrue(same_operation["safe"])
                self.assertEqual(same_operation["fence_operation_id"], operation_id)
                foreign = runtime.activation_preflight_snapshot(
                    operation_id="activation-deferred-restart-other",
                )
                self.assertFalse(foreign["safe"])
                self.assertEqual(foreign["code"], "RUNTIME_BUSY")
                self.assertTrue(runtime.cancel_activation(operation_id))
            finally:
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

    def test_paused_replan_exact_self_controller_is_discounted_only_for_restart_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            run_id = "run-paused-self-controller"
            identity = {
                "client_id": "chatweb-test",
                "client_type": "chatweb",
                "execution_context_id": "execution-context-1234567890",
            }
            client_id = runtime._hub_client_record_id(identity)
            lifecycle = {
                "classification_counts": {"LIVE_OWNED": 1},
                "run_ids_by_class": {"LIVE_OWNED": [run_id]},
                "live_owned_runs": [{
                    "run_id": run_id,
                    "run_status": "active",
                    "latest_state_after": "REPLAN",
                    "ownership": {
                        "active_controller_leases": 1,
                        "active_write_fences": 0,
                        "running_background_operations": 0,
                        "live_agent_lanes": 0,
                        "live_managed_jobs": 0,
                    },
                }],
                "unexplained_active_runs": 0,
                "unbound_live_resource_residues": 0,
                "p5_lifecycles": [],
                "snapshot": self._canonical_lifecycle_snapshot(),
            }
            task = {"status": "paused", "orchestration": {"run_id": run_id}}
            lease = {
                "run_id": run_id,
                "status": "active",
                "owner_client_id": client_id,
                "lease_id": f"client:{client_id}",
            }
            try:
                with (
                    patch.object(runtime, "_activation_lifecycle_summary", return_value=lifecycle),
                    patch.object(runtime.task_state, "get", return_value=task),
                    patch.object(runtime, "_current_hub_client", return_value=identity),
                    patch.object(runtime.orchestration_ledger, "peek_controller_lease", return_value=lease),
                    patch.object(runtime.orchestration_control, "snapshot", return_value=SimpleNamespace(state="REPLAN")),
                    patch.object(runtime.orchestration_ledger, "verify_chain", return_value={"ok": True}),
                    patch.object(runtime.orchestration_ledger, "current_active_execution_run", return_value={"run_id": run_id}),
                ):
                    ordinary = runtime.activation_preflight()
                    allowed = runtime.activation_preflight(allow_self_controller_lease=True)
                self.assertFalse(ordinary["safe"])
                self.assertEqual(ordinary["reason"], "lifecycle_live_owned")
                self.assertTrue(allowed["safe"])
                self.assertEqual(allowed["reason"], "paused_replan_self_controller_is_quiescent")
                self.assertEqual(allowed["orchestration_state"], "QUIESCENT_REPLAN_WITH_SELF_CONTROLLER")
                self.assertEqual(allowed["counts"]["self_controller_leases_discounted"], 1)
            finally:
                runtime.close()

    def test_self_controller_discount_fails_closed_for_foreign_or_additional_ownership(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            run_id = "run-self-controller-unsafe"
            identity = {
                "client_id": "chatweb-test",
                "client_type": "chatweb",
                "execution_context_id": "execution-context-1234567890",
            }
            client_id = runtime._hub_client_record_id(identity)
            base_ownership = {
                "active_controller_leases": 1,
                "active_write_fences": 0,
                "running_background_operations": 0,
                "live_agent_lanes": 0,
                "live_managed_jobs": 0,
            }
            task = {"status": "paused", "orchestration": {"run_id": run_id}}
            try:
                for label, ownership, owner, task_status in (
                    ("foreign-controller", base_ownership, "another-client", "paused"),
                    ("write-fence", {**base_ownership, "active_write_fences": 1}, client_id, "paused"),
                    ("task-not-paused", base_ownership, client_id, "active"),
                ):
                    lifecycle = {
                        "classification_counts": {"LIVE_OWNED": 1},
                        "run_ids_by_class": {"LIVE_OWNED": [run_id]},
                        "live_owned_runs": [{
                            "run_id": run_id,
                            "run_status": "active",
                            "latest_state_after": "REPLAN",
                            "ownership": ownership,
                        }],
                        "unexplained_active_runs": 0,
                        "unbound_live_resource_residues": 0,
                        "p5_lifecycles": [],
                        "snapshot": self._canonical_lifecycle_snapshot(),
                    }
                    lease = {"run_id": run_id, "status": "active", "owner_client_id": owner}
                    with (
                        self.subTest(label=label),
                        patch.object(runtime, "_activation_lifecycle_summary", return_value=lifecycle),
                        patch.object(runtime.task_state, "get", return_value={**task, "status": task_status}),
                        patch.object(runtime, "_current_hub_client", return_value=identity),
                        patch.object(runtime.orchestration_ledger, "peek_controller_lease", return_value=lease),
                        patch.object(runtime.orchestration_control, "snapshot", return_value=SimpleNamespace(state="REPLAN")),
                        patch.object(runtime.orchestration_ledger, "verify_chain", return_value={"ok": True}),
                    ):
                        refused = runtime.activation_preflight(allow_self_controller_lease=True)
                    self.assertFalse(refused["safe"])
                    self.assertEqual(refused["reason"], "lifecycle_live_owned")
                    self.assertEqual(refused["counts"]["self_controller_leases_discounted"], 0)
            finally:
                runtime.close()

    def test_lifecycle_summary_projects_live_owned_ownership_from_same_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            run_id = "run-live-owned-summary"
            ownership = {
                "active_controller_leases": 1,
                "active_write_fences": 0,
                "running_background_operations": 0,
                "live_agent_lanes": 0,
                "live_managed_jobs": 0,
            }
            census = {
                "snapshot": self._canonical_lifecycle_snapshot(),
                "summary": {
                    "run_classification_counts": {"LIVE_OWNED": 1},
                    "unexplained_active_runs": 0,
                    "unbound_live_resource_residues": 0,
                },
                "projection": {},
                "runs": [{
                    "run_id": run_id,
                    "run_status": "active",
                    "classification": "LIVE_OWNED",
                    "latest_state_after": "REPLAN",
                    "ownership": ownership,
                }],
                "unbound_live_resources": [],
            }
            try:
                with (
                    patch.object(runtime, "_projection_rebuild_census", return_value=census),
                    patch.object(runtime, "projection_rebuild_snapshot", return_value={}),
                ):
                    summary = runtime._activation_lifecycle_summary()
                self.assertEqual(summary["run_ids_by_class"]["LIVE_OWNED"], [run_id])
                self.assertEqual(summary["live_owned_runs"], [{
                    "run_id": run_id,
                    "run_status": "active",
                    "latest_state_after": "REPLAN",
                    "ownership": ownership,
                }])
            finally:
                runtime.close()

    def test_restart_runtime_enables_only_bounded_self_controller_preflight_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workspace = root / "workspace"
            control = root / "control"
            workspace.mkdir()
            control.mkdir()
            ticket_path = control / "runtime-supervisor-request.json"
            with patch.dict("os.environ", {"CODING_TOOLS_MCP_SUPERVISOR_REQUEST_FILE": str(ticket_path)}):
                runtime = Runtime(workspace)
                try:
                    with patch.object(runtime, "activation_preflight", return_value={
                        "safe": False,
                        "code": "RUNTIME_BUSY",
                        "reason": "sentinel",
                    }) as preflight:
                        with self.assertRaises(ToolFailure) as raised:
                            runtime._enqueue_runtime_restart({"confirm_restart": True, "reason": "test restart"})
                    self.assertEqual(raised.exception.code, "RUNTIME_BUSY")
                    self.assertTrue(preflight.call_args.kwargs["allow_self_controller_lease"])
                    self.assertEqual(preflight.call_args.kwargs["ignore_active_tool_calls"], 1)
                    self.assertFalse(ticket_path.exists())
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

    def test_projection_drift_fails_closed_but_correct_terminal_projection_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            base = {
                "classification_counts": {},
                "run_ids_by_class": {},
                "unexplained_active_runs": 0,
                "unbound_live_resource_residues": 0,
                "p5_lifecycles": [],
                "snapshot": self._canonical_lifecycle_snapshot(),
            }
            try:
                with patch.object(runtime, "_activation_lifecycle_summary", return_value={
                    **base,
                    "projection": {"classification": "PROJECTION_DRIFT"},
                    "projection_classification": "PROJECTION_DRIFT",
                }):
                    refused = runtime.activation_preflight()
                self.assertFalse(refused["safe"])
                self.assertEqual(refused["code"], "ORCHESTRATION_STATE_UNCERTAIN")
                self.assertEqual(refused["reason"], "projection_drift")
                with patch.object(runtime, "_activation_lifecycle_summary", return_value={
                    **base,
                    "projection": {"classification": "CHECKPOINTED"},
                    "projection_classification": "CHECKPOINTED",
                }):
                    allowed = runtime.activation_preflight()
                self.assertTrue(allowed["safe"])
            finally:
                runtime.close()


if __name__ == "__main__":
    unittest.main()
