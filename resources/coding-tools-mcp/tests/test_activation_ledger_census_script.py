from __future__ import annotations

import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest import mock

from coding_tools_mcp import activation_ledger_census
from coding_tools_mcp.ledger_file_gate import LedgerGateTimeout, ledger_access_gate
from coding_tools_mcp.orchestration_ledger import OrchestrationLedger


class ActivationLedgerCensusModuleTests(unittest.TestCase):
    def test_cli_maps_ledger_gate_timeout_to_typed_sanitized_cause(self) -> None:
        stderr = io.StringIO()
        with (
            mock.patch.object(
                activation_ledger_census,
                "main",
                side_effect=LedgerGateTimeout("secret-ledger-path-must-not-leak"),
            ),
            redirect_stderr(stderr),
        ):
            self.assertEqual(activation_ledger_census._run_cli(), 75)
        self.assertEqual(stderr.getvalue().strip(), "ACTIVATION_LEDGER_CENSUS_LOCK_TIMEOUT")
        self.assertNotIn("secret-ledger-path", stderr.getvalue())

    def test_held_census_blocks_supported_writers_until_epoch_commit_release(self) -> None:
        package_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary).resolve()
            ledger = OrchestrationLedger(workspace).path
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-u",
                    "-m",
                    "coding_tools_mcp.activation_ledger_census",
                    "--workspace",
                    str(workspace),
                    "--hold-exclusive",
                ],
                cwd=package_root,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
            )
            try:
                assert process.stdout is not None
                receipt = json.loads(process.stdout.readline())
                self.assertTrue(receipt["exclusive_gate_held"])
                self.assertTrue(receipt["snapshot"]["backup_api_copy"])
                self.assertTrue(receipt["snapshot"]["immutable"])
                self.assertTrue(receipt["snapshot"]["query_only"])
                self.assertEqual(receipt["snapshot"]["integrity_check"], ["ok"])
                self.assertEqual(receipt["snapshot"]["foreign_key_check_rows"], 0)
                with self.assertRaises(LedgerGateTimeout):
                    with ledger_access_gate(ledger, timeout_seconds=0.05):
                        pass
                assert process.stdin is not None
                process.stdin.write("release\n")
                process.stdin.flush()
                self.assertEqual(process.wait(timeout=5), 0)
                with ledger_access_gate(ledger, timeout_seconds=0.5):
                    pass
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait(timeout=5)


if __name__ == "__main__":
    unittest.main()
