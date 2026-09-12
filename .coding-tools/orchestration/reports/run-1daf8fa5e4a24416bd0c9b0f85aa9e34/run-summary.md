# Orchestration Run Summary

- Run: `1daf8fa5e4a24416bd0c9b0f85aa9e34`
- Task: `5cae3887a87c416ba18a604469f7be92`
- Objective: Natural #21 diagnosis and repair preparation. Determine exactly why the live Codex-web runtime reports 52 unresolved stale orchestration runs and task_orchestration_projection_reconciled=false. Inspect only the supported stale-reconciliation/lifecycle path, distinguish safely reconcilable stale residue from runs that must remain typed blockers, and prepare the smallest causal fix without deleting ledger history, touching accepted/checkpointed semantics, restarting runtime, or modifying unrelated dirty work.
- Status: **aborted**
- Started: `2026-09-10T09:40:13.848Z`
- Finished: `2026-09-10T10:30:39.792Z`

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
| 1 | `1546aa64de2f4bd9a2af16de21dfac40` | 1 | `run_initial_objective` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | aborted |

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
- Events checked: `18`
- Chain head: `9ef232fd40338119f48a29db175b1199d2e8daffa3d3eb7137fcf6153153b31f`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
