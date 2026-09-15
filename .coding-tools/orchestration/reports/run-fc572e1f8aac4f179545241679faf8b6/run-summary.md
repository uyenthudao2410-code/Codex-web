# Orchestration Run Summary

- Run: `fc572e1f8aac4f179545241679faf8b6`
- Task: `62a18c6698a44febaf7cb69c4a5f9567`
- Objective: Prepare the next bounded C01/M02 phase for canonical Problem prl-22e670302757c9b7663170e226ed7c26 rev1, starting from accepted packaging checkpoint 737171aeb2194e3dae2262dd59bb645a and installed-smoke checkpoint 577b890ebdfe487d8ca99f95df333af8. Candidate is dist/coding-tools-mcp-setup-1.0.0.exe, size 121748977, SHA256 8597162DB4D2E3D0955FD8F123F70DA543C79475B17EFAD4DDB088F289429F8E. Current live state: no known 1.0.0 per-user install; existing Scheduled Task WebMCP Recovery Supervisor is a DEVELOPMENT supervisor installed 2026-09-10 for E:\DEV\Codex-web, exact source/install supervisor hashes match, but a stop.request from 2026-09-15T04:09:03Z keeps it in stopping/dead state while Recovery Host PID 9640 remains alive. Identify the repository-supported exact commands and rollback to create a CONTROLLED packaged persistent acceptance install for 1.0.0 in a distinct per-user acceptance path, install/verify its packaged Recovery Supervisor/Scheduled Task without changing source or intentionally stopping the live development Recovery Host/MCP/Tunnels, then capture a pre-reboot capsule. This PREPARE phase must not install/uninstall anything, remove stop.request, register/unregister tasks, restart runtime, reboot/logoff, edit source, clear state, commit, push, publish, release, or deploy. Also account for a separate foreign Problem RUN f1675a1cc4f04482bec7087b16e2c2c6 currently in REPLAN with no active command/write lease; do not mutate or accept/reject that RUN. Return exact command sequence, safety preconditions, expected evidence, and rollback. Actual reboot remains a separate explicit boundary and must not be executed in this wave.
- Status: **accepted**
- Started: `2026-09-15T06:38:32.537Z`
- Finished: `2026-09-15T06:44:28.607Z`

## Outcome metrics

- Waves: **3**
- Route decisions: **3**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **3**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `ffa2874227194db4b5eb2d57ef82a684` | 1 | `run_initial_objective` | `mcp_only` | `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6` | replanned |
| 2 | `c8e2957282f14ba9a9d7168d08440ff3` | 2 | `replan_request` | `mcp_only` | `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6` | replanned |
| 3 | `d0e4ca58f710442c9c5509b561b9fdd8` | 3 | `replan_request` | `mcp_only` | `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 53f2b9a5e4494769b5b93e8f4f72f028 | d0e4ca58f710442c9c5509b561b9fdd8 | accepted | a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6 | 2680ba96d109d3631595027a18490558e5fd72b232d285d4278aa4a6a7e369da | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 56946 | `deterministic` | `deterministic` | explicit_request |
| 56971 | `deterministic` | `deterministic` | explicit_request |
| 57007 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 56960 | `CHECK_FAILED` | `PROVING` |  |
| 56990 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `80`
- Chain head: `0c006a821b788c3fd064513531d1376fb7117c3732b8af155ab03e9518736245`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
