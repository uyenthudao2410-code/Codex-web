from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from coding_tools_mcp.ledger_access import open_existing_ledger_analysis, open_existing_ledger_readonly
from coding_tools_mcp.ledger_analysis import organic_rework_summary
from coding_tools_mcp.orchestration_ledger import OrchestrationLedger
from coding_tools_mcp.solution_economics import record_solution_shadow, solution_shadow_population_report


class LedgerAnalysisTests(unittest.TestCase):
    def _ledger(self, root: Path) -> tuple[OrchestrationLedger, str, str]:
        ledger = OrchestrationLedger(root)
        head = "a" * 40
        first = ledger.create_run(objective="feature", metadata={"workflow": "feature"})
        first_wave = ledger.create_wave(first, execution_mode="mcp_only", base_head=head)
        ledger.finish_wave(first_wave, status="accepted")
        ledger.finish_run(first, status="accepted")
        repaired = ledger.create_run(objective="bugfix", metadata={"workflow": "bugfix"})
        repaired_wave = ledger.create_wave(repaired, execution_mode="mcp_only", base_head=head)
        ledger.append_event(repaired, wave_id=repaired_wave, event_type="failure_observed", state_before="EXECUTING", state_after="REPLAN", payload={"failure_class": "BASE_DRIFT"})
        ledger.finish_wave(repaired_wave, status="replanned")
        accepted_wave = ledger.create_wave(repaired, execution_mode="mcp_only", base_head=head)
        ledger.finish_wave(accepted_wave, status="accepted")
        ledger.finish_run(repaired, status="accepted")
        return ledger, first, repaired

    def test_reader_and_backup_snapshot_do_not_mutate_canonical_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger, _, repaired = self._ledger(root)
            source = ledger.path
            before = hashlib.sha256(source.read_bytes()).hexdigest()
            with open_existing_ledger_readonly(root) as reader:
                self.assertEqual(reader.one("PRAGMA query_only")[0], 1)
                with self.assertRaises(Exception):
                    reader.rows("INSERT INTO runs(run_id,status,started_at) VALUES('forbidden','active','now')")
            with open_existing_ledger_analysis(root) as snapshot:
                self.assertEqual(snapshot.live_backup_connections, 1)
                self.assertEqual(snapshot.ledger.accepted_result_economics(repaired), ledger.accepted_result_economics(repaired))
                self.assertEqual(organic_rework_summary(snapshot.ledger), ledger.organic_rework_summary())
                with self.assertRaises(RuntimeError):
                    snapshot.ledger._connect()
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), before)

    def test_snapshot_preserves_solution_shadow_population_semantics(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger, _, _ = self._ledger(root)
            run_id = ledger.create_run(objective="shadow", metadata={"workflow": "feature"})
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only", base_head="a" * 40)
            record_solution_shadow(
                ledger,
                run_id=run_id,
                wave_id=wave_id,
                recommendation={
                    "recommendation_id": "snapshot-shadow",
                    "candidate_solution_scope": "localized_file",
                    "estimated_touched_surface": {"files": 1, "symbols": 1},
                    "root_cause_confidence": "high",
                    "oracle_strength": "strong",
                    "expected_repair_risk": "low",
                    "smallest_causal_solution": {"scope": "localized_symbol", "estimated_touched_surface": {"files": 1}},
                },
            )
            ledger.finish_wave(wave_id, status="accepted")
            ledger.finish_run(run_id, status="accepted")
            expected = solution_shadow_population_report(ledger)
            with open_existing_ledger_analysis(root) as snapshot:
                self.assertEqual(solution_shadow_population_report(snapshot.ledger), expected)

    def test_snapshot_preserves_proof_cache_summary_without_extra_sql(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger, accepted, _ = self._ledger(root)
            wave_id = ledger.list_waves(accepted)[0]["wave_id"]
            source_proof = ledger.record_proof(
                run_id=accepted, wave_id=wave_id, stage_id="verify:tests", stage_version="1",
                input_fingerprint="cache-source", status="passed", duration_ms=125,
            )
            ledger.append_event(accepted, wave_id=wave_id, event_type="proof_cache_miss", payload={
                "stage_id": "verify:tests", "stage_version": "1", "reason": "cold",
            })
            ledger.append_event(accepted, wave_id=wave_id, event_type="proof_cache_hit", payload={
                "stage_id": "verify:tests", "stage_version": "1", "source_proof_id": source_proof,
            })
            expected = ledger.proof_cache_opportunity_summary(stage_limit=1)
            with open_existing_ledger_analysis(root) as snapshot:
                self.assertEqual(snapshot.statement_count, 8)
                self.assertEqual(snapshot.ledger.proof_cache_opportunity_summary(stage_limit=1), expected)
                self.assertEqual(snapshot.statement_count, 8)

    def test_selective_indexes_cover_remaining_legacy_lookup_shapes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger, _, _ = self._ledger(root)
            with open_existing_ledger_readonly(root) as reader:
                plans = {
                    "runs": reader.rows("EXPLAIN QUERY PLAN SELECT run_id FROM runs WHERE status='accepted' ORDER BY started_at,run_id LIMIT 100"),
                    "delegations": reader.rows("EXPLAIN QUERY PLAN SELECT * FROM delegations WHERE wave_id=? ORDER BY started_at", ("wave",)),
                    "proofs": reader.rows("EXPLAIN QUERY PLAN SELECT * FROM proofs WHERE run_id=? ORDER BY finished_at,proof_id", ("run",)),
                    "checkpoints": reader.rows("EXPLAIN QUERY PLAN SELECT * FROM checkpoints WHERE run_id=? ORDER BY created_at,checkpoint_id", ("run",)),
                    "background": reader.rows("EXPLAIN QUERY PLAN SELECT * FROM background_operations WHERE run_id=? AND status=? ORDER BY updated_at DESC", ("run", "active")),
                }
            names = {"runs": "idx_runs_status_started_run", "delegations": "idx_delegations_wave_started", "proofs": "idx_proofs_run_finished", "checkpoints": "idx_checkpoints_run_created", "background": "idx_background_operations_run_status_updated"}
            for name, plan in plans.items():
                self.assertTrue(any(names[name] in str(row[3]) for row in plan), f"{name}: {plan}")
            self.assertTrue(ledger.path.is_file())


if __name__ == "__main__":
    unittest.main()
