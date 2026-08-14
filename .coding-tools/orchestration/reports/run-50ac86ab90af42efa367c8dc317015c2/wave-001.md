# Orchestration Wave 1

- Run: `50ac86ab90af42efa367c8dc317015c2`
- Wave: `0090feac642b42bdb4eacc1ba2c886d6`
- Objective: Create one temporary source-tree canary file owned by this P1 verification to create a controlled relevant source/worktree fingerprint change without modifying any existing file. Preserve all unrelated work and do not commit. The canary will be removed after the live invalidation measurement.
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
| 627 | 2026-08-14T00:19:10.448Z | run_started |  | PREFLIGHT |  |
| 628 | 2026-08-14T00:19:10.757Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 629 | 2026-08-14T00:19:10.860Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 630 | 2026-08-14T00:19:10.985Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 631 | 2026-08-14T00:19:11.112Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 632 | 2026-08-14T00:19:11.219Z | state_transition | READY | ROUTED | reason=route_selected |
| 633 | 2026-08-14T00:19:11.579Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=956091af616d49d2acc99e09b61e4041 |
| 634 | 2026-08-14T00:19:11.696Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 635 | 2026-08-14T00:19:12.076Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=956091af616d49d2acc99e09b61e4041 |
| 636 | 2026-08-14T00:19:12.191Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 637 | 2026-08-14T00:19:12.645Z | proof_recorded |  |  | stage_id=check:dfc42600689b995a; status=passed; cache_hit=False; input_fingerprint=2291adfebb509a01d7ec9a8f14042ab78ca15dd7994405afaea41fdd3b18f7e3 |
| 638 | 2026-08-14T00:19:12.873Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 639 | 2026-08-14T00:19:24.967Z | state_transition | ACCEPTING | CHECKPOINTED | reason=chatweb_sol_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:dfc42600689b995a | passed | 2291adfebb509a01d7ec9a8f14042ab78ca15dd7994405afaea41fdd3b18f7e3 | False | 83 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 671afee12eb2454493abd5161bf66de6 | accepted | 29a1318bf09f893aca0fbc2c13de3429d9b2fdb9 | 5c149b78506b22271bc62f948446d2a1e342cf8ff426ead5df7bef9e4eff7c60 | ChatWeb Sol |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `13`
- Chain head: `1a2d074c47ba48033aa30e231a172418f865a4f33f970a3472f8e1a50ff8364c`
