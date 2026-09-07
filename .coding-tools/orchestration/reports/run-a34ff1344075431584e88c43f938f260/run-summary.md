# Orchestration Run Summary

- Run: `a34ff1344075431584e88c43f938f260`
- Task: `c1df39908d534a56ac5107264398371b`
- Objective: Read only the exact implementation boundaries needed to execute the final repair safely: locate every production caller of exact stale-run reconciliation, identify whether Recovery Host/full-clean activation invokes it automatically or exposes a maintenance hook, and inspect the task_control restart_runtime confirmation/restart handoff contract. Do not mutate source, Git, ledger, runtime, machine state, or services.
- Status: **aborted**
- Started: `2026-09-07T02:26:38.129Z`
- Finished: `2026-09-07T02:29:25.129Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **4**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `76537433b1a54ee496858da292ed2d53` | 1 | `run_initial_objective` | `mcp_only` | `9255f94c9beff33f8c6c53d6745a08968f5a12bb` | replanned |
| 2 | `9bbf50ef54864b24aea8563186a3545b` | 2 | `replan_request` | `mcp_only` | `9255f94c9beff33f8c6c53d6745a08968f5a12bb` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 42560 | `deterministic` | `deterministic` | explicit_request |
| 42589 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 42579 | `CHECK_FAILED` | `PROVING` |  |
| 42608 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `60`
- Chain head: `2d7928561e47924d779d575198f32af0697cfa69125580d53c6168f0a86e5760`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
