"""Offline tests for r4 additive fixture reuse evidence."""
import json
from pathlib import Path
import tempfile
import unittest

import importlib.util

SPEC = importlib.util.spec_from_file_location("r4_reuse", Path(__file__).with_name("prepare-r4-fixture-reuse.py"))
REUSE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REUSE)


class ReuseTests(unittest.TestCase):
    def test_current_original_fixture_is_read_only_reusable(self):
        manifest = Path(__file__).parents[1] / "fixture-preparation.json"
        harness = Path(__file__).with_name("run-native-first-canary.py")
        receipt = REUSE.verify(manifest, harness)
        self.assertEqual(receipt["mutations"], 0)
        self.assertEqual(receipt["fixture_file_count"], 101)
        self.assertTrue(receipt["build_artifact_absent"])

    def test_manifest_change_fails_without_touching_fixture(self):
        manifest = Path(__file__).parents[1] / "fixture-preparation.json"
        harness = Path(__file__).with_name("run-native-first-canary.py")
        with tempfile.TemporaryDirectory() as directory:
            changed = Path(directory) / "manifest.json"
            value = json.loads(manifest.read_text(encoding="utf-8"))
            value["files"][0]["size_bytes"] += 1
            changed.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "R4_FIXTURE_SEED_CHANGED"):
                REUSE.verify(changed, harness)


if __name__ == "__main__":
    unittest.main()
