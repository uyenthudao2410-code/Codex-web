# Orchestration Wave 1

- Run: `d61c2ccc84e042adada9a93aa8c97603`
- Wave: `62aaae8af31b4a8cbef02627a6e0d640`
- Objective: Render durable EOCL acceptance checkpoints into generated run and wave Markdown reports so postmortems show accepted git head, proof fingerprint, status, and acceptance authority directly from the canonical ledger.
- Mode: `mcp_only`
- Base HEAD: `ec91b82e10d6f4657fd3444bc5093704c9512814`
- Worktree fingerprint: `ca4d192d4c123392c7509e7679b9adce703eaaa050e7fe4b84e71e3bd768d0fa`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 56 | 2026-08-13T05:39:26.165Z | run_started |  | PREFLIGHT |  |
| 57 | 2026-08-13T05:39:26.618Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 58 | 2026-08-13T05:39:26.910Z | execution_mode_resolved | PREFLIGHT | PREFLIGHT | requested=auto; resolved=mcp_only |
| 59 | 2026-08-13T05:39:27.074Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 60 | 2026-08-13T05:39:27.234Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 61 | 2026-08-13T05:39:27.437Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=auto; resolved=deterministic |
| 62 | 2026-08-13T05:39:27.607Z | state_transition | READY | ROUTED | reason=route_selected |
| 63 | 2026-08-13T05:39:28.037Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=1eeeeb35c1284247b410f91e4c133219 |
| 64 | 2026-08-13T05:39:28.201Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 65 | 2026-08-13T05:39:28.711Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=1eeeeb35c1284247b410f91e4c133219 |
| 66 | 2026-08-13T05:39:28.837Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 67 | 2026-08-13T05:39:29.848Z | proof_recorded |  |  | stage_id=check:9c8b57bee9990923; status=passed; cache_hit=False; input_fingerprint=c1115445d7129a68b1e7335afc3b29ffce7fec6a48dbf61dec4565142b5f5ef8 |
| 68 | 2026-08-13T05:39:37.087Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 69 | 2026-08-13T05:42:13.353Z | state_transition | ACCEPTING | CHECKPOINTED | reason=chatweb_sol_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:9c8b57bee9990923 | passed | c1115445d7129a68b1e7335afc3b29ffce7fec6a48dbf61dec4565142b5f5ef8 | False | 461 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| a1d7258ef62243ecac1e954104aa5eaa | accepted | ec91b82e10d6f4657fd3444bc5093704c9512814 | d0a4635a3bbef010b36214fa4298b0af6e7c9b9c80d836c0bf3a3bc08fb2dc93 | ChatWeb Sol |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `14`
- Chain head: `4e05fae4a9650b41d97e37cb0a169260685ea583caeec62e0a2ce4b594ec4397`
