# Orchestration Wave 1

- Run: `8bf171b1fe7346e88cd97c34338c1102`
- Wave: `ffaa77b74f324c0883df5b692546ae52`
- Objective: Fix the observed N21 supervisor restart/full-clean HANDOFF self-deadlock that caused exact maintenance ticket restart-49eqbqg6cR5jzcW7 to fail with RECOVERY_SUPERVISION_BUSY. Root cause already proven: RecoveryHost.superviseOnce consumes an exact restart ticket while the current durable epoch was READY; FullCleanActivation transitions to HANDOFF and stops the runtime, but superviseOnce continues ordinary orchestrator.supervise/recovery/UI work using the pre-ticket admissionBlocked=false value while performFullCleanHandoff waits on the same supervisionInFlight promise. The fix must make the current watchdog iteration yield immediately after serviceSupervisorRestartRequest returns status=accepted, publish only fail-closed transitional readiness, preserve completed/failed/deferred/no-ticket behavior, and add a focused regression test. Preserve all unrelated dirty bytes. Do not modify stale-run reconciliation semantics, timeout constants, ledger data, or Git history.
- Objective revision: `1`
- Objective SHA-256: `809c7e76e08d4aebebb75a88451b6d06a4d87e448b38c845ea87bdc5be0f6ea0`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `7bc1caee37107a15e74eb078b52fe314e5fa33ab`
- Worktree fingerprint: `200185f726f4a202cfe54fc6e64ce6be3bd5ed943c088375dda83804411ec63d`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 48493 | 2026-09-10T17:52:14.202Z | run_started |  | PREFLIGHT |  |
| 48494 | 2026-09-10T17:52:14.578Z | observation_span_recorded |  |  |  |
| 48495 | 2026-09-10T17:52:14.792Z | solution_shadow_recommended |  |  |  |
| 48496 | 2026-09-10T17:52:20.562Z | observation_span_recorded |  |  |  |
| 48497 | 2026-09-10T17:52:20.735Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 48498 | 2026-09-10T17:53:42.680Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 48499 | 2026-09-10T17:53:42.887Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 48500 | 2026-09-10T17:53:43.128Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 48501 | 2026-09-10T17:53:43.569Z | state_transition | READY | ROUTED | reason=route_selected |
| 48502 | 2026-09-10T17:53:43.858Z | observation_span_recorded |  |  |  |
| 48503 | 2026-09-10T17:53:44.765Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=d1b3d413fce049a9bdd4ea70b8a15353 |
| 48504 | 2026-09-10T17:53:44.972Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 48505 | 2026-09-10T17:53:45.860Z | patch_surface_observed |  |  |  |
| 48506 | 2026-09-10T17:53:46.038Z | observation_span_recorded |  |  |  |
| 48507 | 2026-09-10T17:53:46.357Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=d1b3d413fce049a9bdd4ea70b8a15353 |
| 48508 | 2026-09-10T17:53:46.508Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 48509 | 2026-09-10T17:53:47.270Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=f3b11d660ea18e8c1001e53e260f4601c94d411fdc41892590668e6a0d78edcb |
| 48510 | 2026-09-10T17:53:47.727Z | managed_process_admitted |  |  | owner=default |
| 48511 | 2026-09-10T17:53:48.072Z | managed_process_started |  |  | owner=default |
| 48512 | 2026-09-10T17:54:07.589Z | managed_process_terminal |  |  | owner=default |
| 48513 | 2026-09-10T17:54:08.970Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=f3b11d660ea18e8c1001e53e260f4601c94d411fdc41892590668e6a0d78edcb |
| 48514 | 2026-09-10T17:54:10.016Z | observation_span_recorded |  |  |  |
| 48515 | 2026-09-10T17:54:10.212Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 48516 | 2026-09-10T17:59:17.280Z | managed_process_admitted |  |  | owner=default |
| 48517 | 2026-09-10T17:59:17.597Z | managed_process_started |  |  | owner=default |
| 48518 | 2026-09-10T17:59:18.096Z | managed_process_terminal |  |  | owner=default |
| 48519 | 2026-09-10T18:06:10.329Z | managed_process_admitted |  |  | owner=default |
| 48520 | 2026-09-10T18:06:10.622Z | managed_process_started |  |  | owner=default |
| 48521 | 2026-09-10T18:06:12.359Z | managed_process_terminal |  |  | owner=default |
| 48522 | 2026-09-10T18:06:20.423Z | quality_outcome_recorded |  |  |  |
| 48523 | 2026-09-10T18:06:20.657Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 48524 | 2026-09-10T18:06:20.886Z | observation_span_recorded |  |  |  |
| 48525 | 2026-09-10T18:06:21.181Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | f3b11d660ea18e8c1001e53e260f4601c94d411fdc41892590668e6a0d78edcb | False | 21266 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 67a0b107450d44d4a8676142776a2797 | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | e2cc498d683235f7b9e94e08ddcbd3de3bbbc81380ae81206d40c6083dc86672 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `33`
- Chain head: `9119829b1423c37a1d8817340c91ea8c529e3defeb951d11d195aad721621ebf`
