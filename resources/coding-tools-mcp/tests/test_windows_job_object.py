from __future__ import annotations

import os
import signal
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from coding_tools_mcp import processes
from coding_tools_mcp.errors import ToolFailure

from coding_tools_mcp.processes import (
    spawn_process,
    terminate_process_group,
    windows_job_object_enabled,
    WindowsJobLimits,
    attach_managed_process,
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

    def test_native_limits_are_installed_on_the_windows_job(self) -> None:
        import ctypes
        from ctypes import wintypes

        limits = WindowsJobLimits(memory_bytes=512 * 1024 * 1024, active_processes=8, cpu_rate_percent=25, cpu_time_ms=30_000)
        process, _ = spawn_process(
            ["ping", "-n", "8", "127.0.0.1"], cwd=tempfile.gettempdir(), shell=False,
            env={"SYSTEMROOT": os.environ.get("SYSTEMROOT", r"C:\Windows"), "PATH": os.environ.get("PATH", "")},
            tty=False, popen_kwargs={"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)}, windows_job_limits=limits,
        )
        try:
            query = processes._kernel32.QueryInformationJobObject
            query.argtypes = [wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID, wintypes.DWORD, wintypes.LPVOID]
            query.restype = wintypes.BOOL
            info = processes._JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
            cpu = processes._JOBOBJECT_CPU_RATE_CONTROL_INFORMATION()
            handle = getattr(process, "_coding_tools_job_handle")
            self.assertTrue(query(handle, 9, ctypes.byref(info), ctypes.sizeof(info), None))
            self.assertTrue(query(handle, 15, ctypes.byref(cpu), ctypes.sizeof(cpu), None))
            self.assertEqual(info.JobMemoryLimit, limits.memory_bytes)
            self.assertEqual(info.BasicLimitInformation.ActiveProcessLimit, limits.active_processes)
            self.assertEqual(info.BasicLimitInformation.PerJobUserTimeLimit, limits.cpu_time_ms * 10_000)
            self.assertEqual(cpu.CpuRate, limits.cpu_rate_percent * 100)
            self.assertEqual(cpu.ControlFlags, 0x1 | 0x4)
        finally:
            terminate_process_group(process, signal.SIGTERM)

    def test_required_job_attachment_failure_does_not_resume_native_child(self) -> None:
        from unittest.mock import Mock

        process = Mock(_coding_tools_job_handle=None, _coding_tools_created_suspended=True)
        with patch("coding_tools_mcp.processes._attach_windows_job", return_value=False), patch.object(processes._ntdll, "NtResumeProcess") as resume:
            with self.assertRaises(ToolFailure) as context:
                attach_managed_process(process, limits=WindowsJobLimits())
        self.assertEqual(context.exception.code, "NATIVE_RESOURCE_LIMITS_UNAVAILABLE")
        resume.assert_not_called()
        process.kill.assert_called_once()


if __name__ == "__main__":
    unittest.main()
