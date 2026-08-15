# Orchestration Wave 1

- Run: `5383a188ee5849858341e708ecb17213`
- Wave: `22e28bb213b14b5bb52680a4cc539bc0`
- Objective: Close the idempotency edge introduced by pre-EOCL patch preflight: when a deterministic patch preflight fails before any write/run creation, mark the durable idempotency outcome as a known terminal failure instead of unknown. Preserve unknown fail-closed semantics for crashes after possible side effects. Add a focused regression proving no orchestration run/file mutation and failed-not-unknown idempotency. Do not call providers or external review.
- Mode: `mcp_only`
- Base HEAD: `dff81e251836666fc825c40bf86e4167afd29c39`
- Worktree fingerprint: `54d5b821895dbcf203d3cb0e21d7d0f7ee163d23655eeee0c672a6f293aecb80`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 4443 | 2026-08-15T05:31:29.835Z | run_started |  | PREFLIGHT |  |
| 4444 | 2026-08-15T05:31:30.004Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 4445 | 2026-08-15T05:31:30.226Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 4446 | 2026-08-15T05:31:30.417Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 4447 | 2026-08-15T05:31:30.601Z | state_transition | READY | ROUTED | reason=route_selected |
| 4448 | 2026-08-15T05:31:31.217Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=848151a5eac24278aa352e9a1167e128 |
| 4449 | 2026-08-15T05:31:31.447Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 4450 | 2026-08-15T05:31:32.482Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=848151a5eac24278aa352e9a1167e128 |
| 4451 | 2026-08-15T05:31:32.692Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 4452 | 2026-08-15T05:31:33.434Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=f58c617949140bc8f7e0d6d314c931a108eebd7a92eba74e09a09e3c4921385c |
| 4453 | 2026-08-15T05:31:59.806Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=f58c617949140bc8f7e0d6d314c931a108eebd7a92eba74e09a09e3c4921385c |
| 4454 | 2026-08-15T05:32:00.520Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 4455 | 2026-08-15T05:32:23.525Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | f58c617949140bc8f7e0d6d314c931a108eebd7a92eba74e09a09e3c4921385c | False | 25813 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| b1bb32074ea3466f8b420e990f7b2cdd | accepted | dff81e251836666fc825c40bf86e4167afd29c39 | 73069d7766dfe1d54e01b7319f6e1951894f81bfc76e05c8a1bb778101062d28 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `13`
- Chain head: `ca058cfec30c21439cd561b491492fbf4d65631529d6f4d135bc0e6257f8929d`
