# Orchestration Wave 1

- Run: `7ce1f4c4d5ea4fa0a4dad8bbe6b1dec2`
- Wave: `d8ce0b55ced745b5941ba189685467fa`
- Objective: P1.D: add an operational evaluation-plane reporter that summarizes the independent Electron host-visible journal, reports p50/p90 user-visible-to-first-assistant-visible spans without calling them model latency, reports ledger critical-path DAG for an explicit run when requested, and marks host-to-run correlation unlinked unless an explicitly correlated host observation span with trace/turn identity exists in that run. Also update exact smart-v3 contract SHA expectations to the new deterministic source contract after task_control observation was added. Add focused tests.
- Mode: `mcp_only`
- Base HEAD: `7236cd6a72c27e6eb7679585c115220cc54ae842`
- Worktree fingerprint: `76c9df74584ef5a3e1d5df49dd75b3793fff289ca6a47152de687cad03caf275`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 4939 | 2026-08-15T08:13:30.033Z | run_started |  | PREFLIGHT |  |
| 4940 | 2026-08-15T08:13:30.744Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 4941 | 2026-08-15T08:13:30.894Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 4942 | 2026-08-15T08:13:31.097Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 4943 | 2026-08-15T08:13:31.273Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 4944 | 2026-08-15T08:13:31.530Z | state_transition | READY | ROUTED | reason=route_selected |
| 4945 | 2026-08-15T08:13:32.466Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=24f43d4e3edd4b5ba95a3cf25767ad66 |
| 4946 | 2026-08-15T08:13:32.722Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 4947 | 2026-08-15T08:13:33.837Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=24f43d4e3edd4b5ba95a3cf25767ad66 |
| 4948 | 2026-08-15T08:13:34.050Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 4949 | 2026-08-15T08:13:34.792Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=70f4d766942bbee889d3c8cc22364329ae71a0735c3a242707d30f57255e1846 |
| 4950 | 2026-08-15T08:13:48.805Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=70f4d766942bbee889d3c8cc22364329ae71a0735c3a242707d30f57255e1846 |
| 4951 | 2026-08-15T08:13:50.221Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 4952 | 2026-08-15T08:14:02.208Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 70f4d766942bbee889d3c8cc22364329ae71a0735c3a242707d30f57255e1846 | False | 13530 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| c7bc4fafb6ae45d5b3b4190bc443be0d | accepted | 7236cd6a72c27e6eb7679585c115220cc54ae842 | 8832362d35626ce5763d9a27d15701b5355fc1d9ed55542cab316fee73425b22 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `14`
- Chain head: `cbe3bae5f32f7dc049a15018e108ff469faa18007f8fbad13e38452bbf0e0580`
