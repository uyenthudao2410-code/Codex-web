from __future__ import annotations

import unittest

from coding_tools_mcp.trace_context import parse_trace_context, trace_context_metadata


VALID_PARENT = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"


class TraceContextTests(unittest.TestCase):
    def test_valid_context_projects_only_content_free_metadata(self) -> None:
        context = parse_trace_context(VALID_PARENT, "vendor=opaque,other=value")
        self.assertEqual(context["trace_id"], "4bf92f3577b34da6a3ce929d0e0e4736")
        self.assertEqual(context["parent_span_id"], "00f067aa0ba902b7")
        metadata = trace_context_metadata(context)
        self.assertEqual(metadata["trace_id"], context["trace_id"])
        self.assertTrue(metadata["tracestate_present"])
        self.assertNotIn("traceparent", metadata)
        self.assertNotIn("tracestate", metadata)

    def test_absent_context_is_valid_and_tracestate_cannot_stand_alone(self) -> None:
        self.assertEqual(parse_trace_context(None, None), {})
        with self.assertRaises(ValueError):
            parse_trace_context(None, "vendor=opaque")

    def test_malformed_or_zero_identifiers_fail_closed(self) -> None:
        rejected = [
            "ff-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
            "00-00000000000000000000000000000000-00f067aa0ba902b7-01",
            "00-4bf92f3577b34da6a3ce929d0e0e4736-0000000000000000-01",
            "00-4BF92F3577B34DA6A3CE929D0E0E4736-00f067aa0ba902b7-01",
        ]
        for value in rejected:
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_trace_context(value)

    def test_tracestate_is_bounded_unique_ascii_and_rejects_secret_like_keys(self) -> None:
        for state in (
            "token=opaque",
            "vendor=one,vendor=two",
            "vendor=has,comma",
            "vendor=has=equals",
            "vendor=\u2603",
            "vendor=" + "x" * 513,
        ):
            with self.subTest(state=state[:40]), self.assertRaises(ValueError):
                parse_trace_context(VALID_PARENT, state)


if __name__ == "__main__":
    unittest.main()
