# Orchestration Wave 2

- Run: `3c3564b92e5643e7b1248b94bd5386a5`
- Wave: `1709e8853e67498d90cc107f2f1e9339`
- Objective: Repair the Operator Control Panel live-routing path so realtime node states do not depend on heavyweight orchestration analytics. Add an authorized /__control/orchestration/live path backed by a live=True branch of the existing snapshot builder; live mode must return only panel-required authoritative state before usage_analytics, operations_analytics, routing_evidence, flight_recorder, history and resume work. Keep /__control/orchestration full behavior for manager/dashboard. Add panel:live-control IPC with 2500ms timeout; panelPreload uses it while manager preload remains on panel:orchestration. Preserve renderer fail-closed/evidence-gated semantics and usage truth contracts. Add focused regression tests. Preserve unrelated WIP. No commit/push/restart/deploy/release.
- Mode: `mcp_only`
- Base HEAD: `5f059a1a53ff2beb9adfa4f2df9ee42907141816`
- Worktree fingerprint: `9ca9ce0dea1779277cd62a634619149efeecc96848687654f317fd33589b9e8f`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 23387 | 2026-08-20T07:58:54.013Z | wave_replanned |  | PREFLIGHT | reason=BUILD_VERIFICATION_FAILED: the functional patch passed Node syntax and diff hygiene but violated the repository module-size architecture guard because the live projection was added inside mcp_http_handler.py. Changed strategy: move live-control projection into its own domain module and keep the HTTP handler thin; do not weaken the guard or retry the unchanged shape. |
| 23388 | 2026-08-20T07:58:55.370Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 23389 | 2026-08-20T07:59:16.910Z | managed_process_admitted |  |  | owner=default |
| 23390 | 2026-08-20T07:59:17.707Z | managed_process_started |  |  | owner=default |
| 23391 | 2026-08-20T07:59:18.660Z | managed_process_terminal |  |  | owner=default |
| 23392 | 2026-08-20T07:59:45.806Z | managed_process_admitted |  |  | owner=default |
| 23393 | 2026-08-20T07:59:46.773Z | managed_process_started |  |  | owner=default |
| 23394 | 2026-08-20T07:59:47.575Z | managed_process_terminal |  |  | owner=default |
| 23395 | 2026-08-20T08:01:43.723Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 23396 | 2026-08-20T08:01:44.264Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 23397 | 2026-08-20T08:01:44.638Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 23398 | 2026-08-20T08:01:45.029Z | state_transition | READY | ROUTED | reason=route_selected |
| 23399 | 2026-08-20T08:01:46.155Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=b8b8d35860b84d3c980d3d2dcab3fd75 |
| 23400 | 2026-08-20T08:01:46.553Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 23401 | 2026-08-20T08:01:47.944Z | patch_surface_observed |  |  |  |
| 23402 | 2026-08-20T08:01:48.645Z | patch_surface_observed |  |  |  |
| 23403 | 2026-08-20T08:01:49.689Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=b8b8d35860b84d3c980d3d2dcab3fd75 |
| 23404 | 2026-08-20T08:01:50.122Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 23405 | 2026-08-20T08:01:51.238Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:0cfc52e6cfded4a5; input_fingerprint=07447b7376f1612da96815cc6c4cab1284ba1699106d449c2b6e12b87bf0430b |
| 23406 | 2026-08-20T08:01:53.371Z | managed_process_admitted |  |  | owner=default |
| 23407 | 2026-08-20T08:01:54.205Z | managed_process_started |  |  | owner=default |
| 23408 | 2026-08-20T08:01:55.365Z | managed_process_terminal |  |  | owner=default |
| 23409 | 2026-08-20T08:01:56.088Z | proof_recorded |  |  | stage_id=check:0cfc52e6cfded4a5; status=passed; cache_hit=False; input_fingerprint=07447b7376f1612da96815cc6c4cab1284ba1699106d449c2b6e12b87bf0430b |
| 23410 | 2026-08-20T08:01:57.227Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:f14c9da7481385d8; input_fingerprint=d5ec514e9d20cd1b4c71442ab247b9f169cd73a0488a703d2838ebdc19b1301b |
| 23411 | 2026-08-20T08:01:58.874Z | managed_process_admitted |  |  | owner=default |
| 23412 | 2026-08-20T08:01:59.754Z | managed_process_started |  |  | owner=default |
| 23413 | 2026-08-20T08:02:00.620Z | managed_process_terminal |  |  | owner=default |
| 23414 | 2026-08-20T08:02:01.357Z | proof_recorded |  |  | stage_id=check:f14c9da7481385d8; status=passed; cache_hit=False; input_fingerprint=d5ec514e9d20cd1b4c71442ab247b9f169cd73a0488a703d2838ebdc19b1301b |
| 23415 | 2026-08-20T08:02:02.388Z | proof_cache_miss |  |  | reason=cold; stage_id=check:813862b0d2d03edf; input_fingerprint=1e07521380999594255d12ff637561a1246ed298d383265c8decf0b6e991e1bc |
| 23416 | 2026-08-20T08:02:04.018Z | managed_process_admitted |  |  | owner=default |
| 23417 | 2026-08-20T08:02:04.809Z | managed_process_started |  |  | owner=default |
| 23418 | 2026-08-20T08:02:05.677Z | managed_process_terminal |  |  | owner=default |
| 23419 | 2026-08-20T08:02:06.521Z | proof_recorded |  |  | stage_id=check:813862b0d2d03edf; status=passed; cache_hit=False; input_fingerprint=1e07521380999594255d12ff637561a1246ed298d383265c8decf0b6e991e1bc |
| 23420 | 2026-08-20T08:02:07.753Z | proof_cache_miss |  |  | reason=cold; stage_id=check:cf18ebf0fab8217f; input_fingerprint=d0b49102a6e7670f3aa7a12d60dd8275ef99f7971afb7b66a9538d5a2e020d26 |
| 23421 | 2026-08-20T08:02:09.568Z | managed_process_admitted |  |  | owner=default |
| 23422 | 2026-08-20T08:02:10.401Z | managed_process_started |  |  | owner=default |
| 23423 | 2026-08-20T08:02:11.338Z | managed_process_terminal |  |  | owner=default |
| 23424 | 2026-08-20T08:02:12.171Z | proof_recorded |  |  | stage_id=check:cf18ebf0fab8217f; status=passed; cache_hit=False; input_fingerprint=d0b49102a6e7670f3aa7a12d60dd8275ef99f7971afb7b66a9538d5a2e020d26 |
| 23425 | 2026-08-20T08:02:13.325Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=70d3c26af7e0bcca734428e88c9b6e51794d0fb14c93f3b6c2b0aeae79c24b42 |
| 23426 | 2026-08-20T08:02:15.519Z | managed_process_admitted |  |  | owner=default |
| 23427 | 2026-08-20T08:02:16.306Z | managed_process_started |  |  | owner=default |
| 23428 | 2026-08-20T08:02:25.445Z | managed_process_terminal |  |  | owner=default |
| 23429 | 2026-08-20T08:02:28.153Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=70d3c26af7e0bcca734428e88c9b6e51794d0fb14c93f3b6c2b0aeae79c24b42 |
| 23430 | 2026-08-20T08:02:28.988Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 23431 | 2026-08-20T08:22:15.532Z | quality_outcome_recorded |  |  |  |
| 23432 | 2026-08-20T08:22:16.023Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 23433 | 2026-08-20T08:22:18.379Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:0cfc52e6cfded4a5 | passed | 07447b7376f1612da96815cc6c4cab1284ba1699106d449c2b6e12b87bf0430b | False | 4109 | 0 |
| check:f14c9da7481385d8 | passed | d5ec514e9d20cd1b4c71442ab247b9f169cd73a0488a703d2838ebdc19b1301b | False | 3408 | 0 |
| check:813862b0d2d03edf | passed | 1e07521380999594255d12ff637561a1246ed298d383265c8decf0b6e991e1bc | False | 3388 | 0 |
| check:cf18ebf0fab8217f | passed | d0b49102a6e7670f3aa7a12d60dd8275ef99f7971afb7b66a9538d5a2e020d26 | False | 3526 | 0 |
| verify:tests | passed | 70d3c26af7e0bcca734428e88c9b6e51794d0fb14c93f3b6c2b0aeae79c24b42 | False | 13687 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 7fd720871130450a95eead0e88454555 | accepted | 5f059a1a53ff2beb9adfa4f2df9ee42907141816 | 47b71099be17ae8c009ab6e9cf9e596d0c0418948adae2644baa6a53bd24f04b | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `82`
- Chain head: `83d250b614b6956661accaea43ed894b141cfb5de6f6df5d2052d26ad92d4b4a`
