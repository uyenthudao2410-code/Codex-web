from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from coding_tools_mcp.errors import ToolFailure
from coding_tools_mcp.git_tools import MAX_EXACT_STATUS_ENTRIES
from coding_tools_mcp.server import Runtime


@unittest.skipUnless(shutil.which("git"), "git is required")
class SourceWorktreeIdentityTests(unittest.TestCase):
    @staticmethod
    def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)

    def _repository(self, root: Path) -> Path:
        self._git(root, "init")
        source = root / "app.py"
        source.write_text("VALUE = 1\n", encoding="utf-8")
        self._git(root, "add", "app.py")
        self._git(root, "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                  "commit", "-m", "source fixture")
        return source

    def test_large_retained_evidence_does_not_bound_or_invalidate_source_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = self._repository(root)
            runtime = Runtime(root, permission_mode="safe")
            try:
                before = runtime._orchestration_workspace_identity(".")
                evidence_root = root / ".coding-tools" / "evidence"
                evidence_root.mkdir(parents=True, exist_ok=True)
                for index in range(MAX_EXACT_STATUS_ENTRIES + 1):
                    (evidence_root / f"entry-{index}.json").write_text("{}\n", encoding="utf-8")
                self._git(root, "add", ".coding-tools/evidence")
                tracked = self._git(root, "ls-files", ".coding-tools/evidence").stdout.splitlines()
                self.assertEqual(len(tracked), MAX_EXACT_STATUS_ENTRIES + 1)
                # Keep staged, modified, and untracked evidence visible to Git.
                (evidence_root / "entry-0.json").write_text('{"tick": 1}\n', encoding="utf-8")
                (evidence_root / "untracked.json").write_text("{}\n", encoding="utf-8")
                with self.assertRaises(ToolFailure) as full_status:
                    runtime.git_status({"path": ".", "max_entries": MAX_EXACT_STATUS_ENTRIES})
                self.assertEqual(full_status.exception.code, "WORKTREE_STATUS_TOO_LARGE")

                after = runtime._orchestration_workspace_identity(".")
                self.assertEqual(before["source_fingerprint"], after["source_fingerprint"])
                self.assertEqual(before["worktree_fp"], after["worktree_fp"])
                self.assertEqual(after["dirty_source_paths"], [])
                source.write_text("VALUE = 2\n", encoding="utf-8")
                changed = runtime._orchestration_workspace_identity(".")
                self.assertNotEqual(after["source_fingerprint"], changed["source_fingerprint"])
                self.assertEqual(changed["dirty_source_paths"], ["app.py"])
            finally:
                runtime.close()

    def test_genuine_source_status_keeps_exact_entry_bound(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._repository(root)
            source_root = root / "source"
            source_root.mkdir()
            for index in range(MAX_EXACT_STATUS_ENTRIES + 1):
                (source_root / f"entry-{index}.py").write_text("VALUE = 1\n", encoding="utf-8")
            runtime = Runtime(root, permission_mode="safe")
            try:
                with self.assertRaises(ToolFailure) as oversized:
                    runtime._orchestration_workspace_identity(".")
                self.assertEqual(oversized.exception.code, "WORKTREE_STATUS_TOO_LARGE")
                self.assertEqual(oversized.exception.details["observed_entries"], MAX_EXACT_STATUS_ENTRIES + 1)
            finally:
                runtime.close()

    def test_source_identity_from_subdirectory_keeps_repository_wide_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = self._repository(root)
            nested = root / "nested"
            nested.mkdir()
            runtime = Runtime(root, permission_mode="safe")
            try:
                before = runtime._orchestration_workspace_identity("nested")
                evidence_root = root / ".coding-tools" / "evidence"
                evidence_root.mkdir(parents=True, exist_ok=True)
                (evidence_root / "runtime.json").write_text("{}\n", encoding="utf-8")
                self.assertEqual(before["worktree_fp"], runtime._orchestration_workspace_identity("nested")["worktree_fp"])
                source.write_text("VALUE = 2\n", encoding="utf-8")
                after = runtime._orchestration_workspace_identity("nested")
                self.assertNotEqual(before["worktree_fp"], after["worktree_fp"])
                self.assertEqual(after["dirty_source_paths"], ["app.py"])
            finally:
                runtime.close()

    def test_staged_renames_across_evidence_boundary_keep_source_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._repository(root)
            evidence = root / ".coding-tools" / "evidence"
            evidence.mkdir(parents=True)
            (evidence / "seed.py").write_text("OTHER = 1\n", encoding="utf-8")
            self._git(root, "add", ".coding-tools/evidence/seed.py")
            self._git(root, "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                      "commit", "-m", "retained evidence fixture")
            runtime = Runtime(root, permission_mode="safe")
            try:
                before = runtime._orchestration_workspace_identity(".")
                self._git(root, "mv", "app.py", ".coding-tools/evidence/moved-source.py")
                self._git(root, "mv", ".coding-tools/evidence/seed.py", "restored.py")
                after = runtime._orchestration_workspace_identity(".")
                self.assertNotEqual(before["source_fingerprint"], after["source_fingerprint"])
                self.assertEqual(after["dirty_source_paths"], ["app.py", "restored.py"])
                status = runtime.git_status({"path": "."}, source_identity_only=True)
                self.assertEqual({item["path"]: item["index_status"] for item in status["entries"]},
                                 {"app.py": "D", "restored.py": "A"})
            finally:
                runtime.close()


if __name__ == "__main__":
    unittest.main()
