# Orchestration Wave 1

- Run: `0e7268b8bc324ebd972ac00819df82fa`
- Wave: `91c5488530aa4f4d92ce5f0343ea7442`
- Objective: Audit whether the local checkout actually contains and proves the claimed PR #17 recovery/runtime identity fixes. Verify: main/HEAD and ancestry for f6018a5420c28b5da3e6effc456ee07da25a14ed, a1c664c2, 75169953; dev installation_id derived from canonical running checkout root without persisting raw path; dev A->B takeover with authenticated exact owner_pid+instance_id and descriptor TOCTOU rejection RECOVERY_DESCRIPTOR_CHANGED; legacy missing installation_id stale/bootstrap behavior; packaged fail-closed across installation identities; development startWithWindows forced false and stale dev supervisor suppression via stop.request; runtimeIdentity.js included in Recovery Host fingerprint; workspace settings passed as --workspace and not reused to infer checkout source; authorizedRoots/canonical alias behavior; .coding-tools untouched by the claimed merge. Locate the exact regression tests and authoritative commands. Do not modify files.
- Mode: `mcp_only`
- Base HEAD: `f6018a5420c28b5da3e6effc456ee07da25a14ed`
- Worktree fingerprint: `b95a78c6c94bc1307af9a80dfddd528b907e8e297f028810b55b1b1a5fca07ed`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 16450 | 2026-08-18T08:30:43.786Z | run_started |  | PREFLIGHT |  |
| 16451 | 2026-08-18T08:30:54.194Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 16452 | 2026-08-18T08:31:11.568Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 16453 | 2026-08-18T08:31:11.689Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 16454 | 2026-08-18T08:31:11.831Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 16455 | 2026-08-18T08:31:11.942Z | state_transition | READY | ROUTED | reason=route_selected |
| 16456 | 2026-08-18T08:31:12.456Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=f32e44d18c45489cb753542a5c3da6a8 |
| 16457 | 2026-08-18T08:31:12.618Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 16458 | 2026-08-18T08:31:13.100Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=f32e44d18c45489cb753542a5c3da6a8 |
| 16459 | 2026-08-18T08:31:13.266Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 16460 | 2026-08-18T08:31:13.619Z | proof_cache_miss |  |  | reason=cold; stage_id=check:747070c16fa829d5; input_fingerprint=44c2d1e1df59bb68df07fab2089891b301e3d5cec9d3b20a92d2c3e119234822 |
| 16461 | 2026-08-18T08:31:13.994Z | managed_process_admitted |  |  | owner=default |
| 16462 | 2026-08-18T08:31:14.340Z | managed_process_started |  |  | owner=default |
| 16463 | 2026-08-18T08:31:14.783Z | managed_process_terminal |  |  | owner=default |
| 16464 | 2026-08-18T08:31:15.068Z | proof_recorded |  |  | stage_id=check:747070c16fa829d5; status=passed; cache_hit=False; input_fingerprint=44c2d1e1df59bb68df07fab2089891b301e3d5cec9d3b20a92d2c3e119234822 |
| 16465 | 2026-08-18T08:31:15.220Z | proof_cache_miss |  |  | reason=cold; stage_id=check:36b22640ff1b5162; input_fingerprint=c9c14e790271fd735c29cd620c646e1f261c899ffeb1f1d388b1df7c9d089354 |
| 16466 | 2026-08-18T08:31:15.524Z | managed_process_admitted |  |  | owner=default |
| 16467 | 2026-08-18T08:31:15.826Z | managed_process_started |  |  | owner=default |
| 16468 | 2026-08-18T08:31:16.251Z | managed_process_terminal |  |  | owner=default |
| 16469 | 2026-08-18T08:31:16.525Z | proof_recorded |  |  | stage_id=check:36b22640ff1b5162; status=passed; cache_hit=False; input_fingerprint=c9c14e790271fd735c29cd620c646e1f261c899ffeb1f1d388b1df7c9d089354 |
| 16470 | 2026-08-18T08:31:16.671Z | proof_cache_miss |  |  | reason=cold; stage_id=check:a2dacbdd031bb736; input_fingerprint=489a2c04789c59ac6b4cf3b438708189894168f09a422e422a1d217b2a8a4d86 |
| 16471 | 2026-08-18T08:31:17.028Z | managed_process_admitted |  |  | owner=default |
| 16472 | 2026-08-18T08:31:17.293Z | managed_process_started |  |  | owner=default |
| 16473 | 2026-08-18T08:31:17.648Z | managed_process_terminal |  |  | owner=default |
| 16474 | 2026-08-18T08:31:17.985Z | proof_recorded |  |  | stage_id=check:a2dacbdd031bb736; status=passed; cache_hit=False; input_fingerprint=489a2c04789c59ac6b4cf3b438708189894168f09a422e422a1d217b2a8a4d86 |
| 16475 | 2026-08-18T08:31:18.191Z | proof_cache_miss |  |  | reason=cold; stage_id=check:2ea6dab0b5ce5f8e; input_fingerprint=64eef2d67eb98dd4075d8dcdce2efe44b6e081790b2b46a54a59fde778e7ebcb |
| 16476 | 2026-08-18T08:31:18.539Z | managed_process_admitted |  |  | owner=default |
| 16477 | 2026-08-18T08:31:18.860Z | managed_process_started |  |  | owner=default |
| 16478 | 2026-08-18T08:31:19.235Z | managed_process_terminal |  |  | owner=default |
| 16479 | 2026-08-18T08:31:19.551Z | proof_recorded |  |  | stage_id=check:2ea6dab0b5ce5f8e; status=passed; cache_hit=False; input_fingerprint=64eef2d67eb98dd4075d8dcdce2efe44b6e081790b2b46a54a59fde778e7ebcb |
| 16480 | 2026-08-18T08:31:19.680Z | proof_cache_miss |  |  | reason=cold; stage_id=check:0c090157ec1ce7ef; input_fingerprint=dbb1b1f40f6de5ed96e6410d318b7f7623e24ffa3d0d798d38e0dd2fdbf47b04 |
| 16481 | 2026-08-18T08:31:19.968Z | managed_process_admitted |  |  | owner=default |
| 16482 | 2026-08-18T08:31:20.243Z | managed_process_started |  |  | owner=default |
| 16483 | 2026-08-18T08:31:20.634Z | managed_process_terminal |  |  | owner=default |
| 16484 | 2026-08-18T08:31:20.960Z | proof_recorded |  |  | stage_id=check:0c090157ec1ce7ef; status=passed; cache_hit=False; input_fingerprint=dbb1b1f40f6de5ed96e6410d318b7f7623e24ffa3d0d798d38e0dd2fdbf47b04 |
| 16485 | 2026-08-18T08:31:21.085Z | proof_cache_miss |  |  | reason=cold; stage_id=check:770a3a021651a656; input_fingerprint=f56f0341f8344e1e649af96d2c5efa9f818927899a428fe821156eba6969e553 |
| 16486 | 2026-08-18T08:31:21.410Z | managed_process_admitted |  |  | owner=default |
| 16487 | 2026-08-18T08:31:21.681Z | managed_process_started |  |  | owner=default |
| 16488 | 2026-08-18T08:31:22.056Z | managed_process_terminal |  |  | owner=default |
| 16489 | 2026-08-18T08:31:22.361Z | proof_recorded |  |  | stage_id=check:770a3a021651a656; status=passed; cache_hit=False; input_fingerprint=f56f0341f8344e1e649af96d2c5efa9f818927899a428fe821156eba6969e553 |
| 16490 | 2026-08-18T08:31:22.560Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=08dabfa084d4b2967753bff8786e513287c30ff2da5af5e4ed2ec9c6800ffd6b |
| 16491 | 2026-08-18T08:31:22.905Z | managed_process_admitted |  |  | owner=default |
| 16492 | 2026-08-18T08:31:23.178Z | managed_process_started |  |  | owner=default |
| 16493 | 2026-08-18T08:31:23.656Z | managed_process_terminal |  |  | owner=default |
| 16494 | 2026-08-18T08:31:23.956Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=08dabfa084d4b2967753bff8786e513287c30ff2da5af5e4ed2ec9c6800ffd6b |
| 16495 | 2026-08-18T08:31:24.097Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 16496 | 2026-08-18T08:31:44.303Z | managed_process_admitted |  |  | owner=chatweb |
| 16497 | 2026-08-18T08:31:44.661Z | managed_process_started |  |  | owner=chatweb |
| 16498 | 2026-08-18T08:31:45.138Z | managed_process_terminal |  |  | owner=chatweb |
| 16499 | 2026-08-18T08:31:51.365Z | managed_process_admitted |  |  | owner=chatweb |
| 16500 | 2026-08-18T08:31:51.695Z | managed_process_started |  |  | owner=chatweb |
| 16501 | 2026-08-18T08:31:53.063Z | managed_process_terminal |  |  | owner=chatweb |
| 16502 | 2026-08-18T08:32:01.534Z | managed_process_admitted |  |  | owner=chatweb |
| 16503 | 2026-08-18T08:32:01.902Z | managed_process_started |  |  | owner=chatweb |
| 16504 | 2026-08-18T08:32:02.369Z | managed_process_terminal |  |  | owner=chatweb |
| 16505 | 2026-08-18T08:32:09.472Z | managed_process_admitted |  |  | owner=chatweb |
| 16506 | 2026-08-18T08:32:09.821Z | managed_process_started |  |  | owner=chatweb |
| 16507 | 2026-08-18T08:32:11.333Z | managed_process_terminal |  |  | owner=chatweb |
| 16508 | 2026-08-18T08:32:17.206Z | managed_process_admitted |  |  | owner=chatweb |
| 16509 | 2026-08-18T08:32:17.588Z | managed_process_started |  |  | owner=chatweb |
| 16510 | 2026-08-18T08:32:18.047Z | managed_process_terminal |  |  | owner=chatweb |
| 16511 | 2026-08-18T08:32:45.847Z | managed_process_admitted |  |  | owner=chatweb |
| 16512 | 2026-08-18T08:32:46.156Z | managed_process_started |  |  | owner=chatweb |
| 16513 | 2026-08-18T08:32:46.585Z | managed_process_terminal |  |  | owner=chatweb |
| 16514 | 2026-08-18T08:34:03.286Z | managed_process_admitted |  |  | owner=chatweb |
| 16515 | 2026-08-18T08:34:03.688Z | managed_process_started |  |  | owner=chatweb |
| 16516 | 2026-08-18T08:34:04.110Z | managed_process_terminal |  |  | owner=chatweb |
| 16517 | 2026-08-18T08:34:13.078Z | managed_process_admitted |  |  | owner=chatweb |
| 16518 | 2026-08-18T08:34:13.427Z | managed_process_started |  |  | owner=chatweb |
| 16519 | 2026-08-18T08:34:13.887Z | managed_process_terminal |  |  | owner=chatweb |
| 16520 | 2026-08-18T08:34:22.178Z | managed_process_admitted |  |  | owner=chatweb |
| 16521 | 2026-08-18T08:34:22.538Z | managed_process_started |  |  | owner=chatweb |
| 16522 | 2026-08-18T08:34:23.035Z | managed_process_terminal |  |  | owner=chatweb |
| 16523 | 2026-08-18T08:34:27.756Z | managed_process_admitted |  |  | owner=chatweb |
| 16524 | 2026-08-18T08:34:28.178Z | managed_process_started |  |  | owner=chatweb |
| 16525 | 2026-08-18T08:34:28.679Z | managed_process_terminal |  |  | owner=chatweb |
| 16526 | 2026-08-18T08:34:45.072Z | managed_process_admitted |  |  | owner=chatweb |
| 16527 | 2026-08-18T08:34:45.488Z | managed_process_started |  |  | owner=chatweb |
| 16528 | 2026-08-18T08:34:45.920Z | managed_process_terminal |  |  | owner=chatweb |
| 16529 | 2026-08-18T08:34:53.305Z | managed_process_admitted |  |  | owner=chatweb |
| 16530 | 2026-08-18T08:34:53.687Z | managed_process_started |  |  | owner=chatweb |
| 16531 | 2026-08-18T08:34:55.209Z | managed_process_terminal |  |  | owner=chatweb |
| 16532 | 2026-08-18T08:35:04.684Z | managed_process_admitted |  |  | owner=chatweb |
| 16533 | 2026-08-18T08:35:05.032Z | managed_process_started |  |  | owner=chatweb |
| 16534 | 2026-08-18T08:35:05.490Z | managed_process_terminal |  |  | owner=chatweb |
| 16535 | 2026-08-18T08:35:35.615Z | managed_process_admitted |  |  | owner=chatweb |
| 16536 | 2026-08-18T08:35:35.987Z | managed_process_started |  |  | owner=chatweb |
| 16537 | 2026-08-18T08:35:37.463Z | managed_process_terminal |  |  | owner=chatweb |
| 16538 | 2026-08-18T08:35:50.275Z | managed_process_admitted |  |  | owner=chatweb |
| 16539 | 2026-08-18T08:35:50.630Z | managed_process_started |  |  | owner=chatweb |
| 16540 | 2026-08-18T08:35:52.090Z | managed_process_terminal |  |  | owner=chatweb |
| 16541 | 2026-08-18T08:36:07.019Z | managed_process_admitted |  |  | owner=chatweb |
| 16542 | 2026-08-18T08:36:07.377Z | managed_process_started |  |  | owner=chatweb |
| 16543 | 2026-08-18T08:36:09.213Z | managed_process_terminal |  |  | owner=chatweb |
| 16544 | 2026-08-18T08:36:19.617Z | managed_process_admitted |  |  | owner=chatweb |
| 16545 | 2026-08-18T08:36:19.944Z | managed_process_started |  |  | owner=chatweb |
| 16546 | 2026-08-18T08:36:23.184Z | managed_process_terminal |  |  | owner=chatweb |
| 16547 | 2026-08-18T08:36:34.420Z | managed_process_admitted |  |  | owner=chatweb |
| 16548 | 2026-08-18T08:36:34.741Z | managed_process_started |  |  | owner=chatweb |
| 16549 | 2026-08-18T08:36:36.396Z | managed_process_terminal |  |  | owner=chatweb |
| 16550 | 2026-08-18T08:36:51.766Z | managed_process_admitted |  |  | owner=chatweb |
| 16551 | 2026-08-18T08:36:52.188Z | managed_process_started |  |  | owner=chatweb |
| 16552 | 2026-08-18T08:36:52.768Z | managed_process_terminal |  |  | owner=chatweb |
| 16553 | 2026-08-18T08:37:03.181Z | managed_process_admitted |  |  | owner=chatweb |
| 16554 | 2026-08-18T08:37:03.534Z | managed_process_started |  |  | owner=chatweb |
| 16555 | 2026-08-18T08:37:04.032Z | managed_process_terminal |  |  | owner=chatweb |
| 16556 | 2026-08-18T08:37:11.542Z | managed_process_admitted |  |  | owner=chatweb |
| 16557 | 2026-08-18T08:37:11.900Z | managed_process_started |  |  | owner=chatweb |
| 16558 | 2026-08-18T08:37:34.525Z | managed_process_terminal |  |  | owner=chatweb |
| 16559 | 2026-08-18T08:37:49.558Z | managed_process_admitted |  |  | owner=chatweb |
| 16560 | 2026-08-18T08:37:49.883Z | managed_process_started |  |  | owner=chatweb |
| 16561 | 2026-08-18T08:37:51.350Z | managed_process_terminal |  |  | owner=chatweb |
| 16562 | 2026-08-18T08:38:05.810Z | managed_process_admitted |  |  | owner=chatweb |
| 16563 | 2026-08-18T08:38:06.158Z | managed_process_started |  |  | owner=chatweb |
| 16564 | 2026-08-18T08:38:07.492Z | managed_process_terminal |  |  | owner=chatweb |
| 16565 | 2026-08-18T08:38:14.355Z | managed_process_admitted |  |  | owner=chatweb |
| 16566 | 2026-08-18T08:38:14.700Z | managed_process_started |  |  | owner=chatweb |
| 16567 | 2026-08-18T08:38:15.181Z | managed_process_terminal |  |  | owner=chatweb |
| 16568 | 2026-08-18T08:38:25.914Z | managed_process_admitted |  |  | owner=chatweb |
| 16569 | 2026-08-18T08:38:26.289Z | managed_process_started |  |  | owner=chatweb |
| 16570 | 2026-08-18T08:38:27.584Z | managed_process_terminal |  |  | owner=chatweb |
| 16571 | 2026-08-18T08:38:39.063Z | managed_process_admitted |  |  | owner=chatweb |
| 16572 | 2026-08-18T08:38:39.466Z | managed_process_started |  |  | owner=chatweb |
| 16573 | 2026-08-18T08:38:40.005Z | managed_process_terminal |  |  | owner=chatweb |
| 16574 | 2026-08-18T08:38:46.089Z | managed_process_admitted |  |  | owner=chatweb |
| 16575 | 2026-08-18T08:38:46.474Z | managed_process_started |  |  | owner=chatweb |
| 16576 | 2026-08-18T08:38:46.939Z | managed_process_terminal |  |  | owner=chatweb |
| 16577 | 2026-08-18T08:39:03.125Z | failure_observed | ACCEPTING | ACCEPTING | reason=Reject full acceptance: focused checkout/recovery authority regressions pass 16/16 and live Recovery Host/Coding MCP are on E:\DEV\Codex-web with the new installation identity/workspace contract, but project-native `npm test` fails 3/227. Two failures are directly attributable to f6018a54 adding runtimeIdentity.js to RECOVERY_HOST_LEGACY_V1_ADDED_FILE_DIGESTS without updating legacy bridge fixtures in tests/component-revision.test.js and tests/recovery-host.test.js; both now throw REVISION_BRIDGE_FILE_MISSING. A third source-bundle failure is environmental/pre-existing nested resources/coding-tools-mcp/.coding-tools state. Therefore the authority implementation is substantially fixed, but the merged source is not fully acceptance-green.; failure_class=SOL_REJECTED |
| 16578 | 2026-08-18T08:39:03.327Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |
| 16579 | 2026-08-18T08:39:03.529Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |
| 16580 | 2026-08-18T08:41:22.191Z | observation_span_recorded |  |  |  |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:747070c16fa829d5 | passed | 44c2d1e1df59bb68df07fab2089891b301e3d5cec9d3b20a92d2c3e119234822 | False | 1152 | 0 |
| check:36b22640ff1b5162 | passed | c9c14e790271fd735c29cd620c646e1f261c899ffeb1f1d388b1df7c9d089354 | False | 1009 | 0 |
| check:a2dacbdd031bb736 | passed | 489a2c04789c59ac6b4cf3b438708189894168f09a422e422a1d217b2a8a4d86 | False | 971 | 0 |
| check:2ea6dab0b5ce5f8e | passed | 64eef2d67eb98dd4075d8dcdce2efe44b6e081790b2b46a54a59fde778e7ebcb | False | 984 | 0 |
| check:0c090157ec1ce7ef | passed | dbb1b1f40f6de5ed96e6410d318b7f7623e24ffa3d0d798d38e0dd2fdbf47b04 | False | 976 | 0 |
| check:770a3a021651a656 | passed | f56f0341f8344e1e649af96d2c5efa9f818927899a428fe821156eba6969e553 | False | 946 | 0 |
| verify:tests | passed | 08dabfa084d4b2967753bff8786e513287c30ff2da5af5e4ed2ec9c6800ffd6b | False | 1092 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `235`
- Chain head: `060ca0a6268d2b3334e7829b2ea9b22a4448f65faa6dd34c3ef57e625695bb94`
