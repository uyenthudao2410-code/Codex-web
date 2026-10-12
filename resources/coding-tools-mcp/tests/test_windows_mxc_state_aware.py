from __future__ import annotations

import base64
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path, PureWindowsPath
from types import SimpleNamespace
from unittest.mock import Mock, patch

from coding_tools_mcp.errors import ToolFailure
from coding_tools_mcp.processes import ExecSession
from coding_tools_mcp import windows_mxc_state_aware as state_aware
from coding_tools_mcp.windows_mxc_state_aware import (
    GUEST_TOOLCHAIN_SHARE_PREFIX,
    GUEST_WORKSPACE_SHARE,
    MxcWindowsSandboxInvocation,
    MxcWindowsSandboxManager,
    _build_launcher_command,
    _guest_environment_value,
    _guest_path_for_host,
    _phase_config,
    _validate_argv_and_environment,
    build_mxc_windows_sandbox_invocation,
    cleanup_mxc_windows_sandbox_invocation,
    probe_mxc_windows_sandbox_child_process,
)


class MxcWindowsSandboxStateAwareTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="mxc-wsb-state-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()

    def _runner(self, sandbox_ids: list[str], *, fail_deprovision: bool = False, fail_start: bool = False):
        calls: list[dict[str, object]] = []
        identities = iter(sandbox_ids)

        def run(argv, **kwargs):
            config = json.loads(base64.b64decode(argv[3]).decode("utf-8"))
            calls.append(config)
            if config["phase"] == "provision":
                payload = {"result": {"sandboxId": next(identities)}}
                exit_code = 0
            elif (config["phase"] == "deprovision" and fail_deprovision) or (config["phase"] == "start" and fail_start):
                payload = {"error": {"code": "backend_error", "message": "redacted"}}
                exit_code = 1
            else:
                payload = {"result": {}}
                exit_code = 0
            kwargs["stdout"].write(json.dumps(payload).encode("utf-8"))
            return subprocess.CompletedProcess(argv, exit_code)

        return run, calls

    def _manager(self) -> MxcWindowsSandboxManager:
        manager = MxcWindowsSandboxManager(executor_directory=self.root / "tools")
        manager._environment = lambda: {"PATH": "C:\\Windows\\System32"}  # type: ignore[method-assign]
        manager._host_process_count = lambda: 0  # type: ignore[method-assign]
        return manager

    def test_phase_contract_keeps_mapping_immutable_after_provision(self) -> None:
        provision = _phase_config(
            "provision",
            filesystem={"readwritePaths": ["E:\\repo"], "readonlyPaths": ["C:\\tools"]},
        )
        self.assertEqual(provision["version"], "0.10.0-alpha")
        self.assertEqual(provision["containment"], "windows_sandbox")
        self.assertEqual(provision["filesystem"]["readwritePaths"], ["E:\\repo"])
        self.assertEqual(
            _phase_config("exec", "wsb:deadbeef", process={"timeout": 5000})["sandboxId"],
            "wsb:deadbeef",
        )
        self.assertNotIn("filesystem", _phase_config("exec", "wsb:deadbeef", process={"timeout": 5000}))

    def test_cold_start_refuses_lingering_host_vm_without_provision_or_replay(self) -> None:
        manager = self._manager()
        manager._host_process_count = lambda: 1
        with patch.object(state_aware, "verify_mxc_windows_sandbox_candidate", return_value={}):
            with patch.object(state_aware.subprocess, "run") as run:
                with self.assertRaises(ToolFailure) as observed:
                    manager.acquire(self.root, [])
        self.assertEqual(observed.exception.code, "SANDBOX_HOST_BUSY")
        run.assert_not_called()
        self.assertIsNone(manager._active)
        self.assertTrue(manager._lock.acquire(timeout=0.1))
        manager._lock.release()

    def test_warm_owned_vm_reuses_lease_without_foreign_host_guard(self) -> None:
        runner, calls = self._runner(["wsb:11111111"])
        manager = self._manager()
        with patch.object(state_aware, "verify_mxc_windows_sandbox_candidate", return_value={}):
            with patch.object(state_aware.subprocess, "run", side_effect=runner):
                first = manager.acquire(self.root, [])
                manager.release()
                manager._host_process_count = Mock(side_effect=AssertionError("owned VM must not be rejected"))
                second = manager.acquire(self.root, [])
                manager.release()
        self.assertEqual(first, second)
        manager._host_process_count.assert_not_called()
        self.assertEqual([call["phase"] for call in calls], ["provision", "start"])

    def test_host_observation_accepts_only_bounded_numeric_process_count(self) -> None:
        manager = self._manager()
        with patch.object(state_aware, "_system_root", return_value=self.root):
            with patch.object(state_aware.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, stdout=b"2\r\n")) as run:
                self.assertEqual(MxcWindowsSandboxManager._host_process_count(manager), 2)
        self.assertIn("vmmemWindowsSandbox", run.call_args.args[0][-1])
        self.assertNotIn("shell", run.call_args.kwargs)
        for status, output in ((1, b"0"), (0, b"-1"), (0, b"private arbitrary output")):
            with self.subTest(status=status, output=output):
                with patch.object(state_aware, "_system_root", return_value=self.root):
                    with patch.object(state_aware.subprocess, "run", return_value=subprocess.CompletedProcess([], status, stdout=output)):
                        with self.assertRaises(ToolFailure) as observed:
                            MxcWindowsSandboxManager._host_process_count(manager)
                self.assertEqual(observed.exception.code, "SANDBOX_HOST_STATE_UNAVAILABLE")
                self.assertNotIn("private arbitrary output", observed.exception.message)

    def test_unavailable_host_observation_never_provisions(self) -> None:
        manager = self._manager()
        manager._host_process_count = Mock(side_effect=ToolFailure("SANDBOX_HOST_STATE_UNAVAILABLE", "Unavailable."))
        with patch.object(state_aware, "verify_mxc_windows_sandbox_candidate", return_value={}):
            with patch.object(state_aware.subprocess, "run") as run:
                with self.assertRaises(ToolFailure) as observed:
                    manager.acquire(self.root, [])
        self.assertEqual(observed.exception.code, "SANDBOX_HOST_STATE_UNAVAILABLE")
        run.assert_not_called()
        self.assertTrue(manager._lock.acquire(timeout=0.1))
        manager._lock.release()

    def test_launcher_process_cwd_uses_the_same_guest_path_as_the_request_payload(self) -> None:
        workdir = self.root / "src"
        workdir.mkdir()
        manager = Mock()
        manager.executor_path = self.root / "tools" / "wxc-exec.exe"
        manager.acquire.return_value = "wsb:0123abcd"
        manager._environment.return_value = {"PATH": "C:\\Windows\\System32"}

        def guest_path(value, _mappings):
            relative = Path(value).relative_to(self.root)
            suffix = str(relative).replace("/", "\\")
            return GUEST_WORKSPACE_SHARE if suffix in {"", "."} else f"{GUEST_WORKSPACE_SHARE}\\{suffix}"

        with patch.object(state_aware, "os", SimpleNamespace(name="nt")):
            with patch.object(state_aware, "_system_root", return_value=self.root):
                with patch.object(state_aware, "_host_toolchains", return_value=([], [])):
                    with patch.object(state_aware, "_guest_share_map", return_value=[(self.root, GUEST_WORKSPACE_SHARE)]):
                        with patch.object(state_aware, "_guest_path_for_host", side_effect=guest_path):
                            with patch.object(state_aware, "_validate_workspace", return_value=(self.root, workdir)):
                                with patch.object(
                                    state_aware,
                                    "_resolve_executable",
                                    return_value=([str(self.root / "node.exe"), "--version"], []),
                                ):
                                    invocation = build_mxc_windows_sandbox_invocation(
                                        ["node", "--version"],
                                        manager=manager,
                                        workspace_root=self.root,
                                        workdir=workdir,
                                        timeout_ms=5_000,
                                    )
        self.addCleanup(cleanup_mxc_windows_sandbox_invocation, invocation, abort=True)

        config = json.loads(base64.b64decode(invocation.argv[3]).decode("utf-8"))
        request = json.loads((invocation.scratch_directory / "exec-request.json").read_text(encoding="utf-8"))
        expected_guest_cwd = GUEST_WORKSPACE_SHARE + "\\src"
        self.assertEqual(config["process"]["cwd"], expected_guest_cwd)
        self.assertEqual(request["cwd"], expected_guest_cwd)
        self.assertNotIn(str(workdir), json.dumps(config))

    def test_manager_reuses_the_warm_vm_for_same_workspace_and_toolchains(self) -> None:
        runner, calls = self._runner(["wsb:0123abcd"])
        manager = self._manager()
        with patch("coding_tools_mcp.windows_mxc_state_aware.verify_mxc_windows_sandbox_candidate", return_value={}):
            with patch("coding_tools_mcp.windows_mxc_state_aware.subprocess.run", side_effect=runner):
                self.assertTrue(manager._lock.acquire(timeout=1))
                first = manager._ensure_active(self.root, [])
                manager._lock.release()
                self.assertTrue(manager._lock.acquire(timeout=1))
                second = manager._ensure_active(self.root, [])
                manager._lock.release()
        self.assertEqual(first, "wsb:0123abcd")
        self.assertEqual(second, first)
        self.assertEqual([call["phase"] for call in calls], ["provision", "start"])

    def test_manager_host_environment_keeps_system_drive_explicit(self) -> None:
        manager = MxcWindowsSandboxManager(executor_directory=self.root / "tools")
        with patch.object(state_aware, "os", SimpleNamespace(environ={}, pathsep=";")):
            with patch.object(state_aware, "_system_root", return_value=PureWindowsPath(r"D:\Windows")):
                environment = manager._environment()
        self.assertEqual(environment["SystemDrive"], "D:")
        self.assertEqual(environment["SystemRoot"], r"D:\Windows")

    def test_child_process_probe_releases_each_command_lease_once(self) -> None:
        events: list[tuple[str, str | bool]] = []
        manager = Mock()
        manager.release.side_effect = lambda *, abort=False: events.append(("release", abort)) or True
        manager.close.side_effect = lambda: events.append(("close", True)) or True
        invocations: list[MxcWindowsSandboxInvocation] = []
        node_payload_holder: dict[str, str] = {}

        def build(argv, **kwargs):
            phase = (
                "node"
                if argv[0] == "node"
                else "npm-prefix"
                if argv[1] == "prefix"
                else "npm-test"
            )
            events.append(("build", phase))
            expected_releases = {"node": 0, "npm-prefix": 1, "npm-test": 2}[phase]
            self.assertEqual(manager.release.call_count, expected_releases)
            invocation = MxcWindowsSandboxInvocation(
                argv=tuple(argv),
                environment={},
                scratch_directory=self.root / f"scratch-{phase}",
                workspace_root=self.root,
                sandbox_id="wsb:0123abcd",
                manager=manager,
            )
            invocations.append(invocation)
            if phase == "node":
                guest_cwd = f"{GUEST_WORKSPACE_SHARE}\\{kwargs['workdir'].name}"
                payload = {
                    "workspace_realpath": GUEST_WORKSPACE_SHARE,
                    "cwd_realpath": guest_cwd,
                    "temp_created": True,
                    "child_status": 0,
                    "child_marker": True,
                    "reason": None,
                }
                node_payload_holder["payload"] = json.dumps(payload)
                node_payload_holder["guest_cwd"] = guest_cwd
            return invocation

        def run_child(invocation, *, timeout_seconds):
            phase = Path(invocation.scratch_directory).name.removeprefix("scratch-")
            events.append(("run", phase))
            output = {
                "node": node_payload_holder["payload"],
                "npm-prefix": node_payload_holder["guest_cwd"],
                "npm-test": "MXC_WSB_NPM_OK",
            }[phase]
            return subprocess.CompletedProcess(invocation.argv, 0, stdout=output)

        guest_path = lambda value, _mappings: (
            GUEST_WORKSPACE_SHARE
            if Path(value) == self.root
            else f"{GUEST_WORKSPACE_SHARE}\\{Path(value).name}"
        )
        windows_path_key = lambda value: str(value).replace("/", "\\").casefold()
        with patch.object(state_aware, "os", SimpleNamespace(name="nt")):
            with patch.object(state_aware, "MxcWindowsSandboxManager", return_value=manager):
                with patch.object(state_aware, "_validate_workspace", return_value=(self.root, [])):
                    with patch.object(state_aware, "build_mxc_windows_sandbox_invocation", side_effect=build):
                        with patch.object(state_aware, "_run_child", side_effect=run_child):
                            with patch.object(state_aware, "_safe_remove_scratch", return_value=True):
                                with patch.object(state_aware, "_guest_path_for_host", side_effect=guest_path):
                                    with patch.object(state_aware, "_windows_path_key", side_effect=windows_path_key):
                                        result = probe_mxc_windows_sandbox_child_process(str(self.root))

        self.assertTrue(result["available"], result)
        self.assertEqual(manager.release.call_count, 3)
        self.assertEqual(
            events,
            [
                ("build", "node"),
                ("run", "node"),
                ("release", False),
                ("build", "npm-prefix"),
                ("run", "npm-prefix"),
                ("release", False),
                ("build", "npm-test"),
                ("run", "npm-test"),
                ("release", False),
                ("close", True),
            ],
        )

    def test_child_probe_refuses_to_run_npm_script_when_prefix_is_wrong(self) -> None:
        events: list[tuple[str, str | bool]] = []
        manager = Mock()
        manager.release.side_effect = lambda *, abort=False: events.append(("release", abort)) or True
        manager.close.side_effect = lambda: events.append(("close", True)) or True
        node_payload_holder: dict[str, str] = {}

        def build(argv, **kwargs):
            phase = "node" if argv[0] == "node" else "npm-prefix" if argv[1] == "prefix" else "npm-test"
            events.append(("build", phase))
            invocation = MxcWindowsSandboxInvocation(
                argv=tuple(argv),
                environment={},
                scratch_directory=self.root / f"scratch-{phase}",
                workspace_root=self.root,
                sandbox_id="wsb:0123abcd",
                manager=manager,
            )
            if phase == "node":
                node_payload_holder["guest_cwd"] = f"{GUEST_WORKSPACE_SHARE}\\{kwargs['workdir'].name}"
            return invocation

        def run_child(invocation, *, timeout_seconds):
            phase = Path(invocation.scratch_directory).name.removeprefix("scratch-")
            events.append(("run", phase))
            if phase == "node":
                payload = {
                    "workspace_realpath": GUEST_WORKSPACE_SHARE,
                    "cwd_realpath": node_payload_holder["guest_cwd"],
                    "temp_created": True,
                    "child_status": 0,
                    "child_marker": True,
                    "reason": None,
                }
                output = json.dumps(payload)
            elif phase == "npm-prefix":
                output = f"{GUEST_WORKSPACE_SHARE}\\wrong-package\n"
            else:
                self.fail("the npm test script must not run after a prefix mismatch")
            return subprocess.CompletedProcess(invocation.argv, 0, stdout=output)

        def guest_path(value, _mappings):
            target = Path(value)
            return GUEST_WORKSPACE_SHARE if target == self.root else f"{GUEST_WORKSPACE_SHARE}\\{target.name}"

        with patch.object(state_aware, "os", SimpleNamespace(name="nt")):
            with patch.object(state_aware, "MxcWindowsSandboxManager", return_value=manager):
                with patch.object(state_aware, "_validate_workspace", return_value=(self.root, [])):
                    with patch.object(state_aware, "build_mxc_windows_sandbox_invocation", side_effect=build):
                        with patch.object(state_aware, "_run_child", side_effect=run_child):
                            with patch.object(state_aware, "_safe_remove_scratch", return_value=True):
                                with patch.object(state_aware, "_guest_path_for_host", side_effect=guest_path):
                                    with patch.object(
                                        state_aware,
                                        "_windows_path_key",
                                        side_effect=lambda value: str(value).replace("/", "\\").casefold(),
                                    ):
                                        result = probe_mxc_windows_sandbox_child_process(str(self.root))

        self.assertFalse(result["available"])
        self.assertEqual(result["reason"], "WINDOWS_NPM_WORKDIR_MISMATCH")
        self.assertEqual([phase for kind, phase in events if kind == "build"], ["node", "npm-prefix"])
        self.assertEqual(manager.release.call_count, 2)

    def test_child_probe_reports_bounded_lifecycle_failure_details(self) -> None:
        manager = Mock()
        manager.close.return_value = True
        failure = ToolFailure(
            "SANDBOX_STATE_PHASE_FAILED",
            "The Windows Sandbox lifecycle phase failed.",
            details={"phase": "start", "backend_error_code": "backend_error", "private_message": "do-not-surface"},
        )
        with patch.object(state_aware, "os", SimpleNamespace(name="nt")):
            with patch.object(state_aware, "MxcWindowsSandboxManager", return_value=manager):
                with patch.object(state_aware, "_validate_workspace", return_value=(self.root, [])):
                    with patch.object(state_aware, "build_mxc_windows_sandbox_invocation", side_effect=failure):
                        result = probe_mxc_windows_sandbox_child_process(str(self.root))
        self.assertFalse(result["available"])
        self.assertEqual(result["reason"], "SANDBOX_STATE_PHASE_FAILED_START_BACKEND_ERROR")
        self.assertNotIn("private_message", result)
        self.assertTrue(manager.close.called)

    def test_child_probe_classifies_nonzero_runner_exit_after_parsing_payload(self) -> None:
        manager = Mock()
        manager.release.return_value = True
        manager.close.return_value = True
        invocation = MxcWindowsSandboxInvocation(
            argv=("node", "-e", "probe"),
            environment={},
            scratch_directory=self.root / "scratch-node",
            workspace_root=self.root,
            sandbox_id="wsb:0123abcd",
            manager=manager,
        )
        guest_path = lambda value, _mappings: (
            GUEST_WORKSPACE_SHARE
            if Path(value) == self.root
            else f"{GUEST_WORKSPACE_SHARE}\\{Path(value).name}"
        )
        windows_path_key = lambda value: str(value).replace("/", "\\").casefold()

        def run_child(*_args, **_kwargs):
            payload = {
                "workspace_realpath": GUEST_WORKSPACE_SHARE,
                "cwd_realpath": f"{GUEST_WORKSPACE_SHARE}\\expected",
                "temp_created": True,
                "child_status": 0,
                "child_marker": True,
                "reason": None,
            }
            return subprocess.CompletedProcess(invocation.argv, 1, stdout=json.dumps(payload))

        with patch.object(state_aware, "os", SimpleNamespace(name="nt")):
            with patch.object(state_aware, "MxcWindowsSandboxManager", return_value=manager):
                with patch.object(state_aware, "_validate_workspace", return_value=(self.root, [])):
                    with patch.object(state_aware, "build_mxc_windows_sandbox_invocation", return_value=invocation):
                        with patch.object(state_aware, "_run_child", side_effect=run_child):
                            with patch.object(state_aware, "_safe_remove_scratch", return_value=True):
                                with patch.object(state_aware, "_guest_path_for_host", side_effect=guest_path):
                                    with patch.object(state_aware, "_windows_path_key", side_effect=windows_path_key):
                                        result = probe_mxc_windows_sandbox_child_process(str(self.root))
        self.assertFalse(result["available"])
        self.assertEqual(result["reason"], "CHILD_PROCESS_PROBE_EXIT_1")
        self.assertEqual(manager.release.call_count, 1)

    def test_child_probe_distinguishes_empty_from_unparseable_stdout(self) -> None:
        for output, reason in (
            ("", "CHILD_PROCESS_PROBE_OUTPUT_EMPTY_EXIT_0"),
            ("launcher emitted no receipt", "CHILD_PROCESS_PROBE_OUTPUT_UNPARSEABLE_EXIT_0"),
        ):
            with self.subTest(reason=reason):
                manager = Mock()
                manager.release.return_value = True
                manager.close.return_value = True
                invocation = MxcWindowsSandboxInvocation(
                    argv=("node", "-e", "probe"),
                    environment={},
                    scratch_directory=self.root / "scratch-node",
                    workspace_root=self.root,
                    sandbox_id="wsb:0123abcd",
                    manager=manager,
                )
                with patch.object(state_aware, "os", SimpleNamespace(name="nt")):
                    with patch.object(state_aware, "MxcWindowsSandboxManager", return_value=manager):
                        with patch.object(state_aware, "_validate_workspace", return_value=(self.root, [])):
                            with patch.object(state_aware, "build_mxc_windows_sandbox_invocation", return_value=invocation):
                                with patch.object(
                                    state_aware,
                                    "_run_child",
                                    return_value=subprocess.CompletedProcess(invocation.argv, 0, stdout=output),
                                ):
                                    with patch.object(state_aware, "_safe_remove_scratch", return_value=True):
                                        result = probe_mxc_windows_sandbox_child_process(str(self.root))
                self.assertFalse(result["available"])
                self.assertEqual(result["reason"], reason)
                self.assertEqual(manager.release.call_count, 1)

    def test_workspace_change_deprovisions_exact_old_id_before_provisioning_new(self) -> None:
        runner, calls = self._runner(["wsb:11111111", "wsb:22222222"])
        manager = self._manager()
        other = self.root / "other"
        other.mkdir()
        with patch("coding_tools_mcp.windows_mxc_state_aware.verify_mxc_windows_sandbox_candidate", return_value={}):
            with patch("coding_tools_mcp.windows_mxc_state_aware.subprocess.run", side_effect=runner):
                self.assertTrue(manager._lock.acquire(timeout=1))
                first = manager._ensure_active(self.root, [])
                manager._lock.release()
                self.assertTrue(manager._lock.acquire(timeout=1))
                second = manager._ensure_active(other, [])
                manager._lock.release()
        self.assertEqual(first, "wsb:11111111")
        self.assertEqual(second, "wsb:22222222")
        self.assertEqual(
            [(call["phase"], call.get("sandboxId")) for call in calls],
            [
                ("provision", None),
                ("start", "wsb:11111111"),
                ("deprovision", "wsb:11111111"),
                ("provision", None),
                ("start", "wsb:22222222"),
            ],
        )

    def test_failed_teardown_marks_manager_uncertain_and_blocks_new_scope(self) -> None:
        runner, _calls = self._runner(["wsb:11111111", "wsb:22222222"], fail_deprovision=True)
        manager = self._manager()
        other = self.root / "other"
        other.mkdir()
        with patch("coding_tools_mcp.windows_mxc_state_aware.verify_mxc_windows_sandbox_candidate", return_value={}):
            with patch("coding_tools_mcp.windows_mxc_state_aware.subprocess.run", side_effect=runner):
                self.assertTrue(manager._lock.acquire(timeout=1))
                manager._ensure_active(self.root, [])
                manager._lock.release()
                self.assertTrue(manager._lock.acquire(timeout=1))
                with self.assertRaises(ToolFailure) as context:
                    manager._ensure_active(other, [])
                manager._lock.release()
        self.assertEqual(context.exception.code, "SANDBOX_TEARDOWN_UNCONFIRMED")
        self.assertTrue(manager._uncertain)

    def test_start_failure_retains_cause_and_deprovisions_once_without_replay(self) -> None:
        runner, calls = self._runner(["wsb:11111111"], fail_start=True)
        manager = self._manager()
        with patch.object(state_aware, "verify_mxc_windows_sandbox_candidate", return_value={}):
            with patch.object(state_aware.subprocess, "run", side_effect=runner):
                with self.assertRaises(ToolFailure) as observed:
                    manager.acquire(self.root, [])
        self.assertEqual(observed.exception.code, "SANDBOX_STATE_PHASE_FAILED")
        self.assertEqual(observed.exception.details, {"phase": "start", "backend_error_code": "backend_error"})
        self.assertEqual([call["phase"] for call in calls], ["provision", "start", "deprovision"])
        self.assertIsNone(manager._active)
        self.assertFalse(manager._uncertain)
        self.assertTrue(manager._lock.acquire(timeout=0.1))
        manager._lock.release()

    def test_backend_ready_timeout_is_distinct_from_adapter_timeout_and_private_text(self) -> None:
        manager = self._manager()
        def run(argv, **kwargs):
            payload = {"error": {"code": "backend_error", "message": "daemon did not become ready within 120s"}}
            kwargs["stdout"].write(json.dumps(payload).encode())
            return subprocess.CompletedProcess(argv, 1)
        with patch.object(state_aware, "verify_mxc_windows_sandbox_candidate", return_value={}):
            with patch.object(state_aware.subprocess, "run", side_effect=run):
                with self.assertRaises(ToolFailure) as observed:
                    manager._run_envelope(_phase_config("start", "wsb:11111111"))
        self.assertEqual(observed.exception.code, "SANDBOX_STATE_START_READY_TIMEOUT")
        self.assertEqual(observed.exception.details, {"phase": "start", "backend_error_code": "start_ready_timeout"})
        self.assertNotIn("120s", observed.exception.message)

    def test_start_failure_with_unconfirmed_cleanup_blocks_next_acquire(self) -> None:
        runner, calls = self._runner(["wsb:11111111"], fail_start=True, fail_deprovision=True)
        manager = self._manager()
        with patch.object(state_aware, "verify_mxc_windows_sandbox_candidate", return_value={}):
            with patch.object(state_aware.subprocess, "run", side_effect=runner):
                with self.assertRaises(ToolFailure) as observed:
                    manager.acquire(self.root, [])
                self.assertEqual(observed.exception.details["phase"], "start")
                with self.assertRaises(ToolFailure) as blocked:
                    manager.acquire(self.root, [])
        self.assertEqual(blocked.exception.code, "SANDBOX_STATE_UNCERTAIN")
        self.assertEqual([call["phase"] for call in calls], ["provision", "start", "deprovision"])

    def test_launcher_hides_request_path_in_a_cmd_safe_base64_argument(self) -> None:
        launcher = _build_launcher_command(
            Path(r"C:\CodexWorkspace\share-0\.mxc-wsb-probe-0123456789abcdef0123456789abcdef\space ' quote\exec-request.json")
        )
        encoded = launcher.rsplit(" ", 1)[1]
        decoded = base64.b64decode(encoded).decode("utf-16le")
        self.assertRegex(encoded, r"^[A-Za-z0-9+/=]+$")
        self.assertIn("space '' quote", decoded)
        self.assertNotIn("-Command", launcher)
        self.assertLess(len(launcher), 8_000)
        self.assertIn("[void]($stdout.GetAwaiter().GetResult())", decoded)
        self.assertIn("[void]($stderr.GetAwaiter().GetResult())", decoded)
        self.assertIn("[void]($stdin.GetAwaiter().GetResult())", decoded)

    def test_host_workspace_and_toolchain_paths_translate_to_disjoint_guest_c_roots(self) -> None:
        workspace_path = self.root / "src" / "nested"
        workspace_path.parent.mkdir(parents=True)
        toolchain = self.root.parent / (self.root.name + "-node-toolchain")
        toolchain.mkdir()
        self.addCleanup(shutil.rmtree, toolchain, ignore_errors=True)
        node_path = toolchain / "node.exe"
        mappings = [
            (self.root, GUEST_WORKSPACE_SHARE),
            (toolchain, GUEST_TOOLCHAIN_SHARE_PREFIX + "0"),
        ]
        self.assertEqual(
            _guest_path_for_host(workspace_path, mappings),
            GUEST_WORKSPACE_SHARE + "\\src\\nested",
        )
        self.assertEqual(
            _guest_path_for_host(node_path, mappings),
            GUEST_TOOLCHAIN_SHARE_PREFIX + "0\\node.exe",
        )
        self.assertEqual(
            _guest_path_for_host("relative\\script.js", mappings),
            "relative\\script.js",
        )
        self.assertFalse(
            GUEST_WORKSPACE_SHARE.startswith(GUEST_TOOLCHAIN_SHARE_PREFIX)
        )

    def test_environment_path_lists_translate_only_inside_explicit_shares(self) -> None:
        toolchain = self.root.parent / (self.root.name + "-git-toolchain")
        toolchain.mkdir()
        self.addCleanup(shutil.rmtree, toolchain, ignore_errors=True)
        mappings = [
            (self.root, GUEST_WORKSPACE_SHARE),
            (toolchain, GUEST_TOOLCHAIN_SHARE_PREFIX + "1"),
        ]
        value = str(self.root / "node_modules") + ";" + str(toolchain / "cmd")
        self.assertEqual(
            _guest_environment_value(value, mappings),
            GUEST_WORKSPACE_SHARE + "\\node_modules;" + GUEST_TOOLCHAIN_SHARE_PREFIX + "1\\cmd",
        )

    def test_shell_and_reserved_environment_overrides_remain_denied(self) -> None:
        with self.assertRaises(ToolFailure) as shell_error:
            _validate_argv_and_environment(["powershell.exe", "-Command", "whoami"], {})
        self.assertEqual(shell_error.exception.code, "SANDBOX_SHELL_COMMAND_DENIED")
        with self.assertRaises(ToolFailure) as env_error:
            _validate_argv_and_environment(["node", "--version"], {"PATH": "C:\\"})
        self.assertEqual(env_error.exception.code, "SANDBOX_ENV_OVERRIDE_DENIED")

    def test_command_cleanup_removes_only_exact_workspace_scratch_and_propagates_abort(self) -> None:
        class Manager:
            def __init__(self) -> None:
                self.abort_values: list[bool] = []

            def release(self, *, abort: bool = False) -> bool:
                self.abort_values.append(abort)
                return True

        manager = Manager()
        scratch = self.root / ".mxc-wsb-command"
        scratch.mkdir()
        (scratch / "exec-request.json").write_text("{}", encoding="utf-8")
        invocation = MxcWindowsSandboxInvocation(
            argv=("wxc-exec.exe",),
            environment={},
            scratch_directory=scratch,
            workspace_root=self.root,
            sandbox_id="wsb:0123abcd",
            manager=manager,  # type: ignore[arg-type]
        )
        self.assertTrue(cleanup_mxc_windows_sandbox_invocation(invocation, abort=True))
        self.assertFalse(scratch.exists())
        self.assertEqual(manager.abort_values, [True])

    def test_cleanup_refuses_scratch_outside_registered_workspace(self) -> None:
        class Manager:
            abort_value: bool | None = None

            def release(self, *, abort: bool = False) -> bool:
                self.abort_value = abort
                return True

        manager = Manager()
        nested = self.root / "nested"
        nested.mkdir()
        outside = nested / ".mxc-wsb-command-outside"
        outside.mkdir()
        (outside / "keep.txt").write_text("untouched", encoding="utf-8")
        try:
            invocation = MxcWindowsSandboxInvocation(
                argv=("wxc-exec.exe",),
                environment={},
                scratch_directory=outside,
                workspace_root=self.root,
                sandbox_id="wsb:0123abcd",
                manager=manager,  # type: ignore[arg-type]
            )
            self.assertFalse(cleanup_mxc_windows_sandbox_invocation(invocation))
            self.assertTrue((outside / "keep.txt").is_file())
            self.assertIs(manager.abort_value, True)
        finally:
            shutil.rmtree(outside)

    def test_uncertain_sandbox_cleanup_is_retained_as_a_session_warning(self) -> None:
        session = ExecSession(session_id="wsb-cleanup-warning", process=Mock())
        session.cleanup_callback = lambda: False
        session.cleanup_sandbox_state()
        self.assertTrue(any("cleanup could not be confirmed" in warning for warning in session.warnings))


if __name__ == "__main__":
    unittest.main()
