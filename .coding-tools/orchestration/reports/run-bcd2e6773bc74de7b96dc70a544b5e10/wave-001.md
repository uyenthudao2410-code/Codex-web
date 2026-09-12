# Orchestration Wave 1

- Run: `bcd2e6773bc74de7b96dc70a544b5e10`
- Wave: `a5bf52208da9402292d0c2593b292a72`
- Objective: Fix the demonstrated deadline conflation in the supervisor restart path without widening any guard. The 60-second supervisor restart ticket expiry remains the fail-closed admission/claim window. Once a fresh ticket is validly claimed and a full-clean activation begins, do not reuse that ticket expiry as the durable activation execution deadline; let FullCleanActivation establish its existing independent bounded end-to-end deadline. Preserve idempotent processing-journal behavior, source/identity/fence checks, exact stale-run maintenance scope, and all existing activation expiry enforcement. Add focused regression in tests/runtime-lifecycle.test.js proving a fresh supervisor ticket is accepted only within its own expiry but the claimed activation call is not shortened to the ticket expiry, including the exact stale-maintenance path that can complete maintenance before a slower cold startup/connector. Do not modify restart_ticket.py or fullCleanActivation.js. Run focused runtime-lifecycle supervisor tests and the existing full-clean activation tests that assert the independent ten-minute durable deadline. No restart, no stale-run replay, no commit/push/package/release/deploy.
- Objective revision: `1`
- Objective SHA-256: `ba4f64ff9eed52c39d2469f8259d1acd5fca326d5a5fdb93af1ad31f3137c4e4`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `7bc1caee37107a15e74eb078b52fe314e5fa33ab`
- Worktree fingerprint: `0ad22c5e1811b40ec2a1ed108a21e92fb26c3622fe68e643e31c1f9cf6b6d210`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 50053 | 2026-09-12T03:38:58.388Z | run_started |  | PREFLIGHT |  |
| 50054 | 2026-09-12T03:38:58.923Z | observation_span_recorded |  |  |  |
| 50055 | 2026-09-12T03:38:59.139Z | solution_shadow_recommended |  |  |  |
| 50056 | 2026-09-12T03:39:05.436Z | observation_span_recorded |  |  |  |
| 50057 | 2026-09-12T03:39:05.646Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 50058 | 2026-09-12T03:40:01.332Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 50059 | 2026-09-12T03:40:01.554Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 50060 | 2026-09-12T03:40:01.753Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=auto; resolved=deterministic |
| 50061 | 2026-09-12T03:40:01.937Z | state_transition | READY | ROUTED | reason=route_selected |
| 50062 | 2026-09-12T03:40:02.149Z | observation_span_recorded |  |  |  |
| 50063 | 2026-09-12T03:40:03.137Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=5b493c7e087d48588d77a32e27c74eab |
| 50064 | 2026-09-12T03:40:03.337Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 50065 | 2026-09-12T03:40:04.276Z | patch_surface_observed |  |  |  |
| 50066 | 2026-09-12T03:40:04.464Z | observation_span_recorded |  |  |  |
| 50067 | 2026-09-12T03:40:04.836Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=5b493c7e087d48588d77a32e27c74eab |
| 50068 | 2026-09-12T03:40:05.011Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 50069 | 2026-09-12T03:40:05.878Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=fc1b368138735ea26016f8731fb8f4e3307addb0025f3f6053bb016cc6e1259a |
| 50070 | 2026-09-12T03:40:06.259Z | managed_process_admitted |  |  | owner=default |
| 50071 | 2026-09-12T03:40:06.584Z | managed_process_started |  |  | owner=default |
| 50072 | 2026-09-12T03:40:24.430Z | managed_process_terminal |  |  | owner=default |
| 50073 | 2026-09-12T03:40:25.845Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=fc1b368138735ea26016f8731fb8f4e3307addb0025f3f6053bb016cc6e1259a |
| 50074 | 2026-09-12T03:40:26.854Z | observation_span_recorded |  |  |  |
| 50075 | 2026-09-12T03:40:27.069Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 50076 | 2026-09-12T03:41:54.922Z | managed_process_admitted |  |  | owner=default |
| 50077 | 2026-09-12T03:41:55.260Z | managed_process_started |  |  | owner=default |
| 50078 | 2026-09-12T03:41:58.034Z | managed_process_terminal |  |  | owner=default |
| 50079 | 2026-09-12T03:42:11.669Z | quality_outcome_recorded |  |  |  |
| 50080 | 2026-09-12T03:42:11.859Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 50081 | 2026-09-12T03:42:12.126Z | observation_span_recorded |  |  |  |
| 50082 | 2026-09-12T03:42:12.325Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | fc1b368138735ea26016f8731fb8f4e3307addb0025f3f6053bb016cc6e1259a | False | 19547 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| bcb4abd1ac984fa89b8a90bbb2e3690a | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | c67c06dfb6fe7b46b983164f7ed14f7cbc99c7509472e7fb593a90b86c5d232b | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `30`
- Chain head: `86c874cc4b393ef69bf4a61be1c1d87587bde23a479dbf3add27f334c146e856`
