# Orchestration Run Summary

- Run: `35a4c3e13c094de9b07aef7280df8ebb`
- Task: `06d892d149da43528b7d7da2159f6223`
- Objective: Repair the two proven Rust test-contract defects without changing production behavior: make connector host Git fixtures line-ending deterministic on Windows, and align compact tool_manifest metadata tests with the deliberate ModelHidden start_coding_task/API-compatibility boundary. Do not reintroduce start_coding_task into model-visible discovery, do not change product schemas or runtime behavior, and preserve all smart-v3/public-surface invariants.
- Status: **aborted**
- Started: `2026-08-23T04:40:09.358Z`
- Finished: `2026-08-23T04:44:38.767Z`

## Outcome metrics

- Waves: **6**
- Route decisions: **6**
- Failures observed: **9**
- REPLAN transitions: **9**
- Proof stages: **4**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `9b326d1bd1714162b3a7fa82af670f58` | 1 | `run_initial_objective` | `mcp_only` | `9e150020a0c0829a988ffea527d5c8d82132ed65` | replanned |
| 2 | `4dd5d185d94c4f9294f9dcf701b1b253` | 2 | `replan_request` | `mcp_only` | `9e150020a0c0829a988ffea527d5c8d82132ed65` | replanned |
| 3 | `25eb4383852b42008938190741ebee94` | 3 | `replan_request` | `mcp_only` | `9e150020a0c0829a988ffea527d5c8d82132ed65` | replanned |
| 4 | `2d4c6bf552a9463aa26cd49da9937cd2` | 4 | `replan_request` | `mcp_only` | `9e150020a0c0829a988ffea527d5c8d82132ed65` | replanned |
| 5 | `ad7c621cfaa744bf9004be7a6b949060` | 5 | `replan_request` | `mcp_only` | `9e150020a0c0829a988ffea527d5c8d82132ed65` | active |
| 6 | `c939424e57c84cf3a9d7c1d76e9039d4` | 6 | `replan_request` | `mcp_only` | `9e150020a0c0829a988ffea527d5c8d82132ed65` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 28391 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 28409 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 28431 | `deterministic` | `deterministic` | explicit_request |
| 28453 | `deterministic` | `deterministic` | explicit_request |
| 28461 | `deterministic` | `deterministic` | explicit_request |
| 28485 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 28403 | `CHECK_FAILED` | `PROVING` |  |
| 28419 | `RUNTIME_RESUME_REQUIRED` | `PROVING` | A non-terminal wave was recovered outside its original synchronous execution. |
| 28425 | `EXECUTION_OWNER_INVALID` | `PROVING` |  |
| 28440 | `RUNTIME_RESUME_REQUIRED` | `PROVING` | A non-terminal wave was recovered outside its original synchronous execution. |
| 28446 | `EXECUTION_OWNER_INVALID` | `PROVING` |  |
| 28468 | `EXECUTION_OWNER_MISMATCH` | `PROVING` |  |
| 28479 | `EXECUTION_OWNER_MISMATCH` | `PROVING` |  |
| 28490 | `RUNTIME_RESUME_REQUIRED` | `EXECUTING` | A non-terminal wave was recovered outside its original synchronous execution. |
| 28495 | `EXECUTION_OWNER_INVALID` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `113`
- Chain head: `425ad0b8631e517198bf31f9bad74846f1e83fee2eb80c00690ef5fa481a74c3`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
