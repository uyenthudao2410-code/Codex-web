from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from coding_tools_mcp.orchestration_ledger import OrchestrationLedger
from coding_tools_mcp.proof_ledger import ProofLedger


class ProofLedgerTests(unittest.TestCase):
    def test_same_fingerprint_reuses_pass_and_change_invalidates(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "app.py"
            source.write_text("VALUE = 1\n", encoding="utf-8")
            ledger = OrchestrationLedger(root)
            proof = ProofLedger(root, ledger)
            run_id = ledger.create_run(objective="prove")
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only", base_head="base", worktree_fp="work")
            calls = {"count": 0}

            def runner() -> dict:
                calls["count"] += 1
                return {"ok": True, "status": "passed", "exit_code": 0, "duration_ms": 7, "summary": "green"}

            fp1 = proof.fingerprint(
                stage_id="focused",
                base_head="base",
                worktree_fp="work",
                input_paths=["app.py"],
                config={"command": "test"},
            )
            first, first_id = proof.run_cached(
                run_id=run_id,
                wave_id=wave_id,
                stage_id="focused",
                input_fingerprint=fp1,
                command="test",
                runner=runner,
            )
            second, second_id = proof.run_cached(
                run_id=run_id,
                wave_id=wave_id,
                stage_id="focused",
                input_fingerprint=fp1,
                command="test",
                runner=runner,
            )
            self.assertEqual(calls["count"], 1)
            self.assertFalse(first["cache_hit"])
            self.assertTrue(second["cache_hit"])
            self.assertEqual(first_id, second_id)
            self.assertEqual(second["summary"], "green")

            source.write_text("VALUE = 2\n", encoding="utf-8")
            fp2 = proof.fingerprint(
                stage_id="focused",
                base_head="base",
                worktree_fp="work-2",
                input_paths=["app.py"],
                config={"command": "test"},
            )
            self.assertNotEqual(fp1, fp2)
            third, _ = proof.run_cached(
                run_id=run_id,
                wave_id=wave_id,
                stage_id="focused",
                input_fingerprint=fp2,
                command="test",
                runner=runner,
            )
            self.assertFalse(third["cache_hit"])
            self.assertEqual(calls["count"], 2)


if __name__ == "__main__":
    unittest.main()
