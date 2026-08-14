# Orchestration Wave 1

- Run: `b609d40619fd4907847de66edfeb1396`
- Wave: `0e0338a49c6e418ea31478f7d6dc1227`
- Objective: P1 live proof-cache canary, second exact proof opportunity. Use the exact same oracle command, workdir, source state, and proof configuration as the accepted baseline miss, but a different agent_workflow idempotency key. Expect proof-cache reuse rather than command execution. Do not modify project source. Return cache_hit, proof id/input fingerprint, cache_hits, cache_saved_ms, and worktree_fp.
- Mode: `mcp_only`
- Base HEAD: `29a1318bf09f893aca0fbc2c13de3429d9b2fdb9`
- Worktree fingerprint: `4859c9361d95ab356b83df7ee387ead067f15bc412fcc639dac312fd17ccb140`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 613 | 2026-08-14T00:18:09.338Z | run_started |  | PREFLIGHT |  |
| 614 | 2026-08-14T00:18:09.661Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 615 | 2026-08-14T00:18:09.765Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 616 | 2026-08-14T00:18:09.876Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 617 | 2026-08-14T00:18:09.993Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 618 | 2026-08-14T00:18:10.098Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 619 | 2026-08-14T00:18:10.196Z | state_transition | READY | ROUTED | reason=route_selected |
| 620 | 2026-08-14T00:18:10.543Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=6c127e793b7a436e90e2ddf332af0273 |
| 621 | 2026-08-14T00:18:10.655Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 622 | 2026-08-14T00:18:11.018Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=6c127e793b7a436e90e2ddf332af0273 |
| 623 | 2026-08-14T00:18:11.130Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 624 | 2026-08-14T00:18:11.413Z | proof_cache_hit |  |  | stage_id=check:1a5079f2f84e1082; input_fingerprint=3406a7d27b77c54c2570fcb2b59a123b68a449d0cf9d7209d2d782460ee97e90 |
| 625 | 2026-08-14T00:18:11.564Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 626 | 2026-08-14T00:18:24.394Z | state_transition | ACCEPTING | CHECKPOINTED | reason=chatweb_sol_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| - | - | - | - | - | - |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| c7707a34a3e546058c49b7a387f1e7a8 | accepted | 29a1318bf09f893aca0fbc2c13de3429d9b2fdb9 |  | ChatWeb Sol |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `14`
- Chain head: `593740342446e9adbca93f589e19a40f85ea91495b1cde4cc5c8825a9ce113b0`
