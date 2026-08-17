# Orchestration Wave 1

- Run: `c572e35799ba4f628636c9da963dfbb1`
- Wave: `7510128325084a3e992483c1436b7c25`
- Objective: P0.3 coverage wave: add only missing deterministic/isolated proofs. F9: prove persisted recent restart history is preserved and four attempts inside the restart window produce CRASH_LOOP_SUPPRESSED, no new child PID, and future suppressed_until. F3: prove RecoveryPlaneService.ensureMcp in an isolated temporary data root can start a device-bound Recovery MCP, survive an exact owned-process kill by replacing it with a different PID on the same port, and preserve device_id/device_instance_id in health and persisted recovery-plane state. Do not change production implementation because exact preflight showed Get-OptionalProperty is already correct. Do not touch active development runtime/AppData, external tunnel/provider resources, accepted AGENTS.md change, unrelated UI files, or volatile evidence.
- Mode: `mcp_only`
- Base HEAD: `885260b404c2c64df1b1afa835963045ac55dbf6`
- Worktree fingerprint: `3d6f962c961c970ebb3cf1d98bfeaefb500046f1a254a0540410c2ee1b355bcf`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 13239 | 2026-08-17T09:36:45.831Z | run_started |  | PREFLIGHT |  |
| 13240 | 2026-08-17T09:36:46.431Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 13241 | 2026-08-17T09:36:46.624Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 13242 | 2026-08-17T09:36:46.782Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 13243 | 2026-08-17T09:36:47.005Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 13244 | 2026-08-17T09:36:47.206Z | state_transition | READY | ROUTED | reason=route_selected |
| 13245 | 2026-08-17T09:36:47.922Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=3e0ab546cf614762b5237bb634bd456c |
| 13246 | 2026-08-17T09:36:48.121Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 13247 | 2026-08-17T09:36:48.847Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=3e0ab546cf614762b5237bb634bd456c |
| 13248 | 2026-08-17T09:36:49.048Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 13249 | 2026-08-17T09:36:49.630Z | proof_cache_miss |  |  | reason=cold; stage_id=check:faadcd74eb35d8de; input_fingerprint=da0966bea5cd8023622b772a18df685e7bedc9f0bc6f80ea6e12f3e986dd6c95 |
| 13250 | 2026-08-17T09:36:50.050Z | managed_process_admitted |  |  | owner=default |
| 13251 | 2026-08-17T09:36:50.387Z | managed_process_started |  |  | owner=default |
| 13252 | 2026-08-17T09:36:50.937Z | managed_process_terminal |  |  | owner=default |
| 13253 | 2026-08-17T09:36:51.357Z | proof_recorded |  |  | stage_id=check:faadcd74eb35d8de; status=passed; cache_hit=False; input_fingerprint=da0966bea5cd8023622b772a18df685e7bedc9f0bc6f80ea6e12f3e986dd6c95 |
| 13254 | 2026-08-17T09:36:51.547Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=9b31336cbbc1e82a9ec5082380e2b9fd15cbeeebb3bedc2e24ad6c03512df906 |
| 13255 | 2026-08-17T09:36:51.964Z | managed_process_admitted |  |  | owner=default |
| 13256 | 2026-08-17T09:36:52.343Z | managed_process_started |  |  | owner=default |
| 13257 | 2026-08-17T09:37:03.118Z | managed_process_terminal |  |  | owner=default |
| 13258 | 2026-08-17T09:37:04.491Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=9b31336cbbc1e82a9ec5082380e2b9fd15cbeeebb3bedc2e24ad6c03512df906 |
| 13259 | 2026-08-17T09:37:05.265Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 13260 | 2026-08-17T09:37:51.729Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 13261 | 2026-08-17T09:37:52.161Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:faadcd74eb35d8de | passed | da0966bea5cd8023622b772a18df685e7bedc9f0bc6f80ea6e12f3e986dd6c95 | False | 1256 | 0 |
| verify:tests | passed | 9b31336cbbc1e82a9ec5082380e2b9fd15cbeeebb3bedc2e24ad6c03512df906 | False | 12453 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| cece0b058f7b40d3941eb627e7776389 | accepted | 885260b404c2c64df1b1afa835963045ac55dbf6 | 6f36ad2898aff41bd9df7af4c8404b2e2b5c47978a5eecce92bd4d58797970e2 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `23`
- Chain head: `149908a85889058873dae6d7688e431b774ba263d9d391fa7e341291523b2394`
