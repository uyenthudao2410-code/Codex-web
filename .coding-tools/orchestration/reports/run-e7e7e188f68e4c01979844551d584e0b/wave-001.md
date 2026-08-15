# Orchestration Wave 1

- Run: `e7e7e188f68e4c01979844551d584e0b`
- Wave: `49cb2624ca874ae7a60868baa1283c10`
- Objective: P5A implement the authenticated model-hidden Rust native semantic LSP bridge. Add one exact connector-internal route that accepts only project credential auth for the exact grant plus project:read, verifies a SHA-256 of the caller workspace against the connector's canonical executor root, accepts only bounded workspace-symbol queries, dispatches only the existing read-only workspace_symbols ToolKernel operation against context.executor_project, and returns only normalized project-relative symbol matches. Keep the route out of CAPABILITY_NAMES/OpenAPI/MCP and keep generic /api/tools/call denied. Add focused tests for exact-route hard gate, hidden route, bootstrap/wrong-grant/wrong-workspace rejection, unavailable LSP capability, and happy-path typed LSP normalization. Do not touch Routing-v2 gates, restart, deploy, call providers, commit, or push.
- Mode: `mcp_only`
- Base HEAD: `e45bed968bee6db46bb3041de179cbcf23e3906b`
- Worktree fingerprint: `e256475bc2030e8560d22b742269d96e8fdc281a84f8ab7f5325dbe5bb9f71b4`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 3415 | 2026-08-14T22:41:31.153Z | run_started |  | PREFLIGHT |  |
| 3416 | 2026-08-14T22:41:31.288Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 3417 | 2026-08-14T22:41:31.395Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 3418 | 2026-08-14T22:41:31.545Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 3419 | 2026-08-14T22:41:31.671Z | state_transition | READY | ROUTED | reason=route_selected |
| 3420 | 2026-08-14T22:41:32.077Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=9ef2ccc50b554e5f9093a71926df060a |
| 3421 | 2026-08-14T22:41:32.211Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 3422 | 2026-08-14T22:41:32.628Z | failure_observed | EXECUTING | EXECUTING | failure_class=PATCH_AMBIGUOUS |
| 3423 | 2026-08-14T22:41:32.861Z | write_lease_revoked | EXECUTING | EXECUTING | reason=state_transition:replan; owner=MCP; lease_id=9ef2ccc50b554e5f9093a71926df060a |
| 3424 | 2026-08-14T22:41:33.003Z | state_transition | EXECUTING | REPLAN | reason=PATCH_AMBIGUOUS; failure_class=PATCH_AMBIGUOUS |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| - | - | - | - | - | - |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `23`
- Chain head: `66cb5d347876f7f641a0d5742f25fbe54f4dbec0a2cbe002be1caf3f458dc171`
