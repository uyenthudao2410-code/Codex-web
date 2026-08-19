# Orchestration Wave 2

- Run: `ed50decef66646f6a1e2e777f1228954`
- Wave: `60f0de5edda84a1abedc86d8e323ce36`
- Objective: Implement ChatWeb exact token-usage ingress only. Inspect current source and produce the smallest causal patch: accept one namespaced controller usage object from tools/call params._meta only for ChatWeb identity; validate it before dispatch via usage_event_from_controller_report semantics; for an already-active scoped run/wave require current controller lease and record before business dispatch; for the first agent_workflow request validate before dispatch then bind/claim and record after that call creates a run/wave; annotate JSON-RPC result._meta with recorded/duplicate status and usage_id/turn_id but never raw telemetry. Duplicate same evidence is idempotent; conflicting same turn_id fails closed. Missing telemetry remains unknown. Preserve smart-v3 8-tool public surface, isolation, pricing/ledger WIP. No dashboard/restart/commit/push.
- Mode: `mcp_only`
- Base HEAD: `930d3e1e67f2b413aa32d5da99d1a01d22d0bddc`
- Worktree fingerprint: `6d69123b82f9a20c27688f887933532486ace41853b7cf85c592328671d73cac`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 21360 | 2026-08-19T09:46:11.889Z | wave_replanned |  | PREFLIGHT | reason=Wave 1 applied the intended ingress semantics but verification failed only at the module-size guard because mcp_http_handler.py grew by about 100 helper lines. Extract those helpers into a dedicated controller_usage_ingress.py domain module and leave only thin wiring in the handler; rerun the complete focused proof on the changed source. |
| 21361 | 2026-08-19T09:46:12.095Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 21362 | 2026-08-19T09:46:12.264Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 21363 | 2026-08-19T09:46:12.414Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 21364 | 2026-08-19T09:46:12.559Z | state_transition | READY | ROUTED | reason=route_selected |
| 21365 | 2026-08-19T09:46:13.061Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=73cee799174841228374af2ac44686b3 |
| 21366 | 2026-08-19T09:46:13.193Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 21367 | 2026-08-19T09:46:13.583Z | patch_surface_observed |  |  |  |
| 21368 | 2026-08-19T09:46:13.822Z | patch_surface_observed |  |  |  |
| 21369 | 2026-08-19T09:46:14.103Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=73cee799174841228374af2ac44686b3 |
| 21370 | 2026-08-19T09:46:14.226Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 21371 | 2026-08-19T09:46:14.612Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=86d5dd56645c18c0a79c91318a8bad4f2c86893778e3fde3ae735b9c8ac5b147 |
| 21372 | 2026-08-19T09:46:15.060Z | managed_process_admitted |  |  | owner=default |
| 21373 | 2026-08-19T09:46:15.340Z | managed_process_started |  |  | owner=default |
| 21374 | 2026-08-19T09:46:29.762Z | managed_process_terminal |  |  | owner=default |
| 21375 | 2026-08-19T09:46:30.061Z | proof_recorded |  |  | stage_id=verify:tests; status=failed; cache_hit=False; input_fingerprint=86d5dd56645c18c0a79c91318a8bad4f2c86893778e3fde3ae735b9c8ac5b147 |
| 21376 | 2026-08-19T09:46:30.255Z | failure_observed | PROVING | PROVING | failure_class=BUILD_VERIFICATION_FAILED |
| 21377 | 2026-08-19T09:46:30.450Z | state_transition | PROVING | REPLAN | reason=BUILD_VERIFICATION_FAILED; failure_class=BUILD_VERIFICATION_FAILED |
| 21378 | 2026-08-19T09:46:30.618Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | failed | 86d5dd56645c18c0a79c91318a8bad4f2c86893778e3fde3ae735b9c8ac5b147 | False | 15094 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `70`
- Chain head: `336f83fdf2e69e728398753d4f78f33b8d9053e620656fa659198167d46072da`
