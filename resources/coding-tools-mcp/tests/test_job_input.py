"""W5 — WebCodex job-input contract port: caller input_id + typed receipt."""

from __future__ import annotations

import threading
import unittest

from coding_tools_mcp.errors import ToolFailure
from coding_tools_mcp.job_input import (
    OUTCOME_DELIVERED,
    OUTCOME_REJECTED,
    OUTCOME_UNKNOWN,
    JobInputLedger,
)
from coding_tools_mcp.session_control import SessionControlMixin


class JobInputLedgerTests(unittest.TestCase):
    def test_delivered_receipt_records_hash_and_bytes(self) -> None:
        ledger = JobInputLedger()
        written: list[bytes] = []
        receipt = ledger.submit("sess-1", "in-1", b"hello\n", written.append)
        self.assertEqual(receipt["outcome"], OUTCOME_DELIVERED)
        self.assertEqual(receipt["bytes"], 6)
        self.assertEqual(len(receipt["sha256"]), 64)
        self.assertFalse(receipt["duplicate"])
        self.assertEqual(written, [b"hello\n"])

    def test_duplicate_input_id_never_writes_twice(self) -> None:
        ledger = JobInputLedger()
        written: list[bytes] = []
        first = ledger.submit("sess-1", "in-1", b"data", written.append)
        second = ledger.submit("sess-1", "in-1", b"data", written.append)
        self.assertEqual(first["outcome"], OUTCOME_DELIVERED)
        self.assertTrue(second["duplicate"])
        self.assertEqual(second["outcome"], OUTCOME_DELIVERED)
        self.assertEqual(len(written), 1, "a retry must reconcile, not resend")

    def test_failed_write_is_unknown_and_retry_still_does_not_resend(self) -> None:
        ledger = JobInputLedger()
        attempts: list[bytes] = []

        def flaky(data: bytes) -> None:
            attempts.append(data)
            raise BrokenPipeError("pipe gone")

        first = ledger.submit("sess-1", "in-9", b"x", flaky)
        self.assertEqual(first["outcome"], OUTCOME_UNKNOWN)
        second = ledger.submit("sess-1", "in-9", b"x", flaky)
        self.assertEqual(second["outcome"], OUTCOME_UNKNOWN)
        self.assertTrue(second["duplicate"])
        self.assertEqual(len(attempts), 1, "unknown outcome must never auto-replay")

    def test_same_input_id_on_another_session_is_independent(self) -> None:
        ledger = JobInputLedger()
        written: list[bytes] = []
        ledger.submit("sess-1", "in-1", b"a", written.append)
        other = ledger.submit("sess-2", "in-1", b"a", written.append)
        self.assertFalse(other["duplicate"])
        self.assertEqual(len(written), 2)

    def test_record_rejected_is_definite_and_deduped(self) -> None:
        ledger = JobInputLedger()
        first = ledger.record_rejected("sess-1", "in-2", b"nope", "COMMAND_CLOSED")
        second = ledger.record_rejected("sess-1", "in-2", b"nope", "COMMAND_CLOSED")
        self.assertEqual(first["outcome"], OUTCOME_REJECTED)
        self.assertTrue(second["duplicate"])
        self.assertEqual(ledger.receipt_for("sess-1", "in-2")["outcome"], OUTCOME_REJECTED)
        self.assertIsNone(ledger.receipt_for("sess-1", "missing"))

    def test_invalid_input_id_rejected(self) -> None:
        ledger = JobInputLedger()
        with self.assertRaises(ValueError):
            ledger.submit("sess-1", "", b"x", lambda data: None)
        with self.assertRaises(ValueError):
            ledger.submit("sess-1", "x" * 129, b"x", lambda data: None)


class _FakeProcess:
    def __init__(self, exited: bool = False) -> None:
        self._exited = exited

    def poll(self):
        return 0 if self._exited else None


class _FakeSession:
    def __init__(self, exited: bool = False, fail_write: bool = False) -> None:
        self.process = _FakeProcess(exited)
        self.fail_write = fail_write
        self.writes: list[bytes] = []
        self.lock = threading.Lock()
        self.stdout_total_bytes = 0
        self.stdout_cursor = 0
        self.stderr_total_bytes = 0
        self.stderr_cursor = 0

    def refresh_status(self) -> None:
        pass

    def write_input(self, data: bytes) -> None:
        if self.fail_write:
            raise BrokenPipeError("gone")
        self.writes.append(data)

    def snapshot_since_cursor(self, _limit: int, consumer_id: str = "") -> dict:
        return {"status": "running", "stdout": "", "stderr": ""}


class _Harness(SessionControlMixin):
    def __init__(self, session: _FakeSession) -> None:
        self._session = session
        self.task_state = type("TS", (), {"get": staticmethod(lambda: {})})()

    def _command_handle(self, args):  # noqa: ANN001, ANN202
        return str(args.get("session_id") or args.get("command_id"))

    def _get_session(self, _session_id):  # noqa: ANN001, ANN202
        return self._session

    def _format_session_output(self, session, payload, args):  # noqa: ANN001, ANN202
        return dict(payload)


class WriteStdinReceiptTests(unittest.TestCase):
    def _args(self, **overrides):
        args = {"session_id": "sess-1", "chars": "ls\n", "yield_time_ms": 20, "input_id": "in-1"}
        args.update(overrides)
        return args

    def test_write_with_input_id_returns_receipt_and_writes_once(self) -> None:
        session = _FakeSession()
        harness = _Harness(session)
        payload = harness.write_stdin(self._args())
        self.assertEqual(payload["input_receipt"]["outcome"], OUTCOME_DELIVERED)
        self.assertEqual(session.writes, [b"ls\n"])
        again = harness.write_stdin(self._args())
        self.assertTrue(again["input_receipt"]["duplicate"])
        self.assertEqual(len(session.writes), 1, "duplicate input_id must not write again")

    def test_write_without_input_id_keeps_legacy_behavior(self) -> None:
        session = _FakeSession()
        harness = _Harness(session)
        payload = harness.write_stdin(self._args(input_id=""))
        self.assertNotIn("input_receipt", payload)
        self.assertEqual(session.writes, [b"ls\n"])

    def test_failed_write_raises_unknown_with_receipt(self) -> None:
        session = _FakeSession(fail_write=True)
        harness = _Harness(session)
        with self.assertRaises(ToolFailure) as ctx:
            harness.write_stdin(self._args())
        self.assertEqual(ctx.exception.code, "JOB_INPUT_OUTCOME_UNKNOWN")
        receipt = harness.job_input_receipt("sess-1", "in-1")
        self.assertEqual(receipt["outcome"], OUTCOME_UNKNOWN)

    def test_closed_command_records_rejected_receipt(self) -> None:
        session = _FakeSession(exited=True)
        harness = _Harness(session)
        with self.assertRaises(ToolFailure) as ctx:
            harness.write_stdin(self._args())
        self.assertEqual(ctx.exception.code, "COMMAND_CLOSED")
        receipt = harness.job_input_receipt("sess-1", "in-1")
        self.assertEqual(receipt["outcome"], OUTCOME_REJECTED)


if __name__ == "__main__":
    unittest.main()
