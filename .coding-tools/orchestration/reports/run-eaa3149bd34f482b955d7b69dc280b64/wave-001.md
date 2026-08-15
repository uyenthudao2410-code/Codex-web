# Orchestration Wave 1

- Run: `eaa3149bd34f482b955d7b69dc280b64`
- Wave: `95cf7e31d7e442cd88267d4e4377216d`
- Objective: Fix only the stale-health test fixture: task_control recovery snapshot uses action=get, not the nonexistent action=status. Do not change production source.
- Mode: `mcp_only`
- Base HEAD: `dff81e251836666fc825c40bf86e4167afd29c39`
- Worktree fingerprint: `79db2acc70d01e2f4ae7b9f933763d943215f0a5cc8e2c47cf339ddcff4c52df`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 3944 | 2026-08-15T02:54:39.294Z | run_started |  | PREFLIGHT |  |
| 3945 | 2026-08-15T02:54:39.501Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 3946 | 2026-08-15T02:54:39.706Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 3947 | 2026-08-15T02:54:39.914Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 3948 | 2026-08-15T02:54:40.104Z | state_transition | READY | ROUTED | reason=route_selected |
| 3949 | 2026-08-15T02:54:40.637Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=43d98cb00a9641b387bc0213b8dbd479 |
| 3950 | 2026-08-15T02:54:40.838Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 3951 | 2026-08-15T02:54:41.409Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=43d98cb00a9641b387bc0213b8dbd479 |
| 3952 | 2026-08-15T02:54:41.588Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 3953 | 2026-08-15T02:54:42.013Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=ba4f0a942f4ed8293c57dddf27791e75d7ea224d93dcba6cd18d3a12d6cdf51c |
| 3954 | 2026-08-15T02:54:43.888Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=ba4f0a942f4ed8293c57dddf27791e75d7ea224d93dcba6cd18d3a12d6cdf51c |
| 3955 | 2026-08-15T02:54:52.775Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 3956 | 2026-08-15T02:55:39.616Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | ba4f0a942f4ed8293c57dddf27791e75d7ea224d93dcba6cd18d3a12d6cdf51c | False | 1516 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 6ac654832e764982b474de1b129adca9 | accepted | dff81e251836666fc825c40bf86e4167afd29c39 | 25d6ca30b6eb6b18c73a3aa5b0a6ad279a7bbb09d8a041d5d970efeda1f21357 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `13`
- Chain head: `2b0929618c5ca141bd3e6f3fa4714a470d1d9f07c3aa611387c86cd6465eb33b`
