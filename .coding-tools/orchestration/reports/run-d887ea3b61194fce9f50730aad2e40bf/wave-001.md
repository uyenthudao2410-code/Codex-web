# Orchestration Wave 1

- Run: `d887ea3b61194fce9f50730aad2e40bf`
- Wave: `ae62479588614aa8b07106bbada731e5`
- Objective: Fix the Windows cancellation orphan exposed by Wave E: terminate the entire exec_command process tree, not only the shell parent, then rerun the resilience fault-injection suite. Preserve all existing behavior and do not commit/push.
- Mode: `mcp_only`
- Base HEAD: `a051897449827e4753b16def1b693d867fad76e9`
- Worktree fingerprint: `bdd2dc82434ede8ba106b200d6b74dcbb8c31fd37f6942c936b990df9b4c960e`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 400 | 2026-08-13T09:39:19.019Z | run_started |  | PREFLIGHT |  |
| 401 | 2026-08-13T09:39:20.025Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 402 | 2026-08-13T09:39:49.202Z | execution_mode_resolved | PREFLIGHT | PREFLIGHT | requested=auto; resolved=mcp_only |
| 403 | 2026-08-13T09:39:50.402Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 404 | 2026-08-13T09:39:52.791Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 405 | 2026-08-13T09:39:54.186Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=auto; resolved=deterministic |
| 406 | 2026-08-13T09:39:56.066Z | state_transition | READY | ROUTED | reason=route_selected |
| 407 | 2026-08-13T09:39:57.758Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=24a45e3ce7784c8383ad6d0a43b19aa8 |
| 408 | 2026-08-13T09:39:57.956Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 409 | 2026-08-13T09:39:58.651Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=24a45e3ce7784c8383ad6d0a43b19aa8 |
| 410 | 2026-08-13T09:39:58.862Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 411 | 2026-08-13T09:40:08.657Z | proof_recorded |  |  | stage_id=check:60dc4727870e8bf1; status=passed; cache_hit=False; input_fingerprint=4c4b90dbcd5a593a0f1407deb805e6d925405fa7120a7fe7735f5e6c4a5f2130 |
| 412 | 2026-08-13T09:40:09.455Z | proof_recorded |  |  | stage_id=check:101c5c39224a46c9; status=passed; cache_hit=False; input_fingerprint=7c90f75fa7139f8f59fe0be99fa105f495c924c9932ead24b930281eff6ac8a9 |
| 413 | 2026-08-13T09:40:09.821Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 414 | 2026-08-13T09:42:51.015Z | state_transition | ACCEPTING | CHECKPOINTED | reason=chatweb_sol_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:60dc4727870e8bf1 | passed | 4c4b90dbcd5a593a0f1407deb805e6d925405fa7120a7fe7735f5e6c4a5f2130 | False | 8402 | 0 |
| check:101c5c39224a46c9 | passed | 7c90f75fa7139f8f59fe0be99fa105f495c924c9932ead24b930281eff6ac8a9 | False | 208 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 52743dcf666142aa856387278714cb49 | accepted | a051897449827e4753b16def1b693d867fad76e9 | bfa9101d3052cb209f31a33cc3fee9a3f7a1f9287366d7e9e15788dde2c5434f | ChatWeb Sol |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `15`
- Chain head: `ce0decbab603f05f91f006f58a5046bdede9c6b3c72bc890c0adbf2cc1841384`
