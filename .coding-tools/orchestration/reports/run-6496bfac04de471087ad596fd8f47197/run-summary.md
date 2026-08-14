# Orchestration Run Summary

- Run: `6496bfac04de471087ad596fd8f47197`
- Task: `9596b556bb9b4e00a14066e1e7167d48`
- Objective: P1 live proof-cache negative-control after a controlled relevant source-tree change. Use the exact same oracle command/workdir/config as the baseline and exact-repeat runs, with a new agent_workflow idempotency key. The changed source worktree fingerprint must invalidate the prior proof, so this opportunity must be a cache miss and run the real pytest oracle. Do not make additional source changes.
- Status: **accepted**
- Started: `2026-08-14T00:19:30.479Z`
- Finished: `2026-08-14T00:19:51.785Z`

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
| 1 | `ae7c874139cf48b29567b754e5e7e4cf` | `mcp_only` | `29a1318bf09f893aca0fbc2c13de3429d9b2fdb9` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| b8b581f375bb4ec49c101fe282d85a7a | ae7c874139cf48b29567b754e5e7e4cf | accepted | 29a1318bf09f893aca0fbc2c13de3429d9b2fdb9 | bfe50c3bcee8fdaabb6cc40352bf14e3c05e2238f3c54d9a191d5c247e1fc8d8 | ChatWeb Sol |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 645 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `14`
- Chain head: `cb620d60ac7c30bf7a63b68ecdd7ea7242e0dd79c0a26a238ff2e0ae719496cd`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
