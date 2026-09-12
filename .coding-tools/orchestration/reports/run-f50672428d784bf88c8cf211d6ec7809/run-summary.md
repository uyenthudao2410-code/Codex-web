# Orchestration Run Summary

- Run: `f50672428d784bf88c8cf211d6ec7809`
- Task: `d75cd356316340798a6afeef5a9a398f`
- Objective: Make exact stale-run maintenance restart use checkpoint-free full_clean_refresh while preserving ordinary restart accepted-checkpoint authority; preserve all exact stale IDs up to the existing 16-ID bound instead of truncating the maintenance reason; validate maintenance reason structure before any mutation; add regressions proving 16 IDs survive and maintenance refresh does not require source-checkpoint authority.
- Status: **aborted**
- Started: `2026-09-07T08:03:51.764Z`
- Finished: `2026-09-09T10:48:10.346Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **1**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `35334d87bb4147d9a9b44aa76085f6a4` | 1 | `run_initial_objective` | `mcp_only` | `24186fefbdbb9c1dca450ae5e96df167be93c87e` | replanned |
| 2 | `e27372ed7e2f4c238aab003a9219dadb` | 2 | `replan_request` | `mcp_only` | `24186fefbdbb9c1dca450ae5e96df167be93c87e` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 43154 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 43171 | `PERMISSION_REQUIRED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `34`
- Chain head: `4441be1f9537d31de3bcbff08905974c894ceb0eaa816514d460942476c651e2`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
