# Orchestration Wave 1

- Run: `6496bfac04de471087ad596fd8f47197`
- Wave: `ae7c874139cf48b29567b754e5e7e4cf`
- Objective: P1 live proof-cache negative-control after a controlled relevant source-tree change. Use the exact same oracle command/workdir/config as the baseline and exact-repeat runs, with a new agent_workflow idempotency key. The changed source worktree fingerprint must invalidate the prior proof, so this opportunity must be a cache miss and run the real pytest oracle. Do not make additional source changes.
- Mode: `mcp_only`
- Base HEAD: `29a1318bf09f893aca0fbc2c13de3429d9b2fdb9`
- Worktree fingerprint: `4dd0016a6e2b0e1f4ad2bba4f2d516912dda5722139134d216472102859bef78`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 640 | 2026-08-14T00:19:30.636Z | run_started |  | PREFLIGHT |  |
| 641 | 2026-08-14T00:19:30.981Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 642 | 2026-08-14T00:19:31.063Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 643 | 2026-08-14T00:19:31.176Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 644 | 2026-08-14T00:19:31.271Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 645 | 2026-08-14T00:19:31.414Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 646 | 2026-08-14T00:19:31.510Z | state_transition | READY | ROUTED | reason=route_selected |
| 647 | 2026-08-14T00:19:31.860Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=e63e7dc0479d478da7e1534711c32b09 |
| 648 | 2026-08-14T00:19:31.985Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 649 | 2026-08-14T00:19:32.332Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=e63e7dc0479d478da7e1534711c32b09 |
| 650 | 2026-08-14T00:19:32.453Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 651 | 2026-08-14T00:19:33.783Z | proof_recorded |  |  | stage_id=check:1a5079f2f84e1082; status=passed; cache_hit=False; input_fingerprint=1088256b6fa75e57aa5489fdc82eee45ac6d130a71bda0045715fab1bca77d70 |
| 652 | 2026-08-14T00:19:33.905Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 653 | 2026-08-14T00:19:51.585Z | state_transition | ACCEPTING | CHECKPOINTED | reason=chatweb_sol_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:1a5079f2f84e1082 | passed | 1088256b6fa75e57aa5489fdc82eee45ac6d130a71bda0045715fab1bca77d70 | False | 950 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| b8b581f375bb4ec49c101fe282d85a7a | accepted | 29a1318bf09f893aca0fbc2c13de3429d9b2fdb9 | bfe50c3bcee8fdaabb6cc40352bf14e3c05e2238f3c54d9a191d5c247e1fc8d8 | ChatWeb Sol |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `14`
- Chain head: `cb620d60ac7c30bf7a63b68ecdd7ea7242e0dd79c0a26a238ff2e0ae719496cd`
