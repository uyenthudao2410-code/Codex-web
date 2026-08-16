from __future__ import annotations

import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from coding_tools_mcp.execution_resources import (
    ExecutionResourceError,
    ExecutionResourceGovernor,
    classify_resource_class,
    process_is_alive,
)
from coding_tools_mcp.errors import ToolFailure
from coding_tools_mcp.orchestration_control import OrchestrationControl
from coding_tools_mcp.orchestration_ledger import OrchestrationLedger
from coding_tools_mcp.processes import (
    process_group_popen_kwargs,
    spawn_process,
    terminate_process_group,
)
from coding_tools_mcp.server import Runtime


class ExecutionResourceGovernorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.ledger = OrchestrationLedger(self.root)
        self.governor = ExecutionResourceGovernor(
            self.root,
            self.ledger,
            process_instance_id="process-one",
            runtime_instance_id="runtime-one",
        )

    def tearDown(self) -> None:
        for row in self.governor._rows(active_only=True):
            process = self.governor._owned_processes.get(row["job_id"])
            if process is not None and process.poll() is None:
                terminate_process_group(process, signal.SIGTERM, force=True)
        self.temp.cleanup()

    def _owner(self) -> tuple[str, str]:
        run_id = self.ledger.create_run(objective="resource test")
        wave_id = self.ledger.create_wave(run_id, execution_mode="mcp_only")
        return run_id, wave_id

    def _spawn_sleep(self) -> subprocess.Popen[bytes]:
        process, _ = spawn_process(
            [sys.executable, "-c", "import time; time.sleep(60)"],
            cwd=str(self.root),
            shell=False,
            env=dict(os.environ),
            tty=False,
            popen_kwargs=process_group_popen_kwargs(),
        )
        return process

    def test_heavy_requires_owner_and_global_slot_while_light_remains_available(self) -> None:
        with self.assertRaises(ExecutionResourceError) as missing:
            self.governor.admit(
                command="cargo test",
                command_id="missing-owner",
                resource_class="HEAVY",
            )
        self.assertEqual(missing.exception.code, "EXECUTION_OWNERSHIP_REQUIRED")

        run_one, wave_one = self._owner()
        run_two, wave_two = self._owner()
        first = self.governor.admit(
            command="cargo test",
            command_id="heavy-one",
            run_id=run_one,
            wave_id=wave_one,
            resource_class="HEAVY",
        )
        with self.assertRaises(ExecutionResourceError) as busy:
            self.governor.admit(
                command="cargo test",
                command_id="heavy-two",
                run_id=run_two,
                wave_id=wave_two,
                resource_class="HEAVY",
            )
        self.assertEqual(busy.exception.code, "HEAVY_SLOT_BUSY")

        light = self.governor.admit(
            command="git diff --check",
            command_id="light-two",
            run_id=run_two,
            wave_id=wave_two,
            resource_class="LIGHT",
        )
        self.assertEqual(light.resource_class, "LIGHT")
        self.governor.complete(light.job_id, lifecycle_state="exited", exit_code=0)
        self.governor.complete(first.job_id, lifecycle_state="exited", exit_code=0)

    def test_resource_classification_distinguishes_cargo_metadata_and_builds(self) -> None:
        self.assertEqual(classify_resource_class("cargo metadata --no-deps"), "LIGHT")
        self.assertEqual(classify_resource_class("cargo fmt --check"), "MEDIUM")
        self.assertEqual(classify_resource_class("cargo test -p webcodex"), "HEAVY")
        self.assertEqual(
            classify_resource_class("cargo metadata --no-deps && cargo test -p webcodex"),
            "HEAVY",
        )
        self.assertEqual(classify_resource_class("rustfmt --check lib.rs && cargo test"), "HEAVY")
        self.assertEqual(classify_resource_class("python -m pytest tests/test_one.py"), "MEDIUM")
        self.assertEqual(classify_resource_class("python -m pytest tests/"), "HEAVY")
        self.assertEqual(
            classify_resource_class(
                "python -m pytest tests/test_one.py && python -m pytest tests/"
            ),
            "HEAVY",
        )

    def test_heavy_admission_defers_for_host_pressure_and_foreign_process(self) -> None:
        run_id, wave_id = self._owner()
        with patch.object(
            self.governor,
            "_host_pressure",
            return_value={"observed": True, "pressured": True, "available_percent": 2.0},
        ):
            with self.assertRaises(ExecutionResourceError) as pressured:
                self.governor.admit(
                    command="cargo test",
                    command_id="pressure",
                    run_id=run_id,
                    wave_id=wave_id,
                )
        self.assertEqual(pressured.exception.code, "HOST_RESOURCE_PRESSURE")

        with (
            patch.object(
                self.governor,
                "_host_pressure",
                return_value={"observed": True, "pressured": False},
            ),
            patch.object(
                self.governor,
                "_foreign_heavy_processes",
                return_value=[{"pid": 123, "name": "cargo.exe", "working_set_bytes": 1}],
            ),
        ):
            with self.assertRaises(ExecutionResourceError) as foreign:
                self.governor.admit(
                    command="cargo test",
                    command_id="foreign",
                    run_id=run_id,
                    wave_id=wave_id,
                )
        self.assertEqual(foreign.exception.code, "UNOWNED_EXECUTION_PROCESS")

    def test_replan_tears_down_descendants_but_not_another_wave(self) -> None:
        control = OrchestrationControl(
            self.root,
            self.ledger,
            on_wave_terminal=lambda ctx, state: self.governor.teardown_wave(
                ctx.run_id,
                ctx.wave_id,
                reason=f"state:{state.lower()}",
            ),
            assert_wave_quiescent=self.governor.assert_wave_quiescent,
        )
        ctx = control.begin(
            objective="owned descendants",
            task_id="task-one",
            execution_mode="mcp_only",
            base_head="",
            worktree_fp="",
        )
        other_run, other_wave = self._owner()
        pid_file = self.root / "child.pid"
        child_script = (
            "import pathlib,subprocess,sys,time;"
            "child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']);"
            "pathlib.Path(sys.argv[1]).write_text(str(child.pid),encoding='utf-8');"
            "time.sleep(60)"
        )
        owned_admission = self.governor.admit(
            command="synthetic heavy child tree",
            command_id="owned-tree",
            run_id=ctx.run_id,
            wave_id=ctx.wave_id,
            resource_class="HEAVY",
        )
        owned, _ = spawn_process(
            [sys.executable, "-c", child_script, str(pid_file)],
            cwd=str(self.root),
            shell=False,
            env=dict(os.environ),
            tty=False,
            popen_kwargs=process_group_popen_kwargs(),
        )
        self.governor.bind_process(owned_admission, owned)

        other_admission = self.governor.admit(
            command="synthetic light other wave",
            command_id="other-wave",
            run_id=other_run,
            wave_id=other_wave,
            resource_class="LIGHT",
        )
        other = self._spawn_sleep()
        self.governor.bind_process(other_admission, other)

        deadline = time.time() + 5
        while not pid_file.exists() and time.time() < deadline:
            time.sleep(0.02)
        self.assertTrue(pid_file.exists())
        child_pid = int(pid_file.read_text(encoding="utf-8"))
        self.assertTrue(process_is_alive(child_pid))

        control.record_failure(ctx, "TEST_REPLAN")
        self.assertEqual(ctx.state, "REPLAN")
        self.assertIsNotNone(owned.poll())
        deadline = time.time() + 3
        while process_is_alive(child_pid) and time.time() < deadline:
            time.sleep(0.02)
        self.assertFalse(process_is_alive(child_pid))
        self.assertIsNone(other.poll(), "another wave's process must not be terminated")
        self.governor.assert_wave_quiescent(ctx.run_id, ctx.wave_id)

        terminate_process_group(other, signal.SIGTERM, force=True)
        self.governor.complete(
            other_admission.job_id,
            lifecycle_state="terminated",
            exit_code=other.poll(),
        )

    def test_restart_marks_live_owner_orphaned_and_blocks_heavy(self) -> None:
        run_id, wave_id = self._owner()
        admission = self.governor.admit(
            command="synthetic heavy restart",
            command_id="restart-heavy",
            run_id=run_id,
            wave_id=wave_id,
            resource_class="HEAVY",
        )
        process = self._spawn_sleep()
        self.governor.bind_process(admission, process)

        restarted = ExecutionResourceGovernor(
            self.root,
            self.ledger,
            process_instance_id="process-two",
            runtime_instance_id="runtime-two",
        )
        self.assertEqual(restarted.recovery["orphaned"], 1)
        with self.assertRaises(ExecutionResourceError) as orphaned:
            restarted.admit(
                command="cargo test",
                command_id="blocked-after-restart",
                run_id=run_id,
                wave_id=wave_id,
                resource_class="HEAVY",
            )
        self.assertEqual(orphaned.exception.code, "UNOWNED_EXECUTION_PROCESS")

        self.governor.teardown_wave(run_id, wave_id, reason="test_cleanup")
        restarted.reconcile()
        replacement = restarted.admit(
            command="cargo test",
            command_id="replacement-heavy",
            run_id=run_id,
            wave_id=wave_id,
            resource_class="HEAVY",
        )
        restarted.complete(replacement.job_id, lifecycle_state="exited", exit_code=0)

    def test_reconnect_in_same_process_retains_teardown_handle(self) -> None:
        run_id, wave_id = self._owner()
        admission = self.governor.admit(
            command="synthetic medium reconnect",
            command_id="reconnect-medium",
            run_id=run_id,
            wave_id=wave_id,
            resource_class="MEDIUM",
        )
        process = self._spawn_sleep()
        self.governor.bind_process(admission, process)

        reconnected = ExecutionResourceGovernor(
            self.root,
            self.ledger,
            process_instance_id="process-one",
            runtime_instance_id="runtime-two",
        )
        self.assertEqual(reconnected.recovery["orphaned"], 0)
        result = reconnected.teardown_wave(run_id, wave_id, reason="same_process_reconnect")
        self.assertTrue(result["quiescent"])
        self.assertIsNotNone(process.poll())

    def test_replan_owner_cannot_admit_new_heavy_work(self) -> None:
        control = OrchestrationControl(self.root, self.ledger)
        ctx = control.begin(
            objective="replan owner",
            task_id="task-replan",
            execution_mode="mcp_only",
            base_head="",
            worktree_fp="",
        )
        control.record_failure(ctx, "TEST_REPLAN")
        with self.assertRaises(ExecutionResourceError) as invalid:
            self.governor.admit(
                command="cargo test",
                command_id="replan-heavy",
                run_id=ctx.run_id,
                wave_id=ctx.wave_id,
                resource_class="HEAVY",
            )
        self.assertEqual(invalid.exception.code, "EXECUTION_OWNER_INVALID")

    def test_reconcile_closes_owned_tree_after_root_exits(self) -> None:
        run_id, wave_id = self._owner()
        pid_file = self.root / "detached-child.pid"
        script = (
            "import pathlib,subprocess,sys;"
            "child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']);"
            "pathlib.Path(sys.argv[1]).write_text(str(child.pid),encoding='utf-8')"
        )
        admission = self.governor.admit(
            command="synthetic root exits",
            command_id="root-exits",
            run_id=run_id,
            wave_id=wave_id,
            resource_class="HEAVY",
        )
        root, _ = spawn_process(
            [sys.executable, "-c", script, str(pid_file)],
            cwd=str(self.root),
            shell=False,
            env=dict(os.environ),
            tty=False,
            popen_kwargs=process_group_popen_kwargs(),
        )
        self.governor.bind_process(admission, root)
        root.wait(timeout=5)
        deadline = time.time() + 5
        while not pid_file.exists() and time.time() < deadline:
            time.sleep(0.02)
        self.assertTrue(pid_file.exists())
        child_pid = int(pid_file.read_text(encoding="utf-8"))
        self.assertTrue(process_is_alive(child_pid))

        self.governor.reconcile()
        deadline = time.time() + 3
        while process_is_alive(child_pid) and time.time() < deadline:
            time.sleep(0.02)
        self.assertFalse(process_is_alive(child_pid))
        self.assertEqual(self.governor.snapshot()["active_heavy_count"], 0)

    def test_runtime_exec_registers_owner_before_spawn_and_releases_slot(self) -> None:
        runtime_root = self.root / "runtime"
        runtime_root.mkdir()
        runtime = Runtime(runtime_root, permission_mode="trusted")
        try:
            command = f'"{sys.executable}" -c "print(123)"'
            with self.assertRaises(ToolFailure) as missing:
                runtime.exec_command({
                    "cmd": command,
                    "resource_class": "HEAVY",
                    "yield_time_ms": 1000,
                })
            self.assertEqual(missing.exception.code, "EXECUTION_OWNERSHIP_REQUIRED")

            runtime.task_state.ensure_started("managed exec", current_step="test")
            ctx = runtime.orchestration_control.begin(
                objective="managed exec",
                task_id="runtime-task",
                execution_mode="mcp_only",
                base_head="",
                worktree_fp="",
            )
            runtime._project_orchestration(ctx)
            result = runtime.exec_command({
                "cmd": command,
                "run_id": ctx.run_id,
                "wave_id": ctx.wave_id,
                "resource_class": "HEAVY",
                "yield_time_ms": 1000,
            })
            self.assertEqual(result["exit_code"], 0)
            self.assertEqual(result["execution_owner"]["run_id"], ctx.run_id)
            self.assertEqual(result["execution_owner"]["wave_id"], ctx.wave_id)
            self.assertEqual(result["execution_owner"]["resource_class"], "HEAVY")
            self.assertEqual(runtime.execution_resource_governor.snapshot()["active_heavy_count"], 0)
        finally:
            runtime.close()


if __name__ == "__main__":
    unittest.main()
