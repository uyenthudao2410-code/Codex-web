# Orchestration Wave 1

- Run: `6f8d282aad0c46e7ab29b0831dad6765`
- Wave: `a3e5545745f64f9583d64f4795cff2ed`
- Objective: Continue P5 engineering with a dormant measurement/baseline layer only; do not start or enroll treatment. Build the smallest read-only P5 baseline snapshot and experiment-contract surface that combines canonical P5 readiness, the existing organic rework baseline, and the already-accepted dormant treatment implementation. It must preserve unknown-not-zero, report CAR as unavailable when complete total-cost coverage is absent, expose TTAR/rework baseline metrics without inventing promotion thresholds, and explicitly report treatment_started=false / samples_created=false. Add a read-only CLI, focused tests, npm script, and roadmap wording only if needed. Do not generate workload, fabricate treatment/control observations, mutate ledger, enable P5, relax readiness, commit, push, restart, or deploy.
- Mode: `mcp_only`
- Base HEAD: `4aa8a99b877f20b5f2f4bb2ce50e0cbc477a25d2`
- Worktree fingerprint: `cef6c8ae8703bead00b95e5d7c5ac2e853a01080d20f220c06a246d00fd27d64`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 22470 | 2026-08-20T03:55:51.890Z | run_started |  | PREFLIGHT |  |
| 22471 | 2026-08-20T03:55:52.787Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 22472 | 2026-08-20T03:56:56.946Z | solution_shadow_recommended |  |  |  |
| 22473 | 2026-08-20T03:57:47.959Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 22474 | 2026-08-20T03:57:48.087Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 22475 | 2026-08-20T03:57:48.216Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 22476 | 2026-08-20T03:57:48.355Z | state_transition | READY | ROUTED | reason=route_selected |
| 22477 | 2026-08-20T03:57:48.782Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=a53a363c8777461b9c918d6a24121c32 |
| 22478 | 2026-08-20T03:57:48.971Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 22479 | 2026-08-20T03:57:49.387Z | patch_surface_observed |  |  |  |
| 22480 | 2026-08-20T03:57:49.568Z | patch_surface_observed |  |  |  |
| 22481 | 2026-08-20T03:57:49.788Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=a53a363c8777461b9c918d6a24121c32 |
| 22482 | 2026-08-20T03:57:49.940Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 22483 | 2026-08-20T03:57:50.326Z | proof_cache_miss |  |  | reason=cold; stage_id=check:3532a5bec0afb591; input_fingerprint=66bcd2d7afedabba7958eb83d3ca0ca92c3effb5bfa97fcd733759557ecf787e |
| 22484 | 2026-08-20T03:57:50.906Z | managed_process_admitted |  |  | owner=default |
| 22485 | 2026-08-20T03:57:51.158Z | managed_process_started |  |  | owner=default |
| 22486 | 2026-08-20T03:57:51.662Z | managed_process_terminal |  |  | owner=default |
| 22487 | 2026-08-20T03:57:51.952Z | proof_recorded |  |  | stage_id=check:3532a5bec0afb591; status=passed; cache_hit=False; input_fingerprint=66bcd2d7afedabba7958eb83d3ca0ca92c3effb5bfa97fcd733759557ecf787e |
| 22488 | 2026-08-20T03:57:52.180Z | proof_cache_miss |  |  | reason=cold; stage_id=check:6d6fe59b8b128c7e; input_fingerprint=a5399d5af8ffe1d3e249f27fc2828c852ed954ce34be321a121a6db46925e963 |
| 22489 | 2026-08-20T03:57:52.451Z | managed_process_admitted |  |  | owner=default |
| 22490 | 2026-08-20T03:57:52.722Z | managed_process_started |  |  | owner=default |
| 22491 | 2026-08-20T03:57:53.164Z | managed_process_terminal |  |  | owner=default |
| 22492 | 2026-08-20T03:57:53.533Z | proof_recorded |  |  | stage_id=check:6d6fe59b8b128c7e; status=passed; cache_hit=False; input_fingerprint=a5399d5af8ffe1d3e249f27fc2828c852ed954ce34be321a121a6db46925e963 |
| 22493 | 2026-08-20T03:57:53.684Z | proof_cache_miss |  |  | reason=cold; stage_id=check:44f99eab9c3cb541; input_fingerprint=340da66dfb8ef7fa24783412f69b2af902616f26c6147029be72c005b0842911 |
| 22494 | 2026-08-20T03:57:54.006Z | managed_process_admitted |  |  | owner=default |
| 22495 | 2026-08-20T03:57:54.312Z | managed_process_started |  |  | owner=default |
| 22496 | 2026-08-20T03:58:08.157Z | managed_process_terminal |  |  | owner=default |
| 22497 | 2026-08-20T03:58:08.529Z | proof_recorded |  |  | stage_id=check:44f99eab9c3cb541; status=passed; cache_hit=False; input_fingerprint=340da66dfb8ef7fa24783412f69b2af902616f26c6147029be72c005b0842911 |
| 22498 | 2026-08-20T03:58:08.689Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:4b1598eb83d27135; input_fingerprint=ddab3f7fa85dcc98e9759187ba80f513b11009aa7ce9257db0ba1ce723be09f9 |
| 22499 | 2026-08-20T03:58:09.068Z | managed_process_admitted |  |  | owner=default |
| 22500 | 2026-08-20T03:58:09.363Z | managed_process_started |  |  | owner=default |
| 22501 | 2026-08-20T03:58:48.772Z | managed_process_terminal |  |  | owner=default |
| 22502 | 2026-08-20T03:58:49.152Z | proof_recorded |  |  | stage_id=check:4b1598eb83d27135; status=passed; cache_hit=False; input_fingerprint=ddab3f7fa85dcc98e9759187ba80f513b11009aa7ce9257db0ba1ce723be09f9 |
| 22503 | 2026-08-20T03:58:49.363Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:9647a5d1f13b481d; input_fingerprint=4d377db95d33741a836e039f42e0aaeb53a8ab6bb268fbf311c3d5220265d04e |
| 22504 | 2026-08-20T03:58:49.821Z | managed_process_admitted |  |  | owner=default |
| 22505 | 2026-08-20T03:58:50.138Z | managed_process_started |  |  | owner=default |
| 22506 | 2026-08-20T03:59:39.556Z | managed_process_terminal |  |  | owner=default |
| 22507 | 2026-08-20T03:59:40.017Z | proof_recorded |  |  | stage_id=check:9647a5d1f13b481d; status=passed; cache_hit=False; input_fingerprint=4d377db95d33741a836e039f42e0aaeb53a8ab6bb268fbf311c3d5220265d04e |
| 22508 | 2026-08-20T03:59:40.287Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=b9c73030351d6ae5ff1adef05c27d9cdcff5d726961cb46c607b312c091ad0a4 |
| 22509 | 2026-08-20T03:59:40.758Z | managed_process_admitted |  |  | owner=default |
| 22510 | 2026-08-20T03:59:41.136Z | managed_process_started |  |  | owner=default |
| 22511 | 2026-08-20T04:00:00.413Z | managed_process_terminal |  |  | owner=default |
| 22512 | 2026-08-20T04:00:00.872Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=b9c73030351d6ae5ff1adef05c27d9cdcff5d726961cb46c607b312c091ad0a4 |
| 22513 | 2026-08-20T04:00:01.523Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 22514 | 2026-08-20T04:00:18.138Z | quality_outcome_recorded |  |  |  |
| 22515 | 2026-08-20T04:00:18.299Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 22516 | 2026-08-20T04:00:18.843Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:3532a5bec0afb591 | passed | 66bcd2d7afedabba7958eb83d3ca0ca92c3effb5bfa97fcd733759557ecf787e | False | 1328 | 0 |
| check:6d6fe59b8b128c7e | passed | a5399d5af8ffe1d3e249f27fc2828c852ed954ce34be321a121a6db46925e963 | False | 1053 | 0 |
| check:44f99eab9c3cb541 | passed | 340da66dfb8ef7fa24783412f69b2af902616f26c6147029be72c005b0842911 | False | 14508 | 0 |
| check:4b1598eb83d27135 | passed | ddab3f7fa85dcc98e9759187ba80f513b11009aa7ce9257db0ba1ce723be09f9 | False | 40100 | 0 |
| check:9647a5d1f13b481d | passed | 4d377db95d33741a836e039f42e0aaeb53a8ab6bb268fbf311c3d5220265d04e | False | 50290 | 0 |
| verify:tests | passed | b9c73030351d6ae5ff1adef05c27d9cdcff5d726961cb46c607b312c091ad0a4 | False | 20077 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 54872595efb4402f9c252449ea9b3fac | accepted | 4aa8a99b877f20b5f2f4bb2ce50e0cbc477a25d2 | 295934b21d24a5387adbe31f61ef071cf3d1e42979aa02f3754abb25861f052f | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `47`
- Chain head: `1946801d4f665791d08f1bed9fb9b546fc8db9a920febe023c56966c50a78992`
