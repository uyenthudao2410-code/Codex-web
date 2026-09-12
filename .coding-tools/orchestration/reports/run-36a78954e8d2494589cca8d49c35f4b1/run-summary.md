# Orchestration Run Summary

- Run: `36a78954e8d2494589cca8d49c35f4b1`
- Task: `61acf49260c54581b881f36ad6d4a74e`
- Objective: Create one additional no-source-write convergence checkpoint for the exact 40-path remaining accepted-code component boundary at current HEAD, relying on acceptedReceiptUnion across accepted checkpoints so Recovery Host can recompute component eligibility without reopening the prior accepted convergence run.
- Status: **aborted**
- Started: `2026-09-08T18:54:06.245Z`
- Finished: `2026-09-08T18:55:18.026Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **2**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `6533698b6b9e46b3a7fbfe60881f69c7` | 1 | `run_initial_objective` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 44464 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 44486 | `SOL_REJECTED` | `ACCEPTING` | Control-plane orchestration misbinding: this execute unexpectedly created/bound a second RUN instead of continuing the operator-authorized single additional convergence RUN 120a6aa9273349e9841aac519103f06d. Do not accept this candidate; preserve all source bytes and return to the intended existing RUN lineage. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `31`
- Chain head: `9063334516addd06f3796276b71426dfb9cff51794b204b347fe53e6fc48e959`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
