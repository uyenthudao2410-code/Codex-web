# Orchestration Wave 1

- Run: `841eded65717450a9342f9b24c70dec7`
- Wave: `ad201a28cc0045158605d15fcecbea17`
- Objective: Continue the SAME canonical UI lag/dashboard closure RUN/WAVE prepared in this task context. Apply only the final verified gaps on current HEAD 2cc0eefc7d881827ef44e4d1584d84bbd9e494b6, preserving unrelated dirty runtime/docs evidence. Required final behavior: (1) renderer/control-center.js: on Overview, every refresh path including force/manual/initial/visibility/dashboard-request must use api.lightweightSnapshot()+api.liveOrchestration(); only force refresh on non-Overview manager pages may use api.snapshot()+api.orchestration(). Merge lightweight status based on that manager-refresh decision, and include page in the existing coding-tools:overview-pulse detail. (2) resources/coding-tools-mcp/coding_tools_mcp/mcp_http_handler.py: /__control/orchestration/analytics must use one shared current UTC timestamp for both ledger.usage_analytics(days=7, now=...) and operations_analytics(..., days=7, now=...), and return generated_at plus window_days=7; keep it reconciliation-free; add /__control/orchestration/analytics to OPTIONS allowlist. (3) electron/main.js: set PANEL_ANALYTICS_TIMEOUT_MS to 10000. (4) renderer/dashboard.js: canonicalControllerUsageState, canonicalOperationsAnalytics, canonicalMeasuredUsage must consume analyticsSnapshot only, never fall back to orchestration usage/operations analytics. (5) update focused tests to lock all of these rules and remove assertions that require the old fallback/full-force behavior. Do not refactor unrelated code, do not touch unrelated dirty files, do not restart, commit, push, release, or manually edit .coding-tools.
- Objective revision: `1`
- Objective SHA-256: `d251388f6b45506abdfbde3046cb6966a9a04a56db032a4e7a76591b8e2ed301`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `2cc0eefc7d881827ef44e4d1584d84bbd9e494b6`
- Worktree fingerprint: `c1652a1c4631d3417d99b93291f95dc90ce67aa5ac02ad086b7752dce0ff8112`
- Contract fingerprint: ``
- Status: **active**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 32108 | 2026-08-28T10:23:59.033Z | run_started |  | PREFLIGHT |  |
| 32109 | 2026-08-28T10:23:59.422Z | observation_span_recorded |  |  |  |
| 32110 | 2026-08-28T10:23:59.668Z | solution_shadow_recommended |  |  |  |
| 32111 | 2026-08-28T10:23:59.876Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 32112 | 2026-08-28T10:24:00.057Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 32113 | 2026-08-28T10:24:00.245Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 32114 | 2026-08-28T10:24:00.451Z | state_transition | READY | ROUTED | reason=route_selected |
| 32115 | 2026-08-28T10:24:00.710Z | observation_span_recorded |  |  |  |
| 32116 | 2026-08-28T10:24:01.427Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=2f583ba0877a44f3b7c2c093d1f413e0 |
| 32117 | 2026-08-28T10:24:01.588Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 32118 | 2026-08-28T10:24:02.409Z | observation_span_recorded |  |  |  |
| 32119 | 2026-08-28T10:24:02.727Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=2f583ba0877a44f3b7c2c093d1f413e0 |
| 32120 | 2026-08-28T10:24:02.903Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 32121 | 2026-08-28T10:24:03.510Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=381758e2079572e14a15e8a4fc560f0ff1d43d1c64386811d922fa321aaa4ad5 |
| 32122 | 2026-08-28T10:24:03.990Z | managed_process_admitted |  |  | owner=default |
| 32123 | 2026-08-28T10:24:04.262Z | managed_process_started |  |  | owner=default |
| 32124 | 2026-08-28T10:24:22.961Z | managed_process_terminal |  |  | owner=default |
| 32125 | 2026-08-28T10:24:24.611Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=381758e2079572e14a15e8a4fc560f0ff1d43d1c64386811d922fa321aaa4ad5 |
| 32126 | 2026-08-28T10:24:24.994Z | observation_span_recorded |  |  |  |
| 32127 | 2026-08-28T10:24:25.191Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 381758e2079572e14a15e8a4fc560f0ff1d43d1c64386811d922fa321aaa4ad5 | False | 20656 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `20`
- Chain head: `455c32ec3fbd5c0a0e916df312128d08b5d59b6846595ee54eb50477cd9dc2ad`
