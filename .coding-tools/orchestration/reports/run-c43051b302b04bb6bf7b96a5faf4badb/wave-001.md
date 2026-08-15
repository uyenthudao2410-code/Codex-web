# Orchestration Wave 1

- Run: `c43051b302b04bb6bf7b96a5faf4badb`
- Wave: `6a988db78dfe44aeb4835f02a886139f`
- Objective: P4B expose accepted P4A routing_promotion_readiness through routing_evidence and add focused regression tests. Tests must prove known benchmark fixtures and unverified samples are excluded from representative counts, and that even 10 explicitly representative accepted Luna samples across 3 task classes remain HOLD while critical-defect evidence is unknown. Keep automatic_activation=false and provider router shadow-only.
- Mode: `mcp_only`
- Base HEAD: `e45bed968bee6db46bb3041de179cbcf23e3906b`
- Worktree fingerprint: `02733ab28342eae0d9de8d0c2ca3b1378ec429b1c5fc906dd0212933f615a383`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 3388 | 2026-08-14T18:27:47.995Z | run_started |  | PREFLIGHT |  |
| 3389 | 2026-08-14T18:27:48.272Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 3390 | 2026-08-14T18:27:48.620Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 3391 | 2026-08-14T18:27:48.974Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 3392 | 2026-08-14T18:27:49.295Z | state_transition | READY | ROUTED | reason=route_selected |
| 3393 | 2026-08-14T18:27:50.086Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=300f6314d5ad4e28a70943a1452ab374 |
| 3394 | 2026-08-14T18:27:50.338Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 3395 | 2026-08-14T18:27:51.437Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=300f6314d5ad4e28a70943a1452ab374 |
| 3396 | 2026-08-14T18:27:51.760Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 3397 | 2026-08-14T18:27:52.213Z | proof_cache_miss |  |  | reason=cold; stage_id=check:82d3a32a172e2d9c; input_fingerprint=50662834cbfba4629799acfb62694e296a92b4051c281609d70b1b9f2a20eb81 |
| 3398 | 2026-08-14T18:27:54.452Z | proof_recorded |  |  | stage_id=check:82d3a32a172e2d9c; status=passed; cache_hit=False; input_fingerprint=50662834cbfba4629799acfb62694e296a92b4051c281609d70b1b9f2a20eb81 |
| 3399 | 2026-08-14T18:27:54.803Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 3400 | 2026-08-14T18:28:11.281Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:82d3a32a172e2d9c | passed | 50662834cbfba4629799acfb62694e296a92b4051c281609d70b1b9f2a20eb81 | False | 1623 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 88fd485b41ce4554b848d60a7d129de4 | accepted | e45bed968bee6db46bb3041de179cbcf23e3906b | c682f1cf532cb091af1290027aa84c03a55b9b653db0595799247f83799e6b3c | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `13`
- Chain head: `5890aa142e1bdbe45c87787b6957001fa19eec81d91be25da74ad2993065c7df`
