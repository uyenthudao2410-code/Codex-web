# Orchestration Wave 4

- Run: `f5e910d40935469aa9f468bcd760883d`
- Wave: `d871a92609e342b4b7c08ed46cc67fa2`
- Objective: Investigate Project Finance -> Project detail -> Overview in the HR app. Identify every overview KPI/card/table value that is currently hardcoded, mocked, placeholder, seeded only for UI, or falls back to fake numbers. Trace the real data contracts and calculation sources available in the current finance frontend/BFF/backend. Do not mutate files yet. Financial invariant: displayed monetary/percentage/status values must be derived from the selected project's real persisted/read-model data and must not fabricate a value when source data is missing; missing data should be represented truthfully. Return the smallest coherent implementation scope and authoritative focused verification commands.
- Mode: `mcp_only`
- Base HEAD: `788c0f33470611be3d50727a5b23c29ef2169070`
- Worktree fingerprint: `08d2a211d125629da5f463c3afe2487fade0034ebac81bedf444921c3d4b5d0a`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 19369 | 2026-08-19T04:41:32.845Z | wave_replanned |  | PREFLIGHT | reason=The previous prepare identified the relevant subsystems but directory paths could not be materialized; this continuation narrows to concrete source/test files so a complete safe patch can be built without touching unrelated dashboard changes. |
| 19370 | 2026-08-19T04:41:34.023Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 19371 | 2026-08-19T04:41:34.711Z | managed_process_admitted |  |  | owner=chatweb |
| 19372 | 2026-08-19T04:41:34.972Z | managed_process_started |  |  | owner=chatweb |
| 19373 | 2026-08-19T04:41:35.349Z | managed_process_terminal |  |  | owner=chatweb |
| 19374 | 2026-08-19T04:41:41.139Z | managed_process_admitted |  |  | owner=chatweb |
| 19375 | 2026-08-19T04:41:41.405Z | managed_process_started |  |  | owner=chatweb |
| 19376 | 2026-08-19T04:41:41.844Z | managed_process_terminal |  |  | owner=chatweb |
| 19377 | 2026-08-19T04:42:06.658Z | managed_process_admitted |  |  | owner=chatweb |
| 19378 | 2026-08-19T04:42:06.905Z | managed_process_started |  |  | owner=chatweb |
| 19379 | 2026-08-19T04:42:07.527Z | managed_process_terminal |  |  | owner=chatweb |
| 19380 | 2026-08-19T04:42:13.381Z | managed_process_admitted |  |  | owner=chatweb |
| 19381 | 2026-08-19T04:42:13.697Z | managed_process_started |  |  | owner=chatweb |
| 19382 | 2026-08-19T04:42:14.210Z | managed_process_terminal |  |  | owner=chatweb |
| 19383 | 2026-08-19T04:42:20.750Z | managed_process_admitted |  |  | owner=chatweb |
| 19384 | 2026-08-19T04:42:21.039Z | managed_process_started |  |  | owner=chatweb |
| 19385 | 2026-08-19T04:42:23.269Z | managed_process_terminal |  |  | owner=chatweb |
| 19386 | 2026-08-19T04:42:23.438Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 19387 | 2026-08-19T04:42:30.896Z | managed_process_admitted |  |  | owner=chatweb |
| 19388 | 2026-08-19T04:42:31.137Z | managed_process_started |  |  | owner=chatweb |
| 19389 | 2026-08-19T04:42:32.384Z | managed_process_terminal |  |  | owner=chatweb |
| 19390 | 2026-08-19T04:42:37.274Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 19391 | 2026-08-19T04:42:37.360Z | managed_process_admitted |  |  | owner=chatweb |
| 19392 | 2026-08-19T04:42:37.781Z | managed_process_started |  |  | owner=chatweb |
| 19393 | 2026-08-19T04:42:38.202Z | managed_process_terminal |  |  | owner=chatweb |
| 19394 | 2026-08-19T04:42:50.128Z | managed_process_admitted |  |  | owner=chatweb |
| 19395 | 2026-08-19T04:42:50.387Z | managed_process_started |  |  | owner=chatweb |
| 19396 | 2026-08-19T04:42:51.068Z | managed_process_terminal |  |  | owner=chatweb |
| 19397 | 2026-08-19T04:42:55.748Z | managed_process_admitted |  |  | owner=chatweb |
| 19398 | 2026-08-19T04:42:56.005Z | managed_process_started |  |  | owner=chatweb |
| 19399 | 2026-08-19T04:42:56.601Z | managed_process_terminal |  |  | owner=chatweb |
| 19400 | 2026-08-19T04:42:58.123Z | managed_process_admitted |  |  | owner=chatweb |
| 19401 | 2026-08-19T04:42:58.405Z | managed_process_started |  |  | owner=chatweb |
| 19402 | 2026-08-19T04:43:00.001Z | managed_process_terminal |  |  | owner=chatweb |
| 19403 | 2026-08-19T04:43:01.671Z | managed_process_admitted |  |  | owner=chatweb |
| 19404 | 2026-08-19T04:43:01.926Z | managed_process_started |  |  | owner=chatweb |
| 19405 | 2026-08-19T04:43:02.428Z | managed_process_terminal |  |  | owner=chatweb |
| 19406 | 2026-08-19T04:43:18.222Z | managed_process_admitted |  |  | owner=chatweb |
| 19407 | 2026-08-19T04:43:18.472Z | managed_process_started |  |  | owner=chatweb |
| 19408 | 2026-08-19T04:43:19.650Z | managed_process_terminal |  |  | owner=chatweb |
| 19409 | 2026-08-19T04:43:24.339Z | managed_process_admitted |  |  | owner=chatweb |
| 19410 | 2026-08-19T04:43:24.572Z | managed_process_started |  |  | owner=chatweb |
| 19411 | 2026-08-19T04:43:24.987Z | managed_process_terminal |  |  | owner=chatweb |
| 19412 | 2026-08-19T04:43:25.330Z | managed_process_admitted |  |  | owner=chatweb |
| 19413 | 2026-08-19T04:43:25.563Z | managed_process_started |  |  | owner=chatweb |
| 19414 | 2026-08-19T04:43:26.948Z | managed_process_terminal |  |  | owner=chatweb |
| 19415 | 2026-08-19T04:43:29.895Z | managed_process_admitted |  |  | owner=chatweb |
| 19416 | 2026-08-19T04:43:30.137Z | managed_process_started |  |  | owner=chatweb |
| 19417 | 2026-08-19T04:43:31.302Z | managed_process_terminal |  |  | owner=chatweb |
| 19418 | 2026-08-19T04:43:34.013Z | managed_process_admitted |  |  | owner=chatweb |
| 19419 | 2026-08-19T04:43:34.297Z | managed_process_started |  |  | owner=chatweb |
| 19420 | 2026-08-19T04:43:35.419Z | managed_process_terminal |  |  | owner=chatweb |
| 19421 | 2026-08-19T04:43:36.837Z | managed_process_admitted |  |  | owner=chatweb |
| 19422 | 2026-08-19T04:43:37.087Z | managed_process_started |  |  | owner=chatweb |
| 19423 | 2026-08-19T04:43:37.442Z | managed_process_terminal |  |  | owner=chatweb |
| 19424 | 2026-08-19T04:43:43.665Z | managed_process_admitted |  |  | owner=chatweb |
| 19425 | 2026-08-19T04:43:43.989Z | managed_process_started |  |  | owner=chatweb |
| 19426 | 2026-08-19T04:43:44.380Z | managed_process_terminal |  |  | owner=chatweb |
| 19427 | 2026-08-19T04:43:49.960Z | managed_process_admitted |  |  | owner=chatweb |
| 19428 | 2026-08-19T04:43:50.196Z | managed_process_started |  |  | owner=chatweb |
| 19429 | 2026-08-19T04:43:50.576Z | managed_process_terminal |  |  | owner=chatweb |
| 19430 | 2026-08-19T04:44:03.331Z | managed_process_admitted |  |  | owner=chatweb |
| 19431 | 2026-08-19T04:44:03.568Z | managed_process_started |  |  | owner=chatweb |
| 19432 | 2026-08-19T04:44:04.726Z | managed_process_terminal |  |  | owner=chatweb |
| 19433 | 2026-08-19T04:44:07.601Z | managed_process_admitted |  |  | owner=chatweb |
| 19434 | 2026-08-19T04:44:07.855Z | managed_process_started |  |  | owner=chatweb |
| 19435 | 2026-08-19T04:44:09.218Z | managed_process_terminal |  |  | owner=chatweb |
| 19436 | 2026-08-19T04:44:10.890Z | managed_process_admitted |  |  | owner=chatweb |
| 19437 | 2026-08-19T04:44:11.153Z | managed_process_started |  |  | owner=chatweb |
| 19438 | 2026-08-19T04:44:11.657Z | managed_process_terminal |  |  | owner=chatweb |
| 19439 | 2026-08-19T04:44:17.481Z | managed_process_admitted |  |  | owner=chatweb |
| 19440 | 2026-08-19T04:44:17.743Z | managed_process_started |  |  | owner=chatweb |
| 19441 | 2026-08-19T04:44:18.185Z | managed_process_terminal |  |  | owner=chatweb |
| 19442 | 2026-08-19T04:44:21.539Z | managed_process_admitted |  |  | owner=chatweb |
| 19443 | 2026-08-19T04:44:21.781Z | managed_process_started |  |  | owner=chatweb |
| 19444 | 2026-08-19T04:44:22.219Z | managed_process_terminal |  |  | owner=chatweb |
| 19445 | 2026-08-19T04:44:29.489Z | managed_process_admitted |  |  | owner=chatweb |
| 19446 | 2026-08-19T04:44:29.781Z | managed_process_started |  |  | owner=chatweb |
| 19447 | 2026-08-19T04:44:30.937Z | managed_process_terminal |  |  | owner=chatweb |
| 19448 | 2026-08-19T04:44:36.315Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 19449 | 2026-08-19T04:44:36.444Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 19450 | 2026-08-19T04:44:36.619Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 19451 | 2026-08-19T04:44:36.778Z | state_transition | READY | ROUTED | reason=route_selected |
| 19452 | 2026-08-19T04:44:37.249Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=7e11c23b594d40fc909be9d425eafe31 |
| 19453 | 2026-08-19T04:44:37.377Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 19454 | 2026-08-19T04:44:37.800Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=7e11c23b594d40fc909be9d425eafe31 |
| 19455 | 2026-08-19T04:44:37.953Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 19456 | 2026-08-19T04:44:38.261Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=03b5faf4904adf9061e6ab36b638407e12ba9becde949cd58309cc36a00fe28a |
| 19457 | 2026-08-19T04:44:38.559Z | managed_process_admitted |  |  | owner=default |
| 19458 | 2026-08-19T04:44:38.805Z | managed_process_started |  |  | owner=default |
| 19459 | 2026-08-19T04:44:39.255Z | managed_process_terminal |  |  | owner=default |
| 19460 | 2026-08-19T04:44:39.618Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=03b5faf4904adf9061e6ab36b638407e12ba9becde949cd58309cc36a00fe28a |
| 19461 | 2026-08-19T04:44:40.163Z | managed_process_admitted |  |  | owner=chatweb |
| 19462 | 2026-08-19T04:44:40.388Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 19463 | 2026-08-19T04:44:40.422Z | managed_process_started |  |  | owner=chatweb |
| 19464 | 2026-08-19T04:44:41.165Z | managed_process_terminal |  |  | owner=chatweb |
| 19465 | 2026-08-19T04:44:45.945Z | managed_process_admitted |  |  | owner=chatweb |
| 19466 | 2026-08-19T04:44:46.263Z | managed_process_started |  |  | owner=chatweb |
| 19467 | 2026-08-19T04:44:46.694Z | managed_process_terminal |  |  | owner=chatweb |
| 19468 | 2026-08-19T04:44:51.670Z | managed_process_admitted |  |  | owner=chatweb |
| 19469 | 2026-08-19T04:44:51.935Z | managed_process_started |  |  | owner=chatweb |
| 19470 | 2026-08-19T04:44:53.411Z | managed_process_terminal |  |  | owner=chatweb |
| 19471 | 2026-08-19T04:44:58.338Z | managed_process_admitted |  |  | owner=chatweb |
| 19472 | 2026-08-19T04:44:58.555Z | managed_process_started |  |  | owner=chatweb |
| 19473 | 2026-08-19T04:44:59.950Z | managed_process_terminal |  |  | owner=chatweb |
| 19474 | 2026-08-19T04:45:12.944Z | managed_process_admitted |  |  | owner=chatweb |
| 19475 | 2026-08-19T04:45:13.213Z | managed_process_started |  |  | owner=chatweb |
| 19476 | 2026-08-19T04:45:14.414Z | managed_process_terminal |  |  | owner=chatweb |
| 19477 | 2026-08-19T04:45:23.905Z | managed_process_admitted |  |  | owner=chatweb |
| 19478 | 2026-08-19T04:45:24.150Z | managed_process_started |  |  | owner=chatweb |
| 19479 | 2026-08-19T04:45:25.302Z | managed_process_terminal |  |  | owner=chatweb |
| 19480 | 2026-08-19T04:45:47.738Z | managed_process_admitted |  |  | owner=chatweb |
| 19481 | 2026-08-19T04:45:48.438Z | managed_process_started |  |  | owner=chatweb |
| 19482 | 2026-08-19T04:45:49.467Z | managed_process_terminal |  |  | owner=chatweb |
| 19483 | 2026-08-19T04:45:50.038Z | managed_process_admitted |  |  | owner=chatweb |
| 19484 | 2026-08-19T04:45:50.324Z | managed_process_started |  |  | owner=chatweb |
| 19485 | 2026-08-19T04:45:50.658Z | managed_process_terminal |  |  | owner=chatweb |
| 19486 | 2026-08-19T04:45:54.853Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 19487 | 2026-08-19T04:45:55.144Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 03b5faf4904adf9061e6ab36b638407e12ba9becde949cd58309cc36a00fe28a | False | 1015 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| f67dbf0c9b434b75a349e4d8cf9e5a54 | accepted | 788c0f33470611be3d50727a5b23c29ef2169070 | 0ff3c8defc6187c288a2fa80ae5096248961cbe4d9632f3c4ec176fc7d30eaca | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `197`
- Chain head: `b7269eb4089c09255400b81b4981a53bcbe1a4a2fccfe75cabcc724afe37087e`
