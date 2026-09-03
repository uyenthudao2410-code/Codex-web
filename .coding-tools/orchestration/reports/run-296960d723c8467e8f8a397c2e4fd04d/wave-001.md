# Orchestration Wave 1

- Run: `296960d723c8467e8f8a397c2e4fd04d`
- Wave: `62d5206451764b42a2265265b06a0127`
- Objective: W6 of docs/research/260901_CODING_WEB_TOKEN_USAGE_COST_CONTEXT_OBSERVABILITY_AND_ACCEPTED_RESULT_EFFICIENCY_MASTER_PLAN.md: implement correlation plus accepted-result economics on the exact current Codex-web source. Correlate controller/provider/tool observability with stable available session/turn/task/RUN/WAVE/trace identities and the EOCL accepted/checkpointed lifecycle. Compute accepted-result economics only from exact measured token/cost components; preserve unavailable components as unknown/unobserved (never zero, never infer tokens from bytes). Preserve W1-W5 semantics, current public MCP tool_count=8, and fail-closed provenance. Localize the smallest bounded implementation and focused deterministic proof. Do not mutate source during prepare. No commit, push, restart, package, release, or deploy.
- Objective revision: `1`
- Objective SHA-256: `e7cf2f6b2760b525d806f742f2c574e8f2b8d9809285eb5a07666860d32a6543`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `30b7d1b971b65034d3e4c95568c970fcc0e9380c`
- Worktree fingerprint: `3e2c07e197923777244ff838d727d1e11c5f6390901d854e8f05ce94d9604f1d`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 34521 | 2026-09-01T10:38:45.377Z | run_started |  | PREFLIGHT |  |
| 34522 | 2026-09-01T10:38:45.793Z | observation_span_recorded |  |  |  |
| 34523 | 2026-09-01T10:38:47.048Z | observation_span_recorded |  |  |  |
| 34524 | 2026-09-01T10:38:47.295Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 34525 | 2026-09-01T11:10:08.662Z | solution_shadow_recommended |  |  |  |
| 34526 | 2026-09-01T11:10:08.916Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 34527 | 2026-09-01T11:10:09.128Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 34528 | 2026-09-01T11:10:09.385Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 34529 | 2026-09-01T11:10:09.614Z | state_transition | READY | ROUTED | reason=route_selected |
| 34530 | 2026-09-01T11:10:09.835Z | observation_span_recorded |  |  |  |
| 34531 | 2026-09-01T11:10:10.720Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=f45970cf5e9448a9b543b402b13141ae |
| 34532 | 2026-09-01T11:10:10.955Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 34533 | 2026-09-01T11:10:11.796Z | patch_surface_observed |  |  |  |
| 34534 | 2026-09-01T11:10:12.020Z | patch_surface_observed |  |  |  |
| 34535 | 2026-09-01T11:10:12.287Z | patch_surface_observed |  |  |  |
| 34536 | 2026-09-01T11:10:12.465Z | observation_span_recorded |  |  |  |
| 34537 | 2026-09-01T11:10:12.830Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=f45970cf5e9448a9b543b402b13141ae |
| 34538 | 2026-09-01T11:10:13.011Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 34539 | 2026-09-01T11:10:13.685Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=792b936da60a0c76e43d0efa09f193e352afc94e13d8897796601a54abaea2a6 |
| 34540 | 2026-09-01T11:10:14.023Z | managed_process_admitted |  |  | owner=default |
| 34541 | 2026-09-01T11:10:14.348Z | managed_process_started |  |  | owner=default |
| 34542 | 2026-09-01T11:10:16.290Z | managed_process_terminal |  |  | owner=default |
| 34543 | 2026-09-01T11:10:17.549Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=792b936da60a0c76e43d0efa09f193e352afc94e13d8897796601a54abaea2a6 |
| 34544 | 2026-09-01T11:10:18.479Z | observation_span_recorded |  |  |  |
| 34545 | 2026-09-01T11:10:18.658Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 34546 | 2026-09-01T14:25:49.665Z | quality_outcome_recorded |  |  |  |
| 34547 | 2026-09-01T14:25:49.838Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 34548 | 2026-09-01T14:25:50.082Z | observation_span_recorded |  |  |  |
| 34549 | 2026-09-01T14:25:50.304Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 792b936da60a0c76e43d0efa09f193e352afc94e13d8897796601a54abaea2a6 | False | 3468 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 5c65470e016e42f7858c80d250b1ceb9 | accepted | 30b7d1b971b65034d3e4c95568c970fcc0e9380c | 7a2440f2420567c20733d30d91ec15f2c6cb3a0b3350e83fe4521a504e2020f7 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `29`
- Chain head: `bdcd0bbbb0eff9cbaff6ac51af910570eae667ed750b177e693147ad438db82b`
