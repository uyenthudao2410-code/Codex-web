# Orchestration Wave 1

- Run: `161d565abf5a48b2b3ec36439b9b3797`
- Wave: `bc47914ad5f4457f980cc068242ee030`
- Objective: Expose durable checkpoint records in orchestration audit summaries so CHECKPOINTED runs include checkpoint provenance in generated audit/report data.
- Mode: `mcp_only`
- Base HEAD: `83581b4f262846a3c8b0daadb7417391702e5fb3`
- Worktree fingerprint: `7b40b7255a57bef071810855a4b43f20b14d2b3ced43edcafbe7672fa804370a`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 41 | 2026-08-13T05:35:13.558Z | run_started |  | PREFLIGHT |  |
| 42 | 2026-08-13T05:35:13.994Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 43 | 2026-08-13T05:35:14.257Z | execution_mode_resolved | PREFLIGHT | PREFLIGHT | requested=auto; resolved=mcp_only |
| 44 | 2026-08-13T05:35:14.424Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 45 | 2026-08-13T05:35:14.571Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 46 | 2026-08-13T05:35:14.729Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=auto; resolved=deterministic |
| 47 | 2026-08-13T05:35:14.888Z | state_transition | READY | ROUTED | reason=route_selected |
| 48 | 2026-08-13T05:35:15.267Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=c94503ef03f34d5d854ed43f5bf9a668 |
| 49 | 2026-08-13T05:35:15.441Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 50 | 2026-08-13T05:35:15.950Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=c94503ef03f34d5d854ed43f5bf9a668 |
| 51 | 2026-08-13T05:35:16.097Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 52 | 2026-08-13T05:35:17.101Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=5d84854a7bc1caea67af12aabd2ba56b1898b5824f6903fd996816c0da27b2a6 |
| 53 | 2026-08-13T05:35:17.398Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 55 | 2026-08-13T05:36:43.714Z | state_transition | ACCEPTING | CHECKPOINTED | reason=chatweb_sol_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 5d84854a7bc1caea67af12aabd2ba56b1898b5824f6903fd996816c0da27b2a6 | False | 500 |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `14`
- Chain head: `c826cad47978ed6d1ec9e3d85ce7291e76e4ecacb80412f40382f4a66df5d94c`
