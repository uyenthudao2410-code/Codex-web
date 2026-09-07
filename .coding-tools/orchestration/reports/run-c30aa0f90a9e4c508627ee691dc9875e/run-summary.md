# Orchestration Run Summary

- Run: `c30aa0f90a9e4c508627ee691dc9875e`
- Task: `714c33b697bd44e7bbd9b3019fdb1476`
- Objective: Read only the implementation and tests that define managed_job_residue and its supported remediation for exact stale RUN reconciliation. Identify whether residue can be terminalized via command_control/task_control while the runtime is live, or only through stopped-runtime maintenance. Do not modify jobs, ledger, source, Git, runtime, or services.
- Status: **accepted**
- Started: `2026-09-07T02:33:34.701Z`
- Finished: `2026-09-07T02:35:53.351Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **3**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `7ff8d8303c544a3a9d0898b8c50f578a` | 1 | `run_initial_objective` | `mcp_only` | `9255f94c9beff33f8c6c53d6745a08968f5a12bb` | replanned |
| 2 | `5975e031825a4291aced101ea6073465` | 1 | `replan_request` | `mcp_only` | `9255f94c9beff33f8c6c53d6745a08968f5a12bb` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| d454dcfea25c4034b516d36c9217c35d | 5975e031825a4291aced101ea6073465 | accepted | 9255f94c9beff33f8c6c53d6745a08968f5a12bb | 67f529aef336553de249cccc25e08ed4f642005975ac22e70edf05d3b90464c4 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 42694 | `deterministic` | `deterministic` | explicit_request |
| 42719 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 42709 | `INVALID_ARGUMENT` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `56`
- Chain head: `141632cf510359a3f35d94fe39ff8fa4cb0ff0867c72601a7eaad68a644c0836`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
