# Orchestration Wave 1

- Run: `5ed4115abd52443fbc4a5b1034cbe0dd`
- Wave: `a93d2c5e325a4d22a8fb5b9341eae4f5`
- Objective: Make Recovery Supervisor reinstall replace an orphaned prior supervisor cooperatively and fail closed unless the exact newly installed capability-bearing process publishes a fresh heartbeat.
- Objective revision: `1`
- Objective SHA-256: `492b4f484834f87ed90d12aa1821695fd1e01cd1d5fcf5f1ca5d18011d557398`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `7bc1caee37107a15e74eb078b52fe314e5fa33ab`
- Worktree fingerprint: `8ce6e50a994c7a89260f52b668edc8f91df316388b88d084ad47c5d2af940540`
- Contract fingerprint: `5f5ab95312751d2577cc6cabb17afe507976a8085af893af87e1fac6394826e8`
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 43936 | 2026-09-08T14:27:35.687Z | run_started |  | PREFLIGHT |  |
| 43937 | 2026-09-08T14:27:36.082Z | observation_span_recorded |  |  |  |
| 43938 | 2026-09-08T14:27:36.249Z | solution_shadow_recommended |  |  |  |
| 43939 | 2026-09-08T14:27:36.411Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 43940 | 2026-09-08T14:27:36.554Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 43941 | 2026-09-08T14:27:36.763Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 43942 | 2026-09-08T14:27:36.954Z | state_transition | READY | ROUTED | reason=route_selected |
| 43943 | 2026-09-08T14:27:37.300Z | observation_span_recorded |  |  |  |
| 43944 | 2026-09-08T14:27:38.062Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=7064e2bb15ef463186dc4bd79c74af01 |
| 43945 | 2026-09-08T14:27:38.294Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 43946 | 2026-09-08T14:27:39.052Z | existing_file_adoption_observed |  |  |  |
| 43947 | 2026-09-08T14:27:39.230Z | observation_span_recorded |  |  |  |
| 43948 | 2026-09-08T14:27:39.553Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=7064e2bb15ef463186dc4bd79c74af01 |
| 43949 | 2026-09-08T14:27:39.688Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 43950 | 2026-09-08T14:27:40.434Z | proof_cache_miss |  |  | reason=cold; stage_id=check:fe3ffbf7aa7a92a6; input_fingerprint=320ea16c14c48429d787f3b83cdb83d782d9b5a934961661f78bf650c411e8a1 |
| 43951 | 2026-09-08T14:27:40.768Z | managed_process_admitted |  |  | owner=default |
| 43952 | 2026-09-08T14:27:41.058Z | managed_process_started |  |  | owner=default |
| 43953 | 2026-09-08T14:28:04.577Z | managed_process_terminal |  |  | owner=default |
| 43954 | 2026-09-08T14:28:04.907Z | proof_recorded |  |  | stage_id=check:fe3ffbf7aa7a92a6; status=passed; cache_hit=False; input_fingerprint=320ea16c14c48429d787f3b83cdb83d782d9b5a934961661f78bf650c411e8a1 |
| 43955 | 2026-09-08T14:28:05.150Z | proof_cache_miss |  |  | reason=cold; stage_id=check:46508d374f5d93c2; input_fingerprint=5cf7c53c65528e0df968036b6227c6a9e5f67edee14ceab3b8ea6cbe14df9616 |
| 43956 | 2026-09-08T14:28:05.592Z | managed_process_admitted |  |  | owner=default |
| 43957 | 2026-09-08T14:28:05.891Z | managed_process_started |  |  | owner=default |
| 43958 | 2026-09-08T14:28:06.509Z | managed_process_terminal |  |  | owner=default |
| 43959 | 2026-09-08T14:28:06.816Z | proof_recorded |  |  | stage_id=check:46508d374f5d93c2; status=passed; cache_hit=False; input_fingerprint=5cf7c53c65528e0df968036b6227c6a9e5f67edee14ceab3b8ea6cbe14df9616 |
| 43960 | 2026-09-08T14:28:07.008Z | proof_cache_miss |  |  | reason=cold; stage_id=check:9bb70a158b1c7dcc; input_fingerprint=0ce13a3f2d58969f7da206541edc8e705431003b53d2b56ba693d142f9ac2c72 |
| 43961 | 2026-09-08T14:28:07.346Z | managed_process_admitted |  |  | owner=default |
| 43962 | 2026-09-08T14:28:07.673Z | managed_process_started |  |  | owner=default |
| 43963 | 2026-09-08T14:28:08.199Z | managed_process_terminal |  |  | owner=default |
| 43964 | 2026-09-08T14:28:08.507Z | proof_recorded |  |  | stage_id=check:9bb70a158b1c7dcc; status=passed; cache_hit=False; input_fingerprint=0ce13a3f2d58969f7da206541edc8e705431003b53d2b56ba693d142f9ac2c72 |
| 43965 | 2026-09-08T14:28:08.682Z | observation_span_recorded |  |  |  |
| 43966 | 2026-09-08T14:28:08.846Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 43967 | 2026-09-08T14:28:44.755Z | quality_outcome_recorded |  |  |  |
| 43968 | 2026-09-08T14:28:44.909Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 43969 | 2026-09-08T14:28:45.150Z | observation_span_recorded |  |  |  |
| 43970 | 2026-09-08T14:28:45.345Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:fe3ffbf7aa7a92a6 | passed | 320ea16c14c48429d787f3b83cdb83d782d9b5a934961661f78bf650c411e8a1 | False | 24188 | 0 |
| check:46508d374f5d93c2 | passed | 5cf7c53c65528e0df968036b6227c6a9e5f67edee14ceab3b8ea6cbe14df9616 | False | 1303 | 0 |
| check:9bb70a158b1c7dcc | passed | 0ce13a3f2d58969f7da206541edc8e705431003b53d2b56ba693d142f9ac2c72 | False | 1212 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| fc1fc9b52c1d4d1a9b699bcb9aa26dae | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | c7903cfe89973fa3f2e01437eb926ac0dbe0fdbbb813735e3719620ac354df50 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `35`
- Chain head: `0e578347e0823b6f5388a5aa3490a7565e9eb99c52caa4ed28906655f08c871a`
