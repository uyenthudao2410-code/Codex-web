# Orchestration Wave 1

- Run: `8345f396bd3341da920d835683cef82d`
- Wave: `cf9e631714c5465f843e20b73968d296`
- Objective: Implement same-clock acceptance latency attribution without changing EOCL authority. Preserve existing runtime stage observations. Persist a bounded descriptive ACCEPTING start anchor scoped to exact RUN/WAVE and the current coding-mcp monotonic clock domain. On controller task_control accept, measure controller-processing in that same runtime clock and emit acceptance-wait only when the durable anchor clock domain exactly matches the current runtime clock; otherwise leave wait unknown. Extend stage_latency_attribution reporting with controller_processing_ms and acceptance_wait_ms coverage/missingness, without cross-clock subtraction or summing nonexclusive spans. Do not modify workflow_tools.py or backfill history.
- Objective revision: `1`
- Objective SHA-256: `33252a34d2f3e4a1d46a09265b67b6d648b8851e9f31a471f721032848201e7e`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `7bc1caee37107a15e74eb078b52fe314e5fa33ab`
- Worktree fingerprint: `0e3d52f831b921e1c020115046dcd6dc801ba29d1a4f1c6b751621c8b66f23e7`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 50307 | 2026-09-12T05:46:44.221Z | run_started |  | PREFLIGHT |  |
| 50308 | 2026-09-12T05:46:44.792Z | observation_span_recorded |  |  |  |
| 50309 | 2026-09-12T05:46:45.020Z | solution_shadow_recommended |  |  |  |
| 50310 | 2026-09-12T05:46:50.445Z | observation_span_recorded |  |  |  |
| 50311 | 2026-09-12T05:46:50.701Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 50312 | 2026-09-12T05:47:09.174Z | managed_process_admitted |  |  | owner=default |
| 50313 | 2026-09-12T05:47:09.561Z | managed_process_started |  |  | owner=default |
| 50314 | 2026-09-12T05:47:10.188Z | managed_process_terminal |  |  | owner=default |
| 50315 | 2026-09-12T05:47:23.080Z | managed_process_admitted |  |  | owner=default |
| 50316 | 2026-09-12T05:47:23.455Z | managed_process_started |  |  | owner=default |
| 50317 | 2026-09-12T05:47:24.089Z | managed_process_terminal |  |  | owner=default |
| 50318 | 2026-09-12T05:47:50.205Z | managed_process_admitted |  |  | owner=default |
| 50319 | 2026-09-12T05:47:50.605Z | managed_process_started |  |  | owner=default |
| 50320 | 2026-09-12T05:47:51.206Z | managed_process_terminal |  |  | owner=default |
| 50321 | 2026-09-12T05:48:46.531Z | managed_process_admitted |  |  | owner=default |
| 50322 | 2026-09-12T05:48:46.863Z | managed_process_started |  |  | owner=default |
| 50323 | 2026-09-12T05:48:47.447Z | managed_process_terminal |  |  | owner=default |
| 50324 | 2026-09-12T05:49:03.625Z | managed_process_admitted |  |  | owner=default |
| 50325 | 2026-09-12T05:49:04.026Z | managed_process_started |  |  | owner=default |
| 50326 | 2026-09-12T05:49:04.585Z | managed_process_terminal |  |  | owner=default |
| 50327 | 2026-09-12T05:49:19.325Z | managed_process_admitted |  |  | owner=default |
| 50328 | 2026-09-12T05:49:19.743Z | managed_process_started |  |  | owner=default |
| 50329 | 2026-09-12T05:49:20.309Z | managed_process_terminal |  |  | owner=default |
| 50330 | 2026-09-12T05:51:26.678Z | managed_process_admitted |  |  | owner=default |
| 50331 | 2026-09-12T05:51:27.035Z | managed_process_started |  |  | owner=default |
| 50332 | 2026-09-12T05:51:27.601Z | managed_process_terminal |  |  | owner=default |
| 50333 | 2026-09-12T05:51:50.545Z | managed_process_admitted |  |  | owner=default |
| 50334 | 2026-09-12T05:51:50.844Z | managed_process_started |  |  | owner=default |
| 50335 | 2026-09-12T05:51:51.327Z | managed_process_terminal |  |  | owner=default |
| 50336 | 2026-09-12T05:52:44.032Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 50337 | 2026-09-12T05:52:44.211Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 50338 | 2026-09-12T05:52:44.403Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 50339 | 2026-09-12T05:52:44.579Z | state_transition | READY | ROUTED | reason=route_selected |
| 50340 | 2026-09-12T05:52:44.839Z | observation_span_recorded |  |  |  |
| 50341 | 2026-09-12T05:52:45.795Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=a2187cc2faa84d3aa1cfdd302a1ed7ca |
| 50342 | 2026-09-12T05:52:46.003Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 50343 | 2026-09-12T05:52:46.906Z | patch_surface_observed |  |  |  |
| 50344 | 2026-09-12T05:52:47.164Z | patch_surface_observed |  |  |  |
| 50345 | 2026-09-12T05:52:47.449Z | patch_surface_observed |  |  |  |
| 50346 | 2026-09-12T05:52:47.643Z | patch_surface_observed |  |  |  |
| 50347 | 2026-09-12T05:52:47.886Z | patch_surface_observed |  |  |  |
| 50348 | 2026-09-12T05:52:48.056Z | observation_span_recorded |  |  |  |
| 50349 | 2026-09-12T05:52:48.294Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=a2187cc2faa84d3aa1cfdd302a1ed7ca |
| 50350 | 2026-09-12T05:52:48.467Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 50351 | 2026-09-12T05:52:49.309Z | proof_cache_miss |  |  | reason=cold; stage_id=check:ea8ebd6fe4fff459; input_fingerprint=5f2f23f8d21cc203289e390d14ad7c937988deea3103563a61ff96369089fea8 |
| 50352 | 2026-09-12T05:52:49.747Z | managed_process_admitted |  |  | owner=default |
| 50353 | 2026-09-12T05:52:50.061Z | managed_process_started |  |  | owner=default |
| 50354 | 2026-09-12T05:52:50.530Z | managed_process_terminal |  |  | owner=default |
| 50355 | 2026-09-12T05:52:51.278Z | proof_recorded |  |  | stage_id=check:ea8ebd6fe4fff459; status=passed; cache_hit=False; input_fingerprint=5f2f23f8d21cc203289e390d14ad7c937988deea3103563a61ff96369089fea8 |
| 50356 | 2026-09-12T05:52:51.475Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=bfbca7909e97c6f882c0456b053bbe16af8d8de35f29da68ffb0017e741d1406 |
| 50357 | 2026-09-12T05:52:51.875Z | managed_process_admitted |  |  | owner=default |
| 50358 | 2026-09-12T05:52:52.234Z | managed_process_started |  |  | owner=default |
| 50359 | 2026-09-12T05:53:57.748Z | managed_process_terminal |  |  | owner=default |
| 50360 | 2026-09-12T05:53:58.157Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=bfbca7909e97c6f882c0456b053bbe16af8d8de35f29da68ffb0017e741d1406 |
| 50361 | 2026-09-12T05:53:59.172Z | observation_span_recorded |  |  |  |
| 50362 | 2026-09-12T05:53:59.362Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 50363 | 2026-09-12T05:54:38.147Z | managed_process_admitted |  |  | owner=default |
| 50364 | 2026-09-12T05:54:38.484Z | managed_process_started |  |  | owner=default |
| 50365 | 2026-09-12T05:54:39.048Z | managed_process_terminal |  |  | owner=default |
| 50366 | 2026-09-12T05:55:18.526Z | quality_outcome_recorded |  |  |  |
| 50367 | 2026-09-12T05:55:18.718Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 50368 | 2026-09-12T05:55:19.091Z | observation_span_recorded |  |  |  |
| 50369 | 2026-09-12T05:55:19.331Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:ea8ebd6fe4fff459 | passed | 5f2f23f8d21cc203289e390d14ad7c937988deea3103563a61ff96369089fea8 | False | 1621 | 0 |
| verify:tests | passed | bfbca7909e97c6f882c0456b053bbe16af8d8de35f29da68ffb0017e741d1406 | False | 66311 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| aa4bf2c32b2b46ecbf392496e3af9943 | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | de2b54dc76683029f31e4d5ee64efabba0be0f5cf177db1f951b82ebaa6879e1 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `63`
- Chain head: `5b36d9e21a2419ed41159de53d09aa3bf969378f2c86f15bcb552526535c9c62`
