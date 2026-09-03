# Orchestration Wave 1

- Run: `b3273e736aad4928a0631dcad65af8c2`
- Wave: `8ea0be9cb8d2498d8661bda24d157fc4`
- Objective: Replacement W2 after durable control-plane context loss terminalized prior RUN 03fd5fbb0cc34177972b6065150c8f73 without Wave-3 writes. Implement exact cross-wave idempotency for ChatWeb controller usage. Controller economic usage_id must be stable for RUN + turn_id across reconnect/REPLAN waves; wave_id/delegation_id remain first-attribution metadata. Same exact controller receipt in a later wave must deduplicate without double-counting. Conflicting economic evidence for the same RUN+turn must fail closed. Generic/provider build_usage_event identity and provider dedupe semantics must remain unchanged. Preserve unknown_not_zero and unrelated dirty work. Add focused regression proof. Do not reuse prior stale proof. No commit/push/restart/package/release/deploy.
- Objective revision: `1`
- Objective SHA-256: `dd4208ba4e446e50864cbf4cc2113f37cce8071e430436a2c0a01ffef41ed89a`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `30b7d1b971b65034d3e4c95568c970fcc0e9380c`
- Worktree fingerprint: `808eed8f72b06394accf31267b8bb5211e6dca404551be197fd575a9030acbfc`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 33638 | 2026-08-31T19:04:17.858Z | run_started |  | PREFLIGHT |  |
| 33639 | 2026-08-31T19:04:18.275Z | observation_span_recorded |  |  |  |
| 33640 | 2026-08-31T19:04:18.522Z | solution_shadow_recommended |  |  |  |
| 33641 | 2026-08-31T19:04:19.307Z | observation_span_recorded |  |  |  |
| 33642 | 2026-08-31T19:04:19.512Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 33643 | 2026-08-31T19:04:19.772Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 33644 | 2026-08-31T19:04:19.972Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 33645 | 2026-08-31T19:04:20.190Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 33646 | 2026-08-31T19:04:20.403Z | state_transition | READY | ROUTED | reason=route_selected |
| 33647 | 2026-08-31T19:04:20.627Z | observation_span_recorded |  |  |  |
| 33648 | 2026-08-31T19:04:21.446Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=638541260b764928811cf00781e3f85b |
| 33649 | 2026-08-31T19:04:21.653Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 33650 | 2026-08-31T19:04:22.465Z | patch_surface_observed |  |  |  |
| 33651 | 2026-08-31T19:04:22.634Z | observation_span_recorded |  |  |  |
| 33652 | 2026-08-31T19:04:22.930Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=638541260b764928811cf00781e3f85b |
| 33653 | 2026-08-31T19:04:23.116Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 33654 | 2026-08-31T19:04:23.848Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=f3e52f0e60f792c1b9d938df5b1df04555787031dde3e4b98bdf70999faaca33 |
| 33655 | 2026-08-31T19:04:24.142Z | managed_process_admitted |  |  | owner=default |
| 33656 | 2026-08-31T19:04:24.478Z | managed_process_started |  |  | owner=default |
| 33657 | 2026-08-31T19:04:25.785Z | managed_process_terminal |  |  | owner=default |
| 33658 | 2026-08-31T19:04:27.033Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=f3e52f0e60f792c1b9d938df5b1df04555787031dde3e4b98bdf70999faaca33 |
| 33659 | 2026-08-31T19:04:27.926Z | observation_span_recorded |  |  |  |
| 33660 | 2026-08-31T19:04:28.132Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 33661 | 2026-08-31T19:10:14.453Z | quality_outcome_recorded |  |  |  |
| 33662 | 2026-08-31T19:10:14.732Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 33663 | 2026-08-31T19:10:15.085Z | observation_span_recorded |  |  |  |
| 33664 | 2026-08-31T19:10:15.349Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | f3e52f0e60f792c1b9d938df5b1df04555787031dde3e4b98bdf70999faaca33 | False | 2796 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| c4dc970d846742c28e53fc98c6f3aeb7 | accepted | 30b7d1b971b65034d3e4c95568c970fcc0e9380c | 9263765c83e2b98ca345ee37472a87ffcfe735215a5f64ce746a464837bd3bc8 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `27`
- Chain head: `1cb3f7580c257dbc2b3c6d3c37af0fd8e8f964f15fa040b2f549408cf466cc60`
