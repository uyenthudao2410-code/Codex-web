# Orchestration Wave 1

- Run: `816cc0586ce24f05b07b928b920dd49c`
- Wave: `a9304937d5f94b0c918b019dce307cc5`
- Objective: Strict-timing mini-canary for Problem prl-terminal-projection-clear-restart-drift-20260912 revision 2. Create one normal read-only RUN, obtain a valid proof and final acceptance, operator-ACK the accepted report, then clear this request-scoped projection. A separately pre-armed observer will immediately run the full immutable lifecycle census. Acceptance/probe timestamps must demonstrate the post-clear semantic census occurred less than 60 seconds after this RUN became accepted, specifically testing the historical controller-lease TTL window. No source mutation, restart, ledger-history rewrite, commit, push, clean, reset, package, release, or deploy.
- Objective revision: `1`
- Objective SHA-256: `066046c3527b86cae891953d94f1a3c407aafc0aadfb67b005c78e46c70dc570`
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
| 51582 | 2026-09-12T10:39:43.074Z | run_started |  | PREFLIGHT |  |
| 51583 | 2026-09-12T10:39:43.686Z | observation_span_recorded |  |  |  |
| 51584 | 2026-09-12T10:39:44.777Z | observation_span_recorded |  |  |  |
| 51585 | 2026-09-12T10:39:44.838Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 51586 | 2026-09-12T10:39:56.518Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 51587 | 2026-09-12T10:39:56.768Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 51588 | 2026-09-12T10:39:57.057Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 51589 | 2026-09-12T10:39:57.350Z | state_transition | READY | ROUTED | reason=route_selected |
| 51590 | 2026-09-12T10:39:57.593Z | observation_span_recorded |  |  |  |
| 51591 | 2026-09-12T10:39:58.761Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=4bb0d16f2a9d4b94907548c22f04f369 |
| 51592 | 2026-09-12T10:39:59.001Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 51593 | 2026-09-12T10:40:00.152Z | observation_span_recorded |  |  |  |
| 51594 | 2026-09-12T10:40:00.469Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=4bb0d16f2a9d4b94907548c22f04f369 |
| 51595 | 2026-09-12T10:40:00.655Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 51596 | 2026-09-12T10:40:01.895Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=True; input_fingerprint=6e0a8684066997352ee14754cdb262d0e3b947492f3f82c045eff5690e77ce06 |
| 51597 | 2026-09-12T10:40:02.064Z | proof_cache_hit |  |  | stage_id=verify:tests; input_fingerprint=6e0a8684066997352ee14754cdb262d0e3b947492f3f82c045eff5690e77ce06 |
| 51598 | 2026-09-12T10:40:02.282Z | observation_span_recorded |  |  |  |
| 51599 | 2026-09-12T10:40:02.472Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 51600 | 2026-09-12T10:40:02.671Z | observation_stage_anchor_recorded | ACCEPTING | ACCEPTING |  |
| 51601 | 2026-09-12T10:40:52.814Z | quality_outcome_recorded |  |  |  |
| 51602 | 2026-09-12T10:40:53.016Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 51603 | 2026-09-12T10:40:53.371Z | observation_span_recorded |  |  |  |
| 51604 | 2026-09-12T10:40:53.681Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |
| 51605 | 2026-09-12T10:40:54.385Z | observation_span_recorded |  |  |  |
| 51606 | 2026-09-12T10:40:54.619Z | observation_span_recorded |  |  |  |
| 51607 | 2026-09-12T10:40:54.824Z | continuity_telemetry_recorded |  |  |  |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 6e0a8684066997352ee14754cdb262d0e3b947492f3f82c045eff5690e77ce06 | True | 0 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| f1b85cff74a046d1a512b079944c7c6d | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | 8962a8c9cab3f2d5026b41acf61c9f725076630d6e0d6cb35fb5b2a7b327c794 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `26`
- Chain head: `da498c355d426fc6ccc80960c77cab26aa2285c932ef0627aeb616171933265c`
