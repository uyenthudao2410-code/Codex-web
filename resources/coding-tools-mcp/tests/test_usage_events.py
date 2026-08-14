from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from coding_tools_mcp.orchestration_ledger import OrchestrationLedger
from coding_tools_mcp.usage_events import build_usage_event, usage_event_from_provider_telemetry


class UsageEventTests(unittest.TestCase):
    def test_provider_telemetry_preserves_measured_usage_and_unknown_timing(self) -> None:
        event = usage_event_from_provider_telemetry(
            run_id="run-1",
            wave_id="wave-1",
            delegation_id="delegation-1",
            telemetry={
                "provider_id": "opencode-go",
                "model_id": "deepseek-v4-flash",
                "status": "completed",
                "input_tokens": 100,
                "output_tokens": 20,
                "reasoning_output_tokens": 4,
                "cache_read_tokens": 40,
                "cache_write_tokens": 2,
                "provider_cost": 0.004,
                "duration_ms": 600,
            },
        )
        self.assertEqual(event["usage"]["cached_input_tokens"], 40)
        self.assertEqual(event["usage"]["uncached_input_tokens"], 60)
        self.assertEqual(event["cost"]["provider_cost"], 0.004)
        self.assertIsNone(event["timing"]["queue_ms"])
        self.assertEqual(event["timing"]["provider_ms"], 600)
        self.assertIsNone(event["timing"]["total_ms"])
        self.assertEqual(event["measurement"]["queue_timing"], "unobserved")

    def test_failed_usage_records_typed_error_only(self) -> None:
        raw = "RateLimitError-super-secret-message"
        event = build_usage_event(
            run_id="run-2",
            wave_id="wave-2",
            delegation_id="delegation-2",
            provider_id="opencode-go",
            model_id="deepseek-v4-pro",
            status="failed",
            source="test",
            error_name=raw,
        )
        self.assertEqual(event["error"]["class"], "capacity_or_rate_limit")
        self.assertNotIn(raw, repr(event))

    def test_ledger_usage_projection_is_sanitized_and_ordered(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(objective="measure")
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
            usage = build_usage_event(
                run_id=run_id,
                wave_id=wave_id,
                delegation_id="delegation-3",
                provider_id="opencode-go",
                model_id="deepseek-v4-flash",
                status="completed",
                source="test",
                input_tokens=12,
                cached_input_tokens=2,
                provider_cost=0.001,
            )
            first = ledger.record_usage_event(run_id=run_id, wave_id=wave_id, delegation_id="delegation-3", usage_event=usage)
            duplicate = ledger.record_usage_event(run_id=run_id, wave_id=wave_id, delegation_id="delegation-3", usage_event=usage)
            self.assertTrue(first["recorded"])
            self.assertFalse(duplicate["recorded"])
            projected = ledger.list_usage_events(run_id)
            self.assertEqual(len(projected), 1)
            self.assertEqual(projected[0]["usage_id"], usage["usage_id"])
            self.assertEqual(projected[0]["usage"]["input_tokens"], 12)


if __name__ == "__main__":
    unittest.main()
