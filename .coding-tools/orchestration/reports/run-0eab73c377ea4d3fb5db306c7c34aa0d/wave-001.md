# Orchestration Wave 1

- Run: `0eab73c377ea4d3fb5db306c7c34aa0d`
- Wave: `75b001ac00aa46b2a96c3f0a6ae09cb9`
- Objective: Authoritative P0.3 F5 primary Coding MCP death/recovery gap analysis, read-only. Inspect the current worktree implementation and tests for RuntimeOrchestrator/Recovery Host supervision when the owned primary Coding MCP process dies while the primary Tunnel remains healthy. Determine whether an existing real-process test already kills the real Coding MCP PID, triggers the production supervision/recovery path, proves a new healthy MCP PID with the same workspace/device identity, and proves the existing primary Tunnel PID/listener is preserved. If exact proof is missing, identify the smallest test-only insertion point and reusable fixture from the already-accepted F4/F6 tunnel process fixture. Do not modify production source, unrelated UI files, or live production processes.
- Mode: `mcp_only`
- Base HEAD: `885260b404c2c64df1b1afa835963045ac55dbf6`
- Worktree fingerprint: `cdec58405a1ec054b3e8c3147df5eb4bb1a95c84630c374437041b82381568f7`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 13704 | 2026-08-17T11:08:23.918Z | run_started |  | PREFLIGHT |  |
| 13705 | 2026-08-17T11:08:25.162Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 13706 | 2026-08-17T11:08:50.827Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 13707 | 2026-08-17T11:10:16.490Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 13708 | 2026-08-17T11:11:41.363Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 13709 | 2026-08-17T11:11:41.563Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 13710 | 2026-08-17T11:11:41.830Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 13711 | 2026-08-17T11:11:42.030Z | state_transition | READY | ROUTED | reason=route_selected |
| 13712 | 2026-08-17T11:11:42.872Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=828eb763ee4e47ce88ae5a16ce68bbee |
| 13713 | 2026-08-17T11:11:43.136Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 13714 | 2026-08-17T11:11:44.164Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=828eb763ee4e47ce88ae5a16ce68bbee |
| 13715 | 2026-08-17T11:11:44.563Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 13716 | 2026-08-17T11:11:45.268Z | proof_cache_miss |  |  | reason=cold; stage_id=check:ca0c352a560713c4; input_fingerprint=4713fe9dd1e1f0beaf44381d37a59e61d73274e089c7b036043519d63777c1b7 |
| 13717 | 2026-08-17T11:11:45.882Z | managed_process_admitted |  |  | owner=default |
| 13718 | 2026-08-17T11:11:46.318Z | managed_process_started |  |  | owner=default |
| 13719 | 2026-08-17T11:11:46.792Z | managed_process_terminal |  |  | owner=default |
| 13720 | 2026-08-17T11:11:47.367Z | proof_recorded |  |  | stage_id=check:ca0c352a560713c4; status=passed; cache_hit=False; input_fingerprint=4713fe9dd1e1f0beaf44381d37a59e61d73274e089c7b036043519d63777c1b7 |
| 13721 | 2026-08-17T11:11:47.536Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=7f3fb037987f66f3d98ef1cc9178e03ca8bcc3add1782bdc2d0304438aaaba85 |
| 13722 | 2026-08-17T11:11:47.901Z | managed_process_admitted |  |  | owner=default |
| 13723 | 2026-08-17T11:11:48.276Z | managed_process_started |  |  | owner=default |
| 13724 | 2026-08-17T11:11:57.102Z | managed_process_terminal |  |  | owner=default |
| 13725 | 2026-08-17T11:11:58.582Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=7f3fb037987f66f3d98ef1cc9178e03ca8bcc3add1782bdc2d0304438aaaba85 |
| 13726 | 2026-08-17T11:11:59.409Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 13727 | 2026-08-17T11:12:48.534Z | managed_process_admitted |  |  | owner=chatweb |
| 13728 | 2026-08-17T11:12:48.901Z | managed_process_started |  |  | owner=chatweb |
| 13729 | 2026-08-17T11:12:49.494Z | managed_process_terminal |  |  | owner=chatweb |
| 13730 | 2026-08-17T11:13:03.392Z | managed_process_admitted |  |  | owner=chatweb |
| 13731 | 2026-08-17T11:13:03.761Z | managed_process_started |  |  | owner=chatweb |
| 13732 | 2026-08-17T11:13:12.433Z | managed_process_terminal |  |  | owner=chatweb |
| 13733 | 2026-08-17T11:13:26.228Z | managed_process_admitted |  |  | owner=chatweb |
| 13734 | 2026-08-17T11:13:26.576Z | managed_process_started |  |  | owner=chatweb |
| 13735 | 2026-08-17T11:13:35.318Z | managed_process_terminal |  |  | owner=chatweb |
| 13736 | 2026-08-17T11:15:34.197Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 13737 | 2026-08-17T11:15:34.591Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:ca0c352a560713c4 | passed | 4713fe9dd1e1f0beaf44381d37a59e61d73274e089c7b036043519d63777c1b7 | False | 1510 | 0 |
| verify:tests | passed | 7f3fb037987f66f3d98ef1cc9178e03ca8bcc3add1782bdc2d0304438aaaba85 | False | 10610 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| e5f73a645909449ea757041714fa7447 | accepted | 885260b404c2c64df1b1afa835963045ac55dbf6 | 57c3373991cb0ed094f4f51ca487ec3d6bb3aec52bf1c1054a8fa979bc76bf7e | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `34`
- Chain head: `dfa685df9bd75e968468e8bedd11a9d7682be7aee4e2c879edc1b07db3c3bdc5`
