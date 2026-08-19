# Orchestration Wave 1

- Run: `bc54f7f039c8497887e51f39b931139d`
- Wave: `e40fedee9c2c4895b83fc34dda01c738`
- Objective: Verify the existing Execution Hub reconnect/fault regression suite against the corrected multi-root source. Do not modify source. This is the second half of the prior combined oracle, run independently to distinguish a real regression from runtime/orchestration interference.
- Mode: `mcp_only`
- Base HEAD: `7c1c93ea72fa3465d718f7826494629426c1a9e8`
- Worktree fingerprint: `109c2d82d04f83197647a5d1a295bcd3edbd06d8724634041a64d7674ceefb78`
- Contract fingerprint: ``
- Status: **aborted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 19741 | 2026-08-19T05:05:19.755Z | run_started |  | PREFLIGHT |  |
| 19742 | 2026-08-19T05:05:20.162Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 19743 | 2026-08-19T05:05:20.363Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 19744 | 2026-08-19T05:05:20.537Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 19745 | 2026-08-19T05:05:20.724Z | state_transition | READY | ROUTED | reason=route_selected |
| 19746 | 2026-08-19T05:05:21.270Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=ebc94555389f48c9895a5fb39c1ba576 |
| 19747 | 2026-08-19T05:05:21.405Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 19748 | 2026-08-19T05:05:21.677Z | managed_process_admitted |  |  | owner=chatweb |
| 19749 | 2026-08-19T05:05:21.891Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=ebc94555389f48c9895a5fb39c1ba576 |
| 19750 | 2026-08-19T05:05:21.981Z | managed_process_started |  |  | owner=chatweb |
| 19751 | 2026-08-19T05:05:22.129Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 19752 | 2026-08-19T05:05:23.093Z | proof_cache_miss |  |  | reason=cold; stage_id=check:b61ae36d8167459a; input_fingerprint=27b9670daeddc41198b1bd3cd022349c3694181a7baab11a13e4ede57e365499 |
| 19753 | 2026-08-19T05:05:23.438Z | managed_process_admitted |  |  | owner=default |
| 19754 | 2026-08-19T05:05:23.684Z | managed_process_started |  |  | owner=default |
| 19755 | 2026-08-19T05:05:24.693Z | managed_process_terminal |  |  | owner=chatweb |
| 19756 | 2026-08-19T05:05:29.371Z | state_transition | PROVING | ABORTED | reason=task_replaced |
| 19757 | 2026-08-19T05:05:29.936Z | managed_process_terminal |  |  | owner=default |
| 19758 | 2026-08-19T05:05:30.276Z | proof_recorded |  |  | stage_id=check:b61ae36d8167459a; status=passed; cache_hit=False; input_fingerprint=27b9670daeddc41198b1bd3cd022349c3694181a7baab11a13e4ede57e365499 |
| 19759 | 2026-08-19T05:05:30.278Z | wave_processes_quiesced |  |  | reason=orchestration_state:aborted |
| 19760 | 2026-08-19T05:05:30.638Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:b61ae36d8167459a | passed | 27b9670daeddc41198b1bd3cd022349c3694181a7baab11a13e4ede57e365499 | False | 6824 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `20`
- Chain head: `b6cc55778aa1973191a39974890d3202082ab1c31ea56d6a6ba52de119317129`
