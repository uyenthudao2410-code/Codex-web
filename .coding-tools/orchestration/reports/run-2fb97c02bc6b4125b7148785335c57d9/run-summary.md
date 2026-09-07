# Orchestration Run Summary

- Run: `2fb97c02bc6b4125b7148785335c57d9`
- Task: `efefcb46c67a4f5392114d1983790b18`
- Objective: Fix controlled supervisor restart propagation so allow_acceptance_pending survives from task_control restart_runtime into the durable restart ticket and then into FullCleanActivation. Preserve authorized-child exact-stale target_workspace behavior and all unrelated PRL/dashboard WIP. Add focused regression proof; do not run a runtime restart in this engineering wave.
- Status: **active**
- Started: `2026-09-07T11:04:24.577Z`
- Finished: `None`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `45a1d77efc014ce0b613043597f69d50` | 1 | `run_initial_objective` | `mcp_only` | `58dfd3093d7a05f6999fe93e15c94050aa51d204` | active |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 43544 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `26`
- Chain head: `f49dfe3db9bfaffb7b1d8a515923ef357bbf77fee9652ab5aadd683ef2b62777`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
