# Orchestration Wave 1

- Run: `60bbd05f5172477694d5785ac9304c8e`
- Wave: `4479479d6d5c42ca80d31c807cd0dac8`
- Objective: Natural #19: add fail-closed paired durable replan-reason attribution for PERMISSION_REQUIRED and PROTECTED_PATH_WRITE rework. Classify request_contract_correction only when the existing failure_observed to wave_replanned index pairing proves an avoidable filesystem-escape/parent-traversal, unsupported inline-script replacement, denied network-proof replacement, or protected-path strategy correction. Keep both failure classes unmapped by class alone and preserve all security/runtime behavior.
- Objective revision: `1`
- Objective SHA-256: `36cdf0b3cdb5182760baf279499d1c8bc6f1bd0fbcf6a26cfebcb6b9335533e9`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `7bc1caee37107a15e74eb078b52fe314e5fa33ab`
- Worktree fingerprint: `1e78fe9b5a4abac5845c3450fee92ce4c4af2bbdd99b513742399b8c4bcef1fa`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 47129 | 2026-09-10T07:39:31.250Z | run_started |  | PREFLIGHT |  |
| 47130 | 2026-09-10T07:39:31.811Z | observation_span_recorded |  |  |  |
| 47131 | 2026-09-10T07:39:32.069Z | solution_shadow_recommended |  |  |  |
| 47132 | 2026-09-10T07:39:38.325Z | observation_span_recorded |  |  |  |
| 47133 | 2026-09-10T07:39:38.524Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 47134 | 2026-09-10T07:43:07.398Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 47135 | 2026-09-10T07:43:07.596Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 47136 | 2026-09-10T07:43:07.807Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 47137 | 2026-09-10T07:43:08.034Z | state_transition | READY | ROUTED | reason=route_selected |
| 47138 | 2026-09-10T07:43:08.268Z | observation_span_recorded |  |  |  |
| 47139 | 2026-09-10T07:43:09.260Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=ef0584c27b854799ba55652b9eaa93e7 |
| 47140 | 2026-09-10T07:43:09.500Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 47141 | 2026-09-10T07:43:10.312Z | patch_surface_observed |  |  |  |
| 47142 | 2026-09-10T07:43:10.498Z | observation_span_recorded |  |  |  |
| 47143 | 2026-09-10T07:43:10.793Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=ef0584c27b854799ba55652b9eaa93e7 |
| 47144 | 2026-09-10T07:43:10.987Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 47145 | 2026-09-10T07:43:11.746Z | proof_cache_miss |  |  | reason=cold; stage_id=check:14ac4d29e08d3b92; input_fingerprint=b2c6404ad9ec13fbca8253fe12b47ce9c8b4485cd48e38c24b7f7515db1574da |
| 47146 | 2026-09-10T07:43:12.117Z | managed_process_admitted |  |  | owner=default |
| 47147 | 2026-09-10T07:43:12.750Z | managed_process_started |  |  | owner=default |
| 47148 | 2026-09-10T07:43:13.254Z | managed_process_terminal |  |  | owner=default |
| 47149 | 2026-09-10T07:43:13.584Z | proof_recorded |  |  | stage_id=check:14ac4d29e08d3b92; status=failed; cache_hit=False; input_fingerprint=b2c6404ad9ec13fbca8253fe12b47ce9c8b4485cd48e38c24b7f7515db1574da |
| 47150 | 2026-09-10T07:43:13.854Z | observation_span_recorded |  |  |  |
| 47151 | 2026-09-10T07:43:14.029Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 47152 | 2026-09-10T07:43:14.204Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 47153 | 2026-09-10T07:43:14.437Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:14ac4d29e08d3b92 | failed | b2c6404ad9ec13fbca8253fe12b47ce9c8b4485cd48e38c24b7f7515db1574da | False | 1515 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `102`
- Chain head: `93def450d2823f307469143cba916b5008e3b0bba0eacd6b421f7c4e2adb5630`
