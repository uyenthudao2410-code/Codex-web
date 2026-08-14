# Orchestration Run Summary

- Run: `200332da9f66499f8ff36e42c0d93005`
- Task: `56bb286b2f6543e68fd559d8c46b9a51`
- Objective: Fix the Execution Control Center analytics projection and evidence semantics without changing layout, routing policy, or the public MCP contract. The dashboard must consume PerformanceTraceStore.recent (legacy records fallback only), derive context-token equivalents only from measured model_visible_bytes, never from request/response transport bytes, and prefer measured numeric delegation economics for model rows. Clearly mark MEASURED vs ESTIMATED and SCENARIO cost. Preserve all concurrent UI work.
- Status: **accepted**
- Started: `2026-08-14T08:46:56.147Z`
- Finished: `2026-08-14T08:47:52.969Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **0**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `748b42ed5aae4ac7a035f445357acd0e` | `mcp_only` | `bc820986e383391e36d243e0252e23b0aef8d5b8` | replanned |
| 2 | `274468e1b1be4bd38b74e9b5dfcbecf6` | `mcp_only` | `bc820986e383391e36d243e0252e23b0aef8d5b8` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 982b96c950764cb997134f9f905ce0c4 | 274468e1b1be4bd38b74e9b5dfcbecf6 | accepted | bc820986e383391e36d243e0252e23b0aef8d5b8 |  | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 1638 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 1648 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 1642 | `PATCH_AMBIGUOUS` | `EXECUTING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `22`
- Chain head: `64b6a02e5f64a7a000a9ea9acede9ab401d759d3216257ad1bea797d49f57a81`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
