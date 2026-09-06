from __future__ import annotations

import hashlib
import os
import sqlite3
import tempfile
import threading
import time
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

from coding_tools_mcp import ledger_maintenance as maintenance
from coding_tools_mcp.ledger_file_gate import LedgerGateTimeout, ledger_access_gate
from coding_tools_mcp.ledger_maintenance import compact_ledger, inspect_maintenance_readiness, post_restart_append_smoke
from coding_tools_mcp.orchestration_ledger import OrchestrationLedger


class LedgerMaintenanceTests(unittest.TestCase):
    @staticmethod
    def _file_sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()

    @staticmethod
    def _finished_ledger(root: Path) -> tuple[OrchestrationLedger, str, str]:
        ledger = OrchestrationLedger(root)
        run_id = ledger.create_run(objective="maintenance")
        wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
        ledger.finish_wave(wave_id, status="accepted")
        ledger.finish_run(run_id, status="accepted")
        return ledger, run_id, wave_id

    @staticmethod
    def _insert_blocker(path: Path, *, kind: str, run_id: str, wave_id: str) -> None:
        now_text = "2026-08-23T00:00:00+00:00"
        connection = sqlite3.connect(path)
        try:
            connection.execute("PRAGMA journal_mode=WAL")
            if kind == "controller":
                connection.execute(
                    """INSERT OR REPLACE INTO controller_leases(
                        run_id,fencing_token,lease_id,owner_client_id,status,expires_at,updated_at
                    ) VALUES(?,?,?,?,?,?,?)""",
                    (run_id, 1, "late-lease", "test", "active", time.time() + 60, now_text),
                )
            elif kind == "fence":
                connection.execute(
                    """INSERT OR REPLACE INTO write_fences(
                        scope_key,fencing_token,lease_id,owner,run_id,wave_id,status,expires_at,updated_at
                    ) VALUES(?,?,?,?,?,?,?,?,?)""",
                    ("late-fence", 1, "late-lease", "test", run_id, wave_id, "active", time.time() + 60, now_text),
                )
            elif kind == "job":
                connection.execute(
                    """INSERT INTO managed_process_jobs(
                        job_id,run_id,wave_id,command_id,owner,checkout_id,resource_class,
                        root_pid,root_process_token,process_instance_id,runtime_instance_id,
                        lifecycle_state,started_at,updated_at,finished_at,metadata_json
                    ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        "late-job", run_id, wave_id, "late-command", "test", "test-checkout", "MEDIUM",
                        0, "", "test-process", "test-runtime", "running", now_text, now_text, None, "{}",
                    ),
                )
            elif kind == "background":
                connection.execute(
                    """INSERT INTO background_operations(
                        operation_id,server_instance_id,tool,task_id,run_id,wave_id,status,
                        started_at,updated_at,finished_at,summary_json
                    ) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        "late-background", "test-server", "test", "", run_id, wave_id, "running",
                        now_text, now_text, None, "{}",
                    ),
                )
            else:
                raise AssertionError(f"unknown blocker kind: {kind}")
            connection.commit()
        finally:
            connection.close()

    def test_compaction_requires_explicit_stop_and_preserves_facts(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger, _, _ = self._finished_ledger(root)
            source = root / ".coding-tools" / "orchestration" / "ledger.sqlite3"
            connection = sqlite3.connect(source)
            try:
                connection.execute("CREATE TABLE maintenance_reclaimable_probe(payload BLOB)")
                connection.execute("INSERT INTO maintenance_reclaimable_probe(payload) VALUES(zeroblob(?))", (1024 * 1024,))
                connection.commit()
                connection.execute("DELETE FROM maintenance_reclaimable_probe")
                connection.commit()
            finally:
                connection.close()
            before = inspect_maintenance_readiness(root)
            self.assertTrue(before["compact_allowed"])
            with self.assertRaises(PermissionError):
                compact_ledger(root, expected_sha256=before["ledger_sha256"], runtime_stopped=False)

            events: list[tuple[str, str]] = []
            real_fsync = maintenance._fsync_file
            real_replace = os.replace
            real_directory_sync = maintenance._fsync_parent_directory

            def record_fsync(path: Path) -> None:
                events.append(("fsync", Path(path).name))
                real_fsync(path)

            def record_replace(source: str | bytes | os.PathLike[str] | os.PathLike[bytes], target: str | bytes | os.PathLike[str] | os.PathLike[bytes]) -> None:
                events.append(("replace", Path(source).name))
                real_replace(source, target)

            def record_directory_sync(path: Path) -> dict[str, object]:
                events.append(("dirsync", Path(path).parent.name))
                return real_directory_sync(path)

            with (
                mock.patch.object(maintenance, "_fsync_file", side_effect=record_fsync),
                mock.patch.object(maintenance.os, "replace", side_effect=record_replace),
                mock.patch.object(maintenance, "_fsync_parent_directory", side_effect=record_directory_sync),
            ):
                result = compact_ledger(root, expected_sha256=before["ledger_sha256"], runtime_stopped=True)
            self.assertTrue(result["replaced"])
            self.assertEqual(result["candidate_logical_sha256"], before["logical_sha256"])
            self.assertEqual(result["candidate_compaction"]["journal_mode"], "delete")
            self.assertGreater(result["candidate_compaction"]["saved_bytes"], 0)
            self.assertTrue(result["durability"]["candidate_fsync"])
            self.assertTrue(result["durability"]["replacement_fsync"])
            candidate_fsync = events.index(("fsync", "ledger.compact.sqlite3"))
            replace_index = next(index for index, item in enumerate(events) if item[0] == "replace")
            source_fsync = next(index for index, item in enumerate(events) if index > replace_index and item == ("fsync", "ledger.sqlite3"))
            directory_sync = next(index for index, item in enumerate(events) if item[0] == "dirsync")
            self.assertLess(candidate_fsync, replace_index)
            self.assertLess(replace_index, source_fsync)
            self.assertLess(source_fsync, directory_sync)
            after = inspect_maintenance_readiness(root)
            self.assertEqual(after["counts"], before["counts"])
            self.assertEqual(after["max_event_seq"], before["max_event_seq"])
            self.assertEqual(after["head_event_hash"], before["head_event_hash"])
            self.assertEqual(after["logical_sha256"], before["logical_sha256"])
            self.assertLess(after["size_bytes"], before["size_bytes"])
            with self.assertRaises(PermissionError):
                post_restart_append_smoke(root, explicitly_authorized=False)
            smoke = post_restart_append_smoke(root, explicitly_authorized=True)
            self.assertTrue(smoke["chain_valid"])

    def test_late_runtime_blockers_are_rechecked_under_exclusive_gate(self) -> None:
        cases = {
            "controller": "active_controller_leases",
            "fence": "active_write_fences",
            "job": "active_managed_jobs",
            "background": "active_background_operations",
        }
        for kind, blocker in cases.items():
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                _, run_id, wave_id = self._finished_ledger(root)
                before = inspect_maintenance_readiness(root)
                source = Path(before["ledger_path"])
                real_gate = maintenance.ledger_access_gate
                injected = False

                @contextmanager
                def late_gate(path: Path, *, exclusive: bool = False, timeout_seconds: float = 5.0):
                    nonlocal injected
                    if exclusive and not injected:
                        injected = True
                        self._insert_blocker(source, kind=kind, run_id=run_id, wave_id=wave_id)
                    with real_gate(path, exclusive=exclusive, timeout_seconds=timeout_seconds):
                        yield

                with (
                    mock.patch.object(maintenance, "ledger_access_gate", late_gate),
                    mock.patch.object(maintenance.os, "replace") as replace,
                ):
                    with self.assertRaisesRegex(RuntimeError, blocker):
                        compact_ledger(root, expected_sha256=before["ledger_sha256"], runtime_stopped=True)
                    replace.assert_not_called()
                after = inspect_maintenance_readiness(root)
                self.assertIn(blocker, after["blockers"])

    def test_late_committed_wal_write_is_detected_even_when_main_sha_is_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, run_id, _ = self._finished_ledger(root)
            before = inspect_maintenance_readiness(root)
            source = Path(before["ledger_path"])
            main_sha = before["ledger_sha256"]

            pinned_reader = sqlite3.connect(source)
            pinned_reader.execute("PRAGMA journal_mode=WAL")
            pinned_reader.execute("BEGIN")
            pinned_reader.execute("SELECT metadata_json FROM runs WHERE run_id=?", (run_id,)).fetchone()
            real_gate = maintenance.ledger_access_gate
            injected = False

            @contextmanager
            def late_gate(path: Path, *, exclusive: bool = False, timeout_seconds: float = 5.0):
                nonlocal injected
                if exclusive and not injected:
                    injected = True
                    writer = sqlite3.connect(source)
                    try:
                        writer.execute("PRAGMA wal_autocheckpoint=0")
                        writer.execute("UPDATE runs SET metadata_json=? WHERE run_id=?", ('{\"late_wal\":true}', run_id))
                        writer.commit()
                    finally:
                        writer.close()
                    self.assertEqual(self._file_sha256(source), main_sha)
                    self.assertGreater(Path(f"{source}-wal").stat().st_size, 0)
                with real_gate(path, exclusive=exclusive, timeout_seconds=timeout_seconds):
                    yield

            try:
                with (
                    mock.patch.object(maintenance, "ledger_access_gate", late_gate),
                    mock.patch.object(maintenance.os, "replace") as replace,
                ):
                    with self.assertRaisesRegex(RuntimeError, "logical source changed"):
                        compact_ledger(root, expected_sha256=main_sha, runtime_stopped=True)
                    replace.assert_not_called()
            finally:
                pinned_reader.rollback()
                pinned_reader.close()

            connection = sqlite3.connect(source)
            try:
                metadata = str(connection.execute("SELECT metadata_json FROM runs WHERE run_id=?", (run_id,)).fetchone()[0])
            finally:
                connection.close()
            self.assertIn("late_wal", metadata)

    def test_shared_gate_blocks_exclusive_maintenance_authority(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, _, _ = self._finished_ledger(root)
            source = Path(inspect_maintenance_readiness(root)["ledger_path"])
            failures: list[BaseException] = []

            def acquire_exclusive() -> None:
                try:
                    with ledger_access_gate(source, exclusive=True, timeout_seconds=0.05):
                        pass
                except BaseException as exc:  # deterministic assertion capture from worker thread
                    failures.append(exc)

            with ledger_access_gate(source, exclusive=False):
                worker = threading.Thread(target=acquire_exclusive)
                worker.start()
                worker.join(timeout=1.0)
                self.assertFalse(worker.is_alive())
            self.assertEqual(len(failures), 1)
            self.assertIsInstance(failures[0], LedgerGateTimeout)

    def test_candidate_fsync_failure_refuses_replace_and_preserves_logical_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, _, _ = self._finished_ledger(root)
            before = inspect_maintenance_readiness(root)
            with (
                mock.patch.object(maintenance, "_fsync_file", side_effect=OSError("fsync failed")),
                mock.patch.object(maintenance.os, "replace") as replace,
            ):
                with self.assertRaisesRegex(OSError, "fsync failed"):
                    compact_ledger(root, expected_sha256=before["ledger_sha256"], runtime_stopped=True)
                replace.assert_not_called()
            after = inspect_maintenance_readiness(root)
            self.assertEqual(after["logical_sha256"], before["logical_sha256"])
            self.assertEqual(after["counts"], before["counts"])
            self.assertEqual(after["head_event_hash"], before["head_event_hash"])


if __name__ == "__main__":
    unittest.main()
