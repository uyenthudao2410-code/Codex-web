# Orchestration Run Summary

- Run: `621cc7fdbfaa45b4b1a35a75b1bc71ed`
- Task: `3e2546875dd7460f9ea3bb6309115bef`
- Objective: Formally accept the already implemented recovery-host source fix for the production activation gate. Preserve all existing changes and run focused recovery-action acceptance tests.
- Status: **aborted**
- Started: `2026-10-13T01:35:49.103Z`
- Finished: `2026-10-13T02:06:31.621Z`

## Outcome metrics

- Waves: **4**
- Route decisions: **2**
- Failures observed: **4**
- REPLAN transitions: **4**
- Proof stages: **0**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `210f7c0af5e742f5aa99391dcb150877` | 1 | `run_initial_objective` | `mcp_only` | `7999c4151cb501db86f2e4d0a2275d33fc248324` | replanned |
| 2 | `b05a8c2c8d574395895c39441c0a41f7` | 1 | `replan_request` | `mcp_only` | `7999c4151cb501db86f2e4d0a2275d33fc248324` | replanned |
| 3 | `8c666a7e90a940918ebe446615e278b2` | 1 | `replan_request` | `mcp_only` | `7999c4151cb501db86f2e4d0a2275d33fc248324` | replanned |
| 4 | `05957ce872fe4e6c998b12022ed62120` | 1 | `replan_request` | `mcp_only` | `7999c4151cb501db86f2e4d0a2275d33fc248324` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 61306 | `deterministic` | `deterministic` | explicit_request |
| 61330 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 61288 | `BASE_DRIFT` | `PREFLIGHT` |  |
| 61295 | `BASE_DRIFT` | `PREFLIGHT` |  |
| 61320 | `RUNTIME_RESUME_REQUIRED` | `PROVING` | A non-terminal wave was recovered outside its original synchronous execution. |
| 61343 | `RUNTIME_RESUME_REQUIRED` | `PROVING` | A non-terminal wave was recovered outside its original synchronous execution. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `64`
- Chain head: `04f4a81692f463b3aa5d555bf0a5ad5d43fe6230aedb950b4ef7a870e46dc262`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
