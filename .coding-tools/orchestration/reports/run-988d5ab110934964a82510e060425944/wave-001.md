# Orchestration Wave 1

- Run: `988d5ab110934964a82510e060425944`
- Wave: `5df31513864c4a67b4aea10c014f9729`
- Objective: Checkpoint the prepared-workflow binding fix.
- Objective revision: `1`
- Objective SHA-256: `74fb87ebeeea913bb69c78ef25b434100ed836fa4afb20991aaca6c4127b8961`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `7bc1caee37107a15e74eb078b52fe314e5fa33ab`
- Worktree fingerprint: `156bf65c73eb3691eaaba38c1eabb8b7ae2d93068d657884f7a88633033e1161`
- Contract fingerprint: `09e1ca748a1319b814734967959d667aa111d70c1e3720353e3c83b1da22ccb9`
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 44771 | 2026-09-08T23:06:55.778Z | run_started |  | PREFLIGHT |  |
| 44772 | 2026-09-08T23:06:56.252Z | observation_span_recorded |  |  |  |
| 44773 | 2026-09-08T23:09:11.977Z | solution_shadow_recommended |  |  |  |
| 44774 | 2026-09-08T23:09:12.178Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 44775 | 2026-09-08T23:09:12.340Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 44776 | 2026-09-08T23:09:12.557Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 44777 | 2026-09-08T23:09:12.743Z | state_transition | READY | ROUTED | reason=route_selected |
| 44778 | 2026-09-08T23:09:13.025Z | observation_span_recorded |  |  |  |
| 44779 | 2026-09-08T23:09:14.110Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=91c0346085304f3b982a55374e90835f |
| 44780 | 2026-09-08T23:09:14.284Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 44781 | 2026-09-08T23:09:15.281Z | existing_file_adoption_observed |  |  |  |
| 44782 | 2026-09-08T23:09:15.505Z | observation_span_recorded |  |  |  |
| 44783 | 2026-09-08T23:09:15.812Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=91c0346085304f3b982a55374e90835f |
| 44784 | 2026-09-08T23:09:15.976Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 44785 | 2026-09-08T23:09:16.989Z | proof_cache_miss |  |  | reason=cold; stage_id=check:b29c48234414d477; input_fingerprint=644dac2a04b205103e74d8930a3ff33df975a18b8c4c253b1e28fc67a4c14a96 |
| 44786 | 2026-09-08T23:09:17.417Z | managed_process_admitted |  |  | owner=default |
| 44787 | 2026-09-08T23:09:17.749Z | managed_process_started |  |  | owner=default |
| 44788 | 2026-09-08T23:09:51.072Z | managed_process_terminal |  |  | owner=default |
| 44789 | 2026-09-08T23:09:51.371Z | proof_recorded |  |  | stage_id=check:b29c48234414d477; status=passed; cache_hit=False; input_fingerprint=644dac2a04b205103e74d8930a3ff33df975a18b8c4c253b1e28fc67a4c14a96 |
| 44790 | 2026-09-08T23:09:51.920Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:80a1a46bd01d26a3; input_fingerprint=879232d7dfd010ea9ab5b5e24b988f851d6c54f9273d3265395c8d8988fcf6ff |
| 44791 | 2026-09-08T23:09:52.401Z | managed_process_admitted |  |  | owner=default |
| 44792 | 2026-09-08T23:09:53.416Z | managed_process_started |  |  | owner=default |
| 44793 | 2026-09-08T23:09:54.578Z | managed_process_terminal |  |  | owner=default |
| 44794 | 2026-09-08T23:09:54.993Z | proof_recorded |  |  | stage_id=check:80a1a46bd01d26a3; status=passed; cache_hit=False; input_fingerprint=879232d7dfd010ea9ab5b5e24b988f851d6c54f9273d3265395c8d8988fcf6ff |
| 44795 | 2026-09-08T23:09:55.244Z | observation_span_recorded |  |  |  |
| 44796 | 2026-09-08T23:09:55.432Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 44797 | 2026-09-08T23:10:30.560Z | quality_outcome_recorded |  |  |  |
| 44798 | 2026-09-08T23:10:30.755Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 44799 | 2026-09-08T23:10:31.147Z | observation_span_recorded |  |  |  |
| 44800 | 2026-09-08T23:10:31.528Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:b29c48234414d477 | passed | 644dac2a04b205103e74d8930a3ff33df975a18b8c4c253b1e28fc67a4c14a96 | False | 34077 | 0 |
| check:80a1a46bd01d26a3 | passed | 879232d7dfd010ea9ab5b5e24b988f851d6c54f9273d3265395c8d8988fcf6ff | False | 2609 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| e3a13fe791ca41b3bc811e0455ea73e3 | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | 57f29e1b9c5c1779bd7819ee63682e2a93abc58dd1c8298805e7d22db703289e | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `30`
- Chain head: `179e98160079240d2a01ebc534baef52cfad311d7332f0981680f7a49af89040`
