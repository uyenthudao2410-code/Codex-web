"""Offline transport tests; subprocess/SSH execution is always mocked."""
from __future__ import annotations
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("transport", HERE / "root-canary-ssh.py")
transport = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transport)


class OfflineTransportTests(unittest.TestCase):
    def test_frozen_root_ssh_is_loaded_by_exact_hash_only(self):
        module = transport.fixed_module("offline_pinned_ssh", transport.SERVER / "root-ssh.py", transport.SSH_HELPER_SHA)
        self.assertIn("sys.stdin.buffer.read", module.STAGE)
        self.assertIn("os.execv", module.INVOKE)
        with self.assertRaises(transport.Failure):
            transport.fixed_module("wrong", transport.SERVER / "root-ssh.py", "0" * 64)

    def test_private_json_or_output_rejected(self):
        for value in ({"authorization": "anything"}, {"nested": ["Bearer SHOULD_NOT_LEAK"]}, {"token": "anything"}):
            with self.assertRaises(transport.Failure):
                transport.reject_private(value)
        with self.assertRaises(transport.Failure):
            transport.receipts(b'{"phase":"observe","authorization":"private"}\n')

    def test_root_execute_and_owned_manifest_required(self):
        with self.assertRaises(transport.Failure) as error:
            transport.transport(types.SimpleNamespace(execute=False, manifest="anything"))
        self.assertEqual(error.exception.code, "ROOT_EXPLICIT_EXECUTION_AND_MANIFEST_REQUIRED")

    def test_immutable_local_intent_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "intent.json"
            transport.freeze(path, b"original")
            with self.assertRaises(transport.Failure) as error:
                transport.freeze(path, b"replacement")
            self.assertEqual(error.exception.code, "LOCAL_IMMUTABLE_ARTIFACT_ALREADY_EXISTS_NO_REPLAY")
            self.assertEqual(path.read_bytes(), b"original")

    def test_stage_sends_binary_once_and_uncertainty_preserves_intent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet_dir = root / "prepared-20261011T150000000000Z"
            packet_dir.mkdir()
            binary = b"binary-tar-fixture-not-a-shell-string"
            (packet_dir / "canary-bundle.tar").write_bytes(binary)
            manifest = {"bundle_sha256": transport.sha(binary), "bundle_size_bytes": len(binary),
                "native_preflight_observed_at_ms": 1000,
                "remote_dir": transport.REMOTE_PARENT + "/r11-approved-20261011T150000000000Z", "files": {}, "pins_sha256": "a" * 64}
            args = types.SimpleNamespace(execute=True, manifest="synthetic", action="stage")
            pinned = types.SimpleNamespace(STAGE="known-binary-stage-only")
            calls = []
            def uncertain(argv, **options):
                calls.append((argv, options))
                self.assertEqual(options["input"], binary)
                self.assertIsInstance(argv, list)
                self.assertNotIn("shell", options)
                self.assertTrue((packet_dir / "transport-intent-stage.json").exists())
                raise OSError("raw stderr secret must never print")
            with patch.object(transport, "HERE", root), patch.object(transport, "manifest_packet", return_value=(packet_dir, manifest)), \
                 patch.object(transport, "fixed_module", return_value=pinned), patch.object(transport.shutil, "which", return_value="ssh-mocked"), \
                 patch.object(transport.time, "time", return_value=1.001), patch.object(transport.subprocess, "run", side_effect=uncertain):
                with self.assertRaises(transport.Failure) as first:
                    transport.transport(args)
                self.assertEqual(first.exception.code, "SSH_TRANSPORT_UNCERTAIN_NO_RETRY")
                with self.assertRaises(transport.Failure) as second:
                    transport.transport(args)
                self.assertEqual(second.exception.code, "LOCAL_IMMUTABLE_ARTIFACT_ALREADY_EXISTS_NO_REPLAY")
            self.assertEqual(len(calls), 1)

    def test_observe_uses_same_fixed_pins_and_does_not_create_effect_intent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet_dir = root / "prepared-20261011T150000000000Z"
            packet_dir.mkdir()
            manifest = {"remote_dir": transport.REMOTE_PARENT + "/r11-approved-20261011T150000000000Z",
                        "files": {"pins.json": {"sha256": "a" * 64, "size_bytes": 10}}, "pins_sha256": "a" * 64}
            args = types.SimpleNamespace(execute=True, manifest="synthetic", action="observe")
            pinned = types.SimpleNamespace(INVOKE="known-fixed-hash-invoke")
            stdout = b'{"phase":"observe","ok":true,"family":{"action_id":"act_existing"},"remote_mutation":false}\n'
            result = types.SimpleNamespace(returncode=0, stdout=stdout, stderr=b"SHOULD_NOT_LEAK")
            with patch.object(transport, "HERE", root), patch.object(transport, "manifest_packet", return_value=(packet_dir, manifest)), \
                 patch.object(transport, "fixed_module", return_value=pinned), patch.object(transport.shutil, "which", return_value="ssh-mocked"), \
                 patch.object(transport.subprocess, "run", return_value=result) as mocked:
                public = transport.transport(args)
            self.assertFalse(public["remote_mutation"])
            self.assertFalse((packet_dir / "transport-intent-observe.json").exists())
            self.assertEqual(mocked.call_args.kwargs["input"], b"")
            self.assertIn("r11_mcp_canary.py", mocked.call_args.args[0][-1])
            self.assertNotIn("SHOULD_NOT_LEAK", json.dumps(public))
            self.assertFalse(public["stderr_disclosed"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
