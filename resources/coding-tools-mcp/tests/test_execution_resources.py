from __future__ import annotations

import os
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from coding_tools_mcp import execution_resources
from coding_tools_mcp.acceptance_receipts import passed_proof_fingerprint
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

    # The governor treats psutil as an optional dependency (it is only in
    # the desktop extra); this case patches psutil directly, so it requires
    # psutil to be installed in the test environment.
    @unittest.skipIf(execution_resources.psutil is None, "psutil is not installed in this environment")
    def test_foreign_heavy_scan_defers_expensive_process_attrs_until_heavy(self) -> None:
        class FakeProcess:
            def __init__(self, pid: int, name: str, cmdline: list[str], cwd: str, rss: int) -> None:
                self.info = {"pid": pid, "name": name, "cmdline": cmdline}
                self._cwd = cwd
                self._rss = rss
                self.cwd_calls = 0
                self.memory_info_calls = 0

            def cwd(self) -> str:
                self.cwd_calls += 1
                return self._cwd

            def memory_info(self) -> SimpleNamespace:
                self.memory_info_calls += 1
                return SimpleNamespace(rss=self._rss)

        light = FakeProcess(41001, "explorer.exe", [], str(self.root), 1)
        heavy = FakeProcess(41002, "cargo.exe", ["cargo.exe", "test"], str(self.root), 123)
        current = Mock()
        current.parents.return_value = []

        with (
            patch("coding_tools_mcp.execution_resources.psutil.Process", return_value=current),
            patch(
                "coding_tools_mcp.execution_resources.psutil.process_iter",
                return_value=[light, heavy],
            ) as process_iter,
        ):
            foreign = self.governor._foreign_heavy_processes()

        process_iter.assert_called_once_with(["pid", "name", "cmdline"])
        self.assertEqual(light.cwd_calls, 0)
        self.assertEqual(light.memory_info_calls, 0)
        self.assertEqual(heavy.cwd_calls, 1)
        self.assertEqual(heavy.memory_info_calls, 1)
        self.assertEqual(
            foreign,
            [{"pid": 41002, "name": "cargo.exe", "working_set_bytes": 123}],
        )

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

    def test_snapshot_prioritizes_active_jobs_over_newer_terminal_history(self) -> None:
        run_id, wave_id = self._owner()
        active = self.governor.admit(
            command="git status --short",
            command_id="older-active",
            run_id=run_id,
            wave_id=wave_id,
            resource_class="LIGHT",
        )
        terminal_job_ids: list[str] = []
        try:
            for index in range(5):
                terminal = self.governor.admit(
                    command="git status --short",
                    command_id=f"terminal-{index}",
                    run_id=run_id,
                    wave_id=wave_id,
                    resource_class="LIGHT",
                )
                terminal_job_ids.append(terminal.job_id)
                self.governor.complete(
                    terminal.job_id,
                    lifecycle_state="exited",
                    exit_code=0,
                )

            with patch.object(
                self.governor,
                "_rows",
                side_effect=AssertionError("snapshot must use bounded SQL instead of loading all jobs"),
            ), patch.object(
                self.governor,
                "_claim_rows",
                side_effect=AssertionError("snapshot must use bounded SQL instead of loading all claims"),
            ):
                snapshot = self.governor.snapshot(limit=3, reconcile=False)

            self.assertEqual(snapshot["active_command_count"], 1)
            self.assertEqual(snapshot["active_heavy_count"], 0)
            self.assertEqual(
                [row["job_id"] for row in snapshot["jobs"]],
                [active.job_id, *terminal_job_ids[-2:]],
            )
        finally:
            self.governor.complete(active.job_id, lifecycle_state="exited", exit_code=0)

    def test_exact_job_lookup_exposes_terminal_result_and_enforces_unique_command_id(self) -> None:
        run_id, wave_id = self._owner()
        first = self.governor.admit(
            command="git rev-parse HEAD",
            command_id="durable-command",
            run_id=run_id,
            wave_id=wave_id,
            resource_class="LIGHT",
        )
        self.governor.complete(first.job_id, lifecycle_state="exited", exit_code=0)

        observed = self.governor.find_exact_job(command_id="durable-command")
        self.assertIsNotNone(observed)
        self.assertEqual(observed["job_id"], first.job_id)
        self.assertTrue(observed["terminal"])
        self.assertEqual(observed["exit_code"], 0)
        self.assertEqual(observed["result_status"], "succeeded")
        self.assertTrue(observed["finished_at"])
        self.assertNotIn("metadata", observed)

        with self.assertRaises(ExecutionResourceError) as duplicate:
            self.governor.admit(
                command="git rev-parse HEAD",
                command_id="durable-command",
                run_id=run_id,
                wave_id=wave_id,
                resource_class="LIGHT",
            )
        self.assertEqual(duplicate.exception.code, "COMMAND_ID_CONFLICT")
        self.assertIsNone(
            self.governor.find_exact_job(
                command_id="durable-command", job_id="different-job"
            )
        )

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
        self.assertEqual(classify_resource_class("python -m pytest --version"), "LIGHT")
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
                return_value=[
                    {
                        "pid": 123,
                        "name": "rust-analyzer.exe",
                        "working_set_bytes": 2 * 1024 * 1024 * 1024,
                    }
                ],
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

    def test_semantic_native_claim_is_separate_from_process_ownership_and_recovers(self) -> None:
        run_id, wave_id = self._owner()
        heavy = self.governor.admit(
            command="cargo test",
            command_id="semantic-conflict",
            run_id=run_id,
            wave_id=wave_id,
            resource_class="HEAVY",
        )
        rows_before = len(self.governor._rows())
        with (
            patch.object(
                self.governor,
                "_host_pressure",
                return_value={"observed": True, "pressured": False},
            ),
            patch.object(self.governor, "_foreign_heavy_processes", return_value=[]),
        ):
            denied_lease = self.governor.semantic_native_claim(
                mode="workspace",
                cost="HEAVY",
            )
            denied = denied_lease.public_decision()
        self.assertFalse(denied["allowed"])
        self.assertEqual(denied["reason_code"], "HEAVY_SLOT_BUSY")
        self.assertEqual(denied["active_heavy_count"], 1)
        self.assertEqual(len(self.governor._rows()), rows_before)

        # LIGHT/read-only status remains available while the HEAVY slot is
        # occupied; semantic admission never kills or completes that owner.
        self.assertEqual(self.governor.snapshot()["active_heavy_count"], 1)
        self.governor.complete(heavy.job_id, lifecycle_state="exited", exit_code=0)
        with (
            patch.object(
                self.governor,
                "_host_pressure",
                return_value={"observed": True, "pressured": False},
            ),
            patch.object(self.governor, "_foreign_heavy_processes", return_value=[]),
        ):
            with self.governor.semantic_native_claim(
                mode="workspace",
                cost="HEAVY",
            ) as allowed_lease:
                allowed = allowed_lease.public_decision()
                self.assertTrue(allowed["allowed"])
                self.assertTrue(allowed["claim_acquired"])
                self.assertEqual(allowed["reason_code"], "ALLOWED")
        snapshot = self.governor.snapshot()
        self.assertEqual(
            snapshot["semantic_native_admission_counts"],
            {"allowed": 1, "rejected": 1},
        )

    def test_semantic_native_claim_reason_priority_is_deterministic(self) -> None:
        with (
            patch.object(
                self.governor,
                "_host_pressure",
                return_value={"observed": True, "pressured": True},
            ),
            patch.object(self.governor, "_foreign_heavy_processes", return_value=[]),
        ):
            pressured = self.governor.semantic_native_claim(
                mode="single_file",
                cost="MEDIUM",
            ).public_decision()
        self.assertEqual(pressured["reason_code"], "HOST_RESOURCE_PRESSURE")

        with (
            patch.object(
                self.governor,
                "_host_pressure",
                return_value={"observed": True, "pressured": False},
            ),
            patch.object(
                self.governor,
                "_foreign_heavy_processes",
                return_value=[
                    {"pid": 123, "name": "cargo.exe", "working_set_bytes": 1}
                ],
            ),
        ):
            foreign = self.governor.semantic_native_claim(
                mode="single_file",
                cost="MEDIUM",
            ).public_decision()
        self.assertEqual(foreign["reason_code"], "UNOWNED_EXECUTION_PROCESS")

        with (
            patch.object(
                self.governor,
                "_host_pressure",
                return_value={"observed": True, "pressured": False},
            ),
            patch.object(
                self.governor,
                "_foreign_heavy_processes",
                return_value=[
                    {
                        "pid": 456,
                        "name": "rust-analyzer.exe",
                        "working_set_bytes": 2 * 1024 * 1024 * 1024,
                    }
                ],
            ),
        ):
            focused = self.governor.semantic_native_claim(
                mode="single_file",
                cost="MEDIUM",
            ).public_decision()
            workspace = self.governor.semantic_native_claim(
                mode="workspace",
                cost="HEAVY",
            ).public_decision()
        self.assertTrue(focused["allowed"])
        self.assertTrue(focused["foreign_heavy_present"])
        self.assertEqual(workspace["reason_code"], "UNOWNED_EXECUTION_PROCESS")

    def test_atomic_semantic_and_managed_heavy_claim_barrier_100_iterations(self) -> None:
        run_id, wave_id = self._owner()
        other = ExecutionResourceGovernor(
            self.root,
            self.ledger,
            process_instance_id="process-two",
            runtime_instance_id="runtime-two",
        )
        for governor in (self.governor, other):
            governor._host_pressure = lambda: {"observed": True, "pressured": False}  # type: ignore[method-assign]
            governor._foreign_heavy_processes = lambda: []  # type: ignore[method-assign]

        for iteration in range(100):
            barrier = threading.Barrier(3)
            release = threading.Event()
            semantic_done = threading.Event()
            managed_done = threading.Event()
            results: dict[str, object] = {}

            def semantic_lane() -> None:
                barrier.wait()
                with self.governor.semantic_native_claim(
                    mode="single_file",
                    cost="HEAVY",
                    resource_status={
                        "lifecycle_state": "STOPPED",
                        "warm": False,
                        "pressure_state": "UNKNOWN",
                    },
                ) as lease:
                    results["semantic"] = lease.public_decision()
                    semantic_done.set()
                    release.wait(timeout=5)

            def managed_lane() -> None:
                barrier.wait()
                admission = None
                try:
                    admission = other.admit(
                        command="cargo test",
                        command_id=f"barrier-managed-{iteration}",
                        run_id=run_id,
                        wave_id=wave_id,
                        resource_class="HEAVY",
                    )
                    results["managed"] = "allowed"
                except ExecutionResourceError as exc:
                    results["managed"] = exc.code
                finally:
                    managed_done.set()
                release.wait(timeout=5)
                if admission is not None:
                    other.complete(admission.job_id, lifecycle_state="exited", exit_code=0)

            semantic_thread = threading.Thread(target=semantic_lane)
            managed_thread = threading.Thread(target=managed_lane)
            semantic_thread.start()
            managed_thread.start()
            barrier.wait()
            self.assertTrue(semantic_done.wait(timeout=5), iteration)
            self.assertTrue(managed_done.wait(timeout=5), iteration)
            semantic_allowed = bool(
                isinstance(results.get("semantic"), dict)
                and results["semantic"].get("allowed") is True  # type: ignore[union-attr]
            )
            managed_allowed = results.get("managed") == "allowed"
            self.assertEqual(int(semantic_allowed) + int(managed_allowed), 1, (iteration, results))
            self.assertEqual(len(self.governor._claim_rows(active_only=True)), 1, iteration)
            loser = results.get("managed") if semantic_allowed else results["semantic"]["reason_code"]  # type: ignore[index]
            self.assertEqual(loser, "HEAVY_SLOT_BUSY", (iteration, results))
            release.set()
            semantic_thread.join(timeout=5)
            managed_thread.join(timeout=5)
            self.assertFalse(semantic_thread.is_alive(), iteration)
            self.assertFalse(managed_thread.is_alive(), iteration)
            self.assertEqual(self.governor._claim_rows(active_only=True), [], iteration)

        with self.governor.semantic_native_claim(
            mode="workspace",
            cost="HEAVY",
        ) as retry:
            self.assertTrue(retry["allowed"])
            self.assertTrue(retry["claim_acquired"])

    def test_semantic_claim_releases_on_exception_and_expiry_is_owner_safe(self) -> None:
        self.governor._host_pressure = lambda: {"observed": True, "pressured": False}  # type: ignore[method-assign]
        self.governor._foreign_heavy_processes = lambda: []  # type: ignore[method-assign]
        with self.assertRaisesRegex(RuntimeError, "provider failed"):
            with self.governor.semantic_native_claim(
                mode="workspace",
                cost="HEAVY",
            ) as lease:
                self.assertTrue(lease["claim_acquired"])
                raise RuntimeError("provider failed")
        self.assertEqual(self.governor._claim_rows(active_only=True), [])

        stale = self.governor.semantic_native_claim(mode="workspace", cost="HEAVY")
        stale_claim = self.governor._claim_rows(active_only=True)[0]
        with self.ledger._lock, self.ledger._connect() as connection:
            connection.execute(
                "UPDATE checkout_resource_claims SET expires_at=? WHERE claim_id=?",
                (time.time() - 1, stale_claim["claim_id"]),
            )
        self.governor.reconcile()
        with self.governor.semantic_native_claim(mode="workspace", cost="HEAVY") as current:
            self.assertTrue(current["allowed"])
            stale.release()
            self.assertEqual(len(self.governor._claim_rows(active_only=True)), 1)
        self.assertEqual(self.governor._claim_rows(active_only=True), [])

    def test_reconcile_releases_backfilled_claim_after_older_runtime_terminalizes_job(self) -> None:
        run_id, wave_id = self._owner()
        admission = self.governor.admit(
            command="cargo test",
            command_id="cross-version-terminal",
            run_id=run_id,
            wave_id=wave_id,
            resource_class="HEAVY",
        )
        with self.ledger._lock, self.ledger._connect() as connection:
            connection.execute(
                """UPDATE managed_process_jobs
                   SET lifecycle_state='exited',finished_at=updated_at
                   WHERE job_id=?""",
                (admission.job_id,),
            )
        self.assertEqual(len(self.governor._claim_rows(active_only=True)), 1)

        self.governor.reconcile()

        self.assertEqual(self.governor._claim_rows(active_only=True), [])
        with (
            patch.object(
                self.governor,
                "_host_pressure",
                return_value={"observed": True, "pressured": False},
            ),
            patch.object(self.governor, "_foreign_heavy_processes", return_value=[]),
        ):
            with self.governor.semantic_native_claim(mode="workspace", cost="HEAVY") as lease:
                self.assertTrue(lease["allowed"])
                self.assertTrue(lease["claim_acquired"])

    def test_semantic_claim_respects_lsp_pressure_policy(self) -> None:
        self.governor._host_pressure = lambda: {"observed": True, "pressured": False}  # type: ignore[method-assign]
        self.governor._foreign_heavy_processes = lambda: []  # type: ignore[method-assign]

        hard = self.governor.semantic_native_claim(
            mode="single_file",
            cost="MEDIUM",
            resource_status={"pressure_state": "HARD"},
        ).public_decision()
        soft_workspace = self.governor.semantic_native_claim(
            mode="workspace",
            cost="HEAVY",
            resource_status={"pressure_state": "SOFT"},
        ).public_decision()
        with self.governor.semantic_native_claim(
            mode="single_file",
            cost="MEDIUM",
            resource_status={"pressure_state": "SOFT"},
        ) as soft_focused:
            self.assertTrue(soft_focused["allowed"])

        self.assertEqual(hard["reason_code"], "LSP_RESOURCE_PRESSURE")
        self.assertEqual(soft_workspace["reason_code"], "LSP_RESOURCE_PRESSURE")
        self.assertEqual(self.governor._claim_rows(active_only=True), [])

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
            runtime_instance_id="runtime-one",
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

    def test_restart_quiesces_stale_unbound_start_from_prior_runtime_and_releases_claim(self) -> None:
        run_id, wave_id = self._owner()
        admission = self.governor.admit(
            command="cargo test",
            command_id="stale-unbound-heavy",
            run_id=run_id,
            wave_id=wave_id,
            resource_class="HEAVY",
        )
        with self.ledger._lock, self.ledger._connect() as connection:
            connection.execute(
                """UPDATE managed_process_jobs
                   SET started_at='2000-01-01T00:00:00+00:00',
                       updated_at='2000-01-01T00:00:00+00:00'
                   WHERE job_id=?""",
                (admission.job_id,),
            )

        restarted = ExecutionResourceGovernor(
            self.root,
            self.ledger,
            process_instance_id="process-two",
            runtime_instance_id="runtime-two",
        )

        self.assertEqual(restarted.recovery["quiesced"], 1)
        row = next(item for item in restarted._rows() if item["job_id"] == admission.job_id)
        self.assertEqual(row["lifecycle_state"], "quiesced")
        self.assertEqual(restarted.snapshot()["active_command_count"], 0)
        self.assertEqual(restarted._claim_rows(active_only=True), [])

    def test_restart_preserves_fresh_unbound_start_from_prior_runtime_during_grace(self) -> None:
        admission = self.governor.admit(
            command="git status --short",
            command_id="fresh-unbound-light",
            resource_class="LIGHT",
        )
        restarted = ExecutionResourceGovernor(
            self.root,
            self.ledger,
            process_instance_id="process-two",
            runtime_instance_id="runtime-two",
        )
        try:
            row = next(item for item in restarted._rows() if item["job_id"] == admission.job_id)
            self.assertEqual(row["lifecycle_state"], "starting")
            self.assertEqual(restarted.snapshot()["active_command_count"], 1)
        finally:
            self.governor.complete(admission.job_id, lifecycle_state="spawn_failed")

    def test_restart_preserves_fresh_unbound_start_from_same_runtime_during_grace(self) -> None:
        admission = self.governor.admit(
            command="git status --short",
            command_id="fresh-unbound-same-runtime",
            resource_class="LIGHT",
        )
        same_runtime = ExecutionResourceGovernor(
            self.root,
            self.ledger,
            process_instance_id="process-one",
            runtime_instance_id="runtime-one",
        )
        try:
            row = next(item for item in same_runtime._rows() if item["job_id"] == admission.job_id)
            self.assertEqual(row["lifecycle_state"], "starting")
            self.assertEqual(same_runtime.snapshot()["active_command_count"], 1)
        finally:
            self.governor.complete(admission.job_id, lifecycle_state="spawn_failed")

    def test_restart_quiesces_dead_foreign_bound_row_and_releases_claim(self) -> None:
        run_id, wave_id = self._owner()
        admission = self.governor.admit(
            command="cargo test",
            command_id="dead-foreign-heavy",
            run_id=run_id,
            wave_id=wave_id,
            resource_class="HEAVY",
        )
        with self.ledger._lock, self.ledger._connect() as connection:
            connection.execute(
                """UPDATE managed_process_jobs
                   SET lifecycle_state='running',root_pid=2147483647,
                       root_process_token='definitely-dead-process'
                   WHERE job_id=?""",
                (admission.job_id,),
            )

        restarted = ExecutionResourceGovernor(
            self.root,
            self.ledger,
            process_instance_id="process-two",
            runtime_instance_id="runtime-two",
        )

        self.assertEqual(restarted.recovery["quiesced"], 1)
        row = next(item for item in restarted._rows() if item["job_id"] == admission.job_id)
        self.assertEqual(row["lifecycle_state"], "quiesced")
        self.assertEqual(restarted.snapshot()["active_command_count"], 0)
        self.assertEqual(restarted._claim_rows(active_only=True), [])

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
                "yield_time_ms": 5000,
            })
            self.assertEqual(result["exit_code"], 0)
            self.assertEqual(result["execution_owner"]["run_id"], ctx.run_id)
            self.assertEqual(result["execution_owner"]["wave_id"], ctx.wave_id)
            self.assertEqual(result["execution_owner"]["resource_class"], "HEAVY")
            self.assertEqual(runtime.execution_resource_governor.snapshot()["active_heavy_count"], 0)
        finally:
            runtime.close()

    def test_unscoped_exec_does_not_inherit_active_task_projection(self) -> None:
        runtime_root = self.root / "unscoped-runtime"
        runtime_root.mkdir()
        runtime = Runtime(runtime_root, permission_mode="dangerous")
        try:
            runtime.task_state.ensure_started("owned task", current_step="test")
            ctx = runtime.orchestration_control.begin(
                objective="owned task",
                task_id="unscoped-task",
                execution_mode="mcp_only",
                base_head="",
                worktree_fp="",
            )
            runtime._project_orchestration(ctx)
            self.assertFalse(runtime.task_state.is_scoped())

            result = runtime.exec_command({
                "cmd": f'"{sys.executable}" --version',
                "resource_class": "LIGHT",
                "yield_time_ms": 5000,
            })

            self.assertEqual(result["exit_code"], 0)
            self.assertEqual(result["execution_owner"]["run_id"], "")
            self.assertEqual(result["execution_owner"]["wave_id"], "")
            self.assertIsNone(runtime.task_state.get()["current_command"])
            row = next(
                item
                for item in runtime.execution_resource_governor._rows()
                if item["command_id"] == result["session_id"]
            )
            self.assertEqual(row["run_id"], "")
            self.assertEqual(row["wave_id"], "")
        finally:
            runtime.close()

    def test_internal_continuous_check_explicitly_preserves_eocl_owner(self) -> None:
        runtime_root = self.root / "owned-internal-runtime"
        runtime_root.mkdir()
        runtime = Runtime(runtime_root, permission_mode="dangerous")
        try:
            runtime.task_state.ensure_started("owned proof", current_step="test")
            ctx = runtime.orchestration_control.begin(
                objective="owned proof",
                task_id="owned-proof-task",
                execution_mode="mcp_only",
                base_head="",
                worktree_fp="",
            )
            runtime.orchestration_control.mark_ready(ctx)
            runtime.orchestration_control.select_route(
                ctx,
                {"requested": "deterministic", "selected": "deterministic", "reason": "test"},
            )
            runtime.orchestration_control.acquire_write_lease(ctx, owner="MCP", mode="mcp_only")
            runtime._project_orchestration(ctx)
            self.assertFalse(runtime.task_state.is_scoped())

            result = runtime.apply_changes_and_verify({
                "objective": "run one owned proof check",
                "checks": [f'"{sys.executable}" --version'],
                "path": ".",
                "workdir": ".",
                "verification": "none",
                "include_diff": False,
                "_orchestration_context": ctx,
            })

            self.assertTrue(result["ok"])
            self.assertEqual(result["check_results"][0]["status"], "passed")
            current_wave_proofs = runtime.orchestration_ledger.list_proofs(ctx.run_id, wave_id=ctx.wave_id)
            self.assertEqual(
                result["proof_summary"]["proof_fingerprint"],
                passed_proof_fingerprint(current_wave_proofs),
            )
            session_id = str(result["check_results"][0]["session_id"])
            row = next(
                item
                for item in runtime.execution_resource_governor._rows(
                    run_id=ctx.run_id,
                    wave_id=ctx.wave_id,
                )
                if item["command_id"] == session_id
            )
            self.assertEqual(row["run_id"], ctx.run_id)
            self.assertEqual(row["wave_id"], ctx.wave_id)
        finally:
            runtime.close()

    def test_failed_continuous_check_records_content_free_p2_detail(self) -> None:
        runtime_root = self.root / "failed-owned-check-runtime"
        runtime_root.mkdir()
        runtime = Runtime(runtime_root, permission_mode="dangerous")
        try:
            runtime.task_state.ensure_started("owned failed proof", current_step="test")
            ctx = runtime.orchestration_control.begin(
                objective="owned failed proof",
                task_id="failed-owned-proof-task",
                execution_mode="mcp_only",
                base_head="",
                worktree_fp="",
            )
            runtime.orchestration_control.mark_ready(ctx)
            runtime.orchestration_control.select_route(
                ctx,
                {"requested": "deterministic", "selected": "deterministic", "reason": "test"},
            )
            runtime.orchestration_control.acquire_write_lease(ctx, owner="MCP", mode="mcp_only")
            runtime._project_orchestration(ctx)

            result = runtime.apply_changes_and_verify({
                "objective": "run one failed owned proof check",
                "checks": [f'"{sys.executable}" -c "import sys; sys.exit(3)"'],
                "path": ".",
                "workdir": ".",
                "verification": "none",
                "include_diff": False,
                "_orchestration_context": ctx,
            })

            self.assertFalse(result["ok"])
            failure = next(
                event
                for event in runtime.orchestration_ledger.list_events(ctx.run_id)
                if event.get("event_type") == "failure_observed"
            )
            detail = failure["payload"]["p2_failure_detail"]
            self.assertEqual(failure["payload"]["failure_class"], "CHECK_FAILED")
            self.assertEqual(detail["schema"], "p2_failure_observation_v3")
            self.assertEqual(detail["stage"], "checks")
            self.assertEqual(detail["command_family"], "other")
            self.assertNotIn("command", detail)
            self.assertNotIn("output", detail)
        finally:
            runtime.close()


if __name__ == "__main__":
    unittest.main()
