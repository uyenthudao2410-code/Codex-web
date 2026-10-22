from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from coding_tools_mcp.errors import ToolFailure
from coding_tools_mcp.processes import WindowsJobLimits, spawn_process, require_windows_native_token
from coding_tools_mcp.runtime_config import is_filtered_env_var
from coding_tools_mcp.server import Runtime
from coding_tools_mcp.tool_schema import validate_arguments
from coding_tools_mcp.windows_execution_policy import decide_windows_execution, safe_native_argv
from coding_tools_mcp.windows_mxc_sandbox import _executor_path, _probe_executor, _system_root


class WindowsExecutionPolicyTests(unittest.TestCase):
    def decide(self, argv: list[str], **args):
        return decide_windows_execution(argv, args, attested_bridge=True)

    def test_versions_and_metadata_are_native_without_project_trust(self):
        for argv in (["node", "--version"], ["python.exe", "-V"], ["git", "status", "--short"], ["git", "diff", "--stat"], ["git", "log", "--oneline", "-n", "10"]):
            with self.subTest(argv=argv):
                result = self.decide(argv)
                self.assertEqual(result.execution_backend, "native")
                self.assertEqual(result.isolation_level, "process_container")
                self.assertEqual(result.policy_decision, "native_safe_command")

    def test_build_scripts_and_git_config_overrides_require_approval(self):
        for argv in (["npm", "test"], ["dotnet", "--version"], ["dotnet", "build"], ["node", "script.js"], ["git", "-c", "core.fsmonitor=runner", "status"], ["git", "diff", "--ext-diff"], ["git", "log", "--max-count=101"], [r"C:\workspace\node.exe", "--version"]):
            with self.subTest(argv=argv):
                self.assertEqual(self.decide(argv).execution_backend, "isolated")
                with self.assertRaises(ToolFailure) as context:
                    self.decide(argv, _windows_execution_mode="native_only")
                self.assertEqual(context.exception.code, "NATIVE_EXECUTION_NOT_APPROVED")
                self.assertFalse(context.exception.details["execution_started"])

    def test_exact_approved_prefix_and_explicit_isolation(self):
        approved = {"_windows_native_argv_prefixes": [["npm", "test"]]}
        self.assertEqual(self.decide(["npm", "test", "--", "case"], **approved).policy_decision, "native_explicit_approval")
        self.assertEqual(self.decide(["npm", "install"], **approved).execution_backend, "isolated")
        result = self.decide(["node", "--version"], _windows_execution_mode="isolated")
        self.assertEqual(result.policy_decision, "isolated_preferred")
        self.assertEqual(result.isolation_level, "hypervisor")

    def test_policy_overrides_require_attested_bridge(self):
        for args in ({"_windows_execution_mode": "native_first"}, {"_windows_native_argv_prefixes": [["npm", "test"]]}):
            with self.assertRaises(ToolFailure) as context:
                decide_windows_execution(["node", "--version"], args, attested_bridge=False)
            self.assertEqual(context.exception.code, "WINDOWS_EXECUTION_POLICY_DENIED")
        with self.assertRaises(ToolFailure):
            self.decide(["node", "--version"], _windows_execution_mode="automatic")
        for prefixes in ([["cmd", "/c"]], [["node", "-e", "x;bad"]], [["../node"]], [["node", 1]]):
            with self.assertRaises(ToolFailure):
                self.decide(["node", "--version"], _windows_native_argv_prefixes=prefixes)

    def test_local_policy_is_outside_public_schema_and_requires_verified_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Runtime(Path(directory))
            args = {"cmd": "node", "argv": ["node", "--version"], "_windows_execution_mode": "native_only", "_windows_native_argv_prefixes": []}
            try:
                for identity in (None, {"client_id": "electron-control-plane-exec-bridge", "client_type": "electron", "attestation_verified": False}):
                    runtime.request_context.hub_client = identity
                    with self.assertRaises(Exception):
                        validate_arguments("exec_command", runtime._exec_public_schema_arguments(args))
                runtime.request_context.hub_client = {"client_id": "electron-control-plane-exec-bridge", "client_type": "electron", "attestation_verified": True}
                projection = runtime._exec_public_schema_arguments(args)
                validate_arguments("exec_command", projection)
                self.assertNotIn("_windows_execution_mode", projection)
                self.assertIn("_windows_execution_mode", args)
            finally:
                runtime.close()

    def test_git_metadata_disables_executable_helpers(self):
        argv = safe_native_argv(["git", "diff", "--stat"])
        self.assertIn("core.fsmonitor=false", argv)
        self.assertIn("--no-pager", argv)
        self.assertIn("--no-optional-locks", argv)
        self.assertIn("--no-ext-diff", argv)
        self.assertIn("--no-textconv", argv)
        self.assertIn("log.showSignature=false", argv)
        self.assertIn("diff.submodule=short", argv)
        log = safe_native_argv(["git", "log", "--oneline"])
        self.assertIn("--no-show-signature", log)
        self.assertIn("--no-ext-diff", log)
        self.assertIn("--no-textconv", log)

    def test_native_job_limits_unavailable_never_spawns(self):
        with patch("coding_tools_mcp.processes.windows_job_object_enabled", return_value=False), patch("coding_tools_mcp.processes.subprocess.Popen") as popen:
            with self.assertRaises(ToolFailure) as context:
                spawn_process(["node", "--version"], cwd=".", shell=False, env={}, tty=False, popen_kwargs={}, windows_job_limits=WindowsJobLimits())
        self.assertEqual(context.exception.code, "NATIVE_RESOURCE_LIMITS_UNAVAILABLE")
        popen.assert_not_called()

    def test_elevated_or_high_integrity_native_host_is_denied(self):
        for posture in ({"elevated": True, "integrity_rid": 0x2000}, {"elevated": False, "integrity_rid": 0x3000}):
            with patch("coding_tools_mcp.processes.windows_host_token_posture", return_value=posture):
                with self.assertRaises(ToolFailure) as context:
                    require_windows_native_token()
            self.assertEqual(context.exception.code, "NATIVE_ELEVATED_HOST_DENIED")
        with patch("coding_tools_mcp.processes.windows_host_token_posture", return_value={"elevated": False, "integrity_rid": 0x2000}):
            require_windows_native_token()

    def test_dotnet_loader_and_profiler_credentials_are_not_forwarded(self):
        for key in ("DOTNET_STARTUP_HOOKS", "DOTNET_ADDITIONAL_DEPS", "DOTNET_SHARED_STORE", "COR_PROFILER", "CORECLR_PROFILER_PATH"):
            self.assertTrue(is_filtered_env_var(key, "fixture"))


@unittest.skipUnless(os.name == "nt", "Windows native ProcessContainer integration")
class WindowsNativeExecutionIntegrationTests(unittest.TestCase):
    def setUp(self):
        mode = patch("coding_tools_mcp.exec_tools.is_sandboxed_execution", return_value=True)
        mode.start()
        self.addCleanup(mode.stop)

    @classmethod
    def setUpClass(cls):
        try:
            _probe_executor(_executor_path(), _system_root())
        except ToolFailure as error:
            raise unittest.SkipTest(f"Native ProcessContainer unavailable: {error.code}")

    def test_ten_native_commands_retain_job_and_backend_receipts(self):
        with tempfile.TemporaryDirectory(prefix="native-first-proof-", dir=str(Path(__file__).resolve().anchor)) as directory:
            runtime = Runtime(Path(directory))
            runtime.request_context.hub_client = {"client_id": "electron-control-plane-exec-bridge", "client_type": "electron", "attestation_verified": True}
            commands = set()
            jobs = set()
            try:
                # This test never selects or starts Windows Sandbox.
                with patch("coding_tools_mcp.exec_tools.build_mxc_windows_sandbox_invocation") as isolated:
                    for _ in range(10):
                        result = runtime.exec_command({"cmd": "node", "argv": ["node", "--version"], "_windows_execution_mode": "native_only", "yield_time_ms": 30_000, "verbosity": "full"})
                        command_id = result["command_id"]
                        while result["status"] == "running":
                            result = runtime.command_control({"action": "poll", "command_id": command_id, "yield_time_ms": 1000, "verbosity": "full"})
                        self.assertEqual(result["exit_code"], 0, result)
                        self.assertEqual(result["execution_backend"], "native")
                        self.assertEqual(result["isolation_level"], "process_container")
                        self.assertEqual(result["policy_decision"], "native_safe_command")
                        self.assertTrue(result["execution_owner"]["job_id"])
                        commands.add(command_id)
                        jobs.add(result["execution_owner"]["job_id"])
                        # A later observation must describe the same runner and Job.
                        again = runtime.command_control({"action": "poll", "command_id": command_id, "yield_time_ms": 0})
                        self.assertEqual(again["execution_backend"], "native")
                        self.assertEqual(again["execution_owner"], result["execution_owner"])
                    isolated.assert_not_called()
                self.assertEqual(len(commands), 10)
                self.assertEqual(len(jobs), 10)
                self.assertFalse(runtime.sessions)
            finally:
                runtime.close()

    def test_native_failure_never_starts_isolated_or_host_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Runtime(Path(directory))
            runtime.request_context.hub_client = {"client_id": "electron-control-plane-exec-bridge", "client_type": "electron", "attestation_verified": True}
            try:
                with patch("coding_tools_mcp.exec_tools.build_mxc_invocation", side_effect=ToolFailure("SANDBOX_UNAVAILABLE", "fixture capability denial", category="security")), patch("coding_tools_mcp.exec_tools.build_mxc_windows_sandbox_invocation") as isolated, patch("coding_tools_mcp.exec_tools.spawn_process") as spawn:
                    with self.assertRaises(ToolFailure) as context:
                        runtime.exec_command({"cmd": "node", "argv": ["node", "--version"]})
                self.assertEqual(context.exception.code, "SANDBOX_UNAVAILABLE")
                isolated.assert_not_called()
                spawn.assert_not_called()
                self.assertEqual(runtime.starting_sessions, 0)
                self.assertFalse(runtime.sessions)
            finally:
                runtime.close()

    def test_native_git_metadata_does_not_execute_repository_helpers(self):
        with tempfile.TemporaryDirectory(prefix="native-git-policy-", dir=str(Path(__file__).resolve().anchor)) as directory:
            root = Path(directory)
            runtime = Runtime(root)
            runtime.request_context.hub_client = {"client_id": "electron-control-plane-exec-bridge", "client_type": "electron", "attestation_verified": True}
            try:
                def git(*args: str, input_bytes: bytes | None = None) -> str:
                    result = subprocess.run(["git", "-C", directory, *args], input=input_bytes, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, env=runtime._git_env(), creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                    return result.stdout.decode("utf-8").strip()

                git("init", "--quiet")
                blob = git("hash-object", "-w", "--stdin", input_bytes=b"before\n")
                tree = git("mktree", input_bytes=f"100644 blob {blob}\ttracked.fixture\n".encode())
                raw_commit = (f"tree {tree}\nauthor Fixture <fixture@example.invalid> 1 +0000\ncommitter Fixture <fixture@example.invalid> 1 +0000\ngpgsig -----BEGIN PGP SIGNATURE-----\n fixture\n -----END PGP SIGNATURE-----\n\nmetadata-only fixture\n").encode("utf-8")
                commit = git("hash-object", "-t", "commit", "-w", "--stdin", input_bytes=raw_commit)
                git("update-ref", "HEAD", commit)
                git("read-tree", "HEAD")
                git("checkout-index", "-a")
                (root / "tracked.fixture").write_text("after\n", encoding="utf-8")
                (root / ".gitattributes").write_text("*.fixture diff=hostile\n", encoding="utf-8")
                sentinel = root / "gpg-helper-ran.txt"
                helper = root / "signature-helper.cmd"
                helper.write_text(f'@echo off\r\necho unexpected>"{sentinel}"\r\nexit /b 1\r\n', encoding="utf-8")
                git("config", "--local", "log.showSignature", "true")
                git("config", "--local", "gpg.program", str(helper))
                git("config", "--local", "core.fsmonitor", str(helper))
                git("config", "--local", "diff.external", str(helper))
                git("config", "--local", "diff.hostile.textconv", str(helper))
                git("config", "--local", "diff.submodule", "diff")
                with patch("coding_tools_mcp.exec_tools.build_mxc_windows_sandbox_invocation") as isolated:
                    for arguments, expected in ((["status", "--short"], "tracked.fixture"), (["diff"], "+after"), (["log", "--oneline", "-n", "1"], "metadata-only fixture")):
                        result = runtime.exec_command({"cmd": "git", "argv": ["git", *arguments], "_windows_execution_mode": "native_only", "yield_time_ms": 30_000, "verbosity": "full"})
                        while result["status"] == "running":
                            result = runtime.command_control({"action": "poll", "command_id": result["command_id"], "yield_time_ms": 1000, "verbosity": "full"})
                        self.assertEqual(result["exit_code"], 0, result)
                        self.assertIn(expected, result["stdout"])
                        self.assertFalse(sentinel.exists())
                        self.assertEqual(result["policy_decision"], "native_safe_command")
                    isolated.assert_not_called()
            finally:
                runtime.close()

    def test_unapproved_project_build_requires_isolation(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Runtime(Path(directory))
            runtime.request_context.hub_client = {"client_id": "electron-control-plane-exec-bridge", "client_type": "electron", "attestation_verified": True}
            try:
                with patch("coding_tools_mcp.exec_tools.windows_sandbox_feature_enabled", return_value=False), patch("coding_tools_mcp.exec_tools.build_mxc_invocation") as native, patch("coding_tools_mcp.exec_tools.spawn_process") as spawn:
                    with self.assertRaises(ToolFailure) as context:
                        runtime.exec_command({"cmd": "dotnet", "argv": ["dotnet", "build"]})
                self.assertEqual(context.exception.code, "WINDOWS_SANDBOX_FEATURE_DISABLED")
                self.assertEqual(context.exception.details["execution_backend"], "isolated")
                native.assert_not_called()
                spawn.assert_not_called()
            finally:
                runtime.close()

    def test_explicit_native_project_build_writes_artifact_and_keeps_durable_receipt(self):
        with tempfile.TemporaryDirectory(prefix="native-approved-build-", dir=str(Path(__file__).resolve().anchor)) as directory:
            root = Path(directory)
            script = root / "trusted-build.js"
            script.write_text("require('node:fs').writeFileSync('artifact.txt','TRUSTED_BUILD_OK'); console.log('TRUSTED_BUILD_OK');\n", encoding="utf-8")
            runtime = Runtime(root)
            runtime.request_context.hub_client = {"client_id": "electron-control-plane-exec-bridge", "client_type": "electron", "attestation_verified": True}
            try:
                args = {"cmd": "node", "argv": ["node", "trusted-build.js"], "_windows_execution_mode": "native_only", "yield_time_ms": 30_000, "verbosity": "full"}
                with patch("coding_tools_mcp.exec_tools.spawn_process") as spawn:
                    with self.assertRaises(ToolFailure) as context:
                        runtime.exec_command(args)
                self.assertEqual(context.exception.code, "NATIVE_EXECUTION_NOT_APPROVED")
                spawn.assert_not_called()
                self.assertFalse((root / "artifact.txt").exists())
                with patch("coding_tools_mcp.exec_tools.build_mxc_windows_sandbox_invocation") as isolated:
                    result = runtime.exec_command({**args, "_windows_native_argv_prefixes": [["node", "trusted-build.js"]]})
                    while result["status"] == "running":
                        result = runtime.command_control({"action": "poll", "command_id": result["command_id"], "yield_time_ms": 1000, "verbosity": "full"})
                    isolated.assert_not_called()
                self.assertEqual(result["exit_code"], 0, result)
                self.assertEqual(result["policy_decision"], "native_explicit_approval")
                self.assertEqual((root / "artifact.txt").read_text(encoding="utf-8"), "TRUSTED_BUILD_OK")
                durable = runtime.execution_resource_governor.find_exact_job(command_id=result["command_id"])
                self.assertEqual(durable["job_id"], result["execution_owner"]["job_id"])
                self.assertEqual(durable["lifecycle_state"], "exited")
                self.assertFalse(runtime.sessions)
            finally:
                runtime.close()


if __name__ == "__main__":
    unittest.main()
