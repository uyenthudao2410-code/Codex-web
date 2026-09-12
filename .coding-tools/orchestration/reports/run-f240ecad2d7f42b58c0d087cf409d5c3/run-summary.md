# Orchestration Run Summary

- Run: `f240ecad2d7f42b58c0d087cf409d5c3`
- Task: `8829a48b78164c3ca7d2af325c806c52`
- Objective: Fix the remaining stage-latency reporter cohort/binding defect for Problem prl-8a57cc01ad8abd9f56a14c8bd605229d revision 1. Canonical live ledger already proves a post-activation accepted natural RUN e94e9cadac0b40708f2274fa24ec28fb / wave 19d9574db27547faa36ed20e6af3a1a2 emitted an acceptance anchor plus same-clock controller_processing and acceptance_wait spans, yet report_stage_latency_attribution with explicit source_head 7bc1caee37107a15e74eb078b52fe314e5fa33ab reports accepted_current_source_runs=0, observed_runs=0, source_head_used_for_current_cohort=null, and HOST_BINDING_COVERAGE_BELOW_THRESHOLD. Diagnose the exact consumer selection/binding cause and prepare the smallest fail-closed fix so explicit immutable source_head can select matching latest waves even on a dirty worktree, while host binding remains exact and missing evidence remains unknown. Do not weaken the 0.9 host-binding threshold, do not infer by timestamp proximity, do not backfill history, do not touch workflow_tools.py, and do not change EOCL/Problem authority.
- Status: **accepted**
- Started: `2026-09-12T06:48:28.994Z`
- Finished: `2026-09-12T06:51:28.978Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **3**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `1c641d5bcf224a4ea3428abfa44421bd` | 1 | `run_initial_objective` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| f80a3d0317474dbdb293488997238f21 | 1c641d5bcf224a4ea3428abfa44421bd | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | 066befe8dd4c3a0ad6f2f9381da71b814eaa284446df84b651c4354229043c61 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 50412 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `47`
- Chain head: `1b1ae0ee55b106579f19ae5b1e2061f1568ce8bf8bbb216b20fec7703f964ef7`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
