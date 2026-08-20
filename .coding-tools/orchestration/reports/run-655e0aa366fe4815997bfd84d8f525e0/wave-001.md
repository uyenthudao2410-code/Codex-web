# Orchestration Wave 1

- Run: `655e0aa366fe4815997bfd84d8f525e0`
- Wave: `5f7e7d25c41c42b1879a3c921d483f63`
- Objective: Fix only the two known research-stress fixture defects G04_cross_source_stable_signal_recovers and S01_rare_positive_strong_signal_recovers. Do not change canonical validator semantics, readiness thresholds, promotion policy, P5 treatment behavior, or synthetic promotion rules. Preserve the v5 validator behavior that already makes G03/M01/T02 pass. Acceptance: raw run_p4_research_stress_suite.py must become 35/35 PASS with blind_spots=[], multilayer strict must remain 37/37 PASS with canonical non-interference, and canonical readiness before/after the benchmark must remain unchanged. Do not commit, push, restart, or activate treatment in this wave.
- Mode: `mcp_only`
- Base HEAD: `4aa8a99b877f20b5f2f4bb2ce50e0cbc477a25d2`
- Worktree fingerprint: `ecaacde45b521a1dc0904e2842069b369a8f161ef0e03206425e91bf20633f15`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 22518 | 2026-08-20T04:27:55.424Z | run_started |  | PREFLIGHT |  |
| 22519 | 2026-08-20T04:27:56.289Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 22520 | 2026-08-20T04:28:22.730Z | managed_process_admitted |  |  | owner=default |
| 22521 | 2026-08-20T04:28:23.104Z | managed_process_started |  |  | owner=default |
| 22522 | 2026-08-20T04:28:24.764Z | managed_process_terminal |  |  | owner=default |
| 22523 | 2026-08-20T04:29:06.577Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 22524 | 2026-08-20T04:29:06.729Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 22525 | 2026-08-20T04:29:06.867Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 22526 | 2026-08-20T04:29:07.063Z | state_transition | READY | ROUTED | reason=route_selected |
| 22527 | 2026-08-20T04:29:07.597Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=171c8fc85a7f40ccace9e915a79f39ee |
| 22528 | 2026-08-20T04:29:07.727Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 22529 | 2026-08-20T04:29:08.168Z | patch_surface_observed |  |  |  |
| 22530 | 2026-08-20T04:29:08.522Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=171c8fc85a7f40ccace9e915a79f39ee |
| 22531 | 2026-08-20T04:29:08.635Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 22532 | 2026-08-20T04:29:08.951Z | proof_cache_miss |  |  | reason=cold; stage_id=check:3045ec66daf3a081; input_fingerprint=e08a8ec180c82298dc42e1875fa8327d989d92ad1ed53775f4b6543ec8fdf17c |
| 22533 | 2026-08-20T04:29:09.297Z | managed_process_admitted |  |  | owner=default |
| 22534 | 2026-08-20T04:29:09.568Z | managed_process_started |  |  | owner=default |
| 22535 | 2026-08-20T04:29:10.021Z | managed_process_terminal |  |  | owner=default |
| 22536 | 2026-08-20T04:29:10.373Z | proof_recorded |  |  | stage_id=check:3045ec66daf3a081; status=passed; cache_hit=False; input_fingerprint=e08a8ec180c82298dc42e1875fa8327d989d92ad1ed53775f4b6543ec8fdf17c |
| 22537 | 2026-08-20T04:29:10.507Z | proof_cache_miss |  |  | reason=cold; stage_id=check:fd71cdc4b22e7c92; input_fingerprint=7f7a7b6ddda94764ab6f6c81f9b2144115e693618931b6748d2ab656833a4787 |
| 22538 | 2026-08-20T04:29:10.871Z | managed_process_admitted |  |  | owner=default |
| 22539 | 2026-08-20T04:29:11.199Z | managed_process_started |  |  | owner=default |
| 22540 | 2026-08-20T04:29:35.810Z | managed_process_terminal |  |  | owner=default |
| 22541 | 2026-08-20T04:29:36.127Z | proof_recorded |  |  | stage_id=check:fd71cdc4b22e7c92; status=failed; cache_hit=False; input_fingerprint=7f7a7b6ddda94764ab6f6c81f9b2144115e693618931b6748d2ab656833a4787 |
| 22542 | 2026-08-20T04:29:36.316Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 22543 | 2026-08-20T04:29:36.484Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 22544 | 2026-08-20T04:29:36.641Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:3045ec66daf3a081 | passed | e08a8ec180c82298dc42e1875fa8327d989d92ad1ed53775f4b6543ec8fdf17c | False | 1085 | 0 |
| check:fd71cdc4b22e7c92 | failed | 7f7a7b6ddda94764ab6f6c81f9b2144115e693618931b6748d2ab656833a4787 | False | 25318 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `66`
- Chain head: `261defdf25750d0535920a99325b36111e5b3a30c65d20ff950f86e6b7dd7a6e`
