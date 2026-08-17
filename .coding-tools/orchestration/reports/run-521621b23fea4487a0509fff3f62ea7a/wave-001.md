# Orchestration Wave 1

- Run: `521621b23fea4487a0509fff3f62ea7a`
- Wave: `0c24e7b07dd64306a238a35893fad0b6`
- Objective: Diagnose why the live Recovery Host inspectCodeActivation rejects with WORKSPACE_MISMATCH even though Recovery Host settings, runtime health, and Coding MCP workspace_context all report E:\DEV\Tools-Codex-web. Focus on the Coding MCP /__control/activation GET response workspace field versus /__control/health and JavaScript workspaceKey normalization. Do not mutate files. Identify exact root cause and smallest safe fix if code defect.
- Mode: `mcp_only`
- Base HEAD: `4e5a5165e063b1b1816ef438babb19ca38d379d4`
- Worktree fingerprint: `f370fff1b3b1141cdb4476e03763ecdea536d43631e608b4977c840b1411a54d`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 11508 | 2026-08-17T05:01:44.052Z | run_started |  | PREFLIGHT |  |
| 11509 | 2026-08-17T05:01:44.789Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 11510 | 2026-08-17T05:01:58.968Z | managed_process_admitted |  |  | owner=default |
| 11511 | 2026-08-17T05:01:59.311Z | managed_process_started |  |  | owner=default |
| 11512 | 2026-08-17T05:01:59.940Z | managed_process_terminal |  |  | owner=default |
| 11513 | 2026-08-17T05:02:59.783Z | managed_process_admitted |  |  | owner=default |
| 11514 | 2026-08-17T05:03:00.134Z | managed_process_started |  |  | owner=default |
| 11515 | 2026-08-17T05:03:16.797Z | managed_process_terminal |  |  | owner=default |
| 11516 | 2026-08-17T05:03:29.925Z | managed_process_admitted |  |  | owner=default |
| 11517 | 2026-08-17T05:03:30.342Z | managed_process_started |  |  | owner=default |
| 11518 | 2026-08-17T05:03:43.391Z | managed_process_terminal |  |  | owner=default |
| 11519 | 2026-08-17T05:04:08.965Z | managed_process_admitted |  |  | owner=default |
| 11520 | 2026-08-17T05:04:09.340Z | managed_process_started |  |  | owner=default |
| 11521 | 2026-08-17T05:04:19.823Z | managed_process_terminal |  |  | owner=default |
| 11522 | 2026-08-17T05:04:34.374Z | managed_process_admitted |  |  | owner=default |
| 11523 | 2026-08-17T05:04:34.682Z | managed_process_started |  |  | owner=default |
| 11524 | 2026-08-17T05:04:47.373Z | managed_process_terminal |  |  | owner=default |
| 11525 | 2026-08-17T05:04:47.841Z | managed_process_admitted |  |  | owner=default |
| 11526 | 2026-08-17T05:04:48.186Z | managed_process_started |  |  | owner=default |
| 11527 | 2026-08-17T05:05:00.840Z | managed_process_terminal |  |  | owner=default |
| 11528 | 2026-08-17T05:05:13.474Z | managed_process_admitted |  |  | owner=default |
| 11529 | 2026-08-17T05:05:13.799Z | managed_process_started |  |  | owner=default |
| 11530 | 2026-08-17T05:05:28.500Z | managed_process_terminal |  |  | owner=default |
| 11531 | 2026-08-17T05:05:47.499Z | managed_process_admitted |  |  | owner=default |
| 11532 | 2026-08-17T05:05:47.856Z | managed_process_started |  |  | owner=default |
| 11533 | 2026-08-17T05:05:48.431Z | managed_process_terminal |  |  | owner=default |
| 11534 | 2026-08-17T05:06:21.566Z | managed_process_admitted |  |  | owner=default |
| 11535 | 2026-08-17T05:06:21.915Z | managed_process_started |  |  | owner=default |
| 11536 | 2026-08-17T05:06:32.357Z | managed_process_terminal |  |  | owner=default |
| 11537 | 2026-08-17T05:07:13.615Z | managed_process_admitted |  |  | owner=default |
| 11538 | 2026-08-17T05:07:13.990Z | managed_process_started |  |  | owner=default |
| 11539 | 2026-08-17T05:07:27.776Z | managed_process_terminal |  |  | owner=default |
| 11540 | 2026-08-17T05:07:43.365Z | managed_process_admitted |  |  | owner=default |
| 11541 | 2026-08-17T05:07:43.707Z | managed_process_started |  |  | owner=default |
| 11542 | 2026-08-17T05:08:43.174Z | managed_process_terminal |  |  | owner=default |
| 11543 | 2026-08-17T05:09:05.670Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 11544 | 2026-08-17T05:09:05.861Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 11545 | 2026-08-17T05:09:06.033Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 11546 | 2026-08-17T05:09:06.172Z | state_transition | READY | ROUTED | reason=route_selected |
| 11547 | 2026-08-17T05:09:06.684Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=c63a5c0e6e3d40e9b4dc6aedf3c0c150 |
| 11548 | 2026-08-17T05:09:07.342Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 11549 | 2026-08-17T05:09:09.276Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=c63a5c0e6e3d40e9b4dc6aedf3c0c150 |
| 11550 | 2026-08-17T05:09:09.491Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 11551 | 2026-08-17T05:09:09.883Z | proof_cache_miss |  |  | reason=cold; stage_id=check:359a24141ac8d518; input_fingerprint=cf36ea69c8e337dd843ec75c26bfe0b238cc5c8e89972175155efd0158ae85c8 |
| 11552 | 2026-08-17T05:09:10.365Z | managed_process_admitted |  |  | owner=default |
| 11553 | 2026-08-17T05:09:10.673Z | managed_process_started |  |  | owner=default |
| 11554 | 2026-08-17T05:09:11.122Z | managed_process_terminal |  |  | owner=default |
| 11555 | 2026-08-17T05:09:11.478Z | proof_recorded |  |  | stage_id=check:359a24141ac8d518; status=passed; cache_hit=False; input_fingerprint=cf36ea69c8e337dd843ec75c26bfe0b238cc5c8e89972175155efd0158ae85c8 |
| 11556 | 2026-08-17T05:09:11.672Z | proof_cache_miss |  |  | reason=cold; stage_id=check:cf75f1104df2f33c; input_fingerprint=2baf9eb8075275db1af716025a501fdd5433f29758ee04dedc1f515d8c1bb9b2 |
| 11557 | 2026-08-17T05:09:12.041Z | managed_process_admitted |  |  | owner=default |
| 11558 | 2026-08-17T05:09:12.312Z | managed_process_started |  |  | owner=default |
| 11559 | 2026-08-17T05:09:48.459Z | managed_process_terminal |  |  | owner=default |
| 11560 | 2026-08-17T05:09:48.812Z | proof_recorded |  |  | stage_id=check:cf75f1104df2f33c; status=passed; cache_hit=False; input_fingerprint=2baf9eb8075275db1af716025a501fdd5433f29758ee04dedc1f515d8c1bb9b2 |
| 11561 | 2026-08-17T05:09:49.228Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:2d5ca5fa7103a4f6; input_fingerprint=3d82f12aac1d2fd49029b81d32cd0cfa7d93c8f10235d40c0e113a3497e382e2 |
| 11562 | 2026-08-17T05:09:49.642Z | managed_process_admitted |  |  | owner=default |
| 11563 | 2026-08-17T05:09:49.967Z | managed_process_started |  |  | owner=default |
| 11564 | 2026-08-17T05:09:50.415Z | managed_process_terminal |  |  | owner=default |
| 11565 | 2026-08-17T05:09:50.828Z | proof_recorded |  |  | stage_id=check:2d5ca5fa7103a4f6; status=passed; cache_hit=False; input_fingerprint=3d82f12aac1d2fd49029b81d32cd0cfa7d93c8f10235d40c0e113a3497e382e2 |
| 11566 | 2026-08-17T05:09:51.013Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:b39a03c60a5b0526; input_fingerprint=bf3bdb7c2b5b2531aefbaeddfe7e3e5f43812ba117d82cf8f55781c4dfa46ca5 |
| 11567 | 2026-08-17T05:09:51.381Z | managed_process_admitted |  |  | owner=default |
| 11568 | 2026-08-17T05:09:51.660Z | managed_process_started |  |  | owner=default |
| 11569 | 2026-08-17T05:09:52.158Z | managed_process_terminal |  |  | owner=default |
| 11570 | 2026-08-17T05:09:52.543Z | proof_recorded |  |  | stage_id=check:b39a03c60a5b0526; status=passed; cache_hit=False; input_fingerprint=bf3bdb7c2b5b2531aefbaeddfe7e3e5f43812ba117d82cf8f55781c4dfa46ca5 |
| 11571 | 2026-08-17T05:09:52.742Z | proof_cache_miss |  |  | reason=cold; stage_id=check:b5185aa9957303ac; input_fingerprint=fa5405a91833e52eff28dc174e33ceaf5a22cffe844cfc2e323ec62df2299988 |
| 11572 | 2026-08-17T05:09:53.115Z | managed_process_admitted |  |  | owner=default |
| 11573 | 2026-08-17T05:09:53.425Z | managed_process_started |  |  | owner=default |
| 11574 | 2026-08-17T05:09:53.891Z | managed_process_terminal |  |  | owner=default |
| 11575 | 2026-08-17T05:09:54.219Z | proof_recorded |  |  | stage_id=check:b5185aa9957303ac; status=passed; cache_hit=False; input_fingerprint=fa5405a91833e52eff28dc174e33ceaf5a22cffe844cfc2e323ec62df2299988 |
| 11576 | 2026-08-17T05:09:54.751Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 11577 | 2026-08-17T05:10:10.717Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 11578 | 2026-08-17T05:10:11.089Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:359a24141ac8d518 | passed | cf36ea69c8e337dd843ec75c26bfe0b238cc5c8e89972175155efd0158ae85c8 | False | 1234 | 0 |
| check:cf75f1104df2f33c | passed | 2baf9eb8075275db1af716025a501fdd5433f29758ee04dedc1f515d8c1bb9b2 | False | 36778 | 0 |
| check:2d5ca5fa7103a4f6 | passed | 3d82f12aac1d2fd49029b81d32cd0cfa7d93c8f10235d40c0e113a3497e382e2 | False | 1197 | 0 |
| check:b39a03c60a5b0526 | passed | bf3bdb7c2b5b2531aefbaeddfe7e3e5f43812ba117d82cf8f55781c4dfa46ca5 | False | 1184 | 0 |
| check:b5185aa9957303ac | passed | fa5405a91833e52eff28dc174e33ceaf5a22cffe844cfc2e323ec62df2299988 | False | 1110 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 24364f8a1737484e947a8a804a31f165 | accepted | 4e5a5165e063b1b1816ef438babb19ca38d379d4 | 43b4ed2638de078e535e93ef4e95b20810b914ad753d956309f57997ea202e17 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `71`
- Chain head: `37f2cce6b0eb76f85fac3c172ec06f2c47fd886704c497ff8ef7d4e774ab27fd`
