from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path

from benchmarks.runtime_activation import build_snapshot
from coding_tools_mcp.orchestration_ledger import OrchestrationLedger
from coding_tools_mcp.performance_trace import PerformanceTraceStore


class RuntimeActivationSnapshotTests(unittest.TestCase):
    def test_snapshot_uses_explicit_idempotency_denominator_and_durable_tta(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            trace = PerformanceTraceStore(root)
            trace.record(
                tool="workspace_context",
                started_monotonic=1.0,
                finished_monotonic=1.1,
                idempotency_eligible=False,
            )
            trace.record(
                tool="exec_command",
                started_monotonic=2.0,
                finished_monotonic=2.2,
                idempotency_eligible=True,
                idempotency_key_present=True,
                proof_cache_hits=1,
                proof_cache_saved_ms=900,
                orchestration={"run_id": "run-measured", "route_resolved": "deterministic", "execution_mode": "mcp_only"},
            )
            ledger = OrchestrationLedger(root)
            run_id = ledger.create_run(objective="measurement")
            time.sleep(0.01)
            ledger.finish_run(run_id, status="accepted")
            snapshot = build_snapshot(root)
            performance = snapshot["performance"]
            self.assertEqual(performance["version"], 3)
            self.assertEqual(performance["idempotency_eligible_calls"], 1)
            self.assertEqual(performance["idempotency_eligible_key_calls"], 1)
            self.assertEqual(performance["idempotency_coverage"], 1.0)
            self.assertEqual(performance["proof_cache_saved_ms"], 900)
            self.assertEqual(snapshot["ledger"]["accepted_run_tta"]["n"], 1)
            self.assertEqual(snapshot["evidence_class"], "local_runtime_measurement_snapshot")


if __name__ == "__main__":
    unittest.main()
