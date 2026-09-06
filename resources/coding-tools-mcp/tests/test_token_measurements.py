from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

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

    def test_later_final_structural_snapshot_replaces_interim_without_duplicate_turn(self):
        turn = "stream-turn"
        trace = "stream-trace"
        span = {"event_type": "host_turn_span", "turn_id": turn, "trace_id": trace}
        interim = _features(turn=turn, trace=trace, user_chars=100, asst_chars=300, wall_time_ms=3400)
        final = _features(turn=turn, trace=trace, user_chars=100, asst_chars=900, wall_time_ms=5200)

        structural = tm.effective_turn_measurements([span, interim, final])
        self.assertEqual(len(structural), 1)
        self.assertEqual(structural[0]["kind"], "structural_estimate")
        self.assertEqual(structural[0]["wall_time_ms"], 5200)
        self.assertEqual(structural[0]["total"], {"point": 250, "lower": 167, "upper": 500})

        public = tm.summarize_measurements(structural)
        self.assertEqual(public["turns_total"], 1)
        self.assertEqual(public["session_total"], {"point": 250, "lower": 167, "upper": 500})
        self.assertEqual(public["latest_turn"]["point"], 250)
        self.assertEqual(public["recent_turns"], [{
            "wall_time_ms": 5200,
            "kind": "structural_estimate",
            "point": 250,
            "lower": 167,
            "upper": 500,
        }])
        rendered = json.dumps(public)
        self.assertNotIn(turn, rendered)
        self.assertNotIn(trace, rendered)

        with_exact = tm.effective_turn_measurements([span, interim, final, _exact(turn=turn, trace=trace)])
        self.assertEqual(len(with_exact), 1)
        self.assertEqual(with_exact[0]["kind"], "exact")
        self.assertEqual(with_exact[0]["total"], {"point": 1100, "lower": 1100, "upper": 1100})

    def test_malformed_or_missing_latest_structural_snapshot_is_unknown_not_zero(self):
        turn = "bad-final-turn"
        trace = "bad-final-trace"
        span = {"event_type": "host_turn_span", "turn_id": turn, "trace_id": trace}
        interim = _features(turn=turn, trace=trace, user_chars=100, asst_chars=300)
        malformed = _features(turn=turn, trace=trace, user_chars=100, asst_chars="not-a-number")
        missing = _features(turn=turn, trace=trace, user_chars=100)
        del missing["asst_chars"]

        for latest in (malformed, missing):
            measurements = tm.effective_turn_measurements([span, interim, latest])
            self.assertEqual(len(measurements), 1)
            self.assertEqual(measurements[0]["kind"], "unknown")
            self.assertIsNone(measurements[0]["total"])
            public = tm.summarize_measurements(measurements)
            self.assertEqual(public["session_total"], {"point": None, "lower": None, "upper": None})
            self.assertIsNone(public["latest_turn"]["point"])

    def test_later_event_for_an_earlier_turn_becomes_the_latest_measurement(self):
        first = "first-turn"
        second = "second-turn"
        events = [
            {"event_type": "host_turn_span", "turn_id": first, "trace_id": first},
            {"event_type": "host_turn_span", "turn_id": second, "trace_id": second},
            _features(turn=first, trace=first, user_chars=100, asst_chars=900),
        ]

        measurements = tm.effective_turn_measurements(events)
        self.assertEqual([item["turn_id"] for item in measurements], [second, first])
        public = tm.summarize_measurements(measurements)
        self.assertEqual(public["latest_turn"], {
            "kind": "structural_estimate",
            "point": 250,
            "lower": 167,
            "upper": 500,
        })

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

    def test_recent_turns_newest_first_without_identity(self):
        first = tm.effective_turn_measurements([_features(turn="a", trace="a")])[0]
        second = tm.effective_turn_measurements([_exact(turn="b", trace="b")])[0]
        summary = tm.summarize_measurements([first, second])
        recent = summary["recent_turns"]
        self.assertEqual(len(recent), 2)
        self.assertEqual(recent[0]["kind"], "exact")
        self.assertEqual(recent[1]["kind"], "structural_estimate")
        for row in recent:
            self.assertNotIn("turn_id", row)
            self.assertNotIn("trace_id", row)
            self.assertIn("wall_time_ms", row)


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


class LiveTailTest(unittest.TestCase):
    def test_latest_turn_invalid_arguments_are_unavailable(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            cases = [
                tm.latest_turn_measurement(None),
                tm.latest_turn_measurement(root, tail_lines=None),
                tm.latest_turn_measurement(root, tail_lines=float("inf")),
            ]

        for live in cases:
            self.assertEqual(live["measurement"], "chat_turn_measurements_v1")
            self.assertEqual(live["missing_measurement_policy"], "unknown_not_zero")
            self.assertTrue(live["content_free"])
            self.assertFalse(live["journal_available"])
            self.assertIsNone(live["latest_turn"])
            self.assertEqual(live["missing_reason"], "chat_journal_unavailable")

    def test_latest_turn_reads_bounded_bytes_and_tail_lines(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / ".coding-tools" / "evaluation"
            target.mkdir(parents=True, exist_ok=True)
            journal = target / "chatweb-host-observations.jsonl"
            journal.write_text(
                json.dumps({"event_type": "ignored", "padding": "x" * (tm.LIVE_TAIL_BYTES + 1024)}) + "\n"
                + json.dumps(_features(turn="t1", trace="r1", user_chars=100, asst_chars=300)) + "\n"
                + json.dumps(_exact(turn="t2", trace="r2")) + "\n", encoding="utf-8")

            class ReadSpy:
                def __init__(self, path: Path):
                    self.handle = path.open("rb")
                    self.read_sizes: list[int] = []
                    self.seek_calls: list[tuple[int, int]] = []

                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    self.handle.close()

                def seek(self, offset, whence=0):
                    self.seek_calls.append((offset, whence))
                    return self.handle.seek(offset, whence)

                def tell(self):
                    return self.handle.tell()

                def read(self, size=-1):
                    self.read_sizes.append(size)
                    if size < 0:
                        raise AssertionError("latest tail must not issue an unbounded read")
                    return self.handle.read(size)

            spy = ReadSpy(journal)
            with patch.object(tm, "open", return_value=spy, create=True):
                live = tm.latest_turn_measurement(root, tail_lines=2)
            self.assertEqual(live["measurement"], "chat_turn_measurements_v1")
            self.assertTrue(live["journal_available"])
            self.assertEqual(live["latest_turn"]["kind"], "exact")
            self.assertEqual(live["latest_turn"]["point"], 1100)
            self.assertEqual(spy.read_sizes, [tm.LIVE_TAIL_BYTES])
            self.assertIn((0, 2), spy.seek_calls)

    def test_latest_turn_discards_partial_first_record_at_byte_boundary(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / ".coding-tools" / "evaluation"
            target.mkdir(parents=True, exist_ok=True)
            (target / "chatweb-host-observations.jsonl").write_text(
                json.dumps({"event_type": "ignored", "padding": "x" * (tm.LIVE_TAIL_BYTES + 1024)}) + "\n"
                + json.dumps(_exact(turn="t2", trace="r2")) + "\n", encoding="utf-8")
            live = tm.latest_turn_measurement(root)
            self.assertEqual(live["latest_turn"]["kind"], "exact")
            self.assertEqual(live["latest_turn"]["point"], 1100)

    def test_latest_turn_ignores_a_trailing_partial_record(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / ".coding-tools" / "evaluation"
            target.mkdir(parents=True, exist_ok=True)
            (target / "chatweb-host-observations.jsonl").write_bytes(
                (json.dumps(_exact(turn="t2", trace="r2")) + "\n").encode("utf-8")
                + b'{"event_type":"turn_features","turn_id":"partial"')
            live = tm.latest_turn_measurement(root)
            self.assertEqual(live["latest_turn"]["kind"], "exact")
            self.assertEqual(live["latest_turn"]["point"], 1100)

    def test_latest_turn_fails_closed_for_complete_invalid_final_json_record(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / ".coding-tools" / "evaluation"
            target.mkdir(parents=True, exist_ok=True)
            (target / "chatweb-host-observations.jsonl").write_bytes(
                (json.dumps(_exact(turn="t2", trace="r2")) + "\n").encode("utf-8")
                + b"not-json\n"
            )
            live = tm.latest_turn_measurement(root)
            self.assertTrue(live["journal_available"])
            self.assertIsNone(live["latest_turn"])
            self.assertEqual(live["missing_reason"], "latest_tail_record_invalid")

    def test_latest_turn_fails_closed_for_invalid_utf8_final_record(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / ".coding-tools" / "evaluation"
            target.mkdir(parents=True, exist_ok=True)
            (target / "chatweb-host-observations.jsonl").write_bytes(
                (json.dumps(_exact(turn="t2", trace="r2")) + "\n").encode("utf-8")
                + b'{"event_type":"turn_features","turn_id":"bad\xff","trace_id":"r"}\n'
            )
            live = tm.latest_turn_measurement(root)
            self.assertTrue(live["journal_available"])
            self.assertIsNone(live["latest_turn"])
            self.assertEqual(live["missing_reason"], "latest_tail_record_invalid")

    def test_latest_turn_unknown_when_tail_unmeasured(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / ".coding-tools" / "evaluation"
            target.mkdir(parents=True, exist_ok=True)
            (target / "chatweb-host-observations.jsonl").write_text(
                json.dumps({"event_type": "host_turn_span", "turn_id": "t", "trace_id": "r"}) + "\n",
                encoding="utf-8")
            live = tm.latest_turn_measurement(root)
            self.assertTrue(live["journal_available"])
            self.assertIsNone(live["latest_turn"])
            self.assertEqual(live["missing_reason"], "latest_turn_unmeasured")

    def test_latest_turn_keeps_malformed_final_structural_measurement_unknown(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / ".coding-tools" / "evaluation"
            target.mkdir(parents=True, exist_ok=True)
            malformed = _features(turn="t", trace="r")
            malformed.pop("asst_chars")
            (target / "chatweb-host-observations.jsonl").write_text(json.dumps(malformed) + "\n", encoding="utf-8")
            live = tm.latest_turn_measurement(root)
            self.assertTrue(live["journal_available"])
            self.assertIsNone(live["latest_turn"])
            self.assertEqual(live["missing_reason"], "latest_turn_unmeasured")

    def test_latest_turn_missing_journal_is_unavailable(self):
        with TemporaryDirectory() as tmp:
            live = tm.latest_turn_measurement(Path(tmp))
            self.assertFalse(live["journal_available"])
            self.assertIsNone(live["latest_turn"])


if __name__ == "__main__":
    unittest.main()
