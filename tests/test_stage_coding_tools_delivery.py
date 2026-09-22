from __future__ import annotations

import shutil
import sqlite3
import subprocess
import tempfile
import unittest
import hashlib
import json
from contextlib import closing
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_STAGE_SCRIPT = REPO_ROOT / "scripts" / "stage-coding-tools-delivery.py"
SOURCE_GUARD_SCRIPT = REPO_ROOT / "scripts" / "check-coding-tools-history.js"
LEDGER_REL = ".coding-tools/orchestration/ledger.sqlite3"
RECEIPT_REL = ".coding-tools/delivery-snapshot.json"


class CodingToolsDeliveryStageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="coding-tools-delivery-test-")
        self.root = Path(self.temp.name)
        self.run_cmd("git", "init", "-q")
        self.run_cmd("git", "config", "user.email", "test@example.com")
        self.run_cmd("git", "config", "user.name", "Test User")
        (self.root / "scripts").mkdir(parents=True)
        shutil.copy2(SOURCE_STAGE_SCRIPT, self.root / "scripts" / SOURCE_STAGE_SCRIPT.name)
        shutil.copy2(REPO_ROOT / 'scripts' / 'ledger-delivery-history.py', self.root / 'scripts' / 'ledger-delivery-history.py')
        shutil.copy2(SOURCE_GUARD_SCRIPT, self.root / "scripts" / SOURCE_GUARD_SCRIPT.name)
        shutil.copy2(REPO_ROOT / 'scripts' / 'run-python.js', self.root / 'scripts' / 'run-python.js')
        (self.root / ".gitignore").write_text(
            ".coding-tools/orchestration/ledger.sqlite3-shm\n"
            ".coding-tools/orchestration/ledger.sqlite3-wal\n",
            encoding="utf-8",
        )
        ledger = self.root / LEDGER_REL
        ledger.parent.mkdir(parents=True)
        connection = sqlite3.connect(ledger)
        try:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("CREATE TABLE events(seq INTEGER PRIMARY KEY, value TEXT NOT NULL)")
            connection.execute("INSERT INTO events(value) VALUES('initial')")
            connection.commit()
        finally:
            connection.close()
        self.run_cmd("git", "add", ".gitignore", "scripts", LEDGER_REL)
        self.run_cmd("git", "commit", "-qm", "initial")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_cmd(self, *args: str, check: bool = True) -> subprocess.CompletedProcess:
        result = subprocess.run(
            args,
            cwd=self.root,
            check=False,
            capture_output=True,
            text=True,
        )
        if check and result.returncode:
            raise RuntimeError(f'fixture command failed: {args}\n{result.stdout}\n{result.stderr}')
        return result

    def open_writer(self) -> sqlite3.Connection:
        writer = sqlite3.connect(self.root / LEDGER_REL, timeout=10.0)
        writer.execute("PRAGMA journal_mode=WAL")
        return writer

    def staged_ledger_copy(self) -> Path:
        data = subprocess.run(
            ["git", "show", f":{LEDGER_REL}"],
            cwd=self.root,
            check=True,
            capture_output=True,
        ).stdout
        target = self.root / "staged-ledger.sqlite3"
        target.write_bytes(data)
        return target

    def test_stages_consistent_snapshot_and_guard_accepts_live_drift(self) -> None:
        writer = self.open_writer()
        try:
            writer.execute("INSERT INTO events(value) VALUES('before-stage')")
            writer.commit()
            result = self.run_cmd("python", "scripts/stage-coding-tools-delivery.py")
            self.assertIn("delivery stage: PASS", result.stdout)

            staged = self.staged_ledger_copy()
            connection = sqlite3.connect(staged)
            try:
                self.assertEqual(connection.execute("PRAGMA integrity_check").fetchone()[0], "ok")
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM events").fetchone()[0], 2)
            finally:
                connection.close()

            writer.execute("INSERT INTO events(value) VALUES('after-stage')")
            writer.commit()
            guard = self.run_cmd("node", "scripts/check-coding-tools-history.js", "--require-staged")
            self.assertIn("coding-tools delivery check: PASS", guard.stdout)
            tracked = self.run_cmd(
                "git",
                "ls-files",
                "--",
                ".coding-tools/orchestration/ledger.sqlite3-shm",
                ".coding-tools/orchestration/ledger.sqlite3-wal",
            ).stdout
            self.assertEqual(tracked, "")
        finally:
            writer.close()

    def test_fresh_receipt_allows_live_drift_when_ledger_snapshot_matches_head(self) -> None:
        writer = self.open_writer()
        try:
            first = self.run_cmd("python", "scripts/stage-coding-tools-delivery.py")
            self.assertIn("delivery stage: PASS", first.stdout)
            self.run_cmd("git", "commit", "-qm", "snapshot baseline")

            result = self.run_cmd("python", "scripts/stage-coding-tools-delivery.py")
            self.assertIn("delivery stage: PASS", result.stdout)
            staged_ledger = self.run_cmd("git", "diff", "--cached", "--name-only", "--", LEDGER_REL).stdout
            self.assertEqual(staged_ledger, "")
            staged_receipt = self.run_cmd("git", "diff", "--cached", "--name-only", "--", RECEIPT_REL).stdout
            self.assertEqual(staged_receipt.strip(), RECEIPT_REL)

            writer.execute("INSERT INTO events(value) VALUES('after-equal-snapshot')")
            writer.commit()
            guard = self.run_cmd("node", "scripts/check-coding-tools-history.js", "--require-staged")
            self.assertIn("coding-tools delivery check: PASS", guard.stdout)
        finally:
            writer.close()

    def test_guard_still_rejects_other_unstaged_evidence(self) -> None:
        self.run_cmd("python", "scripts/stage-coding-tools-delivery.py")
        extra = self.root / ".coding-tools" / "unstaged.json"
        extra.write_text('{"state":"new"}\n', encoding="utf-8")
        guard = self.run_cmd("node", "scripts/check-coding-tools-history.js", "--require-staged", check=False)
        self.assertNotEqual(guard.returncode, 0)
        self.assertIn(".coding-tools/unstaged.json", guard.stderr)

    def test_verify_index_rejects_corrupt_staged_ledger(self) -> None:
        self.run_cmd("python", "scripts/stage-coding-tools-delivery.py")
        bad = self.root / "bad-ledger.bin"
        bad.write_bytes(b"not-a-sqlite-database")
        blob = self.run_cmd("git", "hash-object", "-w", "--", str(bad)).stdout.strip()
        self.run_cmd(
            "git",
            "update-index",
            "--add",
            "--cacheinfo",
            f"100644,{blob},{LEDGER_REL}",
        )
        result = self.run_cmd("python", "scripts/stage-coding-tools-delivery.py", "--verify-index", check=False)
        self.assertNotEqual(result.returncode, 0)

    def test_fresh_checksum_cannot_hide_deleted_or_changed_history(self) -> None:
        for sql in ["DELETE FROM events", "UPDATE events SET value='rewritten'"]:
            with self.subTest(sql=sql):
                with closing(self.open_writer()) as writer:
                    writer.execute(sql)
                    writer.commit()
                result = self.run_cmd('python', 'scripts/stage-coding-tools-delivery.py', check=False)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('LEDGER_HISTORY_NOT_PRESERVED', result.stderr)
                with closing(self.open_writer()) as writer:
                    writer.execute('DELETE FROM events')
                    writer.execute("INSERT INTO events(seq,value) VALUES(1,'initial')")
                    writer.commit()

    def test_pending_merge_cannot_drop_other_parent_tail(self) -> None:
        base = self.run_cmd('git', 'rev-parse', 'HEAD').stdout.strip()
        with closing(self.open_writer()) as writer:
            writer.execute("INSERT INTO events(value) VALUES('other-parent-event')")
            writer.commit()
        self.run_cmd('python', 'scripts/stage-coding-tools-delivery.py')
        self.run_cmd('git', 'commit', '-qm', 'other parent')
        other = self.run_cmd('git', 'rev-parse', 'HEAD').stdout.strip()
        # The snapshot has a different SQLite header from the closed WAL writer.
        # Align only this disposable fixture with its own committed blob.
        committed = subprocess.run(['git', 'show', f'HEAD:{LEDGER_REL}'], cwd=self.root,
                                   check=True, capture_output=True).stdout
        (self.root / LEDGER_REL).write_bytes(committed)
        self.run_cmd('git', 'checkout', '-q', '-b', 'candidate', base)
        # Simulate a merge resolution retaining only the first parent's DB.
        (self.root / '.git' / 'MERGE_HEAD').write_text(other + '\n', encoding='ascii')
        result = self.run_cmd('python', 'scripts/stage-coding-tools-delivery.py', check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('LEDGER_HISTORY_NOT_PRESERVED', result.stderr)

    def test_archived_history_counts_only_with_valid_staged_manifest(self) -> None:
        archive_dir = self.root / '.coding-tools/orchestration/archives'
        archive_dir.mkdir()
        with closing(self.open_writer()) as writer:
            writer.execute('CREATE TABLE runs(run_id TEXT PRIMARY KEY)')
            writer.execute("INSERT INTO runs VALUES('run-one')")
            writer.commit()
        self.run_cmd('python', 'scripts/stage-coding-tools-delivery.py')
        self.run_cmd('git', 'commit', '-qm', 'run baseline')
        raw = subprocess.run(['git', 'show', f'HEAD:{LEDGER_REL}'], cwd=self.root,
                             check=True, capture_output=True).stdout
        (archive_dir / 'shard.sqlite3').write_bytes(raw)
        entry = {'file': 'shard.sqlite3', 'sha256': hashlib.sha256(raw).hexdigest(),
                 'size_bytes': len(raw), 'run_ids': ['run-one'], 'run_count': 1}
        manifest = archive_dir / 'manifest.json'
        manifest.write_text(json.dumps({'schema_version': 1, 'archives': [entry]}))
        with closing(self.open_writer()) as writer:
            writer.execute('DELETE FROM events')
            writer.execute('DELETE FROM runs')
            writer.commit()
        self.assertIn('PASS', self.run_cmd('python', 'scripts/stage-coding-tools-delivery.py').stdout)
        entry['sha256'] = '0' * 64
        manifest.write_text(json.dumps({'schema_version': 1, 'archives': [entry]}))
        result = self.run_cmd('python', 'scripts/stage-coding-tools-delivery.py', check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('LEDGER_HISTORY_ARCHIVE_HASH_MISMATCH', result.stderr)


if __name__ == "__main__":
    unittest.main()
