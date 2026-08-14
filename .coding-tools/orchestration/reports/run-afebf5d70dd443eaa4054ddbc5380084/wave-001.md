# Orchestration Wave 1

- Run: `afebf5d70dd443eaa4054ddbc5380084`
- Wave: `7180d92737da41ff995b96f077748c32`
- Objective: Implement Execution Hub backend state primitives only: durable Hub client registry, monotonic per-client event cursors, separate controller lease with monotonic fencing token/TTL, operator transfer only to an online registered client, and focused persistence/contention/expiry tests. Do not modify server public schemas, panel, proxy, routing, or existing P1.5 behavior in this wave.
- Mode: `mcp_only`
- Base HEAD: `5f756b5f9a4ab29ca84401314bcc72efc17ae31b`
- Worktree fingerprint: `9e8c458a4a9aa910f1010d6d3c9310d671e8f9445176c2ae431fe9349f65c3ae`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 905 | 2026-08-14T05:04:46.614Z | run_started |  | PREFLIGHT |  |
| 906 | 2026-08-14T05:04:47.114Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 907 | 2026-08-14T05:04:47.274Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 908 | 2026-08-14T05:04:47.422Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 909 | 2026-08-14T05:04:47.705Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 910 | 2026-08-14T05:04:47.889Z | state_transition | READY | ROUTED | reason=route_selected |
| 911 | 2026-08-14T05:04:48.505Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=1b4924061c514b96b05d98966b35ec4e |
| 912 | 2026-08-14T05:04:48.673Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 913 | 2026-08-14T05:04:49.508Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=1b4924061c514b96b05d98966b35ec4e |
| 914 | 2026-08-14T05:04:49.689Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 915 | 2026-08-14T05:04:53.588Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=38e06dd6c08bb85f24768e6963cb60863f0d8ed152fb2bab0dcfc84e3085492b |
| 916 | 2026-08-14T05:04:53.924Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 917 | 2026-08-14T05:05:11.764Z | failure_observed | ACCEPTING | ACCEPTING | reason=Critical review: new hub_client_cursors/controller_leases must be referentially bound to real orchestration runs (and cursor/client identity where appropriate). Current green implementation permits orphan controller/cursor rows for nonexistent run ids. Add FK/validation and prove invalid references fail before acceptance.; failure_class=SOL_REJECTED |
| 918 | 2026-08-14T05:05:11.948Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 38e06dd6c08bb85f24768e6963cb60863f0d8ed152fb2bab0dcfc84e3085492b | False | 3186 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `36`
- Chain head: `fc53484f19e8f2b0276989e9ea53f7dad57aa6af35543dd9f5301b8cb447d5c8`
