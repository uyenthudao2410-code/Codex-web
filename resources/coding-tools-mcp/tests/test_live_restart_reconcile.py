from __future__ import annotations

import http.client
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

PACKAGE_PARENT = str(Path(__file__).resolve().parents[1])
IS_WINDOWS = os.name == "nt"


def _rpc(port: int, method: str, params: dict, *, session_header: str | None = None) -> tuple[int, dict[str, str], dict]:
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode("utf-8")
    headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    if session_header:
        headers["Mcp-Session-Id"] = session_header
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    try:
        connection.request("POST", "/mcp", body=body, headers=headers)
        response = connection.getresponse()
        raw = response.read()
        decoded = json.loads(raw.decode("utf-8")) if raw else {}
        response_headers = {key.lower(): value for key, value in response.getheaders()}
        return response.status, response_headers, decoded
    finally:
        connection.close()


def _health(port: int) -> bool:
    try:
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
        connection.request("GET", "/__control/health")
        response = connection.getresponse()
        response.read()
        return response.status == 200
    except OSError:
        return False
    finally:
        connection.close()


@unittest.skipUnless(sys.platform.startswith(("win", "linux", "darwin")), "live process harness")
class LiveRestartReconcileTests(unittest.TestCase):
    def _spawn_mcp(self, workspace: Path, port: int) -> subprocess.Popen:
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        env["CODING_TOOLS_MCP_TOOL_MODE"] = "smart"
        return subprocess.Popen(
            [sys.executable, "-m", "coding_tools_mcp", "--port", str(port), "--workspace", str(workspace)],
            cwd=PACKAGE_PARENT,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )

    def _wait_ready(self, port: int, process: subprocess.Popen, timeout: float = 30.0) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if process.poll() is not None:
                stderr = b""
                try:
                    stderr = process.stderr.read() or b""
                except Exception:
                    pass
                self.fail(f"MCP exited during startup with {process.returncode}: {stderr.decode('utf-8', errors='replace')[:2000]}")
            if _health(port):
                return
            time.sleep(0.1)
        self.fail("MCP did not become healthy in time")

    def _initialize(self, port: int) -> str:
        status, headers, _body = _rpc(
            port,
            "initialize",
            {"protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "live-e2e", "version": "1"}},
        )
        self.assertEqual(status, 200)
        session_id = headers.get("mcp-session-id")
        self.assertTrue(session_id)
        return str(session_id)

    def test_mcp_restart_mid_call_reconciles_durable_state_and_kills_tree(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            probe = root / "sleep_probe.py"
            child_pid_file = root / "child.pid"
            probe.write_text(
                "import os\n"
                "import time\n"
                "from pathlib import Path\n"
                "Path('child.pid.tmp').write_text(str(os.getpid()), encoding='ascii')\n"
                "os.replace('child.pid.tmp', 'child.pid')\n"
                "time.sleep(60)\n",
                encoding="utf-8",
            )
            port = 19087
            process_a = self._spawn_mcp(root, port)
            process_b: subprocess.Popen | None = None
            child_pid: int | None = None
            try:
                self._wait_ready(port, process_a)
                session_id = self._initialize(port)

                exec_args = {
                    "cmd": f'"{sys.executable}" sleep_probe.py',
                    "yield_time_ms": 0,
                    "max_output_bytes": 4096,
                    "verbosity": "full",
                    "idempotency_key": "live-e2e-exec-1",
                }
                status, _headers, body = _rpc(
                    port,
                    "tools/call",
                    {"name": "exec_command", "arguments": exec_args},
                    session_header=session_id,
                )
                self.assertEqual(status, 200)
                structured = body.get("result", {}).get("structuredContent", {})
                self.assertEqual(structured.get("status"), "running")
                command_id = structured.get("command_id")
                deadline = time.monotonic() + 10
                while child_pid is None and time.monotonic() < deadline:
                    if child_pid_file.exists():
                        raw_pid = child_pid_file.read_text(encoding="ascii").strip()
                        if raw_pid.isdecimal() and int(raw_pid) > 0:
                            child_pid = int(raw_pid)
                            break
                    time.sleep(0.05)
                self.assertIsNotNone(child_pid, "child process never published a parseable PID")

                process_a.kill()
                process_a.wait(timeout=10)

                if IS_WINDOWS:
                    deadline = time.monotonic() + 8
                    while self._pid_alive(child_pid) and time.monotonic() < deadline:
                        time.sleep(0.1)
                    self.assertFalse(
                        self._pid_alive(child_pid),
                        "command child survived the MCP crash despite kill-on-close Job Object",
                    )
                child_pid = None

                process_b = self._spawn_mcp(root, port)
                self._wait_ready(port, process_b)

                status, headers, body = _rpc(
                    port,
                    "tools/call",
                    {"name": "task_control", "arguments": {"action": "get"}},
                    session_header=session_id,
                )
                self.assertEqual(status, 200)
                rebound_session_id = headers.get("mcp-session-id")
                self.assertTrue(rebound_session_id)
                session_id = str(rebound_session_id)
                state = body.get("result", {}).get("structuredContent", {}).get("state", {})
                self.assertEqual(state.get("objective"), "Run a workspace command")

                status, _headers, body = _rpc(
                    port,
                    "tools/call",
                    {"name": "exec_command", "arguments": exec_args},
                    session_header=session_id,
                )
                self.assertEqual(status, 200)
                repeated = body.get("result", {}).get("structuredContent", {})
                self.assertTrue(repeated.get("deduplicated"))
                self.assertTrue(repeated.get("durable_idempotency"))

                status, _headers, body = _rpc(
                    port,
                    "tools/call",
                    {
                        "name": "command_control",
                        "arguments": {"action": "poll", "command_id": command_id, "yield_time_ms": 0},
                    },
                    session_header=session_id,
                )
                self.assertEqual(status, 200)
                polled = body.get("result", {}).get("structuredContent", {})
                if IS_WINDOWS:
                    # The Windows Job Object is owned by the killed MCP
                    # process and has kill-on-close semantics, so startup can
                    # prove that the exact process tree is gone and safely
                    # terminalize the durable row.
                    self.assertTrue(polled.get("ok"))
                    self.assertEqual(polled.get("status"), "reconciled_terminal")
                    self.assertTrue(polled.get("reconciled"))
                    self.assertEqual(polled.get("reconciled_sources"), ["managed_process_job"])
                    managed_job = polled.get("managed_job") or {}
                    self.assertTrue(managed_job.get("terminal"))
                    self.assertNotEqual(managed_job.get("result_status"), "succeeded")
                    completion_report = polled.get("completion_report") or {}
                    self.assertEqual(completion_report.get("accepted_or_not"), "COMMAND_FAILED")
                else:
                    # POSIX has no equivalent owner handle in this fixture.
                    # The child intentionally survives the MCP parent, so the
                    # replacement runtime must fail closed rather than adopt
                    # or terminalize a live process by PID alone.
                    self.assertFalse(polled.get("ok"))
                    self.assertIn(
                        (polled.get("error") or {}).get("code"),
                        {"COMMAND_NOT_FOUND", "COMMAND_COMPLETION_CONFLICT"},
                    )
            finally:
                if process_b is not None and process_b.poll() is None:
                    process_b.kill()
                    process_b.wait(timeout=10)
                if process_a.poll() is None:
                    process_a.kill()
                    process_a.wait(timeout=10)
                if child_pid is not None and self._pid_alive(child_pid):
                    if IS_WINDOWS:
                        subprocess.run(
                            ["taskkill.exe", "/PID", str(child_pid), "/T", "/F"],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            check=False,
                        )

    @staticmethod
    def _pid_alive(pid: int) -> bool:
        if IS_WINDOWS:
            result = subprocess.run(
                ["tasklist.exe", "/FI", f"PID eq {pid}", "/NH"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            return str(pid).encode() in result.stdout
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False


if __name__ == "__main__":
    unittest.main()
