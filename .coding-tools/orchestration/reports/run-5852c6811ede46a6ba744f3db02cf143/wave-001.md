# Orchestration Wave 1

- Run: `5852c6811ede46a6ba744f3db02cf143`
- Wave: `cceaba0cd2f8421a95038d86c286ea43`
- Objective: Fix the one full-suite regression caused by the accepted task-epoch idempotency contract. Update the old efficiency test so agent_workflow execute derives from durable TaskState task epoch + request hash: changing only wave within the same task must not change its key; completing the task and starting a new task epoch must change the key. Preserve task_control accept/reject run+wave+caller+fence assertions and add an explicit same-caller/fence different-wave accept key difference. No production source change.
- Mode: `mcp_only`
- Base HEAD: `5decaa48300b10a6df39676c677745bc881cd7d9`
- Worktree fingerprint: `9fd32fdc002ea9d9e2ee95979e97c4b697e527f1f2f63386a699d3075cf960d4`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 3348 | 2026-08-14T18:18:35.187Z | run_started |  | PREFLIGHT |  |
| 3349 | 2026-08-14T18:18:35.305Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 3350 | 2026-08-14T18:18:35.415Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 3351 | 2026-08-14T18:18:35.749Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 3352 | 2026-08-14T18:18:35.877Z | state_transition | READY | ROUTED | reason=route_selected |
| 3353 | 2026-08-14T18:18:36.359Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=c2b1d40be38544bd8faa99caa5cf3e5c |
| 3354 | 2026-08-14T18:18:36.527Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 3355 | 2026-08-14T18:18:37.068Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=c2b1d40be38544bd8faa99caa5cf3e5c |
| 3356 | 2026-08-14T18:18:37.221Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 3357 | 2026-08-14T18:18:37.580Z | proof_cache_miss |  |  | reason=cold; stage_id=check:f4519402607328a3; input_fingerprint=b7a8a3b55b82905dff0e58e09c71b2389bb816493471e5bc1b1d6c98e8f82b9d |
| 3358 | 2026-08-14T18:18:38.991Z | proof_recorded |  |  | stage_id=check:f4519402607328a3; status=passed; cache_hit=False; input_fingerprint=b7a8a3b55b82905dff0e58e09c71b2389bb816493471e5bc1b1d6c98e8f82b9d |
| 3359 | 2026-08-14T18:18:39.282Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 3360 | 2026-08-14T18:18:51.730Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:f4519402607328a3 | passed | b7a8a3b55b82905dff0e58e09c71b2389bb816493471e5bc1b1d6c98e8f82b9d | False | 1107 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| ce3ddd96de65434baa88e7e854502dc0 | accepted | 5decaa48300b10a6df39676c677745bc881cd7d9 | 91dc0d6108352981d1cad2cf1d195289e46554315b3a95ed4060f8a3335fb02f | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `13`
- Chain head: `618202f20c2e29f0e5e38260e0b989045d35f876c194fc3e5391d586e85f5f10`
