from __future__ import annotations

import unittest

from coding_tools_mcp.provider_traffic import ProviderTrafficGovernor


class _Clock:
    def __init__(self) -> None:
        self.value = 1000.0

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


class ProviderTrafficGovernorTests(unittest.TestCase):
    def test_unconfigured_limits_remain_unknown_and_do_not_block_manual_dispatch(self) -> None:
        governor = ProviderTrafficGovernor({})
        decision = governor.admit("provider/model", "request")
        self.assertTrue(decision["allowed"])
        self.assertEqual(decision["mode"], "observe_only")
        self.assertEqual(decision["reason"], "limits_unconfigured")
        self.assertEqual(decision["limits"], {"rpm": None, "tpm": None, "concurrency": None})
        self.assertEqual(decision["remaining"], {"rpm": None, "tpm": None, "concurrency": None})

    def test_concurrency_rpm_and_dedup_are_deterministic(self) -> None:
        clock = _Clock()
        governor = ProviderTrafficGovernor({"provider/model": {"rpm": 2, "concurrency": 1}}, clock=clock)
        first = governor.admit("provider/model", "request-1")
        self.assertTrue(first["allowed"])
        duplicate = governor.admit("provider/model", "request-1")
        self.assertTrue(duplicate["allowed"])
        self.assertTrue(duplicate["deduplicated"])
        self.assertEqual(duplicate["usage"]["requests_last_minute"], 1)
        blocked = governor.admit("provider/model", "request-2")
        self.assertFalse(blocked["allowed"])
        self.assertEqual(blocked["reason"], "concurrency_exhausted")
        self.assertTrue(governor.complete("request-1"))
        second = governor.admit("provider/model", "request-2")
        self.assertTrue(second["allowed"])
        governor.complete("request-2")
        rate_limited = governor.admit("provider/model", "request-3")
        self.assertFalse(rate_limited["allowed"])
        self.assertEqual(rate_limited["reason"], "rpm_exhausted")
        self.assertGreater(rate_limited["retry_after_ms"], 0)
        clock.advance(61)
        after_window = governor.admit("provider/model", "request-3")
        self.assertTrue(after_window["allowed"])

    def test_tpm_requires_explicit_request_budget_and_never_invents_usage(self) -> None:
        clock = _Clock()
        governor = ProviderTrafficGovernor({"provider/model": {"tpm": 100}}, clock=clock)
        missing = governor.admit("provider/model", "request-1")
        self.assertFalse(missing["allowed"])
        self.assertEqual(missing["reason"], "token_budget_required")
        first = governor.admit("provider/model", "request-1", token_budget=70)
        self.assertTrue(first["allowed"])
        governor.complete("request-1")
        blocked = governor.admit("provider/model", "request-2", token_budget=40)
        self.assertFalse(blocked["allowed"])
        self.assertEqual(blocked["reason"], "tpm_exhausted")
        self.assertEqual(blocked["usage"]["reserved_tokens_last_minute"], 70)
        exact = governor.admit("provider/model", "request-2", token_budget=30)
        self.assertTrue(exact["allowed"])
        self.assertEqual(exact["usage"]["reserved_tokens_last_minute"], 100)

    def test_invalid_explicit_configuration_fails_closed(self) -> None:
        governor = ProviderTrafficGovernor({"provider/model": {"rpm": 0}})
        decision = governor.admit("provider/model", "request")
        self.assertFalse(decision["allowed"])
        self.assertEqual(decision["mode"], "invalid")
        self.assertEqual(decision["reason"], "invalid_configuration")
        snapshot = governor.snapshot(models=["provider/model"])
        self.assertEqual(snapshot["configuration"]["status"], "invalid")
        self.assertEqual(snapshot["configuration"]["invalid_models"], ["provider/model"])

    def test_snapshot_retry_after_is_only_an_actual_denial_signal(self) -> None:
        governor = ProviderTrafficGovernor({"provider/model": {"rpm": 2}})
        self.assertTrue(governor.admit("provider/model", "request-1")["allowed"])
        snapshot = governor.snapshot(models=["provider/model"])
        self.assertIsNone(snapshot["providers"][0]["retry_after_ms"])

    def test_global_configuration_error_marks_all_requested_provider_rows_invalid(self) -> None:
        governor = ProviderTrafficGovernor({}, configuration_error="invalid json")
        snapshot = governor.snapshot(models=["provider/model"])
        provider = snapshot["providers"][0]
        self.assertEqual(snapshot["configuration"]["status"], "invalid")
        self.assertFalse(provider["allowed"])
        self.assertEqual(provider["mode"], "invalid")
        self.assertEqual(provider["reason"], "invalid_configuration")
        self.assertEqual(provider["configuration_error"], "invalid json")


if __name__ == "__main__":
    unittest.main()
