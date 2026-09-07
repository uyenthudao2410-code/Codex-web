# Orchestration Wave 2

- Run: `2f73ac20a59e4bc0b3e2ba638b5a990c`
- Wave: `20c0618be24148de938f7a27d9e407ee`
- Objective: Start the local WebCodex native semantic provider for E:\DEV\Codex-web from the repaired machine state at C:\Users\Admin\AppData\Local\WebCodex\g4-semantic\codex-web-current, then verify it remains alive. Do not modify repository source, Git, ledger, activation configuration, or release artifacts.
- Objective revision: `2`
- Objective SHA-256: `7a290adb84dbfd233f24f92d2fc261a2c55b1b52affaac4dd30873d74ebf8338`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `9255f94c9beff33f8c6c53d6745a08968f5a12bb`
- Worktree fingerprint: `5c7c04dbe08093df17462094e6fcbd44e29f691345f347af639325d7305f7b85`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 42407 | 2026-09-07T02:18:21.647Z | wave_replanned |  | PREFLIGHT | reason=The first background launch exited immediately and provided no child stderr. Change strategy: launch with temporary redirected stdout/stderr, retain the child only if it stays alive for the initial startup window, and emit bounded startup diagnostics only on immediate exit. |
| 42408 | 2026-09-07T02:18:21.866Z | observation_span_recorded |  |  |  |
| 42409 | 2026-09-07T02:18:22.330Z | observation_span_recorded |  |  |  |
| 42410 | 2026-09-07T02:18:22.583Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 42411 | 2026-09-07T02:18:22.807Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 42412 | 2026-09-07T02:18:22.984Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 42413 | 2026-09-07T02:18:23.174Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 42414 | 2026-09-07T02:18:23.336Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 42415 | 2026-09-07T02:18:23.532Z | state_transition | READY | ROUTED | reason=route_selected |
| 42416 | 2026-09-07T02:18:23.718Z | observation_span_recorded |  |  |  |
| 42417 | 2026-09-07T02:18:24.184Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=1fd610b9639c4c5e8fd79fc2db5eacd3 |
| 42418 | 2026-09-07T02:18:24.382Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 42419 | 2026-09-07T02:18:24.789Z | observation_span_recorded |  |  |  |
| 42420 | 2026-09-07T02:18:25.104Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=1fd610b9639c4c5e8fd79fc2db5eacd3 |
| 42421 | 2026-09-07T02:18:25.274Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 42422 | 2026-09-07T02:18:25.730Z | proof_cache_miss |  |  | reason=cold; stage_id=check:a2e142e4d09ad612; input_fingerprint=90905fffe41c0b1a30f0f84b6227f51f1e12bd0177f88930b08009e6cd506d11 |
| 42423 | 2026-09-07T02:18:26.085Z | managed_process_admitted |  |  | owner=default |
| 42424 | 2026-09-07T02:18:26.383Z | managed_process_started |  |  | owner=default |
| 42425 | 2026-09-07T02:18:30.305Z | managed_process_terminal |  |  | owner=default |
| 42426 | 2026-09-07T02:18:30.649Z | proof_recorded |  |  | stage_id=check:a2e142e4d09ad612; status=failed; cache_hit=False; input_fingerprint=90905fffe41c0b1a30f0f84b6227f51f1e12bd0177f88930b08009e6cd506d11 |
| 42427 | 2026-09-07T02:18:30.880Z | observation_span_recorded |  |  |  |
| 42428 | 2026-09-07T02:18:31.048Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 42429 | 2026-09-07T02:18:31.233Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 42430 | 2026-09-07T02:18:31.428Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:a2e142e4d09ad612 | failed | 90905fffe41c0b1a30f0f84b6227f51f1e12bd0177f88930b08009e6cd506d11 | False | 4544 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `139`
- Chain head: `27e07c13675e7babc01a534fac9e304ceff482c33898fdad217869a5037c5f98`
