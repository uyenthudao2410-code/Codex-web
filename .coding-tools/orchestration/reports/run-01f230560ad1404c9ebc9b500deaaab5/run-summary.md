# Orchestration Run Summary

- Run: `01f230560ad1404c9ebc9b500deaaab5`
- Task: `68a560db3ffc47618acce24951c0f752`
- Objective: Prepare the smallest safe C01 true Windows reboot/logon acceptance wave for Problem prl-22e670302757c9b7663170e226ed7c26 revision 1. Determine the exact required matrix and design a durable post-reboot evidence probe that can distinguish a real OS reboot from process restart and verify the installed packaged Recovery Supervisor/Recovery Host after user logon. Do not reboot, logoff, restart runtime, commit, push, release, or mutate source in this prepare phase. Reuse the already-accepted fresh packaged artifact and Recovery Supervisor design; preserve all concurrent dirty work.
- Status: **accepted**
- Started: `2026-09-15T08:30:22.281Z`
- Finished: `2026-09-15T08:55:25.149Z`

## Outcome metrics

- Waves: **4**
- Route decisions: **4**
- Failures observed: **3**
- REPLAN transitions: **3**
- Proof stages: **7**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `0b7da6fcb9324d15bf0b87991ffa4ff5` | 1 | `run_initial_objective` | `mcp_only` | `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6` | replanned |
| 2 | `76dda3bac45f4a8bad55f80539a11882` | 2 | `replan_request` | `mcp_only` | `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6` | replanned |
| 3 | `75232bd7fb3f4a5398630f40a6c46459` | 3 | `replan_request` | `mcp_only` | `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6` | replanned |
| 4 | `c5754eb770c84b82a43c8a90726cc779` | 4 | `replan_request` | `mcp_only` | `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| daaa58b32e4b4efd9a1dd0a94c7240fd | c5754eb770c84b82a43c8a90726cc779 | accepted | a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6 | d674752cc7e6c397d259c8dc8951f90c641fa8431657a7c3e3905a130708b414 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 58536 | `deterministic` | `deterministic` | explicit_request |
| 58552 | `deterministic` | `deterministic` | explicit_request |
| 58581 | `deterministic` | `deterministic` | explicit_request |
| 58611 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 58542 | `INVALID_ARGUMENT` | `EXECUTING` |  |
| 58570 | `SOL_REJECTED` | `ACCEPTING` | Rejecting this wave because only the exact-byte preflight executed. The canonical npm run dist build did not execute and build_report is null, so the stated artifact-rebuild objective is not proven. No installed-state or reboot side effect occurred. Replan with npm run dist as an explicit check command so its exit status becomes durable proof before any installer replacement or reboot preparation. |
| 58600 | `PROOF_TIMEOUT` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `144`
- Chain head: `42c884cae51c8a7286a902f5cde990737dd7736deba3ca0d5eceee1bc409ed53`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
