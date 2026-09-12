from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from scripts import report_lifecycle_census as cli  # noqa: E402


SUMMARY_FIELDS = (
    "summary",
    "projection",
    "snapshot",
    "read_contract",
    "content_free",
    "mutated_canonical_ledger",
    "observed_at_unix_seconds",
    "schema_version",
)


def _report_fixture() -> dict[str, object]:
    return {
        "summary": {"blocker": False, "nullable": None, "status": "unknown"},
        "projection": {"classification": "PROJECTION_DRIFT", "projection_drift": False},
        "snapshot": {"immutable": True},
        "read_contract": {"canonical_writer_instantiated": False},
        "content_free": False,
        "mutated_canonical_ledger": False,
        "observed_at_unix_seconds": None,
        "schema_version": 2,
        "runs": [{"run_id": "run-1", "classification": "AWAITING_ACCEPTANCE"}],
        "extra": {"preserved_by_default": "yes"},
    }


class LifecycleCensusCliTests(unittest.TestCase):
    def _invoke(self, argv: list[str], payload: dict[str, object]) -> tuple[int, dict[str, object], object]:
        stdout = io.StringIO()
        with patch.object(cli, "report", return_value=payload) as reporter, redirect_stdout(stdout):
            code = cli.main(argv)
        return code, json.loads(stdout.getvalue()), reporter

    def test_default_retains_complete_report_and_reads_once(self) -> None:
        payload = _report_fixture()
        with tempfile.TemporaryDirectory() as temp:
            code, output, reporter = self._invoke(
                ["--workspace", temp, "--observed-at", "2026-09-09T00:00:00Z"],
                payload,
            )
        self.assertEqual(code, 0)
        self.assertEqual(output, payload)
        self.assertIn("runs", output)
        reporter.assert_called_once()

    def test_summary_selects_only_bounded_fields_and_preserves_values(self) -> None:
        payload = _report_fixture()
        payload.pop("snapshot")
        with tempfile.TemporaryDirectory() as temp:
            code, output, reporter = self._invoke(
                ["--workspace", temp, "--observed-at", "2026-09-09T00:00:00Z", "--summary"],
                payload,
            )
        expected = {field: payload[field] for field in SUMMARY_FIELDS if field in payload}
        self.assertEqual(code, 0)
        self.assertEqual(output, expected)
        self.assertNotIn("runs", output)
        self.assertNotIn("snapshot", output)
        self.assertIs(output["summary"]["blocker"], False)
        self.assertIsNone(output["summary"]["nullable"])
        self.assertEqual(output["summary"]["status"], "unknown")
        self.assertIs(output["content_free"], False)
        self.assertIs(output["mutated_canonical_ledger"], False)
        self.assertIsNone(output["observed_at_unix_seconds"])
        reporter.assert_called_once()

    def test_report_errors_still_return_exit_two_and_read_once(self) -> None:
        stdout = io.StringIO()
        with tempfile.TemporaryDirectory() as temp, patch.object(
            cli,
            "report",
            side_effect=RuntimeError("synthetic failure"),
        ) as reporter, redirect_stdout(stdout):
            code = cli.main(["--workspace", temp, "--observed-at", "2026-09-09T00:00:00Z", "--summary"])
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(stdout.getvalue()), {"ok": False, "error": "RuntimeError"})
        reporter.assert_called_once()

    def test_argument_errors_still_exit_two_without_reading_report(self) -> None:
        stderr = io.StringIO()
        with patch.object(cli, "report") as reporter, redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as raised:
                cli.main(["--not-a-real-option"])
        self.assertEqual(raised.exception.code, 2)
        reporter.assert_not_called()


if __name__ == "__main__":
    unittest.main()
