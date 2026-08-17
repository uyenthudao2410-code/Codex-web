# Orchestration Wave 1

- Run: `967bb4c9007f4f8aac4f14eaf16ed521`
- Wave: `3d1671ab31ed4924baf2f53d52cea8e6`
- Objective: P1.1 only: identify the existing authoritative evaluator/report path that can generate a fresh canonical current-ledger baseline from .coding-tools/orchestration/ledger.sqlite3 without inventing a second analytics pipeline. The baseline must cover total runs; accepted/rejected/aborted/current states; first-pass vs repaired; TTAR p50/p90 where methodologically supported; replan counts; failure/error classes; route counts; pair counts; quality-outcome coverage; controller timing/usage/cost coverage; and host-bound span coverage or an explicit unavailable/not-yet-computed state if the current evaluator cannot derive it. Determine exact commands/files to use, source/runtime/fingerprint provenance to record, and whether any small evaluator/reporting gap must be fixed before generating the report. Do not mutate files in prepare. Preserve P0.2/P0.3 closure and do not publish/release.
- Mode: `mcp_only`
- Base HEAD: `db4e295cdd2cf71c0a4d0b91f1e5dcb5f9e6e4dc`
- Worktree fingerprint: `e80104e3654ef4a0e0c8b1bf251d73ba88af143af2b632667a3f870c9c6d6181`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 14310 | 2026-08-17T14:51:35.649Z | run_started |  | PREFLIGHT |  |
| 14311 | 2026-08-17T14:51:40.668Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 14312 | 2026-08-17T14:53:03.917Z | managed_process_admitted |  |  | owner=default |
| 14313 | 2026-08-17T14:53:04.123Z | managed_process_started |  |  | owner=default |
| 14314 | 2026-08-17T14:53:04.473Z | managed_process_terminal |  |  | owner=default |
| 14315 | 2026-08-17T14:53:34.091Z | managed_process_admitted |  |  | owner=default |
| 14316 | 2026-08-17T14:53:34.316Z | managed_process_started |  |  | owner=default |
| 14317 | 2026-08-17T14:53:34.656Z | managed_process_terminal |  |  | owner=default |
| 14318 | 2026-08-17T14:53:57.973Z | managed_process_admitted |  |  | owner=default |
| 14319 | 2026-08-17T14:53:58.189Z | managed_process_started |  |  | owner=default |
| 14320 | 2026-08-17T14:54:16.589Z | managed_process_terminal |  |  | owner=default |
| 14321 | 2026-08-17T14:54:27.156Z | managed_process_admitted |  |  | owner=default |
| 14322 | 2026-08-17T14:54:27.338Z | managed_process_started |  |  | owner=default |
| 14323 | 2026-08-17T14:54:27.731Z | managed_process_terminal |  |  | owner=default |
| 14324 | 2026-08-17T14:54:36.872Z | managed_process_admitted |  |  | owner=default |
| 14325 | 2026-08-17T14:54:37.072Z | managed_process_started |  |  | owner=default |
| 14326 | 2026-08-17T14:54:37.456Z | managed_process_terminal |  |  | owner=default |
| 14327 | 2026-08-17T14:55:38.780Z | managed_process_admitted |  |  | owner=default |
| 14328 | 2026-08-17T14:55:39.056Z | managed_process_started |  |  | owner=default |
| 14329 | 2026-08-17T14:55:39.546Z | managed_process_terminal |  |  | owner=default |
| 14330 | 2026-08-17T14:57:52.294Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 14331 | 2026-08-17T14:57:52.470Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 14332 | 2026-08-17T14:57:52.609Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 14333 | 2026-08-17T14:57:52.753Z | state_transition | READY | ROUTED | reason=route_selected |
| 14334 | 2026-08-17T14:57:53.660Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=3b2d2cee03aa4920b8080bbfb998ce21 |
| 14335 | 2026-08-17T14:57:53.769Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 14336 | 2026-08-17T14:57:54.771Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=3b2d2cee03aa4920b8080bbfb998ce21 |
| 14337 | 2026-08-17T14:57:55.019Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 14338 | 2026-08-17T14:57:55.505Z | proof_cache_miss |  |  | reason=cold; stage_id=check:f35f8e2de717f34a; input_fingerprint=e15ff8b539ceecbe6cc4059dc3003e4d498b9b8e38ec5260958660842708418a |
| 14339 | 2026-08-17T14:57:55.855Z | managed_process_admitted |  |  | owner=default |
| 14340 | 2026-08-17T14:57:56.162Z | managed_process_started |  |  | owner=default |
| 14341 | 2026-08-17T14:57:57.987Z | managed_process_terminal |  |  | owner=default |
| 14342 | 2026-08-17T14:57:58.271Z | proof_recorded |  |  | stage_id=check:f35f8e2de717f34a; status=passed; cache_hit=False; input_fingerprint=e15ff8b539ceecbe6cc4059dc3003e4d498b9b8e38ec5260958660842708418a |
| 14343 | 2026-08-17T14:57:59.188Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 14344 | 2026-08-17T14:58:21.685Z | managed_process_admitted |  |  | owner=default |
| 14345 | 2026-08-17T14:58:22.169Z | managed_process_started |  |  | owner=default |
| 14346 | 2026-08-17T14:58:22.942Z | managed_process_terminal |  |  | owner=default |
| 14347 | 2026-08-17T14:58:49.638Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 14348 | 2026-08-17T14:58:50.105Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:f35f8e2de717f34a | passed | e15ff8b539ceecbe6cc4059dc3003e4d498b9b8e38ec5260958660842708418a | False | 2411 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 41cc3b9c15344ea3afaf328ba7b1b08f | accepted | db4e295cdd2cf71c0a4d0b91f1e5dcb5f9e6e4dc | 8e6fc113b8a3dcfa05592f1afd3c7ecfc7e01613d6347dd9940b3c7d655ea9ce | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `39`
- Chain head: `d179477d2d9974ba587c43a700e2aad53b5c56c5c6f6907ed24f3903da908886`
