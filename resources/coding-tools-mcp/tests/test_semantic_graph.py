from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from coding_tools_mcp.semantic_graph import MAX_GRAPH_RECORD_BUDGET, SemanticRepositoryGraph


class SemanticRepositoryGraphTests(unittest.TestCase):
    def test_degraded_text_fallback_is_useful_relative_and_explicitly_partial(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "src").mkdir()
            (root / "src/app.py").write_text("def target():\n    return 1\n", encoding="utf-8")
            graph = SemanticRepositoryGraph(root)
            status = graph.update(
                searches=[{
                    "query": "target",
                    "engine": "rg",
                    "matches": [{"path": "src/app.py", "line": 1}],
                }],
                provider_status={
                    "available": False,
                    "provider": None,
                    "reason": "NATIVE_LSP_BINDING_NOT_CONFIGURED",
                },
            )
            self.assertFalse(status["provider_available"])
            self.assertEqual(status["fallback_records"], 1)
            self.assertEqual(status["completeness"], "partial")
            rows = graph.resolve_symbols("target", 5)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["path"], "src/app.py")
            self.assertEqual(rows[0]["provider"], "text_fallback")
            self.assertEqual(rows[0]["confidence"], "low")
            self.assertEqual(rows[0]["completeness"], "partial")
            self.assertTrue(rows[0]["current"])
            self.assertFalse(rows[0]["stale"])

    def test_semantic_records_link_references_related_tests_and_impact(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "src").mkdir()
            (root / "tests").mkdir()
            (root / "src/app.py").write_text("def target():\n    return 1\n", encoding="utf-8")
            (root / "tests/test_app.py").write_text("def test_target():\n    assert target() == 1\n", encoding="utf-8")
            graph = SemanticRepositoryGraph(root)
            status = graph.update(
                searches=[{
                    "query": "target",
                    "engine": "semantic:native-test",
                    "matches": [
                        {"path": "src/app.py", "line": 1, "kind": "definition", "symbol": "target"},
                        {"path": "tests/test_app.py", "line": 2, "kind": "reference", "symbol": "target"},
                    ],
                }],
                provider_status={"available": True, "provider": "native-test", "provider_version": "1.2.3"},
            )
            self.assertEqual(status["completeness"], "complete")
            definition = next(row for row in graph.resolve_symbols("target", 10) if row["kind"] == "definition")
            refs = graph.references(definition["symbol_id"], 10)
            self.assertEqual([row["kind"] for row in refs], ["reference"])
            self.assertEqual(refs[0]["provider_version"], "1.2.3")
            related = graph.related_tests(definition["symbol_id"], 10)
            self.assertEqual([row["path"] for row in related], ["tests/test_app.py"])
            impact = graph.impact([definition["symbol_id"]], depth=1, budget=10)
            self.assertEqual({row["path"] for row in impact["records"]}, {"src/app.py", "tests/test_app.py"})
            self.assertFalse(impact["truncated"])

    def test_changed_source_record_is_stale_and_never_current(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "app.py"
            source.write_text("def target():\n    return 1\n", encoding="utf-8")
            graph = SemanticRepositoryGraph(root)
            graph.update(
                searches=[{
                    "query": "target",
                    "engine": "semantic:native-test",
                    "matches": [{"path": "app.py", "line": 1, "kind": "definition", "symbol": "target"}],
                }],
                provider_status={"available": True, "provider": "native-test"},
            )
            source.write_text("def target():\n    return 2\n", encoding="utf-8")
            row = graph.resolve_symbols("target", 5)[0]
            self.assertFalse(row["current"])
            self.assertTrue(row["stale"])
            self.assertEqual(graph.status(refresh=True)["stale_records"], 1)

    def test_incremental_update_replaces_touched_path_and_retains_untouched_record(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "src").mkdir()
            (root / "tests").mkdir()
            app = root / "src/app.py"
            test = root / "tests/test_app.py"
            app.write_text("def target():\n    return 1\n", encoding="utf-8")
            test.write_text("target()\n", encoding="utf-8")
            graph = SemanticRepositoryGraph(root)
            graph.update(
                searches=[{
                    "query": "target",
                    "engine": "semantic:native-test",
                    "matches": [
                        {"path": "src/app.py", "line": 1, "kind": "definition", "symbol": "target"},
                        {"path": "tests/test_app.py", "line": 1, "kind": "reference", "symbol": "target"},
                    ],
                }],
                provider_status={"available": True, "provider": "native-test"},
            )
            old_test_id = graph.related_tests(graph.resolve_symbols("target", 10)[0]["symbol_id"], 10)[0]["symbol_id"]
            app.write_text("def target():\n    return 2\n", encoding="utf-8")
            status = graph.update(
                searches=[{
                    "query": "target",
                    "engine": "semantic:native-test",
                    "matches": [{"path": "src/app.py", "line": 1, "kind": "definition", "symbol": "target"}],
                }],
                provider_status={"available": True, "provider": "native-test"},
            )
            self.assertEqual(status["indexed_records"], 2)
            self.assertEqual(status["last_update"]["retained_records"], 1)
            new_definition = next(row for row in graph.resolve_symbols("target", 10) if row["path"] == "src/app.py")
            related = graph.related_tests(new_definition["symbol_id"], 10)
            self.assertEqual([row["symbol_id"] for row in related], [old_test_id])

    def test_large_source_uses_bounded_sample_and_never_claims_complete_currentness(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "large.py").write_bytes(b"x" * 4096)
            graph = SemanticRepositoryGraph(root)
            status = graph.update(
                searches=[{
                    "query": "large",
                    "engine": "semantic:native-test",
                    "matches": [{"path": "large.py", "line": 1, "kind": "definition", "symbol": "large"}],
                }],
                provider_status={"available": True, "provider": "native-test"},
                max_total_bytes=1024,
                max_file_bytes=1024,
            )
            self.assertLessEqual(status["last_update"]["bytes_read"], 1024)
            row = graph.resolve_symbols("large", 5)[0]
            self.assertEqual(row["source_hash_kind"], "prefix_suffix")
            self.assertEqual(row["completeness"], "partial")
            self.assertIsNone(row["current"])
            self.assertFalse(row["stale"])

    def test_reduced_remaining_budget_is_reused_for_stale_refresh(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "first.py").write_bytes(b"a" * 4096)
            (root / "second.py").write_bytes(b"b" * 4096)
            graph = SemanticRepositoryGraph(root)
            status = graph.update(
                searches=[{
                    "query": "symbols",
                    "engine": "semantic:native-test",
                    "matches": [
                        {"path": "first.py", "line": 1, "kind": "definition", "symbol": "first"},
                        {"path": "second.py", "line": 1, "kind": "definition", "symbol": "second"},
                    ],
                }],
                provider_status={"available": True, "provider": "native-test"},
                max_total_bytes=1536,
                max_file_bytes=1024,
            )
            self.assertEqual(status["last_update"]["bytes_read"], 1536)
            second = graph.resolve_symbols("second", 5)[0]
            self.assertIsNone(second["current"])
            self.assertFalse(second["stale"])
            refreshed = graph.status(refresh=True)
            self.assertEqual(refreshed["stale_records"], 0)
            self.assertEqual(refreshed["uncertain_records"], 2)

    def test_incremental_graph_has_a_hard_lifetime_record_cap(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            graph = SemanticRepositoryGraph(root)
            last_status = None
            for start in range(0, 240, 60):
                matches = []
                for index in range(start, start + 60):
                    path = f"file-{index}.py"
                    (root / path).write_text(f"symbol_{index} = {index}\n", encoding="utf-8")
                    matches.append({
                        "path": path,
                        "line": 1,
                        "kind": "definition",
                        "symbol": f"symbol_{index}",
                    })
                last_status = graph.update(
                    searches=[{
                        "query": f"batch-{start}",
                        "engine": "semantic:native-test",
                        "matches": matches,
                    }],
                    provider_status={"available": True, "provider": "native-test"},
                    max_records=MAX_GRAPH_RECORD_BUDGET,
                    max_files=64,
                )
            self.assertIsNotNone(last_status)
            self.assertEqual(last_status["indexed_records"], MAX_GRAPH_RECORD_BUDGET)
            self.assertEqual(last_status["last_update"]["evicted_records"], 40)
            self.assertEqual(last_status["last_update"]["retained_records"], 140)
            self.assertEqual(graph.resolve_symbols("symbol_0", 5), [])
            newest = graph.resolve_symbols("symbol_239", 5)
            self.assertEqual(len(newest), 1)
            self.assertEqual(newest[0]["path"], "file-239.py")


if __name__ == "__main__":
    unittest.main()
