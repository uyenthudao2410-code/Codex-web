# Orchestration Run Summary

- Run: `1b2646cf96444590a6e70e138742d97c`
- Task: `bc9d0933084942a9b19febf259aae04d`
- Objective: Fix the Recovery Host restart-ticket consumption bug so an explicit task_control restart_runtime ticket is serviced under an ordinary healthy READY activation epoch as well as a blocked READY-adoption epoch, while still never consuming it during any non-READY activation transaction. Add a focused regression test. Preserve all unrelated dirty work and do not commit/push/release/deploy.
- Status: **accepted**
- Started: `2026-09-07T03:32:43.250Z`
- Finished: `2026-09-07T03:36:02.227Z`

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
| 1 | `1346a2aed12648a2976ed22e8f850163` | 1 | `run_initial_objective` | `mcp_only` | `9255f94c9beff33f8c6c53d6745a08968f5a12bb` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 00ececc1c172430ea5e271fc15ca065c | 1346a2aed12648a2976ed22e8f850163 | accepted | 9255f94c9beff33f8c6c53d6745a08968f5a12bb | d0e1632e7402092b1062ba8fe1a1dd5ae806fd12d2426d78e618da29a9030ecd | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 43086 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `35`
- Chain head: `f28c4e8be6fc351c6d88ad9622ed3a134bcd87f863644f8ed6f92a18403fb7da`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
