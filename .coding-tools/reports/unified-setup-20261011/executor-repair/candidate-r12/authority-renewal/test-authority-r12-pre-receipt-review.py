"""Focused offline renewal/transport proof, no SSH/API/runtime effects."""
from contextlib import redirect_stdout
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shlex
import sys
import tarfile
import tempfile
import types
import unittest
from unittest import mock
sys.dont_write_bytecode = True
sys.modules.setdefault("fcntl", types.SimpleNamespace())
sys.modules.setdefault("pwd", types.SimpleNamespace())
OUT = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


h = load("next_authority_fixture", OUT / "ubuntu-r12-authority.py")
t = load("next_transport_fixture", OUT / "root-ssh-r12.py")


class RenewalTests(unittest.TestCase):
    def setUp(self):
        self.now = h.PRIOR_EXPIRES + 1000
        self.grant = {"expires_at_ms": self.now + 7200000}
        self.overview = {"observed_at_ms": self.now, "admission": {"admission_mode": "recovery"},
                         "contexts": [{"context_id": h.PRIOR_CONTEXT, "binding_id": h.c.BINDING,
                            "device_id": h.c.DEVICE, "workspace_id": h.c.WORKSPACE, "workspace_generation": h.c.GENERATION,
                            "expires_at_ms": h.PRIOR_EXPIRES, "closed_at_ms": None}],
                         "scoped_pilot_decisions": [{"decision_id": h.PRIOR_PILOT, "binding_id": h.c.BINDING,
                            "device_id": h.c.DEVICE, "workspace_id": h.c.WORKSPACE, "workspace_generation": h.c.GENERATION,
                            "principal_id": h.c.PRINCIPAL, "expires_at_ms": h.PRIOR_EXPIRES, "revoked_at_ms": None, "reason": "prior"}]}
        close_ids, revoke_ids = h.selected_expired(self.overview)
        self.marker = {"phase": "close_prepared", "old_context_ids": close_ids, "old_pilot_ids": revoke_ids,
                       "authority_initial": h.authority_fence(self.overview, close_ids, revoke_ids)}
        self.calls = []
        self.saved = []
        self.patches = [mock.patch.object(h, "save", lambda value: self.saved.append(json.loads(json.dumps(value)))),
                        mock.patch.object(h, "bootstrap_canary_directory", lambda: None),
                        mock.patch.object(h, "now_ms", lambda: self.now),
                        mock.patch.object(h.c, "api", self.api)]
        for patch in self.patches:
            patch.start(); self.addCleanup(patch.stop)

    def api(self, _origin, _auth, route, body=None):
        self.calls.append((route, body))
        if route == "/v1/ui/overview":
            return self.overview
        if route == "/healthz":
            return {"admission_mode": self.overview["admission"]["admission_mode"]}
        if route.endswith("/revoke"):
            self.overview["scoped_pilot_decisions"][0]["revoked_at_ms"] = self.now
            return self.overview["scoped_pilot_decisions"][0]
        if route.endswith("/close"):
            self.overview["contexts"][0]["closed_at_ms"] = self.now
            return self.overview["contexts"][0]
        if route == "/v1/contexts":
            row = {**body, "context_id": "ctx_new", "device_id": h.c.DEVICE,
                   "workspace_id": h.c.WORKSPACE, "workspace_generation": h.c.GENERATION, "closed_at_ms": None}
            self.overview["contexts"].append(row); return row
        if route == "/v1/scoped-pilot-decisions":
            row = {**body, "decision_id": "pilot_new", "device_id": h.c.DEVICE,
                   "workspace_id": h.c.WORKSPACE, "workspace_generation": h.c.GENERATION, "revoked_at_ms": None}
            self.overview["scoped_pilot_decisions"].append(row); return row
        raise AssertionError(route)

    def test_close_then_anchor_once_renew_no_duplicate_or_grant(self):
        h.close_expired("fixture", "fixture-only", self.overview, self.marker)
        self.assertNotIn("requested_at_ms", self.marker)
        self.now += 10000; self.overview["observed_at_ms"] = self.now
        h.renew("fixture", "fixture-only", self.overview, self.marker, self.grant)
        first = dict(self.marker)
        self.now += 5000; self.overview["observed_at_ms"] = self.now
        h.renew("fixture", "fixture-only", self.overview, self.marker, self.grant)
        self.assertEqual(self.marker["expires_at_ms"] - self.marker["requested_at_ms"], 3600000)
        self.assertEqual(first["requested_at_ms"], self.marker["requested_at_ms"])
        self.assertEqual(sum(route == "/v1/contexts" for route, _ in self.calls), 1)
        self.assertEqual(sum(route == "/v1/scoped-pilot-decisions" for route, _ in self.calls), 1)
        self.assertFalse(any("grant" in route or "renew" in route for route, _ in self.calls))

    def test_unrelated_pilot_blocked_before_recovery_effect(self):
        self.overview["scoped_pilot_decisions"].append({"decision_id": "unrelated", "revoked_at_ms": None})
        with self.assertRaises(h.c.GuardFailure):
            h.selected_expired(self.overview)
        with self.assertRaises(h.c.GuardFailure):
            h.close_expired("fixture", "fixture-only", self.overview, self.marker)
        self.assertEqual(self.calls, [])

    def test_unknown_create_outcome_blocks_replay(self):
        h.close_expired("fixture", "fixture-only", self.overview, self.marker)
        self.marker.update(requested_at_ms=self.now, expires_at_ms=self.now + 3600000,
                           phase="context_create_intended", context_create_intended=True)
        before = len(self.calls)
        with self.assertRaises(h.c.GuardFailure) as failure:
            h.renew("fixture", "fixture-only", self.overview, self.marker, self.grant)
        self.assertEqual(failure.exception.code, "CONTEXT_CREATE_OUTCOME_UNKNOWN_NO_REPLAY")
        self.assertEqual(len(self.calls), before)

    def test_lost_context_response_adopts_one_exact_row_without_replay(self):
        h.close_expired("fixture", "fixture-only", self.overview, self.marker)
        self.marker.update(requested_at_ms=self.now, expires_at_ms=self.now + 3600000,
                           phase="context_create_intended", context_create_intended=True)
        self.api("fixture", "fixture-only", "/v1/contexts", {"binding_id": h.c.BINDING, "expires_at_ms": self.marker["expires_at_ms"]})
        h.renew("fixture", "fixture-only", self.overview, self.marker, self.grant)
        self.assertEqual(sum(route == "/v1/contexts" for route, _ in self.calls), 1)
        self.assertEqual(self.marker["phase"], "authority_renewed")

    def test_unrelated_authority_field_change_rejected(self):
        self.overview["contexts"][0]["expires_at_ms"] += 1
        with self.assertRaises(h.c.GuardFailure) as failure:
            h.preserve_authority_rows(self.overview, self.marker)
        self.assertEqual(failure.exception.code, "UNRELATED_AUTHORITY_HISTORY_CHANGED")

    def test_prior_authority_renewed_marker_exact_and_immutable(self):
        prior = {"operation": "owner_approved_r11_initial_verification_next_60m", "binding_id": h.c.BINDING,
                 "device_id": h.c.DEVICE, "workspace_id": h.c.WORKSPACE, "workspace_generation": h.c.GENERATION,
                 "root": h.c.LOCAL_ROOT, "profile": h.c.LOCAL_PROFILE, "source_revision": h.c.REVISION,
                 "service_grant_sha256": h.c.digest(self.grant), "phase": "intake_reopened",
                 "requested_at_ms": h.PRIOR_REQUESTED, "expires_at_ms": h.PRIOR_EXPIRES,
                 "context_id": h.PRIOR_CONTEXT, "pilot_id": h.PRIOR_PILOT}
        raw = json.dumps(prior).encode()
        with mock.patch.object(h.c, "protected_file", return_value=raw), mock.patch.object(h, "PRIOR_MARKER_SHA", hashlib.sha256(raw).hexdigest()):
            self.assertEqual(h.prior_marker(self.grant)[1], hashlib.sha256(raw).hexdigest())
        prior["phase"] = "authority_renewed"
        with mock.patch.object(h.c, "protected_file", return_value=json.dumps(prior).encode()), self.assertRaises(h.c.GuardFailure):
            h.prior_marker(self.grant)

    def test_expired_standing_telemetry_ttl_and_wrong_context_block_reopen(self):
        h.close_expired("fixture", "fixture-only", self.overview, self.marker)
        h.renew("fixture", "fixture-only", self.overview, self.marker, self.grant)
        self.overview["nodes"] = [{"device_id": h.c.DEVICE, "activation_epoch": "epoch", "runtime_instance_id": "runtime",
          "mcp_server_instance_id": "mcp", "contract_version": "sha256:" + "a" * 64, "last_seen_at_ms": self.now,
          "readiness": "ready", "policy_state": "enabled", "policy_expires_at_ms": self.now}]
        args = types.SimpleNamespace(expected_activation_epoch="epoch", expected_runtime_instance="runtime",
                                     expected_mcp_instance="mcp", expected_contract_version="sha256:" + "a" * 64)
        before = len(self.calls)
        with self.assertRaises(h.c.GuardFailure) as failure:
            h.reopen("fixture", "fixture-only", self.overview, self.marker, args)
        self.assertEqual(failure.exception.code, "NODE_NOT_FRESH_READY_CURRENT_STANDING_POLICY_TTL")
        self.overview["nodes"][0]["policy_expires_at_ms"] = self.now + 59000
        self.overview["contexts"][-1]["context_id"] = "ctx_wrong"
        with self.assertRaises(h.c.GuardFailure) as failure:
            h.reopen("fixture", "fixture-only", self.overview, self.marker, args)
        self.assertEqual(failure.exception.code, "RENEWED_CONTEXT_CHANGED")
        self.assertEqual(len(self.calls), before)


class TransportTests(unittest.TestCase):
    def run_mock(self, args, effect):
        with tempfile.TemporaryDirectory(prefix="r11-next-transport-fixture-") as directory:
            root = Path(directory)
            manifest = {"helpers": {}, "archives": []}
            for name in ("r11_common.py", "ubuntu-r12-authority.py"):
                raw = (OUT / name).read_bytes(); (root / name).write_bytes(raw)
                manifest["helpers"][name] = {"sha256": t.sha(raw), "size_bytes": len(raw)}
            (root / "helper-manifest.json").write_text(json.dumps(manifest))
            with mock.patch.object(t, "OUT", root), mock.patch.object(t.shutil, "which", return_value="ssh-fixture"), \
                 mock.patch.object(t.subprocess, "run", side_effect=effect), mock.patch.object(sys, "argv", ["driver", *args]), redirect_stdout(io.StringIO()) as stdout:
                try:
                    t.main()
                except SystemExit as error:
                    self.assertEqual(error.code, 2)
            result = json.loads(stdout.getvalue())
            self.assertNotIn("private stderr fixture", stdout.getvalue())
            self.assertEqual(len(list((root / "remote-receipts").glob("*.json"))), 1)
            return result

    def test_binary_two_helper_stage_strict_ssh_no_archives(self):
        def call(argv, **kwargs):
            self.assertEqual(argv[1:5], ["-T", "-oBatchMode=yes", "-oStrictHostKeyChecking=yes", "-oConnectTimeout=15"])
            self.assertIn("-oServerAliveInterval=15", argv)
            self.assertEqual(kwargs["timeout"], 120)
            command = shlex.split(argv[-1]); expected = json.loads(command[5])
            with tarfile.open(fileobj=io.BytesIO(kwargs["input"]), mode="r:") as archive:
                self.assertEqual(set(x.name for x in archive.getmembers()), {"r11_common.py", "ubuntu-r12-authority.py"})
                for member in archive.getmembers():
                    self.assertEqual(t.sha(archive.extractfile(member).read()), expected[member.name]["sha256"])
            return types.SimpleNamespace(returncode=0, stdout=b'{"phase":"r11_artifacts_staged","ok":true}\n', stderr=b"private stderr fixture")
        result = self.run_mock(["stage", "--execute", "--operator-approved", "--approval-id", "call_r12_future_fixture", "--approved-duration-ms", "3600000"], call)
        self.assertFalse(result["archives_transferred"])
        self.assertFalse(result["deployment_or_restart_requested"])

    def test_timeout_receipt_unknown_without_stdout_disclosure(self):
        def call(*args, **kwargs):
            raise t.subprocess.TimeoutExpired("fixture", 600, output=b"private stdout", stderr=b"private stderr fixture")
        result = self.run_mock(["stage", "--execute", "--operator-approved", "--approval-id", "call_r12_future_fixture", "--approved-duration-ms", "3600000"], call)
        self.assertFalse(result["effect_known"])
        self.assertEqual(result["code"], "TRANSPORT_TIMEOUT_OUTCOME_UNKNOWN_NO_REPLAY")


class R12GuardTests(unittest.TestCase):
    def test_read_only_observe_receipt_serializes_worker_fields_without_effects(self):
        marker = {"operation": h.OPERATION, "phase": "authority_renewed", "requested_at_ms": 100000,
                  "expires_at_ms": 3700000, "context_id": "ctx_new", "pilot_id": "pilot_new"}
        health = {"declared_source_revision": h.c.REVISION, "package_source_sha256": h.c.PACKAGE,
                  "service_instance_id": "cp_fixture"}
        overview = {"observed_at_ms": 110000, "admission": {"admission_mode": "recovery"},
                    "nodes": [{"device_id": h.c.DEVICE}], "contexts": [], "scoped_pilot_decisions": []}
        snapshot = {"fixture": True}
        grant = {"expires_at_ms": 5000000}
        with tempfile.TemporaryDirectory() as directory:
            marker_path = Path(directory) / "authority-renewal-public.json"
            raw = json.dumps(marker).encode(); marker_path.write_bytes(raw)
            with mock.patch.object(h, "NEXT_MARKER", marker_path), \
                 mock.patch.object(h, "prior_marker", return_value=({}, h.PRIOR_MARKER_SHA)), \
                 mock.patch.object(h.c, "inspect", return_value=("fixture", "fixture-only", None, health, snapshot, overview, grant)), \
                 mock.patch.object(h.c, "protected_file", return_value=raw), \
                 mock.patch.object(h.c, "api") as api, mock.patch.object(h, "save") as save, \
                 mock.patch.object(sys, "argv", ["driver", "observe"]), redirect_stdout(io.StringIO()) as stdout:
                h.main()
            receipt = json.loads(stdout.getvalue())
        for key in ("observed_at_ms", "service_instance_id", "binding_id", "device_id", "workspace_id",
                    "workspace_generation", "root", "profile", "requested_at_ms", "expires_at_ms", "context_id",
                    "pilot_id", "capabilities", "canary_directory", "minimum_canary_remaining_ms", "admission",
                    "next_marker_sha256", "state_sha256", "service_grant_sha256"):
            self.assertIn(key, receipt)
        self.assertEqual(receipt["capabilities"], {"read": True, "write": True, "exec": True})
        self.assertEqual(receipt["next_marker_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(receipt["expires_at_ms"], 3700000)
        self.assertFalse(receipt["remote_mutation"])
        api.assert_not_called(); save.assert_not_called()

    def test_full_ten_minute_action_window_plus_margin_required(self):
        marker = {"requested_at_ms": 100000, "expires_at_ms": 3700000}
        h.canary_window(marker, 3700000 - 720000)
        for now in (3700000 - 720000 + 1, 3700000 - 600000, 99999, True):
            with self.assertRaises(h.c.GuardFailure) as error:
                h.canary_window(marker, now)
            self.assertEqual(error.exception.code, "R12_WINDOW_TOO_SHORT_FOR_FULL_10M_ACTION_PLUS_MARGIN")

    def test_new_namespace_old_marker_and_unchanged_common(self):
        self.assertEqual(h.NEXT_DIR.name, "r12-initial-verification-60m")
        self.assertEqual(h.CANARY_DIR, h.NEXT_DIR / "canary")
        self.assertEqual(h.PRIOR_MARKER.parent.name, "r11-initial-verification-next-60m")
        self.assertEqual(h.c.MARKER.parent.name, "r11-initial-verification-60m")
        self.assertEqual(hashlib.sha256((OUT / "r11_common.py").read_bytes()).hexdigest(), h.COMMON_SHA)

    def test_bootstrap_creates_only_child_and_rejects_existing_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            child = parent / "canary"
            checked = []
            def private(path):
                if not path.is_dir() or path.is_symlink():
                    raise h.c.GuardFailure("PRIVATE_DIRECTORY_UNSAFE")
                checked.append(path)
            with mock.patch.object(h, "NEXT_DIR", parent), mock.patch.object(h, "CANARY_DIR", child), \
                 mock.patch.object(h.c, "private_directory", side_effect=private):
                h.bootstrap_canary_directory()
                self.assertTrue(child.is_dir())
                self.assertEqual(list(parent.iterdir()), [child])
                h.bootstrap_canary_directory()
                (child / "retained.json").write_text("history")
                with self.assertRaises(h.c.GuardFailure) as error:
                    h.bootstrap_canary_directory()
                self.assertEqual(error.exception.code, "R12_CANARY_EVIDENCE_ALREADY_EXISTS_NO_REPLAY")
                self.assertEqual((child / "retained.json").read_text(), "history")

    def test_stage_requires_future_approval_before_subprocess(self):
        with mock.patch.object(sys, "argv", ["driver", "stage"]), mock.patch.object(t.subprocess, "run") as called:
            with self.assertRaises(ValueError) as error:
                t.main()
        self.assertEqual(str(error.exception), "EXPLICIT_FUTURE_60M_APPROVAL_REQUIRED")
        called.assert_not_called()

    def test_transport_intent_once_only(self):
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(t, "OUT", Path(directory)):
            t.effect_intent("renew", "fixed-remote", "call_r12_future_fixture")
            with self.assertRaises(ValueError) as error:
                t.effect_intent("renew", "fixed-remote", "call_r12_future_fixture")
            self.assertEqual(str(error.exception), "IMMUTABLE_TRANSPORT_INTENT_EXISTS_NO_REPLAY")


if __name__ == "__main__":
    unittest.main()
