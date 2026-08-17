# Orchestration Wave 1

- Run: `2ae5487d82c24c1ba8317f7a5773bd39`
- Wave: `a6de1f5715684d8dbfc2d1b403a52fc7`
- Objective: Complete final pre-P3 intention-to-treat paired-analysis readiness without starting P3 treatment. Extend paired_policy_evaluation output so all explicit representative comparable pairs, regardless of terminal status, report symmetric baseline/candidate acceptance rates, first-pass acceptance rates, and repair rates. Keep TTAR conditional on both accepted. Add a regression where baseline is accepted and SERVER_FIRST_DETERMINISTIC_V1 candidate is aborted with a replan, proving the aborted candidate remains in pair_count and yields candidate_acceptance_rate=0, candidate_first_pass_rate=0, candidate_repair_rate=1 instead of being survivor-filtered. Preserve exact pair identity, unknown cost semantics, automatic_activation=false, and existing ledger/public MCP semantics.
- Mode: `mcp_only`
- Base HEAD: `bc07e240740726d9a5ddbd590e01568344a92440`
- Worktree fingerprint: `b6c94dbf87dce385f7b9c9ce10dfb00337ee3c2269ffe3f25882e47122c3f9c6`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 15715 | 2026-08-17T20:00:34.011Z | run_started |  | PREFLIGHT |  |
| 15716 | 2026-08-17T20:00:34.413Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 15717 | 2026-08-17T20:00:34.529Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 15718 | 2026-08-17T20:00:34.646Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 15719 | 2026-08-17T20:00:34.765Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 15720 | 2026-08-17T20:00:34.879Z | state_transition | READY | ROUTED | reason=route_selected |
| 15721 | 2026-08-17T20:00:35.294Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=d5f7ebeeb2424f09b51a34c45f408b03 |
| 15722 | 2026-08-17T20:00:35.421Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 15723 | 2026-08-17T20:00:35.910Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=d5f7ebeeb2424f09b51a34c45f408b03 |
| 15724 | 2026-08-17T20:00:36.012Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 15725 | 2026-08-17T20:00:36.328Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:d9a732e581c2f22f; input_fingerprint=943d7da7634eb3671d57825420372b3c9e1acf906f1ba15376933fcb5296f88f |
| 15726 | 2026-08-17T20:00:36.582Z | managed_process_admitted |  |  | owner=default |
| 15727 | 2026-08-17T20:00:36.836Z | managed_process_started |  |  | owner=default |
| 15728 | 2026-08-17T20:00:37.250Z | managed_process_terminal |  |  | owner=default |
| 15729 | 2026-08-17T20:00:37.479Z | proof_recorded |  |  | stage_id=check:d9a732e581c2f22f; status=passed; cache_hit=False; input_fingerprint=943d7da7634eb3671d57825420372b3c9e1acf906f1ba15376933fcb5296f88f |
| 15730 | 2026-08-17T20:00:37.630Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:80a1a46bd01d26a3; input_fingerprint=3bd4aaf3451a4e9359ac5eb1151e8622bbe35a41b634c08a52c276c0a7d8b660 |
| 15731 | 2026-08-17T20:00:37.862Z | managed_process_admitted |  |  | owner=default |
| 15732 | 2026-08-17T20:00:38.145Z | managed_process_started |  |  | owner=default |
| 15733 | 2026-08-17T20:00:38.513Z | managed_process_terminal |  |  | owner=default |
| 15734 | 2026-08-17T20:00:38.762Z | proof_recorded |  |  | stage_id=check:80a1a46bd01d26a3; status=passed; cache_hit=False; input_fingerprint=3bd4aaf3451a4e9359ac5eb1151e8622bbe35a41b634c08a52c276c0a7d8b660 |
| 15735 | 2026-08-17T20:00:38.905Z | proof_cache_miss |  |  | reason=cold; stage_id=check:6f5f72f78509db88; input_fingerprint=9ca3edf912c7bf2e988f94ca7b8c3e99f7655538b79fa8a5d642af521c69e07f |
| 15736 | 2026-08-17T20:00:39.162Z | managed_process_admitted |  |  | owner=default |
| 15737 | 2026-08-17T20:00:39.411Z | managed_process_started |  |  | owner=default |
| 15738 | 2026-08-17T20:00:39.772Z | managed_process_terminal |  |  | owner=default |
| 15739 | 2026-08-17T20:00:40.029Z | proof_recorded |  |  | stage_id=check:6f5f72f78509db88; status=passed; cache_hit=False; input_fingerprint=9ca3edf912c7bf2e988f94ca7b8c3e99f7655538b79fa8a5d642af521c69e07f |
| 15740 | 2026-08-17T20:00:40.158Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=71f11d667d6edd62904fefd26c3f7a529738de5d5b7be33c01325d3dbf4f4fee |
| 15741 | 2026-08-17T20:00:40.412Z | managed_process_admitted |  |  | owner=default |
| 15742 | 2026-08-17T20:00:40.697Z | managed_process_started |  |  | owner=default |
| 15743 | 2026-08-17T20:00:46.829Z | managed_process_terminal |  |  | owner=default |
| 15744 | 2026-08-17T20:00:47.065Z | proof_recorded |  |  | stage_id=verify:tests; status=failed; cache_hit=False; input_fingerprint=71f11d667d6edd62904fefd26c3f7a529738de5d5b7be33c01325d3dbf4f4fee |
| 15745 | 2026-08-17T20:00:47.178Z | failure_observed | PROVING | PROVING | failure_class=BUILD_VERIFICATION_FAILED |
| 15746 | 2026-08-17T20:00:47.305Z | state_transition | PROVING | REPLAN | reason=BUILD_VERIFICATION_FAILED; failure_class=BUILD_VERIFICATION_FAILED |
| 15747 | 2026-08-17T20:00:47.447Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:d9a732e581c2f22f | passed | 943d7da7634eb3671d57825420372b3c9e1acf906f1ba15376933fcb5296f88f | False | 915 | 0 |
| check:80a1a46bd01d26a3 | passed | 3bd4aaf3451a4e9359ac5eb1151e8622bbe35a41b634c08a52c276c0a7d8b660 | False | 913 | 0 |
| check:6f5f72f78509db88 | passed | 9ca3edf912c7bf2e988f94ca7b8c3e99f7655538b79fa8a5d642af521c69e07f | False | 900 | 0 |
| verify:tests | failed | 71f11d667d6edd62904fefd26c3f7a529738de5d5b7be33c01325d3dbf4f4fee | False | 6672 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `69`
- Chain head: `286be33bc51845409aa2651b2d40993524be52729f737d72d3c1a15045089563`
