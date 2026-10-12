from __future__ import annotations

import http.client
import json
import tempfile
import threading
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from coding_tools_mcp.errors import ToolFailure
from coding_tools_mcp.server import MCPHandler, Runtime, RuntimeHTTPServer
from coding_tools_mcp.windows_mxc_state_aware import MxcWindowsSandboxManager


class OwnedManager:
    close_timeout_seconds = 425

    def __init__(self, outcome: bool = True) -> None:
        self.started = threading.Event()
        self.release = threading.Event()
        self.outcome = outcome
        self.calls = 0

    def close(self) -> bool:
        self.calls += 1
        self.started.set()
        if not self.release.wait(5):
            raise AssertionError("test did not release owned cleanup")
        return self.outcome


class ActivationExecutorCleanupTests(unittest.TestCase):
    operation = "activation-executor-cleanup-0001"

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.runtime = Runtime(Path(self.temporary.name), auth_token="cleanup-test-token")
        self.manager = OwnedManager()
        self.runtime._windows_mxc_sandbox_manager = self.manager

    def tearDown(self) -> None:
        self.manager.release.set()
        self.runtime.close()
        self.temporary.cleanup()

    def prepare(self, *, operation: str | None = None) -> dict:
        return self.runtime.activation_preflight(
            operation_id=operation or self.operation,
            expires_at_unix_ms=int(time.time() * 1000) + 55_000,
            prepare=True,
        )

    def wait_terminal(self) -> dict:
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            with self.runtime.activation_lock:
                cleanup = self.runtime._activation_executor_cleanup_locked()
                if cleanup and cleanup["state"] != "pending":
                    return cleanup
            time.sleep(0.001)
        self.fail("owned cleanup did not settle")

    def test_prepare_returns_pending_without_holding_activation_lock(self) -> None:
        result = self.prepare()
        self.assertFalse(result["safe"])
        self.assertEqual(result["code"], "SANDBOX_CLEANUP_PENDING")
        self.assertEqual(result["operation_id"], self.operation)
        self.assertEqual(result["workspace"], str(self.runtime.workspace.root))
        self.assertEqual(result["process_instance_id"], self.runtime.process_instance_id)
        self.assertEqual(result["server_instance_id"], self.runtime.server_instance_id)
        self.assertTrue(self.manager.started.wait(1))
        self.assertTrue(self.runtime.activation_lock.acquire(timeout=0.1))
        self.runtime.activation_lock.release()
        health = self.runtime.activation_admission_snapshot(blocking=False)
        self.assertFalse(health["admission_open"])
        self.assertFalse(health["snapshot_busy"])
        self.assertEqual(result["executor_cleanup"]["deadline_at_unix_ms"] - result["executor_cleanup"]["started_at_unix_ms"], 430_000)

    def test_same_operation_refresh_keeps_single_cleanup_and_fixed_deadline(self) -> None:
        first = self.prepare()
        self.assertTrue(self.manager.started.wait(1))
        self.runtime.activation_fence["expires_at_unix_ms"] = 1
        second = self.prepare()
        self.assertEqual(second["code"], "SANDBOX_CLEANUP_PENDING")
        self.assertEqual(first["executor_cleanup"], second["executor_cleanup"])
        self.assertGreater(second["expires_at_unix_ms"], int(time.time() * 1000))
        self.assertEqual(self.manager.calls, 1)

    def test_expired_fence_does_not_reopen_pending_cleanup_admission(self) -> None:
        self.prepare()
        self.runtime.activation_fence["expires_at_unix_ms"] = 1
        for name, args in (("workspace_context", {}), ("task_control", {"action": "restart_runtime", "confirm_restart": True})):
            with self.subTest(name=name), self.assertRaises(ToolFailure) as blocked:
                self.runtime._activation_enter_tool_call(name, args)
            self.assertEqual(blocked.exception.code, "SANDBOX_CLEANUP_PENDING")
        self.assertEqual(self.runtime.active_tool_calls, 0)
        with self.assertRaises(ToolFailure) as cancelled:
            self.runtime.cancel_activation(self.operation)
        self.assertEqual(cancelled.exception.code, "SANDBOX_CLEANUP_PENDING")
        self.assertFalse(self.runtime.activation_admission_snapshot()["admission_open"])

    def test_direct_exec_admission_cannot_race_cleanup_after_fence_expiry(self) -> None:
        self.prepare()
        self.runtime.activation_fence["expires_at_unix_ms"] = 1
        with patch.object(self.runtime, "_check_command_policy"), patch.object(self.runtime, "landlock_enabled", return_value=False):
            with patch("coding_tools_mcp.exec_tools.spawn_process") as spawn:
                with self.assertRaises(ToolFailure) as blocked:
                    self.runtime.exec_command({"cmd": "echo blocked"})
        self.assertEqual(blocked.exception.code, "SANDBOX_CLEANUP_PENDING")
        spawn.assert_not_called()
        self.assertEqual(self.runtime.starting_sessions, 0)

    def test_other_operation_cannot_cancel_or_adopt_owned_cleanup(self) -> None:
        self.prepare()
        other = "activation-executor-cleanup-0002"
        result = self.prepare(operation=other)
        self.assertFalse(result["safe"])
        self.assertEqual(result["operation_id"], self.operation)
        self.assertEqual(self.runtime.activation_fence["operation_id"], self.operation)
        with self.assertRaises(ToolFailure) as wrong_owner:
            self.runtime.cancel_activation(other)
        self.assertEqual(wrong_owner.exception.code, "ACTIVATION_OPERATION_MISMATCH")

    def test_confirmed_close_discards_manager_then_fresh_prepare_and_cancel_resume(self) -> None:
        self.prepare()
        self.manager.release.set()
        self.assertEqual(self.wait_terminal()["state"], "completed")
        self.assertIsNone(self.runtime._windows_mxc_sandbox_manager)
        ready = self.prepare()
        self.assertTrue(ready["safe"])
        self.assertEqual(ready["executor_cleanup"]["state"], "completed")
        self.assertTrue(ready["executor_cleanup"]["confirmed"])
        self.assertTrue(self.runtime.cancel_activation(self.operation))
        self.runtime._activation_enter_tool_call("workspace_context", {})
        self.runtime._activation_leave_tool_call()
        self.assertEqual(self.manager.calls, 1)

    def test_cleanup_failure_retains_manager_and_blocks_cancel_and_restart(self) -> None:
        self.manager.outcome = False
        self.prepare()
        self.manager.release.set()
        self.assertEqual(self.wait_terminal()["state"], "failed")
        self.assertIs(self.runtime._windows_mxc_sandbox_manager, self.manager)
        result = self.prepare()
        self.assertFalse(result["safe"])
        self.assertEqual(result["code"], "SANDBOX_TEARDOWN_UNCONFIRMED")
        with self.assertRaises(ToolFailure) as cancelled:
            self.runtime.cancel_activation(self.operation)
        self.assertEqual(cancelled.exception.code, "SANDBOX_TEARDOWN_UNCONFIRMED")

    def test_cleanup_deadline_is_terminal_even_if_thread_later_confirms(self) -> None:
        self.prepare()
        with self.runtime.activation_lock:
            self.runtime._activation_executor_cleanup["deadline_monotonic"] = 0
        self.assertEqual(self.prepare()["code"], "SANDBOX_TEARDOWN_UNCONFIRMED")
        self.manager.release.set()
        self.assertEqual(self.wait_terminal()["state"], "failed")
        self.assertIs(self.runtime._windows_mxc_sandbox_manager, self.manager)

    def test_manager_identity_change_cannot_be_cleared_by_old_thread(self) -> None:
        self.prepare()
        replacement = OwnedManager()
        replacement.release.set()
        self.runtime._windows_mxc_sandbox_manager = replacement
        self.manager.release.set()
        self.assertEqual(self.wait_terminal()["state"], "failed")
        self.assertIs(self.runtime._windows_mxc_sandbox_manager, replacement)

    def test_live_or_starting_commands_prevent_owned_cleanup(self) -> None:
        self.runtime.starting_sessions = 1
        try:
            self.assertEqual(self.prepare()["code"], "RUNTIME_BUSY")
            self.assertFalse(self.manager.started.is_set())
        finally:
            self.runtime.starting_sessions = 0
        self.runtime.sessions["fixture"] = SimpleNamespace(process=SimpleNamespace(poll=lambda: None))
        try:
            self.assertEqual(self.prepare()["code"], "RUNTIME_BUSY")
            self.assertFalse(self.manager.started.is_set())
        finally:
            self.runtime.sessions.clear()

    def test_read_only_preflight_never_starts_cleanup_and_no_manager_prepare_is_explicit(self) -> None:
        self.assertTrue(self.runtime.activation_preflight()["safe"])
        self.assertTrue(self.runtime.activation_preflight_snapshot()["executor_cleanup_supported"])
        self.assertFalse(self.manager.started.is_set())
        self.runtime._windows_mxc_sandbox_manager = None
        ready = self.prepare()
        self.assertTrue(ready["safe"])
        self.assertEqual(ready["executor_cleanup"], {"state": "not_required", "confirmed": True})

    def test_authenticated_http_prepare_is_bounded_pending_409_and_cancel_stays_closed(self) -> None:
        server = RuntimeHTTPServer(("127.0.0.1", 0), MCPHandler, self.runtime, runtime_factory=None)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        def request(payload: dict, token: str = "cleanup-test-token") -> tuple[int, dict]:
            connection = http.client.HTTPConnection("127.0.0.1", int(server.server_address[1]), timeout=2)
            body = json.dumps(payload)
            connection.request("POST", "/__control/activation", body=body, headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
            response = connection.getresponse()
            result = response.status, json.loads(response.read())
            connection.close()
            return result

        try:
            payload = {"action": "prepare", "operation_id": self.operation, "workspace": str(self.runtime.workspace.root), "expires_at_unix_ms": int(time.time() * 1000) + 55_000}
            unauthorized, _ = request(payload, token="wrong-test-token")
            self.assertEqual(unauthorized, 401)
            self.assertFalse(self.manager.started.is_set())
            status, pending = request(payload)
            self.assertEqual(status, 409)
            self.assertEqual(pending["code"], "SANDBOX_CLEANUP_PENDING")
            self.assertTrue(pending["executor_cleanup_supported"])
            status, cancelled = request({"action": "cancel", "operation_id": self.operation})
            self.assertEqual(status, 409)
            self.assertEqual(cancelled["code"], "SANDBOX_CLEANUP_PENDING")
        finally:
            self.manager.release.set()
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_manager_close_deprovisions_only_exact_owned_identity_with_bounded_lease(self) -> None:
        manager = MxcWindowsSandboxManager(executor_directory=Path(self.temporary.name))
        manager._active = SimpleNamespace(sandbox_id="wsb:0123abcd")
        with patch.object(manager, "_deprovision_id") as deprovision:
            self.assertTrue(manager.close())
        deprovision.assert_called_once_with("wsb:0123abcd")
        self.assertIsNone(manager._active)
        self.assertTrue(manager.close())
        manager = MxcWindowsSandboxManager(executor_directory=Path(self.temporary.name))
        manager._lock = Mock()
        manager._lock.acquire.return_value = False
        with patch.object(manager, "_deprovision_id") as deprovision:
            self.assertFalse(manager.close())
        self.assertEqual(manager._lock.acquire.call_args.kwargs, {"timeout": 215})
        deprovision.assert_not_called()


if __name__ == "__main__":
    unittest.main()
