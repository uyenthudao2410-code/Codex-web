# Orchestration Wave 1

- Run: `36767d6bd73d41c380ebd3236aa1117c`
- Wave: `89a5fbd963c348eea408032822300d0a`
- Objective: Prepare a versioned Recovery Host revision-contract bridge for the live activation blocker. Current old Recovery Host computes exact disk revision e9330b786adf2268efa294ff76fa643eecbebe034fd326c951d6e160a30b9c68 using the previous recovery_host component spec; current code computes 4717fdb6bd23768c53e79f12e95a69cd6592315b39488e2fbad5dc4443447e42 because the current component spec added exactly electron/services/deviceIdentity.js. Prove and implement a fail-closed bridge: current componentRevision.js must pin SHA-256 ede358714afa4d35a2fc939f56051859922acdc3693a40563234bf81a650a4ee for deviceIdentity.js so the old host's hash of componentRevision.js binds the newly added file; new Recovery Host may accept a legacy expected revision only if the exact legacy-spec hash matches, all pinned added-file digests match current bytes, and current running_revision equals current disk_revision. Preserve the already-proven M1.2 activation/migration fixes and unrelated WIP.
- Mode: `mcp_only`
- Base HEAD: `4e5a5165e063b1b1816ef438babb19ca38d379d4`
- Worktree fingerprint: `b60ba0e3802a1a578fbcaa8974cec93e0be0c69295f674fbbe2519a70357abb6`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 11479 | 2026-08-17T04:44:17.085Z | run_started |  | PREFLIGHT |  |
| 11480 | 2026-08-17T04:44:17.987Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 11481 | 2026-08-17T04:45:55.216Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 11482 | 2026-08-17T04:45:55.378Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 11483 | 2026-08-17T04:45:55.542Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 11484 | 2026-08-17T04:45:55.771Z | state_transition | READY | ROUTED | reason=route_selected |
| 11485 | 2026-08-17T04:45:56.544Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=6b47926da3144b81a82ff32328be20e8 |
| 11486 | 2026-08-17T04:45:56.734Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 11487 | 2026-08-17T04:45:57.620Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=6b47926da3144b81a82ff32328be20e8 |
| 11488 | 2026-08-17T04:45:57.817Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 11489 | 2026-08-17T04:45:58.440Z | proof_cache_miss |  |  | reason=cold; stage_id=check:4bbbf93b8561fc21; input_fingerprint=575973c15cc778cc4057aa44b31d54528e094e2fb86184375111660cd93a1d77 |
| 11490 | 2026-08-17T04:45:58.868Z | managed_process_admitted |  |  | owner=default |
| 11491 | 2026-08-17T04:45:59.158Z | managed_process_started |  |  | owner=default |
| 11492 | 2026-08-17T04:45:59.659Z | managed_process_terminal |  |  | owner=default |
| 11493 | 2026-08-17T04:45:59.968Z | proof_recorded |  |  | stage_id=check:4bbbf93b8561fc21; status=passed; cache_hit=False; input_fingerprint=575973c15cc778cc4057aa44b31d54528e094e2fb86184375111660cd93a1d77 |
| 11494 | 2026-08-17T04:46:00.142Z | proof_cache_miss |  |  | reason=cold; stage_id=check:200367ba3719806c; input_fingerprint=a3606270b69c4d798df1ca94e6eb3075864cc42c1b9a64e70101826f3aafebf1 |
| 11495 | 2026-08-17T04:46:00.490Z | managed_process_admitted |  |  | owner=default |
| 11496 | 2026-08-17T04:46:00.766Z | managed_process_started |  |  | owner=default |
| 11497 | 2026-08-17T04:46:01.435Z | managed_process_terminal |  |  | owner=default |
| 11498 | 2026-08-17T04:46:01.701Z | proof_recorded |  |  | stage_id=check:200367ba3719806c; status=passed; cache_hit=False; input_fingerprint=a3606270b69c4d798df1ca94e6eb3075864cc42c1b9a64e70101826f3aafebf1 |
| 11499 | 2026-08-17T04:46:01.885Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=5608be2a94b55d9860362dec5109ec4cf58a420c499ed68362f3ebfaf2e1884d |
| 11500 | 2026-08-17T04:46:02.245Z | managed_process_admitted |  |  | owner=default |
| 11501 | 2026-08-17T04:46:02.507Z | managed_process_started |  |  | owner=default |
| 11502 | 2026-08-17T04:46:29.724Z | managed_process_terminal |  |  | owner=default |
| 11503 | 2026-08-17T04:46:31.518Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=5608be2a94b55d9860362dec5109ec4cf58a420c499ed68362f3ebfaf2e1884d |
| 11504 | 2026-08-17T04:46:32.236Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 11506 | 2026-08-17T04:57:31.071Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 11507 | 2026-08-17T04:57:31.513Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:4bbbf93b8561fc21 | passed | 575973c15cc778cc4057aa44b31d54528e094e2fb86184375111660cd93a1d77 | False | 1158 | 0 |
| check:200367ba3719806c | passed | a3606270b69c4d798df1ca94e6eb3075864cc42c1b9a64e70101826f3aafebf1 | False | 1255 | 0 |
| verify:tests | passed | 5608be2a94b55d9860362dec5109ec4cf58a420c499ed68362f3ebfaf2e1884d | False | 29186 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| df90fd47ae7947cb8315ee666b47d3b4 | accepted | 4e5a5165e063b1b1816ef438babb19ca38d379d4 | dc79cb6b5c9d1ef1f375e3dcbad9e777c024bd48abd959dfbbd91b5f7eda7ba3 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `28`
- Chain head: `c4cc768128287432575d74abc2dfcb11d77da281be00f3f1131a0fc4a1fc5315`
