# Orchestration Wave 2

- Run: `11d1a20e29714117bd1bd3061e9e559c`
- Wave: `5f27d3ae58a64202becd5a5e35718af4`
- Objective: Complete the multi-device product slice on authoritative E:\DEV\Tools-Codex-web only. Preserve accepted M1.1 device identity lifecycle and all unrelated WIP. Finish M1.2 end-to-end ownership: Coding MCP and Recovery MCP health/status expose persistent device_id and Recovery-Host-lifecycle device_instance_id; RuntimeOrchestrator accepts supervised Coding MCP only when expected workspace and device_id match; local Native/Tunnel/Recovery Plane state records device ownership fingerprints so a known foreign-owned live PID is never silently reused, adopted, or killed, while legacy ownerless local state is migrated safely without claiming proof. Then add operator-facing device UI: the main header must clearly show the current device display name/identity plus Coding/Recovery/Git status; add a management section that shows current device_id, device_instance_id, online/runtime/tunnel state, workspace/project, Git branch/head/dirty when available, and current Coding/Recovery tunnel IDs with explicit local-only scope. Provide safe controls only for operations the existing Recovery Host already supports (refresh/start/stop/restart/repair current device/runtime as applicable); do not invent cross-device actions or claim a shared registry exists. Structure the UI so a future M2 device selector/list can replace the current-device-only projection without changing identity semantics. Add focused tests for ownership fail-closed behavior and UI/status projection. Do not change public smart-v3 MCP tool surface, do not restart/deploy/push, and fail closed if repository root is not E:/DEV/Tools-Codex-web.
- Mode: `mcp_only`
- Base HEAD: `3a3abaff72a8e6382e4c362865becba069e4ecfc`
- Worktree fingerprint: `3e957266c165b931e2c5d156a668ba01e5dc3454c671cc72939d4d571b554e78`
- Contract fingerprint: `7945d54fbaf9fbf95da004970adece1cb670f32e8091129a70eb91099317b71b`
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 11188 | 2026-08-17T04:11:00.006Z | wave_replanned |  | PREFLIGHT | reason=Acceptance review discovered that RecoveryIpcServer, the actual recovery-host.json descriptor writer, did not receive or persist device_id/device_instance_id while Recovery MCP now validates those fields. Keep the accepted architecture and UI unchanged; add identity to that descriptor boundary and prove the real Recovery MCP health/repair path with matching device lifecycle identity. |
| 11189 | 2026-08-17T04:11:00.202Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 11190 | 2026-08-17T04:11:00.362Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 11191 | 2026-08-17T04:11:00.536Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 11192 | 2026-08-17T04:11:00.735Z | state_transition | READY | ROUTED | reason=route_selected |
| 11193 | 2026-08-17T04:11:01.295Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=1a9dba8ef4104054ac99438d1ba1ee0f |
| 11194 | 2026-08-17T04:11:01.460Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 11195 | 2026-08-17T04:11:02.236Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=1a9dba8ef4104054ac99438d1ba1ee0f |
| 11196 | 2026-08-17T04:11:02.417Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 11197 | 2026-08-17T04:11:03.107Z | proof_cache_miss |  |  | reason=cold; stage_id=check:b17287e1de32ed9a; input_fingerprint=aa03deee36bb16f0d804e0ebe7506a120907e879b02dafee5f5d82d51404b4de |
| 11198 | 2026-08-17T04:11:03.455Z | managed_process_admitted |  |  | owner=default |
| 11199 | 2026-08-17T04:11:03.722Z | managed_process_started |  |  | owner=default |
| 11200 | 2026-08-17T04:11:04.403Z | managed_process_terminal |  |  | owner=default |
| 11201 | 2026-08-17T04:11:04.719Z | proof_recorded |  |  | stage_id=check:b17287e1de32ed9a; status=passed; cache_hit=False; input_fingerprint=aa03deee36bb16f0d804e0ebe7506a120907e879b02dafee5f5d82d51404b4de |
| 11202 | 2026-08-17T04:11:04.889Z | proof_cache_miss |  |  | reason=cold; stage_id=check:6e7fb10f0883115c; input_fingerprint=3464886bd7fd1ab429341504a38e2fd31e75777033fad0e208d39eae47672a18 |
| 11203 | 2026-08-17T04:11:05.214Z | managed_process_admitted |  |  | owner=default |
| 11204 | 2026-08-17T04:11:05.573Z | managed_process_started |  |  | owner=default |
| 11205 | 2026-08-17T04:11:06.002Z | managed_process_terminal |  |  | owner=default |
| 11206 | 2026-08-17T04:11:06.340Z | proof_recorded |  |  | stage_id=check:6e7fb10f0883115c; status=passed; cache_hit=False; input_fingerprint=3464886bd7fd1ab429341504a38e2fd31e75777033fad0e208d39eae47672a18 |
| 11207 | 2026-08-17T04:11:06.535Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:25606f562d597b39; input_fingerprint=967cbb0cb46781b876dce014ca6b9cfa22587ee0bacaf10265140d250a062987 |
| 11208 | 2026-08-17T04:11:06.869Z | managed_process_admitted |  |  | owner=default |
| 11209 | 2026-08-17T04:11:07.130Z | managed_process_started |  |  | owner=default |
| 11210 | 2026-08-17T04:11:07.561Z | managed_process_terminal |  |  | owner=default |
| 11211 | 2026-08-17T04:11:07.900Z | proof_recorded |  |  | stage_id=check:25606f562d597b39; status=passed; cache_hit=False; input_fingerprint=967cbb0cb46781b876dce014ca6b9cfa22587ee0bacaf10265140d250a062987 |
| 11212 | 2026-08-17T04:11:08.182Z | proof_cache_miss |  |  | reason=cold; stage_id=check:2ae5f9fdc9978191; input_fingerprint=3e87dfc8e170f29006a963d9d4f1e25bc14c0de68018aec9d0699fc7049b700b |
| 11213 | 2026-08-17T04:11:08.547Z | managed_process_admitted |  |  | owner=default |
| 11214 | 2026-08-17T04:11:08.822Z | managed_process_started |  |  | owner=default |
| 11215 | 2026-08-17T04:11:10.264Z | managed_process_terminal |  |  | owner=default |
| 11216 | 2026-08-17T04:11:10.653Z | proof_recorded |  |  | stage_id=check:2ae5f9fdc9978191; status=passed; cache_hit=False; input_fingerprint=3e87dfc8e170f29006a963d9d4f1e25bc14c0de68018aec9d0699fc7049b700b |
| 11217 | 2026-08-17T04:11:11.274Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 11218 | 2026-08-17T04:11:38.647Z | managed_process_admitted |  |  | owner=default |
| 11219 | 2026-08-17T04:11:39.003Z | managed_process_started |  |  | owner=default |
| 11220 | 2026-08-17T04:11:40.198Z | managed_process_terminal |  |  | owner=default |
| 11221 | 2026-08-17T04:12:02.354Z | failure_observed | ACCEPTING | ACCEPTING | reason=Acceptance review found a state-preservation defect: NativeService.start rewrites runtime-state via currentRuntimeState(), whose whitelist preserves tunnelPid/tunnelStartedAt but not the new tunnelId/tunnelFingerprint/tunnelDeviceId/tunnelDeviceInstanceId. A controlled Coding MCP activation intentionally preserves the live Tunnel, so this rewrite would erase its ownership proof and make the same Tunnel fail device-aware status/stop checks. Replan must preserve the complete current Tunnel ownership tuple across Native process replacement and add regression proof.; failure_class=SOL_REJECTED |
| 11222 | 2026-08-17T04:12:02.502Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |
| 11223 | 2026-08-17T04:12:02.835Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:b17287e1de32ed9a | passed | aa03deee36bb16f0d804e0ebe7506a120907e879b02dafee5f5d82d51404b4de | False | 1303 | 0 |
| check:6e7fb10f0883115c | passed | 3464886bd7fd1ab429341504a38e2fd31e75777033fad0e208d39eae47672a18 | False | 1116 | 0 |
| check:25606f562d597b39 | passed | 967cbb0cb46781b876dce014ca6b9cfa22587ee0bacaf10265140d250a062987 | False | 1030 | 0 |
| check:2ae5f9fdc9978191 | passed | 3e87dfc8e170f29006a963d9d4f1e25bc14c0de68018aec9d0699fc7049b700b | False | 2098 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `120`
- Chain head: `c0360c2ca738977bb2bcca8e30ae45300c1d6d1448a5737d297669c22d3624a1`
