from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from coding_tools_mcp import landlock_exec


class _ExecIntercept(RuntimeError):
    pass


class LandlockStructuredArgvTests(unittest.TestCase):
    def test_standalone_helper_resolves_package_imports_before_argument_validation(self) -> None:
        helper = Path(landlock_exec.__file__).resolve()
        result = subprocess.run(
            [sys.executable, str(helper)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 126)
        expected = "landlock_exec requires" if sys.platform == "linux" else "only supported on Linux"
        self.assertIn(expected, result.stderr)
        self.assertNotIn("attempted relative import", result.stderr)

    def test_argv_builder_uses_json_handoff_for_structured_command(self) -> None:
        argv = ["/usr/bin/python3", "-c", "print('literal&&not-a-shell-command')"]
        wrapped = landlock_exec.landlock_exec_argv(41, argv)

        self.assertEqual(wrapped[2:5], ["41", "--argv-json", json.dumps(argv, ensure_ascii=False, separators=(",", ":"))])

    def test_structured_mode_execs_original_argv_without_shell(self) -> None:
        argv = ["/usr/bin/python3", "-c", "print('literal&&not-a-shell-command')"]
        libc = MagicMock()
        libc.prctl.return_value = 0
        invoked: list[tuple[str, list[str]]] = []

        def intercept(program: str, args: list[str], _environment: object) -> None:
            invoked.append((program, args))
            raise _ExecIntercept()

        with (
            patch.object(landlock_exec.sys, "platform", "linux"),
            patch.object(landlock_exec, "landlock_libc", return_value=libc),
            patch.object(landlock_exec, "libc_syscall", return_value=0),
            patch.object(landlock_exec.os, "close"),
            patch.object(landlock_exec.os, "execvpe", side_effect=intercept),
        ):
            with self.assertRaises(_ExecIntercept):
                landlock_exec.main(["41", "--argv-json", json.dumps(argv)])

        self.assertEqual(invoked, [(argv[0], argv)])


if __name__ == "__main__":
    unittest.main()
