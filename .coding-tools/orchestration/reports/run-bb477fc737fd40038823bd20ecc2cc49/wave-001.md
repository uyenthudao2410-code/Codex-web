# Orchestration Wave 1

- Run: `bb477fc737fd40038823bd20ecc2cc49`
- Wave: `f9e2ed6273a0481eb8ee0e4f09a9f9ee`
- Objective: P3 activation preflight only: rebuild exact-HEAD webcodex-server and webcodex-runner, verify both binary versions carry current Git HEAD bc17700e, then run scripts/e2e_server_first_snapshot_ws.ps1 as a real-process loopback SourceSnapshot server-first dispatch/fallback mechanism canary. Do not modify product source, do not create representative evaluation tags, and do not interpret this canary as P3 efficacy evidence.
- Mode: `mcp_only`
- Base HEAD: `bc17700e475ce74c96a9547117aade58823f0811`
- Worktree fingerprint: `e8c159440c324c40eb2c8f2f3d85416a377d64be6d5c466ea3d0bd1089609264`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 15831 | 2026-08-17T20:33:50.679Z | run_started |  | PREFLIGHT |  |
| 15832 | 2026-08-17T20:33:51.057Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 15833 | 2026-08-17T20:33:51.150Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 15834 | 2026-08-17T20:33:51.255Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 15835 | 2026-08-17T20:33:51.372Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 15836 | 2026-08-17T20:33:51.472Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 15837 | 2026-08-17T20:33:51.568Z | state_transition | READY | ROUTED | reason=route_selected |
| 15838 | 2026-08-17T20:33:51.948Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=4ac73d8ca81e4162b45b5787117b0fb0 |
| 15839 | 2026-08-17T20:33:52.059Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 15840 | 2026-08-17T20:33:52.417Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=4ac73d8ca81e4162b45b5787117b0fb0 |
| 15841 | 2026-08-17T20:33:52.534Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 15842 | 2026-08-17T20:33:52.850Z | proof_cache_miss |  |  | reason=cold; stage_id=check:74b2b265600e7b49; input_fingerprint=3db631839b30f539038a315c274419ac350cc1598871338970281caffc45fdd4 |
| 15843 | 2026-08-17T20:33:53.105Z | managed_process_admitted |  |  | owner=default |
| 15844 | 2026-08-17T20:33:53.305Z | managed_process_started |  |  | owner=default |
| 15845 | 2026-08-17T20:33:54.680Z | managed_process_terminal |  |  | owner=default |
| 15846 | 2026-08-17T20:33:54.916Z | proof_recorded |  |  | stage_id=check:74b2b265600e7b49; status=failed; cache_hit=False; input_fingerprint=3db631839b30f539038a315c274419ac350cc1598871338970281caffc45fdd4 |
| 15847 | 2026-08-17T20:33:55.032Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 15848 | 2026-08-17T20:33:55.174Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 15849 | 2026-08-17T20:33:55.316Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:74b2b265600e7b49 | failed | 3db631839b30f539038a315c274419ac350cc1598871338970281caffc45fdd4 | False | 1833 | 101 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `61`
- Chain head: `6f11d1d0e8be75c080bd2bba6a64cfe15d85ee89238cf796040bd1c0bf8dcff5`
