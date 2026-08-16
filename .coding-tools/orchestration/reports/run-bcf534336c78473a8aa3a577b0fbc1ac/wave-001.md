# Orchestration Wave 1

- Run: `bcf534336c78473a8aa3a577b0fbc1ac`
- Wave: `9b69917c875f451baa0186830db585d5`
- Objective: Continue P0 proof only. Source patches are already applied. Re-run the focused Python tests from the Coding Tools MCP package directory; the previous failure was test-runner cwd/import setup, not a code assertion. Preserve the already-passed Node packaging proof and diff-check evidence. No new source changes unless a real test assertion fails.
- Mode: `mcp_only`
- Base HEAD: `8581b8331e83cc600c2b813629875639e48a8245`
- Worktree fingerprint: `512437386ea8bd786a5257ce02c41b0e003639c5b18e0248e8da772a38ccf182`
- Contract fingerprint: ``
- Status: **active**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 3592 | 2026-08-15T00:03:58.852Z | run_started |  | PREFLIGHT |  |
| 3593 | 2026-08-15T00:03:59.065Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 3594 | 2026-08-15T00:03:59.251Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 3595 | 2026-08-15T00:03:59.443Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 3596 | 2026-08-15T00:03:59.654Z | state_transition | READY | ROUTED | reason=route_selected |
| 3597 | 2026-08-15T00:04:00.418Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=da992d77c004417da96bdced24cda0ca |
| 3598 | 2026-08-15T00:04:00.545Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 3599 | 2026-08-15T00:04:01.017Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=da992d77c004417da96bdced24cda0ca |
| 3600 | 2026-08-15T00:04:01.154Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 3601 | 2026-08-15T00:04:01.589Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=0ff17c5a1e33f3db21bb56ba7feb8391fb64bd85078c0512d4520013af67e7c3 |
| 3602 | 2026-08-15T00:04:15.376Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=0ff17c5a1e33f3db21bb56ba7feb8391fb64bd85078c0512d4520013af67e7c3 |
| 3603 | 2026-08-15T00:04:15.751Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 5573 | 2026-08-16T00:33:51.448Z | failure_observed | ACCEPTING | ACCEPTING | reason=Stale unrelated P0 acceptance lineage: audited proof is green for historical base_head 8581b833... and worktree fingerprint 512437..., while the current P2/P3 checkout is on a different base/worktree. Reject rather than falsely accepting evidence that does not bind to the current source state.; failure_class=SOL_REJECTED |
| 5574 | 2026-08-16T00:33:51.566Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 0ff17c5a1e33f3db21bb56ba7feb8391fb64bd85078c0512d4520013af67e7c3 | False | 13453 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `14`
- Chain head: `c593ddb6a9e380565d91f33c14df1ca9644e5f850301c42ace24737ea18507ee`
