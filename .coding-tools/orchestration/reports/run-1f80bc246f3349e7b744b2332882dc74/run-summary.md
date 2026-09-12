# Orchestration Run Summary

- Run: `1f80bc246f3349e7b744b2332882dc74`
- Task: `9f284169c83e4d6e9e5c50e6242257e8`
- Objective: Resolve Problem prl-semantic-localization-provider-health-20260912 revision 1 from current source/runtime state. Diagnose the causal break between configured semantic localization availability and executable native provider/LSP resource health. Trace workspace_context semantic_localization projection, agent_workflow semantic-first localization, native semantic provider call, LSP/resource admission/health reporting, SEMANTIC_PROVIDER_CALL_FAILED and LSP_RESOURCE_STATUS_FAILED translation, and bounded text fallback. Identify the smallest causal repair and exact focused oracle that proves: healthy known-symbol query is semantic-handled; unavailable/unhealthy provider is reported truthfully with actionable health reason; bounded text fallback remains correct; HEAVY admission/host-pressure guards are not weakened; post-fix telemetry records a semantic-handled query. Preserve unrelated dirty WIP. No restart, commit, push, clean, reset, package, release, or deploy.
- Status: **aborted**
- Started: `2026-09-12T11:38:31.707Z`
- Finished: `2026-09-12T11:47:00.591Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **0**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `ed3d6623a3534b1e8b11855e838398b7` | 1 | `run_initial_objective` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 51886 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `52`
- Chain head: `06604aae82455bf81c6b085c6abd7fe140d98a44b5e1bf675ce75142ad4040a0`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
