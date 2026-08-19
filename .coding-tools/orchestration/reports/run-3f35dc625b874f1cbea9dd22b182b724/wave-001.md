# Orchestration Wave 1

- Run: `3f35dc625b874f1cbea9dd22b182b724`
- Wave: `70b90025d4d24922acac98cc269dfb33`
- Objective: Prepare the smallest safe frontend-only fix for Intake #117 / US-105. In Project Finance selected-project detail, live modes must never render ProjectFinancialDetailOverview fixture values or ProjectFinancialHeroBanner default sample fields. Keep fixture/mock presentation only in explicit standalone fixture preview. In finance-read/live modes, make the already-adapted PfmProjectVisualModel overview visible (metrics, cost breakdown, trend, diagnoses, notable costs, source cards, quick links), preserving exact-string/missing-data semantics. For the live project header, remove default sample fallbacks; use source-backed identity/profile values and represent unavailable hero fields truthfully or omit the decorative hero if its contract cannot represent missing values safely. Do not change backend, API, schema, capabilities, semantic sign-off, or DIRECT_COST. Identify focused tests to add/update and exact commands to prove the regression is closed.
- Mode: `mcp_only`
- Base HEAD: `06854413b465b17749346ecfd7ce51731b6a4789`
- Worktree fingerprint: `dabfe19bd747b107a65e8fd92dd57a34228f4507731c272bc732edb29ecf3017`
- Contract fingerprint: ``
- Status: **active**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 19306 | 2026-08-19T04:33:59.788Z | run_started |  | PREFLIGHT |  |
| 19307 | 2026-08-19T04:34:00.601Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 19308 | 2026-08-19T04:34:11.569Z | managed_process_admitted |  |  | owner=chatweb |
| 19309 | 2026-08-19T04:34:11.867Z | managed_process_started |  |  | owner=chatweb |
| 19310 | 2026-08-19T04:34:12.263Z | managed_process_terminal |  |  | owner=chatweb |
| 19311 | 2026-08-19T04:34:23.960Z | managed_process_admitted |  |  | owner=chatweb |
| 19312 | 2026-08-19T04:34:24.230Z | managed_process_started |  |  | owner=chatweb |
| 19313 | 2026-08-19T04:34:24.677Z | managed_process_terminal |  |  | owner=chatweb |
| 19314 | 2026-08-19T04:34:29.978Z | managed_process_admitted |  |  | owner=chatweb |
| 19315 | 2026-08-19T04:34:30.202Z | managed_process_started |  |  | owner=chatweb |
| 19316 | 2026-08-19T04:34:30.559Z | managed_process_terminal |  |  | owner=chatweb |
| 19317 | 2026-08-19T04:35:03.356Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 19318 | 2026-08-19T04:35:03.522Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 19319 | 2026-08-19T04:35:03.672Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 19320 | 2026-08-19T04:35:03.831Z | state_transition | READY | ROUTED | reason=route_selected |
| 19321 | 2026-08-19T04:35:04.422Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=eacf377ec0a94bd8afc1f4ea551116bb |
| 19322 | 2026-08-19T04:35:04.581Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 19323 | 2026-08-19T04:35:05.139Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=eacf377ec0a94bd8afc1f4ea551116bb |
| 19324 | 2026-08-19T04:35:05.274Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 19325 | 2026-08-19T04:35:05.685Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=471b4711cad8adec5988e713ea59167566977c9679c28af6f113d05a7006a91d |
| 19326 | 2026-08-19T04:35:32.324Z | managed_process_admitted |  |  | owner=chatweb |
| 19327 | 2026-08-19T04:35:32.643Z | managed_process_started |  |  | owner=chatweb |
| 19328 | 2026-08-19T04:35:33.057Z | managed_process_terminal |  |  | owner=chatweb |
| 19329 | 2026-08-19T04:36:10.178Z | managed_process_admitted |  |  | owner=chatweb |
| 19330 | 2026-08-19T04:36:10.443Z | managed_process_started |  |  | owner=chatweb |
| 19331 | 2026-08-19T04:36:10.985Z | managed_process_terminal |  |  | owner=chatweb |
| 19332 | 2026-08-19T04:36:16.977Z | managed_process_admitted |  |  | owner=chatweb |
| 19333 | 2026-08-19T04:36:17.285Z | managed_process_started |  |  | owner=chatweb |
| 19334 | 2026-08-19T04:36:59.987Z | managed_process_terminal |  |  | owner=chatweb |
| 19335 | 2026-08-19T04:37:09.031Z | managed_process_admitted |  |  | owner=chatweb |
| 19336 | 2026-08-19T04:37:09.471Z | managed_process_started |  |  | owner=chatweb |
| 19337 | 2026-08-19T04:37:14.276Z | managed_process_admitted |  |  | owner=default |
| 19338 | 2026-08-19T04:37:14.557Z | managed_process_started |  |  | owner=default |
| 19339 | 2026-08-19T04:37:15.210Z | managed_process_terminal |  |  | owner=default |
| 19340 | 2026-08-19T04:37:25.885Z | managed_process_admitted |  |  | owner=default |
| 19341 | 2026-08-19T04:37:26.170Z | managed_process_started |  |  | owner=default |
| 19342 | 2026-08-19T04:37:26.586Z | managed_process_terminal |  |  | owner=default |
| 19343 | 2026-08-19T04:37:31.998Z | managed_process_admitted |  |  | owner=default |
| 19344 | 2026-08-19T04:37:32.336Z | managed_process_started |  |  | owner=default |
| 19345 | 2026-08-19T04:37:32.794Z | managed_process_terminal |  |  | owner=default |

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
- Events checked: `40`
- Chain head: `055e0d0802057b8240cb4496d3c9a3263c8b94b13de7461bd7c024d25ae50d1e`
