# Orchestration Wave 1

- Run: `0331381d732443a4beae92fec661067c`
- Wave: `f97ecc4a14c449f2b7d89ae01632b18f`
- Objective: Run the focused P0 causal-evaluation regression suite against the exact current dirty worktree. Do not mutate source unless a failing test requires a separately reasoned replan; this run is proof-only.
- Mode: `mcp_only`
- Base HEAD: `7236cd6a72c27e6eb7679585c115220cc54ae842`
- Worktree fingerprint: `5993fbd75d3810d46e0f228a924a89a6d7e3a2059518f4f8362fa84fff8ba2cf`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 4807 | 2026-08-15T07:46:48.979Z | run_started |  | PREFLIGHT |  |
| 4808 | 2026-08-15T07:46:49.687Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 4809 | 2026-08-15T07:47:38.827Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 4810 | 2026-08-15T07:47:39.026Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 4811 | 2026-08-15T07:47:39.213Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 4812 | 2026-08-15T07:47:39.410Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 4813 | 2026-08-15T07:47:39.630Z | state_transition | READY | ROUTED | reason=route_selected |
| 4814 | 2026-08-15T07:47:40.366Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=dae0bd34236947aea0b06cec580121a5 |
| 4815 | 2026-08-15T07:47:40.559Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 4816 | 2026-08-15T07:47:41.362Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=dae0bd34236947aea0b06cec580121a5 |
| 4817 | 2026-08-15T07:47:41.559Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 4818 | 2026-08-15T07:47:42.069Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=fdcff4499dc00466135ee419a0add19964758603abecf82a2aefca264a3602e6 |
| 4819 | 2026-08-15T07:48:28.236Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=fdcff4499dc00466135ee419a0add19964758603abecf82a2aefca264a3602e6 |
| 4820 | 2026-08-15T07:48:28.457Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 4821 | 2026-08-15T07:48:38.348Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | fdcff4499dc00466135ee419a0add19964758603abecf82a2aefca264a3602e6 | False | 45811 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| fac3eefb2d034ff2b8d9632ae7d94802 | accepted | 7236cd6a72c27e6eb7679585c115220cc54ae842 | 803e2cf4f5a396c016670bc695e79d2628789615424bc8f959ea18f9faf72ecf | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `15`
- Chain head: `f99a3e8b748fe3e4efcb04c66d8dabe269d65bc8c6ca927c126d497831388fbb`
