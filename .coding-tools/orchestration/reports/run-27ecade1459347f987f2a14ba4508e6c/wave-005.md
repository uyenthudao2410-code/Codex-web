# Orchestration Wave 5

- Run: `27ecade1459347f987f2a14ba4508e6c`
- Wave: `43a7f9bc3e0d4df4bd4523611a6c3e55`
- Objective: Prepare the smallest deterministic fixes for the two exact full-suite failures on HEAD 0415538: (1) update the runtime tool-contract SHA expectation in tests/test_efficiency_runtime.py to the current source contract produced by the intentional task_control accept schema extension, without weakening the contract assertion; (2) eliminate the Windows timing flake in tests/test_orchestration_control.py test_write_lease_expiry_and_renewal_are_enforced while preserving production expiry/renewal semantics, preferably by widening only the test timing margin rather than changing orchestration_control.py unless source inspection proves a production defect. Do not modify mcp_http_handler.py. Return exact context for a minimal patch.
- Objective revision: `5`
- Objective SHA-256: `4791fb5a6b545c6295f4a3744c597ffe83390d74cab5f3bd5f1e0777219740e4`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `0415538a0c8212d0d7e4b7217faad5b289020cff`
- Worktree fingerprint: `2d56d6a973dd529306d1b368d6e150327ccce7889c345bfc23bb61ab108fee33`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 26574 | 2026-08-22T03:56:17.294Z | wave_replanned |  | PREFLIGHT | reason=The full suite on checkpoint HEAD reproduced exact failures: a stale expected tool-contract SHA after the intentional task_control schema extension, and a 0.15-second lease-renewal timing flake under full-suite Windows load. Strategy changes from broad reproduction to two targeted deterministic oracle repairs. |
| 26575 | 2026-08-22T03:56:17.757Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 26576 | 2026-08-22T03:57:32.071Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 26577 | 2026-08-22T03:57:32.257Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 26578 | 2026-08-22T03:57:32.407Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 26579 | 2026-08-22T03:57:32.543Z | state_transition | READY | ROUTED | reason=route_selected |
| 26580 | 2026-08-22T03:57:33.050Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=a0dd43a8d124468e85eef8ee2e014b7d |
| 26581 | 2026-08-22T03:57:33.208Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 26582 | 2026-08-22T03:57:33.643Z | patch_surface_observed |  |  |  |
| 26583 | 2026-08-22T03:57:33.859Z | patch_surface_observed |  |  |  |
| 26584 | 2026-08-22T03:57:34.107Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=a0dd43a8d124468e85eef8ee2e014b7d |
| 26585 | 2026-08-22T03:57:34.257Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 26586 | 2026-08-22T03:57:34.618Z | proof_cache_miss |  |  | reason=cold; stage_id=check:b270e2f0e12f038d; input_fingerprint=32282c4e8094606bec60060c3a23ef748ae864e903adc3cbb8f42fc47639b16d |
| 26587 | 2026-08-22T03:57:34.961Z | managed_process_admitted |  |  | owner=default |
| 26588 | 2026-08-22T03:57:35.233Z | managed_process_started |  |  | owner=default |
| 26589 | 2026-08-22T03:57:36.137Z | managed_process_terminal |  |  | owner=default |
| 26590 | 2026-08-22T03:57:36.466Z | proof_recorded |  |  | stage_id=check:b270e2f0e12f038d; status=passed; cache_hit=False; input_fingerprint=32282c4e8094606bec60060c3a23ef748ae864e903adc3cbb8f42fc47639b16d |
| 26591 | 2026-08-22T03:57:36.635Z | proof_cache_miss |  |  | reason=cold; stage_id=check:b728a12a95ce1578; input_fingerprint=56d326afdab327b938d1441c59a1cf9eed2d2a895d2d1c00762755de3bf8f04d |
| 26592 | 2026-08-22T03:57:37.099Z | managed_process_admitted |  |  | owner=default |
| 26593 | 2026-08-22T03:57:37.416Z | managed_process_started |  |  | owner=default |
| 26594 | 2026-08-22T03:57:40.037Z | managed_process_terminal |  |  | owner=default |
| 26595 | 2026-08-22T03:57:40.458Z | proof_recorded |  |  | stage_id=check:b728a12a95ce1578; status=passed; cache_hit=False; input_fingerprint=56d326afdab327b938d1441c59a1cf9eed2d2a895d2d1c00762755de3bf8f04d |
| 26596 | 2026-08-22T03:57:40.695Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:1188037643a6e8c4; input_fingerprint=cee61c76cb7f96c3d1d15dbbb057c0d31b9fedaa1fb3cea9d5e6baab4412f596 |
| 26597 | 2026-08-22T03:57:41.059Z | managed_process_admitted |  |  | owner=default |
| 26598 | 2026-08-22T03:57:41.228Z | managed_process_started |  |  | owner=default |
| 26599 | 2026-08-22T03:57:44.471Z | managed_process_terminal |  |  | owner=default |
| 26600 | 2026-08-22T03:57:44.798Z | proof_recorded |  |  | stage_id=check:1188037643a6e8c4; status=passed; cache_hit=False; input_fingerprint=cee61c76cb7f96c3d1d15dbbb057c0d31b9fedaa1fb3cea9d5e6baab4412f596 |
| 26601 | 2026-08-22T03:57:45.010Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=44f1b597a2cbf34e0a78bc65065b463fdbc6748a9bd1b166052289c1ff4a04b6 |
| 26602 | 2026-08-22T03:57:45.407Z | managed_process_admitted |  |  | owner=default |
| 26603 | 2026-08-22T03:57:45.635Z | managed_process_started |  |  | owner=default |
| 26604 | 2026-08-22T04:00:54.429Z | managed_process_terminal |  |  | owner=default |
| 26605 | 2026-08-22T04:00:54.747Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=44f1b597a2cbf34e0a78bc65065b463fdbc6748a9bd1b166052289c1ff4a04b6 |
| 26606 | 2026-08-22T04:00:55.257Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 26607 | 2026-08-22T04:01:11.488Z | quality_outcome_recorded |  |  |  |
| 26608 | 2026-08-22T04:01:11.645Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 26609 | 2026-08-22T04:01:11.978Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:b270e2f0e12f038d | passed | 32282c4e8094606bec60060c3a23ef748ae864e903adc3cbb8f42fc47639b16d | False | 1494 | 0 |
| check:b728a12a95ce1578 | passed | 56d326afdab327b938d1441c59a1cf9eed2d2a895d2d1c00762755de3bf8f04d | False | 3465 | 0 |
| check:1188037643a6e8c4 | passed | cee61c76cb7f96c3d1d15dbbb057c0d31b9fedaa1fb3cea9d5e6baab4412f596 | False | 3771 | 0 |
| verify:tests | passed | 44f1b597a2cbf34e0a78bc65065b463fdbc6748a9bd1b166052289c1ff4a04b6 | False | 189375 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| c008fde579d74593baf2f668ed8c9174 | accepted | 0415538a0c8212d0d7e4b7217faad5b289020cff | e4765bc066852cd574aa75455fc0e3d3c9185ad0dba60e3594768d7645b65d58 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `141`
- Chain head: `4db1ca0f91a496b1bad885a43f3d9b998de192d05d5bd8d521657d239be34121`
