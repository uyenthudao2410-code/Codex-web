from __future__ import annotations

"""W4 wiring between the continuation driver and the ported CoS contracts.

This mixin owns the two seams the W4 logic port (see
``continuation_send_state``) left open:

- when a continuation dispatch outcome is unknown, persist the durable
  ``possibly_sent`` send checkpoint on the RUN's handoff capsule so a later
  resume reconciles instead of replaying;
- when the driver is about to dispatch another turn for a Goal-episode
  child RUN, consume the deterministic Goal completion signal as a
  continue/stop input.

Both seams are projections/inputs only: they grant no authority, dispatch
nothing themselves, and never raise into the driver's fail-closed paths.
The driver class inherits this mixin; EOCL/grant machinery keeps every
dispatch decision.
"""

from typing import Any

from .continuation_send_state import (
    SEND_STATE_POSSIBLY_SENT,
    goal_completion_signal,
    send_state_order,
)
from .goal_continuation_ledger import GOAL_CONTINUATION_NO_PROGRESS


class ContinuationWiringMixin:
    def _run_continuation_record_dispatch_unknown_checkpoint(
        self,
        *,
        run_id: str,
        action_id: str,
        reason: str,
    ) -> bool:
        """Persist a ``possibly_sent`` send checkpoint on the RUN's handoff capsule.

        CoS rule ported in ``continuation_send_state``: when a continuation
        dispatch outcome is unknown, the carried prompt/effect may already
        have landed, so the next conversation must reconcile before any
        replay. The checkpoint is written through the existing capsule store
        (the same record path the coordination handoff uses), preserving the
        previous capsule payload. It is monotonic -- an existing checkpoint
        at ``possibly_sent`` or beyond is never rewritten -- and it is a
        best-effort safety projection: it grants no authority and never
        raises, so a failed write cannot change the driver's fail-closed
        outcome.
        """
        try:
            ledger = self.orchestration_ledger
            existing = ledger.latest_handoff_capsule(run_id=run_id)
            payload: dict[str, Any] = {}
            wave_id = ""
            epoch = 1
            if isinstance(existing, dict):
                wave_id = str(existing.get("wave_id") or "")
                try:
                    epoch = max(1, int(existing.get("conversation_epoch") or 1))
                except (TypeError, ValueError):
                    epoch = 1
                previous = existing.get("payload")
                if isinstance(previous, dict):
                    payload = dict(previous)
                    previous_checkpoint = payload.get("send_checkpoint")
                    if isinstance(previous_checkpoint, dict):
                        try:
                            if send_state_order(
                                previous_checkpoint.get("state")
                            ) >= send_state_order(SEND_STATE_POSSIBLY_SENT):
                                return False
                        except ValueError:
                            pass
            marker = {
                "action_id": str(action_id or "")[:256],
                "reason": str(reason or "")[:256],
            }
            payload["send_checkpoint"] = {"state": SEND_STATE_POSSIBLY_SENT, "message_id": ""}
            payload["continuation_dispatch_unknown"] = marker
            try:
                ledger.record_handoff_capsule(
                    run_id=run_id,
                    wave_id=wave_id,
                    conversation_epoch=epoch,
                    payload=payload,
                )
            except ValueError:
                # Augmenting the previous capsule would exceed the capsule
                # size bound; store a minimal capsule carrying only the
                # checkpoint contract so the resume directive still lands.
                ledger.record_handoff_capsule(
                    run_id=run_id,
                    wave_id=wave_id,
                    conversation_epoch=epoch,
                    payload={
                        "send_checkpoint": {"state": SEND_STATE_POSSIBLY_SENT, "message_id": ""},
                        "continuation_dispatch_unknown": marker,
                    },
                )
            return True
        except Exception:
            return False

    def _run_continuation_episode_goal_signal(
        self,
        record: dict[str, Any],
        *,
        goal_observation: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Deterministic Goal signal for one episode-child continuation RUN.

        Returns ``None`` for non-episode RUNs. Coverage comes from the exact
        live Goal projection (``goal_pursuit_live_summary`` ->
        ``completion.criterion_signal``, itself ``goal_completion_signal``
        over the criterion coverage map goal_pursuit builds); the episode
        budgets come from the parent ``goal_continuations`` row, whose
        remaining turns/attempts are decremented authoritatively by the
        ledger. The signal is only an input to the driver's continue/stop
        decision -- it dispatches nothing and grants nothing; EOCL/grant
        machinery keeps every dispatch decision.
        """
        episode_id = str(record.get("parent_episode_id") or "")
        if not episode_id:
            return None
        try:
            parent = self.orchestration_ledger._goal_continuation_get_raw(episode_id)
        except Exception:
            parent = None
        if not isinstance(parent, dict):
            return None
        policy = parent.get("policy") if isinstance(parent.get("policy"), dict) else {}
        no_progress_count = parent.get("no_progress_count")
        if isinstance(goal_observation, dict) and goal_observation.get("no_progress_count") is not None:
            no_progress_count = goal_observation.get("no_progress_count")
        criterion_signal: dict[str, Any] | None = None
        try:
            summary = self.orchestration_ledger.goal_pursuit_live_summary(
                run_id=str(record.get("run_id") or "")
            )
            completion = summary.get("completion") if isinstance(summary, dict) else None
            if isinstance(completion, dict) and isinstance(completion.get("criterion_signal"), dict):
                criterion_signal = completion["criterion_signal"]
        except Exception:
            criterion_signal = None
        coverage: dict[str, Any] | None = None
        if criterion_signal is not None:
            # Rebuild a status-only coverage map from the projection's own
            # signal: unresolved ids keep their exact identity; proven
            # criteria are represented by count, which is all the signal
            # verdict (complete / unresolved / counts) depends on.
            coverage = {}
            for criterion_id in criterion_signal.get("unresolved_criterion_ids") or []:
                coverage[str(criterion_id)] = {"status": "UNRESOLVED"}
            for index in range(max(0, int(criterion_signal.get("criteria_proven") or 0))):
                coverage[f"__proven_{index}"] = {"status": "PROVEN"}
        try:
            max_no_progress = int(policy.get("max_no_progress") or 0)
        except (TypeError, ValueError):
            max_no_progress = 0
        return goal_completion_signal(
            coverage,
            no_progress_count=int(no_progress_count) if no_progress_count is not None else None,
            max_no_progress=max_no_progress or None,
            remaining_decision_turns=int(parent.get("remaining_decision_turns") or 0),
            remaining_patch_attempts=int(parent.get("remaining_patch_attempts") or 0),
        )

    def _run_continuation_episode_stop(
        self,
        record: dict[str, Any],
        *,
        goal_observation: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Stop decision when the Goal signal forbids another dispatch.

        ``complete`` -> no further dispatch for this episode. A hard stop
        (no-progress ceiling or exhausted episode budgets) -> stop with the
        signal's exact reason. ``None`` means the signal permits continuing
        and the existing driver flow decides as before.
        """
        signal = self._run_continuation_episode_goal_signal(record, goal_observation=goal_observation)
        if signal is None or bool(signal.get("may_continue")):
            return None
        if bool(signal.get("complete")):
            return {"status": "GOAL_COMPLETE", "reason": "CRITERIA_COMPLETE", "goal_signal": signal}
        reason = str(signal.get("stop_reason") or "")
        if reason == "NO_PROGRESS_LIMIT_REACHED":
            reason = GOAL_CONTINUATION_NO_PROGRESS
        return {
            "status": "PAUSED",
            "reason": reason or "GOAL_CONTINUATION_SIGNAL_STOP",
            "goal_signal": signal,
        }

