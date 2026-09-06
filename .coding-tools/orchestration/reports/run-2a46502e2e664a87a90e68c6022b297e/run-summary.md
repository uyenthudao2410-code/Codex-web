# Orchestration Run Summary

- Run: `2a46502e2e664a87a90e68c6022b297e`
- Task: `4c59649bcdb348b0bb30e1f30fc10ede`
- Objective: DASHBOARD-MEASUREMENT-01: correct the current dashboard measurement projection and UI so missing or invalid by_model evidence never becomes observed measured zero. Preserve known input/output when only cached tokens are unknown, distinguish unavailable versus partial breakdown from complete genuine zero, clear stale/in-flight donut totals when breakdown becomes unavailable, and add behavioral VM coverage through the actual projector/render consumer. Write only renderer/dashboard.js and tests/dashboard-measurement-behavior.test.js; preserve all unrelated WIP.
- Status: **accepted**
- Started: `2026-09-05T09:20:59.366Z`
- Finished: `2026-09-05T09:40:12.304Z`

## Outcome metrics

- Waves: **3**
- Route decisions: **3**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **3**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `5b32ac0e27c740d2b2ec95c6d0fd76ca` | 1 | `run_initial_objective` | `mcp_only` | `8697ace8204e7e3da55d250d4a52d9b2b930116c` | replanned |
| 2 | `d8b257470bd6410693b5c5061509e374` | 1 | `replan_request` | `mcp_only` | `8697ace8204e7e3da55d250d4a52d9b2b930116c` | replanned |
| 3 | `5f6825a55cf149ab833a8405e4c98f4d` | 1 | `replan_request` | `mcp_only` | `8697ace8204e7e3da55d250d4a52d9b2b930116c` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| ae0c65c6b44f463e83e73fb3265f248d | 5f6825a55cf149ab833a8405e4c98f4d | accepted | 8697ace8204e7e3da55d250d4a52d9b2b930116c | 243893d52d8f8f6d5c5ef6349a197f911195db3a5c695d311a5fffa5f43635d3 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 40421 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 40445 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 40467 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 40436 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |
| 40460 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `72`
- Chain head: `f5afc8ad4e17aa4076ec736d39ced0253b773f3b35a8cc00fd4a2eddf3929989`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
