# Orchestration Run Summary

- Run: `8cfd89b66cd24295bdad2a08fb2327f8`
- Task: `8e2b8b797d3e4c92a3378979be057f17`
- Objective: Fix MCP-2026 exact-run continuation so task_control(action=stop, run_id=...) recovers the durable stateless task context instead of minting a new context. Correct the regression to assert the explicit-run stop receipt contract: top-level stopped/target_run_id/detached/orchestration state, while preserving task-level state.
- Status: **accepted**
- Started: `2026-08-26T07:34:24.292Z`
- Finished: `2026-08-26T07:37:57.424Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `debb483b02774c319dc8e1a788ef8d10` | 1 | `run_initial_objective` | `mcp_only` | `52faa0e9cfacf582fcf5bc6f40ed230cea7602e9` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| e513d927cde245aa9443d23cceb49664 | debb483b02774c319dc8e1a788ef8d10 | accepted | 52faa0e9cfacf582fcf5bc6f40ed230cea7602e9 | 70dd970f9a7e455ae75391254c41976b17b76e5a9e2b2039e2f70b5f76b23962 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 30360 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `28`
- Chain head: `3f54e9acca444281d5de3bdec8777636f48070e9a69e1a2de8812b6f5c33de2f`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
