# Orchestration Wave 1

- Run: `d2bc327185d0479395b57a06d4650f70`
- Wave: `0824fe99d0274225bbc7b8a80128a4bd`
- Objective: Correct the stale integration oracle for acceptance observation spans under Parent Problem prl-22e670302757c9b7663170e226ed7c26 revision 1. Current authoritative behavior records three acceptance measurements on same-clock normal acceptance: observed_stage_duration, controller_processing, and acceptance_wait; tests/test_orchestration_control.py already validates controller_processing and acceptance_wait. Update only tests/test_orchestration_workflow.py::test_runtime_records_content_free_a2_stage_spans_without_new_contract_surface so it validates those three measurements and their stable span IDs instead of requiring exactly one acceptance span. Do not change production telemetry or controller-lease behavior. Then run the focused test and the affected execution_hub/controller/orchestration suite. No packaging/install/reboot/runtime restart/commit/push/release/deploy.
- Objective revision: `1`
- Objective SHA-256: `46508939fb1680fb0c1bb2dd6c4e23cfd2d5fd0825448e07ae3b15c81b5dc645`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6`
- Worktree fingerprint: `e548b43d9d334d4b6b8710e81f1daaa9333ade6628cdade5c8974e81c3e5a707`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 55591 | 2026-09-15T02:39:53.055Z | run_started |  | PREFLIGHT |  |
| 55592 | 2026-09-15T02:39:53.720Z | observation_span_recorded |  |  |  |
| 55593 | 2026-09-15T02:39:58.666Z | observation_span_recorded |  |  |  |
| 55594 | 2026-09-15T02:39:58.866Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 55595 | 2026-09-15T02:39:59.090Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 55596 | 2026-09-15T02:39:59.313Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 55597 | 2026-09-15T02:39:59.524Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 55598 | 2026-09-15T02:39:59.715Z | state_transition | READY | ROUTED | reason=route_selected |
| 55599 | 2026-09-15T02:39:59.911Z | observation_span_recorded |  |  |  |
| 55600 | 2026-09-15T02:40:00.411Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=c8ed67a16d8f444e841a08eefebf1df7 |
| 55601 | 2026-09-15T02:40:00.639Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 55602 | 2026-09-15T02:40:01.116Z | patch_surface_observed |  |  |  |
| 55603 | 2026-09-15T02:40:01.354Z | observation_span_recorded |  |  |  |
| 55604 | 2026-09-15T02:40:01.622Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=c8ed67a16d8f444e841a08eefebf1df7 |
| 55605 | 2026-09-15T02:40:01.822Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 55606 | 2026-09-15T02:40:02.307Z | proof_cache_miss |  |  | reason=cold; stage_id=check:61fe412bab5eabf9; input_fingerprint=27946311f3385c31b7ced9c5a7be77dfe8f5001856a91c9771eff9adfee22e12 |
| 55607 | 2026-09-15T02:40:02.733Z | managed_process_admitted |  |  | owner=default |
| 55608 | 2026-09-15T02:40:03.004Z | managed_process_started |  |  | owner=default |
| 55609 | 2026-09-15T02:40:10.370Z | managed_process_terminal |  |  | owner=default |
| 55610 | 2026-09-15T02:40:10.654Z | proof_recorded |  |  | stage_id=check:61fe412bab5eabf9; status=passed; cache_hit=False; input_fingerprint=27946311f3385c31b7ced9c5a7be77dfe8f5001856a91c9771eff9adfee22e12 |
| 55611 | 2026-09-15T02:40:10.846Z | proof_cache_miss |  |  | reason=cold; stage_id=check:aec52a94f06cb088; input_fingerprint=18a359c4a17af64d3d509c900b4cc27e04b340b857340b76e46ac61a02e6cc62 |
| 55612 | 2026-09-15T02:40:11.242Z | managed_process_admitted |  |  | owner=default |
| 55613 | 2026-09-15T02:40:11.548Z | managed_process_started |  |  | owner=default |
| 55617 | 2026-09-15T02:41:59.867Z | managed_process_terminal |  |  | owner=default |
| 55618 | 2026-09-15T02:42:00.228Z | proof_recorded |  |  | stage_id=check:aec52a94f06cb088; status=passed; cache_hit=False; input_fingerprint=18a359c4a17af64d3d509c900b4cc27e04b340b857340b76e46ac61a02e6cc62 |
| 55619 | 2026-09-15T02:42:00.440Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=9e8e114951397551033cfb2ab653ed8e8e97b1b2abce37d608170dec7142d550 |
| 55620 | 2026-09-15T02:42:00.996Z | managed_process_admitted |  |  | owner=default |
| 55621 | 2026-09-15T02:42:01.308Z | managed_process_started |  |  | owner=default |
| 55627 | 2026-09-15T02:49:47.405Z | managed_process_terminal |  |  | owner=default |
| 55628 | 2026-09-15T02:49:47.791Z | proof_recorded |  |  | stage_id=verify:tests; status=failed; cache_hit=False; input_fingerprint=9e8e114951397551033cfb2ab653ed8e8e97b1b2abce37d608170dec7142d550 |
| 55629 | 2026-09-15T02:49:47.995Z | observation_span_recorded |  |  |  |
| 55630 | 2026-09-15T02:49:48.281Z | failure_observed | PROVING | PROVING | failure_class=DEADLINE |
| 55631 | 2026-09-15T02:49:48.548Z | state_transition | PROVING | REPLAN | reason=DEADLINE; failure_class=DEADLINE |
| 55632 | 2026-09-15T02:49:48.831Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |
| 55633 | 2026-09-15T02:51:30.177Z | continuity_telemetry_recorded |  |  |  |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:61fe412bab5eabf9 | passed | 27946311f3385c31b7ced9c5a7be77dfe8f5001856a91c9771eff9adfee22e12 | False | 8019 | 0 |
| check:aec52a94f06cb088 | passed | 18a359c4a17af64d3d509c900b4cc27e04b340b857340b76e46ac61a02e6cc62 | False | 109027 | 0 |
| verify:tests | failed | 9e8e114951397551033cfb2ab653ed8e8e97b1b2abce37d608170dec7142d550 | False | 466765 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `158`
- Chain head: `c01be013329975477f9ecbdbe2b7c01d14beb8d1ff86e41615558beb70a5215b`
