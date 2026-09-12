# Orchestration Wave 1

- Run: `1a696a5607aa42b1a0272a10a72b7178`
- Wave: `3ba6e77ba7144cc19accf1e7ed3e8a64`
- Objective: Replace the Windows kill-on-close detached activation child with a capability-gated Recovery Supervisor-owned durable worker, prove single-launch and credential isolation, and prepare a new trusted recovery_host bootstrap without replaying the expired operation.
- Objective revision: `1`
- Objective SHA-256: `538cff1f2d442f83507d13b5db28b166b844d1b01920c9d4663f5a2359d1f456`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `7bc1caee37107a15e74eb078b52fe314e5fa33ab`
- Worktree fingerprint: `3b5e1fffb56ec8322e1e6786aa64c03223eaa3ed7c446b20358e523530c7cd89`
- Contract fingerprint: `85c452de1bdba5f568643637bd82c1d8edb2a0e610d2ad15afb1a31495c6c3af`
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 43896 | 2026-09-08T14:14:23.434Z | run_started |  | PREFLIGHT |  |
| 43897 | 2026-09-08T14:14:23.925Z | observation_span_recorded |  |  |  |
| 43898 | 2026-09-08T14:14:24.215Z | solution_shadow_recommended |  |  |  |
| 43899 | 2026-09-08T14:14:24.397Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 43900 | 2026-09-08T14:14:24.605Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 43901 | 2026-09-08T14:14:24.773Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 43902 | 2026-09-08T14:14:24.946Z | state_transition | READY | ROUTED | reason=route_selected |
| 43903 | 2026-09-08T14:14:25.414Z | observation_span_recorded |  |  |  |
| 43904 | 2026-09-08T14:14:26.117Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=52622237f8614f06b917e7264d86c37f |
| 43905 | 2026-09-08T14:14:26.265Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 43906 | 2026-09-08T14:14:26.943Z | existing_file_adoption_observed |  |  |  |
| 43907 | 2026-09-08T14:14:27.109Z | observation_span_recorded |  |  |  |
| 43908 | 2026-09-08T14:14:27.376Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=52622237f8614f06b917e7264d86c37f |
| 43909 | 2026-09-08T14:14:27.518Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 43910 | 2026-09-08T14:14:28.166Z | proof_cache_miss |  |  | reason=cold; stage_id=check:fac1bdd7a8e41556; input_fingerprint=ebf64cda5ec259729e7302928296d9fe7c156e0b4f79fbe9b2f2d149144508d8 |
| 43911 | 2026-09-08T14:14:28.452Z | managed_process_admitted |  |  | owner=default |
| 43912 | 2026-09-08T14:14:28.726Z | managed_process_started |  |  | owner=default |
| 43913 | 2026-09-08T14:14:44.364Z | managed_process_terminal |  |  | owner=default |
| 43914 | 2026-09-08T14:14:44.686Z | proof_recorded |  |  | stage_id=check:fac1bdd7a8e41556; status=passed; cache_hit=False; input_fingerprint=ebf64cda5ec259729e7302928296d9fe7c156e0b4f79fbe9b2f2d149144508d8 |
| 43915 | 2026-09-08T14:14:44.888Z | proof_cache_miss |  |  | reason=cold; stage_id=check:7a28619f5e0fb586; input_fingerprint=1888cf40cd125c8c298931bfd70b8ee2fdd2b1576657eb4a18ea04cabcf1caca |
| 43916 | 2026-09-08T14:14:45.273Z | managed_process_admitted |  |  | owner=default |
| 43917 | 2026-09-08T14:14:45.599Z | managed_process_started |  |  | owner=default |
| 43918 | 2026-09-08T14:14:51.281Z | managed_process_terminal |  |  | owner=default |
| 43919 | 2026-09-08T14:14:51.595Z | proof_recorded |  |  | stage_id=check:7a28619f5e0fb586; status=passed; cache_hit=False; input_fingerprint=1888cf40cd125c8c298931bfd70b8ee2fdd2b1576657eb4a18ea04cabcf1caca |
| 43920 | 2026-09-08T14:14:51.762Z | proof_cache_miss |  |  | reason=cold; stage_id=check:5b28da7b52290f53; input_fingerprint=8b92dcab90ee7d0c325c202c3aaa79ba78df44b51dd482785f44262f609fc02e |
| 43921 | 2026-09-08T14:14:52.102Z | managed_process_admitted |  |  | owner=default |
| 43922 | 2026-09-08T14:14:52.348Z | managed_process_started |  |  | owner=default |
| 43923 | 2026-09-08T14:14:56.599Z | managed_process_terminal |  |  | owner=default |
| 43924 | 2026-09-08T14:14:56.940Z | proof_recorded |  |  | stage_id=check:5b28da7b52290f53; status=passed; cache_hit=False; input_fingerprint=8b92dcab90ee7d0c325c202c3aaa79ba78df44b51dd482785f44262f609fc02e |
| 43925 | 2026-09-08T14:14:57.121Z | proof_cache_miss |  |  | reason=cold; stage_id=check:d27f10e61eb0c25a; input_fingerprint=2245f6408b9f7ab02ae33b64fe6e907dd0e39d5837eeb3bf5897b8b2d9e8dbae |
| 43926 | 2026-09-08T14:14:57.523Z | managed_process_admitted |  |  | owner=default |
| 43927 | 2026-09-08T14:14:57.785Z | managed_process_started |  |  | owner=default |
| 43928 | 2026-09-08T14:14:58.202Z | managed_process_terminal |  |  | owner=default |
| 43929 | 2026-09-08T14:14:58.522Z | proof_recorded |  |  | stage_id=check:d27f10e61eb0c25a; status=passed; cache_hit=False; input_fingerprint=2245f6408b9f7ab02ae33b64fe6e907dd0e39d5837eeb3bf5897b8b2d9e8dbae |
| 43930 | 2026-09-08T14:14:58.745Z | observation_span_recorded |  |  |  |
| 43931 | 2026-09-08T14:14:58.914Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 43932 | 2026-09-08T14:15:59.851Z | quality_outcome_recorded |  |  |  |
| 43933 | 2026-09-08T14:16:00.058Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 43934 | 2026-09-08T14:16:00.283Z | observation_span_recorded |  |  |  |
| 43935 | 2026-09-08T14:16:00.523Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:fac1bdd7a8e41556 | passed | ebf64cda5ec259729e7302928296d9fe7c156e0b4f79fbe9b2f2d149144508d8 | False | 16248 | 0 |
| check:7a28619f5e0fb586 | passed | 1888cf40cd125c8c298931bfd70b8ee2fdd2b1576657eb4a18ea04cabcf1caca | False | 6380 | 0 |
| check:5b28da7b52290f53 | passed | 8b92dcab90ee7d0c325c202c3aaa79ba78df44b51dd482785f44262f609fc02e | False | 4862 | 0 |
| check:d27f10e61eb0c25a | passed | 2245f6408b9f7ab02ae33b64fe6e907dd0e39d5837eeb3bf5897b8b2d9e8dbae | False | 1013 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| f92afffa5e89407286906e1f1ef82bdf | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | 112120bef0a199264607f32693a088bb7007e5ff97b647b49c54ac7d2a7836da | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `40`
- Chain head: `818a9951abb668c40139413613dc2f5147a42f0549544ba1cb637bbdf84ffea5`
