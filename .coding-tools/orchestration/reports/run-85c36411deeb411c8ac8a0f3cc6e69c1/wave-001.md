# Orchestration Wave 1

- Run: `85c36411deeb411c8ac8a0f3cc6e69c1`
- Wave: `6114ac96e2314a1bbf8af620977cd41e`
- Objective: Continue RUN 4ccf77eee93d4cfba07e46609157d04e with a new corrective wave after the pre-write SOLUTION_SHADOW_REQUIRED gate. Fix the Full clean activation race that causes ACTIVATION_EPOCH_STATE_REGRESSION: RecoveryHost.superviseOnce must run replacement watchdog final-census only in post-handoff assembly states STARTING or VERIFYING, never in PREPARING, ADMISSION_CLOSED, FROZEN, STOPPING, or HANDOFF. FullCleanActivation.recordPendingCensus must fail closed without mutating the durable epoch unless current state is STARTING or VERIFYING; preserve STARTING -> VERIFYING and VERIFYING evidence refresh. Add deterministic regressions proving STOPPING is not advanced by watchdog, pre-start/pre-handoff recordPendingCensus rejects without mutation, STARTING and VERIFYING remain valid, and existing duplicate/finalization semantics do not regress. Preserve all unrelated dirty worktree and .coding-tools evidence. No adoption or force-release. No commit/push/tag/release/deploy/restart/activation. Use only the supplied four paths.
- Objective revision: `1`
- Objective SHA-256: `f98d71720dbe030c45f4ea864bbf674c64070636199b18051dcfafb12d0f3290`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `30b7d1b971b65034d3e4c95568c970fcc0e9380c`
- Worktree fingerprint: `7573c9037fbba39777f4190f8c36d72b39ae76215e3e88b786f80e097ad4a3a2`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 34601 | 2026-09-01T16:01:31.529Z | run_started |  | PREFLIGHT |  |
| 34602 | 2026-09-01T16:01:31.911Z | observation_span_recorded |  |  |  |
| 34603 | 2026-09-01T16:01:32.161Z | solution_shadow_recommended |  |  |  |
| 34604 | 2026-09-01T16:01:32.381Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 34605 | 2026-09-01T16:01:32.564Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 34606 | 2026-09-01T16:01:32.778Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 34607 | 2026-09-01T16:01:32.964Z | state_transition | READY | ROUTED | reason=route_selected |
| 34608 | 2026-09-01T16:01:33.204Z | observation_span_recorded |  |  |  |
| 34609 | 2026-09-01T16:01:34.124Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=f33bff6a2dca4756a19e755aadd126fa |
| 34610 | 2026-09-01T16:01:34.359Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 34611 | 2026-09-01T16:01:35.093Z | observation_span_recorded |  |  |  |
| 34612 | 2026-09-01T16:01:35.490Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=f33bff6a2dca4756a19e755aadd126fa |
| 34613 | 2026-09-01T16:01:35.720Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 34614 | 2026-09-01T16:01:36.449Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:466c2f308b48c766; input_fingerprint=1d28620d687ec1063e1dc798b9f45796ca9b1bdba410bf498dd9b94fdaa7764d |
| 34615 | 2026-09-01T16:01:36.855Z | managed_process_admitted |  |  | owner=default |
| 34616 | 2026-09-01T16:01:37.208Z | managed_process_started |  |  | owner=default |
| 34617 | 2026-09-01T16:01:38.082Z | managed_process_terminal |  |  | owner=default |
| 34618 | 2026-09-01T16:01:38.443Z | proof_recorded |  |  | stage_id=check:466c2f308b48c766; status=passed; cache_hit=False; input_fingerprint=1d28620d687ec1063e1dc798b9f45796ca9b1bdba410bf498dd9b94fdaa7764d |
| 34619 | 2026-09-01T16:01:38.649Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=49b8b434c15dcdf27e9654c73b076e74ef114358ab3c7b7a738ff21c4180dc9f |
| 34620 | 2026-09-01T16:01:39.026Z | managed_process_admitted |  |  | owner=default |
| 34621 | 2026-09-01T16:01:39.540Z | managed_process_started |  |  | owner=default |
| 34622 | 2026-09-01T16:01:44.025Z | managed_process_terminal |  |  | owner=default |
| 34623 | 2026-09-01T16:01:45.249Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=49b8b434c15dcdf27e9654c73b076e74ef114358ab3c7b7a738ff21c4180dc9f |
| 34624 | 2026-09-01T16:01:45.552Z | observation_span_recorded |  |  |  |
| 34625 | 2026-09-01T16:01:45.764Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 34626 | 2026-09-01T16:02:05.443Z | observation_span_recorded |  |  |  |
| 34627 | 2026-09-01T16:02:05.657Z | failure_observed | ACCEPTING | ACCEPTING | reason=Reject to REPLAN: deterministic execution ran only the pre-existing focused suite and produced modified_files=[] with no write lease. The old oracle does not discriminate the reported STOPPING watchdog/state-regression race, so the requested implementation and regressions are absent.; failure_class=SOL_REJECTED |
| 34628 | 2026-09-01T16:02:05.868Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |
| 34629 | 2026-09-01T16:02:06.059Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:466c2f308b48c766 | passed | 1d28620d687ec1063e1dc798b9f45796ca9b1bdba410bf498dd9b94fdaa7764d | False | 1637 | 0 |
| verify:tests | passed | 49b8b434c15dcdf27e9654c73b076e74ef114358ab3c7b7a738ff21c4180dc9f | False | 6172 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `132`
- Chain head: `1a2cafc28aa67b8ed4ddb35ed93dec2b08d9613e2c333c12109e21dacdfd1b55`
