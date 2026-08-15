# Orchestration Wave 1

- Run: `ef61530282f94f1888ac8ef6aa85af27`
- Wave: `9811772d705240bbb877451b3a296fd8`
- Objective: Final integrated acceptance for stale-orchestration health semantics on the exact current worktree. Verify the read-only stale candidate refactor, current-vs-reconciled recovery projections, all existing P1 continuation/idempotency/provenance behavior, and root Electron/Node source contracts. Do not mutate source, restart runtime, commit, push, release, change CI billing, activate semantic credentials, or promote routing.
- Mode: `mcp_only`
- Base HEAD: `dff81e251836666fc825c40bf86e4167afd29c39`
- Worktree fingerprint: `75b89fbb26593676d4723ff5a67143e6a5dbfa45722f5b7dbf03b0c145d3977c`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 3957 | 2026-08-15T02:56:02.077Z | run_started |  | PREFLIGHT |  |
| 3958 | 2026-08-15T02:56:02.274Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 3959 | 2026-08-15T02:56:02.481Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 3960 | 2026-08-15T02:56:02.676Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 3961 | 2026-08-15T02:56:02.888Z | state_transition | READY | ROUTED | reason=route_selected |
| 3962 | 2026-08-15T02:56:03.350Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=47792253632c46048fd169987fe59ead |
| 3963 | 2026-08-15T02:56:03.533Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 3964 | 2026-08-15T02:56:04.167Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=47792253632c46048fd169987fe59ead |
| 3965 | 2026-08-15T02:56:04.351Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 3966 | 2026-08-15T02:56:04.716Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:466c2f308b48c766; input_fingerprint=a98132cfdee5bbd103b462e5bd9bb839a1410f264b2058c8dcf54c3ee6908928 |
| 3967 | 2026-08-15T02:56:05.370Z | proof_recorded |  |  | stage_id=check:466c2f308b48c766; status=passed; cache_hit=False; input_fingerprint=a98132cfdee5bbd103b462e5bd9bb839a1410f264b2058c8dcf54c3ee6908928 |
| 3968 | 2026-08-15T02:56:05.592Z | proof_cache_miss |  |  | reason=cold; stage_id=check:328e123c63857fd8; input_fingerprint=042f1a3b654ab320200d0c9585e8ea3bd1ad10bd0022eddc0c37db8b86f3d15a |
| 3969 | 2026-08-15T02:56:08.821Z | proof_recorded |  |  | stage_id=check:328e123c63857fd8; status=passed; cache_hit=False; input_fingerprint=042f1a3b654ab320200d0c9585e8ea3bd1ad10bd0022eddc0c37db8b86f3d15a |
| 3970 | 2026-08-15T02:56:09.024Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=fc519193a9e18240cf8f07daeda6b9e348551a3d73cf5d0b637e09facb2a713f |
| 3971 | 2026-08-15T02:57:44.513Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=fc519193a9e18240cf8f07daeda6b9e348551a3d73cf5d0b637e09facb2a713f |
| 3972 | 2026-08-15T02:57:44.712Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 3973 | 2026-08-15T02:57:56.765Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:466c2f308b48c766 | passed | a98132cfdee5bbd103b462e5bd9bb839a1410f264b2058c8dcf54c3ee6908928 | False | 273 | 0 |
| check:328e123c63857fd8 | passed | 042f1a3b654ab320200d0c9585e8ea3bd1ad10bd0022eddc0c37db8b86f3d15a | False | 2896 | 0 |
| verify:tests | passed | fc519193a9e18240cf8f07daeda6b9e348551a3d73cf5d0b637e09facb2a713f | False | 95125 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 7f9e9a9a8028460f8bce37b15b73ee0f | accepted | dff81e251836666fc825c40bf86e4167afd29c39 | 3dceaaf4bf40e1502f6b4b37f899db6b1b1cfc23c0224a83ff5a062cd3ee449f | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `17`
- Chain head: `284a6941b804a071cfaed5162628ac88d4f617d85cd5d70ca62d578d86e9f948`
