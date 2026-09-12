# Orchestration Wave 1

- Run: `e817aa0815b9402b9c4a48c0e9aec103`
- Wave: `136a1d0d9fd54f6b9d441dbd9f4284dd`
- Objective: Natural #18: add a reporter-only retrospective process-outcome projection for generic CHECK_FAILED and BUILD_VERIFICATION_FAILED by linking each failure only to a unique durable failed proof using same-wave exact command_hash for checks and same-wave exact verify:<verification> stage for build verification. Surface only content-free outcome/linkage counts, preserve p2_failure_observation_v3 and historical events, and keep causal classification unchanged.
- Objective revision: `1`
- Objective SHA-256: `c4bf6d7fc659e0b0bd740b6eab4ce330cf4be905c959d811014e1f8d30a509ca`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `7bc1caee37107a15e74eb078b52fe314e5fa33ab`
- Worktree fingerprint: `b69f5ef0d8cca73e9c00ef95feef797c8f0bfa2660fc05351535dd0875bfe92d`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 46938 | 2026-09-10T07:02:40.793Z | run_started |  | PREFLIGHT |  |
| 46939 | 2026-09-10T07:02:41.509Z | observation_span_recorded |  |  |  |
| 46940 | 2026-09-10T07:02:41.762Z | solution_shadow_recommended |  |  |  |
| 46941 | 2026-09-10T07:02:48.240Z | observation_span_recorded |  |  |  |
| 46942 | 2026-09-10T07:02:48.453Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 46943 | 2026-09-10T07:05:16.158Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 46944 | 2026-09-10T07:05:16.321Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 46945 | 2026-09-10T07:05:16.519Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 46946 | 2026-09-10T07:05:16.666Z | state_transition | READY | ROUTED | reason=route_selected |
| 46947 | 2026-09-10T07:05:16.913Z | observation_span_recorded |  |  |  |
| 46948 | 2026-09-10T07:05:18.070Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=c3c70e569e444ea493c97971c9d9193c |
| 46949 | 2026-09-10T07:05:18.248Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 46950 | 2026-09-10T07:05:19.297Z | patch_surface_observed |  |  |  |
| 46951 | 2026-09-10T07:05:19.481Z | observation_span_recorded |  |  |  |
| 46952 | 2026-09-10T07:05:19.794Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=c3c70e569e444ea493c97971c9d9193c |
| 46953 | 2026-09-10T07:05:19.966Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 46954 | 2026-09-10T07:05:20.896Z | proof_cache_miss |  |  | reason=cold; stage_id=check:832c7ad9001e7bab; input_fingerprint=52984ac0b56ff80153fc2caa0f5ac7bacd5019286fd0960b1ede6214b5a8df25 |
| 46955 | 2026-09-10T07:05:21.250Z | managed_process_admitted |  |  | owner=default |
| 46956 | 2026-09-10T07:05:21.509Z | managed_process_started |  |  | owner=default |
| 46957 | 2026-09-10T07:05:24.416Z | managed_process_terminal |  |  | owner=default |
| 46958 | 2026-09-10T07:05:24.689Z | proof_recorded |  |  | stage_id=check:832c7ad9001e7bab; status=passed; cache_hit=False; input_fingerprint=52984ac0b56ff80153fc2caa0f5ac7bacd5019286fd0960b1ede6214b5a8df25 |
| 46959 | 2026-09-10T07:05:24.832Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:1e606d62e02d0f68; input_fingerprint=7ade88bfa66faaad0a1c7f9ee76effe6de0e7df5b736074380c34402b4df0fb3 |
| 46960 | 2026-09-10T07:05:25.110Z | managed_process_admitted |  |  | owner=default |
| 46961 | 2026-09-10T07:05:25.422Z | managed_process_started |  |  | owner=default |
| 46962 | 2026-09-10T07:05:55.431Z | managed_process_terminal |  |  | owner=default |
| 46963 | 2026-09-10T07:05:55.991Z | proof_recorded |  |  | stage_id=check:1e606d62e02d0f68; status=passed; cache_hit=False; input_fingerprint=7ade88bfa66faaad0a1c7f9ee76effe6de0e7df5b736074380c34402b4df0fb3 |
| 46964 | 2026-09-10T07:05:56.214Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:6d884becdef27c18; input_fingerprint=8054d9ac2aedeecd57ad63b3136ca61bd5d9f00a4597db237486bdf1e96ea99a |
| 46965 | 2026-09-10T07:05:56.680Z | managed_process_admitted |  |  | owner=default |
| 46966 | 2026-09-10T07:05:57.135Z | managed_process_started |  |  | owner=default |
| 46967 | 2026-09-10T07:06:01.373Z | managed_process_terminal |  |  | owner=default |
| 46968 | 2026-09-10T07:06:01.871Z | proof_recorded |  |  | stage_id=check:6d884becdef27c18; status=passed; cache_hit=False; input_fingerprint=8054d9ac2aedeecd57ad63b3136ca61bd5d9f00a4597db237486bdf1e96ea99a |
| 46969 | 2026-09-10T07:06:02.361Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:20af4e8e69d7c88b; input_fingerprint=7388ed02c41d08d8d6bf096aad826fb2b0ca2dc4be650475e2295196e82e6e86 |
| 46970 | 2026-09-10T07:06:02.861Z | managed_process_admitted |  |  | owner=default |
| 46971 | 2026-09-10T07:06:03.271Z | managed_process_started |  |  | owner=default |
| 46972 | 2026-09-10T07:06:03.981Z | managed_process_terminal |  |  | owner=default |
| 46973 | 2026-09-10T07:06:04.444Z | proof_recorded |  |  | stage_id=check:20af4e8e69d7c88b; status=passed; cache_hit=False; input_fingerprint=7388ed02c41d08d8d6bf096aad826fb2b0ca2dc4be650475e2295196e82e6e86 |
| 46974 | 2026-09-10T07:06:06.131Z | observation_span_recorded |  |  |  |
| 46975 | 2026-09-10T07:06:06.398Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 46976 | 2026-09-10T07:06:53.334Z | managed_process_admitted |  |  | owner=default |
| 46977 | 2026-09-10T07:06:53.681Z | managed_process_started |  |  | owner=default |
| 46978 | 2026-09-10T07:06:56.372Z | managed_process_terminal |  |  | owner=default |
| 46979 | 2026-09-10T07:07:34.163Z | quality_outcome_recorded |  |  |  |
| 46980 | 2026-09-10T07:07:34.342Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 46981 | 2026-09-10T07:07:34.647Z | observation_span_recorded |  |  |  |
| 46982 | 2026-09-10T07:07:34.909Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:832c7ad9001e7bab | passed | 52984ac0b56ff80153fc2caa0f5ac7bacd5019286fd0960b1ede6214b5a8df25 | False | 3508 | 0 |
| check:1e606d62e02d0f68 | passed | 7ade88bfa66faaad0a1c7f9ee76effe6de0e7df5b736074380c34402b4df0fb3 | False | 30733 | 0 |
| check:6d884becdef27c18 | passed | 8054d9ac2aedeecd57ad63b3136ca61bd5d9f00a4597db237486bdf1e96ea99a | False | 5242 | 0 |
| check:20af4e8e69d7c88b | passed | 7388ed02c41d08d8d6bf096aad826fb2b0ca2dc4be650475e2295196e82e6e86 | False | 1598 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| e136230aa9754055b365b907ce28c355 | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | df99b4c4747fd60010afff9f31074f2dc29c9be6193eb2af7b2c112ea1ae85c0 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `45`
- Chain head: `08b764670127bdbd0c9ffe285281ab4ddb714a9846ec2749361b1f5f22fe81bd`
