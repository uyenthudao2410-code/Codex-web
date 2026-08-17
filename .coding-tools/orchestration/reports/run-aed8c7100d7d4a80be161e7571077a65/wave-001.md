# Orchestration Wave 1

- Run: `aed8c7100d7d4a80be161e7571077a65`
- Wave: `ffb53a382c554bada1e4a3a259b98333`
- Objective: Close the final pre-P3 preregistration analysis gap without starting any P3 treatment. Generalize the existing compare_route_policies CLI so it accepts arbitrary explicit policy identifiers while keeping mini/luna as defaults when omitted, and add focused regression proving the generic paired-policy evaluator accepts LOCAL_FIRST_V1 versus SERVER_FIRST_DETERMINISTIC_V1 with exact representative pair identity. Do not change ledger semantics, public MCP schema, routing authority, automatic activation, or run any representative P3 treatment.
- Mode: `mcp_only`
- Base HEAD: `bc07e240740726d9a5ddbd590e01568344a92440`
- Worktree fingerprint: `7aa7dd66c9489dc8071ba6f75b0b0de0aad2c2caf46c08311f850501c3092120`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 15682 | 2026-08-17T19:56:17.199Z | run_started |  | PREFLIGHT |  |
| 15683 | 2026-08-17T19:56:17.626Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 15684 | 2026-08-17T19:56:17.733Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 15685 | 2026-08-17T19:56:17.855Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 15686 | 2026-08-17T19:56:17.980Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 15687 | 2026-08-17T19:56:18.105Z | state_transition | READY | ROUTED | reason=route_selected |
| 15688 | 2026-08-17T19:56:18.532Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=9b9a84c23d674b1482a6ecebc8074ede |
| 15689 | 2026-08-17T19:56:18.632Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 15690 | 2026-08-17T19:56:19.066Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=9b9a84c23d674b1482a6ecebc8074ede |
| 15691 | 2026-08-17T19:56:19.183Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 15692 | 2026-08-17T19:56:19.520Z | proof_cache_miss |  |  | reason=cold; stage_id=check:d9a732e581c2f22f; input_fingerprint=607169f5db181ed433cc8ce9211cfa00fef2d4108e78ad73c74a7b823d692ca0 |
| 15693 | 2026-08-17T19:56:19.779Z | managed_process_admitted |  |  | owner=default |
| 15694 | 2026-08-17T19:56:20.004Z | managed_process_started |  |  | owner=default |
| 15695 | 2026-08-17T19:56:20.416Z | managed_process_terminal |  |  | owner=default |
| 15696 | 2026-08-17T19:56:20.713Z | proof_recorded |  |  | stage_id=check:d9a732e581c2f22f; status=passed; cache_hit=False; input_fingerprint=607169f5db181ed433cc8ce9211cfa00fef2d4108e78ad73c74a7b823d692ca0 |
| 15697 | 2026-08-17T19:56:20.833Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:80a1a46bd01d26a3; input_fingerprint=9f9b7229835bcfc848736a620f17998c64564707ef6139e79b75960cca04ae9f |
| 15698 | 2026-08-17T19:56:21.096Z | managed_process_admitted |  |  | owner=default |
| 15699 | 2026-08-17T19:56:21.315Z | managed_process_started |  |  | owner=default |
| 15700 | 2026-08-17T19:56:21.763Z | managed_process_terminal |  |  | owner=default |
| 15701 | 2026-08-17T19:56:21.963Z | proof_recorded |  |  | stage_id=check:80a1a46bd01d26a3; status=passed; cache_hit=False; input_fingerprint=9f9b7229835bcfc848736a620f17998c64564707ef6139e79b75960cca04ae9f |
| 15702 | 2026-08-17T19:56:22.075Z | proof_cache_miss |  |  | reason=cold; stage_id=check:5b6d1dc63b585e6e; input_fingerprint=4277d6638a9932af40458058400b2bacfb3dff51506aab55e97684b481f47adc |
| 15703 | 2026-08-17T19:56:22.313Z | managed_process_admitted |  |  | owner=default |
| 15704 | 2026-08-17T19:56:22.625Z | managed_process_started |  |  | owner=default |
| 15705 | 2026-08-17T19:56:22.980Z | managed_process_terminal |  |  | owner=default |
| 15706 | 2026-08-17T19:56:23.253Z | proof_recorded |  |  | stage_id=check:5b6d1dc63b585e6e; status=passed; cache_hit=False; input_fingerprint=4277d6638a9932af40458058400b2bacfb3dff51506aab55e97684b481f47adc |
| 15707 | 2026-08-17T19:56:23.369Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=00f393fa90e16089ab24057257304bf31504e95c723ea0c597229994ddcd0fe0 |
| 15708 | 2026-08-17T19:56:23.634Z | managed_process_admitted |  |  | owner=default |
| 15709 | 2026-08-17T19:56:23.883Z | managed_process_started |  |  | owner=default |
| 15710 | 2026-08-17T19:56:30.055Z | managed_process_terminal |  |  | owner=default |
| 15711 | 2026-08-17T19:56:31.014Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=00f393fa90e16089ab24057257304bf31504e95c723ea0c597229994ddcd0fe0 |
| 15712 | 2026-08-17T19:56:31.480Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 15713 | 2026-08-17T19:57:47.119Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 15714 | 2026-08-17T19:57:47.368Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:d9a732e581c2f22f | passed | 607169f5db181ed433cc8ce9211cfa00fef2d4108e78ad73c74a7b823d692ca0 | False | 940 | 0 |
| check:80a1a46bd01d26a3 | passed | 9f9b7229835bcfc848736a620f17998c64564707ef6139e79b75960cca04ae9f | False | 905 | 0 |
| check:5b6d1dc63b585e6e | passed | 4277d6638a9932af40458058400b2bacfb3dff51506aab55e97684b481f47adc | False | 939 | 0 |
| verify:tests | passed | 00f393fa90e16089ab24057257304bf31504e95c723ea0c597229994ddcd0fe0 | False | 7344 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 646274209f734ba7b396ccbfe2913aaa | accepted | bc07e240740726d9a5ddbd590e01568344a92440 | e438083c5b379c8d983bc96a1b8e9d53180f961be9a0564fe25ca95e187238af | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `33`
- Chain head: `a5f7004415ce1408666ea50aea7652a1d91cfec2bb26e775dfcfb666a606b77e`
