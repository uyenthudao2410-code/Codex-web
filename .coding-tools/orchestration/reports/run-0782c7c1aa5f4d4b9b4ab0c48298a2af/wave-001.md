# Orchestration Wave 1

- Run: `0782c7c1aa5f4d4b9b4ab0c48298a2af`
- Wave: `8bbe2ddcbf4144d88ba55af33fdf4826`
- Objective: Natural #15: add phase-aware P2 accepted-run timing metrics without changing total TTA or EOCL timing semantics. Aggregate durable phase_timing into engineering-active and acceptance-wait measurements, stratified by first-pass vs repaired, preserving unknown when phase timing is incomplete. Add focused regression including a first-pass accepted run dominated by ACCEPTING wait.
- Objective revision: `1`
- Objective SHA-256: `59087184a89cd315ab4ebe43d249322ecd6b205da17e02e6a9fbe636c1c3f207`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `7bc1caee37107a15e74eb078b52fe314e5fa33ab`
- Worktree fingerprint: `548838251b5b79e8fc18d8ce093272da7ba44e1d926caa5f96c57f91b6fccca9`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 46621 | 2026-09-10T05:20:27.117Z | run_started |  | PREFLIGHT |  |
| 46622 | 2026-09-10T05:20:27.688Z | observation_span_recorded |  |  |  |
| 46623 | 2026-09-10T05:20:27.914Z | solution_shadow_recommended |  |  |  |
| 46624 | 2026-09-10T05:20:33.874Z | observation_span_recorded |  |  |  |
| 46625 | 2026-09-10T05:20:34.123Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 46626 | 2026-09-10T05:20:51.240Z | managed_process_admitted |  |  | owner=chatweb |
| 46627 | 2026-09-10T05:20:51.570Z | managed_process_started |  |  | owner=chatweb |
| 46628 | 2026-09-10T05:20:52.159Z | managed_process_terminal |  |  | owner=chatweb |
| 46629 | 2026-09-10T05:21:01.706Z | managed_process_admitted |  |  | owner=chatweb |
| 46630 | 2026-09-10T05:21:01.967Z | managed_process_started |  |  | owner=chatweb |
| 46631 | 2026-09-10T05:21:05.020Z | managed_process_terminal |  |  | owner=chatweb |
| 46632 | 2026-09-10T05:21:35.216Z | managed_process_admitted |  |  | owner=chatweb |
| 46633 | 2026-09-10T05:21:35.503Z | managed_process_started |  |  | owner=chatweb |
| 46634 | 2026-09-10T05:21:35.960Z | managed_process_terminal |  |  | owner=chatweb |
| 46635 | 2026-09-10T05:21:47.016Z | managed_process_admitted |  |  | owner=chatweb |
| 46636 | 2026-09-10T05:21:47.323Z | managed_process_started |  |  | owner=chatweb |
| 46637 | 2026-09-10T05:21:49.643Z | managed_process_terminal |  |  | owner=chatweb |
| 46638 | 2026-09-10T05:22:03.626Z | managed_process_admitted |  |  | owner=chatweb |
| 46639 | 2026-09-10T05:22:04.012Z | managed_process_started |  |  | owner=chatweb |
| 46640 | 2026-09-10T05:22:06.365Z | managed_process_terminal |  |  | owner=chatweb |
| 46641 | 2026-09-10T05:24:07.040Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 46642 | 2026-09-10T05:24:07.227Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 46643 | 2026-09-10T05:24:07.490Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 46644 | 2026-09-10T05:24:07.636Z | state_transition | READY | ROUTED | reason=route_selected |
| 46645 | 2026-09-10T05:24:07.868Z | observation_span_recorded |  |  |  |
| 46646 | 2026-09-10T05:24:08.828Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=c8d42f8e3d974a04905f980d1a266ccf |
| 46647 | 2026-09-10T05:24:09.011Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 46648 | 2026-09-10T05:24:09.890Z | patch_surface_observed |  |  |  |
| 46649 | 2026-09-10T05:24:10.099Z | observation_span_recorded |  |  |  |
| 46650 | 2026-09-10T05:24:10.451Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=c8d42f8e3d974a04905f980d1a266ccf |
| 46651 | 2026-09-10T05:24:10.631Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 46652 | 2026-09-10T05:24:11.415Z | proof_cache_miss |  |  | reason=cold; stage_id=check:a168dafddd4eed46; input_fingerprint=e94ce907fb419faf0ce9b9b517a75b07f8d6b9513cd18bc99e95305d1d22fec9 |
| 46653 | 2026-09-10T05:24:11.871Z | managed_process_admitted |  |  | owner=default |
| 46654 | 2026-09-10T05:24:12.195Z | managed_process_started |  |  | owner=default |
| 46655 | 2026-09-10T05:24:12.686Z | managed_process_terminal |  |  | owner=default |
| 46656 | 2026-09-10T05:24:13.048Z | proof_recorded |  |  | stage_id=check:a168dafddd4eed46; status=failed; cache_hit=False; input_fingerprint=e94ce907fb419faf0ce9b9b517a75b07f8d6b9513cd18bc99e95305d1d22fec9 |
| 46657 | 2026-09-10T05:24:13.214Z | observation_span_recorded |  |  |  |
| 46658 | 2026-09-10T05:24:13.369Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 46659 | 2026-09-10T05:24:13.511Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 46660 | 2026-09-10T05:24:13.680Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:a168dafddd4eed46 | failed | e94ce907fb419faf0ce9b9b517a75b07f8d6b9513cd18bc99e95305d1d22fec9 | False | 1206 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `113`
- Chain head: `ae4879d61ae7e90a326f395c7b00c0afb492fac98b7cf8be046beee20050e2e2`
