from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from coding_tools_mcp.context_compiler import (
    CONTEXT_COMPILER_ENV,
    compile_context,
    context_compiler_treatment,
)
from coding_tools_mcp.server import Runtime


class ContextCompilerTests(unittest.TestCase):
    def test_budget_dedupe_scope_and_already_seen_are_fail_closed(self) -> None:
        evidence = {
            "files": [
                {"path": "src/a.py", "content": "A" * 80},
                {"path": "src/a.py", "content": "duplicate"},
                {"path": "src/b.py", "content": "B" * 80},
                {"path": "other/c.py", "content": "C" * 10},
            ],
            "searches": [{"matches": [{"path": "src/a.py"}, {"path": "src/b.py"}]}],
        }
        first = compile_context("change src", "rev-1", 25, evidence, [], ["src"])
        self.assertLessEqual(first["estimated_tokens"], first["token_budget"])
        self.assertEqual([item["path"] for item in first["primary_files"]], ["src/a.py"])
        reasons = {(item["id"], item["reason"]) for item in first["omitted_candidates"]}
        self.assertIn(("src/a.py", "duplicate"), reasons)
        self.assertIn(("src/b.py", "token_budget"), reasons)
        self.assertIn(("other/c.py", "out_of_scope"), reasons)

        seen = compile_context("change src", "rev-1", 100, evidence, ["src/a.py"], ["src"])
        self.assertEqual([item["path"] for item in seen["primary_files"]], ["src/b.py"])
        self.assertTrue(any(item["id"] == "src/a.py" and item["reason"] == "already_seen" for item in seen["omitted_candidates"]))

    def test_stale_semantics_rules_diff_config_and_uncertainty_are_explicit(self) -> None:
        evidence = {
            "files": [
                {"path": "src/app.py", "content": "def target():\n    return 1\n"},
                {"path": "package.json", "content": "{}"},
                {"path": "tests/test_app.py", "content": "target()\n"},
            ],
            "semantic_records": [
                {"symbol_id": "def", "path": "src/app.py", "symbol": "target", "kind": "definition", "current": True, "stale": False, "confidence": "high", "completeness": "complete"},
                {"symbol_id": "ref", "path": "tests/test_app.py", "symbol": "target", "kind": "reference", "current": True, "stale": False, "test_association": True, "confidence": "high", "completeness": "complete"},
                {"symbol_id": "stale", "path": "src/app.py", "symbol": "old", "kind": "reference", "current": False, "stale": True},
            ],
            "instructions": {"root": [{"path": "AGENTS.md", "content": "# Rules\nKeep scope bounded."}]},
            "dirty_diff": [{"path": "src/app.py", "diff": "-return 0\n+return 1\n"}],
            "semantic_graph": {"provider_available": False, "completeness": "partial"},
        }
        compiled = compile_context("fix target", "rev-2", 500, evidence, [], [])
        self.assertEqual([item["symbol_id"] for item in compiled["entry_points"]], ["def"])
        self.assertEqual([item["symbol_id"] for item in compiled["relations"]], ["ref"])
        self.assertEqual([item["symbol_id"] for item in compiled["relevant_tests"]], ["ref"])
        self.assertEqual([item["path"] for item in compiled["relevant_config"]], ["package.json"])
        self.assertEqual([item["path"] for item in compiled["rules"]], ["AGENTS.md"])
        self.assertEqual([item["path"] for item in compiled["related_dirty_diff"]], ["src/app.py"])
        self.assertTrue(any(item["id"] == "stale" and item["reason"] == "stale" for item in compiled["omitted_candidates"]))
        self.assertIn("semantic_provider_unavailable", compiled["uncertainty"])
        self.assertIn("semantic_graph_partial", compiled["uncertainty"])
        self.assertEqual(compiled["completeness"], "partial")

    def test_fingerprints_are_stable_and_change_with_revision_or_evidence(self) -> None:
        evidence = {"files": [{"path": "app.py", "content": "VALUE = 1\n"}]}
        first = compile_context("change value", "rev-a", 100, evidence, [], [])
        second = compile_context("change value", "rev-a", 100, json.loads(json.dumps(evidence)), [], [])
        self.assertEqual(first["fingerprints"], second["fingerprints"])
        changed_revision = compile_context("change value", "rev-b", 100, evidence, [], [])
        self.assertNotEqual(first["fingerprints"]["input_sha256"], changed_revision["fingerprints"]["input_sha256"])
        changed_evidence = compile_context("change value", "rev-a", 100, {"files": [{"path": "app.py", "content": "VALUE = 2\n"}]}, [], [])
        self.assertNotEqual(first["fingerprints"]["compiled_sha256"], changed_evidence["fingerprints"]["compiled_sha256"])

    def test_input_fingerprint_binds_evidence_even_when_that_evidence_is_omitted(self) -> None:
        evidence = {
            "files": [{"path": "app.py", "content": "VALUE = 1\n"}],
            "dirty_diff": [{"path": "app.py", "diff": "X" * 400}],
        }
        first = compile_context("inspect", "rev-a", 8, evidence, [], [])
        copied = compile_context("inspect", "rev-a", 8, json.loads(json.dumps(evidence)), [], [])
        changed = json.loads(json.dumps(evidence))
        changed["dirty_diff"][0]["diff"] = "Y" * 400
        second = compile_context("inspect", "rev-a", 8, changed, [], [])
        self.assertEqual(first["fingerprints"], copied["fingerprints"])
        self.assertEqual(first["related_dirty_diff"], [])
        self.assertEqual(second["related_dirty_diff"], [])
        self.assertNotEqual(first["fingerprints"]["input_sha256"], second["fingerprints"]["input_sha256"])
        self.assertEqual(first["fingerprints"]["compiled_sha256"], second["fingerprints"]["compiled_sha256"])

    def test_treatment_mode_is_off_by_default_shadow_only_and_invalid_modes_fail_closed(self) -> None:
        self.assertEqual(context_compiler_treatment({})["mode"], "off")
        shadow = context_compiler_treatment({CONTEXT_COMPILER_ENV: "shadow"})
        self.assertEqual(shadow["mode"], "shadow")
        self.assertFalse(shadow["auto_inject"])
        invalid = context_compiler_treatment({CONTEXT_COMPILER_ENV: "inject"})
        self.assertEqual(invalid["mode"], "off")
        self.assertFalse(invalid["auto_inject"])
        self.assertEqual(invalid["reason"], "CONTEXT_COMPILER_MODE_UNSUPPORTED")

    def test_prepare_context_shadow_records_status_without_changing_selected_context(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "app.py").write_text("def target():\n    return 1\n", encoding="utf-8")
            runtime = Runtime(root)
            try:
                args = {"objective": "inspect target", "queries": ["target"], "max_files": 4, "force_refresh": True}
                with patch.dict("os.environ", {CONTEXT_COMPILER_ENV: "off"}, clear=False):
                    baseline = runtime.prepare_coding_context(args)
                with patch.dict("os.environ", {CONTEXT_COMPILER_ENV: "shadow"}, clear=False):
                    shadow = runtime.prepare_coding_context(args)
                self.assertEqual(shadow["selected_paths"], baseline["selected_paths"])
                self.assertEqual(shadow["files"], baseline["files"])
                self.assertNotIn("context_compiler", baseline["composite_read"]["execution"]["localization"])
                status = shadow["composite_read"]["execution"]["localization"]["context_compiler"]
                self.assertEqual(status["mode"], "shadow")
                self.assertFalse(status["auto_inject"])
                self.assertEqual(len(status["input_sha256"]), 64)
                self.assertEqual(len(status["compiled_sha256"]), 64)
                self.assertIn("estimated_tokens", status)
                self.assertIn("selected_file_count", status)
                self.assertTrue(hasattr(runtime, "_last_context_compiler_shadow"))
                public_text = json.dumps(status, ensure_ascii=False)
                self.assertNotIn("target", public_text)
            finally:
                runtime.close()


if __name__ == "__main__":
    unittest.main()
