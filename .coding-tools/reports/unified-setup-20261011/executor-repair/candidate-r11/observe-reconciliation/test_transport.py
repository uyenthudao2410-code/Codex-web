"""Offline exact transport tests; SSH mocked."""
import importlib.util
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("transport", HERE / "root-observe-ssh.py")
transport = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transport)


class TransportTests(unittest.TestCase):
    def test_pinned_frozen_stage_loaded(self):
        self.assertIn("os.execv", transport.frozen_ssh().INVOKE)

    def test_explicit_root_authority_required(self):
        with self.assertRaises(transport.Failure):
            transport.transport("stage", False)

    def test_uncertain_stage_has_once_only_intent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in transport.HELPERS:
                (root / name).write_bytes((HERE / name).read_bytes())
            pinned = transport.frozen_ssh()
            calls = []
            def uncertain(*args, **kwargs):
                calls.append(args)
                self.assertIsInstance(kwargs["input"], bytes)
                self.assertNotIn("shell", kwargs)
                self.assertTrue((root / "transport-intent-stage.json").exists())
                raise OSError("SHOULD_NOT_LEAK")
            with patch.object(transport, "HERE", root), patch.object(transport, "frozen_ssh", return_value=pinned), \
                 patch.object(transport.shutil, "which", return_value="ssh-mocked"), \
                 patch.object(transport.subprocess, "run", side_effect=uncertain):
                with self.assertRaises(transport.Failure) as first:
                    transport.transport("stage", True)
                self.assertEqual(first.exception.code, "SSH_TRANSPORT_UNCERTAIN_NO_RETRY")
                with self.assertRaises(transport.Failure) as second:
                    transport.transport("stage", True)
                self.assertEqual(second.exception.code, "IMMUTABLE_TRANSPORT_INTENT_EXISTS_NO_REPLAY")
            self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
