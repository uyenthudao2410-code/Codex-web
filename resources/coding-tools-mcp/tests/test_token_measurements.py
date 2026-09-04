from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from coding_tools_mcp import token_measurements as tm
from coding_tools_mcp.operations_analytics import operations_analytics
from coding_tools_mcp.orchestration_ledger import OrchestrationLedger


def _features(turn="turn-1", trace="trace-1", user_chars=400, asst_chars=1600, **extra):
    event = {
        "schema_version": 6,
        "event_type": "turn_features",
        "observation_id": "a1:features",
        "navigation_epoch": 1,
        "clock_domain": "electron-renderer:1",
        "monotonic_ms": 30,
        "wall_time_ms": 1030,
        "trace_id": trace,
        "turn_id": turn,
        "observer_plane": "electron_chatgpt_dom",
        "measurement": "structural_turn_features",
        "turn_ordinal": 7,
        "duration_ms": 12500,
        "tool_card_count": 0,
        "user_chars": user_chars,
        "user_code_blocks": 0,
        "asst_chars": asst_chars,
        "asst_code_blocks": 1,
    }
    event.update(extra)
    return event


def _exact(turn="turn-1", trace="trace-1"):
    return {
        "schema_version": 6,
        "event_type": "controller_usage",
        "observation_id": "u1",
        "navigation_epoch": 1,
        "clock_domain": "electron-renderer:1",
        "monotonic_ms": 31,
        "wall_time_ms": 1031,
        "trace_id": trace,
        "turn_id": turn,
        "observer_plane": "electron_chatgpt_structured_response",
        "measurement": "structured_response_usage_exact",
        "accounting_profile": "openai_compatible",
        "source": "client_reported",
        "input_tokens": 1000,
        "cached_input_tokens": 200,
        "output_tokens": 100,
        "reasoning_output_tokens": 10,
    }


class StructuralEstimateTest(unittest.TestCase):
    def test_chars_ladder_math(self):
        estimated = tm.structural_estimate(_features(user_chars=400, asst_chars=1600))
        self.assertIsNotNone(estimated)
        assert estimated is not None
        self.assertEqual(estimated["kind"], "structural_estimate")
        # total 2000 chars: P50 500, P10 333, P90 1000.
        self.assertEqual(estimated["total"], {"point": 500, "lower": 333, "upper": 1000})
        self.assertIsNone(estimated["input"])
        self.assertIsNone(estimated["output"])
        self.assertEqual(estimated["confidence"], "none")
        self.assertEqual(estimated["method_version"], "structural-chars-v1")

    def test_empty_or_missing_chars_is_no_estimate(self):
        self.assertIsNone(tm.structural_estimate(_features(user_chars=0, asst_chars=0)))
        broken = _features()
        del broken["asst_chars"]
        self.assertIsNone(tm.structural_estimate(broken))
        self.assertIsNone(tm.structural_estimate({"turn_id": "t"}))

    def test_exact_receipt_validation(self):
        measured = tm.exact_measurement(_exact())
        self.assertIsNotNone(measured)
        assert measured is not None
        self.assertEqual(measured["total"], {"point": 1100, "lower": 1100, "upper": 1100})
        broken = _exact()
        broken["cached_input_tokens"] = 5000
        self.assertIsNone(tm.exact_measurement(broken))


class EffectiveTurnTest(unittest.TestCase):
    def test_exact_supersedes_structural_without_double_count(self):
        measurements = tm.effective_turn_measurements([_features(), _exact()])
        self.assertEqual(len(measurements), 1)
        self.assertEqual(measurements[0]["kind"], "exact")

    def test_structural_when_no_exact(self):
        measurements = tm.effective_turn_measurements([_features()])
        self.assertEqual(len(measurements), 1)
        self.assertEqual(measurements[0]["kind"], "structural_estimate")

    def test_unknown_when_nothing_usable(self):
        measurements = tm.effective_turn_measurements([{"event_type": "host_turn_span", "turn_id": "t", "trace_id": "r"}])
        self.assertEqual(len(measurements), 1)
        self.assertEqual(measurements[0]["kind"], "unknown")
        self.assertIsNone(measurements[0]["total"])

    def test_session_summary_math(self):
        first = tm.effective_turn_measurements([_features(turn="a", trace="a")])[0]
        second = tm.effective_turn_measurements([_exact(turn="b", trace="b")])[0]
        summary = tm.summarize_measurements([first, second])
        self.assertEqual(summary["turns_total"], 2)
        self.assertEqual(summary["turns_exact"], 1)
        self.assertEqual(summary["turns_estimated"], 1)
        self.assertEqual(summary["turns_unknown"], 0)
        self.assertEqual(summary["session_total"], {"point": 500 + 1100, "lower": 333 + 1100, "upper": 1000 + 1100})
        self.assertEqual(summary["latest_turn"]["kind"], "exact")

    def test_empty_summary_is_null_not_zero(self):
        summary = tm.summarize_measurements([])
        self.assertEqual(summary["session_total"], {"point": None, "lower": None, "upper": None})
        self.assertIsNone(summary["latest_turn"])

    def test_turn_cap_keeps_latest(self):
        events = [_features(turn=f"t{i}", trace=f"r{i}") for i in range(5)]
        measurements = tm.effective_turn_measurements(events, max_turns=2)
        self.assertEqual([item["turn_id"] for item in measurements], ["t3", "t4"])


class JournalWorkspaceTest(unittest.TestCase):
    def _write_journal(self, root: Path, lines: list[str], rotated: list[str] | None = None) -> None:
        target = root / ".coding-tools" / "evaluation"
        target.mkdir(parents=True, exist_ok=True)
        (target / "chatweb-host-observations.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
        if rotated is not None:
            (target / "chatweb-host-observations.jsonl.1").write_text("\n".join(rotated) + "\n", encoding="utf-8")

    def test_rotated_journal_merges_chronologically(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            old = _features(turn="old", trace="old")
            new = _features(turn="new", trace="new")
            self._write_journal(root, [json.dumps(new)], rotated=[json.dumps(old), "not json{{{"])
            summary = tm.summarize_workspace(root)
            self.assertTrue(summary["journal_available"])
            self.assertEqual(summary["turns_total"], 2)
            self.assertEqual(summary["turns_estimated"], 2)
            self.assertEqual(summary["blend"], "estimated")

    def test_missing_journal_is_unavailable_unknown(self):
        with TemporaryDirectory() as tmp:
            summary = tm.summarize_workspace(Path(tmp))
            self.assertFalse(summary["journal_available"])
            self.assertEqual(summary["session_total"], {"point": None, "lower": None, "upper": None})
            self.assertEqual(summary["missing_reason"], "chat_journal_unavailable")

    def test_no_content_fields_consumed(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            event = _features()
            event["prompt"] = "secret prompt"
            event["response"] = "secret response"
            event["url"] = "https://chatgpt.com/c/secret"
            self._write_journal(root, [json.dumps(event)])
            summary = tm.summarize_workspace(root)
            blob = json.dumps(summary)
            self.assertNotIn("secret", blob)


class AnalyticsWiringTest(unittest.TestCase):
    def test_operations_analytics_carries_turn_section(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger = OrchestrationLedger(root)
            target = root / ".coding-tools" / "evaluation"
            target.mkdir(parents=True, exist_ok=True)
            (target / "chatweb-host-observations.jsonl").write_text(
                json.dumps(_features(turn="w1", trace="w1")) + "\n", encoding="utf-8")
            result = operations_analytics(ledger, performance={}, days=7, now="2026-09-04T10:00:00Z")
            section = result["turn_token_measurements"]
            self.assertEqual(section["measurement"], "chat_turn_measurements_v1")
            self.assertEqual(section["missing_measurement_policy"], "unknown_not_zero")
            self.assertTrue(section["journal_available"])
            self.assertEqual(section["turns_total"], 1)
            self.assertEqual(section["turns_estimated"], 1)
            self.assertEqual(section["session_total"]["point"], 500)

    def test_operations_analytics_survives_missing_journal(self):
        with TemporaryDirectory() as tmp:
            ledger = OrchestrationLedger(Path(tmp))
            result = operations_analytics(ledger, performance={}, days=7, now="2026-09-04T10:00:00Z")
            section = result["turn_token_measurements"]
            self.assertFalse(section["journal_available"])
            self.assertEqual(section["session_total"], {"point": None, "lower": None, "upper": None})


if __name__ == "__main__":
    unittest.main()
