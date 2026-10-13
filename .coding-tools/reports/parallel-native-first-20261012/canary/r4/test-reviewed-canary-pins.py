"""Focused offline boundaries for combining reviewed canary evidence."""

import copy
import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location("reviewed_canary_pins", Path(__file__).with_name("prepare-reviewed-canary-pins.py"))
PINS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PINS)


class ReviewedEvidenceTests(unittest.TestCase):
    def evidence(self):
        now = 1_700_000_000_000
        contract = {"schema_version": 34, "profile": "reviewed-facade", "sha256": "a" * 64}
        server = {"ok": True, "service_stable": True, "source_startup_disk_attestation_matches": True,
            "sqlite_integrity_ok": True, "capture_completed_at_ms": now, "principal_id": "principal-reviewed",
            "service_pid": 123, "node": {"readiness": "ready", "revoked_at_ms": None, "last_seen_at_ms": now,
                "activation_epoch": "epoch-reviewed", "contract_version": "sha256:" + "b" * 64,
                "device_id": "device-reviewed", "runtime_instance_id": "process-reviewed", "mcp_server_instance_id": "server-reviewed"},
            "service_grant": {"live": True, "grant_id": "grant-reviewed"}, "tool_contract": contract,
            "serving_source": {"release_file_integrity_verified": True,
                "python_files_sha256": {name: "c" * 64 for name in ("mcp_facade.py", "node_agent.py", "store.py")}},
            "expected_current_scopes": {}, "delegated_inventory_targets": [], "live_pilots": []}
        approvals = {"observed_at_ms": now, "activation_epoch_id": "epoch-reviewed", "approval_set": "overlap", "targets": []}
        manifest = {"prepared": True, "targets": []}
        for index, label in enumerate(("Codex-web", "Autocad")):
            binding = {"binding_id": "binding-reviewed-" + str(index), "workspace_id": "workspace-reviewed-" + str(index),
                       "workspace_generation": "generation-reviewed-" + str(index)}
            server["expected_current_scopes"][label] = {"active_bindings": [binding], "active_registrations": [binding.copy()]}
            server["delegated_inventory_targets"].append({**binding, "readiness": "ready", "presence_state": "online", "dispatch_state": "dispatchable"})
            server["live_pilots"].append({**binding, "principal_id": server["principal_id"],
                                       "decision_id": "pilot-reviewed-" + str(index), "expires_at_ms": now + 3_600_000})
            approval = {**binding, "workspace_label": label, "native_source_sha256": str(index + 1) * 64,
                "added_native_argv": ["node", "tests/fixtures/parallel-native-overlap-20261012/hold.cjs"], "added_native_cwd": "",
                "policy": {"state": "enabled", "facade_contract": contract, "policy_sha256": str(index + 3) * 64}}
            approvals["targets"].append(approval)
            manifest["targets"].append({"workspace_label": label, "native_source_sha256": approval["native_source_sha256"],
                                       "native_argv": approval["added_native_argv"], "native_cwd": ""})
        quarantine = {"ok": True, "actions_settled": False, "actions_replayed": False,
                      "quarantined_action_ids": ["act_" + str(index) * 32 for index in range(3)]}
        return server, approvals, manifest, quarantine, now

    def construct(self, evidence, kind="overlap"):
        server, approvals, manifest, quarantine, now = evidence
        return PINS.construct(server, approvals, manifest, quarantine, kind, now)

    def test_overlap_pins_preserve_exact_runtime_targets_and_unknowns(self):
        evidence = self.evidence()
        pins = self.construct(evidence)
        self.assertEqual(pins["local_tool_contract_sha256"], "b" * 64)
        self.assertEqual(pins["activation_epoch"], evidence[1]["activation_epoch_id"])
        self.assertEqual(len({target["binding_id"] for target in pins["targets"]}), 2)
        self.assertNotIn("retained_unknown_actions", pins["targets"][0])
        self.assertEqual(pins["targets"][1]["retained_unknown_actions"], evidence[3]["quarantined_action_ids"])

    def test_stale_epoch_wrong_source_and_settled_unknown_fail_closed(self):
        mutations = [
            (lambda item: item[1].update(observed_at_ms=item[4] - 120001), "FRESH_SERVER_AND_APPROVAL"),
            (lambda item: item[1].update(activation_epoch_id="epoch-retired"), "APPROVAL_AND_HEARTBEAT_EPOCH_DIFFER"),
            (lambda item: item[2]["targets"][1].update(native_source_sha256="e" * 64), "EXACT_OVERLAP_FIXTURE_SOURCE"),
            (lambda item: item[3].update(actions_settled=True), "EXACT_PRESERVED_QUARANTINE"),
        ]
        for mutate, error in mutations:
            with self.subTest(error=error):
                evidence = self.evidence()
                mutate(evidence)
                with self.assertRaisesRegex(RuntimeError, error):
                    self.construct(evidence)

    def test_codex_build_requires_exact_source_argv_and_cwd(self):
        server, approvals, _, quarantine, now = self.evidence()
        approvals = copy.deepcopy(approvals)
        approvals["approval_set"] = "codex-build"
        approval = approvals["targets"][0]
        approval.update(added_native_argv=["node", "trusted-build.js"], added_native_cwd="tests/fixtures/native-first-canary")
        manifest = {"prepared": True, "fixture": "tests/fixtures/native-first-canary", "files": [
            {"path": "tests/fixtures/native-first-canary/trusted-build.js", "sha256": approval["native_source_sha256"]}]}
        evidence = server, {"receipt": approvals}, manifest, quarantine, now
        pins = self.construct(evidence, "codex-full")
        self.assertTrue(pins["trusted_build_explicitly_approved"])
        self.assertEqual(pins["workspace_label"], "Codex-web")
        self.assertNotIn("targets", pins)
        approval["added_native_cwd"] = ""
        with self.assertRaisesRegex(RuntimeError, "EXACT_CODEX_BUILD_APPROVAL"):
            self.construct(evidence, "codex-full")


if __name__ == "__main__":
    unittest.main()
