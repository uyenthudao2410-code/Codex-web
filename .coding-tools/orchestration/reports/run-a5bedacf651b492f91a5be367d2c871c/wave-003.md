# Orchestration Wave 3

- Run: `a5bedacf651b492f91a5be367d2c871c`
- Wave: `e268bd793efd4990921474d532b00c40`
- Objective: Natural #9: fix the Manager Task page truthfulness/data bridge. Preserve bounded structured task evidence only when it belongs to the exact canonical displayed task/run; reject stale/hybrid detail on identity mismatch. Keep task history sourced from orchestration_ledger and preserve stateless/cross-context authority boundaries. Do not restart, commit, push, package, release, deploy, mutate P5, or reconcile stale runs.
- Objective revision: `2`
- Objective SHA-256: `9a2832dafaca5a74351e188929607437b0092bfea410a087096c8f5052a3b73a`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `7bc1caee37107a15e74eb078b52fe314e5fa33ab`
- Worktree fingerprint: `9f658382e0403e9d1243bb94d6bd9a91ed18a4fecee451507c1b9ff1cf4184f6`
- Contract fingerprint: `c04fdc5e1ad20804ad3afad9465e6a9d6a91ac5339822bec7e2e933d6a352b1a`
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 45872 | 2026-09-09T13:20:58.286Z | wave_replanned |  | PREFLIGHT | reason=Wave 2 exact-byte adoption succeeded and both new Task projection bridge regressions passed. The only Node failure was the pre-existing static assertion that searched for taskList.current inside the task-state:read handler slice; the refactor intentionally moved that canonical selection into canonicalTaskStateFromControl. Wave 3 updates that static regression to assert delegation from the handler plus canonical-source/current/exact-binding invariants inside the helper, then runs the full dev-ui lifecycle test, the focused Python HTTP integration test from its module root, and diff check. |
| 45873 | 2026-09-09T13:20:58.508Z | observation_span_recorded |  |  |  |
| 45874 | 2026-09-09T13:21:04.732Z | observation_span_recorded |  |  |  |
| 45875 | 2026-09-09T13:21:04.948Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 45876 | 2026-09-09T13:21:48.670Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 45877 | 2026-09-09T13:21:48.845Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 45878 | 2026-09-09T13:21:48.979Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 45879 | 2026-09-09T13:21:49.136Z | state_transition | READY | ROUTED | reason=route_selected |
| 45880 | 2026-09-09T13:21:49.324Z | observation_span_recorded |  |  |  |
| 45881 | 2026-09-09T13:21:50.344Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=0cff61a671d84dedab45efacad70e7b9 |
| 45882 | 2026-09-09T13:21:50.489Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 45883 | 2026-09-09T13:21:51.303Z | existing_file_adoption_observed |  |  |  |
| 45884 | 2026-09-09T13:21:51.496Z | patch_surface_observed |  |  |  |
| 45885 | 2026-09-09T13:21:51.660Z | observation_span_recorded |  |  |  |
| 45886 | 2026-09-09T13:21:51.909Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=0cff61a671d84dedab45efacad70e7b9 |
| 45887 | 2026-09-09T13:21:52.069Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 45888 | 2026-09-09T13:21:52.989Z | proof_cache_miss |  |  | reason=cold; stage_id=check:ec8d8b2c91d870cf; input_fingerprint=3479a64cb13924a131caeacef5ab5ac623750ea3f6657e55b8bfffe656bf220b |
| 45889 | 2026-09-09T13:21:53.362Z | managed_process_admitted |  |  | owner=default |
| 45890 | 2026-09-09T13:21:53.639Z | managed_process_started |  |  | owner=default |
| 45891 | 2026-09-09T13:21:56.226Z | managed_process_terminal |  |  | owner=default |
| 45892 | 2026-09-09T13:21:56.518Z | proof_recorded |  |  | stage_id=check:ec8d8b2c91d870cf; status=passed; cache_hit=False; input_fingerprint=3479a64cb13924a131caeacef5ab5ac623750ea3f6657e55b8bfffe656bf220b |
| 45893 | 2026-09-09T13:21:56.812Z | proof_cache_miss |  |  | reason=cold; stage_id=check:687903aa1f6c9d13; input_fingerprint=8aae71aea022d7248056fadff6bc86aaed6937dbe7b2e77b8fe828cf05c022e0 |
| 45894 | 2026-09-09T13:21:57.161Z | managed_process_admitted |  |  | owner=default |
| 45895 | 2026-09-09T13:21:57.427Z | managed_process_started |  |  | owner=default |
| 45896 | 2026-09-09T13:21:57.929Z | managed_process_terminal |  |  | owner=default |
| 45897 | 2026-09-09T13:21:58.210Z | proof_recorded |  |  | stage_id=check:687903aa1f6c9d13; status=passed; cache_hit=False; input_fingerprint=8aae71aea022d7248056fadff6bc86aaed6937dbe7b2e77b8fe828cf05c022e0 |
| 45898 | 2026-09-09T13:21:58.351Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=fa4d196d85e0c25de9b2f50ed99780a3d7d31a2e8d00787a6d8b9a59b43da3fc |
| 45899 | 2026-09-09T13:21:58.619Z | managed_process_admitted |  |  | owner=default |
| 45900 | 2026-09-09T13:21:58.819Z | managed_process_started |  |  | owner=default |
| 45901 | 2026-09-09T13:22:01.848Z | managed_process_terminal |  |  | owner=default |
| 45902 | 2026-09-09T13:22:02.195Z | proof_recorded |  |  | stage_id=verify:tests; status=failed; cache_hit=False; input_fingerprint=fa4d196d85e0c25de9b2f50ed99780a3d7d31a2e8d00787a6d8b9a59b43da3fc |
| 45903 | 2026-09-09T13:22:02.392Z | observation_span_recorded |  |  |  |
| 45904 | 2026-09-09T13:22:02.549Z | failure_observed | PROVING | PROVING | failure_class=BUILD_VERIFICATION_FAILED |
| 45905 | 2026-09-09T13:22:02.707Z | state_transition | PROVING | REPLAN | reason=BUILD_VERIFICATION_FAILED; failure_class=BUILD_VERIFICATION_FAILED |
| 45906 | 2026-09-09T13:22:02.903Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:ec8d8b2c91d870cf | passed | 3479a64cb13924a131caeacef5ab5ac623750ea3f6657e55b8bfffe656bf220b | False | 3244 | 0 |
| check:687903aa1f6c9d13 | passed | 8aae71aea022d7248056fadff6bc86aaed6937dbe7b2e77b8fe828cf05c022e0 | False | 1069 | 0 |
| verify:tests | failed | fa4d196d85e0c25de9b2f50ed99780a3d7d31a2e8d00787a6d8b9a59b43da3fc | False | 3546 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `273`
- Chain head: `d882db9fd950ba73a7fd1fa1788fb65639608ff3522f81d5154eba3c07ab5251`
