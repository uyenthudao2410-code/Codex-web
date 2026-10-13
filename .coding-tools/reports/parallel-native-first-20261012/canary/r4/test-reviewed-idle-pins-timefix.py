"""Offline boundaries for actual isolated and native-first policy evidence."""
import copy
import importlib.util
from pathlib import Path
import unittest


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(file))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


IDLE = load("idle_pins", "prepare-reviewed-idle-pins-timefix.py")
BASE_TESTS = load("canary_evidence", "test-reviewed-canary-pins.py")


class ActualIdleEvidenceTests(unittest.TestCase):
    def evidence(self):
        server, approvals, _, quarantine, now = BASE_TESTS.ReviewedEvidenceTests().evidence()
        policies = []
        for item in approvals["targets"]:
            policy = {**item["policy"], "workspace_id": item["workspace_id"],
                      "workspace_generation": item["workspace_generation"], "execution_mode": "native_first"}
            item["policy"] = policy
            policies.append(copy.deepcopy(policy))
        common = {"candidate": "E:/DEV/Codex-web/dist/windows-candidate-mxc-wsb-cbe1774-parallel-r4-timefix/win-unpacked", "parity_sha256": "a" * 64,
                  "smoke_sha256": "b" * 64, "activation_epoch_id": "epoch-reviewed",
                  "owner_instance_id": "owner-reviewed", "other_scope_sha256": "c" * 64}
        final = {"ok": True, "operation": "final-policy", "candidate": common["candidate"],
                 "parity_proof_sha256": common["parity_sha256"], "smoke_proof_sha256": common["smoke_sha256"],
                 "receipt": {"activation_epoch_id": common["activation_epoch_id"], "targets": approvals["targets"]}}
        plan = {**common, "ok": True, "operation": "isolated-idle-policy-plan", "mutations": 0,
                "before": policies, "_file_sha256": "d" * 64}
        isolated = {**common, "ok": True, "operation": "isolated-idle-policy-isolate",
                    "observed_at_ms": now, "other_scope_unchanged": True,
                    "plan_sha256": plan["_file_sha256"], "after": {
                        **policies[0], "execution_mode": "isolated", "policy_sha256": "e" * 64}}
        local_state = {"nativeActivationEpochId": common["activation_epoch_id"], "nativeInstanceId": "1" * 24,
                       "nativePid": 50724, "nativeProcessStartToken": "134362825928499830",
                       "nativeModuleRoot": common["candidate"] + "/resources/resources/coding-tools-mcp"}
        local_epoch = {"current": {"activation_epoch_id": common["activation_epoch_id"],
                                   "state": "READY", "admission_state": "OPEN"}}
        return server, final, isolated, plan, quarantine, now, local_state, local_epoch

    def test_actual_modes_and_digests_without_native_fixture_approval(self):
        evidence = self.evidence()
        pins = IDLE.construct(*evidence)
        self.assertEqual(pins["purpose"], "isolated-idle")
        self.assertTrue(pins["no_native_fixture_approval_claim"])
        self.assertEqual([item["execution_mode"] for item in pins["targets"]], ["isolated", "native_first"])
        self.assertEqual(pins["targets"][0]["exec_policy_sha256"], evidence[2]["after"]["policy_sha256"])
        self.assertEqual(pins["targets"][1]["retained_unknown_actions"], evidence[4]["quarantined_action_ids"])
        for item in pins["targets"]:
            self.assertNotIn("native_fixture_explicitly_approved", item)
            self.assertNotIn("native_source_sha256", item)
            self.assertNotIn("native_argv", item)
        self.assertEqual(pins["serving_node_agent_sha256"], "c" * 64)
        self.assertEqual(pins["supervisor_instance_id"], "1" * 24)
        self.assertEqual(pins["process_instance_id"], "process-reviewed")
        self.assertNotEqual(pins["supervisor_instance_id"], pins["process_instance_id"])

    def test_stale_readiness_wrong_policy_scope_and_modified_other_scope_fail(self):
        cases = [
            (lambda value: value[0].update(capture_completed_at_ms=value[5] - 120001), "FRESH_SERVER_READINESS"),
            (lambda value: value[2].update(observed_at_ms=value[5] - 120001), "FRESH_ISOLATED_POLICY"),
            (lambda value: value[2]["after"].update(workspace_generation="different"), "EXACT_CURRENT_IDLE_POLICY"),
            (lambda value: value[2].update(other_scope_sha256="f" * 64), "EXACT_ISOLATE_PLAN"),
            (lambda value: value[0]["delegated_inventory_targets"][0].update(workspace_generation="different"), "EXACT_CURRENT_TARGET"),
            (lambda value: value[0]["live_pilots"][0].update(expires_at_ms=value[5]), "EXACT_CURRENT_PILOT"),
            (lambda value: value[4].update(actions_settled=True), "EXACT_PRESERVED_QUARANTINE"),
            (lambda value: value[6].update(nativeInstanceId="process-reviewed"), "EXACT_CURRENT_LOCAL_SUPERVISOR"),
            (lambda value: value[6].update(nativeModuleRoot="other-module"), "EXACT_CURRENT_LOCAL_SUPERVISOR"),
            (lambda value: value[7]["current"].update(admission_state="CLOSED"), "EXACT_CURRENT_LOCAL_SUPERVISOR"),
        ]
        for mutate, code in cases:
            with self.subTest(code=code):
                evidence = self.evidence()
                mutate(evidence)
                with self.assertRaisesRegex(RuntimeError, code):
                    IDLE.construct(*evidence)

    def test_real_registration_has_scope_without_binding_id(self):
        evidence = self.evidence()
        for scope in evidence[0]["expected_current_scopes"].values():
            scope["active_registrations"][0].pop("binding_id")
        self.assertEqual(len(IDLE.construct(*evidence)["targets"]), 2)


if __name__ == "__main__":
    unittest.main()
