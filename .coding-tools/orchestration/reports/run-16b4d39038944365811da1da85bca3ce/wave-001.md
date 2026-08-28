# Orchestration Wave 1

- Run: `16b4d39038944365811da1da85bca3ce`
- Wave: `71946b7c1fcc4d0eb39c05921eb61166`
- Objective: Resolve the long-standing Electron UI lag/freeze and dashboard observability failure causally, on the current dirty worktree without reverting or touching unrelated activation/recovery WIP. Keep full /__control/orchestration compatibility for non-hot-path consumers, but remove it from frequent Overview refresh. Required implementation outcome: (1) /__control/orchestration/live becomes a genuinely bounded read hot path: no stale/task reconciliation, no full ledger hash-chain verification, no full-history event/proof/checkpoint scans, and no read-triggered controller-lease maintenance write; return only current authoritative control/runtime facts with bounded recent data and explicit integrity status such as unverified_on_live_path rather than pretending verified. (2) Add a dedicated /__control/orchestration/analytics read endpoint for Dashboard. It returns current usage_analytics + operations_analytics and freshness/generated_at metadata without control-plane reconciliation. Make operations_analytics scale with the requested UTC window: SQL must filter terminal runs by window at the database query, not scan all terminal history; remove accepted-run N+1 behavior where practical via bounded/batched SQL/projections, or otherwise prove query work is independent of historical runs outside the window. Preserve unknown_not_zero and measured/derived provenance semantics. (3) Electron main/preload expose a separate dashboardAnalytics IPC/API with a slower timeout/cadence; existing orchestration APIs remain compatible. (4) Overview has one timer owner only: Control Center owns the periodic pulse; Dashboard must not schedule its own recursive poll loop. Dashboard refresh on pulse uses liveOrchestration for control state and dashboardAnalytics on a slow ~30s cadence, and it must continue to refresh analytics while orchestration is busy instead of freezing stale KPIs. Avoid duplicate full snapshot/performance reads when unchanged where feasible. (5) Fix renderChart listener accumulation: repeated renderChart calls must not add unbounded mousemove/mouseleave listeners; bind stable handlers once or explicitly remove/replace them. Add a regression capable of detecting listener-growth semantics. (6) Precompute lane/controller attribution windows once per modelBreakdown render rather than rebuilding them per record. (7) Remove fabricated Fleet latency/trend telemetry. If there is no measured latency/trend for a model, show em dash/UNKNOWN rather than synthetic values; never present row-index-generated values as observations. (8) Update focused tests so they assert the new architecture rather than codifying old dual-poll/full-orchestration behavior. Acceptance proof must include tests/dashboard-analytics.test.js, tests/control-center-manager.test.js, tests/control-panel.test.js, resources/coding-tools-mcp/tests/test_operations_analytics.py, plus git diff --check. Add/strengthen tests for live hot-path exclusions, analytics endpoint/API, SQL-window boundedness, single Overview timer owner, listener lifecycle, busy analytics freshness, and no fabricated latency/trend. Do not restart runtime, do not activate, do not push/release, do not modify .coding-tools manually, and do not revert concurrent work. If exact runtime smoke needs restart, stop at that gate after source proof.
- Objective revision: `1`
- Objective SHA-256: `6ce0b7b91f0457184b5ad6065245f2065d6b2748d5deacc8f3f2efaf7dfac527`
- Objective source: `run_initial_objective`
- Mode: `deep_single_lane`
- Base HEAD: `148de18795787e820ef1bc51d0f2591052d24238`
- Worktree fingerprint: `593ed7a9accc002d2950213d221bb13e7c985742c4e8af910ee0ef8bd1dcdcaa`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| 7937ca63e0e449838a4bd8c2a3610b6f | CODEX:sol_xhigh | sol_xhigh | sol_xhigh | gpt-5.6-sol | xhigh | blocked |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 31723 | 2026-08-28T09:24:38.240Z | run_started |  | PREFLIGHT |  |
| 31726 | 2026-08-28T09:24:39.477Z | observation_span_recorded |  |  |  |
| 31727 | 2026-08-28T09:24:39.814Z | solution_shadow_recommended |  |  |  |
| 31728 | 2026-08-28T09:24:41.789Z | observation_span_recorded |  |  |  |
| 31729 | 2026-08-28T09:24:42.143Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 31730 | 2026-08-28T09:24:42.824Z | managed_process_admitted |  |  | owner=default |
| 31731 | 2026-08-28T09:24:43.415Z | managed_process_started |  |  | owner=default |
| 31732 | 2026-08-28T09:24:46.670Z | managed_process_terminal |  |  | owner=default |
| 31733 | 2026-08-28T09:24:47.007Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 31734 | 2026-08-28T09:24:47.317Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 31735 | 2026-08-28T09:24:47.540Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 31736 | 2026-08-28T09:24:47.785Z | route_selected | READY | READY | reason=explicit_request; requested=sol_xhigh; resolved=sol_xhigh |
| 31737 | 2026-08-28T09:24:48.050Z | state_transition | READY | ROUTED | reason=route_selected |
| 31738 | 2026-08-28T09:24:48.355Z | observation_span_recorded |  |  |  |
| 31739 | 2026-08-28T09:24:48.674Z | delegation_started | ROUTED | ROUTED | authority_owner=CODEX:sol_xhigh |
| 31740 | 2026-08-28T09:24:48.878Z | model_dispatch_started | ROUTED | ROUTED |  |
| 31741 | 2026-08-28T09:24:49.753Z | model_dispatch_finished | ROUTED | ROUTED | failure_class=PROMPT_TOO_LARGE; status=error |
| 31742 | 2026-08-28T09:24:50.179Z | delegation_finished | ROUTED | ROUTED | reason=PROMPT_TOO_LARGE; status=blocked |
| 31743 | 2026-08-28T09:24:50.480Z | failure_observed | ROUTED | ROUTED | failure_class=PROMPT_TOO_LARGE |
| 31744 | 2026-08-28T09:24:50.723Z | state_transition | ROUTED | REPLAN | reason=PROMPT_TOO_LARGE; failure_class=PROMPT_TOO_LARGE |
| 31745 | 2026-08-28T09:24:51.158Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| - | - | - | - | - | - |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `67`
- Chain head: `3a962f8d62b75473f4d5a48d29feeb4de4d3d1afdd790731a04f5e03aaef42b3`
