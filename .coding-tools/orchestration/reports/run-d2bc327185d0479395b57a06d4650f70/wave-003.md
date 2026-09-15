# Orchestration Wave 3

- Run: `d2bc327185d0479395b57a06d4650f70`
- Wave: `6611889de49c4c15ba95c13a037e6c8d`
- Objective: Fix the independently reproduced stale runtime-component oracle in tests/test_efficiency_runtime.py. The live Runtime.loaded_behavior.components now authoritatively includes run_continuation_driver and run_continuation_autoresume in addition to the previously expected components. Update only the expected component set in EfficiencyRuntimeTests.test_runtime_startup_preserves_stale_candidates_until_explicit_reconcile. Preserve the existing observation-span oracle change in tests/test_orchestration_workflow.py unchanged. Then prove the entire efficiency_runtime file, the focused observation-span test, and the affected execution_hub/controller/orchestration suite. Do not modify production code or boot/recovery C01 files; no package/install/reboot/runtime restart/commit/push/publish/release/deploy.
- Objective revision: `3`
- Objective SHA-256: `c2d8363b522aecb59a247cd21faec2527423b6873d5660c29ff7547787a4eac7`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6`
- Worktree fingerprint: `41e7f3dd18caeb3ab9515177c88dea102b588f1b15502f4e45fe79c33b989d6b`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 55659 | 2026-09-15T02:53:48.596Z | wave_replanned |  | PREFLIGHT | reason=Focused verbose reproduction proved the only efficiency-runtime failure is a stale expected component set: current Runtime.loaded_behavior.components includes run_continuation_driver and run_continuation_autoresume. Patch only that oracle and verify focused/affected suites; do not retry the broad 1155-test suite in this wave. |
| 55660 | 2026-09-15T02:53:49.012Z | observation_span_recorded |  |  |  |
| 55661 | 2026-09-15T02:53:49.698Z | observation_span_recorded |  |  |  |
| 55662 | 2026-09-15T02:53:49.968Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 55663 | 2026-09-15T02:53:50.272Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 55664 | 2026-09-15T02:53:50.453Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 55665 | 2026-09-15T02:53:50.664Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 55666 | 2026-09-15T02:53:50.899Z | state_transition | READY | ROUTED | reason=route_selected |
| 55667 | 2026-09-15T02:53:51.300Z | observation_span_recorded |  |  |  |
| 55668 | 2026-09-15T02:53:51.958Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=70107b651ea445dd93b919e1f51908a3 |
| 55669 | 2026-09-15T02:53:52.133Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 55670 | 2026-09-15T02:53:52.810Z | patch_surface_observed |  |  |  |
| 55671 | 2026-09-15T02:53:53.117Z | observation_span_recorded |  |  |  |
| 55672 | 2026-09-15T02:53:53.775Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=70107b651ea445dd93b919e1f51908a3 |
| 55673 | 2026-09-15T02:53:54.138Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 55674 | 2026-09-15T02:53:54.700Z | proof_cache_miss |  |  | reason=cold; stage_id=check:33819b98d9cbbafe; input_fingerprint=95a7734e54855b55cf3766949ace2e70dd3181edb757e5875903c8718fd74a91 |
| 55675 | 2026-09-15T02:53:55.451Z | managed_process_admitted |  |  | owner=default |
| 55676 | 2026-09-15T02:53:56.010Z | managed_process_started |  |  | owner=default |
| 55677 | 2026-09-15T02:54:17.853Z | managed_process_terminal |  |  | owner=default |
| 55678 | 2026-09-15T02:54:18.603Z | proof_recorded |  |  | stage_id=check:33819b98d9cbbafe; status=passed; cache_hit=False; input_fingerprint=95a7734e54855b55cf3766949ace2e70dd3181edb757e5875903c8718fd74a91 |
| 55679 | 2026-09-15T02:54:18.905Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:61fe412bab5eabf9; input_fingerprint=dd87ce323a4f7e20cca2c44674524e3da32cf55d5fca18848bb0dc8bc6f024c0 |
| 55680 | 2026-09-15T02:54:19.606Z | managed_process_admitted |  |  | owner=default |
| 55681 | 2026-09-15T02:54:19.901Z | managed_process_started |  |  | owner=default |
| 55682 | 2026-09-15T02:54:27.642Z | managed_process_terminal |  |  | owner=default |
| 55683 | 2026-09-15T02:54:28.006Z | proof_recorded |  |  | stage_id=check:61fe412bab5eabf9; status=passed; cache_hit=False; input_fingerprint=dd87ce323a4f7e20cca2c44674524e3da32cf55d5fca18848bb0dc8bc6f024c0 |
| 55684 | 2026-09-15T02:54:28.245Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:aec52a94f06cb088; input_fingerprint=0ee8865f5c8ba91c399f2b369c65d7511b593ead2640333a3a21aa002eead93b |
| 55685 | 2026-09-15T02:54:28.576Z | managed_process_admitted |  |  | owner=default |
| 55686 | 2026-09-15T02:54:28.859Z | managed_process_started |  |  | owner=default |
| 55687 | 2026-09-15T02:56:19.883Z | managed_process_terminal |  |  | owner=default |
| 55688 | 2026-09-15T02:56:20.183Z | proof_recorded |  |  | stage_id=check:aec52a94f06cb088; status=passed; cache_hit=False; input_fingerprint=0ee8865f5c8ba91c399f2b369c65d7511b593ead2640333a3a21aa002eead93b |
| 55689 | 2026-09-15T02:56:20.769Z | observation_span_recorded |  |  |  |
| 55690 | 2026-09-15T02:56:21.048Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 55691 | 2026-09-15T02:56:21.298Z | observation_stage_anchor_recorded | ACCEPTING | ACCEPTING |  |
| 55692 | 2026-09-15T02:57:04.427Z | continuity_telemetry_recorded |  |  |  |
| 55693 | 2026-09-15T02:57:32.989Z | observation_span_recorded |  |  |  |
| 55694 | 2026-09-15T02:57:33.173Z | failure_observed | ACCEPTING | ACCEPTING | reason=Final acceptance failed closed because one pre-existing dirty acceptance path (tests/test_orchestration_workflow.py) was not proven inside the current wave's durable mutation surface/write lease. Replan the same RUN to an exact-byte adoption wave for both test files, rerun the focused/affected oracles, and only then final-accept.; failure_class=SOL_REJECTED |
| 55695 | 2026-09-15T02:57:33.373Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |
| 55696 | 2026-09-15T02:57:33.662Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |
| 55697 | 2026-09-15T02:58:53.814Z | continuity_telemetry_recorded |  |  |  |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:33819b98d9cbbafe | passed | 95a7734e54855b55cf3766949ace2e70dd3181edb757e5875903c8718fd74a91 | False | 23129 | 0 |
| check:61fe412bab5eabf9 | passed | dd87ce323a4f7e20cca2c44674524e3da32cf55d5fca18848bb0dc8bc6f024c0 | False | 8577 | 0 |
| check:aec52a94f06cb088 | passed | 0ee8865f5c8ba91c399f2b369c65d7511b593ead2640333a3a21aa002eead93b | False | 111614 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `158`
- Chain head: `c01be013329975477f9ecbdbe2b7c01d14beb8d1ff86e41615558beb70a5215b`
