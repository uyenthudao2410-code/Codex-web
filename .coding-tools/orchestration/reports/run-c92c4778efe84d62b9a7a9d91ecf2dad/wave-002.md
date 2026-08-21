# Orchestration Wave 2

- Run: `c92c4778efe84d62b9a7a9d91ecf2dad`
- Wave: `f872a674c10940cd840d94e65caf3924`
- Objective: C1 Executable Engineering Casebook repair only: keep the one-file ordinary unittest casebook and correct Case 01 to match the actual accepted T1 API. `wave_objective_provenance()` intentionally returns wave-local provenance only; the immutable run initial objective must be read from `ledger.get_run(run_id)`. Remove the invalid `provenance['run_initial_objective']` assertion while retaining assertions that the run objective is immutable, the new wave effective objective changes, revision becomes 2, hash is valid, and source is `replan_request`. No production code or scope expansion.
- Objective revision: `2`
- Objective SHA-256: `0dc75ccf5e022ce62627f7355435b8480a0528bb9a43d7f613bedefcf05a4ae8`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `36ce22300aa4cb628d84d895942aeafd35b6bde6`
- Worktree fingerprint: `1a8ebc8c8ae103c3dcbb64460e8be739479480a99d690365092a00861d13a93b`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 26228 | 2026-08-21T07:53:50.407Z | wave_replanned |  | PREFLIGHT | reason=Focused C1 proof failed only because the new test expected a non-existent `run_initial_objective` key from the wave-local provenance helper. The accepted implementation keeps immutable initial objective on the run row and returns only wave-local provenance. Repair the test fixture/assertion, not production code. |
| 26229 | 2026-08-21T07:53:51.191Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 26230 | 2026-08-21T07:54:18.579Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 26231 | 2026-08-21T07:54:18.742Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 26232 | 2026-08-21T07:54:18.909Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 26233 | 2026-08-21T07:54:19.131Z | state_transition | READY | ROUTED | reason=route_selected |
| 26234 | 2026-08-21T07:54:19.555Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=a7512aeb040146b6a1787689b0438d1e |
| 26235 | 2026-08-21T07:54:19.806Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 26236 | 2026-08-21T07:54:20.172Z | patch_surface_observed |  |  |  |
| 26237 | 2026-08-21T07:54:20.422Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=a7512aeb040146b6a1787689b0438d1e |
| 26238 | 2026-08-21T07:54:20.619Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 26239 | 2026-08-21T07:54:21.019Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=c39c814820a24bfd89140b3c955f313903c4ecdeda4a1fdb924e0234ae8d7ea0 |
| 26240 | 2026-08-21T07:54:21.320Z | managed_process_admitted |  |  | owner=default |
| 26241 | 2026-08-21T07:54:21.597Z | managed_process_started |  |  | owner=default |
| 26242 | 2026-08-21T07:54:24.406Z | managed_process_terminal |  |  | owner=default |
| 26243 | 2026-08-21T07:54:25.683Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=c39c814820a24bfd89140b3c955f313903c4ecdeda4a1fdb924e0234ae8d7ea0 |
| 26244 | 2026-08-21T07:54:26.160Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 26245 | 2026-08-21T07:55:00.603Z | quality_outcome_recorded |  |  |  |
| 26246 | 2026-08-21T07:55:00.753Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 26247 | 2026-08-21T07:55:01.086Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | c39c814820a24bfd89140b3c955f313903c4ecdeda4a1fdb924e0234ae8d7ea0 | False | 4233 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| a7bb97928def4e3199c5814224b2d8af | accepted | 36ce22300aa4cb628d84d895942aeafd35b6bde6 | 114c4ac90e42d4cb120851bd971dde822ca4125f31410d7a29c40b14b031802f | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `40`
- Chain head: `194ae76fee4d7ef24e353c2ba444ac09f9341dcd0fdb980fefcd41603cf4bb3f`
