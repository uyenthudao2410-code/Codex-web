"""Cluster 4a — pipe-interactive sessions: ``exec_command`` ``stdin_open``.

Live smoke r20 (docs/research/261024_W7_COMPLETION.md §7 item 4) proved
``input_id`` dedupe could not be demonstrated on the packaged Windows build
through the public wire: every non-TTY session had its stdin closed in the
``finally`` right after spawn (``exec_tools.py``), and ``tty=true`` returns
``TTY_UNSUPPORTED`` (no ConPTY in the build), so no wire-reachable session
ever had a live stdin for ``command_control`` write / ``write_stdin`` to
feed — both writes landed on ``COMMAND_CLOSED``.

Cluster 4a adds ONE opt-in to ``exec_command``: ``stdin_open=true`` keeps a
non-TTY session's stdin pipe open after spawn (and after any initial
``stdin`` payload). Everything downstream is reused unchanged:

- ``processes.ManagedProcess.write_input`` already writes through the
  anonymous pipe whenever stdin is open and the process is alive;
- ``session_control.write_stdin`` is NOT modified — its ``COMMAND_CLOSED``
  gate reads live state (``process.poll()`` / the write itself), so a
  pipe-interactive session passes the gate naturally, and the W5
  ``JobInputLedger`` receipts (delivered / duplicate / rejected) apply;
- the session stays bounded by ``timeout_ms`` + the session watchdog and
  ends on process exit or an explicit kill, like every other session.

Property name: ``stdin_open`` was chosen over ``interactive`` because it
names the exact effect (the stdin pipe stays open), sits next to the
existing ``stdin``/``tty`` properties, and does not promise terminal
semantics — a pipe-interactive session is NOT a real terminal (no
ConPTY/PTY, no prompt echo, no full-screen TUI). It only lets a
line-oriented process (cmd/PowerShell/python reading lines from a pipe)
keep receiving input.
"""

from __future__ import annotations

import sys
import tempfile
import time
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

from coding_tools_mcp.errors import JsonRpcError, ToolFailure
from coding_tools_mcp.job_input import OUTCOME_DELIVERED, OUTCOME_REJECTED
from coding_tools_mcp.server import Runtime
from coding_tools_mcp.tool_schema import input_schemas, validate_arguments

ECHO_LINES_SCRIPT = (
    "import sys\n"
    "for line in sys.stdin:\n"
    "    cmd = line.strip()\n"
    "    if cmd == 'quit':\n"
    "        break\n"
    "    if cmd:\n"
    "        print('GOT:' + cmd, flush=True)\n"
)


class _RecordingStdin:
    """Process stdin double: records writes; close() flips ``closed``."""

    def __init__(self) -> None:
        self.closed = False
        self.writes: list[bytes] = []

    def write(self, data: bytes) -> int:
        if self.closed:
            raise ValueError("I/O operation on closed file")
        self.writes.append(bytes(data))
        return len(data)

    def flush(self) -> None:
        pass

    def close(self) -> None:
        self.closed = True


class _FakeProcess:
    """Minimal Popen double for the spawn-seam unit tests.

    Only what ``exec_command``/``ExecSession`` touch on this path: ``stdin``
    (via ``write_input``/``close_stdin``), ``poll()``, and — because the
    governor's ``bind_process`` is patched out below — nothing else.
    """

    def __init__(self) -> None:
        self.stdin = _RecordingStdin()
        self.stdout = None
        self.stderr = None
        self.exited = False

    def poll(self):  # noqa: ANN202 - mirrors subprocess.Popen.poll
        return 0 if self.exited else None


class StdinOpenSchemaTests(unittest.TestCase):
    def test_schema_declares_optional_stdin_open_on_exec_command(self) -> None:
        schemas = input_schemas()
        schema = schemas["exec_command"]
        self.assertFalse(schema["additionalProperties"])
        self.assertNotIn("stdin_open", schema["required"])
        prop = schema["properties"]["stdin_open"]
        self.assertEqual(prop["type"], "boolean")
        self.assertIs(prop["default"], False)
        # The description must not over-promise: pipe, not a terminal.
        for snippet in ("NOT closed", "input_id", "not a real terminal", "tty=true"):
            self.assertIn(snippet, prop["description"])
        # The public smart-v3 surface is untouched: still no stdin_open on
        # the write paths themselves (it is a spawn-time opt-in only).
        self.assertNotIn("stdin_open", schemas["write_stdin"]["properties"])
        self.assertNotIn("stdin_open", schemas["command_control"]["properties"])

    def test_validate_arguments_accepts_and_rejects_stdin_open(self) -> None:
        validate_arguments("exec_command", {"cmd": "echo x", "stdin_open": True})
        validate_arguments("exec_command", {"cmd": "echo x", "stdin_open": False})
        validate_arguments("exec_command", {"cmd": "echo x"})
        for bad in (123, "yes"):
            with self.subTest(bad=bad):
                with self.assertRaises(JsonRpcError):
                    validate_arguments("exec_command", {"cmd": "echo x", "stdin_open": bad})
        with self.assertRaises(JsonRpcError):
            validate_arguments("exec_command", {"cmd": "echo x", "stdin_open": True, "bogus": 1})

    def test_stdin_open_cannot_be_combined_with_tty(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            try:
                with patch("coding_tools_mcp.exec_tools.spawn_process") as spawn:
                    with self.assertRaises(ToolFailure) as caught:
                        runtime.exec_command({"cmd": "echo x", "stdin_open": True, "tty": True})
                self.assertEqual(caught.exception.code, "INVALID_ARGUMENT")
                spawn.assert_not_called()
            finally:
                runtime.close()


class StdinOpenFakeSpawnTests(unittest.TestCase):
    """Unit seam: patch spawn_process with a fake process and assert the
    spawn-time finally keeps or closes stdin exactly per the opt-in."""

    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.runtime = Runtime(Path(self._temp.name))
        self._fakes: list[_FakeProcess] = []

    def tearDown(self) -> None:
        for fake in self._fakes:
            fake.exited = True
        self.runtime.close()
        self._temp.cleanup()

    def _exec_with_fake(self, args: dict[str, Any]) -> tuple[dict[str, Any], _FakeProcess]:
        fake = _FakeProcess()
        self._fakes.append(fake)
        with (
            patch("coding_tools_mcp.exec_tools.spawn_process", return_value=(fake, None)),
            patch("coding_tools_mcp.exec_tools.start_reader_threads", lambda session: None),
            patch("coding_tools_mcp.exec_tools.start_session_watchdog", lambda session: None),
            patch.object(self.runtime.execution_resource_governor, "bind_process", lambda *a, **k: None),
        ):
            result = self.runtime.exec_command({"cmd": "echo probe", "yield_time_ms": 0, **args})
        return result, fake

    def test_opt_in_keeps_stdin_open_after_spawn(self) -> None:
        result, fake = self._exec_with_fake({"stdin_open": True})
        self.assertEqual(result["status"], "running")
        self.assertIs(result["stdin_open"], True)
        session = self.runtime.sessions[result["session_id"]]
        self.assertTrue(session.stdin_open)
        self.assertTrue(session.stdin_is_open)
        self.assertFalse(fake.stdin.closed, "opt-in spawn must not close stdin")

    def test_opt_in_writes_initial_stdin_then_keeps_pipe_open(self) -> None:
        result, fake = self._exec_with_fake({"stdin_open": True, "stdin": "first\n"})
        self.assertEqual(fake.stdin.writes, [b"first\n"])
        self.assertFalse(fake.stdin.closed)
        self.assertIs(result["stdin_open"], True)

    def test_absent_opt_in_closes_stdin_after_spawn_like_legacy(self) -> None:
        result, fake = self._exec_with_fake({})
        self.assertEqual(result["status"], "running")
        self.assertIs(result["stdin_open"], False)
        session = self.runtime.sessions[result["session_id"]]
        self.assertFalse(session.stdin_open)
        self.assertFalse(session.stdin_is_open)
        self.assertTrue(fake.stdin.closed, "legacy spawn must close stdin in the finally")

    def test_explicit_false_closes_stdin_and_still_writes_initial_payload(self) -> None:
        result, fake = self._exec_with_fake({"stdin_open": False, "stdin": "only\n"})
        self.assertEqual(fake.stdin.writes, [b"only\n"])
        self.assertTrue(fake.stdin.closed)
        self.assertIs(result["stdin_open"], False)


class PipeInteractiveRealProcessTests(unittest.TestCase):
    """Platform-neutral integration: a real child process reading lines
    from its stdin pipe, driven through the real Runtime handlers."""

    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.root = Path(self._temp.name)
        (self.root / "echo_lines.py").write_text(ECHO_LINES_SCRIPT, encoding="utf-8")
        self.runtime = Runtime(self.root)
        self.cmd = f'"{sys.executable}" echo_lines.py'

    def tearDown(self) -> None:
        self.runtime.close()
        self._temp.cleanup()

    def _wait_exit(self, session: Any, timeout: float = 5.0) -> int | None:
        deadline = time.time() + timeout
        while time.time() < deadline:
            code = session.process.poll()
            if code is not None:
                return code
            time.sleep(0.02)
        return session.process.poll()

    def test_write_with_input_id_executes_exactly_once_via_both_write_paths(self) -> None:
        started = self.runtime.exec_command(
            {"cmd": self.cmd, "stdin_open": True, "yield_time_ms": 100, "timeout_ms": 30000, "verbosity": "full"}
        )
        self.assertEqual(started["status"], "running", started)
        self.assertIs(started["stdin_open"], True)
        session_id = started["session_id"]
        session = self.runtime.sessions[session_id]
        self.assertTrue(session.stdin_is_open)
        self.assertFalse(session.process.stdin.closed)

        # First write through the public facade (command_control write).
        first = self.runtime.command_control(
            {"action": "write", "command_id": session_id, "chars": "hello-4a\n",
             "input_id": "in-4a-1", "yield_time_ms": 2000, "verbosity": "full"}
        )
        receipt = first["input_receipt"]
        self.assertEqual(receipt["outcome"], OUTCOME_DELIVERED)
        self.assertFalse(receipt["duplicate"])
        self.assertEqual(receipt["session_id"], session_id)

        # Same (session, input_id) again: reconciles, never re-executes.
        second = self.runtime.command_control(
            {"action": "write", "command_id": session_id, "chars": "hello-4a\n",
             "input_id": "in-4a-1", "yield_time_ms": 200, "verbosity": "full"}
        )
        self.assertTrue(second["input_receipt"]["duplicate"])
        self.assertEqual(second["input_receipt"]["outcome"], OUTCOME_DELIVERED)

        # A second line through the internal write_stdin handler also works
        # (same ledger, same gate — session_control needed no change).
        third = self.runtime.write_stdin(
            {"session_id": session_id, "chars": "second-line\n",
             "input_id": "in-4a-2", "yield_time_ms": 2000}
        )
        self.assertEqual(third["input_receipt"]["outcome"], OUTCOME_DELIVERED)
        self.assertFalse(third["input_receipt"]["duplicate"])

        # The gate stays natural after the writes: session still open.
        self.assertIs(third["stdin_open"], True)
        self.assertTrue(session.stdin_is_open)

        # End the session explicitly through the process's own protocol.
        self.runtime.write_stdin({"session_id": session_id, "chars": "quit\n", "yield_time_ms": 2000})
        self.assertEqual(self._wait_exit(session), 0)
        session.refresh_status()
        retained = session.retained_output_bytes()
        self.assertEqual(retained.count(b"GOT:hello-4a"), 1, "input_id write must execute exactly once")
        self.assertEqual(retained.count(b"GOT:second-line"), 1)

    def test_plain_session_closes_stdin_and_later_write_is_command_closed(self) -> None:
        started = self.runtime.exec_command(
            {"cmd": self.cmd, "yield_time_ms": 100, "timeout_ms": 30000, "verbosity": "full"}
        )
        # The first snapshot races the child: on fast runners the line
        # reader already sees EOF and exits 0 inside the 100ms yield, so
        # the snapshot is 'exited' instead of 'running'. Both outcomes are
        # legitimate; anything else (timeout/terminated) still fails, and
        # an 'exited' snapshot must carry exit_code 0 — this does not pass
        # arbitrary states. (Gate run 40078678540 failed only on the old
        # assertEqual(status, 'running') line.)
        self.assertIn(started["status"], ("running", "exited"), started)
        if started["status"] == "exited":
            self.assertEqual(started["exit_code"], 0, started)
        self.assertIs(started["stdin_open"], False)
        session_id = started["session_id"]
        # A completed session is popped from sessions but remembered in
        # output_sessions, so look in both; the late-write gate below
        # resolves through the same fallback.
        session = self.runtime.sessions.get(session_id) or self.runtime.output_sessions.get(session_id)
        self.assertIsNotNone(session, started)
        # Legacy guarantee, checked at the spawn seam: stdin already closed.
        self.assertFalse(session.stdin_is_open)
        self.assertTrue(session.process.stdin.closed)

        # The line reader sees EOF and exits on its own; after that the
        # pre-existing COMMAND_CLOSED gate answers the write, exactly as
        # before cluster 4a (and as the r20 live smoke observed).
        self.assertEqual(self._wait_exit(session), 0)
        with self.assertRaises(ToolFailure) as caught:
            self.runtime.command_control(
                {"action": "write", "command_id": session_id, "chars": "too-late\n",
                 "input_id": "in-plain-1", "yield_time_ms": 100}
            )
        self.assertEqual(caught.exception.code, "COMMAND_CLOSED")
        stored = self.runtime.job_input_receipt(session_id, "in-plain-1")
        self.assertIsNotNone(stored)
        self.assertEqual(stored["outcome"], OUTCOME_REJECTED)
        self.assertEqual(stored["reason"], "COMMAND_CLOSED")
        self.assertNotIn(b"GOT:too-late", session.retained_output_bytes())

    def test_pipe_interactive_session_can_be_killed_explicitly(self) -> None:
        started = self.runtime.exec_command(
            {"cmd": self.cmd, "stdin_open": True, "yield_time_ms": 100, "timeout_ms": 30000, "verbosity": "full"}
        )
        session_id = started["session_id"]
        session = self.runtime.sessions[session_id]
        killed = self.runtime.command_control(
            {"action": "kill", "command_id": session_id, "wait_ms": 2000}
        )
        self.assertTrue(killed["killed"], killed)
        self.assertIsNotNone(self._wait_exit(session, timeout=2.0))


if __name__ == "__main__":
    unittest.main()
