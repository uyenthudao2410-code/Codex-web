# Orchestration Run Summary

- Run: `da50df5e1b01454db64505659073e0f0`
- Task: `b206dc2db69d44599ff8de04455d459f`
- Objective: P2A lifecycle reconciliation: make OrchestrationLedger.reconcile_stale_runs preserve live ownership and repair parent/child terminal consistency. A non-expired controller lease must protect an active run from stale reconciliation. When a run becomes stale, every active child wave must become aborted with finished_at and a bounded lifecycle-reconcile event. Also repair pre-existing terminal parents with lingering active child waves idempotently: accepted->accepted/CHECKPOINTED, blocked->blocked/BLOCKED, stale|aborted->aborted/ABORTED. Preserve all evidence, return contract (only newly stale run ids), integrity chain, and live background/lane/write-fence protection. Add focused tests for child terminalization, controller protection, historical terminal-parent repair, and idempotency. No TaskState projection change in this wave.
- Status: **accepted**
- Started: `2026-08-14T18:03:42.278Z`
- Finished: `2026-08-14T18:03:57.020Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `d4f717a776ec45a6bdc39841ecbbca47` | `mcp_only` | `5decaa48300b10a6df39676c677745bc881cd7d9` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 278aed550e0948a8962417d318f8a536 | d4f717a776ec45a6bdc39841ecbbca47 | accepted | 5decaa48300b10a6df39676c677745bc881cd7d9 | b31005bca9d6425970fd7a64931b9e82ce3d0a0bdef46de4f8cfde79f51ebdf5 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 3224 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `13`
- Chain head: `8607226011bd96e51f42a6646bdd118e0bcb1d961d0da7007c39762c7811eb0d`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
