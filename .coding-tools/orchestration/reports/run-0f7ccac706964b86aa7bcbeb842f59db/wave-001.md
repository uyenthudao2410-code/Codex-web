# Orchestration Wave 1

- Run: `0f7ccac706964b86aa7bcbeb842f59db`
- Wave: `a9287b52cb2b4b22ba81683128413918`
- Objective: Create three identical isolated benchmark fixtures under tmp/execution-hub-benchmark/{mini,luna,sol} for paired routing evaluation. Each fixture contains the same intentionally broken normalize_score implementation and the same deterministic 3-case oracle. This is benchmark setup only; do not touch production source.
- Mode: `mcp_only`
- Base HEAD: `5f756b5f9a4ab29ca84401314bcc72efc17ae31b`
- Worktree fingerprint: `ae452b7e2209892ad49784725dfd4f533cf894da34407cf13ac7eec20a8f60e4`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 1228 | 2026-08-14T06:05:32.353Z | run_started |  | PREFLIGHT |  |
| 1229 | 2026-08-14T06:05:32.851Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 1230 | 2026-08-14T06:05:33.033Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 1231 | 2026-08-14T06:05:33.275Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 1232 | 2026-08-14T06:05:33.500Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 1233 | 2026-08-14T06:05:33.684Z | state_transition | READY | ROUTED | reason=route_selected |
| 1234 | 2026-08-14T06:05:34.262Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=a0c1a85b95bf43dda1d23c21763e4dff |
| 1235 | 2026-08-14T06:05:34.406Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 1236 | 2026-08-14T06:05:35.301Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=a0c1a85b95bf43dda1d23c21763e4dff |
| 1237 | 2026-08-14T06:05:35.495Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 1238 | 2026-08-14T06:05:36.142Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 1239 | 2026-08-14T06:05:48.944Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| - | - | - | - | - | - |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 3c88d72aa62846e3add04c713ec354f6 | accepted | 5f756b5f9a4ab29ca84401314bcc72efc17ae31b |  | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `12`
- Chain head: `4ba842a3d952c8404fc6d313d4670720042dd9774603143ddebbe0baa53c51e6`
