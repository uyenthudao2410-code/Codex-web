# Orchestration Wave 2

- Run: `db739e7071ac4cd48d42320247b92873`
- Wave: `80a24648525e4eac808e953ad54028c5`
- Objective: Close P0.3 F2 in scripts/packaged-recovery-smoke.js only. Preserve exact packaged Supervisor argv ['--recovery-host']; isolate through a temporary APPDATA root, kill only the exact owned host PID without /T, then require real packaged Supervisor Once to recreate a new authenticated Recovery Host and healthy Recovery MCP. Preserve production descriptor stability and cleanup. Do not rebuild or touch dist, Scheduled Tasks, production AppData, active development runtime, tests, AGENTS.md, UI files, or volatile evidence.
- Mode: `mcp_only`
- Base HEAD: `885260b404c2c64df1b1afa835963045ac55dbf6`
- Worktree fingerprint: `d753aa5e3283a418fe31b7c2580347c4ed15d27b53f17a257e10acb47067abbc`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 13375 | 2026-08-17T09:51:02.962Z | wave_replanned |  | PREFLIGHT | reason=The first F2 packaged smoke attempt proved APPDATA-only isolation invalid before any fault injection: the packaged --recovery-host child exited and no production process was killed. Replan only to inspect exact Electron userData/startup routing and choose an isolation mechanism that preserves the fixed production Supervisor argv; do not retry the failed smoke unchanged. |
| 13376 | 2026-08-17T09:51:04.537Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 13377 | 2026-08-17T09:52:13.721Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 13378 | 2026-08-17T09:53:10.256Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 13379 | 2026-08-17T09:53:10.492Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 13380 | 2026-08-17T09:53:10.734Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 13381 | 2026-08-17T09:53:10.925Z | state_transition | READY | ROUTED | reason=route_selected |
| 13382 | 2026-08-17T09:53:11.615Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=ddec5267a2c7418788d93dd72dcb8bd1 |
| 13383 | 2026-08-17T09:53:11.875Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 13384 | 2026-08-17T09:53:12.609Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=ddec5267a2c7418788d93dd72dcb8bd1 |
| 13385 | 2026-08-17T09:53:12.767Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 13386 | 2026-08-17T09:53:13.283Z | proof_cache_miss |  |  | reason=cold; stage_id=check:776efcdd91eaee94; input_fingerprint=06e474ae1351f156fa6032d051397a1d45b32cab141a738c6fac2f88002dcedd |
| 13387 | 2026-08-17T09:53:13.697Z | managed_process_admitted |  |  | owner=default |
| 13388 | 2026-08-17T09:53:14.010Z | managed_process_started |  |  | owner=default |
| 13389 | 2026-08-17T09:53:14.502Z | managed_process_terminal |  |  | owner=default |
| 13390 | 2026-08-17T09:53:14.874Z | proof_recorded |  |  | stage_id=check:776efcdd91eaee94; status=passed; cache_hit=False; input_fingerprint=06e474ae1351f156fa6032d051397a1d45b32cab141a738c6fac2f88002dcedd |
| 13391 | 2026-08-17T09:53:15.062Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:fe3ffbf7aa7a92a6; input_fingerprint=b54a15a70a5f2965cd0368543e37f2988158741a750f34fdd76e0e5ab7ad6264 |
| 13392 | 2026-08-17T09:53:15.474Z | managed_process_admitted |  |  | owner=default |
| 13393 | 2026-08-17T09:53:15.786Z | managed_process_started |  |  | owner=default |
| 13394 | 2026-08-17T09:53:27.860Z | managed_process_terminal |  |  | owner=default |
| 13395 | 2026-08-17T09:53:28.262Z | proof_recorded |  |  | stage_id=check:fe3ffbf7aa7a92a6; status=failed; cache_hit=False; input_fingerprint=b54a15a70a5f2965cd0368543e37f2988158741a750f34fdd76e0e5ab7ad6264 |
| 13396 | 2026-08-17T09:53:28.555Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 13397 | 2026-08-17T09:53:28.757Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 13398 | 2026-08-17T09:53:29.000Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:776efcdd91eaee94 | passed | 06e474ae1351f156fa6032d051397a1d45b32cab141a738c6fac2f88002dcedd | False | 1241 | 0 |
| check:fe3ffbf7aa7a92a6 | failed | b54a15a70a5f2965cd0368543e37f2988158741a750f34fdd76e0e5ab7ad6264 | False | 12867 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `81`
- Chain head: `d3ea95e8cfc0fe333b9980ef064af64376813f71f7951d97c71420d22bd36c41`
