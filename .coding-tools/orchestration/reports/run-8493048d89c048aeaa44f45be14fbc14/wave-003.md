# Orchestration Wave 3

- Run: `8493048d89c048aeaa44f45be14fbc14`
- Wave: `d5356ba14b2041be95c4ac94ebfd688b`
- Objective: Prepare the narrow R2B automatic server-preferred dispatch slice on top of accepted server_compute opt-in. Inspect current Cargo read-only validation flow and compute placement adapter to implement source-authoritative HEAVY offload only for cargo_check/cargo_test when timeout has durable-job handoff headroom and sandbox is absent. Source Runner must supply full clean exact HEAD; candidate compute Runner must be a different Runner, explicitly server_compute=true, same logical project id, exact same full clean HEAD, structured validation + exact-source capable, fresh and within known job capacity. If no eligible target, preserve current source Runner behavior. No cross-runner retry, no dirty snapshot, no mutating cargo_fmt offload, no public tool schema changes. Determine exact current methods for listing auth-visible clients/jobs and canonical runtime project resolution, and exact test helpers for multi-runner validation dispatch.
- Mode: `mcp_only`
- Base HEAD: `cf6cb6ddbf29d90515d003ce72490ffda985c37f`
- Worktree fingerprint: `62a1615cd6c370925c02143411a0fee9bca15a9e6b8cf3685083824921c6a913`
- Contract fingerprint: `e30758163c30fa30d691efc6bafea7b974302b7d76c618ea0bfb05e69334d5da`
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 8080 | 2026-08-16T13:01:57.305Z | wave_replanned |  | PREFLIGHT | reason=The previous deterministic wave was rejected during patch preflight because the test insertion anchor matched five generic assertions. No files were written. Use a unique boundary anchored by exact_source_capable_dirty_validation_fails_before_enqueue followed by wait_for_agent_request; keep the implementation and proof plan unchanged. |
| 8081 | 2026-08-16T13:01:57.413Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 8082 | 2026-08-16T13:01:57.546Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 8083 | 2026-08-16T13:01:57.680Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 8084 | 2026-08-16T13:01:57.822Z | state_transition | READY | ROUTED | reason=route_selected |
| 8085 | 2026-08-16T13:01:58.313Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=1f67ec1432c443fbbb6b11d9d754ef58 |
| 8086 | 2026-08-16T13:01:58.399Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 8087 | 2026-08-16T13:01:59.071Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=1f67ec1432c443fbbb6b11d9d754ef58 |
| 8088 | 2026-08-16T13:01:59.165Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 8089 | 2026-08-16T13:01:59.629Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:810e75f0d3dee10e; input_fingerprint=4eef262aba6e7c066abf9ea7af6ae7322c7ac9b2e4b08c6a1d3bb43e6283bdf8 |
| 8090 | 2026-08-16T13:01:59.879Z | managed_process_admitted |  |  | owner=default |
| 8091 | 2026-08-16T13:02:00.142Z | managed_process_started |  |  | owner=default |
| 8092 | 2026-08-16T13:02:06.811Z | managed_process_terminal |  |  | owner=default |
| 8093 | 2026-08-16T13:02:07.056Z | proof_recorded |  |  | stage_id=check:810e75f0d3dee10e; status=failed; cache_hit=False; input_fingerprint=4eef262aba6e7c066abf9ea7af6ae7322c7ac9b2e4b08c6a1d3bb43e6283bdf8 |
| 8094 | 2026-08-16T13:02:07.220Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 8095 | 2026-08-16T13:02:07.332Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 8096 | 2026-08-16T13:02:07.453Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:810e75f0d3dee10e | failed | 4eef262aba6e7c066abf9ea7af6ae7322c7ac9b2e4b08c6a1d3bb43e6283bdf8 | False | 7207 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `172`
- Chain head: `e7827db97a33ae955a83687a56516ee6906376b1ec5710730e6ea409f48dc24d`
