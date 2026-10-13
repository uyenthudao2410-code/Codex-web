"""Offline original-result lineage and no-active-work gates; no live requests."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("reviewed_read067_reconciliation", HERE / "reconcile-original-read067.py")
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


class ReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.server = json.loads((HERE.parent / "server-readiness-read067-unknown.json").read_text(encoding="utf-8-sig"))
        self.local = json.loads((HERE.parent / "local-read067-timeout-evidence.json").read_text(encoding="utf-8-sig"))
        self.now = self.server["capture_completed_at_ms"]
        self.journal = {"entries": {helper.ACTION + "|" + helper.ATTEMPT: {
            "action_id": helper.ACTION, "attempt_id": helper.ATTEMPT, "state": "unknown", "receipt": {
                "receipt_state": "unknown", "receipt_submitted": True, "local_handle": "",
                "payload": self.local["journal_projection"]["payload"]}}}}

    def test_original_unknown_becomes_only_conservative_rejected_payload(self):
        before = copy.deepcopy(self.journal)
        result = helper.prepare(self.server, self.local, self.journal, self.now)
        self.assertEqual(self.journal, before)
        self.assertEqual(result["original_unknown_receipt_id"], helper.RECEIPT)
        self.assertTrue(result["read_may_have_occurred"])
        self.assertFalse(result["read_success_claimed"])
        self.assertFalse(result["valid_bounded_read_receipt_retained"])
        self.assertFalse(result["action_redispatched"])
        self.assertNotIn("content", result)

    def test_changed_original_receipt_or_attempt_rejected(self):
        for mutation in ("receipt", "settled", "second_attempt", "scope"):
            server = copy.deepcopy(self.server)
            row = next(item for item in server["historical_unknown_actions_preserved"] if item["action_id"] == helper.ACTION)
            if mutation == "receipt":
                row["receipts"][0]["receipt_digest"] = "0" * 64
            elif mutation == "settled":
                row["delivery_state"] = "settled"
            elif mutation == "second_attempt":
                row["delivery_attempts"].append(copy.deepcopy(row["delivery_attempts"][0]))
            else:
                row["workspace_generation"] = "other_generation"
            with self.subTest(mutation=mutation), self.assertRaises(RuntimeError):
                helper.prepare(server, self.local, self.journal, self.now)

    def test_stale_or_different_server_runtime_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "FRESH_EXACT_SERVER"):
            helper.prepare(self.server, self.local, self.journal, self.now + 120001)
        server = copy.deepcopy(self.server)
        server["node"]["mcp_server_instance_id"] = "other_server"
        with self.assertRaisesRegex(RuntimeError, "EXACT_CURRENT_SERVER_NODE"):
            helper.prepare(server, self.local, self.journal, self.now)

    def test_local_completed_or_payload_drift_cannot_repair_unknown(self):
        for mutation in ("completed", "payload", "handle"):
            journal = copy.deepcopy(self.journal)
            receipt = journal["entries"][helper.ACTION + "|" + helper.ATTEMPT]["receipt"]
            receipt[{"completed": "receipt_state", "payload": "payload", "handle": "local_handle"}[mutation]] = {
                "completed": "completed", "payload": {"code": "success"}, "handle": "new_handle"}[mutation]
            with self.subTest(mutation=mutation), self.assertRaises(RuntimeError):
                helper.prepare(self.server, self.local, journal, self.now)

    def test_controller_gate_requires_exact_fresh_binding_and_idle_census(self):
        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory)
            files = {name: "1" for name in ("Coding Tools MCP.exe", "resources/app.asar", "resources/resources/control-plane/node_agent.py")}
            for name in files:
                (candidate / name).parent.mkdir(parents=True, exist_ok=True)
                (candidate / name).write_text("proof", encoding="utf-8")
                files[name] = hashlib.sha256((candidate / name).read_bytes()).hexdigest()
            gate = {"operation": "original-read067-reconciliation-gate", "ok": True, "candidate": str(candidate),
                "observed_at_ms": self.now, "receipt": {"action_id": helper.ACTION, "attempt_id": helper.ATTEMPT,
                "runtime_identity": helper.EXPECTED_RUNTIME, "server_evidence_sha256": "server", "local_evidence_sha256": "local",
                "local_journal_sha256": "journal", "helper_sha256": hashlib.sha256((HERE / "reconcile-original-read067.py").read_bytes()).hexdigest(),
                "package_sha256": files, "census": {"content_free": True, "mutated_canonical_ledger": False,
                "lifecycle": {"blockers": ["live_runtime_state_process"], "unexplained_active_runs": 0, "unbound_live_resource_residues": 0},
                "counts": dict.fromkeys(("active_tool_calls", "active_commands", "starting_commands", "active_background_operations",
                    "active_managed_processes", "foreign_heavy_processes", "active_agent_lanes", "owned_codex_sidecar_residues"), 0)}}}
            helper.validate_gate(gate, candidate, "server", "local", "journal", self.now)
            for mutation in ("stale", "active", "journal", "package"):
                changed = copy.deepcopy(gate)
                if mutation == "stale":
                    changed["observed_at_ms"] -= 60001
                elif mutation == "active":
                    changed["receipt"]["census"]["counts"]["active_tool_calls"] = 1
                elif mutation == "journal":
                    changed["receipt"]["local_journal_sha256"] = "other"
                else:
                    changed["receipt"]["package_sha256"].pop("resources/app.asar")
                with self.subTest(mutation=mutation), self.assertRaises(RuntimeError):
                    helper.validate_gate(changed, candidate, "server", "local", "journal", self.now)


if __name__ == "__main__":
    unittest.main()
