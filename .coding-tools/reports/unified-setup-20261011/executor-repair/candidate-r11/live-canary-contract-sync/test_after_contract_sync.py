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


canary = module("after_contract_sync_canary", HERE / "r11_mcp_canary.py")
fixture_module = module("offline_prior_observer_fixtures", HERE.parent / "observe-reconciliation/test_observe_r11.py")


class ContractSyncTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixture_module.ObserverTests(methodName="test_exact_causal_context_accepted_and_database_unchanged")
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        for key in ("database", "common", "pins", "family", "context", "owner_context", "overview"):
            setattr(self, key, getattr(self.fixture, key))
        self.operation_dir = Path(self.fixture.temp.name) / "canary-after-contract-sync"
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
        self.assertEqual(canary.CANARY_OPERATION_DIR, canary.NEXT_OPERATION_DIR / "canary-after-contract-sync")
        self.assertEqual(canary.NEXT_AUTHORITY_MARKER, canary.NEXT_OPERATION_DIR / "authority-renewal-public.json")
        self.assertEqual(canary.NEXT_REQUESTED_AT_MS, 1791735729910)
        self.assertEqual(canary.NEXT_EXPIRES_AT_MS, 1791739329910)
        source = (HERE / "r11_mcp_canary.py").read_text()
        tree = ast.parse(source)
        main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
        names = {node.id for node in ast.walk(main) if isinstance(node, ast.Name)}
        self.assertIn("CANARY_OPERATION_DIR", names)
        self.assertNotIn("NEXT_OPERATION_DIR", names)
        self.assertIn("r11-contract-sync-task-", source)
        self.assertIn("r11-contract-sync-patch-", source)
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
        self.assertTrue(json.loads(marker.read_bytes())["task_key"].startswith("r11-contract-sync-task-"))

    def test_frozen_prior_helpers_and_packet_unchanged(self):
        self.assertEqual(canary.sha((HERE.parent / "live-canary-next/r11_mcp_canary.py").read_bytes()),
            "b9be1f2fb50b3831442dbf12aaf15f68a2af5286c8ae5bd14b74f0a375b7918a")
        self.assertEqual(canary.sha((HERE.parent / "observe-reconciliation/observe-r11.py").read_bytes()),
            "6525b2c6069c474c1c0c6e45084f19e4700246d2262b087c633e3692983caf73")
        self.assertEqual(canary.sha((HERE.parent / "activation-server/r11_common.py").read_bytes()), canary.COMMON_SHA256)
        patch_text, post = canary.packet()
        self.assertEqual(canary.sha(patch_text.encode()), canary.PATCH)
        self.assertEqual(canary.sha(post), canary.POST)


if __name__ == "__main__":
    unittest.main(verbosity=2)
