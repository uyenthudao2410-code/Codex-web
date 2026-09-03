# Orchestration Wave 1

- Run: `f423d1ffaedd4c1d81dac0eb63af489c`
- Wave: `8b8b0cf40c7d45c5b3aa4243d264b745`
- Objective: Continue the existing evidence-only baseline roll-forward RUN/WAVE. Do not modify source or runtime. Prove current HEAD and Coding MCP correctness with module-size guard, repository diff check, and the full pytest suite. Preserve all dirty WIP and .coding-tools evidence; do not touch unbound job 71f8e9646b644839bbd4f95be7dba7d5. This proof will be followed only if green by exact current-byte final-acceptance attestations for the independently recomputed untrusted coding_mcp baseline paths.
- Objective revision: `1`
- Objective SHA-256: `0ca1c56cbb5edc7e5b491a940af67c0847f319ef91128da85f73dc067d6f7b40`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `30b7d1b971b65034d3e4c95568c970fcc0e9380c`
- Worktree fingerprint: `cd9fdac8b4ee50cfe307293d1356ef0f974776cd285d00e4dd4355cdb040bbad`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 33939 | 2026-09-01T01:26:48.250Z | run_started |  | PREFLIGHT |  |
| 33940 | 2026-09-01T01:26:48.618Z | observation_span_recorded |  |  |  |
| 33941 | 2026-09-01T01:26:48.868Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 33942 | 2026-09-01T01:26:49.079Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 33943 | 2026-09-01T01:26:49.522Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 33944 | 2026-09-01T01:26:49.685Z | state_transition | READY | ROUTED | reason=route_selected |
| 33945 | 2026-09-01T01:26:49.898Z | observation_span_recorded |  |  |  |
| 33946 | 2026-09-01T01:26:50.692Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=5bbcb77742714c92801574b7f580540a |
| 33947 | 2026-09-01T01:26:50.851Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 33948 | 2026-09-01T01:26:51.657Z | observation_span_recorded |  |  |  |
| 33949 | 2026-09-01T01:26:52.010Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=5bbcb77742714c92801574b7f580540a |
| 33950 | 2026-09-01T01:26:52.188Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 33951 | 2026-09-01T01:26:52.941Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:80a1a46bd01d26a3; input_fingerprint=656387423ca080141198ea9651d187664343ba5be00e8e45105c0d118cc33433 |
| 33952 | 2026-09-01T01:26:53.360Z | managed_process_admitted |  |  | owner=default |
| 33953 | 2026-09-01T01:26:53.708Z | managed_process_started |  |  | owner=default |
| 33954 | 2026-09-01T01:26:54.101Z | managed_process_terminal |  |  | owner=default |
| 33955 | 2026-09-01T01:26:54.523Z | proof_recorded |  |  | stage_id=check:80a1a46bd01d26a3; status=passed; cache_hit=False; input_fingerprint=656387423ca080141198ea9651d187664343ba5be00e8e45105c0d118cc33433 |
| 33956 | 2026-09-01T01:26:54.714Z | proof_cache_miss |  |  | reason=cold; stage_id=check:c965b49d51d1831f; input_fingerprint=7275acba6b491c61d699d9e398906f38c797febb7bc7b2d7dd45cf3320d9d8f5 |
| 33957 | 2026-09-01T01:26:55.116Z | managed_process_admitted |  |  | owner=default |
| 33958 | 2026-09-01T01:26:55.468Z | managed_process_started |  |  | owner=default |
| 33959 | 2026-09-01T01:26:55.942Z | managed_process_terminal |  |  | owner=default |
| 33960 | 2026-09-01T01:26:56.369Z | proof_recorded |  |  | stage_id=check:c965b49d51d1831f; status=passed; cache_hit=False; input_fingerprint=7275acba6b491c61d699d9e398906f38c797febb7bc7b2d7dd45cf3320d9d8f5 |
| 33961 | 2026-09-01T01:26:56.566Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:7500afc22c04e24e; input_fingerprint=c41e3dac9cbfdf5a42463b34ea000a60994e86c7fcff35a234e8703cf494a407 |
| 33962 | 2026-09-01T01:26:56.953Z | managed_process_admitted |  |  | owner=default |
| 33963 | 2026-09-01T01:26:57.294Z | managed_process_started |  |  | owner=default |
| 33964 | 2026-09-01T01:26:58.101Z | managed_process_terminal |  |  | owner=default |
| 33965 | 2026-09-01T01:26:58.468Z | proof_recorded |  |  | stage_id=check:7500afc22c04e24e; status=passed; cache_hit=False; input_fingerprint=c41e3dac9cbfdf5a42463b34ea000a60994e86c7fcff35a234e8703cf494a407 |
| 33966 | 2026-09-01T01:26:58.670Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=1fd8d6b38d211115eb40a1330e08645ac165781d01e3c9e0ef1b339a08d2c14b |
| 33967 | 2026-09-01T01:26:59.125Z | managed_process_admitted |  |  | owner=default |
| 33968 | 2026-09-01T01:26:59.481Z | managed_process_started |  |  | owner=default |
| 33969 | 2026-09-01T01:32:14.028Z | managed_process_terminal |  |  | owner=default |
| 33970 | 2026-09-01T01:32:15.396Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=1fd8d6b38d211115eb40a1330e08645ac165781d01e3c9e0ef1b339a08d2c14b |
| 33971 | 2026-09-01T01:32:15.691Z | observation_span_recorded |  |  |  |
| 33972 | 2026-09-01T01:32:15.926Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 34036 | 2026-09-01T01:41:24.964Z | managed_process_admitted |  |  | owner=default |
| 34037 | 2026-09-01T01:41:25.356Z | managed_process_started |  |  | owner=default |
| 34038 | 2026-09-01T01:41:25.883Z | managed_process_terminal |  |  | owner=default |
| 34039 | 2026-09-01T01:41:33.660Z | managed_process_admitted |  |  | owner=default |
| 34040 | 2026-09-01T01:41:34.005Z | managed_process_started |  |  | owner=default |
| 34041 | 2026-09-01T01:41:34.480Z | managed_process_terminal |  |  | owner=default |
| 34042 | 2026-09-01T01:41:45.292Z | managed_process_admitted |  |  | owner=default |
| 34043 | 2026-09-01T01:41:45.700Z | managed_process_started |  |  | owner=default |
| 34044 | 2026-09-01T01:41:46.166Z | managed_process_terminal |  |  | owner=default |
| 34045 | 2026-09-01T01:41:55.421Z | managed_process_admitted |  |  | owner=default |
| 34046 | 2026-09-01T01:41:55.790Z | managed_process_started |  |  | owner=default |
| 34047 | 2026-09-01T01:41:56.334Z | managed_process_terminal |  |  | owner=default |
| 34048 | 2026-09-01T01:42:06.567Z | managed_process_admitted |  |  | owner=default |
| 34049 | 2026-09-01T01:42:06.941Z | managed_process_started |  |  | owner=default |
| 34050 | 2026-09-01T01:42:07.411Z | managed_process_terminal |  |  | owner=default |
| 34051 | 2026-09-01T01:42:19.012Z | managed_process_admitted |  |  | owner=default |
| 34052 | 2026-09-01T01:42:19.533Z | managed_process_started |  |  | owner=default |
| 34053 | 2026-09-01T01:42:20.025Z | managed_process_terminal |  |  | owner=default |
| 34054 | 2026-09-01T01:42:31.270Z | managed_process_admitted |  |  | owner=default |
| 34055 | 2026-09-01T01:42:31.624Z | managed_process_started |  |  | owner=default |
| 34056 | 2026-09-01T01:42:32.225Z | managed_process_terminal |  |  | owner=default |
| 34059 | 2026-09-01T01:42:53.134Z | managed_process_admitted |  |  | owner=default |
| 34060 | 2026-09-01T01:42:53.525Z | managed_process_started |  |  | owner=default |
| 34061 | 2026-09-01T01:42:54.709Z | managed_process_terminal |  |  | owner=default |
| 34068 | 2026-09-01T01:49:55.916Z | managed_process_admitted |  |  | owner=default |
| 34069 | 2026-09-01T01:49:56.283Z | managed_process_started |  |  | owner=default |
| 34070 | 2026-09-01T01:49:56.766Z | managed_process_terminal |  |  | owner=default |
| 34071 | 2026-09-01T01:50:04.800Z | managed_process_admitted |  |  | owner=default |
| 34072 | 2026-09-01T01:50:05.186Z | managed_process_started |  |  | owner=default |
| 34073 | 2026-09-01T01:50:05.731Z | managed_process_terminal |  |  | owner=default |
| 34108 | 2026-09-01T01:57:21.335Z | observation_span_recorded |  |  |  |
| 34109 | 2026-09-01T01:57:21.545Z | failure_observed | ACCEPTING | ACCEPTING | reason=ACCEPTANCE_FILE_ATTESTATION_REQUIRED — final acceptance proved two pre-existing dirty acceptance paths lack durable current-lineage provenance: resources/coding-tools-mcp/coding_tools_mcp/problem_lineage.py and resources/coding-tools-mcp/tests/test_problem_lineage.py. Replan the SAME RUN only to adopt these exact current bytes without content mutation; preserve the existing green proof authority and do not create a new RUN.; failure_class=SOL_REJECTED |
| 34110 | 2026-09-01T01:57:21.761Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |
| 34111 | 2026-09-01T01:57:22.008Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:80a1a46bd01d26a3 | passed | 656387423ca080141198ea9651d187664343ba5be00e8e45105c0d118cc33433 | False | 1192 | 0 |
| check:c965b49d51d1831f | passed | 7275acba6b491c61d699d9e398906f38c797febb7bc7b2d7dd45cf3320d9d8f5 | False | 1245 | 0 |
| check:7500afc22c04e24e | passed | c41e3dac9cbfdf5a42463b34ea000a60994e86c7fcff35a234e8703cf494a407 | False | 1548 | 0 |
| verify:tests | passed | 1fd8d6b38d211115eb40a1330e08645ac165781d01e3c9e0ef1b339a08d2c14b | False | 316203 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `204`
- Chain head: `855850803062800611e9d45e3c4ddd2517e83caefea8b866fb59ecf9ff4bddbf`
