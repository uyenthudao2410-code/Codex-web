"""Exec node policy, allowlist, workspace lock and bounded runner."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from control_plane.node_agent import (
    _exec_allowlist_match,
    _exec_argv_item,
    _normalise_exec_policy,
    _run_bounded_exec,
)

FACADE = {"schema_version": 14, "profile": "control-plane-oauth-bounded-exec-v1", "sha256": "f" * 64}


def _policy(**overrides):
    base = {
        "schema_version": 1, "enabled": True, "server_origin": "https://control.example.test",
        "owner_id": "owner-default", "device_id": "device-exec-0001", "endpoint_id": "endpoint-exec-0001",
        "workspace_id": "workspace-exec-0001", "workspace_generation": "generation-exec-0001",
        "expires_at_ms": 1_800_000_000_000, "facade_contract": dict(FACADE),
        "allowed_argv_prefixes": [["python", "-m", "pytest"], ["npm", "test"]],
        "max_timeout_ms": 60000, "max_output_bytes": 32768, "max_concurrent": 2,
    }
    base.update(overrides)
    return base


class ExecPolicyTests(unittest.TestCase):
    def test_allowlist_prefix_match(self) -> None:
        prefixes = [["python", "-m", "pytest"], ["npm", "test"]]
        self.assertTrue(_exec_allowlist_match(["python", "-m", "pytest", "-q"], prefixes))
        self.assertTrue(_exec_allowlist_match(["npm", "test"], prefixes))
        self.assertFalse(_exec_allowlist_match(["python", "-m", "pip", "install", "x"], prefixes))
        self.assertFalse(_exec_allowlist_match(["rm", "-rf", "/"], prefixes))

    def test_shell_tokens_rejected_in_policy_items(self) -> None:
        with self.assertRaises(RuntimeError):
            _exec_argv_item("a;rm -rf /")
        with self.assertRaises(RuntimeError):
            _exec_argv_item("$(whoami)")

    def test_policy_caps_are_enforced_by_shape(self) -> None:
        ok = _normalise_exec_policy(_policy(), now_ms=1_700_000_000_000, require_enabled=True)
        self.assertEqual(ok["max_concurrent"], 2)
        with self.assertRaises(RuntimeError):
            _normalise_exec_policy(_policy(max_timeout_ms=10_000_000), now_ms=1_700_000_000_000)
        with self.assertRaises(RuntimeError):
            _normalise_exec_policy(_policy(enabled=False), now_ms=1_700_000_000_000, require_enabled=True)
        with self.assertRaises(RuntimeError):
            _normalise_exec_policy(_policy(expires_at_ms=1_600_000_000_000), now_ms=1_700_000_000_000)


class BoundedRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="exec-runner-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_success_and_output_caps(self) -> None:
        result, error = _run_bounded_exec(
            argv=["python3", "-c", "print('hello-exec')"], cwd_path=self.root,
            timeout_ms=10000, max_output_bytes=32768)
        self.assertIsNone(error)
        assert result is not None
        self.assertEqual(result["exit_code"], 0)
        self.assertIn("hello-exec", result["stdout"])

    def test_timeout_reports_typed_uncertainty_or_timeout(self) -> None:
        result, error = _run_bounded_exec(
            argv=["python3", "-c", "import time; time.sleep(30)"], cwd_path=self.root,
            timeout_ms=5000, max_output_bytes=32768)
        # Either a timed-out result or a typed cleanup-uncertain error; never silent.
        self.assertTrue((result is not None and result.get("timed_out")) or error is not None)

    def test_verified_stop_kills_tree(self) -> None:
        calls = {"n": 0}

        def _stop_check() -> bool:
            calls["n"] += 1
            return calls["n"] >= 3

        result, error = _run_bounded_exec(
            argv=["python3", "-c", "import time; time.sleep(30)"], cwd_path=self.root,
            timeout_ms=60000, max_output_bytes=32768, stop_check=_stop_check)
        self.assertIsNone(error)
        assert result is not None
        self.assertTrue(result.get("stopped"))

    def test_shell_is_never_used(self) -> None:
        # If shell were used, echo would expand; with shell=False the literal runs.
        result, error = _run_bounded_exec(
            argv=["python3", "-c", "import sys; sys.stdout.write(';rm')"], cwd_path=self.root,
            timeout_ms=10000, max_output_bytes=32768)
        self.assertIsNone(error)
        assert result is not None
        self.assertIn(";rm", result["stdout"])


if __name__ == "__main__":
    unittest.main()
