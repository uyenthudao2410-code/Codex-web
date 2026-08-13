from __future__ import annotations

import http.client
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from coding_tools_mcp.protocol import STATELESS_PROTOCOL_VERSION
from coding_tools_mcp.server import MCPHandler, Runtime, RuntimeHTTPServer


PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def process_is_alive(process_id: int) -> bool:
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        process_query_limited_information = 0x1000
        still_active = 259
        kernel32 = ctypes.windll.kernel32
        open_process = kernel32.OpenProcess
        open_process.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        open_process.restype = wintypes.HANDLE
        get_exit_code = kernel32.GetExitCodeProcess
        get_exit_code.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        get_exit_code.restype = wintypes.BOOL
        close_handle = kernel32.CloseHandle
        close_handle.argtypes = [wintypes.HANDLE]
        close_handle.restype = wintypes.BOOL
        handle = open_process(
            process_query_limited_information, False, int(process_id)
        )
        if not handle:
            return False
        exit_code = wintypes.DWORD()
        try:
            return bool(get_exit_code(handle, ctypes.byref(exit_code)) and exit_code.value == still_active)
        finally:
            close_handle(handle)
    try:
        os.kill(int(process_id), 0)
    except OSError:
        return False
    return True


def modern_params(extra: dict | None = None) -> dict:
    payload = dict(extra or {})
    payload["_meta"] = {
        "io.modelcontextprotocol/protocolVersion": STATELESS_PROTOCOL_VERSION,
        "io.modelcontextprotocol/clientCapabilities": {},
        "io.modelcontextprotocol/clientInfo": {"name": "fault-canary", "version": "1"},
    }
    return payload


class StatelessReconnectFaultInjectionTests(unittest.TestCase):
    def test_new_http_connection_recovers_durable_task_without_transport_session(self) -> None:
        with tempfile.TemporaryDirectory() as temp, patch.dict(
            os.environ,
            {
                "CODING_TOOLS_MCP_TOOL_MODE": "smart",
                "CODING_TOOLS_MCP_STATELESS_HTTP_2026": "1",
            },
        ):
            runtime = Runtime(Path(temp), transport="http")
            server = RuntimeHTTPServer(
                ("127.0.0.1", 0), MCPHandler, runtime, runtime_factory=None
            )
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            port = int(server.server_address[1])

            def call_task_control(arguments: dict, request_id: int) -> tuple[int, dict[str, str], dict]:
                body = json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "method": "tools/call",
                        "params": modern_params(
                            {"name": "task_control", "arguments": arguments}
                        ),
                    }
                ).encode("utf-8")
                connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
                try:
                    connection.request(
                        "POST",
                        "/mcp",
                        body=body,
                        headers={
                            "Content-Type": "application/json",
                            "MCP-Protocol-Version": STATELESS_PROTOCOL_VERSION,
                            "Mcp-Method": "tools/call",
                            "Mcp-Name": "task_control",
                        },
                    )
                    response = connection.getresponse()
                    raw = response.read()
                    decoded = json.loads(raw.decode("utf-8")) if raw else {}
                    return (
                        response.status,
                        {key.lower(): value for key, value in response.getheaders()},
                        decoded,
                    )
                finally:
                    connection.close()

            try:
                status, headers, started = call_task_control(
                    {"action": "start", "objective": "survive stateless reconnect"}, 1
                )
                self.assertEqual(status, 200)
                self.assertNotIn("mcp-session-id", headers)
                self.assertFalse(started["result"]["isError"])

                # The helper deliberately creates a fresh HTTP connection for every
                # request. No initialize call or MCP transport-session header is used.
                status, headers, restored = call_task_control({"action": "get"}, 2)
                self.assertEqual(status, 200)
                self.assertNotIn("mcp-session-id", headers)
                self.assertFalse(restored["result"]["isError"])
                structured = restored["result"].get("structuredContent") or {}
                self.assertEqual(structured["state"]["objective"], "survive stateless reconnect")
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)
                self.assertFalse(thread.is_alive())


class RuntimeRestartFaultInjectionTests(unittest.TestCase):
    def test_real_process_restart_marks_inflight_idempotency_outcome_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            child_code = """
from pathlib import Path
import sys
from coding_tools_mcp.server import Runtime

root = Path(sys.argv[1])
runtime = Runtime(root)
runtime.orchestration_ledger.claim_idempotency(
    idempotency_key="process-crash-op",
    operation="agent_workflow",
    request_hash="stable-hash",
    process_instance_id=runtime.process_instance_id,
)
print(runtime.process_instance_id)
"""
            env = dict(os.environ)
            existing = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = os.pathsep.join(
                part for part in (str(PACKAGE_ROOT), existing) if part
            )
            child = subprocess.run(
                [sys.executable, "-c", child_code, str(root)],
                cwd=str(PACKAGE_ROOT),
                env=env,
                capture_output=True,
                text=True,
                timeout=20,
                check=True,
            )
            child_process_id = child.stdout.strip().splitlines()[-1]
            self.assertTrue(child_process_id)

            restored = Runtime(root)
            try:
                self.assertNotEqual(restored.process_instance_id, child_process_id)
                record = restored.orchestration_ledger.get_idempotency("process-crash-op")
                self.assertIsNotNone(record)
                assert record is not None
                self.assertEqual(record["status"], "unknown")
                self.assertEqual(
                    record["summary"]["outcome_unknown_reason"],
                    "mcp_process_restarted",
                )
            finally:
                restored.close()

    def test_task_and_durable_event_cursor_survive_runtime_recreation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = Runtime(root)
            started = first.task_control(
                {"action": "start", "objective": "persist task and events"}
            )
            self.assertEqual(started["state"]["objective"], "persist task and events")
            run_id = first.orchestration_ledger.create_run(
                objective="event replay", task_id=started["state"]["task_id"]
            )
            wave_id = first.orchestration_ledger.create_wave(
                run_id, execution_mode="mcp_only"
            )
            for index in range(3):
                first.orchestration_ledger.append_event(
                    run_id,
                    wave_id=wave_id,
                    event_type=f"restart-event-{index}",
                )
            first.close()

            restored = Runtime(root)
            try:
                state = restored.task_control({"action": "get"})["state"]
                self.assertEqual(state["objective"], "persist task and events")
                page = restored.orchestration_ledger.list_events_since(
                    run_id, after_seq=0, limit=10
                )
                self.assertEqual(
                    [item["event_type"] for item in page["events"]],
                    ["restart-event-0", "restart-event-1", "restart-event-2"],
                )
                self.assertFalse(page["has_more"])
            finally:
                restored.close()


class CommandCancellationFaultInjectionTests(unittest.TestCase):
    def test_cancelled_command_has_no_live_child_process(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            probe = root / "sleep_probe.py"
            child_pid_file = root / "child.pid"
            probe.write_text(
                "import os\n"
                "from pathlib import Path\n"
                "import time\n"
                "Path('child.pid').write_text(str(os.getpid()), encoding='ascii')\n"
                "time.sleep(30)\n",
                encoding="utf-8",
            )
            runtime = Runtime(root)
            child_process_id: int | None = None
            try:
                command = runtime.exec_command(
                    {
                        "cmd": f'"{sys.executable}" sleep_probe.py',
                        "yield_time_ms": 0,
                        "max_output_bytes": 4096,
                        "verbosity": "full",
                    }
                )
                self.assertEqual(command["status"], "running")
                command_id = command["command_id"]
                deadline = time.monotonic() + 3
                while not child_pid_file.exists() and time.monotonic() < deadline:
                    time.sleep(0.05)
                self.assertTrue(child_pid_file.exists(), "child process did not publish its PID")
                child_process_id = int(child_pid_file.read_text(encoding="ascii"))
                self.assertTrue(process_is_alive(child_process_id))
                killed = runtime.command_control(
                    {
                        "action": "kill",
                        "command_id": command_id,
                        "wait_ms": 3000,
                        "verbosity": "full",
                    }
                )
                self.assertIn(
                    killed["status"],
                    {"terminated", "killed", "exited", "terminating"},
                )
                session = runtime._get_output_session(command_id)
                session.refresh_status()
                self.assertIsNotNone(session.process.poll())
                deadline = time.monotonic() + 3
                while process_is_alive(child_process_id) and time.monotonic() < deadline:
                    time.sleep(0.05)
                self.assertFalse(process_is_alive(child_process_id))
            finally:
                runtime.close()
                if child_process_id and process_is_alive(child_process_id):
                    if os.name == "nt":
                        subprocess.run(
                            ["taskkill.exe", "/PID", str(child_process_id), "/T", "/F"],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            check=False,
                        )
                    else:
                        os.kill(child_process_id, 9)


if __name__ == "__main__":
    unittest.main()
