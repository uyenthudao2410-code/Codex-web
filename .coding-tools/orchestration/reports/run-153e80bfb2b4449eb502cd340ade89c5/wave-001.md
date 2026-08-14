# Orchestration Wave 1

- Run: `153e80bfb2b4449eb502cd340ade89c5`
- Wave: `f73b4ba1cdb5454fac4b06799c3b306c`
- Objective: Apply the manually localized deterministic multi-provider Execution Hub patch after Terra timed out. This is the same user-visible scope, but no model cascade: explicit proxy identity for Codex Desktop/OpenCode, strict gateway allowlist, OpenCode worker registration, OpenCode config identity, and truthful nine-node router UI with focused tests.
- Mode: `mcp_only`
- Base HEAD: `5f756b5f9a4ab29ca84401314bcc72efc17ae31b`
- Worktree fingerprint: `81ecc5e08c95300c046c5021daf78b0f57cb8884b83c1c99d99416395e0ce1be`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 1471 | 2026-08-14T07:12:09.959Z | run_started |  | PREFLIGHT |  |
| 1472 | 2026-08-14T07:12:10.142Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 1473 | 2026-08-14T07:12:10.306Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 1474 | 2026-08-14T07:12:10.505Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 1475 | 2026-08-14T07:12:10.726Z | state_transition | READY | ROUTED | reason=route_selected |
| 1476 | 2026-08-14T07:12:11.332Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=cb40e371dbe7432a850c8a23f88f7384 |
| 1477 | 2026-08-14T07:12:11.566Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 1478 | 2026-08-14T07:12:12.207Z | failure_observed | EXECUTING | EXECUTING | failure_class=PATCH_AMBIGUOUS |
| 1479 | 2026-08-14T07:12:12.525Z | write_lease_revoked | EXECUTING | EXECUTING | reason=state_transition:replan; owner=MCP; lease_id=cb40e371dbe7432a850c8a23f88f7384 |
| 1480 | 2026-08-14T07:12:12.730Z | state_transition | EXECUTING | REPLAN | reason=PATCH_AMBIGUOUS; failure_class=PATCH_AMBIGUOUS |

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
