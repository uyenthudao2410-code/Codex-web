# Orchestration Wave 1

- Run: `a34ff1344075431584e88c43f938f260`
- Wave: `76537433b1a54ee496858da292ed2d53`
- Objective: Read only the exact implementation boundaries needed to execute the final repair safely: locate every production caller of exact stale-run reconciliation, identify whether Recovery Host/full-clean activation invokes it automatically or exposes a maintenance hook, and inspect the task_control restart_runtime confirmation/restart handoff contract. Do not mutate source, Git, ledger, runtime, machine state, or services.
- Objective revision: `1`
- Objective SHA-256: `7d0edfbd93be8c46313a87c5fad6847bda0c1c74d60c2cdc8a5b24f150693bfd`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `9255f94c9beff33f8c6c53d6745a08968f5a12bb`
- Worktree fingerprint: `8cade6d95f0b3eafb1a7d2f3099aefff7284debe47b43794aa68bde3e1818ffd`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 42553 | 2026-09-07T02:26:38.447Z | run_started |  | PREFLIGHT |  |
| 42554 | 2026-09-07T02:26:38.842Z | observation_span_recorded |  |  |  |
| 42555 | 2026-09-07T02:26:39.253Z | observation_span_recorded |  |  |  |
| 42556 | 2026-09-07T02:26:39.399Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 42557 | 2026-09-07T02:26:39.560Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 42558 | 2026-09-07T02:26:39.791Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 42559 | 2026-09-07T02:26:39.948Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 42560 | 2026-09-07T02:26:40.124Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 42561 | 2026-09-07T02:26:40.318Z | state_transition | READY | ROUTED | reason=route_selected |
| 42562 | 2026-09-07T02:26:40.502Z | observation_span_recorded |  |  |  |
| 42563 | 2026-09-07T02:26:40.967Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=5adbefef64c24e5683f3b2836995d25e |
| 42564 | 2026-09-07T02:26:41.122Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 42565 | 2026-09-07T02:26:41.503Z | observation_span_recorded |  |  |  |
| 42566 | 2026-09-07T02:26:41.740Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=5adbefef64c24e5683f3b2836995d25e |
| 42567 | 2026-09-07T02:26:41.875Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 42568 | 2026-09-07T02:26:42.282Z | proof_cache_miss |  |  | reason=cold; stage_id=check:84be68fac14adee9; input_fingerprint=25e644cd175579834cfdcf3db75d805f2d622fe2e1a993d45c7f668c16c106ee |
| 42569 | 2026-09-07T02:26:42.620Z | managed_process_admitted |  |  | owner=default |
| 42570 | 2026-09-07T02:26:42.863Z | managed_process_started |  |  | owner=default |
| 42571 | 2026-09-07T02:26:43.220Z | managed_process_terminal |  |  | owner=default |
| 42572 | 2026-09-07T02:26:43.520Z | proof_recorded |  |  | stage_id=check:84be68fac14adee9; status=passed; cache_hit=False; input_fingerprint=25e644cd175579834cfdcf3db75d805f2d622fe2e1a993d45c7f668c16c106ee |
| 42573 | 2026-09-07T02:26:43.660Z | proof_cache_miss |  |  | reason=cold; stage_id=check:f31c868f977174a0; input_fingerprint=0d99d1197d9d6ddb7c375e88f77e4e70cf52e6073766408557ed628d9563c6d6 |
| 42574 | 2026-09-07T02:26:43.933Z | managed_process_admitted |  |  | owner=default |
| 42575 | 2026-09-07T02:26:44.196Z | managed_process_started |  |  | owner=default |
| 42576 | 2026-09-07T02:26:44.663Z | managed_process_terminal |  |  | owner=default |
| 42577 | 2026-09-07T02:26:44.920Z | proof_recorded |  |  | stage_id=check:f31c868f977174a0; status=failed; cache_hit=False; input_fingerprint=0d99d1197d9d6ddb7c375e88f77e4e70cf52e6073766408557ed628d9563c6d6 |
| 42578 | 2026-09-07T02:26:45.070Z | observation_span_recorded |  |  |  |
| 42579 | 2026-09-07T02:26:45.229Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 42580 | 2026-09-07T02:26:45.364Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 42581 | 2026-09-07T02:26:45.522Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:84be68fac14adee9 | passed | 25e644cd175579834cfdcf3db75d805f2d622fe2e1a993d45c7f668c16c106ee | False | 913 | 0 |
| check:f31c868f977174a0 | failed | 0d99d1197d9d6ddb7c375e88f77e4e70cf52e6073766408557ed628d9563c6d6 | False | 1030 | 2 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `60`
- Chain head: `2d7928561e47924d779d575198f32af0697cfa69125580d53c6168f0a86e5760`
