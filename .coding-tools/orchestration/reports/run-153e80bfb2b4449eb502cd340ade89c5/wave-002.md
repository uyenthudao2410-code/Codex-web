# Orchestration Wave 2

- Run: `153e80bfb2b4449eb502cd340ade89c5`
- Wave: `2533e69eb18a44b2b4fa939850b1efb5`
- Objective: Apply the manually localized deterministic multi-provider Execution Hub patch after Terra timed out. This is the same user-visible scope, but no model cascade: explicit proxy identity for Codex Desktop/OpenCode, strict gateway allowlist, OpenCode worker registration, OpenCode config identity, and truthful nine-node router UI with focused tests.
- Mode: `mcp_only`
- Base HEAD: `5f756b5f9a4ab29ca84401314bcc72efc17ae31b`
- Worktree fingerprint: `5e3229a75bfd24853d11c161960d37d78459cbcea4188911787cccf011081769`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 1481 | 2026-08-14T07:12:35.734Z | wave_replanned |  | PREFLIGHT | reason=The deterministic patch was rejected before commit because one hubProxyGateway hunk had ambiguous context. Verify current files and make the next gateway hunk uniquely anchored; do not change scope or route. |
| 1482 | 2026-08-14T07:12:36.388Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 1483 | 2026-08-14T07:14:50.736Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 1484 | 2026-08-14T07:14:50.901Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 1485 | 2026-08-14T07:14:51.119Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 1486 | 2026-08-14T07:14:51.302Z | state_transition | READY | ROUTED | reason=route_selected |
| 1487 | 2026-08-14T07:14:52.008Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=0d69a16f871e425d954e230d33f2bcb7 |
| 1488 | 2026-08-14T07:14:52.218Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 1489 | 2026-08-14T07:14:53.028Z | failure_observed | EXECUTING | EXECUTING | failure_class=PATCH_CONTEXT_NOT_FOUND |
| 1490 | 2026-08-14T07:14:53.358Z | write_lease_revoked | EXECUTING | EXECUTING | reason=state_transition:replan; owner=MCP; lease_id=0d69a16f871e425d954e230d33f2bcb7 |
| 1491 | 2026-08-14T07:14:53.869Z | state_transition | EXECUTING | REPLAN | reason=PATCH_CONTEXT_NOT_FOUND; failure_class=PATCH_CONTEXT_NOT_FOUND |

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
- Events checked: `34`
- Chain head: `c24f0cb51295336ea2d378cc24c3c26a75a772ae699c2e5ef611ce67bc1cc0f7`
