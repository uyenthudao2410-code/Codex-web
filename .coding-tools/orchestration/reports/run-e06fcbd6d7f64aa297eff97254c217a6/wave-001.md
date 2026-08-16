# Orchestration Wave 1

- Run: `e06fcbd6d7f64aa297eff97254c217a6`
- Wave: `268172e916ef4268aa4a85d39003a647`
- Objective: Find stale R1 observability test expectations after R2B dispatch was enabled. Search only for assertions or fixtures expecting compute.mode="shadow" or compute.dispatch_enabled=false, especially runtime_status tests. Return exact locations; do not modify files.
- Mode: `mcp_only`
- Base HEAD: `cf6cb6ddbf29d90515d003ce72490ffda985c37f`
- Worktree fingerprint: `3fb599aab429b37755f783a7397a73d778c20c5cd6a9703de0930bcf685907d2`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 8359 | 2026-08-16T13:15:37.889Z | run_started |  | PREFLIGHT |  |
| 8360 | 2026-08-16T13:15:38.404Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 8361 | 2026-08-16T13:16:18.044Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 8362 | 2026-08-16T13:16:18.137Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 8363 | 2026-08-16T13:16:18.272Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 8364 | 2026-08-16T13:16:18.405Z | state_transition | READY | ROUTED | reason=route_selected |
| 8365 | 2026-08-16T13:16:18.817Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=3bad7c62cb26445cb5ae88b91aff8fbc |
| 8366 | 2026-08-16T13:16:18.916Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 8367 | 2026-08-16T13:16:19.422Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=3bad7c62cb26445cb5ae88b91aff8fbc |
| 8368 | 2026-08-16T13:16:19.548Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 8369 | 2026-08-16T13:16:19.972Z | proof_cache_miss |  |  | reason=cold; stage_id=check:0fd559d8beed514d; input_fingerprint=0f74f2e954e71c04280db102e71c5126cce161229450af32478dfd75778ab8e5 |
| 8370 | 2026-08-16T13:16:20.239Z | managed_process_admitted |  |  | owner=default |
| 8371 | 2026-08-16T13:16:20.505Z | managed_process_started |  |  | owner=default |
| 8372 | 2026-08-16T13:16:20.863Z | managed_process_terminal |  |  | owner=default |
| 8373 | 2026-08-16T13:16:21.096Z | proof_recorded |  |  | stage_id=check:0fd559d8beed514d; status=passed; cache_hit=False; input_fingerprint=0f74f2e954e71c04280db102e71c5126cce161229450af32478dfd75778ab8e5 |
| 8374 | 2026-08-16T13:16:21.250Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:eae0cb5e0af81aca; input_fingerprint=11bb955ba0dd07076f8ebcc806cd1e90dbd057059ffb6042362a3cab3c4cf8e8 |
| 8375 | 2026-08-16T13:16:21.505Z | managed_process_admitted |  |  | owner=default |
| 8376 | 2026-08-16T13:16:21.739Z | managed_process_started |  |  | owner=default |
| 8377 | 2026-08-16T13:16:29.801Z | managed_process_terminal |  |  | owner=default |
| 8378 | 2026-08-16T13:16:30.087Z | proof_recorded |  |  | stage_id=check:eae0cb5e0af81aca; status=passed; cache_hit=False; input_fingerprint=11bb955ba0dd07076f8ebcc806cd1e90dbd057059ffb6042362a3cab3c4cf8e8 |
| 8379 | 2026-08-16T13:16:30.296Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:95d712e4a0a41592; input_fingerprint=d93cab162ea64a382fec7d234bb8c3323b052bbeda057239e8281460c47dca4b |
| 8380 | 2026-08-16T13:16:30.592Z | managed_process_admitted |  |  | owner=default |
| 8381 | 2026-08-16T13:16:30.837Z | managed_process_started |  |  | owner=default |
| 8382 | 2026-08-16T13:16:45.863Z | managed_process_terminal |  |  | owner=default |
| 8383 | 2026-08-16T13:16:46.075Z | proof_recorded |  |  | stage_id=check:95d712e4a0a41592; status=passed; cache_hit=False; input_fingerprint=d93cab162ea64a382fec7d234bb8c3323b052bbeda057239e8281460c47dca4b |
| 8384 | 2026-08-16T13:16:46.505Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 8385 | 2026-08-16T13:16:55.377Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 8386 | 2026-08-16T13:16:55.620Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:0fd559d8beed514d | passed | 0f74f2e954e71c04280db102e71c5126cce161229450af32478dfd75778ab8e5 | False | 888 | 0 |
| check:eae0cb5e0af81aca | passed | 11bb955ba0dd07076f8ebcc806cd1e90dbd057059ffb6042362a3cab3c4cf8e8 | False | 8536 | 0 |
| check:95d712e4a0a41592 | passed | d93cab162ea64a382fec7d234bb8c3323b052bbeda057239e8281460c47dca4b | False | 15536 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| ec65e00944904845ab9a98d9339af834 | accepted | cf6cb6ddbf29d90515d003ce72490ffda985c37f | 7684760c1edea4ab90f4fb35aaadb1ccd5b05cea587e8ec200ee84a0ebdd7784 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `28`
- Chain head: `03e0dad361c6b89999fe1ca52435fb4e1799dadffb2084802eaddd62c6c2f653`
