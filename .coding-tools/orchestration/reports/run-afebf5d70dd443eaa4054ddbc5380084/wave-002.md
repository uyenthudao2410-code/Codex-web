# Orchestration Wave 2

- Run: `afebf5d70dd443eaa4054ddbc5380084`
- Wave: `8f5ac3c78a704d9ab0aa4817124166ff`
- Objective: Implement Execution Hub backend state primitives only: durable Hub client registry, monotonic per-client event cursors, separate controller lease with monotonic fencing token/TTL, operator transfer only to an online registered client, and focused persistence/contention/expiry tests. Do not modify server public schemas, panel, proxy, routing, or existing P1.5 behavior in this wave.
- Mode: `mcp_only`
- Base HEAD: `5f756b5f9a4ab29ca84401314bcc72efc17ae31b`
- Worktree fingerprint: `abe3b1aefed3d123ed5aa8417d040ba48f86e9543d61e219f683d66b29a1db79`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 919 | 2026-08-14T05:05:35.172Z | wave_replanned |  | PREFLIGHT | reason=Critical review found orphan authority/cursor rows were possible for nonexistent run/client ids despite green tests. Add explicit referential validation plus FK declarations and update tests to create valid run/client records and prove invalid references fail. |
| 920 | 2026-08-14T05:05:35.341Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 921 | 2026-08-14T05:05:35.549Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 922 | 2026-08-14T05:05:35.739Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 923 | 2026-08-14T05:05:35.930Z | state_transition | READY | ROUTED | reason=route_selected |
| 924 | 2026-08-14T05:05:36.472Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=8578f059a4ed43ee8286b26bc7cb462a |
| 925 | 2026-08-14T05:05:36.680Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 926 | 2026-08-14T05:05:37.133Z | failure_observed | EXECUTING | EXECUTING | failure_class=PATCH_AMBIGUOUS |
| 927 | 2026-08-14T05:05:37.430Z | write_lease_revoked | EXECUTING | EXECUTING | reason=state_transition:replan; owner=MCP; lease_id=8578f059a4ed43ee8286b26bc7cb462a |
| 928 | 2026-08-14T05:05:37.613Z | state_transition | EXECUTING | REPLAN | reason=PATCH_AMBIGUOUS; failure_class=PATCH_AMBIGUOUS |

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
- Events checked: `36`
- Chain head: `fc53484f19e8f2b0276989e9ea53f7dad57aa6af35543dd9f5301b8cb447d5c8`
