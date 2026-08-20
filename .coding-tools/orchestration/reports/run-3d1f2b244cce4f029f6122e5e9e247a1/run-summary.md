# Orchestration Run Summary

- Run: `3d1f2b244cce4f029f6122e5e9e247a1`
- Task: `2131fd0f8b224bf8874900b33217bdf5`
- Objective: Prepare the final test-only repair for the three remaining legacy Execution Hub failures on main checkout. Read and obey resources/coding-tools-mcp/AGENTS.md. Preserve the already-written panel fail-visible changes and unrelated P4-MX/evaluation/telemetry dirt. Do not write yet. Localize post_stateless and only the three failing tests, plus the current acquire_controller_lease and events/run_id contract. Production Python must remain unchanged.
- Status: **accepted**
- Started: `2026-08-20T06:44:56.958Z`
- Finished: `2026-08-20T07:17:44.774Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **3**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `5c59c237603448129ceae0265665f2d5` | `mcp_only` | `2c29a7c8af82215c3c332c8f26902f1eb8d1c894` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 299aece714384479965a013a998574ee | 5c59c237603448129ceae0265665f2d5 | accepted | 2c29a7c8af82215c3c332c8f26902f1eb8d1c894 | 4458f43b35217d24a59bb71d2bc487d6275706c264784d98a9f19310b11ce2bc | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 23117 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `62`
- Chain head: `d6ee3be3ea9805150fa1037a5ad4df0ce598101f865b2dc56165ef4389a7cdf3`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
