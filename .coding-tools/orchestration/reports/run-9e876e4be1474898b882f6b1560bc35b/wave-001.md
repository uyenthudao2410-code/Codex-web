# Orchestration Wave 1

- Run: `9e876e4be1474898b882f6b1560bc35b`
- Wave: `626716c8eaba49c68f134a4ae213dd97`
- Objective: P1.C executor proof: add a focused integration test using a temporary local git repository to exercise explicit controlled replay execution. The test must create two counterbalanced pairs (four trials), verify every trial starts at the exact clean base HEAD, executes caller-supplied argv, records hashes/timing without inferring acceptance, and cleans temporary worktrees. This is software verification only and must not be treated as benchmark/ROI evidence.
- Mode: `mcp_only`
- Base HEAD: `7236cd6a72c27e6eb7679585c115220cc54ae842`
- Worktree fingerprint: `0cf089766a2b340b89d3e3151e5c93b5fdc547bdb6d0d162f52146630ac042c4`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 4953 | 2026-08-15T08:14:20.427Z | run_started |  | PREFLIGHT |  |
| 4954 | 2026-08-15T08:14:21.114Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 4955 | 2026-08-15T08:14:21.461Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 4956 | 2026-08-15T08:14:21.630Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 4957 | 2026-08-15T08:14:21.845Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 4958 | 2026-08-15T08:14:22.076Z | state_transition | READY | ROUTED | reason=route_selected |
| 4959 | 2026-08-15T08:14:22.937Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=f01df87d6f8041f494817a5856ab929e |
| 4960 | 2026-08-15T08:14:23.154Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 4961 | 2026-08-15T08:14:24.158Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=f01df87d6f8041f494817a5856ab929e |
| 4962 | 2026-08-15T08:14:24.433Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 4963 | 2026-08-15T08:14:25.030Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=aff076cb970fc5bb6d50d0ff88d947458a48145d8973166fbd47f661b5ad2d6e |
| 4964 | 2026-08-15T08:14:31.099Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=aff076cb970fc5bb6d50d0ff88d947458a48145d8973166fbd47f661b5ad2d6e |
| 4965 | 2026-08-15T08:14:31.818Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 4966 | 2026-08-15T08:14:41.363Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | aff076cb970fc5bb6d50d0ff88d947458a48145d8973166fbd47f661b5ad2d6e | False | 5640 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| f887b4b61ae34cb7b15f40fd07ea8df3 | accepted | 7236cd6a72c27e6eb7679585c115220cc54ae842 | 3a334f033d1dc8721ce3798cd31864ac9081b5435e9a76b5591ec8a900cd3e0f | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `14`
- Chain head: `4b87110e640f1b2661d8402bcff8a8060607c495eeec3204f22896c8bea016e2`
