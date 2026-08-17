# Orchestration Run Summary

- Run: `78c02031bba54724a61293f6b7618aa4`
- Task: `2c5650e8c26645ea88cedc294e60d445`
- Objective: Fix Recovery Host replacement race RECOVERY_TUNNEL_CANDIDATE_OWNER_UNVERIFIED without weakening ownership safety. A live legacy Recovery Tunnel candidate may be left by the old host's in-flight RecoveryPlane.ensure during handoff. The new host may migrate it only after exact legacy fingerprint + tunnel readiness/PID proof. Stamp its device owner atomically with other proven legacy recovery processes, then ensureTunnel must stop/clear known-owned stale candidate or primary tunnel processes before treating the health port as unrecognized. Foreign or unproven candidates remain fail-closed.
- Status: **accepted**
- Started: `2026-08-17T05:22:44.482Z`
- Finished: `2026-08-17T05:23:14.248Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **4**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `fdcfbec98c664bb6946091dbc95c2d85` | `mcp_only` | `4e5a5165e063b1b1816ef438babb19ca38d379d4` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| da8cbb5365d7424e96865aba9d4c822d | fdcfbec98c664bb6946091dbc95c2d85 | accepted | 4e5a5165e063b1b1816ef438babb19ca38d379d4 | 0871e395874e477d960f2552da5ab7f6e2a5d5097e3c8e588bac46c4b7432618 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 11590 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `32`
- Chain head: `fe70ef2c3a5f08198dbf6dcbd8f2772b4e363de0415645f32421b6d44e32e85c`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
