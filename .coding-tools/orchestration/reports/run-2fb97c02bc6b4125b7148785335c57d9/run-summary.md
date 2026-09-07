# Orchestration Run Summary

- Run: `2fb97c02bc6b4125b7148785335c57d9`
- Task: `efefcb46c67a4f5392114d1983790b18`
- Objective: Fix controlled supervisor restart propagation so allow_acceptance_pending survives from task_control restart_runtime into the durable restart ticket and then into FullCleanActivation. Preserve authorized-child exact-stale target_workspace behavior and all unrelated PRL/dashboard WIP. Add focused regression proof; do not run a runtime restart in this engineering wave.
- Status: **accepted**
- Started: `2026-09-07T11:04:24.577Z`
- Finished: `2026-09-07T11:34:14.839Z`

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
| 1 | `45a1d77efc014ce0b613043597f69d50` | 1 | `run_initial_objective` | `mcp_only` | `58dfd3093d7a05f6999fe93e15c94050aa51d204` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 42a72abf64d1427092677f97e2f32e32 | 45a1d77efc014ce0b613043597f69d50 | accepted | d02c6e2ef1506a25819dd65ec7811c4ac7c01edc | 5c81ceeb55ca000d7e27e978654893198f84167f0c8ee3d9420b851f7c521b20 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 43544 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `33`
- Chain head: `044917707d683af02abb8466dfb883c78396d60de73a06ab53e84907a3702e25`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
