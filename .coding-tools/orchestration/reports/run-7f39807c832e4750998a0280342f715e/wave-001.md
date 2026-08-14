# Orchestration Wave 1

- Run: `7f39807c832e4750998a0280342f715e`
- Wave: `2fac889ffaea47c8acfbd58e4fe04188`
- Objective: Fix the full-suite regression introduced by auto-derived task_control accept/reject idempotency keys. Scope only accept/reject derived keys by current caller client_id and controller fencing_token so a denied stale client cannot poison a valid controller's key, and a new authority epoch gets a new key. Keep agent_workflow execute derivation unchanged, explicit keys unchanged, and idempotency failure semantics fail-closed. Add focused unit assertions.
- Mode: `mcp_only`
- Base HEAD: `62ff046711503260b079e53a85c66e5b9af01e32`
- Worktree fingerprint: `65ae17c594317da5cb707382baeabc8e6146a3ddd9cc6a8dfb3e5daaa2d4aa40`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 2877 | 2026-08-14T16:33:21.376Z | run_started |  | PREFLIGHT |  |
| 2878 | 2026-08-14T16:33:21.545Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 2879 | 2026-08-14T16:33:21.709Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 2880 | 2026-08-14T16:33:21.898Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 2881 | 2026-08-14T16:33:22.090Z | state_transition | READY | ROUTED | reason=route_selected |
| 2882 | 2026-08-14T16:33:22.821Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=7c18b7d581804fb48d608a2e0ef5a975 |
| 2883 | 2026-08-14T16:33:23.237Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 2884 | 2026-08-14T16:33:24.754Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=7c18b7d581804fb48d608a2e0ef5a975 |
| 2885 | 2026-08-14T16:33:25.204Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 2886 | 2026-08-14T16:33:26.047Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 2887 | 2026-08-14T16:37:27.174Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| - | - | - | - | - | - |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| d58e02105993401fb176b18ccdb9cb3a | accepted | 62ff046711503260b079e53a85c66e5b9af01e32 |  | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `11`
- Chain head: `c15aec36fa9dc4e9d3176d409a652c7504211e7b5487fa628da9ee8369051dc3`
