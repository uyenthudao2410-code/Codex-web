from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts/reconcile_execution_resources.py"
SPEC = importlib.util.spec_from_file_location("reconcile_execution_resources_script", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
reconcile_script = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reconcile_script)


def sidecar_row(**overrides):
    row = {
        "job_id": "sidecar-job",
        "run_id": "",
        "wave_id": "",
        "command_id": "codex-app-server-test",
        "owner": "codex-app-server",
        "resource_class": "MEDIUM",
        "root_pid": 4242,
        "root_process_token": "token-4242",
        "lifecycle_state": "running",
    }
    row.update(overrides)
    return row


class FakeGovernor:
    def __init__(self, row):
        self.rows = [row]

    def reconcile(self):
        if getattr(self, "terminated", False):
            self.rows = []
        return {"quiesced": 0, "orphaned": 0}

    def _rows(self, *, active_only=False):
        return list(self.rows)


def test_select_owned_codex_sidecar_requires_exact_unique_identity_and_no_claims():
    row = sidecar_row()
    selected, reason = reconcile_script._select_owned_codex_sidecar([row], [])
    assert selected is row
    assert reason == "eligible"

    assert reconcile_script._select_owned_codex_sidecar([row, sidecar_row(job_id="other")], [])[0] is None
    assert reconcile_script._select_owned_codex_sidecar([row], [{"claim_id": "busy"}])[0] is None
    assert reconcile_script._select_owned_codex_sidecar([sidecar_row(owner="other")], [])[0] is None
    assert reconcile_script._select_owned_codex_sidecar([sidecar_row(root_process_token="")], [])[0] is None


def test_repair_refuses_identity_mismatch_without_termination():
    row = sidecar_row()
    governor = FakeGovernor(row)
    terminated = []
    result = reconcile_script.repair_owned_codex_sidecar(
        governor,
        [row],
        [],
        is_alive=lambda _pid: True,
        identity_token=lambda _pid: "different-token",
        terminate_tree=lambda pid: terminated.append(pid) or True,
    )
    assert result == {
        "attempted": False,
        "repaired": False,
        "reason": "process_identity_mismatch",
    }
    assert terminated == []


def test_repair_verified_sidecar_terminates_exact_pid_and_reconciles():
    row = sidecar_row()
    governor = FakeGovernor(row)
    alive = {4242: True}

    def terminate(pid):
        assert pid == 4242
        alive[pid] = False
        governor.terminated = True
        return True

    result = reconcile_script.repair_owned_codex_sidecar(
        governor,
        [row],
        [],
        is_alive=lambda pid: alive.get(pid, False),
        identity_token=lambda _pid: "token-4242",
        terminate_tree=terminate,
    )
    assert result == {"attempted": True, "repaired": True, "reason": "repaired"}
    assert governor._rows(active_only=True) == []
