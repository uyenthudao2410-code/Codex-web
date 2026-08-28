# Orchestration Run Summary

- Run: `16b4d39038944365811da1da85bca3ce`
- Task: `d335195e3e5744dca220478ff73ef4bd`
- Objective: Resolve the long-standing Electron UI lag/freeze and dashboard observability failure causally, on the current dirty worktree without reverting or touching unrelated activation/recovery WIP. Keep full /__control/orchestration compatibility for non-hot-path consumers, but remove it from frequent Overview refresh. Required implementation outcome: (1) /__control/orchestration/live becomes a genuinely bounded read hot path: no stale/task reconciliation, no full ledger hash-chain verification, no full-history event/proof/checkpoint scans, and no read-triggered controller-lease maintenance write; return only current authoritative control/runtime facts with bounded recent data and explicit integrity status such as unverified_on_live_path rather than pretending verified. (2) Add a dedicated /__control/orchestration/analytics read endpoint for Dashboard. It returns current usage_analytics + operations_analytics and freshness/generated_at metadata without control-plane reconciliation. Make operations_analytics scale with the requested UTC window: SQL must filter terminal runs by window at the database query, not scan all terminal history; remove accepted-run N+1 behavior where practical via bounded/batched SQL/projections, or otherwise prove query work is independent of historical runs outside the window. Preserve unknown_not_zero and measured/derived provenance semantics. (3) Electron main/preload expose a separate dashboardAnalytics IPC/API with a slower timeout/cadence; existing orchestration APIs remain compatible. (4) Overview has one timer owner only: Control Center owns the periodic pulse; Dashboard must not schedule its own recursive poll loop. Dashboard refresh on pulse uses liveOrchestration for control state and dashboardAnalytics on a slow ~30s cadence, and it must continue to refresh analytics while orchestration is busy instead of freezing stale KPIs. Avoid duplicate full snapshot/performance reads when unchanged where feasible. (5) Fix renderChart listener accumulation: repeated renderChart calls must not add unbounded mousemove/mouseleave listeners; bind stable handlers once or explicitly remove/replace them. Add a regression capable of detecting listener-growth semantics. (6) Precompute lane/controller attribution windows once per modelBreakdown render rather than rebuilding them per record. (7) Remove fabricated Fleet latency/trend telemetry. If there is no measured latency/trend for a model, show em dash/UNKNOWN rather than synthetic values; never present row-index-generated values as observations. (8) Update focused tests so they assert the new architecture rather than codifying old dual-poll/full-orchestration behavior. Acceptance proof must include tests/dashboard-analytics.test.js, tests/control-center-manager.test.js, tests/control-panel.test.js, resources/coding-tools-mcp/tests/test_operations_analytics.py, plus git diff --check. Add/strengthen tests for live hot-path exclusions, analytics endpoint/API, SQL-window boundedness, single Overview timer owner, listener lifecycle, busy analytics freshness, and no fabricated latency/trend. Do not restart runtime, do not activate, do not push/release, do not modify .coding-tools manually, and do not revert concurrent work. If exact runtime smoke needs restart, stop at that gate after source proof.
- Status: **active**
- Started: `2026-08-28T09:24:36.730Z`
- Finished: `None`

## Outcome metrics

- Waves: **4**
- Route decisions: **3**
- Failures observed: **3**
- REPLAN transitions: **3**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `71946b7c1fcc4d0eb39c05921eb61166` | 1 | `run_initial_objective` | `deep_single_lane` | `148de18795787e820ef1bc51d0f2591052d24238` | replanned |
| 2 | `38b6b2cbdea048588d1bb85d4dcb513f` | 2 | `replan_request` | `deep_single_lane` | `148de18795787e820ef1bc51d0f2591052d24238` | replanned |
| 3 | `c72d84667a774fb1b60a7914bb79ee03` | 3 | `replan_request` | `mcp_only` | `148de18795787e820ef1bc51d0f2591052d24238` | replanned |
| 4 | `d189a74422f64bd7b7bb313c6ccd2fbe` | 4 | `replan_request` | `mcp_only` | `148de18795787e820ef1bc51d0f2591052d24238` | active |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 31736 | `sol_xhigh` | `sol_xhigh` | explicit_request |
| 31757 | `sol_xhigh` | `sol_xhigh` | explicit_request |
| 31774 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 31743 | `PROMPT_TOO_LARGE` | `ROUTED` |  |
| 31764 | `PROMPT_TOO_LARGE` | `ROUTED` |  |
| 31789 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `67`
- Chain head: `3a962f8d62b75473f4d5a48d29feeb4de4d3d1afdd790731a04f5e03aaef42b3`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
