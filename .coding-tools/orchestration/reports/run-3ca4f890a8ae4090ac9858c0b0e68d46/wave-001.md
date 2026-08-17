# Orchestration Wave 1

- Run: `3ca4f890a8ae4090ac9858c0b0e68d46`
- Wave: `16b3281053d24c32941153b9ab1fc428`
- Objective: Build the fresh NSIS installer for P0.2 installed Windows acceptance from exact delivered HEAD d5d4bbb5 using the hardened exact-source packaging pipeline. Run `npm run dist` as the release build, require artifact collection to find the generated installer, and preserve the package/test output as proof. Do not install or mutate external system state in this wave.
- Mode: `mcp_only`
- Base HEAD: `d5d4bbb533b21937041c1b48a2005583f2652383`
- Worktree fingerprint: `54633b48e57c8037b95e1addde38631556ce9966bdb31d135f006dd74f2b82fc`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 12437 | 2026-08-17T08:04:01.574Z | run_started |  | PREFLIGHT |  |
| 12438 | 2026-08-17T08:04:01.998Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 12439 | 2026-08-17T08:04:02.358Z | managed_process_admitted |  |  | owner=default |
| 12440 | 2026-08-17T08:04:02.654Z | managed_process_started |  |  | owner=default |
| 12441 | 2026-08-17T08:05:07.579Z | managed_process_admitted |  |  | owner=default |
| 12442 | 2026-08-17T08:05:07.877Z | managed_process_started |  |  | owner=default |
| 12443 | 2026-08-17T08:05:08.644Z | managed_process_terminal |  |  | owner=default |
| 12444 | 2026-08-17T08:05:15.253Z | managed_process_terminal |  |  | owner=default |
| 12445 | 2026-08-17T08:05:15.621Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 12446 | 2026-08-17T08:05:15.998Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 12447 | 2026-08-17T08:05:16.559Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 12448 | 2026-08-17T08:05:16.754Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 12449 | 2026-08-17T08:05:16.931Z | state_transition | READY | ROUTED | reason=route_selected |
| 12450 | 2026-08-17T08:05:17.486Z | managed_process_admitted |  |  | owner=default |
| 12451 | 2026-08-17T08:05:17.597Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=46bff36b0b0847f99c51a90ba603006d |
| 12452 | 2026-08-17T08:05:17.994Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 12453 | 2026-08-17T08:05:18.133Z | managed_process_started |  |  | owner=default |
| 12454 | 2026-08-17T08:05:18.605Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=46bff36b0b0847f99c51a90ba603006d |
| 12455 | 2026-08-17T08:05:18.770Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 12456 | 2026-08-17T08:05:18.978Z | managed_process_terminal |  |  | owner=default |
| 12457 | 2026-08-17T08:05:19.325Z | proof_cache_miss |  |  | reason=cold; stage_id=verify:build; input_fingerprint=5774e3d3e9c310d6cc0be96b21eee63c2dd7579a9f3dbe953b7993041ab8da13 |
| 12458 | 2026-08-17T08:05:19.736Z | managed_process_admitted |  |  | owner=default |
| 12459 | 2026-08-17T08:05:20.077Z | managed_process_started |  |  | owner=default |
| 12460 | 2026-08-17T08:05:27.150Z | managed_process_admitted |  |  | owner=default |
| 12461 | 2026-08-17T08:05:27.470Z | managed_process_started |  |  | owner=default |
| 12462 | 2026-08-17T08:05:28.120Z | managed_process_terminal |  |  | owner=default |
| 12463 | 2026-08-17T08:05:33.561Z | managed_process_admitted |  |  | owner=default |
| 12464 | 2026-08-17T08:05:33.953Z | managed_process_started |  |  | owner=default |
| 12465 | 2026-08-17T08:05:34.494Z | managed_process_terminal |  |  | owner=default |
| 12466 | 2026-08-17T08:05:44.335Z | managed_process_admitted |  |  | owner=default |
| 12467 | 2026-08-17T08:05:44.735Z | managed_process_started |  |  | owner=default |
| 12468 | 2026-08-17T08:05:45.253Z | managed_process_terminal |  |  | owner=default |
| 12469 | 2026-08-17T08:05:51.298Z | managed_process_admitted |  |  | owner=default |
| 12470 | 2026-08-17T08:05:51.542Z | managed_process_started |  |  | owner=default |
| 12471 | 2026-08-17T08:05:52.423Z | managed_process_terminal |  |  | owner=default |
| 12472 | 2026-08-17T08:06:16.545Z | managed_process_admitted |  |  | owner=default |
| 12473 | 2026-08-17T08:06:17.070Z | managed_process_started |  |  | owner=default |
| 12474 | 2026-08-17T08:06:18.205Z | managed_process_terminal |  |  | owner=default |
| 12475 | 2026-08-17T08:06:31.155Z | managed_process_admitted |  |  | owner=default |
| 12476 | 2026-08-17T08:06:31.527Z | managed_process_started |  |  | owner=default |
| 12477 | 2026-08-17T08:06:32.052Z | managed_process_terminal |  |  | owner=default |
| 12478 | 2026-08-17T08:06:32.736Z | managed_process_terminal |  |  | owner=default |
| 12479 | 2026-08-17T08:06:34.160Z | proof_recorded |  |  | stage_id=verify:build; status=passed; cache_hit=False; input_fingerprint=5774e3d3e9c310d6cc0be96b21eee63c2dd7579a9f3dbe953b7993041ab8da13 |
| 12480 | 2026-08-17T08:06:34.447Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 12481 | 2026-08-17T08:06:39.275Z | managed_process_admitted |  |  | owner=default |
| 12482 | 2026-08-17T08:06:39.610Z | managed_process_started |  |  | owner=default |
| 12483 | 2026-08-17T08:06:40.132Z | managed_process_terminal |  |  | owner=default |
| 12484 | 2026-08-17T08:08:08.766Z | managed_process_admitted |  |  | owner=chatweb |
| 12485 | 2026-08-17T08:08:09.079Z | managed_process_started |  |  | owner=chatweb |
| 12486 | 2026-08-17T08:08:09.967Z | managed_process_terminal |  |  | owner=chatweb |
| 12487 | 2026-08-17T08:08:20.217Z | managed_process_admitted |  |  | owner=chatweb |
| 12488 | 2026-08-17T08:08:20.566Z | managed_process_started |  |  | owner=chatweb |
| 12489 | 2026-08-17T08:08:21.105Z | managed_process_terminal |  |  | owner=chatweb |
| 12490 | 2026-08-17T08:14:27.019Z | managed_process_admitted |  |  | owner=default |
| 12491 | 2026-08-17T08:14:27.285Z | managed_process_started |  |  | owner=default |
| 12492 | 2026-08-17T08:14:27.828Z | managed_process_terminal |  |  | owner=default |
| 12493 | 2026-08-17T08:14:39.091Z | managed_process_admitted |  |  | owner=default |
| 12494 | 2026-08-17T08:14:39.360Z | managed_process_started |  |  | owner=default |
| 12495 | 2026-08-17T08:14:39.937Z | managed_process_terminal |  |  | owner=default |
| 12496 | 2026-08-17T08:15:26.010Z | managed_process_admitted |  |  | owner=default |
| 12497 | 2026-08-17T08:15:26.363Z | managed_process_started |  |  | owner=default |
| 12498 | 2026-08-17T08:15:26.860Z | managed_process_terminal |  |  | owner=default |
| 12499 | 2026-08-17T08:15:36.686Z | managed_process_admitted |  |  | owner=default |
| 12500 | 2026-08-17T08:15:37.169Z | managed_process_started |  |  | owner=default |
| 12501 | 2026-08-17T08:15:37.885Z | managed_process_terminal |  |  | owner=default |
| 12502 | 2026-08-17T08:15:52.264Z | managed_process_admitted |  |  | owner=default |
| 12503 | 2026-08-17T08:15:52.674Z | managed_process_started |  |  | owner=default |
| 12504 | 2026-08-17T08:16:01.743Z | managed_process_terminal |  |  | owner=default |
| 12505 | 2026-08-17T08:16:18.531Z | managed_process_admitted |  |  | owner=default |
| 12506 | 2026-08-17T08:16:18.855Z | managed_process_started |  |  | owner=default |
| 12507 | 2026-08-17T08:16:19.633Z | managed_process_terminal |  |  | owner=default |
| 12508 | 2026-08-17T08:16:29.005Z | managed_process_admitted |  |  | owner=default |
| 12509 | 2026-08-17T08:16:29.373Z | managed_process_started |  |  | owner=default |
| 12510 | 2026-08-17T08:16:29.973Z | managed_process_terminal |  |  | owner=default |
| 12511 | 2026-08-17T08:17:53.945Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 12512 | 2026-08-17T08:17:54.414Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:build | passed | 5774e3d3e9c310d6cc0be96b21eee63c2dd7579a9f3dbe953b7993041ab8da13 | False | 74375 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 1e0dbba2cac04386a9497ee6abf592ba | accepted | d5d4bbb533b21937041c1b48a2005583f2652383 | 5978104dffbe4cdc2cff248bd9efaec8be2b0e03876537ff2160acd9c3157b06 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `76`
- Chain head: `68a9d972160377e2fabbe902db108fb8858a3d9d2b12c0e87c13f76b5d1b289c`
