"""Terminal connected action failures expose safe, truthful status metadata."""

from __future__ import annotations

import json
import unittest

from control_plane.mcp_status import terminal_failure


class McpTerminalStatusTests(unittest.TestCase):
    @staticmethod
    def _receipt(state: str, payload: object) -> dict[str, object]:
        return {"receipt_state": state, "payload_json": json.dumps(payload)}

    def _action(self, state: str, payload: object, **extra: object) -> dict[str, object]:
        return {"delivery_state": "settled", "receipts": [self._receipt(state, payload)], **extra}

    def test_rejected_exposes_exact_safe_code_without_raw_payload(self) -> None:
        action = self._action("rejected", {
            "code": "CONTROL_PLANE_FILE_READ_POLICY_EXPIRED",
            "message": "private operator token: do-not-disclose",
            "path": "C:/private/credentials.json",
            "retryable": True,
            "next_action": "run an arbitrary command",
        })
        self.assertEqual(terminal_failure(action), {
            "code": "CONTROL_PLANE_FILE_READ_POLICY_EXPIRED",
            "category": "local_admission", "retryable": False, "next_action": "inspect_action",
        })

    def test_failed_and_stopped_are_execution_failures_without_effect_claims(self) -> None:
        for state, code in (("failed", "LOCAL_ACTION_FAILED"), ("stopped", "LOCAL_ACTION_STOPPED")):
            with self.subTest(state=state):
                self.assertEqual(terminal_failure(self._action(state, {})), {
                    "code": code, "category": "execution", "retryable": False,
                    "next_action": "do_not_replay_automatically",
                })

    def test_malformed_or_sensitive_codes_use_generic_fallback(self) -> None:
        codes = [None, True, 3, {}, "", "AB", "lowercase_code", "Bearer secret",
                 "C:/private/token", "SECRET\nPRIVATE", "SECRET\x00PRIVATE", "A" * 97]
        for code in codes:
            with self.subTest(code=code):
                failure = terminal_failure(self._action("rejected", {
                    "code": code, "diagnostic_code": code, "message": "sensitive-message",
                }))
                self.assertEqual(failure, {
                    "code": "LOCAL_ACTION_REJECTED", "category": "local_admission",
                    "retryable": False, "next_action": "inspect_action",
                })

    def test_code_shape_accepts_exact_minimum_and_maximum_length(self) -> None:
        for code in ("ABC", "A" * 96):
            with self.subTest(length=len(code)):
                self.assertEqual(terminal_failure(self._action("failed", {"code": code}))["code"], code)

    def test_diagnostic_is_optional_distinct_and_sanitized(self) -> None:
        self.assertEqual(terminal_failure(self._action("failed", {
            "code": "LOCAL_ACTION_FAILED", "diagnostic_code": "PROCESS_EXIT_UNCONFIRMED",
        }))["diagnostic_code"], "PROCESS_EXIT_UNCONFIRMED")
        for diagnostic in ("LOCAL_ACTION_FAILED", "private token", "a" * 64, {"token": "secret"}):
            with self.subTest(diagnostic=diagnostic):
                self.assertNotIn("diagnostic_code", terminal_failure(self._action("failed", {
                    "code": "LOCAL_ACTION_FAILED", "diagnostic_code": diagnostic,
                })))

    def test_unknown_is_never_inferred_as_terminal_failure(self) -> None:
        for delivery in ("reconcile_required", "settled"):
            with self.subTest(delivery=delivery):
                self.assertIsNone(terminal_failure(self._action("unknown", {
                    "code": "LOCAL_ACTION_FAILED", "diagnostic_code": "PATCH_REJECTED",
                }, delivery_state=delivery)))
        for delivery in ("queued", "accepted", "dispatch_unconfirmed", "reconcile_required"):
            with self.subTest(delivery=delivery):
                self.assertIsNone(terminal_failure(self._action("failed", {}, delivery_state=delivery)))

    def test_latest_receipt_overrides_earlier_unknown_or_failure(self) -> None:
        history = [self._receipt("unknown", {"code": "EFFECT_UNKNOWN"}),
                   self._receipt("rejected", {"code": "EXACT_TARGET_REJECTED"})]
        action = {"delivery_state": "settled", "receipts": history}
        self.assertEqual(terminal_failure(action)["code"], "EXACT_TARGET_REJECTED")
        self.assertEqual(len(history), 2)
        action["receipts"] = [*history, self._receipt("completed", {})]
        self.assertIsNone(terminal_failure(action))
        action["receipts"] = [*history, self._receipt("stopped", {})]
        self.assertEqual(terminal_failure(action)["code"], "LOCAL_ACTION_STOPPED")
        action["receipts"] = [*history, None]
        self.assertIsNone(terminal_failure(action))

    def test_missing_or_invalid_payload_is_safe_generic_status(self) -> None:
        for raw in (None, {}, "not-json", "[]", "null", '"private-value"',
                    '{"code": "VALID_CODE", "extra": "' + "s" * (64 * 1024) + '"}',
                    "[" * 2000 + "]" * 2000):
            with self.subTest(payload_type=type(raw).__name__):
                self.assertEqual(terminal_failure({
                    "delivery_state": "settled", "receipts": [{"receipt_state": "rejected", "payload_json": raw}],
                }), {
                    "code": "LOCAL_ACTION_REJECTED", "category": "local_admission",
                    "retryable": False, "next_action": "inspect_action",
                })

    def test_missing_or_invalid_receipts_do_not_fabricate_failure(self) -> None:
        for receipts in (None, {}, [], [None], [{"receipt_state": []}], [{"receipt_state": "accepted"}]):
            with self.subTest(receipts=receipts):
                self.assertIsNone(terminal_failure({"delivery_state": "settled", "receipts": receipts}))


if __name__ == "__main__":
    unittest.main()
