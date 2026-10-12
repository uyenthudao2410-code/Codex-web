"""Focused offline proof for separate trial paths and causal observation."""
import ast
import copy
import importlib.util
import json
from pathlib import Path
import sys
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


canary = module("after_contract_sync_canary", HERE / "r13_5h_mcp_canary.py")
fixture_module = module("offline_prior_observer_fixtures", HERE.parent.parent / "candidate-r11/observe-reconciliation/test_observe_r11.py")


class ContractSyncTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixture_module.ObserverTests(methodName="test_exact_causal_context_accepted_and_database_unchanged")
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        for key in ("database", "common", "pins", "family", "context", "owner_context", "overview"):
            setattr(self, key, getattr(self.fixture, key))
        self.operation_dir = Path(self.fixture.temp.name) / "canary"
        self.operation_dir.mkdir()
        (self.operation_dir / "canary-dispatch.json").write_bytes(b"{}")

    def consume(self):
        with patch.object(canary, "CANARY_OPERATION_DIR", self.operation_dir), \
             patch.object(canary, "private_json", return_value={"pins_sha256": canary.digest(self.pins)}), \
             patch.object(canary, "ids", return_value=self.family):
            return canary.own_context_view(self.common, self.pins, self.database, self.overview)

    def test_only_exact_own_context_filtered_and_database_unchanged(self):
        raw = self.database.read_bytes()
        before = copy.deepcopy(self.overview)
        view = self.consume()
        self.assertEqual(view["contexts"], [self.owner_context])
        self.assertEqual(self.overview, before)
        self.assertEqual(self.database.read_bytes(), raw)
        self.common.renewed_authority(view, self.pins)

    def test_unrelated_context_still_fails_original_guard(self):
        self.overview["contexts"].append({**self.context, "context_id": "unrelated"})
        view = self.consume()
        with self.assertRaises(fixture_module.observer.Failure) as error:
            self.common.renewed_authority(view, self.pins)
        self.assertEqual(error.exception.code, "RENEWED_CONTEXT_CHANGED")

    def test_changed_owner_context_still_fails_original_guard(self):
        self.overview["contexts"][0] = {**self.owner_context, "expires_at_ms": 3700001}
        with self.assertRaises(fixture_module.observer.Failure):
            self.common.renewed_authority(self.consume(), self.pins)

    def test_broken_action_request_context_link_rejected(self):
        self.fixture.change("UPDATE work_requests SET context_id='other'")
        with self.assertRaises(canary.Failure) as error:
            self.consume()
        self.assertEqual(error.exception.code, "OWN_ACTION_CONTEXT_CAUSAL_LINK_CHANGED")

    def test_other_context_owner_or_target_rejected(self):
        self.fixture.change("UPDATE contexts SET device_id='other' WHERE context_id='action-context'")
        with self.assertRaises(canary.Failure) as error:
            self.consume()
        self.assertEqual(error.exception.code, "OWN_ACTION_CONTEXT_TARGET_CHANGED")

    def test_context_window_changed_rejected(self):
        self.fixture.change("UPDATE contexts SET expires_at_ms=800001 WHERE context_id='action-context'")
        with self.assertRaises(canary.Failure) as error:
            self.consume()
        self.assertEqual(error.exception.code, "OWN_ACTION_CONTEXT_WINDOW_CHANGED")

    def test_context_reused_by_other_action_rejected(self):
        self.fixture.change("INSERT INTO actions SELECT owner_id,binding_id,device_id,endpoint_id,workspace_id,workspace_generation,'other',request_id,context_id,created_at_ms,expires_at_ms FROM actions")
        with self.assertRaises(canary.Failure) as error:
            self.consume()
        self.assertEqual(error.exception.code, "OWN_ACTION_CONTEXT_REUSED")

    def test_overview_context_changed_rejected(self):
        self.overview["contexts"][1] = {**self.context, "created_at_ms": 200001}
        with self.assertRaises(canary.Failure) as error:
            self.consume()
        self.assertEqual(error.exception.code, "OWN_CONTEXT_OVERVIEW_CHANGED")

    def test_family_not_yet_dispatched_does_not_filter_anything(self):
        self.family["action_id"] = None
        self.assertIs(self.consume(), self.overview)

    def test_preflight_without_trial_marker_does_not_filter_anything(self):
        (self.operation_dir / "canary-dispatch.json").unlink()
        self.assertIs(self.consume(), self.overview)

    def test_intent_path_scope_and_old_authority_remain_exact(self):
        self.assertEqual(canary.CANARY_OPERATION_DIR, canary.NEXT_OPERATION_DIR / "canary")
        self.assertEqual(canary.NEXT_AUTHORITY_MARKER, canary.NEXT_OPERATION_DIR / "authority-renewal-public.json")
        self.assertEqual(canary.MIN_CANARY_REMAINING_MS, 720000)
        self.assertEqual(canary.NEXT_OPERATION, "owner_approved_r13_initial_verification_5h")
        self.assertNotIn("NEXT_REQUESTED_AT_MS", (HERE / "r13_5h_mcp_canary.py").read_text())
        source = (HERE / "r13_5h_mcp_canary.py").read_text()
        tree = ast.parse(source)
        main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
        names = {node.id for node in ast.walk(main) if isinstance(node, ast.Name)}
        self.assertIn("CANARY_OPERATION_DIR", names)
        self.assertNotIn("NEXT_OPERATION_DIR", names)
        self.assertIn("r13_5h-initial-task-", source)
        self.assertIn("r13_5h-initial-patch-", source)
        self.assertNotIn("r11-initial-task-", source)
        self.assertNotIn("r11-initial-patch-", source)

    def test_new_trial_once_only_marker_before_first_effect(self):
        marker = self.operation_dir / "canary-dispatch.json"
        marker.unlink()
        common = types.SimpleNamespace(BINDING="binding", private_directory=lambda path: None)
        observed = {"state": {"historical_action_families_sha256": "a" * 64,
            "patch_acceptances_sha256": "b" * 64, "actions": 41, "tasks": 13}}
        calls = []
        def uncertain(*args):
            self.assertTrue(marker.exists())
            calls.append(args)
            raise canary.Failure("MCP_TRANSPORT_UNCERTAIN_NO_RETRY")
        with patch.object(canary, "CANARY_OPERATION_DIR", self.operation_dir), \
             patch.object(sys, "argv", ["helper", "dispatch"]), patch.object(canary, "load_common", return_value=common), \
             patch.object(canary, "pins_input", return_value=self.pins), \
             patch.object(canary, "preflight", return_value=(None, "http://127.0.0.1", "mock-only", {}, observed)), \
             patch.object(canary, "call", side_effect=uncertain):
            with self.assertRaises(canary.Failure):
                canary.main()
            with self.assertRaises(canary.Failure) as error:
                canary.main()
            self.assertEqual(error.exception.code, "IMMUTABLE_RECEIPT_ALREADY_EXISTS_NO_REPLAY")
        self.assertEqual(len(calls), 1)
        self.assertTrue(json.loads(marker.read_bytes())["task_key"].startswith("r13_5h-initial-task-"))

    def test_frozen_prior_helpers_and_packet_unchanged(self):
        self.assertEqual(canary.sha((HERE.parent.parent / "candidate-r11/live-canary-next/r11_mcp_canary.py").read_bytes()),
            "b9be1f2fb50b3831442dbf12aaf15f68a2af5286c8ae5bd14b74f0a375b7918a")
        self.assertEqual(canary.sha((HERE.parent.parent / "candidate-r11/observe-reconciliation/observe-r11.py").read_bytes()),
            "6525b2c6069c474c1c0c6e45084f19e4700246d2262b087c633e3692983caf73")
        self.assertEqual(canary.sha((HERE.parent / "authority-5h/r11_common.py").read_bytes()), canary.COMMON_SHA256)
        patch_text, post = canary.packet()
        self.assertEqual(canary.sha(patch_text.encode()), canary.PATCH)
        self.assertEqual(canary.sha(post), canary.POST)


class R13_5HAuthorityTests(unittest.TestCase):
    def setUp(self):
        self.now = 10_000_000
        self.pins = {"requested_at_ms": self.now - 1000, "expires_at_ms": self.now + 17999000,
            "context_id": "ctx_new", "pilot_id": "pilot_new", "service_instance_id": "cp_new",
            "activation_epoch": "epoch_new", "runtime_instance_id": "process_new", "mcp_server_instance_id": "server_new",
            "contract_version": "sha256:" + canary.NATIVE_TOOL_SHA256, "native_tool_contract_sha256": canary.NATIVE_TOOL_SHA256,
            "approval_id": "call_a60e931056bd402b997c6c10b0796d81", "native_preflight": {"observed_at_ms": self.now - 1,
                "source_head": canary.HEAD, "preimage_sha256": canary.PRE, "checker_sha256": canary.CHECK,
                "old_run_sha256": canary.OLD_RUN_SHA, "old_wave_sha256": canary.OLD_WAVE_SHA,
                "no_active_jobs": True, "receipt_sha256": "a" * 64}}
        self.common = types.SimpleNamespace(BINDING="binding",DEVICE="device",WORKSPACE="workspace",GENERATION="generation",
            LOCAL_ROOT=r"E:\Github\Tools-Codex-web",LOCAL_PROFILE="web-mcp-assistant",REVISION="revision",PACKAGE="package",
            HOST="100.116.112.22",SERVICE="codex-control-plane.service",renewed_authority=lambda *args: None)
        self.target = {"operation": canary.NEXT_OPERATION,"binding_id":"binding","device_id":"device",
            "workspace_id":"workspace","workspace_generation":"generation","root":self.common.LOCAL_ROOT,
            "profile":self.common.LOCAL_PROFILE,"source_revision":"revision","approval_id":self.pins["approval_id"],
            "approved_duration_ms":18000000}
        self.prior = {"operation":"owner_approved_r12_initial_verification_60m","phase":"intake_reopened",
            "requested_at_ms":1791747735200,"expires_at_ms":1791751335200,
            "binding_id":"binding","root":self.common.LOCAL_ROOT,"profile":self.common.LOCAL_PROFILE}
        self.prior_raw = canary.canonical(self.prior)
        self.authority = {**self.target,**{key:self.pins[key] for key in
            ("requested_at_ms","expires_at_ms","context_id","pilot_id","service_instance_id",
             "activation_epoch","runtime_instance_id","mcp_server_instance_id","contract_version")},
            "phase":"intake_reopened","prior_marker_sha256":canary.sha(self.prior_raw)}
        self.authority_raw = canary.canonical(self.authority)
        self.receipt = {**{key:value for key,value in self.target.items() if key not in {"operation","approved_duration_ms"}},
            **{key:self.pins[key] for key in ("requested_at_ms","expires_at_ms","context_id","pilot_id","service_instance_id")},
            "ok":True,"phase":"r13_5h_intake_reopened","host":self.common.HOST,"service":self.common.SERVICE,
            "admission":"scoped_pilot","duration_ms":18000000,"prior_marker_unchanged":True,
            "prior_marker_sha256":canary.sha(self.prior_raw),"next_marker_sha256":canary.sha(self.authority_raw),
            "deployed":False,"service_restarted":False}
        self.receipt_raw = canary.canonical(self.receipt)
        self.pins.update(authority_receipt_sha256=canary.sha(self.receipt_raw),authority_marker_sha256=canary.sha(self.authority_raw))
        self.docs = {canary.HERE/"pins.json":self.pins,canary.HERE/"authority-receipt.json":self.receipt,
            canary.NEXT_AUTHORITY_MARKER:self.authority,canary.PRIOR_AUTHORITY_MARKER:self.prior}
        self.raw = {canary.HERE/"authority-receipt.json":self.receipt_raw,canary.NEXT_AUTHORITY_MARKER:self.authority_raw,
            canary.PRIOR_AUTHORITY_MARKER:self.prior_raw}
        self.common.protected_file = lambda path:self.raw[path]
        self.health = {"declared_source_revision":"revision","schema_version":29,"ok":True,
            "package_source_sha256":"package","expected_package_source_sha256":"package","service_instance_id":"cp_new"}
        self.node = {"device_id":"device",**{key:self.pins[key] for key in
            ("activation_epoch","runtime_instance_id","mcp_server_instance_id","contract_version")},
            "readiness":"ready","policy_state":"enabled","last_seen_at_ms":self.now - 1,"policy_expires_at_ms":self.now + 59999}
        self.overview = {"observed_at_ms":self.now,"admission":{"admission_mode":"scoped_pilot"},"nodes":[self.node]}

    def pinned(self):
        with patch.object(canary,"private_json",side_effect=lambda path:self.docs[path]), \
             patch.object(canary,"PRIOR_AUTHORITY_SHA256",canary.sha(self.prior_raw)):
            return canary.pins_input(self.common)

    def guard(self):
        return canary.authority_guard(self.common,self.pins,self.health,self.overview,
            {"expires_at_ms":self.now+18000000},dispatch=True)

    def test_dynamic_new_window_is_receipt_and_marker_bound(self):
        self.assertIs(self.pinned(),self.pins)
        self.guard()

    def test_changed_receipt_or_marker_hash_is_rejected(self):
        for field in ("authority_receipt_sha256","authority_marker_sha256"):
            with self.subTest(field=field):
                old=self.pins[field];self.pins[field]="b"*64
                with self.assertRaises(canary.Failure):self.pinned()
                self.pins[field]=old

    def test_expired_approval_or_wrong_reopened_native_is_rejected(self):
        self.pins["approval_id"]=canary.EXPIRED_APPROVAL
        with self.assertRaises(canary.Failure):self.pinned()
        self.pins["approval_id"]=self.target["approval_id"]
        self.authority["runtime_instance_id"]="different"
        with self.assertRaises(canary.Failure) as error:self.pinned()
        self.assertEqual(error.exception.code,"REOPENED_NATIVE_PIN_MISMATCH")

    def test_twelve_minute_margin_at_actual_server_observation(self):
        self.pins["expires_at_ms"]=self.now+720000
        self.guard()
        self.pins["expires_at_ms"]-=1
        with self.assertRaises(canary.Failure) as error:self.guard()
        self.assertEqual(error.exception.code,"PREFLIGHT_STALE_OR_TRIAL_TOO_SHORT")

    def test_stale_native_or_policy_heartbeat_is_rejected(self):
        self.pins["native_preflight"]["observed_at_ms"]=self.now-60000
        with self.assertRaises(canary.Failure):self.guard()
        self.pins["native_preflight"]["observed_at_ms"]=self.now-1
        self.node["policy_expires_at_ms"]=self.now
        with self.assertRaises(canary.Failure):self.guard()

    def test_both_preflight_and_dispatch_use_same_strong_guard(self):
        source=(HERE/"r13_5h_mcp_canary.py").read_text()
        self.assertIn("authority_guard(common, pins, health, overview, grant, dispatch=initial)",source)
        self.assertIn("authority_guard(common, pins, fresh_health, fresh_overview, fresh_grant, dispatch=True)",source)
        self.assertIn("MIN_CANARY_REMAINING_MS = 720000",source)
        self.assertNotIn("expires_at_ms\"] - now >= 120000",source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
