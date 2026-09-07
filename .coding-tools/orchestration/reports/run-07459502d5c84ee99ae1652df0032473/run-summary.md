# Orchestration Run Summary

- Run: `07459502d5c84ee99ae1652df0032473`
- Task: `f0d793a027a243ed948af43bbfc8de47`
- Objective: Implement the prepared Natural HR Problem Lineage activation fix. Requirements: (1) problem_lineage_activation.py must be retry-idempotent when a guarded stopped-runtime retry sees schema already at v12, while still enforcing exact snapshot/logical hashes and full postflight checks; (2) introduce an exact typed maintenance reason problem_lineage_schema_v12 and a generalized workspace-maintenance predicate in Python restart-ticket/coordination code so an authorized target workspace is preserved only for exact-stale or PRL-v12 maintenance, with malformed prefix variants rejected; (3) mirror that reason/target validation in runtimeOrchestrator.js without weakening ordinary restart checkpoint semantics; (4) in fullCleanActivation.js run the existing scripts/activate_problem_lineage.py preflight and activation only after the old canonical runtime is stopped, derive fresh exact snapshot and logical hashes from preflight, pass them into --activate --runtime-stopped, validate schema 12/postflight receipt, record bounded verification evidence, and make Recovery Host retry safe; (5) preserve existing exact-stale maintenance and all unrelated dirty work; (6) do not manually edit SQLite, do not backfill historical Problems/outcomes, do not add a public tool. Add focused Python and Node tests for exact PRL maintenance target propagation, malformed-reason rejection, already-v12 retry, and stopped-runtime activation sequencing/receipt.
- Status: **active**
- Started: `2026-09-07T10:44:47.463Z`
- Finished: `None`

## Outcome metrics

- Waves: **7**
- Route decisions: **2**
- Failures observed: **6**
- REPLAN transitions: **6**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `e554e600cfe94bb195bd648935bd1fe3` | 1 | `run_initial_objective` | `mcp_only` | `58dfd3093d7a05f6999fe93e15c94050aa51d204` | replanned |
| 2 | `6a4d741d56924e83a2c0a91dec353b95` | 1 | `replan_request` | `deep_single_lane` | `58dfd3093d7a05f6999fe93e15c94050aa51d204` | replanned |
| 3 | `1fa33da5172a407282273bc6cc57ae3b` | 1 | `replan_request` | `deep_single_lane` | `58dfd3093d7a05f6999fe93e15c94050aa51d204` | replanned |
| 4 | `605dfadd28c34b66885745b3b3bc6d1b` | 2 | `replan_request` | `deep_single_lane` | `58dfd3093d7a05f6999fe93e15c94050aa51d204` | replanned |
| 5 | `a7095bc8d5a1402798d5f9b68087f6a6` | 2 | `replan_request` | `deep_single_lane` | `58dfd3093d7a05f6999fe93e15c94050aa51d204` | replanned |
| 6 | `0be8558c43c343cb9b498730592907d3` | 3 | `replan_request` | `deep_single_lane` | `58dfd3093d7a05f6999fe93e15c94050aa51d204` | replanned |
| 7 | `a419b79ef5ae419a8c5bf2038817e644` | 4 | `replan_request` | `auto` | `58dfd3093d7a05f6999fe93e15c94050aa51d204` | active |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 43437 | `auto` | `deterministic` | roi_gate_hold_insufficient_paired_evidence |
| 43485 | `sol_xhigh` | `sol_xhigh` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 43451 | `CHECK_FAILED` | `PROVING` |  |
| 43456 | `COMPLETION_READINESS_BLOCKED` | `PREFLIGHT` |  |
| 43461 | `COMPLETION_READINESS_BLOCKED` | `PREFLIGHT` |  |
| 43468 | `COMPLETION_READINESS_BLOCKED` | `PREFLIGHT` |  |
| 43475 | `COMPLETION_READINESS_BLOCKED` | `PREFLIGHT` |  |
| 43492 | `CANDIDATE_MODEL_NOT_COMPLETED` | `ROUTED` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `83`
- Chain head: `31e650dafcc0a85a59b6e441ea67f0f1a504166c56464f75bf72edbf00015f59`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
