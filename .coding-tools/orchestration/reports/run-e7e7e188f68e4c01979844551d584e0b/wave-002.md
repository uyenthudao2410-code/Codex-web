# Orchestration Wave 2

- Run: `e7e7e188f68e4c01979844551d584e0b`
- Wave: `b405c5c2b1e14daab57d039173588420`
- Objective: P5A implement the authenticated model-hidden Rust native semantic LSP bridge. Add one exact connector-internal route that accepts only project credential auth for the exact grant plus project:read, verifies a SHA-256 of the caller workspace against the connector's canonical executor root, accepts only bounded workspace-symbol queries, dispatches only the existing read-only workspace_symbols ToolKernel operation against context.executor_project, and returns only normalized project-relative symbol matches. Keep the route out of CAPABILITY_NAMES/OpenAPI/MCP and keep generic /api/tools/call denied. Add focused tests for exact-route hard gate, hidden route, bootstrap/wrong-grant/wrong-workspace rejection, unavailable LSP capability, and happy-path typed LSP normalization. Do not touch Routing-v2 gates, restart, deploy, call providers, commit, or push.
- Mode: `mcp_only`
- Base HEAD: `e45bed968bee6db46bb3041de179cbcf23e3906b`
- Worktree fingerprint: `4c8db6f189393af65db0df2f4fa5c8ae2a8d1c098061c00658aeaf98f78af2b5`
- Contract fingerprint: ``
- Status: **active**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 3425 | 2026-08-14T22:42:08.155Z | wave_replanned |  | PREFLIGHT | reason=The prior P5A attempt created only the intended new semantic_bridge.rs file, then the multi-file patch was rejected because one http.rs hunk matched multiple contexts. Continue from that partial intended file, use exact function-boundary contexts for the remaining wiring, and do not retry the ambiguous hunk unchanged. |
| 3426 | 2026-08-14T22:42:08.270Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 3427 | 2026-08-14T22:42:08.378Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 3428 | 2026-08-14T22:42:08.500Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 3429 | 2026-08-14T22:42:08.690Z | state_transition | READY | ROUTED | reason=route_selected |
| 3430 | 2026-08-14T22:42:09.127Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=ce3b70ed6237423e98c8a5623769d0b6 |
| 3431 | 2026-08-14T22:42:09.230Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 3432 | 2026-08-14T22:42:09.868Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=ce3b70ed6237423e98c8a5623769d0b6 |
| 3433 | 2026-08-14T22:42:09.976Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 3434 | 2026-08-14T22:42:10.621Z | proof_cache_miss |  |  | reason=cold; stage_id=check:194fabc0129ce4a9; input_fingerprint=99261ea8dd67ce82532ddfb1c3c7017659e7f69aecb3e2f481fbda4cb89c8c54 |
| 3435 | 2026-08-14T22:42:12.988Z | proof_recorded |  |  | stage_id=check:194fabc0129ce4a9; status=failed; cache_hit=False; input_fingerprint=99261ea8dd67ce82532ddfb1c3c7017659e7f69aecb3e2f481fbda4cb89c8c54 |
| 3436 | 2026-08-14T22:42:13.103Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 3437 | 2026-08-14T22:42:13.211Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:194fabc0129ce4a9 | failed | 99261ea8dd67ce82532ddfb1c3c7017659e7f69aecb3e2f481fbda4cb89c8c54 | False | 1827 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `23`
- Chain head: `66cb5d347876f7f641a0d5742f25fbe54f4dbec0a2cbe002be1caf3f458dc171`
