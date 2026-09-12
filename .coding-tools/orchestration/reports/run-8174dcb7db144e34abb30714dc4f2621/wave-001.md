# Orchestration Wave 1

- Run: `8174dcb7db144e34abb30714dc4f2621`
- Wave: `cf29b3bd25ad4ef2a6c5ad2266696872`
- Objective: Propagate the durable source-controlled activation policy flag into successor final-census verification without changing checkpoint-free or other activation semantics: in FullCleanActivation._freshActivationObservation(record), when sourceCheckpoint exists, call orchestrator.verifyCodeActivation(record.operation_id, sourceCheckpoint, record.metadata?.allow_acceptance_pending === true). Add one focused regression in tests/full-clean-activation.test.js that directly proves the third verifyCodeActivation argument is true only when durable record metadata explicitly sets allow_acceptance_pending:true and false when absent/false. Preserve all unrelated pre-existing WIP bytes.
- Objective revision: `1`
- Objective SHA-256: `f8910ab6f54ec75cd3d8c774f0e62ccd70dbd91445cd9fdfdacf6d5aa49b7346`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `7bc1caee37107a15e74eb078b52fe314e5fa33ab`
- Worktree fingerprint: `ea172e9ba82d71ec6808af3e77508ee85530cc1f5c004383e8841dedbe0650c0`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 44658 | 2026-09-08T20:22:06.311Z | run_started |  | PREFLIGHT |  |
| 44659 | 2026-09-08T20:22:06.779Z | observation_span_recorded |  |  |  |
| 44660 | 2026-09-08T20:22:06.956Z | solution_shadow_recommended |  |  |  |
| 44661 | 2026-09-08T20:22:07.125Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 44662 | 2026-09-08T20:22:07.265Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 44663 | 2026-09-08T20:22:07.492Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 44664 | 2026-09-08T20:22:07.709Z | state_transition | READY | ROUTED | reason=route_selected |
| 44665 | 2026-09-08T20:22:07.914Z | observation_span_recorded |  |  |  |
| 44666 | 2026-09-08T20:22:08.677Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=4e18c8bbc9aa433c97926f615acacdbf |
| 44667 | 2026-09-08T20:22:08.811Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 44668 | 2026-09-08T20:22:09.689Z | patch_surface_observed |  |  |  |
| 44669 | 2026-09-08T20:22:09.975Z | observation_span_recorded |  |  |  |
| 44670 | 2026-09-08T20:22:10.194Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=4e18c8bbc9aa433c97926f615acacdbf |
| 44671 | 2026-09-08T20:22:10.325Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 44672 | 2026-09-08T20:22:11.041Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:9273835c18178321; input_fingerprint=ad571cc3ac92456fc89e12a0b1c79d7e27d5e71eac50fac30fc153d6ecf13ca7 |
| 44673 | 2026-09-08T20:22:11.388Z | managed_process_admitted |  |  | owner=default |
| 44674 | 2026-09-08T20:22:11.712Z | managed_process_started |  |  | owner=default |
| 44675 | 2026-09-08T20:22:16.646Z | managed_process_terminal |  |  | owner=default |
| 44676 | 2026-09-08T20:22:17.001Z | proof_recorded |  |  | stage_id=check:9273835c18178321; status=passed; cache_hit=False; input_fingerprint=ad571cc3ac92456fc89e12a0b1c79d7e27d5e71eac50fac30fc153d6ecf13ca7 |
| 44677 | 2026-09-08T20:22:17.215Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:fdd8d9bbdabfc13b; input_fingerprint=156aaf6da10edb101d0b6b2a9c9bc521f84ad1eebd30f9446263b728d28f03ed |
| 44678 | 2026-09-08T20:22:17.623Z | managed_process_admitted |  |  | owner=default |
| 44679 | 2026-09-08T20:22:17.993Z | managed_process_started |  |  | owner=default |
| 44680 | 2026-09-08T20:22:18.422Z | managed_process_terminal |  |  | owner=default |
| 44681 | 2026-09-08T20:22:18.752Z | proof_recorded |  |  | stage_id=check:fdd8d9bbdabfc13b; status=passed; cache_hit=False; input_fingerprint=156aaf6da10edb101d0b6b2a9c9bc521f84ad1eebd30f9446263b728d28f03ed |
| 44682 | 2026-09-08T20:22:19.677Z | observation_span_recorded |  |  |  |
| 44683 | 2026-09-08T20:22:19.853Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 44684 | 2026-09-08T20:24:55.525Z | quality_outcome_recorded |  |  |  |
| 44685 | 2026-09-08T20:24:55.713Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 44686 | 2026-09-08T20:24:56.031Z | observation_span_recorded |  |  |  |
| 44687 | 2026-09-08T20:24:56.206Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:9273835c18178321 | passed | ad571cc3ac92456fc89e12a0b1c79d7e27d5e71eac50fac30fc153d6ecf13ca7 | False | 5603 | 0 |
| check:fdd8d9bbdabfc13b | passed | 156aaf6da10edb101d0b6b2a9c9bc521f84ad1eebd30f9446263b728d28f03ed | False | 1161 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 63eb3b7d800c4ad5a926dbe1a8e9e457 | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | ad41a18c64cd3578a639d431877add65161d70946b6d9f58d1bb1786196b6391 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `30`
- Chain head: `85301bc4b622968bbc5b59ff8eef55fbb58bd5d371f8dab0a01c9bc665d5a1d5`
