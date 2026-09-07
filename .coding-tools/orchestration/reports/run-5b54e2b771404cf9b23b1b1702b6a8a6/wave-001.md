# Orchestration Wave 1

- Run: `5b54e2b771404cf9b23b1b1702b6a8a6`
- Wave: `1801212072054bce81cdd03ff7f93032`
- Objective: Read only the exact JSON output contract of reconcile_exact_stale_run.py and its return value from reconcile_exact_stale_run so the Recovery Host validator can be exact. Do not execute reconciliation and do not modify anything.
- Objective revision: `1`
- Objective SHA-256: `d0bf61385f31686881787c2e4adceb610d14355f992392a9e8992f18aac8532f`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `9255f94c9beff33f8c6c53d6745a08968f5a12bb`
- Worktree fingerprint: `d930a6901c3810b35d954108bef4714bf1d28faf541b797c09d5defe6aed8193`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 42948 | 2026-09-07T02:51:43.684Z | run_started |  | PREFLIGHT |  |
| 42949 | 2026-09-07T02:51:44.092Z | observation_span_recorded |  |  |  |
| 42950 | 2026-09-07T02:51:44.582Z | observation_span_recorded |  |  |  |
| 42951 | 2026-09-07T02:51:44.826Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 42952 | 2026-09-07T02:51:45.018Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 42953 | 2026-09-07T02:51:45.198Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 42954 | 2026-09-07T02:51:45.442Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 42955 | 2026-09-07T02:51:45.744Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 42956 | 2026-09-07T02:51:46.049Z | state_transition | READY | ROUTED | reason=route_selected |
| 42957 | 2026-09-07T02:51:46.374Z | observation_span_recorded |  |  |  |
| 42958 | 2026-09-07T02:51:46.844Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=8e66080227fc4ab2b77dd14bc9b58859 |
| 42959 | 2026-09-07T02:51:47.060Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 42960 | 2026-09-07T02:51:47.418Z | observation_span_recorded |  |  |  |
| 42961 | 2026-09-07T02:51:47.751Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=8e66080227fc4ab2b77dd14bc9b58859 |
| 42962 | 2026-09-07T02:51:47.917Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 42963 | 2026-09-07T02:51:48.358Z | proof_cache_miss |  |  | reason=cold; stage_id=check:34fa00eb001678ad; input_fingerprint=954cd4d4a509754c5b0c5c183f4f4eae35ccec5127e49f5874db7fabc943f117 |
| 42964 | 2026-09-07T02:51:48.783Z | managed_process_admitted |  |  | owner=default |
| 42965 | 2026-09-07T02:51:49.099Z | managed_process_started |  |  | owner=default |
| 42966 | 2026-09-07T02:51:49.578Z | managed_process_terminal |  |  | owner=default |
| 42967 | 2026-09-07T02:51:49.942Z | proof_recorded |  |  | stage_id=check:34fa00eb001678ad; status=passed; cache_hit=False; input_fingerprint=954cd4d4a509754c5b0c5c183f4f4eae35ccec5127e49f5874db7fabc943f117 |
| 42968 | 2026-09-07T02:51:50.131Z | observation_span_recorded |  |  |  |
| 42969 | 2026-09-07T02:51:50.352Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 42970 | 2026-09-07T02:52:10.262Z | quality_outcome_recorded |  |  |  |
| 42971 | 2026-09-07T02:52:10.476Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 42972 | 2026-09-07T02:52:10.775Z | observation_span_recorded |  |  |  |
| 42973 | 2026-09-07T02:52:11.086Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:34fa00eb001678ad | passed | 954cd4d4a509754c5b0c5c183f4f4eae35ccec5127e49f5874db7fabc943f117 | False | 1222 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 6c0cdd8fea4a41c6915ae77bf0fec8b1 | accepted | 9255f94c9beff33f8c6c53d6745a08968f5a12bb | b9e4a7bd455698528661adff1005bcca191c206c845eb1f0c85a4c574688a33c | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `26`
- Chain head: `5edbb3b8b02850c2dd4d9259495b09dca56e0298b82b6b9d3e41c409a0f1a162`
