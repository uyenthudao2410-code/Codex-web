# Orchestration Run Summary

- Run: `7f02ca97c017448098364c1d2f7cd14f`
- Task: `26ea3e81b1774cc793bc75fc6e90b2df`
- Objective: Read-only final audit after the accepted canonical Operations Overview patch. Determine whether any visible token/cost field in the same Operations Overview page still consumes the dead legacy measuredUsage aggregation or estimated model-visible bytes without an explicit ESTIMATED label. Focus on secondary model/fleet table, legacy measuredUsage references, modelBreakdown, toolBreakdown, and all calls to renderModelTable/renderFleetTable. If no user-visible inconsistency remains, do not change source. If a residual path exists, identify the smallest cleanup patch and focused oracle. No restart/commit/push.
- Status: **aborted**
- Started: `2026-08-19T10:00:38.537Z`
- Finished: `2026-08-19T10:03:21.646Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **0**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **0**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `b8ead2c5b672439a93c15dcb1d6d91a1` | `mcp_only` | `930d3e1e67f2b413aa32d5da99d1a01d22d0bddc` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `25`
- Chain head: `9eda18cd4c5aa9b80c296937ca77071bda02aa87700e09b7b066fc2901f7868e`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
