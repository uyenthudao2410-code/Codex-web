# Orchestration Wave 1

- Run: `94d12f71be29494cbaf3dfc430b5cf3e`
- Wave: `d87d6d29c0a74889967ae65cbecfeaaa`
- Objective: Proof-only reconciliation of the already-installed Machine-A C01 candidate after the prior orchestration parser failure. Do not install again. Verify current persistent state only: one Coding Tools MCP uninstall registration at the normal per-user location, installed executable exists and hash is captured, no packaged process is running, HKCU Run has no Coding Tools MCP entry, production Recovery descriptor remains SHA256 90cd716495beda127cf00aaf44614ef71b7cb80471e02b1176e30e756f8941f6, and WebMCP Recovery Supervisor task XML remains SHA256 68b7d4a018fbe21c044d34a409ec09248b47198a35400d82a3bd1f552a043295. No source edits, launch, autostart enable, reboot/runtime restart, commit/push/publish/release/deploy.
- Objective revision: `1`
- Objective SHA-256: `08758d109846934209192ba4950df11d30dc0a6d6be31e64f1e8039dbee47fca`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `ae04947d5969e9ee92bf1fe7532bf30e186f8280`
- Worktree fingerprint: `040697b3da54854e17f7eb6a9d4405204217cbea6705207af6c3e113345ffcb9`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 55461 | 2026-09-14T14:10:53.801Z | run_started |  | PREFLIGHT |  |
| 55462 | 2026-09-14T14:10:54.596Z | observation_span_recorded |  |  |  |
| 55463 | 2026-09-14T14:11:00.049Z | observation_span_recorded |  |  |  |
| 55464 | 2026-09-14T14:11:00.318Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 55465 | 2026-09-14T14:11:00.500Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 55466 | 2026-09-14T14:11:00.737Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 55467 | 2026-09-14T14:11:00.950Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 55468 | 2026-09-14T14:11:01.219Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 55469 | 2026-09-14T14:11:01.396Z | state_transition | READY | ROUTED | reason=route_selected |
| 55470 | 2026-09-14T14:11:01.611Z | observation_span_recorded |  |  |  |
| 55471 | 2026-09-14T14:11:02.184Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=dfd4675601064bc49e5a0926e267cc6c |
| 55472 | 2026-09-14T14:11:02.384Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 55473 | 2026-09-14T14:11:02.869Z | observation_span_recorded |  |  |  |
| 55474 | 2026-09-14T14:11:03.310Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=dfd4675601064bc49e5a0926e267cc6c |
| 55475 | 2026-09-14T14:11:03.521Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 55476 | 2026-09-14T14:11:04.037Z | proof_cache_miss |  |  | reason=cold; stage_id=check:7c235aeadb94ec7e; input_fingerprint=988d2e69722909ca0fdc0683d09e4e84cc829c577a688f69f5043458be3645e6 |
| 55477 | 2026-09-14T14:11:04.410Z | managed_process_admitted |  |  | owner=default |
| 55478 | 2026-09-14T14:11:04.833Z | managed_process_started |  |  | owner=default |
| 55479 | 2026-09-14T14:11:05.349Z | managed_process_terminal |  |  | owner=default |
| 55480 | 2026-09-14T14:11:05.755Z | proof_recorded |  |  | stage_id=check:7c235aeadb94ec7e; status=passed; cache_hit=False; input_fingerprint=988d2e69722909ca0fdc0683d09e4e84cc829c577a688f69f5043458be3645e6 |
| 55481 | 2026-09-14T14:11:05.950Z | proof_cache_miss |  |  | reason=cold; stage_id=check:18dbc6049c4207bc; input_fingerprint=9f6fb6af9e48b392c7e95b99deff39dc9df6fb6d9502c19910d88676a812102c |
| 55482 | 2026-09-14T14:11:06.355Z | managed_process_admitted |  |  | owner=default |
| 55483 | 2026-09-14T14:11:06.729Z | managed_process_started |  |  | owner=default |
| 55484 | 2026-09-14T14:11:07.212Z | managed_process_terminal |  |  | owner=default |
| 55485 | 2026-09-14T14:11:07.667Z | proof_recorded |  |  | stage_id=check:18dbc6049c4207bc; status=passed; cache_hit=False; input_fingerprint=9f6fb6af9e48b392c7e95b99deff39dc9df6fb6d9502c19910d88676a812102c |
| 55486 | 2026-09-14T14:11:07.838Z | proof_cache_miss |  |  | reason=cold; stage_id=check:84a2a6ee761b2fd3; input_fingerprint=4303d28ec1acf5679f195a95ee2f61524357b46da8d42db08f44b254951ba2ee |
| 55487 | 2026-09-14T14:11:08.168Z | managed_process_admitted |  |  | owner=default |
| 55488 | 2026-09-14T14:11:08.604Z | managed_process_started |  |  | owner=default |
| 55489 | 2026-09-14T14:11:09.061Z | managed_process_terminal |  |  | owner=default |
| 55490 | 2026-09-14T14:11:09.459Z | proof_recorded |  |  | stage_id=check:84a2a6ee761b2fd3; status=passed; cache_hit=False; input_fingerprint=4303d28ec1acf5679f195a95ee2f61524357b46da8d42db08f44b254951ba2ee |
| 55491 | 2026-09-14T14:11:09.621Z | proof_cache_miss |  |  | reason=cold; stage_id=check:2f6c1b6b180db301; input_fingerprint=f50134d36ae8525cbd742bd25508f082440e8af2f0d3ab3099fb4987cc1ce321 |
| 55492 | 2026-09-14T14:11:10.331Z | managed_process_admitted |  |  | owner=default |
| 55493 | 2026-09-14T14:11:10.770Z | managed_process_started |  |  | owner=default |
| 55494 | 2026-09-14T14:11:11.304Z | managed_process_terminal |  |  | owner=default |
| 55495 | 2026-09-14T14:11:11.644Z | proof_recorded |  |  | stage_id=check:2f6c1b6b180db301; status=passed; cache_hit=False; input_fingerprint=f50134d36ae8525cbd742bd25508f082440e8af2f0d3ab3099fb4987cc1ce321 |
| 55496 | 2026-09-14T14:11:11.888Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:564df5f1546757a9; input_fingerprint=83261a35c57aa013abeeca56423c0850ef117fa7fd358d3687eae46b64fcc96d |
| 55497 | 2026-09-14T14:11:12.346Z | managed_process_admitted |  |  | owner=default |
| 55498 | 2026-09-14T14:11:12.696Z | managed_process_started |  |  | owner=default |
| 55499 | 2026-09-14T14:11:13.170Z | managed_process_terminal |  |  | owner=default |
| 55500 | 2026-09-14T14:11:13.546Z | proof_recorded |  |  | stage_id=check:564df5f1546757a9; status=passed; cache_hit=False; input_fingerprint=83261a35c57aa013abeeca56423c0850ef117fa7fd358d3687eae46b64fcc96d |
| 55501 | 2026-09-14T14:11:13.728Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:113ac9c59cdb7236; input_fingerprint=f1bbecf9ad7afb2f00c37536a6c3e73bfe1a6bc187203779340ebaaff3eda17d |
| 55502 | 2026-09-14T14:11:14.178Z | managed_process_admitted |  |  | owner=default |
| 55503 | 2026-09-14T14:11:14.554Z | managed_process_started |  |  | owner=default |
| 55504 | 2026-09-14T14:11:15.088Z | managed_process_terminal |  |  | owner=default |
| 55505 | 2026-09-14T14:11:15.454Z | proof_recorded |  |  | stage_id=check:113ac9c59cdb7236; status=passed; cache_hit=False; input_fingerprint=f1bbecf9ad7afb2f00c37536a6c3e73bfe1a6bc187203779340ebaaff3eda17d |
| 55506 | 2026-09-14T14:11:15.796Z | observation_span_recorded |  |  |  |
| 55507 | 2026-09-14T14:11:16.052Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 55508 | 2026-09-14T14:11:16.368Z | observation_stage_anchor_recorded | ACCEPTING | ACCEPTING |  |
| 55509 | 2026-09-14T14:11:31.392Z | continuity_telemetry_recorded |  |  |  |
| 55510 | 2026-09-14T14:11:41.348Z | quality_outcome_recorded |  |  |  |
| 55511 | 2026-09-14T14:11:41.569Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 55512 | 2026-09-14T14:11:41.912Z | observation_span_recorded |  |  |  |
| 55513 | 2026-09-14T14:11:42.151Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |
| 55514 | 2026-09-14T14:11:42.367Z | observation_span_recorded |  |  |  |
| 55515 | 2026-09-14T14:11:42.907Z | observation_span_recorded |  |  |  |
| 55516 | 2026-09-14T14:11:43.168Z | continuity_telemetry_recorded |  |  |  |
| 55517 | 2026-09-14T14:12:12.841Z | continuity_telemetry_recorded |  |  |  |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:7c235aeadb94ec7e | passed | 988d2e69722909ca0fdc0683d09e4e84cc829c577a688f69f5043458be3645e6 | False | 1344 | 0 |
| check:18dbc6049c4207bc | passed | 9f6fb6af9e48b392c7e95b99deff39dc9df6fb6d9502c19910d88676a812102c | False | 1378 | 0 |
| check:84a2a6ee761b2fd3 | passed | 4303d28ec1acf5679f195a95ee2f61524357b46da8d42db08f44b254951ba2ee | False | 1270 | 0 |
| check:2f6c1b6b180db301 | passed | f50134d36ae8525cbd742bd25508f082440e8af2f0d3ab3099fb4987cc1ce321 | False | 1392 | 0 |
| check:564df5f1546757a9 | passed | 83261a35c57aa013abeeca56423c0850ef117fa7fd358d3687eae46b64fcc96d | False | 1197 | 0 |
| check:113ac9c59cdb7236 | passed | f1bbecf9ad7afb2f00c37536a6c3e73bfe1a6bc187203779340ebaaff3eda17d | False | 1318 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 23cfc9c9ed69490caf63591ee317c369 | accepted | ae04947d5969e9ee92bf1fe7532bf30e186f8280 | 7b73ab5e11b21e44c351b4c1947b4ce72634d71c248f4b75858d5987da0ed848 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `57`
- Chain head: `d76ce0adf8ee1931d07af4496a0f7db98ff1a5cd5d35d4eef1f995f2ec0942e1`
