# Orchestration Run Summary

- Run: `a5670a7d4f814daca7ca44319b0c52ed`
- Task: `45fa8cf42f43442e806072e5cb4ca268`
- Objective: Final evidence-gap analysis for Problem prl-terminal-projection-clear-restart-drift-20260912 revision 2. The source repair is already accepted and activated, and strict post-terminal semantic probes are clean inside the historical 60-second lease window. Inspect only the official controlled-restart preflight path and focused tests to determine the smallest non-restart proof needed for criterion restart_preflight_race_safe. Also identify the exact focused tests that jointly cover the remaining Problem criteria so a later full_problem verification wave can map all 7 criteria without inventing evidence. Read-only only; no source mutation, restart, ledger-history edit, commit, push, clean, reset, package, release, or deploy.
- Status: **accepted**
- Started: `2026-09-12T10:47:41.702Z`
- Finished: `2026-09-12T11:05:58.469Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `d71868c873f34a5a89eb49fcdf168bcd` | 1 | `run_initial_objective` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| a93c7dff4fe4495880eca2fdb735d4af | d71868c873f34a5a89eb49fcdf168bcd | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | 47e42aff3760a30ba471620d343faa4178cb81bee66510722e43ba58a808cd17 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 51704 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `59`
- Chain head: `43a30e0573c7864981426d7e6fe37b3c23952c3f81520a188743220b14c79a84`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
