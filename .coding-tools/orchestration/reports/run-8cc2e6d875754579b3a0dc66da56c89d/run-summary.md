# Orchestration Run Summary

- Run: `8cc2e6d875754579b3a0dc66da56c89d`
- Task: `26031f24e62d45e789ddaf6b81087254`
- Objective: Diagnose why the production WebMCP Recovery Supervisor Scheduled Task invoking the installed recovery-supervisor.ps1 -Action Run does not publish a fresh capability-bearing heartbeat after the official Install. Determine the exact production-only failure cause using read-only evidence: Scheduled Task definition/result/principal/settings, TaskScheduler Operational events, installed/source/status/manifest timestamps and hashes, any live installed Run process, install-directory timestamps, source Run/lock logic, and the full focused Recovery Supervisor test file. Do not retry Install, do not start/stop/delete tasks, do not edit source/runtime files, and do not restart runtime in this wave.
- Status: **accepted**
- Started: `2026-09-15T07:43:11.656Z`
- Finished: `2026-09-15T07:51:38.223Z`

## Outcome metrics

- Waves: **3**
- Route decisions: **3**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **11**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `f4685ca3c80b401887a3c5ae831bb658` | 1 | `run_initial_objective` | `mcp_only` | `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6` | replanned |
| 2 | `694692871e75418eb1692aa65fd09ece` | 2 | `replan_request` | `mcp_only` | `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6` | replanned |
| 3 | `063b2db00b894b53901d6124e8912a2f` | 3 | `replan_request` | `mcp_only` | `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 4b11484982ee4258b3b883ba0a8bf654 | 063b2db00b894b53901d6124e8912a2f | accepted | a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6 | c6b29b4b6b61ee412770213f5c0dd3092e85842e495f302efa0479df34e2baf1 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 57938 | `deterministic` | `deterministic` | explicit_request |
| 58009 | `deterministic` | `deterministic` | explicit_request |
| 58052 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 57978 | `CHECK_FAILED` | `PROVING` |  |
| 58033 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `117`
- Chain head: `50b0fb572d5b96878be3a397fa5e21771d786a44f19bc6f096daea79d3f68634`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
