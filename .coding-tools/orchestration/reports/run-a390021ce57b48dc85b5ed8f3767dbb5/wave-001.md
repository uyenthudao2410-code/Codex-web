# Orchestration Wave 1

- Run: `a390021ce57b48dc85b5ed8f3767dbb5`
- Wave: `fef95a8925564ab092cf46ac1cebfa28`
- Objective: P1.A1 proof repair: correct the critical-path test expectation for the four explicit cross-clock dependency edges. Production DAG implementation is unchanged because the failed assertion showed the implementation counted the graph correctly. Re-run the focused ledger suite only.
- Mode: `mcp_only`
- Base HEAD: `7236cd6a72c27e6eb7679585c115220cc54ae842`
- Worktree fingerprint: `17de4574c428c18d425b40bccc2aa62303debbc451f949564414db6cdf726010`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 4855 | 2026-08-15T08:04:45.214Z | run_started |  | PREFLIGHT |  |
| 4856 | 2026-08-15T08:04:45.738Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 4857 | 2026-08-15T08:04:45.914Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 4858 | 2026-08-15T08:04:46.206Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 4859 | 2026-08-15T08:04:46.441Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 4860 | 2026-08-15T08:04:46.671Z | state_transition | READY | ROUTED | reason=route_selected |
| 4861 | 2026-08-15T08:04:47.330Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=48fb5522925a479f8caa9491d77ac331 |
| 4862 | 2026-08-15T08:04:47.546Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 4863 | 2026-08-15T08:04:48.190Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=48fb5522925a479f8caa9491d77ac331 |
| 4864 | 2026-08-15T08:04:48.380Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 4865 | 2026-08-15T08:04:48.848Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=ffde87b7a58faa9d906fb4aa633d04297a0368bd16fce78172276fafdc405ea2 |
| 4866 | 2026-08-15T08:04:59.750Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=ffde87b7a58faa9d906fb4aa633d04297a0368bd16fce78172276fafdc405ea2 |
| 4867 | 2026-08-15T08:05:00.406Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 4868 | 2026-08-15T08:05:11.106Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | ffde87b7a58faa9d906fb4aa633d04297a0368bd16fce78172276fafdc405ea2 | False | 10405 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| b9c24877e25a44ca87de66bbe5362360 | accepted | 7236cd6a72c27e6eb7679585c115220cc54ae842 | 1eb865e944d872bf784fea0227a4be24e76f5997d94bf892af2c024a789fd13b | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `14`
- Chain head: `c82afbc14e1fe08812fb44c2c9b8ca783818bf084a2406b6be2d88e7a96332ee`
