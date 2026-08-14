# Orchestration Wave 3

- Run: `dba11cf58e14482bb22b52ae453840fc`
- Wave: `e65b2e07912548358195734b429c7408`
- Objective: Implement P-MP3 shadow provider routing as recommendation/evidence only, with no automatic dispatch, orchestration route transition, controller transfer, write-lease mutation, or public MCP tool change. Add a small pure provider_routing module with strict bounded task features and deterministic recommendations aligned to current policy: deterministic mutation -> MCP deterministic; broad read-only -> OpenCode Flash; broad read-only + hard reasoning -> OpenCode Pro; localized + strong oracle -> Codex Mini; localized/bounded harder leaf -> Codex Luna; bounded/cross-file with localized evidence and normal/low latency -> Terra; high/critical risk or consequential mutation -> manual controller/deep review gate rather than OpenCode auto execution. Add idempotent shadow_route_recommended audit events keyed by canonical feature hash, recent shadow-route projection, and an internal routing_evidence projection that pairs recommendations with actual delegations and canonical UsageEvents for later cohort calibration. Expose internal /__control/hub action=shadow_route restricted to electron-panel/electron and bound to the current active task-projected nonterminal run/wave, including PREFLIGHT/READY before actual route selection. Tests must prove recommendations, idempotency, and that shadow_route leaves actual orchestration route/state/controller/write fence/provider adapter untouched. Preserve Smart-v3 8 tools, current production routing thresholds, OpenCode worker-only role, UI, settings, and service state. No provider inference, restart, commit, push, release, or deploy.
- Mode: `mcp_only`
- Base HEAD: `bc820986e383391e36d243e0252e23b0aef8d5b8`
- Worktree fingerprint: `66280d2a361eaaef5f67689f126afaf2eae2f7314475442c0ee389ab8c2ef1fe`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 1870 | 2026-08-14T10:00:24.051Z | wave_replanned |  | PREFLIGHT | reason=The previous shadow-route wave was explicitly rejected for missing integration proof. While preparing that proof, source inspection also found routing_evidence incorrectly passed run_id to the wave-scoped list_delegations API. Materially change the wave to proof-driven repair: fix only that projection contract and add invariance/idempotency tests before acceptance. |
| 1871 | 2026-08-14T10:00:24.380Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 1872 | 2026-08-14T10:00:24.732Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 1873 | 2026-08-14T10:00:25.076Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 1874 | 2026-08-14T10:00:25.358Z | state_transition | READY | ROUTED | reason=route_selected |
| 1875 | 2026-08-14T10:00:26.225Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=e2245ac811da42ffaca77b5911766c64 |
| 1876 | 2026-08-14T10:00:26.623Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 1877 | 2026-08-14T10:00:29.734Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=e2245ac811da42ffaca77b5911766c64 |
| 1878 | 2026-08-14T10:00:30.067Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 1879 | 2026-08-14T10:00:31.607Z | proof_recorded |  |  | stage_id=check:983b6756ab21e193; status=passed; cache_hit=False; input_fingerprint=0b9f7d462cc943288f46166517483e15246026aefd043b517a79070131ca36a7 |
| 1880 | 2026-08-14T10:00:32.898Z | proof_recorded |  |  | stage_id=check:94eeb1ff6043e00f; status=passed; cache_hit=False; input_fingerprint=6c5289b71a020b3429677acb3681743cc0aab4f8fbcd3f989b01a8574892f1d8 |
| 1881 | 2026-08-14T10:00:41.229Z | proof_recorded |  |  | stage_id=check:d68f99d3d141b6d7; status=passed; cache_hit=False; input_fingerprint=e566c484563a3a7c1c9bd59c3f716b3b541d8bf03bee73670a88afd0b8ec910d |
| 1882 | 2026-08-14T10:00:45.785Z | proof_recorded |  |  | stage_id=check:27d05452881c31de; status=passed; cache_hit=False; input_fingerprint=f3970ad1ec46726e99952de4d5f6f3eab6d812b08c7641c7892c7ff9bcfa2e6d |
| 1883 | 2026-08-14T10:00:49.580Z | proof_recorded |  |  | stage_id=check:6b5eb56c39e969bc; status=passed; cache_hit=False; input_fingerprint=d90d4073a2ef89a0e0f035a876d3c1581be02778a643731e312227a73ea731b0 |
| 1884 | 2026-08-14T10:00:50.473Z | proof_recorded |  |  | stage_id=check:619de2c276141ae3; status=passed; cache_hit=False; input_fingerprint=69d6a36f74b84b7541b8341e9e39a92e330051155df3fd5da28fd4011fc57626 |
| 1885 | 2026-08-14T10:00:51.247Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 1886 | 2026-08-14T10:01:21.579Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:983b6756ab21e193 | passed | 0b9f7d462cc943288f46166517483e15246026aefd043b517a79070131ca36a7 | False | 310 | 0 |
| check:94eeb1ff6043e00f | passed | 6c5289b71a020b3429677acb3681743cc0aab4f8fbcd3f989b01a8574892f1d8 | False | 294 | 0 |
| check:d68f99d3d141b6d7 | passed | e566c484563a3a7c1c9bd59c3f716b3b541d8bf03bee73670a88afd0b8ec910d | False | 6536 | 0 |
| check:27d05452881c31de | passed | f3970ad1ec46726e99952de4d5f6f3eab6d812b08c7641c7892c7ff9bcfa2e6d | False | 1579 | 0 |
| check:6b5eb56c39e969bc | passed | d90d4073a2ef89a0e0f035a876d3c1581be02778a643731e312227a73ea731b0 | False | 2678 | 0 |
| check:619de2c276141ae3 | passed | 69d6a36f74b84b7541b8341e9e39a92e330051155df3fd5da28fd4011fc57626 | False | 152 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 0d9adf99903646ddb7dbcbb1817b4fe9 | accepted | 7609297462713beb104e5c933ea4d6bf3b24ec11 | d9ed6923c141172199000794fa5a844178a0a4374b49b6a43db8b0bd1fbc25df | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `42`
- Chain head: `fd84fbb76b744abd300421a6427ff131d24e8c8a9e2a908b79e39a9175a1fefd`
