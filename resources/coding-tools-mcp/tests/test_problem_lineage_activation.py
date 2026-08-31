from __future__ import annotations

import hashlib
import json
import tempfile
import time
import unittest
from pathlib import Path

from coding_tools_mcp.ledger_analysis import open_ledger_analysis_snapshot
from coding_tools_mcp.orchestration_ledger import OrchestrationLedger
from coding_tools_mcp.problem_lineage import PROBLEM_SCHEMA_VERSION, problem_event_hash_material
from coding_tools_mcp.problem_lineage_activation import (
    ProblemLineageActivationError,
    activate_problem_lineage_schema,
    preflight_problem_lineage_activation,
)
from coding_tools_mcp.problem_resolution_economics import ProblemLineageFacts, problem_resolution_economics_report


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

    @staticmethod
    def _seed_v11_schema_with_historical_confirmation(ledger: OrchestrationLedger) -> tuple[str, str]:
        problem_id = "historical-v11-problem"
        capsule = {
            "objective_summary": "Preserve the historical confirmation without inventing a receipt",
            "acceptance_criteria": [{"criterion_id": "criterion-1", "summary": "Historical bytes remain unchanged"}],
            "protected_invariants": [],
            "constraints": [],
            "unresolved_conditions": [],
        }
        canonical_capsule = json.dumps(capsule, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        contract_fingerprint = hashlib.sha256(canonical_capsule.encode()).hexdigest()
        criteria_fingerprint = hashlib.sha256(
            json.dumps(capsule["acceptance_criteria"], ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        event = {
            "event_schema_version": 2,
            "event_id": "historical-v11-confirm",
            "problem_id": problem_id,
            "problem_revision": 1,
            "task_id": "task-historical",
            "turn_id": "turn-historical",
            "trace_id": "trace-historical",
            "run_id": "",
            "wave_id": "",
            "capsule_id": "",
            "conversation_epoch": 0,
            "relation_type": "CONFIRMED_RESOLUTION",
            "link_status": "EXACT",
            "link_role": "PRIMARY",
            "feedback_intent": "CONFIRM_RESOLVED",
            "causal_mechanism": "UNKNOWN",
            "economic_class": "UNKNOWN",
            "provenance": "CONTROLLER_REPORTED_EXPLICIT_USER",
            "evidence_level": "OBSERVED",
            "eligible_for_policy": True,
            "transition_authority": "RUNTIME_EXPLICIT_USER",
            "reason_code": "user_confirmation",
            "criteria_count": 1,
            "criteria_fingerprint": criteria_fingerprint,
            "contract_fingerprint": contract_fingerprint,
            "recorded_at": "2026-08-25T00:00:00Z",
            "occurred_at": "2026-08-25T00:00:00Z",
            "occurred_at_source": "EXPLICIT_USER",
            "clock_authority": "EXPLICIT_USER_ATTESTED",
        }
        material = problem_event_hash_material(
            event,
            state_before="PROVISIONALLY_RESOLVED",
            state_after="RESOLVED_CONFIRMED",
            prev_hash="",
        )
        event_hash = hashlib.sha256(
            json.dumps(material, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        request_hash = hashlib.sha256(b"historical-v11-confirm-request").hexdigest()
        with ledger._lock, ledger._connect() as connection:
            connection.executescript("""
                CREATE TABLE problem_threads (
                    problem_id TEXT PRIMARY KEY,current_revision INTEGER NOT NULL,resolution_state TEXT NOT NULL,task_class TEXT NOT NULL,engineering_floor TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,closed_at TEXT,latest_problem_event_seq INTEGER NOT NULL DEFAULT 0,latest_problem_event_hash TEXT NOT NULL DEFAULT ''
                );
                CREATE TABLE problem_revisions (
                    problem_id TEXT NOT NULL REFERENCES problem_threads(problem_id) ON DELETE RESTRICT,revision INTEGER NOT NULL CHECK(revision>=1),contract_fingerprint TEXT NOT NULL,criteria_fingerprint TEXT NOT NULL,criteria_count INTEGER NOT NULL,typed_contract_capsule TEXT NOT NULL,task_class TEXT NOT NULL,engineering_floor TEXT NOT NULL,created_event_seq INTEGER NOT NULL DEFAULT 0,created_at TEXT NOT NULL,creation_authority TEXT NOT NULL,PRIMARY KEY(problem_id,revision)
                );
                CREATE TABLE problem_events (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT,event_id TEXT NOT NULL UNIQUE,event_schema_version INTEGER NOT NULL DEFAULT 2,problem_id TEXT REFERENCES problem_threads(problem_id) ON DELETE RESTRICT,problem_revision INTEGER,task_id TEXT NOT NULL DEFAULT '',turn_id TEXT NOT NULL DEFAULT '',trace_id TEXT NOT NULL DEFAULT '',run_id TEXT NOT NULL DEFAULT '',wave_id TEXT NOT NULL DEFAULT '',capsule_id TEXT NOT NULL DEFAULT '',conversation_epoch INTEGER NOT NULL DEFAULT 0,relation_type TEXT NOT NULL,link_status TEXT NOT NULL,link_role TEXT NOT NULL,feedback_intent TEXT NOT NULL,causal_mechanism TEXT NOT NULL,economic_class TEXT NOT NULL,provenance TEXT NOT NULL,evidence_level TEXT NOT NULL,eligible_for_policy INTEGER NOT NULL DEFAULT 0,transition_authority TEXT NOT NULL DEFAULT '',state_before TEXT NOT NULL DEFAULT '',state_after TEXT NOT NULL DEFAULT '',reason_code TEXT NOT NULL DEFAULT 'none',criteria_count INTEGER NOT NULL DEFAULT 0,criteria_fingerprint TEXT NOT NULL DEFAULT '',contract_fingerprint TEXT NOT NULL DEFAULT '',request_hash TEXT NOT NULL,recorded_at TEXT,occurred_at TEXT NOT NULL DEFAULT '',occurred_at_source TEXT NOT NULL DEFAULT '',clock_authority TEXT NOT NULL DEFAULT '',event_time TEXT NOT NULL DEFAULT '',prev_hash TEXT NOT NULL DEFAULT '',event_hash TEXT NOT NULL,
                    CHECK((event_schema_version=1) OR (event_schema_version=2 AND recorded_at IS NOT NULL AND recorded_at<>'')),
                    CHECK((event_schema_version=1) OR ((occurred_at='' AND occurred_at_source='' AND clock_authority='') OR (occurred_at<>'' AND occurred_at_source<>'' AND clock_authority<>''))),
                    CHECK((event_schema_version=1) OR ((link_status='EXACT' AND problem_id IS NOT NULL AND problem_revision IS NOT NULL) OR (link_status<>'EXACT' AND problem_id IS NULL AND problem_revision IS NULL))),
                    FOREIGN KEY(problem_id,problem_revision) REFERENCES problem_revisions(problem_id,revision) ON DELETE RESTRICT
                );
                CREATE INDEX idx_problem_events_problem_seq ON problem_events(problem_id,seq);
                CREATE INDEX idx_problem_events_problem_revision_seq ON problem_events(problem_id,problem_revision,seq);
                CREATE INDEX idx_problem_events_task_turn ON problem_events(task_id,turn_id,seq);
                CREATE INDEX idx_problem_events_run_wave ON problem_events(run_id,wave_id,seq);
                CREATE UNIQUE INDEX idx_problem_events_one_primary_run_binding ON problem_events(run_id) WHERE run_id<>'' AND link_status='EXACT' AND link_role='PRIMARY' AND relation_type IN ('LINK','ENGINEERING_ATTEMPT_BOUND');
                PRAGMA user_version=11;
            """)
            connection.execute(
                "INSERT INTO problem_threads VALUES(?,?,?,?,?,?,?,?,?,?)",
                (problem_id, 1, "RESOLVED_CONFIRMED", "bugfix", "REQUIRED", event["recorded_at"], event["recorded_at"], event["recorded_at"], 1, event_hash),
            )
            connection.execute(
                "INSERT INTO problem_revisions VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (problem_id, 1, contract_fingerprint, criteria_fingerprint, 1, canonical_capsule, "bugfix", "REQUIRED", 1, event["recorded_at"], "RUNTIME_EXPLICIT_USER"),
            )
            connection.execute(
                """INSERT INTO problem_events(seq,event_id,event_schema_version,problem_id,problem_revision,task_id,turn_id,trace_id,run_id,wave_id,capsule_id,conversation_epoch,relation_type,link_status,link_role,feedback_intent,causal_mechanism,economic_class,provenance,evidence_level,eligible_for_policy,transition_authority,state_before,state_after,reason_code,criteria_count,criteria_fingerprint,contract_fingerprint,request_hash,recorded_at,occurred_at,occurred_at_source,clock_authority,event_time,prev_hash,event_hash) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (1, event["event_id"], 2, problem_id, 1, event["task_id"], event["turn_id"], event["trace_id"], "", "", "", 0, event["relation_type"], event["link_status"], event["link_role"], event["feedback_intent"], event["causal_mechanism"], event["economic_class"], event["provenance"], event["evidence_level"], 1, event["transition_authority"], "PROVISIONALLY_RESOLVED", "RESOLVED_CONFIRMED", event["reason_code"], 1, criteria_fingerprint, contract_fingerprint, request_hash, event["recorded_at"], event["occurred_at"], event["occurred_at_source"], event["clock_authority"], "", "", event_hash),
            )
        return problem_id, event_hash

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

    def test_preflight_and_guarded_v10_to_v12_migration(self) -> None:
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

    def test_guarded_v11_to_v12_migration_preserves_historical_event_bytes_without_receipt_backfill(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            problem_id, historical_hash = self._seed_v11_schema_with_historical_confirmation(ledger)
            before = preflight_problem_lineage_activation(root, observed_at=time.time())
            self.assertEqual(before["schema"]["user_version"], 11)
            self.assertNotIn("outcome_receipt_type", before["schema"]["problem_event_columns"])
            self.assertNotIn("outcome_receipt_id", before["schema"]["problem_event_columns"])
            receipt = activate_problem_lineage_schema(
                root,
                observed_at=time.time(),
                expected_snapshot_sha256=str(before["snapshot"]["sha256"]),
                expected_logical_sha256=str(before["snapshot"]["logical_sha256"]),
                runtime_stopped=True,
            )
            self.assertEqual(receipt.migration["from_schema_version"], 11)
            self.assertEqual(receipt.migration["schema_version"], 12)
            self.assertIn("outcome_receipt_type", receipt.postflight["schema"]["problem_event_columns"])
            self.assertIn("outcome_receipt_id", receipt.postflight["schema"]["problem_event_columns"])
            migrated = OrchestrationLedger(root)
            problem = migrated.problem_get(problem_id)
            assert problem is not None
            event = problem["events"][0]
            self.assertEqual(event["event_schema_version"], 2)
            self.assertEqual(event["event_hash"], historical_hash)
            self.assertEqual(event["outcome_receipt_type"], "")
            self.assertEqual(event["outcome_receipt_id"], "")
            self.assertTrue(migrated.problem_verify_chain(problem_id)["ok"])
            with open_ledger_analysis_snapshot(root) as snapshot:
                report = problem_resolution_economics_report(
                    snapshot.ledger,
                    ProblemLineageFacts.load(snapshot.reader),
                )
            independent = report["revision_4_metrics"]["independent_outcome_evidence_coverage"]
            self.assertEqual(independent["authoritative_confirmation_events"], 1)
            self.assertEqual(independent["receipt_bound_confirmation_events"], 0)
            self.assertEqual(independent["unbound_authoritative_confirmation_events"], 1)
            self.assertEqual(independent["coverage"], 0.0)
            self.assertTrue(independent["historical_confirmations_not_backfilled"])

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
