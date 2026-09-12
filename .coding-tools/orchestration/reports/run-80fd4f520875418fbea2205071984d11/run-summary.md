# Orchestration Run Summary

- Run: `80fd4f520875418fbea2205071984d11`
- Task: `5cfc5996831b430cbe2fbef4c3ca6150`
- Objective: Resolve Problem prl-semantic-localization-provider-health-20260912 revision 1 with the localized causal repair. Normalize absolute caller semantic scopes to project-relative only when the resolved target is inside the bound workspace; keep outside/traversal/NUL scopes fail-closed. Add truthful effective semantic provider health that distinguishes configured binding from executable resource health, and use it for full workspace_context capability reporting. Preserve existing semantic-first admission and bounded text fallback; do not weaken HEAVY concurrency/host-pressure guards and do not modify the Rust bridge. Add focused regression tests for absolute-in-workspace normalization, outside rejection, configured-but-unhealthy truthful reporting, bounded text fallback, and healthy semantic handling. Preserve unrelated dirty WIP. No restart, commit, push, clean, reset, package, release, or deploy.
- Status: **active**
- Started: `2026-09-12T11:50:37.253Z`
- Finished: `None`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **2**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `f3ff3ae3dbc0449496a1696c1f879fbf` | 1 | `run_initial_objective` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | replanned |
| 2 | `35f014514ac846f1a63e4ae1d94769d9` | 2 | `replan_request` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | active |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 51899 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 51930 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 51919 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `59`
- Chain head: `2258492c5c9e13cffda76a5993e036e39b441dfb0ae5db8a2eadd2835e536039`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
