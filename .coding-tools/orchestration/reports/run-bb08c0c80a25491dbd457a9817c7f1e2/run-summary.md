# Orchestration Run Summary

- Run: `bb08c0c80a25491dbd457a9817c7f1e2`
- Task: `8e0a643227174dd3acfb1a1e27c04bcd`
- Objective: T2.1 TruthSnapshot integration bugfix only: fix the authenticated orchestration snapshot crash caused by passing unsupported keyword `wave=` into `OrchestrationLedger.wave_objective_provenance()`, whose accepted API takes `wave_id`. Change only that call-site and strengthen test_truth_snapshot with an active-wave regression that executes the same helper path. No other behavior, public tools, authority, UI, restart, package, release, or deployment changes.
- Status: **aborted**
- Started: `2026-08-21T08:01:23.508Z`
- Finished: `2026-08-21T20:34:49.028Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **1**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `5a63cd744ad54b71bee4f3b928ae7196` | 1 | `run_initial_objective` | `mcp_only` | `9eb05072e54ffca9576e23c2d4a4f4e14034bddc` | replanned |
| 2 | `38c1c11276f649d285014715ef9a588d` | 2 | `replan_request` | `mcp_only` | `9eb05072e54ffca9576e23c2d4a4f4e14034bddc` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 26253 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 26265 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `25`
- Chain head: `9477966f921405f9a6f7493d1814c9cfbaba5cf0bbe0004dc9a6729b012a8a9d`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
