# Orchestration Run Summary

- Run: `8c5d64ae9e6a4f8b903b1a61b4d90954`
- Task: `389de5b5d3e1466c9efe753172c43f32`
- Objective: Natural #3: implement a compact empirical read-only reporter for the natural-problem cohort and accepted-result economics. Determine the safest existing immutable/read-only access path first. The reporter must expose cohort/status counts, timing/economics only when observed, explicit UNKNOWN/missing-evidence reasons, P4 blockers/readiness, and P5 eligibility; it must not initialize a writer ledger, mutate canonical .coding-tools state, reconcile stale RUNs, reopen P5, or touch unrelated dirty files. Add focused mock/temp tests and a live read-only oracle from workspace root.
- Status: **accepted**
- Started: `2026-09-09T08:27:19.892Z`
- Finished: `2026-09-09T09:13:38.607Z`

## Outcome metrics

- Waves: **3**
- Route decisions: **3**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **5**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `aa4b76fa4d06410fb4a594f97965a868` | 1 | `run_initial_objective` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | replanned |
| 2 | `c61ee569058c45ab87af20ec77e64d22` | 2 | `replan_request` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | replanned |
| 3 | `d9e7cc9ae12445abb7fc858ee8bb4c2e` | 3 | `replan_request` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| cee5cb07551f441f98a1a1131a15414c | d9e7cc9ae12445abb7fc858ee8bb4c2e | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | 1b32b6d4b54412fcc38e72aca4b01c0cb54609ea5559c7458e1155f4d2f9e230 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 45303 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 45327 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 45362 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 45318 | `CHECK_FAILED` | `PROVING` |  |
| 45353 | `SOL_REJECTED` | `ACCEPTING` | Final acceptance is blocked by ACCEPTANCE_FILE_ATTESTATION_REQUIRED because wave 2 contains two current files plus two deleted wave-1 cleanup paths. The deleted paths cannot be exact-byte attested through the current acceptance_files contract. Replan in the same RUN to an adoption-only wave over the two surviving authoritative files, with no source-byte mutation, then rerun the same live reporter and focused tests. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `118`
- Chain head: `565a2914c7f3694fe267b9a07f1bfaef9e709c2d42affc2a22fb5ac93e91a398`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
