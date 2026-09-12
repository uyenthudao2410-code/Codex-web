# Orchestration Wave 1

- Run: `6f62b7ad85034167a3889a4dd996f6bc`
- Wave: `875af05472e74997b393b13d4df0e410`
- Objective: N21 causal fix. Replace per-RUN exact stale maintenance with one bounded, atomic exact-ID batch so a single explicitly requested maintenance restart can reconcile all currently eligible zero-ownership stale RUN IDs without partial-prefix mutation. Preserve fail-closed guards: one immutable preflight batch snapshot must validate every exact target, reject any below-threshold/live-owned/P5/accepting/unrecognized target before mutation, bind all per-run activity/event guards, then one immediate transaction must revalidate the same logical snapshot and all targets before writing any target; one postflight must prove every target has the exact reconciliation receipt and intact hash chain. Raise the exact maintenance batch envelope only as needed for 64 IDs while retaining the ordinary supervisor restart reason bound. Update the CLI and FullCleanActivation to invoke batch preflight/reconcile once per batch rather than spawning per RUN. Preserve current unrelated dirty bytes in fullCleanActivation/runtimeOrchestrator/recoveryHost and all other files. The already-present RecoveryHost HANDOFF-yield fix is in scope only for verification, not rewriting. No restart in this wave; no reset/clean/commit/push/package/release/deploy. Add focused regression tests covering >16 IDs, atomic rejection/no partial writes, below-threshold/live-owned protection, batch CLI/FullClean invocation count, and existing handoff reconnect behavior.
- Objective revision: `1`
- Objective SHA-256: `9ecbb0ed6308cc09c45b05bf7bf0a89cf428e849d4a9ca6df30c30296db7ba00`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `7bc1caee37107a15e74eb078b52fe314e5fa33ab`
- Worktree fingerprint: `5ba63d33962971b8e2ca868861f040f4708602dc43f9ce95ae7cda05257a1942`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 48599 | 2026-09-11T03:15:30.764Z | run_started |  | PREFLIGHT |  |
| 48600 | 2026-09-11T03:15:31.148Z | observation_span_recorded |  |  |  |
| 48601 | 2026-09-11T03:15:31.392Z | solution_shadow_recommended |  |  |  |
| 48602 | 2026-09-11T03:15:37.148Z | observation_span_recorded |  |  |  |
| 48603 | 2026-09-11T03:15:37.334Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 48604 | 2026-09-11T03:16:58.797Z | managed_process_admitted |  |  | owner=default |
| 48605 | 2026-09-11T03:16:59.249Z | managed_process_started |  |  | owner=default |
| 48606 | 2026-09-11T03:16:59.729Z | managed_process_terminal |  |  | owner=default |
| 48607 | 2026-09-11T03:17:04.331Z | managed_process_admitted |  |  | owner=default |
| 48608 | 2026-09-11T03:17:04.723Z | managed_process_started |  |  | owner=default |
| 48609 | 2026-09-11T03:17:05.206Z | managed_process_terminal |  |  | owner=default |
| 48610 | 2026-09-11T03:17:16.908Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 48611 | 2026-09-11T03:17:17.109Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 48612 | 2026-09-11T03:17:17.332Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 48613 | 2026-09-11T03:17:17.538Z | state_transition | READY | ROUTED | reason=route_selected |
| 48614 | 2026-09-11T03:17:17.748Z | observation_span_recorded |  |  |  |
| 48615 | 2026-09-11T03:17:18.669Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=c7ec0b4494604d5496b763f95aa92131 |
| 48616 | 2026-09-11T03:17:18.861Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 48617 | 2026-09-11T03:17:19.612Z | existing_file_adoption_observed |  |  |  |
| 48618 | 2026-09-11T03:17:20.354Z | observation_span_recorded |  |  |  |
| 48619 | 2026-09-11T03:17:20.677Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=c7ec0b4494604d5496b763f95aa92131 |
| 48620 | 2026-09-11T03:17:20.882Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 48621 | 2026-09-11T03:17:21.640Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=c0309c7038c10ab6523adc47033c0310b2d5dc632206b829f2f7d9821c25adc2 |
| 48622 | 2026-09-11T03:17:21.994Z | managed_process_admitted |  |  | owner=default |
| 48623 | 2026-09-11T03:17:22.424Z | managed_process_started |  |  | owner=default |
| 48624 | 2026-09-11T03:17:24.172Z | managed_process_terminal |  |  | owner=default |
| 48625 | 2026-09-11T03:17:24.478Z | proof_recorded |  |  | stage_id=verify:tests; status=failed; cache_hit=False; input_fingerprint=c0309c7038c10ab6523adc47033c0310b2d5dc632206b829f2f7d9821c25adc2 |
| 48626 | 2026-09-11T03:17:24.681Z | observation_span_recorded |  |  |  |
| 48627 | 2026-09-11T03:17:24.866Z | failure_observed | PROVING | PROVING | failure_class=BUILD_VERIFICATION_FAILED |
| 48628 | 2026-09-11T03:17:25.077Z | state_transition | PROVING | REPLAN | reason=BUILD_VERIFICATION_FAILED; failure_class=BUILD_VERIFICATION_FAILED |
| 48629 | 2026-09-11T03:17:25.262Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | failed | c0309c7038c10ab6523adc47033c0310b2d5dc632206b829f2f7d9821c25adc2 | False | 2515 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `230`
- Chain head: `8472b3a1abb2df938d5130adc92d4598067a4a18c83329f943f5b0d9660cc601`
