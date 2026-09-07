# Orchestration Wave 1

- Run: `2fb97c02bc6b4125b7148785335c57d9`
- Wave: `45a1d77efc014ce0b613043597f69d50`
- Objective: Fix controlled supervisor restart propagation so allow_acceptance_pending survives from task_control restart_runtime into the durable restart ticket and then into FullCleanActivation. Preserve authorized-child exact-stale target_workspace behavior and all unrelated PRL/dashboard WIP. Add focused regression proof; do not run a runtime restart in this engineering wave.
- Objective revision: `1`
- Objective SHA-256: `71a4bfe9a4f4895235f394a102aa760a2215f7fc9f42aa5d16940e17db3e7fd5`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `58dfd3093d7a05f6999fe93e15c94050aa51d204`
- Worktree fingerprint: `011676ec3065255b19fd2ba0f0b77b4f4accfc973ab1db17a5e8ee042157ea5b`
- Contract fingerprint: ``
- Status: **active**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 43537 | 2026-09-07T11:04:25.324Z | run_started |  | PREFLIGHT |  |
| 43538 | 2026-09-07T11:04:26.183Z | observation_span_recorded |  |  |  |
| 43539 | 2026-09-07T11:04:26.644Z | solution_shadow_recommended |  |  |  |
| 43540 | 2026-09-07T11:04:27.848Z | observation_span_recorded |  |  |  |
| 43541 | 2026-09-07T11:04:28.362Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 43542 | 2026-09-07T11:04:28.699Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 43543 | 2026-09-07T11:04:29.703Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 43544 | 2026-09-07T11:04:29.869Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 43545 | 2026-09-07T11:04:30.076Z | state_transition | READY | ROUTED | reason=route_selected |
| 43546 | 2026-09-07T11:04:30.500Z | observation_span_recorded |  |  |  |
| 43547 | 2026-09-07T11:04:31.180Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=35cbafa1b3b84b48b831657d22f4a7c2 |
| 43548 | 2026-09-07T11:04:31.352Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 43549 | 2026-09-07T11:04:32.369Z | patch_surface_observed |  |  |  |
| 43550 | 2026-09-07T11:04:32.558Z | observation_span_recorded |  |  |  |
| 43551 | 2026-09-07T11:04:32.815Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=35cbafa1b3b84b48b831657d22f4a7c2 |
| 43552 | 2026-09-07T11:04:32.965Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 43553 | 2026-09-07T11:04:33.614Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=88bc9fd0d324dce8a8d257e25084bebbfa75887da0a97c4ad7c01d2d49798bf5 |
| 43554 | 2026-09-07T11:04:34.282Z | managed_process_admitted |  |  | owner=default |
| 43555 | 2026-09-07T11:04:34.813Z | managed_process_started |  |  | owner=default |
| 43556 | 2026-09-07T11:04:46.035Z | managed_process_terminal |  |  | owner=default |
| 43557 | 2026-09-07T11:04:56.266Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=88bc9fd0d324dce8a8d257e25084bebbfa75887da0a97c4ad7c01d2d49798bf5 |
| 43558 | 2026-09-07T11:04:57.278Z | observation_span_recorded |  |  |  |
| 43559 | 2026-09-07T11:04:57.455Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 43560 | 2026-09-07T11:13:56.421Z | managed_process_admitted |  |  | owner=default |
| 43561 | 2026-09-07T11:13:56.827Z | managed_process_started |  |  | owner=default |
| 43562 | 2026-09-07T11:14:31.578Z | managed_process_terminal |  |  | owner=default |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 88bc9fd0d324dce8a8d257e25084bebbfa75887da0a97c4ad7c01d2d49798bf5 | False | 22187 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `26`
- Chain head: `f49dfe3db9bfaffb7b1d8a515923ef357bbf77fee9652ab5aadd683ef2b62777`
