# Goal continuation pilot — operator-run, fresh problem (2026-10-23)

## Mandate and method

At the user's direction ("pick a problem yourself, run it, judge it"),
the operator authored a fresh, non-fixture problem and drove the
shipped goal-continuation machinery over it end to end in an isolated
workspace (`pilot-20261023/ws`), judging the result against criteria
registered in the Problem capsule **before** execution.

**Problem** `pilot-20261023-merge-intervals` rev 1: `merge_intervals`
in `pilotlib/ranges.py` violates its documented contract — touching
intervals ([1,2],[2,3]) must merge. Pre-registered oracle:
`tests/test_ranges.py`, 9 tests. Baseline before the pilot:
**3 failed, 6 passed** (exactly the touching cases).

**Budget granted**: 4 decision turns, 2 patch attempts, 600 s; write
scope `pilotlib/ranges.py` only; oracle file protected.

## What ran (all production code paths)

1. Problem opened in a fresh ledger (capsule, contract fingerprint
   `c4ce4b9a…`), origin RUN + link event recorded.
2. Goal continuation policy built, consent bound to the exact scope
   descriptor, episode issued and materialized onto the child RUN
   (status GRANTED; shared budget 4 turns / 2 patches).
3. Driver claim taken (generation 1); evidence packet assembled by the
   runtime and hashed (`5921724e…`); proposal action reserved and
   dispatched.
4. PATCH proposal validated by `parse_run_continuation_proposal`
   (exact preimage, scope, check-hash binding) and applied by
   `_run_continuation_apply_patch`: one replacement
   (`if start < last[1]:` → `if start <= last[1]:`), effect journaled
   with pre/post SHA-256 and a materialized backup
   (status **applied**).
5. The same production call ran the approved check through the proof
   engine: pytest **passed** (exit 0; independently re-run by the
   operator: 9 passed). Run state: **ACCEPTING** (technical), with the
   design's `FINAL_ACCEPTANCE_REQUIRED` gate left for the user.
6. Budget accounting: 1/4 turns and 1/2 patch attempts consumed;
   parent episode mirrors the child exactly.
7. Negative probes: a stale-generation claim from a foreign runtime
   instance did **not** take ownership; completing the same action
   twice was refused (`RUN_CONTINUATION_ACTION_MISMATCH`); the run's
   hash chain verifies (`verify_chain ok`).

## Seams that were substituted — stated plainly

- **Controller attestation**: at the ledger layer the controller
  precondition was satisfied by operator assertion (the same seam the
  product's own test-suite uses). No attested ChatWeb transport was
  involved.
- **Proposal transport**: proposals were authored by the operator and
  injected where the bridge would deliver them. A live provider seam
  is currently impossible, verified on both machines on 2026-10-23:
  the VM gateway is down with no Codex auth present, and the Windows
  machine has no discoverable Codex binary. The continuation profile
  additionally requires the certified default App Server launch
  (`require_default_argv`), so no compliant substitute exists.

## Verdict

- Criteria c1 (oracle), c2 (scope — exactly one file in the effect
  manifest, oracle untouched), c3 (contract/signature unchanged):
  **all met**, on evidence produced by the machinery itself.
- B6 layer 4 (detached continuation mechanics): demonstrated on a
  fresh problem with a real oracle — grant, consent binding, fencing,
  budgets, journaled effects, proof and technical acceptance all
  behaved as specified.
- B6 layer 5 (natural pilot): **still NOT_RUN**. The remaining gate
  is exactly one environmental asset: a working Codex provider
  session on one machine (install/sign-in), after which the same
  pilot shape runs unattended. Final outcome confirmation for this
  pilot's Problem also remains the user's explicit act, per B7.
