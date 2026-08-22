# Orchestration Run Summary

- Run: `df773562c37d42e6ae5c90505544e408`
- Task: `fb7d810b6a724ad89c79cd7b7130f9a5`
- Objective: Continue diagnosing the T2.1 integration failure now reproduced exactly: MCPHandler.control_orchestration_snapshot() returns truth_snapshot.orchestration.wave_id=None although the test created an active OrchestrationControl context and called task_state.set_orchestration_projection(ctx.projection()). Inspect only the reconciliation and task-state code that can clear/replace projection before truth snapshot construction. Identify the causal line and smallest correct fix/test adjustment. No mutation and no package/release/restart.
- Status: **accepted**
- Started: `2026-08-21T08:18:06.562Z`
- Finished: `2026-08-21T13:40:34.702Z`

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
| 1 | `dfb052eeff2d4153b158b87d91607eca` | 1 | `run_initial_objective` | `mcp_only` | `9eb05072e54ffca9576e23c2d4a4f4e14034bddc` | replanned |
| 2 | `b7e8d26a80404bf1984706c4a65beacc` | 2 | `replan_request` | `mcp_only` | `9eb05072e54ffca9576e23c2d4a4f4e14034bddc` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 6d4453ffb7254deca6af7b92934b1395 | b7e8d26a80404bf1984706c4a65beacc | accepted | 9eb05072e54ffca9576e23c2d4a4f4e14034bddc | c53830a4abb05b5db0fa038fa6c86714d9f4d28849bfb4254e660d6013e48d06 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 26280 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 26301 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 26293 | `SOL_REJECTED` | `ACCEPTING` | Reject final acceptance because the wave's canonical effective_objective is the original diagnostic/no-mutation objective, but this same wave acquired a write lease and mutated resources/coding-tools-mcp/tests/test_truth_snapshot.py. Event replay contains no wave_replanned transition before mutation. This objective-to-mutation provenance mismatch violates T1 traceability. Replan a new wave with the exact T2.1 fixture-fix objective and rerun the focused TruthSnapshot oracle; do not modify production source. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `40`
- Chain head: `cae031e222add1786f2217b78666b443e10e361ea82faded7060bf45296cc28c`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
