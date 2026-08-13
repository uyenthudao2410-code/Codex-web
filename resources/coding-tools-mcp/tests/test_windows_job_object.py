from __future__ import annotations

import os
import signal
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from coding_tools_mcp.processes import (
    spawn_process,
    terminate_process_group,
    windows_job_object_enabled,
)


@unittest.skipUnless(os.name == "nt", "Windows-only Job Object ownership proof")
class WindowsJobObjectTests(unittest.TestCase):
    def _spawn_ping(self) -> subprocess.Popen[bytes]:
        process, _ = spawn_process(
            ["ping", "-n", "8", "127.0.0.1"],
            cwd=tempfile.gettempdir(),
            shell=False,
            env={"SYSTEMROOT": os.environ.get("SYSTEMROOT", r"C:\Windows"), "PATH": os.environ.get("PATH", "")},
            tty=False,
            popen_kwargs={
                "creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0),
            },
        )
        return process

    def test_spawned_command_is_attached_to_kill_on_close_job(self) -> None:
        process = self._spawn_ping()
        try:
            self.assertTrue(getattr(process, "_coding_tools_job_handle", None))
            self.assertIsNone(process.poll())
        finally:
            terminate_process_group(process, signal.SIGTERM)

    def test_job_close_kills_whole_tree(self) -> None:
        process = self._spawn_ping()
        try:
            terminate_process_group(process, signal.SIGTERM)
            process.wait(timeout=3)
            self.assertIsNotNone(process.poll())
            self.assertFalse(getattr(process, "_coding_tools_job_handle", None))
        finally:
            if process.poll() is None:
                process.kill()

    def test_job_object_can_be_disabled_via_env(self) -> None:
        with patch.dict(os.environ, {"CODING_TOOLS_MCP_WINDOWS_JOB_OBJECT": "0"}):
            self.assertFalse(windows_job_object_enabled())
            process = self._spawn_ping()
            try:
                self.assertFalse(getattr(process, "_coding_tools_job_handle", None))
            finally:
                terminate_process_group(process, signal.SIGTERM)


if __name__ == "__main__":
    unittest.main()
