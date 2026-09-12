from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from coding_tools_mcp.server import Runtime


class ProofCacheSourceBindingTests(unittest.TestCase):
    @staticmethod
    def _owner(runtime: Runtime, label: str) -> tuple[str, str]:
        run_id = runtime.orchestration_ledger.create_run(objective=f"proof cache source binding {label}")
        wave_id = runtime.orchestration_ledger.create_wave(
            run_id,
            execution_mode="mcp_only",
            base_head="fixture-head",
            worktree_fp="fixture-worktree",
        )
        return run_id, wave_id

    def test_exact_source_bytes_control_cache_reuse_and_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "existing.py"
            source.write_bytes(b"VALUE = 1\n")
            runtime = Runtime(root, permission_mode="dangerous")
            calls = {"count": 0}

            def runner() -> dict[str, object]:
                calls["count"] += 1
                return {"ok": True, "status": "passed", "exit_code": 0, "duration_ms": 7}

            def identity() -> tuple[str, dict[str, object]]:
                binding = runtime.proof_ledger.source_binding(
                    base_head="fixture-head",
                    contract_fp="fixture-contract",
                    input_paths=["existing.py"],
                )
                fingerprint = runtime.proof_ledger.fingerprint(
                    stage_id="verify:tests",
                    base_head="fixture-head",
                    worktree_fp="fixture-worktree",
                    contract_fp="fixture-contract",
                    input_paths=["existing.py"],
                    config={"verification": "tests", "test_command": "fixture"},
                )
                return fingerprint, binding

            try:
                first_fp, first_binding = identity()
                first_run, first_wave = self._owner(runtime, "first")
                first, first_proof_id = runtime.proof_ledger.run_cached(
                    run_id=first_run,
                    wave_id=first_wave,
                    stage_id="verify:tests",
                    input_fingerprint=first_fp,
                    command="fixture",
                    runner=runner,
                    metadata={"proof_source_binding": first_binding},
                )
                self.assertFalse(first["cache_hit"])
                self.assertEqual(calls["count"], 1)

                same_fp, same_binding = identity()
                self.assertEqual(same_fp, first_fp)
                self.assertEqual(same_binding, first_binding)
                second_run, second_wave = self._owner(runtime, "same-bytes")
                second, second_proof_id = runtime.proof_ledger.run_cached(
                    run_id=second_run,
                    wave_id=second_wave,
                    stage_id="verify:tests",
                    input_fingerprint=same_fp,
                    command="fixture",
                    runner=runner,
                    metadata={"proof_source_binding": same_binding},
                )
                self.assertTrue(second["cache_hit"])
                self.assertEqual(calls["count"], 1)
                self.assertEqual(second["proof_cache_source_proof_id"], first_proof_id)
                self.assertNotEqual(second_proof_id, first_proof_id)
                reuse_proof = runtime.orchestration_ledger.list_proofs(
                    second_run, wave_id=second_wave
                )[0]
                self.assertEqual(
                    reuse_proof["metadata"]["proof_source_binding"],
                    same_binding,
                )
                self.assertEqual(
                    reuse_proof["metadata"]["proof_reuse"]["source_proof_id"],
                    first_proof_id,
                )

                source.write_bytes(b"VALUE = 2\n")
                changed_fp, changed_binding = identity()
                self.assertNotEqual(changed_binding["path_fingerprint"], first_binding["path_fingerprint"])
                self.assertNotEqual(changed_fp, first_fp)

                third_run, third_wave = self._owner(runtime, "changed-bytes")
                third, third_proof_id = runtime.proof_ledger.run_cached(
                    run_id=third_run,
                    wave_id=third_wave,
                    stage_id="verify:tests",
                    input_fingerprint=changed_fp,
                    command="fixture",
                    runner=runner,
                    metadata={"proof_source_binding": changed_binding},
                )
                self.assertFalse(third["cache_hit"])
                self.assertEqual(calls["count"], 2)
                self.assertNotEqual(third_proof_id, first_proof_id)
                changed_proof = runtime.orchestration_ledger.list_proofs(
                    third_run, wave_id=third_wave
                )[0]
                self.assertEqual(
                    changed_proof["metadata"]["proof_source_binding"],
                    changed_binding,
                )
            finally:
                runtime.close()


if __name__ == "__main__":
    unittest.main()
