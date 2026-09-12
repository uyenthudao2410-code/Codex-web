# Orchestration Run Summary

- Run: `9d078460105e456ebc5f108fbafc6ee6`
- Task: `ec635f22600d4dd589c22cf9d2e31574`
- Objective: Diagnose why exact-ID stale-run reconciliation preflight for RUNs c9a67701e8554ce2b21e3117212797f6, 9c633d2185d84ed4b86fa60f6bfb38ef, and 6559ba677eb742139c6f111e760edc78 fails with unbound_live_resource_residues,managed_job_residue even though task_control audit reports each target run quiescent with zero active commands/claims. Determine whether the preflight is intentionally global, incorrectly scopes unrelated current jobs/resources, or is detecting real canonical writer residue. Also identify the fourth threshold-sensitive census candidate and explain why runtime unresolved stale projection reports only three. Read-only diagnosis only; do not mutate, reconcile, restart, commit, push, clean, or reset.
- Status: **accepted**
- Started: `2026-09-12T07:15:26.915Z`
- Finished: `2026-09-12T07:19:54.512Z`

## Outcome metrics

- Waves: **3**
- Route decisions: **3**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **2**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `5f75666681774698b15b9e4929968f5a` | 1 | `run_initial_objective` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | replanned |
| 2 | `a8b08d985225402db7d8c2b9458e7d80` | 2 | `replan_request` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | replanned |
| 3 | `6afbc1f339fe4fc3aa613ca9e1074543` | 3 | `replan_request` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| c1ecbf6e437d430a8f6350b4b006a679 | 6afbc1f339fe4fc3aa613ca9e1074543 | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | d8c3b09db833388e68332484bf2a300d7287328a374d1c902fb5418bf37229ab | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 50495 | `deterministic` | `deterministic` | explicit_request |
| 50511 | `deterministic` | `deterministic` | explicit_request |
| 50535 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 50501 | `INVALID_ARGUMENT` | `EXECUTING` |  |
| 50525 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `70`
- Chain head: `ddf92bba54513dccad8af47a19ba238ff2320b38af3e74e70743eb98b5cf8062`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
