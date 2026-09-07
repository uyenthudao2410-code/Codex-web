# Orchestration Wave 1

- Run: `1b2646cf96444590a6e70e138742d97c`
- Wave: `1346a2aed12648a2976ed22e8f850163`
- Objective: Fix the Recovery Host restart-ticket consumption bug so an explicit task_control restart_runtime ticket is serviced under an ordinary healthy READY activation epoch as well as a blocked READY-adoption epoch, while still never consuming it during any non-READY activation transaction. Add a focused regression test. Preserve all unrelated dirty work and do not commit/push/release/deploy.
- Objective revision: `1`
- Objective SHA-256: `9501de5d227264f157a09809ba88b347ca9e40ddd66e7f6773565e23c54d76ce`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `9255f94c9beff33f8c6c53d6745a08968f5a12bb`
- Worktree fingerprint: `887a20b6c043370d054dc0baa696b593400ed9c75ea808a3ead6159f108069db`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 43079 | 2026-09-07T03:32:44.311Z | run_started |  | PREFLIGHT |  |
| 43080 | 2026-09-07T03:32:45.266Z | observation_span_recorded |  |  |  |
| 43081 | 2026-09-07T03:32:45.796Z | solution_shadow_recommended |  |  |  |
| 43082 | 2026-09-07T03:32:46.738Z | observation_span_recorded |  |  |  |
| 43083 | 2026-09-07T03:32:47.065Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 43084 | 2026-09-07T03:32:47.367Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 43085 | 2026-09-07T03:32:47.689Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 43086 | 2026-09-07T03:32:47.998Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 43087 | 2026-09-07T03:32:48.326Z | state_transition | READY | ROUTED | reason=route_selected |
| 43088 | 2026-09-07T03:32:48.686Z | observation_span_recorded |  |  |  |
| 43089 | 2026-09-07T03:32:49.769Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=3853703eb40049da8d4daa1cf333d3d4 |
| 43090 | 2026-09-07T03:32:50.039Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 43091 | 2026-09-07T03:32:50.985Z | patch_surface_observed |  |  |  |
| 43092 | 2026-09-07T03:32:51.330Z | observation_span_recorded |  |  |  |
| 43093 | 2026-09-07T03:32:51.930Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=3853703eb40049da8d4daa1cf333d3d4 |
| 43094 | 2026-09-07T03:32:52.190Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 43095 | 2026-09-07T03:32:52.741Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:23bff18b9aaa12d4; input_fingerprint=27945ff0b4b91a969347f021f025a7d69a394dd44ca3bc17a017d485dbf11e60 |
| 43096 | 2026-09-07T03:32:53.377Z | managed_process_admitted |  |  | owner=default |
| 43097 | 2026-09-07T03:32:54.022Z | managed_process_started |  |  | owner=default |
| 43098 | 2026-09-07T03:32:54.898Z | managed_process_terminal |  |  | owner=default |
| 43099 | 2026-09-07T03:32:55.553Z | proof_recorded |  |  | stage_id=check:23bff18b9aaa12d4; status=passed; cache_hit=False; input_fingerprint=27945ff0b4b91a969347f021f025a7d69a394dd44ca3bc17a017d485dbf11e60 |
| 43100 | 2026-09-07T03:32:55.985Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=b59739e2956ff68d207a65ab7000dbb43323d082f69f39f34338f55d05237340 |
| 43101 | 2026-09-07T03:32:56.702Z | managed_process_admitted |  |  | owner=default |
| 43102 | 2026-09-07T03:32:57.368Z | managed_process_started |  |  | owner=default |
| 43103 | 2026-09-07T03:33:03.560Z | managed_process_terminal |  |  | owner=default |
| 43104 | 2026-09-07T03:33:31.938Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=b59739e2956ff68d207a65ab7000dbb43323d082f69f39f34338f55d05237340 |
| 43105 | 2026-09-07T03:33:32.791Z | observation_span_recorded |  |  |  |
| 43106 | 2026-09-07T03:33:33.111Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 43107 | 2026-09-07T03:35:44.816Z | managed_process_admitted |  |  | owner=default |
| 43108 | 2026-09-07T03:35:46.373Z | managed_process_started |  |  | owner=default |
| 43109 | 2026-09-07T03:35:47.738Z | managed_process_terminal |  |  | owner=default |
| 43110 | 2026-09-07T03:36:01.222Z | quality_outcome_recorded |  |  |  |
| 43111 | 2026-09-07T03:36:02.227Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 43112 | 2026-09-07T03:36:03.196Z | observation_span_recorded |  |  |  |
| 43113 | 2026-09-07T03:36:03.982Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:23bff18b9aaa12d4 | passed | 27945ff0b4b91a969347f021f025a7d69a394dd44ca3bc17a017d485dbf11e60 | False | 2173 | 0 |
| verify:tests | passed | b59739e2956ff68d207a65ab7000dbb43323d082f69f39f34338f55d05237340 | False | 34844 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 00ececc1c172430ea5e271fc15ca065c | accepted | 9255f94c9beff33f8c6c53d6745a08968f5a12bb | d0e1632e7402092b1062ba8fe1a1dd5ae806fd12d2426d78e618da29a9030ecd | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `35`
- Chain head: `f28c4e8be6fc351c6d88ad9622ed3a134bcd87f863644f8ed6f92a18403fb7da`
