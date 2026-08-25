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
    @staticmethod
    def _seed_v10_schema(ledger: OrchestrationLedger) -> None:
        with ledger._lock, ledger._connect() as connection:
            connection.executescript("""
                CREATE TABLE problem_threads (problem_id TEXT PRIMARY KEY,current_revision INTEGER NOT NULL,resolution_state TEXT NOT NULL,task_class TEXT NOT NULL,engineering_floor TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,closed_at TEXT,latest_problem_event_seq INTEGER NOT NULL DEFAULT 0,latest_problem_event_hash TEXT NOT NULL DEFAULT '');
                CREATE TABLE problem_events (seq INTEGER PRIMARY KEY AUTOINCREMENT,event_id TEXT NOT NULL UNIQUE,problem_id TEXT,task_id TEXT NOT NULL DEFAULT '',turn_id TEXT NOT NULL DEFAULT '',trace_id TEXT NOT NULL DEFAULT '',run_id TEXT NOT NULL DEFAULT '',wave_id TEXT NOT NULL DEFAULT '',capsule_id TEXT NOT NULL DEFAULT '',conversation_epoch INTEGER NOT NULL DEFAULT 0,relation_type TEXT NOT NULL,link_status TEXT NOT NULL,link_role TEXT NOT NULL,feedback_intent TEXT NOT NULL,causal_mechanism TEXT NOT NULL,economic_class TEXT NOT NULL,provenance TEXT NOT NULL,evidence_level TEXT NOT NULL,eligible_for_policy INTEGER NOT NULL DEFAULT 0,state_before TEXT NOT NULL DEFAULT '',state_after TEXT NOT NULL DEFAULT '',reason_code TEXT NOT NULL DEFAULT 'none',criteria_count INTEGER NOT NULL DEFAULT 0,criteria_fingerprint TEXT NOT NULL DEFAULT '',request_hash TEXT NOT NULL,event_time TEXT NOT NULL,prev_hash TEXT NOT NULL DEFAULT '',event_hash TEXT NOT NULL);
                CREATE INDEX idx_problem_events_problem_seq ON problem_events(problem_id,seq);
                CREATE INDEX idx_problem_events_task_turn ON problem_events(task_id,turn_id,seq);
                CREATE INDEX idx_problem_events_run_wave ON problem_events(run_id,wave_id,seq);
                CREATE UNIQUE INDEX idx_problem_events_one_primary_run_binding ON problem_events(run_id) WHERE run_id<>'' AND link_status='EXACT' AND link_role='PRIMARY' AND relation_type IN ('LINK','ENGINEERING_ATTEMPT_BOUND');
                PRAGMA user_version=10;
            """)

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
            self.assertEqual(set(receipt.postflight["schema"]["problem_tables"]), {"problem_threads", "problem_revisions", "problem_events"})
            self.assertEqual(receipt.preflight["event_chain"], receipt.postflight["event_chain"])
            self.assertTrue(OrchestrationLedger(root).verify_chain(run_id)["ok"])

    def test_preflight_and_guarded_v10_to_v11_migration(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            self._seed_v10_schema(ledger)
            before = preflight_problem_lineage_activation(root, observed_at=time.time())
            self.assertEqual(before["schema"]["user_version"], 10)
            self.assertEqual(set(before["schema"]["problem_tables"]), {"problem_threads", "problem_events"})
            receipt = activate_problem_lineage_schema(
                root,
                observed_at=time.time(),
                expected_snapshot_sha256=str(before["snapshot"]["sha256"]),
                expected_logical_sha256=str(before["snapshot"]["logical_sha256"]),
                runtime_stopped=True,
            )
            self.assertTrue(receipt.migration["migrated"])
            self.assertEqual(receipt.migration["from_schema_version"], 10)
            self.assertEqual(receipt.migration["schema_version"], PROBLEM_SCHEMA_VERSION)
            self.assertEqual(set(receipt.postflight["schema"]["problem_tables"]), {"problem_threads", "problem_revisions", "problem_events"})

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
