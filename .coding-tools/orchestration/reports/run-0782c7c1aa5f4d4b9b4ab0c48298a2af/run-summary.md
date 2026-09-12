# Orchestration Run Summary

- Run: `0782c7c1aa5f4d4b9b4ab0c48298a2af`
- Task: `aecb3c0b841c458f850e3aa389792dbf`
- Objective: Natural #15: add phase-aware P2 accepted-run timing metrics without changing total TTA or EOCL timing semantics. Aggregate durable phase_timing into engineering-active and acceptance-wait measurements, stratified by first-pass vs repaired, preserving unknown when phase timing is incomplete. Add focused regression including a first-pass accepted run dominated by ACCEPTING wait.
- Status: **accepted**
- Started: `2026-09-10T05:20:26.750Z`
- Finished: `2026-09-10T05:53:43.714Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **6**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `8bbe2ddcbf4144d88ba55af33fdf4826` | 1 | `run_initial_objective` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | replanned |
| 2 | `be83285c600a4b9dae746b12ab072906` | 1 | `replan_request` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| fc8f4b3a6aa64340846915ce7735e77c | be83285c600a4b9dae746b12ab072906 | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | 809ec8fc70c9ea998518c3430ff1457979ccec198aae41a731ba38bb83f9759a | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 46643 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 46673 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 46658 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `113`
- Chain head: `ae4879d61ae7e90a326f395c7b00c0afb492fac98b7cf8be046beee20050e2e2`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
