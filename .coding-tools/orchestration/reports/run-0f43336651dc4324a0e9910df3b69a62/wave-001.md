# Orchestration Wave 1

- Run: `0f43336651dc4324a0e9910df3b69a62`
- Wave: `da9f5905397446868e247c1849610f78`
- Objective: Natural #6: fix empirical-readiness automatic natural-cohort start selection so trailing valid-but-untyped Problem revisions do not erase the newest existing typed-natural segment. Keep explicit exact start behavior unchanged, do not alter technically_accepted semantics, and preserve read-only/audit-only/no-P5/no-stale-reconciliation behavior. Prepare only; no mutation.
- Objective revision: `1`
- Objective SHA-256: `ffef902a818d220ee23cf5ff23f1b0aca54c410256e559dfc6d3c4d9a7204956`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `7bc1caee37107a15e74eb078b52fe314e5fa33ab`
- Worktree fingerprint: `ae6b9490916c7d3b3a2fe617ed7fcbef3a89e943ac4f12c80490a1d4039e1757`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 45595 | 2026-09-09T10:52:57.739Z | run_started |  | PREFLIGHT |  |
| 45596 | 2026-09-09T10:52:58.239Z | observation_span_recorded |  |  |  |
| 45597 | 2026-09-09T10:52:58.450Z | solution_shadow_recommended |  |  |  |
| 45598 | 2026-09-09T10:53:04.413Z | observation_span_recorded |  |  |  |
| 45599 | 2026-09-09T10:53:05.294Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 45600 | 2026-09-09T10:53:39.493Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 45601 | 2026-09-09T10:53:39.677Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 45602 | 2026-09-09T10:53:39.903Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 45603 | 2026-09-09T10:53:40.084Z | state_transition | READY | ROUTED | reason=route_selected |
| 45604 | 2026-09-09T10:53:40.293Z | observation_span_recorded |  |  |  |
| 45605 | 2026-09-09T10:53:41.149Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=e31014d425a5462290e0e0d818928e07 |
| 45606 | 2026-09-09T10:53:41.268Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 45607 | 2026-09-09T10:53:42.093Z | patch_surface_observed |  |  |  |
| 45608 | 2026-09-09T10:53:42.234Z | observation_span_recorded |  |  |  |
| 45609 | 2026-09-09T10:53:42.514Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=e31014d425a5462290e0e0d818928e07 |
| 45610 | 2026-09-09T10:53:42.659Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 45611 | 2026-09-09T10:53:43.414Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:5a9e8e2e0183e99b; input_fingerprint=36682db970052495336f2a9e635e5c3c1e00b5612992f7296b1c2de120c142e4 |
| 45612 | 2026-09-09T10:53:43.757Z | managed_process_admitted |  |  | owner=default |
| 45613 | 2026-09-09T10:53:44.017Z | managed_process_started |  |  | owner=default |
| 45614 | 2026-09-09T10:53:44.485Z | managed_process_terminal |  |  | owner=default |
| 45615 | 2026-09-09T10:53:44.946Z | proof_recorded |  |  | stage_id=check:5a9e8e2e0183e99b; status=passed; cache_hit=False; input_fingerprint=36682db970052495336f2a9e635e5c3c1e00b5612992f7296b1c2de120c142e4 |
| 45616 | 2026-09-09T10:53:45.142Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:d19c219b7186c61b; input_fingerprint=0aa3ebde7665cc3ebbf434a6f8c604a6d2eb9ef866f89db30b25b4c5d309298a |
| 45617 | 2026-09-09T10:53:45.493Z | managed_process_admitted |  |  | owner=default |
| 45618 | 2026-09-09T10:53:45.776Z | managed_process_started |  |  | owner=default |
| 45619 | 2026-09-09T10:53:52.927Z | managed_process_terminal |  |  | owner=default |
| 45620 | 2026-09-09T10:53:53.363Z | proof_recorded |  |  | stage_id=check:d19c219b7186c61b; status=passed; cache_hit=False; input_fingerprint=0aa3ebde7665cc3ebbf434a6f8c604a6d2eb9ef866f89db30b25b4c5d309298a |
| 45621 | 2026-09-09T10:53:53.570Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=dc3606840018d191898a97b95f1e41009d6fdfee56a600eaa86c5a19e78c65b4 |
| 45622 | 2026-09-09T10:53:53.920Z | managed_process_admitted |  |  | owner=default |
| 45623 | 2026-09-09T10:53:54.200Z | managed_process_started |  |  | owner=default |
| 45624 | 2026-09-09T10:53:55.383Z | managed_process_terminal |  |  | owner=default |
| 45625 | 2026-09-09T10:53:56.639Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=dc3606840018d191898a97b95f1e41009d6fdfee56a600eaa86c5a19e78c65b4 |
| 45626 | 2026-09-09T10:53:57.620Z | observation_span_recorded |  |  |  |
| 45627 | 2026-09-09T10:53:57.833Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 45628 | 2026-09-09T10:56:07.785Z | managed_process_admitted |  |  | owner=default |
| 45629 | 2026-09-09T10:56:08.190Z | managed_process_started |  |  | owner=default |
| 45630 | 2026-09-09T10:56:08.600Z | managed_process_terminal |  |  | owner=default |
| 45631 | 2026-09-09T10:57:14.229Z | managed_process_admitted |  |  | owner=default |
| 45632 | 2026-09-09T10:57:14.583Z | managed_process_started |  |  | owner=default |
| 45633 | 2026-09-09T10:57:15.019Z | managed_process_terminal |  |  | owner=default |
| 45634 | 2026-09-09T10:57:23.808Z | managed_process_admitted |  |  | owner=default |
| 45635 | 2026-09-09T10:57:24.138Z | managed_process_started |  |  | owner=default |
| 45636 | 2026-09-09T10:57:24.620Z | managed_process_terminal |  |  | owner=default |
| 45637 | 2026-09-09T10:58:55.394Z | managed_process_admitted |  |  | owner=default |
| 45638 | 2026-09-09T10:58:55.737Z | managed_process_started |  |  | owner=default |
| 45639 | 2026-09-09T10:58:56.351Z | managed_process_terminal |  |  | owner=default |
| 45640 | 2026-09-09T11:03:38.600Z | managed_process_admitted |  |  | owner=default |
| 45641 | 2026-09-09T11:03:39.005Z | managed_process_started |  |  | owner=default |
| 45642 | 2026-09-09T11:03:39.770Z | managed_process_terminal |  |  | owner=default |
| 45643 | 2026-09-09T11:05:05.790Z | managed_process_admitted |  |  | owner=default |
| 45644 | 2026-09-09T11:05:06.133Z | managed_process_started |  |  | owner=default |
| 45645 | 2026-09-09T11:05:06.629Z | managed_process_terminal |  |  | owner=default |
| 45646 | 2026-09-09T11:05:34.023Z | quality_outcome_recorded |  |  |  |
| 45647 | 2026-09-09T11:05:34.174Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 45648 | 2026-09-09T11:05:34.455Z | observation_span_recorded |  |  |  |
| 45649 | 2026-09-09T11:05:34.712Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:5a9e8e2e0183e99b | passed | 36682db970052495336f2a9e635e5c3c1e00b5612992f7296b1c2de120c142e4 | False | 1118 | 0 |
| check:d19c219b7186c61b | passed | 0aa3ebde7665cc3ebbf434a6f8c604a6d2eb9ef866f89db30b25b4c5d309298a | False | 7883 | 0 |
| verify:tests | passed | dc3606840018d191898a97b95f1e41009d6fdfee56a600eaa86c5a19e78c65b4 | False | 2657 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 42617b1266e14e12b489cb43026b777e | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | 9d612d8c8503d28c1e6663d6b280dd5638309c8d2afee58038f1a7060490fc74 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `55`
- Chain head: `4441468204bae4265719f71e2891cefbd2d4c35946f440a9d50f5f202437fd92`
