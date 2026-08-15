# Orchestration Wave 1

- Run: `1cd63b2af44e47298487ad64d863e3ed`
- Wave: `12ed4cdeeb88401bade1a72ec4c0ea1d`
- Objective: Fix only the live-supervisor E2E teardown race by making the test harness restart stub wait for the spawned MCP ChildProcess close event instead of exit. This ensures piped stdio is closed before supervise returns and before workspace cleanup. Test-only change; do not modify production supervisor code.
- Mode: `mcp_only`
- Base HEAD: `dff81e251836666fc825c40bf86e4167afd29c39`
- Worktree fingerprint: `07f5a0fe8c0d9026550cc71e1ab6811d89c95db85987384131ee3729014695ce`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 4628 | 2026-08-15T06:46:33.677Z | run_started |  | PREFLIGHT |  |
| 4629 | 2026-08-15T06:46:34.149Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 4630 | 2026-08-15T06:46:34.298Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 4631 | 2026-08-15T06:46:34.478Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 4632 | 2026-08-15T06:46:34.646Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 4633 | 2026-08-15T06:46:34.844Z | state_transition | READY | ROUTED | reason=route_selected |
| 4634 | 2026-08-15T06:46:35.354Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=22f6b5ca77e348138c0a0d4a9a93ff19 |
| 4635 | 2026-08-15T06:46:35.542Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 4636 | 2026-08-15T06:46:36.078Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=22f6b5ca77e348138c0a0d4a9a93ff19 |
| 4637 | 2026-08-15T06:46:36.262Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 4638 | 2026-08-15T06:46:36.687Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=49a786ba0d4b619506aa599844d6577f5bb7fbda400f557eb57d4f1836b4b48a |
| 4639 | 2026-08-15T06:46:44.340Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=49a786ba0d4b619506aa599844d6577f5bb7fbda400f557eb57d4f1836b4b48a |
| 4640 | 2026-08-15T06:46:44.943Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 4641 | 2026-08-15T06:46:56.960Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 49a786ba0d4b619506aa599844d6577f5bb7fbda400f557eb57d4f1836b4b48a | False | 7265 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 5e897fe618d94199846bdf1478286d2f | accepted | dff81e251836666fc825c40bf86e4167afd29c39 | 4ad9f035cf245e82e7cbafea04429e6058a60179d27d9b120f9eb5ce897ced63 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `14`
- Chain head: `a398cdd266f0263f10652134574e099046a079a51022fca062edbb28b9a8172f`
