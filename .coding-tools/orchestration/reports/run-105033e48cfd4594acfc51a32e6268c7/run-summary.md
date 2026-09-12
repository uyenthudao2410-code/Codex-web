# Orchestration Run Summary

- Run: `105033e48cfd4594acfc51a32e6268c7`
- Task: `cc4c928825da4ac9bf29f2cc18dcf2dc`
- Objective: Natural #5: fix the prepared-workflow exact-binding defect that rejects execute after run -> REPLAN -> new prepare wave because validate_prepared_workflow_binding reads run-level metadata.phase instead of authoritative active prepared-wave state. Preserve all exact RUN/WAVE/task/workflow/state fail-closed checks and historical metadata. Prepare only; no mutation yet.
- Status: **aborted**
- Started: `2026-09-09T09:41:32.810Z`
- Finished: `2026-09-09T09:45:43.097Z`

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
| 1 | `4339b0f655554e73be978a6b6d8dacb5` | 1 | `run_initial_objective` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | aborted |

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
- Events checked: `24`
- Chain head: `4aca67866c8b9ea353823ec37c680e3dbffa53eb56e653700d7eafe191aea489`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
