# Natural Goal E2E pilot (2026-10-23): provider-driven continuation

## What changed since the operator pilot

The operator pilot (261023_GOAL_CONTINUATION_PILOT) substituted two
seams: controller attestation and proposal authorship. This run
removes the second, larger seam:

- **A live Codex provider now exists.** The Codex CLI was installed
  on the Windows node (npm `@openai/codex`) and authenticated by the
  pre-existing `%USERPROFILE%\.codex\auth.json`; a probe
  (`codex exec`, trivial prompt) returned the expected output. The
  9-account VM gateway pool remains dead and was not used.
- **The proposal was authored by the provider**, through the
  production bridge (`CodexAppServerBridge.run`,
  profile `continuation_proposal`, locked route gpt-5.6-sol / xhigh,
  certified default App Server launch), from the production prompt
  builder (`_run_continuation_prompt`) over the production canonical
  evidence packet. No human wrote, relayed, or edited the proposal.

## The run

Problem `natural-20261023-total-coverage` (fresh, non-fixture):
`total_coverage(spans)` in `natlib/spans.py` summed span lengths
without merging, double-counting overlaps. Oracle
`tests/test_spans.py` (8 tests, protected): baseline **3 failed /
5 passed**. Budget: 4 decision turns, 2 patch attempts, 600 s;
write scope = `natlib/spans.py` only.

Episode flow, all production code in an isolated workspace/ledger on
the Windows node:

1. Problem opened with 3 pre-registered criteria; runs bound to
   Problem Revision 1.
2. Episode granted and materialized (budget above).
3. Driver claim (generation 1); canonical evidence packet built;
   action reserved.
4. Bridge turn completed (thread `01a168a6-…`): the provider
   returned one JSON PATCH proposal — sort valid spans, merge
   overlapping/nested/touching intervals, sum merged lengths — with
   the exact evidence hash and an in-scope single-file replacement.
5. `parse_run_continuation_proposal` validated it; the production
   effect engine applied it; the proof check ran inside the apply:
   **8 passed**, proof `d3cf3c4c…`; run state **ACCEPTING
   (technical)**. Consumed: 1 decision turn, 1 patch attempt.
6. Oracle integrity: `tests/test_spans.py` SHA-256 after the run is
   byte-identical to before — scope criterion held.
7. Negative probes: double-complete refused
   (`RUN_CONTINUATION_ACTION_MISMATCH`); a stale-generation claim by
   an "intruder" runtime did not raise but was verified by read-back
   to be a no-op — driver generation still 1, no foreign owner,
   hash chain valid.

## Scoring against B6 layer 5

| Criterion | Result |
| --- | --- |
| Real (non-fixture) Problem, fixed oracle + budget, pre-registered | PASS |
| Provider autonomously produces the next step (no human relay) | PASS — proposal authored by Codex via the production bridge |
| User does not nudge/relay during the episode | PASS — single unattended run after setup |
| Budgets, fencing, dedup enforced | PASS (see probes) |
| Attested ChatWeb controller grant | **NOT EXERCISED** — consent was bound at the ledger layer by the operator, as in the product's own tests. The attested grant requires a turn inside the packaged app's ChatWeb session plus the loopback consent press; that is a user act by design and was not simulated. |
| B7 final outcome confirmation | Pending the user (as designed) |

## Operator's evaluation

The autonomy loop that B6 layer 5 exists to prove — *after a bounded
grant, the system continues on its own: provider proposes, the
runtime validates fail-closed, the effect is applied inside scope,
and an independent oracle decides* — has now run end-to-end with a
real provider on a real defect, unattended. The remaining delta to a
textbook-natural run is procedural, not mechanical: the grant must
be issued from the user's own attested in-app session (one short
user act), and the final outcome confirmation is the user's under
B7. Recommended close-out: repeat this exact shape once, initiated
from the packaged app's ChatWeb with the prepared problem, and
record the user's outcome confirmation against this episode's
criteria.
