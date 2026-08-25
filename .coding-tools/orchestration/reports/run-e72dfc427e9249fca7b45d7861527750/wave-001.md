# Orchestration Wave 1

- Run: `e72dfc427e9249fca7b45d7861527750`
- Wave: `9b07693a2ad84987b166c1dfb41788f4`
- Objective: Classify the focused verification failures and capture independent read-only proof of activation/runtime and current live Recovery Host/UI revision state. Do not modify source or runtime state.
- Objective revision: `1`
- Objective SHA-256: `ebfa9552c5a564e3ce84908901c432a9d0d91eeaba89c8c83a34bc996bf43f42`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `026f79b3ab5997cb15f38a3b41769da6a79d790b`
- Worktree fingerprint: `8ef276970782a7d2e21bfe7a2ea401e99a611dc59e41dc6aa27ae498fe1fb322`
- Contract fingerprint: ``
- Status: **active**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 29360 | 2026-08-25T09:08:24.914Z | run_started |  | PREFLIGHT |  |
| 29361 | 2026-08-25T09:08:25.130Z | observation_span_recorded |  |  |  |
| 29362 | 2026-08-25T09:08:25.288Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 29363 | 2026-08-25T09:08:25.421Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 29364 | 2026-08-25T09:08:25.547Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 29365 | 2026-08-25T09:08:25.704Z | state_transition | READY | ROUTED | reason=route_selected |
| 29366 | 2026-08-25T09:08:25.866Z | observation_span_recorded |  |  |  |
| 29367 | 2026-08-25T09:08:26.659Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=469c8e9f6f5b4c699e3849f849b360f6 |
| 29368 | 2026-08-25T09:08:26.789Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 29369 | 2026-08-25T09:08:27.586Z | observation_span_recorded |  |  |  |
| 29370 | 2026-08-25T09:08:27.829Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=469c8e9f6f5b4c699e3849f849b360f6 |
| 29371 | 2026-08-25T09:08:28.004Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 29372 | 2026-08-25T09:08:28.728Z | proof_cache_miss |  |  | reason=cold; stage_id=check:f91abf21fea46bcd; input_fingerprint=265d4edf28295a31842983617a69cdcc44dca7f39a63066b21e65f6c717e17cb |
| 29373 | 2026-08-25T09:08:28.970Z | managed_process_admitted |  |  | owner=default |
| 29374 | 2026-08-25T09:08:29.229Z | managed_process_started |  |  | owner=default |
| 29375 | 2026-08-25T09:08:29.612Z | managed_process_terminal |  |  | owner=default |
| 29376 | 2026-08-25T09:08:29.871Z | proof_recorded |  |  | stage_id=check:f91abf21fea46bcd; status=passed; cache_hit=False; input_fingerprint=265d4edf28295a31842983617a69cdcc44dca7f39a63066b21e65f6c717e17cb |
| 29377 | 2026-08-25T09:08:30.010Z | proof_cache_miss |  |  | reason=cold; stage_id=check:5895b0eb8e5499f7; input_fingerprint=b7320651d7243915d5de3058063ccf377cb67ace26e7aea3ff389f84349aa6f5 |
| 29378 | 2026-08-25T09:08:30.318Z | managed_process_admitted |  |  | owner=default |
| 29379 | 2026-08-25T09:08:30.562Z | managed_process_started |  |  | owner=default |
| 29380 | 2026-08-25T09:08:31.270Z | managed_process_terminal |  |  | owner=default |
| 29381 | 2026-08-25T09:08:31.521Z | proof_recorded |  |  | stage_id=check:5895b0eb8e5499f7; status=failed; cache_hit=False; input_fingerprint=b7320651d7243915d5de3058063ccf377cb67ace26e7aea3ff389f84349aa6f5 |
| 29382 | 2026-08-25T09:08:31.668Z | observation_span_recorded |  |  |  |
| 29383 | 2026-08-25T09:08:31.830Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 29384 | 2026-08-25T09:08:31.969Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 29385 | 2026-08-25T09:08:32.139Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:f91abf21fea46bcd | passed | 265d4edf28295a31842983617a69cdcc44dca7f39a63066b21e65f6c717e17cb | False | 877 | 0 |
| check:5895b0eb8e5499f7 | failed | b7320651d7243915d5de3058063ccf377cb67ace26e7aea3ff389f84349aa6f5 | False | 1225 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `26`
- Chain head: `74a399d09aa5193110e6cda0737b92b2d4f0e7e4a470dc14316d33fa06736f02`
