# Orchestration Wave 1

- Run: `cb2c9c6255ad409cadc14c2c4e8d8395`
- Wave: `2109f1637d3b4ccf981efa286f0e1bb0`
- Objective: Prove the already-applied test-oracle race fix in resources/coding-tools-mcp/tests/test_resilience_fault_injection.py. The only intended change waits for child.pid to contain a parseable positive PID instead of treating file existence as publication completion. Do not mutate source, do not call providers/reviewers, and do not touch stale Execution Hub runs.
- Mode: `mcp_only`
- Base HEAD: `dff81e251836666fc825c40bf86e4167afd29c39`
- Worktree fingerprint: `2c35dc3912da8a5424ab2f469e13f9fc7a9e324bbc8549fb575435f3bb9dfd45`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 4583 | 2026-08-15T06:27:34.952Z | run_started |  | PREFLIGHT |  |
| 4584 | 2026-08-15T06:27:35.532Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 4585 | 2026-08-15T06:27:39.599Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 4586 | 2026-08-15T06:27:39.834Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 4587 | 2026-08-15T06:27:40.075Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 4588 | 2026-08-15T06:27:40.280Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 4589 | 2026-08-15T06:27:40.561Z | state_transition | READY | ROUTED | reason=route_selected |
| 4590 | 2026-08-15T06:27:41.247Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=89472f302fca4349814b37344c2e064f |
| 4591 | 2026-08-15T06:27:41.425Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 4592 | 2026-08-15T06:27:42.133Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=89472f302fca4349814b37344c2e064f |
| 4593 | 2026-08-15T06:27:42.318Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 4594 | 2026-08-15T06:27:42.789Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=962247af4598e8b56c5fca345983d26d92802df9b8ba5ac264b7d4edfc75e09f |
| 4595 | 2026-08-15T06:27:46.945Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=962247af4598e8b56c5fca345983d26d92802df9b8ba5ac264b7d4edfc75e09f |
| 4596 | 2026-08-15T06:27:47.152Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 4597 | 2026-08-15T06:27:59.840Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 962247af4598e8b56c5fca345983d26d92802df9b8ba5ac264b7d4edfc75e09f | False | 3781 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 20772ffebc2b4be093f59fd634570854 | accepted | dff81e251836666fc825c40bf86e4167afd29c39 | 217fc86458f4aa084b5ed80c5d9440e7bbb60cecc2925ed2428727b4705a71d0 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `15`
- Chain head: `b29399c903775f086844eaa7c4599ae301555d312434eb74385873750d27c80c`
