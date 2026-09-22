import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "resources" / "coding-tools-mcp"
sys.path.insert(0, str(PACKAGE))


def load_script(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rehearsal = load_script("rehearsal_for_candidate_audit", ROOT / "scripts" / "rehearse-ledger-recovery.py")
audit = load_script("audit_candidate", ROOT / "scripts" / "audit-ledger-recovery-candidate.py")

from coding_tools_mcp.orchestration_ledger import OrchestrationLedger  # noqa: E402


class RecoveryCandidateAuditTests(unittest.TestCase):
    def test_clone_append_and_duplicate_probes_are_isolated(self):
        with tempfile.TemporaryDirectory(prefix="candidate-audit-test-") as temp:
            root = Path(temp)
            current_root = root / "current"
            historical_root = root / "historical"
            current_ledger = OrchestrationLedger(current_root)
            current_run = current_ledger.create_run(objective="current")
            current_wave = current_ledger.create_wave(current_run, execution_mode="mcp_only")
            current_ledger.append_event(current_run, wave_id=current_wave, event_type="current_event")

            current_path = current_root / ".coding-tools" / "orchestration" / "ledger.sqlite3"
            historical_root.mkdir()
            historical_path = historical_root / ".coding-tools" / "orchestration" / "ledger.sqlite3"
            historical_path.parent.mkdir(parents=True)
            shutil.copyfile(current_path, historical_path)
            historical_ledger = OrchestrationLedger(historical_root)
            recovered_run = historical_ledger.create_run(objective="historical")
            recovered_wave = historical_ledger.create_wave(recovered_run, execution_mode="mcp_only")
            historical_ledger.append_event(recovered_run, wave_id=recovered_wave, event_type="historical_event")

            candidate_path = root / "candidate.sqlite3"
            rehearsal_result = rehearsal.rehearse(current_path, historical_path, candidate_path, {recovered_run})
            self.assertFalse(rehearsal_result["activation_eligible"])
            before_current = rehearsal.sha(current_path)
            before_candidate = rehearsal.sha(candidate_path)
            result = audit.audit(
                current_path,
                candidate_path,
                historical_path,
                {recovered_run},
                {
                    "current": before_current,
                    "candidate": before_candidate,
                    "historical": rehearsal.sha(historical_path),
                },
            )
            self.assertTrue(result["current_rows_preserved"])
            self.assertTrue(result["authority_preserved"])
            self.assertTrue(result["event_chains"]["candidate"]["valid"])
            self.assertTrue(result["append_duplicate_authority_probe"]["valid"])
            self.assertEqual(rehearsal.sha(current_path), before_current)
            self.assertEqual(rehearsal.sha(candidate_path), before_candidate)
            self.assertFalse(result["activation_eligible"])


if __name__ == "__main__":
    unittest.main()
