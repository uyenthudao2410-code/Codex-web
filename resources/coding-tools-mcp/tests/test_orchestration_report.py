from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from coding_tools_mcp.orchestration_ledger import OrchestrationLedger
from coding_tools_mcp.orchestration_report import OrchestrationReport


class OrchestrationReportTests(unittest.TestCase):
    def test_reports_are_generated_from_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            run_id = ledger.create_run(objective="document the wave", task_id="task-r")
            wave_id = ledger.create_wave(run_id, execution_mode="bounded_candidate", base_head="abc", worktree_fp="fp")
            delegation_id = ledger.create_delegation(
                wave_id,
                authority_owner="CODEX:mini",
                route_requested="auto",
                route_resolved="mini",
                model="gpt-test",
                effort="low",
                allowed_scope=["app.py"],
            )
            ledger.append_event(
                run_id,
                wave_id=wave_id,
                delegation_id=delegation_id,
                event_type="route_selected",
                state_before="READY",
                state_after="ROUTED",
                payload={"requested": "auto", "resolved": "mini", "reason": "strong_oracle"},
            )
            ledger.record_proof(
                run_id=run_id,
                wave_id=wave_id,
                stage_id="focused",
                stage_version="1",
                input_fingerprint="proof-fp",
                status="passed",
            )
            ledger.record_checkpoint(
                run_id=run_id,
                wave_id=wave_id,
                git_head="abc",
                proof_fingerprint="proof-fp",
                status="accepted",
                metadata={"accepted_by": "ChatWeb Sol"},
            )
            ledger.finish_delegation(delegation_id, status="accepted_candidate")
            ledger.finish_wave(wave_id, status="accepted")
            ledger.finish_run(run_id, status="accepted")

            report = OrchestrationReport(root, ledger)
            paths = report.write_reports(run_id)
            run_text = Path(paths["run_report"]).read_text(encoding="utf-8")
            wave_text = Path(paths["wave_reports"][0]).read_text(encoding="utf-8")
            self.assertIn("Orchestration Run Summary", run_text)
            self.assertIn("mini", run_text)
            self.assertIn("Hash chain valid: **True**", run_text)
            self.assertIn("Acceptance checkpoints: **1**", run_text)
            self.assertIn("ChatWeb Sol", run_text)
            self.assertIn("proof-fp", run_text)
            self.assertIn("CODEX:mini", wave_text)
            self.assertIn("focused", wave_text)
            self.assertIn("Objective revision: `1`", wave_text)
            self.assertIn("Objective source: `run_initial_objective`", wave_text)
            self.assertIn("## Acceptance checkpoints", wave_text)
            self.assertIn("ChatWeb Sol", wave_text)


if __name__ == "__main__":
    unittest.main()
