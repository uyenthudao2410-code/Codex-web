# Orchestration Wave 3

- Run: `db739e7071ac4cd48d42320247b92873`
- Wave: `e91566a97df440dfa6bd1e4598c8aae2`
- Objective: Close P0.3 F2 in scripts/packaged-recovery-smoke.js only. Preserve exact packaged Supervisor argv ['--recovery-host']; isolate through a temporary APPDATA root, kill only the exact owned host PID without /T, then require real packaged Supervisor Once to recreate a new authenticated Recovery Host and healthy Recovery MCP. Preserve production descriptor stability and cleanup. Do not rebuild or touch dist, Scheduled Tasks, production AppData, active development runtime, tests, AGENTS.md, UI files, or volatile evidence.
- Mode: `mcp_only`
- Base HEAD: `885260b404c2c64df1b1afa835963045ac55dbf6`
- Worktree fingerprint: `110f6b3b96d118557ee6d161cc387d716b70f969023a2825f1b0b1ee48cad4a1`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 13399 | 2026-08-17T09:54:22.092Z | wave_replanned |  | PREFLIGHT | reason=The new F2 fixture passed all resurrection/authenticated-identity assertions; the only failure was a Windows EPERM in test cleanup while removing the fixture app root. Replan only to harden test-only fixture termination and bounded cleanup, then rerun the focused Supervisor suite and restored packaged smoke. Do not change F2 semantics or production behavior. |
| 13400 | 2026-08-17T09:54:22.308Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 13401 | 2026-08-17T09:54:22.532Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 13402 | 2026-08-17T09:54:22.727Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 13403 | 2026-08-17T09:54:22.939Z | state_transition | READY | ROUTED | reason=route_selected |
| 13404 | 2026-08-17T09:54:23.625Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=e3c5a2fab0dc42d58cc26160170529b5 |
| 13405 | 2026-08-17T09:54:23.846Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 13406 | 2026-08-17T09:54:24.534Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=e3c5a2fab0dc42d58cc26160170529b5 |
| 13407 | 2026-08-17T09:54:24.783Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 13408 | 2026-08-17T09:54:25.426Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:776efcdd91eaee94; input_fingerprint=a7398f9e241968754f947df36ee93c27d9cba298564644eff433752c14522477 |
| 13409 | 2026-08-17T09:54:25.811Z | managed_process_admitted |  |  | owner=default |
| 13410 | 2026-08-17T09:54:26.183Z | managed_process_started |  |  | owner=default |
| 13411 | 2026-08-17T09:54:26.683Z | managed_process_terminal |  |  | owner=default |
| 13412 | 2026-08-17T09:54:27.064Z | proof_recorded |  |  | stage_id=check:776efcdd91eaee94; status=passed; cache_hit=False; input_fingerprint=a7398f9e241968754f947df36ee93c27d9cba298564644eff433752c14522477 |
| 13413 | 2026-08-17T09:54:27.259Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:fe3ffbf7aa7a92a6; input_fingerprint=c7cea4b4b44b57a2602c1b199102452a081cb4cc8b6c591393ae948dad86008c |
| 13414 | 2026-08-17T09:54:27.650Z | managed_process_admitted |  |  | owner=default |
| 13415 | 2026-08-17T09:54:28.004Z | managed_process_started |  |  | owner=default |
| 13416 | 2026-08-17T09:54:39.725Z | managed_process_terminal |  |  | owner=default |
| 13417 | 2026-08-17T09:54:40.045Z | proof_recorded |  |  | stage_id=check:fe3ffbf7aa7a92a6; status=passed; cache_hit=False; input_fingerprint=c7cea4b4b44b57a2602c1b199102452a081cb4cc8b6c591393ae948dad86008c |
| 13418 | 2026-08-17T09:54:40.261Z | proof_cache_miss |  |  | reason=cold; stage_id=check:470e7e0d382448b5; input_fingerprint=db78f8bd1e55195e8ea44d3c46d92c3285dd077234eba5f14c375e1b5c4df2e7 |
| 13419 | 2026-08-17T09:54:40.660Z | managed_process_admitted |  |  | owner=default |
| 13420 | 2026-08-17T09:54:41.084Z | managed_process_started |  |  | owner=default |
| 13421 | 2026-08-17T09:54:45.483Z | managed_process_terminal |  |  | owner=default |
| 13422 | 2026-08-17T09:54:46.132Z | proof_recorded |  |  | stage_id=check:470e7e0d382448b5; status=passed; cache_hit=False; input_fingerprint=db78f8bd1e55195e8ea44d3c46d92c3285dd077234eba5f14c375e1b5c4df2e7 |
| 13423 | 2026-08-17T09:54:46.297Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=069bfee7b0f48d2d8135815d1041217f262fc053d5929ed8e8deb6b9b9cff6e7 |
| 13424 | 2026-08-17T09:54:46.709Z | managed_process_admitted |  |  | owner=default |
| 13425 | 2026-08-17T09:54:47.067Z | managed_process_started |  |  | owner=default |
| 13426 | 2026-08-17T09:55:07.341Z | managed_process_terminal |  |  | owner=default |
| 13427 | 2026-08-17T09:55:08.781Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=069bfee7b0f48d2d8135815d1041217f262fc053d5929ed8e8deb6b9b9cff6e7 |
| 13428 | 2026-08-17T09:55:09.551Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 13430 | 2026-08-17T10:00:06.830Z | managed_process_admitted |  |  | owner=chatweb |
| 13431 | 2026-08-17T10:00:07.196Z | managed_process_started |  |  | owner=chatweb |
| 13432 | 2026-08-17T10:00:07.871Z | managed_process_terminal |  |  | owner=chatweb |
| 13433 | 2026-08-17T10:00:26.843Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 13434 | 2026-08-17T10:00:27.251Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:776efcdd91eaee94 | passed | a7398f9e241968754f947df36ee93c27d9cba298564644eff433752c14522477 | False | 1254 | 0 |
| check:fe3ffbf7aa7a92a6 | passed | c7cea4b4b44b57a2602c1b199102452a081cb4cc8b6c591393ae948dad86008c | False | 12452 | 0 |
| check:470e7e0d382448b5 | passed | db78f8bd1e55195e8ea44d3c46d92c3285dd077234eba5f14c375e1b5c4df2e7 | False | 5426 | 0 |
| verify:tests | passed | 069bfee7b0f48d2d8135815d1041217f262fc053d5929ed8e8deb6b9b9cff6e7 | False | 21985 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 46b3c443bdb44a99a158747b63d05791 | accepted | 885260b404c2c64df1b1afa835963045ac55dbf6 | 9dd2363f558dad78294e3431c5b4776bdd73f3655004e4653655ef7db791c340 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `81`
- Chain head: `d3ea95e8cfc0fe333b9980ef064af64376813f71f7951d97c71420d22bd36c41`
