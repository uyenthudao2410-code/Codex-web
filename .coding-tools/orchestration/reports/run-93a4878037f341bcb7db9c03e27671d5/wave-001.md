# Orchestration Wave 1

- Run: `93a4878037f341bcb7db9c03e27671d5`
- Wave: `855b32ea9e554b2aaaa250b087d1260c`
- Objective: Correct the Windows deferred full-clean activation race where deferExecute exit cleanup can delete the parent marker before the detached deferred worker starts. Create an independent corrective EOCL RUN/WAVE. Preserve all unrelated dirty work. Scope mutation to scripts/full-clean-activation.js and tests/full-clean-activation-command.test.js only. Add a deterministic regression for worker start after parent exit/marker cleanup. Implement the smallest fail-closed fix that accepts only a valid closed parent boundary while still rejecting replaced/wrong-nonce markers and duplicate workers. Do not adopt or force-release any existing W7/old lease. Do not commit, push, restart, deploy, or edit the ledger directly.
- Objective revision: `1`
- Objective SHA-256: `48d6f110ebdc12f7a2fe7eaaa5f76ac1351952f1091c2677948779cd25a0d245`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `30b7d1b971b65034d3e4c95568c970fcc0e9380c`
- Worktree fingerprint: `09ab9500ce39b7fa5af045e0c4c7f4149a6820fd20b04886835e78bfe73b4f12`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 34556 | 2026-09-01T15:30:01.206Z | run_started |  | PREFLIGHT |  |
| 34557 | 2026-09-01T15:30:01.608Z | observation_span_recorded |  |  |  |
| 34558 | 2026-09-01T15:30:01.836Z | solution_shadow_recommended |  |  |  |
| 34559 | 2026-09-01T15:30:02.905Z | observation_span_recorded |  |  |  |
| 34560 | 2026-09-01T15:30:04.214Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 34561 | 2026-09-01T15:31:00.984Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 34562 | 2026-09-01T15:31:01.206Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 34563 | 2026-09-01T15:31:01.412Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 34564 | 2026-09-01T15:31:01.604Z | state_transition | READY | ROUTED | reason=route_selected |
| 34565 | 2026-09-01T15:31:01.816Z | observation_span_recorded |  |  |  |
| 34566 | 2026-09-01T15:31:02.622Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=4021f21df61b4bfc9001396fc50dc847 |
| 34567 | 2026-09-01T15:31:02.854Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 34568 | 2026-09-01T15:31:03.729Z | patch_surface_observed |  |  |  |
| 34569 | 2026-09-01T15:31:03.906Z | observation_span_recorded |  |  |  |
| 34570 | 2026-09-01T15:31:04.247Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=4021f21df61b4bfc9001396fc50dc847 |
| 34571 | 2026-09-01T15:31:04.397Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 34572 | 2026-09-01T15:31:05.098Z | proof_cache_miss |  |  | reason=cold; stage_id=check:feffe3ea877a9c9f; input_fingerprint=1561950de999b79b5504d3eadb8fda5a5d003c9e44c9a6b42c97e18e3e1a05b2 |
| 34573 | 2026-09-01T15:31:05.426Z | managed_process_admitted |  |  | owner=default |
| 34574 | 2026-09-01T15:31:05.944Z | managed_process_started |  |  | owner=default |
| 34575 | 2026-09-01T15:31:06.414Z | managed_process_terminal |  |  | owner=default |
| 34576 | 2026-09-01T15:31:06.801Z | proof_recorded |  |  | stage_id=check:feffe3ea877a9c9f; status=passed; cache_hit=False; input_fingerprint=1561950de999b79b5504d3eadb8fda5a5d003c9e44c9a6b42c97e18e3e1a05b2 |
| 34577 | 2026-09-01T15:31:06.992Z | proof_cache_miss |  |  | reason=cold; stage_id=check:358ee0de1aeaec17; input_fingerprint=cd6d3afb967929e7c16111dcf9d7cdd85f4701c686c4fd08f1828e45196424f7 |
| 34578 | 2026-09-01T15:31:07.368Z | managed_process_admitted |  |  | owner=default |
| 34579 | 2026-09-01T15:31:07.738Z | managed_process_started |  |  | owner=default |
| 34580 | 2026-09-01T15:31:08.251Z | managed_process_terminal |  |  | owner=default |
| 34581 | 2026-09-01T15:31:08.594Z | proof_recorded |  |  | stage_id=check:358ee0de1aeaec17; status=passed; cache_hit=False; input_fingerprint=cd6d3afb967929e7c16111dcf9d7cdd85f4701c686c4fd08f1828e45196424f7 |
| 34582 | 2026-09-01T15:31:08.776Z | proof_cache_miss |  |  | reason=cold; stage_id=check:23efc2d04b2baee1; input_fingerprint=4ad3e21eb4da38e9f564aa4e3efdef6ae1b547e0290635b3b91c40d3674d1b80 |
| 34583 | 2026-09-01T15:31:09.183Z | managed_process_admitted |  |  | owner=default |
| 34584 | 2026-09-01T15:31:09.524Z | managed_process_started |  |  | owner=default |
| 34585 | 2026-09-01T15:31:09.958Z | managed_process_terminal |  |  | owner=default |
| 34586 | 2026-09-01T15:31:10.460Z | proof_recorded |  |  | stage_id=check:23efc2d04b2baee1; status=passed; cache_hit=False; input_fingerprint=4ad3e21eb4da38e9f564aa4e3efdef6ae1b547e0290635b3b91c40d3674d1b80 |
| 34587 | 2026-09-01T15:31:10.662Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=09ae8da4b3013782c18a3585f703d20befaec826a6f68e2d0a185ac8265968fa |
| 34588 | 2026-09-01T15:31:11.019Z | managed_process_admitted |  |  | owner=default |
| 34589 | 2026-09-01T15:31:11.307Z | managed_process_started |  |  | owner=default |
| 34590 | 2026-09-01T15:31:11.907Z | managed_process_terminal |  |  | owner=default |
| 34591 | 2026-09-01T15:31:13.118Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=09ae8da4b3013782c18a3585f703d20befaec826a6f68e2d0a185ac8265968fa |
| 34592 | 2026-09-01T15:31:13.999Z | observation_span_recorded |  |  |  |
| 34593 | 2026-09-01T15:31:14.223Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 34594 | 2026-09-01T15:39:53.803Z | quality_outcome_recorded |  |  |  |
| 34595 | 2026-09-01T15:39:54.039Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 34596 | 2026-09-01T15:39:54.291Z | observation_span_recorded |  |  |  |
| 34597 | 2026-09-01T15:39:54.492Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:feffe3ea877a9c9f | passed | 1561950de999b79b5504d3eadb8fda5a5d003c9e44c9a6b42c97e18e3e1a05b2 | False | 1378 | 0 |
| check:358ee0de1aeaec17 | passed | cd6d3afb967929e7c16111dcf9d7cdd85f4701c686c4fd08f1828e45196424f7 | False | 1261 | 0 |
| check:23efc2d04b2baee1 | passed | 4ad3e21eb4da38e9f564aa4e3efdef6ae1b547e0290635b3b91c40d3674d1b80 | False | 1136 | 0 |
| verify:tests | passed | 09ae8da4b3013782c18a3585f703d20befaec826a6f68e2d0a185ac8265968fa | False | 2000 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 254fd1f05e324855963186b4ea60e051 | accepted | 30b7d1b971b65034d3e4c95568c970fcc0e9380c | 92cce819a65cf560ace3056a86d1dbebc3596c408bdf84ff4e97ad227c9eb1a8 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `42`
- Chain head: `6f376152cd85700ba74400cfe34bcaf851657c5ea6c31c7119fdc1f649f4f8ee`
