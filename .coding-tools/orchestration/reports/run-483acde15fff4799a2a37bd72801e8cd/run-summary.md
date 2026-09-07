# Orchestration Run Summary

- Run: `483acde15fff4799a2a37bd72801e8cd`
- Task: `e379fb34592f4c66bb043b4be8cdeb5e`
- Objective: Adopt the exact 4-file patch produced by the previous wave without modifying it, then prove the maintenance restart contract: a full 16-ID exact_stale_runs reason is preserved, malformed batches fail closed, exact-stale supervisor maintenance uses full_clean_refresh with sourceCheckpoint=null, ordinary restart still requires accepted source-checkpoint authority, and existing exact stale reconciliation guards continue to pass.
- Status: **accepted**
- Started: `2026-09-07T08:08:04.823Z`
- Finished: `2026-09-07T08:12:49.684Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **2**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `678b6efa32014ad795bf3ae66fec081b` | 1 | `run_initial_objective` | `mcp_only` | `24186fefbdbb9c1dca450ae5e96df167be93c87e` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| e94c9e1f27344bc5aad0adac76bd9d47 | 678b6efa32014ad795bf3ae66fec081b | accepted | 24186fefbdbb9c1dca450ae5e96df167be93c87e | a1d8df0df98c5672e67671dfd8ad3bf244fb75cf5656f0673c66052c24e9fc74 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 43186 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `36`
- Chain head: `6495dcedf7bba71796050ebc27848469061d5738deaa9e07b32f14c63869040c`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
