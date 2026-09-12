# Orchestration Run Summary

- Run: `c2450739fa4249bcb95d686bda851452`
- Task: `7daf58f7af07467d9cfc1ca193b912ed`
- Objective: Natural #22 diagnosis and repair. Starting from the authoritative lifecycle census evidence that contextual projection has PROJECTION_DRIFT with missing_run_count=1, conflicting_run_count=0, malformed_context_projection=false, locate the exact missing relevant canonical run/context and determine whether the cause is projection rebuild logic, context-registry persistence, or relevance classification. Prepare the smallest causal repair. Do not rewrite canonical ledger history, alter accepted/checkpointed or P5/live/stale semantics, restart runtime, or modify unrelated dirty work.
- Status: **accepted**
- Started: `2026-09-10T10:31:14.774Z`
- Finished: `2026-09-10T10:50:30.360Z`

## Outcome metrics

- Waves: **5**
- Route decisions: **3**
- Failures observed: **4**
- REPLAN transitions: **4**
- Proof stages: **10**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `29b2d36a2e554429a5ddf7cef1da75b6` | 1 | `run_initial_objective` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | replanned |
| 2 | `b466ecbeef204d42a1fbdbb85ff91e63` | 2 | `replan_request` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | replanned |
| 3 | `e589f2aa4c9b4ea687962869a2324bdf` | 2 | `replan_request` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | replanned |
| 4 | `026440f1cc1e4f6d8860149299d8f78d` | 3 | `replan_request` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | replanned |
| 5 | `90256766d6e9491c82de4a3305b091e8` | 4 | `replan_request` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| c72d2946657b482698455c3337ed71ab | 90256766d6e9491c82de4a3305b091e8 | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | f6aa6bf1a3ec0f814ed4aece7065d67fe6c3c3139bf5c22b1660e575c03b1d5d | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 47541 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 47571 | `deterministic` | `deterministic` | explicit_request |
| 47618 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 47525 | `BASE_DRIFT` | `PREFLIGHT` |  |
| 47532 | `BASE_DRIFT` | `PREFLIGHT` |  |
| 47561 | `CHECK_FAILED` | `PROVING` |  |
| 47608 | `SOL_REJECTED` | `ACCEPTING` | Final acceptance failed closed with ACCEPTANCE_FILE_ATTESTATION_REQUIRED because the three source paths were already dirty when Wave 4 began and Wave 4 only proved them; it did not durable-adopt their exact current bytes into its mutation surface. Replan to a no-write adoption wave using the exact SHA-256 values already observed, then rerun the focused proof. Do not modify source. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `160`
- Chain head: `407dd1e3990cec4fbc266b2d4a2e336343b34d45a602b1437588121b9a6b79b8`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
