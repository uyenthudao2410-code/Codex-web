from __future__ import annotations

import importlib.util
import os
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts/resource_hygiene.py"
SPEC = importlib.util.spec_from_file_location("resource_hygiene_script", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
resource_hygiene = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(resource_hygiene)


class ResourceHygieneScriptTests(unittest.TestCase):
    def test_snapshot_and_guarded_soft_cleanup_leave_primary_target_untouched(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repository"
            primary_incremental = root / "target/debug/incremental"
            primary_release = root / "target/release"
            primary_incremental.mkdir(parents=True)
            primary_release.mkdir(parents=True)
            (primary_incremental / "incremental.bin").write_bytes(b"1234")
            (primary_release / "release.bin").write_bytes(b"123")

            temporary_target = Path(temp) / "worktree/target"
            temporary_target.mkdir(parents=True)
            disposable = temporary_target / "old.bin"
            disposable.write_bytes(b"12345")
            old = time.time() - 10 * 3600
            os.utime(disposable, (old, old))
            os.utime(temporary_target, (old, old))
            state = Path(temp) / "hygiene-state.json"

            snapshot = resource_hygiene.disk_snapshot(
                root,
                [temporary_target],
                state_path=state,
            )
            self.assertEqual(snapshot["target_total_bytes"], 7)
            self.assertEqual(snapshot["debug_incremental_bytes"], 4)
            self.assertEqual(snapshot["release_artifact_bytes"], 3)
            self.assertEqual(snapshot["temporary_worktree_target_bytes"], 5)
            self.assertIsNone(snapshot["last_soft_cleanup_at"])

            result = resource_hygiene.soft_cleanup(
                root,
                [temporary_target],
                older_than_hours=1,
                state_path=state,
                process_observer=lambda _targets: {
                    "observed": True,
                    "active_build_process_count": 0,
                    "active_connector_reference_count": 0,
                },
            )
            self.assertEqual(result["bytes_removed"], 5)
            self.assertFalse(temporary_target.exists())
            self.assertTrue((primary_incremental / "incremental.bin").exists())
            self.assertFalse(result["hard_cleanup_performed"])
            self.assertIsNotNone(
                resource_hygiene.disk_snapshot(root, state_path=state)[
                    "last_soft_cleanup_at"
                ]
            )

            with self.assertRaises(resource_hygiene.HygieneError):
                resource_hygiene.soft_cleanup(
                    root,
                    [root / "target"],
                    older_than_hours=0,
                    state_path=state,
                )

            nested_primary = root / "target/cache/target"
            nested_primary.mkdir(parents=True)
            with self.assertRaises(resource_hygiene.HygieneError):
                resource_hygiene.soft_cleanup(
                    root,
                    [nested_primary],
                    older_than_hours=0,
                    state_path=state,
                )

            unobserved = Path(temp) / "unobserved/target"
            unobserved.mkdir(parents=True)
            with self.assertRaisesRegex(
                resource_hygiene.HygieneError,
                "process ownership is unavailable",
            ):
                resource_hygiene.soft_cleanup(
                    root,
                    [unobserved],
                    older_than_hours=0,
                    state_path=state,
                    process_observer=lambda _targets: {
                        "observed": False,
                        "active_build_process_count": 0,
                        "active_connector_reference_count": 0,
                    },
                )

    def test_active_heavy_claim_or_legacy_managed_owner_blocks_soft_cleanup(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repository"
            target = Path(temp) / "worktree/target"
            target.mkdir(parents=True)
            (target / "old.bin").write_bytes(b"x")
            ledger = root / ".coding-tools/orchestration/ledger.sqlite3"
            ledger.parent.mkdir(parents=True)
            with sqlite3.connect(ledger) as connection:
                connection.execute(
                    """CREATE TABLE managed_process_jobs(
                           resource_class TEXT NOT NULL,
                           lifecycle_state TEXT NOT NULL
                       )"""
                )
                connection.execute(
                    "INSERT INTO managed_process_jobs VALUES('HEAVY','running')"
                )
            connection.close()

            with self.assertRaisesRegex(
                resource_hygiene.HygieneError,
                "active HEAVY scheduling claim",
            ):
                resource_hygiene.soft_cleanup(
                    root,
                    [target],
                    older_than_hours=0,
                    process_observer=lambda _targets: {
                        "observed": True,
                        "active_build_process_count": 0,
                        "active_connector_reference_count": 0,
                    },
                )
            self.assertTrue(target.exists())


if __name__ == "__main__":
    unittest.main()
