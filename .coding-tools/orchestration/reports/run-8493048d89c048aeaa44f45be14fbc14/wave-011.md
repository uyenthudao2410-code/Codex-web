# Orchestration Wave 11

- Run: `8493048d89c048aeaa44f45be14fbc14`
- Wave: `5b266a072e304b44b0aab3de02b7d9e3`
- Objective: Prepare the narrow R2B automatic server-preferred dispatch slice on top of accepted server_compute opt-in. Inspect current Cargo read-only validation flow and compute placement adapter to implement source-authoritative HEAVY offload only for cargo_check/cargo_test when timeout has durable-job handoff headroom and sandbox is absent. Source Runner must supply full clean exact HEAD; candidate compute Runner must be a different Runner, explicitly server_compute=true, same logical project id, exact same full clean HEAD, structured validation + exact-source capable, fresh and within known job capacity. If no eligible target, preserve current source Runner behavior. No cross-runner retry, no dirty snapshot, no mutating cargo_fmt offload, no public tool schema changes. Determine exact current methods for listing auth-visible clients/jobs and canonical runtime project resolution, and exact test helpers for multi-runner validation dispatch.
- Mode: `mcp_only`
- Base HEAD: `cf6cb6ddbf29d90515d003ce72490ffda985c37f`
- Worktree fingerprint: `bc6e4ed5ecaefa49f6a3ab53db6022f144261c8e3f69ed37432c2caed989ae87`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 8467 | 2026-08-16T13:58:37.887Z | wave_replanned |  | PREFLIGHT | reason=The R2B proof-lifecycle investigation exposed a distinct durable resource leak: activation preflight reports active_managed_processes=1 while OS cargo/rustc/link processes are absent. Current ExecutionResourceGovernor skips foreign-runtime rows before stale-start reconciliation and can keep an unbound starting/root_pid=0 row active forever. This wave changes the failure strategy by fixing conservative stale admission reconciliation and providing a bounded on-disk reconciliation CLI so the accepted runtime fix can be activated safely; it does not retry the prior monolithic proof. |
| 8468 | 2026-08-16T13:58:38.028Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 8469 | 2026-08-16T13:58:38.392Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 8470 | 2026-08-16T13:58:38.961Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 8471 | 2026-08-16T13:58:39.221Z | state_transition | READY | ROUTED | reason=route_selected |
| 8472 | 2026-08-16T13:58:40.054Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=5d62b0d262234dbeb10165d723455871 |
| 8473 | 2026-08-16T13:58:40.168Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 8474 | 2026-08-16T13:58:40.884Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=5d62b0d262234dbeb10165d723455871 |
| 8475 | 2026-08-16T13:58:41.201Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 8476 | 2026-08-16T13:58:41.995Z | proof_cache_miss |  |  | reason=cold; stage_id=check:2c66d1233cd6e430; input_fingerprint=5e99a64fb4ea273a4b871a349d3bf7c43211543cec2fa82e195a3c5d3d5c5d37 |
| 8477 | 2026-08-16T13:58:42.446Z | managed_process_admitted |  |  | owner=default |
| 8478 | 2026-08-16T13:58:42.716Z | managed_process_started |  |  | owner=default |
| 8479 | 2026-08-16T13:58:43.088Z | managed_process_terminal |  |  | owner=default |
| 8480 | 2026-08-16T13:58:43.372Z | proof_recorded |  |  | stage_id=check:2c66d1233cd6e430; status=passed; cache_hit=False; input_fingerprint=5e99a64fb4ea273a4b871a349d3bf7c43211543cec2fa82e195a3c5d3d5c5d37 |
| 8481 | 2026-08-16T13:58:43.645Z | proof_cache_miss |  |  | reason=cold; stage_id=check:b373bbf17756562b; input_fingerprint=cad886e1402d5107ddf2b4243fdbb92530e8b45451149ec8d9dc359dbf69e98a |
| 8482 | 2026-08-16T13:58:44.098Z | managed_process_admitted |  |  | owner=default |
| 8483 | 2026-08-16T13:58:44.607Z | managed_process_started |  |  | owner=default |
| 8484 | 2026-08-16T13:58:51.924Z | managed_process_terminal |  |  | owner=default |
| 8485 | 2026-08-16T13:58:52.195Z | proof_recorded |  |  | stage_id=check:b373bbf17756562b; status=passed; cache_hit=False; input_fingerprint=cad886e1402d5107ddf2b4243fdbb92530e8b45451149ec8d9dc359dbf69e98a |
| 8486 | 2026-08-16T13:58:53.331Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 8487 | 2026-08-16T13:59:10.790Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 8488 | 2026-08-16T13:59:11.376Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:2c66d1233cd6e430 | passed | 5e99a64fb4ea273a4b871a349d3bf7c43211543cec2fa82e195a3c5d3d5c5d37 | False | 941 | 0 |
| check:b373bbf17756562b | passed | cad886e1402d5107ddf2b4243fdbb92530e8b45451149ec8d9dc359dbf69e98a | False | 8225 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 78286bcad874456b916e5c1bc3932a58 | accepted | cf6cb6ddbf29d90515d003ce72490ffda985c37f | f2fff591792393621e2d77d202d4c3c9937c6153b57da7fda8c9eb3dcf197d40 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `172`
- Chain head: `e7827db97a33ae955a83687a56516ee6906376b1ec5710730e6ea409f48dc24d`
