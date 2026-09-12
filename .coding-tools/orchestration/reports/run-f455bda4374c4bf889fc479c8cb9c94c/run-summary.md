# Orchestration Run Summary

- Run: `f455bda4374c4bf889fc479c8cb9c94c`
- Task: `4c992735740246399d5ab44131502607`
- Objective: Natural #20 candidate diagnostic only: investigate the remaining causal-unknown P2 cohort after Natural #19 closure, prioritizing CHECK_FAILED and BUILD_VERIFICATION_FAILED. Determine from existing immutable ledger facts and exact failure_observed-to-wave_replanned pairing whether any of these generic failures have narrow high-confidence durable replan reasons that support a semantic repair-cause label. Do not open a Problem, do not change source, do not weaken fail-closed attribution, and keep process nonzero outcome non-causal by itself.
- Status: **aborted**
- Started: `2026-09-10T08:28:52.140Z`
- Finished: `2026-09-10T08:55:11.913Z`

## Outcome metrics

- Waves: **4**
- Route decisions: **3**
- Failures observed: **3**
- REPLAN transitions: **3**
- Proof stages: **5**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `8cbd18807961496eae1d07b97a7ad999` | 1 | `run_initial_objective` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | replanned |
| 2 | `9b49b027d76a4a9cb7d218676778b100` | 2 | `replan_request` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | replanned |
| 3 | `e3b52b2347844408811cab3a036b1a74` | 3 | `replan_request` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | replanned |
| 4 | `05bf811741d84e1eaf3de42c1733b552` | 4 | `replan_request` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 47309 | `deterministic` | `deterministic` | explicit_request |
| 47339 | `deterministic` | `deterministic` | explicit_request |
| 47367 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 47330 | `SOL_REJECTED` | `ACCEPTING` | Wave 1 established the aggregate baseline and confirmed the reporter has no per-occurrence detail mode, but that evidence is insufficient to answer the Natural #20 diagnostic objective. The remaining 42 generic CHECK_FAILED/BUILD_VERIFICATION_FAILED events already pass through the existing high-confidence durable-replan fallback and remain unclassified, so a second read-only wave must inspect the exact paired failure_observed and wave_replanned records before any new causal rule or source change can be justified. |
| 47358 | `CHECK_FAILED` | `PROVING` |  |
| 47381 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `126`
- Chain head: `95dbefd4b89c56d59d1248e254ced9095acaca4fdbc0f70baaf619481bec7b52`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
