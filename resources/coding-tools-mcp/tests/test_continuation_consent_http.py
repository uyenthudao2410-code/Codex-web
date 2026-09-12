from __future__ import annotations

import json
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from coding_tools_mcp.continuation_consent_http import (
    CONTINUATION_CONSENT_CHALLENGE_TTL_MS,
    CONTINUATION_CONSENT_HTTP_PATH,
    ContinuationConsentChallengeStore,
)
from coding_tools_mcp.continuation_contract import continuation_consent_descriptor
from coding_tools_mcp.mcp_http_handler import MCPHandler, RuntimeHTTPServer
from coding_tools_mcp.run_continuation import RunContinuationMixin
from coding_tools_mcp.server import Runtime


def policy(*, run_id: str = "run-test", wave_id: str = "wave-test") -> dict[str, object]:
    return {
        "schema_version": 1,
        "run_id": run_id,
        "grant_wave_id": wave_id,
        "workspace_id": "workspace-test",
        "problem_id": "problem-test",
        "problem_revision": 1,
        "contract_fingerprint": "a" * 64,
        "tool_contract_sha256": "b" * 64,
        "runtime_behavior_fingerprint": "c" * 64,
        "activation_epoch_id": "epoch-test",
        "activation_admission": "open",
        "issuer_client_id": "chatweb:test",
        "read_paths": ["read.txt"],
        "write_paths": ["write.txt"],
        "protected_paths": ["protected.txt"],
        "approved_checks": [{"definition_hash": "d" * 64}],
        "max_duration_seconds": 600,
        "max_decision_turns": 8,
        "max_patch_attempts": 2,
    }


def issue(store: ContinuationConsentChallengeStore, *, now_ms: int = 1_000_000) -> dict[str, object]:
    current_policy = policy()
    return store.issue(
        descriptor=continuation_consent_descriptor(current_policy),
        policy=current_policy,
        controller={"owner_client_id": "chatweb:test", "lease_id": "client:chatweb:test", "fencing_token": 4},
        host_turn={"turn_id": "chatweb-trace:trace-test", "trace_id": "trace-test"},
        now_ms=now_ms,
    )


class ContinuationConsentChallengeStoreTests(unittest.TestCase):
    def test_exact_challenge_is_previewable_process_owned_and_one_shot(self) -> None:
        store = ContinuationConsentChallengeStore()
        issued = issue(store)
        token = str(issued["token"])
        preview = store.preview(token, now_ms=1_000_100)
        self.assertIsNotNone(preview)
        assert preview is not None
        self.assertEqual(preview["descriptor"], continuation_consent_descriptor(policy()))
        approved = store.begin_approval(token, now_ms=1_000_200)
        self.assertIsNotNone(approved)
        assert approved is not None
        self.assertIsNone(store.begin_approval(token, now_ms=1_000_201))
        store.consume(approved)
        self.assertIsNone(store.preview(token, now_ms=1_000_202))

    def test_failed_finalization_can_retry_but_expiry_cannot(self) -> None:
        store = ContinuationConsentChallengeStore()
        issued = issue(store)
        token = str(issued["token"])
        approved = store.begin_approval(token, now_ms=1_000_100)
        assert approved is not None
        store.release(approved)
        self.assertIsNotNone(store.begin_approval(token, now_ms=1_000_101))
        self.assertIsNone(
            store.preview(token, now_ms=1_000_000 + CONTINUATION_CONSENT_CHALLENGE_TTL_MS + 1)
        )


class ContinuationConsentHTTPTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.runtime = Runtime(Path(self.directory.name))
        self.runtime._run_continuation_approve_http_challenge = Mock(
            return_value={"run_id": "run-test", "status": "PROPOSING", "grant_status": "GRANTED"}
        )
        self.server = RuntimeHTTPServer(("127.0.0.1", 0), MCPHandler, self.runtime, runtime_factory=None)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.directory.cleanup()

    def _post(self, payload: dict[str, object], *, headers: dict[str, str] | None = None) -> tuple[int, dict[str, object]]:
        request = urllib.request.Request(
            self.base + CONTINUATION_CONSENT_HTTP_PATH,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", **(headers or {})},
            method="POST",
        )
        try:
            response = urllib.request.urlopen(request, timeout=5)
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read().decode("utf-8"))
        with response:
            return response.status, json.loads(response.read().decode("utf-8"))

    def test_fragment_token_preview_and_click_start_without_second_chat_turn(self) -> None:
        issued = issue(self.runtime.run_continuation_consent_challenges, now_ms=int(time.time() * 1000))
        token = str(issued["token"])
        with urllib.request.urlopen(self.base + CONTINUATION_CONSENT_HTTP_PATH + "#" + token, timeout=5) as response:
            page = response.read().decode("utf-8")
            self.assertEqual(response.headers.get("Referrer-Policy"), "no-referrer")
            self.assertIn("connect-src 'self'", response.headers.get("Content-Security-Policy") or "")
            self.assertIn("Authorize and start", page)
            self.assertNotIn(token, page)
        preview_status, preview = self._post({"action": "preview", "token": token})
        self.assertEqual(preview_status, 200)
        self.assertEqual(preview["descriptor"], continuation_consent_descriptor(policy()))
        approve_status, approved = self._post({"action": "approve", "token": token})
        self.assertEqual(approve_status, 200)
        self.assertEqual(approved["status"], "PROPOSING")
        self.runtime._run_continuation_approve_http_challenge.assert_called_once()
        replay_status, replay = self._post({"action": "approve", "token": token})
        self.assertEqual(replay_status, 409)
        self.assertEqual(replay["code"], "CHALLENGE_MISSING_EXPIRED_OR_CONSUMED")

    def test_forwarded_tunnel_shape_is_denied_even_from_loopback_peer(self) -> None:
        status, body = self._post(
            {"action": "preview", "token": "not-a-token"},
            headers={"X-Forwarded-For": "203.0.113.10"},
        )
        self.assertEqual(status, 403)
        self.assertEqual(body["code"], "LOCAL_APPROVAL_REQUIRED")


class ContinuationConsentFinalizationTests(unittest.TestCase):
    def test_exact_click_issues_and_starts_while_controller_transfer_is_denied(self) -> None:
        current_policy = policy()
        descriptor = continuation_consent_descriptor(current_policy)
        receipt = {
            "receipt_id": "chatweb-continuation-consent-web:test",
            "turn_id": "chatweb-trace:trace-test",
            "trace_id": "trace-test",
            "descriptor": descriptor,
        }
        controller = {"owner_client_id": "chatweb:test", "lease_id": "client:chatweb:test", "fencing_token": 4}
        ledger = Mock()
        ledger.peek_controller_lease.return_value = {**controller, "status": "active"}
        ledger.issue_run_continuation.return_value = {"status": "GRANTED"}
        runtime = SimpleNamespace(
            tool_contract={"sha256": "b" * 64},
            orchestration_ledger=ledger,
            orchestration_control=Mock(snapshot=Mock(return_value=SimpleNamespace(wave_id="wave-test"))),
            _run_continuation_assert_runtime=Mock(),
            _project_orchestration=Mock(),
            _run_continuation_start_driver=Mock(return_value={"run_id": "run-test", "status": "PROPOSING"}),
            _run_continuation_tool_failure=RunContinuationMixin._run_continuation_tool_failure,
        )
        approved = {"challenge_id": "challenge-test", "policy": current_policy, "controller": controller, "receipt": receipt}
        result = RunContinuationMixin._run_continuation_approve_http_challenge(runtime, approved)
        self.assertEqual(result["status"], "PROPOSING")
        ledger.issue_run_continuation.assert_called_once()
        runtime._run_continuation_start_driver.assert_called_once_with({"run_id": "run-test"})

        ledger.peek_controller_lease.return_value = {
            "owner_client_id": "chatweb:other",
            "lease_id": "client:chatweb:other",
            "fencing_token": 5,
            "status": "active",
        }
        with self.assertRaisesRegex(Exception, "Controller authority changed"):
            RunContinuationMixin._run_continuation_approve_http_challenge(runtime, approved)


if __name__ == "__main__":
    unittest.main()
