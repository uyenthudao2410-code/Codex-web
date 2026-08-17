# Orchestration Wave 1

- Run: `d8231d2e1d384197912fe48d8eb97906`
- Wave: `38c2df6ff6ff42348006c2133b32b666`
- Objective: Implement Phase P2 from docs/research/260817_PROJECT_REAL_STATE_SCIENTIFIC_EVIDENCE_AND_FULL_EXECUTION_PLAN.md, starting with P2.1 Stratified Rework Diagnosis, then P2.2 Root-Cause Categories and P2.3 Countermeasure Evaluation only after each prior acceptance criterion is satisfied. Preserve the completed P1 measurement contracts. Use the canonical orchestration ledger as causal source. Do not manufacture causal conclusions from non-comparable history. Build a stratified report by workflow/task class with n, first-pass rate, repair rate, replan count, TTAR p50/p90, failure class, scope size and oracle strength where observable; preserve missing values as unknown. Then classify repair causes using evidence-backed categories and evaluate existing interventions using before/after or baseline/intervention/fresh-rerun evidence only when comparable. Update the current baseline and master research plan only after proof. Do not start P3. Do not modify or omit .coding-tools retention policy. The prior commit/push remains blocked by live SQLite sidecar locks; treat that as delivery debt, not permission to ignore .coding-tools.
- Mode: `mcp_only`
- Base HEAD: `b9b7ee1223351c2f7b2b6da7914c0de10e85de9c`
- Worktree fingerprint: `5aa31a5bdab9264b1b216cea3643d1f5ba0f307e9003a0d9b249c5020bff7743`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 15395 | 2026-08-17T18:32:42.663Z | run_started |  | PREFLIGHT |  |
| 15396 | 2026-08-17T18:32:56.298Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 15397 | 2026-08-17T18:33:18.152Z | managed_process_admitted |  |  | owner=default |
| 15398 | 2026-08-17T18:33:18.425Z | managed_process_started |  |  | owner=default |
| 15399 | 2026-08-17T18:33:18.896Z | managed_process_terminal |  |  | owner=default |
| 15400 | 2026-08-17T18:33:37.168Z | managed_process_admitted |  |  | owner=default |
| 15401 | 2026-08-17T18:33:37.409Z | managed_process_started |  |  | owner=default |
| 15402 | 2026-08-17T18:33:37.801Z | managed_process_terminal |  |  | owner=default |
| 15403 | 2026-08-17T18:33:56.342Z | managed_process_admitted |  |  | owner=default |
| 15404 | 2026-08-17T18:33:56.645Z | managed_process_started |  |  | owner=default |
| 15405 | 2026-08-17T18:33:57.050Z | managed_process_terminal |  |  | owner=default |
| 15406 | 2026-08-17T18:35:10.432Z | managed_process_admitted |  |  | owner=default |
| 15407 | 2026-08-17T18:35:10.668Z | managed_process_started |  |  | owner=default |
| 15408 | 2026-08-17T18:35:11.098Z | managed_process_terminal |  |  | owner=default |
| 15409 | 2026-08-17T18:35:26.859Z | managed_process_admitted |  |  | owner=default |
| 15410 | 2026-08-17T18:35:27.315Z | managed_process_started |  |  | owner=default |
| 15411 | 2026-08-17T18:35:27.998Z | managed_process_terminal |  |  | owner=default |
| 15412 | 2026-08-17T18:36:10.197Z | managed_process_admitted |  |  | owner=default |
| 15413 | 2026-08-17T18:36:10.414Z | managed_process_started |  |  | owner=default |
| 15414 | 2026-08-17T18:36:10.805Z | managed_process_terminal |  |  | owner=default |
| 15415 | 2026-08-17T18:38:29.828Z | managed_process_admitted |  |  | owner=default |
| 15416 | 2026-08-17T18:38:30.052Z | managed_process_started |  |  | owner=default |
| 15417 | 2026-08-17T18:38:30.588Z | managed_process_terminal |  |  | owner=default |
| 15418 | 2026-08-17T18:38:52.777Z | managed_process_admitted |  |  | owner=default |
| 15419 | 2026-08-17T18:38:52.998Z | managed_process_started |  |  | owner=default |
| 15420 | 2026-08-17T18:38:53.502Z | managed_process_terminal |  |  | owner=default |
| 15421 | 2026-08-17T18:39:41.168Z | managed_process_admitted |  |  | owner=default |
| 15422 | 2026-08-17T18:39:41.393Z | managed_process_started |  |  | owner=default |
| 15423 | 2026-08-17T18:39:41.801Z | managed_process_terminal |  |  | owner=default |
| 15424 | 2026-08-17T18:39:57.665Z | managed_process_admitted |  |  | owner=default |
| 15425 | 2026-08-17T18:39:57.909Z | managed_process_started |  |  | owner=default |
| 15426 | 2026-08-17T18:39:58.292Z | managed_process_terminal |  |  | owner=default |
| 15427 | 2026-08-17T18:40:21.765Z | managed_process_admitted |  |  | owner=default |
| 15428 | 2026-08-17T18:40:22.021Z | managed_process_started |  |  | owner=default |
| 15429 | 2026-08-17T18:40:22.410Z | managed_process_terminal |  |  | owner=default |
| 15430 | 2026-08-17T18:41:45.653Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 15431 | 2026-08-17T18:41:45.785Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 15432 | 2026-08-17T18:41:45.909Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 15433 | 2026-08-17T18:41:46.044Z | state_transition | READY | ROUTED | reason=route_selected |
| 15434 | 2026-08-17T18:41:46.425Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=bf23f63fa060448f8df3ff87bd49f52b |
| 15435 | 2026-08-17T18:41:46.602Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 15436 | 2026-08-17T18:41:47.208Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=bf23f63fa060448f8df3ff87bd49f52b |
| 15437 | 2026-08-17T18:41:47.335Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 15438 | 2026-08-17T18:41:47.669Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:80a1a46bd01d26a3; input_fingerprint=fc917f7c3a9324a429fd8e92fea86e448ed7f94f6f3d15b6923768b8cd126c3f |
| 15439 | 2026-08-17T18:41:47.984Z | managed_process_admitted |  |  | owner=default |
| 15440 | 2026-08-17T18:41:48.252Z | managed_process_started |  |  | owner=default |
| 15441 | 2026-08-17T18:41:48.647Z | managed_process_terminal |  |  | owner=default |
| 15442 | 2026-08-17T18:41:48.867Z | proof_recorded |  |  | stage_id=check:80a1a46bd01d26a3; status=passed; cache_hit=False; input_fingerprint=fc917f7c3a9324a429fd8e92fea86e448ed7f94f6f3d15b6923768b8cd126c3f |
| 15443 | 2026-08-17T18:41:49.007Z | proof_cache_miss |  |  | reason=cold; stage_id=check:1b64865d29e7bce2; input_fingerprint=efdc512e44909a823b5eff728fd3f45b0facab7258a79a0df8b3ed533b33ee18 |
| 15444 | 2026-08-17T18:41:49.283Z | managed_process_admitted |  |  | owner=default |
| 15445 | 2026-08-17T18:41:49.550Z | managed_process_started |  |  | owner=default |
| 15446 | 2026-08-17T18:41:49.942Z | managed_process_terminal |  |  | owner=default |
| 15447 | 2026-08-17T18:41:50.225Z | proof_recorded |  |  | stage_id=check:1b64865d29e7bce2; status=passed; cache_hit=False; input_fingerprint=efdc512e44909a823b5eff728fd3f45b0facab7258a79a0df8b3ed533b33ee18 |
| 15448 | 2026-08-17T18:41:50.367Z | proof_cache_miss |  |  | reason=cold; stage_id=check:6fd3842495485b3b; input_fingerprint=1376d790023dcb4bc62256ade0e28294d061dbc2fe20bfd71c729db2ec114901 |
| 15449 | 2026-08-17T18:41:50.708Z | managed_process_admitted |  |  | owner=default |
| 15450 | 2026-08-17T18:41:50.988Z | managed_process_started |  |  | owner=default |
| 15451 | 2026-08-17T18:41:51.375Z | managed_process_terminal |  |  | owner=default |
| 15452 | 2026-08-17T18:41:51.658Z | proof_recorded |  |  | stage_id=check:6fd3842495485b3b; status=passed; cache_hit=False; input_fingerprint=1376d790023dcb4bc62256ade0e28294d061dbc2fe20bfd71c729db2ec114901 |
| 15453 | 2026-08-17T18:41:51.790Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=9a022851c23ca8c73ef58b1f2f13658c7824e8ef67f2f70d1ac6d98d798f6cf3 |
| 15454 | 2026-08-17T18:41:52.058Z | managed_process_admitted |  |  | owner=default |
| 15455 | 2026-08-17T18:41:52.305Z | managed_process_started |  |  | owner=default |
| 15456 | 2026-08-17T18:41:55.367Z | managed_process_terminal |  |  | owner=default |
| 15457 | 2026-08-17T18:42:04.710Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=9a022851c23ca8c73ef58b1f2f13658c7824e8ef67f2f70d1ac6d98d798f6cf3 |
| 15458 | 2026-08-17T18:42:05.198Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 15459 | 2026-08-17T18:44:11.330Z | managed_process_admitted |  |  | owner=default |
| 15460 | 2026-08-17T18:44:11.594Z | managed_process_started |  |  | owner=default |
| 15461 | 2026-08-17T18:44:12.066Z | managed_process_terminal |  |  | owner=default |
| 15462 | 2026-08-17T18:44:28.414Z | managed_process_admitted |  |  | owner=default |
| 15463 | 2026-08-17T18:44:28.697Z | managed_process_started |  |  | owner=default |
| 15464 | 2026-08-17T18:44:30.039Z | managed_process_terminal |  |  | owner=default |
| 15465 | 2026-08-17T18:44:46.546Z | managed_process_admitted |  |  | owner=default |
| 15466 | 2026-08-17T18:44:46.813Z | managed_process_started |  |  | owner=default |
| 15467 | 2026-08-17T18:44:47.246Z | managed_process_terminal |  |  | owner=default |
| 15468 | 2026-08-17T18:45:04.184Z | managed_process_admitted |  |  | owner=default |
| 15469 | 2026-08-17T18:45:04.412Z | managed_process_started |  |  | owner=default |
| 15470 | 2026-08-17T18:45:04.831Z | managed_process_terminal |  |  | owner=default |
| 15471 | 2026-08-17T18:45:19.628Z | managed_process_admitted |  |  | owner=default |
| 15472 | 2026-08-17T18:45:19.887Z | managed_process_started |  |  | owner=default |
| 15473 | 2026-08-17T18:45:20.278Z | managed_process_terminal |  |  | owner=default |
| 15474 | 2026-08-17T18:49:18.771Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 15475 | 2026-08-17T18:49:19.490Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:80a1a46bd01d26a3 | passed | fc917f7c3a9324a429fd8e92fea86e448ed7f94f6f3d15b6923768b8cd126c3f | False | 942 | 0 |
| check:1b64865d29e7bce2 | passed | efdc512e44909a823b5eff728fd3f45b0facab7258a79a0df8b3ed533b33ee18 | False | 950 | 0 |
| check:6fd3842495485b3b | passed | 1376d790023dcb4bc62256ade0e28294d061dbc2fe20bfd71c729db2ec114901 | False | 1031 | 0 |
| verify:tests | passed | 9a022851c23ca8c73ef58b1f2f13658c7824e8ef67f2f70d1ac6d98d798f6cf3 | False | 12578 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 5a3d783d77244187bc8c8da5396d5885 | accepted | b9b7ee1223351c2f7b2b6da7914c0de10e85de9c | eac0f7f511249d97627ac0c07d8de41a9f61cf8177c4de607cde7459873720f1 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `81`
- Chain head: `2efb0871553c7d643d14af66f38c203ad4010afb48550a63c1332555142eb796`
