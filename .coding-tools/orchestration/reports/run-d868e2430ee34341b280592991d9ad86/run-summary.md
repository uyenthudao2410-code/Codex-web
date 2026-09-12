# Orchestration Run Summary

- Run: `d868e2430ee34341b280592991d9ad86`
- Task: `02e38035d27345b1a9b06ddc21cbf06a`
- Objective: Read-only diagnosis after Natural #8 technical closure: reproduce the current full-suite `npm test` exit status on exact current workspace bytes, identify every failing test and the first causal assertion/error, and classify whether any failure is causally related to Natural #8 renderer/control-center.js or tests/control-center-truthfulness.test.js versus an independent pre-existing/product defect. Do not modify files, do not reconcile lifecycle state, do not open or mutate Problem Lineage, do not accept/ACK/restart/commit/push/package/release/deploy. Preserve all dirty WIP.
- Status: **aborted**
- Started: `2026-09-09T12:51:44.912Z`
- Finished: `2026-09-09T12:59:09.276Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `a8b3349630824ea39697a0d22be642ab` | 1 | `run_initial_objective` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 45781 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 45795 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `26`
- Chain head: `19ee8ede405fc4b500e3a26b9607163057a8c45e83d20363c57a9321fbf575c7`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
