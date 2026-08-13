# Orchestration Wave 1

- Run: `7be656325e1d424b816a0bf5fa6098bc`
- Wave: `2e0b3299f1514ed392df5375e9cee888`
- Objective: Fix EOCL recovered-context cache coherence so a replacement wave that reaches ACCEPTING can be accepted in the same runtime process, and add a regression assertion for the exact REPLAN-to-new-wave-to-CHECKPOINTED path.
- Mode: `mcp_only`
- Base HEAD: `571d30fc7237379fdc124d1b988054813d98bb45`
- Worktree fingerprint: `87b200a15eb63ab624e41b3ef198e89b187c99590b793c41b6757e8fe873af51`
- Contract fingerprint: ``
- Status: **active**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 1 | 2026-08-13T05:12:44.280Z | run_started |  | PREFLIGHT |  |
| 2 | 2026-08-13T05:12:44.889Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 3 | 2026-08-13T05:12:45.119Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 4 | 2026-08-13T05:12:45.352Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 5 | 2026-08-13T05:12:45.572Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 6 | 2026-08-13T05:12:45.784Z | state_transition | READY | ROUTED | reason=route_selected |
| 7 | 2026-08-13T05:12:46.211Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=ec66040ebc5c4f8099ebd20d2224ec49 |
| 8 | 2026-08-13T05:12:46.395Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 9 | 2026-08-13T05:12:47.055Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=ec66040ebc5c4f8099ebd20d2224ec49 |
| 10 | 2026-08-13T05:12:47.263Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 11 | 2026-08-13T05:12:51.169Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=bac3b063a910b3e5e4fc58cc4b67469c0463e19bb8fbf0c52f6794e862150ec6 |
| 12 | 2026-08-13T05:12:51.525Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | bac3b063a910b3e5e4fc58cc4b67469c0463e19bb8fbf0c52f6794e862150ec6 | False | 3218 |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `12`
- Chain head: `65bb3b0ec62f35ac1366d2f1d257019014de97ae4767d7158bc36917c2f9a9f5`
