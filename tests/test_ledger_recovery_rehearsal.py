import importlib.util
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

spec = importlib.util.spec_from_file_location('rehearsal', Path(__file__).resolve().parents[1] / 'scripts/rehearse-ledger-recovery.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class RecoveryRehearsalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='ledger-rehearsal-test-')
        self.root = Path(self.temp.name)
        self.current = self.root / 'current.sqlite3'
        self.old = self.root / 'old.sqlite3'
        self.candidate = self.root / 'candidate.sqlite3'
        for file in [self.current, self.old]:
            with closing(sqlite3.connect(file)) as c:
                c.executescript('''CREATE TABLE runs(run_id TEXT PRIMARY KEY,status TEXT);
                    CREATE TABLE events(event_id TEXT PRIMARY KEY,run_id TEXT REFERENCES runs(run_id),payload TEXT);
                    CREATE TABLE hub_clients(client_id TEXT PRIMARY KEY,observed TEXT);
                    CREATE TABLE controller_leases(run_id TEXT PRIMARY KEY,status TEXT);
                    CREATE TABLE idempotency_records(idempotency_key TEXT PRIMARY KEY,status TEXT);
                    INSERT INTO runs VALUES('shared','active');
                    INSERT INTO events VALUES('shared-event','shared','immutable');''')
                c.execute('INSERT INTO hub_clients VALUES(?,?)', ('client', 'new' if file == self.current else 'old'))
                c.commit()
        with closing(sqlite3.connect(self.old)) as c:
            c.execute("INSERT INTO runs VALUES('recovered','accepted')")
            c.execute("INSERT INTO events VALUES('recovered-event','recovered','historical')")
            c.execute("INSERT INTO controller_leases VALUES('recovered','active')")
            c.execute("INSERT INTO idempotency_records VALUES('unknown-effect','unknown')")
            c.commit()

    def tearDown(self):
        self.temp.cleanup()

    def test_recovers_evidence_but_preserves_current_state_and_unknown_effect(self):
        before = module.sha(self.current)
        r = module.rehearse(self.current, self.old, self.candidate, {'recovered'})
        self.assertFalse(r['activation_eligible'])
        self.assertTrue(r['existing_rows_preserved'])
        self.assertEqual(module.sha(self.current), before)
        with closing(module.ro(self.candidate)) as c:
            self.assertEqual(c.execute('SELECT count(*) FROM events').fetchone()[0], 2)
            self.assertEqual(c.execute('SELECT observed FROM hub_clients').fetchone()[0], 'new')
            self.assertEqual(c.execute('SELECT count(*) FROM controller_leases').fetchone()[0], 0)
            self.assertEqual(c.execute('SELECT status FROM idempotency_records').fetchone()[0], 'unknown')

    def test_immutable_conflict_rolls_back_candidate(self):
        with closing(sqlite3.connect(self.old)) as c:
            c.execute("UPDATE events SET payload='tampered' WHERE event_id='shared-event'")
            c.commit()
        with self.assertRaisesRegex(RuntimeError, 'IMMUTABLE_CONFLICT'):
            module.rehearse(self.current, self.old, self.candidate, {'recovered'})
        with closing(module.ro(self.candidate)) as c:
            self.assertEqual(c.execute('SELECT count(*) FROM events').fetchone()[0], 1)

    def test_wrong_allowlist_and_overwrite_refused(self):
        with self.assertRaisesRegex(RuntimeError, 'ALLOWLIST'):
            module.rehearse(self.current, self.old, self.candidate, {'wrong'})
        self.assertFalse(self.candidate.exists())
        with self.assertRaisesRegex(RuntimeError, 'NEW_ISOLATED'):
            module.rehearse(self.current, self.old, self.current, {'recovered'})

    def test_withheld_authority_cannot_be_imported_via_foreign_key_dependency(self):
        for file in [self.current, self.old]:
            with closing(sqlite3.connect(file)) as c:
                c.execute('CREATE TABLE receipts(id TEXT PRIMARY KEY,owner TEXT REFERENCES controller_leases(run_id))')
                if file == self.old:
                    c.execute("INSERT INTO receipts VALUES('receipt','recovered')")
                c.commit()
        with self.assertRaisesRegex(RuntimeError, 'FOREIGN_KEY_CONFLICT'):
            module.rehearse(self.current, self.old, self.candidate, {'recovered'})


if __name__ == '__main__':
    unittest.main()
