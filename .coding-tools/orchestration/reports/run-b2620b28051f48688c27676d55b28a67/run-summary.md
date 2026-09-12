# Orchestration Run Summary

- Run: `b2620b28051f48688c27676d55b28a67`
- Task: `16b403493a42453c92d59d8616b4f542`
- Objective: Correct the PRL C4 full-claim mechanics canary so it measures actual immutable full_problem outcome claims, uses the canonical one-per-RUN exact primary Problem revision binding across replan waves, and preserves exact-wave manifest/proof/checkpoint/bridge verification. Add focused regressions for intent-only exclusion, valid replan claim coverage, and mismatched RUN binding failure. Do not backfill historical ledger data or modify schema/workflow producer semantics.
- Status: **accepted**
- Started: `2026-09-12T07:57:01.642Z`
- Finished: `2026-09-12T08:06:49.860Z`

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
| 1 | `af46bf48ed8d4736bd82ed88cd56c764` | 1 | `run_initial_objective` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| c9b6e72b9b434ddb880125bc6bf38847 | af46bf48ed8d4736bd82ed88cd56c764 | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | 703e55a4b504f32068d9f3201b47ba5212a68c62d010653dd8707b28d79e23c5 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 50709 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `49`
- Chain head: `b8e6914cf550cdca25107201de59b2e93f6e6ffb47f9443eeaeda5d4aa75dbf9`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
