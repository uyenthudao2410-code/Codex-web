# Orchestration Wave 1

- Run: `54f3828441a747fa94aca227a10f1dac`
- Wave: `632362e0077d4fcd89e488bfb37f080a`
- Objective: Fix the Recovery Supervisor deferred-envelope contract mismatch so Get-DeferredRequest continues requiring source_checkpoint but treats trusted_recovery_bootstrap as optional: read it via Get-OptionalProperty and fail closed only when a present value is not a PSCustomObject. Update only the existing deferred-worker supervisor test so the canonical live request omits trusted_recovery_bootstrap and still launches exactly one worker, preserving expired-request and all other checks. Preserve all unrelated pre-existing WIP bytes in exactly these two already-dirty files.
- Objective revision: `1`
- Objective SHA-256: `a2097abf936b40dba654e63743b9163b690cd0d2f475ef47e0440e511601b1f7`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `7bc1caee37107a15e74eb078b52fe314e5fa33ab`
- Worktree fingerprint: `c1cab4fb02990a1430fe0a09bc30714357ae3344c7d25a3365d4f0f2b7e0268d`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 44608 | 2026-09-08T19:34:45.307Z | run_started |  | PREFLIGHT |  |
| 44609 | 2026-09-08T19:34:45.694Z | observation_span_recorded |  |  |  |
| 44610 | 2026-09-08T19:34:45.924Z | solution_shadow_recommended |  |  |  |
| 44611 | 2026-09-08T19:34:55.909Z | observation_span_recorded |  |  |  |
| 44612 | 2026-09-08T19:34:56.132Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 44613 | 2026-09-08T19:35:40.622Z | managed_process_admitted |  |  | owner=default |
| 44614 | 2026-09-08T19:35:41.005Z | managed_process_started |  |  | owner=default |
| 44615 | 2026-09-08T19:35:41.504Z | managed_process_terminal |  |  | owner=default |
| 44616 | 2026-09-08T19:36:13.572Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 44617 | 2026-09-08T19:36:13.791Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 44618 | 2026-09-08T19:36:13.992Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 44619 | 2026-09-08T19:36:14.176Z | state_transition | READY | ROUTED | reason=route_selected |
| 44620 | 2026-09-08T19:36:14.391Z | observation_span_recorded |  |  |  |
| 44621 | 2026-09-08T19:36:15.168Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=26c35d790e4b4953826b4113d26fd22b |
| 44622 | 2026-09-08T19:36:15.352Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 44623 | 2026-09-08T19:36:16.130Z | patch_surface_observed |  |  |  |
| 44624 | 2026-09-08T19:36:16.402Z | observation_span_recorded |  |  |  |
| 44625 | 2026-09-08T19:36:16.671Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=26c35d790e4b4953826b4113d26fd22b |
| 44626 | 2026-09-08T19:36:16.838Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 44627 | 2026-09-08T19:36:17.741Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:fe3ffbf7aa7a92a6; input_fingerprint=64f4f089fca85f1e247314f6cc41b2a5c376eb00d346f6f3f62cd22eb59f4072 |
| 44628 | 2026-09-08T19:36:18.096Z | managed_process_admitted |  |  | owner=default |
| 44629 | 2026-09-08T19:36:18.422Z | managed_process_started |  |  | owner=default |
| 44630 | 2026-09-08T19:36:40.138Z | managed_process_terminal |  |  | owner=default |
| 44631 | 2026-09-08T19:36:40.538Z | proof_recorded |  |  | stage_id=check:fe3ffbf7aa7a92a6; status=passed; cache_hit=False; input_fingerprint=64f4f089fca85f1e247314f6cc41b2a5c376eb00d346f6f3f62cd22eb59f4072 |
| 44632 | 2026-09-08T19:36:40.746Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:d748b3f2c2065ed5; input_fingerprint=d3613ca69ffc03201e951a4251e3a313ef45255444ddda6666715689482ec7de |
| 44633 | 2026-09-08T19:36:41.088Z | managed_process_admitted |  |  | owner=default |
| 44634 | 2026-09-08T19:36:41.355Z | managed_process_started |  |  | owner=default |
| 44635 | 2026-09-08T19:36:41.763Z | managed_process_terminal |  |  | owner=default |
| 44636 | 2026-09-08T19:36:42.055Z | proof_recorded |  |  | stage_id=check:d748b3f2c2065ed5; status=passed; cache_hit=False; input_fingerprint=d3613ca69ffc03201e951a4251e3a313ef45255444ddda6666715689482ec7de |
| 44637 | 2026-09-08T19:36:42.875Z | observation_span_recorded |  |  |  |
| 44638 | 2026-09-08T19:36:43.354Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 44639 | 2026-09-08T19:37:03.376Z | managed_process_admitted |  |  | owner=default |
| 44640 | 2026-09-08T19:37:03.884Z | managed_process_started |  |  | owner=default |
| 44641 | 2026-09-08T19:37:04.474Z | managed_process_terminal |  |  | owner=default |
| 44642 | 2026-09-08T19:37:20.418Z | quality_outcome_recorded |  |  |  |
| 44643 | 2026-09-08T19:37:20.619Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 44644 | 2026-09-08T19:37:20.868Z | observation_span_recorded |  |  |  |
| 44645 | 2026-09-08T19:37:21.084Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:fe3ffbf7aa7a92a6 | passed | 64f4f089fca85f1e247314f6cc41b2a5c376eb00d346f6f3f62cd22eb59f4072 | False | 22452 | 0 |
| check:d748b3f2c2065ed5 | passed | d3613ca69ffc03201e951a4251e3a313ef45255444ddda6666715689482ec7de | False | 1021 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 16b78589129447da882f39ce58ede8e8 | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | 062451b822ee95579f058442237660f18acdd50f08f2c3fb7fdc306f567f687b | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `38`
- Chain head: `374a1c3f5c8bb7c8261acf45f514ec6a4ab7dfa5eeecd76437dfe20d13bdf8df`
