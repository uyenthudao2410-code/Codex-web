# Orchestration Run Summary

- Run: `e6ca4861eb3c4103bdeccac1e75bee27`
- Task: `c28bef1e188e44daa23d4a6dd9d30cf9`
- Objective: Fix the single full-Python regression failure after P1A by updating only the stale Smart-v3 contract SHA oracle. The public tool count/profile remain 8/smart-v3; the schema fingerprint legitimately changed because the existing agent_workflow schema gained continuation. Do not change production runtime behavior or historical research snapshots in this wave.
- Status: **accepted**
- Started: `2026-08-15T02:40:34.700Z`
- Finished: `2026-08-15T02:41:07.408Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **2**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `59794793c40443b08cc2cd5979456df3` | `mcp_only` | `dff81e251836666fc825c40bf86e4167afd29c39` | replanned |
| 2 | `fee33de556ce41678918f9f1fba0ad0c` | `mcp_only` | `dff81e251836666fc825c40bf86e4167afd29c39` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 43d93edbe5e74bcfa139384ba2286250 | fee33de556ce41678918f9f1fba0ad0c | accepted | dff81e251836666fc825c40bf86e4167afd29c39 | aa66a0c44e5e556d5dfab6d2f2e5dbe85d00b2f0851db542162de1dabf3f0d58 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 3859 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 3872 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 3867 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `27`
- Chain head: `367beae5da4f68e1bd3c40adf6210ee8baad15cb15b4191b516ca331f3cd6238`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
