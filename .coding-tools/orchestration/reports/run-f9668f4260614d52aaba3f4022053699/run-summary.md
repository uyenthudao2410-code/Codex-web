# Orchestration Run Summary

- Run: `f9668f4260614d52aaba3f4022053699`
- Task: `1f3f20c280e141dcb265af565ad860fd`
- Objective: Bootstrap activation-authority checkpoint only: exact-byte, no-write adoption of the complete current pre-existing dirty Coding MCP component surface after UNACCEPTED_COMPONENT_DIRTY. Preserve bytes exactly; do not execute or claim Stage B/TG completion.
- Status: **aborted**
- Started: `2026-09-02T00:47:40.602Z`
- Finished: `2026-09-02T01:08:50.672Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **1**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `ea660a139b974e6fb06cb546102d8e9b` | 1 | `run_initial_objective` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | replanned |
| 2 | `6013ae952b464b72a6ffccb2664abe2d` | 1 | `replan_request` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 35207 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 35222 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `47`
- Chain head: `f5ffd2104720fd8522e731416aa2ddeccc9ac6de41fdc43b28cf818762da314b`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
