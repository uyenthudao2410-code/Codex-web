# Orchestration Run Summary

- Run: `1739e35082cc4ba9bd29429a8ba10b9c`
- Task: `98376b144e0c40808317f73578fee70d`
- Objective: Diagnose and localize the orchestration lifecycle bug evidenced by run 761f3b60b16c4be6a0dc9b1f43881173: the outer durable agent_workflow operation hit WORKFLOW_RUNTIME_EXCEEDED at 600s while its inner proof command continued, was later recorded as passed, a second proof command was admitted after the outer deadline, the canonical EOCL run was later ABORTED, but task-state/UI remained waiting at 'Awaiting acceptance'. Find the smallest coherent fix so workflow deadline terminalizes/cancels remaining proof execution, no next command is launched after deadline/cancel, timeout is never recorded as passed proof solely because exit_code is 0 after forced termination, and task projection reconciles terminal ABORTED/REPLAN states instead of showing Awaiting acceptance. Also identify tests to reproduce this without a 600s sleep. Do not modify files in prepare.
- Status: **accepted**
- Started: `2026-08-16T13:43:34.707Z`
- Finished: `2026-08-16T13:52:12.894Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **5**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `bbaaadd6a49640ee9dfeb11d04d4876c` | `mcp_only` | `cf6cb6ddbf29d90515d003ce72490ffda985c37f` | replanned |
| 2 | `10d8d913be294df49454d7a69840c3af` | `mcp_only` | `cf6cb6ddbf29d90515d003ce72490ffda985c37f` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 6187947743604496b52ecac35f65ff49 | 10d8d913be294df49454d7a69840c3af | accepted | cf6cb6ddbf29d90515d003ce72490ffda985c37f | 2b834cff8cbae1095999201a9122f73e708ac4e27d8d500f5824fc5bdb5e491e | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 8419 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 8441 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 8435 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `50`
- Chain head: `adf31dfa175b1bd0d91e77598e18bb28abee79b22b8c51b2124e2fa3efd6ab6c`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
