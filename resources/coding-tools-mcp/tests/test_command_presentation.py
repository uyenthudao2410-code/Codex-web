from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from coding_tools_mcp.execution_resources import ExecutionResourceError
from coding_tools_mcp.live_control import live_control_snapshot
from coding_tools_mcp.server import Runtime
from coding_tools_mcp.task_state import command_presentation


class CommandPresentationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.runtime = Runtime(self.root)
        state = self.runtime.task_state.update({"objective": "Command presentation", "status": "active"})
        self.ctx = self.runtime.orchestration_control.begin(
            objective="Command presentation",
            task_id=state["task_id"],
            execution_mode="mcp_only",
            base_head="fixture-head",
            worktree_fp="fixture-fingerprint",
        )
        self.runtime.task_state.set_orchestration_projection(self.ctx.projection())
        self.command_id = "presentation-command"
        self.admission = self.runtime.execution_resource_governor.admit(
            command="git rev-parse HEAD",
            command_id=self.command_id,
            run_id=self.ctx.run_id,
            wave_id=self.ctx.wave_id,
            resource_class="LIGHT",
        )
        self.runtime.task_state.record_command_started(
            "git rev-parse HEAD",
            self.command_id,
            ".",
            owner_run_id=self.ctx.run_id,
            owner_wave_id=self.ctx.wave_id,
        )

    def tearDown(self) -> None:
        self.runtime.close()
        self.temp.cleanup()

    def _finish(self, *, lifecycle: str = "exited", exit_code: int | None = 0) -> None:
        self.runtime.execution_resource_governor.complete(
            self.admission.job_id, lifecycle_state=lifecycle, exit_code=exit_code
        )

    def _present(self, state: dict | None = None, *, workspace: Path | None = None) -> dict:
        return command_presentation(
            self.runtime.task_state.get() if state is None else state,
            governor=self.runtime.execution_resource_governor,
            workspace=self.root if workspace is None else workspace,
        )

    def _readers(self) -> tuple:
        return (
            ("task_control_get", lambda: self.runtime.task_control({"action": "get"})["state"]),
            ("task_state_get", lambda: self.runtime.task_state_get({})["state"]),
            ("live_control", lambda: live_control_snapshot(self.runtime, client_online_seconds=45)["task"]),
        )

    def test_get_suppresses_terminal_command_without_live_handle_or_poll(self) -> None:
        self._finish()
        self.assertEqual(self.runtime.sessions, {})
        self.assertEqual(self.runtime.output_sessions, {})
        state = self.runtime.task_control({"action": "get"})["state"]
        self.assertIsNone(state["current_command"])
        self.assertEqual(state["current_command_observation"]["result_status"], "succeeded")

    def test_all_readers_are_repeatable_without_persisting_results_events_or_reports(self) -> None:
        self._finish()
        self.runtime.task_state.set_completion_report({
            "source_run_wave": {"run_id": self.ctx.run_id, "wave_id": self.ctx.wave_id},
            "accepted_or_not": "EXISTING_REPORT",
            "current_state": {},
        })
        before = self.runtime.task_state.get()
        store = self.runtime.task_state._current_store()
        before_bytes = store.path.read_bytes()
        before_events = self.runtime.orchestration_ledger.list_events(self.ctx.run_id)
        for name, read in self._readers():
            with self.subTest(reader=name):
                first, second = read(), read()
                self.assertIsNone(first["current_command"])
                self.assertEqual(first["current_command_observation"], second["current_command_observation"])
                self.assertEqual(first["status"], before["status"])
                self.assertEqual(first["current_step"], before["current_step"])
                self.assertEqual(first["updated_at"], before["updated_at"])
                self.assertEqual(store.path.read_bytes(), before_bytes)
                self.assertEqual(self.runtime.task_state.get(), before)
                self.assertEqual(self.runtime.orchestration_ledger.list_events(self.ctx.run_id), before_events)

    def test_checkpoints_and_existing_results_are_preserved_even_when_exit_is_missing(self) -> None:
        self._finish(exit_code=None)
        state = self.runtime.task_state.get()
        state.update({
            "status": "completed", "current_step": "Completed", "next_step": "Existing action",
            "last_command_result": {"command_id": "earlier-command", "exit_code": 7},
            "test_results": [{"status": "passed"}], "build_results": [{"status": "failed"}],
            "completion_report": {"accepted_or_not": "ACCEPTED"}, "completion_report_id": "existing-report",
        })
        state["orchestration"]["orchestration_state"] = "CHECKPOINTED"
        before = copy.deepcopy(state)
        presented = self._present(state)
        self.assertIsNone(presented["current_command"])
        self.assertIsNone(presented["current_command_observation"]["exit_code"])
        self.assertEqual(presented["current_command_observation"]["result_status"], "unknown")
        for key in before.keys() - {"current_command"}:
            self.assertEqual(presented[key], before[key], key)
        self.assertEqual(state, before)

    def test_exact_active_job_remains_running_without_live_handle(self) -> None:
        self.assertEqual(self.runtime.sessions, {})
        for name, read in self._readers():
            with self.subTest(reader=name):
                presented = read()
                self.assertEqual(presented["current_command"]["status"], "running")
                self.assertEqual(presented["current_command_observation"]["status"], "active")
                self.assertEqual(presented["current_command_observation"]["result_status"], "running")

    def test_get_observes_terminalization_from_its_resource_snapshot(self) -> None:
        governor = self.runtime.execution_resource_governor
        snapshot = governor.snapshot

        def terminal_snapshot() -> dict:
            self._finish()
            return snapshot(reconcile=False)

        with patch.object(governor, "snapshot", side_effect=terminal_snapshot):
            result = self.runtime.task_control({"action": "get"})
        self.assertEqual(result["resources"]["active_command_count"], 0)
        self.assertIsNone(result["state"]["current_command"])

    def test_live_reader_does_not_reconcile_or_scan_process_census(self) -> None:
        self._finish()
        with (
            patch.object(self.runtime.execution_resource_governor, "reconcile", side_effect=AssertionError("no reconciliation")),
            patch.object(self.runtime, "_reconcile_task_orchestration_projection", side_effect=AssertionError("no projection repair")),
            patch("coding_tools_mcp.coordination.lifecycle_census", side_effect=AssertionError("no census")),
        ):
            result = live_control_snapshot(self.runtime, client_online_seconds=45)
        self.assertIsNone(result["task"]["current_command"])

    def test_live_reader_without_command_skips_command_presentation(self) -> None:
        state = self.runtime.task_state.get()
        state["current_command"] = None
        with (
            patch.object(self.runtime.task_state, "get", return_value=state),
            patch("coding_tools_mcp.live_control.command_presentation", side_effect=AssertionError("no command")),
        ):
            result = live_control_snapshot(self.runtime, client_online_seconds=45)
        self.assertIsNone(result["task"]["current_command"])
        self.assertIsNone(result["task"]["current_command_observation"])

    def test_exact_lookup_recovers_command_beyond_snapshot_history_cap(self) -> None:
        self._finish()
        governor = self.runtime.execution_resource_governor
        for index in range(22):
            admission = governor.admit(command="git status", command_id=f"later-{index}", resource_class="LIGHT")
            governor.complete(admission.job_id, lifecycle_state="exited", exit_code=0)
        snapshot = governor.snapshot(reconcile=False)
        self.assertNotIn(self.command_id, [job["command_id"] for job in snapshot["jobs"]])
        self.assertIsNone(self.runtime.task_control({"action": "get"})["state"]["current_command"])

    def test_unscoped_ordinary_command_keeps_existing_behavior_without_lookup(self) -> None:
        state = self.runtime.task_state.get()
        state["orchestration"] = {}
        state["current_command"].pop("owner_run")
        state["current_command"].pop("owner_wave")
        with patch.object(self.runtime.execution_resource_governor, "find_exact_job", side_effect=AssertionError("ordinary command")):
            self.assertEqual(self._present(state), state)

    def test_missing_or_mismatched_projection_identity_is_unknown(self) -> None:
        cases = (
            ("missing_command", "current_command", "session_id", ""),
            ("missing_owner", "current_command", "owner_wave", ""),
            ("foreign_owner", "current_command", "owner_run", "foreign-run"),
            ("missing_projection", "orchestration", "run_id", ""),
            ("foreign_projection", "orchestration", "wave_id", "foreign-wave"),
            ("conflicting_alias", "current_command", "command_id", "other-command"),
        )
        for name, field, key, value in cases:
            with self.subTest(case=name):
                state = self.runtime.task_state.get()
                state[field][key] = value
                with patch.object(self.runtime.execution_resource_governor, "find_exact_job", side_effect=AssertionError("invalid scope")):
                    presented = self._present(state)
                self.assertEqual(presented["current_command"]["status"], "unknown")
                self.assertNotIn("exit_code", presented["current_command_observation"])
                self.assertNotIn("result_status", presented["current_command_observation"])

    def test_wrong_job_identity_does_not_disclose_foreign_results(self) -> None:
        self._finish()
        governor = self.runtime.execution_resource_governor
        exact = governor.find_exact_job(command_id=self.command_id)
        for key in ("command_id", "run_id", "wave_id"):
            with self.subTest(mismatch=key):
                foreign = {**exact, key: "foreign-identity", "job_id": "foreign-job", "exit_code": 77}
                with patch.object(governor, "find_exact_job", return_value=foreign):
                    presented = self._present()
                observation = presented["current_command_observation"]
                self.assertEqual(observation["status"], "conflict")
                self.assertEqual(presented["current_command"]["status"], "unknown")
                for forbidden in ("job_id", "run_id", "wave_id", "exit_code", "result_status", "finished_at"):
                    self.assertNotIn(forbidden, observation)

    def test_missing_and_ambiguous_job_retain_uncertainty(self) -> None:
        governor = self.runtime.execution_resource_governor
        with patch.object(governor, "find_exact_job", return_value=None):
            missing = self._present()
        self.assertEqual(missing["current_command_observation"]["reason"], "managed_job_missing")
        self.assertEqual(missing["current_command"]["status"], "unknown")
        with patch.object(governor, "find_exact_job", side_effect=ExecutionResourceError("EXECUTION_JOB_AMBIGUOUS", "fixture")):
            ambiguous = self._present()
        self.assertEqual(ambiguous["current_command_observation"]["status"], "conflict")
        self.assertNotIn("result_status", ambiguous["current_command_observation"])

    def test_foreign_workspace_is_not_looked_up(self) -> None:
        with tempfile.TemporaryDirectory() as other:
            with patch.object(self.runtime.execution_resource_governor, "find_exact_job", side_effect=AssertionError("foreign lookup")):
                presented = self._present(workspace=Path(other))
        self.assertEqual(presented["current_command_observation"]["reason"], "workspace_mismatch")
        self.assertEqual(presented["current_command"]["status"], "unknown")


if __name__ == "__main__":
    unittest.main()
