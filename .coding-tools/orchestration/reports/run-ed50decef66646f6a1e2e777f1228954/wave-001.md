# Orchestration Wave 1

- Run: `ed50decef66646f6a1e2e777f1228954`
- Wave: `13523ed5108b49b1b5ce17b2507748e9`
- Objective: Implement ChatWeb exact token-usage ingress only. Inspect current source and produce the smallest causal patch: accept one namespaced controller usage object from tools/call params._meta only for ChatWeb identity; validate it before dispatch via usage_event_from_controller_report semantics; for an already-active scoped run/wave require current controller lease and record before business dispatch; for the first agent_workflow request validate before dispatch then bind/claim and record after that call creates a run/wave; annotate JSON-RPC result._meta with recorded/duplicate status and usage_id/turn_id but never raw telemetry. Duplicate same evidence is idempotent; conflicting same turn_id fails closed. Missing telemetry remains unknown. Preserve smart-v3 8-tool public surface, isolation, pricing/ledger WIP. No dashboard/restart/commit/push.
- Mode: `mcp_only`
- Base HEAD: `930d3e1e67f2b413aa32d5da99d1a01d22d0bddc`
- Worktree fingerprint: `6c5f6f0d890b3854b961e4113dce989d305c160d084d3f767571e72a25c21c40`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 21335 | 2026-08-19T09:39:29.612Z | run_started |  | PREFLIGHT |  |
| 21336 | 2026-08-19T09:39:31.008Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 21337 | 2026-08-19T09:40:54.419Z | managed_process_admitted |  |  | owner=default |
| 21338 | 2026-08-19T09:40:54.723Z | managed_process_started |  |  | owner=default |
| 21339 | 2026-08-19T09:40:56.321Z | managed_process_terminal |  |  | owner=default |
| 21340 | 2026-08-19T09:41:10.776Z | solution_shadow_recommended |  |  |  |
| 21341 | 2026-08-19T09:44:47.948Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 21342 | 2026-08-19T09:44:48.083Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 21343 | 2026-08-19T09:44:48.207Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 21344 | 2026-08-19T09:44:48.384Z | state_transition | READY | ROUTED | reason=route_selected |
| 21345 | 2026-08-19T09:44:48.833Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=8eba6dbe7594457e9f5275911273c08f |
| 21346 | 2026-08-19T09:44:49.043Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 21347 | 2026-08-19T09:44:49.503Z | patch_surface_observed |  |  |  |
| 21348 | 2026-08-19T09:44:49.735Z | patch_surface_observed |  |  |  |
| 21349 | 2026-08-19T09:44:49.914Z | patch_surface_observed |  |  |  |
| 21350 | 2026-08-19T09:44:50.151Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=8eba6dbe7594457e9f5275911273c08f |
| 21351 | 2026-08-19T09:44:50.341Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 21352 | 2026-08-19T09:44:50.745Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=b32e9f2a24d038d7649af1cde1e43e4f67cdd4dfbccdc5cd21ccb156c52c3b90 |
| 21353 | 2026-08-19T09:44:51.109Z | managed_process_admitted |  |  | owner=default |
| 21354 | 2026-08-19T09:44:51.399Z | managed_process_started |  |  | owner=default |
| 21355 | 2026-08-19T09:45:06.588Z | managed_process_terminal |  |  | owner=default |
| 21356 | 2026-08-19T09:45:06.905Z | proof_recorded |  |  | stage_id=verify:tests; status=failed; cache_hit=False; input_fingerprint=b32e9f2a24d038d7649af1cde1e43e4f67cdd4dfbccdc5cd21ccb156c52c3b90 |
| 21357 | 2026-08-19T09:45:07.444Z | failure_observed | PROVING | PROVING | failure_class=BUILD_VERIFICATION_FAILED |
| 21358 | 2026-08-19T09:45:07.567Z | state_transition | PROVING | REPLAN | reason=BUILD_VERIFICATION_FAILED; failure_class=BUILD_VERIFICATION_FAILED |
| 21359 | 2026-08-19T09:45:07.722Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | failed | b32e9f2a24d038d7649af1cde1e43e4f67cdd4dfbccdc5cd21ccb156c52c3b90 | False | 15889 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `70`
- Chain head: `336f83fdf2e69e728398753d4f78f33b8d9053e620656fa659198167d46072da`
