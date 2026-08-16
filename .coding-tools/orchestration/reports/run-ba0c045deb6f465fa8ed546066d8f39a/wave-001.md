# Orchestration Wave 1

- Run: `ba0c045deb6f465fa8ed546066d8f39a`
- Wave: `9b5e4b1cd9de4bef902c3ca46ac705e5`
- Objective: Verify the current R2B server-first auto-dispatch implementation already present in the worktree after the formatting recovery. Do not modify source. Prove formatting for the four touched files, core placement policy behavior, production root compilation, and test-graph type correctness. Preserve all unrelated worktree changes. This verification corresponds to the implementation originally written under R2B run 8493048d89c048aeaa44f45be14fbc14; the temporary formatting recovery run changed only formatting of validation_handoff.rs.
- Mode: `mcp_only`
- Base HEAD: `cf6cb6ddbf29d90515d003ce72490ffda985c37f`
- Worktree fingerprint: `135da91912d727ef74b8564c3a5bf128a41af14d14c7b49d7658d2da8536b1ad`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 8304 | 2026-08-16T13:10:21.473Z | run_started |  | PREFLIGHT |  |
| 8305 | 2026-08-16T13:10:21.518Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 8306 | 2026-08-16T13:10:21.657Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 8307 | 2026-08-16T13:10:21.789Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 8308 | 2026-08-16T13:10:21.918Z | state_transition | READY | ROUTED | reason=route_selected |
| 8309 | 2026-08-16T13:10:22.375Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=7f694f4e25e54801a8bf5d9e2b71c58c |
| 8310 | 2026-08-16T13:10:22.519Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 8311 | 2026-08-16T13:10:23.260Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=7f694f4e25e54801a8bf5d9e2b71c58c |
| 8312 | 2026-08-16T13:10:23.308Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 8313 | 2026-08-16T13:10:23.550Z | proof_cache_miss |  |  | reason=cold; stage_id=check:04a4ddddbf955f2e; input_fingerprint=3bc2f9b2e58f15748fb6d4637602bf67ff040e74b901914d5b6e06457b37c3ec |
| 8314 | 2026-08-16T13:10:23.862Z | managed_process_admitted |  |  | owner=default |
| 8315 | 2026-08-16T13:10:24.088Z | managed_process_started |  |  | owner=default |
| 8316 | 2026-08-16T13:10:24.472Z | managed_process_terminal |  |  | owner=default |
| 8317 | 2026-08-16T13:10:24.731Z | proof_recorded |  |  | stage_id=check:04a4ddddbf955f2e; status=passed; cache_hit=False; input_fingerprint=3bc2f9b2e58f15748fb6d4637602bf67ff040e74b901914d5b6e06457b37c3ec |
| 8318 | 2026-08-16T13:10:24.860Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:67144c3fff08377b; input_fingerprint=b2b6b8edbdbb30d8f1e75ff1622ed026c7757fa543cb2871a6d674d87b692ff4 |
| 8319 | 2026-08-16T13:10:25.174Z | managed_process_admitted |  |  | owner=default |
| 8320 | 2026-08-16T13:10:25.460Z | managed_process_started |  |  | owner=default |
| 8321 | 2026-08-16T13:10:26.084Z | managed_process_terminal |  |  | owner=default |
| 8322 | 2026-08-16T13:10:26.488Z | proof_recorded |  |  | stage_id=check:67144c3fff08377b; status=passed; cache_hit=False; input_fingerprint=b2b6b8edbdbb30d8f1e75ff1622ed026c7757fa543cb2871a6d674d87b692ff4 |
| 8323 | 2026-08-16T13:10:26.531Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:eae0cb5e0af81aca; input_fingerprint=4572e616b25f98d6a87b30840463163a4415f03982155ee93a8d905758d3f98a |
| 8324 | 2026-08-16T13:10:26.804Z | managed_process_admitted |  |  | owner=default |
| 8325 | 2026-08-16T13:10:27.052Z | managed_process_started |  |  | owner=default |
| 8326 | 2026-08-16T13:11:27.221Z | managed_process_terminal |  |  | owner=default |
| 8327 | 2026-08-16T13:11:27.593Z | proof_recorded |  |  | stage_id=check:eae0cb5e0af81aca; status=passed; cache_hit=False; input_fingerprint=4572e616b25f98d6a87b30840463163a4415f03982155ee93a8d905758d3f98a |
| 8328 | 2026-08-16T13:11:27.728Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:95d712e4a0a41592; input_fingerprint=569e07226b5a609cf2f3bf6611e4b30bcc4d101eee4ab8571abf96c29ed09117 |
| 8329 | 2026-08-16T13:11:27.964Z | managed_process_admitted |  |  | owner=default |
| 8330 | 2026-08-16T13:11:28.188Z | managed_process_started |  |  | owner=default |
| 8331 | 2026-08-16T13:12:54.759Z | managed_process_terminal |  |  | owner=default |
| 8332 | 2026-08-16T13:12:55.018Z | proof_recorded |  |  | stage_id=check:95d712e4a0a41592; status=failed; cache_hit=False; input_fingerprint=569e07226b5a609cf2f3bf6611e4b30bcc4d101eee4ab8571abf96c29ed09117 |
| 8333 | 2026-08-16T13:12:55.158Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 8334 | 2026-08-16T13:12:55.285Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 8335 | 2026-08-16T13:12:55.403Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:04a4ddddbf955f2e | passed | 3bc2f9b2e58f15748fb6d4637602bf67ff040e74b901914d5b6e06457b37c3ec | False | 908 | 0 |
| check:67144c3fff08377b | passed | b2b6b8edbdbb30d8f1e75ff1622ed026c7757fa543cb2871a6d674d87b692ff4 | False | 1492 | 0 |
| check:eae0cb5e0af81aca | passed | 4572e616b25f98d6a87b30840463163a4415f03982155ee93a8d905758d3f98a | False | 60806 | 0 |
| check:95d712e4a0a41592 | failed | 569e07226b5a609cf2f3bf6611e4b30bcc4d101eee4ab8571abf96c29ed09117 | False | 87041 | 101 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `55`
- Chain head: `c5e566672ff720f89dc4fb30dc769cf3282600281374ba70549f87aa320c8f14`
