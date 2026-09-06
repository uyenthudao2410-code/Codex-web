from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from coding_tools_mcp.command_parse import explicit_command_path_candidates, shlex_split
from coding_tools_mcp.errors import ToolFailure
from coding_tools_mcp.server import Runtime


class PytestSelectorPathTests(unittest.TestCase):
    def test_python_pytest_node_id_inspects_only_the_filesystem_prefix(self) -> None:
        for interpreter in ("python", "python3"):
            for selector in (
                "tests/test_sample.py::test_one",
                "tests/test_sample.py::TestSample::test_one",
                "tests/test_sample.py::test_one[param/with:punctuation]",
            ):
                with self.subTest(interpreter=interpreter, selector=selector):
                    self.assertEqual(
                        explicit_command_path_candidates(shlex_split(f'{interpreter} -B -m pytest "{selector}" -q')),
                        ["tests/test_sample.py"],
                    )

    def test_pytest_module_context_is_not_inferred_from_other_command_arguments(self) -> None:
        for command, expected in (
            ("python script.py::literal -m pytest", ["script.py::literal"]),
            ("python -m unittest tests/test_sample.py::literal", ["tests/test_sample.py::literal"]),
            ("python -m unittest -m pytest tests/test_sample.py::literal", ["tests/test_sample.py::literal"]),
            ("python -- -m pytest tests/test_sample.py::literal", ["tests/test_sample.py::literal"]),
            ("python -m pytest -m unittest tests/test_sample.py::test_one", ["tests/test_sample.py::test_one"]),
            ("python -m pytest -q -vv tests/test_sample.py::test_one", ["tests/test_sample.py"]),
            ('python -m pytest --basetemp "tests.py::/../../outside"', ["tests.py::/../../outside"]),
            ('python -m pytest --rootdir "tests.py::/../../outside"', ["tests.py::/../../outside"]),
            ('python -m pytest --junitxml "tests.py::/../../outside.xml"', ["tests.py::/../../outside.xml"]),
            ('python -m pytest --plugin-option -q "tests.py::/../../outside"', ["tests.py::/../../outside"]),
            ('python -m pytest "@tests.py::/../../outside"', ["@tests.py::/../../outside"]),
            ('python -X -m pytest "tests.py::/../../outside.py"', ["tests.py::/../../outside.py"]),
            ('python -W -m pytest "tests.py::/../../outside.py"', ["tests.py::/../../outside.py"]),
            ('python -X -m pytest -m pytest "tests.py::/../../outside.py"', ["tests.py::/../../outside.py"]),
            ('python -W -m pytest -m pytest "tests.py::/../../outside.py"', ["tests.py::/../../outside.py"]),
            ('python "-cprint(1)" -m pytest "tests.py::/../../outside.py"', ["tests.py::/../../outside.py"]),
            ('python -munittest -m pytest "tests.py::/../../outside.py"', ["tests.py::/../../outside.py"]),
            ('python -Bm unittest -m pytest "tests.py::/../../outside.py"', []),
            ('python -W "tests.py::/../../outside.py" -m pytest tests/test_sample.py', ["tests.py::/../../outside.py"]),
            ('python -X "tests.py::/../../outside.py" -m pytest tests/test_sample.py', ["tests.py::/../../outside.py"]),
            ('python -X "pycache_prefix=tests.py::/../../outside.py" -m pytest tests/test_sample.py',
             ["pycache_prefix=tests.py::/../../outside.py"]),
            ('python --check-hash-based-pycs -m pytest -m pytest "tests.py::/../../outside.py"',
             ["tests.py::/../../outside.py"]),
            ("python -W -X -m pytest tests/test_sample.py::test_one", ["tests/test_sample.py"]),
            ("python -X -- -m pytest tests/test_sample.py::test_one", ["tests/test_sample.py"]),
            ("node tests/test_sample.js::literal", ["tests/test_sample.js::literal"]),
            ("cat tests/test_sample.py::literal", ["tests/test_sample.py::literal"]),
            ("python -m pytest tests/test_sample.py", ["tests/test_sample.py"]),
        ):
            with self.subTest(command=command):
                self.assertEqual(explicit_command_path_candidates(shlex_split(command)), expected)

    def test_env_wrapper_and_redirection_preserve_separate_path_authority(self) -> None:
        self.assertEqual(
            explicit_command_path_candidates(shlex_split(
                'env PYTHONUTF8=1 python -m pytest "tests/test sample.py::test_one" > output.log'
            )),
            ["output.log", "tests/test sample.py"],
        )

    def test_selector_suffix_does_not_exempt_an_unsafe_filesystem_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = Runtime(Path(directory))
            try:
                for target in (
                    "../outside.py::test_one",
                    "tests/../../outside.py::TestSample::test_one",
                    "/outside.py::test_one",
                    "C:/outside.py::test_one",
                    "~/outside.py::test_one",
                ):
                    with self.subTest(target=target):
                        with self.assertRaises(ToolFailure) as failure:
                            runtime._check_command_paths(f'python -m pytest "{target}" -q')
                        self.assertEqual(failure.exception.code, "PERMISSION_REQUIRED")
                        self.assertEqual(failure.exception.details["permission"], "filesystem_escape")
                for command in (
                    'python -X -m pytest "tests.py::/../../outside.py"',
                    'python -W -m pytest "tests.py::/../../outside.py"',
                    'python -X -m pytest -m pytest "tests.py::/../../outside.py"',
                    'python -W -m pytest -m pytest "tests.py::/../../outside.py"',
                    'python -X "pycache_prefix=tests.py::/../../outside.py" -m pytest tests/test_sample.py',
                    'python -m pytest --basetemp "tests.py::/../../outside"',
                    'python -m pytest --rootdir "tests.py::/../../outside"',
                    'python -m pytest --junitxml "tests.py::/../../outside.xml"',
                    'python -m pytest "@tests.py::/../../outside"',
                ):
                    with self.subTest(command=command):
                        with self.assertRaises(ToolFailure) as failure:
                            runtime._check_command_paths(command)
                        self.assertEqual(failure.exception.details["permission"], "filesystem_escape")
            finally:
                runtime.close()

    def test_workspace_selector_cannot_follow_a_symlink_outside_the_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root = Path(directory)
            target = Path(outside) / "test_sample.py"
            target.write_text("def test_one(): pass\n", encoding="utf-8")
            try:
                (root / "test_sample.py").symlink_to(target)
            except OSError as exc:
                self.skipTest(f"Symlink creation unavailable: {exc.errno}")
            runtime = Runtime(root)
            try:
                with self.assertRaises(ToolFailure) as failure:
                    runtime._check_command_paths("python -m pytest test_sample.py::test_one -q")
                self.assertEqual(failure.exception.details["permission"], "filesystem_escape")
            finally:
                runtime.close()

    def test_existing_workspace_file_can_be_selected_without_treating_node_id_as_a_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "test_sample.py").write_text("def test_one(): pass\n", encoding="utf-8")
            runtime = Runtime(root)
            inspected = []
            resolve_existing = runtime.resolve_existing

            def inspect(path, *args, **kwargs):
                inspected.append(path)
                return resolve_existing(path, *args, **kwargs)

            runtime.resolve_existing = inspect
            try:
                runtime._check_command_paths("python -m pytest test_sample.py::test_one -q")
                self.assertEqual(inspected, ["test_sample.py"])
            finally:
                runtime.close()


if __name__ == "__main__":
    unittest.main()
