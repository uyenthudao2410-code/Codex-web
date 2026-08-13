from __future__ import annotations

import http.client
import json
import os
import socket
import socketserver
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

PACKAGE_PARENT = str(Path(__file__).resolve().parents[1])


def _rpc(port: int, method: str, params: dict, *, timeout: float = 15.0) -> tuple[int, dict]:
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode("utf-8")
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=timeout)
    try:
        connection.request(
            "POST", "/mcp", body=body,
            headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"},
        )
        response = connection.getresponse()
        raw = response.read()
        return response.status, json.loads(raw.decode("utf-8")) if raw else {}
    finally:
        connection.close()


def _initialize(port: int) -> None:
    status, _body = _rpc(
        port, "initialize",
        {"protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "live-client", "version": "1"}},
    )
    assert status == 200


def _health(port: int) -> bool:
    connection = None
    try:
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
        connection.request("GET", "/__control/health")
        response = connection.getresponse()
        response.read()
        return response.status == 200
    except OSError:
        return False
    finally:
        if connection is not None:
            connection.close()


def _spawn_mcp(workspace: Path, port: int, extra_env: dict[str, str] | None = None) -> subprocess.Popen:
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["CODING_TOOLS_MCP_TOOL_MODE"] = "smart"
    env.update(extra_env or {})
    return subprocess.Popen(
        [sys.executable, "-m", "coding_tools_mcp", "--port", str(port), "--workspace", str(workspace)],
        cwd=PACKAGE_PARENT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


def _wait_ready(port: int, process: subprocess.Popen, timeout: float = 30.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            stderr = b""
            try:
                stderr = process.stderr.read() or b""
            except Exception:
                pass
            raise AssertionError(f"MCP exited during startup: {stderr.decode('utf-8', errors='replace')[:2000]}")
        if _health(port):
            return
        time.sleep(0.1)
    raise AssertionError("MCP did not become healthy in time")


class _TcpProxyHandler(socketserver.BaseRequestHandler):
    def handle(self) -> None:
        server = self.server
        upstream = socket.create_connection(("127.0.0.1", server.target_port), timeout=10)
        upstream.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        try:
            server._tracked.append(upstream)
            server._tracked.append(self.request)
            stop = threading.Event()

            def pump(source: socket.socket, target: socket.socket) -> None:
                try:
                    while not stop.is_set():
                        data = source.recv(65536)
                        if not data:
                            break
                        target.sendall(data)
                except OSError:
                    pass
                finally:
                    try:
                        target.shutdown(socket.SHUT_WR)
                    except OSError:
                        pass

            threads = [
                threading.Thread(target=pump, args=(self.request, upstream), daemon=True),
                threading.Thread(target=pump, args=(upstream, self.request), daemon=True),
            ]
            for thread in threads:
                thread.start()
            for thread in threads:
                while thread.is_alive():
                    thread.join(timeout=0.2)
                    if stop.is_set():
                        break
        finally:
            try:
                upstream.close()
            except OSError:
                pass


class _TcpProxy(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, target_port: int, listen_port: int = 0) -> None:
        self.target_port = target_port
        self._tracked: list[socket.socket] = []
        self._stop = threading.Event()
        super().__init__(("127.0.0.1", listen_port), _TcpProxyHandler)

    def stop(self) -> None:
        self._stop.set()
        for sock in list(self._tracked):
            try:
                sock.close()
            except OSError:
                pass
        self.shutdown()
        self.server_close()

    @property
    def listen_port(self) -> int:
        return int(self.server_address[1])


class LiveBrowserDisconnectReconnectTests(unittest.TestCase):
    def test_client_drop_mid_task_does_not_kill_durable_work_and_reconnect_replays(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "step.txt").write_text("before\n", encoding="utf-8")
            (root / "sleep_step.py").write_text("import time\ntime.sleep(4)\n", encoding="utf-8")
            port = 19111
            process = _spawn_mcp(
                root, port,
                {"CODING_TOOLS_MCP_LONG_TOOL_HANDOFF_SECONDS": "2"},
            )
            try:
                _wait_ready(port, process)
                _initialize(port)

                status, body = _rpc(port, "tools/call", {
                    "name": "agent_workflow",
                    "arguments": {
                        "phase": "execute",
                        "workflow": "custom",
                        "objective": "E2E durable workflow",
                        "commands": [
                            'echo step-one >> step.txt',
                            f'"{sys.executable}" sleep_step.py',
                            'echo step-two >> step.txt',
                        ],
                    },
                }, timeout=30.0)
                self.assertEqual(status, 200)
                structured = body.get("result", {}).get("structuredContent", {})
                background = structured.get("background_operation")
                operation_id = background.get("operation_id") if isinstance(background, dict) else None
                if operation_id:
                    status, body = _rpc(port, "tools/call", {
                        "name": "task_control",
                        "arguments": {"action": "operation", "operation_id": operation_id, "wait_ms": 15000},
                    }, timeout=20.0)
                    self.assertEqual(status, 200)
                    operation = body.get("result", {}).get("structuredContent", {})
                    snapshot = operation.get("background_operation") if isinstance(operation.get("background_operation"), dict) else {}
                    if "result" in snapshot and snapshot.get("status") != "completed":
                        snapshot_status = str(snapshot.get("status", ""))
                    else:
                        snapshot_status = "completed" if snapshot.get("result") else str(snapshot.get("status", ""))
                    self.assertEqual(snapshot_status, "completed", structured)
                else:
                    execution = structured.get("execution") or {}
                    self.assertTrue(execution.get("ok"), structured)

                status, body = _rpc(port, "tools/call", {
                    "name": "task_control",
                    "arguments": {"action": "events", "after_seq": 0, "limit": 20},
                })
                self.assertEqual(status, 200)
                events = body.get("result", {}).get("structuredContent", {})
                event_rows = events.get("events", [])
                self.assertTrue(any(item.get("event_type") == "run_started" for item in event_rows))

                status, body = _rpc(port, "tools/call", {
                    "name": "task_control",
                    "arguments": {"action": "get"},
                })
                state = body.get("result", {}).get("structuredContent", {}).get("state", {})
                self.assertEqual(state.get("objective"), "E2E durable workflow")
                self.assertIn("step-one", (root / "step.txt").read_text(encoding="utf-8"))
                self.assertIn("step-two", (root / "step.txt").read_text(encoding="utf-8"))
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait(timeout=10)


class LiveTunnelFailureTests(unittest.TestCase):
    def test_tunnel_death_mid_call_does_not_kill_mcp_or_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "sleep_probe.py").write_text(
                "import time\ntime.sleep(30)\n", encoding="utf-8"
            )
            port = 19112
            process = _spawn_mcp(root, port)
            proxy: _TcpProxy | None = None
            try:
                _wait_ready(port, process)
                proxy = _TcpProxy(port)
                proxy_thread = threading.Thread(target=proxy.serve_forever, daemon=True)
                proxy_thread.start()
                _initialize(proxy.listen_port)

                status, body = _rpc(proxy.listen_port, "tools/call", {
                    "name": "exec_command",
                    "arguments": {
                        "cmd": f'"{sys.executable}" sleep_probe.py',
                        "yield_time_ms": 0,
                        "max_output_bytes": 4096,
                        "verbosity": "full",
                    },
                })
                self.assertEqual(status, 200)
                structured = body.get("result", {}).get("structuredContent", {})
                self.assertEqual(structured.get("status"), "running")
                command_id = structured.get("command_id")
                pid_before = process.pid

                proxy.stop()
                proxy = None

                self.assertTrue(_health(port), "MCP must stay healthy after tunnel death")
                self.assertEqual(process.pid, pid_before)

                new_proxy = _TcpProxy(port)
                proxy_thread = threading.Thread(target=new_proxy.serve_forever, daemon=True)
                proxy_thread.start()
                try:
                    _initialize(new_proxy.listen_port)
                    status, body = _rpc(new_proxy.listen_port, "tools/call", {
                        "name": "command_control",
                        "arguments": {
                            "action": "poll",
                            "command_id": command_id,
                            "yield_time_ms": 0,
                            "max_output_bytes": 4096,
                            "verbosity": "full",
                        },
                    })
                    self.assertEqual(status, 200)
                    polled = body.get("result", {}).get("structuredContent", {})
                    self.assertIn(polled.get("status"), {"running", "exited"})
                finally:
                    new_proxy.stop()
            finally:
                if proxy is not None:
                    proxy.stop()
                if process.poll() is None:
                    process.kill()
                    process.wait(timeout=10)


if __name__ == "__main__":
    unittest.main()
