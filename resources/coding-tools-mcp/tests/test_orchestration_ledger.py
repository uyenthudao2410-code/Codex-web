from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from coding_tools_mcp.orchestration_ledger import OrchestrationLedger


class OrchestrationLedgerTests(unittest.TestCase):
    def test_events_survive_restart_and_hash_chain_verifies(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            run_id = ledger.create_run(objective="ship behavior", task_id="task-1")
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only", base_head="abc", worktree_fp="fp")
            ledger.append_event(run_id, wave_id=wave_id, event_type="preflight", state_after="PREFLIGHT")
            ledger.append_event(run_id, wave_id=wave_id, event_type="ready", state_before="PREFLIGHT", state_after="READY")

            restored = OrchestrationLedger(root)
            events = restored.list_events(run_id)
            self.assertEqual([item["event_type"] for item in events], ["preflight", "ready"])
            integrity = restored.verify_chain(run_id)
            self.assertTrue(integrity["ok"])
            self.assertEqual(integrity["checked"], 2)

    def test_sensitive_payload_is_redacted_but_identity_remains(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(objective="safe audit")
            wave_id = ledger.create_wave(run_id, execution_mode="bounded_candidate")
            ledger.append_event(
                run_id,
                wave_id=wave_id,
                event_type="model_dispatch_started",
                payload={"prompt": "super secret prompt", "api_token": "secret-token", "model": "gpt-test"},
            )
            payload = ledger.list_events(run_id)[0]["payload"]
            self.assertEqual(payload["api_token"], "[REDACTED]")
            self.assertTrue(payload["prompt"]["redacted"])
            self.assertEqual(payload["model"], "gpt-test")
            self.assertEqual(len(payload["prompt"]["sha256"]), 64)

    def test_export_summary_includes_checkpoint_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(objective="accepted behavior", task_id="task-checkpoint")
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only", base_head="abc123", worktree_fp="fp")
            checkpoint_id = ledger.record_checkpoint(
                run_id=run_id,
                wave_id=wave_id,
                git_head="abc123",
                proof_fingerprint="proof-fp",
                status="accepted",
                metadata={"accepted_by": "ChatWeb Sol"},
            )

            summary = ledger.export_summary(run_id)

            self.assertEqual(len(summary["checkpoints"]), 1)
            checkpoint = summary["checkpoints"][0]
            self.assertEqual(checkpoint["checkpoint_id"], checkpoint_id)
            self.assertEqual(checkpoint["wave_id"], wave_id)
            self.assertEqual(checkpoint["git_head"], "abc123")
            self.assertEqual(checkpoint["proof_fingerprint"], "proof-fp")
            self.assertEqual(checkpoint["status"], "accepted")
            self.assertEqual(checkpoint["metadata"]["accepted_by"], "ChatWeb Sol")


if __name__ == "__main__":
    unittest.main()
