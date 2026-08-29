# Orchestration Run Summary

- Run: `54290b6f078c43bdabe921de358a5d3a`
- Task: `8c29ae2870d74a0ea48eb59e463dfcce`
- Objective: Apply the already-localized smallest final UI/dashboard performance patch only. Preserve concurrent recovery/runtimeOrchestrator changes and all .coding-tools evidence. Required behavior: Overview force/manual/visibility refresh uses only lightweightSnapshot + liveOrchestration; analytics IPC timeout 10000 ms; dashboard analytics payload includes generated_at and window_days; dashboard canonical analytics helpers use analyticsSnapshot only with no full-orchestration fallback. Update focused regressions to make these invariants fail if reverted. Do not modify unrelated files.
- Status: **accepted**
- Started: `2026-08-28T10:47:33.598Z`
- Finished: `2026-08-28T11:45:33.763Z`

## Outcome metrics

- Waves: **3**
- Route decisions: **3**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **5**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `1216109b5a5d4ac5929bd3ad0b606521` | 1 | `run_initial_objective` | `mcp_only` | `2cc0eefc7d881827ef44e4d1584d84bbd9e494b6` | replanned |
| 2 | `a43a763240aa47a7a4b238eca2de6b53` | 2 | `replan_request` | `mcp_only` | `2cc0eefc7d881827ef44e4d1584d84bbd9e494b6` | replanned |
| 3 | `e7388c6e405a4186817a474aac4ca63a` | 3 | `replan_request` | `mcp_only` | `2cc0eefc7d881827ef44e4d1584d84bbd9e494b6` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| e74de22edbfc4e38a7ea5d0a4c9b4861 | e7388c6e405a4186817a474aac4ca63a | accepted | e4075d81e5de465837e501e28016ccc7b2afa7ce | 0000000000000000000000000000000000000000000000000000000000000000 |  |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 32261 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 32291 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 32313 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 32284 | `CHECK_FAILED` | `PROVING` |  |
| 32306 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `76`
- Chain head: `e830d963b0e327561ec2c5165933c1358c70cce6721b3ae81bb842a349a062a1`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
