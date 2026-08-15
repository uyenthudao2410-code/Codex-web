# Orchestration Wave 1

- Run: `4d0e518814db4cb0b8f656faf0e7caa7`
- Wave: `2f40d46983e545bf9b7210d53a4c12aa`
- Objective: P1.A1: add content-free observation span storage and a fail-closed critical-path DAG projection to OrchestrationLedger. Durations are measured only inside each declared monotonic clock domain; cross-clock ordering is allowed only through explicit dependency IDs. Missing dependencies or cycles must make the analysis incomplete. Add focused ledger tests. Preserve all P0 evaluation behavior and routing policy. No restart/commit/push/models/synthetic workload.
- Mode: `mcp_only`
- Base HEAD: `7236cd6a72c27e6eb7679585c115220cc54ae842`
- Worktree fingerprint: `5993fbd75d3810d46e0f228a924a89a6d7e3a2059518f4f8362fa84fff8ba2cf`
- Contract fingerprint: ``
- Status: **active**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 4841 | 2026-08-15T08:03:59.436Z | run_started |  | PREFLIGHT |  |
| 4842 | 2026-08-15T08:04:00.032Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 4843 | 2026-08-15T08:04:00.273Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 4844 | 2026-08-15T08:04:00.484Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 4845 | 2026-08-15T08:04:00.734Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 4846 | 2026-08-15T08:04:00.975Z | state_transition | READY | ROUTED | reason=route_selected |
| 4847 | 2026-08-15T08:04:01.613Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=f9d56511065d438491fa100285f9ee4d |
| 4848 | 2026-08-15T08:04:01.825Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 4849 | 2026-08-15T08:04:02.638Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=f9d56511065d438491fa100285f9ee4d |
| 4850 | 2026-08-15T08:04:02.867Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 4851 | 2026-08-15T08:04:03.396Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=59551b86cdd9ab6767a1a8a6580d9bf942a6e5d5037a3c80f8782e1f64aabbb6 |
| 4852 | 2026-08-15T08:04:15.685Z | proof_recorded |  |  | stage_id=verify:tests; status=failed; cache_hit=False; input_fingerprint=59551b86cdd9ab6767a1a8a6580d9bf942a6e5d5037a3c80f8782e1f64aabbb6 |
| 4853 | 2026-08-15T08:04:15.894Z | failure_observed | PROVING | PROVING | failure_class=BUILD_VERIFICATION_FAILED |
| 4854 | 2026-08-15T08:04:16.149Z | state_transition | PROVING | REPLAN | reason=BUILD_VERIFICATION_FAILED; failure_class=BUILD_VERIFICATION_FAILED |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | failed | 59551b86cdd9ab6767a1a8a6580d9bf942a6e5d5037a3c80f8782e1f64aabbb6 | False | 11859 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `14`
- Chain head: `638f099752b04eca522e293f32736d9c22f53d469e92faba0541e53f0dadfc60`
