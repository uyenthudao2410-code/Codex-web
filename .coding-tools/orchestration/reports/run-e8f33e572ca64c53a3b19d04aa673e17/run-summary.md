# Orchestration Run Summary

- Run: `e8f33e572ca64c53a3b19d04aa673e17`
- Task: `0d533b8ad7a445e0848857f4f3f24584`
- Objective: Implement Wave 0 measurement-correctness improvements on top of the current concurrent dashboard without changing routing policy, public MCP tool count, or authority semantics. Add exact model_visible_bytes accounting for MCP text actually projected to the model; preserve request_bytes/response_bytes only as transport/payload telemetry, not token truth. Allow the orchestration ledger to persist only exact known non-secret numeric token-usage counters from model economics while continuing to redact API/auth/credential token fields and invalid/string values. Update the existing dashboard to estimate context-equivalent tokens only from model_visible_bytes, clearly label context estimates and SCENARIO costs, and prefer measured delegation economics token counts for model/lane rows when available, with MEASURED vs ESTIMATED evidence labels. Do not call provider billing APIs, do not add a ninth tool, do not alter cost/routing thresholds, and preserve all unrelated dirty workspace changes.
- Status: **accepted**
- Started: `2026-08-14T08:43:03.172Z`
- Finished: `2026-08-14T08:46:17.469Z`

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
| 1 | `5e3cac708d6a4660962b0bd6d558ee26` | `mcp_only` | `bc820986e383391e36d243e0252e23b0aef8d5b8` | replanned |
| 2 | `3b605ae688d346ae8bfb5dbf45b23c0d` | `mcp_only` | `bc820986e383391e36d243e0252e23b0aef8d5b8` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 34ed081e799540e38917e7cca7071401 | 3b605ae688d346ae8bfb5dbf45b23c0d | accepted | bc820986e383391e36d243e0252e23b0aef8d5b8 |  | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 1616 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 1626 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 1620 | `PATCH_AMBIGUOUS` | `EXECUTING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `21`
- Chain head: `054cbf1c266ae4e2c3d782ff18050c03ecc4a8adcbbe3d5272326d0f083516de`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
