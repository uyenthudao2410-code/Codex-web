# Orchestration Wave 1

- Run: `1cff8400384c4fab8a8d6833db31f7e8`
- Wave: `4f9b0b3dddd94db89d050ee3533ff897`
- Objective: Make organic post-fix measurement observable without creating a run: when agent_workflow terminates on a known no-write patch-preflight failure, persist a content-free workflow_patch_preflight boolean in the durable idempotency summary alongside error_code/outcome_unknown. This lets later baseline analysis count avoided orchestration replans without synthetic workload. Add focused assertion only. No routing/provider/reviewer/restart changes.
- Mode: `mcp_only`
- Base HEAD: `dff81e251836666fc825c40bf86e4167afd29c39`
- Worktree fingerprint: `2e13e7089b9db2b20a0981a4e9c347e0ad76b5f1802aad208ecd7c82d52776b2`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 4469 | 2026-08-15T05:35:24.460Z | run_started |  | PREFLIGHT |  |
| 4470 | 2026-08-15T05:35:24.648Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 4471 | 2026-08-15T05:35:24.853Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 4472 | 2026-08-15T05:35:25.074Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 4473 | 2026-08-15T05:35:25.273Z | state_transition | READY | ROUTED | reason=route_selected |
| 4474 | 2026-08-15T05:35:25.920Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=8161433e97624d83a16be25b65184f0f |
| 4475 | 2026-08-15T05:35:26.135Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 4476 | 2026-08-15T05:35:26.920Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=8161433e97624d83a16be25b65184f0f |
| 4477 | 2026-08-15T05:35:27.105Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 4478 | 2026-08-15T05:35:27.582Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=06f46fdde8892b1758853a525b56e5ef8de6621b8618abf6c700883702ae7cb6 |
| 4479 | 2026-08-15T05:35:31.482Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=06f46fdde8892b1758853a525b56e5ef8de6621b8618abf6c700883702ae7cb6 |
| 4480 | 2026-08-15T05:35:32.172Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 4481 | 2026-08-15T05:36:29.430Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 06f46fdde8892b1758853a525b56e5ef8de6621b8618abf6c700883702ae7cb6 | False | 3500 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| e677a10c823f4e35a15630bfdb520ef7 | accepted | dff81e251836666fc825c40bf86e4167afd29c39 | 1ad0b232328f915169853e065c51a726fed2965a623e7fa707bc364a0b5391aa | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `13`
- Chain head: `6bc070af3bf23e7d8bd25a98678f78f6a413a6b729364a021cdb869df555f99a`
