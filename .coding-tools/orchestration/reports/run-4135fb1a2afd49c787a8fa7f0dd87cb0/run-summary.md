# Orchestration Run Summary

- Run: `4135fb1a2afd49c787a8fa7f0dd87cb0`
- Task: `686e65f69c4847d991139824d68c609a`
- Objective: Add a focused isolated HTTP fixture regression test for latest-turn measurement envelope preservation, reader exception unknown state, and admission-closed journal non-read. Test-only maintenance; not usage instrumentation, real outcome, or natural Problem evidence.
- Status: **accepted**
- Started: `2026-09-05T04:43:14.596Z`
- Finished: `2026-09-05T07:47:55.502Z`

## Outcome metrics

- Waves: **4**
- Route decisions: **3**
- Failures observed: **3**
- REPLAN transitions: **3**
- Proof stages: **2**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `73b0f849954e4660beee87e99919650d` | 1 | `run_initial_objective` | `mcp_only` | `8697ace8204e7e3da55d250d4a52d9b2b930116c` | replanned |
| 2 | `a7a187e643f04d6987eef151b0645c96` | 2 | `replan_request` | `mcp_only` | `8697ace8204e7e3da55d250d4a52d9b2b930116c` | replanned |
| 3 | `edd6c5d3c6cd44768fe31da84a82c268` | 3 | `replan_request` | `mcp_only` | `8697ace8204e7e3da55d250d4a52d9b2b930116c` | replanned |
| 4 | `18004d86286a443781430706870ed561` | 3 | `replan_request` | `mcp_only` | `8697ace8204e7e3da55d250d4a52d9b2b930116c` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 914b8c816f1e42ffa793a8c7c976e90f | 18004d86286a443781430706870ed561 | accepted | 8697ace8204e7e3da55d250d4a52d9b2b930116c | 24002d4b198cb88ca916b8898fb80464cf2ba26c8764b7447c3a49a4a12476d7 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 40329 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 40349 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 40391 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 40340 | `INVALID_ARGUMENT` | `PROVING` |  |
| 40366 | `SOL_REJECTED` | `ACCEPTING` | REPORT-PARTIAL-01 review rejection: schema_version currently accepts 1.0 via equality instead of exact integer 1; timestamp parsing lacks bounded canonical ASCII shape/offset validation before datetime parsing; and the current tests/implementation allow an applied_patch_delta_v1 observation with zero affected files to be marked complete even though the canonical producer contract requires at least one affected file. Focused 14-test pass is therefore insufficient for final acceptance. |
| 40382 | `BASE_DRIFT` | `PREFLIGHT` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `78`
- Chain head: `736a38f27e21bad55f4e9565dd11f6d227579187eb511c818545be70a128a251`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
