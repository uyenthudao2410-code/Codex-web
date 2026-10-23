from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from coding_tools_mcp.continuation_send_state import (
    SEND_STATE_CONFIRMED,
    SEND_STATE_NOT_ATTEMPTED,
    SEND_STATE_POSSIBLY_SENT,
    SEND_STATE_STARTED_UNKNOWN,
    advance_send_state,
    goal_completion_signal,
    handoff_resume_directive,
    normalize_send_checkpoint,
    normalize_send_state,
    send_may_be_replayed,
    send_requires_reconciliation,
)
from coding_tools_mcp.orchestration_ledger import OrchestrationLedger


class SendStateVocabularyTests(unittest.TestCase):
    def test_canonical_and_cos_spellings_normalize(self) -> None:
        self.assertEqual(normalize_send_state("not_attempted"), SEND_STATE_NOT_ATTEMPTED)
        self.assertEqual(normalize_send_state("not-attempted"), SEND_STATE_NOT_ATTEMPTED)
        self.assertEqual(normalize_send_state("attempted-unresolved"), SEND_STATE_STARTED_UNKNOWN)
        self.assertEqual(normalize_send_state("started_unknown"), SEND_STATE_STARTED_UNKNOWN)
        self.assertEqual(normalize_send_state("dispatched-unresolved"), SEND_STATE_POSSIBLY_SENT)
        self.assertEqual(normalize_send_state("possibly_sent"), SEND_STATE_POSSIBLY_SENT)
        self.assertEqual(normalize_send_state("sent"), SEND_STATE_CONFIRMED)
        self.assertEqual(normalize_send_state(" CONFIRMED "), SEND_STATE_CONFIRMED)

    def test_unknown_state_is_rejected(self) -> None:
        for bad in ("", "delivered", "pending", None, 3, {"state": "sent"}):
            with self.assertRaises(ValueError):
                normalize_send_state(bad)  # type: ignore[arg-type]


class SendStateTransitionTests(unittest.TestCase):
    def test_forward_and_idempotent_transitions_are_allowed(self) -> None:
        self.assertEqual(
            advance_send_state("not_attempted", "started_unknown"), SEND_STATE_STARTED_UNKNOWN
        )
        self.assertEqual(
            advance_send_state("started_unknown", "started_unknown"), SEND_STATE_STARTED_UNKNOWN
        )
        # Late confirmation evidence may skip the middle positions.
        self.assertEqual(advance_send_state("not_attempted", "sent"), SEND_STATE_CONFIRMED)
        self.assertEqual(
            advance_send_state("attempted-unresolved", "dispatched-unresolved"),
            SEND_STATE_POSSIBLY_SENT,
        )

    def test_backward_transitions_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            advance_send_state("possibly_sent", "not_attempted")
        with self.assertRaises(ValueError):
            advance_send_state("confirmed", "possibly_sent")
        # A confirmed effect is terminal: it cannot be rewritten as replayable.
        with self.assertRaises(ValueError):
            advance_send_state("confirmed", "started_unknown")


class SendStateReplayRuleTests(unittest.TestCase):
    def test_replay_and_reconciliation_truth_table(self) -> None:
        expected = {
            SEND_STATE_NOT_ATTEMPTED: (True, False, "REPLAY_SAFE"),
            SEND_STATE_STARTED_UNKNOWN: (True, False, "REPLAY_SAFE"),
            SEND_STATE_POSSIBLY_SENT: (False, True, "RECONCILE_BEFORE_REPLAY"),
            SEND_STATE_CONFIRMED: (False, False, "ALREADY_CONFIRMED"),
        }
        for state, (replay, reconcile, directive_name) in expected.items():
            self.assertEqual(send_may_be_replayed(state), replay, state)
            self.assertEqual(send_requires_reconciliation(state), reconcile, state)
            directive = handoff_resume_directive(state)
            self.assertEqual(directive["state"], state)
            self.assertEqual(directive["directive"], directive_name)
            self.assertEqual(directive["may_replay"], replay)
            self.assertEqual(directive["requires_reconciliation"], reconcile)

    def test_unknown_outcome_is_never_replayable(self) -> None:
        # The core CoS rule: unknown means reconcile, never resend.
        directive = handoff_resume_directive({"state": "dispatched-unresolved", "messageId": "m-1"})
        self.assertFalse(directive["may_replay"])
        self.assertTrue(directive["requires_reconciliation"])


class SendCheckpointTests(unittest.TestCase):
    def test_cos_camel_case_message_id_is_accepted_and_extras_dropped(self) -> None:
        checkpoint = normalize_send_checkpoint(
            {"state": "attempted-unresolved", "messageId": "msg-42", "unrelated": "drop me"}
        )
        self.assertEqual(
            checkpoint, {"state": SEND_STATE_STARTED_UNKNOWN, "message_id": "msg-42"}
        )

    def test_checkpoint_requires_object_with_valid_state(self) -> None:
        with self.assertRaises(ValueError):
            normalize_send_checkpoint("sent")  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            normalize_send_checkpoint({"message_id": "m-1"})
        with self.assertRaises(ValueError):
            normalize_send_checkpoint({"state": "sent", "message_id": 7})


class HandoffCapsuleSendCheckpointTests(unittest.TestCase):
    def test_capsule_round_trip_preserves_checkpoint_and_directive(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            checkpoint = normalize_send_checkpoint(
                {"state": "dispatched-unresolved", "messageId": None}
            )
            created = ledger.record_handoff_capsule(
                run_id="run-1",
                payload={"goal": "resume in chat B", "send_checkpoint": checkpoint},
            )
            self.assertEqual(created["payload"]["send_checkpoint"]["state"], SEND_STATE_POSSIBLY_SENT)

            latest = OrchestrationLedger(Path(temp)).latest_handoff_capsule(run_id="run-1")
            self.assertIsNotNone(latest)
            assert latest is not None
            stored = latest["payload"]["send_checkpoint"]
            self.assertEqual(stored, {"state": SEND_STATE_POSSIBLY_SENT, "message_id": ""})
            directive = handoff_resume_directive(stored)
            self.assertEqual(directive["directive"], "RECONCILE_BEFORE_REPLAY")
            self.assertFalse(directive["may_replay"])


class GoalCompletionSignalTests(unittest.TestCase):
    def test_all_criteria_satisfied_is_complete(self) -> None:
        signal = goal_completion_signal(
            {
                "c1": {"status": "PROVEN"},
                "c2": {"status": "SATISFIED_NON_CODE"},
            }
        )
        self.assertTrue(signal["complete"])
        self.assertFalse(signal["may_continue"])
        self.assertEqual(signal["stop_reason"], "CRITERIA_COMPLETE")
        self.assertEqual(signal["incomplete_reasons"], [])
        self.assertEqual(signal["criteria_proven"], 2)

    def test_unresolved_criteria_mean_incomplete_and_continuable(self) -> None:
        signal = goal_completion_signal(
            {"c1": {"status": "PROVEN"}, "c2": {"status": "UNRESOLVED"}},
            remaining_decision_turns=5,
            remaining_patch_attempts=2,
        )
        self.assertFalse(signal["complete"])
        self.assertTrue(signal["may_continue"])
        self.assertEqual(signal["unresolved_criterion_ids"], ["c2"])
        self.assertEqual(signal["incomplete_reasons"], ["UNRESOLVED_CRITERIA"])
        self.assertEqual(signal["stop_reason"], "")

    def test_string_status_coverage_form_is_accepted(self) -> None:
        signal = goal_completion_signal({"c1": "PROVEN"})
        self.assertTrue(signal["complete"])

    def test_no_progress_cap_is_a_hard_stop(self) -> None:
        signal = goal_completion_signal(
            {"c1": {"status": "UNRESOLVED"}},
            no_progress_count=2,
            max_no_progress=2,
        )
        self.assertFalse(signal["complete"])
        self.assertFalse(signal["may_continue"])
        self.assertEqual(signal["stop_reason"], "NO_PROGRESS_LIMIT_REACHED")
        self.assertIn("NO_PROGRESS_LIMIT_REACHED", signal["incomplete_reasons"])

    def test_exhausted_budgets_are_hard_stops(self) -> None:
        signal = goal_completion_signal(
            {"c1": {"status": "UNRESOLVED"}},
            remaining_decision_turns=0,
        )
        self.assertFalse(signal["may_continue"])
        self.assertEqual(signal["stop_reason"], "DECISION_TURNS_EXHAUSTED")

        signal = goal_completion_signal(
            {"c1": {"status": "UNRESOLVED"}},
            remaining_patch_attempts=0,
        )
        self.assertFalse(signal["may_continue"])
        self.assertEqual(signal["stop_reason"], "PATCH_ATTEMPTS_EXHAUSTED")

    def test_empty_coverage_is_not_complete(self) -> None:
        signal = goal_completion_signal({})
        self.assertFalse(signal["complete"])
        self.assertEqual(signal["incomplete_reasons"], ["CRITERIA_UNAVAILABLE"])
        # Nothing proves a stop either; budgets/grant machinery still decides.
        self.assertTrue(signal["may_continue"])


if __name__ == "__main__":
    unittest.main()
