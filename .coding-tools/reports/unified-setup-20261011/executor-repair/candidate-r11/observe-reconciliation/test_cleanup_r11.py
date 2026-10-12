"""Offline cleanup guards; no remote transport or live state calls."""
import importlib.util
from pathlib import Path
import types
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("cleanup", HERE / "cleanup-r11.py")
cleanup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cleanup)


class CleanupTests(unittest.TestCase):
    def test_pinned_observer_loads_unchanged(self):
        observer = cleanup.load_observer()
        self.assertEqual(observer.ACTION, "act_a0b6b348fd944ea7b9e1eccf0b4c816f")

    def test_explicit_root_execute_required_before_live_observation(self):
        observer = cleanup.load_observer()
        with patch.object(cleanup, "load_observer", return_value=observer), patch.object(observer, "observed_state") as called:
            with self.assertRaises(observer.Failure) as error:
                cleanup.cleanup(False)
        self.assertEqual(error.exception.code, "ROOT_EXPLICIT_CLEANUP_REQUIRED")
        called.assert_not_called()

    def test_terminal_rejection_required_before_cleanup_intent_or_rpc(self):
        observer = cleanup.load_observer()
        canary = types.SimpleNamespace(_prior_marker_path=None)
        with patch.object(cleanup, "load_observer", return_value=observer), \
             patch.object(observer, "observed_state", return_value=(canary, None, None, None, None, {})):
            with self.assertRaises(observer.Failure) as error:
                cleanup.cleanup(True)
        self.assertEqual(error.exception.code, "EXACT_SETTLED_REJECTION_REQUIRED_NO_CLEANUP")


if __name__ == "__main__":
    unittest.main(verbosity=2)
