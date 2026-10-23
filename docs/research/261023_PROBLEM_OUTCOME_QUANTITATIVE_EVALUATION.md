# Problem → Outcome: quantitative evaluation (2026-10-23)

## Mandate, method, and honesty bounds

At the user's direction, the shipped measurement instruments were run
against a read-only snapshot of the production ledger (Windows
`.coding-tools/orchestration/ledger.sqlite3`, snapshot logical SHA-256
`44c509cd…`, source HEAD at capture `cd52d807`):

- `scripts/report_problem_lineage_canary.py` (PRL v12, codebook 1.0.0,
  cohort rules 2.0.0)
- `scripts/report_natural_problem_cohort.py` (pre-registered cohort:
  fixed start at the canary problem rev 1, next 10 problem revisions
  in creation order, no success/terminal filtering)
- `scripts/report_accepted_result_economics.py`

The instruments' own policy is binding on this evaluation: with the
available sample sizes, results are **descriptive mechanics only** —
no causal efficacy claim is made or permitted (`causal_claim_allowed:
false` in the cohort decision).

## Measured results

### Ledger integrity and structural mechanics (canary report)

| Metric | Value | Wilson 95% |
| --- | --- | --- |
| Ledger integrity (sqlite + FK + chain + projections) | all checks pass | — |
| Exact-revision binding (runs bound to the exact Problem Revision) | 193/211 = 91.5% | [0.354, 1.0] as computed by the instrument on its attested subset |
| Criterion → proof structural coverage | 34/34 = 100% | [0.653, 1.0] |
| Attested occurrence clock coverage | 34/34 = 100% | [0.653, 1.0] |
| Authoritative outcome confirmation | 3/3 = 100% of confirmations carry a valid authority (RUNTIME_EXPLICIT_USER / OUTCOME_RECEIPT / HUMAN_REVIEW) | [0.233, 1.0] |
| Ambiguous or unlinked problem events | 18 of 307 action-kind events | — |

Canary status remains `C4_SOURCE_READY_AWAITING_NATURAL_CANARY`:
307 policy-schema events exist, but the ledger does not classify
records as natural, and the report — by design — does not fabricate
that classification.

### Pre-registered natural cohort (n = 10 problem revisions)

- Typed-natural eligibility: **3/10 rows** fully eligible
  (`prl-6fc8d557…`, `prl-b0d0182a…`, `prl-3b6e6469…`). The other 7 rows
  fail on one repeated reason: `typed_representative_natural_
  provenance_missing` on their primary runs — the runs happened, the
  typed provenance marker did not get recorded.
- Cohort decision at n=10 (the instrument's own gate):
  **REJECT_NONCONSECUTIVE_OR_UNVERIFIED_NATURAL_COHORT** — the cohort
  cannot support an effectiveness conclusion in its current state.
- False closures: **0**. Reopens: **0**.
- User correction turns: 0 in 8/10 rows; 1 each in rev 2 and rev 3 of
  `prl-151d9ff308…` — the cohort's only multi-revision problem and its
  only measurable rework case (3 revisions).
- Time-to-proof where observed: 5.3 s – 38.6 s (proof stage only, not
  end-to-end resolution time).

### Accepted-result economics (286 accepted deterministic runs)

- Performance-metric coverage is thin: 76/286 runs (26.6%) carry the
  full performance vector; controller token/cost coverage is **0%** —
  no monetary or token cost claim is possible, and none is made.
- Proof-cache economics: 1,017 eligible proof opportunities, **6 hits
  (0.59%)**, 25.3 s saved in total. Misses are dominated by input
  fingerprint changes (489) and cold starts (522): at the current
  change rate the proof cache is economically negligible.
- Wait-to-execution ratio on accepted runs ≈ 1.33 (first-pass 0.92):
  for every second of local execution, ≈1.3 s elapsed in inter-call
  gaps (controller/model/network/operator time; not proven avoidable).
- Current-source window (HEAD at capture): 0 accepted runs, so the
  DRE mechanism reports `insufficient_head_window_volume` and — by
  design — produces no effect estimate from historical counts.

## Operator's evaluation

1. **What the numbers prove.** The lineage machinery is structurally
   sound: integrity is clean, every acceptance criterion that exists
   is structurally bound to proof (34/34), every recorded outcome
   confirmation is authoritative (3/3), there are no false closures
   and no reopens in the cohort, and exact-revision binding is high
   (91.5%). As a *record-keeping and fencing* system, Problem→Outcome
   works and is now measured, not asserted.
2. **What the numbers do not prove.** Effectiveness. The decisive
   sample — natural problems with complete typed evidence — is 3,
   not the 5–10 the plan requires even for descriptive calibration,
   and the cohort gate formally rejects an efficacy conclusion. The
   binding constraint is not problem volume (49 problem-identity
   units, 211 bound runs) but **provenance capture**: 7 of 10 cohort
   rows lost eligibility because their runs lack the typed natural
   provenance marker.
3. **The cheapest high-leverage fix is therefore identified, not
   speculative:** make the runtime stamp typed representative-natural
   provenance by default on organically created runs (the 3 eligible
   rows carry `runtime_default_organic_v1`; the ineligible ones carry
   none). One instrumentation change converts future real work into
   measurable cohort rows automatically; without it, every future
   evaluation re-runs into the same wall.
4. **Secondary findings.** The proof cache's 0.59% hit rate does not
   justify cache-architecture work (the economics report's own policy
   agrees). Cost evaluation is impossible until provider usage is
   recorded (0% coverage) — if monetary evaluation is ever wanted,
   that recording is the prerequisite, not analysis.
5. **Standing conclusion.** Problem→Outcome effectiveness remains
   **unproven — now with the blocker quantified** (3/10 eligible,
   gate: REJECT_NONCONSECUTIVE_OR_UNVERIFIED_NATURAL_COHORT). The
   next measurement should be taken after (a) the provenance-stamping
   change has been live for a window of real work, and (b) the
   natural continuation pilot (B6 layer 5) has run, since continuation
   episodes are the strongest future source of fully-typed rows.
