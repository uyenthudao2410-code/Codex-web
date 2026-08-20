# Orchestration Run Summary

- Run: `3c3564b92e5643e7b1248b94bd5386a5`
- Task: `a6868641c0034ebcbf52933c7b35cf51`
- Objective: Repair the Operator Control Panel live-routing path so realtime node states do not depend on heavyweight orchestration analytics. Add an authorized /__control/orchestration/live path backed by a live=True branch of the existing snapshot builder; live mode must return only panel-required authoritative state before usage_analytics, operations_analytics, routing_evidence, flight_recorder, history and resume work. Keep /__control/orchestration full behavior for manager/dashboard. Add panel:live-control IPC with 2500ms timeout; panelPreload uses it while manager preload remains on panel:orchestration. Preserve renderer fail-closed/evidence-gated semantics and usage truth contracts. Add focused regression tests. Preserve unrelated WIP. No commit/push/restart/deploy/release.
- Status: **accepted**
- Started: `2026-08-20T07:54:17.759Z`
- Finished: `2026-08-20T08:22:17.215Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **9**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `e943601fe3514d63a1344ec3ccf6b32f` | `mcp_only` | `5f059a1a53ff2beb9adfa4f2df9ee42907141816` | replanned |
| 2 | `1709e8853e67498d90cc107f2f1e9339` | `mcp_only` | `5f059a1a53ff2beb9adfa4f2df9ee42907141816` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 7fd720871130450a95eead0e88454555 | 1709e8853e67498d90cc107f2f1e9339 | accepted | 5f059a1a53ff2beb9adfa4f2df9ee42907141816 | 47b71099be17ae8c009ab6e9cf9e596d0c0418948adae2644baa6a53bd24f04b | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 23356 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 23397 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 23383 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `82`
- Chain head: `83d250b614b6956661accaea43ed894b141cfb5de6f6df5d2052d26ad92d4b4a`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
