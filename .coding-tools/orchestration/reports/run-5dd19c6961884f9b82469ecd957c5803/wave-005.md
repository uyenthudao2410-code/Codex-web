# Orchestration Wave 5

- Run: `5dd19c6961884f9b82469ecd957c5803`
- Wave: `449ccb830523455c877ba5f8213901c8`
- Objective: Final read-only audit of the retained current documentation after the English-only cleanup. Check the retained docs for obsolete standalone WebCodex/server/runner/OAuth/GPT Actions/Docker operational guidance, broken references to deleted documentation, and any non-English maintained-doc content. Focus on TESTING.md, ROADMAP.md, RELEASE_CHECKLIST.md plus the newly rewritten current docs and root guidance. Return exact remaining cleanup items only; do not mutate.
- Mode: `mcp_only`
- Base HEAD: `cf6cb6ddbf29d90515d003ce72490ffda985c37f`
- Worktree fingerprint: `bd178a6ecfb19cc7d80aea621d69d86ea9a986e4ecac897c8cd6bcdf92a99cdc`
- Contract fingerprint: `1c6f9f376298f5e3438fa67afdd134bd8a536d9384d23baa3aa581399c5f58d0`
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 7479 | 2026-08-16T11:41:45.023Z | wave_replanned |  | PREFLIGHT | reason=Move the pure placement policy/evaluator into the small side-effect-free webcodex-core crate so behavior tests execute cheaply; keep root as a thin ShellClientRegistry adapter and type-check root tests without relinking the monolithic test binary. Also make MEDIUM explicitly local in V1. |
| 7480 | 2026-08-16T11:41:45.167Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 7481 | 2026-08-16T11:41:45.296Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 7482 | 2026-08-16T11:41:45.423Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 7483 | 2026-08-16T11:41:45.538Z | state_transition | READY | ROUTED | reason=route_selected |
| 7484 | 2026-08-16T11:41:46.037Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=0e31f204e06348cbb03f29916a898bb8 |
| 7485 | 2026-08-16T11:41:46.171Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 7486 | 2026-08-16T11:41:46.679Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=0e31f204e06348cbb03f29916a898bb8 |
| 7487 | 2026-08-16T11:41:46.786Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 7488 | 2026-08-16T11:41:47.245Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:718b79fbd1bef7b9; input_fingerprint=0d76ad7394d316415c723d96fd8a51946fa5cb0033c0a7003cc2146653decf37 |
| 7489 | 2026-08-16T11:41:47.513Z | managed_process_admitted |  |  | owner=default |
| 7490 | 2026-08-16T11:41:47.720Z | managed_process_started |  |  | owner=default |
| 7491 | 2026-08-16T11:41:53.737Z | managed_process_terminal |  |  | owner=default |
| 7492 | 2026-08-16T11:41:53.952Z | proof_recorded |  |  | stage_id=check:718b79fbd1bef7b9; status=passed; cache_hit=False; input_fingerprint=0d76ad7394d316415c723d96fd8a51946fa5cb0033c0a7003cc2146653decf37 |
| 7493 | 2026-08-16T11:41:54.117Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:810e75f0d3dee10e; input_fingerprint=e0a81b76f160c2aec7b0d262a1fe2877a113da5a41ef6922bf0d04b400bf9ed1 |
| 7494 | 2026-08-16T11:41:54.367Z | managed_process_admitted |  |  | owner=default |
| 7495 | 2026-08-16T11:41:54.593Z | managed_process_started |  |  | owner=default |
| 7496 | 2026-08-16T11:42:00.145Z | managed_process_terminal |  |  | owner=default |
| 7497 | 2026-08-16T11:42:00.422Z | proof_recorded |  |  | stage_id=check:810e75f0d3dee10e; status=passed; cache_hit=False; input_fingerprint=e0a81b76f160c2aec7b0d262a1fe2877a113da5a41ef6922bf0d04b400bf9ed1 |
| 7498 | 2026-08-16T11:42:00.533Z | proof_cache_miss |  |  | reason=cold; stage_id=check:c14be7b9ffb554d1; input_fingerprint=10b1de14c5fdcf9bbe8608780a01a90bd1a4d0706fb53fa3d899fe1ced1f8bfe |
| 7499 | 2026-08-16T11:42:00.820Z | managed_process_admitted |  |  | owner=default |
| 7500 | 2026-08-16T11:42:01.305Z | managed_process_started |  |  | owner=default |
| 7501 | 2026-08-16T11:42:14.222Z | managed_process_terminal |  |  | owner=default |
| 7502 | 2026-08-16T11:42:14.429Z | proof_recorded |  |  | stage_id=check:c14be7b9ffb554d1; status=passed; cache_hit=False; input_fingerprint=10b1de14c5fdcf9bbe8608780a01a90bd1a4d0706fb53fa3d899fe1ced1f8bfe |
| 7503 | 2026-08-16T11:42:14.816Z | proof_cache_miss |  |  | reason=cold; stage_id=check:67144c3fff08377b; input_fingerprint=a065acb376227762d6a906b6d01059a9df25373caa5a459d45a6a6c9aec07394 |
| 7504 | 2026-08-16T11:42:15.113Z | managed_process_admitted |  |  | owner=default |
| 7505 | 2026-08-16T11:42:15.363Z | managed_process_started |  |  | owner=default |
| 7506 | 2026-08-16T11:42:30.229Z | managed_process_terminal |  |  | owner=default |
| 7507 | 2026-08-16T11:42:30.500Z | proof_recorded |  |  | stage_id=check:67144c3fff08377b; status=failed; cache_hit=False; input_fingerprint=a065acb376227762d6a906b6d01059a9df25373caa5a459d45a6a6c9aec07394 |
| 7508 | 2026-08-16T11:42:30.649Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 7509 | 2026-08-16T11:42:30.975Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 7510 | 2026-08-16T11:42:31.227Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:718b79fbd1bef7b9 | passed | 0d76ad7394d316415c723d96fd8a51946fa5cb0033c0a7003cc2146653decf37 | False | 6500 | 0 |
| check:810e75f0d3dee10e | passed | e0a81b76f160c2aec7b0d262a1fe2877a113da5a41ef6922bf0d04b400bf9ed1 | False | 6058 | 0 |
| check:c14be7b9ffb554d1 | passed | 10b1de14c5fdcf9bbe8608780a01a90bd1a4d0706fb53fa3d899fe1ced1f8bfe | False | 13694 | 0 |
| check:67144c3fff08377b | failed | a065acb376227762d6a906b6d01059a9df25373caa5a459d45a6a6c9aec07394 | False | 15442 | 101 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `165`
- Chain head: `84646e17dcd093b7f8ac7fbaa70bfe2f6e5ccd2b20c2afb11107e0eb396c6e43`
