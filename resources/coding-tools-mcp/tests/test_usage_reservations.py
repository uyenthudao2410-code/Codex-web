from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from coding_tools_mcp.orchestration_ledger import OrchestrationLedger
from coding_tools_mcp.usage_reservations import UsageReservationError, UsageReservationStore


class _ClockMs:
    def __init__(self) -> None:
        self.value = 1_000_000

    def __call__(self) -> int:
        return self.value

    def advance(self, milliseconds: int) -> None:
        self.value += milliseconds


class UsageReservationStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.ledger = OrchestrationLedger(Path(self.temp.name))
        self.run_id = self.ledger.create_run(objective="reservation lifecycle")
        self.wave_id = self.ledger.create_wave(self.run_id, execution_mode="mcp_only")
        self.clock = _ClockMs()
        self.store = UsageReservationStore(self.ledger, clock_ms=self.clock)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def reserve(self, *, units: int = 120, reservation_id: str = "reservation-a") -> dict:
        return self.store.reserve(run_id=self.run_id, wave_id=self.wave_id, reservation_id=reservation_id, request_id="request-a", provider_model="opencode-go/deepseek-v4-flash", reserved_units=units, expires_at_unix_ms=self.clock() + 60_000)

    def test_lifecycle_is_durable_idempotent_and_preserves_unknown_not_zero(self) -> None:
        created = self.reserve()
        self.assertTrue(created["changed"])
        self.assertEqual(created["reservation"], {"unit": "tokens", "units": 120, "measurement": "estimated"})
        replay = UsageReservationStore(self.ledger, clock_ms=self.clock)
        duplicate = replay.reserve(run_id=self.run_id, wave_id=self.wave_id, reservation_id="reservation-a", request_id="request-a", provider_model="opencode-go/deepseek-v4-flash", reserved_units=120, expires_at_unix_ms=self.clock() + 90_000)
        self.assertFalse(duplicate["changed"])
        indeterminate = replay.mark_indeterminate(run_id=self.run_id, wave_id=self.wave_id, reservation_id="reservation-a", provider_model="opencode-go/deepseek-v4-flash")
        self.assertEqual(indeterminate["status"], "indeterminate")
        self.assertEqual(indeterminate["actual"], {"unit": "tokens", "units": None, "measurement": "unobserved"})
        exact = UsageReservationStore(self.ledger, clock_ms=self.clock).reconcile(run_id=self.run_id, wave_id=self.wave_id, reservation_id="reservation-a", provider_model="opencode-go/deepseek-v4-flash", actual_units=92, usage_id="usage-a")
        self.assertEqual(exact["status"], "reconciled")
        self.assertEqual(exact["actual"], {"unit": "tokens", "units": 92, "measurement": "measured"})
        self.assertEqual(exact["reservation"]["units"], 120)
        duplicate_exact = replay.reconcile(run_id=self.run_id, wave_id=self.wave_id, reservation_id="reservation-a", provider_model="opencode-go/deepseek-v4-flash", actual_units=92, usage_id="usage-a")
        self.assertFalse(duplicate_exact["changed"])
        event_types = [item["event_type"] for item in self.ledger.list_events(self.run_id)]
        self.assertEqual(event_types.count("usage_reservation_reserved"), 1)
        self.assertEqual(event_types.count("usage_reservation_indeterminate"), 1)
        self.assertEqual(event_types.count("usage_reservation_reconciled"), 1)
        raw = next(item for item in self.ledger.list_events(self.run_id) if item["event_type"] == "usage_reservation_reserved")
        self.assertEqual(raw["payload"]["reservation"], {"unit": "tokens", "units": 120, "measurement": "estimated"})

    def test_missing_conflicting_and_expired_authority_fail_closed_but_late_exact_can_reconcile(self) -> None:
        with self.assertRaisesRegex(UsageReservationError, "missing") as missing:
            self.store.require(run_id=self.run_id, wave_id=self.wave_id, reservation_id="missing", provider_model="opencode-go/deepseek-v4-flash")
        self.assertEqual(missing.exception.code, "USAGE_RESERVATION_MISSING")
        self.reserve(units=64)
        with self.assertRaises(UsageReservationError) as conflict:
            self.store.reserve(run_id=self.run_id, wave_id=self.wave_id, reservation_id="reservation-a", request_id="request-a", provider_model="opencode-go/deepseek-v4-flash", reserved_units=65, expires_at_unix_ms=self.clock() + 60_000)
        self.assertEqual(conflict.exception.code, "USAGE_RESERVATION_CONFLICT")
        self.clock.advance(60_001)
        with self.assertRaises(UsageReservationError) as stale:
            self.store.require(run_id=self.run_id, wave_id=self.wave_id, reservation_id="reservation-a", provider_model="opencode-go/deepseek-v4-flash")
        self.assertEqual(stale.exception.code, "USAGE_RESERVATION_STALE")
        indeterminate = self.store.mark_indeterminate(run_id=self.run_id, wave_id=self.wave_id, reservation_id="reservation-a", provider_model="opencode-go/deepseek-v4-flash")
        self.assertEqual(indeterminate["status"], "indeterminate")
        reconciled = self.store.reconcile(run_id=self.run_id, wave_id=self.wave_id, reservation_id="reservation-a", provider_model="opencode-go/deepseek-v4-flash", actual_units=17, usage_id="usage-late")
        self.assertEqual(reconciled["actual"]["units"], 17)

    def test_abort_is_terminal_and_cannot_be_used_for_dispatch(self) -> None:
        self.reserve()
        aborted = self.store.abort(run_id=self.run_id, wave_id=self.wave_id, reservation_id="reservation-a", provider_model="opencode-go/deepseek-v4-flash", reason="provider_start_failed")
        self.assertEqual(aborted["status"], "aborted")
        with self.assertRaises(UsageReservationError) as stale:
            self.store.require(run_id=self.run_id, wave_id=self.wave_id, reservation_id="reservation-a", provider_model="opencode-go/deepseek-v4-flash")
        self.assertEqual(stale.exception.code, "USAGE_RESERVATION_STALE")


if __name__ == "__main__":
    unittest.main()
