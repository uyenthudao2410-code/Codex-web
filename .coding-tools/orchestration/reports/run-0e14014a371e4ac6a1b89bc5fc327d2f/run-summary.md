# Orchestration Run Summary

- Run: `0e14014a371e4ac6a1b89bc5fc327d2f`
- Task: `eb71d3bcad194055a613cd932bc4c37a`
- Objective: Pinpoint the Scheduled Task failure with one bounded on-demand diagnostic task. Keep the production development supervisor suppressed via stop.request and do not alter the existing WebMCP Recovery Supervisor task. Register a temporary same-user Limited Interactive Scheduled Task whose action is direct powershell.exe invoking the already-installed recovery-supervisor.ps1 -Action Once, start it, wait for completion, inspect LastTaskResult and status, then unregister the temporary task in finally. Recovery Host PID/instance must remain unchanged and alive. Leave production stop.request present. No source edits, packaged install, runtime stop/restart, reboot/logoff, commit/push/release/deploy.
- Status: **accepted**
- Started: `2026-09-15T07:05:45.923Z`
- Finished: `2026-09-15T07:08:27.606Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **2**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `57edc64419374b91822f024613b92d4f` | 1 | `run_initial_objective` | `mcp_only` | `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6` | replanned |
| 2 | `710748d91d2447d19642d56fd4211cb4` | 2 | `replan_request` | `mcp_only` | `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 472a52de6d24432e80fffc3b7c379afd | 710748d91d2447d19642d56fd4211cb4 | accepted | a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6 | 6e67a40ff39628c7291fb35b6352d83eff10e79e2c281d89efdb7c9229672a1a | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 57320 | `deterministic` | `deterministic` | explicit_request |
| 57382 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 57334 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `55`
- Chain head: `86eded55b45ce86d00443577a9a0c06ab5ab6ab2183d8eba7cdad67998a9d45c`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
