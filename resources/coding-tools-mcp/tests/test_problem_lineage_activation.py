from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path

from coding_tools_mcp.orchestration_ledger import OrchestrationLedger
from coding_tools_mcp.problem_lineage import PROBLEM_SCHEMA_VERSION
from coding_tools_mcp.problem_lineage_activation import (
    ProblemLineageActivationError,
    activate_problem_lineage_schema,
    preflight_problem_lineage_activation,
)


class ProblemLineageActivationTests(unittest.TestCase):
    def test_preflight_and_guarded_forward_migration_preserve_event_chains(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            run_id = ledger.create_run(objective="fixture")
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
            ledger.finish_wave(wave_id, status="accepted")
            ledger.finish_run(run_id, status="accepted")
            before = preflight_problem_lineage_activation(root, observed_at=time.time())
            self.assertEqual(before["schema"]["user_version"], 9)
            self.assertEqual(before["schema"]["problem_tables"], [])
            self.assertEqual(before["event_chain"]["invalid_run_ids"], [])
            receipt = activate_problem_lineage_schema(
                root,
                observed_at=time.time(),
                expected_snapshot_sha256=str(before["snapshot"]["sha256"]),
                expected_logical_sha256=str(before["snapshot"]["logical_sha256"]),
                runtime_stopped=True,
            )
            self.assertTrue(receipt.migration["migrated"])
            self.assertEqual(receipt.migration["schema_version"], PROBLEM_SCHEMA_VERSION)
            self.assertEqual(receipt.postflight["schema"]["user_version"], PROBLEM_SCHEMA_VERSION)
            self.assertEqual(set(receipt.postflight["schema"]["problem_tables"]), {"problem_threads", "problem_events"})
            self.assertEqual(receipt.preflight["event_chain"], receipt.postflight["event_chain"])
            self.assertTrue(OrchestrationLedger(root).verify_chain(run_id)["ok"])

    def test_migration_requires_stopped_runtime_and_exact_snapshot_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            OrchestrationLedger(root)
            before = preflight_problem_lineage_activation(root, observed_at=time.time())
            with self.assertRaises(ProblemLineageActivationError):
                activate_problem_lineage_schema(
                    root,
                    observed_at=time.time(),
                    expected_snapshot_sha256=str(before["snapshot"]["sha256"]),
                    expected_logical_sha256=str(before["snapshot"]["logical_sha256"]),
                    runtime_stopped=False,
                )
            with self.assertRaises(ProblemLineageActivationError):
                activate_problem_lineage_schema(
                    root,
                    observed_at=time.time(),
                    expected_snapshot_sha256="0" * 64,
                    expected_logical_sha256=str(before["snapshot"]["logical_sha256"]),
                    runtime_stopped=True,
                )
            self.assertEqual(OrchestrationLedger(root).problem_lineage_schema_version(), 9)


if __name__ == "__main__":
    unittest.main()
