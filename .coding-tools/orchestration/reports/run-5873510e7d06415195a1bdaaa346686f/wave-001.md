# Orchestration Wave 1

- Run: `5873510e7d06415195a1bdaaa346686f`
- Wave: `bd902d6d4b2542499a67442e5d3d1ec1`
- Objective: Rebuild dist/win-unpacked from the accepted UTF-8 Recovery Supervisor fix on top of HEAD f1b38e6c. This package must include the fixed supervisor bytes and pass electron-builder afterPack sanitation. Do not publish, install, tag, or alter the live production runtime.
- Mode: `mcp_only`
- Base HEAD: `f1b38e6ca8d63c2d07357f0fc88aa1631021c6b1`
- Worktree fingerprint: `879d7fab0a8c6ef6824f23191f250b18818d31471a0ed0c17c155eb19e159d6d`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 11953 | 2026-08-17T07:20:54.762Z | run_started |  | PREFLIGHT |  |
| 11954 | 2026-08-17T07:20:55.286Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 11955 | 2026-08-17T07:20:55.460Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 11956 | 2026-08-17T07:20:55.624Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 11957 | 2026-08-17T07:20:55.773Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 11958 | 2026-08-17T07:20:55.963Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 11959 | 2026-08-17T07:20:56.162Z | state_transition | READY | ROUTED | reason=route_selected |
| 11960 | 2026-08-17T07:20:56.643Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=a683ad99734e456abc389e944fa7bbb5 |
| 11961 | 2026-08-17T07:20:56.805Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 11962 | 2026-08-17T07:20:57.200Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=a683ad99734e456abc389e944fa7bbb5 |
| 11963 | 2026-08-17T07:20:57.354Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 11964 | 2026-08-17T07:20:57.814Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:19d9608459d0cb40; input_fingerprint=98d50bd9fab0d8d41eb080f6d483a95f91c4e6ae0f83bbeef8c645452091f864 |
| 11965 | 2026-08-17T07:20:58.194Z | managed_process_admitted |  |  | owner=default |
| 11966 | 2026-08-17T07:20:58.462Z | managed_process_started |  |  | owner=default |
| 11967 | 2026-08-17T07:21:26.876Z | managed_process_terminal |  |  | owner=default |
| 11968 | 2026-08-17T07:21:27.433Z | proof_recorded |  |  | stage_id=check:19d9608459d0cb40; status=passed; cache_hit=False; input_fingerprint=98d50bd9fab0d8d41eb080f6d483a95f91c4e6ae0f83bbeef8c645452091f864 |
| 11969 | 2026-08-17T07:21:27.576Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 11970 | 2026-08-17T07:21:35.451Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 11971 | 2026-08-17T07:21:35.832Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:19d9608459d0cb40 | passed | 98d50bd9fab0d8d41eb080f6d483a95f91c4e6ae0f83bbeef8c645452091f864 | False | 29266 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 8980ff9d57d44cbe8f3f1866d31179d4 | accepted | f1b38e6ca8d63c2d07357f0fc88aa1631021c6b1 | f72d0ad9adfe1a7ccd60d1551307226273ec924bba954c9bfa0da0136185ba9c | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `19`
- Chain head: `e02ec1a55241226126f28245780e23f9b3eea8f8e142146e1fdc340a452efbb7`
