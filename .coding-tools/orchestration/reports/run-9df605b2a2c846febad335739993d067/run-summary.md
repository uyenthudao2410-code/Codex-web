# Orchestration Run Summary

- Run: `9df605b2a2c846febad335739993d067`
- Task: `85fe860657fc44888e62b1aedd8de9cb`
- Objective: Fix the live automatic code-activation state-machine loop on E:\DEV\Tools-Codex-web. Current Recovery Host repeatedly logs BASE_HEAD_CHANGED every ~3 seconds after an activation intent captured an older Git HEAD; it never terminalizes/replans, so newer accepted Recovery Host/UI code cannot activate. Preserve fail-closed revision/device/workspace checks and already accepted legacy revision bridge. Required behavior: when the accepted activation candidate/base HEAD becomes stale before mutation, terminalize or supersede that stale intent deterministically and allow the scheduler to consider the current accepted candidate; never activate a revision proven against a different base. Add a focused regression proving no repeated active loop and that the newer candidate can progress. Do not touch unrelated WIP.
- Status: **accepted**
- Started: `2026-08-17T05:51:48.322Z`
- Finished: `2026-08-17T05:55:35.371Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **3**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `b5b55a6d709f4cfea81705a6165a55f2` | `mcp_only` | `4e5a5165e063b1b1816ef438babb19ca38d379d4` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 2060411587d94c4d9a7861c9ae13f7fd | b5b55a6d709f4cfea81705a6165a55f2 | accepted | 4e5a5165e063b1b1816ef438babb19ca38d379d4 | 68d2cecea4550795b20d5bb95add5df9b5a0ed52b1d9640eed7be4d915402818 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 11652 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `34`
- Chain head: `f4611263d7607f676b7ca3bade117ae3baaf1d743e4eb4db04784a74acbc9c8d`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
