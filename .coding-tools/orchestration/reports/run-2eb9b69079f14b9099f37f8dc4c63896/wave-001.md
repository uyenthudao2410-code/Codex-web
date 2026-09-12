# Orchestration Wave 1

- Run: `2eb9b69079f14b9099f37f8dc4c63896`
- Wave: `6c951632060443a8a8bd2a1061f680f2`
- Objective: Natural #17: extend only P2-local request_contract_correction to include EXISTING_FILE_ADOPTION_PREEXISTING_DIRTY_REQUIRED, update focused regression expectations from 2/7 to 3/7 mapped, and preserve global repair-cause/runtime semantics.
- Objective revision: `1`
- Objective SHA-256: `1da93b92432a89aa48cafbf4bf225ae09acea2d3c75d0af0c03f3b5ec5824ee6`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `7bc1caee37107a15e74eb078b52fe314e5fa33ab`
- Worktree fingerprint: `a6ad6c0bb96181797b8ab684ae1eb9acec20e93b7e25f5bf3f468fc1bd9d775f`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 46854 | 2026-09-10T06:34:37.274Z | run_started |  | PREFLIGHT |  |
| 46855 | 2026-09-10T06:34:37.928Z | observation_span_recorded |  |  |  |
| 46856 | 2026-09-10T06:34:43.660Z | observation_span_recorded |  |  |  |
| 46857 | 2026-09-10T06:34:43.842Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 46858 | 2026-09-10T06:35:07.382Z | solution_shadow_recommended |  |  |  |
| 46859 | 2026-09-10T06:35:07.590Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 46860 | 2026-09-10T06:35:07.767Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 46861 | 2026-09-10T06:35:07.981Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 46862 | 2026-09-10T06:35:08.169Z | state_transition | READY | ROUTED | reason=route_selected |
| 46863 | 2026-09-10T06:35:08.395Z | observation_span_recorded |  |  |  |
| 46864 | 2026-09-10T06:35:09.303Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=60a26aa8b5fc48cc9338531fbaca050d |
| 46865 | 2026-09-10T06:35:09.458Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 46866 | 2026-09-10T06:35:10.379Z | patch_surface_observed |  |  |  |
| 46867 | 2026-09-10T06:35:10.562Z | observation_span_recorded |  |  |  |
| 46868 | 2026-09-10T06:35:10.851Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=60a26aa8b5fc48cc9338531fbaca050d |
| 46869 | 2026-09-10T06:35:11.025Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 46870 | 2026-09-10T06:35:12.185Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:ed7873ee22bf15b5; input_fingerprint=5e881e9a336fd3f6d5984ead4ccdaed810f2bccfdaacdc99641c064ff81cc92a |
| 46871 | 2026-09-10T06:35:12.491Z | managed_process_admitted |  |  | owner=default |
| 46872 | 2026-09-10T06:35:12.775Z | managed_process_started |  |  | owner=default |
| 46873 | 2026-09-10T06:35:16.204Z | managed_process_reconciled |  |  | reason=root_process_gone; owner=default |
| 46874 | 2026-09-10T06:35:16.583Z | proof_recorded |  |  | stage_id=check:ed7873ee22bf15b5; status=passed; cache_hit=False; input_fingerprint=5e881e9a336fd3f6d5984ead4ccdaed810f2bccfdaacdc99641c064ff81cc92a |
| 46875 | 2026-09-10T06:35:16.769Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:1e606d62e02d0f68; input_fingerprint=fc7d2c744eabb2062310d76d73302ee547d4362903153d471eeb8051000c0b59 |
| 46876 | 2026-09-10T06:35:17.102Z | managed_process_admitted |  |  | owner=default |
| 46877 | 2026-09-10T06:35:17.392Z | managed_process_started |  |  | owner=default |
| 46878 | 2026-09-10T06:35:34.752Z | managed_process_terminal |  |  | owner=default |
| 46879 | 2026-09-10T06:35:35.066Z | proof_recorded |  |  | stage_id=check:1e606d62e02d0f68; status=passed; cache_hit=False; input_fingerprint=fc7d2c744eabb2062310d76d73302ee547d4362903153d471eeb8051000c0b59 |
| 46880 | 2026-09-10T06:35:35.240Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:6d884becdef27c18; input_fingerprint=5f9c838753c87406cb28c612a9a93e98c66a699e4659d3b91c2f02a97bf5c4bf |
| 46881 | 2026-09-10T06:35:35.583Z | managed_process_admitted |  |  | owner=default |
| 46882 | 2026-09-10T06:35:35.858Z | managed_process_started |  |  | owner=default |
| 46883 | 2026-09-10T06:35:38.645Z | managed_process_terminal |  |  | owner=default |
| 46884 | 2026-09-10T06:35:39.008Z | proof_recorded |  |  | stage_id=check:6d884becdef27c18; status=passed; cache_hit=False; input_fingerprint=5f9c838753c87406cb28c612a9a93e98c66a699e4659d3b91c2f02a97bf5c4bf |
| 46885 | 2026-09-10T06:35:39.206Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:20af4e8e69d7c88b; input_fingerprint=4ea55813eb49d32187777711b8c54feffb98ce2c70d6000195ff621f4c2de167 |
| 46886 | 2026-09-10T06:35:39.576Z | managed_process_admitted |  |  | owner=default |
| 46887 | 2026-09-10T06:35:39.907Z | managed_process_started |  |  | owner=default |
| 46888 | 2026-09-10T06:35:40.358Z | managed_process_terminal |  |  | owner=default |
| 46889 | 2026-09-10T06:35:40.750Z | proof_recorded |  |  | stage_id=check:20af4e8e69d7c88b; status=passed; cache_hit=False; input_fingerprint=4ea55813eb49d32187777711b8c54feffb98ce2c70d6000195ff621f4c2de167 |
| 46890 | 2026-09-10T06:35:41.739Z | observation_span_recorded |  |  |  |
| 46891 | 2026-09-10T06:35:41.925Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 46892 | 2026-09-10T06:44:41.726Z | managed_process_admitted |  |  | owner=default |
| 46893 | 2026-09-10T06:44:42.057Z | managed_process_started |  |  | owner=default |
| 46894 | 2026-09-10T06:44:44.134Z | managed_process_terminal |  |  | owner=default |
| 46895 | 2026-09-10T06:45:44.686Z | quality_outcome_recorded |  |  |  |
| 46896 | 2026-09-10T06:45:44.865Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 46897 | 2026-09-10T06:45:45.162Z | observation_span_recorded |  |  |  |
| 46898 | 2026-09-10T06:45:45.659Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:ed7873ee22bf15b5 | passed | 5e881e9a336fd3f6d5984ead4ccdaed810f2bccfdaacdc99641c064ff81cc92a | False | 3880 | 0 |
| check:1e606d62e02d0f68 | passed | fc7d2c744eabb2062310d76d73302ee547d4362903153d471eeb8051000c0b59 | False | 17997 | 0 |
| check:6d884becdef27c18 | passed | 5f9c838753c87406cb28c612a9a93e98c66a699e4659d3b91c2f02a97bf5c4bf | False | 3466 | 0 |
| check:20af4e8e69d7c88b | passed | 4ea55813eb49d32187777711b8c54feffb98ce2c70d6000195ff621f4c2de167 | False | 1193 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 997baceb5f1447e2b2c8307230cb1424 | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | b7c741cc15cd4dbf7a8e321767008d427a442c6da5f5b2d16b54a6d4c2a734ae | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `45`
- Chain head: `7b62dd4b58e5e80dffd58d95499a9b50805722efbd53e8425e8fb603e477d7af`
