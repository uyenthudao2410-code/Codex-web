# Orchestration Run Summary

- Run: `f1675a1cc4f04482bec7087b16e2c2c6`
- Task: `478937a3b3dd4c9393e33319a7c15d04`
- Objective: Consolidate the exact current runtime-source bytes needed to unblock accepted-code activation without modifying file contents or weakening source authority. Dirty runtime surface is exactly 12 files; workspace scheduling resources are currently quiescent. Prepare a bounded EOCL wave that may exact-adopt those 12 existing dirty bytes, run broad recovery/activation/continuation regressions, then submit the current recovery_host and coding_mcp component source as SHA-attested acceptance evidence. No restart until accepted/checkpointed; no full Problem resolution claim.
- Status: **accepted**
- Started: `2026-09-15T06:17:11.887Z`
- Finished: `2026-09-15T06:43:21.033Z`

## Outcome metrics

- Waves: **6**
- Route decisions: **3**
- Failures observed: **5**
- REPLAN transitions: **5**
- Proof stages: **4**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `55d118adff17442bbeb7cab5ba5f7a89` | 1 | `run_initial_objective` | `mcp_only` | `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6` | replanned |
| 2 | `6e329a6dffac44f18f5d159c649f6191` | 2 | `replan_request` | `mcp_only` | `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6` | replanned |
| 3 | `3d8414ba32ef4cc1b3e8572e11d01519` | 3 | `replan_request` | `mcp_only` | `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6` | replanned |
| 4 | `20ed4227348343469b19e9c50eff30c0` | 4 | `replan_request` | `mcp_only` | `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6` | replanned |
| 5 | `24074fe1254e4b148de2e99bdaa22d5f` | 4 | `replan_request` | `mcp_only` | `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6` | replanned |
| 6 | `1bef8075beb542339283f5222b0d7a53` | 5 | `replan_request` | `mcp_only` | `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 90bcf7e890dd4a32beee67501732ec57 | 1bef8075beb542339283f5222b0d7a53 | accepted | a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6 | e2af7a520f6ac1dd1ae7ed382628dd851ee3eea98d28eb386aa66efc3479322c | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 56808 | `deterministic` | `deterministic` | explicit_request |
| 56876 | `deterministic` | `deterministic` | explicit_request |
| 56923 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 56787 | `BASE_DRIFT` | `PREFLIGHT` |  |
| 56821 | `PERMISSION_REQUIRED` | `PROVING` |  |
| 56840 | `BASE_DRIFT` | `PREFLIGHT` |  |
| 56866 | `BASE_DRIFT` | `PREFLIGHT` |  |
| 56912 | `SOL_REJECTED` | `ACCEPTING` | Acceptance failed closed because pre-existing dirty acceptance paths must be present in the durable mutation surface of the same accepted wave. Replan one atomic wave that exact-adopts the same 12 unchanged bytes and runs the same proven checks before acceptance; this is an acceptance-lineage correction, not a source defect. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `152`
- Chain head: `e99930fbaa044000e85e353d9bb7eccc57c32b92ac2048909600f90b4637be70`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
