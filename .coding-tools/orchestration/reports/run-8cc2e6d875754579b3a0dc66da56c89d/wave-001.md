# Orchestration Wave 1

- Run: `8cc2e6d875754579b3a0dc66da56c89d`
- Wave: `f4685ca3c80b401887a3c5ae831bb658`
- Objective: Diagnose why the production WebMCP Recovery Supervisor Scheduled Task invoking the installed recovery-supervisor.ps1 -Action Run does not publish a fresh capability-bearing heartbeat after the official Install. Determine the exact production-only failure cause using read-only evidence: Scheduled Task definition/result/principal/settings, TaskScheduler Operational events, installed/source/status/manifest timestamps and hashes, any live installed Run process, install-directory timestamps, source Run/lock logic, and the full focused Recovery Supervisor test file. Do not retry Install, do not start/stop/delete tasks, do not edit source/runtime files, and do not restart runtime in this wave.
- Objective revision: `1`
- Objective SHA-256: `1e9d4dad17fc38ffafa72174bc3d55d8c566af44b76e8332b4dd08f5e1de248f`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6`
- Worktree fingerprint: `4b92be7b9fc17947885c8e371f5f2aa0c2be7f9999e2e9546e12dc9b71db5732`
- Contract fingerprint: `270e9a76c407a40e3a8d7c9151f355841314d54e778559402beef4517ffe282f`
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 57931 | 2026-09-15T07:43:11.965Z | run_started |  | PREFLIGHT |  |
| 57932 | 2026-09-15T07:43:12.672Z | observation_span_recorded |  |  |  |
| 57933 | 2026-09-15T07:43:13.307Z | observation_span_recorded |  |  |  |
| 57934 | 2026-09-15T07:43:13.570Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 57935 | 2026-09-15T07:43:13.804Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 57936 | 2026-09-15T07:43:13.995Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 57937 | 2026-09-15T07:43:14.209Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 57938 | 2026-09-15T07:43:14.414Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 57939 | 2026-09-15T07:43:14.656Z | state_transition | READY | ROUTED | reason=route_selected |
| 57940 | 2026-09-15T07:43:14.915Z | observation_span_recorded |  |  |  |
| 57941 | 2026-09-15T07:43:15.545Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=e106df4309fb4e6c84c2821edaa2e58c |
| 57942 | 2026-09-15T07:43:15.777Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 57943 | 2026-09-15T07:43:16.400Z | observation_span_recorded |  |  |  |
| 57944 | 2026-09-15T07:43:16.781Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=e106df4309fb4e6c84c2821edaa2e58c |
| 57945 | 2026-09-15T07:43:17.013Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 57946 | 2026-09-15T07:43:17.592Z | proof_cache_miss |  |  | reason=cold; stage_id=check:1d6a1170eabfa845; input_fingerprint=15873e4f929b4d8d78e319a05c02fa5bf4d9a821e90886731098329ee1948769 |
| 57947 | 2026-09-15T07:43:18.054Z | managed_process_admitted |  |  | owner=default |
| 57948 | 2026-09-15T07:43:18.397Z | managed_process_started |  |  | owner=default |
| 57949 | 2026-09-15T07:43:20.428Z | managed_process_terminal |  |  | owner=default |
| 57950 | 2026-09-15T07:43:20.793Z | proof_recorded |  |  | stage_id=check:1d6a1170eabfa845; status=passed; cache_hit=False; input_fingerprint=15873e4f929b4d8d78e319a05c02fa5bf4d9a821e90886731098329ee1948769 |
| 57951 | 2026-09-15T07:43:20.985Z | proof_cache_miss |  |  | reason=cold; stage_id=check:2e539278f50a7dec; input_fingerprint=2f2c98d247e263e07483ae5c91f44ccdb07a5d24fa352bf4f822fe7115e0144b |
| 57952 | 2026-09-15T07:43:21.365Z | managed_process_admitted |  |  | owner=default |
| 57953 | 2026-09-15T07:43:21.753Z | managed_process_started |  |  | owner=default |
| 57954 | 2026-09-15T07:43:22.577Z | managed_process_terminal |  |  | owner=default |
| 57955 | 2026-09-15T07:43:23.023Z | proof_recorded |  |  | stage_id=check:2e539278f50a7dec; status=passed; cache_hit=False; input_fingerprint=2f2c98d247e263e07483ae5c91f44ccdb07a5d24fa352bf4f822fe7115e0144b |
| 57956 | 2026-09-15T07:43:23.232Z | proof_cache_miss |  |  | reason=cold; stage_id=check:35a7dd5a1e3e1b91; input_fingerprint=f989b61ef1e1231373ba3c7ad8c3ed6b6450a21278f01e881268faf95d389b30 |
| 57957 | 2026-09-15T07:43:23.666Z | managed_process_admitted |  |  | owner=default |
| 57958 | 2026-09-15T07:43:24.006Z | managed_process_started |  |  | owner=default |
| 57959 | 2026-09-15T07:43:25.187Z | managed_process_reconciled |  |  | reason=root_process_gone; owner=default |
| 57960 | 2026-09-15T07:43:25.663Z | proof_recorded |  |  | stage_id=check:35a7dd5a1e3e1b91; status=passed; cache_hit=False; input_fingerprint=f989b61ef1e1231373ba3c7ad8c3ed6b6450a21278f01e881268faf95d389b30 |
| 57961 | 2026-09-15T07:43:25.898Z | proof_cache_miss |  |  | reason=cold; stage_id=check:c5bf9247f7593217; input_fingerprint=440c90ba1368821722b247d5cdcb1539f16d343634c7caca6c812066789d9edf |
| 57962 | 2026-09-15T07:43:26.232Z | managed_process_admitted |  |  | owner=default |
| 57963 | 2026-09-15T07:43:26.541Z | managed_process_started |  |  | owner=default |
| 57964 | 2026-09-15T07:43:27.454Z | managed_process_terminal |  |  | owner=default |
| 57965 | 2026-09-15T07:43:28.080Z | proof_recorded |  |  | stage_id=check:c5bf9247f7593217; status=passed; cache_hit=False; input_fingerprint=440c90ba1368821722b247d5cdcb1539f16d343634c7caca6c812066789d9edf |
| 57966 | 2026-09-15T07:43:29.017Z | proof_cache_miss |  |  | reason=cold; stage_id=check:cbe4cb60fda51955; input_fingerprint=20d9a5932c9a21211839a83f5f90545d27d3a4f24cd9daeea50a812f1bb7aac3 |
| 57967 | 2026-09-15T07:43:29.469Z | managed_process_admitted |  |  | owner=default |
| 57968 | 2026-09-15T07:43:29.930Z | managed_process_started |  |  | owner=default |
| 57969 | 2026-09-15T07:43:30.544Z | managed_process_terminal |  |  | owner=default |
| 57970 | 2026-09-15T07:43:30.970Z | proof_recorded |  |  | stage_id=check:cbe4cb60fda51955; status=passed; cache_hit=False; input_fingerprint=20d9a5932c9a21211839a83f5f90545d27d3a4f24cd9daeea50a812f1bb7aac3 |
| 57971 | 2026-09-15T07:43:31.380Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:fe3ffbf7aa7a92a6; input_fingerprint=cb0f1472e83a4b7594865b4367765ce0d5ce41ab6c3b650abe4e141be1fb5a9d |
| 57972 | 2026-09-15T07:43:31.887Z | managed_process_admitted |  |  | owner=default |
| 57973 | 2026-09-15T07:43:32.210Z | managed_process_started |  |  | owner=default |
| 57975 | 2026-09-15T07:43:57.322Z | managed_process_terminal |  |  | owner=default |
| 57976 | 2026-09-15T07:43:57.776Z | proof_recorded |  |  | stage_id=check:fe3ffbf7aa7a92a6; status=failed; cache_hit=False; input_fingerprint=cb0f1472e83a4b7594865b4367765ce0d5ce41ab6c3b650abe4e141be1fb5a9d |
| 57977 | 2026-09-15T07:43:58.058Z | observation_span_recorded |  |  |  |
| 57978 | 2026-09-15T07:43:58.262Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 57979 | 2026-09-15T07:43:58.567Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 57980 | 2026-09-15T07:43:58.813Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |
| 57981 | 2026-09-15T07:44:19.646Z | continuity_telemetry_recorded |  |  |  |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:1d6a1170eabfa845 | passed | 15873e4f929b4d8d78e319a05c02fa5bf4d9a821e90886731098329ee1948769 | False | 2821 | 0 |
| check:2e539278f50a7dec | passed | 2f2c98d247e263e07483ae5c91f44ccdb07a5d24fa352bf4f822fe7115e0144b | False | 1601 | 0 |
| check:35a7dd5a1e3e1b91 | passed | f989b61ef1e1231373ba3c7ad8c3ed6b6450a21278f01e881268faf95d389b30 | False | 2008 | 0 |
| check:c5bf9247f7593217 | passed | 440c90ba1368821722b247d5cdcb1539f16d343634c7caca6c812066789d9edf | False | 1625 | 0 |
| check:cbe4cb60fda51955 | passed | 20d9a5932c9a21211839a83f5f90545d27d3a4f24cd9daeea50a812f1bb7aac3 | False | 1553 | 0 |
| check:fe3ffbf7aa7a92a6 | failed | cb0f1472e83a4b7594865b4367765ce0d5ce41ab6c3b650abe4e141be1fb5a9d | False | 26005 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `117`
- Chain head: `50b0fb572d5b96878be3a397fa5e21771d786a44f19bc6f096daea79d3f68634`
