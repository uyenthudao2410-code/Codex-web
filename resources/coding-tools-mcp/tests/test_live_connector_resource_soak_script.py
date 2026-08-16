from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_live_connector_resource_soak.py"
SPEC = importlib.util.spec_from_file_location("run_live_connector_resource_soak", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class LiveConnectorResourceSoakScriptTests(unittest.TestCase):
    def test_distribution_uses_nearest_rank_p95_and_integer_median(self) -> None:
        self.assertEqual(MODULE.distribution([]), {"count": 0})
        self.assertEqual(
            MODULE.distribution([10, 1, 9, 2, 8, 3, 7, 4, 6, 5]),
            {"count": 10, "min": 1, "median": 5, "p95": 10, "max": 10},
        )

    def test_live_inputs_require_path_free_artifacts_and_real_relative_rust_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "src").mkdir()
            (root / "src/lib.rs").write_text("pub fn stable_symbol() {}\n", encoding="utf-8")
            self.assertEqual(MODULE._relative_rust_file(root, "src/lib.rs"), "src/lib.rs")
            self.assertEqual(MODULE._bounded_label("connector-sha256:abc", name="artifact"), "connector-sha256:abc")
            with self.assertRaises(MODULE.LiveSoakBlocked):
                MODULE._relative_rust_file(root, "../outside.rs")
            with self.assertRaises(MODULE.LiveSoakBlocked):
                MODULE._bounded_label("C:/secret/connector.exe", name="artifact")
            with self.assertRaises(MODULE.LiveSoakBlocked):
                MODULE._bounded_label("webcodex_" + "a" * 64, name="artifact")

    def test_native_transport_failure_becomes_structured_live_blocker(self) -> None:
        class FailingProvider:
            def localize(self, **_kwargs):
                raise RuntimeError("provider details must not escape")

        with self.assertRaises(MODULE.LiveSoakBlocked) as raised:
            MODULE._native_call(
                FailingProvider(),
                repository=Path.cwd(),
                path="src/lib.rs",
                query="stable_symbol",
                resource_class="MEDIUM",
            )

        self.assertEqual(raised.exception.code, "LIVE_NATIVE_CALL_FAILED")
        self.assertNotIn("provider details", str(raised.exception))

    def test_workspace_warmup_retries_only_unhandled_results_within_deadline(self) -> None:
        unhandled = MODULE.LiveSoakBlocked("LIVE_QUERY_NOT_HANDLED", "not indexed yet")
        with mock.patch.object(
            MODULE,
            "_native_call",
            side_effect=[unhandled, unhandled, (1, [{"handled": True}])],
        ) as native_call:
            latency, rows = MODULE._native_call_until_handled(
                object(),
                repository=Path.cwd(),
                path=".",
                query="stable_symbol",
                resource_class="HEAVY",
                timeout_seconds=1,
                poll_seconds=0,
            )

        self.assertEqual(native_call.call_count, 3)
        self.assertGreaterEqual(latency, 0)
        self.assertEqual(rows, [{"handled": True}])


if __name__ == "__main__":
    unittest.main()
