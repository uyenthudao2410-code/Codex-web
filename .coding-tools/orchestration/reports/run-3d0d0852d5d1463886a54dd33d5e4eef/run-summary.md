# Orchestration Run Summary

- Run: `3d0d0852d5d1463886a54dd33d5e4eef`
- Task: `cad8a09779754bbb88228a07a1124b4b`
- Objective: Natural Codex-web bugfix: make lifecycle census projection source selection fail closed against stale unscoped global task-state. When valid contextual task projections exist, they must be evaluated instead of being masked by any non-empty global projection; preserve global fallback only when contextual projections are absent, preserve existing lifecycle classifications/read-only invariants, and add a focused regression for stale global ACCEPTING versus contextual CHECKPOINTED.
- Status: **aborted**
- Started: `2026-09-09T06:57:25.180Z`
- Finished: `2026-09-09T07:05:24.693Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **0**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **0**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `e6b35e273828461cbd476ce26d645f9a` | 1 | `run_initial_objective` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `16`
- Chain head: `0ae2120b76cb3b01ff474f4fb58d209ce68283fdf454876c9b0430d9130f4c8e`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
