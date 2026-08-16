# Orchestration Run Summary

- Run: `23df148da9be4d73bfa024f62ce16c50`
- Task: `3e2db75d8452414bb3f6dc721fd02129`
- Objective: Final read-only repository acceptance verification for the completed Phase 2.5 Safe Code Activation hardening. Do not mutate source, runtime, Git, or files. The focused unit suite and exact Windows real-process E2E already passed on the current worktree; do not rerun the same E2E unnecessarily. Run the broad npm test suite, module-size budget check, and git diff whitespace check. Preserve all concurrent dirty changes and do not commit/push/restart live runtime.
- Status: **accepted**
- Started: `2026-08-16T04:35:43.579Z`
- Finished: `2026-08-16T04:37:34.151Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **3**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `7ac7b86974754764b4071fabb6d17e9b` | `mcp_only` | `597170860118a847b7e8a6f06903c37da8432d82` | replanned |
| 2 | `c5601a878dac4b46acc0a8397fdf18fb` | `mcp_only` | `597170860118a847b7e8a6f06903c37da8432d82` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| f7487bfa554045789b753d717613064f | c5601a878dac4b46acc0a8397fdf18fb | accepted | 597170860118a847b7e8a6f06903c37da8432d82 | 1af0662fa87b8834cae70e76098e8ad888b20c6a7fbf8104ec3dbbb90a407978 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 5737 | `deterministic` | `deterministic` | explicit_request |
| 5755 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 5748 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `45`
- Chain head: `5a469c0c6c7338bddc381921b6814f563cd851c12e5399692ce57a30065301a5`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
