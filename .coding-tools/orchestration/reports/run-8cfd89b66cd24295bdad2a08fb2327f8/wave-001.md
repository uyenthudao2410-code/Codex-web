# Orchestration Wave 1

- Run: `8cfd89b66cd24295bdad2a08fb2327f8`
- Wave: `debb483b02774c319dc8e1a788ef8d10`
- Objective: Fix MCP-2026 exact-run continuation so task_control(action=stop, run_id=...) recovers the durable stateless task context instead of minting a new context. Correct the regression to assert the explicit-run stop receipt contract: top-level stopped/target_run_id/detached/orchestration state, while preserving task-level state.
- Objective revision: `1`
- Objective SHA-256: `299ef395a91699d5611b985290ca320a2ed5721e45128742a72a3a3d248000ae`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `52faa0e9cfacf582fcf5bc6f40ed230cea7602e9`
- Worktree fingerprint: `3d5ffa0d515a206ceb984dfe65a78295ab4c9d599104c52fa3ea58f58dea2b13`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 30355 | 2026-08-26T07:34:24.505Z | run_started |  | PREFLIGHT |  |
| 30356 | 2026-08-26T07:34:24.712Z | observation_span_recorded |  |  |  |
| 30357 | 2026-08-26T07:34:52.406Z | solution_shadow_recommended |  |  |  |
| 30358 | 2026-08-26T07:34:52.572Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 30359 | 2026-08-26T07:34:52.687Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 30360 | 2026-08-26T07:34:52.791Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 30361 | 2026-08-26T07:34:52.902Z | state_transition | READY | ROUTED | reason=route_selected |
| 30362 | 2026-08-26T07:34:53.045Z | observation_span_recorded |  |  |  |
| 30363 | 2026-08-26T07:34:53.855Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=733c3f57058c4f80b05666b315fe12d4 |
| 30364 | 2026-08-26T07:34:53.977Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 30365 | 2026-08-26T07:34:54.770Z | patch_surface_observed |  |  |  |
| 30366 | 2026-08-26T07:34:54.931Z | observation_span_recorded |  |  |  |
| 30367 | 2026-08-26T07:34:55.170Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=733c3f57058c4f80b05666b315fe12d4 |
| 30368 | 2026-08-26T07:34:55.304Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 30369 | 2026-08-26T07:34:56.058Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=2285b2e66abf6e311ddf89b7951ed44d92f5f3971188871d85fa6b252bf7604e |
| 30370 | 2026-08-26T07:34:56.381Z | managed_process_admitted |  |  | owner=default |
| 30371 | 2026-08-26T07:34:56.596Z | managed_process_started |  |  | owner=default |
| 30372 | 2026-08-26T07:35:12.961Z | managed_process_terminal |  |  | owner=default |
| 30373 | 2026-08-26T07:35:14.011Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=2285b2e66abf6e311ddf89b7951ed44d92f5f3971188871d85fa6b252bf7604e |
| 30374 | 2026-08-26T07:35:14.861Z | observation_span_recorded |  |  |  |
| 30375 | 2026-08-26T07:35:15.139Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 30376 | 2026-08-26T07:37:34.164Z | managed_process_admitted |  |  | owner=chatweb |
| 30377 | 2026-08-26T07:37:34.610Z | managed_process_started |  |  | owner=chatweb |
| 30378 | 2026-08-26T07:37:35.646Z | managed_process_terminal |  |  | owner=chatweb |
| 30379 | 2026-08-26T07:37:57.255Z | quality_outcome_recorded |  |  |  |
| 30380 | 2026-08-26T07:37:57.424Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 30381 | 2026-08-26T07:37:58.444Z | observation_span_recorded |  |  |  |
| 30382 | 2026-08-26T07:37:59.812Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 2285b2e66abf6e311ddf89b7951ed44d92f5f3971188871d85fa6b252bf7604e | False | 17657 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| e513d927cde245aa9443d23cceb49664 | accepted | 52faa0e9cfacf582fcf5bc6f40ed230cea7602e9 | 70dd970f9a7e455ae75391254c41976b17b76e5a9e2b2039e2f70b5f76b23962 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `28`
- Chain head: `3f54e9acca444281d5de3bdec8777636f48070e9a69e1a2de8812b6f5c33de2f`
