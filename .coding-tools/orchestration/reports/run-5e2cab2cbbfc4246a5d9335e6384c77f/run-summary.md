# Orchestration Run Summary

- Run: `5e2cab2cbbfc4246a5d9335e6384c77f`
- Task: `d087490bdcff443cb10f1c75124cce5b`
- Objective: Wave B: make the runtime cost-controlled while representative ROI data is being collected. Automatic agent routing must not spend model credits: execution_route=auto resolves deterministic with a fail-closed ROI-evidence hold reason. Mini/Luna/Sol/Terra remain explicit-only routes; max/ultra high-cost acknowledgement remains unchanged. External semantic review defaults off and remains explicit opt-in via the existing environment control. Admission budgeting must not count auto as a candidate call. Preserve Smart-v3 at 8 public tools and do not call any provider.
- Status: **accepted**
- Started: `2026-08-15T04:22:46.781Z`
- Finished: `2026-08-15T04:23:23.138Z`

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
| 1 | `f205e3a81a3c453f979f5e969cc5ad51` | `mcp_only` | `dff81e251836666fc825c40bf86e4167afd29c39` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| a1a3f1d5f3754407a269977a17448dcc | f205e3a81a3c453f979f5e969cc5ad51 | accepted | dff81e251836666fc825c40bf86e4167afd29c39 | 0f945a683ac6c524b19e7c146234745abe81d09c443e77a836e43cb100abc54d | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 4169 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `13`
- Chain head: `047bc968f2649d52939a82d492385d696c8adf61d0708e1cf15cb2288e22be99`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
