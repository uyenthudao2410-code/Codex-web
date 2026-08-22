from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from coding_tools_mcp.ledger_access import open_existing_ledger
from coding_tools_mcp.orchestration_ledger import OrchestrationLedger


class LedgerAccessTests(unittest.TestCase):
    def test_open_existing_rejects_missing_ledger_without_creating_project_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertRaises(FileNotFoundError):
                open_existing_ledger(root)
            self.assertFalse((root / ".coding-tools").exists())

    def test_open_existing_reuses_a_legitimately_created_workspace_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            created = OrchestrationLedger(root)
            reopened = open_existing_ledger(root)
            self.assertEqual(reopened.path, created.path)


if __name__ == "__main__":
    unittest.main()
