# Orchestration Wave 1

- Run: `6a0264ba134f4f8790ce17a52b73df37`
- Wave: `452a5b1cb742493a824566921bb7463a`
- Objective: Natural #10: bind final acceptance to the exact proof-covered source bytes while tolerating unrelated dirty-path drift. Persist a bounded proof-source binding for the affected paths at proof time, validate it at final acceptance before checkpoint, reject proof-covered source drift with a typed error, and preserve existing explicit SHA/adoption/write-lease/PRL guards.
- Objective revision: `1`
- Objective SHA-256: `36a52f2d1ee342be2af31fd198c7e288ff98e4d39b92b7b1ee3c1d9995c22896`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `7bc1caee37107a15e74eb078b52fe314e5fa33ab`
- Worktree fingerprint: `4f99922399e2bd967ff39d4b56b3941e7233c47ea5478dfd345a28860960f289`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 46073 | 2026-09-09T17:41:35.905Z | run_started |  | PREFLIGHT |  |
| 46074 | 2026-09-09T17:41:36.408Z | observation_span_recorded |  |  |  |
| 46075 | 2026-09-09T17:41:36.613Z | solution_shadow_recommended |  |  |  |
| 46076 | 2026-09-09T17:41:42.711Z | observation_span_recorded |  |  |  |
| 46077 | 2026-09-09T17:41:42.915Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 46078 | 2026-09-09T17:43:09.986Z | managed_process_admitted |  |  | owner=default |
| 46079 | 2026-09-09T17:43:10.370Z | managed_process_started |  |  | owner=default |
| 46080 | 2026-09-09T17:43:16.336Z | managed_process_terminal |  |  | owner=default |
| 46081 | 2026-09-09T17:44:12.001Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 46082 | 2026-09-09T17:44:12.160Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 46083 | 2026-09-09T17:44:12.374Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 46084 | 2026-09-09T17:44:12.643Z | state_transition | READY | ROUTED | reason=route_selected |
| 46085 | 2026-09-09T17:44:12.884Z | observation_span_recorded |  |  |  |
| 46086 | 2026-09-09T17:44:13.717Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=b3dc6174ce934209aec9ffa6055e578e |
| 46087 | 2026-09-09T17:44:13.896Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 46088 | 2026-09-09T17:44:14.722Z | patch_surface_observed |  |  |  |
| 46089 | 2026-09-09T17:44:14.956Z | observation_span_recorded |  |  |  |
| 46090 | 2026-09-09T17:44:15.240Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=b3dc6174ce934209aec9ffa6055e578e |
| 46091 | 2026-09-09T17:44:15.356Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 46092 | 2026-09-09T17:44:16.072Z | proof_cache_miss |  |  | reason=cold; stage_id=check:4de340fcb1a4540d; input_fingerprint=fd439fa87d93fd35aa3fb598ad537902a14edcfb4c43aa8143b6406f51a0d0f9 |
| 46093 | 2026-09-09T17:44:16.424Z | managed_process_admitted |  |  | owner=default |
| 46094 | 2026-09-09T17:44:16.632Z | managed_process_started |  |  | owner=default |
| 46095 | 2026-09-09T17:44:27.578Z | managed_process_terminal |  |  | owner=default |
| 46096 | 2026-09-09T17:44:27.802Z | proof_recorded |  |  | stage_id=check:4de340fcb1a4540d; status=passed; cache_hit=False; input_fingerprint=fd439fa87d93fd35aa3fb598ad537902a14edcfb4c43aa8143b6406f51a0d0f9 |
| 46097 | 2026-09-09T17:44:27.943Z | proof_cache_miss |  |  | reason=cold; stage_id=check:ad9831dfeb69808b; input_fingerprint=8b98af446db3c5a1874949fd12c71ce1007cb9a35b7eb9c2f11a80e56a6ff412 |
| 46098 | 2026-09-09T17:44:28.198Z | managed_process_admitted |  |  | owner=default |
| 46099 | 2026-09-09T17:44:28.380Z | managed_process_started |  |  | owner=default |
| 46100 | 2026-09-09T17:44:31.326Z | managed_process_terminal |  |  | owner=default |
| 46101 | 2026-09-09T17:44:31.592Z | proof_recorded |  |  | stage_id=check:ad9831dfeb69808b; status=passed; cache_hit=False; input_fingerprint=8b98af446db3c5a1874949fd12c71ce1007cb9a35b7eb9c2f11a80e56a6ff412 |
| 46102 | 2026-09-09T17:44:31.759Z | proof_cache_miss |  |  | reason=cold; stage_id=check:dedcfe9ce4498444; input_fingerprint=76c4fdf23090e21adbc659fc9f3f01c0461072cb4a95b45b5418cb82a4a4756d |
| 46103 | 2026-09-09T17:44:32.093Z | managed_process_admitted |  |  | owner=default |
| 46104 | 2026-09-09T17:44:32.323Z | managed_process_started |  |  | owner=default |
| 46105 | 2026-09-09T17:45:43.495Z | managed_process_terminal |  |  | owner=default |
| 46106 | 2026-09-09T17:45:43.827Z | proof_recorded |  |  | stage_id=check:dedcfe9ce4498444; status=passed; cache_hit=False; input_fingerprint=76c4fdf23090e21adbc659fc9f3f01c0461072cb4a95b45b5418cb82a4a4756d |
| 46107 | 2026-09-09T17:45:44.044Z | proof_cache_miss |  |  | reason=cold; stage_id=check:e7b88c3d049e3166; input_fingerprint=54547a1a507c9655068af07031424b50d293faf9a9674889e116c737658d35bd |
| 46108 | 2026-09-09T17:45:44.401Z | managed_process_admitted |  |  | owner=default |
| 46109 | 2026-09-09T17:45:44.658Z | managed_process_started |  |  | owner=default |
| 46110 | 2026-09-09T17:45:45.028Z | managed_process_terminal |  |  | owner=default |
| 46111 | 2026-09-09T17:45:45.309Z | proof_recorded |  |  | stage_id=check:e7b88c3d049e3166; status=passed; cache_hit=False; input_fingerprint=54547a1a507c9655068af07031424b50d293faf9a9674889e116c737658d35bd |
| 46112 | 2026-09-09T17:45:46.342Z | observation_span_recorded |  |  |  |
| 46113 | 2026-09-09T17:45:46.543Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 46114 | 2026-09-09T17:46:06.646Z | managed_process_admitted |  |  | owner=default |
| 46115 | 2026-09-09T17:46:07.003Z | managed_process_started |  |  | owner=default |
| 46116 | 2026-09-09T17:46:07.631Z | managed_process_terminal |  |  | owner=default |
| 46117 | 2026-09-09T17:46:59.914Z | quality_outcome_recorded |  |  |  |
| 46118 | 2026-09-09T17:47:00.099Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 46119 | 2026-09-09T17:47:00.371Z | observation_span_recorded |  |  |  |
| 46120 | 2026-09-09T17:47:00.566Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:4de340fcb1a4540d | passed | fd439fa87d93fd35aa3fb598ad537902a14edcfb4c43aa8143b6406f51a0d0f9 | False | 11488 | 0 |
| check:ad9831dfeb69808b | passed | 8b98af446db3c5a1874949fd12c71ce1007cb9a35b7eb9c2f11a80e56a6ff412 | False | 3436 | 0 |
| check:dedcfe9ce4498444 | passed | 76c4fdf23090e21adbc659fc9f3f01c0461072cb4a95b45b5418cb82a4a4756d | False | 71780 | 0 |
| check:e7b88c3d049e3166 | passed | 54547a1a507c9655068af07031424b50d293faf9a9674889e116c737658d35bd | False | 978 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 220eb43e8ebc45e1abc2ee06460bc613 | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | 989743e36bdb832d5f14444b47906ae1f7ae6ebe32e7a8855a6a1c02e924edb8 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `48`
- Chain head: `5485ff134586b08e93d9e8333f9ca3e8f78d16b7db5543b3c55dc26e0b91d96f`
