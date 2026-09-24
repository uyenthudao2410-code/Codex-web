from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import secrets
import subprocess
import tempfile
import threading
import time
import unittest
from pathlib import Path

from coding_tools_mcp.errors import ToolFailure
from coding_tools_mcp.windows_mxc_sandbox import (
    _executor_path,
    _probe_executor,
    _resolve_executable,
    _system_root,
    build_mxc_invocation,
    cleanup_mxc_invocation,
)


def _windows_process_alive(pid: int) -> bool:
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    handle = kernel32.OpenProcess(0x00100000, False, int(pid))  # SYNCHRONIZE only
    if not handle:
        return False
    try:
        return kernel32.WaitForSingleObject(handle, 0) == 0x00000102  # WAIT_TIMEOUT
    finally:
        kernel32.CloseHandle(handle)


class NpmCommandResolutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="mxc-npm-prefix-")
        self.addCleanup(self.temporary.cleanup)
        root = Path(self.temporary.name).resolve()
        self.workspace = root / "workspace"
        self.workdir = self.workspace / "packages" / "selected"
        self.toolchain = root / "toolchain"
        self.scratch = self.workspace / ".mxc-npm-prefix-scratch"
        self.workdir.mkdir(parents=True)
        self.scratch.mkdir(parents=True)
        npm_bin = self.toolchain / "node_modules" / "npm" / "bin"
        npm_bin.mkdir(parents=True)
        (self.toolchain / "node.exe").write_bytes(b"test fixture; never executed")
        (npm_bin / "npm-cli.js").write_text("// test fixture\n", encoding="utf-8")
        (npm_bin / "npx-cli.js").write_text("// test fixture\n", encoding="utf-8")

    def resolve(self, argv: list[str], *, scratch_directory: Path | None = None) -> list[str]:
        resolved, _roots = _resolve_executable(
            argv,
            workspace_root=self.workspace,
            workdir=self.workdir,
            scratch_directory=scratch_directory or self.scratch,
            roots=[self.toolchain],
            path_entries=[],
        )
        return resolved

    def test_npm_and_npx_bind_prefix_to_selected_workdir(self) -> None:
        for command, cli_name in (("npm", "npm-cli.js"), ("npx", "npx-cli.js")):
            with self.subTest(command=command):
                scratch = self.workspace / f".mxc-npm-prefix-{command}"
                scratch.mkdir()
                resolved = self.resolve([command, "test"], scratch_directory=scratch)
                cli_path = str((scratch / "npm" / "bin" / cli_name).resolve())
                cli_index = resolved.index(cli_path)
                self.assertEqual(
                    resolved[cli_index + 1:cli_index + 4],
                    ["--prefix", str(self.workdir.resolve()), "test"],
                )

    def test_explicit_off_scope_npm_prefix_fails_before_staging(self) -> None:
        outside = self.workspace / "other"
        outside.mkdir()
        with self.assertRaises(ToolFailure) as context:
            self.resolve(["npm", "--prefix", str(outside), "test"])
        self.assertEqual(context.exception.code, "SANDBOX_NPM_PREFIX_SCOPE_DENIED")
        self.assertFalse((self.scratch / "npm").exists())


@unittest.skipUnless(os.name == "nt", "Windows MXC ProcessContainer integration")
class WindowsMxcSandboxIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            _probe_executor(_executor_path(), _system_root())
        except Exception as error:  # noqa: BLE001 - unsupported hosts deny exec and skip the OS integration suite
            raise unittest.SkipTest(f"Windows BaseContainer is unavailable: {getattr(error, 'code', type(error).__name__)}")

    def invoke(
        self,
        workspace: Path,
        argv: list[str],
        *,
        timeout_ms: int = 15000,
        extra_environment: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        invocation = build_mxc_invocation(
            argv,
            workspace_root=workspace,
            workdir=workspace,
            timeout_ms=timeout_ms,
            extra_environment=extra_environment,
        )
        try:
            return subprocess.run(
                list(invocation.argv),
                cwd=workspace,
                env=invocation.environment,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=(timeout_ms / 1000) + 10,
                check=False,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        finally:
            self.assertTrue(cleanup_mxc_invocation(invocation))

    def temporary_workspace(self, prefix: str) -> tempfile.TemporaryDirectory[str]:
        try:
            return tempfile.TemporaryDirectory(prefix=prefix, dir=str(Path(__file__).resolve().anchor))
        except OSError as error:
            raise unittest.SkipTest(f"the test account cannot create an isolated workspace at the volume root: {error}")

    def test_workspace_write_sibling_deny_junction_deny_and_loopback_deny(self) -> None:
        with self.temporary_workspace("mxc-workspace-boundary-") as temporary:
            workspace = Path(temporary).resolve()
            sentinel_file = tempfile.NamedTemporaryFile(
                prefix="mxc-outside-sentinel-", suffix=".txt",
                dir=str(workspace.anchor), delete=False,
            )
            sentinel = Path(sentinel_file.name)
            sentinel_file.write(b"MXC_OUTSIDE_SENTINEL")
            sentinel_file.close()
            self.addCleanup(sentinel.unlink, missing_ok=True)

            allowed = self.invoke(workspace, [
                "node", "-e",
                "require('fs').writeFileSync(process.cwd()+'/inside.txt','MXC_INSIDE_OK');console.log('MXC_RUN_OK')",
            ])
            self.assertEqual(allowed.returncode, 0, allowed.stdout)
            self.assertEqual((workspace / "inside.txt").read_text(encoding="utf-8"), "MXC_INSIDE_OK")

            alias_sibling = "mxc-alias-parent-" + secrets.token_hex(6) + ".txt"
            alias_parent_write = self.invoke(workspace, [
                "node", "-e",
                "const fs=require('fs'),path=require('path');"
                f"const target=path.join(path.dirname(process.cwd()),{json.dumps(alias_sibling)});"
                "try{fs.writeFileSync(target,'MXC_ALIAS_PARENT_ESCAPE');console.log('ALIAS_PARENT_WRITE_ALLOWED')}"
                "catch(e){console.log('ALIAS_PARENT_WRITE_DENIED:'+e.code)}",
            ])
            self.assertEqual(alias_parent_write.returncode, 0, alias_parent_write.stdout)
            self.assertIn("ALIAS_PARENT_WRITE_DENIED:", alias_parent_write.stdout)
            self.assertNotIn("ALIAS_PARENT_WRITE_ALLOWED", alias_parent_write.stdout)

            outside_read = self.invoke(workspace, [
                "node", "-e",
                "try{process.stdout.write(require('fs').readFileSync(process.env.OUTSIDE_SENTINEL,'utf8'))}"
                "catch(e){if(!['EPERM','EACCES','ENOENT'].includes(e.code))process.exit(30);console.error('DENIED:'+e.code);process.exit(3)}",
            ], extra_environment={"OUTSIDE_SENTINEL": str(sentinel)})
            self.assertEqual(outside_read.returncode, 3)
            self.assertNotIn("MXC_OUTSIDE_SENTINEL", outside_read.stdout)
            self.assertRegex(outside_read.stdout, r"DENIED:(EPERM|ENOENT)")

            outside_write = self.invoke(workspace, [
                "node", "-e",
                "try{require('fs').writeFileSync(process.env.OUTSIDE_SENTINEL,'MXC_BAD_WRITE')}"
                "catch(e){if(!['EPERM','EACCES','ENOENT'].includes(e.code))process.exit(40);console.error('DENIED:'+e.code);process.exit(4)}",
            ], extra_environment={"OUTSIDE_SENTINEL": str(sentinel)})
            self.assertEqual(outside_write.returncode, 4)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "MXC_OUTSIDE_SENTINEL")

            junction = workspace / "escape"
            result = subprocess.run(
                ["cmd.exe", "/d", "/c", "mklink", "/J", str(junction), str(workspace.anchor)],
                capture_output=True, text=True, check=False,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if result.returncode == 0:
                try:
                    reparse_read = self.invoke(workspace, [
                        "node", "-e",
                        "try{process.stdout.write(require('fs').readFileSync(process.cwd()+'/escape/outside-sentinel.txt','utf8'))}"
                        "catch(e){console.error('DENIED:'+e.code);process.exit(5)}",
                    ])
                    self.assertEqual(reparse_read.returncode, 5)
                    self.assertNotIn("MXC_OUTSIDE_SENTINEL", reparse_read.stdout)
                    self.assertRegex(reparse_read.stdout, r"DENIED:(EPERM|ENOENT)")
                finally:
                    junction.rmdir()

            server_hits = 0

            class Handler(BaseHTTPRequestHandler):
                def do_GET(self) -> None:  # noqa: N802
                    nonlocal server_hits
                    server_hits += 1
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b"host-loopback-reached")

                def log_message(self, _format: str, *_args: object) -> None:
                    return

            server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                loopback = self.invoke(workspace, [
                    "node", "-e",
                    f"fetch('http://127.0.0.1:{server.server_port}/').then(r=>r.text()).then(t=>console.log('REACHED:'+t)).catch(e=>console.log('DENIED:'+((e.cause&&e.cause.code)||e.name)))",
                ])
                self.assertEqual(loopback.returncode, 0, loopback.stdout)
                self.assertIn("DENIED:", loopback.stdout)
                self.assertNotIn("REACHED:", loopback.stdout)
                self.assertEqual(server_hits, 0)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)
                sentinel.unlink(missing_ok=True)

    def test_npm_script_child_process_stays_inside_the_registered_workspace(self) -> None:
        with self.temporary_workspace("mxc-npm-workspace-") as temporary:
            workspace = Path(temporary).resolve()
            sentinel_file = tempfile.NamedTemporaryFile(
                prefix="mxc-npm-sentinel-", suffix=".txt",
                dir=str(workspace.anchor), delete=False,
            )
            sentinel = Path(sentinel_file.name)
            sentinel_file.write(b"MXC_NPM_OUTSIDE_SENTINEL")
            sentinel_file.close()
            self.addCleanup(sentinel.unlink, missing_ok=True)
            package = {
                "name": "mxc-workspace-test",
                "version": "1.0.0",
                "scripts": {
                    "test": (
                        "node -e \"try{require('fs').readFileSync(process.env.OUTSIDE_SENTINEL);process.exit(6)}"
                        "catch(e){if(!['EPERM','EACCES','ENOENT'].includes(e.code))process.exit(7);"
                        "require('fs').writeFileSync('npm-inside.txt','NPM_INSIDE_OK');"
                        "console.log('NPM_SANDBOX_OK')}\""
                    )
                }
            }
            (workspace / "package.json").write_text(json.dumps(package), encoding="utf-8")
            result = self.invoke(
                workspace, ["npm", "test"], timeout_ms=90_000,
                extra_environment={"OUTSIDE_SENTINEL": str(sentinel)},
            )
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn("NPM_SANDBOX_OK", result.stdout)
            self.assertEqual((workspace / "npm-inside.txt").read_text(encoding="utf-8"), "NPM_INSIDE_OK")
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "MXC_NPM_OUTSIDE_SENTINEL")
            sentinel.unlink(missing_ok=True)

    def test_node_child_can_launch_within_the_same_sandbox(self) -> None:
        with self.temporary_workspace("mxc-child-workspace-") as temporary:
            workspace = Path(temporary).resolve()
            code = (
                "const cp=require('child_process');"
                "const r=cp.spawnSync(process.execPath,['--preserve-symlinks','--preserve-symlinks-main','-e','console.log(\\\"MXC_CHILD_OK\\\")'],{encoding:'utf8'});"
                "console.log(JSON.stringify({error:r.error&&{code:r.error.code,path:r.error.path},status:r.status,stdout:r.stdout}))"
            )
            result = self.invoke(workspace, ["node", "-e", code])
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn('"status":0', result.stdout)
            self.assertIn("MXC_CHILD_OK", result.stdout)

    def test_wrapper_cancel_closes_wxc_job_and_child_process(self) -> None:
        with self.temporary_workspace("mxc-workspace-stop-") as temporary:
            workspace = Path(temporary).resolve()
            marker = "MXC_CANCEL_" + os.urandom(8).hex()
            invocation = build_mxc_invocation(
                ["node", "-e", f"console.log('MXC_PID:'+process.pid+':{marker}');setInterval(()=>{{}},1000)"],
                workspace_root=workspace,
                workdir=workspace,
                timeout_ms=60_000,
            )
            process = subprocess.Popen(
                list(invocation.argv),
                cwd=workspace,
                env=invocation.environment,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            child_pid = 0
            try:
                line = process.stdout.readline() if process.stdout else ""
                self.assertIn(marker, line)
                child_pid = int(line.split("MXC_PID:", 1)[1].split(":", 1)[0])
                self.assertTrue(_windows_process_alive(child_pid))
                process.kill()
                process.wait(timeout=5)
                deadline = time.time() + 5
                while _windows_process_alive(child_pid) and time.time() < deadline:
                    time.sleep(0.05)
                self.assertFalse(_windows_process_alive(child_pid), "sandbox child survived termination of wxc-exec")
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait(timeout=5)
                if process.stdout:
                    process.stdout.close()
                self.assertTrue(cleanup_mxc_invocation(invocation))


if __name__ == "__main__":
    unittest.main()
