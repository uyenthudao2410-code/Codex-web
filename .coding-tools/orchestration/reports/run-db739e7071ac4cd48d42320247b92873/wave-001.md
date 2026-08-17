# Orchestration Wave 1

- Run: `db739e7071ac4cd48d42320247b92873`
- Wave: `e91e5625ce914f1b86b6e56f498ff18e`
- Objective: Close P0.3 F2 in scripts/packaged-recovery-smoke.js only. Preserve exact packaged Supervisor argv ['--recovery-host']; isolate through a temporary APPDATA root, kill only the exact owned host PID without /T, then require real packaged Supervisor Once to recreate a new authenticated Recovery Host and healthy Recovery MCP. Preserve production descriptor stability and cleanup. Do not rebuild or touch dist, Scheduled Tasks, production AppData, active development runtime, tests, AGENTS.md, UI files, or volatile evidence.
- Mode: `mcp_only`
- Base HEAD: `885260b404c2c64df1b1afa835963045ac55dbf6`
- Worktree fingerprint: `ec1811764502d2852d3545c7b17bb9b54cdf40de8f0700c610b40cb0198633c9`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 13353 | 2026-08-17T09:50:00.397Z | run_started |  | PREFLIGHT |  |
| 13354 | 2026-08-17T09:50:00.596Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 13355 | 2026-08-17T09:50:00.959Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 13356 | 2026-08-17T09:50:01.171Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 13357 | 2026-08-17T09:50:01.352Z | state_transition | READY | ROUTED | reason=route_selected |
| 13358 | 2026-08-17T09:50:02.163Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=842ce9dc7fb9488ea9c9f7620ec872a8 |
| 13359 | 2026-08-17T09:50:02.328Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 13360 | 2026-08-17T09:50:03.046Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=842ce9dc7fb9488ea9c9f7620ec872a8 |
| 13361 | 2026-08-17T09:50:03.253Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 13362 | 2026-08-17T09:50:03.881Z | proof_cache_miss |  |  | reason=cold; stage_id=check:c05354292c3fa46b; input_fingerprint=64a91940788c7989f89fd2538747331ba9fa760e08d90a91e0f69e2a3760d329 |
| 13363 | 2026-08-17T09:50:04.273Z | managed_process_admitted |  |  | owner=default |
| 13364 | 2026-08-17T09:50:04.572Z | managed_process_started |  |  | owner=default |
| 13365 | 2026-08-17T09:50:05.089Z | managed_process_terminal |  |  | owner=default |
| 13366 | 2026-08-17T09:50:05.491Z | proof_recorded |  |  | stage_id=check:c05354292c3fa46b; status=passed; cache_hit=False; input_fingerprint=64a91940788c7989f89fd2538747331ba9fa760e08d90a91e0f69e2a3760d329 |
| 13367 | 2026-08-17T09:50:05.675Z | proof_cache_miss |  |  | reason=cold; stage_id=check:470e7e0d382448b5; input_fingerprint=01ffc98ea577847b3b2923791a8e4b89a2d0bc38d0ec58404f8c869b367a2054 |
| 13368 | 2026-08-17T09:50:06.142Z | managed_process_admitted |  |  | owner=default |
| 13369 | 2026-08-17T09:50:06.456Z | managed_process_started |  |  | owner=default |
| 13370 | 2026-08-17T09:50:19.414Z | managed_process_terminal |  |  | owner=default |
| 13371 | 2026-08-17T09:50:19.773Z | proof_recorded |  |  | stage_id=check:470e7e0d382448b5; status=failed; cache_hit=False; input_fingerprint=01ffc98ea577847b3b2923791a8e4b89a2d0bc38d0ec58404f8c869b367a2054 |
| 13372 | 2026-08-17T09:50:19.975Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 13373 | 2026-08-17T09:50:20.158Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 13374 | 2026-08-17T09:50:20.321Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:c05354292c3fa46b | passed | 64a91940788c7989f89fd2538747331ba9fa760e08d90a91e0f69e2a3760d329 | False | 1252 | 0 |
| check:470e7e0d382448b5 | failed | 01ffc98ea577847b3b2923791a8e4b89a2d0bc38d0ec58404f8c869b367a2054 | False | 13744 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `81`
- Chain head: `d3ea95e8cfc0fe333b9980ef064af64376813f71f7951d97c71420d22bd36c41`
