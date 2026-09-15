# Orchestration Run Summary

- Run: `d01a5dce50c846fc8e13673cdfc8b3b3`
- Task: `ef4b241d0f2b470cab708fdf0896907d`
- Objective: C01 packaged cold-start post-canary proof for Problem prl-22e670302757c9b7663170e226ed7c26 revision 1. Prove that the accepted canary targeting development Recovery Host PID 47904 / instance 7fbed2a56114c6fa173915c12b6e2b5a completed successfully, and that the already-installed packaged Recovery Supervisor cold-started a new healthy packaged Recovery Host without manual reopen. Require canary LastTaskResult=0; manifest mode=packaged with exact host root/executable and installed supervisor SHA 9f6cd06422484cb4911ea47c822dd6e4c5040dc6647ce283bb024b7b861a0dab; supervisor healthy/live with zero consecutive failures and no error; Recovery Host PID/instance differ from the killed target; runtime_mode=packaged; process executable is E:\WebMcpAcceptanceHost-1.0.0\Coding Tools MCP.exe with SHA cf9235c1398d009762e9de5b25588e7fa85347a075ff6f18f2c4a5712558827c; supervisor last_spawned_pid equals the new Recovery Host PID; canonical supervisor task is Ready or Running. No source edit, process kill, reinstall, restart, reboot, commit, push, release, publish or deploy.
- Status: **accepted**
- Started: `2026-09-15T11:31:45.394Z`
- Finished: `2026-09-15T11:32:15.732Z`

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
| 1 | `2f7fed7000b0427ba2a4ab6d08f062ac` | 1 | `run_initial_objective` | `mcp_only` | `cffd2acee24a4f38f4a83ddfea4c40f766de7a63` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 6fb3de41a26349f5995a6a2bd92d82f2 | 2f7fed7000b0427ba2a4ab6d08f062ac | accepted | cffd2acee24a4f38f4a83ddfea4c40f766de7a63 | d40ed776c7dd2cd0b03f766cbbd77e571422e35aca5212dac041ddc9fdd890b4 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 59734 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `30`
- Chain head: `37d9c21464627a9c96d4e8986e92b7ab917c28277a6be5995fdc227998e2fc8d`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
