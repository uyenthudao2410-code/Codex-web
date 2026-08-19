# Orchestration Run Summary

- Run: `913e692f116c4d31963046197a97083c`
- Task: `0a5e75818f8f44ae99a23d8f4534dee0`
- Objective: Fix the final residual token-metrics inconsistency in Operations Overview only. Main KPI/trend/donut canonical usage_analytics remain unchanged. Secondary operational lane/model/fleet tables must not claim noncanonical delegations+lanes overlays as MEASURED token truth. Make modelBreakdown an explicit ESTIMATED/SCENARIO view from performance trace only, remove the dead legacy measuredUsage aggregator, label model/fleet token and cost columns as ESTIMATED/SCENARIO, and ensure no visible secondary token/cost number can be mistaken for canonical measured billing. Preserve lane operational state/calls and all unrelated WIP. Add focused regression. No restart/commit/push.
- Status: **accepted**
- Started: `2026-08-19T10:03:54.336Z`
- Finished: `2026-08-19T10:08:14.138Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **2**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `48d27d035f614b8290c952de72572e7b` | `mcp_only` | `930d3e1e67f2b413aa32d5da99d1a01d22d0bddc` | replanned |
| 2 | `85e2caa364e04235a20819ac18500a2b` | `mcp_only` | `930d3e1e67f2b413aa32d5da99d1a01d22d0bddc` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 0e8fce13183c4cd78f62bd13bdc16ccd | 85e2caa364e04235a20819ac18500a2b | accepted | 930d3e1e67f2b413aa32d5da99d1a01d22d0bddc | d2fac63c441dd4bdee47b889035964a58f1350318e16a1c3398d3a3816069282 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 21492 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 21511 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 21504 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `55`
- Chain head: `673292e148d6a3da91956c7d87bc634b5e09b05daa577acf2a168d16b914f303`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
