from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from coding_tools_mcp import ledger_evidence_recovery as recovery


PROBLEM_ID = "prl-test"
RUN_ID = "run-recovered"
WAVE_ID = "wave-recovered"


def _event_hash(*, event_id: str, run_id: str, event_time: str, wave_id: str = "", prev_hash: str = "") -> str:
    material = {
        "event_id": event_id,
        "run_id": run_id,
        "wave_id": wave_id,
        "delegation_id": "",
        "event_type": "run_started",
        "state_before": "",
        "state_after": "PREFLIGHT",
        "event_time": event_time,
        "payload": {},
        "prev_hash": prev_hash,
    }
    return hashlib.sha256(json.dumps(material, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        PRAGMA foreign_keys=ON;
        CREATE TABLE runs(run_id TEXT PRIMARY KEY, task_id TEXT NOT NULL, objective TEXT NOT NULL,
            status TEXT NOT NULL, started_at TEXT NOT NULL, finished_at TEXT, metadata_json TEXT NOT NULL);
        CREATE TABLE waves(wave_id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(run_id), ordinal INTEGER NOT NULL,
            execution_mode TEXT NOT NULL, base_head TEXT NOT NULL, worktree_fp TEXT NOT NULL, contract_fp TEXT NOT NULL,
            status TEXT NOT NULL, started_at TEXT NOT NULL, finished_at TEXT, metadata_json TEXT NOT NULL);
        CREATE TABLE checkpoints(checkpoint_id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(run_id), wave_id TEXT,
            git_head TEXT NOT NULL, proof_fingerprint TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL, metadata_json TEXT NOT NULL);
        CREATE TABLE proofs(proof_id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(run_id), wave_id TEXT NOT NULL REFERENCES waves(wave_id),
            stage_id TEXT NOT NULL, stage_version TEXT NOT NULL, input_fingerprint TEXT NOT NULL, status TEXT NOT NULL,
            command_hash TEXT NOT NULL, started_at TEXT NOT NULL, finished_at TEXT NOT NULL, duration_ms INTEGER NOT NULL,
            exit_code INTEGER, cache_hit INTEGER NOT NULL, upstream_json TEXT NOT NULL, metadata_json TEXT NOT NULL);
        CREATE TABLE events(seq INTEGER PRIMARY KEY, event_id TEXT NOT NULL UNIQUE, run_id TEXT NOT NULL REFERENCES runs(run_id),
            wave_id TEXT, delegation_id TEXT, event_type TEXT NOT NULL, state_before TEXT NOT NULL, state_after TEXT NOT NULL,
            event_time TEXT NOT NULL, payload_json TEXT NOT NULL, prev_hash TEXT NOT NULL, event_hash TEXT NOT NULL);
        CREATE TABLE continuity_telemetry(logical_id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(run_id), wave_id TEXT,
            event_type TEXT NOT NULL, problem_id TEXT, problem_revision INTEGER, task_context_id TEXT, activation_epoch_id TEXT,
            process_instance_id TEXT, server_instance_id TEXT, restart_ticket_id TEXT, outcome TEXT, code TEXT, duration_ms INTEGER,
            event_time TEXT NOT NULL, record_sha256 TEXT NOT NULL, provenance TEXT NOT NULL);
        CREATE TABLE controller_knowledge_acks(ack_id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL, problem_id TEXT NOT NULL,
            problem_revision INTEGER NOT NULL, knowledge_revision TEXT NOT NULL, current_knowledge_revision TEXT NOT NULL,
            controller_endpoint_id TEXT NOT NULL, status TEXT NOT NULL, request_hash TEXT NOT NULL, recovery_json TEXT NOT NULL, created_at TEXT NOT NULL);
        CREATE TABLE problem_threads(problem_id TEXT PRIMARY KEY, current_revision INTEGER NOT NULL, resolution_state TEXT NOT NULL,
            task_class TEXT NOT NULL, engineering_floor TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
            closed_at TEXT, latest_problem_event_seq INTEGER NOT NULL, latest_problem_event_hash TEXT NOT NULL);
        CREATE TABLE problem_revisions(problem_id TEXT NOT NULL REFERENCES problem_threads(problem_id), revision INTEGER NOT NULL,
            contract_fingerprint TEXT NOT NULL, criteria_fingerprint TEXT NOT NULL, criteria_count INTEGER NOT NULL,
            typed_contract_capsule TEXT NOT NULL, task_class TEXT NOT NULL, engineering_floor TEXT NOT NULL, created_event_seq INTEGER NOT NULL,
            created_at TEXT NOT NULL, creation_authority TEXT NOT NULL, PRIMARY KEY(problem_id,revision));
        CREATE TABLE problem_events(seq INTEGER PRIMARY KEY, event_id TEXT NOT NULL UNIQUE, problem_id TEXT NOT NULL,
            problem_revision INTEGER NOT NULL, run_id TEXT NOT NULL, wave_id TEXT NOT NULL, relation_type TEXT NOT NULL,
            link_status TEXT NOT NULL, link_role TEXT NOT NULL, state_before TEXT NOT NULL, state_after TEXT NOT NULL,
            recorded_at TEXT NOT NULL, prev_hash TEXT NOT NULL, event_hash TEXT NOT NULL,
            FOREIGN KEY(problem_id,problem_revision) REFERENCES problem_revisions(problem_id,revision));
        CREATE TABLE controller_leases(run_id TEXT PRIMARY KEY, status TEXT NOT NULL);
        CREATE TABLE idempotency_records(idempotency_key TEXT PRIMARY KEY, status TEXT NOT NULL);
        CREATE INDEX idx_events_run_seq ON events(run_id,seq);
        """
    )
    base_hash = _event_hash(event_id="event-base", run_id="run-base", event_time="2026-09-22T00:00:00Z")
    connection.execute(
        "INSERT INTO runs VALUES(?,?,?,?,?,?,?)",
        ("run-base", "task", "base", "accepted", "2026-09-22T00:00:00Z", "2026-09-22T00:00:01Z", "{}"),
    )
    connection.execute(
        "INSERT INTO events VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
        (1, "event-base", "run-base", "", "", "run_started", "", "PREFLIGHT", "2026-09-22T00:00:00Z", "{}", "", base_hash),
    )
    connection.execute(
        "INSERT INTO problem_threads VALUES(?,?,?,?,?,?,?,?,?,?)",
        (PROBLEM_ID, 1, "OPEN", "bugfix", "REQUIRED", "2026-09-22T00:00:00Z", "2026-09-22T00:00:01Z", None, 1, "problem-base"),
    )
    connection.execute(
        "INSERT INTO problem_revisions VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (PROBLEM_ID, 1, "contract", "criteria", 1, "{}", "bugfix", "REQUIRED", 1, "2026-09-22T00:00:00Z", "TEST"),
    )
    connection.execute(
        "INSERT INTO problem_events VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (1, "problem-base", PROBLEM_ID, 1, "", "", "OPEN", "EXACT", "PRIMARY", "OPEN", "OPEN", "2026-09-22T00:00:01Z", "", "problem-base"),
    )
    connection.commit()


class LedgerEvidenceRecoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="ledger-evidence-recovery-")
        self.root = Path(self.temp.name)
        self.ledger_path = self.root / ".coding-tools" / "orchestration" / "ledger.sqlite3"
        self.ledger_path.parent.mkdir(parents=True)
        connection = sqlite3.connect(self.ledger_path)
        _schema(connection)
        connection.close()
        self.candidate = self.root / "candidate.sqlite3"
        shutil.copyfile(self.ledger_path, self.candidate)
        connection = sqlite3.connect(self.candidate)
        recovered_hash = _event_hash(event_id="event-recovered", run_id=RUN_ID, event_time="2026-09-22T00:01:00Z", wave_id=WAVE_ID)
        connection.execute(
            "INSERT INTO runs VALUES(?,?,?,?,?,?,?)",
            (RUN_ID, "task", "recovered evidence", "accepted", "2026-09-22T00:01:00Z", "2026-09-22T00:02:00Z", "{}"),
        )
        connection.execute(
            "INSERT INTO waves VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (WAVE_ID, RUN_ID, 1, "mcp_only", "head", "fp", "contract", "accepted", "2026-09-22T00:01:00Z", "2026-09-22T00:02:00Z", "{}"),
        )
        connection.execute(
            "INSERT INTO events VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (2, "event-recovered", RUN_ID, WAVE_ID, "", "run_started", "", "PREFLIGHT", "2026-09-22T00:01:00Z", "{}", "", recovered_hash),
        )
        connection.execute(
            "INSERT INTO checkpoints VALUES(?,?,?,?,?,?,?,?)",
            ("checkpoint-recovered", RUN_ID, WAVE_ID, "head", "proof", "accepted", "2026-09-22T00:02:00Z", "{}"),
        )
        connection.execute(
            "INSERT INTO proofs VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ("proof-recovered", RUN_ID, WAVE_ID, "test", "1", "input", "passed", "command", "2026-09-22T00:01:00Z", "2026-09-22T00:02:00Z", 1, 0, 0, "[]", "{}"),
        )
        connection.execute(
            "INSERT INTO continuity_telemetry VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ("telemetry-recovered", RUN_ID, WAVE_ID, "continuation_success", PROBLEM_ID, 1, "ctx", "epoch", "proc", "server", "ticket", "observed", "OK", 1, "2026-09-22T00:02:00Z", "digest", "test"),
        )
        connection.execute(
            "INSERT INTO controller_knowledge_acks VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            ("ack-recovered", "workspace", PROBLEM_ID, 1, "k1", "k1", "controller", "acknowledged", "request", "{}", "2026-09-22T00:02:00Z"),
        )
        connection.execute(
            "INSERT INTO problem_events VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (2, "problem-recovered", PROBLEM_ID, 1, RUN_ID, WAVE_ID, "ENGINEERING_ATTEMPT_BOUND", "EXACT", "PRIMARY", "OPEN", "OPEN", "2026-09-22T00:02:00Z", "problem-base", "problem-recovered-hash"),
        )
        connection.execute("INSERT INTO idempotency_records VALUES(?,?)", ("unknown-recovered", "unknown"))
        connection.commit()
        connection.close()
        self.mock_readiness = patch.object(
            recovery,
            "inspect_maintenance_readiness",
            return_value={
                "compact_allowed": True,
                "active_controller_leases": 0,
                "active_write_fences": 0,
                "active_managed_jobs": 0,
                "active_background_operations": 0,
                "integrity_check": "ok",
                "foreign_key_violations": 0,
                "logical_sha256": "",
            },
        )
        self.mock_readiness.start()

    def tearDown(self) -> None:
        self.mock_readiness.stop()
        self.temp.cleanup()

    def _preflight(self) -> dict[str, object]:
        current = recovery._snapshot(self.ledger_path, immutable=False)
        candidate = recovery._snapshot(self.candidate, immutable=True)
        return recovery.preflight_evidence_recovery(
            self.root,
            candidate=self.candidate,
            expected_current_sha256=current.physical_sha256,
            expected_current_logical_sha256=current.logical_sha256,
            expected_candidate_sha256=candidate.physical_sha256,
            expected_candidate_logical_sha256=candidate.logical_sha256,
            allowed_run_ids={RUN_ID},
            allowed_problem_ids={PROBLEM_ID},
            allowed_evidence_ids={"ack-recovered"},
        )

    def _candidate_with_existing_run_evidence(self) -> tuple[Path, str]:
        candidate = self.root / "candidate-existing-run.sqlite3"
        shutil.copyfile(self.candidate, candidate)
        identity = "continuity-existing-run"
        connection = sqlite3.connect(candidate)
        connection.execute(
            "INSERT INTO continuity_telemetry VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                identity,
                "run-base",
                "",
                "continuation_failure",
                PROBLEM_ID,
                1,
                "ctx-existing",
                "epoch-existing",
                "proc-existing",
                "server-existing",
                "ticket-existing",
                "observed",
                "RECOVERY_TEST",
                1,
                "2026-09-22T00:03:00Z",
                "digest-existing",
                "test",
            ),
        )
        connection.commit()
        connection.close()
        return candidate, identity

    def test_preflight_imports_only_immutable_evidence_and_proposes_pointer_cas(self) -> None:
        before = recovery._sha256_file(self.ledger_path)
        receipt = self._preflight()
        self.assertEqual(recovery._sha256_file(self.ledger_path), before)
        self.assertEqual(receipt["immutable_additions"]["runs"], 1)
        self.assertEqual(receipt["immutable_additions"]["problem_events"], 1)
        self.assertEqual(receipt["withheld_effects"]["idempotency_records"]["row_count"], 1)
        self.assertEqual(receipt["pointer_plans"][0]["current_pointer_seq"], 1)
        self.assertEqual(receipt["pointer_plans"][0]["proposed_pointer_seq"], 2)
        self.assertTrue(receipt["apply_eligible"])
        self.assertFalse(receipt["recovery_policy"]["activation_eligible"])
        self.assertTrue(receipt["probe"]["canonical_mutated"] is False)

    def test_apply_requires_stopped_runtime_and_exact_receipt_then_preserves_unknown_effect(self) -> None:
        preflight = self._preflight()
        quiesce = self.root / "quiesce.json"
        snapshot = preflight["current_snapshot"]
        quiesce.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "kind": "LEDGER_RECOVERY_QUIESCE",
                    "workspace": str(self.root),
                    "ledger_path": str(self.ledger_path),
                    "runtime_stopped": True,
                    "operator_authority": "test",
                    "source_snapshot": snapshot,
                    "ownership": {"active_controller_leases": 0, "active_write_fences": 0, "active_managed_jobs": 0, "active_background_operations": 0},
                }
            ),
            encoding="utf-8",
        )
        rollback = self.root / "rollback.sqlite3"
        with self.assertRaisesRegex(recovery.LedgerEvidenceRecoveryError, "RUNTIME_STOPPED"):
            recovery.apply_evidence_recovery(
                self.root,
                candidate=self.candidate,
                preflight=preflight,
                quiesce_receipt=quiesce,
                rollback_backup=rollback,
                runtime_stopped=False,
                authority="test",
            )
        result = recovery.apply_evidence_recovery(
            self.root,
            candidate=self.candidate,
            preflight=preflight,
            quiesce_receipt=quiesce,
            rollback_backup=rollback,
            runtime_stopped=True,
            authority="test",
        )
        self.assertTrue(result["committed"])
        self.assertEqual(result["replay_allowed"], 0)
        self.assertEqual(result["problem_pointer_updates"][0]["from_seq"], 1)
        self.assertEqual(result["problem_pointer_updates"][0]["to_seq"], 2)
        self.assertTrue(rollback.exists())
        connection = sqlite3.connect(self.ledger_path)
        self.assertEqual(connection.execute("SELECT COUNT(*) FROM runs WHERE run_id=?", (RUN_ID,)).fetchone()[0], 1)
        self.assertEqual(connection.execute("SELECT latest_problem_event_seq FROM problem_threads WHERE problem_id=?", (PROBLEM_ID,)).fetchone()[0], 2)
        self.assertEqual(connection.execute("SELECT COUNT(*) FROM idempotency_records WHERE idempotency_key='unknown-recovered'").fetchone()[0], 0)
        connection.close()

    def test_source_drift_after_preflight_refuses_without_mutation(self) -> None:
        preflight = self._preflight()
        connection = sqlite3.connect(self.ledger_path)
        connection.execute("UPDATE problem_threads SET updated_at='drift' WHERE problem_id=?", (PROBLEM_ID,))
        connection.commit()
        connection.close()
        quiesce = self.root / "quiesce.json"
        quiesce.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "kind": "LEDGER_RECOVERY_QUIESCE",
                    "workspace": str(self.root),
                    "ledger_path": str(self.ledger_path),
                    "runtime_stopped": True,
                    "operator_authority": "test",
                    "source_snapshot": preflight["current_snapshot"],
                    "ownership": {"active_controller_leases": 0, "active_write_fences": 0, "active_managed_jobs": 0, "active_background_operations": 0},
                }
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(recovery.LedgerEvidenceRecoveryError, "SOURCE_DRIFT"):
            recovery.apply_evidence_recovery(
                self.root,
                candidate=self.candidate,
                preflight=preflight,
                quiesce_receipt=quiesce,
                rollback_backup=self.root / "rollback.sqlite3",
                runtime_stopped=True,
                authority="test",
            )
        self.assertFalse((self.root / "rollback.sqlite3").exists())

    def test_existing_run_evidence_requires_exact_run_and_identity_allowlists(self) -> None:
        candidate, identity = self._candidate_with_existing_run_evidence()
        current = recovery._snapshot(self.ledger_path, immutable=False)
        candidate_snapshot = recovery._snapshot(candidate, immutable=True)
        common = {
            "candidate": candidate,
            "expected_current_sha256": current.physical_sha256,
            "expected_current_logical_sha256": current.logical_sha256,
            "expected_candidate_sha256": candidate_snapshot.physical_sha256,
            "expected_candidate_logical_sha256": candidate_snapshot.logical_sha256,
            "allowed_run_ids": {RUN_ID},
            "allowed_problem_ids": {PROBLEM_ID},
            "allowed_evidence_ids": {"ack-recovered"},
        }
        with self.assertRaisesRegex(recovery.LedgerEvidenceRecoveryError, "EXISTING_RUN_NOT_ALLOWLISTED"):
            recovery.preflight_evidence_recovery(self.root, **common)
        with self.assertRaisesRegex(recovery.LedgerEvidenceRecoveryError, "EXISTING_EVIDENCE_ID_NOT_ALLOWLISTED"):
            recovery.preflight_evidence_recovery(
                self.root,
                **common,
                allowed_existing_run_ids={"run-base"},
            )
        receipt = recovery.preflight_evidence_recovery(
            self.root,
            **common,
            allowed_existing_run_ids={"run-base"},
            allowed_existing_evidence_ids={identity},
        )
        self.assertEqual(receipt["expected_allowlists"]["existing_run_ids"], ["run-base"])
        self.assertEqual(receipt["expected_allowlists"]["existing_evidence_ids"], [identity])

    def test_existing_run_identity_allowlist_rejects_wrong_logical_id(self) -> None:
        candidate, _identity = self._candidate_with_existing_run_evidence()
        current = recovery._snapshot(self.ledger_path, immutable=False)
        candidate_snapshot = recovery._snapshot(candidate, immutable=True)
        with self.assertRaisesRegex(recovery.LedgerEvidenceRecoveryError, "EXISTING_EVIDENCE_ID_NOT_ALLOWLISTED"):
            recovery.preflight_evidence_recovery(
                self.root,
                candidate=candidate,
                expected_current_sha256=current.physical_sha256,
                expected_current_logical_sha256=current.logical_sha256,
                expected_candidate_sha256=candidate_snapshot.physical_sha256,
                expected_candidate_logical_sha256=candidate_snapshot.logical_sha256,
                allowed_run_ids={RUN_ID},
                allowed_existing_run_ids={"run-base"},
                allowed_problem_ids={PROBLEM_ID},
                allowed_evidence_ids={"ack-recovered"},
                allowed_existing_evidence_ids={"continuity-wrong-id"},
            )


if __name__ == "__main__":
    unittest.main()
