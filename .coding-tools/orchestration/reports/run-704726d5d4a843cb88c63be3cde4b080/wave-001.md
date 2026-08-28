# Orchestration Wave 1

- Run: `704726d5d4a843cb88c63be3cde4b080`
- Wave: `ac936e2dd44149f2ac1fc38a4fbdc1a9`
- Objective: Continue the SAME canonical Dashboard lag closure RUN/WAVE lineage and implement the remaining smallest coherent A2/A3/A4 repair on the current dirty worktree. Preserve all unrelated concurrent changes and the already-good A1 live-state changes. Do not reset/revert/clean and do not touch .coding-tools/orchestration/ledger.sqlite3 manually. A2: audit the already-partial operations analytics implementation; make terminal-run selection bounded in SQL by the requested time window rather than loading retained terminal history then Python-filtering; eliminate or reduce accepted-run N+1 economics/evaluation/wave lookups into a fixed small number of queries or equivalent batch projection; keep missing_measurement_policy=unknown_not_zero; keep full /__control/orchestration compatibility unchanged; ensure GET /__control/orchestration/analytics is read-only, performs no stale/task reconciliation, returns snapshot_scope=dashboard_analytics, generated_at, window_days plus usage_analytics and operations_analytics. A3: preserve the already-present dedicated panel:dashboard-analytics IPC and preload dashboardAnalytics API; set its timeout to 10000 ms and add focused contract tests. A4: Control Center must be the sole Overview polling timer owner. On Overview, even force/manual refresh must call only api.lightweightSnapshot() + api.liveOrchestration(), never full api.snapshot()/api.orchestration(); non-Overview manual manager reads may keep full calls only if needed. Publish window CustomEvent named exactly mcp:overview-pulse carrying page, snapshot, orchestration, performance and observation time. Dashboard must consume that pulse for snapshot/live/performance, must never call api.orchestration(), api.liveOrchestration(), api.lightweightSnapshot(), or api.performanceTrace() as a polling owner, must have no recursive general polling loop, and must call api.dashboardAnalytics() independently on a staleness-based 30000 ms cadence triggered by pulses/manual refresh/initial load even while orchestration is busy. Canonical usage/operations helpers must read the dedicated analytics payload rather than full orchestration. Precompute laneWindows() and controllerWindows() once per modelBreakdown invocation and pass them into modelOf. Prevent renderChart mousemove/mouseleave listener accumulation by replacing handlers or explicitly removing previous handlers. Remove fabricated fleet latency/trend: derive average latency only from actual normalized performance trace durationMs+waitMs samples attributed to the model and label it derived/measured; otherwise render em dash; render trend as em dash unless real model-specific trend evidence exists. Update only focused tests to enforce these invariants. Do not broaden into unrelated UI copy cleanup. Do not restart, commit, push, publish, or release.
- Objective revision: `1`
- Objective SHA-256: `d133010f27c0feb0a8dbeed4e1ce67842f3d5ddb68d450a988ca7d1eeab67f8d`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `148de18795787e820ef1bc51d0f2591052d24238`
- Worktree fingerprint: `de1fc3e100e7b6d9565cd03a9dbf8bed652c07f7c0750b0610ba9dd7f92eabf9`
- Contract fingerprint: ``
- Status: **active**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 31887 | 2026-08-28T09:57:20.551Z | run_started |  | PREFLIGHT |  |
| 31888 | 2026-08-28T09:57:21.117Z | observation_span_recorded |  |  |  |
| 31889 | 2026-08-28T09:57:50.634Z | solution_shadow_recommended |  |  |  |
| 31890 | 2026-08-28T09:57:50.884Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 31891 | 2026-08-28T09:57:51.075Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 31892 | 2026-08-28T09:57:51.282Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 31893 | 2026-08-28T09:57:51.446Z | state_transition | READY | ROUTED | reason=route_selected |
| 31894 | 2026-08-28T09:57:51.915Z | observation_span_recorded |  |  |  |
| 31895 | 2026-08-28T09:57:52.829Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=3101c08263ce4ff5a393960a0dfe6eae |
| 31896 | 2026-08-28T09:57:53.020Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 31898 | 2026-08-28T09:57:54.260Z | observation_span_recorded |  |  |  |
| 31899 | 2026-08-28T09:57:54.503Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=3101c08263ce4ff5a393960a0dfe6eae |
| 31900 | 2026-08-28T09:57:54.671Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 31904 | 2026-08-28T09:57:55.421Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=f152a5fd9e28bcd965814f93011007ad430eaf8c4928bbcf78525b3244624ac8 |
| 31908 | 2026-08-28T09:57:56.253Z | managed_process_admitted |  |  | owner=default |
| 31910 | 2026-08-28T09:57:56.742Z | managed_process_started |  |  | owner=default |
| 31918 | 2026-08-28T09:58:13.299Z | managed_process_terminal |  |  | owner=default |
| 31919 | 2026-08-28T09:58:15.007Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=f152a5fd9e28bcd965814f93011007ad430eaf8c4928bbcf78525b3244624ac8 |
| 31920 | 2026-08-28T09:58:15.268Z | observation_span_recorded |  |  |  |
| 31921 | 2026-08-28T09:58:15.447Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | f152a5fd9e28bcd965814f93011007ad430eaf8c4928bbcf78525b3244624ac8 | False | 19171 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `20`
- Chain head: `cd02b48325a0274de6ca7a1555b3d3935eacf7d5653019db3718b0e3dda346e1`
