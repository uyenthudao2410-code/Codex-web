# Orchestration Run Summary

- Run: `38ea02bb4f924ac98eda7df6ad8ab204`
- Task: `40b1adda435e48dd888a7a3afddd7db7`
- Objective: Complete the current replan wave for truthful token metering. Preserve the already-applied Control Center slice. MCP tools/list remains exact 8-tool contract discovery; controller/provider UsageEvents remain model usage/cost receipts; ChatWeb/Coding-VP Tool-call-card tokens are a distinct per-invocation host metric. Because current MCP transport has no exact post-call host receipt, expose card metering as unknown/— and never derive it from bytes/time/analytics. The visible Dashboard token/cost path must be canonical UsageEvent-only; remove the byte/token UI control and fail closed secondary model/fleet economics without canonical lane mapping. Preserve unrelated dirty work.
- Status: **accepted**
- Started: `2026-08-30T15:46:04.490Z`
- Finished: `2026-08-30T16:27:14.712Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **3**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `52bd621855d44d0c913a97d1e48df7c4` | 1 | `run_initial_objective` | `mcp_only` | `9b766f241432b9b5bfa8aa75ae2f1816709a2c2d` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 790ff6659a324e698d06956a4d3dd86a | 52bd621855d44d0c913a97d1e48df7c4 | accepted | 9b766f241432b9b5bfa8aa75ae2f1816709a2c2d | f88449b41325b8baa1fa0d85c8adb1c22c89eb7228e18ae7b0a614345e21919f | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 32774 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `37`
- Chain head: `0c2e99a719d324376db0773d3b31f19ad9d900aa8d95bf0252c33729f8852727`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
