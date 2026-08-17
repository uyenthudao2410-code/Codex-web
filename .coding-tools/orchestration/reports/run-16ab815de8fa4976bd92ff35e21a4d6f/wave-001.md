# Orchestration Wave 1

- Run: `16ab815de8fa4976bd92ff35e21a4d6f`
- Wave: `72524477cded4457858d1ae2e8426e12`
- Objective: Implement and close P1.3 Controller Usage Coverage only. Add a causal explicit experimental-enrollment denominator to current_ledger_baseline controller coverage; count controller started_at/token/cost/source only for enrolled experimental runs, keep missing telemetry unknown, and fail closed for promotion economics when enrolled controller monetary-cost coverage is incomplete. Preserve all-history controller counts only if clearly labeled separately; do not let organic host trace/turn identity enter the experimental denominator. Add focused regression tests. Do not implement P1.4, change routing/public schema/DB, or restart runtime.
- Mode: `mcp_only`
- Base HEAD: `db4e295cdd2cf71c0a4d0b91f1e5dcb5f9e6e4dc`
- Worktree fingerprint: `b4557a1b5fa4280fbf3c1c7f9a6ba92c485b37a76bad91cfb4333b152db50991`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 14492 | 2026-08-17T16:24:10.226Z | run_started |  | PREFLIGHT |  |
| 14493 | 2026-08-17T16:24:10.352Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 14494 | 2026-08-17T16:24:10.529Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 14495 | 2026-08-17T16:24:10.709Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 14496 | 2026-08-17T16:24:10.825Z | state_transition | READY | ROUTED | reason=route_selected |
| 14497 | 2026-08-17T16:24:11.442Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=f636682e23cd4e7ba516566e2f159977 |
| 14498 | 2026-08-17T16:24:11.576Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 14499 | 2026-08-17T16:24:12.260Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=f636682e23cd4e7ba516566e2f159977 |
| 14500 | 2026-08-17T16:24:12.360Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 14501 | 2026-08-17T16:24:12.858Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:80a1a46bd01d26a3; input_fingerprint=0d16750003a43e5028a5066bffe50fadaae23d1bca87a87853992d3c7b96956c |
| 14502 | 2026-08-17T16:24:13.092Z | managed_process_admitted |  |  | owner=default |
| 14503 | 2026-08-17T16:24:13.330Z | managed_process_started |  |  | owner=default |
| 14504 | 2026-08-17T16:24:13.718Z | managed_process_terminal |  |  | owner=default |
| 14505 | 2026-08-17T16:24:13.993Z | proof_recorded |  |  | stage_id=check:80a1a46bd01d26a3; status=passed; cache_hit=False; input_fingerprint=0d16750003a43e5028a5066bffe50fadaae23d1bca87a87853992d3c7b96956c |
| 14506 | 2026-08-17T16:24:14.118Z | proof_cache_miss |  |  | reason=cold; stage_id=check:04e37108a6daf03e; input_fingerprint=9a4c29877c41b75541653725cf3c5987eb6589f9ac3f54bea023812ef13e5fdb |
| 14507 | 2026-08-17T16:24:14.384Z | managed_process_admitted |  |  | owner=default |
| 14508 | 2026-08-17T16:24:14.650Z | managed_process_started |  |  | owner=default |
| 14509 | 2026-08-17T16:24:15.015Z | managed_process_terminal |  |  | owner=default |
| 14510 | 2026-08-17T16:24:15.250Z | proof_recorded |  |  | stage_id=check:04e37108a6daf03e; status=passed; cache_hit=False; input_fingerprint=9a4c29877c41b75541653725cf3c5987eb6589f9ac3f54bea023812ef13e5fdb |
| 14511 | 2026-08-17T16:24:15.406Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=ac3d1015d9707e8ca8e3cd4ad8a9877b11f4aa4d9f05b2b3c5f5353f1c4d101f |
| 14512 | 2026-08-17T16:24:15.705Z | managed_process_admitted |  |  | owner=default |
| 14513 | 2026-08-17T16:24:15.963Z | managed_process_started |  |  | owner=default |
| 14514 | 2026-08-17T16:24:17.429Z | managed_process_terminal |  |  | owner=default |
| 14515 | 2026-08-17T16:24:22.509Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=ac3d1015d9707e8ca8e3cd4ad8a9877b11f4aa4d9f05b2b3c5f5353f1c4d101f |
| 14516 | 2026-08-17T16:24:23.242Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 14517 | 2026-08-17T16:25:42.695Z | managed_process_admitted |  |  | owner=default |
| 14518 | 2026-08-17T16:25:43.503Z | managed_process_started |  |  | owner=default |
| 14519 | 2026-08-17T16:25:49.610Z | managed_process_terminal |  |  | owner=default |
| 14520 | 2026-08-17T16:26:02.231Z | managed_process_admitted |  |  | owner=default |
| 14521 | 2026-08-17T16:26:02.620Z | managed_process_started |  |  | owner=default |
| 14522 | 2026-08-17T16:26:03.097Z | managed_process_terminal |  |  | owner=default |
| 14523 | 2026-08-17T16:26:51.794Z | managed_process_admitted |  |  | owner=default |
| 14524 | 2026-08-17T16:26:52.110Z | managed_process_started |  |  | owner=default |
| 14525 | 2026-08-17T16:26:52.585Z | managed_process_terminal |  |  | owner=default |
| 14526 | 2026-08-17T16:27:53.759Z | managed_process_admitted |  |  | owner=default |
| 14527 | 2026-08-17T16:27:54.073Z | managed_process_started |  |  | owner=default |
| 14528 | 2026-08-17T16:27:54.603Z | managed_process_terminal |  |  | owner=default |
| 14529 | 2026-08-17T16:28:03.077Z | managed_process_admitted |  |  | owner=default |
| 14530 | 2026-08-17T16:28:03.356Z | managed_process_started |  |  | owner=default |
| 14531 | 2026-08-17T16:28:04.061Z | managed_process_terminal |  |  | owner=default |
| 14532 | 2026-08-17T16:28:11.690Z | managed_process_admitted |  |  | owner=default |
| 14533 | 2026-08-17T16:28:12.122Z | managed_process_started |  |  | owner=default |
| 14534 | 2026-08-17T16:28:12.602Z | managed_process_terminal |  |  | owner=default |
| 14535 | 2026-08-17T16:28:51.456Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 14536 | 2026-08-17T16:28:51.952Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:80a1a46bd01d26a3 | passed | 0d16750003a43e5028a5066bffe50fadaae23d1bca87a87853992d3c7b96956c | False | 900 | 0 |
| check:04e37108a6daf03e | passed | 9a4c29877c41b75541653725cf3c5987eb6589f9ac3f54bea023812ef13e5fdb | False | 899 | 0 |
| verify:tests | passed | ac3d1015d9707e8ca8e3cd4ad8a9877b11f4aa4d9f05b2b3c5f5353f1c4d101f | False | 6639 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| e448ffb3569f40e697ebdd784b9a2600 | accepted | db4e295cdd2cf71c0a4d0b91f1e5dcb5f9e6e4dc | 84ab8491ec4d290e08cab7af7f24444456121162ba477c060fe30282e3b9c5c6 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `45`
- Chain head: `ff2300b2f71a373369816b0bf92f9e34151f4d003f977faa2f7627f87260344c`
