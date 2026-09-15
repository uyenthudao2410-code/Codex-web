# Orchestration Run Summary

- Run: `dcb539e0e1694bc1bb29eed2b2e07f8b`
- Task: `86178b551c8c4b8997a24bdd6010683e`
- Objective: C01/M02 packaged cold-start canary on the current base for Problem prl-22e670302757c9b7663170e226ed7c26 revision 1. The Recovery Supervisor is already installed in packaged mode at E:\WebMcpAcceptanceHost-1.0.0 and healthy, while a development Recovery Host created by the manually reopened development app is currently being adopted. Arm one fail-closed current-user Interactive/Limited Scheduled Task that waits 15 seconds, revalidates the exact then-current Recovery Host PID, instance_id, runtime_mode=development and exact development Electron executable, and only then kills that exact Recovery Host. Do nothing if identity drifts. Do not edit source, reinstall, change supervisor manifest, reboot Windows, commit, push, release, publish or deploy. This wave proves only safe canary arming; packaged cold-start and tunnel return are evaluated after reconnect.
- Status: **accepted**
- Started: `2026-09-15T11:29:28.702Z`
- Finished: `2026-09-15T11:29:53.347Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `b35ed64b24dc4fa093cbe241df38719a` | 1 | `run_initial_objective` | `mcp_only` | `cffd2acee24a4f38f4a83ddfea4c40f766de7a63` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 8d10f27638e2498cba80edf0bcbe77ce | b35ed64b24dc4fa093cbe241df38719a | accepted | cffd2acee24a4f38f4a83ddfea4c40f766de7a63 | 11230a5fc02fa0a7285d238d9b86774fedb6a2c123f0e5d37eca69f7c56b9638 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 59702 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `30`
- Chain head: `9358353ebb48966d8e2bcf735e31e4674096f618ed0226c51b557b8c7596de78`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
