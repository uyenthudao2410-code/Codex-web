# Orchestration Run Summary

- Run: `77e88839ea464139b8f9ba0fb9e935ad`
- Task: `8220f02e5228498ca1a8244fa5e7134b`
- Objective: Post-restart exact-ID preflight for the three scoped unresolved stale orchestration RUNs after controlled restart, and separately inspect the previously below-threshold candidate without folding it into the original three. Read-only only: do not reconcile, mutate source, restart runtime, commit, push, clean, reset, or alter unrelated lifecycle state.
- Status: **accepted**
- Started: `2026-09-12T08:30:37.394Z`
- Finished: `2026-09-12T08:34:17.282Z`

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
| 1 | `8430a04a114a414db42edfbe5c98d049` | 1 | `run_initial_objective` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | replanned |
| 2 | `6d93496515bd465aaa9ce096cd5d432a` | 2 | `replan_request` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | replanned |
| 3 | `4bc295a2ba5d445a86f884c5157b09a0` | 3 | `replan_request` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 63d5d2631e5542b1a213853283ee48bd | 4bc295a2ba5d445a86f884c5157b09a0 | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | dc0c3b65abd79d4e7659da7c019c17d7c817f979f5bcd2883b11fc624167f81a | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 50759 | `deterministic` | `deterministic` | explicit_request |
| 50804 | `deterministic` | `deterministic` | explicit_request |
| 50820 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 50788 | `CHECK_FAILED` | `PROVING` |  |
| 50810 | `INVALID_ARGUMENT` | `EXECUTING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `92`
- Chain head: `1fc88744c4db21f14c20a075ae02c7009b58a10fa4dc1783a7fce444f6263563`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
