# Orchestration Run Summary

- Run: `5e7915c474714154b7ac0f89a43f741d`
- Task: `b05be44cc13e402f88cd707e204399f7`
- Objective: Audit S6/W7 Capability Policy + Secret Broker foundation against current source. Determine the smallest causal implementation that unifies existing permission/EOCL/execution-resource decisions without adding a public tool or duplicate authority. Explicitly inspect secret/env injection paths and experimental Code Mode isolation; keep Code Mode fail-closed if no verified isolated worker exists. Identify exact negative security tests for: model input cannot elevate capability, secret values never enter model-facing result/audit, sensitive execution defaults deny network/full host env, child/process paths cannot bypass denied capability, and crashes/terminalization leave no orphan authority. Do not mutate source.
- Status: **accepted**
- Started: `2026-08-21T01:26:05.532Z`
- Finished: `2026-08-21T02:16:16.969Z`

## Outcome metrics

- Waves: **6**
- Route decisions: **6**
- Failures observed: **5**
- REPLAN transitions: **5**
- Proof stages: **20**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `ed195191c68a4b6babdc2a75f6dd2448` | `mcp_only` | `640ad37e3e571a0a56af376e9d3bda2b89bf0669` | replanned |
| 2 | `cf3f2dd6cfa64ddea450ef2447494f06` | `mcp_only` | `640ad37e3e571a0a56af376e9d3bda2b89bf0669` | replanned |
| 3 | `0772e6d6c76d4267b4a3238e9611bb20` | `mcp_only` | `640ad37e3e571a0a56af376e9d3bda2b89bf0669` | replanned |
| 4 | `7d38651f175144a69734e00756a3fd0f` | `mcp_only` | `640ad37e3e571a0a56af376e9d3bda2b89bf0669` | replanned |
| 5 | `5ef6e80e5c914b4ca7c0e7679291e448` | `mcp_only` | `640ad37e3e571a0a56af376e9d3bda2b89bf0669` | replanned |
| 6 | `1f74ab333f94410da7d263ddc101516b` | `mcp_only` | `640ad37e3e571a0a56af376e9d3bda2b89bf0669` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| be450ceb3cb24803ba321dfc1c2d8c64 | 1f74ab333f94410da7d263ddc101516b | accepted | 640ad37e3e571a0a56af376e9d3bda2b89bf0669 | 588962bc4a36e183df002a4e93ea0bdb7508ee557e8d9575089b384c79be9c10 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 25068 | `deterministic` | `deterministic` | explicit_request |
| 25095 | `deterministic` | `deterministic` | explicit_request |
| 25149 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 25188 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 25227 | `deterministic` | `deterministic` | explicit_request |
| 25245 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 25084 | `CHECK_FAILED` | `PROVING` |  |
| 25121 | `CHECK_FAILED` | `PROVING` |  |
| 25181 | `CHECK_FAILED` | `PROVING` |  |
| 25216 | `PERMISSION_REQUIRED` | `PROVING` |  |
| 25234 | `PERMISSION_REQUIRED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `241`
- Chain head: `cede4903a1a6550f11d36e3bb6270e498c742038d3fcbc8b2dc3fe95b53a6652`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
