"""Focused checks for joining production receipts without a live action."""

import importlib.util
from pathlib import Path
import unittest


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("production_join", HERE / "build-production-final-evidence.py")
JOINER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(JOINER)


class ProductionJoinTests(unittest.TestCase):
    def test_retained_same_runtime_evidence_is_aggregated_truthfully(self):
        r4 = HERE.parent / "r4"
        root = HERE.parent.parent
        args = type("Args", (), {
            "semantic": str(r4 / "semantic-independent-audit-20261013.json"),
            "overlap": str(r4 / "parallel-overlap-receipt-90307d8ef64b429aab250c9797538717.ndjson"),
            "idle": str(r4 / "isolated-idle-observation-a00b2f59ccb14bc68cb09dc4159f2237.json"),
            "policy": str(root / "final-policy-1791835447951-2c32b007.json"),
            "readiness": str(root / "server-readiness-completion-20261013-002.json"),
            "local_ready": str(root / "status-1791847175673-e8bc7ad6.json"),
            "discovery": str(HERE / "discovery-central-classification-20261013.json"),
            "joined": str(HERE / "native-first-continuation-evidence-join-20261013-v2.json"),
        })()
        report = JOINER.build(args)
        self.assertEqual(report["semantic_acceptance"]["source_final_audit_accepted_count"], 20)
        self.assertEqual(report["parallel_overlap"]["overlap"]["overlap_duration_ms"], 2078)
        self.assertEqual(report["native_continuation"]["combined_proof_counts"]["node_jobs"], 10)
        self.assertEqual(report["idle_observation"]["final_sandbox_working_set_bytes"], 0)
        self.assertEqual(report["ubuntu_readiness"]["connector_contract_state"], "CHANGED_NEEDS_DISCOVERY")
        self.assertEqual(report["ubuntu_readiness"]["connector_applicability"], "not_applicable_central_executor")
        self.assertEqual(report["remaining_acceptance_gates"][2]["status"], "closed_for_central_executor")
        self.assertEqual(report["ubuntu_readiness"]["scopes"]["Autocad"]["census"]["reconciliation_required_actions"], 3)
        self.assertFalse(report["windows_readiness"]["census_safe"])
        self.assertTrue(report["no_live_mutation_performed"])


if __name__ == "__main__":
    unittest.main()
