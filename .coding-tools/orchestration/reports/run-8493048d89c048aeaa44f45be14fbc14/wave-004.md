# Orchestration Wave 4

- Run: `8493048d89c048aeaa44f45be14fbc14`
- Wave: `361e51fe83124b508dfdc3291faad23b`
- Objective: Prepare the narrow R2B automatic server-preferred dispatch slice on top of accepted server_compute opt-in. Inspect current Cargo read-only validation flow and compute placement adapter to implement source-authoritative HEAVY offload only for cargo_check/cargo_test when timeout has durable-job handoff headroom and sandbox is absent. Source Runner must supply full clean exact HEAD; candidate compute Runner must be a different Runner, explicitly server_compute=true, same logical project id, exact same full clean HEAD, structured validation + exact-source capable, fresh and within known job capacity. If no eligible target, preserve current source Runner behavior. No cross-runner retry, no dirty snapshot, no mutating cargo_fmt offload, no public tool schema changes. Determine exact current methods for listing auth-visible clients/jobs and canonical runtime project resolution, and exact test helpers for multi-runner validation dispatch.
- Mode: `mcp_only`
- Base HEAD: `cf6cb6ddbf29d90515d003ce72490ffda985c37f`
- Worktree fingerprint: `cfcf97910bb1843bd51510767e5a0f35ce202c2e3a9fe16bea20cae1f1383992`
- Contract fingerprint: `e30758163c30fa30d691efc6bafea7b974302b7d76c618ea0bfb05e69334d5da`
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 8097 | 2026-08-16T13:02:17.945Z | wave_replanned |  | PREFLIGHT | reason=The implementation patch applied successfully. The only observed failure is cargo fmt --check, so the next wave changes strategy from patching behavior to deterministic rustfmt of the already-written files, then resumes compile/test proof. This is not an unchanged retry. |
| 8098 | 2026-08-16T13:02:18.196Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 8099 | 2026-08-16T13:02:18.335Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 8100 | 2026-08-16T13:02:18.589Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 8101 | 2026-08-16T13:02:18.746Z | state_transition | READY | ROUTED | reason=route_selected |
| 8102 | 2026-08-16T13:02:19.254Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=756e8d4c7d8c4194be883cd864e41fba |
| 8103 | 2026-08-16T13:02:19.360Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 8104 | 2026-08-16T13:02:19.938Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=756e8d4c7d8c4194be883cd864e41fba |
| 8105 | 2026-08-16T13:02:20.046Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 8106 | 2026-08-16T13:02:20.496Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:718b79fbd1bef7b9; input_fingerprint=68c8e00222d83cd34a7e3b31ef66f401a7971c3285fd17858bc7e86999d9a537 |
| 8107 | 2026-08-16T13:02:20.854Z | managed_process_admitted |  |  | owner=default |
| 8108 | 2026-08-16T13:02:21.094Z | managed_process_started |  |  | owner=default |
| 8109 | 2026-08-16T13:02:28.079Z | managed_process_terminal |  |  | owner=default |
| 8110 | 2026-08-16T13:02:28.329Z | proof_recorded |  |  | stage_id=check:718b79fbd1bef7b9; status=failed; cache_hit=False; input_fingerprint=68c8e00222d83cd34a7e3b31ef66f401a7971c3285fd17858bc7e86999d9a537 |
| 8111 | 2026-08-16T13:02:28.450Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 8112 | 2026-08-16T13:02:28.566Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 8113 | 2026-08-16T13:02:28.690Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:718b79fbd1bef7b9 | failed | 68c8e00222d83cd34a7e3b31ef66f401a7971c3285fd17858bc7e86999d9a537 | False | 7550 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `172`
- Chain head: `e7827db97a33ae955a83687a56516ee6906376b1ec5710730e6ea409f48dc24d`
