# Orchestration Wave 3

- Run: `11d1a20e29714117bd1bd3061e9e559c`
- Wave: `c77b36d4a3c6473b92ece6b5214a9cc3`
- Objective: Complete the multi-device product slice on authoritative E:\DEV\Tools-Codex-web only. Preserve accepted M1.1 device identity lifecycle and all unrelated WIP. Finish M1.2 end-to-end ownership: Coding MCP and Recovery MCP health/status expose persistent device_id and Recovery-Host-lifecycle device_instance_id; RuntimeOrchestrator accepts supervised Coding MCP only when expected workspace and device_id match; local Native/Tunnel/Recovery Plane state records device ownership fingerprints so a known foreign-owned live PID is never silently reused, adopted, or killed, while legacy ownerless local state is migrated safely without claiming proof. Then add operator-facing device UI: the main header must clearly show the current device display name/identity plus Coding/Recovery/Git status; add a management section that shows current device_id, device_instance_id, online/runtime/tunnel state, workspace/project, Git branch/head/dirty when available, and current Coding/Recovery tunnel IDs with explicit local-only scope. Provide safe controls only for operations the existing Recovery Host already supports (refresh/start/stop/restart/repair current device/runtime as applicable); do not invent cross-device actions or claim a shared registry exists. Structure the UI so a future M2 device selector/list can replace the current-device-only projection without changing identity semantics. Add focused tests for ownership fail-closed behavior and UI/status projection. Do not change public smart-v3 MCP tool surface, do not restart/deploy/push, and fail closed if repository root is not E:/DEV/Tools-Codex-web.
- Mode: `mcp_only`
- Base HEAD: `3a3abaff72a8e6382e4c362865becba069e4ecfc`
- Worktree fingerprint: `9d72de83ddf151cb58c8acf83dc9ded25d4f404ede8cc74407f9bdb07cdd5e95`
- Contract fingerprint: `7945d54fbaf9fbf95da004970adece1cb670f32e8091129a70eb91099317b71b`
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 11224 | 2026-08-17T04:12:23.505Z | wave_replanned |  | PREFLIGHT | reason=Acceptance review showed NativeService.start preserves only tunnelPid/tunnelStartedAt when rewriting runtime-state, dropping the new tunnel ownership/fingerprint tuple during a Coding MCP-only restart. Keep all other M1.2 behavior unchanged; preserve the complete Coding Tunnel identity tuple in currentRuntimeState and lock it with a regression test. |
| 11225 | 2026-08-17T04:12:23.688Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 11226 | 2026-08-17T04:12:23.805Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 11227 | 2026-08-17T04:12:23.968Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 11228 | 2026-08-17T04:12:24.160Z | state_transition | READY | ROUTED | reason=route_selected |
| 11229 | 2026-08-17T04:12:25.261Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=de809e7eff8241259a6516aeea20adb9 |
| 11230 | 2026-08-17T04:12:25.410Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 11231 | 2026-08-17T04:12:26.103Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=de809e7eff8241259a6516aeea20adb9 |
| 11232 | 2026-08-17T04:12:26.319Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 11233 | 2026-08-17T04:12:27.016Z | proof_cache_miss |  |  | reason=cold; stage_id=check:943287ed6741d397; input_fingerprint=d85c0ee1284aa1b1bd0d33ee6d917d0b84157022a745046ef86dcfc2f16590ff |
| 11234 | 2026-08-17T04:12:27.439Z | managed_process_admitted |  |  | owner=default |
| 11235 | 2026-08-17T04:12:27.764Z | managed_process_started |  |  | owner=default |
| 11236 | 2026-08-17T04:12:28.599Z | managed_process_terminal |  |  | owner=default |
| 11237 | 2026-08-17T04:12:28.960Z | proof_recorded |  |  | stage_id=check:943287ed6741d397; status=passed; cache_hit=False; input_fingerprint=d85c0ee1284aa1b1bd0d33ee6d917d0b84157022a745046ef86dcfc2f16590ff |
| 11238 | 2026-08-17T04:12:29.373Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:a93edb4da0e64a89; input_fingerprint=85a54510cc7fcc6be032eb85a68b0da257717b00d72fa19ce170fea2b31d7551 |
| 11239 | 2026-08-17T04:12:29.752Z | managed_process_admitted |  |  | owner=default |
| 11240 | 2026-08-17T04:12:30.069Z | managed_process_started |  |  | owner=default |
| 11241 | 2026-08-17T04:12:30.636Z | managed_process_terminal |  |  | owner=default |
| 11242 | 2026-08-17T04:12:30.936Z | proof_recorded |  |  | stage_id=check:a93edb4da0e64a89; status=passed; cache_hit=False; input_fingerprint=85a54510cc7fcc6be032eb85a68b0da257717b00d72fa19ce170fea2b31d7551 |
| 11243 | 2026-08-17T04:12:31.118Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:2ae5f9fdc9978191; input_fingerprint=f6a91ae9faf4a8d43c08f4cad670ebcc01f7dee69b49a1debb2d993c92bef94f |
| 11244 | 2026-08-17T04:12:31.498Z | managed_process_admitted |  |  | owner=default |
| 11245 | 2026-08-17T04:12:31.806Z | managed_process_started |  |  | owner=default |
| 11246 | 2026-08-17T04:12:33.432Z | managed_process_terminal |  |  | owner=default |
| 11247 | 2026-08-17T04:12:33.822Z | proof_recorded |  |  | stage_id=check:2ae5f9fdc9978191; status=passed; cache_hit=False; input_fingerprint=f6a91ae9faf4a8d43c08f4cad670ebcc01f7dee69b49a1debb2d993c92bef94f |
| 11248 | 2026-08-17T04:12:34.524Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 11249 | 2026-08-17T04:12:54.483Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 11250 | 2026-08-17T04:12:54.761Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:943287ed6741d397 | passed | d85c0ee1284aa1b1bd0d33ee6d917d0b84157022a745046ef86dcfc2f16590ff | False | 1572 | 0 |
| check:a93edb4da0e64a89 | passed | 85a54510cc7fcc6be032eb85a68b0da257717b00d72fa19ce170fea2b31d7551 | False | 1216 | 0 |
| check:2ae5f9fdc9978191 | passed | f6a91ae9faf4a8d43c08f4cad670ebcc01f7dee69b49a1debb2d993c92bef94f | False | 2314 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| cf6caaf16c364483a74e1db5a30e9fff | accepted | 3a3abaff72a8e6382e4c362865becba069e4ecfc | f39b019ce72d0bf505dc02f3d732e1240c92712255abbb6eda32962b833f32aa | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `120`
- Chain head: `c0360c2ca738977bb2bcca8e30ae45300c1d6d1448a5737d297669c22d3624a1`
