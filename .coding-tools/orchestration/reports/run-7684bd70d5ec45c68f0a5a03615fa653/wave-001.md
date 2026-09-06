# Orchestration Wave 1

- Run: `7684bd70d5ec45c68f0a5a03615fa653`
- Wave: `3618a4ff5cc4417ab52ea48ee0856d92`
- Objective: C5 historical prior-artifact build only, continuing after accepted current-lifecycle checkpoint b51dd665a3dc4db7ac5c73d93f160f02, C5 contract checkpoint fd7c90d5d2db477cbc45e7bfa280d3fc, and predecessor C4 checkpoint 777480e8957941f9ade53ec06e248d55. Current source remains main/origin HEAD 9e752e34db745cd4fb2d0830a517910eced9c37f. Reproduce the legitimate prior 0.3.4 source at exact commit 026f79b3ab5997cb15f38a3b41769da6a79d790b in external worktree C:\Users\Admin\AppData\Local\Temp\codex-web-c5-prior-026f79b3. Network is forbidden: dependency installation must use npm --offline only, Electron 43.2.0 and electron-builder/NSIS caches were preverified locally. Build the repository-defined prior NSIS artifact only if fully offline succeeds; hash and copy the resulting web-mcp-assistant-setup-0.3.4.exe into C:\Users\Admin\AppData\Local\Temp\codex-web-c5-9e752e34\artifacts. Do NOT install or launch 0.3.4 and do NOT claim upgrade/rollback: the real user profile contains a pre-existing legacy Trợ lý Web MCP shortcut SHA256 393337c654c77795dad8a847a259391364635ed058e75603314b8321200c5957, the prior/current packages share appId com.gptwebcodex.assistant, and Windows Sandbox is unavailable, so host-side upgrade/rollback is not safely isolated. Preserve main source bytes, all .coding-tools evidence and unrelated work. No normal UI, production profile/descriptor/task writes, C4 rerun, network, publish/tag/release/deploy, or forbidden ACK.
- Objective revision: `1`
- Objective SHA-256: `2078766d245ce7d2f61b15d456732bb748a6f3d2405b28d1c38768c21e1346a9`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `9e752e34db745cd4fb2d0830a517910eced9c37f`
- Worktree fingerprint: `6546f235f77e31e7b47a1f6c568d1f6291fec2c3fce76edc6b85030cc9b5259e`
- Contract fingerprint: `937f13a27474a375c6bae1d231939713968154236d3800dab755d951d8b60eb1`
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 41741 | 2026-09-06T06:01:32.737Z | run_started |  | PREFLIGHT |  |
| 41742 | 2026-09-06T06:01:33.142Z | observation_span_recorded |  |  |  |
| 41743 | 2026-09-06T06:01:34.310Z | observation_span_recorded |  |  |  |
| 41744 | 2026-09-06T06:01:34.515Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 41745 | 2026-09-06T06:01:34.738Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 41746 | 2026-09-06T06:01:34.932Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 41747 | 2026-09-06T06:01:35.204Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 41748 | 2026-09-06T06:01:35.405Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 41749 | 2026-09-06T06:01:35.611Z | state_transition | READY | ROUTED | reason=route_selected |
| 41750 | 2026-09-06T06:01:35.831Z | observation_span_recorded |  |  |  |
| 41751 | 2026-09-06T06:01:36.987Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=d342f3da97c44cfd8c9e897fa3a0a9e8 |
| 41752 | 2026-09-06T06:01:37.194Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 41753 | 2026-09-06T06:01:38.160Z | observation_span_recorded |  |  |  |
| 41754 | 2026-09-06T06:01:38.978Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=d342f3da97c44cfd8c9e897fa3a0a9e8 |
| 41755 | 2026-09-06T06:01:39.337Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 41756 | 2026-09-06T06:01:40.318Z | proof_cache_miss |  |  | reason=cold; stage_id=check:68952bdfdf25eaca; input_fingerprint=b0c0f33116a5be05ce2d1703452ad3955ea4b1c759e378a79ec0020dd860dcc7 |
| 41757 | 2026-09-06T06:01:41.044Z | managed_process_admitted |  |  | owner=default |
| 41758 | 2026-09-06T06:01:41.474Z | managed_process_started |  |  | owner=default |
| 41759 | 2026-09-06T06:01:45.006Z | managed_process_terminal |  |  | owner=default |
| 41760 | 2026-09-06T06:01:45.371Z | proof_recorded |  |  | stage_id=check:68952bdfdf25eaca; status=passed; cache_hit=False; input_fingerprint=b0c0f33116a5be05ce2d1703452ad3955ea4b1c759e378a79ec0020dd860dcc7 |
| 41761 | 2026-09-06T06:01:45.558Z | proof_cache_miss |  |  | reason=cold; stage_id=check:e4c791e9c6fad3b4; input_fingerprint=5d30ee3a853b79b360619559ed58c9a0589edbd8e6e7d0c9f490b4b5605f192e |
| 41762 | 2026-09-06T06:01:46.012Z | managed_process_admitted |  |  | owner=default |
| 41763 | 2026-09-06T06:01:46.354Z | managed_process_started |  |  | owner=default |
| 41764 | 2026-09-06T06:01:52.095Z | managed_process_terminal |  |  | owner=default |
| 41765 | 2026-09-06T06:01:52.518Z | proof_recorded |  |  | stage_id=check:e4c791e9c6fad3b4; status=passed; cache_hit=False; input_fingerprint=5d30ee3a853b79b360619559ed58c9a0589edbd8e6e7d0c9f490b4b5605f192e |
| 41766 | 2026-09-06T06:01:52.702Z | proof_cache_miss |  |  | reason=cold; stage_id=check:4a2b623632395e21; input_fingerprint=9164302dd3194cbb69e453beae385fd07f6e81ae7fc37ba6169a955edf8173ea |
| 41767 | 2026-09-06T06:01:53.062Z | managed_process_admitted |  |  | owner=default |
| 41768 | 2026-09-06T06:01:53.506Z | managed_process_started |  |  | owner=default |
| 41770 | 2026-09-06T06:02:30.576Z | managed_process_terminal |  |  | owner=default |
| 41771 | 2026-09-06T06:02:30.921Z | proof_recorded |  |  | stage_id=check:4a2b623632395e21; status=failed; cache_hit=False; input_fingerprint=9164302dd3194cbb69e453beae385fd07f6e81ae7fc37ba6169a955edf8173ea |
| 41772 | 2026-09-06T06:02:31.196Z | observation_span_recorded |  |  |  |
| 41773 | 2026-09-06T06:02:31.383Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 41774 | 2026-09-06T06:02:31.584Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 41775 | 2026-09-06T06:02:31.777Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:68952bdfdf25eaca | passed | b0c0f33116a5be05ce2d1703452ad3955ea4b1c759e378a79ec0020dd860dcc7 | False | 4384 | 0 |
| check:e4c791e9c6fad3b4 | passed | 5d30ee3a853b79b360619559ed58c9a0589edbd8e6e7d0c9f490b4b5605f192e | False | 6575 | 0 |
| check:4a2b623632395e21 | failed | 9164302dd3194cbb69e453beae385fd07f6e81ae7fc37ba6169a955edf8173ea | False | 37875 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `70`
- Chain head: `2673ebda23130a050414a5f0813b71cd51f7d7274ff913d95f592f9674d45129`
