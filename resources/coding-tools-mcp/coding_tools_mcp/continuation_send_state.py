from __future__ import annotations

"""Four-position send/effect checkpoint for continuation handoffs.

Concept ported from Chat On Steroids (MIT), ``src/main/session/continuation.ts``
(``ContinuationSendState`` / ``ContinuationSendCheckpoint`` / ``sendUnattempted``):
one prompt or effect carried by a session handoff occupies exactly one of four
durable positions, in order:

===================  =======================  ================================
canonical            CoS wire name            meaning
===================  =======================  ================================
``not_attempted``    ``not-attempted``        nothing was started
``started_unknown``  ``attempted-unresolved`` attempt began, but the checkpoint
                                              is written *before* dispatch, so
                                              it proves nothing was sent yet
``possibly_sent``    ``dispatched-unresolved`` dispatch was armed/performed and
                                              the outcome is unknown; the effect
                                              may or may not have landed
``confirmed``        ``sent``                 server-authored evidence confirms
                                              the effect landed
===================  =======================  ================================

The rule that makes the taxonomy useful, copied from CoS: only the first two
positions may be replayed (both are provably pre-dispatch). ``possibly_sent``
is *never* replayed -- it must be reconciled against the destination first.
``confirmed`` is terminal.

This module is a leaf: it owns the vocabulary, the monotonic transition rule,
checkpoint normalization, the resume directive a handoff reader must follow,
and a deterministic Goal completion signal (the non-model analogue of the CoS
Goal judge). It grants no authority and dispatches nothing; EOCL/grant checks
remain with the existing continuation and Goal machinery.
"""

from typing import Any

SEND_STATE_NOT_ATTEMPTED = "not_attempted"
SEND_STATE_STARTED_UNKNOWN = "started_unknown"
SEND_STATE_POSSIBLY_SENT = "possibly_sent"
SEND_STATE_CONFIRMED = "confirmed"

SEND_STATES: tuple[str, ...] = (
    SEND_STATE_NOT_ATTEMPTED,
    SEND_STATE_STARTED_UNKNOWN,
    SEND_STATE_POSSIBLY_SENT,
    SEND_STATE_CONFIRMED,
)

_SEND_STATE_ORDER = {state: index for index, state in enumerate(SEND_STATES)}

# Canonical names plus the exact CoS wire spellings, so a checkpoint authored
# by either vocabulary normalizes to the canonical form above.
_SEND_STATE_ALIASES = {
    "not_attempted": SEND_STATE_NOT_ATTEMPTED,
    "not-attempted": SEND_STATE_NOT_ATTEMPTED,
    "started_unknown": SEND_STATE_STARTED_UNKNOWN,
    "attempted-unresolved": SEND_STATE_STARTED_UNKNOWN,
    "attempted_unresolved": SEND_STATE_STARTED_UNKNOWN,
    "possibly_sent": SEND_STATE_POSSIBLY_SENT,
    "dispatched-unresolved": SEND_STATE_POSSIBLY_SENT,
    "dispatched_unresolved": SEND_STATE_POSSIBLY_SENT,
    "confirmed": SEND_STATE_CONFIRMED,
    "sent": SEND_STATE_CONFIRMED,
}

_REPLAYABLE = frozenset({SEND_STATE_NOT_ATTEMPTED, SEND_STATE_STARTED_UNKNOWN})

_CHECKPOINT_MESSAGE_ID_MAX_CHARS = 256
_SIGNAL_UNRESOLVED_IDS_MAX = 64

# Criterion coverage statuses produced by GoalPursuitLedgerMixin
# ._goal_criterion_coverage that count as satisfied.
_CRITERION_SATISFIED_STATUSES = frozenset({"PROVEN", "SATISFIED_NON_CODE"})


def normalize_send_state(value: Any, *, field: str = "send_state") -> str:
    """Return the canonical send state for a canonical or CoS-spelled name."""
    if isinstance(value, str):
        canonical = _SEND_STATE_ALIASES.get(value.strip().lower())
        if canonical is not None:
            return canonical
    raise ValueError(
        f"{field} must be one of {sorted(_SEND_STATE_ALIASES)}; got {value!r}"
    )


def send_state_order(state: Any) -> int:
    """Position of a send state in the durable order (0..3)."""
    return _SEND_STATE_ORDER[normalize_send_state(state)]


def advance_send_state(current: Any, nxt: Any) -> str:
    """Validate a checkpoint transition and return the new canonical state.

    Transitions are monotonic: re-recording the same state is idempotent,
    moving forward (including skipping, when late confirmation evidence
    arrives) is allowed, and moving backward is rejected -- a checkpoint may
    never rewrite a possibly-sent or confirmed effect into a replayable one.
    """
    current_canonical = normalize_send_state(current, field="current send_state")
    next_canonical = normalize_send_state(nxt, field="next send_state")
    if _SEND_STATE_ORDER[next_canonical] < _SEND_STATE_ORDER[current_canonical]:
        raise ValueError(
            "send_state may not move backward: "
            f"{current_canonical} -> {next_canonical}"
        )
    return next_canonical


def send_may_be_replayed(state: Any) -> bool:
    """True only while the checkpoint proves nothing was dispatched yet."""
    return normalize_send_state(state) in _REPLAYABLE


def send_requires_reconciliation(state: Any) -> bool:
    """True when the effect may have landed and must be reconciled, not replayed."""
    return normalize_send_state(state) == SEND_STATE_POSSIBLY_SENT


def normalize_send_checkpoint(value: Any) -> dict[str, Any]:
    """Normalize a handoff ``send_checkpoint`` payload to its canonical shape.

    Accepts ``message_id`` or the CoS spelling ``messageId``. Unknown keys are
    dropped so the stored capsule carries exactly the durable contract.
    """
    if not isinstance(value, dict):
        raise ValueError("send_checkpoint must be an object with a state")
    state = normalize_send_state(value.get("state"), field="send_checkpoint.state")
    message_id = value.get("message_id", value.get("messageId", ""))
    if message_id is None:
        message_id = ""
    if not isinstance(message_id, str):
        raise ValueError("send_checkpoint.message_id must be a string")
    return {
        "state": state,
        "message_id": message_id.strip()[:_CHECKPOINT_MESSAGE_ID_MAX_CHARS],
    }


def handoff_resume_directive(checkpoint: Any) -> dict[str, Any]:
    """The resume decision a handoff reader must follow for a send checkpoint.

    ``checkpoint`` may be a state name or a checkpoint object. The directive
    never grants send authority by itself; it states whether replaying the
    carried prompt/effect is provably safe, forbidden pending reconciliation,
    or unnecessary because the effect is already confirmed.
    """
    if isinstance(checkpoint, dict):
        state = normalize_send_checkpoint(checkpoint)["state"]
    else:
        state = normalize_send_state(checkpoint)
    if state in _REPLAYABLE:
        directive = "REPLAY_SAFE"
    elif state == SEND_STATE_POSSIBLY_SENT:
        directive = "RECONCILE_BEFORE_REPLAY"
    else:
        directive = "ALREADY_CONFIRMED"
    return {
        "state": state,
        "directive": directive,
        "may_replay": state in _REPLAYABLE,
        "requires_reconciliation": state == SEND_STATE_POSSIBLY_SENT,
    }


def goal_completion_signal(
    coverage: Any,
    *,
    no_progress_count: int | None = None,
    max_no_progress: int | None = None,
    remaining_decision_turns: int | None = None,
    remaining_patch_attempts: int | None = None,
) -> dict[str, Any]:
    """Deterministic Goal completion signal from criterion coverage + budgets.

    This is the non-model analogue of the CoS Goal judge (which asks a model
    whether the whole request is complete and expects NO_REPLY only then):
    here the verdict is derived only from durable facts -- the per-criterion
    coverage map produced by ``_goal_criterion_coverage`` and the Goal
    continuation episode budgets. A Goal is complete only when at least one
    criterion exists and every criterion is PROVEN or SATISFIED_NON_CODE.
    ``may_continue`` reports whether continuation remains legitimate; it does
    not dispatch anything -- EOCL/grant machinery still decides that.
    """
    statuses: dict[str, str] = {}
    if isinstance(coverage, dict):
        for criterion_id, entry in coverage.items():
            if isinstance(entry, dict):
                statuses[str(criterion_id)] = str(entry.get("status") or "UNRESOLVED")
            elif isinstance(entry, str):
                statuses[str(criterion_id)] = entry
    unresolved = sorted(
        criterion_id
        for criterion_id, status in statuses.items()
        if status not in _CRITERION_SATISFIED_STATUSES
    )
    proven = len(statuses) - len(unresolved)
    complete = bool(statuses) and not unresolved

    reasons: list[str] = []
    if not statuses:
        reasons.append("CRITERIA_UNAVAILABLE")
    elif unresolved:
        reasons.append("UNRESOLVED_CRITERIA")
    if (
        max_no_progress is not None
        and int(max_no_progress) >= 1
        and no_progress_count is not None
        and int(no_progress_count) >= int(max_no_progress)
    ):
        reasons.append("NO_PROGRESS_LIMIT_REACHED")
    if remaining_decision_turns is not None and int(remaining_decision_turns) <= 0:
        reasons.append("DECISION_TURNS_EXHAUSTED")
    if remaining_patch_attempts is not None and int(remaining_patch_attempts) <= 0:
        reasons.append("PATCH_ATTEMPTS_EXHAUSTED")

    hard_stop = next(
        (reason for reason in reasons if reason != "UNRESOLVED_CRITERIA" and reason != "CRITERIA_UNAVAILABLE"),
        "",
    )
    may_continue = not complete and not hard_stop
    return {
        "complete": complete,
        "criteria_total": len(statuses),
        "criteria_proven": proven,
        "criteria_unresolved": len(unresolved),
        "unresolved_criterion_ids": unresolved[:_SIGNAL_UNRESOLVED_IDS_MAX],
        "incomplete_reasons": reasons,
        "may_continue": may_continue,
        "stop_reason": "CRITERIA_COMPLETE" if complete else hard_stop,
        "signal_source": "DETERMINISTIC_CRITERION_COVERAGE",
    }
