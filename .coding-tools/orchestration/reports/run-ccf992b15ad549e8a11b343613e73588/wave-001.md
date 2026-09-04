# Orchestration Wave 1

- Run: `ccf992b15ad549e8a11b343613e73588`
- Wave: `13f9cc453081468bb977092f66ebc587`
- Objective: G2-P10 provenance closure only for the exact current canonical usage/cost analytics packet. Adopt without changing source bytes exactly renderer/dashboard.js SHA-256 5d1086200c10afcf8e30da55407cf919e5f1bba49fe9a7ef53ec88390562345c; tests/dashboard-analytics.test.js SHA-256 a95179979d81edf8e5ba85aed5a4ff0fc84c9bfaa925ac875cd8be01a0a15d5b; resources/coding-tools-mcp/coding_tools_mcp/operations_analytics.py SHA-256 45ec6ba6363029d93d5f83463c246aa2ee7b22f3b2032dc0859c9f6f7459d508; resources/coding-tools-mcp/tests/test_operations_analytics.py SHA-256 5650062710d0630fada4614d90b6b30c98f0d0ba513e53820a4682ddc9e2884b. Causal objective: dashboard/operations analytics display only canonical measured UsageEvent tokens/cost and explicit measurement coverage; transport/model-visible bytes remain bytes and are never converted into plausible tokens; byte-to-token and settings-estimate secondary paths stay removed; missing measurements remain unknown_not_zero. Expose and prove exactly six evidence-qualified coverage planes: controller usage, provider usage, retained tool invocation versus expected calls, tool-card tokens explicitly unobserved, cost completeness, exact RUN attribution. Accepted-result KPIs remain primary. renderer/index.html is ACCEPTED_CURRENT dependency context only and must not be adopted or modified. Preserve all concurrent dirty work and .coding-tools evidence. No source outside these four paths, no live provider, no fabricated usage, no browser UI, no direct SQLite, no stale-run reconciliation, no Problems/outcomes/cohorts, no reset/restore/clean/rebase, no commit/push/tag/release/publish/deploy.
- Objective revision: `1`
- Objective SHA-256: `14c90381e20bd664692cdac4e703ff786f389ccfe219d9b8b30aa2a6de45f0a9`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `80aceb583202ad381c25687969fb48adbf74622c`
- Worktree fingerprint: `6b5fb2badfbcfa32b95881356c90eb51b89d687739b0b7df90dd27ec25209209`
- Contract fingerprint: `2c2f43580cbfcd810793599570ad68e0a46f8f658fa16711817d580effbe824a`
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 38367 | 2026-09-03T17:44:55.890Z | run_started |  | PREFLIGHT |  |
| 38368 | 2026-09-03T17:44:56.294Z | observation_span_recorded |  |  |  |
| 38369 | 2026-09-03T17:44:57.290Z | observation_span_recorded |  |  |  |
| 38370 | 2026-09-03T17:44:57.553Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 38371 | 2026-09-03T17:44:57.761Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 38372 | 2026-09-03T17:44:57.936Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 38373 | 2026-09-03T17:44:58.151Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 38374 | 2026-09-03T17:44:58.444Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 38375 | 2026-09-03T17:44:58.681Z | state_transition | READY | ROUTED | reason=route_selected |
| 38376 | 2026-09-03T17:44:58.946Z | observation_span_recorded |  |  |  |
| 38377 | 2026-09-03T17:45:00.073Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=191059a3602746cf8925634d03a9363d |
| 38378 | 2026-09-03T17:45:00.301Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 38379 | 2026-09-03T17:45:01.218Z | existing_file_adoption_observed |  |  |  |
| 38380 | 2026-09-03T17:45:01.464Z | observation_span_recorded |  |  |  |
| 38381 | 2026-09-03T17:45:01.781Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=191059a3602746cf8925634d03a9363d |
| 38382 | 2026-09-03T17:45:01.960Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 38383 | 2026-09-03T17:45:02.833Z | proof_cache_miss |  |  | reason=cold; stage_id=check:19b120e61f158d04; input_fingerprint=d7cc4d98bddbd160ade4c9646a421202759f5731c372f6b5762d9f58025a4497 |
| 38384 | 2026-09-03T17:45:03.250Z | managed_process_admitted |  |  | owner=default |
| 38385 | 2026-09-03T17:45:03.598Z | managed_process_started |  |  | owner=default |
| 38386 | 2026-09-03T17:45:04.279Z | managed_process_terminal |  |  | owner=default |
| 38387 | 2026-09-03T17:45:04.678Z | proof_recorded |  |  | stage_id=check:19b120e61f158d04; status=passed; cache_hit=False; input_fingerprint=d7cc4d98bddbd160ade4c9646a421202759f5731c372f6b5762d9f58025a4497 |
| 38388 | 2026-09-03T17:45:04.943Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:d3e764597ea65558; input_fingerprint=88bda76486470fc59262d93d45823e0e91ffed7367c48471907700d388bb7b25 |
| 38389 | 2026-09-03T17:45:05.408Z | managed_process_admitted |  |  | owner=default |
| 38390 | 2026-09-03T17:45:05.816Z | managed_process_started |  |  | owner=default |
| 38391 | 2026-09-03T17:45:06.283Z | managed_process_terminal |  |  | owner=default |
| 38392 | 2026-09-03T17:45:06.727Z | proof_recorded |  |  | stage_id=check:d3e764597ea65558; status=passed; cache_hit=False; input_fingerprint=88bda76486470fc59262d93d45823e0e91ffed7367c48471907700d388bb7b25 |
| 38393 | 2026-09-03T17:45:06.938Z | proof_cache_miss |  |  | reason=cold; stage_id=check:fc4c3fee64ecf083; input_fingerprint=bb6208e8f488b6b7cc9b3870078ed92a9443e173c8a1c56541a3ef48c426dd80 |
| 38394 | 2026-09-03T17:45:07.334Z | managed_process_admitted |  |  | owner=default |
| 38395 | 2026-09-03T17:45:07.691Z | managed_process_started |  |  | owner=default |
| 38396 | 2026-09-03T17:45:09.032Z | managed_process_terminal |  |  | owner=default |
| 38397 | 2026-09-03T17:45:09.426Z | proof_recorded |  |  | stage_id=check:fc4c3fee64ecf083; status=passed; cache_hit=False; input_fingerprint=bb6208e8f488b6b7cc9b3870078ed92a9443e173c8a1c56541a3ef48c426dd80 |
| 38398 | 2026-09-03T17:45:09.643Z | observation_span_recorded |  |  |  |
| 38399 | 2026-09-03T17:45:09.864Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 38400 | 2026-09-03T17:45:28.255Z | quality_outcome_recorded |  |  |  |
| 38401 | 2026-09-03T17:45:28.488Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 38402 | 2026-09-03T17:45:28.762Z | observation_span_recorded |  |  |  |
| 38403 | 2026-09-03T17:45:29.000Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:19b120e61f158d04 | passed | d7cc4d98bddbd160ade4c9646a421202759f5731c372f6b5762d9f58025a4497 | False | 1444 | 0 |
| check:d3e764597ea65558 | passed | 88bda76486470fc59262d93d45823e0e91ffed7367c48471907700d388bb7b25 | False | 1361 | 0 |
| check:fc4c3fee64ecf083 | passed | bb6208e8f488b6b7cc9b3870078ed92a9443e173c8a1c56541a3ef48c426dd80 | False | 2158 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 475769e7ec7947d796c173608d72fc77 | accepted | 80aceb583202ad381c25687969fb48adbf74622c | 977942251e514701a849743d834708d2557224eb137687b64f38a0e4dd245452 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `37`
- Chain head: `bbe0383613d4e8a9853a0bc76ea09d3da80ebe9dfb6bae4b11de59a250de2996`
