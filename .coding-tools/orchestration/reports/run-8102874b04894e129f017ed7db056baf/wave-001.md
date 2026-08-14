# Orchestration Wave 1

- Run: `8102874b04894e129f017ed7db056baf`
- Wave: `16c598fede4e4befb16eaad4247a307b`
- Objective: P2B runtime projection reconciliation: after startup stale/terminal ledger reconciliation and after OrchestrationControl is available, reconcile the persisted TaskState orchestration projection with the authoritative run row. If the projected run is terminal, map accepted->CHECKPOINTED, blocked->BLOCKED, aborted|stale->ABORTED, use the latest durable wave id, clear write lease/owner fields, and emit orchestration_projection_reconciled. Do not change task objective/history, do not turn stale proof into acceptance, and do not touch active runs. Expose a bounded boolean recovery flag in workspace_context/task_control recovery. Add focused test with a stale parent + lingering ACCEPTING TaskState proving fresh Runtime repairs both child wave and projection while preserving run status stale.
- Mode: `mcp_only`
- Base HEAD: `5decaa48300b10a6df39676c677745bc881cd7d9`
- Worktree fingerprint: `0b1802aa1fcd19b2359d2575eb0ab8d4352cb22936db948cf5b097c4013fe549`
- Contract fingerprint: ``
- Status: **active**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 3234 | 2026-08-14T18:04:28.130Z | run_started |  | PREFLIGHT |  |
| 3235 | 2026-08-14T18:04:28.265Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 3236 | 2026-08-14T18:04:28.408Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 3237 | 2026-08-14T18:04:28.545Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 3238 | 2026-08-14T18:04:28.670Z | state_transition | READY | ROUTED | reason=route_selected |
| 3239 | 2026-08-14T18:04:29.161Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=0b6d8e274723402aa0b1d3a2814c4f44 |
| 3240 | 2026-08-14T18:04:29.279Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 3241 | 2026-08-14T18:04:29.866Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=0b6d8e274723402aa0b1d3a2814c4f44 |
| 3242 | 2026-08-14T18:04:30.000Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 3243 | 2026-08-14T18:04:30.351Z | proof_cache_miss |  |  | reason=cold; stage_id=check:f562f0b244e63c8e; input_fingerprint=39cca6c11c4e0d5a65216723737d24b9cce47abf3c62571c5b3fcf06d625b096 |
| 3244 | 2026-08-14T18:04:32.119Z | proof_recorded |  |  | stage_id=check:f562f0b244e63c8e; status=failed; cache_hit=False; input_fingerprint=39cca6c11c4e0d5a65216723737d24b9cce47abf3c62571c5b3fcf06d625b096 |
| 3245 | 2026-08-14T18:04:32.320Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 3246 | 2026-08-14T18:04:32.449Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:f562f0b244e63c8e | failed | 39cca6c11c4e0d5a65216723737d24b9cce47abf3c62571c5b3fcf06d625b096 | False | 1467 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `13`
- Chain head: `eb04697fe04123511be28e80976684e05bb5b4540a1898f48f7955f84f2eba73`
