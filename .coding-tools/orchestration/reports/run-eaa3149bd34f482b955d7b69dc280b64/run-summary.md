# Orchestration Run Summary

- Run: `eaa3149bd34f482b955d7b69dc280b64`
- Task: `099228ac95524503b7a7abfa1b2e34f3`
- Objective: Fix only the stale-health test fixture: task_control recovery snapshot uses action=get, not the nonexistent action=status. Do not change production source.
- Status: **accepted**
- Started: `2026-08-15T02:54:39.009Z`
- Finished: `2026-08-15T02:55:39.941Z`

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
| 1 | `95cf7e31d7e442cd88267d4e4377216d` | `mcp_only` | `dff81e251836666fc825c40bf86e4167afd29c39` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 6ac654832e764982b474de1b129adca9 | 95cf7e31d7e442cd88267d4e4377216d | accepted | dff81e251836666fc825c40bf86e4167afd29c39 | 25d6ca30b6eb6b18c73a3aa5b0a6ad279a7bbb09d8a041d5d970efeda1f21357 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 3947 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `13`
- Chain head: `2b0929618c5ca141bd3e6f3fa4714a470d1d9f07c3aa611387c86cd6465eb33b`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
