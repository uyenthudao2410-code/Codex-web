# Orchestration Wave 1

- Run: `2a46502e2e664a87a90e68c6022b297e`
- Wave: `5b32ac0e27c740d2b2ec95c6d0fd76ca`
- Objective: DASHBOARD-MEASUREMENT-01: correct the current dashboard measurement projection and UI so missing or invalid by_model evidence never becomes observed measured zero. Preserve known input/output when only cached tokens are unknown, distinguish unavailable versus partial breakdown from complete genuine zero, clear stale/in-flight donut totals when breakdown becomes unavailable, and add behavioral VM coverage through the actual projector/render consumer. Write only renderer/dashboard.js and tests/dashboard-measurement-behavior.test.js; preserve all unrelated WIP.
- Objective revision: `1`
- Objective SHA-256: `a46bc26fd6e4e7241617cec519dd344e8143bc3b7593030ab5bb729b63534d45`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `8697ace8204e7e3da55d250d4a52d9b2b930116c`
- Worktree fingerprint: `b55c6a37313af06601e1aacdefe0c1d027719993459209b4cd519a8fabfe0655`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 40416 | 2026-09-05T09:20:59.643Z | run_started |  | PREFLIGHT |  |
| 40417 | 2026-09-05T09:20:59.940Z | observation_span_recorded |  |  |  |
| 40418 | 2026-09-05T09:21:00.201Z | solution_shadow_recommended |  |  |  |
| 40419 | 2026-09-05T09:21:00.398Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 40420 | 2026-09-05T09:21:00.608Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 40421 | 2026-09-05T09:21:00.834Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 40422 | 2026-09-05T09:21:01.041Z | state_transition | READY | ROUTED | reason=route_selected |
| 40423 | 2026-09-05T09:21:01.257Z | observation_span_recorded |  |  |  |
| 40424 | 2026-09-05T09:21:01.858Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=77618bfafbff4b3cb2b7704f391497c9 |
| 40425 | 2026-09-05T09:21:02.038Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 40426 | 2026-09-05T09:21:02.652Z | patch_surface_observed |  |  |  |
| 40427 | 2026-09-05T09:21:02.829Z | observation_span_recorded |  |  |  |
| 40428 | 2026-09-05T09:21:03.075Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=77618bfafbff4b3cb2b7704f391497c9 |
| 40429 | 2026-09-05T09:21:03.279Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 40430 | 2026-09-05T09:21:03.745Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=dc61dab36ec224f8f242aad58b8030bb1b6a3cc5fafc9e10179f160ec7ad4ca3 |
| 40431 | 2026-09-05T09:21:04.090Z | managed_process_admitted |  |  | owner=default |
| 40432 | 2026-09-05T09:21:04.398Z | managed_process_started |  |  | owner=default |
| 40433 | 2026-09-05T09:21:04.940Z | managed_process_terminal |  |  | owner=default |
| 40434 | 2026-09-05T09:21:05.367Z | proof_recorded |  |  | stage_id=verify:tests; status=failed; cache_hit=False; input_fingerprint=dc61dab36ec224f8f242aad58b8030bb1b6a3cc5fafc9e10179f160ec7ad4ca3 |
| 40435 | 2026-09-05T09:21:05.564Z | observation_span_recorded |  |  |  |
| 40436 | 2026-09-05T09:21:05.812Z | failure_observed | PROVING | PROVING | failure_class=BUILD_VERIFICATION_FAILED |
| 40437 | 2026-09-05T09:21:05.985Z | state_transition | PROVING | REPLAN | reason=BUILD_VERIFICATION_FAILED; failure_class=BUILD_VERIFICATION_FAILED |
| 40438 | 2026-09-05T09:21:06.173Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | failed | dc61dab36ec224f8f242aad58b8030bb1b6a3cc5fafc9e10179f160ec7ad4ca3 | False | 1313 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `72`
- Chain head: `f5afc8ad4e17aa4076ec736d39ced0253b773f3b35a8cc00fd4a2eddf3929989`
