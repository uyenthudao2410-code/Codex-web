# Orchestration Wave 1

- Run: `6f576099cc9a4974a9a62eb225baa340`
- Wave: `aaa1628991864052be72020b34133735`
- Objective: Natural #5 revision 3: fix prepared-workflow exact binding so a RUN originally created with phase=run can, after REPLAN and an exact new preparation wave, execute only when canonical context_prepared evidence exists for that exact active wave. Preserve exact RUN/WAVE/task/workflow/state fail-closed checks and historical metadata. Prepare only; no mutation.
- Objective revision: `1`
- Objective SHA-256: `5f4a25ae3fc55ca4d37b1d96c4500c515fbe53ce8749434daeb83f5d7f37f4a2`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `7bc1caee37107a15e74eb078b52fe314e5fa33ab`
- Worktree fingerprint: `5c4ef280d73a18ebbe2a9cf36edc8ac24f46ba285b23ba3f81e0ff8bc9ae08bc`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 45449 | 2026-09-09T09:46:06.247Z | run_started |  | PREFLIGHT |  |
| 45450 | 2026-09-09T09:46:06.701Z | observation_span_recorded |  |  |  |
| 45451 | 2026-09-09T09:46:12.420Z | observation_span_recorded |  |  |  |
| 45452 | 2026-09-09T09:46:12.638Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 45453 | 2026-09-09T09:48:35.149Z | solution_shadow_recommended |  |  |  |
| 45454 | 2026-09-09T09:48:35.409Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 45455 | 2026-09-09T09:48:35.602Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 45456 | 2026-09-09T09:48:35.810Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 45457 | 2026-09-09T09:48:36.034Z | state_transition | READY | ROUTED | reason=route_selected |
| 45458 | 2026-09-09T09:48:36.292Z | observation_span_recorded |  |  |  |
| 45459 | 2026-09-09T09:48:37.205Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=46d238e85c064facb0c3dbd99236c907 |
| 45460 | 2026-09-09T09:48:37.428Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 45461 | 2026-09-09T09:48:38.243Z | patch_surface_observed |  |  |  |
| 45462 | 2026-09-09T09:48:38.493Z | patch_surface_observed |  |  |  |
| 45463 | 2026-09-09T09:48:38.704Z | patch_surface_observed |  |  |  |
| 45464 | 2026-09-09T09:48:38.886Z | observation_span_recorded |  |  |  |
| 45465 | 2026-09-09T09:48:39.185Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=46d238e85c064facb0c3dbd99236c907 |
| 45466 | 2026-09-09T09:48:39.357Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 45467 | 2026-09-09T09:48:40.084Z | proof_cache_miss |  |  | reason=cold; stage_id=check:d616cd12b540f8ba; input_fingerprint=cff5d2851b6143d7685dd3e4a4603d69204556c6b9529424123fd5a360b63460 |
| 45468 | 2026-09-09T09:48:40.388Z | managed_process_admitted |  |  | owner=default |
| 45469 | 2026-09-09T09:48:40.707Z | managed_process_started |  |  | owner=default |
| 45470 | 2026-09-09T09:48:41.182Z | managed_process_terminal |  |  | owner=default |
| 45471 | 2026-09-09T09:48:41.455Z | proof_recorded |  |  | stage_id=check:d616cd12b540f8ba; status=passed; cache_hit=False; input_fingerprint=cff5d2851b6143d7685dd3e4a4603d69204556c6b9529424123fd5a360b63460 |
| 45472 | 2026-09-09T09:48:41.622Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=5d96ba9d9785bb5b8ebd09d277562b08dc3e394f0df8fa75a7f21be5289d9c50 |
| 45473 | 2026-09-09T09:48:41.956Z | managed_process_admitted |  |  | owner=default |
| 45474 | 2026-09-09T09:48:42.327Z | managed_process_started |  |  | owner=default |
| 45475 | 2026-09-09T09:49:14.986Z | managed_process_terminal |  |  | owner=default |
| 45476 | 2026-09-09T09:49:16.381Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=5d96ba9d9785bb5b8ebd09d277562b08dc3e394f0df8fa75a7f21be5289d9c50 |
| 45477 | 2026-09-09T09:49:17.614Z | observation_span_recorded |  |  |  |
| 45478 | 2026-09-09T09:49:17.975Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 45479 | 2026-09-09T10:00:16.022Z | managed_process_admitted |  |  | owner=default |
| 45480 | 2026-09-09T10:00:16.303Z | managed_process_started |  |  | owner=default |
| 45481 | 2026-09-09T10:00:16.726Z | managed_process_terminal |  |  | owner=default |
| 45482 | 2026-09-09T10:00:26.590Z | managed_process_admitted |  |  | owner=default |
| 45483 | 2026-09-09T10:00:26.935Z | managed_process_started |  |  | owner=default |
| 45484 | 2026-09-09T10:00:27.425Z | managed_process_terminal |  |  | owner=default |
| 45485 | 2026-09-09T10:01:12.738Z | managed_process_admitted |  |  | owner=default |
| 45486 | 2026-09-09T10:01:13.122Z | managed_process_started |  |  | owner=default |
| 45487 | 2026-09-09T10:01:13.809Z | managed_process_terminal |  |  | owner=default |
| 45488 | 2026-09-09T10:01:24.591Z | managed_process_admitted |  |  | owner=default |
| 45489 | 2026-09-09T10:01:24.909Z | managed_process_started |  |  | owner=default |
| 45490 | 2026-09-09T10:01:25.469Z | managed_process_terminal |  |  | owner=default |
| 45491 | 2026-09-09T10:01:47.988Z | quality_outcome_recorded |  |  |  |
| 45492 | 2026-09-09T10:01:48.188Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 45493 | 2026-09-09T10:01:48.499Z | observation_span_recorded |  |  |  |
| 45494 | 2026-09-09T10:01:48.737Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:d616cd12b540f8ba | passed | cff5d2851b6143d7685dd3e4a4603d69204556c6b9529424123fd5a360b63460 | False | 1090 | 0 |
| verify:tests | passed | 5d96ba9d9785bb5b8ebd09d277562b08dc3e394f0df8fa75a7f21be5289d9c50 | False | 34375 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| a2db60129f99457db09b2e658e4acdf8 | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | c9d05174283ae1b9aa9f154afdc9d366ff615c978caaaf9d207c2fb94ebaf8b4 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `46`
- Chain head: `925bd4c0a27c68f87b725d7966dc70ca24ca5fef5fefeffe6dee3d596deb6f0d`
