# Orchestration Run Summary

- Run: `d2bc327185d0479395b57a06d4650f70`
- Task: `1e57a5e693074656a56fbb69e7151edb`
- Objective: Correct the stale integration oracle for acceptance observation spans under Parent Problem prl-22e670302757c9b7663170e226ed7c26 revision 1. Current authoritative behavior records three acceptance measurements on same-clock normal acceptance: observed_stage_duration, controller_processing, and acceptance_wait; tests/test_orchestration_control.py already validates controller_processing and acceptance_wait. Update only tests/test_orchestration_workflow.py::test_runtime_records_content_free_a2_stage_spans_without_new_contract_surface so it validates those three measurements and their stable span IDs instead of requiring exactly one acceptance span. Do not change production telemetry or controller-lease behavior. Then run the focused test and the affected execution_hub/controller/orchestration suite. No packaging/install/reboot/runtime restart/commit/push/release/deploy.
- Status: **accepted**
- Started: `2026-09-15T02:39:52.711Z`
- Finished: `2026-09-15T03:51:40.029Z`

## Outcome metrics

- Waves: **5**
- Route decisions: **5**
- Failures observed: **4**
- REPLAN transitions: **4**
- Proof stages: **10**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `0824fe99d0274225bbc7b8a80128a4bd` | 1 | `run_initial_objective` | `mcp_only` | `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6` | replanned |
| 2 | `048642464eca4813b164952fa317c8ee` | 2 | `replan_request` | `mcp_only` | `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6` | replanned |
| 3 | `6611889de49c4c15ba95c13a037e6c8d` | 3 | `replan_request` | `mcp_only` | `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6` | replanned |
| 4 | `26ba20a04aa94d2d89b38c37244515c1` | 4 | `replan_request` | `mcp_only` | `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6` | replanned |
| 5 | `62cd8229fb5646eda551e465c6e88c84` | 5 | `replan_request` | `mcp_only` | `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 7afb35dff4474f04a995c0e48bded47e | 62cd8229fb5646eda551e465c6e88c84 | accepted | a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6 | b5fb4857c846ee45c4a58f15460b22b1efd6e1e63131e877a26b5e8e36419d13 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 55597 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 55641 | `deterministic` | `deterministic` | explicit_request |
| 55665 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 55705 | `deterministic` | `deterministic` | explicit_request |
| 55722 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 55630 | `DEADLINE` | `PROVING` |  |
| 55655 | `CHECK_FAILED` | `PROVING` |  |
| 55694 | `SOL_REJECTED` | `ACCEPTING` | Final acceptance failed closed because one pre-existing dirty acceptance path (tests/test_orchestration_workflow.py) was not proven inside the current wave's durable mutation surface/write lease. Replan the same RUN to an exact-byte adoption wave for both test files, rerun the focused/affected oracles, and only then final-accept. |
| 55711 | `EXISTING_FILE_ADOPTION_PREEXISTING_DIRTY_REQUIRED` | `EXECUTING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `158`
- Chain head: `c01be013329975477f9ecbdbe2b7c01d14beb8d1ff86e41615558beb70a5215b`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
