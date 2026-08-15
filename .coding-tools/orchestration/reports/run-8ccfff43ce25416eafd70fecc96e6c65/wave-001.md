# Orchestration Wave 1

- Run: `8ccfff43ce25416eafd70fecc96e6c65`
- Wave: `554ce036a60647c9b2b5263510eb1547`
- Objective: Live Wave 2A idempotency canary after runtime recovery. Dry-run only; prove same-key durable replay without writing source.
- Mode: `mcp_only`
- Base HEAD: `f64abe25a85e6abaa9fe9eeacd3665eb29a82515`
- Worktree fingerprint: `e87dec8711ecc2d04be3f3cb61d20e58159279d63efa779b7d94d6fb7f7dbd5b`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 5287 | 2026-08-15T10:53:06.766Z | run_started |  | PREFLIGHT |  |
| 5288 | 2026-08-15T10:53:07.199Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 5289 | 2026-08-15T10:53:07.485Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 5290 | 2026-08-15T10:53:07.843Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 5291 | 2026-08-15T10:53:08.167Z | state_transition | READY | ROUTED | reason=route_selected |
| 5292 | 2026-08-15T10:53:08.949Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=a135a0b736d84f60b9e37a2deb973b96 |
| 5293 | 2026-08-15T10:53:09.281Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 5294 | 2026-08-15T10:53:10.155Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=a135a0b736d84f60b9e37a2deb973b96 |
| 5295 | 2026-08-15T10:53:10.527Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 5296 | 2026-08-15T10:53:11.547Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 5297 | 2026-08-15T10:53:36.369Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| - | - | - | - | - | - |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 41db49a5df22422a90c0f77fca55c710 | accepted | f64abe25a85e6abaa9fe9eeacd3665eb29a82515 |  | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `11`
- Chain head: `81e5aaf11007ae0eb1632b27c26adb0e946b866176616e72bd637e8fb26ae7e8`
