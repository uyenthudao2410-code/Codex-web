from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from coding_tools_mcp.orchestration_ledger import OrchestrationLedger
from coding_tools_mcp.solution_economics import record_solution_shadow, solution_shadow_population_report


def recommendation(recommendation_id: str) -> dict[str, object]:
    return {
        "recommendation_id": recommendation_id,
        "candidate_solution_scope": "localized_file",
        "estimated_touched_surface": {"files": 1, "lines": 4},
        "root_cause_confidence": "medium",
        "oracle_strength": "strong",
        "expected_repair_risk": "low",
        "smallest_causal_solution": {
            "scope": "localized_file",
            "estimated_touched_surface": {"files": 1, "lines": 4},
        },
    }


class P4PopulationWindowTests(unittest.TestCase):
    def test_limit_applies_to_shadow_runs_not_unrelated_run_churn(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))

            def shadow(name: str) -> str:
                run_id = ledger.create_run(
                    objective=name,
                    metadata={"workflow": "feature", "evaluation": {"provenance": "representative"}},
                )
                wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
                record_solution_shadow(
                    ledger,
                    run_id=run_id,
                    wave_id=wave_id,
                    recommendation=recommendation(f"rec-{name}"),
                )
                ledger.finish_wave(wave_id, status="accepted")
                ledger.finish_run(run_id, status="accepted")
                return run_id

            oldest = shadow("oldest")
            for index in range(8):
                ledger.create_run(objective=f"diagnostic-before-{index}", metadata={"workflow": "diagnose"})
            middle = shadow("middle")
            for index in range(12):
                ledger.create_run(objective=f"diagnostic-middle-{index}", metadata={"workflow": "diagnose"})
            newest = shadow("newest")
            for index in range(20):
                ledger.create_run(objective=f"diagnostic-after-{index}", metadata={"workflow": "diagnose"})

            population = solution_shadow_population_report(ledger, limit=2)
            self.assertEqual(population["population_scope"], "latest_shadow_runs_v2")
            self.assertEqual(population["scan_limit"], 2)
            self.assertEqual(population["scan_limit_semantics"], "shadow_runs_with_solution_shadow_event")
            self.assertEqual(population["cohort"]["shadow_tasks"], 2)
            self.assertEqual([item["run_id"] for item in population["records"]], [newest, middle])
            self.assertNotIn(oldest, {item["run_id"] for item in population["records"]})


if __name__ == "__main__":
    unittest.main()
