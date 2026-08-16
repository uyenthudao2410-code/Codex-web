# Orchestration Wave 8

- Run: `8493048d89c048aeaa44f45be14fbc14`
- Wave: `c359b9d045744318b8605240ea751229`
- Objective: Prepare the narrow R2B automatic server-preferred dispatch slice on top of accepted server_compute opt-in. Inspect current Cargo read-only validation flow and compute placement adapter to implement source-authoritative HEAVY offload only for cargo_check/cargo_test when timeout has durable-job handoff headroom and sandbox is absent. Source Runner must supply full clean exact HEAD; candidate compute Runner must be a different Runner, explicitly server_compute=true, same logical project id, exact same full clean HEAD, structured validation + exact-source capable, fresh and within known job capacity. If no eligible target, preserve current source Runner behavior. No cross-runner retry, no dirty snapshot, no mutating cargo_fmt offload, no public tool schema changes. Determine exact current methods for listing auth-visible clients/jobs and canonical runtime project resolution, and exact test helpers for multi-runner validation dispatch.
- Mode: `mcp_only`
- Base HEAD: `cf6cb6ddbf29d90515d003ce72490ffda985c37f`
- Worktree fingerprint: `5c0ad99281311c93d0fafecdb6e6fc8b86bce80d2789c0d766eadb9c90a7a7d4`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 8163 | 2026-08-16T13:04:20.905Z | wave_replanned |  | PREFLIGHT | reason=Establish a fresh PREPARE wave after the read-only formatting check so retained command output can be consumed without retrying the failed formatter. |
| 8164 | 2026-08-16T13:04:21.048Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 8165 | 2026-08-16T13:04:38.535Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 8166 | 2026-08-16T13:04:38.655Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 8167 | 2026-08-16T13:04:38.807Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 8168 | 2026-08-16T13:04:38.937Z | state_transition | READY | ROUTED | reason=route_selected |
| 8169 | 2026-08-16T13:04:39.430Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=877a9ab5aa6543e0a413720aaf257fb1 |
| 8170 | 2026-08-16T13:04:39.529Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 8171 | 2026-08-16T13:04:40.980Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=877a9ab5aa6543e0a413720aaf257fb1 |
| 8172 | 2026-08-16T13:04:41.550Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 8173 | 2026-08-16T13:04:42.047Z | proof_cache_miss |  |  | reason=cold; stage_id=check:04a4ddddbf955f2e; input_fingerprint=2326ed6bdde2abd8f5c054139209b5cbc50ebc7069d1a18e702db4caed63b640 |
| 8174 | 2026-08-16T13:04:42.393Z | managed_process_admitted |  |  | owner=default |
| 8175 | 2026-08-16T13:04:42.666Z | managed_process_started |  |  | owner=default |
| 8176 | 2026-08-16T13:04:43.133Z | managed_process_terminal |  |  | owner=default |
| 8177 | 2026-08-16T13:04:43.397Z | proof_recorded |  |  | stage_id=check:04a4ddddbf955f2e; status=failed; cache_hit=False; input_fingerprint=2326ed6bdde2abd8f5c054139209b5cbc50ebc7069d1a18e702db4caed63b640 |
| 8178 | 2026-08-16T13:04:43.513Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 8179 | 2026-08-16T13:04:43.630Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 8180 | 2026-08-16T13:04:43.762Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:04a4ddddbf955f2e | failed | 2326ed6bdde2abd8f5c054139209b5cbc50ebc7069d1a18e702db4caed63b640 | False | 1053 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `172`
- Chain head: `e7827db97a33ae955a83687a56516ee6906376b1ec5710730e6ea409f48dc24d`
