# Orchestration Wave 1

- Run: `03e4ff4dad8b4cc38d77ee7a10da6d09`
- Wave: `f51e17c461c64322b5a25655418c01be`
- Objective: Strict-timing mini-canary retry for Problem prl-terminal-projection-clear-restart-drift-20260912 revision 2. Create one normal read-only RUN, obtain final acceptance, ACK its accepted report, clear the request-scoped projection, then immediately use the already-live observer RUN 8aa174e6591a4bec975916556dc0e508 / WAVE 7a38a7e9628a49f59a4a612773be8284 to run the full immutable lifecycle census. This retry exists because the previous attempt's first observer call used stale owner IDs and lost the <60-second acceptance window. Measure from final_acceptance_recorded to observer census observed_at; require <60 seconds. No source mutation, restart, ledger-history rewrite, commit, push, clean, reset, package, release, or deploy.
- Objective revision: `1`
- Objective SHA-256: `744f15ce5e52cc2f2369edfdf181caf9a02315016861b169383e974dde249c5f`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `7bc1caee37107a15e74eb078b52fe314e5fa33ab`
- Worktree fingerprint: `3388a2f3375dbd7e9858133bfd7aeb840c4053256947a77fedfb1b4f13ab022d`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 51612 | 2026-09-12T10:42:38.115Z | run_started |  | PREFLIGHT |  |
| 51613 | 2026-09-12T10:42:38.697Z | observation_span_recorded |  |  |  |
| 51614 | 2026-09-12T10:42:39.614Z | observation_span_recorded |  |  |  |
| 51615 | 2026-09-12T10:42:39.827Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 51616 | 2026-09-12T10:42:50.194Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 51617 | 2026-09-12T10:42:50.394Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 51618 | 2026-09-12T10:42:50.561Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 51619 | 2026-09-12T10:42:50.760Z | state_transition | READY | ROUTED | reason=route_selected |
| 51620 | 2026-09-12T10:42:50.944Z | observation_span_recorded |  |  |  |
| 51621 | 2026-09-12T10:42:51.949Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=87919f06c544410c93869e871dbac14e |
| 51622 | 2026-09-12T10:42:52.100Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 51623 | 2026-09-12T10:42:52.939Z | observation_span_recorded |  |  |  |
| 51624 | 2026-09-12T10:42:53.232Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=87919f06c544410c93869e871dbac14e |
| 51625 | 2026-09-12T10:42:53.439Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 51626 | 2026-09-12T10:42:54.546Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=True; input_fingerprint=6e0a8684066997352ee14754cdb262d0e3b947492f3f82c045eff5690e77ce06 |
| 51627 | 2026-09-12T10:42:54.761Z | proof_cache_hit |  |  | stage_id=verify:tests; input_fingerprint=6e0a8684066997352ee14754cdb262d0e3b947492f3f82c045eff5690e77ce06 |
| 51628 | 2026-09-12T10:42:54.980Z | observation_span_recorded |  |  |  |
| 51629 | 2026-09-12T10:42:55.167Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 51630 | 2026-09-12T10:42:55.407Z | observation_stage_anchor_recorded | ACCEPTING | ACCEPTING |  |
| 51631 | 2026-09-12T10:43:45.872Z | quality_outcome_recorded |  |  |  |
| 51632 | 2026-09-12T10:43:46.107Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 51633 | 2026-09-12T10:43:46.427Z | observation_span_recorded |  |  |  |
| 51634 | 2026-09-12T10:43:46.659Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |
| 51635 | 2026-09-12T10:43:46.859Z | observation_span_recorded |  |  |  |
| 51636 | 2026-09-12T10:43:47.092Z | observation_span_recorded |  |  |  |
| 51637 | 2026-09-12T10:43:47.315Z | continuity_telemetry_recorded |  |  |  |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 6e0a8684066997352ee14754cdb262d0e3b947492f3f82c045eff5690e77ce06 | True | 0 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 115379d8018849279c7ee3688a567e22 | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | 5d11b5d1033eb13377d050e45fb8bc7ad6bae3fd7d4239d46f474b306f187cec | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `26`
- Chain head: `f0a83830f41d62f4448dd9887a4063fafaeb10a98d0890eced62a5bfc63f1f1e`
