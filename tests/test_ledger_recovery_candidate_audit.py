import importlib.util
import sqlite3
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "resources" / "coding-tools-mcp"
sys.path.insert(0, str(PACKAGE))


def load_script(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rehearsal = load_script("rehearsal_for_candidate_audit", ROOT / "scripts" / "rehearse-ledger-recovery.py")
audit = load_script("audit_candidate", ROOT / "scripts" / "audit-ledger-recovery-candidate.py")

from coding_tools_mcp.orchestration_ledger import OrchestrationLedger  # noqa: E402


class RecoveryCandidateAuditTests(unittest.TestCase):
    def test_projection_plan_is_pointer_only_and_read_only(self):
        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row
        connection.executescript(
            """
            CREATE TABLE problem_threads (
                problem_id TEXT PRIMARY KEY,
                current_revision INTEGER NOT NULL,
                resolution_state TEXT NOT NULL,
                latest_problem_event_seq INTEGER NOT NULL,
                latest_problem_event_hash TEXT NOT NULL
            );
            CREATE TABLE problem_events (
                problem_id TEXT NOT NULL,
                seq INTEGER PRIMARY KEY,
                problem_revision INTEGER NOT NULL,
                relation_type TEXT NOT NULL,
                link_status TEXT NOT NULL,
                link_role TEXT NOT NULL,
                state_before TEXT NOT NULL,
                state_after TEXT NOT NULL,
                event_id TEXT NOT NULL,
                event_hash TEXT NOT NULL,
                prev_hash TEXT NOT NULL
            );
            """
        )
        connection.execute(
            "INSERT INTO problem_threads VALUES(?,?,?,?,?)",
            ("prl-test", 1, "OPEN", 1, "h1"),
        )
        connection.executemany(
            "INSERT INTO problem_events VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            [
                ("prl-test", 1, 1, "ENGINEERING_ATTEMPT_BOUND", "EXACT", "PRIMARY", "OPEN", "OPEN", "e1", "h1", ""),
                ("prl-test", 2, 1, "ENGINEERING_ATTEMPT_BOUND", "EXACT", "PRIMARY", "OPEN", "OPEN", "e2", "h2", "h1"),
                ("prl-test", 3, 1, "ENGINEERING_ATTEMPT_BOUND", "EXACT", "PRIMARY", "OPEN", "OPEN", "e3", "h3", "h2"),
            ],
        )
        before = connection.execute("SELECT * FROM problem_threads").fetchall()
        plan = audit._problem_projection_reconciliation_plan(connection)
        after = connection.execute("SELECT * FROM problem_threads").fetchall()
        self.assertTrue(plan["valid"])
        self.assertFalse(plan["can_apply"])
        self.assertEqual(plan["plans"][0]["classification"], "POINTER_ONLY_SAFE")
        self.assertEqual(plan["plans"][0]["current_pointer_seq"], 1)
        self.assertEqual(plan["plans"][0]["proposed_pointer_seq"], 3)
        self.assertEqual([item["seq"] for item in plan["plans"][0]["tail_events"]], [2, 3])
        self.assertEqual([tuple(row) for row in before], [tuple(row) for row in after])
        connection.close()

    def test_projection_apply_probe_is_clone_only(self):
        with tempfile.TemporaryDirectory(prefix="projection-probe-test-") as temp:
            candidate = Path(temp) / "candidate.sqlite3"
            connection = sqlite3.connect(candidate)
            connection.executescript(
                """
                CREATE TABLE problem_threads (
                    problem_id TEXT PRIMARY KEY,
                    current_revision INTEGER NOT NULL,
                    resolution_state TEXT NOT NULL,
                    latest_problem_event_seq INTEGER NOT NULL,
                    latest_problem_event_hash TEXT NOT NULL
                );
                CREATE TABLE problem_events (
                    problem_id TEXT NOT NULL,
                    seq INTEGER PRIMARY KEY,
                    problem_revision INTEGER NOT NULL,
                    relation_type TEXT NOT NULL,
                    link_status TEXT NOT NULL,
                    link_role TEXT NOT NULL,
                    state_before TEXT NOT NULL,
                    state_after TEXT NOT NULL,
                    event_id TEXT NOT NULL,
                    event_hash TEXT NOT NULL,
                    prev_hash TEXT NOT NULL
                );
                INSERT INTO problem_threads VALUES('prl-test',1,'OPEN',1,'h1');
                INSERT INTO problem_events VALUES('prl-test',1,1,'ENGINEERING_ATTEMPT_BOUND','EXACT','PRIMARY','OPEN','OPEN','e1','h1','');
                INSERT INTO problem_events VALUES('prl-test',2,1,'ENGINEERING_ATTEMPT_BOUND','EXACT','PRIMARY','OPEN','OPEN','e2','h2','h1');
                """
            )
            connection.commit()
            connection.close()
            before = audit.sha(candidate)
            result = audit._isolated_projection_reconciliation_probe(candidate)
            self.assertTrue(result["clone_only"])
            self.assertTrue(result["valid"])
            self.assertTrue(result["projection_valid_after"])
            self.assertEqual(result["applied_pointer_count"], 1)
            self.assertEqual(audit.sha(candidate), before)

    def test_clone_append_and_duplicate_probes_are_isolated(self):
        with tempfile.TemporaryDirectory(prefix="candidate-audit-test-") as temp:
            root = Path(temp)
            current_root = root / "current"
            historical_root = root / "historical"
            current_ledger = OrchestrationLedger(current_root)
            current_run = current_ledger.create_run(objective="current")
            current_wave = current_ledger.create_wave(current_run, execution_mode="mcp_only")
            current_ledger.append_event(current_run, wave_id=current_wave, event_type="current_event")

            current_path = current_root / ".coding-tools" / "orchestration" / "ledger.sqlite3"
            historical_root.mkdir()
            historical_path = historical_root / ".coding-tools" / "orchestration" / "ledger.sqlite3"
            historical_path.parent.mkdir(parents=True)
            shutil.copyfile(current_path, historical_path)
            historical_ledger = OrchestrationLedger(historical_root)
            recovered_run = historical_ledger.create_run(objective="historical")
            recovered_wave = historical_ledger.create_wave(recovered_run, execution_mode="mcp_only")
            historical_ledger.append_event(recovered_run, wave_id=recovered_wave, event_type="historical_event")

            candidate_path = root / "candidate.sqlite3"
            rehearsal_result = rehearsal.rehearse(current_path, historical_path, candidate_path, {recovered_run})
            self.assertFalse(rehearsal_result["activation_eligible"])
            before_current = rehearsal.sha(current_path)
            before_candidate = rehearsal.sha(candidate_path)
            result = audit.audit(
                current_path,
                candidate_path,
                historical_path,
                {recovered_run},
                {
                    "current": before_current,
                    "candidate": before_candidate,
                    "historical": rehearsal.sha(historical_path),
                },
            )
            self.assertTrue(result["current_rows_preserved"])
            self.assertTrue(result["authority_preserved"])
            self.assertTrue(result["event_chains"]["candidate"]["valid"])
            self.assertTrue(result["append_duplicate_authority_probe"]["valid"])
            self.assertEqual(rehearsal.sha(current_path), before_current)
            self.assertEqual(rehearsal.sha(candidate_path), before_candidate)
            self.assertFalse(result["activation_eligible"])


if __name__ == "__main__":
    unittest.main()
