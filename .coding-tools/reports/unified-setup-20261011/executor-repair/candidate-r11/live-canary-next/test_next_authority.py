"""Offline derivative guards; no real network, services, authority or runtime."""
from __future__ import annotations

import ast
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


canary = module("next_authority_canary", HERE / "r11_mcp_canary.py")
transport = module("next_authority_transport", HERE / "root-canary-ssh.py")


class NextAuthorityTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.prior_path = self.root / "old" / "authority-renewal-public.json"
        self.prior_path.parent.mkdir()
        self.common = types.SimpleNamespace(BINDING="binding", DEVICE="device", WORKSPACE="workspace",
            GENERATION="generation", LOCAL_ROOT=r"E:\Github\Tools-Codex-web", LOCAL_PROFILE="web-mcp-assistant",
            REVISION="revision", MARKER=self.prior_path)
        self.prior = {"operation": "owner_approved_r11_initial_verification_60m", "phase": "authority_renewed",
            "requested_at_ms": 1791730996302, "expires_at_ms": 1791734596302,
            "binding_id": self.common.BINDING, "root": self.common.LOCAL_ROOT, "profile": self.common.LOCAL_PROFILE}
        self.prior_raw = canary.canonical(self.prior)
        self.prior_path.write_bytes(self.prior_raw)
        self.pins = {"requested_at_ms": canary.NEXT_REQUESTED_AT_MS, "expires_at_ms": canary.NEXT_EXPIRES_AT_MS,
            "context_id": canary.NEXT_CONTEXT_ID, "pilot_id": canary.NEXT_PILOT_ID,
            "service_instance_id": "service", "activation_epoch": "epoch", "runtime_instance_id": "runtime",
            "mcp_server_instance_id": "native-server", "native_tool_contract_sha256": canary.NATIVE_TOOL_SHA256,
            "contract_version": "sha256:" + canary.NATIVE_TOOL_SHA256, "native_preflight": {}}
        self.next = {"phase": "intake_reopened", "operation": canary.NEXT_OPERATION,
            "binding_id": self.common.BINDING, "device_id": self.common.DEVICE,
            "workspace_id": self.common.WORKSPACE, "workspace_generation": self.common.GENERATION,
            "root": self.common.LOCAL_ROOT, "profile": self.common.LOCAL_PROFILE, "source_revision": self.common.REVISION,
            "approval_id": "call_flEpmLChKJPZsbnlAAXR5byS", "approved_duration_ms": 3600000,
            "prior_marker_sha256": canary.sha(self.prior_raw),
            **{key: self.pins[key] for key in ("requested_at_ms", "expires_at_ms", "context_id", "pilot_id", "service_instance_id")}}
        self.addCleanup(setattr, canary, "_prior_marker_path", None)
        self.addCleanup(setattr, canary, "_prior_marker_sha256", None)

    def read(self, path):
        if path == canary.HERE / "pins.json":
            return copy.deepcopy(self.pins)
        if path == canary.NEXT_AUTHORITY_MARKER:
            return copy.deepcopy(self.next)
        if path == self.prior_path:
            return json.loads(self.prior_path.read_bytes())
        self.fail("unexpected private input path")

    def consume(self):
        with patch.object(canary, "private_json", side_effect=self.read):
            return canary.pins_input(self.common)

    def assert_denial(self, code):
        with self.assertRaises(canary.Failure) as error:
            self.consume()
        self.assertEqual(error.exception.code, code)

    def test_new_marker_without_native_identity_fields_uses_actual_pins(self):
        self.assertEqual(self.consume(), self.pins)
        self.assertEqual(canary._prior_marker_sha256, canary.sha(self.prior_raw))
        for field in ("activation_epoch", "runtime_instance_id", "mcp_server_instance_id", "contract_version"):
            self.assertNotIn(field, self.next)
        self.assertEqual(self.prior_path.read_bytes(), self.prior_raw)

    def test_old_marker_cannot_be_used_as_new_marker(self):
        self.next = {**self.prior, "phase": "intake_reopened"}
        self.assert_denial("NEXT_AUTHORITY_SCOPE_OR_APPROVAL_CHANGED")

    def test_unopened_new_marker_refused(self):
        self.next["phase"] = "authority_renewed"
        self.assert_denial("AUTHORITY_NOT_REOPENED")

    def test_wrong_operation_target_or_approval_refused(self):
        original = copy.deepcopy(self.next)
        for key, value in (("operation", "old-operation"), ("root", r"E:\other"),
                           ("binding_id", "other-binding"), ("profile", "other-profile"),
                           ("approval_id", "other-approval"), ("approved_duration_ms", 7200000)):
            self.next = {**original, key: value}
            self.assert_denial("NEXT_AUTHORITY_SCOPE_OR_APPROVAL_CHANGED")

    def test_wrong_context_pilot_or_window_refused(self):
        original = copy.deepcopy(self.next)
        for key, value in (("context_id", "old-context"), ("pilot_id", "old-pilot"),
                           ("requested_at_ms", 1791730996302), ("expires_at_ms", 1791734596302)):
            self.next = {**original, key: value}
            self.assert_denial("EXACT_NEXT_AUTHORITY_WINDOW_REQUIRED")

    def test_exact_marker_must_agree_with_supplied_pins(self):
        self.pins["context_id"] = "old-context"
        self.assert_denial("AUTHORITY_PIN_MISMATCH")

    def test_prior_marker_changed_before_pins_is_refused(self):
        self.prior_path.write_bytes(self.prior_raw + b"\n")
        self.assert_denial("PREVIOUS_AUTHORITY_MARKER_CHANGED")

    def test_prior_phase_and_expiry_are_pinned(self):
        for key, value in (("phase", "intake_reopened"), ("expires_at_ms", 1791734596303)):
            prior = {**self.prior, key: value}
            raw = canary.canonical(prior)
            self.prior_path.write_bytes(raw)
            self.next["prior_marker_sha256"] = canary.sha(raw)
            self.assert_denial("PREVIOUS_AUTHORITY_MARKER_CHANGED")

    def test_pins_and_new_once_only_intent_preserve_old_bytes(self):
        self.consume()
        newdir = self.root / "new"
        newdir.mkdir()
        with patch.object(canary, "NEXT_OPERATION_DIR", newdir):
            canary.exclusive(canary.NEXT_OPERATION_DIR / "canary-dispatch.json", {"pins_sha256": canary.digest(self.pins)})
        self.assertEqual(self.prior_path.read_bytes(), self.prior_raw)
        self.assertTrue((newdir / "canary-dispatch.json").is_file())

    def test_old_marker_postcondition_checked_after_success_or_failure(self):
        self.consume()
        with patch.object(canary, "main", return_value={"phase": "synthetic"}):
            self.assertEqual(canary.run_guarded(), {"phase": "synthetic"})
        self.prior_path.write_bytes(self.prior_raw + b"\n")
        for outcome in (None, canary.Failure("SYNTHETIC_FAILURE")):
            with patch.object(canary, "main", return_value={"phase": "synthetic"}, side_effect=outcome):
                with self.assertRaises(canary.Failure) as error:
                    canary.run_guarded()
                self.assertEqual(error.exception.code, "PREVIOUS_AUTHORITY_MARKER_CHANGED_DURING_TRIAL")

    def test_no_common_operation_directory_writes_or_remapping(self):
        tree = ast.parse((HERE / "r11_mcp_canary.py").read_bytes())
        attrs = [node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)
                 and isinstance(node.value, ast.Name) and node.value.id == "common"]
        self.assertNotIn("OPERATION_DIR", attrs)
        common_assignments = [node for node in ast.walk(tree) if isinstance(node, (ast.Assign, ast.AnnAssign))
            for target in (node.targets if isinstance(node, ast.Assign) else [node.target])
            if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "common"]
        self.assertEqual(common_assignments, [])

    def test_frozen_originals_and_common_constants_unchanged(self):
        hashes = {"live-canary/r11_mcp_canary.py": "110b0a648c831312e01294c74d8acc260c6ad89374880ec2bdd77036971c4f75",
            "live-canary/root-canary-ssh.py": "c8c47308e8cfdc0bf1153875d93e4dff60a53fee995ea5fb21aed53686e40d87",
            "activation-server/r11_common.py": canary.COMMON_SHA256}
        for relative, expected in hashes.items():
            self.assertEqual(canary.sha((HERE.parent / relative).read_bytes()), expected)
        common_source = ast.parse((HERE.parent / "activation-server/r11_common.py").read_bytes())
        constants = {node.targets[0].id: node.value for node in common_source.body
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)}
        self.assertIn("r11-initial-verification-60m", ast.unparse(constants["OPERATION_DIR"]))
        self.assertNotIn("next", ast.unparse(constants["OPERATION_DIR"]))
        self.assertEqual(canary.NEXT_AUTHORITY_MARKER.name, "authority-renewal-public.json")

    def test_transport_refuses_old_window_before_staging(self):
        proof = {"observed_at_ms": 1791731000000, "no_active_jobs": True}
        native_raw = transport.canonical(proof)
        pins = {**self.pins, "requested_at_ms": 1791730996302, "expires_at_ms": 1791734596302,
            "context_id": "old-context", "pilot_id": "old-pilot", "native_preflight": {**proof, "receipt_sha256": transport.sha(native_raw)}}
        args = types.SimpleNamespace(pins="synthetic-pins", native_preflight="synthetic-native",
            expected_native_preflight_sha256=transport.sha(native_raw))
        def read_json(path):
            return Path(path), transport.canonical(pins), pins if path == args.pins else proof
        with patch.object(transport, "read_json", side_effect=lambda path:
                (Path(path), transport.canonical(pins), pins) if path == args.pins else (Path(path), native_raw, proof)), \
             patch.object(transport.time, "time", return_value=1791731000.001):
            with self.assertRaises(transport.Failure) as error:
                transport.prepare(args)
            self.assertEqual(error.exception.code, "EXACT_NEW_AUTHORITY_PINS_REQUIRED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
