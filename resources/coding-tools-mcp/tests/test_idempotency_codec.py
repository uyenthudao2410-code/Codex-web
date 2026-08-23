from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from coding_tools_mcp.idempotency_codec import secret_key_findings
from coding_tools_mcp.orchestration_ledger import OrchestrationLedger


class IdempotencyCodecTests(unittest.TestCase):
    def test_new_large_summary_round_trips_through_zlib_and_scalar_columns(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            key, request_hash = "codec", "a" * 64
            self.assertTrue(ledger.claim_idempotency(idempotency_key=key, operation="agent_workflow", request_hash=request_hash, process_instance_id="process")["claimed"])
            summary = {"error_code": "PATCH_CONTEXT_AMBIGUOUS", "workflow_patch_preflight": 1, "details": "repeatable-data-" * 500}
            updated = ledger.finish_idempotency(key, request_hash=request_hash, status="failed", summary=summary)
            self.assertIsNotNone(updated)
            self.assertEqual(updated["summary"], summary)
            with ledger._connect() as connection:
                row = connection.execute("SELECT summary_json,error_code,workflow_patch_preflight,summary_codec,summary_blob FROM idempotency_records WHERE idempotency_key=?", (key,)).fetchone()
            self.assertEqual(row["summary_json"], "{}")
            self.assertEqual(row["summary_codec"], "zlib_json")
            self.assertEqual(row["error_code"], "PATCH_CONTEXT_AMBIGUOUS")
            self.assertEqual(row["workflow_patch_preflight"], 1)
            self.assertGreater(len(bytes(row["summary_blob"])), 0)
            self.assertEqual(ledger.get_idempotency(key)["summary"], summary)

    def test_legacy_plain_summary_and_orphan_transition_remain_readable(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            with ledger._connect() as connection:
                connection.execute("""INSERT INTO idempotency_records(
                    idempotency_key,operation,request_hash,status,process_instance_id,started_at,updated_at,summary_json
                ) VALUES(?,?,?,?,?,?,?,?)""", ("legacy", "agent_workflow", "hash", "in_progress", "old", "now", "now", json.dumps({"legacy": True})))
            self.assertEqual(ledger.get_idempotency("legacy")["summary"], {"legacy": True})
            self.assertEqual(ledger.mark_orphaned_idempotency(current_process_instance_id="new"), 1)
            self.assertEqual(ledger.get_idempotency("legacy")["summary"]["outcome_unknown_reason"], "mcp_process_restarted")

    def test_codec_aware_secret_scan_inspects_decompressed_summary_keys(self) -> None:
        self.assertEqual(secret_key_findings({"nested": {"api_token": "raw-secret"}}), ["api_token"])
        self.assertEqual(secret_key_findings({"nested": {"api_token": "[REDACTED]", "fencing_token": 3}}), [])


if __name__ == "__main__":
    unittest.main()
