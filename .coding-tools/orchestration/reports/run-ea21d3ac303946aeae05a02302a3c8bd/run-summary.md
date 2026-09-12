# Orchestration Run Summary

- Run: `ea21d3ac303946aeae05a02302a3c8bd`
- Task: `bb815d5a6f35496eb456f49748271f31`
- Objective: G6 operational continuity closure verification for Problem prl-b1fed3cdfd5203d9d9202643265865c3 revision 1. Make no source changes. Verify the current durable evidence for G6-C1 through G6-C8, and verify G6-C9 as the preserved two-plane rule: technical acceptance may only create PROVISIONALLY_RESOLVED while independent explicit user outcome remains absent and unclaimed. Use exact identities, bounded content-free continuity evidence, and current authoritative reporters/tests. Do not rewrite historical runs, do not recover by recency, do not mutate ledger manually, and do not restart/commit/push/release/deploy.
- Status: **aborted**
- Started: `2026-09-10T11:47:10.377Z`
- Finished: `2026-09-10T11:59:06.871Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **2**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `30c231c30ebd4c20a8f768f6f453bc20` | 1 | `run_initial_objective` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | replanned |
| 2 | `b4abdd6bfb8849348f6ca72d777725a5` | 2 | `replan_request` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 47760 | `deterministic` | `deterministic` | explicit_request |
| 47781 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 47774 | `CHECK_FAILED` | `PROVING` |  |
| 47795 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `46`
- Chain head: `7c023027181ff48701bfde9317c5bbc902872616eafc6fb0cef066d58c1e5473`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
