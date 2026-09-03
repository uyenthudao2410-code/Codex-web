# Orchestration Run Summary

- Run: `1d885be697f84a98bafc407a92ce8bee`
- Task: `56499b50b3694ab58cffa877268ced58`
- Objective: W2 repair after the no-mutation broad-suite failure. Implement exact cross-wave idempotency for ChatWeb controller usage within one RUN. Controller economic usage_id must be derived from RUN + turn_id, independent of wave_id, while controller delegation_id remains wave-bound attribution. The ledger must treat wave_id/delegation_id as non-economic attribution only when comparing duplicate controller events, preserving the first stored attribution event. Same exact controller receipt replayed in a later wave must deduplicate; changed economic evidence for the same RUN+turn must fail closed. Generic/provider build_usage_event identity and provider dedupe semantics must remain unchanged. Add a focused unit oracle covering cross-wave controller duplicate, first-attribution preservation, conflict rejection, and provider wave-bound identity. Preserve unknown_not_zero and unrelated dirty work. No commit/push/restart/package/release/deploy.
- Status: **aborted**
- Started: `2026-08-31T19:01:32.751Z`
- Finished: `2026-08-31T19:01:58.733Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **0**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **0**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `d14b4b38fbab4c969cac9ec3527a7ffe` | 1 | `run_initial_objective` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `4`
- Chain head: `96d5cf59d4464d0565e5ed646bb28ac12cfff9a7e527e67aa0cf23b39c9c46e0`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
