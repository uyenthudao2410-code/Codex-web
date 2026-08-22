# Orchestration Run Summary

- Run: `c53580bc18704b1faa7ba9b67d0b5363`
- Task: `ac061adec9a749509040a1e5502e9143`
- Objective: Retry the same accepted-result economics source slice after correcting the one stale report_p5_baseline import context. All prior attempts failed at patch preflight with no source write. Apply read-only economics reporting plus P5 resource noninferiority only; no new public tool/service/database/router; no P5 activation.
- Status: **active**
- Started: `2026-08-22T15:50:42.652Z`
- Finished: `None`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `d4bdf755984646e9a6245a609e2bcf9b` | 1 | `run_initial_objective` | `mcp_only` | `4ac63724cd07769b45c7063a6259b0f80276f73d` | active |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 27627 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 27645 | `SOL_REJECTED` | `ACCEPTING` | Focused verification is not green: 46/47 passed. The new accepted-result economics reporter orders the runs table by started_at, but the durable runs schema uses created_at. Reject this wave to apply the one-line schema correction and rerun the identical focused suite before acceptance. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `25`
- Chain head: `cf04c7c54164081d4f5ee6b6f6d18616837e662a81284a52e7bb2df0652e29a6`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
