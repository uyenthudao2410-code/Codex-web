"""Diagnostic only: original integration assertions with synthetic OS boundaries.

This is no evidence of live MXC execution. No process, VM, or system feature is
created. Source/ledger/state-machine logic remains real in temporary workspaces.
"""
from __future__ import annotations

import io
import json
import sys
import time
import unittest
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

PACKAGE = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(PACKAGE))
sys.path.insert(0, str(PACKAGE / "tests"))

from test_run_continuation import RunContinuationSurfaceTests
from test_wave_a_runtime import CommandHandleMigrationTests

spawns: list[dict[str, object]] = []
builds: list[dict[str, object]] = []
polls: list[str] = []


class SyntheticProcess:
    pid = 2147483001
    def __init__(self, code: int, output: bytes, *, delayed: bool = False):
        self.returncode = None
        self.result = code
        self.output = output
        self.ready_at = time.monotonic() + (0.05 if delayed else 0)
        self.stdin = io.BytesIO()
        self.stdout = None
        self.stderr = None
        self.session = None
        self.output_sent = False

    def poll(self):
        if time.monotonic() >= self.ready_at:
            self.returncode = self.result
            if self.session is not None and not self.output_sent:
                self.output_sent = True
                self.session.append_stdout(self.output)
        return self.returncode

    def wait(self, timeout=None):
        self.ready_at = 0
        return self.poll()

    def kill(self):
        self.returncode = -9

    def terminate(self):
        self.returncode = -15


def synthetic_invocation(argv, **kwargs):
    assert isinstance(argv, list)
    assert argv[0] == sys.executable
    assert argv[1] == "-c"
    bridge = "bridge-argv-ok" in argv[2]
    builds.append({"structured": True, "bridge": bridge})
    if bridge:
        # Force the existing yield contract's running branch without a VM.
        time.sleep(1.05)
    return SimpleNamespace(argv=tuple(argv), environment={},
                           cwd_alias_path=kwargs["workdir"] if bridge else None)


def synthetic_spawn(argv, *, cwd, shell, env, tty, popen_kwargs):
    assert shell is False
    assert tty is False
    assert isinstance(argv, list)
    assert argv[0] == sys.executable and argv[1] == "-c"
    script = argv[2]
    bridge = "bridge-argv-ok" in script
    if bridge:
        code, output = 0, b"bridge-argv-ok\n"
    elif "literal&&not-a-command" in argv:
        assert argv == [sys.executable, "-c", "import sys; print(sys.argv[1])", "literal&&not-a-command"]
        code, output = 0, b"literal&&not-a-command\n"
    elif "Path('../target.py').read_text" in script:
        expected = "correct\n" if "correct\\n" in script else "after\n"
        observed = (Path(cwd).parent / "target.py").read_text(encoding="utf-8")
        code, output = (0 if observed == expected else 1), b""
    else:
        raise AssertionError("Diagnostic received an unexpected command")
    spawns.append({"shell": shell, "code": code, "bridge": bridge})
    return SyntheticProcess(code, output, delayed=bridge), None


def synthetic_readers(session):
    session.process.session = session


original_poll = CommandHandleMigrationTests.__dict__["test_control_plane_structured_argv_requires_attested_bridge_identity"]

suite = unittest.TestSuite([
    RunContinuationSurfaceTests("test_internal_structured_argv_uses_no_shell_and_is_not_a_public_escape_hatch"),
    RunContinuationSurfaceTests("test_patch_proposal_journals_backup_runs_structured_proof_and_stops_at_accepting"),
    RunContinuationSurfaceTests("test_failed_proof_dispatches_one_bounded_repair_turn_then_reaches_accepting"),
    CommandHandleMigrationTests("test_control_plane_structured_argv_requires_attested_bridge_identity"),
])

with ExitStack() as stack:
    for target, value in [
        ("coding_tools_mcp.exec_tools.windows_sandbox_feature_enabled", lambda: True),
        ("coding_tools_mcp.exec_tools.MxcWindowsSandboxManager", Mock),
        ("coding_tools_mcp.exec_tools.build_mxc_windows_sandbox_invocation", synthetic_invocation),
        ("coding_tools_mcp.exec_tools.build_mxc_invocation", synthetic_invocation),
        ("coding_tools_mcp.exec_tools.cleanup_mxc_windows_sandbox_invocation", lambda *a, **kw: True),
        ("coding_tools_mcp.exec_tools.cleanup_mxc_invocation", lambda *a, **kw: True),
        ("coding_tools_mcp.exec_tools.spawn_process", synthetic_spawn),
        ("coding_tools_mcp.exec_tools.start_reader_threads", synthetic_readers),
        ("coding_tools_mcp.exec_tools.start_session_watchdog", lambda session: None),
        ("coding_tools_mcp.execution_resources.attach_managed_process", lambda process: False),
        ("coding_tools_mcp.execution_resources.process_identity_token", lambda pid: "synthetic-only"),
        ("coding_tools_mcp.execution_resources.terminate_process_group", lambda *a, **kw: None),
        ("coding_tools_mcp.exec_tools.terminate_process_group", lambda *a, **kw: None),
        ("coding_tools_mcp.session_control.terminate_process_group", lambda *a, **kw: None),
        ("coding_tools_mcp.processes.terminate_process_group", lambda *a, **kw: None),
    ]:
        stack.enter_context(patch(target, value))
    from coding_tools_mcp.server import Runtime
    original_write_stdin = Runtime.write_stdin
    def record_poll(self, args):
        polls.append(str(args["command_id"]))
        return original_write_stdin(self, args)
    stack.enter_context(patch.object(Runtime, "write_stdin", record_poll))
    result = unittest.TextTestRunner(verbosity=2).run(suite)

summary = {"tests_run": result.testsRun, "failures": len(result.failures),
           "errors": len(result.errors), "synthetic_spawn_count": len(spawns),
           "all_shell_false": all(item["shell"] is False for item in spawns),
           "simulated_failed_checks": sum(item["code"] == 1 for item in spawns),
           "bridge_poll_count": len(polls), "distinct_polled_commands": len(set(polls)),
           "real_process_or_vm_started": False,
           "scope": "isolated boundary diagnostic; not live MXC acceptance"}
print(json.dumps(summary, sort_keys=True))
assert len(polls) >= 1 and len(set(polls)) == 1
assert len(spawns) == 5 and summary["simulated_failed_checks"] == 1
sys.exit(0 if result.wasSuccessful() else 1)
