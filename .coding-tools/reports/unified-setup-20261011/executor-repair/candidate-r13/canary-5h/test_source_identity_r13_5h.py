"""Source-observation bounds for the read-only derivative; no live effects."""
import importlib.util
import os
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("r13_5h_source_correlation", HERE / "correlate_r13_5h_source_identity.py")
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


class SourceIdentityTests(unittest.TestCase):
    def test_retained_evidence_excluded_before_bound_and_docs_remain_source(self):
        with tempfile.TemporaryDirectory(dir=HERE) as temp:
            root = Path(temp)
            self.assertEqual(root.resolve().parent, HERE.resolve())
            (root / "docs").mkdir()
            document = root / "docs/CURRENT_STATE.md"
            document.write_bytes(b"before")
            (root / ".coding-tools").mkdir()
            evidence = root / ".coding-tools/volatile.json"
            evidence.write_bytes(b"before")
            status_calls = []
            exclude = "top,exclude,icase" if os.name == "nt" else "top,exclude"
            def git(command, **_kwargs):
                args = command[4:]
                if args == ["rev-parse", "HEAD"]:
                    stdout = c.HEAD + "\n"
                elif args == ["branch", "--show-current"]:
                    stdout = "main\n"
                else:
                    status_calls.append(args)
                    self.assertEqual(args, ["status", "--porcelain=v1", "-z", "-b", "--untracked-files=all",
                        "--", ":(top)**", f":({exclude}).coding-tools", f":({exclude}).coding-tools/**"])
                    stdout = "## main\0 M docs/CURRENT_STATE.md\0"
                return types.SimpleNamespace(returncode=0, stdout=stdout.encode())
            with patch.object(c.subprocess, "run", side_effect=git):
                first = c.source_identity(root)
                evidence.write_bytes(b"after")
                self.assertEqual(c.source_identity(root), first)
                document.write_bytes(b"after")
                self.assertNotEqual(c.source_identity(root), first)
            self.assertEqual(len(status_calls), 3)

    def test_source_entry_bound_is_preserved(self):
        def git(command, **_kwargs):
            args = command[4:]
            if args == ["rev-parse", "HEAD"]:
                stdout = c.HEAD + "\n"
            elif args == ["branch", "--show-current"]:
                stdout = "main\n"
            else:
                stdout = "## main\0" + "".join(f"?? source/{index}.txt\0" for index in range(2001))
            return types.SimpleNamespace(returncode=0, stdout=stdout.encode())
        with patch.object(c.subprocess, "run", side_effect=git):
            with self.assertRaisesRegex(c.Rejected, "GIT_STATUS_EXCEEDS_RUNTIME_BOUND"):
                c.source_identity(HERE)


if __name__ == "__main__":
    unittest.main()
