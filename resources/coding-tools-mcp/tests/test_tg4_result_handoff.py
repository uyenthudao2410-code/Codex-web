from __future__ import annotations

import unittest

from coding_tools_mcp.errors import ToolFailure
from coding_tools_mcp.patching import apply_update_hunks
from coding_tools_mcp.session_control import _output_page_handoff


class _RetainedSession:
    session_id = "command-retained"

    @staticmethod
    def retained_stream_metrics(_stream: str) -> dict[str, int]:
        return {
            "total_stream_bytes": 120_000,
            "total_retained_bytes": 65_536,
            "evicted_gap_bytes": 54_464,
        }


class Tg4ResultHandoffTests(unittest.TestCase):
    def test_retention_gap_never_claims_complete_output_recovery(self) -> None:
        handoff = _output_page_handoff(
            _RetainedSession(),  # type: ignore[arg-type]
            stream="stdout",
            output_ref="command:command-retained:stdout",
            requested_offset=8_192,
            next_offset=62_656,
            limit=8_192,
            has_more=True,
        )

        self.assertEqual(handoff["kind"], "OUTPUT_PAGE")
        self.assertEqual(handoff["reason"], "OUTPUT_RETENTION_BOUND")
        self.assertFalse(
            handoff["recoverability"]["continuation_recovers_all_omitted_data"]
        )
        self.assertIn("middle gap", handoff["narrow_scope_hint"])
        self.assertEqual(handoff["next_operation"]["tool"], "command_control")

    def test_existing_exact_patch_primitive_fails_closed_on_ambiguity(self) -> None:
        content = "VALUE = 1\nVALUE = 1\n"
        hunks = [["-VALUE = 1", "+VALUE = 2"]]

        with self.assertRaises(ToolFailure) as caught:
            apply_update_hunks(content, hunks, "app.py")

        self.assertEqual(caught.exception.code, "PATCH_CONTEXT_AMBIGUOUS")
        self.assertEqual(caught.exception.details["candidate_lines"], [1, 2])


if __name__ == "__main__":
    unittest.main()
