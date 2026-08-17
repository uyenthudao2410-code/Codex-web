# Orchestration Wave 1

- Run: `11d1a20e29714117bd1bd3061e9e559c`
- Wave: `6d309b932532411aa3df4e07e2628dc0`
- Objective: Complete the multi-device product slice on authoritative E:\DEV\Tools-Codex-web only. Preserve accepted M1.1 device identity lifecycle and all unrelated WIP. Finish M1.2 end-to-end ownership: Coding MCP and Recovery MCP health/status expose persistent device_id and Recovery-Host-lifecycle device_instance_id; RuntimeOrchestrator accepts supervised Coding MCP only when expected workspace and device_id match; local Native/Tunnel/Recovery Plane state records device ownership fingerprints so a known foreign-owned live PID is never silently reused, adopted, or killed, while legacy ownerless local state is migrated safely without claiming proof. Then add operator-facing device UI: the main header must clearly show the current device display name/identity plus Coding/Recovery/Git status; add a management section that shows current device_id, device_instance_id, online/runtime/tunnel state, workspace/project, Git branch/head/dirty when available, and current Coding/Recovery tunnel IDs with explicit local-only scope. Provide safe controls only for operations the existing Recovery Host already supports (refresh/start/stop/restart/repair current device/runtime as applicable); do not invent cross-device actions or claim a shared registry exists. Structure the UI so a future M2 device selector/list can replace the current-device-only projection without changing identity semantics. Add focused tests for ownership fail-closed behavior and UI/status projection. Do not change public smart-v3 MCP tool surface, do not restart/deploy/push, and fail closed if repository root is not E:/DEV/Tools-Codex-web.
- Mode: `mcp_only`
- Base HEAD: `3a3abaff72a8e6382e4c362865becba069e4ecfc`
- Worktree fingerprint: `d55545ecb18af3bb826c4216b562405e79412a5f59058824c15cbecff1a91379`
- Contract fingerprint: `7945d54fbaf9fbf95da004970adece1cb670f32e8091129a70eb91099317b71b`
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 11131 | 2026-08-17T03:56:48.531Z | run_started |  | PREFLIGHT |  |
| 11132 | 2026-08-17T03:56:49.334Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 11133 | 2026-08-17T03:57:08.387Z | managed_process_admitted |  |  | owner=default |
| 11134 | 2026-08-17T03:57:08.703Z | managed_process_started |  |  | owner=default |
| 11135 | 2026-08-17T03:57:09.329Z | managed_process_terminal |  |  | owner=default |
| 11136 | 2026-08-17T03:58:51.188Z | managed_process_admitted |  |  | owner=default |
| 11137 | 2026-08-17T03:58:51.490Z | managed_process_started |  |  | owner=default |
| 11138 | 2026-08-17T03:58:52.094Z | managed_process_terminal |  |  | owner=default |
| 11139 | 2026-08-17T03:59:08.957Z | managed_process_admitted |  |  | owner=default |
| 11140 | 2026-08-17T03:59:09.261Z | managed_process_started |  |  | owner=default |
| 11141 | 2026-08-17T03:59:10.027Z | managed_process_terminal |  |  | owner=default |
| 11142 | 2026-08-17T03:59:32.390Z | managed_process_admitted |  |  | owner=default |
| 11143 | 2026-08-17T03:59:32.716Z | managed_process_started |  |  | owner=default |
| 11144 | 2026-08-17T03:59:33.444Z | managed_process_terminal |  |  | owner=default |
| 11145 | 2026-08-17T04:01:53.857Z | managed_process_admitted |  |  | owner=default |
| 11146 | 2026-08-17T04:01:54.161Z | managed_process_started |  |  | owner=default |
| 11147 | 2026-08-17T04:01:54.628Z | managed_process_terminal |  |  | owner=default |
| 11148 | 2026-08-17T04:08:16.373Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 11149 | 2026-08-17T04:08:16.680Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 11150 | 2026-08-17T04:08:16.890Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 11151 | 2026-08-17T04:08:17.056Z | state_transition | READY | ROUTED | reason=route_selected |
| 11152 | 2026-08-17T04:08:17.897Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=f68cd40bccb546fe91a62bc56621aa52 |
| 11153 | 2026-08-17T04:08:18.130Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 11154 | 2026-08-17T04:08:19.995Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=f68cd40bccb546fe91a62bc56621aa52 |
| 11155 | 2026-08-17T04:08:20.243Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 11156 | 2026-08-17T04:08:20.940Z | proof_cache_miss |  |  | reason=cold; stage_id=check:3be3c6b27b6df81e; input_fingerprint=f6bea6a30cfd6277f65df67cc625ba339de57058f7ae56ced723d2f7f3ff9103 |
| 11157 | 2026-08-17T04:08:21.443Z | managed_process_admitted |  |  | owner=default |
| 11158 | 2026-08-17T04:08:21.770Z | managed_process_started |  |  | owner=default |
| 11159 | 2026-08-17T04:08:22.353Z | managed_process_terminal |  |  | owner=default |
| 11160 | 2026-08-17T04:08:22.688Z | proof_recorded |  |  | stage_id=check:3be3c6b27b6df81e; status=passed; cache_hit=False; input_fingerprint=f6bea6a30cfd6277f65df67cc625ba339de57058f7ae56ced723d2f7f3ff9103 |
| 11161 | 2026-08-17T04:08:22.901Z | proof_cache_miss |  |  | reason=cold; stage_id=check:c52c372a9fb3ece6; input_fingerprint=327b56bf6fbf391c24349fe96601ec81368c5fc1662c811977c610dead7d3057 |
| 11162 | 2026-08-17T04:08:23.369Z | managed_process_admitted |  |  | owner=default |
| 11163 | 2026-08-17T04:08:23.670Z | managed_process_started |  |  | owner=default |
| 11164 | 2026-08-17T04:08:24.594Z | managed_process_terminal |  |  | owner=default |
| 11165 | 2026-08-17T04:08:24.943Z | proof_recorded |  |  | stage_id=check:c52c372a9fb3ece6; status=passed; cache_hit=False; input_fingerprint=327b56bf6fbf391c24349fe96601ec81368c5fc1662c811977c610dead7d3057 |
| 11166 | 2026-08-17T04:08:25.141Z | proof_cache_miss |  |  | reason=cold; stage_id=check:9fab50ad681fe431; input_fingerprint=bec1023680f2f7dbd5f6577eb210801fa4e29b4d2238760abfa66869b975621c |
| 11167 | 2026-08-17T04:08:25.493Z | managed_process_admitted |  |  | owner=default |
| 11168 | 2026-08-17T04:08:25.803Z | managed_process_started |  |  | owner=default |
| 11169 | 2026-08-17T04:08:26.303Z | managed_process_terminal |  |  | owner=default |
| 11170 | 2026-08-17T04:08:26.630Z | proof_recorded |  |  | stage_id=check:9fab50ad681fe431; status=passed; cache_hit=False; input_fingerprint=bec1023680f2f7dbd5f6577eb210801fa4e29b4d2238760abfa66869b975621c |
| 11171 | 2026-08-17T04:08:26.883Z | proof_cache_miss |  |  | reason=cold; stage_id=check:7b84264a3f056c4f; input_fingerprint=e574bfc0f089a62a4d6877df91eb16be80db69675f379e46ffe7f96055b2b407 |
| 11172 | 2026-08-17T04:08:27.355Z | managed_process_admitted |  |  | owner=default |
| 11173 | 2026-08-17T04:08:27.686Z | managed_process_started |  |  | owner=default |
| 11174 | 2026-08-17T04:08:28.994Z | managed_process_terminal |  |  | owner=default |
| 11175 | 2026-08-17T04:08:29.352Z | proof_recorded |  |  | stage_id=check:7b84264a3f056c4f; status=passed; cache_hit=False; input_fingerprint=e574bfc0f089a62a4d6877df91eb16be80db69675f379e46ffe7f96055b2b407 |
| 11176 | 2026-08-17T04:08:29.590Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:9f3f83d6b46d2388; input_fingerprint=77d6b602663d2d428d6d58188fd9b081b2f2d12766d9c6220127ad5fc21d64b2 |
| 11177 | 2026-08-17T04:08:30.035Z | managed_process_admitted |  |  | owner=default |
| 11178 | 2026-08-17T04:08:30.359Z | managed_process_started |  |  | owner=default |
| 11179 | 2026-08-17T04:08:31.427Z | managed_process_terminal |  |  | owner=default |
| 11180 | 2026-08-17T04:08:31.829Z | proof_recorded |  |  | stage_id=check:9f3f83d6b46d2388; status=passed; cache_hit=False; input_fingerprint=77d6b602663d2d428d6d58188fd9b081b2f2d12766d9c6220127ad5fc21d64b2 |
| 11181 | 2026-08-17T04:08:32.840Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 11182 | 2026-08-17T04:09:48.935Z | managed_process_admitted |  |  | owner=default |
| 11183 | 2026-08-17T04:09:49.294Z | managed_process_started |  |  | owner=default |
| 11184 | 2026-08-17T04:09:50.186Z | managed_process_terminal |  |  | owner=default |
| 11185 | 2026-08-17T04:10:12.888Z | failure_observed | ACCEPTING | ACCEPTING | reason=Acceptance review found a real cross-boundary defect: Recovery MCP now validates recovery-host.json against expected device_id/device_instance_id, but RecoveryIpcServer—the actual descriptor writer—still emits only instance_id and no device identity. In the real device-aware Recovery Plane this would make repair_primary_runtime reject its own current Recovery Host. The wave must be replanned to bind RecoveryIpcServer descriptor ownership to the same persistent device/current host lifecycle and add focused proof.; failure_class=SOL_REJECTED |
| 11186 | 2026-08-17T04:10:13.070Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |
| 11187 | 2026-08-17T04:10:13.339Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:3be3c6b27b6df81e | passed | f6bea6a30cfd6277f65df67cc625ba339de57058f7ae56ced723d2f7f3ff9103 | False | 1407 | 0 |
| check:c52c372a9fb3ece6 | passed | 327b56bf6fbf391c24349fe96601ec81368c5fc1662c811977c610dead7d3057 | False | 1711 | 0 |
| check:9fab50ad681fe431 | passed | bec1023680f2f7dbd5f6577eb210801fa4e29b4d2238760abfa66869b975621c | False | 1158 | 0 |
| check:7b84264a3f056c4f | passed | e574bfc0f089a62a4d6877df91eb16be80db69675f379e46ffe7f96055b2b407 | False | 2107 | 0 |
| check:9f3f83d6b46d2388 | passed | 77d6b602663d2d428d6d58188fd9b081b2f2d12766d9c6220127ad5fc21d64b2 | False | 1868 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `120`
- Chain head: `c0360c2ca738977bb2bcca8e30ae45300c1d6d1448a5737d297669c22d3624a1`
