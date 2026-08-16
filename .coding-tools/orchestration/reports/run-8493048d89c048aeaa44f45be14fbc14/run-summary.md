# Orchestration Run Summary

- Run: `8493048d89c048aeaa44f45be14fbc14`
- Task: `f7809f328eb04aa7af9a4b958804c9e5`
- Objective: Prepare the narrow R2B automatic server-preferred dispatch slice on top of accepted server_compute opt-in. Inspect current Cargo read-only validation flow and compute placement adapter to implement source-authoritative HEAVY offload only for cargo_check/cargo_test when timeout has durable-job handoff headroom and sandbox is absent. Source Runner must supply full clean exact HEAD; candidate compute Runner must be a different Runner, explicitly server_compute=true, same logical project id, exact same full clean HEAD, structured validation + exact-source capable, fresh and within known job capacity. If no eligible target, preserve current source Runner behavior. No cross-runner retry, no dirty snapshot, no mutating cargo_fmt offload, no public tool schema changes. Determine exact current methods for listing auth-visible clients/jobs and canonical runtime project resolution, and exact test helpers for multi-runner validation dispatch.
- Status: **accepted**
- Started: `2026-08-16T12:43:10.313Z`
- Finished: `2026-08-16T13:59:11.237Z`

## Outcome metrics

- Waves: **11**
- Route decisions: **10**
- Failures observed: **10**
- REPLAN transitions: **10**
- Proof stages: **8**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `ba85235190894dde9cc39eadd39a49cf` | `mcp_only` | `cf6cb6ddbf29d90515d003ce72490ffda985c37f` | replanned |
| 2 | `80dca6b3e36447ae8832382db5c6b2e1` | `deep_single_lane` | `cf6cb6ddbf29d90515d003ce72490ffda985c37f` | replanned |
| 3 | `d5356ba14b2041be95c4ac94ebfd688b` | `mcp_only` | `cf6cb6ddbf29d90515d003ce72490ffda985c37f` | replanned |
| 4 | `361e51fe83124b508dfdc3291faad23b` | `mcp_only` | `cf6cb6ddbf29d90515d003ce72490ffda985c37f` | replanned |
| 5 | `5173e055072e4d12864a705503154712` | `mcp_only` | `cf6cb6ddbf29d90515d003ce72490ffda985c37f` | replanned |
| 6 | `f9600207c6214b5781164f705e95527c` | `mcp_only` | `cf6cb6ddbf29d90515d003ce72490ffda985c37f` | replanned |
| 7 | `efbc6560c5d4457fa2a0223d7f0222cd` | `mcp_only` | `cf6cb6ddbf29d90515d003ce72490ffda985c37f` | replanned |
| 8 | `c359b9d045744318b8605240ea751229` | `mcp_only` | `cf6cb6ddbf29d90515d003ce72490ffda985c37f` | replanned |
| 9 | `fd12329a20bc4c5da5e6653baf981165` | `mcp_only` | `cf6cb6ddbf29d90515d003ce72490ffda985c37f` | replanned |
| 10 | `31304bded2114a119aebac4d1e5c99f4` | `mcp_only` | `cf6cb6ddbf29d90515d003ce72490ffda985c37f` | replanned |
| 11 | `5b266a072e304b44b0aab3de02b7d9e3` | `mcp_only` | `cf6cb6ddbf29d90515d003ce72490ffda985c37f` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 78286bcad874456b916e5c1bc3932a58 | 5b266a072e304b44b0aab3de02b7d9e3 | accepted | cf6cb6ddbf29d90515d003ce72490ffda985c37f | f2fff591792393621e2d77d202d4c3c9937c6153b57da7fda8c9eb3dcf197d40 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 8071 | `sol_xhigh` | `sol_xhigh` | explicit_request |
| 8083 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 8100 | `deterministic` | `deterministic` | explicit_request |
| 8120 | `deterministic` | `deterministic` | explicit_request |
| 8131 | `deterministic` | `deterministic` | explicit_request |
| 8149 | `deterministic` | `deterministic` | explicit_request |
| 8167 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 8187 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 8205 | `deterministic` | `deterministic` | explicit_request |
| 8470 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 8064 | `BASE_DRIFT` | `PREFLIGHT` |  |
| 8077 | `CANDIDATE_MODEL_NOT_COMPLETED` | `ROUTED` |  |
| 8094 | `CHECK_FAILED` | `PROVING` |  |
| 8111 | `CHECK_FAILED` | `PROVING` |  |
| 8124 | `INVALID_ARGUMENT` | `EXECUTING` |  |
| 8142 | `CHECK_FAILED` | `PROVING` |  |
| 8160 | `CHECK_FAILED` | `PROVING` |  |
| 8178 | `CHECK_FAILED` | `PROVING` |  |
| 8198 | `CHECK_FAILED` | `PROVING` |  |
| 8209 | `INVALID_ARGUMENT` | `EXECUTING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `172`
- Chain head: `e7827db97a33ae955a83687a56516ee6906376b1ec5710730e6ea409f48dc24d`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
