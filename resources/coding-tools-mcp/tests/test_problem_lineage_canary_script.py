from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from coding_tools_mcp.orchestration_ledger import OrchestrationLedger


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "report_problem_lineage_canary.py"
SPEC = importlib.util.spec_from_file_location("report_problem_lineage_canary", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
REPORTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REPORTER)


class ProblemLineageCanaryScriptTests(unittest.TestCase):
    def test_reporter_pins_identity_of_its_backup_api_copy_without_mutating_live_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            OrchestrationLedger(root)
            ledger_path = root / ".coding-tools" / "orchestration" / "ledger.sqlite3"
            before = hashlib.sha256(ledger_path.read_bytes()).hexdigest()
            stream = io.StringIO()
            with patch.object(REPORTER, "_git", side_effect=["a" * 40, ""]), contextlib.redirect_stdout(stream):
                self.assertEqual(REPORTER.main(["--workspace", str(root)]), 0)
            after = hashlib.sha256(ledger_path.read_bytes()).hexdigest()
            result = json.loads(stream.getvalue())["result"]
            snapshot = result["snapshot"]
            self.assertEqual(before, after)
            self.assertTrue(snapshot["immutable_backup_api_copy"])
            self.assertTrue(snapshot["immutable"])
            self.assertTrue(snapshot["query_only"])
            self.assertEqual(snapshot["live_backup_connections"], 1)
            self.assertGreater(snapshot["size_bytes"], 0)
            self.assertRegex(snapshot["sha256"], r"^[0-9a-f]{64}$")
            self.assertRegex(snapshot["logical_sha256"], r"^[0-9a-f]{64}$")
            self.assertRegex(snapshot["snapshot_at"], r"Z$")

    def test_git_probe_failure_is_not_coerced_to_a_clean_source(self) -> None:
        with patch.object(subprocess, "run", return_value=subprocess.CompletedProcess(["git"], 1, stdout="", stderr="")):
            with self.assertRaises(RuntimeError):
                REPORTER._git(Path.cwd(), "rev-parse", "HEAD")


if __name__ == "__main__":
    unittest.main()
