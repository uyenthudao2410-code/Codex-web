# Orchestration Wave 3

- Run: `ed50decef66646f6a1e2e777f1228954`
- Wave: `68b99181913b4871916e805a7cc2346b`
- Objective: Implement ChatWeb exact token-usage ingress only. Inspect current source and produce the smallest causal patch: accept one namespaced controller usage object from tools/call params._meta only for ChatWeb identity; validate it before dispatch via usage_event_from_controller_report semantics; for an already-active scoped run/wave require current controller lease and record before business dispatch; for the first agent_workflow request validate before dispatch then bind/claim and record after that call creates a run/wave; annotate JSON-RPC result._meta with recorded/duplicate status and usage_id/turn_id but never raw telemetry. Duplicate same evidence is idempotent; conflicting same turn_id fails closed. Missing telemetry remains unknown. Preserve smart-v3 8-tool public surface, isolation, pricing/ledger WIP. No dashboard/restart/commit/push.
- Mode: `mcp_only`
- Base HEAD: `930d3e1e67f2b413aa32d5da99d1a01d22d0bddc`
- Worktree fingerprint: `4a52db54d7bd753bfe63b3f2616f3e420fb9463589bc46a9e561a8b5ef3623e3`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 21379 | 2026-08-19T09:47:12.380Z | wave_replanned |  | PREFLIGHT | reason=Wave 2 preserved ingress semantics and extracted 92 lines into controller_usage_ingress.py, but fresh verification still failed solely at module-size policy. Direct guard execution is not admitted from REPLAN, so create a new PREFLIGHT wave to obtain exact current module budget evidence before the next mutation. |
| 21380 | 2026-08-19T09:47:12.938Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 21381 | 2026-08-19T09:48:19.648Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 21382 | 2026-08-19T09:48:19.822Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 21383 | 2026-08-19T09:48:20.008Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 21384 | 2026-08-19T09:48:20.210Z | state_transition | READY | ROUTED | reason=route_selected |
| 21385 | 2026-08-19T09:48:20.602Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=d5b262d7551346d6baf5fea05272f9eb |
| 21386 | 2026-08-19T09:48:20.729Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 21387 | 2026-08-19T09:48:21.130Z | patch_surface_observed |  |  |  |
| 21388 | 2026-08-19T09:48:21.353Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=d5b262d7551346d6baf5fea05272f9eb |
| 21389 | 2026-08-19T09:48:21.501Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 21390 | 2026-08-19T09:48:21.859Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=ba390f034b59d76614d7a76469ba208c9927b85237767fa9fc5b0cb4485ef4d4 |
| 21391 | 2026-08-19T09:48:22.158Z | managed_process_admitted |  |  | owner=default |
| 21392 | 2026-08-19T09:48:22.440Z | managed_process_started |  |  | owner=default |
| 21393 | 2026-08-19T09:48:24.116Z | failure_observed | PROVING | PROVING | reason=A non-terminal wave was recovered outside its original synchronous execution.; failure_class=RUNTIME_RESUME_REQUIRED |
| 21394 | 2026-08-19T09:48:24.283Z | state_transition | PROVING | REPLAN | reason=RUNTIME_RESUME_REQUIRED; failure_class=RUNTIME_RESUME_REQUIRED |
| 21395 | 2026-08-19T09:48:24.753Z | managed_process_terminal |  |  | owner=default |
| 21396 | 2026-08-19T09:48:24.756Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |
| 21397 | 2026-08-19T09:48:25.206Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=ba390f034b59d76614d7a76469ba208c9927b85237767fa9fc5b0cb4485ef4d4 |
| 21398 | 2026-08-19T09:48:25.621Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 21399 | 2026-08-19T09:48:31.098Z | managed_process_admitted |  |  | owner=default |
| 21400 | 2026-08-19T09:48:31.342Z | managed_process_started |  |  | owner=default |
| 21401 | 2026-08-19T09:48:31.769Z | managed_process_terminal |  |  | owner=default |
| 21402 | 2026-08-19T09:48:50.470Z | quality_outcome_recorded |  |  |  |
| 21403 | 2026-08-19T09:48:50.593Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 21404 | 2026-08-19T09:48:50.895Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | ba390f034b59d76614d7a76469ba208c9927b85237767fa9fc5b0cb4485ef4d4 | False | 2905 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 405c39021de24be0a3e755fb019f871f | accepted | 930d3e1e67f2b413aa32d5da99d1a01d22d0bddc | 8575c021ba7e112b9f7e36c71d5a4c04c328848bb66a43e82017a30f2f7d1dc6 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `70`
- Chain head: `336f83fdf2e69e728398753d4f78f33b8d9053e620656fa659198167d46072da`
