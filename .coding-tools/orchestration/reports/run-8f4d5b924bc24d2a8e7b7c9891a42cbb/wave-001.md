# Orchestration Wave 1

- Run: `8f4d5b924bc24d2a8e7b7c9891a42cbb`
- Wave: `61f3af63f7b8445cb62edf450622e8aa`
- Objective: Synchronize the P4 multilayer benchmark and protocol with the now-proven canonical validator v5 behavior. The research stress run on the accepted core worktree showed G03, M01, and T02 PASS, blind_spots=[], 33/35 pass, with only G04 and S01 remaining as fixture defects. Update known_diagnostics_v1 to zero canonical blind spots and the two fixture failures only; update the three L08 hidden oracles and public challenge descriptions from known-diagnostic expectations to regression PASS expectations; update multilayer unit assertions and p4 evaluation protocol to document exact deduplication, leave-one-source-state-out, and rolling temporal validation. Also add an explicit source_state_identity_policy field to canonical predictive-validation output and a focused assertion so this synchronization wave records durable final receipts for the core source/test files after the prior permission-exception wave. Do not change stress fixtures, thresholds, labels, or promotion semantics. Preserve p5_automatic_start=false, automatic_policy_activation=false, synthetic nonpromotion, association-only/causal_claim_allowed=false, and unrelated WIP. Final oracle is normal multilayer PASS and strict multilayer PASS with canonical non-interference. No commit/push/restart/deploy.
- Mode: `mcp_only`
- Base HEAD: `4aa8a99b877f20b5f2f4bb2ce50e0cbc477a25d2`
- Worktree fingerprint: `d7338cf444c1b37d27dd3178ff671d2f71378bce9e22f037618a53129ed937fb`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 22354 | 2026-08-20T03:42:53.651Z | run_started |  | PREFLIGHT |  |
| 22355 | 2026-08-20T03:42:54.727Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 22356 | 2026-08-20T03:43:52.516Z | solution_shadow_recommended |  |  |  |
| 22357 | 2026-08-20T03:44:19.697Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 22358 | 2026-08-20T03:44:19.839Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 22359 | 2026-08-20T03:44:19.975Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 22360 | 2026-08-20T03:44:20.121Z | state_transition | READY | ROUTED | reason=route_selected |
| 22361 | 2026-08-20T03:44:20.575Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=a05b392af5754b25a6ed9c2994d3a50b |
| 22362 | 2026-08-20T03:44:20.753Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 22363 | 2026-08-20T03:44:21.285Z | patch_surface_observed |  |  |  |
| 22364 | 2026-08-20T03:44:21.542Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=a05b392af5754b25a6ed9c2994d3a50b |
| 22365 | 2026-08-20T03:44:21.660Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 22366 | 2026-08-20T03:44:22.029Z | proof_cache_miss |  |  | reason=cold; stage_id=check:32388c83904a2a33; input_fingerprint=b381d622b3b46c98b5602df2803067f897626b98dbd2a042a7e75a3dfa94685f |
| 22367 | 2026-08-20T03:44:22.392Z | managed_process_admitted |  |  | owner=default |
| 22368 | 2026-08-20T03:44:22.676Z | managed_process_started |  |  | owner=default |
| 22369 | 2026-08-20T03:44:23.305Z | managed_process_terminal |  |  | owner=default |
| 22370 | 2026-08-20T03:44:23.591Z | proof_recorded |  |  | stage_id=check:32388c83904a2a33; status=passed; cache_hit=False; input_fingerprint=b381d622b3b46c98b5602df2803067f897626b98dbd2a042a7e75a3dfa94685f |
| 22371 | 2026-08-20T03:44:23.773Z | proof_cache_miss |  |  | reason=cold; stage_id=check:c7e1b9653bbfd62e; input_fingerprint=b6d7b1fbe4836a304f6ef02fc9f9c7b936b651e707d5e64546ee18b499e5d794 |
| 22372 | 2026-08-20T03:44:24.143Z | managed_process_admitted |  |  | owner=default |
| 22373 | 2026-08-20T03:44:24.351Z | managed_process_started |  |  | owner=default |
| 22374 | 2026-08-20T03:44:24.826Z | managed_process_terminal |  |  | owner=default |
| 22375 | 2026-08-20T03:44:25.225Z | proof_recorded |  |  | stage_id=check:c7e1b9653bbfd62e; status=passed; cache_hit=False; input_fingerprint=b6d7b1fbe4836a304f6ef02fc9f9c7b936b651e707d5e64546ee18b499e5d794 |
| 22376 | 2026-08-20T03:44:25.394Z | proof_cache_miss |  |  | reason=cold; stage_id=check:cbcb0425f1b97db6; input_fingerprint=996df712a5fe9bb8ac92f03c3395c9051ce277c5839f59d9c61f7bab7e67f2ef |
| 22377 | 2026-08-20T03:44:25.764Z | managed_process_admitted |  |  | owner=default |
| 22378 | 2026-08-20T03:44:26.106Z | managed_process_started |  |  | owner=default |
| 22379 | 2026-08-20T03:44:37.755Z | managed_process_terminal |  |  | owner=default |
| 22380 | 2026-08-20T03:44:38.108Z | proof_recorded |  |  | stage_id=check:cbcb0425f1b97db6; status=passed; cache_hit=False; input_fingerprint=996df712a5fe9bb8ac92f03c3395c9051ce277c5839f59d9c61f7bab7e67f2ef |
| 22381 | 2026-08-20T03:44:38.291Z | proof_cache_miss |  |  | reason=cold; stage_id=check:4b1598eb83d27135; input_fingerprint=d6c19e09a1604693126e1a67c7084ae7367918642bc3532adb6b8e88a8d7c7e0 |
| 22382 | 2026-08-20T03:44:38.646Z | managed_process_admitted |  |  | owner=default |
| 22383 | 2026-08-20T03:44:38.951Z | managed_process_started |  |  | owner=default |
| 22384 | 2026-08-20T03:45:04.732Z | managed_process_terminal |  |  | owner=default |
| 22385 | 2026-08-20T03:45:05.029Z | proof_recorded |  |  | stage_id=check:4b1598eb83d27135; status=passed; cache_hit=False; input_fingerprint=d6c19e09a1604693126e1a67c7084ae7367918642bc3532adb6b8e88a8d7c7e0 |
| 22386 | 2026-08-20T03:45:05.188Z | proof_cache_miss |  |  | reason=cold; stage_id=check:9647a5d1f13b481d; input_fingerprint=82ea850d2c0be779766c9ad7aeffa91af26f400236cadc0da78b421b86bd60b2 |
| 22387 | 2026-08-20T03:45:05.754Z | managed_process_admitted |  |  | owner=default |
| 22388 | 2026-08-20T03:45:06.060Z | managed_process_started |  |  | owner=default |
| 22389 | 2026-08-20T03:45:33.725Z | managed_process_terminal |  |  | owner=default |
| 22390 | 2026-08-20T03:45:34.181Z | proof_recorded |  |  | stage_id=check:9647a5d1f13b481d; status=passed; cache_hit=False; input_fingerprint=82ea850d2c0be779766c9ad7aeffa91af26f400236cadc0da78b421b86bd60b2 |
| 22391 | 2026-08-20T03:45:34.318Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=6267abc204d7549fc1614142a0de19c1efaa9e416a25fcaae6bbd712ea4f83d8 |
| 22392 | 2026-08-20T03:45:34.809Z | managed_process_admitted |  |  | owner=default |
| 22393 | 2026-08-20T03:45:35.058Z | managed_process_started |  |  | owner=default |
| 22394 | 2026-08-20T03:45:35.440Z | managed_process_terminal |  |  | owner=default |
| 22395 | 2026-08-20T03:45:35.821Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=6267abc204d7549fc1614142a0de19c1efaa9e416a25fcaae6bbd712ea4f83d8 |
| 22396 | 2026-08-20T03:45:36.262Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 22397 | 2026-08-20T03:46:05.710Z | quality_outcome_recorded |  |  |  |
| 22398 | 2026-08-20T03:46:05.856Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 22399 | 2026-08-20T03:46:06.199Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:32388c83904a2a33 | passed | b381d622b3b46c98b5602df2803067f897626b98dbd2a042a7e75a3dfa94685f | False | 1211 | 0 |
| check:c7e1b9653bbfd62e | passed | b6d7b1fbe4836a304f6ef02fc9f9c7b936b651e707d5e64546ee18b499e5d794 | False | 1108 | 0 |
| check:cbcb0425f1b97db6 | passed | 996df712a5fe9bb8ac92f03c3395c9051ce277c5839f59d9c61f7bab7e67f2ef | False | 12343 | 0 |
| check:4b1598eb83d27135 | passed | d6c19e09a1604693126e1a67c7084ae7367918642bc3532adb6b8e88a8d7c7e0 | False | 26403 | 0 |
| check:9647a5d1f13b481d | passed | 82ea850d2c0be779766c9ad7aeffa91af26f400236cadc0da78b421b86bd60b2 | False | 28626 | 0 |
| verify:tests | passed | 6267abc204d7549fc1614142a0de19c1efaa9e416a25fcaae6bbd712ea4f83d8 | False | 1157 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 07604273c2f1465da2bbd1cb31f416dd | accepted | 4aa8a99b877f20b5f2f4bb2ce50e0cbc477a25d2 | 1abb6b17b51d0a9368d669c5299c4fd77e02a9095860ec925f6d0f38567be3fd | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `46`
- Chain head: `3e5cf01662af1e337b8385cda628b8b1fa4dd8411dd25e69b5a2b2d9ec7a3b20`
