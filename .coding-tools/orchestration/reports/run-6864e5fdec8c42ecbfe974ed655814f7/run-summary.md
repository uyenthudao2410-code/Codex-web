# Orchestration Run Summary

- Run: `6864e5fdec8c42ecbfe974ed655814f7`
- Task: `8f381b77cda24910ade1557f933d3df7`
- Objective: Add a bounded historical_observational/evidence-completeness projection as a separate evaluation-domain module, avoiding DB migration, new public tools, historical mutation, or P4 backfill. Reuse durable ledger + solution-shadow/economics evidence. evaluation_report.py should only attach the projection to current_ledger_baseline_report and per-run evaluation_plane_report. Per-run fields: workspace_identity, host_turn_correlation, provenance, solution_shadow, pre_write_order, actual_patch_surface, proof, quality_outcome, cost_usage, cross_project_contaminated, promotion_eligible, cohort. Legacy/unenrolled terminal organic runs become historical_observational and are forbidden from P4 predictor validation; benchmark/synthetic retain explicit cohort; active incomplete runs are collecting. UNKNOWN cost/contamination stays UNKNOWN. Add a dedicated focused test module. Preserve unrelated work and 8-tool surface. No commit/push/restart.
- Status: **accepted**
- Started: `2026-08-19T07:39:38.836Z`
- Finished: `2026-08-19T07:40:12.176Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `c13bf82a3a484774b8c90c84e6289582` | `mcp_only` | `359a5f231e1950e8d97303e0d2b798984c145fe6` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 3b44df8cb4d14952bac2154b7adcc172 | c13bf82a3a484774b8c90c84e6289582 | accepted | 359a5f231e1950e8d97303e0d2b798984c145fe6 | 38f5d47c6f6847b83975b234504c65427fc4690a33455d88f48eef7db2c5e496 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 20736 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `21`
- Chain head: `a9de139695f8b333255bd1ada135a2709c3f4a5df99a3ac7594db566295e2573`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
