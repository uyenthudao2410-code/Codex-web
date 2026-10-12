"""Offline helper tests. No main(), live RPC, SSH, authority or runtime effects."""
from __future__ import annotations
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
ROOT = HERE.parents[5]
sys.path.insert(0, str(ROOT / "control-plane"))
spec = importlib.util.spec_from_file_location("canary", HERE / "r11_mcp_canary.py")
canary = importlib.util.module_from_spec(spec)
spec.loader.exec_module(canary)
from control_plane.mcp_facade import tool_contract


def contract_packet():
    value = tool_contract(auth_kind="private_tunnel_service",
        oauth_scopes=("control-plane.inventory", "control-plane.read"),
        oauth_file_read_enabled=True, oauth_patch_write_scope="control-plane.patch",
        oauth_standing_write_enabled=True, oauth_approved_patch_enabled=True,
        oauth_exec_enabled=True)
    meta = {key: value[key] for key in ("schema_version", "profile", "sha256")}
    listed = {"tools": value["tools"], "_meta": {"control_plane": {"access_scope": canary.SERVICE_SCOPE, "tool_contract": meta}}}
    inventory = {"tool_contract": meta, "principal_id": "principal", "targets": [{"binding_id": "binding"}]}
    return listed, inventory


def proof_family(status="passed"):
    pins = {"activation_epoch": "epoch", "runtime_instance_id": "process", "mcp_server_instance_id": "server",
            "native_tool_contract_sha256": "a" * 64}
    marker = {"facade_contract": {"schema_version": 123, "profile": "live-profile", "sha256": "b" * 64}}
    proof = {"plan_sha256": canary.PLAN_SHA, "proof_status": status,
             "proof_ids": ["c" * 32] if status == "passed" else [],
             "proof_fingerprint": "d" * 64 if status == "passed" else None,
             "command_id": "command_1", "job_id": "job_1"}
    file = {"path": canary.TARGET, "preimage_sha256": canary.PRE, "postimage_sha256": canary.POST, "bytes_written": 414}
    payload = {"schema_version": 1, "operation_kind": "control_plane_approved_patch", "patch_applied": True,
        "local_semantic_acceptance": "pending", "task_id": "task_" + "e" * 32, "writer_lease_generation": 1,
        "actor": {"client_id": "electron-control-plane-approved-patch-bridge", "client_type": "electron"},
        "facade_contract": marker["facade_contract"], "run_id": "f" * 32, "wave_id": "1" * 32,
        "local_handle": "cp_ap_" + "2" * 48, "policy_sha256": "3" * 64,
        "runtime_identity": {"activation_epoch_id": "epoch", "process_instance_id": "process", "server_instance_id": "server", "tool_contract_sha256": "a" * 64},
        "file": file, "initial_verification": proof,
        "response_sha256": canary.digest({"file": file, "initial_verification": proof})}
    family = {"settled": True, "state": "settled", "task_id": payload["task_id"], "writer_lease_generation": 1,
              "receipt": {"receipt_id": "receipt_1", "payload_json": json.dumps(payload)}}
    return family, marker, pins, payload


class OfflineCanaryTests(unittest.TestCase):
    def test_exact_60m_context_guard_refuses_expired_context_without_changing_grant(self):
        source = (HERE.parent / "activation-server/r11_common.py").read_bytes()
        self.assertEqual(canary.sha(source), canary.COMMON_SHA256)
        function = next(item for item in ast.parse(source).body if isinstance(item, ast.FunctionDef) and item.name == "renewed_authority")
        namespace = {"require": canary.require, "BINDING": "binding", "DEVICE": "device", "WORKSPACE": "workspace",
                     "GENERATION": "generation", "PRINCIPAL": "principal"}
        exec(compile(ast.Module(body=[function], type_ignores=[]), "frozen-pure-authority-guard", "exec"), namespace)
        pins = {"requested_at_ms": 100000, "expires_at_ms": 3700000, "context_id": "context", "pilot_id": "pilot"}
        context = {"context_id": "context", "binding_id": "binding", "device_id": "device", "workspace_id": "workspace",
                   "workspace_generation": "generation", "expires_at_ms": 3700000, "closed_at_ms": None}
        pilot = {"decision_id": "pilot", "binding_id": "binding", "device_id": "device", "workspace_id": "workspace",
                 "workspace_generation": "generation", "principal_id": "principal", "expires_at_ms": 3700000, "revoked_at_ms": None}
        overview = {"observed_at_ms": 110000, "contexts": [context], "scoped_pilot_decisions": [pilot]}
        namespace["renewed_authority"](overview, pins)
        context["expires_at_ms"] = overview["observed_at_ms"] - 1
        with self.assertRaises(canary.Failure) as error:
            namespace["renewed_authority"](overview, pins)
        self.assertEqual(error.exception.code, "RENEWED_CONTEXT_CHANGED")

    def test_exact_packet_and_local_source(self):
        result = canary.stage(ROOT)
        self.assertEqual(result["patch_sha256"], canary.PATCH)
        self.assertFalse(result["remote_mutation"])
        self.assertEqual(set(canary.PLAN), {"argv", "cwd", "timeout_ms", "max_output_bytes"})

    def test_real_contract_consumed_without_hardcoded_facade_profile(self):
        listed, inventory = contract_packet()
        self.assertEqual(canary.live_contract(listed, inventory, "binding", "principal"), inventory["tool_contract"])

    def test_wrong_contract_and_extra_target_are_refused(self):
        listed, inventory = contract_packet()
        inventory["tool_contract"] = {**inventory["tool_contract"], "sha256": "0" * 64}
        with self.assertRaises(canary.Failure):
            canary.live_contract(listed, inventory, "binding", "principal")
        listed, inventory = contract_packet()
        inventory["targets"].append({"binding_id": "other"})
        with self.assertRaises(canary.Failure):
            canary.live_contract(listed, inventory, "binding", "principal")

    def test_internal_expiry_cannot_enter_public_verification(self):
        listed, inventory = contract_packet()
        tool, schema = canary.branch(listed["tools"], "agent_workflow", "apply_patch")
        schema["properties"]["verification"]["properties"]["initial_verification_expires_at_ms"] = {"type": "integer"}
        with self.assertRaises(canary.Failure):
            canary.live_contract(listed, inventory, "binding", "principal")

    def test_one_immutable_marker_only(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "marker.json"
            canary.exclusive(path, {"value": 1})
            with self.assertRaises(canary.Failure) as error:
                canary.exclusive(path, {"value": 2})
            self.assertEqual(error.exception.code, "IMMUTABLE_RECEIPT_ALREADY_EXISTS_NO_REPLAY")
            self.assertEqual(json.loads(path.read_bytes()), {"value": 1})

    def test_uncertain_first_effect_has_durable_marker_and_cannot_dispatch_again(self):
        with tempfile.TemporaryDirectory() as directory:
            common = types.SimpleNamespace(OPERATION_DIR=Path(directory), BINDING="binding", private_directory=lambda path: None)
            pins = {"expires_at_ms": 999999}
            observed = {"state": {"historical_action_families_sha256": "a" * 64,
                                  "patch_acceptances_sha256": "b" * 64, "actions": 10, "tasks": 2}}
            effect_calls = []
            def uncertain_effect(*arguments):
                self.assertTrue((Path(directory) / "canary-dispatch.json").is_file())
                effect_calls.append(arguments)
                raise canary.Failure("MCP_TRANSPORT_UNCERTAIN_NO_RETRY")
            with patch.object(sys, "argv", ["helper", "dispatch"]), patch.object(canary, "load_common", return_value=common), \
                 patch.object(canary, "pins_input", return_value=pins), \
                 patch.object(canary, "preflight", return_value=(None, "http://127.0.0.1", "secret-in-memory", {}, observed)), \
                 patch.object(canary, "call", side_effect=uncertain_effect):
                with self.assertRaises(canary.Failure) as first:
                    canary.main()
                self.assertEqual(first.exception.code, "MCP_TRANSPORT_UNCERTAIN_NO_RETRY")
                with self.assertRaises(canary.Failure) as second:
                    canary.main()
                self.assertEqual(second.exception.code, "IMMUTABLE_RECEIPT_ALREADY_EXISTS_NO_REPLAY")
            self.assertEqual(len(effect_calls), 1)

    def test_summary_passed_is_not_tap_or_native_acceptance(self):
        family, marker, pins, _ = proof_family()
        value = canary.verified_payload(family, marker, pins)
        self.assertEqual(value["checker_4_of_4"], "not_observed_here")
        self.assertEqual(value["native_proof_correlation"], "root_local_read_only_verifier_required")
        self.assertNotIn("runtime_identity", value)
        self.assertNotIn("policy_sha256", value)
        self.assertNotIn("local_handle", value)

    def test_changed_instance_plan_digest_and_historical_run_refused(self):
        for field, changed in (("runtime_identity", {"activation_epoch_id": "wrong"}),
                               ("run_id", canary.OLD_RUN), ("response_sha256", "0" * 64)):
            family, marker, pins, payload = proof_family()
            payload[field] = changed
            family["receipt"]["payload_json"] = json.dumps(payload)
            with self.assertRaises(canary.Failure):
                canary.verified_payload(family, marker, pins)
        family, marker, pins, payload = proof_family()
        payload["initial_verification"]["plan_sha256"] = "0" * 64
        family["receipt"]["payload_json"] = json.dumps(payload)
        with self.assertRaises(canary.Failure):
            canary.verified_payload(family, marker, pins)

    def test_failed_proof_never_has_passed_fingerprint(self):
        family, marker, pins, payload = proof_family("failed")
        self.assertIsNone(canary.verified_payload(family, marker, pins)["initial_verification"]["proof_fingerprint"])
        payload["initial_verification"]["proof_fingerprint"] = "a" * 64
        family["receipt"]["payload_json"] = json.dumps(payload)
        with self.assertRaises(canary.Failure):
            canary.verified_payload(family, marker, pins)

    def test_null_or_non_string_command_id_refused(self):
        for value in (None, True, 123):
            family, marker, pins, payload = proof_family()
            payload["initial_verification"]["command_id"] = value
            family["receipt"]["payload_json"] = json.dumps(payload)
            with self.assertRaises(canary.Failure):
                canary.verified_payload(family, marker, pins)

    def test_failed_before_job_can_be_reported_without_invented_job_id(self):
        family, marker, pins, payload = proof_family("failed")
        del payload["initial_verification"]["command_id"]
        del payload["initial_verification"]["job_id"]
        payload["response_sha256"] = canary.digest({"file": payload["file"], "initial_verification": payload["initial_verification"]})
        family["receipt"]["payload_json"] = json.dumps(payload)
        self.assertNotIn("job_id", canary.verified_payload(family, marker, pins)["initial_verification"])

    def test_unknown_or_running_effect_refuses_cleanup(self):
        for state in ("accepted", "queued", "reconcile_required"):
            family, marker, pins, _ = proof_family()
            family.update(settled=False, state=state)
            with self.assertRaises(canary.Failure) as error:
                canary.verified_payload(family, marker, pins)
            self.assertEqual(error.exception.code, "ACTION_NOT_SETTLED_NO_CLEANUP")

    def test_raw_receipt_never_enters_public_family(self):
        family, _, _, _ = proof_family()
        family["receipt"]["payload_json"] = "Bearer SHOULD_NOT_LEAK"
        self.assertNotIn("SHOULD_NOT_LEAK", json.dumps(canary.public_family(family)))

    def test_transport_failure_is_typed_without_raw_response_or_secret(self):
        with patch.object(canary.urllib.request, "urlopen", side_effect=OSError("Bearer SHOULD_NOT_LEAK")):
            with self.assertRaises(canary.Failure) as error:
                canary.rpc("http://127.0.0.1:8766", "Bearer SHOULD_NOT_LEAK", "tools/list", {})
        self.assertEqual(error.exception.code, "MCP_TRANSPORT_UNCERTAIN_NO_RETRY")
        self.assertNotIn("SHOULD_NOT_LEAK", str(error.exception.code))

    def test_runtime_change_or_expired_trial_refused(self):
        now = 200000
        common = types.SimpleNamespace(REVISION="revision", PACKAGE="package", DEVICE="device",
                                      renewed_authority=lambda overview, pins: canary.require(overview["observed_at_ms"] < pins["expires_at_ms"], "EXPIRED"))
        pins = {"service_instance_id": "service", "activation_epoch": "epoch", "runtime_instance_id": "runtime",
                "mcp_server_instance_id": "mcp", "contract_version": "contract", "expires_at_ms": now + 300000}
        health = {"declared_source_revision": "revision", "schema_version": 29, "ok": True,
                  "package_source_sha256": "package", "expected_package_source_sha256": "package", "service_instance_id": "service"}
        node = {"device_id": "device", "activation_epoch": "epoch", "runtime_instance_id": "runtime",
                "mcp_server_instance_id": "mcp", "contract_version": "contract", "readiness": "ready",
                "policy_state": "enabled", "last_seen_at_ms": now, "policy_expires_at_ms": now + 50000}
        overview = {"observed_at_ms": now, "admission": {"admission_mode": "scoped_pilot"}, "nodes": [node]}
        grant = {"expires_at_ms": pins["expires_at_ms"]}
        canary.authority_guard(common, pins, health, overview, grant, dispatch=False)
        # Standing policy telemetry has a short TTL separate from the exact
        # 60m context/pilot/grant authority. Fresh 50s TTL must be admitted.
        self.assertLess(node["policy_expires_at_ms"], pins["expires_at_ms"])
        for expiry in (now, now - 1, now + 60001, None, True):
            node["policy_expires_at_ms"] = expiry
            with self.assertRaises(canary.Failure) as error:
                canary.authority_guard(common, pins, health, overview, grant, dispatch=False)
            self.assertEqual(error.exception.code, "NODE_NOT_READY_OR_POLICY_TELEMETRY_EXPIRED")
        node["policy_expires_at_ms"] = now + 50000
        node["activation_epoch"] = "changed"
        with self.assertRaises(canary.Failure):
            canary.authority_guard(common, pins, health, overview, grant, dispatch=False)
        node["activation_epoch"] = "epoch"
        overview["observed_at_ms"] = pins["expires_at_ms"]
        with self.assertRaises(canary.Failure):
            canary.authority_guard(common, pins, health, overview, grant, dispatch=False)


if __name__ == "__main__":
    unittest.main(verbosity=2)
