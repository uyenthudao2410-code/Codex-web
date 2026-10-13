from pathlib import Path
import threading
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from coding_tools_mcp.errors import ToolFailure
from coding_tools_mcp import windows_mxc_state_aware as sandbox
from coding_tools_mcp.session_control import SessionControlMixin


@pytest.fixture
def manager(tmp_path):
    owner = sandbox.MxcWindowsSandboxManager(executor_directory=tmp_path)
    owner._active = sandbox._ActiveSandbox("wsb:12345678", tmp_path, ())
    owner._deprovision_id = Mock()
    with patch.object(sandbox.threading, "Timer") as timers:
        yield owner, timers


def expire(timers):
    invocation = timers.call_args
    invocation.args[1](*invocation.kwargs["args"])


def test_idle_closes_only_the_owned_id_after_job_completion(manager):
    owner, timers = manager
    owner._lock.acquire()
    owner._lease_active = True
    assert owner.release(retire_when_idle=False)
    timers.assert_not_called()
    assert not owner.arm_idle_retirement()
    assert owner.arm_idle_retirement(lease_generation=owner.lease_generation)
    assert timers.call_args.args[0] == 30
    expire(timers)
    owner._deprovision_id.assert_called_once_with("wsb:12345678")
    assert owner._active is None
    assert not owner._uncertain


def test_idle_callback_never_interrupts_a_command(manager):
    owner, timers = manager
    owner.arm_idle_retirement()
    owner._lock.acquire()
    owner._lease_active = True
    callback = threading.Thread(target=expire, args=(timers,), daemon=True)
    try:
        callback.start()
        owner._deprovision_id.assert_not_called()
    finally:
        owner.release(retire_when_idle=False)
    callback.join(timeout=1)
    assert not callback.is_alive()
    owner._deprovision_id.assert_not_called()
    owner.arm_idle_retirement(lease_generation=owner.lease_generation)
    expire(timers)
    owner._deprovision_id.assert_called_once()


def test_idle_callback_survives_observation_lock_contention(manager):
    owner, timers = manager
    owner.arm_idle_retirement()
    owner._lock.acquire()
    callback = threading.Thread(target=expire, args=(timers,), daemon=True)
    try:
        callback.start()
        owner._deprovision_id.assert_not_called()
    finally:
        owner._lock.release()
    callback.join(timeout=1)
    assert not callback.is_alive()
    owner._deprovision_id.assert_called_once_with("wsb:12345678")
    assert owner._active is None
    assert owner._idle_timer is None


def test_terminal_arm_survives_stale_receipt_contention_and_deduplicates(manager):
    owner, timers = manager
    owner.lease_generation = 2
    owner._pending_terminal_generation = 2
    armed = threading.Event()
    timers.return_value.start.side_effect = armed.set
    owner._lock.acquire()
    try:
        # A stale receipt's brief lock cannot discard the correct terminal arm.
        assert not owner.arm_idle_retirement(lease_generation=2)
        assert not owner.arm_idle_retirement(lease_generation=2)
        assert owner._deferred_arm_generations == {2}
        timers.assert_not_called()
    finally:
        owner._lock.release()
    assert armed.wait(timeout=1)
    assert owner._deferred_arm_generations == set()
    assert timers.call_count == 1
    assert owner._pending_terminal_generation is None
    expire(timers)
    owner._deprovision_id.assert_called_once_with("wsb:12345678")


def test_deferred_terminal_arm_cannot_arm_a_new_command_generation(manager):
    owner, timers = manager
    owner.lease_generation = 2
    owner._pending_terminal_generation = 2
    finished = threading.Event()
    original = owner._deferred_arm

    def observe(generation):
        try:
            original(generation)
        finally:
            finished.set()

    owner._lock.acquire()
    try:
        with patch.object(owner, "_deferred_arm", side_effect=observe):
            assert not owner.arm_idle_retirement(lease_generation=2)
        # Model the next acquire while the old waiter is still blocked.
        owner._cancel_idle_locked()
        owner.lease_generation = 3
        owner._pending_terminal_generation = None
        owner._lease_active = True
    finally:
        owner._lock.release()
    assert finished.wait(timeout=1)
    timers.assert_not_called()
    owner._deprovision_id.assert_not_called()
    assert owner._deferred_arm_generations == set()


def test_old_receipt_cannot_arm_pending_new_job_or_extend_deadline(manager):
    owner, timers = manager
    owner.lease_generation = 2
    owner._pending_terminal_generation = 2
    assert not owner.arm_idle_retirement(lease_generation=1)
    timers.assert_not_called()
    assert owner.arm_idle_retirement(lease_generation=2)
    first = timers.call_args
    assert owner.arm_idle_retirement(lease_generation=2)
    assert timers.call_count == 1
    first.args[1](*first.kwargs["args"])
    owner._deprovision_id.assert_called_once()


def test_stale_timer_cannot_close_reused_or_replaced_vm(manager):
    owner, timers = manager
    owner.arm_idle_retirement()
    stale = timers.call_args
    with patch.object(sandbox, "verify_mxc_windows_sandbox_candidate"), \
            patch.object(owner, "_ensure_active", return_value="wsb:12345678"):
        assert owner.acquire(owner._active.workspace_root, []) == "wsb:12345678"
    assert timers.return_value.cancel.called
    owner.release(retire_when_idle=False)
    stale.args[1](*stale.kwargs["args"])
    owner._deprovision_id.assert_not_called()
    owner._active = sandbox._ActiveSandbox("wsb:87654321", Path("other"), ())
    owner.arm_idle_retirement(lease_generation=owner.lease_generation)
    stale.args[1](*stale.kwargs["args"])
    owner._deprovision_id.assert_not_called()
    expire(timers)
    owner._deprovision_id.assert_called_once_with("wsb:87654321")


def test_idle_teardown_uncertainty_blocks_future_commands(manager):
    owner, timers = manager
    owner._deprovision_id.side_effect = ToolFailure("SANDBOX_STATE_PHASE_FAILED", "failure")
    owner.arm_idle_retirement()
    expire(timers)
    assert owner._uncertain
    with patch.object(sandbox, "verify_mxc_windows_sandbox_candidate"), \
            pytest.raises(ToolFailure, match="teardown could not be confirmed"):
        owner.acquire(owner._active.workspace_root, [])
    assert owner._deprovision_id.call_count == 1


def test_close_cancels_idle_callback_without_double_deprovision(manager):
    owner, timers = manager
    owner.arm_idle_retirement()
    assert owner.close()
    assert timers.return_value.cancel.called
    expire(timers)
    owner._deprovision_id.assert_called_once_with("wsb:12345678")


def test_idle_timeout_is_bounded():
    for seconds in (0, -1, 301, float("nan"), float("inf")):
        with pytest.raises(ValueError):
            sandbox.MxcWindowsSandboxManager(idle_timeout_seconds=seconds)


def test_runtime_idle_gate_follows_durable_terminal_job_and_exact_lease():
    order = []
    class Runtime(SessionControlMixin):
        sessions_lock = threading.RLock()
        sessions = {}
        session_principals = {}
        principal_active_counts = {}

        def _remember_output_session(self, session):
            pass

    runtime = Runtime()
    runtime.execution_resource_governor = SimpleNamespace(complete=lambda *args, **kwargs: order.append("terminal_job"))
    runtime._windows_mxc_sandbox_manager = SimpleNamespace(
        arm_idle_retirement=lambda **kwargs: order.append(("idle", kwargs["lease_generation"]))
    )
    session = SimpleNamespace(
        refresh_status=lambda: None, process=SimpleNamespace(poll=lambda: 0),
        cleanup_sandbox_state=lambda: order.append("scratch"), managed_job_id="job",
        resource_terminal_recorded=False, timed_out=False, signal_name=None,
        terminating=False, exit_code=0, execution_metadata={"execution_backend": "isolated"},
        sandbox_idle_generation=7, session_id="command",
    )
    with patch("coding_tools_mcp.session_control.terminate_process_group"):
        runtime._complete_session(session)
    assert order == ["scratch", "terminal_job", ("idle", 7)]
    assert session.resource_terminal_recorded
    order.clear()
    session.resource_terminal_recorded = False
    runtime.execution_resource_governor.complete = Mock(side_effect=RuntimeError("ledger unavailable"))
    with patch("coding_tools_mcp.session_control.terminate_process_group"), pytest.raises(RuntimeError):
        runtime._complete_session(session)
    assert order == ["scratch"]
